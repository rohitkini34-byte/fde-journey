"""Day 15 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Relational thinking: tables, rows, columns and keys =====
# Concept 1: the same question, asked imperatively (Python) and declaratively.
entries = [
    {"uid": "blt1", "title": "Pricing", "status": "published", "views": 900},
    {"uid": "blt2", "title": "Careers", "status": "draft", "views": 0},
    {"uid": "blt3", "title": "Home", "status": "published", "views": 4000},
]

# Imperative: YOU write HOW, step by step (filter, sort, slice)
published = [e for e in entries if e["status"] == "published"]
published.sort(key=lambda e: e["views"], reverse=True)  # most viewed first
print([e["title"] for e in published[:1]])  # -> ['Home']

# Declarative: you say WHAT you want, the database decides how.
# This string is the SQL you will write today (it runs in psql, not here):
query = """
SELECT title FROM entries
WHERE status = 'published'
ORDER BY views DESC
LIMIT 1;
"""
# REMEMBER: a table is a list of same-shaped records; SQL describes the
# result, the database plans the loop.
