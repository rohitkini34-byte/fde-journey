"""Day 11 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Iterators and the iteration protocol =====
# The iteration protocol by hand: what a for loop does under the hood
locales = ["en-us", "fr-fr", "hi-in"]  # a list is an ITERABLE
it = iter(locales)  # ask it for an ITERATOR: an object with a position
print(next(it))  # -> en-us
print(next(it))  # -> fr-fr
print(next(it))  # -> hi-in
try:
    next(it)  # nothing left: the iterator signals "done" by raising
except StopIteration:
    print("done")  # -> done
# JS: it.next() gives {value, done}; Python raises StopIteration

# ===== section: Concept 1: Iterators and the iteration protocol =====
# Iterators are ONE-SHOT; iterables give a fresh iterator each time
uids = ["blt001", "blt002", "blt003"]
it = iter(uids)
print(list(it))  # -> ['blt001', 'blt002', 'blt003']
print(list(it))  # -> []  (already used up; it never rewinds)
print(list(uids), list(uids))  # a list hands out a NEW iterator per loop
# -> ['blt001', 'blt002', 'blt003'] ['blt001', 'blt002', 'blt003']

# Many built-ins return iterators, not lists:
pairs = zip(["a", "b"], [1, 2])  # like a lazy Array.prototype.map pairing
print(pairs)  # -> <zip object at 0x...>  (a zip object, not a list)
print(dict(pairs))  # -> {'a': 1, 'b': 2}
print(dict(pairs))  # -> {}  GOTCHA: the zip was used up by the line above

# ===== section: Concept 1: Iterators and the iteration protocol =====
# A file object is an iterator over lines: it reads one line at a time
from pathlib import Path

path = Path("entries.jsonl")
path.write_text('{"uid": "blt001"}\n{"uid": "blt002"}\n', encoding="utf-8")

with open(path, encoding="utf-8") as f:
    print(iter(f) is f)  # -> True  (a file IS its own iterator)
    for line_no, line in enumerate(f, start=1):  # only 1 line in memory
        print(line_no, line.strip())
# -> 1 {"uid": "blt001"}
# -> 2 {"uid": "blt002"}

# ===== section: Concept 1: Iterators and the iteration protocol =====
# Your own iterator class: __iter__ returns self, __next__ gives the next
class PageNumbers:
    """Yields page numbers 1..last, like a CMS paginator."""

    def __init__(self, last: int):
        self.last = last
        self.current = 0  # the position lives INSIDE the iterator

    def __iter__(self):  # like [Symbol.iterator]() in JavaScript
        return self

    def __next__(self) -> int:
        if self.current >= self.last:
            raise StopIteration  # tells the for loop to stop
        self.current += 1
        return self.current


for page in PageNumbers(3):
    print("fetch page", page)
# -> fetch page 1
# -> fetch page 2
# -> fetch page 3

# ===== section: Concept 2: Generators, lazy pipelines that stream data =====
# A generator function: "yield" makes Python build the iterator for you
def page_numbers(last: int):
    print("  (generator starts)")  # runs only when the first value is asked
    for n in range(1, last + 1):
        yield n  # hand out n, then PAUSE here until next() is called again
    print("  (generator ends)")  # falling off the end = StopIteration


gen = page_numbers(2)  # nothing runs yet: you only get a generator object
print(type(gen).__name__)  # -> generator
print(next(gen))  # -> "(generator starts)" is printed, then 1
print(next(gen))  # -> 2
print(list(gen))  # -> "(generator ends)" is printed, then []
# JS: the same idea as function* pageNumbers() { yield n } in JavaScript

# ===== section: Concept 2: Generators, lazy pipelines that stream data =====
# Memory: a list holds every item; a generator holds only its position
import sys

squares_list = [n * n for n in range(1_000_000)]  # builds 1M ints now
squares_gen = (n * n for n in range(1_000_000))  # () = generator expression

print(sys.getsizeof(squares_list) > 8_000_000)  # -> True  (about 8 MB)
print(sys.getsizeof(squares_gen))  # -> 200  (bytes, on Python 3.13)
print(sum(squares_gen))  # -> 333332833333500000  (values made one by one)
# The generator's size is the same for 10 items or 10 billion.
# REMEMBER: [ ] builds everything now; ( ) makes items on demand

# ===== section: Concept 2: Generators, lazy pipelines that stream data =====
# A streaming pipeline: each stage pulls ONE record through at a time
import json
from collections.abc import Iterator
from pathlib import Path

path = Path("export.jsonl")
lines = [
    '{"uid": "blt001", "title": "SSO guide", "status": "published"}',
    '{"uid": "blt002", "title": "Draft FAQ", "status": "draft"}',
    "",
    '{"uid": "blt003", "title": "Pricing", "status": "published"}',
]
path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def read_records(p: Path) -> Iterator[dict]:
    # Iterator[dict] = "yields dicts"; the hint for any generator
    with open(p, encoding="utf-8") as f:
        for line in f:
            if line.strip():  # skip blank lines
                yield json.loads(line)  # like JSON.parse(line) in JS


def published(records: Iterator[dict]) -> Iterator[dict]:
    for r in records:
        if r["status"] == "published":
            yield r


def titles(records: Iterator[dict]) -> Iterator[str]:
    for r in records:
        print("  title for", r["uid"])  # shows WHEN each record flows
        yield r["title"]


pipeline = titles(published(read_records(path)))  # nothing read yet
for t in pipeline:  # the for loop pulls records through all 3 stages
    print(t)
# ->   title for blt001
# -> SSO guide
# ->   title for blt003
# -> Pricing

# ===== section: Concept 2: Generators, lazy pipelines that stream data =====
# Tools for generators: islice, batched, yield from
from itertools import batched, islice  # batched needs Python 3.12+

uids = (f"blt{n:03}" for n in range(1, 8))  # 7 lazy uids: blt001..blt007
print(list(islice(uids, 2)))  # -> ['blt001', 'blt002']  (first 2 only)
for batch in batched(uids, 2):  # continues where islice stopped
    print(batch)  # tuples of up to 2, like chunks for a bulk API call
# -> ('blt003', 'blt004')
# -> ('blt005', 'blt006')
# -> ('blt007',)  (the last batch can be shorter)


def all_entries(pages):
    for page in pages:
        yield from page  # same as: for e in page: yield e


print(list(all_entries([["e1", "e2"], ["e3"]])))  # -> ['e1', 'e2', 'e3']

# ===== section: Concept 3: Decorators, adding behaviour without editing the function =====
# Step 1: functions are objects; a closure remembers its outer variables
def make_counter():
    count = 0  # lives on after make_counter returns, inside the closure

    def counter():
        nonlocal count  # "use the outer count", not a new local one
        count += 1
        return count

    return counter  # return the function itself, not counter()


tick = make_counter()
print(tick(), tick(), tick())  # -> 1 2 3
# JS: the same closure pattern as useState's setter capturing state

# ===== section: Concept 3: Decorators, adding behaviour without editing the function =====
# Step 2: a decorator takes a function and returns a wrapped version
import functools
import time


def timed(func):
    @functools.wraps(func)  # copy func's name and docstring to wrapper
    def wrapper(*args, **kwargs):  # accept ANY arguments and pass them on
        start = time.perf_counter()
        try:
            return func(*args, **kwargs)  # call the real function
        finally:  # runs even if func raises: we still log the time
            ms = (time.perf_counter() - start) * 1000
            print(f"{func.__name__} took {ms:.0f} ms")

    return wrapper


@timed  # same as: fetch_entry = timed(fetch_entry)
def fetch_entry(uid: str) -> dict:
    """Pretend to call the CMS."""
    time.sleep(0.05)
    return {"uid": uid}


print(fetch_entry("blt001"))
# -> fetch_entry took 50 ms
# -> {'uid': 'blt001'}
print(fetch_entry.__name__, "|", fetch_entry.__doc__)
# -> fetch_entry | Pretend to call the CMS.
# React: the same idea as a higher-order component, withAuth(Page)

# ===== section: Concept 3: Decorators, adding behaviour without editing the function =====
# Step 3: a decorator WITH arguments is a function that returns a decorator
import functools
import os


def require_env(*names: str):  # layer 1: takes the settings
    def decorator(func):  # layer 2: takes the function
        @functools.wraps(func)
        def wrapper(*args, **kwargs):  # layer 3: runs on every call
            missing = [n for n in names if not os.environ.get(n)]
            if missing:
                raise RuntimeError(f"missing env vars: {', '.join(missing)}")
            return func(*args, **kwargs)

        return wrapper

    return decorator


@require_env("CMS_API_KEY", "CMS_BASE_URL")  # note the () with arguments
def export_entries() -> str:
    return "exported"


os.environ["CMS_BASE_URL"] = "https://cms.test"
try:
    export_entries()
except RuntimeError as err:
    print(err)  # -> missing env vars: CMS_API_KEY
os.environ["CMS_API_KEY"] = "demo-key"
print(export_entries())  # -> exported

# ===== section: Concept 3: Decorators, adding behaviour without editing the function =====
# A decorator runs ONCE, when the def line runs; the wrapper runs per call
def register(func):
    print("registering", func.__name__)  # happens at definition time
    HANDLERS[func.__name__] = func  # e.g. a webhook event -> handler map
    return func  # return the original: nothing is wrapped


HANDLERS = {}


@register  # -> registering entry_published  (printed right here)
def entry_published(payload: dict) -> str:
    return f"reindex {payload['uid']}"


print(HANDLERS["entry_published"]({"uid": "blt001"}))  # -> reindex blt001

# ===== section: Concept 4: Context managers and the with statement =====
# A context manager class: __enter__ runs at "with", __exit__ at the end
import time


class Timer:
    def __enter__(self):
        self.start = time.perf_counter()
        return self  # this value is what "as t" receives

    def __exit__(self, exc_type, exc, tb):
        # called on EVERY exit: normal end, return, or an exception
        self.ms = (time.perf_counter() - self.start) * 1000
        print(f"block took {self.ms:.0f} ms, error: {exc_type}")
        return False  # False = do not hide the error, let it propagate


with Timer() as t:
    time.sleep(0.02)
# -> block took 20 ms, error: None

try:
    with Timer():
        raise ValueError("bad entry")
except ValueError as err:
    print("caught:", err)
# -> block took 0 ms, error: <class 'ValueError'>
# -> caught: bad entry

# ===== section: Concept 4: Context managers and the with statement =====
# @contextmanager: write a context manager as a generator with ONE yield
import os
from contextlib import contextmanager
from pathlib import Path


@contextmanager
def atomic_write(path: Path):
    """Write to a temp file; replace the real file only on success."""
    tmp = path.with_suffix(path.suffix + ".tmp")
    f = open(tmp, "w", encoding="utf-8")
    try:
        yield f  # the body of the "with" block runs here
    except BaseException:
        f.close()
        tmp.unlink()  # failed: delete the half-written temp file
        raise  # and re-raise, so the caller still sees the error
    else:
        f.close()
        os.replace(tmp, path)  # success: swap it in (Day 4's safe save)


target = Path("contacts.json")
target.write_text("OLD", encoding="utf-8")

with atomic_write(target) as f:
    f.write("NEW")
print(target.read_text(encoding="utf-8"))  # -> NEW

try:
    with atomic_write(target) as f:
        f.write("HALF")
        raise RuntimeError("CMS went down mid-export")
except RuntimeError:
    pass
print(target.read_text(encoding="utf-8"))  # -> NEW  (old file kept)
print(sorted(p.name for p in Path(".").glob("contacts*")))
# -> ['contacts.json']  (no .tmp left behind)

# ===== section: Concept 4: Context managers and the with statement =====
# The with statement you already use: files, locks, sessions, tempdirs
import tempfile
from pathlib import Path

import requests  # Day 6

with tempfile.TemporaryDirectory() as tmp:  # folder deleted at the end
    p = Path(tmp) / "a.txt"
    p.write_text("hi", encoding="utf-8")
    print(p.exists())  # -> True
print(p.exists())  # -> False  (cleanup ran when the block ended)

with requests.Session() as session:  # closes its connections at the end
    print(type(session).__name__)  # -> Session

# Two managers in one with, closed in reverse order (last opened first)
with (
    open("in.txt", "w", encoding="utf-8") as a,  # () allowed: Python 3.10+
    open("out.txt", "w", encoding="utf-8") as b,
):
    print(a.closed, b.closed)  # -> False False
print(a.closed, b.closed)  # -> True True

# ===== section: Check your understanding (predict first, then run) =====
# Day 11 check: write a prediction for each numbered part, then run
from contextlib import contextmanager
from pathlib import Path

# 1 generators are one-shot
sizes = (len(w) for w in ["sso", "seo", "cdn"])
print(sum(sizes), sum(sizes))

# 2 laziness: what prints, and in what order?
def numbers():
    for n in [1, 2, 3]:
        print("make", n)
        yield n

first = next(n for n in numbers() if n > 1)
print("first:", first)

# 3 a decorator without functools.wraps
def shout(func):
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).upper()
    return wrapper

@shout
def greet(name):
    """Say hello."""
    return f"hello {name}"

print(greet("rohit"), greet.__name__, greet.__doc__)

# 4 does the error escape the with block?
@contextmanager
def quiet():
    try:
        yield
    except KeyError:
        print("swallowed")

with quiet():
    {}["missing"]
print("after 4")

# 5 a generator returned from inside a with block
Path("t.txt").write_text("a\nb\n", encoding="utf-8")

def read_lines(path):
    with open(path, encoding="utf-8") as f:
        return (line.strip() for line in f)

try:
    print(list(read_lines("t.txt")))
except ValueError as err:
    print("ValueError:", err)
