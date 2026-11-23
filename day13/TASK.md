# Day 13 — Async Python: asyncio, async/await, httpx & Concurrency Limits (6 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): day13/async_export.py

The scenario: the customer's content lead says: "The nightly export takes too long and it will be ten times bigger after the migration. Make it faster, but our CMS team says: never more than 3 requests at once per key, or they will block us."

Before you start: git switch main && git pull, then git switch -c day13. Create a venv in day13/ and pip install httpx pytest. Everything else is in the folder.

```bash
# day13/ as you get it
day13/
    mock_cms.py           # the fake customer CMS (given, do not edit)
    cms_common.py         # key, CSV, flags, logging (given)
    sync_export.py        # the sequential baseline (given, read it)
    async_export.py       # YOUR task: 4 TODO functions
    test_async_export.py  # 8 given tests (do not edit)
    dsa.py                # today's two DSA problems
    day13_notes.ipynb     # runnable examples from this session
```

Step 1, measure the baseline (15 min). Start the mock CMS in terminal 1. In terminal 2, export CMS_API_KEY=demo-key-123, run python sync_export.py article and python sync_export.py blog_post, and note the times. Read sync_export.py top to bottom: your fetch_page has the same rules.

Step 2, fetch_page (45 min). Port the retry loop to async. Then run python -m pytest test_async_export.py -q -k fetch_page: four tests should pass.

Step 3, fetch_all_entries (45 min). First page, then the other pages in a TaskGroup, all through one semaphore. Run the remaining tests.

Step 4, export and main (30 min). Wire it together, then run the real thing against the mock CMS and compare with the baseline. Restart mock_cms.py before each timing run, or open http://127.0.0.1:8013/stats?reset=1, so the 503s happen again.

Step 5, the experiment (15 min). Run the article export with --max-in-flight 1, 3 and 10, and check /stats after each. Write the three times and the rejected_429 numbers into your PR description with one sentence explaining the result for 10.

```bash
# What a correct run looks like (times differ a little on your laptop)
$ python sync_export.py article
  2623ms WARNING sync_export: HTTP 503 on skip=12, retrying in 0.5s ...
  6139ms INFO sync_export: fetched 30 entries in 6.1s
$ python async_export.py article
  1643ms WARNING async_export: HTTP 503 on skip=12, retrying in 0.5s ...
  2653ms INFO async_export: fetched 30 entries in 2.6s (max 3 in flight)
  2654ms INFO async_export: wrote 30 rows to output/article.csv
$ curl -s http://127.0.0.1:8013/stats
{"requests": 15, "in_flight": 0, "max_in_flight": 3, "rejected_429": 0}
# The failure cases: one ERROR line, the right exit code, no traceback
$ CMS_API_KEY=wrong python async_export.py blog_post; echo $?
   640ms ERROR async_export: HTTP 401: Invalid API key
1
$ python async_export.py product; echo $?
   649ms ERROR async_export: HTTP 422: Content type 'product' was not found
1
```

Acceptance criteria:

- python async_export.py blog_post --out output/posts_async.csv writes a file identical to sync_export.py's output/blog_post.csv: diff prints nothing.
- python async_export.py article finishes in under 3 s (the baseline needs about 6 s) and logs one WARNING retry line for skip=12.
- After that run, /stats shows "max_in_flight": 3 and "rejected_429": 0. With --max-in-flight 1 it shows 1.
- The CSV rows are in uid order, although pages finish in any order, and you did not sort them.
- Wrong key: one ERROR line HTTP 401: Invalid API key, exit code 1, exactly one request in the mock's log. Unknown type: the HTTP 422 line, exit 1. No key set: the SetupError line, exit 2.
- python -m pytest test_async_export.py -q shows 8 passed.
- async_export.py contains no time.sleep and no import requests, opens one AsyncClient per run, and every request goes through the semaphore.
- python -c "import async_export" prints nothing.
- Work on the branch day13, pushed, with a pull request whose description has What, Why, How to test and your Step 5 numbers.
Hints (no solutions, try first):

- Build fetch_page by changing the sync version in three places, not by starting from a blank page. The rules are identical; only the waiting changes.
- Place async with sem: around the await client.get(...) line only. Then check with -v: the DEBUG start and end lines should show three requests overlapping and never four.
- If max_in_flight in /stats is 1 although you use a TaskGroup, look for an await inside the loop that creates the tasks. Creating a task must not wait for the previous one.
- If it is above 3 or you see 429s with the default settings, check where the semaphore is created. There must be exactly one per export run.
- If a test hangs, you are probably awaiting something inside the semaphore block that also needs the semaphore.
- Run the tests after every function. They are faster than the real server and point at the exact rule you broke.
## DSA practice (30 min)

Both problems are in day13/dsa.py with signatures, examples and hints. Both are about counting what is happening at the same time, the question behind every rate limit.

- Max requests in flight. max_in_flight(intervals) takes (start, end) times of requests and returns the largest number open at the same moment. [(0, 5), (1, 3), (2, 6), (7, 8)] gives 3, and [(0, 1), (1, 2)] gives 1 because a request that ends at 1 is closed when the next one starts at 1. Hint: turn each request into two events, +1 at start and -1 at end, sort them so that an end comes before a start at the same time, and keep a running total.
- First rate-limit violation. first_violation(timestamps, limit, window) takes sorted request times and returns the index of the first request that makes more than limit requests in any window of window seconds, or -1. ([0, 0.2, 0.4, 0.5, 1.3], 3, 1.0) gives 3, and ([0, 1, 2, 3], 1, 1.0) gives -1. Hint: keep a deque of recent times; before adding a time t, drop times that are t - window or older from the left.
## Quiz (3 quick questions)

- In Step 5, --max-in-flight 10 was slower than 3. Explain why, using what the server did and what your retry code did.
- A teammate's fetch_page holds the semaphore during await asyncio.sleep(wait) for retries. Nothing crashes. What gets worse, and when would the customer notice?
- A pull request adds r = requests.get(url, timeout=5) inside an async def that runs in a TaskGroup with 20 other tasks. What happens to those tasks while it waits, and what are two ways to fix it?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 13 review": your recap answers and check-your-understanding predictions next to the real outputs, async_export.py, the output of python -m pytest test_async_export.py -v, the article and blog_post runs with their times, the /stats output for 1, 3 and 10 in flight, both failure cases, dsa.py, the pull request link and your quiz answers. Say which concept felt least natural; tomorrow's review starts there.

