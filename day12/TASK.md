# Day 12 — Project Structure, pyproject.toml & uv, Logging, ruff & mypy (5 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): the cms-export package

The scenario: a customer's platform lead says: "Our content migration runs on one script that only works on Priya's laptop. It prints to the console, crashes on some exports, and nobody can install it on the job runner. Make it something any engineer can install with one command, that logs properly into our log platform (we collect stderr), and that our CI can lint and type check."

Before you start: git switch main && git pull, then git switch -c day12. In day12/ you get the customer's script legacy_cms_export.py (it works; read it, do not edit it), the sample export_sample.jsonl (9 lines: one blank, one broken, a draft, an archived entry and one entry with no locale) and the starter project cms-export/. Every function you write has a comment block with its rules and HINT lines, and a body of raise NotImplementedError("TODO"). The two test files are given; do not edit them.

```bash
# day12/ as you get it (git pull on main first)
day12/
    legacy_cms_export.py     # the customer's script: read, do not edit
    export_sample.jsonl      # 9 lines: blank, broken, draft, archived...
    dsa.py                   # today's two DSA problems
    day12_notes.ipynb        # runnable examples from this session
    cms-export/              # YOUR project (Part A makes it one)
        .gitignore           # given: .venv/, dist/, out/ and caches
        src/cms_export/      # __init__, __main__, py.typed given;
                             # cli, reader, transform, writer and
                             # logging_setup are starters with TODOs
        tests/               # 2 given test files + data/ sample

# Part A, starting from the repo root
$ cd day12/cms-export
$ uv init --package          # adds pyproject.toml, README, .python-version
$ uv add --dev pytest ruff mypy
$ uv run pytest -q           # red at first: every TODO raises
# -> 10 failed, 1 passed   (the ExportStats test: it is given)
```

Part A, make it a project (30 min). Inside day12/cms-export/ run uv init --package; it adds pyproject.toml, README.md and .python-version and leaves the starter files alone. Then edit pyproject.toml: a real description, requires-python = ">=3.12", the script line pointing at cms_export.cli:main, and the [tool.ruff], [tool.ruff.lint] and [tool.mypy] tables from Concepts 5 and 6, with strict = true and files = ["src"] under mypy. Check that uv run python -c "import cms_export" prints nothing.

Part B, port the logic with types (60 min). Read the legacy script once, top to bottom, and write down its problems (you should find at least six). Then fill in transform.py, reader.py and writer.py. Port the behaviour, not the bugs: no globals, no print, no bare except, and a header row even when nothing is published. Run uv run pytest tests/test_transform.py after each function.

Part C, logging and the command (40 min). Write level_for and configure_logging, then build_parser, published_rows and main in cli.py. Run the command on the sample and compare with the expected output below.

Part D, quality gates and install (20 min). Make uv run ruff check, uv run ruff format --check and uv run mypy pass. Add at least three tests of your own in tests/test_mine.py: a parametrized test for level_for, one proving that -v logs "skipping blt003: status draft", and one for write_csv with zero rows. Then build the wheel and install it into a fresh venv outside the project.

```bash
# What a correct run looks like (inside day12/cms-export). Each log line
# starts with a time such as 2026-11-05T08:00:01, cut here to fit.
$ uv run cms-export ../export_sample.jsonl out/posts.csv
# -> WARNING cms_export.reader: skipping line 6: Expecting ',' delimiter
# -> WARNING cms_export.transform: blt006 has no locale, using en-us
# -> INFO cms_export.cli: read 7 entries, 5 published, bad lines: [6]
# -> INFO cms_export.cli: wrote 5 rows to out/posts.csv
$ uv run cms-export -v ../export_sample.jsonl out/posts.csv
# -> adds DEBUG cms_export.cli: skipping blt003: status draft
# -> and  DEBUG cms_export.cli: skipping blt007: status archived
$ uv run cms-export -q ../export_sample.jsonl out/posts.csv
# -> only the two WARNING lines
$ uv run cms-export missing.jsonl out.csv; echo $?
# -> ERROR cms_export.cli: export file not found: missing.jsonl
# -> 1
$ uv run python -m cms_export --version
# -> cms-export 0.1.0

# Part D: build, then install into a fresh venv OUTSIDE the project
$ uv build
# -> Successfully built dist/cms_export-0.1.0-py3-none-any.whl
$ uv venv ~/fresh-venv
$ uv pip install --python ~/fresh-venv dist/cms_export-0.1.0-py3-none-any.whl
$ ~/fresh-venv/bin/cms-export --version   # Windows: Scripts, not bin
# -> cms-export 0.1.0
```

Acceptance criteria:

- uv run cms-export ../export_sample.jsonl out/posts.csv writes the four log lines shown to stderr (your timestamps differ), nothing to stdout, and exits with 0. out/posts.csv has the header and 5 rows (blt001, blt002, blt004, blt006, blt008), titles stripped, blt006 with locale en-us.
- -v adds the two DEBUG skipping lines; -q shows only the two WARNING lines; a missing source file logs ERROR export file not found: ... and exits with 1; no arguments prints usage and exits with 2; --version prints cms-export 0.1.0, read from the package metadata.
- uv run python -m cms_export ... behaves exactly like the cms-export command.
- uv run pytest: the 11 given tests plus at least 3 of yours, all green.
- uv run ruff check, uv run ruff format --check and uv run mypy (strict, on src) all pass, with no noqa or type: ignore comments.
- No print( anywhere in src/, no module-level mutable state, and only cli.py calls configure_logging.
- uv build makes a wheel, and after installing it into a fresh venv outside the project, cms-export --version works there.
- pyproject.toml and uv.lock are committed; .venv/, dist/ and out/ are not (the given .gitignore covers them).
- The work is on the branch day12 in at least two commits (project skeleton; port with logging and checks), pushed, with a pull request that has What, Why, How to test and your list of legacy problems.
Hints (no solutions, try first):

- Work in the order the modules import each other: transform first (it imports nothing of yours), then reader and writer, then cli. That is also the dependency direction from Concept 1.
- If uv run cms-export fails with ModuleNotFoundError or "cannot import name main", check the [project.scripts] line, then run uv sync again: commands are created at install time.
- If the CLI tests see no log lines, read the GOTCHA at the end of Concept 4 again, then look at how you set the level.
- If mypy reports an error you do not understand, put reveal_type(...) on the line above, run mypy again, and remove it afterwards.
- The pipeline is lazy: nothing is read until write_csv pulls rows through it. Log the summary after write_csv returns, or every count will be 0.
- Before you finish, search src/ for print( and for basicConfig. Each should appear exactly where the acceptance criteria allow, and nowhere else.
## DSA practice (30 min)

Both problems are in day12/dsa.py with signatures, examples and hints. Both split a string into parts and compare the parts, the pattern behind every version check and log parser.

- Compare versions. compare_versions("1.10.0", "1.9.3") returns 1, ("0.11.32", "0.12.0") returns -1, and ("2.0", "2.0.0") returns 0. Hint: comparing the strings directly gets 1.10 against 1.9 wrong; split on dots, convert each part to int, and treat a missing part as 0.
- Common package prefix. common_package(["cms_export.reader", "cms_export.cli"]) returns "cms_export", and ["a.b.c", "a.b.d", "a.b"] gives "a.b". Hint: split each name on dots, then walk position by position with zip(*parts) and stop at the first position where the parts differ. Whole parts only: "reader" and "readers" share nothing.
## Quiz (3 quick questions)

- A teammate adds logging.basicConfig(level=logging.DEBUG) at the top of reader.py "so the debug lines show". What goes wrong for the customer's application that imports your package, and where should that line live?
- The customer's CI runs pip install -r requirements.txt with no versions pinned, and a deploy broke after a dependency released a new version. What do you change in your project, and which command should their CI run?
- mypy reports Item "None" of "str | None" has no attribute "upper". Explain the error in one sentence, give two ways to fix it, and say which you prefer for data coming from a customer's CMS.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 12 review": your recap answers and check-your-understanding predictions next to the real outputs, your pyproject.toml, the five module files and tests/test_mine.py, the output of uv run pytest -v, uv run ruff check and uv run mypy, the cms-export --version run from the fresh venv, your list of legacy problems, dsa.py, the pull request link and your quiz answers. Say which concept felt least natural; tomorrow's recap starts there.

