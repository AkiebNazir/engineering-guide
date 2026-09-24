# Review Ledger 🔁

Companion to `master_dsa_plan.md` §10. This is the file that turns *"I solved 150 problems"* into *"I can solve 150 problems."*

---

## How this works

Every problem you solve gets a row. You re-solve it **cold** at four intervals:

```
solve ──► D+1 ──► D+3 ──► D+10 ──► D+30 ──► [★] mastered
            │       │        │        │
            └───────┴────────┴────────┴──► fail? reset to D+1
```

**Cold means cold:** blank file, no notes, no previous solution open, 20-minute timer, narrated out loud.

**Marking a re-solve:**

| Mark | Meaning |
|:---:|---|
| `✅` | Solved cold, correct on first run, within 20 min |
| `⚠️` | Solved, but slow (>20 min) or needed a run to find a bug → **repeat this same interval** |
| `❌` | Couldn't solve it → **reset the whole row to D+1** |

A row that clears all four moves to [Mastered](#mastered-). A row marked `❌` twice in a row means the *pattern* is weak, not the problem — go re-drill that whole ladder in `master_dsa_plan.md` §4.

**Budget:** ~5 hrs/week, roughly 45 min/day. If the due list ever exceeds that, clear oldest-first and let the rest slip a day. Never skip review to add new problems — that trade always loses.

---

## Due this week

> Update every Sunday during the weekly retro.

**Week 1 (Sep 7–13, 2026) — baseline audit.** Everything below was solved before this plan existed, so its retention is unknown. Re-solve each one cold to establish a real starting line. Anything that fails goes into the normal ladder; anything that passes jumps straight to D+10.

- [ ] Subsets (Py + Go)
- [ ] Permutations (Py)
- [ ] Palindrome — recursive two-pointer (Py + Go)
- [ ] Reverse Linked List — iterative *and* recursive (Py)
- [ ] Fibonacci, Factorial (Py + Go) — *fast, just confirm*

---

## Active ledger

| Problem | Pattern | Solved | Help? | D+1 | D+3 | D+10 | D+30 |
|---|---|:--:|:--:|:--:|:--:|:--:|:--:|
| Subsets | Backtracking — include/exclude | pre-plan | – | | | | |
| Permutations | Backtracking — choose available | pre-plan | – | | | | |
| Palindrome (recursive) | Recursion + two pointers | pre-plan | – | | | | |
| Reverse Linked List | Pointer rewiring | pre-plan | – | | | | |
| Fibonacci | Branching recursion | pre-plan | – | | | | |
| Factorial | Linear recursion | pre-plan | – | | | | |
| Doubly Linked List | Structure implementation | pre-plan | – | | | | |
| | | | | | | | |

**Help?** — `no` if you solved it unaided, `hint` if you took the 25-minute hint, `full` if you needed the solution. `full` rows are the ones that bite you in week 12; watch them.

### Date helper

For a problem solved on day **D**, fill the columns with actual dates so nothing silently slips:

| Solved | D+1 | D+3 | D+10 | D+30 |
|---|---|---|---|---|
| Sep 7 | Sep 8 | Sep 10 | Sep 17 | Oct 7 |
| Sep 14 | Sep 15 | Sep 17 | Sep 24 | Oct 14 |
| Sep 21 | Sep 22 | Sep 24 | Oct 1 | Oct 21 |
| Sep 28 | Sep 29 | Oct 1 | Oct 8 | Oct 28 |
| Oct 5 | Oct 6 | Oct 8 | Oct 15 | Nov 4 |
| Oct 12 | Oct 13 | Oct 15 | Oct 22 | Nov 11 |
| Oct 19 | Oct 20 | Oct 22 | Oct 29 | Nov 18 |
| Oct 26 | Oct 27 | Oct 29 | Nov 5 | Nov 25 |
| Nov 2 | Nov 3 | Nov 5 | Nov 12 | Dec 2 |
| Nov 9 | Nov 10 | Nov 12 | Nov 19 | *past target* |
| Nov 16 | Nov 17 | Nov 19 | Nov 26 | *past target* |

> Problems solved after **Nov 9** won't complete a full D+30 cycle before the 7 Dec target. That's expected — for those, D+1/D+3/D+10 plus a Week 13 pass is the realistic bar.

---

## Mastered ⭐

Cleared all four intervals cold. Promote the `[x]` to `[★]` in `master_dsa_plan.md` when a problem lands here.

| Problem | Pattern | Date mastered |
|---|---|:--:|
| | | |

**Count: 0 / 150** — target is ≥80 by end of Week 12.

---

## Pattern journal

One line per problem, written *immediately* after solving. Record the **trigger you should have spotted** and the technique — never the code. The code you can re-derive; the trigger is the thing you're actually training.

> Format: `Problem — "signal in the statement" → technique`

- _Subsets — "all possible combinations, order doesn't matter" → include/exclude recursion on index_
- _Permutations — "all possible orderings" → backtrack over unused elements, `used` set_
-

---

## Mock interview log

Weeks 11–13, two per week minimum. See `master_dsa_plan.md` §9.

| # | Date | Problem / pattern | Time to identify | Solved? | Comms 1–5 | The one thing to fix |
|:--:|---|---|:--:|:--:|:--:|---|
| 1 | | | | | | |
| 2 | | | | | | |
| 3 | | | | | | |
| 4 | | | | | | |
| 5 | | | | | | |
| 6 | | | | | | |

**Comms scale:** 1 = long silences, coded before explaining · 3 = explained the approach, went quiet while coding · 5 = narrated throughout, stated complexity before coding, caught own bugs in a dry run.

Two consecutive mocks failing the same way → back to §4 and re-drill that pattern's full ladder.
