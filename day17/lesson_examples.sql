-- ===== section: Concept 1: Normalisation: why one big table breaks =====
-- Concept 1: the flat export repeats facts and hides lists in text.
\pset null '(null)'
SELECT uid, writer_name, writer_email, topics
FROM articles_flat
ORDER BY uid;
-- ->   uid   | writer_name |  writer_email  |    topics
-- -> --------+-------------+----------------+--------------
-- ->  blt201 | Asha        | asha@acme.in   | festive,sale
-- ->  blt202 | Ravi        | ravi@acme.in   | help
-- ->  blt203 | Ravi        | ravi.k@acme.in | help
-- ->  blt204 | Asha        | asha@acme.in   | sale
-- ->  blt205 | (null)      | (null)         | (null)
-- ->  blt206 | Meera       | meera@acme.in  | help
-- GOTCHA: Ravi has two emails. Which one is right? The table cannot say.

-- ===== section: Concept 1: Normalisation: why one big table breaks =====
-- Concept 1: searching a comma list is a text search, and text search lies.
SELECT uid, title FROM articles_flat WHERE topics LIKE '%sale%' ORDER BY uid;
-- ->   uid   |       title
-- -> --------+-------------------
-- ->  blt201 | Diwali gift guide
-- ->  blt204 | Monsoon sale
-- Correct today. Add a topic called 'presale' and it matches too.
-- No index can help either: '%...' at the start forces a full scan.
-- REMEMBER: one value per cell. A list in a cell is a missing table.

-- ===== section: Concept 2: Primary keys and foreign keys =====
-- Concept 2: the keys in setup.sql (shortened). Parents first.
CREATE TABLE writers (
    id    integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name  text NOT NULL,
    email text NOT NULL UNIQUE        -- stored once, so it cannot disagree
);

CREATE TABLE articles (
    id        integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uid       text NOT NULL UNIQUE,   -- the CMS id, kept for syncing
    title     text NOT NULL,
    status    text NOT NULL,
    -- FK: must match a writers.id, or be NULL (= unassigned)
    writer_id integer REFERENCES writers (id)
);
-- FDE TIP: keep the source system's id (uid) as its own UNIQUE column.
-- Your own id is for joins; the uid is how the next sync finds the row.

-- ===== section: Concept 2: Primary keys and foreign keys =====
-- Concept 2: a foreign key blocks orphans in both directions.
INSERT INTO articles (uid, title, status, writer_id)
VALUES ('blt299', 'Test', 'draft', 99);
-- -> ERROR:  insert or update on table "articles" violates foreign key
-- ->         constraint "articles_writer_id_fkey"
-- -> DETAIL:  Key (writer_id)=(99) is not present in table "writers".

DELETE FROM writers WHERE id = 3;     -- Meera still has the Size chart
-- -> ERROR:  update or delete on table "writers" violates foreign key
-- ->         constraint "articles_writer_id_fkey" on table "articles"
-- -> DETAIL:  Key (id)=(3) is still referenced from table "articles".
-- REMEMBER: the FK lives on the "many" side and points at the "one" side.

-- ===== section: Concept 2: Primary keys and foreign keys =====
-- Concept 2: CASCADE removes the link rows along with their article.
-- BEGIN ... ROLLBACK runs a change and then undoes it (Day 18 covers it).
BEGIN;
DELETE FROM articles WHERE uid = 'blt201';  -- the Diwali gift guide
SELECT count(*) AS links_left FROM article_topics;
-- ->  links_left
-- -> ------------
-- ->           4     (was 6: its festive and sale links went with it)
ROLLBACK;
SELECT count(*) AS links_back FROM article_topics;
-- ->  links_back
-- -> ------------
-- ->           6
-- GOTCHA: CASCADE on the wrong FK (writers -> articles) would let one
-- DELETE of a writer wipe out all their published pages.

-- ===== section: Concept 3: One-to-many and INNER JOIN =====
-- Concept 3: each article next to its writer's name.
SELECT a.uid, a.title, w.name AS writer   -- a and w are table aliases
FROM articles AS a
JOIN writers  AS w ON w.id = a.writer_id  -- JOIN means INNER JOIN
ORDER BY a.uid;
-- ->   uid   |       title       | writer
-- -> --------+-------------------+--------
-- ->  blt201 | Diwali gift guide | Asha
-- ->  blt202 | Return policy     | Ravi
-- ->  blt203 | Store locator     | Ravi
-- ->  blt204 | Monsoon sale      | Asha
-- ->  blt206 | Size chart        | Meera
-- 5 rows, but articles has 6. blt205 (Careers) has writer_id NULL, and
-- NULL = anything is unknown, so it has no partner and is dropped.
-- Kiran has no articles, so she never appears either.

-- ===== section: Concept 3: One-to-many and INNER JOIN =====
-- Concept 3: unqualified names fail when both tables have the column.
SELECT uid, title, name
FROM articles JOIN writers ON writers.id = articles.writer_id
WHERE id = 1;
-- -> ERROR:  column reference "id" is ambiguous
-- Fix: WHERE articles.id = 1 (or use aliases: a.id = 1).

-- Filtering on the joined table: Ravi's articles, by name not by id.
SELECT a.uid, a.title
FROM articles AS a
JOIN writers  AS w ON w.id = a.writer_id
WHERE w.name = 'Ravi'
ORDER BY a.uid;
-- ->   uid   |     title
-- -> --------+---------------
-- ->  blt202 | Return policy
-- ->  blt203 | Store locator

-- ===== section: Concept 4: LEFT JOIN: keep every row, find what is missing =====
-- Concept 4: every article, with or without a writer.
\pset null '(null)'
SELECT a.uid, a.title, w.name AS writer
FROM articles AS a
LEFT JOIN writers AS w ON w.id = a.writer_id
ORDER BY a.uid;
-- ->   uid   |       title       | writer
-- -> --------+-------------------+--------
-- ->  blt201 | Diwali gift guide | Asha
-- ->  blt202 | Return policy     | Ravi
-- ->  blt203 | Store locator     | Ravi
-- ->  blt204 | Monsoon sale      | Asha
-- ->  blt205 | Careers           | (null)   <- kept, writer columns NULL
-- ->  blt206 | Size chart        | Meera
-- FDE TIP: show it as coalesce(w.name, 'Unassigned') for humans (Day 16).

-- ===== section: Concept 4: LEFT JOIN: keep every row, find what is missing =====
-- Concept 4: articles per writer, zeros included.
SELECT w.name,
       count(a.id) AS articles,    -- counts real partners only
       count(*)    AS rows_seen    -- counts result rows, NULL-filled too
FROM writers AS w
LEFT JOIN articles AS a ON a.writer_id = w.id
GROUP BY w.id, w.name              -- group by the key, not just the name
ORDER BY articles DESC, w.name;
-- ->  name  | articles | rows_seen
-- -> -------+----------+-----------
-- ->  Asha  |        2 |         2
-- ->  Ravi  |        2 |         2
-- ->  Meera |        1 |         1
-- ->  Kiran |        0 |         1     <- count(*) would report 1 article

-- The anti-join: keep only the rows that found NO partner.
SELECT w.name
FROM writers AS w
LEFT JOIN articles AS a ON a.writer_id = w.id
WHERE a.id IS NULL;                -- NULL here means "no match"
-- ->  name
-- -> -------
-- ->  Kiran
-- REMEMBER: LEFT JOIN + WHERE right.id IS NULL finds what is missing.

-- ===== section: Concept 4: LEFT JOIN: keep every row, find what is missing =====
-- Concept 4: the same filter in WHERE versus in ON.
SELECT w.name, a.uid
FROM writers AS w
LEFT JOIN articles AS a ON a.writer_id = w.id
WHERE a.status = 'published'       -- runs AFTER the join
ORDER BY w.name, a.uid;
-- ->  Asha | blt201,  Asha | blt204,  Meera | blt206,  Ravi | blt202
-- -> (4 rows)   Kiran is gone: it behaves like an INNER JOIN now

SELECT w.name, a.uid
FROM writers AS w
LEFT JOIN articles AS a
       ON a.writer_id = w.id
      AND a.status = 'published'   -- part of the match rule
ORDER BY w.name, a.uid;
-- ->  Asha | blt201,  Asha | blt204,  Kiran | (null),
-- ->  Meera | blt206,  Ravi | blt202
-- -> (5 rows)   every writer kept; only published articles attached
-- GOTCHA: right-table filters go in ON when you need the zeros.

-- ===== section: Concept 5: Many-to-many: junction tables and the fan-out trap =====
-- Concept 5: the junction table from setup.sql.
CREATE TABLE article_topics (
    article_id integer REFERENCES articles (id) ON DELETE CASCADE,
    topic_id   integer REFERENCES topics (id)   ON DELETE CASCADE,
    PRIMARY KEY (article_id, topic_id)    -- each pair at most once
);

-- Two joins: article -> link rows -> topic. One result row per link.
SELECT a.title, t.name AS topic
FROM articles       AS a
JOIN article_topics AS at ON at.article_id = a.id
JOIN topics         AS t  ON t.id = at.topic_id
ORDER BY a.title, t.name;
-- ->        title       |  topic
-- -> -------------------+---------
-- ->  Diwali gift guide | festive
-- ->  Diwali gift guide | sale
-- ->  Monsoon sale      | sale
-- ->  Return policy     | help
-- ->  Size chart        | help
-- ->  Store locator     | help
-- Careers has no topics, so the inner joins drop it.

-- ===== section: Concept 5: Many-to-many: junction tables and the fan-out trap =====
-- Concept 5: topics as one string per article, and topic usage.
\pset null '(null)'
SELECT a.title,
       string_agg(t.name, ', ' ORDER BY t.name) AS topics
FROM articles AS a
LEFT JOIN article_topics AS at ON at.article_id = a.id
LEFT JOIN topics         AS t  ON t.id = at.topic_id
GROUP BY a.id, a.title
ORDER BY a.title;
-- ->        title       |    topics
-- -> -------------------+---------------
-- ->  Careers           | (null)        <- no links: string_agg of nothing
-- ->  Diwali gift guide | festive, sale
-- ->  Monsoon sale      | sale
-- ->  Return policy     | help
-- ->  Size chart        | help
-- ->  Store locator     | help

SELECT t.name, count(at.article_id) AS articles
FROM topics AS t
LEFT JOIN article_topics AS at ON at.topic_id = t.id
GROUP BY t.id, t.name
ORDER BY articles DESC, t.name;
-- ->   name   | articles
-- -> ---------+----------
-- ->  help    |        3
-- ->  sale    |        2
-- ->  festive |        1
-- ->  brand   |        0     <- unused topic, kept by the LEFT JOIN

-- ===== section: Concept 5: Many-to-many: junction tables and the fan-out trap =====
-- Concept 5: joining through topics multiplies the writer's rows.
SELECT w.name, count(*) AS articles_wrong
FROM writers        AS w
JOIN articles       AS a  ON a.writer_id = w.id
JOIN article_topics AS at ON at.article_id = a.id
GROUP BY w.name
ORDER BY w.name;
-- ->  name  | articles_wrong
-- -> -------+----------------
-- ->  Asha  |              3     <- she has 2 articles
-- ->  Meera |              1
-- ->  Ravi  |              2

-- Fix 1: count each article once.
SELECT w.name, count(DISTINCT a.id) AS articles
FROM writers        AS w
JOIN articles       AS a  ON a.writer_id = w.id
JOIN article_topics AS at ON at.article_id = a.id
GROUP BY w.name
ORDER BY w.name;
-- ->  Asha 2,  Meera 1,  Ravi 2
-- Fix 2 (better): do not join tables the question does not need.
-- GOTCHA: count(DISTINCT) fixes counts, but sum(DISTINCT views) would
-- also merge two different articles that happen to have equal views.

-- ===== section: Concept 6: Modelling a headless CMS: locales and finding the gaps =====
-- Concept 6: every (article, language) pair that SHOULD exist.
SELECT count(*) AS pairs FROM articles CROSS JOIN languages;
-- ->  pairs
-- -> -------
-- ->     12      (6 articles x 2 languages, no ON condition)

-- Keep the pairs with no translation: the translation backlog.
SELECT a.uid, l.code AS missing
FROM articles  AS a
CROSS JOIN languages AS l
LEFT JOIN article_translations AS tr
       ON tr.article_id = a.id
      AND tr.lang_code  = l.code      -- match on BOTH key columns
WHERE tr.article_id IS NULL
ORDER BY a.uid, l.code;
-- ->   uid   | missing
-- -> --------+---------
-- ->  blt203 | hi-in
-- ->  blt204 | hi-in
-- ->  blt205 | hi-in
-- GOTCHA: CROSS JOIN on big tables explodes (10,000 x 10,000 = 100M rows).
-- It is safe here because one side is a short list of locales.

-- ===== section: Concept 6: Modelling a headless CMS: locales and finding the gaps =====
-- Concept 6: the same gap for Hindi, written with NOT EXISTS.
SELECT a.uid
FROM articles AS a
WHERE NOT EXISTS (
    SELECT 1                           -- the value does not matter
    FROM article_translations AS tr
    WHERE tr.article_id = a.id         -- linked to the outer row
      AND tr.lang_code  = 'hi-in'
)
ORDER BY a.uid;
-- ->  blt203, blt204, blt205    (3 rows, the same answer)

-- The composite key refuses a second English version of article 1.
INSERT INTO article_translations VALUES (1, 'en-us', 'Duplicate');
-- -> ERROR:  duplicate key value violates unique constraint
-- ->         "article_translations_pkey"
-- -> DETAIL:  Key (article_id, lang_code)=(1, en-us) already exists.

-- ===== section: Check your understanding (predict first, then run) =====
-- Check your understanding: predict each result, then run it.
\pset null '(null)'
-- 1. How many rows?
SELECT a.uid, w.name FROM articles a JOIN writers w ON w.id = a.writer_id;
-- 2. How many rows, and which writer appears with a NULL?
SELECT w.name, a.uid FROM writers w LEFT JOIN articles a
    ON a.writer_id = w.id;
-- 3. What number comes back?
SELECT count(*) FROM writers CROSS JOIN topics;
-- 4. Which topic names, and why not 'brand'?
SELECT DISTINCT t.name FROM topics t
JOIN article_topics at ON at.topic_id = t.id ORDER BY t.name;
-- 5. Two numbers. Why are they different?
SELECT count(*), count(DISTINCT a.id)
FROM articles a JOIN article_topics at ON at.article_id = a.id;
-- 6. How many rows? (Hint: where is the status condition?)
SELECT w.name, count(a.id) FROM writers w
LEFT JOIN articles a ON a.writer_id = w.id
WHERE a.status = 'draft' GROUP BY w.id, w.name;
