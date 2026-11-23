# Day 14 — Weekly Review: Week 2, Python for Production (7 Nov)

Rebuilt from the master Google Doc. Original starter files and given tests were sent as zips by the daily runs and are not included here.

## DSA practice (30 min)

No new problems. Finish the two in day04/dsa.py, which is already in your repo with the signatures, examples and hints.

- Top k words. top_words(text, k). Hint: count with a dict as on Day 3, then sort the (word, count) pairs with one key that puts higher counts first and breaks ties alphabetically. Think about what a tuple key with a minus sign does.
- Balanced brackets. is_balanced(s). Hint: a list works as a stack. Map each closing bracket to its opening one, and ask what must be true about the stack when the loop ends.
## Quiz (3 quick questions)

- A customer asks whether your CMS exporter can run every night in their CI pipeline. Name three things from Week 2 that let you say yes.
- You notice that a pull request merged yesterday added a .env file holding the customer's API key. What do you do, in order?
- Explain to a non-technical product owner, in two sentences, why the exporter sends at most 3 requests at a time even though 10 would look faster.
## When you're done

Paste into the Forward Deployment Engineer project chat as "Day 14 review": your checklist with yes or no on each line, your recap answers, your predictions next to the real outputs, the link to your latest commit (Day 4 finished, Day 5 to 13 folders in), the new README top section, your quiz answers, and how many hours a day you can really study for the next two weeks. Then run the coding mock in the same chat.

