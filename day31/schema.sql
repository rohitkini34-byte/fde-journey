-- Day 31 task, TODO 3: the entries table for thin-sync (store layer).
--
-- Real-world purpose: this table is the copy of the customer's CMS content
-- that your own API (Day 32) serves. The fetch layer (Day 30) checks data
-- in Python; this file is the LAST line of defence: whatever code writes
-- here later (a webhook handler, a teammate's script, a hotfix at 2 AM),
-- the database itself refuses a row that breaks the rules.
--
-- In Contentstack terms: one row per entry PER LOCALE. "blt001" in en-us
-- and "blt001" in hi-in are two different rows with the same uid.
--
-- This file must be SAFE TO RUN TWICE (load.py runs it on every start),
-- so every statement uses IF NOT EXISTS.
--
-- As given, the file runs but has no rules at all. Add them where the
-- TODO comments say. The tests in test_load.py check each rule.

CREATE TABLE IF NOT EXISTS entries (
    -- TODO 3a: uid must be present and not empty or only spaces.
    -- HINT 1: NOT NULL stops a missing value; a CHECK stops ''.
    -- HINT 2: btrim(x) removes spaces at both ends (like .trim() in JS).
    uid          text,

    -- TODO 3b: present, defaults to 'en-us', and shaped like xx-yy
    -- (two lowercase letters, a dash, two lowercase letters).
    -- HINT 3: Postgres regex match is the ~ operator:
    --         CHECK (locale ~ '^[a-z]{2}-[a-z]{2}$')
    locale       text,

    -- TODO 3c: present and not blank (same idea as uid).
    content_type text,

    -- TODO 3d: present and not blank.
    title        text,

    -- TODO 3e: present, defaults to an empty array.
    -- HINT 4: the literal for an empty text array is '{}'.
    tags         text[],

    -- TODO 3f: present. Keep the type timestamptz: it stores a moment in
    -- time, so 09:30Z and 15:00+05:30 are the same value (Concept 1).
    updated_at   timestamptz,

    -- TODO 3g: present, defaults to now(): when WE last wrote this row.
    -- GOTCHA: this is not the CMS's updated_at. Keep both: one says when
    -- the content changed, the other when the sync touched it.
    synced_at    timestamptz

    -- TODO 3h: the primary key is the PAIR (uid, locale).
    -- HINT 5: add a comma after synced_at's line, then
    --         PRIMARY KEY (uid, locale)
);

-- Given: the index Day 32's "list entries of a type, newest first" query
-- will use (Day 19 taught why). IF NOT EXISTS keeps the file re-runnable.
CREATE INDEX IF NOT EXISTS entries_content_type_updated_at_idx
    ON entries (content_type, updated_at DESC);
