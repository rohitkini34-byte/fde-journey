# Day 10 — Testing with pytest: Asserts, Fixtures, Parametrize, Testing Errors & Faking HTTP (3 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): day10 test suites

The scenario: a customer is about to run your Day 4 contact import and Day 6 CMS export on their own servers. Their tech lead says: "We run nothing in production that does not come with tests. Show me a green suite that does not need our network." Today you write those suites.

Before you start: git switch main && git pull, then git switch -c day10-tests. The starters are in day10/: pytest.ini (given, complete), test_contact_store.py, test_cms_export.py and dsa.py. Every test function in the starters has a comment saying what to prove and HINT lines; its body is raise NotImplementedError("TODO"), so it is red until you write it.

Part A, test_contact_store.py, then finish contact_store.py (110 min). Write the tests first, from the rules in contact_store.py's comments, and run them: they fail with NotImplementedError from contact_store. Then implement the five Day 4 functions one at a time until each group goes green: validate_contact, merge_contacts, save and load, then import. Finally run day04/main.py and check Day 4's acceptance criteria. The tests use the real day04/contacts_import.json for the import test and tmp_path for every file they write.

Part B, test_cms_export.py (40 min). Tests for entry_to_row, write_csv, get_api_key, fetch_page, fetch_all_entries and main, with a FakeSession like Concept 5's. Match the fakes to your own cms_export.py: look at how your code calls session.get and which response fields it reads. The file starts with pytest.importorskip("cms_export"), so it skips cleanly if day06/cms_export.py is missing.

```bash
# Hands-on target: from the repo root, when both parts are done
python3 -m pytest day10 -v
# -> collected 30+ items       (your exact count will differ)
# -> day10/test_contact_store.py::test_validate_cleans_good_record PASSED
# -> ...
# -> day10/test_cms_export.py::test_fetch_page_retries_503 PASSED
# -> ============ 30 passed in 0.15s ============
python3 -m pytest day10 --durations=3   # no test should take 0.1 s+
python3 -m pytest day10 -q; echo "exit: $?"
# -> exit: 0
```

Acceptance criteria:

- From the repo root, python3 -m pytest day10 -v shows every test passing: 0 failed and 0 skipped (a skip means cms_export.py is missing, so Part B is not done yet).
- python3 -m pytest day10 --co -q lists at least 15 tests in test_contact_store.py and at least 12 in test_cms_export.py. Parametrized cases count separately.
- Each file defines at least one fixture of your own, at least one parametrize, and at least two pytest.raises checks with match=.
- No network: the suite passes with mock_cms.py stopped and Wi-Fi off. No real waiting: --durations=3 shows no test at 0.1 s or slower.
- Tests never touch your real files: day04/data/contacts.json and day06/output/ are unchanged after a full run (check with git status and ls -l). Every write goes to tmp_path.
- Every test passes alone. Run two of them by node id to check.
- Mutation check: make each of these bugs on purpose, one at a time, and confirm at least one test goes red: remove the email .lower() in validate_contact; change start=1 to start=0 in import_contacts; add 401 to the statuses fetch_page retries. Put the code back. Note in the pull request which test caught each bug.
- day04/main.py now meets Day 4's acceptance criteria 1 to 7 (the tests helped you get there).
- The work goes in through the branch day10-tests in at least three commits (contact_store tests; contact_store implementation; cms_export tests), pushed, with a pull request that has What, Why, How to test and Open items.
Hints (no solutions, try first):

- Write one test, run it, watch it fail for the right reason, then write the next one. python3 -m pytest day10 -x stops at the first failure so the output stays short.
- For "does not change its input", keep a copy before the call with copy.deepcopy(raw) (or a hand-written dict literal) and compare after.
- The import test needs the path of the real export file. Path(contact_store.__file__).parent is the day04/ folder, wherever you run pytest from.
- For the broken-store test, write a file with invalid JSON into tmp_path (for example a JSON object with its closing brace missing) and check the message names the file and a line number, using match=.
- For fetch_page's connection error, a fake session can raise instead of return: store an exception instance in the prepared list, and in get(), raise it if isinstance(reply, Exception). Use requests.ConnectionError() so your code's except clause catches it.
- If fetch_page waits with time.sleep, patch cms_export.time.sleep (Concept 5's GOTCHA tells you which name to patch).
- To test main without HTTP, monkeypatch cms_export.fetch_all_entries with a small function that returns two hand-written entries, then check the return code and the CSV in tmp_path.
- If a test passes before you have written the code it tests, it is not testing anything. Expect red first.
## DSA practice (30 min)

Both problems are in day10/dsa.py with signatures, examples and hints. Today, also write a parametrized test for each in day10/test_dsa.py (stretch, not counted in the 15 + 12).

- Valid palindrome. is_palindrome("A man, a plan, a canal: Panama") is True: ignoring case and everything that is not a letter or digit, it reads the same both ways. Hint: either build the cleaned string (the slugify idea from Concept 1) and compare it with its reverse, or walk two indexes inward from both ends and skip characters that do not count. Ask yourself what an empty string should return.
- Binary search. binary_search([1, 3, 5, 8, 13], 8) returns 3, the index, and -1 when the target is missing. The list is sorted. Hint: keep low and high indexes, look at the middle one, and throw away the half that cannot contain the target. Your tests should include an empty list, a one-item list, and the first and last items: off-by-one bugs live there.
## Quiz (3 quick questions)

- Your teammate's test for the CMS export calls the customer's real sandbox API. It passes on their laptop and fails in CI about one run in five. Give two reasons this can happen and describe how you would rewrite the test.
- What is the difference between a fixture that uses return and one that uses yield? Give one FDE situation where you need yield.
- A customer's tech lead asks: "Your tests are all green. How do I know they test anything?" Give two concrete answers.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 10 review": your recap and check-your-understanding predictions next to the real outputs, test_contact_store.py, test_cms_export.py, the finished contact_store.py, the output of python3 -m pytest day10 -v, the three mutation results, dsa.py, the link to the pull request, and your quiz answers. Say which concept felt least natural; tomorrow's recap starts there.

