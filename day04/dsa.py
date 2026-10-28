"""Day 4 DSA practice (30 min): counting with dicts, and a stack with a list.

Both patterns show up in real FDE work: "top N error codes in this log" is
top_words, and validating nested JSON/template brackets is is_balanced.
Try each one for 15 minutes before looking at any hint.
"""


# ---------------------------------------------------------------------------
# top_words
# What:    the k most frequent words in a text.
# Input:   text: str, k: int
#          e.g. top_words("The cat and the hat. The end!", 2)
# Output:  [("the", 3), ("and", 1)]
# Rules:   lowercase everything; strip the characters .,!?;: from both ends
#          of each word; sort by count (highest first), then alphabetically.
# Practises: Day 3 counting pattern (dict.get(word, 0) + 1), sorted with key.
# ---------------------------------------------------------------------------
def top_words(text: str, k: int) -> list[tuple[str, int]]:
    """Return the k most common words as (word, count) pairs."""
    # HINT 1: text.lower().split() gives the words; word.strip(".,!?;:")
    #         removes punctuation from the ends only.
    # HINT 2: skip empty strings left over after stripping.
    # HINT 3: counts.items() gives (word, count) tuples. sorted() accepts
    #         key=a function; return (-count, word) from that function so the
    #         biggest count comes first and ties go alphabetical.
    # HINT 4: slicing [:k] keeps the first k results.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# is_balanced
# What:    are all (), [] and {} correctly opened and closed?
# Input:   s: str, e.g. "([]{})"
# Output:  True for "([]{})" and "", False for "([)]" and "(("
# Practises: a list used as a STACK (append = push, pop = take the last).
# ---------------------------------------------------------------------------
def is_balanced(s: str) -> bool:
    """Return True if every bracket closes in the right order."""
    # HINT 1: pairs = {")": "(", "]": "[", "}": "{"} maps closer -> opener.
    # HINT 2: on an opener, push it. On a closer, the stack must not be empty
    #         and its last item must be the matching opener.
    # HINT 3: at the end, the string is balanced only if the stack is empty.
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    print(top_words("The cat and the hat. The end!", 2))  # -> [('the', 3), ('and', 1)]
    print(is_balanced("([]{})"))  # -> True
    print(is_balanced("([)]"))  # -> False
    print(is_balanced("(("))  # -> False
    print(is_balanced(""))  # -> True
