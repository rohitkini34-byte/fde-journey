# Day 8 — Git Properly: Commits, Branches, Pull Requests & Rebase (1 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## Hands-on task (about 2.5 hours): Days 5 and 6 into main through two pull requests

Treat fde-journey like a customer repo: nobody commits to main directly; every change arrives through a branch and a reviewed PR. You are the author today, and also the reviewer.

Before you start: the Day 5 and Day 6 files come from those days' sessions: the starter files that came with them (support_ticket.py, tickets_export.json, mock_cms.py, cms_export.py and both dsa.py files) plus whatever you have written. If you no longer have the starters, say so in the project chat before you begin. Unfinished code is fine: commit what you have and list what is missing under Open items. Finishing the code is not today's goal; getting it reviewed and merged properly is.

Step 0, setup (15 min). Fix your identity so new commits link to your GitHub profile, install gh, and update main (it now holds today's day08/ starters).

```bash
# Step 0: run once on your Mac
git config --global user.name "Rohit Kini"
# Use the email on your GitHub account, or the private noreply address
# from GitHub > Settings > Emails (it looks like 12345+name@users...)
git config --global user.email "you@example.com"
git config --global core.editor "code --wait"  # commit messages in VS Code
brew install gh && gh auth login
cd ~/path/to/fde-journey  # your clone
git switch main && git pull  # get today's day08/ folder
git log -1 --format="%an <%ae>"  # the old commit keeps the old email
```

Step 1, PR 1: Day 5 (45 min).

- From an up-to-date main, create day05-support-ticket.
- Add day05/ in at least three commits, one logical piece each (for example: the starter files and data; your dataclass and validation; the queue, loader and dsa.py). Fill row 5 of the README's Files column in a commit of its own.
- Push with -u and open the PR with a filled-in pr.txt.
- Do not merge it yet.
Step 2, PR 2: Day 6 (45 min).

- Switch back to main (PR 1 is not merged, so main has no day05/) and create day06-cms-export from it.
- First commit: extend the repo's .gitignore with the missing rules from Concept 3 (.env, output/, day04/data/ and the caches). Check it with git check-ignore -v.
- Add day06/ in at least three commits, with requirements.txt but never .venv/, .env or output/. Fill README row 6 in its own commit.
- Push and open PR 2. If cms_export.py is not finished, open it as a draft.
Step 3, merge, rebase, conflict (45 min).

- On GitHub, read PR 1's "Files changed" as a reviewer, leave yourself at least one comment, then merge it with "Create a merge commit" and delete the branch.
- Locally: git switch main && git pull, then switch to day06-cms-export and git rebase origin/main. The README rows 5 and 6 sit next to each other, so expect a conflict. Resolve it so both rows are filled, git add README.md, git rebase --continue.
- Push with --force-with-lease. Mark PR 2 ready (if it was a draft and the code works), then merge it with "Rebase and merge" and delete the branch.
- git switch main && git pull, then git branch -d both local branches.
Step 4, repo_check.py (30 min). On a branch day08-repo-check, complete day08/repo_check.py and day08/dsa.py from the starters, run python day08/repo_check.py from the repo root, and bring them in through a third, small PR.

Acceptance criteria:

- GitHub shows PR 1 (Day 5) and PR 2 (Day 6) as merged, each with a description that fills What, Why, How to test and Open items.
- Each of the two PRs has at least three commits, and every new subject passes repo_check.py's rules: 50 characters or fewer, capital first letter, imperative, no full stop, at least three words.
- git log --oneline --graph on main shows PR 1's merge commit, with PR 2's commits after it in a straight line.
- git ls-files | grep -E "(^|/)(\.env|\.venv|__pycache__|output)(/|$)" prints nothing, and git check-ignore -v .env prints the rule that ignores it.
- README rows 5 and 6 list their files, and git grep -n "<<<<<<<" prints nothing (no conflict markers left anywhere).
- Your new commits show your GitHub avatar, because the author email matches your account.
- python day08/repo_check.py prints the report and flags your old "Day 4" subject as too short, and nothing you committed today.
- git status on main says "Your branch is up to date with 'origin/main'", and the merged branches are deleted locally and on GitHub.
Hints (no solutions, try first):

- Before every commit, run git status and git diff --staged. If you see .venv, .env or output in the list, stop and fix .gitignore first.
- To make three commits from files that already exist, stage them in groups: git add day05/tickets_export.json day05/dsa.py, commit, then the next group. Use git add -p when one file holds two logical pieces.
- If the rebase conflict confuses you, run git status: it names the file and tells you the next command. git rebase --abort is always a safe way back.
- If a push is rejected after the rebase, that is expected; read Concept 6 again before you reach for a force push.
- repo_check.py uses subprocess.run, which is new; the starter's hints show the exact call. It runs git the same way you type it in the terminal and hands back the printed text.
- If you commit to main by accident before pushing: git branch my-work keeps the commit on a new label, then git reset --hard origin/main moves main back. Check git log --oneline --all before and after.
## DSA practice (30 min)

Both problems are in day08/dsa.py, with signatures, examples and hints.

- Merge two sorted lists. merge_sorted(a, b) returns one sorted list without calling sorted(). merge_sorted([1, 4, 9], [2, 3, 10, 12]) gives [1, 2, 3, 4, 9, 10, 12]. Hint: keep one index into each list, always take the smaller front item, and think about what is left over when one list runs out. This is the core step of merge sort, and the same "walk two sorted streams" idea Git uses to compare histories.
- First bad commit. first_bad(versions, is_bad) returns the first version for which is_bad(version) is True, or None, calling is_bad as few times as possible. It is what git bisect does to find the commit that broke a build. Hint: once a version is bad, every later one is bad too, so check the middle and throw away half the list each time (binary search). Eight versions need at most four checks.
## Quiz (3 quick questions)

- A teammate pushed .env with a customer's CMS key to a public repo, then removed it in the next commit. Is the key safe now? What do you do, in what order?
- When would you merge main into your branch, and when would you rebase your branch onto main? State the golden rule.
- Explain to a customer's non-technical project manager, in two sentences, what a pull request is and why you open one before changing their system.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 8 review": the links to your two PRs, the output of git log --oneline --graph -n 15 on main, your final .gitignore, your recap and check-your-understanding predictions next to the real outputs, repo_check.py, dsa.py and your quiz answers. Say which step was hardest; that is where tomorrow's recap will start.

