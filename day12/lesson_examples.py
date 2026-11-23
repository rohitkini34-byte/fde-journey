"""Day 12 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Modules, packages and the src layout =====
# Day 12: what "import" really does. Save as pricing.py, then run the
# two commands at the bottom from the same folder.
"""Tiny module used to show how imports and __name__ work."""

GST_RATE = 0.18  # top-level code runs once, at the first import

print("pricing loaded, __name__ =", __name__)  # runs on import too


def with_gst(amount: float) -> float:
    """Return the amount including 18% GST."""
    return round(amount * (1 + GST_RATE), 2)


# True only when the file is run directly: like require.main === module
if __name__ == "__main__":
    print(with_gst(100))

# $ python3 pricing.py
# -> pricing loaded, __name__ = __main__
# -> 118.0
# $ python3 -c "import pricing; import pricing; print(pricing.with_gst(50))"
# -> pricing loaded, __name__ = pricing   (once: imports are cached)
# -> 59.0

# ===== section: Concept 4: Logging, messages for the people who run your code =====
# Day 12: logging basics and where output goes (save as logdemo.py)
import logging
import sys

# one logger per module, named after it; in a real module, use __name__
logger = logging.getLogger("cms_export.reader")

# configure ONCE, in the program's entry point (main), never in a library
logging.basicConfig(
    level=logging.INFO,  # show INFO and above; DEBUG is dropped
    format="%(levelname)s %(name)s: %(message)s",
    stream=sys.stderr,  # messages on stderr, data on stdout (Day 9)
)

logger.debug("opened export file")  # below INFO: dropped, almost free
logger.info("read %d entries", 7)  # -> INFO cms_export.reader: read 7 entries
logger.warning("skipping line %d", 6)
# -> WARNING cms_export.reader: skipping line 6
logger.error("export file not found: %s", "nope.jsonl")
# -> ERROR cms_export.reader: export file not found: nope.jsonl
print("uid,title")  # -> uid,title   (stdout: the data channel)

# $ python3 logdemo.py 2>/dev/null    shows only:  uid,title
# $ python3 logdemo.py 1>/dev/null    shows only the three log lines

# ===== section: Concept 4: Logging, messages for the people who run your code =====
# Day 12: logger names form a tree; lazy formatting; logging exceptions
import json
import logging

logging.basicConfig(
    level=logging.INFO, format="%(levelname)s %(name)s: %(message)s"
)

reader_log = logging.getLogger("cms_export.reader")  # child of cms_export
cli_log = logging.getLogger("cms_export.cli")

# turn ONE part of the app down without touching the others
logging.getLogger("cms_export.reader").setLevel(logging.WARNING)
reader_log.info("hidden: the reader logger now needs WARNING")
cli_log.info("still shown")  # -> INFO cms_export.cli: still shown

# noisy third-party libraries are quietened the same way
logging.getLogger("urllib3").setLevel(logging.WARNING)

# FDE TIP: pass values as arguments, not f-strings; the text is built
# only if the message is actually shown
cli_log.debug("entry %s", {"uid": "blt001"})  # never formatted: DEBUG off

try:
    json.loads('{"uid": "blt005"')  # a broken line from the export
except json.JSONDecodeError:
    # .exception() = ERROR level + the full traceback; use it in except
    cli_log.exception("could not parse line %d", 6)
# -> ERROR cms_export.cli: could not parse line 6
# -> Traceback (most recent call last):
# ->   ... (the frames, as in any traceback)
# -> json.decoder.JSONDecodeError: Expecting ',' delimiter: line 1 ...

# ===== section: Concept 4: Logging, messages for the people who run your code =====
# Day 12: testing log output with pytest's built-in caplog fixture
# --- locale_fix.py (the module under test) ---
import logging

logger = logging.getLogger(__name__)


def pick_locale(entry: dict[str, str], default: str = "en-us") -> str:
    """Return the entry's locale, or the default with a warning."""
    if not entry.get("locale"):
        logger.warning("%s has no locale, using %s", entry["uid"], default)
        return default
    return entry["locale"]


# --- test_locale_fix.py ---
import logging

import pytest

from locale_fix import pick_locale


def test_warns_when_locale_missing(caplog: pytest.LogCaptureFixture) -> None:
    # caplog collects every log record made during the test
    with caplog.at_level(logging.WARNING):  # make sure WARNING is shown
        assert pick_locale({"uid": "blt006"}) == "en-us"
    assert "blt006 has no locale" in caplog.text  # the formatted text
    assert caplog.records[0].levelname == "WARNING"  # the record itself


def test_silent_when_locale_present(caplog: pytest.LogCaptureFixture) -> None:
    assert pick_locale({"uid": "blt001", "locale": "en-in"}) == "en-in"
    assert caplog.records == []  # REMEMBER: prove the noise is NOT there
# $ python3 -m pytest -q test_locale_fix.py
# -> 2 passed

# ===== section: Concept 6: mypy, checking types before the code runs =====
# Day 12: three bugs mypy finds without running the code
from dataclasses import dataclass


@dataclass
class Entry:
    uid: str
    title: str
    word_count: int
    author: str | None = None  # "str | None": the value may be missing


def reading_minutes(entry: Entry) -> int:
    return entry.word_count / 200  # BUG 1: "/" always gives a float


def author_initials(entry: Entry) -> str:
    return entry.author[0].upper()  # BUG 2: author can be None


def total_words(entries: list[Entry]) -> int:
    return sum(e.word_count for e in entries)


print(total_words(Entry("blt001", "SSO", "820")))  # BUG 3: two in one

# $ mypy typed.py   (messages shortened to fit)
# -> typed.py:14: error: Incompatible return value type
#        (got "float", expected "int")  [return-value]
# -> typed.py:18: error: Value of type "str | None" is not indexable
#        [index]
# -> typed.py:25: error: Argument 1 to "total_words" has incompatible
#        type "Entry"; expected "list[Entry]"  [arg-type]
# -> typed.py:25: error: Argument 3 to "Entry" has incompatible type
#        "str"; expected "int"  [arg-type]
# -> Found 4 errors in 1 file (checked 1 source file)

# ===== section: Concept 6: mypy, checking types before the code runs =====
# Day 12: fixing mypy errors by narrowing, and what --strict adds
from dataclasses import dataclass
from typing import reveal_type


@dataclass
class Entry:
    uid: str
    word_count: int
    author: str | None = None


def reading_minutes(entry: Entry) -> int:
    return max(1, entry.word_count // 200)  # "//": whole-number division


def author_initials(entry: Entry) -> str:
    if entry.author is None:  # narrowing: mypy follows this check
        return ""
    reveal_type(entry.author)  # asks mypy which type it sees here
    return entry.author[0].upper()  # safe: author is a str on this line


def legacy_to_row(e, default_locale="en-us"):  # no hints at all
    return {"uid": e["uid"], "locale": e.get("locale") or default_locale}


print(author_initials(Entry("blt001", 820, "priya")))  # -> P
print(reading_minutes(Entry("blt002", 150)))  # -> 1  (max keeps 1 min)

# $ mypy fixed.py
# -> fixed.py:20: note: Revealed type is "str"
# -> Success: no issues found in 1 source file   (legacy_to_row skipped!)
# $ mypy --strict fixed.py
# -> fixed.py:24: error: Function is missing a type annotation
# GOTCHA: at runtime reveal_type also prints "Runtime type is 'str'" to
# stderr, so delete it once you have your answer.

# ===== section: Check your understanding (predict first, then run) =====
# Day 12 check: predict each numbered part, then run python3 check12.py
import logging
import sys

# 1 which messages appear, and on which stream?
logging.basicConfig(
    level=logging.WARNING,
    stream=sys.stdout,  # note: stdout this time
    format="%(levelname)s %(message)s",
)
log = logging.getLogger("check")
log.info("one")
log.warning("two")

# 2 does a second basicConfig call change anything?
logging.basicConfig(level=logging.DEBUG)
log.debug("three")

# 3 a child logger with its own level
logging.getLogger("check.child").setLevel(logging.ERROR)
logging.getLogger("check.child").warning("four")
logging.getLogger("check.child").error("five")


# 4 then run: mypy check12.py   and   mypy --strict check12.py
def add_gst(amount):
    return amount * 1.18


def label(count: int) -> str:
    return "entries: " + str(count)


print(add_gst("100"), label(3))
