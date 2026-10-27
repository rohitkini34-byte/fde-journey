"""Day 2 DSA: is_prime and vowel count."""


def is_prime(n: int) -> bool:
    """Return True if n is a prime number.

    Only divisors up to sqrt(n) need checking: if n = a * b and both a and b
    were bigger than sqrt(n), then a * b would be bigger than n. So every
    composite number has at least one factor <= sqrt(n).
    """
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d * d <= n:          # same as d <= sqrt(n), without floats
        if n % d == 0:
            return False
        d += 2                 # even divisors were already ruled out
    return True


def count_vowels(text: str) -> int:
    """Return how many vowels (a, e, i, o, u, any case) are in text."""
    count = 0
    for ch in text.lower():
        if ch in "aeiou":
            count += 1
    return count


if __name__ == "__main__":
    print([n for n in range(30) if is_prime(n)])   # [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
    print(is_prime(97), is_prime(1), is_prime(91))  # True False False (91 = 7 * 13)
    print(count_vowels("Forward Deployed Engineer"))  # 9
    print(count_vowels("rhythm"))                     # 0
