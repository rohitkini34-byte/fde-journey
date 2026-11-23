-- ===== section: Concept 1: Aggregate functions: many rows in, one value out =====
-- Concept 1: count rows versus count values. pages has 8 rows.
SELECT count(*)          AS total_rows,   -- every row, NULLs or not
       count(author)     AS with_author,  -- rows where author IS NOT NULL
       count(word_count) AS counted,
       count(views)      AS with_views
FROM pages;
-- ->  total_rows | with_author | counted | with_views
-- -> ------------+-------------+---------+------------
-- ->           8 |           6 |       7 |          6
-- Like entries.filter(e => e.author != null).length in JS.
-- REMEMBER: count(*) counts rows; count(col) counts non-NULL values.

-- ===== section: Concept 1: Aggregate functions: many rows in, one value out =====
-- Concept 1: the other four aggregates, all skipping NULL views.
SELECT sum(views)           AS total_views,
       round(avg(views), 1) AS avg_views,   -- avg over the 6 known
       min(word_count)      AS shortest,
       max(word_count)      AS longest
FROM pages;
-- ->  total_views | avg_views | shortest | longest
-- -> -------------+-----------+----------+---------
-- ->         7390 |    1231.7 |      150 |    1800
-- Without round(): 1231.6666666666666667 (integer avg gives numeric)

-- Treat missing views as 0 instead: a DIFFERENT question, a different answer
SELECT round(avg(coalesce(views, 0)), 1) AS avg_null_as_zero FROM pages;
-- ->  avg_null_as_zero
-- -> ------------------
-- ->             923.8      (7390 / 8 instead of 7390 / 6)
-- coalesce() is Concept 5; here it turns each NULL into 0 before avg.

-- ===== section: Concept 1: Aggregate functions: many rows in, one value out =====
-- Concept 1: zero rows in, and mixing a plain column with an aggregate.
-- psql meta-command: show NULL as (null), not blank. No ; and no
-- comment on the same line: psql would read the comment as arguments.
\pset null '(null)'
SELECT count(*) AS n, sum(views) AS s, max(views) AS m
FROM pages
WHERE locale = 'fr-fr';   -- there are no French pages
-- ->  n |   s    |   m
-- -> ---+--------+--------
-- ->  0 | (null) | (null)
-- GOTCHA: a total of NULL on a dashboard is "no rows", not "zero".

SELECT uid, count(*) FROM pages;
-- -> ERROR:  column "pages.uid" must appear in the GROUP BY clause or be
-- ->         used in an aggregate function
-- 8 uids, 1 count: which uid should the single row show? Concept 2.

-- ===== section: Concept 2: GROUP BY: one result row per group =====
-- Concept 2: count pages per status, biggest group first.
SELECT status, count(*) AS pages
FROM pages
GROUP BY status              -- one bucket per distinct status
ORDER BY pages DESC, status; -- tie-breaker: status A to Z
-- ->   status   | pages
-- -> -----------+-------
-- ->  published |     5
-- ->  draft     |     2
-- ->  archived  |     1
-- Day 3 in Python: counts = {}; for p in pages:
--     counts[p["status"]] = counts.get(p["status"], 0) + 1

-- ===== section: Concept 2: GROUP BY: one result row per group =====
-- Concept 2: two grouping columns = one row per (locale, status) pair.
SELECT locale, status, count(*) AS pages, sum(views) AS views
FROM pages
GROUP BY locale, status
ORDER BY locale, status;
-- ->  locale |  status   | pages | views
-- -> --------+-----------+-------+--------
-- ->  en-gb  | published |     1 |     90
-- ->  en-us  | archived  |     1 |      0
-- ->  en-us  | draft     |     1 | (null)   <- its only page has NULL views
-- ->  en-us  | published |     3 |   7000
-- ->  hi-in  | draft     |     1 | (null)
-- ->  hi-in  | published |     1 |    300

-- ===== section: Concept 2: GROUP BY: one result row per group =====
-- Concept 2: the grouping rule, and NULL as its own group.
SELECT locale, uid, count(*) FROM pages GROUP BY locale;
-- -> ERROR:  column "pages.uid" must appear in the GROUP BY clause or be
-- ->         used in an aggregate function

SELECT author, count(*) AS pages
FROM pages
GROUP BY author
ORDER BY author;            -- NULLs sort LAST in ascending order
-- ->  author | pages
-- -> --------+-------
-- ->  Asha   |     2
-- ->  Meera  |     1
-- ->  Ravi   |     3
-- ->  (null) |     2      <- blt104 and blt107, both unassigned
-- FDE TIP: label that row for humans: coalesce(author, 'Unassigned').

-- ===== section: Concept 3: HAVING, and the full order of work =====
-- Concept 3: WHERE filters rows first, HAVING filters groups after.
SELECT author, count(*) AS pages
FROM pages
WHERE status = 'published'      -- 1) only live pages go into groups
GROUP BY author                 -- 2) one group per author
HAVING count(*) >= 2            -- 3) keep authors with 2+ live pages
ORDER BY pages DESC, author;
-- ->  author | pages
-- -> --------+-------
-- ->  Asha   |     2
-- ->  Ravi   |     2      (Ravi's archived FAQ never reached a group)

SELECT author, count(*) FROM pages WHERE count(*) >= 2 GROUP BY author;
-- -> ERROR:  aggregate functions are not allowed in WHERE
-- WHERE runs before any group exists, so there is nothing to count yet.

-- ===== section: Concept 3: HAVING, and the full order of work =====
-- Concept 3: an alias cannot be used in HAVING.
SELECT locale, count(*) AS n
FROM pages
GROUP BY locale
HAVING n > 1;
-- -> ERROR:  column "n" does not exist
-- Write HAVING count(*) > 1 instead. ORDER BY n would have been fine.

SELECT locale, sum(views) AS views
FROM pages
GROUP BY locale
HAVING sum(views) > 500
ORDER BY views DESC;
-- ->  locale | views
-- -> --------+-------
-- ->  en-us  |  7000   (hi-in has 300, en-gb has 90)
-- REMEMBER: WHERE picks rows before grouping; HAVING picks groups after.

-- ===== section: Concept 4: DISTINCT: unique values and unique counts =====
-- Concept 4: unique values, unique combinations, unique counts.
SELECT DISTINCT locale FROM pages ORDER BY locale;
-- ->  en-gb
-- ->  en-us
-- ->  hi-in

SELECT DISTINCT locale, status FROM pages ORDER BY locale, status;
-- -> 6 rows: every (locale, status) PAIR that exists, e.g.
-- ->  en-us | archived,  en-us | draft,  en-us | published, ...
-- DISTINCT applies to the whole selected row, not just to locale.

SELECT count(*)               AS rows,
       count(DISTINCT locale) AS locales,
       count(DISTINCT author) AS authors   -- NULL is not counted
FROM pages;
-- ->  rows | locales | authors
-- -> ------+---------+---------
-- ->     8 |       3 |       3

-- ===== section: Concept 4: DISTINCT: unique values and unique counts =====
-- Concept 4: count(DISTINCT) inside groups.
SELECT status, count(DISTINCT locale) AS locales
FROM pages
GROUP BY status
ORDER BY status;
-- ->   status   | locales
-- -> -----------+---------
-- ->  archived  |       1
-- ->  draft     |       2
-- ->  published |       3
-- GOTCHA: if a query returns duplicates you did not expect, find out why
-- before adding DISTINCT. On Day 17 a bad join creates duplicates, and
-- DISTINCT hides the bug instead of fixing it.

-- ===== section: Concept 5: NULL in depth: three-valued logic, COALESCE and NULLIF =====
-- Concept 5: how NULL behaves in comparisons and arithmetic.
SELECT NULL = NULL                   AS eq,       -- unknown, not true
       NULL IS NULL                  AS is_null,
       1 + NULL                      AS plus,     -- NULL in, NULL out
       'a' || NULL                   AS joined,   -- || joins text
       5 IS DISTINCT FROM NULL       AS differs;  -- NULL-safe <>
-- ->    eq   | is_null |  plus  | joined | differs
-- -> --------+---------+--------+--------+---------
-- ->  (null) | t       | (null) | (null) | t
-- In JS, null === null is true. In SQL, NULL = NULL is unknown.

SELECT uid FROM pages WHERE author <> 'Ravi' ORDER BY uid;
-- ->  blt101, blt105, blt106     (3 rows: the unassigned are missing)
SELECT uid FROM pages WHERE author IS DISTINCT FROM 'Ravi' ORDER BY uid;
-- ->  blt101, blt104, blt105, blt106, blt107   (5 rows)
-- REMEMBER: any comparison with NULL is unknown, and WHERE drops unknown.

-- ===== section: Concept 5: NULL in depth: three-valued logic, COALESCE and NULLIF =====
-- Concept 5: NOT IN with a NULL in the list returns nothing.
SELECT uid FROM pages WHERE locale NOT IN ('en-us', NULL);
-- -> (0 rows)   no error, no warning, just an empty result
-- GOTCHA: keep NULLs out of NOT IN lists, or test IS NULL separately.

-- ===== section: Concept 5: NULL in depth: three-valued logic, COALESCE and NULLIF =====
-- Concept 5: coalesce (like ?? in JS) and nullif.
SELECT uid,
       coalesce(author, 'Unassigned') AS author,  -- label the unknown
       coalesce(views, 0)             AS views    -- only if NULL means 0
FROM pages
ORDER BY id
LIMIT 4;
-- ->   uid   |   author   | views
-- -> --------+------------+-------
-- ->  blt101 | Asha       |  5000
-- ->  blt102 | Ravi       |  1200
-- ->  blt103 | Ravi       |   300
-- ->  blt104 | Unassigned |     0

SELECT 10 / 0;
-- -> ERROR:  division by zero
SELECT 100 / nullif(0, 0) AS safe_div;
-- ->  safe_div
-- -> ----------
-- ->    (null)       nullif turned the 0 into NULL; 100 / NULL is NULL
-- FDE TIP: rates and percentages: x / nullif(total, 0), so one empty
-- group shows NULL instead of failing the whole dashboard query.

-- ===== section: Concept 6: CASE: if/else inside a query =====
-- Concept 6: a searched CASE puts each page into a traffic bucket.
SELECT uid, views,
       CASE
           WHEN views IS NULL THEN 'no data'  -- test NULL FIRST
           WHEN views >= 1000 THEN 'high'     -- first true WHEN wins
           WHEN views >= 100  THEN 'medium'   -- so this means 100..999
           ELSE 'low'
       END AS traffic
FROM pages
ORDER BY id;
-- ->   uid   | views  | traffic
-- -> --------+--------+---------
-- ->  blt101 |   5000 | high
-- ->  blt102 |   1200 | high
-- ->  blt103 |    300 | medium
-- ->  blt104 | (null) | no data
-- ->  blt105 |    800 | medium
-- ->  blt106 | (null) | no data
-- ->  blt107 |     90 | low
-- ->  blt108 |      0 | low

-- ===== section: Concept 6: CASE: if/else inside a query =====
-- Concept 6: group by a computed label; simple CASE; the NULL trap.
SELECT CASE WHEN views IS NULL THEN 'no data'
            WHEN views >= 1000 THEN 'high'
            WHEN views >= 100  THEN 'medium'
            ELSE 'low' END AS traffic,
       count(*) AS pages
FROM pages
GROUP BY traffic            -- Postgres lets GROUP BY use the alias
ORDER BY pages DESC, traffic;
-- -> high 2, low 2, medium 2, no data 2

-- simple CASE: compare one value; no ELSE means NULL for the rest
SELECT uid, CASE status WHEN 'published' THEN 'Live'
                        WHEN 'draft'     THEN 'In progress'
            END AS label
FROM pages WHERE uid IN ('blt101', 'blt104', 'blt108') ORDER BY uid;
-- ->  blt101 | Live
-- ->  blt104 | In progress
-- ->  blt108 | (null)        archived matched nothing, no ELSE

-- ===== section: Concept 6: CASE: if/else inside a query =====
-- Concept 6: a pivot, three ways to count conditionally.
SELECT locale,
       count(*) AS total,
       count(*) FILTER (WHERE status = 'published') AS published,
       sum(CASE WHEN status = 'draft' THEN 1 ELSE 0 END) AS drafts,
       count(CASE WHEN status = 'archived' THEN 1 END) AS archived
FROM pages
GROUP BY locale
ORDER BY locale;
-- ->  locale | total | published | drafts | archived
-- -> --------+-------+-----------+--------+----------
-- ->  en-gb  |     1 |         1 |      0 |        0
-- ->  en-us  |     5 |         3 |      1 |        1
-- ->  hi-in  |     2 |         1 |      1 |        0
-- Zeros appear here (unlike GROUP BY locale, status), because every
-- locale row exists and the CASE just counts nothing.
-- REMEMBER: CASE picks the FIRST true branch; NULL needs its own WHEN.

-- ===== section: Check your understanding (predict first, then run) =====
-- Check your understanding: predict each result, then run it.
\pset null '(null)'
-- 1. Three numbers. Which is not 8, and why?
SELECT count(*), count(views), count(DISTINCT status) FROM pages;
-- 2. Why are a and b different? (7 pages have a word count.)
SELECT round(avg(word_count)) AS a,
       sum(word_count) / count(*) AS b
FROM pages;
-- 3. How many rows, and what is in the last one?
SELECT author, count(*) FROM pages
WHERE status <> 'published'
GROUP BY author ORDER BY author;
-- 4. Which locales?
SELECT locale FROM pages GROUP BY locale HAVING max(views) > 1000;
-- 5. Four rows: in which order, and why is 'none' where it is?
SELECT coalesce(author, 'none') AS a, count(*) FROM pages
GROUP BY 1 ORDER BY 2 DESC, 1;   -- 1 and 2 mean "first/second column"
-- 6. Where does blt106 (word_count NULL) end up?
SELECT CASE WHEN word_count > 500 THEN 'long' ELSE 'short' END AS len,
       count(*)
FROM pages GROUP BY len ORDER BY len;
