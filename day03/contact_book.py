"""Day 3: contact book — the data layer of a tiny CRM."""

contacts = [
    {"name": "Asha Patil", "email": "asha@acme.in", "city": "Pune", "tags": ["lead", "ai"]},
    {"name": "Ravi Shah", "email": "ravi@globex.com", "city": "Mumbai", "tags": ["customer"]},
    {"name": "Meera Iyer", "email": "meera@initech.io", "city": "Mumbai", "tags": ["lead"]},
    {"name": "Asha P", "email": "ASHA@acme.in", "city": "Pune", "tags": ["ai"]},
    # my own three: one duplicate email in different case, one with no tags/city
    {"name": "Karan Mehta", "email": "karan@hooli.dev", "city": "Bengaluru", "tags": ["customer", "cms"]},
    {"name": "Neha Rao", "email": "neha@umbrella.co"},
    {"name": "Karan M", "email": "Karan@Hooli.dev", "city": "Bengaluru", "tags": ["lead"]},
]


def add_contact(book: list[dict], name: str, email: str, city: str, tags: list[str] | None = None) -> bool:
    """Add a contact with a lowercased email; return False if the email already exists."""
    email = email.lower()
    if find_by_email(book, email) is not None:
        return False
    if tags is None:
        tags = []                       # fresh list on every call
    book.append({"name": name, "email": email, "city": city, "tags": tags})
    return True


def find_by_email(book: list[dict], email: str) -> dict | None:
    """Return the first contact whose email matches case-insensitively, or None."""
    target = email.lower()
    for contact in book:
        if contact.get("email", "").lower() == target:
            return contact
    return None


def contacts_by_city(book: list[dict]) -> dict[str, list[str]]:
    """Group contact names by city; contacts without a city go under 'Unknown'."""
    groups: dict[str, list[str]] = {}
    for contact in book:
        groups.setdefault(contact.get("city", "Unknown"), []).append(contact["name"])
    return groups


def unique_tags(book: list[dict]) -> set[str]:
    """Return every tag used across all contacts."""
    return {tag for contact in book for tag in contact.get("tags", [])}


def dedupe(book: list[dict]) -> list[dict]:
    """Return contacts with duplicate emails removed, keeping the first seen, in order."""
    seen: set[str] = set()
    result = []
    for contact in book:
        email = contact["email"].lower()
        if email not in seen:
            seen.add(email)
            result.append(contact)
    return result


def search(book: list[dict], term: str) -> list[str]:
    """Return names whose name or any tag contains term, case-insensitively."""
    t = term.lower()
    return [
        c["name"]
        for c in book
        if t in c["name"].lower() or any(t in tag.lower() for tag in c.get("tags", []))
    ]


def tag_counts(book: list[dict]) -> dict[str, int]:
    """Return how many contacts carry each tag."""
    counts: dict[str, int] = {}
    for contact in book:
        for tag in set(contact.get("tags", [])):   # a tag listed twice on one contact counts once
            counts[tag] = counts.get(tag, 0) + 1
    return counts


if __name__ == "__main__":
    print("=== dedupe ===")
    clean = dedupe(contacts)
    print(f"original sample: 4 contacts -> {len(dedupe(contacts[:4]))} after dedupe")
    print(f"{len(contacts)} contacts -> {len(clean)} after dedupe")
    for c in clean:
        print(f"  {c['name']:<12} {c['email']}")

    print("\n=== find_by_email ===")
    ravi = find_by_email(contacts, "RAVI@GLOBEX.COM")
    print(f"RAVI@GLOBEX.COM -> {ravi['name'] if ravi else None}")
    print(f"nobody@x.com    -> {find_by_email(contacts, 'nobody@x.com')}")

    print("\n=== contacts_by_city ===")
    for city, names in contacts_by_city(clean).items():
        print(f"  {city:<10} {', '.join(names)}")

    print("\n=== unique_tags ===")
    print(f"  {sorted(unique_tags(clean))}")

    print("\n=== search ===")
    print(f"  'ai'   -> {search(clean, 'ai')}")
    print(f"  'SHAH' -> {search(clean, 'SHAH')}")
    print(f"  'lead' -> {search(clean, 'lead')}")

    print("\n=== tag_counts ===")
    for tag, n in sorted(tag_counts(clean).items()):
        print(f"  {tag:<9} {n}")

    print("\n=== add_contact ===")
    book = dedupe(contacts)
    print(f"  add Divya:            {add_contact(book, 'Divya Nair', 'divya@stark.in', 'Kochi')}")
    print(f"  add Arjun:            {add_contact(book, 'Arjun Das', 'arjun@wayne.in', 'Kolkata')}")
    print(f"  add DIVYA@STARK.IN:   {add_contact(book, 'Divya again', 'DIVYA@STARK.IN', 'Kochi')}")
    divya, arjun = book[-2], book[-1]
    print(f"  stored email:         {divya['email']}")
    print(f"  tags lists shared?    {divya['tags'] is arjun['tags']}")   # must be False
