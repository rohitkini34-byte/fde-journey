"""Day 4 task, part 2: the script you run. It imports contact_store.

Real-world purpose: this is the "job" a client would schedule weekly:
load the store, import the new CRM export, report rejects, save.

Run it from the repo root:   python day04/main.py
Expected first run:
    rejected: record 3: name is empty
    rejected: record 6: email 'john.doe-at-contoso' has no '@'
    rejected: record 7: tags must be a list, got str
    valid: 4, rejected: 3, added: 3, total: 3
Expected second run: same rejections, then
    valid: 4, rejected: 3, added: 0, total: 3
If data/contacts.json is broken: one line starting with "error:", exit code 1.
"""

from pathlib import Path

import contact_store  # your module in the same folder (Concept 4)

# __file__ is the path of THIS script. .parent is the day04/ folder.
# FDE TIP: build paths from the script's folder, not from where you ran the
# command, so "python day04/main.py" and "cd day04; python main.py" both work.
HERE = Path(__file__).parent
STORE_PATH = HERE / "data" / "contacts.json"
IMPORT_PATH = HERE / "contacts_import.json"


# ---------------------------------------------------------------------------
# main
# What:    load -> import -> print rejections -> merge -> save -> summary.
# Input:   none (uses STORE_PATH and IMPORT_PATH)
# Output:  prints lines like "valid: 4, rejected: 3, added: 3, total: 3"
# Errors:  catch contact_store.ContactStoreError ONCE around the whole flow,
#          print "error: <message>" and exit with code 1.
# Practises: modules/imports (Concept 4), specific except (Concept 3).
# ---------------------------------------------------------------------------
def main() -> None:
    """Run one import cycle and print a summary."""
    # HINT 1: existing = contact_store.load_contacts(STORE_PATH)
    # HINT 2: valid, errors = contact_store.import_contacts(IMPORT_PATH)
    # HINT 3: print each error as "rejected: <message>"
    # HINT 4: merge, then save, then print the f-string summary line.
    # HINT 5: wrap steps 1-4 in try/except contact_store.ContactStoreError as
    #         err: print(f"error: {err}") then raise SystemExit(1).
    raise NotImplementedError("TODO")


if __name__ == "__main__":
    main()
