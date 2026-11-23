"""Day 21 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Check your understanding (predict first, then run) =====
# Question 7 (Day 18): predict what each block prints, then run it.
import psycopg

# use your own connection string here (the DATABASE_URL from Day 18)
URL = "postgresql://postgres@localhost/postgres"

with psycopg.connect(URL) as conn:
    conn.execute("CREATE TEMP TABLE t (id int PRIMARY KEY, title text)")
    # a) one parameter passed without the tuple comma
    try:
        conn.execute("INSERT INTO t VALUES (%s, %s)", (1, "Home"))
        conn.execute("SELECT title FROM t WHERE id = %s", 1)
    except TypeError as e:
        print("a)", type(e).__name__)
    # b) an error inside conn.transaction() rolls back only that block
    try:
        with conn.transaction():
            conn.execute("INSERT INTO t VALUES (2, 'About')")
            conn.execute("INSERT INTO t VALUES (1, 'Dup')")  # id 1 exists
    except psycopg.errors.UniqueViolation:
        print("b) duplicate key")
    rows = conn.execute("SELECT id FROM t ORDER BY id").fetchall()
    print("c)", rows)
