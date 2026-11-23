# Day 7 — Weekly Review: Week 1, Python Basics (31 Oct)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## DSA practice (30 min)

No new problems today. Finish the two open ones in day04/dsa.py; the starter file has the signatures, examples and hints.

- Top k words. top_words(text, k). Hint: count with a dict as on Day 3, then sort the (word, count) pairs with a key that puts higher counts first and breaks ties alphabetically. A tuple key such as (-count, word) does both at once.
- Balanced brackets. is_balanced(s). Hint: a list works as a stack (append to push, pop to take the last item). Keep a dict that maps each closing bracket to its opening one, and ask what must be true when the loop ends.
## Quiz (3 quick questions)

- A customer's nightly export crashes on one record with a KeyError, and the whole night's run is lost. Name two things from this week that would have prevented the lost run.
- When would you model a CMS entry as a dataclass instead of a plain dict, and when is a dict fine?
- Explain to a non-technical content manager, in two sentences, why the export "fails with 401" and what they need to do about it.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 7 review": your checklist with yes or no on each line, your recap answers, your predictions next to the real outputs, Day 4's contact_store.py, main.py and dsa.py, the quiz answers and the link to your LinkedIn post. Then run the behavioral mock in the same chat.

