"""Day 3 DSA: Two Sum and first unique character."""


def two_sum_brute(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return indices (i, j) whose values add up to target, checking every pair. O(n^2)."""
    for i in range(len(nums)):
        for j in range(i + 1, len(nums)):
            if nums[i] + nums[j] == target:
                return i, j
    return None


def two_sum(nums: list[int], target: int) -> tuple[int, int] | None:
    """Return indices (i, j) whose values add up to target in one pass. O(n) time, O(n) space."""
    seen: dict[int, int] = {}            # value -> index where we saw it
    for i, n in enumerate(nums):
        need = target - n
        if need in seen:                 # O(1) dict lookup instead of a second loop
            return seen[need], i
        seen[n] = i
    return None


def first_unique_char(s: str) -> int:
    """Return the index of the first character that appears exactly once, or -1. O(n)."""
    counts: dict[str, int] = {}
    for ch in s:
        counts[ch] = counts.get(ch, 0) + 1
    for i, ch in enumerate(s):
        if counts[ch] == 1:
            return i
    return -1


if __name__ == "__main__":
    print(two_sum_brute([2, 7, 11, 15], 9))   # (0, 1)
    print(two_sum([2, 7, 11, 15], 9))         # (0, 1)
    print(two_sum([3, 2, 4], 6))              # (1, 2)
    print(two_sum([3, 3], 6))                 # (0, 1)
    print(two_sum([1, 2], 10))                # None
    print(first_unique_char("leetcode"))      # 0
    print(first_unique_char("loveleetcode"))  # 2
    print(first_unique_char("aabb"))          # -1
