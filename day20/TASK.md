# Day 20 — Analytics SQL: CTEs, Window Functions, JSONB & pandas read_sql (13 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day20/analytics.sql and report.py

Acme Retail's content lead sends the same three questions every Monday: what is live and what is waiting in draft, what is getting views this festive season, and "can I have it in Excel?". Your job: answer the questions in SQL a teammate can read, then wrap the weekly numbers in a small pandas report. Week 4 puts both behind FastAPI endpoints, so the queries must be correct, ordered and reusable.

```bash
# day20/ layout for today's task. Everything except the SELECT 'TODO'
# lines in analytics.sql, the TODO functions in report.py and dsa.py
# is given.
day20/
    setup.sql            # lesson tables for the concept examples
    task_data.sql        # Acme's cms_versions (20 saves of 12 entries)
                         # and cms_daily_views (4 weeks, 280 rows)
    analytics.sql        # YOUR 8 queries, A1 to A8
    test_analytics.py    # 8 given tests: runs each query, checks rows
    report.py            # YOUR weekly report: 5 TODOs
    test_report.py       # 14 given tests (9 need no database)
    requirements.txt     # psycopg 3, SQLAlchemy 2, pandas, pytest
    dsa.py               # today's two DSA problems
    day20_notes.ipynb    # today's examples, already run
```

Step 1 (10 min): run psql "$DATABASE_URL" -f task_data.sql, then look at the data: SELECT * FROM cms_versions ORDER BY uid, version; and \d cms_daily_views. Write down which entries have more than one version, which were never published, and which have no views.

Step 2 (45 min): write A1 to A5 in analytics.sql. Try each in psql first, then paste it in, and run python -m pytest -q test_analytics.py after each one. A failing test tells you whether the columns, the row count or the values differ.

Step 3 (25 min): write A6 (week over week with lag), A7 and A8 (JSONB). All 8 tests should pass.

Step 4 (35 min): write report.py: DAILY_SQL and make_engine first, then summarise_by_type and weekly_grid (their tests need no database), then fetch_daily and main.

Step 5 (5 min): do the four manual runs below, open weekly_views.csv in Excel or Numbers, and run the whole suite.

```bash
# Steps 2 to 5: what correct runs look like.
$ python -m pytest -q test_analytics.py
........                                                     [100%]
8 passed in 0.13s
$ python report.py
rows: 280, entries: 10, since: 2026-10-05
              entries  total_views  avg_per_entry
content_type
campaign            4        48541        12135.2
article             2        13664         6832.0
page                4        13082         3270.5
wrote summary_by_type.csv and weekly_views.csv
$ python report.py 2026-10-26
rows: 70, entries: 10, since: 2026-10-26
              entries  total_views  avg_per_entry
content_type
campaign            4        16722         4180.5
article             2         4716         2358.0
page                4         3786          946.5
wrote summary_by_type.csv and weekly_views.csv
$ python report.py 2027-01-01
no views since 2027-01-01
$ DATABASE_URL=postgresql://localhost:5999/fde python report.py
error: cannot reach the database; is Postgres running?
$ echo $?
1
$ python -m pytest -q
22 passed in 0.66s
```

Acceptance criteria:

- python -m pytest -q inside day20/ shows 22 passed (8 in test_analytics.py, 14 in test_report.py).
- The four manual runs print exactly the lines above and exit with those codes. Errors go to stderr, and no run prints a traceback.
- Every query that needs the latest version gets it from a CTE named latest, built with row_number() or DISTINCT ON. No query uses a correlated max(version) subquery.
- Every query in analytics.sql ends with an ORDER BY, and every CTE and output column has a clear name.
- The since date reaches SQL through :since and params; no f-string or + builds SQL text anywhere.
- python -c "import report" inside day20/ prints nothing.
- Committed and pushed with a meaningful message; .venv/ and the generated CSV files are not committed.
Hints (no solutions, try first):

- A2 is A1 with one extra condition. Where does it go: before the numbering (in the CTE) or after it (rn = 1)? Try both and compare blt003.
- A3 joins two CTEs. If you get blt010 or blt012 in the result, your join keeps entries that were never published.
- A4: count the rows of your totals CTE before ranking. If it has 10 rows instead of 12, the LEFT JOIN or the COALESCE is missing.
- A6: build the weekly CTE first and check it has 8 rows for the two entries. Only then add lag().
- A7: run your noindex condition on its own over all latest rows. blt009 (noindex true) must be out; blt005 (no noindex key at all) must be in.
- weekly_grid: print df["day"].dt.to_period("W-SUN").head() to see what a weekly period looks like before you convert it.
- If a report.py test fails with a KeyError on a column name, print out.columns and compare with the names in the test.
## DSA practice (30 min)

Both problems are in day20/dsa.py with signatures, examples and hints. Run python dsa.py; every line should print True.

- Latest by key (easy). latest_by_key(records) takes (uid, version, title) tuples in any order and returns {uid: title of the highest version}: today's "latest version per entry" without a database. Hint: one pass with a dict that stores the best (version, title) seen so far for each uid.
- Maximum window sum (medium). max_window_sum(nums, k) returns the largest total of k consecutive days, in O(n). This is the moving frame from Concept 3. Hint: when the window slides one step, one number enters and one leaves; you never need to re-add the whole window.
## Quiz (3 quick questions)

- A teammate finds the latest version per entry with WHERE version = (SELECT max(version) FROM cms_versions v2 WHERE v2.uid = v.uid). The customer now wants "latest published version, and the version before it". Why is row_number() the better starting point?
- Acme wants to store each entry's SEO block. One proposal: three columns (meta_title, meta_description, noindex). The other: one JSONB column for all SEO fields. Which would you choose for an FDE engagement where content types keep changing, and what would make you move a field out of JSONB?
- The content lead says your report shows "0 views" for a new page on a day before it was published. What happened in the code, and what would you change?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 20 review": your recap answers, your four predictions next to the real outputs, analytics.sql, report.py, the pytest summary line, the terminal output of the four manual runs, your quiz answers, dsa.py, and the link to your latest commit. Say how far the Day 19 catch-up got.

