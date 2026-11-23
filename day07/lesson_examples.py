"""Day 7 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Recap (2 minutes, from memory) =====
# Recap: predict the output, then explain why 401 and 404 are not in it.
def should_retry(status: int) -> bool:
    # True when sending the same request again might succeed
    return status == 429 or status >= 500


statuses = (200, 401, 404, 429, 500, 503)
print([s for s in statuses if should_retry(s)])

# ===== section: Check your understanding (predict first, then run) =====
# Week 1 mixed review: write your prediction for each part, then run.
import json
from dataclasses import dataclass

# 1 (Day 2) labels and defaults
def add_tag(tag, tags=[]):  # where does this [] live between calls?
    tags.append(tag)
    return tags

add_tag("sso")
print(add_tag("seo"))

# 2 (Day 3) counting with a dict, then a dict comprehension
priorities = ["high", "low", "high", "medium", "high", "low"]
counts = {}
for p in priorities:
    counts[p] = counts.get(p, 0) + 1  # .get(): 0 the first time
print({k: v for k, v in counts.items() if v > 1})

# 3 (Day 4) a JSON round trip: like JSON.parse(JSON.stringify(x)) in JS
original = {1: ("blt001", "blt002")}
print(json.loads(json.dumps(original)))

# 4 (Day 4) try / except / else / finally: what runs, and in what order?
def double(raw: str):
    try:
        n = int(raw)
    except ValueError:
        return "bad input"
    else:  # runs only when the try block raised nothing
        return n * 2
    finally:  # runs every time, even after a return
        print("checked", raw)

print(double("21"))
print(double("x"))

# 5 (Day 5) dataclasses compare by value, like a deep equals
@dataclass
class Ticket:
    uid: str
    priority: int = 3

tickets = [Ticket("t2", 1), Ticket("t1")]
print(sorted(tickets, key=lambda t: t.priority)[0])
print(Ticket("t1") == Ticket("t1"), Ticket("t1") is Ticket("t1"))
