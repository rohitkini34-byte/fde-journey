"""Day 24 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Settings from environment variables =====
# Settings from environment variables, with pydantic-settings.
import os

from pydantic import Field, SecretStr, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # env_prefix: ACME_DATABASE_URL fills database_url, and so on.
    # extra="ignore": other ACME_ variables do not cause an error.
    model_config = SettingsConfigDict(env_prefix="ACME_", extra="ignore")

    database_url: SecretStr  # no default, so it is REQUIRED
    pool_max_size: int = Field(default=5, ge=1)  # optional, at least 1
    debug: bool = False


# In real life these come from the shell, Docker or the cloud console.
# Here we set them in code only to show what Settings() does with them.
os.environ["ACME_DATABASE_URL"] = "postgresql://app:hunter2@db.acme.in/cms"
os.environ["ACME_POOL_MAX_SIZE"] = "10"  # env values are ALWAYS strings
os.environ["ACME_DEBUG"] = "yes"

s = Settings()
print(s.pool_max_size, type(s.pool_max_size).__name__)
# -> 10 int        the string "10" was converted, like Day 23's lax mode
print(s.debug)
# -> True          "yes", "true", "1" and "on" all mean True
print(s.database_url)
# -> **********    SecretStr hides the value when printed or logged
print(s)
# -> database_url=SecretStr('**********') pool_max_size=10 debug=True
print(s.database_url.get_secret_value())
# -> postgresql://app:hunter2@db.acme.in/cms   only when you ask for it

del os.environ["ACME_DATABASE_URL"]  # simulate a missing variable
try:
    Settings()
except ValidationError as exc:
    err = exc.errors()[0]
    print(err["loc"], err["type"])
# -> ('database_url',) missing    the app refuses to start without it

# ===== section: Concept 1: Settings from environment variables =====
# A .env file, which source wins, and reading settings only once.
import os
from functools import lru_cache
from pathlib import Path

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

# Start clean: forget any ACME_ variables set earlier in this session.
for key in [k for k in os.environ if k.startswith("ACME_")]:
    del os.environ[key]

# A .env file is plain KEY=value lines, like the .env files Vite reads.
# (Named demo.env here so it cannot clash with your real day24/.env.)
Path("demo.env").write_text(
    "ACME_DATABASE_URL=postgresql:///fde\nACME_POOL_MAX_SIZE=4\n",
    encoding="utf-8",
)


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACME_", env_file="demo.env",
                                      extra="ignore")
    database_url: SecretStr
    pool_max_size: int = 5


print(Settings().pool_max_size)  # -> 4   from the demo.env file
os.environ["ACME_POOL_MAX_SIZE"] = "12"
print(Settings().pool_max_size)  # -> 12  an environment variable wins
print(Settings(pool_max_size=2).pool_max_size)  # -> 2   an argument wins


@lru_cache  # run the body once, then return the same object every time
def get_settings() -> Settings:
    print("reading settings...")
    return Settings()


a = get_settings()
b = get_settings()
print(a is b)
# -> reading settings...     printed once: the second call used the cache
# -> True                    the same object both times
Path("demo.env").unlink()  # tidy up the demo file

# ===== section: Concept 2: Dependency injection with Depends =====
# Depends: one function supplies shared inputs to many routes.
from typing import Annotated

from fastapi import Depends, FastAPI, Query
from fastapi.testclient import TestClient

app = FastAPI()


# A dependency is a plain function. FastAPI reads ITS parameters from the
# request too, so limit and cursor become query parameters of every route
# that uses it.
def paging(
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    cursor: str | None = None,
) -> dict:
    return {"limit": limit, "cursor": cursor}


# Name it once with Annotated, then reuse it like a type.
Paging = Annotated[dict, Depends(paging)]


@app.get("/v1/entries")
def list_entries(page: Paging) -> dict:
    return {"entries": page}


@app.get("/v1/assets")
def list_assets(page: Paging) -> dict:
    return {"assets": page}


c = TestClient(app)
print(c.get("/v1/entries?limit=5").json())
# -> {'entries': {'limit': 5, 'cursor': None}}
print(c.get("/v1/assets?cursor=blt9").json())
# -> {'assets': {'limit': 20, 'cursor': 'blt9'}}
print(c.get("/v1/assets?limit=99").status_code)
# -> 422   the rule lives in ONE place and protects every route
# FDE TIP: /docs lists limit and cursor on both routes automatically.

# ===== section: Concept 2: Dependency injection with Depends =====
# A yield dependency: setup, hand over, then clean up after the route.
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

app = FastAPI()


def get_conn():
    print("  1. take a connection from the pool")
    try:
        yield "conn-42"  # the route runs while we are paused here
        print("  3. no error: COMMIT")
    except Exception as exc:  # anything the route raised lands here
        print(f"  3. {type(exc).__name__}: ROLLBACK")
        raise  # GOTCHA: re-raise, or FastAPI cannot send the error
    finally:
        print("  4. give the connection back")


Conn = Annotated[str, Depends(get_conn)]


@app.get("/ok")
def ok(conn: Conn) -> dict:
    print(f"  2. route runs with {conn}")
    return {"conn": conn}


@app.get("/missing")
def missing(conn: Conn) -> dict:
    print(f"  2. route runs with {conn}")
    raise HTTPException(status_code=404, detail="not found")


c = TestClient(app)
print("GET /ok")
print("  ->", c.get("/ok").status_code)
# -> GET /ok
# ->   1. take a connection from the pool
# ->   2. route runs with conn-42
# ->   3. no error: COMMIT
# ->   4. give the connection back
# ->   -> 200
print("GET /missing")
print("  ->", c.get("/missing").status_code)
# -> GET /missing
# ->   1. take a connection from the pool
# ->   2. route runs with conn-42
# ->   3. HTTPException: ROLLBACK      a 404 is an exception, so: rollback
# ->   4. give the connection back
# ->   -> 404

# Tests can swap any dependency for a fake, without touching the routes.
app.dependency_overrides[get_conn] = lambda: "fake-conn"
print("GET /ok with an override ->", c.get("/ok").json())
# ->   2. route runs with fake-conn
# -> GET /ok with an override -> {'conn': 'fake-conn'}
app.dependency_overrides.clear()  # always undo overrides after a test

# ===== section: Concept 3: Connection pools and the app lifespan =====
# A connection pool versus a new connection for every query.
import time

import psycopg
from psycopg_pool import ConnectionPool

URL = "postgresql:///fde"  # local Postgres, database fde (Week 3)

start = time.perf_counter()
for _ in range(50):
    # A new connection each time: TCP or socket, login, session setup.
    with psycopg.connect(URL) as conn:
        conn.execute("SELECT 1")
per_query = (time.perf_counter() - start) * 1000 / 50
print(f"new connection each time: {per_query:.2f} ms per query")
# -> new connection each time: 2.12 ms per query   (yours will differ)

# open=True connects min_size connections now; "with" closes them all at
# the end. Like a pool of database clients in Node's pg library.
with ConnectionPool(URL, min_size=2, max_size=5, open=True) as pool:
    pool.wait()  # block until the first min_size connections are ready
    start = time.perf_counter()
    for _ in range(50):
        # Borrow a ready connection, use it, hand it back.
        with pool.connection() as conn:
            conn.execute("SELECT 1")
    per_query = (time.perf_counter() - start) * 1000 / 50
    print(f"borrowed from the pool:   {per_query:.2f} ms per query")
    # -> borrowed from the pool:   0.11 ms per query   about 20x faster
    stats = pool.get_stats()
    print({k: stats[k] for k in ("pool_min", "pool_max", "pool_size",
                                 "requests_num")})
    # -> {'pool_min': 2, 'pool_max': 5, 'pool_size': 2, 'requests_num': 50}
    # 50 requests were served by only 2 real connections.
# GOTCHA: locally a new connection costs about 2 ms. To a cloud database
# with TLS it is often 20 to 100 ms, on EVERY request, before any query.

# ===== section: Concept 3: Connection pools and the app lifespan =====
# pool.connection() is a transaction: COMMIT on success, ROLLBACK on error.
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool, PoolTimeout

URL = "postgresql:///fde"

with ConnectionPool(URL, min_size=1, max_size=2, open=True,
                    kwargs={"row_factory": dict_row}) as pool:
    with pool.connection() as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS pool_demo (n integer)")
        conn.execute("TRUNCATE pool_demo")

    with pool.connection() as conn:
        conn.execute("INSERT INTO pool_demo VALUES (1)")
    # The block ended normally, so the pool COMMITTED the insert.

    try:
        with pool.connection() as conn:
            conn.execute("INSERT INTO pool_demo VALUES (2)")
            raise ValueError("boom")  # something fails halfway
    except ValueError:
        pass
    # The block ended with an error, so the pool ROLLED BACK insert 2.

    with pool.connection() as conn:
        # dict_row: each row is a dict, like rows in Node's pg library.
        print(conn.execute("SELECT n FROM pool_demo").fetchall())
        # -> [{'n': 1}]      row 2 was rolled back

# A pool with ONE connection, and a second request while it is busy.
with ConnectionPool(URL, min_size=1, max_size=1, timeout=0.5,
                    open=True) as pool:
    with pool.connection():  # request A holds the only connection
        try:
            with pool.connection():  # request B waits up to 0.5 s
                pass
        except PoolTimeout as exc:
            print("PoolTimeout:", exc)
            # -> PoolTimeout: couldn't get a connection after 0.50 sec
# FDE TIP: max_size x number of app instances must stay below the
# database's max_connections (often 100). 10 pods x 20 = 200 is too many.

# ===== section: Concept 4: The repository layer =====
# A small repository: the ONLY place that knows the SQL for entries.
import secrets

import psycopg
from psycopg import errors, sql
from psycopg.rows import dict_row


class DuplicateSlugError(Exception):
    """Our own error, so the API layer never imports psycopg errors."""


class EntryRepository:
    def __init__(self, conn: psycopg.Connection) -> None:
        self.conn = conn  # given from outside (Depends), not created here

    def create(self, title: str, slug: str) -> dict:
        uid = "blt" + secrets.token_hex(8)  # 16 random hex characters
        try:
            # transaction() inside an open transaction is a SAVEPOINT: if
            # the INSERT fails, only this part is undone, and the
            # connection stays usable.
            with self.conn.transaction():
                cur = self.conn.execute(
                    "INSERT INTO api_entries (uid, title, slug, content_type)"
                    " VALUES (%s, %s, %s, 'blog_post')"
                    " RETURNING uid, title, slug, status, version",
                    (uid, title, slug),  # values travel separately (Day 18)
                )
                return cur.fetchone()  # RETURNING: the row, in one trip
        except errors.UniqueViolation as exc:  # the UNIQUE (slug) rule
            raise DuplicateSlugError(slug) from exc

    def get(self, uid: str) -> dict | None:
        cur = self.conn.execute(
            "SELECT uid, title, slug, status, version"
            " FROM api_entries WHERE uid = %s",
            (uid,),  # GOTCHA: (uid,) with a comma is a tuple; (uid) is not
        )
        return cur.fetchone()  # None when no row matched


with psycopg.connect("postgresql:///fde", row_factory=dict_row) as conn:
    repo = EntryRepository(conn)
    row = repo.create("Monsoon sale", "monsoon-sale")
    print(row["title"], row["status"], row["version"], len(row["uid"]))
    # -> Monsoon sale draft 1 19   status and version came from DEFAULTs
    print(repo.get(row["uid"])["slug"])
    # -> monsoon-sale
    print(repo.get("blt-missing"))
    # -> None
    try:
        repo.create("Monsoon sale again", "monsoon-sale")
    except DuplicateSlugError as exc:
        print("duplicate slug:", exc)
    # -> duplicate slug: monsoon-sale
    print(repo.get(row["uid"])["title"])  # still works after the error
    # -> Monsoon sale      thanks to the savepoint
    conn.rollback()  # demo only: leave the table empty for later examples

# Safe dynamic SQL: column names go through sql.Identifier, values stay %s.
changes = {"title": "New title", "tags": ["sale"]}
sets = sql.SQL(", ").join(
    sql.SQL("{} = {}").format(sql.Identifier(col), sql.Placeholder(col))
    for col in changes
)
query = sql.SQL("UPDATE api_entries SET {} WHERE uid = %(uid)s").format(sets)
with psycopg.connect("postgresql:///fde") as conn:
    print(query.as_string(conn))
# -> UPDATE api_entries SET "title" = %(title)s, "tags" = %(tags)s
#    WHERE uid = %(uid)s       (printed on one line)
# Names are quoted identifiers; values are still parameters.

# ===== section: Concept 5: Wiring it together, request by request =====
# The whole chain: lifespan -> pool -> get_conn -> repository -> route.
from collections.abc import Iterator
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.testclient import TestClient
from psycopg import Connection
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

URL = "postgresql:///fde"  # Day 24's task reads this from Settings instead


# lifespan: code that runs once at startup (before yield) and once at
# shutdown (after it). Like a useEffect with an empty dependency list
# and a cleanup function, but for the whole server.
@asynccontextmanager
async def lifespan(app: FastAPI):
    print("startup: open the pool")
    pool = ConnectionPool(URL, min_size=1, max_size=5, open=False,
                          kwargs={"row_factory": dict_row})
    pool.open(wait=True, timeout=10)  # fail at startup if the DB is down
    app.state.pool = pool  # app.state: a place for app-wide objects
    yield  # the server handles requests while we are paused here
    pool.close()
    print("shutdown: pool closed")


app = FastAPI(lifespan=lifespan)


def get_conn(request: Request) -> Iterator[Connection]:
    # One connection per request; commit or rollback happens on exit.
    with request.app.state.pool.connection() as conn:
        yield conn


Conn = Annotated[Connection, Depends(get_conn)]


@app.post("/v1/notes", status_code=201)
def create_note(conn: Conn) -> dict:
    row = conn.execute(
        "INSERT INTO api_entries (uid, title, slug, content_type)"
        " VALUES ('blt1', 'Hello', 'hello', 'blog_post') RETURNING uid"
    ).fetchone()
    return row


@app.get("/v1/notes/{uid}")
def get_note(uid: str, conn: Conn) -> dict:
    row = conn.execute("SELECT uid, title FROM api_entries WHERE uid = %s",
                       (uid,)).fetchone()
    if row is None:
        raise HTTPException(status_code=404, detail=f"{uid} not found")
    return row


# "with TestClient(app)" runs the lifespan, like starting the server.
with TestClient(app) as first_run:
    print(first_run.post("/v1/notes").json())
# -> startup: open the pool
# -> {'uid': 'blt1'}
# -> shutdown: pool closed

# A brand-new startup: a new pool, nothing left in Python memory.
with TestClient(app) as second_run:
    print(second_run.get("/v1/notes/blt1").json())
    print(second_run.get("/v1/notes/blt2").status_code)
# -> startup: open the pool
# -> {'uid': 'blt1', 'title': 'Hello'}    it survived the restart
# -> 404
# -> shutdown: pool closed
# Clean up: psql -d fde -c "TRUNCATE api_entries" before the task.

# ===== section: Check your understanding (predict first, then run) =====
# Six predictions. Write each answer down BEFORE you run the file.
import os
from typing import Annotated

import psycopg
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from psycopg.rows import dict_row
from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACME_")
    database_url: SecretStr
    pool_max_size: int = 5


os.environ["ACME_DATABASE_URL"] = "postgresql:///fde"
os.environ["ACME_POOL_MAX_SIZE"] = "3"
print("Q1", Settings(pool_max_size=8).pool_max_size)
print("Q2", Settings().database_url)

calls = []


def get_conn():
    calls.append("conn")
    yield "conn"


def get_repo(conn: Annotated[str, Depends(get_conn)]) -> str:
    return f"repo({conn})"


app = FastAPI()


@app.get("/x")
def x(repo: Annotated[str, Depends(get_repo)],
      conn: Annotated[str, Depends(get_conn)]) -> dict:
    return {"repo": repo, "conn": conn}


print("Q3", TestClient(app).get("/x").json(), len(calls))

with psycopg.connect("postgresql:///fde", row_factory=dict_row) as conn:
    print("Q4", conn.execute("SELECT %s AS v", ("x' OR '1'='1",)).fetchone())
    print("Q5", conn.execute("SELECT 1 AS n WHERE false").fetchone())
    conn.execute("CREATE TEMP TABLE t (n integer)")
    try:
        with conn.transaction():
            conn.execute("INSERT INTO t VALUES (1)")
            conn.execute("INSERT INTO t VALUES ('one')")
    except psycopg.errors.InvalidTextRepresentation:
        pass
    print("Q6", conn.execute("SELECT count(*) AS c FROM t").fetchone())
