# Day 17 — Joins and Modelling: Primary and Foreign Keys, One-to-Many, Many-to-Many, INNER and LEFT JOIN & Normalisation (10 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day17/schema.sql and day17/joins.sql

The scenario: Acme Retail's Contentstack export has been one wide table so far (Days 15 and 16). Their content lead wants answers that table cannot give reliably: who owns what, which tags are used, and which pages are missing in Hindi and Marathi. You design the normalised model and answer eight questions with joins. The starter files have the brief, the exact table spec, the expected output for each question and hints above every TODO. Do not edit seed.sql; the expected outputs depend on its rows.

- Pull and load the lesson tables (10 min). git pull, then from inside day17/ run psql -d fde -v ON_ERROR_STOP=1 -f setup.sql if you have not already.
- Write schema.sql (40 min). The brief at the top lists six tables: authors, locales, content_entries, entry_locales, tags and entry_tags, with every column, type, key and ON DELETE rule. The parent table is called content_entries so it does not clash with Day 15's entries table in the same database. Start the file with one DROP TABLE IF EXISTS that lists all six, so it can be re-run. Then answer the three design questions D1 to D3 in the comments.
- Load the data (5 min). psql -d fde -v ON_ERROR_STOP=1 -f schema.sql -f seed.sql. If seed.sql fails, the error names the table or column that does not match the brief. Fix schema.sql and run both again. Check with \d entry_locales: two foreign keys and a two-column primary key.
- Answer J1 to J8 (60 min). One query per question under its TODO in joins.sql. Run each alone in psql, compare it with its Expected comment, then save it.
- Run the whole file (5 min). psql -d fde -v ON_ERROR_STOP=1 -f joins.sql. Every result must match.
- Commit and push. git add day17 && git commit -m "Day 17: normalised CMS schema and join queries" && git push.
The eight questions (full wording and expected outputs are in the file):

| # | Question | Main idea |
|---|---|---|
| J1 | Entries with their author's name (owned entries only) | INNER JOIN, one-to-many |
| J2 | Every entry with its author, Unassigned when none | LEFT JOIN, coalesce |
| J3 | Entries per author, including authors with none | LEFT JOIN, count(col) |
| J4 | Published versions and views per locale, by locale name | join a lookup table, GROUP BY |
| J5 | Every entry's English title and its tags as one string | two joins through a junction, string_agg |
| J6 | Tag usage, including unused tags | LEFT JOIN from the many-to-many side |
| J7 | Missing translations: every (entry, locale) with no version | CROSS JOIN plus anti-join |
| J8 | Published views per author: fix a given wrong query | the fan-out trap |

Acceptance criteria:

- psql -d fde -v ON_ERROR_STOP=1 -f schema.sql -f seed.sql runs with no ERROR lines, twice in a row.
- \d on each table shows the primary keys, foreign keys, UNIQUE columns and ON DELETE rules from the brief.
- Each of J1 to J8 matches its Expected comment exactly: columns, names, row count and every value.
- Every column in a join query is qualified with a table alias; every multi-row result has an ORDER BY with a tie-breaker; no SELECT *.
- D1 to D3 in schema.sql and the J8 explanation are answered in your own words, in one to three sentences each.
- The day17 folder is pushed to main.
Hints, if you are stuck (try for 10 minutes first):

- schema.sql: create parents before children (authors and locales, then content_entries, then the rest). The FK column's type must match the key it points at: integer for ids, text for the locale code.
- J3 and J6: which table must be complete? Put it on the left, and count a column of the right table.
- J4: join entry_locales to locales to get the name. The published filter is about rows, so it goes in WHERE.
- J5: start from content_entries, join entry_locales for the English title (a condition on both entry and locale), then left join entry_tags and tags. Wrap string_agg in coalesce for entries with no tags.
- J7: Concept 6's pattern, with your table names. Match the left join on both key columns.
- J8: run the given query, then remove one table from it. Ask which table the question does not need.
Catch-up lane (1h): Day 16. Finish report.sql from the Day 16 patch. Done when psql -d fde -v ON_ERROR_STOP=1 -f setup.sql -f report.sql runs with no ERROR and R1 to R9 match. Push it as its own commit before today's.

## DSA practice (30 min)

Two problems in day17/dsa.py that are today's SQL written by hand. Signatures, examples and hints are in the file; the expected outputs are in its __main__ block.

- hash_join(left, right, left_key, right_key). An inner join of two lists of dicts in O(n + m) time, which is how Postgres runs most joins (a "hash join"). Hint: loop over right once and build a dict from key to the list of rows with that key, then loop over left and look each key up. Two nested loops would also work but are O(n x m).
- find_orphans(children, parents, fk, pk). Return the children whose foreign key points at no parent: the check a foreign key does for you. Hint: put every parent key in a set (Day 3), then keep the children whose key is not None and not in the set.
## Quiz (3 quick questions)

- A customer's export has a categories column like "shoes,sale,new". Name the problem and the tables you would create instead, with their keys.
- Write the query: every locale's name with the number of entries that have a version in it, including locales with zero, most first. Use the task tables.
- A dashboard joins orders to order_items and shows sum(orders.shipping_fee) per day. The total is too high. Why, and what are two ways to fix it?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 17 review": your recap answers, your six predictions next to the real outputs, schema.sql with D1 to D3, joins.sql (or the commit link), your dsa.py, your quiz answers and the Day 16 catch-up status. Note anything that felt unclear; tomorrow starts there.

