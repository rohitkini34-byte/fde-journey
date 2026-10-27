"""Day 1 DSA: largest of three numbers without using max()."""


def largest_of_three(a: float, b: float, c: float) -> float:
    """Return the largest of a, b and c using only comparisons."""
    largest = a
    if b > largest:
        largest = b
    if c > largest:
        largest = c
    return largest


if __name__ == "__main__":
    print(largest_of_three(3, 9, 4))      # 9
    print(largest_of_three(-1, -5, -2))   # -1
    print(largest_of_three(7, 7, 2))      # 7 (ties are fine)
    print(largest_of_three(1.5, 2.5, 2))  # 2.5
