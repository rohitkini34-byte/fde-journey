"""Day 10 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: pytest, assert and reading a failure =====
# cms_utils.py: the code under test in today's examples
import json
import math
import os
import sys
import time
from pathlib import Path


class EntryError(ValueError):
    """Raised when a CMS entry or setting is unusable."""


def slugify(title: str) -> str:
    """'  Hello, World! ' -> 'hello-world' (a URL-safe slug)."""
    # keep letters and digits, turn everything else into a space
    cleaned = "".join(c if c.isalnum() else " " for c in title.lower())
    return "-".join(cleaned.split())


def reading_minutes(word_count: int, wpm: int = 200) -> int:
    """Minutes to read a post, rounded up, never less than 1."""
    if word_count < 0:
        raise EntryError(f"word_count must be >= 0, got {word_count}")
    return max(1, math.ceil(word_count / wpm))


def load_entries(path: Path) -> list[dict]:
    """Read a JSON list of entries; [] if the file does not exist."""
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return []
    if not isinstance(data, list):
        raise EntryError(f"{path.name} must hold a JSON list")
    return data


def get_base_url() -> str:
    """Read CMS_BASE_URL from the environment, without a trailing /."""
    url = os.environ.get("CMS_BASE_URL", "").strip()
    if not url:
        raise EntryError("CMS_BASE_URL is not set")
    return url.rstrip("/")


def fetch_title(session, base_url: str, uid: str) -> str:
    """GET one entry's title; on a 503 wait 2 s and try once more."""
    url = f"{base_url}/entries/{uid}"
    r = session.get(url, timeout=5)
    if r.status_code == 503:  # busy right now: wait, then retry once
        time.sleep(2)
        r = session.get(url, timeout=5)
    if r.status_code != 200:
        raise EntryError(f"HTTP {r.status_code} for {uid}")
    return r.json()["entry"]["title"].strip()


def main(argv: list[str]) -> int:
    """CLI: print the slug of the words given; return an exit code."""
    if not argv:
        print("error: give a title", file=sys.stderr)
        return 2
    print(slugify(" ".join(argv)))
    return 0

# ===== section: Concept 1: pytest, assert and reading a failure =====
# test_fail_demo.py: a test that fails ON PURPOSE, to read the report
from cms_utils import slugify


def test_slug_keeps_accents():
    # we EXPECT the accents to be dropped, but isalnum() keeps them
    assert slugify("Renée's café") == "renees-cafe"

# --- python3 -m pytest test_fail_demo.py prints (shortened) ---
# -> >       assert slugify("Renée's café") == "renees-cafe"
# -> E       AssertionError: assert 'renée-s-café' == 'renees-cafe'
# -> E         - renees-cafe
# -> E         + renée-s-café
# -> test_fail_demo.py:7: AssertionError
# -> FAILED test_fail_demo.py::test_slug_keeps_accents
# -> ============ 1 failed in 0.02s ============
# The > line is the failing assert; E lines show BOTH values.
# "-" is what you expected, "+" is what the code really returned.

# ===== section: Concept 2: Fixtures, tmp_path and conftest.py =====
# test_fixtures.py: fixtures give each test fresh, ready-made inputs
import json

import pytest

from cms_utils import load_entries


@pytest.fixture  # marks a function as a fixture; tests ask for it by NAME
def entries_file(tmp_path):
    # tmp_path is a built-in fixture: a new empty folder for EACH test
    path = tmp_path / "entries.json"
    data = [{"uid": "blt001", "title": "SSO"}, {"uid": "blt002"}]
    path.write_text(json.dumps(data), encoding="utf-8")
    return path  # the test receives this value as its argument


def test_load_entries_reads_list(entries_file):
    entries = load_entries(entries_file)
    assert [e["uid"] for e in entries] == ["blt001", "blt002"]


def test_missing_file_gives_empty_list(tmp_path):
    assert load_entries(tmp_path / "nope.json") == []


def test_each_test_gets_its_own_folder(tmp_path, entries_file):
    # entries_file used the SAME tmp_path as this test (one per test)
    print(tmp_path.name, sorted(p.name for p in tmp_path.iterdir()))
    assert entries_file.parent == tmp_path

# --- python3 -m pytest test_fixtures.py -v -s  (-s shows print output) ---
# -> test_fixtures.py::test_load_entries_reads_list PASSED
# -> test_fixtures.py::test_missing_file_gives_empty_list PASSED
# -> test_fixtures.py::test_each_test_gets_its_own_folder
# ->   test_each_test_gets_its_own_fo0 ['entries.json']  PASSED
# -> ============ 3 passed in 0.03s ============

# ===== section: Concept 2: Fixtures, tmp_path and conftest.py =====
# conftest.py: fixtures here are shared by every test file in this folder
import pytest


@pytest.fixture
def cms_settings():
    # code BEFORE yield is setup, like beforeEach in Jest
    settings = {"base_url": "https://cms.test", "api_key": "test-key"}
    print("\n  setup: settings ready")
    yield settings  # the test runs here, using this value
    # code AFTER yield is teardown, like afterEach; runs even if it failed
    settings.clear()
    print("  teardown: settings cleared")

# test_conftest_demo.py: uses a fixture from conftest.py, no import needed
def test_settings_have_key(cms_settings):
    print("  test body runs")
    assert cms_settings["api_key"] == "test-key"

# --- python3 -m pytest test_conftest_demo.py -s -q ---
# ->   setup: settings ready
# ->   test body runs
# -> .  teardown: settings cleared
# -> 1 passed in 0.01s

# ===== section: Concept 4: Testing errors and output with pytest.raises and capsys =====
# test_errors.py: proving that bad input fails the RIGHT way
import json

import pytest

from cms_utils import EntryError, load_entries, main, reading_minutes


def test_negative_word_count_raises():
    # passes only if the block raises EntryError (or a subclass of it)
    with pytest.raises(EntryError, match="must be >= 0, got -5"):
        reading_minutes(-5)


def test_error_object_can_be_inspected(tmp_path):
    path = tmp_path / "entries.json"
    path.write_text(json.dumps({"uid": "blt001"}), encoding="utf-8")
    with pytest.raises(EntryError) as exc_info:  # keep the error to look at
        load_entries(path)
    assert "entries.json" in str(exc_info.value)
    # EntryError inherits from ValueError (Day 5), so this is True too
    assert isinstance(exc_info.value, ValueError)


def test_main_prints_slug_and_returns_0(capsys):
    code = main(["Hello", "World"])
    out, err = capsys.readouterr()  # everything printed so far, split in two
    assert (code, out, err) == (0, "hello-world\n", "")


def test_main_without_args_returns_2(capsys):
    assert main([]) == 2
    assert capsys.readouterr().err == "error: give a title\n"

# --- python3 -m pytest test_errors.py -q ---
# -> 4 passed in 0.02s
# If the code does NOT raise, pytest.raises itself fails the test:
# -> Failed: DID NOT RAISE ValueError

# ===== section: Concept 5: Faking the outside world with monkeypatch and fake objects =====
# test_env.py: monkeypatch changes the world for ONE test, then undoes it
import pytest

import cms_utils
from cms_utils import EntryError, get_base_url


def test_base_url_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("CMS_BASE_URL", "https://cms.test/")  # set for 1 test
    assert get_base_url() == "https://cms.test"


def test_missing_base_url_is_a_clear_error(monkeypatch):
    # raising=False: do not complain if the variable was never set
    monkeypatch.delenv("CMS_BASE_URL", raising=False)
    with pytest.raises(EntryError, match="CMS_BASE_URL is not set"):
        get_base_url()


def test_sleep_can_be_replaced(monkeypatch):
    calls = []
    # replace time.sleep AS SEEN BY cms_utils with a fake that only records
    monkeypatch.setattr(cms_utils.time, "sleep", calls.append)
    cms_utils.time.sleep(2)  # returns at once, nothing waits
    assert calls == [2]

# --- python3 -m pytest test_env.py -q ---
# -> 3 passed in 0.01s

# ===== section: Concept 5: Faking the outside world with monkeypatch and fake objects =====
# test_http.py: test HTTP code with a FAKE session, no network at all
import pytest

import cms_utils
from cms_utils import EntryError, fetch_title


class FakeResponse:
    """Just the parts of requests.Response our code uses."""

    def __init__(self, status_code, body=None):
        self.status_code = status_code
        self._body = body or {}

    def json(self):
        return self._body


class FakeSession:
    """Plays back prepared responses in order and records each call."""

    def __init__(self, *responses):
        self.responses = list(responses)
        self.calls = []  # (url, kwargs) for every get(), to assert on later

    def get(self, url, **kwargs):
        self.calls.append((url, kwargs))
        return self.responses.pop(0)  # next prepared reply, like a script


@pytest.fixture
def no_sleep(monkeypatch):
    waits = []
    monkeypatch.setattr(cms_utils.time, "sleep", waits.append)
    return waits  # the test can check how long the code WOULD have waited


def test_returns_stripped_title():
    s = FakeSession(FakeResponse(200, {"entry": {"title": " SSO guide "}}))
    assert fetch_title(s, "https://cms.test", "blt001") == "SSO guide"
    url, kwargs = s.calls[0]
    assert url == "https://cms.test/entries/blt001"
    assert kwargs["timeout"] == 5  # a test can enforce "always a timeout"


def test_retries_once_on_503(no_sleep):
    s = FakeSession(FakeResponse(503),
                    FakeResponse(200, {"entry": {"title": "SSO"}}))
    assert fetch_title(s, "https://cms.test", "blt001") == "SSO"
    assert len(s.calls) == 2 and no_sleep == [2]  # waited 2 s, but not really


def test_404_fails_fast_without_retry(no_sleep):
    s = FakeSession(FakeResponse(404))
    with pytest.raises(EntryError, match="HTTP 404 for blt999"):
        fetch_title(s, "https://cms.test", "blt999")
    assert len(s.calls) == 1 and no_sleep == []  # no retry, no wait

# --- python3 -m pytest test_http.py -v ---
# -> test_http.py::test_returns_stripped_title PASSED         [ 33%]
# -> test_http.py::test_retries_once_on_503 PASSED            [ 66%]
# -> test_http.py::test_404_fails_fast_without_retry PASSED   [100%]
# -> ============ 3 passed in 0.02s ============

# ===== section: Check your understanding (predict first, then run) =====
# test_check.py: predict what pytest reports for each test, then run it
import os

import pytest

from cms_utils import reading_minutes


def check_slug():  # Check 1: is this run?
    assert False


def test_float_sum():  # Check 2: pass or fail?
    assert 0.1 + 0.2 == 0.3


def test_parent_class():  # Check 3: pass or fail?
    with pytest.raises(ValueError):
        reading_minutes(-1)


@pytest.mark.parametrize("a", [1, 2, 3])
@pytest.mark.parametrize("b", ["x", "y"])
def test_grid(a, b):  # Check 4: how many tests does this make?
    assert a and b


def test_set_env(monkeypatch):  # Check 5a
    monkeypatch.setenv("DAY10_DEMO", "on")
    assert os.environ["DAY10_DEMO"] == "on"


def test_read_env():  # Check 5b: pass or fail? (runs after 5a)
    assert os.environ.get("DAY10_DEMO") is None

# --- run it: python3 -m pytest test_check.py -q, then -v ---
