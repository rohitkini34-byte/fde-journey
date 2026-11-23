"""Day 22 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: What HTTP is, and how to see it with curl =====
# HTTP is just text over a network connection. Send it by hand once.
import json
import socket  # low-level network connections; requests/fetch hide this

# 1. Open a TCP connection to the mock server (like dialling a number).
conn = socket.create_connection(("127.0.0.1", 8022))

# 2. A request is a request line, headers, then a blank line.
#    "\r\n" ends every line; the empty line means "headers are done".
request = (
    "GET /v1/entries/blt001 HTTP/1.1\r\n"  # method, path, HTTP version
    "Host: 127.0.0.1:8022\r\n"             # which site (required in 1.1)
    "X-API-Key: acme-dev-key\r\n"          # our credential (Concept 4)
    "Connection: close\r\n"                # close after one response
    "\r\n"
)
conn.sendall(request.encode())  # the network carries bytes, not str

# 3. Read everything the server sends back until it closes.
raw = b""
while chunk := conn.recv(4096):  # recv returns b"" when the server is done
    raw += chunk
conn.close()

head, body = raw.decode().split("\r\n\r\n", 1)  # blank line splits them
print(head)
# -> HTTP/1.1 200 OK                       <- status line
# -> Server: AcmeMock/1.0 Python/3.13.18
# -> Date: Sun, 15 Nov 2026 02:20:11 GMT
# -> X-Request-Id: req_5c1f0a9e            <- random on every call
# -> ETag: "v1"
# -> Cache-Control: max-age=60
# -> Content-Type: application/json
# -> Content-Length: 191                   <- body size in bytes
print(json.loads(body)["title"])  # -> Diwali sale guide

# ===== section: Concept 3: Status codes and error bodies =====
# Decide what to do from the status code, the way a careful client does.
import time

import requests  # Day 6; like fetch() but with resp.status_code built in

BASE = "http://127.0.0.1:8022"
KEY = {"X-API-Key": "acme-dev-key"}


def what_to_do(status: int) -> str:
    """Map a status code to the client's next move."""
    if 200 <= status < 300:
        return "success: use the body"
    if status in (408, 429) or status >= 500:
        return "temporary: wait and retry"  # the server may recover
    return "permanent: fix the request, do not retry"  # other 4xx


for path, headers in [
    ("/health", {}),                    # no key needed
    ("/v1/entries", {}),                # forgot the key
    ("/v1/entries/blt999", KEY),        # uid that does not exist
    ("/v1/entries?limit=500", KEY),     # limit outside 1..50
]:
    r = requests.get(BASE + path, headers=headers, timeout=5)
    print(r.status_code, what_to_do(r.status_code))
# -> 200 success: use the body
# -> 401 permanent: fix the request, do not retry
# -> 404 permanent: fix the request, do not retry
# -> 422 permanent: fix the request, do not retry

# Error bodies share one shape, so one code path can log them all.
err = requests.get(BASE + "/v1/entries", timeout=5)
print(err.headers["content-type"])  # -> application/problem+json
print(err.json()["detail"])  # -> Missing or unknown X-API-Key


def get_with_retry(url: str, tries: int = 4) -> requests.Response:
    """GET, retrying 429/503 and honouring the Retry-After header."""
    for attempt in range(1, tries + 1):
        r = requests.get(url, headers=KEY, timeout=5)
        if r.status_code not in (429, 503) or attempt == tries:
            return r
        # Retry-After is in seconds here; fall back to 1 if missing.
        wait = int(r.headers.get("Retry-After", "1"))
        print(f"attempt {attempt}: {r.status_code}, waiting {wait}s")
        time.sleep(wait)
    raise AssertionError("unreachable")


r = get_with_retry(BASE + "/v1/reports/views")
print(r.status_code, r.json())
# -> attempt 1: 503, waiting 1s
# -> attempt 2: 503, waiting 1s
# -> 200 {'views_last_7_days': 18240}

# ===== section: Concept 5: Idempotency keys and pagination =====
# A retried POST without and with an Idempotency-Key.
import uuid

import requests

URL = "http://127.0.0.1:8022/v1/entries"
KEY = {"X-API-Key": "acme-dev-key"}
entry = {"title": "Winter sale banner", "content_type": "product_page"}


def count_titled(title: str) -> int:
    """How many entries on the server have this title?"""
    r = requests.get(URL, headers=KEY, params={"limit": 50}, timeout=5)
    return sum(e["title"] == title for e in r.json()["items"])


# Imagine the first response was lost (timeout), so the client retries.
for _ in range(2):
    requests.post(URL, headers=KEY, json=entry, timeout=5)
print(count_titled("Winter sale banner"))  # -> 2   <- a duplicate entry

# Same story, but the client sends ONE key for both attempts.
op_key = str(uuid.uuid4())  # made once per logical operation, not per try
entry2 = {"title": "Spring sale banner", "content_type": "product_page"}
for attempt in range(2):
    # json= sets Content-Type: application/json and encodes the dict
    r = requests.post(URL, json=entry2, timeout=5,
                      headers={**KEY, "Idempotency-Key": op_key})
    print(attempt, r.status_code, r.json()["uid"],
          r.headers.get("Idempotent-Replayed"))
# -> 0 201 blt011 None
# -> 1 201 blt011 true    <- same answer replayed, nothing new created
print(count_titled("Spring sale banner"))  # -> 1

# ===== section: Concept 5: Idempotency keys and pagination =====
# Why offset pagination breaks while data changes, and how cursors fix it.

# The "server" holds entries sorted newest first, like a CMS list view.
entries = ["e8", "e7", "e6", "e5", "e4", "e3", "e2", "e1"]


def page_by_offset(offset: int, limit: int) -> list[str]:
    """LIMIT/OFFSET from Day 15: skip `offset` rows, take `limit`."""
    return entries[offset:offset + limit]


first = page_by_offset(0, 3)
print(first)  # -> ['e8', 'e7', 'e6']

# Between our two calls an editor publishes a new entry at the top.
entries.insert(0, "e9")

second = page_by_offset(3, 3)
print(second)  # -> ['e6', 'e5', 'e4']   <- e6 appears twice!
# GOTCHA: an item deleted between calls makes one get skipped instead.


def page_by_cursor(after: str | None, limit: int) -> list[str]:
    """Keyset pagination: continue after the last item we saw."""
    start = 0 if after is None else entries.index(after) + 1
    return entries[start:start + limit]


# The cursor is "the last item of the previous page", not a row count,
# so a new entry at the top cannot shift what comes next.
print(page_by_cursor("e6", 3))  # -> ['e5', 'e4', 'e3']
# REMEMBER: offset says "skip N rows"; a cursor says "after this row".

# ===== section: Concept 5: Idempotency keys and pagination =====
# Fetch every page from the mock API by following next_cursor.
import requests

BASE = "http://127.0.0.1:8022"
KEY = {"X-API-Key": "acme-dev-key"}


def fetch_all(content_type: str, limit: int = 2) -> list[dict]:
    """Collect all entries of one content type, page by page."""
    items: list[dict] = []
    params = {"content_type": content_type, "limit": limit}
    while True:
        # params= builds and encodes the query string for us,
        # like new URLSearchParams(obj) in JS.
        r = requests.get(BASE + "/v1/entries", headers=KEY,
                         params=params, timeout=5)
        r.raise_for_status()  # turn any 4xx/5xx into an exception
        page = r.json()
        items.extend(page["items"])
        print(f"got {len(page['items'])}, next={page['next_cursor']}")
        if page["next_cursor"] is None:  # no more pages
            return items
        params["cursor"] = page["next_cursor"]  # FDE TIP: never decode it


blogs = fetch_all("blog_post")
# -> got 2, next=Ymx0MDAy
# -> got 2, next=None      <- the server knew there was nothing left
print([e["uid"] for e in blogs])
# -> ['blt001', 'blt002', 'blt005', 'blt008']
