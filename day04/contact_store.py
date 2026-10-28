"""Day 4 task: a safe JSON store for the contact book, plus a CRM import.

Real-world purpose: a client's marketing team sends a weekly JSON export from
their old CRM. It is messy. This module keeps the good records, reports the bad
ones, and saves everything to disk without ever corrupting the saved file.
In Contentstack terms: this is the validation + persistence layer you would
write before pushing entries into the CMS.

ASSIGNMENT (from the Day 4 session in the master doc)
-----------------------------------------------------
Implement the five functions below. main.py (your other file) imports this
module and runs the whole flow.

ACCEPTANCE CRITERIA
1. First run of main.py prints exactly:
       rejected: record 3: name is empty
       rejected: record 6: email 'john.doe-at-contoso' has no '@'
       rejected: record 7: tags must be a list, got str
       valid: 4, rejected: 3, added: 3, total: 3
2. day04/data/contacts.json exists, is indented, has "version": 1 and
   "saved_at", and lists the 3 contacts sorted by name with lowercased emails.
3. A second run adds 0 and keeps the total at 3.
4. Deleting data/contacts.json and running again behaves like a first run.
5. A broken store file (delete its last line) makes main.py print ONE clear
   line naming the file and JSON line number, exit with code 1, no traceback.
6. validate_contact never changes the dict it was given; no bare "except";
   every open() uses "with" and encoding="utf-8".
7. python -c "import contact_store" (run inside day04/) prints nothing.
8. Committed and pushed with a meaningful message.
"""

import json  # JSON text <-> Python (Concept 2)
import os  # os.replace() for the atomic swap (Concept 5)
from datetime import datetime, timezone  # for the "saved_at" timestamp
from pathlib import Path  # paths that work on any OS (Concept 1)

STORE_VERSION = 1  # REMEMBER: version your file formats from day one


# ---------------------------------------------------------------------------
# Custom exceptions (given, you do not need to change these).
# A custom exception is a tiny class that "is a" built-in error type.
# Classes are tomorrow's topic; for now just use them with raise/except.
# ---------------------------------------------------------------------------
class ContactStoreError(Exception):
    """Raised when the store or import FILE itself is missing or broken."""


class InvalidContactError(ValueError):
    """Raised when ONE contact record fails validation."""


# ---------------------------------------------------------------------------
# validate_contact
# What:    check one raw record and return a NEW, cleaned dict.
# Input:   raw dict, e.g. {"name": " Ravi Shah", "email": " RAVI@Globex.com",
#                          "city": "Mumbai", "tags": ["Customer"]}
# Output:  {"name": "Ravi Shah", "email": "ravi@globex.com",
#           "city": "Mumbai", "tags": ["customer"]}
# Rules:   name  -> stripped, must not be empty   -> "name is empty"
#          email -> stripped + lowercased, needs "@" -> "email 'x' has no '@'"
#                   and a "." after the "@"          -> "email 'x' has no domain"
#          city  -> stripped, or "Unknown" if missing/None/blank
#          tags  -> missing or None means []; must be a list
#                   -> "tags must be a list, got str"; then lowercase,
#                   remove duplicates, sort
# Practises: dict .get() (Day 3), raising your own exception (Concept 3).
# ---------------------------------------------------------------------------
def validate_contact(raw: dict) -> dict:
    """Return a cleaned copy of one contact, or raise InvalidContactError."""
    # HINT 1: read every field with raw.get("field") so a missing key does not
    #         crash; "or ''" turns None into an empty string before .strip().
    # HINT 2: raise InvalidContactError("name is empty") when the name is blank.
    # HINT 3: for the error text use {raw.get('email')!r} so the ORIGINAL value
    #         appears in quotes, exactly like the expected output.
    # HINT 4: isinstance(tags, list) tells you whether tags is really a list;
    #         type(tags).__name__ gives "str" for the message.
    # HINT 5: build and return a NEW dict; never assign into raw.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# load_contacts
# What:    read the saved store and return its list of contacts.
# Input:   path to data/contacts.json
# Output:  list of contact dicts; [] when the file does not exist yet.
# File shape: {"version": 1, "saved_at": "...", "contacts": [ ... ]}
# Errors:  invalid JSON           -> ContactStoreError("<path> is not valid
#                                    JSON (line N)")
#          wrong shape or version -> ContactStoreError naming the file
# Practises: with/open (Concept 1), json.load (Concept 2), try/except/raise
#            from (Concept 3).
# ---------------------------------------------------------------------------
def load_contacts(path: Path) -> list[dict]:
    """Return contacts from the store file, or [] if it does not exist."""
    # HINT 1: copy the shape of load_settings() from Concept 3, but return []
    #         (not {}) for FileNotFoundError.
    # HINT 2: json.JSONDecodeError has .lineno; put it in the message and use
    #         "raise ContactStoreError(msg) from err".
    # HINT 3: after loading, check: isinstance(data, dict),
    #         data.get("version") == STORE_VERSION, and that
    #         data.get("contacts") is a list. Otherwise raise.
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# save_contacts
# What:    write all contacts to disk, safely.
# Input:   path to data/contacts.json, list of contact dicts
# Output:  None. The file contains
#          {"version": 1, "saved_at": "<UTC ISO time>", "contacts": [...]}
#          with contacts sorted by name, indent=2, ensure_ascii=False, UTF-8.
# Must:    create the data/ folder if missing; use an ATOMIC write
#          (temp file + os.replace) so a crash never leaves half a file.
# Practises: Concept 5 (safe JSON store), datetime from Concept 4.
# ---------------------------------------------------------------------------
def save_contacts(path: Path, contacts: list[dict]) -> None:
    """Save contacts as versioned JSON using an atomic write."""
    # HINT 1: datetime.now(timezone.utc).isoformat() gives the saved_at text.
    # HINT 2: sorted(contacts, key=...) needs a function that returns the name;
    #         a tiny helper def by_name(c): return c["name"] works fine.
    # HINT 3: reuse the save_json() pattern from Concept 5 (tmp file in the
    #         same folder, then os.replace).
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# import_contacts
# What:    read the CRM export (a JSON LIST of raw records) and validate each.
# Input:   path to contacts_import.json
# Output:  (valid_contacts, error_messages)
#          e.g. ([{...}, {...}], ["record 3: name is empty", ...])
# Rule:    one bad record NEVER stops the import; record numbers start at 1.
# Errors:  missing file or invalid JSON -> ContactStoreError
# Practises: try/except inside a loop (Concept 3), enumerate.
# ---------------------------------------------------------------------------
def import_contacts(path: Path) -> tuple[list[dict], list[str]]:
    """Validate every record in the export; return (valid, error messages)."""
    # HINT 1: open + json.load the file inside try; turn FileNotFoundError and
    #         json.JSONDecodeError into ContactStoreError.
    # HINT 2: for number, record in enumerate(records, start=1): ...
    # HINT 3: inside the loop, try validate_contact(record); on
    #         InvalidContactError as err, append f"record {number}: {err}".
    raise NotImplementedError("TODO")


# ---------------------------------------------------------------------------
# merge_contacts
# What:    add incoming contacts whose email is not in the store yet.
# Input:   existing list, incoming list (both already validated)
# Output:  (merged_list, number_added)
# Note:    also skip duplicates INSIDE incoming (Asha appears twice in the
#          sample export with the same email after cleaning).
# Practises: Day 3 dedupe with a set of seen emails.
# ---------------------------------------------------------------------------
def merge_contacts(
    existing: list[dict], incoming: list[dict]
) -> tuple[list[dict], int]:
    """Return existing + new contacts (deduplicated by email) and the count."""
    # HINT 1: start a set with every email already in existing.
    # HINT 2: copy existing into a new list (list(existing)) so you do not
    #         change the caller's list.
    # HINT 3: for each incoming contact, skip it if its email is in the set;
    #         otherwise append it, add the email to the set, count it.
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    # Quick self-checks while you build. Runs only with: python contact_store.py
    # (never when main.py imports this module).
    print(validate_contact({"name": " Ravi Shah", "email": " RAVI@Globex.com"}))
    # -> {'name': 'Ravi Shah', 'email': 'ravi@globex.com', 'city': 'Unknown',
    #     'tags': []}
    try:
        validate_contact({"name": "John", "email": "john.doe-at-contoso"})
    except InvalidContactError as err:
        print("rejected:", err)
    # -> rejected: email 'john.doe-at-contoso' has no '@'
    print(load_contacts(Path("does_not_exist.json")))  # -> []
