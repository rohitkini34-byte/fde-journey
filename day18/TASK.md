# Day 18 — Python and Postgres: psycopg 3, Parameterised Queries, SQL Injection & Transactions (11 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day18/load_export.py

Acme Retail is moving its blog off the old CMS. Their content team exported every post to CSV with your Day 6 tool, and the new platform reads from Postgres. Write the loader. The customer's one requirement: a failed run must leave the database untouched, so they can fix the file and try again.

```bash
# day18/ layout for today's task (everything except load_export.py's
# function bodies and dsa.py is given)
day18/
    setup.sql  # lesson tables for the concept examples
    schema.sql  # blog_authors, blog_tags, blog_posts, blog_post_tags
    posts.csv  # 8 posts, the Day 6 export format
    posts_bad.csv  # line 7 has word_count "about 1000"
    posts_dup.csv  # line 8 repeats uid blt003 after 6 good posts
    check_load.sql  # shows what a correct load looks like
    load_export.py  # YOUR loader: six functions with hints
    test_load_export.py  # 19 given tests, do not edit
    requirements.txt  # psycopg[binary] and pytest, pinned
    dsa.py  # today's two DSA problems
    day18_notes.ipynb  # every example from this session, with outputs
```

Step 1 (10 min): run schema.sql, open it and posts.csv side by side, and say out loud which CSV column ends up in which table.

Step 2 (60 min), no database yet: write get_db_url, parse_row and read_posts. Run python -m pytest -q -k "parse or read"; those 8 tests need no database.

Step 3 (40 min): write get_or_create, load_posts and find_posts_by_author, then main. Run the whole suite.

Step 4 (10 min): the manual runs below, in this order, checking with check_load.sql and SELECT count(*) FROM blog_posts; in psql after each.

```bash
# What correct runs look like (reset first with schema.sql)
$ python load_export.py posts.csv --dry-run
parsed 8 posts from posts.csv (dry run, nothing loaded)
$ python load_export.py posts_bad.csv
error: line 7: word_count 'about 1000' is not a whole number; nothing was
loaded  # one line on stderr; exit code 1; no connection was opened
$ python load_export.py posts_dup.csv
error: line 8: post blt003 is already in the database; nothing was loaded
# exit 1. Six posts were inserted before line 8, and all were rolled back:
# SELECT count(*) FROM blog_posts;  -> 0
$ python load_export.py posts.csv
loaded 8 posts, 4 authors, 8 tags, 10 tag links  # exit 0
$ python load_export.py posts.csv
error: line 2: post blt001 is already in the database; nothing was loaded
# exit 1, and the 8 posts from the previous run are untouched
$ unset DATABASE_URL; python load_export.py posts.csv
error: DATABASE_URL is not set. Run: export DATABASE_URL=postgresql://...
# exit 2 (the real message ends with localhost/fde; shortened to fit here)
```

Acceptance criteria:

- All the runs above print exactly those lines and exit with those codes (check with echo $?). Errors go to stderr, and none prints a traceback.
- After the posts_bad.csv and posts_dup.csv runs, every blog_ table has 0 rows.
- After the good load, check_load.sql shows posts 8, authors 4, tags 8, tag_links 10; blt003 has no author (NULL, not an empty string) and no tags; the blt002 title keeps its quotes; Renée and O'Neil are spelled correctly.
- python -m pytest -q shows 19 passed with DATABASE_URL set.
- Every value reaches SQL through a placeholder. The table name in get_or_create goes through sql.Identifier. No f-string or + builds SQL text.
- The whole load runs inside one conn.transaction() block, and no commit() happens per row.
- python -c "import load_export" inside day18/ prints nothing.
- Committed and pushed with a meaningful message. .venv/ is not committed.
Hints (no solutions, try first):

- Build bottom-up and test each function alone. parse_row needs only a dict; copy GOOD from the test file into a Python shell.
- Concept 5's example already shows every conversion parse_row needs. What is new is checking them in order and raising LoadError with the exact message.
- For the error messages, raise LoadError(...) from None hides the original ValueError, so the user sees only your line.
- get_or_create is Concept 2's sql.Identifier example plus Concept 4's RETURNING id. Return a tuple: the id and whether you created it.
- Raise the duplicate-post LoadError inside the conn.transaction() block. Raising it there is what triggers the rollback.
- Open the connection with autocommit=True in main, so conn.transaction() is the only transaction. Concept 3's third example has the shape.
- If tests hang or fail with "aborted", an earlier error left a transaction open: look for a caught exception that carried on (Concept 3, fourth example).
## DSA practice (30 min)

Both problems are in day18/dsa.py with signatures, examples and hints.

- Safe identifier (easy). is_safe_identifier(name): True only for 1 to 63 characters of a-z, 0-9 and _, not starting with a digit. This is the allow-list you put in front of sql.Identifier. Hint: check the length first, then compare every character against a set.
- Transactional key-value store (medium). TxStore with get, set, delete, and nested begin, commit and rollback. This is a common interview question. Hint: keep a list of dicts as a stack, one dict of pending changes per open transaction; reads look from the newest layer down.
## Quiz (3 quick questions)

- A teammate's fix for a search bug is name.replace("'", "''") before an f-string query. In two sentences, explain to them what to do instead and why.
- Your nightly loader has inserted 5,000 of 8,000 rows when the network drops. With one transaction for the load, what is in the database the next morning, and what does the customer need to do?
- Why does get_or_create use sql.Identifier for the table name but %s for the name value? Could you swap them?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 18 review": your recap answers, your four predictions next to the real outputs, load_export.py, the pytest -q summary line, the terminal output of the six manual runs, your quiz answers, dsa.py, and the link to your latest commit. Say how far the Day 17 catch-up got.

