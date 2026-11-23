-- ===== section: Concept 1: CTEs, queries written as named steps =====
-- Concept 1: the same question as nested subqueries, then as CTEs.
-- Question: which entries had more total views than the average entry?
-- 1. Nested subqueries: you have to read from the inside out.
SELECT uid, total
FROM (SELECT uid, sum(views) AS total FROM lesson_views GROUP BY uid) t
WHERE total > (SELECT avg(total) FROM
              (SELECT sum(views) AS total FROM lesson_views GROUP BY uid) a)
ORDER BY total DESC;
-- ->   uid   | total
-- ->  blt101 |   935
-- 2. With CTEs: read top to bottom, one named step at a time.
WITH totals AS (                    -- step 1: views per entry
    SELECT uid, sum(views) AS total
    FROM lesson_views
    GROUP BY uid
),
average AS (                        -- step 2: one number, the average
    SELECT avg(total) AS avg_total FROM totals   -- reuses step 1
)
SELECT t.uid, t.total, round(a.avg_total, 1) AS avg_total
FROM totals t
CROSS JOIN average a    -- average has 1 row, so this adds 1 column
WHERE t.total > a.avg_total
ORDER BY t.total DESC;
-- ->   uid   | total | avg_total
-- ->  blt101 |   935 |     409.3
-- Same answer. Notice the subquery version had to compute the totals
-- twice; the CTE version names them once and uses them twice.

-- ===== section: Concept 1: CTEs, queries written as named steps =====
-- Concept 1: a CTE disappears when its statement ends.
WITH totals AS (
    SELECT uid, sum(views) AS total FROM lesson_views GROUP BY uid
)
SELECT count(*) FROM totals;
-- -> 4
SELECT count(*) FROM totals;          -- a NEW statement: totals is gone
-- -> ERROR:  relation "totals" does not exist
-- FDE TIP: if many queries need the same step, make it a VIEW
-- (CREATE VIEW latest_versions AS ...). A view is a saved query.

-- ===== section: Concept 1: CTEs, queries written as named steps =====
-- Concept 1: a recursive CTE builds the full URL path of every page.
WITH RECURSIVE tree AS (
    -- Anchor: the starting rows (pages with no parent, here only home).
    SELECT id, slug, '/' || slug AS path, 0 AS depth
    FROM lesson_pages
    WHERE parent_id IS NULL
    UNION ALL
    -- Step: children of the rows found so far. || joins text,
    -- like + on strings in JS.
    SELECT p.id, p.slug, t.path || '/' || p.slug, t.depth + 1
    FROM lesson_pages p
    JOIN tree t ON p.parent_id = t.id
)
SELECT id, depth, path FROM tree ORDER BY path;
-- ->  id | depth |              path
-- ->   1 |     0 | /home
-- ->   2 |     1 | /home/men
-- ->   3 |     1 | /home/women
-- ->   4 |     2 | /home/women/ethnic-wear
-- ->   5 |     3 | /home/women/ethnic-wear/sarees
-- REMEMBER: anchor UNION ALL step; the step joins the table to the CTE.
-- GOTCHA: if the data has a loop (page 4's parent is 5, 5's is 4), this
-- runs forever. Add WHERE t.depth < 20 in the step as a safety limit.

-- ===== section: Concept 2: Window functions, calculations across rows without losing them =====
-- Concept 2: GROUP BY collapses rows; a window function keeps every row.
-- 1. GROUP BY: one row per entry, the daily detail is gone.
SELECT uid, sum(views) AS total
FROM lesson_views
WHERE uid IN ('blt102', 'blt103')
GROUP BY uid
ORDER BY uid;
-- ->   uid   | total
-- ->  blt102 |   222
-- ->  blt103 |    95
-- 2. Window: every daily row stays, and also sees its entry's total.
SELECT uid, day, views,
       sum(views) OVER (PARTITION BY uid) AS entry_total,
       round(100.0 * views / sum(views) OVER (PARTITION BY uid), 1)
           AS pct_of_entry
FROM lesson_views
WHERE uid IN ('blt102', 'blt103')
ORDER BY uid, day;
-- ->   uid   |    day     | views | entry_total | pct_of_entry
-- ->  blt102 | 2026-11-01 |    40 |         222 |         18.0
-- ->  blt102 | 2026-11-02 |    45 |         222 |         20.3
-- ->  blt102 | 2026-11-03 |    38 |         222 |         17.1
-- ->  blt102 | 2026-11-04 |    52 |         222 |         23.4
-- ->  blt102 | 2026-11-05 |    47 |         222 |         21.2
-- ->  blt103 | 2026-11-03 |    10 |          95 |         10.5
-- ->  blt103 | 2026-11-04 |    25 |          95 |         26.3
-- ->  blt103 | 2026-11-05 |    60 |          95 |         63.2
-- 8 rows in, 8 rows out. 100.0 (not 100) makes the division decimal.

-- ===== section: Concept 2: Window functions, calculations across rows without losing them =====
-- Concept 2: three ranking functions on the same order, with a tie.
SELECT uid, day, views,
       row_number() OVER (ORDER BY views DESC) AS row_num,
       rank()       OVER (ORDER BY views DESC) AS rnk,
       dense_rank() OVER (ORDER BY views DESC) AS dense
FROM lesson_views
ORDER BY views DESC
LIMIT 5;
-- ->   uid   |    day     | views | row_num | rnk | dense
-- ->  blt101 | 2026-11-02 |   340 |       1 |   1 |     1
-- ->  blt104 | 2026-11-01 |   310 |       2 |   2 |     2
-- ->  blt101 | 2026-11-03 |   310 |       3 |   2 |     2
-- ->  blt101 | 2026-11-01 |   120 |       4 |   4 |     3
-- ->  blt101 | 2026-11-04 |    90 |       5 |   5 |     4
-- GOTCHA: the two 310 rows may swap row_num 2 and 3 on your machine.
-- row_number() picks any order among ties unless you add a tiebreaker:
-- OVER (ORDER BY views DESC, uid) is the same on every run.

-- ===== section: Concept 2: Window functions, calculations across rows without losing them =====
-- Concept 2: top 2 days per entry. PARTITION BY restarts the numbering.
WITH ranked AS (
    SELECT uid, day, views,
           row_number() OVER (PARTITION BY uid
                              ORDER BY views DESC, day) AS rn
    FROM lesson_views
)
SELECT uid, day, views, rn
FROM ranked
WHERE rn <= 2          -- filter OUTSIDE the CTE that computed rn
ORDER BY uid, rn;
-- ->   uid   |    day     | views | rn
-- ->  blt101 | 2026-11-02 |   340 |  1
-- ->  blt101 | 2026-11-03 |   310 |  2
-- ->  blt102 | 2026-11-04 |    52 |  1
-- ->  blt102 | 2026-11-05 |    47 |  2
-- ->  blt103 | 2026-11-05 |    60 |  1
-- ->  blt103 | 2026-11-04 |    25 |  2
-- ->  blt104 | 2026-11-01 |   310 |  1
-- ->  blt104 | 2026-11-05 |    22 |  2
-- The same filter written directly in WHERE fails:
-- -> ERROR:  window functions are not allowed in WHERE
-- REMEMBER: compute the window in a CTE, filter on it outside.

-- ===== section: Concept 3: Latest per group, LAG and running totals =====
-- Concept 3: the latest version of every entry, two ways.
-- 1. Standard SQL: number versions newest first, keep number 1.
WITH numbered AS (
    SELECT uid, version, title, status,
           row_number() OVER (PARTITION BY uid
                              ORDER BY version DESC) AS rn
    FROM lesson_versions
)
SELECT uid, version, title, status
FROM numbered
WHERE rn = 1
ORDER BY uid;
-- ->   uid   | version |        title         |  status
-- ->  blt101 |       3 | Diwali mega sale     | published
-- ->  blt102 |       1 | Returns policy       | published
-- ->  blt103 |       2 | Winter lookbook 2026 | draft
-- ->  blt104 |       1 | Store locator        | published
-- 2. Postgres only: DISTINCT ON keeps the FIRST row of each uid group,
-- in the ORDER BY order. The ORDER BY must start with the same column.
SELECT DISTINCT ON (uid) uid, version, title, status
FROM lesson_versions
ORDER BY uid, version DESC;
-- -> (the same 4 rows)
-- REMEMBER: latest per group = row_number() ... ORDER BY x DESC, rn = 1.

-- ===== section: Concept 3: Latest per group, LAG and running totals =====
-- Concept 3: day-over-day change, running total and 3-day average.
SELECT uid, day, views,
       lag(views) OVER w                      AS prev_day,
       views - lag(views) OVER w              AS change,
       sum(views) OVER (w ROWS BETWEEN UNBOUNDED PRECEDING
                          AND CURRENT ROW)    AS running_total,
       round(avg(views) OVER (w ROWS BETWEEN 2 PRECEDING
                                AND CURRENT ROW), 1) AS avg_3day
FROM lesson_views
WHERE uid = 'blt101'
WINDOW w AS (PARTITION BY uid ORDER BY day)   -- name the window once
ORDER BY day;
-- -> day        | views | prev_day | change | running_total | avg_3day
-- -> 2026-11-01 |   120 |          |        |           120 |    120.0
-- -> 2026-11-02 |   340 |      120 |    220 |           460 |    230.0
-- -> 2026-11-03 |   310 |      340 |    -30 |           770 |    256.7
-- -> 2026-11-04 |    90 |      310 |   -220 |           860 |    246.7
-- -> 2026-11-05 |    75 |       90 |    -15 |           935 |    158.3
-- (uid column dropped here to fit the page; it is blt101 on every row)
-- The first day has no previous row, so lag() is NULL and so is change.
-- avg_3day on day 1 and 2 averages the 1 or 2 rows that exist.

-- ===== section: Concept 3: Latest per group, LAG and running totals =====
-- Concept 3: the default frame trap with last_value().
SELECT day, views,
       last_value(views) OVER (ORDER BY day)  AS last_default,
       last_value(views) OVER (ORDER BY day
           ROWS BETWEEN UNBOUNDED PRECEDING
                AND UNBOUNDED FOLLOWING)      AS last_whole
FROM lesson_views
WHERE uid = 'blt103'
ORDER BY day;
-- ->     day     | views | last_default | last_whole
-- ->  2026-11-03 |    10 |           10 |         60
-- ->  2026-11-04 |    25 |           25 |         60
-- ->  2026-11-05 |    60 |           60 |         60
-- The default frame ends at the CURRENT row, so the "last" value it sees
-- is the row itself. GOTCHA: for "the final value", give the whole frame,
-- or use first_value() with ORDER BY day DESC.

-- ===== section: Concept 4: JSONB, searching inside flexible CMS fields =====
-- Concept 4: reading values out of a JSONB column.
SELECT uid,
       fields -> 'seo' ->> 'meta_title' AS meta_title,  -- text
       fields #>> '{seo,noindex}'       AS noindex,     -- path, as text
       (fields ->> 'discount')::int     AS discount     -- text to integer
FROM lesson_entries
ORDER BY uid;
-- ->   uid   | meta_title  | noindex | discount
-- ->  blt101 | Diwali Sale | false   |       40
-- ->  blt102 | Returns     | true    |
-- ->  blt103 | Winter      |         |       15
-- ->  blt104 |             |         |
-- Missing keys give NULL, never an error (like ?. in JavaScript).
SELECT fields -> 'seo' AS seo FROM lesson_entries WHERE uid = 'blt101';
-- ->  {"noindex": false, "meta_title": "Diwali Sale"}
-- The keys came back in a different order than they were inserted:
-- JSONB stores parsed data, not your original text.

-- ===== section: Concept 4: JSONB, searching inside flexible CMS fields =====
-- Concept 4: filtering on JSONB.
-- 1. Entries whose tags array includes "festive".
SELECT uid FROM lesson_entries
WHERE fields -> 'tags' ? 'festive'
ORDER BY uid;
-- -> blt101, blt103
-- 2. The same with containment: "fields contains this JSON".
SELECT uid FROM lesson_entries
WHERE fields @> '{"tags": ["festive"]}'
ORDER BY uid;
-- -> blt101, blt103
-- 3. Pages hidden from search engines (nested containment).
SELECT uid FROM lesson_entries
WHERE fields @> '{"seo": {"noindex": true}}';
-- -> blt102
-- 4. Entries with no seo block at all: ? on the top level.
SELECT uid FROM lesson_entries WHERE NOT fields ? 'seo';
-- -> blt104
-- 5. Numbers need a cast, because ->> always returns text.
SELECT uid FROM lesson_entries
WHERE (fields ->> 'discount')::int >= 20;
-- -> blt101

-- ===== section: Concept 4: JSONB, searching inside flexible CMS fields =====
-- Concept 4: one row per tag, then count like any other column.
SELECT tag, count(*) AS entries
FROM lesson_entries,
     jsonb_array_elements_text(fields -> 'tags') AS tag
GROUP BY tag
ORDER BY entries DESC, tag;
-- ->    tag   | entries
-- ->  festive |       2
-- ->  diwali  |       1
-- ->  help    |       1
-- ->  sale    |       1
-- ->  winter  |       1
-- blt104 has an empty tags array, so it produces no rows at all.

-- ===== section: Concept 4: JSONB, searching inside flexible CMS fields =====
-- Concept 4: a GIN index makes @> fast. Builds 100,000 rows (a few sec).
DROP TABLE IF EXISTS lesson_big;
CREATE TABLE lesson_big AS
SELECT 'blt' || g AS uid,
       jsonb_build_object(
           'tags', CASE WHEN g % 100 = 0 THEN '["festive"]'::jsonb
                        ELSE '["evergreen"]'::jsonb END,
           'n', g) AS fields
FROM generate_series(1, 100000) AS g;      -- 1 row in 100 is festive
ANALYZE lesson_big;
SET max_parallel_workers_per_gather = 0;   -- one process: simpler plans
EXPLAIN ANALYZE SELECT count(*) FROM lesson_big
WHERE fields @> '{"tags": ["festive"]}';
-- ->  Seq Scan on lesson_big (actual time=0.037..32.372 rows=1000)
-- ->    Rows Removed by Filter: 99000
-- ->  Execution Time: 32.626 ms
CREATE INDEX lesson_big_fields_gin ON lesson_big USING gin (fields);
EXPLAIN ANALYZE SELECT count(*) FROM lesson_big
WHERE fields @> '{"tags": ["festive"]}';
-- ->  Bitmap Heap Scan on lesson_big (actual time=1.205..2.247 rows=1000)
-- ->    ->  Bitmap Index Scan on lesson_big_fields_gin
-- ->  Execution Time: 2.352 ms
-- About 14 times faster here. Plan lines shortened; your times differ.
-- GOTCHA: this index helps @>, ? and similar operators. It does NOT help
-- (fields ->> 'discount')::int >= 20; that needs an expression index.

-- ===== section: Check your understanding (predict first, then run) =====
-- Predict, then run. Re-run setup.sql before you start.
-- 1: three ranking functions on 50, 50, 40. Fill in rn, rk and dr.
SELECT v, row_number() OVER (ORDER BY v DESC) AS rn,
       rank()       OVER (ORDER BY v DESC) AS rk,
       dense_rank() OVER (ORDER BY v DESC) AS dr
FROM (VALUES (50), (50), (40)) AS t(v);
-- 2: a running total ordered by day only. Two entries share each day.
-- What is in the running column on each of the 4 rows?
SELECT uid, day, views,
       sum(views) OVER (ORDER BY day) AS running
FROM lesson_views
WHERE uid IN ('blt102', 'blt103') AND day >= '2026-11-04'
ORDER BY day, uid;
-- 3: discount is 40 for blt101 and 15 for blt103. Which rows come back?
SELECT uid FROM lesson_entries
WHERE fields ->> 'discount' > '5'
ORDER BY uid;
-- 4: two entries have "festive" in their tags. What does this count?
SELECT count(*) FROM lesson_entries WHERE fields ? 'festive';
