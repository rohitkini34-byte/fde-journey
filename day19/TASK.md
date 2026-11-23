# Day 19 — Constraints, Indexes and Upserts: NOT NULL, UNIQUE, CHECK, ON CONFLICT, Indexes, EXPLAIN ANALYZE & Migrations (12 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day19/upsert_loader.py

Acme Retail runs your Day 18 loader every night after the CMS export. On night two it failed: every post was already there. The customer's requirements for the replacement: it can run any number of times; it reports how many posts were inserted, updated and unchanged; a bad entry stops the whole run with a message their content team understands, and leaves the database untouched; and the "daily views" report their editors use must get fast.

```sql
# day19/ layout for today's task. Everything except upsert_loader.py's
# function bodies, migrations 003 and 004, explain_notes.md and dsa.py
# is given.
day19/
    setup.sql                 # lesson tables for the concept examples
    reset.sql                 # drops the task tables: a clean start
    migrations/
        001_create_cms_tables.sql
        002_create_cms_views.sql
    seed_views.sql            # 400,000 rows of daily views
    slow_query.sql            # the report the team calls "slow"
    export_v1.json            # 6 posts, the nightly CMS export
    export_v2.json            # next night: 1 new post, 2 edited
    export_bad.json           # one post with status "live"
    upsert_loader.py          # YOUR loader: 6 TODO functions
    test_upsert_loader.py     # 21 given tests
    explain_notes.md          # YOUR before/after notes
    requirements.txt          # psycopg[binary] 3.3 and pytest
    dsa.py                    # today's two DSA problems
```

Step 1 (10 min): read migrations 001 and 002 and list every rule they define. For each, write one export value that would break it.

Step 2 (25 min), no database yet: write read_export. Then apply_migrations, and run python -m pytest -q -k "read_export or migration".

Step 3 (50 min): write upsert_author, upsert_post, sync_tags, load and main, then do the first four manual runs below.

Step 4 (10 min): seed the views table and run slow_query.sql. Paste the output into explain_notes.md and fill in the three lines under it.

Step 5 (15 min): write migrations/003_add_views_index.sql (an index named cms_views_post_day_idx that serves slow_query.sql) and migrations/004_title_not_blank.sql (a CHECK named cms_posts_title_not_blank that refuses titles that are empty or only spaces). Run the loader again so it applies them.

Step 6 (10 min): run slow_query.sql again, finish explain_notes.md, then run the whole test suite.

```bash
# Steps 2 to 6: what correct runs look like, in order.
$ psql "$DATABASE_URL" -f reset.sql
$ python upsert_loader.py export_v1.json
migrations applied: 001_create_cms_tables.sql, 002_create_cms_views.sql
export_v1.json: inserted 6, updated 0, unchanged 0
$ python upsert_loader.py export_v1.json     # the re-run that broke Day 18
migrations: up to date
export_v1.json: inserted 0, updated 0, unchanged 6
$ python upsert_loader.py export_v2.json
migrations: up to date
export_v2.json: inserted 1, updated 2, unchanged 4
$ python upsert_loader.py export_bad.json; echo "exit $?"
migrations: up to date
error: entry blt008 breaks rule cms_posts_status_check; nothing was loaded
exit 1
$ psql "$DATABASE_URL" -f seed_views.sql
$ psql "$DATABASE_URL" -f slow_query.sql     # BEFORE: paste into notes
#   (write migrations 003 and 004 now)
$ python upsert_loader.py export_v2.json
migrations applied: 003_add_views_index.sql, 004_title_not_blank.sql
export_v2.json: inserted 0, updated 0, unchanged 7
$ psql "$DATABASE_URL" -f slow_query.sql     # AFTER: paste into notes
```

Acceptance criteria:

- All the runs above print exactly those lines and exit with those codes (echo $?). Errors go to stderr, and no run prints a traceback.
- After the export_bad.json run, the tables hold exactly what export_v2.json left: posts 7, authors 4, tags 8, tag links 11.
- python -m pytest -q shows 21 passed (17 pass before migrations 003 and 004 exist).
- Every value reaches SQL through a placeholder; no f-string or + builds SQL text. Each migration runs in its own transaction together with its bookkeeping row; the whole load runs in one conn.transaction() block.
- explain_notes.md holds both plans: a Seq Scan before 003 and a Bitmap Index Scan or Index Scan after it, the two execution times, and your two sentences on the column order.
- Migrations 001 and 002 are unchanged; 003 and 004 each make one change, and after the run all four names are in schema_migrations.
- python -c "import upsert_loader" inside day19/ prints nothing.
- Committed and pushed with a meaningful message; .venv/ is not committed.
Hints (no solutions, try first):

- upsert_post is Concept 2's second example with six columns. Named placeholders (%(title)s with a dict) keep it readable.
- For "unchanged", the change check must compare every column you write, including author_id and published_at, and must not compare updated_at.
- sync_tags is three small steps: clean the names, upsert each tag and its link, delete the links you did not keep. The test file shows exactly what "clean" means.
- If apply_migrations records a file as applied even when it fails, the INSERT into schema_migrations is outside the transaction block.
- If tests hang or fail with "current transaction is aborted", an exception was caught inside a transaction block and the code carried on (Day 18, Concept 3).
- For migration 003, look at the WHERE of slow_query.sql: which column is compared with =, and which with >=? Concept 3's rules of thumb decide the order.
- For migration 004, btrim(title) removes spaces from both ends, like .trim() in JavaScript.
## DSA practice (30 min)

Both problems are in day19/dsa.py with signatures, examples and hints.

- In-memory upsert (easy). upsert_records(store, incoming) merges records into a dict keyed by uid and returns the inserted, updated and unchanged counts: the same contract as today's loader, without a database. Hint: three cases, decided by in and ==.
- Lower bound (medium). lower_bound(keys, target) returns the first position whose key is >= target in a sorted list, in O(log n). This is the search a B-tree index does at every level. Hint: keep lo and hi, and move hi = mid (not mid - 1) when keys[mid] is not smaller than the target. Check yourself with bisect.bisect_left afterwards.
## Quiz (3 quick questions)

- The customer's admin UI already validates that status is draft, published or archived. Give two reasons to add the CHECK constraint to the database anyway.
- A report filters WHERE country = 'IN' AND viewed_on >= '2026-01-01'. Your teammate proposes an index on (viewed_on, country). What would you suggest, and how would you prove it is better?
- Your nightly job runs twice by mistake. With today's loader, what is in the database after the second run, and what do the two summary lines say?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 19 review": your recap answers, your four predictions next to the real outputs, upsert_loader.py, migrations 003 and 004, explain_notes.md, the pytest summary line, the terminal output of the manual runs, your quiz answers, dsa.py, and the link to your latest commit. Say how far the Day 18 catch-up got.

