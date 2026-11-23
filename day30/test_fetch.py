"""Given tests for day30/fetch.py (do not edit; add your own in test_mine.py).

Run inside day30/:   python -m pytest -q
Every test uses the FakeCMS from mock_cms.py through httpx.MockTransport,
so nothing touches the network and no test really sleeps.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pytest

from fetch import (
    DEFAULT_BASE_URL,
    Entry,
    FetchError,
    backoff_delay,
    build_client,
    fetch_all,
    get_json,
    is_retryable,
    iter_entries,
)
from mock_cms import FakeCMS

HERE = Path(__file__).parent  # tests find the data file wherever you run them
SAMPLE = json.loads((HERE / "cms_entries.json").read_text(encoding="utf-8"))
PATH = "/content_types/page/entries"


@pytest.fixture
def slept() -> list[float]:
    """A fake sleep: tests pass slept.append, then check what was 'slept'."""
    return []


def client_for(cms: FakeCMS, token: str = "test-token") -> httpx.Client:
    return build_client(DEFAULT_BASE_URL, token, transport=cms.transport)


# ---------- Entry.from_api ----------------------------------------------
def test_from_api_cleans_title_and_tags():
    e = Entry.from_api(SAMPLE[0], "page")
    assert e.uid == "blt001" and e.content_type == "page"
    assert e.title == "Winter Sale"
    assert e.tags == ("sale", "winter")  # lowercased, duplicate removed
    assert e.updated_at == datetime(2026, 11, 20, 9, 30, tzinfo=timezone.utc)


def test_from_api_defaults_locale_and_handles_missing_tags():
    e = Entry.from_api(SAMPLE[5], "page")
    assert e.locale == "en-us" and e.tags == ()


@pytest.mark.parametrize("index", [2, 4])  # blank title; no timezone
def test_from_api_rejects_bad_items(index):
    with pytest.raises(ValueError, match=SAMPLE[index]["uid"]):
        Entry.from_api(SAMPLE[index], "page")


def test_entry_is_frozen():
    e = Entry.from_api(SAMPLE[0], "page")
    with pytest.raises(AttributeError):  # FrozenInstanceError is one
        e.title = "changed"  # type: ignore[misc]


# ---------- build_client, is_retryable, backoff_delay -----------------------
def test_build_client_sets_base_url_header_and_timeouts():
    c = build_client("https://cms.example.test/v3", "abc", timeout_s=7.5)
    assert str(c.base_url) == "https://cms.example.test/v3/"
    assert c.headers["access_token"] == "abc"
    assert c.timeout.read == 7.5 and c.timeout.connect == 3.0


@pytest.mark.parametrize(
    "status, expected",
    [(429, True), (500, True), (502, True), (503, True), (504, True),
     (400, False), (401, False), (404, False), (422, False), (200, False)],
)
def test_is_retryable(status, expected):
    assert is_retryable(status) is expected


def test_backoff_delay_doubles_and_caps():
    assert [backoff_delay(n) for n in range(1, 7)] == [
        0.5, 1.0, 2.0, 4.0, 8.0, 8.0]


def test_backoff_delay_respects_retry_after():
    assert backoff_delay(1, retry_after="3") == 3.0
    assert backoff_delay(1, retry_after="45") == 45.0  # the server decides
    assert backoff_delay(1, retry_after="900") == 60.0  # max_retry_after
    assert backoff_delay(2, retry_after="soon") == 1.0  # unreadable: ignore


# ---------- get_json --------------------------------------------------------
def test_get_json_retries_503_then_succeeds(slept):
    cms = FakeCMS(SAMPLE, fail_first=2)
    data = get_json(client_for(cms), PATH, {"limit": 2}, sleep=slept.append)
    assert len(data["items"]) == 2
    assert len(cms.requests) == 3 and slept == [0.5, 1.0]


def test_get_json_retries_timeouts(slept):
    cms = FakeCMS(SAMPLE, timeout_first=1)
    get_json(client_for(cms), PATH, {"limit": 2}, sleep=slept.append)
    assert len(cms.requests) == 2 and slept == [0.5]


def test_get_json_uses_retry_after_on_429(slept):
    cms = FakeCMS(SAMPLE, fail_first=1, fail_status=429, retry_after="2")
    get_json(client_for(cms), PATH, {"limit": 2}, sleep=slept.append)
    assert slept == [2.0]


def test_get_json_gives_up_after_max_attempts(slept):
    cms = FakeCMS(SAMPLE, fail_first=10)
    with pytest.raises(FetchError, match="503"):
        get_json(client_for(cms), PATH, {"limit": 2}, max_attempts=3,
                 sleep=slept.append)
    assert len(cms.requests) == 3 and len(slept) == 2  # no sleep after last


def test_get_json_does_not_retry_401(slept):
    cms = FakeCMS(SAMPLE)
    with pytest.raises(FetchError, match="401"):
        get_json(client_for(cms, token="wrong"), PATH, {"limit": 2},
                 sleep=slept.append)
    assert len(cms.requests) == 1 and slept == []


# ---------- iter_entries and fetch_all --------------------------------------
def test_iter_entries_follows_cursors_and_skips_bad_items(slept):
    cms = FakeCMS(SAMPLE)
    entries = list(iter_entries(client_for(cms), "page", page_size=2,
                                sleep=slept.append))
    assert [e.uid for e in entries] == ["blt001", "blt002", "blt004",
                                        "blt006"]
    sent = [dict(r.url.params) for r in cms.requests]
    assert sent == [{"limit": "2"}, {"limit": "2", "cursor": "c2"},
                    {"limit": "2", "cursor": "c4"}]  # no "cursor=" on page 1


def test_iter_entries_is_lazy():
    cms = FakeCMS(SAMPLE)
    gen = iter_entries(client_for(cms), "page", page_size=2)
    assert cms.requests == []  # nothing fetched until you iterate
    next(gen)
    assert len(cms.requests) == 1


def test_iter_entries_stops_a_cursor_loop():
    cms = FakeCMS(SAMPLE, loop_cursor=True)
    with pytest.raises(FetchError, match="cursor"):
        list(iter_entries(client_for(cms), "page", page_size=2))
    assert len(cms.requests) <= 3


def test_fetch_all_returns_a_list(slept):
    cms = FakeCMS(SAMPLE, fail_first=1)
    entries = fetch_all(client_for(cms), "page", page_size=3,
                        sleep=slept.append)
    assert isinstance(entries, list) and len(entries) == 4
    assert all(isinstance(e, Entry) for e in entries)
