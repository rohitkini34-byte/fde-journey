-- ===== section: Check your understanding (predict first, then run) =====
-- Week 3 mixed review: predict each numbered result, then run the file.
-- TEMP tables vanish when psql exits, so your real tables are safe.
CREATE TEMP TABLE entries (
    id      int  PRIMARY KEY,
    type    text NOT NULL,
    locale  text,           -- NULL here means "locale not set yet"
    views   int,            -- NULL means "no analytics data yet"
    status  text NOT NULL
);
INSERT INTO entries VALUES
    (1, 'blog', 'en-us', 120,  'published'),
    (2, 'blog', 'hi-in', NULL, 'draft'),
    (3, 'page', NULL,    40,   'published'),
    (4, 'page', 'en-us', 40,   'published'),
    (5, 'faq',  'en-us', NULL, 'draft');

-- 1 (Day 16) count(*) vs count(column), and what avg() does with NULL
SELECT count(*) AS all_rows, count(views) AS with_views,
       round(avg(views)) AS avg_views
FROM entries;

-- 2 (Day 16) a list with a NULL in it
SELECT count(*) FROM entries WHERE locale NOT IN ('hi-in', NULL);

-- 3 (Day 17) LEFT JOIN, then count per type
CREATE TEMP TABLE entry_tags (
    entry_id int REFERENCES entries (id),
    tag      text
);
INSERT INTO entry_tags VALUES (1, 'sale'), (1, 'diwali'), (3, 'sale');
SELECT e.type, count(t.tag) AS tags, count(*) AS row_count
FROM entries AS e
LEFT JOIN entry_tags AS t ON t.entry_id = e.id
GROUP BY e.type
ORDER BY e.type;

-- 4 (Day 20) ranking with a tie
SELECT id, views,
       rank() OVER (ORDER BY views DESC) AS rnk
FROM entries
WHERE status = 'published'
ORDER BY rnk, id;

-- 5 (Day 19) the same upsert, run twice
INSERT INTO entries VALUES (4, 'page', 'en-us', 99, 'published')
ON CONFLICT (id) DO UPDATE SET views = EXCLUDED.views
WHERE entries.views IS DISTINCT FROM EXCLUDED.views
RETURNING id, views;
INSERT INTO entries VALUES (4, 'page', 'en-us', 99, 'published')
ON CONFLICT (id) DO UPDATE SET views = EXCLUDED.views
WHERE entries.views IS DISTINCT FROM EXCLUDED.views
RETURNING id, views;

-- 6 (Day 15) AND and OR without brackets
SELECT id FROM entries
WHERE type = 'blog' OR type = 'page' AND views > 50
ORDER BY id;
