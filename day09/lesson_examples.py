"""Day 9 lesson examples, in lesson order (rebuilt from the master doc).
Run one section at a time: some need Postgres, a server or files from the original starter zip."""

# ===== section: Concept 1: Paths and the file system =====
# Concept 1: the folder you run FROM vs the folder the script lives IN.
from pathlib import Path

# Path.cwd(): the working directory of the terminal that started us
print("cwd:   ", Path.cwd())
# __file__ is this script's own path; .resolve() makes it absolute
here = Path(__file__).resolve().parent
print("script:", here)

# A relative path is looked up from cwd, NOT from the script's folder
print("relative ok?", Path("server.log").exists())
# Anchored to the script's folder: works from anywhere
print("anchored ok?", (here / "server.log").exists())

# Run 1, from inside day09:   cd day09 && python3 where_am_i.py
# -> cwd:    /Users/rohit/fde-journey/day09
# -> script: /Users/rohit/fde-journey/day09
# -> relative ok? True
# -> anchored ok? True
# Run 2, from the repo root:  python3 day09/where_am_i.py
# -> cwd:    /Users/rohit/fde-journey
# -> script: /Users/rohit/fde-journey/day09
# -> relative ok? False      (it looked for fde-journey/server.log)
# -> anchored ok? True
# REMEMBER: relative paths follow the terminal, not the file.

# ===== section: Concept 2: stdin, stdout, stderr, redirection and pipes =====
# Concept 2: a filter that reads stdin, writes stdout, reports on stderr.
import sys

# sys.argv: the words typed after "python3", like process.argv in Node
wanted = sys.argv[1] if len(sys.argv) > 1 else "ERROR"
kept = 0
for line in sys.stdin:  # one line per loop; works for huge inputs too
    if f" {wanted} " in line:  # spaces avoid matching "ERRORS" etc.
        sys.stdout.write(line)  # line already ends in "\n"
        kept += 1
# The count is a message for the human, not data: it goes to stderr
print(f"kept {kept} {wanted} lines", file=sys.stderr)

# $ python3 only.py WARN < server.log
# -> 2026-11-01T22:00:09Z WARN [sync] slow response status=200 took=3904ms
# -> ... (4 WARN lines)
# -> kept 4 WARN lines
# $ python3 only.py WARN < server.log > warn.txt
# -> kept 4 WARN lines      (stderr still on screen; data is in the file)
# $ python3 only.py ERROR < server.log 2>/dev/null | wc -l
# -> 9                      (wc counted data only, never the message)
# REMEMBER: data to stdout, messages to stderr.

# ===== section: Concept 5: Exit codes, && and || =====
# Concept 5: a preflight check that fails fast, with a useful exit code.
import os
import sys

# The settings this deployment cannot run without
REQUIRED = ["CS_API_KEY", "CS_DELIVERY_TOKEN", "CS_ENVIRONMENT"]

def main() -> int:
    """Return 0 if every required variable is set, else 1."""
    # .get() returns None for a missing variable; "" also counts as missing
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        print("missing: " + ", ".join(missing), file=sys.stderr)
        return 1  # non-zero: the caller (shell, CI, cron) sees a failure
    print("config ok for", os.environ["CS_ENVIRONMENT"])
    return 0

if __name__ == "__main__":
    sys.exit(main())  # the int from main() becomes the exit code

# $ python3 preflight.py; echo "exit: $?"
# -> missing: CS_API_KEY, CS_DELIVERY_TOKEN, CS_ENVIRONMENT
# -> exit: 1
# $ CS_API_KEY=a CS_DELIVERY_TOKEN=b CS_ENVIRONMENT=staging \
#     python3 preflight.py && echo "deploying"
# -> config ok for staging
# -> deploying
# REMEMBER: main() returns the code; sys.exit(main()) hands it over.

# ===== section: Concept 6: Processes, signals and ports =====
# Concept 6: a long-running worker that stops cleanly on Ctrl+C.
import os
import sys
import time

def main() -> int:
    """Tick once a second; on Ctrl+C, clean up and exit with 130."""
    # flush=True prints at once, even when stdout is a pipe or a file
    print(f"worker PID {os.getpid()} started", flush=True)
    try:
        for tick in range(1, 6):
            print(f"tick {tick}", flush=True)
            time.sleep(1)  # pretend to sync one page of entries
    except KeyboardInterrupt:  # Ctrl+C arrives as this exception
        print("Ctrl+C received, saving progress and stopping",
              file=sys.stderr)
        return 130  # 128 + 2 (SIGINT): the standard code for Ctrl+C
    print("all ticks done")
    return 0

if __name__ == "__main__":
    sys.exit(main())

# $ python3 worker.py      (press Ctrl+C after about 3 seconds)
# -> worker PID 547 started
# -> tick 1
# -> tick 2
# -> tick 3
# -> Ctrl+C received, saving progress and stopping
# $ echo $?
# -> 130
