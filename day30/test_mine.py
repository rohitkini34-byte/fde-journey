"""Day 30: three tests of your own for fetch.py (acceptance criterion 2).

Writing tests for the unhappy paths is the habit that separates a demo from
something a customer can run. Each test below has a brief and hints; replace
the pytest.skip(...) line with your test body.

Run inside day30/:   python -m pytest -q test_mine.py
"""

import httpx
import pytest

# these imports are for the tests you write (unused until then)
from fetch import (
    DEFAULT_BASE_URL,
    FetchError,
    build_client,
    fetch_all,
    get_json,
)
from mock_cms import FakeCMS

PATH = "/content_types/page/entries"
ONE_ITEM = [{"uid": "blt100", "title": "Home",
             "updated_at": "2026-11-23T08:00:00Z"}]


# ---------------------------------------------------------------------------
# test_wrong_token_fails_fast
# Brief:   a client with the wrong token gets FetchError whose message
#          contains "401", after exactly ONE request and no sleeps.
# Practises: Concept 5 (assert on the requests too), Concept 3 (never
#          retry a 4xx).
# ---------------------------------------------------------------------------
def test_wrong_token_fails_fast():
    # HINT 1: cms = FakeCMS(ONE_ITEM); build_client(DEFAULT_BASE_URL,
    #         "wrong", transport=cms.transport)
    # HINT 2: slept = [] and pass sleep=slept.append to get_json.
    # HINT 3: with pytest.raises(FetchError, match="401"): ...
    # HINT 4: afterwards check len(cms.requests) and slept.
    pytest.skip("TODO: write this test")


# ---------------------------------------------------------------------------
# test_four_timeouts_give_up
# Brief:   if every attempt times out, get_json raises FetchError after
#          max_attempts=4 requests and 3 sleeps of 0.5, 1.0 and 2.0 s.
# Practises: Concept 2 (timeouts are exceptions), Concept 3.
# ---------------------------------------------------------------------------
def test_four_timeouts_give_up():
    # HINT 1: FakeCMS(ONE_ITEM, timeout_first=10) times out on calls 1-10.
    # HINT 2: compare slept with a list, not one value at a time.
    pytest.skip("TODO: write this test")


# ---------------------------------------------------------------------------
# test_empty_first_page_gives_empty_list
# Brief:   a content type with no entries gives [] without an error.
# Practises: Concept 4 (stop conditions), writing your own handler.
# ---------------------------------------------------------------------------
def test_empty_first_page_gives_empty_list():
    # HINT 1: the easiest fake is FakeCMS([]). For extra practice, write
    #         your own handler(request) that returns
    #         httpx.Response(200, json={"items": [], "next_cursor": None})
    #         and pass transport=httpx.MockTransport(handler).
    # HINT 2: fetch_all(client, "page") should equal [].
    pytest.skip("TODO: write this test")
