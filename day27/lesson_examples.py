"""Day 27 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: One project, not five folders =====
# Why "from settings import ..." breaks once files move into a package.
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(tempfile.mkdtemp())  # a throwaway folder for the experiment
pkg = root / "src" / "content_sync_api"
pkg.mkdir(parents=True)
(pkg / "__init__.py").write_text("")  # makes the folder a package
(pkg / "settings.py").write_text("NAME = 'acme'\n")
# Day 26 style: a FLAT import, which only works when settings.py sits
# in the folder you run Python from.
(pkg / "flat.py").write_text("from settings import NAME\n")
# Day 27 style: an ABSOLUTE import that names the package.
(pkg / "absolute.py").write_text(
    "from content_sync_api.settings import NAME\nprint(NAME)\n")

def run(module: str) -> str:
    # -c "import ..." with src/ on the path, the way an installed package
    # (uv run, pytest, uvicorn) sees your code.
    proc = subprocess.run(
        [sys.executable, "-c", f"import content_sync_api.{module}"],
        cwd=root, env={"PYTHONPATH": "src"}, capture_output=True, text=True)
    return (proc.stdout or proc.stderr.strip().splitlines()[-1]).strip()

print(run("flat"))
# -> ModuleNotFoundError: No module named 'settings'
print(run("absolute"))
# -> acme

# ===== section: Concept 1: One project, not five folders =====
# One version number, read from the installed package's metadata.
from importlib.metadata import PackageNotFoundError, version

# version() reads what pyproject.toml said when the package was installed,
# like reading "version" from package.json in a Node app.
print(version("fastapi"))  # -> 0.165.0  (whatever is installed for you)

try:
    print(version("content-sync-api"))
except PackageNotFoundError:
    # Not installed yet. After "uv sync" this prints 0.1.0.
    print("content-sync-api is not installed in this environment")
# -> content-sync-api is not installed in this environment

# ===== section: Concept 2: Logging a web service: one JSON line and one request id per request =====
# ContextVar: a "current request id" that each request sees separately.
import asyncio
from contextvars import ContextVar

# Like React context: set once near the top, read anywhere below,
# without passing it through every function's arguments.
request_id: ContextVar[str] = ContextVar("request_id", default="-")

def log(message: str) -> None:
    # Deep inside the code: no request object here, yet we know the id.
    print(f"[{request_id.get()}] {message}")

async def handle(rid: str, delay: float) -> None:
    request_id.set(rid)  # each asyncio task gets its OWN copy of the var
    log("start")
    await asyncio.sleep(delay)  # the other request runs meanwhile
    log("done")

async def main() -> None:
    # Two requests in flight at once, as on a real server (Day 13).
    await asyncio.gather(handle("req-A", 0.02), handle("req-B", 0.01))

asyncio.run(main())
# -> [req-A] start
# -> [req-B] start
# -> [req-B] done
# -> [req-A] done      each line kept its own id, although they interleave
log("outside any request")
# -> [-] outside any request   the default: nothing was set out here

# ===== section: Concept 2: Logging a web service: one JSON line and one request id per request =====
# A tiny JSON formatter: one log event becomes one line of JSON.
import json
import logging
import sys

class MiniJsonFormatter(logging.Formatter):
    # format() is called once per log event; whatever it returns is written.
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),  # the message with %s filled in
        }
        # extra={"fields": {...}} on the log call becomes record.fields.
        # getattr with a default: not every log call passes fields.
        entry.update(getattr(record, "fields", {}))
        return json.dumps(entry)  # like JSON.stringify() in JS

handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(MiniJsonFormatter())
logger = logging.getLogger("acme.sync")
logger.addHandler(handler)
logger.setLevel(logging.INFO)
logger.propagate = False  # only our handler prints (no duplicate lines)

logger.info("webhook %s", "processed",
            extra={"fields": {"uid": "blt_home_001", "duration_ms": 12.4}})
# -> {"level": "INFO", "logger": "acme.sync", "message": "webhook processed",
# ->  "uid": "blt_home_001", "duration_ms": 12.4}   (one line in reality)

# ===== section: Concept 2: Logging a web service: one JSON line and one request id per request =====
# Middleware: code that runs around EVERY request, like Express app.use().
import time

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

app = FastAPI()

@app.middleware("http")
async def add_timing(request: Request, call_next):
    start = time.perf_counter()  # a precise clock for durations
    # call_next passes the request on to the route and waits for the answer.
    # Everything above this line runs BEFORE the route, below it AFTER.
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Process-Time-Ms"] = f"{elapsed_ms:.1f}"
    print(request.method, request.url.path, response.status_code)
    return response

@app.get("/v1/entries/{uid}")
def read_entry(uid: str) -> dict:
    return {"uid": uid}

client = TestClient(app)
r = client.get("/v1/entries/blt1?locale=en-us")
# -> GET /v1/entries/blt1 200   url.path has no query string
print("X-Process-Time-Ms" in r.headers)  # -> True
client.get("/nope")
# -> GET /nope 404   middleware also sees requests that match no route

# ===== section: Concept 2: Logging a web service: one JSON line and one request id per request =====
# One access line from the finished middleware (wrapped here to fit; it is
# ONE line in reality):
# {"ts": "2026-11-20T02:24:45.827+00:00", "level": "INFO",
#  "logger": "content_sync_api.access", "message": "request",
#  "request_id": "cs-7f3a", "method": "GET",
#  "path": "/v1/entries/blt_home_001", "status": 200, "duration_ms": 1.1}

# ===== section: Concept 3: Logs that never leak and never lie =====
# Three ways logs leak or lie, and the habit that prevents each one.
import json

from pydantic import SecretStr

# 1. Logging whole headers leaks credentials into the log platform.
headers = {"accept": "application/json", "x-api-key": "acme_live_9f2c"}
print(f"incoming {headers}")
# -> incoming {'accept': 'application/json', 'x-api-key': 'acme_live_9f2c'}
# GOTCHA: anyone with log access (vendors, support) now holds a live key.

# A first redaction pass: replace values of known sensitive keys.
SENSITIVE = {"x-api-key", "authorization"}
safe = {k: ("***" if k in SENSITIVE else v) for k, v in headers.items()}
print(f"incoming {safe}")
# -> incoming {'accept': 'application/json', 'x-api-key': '***'}

# 2. SecretStr (Day 24) hides itself when printed or put in an f-string.
db_url = SecretStr("postgresql://app:hunter2@db.acme.in/cms")
print(f"connecting to {db_url}")  # -> connecting to **********

# 3. Log injection: a caller-controlled value with a newline in it.
rid = "abc\n2026-11-20 INFO payment approved user=admin"
print(f"request_id={rid} status=401")
# -> request_id=abc
# -> 2026-11-20 INFO payment approved user=admin status=401
# A plain-text log now shows a fake second line written by an attacker.
print(json.dumps({"request_id": rid, "status": 401}))
# -> {"request_id": "abc\n2026-11-20 INFO payment ...", "status": 401}
# JSON escapes the newline as \n: it stays ONE line, clearly one field.

# ===== section: Concept 4: OpenAPI docs as a deliverable =====
# OpenAPI as a deliverable: metadata, tags, summaries, errors, examples.
from typing import Annotated

from fastapi import FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from pydantic import BaseModel, Field

app = FastAPI(
    title="Acme content sync API",  # the heading of /docs
    version="0.1.0",  # FDE TIP: bump this with every release you hand over
    description="Keeps Acme's Contentstack entries in Postgres.",
    openapi_tags=[  # one description per tag, shown as sections in /docs
        {"name": "entries", "description": "Read synced entries."},
    ],
)
api_key = APIKeyHeader(name="X-API-Key", auto_error=False)

class Entry(BaseModel):
    # examples=[...] fills the "Example Value" box in /docs, like a
    # Storybook story that shows a component with realistic props.
    uid: str = Field(examples=["blt_home_001"])
    title: str = Field(examples=["Home page"])
    locale: str = Field(default="en-us", examples=["en-us"])

@app.get(
    "/v1/entries/{uid}",
    tags=["entries"],
    summary="Read one synced entry",  # the one-line title of the operation
    response_model=Entry,  # documents AND filters the response body
    responses={  # errors are part of the contract too
        401: {"description": "Missing or invalid X-API-Key"},
        404: {"description": "No entry with this uid"},
    },
)
def read_entry(uid: str,
               key: Annotated[str | None, Security(api_key)]) -> Entry:
    """Return the latest published version of an entry."""  # -> description
    if key is None:
        raise HTTPException(status_code=401, detail="invalid api key")
    return Entry(uid=uid, title="Home page")

schema = app.openapi()  # the same dict that /openapi.json serves
op = schema["paths"]["/v1/entries/{uid}"]["get"]
print(schema["info"]["title"], schema["info"]["version"])
# -> Acme content sync API 0.1.0
print(op["summary"], "|", op["description"])
# -> Read one synced entry | Return the latest published version of an entry.
print(sorted(op["responses"]))  # -> ['200', '401', '404', '422']
# 422 was added by FastAPI: uid is a parameter that can fail validation.
print(schema["components"]["securitySchemes"])
# -> {'APIKeyHeader': {'type': 'apiKey', 'in': 'header', 'name': 'X-API-Key'}}
print(schema["components"]["schemas"]["Entry"]["properties"]["uid"])
# -> {'type': 'string', 'title': 'Uid', 'examples': ['blt_home_001']}

# ===== section: Concept 4: OpenAPI docs as a deliverable =====
# Why openapi.json is written with sort_keys and indent.
import json

# The same data, built in a different order (two developers, two machines).
a = {"title": "Acme", "version": "0.1.0"}
b = {"version": "0.1.0", "title": "Acme"}

print(a == b)  # -> True    equal as data
print(json.dumps(a) == json.dumps(b))  # -> False   different TEXT
# json.dumps keeps insertion order, so the files differ and git shows a
# change that is not a change. Readers stop trusting the diff.

stable_a = json.dumps(a, indent=2, sort_keys=True) + "\n"
stable_b = json.dumps(b, indent=2, sort_keys=True) + "\n"
print(stable_a == stable_b)  # -> True    same data, same bytes
print(stable_a, end="")
# -> {
# ->   "title": "Acme",
# ->   "version": "0.1.0"
# -> }
# REMEMBER: a generated file in git must be byte-for-byte reproducible.

# ===== section: Concept 5: The README and the 3-minute demo =====
# httpx.MockTransport: test a client against a fake server, offline.
import httpx

def fake_api(request: httpx.Request) -> httpx.Response:
    # This function plays the server: it gets the request, returns a reply.
    # Like msw (Mock Service Worker) in a React test.
    if request.headers.get("X-API-Key") != "acme_test_key":
        return httpx.Response(401, json={"detail": "invalid api key"})
    return httpx.Response(200, json={"uid": "blt_home_001"})

client = httpx.Client(base_url="http://acme.test",
                      transport=httpx.MockTransport(fake_api))

r1 = client.get("/v1/entries/blt_home_001")
print(r1.status_code, r1.json())  # -> 401 {'detail': 'invalid api key'}
r2 = client.get("/v1/entries/blt_home_001",
                headers={"X-API-Key": "acme_test_key"})
print(r2.status_code, r2.json()["uid"])  # -> 200 blt_home_001
print(r2.request.url)  # -> http://acme.test/v1/entries/blt_home_001
# FDE TIP: the real demo uses the same client code with a real base_url.
# Only the transport changes, so what you tested is what you present.

# ===== section: Check your understanding (predict first, then run) =====
# Six predictions. Write each answer down BEFORE you run the file.
import json
import logging
from contextvars import ContextVar

from fastapi import FastAPI
from fastapi.testclient import TestClient

rid: ContextVar[str] = ContextVar("rid", default="-")
token = rid.set("req-1")
rid.set("req-2")
rid.reset(token)
print("Q1", rid.get())

line = json.dumps({"path": "/v1/entries/a\nb"})
print("Q2", len(line.splitlines()))

logging.getLogger().setLevel(logging.WARNING)
log = logging.getLogger("content_sync_api.access")
print("Q3", log.isEnabledFor(logging.INFO), log.level)

app = FastAPI()
order: list[str] = []

@app.middleware("http")
async def first(request, call_next):
    order.append("first")
    return await call_next(request)

@app.middleware("http")
async def second(request, call_next):
    order.append("second")
    return await call_next(request)

@app.get("/x")
def x() -> dict:
    order.append("route")
    return {}

TestClient(app).get("/x")
print("Q4", order)

schema = app.openapi()
print("Q5", schema["info"])

try:
    log.warning("sync done", extra={"message": "override", "n": 3})
    print("Q6", "logged")
except KeyError as exc:
    print("Q6", "KeyError", exc)
