# Topic 17 · 2D Dynamic Programming — Python Deep Dive

> Topic 16 collapsed every subproblem down to a single index `dp[i]`. This
> topic is exactly the cases where that collapse FAILS: the state genuinely
> needs TWO numbers to name a subproblem — `dp[i][j]` — because two things
> vary independently and neither can be expressed in terms of the other.
> Learn to recognize the four SHAPES that "two numbers" takes (grid
> position, two-string alignment, day+state, interval), and every problem
> in this folder is a variation on one of them.

---

## Part 0 · Why `dp[i]` isn't enough here

Take Unique Paths (001): a robot on an `m x n` grid, moving only right or
down, counting paths to the bottom-right corner. Try to force this into 1D:
"the number of ways to reach position `k`" — but position on a 2D grid
isn't a single number, it's a `(row, col)` PAIR, and the robot's two moves
(right, down) advance ONE coordinate at a time while leaving the other
fixed. There is no single index that captures "how far along the path you
are" without losing WHICH cell you're actually at. The state is
irreducibly two-dimensional:

```python
dp[i][j] = number of ways to reach cell (i, j)
dp[i][j] = dp[i-1][j] + dp[i][j-1]   # only two predecessors: up, left
```

Compare this to topic 16's `dp[i]` recurrences, which only ever read a
FIXED small window of smaller indices (`dp[i-1]`, `dp[i-2]`, …) along ONE
axis. Here, `dp[i][j]` reads neighbors along TWO independent axes at once.
That's the entire qualitative difference this topic is about.

---

## Part 1 · The four shapes "2D" takes in this folder

Not every `dp[i][j]` means the same thing. Recognizing WHICH shape you're
looking at is more valuable than memorizing any individual recurrence,
because the shape tells you the fill order, the space-optimization
strategy (if any), and which mistakes to guard against.

```arch
%% caption: The four shapes 2D DP takes, by what the two dimensions index.
grid 190x70
node r "2D DP: what do the two indices mean?" at 0,1.5 shape=pill w=170
node a "Grid position" at 1,0 color=blue w=180 sub="(row, col)"
node b "Two strings" at 1,1 color=purple w=180 sub="(i, j)"
node c "Day and holding-state" at 1,2 color=teal w=180 sub="(day, state)"
node d "Interval" at 1,3 color=orange w=180 sub="(left, right)"
node a1 "unique paths, min path sum" at 2,0 color=slate w=220
node b1 "LCS, edit distance" at 2,1 color=slate w=220
node c1 "stock trading with cooldown" at 2,2 color=slate w=220
node d1 "palindromic subsequence, burst balloons" at 2,3 color=slate w=220
r:R -> a:L
r:R -> b:L
r:R -> c:L
r:R -> d:L
a -> a1
b -> b1
c -> c1
d -> d1
```


### Shape 1 — Grid position (001–004)

`dp[i][j]` = the answer AT cell `(i, j)` of an actual input grid. Both
indices are literal row/column coordinates. Predecessors are always the
cell(s) immediately above and/or to the left (occasionally the diagonal
too, e.g. 004's Maximal Square). Fill row by row, left to right — dependency
order is just the grid's natural reading order.

| # | Problem | `dp[i][j]` MEANS | Predecessors |
|---|---|---|---|
| 001 | Unique Paths | ways to reach `(i,j)` | up, left (sum) |
| 002 | Unique Paths II | ways to reach `(i,j)`, obstacles zero it | up, left (sum), unless obstacle |
| 003 | Minimum Path Sum | min cost to reach `(i,j)` | up, left (min) |
| 004 | Maximal Square | side of largest all-1s square ending at `(i,j)` | up, left, up-left diagonal (min) |

### Shape 2 — Two strings, two indices (005, 009, 010, 012, 014)

`dp[i][j]` = the answer comparing PREFIX `i` of one sequence against PREFIX
`j` of another. This is the shape most people mean when they say "2D DP" in
an interview. Both indices are prefix LENGTHS into two DIFFERENT strings —
genuinely independent, because the two strings advance at unrelated rates.
Fill row by row (outer = one string's prefix length, inner = the other's).

```arch
%% caption: The LCS recurrence. Edit distance uses the same three neighbours, with min and +1 instead.
grid 170x80
node a "cell (i, j)" at 0.5,0 sub="compare a[i-1] with b[j-1]"
node b "equal?" at 0.5,1 shape=diamond color=amber
node c "dp[i][j] = dp[i-1][j-1] + 1" at 0,2 color=green w=210
node d "dp[i][j] = max(dp[i-1][j], dp[i][j-1])" at 1,2 w=260
a -> b
b -> c : "yes"
b -> d : "no"
```


| # | Problem | `dp[i][j]` MEANS | Combinator |
|---|---|---|---|
| 005 | Longest Common Subsequence | LCS length of `s1[:i]`, `s2[:j]` | max (match: diag+1; else max of 2 neighbors) |
| 009 | Interleaving String | can `s1[:i]`+`s2[:j]` interleave to `s3[:i+j]` | or (of 2 boolean AND-terms) |
| 010 | Edit Distance | min edits to turn `w1[:i]` into `w2[:j]` | min (match: diag; else min of 3 neighbors + 1) |
| 012 | Distinct Subsequences | count of `t[:j]` as a subsequence of `s[:i]` | sum (skip, plus use-if-match) |
| 014 | Regular Expression Matching | does `s[:i]` fully match pattern `p[:j]` | or (pattern-driven: literal / `.` / `*`) |

**The tell:** the problem statement names TWO strings/sequences as input,
and the question is about some relationship BETWEEN their prefixes
(equal, edit into, interleave into, count matches of one in the other).

### Shape 3 — Day × state (state-machine DP) (006)

`dp[day][state]` = the best value achievable ON this day, IN this state,
where "state" is a small, FIXED, enumerable set (not a continuous or
growing axis like the other shapes). The transition graph between states is
usually drawable as a small diagram with 2-4 nodes and directed edges. This
shape's "2D-ness" comes from (time × a small state machine), not (two
independent growing quantities).

| # | Problem | States | Key transition rule |
|---|---|---|---|
| 006 | Buy/Sell Stock w/ Cooldown | `held`, `sold`, `rest` | buying can only follow `rest`, never `sold` directly (the cooldown) |

**The tell:** "you may do X, but not immediately after Y" (cooldown, fee,
transaction limits) — the restriction is naturally expressed as "which
states can transition into which," not as an index relationship.

### Shape 4 — Interval DP (013)

`dp[l][r]` = the answer for the RANGE `[l, r]`, where the two indices are
the ENDPOINTS of a contiguous interval, not two independent positions or
two different sequences. The recurrence splits the interval at every
possible point `k` and combines the two resulting sub-INTERVALS —
`dp[l][k]` and `dp[k][r]` — which is why this shape cannot be filled
row-by-row: `dp[l][r]` depends on sub-intervals with SMALLER SPAN on both
sides, so the fill order must be by INCREASING INTERVAL LENGTH (`gap = r -
l`), a diagonal sweep across the table rather than a row sweep.

| # | Problem | `dp[l][r]` MEANS | Split rule |
|---|---|---|---|
| 013 | Burst Balloons | max coins bursting everything strictly between `l`,`r` | try every `k` as the LAST balloon burst in the range |

**The tell:** "given a sequence, choose an ORDER to remove/merge/split
elements, optimize some function of that order" — matrix chain
multiplication, polygon triangulation, and burst balloons are the classic
trio. The state is a SPAN, and the recurrence always asks "what's the last
(or first, or root) operation within this span."

**How to tell shapes 2 vs 4 apart when both show `dp[i][j]` on one string:**
topic 16's palindrome problems (`dp[i][j]` = is `s[i..j]` a palindrome) LOOK
like interval DP (both indices bound a span of the SAME string) but only
ever read ONE smaller sub-interval (`dp[i+1][j-1]`, the immediate interior)
— no split point `k` to search over. True interval DP (this topic's Shape
4) searches over EVERY possible split point, which is what forces the O(n)
inner loop and the resulting O(n^3) total complexity, versus topic 16's
O(n^2).

---

## Part 2 · Fill order is not optional — get it wrong and cells read garbage

Every shape above has EXACTLY one correct fill order, dictated by "which
smaller subproblems does this cell depend on":

```arch
%% caption: Each cell reads the cell above, to the left, and diagonally up-left. Fill top to bottom, left to right, and every dependency is already computed. Only the previous row is needed for the rolling-array optimisation.
route straight
grid 150x90
node diag "dp[i-1][j-1]" at 0,0 color=slate sub="diagonal"
node up "dp[i-1][j]" at 1,0 color=slate sub="above"
node left "dp[i][j-1]" at 0,1 color=slate sub="left"
node cur "dp[i][j]" at 1,1 color=amber
up -> cur
left -> cur
diag -> cur
```


- **Shape 1 (grid):** row-major (top to bottom, left to right) — `dp[i][j]`
  only ever depends on `dp[i-1][*]` or `dp[*][j-1]`, both already filled by
  the time you reach `(i,j)` in reading order.
- **Shape 2 (two strings):** row-major over `(i, j)` — same reasoning,
  `dp[i][j]` depends only on `dp[i-1][*]` and `dp[i][j-1]` (or, for 012's
  rolling optimization, the OPPOSITE sweep direction within a row — see
  Part 3).
- **Shape 3 (state machine):** simply increasing `day` — each day's states
  depend only on YESTERDAY's states, so a single forward pass suffices.
- **Shape 4 (interval):** increasing GAP (`r - l`), not row-major at all —
  `dp[l][r]` depends on `dp[l][k]` and `dp[k][r]` for every `k` strictly
  between, both of which have a smaller `r - l` than the outer interval.
  Filling row-by-row here would read UNINITIALIZED cells (dependencies
  computed later than the cell that needs them) and silently produce
  zeros/garbage instead of an error — this fill-order mistake is uniquely
  dangerous in Shape 4 because it doesn't crash, it just quietly returns 0
  for every interval, which can look like "a valid, if pessimistic, answer"
  rather than an obvious bug.

---

## Part 2a · Memory layout and CPU cache-hit implications: 1D vs 2D

Fill order (Part 2) is a correctness constraint. This is the *performance*
consequence of the same row-major reasoning, and it is worth being able to
state precisely, not just wave at "cache-friendly."

**What `dp = [[0]*cols for _ in range(rows)]` actually is.** Each inner
`[0]*cols` is its own heap-allocated `list` object — a contiguous C array
of **pointers** (`PyObject*`, 8 bytes each on a 64-bit build), not a
contiguous array of integers. Every `0` in it, for small ints, points at
one of CPython's cached singleton `int` objects (`-5..256`); outside that
range each value is its own separately-allocated `PyObject` (a 28-byte
`int` header for a one-digit value, more for larger magnitudes). So
`dp[i][j]` is, mechanically: **dereference the outer list's pointer array
to find row `i`'s list object → dereference that row list's pointer array
to find slot `j` → dereference that pointer to reach the actual int
object's value.** Three pointer chases, not one array index — this is
the concrete reason "Python is slow for numeric DP tables" is not vague
folklore; boxing turns every cell access into a chain of cache-unfriendly
indirections rather than a single offset computation.

**The row-major win still applies, at the outer-list level.** Traversing
`for i in range(rows): for j in range(cols): dp[i][j]`, the outer list's
own backing array of `rows` pointers is contiguous, so walking `i` in
order is one row-pointer-fetch per row, sequential and cache-friendly at
*that* level. Walking `j` inside a row is similarly sequential at the
row-list level. What is **not** contiguous is the actual integer data
each pointer leads to — those allocations land wherever the allocator
happened to put them, so unlike Go's flattened `[]int` (§ Go guide, same
topic), Python's pointer-chasing cost does not go away even with correct
row-major order; it only avoids being *made worse* by column-major
access.

**The genuine fix: `array.array` or NumPy, when the constraints justify it.**

```python
import array
row = array.array('q', [0]) * cols          # 'q' = signed 8-byte int, contiguous

import numpy as np
dp = np.zeros((rows, cols), dtype=np.int64)  # ONE contiguous allocation, row-major
                                              # by default (C order) — dp[i,j] is a
                                              # true offset computation, no boxing
```

`numpy.zeros((rows, cols))` allocates one contiguous block and computes
`dp[i, j]` as `base + (i*cols + j) * itemsize` — exactly the flattened-array
arithmetic the Go guide shows explicitly, done for you. This is a genuine
speedup on large grids evaluated in a hot loop, but for interview-sized DP
tables (LeetCode constraints are rarely more than low-thousands per
dimension) it is very rarely the right call to reach for mid-interview:
plain nested lists are what interviewers expect, `numpy` pulls in a
dependency and a `dtype`/overflow conversation you don't want to open
live, and the constant-factor win only matters at a scale these problems
don't test. State the trade-off if asked ("I'd use `array`/`numpy` for a
production numeric-heavy table; a nested list is the right default here
and for this interview"), but do not reach for it unprompted.

---

## Part 3 · Space optimization — when the rolling-row trick applies, and when it doesn't

Topic 16 collapsed `dp[i]` to O(1) by noticing the recurrence only reaches a
FIXED small window backward. The 2D analogue: if `dp[i][j]` only ever reads
the row directly above (plus, sometimes, the current row's own earlier
entries), the FULL O(m*n) table collapses to a SINGLE O(n) rolling row,
updated in place as you sweep row by row.

**This works for Shapes 1, 2, and 3** (001, 003, 004, 005, 006, 007, 008,
009, 010, 012, 014 all ship a rolling-row or rolling-scalar solution) — but
the DIRECTION of the in-place sweep is the single most consequential detail
in this entire topic, and it is NOT the same in every problem:

| Sweep direction | Why | Problems |
|---|---|---|
| Left-to-right, reading the SAME row's already-updated left neighbor | recurrence intentionally reuses THIS row's own new value (unbounded reuse, or "reads left") | 001, 003 (rolling row `row[j] += row[j-1]`-style), 005/010 LCS/Edit-Distance's diagonal-preserving sweep, 007 Coin Change II (coin outer, amount ascending — unbounded knapsack) |
| Right-to-left (high-to-low), so the same row's value is NOT yet touched | recurrence must read the PREVIOUS row's value at a smaller column, and updating low-to-high would clobber it first | 008 Target Sum (0/1 knapsack — each number usable once), 012 Distinct Subsequences (must read `dp[i-1][j-1]` before it's overwritten by this row's `dp[i][j-1]`) |
| Snapshot a scalar BEFORE overwriting (diagonal-preserving) | recurrence reads the diagonal `dp[i-1][j-1]`, which sits exactly where the in-place update is ABOUT to write `dp[i][j-1]` | 004 Maximal Square, 005 LCS, 010 Edit Distance |

**Getting 007 vs 008's direction backwards is the single most common,
highest-stakes mistake in this entire topic** — both look like "iterate
coins/items, iterate a sum array" with nearly identical code, but one is
unbounded (coins reusable, sweep low-to-high) and the other is 0/1 (each
number usable once, sweep high-to-low). Swapping them doesn't crash; it
silently computes a DIFFERENT, plausible-looking, wrong number (007's
solution file demonstrates this live: 4 correct combinations vs 9 if you
accidentally count permutations by using the wrong loop nesting; 008's
solution file demonstrates the reverse: 5 correct vs 70 if you sweep the
wrong direction).

**This does NOT work for Shape 4 (013, Burst Balloons).** `dp[l][r]`
depends on `dp[l][k]` and `dp[k][r]` for a split point `k` that ranges over
the ENTIRE interior of the interval — there is no fixed-offset neighbor to
roll away, because the dependency isn't "the row above" or "one column
back," it's "every smaller interval nested inside this one." 013's solution
file states this explicitly: the full O(n^2) table is genuinely required,
and this is worth saying out loud in an interview rather than reflexively
reaching for a space optimization that doesn't exist for this shape.

---

## Part 4 · The Hard problems — why each one is harder than its Medium cousins

**011 Longest Increasing Path in a Matrix** looks like Shape 1 (a grid) but
is really a DAG shortest/longest-path problem in disguise: because every
move must go to a STRICTLY LARGER value, the "increasing move" graph has NO
CYCLES by construction, which is what makes memoized DFS safe WITHOUT a
separate visited set (contrast with topic 14's ungrided graph DFS, which
DOES need one). The trap is recursion depth, not correctness: a
sufficiently long increasing chain can exceed Python's default recursion
limit even though the O(m*n) time complexity is fine — solved here by
processing cells in decreasing-value order (a topological sort of the DAG)
instead of recursing.

**012 Distinct Subsequences** is Shape 2, but the combinator is SUM of two
INDEPENDENT valid choices (skip vs. use), not a max/min pick-the-best like
LCS or Edit Distance — the "skip" option is always available and must
always be added, even when a character match exists, because both are
genuinely different subsequences that both need to be counted.

**013 Burst Balloons** is the only Shape 4 problem in the folder, and its
entire difficulty is the "burst LAST, not FIRST" reframe (Part 1, Shape 4)
— without that insight there IS no clean recurrence, because bursting first
leaves order-dependent, unknown neighbors for whatever remains.

**014 Regular Expression Matching** is Shape 2 with the added twist that
`'*'` makes `dp[i][j]` depend on TWO different places at once: `dp[i][j-2]`
(same row, sideways — the "zero occurrences" branch) AND `dp[i-1][j]` (row
above, same column — the "one more occurrence" branch, which deliberately
does NOT advance the pattern column, since `'*'` can match many characters
one at a time across repeated dp transitions). This dual dependency is why
014 needs TWO explicit rolling rows instead of one true in-place row like
004/005/010.

---

## Part 5 · A decision framework for choosing the shape

1. **Is the input a single grid/matrix, and does the question ask about
   paths, sums, or squares within it?** → Shape 1. Fill row-major, look for
   a rolling-row optimization first.

2. **Are there exactly TWO string/array inputs, and does the question ask
   about a relationship between them (equal, transform, interleave,
   count-contains)?** → Shape 2. State the recurrence as "compare the LAST
   character of each prefix," fill row-major, check whether the recurrence
   reads sideways (same row) or only upward before space-optimizing.

3. **Does the question describe a small number of DISCRETE STATES per time
   step, with restrictions on which state can follow which (cooldown, fee,
   limited transactions)?** → Shape 3. Draw the state transition diagram
   first, on paper, before writing any recurrence — the diagram IS the
   recurrence.

4. **Does the question ask you to choose an ORDER to remove/merge/combine
   elements of ONE sequence, optimizing some function of that order?** →
   Shape 4. State `dp[l][r]` as "the answer for the span `[l, r]`," find
   what the LAST (or first, or root) operation in that span implies about
   its neighbors, and fill by increasing interval length — never row-major.

5. **Sanity-check by asking: can I collapse this to `dp[i]` (topic 16)
   instead?** If one of the two indices is always DERIVABLE from the other
   (like 011's implicit third-string position in 009, which is `i+j-1`, not
   a free index) or if the "second dimension" is actually independent
   linear sub-problems (like topic 16's House Robber II decomposing into
   two 1D passes instead of one genuinely 2D one) — it might not be 2D DP
   at all. Confirming genuine independence between the two indices BEFORE
   writing `dp[i][j] = [[0]*n for _ in range(m)]` avoids over-engineering
   problems that are secretly 1D.

---

## Part 6 · Two traps specific to this topic

**Trap A — mixing up the four shapes' recurrences under time pressure.**
Shape 1's "min of up/left" (003), Shape 2's "max of two" (005) vs "min of
three" (010) vs "sum of two" (012) vs "or of two" (009, 014), and Shape 4's
"max over every split point k" (013) all involve 2-4 neighboring dp cells
combined with SOME operator — but the operator and which neighbors are read
differ per problem, and reaching for the wrong one (e.g. 005's max-of-two
instead of 010's min-of-three-plus-one) produces a plausible, wrong number
rather than a crash. Every solution file in this folder includes a live
runtime demo constructing exactly this confusion and printing the
divergence — read those before an interview, not just the correct code.

**Trap B — Shape 4's fill order is the one place in this whole topic (16 +
17 combined) where row-major iteration is actively wrong, not just
suboptimal.** Every other shape in both topics tolerates (even if it
doesn't require) a row-major or index-ascending sweep. Interval DP does
not: `dp[l][r]` needs sub-intervals with strictly smaller SPAN, which a
row-major sweep does not guarantee are already computed. This is worth
internalizing as a special case, precisely because everything else in two
topics' worth of practice reinforces "just go top-to-bottom, left-to-right"
as a safe default.

---

## Part 7 · Bitmask DP — a fifth shape, for "which SUBSET have I used"

None of Shapes 1–4 fit a problem where the state is "which of up to ~20
elements have I already used/visited," because the number of *subsets* is
exponential — but that exponential IS the point: a subset of up to ~20
items fits in a single machine integer, and "which subset" becomes an
`O(1)`-to-index dimension instead of an intractable one.

### 7.1 The representation

An `n`-element subset is an `n`-bit integer `mask`, where bit `i` set
means "element `i` is in this subset." `dp[mask]` (or `dp[mask][i]` when
you also need to track "and the last element visited was `i`," e.g. TSP)
answers a question about the elements named by `mask`.

```python
n = 4
full_mask = (1 << n) - 1          # 0b1111 — every element included

def is_in(mask, i):     return (mask >> i) & 1
def add(mask, i):       return mask | (1 << i)
def remove(mask, i):    return mask & ~(1 << i)
def popcount(mask):     return bin(mask).count("1")   # Python 3.10+: mask.bit_count()
```

### 7.2 State space and complexity — the exact bound, not a guess

A bitmask-DP table over `n` elements has `2^n` masks. With an additional
"last visited" dimension (the canonical Traveling Salesman Problem
formulation, Held–Karp), the table is `dp[mask][i]` for `i` an element
IN `mask` — `2^n * n` states, each transition trying up to `n` next
elements, giving **`O(2^n * n^2)`** total time and **`O(2^n * n)`**
space. This is *exponentially* better than the `O(n!)` brute-force
permutation search TSP naively implies — `n=15`: `15! ≈ 1.3 * 10^12`
versus Held–Karp's `2^15 * 15^2 ≈ 7.4 * 10^6`, roughly five orders of
magnitude fewer operations — but it is still exponential in `n`, which is
why bitmask DP is only viable for `n` up to roughly 20–22 (`2^22 ≈ 4.2M`
masks is already a lot of memory times an inner dimension; `2^25`+ is
generally infeasible). **Recognizing "n ≤ ~20" in the constraints is
itself the signal** that a problem wants bitmask DP — it is the
single most reliable tell for this shape, the way "sorted array" signals
binary search.

### 7.3 Held–Karp: the canonical worked example

"Visit every city exactly once, minimizing total distance, starting at
city 0" — `dp[mask][i]` = minimum cost to have visited exactly the
cities in `mask`, ending at city `i`.

```python
def tsp(dist: list[list[int]]) -> int:
    n = len(dist)
    INF = float("inf")
    # dp[mask][i]: min cost to visit exactly `mask`, currently at city i
    dp = [[INF] * n for _ in range(1 << n)]
    dp[1][0] = 0                       # start at city 0, mask = {0} = 0b1

    for mask in range(1 << n):
        for i in range(n):
            if dp[mask][i] == INF or not (mask >> i) & 1:
                continue               # i not reachable in this mask yet
            for j in range(n):
                if (mask >> j) & 1:
                    continue           # j already visited — can't revisit
                new_mask = mask | (1 << j)
                new_cost = dp[mask][i] + dist[i][j]
                if new_cost < dp[new_mask][j]:
                    dp[new_mask][j] = new_cost

    full = (1 << n) - 1
    return min(dp[full][i] + dist[i][0] for i in range(n))   # return to start
```

Fill order here is simply increasing `mask` — every transition goes from
`mask` to a STRICTLY LARGER mask (`popcount` strictly increases, since
`j` was, by construction, not yet in `mask`), so iterating `mask` from
`0` upward guarantees every source state is finalized before it's read —
the bitmask analogue of Shape 1's "row `i-1` before row `i`."

### 7.4 The "assignment" variant — matching, not touring

A second common shape: "assign `n` workers to `n` tasks, `mask` = which
tasks are already assigned, minimizing total cost" — here the *row*
index (which worker) is handled implicitly by `popcount(mask)` (the
count of set bits tells you exactly how many workers have been assigned
so far, hence which worker is next), collapsing what looks like a
`dp[worker][mask]` 2D-over-masks table into a 1D-over-masks one:

```python
def min_assignment_cost(cost: list[list[int]]) -> int:
    n = len(cost)
    dp = [float("inf")] * (1 << n)
    dp[0] = 0
    for mask in range(1 << n):
        worker = bin(mask).count("1")      # how many tasks assigned = next worker index
        if worker == n:
            continue
        for task in range(n):
            if (mask >> task) & 1:
                continue
            new_mask = mask | (1 << task)
            dp[new_mask] = min(dp[new_mask], dp[mask] + cost[worker][task])
    return dp[(1 << n) - 1]
```

This is the pattern behind LC 1879 (Minimum XOR Sum of Two Arrays) and LC
1947 (Maximum Compatibility Score Sum) — recognizing "assign each of N
things to N slots, minimize/maximize a pairwise cost" as THIS shape (not
Shape 1/2's grid-DP) is the transferable skill, not memorizing either
problem.

### 7.5 Submask enumeration — the other bitmask-DP primitive

A second recurring technique: iterating every SUBSET of a given mask
(not every mask), used when a state's transition depends on partitioning
`mask` into two disjoint pieces (e.g. "split this subset of jobs between
two workers, minimize the max load"):

```python
def submasks(mask: int):
    sub = mask
    while sub > 0:
        yield sub
        sub = (sub - 1) & mask
    yield 0     # the empty subset, if needed
```

`sub = (sub - 1) & mask` is the standard trick: subtracting 1 flips the
lowest set bit and sets every bit below it, and `& mask` clamps the
result back to a genuine subset of `mask`. This visits every one of a
mask's `2^popcount(mask)` non-empty subsets, and the total work across
ALL masks of an `n`-bit space is `sum over all subsets of 2^popcount`,
which is `O(3^n)` — the standard "sum over subsets" identity (each of
`n` bits is independently: absent from mask, present in mask but absent
from submask, or present in both — three choices, hence `3^n`), a bound
worth having cold since `3^n` for `n=20` (`3.5 * 10^9`) is where this
technique stops being practical, well before plain bitmask DP's `2^n`
ceiling.

### 7.6 Decision tell

| Signal in the problem | Shape |
|---|---|
| `n ≤ ~20`, "visit/use/assign every element exactly once," minimize/count over all orderings or assignments | **Bitmask DP**, `dp[mask]` or `dp[mask][i]` |
| Need to split a set into two (or more) parts and combine | Bitmask DP **with submask enumeration** |
| `n` in the hundreds/thousands, sequence-position based | NOT bitmask — back to Shapes 1–4 or topic 16 |

---

## Part 8 · Added Problems (015–018): Interval DP, State-Space BFS, and DIGIT DP

Added 16 Sep 2026 from the Google prep plan.

### 015 Longest Palindromic Subsequence — interval DP and fill order

`dp[i][j]` over ranges. It reads `dp[i+1][...]`, so rows go from `n-1` DOWN to 0. Filling top-down
reads rows that don't exist yet (the file runs that bug). Subsequence is not substring: `"bbbab"` is 4,
not 3. Also LPS(s) = LCS(s, reversed(s)), and minimum insertions to make a palindrome = n - LPS.

### 016 Shortest Path Visiting All Nodes — BFS over (node, mask)

Section 7 covers bitmask DP and Held–Karp. This problem shows the BFS face of the same state space:
state = (current node, visited mask), multi-source from every node, 12 * 4096 = 49,152 states. A
visited set keyed by node alone can't re-enter the hub of a star graph and never finishes.

### 017–018 · DIGIT DP — the template

Count numbers in [1, n] whose digits satisfy a rule. Build the number from the most significant
digit with state:

```
f(pos, tight, started, [extra state])
  pos      which digit position
  tight    prefix still equal to n's prefix? (bounds the next digit)
  started  placed a non-leading-zero digit yet? (leading zeros aren't digits)
  extra    whatever the rule needs: used-digit mask (018), digit sum, remainder mod k, last digit...
```

Ranges are always `count(hi) - count(lo - 1)`.

- **017 Numbers At Most N Given Digit Set** — the gentle one: shorter lengths `sum D^L`, then walk n's
  digits counting smaller allowed digits times `D^remaining`; stop at a disallowed digit; +1 if n
  itself is formable.
- **018 Count Special Integers** — mask of used digits. The `started` flag is the trap: without it,
  `n = 100` returns 72 instead of 90, because 7 padded to "007" looks like it repeats 0.

### Checklist additions

- [ ] I can state the fill order for any interval DP from which cells the recurrence reads.
- [ ] I can write the digit-DP template with tight and started flags and add one extra state.

<!-- block:17_py_1_beyond -->
## Part 9 · Beyond the Eighteen: Reconstruction, the Stock Family, LCS Cousins and Interval DP

The guide's shapes (grid, two strings, day × state, interval, bitmask, digit) cover the folder. These are the questions
asked *on top of* them. Every snippet was run against known answers while writing this section.

### 9.1 Recovering the answer from a 2D table — walk back from the corner

A DP table tells you the *value*; the *solution* is the path of decisions that produced it. Start at `dp[m][n]` and step
back, at each cell asking "which neighbour did I come from?":

```python
# LCS string: match → diagonal, else follow the larger neighbour
i, j, out = m, n, []
while i and j:
    if a[i-1] == b[j-1]: out.append(a[i-1]); i -= 1; j -= 1
    elif dp[i-1][j] >= dp[i][j-1]: i -= 1
    else: j -= 1
return dp[m][n], "".join(reversed(out))      # "abcde","ace" -> (3,"ace")     "AGGTAB","GXTXAYB" -> (4,"GTAB")
```

For **Edit Distance**, test the three predecessors in turn and record the operation — `dp[i][j] == dp[i-1][j-1] + 1` is a
*replace*, `== dp[i-1][j] + 1` a *delete*, `== dp[i][j-1] + 1` an *insert*, a plain match costs nothing:
`horse → ros` gives `replace h→r, delete r, delete e` (3 operations). Reconstruction needs the **full table** — the
rolling-row space optimisation throws away exactly what you walk back through, so you cannot have both.

### 9.2 The LCS family: one table, six questions

| Question | Reduce to |
|---|---|
| Longest common **subsequence** | the LCS table |
| Shortest common **supersequence** (LC 1092) | `len(a) + len(b) − LCS` (length `5` for `abac` / `cab`) |
| Minimum deletions to make two strings equal (LC 583) | `len(a) + len(b) − 2·LCS` (`sea`/`eat` → 2) |
| Longest palindromic **subsequence** | `LCS(s, reverse(s))` (`bbbab` → 4) |
| Longest common **substring** (contiguous) | the same table, but a **mismatch resets to 0** and the answer is the *maximum cell* (`abcdxyz`/`xyzabcd` → 4) |
| Edit distance | LCS's "agree or skip" plus *replace* |

The subsequence-vs-substring switch is the whole difference between two recurrences: `max(dp[i-1][j], dp[i][j-1])` on a
mismatch (skip a character) versus `0` (contiguity is broken).

### 9.3 The stock family as state machines

Every "Best Time to Buy and Sell Stock" variant is a small state machine over days. Write the states, then the
transitions — and **read all the old values before writing any** (tuple assignment does this for free):

```python
# Cooldown (LC 309): held → (sold) → rest → held.   You may not buy the day after selling.
held, sold, rest = max(held, rest - p), held + p, max(rest, sold)      # buy comes from REST, never from sold
# Transaction fee (LC 714): pay the fee when you sell
hold, cash = max(hold, cash - p), max(cash, hold + p - fee)
# At most k transactions (LC 188): a pair of arrays indexed by transaction count
for p in prices:
    for t in range(1, k + 1):
        hold[t] = max(hold[t], sold[t-1] - p)      # buy: begin transaction t out of the cash after t−1
        sold[t] = max(sold[t], hold[t] + p)        # sell: complete transaction t
```

`[1,2,3,0,2]` with cooldown → 3; `[1,3,2,8,4,9]` with fee 2 → 8; `k = 2` on `[3,3,5,0,0,3,1,4]` → 6, on `[3,2,6,5,0,3]` → 7. When
`k >= len(prices) // 2` the limit never binds — sum every positive day-to-day rise instead. Buying from `sold` (rather than
`rest`) is the cooldown bug; using the *updated* `rest` when computing the new `held` is the ordering bug.

### 9.4 Wildcard matching (LC 44) versus regex (LC 10)

Both are `dp[i][j]` = "does `s[:i]` match `p[:j]`". The difference is what `*` means:

| | `*` means | On `*` in the pattern |
|---|---|---|
| Regex (LC 10) | *zero or more of the previous element* | `dp[i][j-2]` (drop the pair) **or** `dp[i-1][j]` if the previous element matches `s[i-1]` |
| Wildcard (LC 44) | *any sequence, including empty* | `dp[i][j-1]` (match empty) **or** `dp[i-1][j]` (absorb one more character) |

```python
if p[j-1] == '*': dp[i][j] = dp[i][j-1] or dp[i-1][j]              # wildcard: empty, or one more character
elif p[j-1] in ('?', s[i-1]): dp[i][j] = dp[i-1][j-1]
# ("aa","a") F   ("aa","*") T   ("cb","?a") F   ("adceb","*a*b") T   ("acdcb","a*c?b") F
```

Seed `dp[0][j]` for leading `*`s (a pattern of stars matches the empty string). The regex trap is reading `dp[i-1][j-2]`
instead of `dp[i-1][j]` for "one more occurrence" — that caps `*` at exactly one extra character.

### 9.5 Interval DP: the template, and the 1D DP hiding on top of a 2D one

**Interval DP** answers a question about every range `[i, j]` from smaller ranges inside it: fill by **increasing length**,
and try every split point `k`. Matrix Chain Multiplication is the archetype; Burst Balloons (last balloon), Minimum Cost to
Merge Stones and Strange Printer are the same loop:

```python
for length in range(2, n + 1):
    for i in range(n - length + 1):
        j = i + length - 1; dp[i][j] = inf
        for k in range(i, j):
            dp[i][j] = min(dp[i][j], dp[i][k] + dp[k+1][j] + cost(i, k, j))
# matrix chain: dims [10,30,5,60] -> 4500     [40,20,30,10,30] -> 26000
```

That is O(n³). **Palindrome Partitioning II** (minimum cuts) is a *1D* DP over a *2D* precomputed table: build
`pal[i][j]` once (O(n²)), then `cut[i] = min(cut[j] + 1)` over every `j` where `s[j:i]` is a palindrome — `"aab"` → 1,
`"aaaa"` → 0.

### 9.6 Choosing between top-down and bottom-up in 2D

| Situation | Prefer |
|---|---|
| Every cell is needed and the dependency order is obvious (LCS, Edit Distance, grids) | bottom-up: tight loops, rolling rows |
| Only a sparse set of states is reachable (Regex, Interleaving with pruning, Longest Increasing Path) | top-down memo: computes only what is asked |
| The dependency order is not a simple sweep (Longest Increasing Path in a Matrix) | memoised DFS — the strict-increase rule guarantees no cycles, so no `visited` set is needed |
| Recursion depth would exceed ~1000 (CPython) | bottom-up, or an explicit order |

### 9.7 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Return the actual subsequence / edit script." | Keep the full table and walk back from the corner (9.1). |
| "Reduce the space." | Two rolling rows (or one row plus a saved diagonal value) — only when you need the *value*, not the path. |
| "Weighted edit costs? Transpositions (Damerau)?" | Replace the `+1`s by per-operation costs; a transposition adds a fourth neighbour `dp[i-2][j-2]`. |
| "What if the strings are huge?" | Hirschberg's algorithm recovers an LCS in O(min(m, n)) space by divide and conquer. |
| "At most k transactions, unlimited k?" | The pair-of-arrays form; when `k ≥ n/2` just sum the positive differences. |
| "Why is this O(n³)?" | An interval DP has O(n²) states and an O(n) split point per state. |
| "Can it be solved greedily?" | State the counter-example for greedy first; the fact that a locally best choice fails is what forces DP. |

---
<!-- /block:17_py_1_beyond -->

<!-- problem-map:start -->
## Part 10 · Every Problem in This Topic, by Pattern

Eighteen problems, six shapes (grid position · two strings · day × state · knapsack-as-2D · interval · bitmask/digit). Each **Trap** is a mistake documented in that problem's solution file.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Unique Paths](PyDSA/17_dp_2d/001_unique_paths_solution.py) <br>LC 62 · Medium | Grid: sum of two predecessors | A cell is reachable only from above or from the left, so `dp[i][j] = dp[i-1][j] + dp[i][j-1]`; one rolling row suffices. **Trap:** an `m × m` or `n × n` table; initialising the rolling row to `0` instead of `1`. |
| [002 · Unique Paths II](PyDSA/17_dp_2d/002_unique_paths_ii_solution.py) <br>LC 63 · Medium | Grid with an obstacle override | 001's recurrence, with `dp = 0` on an obstacle. **Trap:** applying the start-cell check to the answer but not to `dp[0][0]`; reusing 001's "first row and column are all 1s" (false once an obstacle appears). |
| [003 · Minimum Path Sum](PyDSA/17_dp_2d/003_minimum_path_sum_solution.py) <br>LC 64 · Medium | Grid: min of two, plus own cost | The same predecessor rule, but `dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])`. **Trap:** summing both predecessors out of habit; treating the first row/column as copies (they are *cumulative* sums). |
| [004 · Maximal Square](PyDSA/17_dp_2d/004_maximal_square_solution.py) <br>LC 221 · Medium | Grid: side of the square ending here | `dp[i][j]` = the largest all-1s square whose **bottom-right corner** is `(i, j)`: `1 + min(up, left, diagonal)`. **Trap:** `max` instead of `min`; omitting the diagonal (that is the path recurrence). |
| [005 · Longest Common Subsequence](PyDSA/17_dp_2d/005_longest_common_subsequence_solution.py) <br>LC 1143 · Medium | Two strings: LCS | `dp[i][j]` over *prefix lengths*: match → `dp[i-1][j-1] + 1`, else `max(dp[i-1][j], dp[i][j-1])`. **Trap:** comparing `a[i]` with `b[j]` instead of `a[i-1]` with `b[j-1]`; confusing subsequence with substring. |
| [006 · Best Time to Buy and Sell Stock with Cooldown](PyDSA/17_dp_2d/006_best_time_to_buy_and_sell_stock_with_cooldown_solution.py) <br>LC 309 · Medium | Day × state machine | Three states — held, just sold, resting — with all right-hand sides read from *yesterday*. **Trap:** buying from `sold` (violates the cooldown; it must come from `rest`); updating the rolling scalars in place in the wrong order. |
| [007 · Coin Change II](PyDSA/17_dp_2d/007_coin_change_ii_solution.py) <br>LC 518 · Medium | Unbounded knapsack, combinations | `dp[a] += dp[a - c]` with **coins outermost** and amounts ascending. **Trap:** amounts outermost (counts permutations); scanning high to low (that is 0/1). |
| [008 · Target Sum](PyDSA/17_dp_2d/008_target_sum_solution.py) <br>LC 494 · Medium | 0/1 knapsack via a reframe | Split into a positive subset `P` with `sum(P) = (target + total) / 2`, then count subsets, scanning **high to low**. **Trap:** scanning low to high; not guarding `(target + total)` odd or `\|target\| > total`. |
| [009 · Interleaving String](PyDSA/17_dp_2d/009_interleaving_string_solution.py) <br>LC 97 · Medium | Two strings, interleaving | `dp[i][j]` = can `s1[:i]` and `s2[:j]` interleave to `s3[:i+j]` — the third index is *always* `i + j`. **Trap:** a third free dimension; `and` instead of `or` between the two sources. |
| [010 · Edit Distance](PyDSA/17_dp_2d/010_edit_distance_solution.py) <br>LC 72 · Medium | Two strings, edit distance | Match → `dp[i-1][j-1]` (no `+1`); else `1 + min(replace, delete, insert)`. **Trap:** adding 1 on a match; losing the diagonal value in the rolling-row version. |
| [011 · Longest Increasing Path in a Matrix](PyDSA/17_dp_2d/011_longest_increasing_path_in_a_matrix_solution.py) <br>LC 329 · Hard | Memoised DFS on a grid | `dp` = longest strictly increasing path *starting* here; the strict increase forbids cycles, so no `visited` set. **Trap:** `>=` (plateaus become "increasing"); a redundant, possibly shared `visited`. |
| [012 · Distinct Subsequences](PyDSA/17_dp_2d/012_distinct_subsequences_solution.py) <br>LC 115 · Hard | Two strings, counting | When characters match, `dp[i-1][j-1] + dp[i-1][j]` — *use it* plus *skip it*, both valid and different. **Trap:** `max` instead of sum; dropping the always-allowed "skip" term on a match. |
| [013 · Burst Balloons](PyDSA/17_dp_2d/013_burst_balloons_solution.py) <br>LC 312 · Hard | Interval DP: the *last* balloon | Choose which balloon bursts **last** in `(l, r)`, so the two sides are independent; pad with virtual `1`s. **Trap:** reasoning about the *first* burst (the neighbours become order-dependent); forgetting the padding. |
| [014 · Regular Expression Matching](PyDSA/17_dp_2d/014_regular_expression_matching_solution.py) <br>LC 10 · Hard | Two strings, pattern-driven | Case on `p[j-1]`: a letter or `.` matches one character; `*` means zero-or-more of the previous element. **Trap:** no zero-occurrence branch; reading `dp[i-1][j-2]` instead of `dp[i-1][j]`. |
| [015 · Longest Palindromic Subsequence](PyDSA/17_dp_2d/015_longest_palindromic_subsequence_solution.py) <br>LC 516 · Medium | Interval DP on a string | `dp[i][j] = dp[i+1][j-1] + 2` on matching ends, else `max(dp[i+1][j], dp[i][j-1])`; `dp[i][i] = 1`. **Trap:** solving the *substring* problem (`"bbbab"` → 3, not 4); filling `i` ascending (reads cells not yet computed). |
| [016 · Shortest Path Visiting All Nodes](PyDSA/17_dp_2d/016_shortest_path_visiting_all_nodes_solution.py) <br>LC 847 · Hard | BFS over `(node, mask)` | Search *states*: revisiting a node is fine, revisiting a state never helps; start from *every* node at once. **Trap:** `visited` keyed by node alone; a single source at node 0. |
| [017 · Numbers At Most N Given Digit Set](PyDSA/17_dp_2d/017_numbers_at_most_n_given_digit_set_solution.py) <br>LC 902 · Hard | Digit DP: shorter, then same length | Numbers shorter than `n` are all valid (`D^L` each); same length walks `n` while `tight`. **Trap:** forgetting to count `n` itself; forgetting the shorter lengths (`n = 100` returns 0 instead of 20). |
| [018 · Count Special Integers](PyDSA/17_dp_2d/018_count_special_integers_solution.py) <br>LC 2376 · Hard | Digit DP with a used-digit mask | State `(pos, mask, tight, started)`; `started` makes leading zeros free padding. **Trap:** no `started` flag (`n = 100` gives 72, not 90); allowing `0` as the first digit of the same-length walk. |

---
<!-- problem-map:end -->


## Checklist Before Leaving This Topic <!--ca-->

- [ ] Reconstruct an LCS string and an edit script by walking back from `dp[m][n]`, and say why rolling rows lose it <!--ca-->
- [ ] Reduce shortest common supersequence, minimum deletions and palindromic subsequence to LCS <!--ca-->
- [ ] Write the stock variants (cooldown, fee, k transactions) as state machines that read only *yesterday's* values <!--ca-->
- [ ] Tell wildcard (`*` = any sequence) from regex (`*` = repeat the previous element) and write both recurrences <!--ca-->
- [ ] Fill an interval DP by increasing length and name its O(n³) cost <!--ca-->
