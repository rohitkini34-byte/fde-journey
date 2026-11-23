-- ===== section: Concept 3: Transactions: all of it, or none of it =====
-- Concept 3: a transaction in psql. Nothing is permanent until COMMIT.
BEGIN;  -- start a transaction (psql shows the prompt fde=*#)
UPDATE demo_posts SET status = 'published' WHERE uid = 'blt104';
-- -> UPDATE 1
SELECT uid, status FROM demo_posts WHERE uid = 'blt104';
-- ->   uid   |  status
-- -> --------+-----------
-- ->  blt104 | published     (inside the transaction you see your change)
ROLLBACK;  -- undo everything since BEGIN
SELECT uid, status FROM demo_posts WHERE uid = 'blt104';
-- ->   uid   | status
-- -> --------+--------
-- ->  blt104 | draft         (as if the UPDATE never happened)
-- REMEMBER: BEGIN ... COMMIT keeps the work; BEGIN ... ROLLBACK undoes it.
