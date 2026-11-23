# Day 26 — Webhooks and API Keys: HMAC Signatures, Idempotency & Background Tasks (19 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): Acme's content sync service

Scenario: Acme Retail wants its AI shopping assistant to answer from content that is never more than a few seconds old. Their Contentstack will send publish, unpublish and delete webhooks to your service, signed in HMAC mode, and their search team will read the synced entries with API keys. Their security lead has three conditions before go-live: forged and replayed requests are rejected, retries never duplicate or roll back data, and keys can be rotated without downtime.

| File | Given | You write | Run while working |
|---|---|---|---|
| signatures.py | docstrings, examples | 3 functions | pytest -q -k sig |
| api_keys.py | api_key_header | 3 functions | pytest -q -k key |
| repository.py | get_entry() | event_key and 3 methods | pytest -q -k repo |
| sync_api.py | app, lifespan, health, read route | the webhook route body | pytest -q -k "webhook or read" |
| test_mine.py | 3 named stubs | 3 tests | pytest -q |

Also given, do not edit: settings.py, db.py, models.py, schema.sql, conftest.py, test_sync_api.py, send_webhook.py (a fake Contentstack that signs and sends a sample file) and two payloads in samples/. If your Day 24 db.py and Day 25 conftest.py are not finished, finish them before reading these two files.

- Step 0 (10 min). Do the Setup above. python3 -m pytest -q must show 46 failed, 1 passed, with no import errors. Read models.py and samples/publish_home.json side by side.
- Step 1: signatures.py (30 min). compute_signature, then parse_signature_header, then verify_signature. Rerun python3 -m pytest -q -k sig after each one; then python3 signatures.py must print the four expected lines.
- Step 2: api_keys.py (15 min). Three short functions. Then make your own local key: run python3 -c "import secrets; print('acme_' + secrets.token_urlsafe(24))", hash it with your hash_api_key, and put the hash (never the key) in ACME_API_KEY_HASHES in .env.
- Step 3: repository.py (30 min). event_key, then record_delivery, upsert_entry and delete_entry. Run your SQL by hand in psql on fde_test first if a test fails (Day 24 habit).
- Step 4: the route (30 min). Follow the seven numbered lines of the contract above receive_webhook. When it is done, the full given suite shows 44 passed.
- Step 5: test_mine.py (10 min). Three tests, from the hints. Then python3 -m pytest -q shows 47 passed.
- Step 6: the manual run (5 min). Start fastapi dev sync_api.py. In a second terminal run python3 send_webhook.py samples/publish_home.json twice, then once with --secret wrong, once with --age 3600, then samples/unpublish_home.json. Finish with a curl GET of /v1/entries/blt_home_001 with your key, before and after the unpublish. Paste the commands and outputs into day26/delivery_log.txt.
- Step 7. Run ruff check . and mypy signatures.py api_keys.py repository.py, then commit and push.
Acceptance criteria:

- python3 -m pytest -q inside day26/ shows 47 passed. Do not edit the given files.
- delivery_log.txt shows processed, duplicate, 401 for the wrong secret, 401 for the old timestamp, processed for the unpublish, and the GET returning 200 and then 404.
- The signature is verified on the raw body before any JSON parsing, and every comparison of secrets uses hmac.compare_digest.
- No secret, key or full key hash appears in code, logs, responses or git; .env is not committed.
- Duplicates and stale versions are decided by Postgres (ON CONFLICT and the WHERE guard), with no SELECT-then-INSERT, and nothing in repository.py calls commit().
- Committed and pushed with a message such as "Day 26: signed CMS webhook receiver with idempotent upserts and API keys" (a WIP push counts).
Hints, not answers:

- If every webhook test gets 401 "invalid signature" but the sig tests pass, the route is verifying something other than the raw bytes, or reading the wrong setting. Print the first 20 bytes of what you verify.
- If the duplicate test shows "processed" twice, record_delivery is not returning False on a conflict: check RETURNING and fetchone().
- If the stale test fails, run your upsert twice in psql with an older updated_at and look at the row count Postgres prints (UPDATE 0 or INSERT 0 1).
- If the 422 tests get 500, the ValidationError escaped: catch pydantic's ValidationError around model_validate_json.
- test_mine.py test 3 raises inside the test because the client fixture re-raises server errors (Day 25, Concept 1). That is what pytest.raises is for.
Stretch (only if the task and the push are done): add POST /v1/admin/replay/{event_key} protected by a separate admin key, which deletes one row from webhook_deliveries so that support can force a re-sync of one event. Write two tests for it, including one proving the normal read key gets 403, not 401.

Catch-up (1h): first push whatever exists of Days 22 to 25 (15 min). Then finish Day 25 until its 37 tests pass, because Day 27 packages Days 24 to 26 into one project.

## DSA practice (30 min)

Both problems are in day26/dsa.py with examples and hints; python3 dsa.py prints PASS or FAIL for each example. Give each 15 minutes before reading the hints.

- constant_time_equals: compare two strings without stopping at the first difference, the idea behind hmac.compare_digest. Hint: XOR the character codes and OR them into one accumulator.
- apply_events: replay a stream of webhook events into a final state, skipping repeated keys and versions older than the stored one, and applying deletes. This is your receiver's logic as a pure function. Hint: a set for seen keys, a dict for the state.
## Quiz (3 quick questions)

- Why does the route read await request.body() instead of declaring a Pydantic model parameter, and what would break if it verified json.dumps(payload.model_dump()) instead?
- Your dedupe table records deliveries in its own transaction, committed before the upsert. Describe the failure this allows and how one transaction prevents it.
- A teammate moves the database upsert into a background task "so the webhook answers faster". What can now go wrong, and what would you move into the background instead?
## When you're done

Paste into the Forward Deployment Engineer project chat as Day 26 review: signatures.py, repository.py, the route body, test_mine.py, the last lines of your pytest output, delivery_log.txt, your six predictions next to the real results, your quiz answers, dsa.py, and the link to your latest commit. Say whether Days 22 to 25 are pushed.

