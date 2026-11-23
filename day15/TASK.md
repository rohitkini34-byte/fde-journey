# Day 15 — Relational Thinking and First Queries: Tables, Keys, Data Types, psql, CREATE TABLE, INSERT, SELECT, WHERE, ORDER BY & LIMIT (8 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day15/schema.sql and day15/queries.sql

The scenario: Acme Retail syncs its Contentstack stack into Postgres so a reporting dashboard (and, in Week 6, an AI assistant) can query it. You design the two tables and answer the content team's first ten questions. The starter files are in your repo under day15/: the brief and acceptance criteria are at the top of each file, with hints above every TODO. seed.sql is complete; do not edit it, because the expected answers depend on it.

- Pull and look (10 min). git pull, then read the top of schema.sql and queries.sql in VS Code. Open seed.sql and look at the data: three content types with prices only on products, Hindi and Marathi entries that share a slug with their English versions, drafts with no author.
- Write schema.sql (40 min). Drop both tables if they exist (entries first), create content_types and entries exactly as the brief says, then insert the four content types in one INSERT ... RETURNING uid.
- Load it (5 min). From inside day15/, run psql -d fde -v ON_ERROR_STOP=1 -f schema.sql -f seed.sql. If seed.sql fails, the error names the column that does not match the brief: fix schema.sql and run the command again. Then run it a second time to prove the file is safe to re-run.
- Check the shape (5 min). In psql: \d content_types, \d entries, and SELECT count(*) FROM entries; (expect 20). count(*) is tomorrow's topic; today just read the number.
- Answer Q1 to Q10 (60 min). Write one query per question in queries.sql. Run each one alone in psql first, compare it with its Expected comment, then save it in the file. When all ten are in, run psql -d fde -f queries.sql and check every result once more.
- Commit and push. git add day15 && git commit -m "Day 15: CMS schema and 10 queries" && git push.
Acceptance criteria:

- psql -d fde -v ON_ERROR_STOP=1 -f schema.sql -f seed.sql runs with no ERROR lines, twice in a row.
- \d entries shows the 13 columns with the types, NULL rules and defaults in the brief; SELECT count(*) FROM entries; returns 20.
- Every query in queries.sql matches its Expected comment: row count, first row and (where given) last row.
- No SELECT *; every multi-row query has an ORDER BY with a tie-breaker where values can repeat.
- Each statement has a one-line comment saying why, written for a customer.
- The day15 folder is pushed to main.
Hints, if you are stuck (try for 10 minutes first):

- Q2 and Q3: ORDER BY a DESC, b sorts by a, and uses b only when two rows have the same a.
- Q4: drafts with no author is two conditions. One of them tests for a missing value; Concept 5 says how.
- Q8: "under 1000" means <, not <=, and the question does not mention status.
- Q9: page 2 at 5 per page skips how many rows?
- Q10: compare updated_at with the date '2026-10-01'. The SET timezone line at the top of the file decides which midnight that is.
Catch-up lane (1h): Day 5, support_ticket.py. Open the Day 5 folder from the files in the project chat (or your laptop copy) and finish the Ticket dataclass and the SLA report. Done when the SLA breach report prints for tickets_export.json as shown in the file's docstring. Push it as its own commit: "Day 5: support ticket model".

## DSA practice (30 min)

Two problems in day15/dsa.py that are today's SQL written by hand. Signatures, examples and hints are in the file; the expected outputs are in its __main__ block.

- paginate(items, page, page_size). Return one page of a list, like LIMIT and OFFSET. Hint: work out how many items come before page 1, page 2 and page 3, and turn that into a formula. Slicing past the end of a list does not raise an error.
- duplicate_slugs(rows). Find (slug, locale) pairs used by more than one entry: two pages at the same URL. Hint: group uids in a dict whose key is a tuple, as on Day 3, then keep only the keys with more than one uid. The same slug in two different locales is not a duplicate.
## Quiz (3 quick questions)

- A customer's CMS has a tags field holding a list on each entry. Their developer suggests storing it in a text column as 'sale,diwali'. What do you say, and why?
- Write the query: the 3 most recently published en-us entries in the entries table, showing title and published_at.
- Why does WHERE author = NULL return no rows even when some authors are missing, and what do you write instead?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 15 review": your recap answers, your six predictions next to the real outputs, your schema.sql and queries.sql (or the commit link), your dsa.py, your quiz answers and the Day 5 status. Note anything that felt unclear; tomorrow starts there.

