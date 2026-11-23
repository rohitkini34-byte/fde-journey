-- ===== section: Concept 2: PostgreSQL and psql =====
# Concept 2: make a database and open psql on it (Mac terminal).
createdb fde  # one-time: an empty database called fde
psql -d fde  # connect; the prompt shows the database name
# -> psql (18.x)
# -> Type "help" for help.
# -> fde=#
# FDE TIP: on a customer system you connect with a full connection string,
# and never type the password into the command (it lands in shell history):
# psql "host=db.acme.internal port=5432 dbname=cms user=readonly
#       sslmode=require"
# psql then asks for the password, or reads it from ~/.pgpass.

-- ===== section: Concept 2: PostgreSQL and psql =====
-- Concept 2: the psql commands you will use every day (type at fde=#).
\conninfo   -- which database, user and port am I connected to?
\l          -- list databases on this server
\dt         -- list tables in the current database
\d posts    -- describe one table: columns, types, NULL rules, defaults
\x          -- toggle expanded output: one column per line, for wide rows
\timing     -- print how long each query takes (useful on Day 19)
\i day15/schema.sql  -- run a file of SQL, like pasting it in
\?          -- help for meta-commands;  \h SELECT  shows SQL syntax help
\q          -- quit (Ctrl+D works too)

SELECT 1 + 1;  -- SQL needs the semicolon; meta-commands do not
-- ->  ?column?
-- -> ----------
-- ->         2
-- -> (1 row)
-- GOTCHA: forgot the ;? The prompt shows fde-# and waits. Type ; and Enter.

-- ===== section: Concept 3: Data types and CREATE TABLE =====
-- Concept 3: a table for blog posts in a CMS.
DROP TABLE IF EXISTS posts;  -- start clean so the file can be re-run

CREATE TABLE posts (
    -- the database numbers each row for you: 1, 2, 3 ...
    id           integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    uid          text NOT NULL,          -- like a Contentstack entry uid
    title        text NOT NULL,          -- NOT NULL: a value is required
    locale       text NOT NULL DEFAULT 'en-us',  -- used when omitted
    status       text NOT NULL DEFAULT 'draft',
    word_count   integer,                -- no NOT NULL: may be unknown
    is_featured  boolean NOT NULL DEFAULT false,
    published_at timestamptz,            -- NULL until it goes live
    created_at   timestamptz NOT NULL DEFAULT now()  -- time of INSERT
);  -- no comma after the last column
-- -> NOTICE:  table "posts" does not exist, skipping   (first run only)
-- -> DROP TABLE
-- -> CREATE TABLE

-- ===== section: Concept 3: Data types and CREATE TABLE =====
-- Concept 3: describe the table (Collation column dropped to fit).
\d posts
-- ->    Column     |           Type           | Nullable |    Default
-- -> --------------+--------------------------+----------+--------------
-- ->  id           | integer                  | not null | generated
-- ->               |                          |          | always as
-- ->               |                          |          | identity
-- ->  uid          | text                     | not null |
-- ->  title        | text                     | not null |
-- ->  locale       | text                     | not null | 'en-us'::text
-- ->  status       | text                     | not null | 'draft'::text
-- ->  word_count   | integer                  |          |
-- ->  is_featured  | boolean                  | not null | false
-- ->  published_at | timestamp with time zone |          |
-- ->  created_at   | timestamp with time zone | not null | now()
-- -> Indexes:
-- ->     "posts_pkey" PRIMARY KEY, btree (id)
-- The primary key got an index for free: lookups by id are fast (Day 19).

-- ===== section: Concept 4: INSERT, quoting and RETURNING =====
-- Concept 4: add rows. Strings use SINGLE quotes in SQL.
INSERT INTO posts (uid, title, word_count)
VALUES ('blt001', 'Welcome to our new site', 420);
-- -> INSERT 0 1   (the 1 is the number of rows; ignore the 0)

-- several rows in one statement: one round trip, all or nothing
INSERT INTO posts (uid, title, locale, status, word_count, published_at)
VALUES
    ('blt002', 'Pricing explained', 'en-us', 'published', 980,
     '2026-10-01 09:30:00+05:30'),  -- a timestamp is written as text
    ('blt003', 'Precios explicados', 'es-es', 'published', 1010,
     '2026-10-03 10:00:00+05:30'),
    -- '' inside a string is one quote; NULL is bare, never 'NULL'
    ('blt004', 'Ravi''s launch notes', 'en-us', 'draft', NULL, NULL),
    ('blt005', 'Careers at Acme', 'en-gb', 'published', 300,
     '2026-09-15 12:00:00+05:30');
-- -> INSERT 0 4

-- RETURNING hands back what the database filled in (id, defaults)
INSERT INTO posts (uid, title, is_featured)
VALUES ('blt006', 'Holiday sale', true)
RETURNING id, uid, locale, status;
-- ->  id |  uid   | locale | status
-- -> ----+--------+--------+--------
-- ->   6 | blt006 | en-us  | draft
-- -> (1 row)
-- REMEMBER: leave a column out and you get its DEFAULT (or NULL);
-- RETURNING shows you what that was.

-- ===== section: Concept 4: INSERT, quoting and RETURNING =====
-- Concept 4: three inserts the database refuses, and why.
INSERT INTO posts (id, uid, title) VALUES (99, 'x', 'y');
-- -> ERROR:  cannot insert a non-DEFAULT value into column "id"
-- -> DETAIL:  Column "id" is an identity column defined as GENERATED ALWAYS.
-- The database owns the id. Leave it out and let it count.

INSERT INTO posts (uid) VALUES ('blt007');
-- -> ERROR:  null value in column "title" of relation "posts" violates
-- ->         not-null constraint
-- NOT NULL did its job: no title, no row.

INSERT INTO posts (uid, title) VALUES ("blt008", "Oops");
-- -> ERROR:  column "blt008" does not exist
-- GOTCHA: double quotes mean a NAME (column or table) in SQL, not text.
-- In JS 'a' and "a" are the same string; in SQL only 'a' is a string.

-- ===== section: Concept 5: SELECT and WHERE =====
-- Concept 5: choose columns, compute one, filter rows.
SELECT uid, title, status FROM posts;  -- 6 rows, 3 columns
-- (output not shown: all six posts)

-- a computed column, named with AS (like a derived prop in React)
SELECT uid, word_count, word_count / 200 AS read_minutes FROM posts;
-- ->   uid   | word_count | read_minutes
-- ->  blt001 |        420 |            2   <- integer / integer drops the
-- ->  blt002 |        980 |            4      decimals, as // does in Python
-- ->  blt003 |       1010 |            5
-- ->  blt004 |            |                 <- NULL in, NULL out
-- ->  blt005 |        300 |            1
-- ->  blt006 |            |

-- WHERE keeps only the rows where the condition is TRUE
SELECT uid, title FROM posts WHERE status = 'published';
-- ->  blt002 | Pricing explained
-- ->  blt003 | Precios explicados
-- ->  blt005 | Careers at Acme
SELECT uid FROM posts WHERE status = 'Published';
-- -> (0 rows)   GOTCHA: = on text is case-sensitive

-- ===== section: Concept 5: SELECT and WHERE =====
-- Concept 5: combining conditions, and the shortcuts.
SELECT uid, locale FROM posts
WHERE status = 'published' AND locale <> 'en-us';
-- ->  blt003 | es-es
-- ->  blt005 | en-gb

-- BETWEEN includes both ends: same as >= 400 AND <= 1000
SELECT uid, word_count FROM posts WHERE word_count BETWEEN 400 AND 1000;
-- ->  blt001 |        420
-- ->  blt002 |        980

-- IN: like ['en-gb', 'es-es'].includes(locale) in JS
SELECT uid, locale FROM posts WHERE locale IN ('en-gb', 'es-es');
-- ->  blt003 | es-es
-- ->  blt005 | en-gb

-- LIKE matches a pattern: % = any characters, _ = exactly one.
-- ILIKE is the case-insensitive version (Postgres only).
SELECT uid, title FROM posts WHERE title ILIKE '%pric%';
-- ->  blt002 | Pricing explained   ("Precios" has no "pric", so no match)

-- ===== section: Concept 5: SELECT and WHERE =====
-- Concept 5: NULL, and AND/OR precedence.
SELECT uid FROM posts WHERE word_count = NULL;
-- -> (0 rows)   never true, not even for rows with no word count
SELECT uid FROM posts WHERE word_count IS NULL;
-- ->  blt004
-- ->  blt006
-- REMEMBER: test for missing values with IS NULL, never = NULL.

-- AND binds tighter than OR, like * before + in maths.
-- This reads: draft OR (featured AND Spanish)
SELECT uid FROM posts
WHERE status = 'draft' OR is_featured AND locale = 'es-es';
-- ->  blt001, blt004, blt006   (all three drafts)
-- Brackets say what you mean: (draft OR featured) AND Spanish
SELECT uid FROM posts
WHERE (status = 'draft' OR is_featured) AND locale = 'es-es';
-- -> (0 rows)

-- ===== section: Concept 6: ORDER BY, LIMIT and OFFSET =====
-- Concept 6: sorting. Most words first.
SELECT uid, word_count FROM posts ORDER BY word_count DESC;
-- ->  blt004 |              <- NULLs come FIRST with DESC in Postgres
-- ->  blt006 |                 (these two tie: their order may vary)
-- ->  blt003 |       1010
-- ->  blt002 |        980
-- ->  blt001 |        420
-- ->  blt005 |        300

SELECT uid, word_count FROM posts ORDER BY word_count DESC NULLS LAST;
-- ->  blt003 | 1010, blt002 | 980, blt001 | 420, blt005 | 300,
-- ->  then blt004 and blt006 at the end

-- two keys: status A to Z, then, within each status, most words first
SELECT uid, status, word_count FROM posts
ORDER BY status, word_count DESC NULLS LAST;
-- ->  blt001 | draft     |  420
-- ->  blt004 | draft     |
-- ->  blt006 | draft     |
-- ->  blt003 | published | 1010
-- ->  blt002 | published |  980
-- ->  blt005 | published |  300

-- ===== section: Concept 6: ORDER BY, LIMIT and OFFSET =====
-- Concept 6: LIMIT and OFFSET, i.e. pages (2 rows per page).
SELECT uid, title FROM posts ORDER BY id LIMIT 2;           -- page 1
-- ->  blt001 | Welcome to our new site
-- ->  blt002 | Pricing explained
SELECT uid, title FROM posts ORDER BY id LIMIT 2 OFFSET 2;  -- page 2
-- ->  blt003 | Precios explicados
-- ->  blt004 | Ravi's launch notes
-- OFFSET = (page - 1) * page_size. Same idea as Contentstack's
-- ?limit=2&skip=2 on the Content Delivery API.

-- "the latest published post": sort newest first, keep one
SET timezone = 'Asia/Kolkata';  -- show times in IST
SELECT uid, title, published_at FROM posts
WHERE status = 'published'
ORDER BY published_at DESC
LIMIT 1;
-- ->  blt003 | Precios explicados | 2026-10-03 10:00:00+05:30
-- REMEMBER: no ORDER BY, no order. LIMIT without ORDER BY is a random
-- sample, not "the first rows".

-- ===== section: Concept 6: ORDER BY, LIMIT and OFFSET =====
-- Concept 6: an alias works in ORDER BY but not in WHERE.
SELECT uid, title AS headline FROM posts ORDER BY headline LIMIT 3;
-- ->  blt005 | Careers at Acme
-- ->  blt006 | Holiday sale
-- ->  blt003 | Precios explicados
SELECT uid, title AS headline FROM posts WHERE headline LIKE 'P%';
-- -> ERROR:  column "headline" does not exist
-- WHERE ran before SELECT made the alias. Write WHERE title LIKE 'P%'.

-- ===== section: Check your understanding (predict first, then run) =====
-- Check your understanding: predict each result, then run it.
-- 1. Which rows, and why not the others?
SELECT uid FROM posts WHERE status = 'draft' AND word_count > 400;

-- 2. Which two uids, in which order?
SELECT uid FROM posts WHERE NOT is_featured ORDER BY id DESC LIMIT 2;

-- 3. What are a and b? (Look at Concept 5's read_minutes.)
SELECT 'It''s' AS txt, 7 / 2 AS a, 7 / 2.0 AS b;

-- 4. Which rows, and in which order?
SELECT uid, title FROM posts WHERE title ILIKE 'p%' ORDER BY title;

-- 5. Which id does the last INSERT return?
DROP TABLE IF EXISTS t;
CREATE TABLE t (
    id   integer GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name text NOT NULL
);
INSERT INTO t (name) VALUES ('a');
INSERT INTO t (name) VALUES (NULL);
INSERT INTO t (name) VALUES ('b') RETURNING id;

-- 6. How many rows? Rewrite it with brackets so it means what it says.
SELECT uid FROM posts
WHERE locale = 'en-us' OR locale = 'en-gb' AND status = 'published'
ORDER BY id;
