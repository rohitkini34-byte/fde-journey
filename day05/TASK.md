# Day 5 — Classes, Dataclasses & Type Hints (29 Oct)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): day05/support_ticket.py

A client's support team exports tickets from their helpdesk as JSON. Before an AI assistant can triage them, you need clean, typed objects. Your code must turn the raw export into SupportTicket objects, reject bad records with clear messages, and answer "which tickets have breached their SLA?".

```bash
# day05/ layout for today's task
day05/
    support_ticket.py      # the module: enums, SupportTicket, TicketQueue
    tickets_export.json    # the messy helpdesk export (given, do not edit)
    dsa.py                 # today's two DSA problems
    day05_notes.ipynb      # runnable examples from this session
```

The starter file gives you the Priority and Status enums, SLA_HOURS, the two exception classes, a fixed NOW, and TicketQueue.__init__ / __iter__. You write:

- The SupportTicket dataclass fields: id, subject, customer_email, created_at: datetime, priority (default MEDIUM), status (default OPEN), tags (default: a new empty list).
- __post_init__: strip the subject (empty is an error), strip and lowercase the email (no "@" is an error), and lowercase, dedupe and sort the tags. Raise InvalidTicketError with the messages shown in the starter.
- from_dict(cls, raw): a classmethod that turns one raw record into a ticket. Missing priority or status means MEDIUM or OPEN; missing or null tags means []; an unknown priority raises InvalidTicketError.
- to_dict(), age_hours(now) and is_overdue(now): JSON-safe output, whole hours since creation, and "not closed and older than its SLA".
- TicketQueue.add, __len__, by_status, overdue (oldest first) and summary, then load_queue(path), which never stops on a bad record.
```bash
# What a correct run looks like (run from the repo root)
$ python day05/support_ticket.py
rejected: record 3: subject is empty
rejected: record 4: unknown priority 'critical'
rejected: record 6: email 'john.doe-at-contoso' has no '@'
rejected: record 8: duplicate id 'T-1002'
loaded: 4, rejected: 4
by status: {'open': 2, 'pending': 1, 'closed': 1}
overdue: T-1002 (high, 50h), T-1001 (urgent, 10h)
round trip ok: True
```

Acceptance criteria:

- python day05/support_ticket.py prints exactly the eight lines shown above.
- SupportTicket is a @dataclass; tags uses field(default_factory=list); priority and status are Priority / Status members, never raw strings.
- Building a ticket directly with bad data raises InvalidTicketError, for example SupportTicket("T-1", "   ", "a@b.in", NOW).
- json.dumps(t.to_dict()) works and SupportTicket.from_dict(t.to_dict()) == t for every ticket.
- Every function and method has type hints, and python -c "import support_ticket" run inside day05/ prints nothing.
- Stretch: pip install mypy, then mypy support_ticket.py reports no errors. Skip it if pip is new to you; Day 6 sets this up properly.
- Committed and pushed with a meaningful message.
Hints (no solutions, try first):

- Declare the fields first and test them in a scratch file with print(SupportTicket("T-9", " Slow ", " A@B.in ", NOW)) before writing any method.
- Concept 5's Entry.from_api is the shape of from_dict; the new part is converting ValueError from Priority(...) into InvalidTicketError with raise ... from err.
- now - self.created_at gives a timedelta; look at .total_seconds().
- load_queue is Day 4's import_contacts again: enumerate(records, start=1) and one try around both from_dict() and queue.add().
- For summary, loop over Status itself so statuses with zero tickets still appear.
## DSA practice (30 min)

- MinStack. A class with push(x), pop(), top(), get_min() and __len__, every one O(1), so get_min() cannot loop. Example: push 5, 2, 7, then get_min() is 2; pop twice and get_min() is 5. Hint: keep a second list holding "the minimum so far" at each height.
- Group anagrams. group_anagrams(words: list[str]) -> list[list[str]] groups words with the same letters, in first-seen order. ["eat", "tea", "tan", "ate", "nat", "bat"] gives [["eat", "tea", "ate"], ["tan", "nat"], ["bat"]]. Hint: "".join(sorted(word)) is the same for all anagrams; use it as a dict key with Day 3's setdefault.
## Quiz (3 quick questions)

- What is self, and why does Python make you write it when JavaScript's this is implicit?
- For data coming back from a customer's API, when would you choose a dataclass over a plain dict, and when a plain class over a dataclass?
- You write def total(prices: list[float]) -> float and call total(["1", "2"]). What happens when it runs, and what would have caught it before running?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 5 review": your recap answers, your predictions next to the real outputs, support_ticket.py, the terminal output of the run, both DSA solutions and the quiz answers. Include Day 4's contact_store.py and main.py if they are done. Tracebacks are welcome; send them with what you tried.

