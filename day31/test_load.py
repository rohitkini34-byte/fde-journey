"""Day 31: given tests for load.py and schema.sql (do not edit).

These tests use a REAL Postgres. Each test gets its own throwaway schema
(a namespace inside your database), so your real tables are never touched
and tests cannot see each other's rows. If DATABASE_URL is not set or the
server is down, every database test is SKIPPED, not failed: start Postgres
and export DATABASE_URL first (see the top of load.py).

Run inside day31/:   python -m pytest -q
"""

import os
import uuid
from datetime import UTC, datetime
from pathlib import Path

import psycopg
import pytest

from load import (
    Entry,
    LoadReport,
    apply_schema,
    connect,
    entry_to_params,
    load_file,
    read_batch,
    upsert_entries,
)

HERE = Path(__file__).parent
BATCH_1 = HERE / "batch_1.json"
BATCH_2 = HERE / "batch_2.json"
BAD_BATCH = HERE / "bad_batch.json"


# ---------------------------------------------------------------- fixtures
@pytest.fixture
def db():
    """An autocommit connection whose search_path is a fresh schema."""
    url = os.environ.get("DATABASE_URL")
    if not url:
        pytest.skip("DATABASE_URL is not set")
    try:
        conn = psycopg.connect(url, autocommit=True, connect_timeout=3)
    except psycopg.OperationalError as exc:
        pytest.skip(f"Postgres not reachable: {exc}")
    schema = f"test_day31_{uuid.uuid4().hex[:8]}"
    conn.execute(f'CREATE SCHEMA "{schema}"')
    conn.execute(f'SET search_path TO "{schema}"')
    apply_schema(conn, HERE / "schema.sql")
    yield conn
    conn.execute(f'DROP SCHEMA "{schema}" CASCADE')
    conn.close()


def count_rows(conn) -> int:
    return conn.execute("SELECT count(*) FROM entries").fetchone()[0]


def title_of(conn, uid: str, locale: str = "en-us") -> str:
    return conn.execute(
        "SELECT title FROM entries WHERE uid = %s AND locale = %s",
        [uid, locale],
    ).fetchone()[0]


# ------------------------------------------------- TODO 1: connect()
def test_connect_needs_database_url(monkeypatch):
    monkeypatch.delenv("DATABASE_URL", raising=False)
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        connect()


def test_connect_returns_autocommit_connection(db):
    conn = connect(os.environ["DATABASE_URL"])
    try:
        assert conn.autocommit is True
    finally:
        conn.close()


# ------------------------------------------------- TODO 4: entry_to_params()
ENTRY = Entry(
    uid="blt001",
    content_type="page",
    title="Winter Sale",
    locale="en-us",
    updated_at=datetime(2026, 11, 20, 9, 30, tzinfo=UTC),
    tags=("sale", "winter"),
)


def test_entry_to_params_has_every_column():
    params = entry_to_params(ENTRY)
    assert set(params) == {
        "uid", "locale", "content_type", "title", "tags", "updated_at"
    }
    assert params["updated_at"] == ENTRY.updated_at  # still a datetime


def test_entry_to_params_sends_tags_as_a_list():
    assert entry_to_params(ENTRY)["tags"] == ["sale", "winter"]


# ------------------------------- TODOs 2 and 3: apply_schema(), schema.sql
def test_schema_can_be_applied_twice(db):
    apply_schema(db, HERE / "schema.sql")  # the fixture already ran it once
    assert count_rows(db) == 0


INSERT_ONE = (
    "INSERT INTO entries (uid, locale, content_type, title, updated_at)"
    " VALUES (%s, %s, %s, %s, %s)"
)
WHEN = datetime(2026, 11, 20, tzinfo=UTC)


@pytest.mark.parametrize(
    "uid, locale, content_type, title",
    [
        ("", "en-us", "page", "Title"),  # empty uid
        ("blt9", "en-us", "page", "   "),  # blank title
        ("blt9", "EN_US", "page", "Title"),  # badly formed locale
        ("blt9", "en-us", " ", "Title"),  # blank content type
    ],
)
def test_check_constraints_reject_bad_rows(db, uid, locale, content_type,
                                           title):
    with pytest.raises(psycopg.errors.CheckViolation):
        db.execute(INSERT_ONE, [uid, locale, content_type, title, WHEN])


def test_null_title_is_rejected(db):
    with pytest.raises(psycopg.errors.NotNullViolation):
        db.execute(INSERT_ONE, ["blt9", "en-us", "page", None, WHEN])


def test_primary_key_is_uid_plus_locale(db):
    db.execute(INSERT_ONE, ["blt9", "en-us", "page", "One", WHEN])
    db.execute(INSERT_ONE, ["blt9", "hi-in", "page", "Ek", WHEN])  # fine
    with pytest.raises(psycopg.errors.UniqueViolation):
        db.execute(INSERT_ONE, ["blt9", "en-us", "page", "Again", WHEN])


def test_defaults_fill_locale_tags_and_synced_at(db):
    db.execute(
        "INSERT INTO entries (uid, content_type, title, updated_at)"
        " VALUES ('blt9', 'page', 'T', now())"
    )
    locale, tags, synced_at = db.execute(
        "SELECT locale, tags, synced_at FROM entries"
    ).fetchone()
    assert (locale, tags) == ("en-us", [])
    assert synced_at is not None


def test_updated_at_is_timestamptz(db):
    data_type = db.execute(
        "SELECT data_type FROM information_schema.columns"
        " WHERE table_schema = current_schema()"
        " AND table_name = 'entries' AND column_name = 'updated_at'"
    ).fetchone()[0]
    assert data_type == "timestamp with time zone"


# ------------------------------- TODOs 5 and 6: UPSERT_SQL, upsert_entries()
def test_first_load_inserts_every_entry(db):
    report = upsert_entries(db, read_batch(BATCH_1))
    assert report == LoadReport(inserted=5, updated=0, skipped=0)
    assert count_rows(db) == 5


def test_second_load_changes_0_rows(db):
    upsert_entries(db, read_batch(BATCH_1))
    before = db.execute(
        "SELECT uid, locale, synced_at FROM entries ORDER BY 1, 2"
    ).fetchall()
    report = upsert_entries(db, read_batch(BATCH_1))
    after = db.execute(
        "SELECT uid, locale, synced_at FROM entries ORDER BY 1, 2"
    ).fetchall()
    assert report == LoadReport(inserted=0, updated=0, skipped=5)
    assert report.changed == 0
    assert after == before  # not even synced_at moved: nothing was written


def test_batch_2_inserts_1_updates_2_skips_3(db):
    upsert_entries(db, read_batch(BATCH_1))
    report = upsert_entries(db, read_batch(BATCH_2))
    assert report == LoadReport(inserted=1, updated=2, skipped=3)
    assert title_of(db, "blt001") == "Winter Sale: 40% off"


def test_tag_change_is_saved_as_a_list(db):
    upsert_entries(db, read_batch(BATCH_1))
    upsert_entries(db, read_batch(BATCH_2))
    tags = db.execute(
        "SELECT tags FROM entries WHERE uid = 'blt002'"
    ).fetchone()[0]
    assert tags == ["shipping", "help"]


def test_stale_entry_does_not_overwrite_newer_row(db):
    upsert_entries(db, read_batch(BATCH_1))
    upsert_entries(db, read_batch(BATCH_2))
    # batch_2 carries an OLDER version of blt003: it must lose
    assert title_of(db, "blt003") == "Returns Policy"


def test_updated_row_gets_a_new_synced_at(db):
    upsert_entries(db, read_batch(BATCH_1))
    first = db.execute(
        "SELECT synced_at FROM entries WHERE uid = 'blt002'"
    ).fetchone()[0]
    upsert_entries(db, read_batch(BATCH_2))
    second = db.execute(
        "SELECT synced_at FROM entries WHERE uid = 'blt002'"
    ).fetchone()[0]
    assert second > first


def test_bad_batch_rolls_back_completely(db):
    upsert_entries(db, read_batch(BATCH_1))
    with pytest.raises(psycopg.errors.CheckViolation):
        upsert_entries(db, read_batch(BAD_BATCH))
    # blt001 was valid and came first in the bad batch, but it must NOT
    # have been saved: one transaction, all or nothing
    assert title_of(db, "blt001") == "Winter Sale"
    assert count_rows(db) == 5


def test_connection_is_usable_after_a_failed_batch(db):
    with pytest.raises(psycopg.errors.CheckViolation):
        upsert_entries(db, read_batch(BAD_BATCH))
    assert upsert_entries(db, read_batch(BATCH_1)).inserted == 5


# ------------------------------------------------- TODO 7: load_file()
def test_load_file_returns_the_report(db, caplog):
    caplog.set_level("INFO", logger="load")
    report = load_file(db, BATCH_1)
    assert report.inserted == 5
    assert "batch_1.json: 5 inserted, 0 updated, 0 skipped" in caplog.text
