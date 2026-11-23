"""Day 14 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Recap (2 minutes, from memory) =====
# Recap: predict what prints and roughly how many seconds it takes.
import asyncio
import time


async def fetch(n: int) -> int:
    await asyncio.sleep(1)  # stands in for a 1-second API call
    return n * 10


async def main() -> None:
    start = time.perf_counter()
    a = await fetch(1)  # await one at a time...
    b = await fetch(2)
    both = await asyncio.gather(fetch(3), fetch(4))  # ...then two together
    print(a, b, both, round(time.perf_counter() - start))


asyncio.run(main())

# ===== section: Check your understanding (predict first, then run) =====
# Week 2 mixed review: write your prediction for each part, then run.
import asyncio
import functools
from contextlib import contextmanager


# 1 (Day 11) generators are lazy and one-shot
def numbered(lines):
    for n, line in enumerate(lines, start=1):
        print("reading", n)
        yield f"{n}: {line}"


gen = numbered(["a", "b"])
print("made gen")
print(list(gen))
print(list(gen))  # what is left in gen now?


# 2 (Day 11) a decorator, with and without functools.wraps
def shout(func):
    @functools.wraps(func)  # copies __name__ and the docstring over
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs).upper()
    return wrapper


@shout
def greet(name: str) -> str:
    """Say hello."""
    return f"hello {name}"


print(greet("rohit"), greet.__name__)


# 3 (Day 11) context managers: what order, when an error happens?
@contextmanager
def step(name):
    print("enter", name)
    try:
        yield name
    finally:  # runs on success AND on error
        print("exit", name)


try:
    with step("outer"):
        with step("inner"):
            raise ValueError("boom")
except ValueError as e:
    print("caught", e)


# 4 (Day 13) gather: finish order vs result order
async def job(name, delay):
    await asyncio.sleep(delay)
    print("done", name)
    return name


async def main():
    return await asyncio.gather(job("slow", 0.2), job("fast", 0.1))


print(asyncio.run(main()))

# ===== section: Check your understanding (predict first, then run) =====
# Question 5, test_slug.py: predict pytest's summary line, then run it.
import pytest


def slugify(title: str) -> str:
    return title.strip().lower().replace(" ", "-")


@pytest.mark.parametrize(
    ("title", "expected"),
    [
        ("Hello World", "hello-world"),
        ("  FAQ ", "faq"),
        ("Q&A Page", "qa-page"),
    ],
)
def test_slugify(title, expected):
    assert slugify(title) == expected
