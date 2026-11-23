# Day 29 — Restart: Push Your Work, Finish Day 4 & Your First pytest File (22 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 3 hours): push, Day 4 green, status

Your starter files are in day29/ in the repo: test_day04.py (the tests), pytest.ini (lets them import day04/), dsa.py (DSA checks) and status.md (the table to fill). Pull first: git pull origin main.

Part A: push everything you have (30 min).

- Run the three Concept 1 steps. Write down what git status said before you changed anything; it goes in your review.
- For each day from 5 to 28 that you have locally, or as a zip, add its folder and commit it, oldest first.
- Add the .gitignore, push, and check github.com shows today's date on the latest commit.
Part B: make Day 4 green (2 hours).

- cd day29 and run python -m pytest -q. Expect 21 failed. Read one failure report in full.
- Implement validate_contact() in day04/contact_store.py. Run with -k validate until only your own TODO test is red. Commit and push.
- Then load_contacts() and save_contacts() (-k "load or save"), then import_contacts() and merge_contacts(), then main() in day04/main.py. Commit and push after each one.
- Run python day04/main.py twice from the repo root and compare with its docstring. Then break day04/data/contacts.json (delete its last line), run again and check echo $? prints 1.
Part C: your 3 tests and status.md (30 min).

- Write the three TODO tests at the bottom of test_day04.py.
- For each one, break the rule it checks in contact_store.py, watch it go red, and undo the break.
- Fill in every row of status.md and the summary, then commit and push.
Acceptance criteria

- Inside day29/, python -m pytest -q prints 21 passed.
- The 18 given tests are unchanged: git diff on test_day04.py shows changes only in your three test bodies.
- python day04/main.py matches its docstring on the first and second run; a broken store prints one line starting with "error:" and exits with code 1, with no traceback.
- Each of your three tests fails when you break the rule it checks.
- day29/status.md has a status word and evidence on all 29 rows, and the summary is filled in.
- After a test run, git status is clean: no .venv/, __pycache__/, .pytest_cache/ or day04/data/ waiting to be added.
- At least one commit per finished function, all pushed to main.
Hints (no solutions)

- validate_contact(): the order of the checks decides which message a record gets. Follow the order of the Rules comment: name, email @, email domain, city, tags. For the domain, look only at the text after the "@"; str.partition() or split("@", 1) gives it to you.
- Tags: a set removes duplicates, and sorted() turns any collection back into a sorted list.
- load_contacts() has three outcomes: no file, broken file, good file. Write the test case for each in your head first, then the try, the two except branches and the shape check.
- import_contacts(): ask which error family main() catches. A missing import file must arrive there as a member of it.
- When a test fails, read the lines starting with E first. pytest shows what your code returned next to what the test expected.
- Stuck for more than 20 minutes on one function? Commit what you have with a "WIP:" message, push, move to the next one, and say so in the review.
## DSA practice (30 min)

No new problems this week. Finish the two in day04/dsa.py, then run python dsa.py inside day29/, which checks them against 8 fixed cases, including a tie, an oversized k and a punctuation-only text.

- Top k words. Build the counts first, then sort the pairs once. Ask what key makes Python sort by count high to low and, for equal counts, by word A to Z. A tuple key can do both.
- Balanced brackets. A list works as a stack. Write down by hand what the stack holds after each character of "([)]"; the place where your trace and the rule disagree is where the check belongs.
- Then fill in my_edge_cases() with four cases of your own, expected values worked out by hand, until it prints all 12 checks passed.
## Quiz (3 quick questions)

- Your import loop uses except Exception as err instead of except InvalidContactError as err, and validate_contact() has a typo, emial. What does the run print, and why is that worse than a crash?
- Why does test_main_first_and_second_run call monkeypatch.setattr(main, "STORE_PATH", ...)? What would happen on your laptop without it?
- A teammate's status says "Days 5 to 10: mostly done". Rewrite it as status lines, and name the evidence you would ask for.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 29 review": what git status showed before Part A, the link to your latest commit, the last line of your pytest run, your three tests, your status.md, your six predictions next to the real output, your recap and quiz answers, and the hours you really studied today.

