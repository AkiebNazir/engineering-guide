# Running the 45-Minute Coding Round

This file is about *performing* what you know, not learning new CS concepts — it
applies whether this is your first technical interview or your tenth, at any level.
Knowing algorithms is necessary but not sufficient. Interviewers write feedback on
**four things**: communication, problem solving, code quality, and verification
(testing your own code). An optimal answer reached silently, with sloppy code and no
testing, can still come back as a weak rating. At L5 there's a fifth, implicit
signal: **did you drive it, or did the interviewer drag you through it?**

This file is the execution layer: the timeline, a clarifying-question list you can use until it's automatic, the edge-case checklist, how to think out loud, how to use hints, how to recover when stuck, and how to verify code without running it.

## 1. What Each of the Four Signals Looks Like

| Signal | Strong evidence | Weak evidence |
|---|---|---|
| **Communication** | Restates the problem; explains the idea before coding; narrates decisions, not keystrokes; checks in at transitions | Long silences; codes immediately; talks nonstop without structure |
| **Problem solving** | States brute force with complexity, improves it with a reason, names the pattern, weighs two approaches, reacts to hints quickly | Jumps to a memorized solution that doesn't fit; can't explain why it works; stuck without trying smaller cases |
| **Code quality** | Helper functions with clear names; no magic numbers; handles edge cases explicitly; idiomatic language use; readable in a Google Doc | One 60-line function; `a`, `b`, `tmp`; copy-pasted blocks; clever one-liners nobody can review |
| **Verification** | Traces a real example line by line; tests edge cases; finds and fixes own bugs before the interviewer points them out; states complexity accurately | Says "done" without tracing; interviewer finds the bugs; wrong complexity |

**Leveling:** a correct solution that needed heavy guidance reads as L4. The same solution that you scoped, drove, and verified yourself reads as L5.

## 2. The Timeline

| Minutes | Phase | What you do | Output |
|---|---|---|---|
| 0–5 | **Clarify** | Restate. Ask about input size, ranges, negatives, duplicates, empty input, sortedness, output format, whether you can modify the input. Work one small example by hand. | Agreed problem + example |
| 5–12 | **Design** | State brute force and its complexity. Improve it; name the pattern and WHY it applies. State time and space. **Get agreement before coding.** | Agreed approach |
| 12–30 | **Code** | Write clean code top-down: main function calling well-named helpers. Narrate key decisions briefly. | Complete code |
| 30–38 | **Verify** | Trace your example line by line, then 2–3 edge cases. Fix bugs you find. Restate complexity. | Tested code |
| 38–45 | **Follow-ups** | Optimizations, scaling, variations. Often a second, harder part arrives here. | Discussion or part 2 |

If part 1 is easy, **go faster**: you're expected to reach part 2. If you're at minute 25 and haven't started coding, say so and pick the approach you can finish.

## 3. Clarifying Questions — Your Personal List

Use this on every practice problem until you no longer need to look.

**Input**
- How large can n be? (Tells you the target complexity — see `07_complexity_analysis_deep_dive.md` §8.)
- Value range? Negative numbers? Zero? Floats?
- Can there be duplicates?
- Can the input be empty or null? A single element?
- Is it sorted? Is the graph connected / directed / weighted / cyclic?
- Characters: ASCII letters only, or Unicode? Case-sensitive?
- Can I modify the input in place?

**Output**
- Return the value, the index, or the actual elements/path?
- If there are multiple valid answers, any one, or all? In what order?
- What if there's no answer: -1, empty, exception?
- Exact output format (sorted, deduplicated)?

**Operation / environment**
- For a class: how often is each method called? (Optimizes the right one.)
- Is the data a stream, or all available up front?
- Does it need to be thread-safe?
- Is memory limited?

Don't ask all of them. Ask the ones whose answer changes your algorithm, and **state assumptions** for the rest ("I'll assume the input fits in memory").

## 4. Edge-Case Checklist

Run through this during design (to shape the code) and again during verification (to test it).

| Category | Cases |
|---|---|
| Size | empty, one element, two elements, maximum size |
| Values | all identical, all distinct, zeros, negatives, min/max integer values, overflow (in non-Python languages) |
| Order | already sorted, reverse sorted, all equal |
| Duplicates | duplicates adjacent, duplicates far apart, answer involving duplicates |
| Strings | empty string, single character, all same character, Unicode/case |
| Graphs | disconnected components, cycles, self-loops, single node, unreachable target |
| Trees | null root, single node, skewed (linked-list shaped) tree, duplicate values |
| Intervals | touching endpoints, containment, identical intervals |
| Boundaries | first/last index, k = 0, k = n, k > n |
| Invalid input | when the problem allows it: what to return |

## 5. Thinking Out Loud Without Rambling

**Say:**
- The current goal: "I'm looking for a way to avoid rescanning the window."
- Observations: "The array is sorted, which usually means two pointers or binary search."
- Decisions and trade-offs: "A heap gives O(n log k); sorting gives O(n log n). k is small, so the heap."
- Status at transitions: "Approach agreed — I'll code it now." "Code done — let me trace it."

**Don't say:** every keystroke ("now I type for i in range"), or nothing for a minute.

**Rule of thumb:** no silence longer than ~30 seconds without a status update. If you need to think quietly, say so: "Give me 30 seconds to think about the recurrence."

**Drill:** record yourself solving a problem; watch it; note every stretch of unexplained silence and every stretch of narration that added nothing.

## 6. Using Hints Well

Hints are normal and don't sink you. What you do with them is the signal.

1. **Acknowledge** it: "That's a good point — if it's sorted, then…"
2. **Connect** it to your current approach out loud: what it changes and why.
3. **Move on quickly** with the adjusted plan.

Costly: arguing with the hint, ignoring it, or asking for another hint immediately without trying the first. A hint is almost always a course correction; take it.

## 7. Recovering When Stuck

In order:
1. **Go back to a small example** and solve it by hand. Watch what *you* do; that's often the algorithm.
2. **Solve a simpler version**: sorted input, no duplicates, k = 1, a 1D version of a 2D problem.
3. **Brute force first**, then ask what work it repeats (→ memoization/DP) or what it scans repeatedly (→ hashing, prefix sums, heaps, two pointers).
4. **List techniques that fit the constraints**: n ≤ 20 → bitmask; "shortest" → BFS/Dijkstra; "count ways" → DP; "k largest" → heap; "contiguous" → sliding window/prefix sums.
5. **Ask a specific question**: "Is it OK to use O(n) extra space?" beats "I'm stuck."
6. **Say what you're trying** at every step so the interviewer can steer.

If time is running out: implement the brute force cleanly and explain the optimization. Working code plus a correct plan beats a half-written optimal solution.

## 8. Code Quality in a Google Doc

- **Top-down structure:** write the main function first with calls to helpers you haven't written yet (`if not in_bounds(r, c)`), then fill in helpers. Readable immediately, and the interviewer sees the plan.
- **Names:** `left`, `right`, `window_count`, `visited`, `dist` — not `l2`, `x`, `tmp`.
- **Constants:** `DIRECTIONS = ((0,1),(1,0),(0,-1),(-1,0))`, `MOD = 10**9 + 7`.
- **Guard clauses** for edge cases at the top.
- **Don't mutate the input** unless you said so.
- **Consistent indentation** (4 spaces); no scrolling mega-lines.
- **Idiomatic Python** (`enumerate`, `zip`, `collections`) without code golf.
- In a design-style class problem, state each method's complexity next to its signature.

Deeper principles: `SoftwareDesign/01_philosophy_of_software_design.md` §19.

## 9. Verification: Testing Code You Can't Run

1. **Trace the example you wrote at the start**, line by line, tracking variables in a small table. Actually do it; don't summarize ("this obviously returns 6").
2. **Trace 2–3 edge cases** from §4 that stress different branches (empty, single element, duplicates).
3. **Look for the usual bug classes:**
   - off-by-one in loop bounds and slices (`range(n - 1)`, `lo <= hi`)
   - wrong initial values (0 vs `-inf`, empty result vs None)
   - forgetting to update a variable in one branch
   - mutating a list you then append to results (`res.append(path)` instead of `path[:]`)
   - integer division and negative modulo
   - returning inside a loop too early
4. **Restate time and space complexity** of the final code (not the plan — they sometimes differ).
5. **If you find a bug, say so and fix it calmly.** Finding your own bug is positive evidence.

Mention how you *would* test in production: unit tests for the examples and edge cases, randomized tests against a brute-force oracle (exactly what every solution file in this repo does).

## 10. Follow-ups

After solving, Google interviewers often extend the problem. Prepare an answer for each of these on every practice problem — the full treatment with worked examples is in `10_google_follow_ups_deep_dive.md`:
- Input is a stream you can't store.
- Data doesn't fit in memory or is spread over many machines.
- Millions of queries: what would you precompute?
- Multiple threads call it at once: what needs locking?
- A constraint changes: negatives, duplicates, cycles.

## 11. Practicing the Execution Layer

| Drill | How | Mastery check |
|---|---|---|
| Clarifying reflex | Before every practice problem, write 3 clarifying questions and your assumptions | You stop needing the list |
| Timed full rounds | 45 minutes, unseen medium, plain doc, talking out loud | 8 of 10 unseen mediums in ≤ 25 minutes, bug-free after your own testing |
| Recording review | Record and watch | No silence > 30 s without a status update |
| Verification | Trace every solution before running it | Your trace finds the bug before the tests do |
| Mocks | With strangers (interviewing.io, peers) | Last 3 mocks: hire or strong hire |

Mistakes log format (one line per problem you missed): `date | problem | pattern | the missing insight in one sentence | redo on D+3, D+7, D+21`. The spaced-repetition system in `REVIEW_LEDGER.md` implements this.

## Checklist

- [ ] I clarify, give an example, state brute force, and get agreement before coding — every time.
- [ ] I state time and space complexity before coding.
- [ ] I write top-down with helpers and good names.
- [ ] I trace an example and 2+ edge cases before saying "done."
- [ ] I handle hints by acknowledging, connecting, and moving on.
- [ ] I have a recovery routine when stuck and use it out loud.
