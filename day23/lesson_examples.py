"""Day 23 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: What FastAPI is, and your first app =====
# Your first FastAPI app: one file, two routes.
from fastapi import FastAPI  # the framework; like `import express` in Node

# One app object per service, like `const app = express()`.
app = FastAPI(title="Acme Content API", version="0.1.0")


# A decorator (Day 11) registers the function below as the handler
# for GET /health. Like app.get("/health", handler) in Express.
@app.get("/health")
def health() -> dict[str, str]:
    # Return a plain dict; FastAPI turns it into a JSON response.
    return {"status": "ok"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "Acme Content API. See /docs"}

# ===== section: Concept 2: Path and query parameters =====
# Path and query parameters: FastAPI reads them from the type hints.
from typing import Annotated, Literal

from fastapi import FastAPI, Query
from fastapi.testclient import TestClient  # calls the app without a server

app = FastAPI()


# {entry_id} in the path becomes the function argument of the same name.
# The hint `int` makes FastAPI convert "7" -> 7, or reply 422 if it can't.
@app.get("/v1/items/{entry_id}")
def get_item(entry_id: int) -> dict:
    return {"entry_id": entry_id, "type": type(entry_id).__name__}


# Arguments NOT in the path are query parameters (?status=...&limit=...).
# A default value makes them optional. Literal limits the allowed values.
@app.get("/v1/items")
def list_items(
    status: Literal["draft", "published"] | None = None,
    # Annotated[type, rules]: type first, then extra validation rules.
    limit: Annotated[int, Query(ge=1, le=50)] = 3,
    tag: Annotated[list[str] | None, Query()] = None,  # ?tag=a&tag=b
) -> dict:
    return {"status": status, "limit": limit, "tag": tag}


client = TestClient(app)  # like supertest(app) in Node
print(client.get("/v1/items/7").json())
# -> {'entry_id': 7, 'type': 'int'}   "7" in the URL arrived as an int
print(client.get("/v1/items/seven").status_code)
# -> 422   not a whole number, so FastAPI rejects it before your code runs
print(client.get("/v1/items").json())
# -> {'status': None, 'limit': 3, 'tag': None}   all defaults
print(client.get("/v1/items?status=published&limit=10").json())
# -> {'status': 'published', 'limit': 10, 'tag': None}
print(client.get("/v1/items?tag=sale&tag=diwali").json()["tag"])
# -> ['sale', 'diwali']   repeated keys collect into a list
r = client.get("/v1/items?limit=500")
print(r.status_code, r.json()["detail"][0]["msg"])
# -> 422 Input should be less than or equal to 50

# ===== section: Concept 3: Pydantic models, the contract in code =====
# Pydantic models on their own: validation, conversion, errors, dumping.
from typing import Literal

from pydantic import BaseModel, Field, ValidationError


# A model is a class with typed fields, like a TypeScript interface that
# is also CHECKED at runtime. Think: a Contentstack content type schema.
class EntryCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    content_type: Literal["blog_post", "product_page", "landing_page"]
    tags: list[str] = []  # safe here: Pydantic copies defaults per object
    views: int = 0


# Good data in: you get an object with attributes, not a dict.
e = EntryCreate(title="Navratri lookbook", slug="navratri-lookbook",
                content_type="blog_post", views="12")
print(e.views, type(e.views).__name__)
# -> 12 int   "12" was converted: lax mode accepts numeric strings

# model_dump() -> plain dict (for JSON or a DB row), like a spread {...e}
print(e.model_dump())
# -> {'title': 'Navratri lookbook', 'slug': 'navratri-lookbook',
#     'content_type': 'blog_post', 'tags': [], 'views': 12}

# Bad data in: ONE exception that lists EVERY problem, not just the first.
try:
    EntryCreate(title="", slug="Bad Slug", content_type="faq")
except ValidationError as exc:
    for err in exc.errors():
        print(err["loc"], err["type"])
# -> ('title',) string_too_short
# -> ('slug',) string_pattern_mismatch
# -> ('content_type',) literal_error

# ===== section: Concept 4: Request bodies, response models and status codes =====
# Create and read with a body model, a response model and real status codes.
from datetime import UTC, datetime
from typing import Literal

from fastapi import FastAPI, HTTPException, Response, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

ContentType = Literal["blog_post", "product_page", "landing_page"]


class EntryCreate(BaseModel):
    """What the CLIENT sends. No uid or timestamps: the server owns those."""
    title: str = Field(min_length=1, max_length=120)
    slug: str = Field(pattern=r"^[a-z0-9]+(-[a-z0-9]+)*$")
    content_type: ContentType


class EntryOut(EntryCreate):
    """What the SERVER returns: the input fields plus server-owned ones."""
    uid: str
    status: Literal["draft", "published"]
    created_at: datetime


app = FastAPI()
# An in-memory "database": uid -> dict. It resets on every restart.
# GOTCHA: fine for today; Day 24 swaps it for Postgres.
ENTRIES: dict[str, dict] = {}


@app.post("/v1/entries", status_code=status.HTTP_201_CREATED)
def create_entry(body: EntryCreate, response: Response) -> EntryOut:
    # A parameter typed with a BaseModel is read from the JSON body.
    if any(e["slug"] == body.slug for e in ENTRIES.values()):
        # raise, not return: FastAPI turns this into a 409 JSON response
        raise HTTPException(status_code=409,
                            detail=f"slug '{body.slug}' already exists")
    uid = f"blt{len(ENTRIES) + 1:03d}"  # blt001, blt002 ... (demo only)
    row = {**body.model_dump(), "uid": uid, "status": "draft",
           "created_at": datetime.now(UTC)}
    ENTRIES[uid] = row
    # Day 22: a 201 should say where the new resource lives.
    response.headers["Location"] = f"/v1/entries/{uid}"
    return EntryOut(**row)


# The return type doubles as the response model: FastAPI validates the
# output and FILTERS it to EntryOut's fields before sending.
@app.get("/v1/entries/{uid}")
def get_entry(uid: str) -> EntryOut:
    row = ENTRIES.get(uid)  # .get() returns None instead of KeyError
    if row is None:
        raise HTTPException(status_code=404, detail=f"entry {uid} not found")
    return EntryOut(**row)


client = TestClient(app)
new = {"title": "Diwali gift guide", "slug": "diwali-gift-guide",
       "content_type": "blog_post"}
r = client.post("/v1/entries", json=new)  # json= sets Content-Type for us
print(r.status_code, r.headers["location"])
# -> 201 /v1/entries/blt001
print(r.json()["status"], r.json()["created_at"][:4])
# -> draft 2026   datetime became an ISO 8601 string in the JSON
print(client.post("/v1/entries", json=new).json())
# -> {'detail': "slug 'diwali-gift-guide' already exists"}  (status 409)
print(client.get("/v1/entries/blt999").status_code)
# -> 404

# ===== section: Concept 5: Updates, deletes and validation errors =====
# PATCH with exclude_unset, DELETE with 204, and the 422 error shape.
from fastapi import FastAPI, HTTPException, status
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field


class EntryUpdate(BaseModel):
    """PATCH body: every field optional, because the client sends only
    what changes (Day 22: PATCH = change only the fields I send)."""
    title: str | None = Field(default=None, min_length=1, max_length=120)
    tags: list[str] | None = None


class EntryOut(BaseModel):
    uid: str
    title: str
    tags: list[str]


app = FastAPI()
ENTRIES = {"blt001": {"uid": "blt001", "title": "Old title",
                      "tags": ["sale"], "internal_note": "do not leak"}}


@app.patch("/v1/entries/{uid}")
def update_entry(uid: str, body: EntryUpdate) -> EntryOut:
    if uid not in ENTRIES:
        raise HTTPException(status_code=404, detail=f"entry {uid} not found")
    # exclude_unset=True keeps ONLY the keys the client actually sent.
    changes = body.model_dump(exclude_unset=True)
    print("changes:", changes)
    ENTRIES[uid].update(changes)  # dict.update merges, like {...a, ...b}
    # The row still holds internal_note; returning it as EntryOut drops it.
    return EntryOut(**ENTRIES[uid])


# 204 No Content: success with an empty body (Day 22).
@app.delete("/v1/entries/{uid}", status_code=status.HTTP_204_NO_CONTENT)
def delete_entry(uid: str) -> None:
    if ENTRIES.pop(uid, None) is None:  # pop with a default never raises
        raise HTTPException(status_code=404, detail=f"entry {uid} not found")


client = TestClient(app)
r = client.patch("/v1/entries/blt001", json={"title": "New title"})
# -> changes: {'title': 'New title'}   tags was not sent, so not touched
print(r.json())
# -> {'uid': 'blt001', 'title': 'New title', 'tags': ['sale']}
#    no internal_note: the response model filtered it out

bad = client.patch("/v1/entries/blt001", json={"title": ""})
print(bad.status_code)  # -> 422
err = bad.json()["detail"][0]  # FastAPI's validation error shape
print(err["loc"], err["msg"])
# -> ['body', 'title'] String should have at least 1 character

r = client.delete("/v1/entries/blt001")
print(r.status_code, repr(r.text))  # -> 204 ''
print(client.delete("/v1/entries/blt001").status_code)
# -> 404   DELETE is idempotent: the entry stays gone, the code differs

# ===== section: Check your understanding (predict first, then run) =====
# Six predictions. Write each answer down BEFORE you run the file.
from typing import Annotated

from fastapi import FastAPI, HTTPException, Query
from fastapi.testclient import TestClient
from pydantic import BaseModel


class Entry(BaseModel):
    title: str
    views: int = 0


app = FastAPI()


@app.get("/v1/entries/{uid}")
def get_entry(uid: str) -> dict:
    raise HTTPException(status_code=404, detail=f"entry {uid} not found")


@app.get("/v1/entries/latest")  # declared AFTER the {uid} route
def latest() -> dict:
    return {"uid": "blt042"}


@app.get("/v1/count")
def count(limit: Annotated[int, Query(ge=1)] = 10) -> dict:
    return {"limit": limit}


@app.post("/v1/entries")
def create(entry: Entry) -> Entry:
    return entry


c = TestClient(app)
print("Q1", c.get("/v1/entries/latest").json())
print("Q2", c.get("/v1/count?limit=0").status_code)
print("Q3", c.get("/v1/count?limit=5").json())
r4 = c.post("/v1/entries", json={"views": 3})
print("Q4", r4.json()["detail"][0]["loc"])
print("Q5", c.post("/v1/entries", json={"title": "Hi", "views": "7"}).json())
print("Q6", c.post("/v1/entries", content="title=Hi").status_code)
