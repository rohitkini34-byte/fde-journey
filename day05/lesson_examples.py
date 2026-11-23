"""Day 5 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Recap (2 minutes, from memory) =====
# Recap: predict the output before running.
import json

data = json.loads('{"id": 7, "tags": ["sso"], "vip": false}')
try:
    print(data["vip"], data["owner"])
except KeyError as err:
    print("missing:", err)
else:
    print("all found")
finally:
    print("done")

# ===== section: Concept 1: Classes and objects =====
# A class is a blueprint; each object made from it holds its own data.
class Ticket:
    # __init__ runs once per new object, like constructor() in a JS class
    def __init__(self, ticket_id, subject, priority="medium"):
        # self is the object being built (JS "this", but written out)
        self.ticket_id = ticket_id  # an attribute: data stored ON the object
        self.subject = subject
        self.priority = priority
        self.comments = []  # a NEW list for every ticket (safe)

    # a method is a function that lives on the class and gets self first
    def add_comment(self, text):
        self.comments.append(text)
        return len(self.comments)  # return a value, do not just print

    def describe(self):
        return f"{self.ticket_id} [{self.priority}] {self.subject}"


t1 = Ticket("T-101", "Login fails on SSO")  # no "new" keyword in Python
t2 = Ticket("T-102", "Export is slow", priority="high")
print(t1.describe())  # -> T-101 [medium] Login fails on SSO
print(t2.describe())  # -> T-102 [high] Export is slow
print(t1.add_comment("Asked for a HAR file"))  # -> 1
print(len(t1.comments), len(t2.comments))  # -> 1 0  (each has its own list)
# Python passes t1 as self for you, so these two calls are the same
print(Ticket.describe(t1) == t1.describe())  # -> True
# REMEMBER: self.x = ... inside __init__ is what gives each object its data.

# ===== section: Concept 1: Classes and objects =====
# __repr__ controls how an object prints; __eq__ controls what == means.
class Plain:
    def __init__(self, ticket_id):
        self.ticket_id = ticket_id


# without __repr__ you only see the class name and a memory address
print(Plain("T-1"))  # -> <__main__.Plain object at 0x...>  (address varies)


class Ticket:
    def __init__(self, ticket_id, status="open"):
        self.ticket_id = ticket_id
        self.status = status

    # "dunder" = double underscore. Python calls these for you.
    # __repr__: how the object looks in print() and logs (like toString())
    def __repr__(self):
        return f"Ticket({self.ticket_id!r}, status={self.status!r})"

    # __eq__: without it, == only asks "is this the very same object?"
    def __eq__(self, other):
        if not isinstance(other, Ticket):
            return NotImplemented  # let Python handle other types
        return self.ticket_id == other.ticket_id


a = Ticket("T-7")
b = Ticket("T-7", status="closed")
print(a)  # -> Ticket('T-7', status='open')
print(a == b, a is b)  # -> True False  (same id, but two objects)

# ===== section: Concept 2: Class attributes, classmethods and properties =====
# Class attributes, an alternate constructor, and a computed property.
class Ticket:
    # class attribute: ONE value shared by every ticket (like a static field)
    VALID_PRIORITIES = ("low", "medium", "high", "urgent")

    def __init__(self, ticket_id, subject, priority="medium"):
        if priority not in Ticket.VALID_PRIORITIES:
            raise ValueError(f"unknown priority {priority!r}")
        self.ticket_id = ticket_id
        self.subject = subject
        self.priority = priority

    # @classmethod receives the CLASS (cls) instead of an object (self).
    # FDE TIP: from_dict() is how API clients turn raw JSON into objects,
    # like a static fromJSON() method in JS.
    @classmethod
    def from_dict(cls, raw):
        return cls(raw["id"], raw["subject"].strip(),
                   raw.get("priority", "medium"))

    # @property: a method you READ like an attribute (no parentheses)
    @property
    def is_urgent(self):
        return self.priority == "urgent"


api_row = {"id": "T-201", "subject": "  SSO loop ", "priority": "urgent"}
t = Ticket.from_dict(api_row)
print(t.subject, t.is_urgent)  # -> SSO loop True
print(t.VALID_PRIORITIES[0])  # -> low  (looked up on the class)
try:
    Ticket("T-202", "Typo in footer", priority="critical")
except ValueError as err:
    print(err)  # -> unknown priority 'critical'

# ===== section: Concept 2: Class attributes, classmethods and properties =====
# GOTCHA: a mutable CLASS attribute is shared by every object.
class BadTicket:
    tags = []  # ONE list, created once, when the class is defined

    def __init__(self, ticket_id):
        self.ticket_id = ticket_id


class GoodTicket:
    def __init__(self, ticket_id):
        self.ticket_id = ticket_id
        self.tags = []  # a new list for each object, made in __init__


a, b = BadTicket("T-1"), BadTicket("T-2")
a.tags.append("vip")
print(b.tags)  # -> ['vip']  (b sees a's tag: it is the same list)

c, d = GoodTicket("T-3"), GoodTicket("T-4")
c.tags.append("vip")
print(d.tags)  # -> []
# REMEMBER: this is Day 2's mutable-default trap again. Mutable data
# (lists, dicts, sets) belongs in __init__, not on the class.

# ===== section: Concept 3: Inheritance, in small doses =====
# Inheritance: a child class reuses and extends a parent class.
class Notifier:
    def __init__(self, channel):
        self.channel = channel

    def send(self, message):
        return f"[{self.channel}] {message}"


# EmailNotifier "is a" Notifier, like "class B extends A" in JS
class EmailNotifier(Notifier):
    def __init__(self, address):
        super().__init__("email")  # run the parent's __init__ first
        self.address = address

    def send(self, message):  # override: replace the parent's version...
        base = super().send(message)  # ...but still reuse it
        return f"{base} -> {self.address}"


for n in [Notifier("slack"), EmailNotifier("ops@acme.in")]:
    print(n.send("T-101 breached SLA"))  # same call, different behaviour
# -> [slack] T-101 breached SLA
# -> [email] T-101 breached SLA -> ops@acme.in

print(isinstance(EmailNotifier("x@y.in"), Notifier))  # -> True

# ===== section: Concept 3: Inheritance, in small doses =====
# Day 4's custom exceptions, explained: they are tiny child classes.
class TicketError(Exception):  # the base error for our whole module
    """Anything that goes wrong with tickets."""


class InvalidTicketError(TicketError):  # "is a" TicketError
    """One ticket record is bad."""


try:
    raise InvalidTicketError("record 4: subject is empty")
except TicketError as err:  # catching the PARENT also catches the child
    print(type(err).__name__, "|", err)
# -> InvalidTicketError | record 4: subject is empty

print(issubclass(InvalidTicketError, Exception))  # -> True
# FDE TIP: one base error per module lets callers write ONE except clause.

# ===== section: Concept 4: Dataclasses =====
# @dataclass writes __init__, __repr__ and __eq__ for you.
from dataclasses import dataclass, field


@dataclass
class Ticket:
    # each line is a FIELD: a name, a type hint, and optionally a default
    ticket_id: str
    subject: str
    priority: str = "medium"  # fields with defaults must come last
    # GOTCHA: "tags: list[str] = []" is refused. default_factory=list
    # calls list() for EACH new ticket, so no list is ever shared.
    tags: list[str] = field(default_factory=list)


t = Ticket("T-1", "Webhook")
print(t)  # the generated __repr__ shows every field
# -> Ticket(ticket_id='T-1', subject='Webhook', priority='medium', tags=[])
same = Ticket("T-1", "Webhook")
print(t == same, t is same)  # -> True False  (== compares field values)
t.tags.append("api")  # dataclass objects are normal, changeable objects
print(t.tags, same.tags)  # -> ['api'] []

# ===== section: Concept 4: Dataclasses =====
# __post_init__ cleans and validates; asdict() makes JSON-ready data.
import json
from dataclasses import asdict, dataclass, field


@dataclass
class Ticket:
    ticket_id: str
    subject: str
    tags: list[str] = field(default_factory=list)

    # runs right after the generated __init__: the place for validation
    def __post_init__(self):
        self.subject = self.subject.strip()
        if not self.subject:
            raise ValueError(f"{self.ticket_id}: subject is empty")
        # normalise tags: lowercase, no duplicates, sorted (Day 3 set idea)
        self.tags = sorted({tag.lower() for tag in self.tags})


t = Ticket("T-2", "  Slow CSV ", ["CSV", "csv", "Export"])
print(t.subject, t.tags)  # -> Slow CSV ['csv', 'export']
print(json.dumps(asdict(t)))  # asdict: dataclass -> plain dict (nested too)
# -> {"ticket_id": "T-2", "subject": "Slow CSV", "tags": ["csv", "export"]}

try:
    Ticket("T-3", "   ")
except ValueError as err:
    print(err)  # -> T-3: subject is empty

# ===== section: Concept 4: Dataclasses =====
# frozen=True makes objects read-only: safe to share, usable as dict keys.
from dataclasses import FrozenInstanceError, dataclass, replace


@dataclass(frozen=True)
class Sla:
    priority: str
    hours: int


urgent = Sla("urgent", 4)
try:
    urgent.hours = 8  # not allowed on a frozen dataclass
except FrozenInstanceError as err:
    print("refused:", err)  # -> refused: cannot assign to field 'hours'

# replace() makes a changed COPY, like {...sla, hours: 8} in JS
relaxed = replace(urgent, hours=8)
print(urgent.hours, relaxed.hours)  # -> 4 8
# frozen + eq means Python can hash it, so it works as a dict key
print({urgent: "page on-call"}[Sla("urgent", 4)])  # -> page on-call

# ===== section: Concept 5: Type hints and enums =====
# Type hints say what a value SHOULD be. Python does not enforce them.
def sla_hours(priority: str, business_days: bool = False) -> int:
    hours = {"urgent": 4, "high": 24}.get(priority, 72)
    return hours * 2 if business_days else hours


print(sla_hours("urgent"))  # -> 4
print(sla_hours("high", business_days=True))  # -> 48
# GOTCHA: a wrong type still runs. Hints are for tools and humans.
print(sla_hours(42))  # -> 72  (no error: 42 is simply not in the dict)
print(sla_hours.__annotations__["return"])  # -> <class 'int'>

# ===== section: Concept 5: Type hints and enums =====
# The hint shapes you will use most (Python 3.10+ syntax).
from datetime import datetime


def find_ticket(tickets: list[dict], ticket_id: str) -> dict | None:
    """Return the matching ticket, or None (that is what "| None" says)."""
    for t in tickets:
        if t["id"] == ticket_id:
            return t
    return None


def count_by_status(tickets: list[dict]) -> dict[str, int]:
    counts: dict[str, int] = {}  # you can hint a variable too
    for t in tickets:
        counts[t["status"]] = counts.get(t["status"], 0) + 1
    return counts


rows = [{"id": "T-1", "status": "open"}, {"id": "T-2", "status": "open"},
        {"id": "T-3", "status": "closed"}]
print(find_ticket(rows, "T-3"))  # -> {'id': 'T-3', 'status': 'closed'}
print(find_ticket(rows, "T-9"))  # -> None
print(count_by_status(rows))  # -> {'open': 2, 'closed': 1}

# ISO text from an API -> a real datetime you can compare and subtract
opened: datetime = datetime.fromisoformat("2026-10-29T03:30:00+00:00")
print(opened.hour, opened.tzinfo)  # -> 3 UTC

# ===== section: Concept 5: Type hints and enums =====
# hints.py: a type checker reads hints WITHOUT running the code.
def total_hours(hours: list[int]) -> int:
    return sum(hours)


print(total_hours([4, 24]))  # -> 28
print(total_hours(["4", "24"]))  # wrong type: crashes only when it runs

# ===== section: Concept 5: Type hints and enums =====
# An Enum is a fixed set of named values: no more typo'd status strings.
from enum import StrEnum  # Python 3.11+, like a TypeScript string enum


class Status(StrEnum):
    OPEN = "open"
    PENDING = "pending"
    CLOSED = "closed"


s = Status("pending")  # raw API text -> enum member (and validates it)
print(s, s is Status.PENDING)  # -> pending True
print(s == "pending")  # -> True  (a StrEnum IS a str, so JSON just works)
print([m.value for m in Status])  # -> ['open', 'pending', 'closed']
try:
    Status("resolved")  # not one of the allowed values
except ValueError as err:
    print(err)  # -> 'resolved' is not a valid Status

# ===== section: Concept 5: Type hints and enums =====
# Putting it together: a typed model for a Contentstack-style entry.
from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum


class Locale(StrEnum):
    EN_IN = "en-in"
    HI_IN = "hi-in"


@dataclass
class Entry:
    uid: str
    title: str
    locale: Locale
    updated_at: datetime
    tags: list[str] = field(default_factory=list)

    # "Entry" is in quotes because the class is not finished yet
    @classmethod
    def from_api(cls, raw: dict) -> "Entry":
        """Raw JSON dict (strings everywhere) -> typed Entry."""
        return cls(
            uid=raw["uid"],
            title=raw["title"].strip(),
            locale=Locale(raw["locale"]),  # ValueError if unknown
            updated_at=datetime.fromisoformat(raw["updated_at"]),
            tags=list(raw.get("tags") or []),  # None or missing -> []
        )

    def to_api(self) -> dict:
        """Typed Entry -> JSON-safe dict (enum and datetime as text)."""
        return {"uid": self.uid, "title": self.title,
                "locale": str(self.locale),
                "updated_at": self.updated_at.isoformat(),
                "tags": self.tags}


raw = {"uid": "blt9", "title": " Pricing ", "locale": "hi-in",
       "updated_at": "2026-10-29T03:30:00+00:00"}
entry = Entry.from_api(raw)
print(entry.locale is Locale.HI_IN, entry.updated_at.year)  # -> True 2026
print(entry.to_api()["title"], entry.to_api()["tags"])  # -> Pricing []
print(Entry.from_api(entry.to_api()) == entry)  # -> True  (round trip)

# ===== section: Check your understanding (predict first, then run) =====
# Predict each output BEFORE you run this cell.
from dataclasses import dataclass

# 1
class Counter:
    hits = []

    def hit(self):
        self.hits.append(1)


x, y = Counter(), Counter()
x.hit()
y.hit()
print(len(x.hits))

# 2
@dataclass
class Tag:
    name: str


print(Tag("sso") == Tag("sso"), Tag("sso") is Tag("sso"))

# 3
def double(n: int) -> int:
    return n * 2


print(double("ab"))

# 4
class Light:
    def __init__(self):
        self.on = False

    def toggle(self):
        self.on = not self.on


lamp = Light()
lamp.toggle
print(lamp.on)

# 5
try:
    @dataclass
    class Bad:
        tags: list = []
except ValueError as err:
    print(type(err).__name__)
