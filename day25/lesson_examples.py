"""Day 25 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: TestClient, calling your API without a server =====
# TestClient: call your API in-process, no server and no network needed.
from fastapi import FastAPI, Header
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/v1/entries/{uid}")
def get_entry(uid: str, locale: str = "en-us",
              x_api_key: str | None = Header(default=None)) -> dict:
    # Header(): FastAPI reads X-Api-Key (underscores become dashes).
    return {"uid": uid, "locale": locale, "has_key": x_api_key is not None}


client = TestClient(app)  # built on httpx: the same API as requests (Day 6)

# params= builds the query string; headers= adds request headers.
resp = client.get("/v1/entries/blt1", params={"locale": "fr-fr"},
                  headers={"X-Api-Key": "k-123"})
print(resp.status_code)  # -> 200
print(resp.json())
# -> {'uid': 'blt1', 'locale': 'fr-fr', 'has_key': True}
print(resp.headers["content-type"])  # -> application/json
print(resp.request.url)
# -> http://testserver/v1/entries/blt1?locale=fr-fr
# "testserver" is a fake host: the request never leaves this process.

# A 4xx is a normal response, not an exception. TestClient never raises
# for it, so a test that forgets to check status_code passes by mistake.
missing = client.get("/v1/nothing-here")
print(missing.status_code, missing.json())
# -> 404 {'detail': 'Not Found'}    FastAPI's default shape (Concept 5)
# REMEMBER: assert the status code first, then the body.

# ===== section: Concept 1: TestClient, calling your API without a server =====
# "with TestClient(app)" runs the lifespan; raise_server_exceptions decides
# what a crash looks like in your test.
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("  startup")  # Day 24: the pool is opened here
    app.state.ready = True
    yield
    print("  shutdown")  # and closed here


app = FastAPI(lifespan=lifespan)


@app.get("/ready")
def ready() -> dict:
    return {"ready": app.state.ready}


@app.get("/crash")
def crash() -> dict:
    return {"total": 1 / 0}  # a bug: ZeroDivisionError


print("without with:")
try:
    TestClient(app).get("/ready")
except AttributeError as exc:
    print("  AttributeError:", exc)
# -> without with:
# ->   AttributeError: 'State' object has no attribute 'ready'
# The lifespan never ran, so nothing was put on app.state.

print("with:")
with TestClient(app) as client:  # startup runs HERE
    print(" ", client.get("/ready").json())
# shutdown runs when the with block ends
# -> with:
# ->   startup
# ->   {'ready': True}
# ->   shutdown

with TestClient(app) as client:  # default: raise_server_exceptions=True
    try:
        client.get("/crash")
    except ZeroDivisionError:
        print("  the bug is RAISED inside the test, with its traceback")
# -> startup, then the line above, then shutdown
# Good while you develop: you see the real error at once.

with TestClient(app, raise_server_exceptions=False) as client:
    resp = client.get("/crash")
    print(" ", resp.status_code, resp.text)
# -> startup
# ->   500 Internal Server Error
# -> shutdown
# What a real client would receive. Use this to test your 500 handling.

# ===== section: Concept 2: pytest fixtures for API tests =====
# Fixture scopes, yield fixtures and a factory.
# Run: python3 -m pytest -q -s --noconftest test_fixtures_demo.py
import pytest


@pytest.fixture(scope="session")  # built ONCE for the whole test run
def database() -> str:
    print("\n[session] create schema")
    yield "fde_test"  # code after yield = teardown, like Day 24's get_conn
    print("\n[session] drop schema")


@pytest.fixture  # default scope="function": built again for EVERY test
def clean(database: str) -> None:  # fixtures can use other fixtures
    print(f"[function] truncate tables in {database}")


@pytest.fixture
def make_entry():
    # A factory fixture returns a FUNCTION, so one test can make many
    # entries with different fields. Like a test-data builder in Jest.
    count = {"n": 0}  # a dict, so the inner function can change it

    def _make(**overrides) -> dict:
        count["n"] += 1
        entry = {"uid": f"blt{count['n']}", "title": "Untitled",
                 "status": "draft"}
        entry.update(overrides)  # the test only states what it cares about
        return entry

    return _make


def test_one(clean, make_entry) -> None:
    # Arrange
    a = make_entry(title="Home")
    b = make_entry(status="published")
    # Act + Assert
    assert (a["uid"], b["uid"]) == ("blt1", "blt2")
    assert b["title"] == "Untitled"


def test_two(clean, make_entry) -> None:
    # make_entry is NEW in this test, so its counter starts again at 1.
    assert make_entry()["uid"] == "blt1"

# ===== section: Concept 2: pytest fixtures for API tests =====
# parametrize: one test function, many cases.
# Run: python3 -m pytest -v --noconftest test_param_demo.py
import pytest
from fastapi import FastAPI, Query
from fastapi.testclient import TestClient

app = FastAPI()


@app.get("/v1/assets")
def list_assets(limit: int = Query(default=20, ge=1, le=50)) -> dict:
    return {"limit": limit}


client = TestClient(app)


# Each tuple becomes its own test, with its own pass or fail line.
@pytest.mark.parametrize("query, status", [
    ("", 200),           # the default, 20
    ("?limit=1", 200),   # lowest allowed
    ("?limit=50", 200),  # highest allowed
    ("?limit=0", 422),   # one below the edge
    ("?limit=51", 422),  # one above the edge
    ("?limit=ten", 422),  # not a number at all
])
def test_limit_edges(query: str, status: int) -> None:
    resp = client.get(f"/v1/assets{query}")  # Act: ONE request
    assert resp.status_code == status, resp.text  # message shown on failure
# -> test_param_demo.py::test_limit_edges[-200] PASSED
# -> test_param_demo.py::test_limit_edges[?limit=1-200] PASSED
# ->   ... four more lines ...
# -> test_param_demo.py::test_limit_edges[?limit=ten-422] PASSED
# -> 6 passed

# ===== section: Concept 3: A real test database =====
# A test database: a guard that protects real data, and two ways to reset.
import psycopg
from psycopg.conninfo import conninfo_to_dict


def guard(url: str) -> str:
    # conninfo_to_dict understands every URL style, so we never parse by hand.
    name = str(conninfo_to_dict(url).get("dbname", ""))
    if not name.endswith("_test"):
        raise SystemExit(f"refusing to run tests against {name!r}")
    return url


for url in ["postgresql:///fde_test",
            "postgresql://app:pw@db.acme.in:5432/cms",
            "dbname=fde host=localhost"]:
    try:
        print("ok     ", guard(url))
    except SystemExit as exc:
        print("blocked", exc)
# -> ok      postgresql:///fde_test
# -> blocked refusing to run tests against 'cms'
# -> blocked refusing to run tests against 'fde'


def fake_test(conn: psycopg.Connection, name: str) -> None:
    # Each "test" inserts the same filename, as two real tests might.
    try:
        conn.execute("INSERT INTO demo_assets VALUES ('logo.png')")
        print(name, "passed")
    except psycopg.errors.UniqueViolation:
        print(name, "FAILED: logo.png left over from an earlier test")


URL = guard("postgresql:///fde_test")
with psycopg.connect(URL, autocommit=True) as conn:
    conn.execute("SET client_min_messages = warning")  # hide the NOTICE
    conn.execute("DROP TABLE IF EXISTS demo_assets")
    conn.execute("CREATE TABLE demo_assets (filename text UNIQUE)")
    fake_test(conn, "test_a")  # -> test_a passed
    fake_test(conn, "test_b")  # -> test_b FAILED: logo.png left ...
    # test_b is correct; it fails only because test_a ran first.

    # Reset 1: TRUNCATE before every test. Simple, and works with any app.
    conn.execute("TRUNCATE demo_assets")
    fake_test(conn, "test_b")  # -> test_b passed

    # Reset 2: run the test inside a transaction and roll it back.
    conn.execute("TRUNCATE demo_assets")
    with conn.transaction(force_rollback=True):  # ROLLBACK at the end
        fake_test(conn, "test_c")  # -> test_c passed
    print(conn.execute("SELECT count(*) FROM demo_assets").fetchone())
    # -> (0,)   the insert was rolled back, nothing to clean up
    # GOTCHA: this only works when the app uses THIS connection. Our app
    # borrows its own connections from a pool, so for API tests we TRUNCATE.

# ===== section: Concept 3: A real test database =====
# Point cached settings at the test database.
# Run: python3 -m pytest -q -s --noconftest test_settings_demo.py
import os
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ACME_")
    database_url: str = "postgresql:///fde"  # the DEV database


@lru_cache
def get_settings() -> Settings:
    return Settings()


# Some module read the settings at import time, before any test ran.
print("\nat import:          ", get_settings().database_url)


def test_without_cache_clear(monkeypatch) -> None:
    # monkeypatch.setenv changes os.environ for THIS test only.
    monkeypatch.setenv("ACME_DATABASE_URL", "postgresql:///fde_test")
    print("without cache_clear:", get_settings().database_url)
    # The cache still holds the object built at import: the DEV URL.


def test_with_cache_clear(monkeypatch) -> None:
    monkeypatch.setenv("ACME_DATABASE_URL", "postgresql:///fde_test")
    get_settings.cache_clear()  # forget the old object
    print("with cache_clear:   ", get_settings().database_url)
    get_settings.cache_clear()  # and do not leak the test one either


def test_environment_is_restored() -> None:
    # monkeypatch undid setenv when each test ended.
    print("after the tests:    ", os.environ.get("ACME_DATABASE_URL"))

# ===== section: Concept 4: dependency_overrides =====
# dependency_overrides: swap a dependency for a fake, only in tests.
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient


class RealRepo:
    def get(self, uid: str) -> dict | None:
        raise RuntimeError("would connect to Postgres")  # not in this demo


def get_repo() -> RealRepo:
    return RealRepo()


app = FastAPI()


@app.get("/v1/assets/{uid}")
def get_asset(uid: str, repo: Annotated[RealRepo, Depends(get_repo)]) -> dict:
    row = repo.get(uid)
    if row is None:
        raise HTTPException(status_code=404, detail=f"asset {uid} not found")
    return row


class FakeRepo:
    """Only the methods the route calls. Data lives in a plain dict."""

    def __init__(self, rows: dict[str, dict]) -> None:
        self.rows = rows
        self.calls: list[str] = []  # record calls, to assert on them later

    def get(self, uid: str) -> dict | None:
        self.calls.append(uid)
        return self.rows.get(uid)


fake = FakeRepo({"blt1": {"uid": "blt1", "filename": "logo.png"}})
# KEY: the original function object. VALUE: a function FastAPI calls
# instead. Like jest.mock() for one module, but scoped to this app.
app.dependency_overrides[get_repo] = lambda: fake

client = TestClient(app)
print(client.get("/v1/assets/blt1").json())
# -> {'uid': 'blt1', 'filename': 'logo.png'}
print(client.get("/v1/assets/blt9").status_code)  # -> 404
print(fake.calls)  # -> ['blt1', 'blt9']   the route really used the fake


class DownRepo:
    def get(self, uid: str) -> dict | None:
        raise TimeoutError("db.acme.in:5432 timed out")


# A fake can also FAIL on purpose: the easiest way to test error paths.
app.dependency_overrides[get_repo] = lambda: DownRepo()
crash = TestClient(app, raise_server_exceptions=False)
print(crash.get("/v1/assets/blt1").status_code)  # -> 500

app.dependency_overrides.clear()  # REMEMBER: always clear after each test
try:
    client.get("/v1/assets/blt1")
except RuntimeError as exc:
    print("real dependency again:", exc)
# -> real dependency again: would connect to Postgres

# ===== section: Concept 4: dependency_overrides =====
# GOTCHA: overrides replace Depends(...) only, never a direct call.
from contextlib import asynccontextmanager
from functools import lru_cache
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient


@lru_cache
def get_settings() -> dict:
    return {"database_url": "postgresql:///fde"}  # pretend: from the env


@asynccontextmanager
async def lifespan(app: FastAPI):
    # A plain call: dependency_overrides has no say here.
    app.state.pool_url = get_settings()["database_url"]
    yield


app = FastAPI(lifespan=lifespan)


@app.get("/where")
def where(settings: Annotated[dict, Depends(get_settings)]) -> dict:
    return {"route_sees": settings["database_url"],
            "pool_uses": app.state.pool_url}


def test_settings() -> dict:
    return {"database_url": "postgresql:///fde_test"}


app.dependency_overrides[get_settings] = test_settings
with TestClient(app) as client:
    print(client.get("/where").json())
# -> {'route_sees': 'postgresql:///fde_test',
#     'pool_uses': 'postgresql:///fde'}
# The route was fooled, but the pool still points at the DEV database.
# That is why today's conftest changes the ENVIRONMENT and calls
# get_settings.cache_clear() instead of overriding get_settings.

# ===== section: Concept 5: One error shape for the whole API =====
# FastAPI's default errors: three different shapes for one client to parse.
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

app = FastAPI()


class AssetIn(BaseModel):
    filename: str
    size_bytes: int


@app.post("/v1/assets")
def create(body: AssetIn) -> dict:
    raise HTTPException(status_code=409, detail="filename already exists")


@app.get("/v1/assets/{uid}")
def get_one(uid: str) -> dict:
    return {"total": 1 / 0}  # a bug


c = TestClient(app, raise_server_exceptions=False)
ok_body = {"filename": "a.png", "size_bytes": 1}
print(c.post("/v1/assets", json=ok_body).json())
# -> {'detail': 'filename already exists'}           detail is a STRING
r = c.post("/v1/assets", json={"filename": "a.png", "size_bytes": "big"})
first = r.json()["detail"][0]
print(r.status_code, first["loc"], first["msg"])
# -> 422 ['body', 'size_bytes'] Input should be a valid integer, ...
#                                                    detail is a LIST
r = c.get("/v1/assets/blt1")
print(r.status_code, r.headers["content-type"], repr(r.text))
# -> 500 text/plain; charset=utf-8 'Internal Server Error'   NOT JSON at all
# A front end doing resp.json().detail breaks on two of these three.

# ===== section: Concept 5: One error shape for the whole API =====
# Exception handlers: one place that turns an exception into a response.
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient
from starlette.exceptions import HTTPException as StarletteHTTPException


class ApiError(Exception):  # our own base class, like class X extends Error
    status = 500
    code = "internal_error"

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class NotFoundError(ApiError):
    status = 404
    code = "not_found"


app = FastAPI()


def shape(status: int, code: str, message: str) -> JSONResponse:
    # A tiny version of today's error contract (errors.py has the full one).
    return JSONResponse({"error": {"status": status, "code": code,
                                   "message": message}}, status_code=status)


@app.exception_handler(ApiError)  # also catches every SUBCLASS of ApiError
async def on_api_error(request: Request, exc: ApiError) -> JSONResponse:
    return shape(exc.status, exc.code, exc.message)


@app.exception_handler(StarletteHTTPException)  # the router's 404 and 405
async def on_http(request: Request, exc: StarletteHTTPException):
    return shape(exc.status_code, "http_error", str(exc.detail))


@app.get("/v1/assets/{uid}")
def get_one(uid: str) -> dict:
    raise NotFoundError(f"asset {uid} not found")  # raise, never return


c = TestClient(app)
print(c.get("/v1/assets/blt7").json())
# -> {'error': {'status': 404, 'code': 'not_found',
#               'message': 'asset blt7 not found'}}
print(c.get("/no/such/route").json())
# -> {'error': {'status': 404, 'code': 'http_error',
#               'message': 'Not Found'}}
# Same shape, two different causes: the client needs only one parser.

# ===== section: Check your understanding (predict first, then run) =====
# Six predictions. Write each answer down BEFORE you run the file.
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

app = FastAPI()


def get_tenant() -> str:
    return "acme"


def get_tenant_for_tests() -> str:
    return "test-tenant"


@app.get("/tenant")
def tenant(t: Annotated[str, Depends(get_tenant)]) -> dict:
    return {"tenant": t}


@app.get("/items")
def items(limit: Annotated[int, Query(ge=1)] = 10) -> dict:
    return {"limit": limit}


@app.get("/gone")
def gone() -> dict:
    raise HTTPException(status_code=410, detail="moved to /v2")


@app.exception_handler(HTTPException)
async def on_http(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse({"error": exc.detail}, status_code=exc.status_code)


client = TestClient(app)
r = client.get("/items?limit=0")
print("Q1", r.status_code, r.json()["detail"][0]["loc"])
print("Q2", client.get("/gone").json())
print("Q3", client.get("/nowhere").json())

app.dependency_overrides[get_tenant_for_tests] = get_tenant
print("Q4", client.get("/tenant").json())
app.dependency_overrides = {get_tenant: get_tenant_for_tests}
print("Q5", client.get("/tenant").json())


def make() -> list:
    made = []

    def _make(name: str) -> list:
        made.append(name)
        return made

    return _make


f, g = make(), make()
f("a")
f("b")
print("Q6", g("c"))
