"""Day 18 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Connecting from Python with psycopg 3 =====
# Concept 1: connect, run one query, read the rows back as Python values.
import os
import psycopg  # the Postgres driver; like the "pg" package in Node

# FDE TIP: the connection string comes from the environment, never the code.
DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

with psycopg.connect(DB_URL) as conn:  # opens one connection to the server
    cur = conn.execute(
        "SELECT uid, title, views FROM demo_posts ORDER BY uid"
    )
    rows = cur.fetchall()  # a list of tuples, one tuple per row

print(len(rows))  # -> 4
print(rows[0])  # -> ('blt101', 'Getting started with SSO', 1200)
for uid, title, views in rows:  # unpack each tuple, like JS destructuring
    print(uid, views)
# -> blt101 1200
# -> blt102 860
# -> blt103 None    (SQL NULL arrives as Python None)
# -> blt104 40

# ===== section: Concept 1: Connecting from Python with psycopg 3 =====
# Concept 1: Postgres types arrive as real Python types, not strings.
import os
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

with psycopg.connect(DB_URL) as conn:
    cur = conn.execute(
        "SELECT views, published_at, status = 'published' AS live "
        "FROM demo_posts WHERE uid = 'blt101'"
    )
    row = cur.fetchone()  # exactly one row, or None if nothing matched

views, published_at, live = row
print(type(views).__name__, views)  # -> int 1200
print(type(published_at).__name__)  # -> datetime
print(published_at.isoformat())  # -> 2026-10-01T09:00:00+00:00
# The same moment is shown in the session time zone: a server set to India
# time prints 2026-10-01T14:30:00+05:30. Both are 09:00 UTC.
print(type(live).__name__, live)  # -> bool True
# GOTCHA: fetchone() on an empty result gives None, so row[0] would crash.
# Check "if row is None:" before you index into it.

# ===== section: Concept 1: Connecting from Python with psycopg 3 =====
# Concept 1: dict rows, so you read columns by name instead of position.
import os
import psycopg
from psycopg.rows import dict_row  # a "row factory": decides each row's shape

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

with psycopg.connect(DB_URL, row_factory=dict_row) as conn:
    cur = conn.execute(
        "SELECT uid, author FROM demo_posts WHERE author IS NOT NULL "
        "ORDER BY uid"
    )
    for row in cur:  # a cursor is iterable (Day 11): rows arrive one by one
        print(row)
# -> {'uid': 'blt101', 'author': 'Priya Nair'}
# -> {'uid': 'blt102', 'author': 'Rahul Mehta'}
# -> {'uid': 'blt104', 'author': "Sean O'Neil"}
# REMEMBER: connect -> execute -> fetch. The with block closes it for you.

# ===== section: Concept 2: Parameterised queries and SQL injection =====
# Concept 2: the WRONG way. Pasting input into SQL text lets input become SQL.
import os
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")


def find_by_author_UNSAFE(conn, author: str) -> list:
    # GOTCHA: an f-string builds the SQL text BEFORE Postgres sees it.
    query = f"SELECT uid FROM demo_posts WHERE author = '{author}'"
    print(query)  # show exactly what Postgres will run
    return conn.execute(query).fetchall()


with psycopg.connect(DB_URL) as conn:
    print(find_by_author_UNSAFE(conn, "Priya Nair"))
    # -> SELECT uid FROM demo_posts WHERE author = 'Priya Nair'
    # -> [('blt101',)]
    print(find_by_author_UNSAFE(conn, "x' OR '1'='1"))
    # -> SELECT uid FROM demo_posts WHERE author = 'x' OR '1'='1'
    # -> [('blt101',), ('blt102',), ('blt103',), ('blt104',)]
    # The quote in the input closed the string, and OR '1'='1' is true for
    # every row: a search box just returned the whole table.

# ===== section: Concept 2: Parameterised queries and SQL injection =====
# Concept 2: the RIGHT way. Placeholders send the value separately from SQL.
import os
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")


def find_by_author(conn, author: str) -> list:
    # %s is a placeholder, NOT Python's % formatting. No quotes around it.
    query = "SELECT uid FROM demo_posts WHERE author = %s"
    return conn.execute(query, (author,)).fetchall()  # values go as a tuple


with psycopg.connect(DB_URL) as conn:
    print(find_by_author(conn, "Priya Nair"))  # -> [('blt101',)]
    print(find_by_author(conn, "x' OR '1'='1"))  # -> []
    # The whole input is compared as one plain string: no author has it.
    print(find_by_author(conn, "Sean O'Neil"))  # -> [('blt104',)]
    # The apostrophe that broke the f-string version just works here.

    # Named placeholders read better when there are several values:
    cur = conn.execute(
        "SELECT uid FROM demo_posts "
        "WHERE status = %(status)s AND views >= %(min_views)s",
        {"status": "published", "min_views": 1000},  # a dict, keys = names
    )
    print(cur.fetchall())  # -> [('blt101',)]
# REMEMBER: values travel in the second argument, never inside the SQL text.

# ===== section: Concept 2: Parameterised queries and SQL injection =====
# Concept 2: three placeholder traps, and how to insert a table NAME safely.
import os
import psycopg
from psycopg import sql  # builds SQL from trusted pieces, like a template

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

with psycopg.connect(DB_URL) as conn:
    # Trap 1: one value still needs a tuple. ("blt101") is just a string.
    try:
        q = "SELECT title FROM demo_posts WHERE uid = %s"
        conn.execute(q, ("blt101"))  # missing comma: not a tuple
    except TypeError as err:
        print("TypeError:", err)
    # -> TypeError: query parameters should be a sequence or a mapping,
    #    got str
    # psycopg raised this before sending anything, so conn is still usable.

    # Trap 2: LIKE patterns. The % signs belong in the VALUE, not the SQL.
    term = "sso"
    cur = conn.execute(
        "SELECT uid FROM demo_posts WHERE title ILIKE %s", (f"%{term}%",)
    )
    print(cur.fetchall())  # -> [('blt101',)]

    # Trap 3: placeholders hold VALUES only, never table or column names.
    # A name chosen at run time goes through sql.Identifier, which quotes it.
    table = "demo_posts"
    query = sql.SQL("SELECT count(*) FROM {}").format(sql.Identifier(table))
    print(query.as_string(conn))  # -> SELECT count(*) FROM "demo_posts"
    print(conn.execute(query).fetchone())  # -> (4,)
# FDE TIP: if a name comes from users, also check it against an allow-list.

# ===== section: Concept 3: Transactions: all of it, or none of it =====
# Concept 3: psycopg opens a transaction for you. Uncommitted = invisible.
import os
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

writer = psycopg.connect(DB_URL)  # two separate connections, like two
reader = psycopg.connect(DB_URL)  # users on two laptops

writer.execute(
    "INSERT INTO demo_audit (post_uid, action) VALUES (%s, %s)",
    ("blt104", "review"),
)  # the first execute silently ran BEGIN: we are now inside a transaction
print(writer.info.transaction_status.name)  # -> INTRANS
count = "SELECT count(*) FROM demo_audit"
print(writer.execute(count).fetchone())  # -> (1,)   the writer sees its row
print(reader.execute(count).fetchone())  # -> (0,)   nobody else does yet

writer.commit()  # COMMIT: now the row is permanent and visible to all
print(reader.execute(count).fetchone())  # -> (1,)

writer.execute("DELETE FROM demo_audit")  # reset the lesson data...
writer.commit()  # ...and make the reset permanent too
writer.close()  # GOTCHA: close() WITHOUT commit() throws pending work away
reader.close()

# ===== section: Concept 3: Transactions: all of it, or none of it =====
# Concept 3: two changes that must happen together, or not at all.
import os
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")


def publish(conn, uid: str, action) -> None:
    # "with conn.transaction()" = BEGIN here; COMMIT if the block finishes,
    # ROLLBACK if any exception escapes it. Like try/catch around both writes.
    with conn.transaction():
        conn.execute(
            "UPDATE demo_posts SET status = 'published' WHERE uid = %s",
            (uid,),
        )
        conn.execute(
            "INSERT INTO demo_audit (post_uid, action) VALUES (%s, %s)",
            (uid, action),  # action None breaks the NOT NULL rule
        )


def state(conn) -> tuple:
    status = conn.execute(
        "SELECT status FROM demo_posts WHERE uid = 'blt104'"
    ).fetchone()[0]
    audits = conn.execute("SELECT count(*) FROM demo_audit").fetchone()[0]
    return status, audits


# autocommit=True: no hidden transaction; only our explicit block makes one.
with psycopg.connect(DB_URL, autocommit=True) as conn:
    print(state(conn))  # -> ('draft', 0)
    try:
        publish(conn, "blt104", None)  # the 2nd statement fails
    except psycopg.errors.NotNullViolation as err:
        print("failed:", err.diag.message_primary)
    # -> failed: null value in column "action" of relation "demo_audit"
    #    violates not-null constraint
    print(state(conn))  # -> ('draft', 0)   the UPDATE was undone too
    publish(conn, "blt104", "publish")  # both succeed: both are kept
    print(state(conn))  # -> ('published', 1)
    conn.execute(
        "UPDATE demo_posts SET status = 'draft' WHERE uid = 'blt104'"
    )
    conn.execute("DELETE FROM demo_audit")  # reset the lesson data
# REMEMBER: one business action = one transaction. All of it, or none of it.

# ===== section: Concept 3: Transactions: all of it, or none of it =====
# Concept 3: after an error, the transaction refuses all work until rollback.
import os
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

with psycopg.connect(DB_URL) as conn:  # default: implicit transactions
    try:
        conn.execute("SELECT * FROM demo_postz")  # typo: no such table
    except psycopg.errors.UndefinedTable as err:
        print("1st:", type(err).__name__)  # -> 1st: UndefinedTable
    try:
        conn.execute("SELECT count(*) FROM demo_posts")  # a valid query...
    except psycopg.errors.InFailedSqlTransaction as err:
        print("2nd:", err)
    # -> 2nd: current transaction is aborted, commands ignored until end
    #    of transaction block
    conn.rollback()  # end the broken transaction; the next one starts clean
    print(conn.execute("SELECT count(*) FROM demo_posts").fetchone())
    # -> (4,)
# GOTCHA: catching the error is not enough. Roll back, or every later query
# on this connection fails with the "aborted" message above.

# ===== section: Concept 4: Writing many rows: RETURNING, executemany and COPY =====
# Concept 4: get the new row's id back with RETURNING, then insert many rows.
import os
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")

with psycopg.connect(DB_URL) as conn:
    with conn.cursor() as cur:  # an explicit cursor, needed for executemany
        cur.execute(
            "INSERT INTO demo_posts (uid, title, author) VALUES (%s, %s, %s) "
            "RETURNING id",  # like a REST API answering 201 with the new id
            ("blt105", "Webhooks in five minutes", "Priya Nair"),
        )
        new_id = cur.fetchone()[0]
        print(new_id)  # -> 5
        # A second run prints 6: rollback does not give identity numbers back
        # (the gaps from Day 15).

        rows = [  # a list of tuples: one tuple per row to insert
            ("blt105", "2026-11-01", 120),
            ("blt105", "2026-11-02", 95),
            ("blt101", "2026-11-02", 310),
        ]
        # executemany runs the same INSERT once per tuple, in one round trip
        # batch (psycopg 3 pipelines them), all in the same transaction.
        cur.executemany(
            "INSERT INTO demo_views (uid, day, views) VALUES (%s, %s, %s)",
            rows,
        )
        print(cur.rowcount)  # -> 3   rows affected in total
    conn.rollback()  # lesson only: undo, keep the data as setup.sql made it

# ===== section: Concept 4: Writing many rows: RETURNING, executemany and COPY =====
# Concept 4: COPY streams rows into a table; the fastest way to bulk load.
import os
import time
from datetime import date, timedelta
import psycopg

DB_URL = os.environ.get("DATABASE_URL", "postgresql://localhost/fde")
start_day = date(2026, 1, 1)
rows = [  # 20,000 fake daily view counts
    (f"blt{i % 50:03d}", start_day + timedelta(days=i % 365), i % 900)
    for i in range(20_000)
]

with psycopg.connect(DB_URL) as conn:
    with conn.cursor() as cur:
        t0 = time.perf_counter()
        cur.executemany(
            "INSERT INTO demo_views (uid, day, views) VALUES (%s, %s, %s)",
            rows,
        )
        t1 = time.perf_counter()
        # COPY ... FROM STDIN: one command, then the rows stream after it.
        with cur.copy("COPY demo_views (uid, day, views) FROM STDIN") as cp:
            for row in rows:
                cp.write_row(row)  # psycopg converts each value for you
        t2 = time.perf_counter()
        print(f"executemany: {t1 - t0:.2f}s, copy: {t2 - t1:.2f}s")
        # -> executemany: 0.42s, copy: 0.02s   (your numbers will differ)
        print(cur.execute("SELECT count(*) FROM demo_views").fetchone())
        # -> (40000,)
    conn.rollback()  # lesson only: throw the fake rows away again
# FDE TIP: under ~10k rows executemany is fine and simpler to debug.
# For a customer's million-row backfill, use COPY.

# ===== section: Concept 5: From a flat CSV to linked tables =====
# Concept 5: CSV gives you strings only. Convert each field on purpose.
import csv
from datetime import datetime

with open("posts.csv", newline="", encoding="utf-8") as f:
    reader = csv.DictReader(f)  # each row becomes a dict keyed by the header
    rows = list(reader)

raw = rows[2]  # blt003, the draft with no author and no tags
# repr() shows the quotes, so empty strings are visible:
print(repr(raw["author"]), repr(raw["tags"]), repr(raw["word_count"]))
# -> '' '' '150'   every value is a str, even the number

print(int(raw["word_count"]) + 1)  # -> 151   int() turns '150' into 150
print(raw["author"] or None)  # -> None   '' is falsy, so "or" picks None
print(raw["published"] == "yes")  # -> False   'no' -> False, 'yes' -> True
print("".split("|"))  # -> ['']   GOTCHA: one empty tag, not zero tags
print([t for t in raw["tags"].split("|") if t])  # -> []
when = datetime.fromisoformat(rows[0]["updated_at"])  # '...T09:00:00Z'
print(when.isoformat())  # -> 2026-10-01T09:00:00+00:00   Z means UTC
print(rows[6]["author"])  # -> Sean O'Neil   safe to pass as a parameter
# REMEMBER: '' is not NULL. Decide for every column what empty means.

# ===== section: Check your understanding (predict first, then run) =====
# Predict, then run. Re-run setup.sql between the blocks.
import psycopg
URL = "postgresql://localhost/fde"
ADD = "INSERT INTO demo_audit (post_uid, action) VALUES (%s, %s)"
COUNT = "SELECT count(*) FROM demo_audit"

# 1: what does the last line print?
conn = psycopg.connect(URL)
conn.execute(ADD, ("blt101", "x"))
conn.close()
print(psycopg.connect(URL).execute(COUNT).fetchone())

# 2: which rows come back?
conn = psycopg.connect(URL)
q = "SELECT uid FROM demo_posts WHERE author = %s OR status = %s"
print(conn.execute(q, ("nobody", "draft")).fetchall())

# 3: what happens on the last line?
conn = psycopg.connect(URL)
q = "SELECT uid FROM demo_posts WHERE uid = '%s'"
conn.execute(q, ("blt101",))

# 4: with autocommit=True, what does the last line print?
conn = psycopg.connect(URL, autocommit=True)
try:
    with conn.transaction():
        conn.execute(ADD, ("blt101", "a"))
        conn.execute(ADD, ("blt101", None))
except psycopg.errors.NotNullViolation:
    pass
conn.execute(ADD, ("blt102", "b"))
print(conn.execute(COUNT).fetchone())
