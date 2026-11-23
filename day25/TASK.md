# Day 25 — Testing APIs and Errors: TestClient, a Test Database, Dependency Overrides & One Error Shape (18 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): test Acme's asset API

Scenario: Acme Retail's agency is about to build a media picker on the asset API, and their lead has two conditions before they start: a green test suite they can run in their CI, and one error format they can handle in one place. You own both today. The app (assets_api.py) is finished and you do not edit it; everything you write is in the three files below.

| File | Given | You write | Run while working |
|---|---|---|---|
| errors.py | error classes, HTTP_CODES, request_id_of, install_error_handlers | error_response and four handlers | pytest -q test_error_contract.py |
| conftest.py | imports, docstrings | seven fixtures | pytest -q -k health |
| test_assets_api.py | 22 named stubs, VALID, one parametrize table | the body of every test | pytest -q |
| mutation_check.txt | nothing | which tests caught your deliberate bug | pytest -q |

Every function has a comment block with the exact rules and an example, and step-by-step hints. Work in this order:

- Step 0 (10 min). Do the Setup above. python3 -m pytest -q must show 37 errors that all end in NotImplementedError, and no import errors. Then start the app with fastapi dev assets_api.py and open /docs once, to see what you are about to test.
- Step 1: conftest.py (40 min). Write the fixtures in file order. test_db_url and prepared_db first, then clean_db, app and client. When python3 -m pytest -q -k health shows the health test failing with NotImplementedError from the TEST body (not from a fixture), the fixtures work. Then make_asset and db.
- Step 2: errors.py (30 min). Write error_response first, then one handler at a time. After each one, rerun python3 -m pytest -q test_error_contract.py and watch the passes grow to 12.
- Step 3: test_assets_api.py (40 min). Fill the 22 stubs, top to bottom. Run after every three or four tests. Each one: status code first, then body, then table where the stub says so.
- Step 4: mutation check (10 min). Prove your tests can fail. In assets_api.py, change one rule on purpose (status_code=201 to 200 in create_asset, or ge=1 to ge=0 on limit), run the suite, write the names of the tests that went red into mutation_check.txt, then undo the change. If nothing went red, a test is missing: add it.
- Step 5. Run ruff check . and mypy errors.py conftest.py, then commit and push.
Acceptance criteria:

- python3 -m pytest -q inside day25/ shows 37 passed. Do not edit test_error_contract.py or assets_api.py (apart from the temporary mutation).
- Running the suite twice in a row gives 37 passed both times, and any single test passes when run alone with -k.
- ACME_TEST_DATABASE_URL=postgresql:///fde python3 -m pytest -q stops before any test with a clear "refusing" message, and your fde data is untouched.
- No error response anywhere contains a Python exception message or class name; the 500 test proves it.
- errors.py does not import assets_api; every test has one Act and asserts the status code.
- mutation_check.txt names at least one test that failed for your deliberate bug.
- Committed and pushed with a message such as "Day 25: API tests, test database fixtures and one error contract" (a WIP push counts).
Hints, not answers:

- If every test errors in the app or client fixture with a connection message, run psql -d fde_test -c 'select 1'. If that fails too, the problem is the URL, not your code.
- If the contract tests show {'detail': 'Not Found'} for an unknown route, your HTTPException handler is registered for the wrong class. Q3 below explains it.
- If the 500 test raises RuntimeError instead of returning a response, look at how your client fixture builds the TestClient (Concept 1).
- If test_db_is_empty_at_the_start_of_each_test fails only in the full run, clean_db is not autouse, or it runs on a different database from the app.
- When the 422 field order surprises you, print exc.errors() once inside the handler and compare it with the request body.
Stretch (only if the task and the push are done): copy your Day 24 content_api.py into a branch and point five of today's test patterns at it (create, 404, 409, 422, list). Most tests port with only the URL and the body changed, which is the payoff of fixtures and one error contract.

Catch-up (1h): first push whatever exists of Days 22, 23 and 24 (15 min). Then finish Day 24 until its 32 tests pass; tomorrow's webhook is added to that API's layers.

## DSA practice (30 min)

Both problems are in day25/dsa.py with examples and hints. Give each 15 minutes before reading the hints.

- group_field_errors: group Pydantic-style error dicts by their dotted field path, keeping first-seen order: [{"loc": ("body", "tags", 2), "msg": "not a string"}] becomes {"body.tags.2": ["not a string"]}. This is the core of your 422 handler. Hint: the Day 3 grouping pattern with setdefault.
- json_diff: list every difference between two nested JSON values as strings such as "changed error.code: 'not_found' != 'conflict'", "missing a.2" and "extra debug". This is what pytest's assertion message does for dicts. Hint: recursion with three cases (both dicts, both lists, anything else) and a helper that joins path parts with dots.
## Quiz (3 quick questions)

- Your conftest overrides get_settings with dependency_overrides to point at fde_test, and all tests pass. Why is this dangerous, and what does today's conftest do instead?
- Give one reason to TRUNCATE before each test, and one situation where rolling back a transaction per test is the better choice.
- A teammate's 500 handler returns {"error": {"message": str(exc)}} "so that clients can debug". Name two things that are wrong with it and what to do instead.
## When you're done

Paste into the Forward Deployment Engineer project chat as Day 25 review: errors.py, conftest.py, the last lines of your pytest output, mutation_check.txt, your six predictions next to the real results, your quiz answers, dsa.py, and the link to your latest commit. Say whether Days 22 to 24 are pushed and how far Day 24's tests got.

