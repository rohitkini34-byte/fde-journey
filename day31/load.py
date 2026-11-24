"""Day 31 task: the store layer of thin-sync (Week 5, consolidation week).

Real-world purpose: after the fetch layer (Day 30) pulls entries out of
the customer's CMS, a sync job writes them into YOUR Postgres, every hour,
forever. Three things make that safe:
    1. the table's constraints refuse bad rows (schema.sql),
    2. the write is an upsert that skips rows that did not change, so a
       re-run is harmless and the report says what really happened,
    3. the whole batch is ONE transaction: all rows or none.
The test of success is simple and is what you will demo: run the load
twice, and the second run reports 0 inserted and 0 updated.

In Contentstack terms: this is what a "sync to our own database" job does
after the Sync API or Delivery API hands it a page of entries.

ONE-TIME SETUP (inside day31/)
    uv venv && uv pip install "psycopg[binary]" pytest
        (or: python -m venv .venv, activate it, pip install the same)
    export DATABASE_URL=postgresql://localhost/fde    (your Day 15 database)
    python -m pytest -q          -> 22 errors/failures before you start

ASSIGNMENT (from the Day 31 session in the master doc)
-----------------------------------------------------
Implement the seven TODOs below in order (TODO 3 lives in schema.sql).
Each one has a test group in test_load.py.

ACCEPTANCE CRITERIA
1. Inside day31/:  python -m pytest -q  ->  24 passed (22 given cases in
   test_load.py plus your 2 in test_mine.py), with DATABASE_URL set.
2. python load.py batch_1.json batch_2.json, run twice, prints the demo
   output in the __main__ block: the second run changes 0 rows.
3. python load.py bad_batch.json exits with code 1, logs the name of the
   constraint that failed, and leaves the table exactly as it was.
4. Every value reaches SQL through %(name)s placeholders: no f-strings or
   + around SQL anywhere in load.py.
5. schema.sql can be run twice in a row without an error.
6. day31/ committed and pushed to main with a clear message.
"""

import argparse  # command-line arguments, like process.argv parsing in Node
import json
import logging
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import psycopg  # pip install "psycopg[binary]"  (psycopg 3, Day 18)

log = logging.getLogger("load")  # one named logger per module (Day 12)
HERE = Path(__file__).parent  # this file's folder, so paths work anywhere


# ---------------------------------------------------------------------------
# Given: Entry, the same shape as Day 30's fetch layer returns.
# If your day30/fetch.py is finished you could import it from there; to keep
# today independent, the class is repeated here without the parsing rules.
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class Entry:
    uid: str
    content_type: str
    title: str
    locale: str
    updated_at: datetime  # timezone-aware, as Day 30 guarantees
    tags: tuple[str, ...] = ()  # a TUPLE: see the GOTCHA in TODO 4


def read_batch(path: str | Path) -> list[Entry]:
    """Given: read a JSON batch file (what fetch_all() would return)."""
    # GOTCHA: on purpose, this does NOT check titles. bad_batch.json has a
    # blank title so you can watch the DATABASE refuse it (TODO 3).
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return [
        Entry(
            uid=item["uid"],
            content_type=item["content_type"],
            title=item["title"],
            locale=item.get("locale", "en-us"),
            updated_at=datetime.fromisoformat(item["updated_at"]),
            tags=tuple(item.get("tags") or ()),
        )
        for item in raw
    ]


# ---------------------------------------------------------------------------
# Given: LoadReport, what one load did. The numbers ARE the demo.
# frozen dataclasses compare field by field, so tests can write
# assert report == LoadReport(inserted=1, updated=2, skipped=3)
# ---------------------------------------------------------------------------
@dataclass(frozen=True)
class LoadReport:
    inserted: int = 0  # new rows
    updated: int = 0  # existing rows whose content really changed
    skipped: int = 0  # identical rows, or older (stale) versions

    @property
    def total(self) -> int:
        """Every entry in the batch, written or not."""
        return self.inserted + self.updated + self.skipped

    @property
    def changed(self) -> int:
        """Rows actually written. 0 on a re-run: that is idempotency."""
        return self.inserted + self.updated


# ---------------------------------------------------------------------------
# TODO 1: connect
# What:    open a connection to Postgres.
# Input:   connect("postgresql://localhost/fde") -> that database;
#          connect() -> reads the DATABASE_URL environment variable.
# Output:  a psycopg.Connection with autocommit=True.
# Rules:   no URL given and DATABASE_URL unset -> RuntimeError whose
#          message contains "DATABASE_URL" (a clear message beats a
#          psycopg error about a socket in /tmp).
# Why autocommit: then the ONLY transactions are the ones you open with
#          conn.transaction(), so "one batch = one transaction" is true
#          and visible in the code (Concept 3).
# Practises: Concept 3, Day 9 environment variables.
# ---------------------------------------------------------------------------
def connect(url: str | None = None) -> psycopg.Connection:
    """Return an autocommit connection to the database at url."""
    # HINT 1: url or os.environ.get("DATABASE_URL") picks the first that
    #         is not empty (like url ?? process.env.DATABASE_URL in JS).
    # HINT 2: if it is still empty, raise RuntimeError("DATABASE_URL ...").
    # HINT 3: psycopg.connect(url, autocommit=True)
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 2: apply_schema
# What:    run every statement in schema.sql on conn.
# Input:   apply_schema(conn) or apply_schema(conn, Path("other.sql"))
# Output:  None. Running it twice must not fail (schema.sql uses
#          IF NOT EXISTS; that is TODO 3's job).
# Practises: Concept 1 (schema as code in the repo).
# ---------------------------------------------------------------------------
def apply_schema(conn: psycopg.Connection,
                 path: Path = HERE / "schema.sql") -> None:
    """Create the entries table and its index if they do not exist."""
    # HINT 1: Path(path).read_text(encoding="utf-8") gives the file as text.
    # HINT 2: conn.execute(text) runs it. With NO parameters, psycopg may
    #         send several statements separated by ; in one call.
    raise NotImplementedError("TODO")


# TODO 3 is in schema.sql: add the constraints and defaults.


# ---------------------------------------------------------------------------
# TODO 4: entry_to_params
# What:    turn one Entry into the dict of named parameters UPSERT_SQL uses.
# Input:   Entry(uid="blt001", content_type="page", title="Winter Sale",
#                locale="en-us", updated_at=<aware datetime>,
#                tags=("sale", "winter"))
# Output:  {"uid": "blt001", "locale": "en-us", "content_type": "page",
#           "title": "Winter Sale", "tags": ["sale", "winter"],
#           "updated_at": <the same datetime object>}
# Practises: Concept 3 (how Python values become Postgres types).
# ---------------------------------------------------------------------------
def entry_to_params(entry: Entry) -> dict:
    """Return the named SQL parameters for one entry."""
    # HINT 1: one dict literal with six keys, named like the columns.
    # HINT 2: GOTCHA: psycopg sends a Python LIST as a Postgres array, but
    #         not a tuple. Convert with list(entry.tags).
    # HINT 3: keep updated_at a datetime. Never str() it: psycopg sends the
    #         real type, including its timezone.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 5: UPSERT_SQL
# What:    ONE statement that inserts a new entry, updates a changed one,
#          and does NOTHING (writes no row) when the entry is identical or
#          older than what is stored.
# Rules:   placeholders %(uid)s, %(locale)s, ... matching TODO 4's keys.
#          The conflict target is the primary key (uid, locale).
#          On update: copy content_type, title, tags, updated_at from
#          EXCLUDED and set synced_at = now().
#          Update ONLY when BOTH are true:
#            - the incoming updated_at is >= the stored one (a stale
#              version from a slow worker must never win), and
#            - something differs, compared NULL-safely.
#          RETURNING one column that is true for an insert, false for an
#          update. A skipped row returns NO row at all.
# Practises: Concept 2 (the no-op upsert), Day 19 ON CONFLICT.
# ---------------------------------------------------------------------------
UPSERT_SQL = """
-- TODO 5: write the statement here.
-- HINT 1: INSERT INTO entries AS e (uid, locale, ...) VALUES (%(uid)s, ...)
--         The alias "e" lets the WHERE clause name the stored row.
-- HINT 2: ON CONFLICT (uid, locale) DO UPDATE SET title = EXCLUDED.title,
--         ... (EXCLUDED is the row you tried to insert).
-- HINT 3: WHERE EXCLUDED.updated_at >= e.updated_at
--           AND (e.title, e.tags, ...) IS DISTINCT FROM
--               (EXCLUDED.title, EXCLUDED.tags, ...)
-- HINT 4: RETURNING (xmax = 0) AS inserted
--         (Concept 2 explains why xmax = 0 means "this row is new").
"""


# ---------------------------------------------------------------------------
# TODO 6: upsert_entries
# What:    write a batch of entries in ONE transaction and count the result.
# Input:   upsert_entries(conn, read_batch("batch_1.json")) on an empty
#          table -> LoadReport(inserted=5, updated=0, skipped=0);
#          the same call again -> LoadReport(inserted=0, updated=0,
#          skipped=5).
# Rules:   if any row fails (for example a CHECK constraint), NOTHING from
#          the batch is saved and the psycopg error propagates to the
#          caller (do not catch it here). An empty list -> LoadReport().
# Practises: Concept 3 (transactions, cursors), Concept 4 (idempotency).
# ---------------------------------------------------------------------------
def upsert_entries(conn: psycopg.Connection,
                   entries: list[Entry]) -> LoadReport:
    """Upsert every entry in one transaction; return what happened."""
    # HINT 1: three counters at 0, then
    #         with conn.transaction():   and inside it
    #         with conn.cursor() as cur:
    # HINT 2: for each entry: cur.execute(UPSERT_SQL, entry_to_params(e)),
    #         then row = cur.fetchone()
    # HINT 3: row is None -> skipped; row[0] is True -> inserted;
    #         otherwise -> updated.
    # HINT 4: return LoadReport(...) AFTER the with block, so the counts
    #         are only reported once the commit has happened.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# TODO 7: load_file
# What:    read one batch file, upsert it, log one summary line.
# Input:   load_file(conn, Path("batch_1.json"))
# Output:  the LoadReport, and this INFO log line (copy it exactly; the
#          test looks for it):
#          "batch_1.json: 5 inserted, 0 updated, 0 skipped"
# Practises: Day 12 logging (%-style arguments, not f-strings).
# ---------------------------------------------------------------------------
def load_file(conn: psycopg.Connection, path: str | Path) -> LoadReport:
    """Load one JSON batch file and log its report."""
    # HINT 1: read_batch(path), then upsert_entries(conn, entries).
    # HINT 2: log.info("%s: %d inserted, %d updated, %d skipped",
    #                  Path(path).name, ...)
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# Given: the command line. Read it, do not change it.
# ---------------------------------------------------------------------------
def main(argv: list[str] | None = None) -> int:
    """Load each file given on the command line; return an exit code."""
    parser = argparse.ArgumentParser(description="Load CMS batches.")
    parser.add_argument("files", nargs="+", type=Path)
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(message)s")

    with connect() as conn:  # closes the connection at the end
        apply_schema(conn)
        for path in args.files:
            try:
                load_file(conn, path)
            except psycopg.errors.IntegrityError as exc:
                # IntegrityError is the parent of CheckViolation,
                # NotNullViolation and UniqueViolation
                log.error("%s: rejected, nothing saved (%s)",
                          path.name, exc.diag.constraint_name)
                return 1  # a non-zero exit code tells cron/CI it failed
        total = conn.execute("SELECT count(*) FROM entries").fetchone()[0]
        log.info("entries in table: %d", total)
    return 0


if __name__ == "__main__":
    # Expected output on an EMPTY table (DROP TABLE entries; to reset):
    #   $ python load.py batch_1.json batch_2.json
    #   batch_1.json: 5 inserted, 0 updated, 0 skipped
    #   batch_2.json: 1 inserted, 2 updated, 3 skipped
    #   entries in table: 6
    # The same command again (the point of today):
    #   batch_1.json: 0 inserted, 0 updated, 5 skipped
    #   batch_2.json: 0 inserted, 0 updated, 6 skipped
    #   entries in table: 6
    # And the bad batch (exit code 1, table unchanged):
    #   $ python load.py bad_batch.json
    #   bad_batch.json: rejected, nothing saved (entries_title_check)
    sys.exit(main())
