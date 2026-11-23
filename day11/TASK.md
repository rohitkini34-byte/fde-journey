# Day 11 — Iterators, Generators, Decorators & Context Managers (4 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): retry decorator and streaming export

The scenario: a customer moving off a legacy CMS gives you a JSON Lines export of every entry. Their platform lead says: "The full file is 5 GB and our job runner has 512 MB of memory. Our CMS API also throws 503s during deploys. Show me an exporter that streams, never leaves a half-written CSV, and a retry helper we can put on our API calls."

Before you start: git switch main && git pull, then git switch -c day11. The starters are in day11/: retry.py, stream_export.py, test_day11.py, dsa.py, plus export_sample.jsonl (12 lines with a blank line, two broken lines, drafts and a missing locale) and make_big_export.py (complete, a helper that writes a large fake export). Each function has a comment block with its rules and HINT lines, and a body of raise NotImplementedError("TODO").

Part A, retry.py (45 min). Write backoff_delays() and the decorator factory retry(), then the six retry tests in test_day11.py. Use sleep=waits.append in tests so nothing really waits.

Part B, stream_export.py (95 min). Build the generator stages read_jsonl, only_published, to_rows and batched_rows, the context manager atomic_csv, then run_export and main. Write the six export tests as you go, one stage at a time. Finish with the streaming proof on a 200,000-line file.

```bash
# Streaming proof (acceptance 4): run inside day11/ once the task is done
python3 make_big_export.py big_export.jsonl 200000
# -> wrote 200000 lines to big_export.jsonl (50 MB)
python3 -c "
import tracemalloc
from pathlib import Path
import stream_export as s
tracemalloc.start()  # starts counting every byte Python allocates
r = s.run_export(Path('big_export.jsonl'), Path('big.csv'), 500)
print(r['read'], len(r['bad_lines']), r['published'], r['batches'])
print(tracemalloc.get_traced_memory()[1] // 1024, 'KB peak')
"
# -> 199960 40 180000 360
# -> 577 KB peak      (your number will differ; it must stay under 5 MB)
```

Acceptance criteria:

- python3 retry.py prints exactly the lines shown in its __main__ block, with the retry lines on stderr.
- python3 stream_export.py export_sample.jsonl out.csv prints read: 9, bad lines: [5, 7], published: 6, batches: 2, wrote: out.csv and exits with 0; out.csv has the header and 6 rows, titles stripped, blt010 with locale en-us.
- Every stage in stream_export.py is a generator, and no line calls list() on file data. Calling read_jsonl(...) alone reads nothing.
- The streaming proof above shows a peak under 5 MB. big_export.jsonl and big.csv are in .gitignore, not committed.
- If the export fails halfway, no .tmp file is left and an existing out.csv is unchanged (a test proves it).
- A missing source file prints error: export file not found: ... to stderr and exits with 1; wrong arguments print usage and exit with 2.
- python3 -m pytest day11 -v from the repo root: 12 or more tests (parametrized cases count), all green, and --durations=3 shows nothing at 0.1 s or slower.
- Mutation check (Day 10): remove @functools.wraps, then make retry also retry PermissionError, then remove the blank-line check in read_jsonl. Each time at least one test must go red. Put the code back and note which test caught each bug.
- The work goes in on the branch day11 in at least two commits (retry; streaming export), pushed, with a pull request that has What, Why, How to test and Open items.
Hints (no solutions, try first):

- Start each stage with its test. A generator test can be as small as assert list(only_published([...])) == [...] with two hand-written dicts.
- If you are stuck on the decorator, first write retry without arguments (two layers, like timed), with attempts fixed at 3. Add the outer layer once that works.
- Write the three layers' return lines first (return wrapper, return decorator), then fill in the bodies. Most decorator bugs are a missing return.
- except retry_on as err: works with a tuple of classes, the same as except (A, B):.
- To count records while streaming, a four-line generator that increments a dict value and yields each item is enough. Do not count with len(); generators have no length.
- For atomic_csv, copy the structure of atomic_write from Concept 4 and change only what is opened and what is yielded.
- If the memory check shows tens of MB, search your code for list(, .readlines() or json.load(: one of them is loading the whole file.
## DSA practice (30 min)

Both problems are in day11/dsa.py with signatures, examples and hints. Both are natural generators, so they practise today's main idea.

- Moving average of a stream. moving_average([1, 2, 3, 4, 5], 3) yields 2.0, 3.0, 4.0, the average of each window of 3. The input may be a generator you can read only once. Hint: keep a running total and a collections.deque(maxlen=k); add the new number and subtract the one that falls out, so each step is constant work instead of re-summing the window.
- Flatten a nested list. flatten([1, [2, [3, 4]], [], 5]) yields 1, 2, 3, 4, 5. Hint: for each item, if it is a list, let a recursive call handle it with yield from; otherwise yield the item. Think about why the empty list needs no special case.
## Quiz (3 quick questions)

- A teammate's export does entries = list(read_jsonl(path)) and then loops over entries. It works on the 10 MB sample and is killed in production. Explain why, and what you change.
- Your @retry decorator is on a function that creates an order in the customer's system. The first call times out, but the order was actually created. What goes wrong when you retry, and what would you ask the customer's API team about?
- What is the difference between try/finally written inline and a context manager? Give one reason to prefer the context manager in a codebase you hand over to a customer.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 11 review": your recap answers and check-your-understanding predictions next to the real outputs, retry.py, stream_export.py, test_day11.py, the output of python3 -m pytest day11 -v, the memory check output, the three mutation results, dsa.py, the link to the pull request, and your quiz answers. Say which concept felt least natural; tomorrow's recap starts there.

