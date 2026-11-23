"""Day 26 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Webhooks, the CMS calls you =====
# A webhook is just a POST that the CMS sends to YOUR URL.
import json
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

app = FastAPI()
received: list[bytes] = []  # stands in for "what reached our server"


@app.post("/webhooks/cms")
async def receive(request: Request) -> dict:
    # await request.body(): the RAW bytes exactly as they arrived.
    # Like reading req.body in Express BEFORE express.json() parses it.
    raw = await request.body()
    received.append(raw)
    payload = json.loads(raw)  # bytes -> dict, like JSON.parse()
    return {"status": "received", "event": payload["event"]}


client = TestClient(app)
event = {"event": "content_types.entries.publish",
         "event_data": {"entry": {"uid": "blt1", "title": "Home"}}}

# The CMS serialises the dict to bytes and POSTs them.
resp = client.post("/webhooks/cms", content=json.dumps(event),
                   headers={"Content-Type": "application/json"})
print(resp.status_code, resp.json())
# -> 200 {'status': 'received', 'event': 'content_types.entries.publish'}

# The SAME data, serialised another way, is DIFFERENT bytes.
compact = json.dumps(event, separators=(",", ":"))
print(len(json.dumps(event)), len(compact))  # -> 101 94
print(json.loads(compact) == event)  # -> True   same data...
print(compact.encode() == received[0])  # -> False  ...different bytes
# GOTCHA: a signature is computed over BYTES. Re-serialising the parsed
# dict gives other bytes, so always verify the raw body (Concept 2).

# ===== section: Concept 1: Webhooks, the CMS calls you =====
# Why the same event arrives twice: the sender retries until it sees a 2xx.
import time


def flaky_receiver(attempt: int, seen: list[str], event_id: str) -> int:
    seen.append(event_id)  # the work was DONE on every attempt...
    if attempt == 1:
        time.sleep(0.02)  # ...but attempt 1 was too slow to answer
        return 504  # the sender gave up waiting (a timeout)
    return 200


def cms_send(event_id: str, seen: list[str], max_tries: int = 3) -> None:
    # Roughly what Contentstack does: POST, and on a non-2xx or a timeout,
    # wait and try again (the retry count and delay are configurable).
    for attempt in range(1, max_tries + 1):
        status = flaky_receiver(attempt, seen, event_id)
        print(f"attempt {attempt}: {status}")
        if 200 <= status < 300:  # only a 2xx counts as "delivered"
            return


seen: list[str] = []
cms_send("publish:blt1:v7", seen)
# -> attempt 1: 504
# -> attempt 2: 200
print(seen)
# -> ['publish:blt1:v7', 'publish:blt1:v7']
# The receiver processed ONE event TWICE. That is "at-least-once" delivery.
# REMEMBER: webhooks arrive at least once, maybe late, maybe out of order.

# ===== section: Concept 2: HMAC signatures, proving who sent it =====
# HMAC: prove that a body came from someone who knows the shared secret.
import hashlib
import hmac

SECRET = "whsec_demo_only"  # FDE TIP: in real code this comes from settings
body = b'{"event":"content_types.entries.publish","uid":"blt1"}'

# 1. A plain hash is NOT a signature: anyone can compute it.
print(hashlib.sha256(body).hexdigest()[:16])  # -> 70d33a20ccca93b0

# 2. HMAC mixes the secret into the hash. Without the secret, nobody can
#    produce the right value. Like crypto.createHmac('sha256', key) in Node.
def compute_signature(secret: str, timestamp: int, body: bytes) -> str:
    # Contentstack's HMAC mode signs "<timestamp>.<raw body>".
    signed = f"{timestamp}.".encode() + body  # bytes + bytes
    return hmac.new(secret.encode(), signed, hashlib.sha256).hexdigest()

t = 1795054500  # a Unix timestamp: seconds since 1 Jan 1970 (UTC)
sig = compute_signature(SECRET, t, body)
header = f"t={t},v1={sig}"  # the shape of x-contentstack-hmac-signature
print(header[:28] + "...")  # -> t=1795054500,v1=bf884d4c9e40...

# 3. The receiver recomputes and compares in CONSTANT time.
def verify(secret: str, header: str, body: bytes, now: int,
           tolerance_s: int = 300) -> bool:
    parts = dict(p.split("=", 1) for p in header.split(","))
    ts = int(parts["t"])
    if abs(now - ts) > tolerance_s:  # too old (or from the future)
        return False
    expected = compute_signature(secret, ts, body)
    # GOTCHA: never use == here. compare_digest takes the same time
    # whether the first or the last character differs, so an attacker
    # cannot guess the signature one character at a time.
    return hmac.compare_digest(expected, parts["v1"])

print(verify(SECRET, header, body, now=t + 10))  # -> True
print(verify(SECRET, header, body + b" ", now=t + 10))
# -> False   one extra space changed the bytes
print(verify("wrong-secret", header, body, now=t + 10))  # -> False
print(verify(SECRET, header, body, now=t + 3600))
# -> False   a replay: a real request captured an hour ago
# REMEMBER: sign the raw bytes, check the timestamp, compare_digest.

# ===== section: Concept 2: HMAC signatures, proving who sent it =====
# Key rotation: during a switch, the header carries one v1 per secret.
import hashlib
import hmac

def sign(secret: str, t: int, body: bytes) -> str:
    return hmac.new(secret.encode(), f"{t}.".encode() + body,
                    hashlib.sha256).hexdigest()

body, t = b'{"uid":"blt1"}', 1795054500
# While Contentstack rotates the org key, BOTH keys sign the payload.
header = f"t={t},v1={sign('new-key', t, body)},v1={sign('old-key', t, body)}"

# GOTCHA: dict(...) keeps only the LAST v1. Collect every v1 into a list.
pairs = [part.split("=", 1) for part in header.split(",")]
print(len(dict(pairs)))  # -> 2   keys 't' and 'v1': one signature was lost
v1s = [value for key, value in pairs if key == "v1"]
print(len(v1s))  # -> 2

# Our service still has only the OLD secret configured: accept any match.
expected = sign("old-key", t, body)
print(any(hmac.compare_digest(expected, v) for v in v1s))  # -> True
# FDE TIP: this is what lets the customer rotate a secret with zero downtime.

# ===== section: Concept 3: Idempotency, the same event twice is safe =====
# Idempotency: process each event once, and never let an old one win.
import psycopg

URL = "postgresql:///fde_test"  # the TEST database (Day 25), never fde

with psycopg.connect(URL, autocommit=True) as conn:
    conn.execute("SET client_min_messages = warning")  # hide NOTICEs
    conn.execute("DROP TABLE IF EXISTS demo_deliveries, demo_entries")
    # One row per event we have already handled. The PRIMARY KEY is the
    # whole trick: Postgres itself refuses a second row with the same key.
    conn.execute("CREATE TABLE demo_deliveries (event_key text PRIMARY KEY)")
    conn.execute("""CREATE TABLE demo_entries (
        uid text PRIMARY KEY, title text NOT NULL,
        updated_at timestamptz NOT NULL)""")

    def first_time(key: str) -> bool:
        # ON CONFLICT DO NOTHING: a duplicate is not an error, it is a no-op.
        # RETURNING gives a row only when the INSERT really happened.
        row = conn.execute(
            "INSERT INTO demo_deliveries VALUES (%s)"
            " ON CONFLICT DO NOTHING RETURNING event_key", (key,),
        ).fetchone()
        return row is not None  # None means "seen before"

    print(first_time("publish:blt1:08:00"))  # -> True   new: do the work
    print(first_time("publish:blt1:08:00"))  # -> False  a retry: skip it

    def upsert(uid: str, title: str, updated_at: str) -> int:
        # Day 19's upsert, plus a WHERE on the UPDATE part: only overwrite
        # when the incoming version is NEWER than the stored one.
        cur = conn.execute(
            """INSERT INTO demo_entries VALUES (%s, %s, %s)
               ON CONFLICT (uid) DO UPDATE
               SET title = EXCLUDED.title, updated_at = EXCLUDED.updated_at
               WHERE demo_entries.updated_at < EXCLUDED.updated_at""",
            (uid, title, updated_at),
        )
        return cur.rowcount  # 1 = written, 0 = skipped as stale

    # Deliveries arrive OUT OF ORDER: version 2 first, then version 1.
    print(upsert("blt1", "Home v2", "2026-11-19 08:05+00"))  # -> 1
    print(upsert("blt1", "Home v1", "2026-11-19 08:00+00"))  # -> 0
    print(conn.execute("SELECT title FROM demo_entries").fetchone())
    # -> ('Home v2',)   the late, older event did not overwrite the newer one
    # EXCLUDED is the row you TRIED to insert (Day 19).
# REMEMBER: dedupe by a key, and compare versions before you overwrite.

# ===== section: Concept 3: Idempotency, the same event twice is safe =====
# Record the delivery and apply it in ONE transaction, or a crash loses data.
import psycopg

URL = "postgresql:///fde_test"

with psycopg.connect(URL) as conn:  # not autocommit: we control commits
    conn.execute("TRUNCATE demo_deliveries, demo_entries")
    conn.commit()

    def handle(key: str, title: str, crash: bool) -> None:
        try:
            with conn.transaction():  # BEGIN ... COMMIT, or ROLLBACK on error
                conn.execute("INSERT INTO demo_deliveries VALUES (%s)"
                             " ON CONFLICT DO NOTHING", (key,))
                if crash:
                    raise RuntimeError("pod killed mid-request")
                conn.execute("INSERT INTO demo_entries VALUES"
                             " ('blt9', %s, now())", (title,))
            print("committed")
        except RuntimeError as exc:
            print("rolled back:", exc)

    handle("publish:blt9:v1", "Pricing", crash=True)
    # -> rolled back: pod killed mid-request
    seen = conn.execute("SELECT count(*) FROM demo_deliveries").fetchone()
    print(seen)  # -> (0,)   the delivery record was rolled back too...
    handle("publish:blt9:v1", "Pricing", crash=False)  # ...so the retry works
    # -> committed
    print(conn.execute("SELECT title FROM demo_entries").fetchone())
    # -> ('Pricing',)
    # GOTCHA: with two separate commits, the delivery would be marked "seen"
    # but the entry never written, and every retry would be skipped forever.

# ===== section: Concept 4: API keys, who is calling your API =====
# API keys: generate, store only a hash, check a header in a dependency.
import hashlib
import hmac
import secrets
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Security
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient

# 1. Generate: secrets, not random. random is predictable; secrets is not.
key = "acme_" + secrets.token_urlsafe(24)  # like crypto.randomBytes in Node
print(key[:5], len(key))  # -> acme_ 37

# 2. Store only the SHA-256 hash, as you would a password digest. A leaked
#    database or .env then does not leak a usable key.
def hash_api_key(key: str) -> str:
    return hashlib.sha256(key.encode()).hexdigest()

DEMO_KEY = "acme_demo_key_123"
STORED = [hash_api_key(DEMO_KEY)]  # FDE TIP: in real code, from settings

# 3. APIKeyHeader reads X-API-Key and shows a padlock in /docs.
#    auto_error=False: return None when it is missing, so WE choose the error.
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(
    key: Annotated[str | None, Security(api_key_header)],
) -> str:
    if key is not None:
        digest = hash_api_key(key)
        for stored in STORED:  # several hashes = rotation with no downtime
            if hmac.compare_digest(digest, stored):
                return stored[:8]  # a short key id that is safe to log
    # 401 = "who are you?" (no or bad credentials).
    # 403 = "I know you, but you may not do this" (Week 10, roles).
    raise HTTPException(status_code=401, detail="invalid or missing API key",
                        headers={"WWW-Authenticate": "APIKey"})

app = FastAPI()

@app.get("/v1/entries/{uid}")
def get_entry(uid: str,
              key_id: Annotated[str, Depends(require_api_key)]) -> dict:
    return {"uid": uid, "key_id": key_id}

client = TestClient(app)
print(client.get("/v1/entries/blt1").status_code)  # -> 401
bad = client.get("/v1/entries/blt1", headers={"X-API-Key": "guess"})
print(bad.status_code, bad.json())
# -> 401 {'detail': 'invalid or missing API key'}
ok = client.get("/v1/entries/blt1", headers={"x-api-key": DEMO_KEY})
print(ok.status_code, ok.json() == {"uid": "blt1", "key_id": STORED[0][:8]})
# -> 200 True   header names are case-insensitive in HTTP
# GOTCHA: never put the key in the URL (?api_key=...). URLs end up in logs,
# browser history and proxies. Headers are the place for credentials.

# ===== section: Concept 5: Background tasks, answer fast and finish later =====
# BackgroundTasks: answer the CMS fast, do the slow follow-up afterwards.
import time

from fastapi import BackgroundTasks, FastAPI
from fastapi.testclient import TestClient

app = FastAPI()
events: list[str] = []  # an ordered log of what happened


def reindex_search(uid: str) -> None:
    # Stands in for slow work: refresh a search index, purge a CDN cache.
    time.sleep(0.2)
    events.append(f"reindexed {uid}")


def broken_task(uid: str) -> None:
    raise ValueError(f"search service down for {uid}")


@app.post("/webhooks/cms")
def receive(background_tasks: BackgroundTasks) -> dict:
    # FastAPI injects BackgroundTasks for you, like Request.
    events.append("saved to db")  # the important part, done NOW
    # add_task(function, *args): run it AFTER the response is sent.
    background_tasks.add_task(reindex_search, "blt1")
    events.append("response built")
    return {"status": "processed"}


@app.post("/webhooks/broken")
def receive_broken(background_tasks: BackgroundTasks) -> dict:
    background_tasks.add_task(broken_task, "blt2")
    return {"status": "processed"}


client = TestClient(app)
start = time.perf_counter()
resp = client.post("/webhooks/cms")
print(resp.json(), events)
# -> {'status': 'processed'} ['saved to db', 'response built',
#    'reindexed blt1']
# GOTCHA: TestClient waits for background tasks before it returns, so the
# test sees 'reindexed' already. A real client gets the response FIRST.
print(round(time.perf_counter() - start, 1))  # -> 0.2   (TestClient waited)

safe = TestClient(app, raise_server_exceptions=False)
print(safe.post("/webhooks/broken").status_code)
# -> 200   the response was already sent when the task failed
# The CMS thinks all is well and will NOT retry. A background task has no
# retry and is lost if the process dies: fine for a cache purge, not for
# the database write. REMEMBER: write first, then hand off the extras.

# ===== section: Check your understanding (predict first, then run) =====
# Six predictions. Write each answer down BEFORE you run the file.
import hashlib
import hmac
import json
from typing import Annotated

from fastapi import BackgroundTasks, FastAPI, Security
from fastapi.security import APIKeyHeader
from fastapi.testclient import TestClient

def sig(secret: bytes, body: bytes) -> str:
    return hmac.new(secret, body, hashlib.sha256).hexdigest()

a = json.dumps({"uid": "blt1", "v": 2}).encode()
b = json.dumps({"v": 2, "uid": "blt1"}).encode()
print("Q1", json.loads(a) == json.loads(b), sig(b"k", a) == sig(b"k", b))
print("Q2", len(sig(b"k", a)), len(sig(b"a much longer secret", a)))
print("Q3", hashlib.sha256(a).hexdigest() == sig(b"", a))

app = FastAPI()
log: list[str] = []

@app.get("/strict")
def strict(k: Annotated[str, Security(APIKeyHeader(name="X-API-Key"))]):
    return {"k": k}

@app.post("/hook")
def hook(tasks: BackgroundTasks) -> dict:
    tasks.add_task(log.append, "task")
    log.append("route")
    return {"log": list(log)}

client = TestClient(app)
print("Q4", client.get("/strict").status_code)
print("Q5", client.post("/hook").json(), log)
pairs = [p.split("=", 1) for p in "t=1,v1=aa,v1=bb".split(",")]
print("Q6", dict(pairs))
