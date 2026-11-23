# Day 22 — HTTP and REST in Depth: Requests, Status Codes, Headers, Idempotency & Pagination (15 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2 hours): day22/api_design.md and curl_drills.sh

Scenario: Acme Retail (the Contentstack customer from Week 3) wants a small content API in front of the Postgres database you modelled on Day 17 (authors, locales, content_entries, entry_locales, tags, entry_tags). Their partner agency will build against it, so the design has to be agreed before any code is written. From tomorrow you build it with FastAPI, so the design you write today is the spec for Days 23 to 27.

Part A (75 min): fill in day22/api_design.md. The starter file has the eleven sections, a worked example row for one endpoint, and hints in each section. It covers: resources and URLs; an endpoint table; request and response examples; the error format; pagination; filtering and sorting; caching and concurrency (ETag, If-Match); idempotency; authentication; versioning; and open questions for the customer.

Part B (45 min): fill in day22/curl_drills.sh. Each of the 10 drills states a goal against mock_api.py (for example "create an entry and print only its Location header"). Write the command under the drill, run it, and record the status code and a one-line explanation in the ANSWER comment.

Acceptance criteria:

- api_design.md has all 11 sections filled in and grep -c TODO api_design.md prints 0.
- The endpoint table has at least 12 rows covering entries, authors, tags, an entry's tags and an entry's locales; each row has method, path, purpose, success code, main error codes and whether it is idempotent.
- Paths use plural nouns only; the only verb is an action sub-resource such as /publish. No GET changes data.
- Each of 401, 403, 404, 409, 412, 422 and 429 appears at least once with the situation that triggers it.
- The example JSON bodies are valid: each one passes python3 -m json.tool when pasted into a file.
- Pagination uses a cursor, with a stated default and maximum page size and the exact response shape.
- At least three open questions for the customer, each one a decision the design depends on.
- bash curl_drills.sh, run against a freshly started mock, executes all 10 drills top to bottom and each prints what its ANSWER comment says.
- Committed and pushed with a message such as "Day 22: REST design and curl drills" (a WIP push counts).
Hints, not answers:

- Start the design from the customer's tasks, not the tables: "the agency lists published blog posts in Hindi", "an editor attaches the tag sale". Each task becomes one row of the endpoint table.
- For each row ask two questions from today: is it safe, and is it idempotent? The answers tell you the method and whether it needs an Idempotency-Key.
- A duplicate slug or a tag that is already attached is a clash with current state: decide between 409 and a quiet success, and write down why.
- For the drills, curl -s -i ... | grep -E "^HTTP|^Location" shows the status line and one header without the body. -w "%{http_code}" with -o /dev/null shows only the code.
- Drill 10 (the busy report endpoint) needs a small shell loop with sleep; your Day 9 notes on exit codes and loops help.
Stretch (only if the core task and the catch-up item are both pushed): day22/api_client.py has three functions to write with requests: list_all() (follow the cursor), create_once() (POST with an Idempotency-Key and one retry) and get_if_changed() (conditional GET with an ETag).

Catch-up (1h): Day 15's schema.sql and queries.sql, until all 10 queries return the expected results on seed.sql. If Day 4 is still open after yesterday, finish it first.

## DSA practice (30 min)

Both problems are in day22/dsa.py with examples and hints. Give each 15 minutes before reading the hints.

- parse_query: turn a query string such as type=blog_post&tag=sale&tag=diwali&q=steel+bottle into a dict of lists: {'type': ['blog_post'], 'tag': ['sale', 'diwali'], 'q': ['steel bottle']}. Practises splitting strings and a dict of lists (Day 3). Hint: what should happen to flag with no =?
- cursor_page: given sorted uids, a cursor (the last uid of the previous page, or None) and a limit, return the page and the next cursor. It must work even when the cursor's uid has since been deleted. Practises binary search (Day 10) and today's cursor idea. Hint: you want the first uid greater than the cursor.
## Quiz (3 quick questions)

- A client's POST /v1/entries times out and the client retries. What can go wrong, and what are two ways the API design can prevent it?
- Which status code fits each case: no API key; a valid read-only key tries DELETE; a valid key asks for a uid that does not exist?
- An export pages through entries while an editor publishes a new one. Why does cursor pagination stay correct when offset pagination does not?
## When you're done

Paste into the Forward Deployment Engineer project chat as Day 22 review: your api_design.md (or a link to it), the curl_drills.sh output, your six predictions with the real results, your quiz answers, dsa.py, and the link to your latest commit. Say how far the Day 15 catch-up got.

