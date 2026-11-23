-- ===== section: Concept 5: ruff, linting and formatting in one fast tool =====
# Day 12: messy.py, five classic problems in 17 lines
import os, json
from typing import List


def load(path, cache={}):
    if path in cache:
        return cache[path]
    try:
        data = json.load(open(path))
    except:
        data = None
    cache[path] = data
    return data


def titles(entries: List[dict]) -> List[str]:
    return [e["title"] for e in entries if e["status"] == "published"]

# pyproject.toml, next to it
[tool.ruff.lint]
select = ["E", "F", "W", "I", "B", "UP", "SIM"]

$ ruff check --output-format concise messy.py
# -> messy.py:1:1: E401 [*] Multiple imports on one line
# -> messy.py:1:1: I001 [*] Import block is un-sorted or un-formatted
# -> messy.py:1:8: F401 [*] `os` imported but unused
# -> messy.py:2:1: UP035 `typing.List` is deprecated, use `list` instead
# -> messy.py:5:22: B006 Do not use mutable data structures for ...
# -> messy.py:9:26: SIM115 Use a context manager for opening files
# -> messy.py:10:5: E722 Do not use bare `except`
# -> messy.py:16:21: UP006 [*] Use `list` instead of `List` for ...
# -> messy.py:16:36: UP006 [*] Use `list` instead of `List` for ...
# -> Found 9 errors.
$ ruff check --fix messy.py   # applies the 5 safe fixes, 3 remain
$ ruff format messy.py        # rewrites the layout, like Prettier
