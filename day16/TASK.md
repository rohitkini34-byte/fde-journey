# Day 16 — Aggregates and NULL: COUNT, SUM, AVG, GROUP BY, HAVING, DISTINCT, COALESCE & CASE (9 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day16/report.sql

The scenario: Acme Retail's content-ops lead runs a Monday review of their Contentstack stack. Until now an analyst built it by hand from CSV exports. You will answer her nine standing questions with SQL against cms_entries, the nightly sync table, so the report can be produced in seconds and later served by an API. The starter file has the brief, the exact expected output for each question, and hints above every TODO. Do not edit setup.sql; the expected outputs depend on its rows.

- Pull and load (10 min). Apply yesterday's patch if you have not, then git pull. From inside day16/, run psql -d fde -v ON_ERROR_STOP=1 -f setup.sql. Check with SELECT count(*) FROM cms_entries; (expect 24).
- Look before you count (10 min). Run \d cms_entries and SELECT DISTINCT content_type, locale, status FROM cms_entries ORDER BY 1, 2, 3;. Note which columns can be NULL. That tells you where count(*) and count(col) will differ.
- Answer R1 to R9 (90 min). Write one query per question under its TODO in report.sql. Run each alone in psql, compare it with its Expected comment, then save it.
- Run the whole report (5 min). psql -d fde -v ON_ERROR_STOP=1 -f report.sql. Every result must match.
- Commit and push. git add day16 && git commit -m "Day 16: content-ops report" && git push.
The nine questions (full wording and expected outputs are in the file):

| # | Question | Main idea |
|---|---|---|
| R1 | One-row summary: total, published, drafts, archived, unassigned | count(*), conditional counts, count(col) |
| R2 | Per content type: entries, unique entries, locales | GROUP BY, count(DISTINCT) |
| R3 | Per content type and status | GROUP BY two columns |
| R4 | Per locale: total plus one column per status | pivot with CASE or FILTER |
| R5 | Per owner: entries, published, views (Unassigned for NULL) | COALESCE, NULL group |
| R6 | Owners holding more than one draft | WHERE, GROUP BY, HAVING |
| R7 | Product price health: priced, missing, min, max, average | aggregates over NULLs |
| R8 | Traffic buckets in business order | CASE, sort key |
| R9 | Stale drafts (untouched 30+ days) per owner | dates, interval, min() |

Acceptance criteria:

- psql -d fde -v ON_ERROR_STOP=1 -f report.sql runs with no ERROR lines.
- Each of R1 to R9 matches its Expected comment exactly: the columns, their names, the row count and every value.
- Every multi-row result has an ORDER BY with a tie-breaker; no SELECT *.
- No NULL shows in an owner or label column (use coalesce), and no rounded value is shown unrounded.
- Each query has a one-line comment saying what the content team learns from it.
- The day16 folder is pushed to main.
Hints, if you are stuck (try for 10 minutes first):

- R1: one SELECT with five aggregates and no GROUP BY. "Unassigned" is the number of rows minus the number of rows that have an author.
- R2: one uid appears once per locale, so unique entries is a count of distinct uids.
- R4: start from Concept 6's pivot; the columns are total, published, draft, archived.
- R5: group by the raw author column, but show coalesce(author, 'Unassigned'). Views must show 0, not NULL, for an owner whose entries have no views.
- R6: which condition is about rows and which is about groups? One goes before GROUP BY, one after.
- R8: ORDER BY can use an alias only on its own. Add a second CASE that returns 1 to 4 as a sort_order column, group by both, and order by it.
- R9: "30 days before the report date" is timestamptz '2026-11-09 00:00+05:30' - interval '30 days'. Use that fixed date, not now(), so the expected output never changes. min(updated_at)::date shows the oldest update as a date.
Catch-up lane (1h): Day 15. Finish schema.sql and queries.sql from yesterday's patch. Done when psql -d fde -v ON_ERROR_STOP=1 -f schema.sql -f seed.sql runs twice with no ERROR and all ten queries match. Push it as its own commit before today's.

## DSA practice (30 min)

Two problems in day16/dsa.py that are today's SQL written by hand. Signatures, examples and hints are in the file; the expected outputs are in its __main__ block.

- avg_ignoring_none(values). Behave exactly like SQL's avg: skip None, and return None (not 0, not an error) when nothing is left. Hint: filter first, then check whether the filtered list is empty before you divide.
- top_k_frequent(words, k). Return the k most common words, most frequent first, ties broken alphabetically. This is LeetCode 692, and it is GROUP BY word ORDER BY count(*) DESC, word LIMIT k in Python. Hint: count with a dict (Day 3), then sorted() with a key that returns a tuple: a negative count, then the word.
## Quiz (3 quick questions)

- A customer's dashboard shows "average discount ₹350" from avg(discount), where orders with no discount have NULL. The CFO thinks it means the average across all orders. Is it? What two numbers would you show instead?
- Write the query: published entries per locale in cms_entries, only locales with at least 3, most first.
- Why does WHERE count(*) > 1 fail? Where does a status = 'draft' condition belong in a grouped query, and why there?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 16 review": your recap answers, your six predictions next to the real outputs, report.sql (or the commit link), your dsa.py, your quiz answers and the Day 15 catch-up status. Note anything that felt unclear; tomorrow starts there.

