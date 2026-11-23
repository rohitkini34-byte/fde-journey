"""Day 30 DSA practice (30 min): dicts for "latest wins", and a run counter.

Both come straight from sync work. dedupe_latest is what you do when two
pages (or two webhooks) carry the same entry. longest_failure_streak is the
number an on-call engineer asks for first: "how long was the CMS down?"
Try each one for 15 minutes before reading the hints.
"""


# ---------------------------------------------------------------------------
# dedupe_latest
# What:    keep one item per uid: the one with the largest "version".
# Input:   [{"uid": "a", "version": 1}, {"uid": "b", "version": 1},
#           {"uid": "a", "version": 3}, {"uid": "a", "version": 2}]
# Output:  [{"uid": "a", "version": 3}, {"uid": "b", "version": 1}]
# Rules:   output order = the order in which each uid FIRST appeared.
#          On a tie, keep the item seen first. Do not change the input.
#          Aim for one pass over the list: O(n) time.
# Practises: Day 3 dicts (dicts keep insertion order), "latest wins".
# ---------------------------------------------------------------------------
def dedupe_latest(items: list[dict]) -> list[dict]:
    """Return one item per uid, keeping the highest version."""
    # HINT 1: best = {} maps uid -> the best item seen so far.
    # HINT 2: replacing the VALUE for an existing key does not move the key,
    #         so first-appearance order is kept for free.
    # HINT 3: replace only when the new version is strictly greater (ties).
    # HINT 4: list(best.values()) is your answer.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# longest_failure_streak
# What:    the longest run of consecutive failed calls in a status log.
# Input:   [200, 503, 503, 200, 429, 500, 502, 200, 404]
# Output:  3   (429, 500, 502)
# Rules:   a failure is 429 or any 5xx. A 4xx other than 429 is NOT a
#          failure of the CMS (it is the caller's mistake), so it ends a run.
#          Empty list -> 0.
# Practises: Day 2 loops, the "current run / best run" pattern.
# ---------------------------------------------------------------------------
def longest_failure_streak(statuses: list[int]) -> int:
    """Return the length of the longest run of 429/5xx statuses."""
    # HINT 1: two counters: current (this run) and best (longest so far).
    # HINT 2: a failure adds 1 to current; anything else resets it to 0.
    # HINT 3: update best = max(best, current) inside the loop.
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    rows = [{"uid": "a", "version": 1}, {"uid": "b", "version": 1},
            {"uid": "a", "version": 3}, {"uid": "a", "version": 2}]
    print(dedupe_latest(rows))
    # -> [{'uid': 'a', 'version': 3}, {'uid': 'b', 'version': 1}]
    print(dedupe_latest([]))  # -> []
    print(longest_failure_streak([200, 503, 503, 200, 429, 500, 502, 200,
                                  404]))  # -> 3
    print(longest_failure_streak([404, 404, 401]))  # -> 0
    print(longest_failure_streak([]))  # -> 0
