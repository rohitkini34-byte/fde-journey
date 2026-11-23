-- ===== section: Concept 1: Constraints, rules the database enforces =====
-- Concept 1: each kind of rule, broken once. Run setup.sql first, then
-- paste these into psql one at a time.

-- NOT NULL: a title is required.
INSERT INTO lesson_entries (uid, title) VALUES ('blt104', NULL);
-- -> ERROR:  null value in column "title" of relation "lesson_entries"
-- ->         violates not-null constraint

-- UNIQUE: no two entries may share a slug (the URL part).
INSERT INTO lesson_entries (uid, title, slug)
VALUES ('blt105', 'Gift cards', 'returns');
-- -> ERROR:  duplicate key value violates unique constraint
-- ->         "lesson_entries_slug_key"
-- -> DETAIL:  Key (slug)=(returns) already exists.

-- CHECK: status must be one of three words. Like an enum field in a CMS.
INSERT INTO lesson_entries (uid, title, status)
VALUES ('blt106', 'FAQ', 'live');
-- -> ERROR:  new row for relation "lesson_entries" violates check
-- ->         constraint "lesson_entries_status_check"

-- CHECK on a number: no negative word counts.
INSERT INTO lesson_entries (uid, title, word_count)
VALUES ('blt107', 'FAQ', -5);
-- -> ERROR:  ... violates check constraint
-- ->         "lesson_entries_word_count_check"

-- DEFAULT fills what you leave out; the row passes every rule.
INSERT INTO lesson_entries (uid, title) VALUES ('blt108', 'FAQ');
SELECT uid, status, word_count, slug FROM lesson_entries
WHERE uid = 'blt108';
-- ->   uid   | status | word_count | slug
-- ->  blt108 | draft  |            |
-- GOTCHA: word_count is NULL and the CHECK still passed. A CHECK only
-- rejects FALSE; NULL >= 0 is unknown, so it is let through. Add
-- NOT NULL as well when "missing" must also be refused.

-- ===== section: Concept 1: Constraints, rules the database enforces =====
-- Concept 1: adding a rule to a table that already holds data.
-- The customer now wants a word count on every entry.
ALTER TABLE lesson_entries ALTER COLUMN word_count SET NOT NULL;
-- -> ERROR:  column "word_count" of relation "lesson_entries"
-- ->         contains null values

-- Step 1: find the rows that break the rule BEFORE you add it.
SELECT uid, title FROM lesson_entries WHERE word_count IS NULL;
-- ->   uid   |       title
-- ->  blt103 | Draft: size chart

-- Step 2: agree the fix with the customer (here: unknown becomes 0).
UPDATE lesson_entries SET word_count = 0 WHERE word_count IS NULL;
-- -> UPDATE 1

-- Step 3: now the rule goes on, and protects every future row.
ALTER TABLE lesson_entries ALTER COLUMN word_count SET NOT NULL;
-- -> ALTER TABLE

-- A CHECK can use functions: slugs must be lowercase.
ALTER TABLE lesson_entries ADD CONSTRAINT lesson_entries_slug_lower
    CHECK (slug = lower(slug));
-- -> ALTER TABLE

-- \d shows the columns, the rules, and the indexes behind them:
\d lesson_entries
-- -> Indexes:
-- ->     "lesson_entries_pkey" PRIMARY KEY, btree (uid)
-- ->     "lesson_entries_slug_key" UNIQUE CONSTRAINT, btree (slug)
-- -> Check constraints:
-- ->     "lesson_entries_slug_lower" CHECK (slug = lower(slug))
-- ->     "lesson_entries_status_check" CHECK (status = ANY (...))
-- ->     "lesson_entries_word_count_check" CHECK (word_count >= 0)

-- ===== section: Concept 2: Upserts with INSERT ... ON CONFLICT =====
-- Concept 2: three ways to insert a row that may already exist.
-- Re-run setup.sql first.

-- 1. Plain INSERT: the second run of any loader dies here (Day 18).
INSERT INTO lesson_entries (uid, title) VALUES ('blt102', 'Returns');
-- -> ERROR:  duplicate key value violates unique constraint
-- ->         "lesson_entries_pkey"

-- 2. DO NOTHING: skip the row if the uid is taken.
INSERT INTO lesson_entries (uid, title) VALUES ('blt102', 'Returns')
ON CONFLICT (uid) DO NOTHING;
-- -> INSERT 0 0      (0 rows inserted, and no error)

-- 3. DO UPDATE: insert, or change the row that is already there.
--    EXCLUDED = the row you TRIED to insert. "e" = the row in the table.
INSERT INTO lesson_entries AS e (uid, title, word_count)
VALUES ('blt102', 'Returns and refunds', 520)
ON CONFLICT (uid) DO UPDATE
    SET title      = EXCLUDED.title,
        word_count = EXCLUDED.word_count,
        updated_at = now()
RETURNING e.uid, e.title, e.word_count, e.status;
-- ->   uid   |        title        | word_count |  status
-- ->  blt102 | Returns and refunds |        520 | published
-- status was not in SET, so it kept its old value: like a PATCH, not a PUT.

-- The conflict target must be a UNIQUE constraint or the primary key:
INSERT INTO lesson_entries (uid, title) VALUES ('blt109', 'FAQ')
ON CONFLICT (title) DO NOTHING;
-- -> ERROR:  there is no unique or exclusion constraint matching the
-- ->         ON CONFLICT specification

-- ===== section: Concept 3: Indexes, how a database finds rows fast =====
-- Concept 3: which queries can use the index on (entry_uid, viewed_on)?
-- Run after the previous example, so the index exists. EXPLAIN shows the
-- plan without running the query; Concept 4 reads plans properly.
-- Your cost numbers may differ slightly (statistics are sampled).

-- 1. Filter on the FIRST column of the index: the index is used.
EXPLAIN SELECT * FROM lesson_views WHERE entry_uid = 'blt0042';
-- -> Bitmap Heap Scan on lesson_views  (cost=17.06..1287.46 rows=598 ...)
-- ->   ->  Bitmap Index Scan on lesson_views_uid_day_idx

-- 2. Filter on the SECOND column only: not used. A phone book sorted by
--    surname, then first name, cannot find "every Rohit" quickly.
EXPLAIN SELECT * FROM lesson_views WHERE viewed_on = '2026-06-01';
-- -> Gather  (cost=1000.00..5166.58 rows=497 ...)
-- ->   ->  Parallel Seq Scan on lesson_views

-- 3. A function around the column hides it from the index.
EXPLAIN SELECT * FROM lesson_views WHERE lower(entry_uid) = 'blt0042';
-- -> Gather  (cost=1000.00..5708.06 rows=1500 ...)
-- ->   ->  Parallel Seq Scan on lesson_views
-- FDE TIP: if you really need lower(), index the expression itself:
-- CREATE INDEX ... ON lesson_views (lower(entry_uid));

-- ===== section: Concept 4: Reading query plans with EXPLAIN and EXPLAIN ANALYZE =====
-- Concept 4: EXPLAIN ANALYZE runs the query and reports what happened.
-- Re-run setup.sql first (no index). Plan lines are shortened here, and
-- your costs and times will differ a little: compare the shapes.
SET max_parallel_workers_per_gather = 0;  -- one process: simpler plans

EXPLAIN ANALYZE
SELECT sum(views) FROM lesson_views
WHERE entry_uid = 'blt0042' AND viewed_on >= '2026-06-01';
-- -> Aggregate  (cost=6411.21..6411.22 rows=1 width=8)
-- ->            (actual time=11.655..11.656 rows=1 loops=1)
-- ->   ->  Seq Scan on lesson_views  (cost=0.00..6411.00 rows=84 width=4)
-- ->                    (actual time=9.152..11.642 rows=84 loops=1)
-- ->         Filter: ((viewed_on >= '2026-06-01'::date)
-- ->                  AND (entry_uid = 'blt0042'::text))
-- ->         Rows Removed by Filter: 299916
-- -> Planning Time: 0.250 ms
-- -> Execution Time: 11.703 ms

CREATE INDEX lesson_views_uid_day_idx
    ON lesson_views (entry_uid, viewed_on);

EXPLAIN ANALYZE
SELECT sum(views) FROM lesson_views
WHERE entry_uid = 'blt0042' AND viewed_on >= '2026-06-01';
-- -> Aggregate  (cost=286.86..286.87 rows=1 width=8)
-- ->            (actual time=0.136..0.137 rows=1 loops=1)
-- ->   ->  Bitmap Heap Scan on lesson_views  (... rows=84 ...)
-- ->         Recheck Cond: ((entry_uid = 'blt0042'::text)
-- ->                        AND (viewed_on >= '2026-06-01'::date))
-- ->         Heap Blocks: exact=84
-- ->         ->  Bitmap Index Scan on lesson_views_uid_day_idx
-- ->               (actual time=0.040..0.040 rows=84 loops=1)
-- -> Planning Time: 0.192 ms
-- -> Execution Time: 0.167 ms

-- What did the index cost? Disk space (and work on every write).
SELECT pg_size_pretty(pg_relation_size('lesson_views')) AS table_size,
       pg_size_pretty(pg_relation_size('lesson_views_uid_day_idx'))
           AS index_size;
-- ->  table_size | index_size
-- ->  15 MB      | 9264 kB

-- ===== section: Concept 4: Reading query plans with EXPLAIN and EXPLAIN ANALYZE =====
-- Concept 4: EXPLAIN ANALYZE really runs the statement. For a DELETE or
-- UPDATE, wrap it in a transaction and roll back.
BEGIN;
EXPLAIN ANALYZE DELETE FROM lesson_views WHERE entry_uid = 'blt0042';
-- -> Delete on lesson_views  (actual time=1.181..1.182 rows=0 loops=1)
-- ->   ->  Bitmap Heap Scan on lesson_views  (... rows=600 loops=1)
-- -> Execution Time: 1.245 ms
ROLLBACK;  -- the 600 rows come back
SELECT count(*) FROM lesson_views WHERE entry_uid = 'blt0042';
-- -> 600
-- GOTCHA: without BEGIN ... ROLLBACK those 600 rows would be gone.

-- ===== section: Concept 5: Migrations, schema changes as versioned files =====
-- Concept 5: two facts about schema changes in Postgres.

-- 1. DDL (CREATE, ALTER, DROP) is transactional: a failed migration
--    can be rolled back completely. MySQL cannot do this.
BEGIN;
ALTER TABLE lesson_entries ADD COLUMN locale text NOT NULL DEFAULT 'en-us';
SELECT uid, locale FROM lesson_entries ORDER BY uid LIMIT 2;
-- ->   uid   | locale
-- ->  blt101 | en-us
-- ->  blt102 | en-us
ROLLBACK;
SELECT count(*) FROM information_schema.columns
WHERE table_name = 'lesson_entries' AND column_name = 'locale';
-- -> 0      (the column is gone again: the ALTER was rolled back)

-- 2. On a big, busy table, a normal CREATE INDEX blocks writes until it
--    finishes. CONCURRENTLY does not block, but cannot run in a
--    transaction, so a migration runner must run it on its own.
BEGIN;
CREATE INDEX CONCURRENTLY lesson_views_country_idx
    ON lesson_views (country);
-- -> ERROR:  CREATE INDEX CONCURRENTLY cannot run inside a transaction
-- ->         block
ROLLBACK;
CREATE INDEX CONCURRENTLY IF NOT EXISTS lesson_views_country_idx
    ON lesson_views (country);
-- -> CREATE INDEX
-- IF NOT EXISTS makes the file safe to run twice; run it again:
-- -> NOTICE:  relation "lesson_views_country_idx" already exists, skipping

-- ===== section: Hands-on task (about 2 hours): day19/upsert_loader.py =====
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
