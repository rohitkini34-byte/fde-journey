# Day 27 — Phase 1 Milestone: content-sync-api with uv, Logging, OpenAPI Docs, a README & a Demo (20 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): ship content-sync-api

Scenario: Acme Retail's platform team takes over your sync service next week. Their handover checklist says: one installable project with a lock file, JSON logs with request ids and no secrets, OpenAPI docs that match the code, a README their engineers can follow without calling you, and a demo they can rerun after every deploy. Their VP wants to see the demo on Monday.

| File (in src/content_sync_api/ unless noted) | Given | You write | Run while working |
|---|---|---|---|
| logging_setup.py | request_id_var, SENSITIVE_KEYS | redact, JsonFormatter.format, configure_logging | uv run pytest -q -k logging |
| request_logging.py | header name, logger | choose_request_id, add_request_logging | uv run pytest -q -k request |
| openapi_docs.py | title, description, tags, main() | render_openapi, export_openapi, openapi_is_current | uv run pytest -q -k openapi |
| demo.py | DemoConfig, StepResult, main() | signed_headers, check, run_demo | uv run pytest -q -k demo |
| main.py (your Day 26 sync_api.py) | nothing new | absolute imports, metadata, tags, logging wiring | uv run pytest -q |
| tests/test_openapi_current.py | a stub | one test | uv run pytest -q |
| README.md, docs/demo_script.md | headings and TODO notes | every section | follow it from a fresh clone |

Also given, do not edit: __init__.py (the version), py.typed, the four tests/test_*.py files with 39 cases, .gitignore and .env.example.

- Step 0 (5 min). git pull in fde-journey, then open day27/content-sync-api/ in VS Code. Read the four given test files once, quickly: they are the specification.
- Step 1: the package (20 min). Inside day27/content-sync-api/ run the Concept 1 commands (uv init ..., uv add ..., uv add --dev ...). In pyproject.toml, set a real one-line description, and replace the generated [project.scripts] entry with two lines: content-sync-demo = "content_sync_api.demo:main" and content-sync-openapi = "content_sync_api.openapi_docs:main". Then uv sync and uv run pytest -q must show 39 failed, 1 passed with no import errors.
- Step 2: move Day 26 in (15 min). Copy settings.py, db.py, models.py, repository.py, signatures.py and api_keys.py into src/content_sync_api/; copy sync_api.py there as main.py; schema.sql into sql/; the two sample payloads into samples/; conftest.py, test_sync_api.py and test_mine.py into tests/. Change every flat import to an absolute one. uv run pytest -q tests/test_sync_api.py tests/test_mine.py shows the same 47 passed as on Day 26.
- Step 3: logging (30 min). logging_setup.py, then request_logging.py. uv run pytest -q -k "logging or request" shows 26 passed.
- Step 4: wire it in (25 min). In settings.py add log_level: str = "INFO" and json_logs: bool = True. In main.py: call configure_logging(...) first thing in the lifespan; build the app with FastAPI(title=API_TITLE, version=__version__, description=API_DESCRIPTION, openapi_tags=TAGS_METADATA, lifespan=...); call add_request_logging(app); give every route tags, a summary and its error responses; and in the webhook route write one logger.info("webhook", extra={"fields": {...}}) with the event, the uid and the result (processed, duplicate or ignored). Start uv run fastapi dev src/content_sync_api/main.py and open /docs.
- Step 5: docs (15 min). openapi_docs.py, then uv run content-sync-openapi writes docs/openapi.json. Write tests/test_openapi_current.py. Prove it works: add a dummy route, see the test fail with your message, remove the route.
- Step 6: the demo client (15 min). demo.py until uv run pytest -q -k demo shows 7 passed. Then, with the server running and the tables reset, fill .env from .env.example and run uv run --env-file .env content-sync-demo: 8/8 steps passed, and echo $? prints 0.
- Step 7: README, talk track, recording (30 min). Fill every section of README.md and docs/demo_script.md. Follow your own quick start in a fresh clone of the repo. Rehearse twice, record, and paste the link in both files.
- Step 8. uv run ruff check ., uv run mypy src, the full uv run pytest -q, then commit (including uv.lock and docs/openapi.json) and push.
Acceptance criteria:

- uv run pytest -q inside day27/content-sync-api/ shows 87 passed. The given test files are unchanged.
- uv run ruff check . and uv run mypy src report no errors.
- With the server running, uv run content-sync-demo prints 8 PASS lines and "8/8 steps passed" and exits with code 0; break one thing on purpose (a wrong key in .env) and it exits with 1.
- Every request writes exactly one JSON access line with a request id, the response has an X-Request-ID header, and searching the server output for your raw API key, your webhook secret and hmac-signature values finds nothing.
- /docs shows the title, the version from pyproject.toml, the three tag sections with descriptions, a summary on every route, the 401 and 404 responses and the padlock. docs/openapi.json is committed and the current-docs test passes.
- Every README section is filled, the quick start works from a fresh clone, and the README and docs/demo_script.md link a recording of 3 minutes 30 or less.
- Committed and pushed with uv.lock, without .venv/ or .env, with a message such as "Day 27: content-sync-api package, JSON logs, OpenAPI docs, README and demo".
Hints, not answers:

- If uv run pytest cannot import content_sync_api, you probably ran uv init one folder too high or forgot --package. pyproject.toml must sit next to src/, and uv sync must list content-sync-api as installed.
- If your Day 26 tests fail with ModuleNotFoundError: No module named 'settings', one flat import is left, often in conftest.py. Search the whole project for ^from (settings|db|models|repository|signatures|api_keys)  with VS Code's regex search.
- If every log line appears twice, configure_logging adds a second handler. Mark the handler you create and remove only marked ones (HINT 2 in the file).
- If the route cannot see the request id, check the order: request_id_var.set() must run before await call_next(request).
- If the current-docs test fails right after you exported, you exported from a different app object or the file was written with different formatting. Both sides must go through render_openapi.
- If demo step 2 says "duplicate" instead of "processed", the event is already in your dedupe table from an earlier run. Empty the Day 26 tables before a demo, and write that command in the README's Demo section.
Stretch (only if everything above is pushed): add a GitHub Actions workflow in the repo's .github/workflows/ that runs uv sync --frozen, ruff, mypy and the 39 database-free tests on every push. A green badge in the README is the first thing a reviewer sees.

Catch-up (0.5h): if Day 26's 47 tests are not green yet, use this time there first. If they are, push Days 22 to 26 as they are, so the milestone has its history behind it.

## DSA practice (30 min)

Both problems are in day27/dsa.py with examples and hints; python3 dsa.py prints PASS or FAIL for each example. Give each 15 minutes before reading the hints.

- percentile: the nearest-rank p-th percentile of a list of durations, the number behind "our p95 is 120 ms". Hint: sort a copy, then the rank ceil(p / 100 * n) is 1-based.
- top_k_slowest: read JSON log lines like today's, skip the ones that are not access lines, and return the k paths with the highest average duration, ties alphabetical. Hint: a dict of path to total and count, then sort with a tuple key.
## Quiz (3 quick questions)

- A teammate adds logger.info(f"webhook from {dict(request.headers)}") to the webhook route. Name two separate problems with this line.
- Why do you commit uv.lock but not .venv/, and what does uv sync --frozen --no-dev do in a customer's Dockerfile?
- A customer asks: "how do we know your API docs match what is deployed?" Give the three-part answer this project supports.
## When you're done

Paste into the Forward Deployment Engineer project chat as Day 27 review: the last lines of uv run pytest -q, the output of uv run content-sync-demo, two of your JSON log lines, your README, the recording link, your six predictions next to the real results, your quiz answers, dsa.py, and the link to your latest commit. Say which of Days 22 to 26 are pushed.

