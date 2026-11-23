# Day 9 — Terminal and Shell for Engineers: Paths, Pipes, grep, Environment Variables, Exit Codes, Processes & Ports (2 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): day09/log_report.py

The scenario: a customer runs a nightly Contentstack sync, a webhook listener and a CSV export on one server, all writing to one log. Their on-call engineer wants a command that summarises last night's log and fails loudly when there were errors, so their cron can send an alert. day09/server.log is a real-shaped sample: 37 lines, including a blank line, a log-rotation marker and a line with a mistyped level.

Before you start: git switch main && git pull, then git switch -c day09-log-report. The starters are in day09/: drills.sh, log_report.py, dsa.py and server.log.

Part A, drills.sh (30 min). Six questions about server.log, one shell one-liner each, written into the TODO lines of drills.sh. Run it with bash drills.sh from inside day09/. The answers your commands print are in the file's comments, so you can check yourself; the commands are yours to find.

Part B, log_report.py (100 min). Complete the four functions in the starter: parse_line, summarize, format_report and main. The output for the sample log must look like this:

```bash
# Part B: the target. Run from inside day09/.
python3 log_report.py < server.log; echo "exit: $?"
# stderr (the warnings come first):
# -> warning: line 23: malformed, skipped
# -> warning: line 30: malformed, skipped
# stdout:
# -> Log report
# ->   lines read: 37
# ->   parsed:     34
# ->   skipped:    3
# -> By level:
# ->   ERROR  9
# ->   WARN   4
# ->   INFO   19
# ->   DEBUG  2
# -> Errors by component (top 3):
# ->   webhook  4
# ->   sync     3
# ->   export   2
# -> First error: 2026-11-01T22:00:11Z
# -> Last error:  2026-11-01T22:45:00Z
# -> exit: 1
```

Part C, use it like a real tool (20 min). Prove it works in pipelines: run the acceptance checks below, then commit in at least three commits (drills; parser and summary; report and exit codes), push and open a pull request with What, Why, How to test and Open items.

Acceptance criteria:

- bash drills.sh prints six answers that match the expected values in the file's comments.
- python3 log_report.py < server.log prints exactly the report above on stdout, and the two warnings on stderr only: python3 log_report.py < server.log 2>/dev/null shows no warning lines.
- The blank line is skipped silently; malformed lines (wrong number of fields, unknown level, component without brackets) are skipped with a warning that names the line number. The script never crashes on them.
- Exit code 1 when there is at least one ERROR, 0 when there is none: grep -v ERROR server.log | python3 log_report.py; echo $? prints 0.
- python3 log_report.py --top 2 < server.log shows two components; --top 0 and --top abc print a usage error and exit with 2.
- Run with no input (just python3 log_report.py in a terminal), it does not hang: it prints a one-line usage hint to stderr and exits 2.
- cat server.log | python3 log_report.py and python3 day09/log_report.py < day09/server.log (from the repo root) both work.
- Pressing Ctrl+C while it waits for input exits with 130 and no traceback.
- The pull request is open (or merged) with at least three commits, and the Day 8 pull requests are merged before it.
Hints (no solutions, try first):

- line.split(maxsplit=3) splits on any run of spaces, at most three times, so the message keeps its own spaces. Count the parts before you unpack them.
- enumerate(sys.stdin, start=1) gives you (line_number, line) pairs, which is what the warnings need.
- The top-N list is Day 3's counting dict plus Day 4's sorted(..., key=...). Break ties alphabetically so the output is stable.
- sys.stdin.isatty() is True when nobody piped anything in and the script would wait for the keyboard.
- For --top 0, argparse cannot know that 0 is wrong. After parse_args(), call parser.error("..."): it prints usage and exits with 2 for you.
- Test exit codes by hand first: python3 log_report.py < server.log > /dev/null 2>&1; echo $? should print 1.
- Stuck on output alignment? f-strings pad text: f"{name:<8}" makes name at least 8 characters wide, left-aligned.
## DSA practice (30 min)

Both problems are in day09/dsa.py, with signatures, examples and hints.

- Longest error streak. longest_streak(levels, target) returns the length of the longest run of target in a row. longest_streak(["INFO", "ERROR", "ERROR", "WARN", "ERROR"], "ERROR") gives 2. Hint: walk the list once, keeping the current run length and the best so far; decide what happens to the current run when a different value appears. It is the check an alerting rule does for "5 errors in a row".
- Simplify a path. simplify_path("/home/rohit/../rohit/./fde//day09/") gives "/home/rohit/fde/day09", the same answer cd and Path.resolve() would give. Hint: split on /, ignore empty parts and ., and use a list as a stack (Day 4's brackets problem): a folder name is pushed, .. pops, but never pops past the root.
## Quiz (3 quick questions)

- A cron job runs python3 export.py > export.log every night, and the file has no error messages even on nights when the export failed. Give two reasons this can happen and the fix for each.
- You pip install requests and then python3 cms_export.py still fails with ModuleNotFoundError: requests. Which two commands do you run first, and what are you looking for?
- Your FastAPI server will not start: "Address already in use". Describe the three steps to fix it safely, with the commands.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 9 review": your recap and check-your-understanding predictions next to the real outputs, drills.sh, log_report.py with the output of python3 log_report.py < server.log; echo $?, dsa.py, the link to today's pull request (and the two Day 8 ones), and your quiz answers. Say which concept felt least natural; that is where tomorrow's recap will start.

