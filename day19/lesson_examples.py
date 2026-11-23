"""Day 19 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Constraints, rules the database enforces =====
# Concept 1: catch each kind of violation and read WHICH rule failed.
import os

import psycopg
from psycopg import errors  # one exception class per Postgres error code

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

BAD_ROWS = [
    ("blt201", None, "draft"),       # title missing
    ("blt101", "Copy", "draft"),     # uid already used
    ("blt202", "FAQ", "Published"),  # wrong case: the CHECK is exact
]
INSERT = "INSERT INTO lesson_entries (uid, title, status) VALUES (%s, %s, %s)"

with psycopg.connect(DB_URL, autocommit=True) as conn:
    for row in BAD_ROWS:
        try:
            conn.execute(INSERT, row)
        # All three classes inherit from errors.IntegrityError, so
        # "except errors.IntegrityError" would catch them all at once.
        except (errors.NotNullViolation, errors.UniqueViolation,
                errors.CheckViolation) as e:
            # diag = the structured details Postgres sent with the error
            print(type(e).__name__, "|", e.diag.constraint_name,
                  "|", e.diag.column_name)
# -> NotNullViolation | None | title
# -> UniqueViolation | lesson_entries_pkey | None
# -> CheckViolation | lesson_entries_status_check | None

# ===== section: Concept 2: Upserts with INSERT ... ON CONFLICT =====
# Concept 2: an upsert that says what it did: inserted, updated, unchanged.
import os

import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

UPSERT = """
INSERT INTO lesson_entries AS e (uid, title, status)
VALUES (%s, %s, %s)
ON CONFLICT (uid) DO UPDATE
    SET title = EXCLUDED.title, status = EXCLUDED.status,
        updated_at = now()
    -- only touch the row if something really changed; IS DISTINCT FROM
    -- is "!=" that also treats NULL = NULL as equal (Day 16's NULL rules)
    WHERE (e.title, e.status) IS DISTINCT FROM
          (EXCLUDED.title, EXCLUDED.status)
-- xmax is a hidden system column: 0 means this statement created the row.
-- A widely used trick; Postgres 18 can say it directly with RETURNING old.
RETURNING (xmax = 0) AS inserted
"""


def upsert(conn, uid: str, title: str, status: str) -> str:
    row = conn.execute(UPSERT, (uid, title, status)).fetchone()
    if row is None:  # the WHERE skipped the update, so nothing came back
        return "unchanged"
    return "inserted" if row[0] else "updated"


with psycopg.connect(DB_URL, autocommit=True) as conn:
    print(upsert(conn, "blt110", "Store finder", "draft"))      # -> inserted
    print(upsert(conn, "blt110", "Store finder", "draft"))      # -> unchanged
    print(upsert(conn, "blt110", "Store finder", "published"))  # -> updated
    # Run it 100 times: same final state. That is what "idempotent" means.
    for _ in range(100):
        upsert(conn, "blt110", "Store finder", "published")
    print(conn.execute(
        "SELECT count(*), max(status) FROM lesson_entries "
        "WHERE uid = 'blt110'").fetchone())  # -> (1, 'published')

# ===== section: Concept 3: Indexes, how a database finds rows fast =====
# Concept 3: the same query before and after an index, timed from Python.
import os
import time

import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

QUERY = """
SELECT sum(views) FROM lesson_views
WHERE entry_uid = %s AND viewed_on >= %s
"""
ARGS = ("blt0042", "2026-06-01")


def timed(conn) -> tuple[int, float]:
    start = time.perf_counter()  # like performance.now() in JS
    total = conn.execute(QUERY, ARGS).fetchone()[0]
    for _ in range(19):  # run it 20 times so one slow run does not mislead
        conn.execute(QUERY, ARGS).fetchone()
    ms = (time.perf_counter() - start) * 1000 / 20
    return total, round(ms, 2)


with psycopg.connect(DB_URL, autocommit=True) as conn:
    conn.execute("DROP INDEX IF EXISTS lesson_views_uid_day_idx")
    print("no index:  ", timed(conn))  # -> no index:   (25536, 10.77)
    # A B-tree index on the two columns the WHERE filters on, in that order.
    conn.execute(
        "CREATE INDEX lesson_views_uid_day_idx "
        "ON lesson_views (entry_uid, viewed_on)"
    )
    print("with index:", timed(conn))  # -> with index: (25536, 0.2)
# Same answer, about 50 times faster. Your milliseconds will differ;
# the size of the gap is the point.

# ===== section: Check your understanding (predict first, then run) =====
# Predict, then run. Re-run setup.sql before you start.
import psycopg

conn = psycopg.connect("postgresql://localhost/fde", autocommit=True)
ADD = "INSERT INTO lesson_entries (uid, title, slug, word_count) VALUES "

# 1: does this insert succeed? The CHECK is word_count >= 0.
conn.execute(ADD + "('blt301', 'A', 'a', NULL)")
print(conn.execute("SELECT count(*) FROM lesson_entries "
                   "WHERE uid = 'blt301'").fetchone())

# 2: slug is UNIQUE. Do both of these succeed?
conn.execute(ADD + "('blt302', 'B', NULL, 1)")
conn.execute(ADD + "('blt303', 'C', NULL, 1)")
print(conn.execute("SELECT count(*) FROM lesson_entries "
                   "WHERE slug IS NULL").fetchone())

# 3: what does fetchone() return here?
cur = conn.execute(ADD + "('blt101', 'X', 'x', 1) "
                   "ON CONFLICT (uid) DO NOTHING RETURNING uid")
print(cur.fetchone())

# 4: the same uid twice in ONE statement. What happens?
try:
    conn.execute(ADD + "('blt304', 'D', 'd', 1), ('blt304', 'E', 'e', 2) "
                 "ON CONFLICT (uid) DO UPDATE SET title = EXCLUDED.title")
except psycopg.Error as e:
    print(type(e).__name__, e)
