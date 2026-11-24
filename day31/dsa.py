"""Day 31 DSA practice (30 min): two problems from the store layer.

Give each problem 15 minutes before you read its hints. When a solution
works, write its time and space complexity in a comment above it.

Run:  python dsa.py   (prints the expected outputs when you are done)
"""


# ---------------------------------------------------------------------------
# Problem 1: plan_upsert (a hash map, one pass)
# What:    do in Python what today's upsert does in SQL. Given the rows
#          already stored and an incoming batch, say what each incoming
#          row would cause.
# Input:   stored   = {"a": ("A", 1), "b": ("B", 1)}   key -> (title, version)
#          incoming = [("a", "A", 1), ("b", "B2", 2), ("c", "C", 1),
#                      ("b", "B-old", 0)]
# Output:  {"insert": ["c"], "update": ["b"], "skip": ["a", "b"]}
# Rules:   key not stored -> insert. Stored and incoming version >= stored
#          version and the title differs -> update. Anything else -> skip.
#          Apply each decision to your own copy of stored as you go, so a
#          later row for the same key compares against the NEW value
#          (this is how the database sees a batch, row by row).
#          Lists keep the order of the incoming rows.
# GOTCHA:  do not change the caller's stored dict: copy it first.
# ---------------------------------------------------------------------------
def plan_upsert(
    stored: dict[str, tuple[str, int]],
    incoming: list[tuple[str, str, int]],
) -> dict[str, list[str]]:
    """Classify each incoming row as insert, update or skip."""
    # HINT 1: current = dict(stored) is a shallow copy (like {...stored}).
    # HINT 2: result = {"insert": [], "update": [], "skip": []}
    # HINT 3: for key, title, version in incoming: ... compare with
    #         current.get(key), which is None for a new key.
    # HINT 4: after an insert or update, write current[key] = (title,
    #         version) so the next row for that key sees it.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# Problem 2: longest_unique_run (sliding window, a classic interview one)
# What:    a sync log lists uids in the order they were written. Find the
#          length of the longest stretch with NO uid repeated (a repeat
#          inside one batch is often a paging bug, Day 30).
# Input:   ["a", "b", "c", "a", "d", "b"]  -> 4   ("b", "c", "a", "d")
#          ["a", "a", "a"]                 -> 1
#          []                              -> 0
# Rules:   O(n) time: one pass, never restart the scan from the beginning.
# ---------------------------------------------------------------------------
def longest_unique_run(uids: list[str]) -> int:
    """Return the length of the longest run without a repeated uid."""
    # HINT 1: keep a window [start, i]. last_seen = {} maps uid -> index.
    # HINT 2: at index i, if uid was seen at an index >= start, the window
    #         must begin right after that index: start = last_seen[uid] + 1
    # HINT 3: then record last_seen[uid] = i and update the best length
    #         i - start + 1.
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    stored = {"a": ("A", 1), "b": ("B", 1)}
    incoming = [("a", "A", 1), ("b", "B2", 2), ("c", "C", 1),
                ("b", "B-old", 0)]
    print(plan_upsert(stored, incoming))
    # -> {'insert': ['c'], 'update': ['b'], 'skip': ['a', 'b']}
    print(stored)  # -> {'a': ('A', 1), 'b': ('B', 1)}   (unchanged)
    print(longest_unique_run(["a", "b", "c", "a", "d", "b"]))  # -> 4
    print(longest_unique_run(["a", "a", "a"]))  # -> 1
    print(longest_unique_run([]))  # -> 0
