# Day 23 — FastAPI First Steps: Routes, Path and Query Parameters, Pydantic Models, Validation Errors & /docs (16 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day23/content_api.py and smoke.sh

Scenario: Acme Retail's partner agency is ready to build against the design you wrote yesterday. Your job today is the entries part of it as a running service. Data lives in a Python dict for now; tomorrow the same URLs are backed by Postgres.

Part A (90 min): open day23/content_api.py. The models EntryOut and EntryPage, the store, reset_store(), new_uid() and /health are given. You write the two input models (EntryCreate, EntryUpdate) and seven functions: find_or_404, create_entry, list_entries, get_entry, update_entry, delete_entry and publish_entry. Each has a comment block with the exact rules and an example, plus step-by-step hints. Work one route at a time and rerun the tests after each: python3 -m pytest -q -k create runs only the tests whose name contains "create".

| Method and path | Success | Errors |
|---|---|---|
| POST /v1/entries | 201 + Location | 409 duplicate slug, 422 |
| GET /v1/entries | 200 {items, next_cursor} | 422 bad limit or status |
| GET /v1/entries/{uid} | 200 | 404 |
| PATCH /v1/entries/{uid} | 200, version + 1 | 404, 422 (also for null) |
| DELETE /v1/entries/{uid} | 204, empty body | 404 |
| POST /v1/entries/{uid}/publish | 200, version + 1 | 404, 409 already published |

Part B (30 min): start the server with fastapi dev content_api.py, open /docs and run every route once with "Try it out". Then fill in day23/smoke.sh: nine steps, each with the output it must print; write one curl command under each TODO, using Day 22's flags.

Acceptance criteria:

- python3 -m pytest -q inside day23/ shows 26 passed. Do not edit test_content_api.py.
- /docs lists all seven routes with their models, and you have run each one once with "Try it out".
- bash smoke.sh, against a freshly started dev server, prints every step's expected output from top to bottom.
- No input you can think of produces a 500: bad input is 422, an unknown uid is 404, a clash with the current state is 409.
- EntryCreate has no uid, status, version or timestamp fields: the server owns them.
- ruff check . and mypy content_api.py are clean (Day 12).
- Committed and pushed with a message such as "Day 23: in-memory content API with FastAPI" (a WIP push counts).
Hints, not answers:

- Write the models first and run the tests: the six test_create_invalid_field_is_422 cases should pass before you write any route, because validation happens before your function runs.
- When a test fails, read the assertion line and the response FastAPI printed. Add print(r.json()) in the test temporarily if you need the full body, and remove it afterwards.
- If a route returns 500 in the tests, the traceback in the pytest output points at the exact line; a common cause is returning a row dict that is missing a field EntryOut needs.
- For list_entries, build the filtered list first, then slice it. next_cursor is the uid of the last item on the page, but only when more items exist after it.
- For update_entry, the null check must run before you change the row; otherwise the 422 leaves the entry half updated.
Stretch (only if Part A, Part B and the catch-up item are pushed): add GET /v1/entries/by-slug/{slug} and make sure it is declared so that it cannot be swallowed by /v1/entries/{uid}. Add two tests of your own for it in a new file test_mine.py.

Catch-up (1h): if day22/api_design.md is not pushed, finish it first: today's task is easier when the design is written down. Otherwise continue with Day 15's schema.sql and queries.sql, which tomorrow's Postgres work depends on.

## DSA practice (30 min)

Both problems are in day23/dsa.py with examples and hints. Give each 15 minutes before reading the hints.

- match_route: given a pattern such as /v1/entries/{uid}/tags/{tag} and a path such as /v1/entries/blt7/tags/sale, return {'uid': 'blt7', 'tag': 'sale'}, or None if the path does not match. This is a small version of what FastAPI does for every request. Hint: split both on "/" and compare segment counts first.
- unique_slug: turn "Diwali Gift Guide" into diwali-gift-guide, and if that is already taken return diwali-gift-guide-2, then -3, and so on. Practises sets and while loops, and it is the friendly alternative to today's 409. Hint: a regular expression can find the runs of letters and digits for you.
## Quiz (3 quick questions)

- Why does the task use separate EntryCreate, EntryUpdate and EntryOut models instead of one Entry model? Give two reasons.
- GET /v1/entries/{uid} is declared before GET /v1/entries/latest. What does a request to /v1/entries/latest return, and what are two ways to fix it?
- In a PATCH handler, what is the difference between body.model_dump() and body.model_dump(exclude_unset=True) for the body {"title": "New"}, and why does it matter?
## When you're done

Paste into the Forward Deployment Engineer project chat as Day 23 review: content_api.py, the last lines of your pytest output, the smoke.sh output, your six predictions with the real results, your quiz answers, dsa.py, and the link to your latest commit. Say how far the catch-up item got.

