# Running the 45-Minute Coding Round

This file is about *performing* what you know, not learning new CS concepts — it
applies whether this is your first technical interview or your tenth, at any level.
Knowing algorithms is necessary but not sufficient. Interviewers write feedback on
**four things**: communication, problem solving, code quality, and verification
(testing your own code). An optimal answer reached silently, with sloppy code and no
testing, can still come back as a weak rating. At L5 there's a fifth, implicit
signal: **did you drive it, or did the interviewer drag you through it?**

This file is the execution layer: the timeline, a clarifying-question list you can use until it's automatic, the edge-case checklist, how to think out loud, how to use hints, how to recover when stuck, and how to verify code without running it.

New to technical interviews? Start with the **Foundations** section: what a coding
interview actually is, who is in it, what gets written down afterwards, and why each
phase of the timeline exists. The numbered sections after it are the original
execution guide, now with worked examples added (a before-and-after code-quality
rewrite, a narrated recovery, and a full line-by-line trace). A side-by-side
breakdown of what Junior through Staff+ candidates are expected to show closes the
chapter, just before the interview checklist.

## Foundations — What a Coding Interview Is, and How It Works

### Why Coding Interviews Exist

A company hiring an engineer wants to know one thing: *will this person write
correct, maintainable code with their colleagues, on problems nobody has solved for
them yet?* It can't watch you do the job for six months, so it takes a sample: 45
minutes of you solving an unfamiliar problem while someone watches. The sample is
small and noisy, which is why companies run several rounds with different
interviewers and have each one write down *evidence* against a fixed rubric instead of
a gut feeling. Two consequences follow, and the rest of this file is built on them:

- **The interviewer can only grade what they observe.** A brilliant idea you had but
  didn't say is, as far as the feedback form is concerned, an idea you didn't have.
- **The problem is a vehicle, not the goal.** Interviewers pick problems that let them
  watch you clarify, design, code and test. Reaching the answer matters; *how* you
  reach it is most of the grade.

### What a Coding Interview Actually Is

A coding round is a short, structured collaboration with a hidden scorecard. Its
parts:

| Component | What it is | Why it matters to you | Covered in |
|---|---|---|---|
| **The problem** | A task deliberately left a little underspecified (sizes, edge cases, output format) | Clarifying is part of the test, not a delay before it | §3, §4 |
| **The interviewer** | Evaluator, collaborator and source of hints at once | Treat them like a teammate: think aloud, check in, take hints well | §5, §6 |
| **The medium** | A shared doc, a simple online editor, or a whiteboard; often *no* way to run code | You must verify by reasoning and tracing, not by pressing Run | §8, §9 |
| **The clock** | About 45 minutes, of which roughly 35–40 are problem time | Pace matters: a correct answer at minute 44 with no testing scores lower than a tested one at minute 35 | §2 |
| **The rubric** | Usually four signals: communication, problem solving, code quality, verification | Every behaviour below maps to one of them | §1 |
| **The write-up and decision** | Interviewer notes become written feedback with a hire/no-hire rating; a committee or debrief compares all rounds | Specific, observable evidence ("traced two edge cases unprompted") is what survives into the decision | Foundations |

### How the Pieces Fit Together

```arch
%% caption: The problem goes in, your visible behaviour is observed and written up against the rubric, and a committee decides from the written evidence of every round.
grid 170x110
node prob "Problem prompt" at 1,0 icon=doc sub="deliberately underspecified"
group room "The 45-minute round" color=blue icon=timer
node you "You" at 0,1 in room icon=user sub="clarify, design, code, verify"
node iv "Interviewer" at 2,1 in room icon=users sub="observes, hints, extends"
node notes "Notes" at 1,2 in room icon=edit sub="what you said and did"
group after "After the round" color=purple icon=flag
node fb "Written feedback" at 1,3 in after icon=doc sub="4 signals + rating"
node hc "Committee / debrief" at 1,4 in after icon=group sub="all rounds together"
prob -> you
you <-> iv : "talk, hints"
iv -> notes
notes -> fb -> hc
```

The chain matters: whatever doesn't reach the **notes** can't reach the decision. At
Google, for example, interviewers submit written feedback and a separate hiring
committee reviews the whole packet; the interviewer is not the one who decides. Most
large companies run some version of this (a debrief, a bar raiser, a committee).

### Solving vs Demonstrating: the Distinction This Whole File Assumes

Solving a problem and *demonstrating* that you can solve problems are different
activities. Solving can happen silently, in any order, with ten false starts erased.
Demonstrating means the evidence is visible: you state the brute force so the
interviewer knows you can find one, you name why the optimisation works so they know
it wasn't memorised, you trace the code so they see you catch your own bugs. Every
phase of the timeline in §2 exists to produce one kind of evidence:

| Phase | Why it exists | Evidence it produces |
|---|---|---|
| Clarify | Real requirements are ambiguous; problems are underspecified on purpose | You don't build the wrong thing |
| Design | Rewriting code in a doc is expensive; agreement first saves the round | You can compare approaches and reason about cost |
| Code | The deliverable | Readable, structured, idiomatic code |
| Verify | There's usually no compiler or test runner | You find your own bugs |
| Follow-ups | Calibrates *level*: how far past the base problem you can go | Depth, scale, trade-offs ([Google-Style Follow-Ups — Scaling a Coding Answer](10_google_follow_ups_deep_dive.md)) |

### The Formats You'll Meet

| Format | What changes | Adjust by |
|---|---|---|
| Phone / video screen | Usually one or two shorter problems in a shared editor | Faster pace; same four signals |
| Onsite (in person or virtual) | Several 45-minute rounds, each scored independently | One bad round is recoverable; reset between rounds |
| Whiteboard | No editor at all; space is limited | Plan the layout; write helpers in a corner; trace with a small table |
| Practical / pair-programming | Real editor, can run code, often an existing codebase | Tests and incremental commits replace hand-tracing |
| Take-home | Hours or days, reviewed later | Code quality and tests carry almost all the weight |
| AI-assisted rounds | Some companies now allow an AI assistant during a round | The rubric shifts toward problem framing, reviewing generated code and verification; ask the recruiter what's allowed |

Several large companies (Google among them) have also reintroduced at least one
in-person round, partly because of AI-assisted cheating in virtual ones. The skills
here apply unchanged; check the format with your recruiter in advance.

### Vocabulary You'll Meet Below, in One Table

| Term | One-line meaning |
|---|---|
| Signal | Observable evidence for one rubric dimension |
| Brute force | The simplest correct solution, usually slow; stating it proves you can find a correct baseline |
| Pattern | A reusable technique family (sliding window, BFS, DP) you recognise from the problem's shape |
| Invariant | A statement that stays true every loop iteration; the core of explaining *why* code is correct |
| Trace / dry run | Executing the code by hand on a concrete input, tracking variables |
| Edge case | An input at a boundary (empty, one element, duplicates, extremes) where bugs cluster |
| Hint | An interviewer nudge; normal, and how you use it is itself a signal |
| Follow-up | A change to the problem after you solve it, used to calibrate level |
| Rating scale | Typically Strong No Hire / No Hire / Lean No Hire / Lean Hire / Hire / Strong Hire (names vary) |

With what the round is, who is in it and what gets written down in place, the
sections below are the concrete execution playbook.

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

```arch
%% caption: The coding round follows a strict progression; getting agreement on the design before coding is the most critical gate.
route straight
grid 200x100
node clarify "1. Clarify" at 0,0 icon=question shape=card color=blue sub="0-5 min"
node design "2. Design & Agree" at 0,1 icon=idea shape=card color=amber sub="5-12 min"
node code "3. Code" at 0,2 icon=code shape=card color=green sub="12-30 min"
node verify "4. Verify / Trace" at 0,3 icon=check shape=card color=green sub="30-38 min"
node fup "5. Follow-ups" at 0,4 icon=time shape=card color=slate sub="38-45 min"

clarify -> design
design -> code
code -> verify
verify -> fup
```

## 3. Clarifying Questions — Your Personal List

Use this on every practice problem until you no longer need to look.

**Input**
- How large can n be? (Tells you the target complexity — see [Complexity Analysis](07_complexity_analysis_deep_dive.md) §8.)
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

### A recovery, narrated
Problem: *"Given an array of integers and k, count subarrays whose sum equals k."* You
proposed a sliding window, then realised the array can contain negatives.

> "Wait: a sliding window assumes the sum only grows when the window grows, and
> negatives break that. Let me go back to the brute force: for every start and end,
> sum the range. That's O(n²) with a running sum. What does it repeat? For each end,
> it's asking 'how many earlier prefix sums equal `prefix - k`?' That's a hash map
> lookup, so a Counter of prefix sums gives O(n). Does that sound right before I code
> it?"

Every step of the routine above is visible: name what broke, fall back to brute
force, ask what it repeats, name the technique, check in. Even if the interviewer had
to hint "think about prefix sums", this narration earns most of the problem-solving
credit.

## 8. Code Quality in a Google Doc

- **Top-down structure:** write the main function first with calls to helpers you haven't written yet (`if not in_bounds(r, c)`), then fill in helpers. Readable immediately, and the interviewer sees the plan.
- **Names:** `left`, `right`, `window_count`, `visited`, `dist` — not `l2`, `x`, `tmp`.
- **Constants:** `DIRECTIONS = ((0,1),(1,0),(0,-1),(-1,0))`, `MOD = 10**9 + 7`.
- **Guard clauses** for edge cases at the top.
- **Don't mutate the input** unless you said so.
- **Consistent indentation** (4 spaces); no scrolling mega-lines.
- **Idiomatic Python** (`enumerate`, `zip`, `collections`) without code golf.
- In a design-style class problem, state each method's complexity next to its signature.

Deeper principles: [The Philosophy of Software Design](../SoftwareDesign/01_philosophy_of_software_design.md) §19.

### The same solution, two qualities
Both of these are correct for "number of islands." Only one reads well in a doc.

```python
# Before: correct, but hard to review
def f(g):
    c = 0
    for i in range(len(g)):
        for j in range(len(g[0])):
            if g[i][j] == "1":
                c += 1
                s = [(i, j)]
                g[i][j] = "0"
                while s:
                    a, b = s.pop()
                    for x, y in ((a+1, b), (a-1, b), (a, b+1), (a, b-1)):
                        if 0 <= x < len(g) and 0 <= y < len(g[0]) and g[x][y] == "1":
                            g[x][y] = "0"
                            s.append((x, y))
    return c

# After: same algorithm, top-down, named, and it doesn't destroy the caller's grid
DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))

def num_islands(grid: list[list[str]]) -> int:
    if not grid or not grid[0]:
        return 0
    rows, cols = len(grid), len(grid[0])
    seen = set()

    def in_bounds(r, c):
        return 0 <= r < rows and 0 <= c < cols

    def flood(r, c):                   # iterative DFS: no recursion-limit risk
        stack = [(r, c)]
        seen.add((r, c))
        while stack:
            cr, cc = stack.pop()
            for dr, dc in DIRECTIONS:
                nr, nc = cr + dr, cc + dc
                if in_bounds(nr, nc) and grid[nr][nc] == "1" and (nr, nc) not in seen:
                    seen.add((nr, nc))
                    stack.append((nr, nc))

    islands = 0
    for r in range(rows):
        for c in range(cols):
            if grid[r][c] == "1" and (r, c) not in seen:
                islands += 1
                flood(r, c)
    return islands

g = [list("11000"), list("11000"), list("00100"), list("00011")]
assert num_islands(g) == 3
assert f([row[:] for row in g]) == 3
assert num_islands([]) == 0
```
The "after" version costs O(rows·cols) extra space for `seen`; say so, and offer the
in-place marking of the "before" version as an option *if the interviewer agrees you
may mutate the input*.

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

### A worked trace
Problem: *longest substring without repeating characters.* The code, then the trace
table you'd actually write in the doc for `s = "abba"`, an input chosen because it
exercises the "last seen index is *left* of the window" branch that most bugs hide in.

```python
def length_of_longest_substring(s: str) -> int:
    last_seen = {}                     # char -> most recent index
    left = best = 0
    for right, ch in enumerate(s):
        if ch in last_seen and last_seen[ch] >= left:
            left = last_seen[ch] + 1   # jump past the previous copy
        last_seen[ch] = right
        best = max(best, right - left + 1)
    return best

assert length_of_longest_substring("abba") == 2
assert length_of_longest_substring("abcabcbb") == 3
assert length_of_longest_substring("") == 0
assert length_of_longest_substring("a") == 1
```

| right | ch | `last_seen` before | condition | left | best |
|---|---|---|---|---|---|
| 0 | a | {} | not seen | 0 | 1 |
| 1 | b | {a:0} | not seen | 0 | 2 |
| 2 | b | {a:0, b:1} | seen at 1 ≥ 0 → jump | 2 | 2 |
| 3 | a | {a:0, b:2} | seen at 0, but 0 < 2 → **ignore** | 2 | 2 |

Without the `>= left` check, step 3 would move `left` *backwards* to 1 and report 3.
That one row is the whole reason to trace a tricky input rather than the happy path.
Then say it: "O(n) time, O(min(n, alphabet)) space."

## 10. Follow-ups

After solving, Google interviewers often extend the problem. Prepare an answer for each of these on every practice problem — the full treatment with worked examples is in [Google-Style Follow-Ups — Scaling a Coding Answer](10_google_follow_ups_deep_dive.md):
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

Mistakes log format (one line per problem you missed): `date | problem | pattern | the missing insight in one sentence | redo on D+3, D+7, D+21`. The spaced-repetition system in [Review Ledger](../REVIEW_LEDGER.md) implements this.

## What Each Engineering Level Should Know

The same 45-minute round is used from new grad to Staff, but what counts as a strong
performance shifts. At junior levels the interviewer mostly asks *can they get to
working code?*; from Senior upward the question becomes *did they drive the whole
round themselves?* This table maps the chapter onto a standard industry ladder and the
Google-style ladder side by side. The title-to-level mapping is approximate and
varies by company; the behaviour described in each cell is the reliable part. Read
down a column as a target, or find the cells that match your last mock as a
self-assessment.

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **What's being graded** (Foundations, §1) | Knows the answer isn't the only thing that counts | Knows the four signals and aims at each | Makes every signal visible without being asked; the notes almost write themselves | Also shows engineering judgment beyond the problem: API shape, testability, how it would run in production |
| **Clarify & design** (§2–§4) | Asks some clarifying questions when prompted | Asks the questions that change the algorithm; states brute force and complexity | Scopes the problem, states assumptions, compares two approaches with trade-offs, and gets agreement before coding | Reframes an ambiguous problem into the right one and flags which requirement would change the design |
| **Communication & hints** (§5–§6) | Explains code after writing it; may go quiet under pressure | Narrates decisions; takes hints but may need a second one | No silence longer than ~30 seconds; turns a single hint into a new plan immediately | Runs the round like a design discussion with a peer; rarely needs a hint, and uses the interviewer to check assumptions rather than to get unstuck |
| **Recovering when stuck** (§7) | Needs the interviewer to suggest a smaller case | Uses brute force and small examples to get unstuck | Runs the whole recovery routine out loud, and falls back to a clean brute force if time runs short | Recognises a dead end early and changes approach without losing the thread |
| **Code quality** (§8) | Working code, possibly one long function | Helpers and reasonable names | Top-down structure, guard clauses, idiomatic code, no input mutation without agreement | Code a reviewer would approve as-is, with the contract and complexity written next to each function |
| **Verification & follow-ups** (§9–§10) | Tests by running when possible; misses edge cases | Traces the main example; finds some bugs | Traces a tricky input and two edge cases, finds own bugs, restates exact complexity, reaches the follow-up | Handles the follow-ups as small system-design questions ([Google-Style Follow-Ups — Scaling a Coding Answer](10_google_follow_ups_deep_dive.md)), with concrete trade-offs |

**Reading this table as a study plan:** a correct solution delivered in the Mid-Level
column's style is typically read as L4 even if it's optimal; the same solution in the
Senior column's style reads as L5. That difference is all execution, and it's
trainable with the drills in §11. At Staff+ levels, coding rounds are usually fewer
and weigh less than design and leadership rounds, but a weak coding round can still
sink the packet.

## Interview checklist

- [ ] I clarify, give an example, state brute force, and get agreement before coding — every time.
- [ ] I state time and space complexity before coding.
- [ ] I write top-down with helpers and good names.
- [ ] I trace an example and 2+ edge cases before saying "done."
- [ ] I handle hints by acknowledging, connecting, and moving on.
- [ ] I have a recovery routine when stuck and use it out loud.
- [ ] I can explain what the interviewer writes down after the round and why unspoken reasoning earns no credit.
- [ ] I can adapt to the format (shared doc, whiteboard, runnable editor, AI-assisted) and know which signals shift in each.
- [ ] I pick a tricky trace input on purpose (one that exercises the branch most likely to be wrong), not just the happy path.

Related: [Complexity Analysis](07_complexity_analysis_deep_dive.md) §8–§9, [Python for Coding Interviews](08_python_for_coding_interviews_deep_dive.md), [Google-Style Follow-Ups — Scaling a Coding Answer](10_google_follow_ups_deep_dive.md), [How Google Scores You](../GoogleBehavioral/01_how_google_scores_and_googleyness.md), [Google Interview Master Study Plan (L5 / Senior SWE)](../GOOGLE_INTERVIEW_PREP.md).
