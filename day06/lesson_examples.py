"""Day 6 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Recap (2 minutes, from memory) =====
# Recap: predict the output before running.
from dataclasses import dataclass, field


@dataclass
class Entry:
    uid: str
    tags: list[str] = field(default_factory=list)


a = Entry("blt1")
b = Entry("blt1")
a.tags.append("sso")
print(a == b, b.tags)

# ===== section: Concept 1: Virtual environments =====
# Am I inside a virtual environment? Which Python is running me?
import sys

# sys.prefix is the folder of the Python running this code; base_prefix
# is the "real" install it came from. Different means: inside a venv.
print(sys.prefix != sys.base_prefix)  # -> True in .venv, False outside
print(sys.executable)  # -> .../day06/.venv/bin/python (path varies)

import requests  # works only if installed in THIS env

print(requests.__version__)  # -> 2.34.2 (or whatever you installed)

# ===== section: Concept 3: HTTP, the conversation every API uses =====
# Your first HTTP request: look at every part of the response.
import requests  # the standard HTTP client, like fetch() in JS

BASE = "http://127.0.0.1:8006"  # the mock CMS (other terminal)

r = requests.get(f"{BASE}/health", timeout=5)  # GET = "please give me"
print(r.status_code)  # -> 200  (2xx means success)
print(r.headers["Content-Type"])  # -> application/json; charset=utf-8
print(r.text)  # -> {"status": "ok"}   (the raw body, a str)
data = r.json()  # parse the JSON body, like await res.json() in JS
print(data["status"], type(data))  # -> ok <class 'dict'>
print(r.ok, r.elapsed.total_seconds() < 1)  # -> True True

# ===== section: Concept 3: HTTP, the conversation every API uses =====
# The same API without the key: a 4xx is still a normal response.
import requests

BASE = "http://127.0.0.1:8006"
url = f"{BASE}/v3/content_types/blog_post/entries"

r = requests.get(url, timeout=5)  # no api_key header this time
print(r.status_code, r.ok)  # -> 401 False
print(r.json())  # -> {'error_message': 'Invalid API key', ...}
# GOTCHA: requests did NOT raise an error. A 401 or 500 is a valid HTTP
# reply, so your code keeps going unless YOU check the status.

r = requests.get(url, headers={"api_key": "demo-key-123"}, timeout=5)
print(r.status_code, len(r.json()["entries"]))  # -> 200 5

# ===== section: Concept 4: requests the production way =====
# Query parameters, headers and the final URL.
import requests

BASE = "http://127.0.0.1:8006"
url = f"{BASE}/v3/content_types/blog_post/entries"
headers = {"api_key": "demo-key-123"}  # a header, not part of the URL
# params: requests builds "?skip=0&limit=2&include_count=true" for you
params = {"skip": 0, "limit": 2, "include_count": "true"}

r = requests.get(url, params=params, headers=headers, timeout=5)
print(r.url)
# -> http://127.0.0.1:8006/v3/content_types/blog_post/entries?skip=0&...
body = r.json()
print(body["count"], [e["uid"] for e in body["entries"]])
# -> 8 ['blt001', 'blt002']
# FDE TIP: never glue user input into URLs by hand. params= encodes
# spaces, & and = safely, the way URLSearchParams does in JS.
print(requests.Request("GET", url, params={"q": "a&b c"}).prepare().url)
# -> http://127.0.0.1:8006/v3/content_types/blog_post/entries?q=a%26b+c

# ===== section: Concept 4: requests the production way =====
# raise_for_status() and the three failures every API client must handle.
import requests

BASE = "http://127.0.0.1:8006"
KEY = {"api_key": "demo-key-123"}


def get_json(path: str, headers: dict, timeout: float = 5) -> dict:
    """GET a path and return the JSON body, or raise a requests error."""
    r = requests.get(f"{BASE}{path}", headers=headers, timeout=timeout)
    r.raise_for_status()  # turns a 4xx/5xx reply into an HTTPError
    return r.json()


try:  # 1. the server answered, but with an error status
    get_json("/v3/content_types/blog_post/entries", headers={})
except requests.HTTPError as err:
    print("HTTP error:", err.response.status_code)  # -> HTTP error: 401
    print(err.response.json()["error_message"])  # -> Invalid API key

try:  # 2. the server is too slow (/slow takes 3 s, we wait 1 s)
    get_json("/slow", headers=KEY, timeout=1)
except requests.Timeout:
    print("timed out")  # -> timed out

try:  # 3. nothing is listening on that port at all
    requests.get("http://127.0.0.1:8999/health", timeout=2)
except requests.ConnectionError as err:
    print("cannot connect:", type(err).__name__)
    # -> cannot connect: ConnectionError

# REMEMBER: all three are children of requests.RequestException (Day 5's
# inheritance), so "except requests.RequestException" catches them all.
print(issubclass(requests.Timeout, requests.RequestException))  # -> True

# ===== section: Concept 4: requests the production way =====
# A Session reuses the connection and the headers for every call.
import requests

BASE = "http://127.0.0.1:8006"

# with: the session (and its open connections) closes automatically
with requests.Session() as session:
    # set once, sent on every request: like a configured axios instance
    session.headers.update({"api_key": "demo-key-123"})
    for skip in (0, 5):
        r = session.get(
            f"{BASE}/v3/content_types/blog_post/entries",
            params={"skip": skip, "limit": 5},
            timeout=5,  # GOTCHA: a Session has no default timeout either
        )
        r.raise_for_status()
        print(skip, [e["uid"] for e in r.json()["entries"]])
# -> 0 ['blt001', 'blt002', 'blt003', 'blt004', 'blt005']
# -> 5 ['blt006', 'blt007', 'blt008']

# ===== section: Concept 4: requests the production way =====
# Retry with backoff: try again only when trying again can help.
import time

import requests

BASE = "http://127.0.0.1:8006"
RETRY_STATUSES = {429, 500, 502, 503, 504}  # busy or broken right now


def get_with_retry(session: requests.Session, url: str, params: dict,
                   tries: int = 3, base_delay: float = 0.5) -> dict:
    """GET url; retry 429/5xx and connection errors, waiting longer."""
    for attempt in range(1, tries + 1):
        try:
            r = session.get(url, params=params, timeout=5)
        except requests.ConnectionError:
            if attempt == tries:
                raise  # out of tries: let the caller see the real error
            reason = "connection error"
        else:
            if r.status_code not in RETRY_STATUSES:
                r.raise_for_status()  # a 401 or 404 will not fix itself
                return r.json()
            if attempt == tries:
                r.raise_for_status()
            reason = f"HTTP {r.status_code}"
        delay = base_delay * 2 ** (attempt - 1)  # 0.5 s, 1 s, 2 s ...
        print(f"  {reason}, retry {attempt} of {tries - 1} in {delay}s")
        time.sleep(delay)
    raise RuntimeError("unreachable")  # loop always returns or raises


with requests.Session() as s:
    s.headers["api_key"] = "demo-key-123"
    url = f"{BASE}/v3/content_types/blog_post/entries"
    body = get_with_retry(s, url, {"skip": 3, "limit": 3})
    print([e["uid"] for e in body["entries"]])
# ->   HTTP 503, retry 1 of 2 in 0.5s
# -> ['blt004', 'blt005', 'blt006']

# ===== section: Concept 4: requests the production way =====
# Pagination: keep asking for the next page until you have everything.
import requests

BASE = "http://127.0.0.1:8006"
url = f"{BASE}/v3/content_types/blog_post/entries"
PAGE_SIZE = 5

all_entries: list[dict] = []
with requests.Session() as s:
    s.headers["api_key"] = "demo-key-123"
    skip = 0
    while True:  # Day 2's while loop: we do not know the page count yet
        params = {"skip": skip, "limit": PAGE_SIZE,
                  "include_count": "true"}
        r = s.get(url, params=params, timeout=5)
        r.raise_for_status()
        body = r.json()
        page = body["entries"]
        all_entries.extend(page)  # extend, not append (Day 3)
        print(f"skip={skip}: got {len(page)}, total {len(all_entries)}")
        # stop on an empty page OR once we hold everything the API has
        if not page or len(all_entries) >= body["count"]:
            break
        skip += len(page)  # move forward by what we actually received
# -> skip=0: got 5, total 5
# -> skip=5: got 3, total 8
print(len(all_entries), all_entries[-1]["uid"])  # -> 8 blt008

# ===== section: Concept 4: requests the production way =====
# A real public API: Mumbai's 3-day forecast from Open-Meteo (no key).
import requests

url = "https://api.open-meteo.com/v1/forecast"
params = {
    "latitude": 19.08,  # Mumbai
    "longitude": 72.88,
    "daily": "temperature_2m_max,temperature_2m_min",
    "timezone": "Asia/Kolkata",  # required when you ask for daily data
    "forecast_days": 3,
}
r = requests.get(url, params=params, timeout=10)
r.raise_for_status()
daily = r.json()["daily"]  # a dict of PARALLEL lists, one per field
# zip() walks several lists side by side, item i of each together
for day, hi, lo in zip(daily["time"], daily["temperature_2m_max"],
                       daily["temperature_2m_min"]):
    print(day, hi, lo)
# -> 2026-10-31 33.4 25.1   (live data: your dates and numbers differ)
# -> ...two more lines like it

# ===== section: Concept 5: CSV files, command-line tools and secrets =====
# Writing CSV safely with csv.DictWriter.
import csv
from pathlib import Path

rows = [
    {"uid": "blt001", "title": "Getting started with SSO",
     "tags": "sso|auth"},
    # a comma and quotes INSIDE a value: the csv module escapes them
    {"uid": "blt002",
     "title": 'Pricing FAQ: "Starter" vs "Pro", explained',
     "tags": "pricing"},
]
path = Path("posts_demo.csv")
# newline="": the csv module controls line endings (else blank lines on
# Windows). encoding="utf-8": accents survive. Both are Day 4 habits.
with open(path, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["uid", "title", "tags"])
    writer.writeheader()  # the first line: uid,title,tags
    writer.writerows(rows)  # one line per dict, fieldnames order

print(path.read_text(encoding="utf-8"))
# -> uid,title,tags
# -> blt001,Getting started with SSO,sso|auth
# -> blt002,"Pricing FAQ: ""Starter"" vs ""Pro"", explained",pricing

# ===== section: Concept 5: CSV files, command-line tools and secrets =====
# Reading CSV back: every value comes back as a str.
import csv

with open("posts_demo.csv", newline="", encoding="utf-8") as f:
    for row in csv.DictReader(f):  # each row: a dict keyed by header
        print(row["uid"], row["title"][:20], row["tags"].split("|"))
# -> blt001 Getting started with ['sso', 'auth']
# -> blt002 Pricing FAQ: "Starte ['pricing']
# GOTCHA: CSV has no types. A word_count of 820 comes back as "820", and
# True comes back as "True". Convert with int() when you read it.

# ===== section: Concept 5: CSV files, command-line tools and secrets =====
# argparse turns command-line words into a typed object.
import argparse
import os

parser = argparse.ArgumentParser(description="Export CMS entries.")
parser.add_argument("content_type")  # positional: required, no dashes
parser.add_argument("--out", default="export.csv")  # optional flag
parser.add_argument("--page-size", type=int, default=5)  # gives an int

# parse_args() normally reads sys.argv (what you typed in the terminal);
# passing a list lets us test it without a terminal.
args = parser.parse_args(["blog_post", "--page-size", "3"])
print(args.content_type, args.out, args.page_size)
# -> blog_post export.csv 3
print(type(args.page_size))  # -> <class 'int'>
# GOTCHA: "--page-size" becomes args.page_size (dash -> underscore)

# Secrets come from the environment, never from the code or the CLI args.
# os.environ is a dict of env variables, like process.env in Node.
key = os.environ.get("CMS_API_KEY")  # None if it was never set
print(key is None)  # -> True (until you run: export CMS_API_KEY=...)

# ===== section: Check your understanding (predict first, then run) =====
# Predict each output BEFORE you run this cell.
import csv
import io

import requests

BASE = "http://127.0.0.1:8006"
URL = f"{BASE}/v3/content_types/blog_post/entries"
KEY = {"api_key": "demo-key-123"}

# 1
r = requests.get(URL, timeout=5)
print(r.ok, r.status_code)

# 2
r = requests.get(URL, params={"skip": 0, "limit": 99}, headers=KEY,
                 timeout=5)
print(len(r.json()["entries"]))

# 3
buf = io.StringIO()  # a fake file in memory, handy for quick tests
csv.writer(buf).writerow(["a,b", 'say "hi"', 3])
print(buf.getvalue().strip())

# 4
row = next(csv.DictReader(io.StringIO("uid,published\nblt003,False\n")))
print(row["published"], bool(row["published"]))

# 5
try:
    e0 = requests.get(URL, headers=KEY, timeout=5).json()["entries"][0]
    e0["slug"]
except requests.RequestException:
    print("network problem")
except KeyError as err:
    print("missing field:", err)
