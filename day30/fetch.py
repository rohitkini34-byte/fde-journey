"""Day 30 task: the fetch layer of thin-sync (Week 5, consolidation week).

Real-world purpose: every CMS integration starts by pulling content out of
the customer's CMS reliably. The network will time out, the CMS will answer
503 during a deploy or 429 when you go too fast, some entries will be broken,
and the data comes in pages. This module turns that messy reality into one
clean list of typed Entry objects. Day 31 stores them in Postgres, Day 32
serves them over FastAPI, and Day 33 packages all three as thin-sync.

In Contentstack terms: this is the code behind "fetch all entries of a
content type from the Delivery API", with the retry and paging logic you
would otherwise copy badly into every script.

THE FAKE CMS (mock_cms.py, given)
    GET /v3/content_types/{content_type}/entries?limit=N[&cursor=C]
    header  access_token: <token>
    200 ->  {"items": [raw entries], "next_cursor": "c2" or null}
    The first page has NO cursor parameter at all.

ASSIGNMENT (from the Day 30 session in the master doc)
-----------------------------------------------------
Implement the seven TODOs below, in order. Each one has a test group in
test_fetch.py, so you can run the tests after each function.

ACCEPTANCE CRITERIA
1. Inside day30/:  python -m pytest -q   ->  27 passed (17 given test
   functions; parametrize turns them into 27 cases), in under 2 seconds.
2. test_mine.py holds 3 tests of your own that use FakeCMS or your own
   MockTransport handler: a wrong token gives FetchError naming 401 after
   exactly one request; four timeouts in a row give FetchError; a CMS that
   returns an empty first page gives an empty list.
3. python fetch.py prints the demo output in the __main__ block below.
4. No test touches the network and no test really sleeps (sleep is passed
   in). No bare "except:" anywhere; only httpx.TransportError is caught
   around the request.
5. python -c "import fetch" prints nothing.
6. day30/ committed and pushed to main with a clear message.
"""

import logging  # warnings for retries and skipped items (Day 12)
import time  # time.sleep is the real sleep; tests pass a fake one
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import datetime

import httpx  # pip install httpx   (or: uv add httpx)

# One named logger per module, like a scoped console in JS (Day 12)
log = logging.getLogger("fetch")

DEFAULT_BASE_URL = "https://cms.example.test/v3"
# REMEMBER: retry only what can succeed next time: rate limits and outages
RETRYABLE_STATUSES = frozenset({429, 500, 502, 503, 504})


# ---------------------------------------------------------------------------
# FetchError (given). The ONE error type callers of this module catch.
# Like a custom Error subclass in JS: class FetchError extends Error {}
# ---------------------------------------------------------------------------
class FetchError(Exception):
    """Raised when the CMS cannot be read: bad status, retries used up."""


# ---------------------------------------------------------------------------
# TODO 1: Entry.from_api
# What:    turn one raw CMS item (a dict) into a typed, frozen Entry.
# Input:   raw = {"uid": "blt001", "title": "Winter Sale", "locale": "en-us",
#                 "updated_at": "2026-11-20T09:30:00Z",
#                 "tags": ["Sale", "winter", "sale"]},  content_type = "page"
# Output:  Entry(uid="blt001", content_type="page", title="Winter Sale",
#                locale="en-us", updated_at=datetime(2026, 11, 20, 9, 30,
#                tzinfo=UTC), tags=("sale", "winter"))
# Rules:   uid and title required; title stripped and not empty.
#          locale defaults to "en-us".
#          updated_at is ISO 8601 AND must carry a timezone ("Z" or +05:30).
#          tags: None or missing -> (); each tag stripped and lowercased,
#          empty tags dropped, duplicates removed, first-seen order kept.
#          ANY problem -> ValueError whose message contains the uid,
#          e.g. "entry 'blt003': title is empty".
# Practises: Concept 1 (parse at the edge), Day 5 dataclasses.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Entry:
    uid: str
    content_type: str
    title: str
    locale: str
    updated_at: datetime
    tags: tuple[str, ...] = ()

    @classmethod
    def from_api(cls, raw: dict, content_type: str) -> "Entry":
        """Build an Entry from one raw CMS item, or raise ValueError."""
        # HINT 1: read uid first with raw.get("uid"), so your error message
        #         can name it even when other fields are broken.
        # HINT 2: wrap the parsing in try/except (KeyError, TypeError,
        #         ValueError, AttributeError) and re-raise ONE ValueError
        #         with "from exc" (Concept 1 shows the shape).
        # HINT 3: an empty title after .strip() is not an exception on its
        #         own: raise ValueError("title is empty") yourself.
        # HINT 4: datetime.fromisoformat(text) parses; if the result's
        #         .tzinfo is None, raise ValueError("updated_at has no
        #         timezone"). A naive time is a bug waiting in Day 31's DB.
        # HINT 5: for tags, loop over (raw.get("tags") or []) and build a
        #         list, skipping a tag if it is empty or already in the list.
        #         Convert to tuple() at the end.
        raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 2: build_client
# What:    one configured httpx.Client for the CMS.
# Input:   build_client("https://cms.example.test/v3", "abc", timeout_s=7.5)
# Output:  a Client whose base_url is that URL, that sends the header
#          access_token: abc on every request, with read/write/pool
#          timeouts of timeout_s and a connect timeout of 3.0 seconds.
#          transport is passed straight through (None = real network).
# Practises: Concept 2 (httpx.Client, httpx.Timeout).
# ---------------------------------------------------------------------------
def build_client(
    base_url: str,
    token: str,
    timeout_s: float = 10.0,
    transport: httpx.BaseTransport | None = None,
) -> httpx.Client:
    """Return an httpx.Client set up for the CMS."""
    # HINT 1: httpx.Client(base_url=..., headers={...}, timeout=...,
    #         transport=...) takes all four as keyword arguments.
    # HINT 2: httpx.Timeout(timeout_s, connect=3.0): the first number is
    #         the default for every phase, connect= overrides one phase.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 3: is_retryable
# What:    should a response with this status code be tried again?
# Input:   503 -> True, 429 -> True, 404 -> False, 200 -> False
# Practises: Concept 3 (what to retry), Day 22 status codes.
# ---------------------------------------------------------------------------
def is_retryable(status_code: int) -> bool:
    """Return True for rate limits and temporary server errors."""
    # HINT 1: one line. The set you need is already defined above.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 4: backoff_delay
# What:    how many seconds to wait before the next attempt.
# Input:   attempt = the attempt that just failed (1, 2, 3 ...);
#          retry_after = the response's Retry-After header, or None.
# Output:  backoff_delay(1) -> 0.5, (2) -> 1.0, (3) -> 2.0, (6) -> 8.0
#          backoff_delay(1, retry_after="3")   -> 3.0
#          backoff_delay(1, retry_after="45")  -> 45.0  (the server decides)
#          backoff_delay(1, retry_after="900") -> 60.0  (max_retry_after)
#          backoff_delay(2, retry_after="soon") -> 1.0  (unreadable: ignore)
# Practises: Concept 3 (exponential backoff, Retry-After).
# ---------------------------------------------------------------------------
def backoff_delay(
    attempt: int,
    retry_after: str | None = None,
    base: float = 0.5,
    cap: float = 8.0,
    max_retry_after: float = 60.0,
) -> float:
    """Return the wait in seconds before the next attempt."""
    # HINT 1: Retry-After can be a number of seconds or an HTTP date. Only
    #         use it when retry_after is not None and .strip().isdigit().
    #         Then wait what the server asked, but never more than
    #         max_retry_after: min(float(value), max_retry_after).
    # HINT 2: otherwise min(cap, base * 2 ** (attempt - 1)).
    # HINT 3: return a float: float("3") is 3.0.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 5: get_json
# What:    GET one URL and return the parsed JSON, retrying what is safe.
# Input:   get_json(client, "/content_types/page/entries", {"limit": 2})
# Output:  the response body as a dict, e.g. {"items": [...],
#          "next_cursor": "c2"}
# Rules:   up to max_attempts tries in total.
#          httpx.TransportError (timeouts, connection errors) -> retry.
#          2xx -> return response.json().
#          retryable status -> retry, waiting backoff_delay(attempt,
#          Retry-After header).
#          any other status (401, 404, 422 ...) -> FetchError at once,
#          message contains the status code, no retry.
#          out of attempts -> FetchError (message contains the last status
#          code or the exception name); do NOT sleep after the last attempt.
#          Before each wait: log.warning("retry %d/%d for %s after %s;
#          waiting %.1fs", attempt, max_attempts, path, reason, wait)
#          where reason is the status code or type(exc).__name__.
# Practises: Concepts 2 and 3; Day 4 exceptions; injecting sleep.
# ---------------------------------------------------------------------------
def get_json(
    client: httpx.Client,
    path: str,
    params: dict,
    max_attempts: int = 4,
    sleep: Callable[[float], None] = time.sleep,
) -> dict:
    """GET path with retries; return the JSON body or raise FetchError."""
    # HINT 1: for attempt in range(1, max_attempts + 1): ... (Concept 3).
    # HINT 2: put ONLY client.get(path, params=params) inside try/except
    #         httpx.TransportError. A wide try block hides your own bugs.
    # HINT 3: response.is_success is True for 2xx. Check it first.
    # HINT 4: a status that is_retryable() rejects means "stop now".
    # HINT 5: "attempt == max_attempts" is the moment to raise FetchError
    #         instead of sleeping. Use "raise FetchError(...) from exc"
    #         when you have an exception to chain.
    # HINT 6: response.headers.get("Retry-After") is None when absent;
    #         header names are case-insensitive in httpx.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 6: iter_entries
# What:    a GENERATOR that yields every valid Entry of a content type,
#          page by page, following next_cursor until it is null.
# Input:   iter_entries(client, "page", page_size=2)
# Output:  yields Entry objects; with cms_entries.json the uids are
#          blt001, blt002, blt004, blt006 (blt003 and blt005 are invalid).
# Rules:   path is f"/content_types/{content_type}/entries".
#          params: {"limit": page_size} on the first page, plus
#          "cursor": <value> on later pages. Never send cursor=None.
#          an item that from_api() rejects -> log.warning("skipping bad
#          item: %s", exc) and carry on.
#          a cursor you have already seen -> FetchError mentioning "cursor".
#          more than max_pages pages -> FetchError.
# Practises: Concept 4 (cursor pagination, generators), Day 11.
# ---------------------------------------------------------------------------
def iter_entries(
    client: httpx.Client,
    content_type: str,
    page_size: int = 2,
    max_pages: int = 50,
    sleep: Callable[[float], None] = time.sleep,
) -> Iterator[Entry]:
    """Yield every valid Entry of content_type, one page at a time."""
    # HINT 1: GOTCHA from Check your understanding 3: params={"cursor":
    #         None} sends "cursor=" (an empty value), and the fake CMS
    #         answers 422. Build the params dict, then add the cursor key
    #         only when you have one.
    # HINT 2: for page_number in range(max_pages): ... gives you the page
    #         limit for free; falling out of the loop means "too many".
    # HINT 3: keep a set() of cursors you have seen (Day 3 sets).
    # HINT 4: pass sleep through to get_json, so tests stay instant.
    # HINT 5: "yield entry" inside the loop; a bare "return" ends it.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 7: fetch_all
# What:    the one call Day 31 will use: all valid entries as a list.
# Input:   fetch_all(client, "page", page_size=3)
# Output:  [Entry, Entry, Entry, Entry] for cms_entries.json
# Rules:   then log.info("fetched %d %s entries", count, content_type).
# Practises: consuming a generator (Concept 4).
# ---------------------------------------------------------------------------
def fetch_all(
    client: httpx.Client,
    content_type: str,
    page_size: int = 2,
    sleep: Callable[[float], None] = time.sleep,
) -> list[Entry]:
    """Return every valid Entry of content_type as a list."""
    # HINT 1: list(some_generator) runs it to the end.
    # HINT 2: pass page_size and sleep through by keyword.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# Demo (given). Runs only with "python fetch.py", not on import.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import json
    from pathlib import Path

    from mock_cms import FakeCMS

    logging.basicConfig(level=logging.INFO,
                        format="%(levelname)s %(message)s")
    # FDE TIP: httpx logs every request at INFO; quiet it in demos
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # build the path from this file, so it works from any folder (Day 4)
    data_file = Path(__file__).parent / "cms_entries.json"
    items = json.loads(data_file.read_text(encoding="utf-8"))
    cms = FakeCMS(items, fail_first=1)  # the first call answers 503

    with build_client(DEFAULT_BASE_URL, "test-token",
                      transport=cms.transport) as client:
        # a no-op sleep: the demo should not really wait
        entries = fetch_all(client, "page", page_size=2,
                            sleep=lambda seconds: None)

    for e in entries:
        print(e.uid, e.locale, e.updated_at.isoformat(), e.title,
              list(e.tags))
    print(len(cms.requests), "requests")

    # Expected output:
    # WARNING retry 1/4 for /content_types/page/entries after 503; waiting 0.5s
    # WARNING skipping bad item: entry 'blt003': title is empty
    # WARNING skipping bad item: entry 'blt005': updated_at has no timezone
    # INFO fetched 4 page entries
    # blt001 en-us 2026-11-20T09:30:00+00:00 Winter Sale ['sale', 'winter']
    # blt002 en-us 2026-11-18T14:00:00+05:30 Store Locator []
    # blt004 fr-fr 2026-11-21T11:15:00+00:00 Soldes d'hiver ['sale']
    # blt006 en-us 2026-11-22T16:45:00+00:00 Gift Cards []
    # 4 requests
