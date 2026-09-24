# Topic 18 · Greedy — Python Deep Dive

> A greedy algorithm builds a solution one irreversible local decision at a
> time — "given what I know right now, make the choice that looks best, and
> never revisit it." That is either brilliant or wrong, and the *only* thing
> that tells you which is a proof. This topic is as much about how to prove
> a greedy choice safe as it is about the fourteen lines of code that
> implement it.

---

## Part 1 · What makes a problem greedy-solvable

A problem is a candidate for a greedy algorithm only if it has **both**:

1. **The greedy-choice property.** A globally optimal solution can be
   reached by making a sequence of locally optimal choices, where each
   choice is made once and never reconsidered. Critically, this must be
   *provable* — "it looks like the right move" is not the same as "it is
   provably always at least as good as any alternative move."
2. **Optimal substructure.** After the greedy choice is made, the
   remaining subproblem (on whatever's left) is an instance of the same
   problem, and an optimal solution to the whole problem contains an
   optimal solution to that subproblem.

Optimal substructure alone is not enough — DP problems have it too (that's
*why* DP works on them). The dividing line is the greedy-choice property:
DP explores (or memoizes) multiple choices per state because no single
choice is provably safe in isolation; greedy commits to one choice per
state because it *is* provably safe, and never backtracks.

### 1.1 How to construct/verify an exchange argument

The exchange argument is the standard proof technique for the
greedy-choice property. The shape is always the same:

```arch
%% caption: The exchange argument: show that swapping the greedy choice into any optimal solution never makes it worse.
grid 190x80
node a "Greedy picks choice g first" at 0,0 w=200
node b "Take ANY optimal solution O" at 0,1 w=200
node c "Does O already contain g?" at 0,2 shape=diamond color=amber
node e "Some optimal solution contains g" at 1,2 color=green w=200
node g "Repeat on the remaining subproblem" at 2,2 w=180
node d "Swap g in" at 0,3 w=200 sub="for the element it displaces in O"
node f "Still feasible and no worse?" at 0,4 shape=diamond color=amber
node x "Greedy choice is WRONG" at 0,5 color=red w=200 sub="look at DP"
a -> b -> c
c -> e : "yes"
c -> d : "no"
d -> f
f:R -> e:B : "yes"
f -> x : "no"
e -> g
```


1. Take an arbitrary optimal solution `S*` that does **not** make the
   greedy choice at the first point of difference.
2. Show you can transform `S*` into a solution `S'` that *does* make the
   greedy choice there, **without making the solution worse** (same or
   better objective value), by swapping/exchanging one element for
   another.
3. Conclude: since `S*` was optimal and `S'` is no worse, `S'` is also
   optimal. So there always exists an optimal solution that makes the
   greedy choice — meaning committing to it up front loses nothing.
4. Repeat inductively on the remaining subproblem.

Concretely, for problem 006 (Best Time to Buy/Sell Stock II) in this
topic: suppose an optimal trading plan skips capturing the gain on some
single up-day `prices[i+1] - prices[i] > 0` (holding through it instead of
selling/rebuying at the boundary). Splitting any held interval at that
boundary into two back-to-back buy/sell pairs changes total profit by
exactly `0` (the two legs' gains still sum to the same interval gain) or
strictly **increases** it if the plan wasn't already summing every uphill
step — so a plan that captures every single uphill day is always at least
as good as one that doesn't. That is a complete exchange argument, not
just an assertion.

Contrast that with a *broken* greedy idea the topic deliberately shows
failing: for problem 001 (Maximize Sum of Array After K Negations),
"always negate the largest positive number, regardless of sign" has no
valid exchange argument — you can construct an input (see that problem's
runtime demo) where doing so strictly *decreases* the sum compared to the
provably-correct choice ("always negate the current minimum"). When you
cannot complete step 2 above — when the swap you'd need to perform
provably makes things worse in some case — that is your signal the greedy
idea is wrong, and you need DP (explore both choices, remember the best)
instead.

### 1.2 The generic greedy vs. DP decision test

Ask: **"If I make the locally-best choice now, could a worse-looking
choice now ever lead to a strictly better outcome later?"**

```arch
%% caption: Greedy or DP?
grid 220x80
node q "Optimisation problem" at 0,0 shape=pill
node a "Local choice provably safe?\n(exchange argument)" at 0,1 shape=diamond color=amber
node g "Greedy" at 1,1 color=green sub="sort or scan once"
node b "Do subproblems overlap?" at 0,2 shape=diamond color=amber
node d "Dynamic programming" at 1,2 color=green
node c "Backtracking or search" at 0,3 color=slate
q -> a
a -> g : "yes"
a -> b : "no"
b -> d : "yes"
b -> c : "no"
```


- If you can prove the answer is always "no" (exchange argument holds) →
  greedy, O(n) or O(n log n) typically.
- If you can find *even one* counterexample where the answer is "yes" →
  the locally-best choice is not safe; you need to consider both branches
  and keep the better one — that's DP (topics 16–17), often paying an
  extra O(n) or O(n²) factor for the memoized exploration greedy avoids.

---

## Part 2 · Common greedy patterns

### 2.1 Single left-to-right scan with a running "best so far"

The simplest shape: one pass, one (or a few) running variables, no
sorting needed because the input's natural order already exposes the
right local decision at each step.

- **Kadane's algorithm** (problem 002, Maximum Subarray): at each index,
  decide "extend the current run, or start fresh here" by comparing
  `curr + nums[i]` vs `nums[i]` — a negative running sum can never help a
  future subarray, so drop it. This is a greedy choice with a one-line
  exchange argument (a prefix with negative sum only ever drags down
  anything appended after it).
- **Jump Game** (003) and **Gas Station** (005): track a running
  reachability/feasibility frontier (farthest index reachable; running
  tank total) and only reset the decision point when the invariant breaks.

### 2.2 Sort, then scan

When the input's given order does *not* already expose the right local
decision, sort by whatever key makes the greedy choice provably safe, then
do a single scan.

- **Merge Intervals family** (topic 19, and problem 009 Partition Labels
  in spirit): sort by start (or, for partition labels, precompute last-seen
  index) so overlap/extension decisions become a simple running-max
  comparison.
- **Hand of Straights** (007): must always start a new group from the
  *smallest* remaining card, because nothing smaller exists to complete a
  group that needs it — sorting (or a min-heap) makes that smallest card
  available in O(log n) instead of an O(n) scan every round.
- **Jump Game II** (004): a BFS-flavored greedy over "levels" — implicitly
  processes the array in the order that keeps the reachable frontier
  monotone; no explicit sort needed here because the array index *is* the
  sort key, but the *pattern* (advance a frontier, commit once you can't
  extend for free) is the same family as interval scheduling.

### 2.3 Range/bound tracking

Some greedy problems don't track a single running value but a **range**
of currently-possible values, collapsing back to a single decision only
at the end.

- **Valid Parenthesis String** (010): track `[lo, hi]`, the minimum and
  maximum possible count of unmatched `(` after each character, given that
  `*` can be `(`, `)`, or empty. This is still greedy (no branching
  explosion — the range summarizes all live branches in O(1) extra space)
  but it's a step beyond a single running scalar; the DP alternative
  (problem 010's O(n²) contrast) tracks the *same* information but as an
  explicit boolean table over `(i, balance)` instead of collapsing it to
  an interval, which is the concrete illustration of "DP explores, greedy
  collapses" from Part 1.

---

## Part 3 · "Provably greedy" vs. "looks greedy but needs DP" — contrast with topics 16/17

The whole reason topic 18 exists as a separate unit from topics 16–17 (1D
and 2D DP) is that several classic problems *look* identical in shape to a
DP problem but admit a proof that collapses the DP table to O(1) state.

| Signal | Points toward greedy | Points toward DP |
|---|---|---|
| Can you name the exchange argument in one or two sentences? | Yes → greedy is likely provably correct | No, or every attempt finds a counterexample → DP |
| Does today's optimal choice ever depend on *which* choice was optimal several steps back (not just the current running state)? | No — a small fixed summary (a running max, a range, a frontier index) is always enough | Yes → you need to remember more than a constant amount of history → DP table |
| Do two different prefixes that reach the "same-looking" local state ever need to be treated differently later? | No, they're interchangeable | Yes → local state alone doesn't determine the future → DP |
| Best time to buy/sell stock **II** (unlimited transactions, no fee, no cooldown) | **Greedy** — capture every uphill move (problem 006) | — |
| Best time to buy/sell stock **with cooldown / transaction fee / at most k transactions** | — | **DP** — the "should I sell now" choice depends on state (holding vs. not, transactions used) that a single running max can't capture; that's exactly topic 16's DP-1D territory |
| Jump Game / Jump Game II (can-you-reach / min-jumps) | **Greedy** — farthest-reachable frontier is a provably sufficient summary | Longest Increasing Subsequence-style "which specific path" problems | **DP** — need the actual sequence/count, not just reachability |
| Coin change with unlimited coins of *fixed given* denominations, minimize count | Greedy **only** works for specific denomination sets (e.g. canonical currency systems like US coins) — no general exchange argument | **DP** in general — classic counterexample: coins `{1, 3, 4}`, target `6` → greedy takes `4+1+1` (3 coins), optimal is `3+3` (2 coins) |

The last row is the canonical cautionary tale to keep in mind whenever a
problem *smells* greedy: coin change's greedy heuristic ("always take the
largest denomination that fits") has no valid exchange argument for
arbitrary denominations, and a two-line counterexample kills it. Every
problem in this topic (18) **was** checked for a valid exchange argument
before being written up as greedy — see each solution file's THE CORE IDEA
section for the specific argument, and its runtime demo for a broken
heuristic shown visibly failing where relevant.

---

## Part 4 · Practical checklist before committing to a greedy solution

1. State the greedy rule in one sentence ("always pick the smallest
   remaining X", "always extend if Y", "always negate the current
   minimum").
2. Try to break it: construct the smallest adversarial input you can
   think of (ties, negatives, zeros, all-equal elements, the
   largest-vs-smallest-first ambiguity) and hand-trace the rule against
   what you know the true optimum to be.
3. If it breaks, write down *why* — that failure mode is usually the seed
   of either a corrected greedy rule (add a tiebreak, change the sort key)
   or evidence you actually need DP.
4. If it survives, write the one/two-sentence exchange argument down
   before writing code — if you can't articulate it, you don't yet know
   *why* it works, only that it happened to pass your test cases, which is
   exactly the trap this checklist exists to catch.

---

## Part 5 · This topic's ten problems, by pattern

| # | Problem | Pattern (Part 2) | Contrast worth knowing |
|---|---|---|---|
| 001 | Maximize Sum of Array After K Negations | Sort, then scan | Broken heuristic (negate-largest) shown failing live |
| 002 | Maximum Subarray (Kadane's) | Running best-so-far | O(n) vs. brute-force O(n²)/O(n³), measured |
| 003 | Jump Game | Running frontier | O(n²) DP alternative shown for contrast |
| 004 | Jump Game II | Running frontier (level/BFS-flavored) | O(n²) DP alternative shown for contrast |
| 005 | Gas Station | Running total + reset point | Exchange argument on *why* the reset point works |
| 006 | Best Time to Buy/Sell Stock II | Running best-so-far | Contrast with cooldown/fee variants which need DP (topic 16) |
| 007 | Hand of Straights | Sort, then scan (min-heap variant) | Why you must always start from the current minimum |
| 008 | Merge Triplets to Form Target Triplet | Filter, then scan | Coordinate-wise max is only safe on "usable" triplets |
| 009 | Partition Labels | Sort/precompute, then scan | Same family as interval merging (topic 19) |
| 010 | Valid Parenthesis String | Range/bound tracking | O(n²) DP-over-balance alternative shown for contrast |

<!-- block:18_py_1_beyond -->
## Part 6 · Proof Techniques, Interval Scheduling and the Classics Beyond the Ten

The guide teaches *when* greedy is legal and gives ten problems. This Part adds the proof vocabulary interviewers expect,
the classic scheduling problem the ten do not include, and a way to **test a greedy** before you trust it. Every snippet was
run, and every count below is from a randomised cross-check on this machine.

```arch
%% caption: A greedy is only as good as its proof. Try to break it with a small counter-example first, then name the argument.
grid 200x80
node q "A greedy idea" at 0,0 shape=pill
node a "Small counter-example?\n(brute-force tiny inputs)" at 0,1 shape=diamond color=amber
node d "Not greedy: use DP or search" at 1,1 color=red w=230 sub="e.g. coins 1,3,4 for 6"
node b "Which argument fits?" at 0,2 shape=diamond color=amber
node e "Exchange argument" at 1,2 color=green w=380 sub="swap an optimal choice for the greedy one, no worse"
node s "Greedy stays ahead" at 1,3 color=green w=380 sub="after every step, greedy is at least as far ahead as any other"
node m "Matroid / structural argument" at 1,4 color=green w=380 sub="every partial choice extends to an optimum"
q -> a
a -> d : "yes"
a -> b : "no"
b:R -> e:L
b:R -> s:L
b:R -> m:L
```

### 6.1 Two proof styles, in one sentence each

- **Exchange argument.** Take *any* optimal solution that disagrees with the greedy choice at the first step; **swap** its
  choice for the greedy one; show the result is still feasible and no worse. Repeat, and the greedy solution is optimal.
  (*"If it does not pick the interval that ends earliest, replace its first interval with that one: it ends no later, so
  everything that followed still fits."*)
- **Greedy stays ahead.** Show that after each step the greedy solution is at least as good as *any other* strategy's at
  the same step, measured by a quantity you name (farthest reach, earliest finish time). Jump Game is this argument with
  `farthest` as the measure.

If you can state neither in a sentence, treat the "greedy" as a guess and test it (6.3).

### 6.2 Interval scheduling: the choice of sort key *is* the algorithm

*Maximise the number of non-overlapping intervals.* The only decision is what to sort by — and three natural-sounding keys
are wrong:

```python
last_end = -inf; chosen = 0
for s, e in sorted(intervals, key=lambda iv: (iv[1], iv[0])):     # by END time, ties by start
    if s >= last_end: chosen += 1; last_end = e
```

| Sort by | Why it fails (or works) |
|---|---|
| **earliest end** ✅ | Ending early leaves the most room for the rest — the exchange argument above. |
| earliest start | A long early interval blocks everything: `[[1,10],[2,3],[4,5]]` picks only `[1,10]` → **1**, not 2. |
| shortest first | A short interval in the *middle* can block two others. |
| fewest conflicts | Plausible, and still wrong on small inputs. |

The same skeleton solves **Non-overlapping Intervals** (answer = `n − chosen`), **Minimum Number of Arrows to Burst
Balloons** (one arrow at each *end* of the first uncovered interval: `[[10,16],[2,8],[1,6],[7,12]]` → 2) and is the "sort by
end" cousin of *merge intervals* (sort by start), covered next in topic 19.

### 6.3 Test a greedy against brute force

The fastest way to distrust — or trust — a greedy is to compare it with an exhaustive search on **thousands of tiny random
inputs**. For interval scheduling, brute force tries every subset:

```python
def brute(ivs):
    best = 0
    for r in range(len(ivs) + 1):
        for combo in itertools.combinations(ivs, r):
            cs = sorted(combo)
            if all(cs[i][1] <= cs[i+1][0] for i in range(len(cs) - 1)): best = max(best, r)
    return best
```

Over 2,000 random instances (up to 6 intervals, coordinates 0–13), the earliest-**end** greedy disagreed with brute force
**0** times; earliest-**start** disagreed **100** times; shortest-first **576** times. A counter-example found in seconds is
worth more than a proof attempted in minutes — and the counter-example goes straight into your explanation.

### 6.4 More classics, each with its trick

| Problem | The greedy | The trap |
|---|---|---|
| **Candy** (LC 135) | Two passes: left-to-right (beat the left neighbour), right-to-left with `max` to *keep* the first pass's result. `[1,0,2]` → 5, `[1,2,2]` → 4. | Trying to do it in one pass; overwriting instead of `max` on the second pass. |
| **Two City Scheduling** (LC 1029) | Sort by `cost_A − cost_B`; the first half goes to A, the rest to B. `[[10,20],[30,200],[400,50],[30,20]]` → 110. | Sorting by `cost_A` alone. |
| **Queue Reconstruction by Height** (LC 406) | Sort tallest first (ties by fewer-in-front), then `insert(k, person)`: a shorter person never changes a taller one's count. | Sorting ascending; forgetting the tie-break. |
| **Wiggle Subsequence** (LC 376) | Count direction changes: `up = down + 1` when rising, `down = up + 1` when falling. `[1,7,4,9,2,5]` → 6. | Comparing against the wrong neighbour after equal values. |
| **Assign Cookies** (LC 455) | Sort both; give each cookie to the *least greedy child it satisfies*. | Giving big cookies to small children. |
| **Lemonade Change** (LC 860) | On a `$20` prefer `10 + 5` over `5 + 5 + 5` — the fives are more flexible. | Spending the fives first. |
| **Largest Number** (LC 179) | Sort with the comparator `a + b > b + a` on strings (topic 22). | Sorting numerically or lexicographically. |

### 6.5 When greedy fails — and the variant that rescues it

- **Coin Change** with denominations `{1, 3, 4}`, amount 6: greedy takes `4 + 1 + 1` (3 coins), the optimum is `3 + 3` (2). Greedy
  works only for *canonical* systems (US coins) — no exchange argument exists in general, so use DP.
- **Knapsack:** sort by value-per-weight and take greedily. With **splittable** items (*fractional* knapsack) this is
  optimal — capacity 50 on `(60,10), (100,20), (120,30)` gives **240**. With **indivisible** items (0/1) it is *not* — the DP
  optimum is **220**. Same data, opposite verdicts; the difference is whether you may take a fraction.
- **Stock with cooldown / fee / `k` transactions** needs DP (topic 17): "should I sell now?" depends on state a single running
  maximum cannot hold. Unlimited transactions with no fee is greedy (sum every rise).

### 6.6 Greedy algorithms you already know

| Algorithm | The greedy choice | Why it is safe |
|---|---|---|
| Dijkstra | Settle the closest unsettled node | Non-negative edges: nothing later can be shorter. |
| Kruskal / Prim | Take the cheapest edge that does not close a cycle / that leaves the tree | The cut property (a matroid). |
| Huffman coding | Merge the two lightest subtrees | Exchange argument on the deepest leaves. |
| Kadane | Extend or restart the running subarray | A negative running sum can only hurt. |
| Interval scheduling | Earliest finish first | Exchange argument (6.1). |
| Fractional knapsack | Best value/weight first | Splitting removes the "wasted capacity" counter-example. |

### 6.7 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Prove it." | State the exchange argument or the quantity greedy keeps ahead on, in one sentence. |
| "Why not DP?" | Greedy is O(n log n) or O(n); DP was needed only if a small counter-example exists — show you looked for one. |
| "Does the sort key matter?" | Yes — it *is* the algorithm (6.2). Give the counter-example for the tempting wrong key. |
| "Ties?" | Encode the tie-break as an explicit secondary key; do not rely on stability. |
| "Weighted intervals?" | Greedy fails — weighted interval scheduling is a DP over end-time-sorted intervals with a binary search for the last compatible one. |
| "Online / streaming?" | Some greedies work online (Kadane, farthest reach), others need the whole input sorted. |

---
<!-- /block:18_py_1_beyond -->

<!-- problem-map:start -->
## Part 7 · Every Problem in This Topic, by Pattern

Ten problems, four moves (sort then scan · running best-so-far · running frontier · range tracking). Every **Trap** is a "looks-greedy-but-wrong" mistake documented in that problem's solution file — the topic's recurring lesson is that the wrong greedy passes the examples.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Maximize Sum Of Array After K Negations](PyDSA/18_greedy/001_maximize_sum_of_array_after_k_negations_solution.py) <br>LC 1005 · Easy | Sort, then scan | Negate the most negative numbers first while `k` lasts (each flip adds `2·\|x\|`); if `k` is still odd afterwards, negate the smallest value of the *already-negated* array. **Trap:** "always negate the current maximum" (shown failing live); taking the leftover-`k` minimum from the pre-flip array. |
| [002 · Maximum Subarray](PyDSA/18_greedy/002_maximum_subarray_solution.py) <br>LC 53 · Medium | Running best-so-far (Kadane) | `curr = max(x, curr + x)` extends or restarts in one expression, and `best` records the maximum. O(n) against the brute force's O(n²)/O(n³). **Trap:** `best = 0` (allows the empty subarray — wrong on all-negative input); `curr = max(0, curr) + x` (the same bug). |
| [003 · Jump Game](PyDSA/18_greedy/003_jump_game_solution.py) <br>LC 55 · Medium | Running frontier | Track `farthest`; `i > farthest` means you can never arrive — fail; otherwise extend. No per-step jump choices at all. **Trap:** "always take the biggest jump" (walks into a `0`); only the early-success check without the `i > farthest` guard; comparing against `n` instead of `n - 1`. |
| [004 · Jump Game II](PyDSA/18_greedy/004_jump_game_ii_solution.py) <br>LC 45 · Medium | Running frontier by levels | BFS in disguise: the current level ends at `level_end`; crossing it costs one more jump and sets the next end to `farthest`. **Trap:** "always jump exactly `nums[i]`" (overshoots a better staging index); looping to `n` instead of `n - 1` (a spurious extra jump). |
| [005 · Gas Station](PyDSA/18_greedy/005_gas_station_solution.py) <br>LC 134 · Medium | Running total + reset point | A solution exists iff `sum(gas) >= sum(cost)`; when the tank goes negative, restart after the failed stretch. **Trap:** the local test `gas[i] >= cost[i]` (ignores the carried tank); omitting the global feasibility check. |
| [006 · Best Time to Buy and Sell Stock II](PyDSA/18_greedy/006_best_time_to_buy_and_sell_stock_ii_solution.py) <br>LC 122 · Medium | Sum every rise | With unlimited trades, no fee and no cooldown, profit = the sum of every positive day-to-day increase. **Trap:** hunting for one best (buy, sell) pair (that is LC 121); reusing the trick once a cooldown or fee exists (that is DP). |
| [007 · Hand of Straights](PyDSA/18_greedy/007_hand_of_straights_solution.py) <br>LC 846 · Medium | Sort, then start from the minimum | Always start the next run at the *smallest* remaining card (forced, by the exchange argument); count copies with a `Counter`. **Trap:** starting from an arbitrary or highest-count card (strands a smaller value); dropping the `len(hand) % groupSize` early return. |
| [008 · Merge Triplets to Form Target Triplet](PyDSA/18_greedy/008_merge_triplets_to_form_target_triplet_solution.py) <br>LC 1899 · Medium | Filter, then scan | Merging is a coordinate-wise max, so discard any triplet with a coordinate **above** the target, then check that the survivors reach every coordinate. **Trap:** merging without filtering (one over-target coordinate poisons the max); filtering on only one or two coordinates; `>=` instead of `>`. |
| [009 · Partition Labels](PyDSA/18_greedy/009_partition_labels_solution.py) <br>LC 763 · Medium | Precompute last index, then scan | Store each letter's last occurrence first; extend `end` to the farthest last-occurrence seen; cut when `i == end`. **Trap:** closing a partition once a letter "looks stable"; building the last-occurrence map in the same forward pass. |
| [010 · Valid Parenthesis String](PyDSA/18_greedy/010_valid_parenthesis_string_solution.py) <br>LC 678 · Medium | Range tracking | Track `[lo, hi]` — the min and max possible count of unmatched `(`; clamp `lo` at 0; fail if `hi < 0`; succeed iff `lo == 0`. **Trap:** treating every `*` as `(` first (a fixed commitment cannot backtrack); forgetting to clamp `lo`. |

---
<!-- problem-map:end -->


## Checklist Before Leaving This Topic <!--ca-->

- [ ] State an exchange argument and a "greedy stays ahead" argument in one sentence each <!--ca-->
- [ ] Explain why interval scheduling sorts by **end** time, with the earliest-start counter-example <!--ca-->
- [ ] Cross-check a greedy against brute force on tiny random inputs, and report what the check found <!--ca-->
- [ ] Give the counter-example for greedy Coin Change and 0/1 knapsack, and the variant (fractional) where greedy works <!--ca-->
- [ ] Name three algorithms you already know that are greedy, and why each choice is safe <!--ca-->
