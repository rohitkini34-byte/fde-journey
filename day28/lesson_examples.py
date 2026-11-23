"""Day 28 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Check your understanding (predict first, then run) =====
# Week 4 mixed review: predict every numbered print, then run the file.
# Run it inside your Day 23 project: uv run python review.py
import hashlib
import hmac
import json
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.testclient import TestClient  # in-process client, no server
from pydantic import BaseModel

app = FastAPI()
ENTRIES = {"home": {"uid": "home", "title": "Home", "secret": "x1"}}


class EntryOut(BaseModel):  # used as the return type (response model)
    uid: str
    title: str


class EntryPatch(BaseModel):  # PATCH body: every field optional
    title: str | None = None
    summary: str | None = None


# 1) route order: FastAPI tries routes in the order they were added
@app.get("/entries/{uid}")
def get_entry(uid: str) -> EntryOut:
    if uid not in ENTRIES:
        raise HTTPException(status_code=404, detail="entry not found")
    return EntryOut(**ENTRIES[uid])  # ENTRIES also holds a "secret" key


@app.get("/entries/search")  # registered after the {uid} route
def search() -> dict:
    return {"results": []}


# 3) query validation with Annotated + Query(ge=..., le=...)
@app.get("/entries")
def list_entries(limit: Annotated[int, Query(ge=1, le=50)] = 10) -> dict:
    return {"limit": limit}


# 4) PATCH: the client sends only "summary", and sends it as null
@app.patch("/entries/{uid}")
def patch_entry(uid: str, body: EntryPatch) -> dict:
    return {"changes": body.model_dump(exclude_unset=True)}


# 5) a dependency that tests can swap out
def get_tenant() -> str:
    return "acme-prod"


@app.get("/whoami")
def whoami(tenant: Annotated[str, Depends(get_tenant)]) -> dict:
    return {"tenant": tenant}


client = TestClient(app)

r = client.get("/entries/search")
print(1, r.status_code, r.json())

r = client.get("/entries/home")
print(2, r.json())

r = client.get("/entries", params={"limit": 0})
print(3, r.status_code, r.json()["detail"][0]["loc"])

r = client.patch("/entries/home", json={"summary": None})
print(4, r.json())

app.dependency_overrides[get_tenant] = lambda: "acme-test"
print(5, client.get("/whoami").json())
app.dependency_overrides.clear()  # FDE TIP: clear after every test
print(5, client.get("/whoami").json())

# 6) HMAC over the raw body vs over the body parsed and dumped again
secret = b"whsec_demo"
raw = b'{"uid": "home", "title": "Home"}'  # bytes exactly as sent
good = hmac.new(secret, raw, hashlib.sha256).hexdigest()
redumped = json.dumps(json.loads(raw), separators=(",", ":")).encode()
again = hmac.new(secret, redumped, hashlib.sha256).hexdigest()
print(6, hmac.compare_digest(good, again))
