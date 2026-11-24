"""Day 31: two tests of your own for load.py (acceptance criterion 1).

The given tests cover the rules; these two cover cases a customer will hit
in the first month. Replace each pytest.skip(...) line with your test body.
You may copy the db fixture and helpers from test_load.py, or import them:
    from test_load import db, count_rows, BATCH_1   # noqa: F401
(pytest finds a fixture that is imported into the test module.)

Run inside day31/:   python -m pytest -q test_mine.py
"""

import pytest

from load import LoadReport, read_batch, upsert_entries  # noqa: F401
from test_load import BATCH_1, count_rows, db  # noqa: F401


# ---------------------------------------------------------------------------
# Test 1: an empty batch is a no-op.
# Why:   the CMS had no changes this hour, so the fetch layer returns [].
#        The load must not fail and must report nothing.
# Check: upsert_entries(db, []) == LoadReport() and the table is still empty.
# HINT:  LoadReport() with no arguments is all zeros.
# ---------------------------------------------------------------------------
def test_empty_batch_is_a_no_op(db):
    pytest.skip("TODO: write this test")


# ---------------------------------------------------------------------------
# Test 2: a row deleted by hand comes back on the next load.
# Why:   someone ran DELETE on the table to "fix" something. The next sync
#        must repair it: exactly one insert, everything else skipped.
# Check: load batch_1, delete blt004, load batch_1 again ->
#        LoadReport(inserted=1, updated=0, skipped=4), and 5 rows.
# HINT 1: db.execute("DELETE FROM entries WHERE uid = %s", ["blt004"])
# HINT 2: use count_rows(db) from test_load.py for the row count.
# ---------------------------------------------------------------------------
def test_deleted_row_is_restored_by_the_next_load(db):
    pytest.skip("TODO: write this test")
