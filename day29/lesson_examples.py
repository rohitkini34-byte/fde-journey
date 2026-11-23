"""Day 29 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 2: Validating one record at the boundary =====
# Validate one CMS asset record at the boundary, then a whole export.
class InvalidAssetError(ValueError):
    """One asset record broke a rule. "is a" ValueError, so callers can
    catch either name."""
 
 
def validate_asset(raw: dict) -> dict:
    """Return a cleaned COPY of one asset, or raise InvalidAssetError."""
    # .get() returns None for a missing key instead of raising KeyError;
    # "or ''" turns None into "" so .strip() is always safe
    title = (raw.get("title") or "").strip()
    if not title:
        raise InvalidAssetError("title is empty")
    url = (raw.get("url") or "").strip()
    if not url.startswith("https://"):
        # !r puts the ORIGINAL value in quotes, so a blank shows as ''
        raise InvalidAssetError(f"url {raw.get('url')!r} is not https")
    size = raw.get("size_kb")
    # GOTCHA: True is an int in Python (True == 1), so reject bool first
    if isinstance(size, bool) or not isinstance(size, int) or size <= 0:
        msg = f"size_kb must be a positive int, got {size!r}"
        raise InvalidAssetError(msg)
    # a NEW dict: the caller's raw record is never changed
    return {"title": title, "url": url, "size_kb": size}
 
 
export = [
    {"title": " Hero banner ", "url": "https://cdn.acme.in/hero.png",
     "size_kb": 240},
    {"title": "", "url": "https://cdn.acme.in/x.png", "size_kb": 10},
    {"title": "Logo", "url": "http://cdn.acme.in/logo.svg", "size_kb": 4},
    {"title": "Promo", "url": "https://cdn.acme.in/p.mp4", "size_kb": True},
]
 
clean, errors = [], []
# enumerate(..., start=1): numbers that match what a human counts
for number, record in enumerate(export, start=1):
    try:
        clean.append(validate_asset(record))
    except InvalidAssetError as err:  # catch only the error you expect
        errors.append(f"record {number}: {err}")  # str(err) is the message
 
print(clean)
# -> [{'title': 'Hero banner', 'url': 'https://cdn.acme.in/hero.png',
#      'size_kb': 240}]
print(*errors, sep="\n")
# -> record 2: title is empty
# -> record 3: url 'http://cdn.acme.in/logo.svg' is not https
# -> record 4: size_kb must be a positive int, got True
print(repr(export[0]["title"]))  # -> ' Hero banner ' (input untouched)

# ===== section: Concept 3: Errors that travel up: one family, one catch =====
# Errors that travel up: one family, "raise from", one catch at the top.
import json
import sys
from pathlib import Path
 
 
class SyncError(Exception):
    """Base class: anything wrong with the sync job's own files."""
 
 
class StateFileError(SyncError):
    """The saved sync state is unreadable. Is a SyncError."""
 
 
def load_state(path: Path) -> dict:
    """Read the last sync cursor; a missing file means 'never synced'."""
    try:
        with open(path, encoding="utf-8") as f:  # closes even on error
            return json.load(f)  # like JSON.parse() on the file's text
    except FileNotFoundError:
        return {"version": 1, "cursor": None}  # first run: start fresh
    except json.JSONDecodeError as err:
        # FDE TIP: name the file AND the line, so the reader can fix it
        msg = f"{path} is not valid JSON (line {err.lineno})"
        raise StateFileError(msg) from err  # keeps the original as cause
 
 
def main(state_path: Path) -> int:
    """Run one sync. Return the exit code: 0 ok, 1 failed."""
    try:
        state = load_state(state_path)
        print("resuming from cursor", state["cursor"])
        return 0
    except SyncError as err:  # catches StateFileError too (the family)
        print(f"error: {err}", file=sys.stderr)  # errors go to stderr
        return 1
 
 
scratch = Path("scratch")
scratch.mkdir(exist_ok=True)
state_file = scratch / "state.json"
 
state_file.unlink(missing_ok=True)  # make sure the first run has no file
print(main(state_file))
# -> resuming from cursor None
# -> 0
state_file.write_text('{\n  "version": 1,\n  "cursor": "c-42"\n',
                      encoding="utf-8")  # broken: the closing } is missing
print(main(state_file))
# -> error: scratch/state.json is not valid JSON (line 4)
# -> 1
 
try:
    load_state(state_file)
except StateFileError as err:
    # __cause__ is the error you passed to "from": nothing is lost
    print(type(err.__cause__).__name__)  # -> JSONDecodeError
# REMEMBER: raise specific errors low down, catch the family once at the top

# ===== section: Concept 4: Your first pytest file for real code =====
# A first pytest file: plain asserts, parametrize, raises, tmp_path.
import json
 
import pytest  # the test runner, like Jest in JavaScript
 
from asset_rules import InvalidAssetError, validate_asset
 
GOOD = {"title": " Hero ", "url": "https://cdn.acme.in/h.png", "size_kb": 9}
 
 
def test_good_record_is_cleaned():
    # Arrange, Act, Assert: the three steps of almost every test
    result = validate_asset(GOOD)
    assert result == {"title": "Hero", "url": "https://cdn.acme.in/h.png",
                      "size_kb": 9}
 
 
def test_input_is_not_changed():
    before = dict(GOOD)  # a copy to compare with afterwards
    validate_asset(GOOD)
    assert GOOD == before  # proves the function returned a NEW dict
 
 
# One test body, many rows: each row runs as its own test
@pytest.mark.parametrize(
    ("change", "message"),
    [
        ({"title": "  "}, "title is empty"),
        ({"url": "http://x.in/a.png"}, "is not https"),
        ({"size_kb": True}, "got True"),
        ({"size_kb": None}, "got None"),
    ],
)
def test_bad_records_are_rejected(change, message):
    raw = {**GOOD, **change}  # like {...GOOD, ...change} in JS
    # the test passes only if this exact error type is raised inside
    # GOTCHA: match is a regex searched in str(err); escape ( ) $ . with
    # re.escape() when the message contains them
    with pytest.raises(InvalidAssetError, match=message):
        validate_asset(raw)
 
 
def test_records_from_a_file(tmp_path):
    # tmp_path: a fresh empty folder per test, deleted for you later
    export = tmp_path / "assets.json"
    export.write_text(json.dumps([GOOD, GOOD]), encoding="utf-8")
    records = json.loads(export.read_text(encoding="utf-8"))
    assert [validate_asset(r)["title"] for r in records] == ["Hero", "Hero"]
 
 
def test_this_one_fails_on_purpose():
    # a wrong expectation, to show what a failure report looks like
    assert validate_asset(GOOD)["title"] == " Hero "

# ===== section: Check your understanding (predict first, then run) =====
# Day 29 check: predict every numbered print, then run.
import json
import re
 
# 1) "or" returns the first truthy value, so which text gets stripped?
print(1, repr((None or "x").strip()), repr(("  " or "x").strip()))
 
# 2) is True an int?
print(2, isinstance(True, int), True + True)
 
# 3) which line does json report?
try:
    json.loads('{\n  "a": 1,\n}')
except json.JSONDecodeError as err:
    print(3, err.lineno)
 
# 4) pytest.raises(match=...) uses re.search: does this pattern match?
print(4, bool(re.search("cost $5", "cost $5")),
      bool(re.search(re.escape("cost $5"), "cost $5")))
 
# 5) what is the cause, and is the new error a ValueError?
class StoreError(ValueError):
    pass
 
try:
    try:
        int("x")
    except ValueError as err:
        raise StoreError("bad number in row 2") from err
except ValueError as outer:
    print(5, type(outer).__name__, type(outer.__cause__).__name__)
 
# 6) enumerate with start=1 over a list of three
print(6, list(enumerate(["a", "b", "c"], start=1))[-1])
