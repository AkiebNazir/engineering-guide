# Topic 16 · 1D Dynamic Programming — Python Deep Dive

> Topic 09 taught you recursion over decision trees where every node is a
> **distinct** partial state — nothing to cache, because nothing repeats.
> This topic is the mirror image: recursion where the SAME subproblem gets
> asked for over and over again from different branches, and the entire
> skill is (1) noticing that, and (2) exploiting it. That exploitation has
> a name — dynamic programming — and it always follows the same four-stage
> progression: naive recursion -> memoized top-down -> tabulated bottom-up
> -> space-optimized. Learn that progression once, on one tiny example,
> and every problem in this folder is a variation on it.
>
> "1D" means the state that describes a subproblem collapses to a single
> integer index — `dp[i]` — as opposed to topic 17's `dp[i][j]`. That's the
> entire difference between the two topics: how many numbers you need to
> uniquely name "the subproblem I'm currently solving."

---

## Part 0 · The progression, on one example: climbing stairs

Take `climbStairs(n)`: how many distinct ways to climb `n` stairs, taking 1
or 2 steps at a time. To reach step `n`, your last move was either a
single step from `n-1`, or a double step from `n-2` — so every way to reach
`n` is a way to reach `n-1` (then +1) or a way to reach `n-2` (then +2), and
those two sets never overlap (they're distinguished by the last move).
That gives the recurrence `ways(n) = ways(n-1) + ways(n-2)`.

```arch
%% caption: The four stages of a DP solution and what each one costs.
grid 175x80
node a "1. Naive recursion" at 0,0 color=red sub="O(2^n) time"
node b "2. Memoize (top-down)" at 1,0 sub="O(n) time, O(n) space"
node c "3. Tabulate (bottom-up)" at 2,0 sub="O(n) time, O(n) table"
node d "4. Keep only what is read" at 3,0 color=green sub="O(n) time, O(1) space"
a -> b -> c -> d
```


### Stage 1 — naive recursion (state it, price it, do not ship it)

```arch
%% caption: Naive recursion recomputes the same subproblems: f(3) twice, f(2) three times. Only n distinct states exist, so caching each one turns O(2^n) into O(n).
route straight
grid 80x80
node f5 "f(5)" at 2,0 shape=circle color=blue
node f4 "f(4)" at 1,1 shape=circle color=blue
node f3a "f(3)" at 3,1 shape=circle color=red
node f3b "f(3)" at 0.5,2 shape=circle color=red
node f2a "f(2)" at 1.5,2 shape=circle color=amber
node f2b "f(2)" at 2.5,2 shape=circle color=amber
node f1a "f(1)" at 3.5,2 shape=circle color=blue
node f2c "f(2)" at 0,3 shape=circle color=amber
node f1b "f(1)" at 1,3 shape=circle color=blue
f5 -> f4
f5 -> f3a
f4 -> f3b
f4 -> f2a
f3a -> f2b
f3a -> f1a
f3b -> f2c
f3b -> f1b
```


```python
def ways(n):
    if n <= 2:
        return n          # 1 way to climb 1 step, 2 ways to climb 2
    return ways(n - 1) + ways(n - 2)
```

Correct. Also `O(2^n)` (really `O(phi^n)`) because `ways(n-2)` gets computed
once directly and once again *inside* the `ways(n-1)` call — and that
duplication compounds at every level. Draw the call tree for `ways(5)` and
`ways(3)` appears twice, `ways(2)` three times. This is IDENTICAL to
`fib(n)` from topic 09 problem 001 — same recurrence shape, different cover
story. **The tree has exponentially many nodes but only `n` DISTINCT
node labels** — that gap between "nodes visited" and "distinct labels" is
what every remaining stage closes.

### Stage 2 — memoized top-down (cache the distinct labels)

```python
def ways(n, memo={}):
    if n <= 2:
        return n
    if n in memo:
        return memo[n]
    memo[n] = ways(n - 1, memo) + ways(n - 2, memo)
    return memo[n]
```

Same recursion, same call *shape*, but now the second time any `n` is
requested it's an `O(1)` dict lookup instead of a re-descent. Collapses
`O(2^n)` calls down to `O(n)` distinct computations — each label solved
exactly once, looked up every other time. This is still recursion, still
pays call-stack overhead and Python's recursion-depth ceiling, but it is
now polynomial.

### Stage 3 — tabulation / bottom-up (fill the table in dependency order)

Memoization asks "top-down, cache as I go, recursion decides the order."
Tabulation flips it: figure out the dependency order yourself (`dp[i]`
only needs `dp[i-1]` and `dp[i-2]`, both smaller indices) and fill an
array left to right, no recursion, no call stack at all.

```python
def ways(n):
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]
```

`dp` table for `n = 5`:

```
 i   : 0  1  2  3  4  5
dp[i]: -  1  2  3  5  8
             ^^^^^^^^^ each cell built from the two cells just before it
```

Exactly the same `O(n)` distinct values as memoization, but as an explicit
loop: no recursion depth limit, no per-call stack-frame overhead, and the
computation order is visible on the page instead of implied by call order.

### Stage 4 — space optimization (keep only what the recurrence actually reads)

`dp[i]` only ever reads `dp[i-1]` and `dp[i-2]` — never anything older. The
full array is `O(n)` space to hold information you need only the last two
cells of. Replace the array with two rolling variables:

```python
def ways(n):
    if n <= 2:
        return n
    prev2, prev1 = 1, 2               # dp[1], dp[2]
    for _ in range(3, n + 1):
        prev2, prev1 = prev1, prev2 + prev1
    return prev1
```

`O(n)` time unchanged, `O(1)` space. **This is the version to actually
write in an interview** once you've shown you understand the table it
replaces — say the tabulated version out loud first, then optimize it,
rather than jumping straight to rolling variables and hoping the
interviewer trusts you skipped a step correctly.

This exact four-stage arc — price the exponential recursion, memoize it,
tabulate it, then roll the window down to O(1) where the recurrence's
"reach" allows it — is applied, unchanged, to all sixteen problems below.
What changes per problem is only: what does `dp[i]` MEAN, and how far back
does the recurrence reach (Part 2).

---

## Part 1 · Recognizing a 1D <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> problem

Ask two questions:

1. **Can I describe "the subproblem at position `i`" with a single number
   `i`** — an index into the input, or an amount, or a length — such that
   the answer to the whole problem is `dp[n]` (or a simple combination of a
   few `dp[i]` values, e.g. `max(dp)`)?
2. **Does solving `dp[i]` only need a handful of SMALLER, already-solved
   subproblems** (`dp[i-1]`, `dp[i-2]`, ..., or a bounded/scanned range
   `dp[j]` for `j < i`) — not the whole future, and not a second
   independent dimension like "which items are still available"?

If both are "yes," it's 1D <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>. If the state needs a *pair* of indices (two
pointers into two different strings, a `(row, col)` in a grid, "index AND
how much budget is left" as two independent knobs that both vary) — that's
topic 17 (2D <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>). If there's no overlap between subproblems at all (every
node in the recursion tree is a genuinely distinct partial answer, like
Topic 09's subsets/permutations) — that's backtracking, not <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>; caching
buys nothing because nothing repeats.

**The giveaway phrases** that point at 1D <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>: "number of ways to reach/make
...", "minimum cost to reach/climb/decode...", "longest such-and-such
ending at/starting at position i", "can you partition/break this into...".
Each maps directly onto a state definition in the table below.

---

## Part 2 · State definition discipline — what `dp[i]` MEANS, not how it's built

The single most common way this topic goes wrong isn't a coding bug, it's
starting to code before deciding, in one plain English sentence, what
`dp[i]` represents. The recurrence (how to *compute* `dp[i]` from earlier
cells) falls out mechanically once the meaning is nailed down — but guessing
the recurrence first, without the sentence, produces code that happens to
pass the first two examples and breaks on an edge case nobody thought to
check.

Every problem in this folder, stated as a "`dp[i]` MEANS" sentence:

| # | Problem | `dp[i]` MEANS |
|---|---|---|
| 001 | N-th Tribonacci | the tribonacci value at index `i` |
| 002 | Climbing Stairs | number of distinct ways to reach step `i` |
| 003 | Min Cost Climbing Stairs | minimum cost to REACH step `i` (having already paid to leave it or not, per the exact LC phrasing) |
| 004 | Pascal's Triangle | `dp[i][j]` = the value at row `i`, col `j` (2D indices, but each row is built by scanning only the PREVIOUS row — a 1D recurrence applied row by row) |
| 005 | House Robber | max loot achievable using only houses `0..i`, choosing whether to include house `i` |
| 006 | House Robber II | same as 005, run twice over two linear slices to break the circular adjacency |
| 007 | Longest Palindromic Substring | `dp[i][j]` = is `s[i..j]` a palindrome (built from the SMALLER interior `dp[i+1][j-1]` — 1D-style "smaller subproblem" reasoning even though indexed by a pair) |
| 008 | Palindromic Substrings | same `dp[i][j]` meaning as 007, count instead of locate-longest |
| 009 | Decode Ways | number of ways to decode the PREFIX `s[:i]` |
| 010 | Coin Change | minimum number of coins to make EXACTLY amount `i` |
| 011 | Maximum Product Subarray | `maxEnd[i]` / `minEnd[i]` = max/min product of a subarray ENDING exactly at `i` (two rolling states because a negative can flip min into max) |
| 012 | Word Break | `dp[i]` = can the prefix `s[:i]` be segmented into dictionary words |
| 013 | Longest Increasing Subsequence | `dp[i]` = length of the longest increasing subsequence ENDING exactly at index `i` |
| 014 | Partition Equal Subset Sum | `dp[s]` = is subset-sum `s` achievable using the items considered so far (0/1 knapsack collapsed to 1D over the sum axis) |
| 015 | Combination Sum IV | `dp[t]` = number of ordered combinations that sum to exactly `t` |
| 016 | Perfect Squares | `dp[n]` = minimum count of perfect squares that sum to exactly `n` |

Notice the two shapes hiding in "1D": most of these are **index-indexed**
(`dp[i]` = answer about the input up to/at position `i`) and a few
(010, 014, 015, 016) are **value-indexed** (`dp[amount]` = answer about
that target number, independent of any array position — this is the
"unbounded knapsack on the target value" shape). Same discipline, different
axis.

**Practice saying the sentence before writing a line of code.** "`dp[i]` is
the minimum coins to make amount `i`" is checkable against small examples
by hand; "some array that helps with coins" is not, and is where every
avoidable bug in this topic comes from.

---

## Part 3 · A decision framework for choosing the state

Work through these in order:

```arch
%% caption: Choosing what dp[i] should mean.
grid 200x80
node q "Optimisation or counting problem" at 0,0 shape=pill
node a "Depends only on last few items?" at 0,1 shape=diamond color=amber
node a1 "dp[i] = best for first i items" at 1,1 color=green w=230 sub="climb stairs, house robber"
node b "Subsequence must END at i?" at 0,2 shape=diamond color=amber
node b1 "dp[i] = best ENDING at i" at 1,2 color=green w=230 sub="LIS; final answer: max over all i"
node c "Choose items to hit a target?" at 0,3 shape=diamond color=amber
node c1 "dp[t] = best for target t" at 1,3 color=green w=230 sub="coin change, knapsack"
node d "Add a dimension" at 0,4 color=slate sub="topic 17"
q -> a
a -> a1 : "yes"
a -> b : "no"
b -> b1 : "yes"
b -> c : "no"
c -> c1 : "yes"
c -> d : "no"
```


1. **What does the question ask for at the very end?** A count ("how many
   ways"), an optimum ("min cost" / "max profit" / "longest"), or a
   yes/no ("can it be done")? This fixes what `dp[i]` STORES (a count, a
   number, a boolean) before you've picked what `i` even ranges over.

2. **What does "the last decision" look like?** <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> recurrences are almost
   always "what was the LAST step taken to arrive at state `i`, and what do
   I need to already know to evaluate each candidate last-step?" For
   climbing stairs, the last step was a 1-move or a 2-move — two
   candidates, `dp[i-1]` and `dp[i-2]`. For word break, the last decision
   was "which dictionary word ends exactly at position `i`" — scan all
   valid word lengths ending there. For <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr>, the last decision was "which
   earlier, smaller element does this one extend" — scan all `j < i` with
   `nums[j] < nums[i]`.

3. **Does the reach go back a FIXED small window, or does it scan a
   variable range?** Fixed window (tribonacci: 3 back; climbing stairs:
   2 back; house robber: 2 back) means an O(n) loop with O(1)
   space-optimization available (Part 0 stage 4). Variable range (<abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr>,
   word break, coin change, decode ways, combination sum IV) means an
   inner loop/scan per `dp[i]`, usually O(n) or O(n * target) total — no
   free space optimization, because you may need every earlier cell, not
   just the last two.

4. **Is there a hidden SECOND axis trying to sneak in?** House Robber II's
   circular constraint ("can't rob both the first and last house") looks
   like it needs 2D state ("robbed first? y/n") but decomposes into TWO
   independent 1D runs (exclude house 0, exclude house n-1, take the max)
   instead — recognizing when a constraint splits into independent 1D
   passes rather than actually adding a dimension is itself a skill this
   topic builds. Partition Equal Subset Sum looks like it needs
   `dp[item][sum]` (classic 0/1 knapsack) but the item axis can be
   collapsed away by iterating sums in reverse (Part 4) — study 014's
   solution file for exactly why the iteration DIRECTION substitutes for
   the missing dimension.

5. **Sanity-check the base case(s) and the answer's location.** Off-by-one
   errors dominate this topic's bugs (Part 0's `dp[0]` vs `dp[1]`
   indexing, whether the final answer is `dp[n]`, `dp[n-1]`, or
   `max(dp)`). Trace the smallest 2-3 inputs by hand against your stated
   `dp[i]` sentence before trusting the recurrence on anything bigger.

---

## Part 4 · Two traps specific to this topic

**Trap A — iteration direction matters when you space-optimize a knapsack
onto 1D.** Collapsing `dp[item][sum]` down to `dp[sum]` (014, and the
unbounded-vs-bounded distinction in 015 vs 014) is only correct if you scan
the sum axis in the direction that stops you from reusing the same item
twice (0/1 knapsack: iterate sums HIGH to LOW) or, conversely, DOES let you
reuse an item within the same pass (unbounded/coin-style: iterate sums LOW
to HIGH). Getting the direction backwards produces a number that looks
plausible and is wrong — it silently changes which knapsack variant you
just implemented. This is the single most missed detail in the whole
folder; 014's solution file traces both directions on a tiny input so you
can see the wrong-direction answer diverge from the right one.

**Trap B — Python's recursion limit is real at <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr>-relevant depths.** Naive
or even memoized top-down recursion for `n` up to a few thousand can hit
Python's default `sys.getrecursionlimit()` (1000) well before it hits any
time-complexity trouble — a purely CORRECT `O(n)` memoized solution can
still crash with `RecursionError` on a large enough input, which is
exactly why tabulation (no call stack at all) is the version several files
below actually ship, and why more than one runtime demo in this folder
measures that crash happening live rather than asserting it could.

---

## Part 5 · Where this topic ends and topic 17 begins

Every problem here reduces to ONE number per state (`dp[i]`) or, at most,
a constant handful of ROLLING numbers per index (011's max/min pair, 006's
two independent linear passes). The moment a problem needs `dp[i][j]` where
BOTH `i` and `j` vary independently across the whole recursion and neither
can be collapsed away by a clever reformulation (016's "sum of squares" is
value-indexed but still genuinely 1D; a two-string edit-distance problem is
genuinely 2D because both string positions vary together) — that's topic
17. Recognizing which one you're looking at, fast, in an interview, is
worth more than knowing any individual recurrence by heart, because the
recurrence is derivable once you've correctly named the state.

---

## Part 6 · Added Problem (017) · Russian Doll Envelopes — Reducing 2D to <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr>

Added 16 Sep 2026 from the Google prep plan.

Sort by **width ascending, height DESCENDING**, then take the longest STRICTLY increasing subsequence of
heights with the patience-sorting `tails` array and `bisect_left`.

- Width ascending: any nesting chain reads left to right.
- Height descending for equal widths: two same-width envelopes can never both be in an increasing
  height sequence, so equal widths never falsely nest (`[[3,4],[3,5]]` -> 1, not 2).
- `bisect_left`, not `bisect_right`: equal heights must replace, not extend (`[[1,1],[2,1]]` -> 1).

Measured: O(n^2) <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> took ~445 ms at n = 4,000; the <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr> version took ~1 ms, and ~41 ms at n = 100,000.

- [ ] I can explain both halves of the sort key and the bisect_left choice.

<!-- block:16_py_1_families -->
## Part 7 · The Six 1D DP Families, With the Code That Distinguishes Them

The guide teaches the *method* (state → transition → base case → order). This Part is the catalogue: the six shapes every
problem in the folder falls into, and — the part interviews probe — **the one line that separates two families that look
identical**. Every snippet was run against LeetCode's own examples while writing this section.

```arch
%% caption: The six 1D shapes. The wording of the question picks the family; the family fixes the loop order and the direction.
grid 200x80
node q "1D DP problem" at 0,1 shape=pill
node a "What varies?" at 0,2 shape=diamond color=amber
node l "Linear recurrence" at 1,0 color=green w=400 sub="position i, FIXED look-back · Fibonacci, Stairs, Tribonacci"
node t "Take-or-skip" at 1,1 color=green w=400 sub="position i, take it or skip it · House Robber I and II"
node u "Unbounded knapsack" at 1,2 color=amber w=400 sub="target VALUE, items reusable · Coin Change, Perfect Squares, Combination Sum IV"
node z "0/1 knapsack, sums HIGH to LOW" at 1,3 color=amber w=400 sub="target VALUE, each item once · Partition Equal Subset Sum"
node s "Sequence DP" at 1,4 color=green w=400 sub="best ENDING at i, scan earlier j · LIS, Word Break, Decode Ways, Max Product"
node p "Substring DP" at 1,5 color=green w=400 sub="a centre or an interval · Palindromes: expand or table"
q -> a
a:R -> l:L
a:R -> t:L
a:R -> u:L
a:R -> z:L
a:R -> s:L
a:R -> p:L
```

### 7.1 Take or skip — House Robber I and II

At each house you either **skip** it (keep the best so far) or **take** it (its value plus the best from two houses ago).
Two rolling variables are enough:

```python
take = skip = 0
for x in nums:
    take, skip = skip + x, max(take, skip)      # take needs the PREVIOUS skip; both sides use the OLD values
return max(take, skip)                          # [1,2,3,1] -> 4     [2,7,9,3,1] -> 12
```

The circular version (house 0 is adjacent to house n−1) is **two linear runs**: either house 0 is excluded or house n−1 is —
`max(rob(nums[1:]), rob(nums[:-1]))` — with the `len == 1` case handled separately (`[2,3,2]` → 3, `[1,2,3,1]` → 4).

### 7.2 Unbounded knapsack — and the loop-order fork that counts different things

Coin Change (minimum coins) is order-independent, so either loop order works:

```python
dp = [0] + [INF] * amount
for a in range(1, amount + 1):
    for c in coins:
        if c <= a: dp[a] = min(dp[a], dp[a - c] + 1)
# [1,2,5], 11 -> 3     [2], 3 -> -1     amount 0 -> 0     (INF, not -1, as the "unreachable" sentinel)
```

But when you **count** ways, the loop order changes *which* thing you count. **Coins outside, amount inside** counts
*combinations* (order does not matter); **amount outside, coins inside** counts *sequences* (order matters):

```python
# combinations (Coin Change II)              # sequences (Combination Sum IV — despite its name)
dp = [1] + [0] * amount                       dp = [1] + [0] * target
for c in coins:                               for t in range(1, target + 1):
    for a in range(c, amount + 1):                for x in nums:
        dp[a] += dp[a - c]                            if x <= t: dp[t] += dp[t - x]
# coins [1,2,5], amount 5:  4 combinations   |  9 sequences        [1,2,3], target 4: 7 sequences
```

Copy Coin Change II's structure into Combination Sum IV and you silently **under-count**. Say out loud whether order
matters, then choose the loop order — it is the same decision as Permutations vs Combinations in topic 09.

### 7.3 0/1 knapsack in one dimension — the direction *is* the missing axis

Partition Equal Subset Sum is "does a subset reach `total/2`?" with **each item used once**. The 2D table
`dp[item][sum]` collapses to `dp[sum]` only if you scan sums **high to low**, so `dp[s - x]` still reflects the state
*before* this item:

```python
for x in nums:
    for s in range(target, x - 1, -1):          # HIGH → LOW: each item is used at most once
        if dp[s - x]: dp[s] = True
```

Scan **low to high** and the item's own freshly-set `dp[s - x]` feeds `dp[s]` — the item is reused, silently turning 0/1
into unbounded. The demonstration: items `[2]`, target `4` — reverse scan says **False** (correct), forward scan says
**True** (wrong; it used the 2 twice). `[1,5,11,5]` → True, `[1,2,3,5]` → False (odd sum: return early).

A neat shortcut: represent the whole `dp` as **one big integer** and let a shift process every sum at once —
`bits |= bits << x` for each item, then test bit `target`. Same answers (`True`, `False`), and it often runs far faster in
CPython than the nested loop.

### 7.4 Sequence DP: LIS in O(n log n), Word Break, Decode Ways

**LIS** has two algorithms. The DP is O(n²); **patience sorting** keeps `tails[k]` = the smallest tail of any increasing
subsequence of length `k + 1`, and binary-searches where each number belongs:

```python
for x in nums:
    i = bisect_left(tails, x)                   # strict:  bisect_left;   non-decreasing:  bisect_right
    if i == len(tails): tails.append(x)
    else:               tails[i] = x
return len(tails)      # [10,9,2,5,3,7,101,18] -> 4    [0,1,0,3,2,3] -> 4    [7,7,7,7] -> 1 strict, 4 non-decreasing
```

`tails` is **not** the subsequence itself (it can hold values from different subsequences) — to return the actual
sequence, store the *index* at each length and a `prev` pointer per element, then walk back (`[2, 3, 7, 18]` is one answer).
`bisect_right` on a *strict* LIS is the classic bug: equal values then extend the tail.

**Word Break**: `dp[i]` = can `s[:i]` be segmented. Two habits: a **`set`** of words (a list makes each check O(words)), and
only try split points within the **longest word length** — `for j in range(max(0, i - maxlen), i)` — which turns a quadratic
scan into `O(n · maxlen)`. `"leetcode"` → True, `"catsandog"` → False.

**Decode Ways**: the last token is one digit (valid iff not `'0'`) or two digits (valid iff `10..26`). A lone `'0'` never
decodes, yet `"10"` and `"20"` do:

```python
if not s or s[0] == "0": return 0
prev2, prev1 = 1, 1                              # dp[i-2], dp[i-1]; dp[0] = 1 is the empty prefix
for i in range(2, len(s) + 1):
    cur = 0
    if s[i-1] != "0": cur += prev1                # last char alone
    if 10 <= int(s[i-2:i]) <= 26: cur += prev2     # last two chars together
    prev2, prev1 = prev1, cur
return prev1          # "12" -> 2   "226" -> 3   "06" -> 0   "10" -> 1   "2101" -> 1
```

### 7.5 Substring DP: expand around a centre, or fill a table

A palindrome has a centre — a character (odd length) or a gap (even length) — so there are `2n − 1` centres to expand from.
That is O(n²) time and **O(1) space**, against the `dp[i][j]` table's O(n²) space; Manacher's algorithm does it in O(n).
Forgetting the *even* centres misses `"bb"` in `"cbbd"`. For **counting** palindromic substrings, count every successful
expansion step, not just the longest per centre.

### 7.6 Two rolling states: Maximum Product Subarray

Kadane for a *sum* needs one running value. For a *product* a negative number turns the smallest running product into the
largest, so track **both**:

```python
best = hi = lo = nums[0]
for x in nums[1:]:
    cand = (x, hi * x, lo * x)                   # start fresh, or extend the max, or extend the min
    hi, lo = max(cand), min(cand)
    best = max(best, hi)
# [2,3,-2,4] -> 6     [-2,0,-1] -> 0     [-2,3,-4] -> 24
```

A zero simply resets both (the fresh-start candidate `x` covers it).

### 7.7 Getting the *answer*, not just its value

Store the choice that produced each `dp[i]`, then walk it back. Coin Change with a `choice[a]` array returns the coins:
`coins [1,2,5]`, amount 11 → `[1, 5, 5]` (3 coins). The same trick reconstructs the LIS, a decode, a word segmentation.

### 7.8 Top-down or bottom-up?

| | Top-down (memoised recursion) | Bottom-up (table) |
|---|---|---|
| Writing it | Mirrors the recurrence; easiest to get right first | Needs the iteration order worked out |
| States computed | Only the *reachable* ones | All of them |
| Depth | Recursion depth = chain length — CPython stops at ~1000 (`fib_memo(5000)` raises `RecursionError`) | No call stack |
| Space optimisation | Not possible | Rolling variables / arrays |
| Constant factor | Function-call overhead per state | A tight loop |

A sound interview path: state the recurrence and write it top-down, then convert to bottom-up if depth or speed matters.

### 7.9 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Return the solution, not the count." | Store the choice per state and walk it back (7.7). |
| "Count the ways, modulo 10⁹+7." | Reduce after every addition; in Go/C++ add `mod` before `%` after a subtraction. |
| "Reduce the space." | Rolling variables (fixed window), or one array scanned in the right direction (knapsack). |
| "Bounded coins (each at most k times)?" | Binary-split the counts into 0/1 items, or track a used-count per coin. |
| "Why is Coin Change not greedy?" | `[1, 3, 4]`, amount 6: greedy takes 4+1+1 (3 coins), the optimum is 3+3 (2). |
| "What if the array is huge?" | The rolling form is O(1) space; the table form is the limit. |
| "Is this really DP?" | State the overlapping subproblems and the optimal substructure — if neither holds it is greedy or backtracking. |

---
<!-- /block:16_py_1_families -->

<!-- problem-map:start -->
## Part 8 · Every Problem in This Topic, by Pattern

Seventeen problems, six families (linear recurrence · take-or-skip · unbounded knapsack · 0/1 knapsack · sequence DP · substring DP). Each **Trap** is a mistake documented in that problem's solution file.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · N-th Tribonacci Number](PyDSA/16_dp_1d/001_n_th_tribonacci_number_solution.py) <br>LC 1137 · Easy | Linear recurrence, window 3 | `dp[i] = dp[i-1] + dp[i-2] + dp[i-3]`, keeping only the last three values. **Trap:** treating `T2 = 1` as derived (it is a given base case); `range(3, n)` instead of `range(3, n + 1)`. |
| [002 · Climbing Stairs](PyDSA/16_dp_1d/002_climbing_stairs_solution.py) <br>LC 70 · Easy | Linear recurrence, window 2 | Ways to reach step `i` = ways to `i-1` + ways to `i-2` (the two path sets never overlap) — shifted Fibonacci. **Trap:** returning `fib(n)` instead of `fib(n + 1)` (`climbStairs(2)` must be 2). |
| [003 · Min Cost Climbing Stairs](PyDSA/16_dp_1d/003_min_cost_climbing_stairs_solution.py) <br>LC 746 · Easy | Minimum cost to *reach* a step | `dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2])` — pay for the step you *leave*. **Trap:** adding `cost[i]` (the step you land on) — a different problem. |
| [004 · Pascal's Triangle](PyDSA/16_dp_1d/004_pascals_triangle_solution.py) <br>LC 118 · Easy | Rows from the previous row | Each interior entry is the sum of the two above it in the *previous* row. **Trap:** off-by-one in the interior loop; appending the same list object to the triangle (aliased rows). |
| [005 · House Robber](PyDSA/16_dp_1d/005_house_robber_solution.py) <br>LC 198 · Medium | Take or skip | `dp[i] = max(dp[i-1], dp[i-2] + nums[i])`; `dp[i-1]` is already a max over both possibilities. **Trap:** separately tracking "did I rob `i-1`?" (unnecessary). |
| [006 · House Robber II](PyDSA/16_dp_1d/006_house_robber_ii_solution.py) <br>LC 213 · Medium | Circular = two linear runs | Either house 0 or house `n-1` is excluded: `max(rob(nums[1:]), rob(nums[:-1]))`. **Trap:** forgetting the single-house case (both slices empty); running the helper on the whole array. |
| [007 · Longest Palindromic Substring](PyDSA/16_dp_1d/007_longest_palindromic_substring_solution.py) <br>LC 5 · Medium | Expand around each centre | `2n − 1` centres (characters *and* gaps), O(n²) time, O(1) space; or the `dp[i][j]` table. **Trap:** only odd centres (misses `"bb"` in `"cbbd"`); an off-by-one recording the best window. |
| [008 · Palindromic Substrings](PyDSA/16_dp_1d/008_palindromic_substrings_solution.py) <br>LC 647 · Medium | Count every expansion | Same centres, but every successful expansion step is one more palindrome. **Trap:** counting only the longest per centre; forgetting even centres. |
| [009 · Decode Ways](PyDSA/16_dp_1d/009_decode_ways_solution.py) <br>LC 91 · Medium | Ways to decode a prefix | The last token is one digit (not `'0'`) or two (`10..26`). **Trap:** treating a lone `'0'` as decodable, or rejecting `"10"` / `"20"`; checking the pair range incorrectly. |
| [010 · Coin Change](PyDSA/16_dp_1d/010_coin_change_solution.py) <br>LC 322 · Medium | Unbounded knapsack, minimise | `dp[a] = 1 + min(dp[a - c])` with `INF` for unreachable and `dp[0] = 0`. **Trap:** using `-1` as the sentinel inside the `min`; assuming greedy works (`[1,3,4]`, 6). |
| [011 · Maximum Product Subarray](PyDSA/16_dp_1d/011_maximum_product_subarray_solution.py) <br>LC 152 · Medium | Two rolling states | Track the max *and* the min product ending here — a negative flips them. **Trap:** copy-pasting Kadane's single running max. |
| [012 · Word Break](PyDSA/16_dp_1d/012_word_break_solution.py) <br>LC 139 · Medium | Prefix segmentation | `dp[i]` = some `dp[j]` is true and `s[j:i]` is a word; use a `set`, and only try lengths up to the longest word. **Trap:** a list for the dictionary (O(words) per check); recursion without a memo. |
| [013 · Longest Increasing Subsequence](PyDSA/16_dp_1d/013_longest_increasing_subsequence_solution.py) <br>LC 300 · Medium | <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr> ending at `i`, or patience sorting | O(n²) over earlier `j`, or O(n log n) with `tails` and `bisect_left`. **Trap:** `bisect_right` on a strict <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr> (equal values extend the tail); reading `tails` as the subsequence. |
| [014 · Partition Equal Subset Sum](PyDSA/16_dp_1d/014_partition_equal_subset_sum_solution.py) <br>LC 416 · Medium | 0/1 knapsack in 1D | Odd total → false; else "is `total/2` reachable?" scanning sums **high to low**. **Trap:** scanning low to high — the same item is reused and 0/1 silently becomes unbounded. |
| [015 · Combination Sum IV](PyDSA/16_dp_1d/015_combination_sum_iv_solution.py) <br>LC 377 · Medium | Unbounded knapsack, count sequences | `dp[t] = Σ dp[t - x]` with the *target* in the outer loop (order matters). **Trap:** copying Coin Change II's coins-outside loop — it counts combinations and under-counts. |
| [016 · Perfect Squares](PyDSA/16_dp_1d/016_perfect_squares_solution.py) <br>LC 279 · Medium | Unbounded knapsack over squares | Coin Change with the coins replaced by `1, 4, 9, …, k² <= n`. **Trap:** a floating-point `int(k**0.5) ** 2 == i` test (off by one near perfect squares) instead of an integer `k * k <= i` loop. |
| [017 · Russian Doll Envelopes](PyDSA/16_dp_1d/017_russian_doll_envelopes_solution.py) <br>LC 354 · Hard | Reduce 2D nesting to <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr> | Sort by width ascending, height **descending**, then a *strict* <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr> of heights. **Trap:** ascending heights on equal widths (`[[3,4],[3,5]]` returns 2); `bisect_right` (equal heights nest). |

---
<!-- problem-map:end -->


## Checklist Before Leaving This Topic <!--ca-->

- [ ] Name the family (linear, take-or-skip, unbounded, 0/1, sequence, substring) from the wording of a problem <!--ca-->
- [ ] Choose the loop order for *counting* (coins outside = combinations, target outside = sequences) and say what each counts <!--ca-->
- [ ] Scan a 1D 0/1 knapsack high-to-low, and show the counter-example (`[2]`, target 4) for low-to-high <!--ca-->
- [ ] Write patience-sorting <abbr title="Longest Increasing Subsequence. The problem of finding a subsequence of a given sequence in which the elements are in sorted order.">LIS</abbr> with `bisect_left`, and reconstruct the actual subsequence <!--ca-->
- [ ] Track both the max and the min for a product recurrence, and say why <!--ca-->
