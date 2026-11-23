# Day 24 — FastAPI with Postgres: Dependencies, a Connection Pool, Settings & a Repository Layer (17 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): the content API on Postgres

Scenario: Acme Retail's partner agency has been building against your Day 23 API, and every time you restarted it their test entries vanished. Today the same URLs get a real database. The data goes into the api_entries table from the given schema.sql, in your Week 3 fde database; the tests use a separate fde_test database so they can empty it freely.

A note on the schema: Day 17's six-table model (entries, locale versions, authors, tags) is the right long-term shape for Acme's content. Today's table keeps tags in a Postgres text[] column on one table, so that the work stays on the new ideas (settings, pool, dependencies, repository) rather than on multi-table writes. Day 27's stretch goal moves tags back into a junction table.

| File | Given | You write | Run while working |
|---|---|---|---|
| settings.py | model_config, database_url | four fields, get_settings() | pytest -q -k settings |
| db.py | imports, docstrings | make_pool(), get_conn() | pytest -q -k "pool or health" |
| repository.py | errors, new_uid(), COLUMNS | six methods of EntryRepository | pytest -q -k repo |
| content_api.py | models, lifespan, get_repo, /health, create, get, delete | list_entries, update_entry, publish_entry | pytest -q |

Every function has a comment block with the exact rules and an example, and step-by-step hints. Work through the files in the order of the table and rerun the tests after each one.

- Step 0 (10 min). Do the Setup above. Then run python3 -m pytest -q: you should see many failures and errors that all end in NotImplementedError, and no import errors. If the tests cannot connect, set ACME_TEST_DATABASE_URL as the test file's docstring explains.
- Step 1: settings.py (15 min). Add the four fields and get_settings(). Run python3 settings.py with your .env in place and check that the password is not printed.
- Step 2: db.py (15 min). Write make_pool() and get_conn(). When -k "pool or health" passes, your app can start: fastapi dev content_api.py, then curl -s localhost:8000/health.
- Step 3: repository.py (60 min). One method at a time, in the order of the file. The repository tests call the methods directly on a connection, so you can test the SQL without any routes.
- Step 4: the three routes (20 min). Copy the pattern of the three worked examples. Then the full suite should show 32 passed.
- Step 5: the restart check (10 min). With fastapi dev content_api.py running, create an entry with curl (Day 22's flags), note its uid, stop the server with Ctrl+C, start it again, and GET the entry. Paste the four commands and their output into day24/restart_check.txt.
- Step 6. Run ruff and mypy, then commit and push.
Acceptance criteria:

- python3 -m pytest -q inside day24/ shows 32 passed. Do not edit test_content_api.py.
- day24/restart_check.txt shows an entry created, the server restarted, and the same entry returned with status 200.
- No route contains SQL, and repository.py contains no HTTPException and no commit().
- Every value reaches Postgres as a parameter; the only f-strings in SQL insert the COLUMNS constant.
- .env is in .gitignore and not committed; .env.example is.
- ruff check . and mypy content_api.py are clean (Day 12).
- Committed and pushed with a message such as "Day 24: content API on Postgres with a pool and a repository" (a WIP push counts).
Hints, not answers:

- If every API test errors with AttributeError: 'State' object has no attribute 'pool', the lifespan did not finish: usually make_pool() still raises, or the pool cannot reach the database. Run python3 -m pytest -q -k health -x and read the first traceback.
- psycopg's errors are precise. "the query has 2 placeholders but 1 parameters were passed" means a missing comma or a missing key in your parameter dict.
- When a repository test fails, open psql on fde_test and run your SQL by hand with real values; then put the placeholders back.
- In list_page, test the last page on purpose: with exactly limit rows left, next_cursor must be None.
- If update returns the old title, check that you used RETURNING and returned the row from the UPDATE, not from an earlier get.
Stretch (only if the task and the push are done): add a setting statement_timeout_ms (default 5000) and pass it to every pooled connection, so that a runaway query is stopped by Postgres. Hint: ConnectionPool(..., kwargs={"options": "-c statement_timeout=5000", ...}). Prove it with a route or a test that runs SELECT pg_sleep(10) and fails after 5 seconds.

Catch-up (1h): first push whatever exists of Days 22 and 23, even unfinished (15 min). Then finish Day 23's content_api.py until its 26 tests pass, because today's routes copy its patterns.

## DSA practice (30 min)

Both problems are in day24/dsa.py with examples and hints. Give each 15 minutes before reading the hints.

- parse_env: turn the text of a .env file into a dict: skip comments and blank lines, allow export , split at the first =, strip one pair of matching quotes, let a later key win, and raise ValueError with the line number for a line without =. This is what pydantic-settings does with your .env file. Hint: str.split("=", 1).
- SimplePool: a toy pool that lends out the numbers 0 to size-1 first in, first out, takes them back, refuses a double release, and raises PoolExhausted when everything is lent out. This is the bookkeeping inside psycopg_pool. Hint: a deque for the free numbers and a set for the ones in use.
## Quiz (3 quick questions)

- Why is the pool built in the lifespan, and not at module level or inside get_conn? Give one reason against each alternative.
- A route holds its pooled connection while it calls an LLM API that takes 20 seconds. The pool has max_size=5 and timeout=5. What do the 6th to 10th concurrent requests see, and how do you fix it without raising max_size?
- Why does publish() use one UPDATE ... WHERE status = 'draft' instead of get() followed by UPDATE? Describe the bug the second version allows.
## When you're done

Paste into the Forward Deployment Engineer project chat as Day 24 review: repository.py, the last lines of your pytest output, restart_check.txt, your six predictions next to the real results, your quiz answers, dsa.py, and the link to your latest commit. Say how far the catch-up item got and whether Days 22 and 23 are pushed.

