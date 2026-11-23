# Day 6 — Virtual Environments, pip, requests & Public APIs (30 Oct)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): day06/cms_export.py

A customer's content team wants every blog post from their headless CMS in a spreadsheet before a migration. Their API is paginated, needs a key and has a flaky server. Build a command-line tool that fetches everything, retries only when that can help, stops with one clear message when it cannot, and writes a clean CSV.

```bash
# day06/ layout for today's task
day06/
    mock_cms.py  # the fake customer CMS (given, do not edit)
    cms_export.py  # YOUR CLI: fetch every entry, write a CSV
    requirements.txt  # YOU create it with pip freeze
    weather_csv.py  # stretch: the same idea against a real public API
    dsa.py  # today's two DSA problems
    day06_notes.ipynb  # runnable examples from this session
    .venv/  # your virtual environment (git ignores it, never commit)
```

Step 1, environment (about 20 min): inside day06/, create and activate .venv, install requests, and write requirements.txt with pip freeze. Select the venv in VS Code.

Step 2, the tool: the starter file gives you the constants, the CmsApiError exception and the CSV column order. You write:

- get_api_key(): read CMS_API_KEY from the environment; raise CmsApiError with the exact message shown below if it is missing.
- fetch_page(session, base_url, content_type, skip, limit, tries=3): one page with include_count=true and a 5-second timeout. Return the JSON on 200. Retry 429/5xx (wait Retry-After seconds if the header is there, else 0.5 s, 1 s, 2 s) and connection errors or timeouts. Any other status raises CmsApiError("HTTP <code>: <error_message>") at once.
- fetch_all_entries(session, base_url, content_type, page_size): the pagination loop, printing page N: K entries per page.
- entry_to_row(entry): one flat dict for the CSV. Missing author becomes "", tags are joined with "|", published becomes "yes"/"no", the title is stripped.
- write_csv(rows, path): create the parent folder, write header and rows, return the row count.
- main(argv=None): argparse with a positional content_type, --out (default <content_type>.csv), --page-size (int, default 3) and --base-url. Return 0, 1 or 2 as shown; errors go to stderr.
```bash
# What a correct run looks like (restart mock_cms.py first)
$ export CMS_API_KEY=demo-key-123  # PowerShell: $env:CMS_API_KEY="..."
$ python cms_export.py blog_post --out output/posts.csv
page 1: 3 entries
  HTTP 503 on skip=3, retrying in 1.0s (attempt 1 of 3)
page 2: 3 entries
page 3: 2 entries
wrote 8 rows to output/posts.csv
```

```bash
# The failure cases: one clear line on stderr, no traceback
$ CMS_API_KEY=wrong python cms_export.py blog_post
error: HTTP 401: Invalid API key  # exit code 1, and NO retry
$ python cms_export.py product
error: HTTP 422: Content type 'product' was not found  # exit code 1
$ python cms_export.py blog_post --base-url http://127.0.0.1:8999
  connection failed on skip=0, retrying in 0.5s (attempt 1 of 3)
  connection failed on skip=0, retrying in 1.0s (attempt 2 of 3)
error: cannot reach http://127.0.0.1:8999 after 3 attempts  # exit 1
$ unset CMS_API_KEY; python cms_export.py blog_post
error: CMS_API_KEY is not set. Run: export CMS_API_KEY=demo-key-123
# exit code 2 (wrong setup, not a server problem)
```

```bash
# output/posts.csv, first lines (long rows cut with ... here)
uid,title,author,tags,word_count,published,updated_at
blt001,Getting started with SSO,Priya Nair,sso|auth,820,yes,...
blt002,"Pricing FAQ: ""Starter"" vs ""Pro"", explained",Rahul Mehta,...
blt003,Draft: Q4 roadmap,,,150,no,2026-10-05T08:15:00Z
```

Acceptance criteria:

- With a freshly restarted mock_cms.py, the run above prints exactly those five lines and exits with code 0 (check with echo $?).
- output/posts.csv has the header line shown, 8 data rows in uid order, the blt002 title correctly quoted, an empty author and tags for blt003, and Renée's name readable.
- The four failure cases print exactly the lines shown (on stderr), exit with the codes shown and never print a traceback. The 401 and 422 cases make exactly one request each: watch the server log.
- Every request has a timeout; there is no bare except: and no except Exception.
- requirements.txt exists in day06/, was made by pip freeze inside the venv, and pins requests. .venv/ is not committed.
- No API key appears anywhere in cms_export.py.
- python -c "import cms_export" run inside day06/ prints nothing.
- Stretch: weather_csv.py writes Mumbai's 7-day forecast to output/forecast.csv with columns date, max_c, min_c.
- Committed and pushed with a meaningful message.
Hints (no solutions, try first):

- Build bottom-up. Write entry_to_row and write_csv first and test them on one hand-written dict; they need no network.
- Concept 4's get_with_retry is the shape of fetch_page. What is new: r.headers.get("Retry-After"), converting connection errors into CmsApiError on the last attempt, and reading error_message from the error body.
- Concept 4's pagination loop is the shape of fetch_all_entries. Count pages with a separate counter; do not compute it from skip.
- Use raise CmsApiError(...) from err so the original cause is kept if you ever need it while debugging.
- In main, catch only CmsApiError, print error: <message> to stderr and return the code. sys.exit(main()) is already written for you at the bottom.
- The mock fails every other request to the skip=3 page. Restart it before checking criterion 1, or your first run may not show the retry line.
## DSA practice (30 min)

- Chunk a list into pages. chunk(items: list, size: int) -> list[list] splits a list into pages of at most size items, the same thing an API does on the server. chunk([1, 2, 3, 4, 5, 6, 7], 3) gives [[1, 2, 3], [4, 5, 6], [7]]; chunk([], 3) gives []; a size below 1 raises ValueError. Hint: range(0, len(items), size) gives the start of each page, and slicing past the end is safe.
- Best time to buy and sell. max_profit(prices: list[int]) -> int: buy on one day, sell on a later day, return the best profit or 0. [7, 1, 5, 3, 6, 4] gives 5 (buy at 1, sell at 6); [7, 6, 4, 3, 1] gives 0. One loop, O(n). Hint: as you walk the list, remember the cheapest price so far and ask what selling today would earn.
## Quiz (3 quick questions)

- What problem does a virtual environment solve, and which file lets a teammate rebuild yours? What are the npm equivalents?
- A nightly export gets a 429 on page 40, and on another night a 401 on page 1. What should your client do in each case, and why are they different?
- Why must every requests call have a timeout=, and what happens without one?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 6 review": your recap answers, your predictions next to the real outputs, cms_export.py, your requirements.txt, the terminal output of the main run and the four failure cases, both DSA solutions and the quiz answers. Include anything finished from Day 4 and Day 5. Tracebacks are welcome; send them with what you tried.

