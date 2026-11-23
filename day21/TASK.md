# Day 21 — Weekly Review: Week 3, SQL and Postgres (14 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## DSA practice (30 min)

No new problems this week. Finish the two in day04/dsa.py, which is already in your repo with signatures, examples and hints. If both are done, move on to Day 15's dsa.py (paginate, duplicate slugs).

- Top k words. top_words(text, k). Hint: count with a dict as on Day 3, then sort the (word, count) pairs with one key that puts higher counts first and breaks ties alphabetically. Think about what a tuple key with a minus sign does.
- Balanced brackets. is_balanced(s). Hint: a list works as a stack. Map each closing bracket to its opening one, and ask what must be true about the stack when the loop ends.
## Quiz (3 quick questions)

- A content lead asks for the number of published entries per locale each day, including locales with zero. Which Week 3 tools do you combine, and in what order?
- Your nightly loader crashes at row 4,000 of 5,000. What two things from Week 3 mean the database is not left half-loaded and that running it again is safe?
- A product owner says "looking up an entry by slug is slow". What do you do before you add an index, and how do you prove the index helped?
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 21 review": your checklist with yes or no on each line, your recap answers, your seven predictions next to the real outputs, the link to your latest commit (Day 4 finished, Day 15 files in), your quiz answers, and how many hours a day you can really study next week. Then run the SQL mock in the same chat.

