# Topic 16 · Dynamic Programming (1D) — Go Deep Dive

> Python interviewers let you slap `@lru_cache` on a function and call it a day.
> Go has no such decorator — every memo cache, every sentinel value, every
> overflow guard is something you write with your own hands. That's more typing,
> but it also means you can't hide from the state space: you must know exactly
> what you're caching and why. This document is about building that muscle.

---

## Part 1 · Top-Down Memoization — By Hand

### 1.1 There is no `functools.lru_cache` in Go

In Python you write:

```python
from functools import lru_cache

@lru_cache(None)
def fib(n):
    if n < 2: return n
    return fib(n-1) + fib(n-2)
```

In Go, the cache is not a decorator — it's a variable you declare, check, and
populate yourself, exactly like the hand-rolled recursion helpers in
[`09_recursion_backtracking`](../09_recursion_backtracking/_TOPIC_GUIDE.md):

```go
func fib(n int, memo map[int]int) int {
    if n < 2 {
        return n
    }
    if v, ok := memo[n]; ok {   // comma-ok — topic 1's idiom, again
        return v
    }
    result := fib(n-1, memo) + fib(n-2, memo)
    memo[n] = result
    return result
}
```

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

### 1.2 Map cache vs. slice cache

A `map[int]int` works for any key shape, but for DP the keys are almost always
**dense small integers** (0..n) — the exact situation where [topic 1's
frequency-array-vs-map tradeoff](../01_arrays_hashing/_TOPIC_GUIDE.md) recurs.
A slice cache skips hashing entirely:

```go
memo := make([]int, n+1)
for i := range memo {
    memo[i] = -1               // sentinel meaning "uncomputed"
}

func climb(n int, memo []int) int {
    if n <= 2 {
        return n
    }
    if memo[n] != -1 {
        return memo[n]
    }
    memo[n] = climb(n-1, memo) + climb(n-2, memo)
    return memo[n]
}
```

| Cache | Lookup | Init cost | Use when |
|---|:--:|---|---|
| `map[int]int` | O(1) avg, hashing overhead | O(1) (empty map) | Sparse or non-integer keys |
| `[]int` w/ sentinel | O(1), no hashing | O(n) to fill sentinel | Dense `0..n` integer keys — **the DP default** |

> ✅ **Default to a slice cache in 1D DP.** Your state is `dp[i]` where `i`
> ranges densely over `0..n` — a map buys you nothing but hashing overhead.
> Reach for a map only when the state is sparse or keyed by something that
> isn't a small integer (e.g. a bitmask that's mostly unused, or a string).

The sentinel choice matters: `-1` works when valid answers are non-negative
(counting problems, string lengths). For problems whose answer can itself be
negative or zero, use a separate `computed []bool` slice instead of overloading
a sentinel value — a memo bug from picking a sentinel that's also a valid
answer is a real, easy-to-make interview mistake.

---

## Part 2 · Bottom-Up Tabulation

### 2.1 Preallocate, then fill

```go
dp := make([]int, n+1)   // topic 1: preallocate when size is known
dp[0], dp[1] = 0, 1
for i := 2; i <= n; i++ {
    dp[i] = dp[i-1] + dp[i-2]
}
return dp[n]
```

> ⚠️ **Off-by-one on the base cases is the #1 bug in tabulated DP.** `dp[0]`
> and `dp[1]` (or whatever the problem's true base cases are) must be seeded
> *before* the loop starts, and the loop bound (`i <= n` vs `i < n`) must match
> whether `dp` is sized `n` or `n+1`. Write the base case out explicitly and
> check it against the smallest hand-traceable input (n=0, n=1) before trusting
> the loop.

### 2.2 Iteration order is the transition's dependency graph

`dp[i]` depending on `dp[i-1]` and `dp[i-2]` means the loop **must** run
left-to-right — this is obvious for Fibonacci-shaped problems but becomes the
crux of the design in knapsack-style problems (should the coin/item loop be
outer or inner? forward or backward?). Get the dependency direction wrong and
you silently reuse a value from the *current* pass instead of the *previous*
one — a bug that produces a plausible-looking wrong answer, not a crash.

---

## Part 3 · Space Optimization — Rolling Variables

Most 1D DP only ever looks back a constant number of steps. When that's true,
the `dp` slice itself is waste — O(n) space for information you only need a
few integers of.

```go
// Climbing stairs: O(n) time, O(1) space — no dp slice at all.
func climbStairs(n int) int {
    if n <= 2 {
        return n
    }
    prev, curr := 1, 2
    for i := 3; i <= n; i++ {
        prev, curr = curr, prev+curr   // tuple assignment: no temp variable
    }
    return curr
}
```

House Robber generalizes this to "last two states, and a choice at each step":

```go
func rob(nums []int) int {
    takePrev, skipPrev := 0, 0   // best-if-house-i-1 taken / skipped
    for _, n := range nums {
        take := skipPrev + n              // must skip the immediately previous house
        skip := max(takePrev, skipPrev)
        takePrev, skipPrev = take, skip
    }
    return max(takePrev, skipPrev)
}
```

> ⚡ **This is a real, not cosmetic, optimization in Go.** A `dp []int` of
> length n is a heap allocation; two `int` locals are stack-allocated and often
> live entirely in registers. For large n this is the difference between one
> allocation and zero.

---

## Part 4 · Integer Overflow and Go's `%` Operator

### 4.1 Overflow in counting DP

DP problems that *count* paths, subsets, or ways-to-tile grow combinatorially.
Summing many `dp[i-k]` terms — or worse, multiplying — can silently wrap `int`
exactly as [topic 1's Part 3](../01_arrays_hashing/_TOPIC_GUIDE.md) warned:

```go
dp[i] = dp[i-1] + dp[i-2] + dp[i-3]   // fine for small n, wraps for large n
```

Competitive-programming-style problems that expect huge outputs require modular
reduction at every step:

```go
const mod = 1_000_000_007
dp[i] = (dp[i-1] + dp[i-2]) % mod
```

### 4.2 Go's `%` keeps the dividend's sign — Python's doesn't

This is a genuine, silent-breakage divergence when porting modular-arithmetic
DP code from Python to Go:

```go
// Go:
-7 % 3   // -1

# Python:
-7 % 3   # 2
```

```go
// If a DP transition can produce a negative intermediate before modding
// (subtraction-based recurrences are common in "count of ways" DP with
// exclusion terms), the naive port is wrong in Go:
result := (dp[i-1] - dp[i-k] + mod) % mod   // ✅ add mod before reducing
result := (dp[i-1] - dp[i-k]) % mod          // ⚠️ can be negative in Go
```

> ⚠️ **Always add `mod` back before taking `%` after a subtraction.** A
> straight port of Python modular-DP code that relies on `%` normalizing to
> `[0, mod)` will produce negative array indices or negative "counts" in Go —
> and a negative index into a following `dp[result]` panics instead of failing
> loudly with a wrong-but-plausible number, which is at least easier to catch.

---

## Part 5 · The Methodology — State, Transition, Base Case, Order

Every 1D DP problem answers four questions, in this order:

1. **State** — what does `dp[i]` mean, in one sentence? ("the minimum coins to
   make amount `i`", "the length of the longest increasing subsequence ending
   at index `i`")
2. **Transition** — how is `dp[i]` built from smaller states?
3. **Base case** — what are the smallest `i` for which the answer is known
   directly, not by transition?
4. **Iteration order** — given the transition's dependencies, which direction
   must the loop run?

### 5.1 Coin Change — unbounded "knapsack shape"

State: `dp[a]` = fewest coins to make amount `a`. Transition: try every coin,
take the best. Base case: `dp[0] = 0`. Order: amounts ascending (each amount
depends only on smaller amounts).

### 5.2 Longest Increasing Subsequence — two complexity classes

The natural DP is **O(n²)**: `dp[i]` = LIS ending at `i`, built by scanning all
`j < i` with `nums[j] < nums[i]`. There is a genuinely different **O(n log n)**
algorithm (patience sorting): maintain a slice `tails` where `tails[k]` is the
smallest possible tail of an increasing subsequence of length `k+1`, and use
[topic 5's `sort.Search`](../05_binary_search/_TOPIC_GUIDE.md) to find where
each new element belongs:

```go
idx := sort.Search(len(tails), func(i int) bool { return tails[i] >= num })
```

This is the same monotonic-predicate binary search from the binary search
topic, applied to a structure that *isn't* the original input — a good example
of binary search showing up somewhere non-obvious.

---

## Part 6 · Complexity Table

| Problem | Naive | DP | Space-optimized |
|---|:--:|:--:|:--:|
| Fibonacci / Climbing Stairs | O(2ⁿ) | O(n) time, O(n) space | O(n) time, **O(1)** space |
| House Robber | O(2ⁿ) | O(n) time, O(n) space | O(n) time, **O(1)** space |
| Coin Change | O(coins^amount) | O(amount·coins) time, O(amount) space | — (already minimal) |
| Longest Increasing Subsequence | O(2ⁿ) | O(n²) time, O(n) space | **O(n log n)** time, O(n) space |
| Decode Ways | O(2ⁿ) | O(n) time, O(n) space | O(n) time, **O(1)** space |

---

## Part 7 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Memoization | `@lru_cache` decorator | Hand-rolled `map`/`[]int` + sentinel |
| Default cache shape | Dict (hashed) | Prefer `[]int` for dense integer keys |
| `%` on negatives | Always non-negative (for positive divisor) | **Keeps the dividend's sign** |
| Integer overflow | Never (arbitrary precision) | **Wraps** — mod arithmetic must be explicit |
| "Return two values" from a step | Tuple unpack | Named returns or explicit multi-assign |
| `max`/`min` of two ints | Builtin | Builtin generic `max`/`min` (Go 1.21+) |

---

## Part 8 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Memoized recursion | O(n) | O(n) | LC 509 Fibonacci |
| Bottom-up tabulation | O(n) | O(n) | LC 70 Climbing Stairs |
| Rolling-variable DP | O(n) | **O(1)** | LC 198 House Robber |
| Unbounded knapsack (coin change) | O(amount·coins) | O(amount) | LC 322 Coin Change |
| O(n²) LIS | O(n²) | O(n) | LC 300 (baseline) |
| Patience sorting + binary search | O(n log n) | O(n) | LC 300 (optimized) |
| Interval/segment DP over a string | O(n²) | O(n) | LC 91 Decode Ways |

---

## Part 9 · Building Coin Change and LIS From Scratch

```go
package main

import (
	"math"
	"sort"
)

// Coin Change (LC 322): fewest coins to make amount, or -1 if impossible.
func coinChange(coins []int, amount int) int {
	dp := make([]int, amount+1)
	for i := 1; i <= amount; i++ {
		dp[i] = math.MaxInt32   // sentinel: "not yet reachable"
	}
	dp[0] = 0                  // base case: zero amount needs zero coins

	for a := 1; a <= amount; a++ {
		for _, c := range coins {
			if c > a || dp[a-c] == math.MaxInt32 {
				continue        // this coin can't contribute to amount a
			}
			// dp[a-c]+1 cannot overflow: dp[a-c] is bounded by amount,
			// but guard the sentinel check above regardless — adding 1
			// to MaxInt32 would wrap and silently look "reachable".
			if dp[a-c]+1 < dp[a] {
				dp[a] = dp[a-c] + 1
			}
		}
	}

	if dp[amount] == math.MaxInt32 {
		return -1
	}
	return dp[amount]
}

// Longest Increasing Subsequence (LC 300): O(n log n) patience sorting.
func lengthOfLIS(nums []int) int {
	tails := make([]int, 0, len(nums))   // preallocate: topic 1's advice

	for _, num := range nums {
		// Find the first tail >= num (topic 5's sort.Search monotonic predicate).
		idx := sort.Search(len(tails), func(i int) bool { return tails[i] >= num })
		if idx == len(tails) {
			tails = append(tails, num)   // num extends the longest subsequence so far
		} else {
			tails[idx] = num             // num gives an earlier subsequence a smaller tail
		}
	}

	return len(tails)   // NOT the actual subsequence — just its length
}
```

**Talk track while writing:** in Coin Change, the sentinel guard
(`dp[a-c] == math.MaxInt32`) must come *before* the `+1`, or the addition
wraps into negative territory and looks like a valid (better!) answer — the
same overflow discipline from Part 4. In LIS, `tails` is not the subsequence
itself — overwriting `tails[idx]` discards information about *which* elements
were chosen, which is fine because the problem only asks for the length; if it
asked for the actual subsequence, reconstruction needs a separate parent-index
array.

---

<!-- block:16_go_1_families -->
## Part 10 · The Six 1D DP Families in Go — and the Line That Separates Look-Alikes

Parts 1–5 give the Go mechanics (slice memos, rolling variables, overflow, `%`). This Part is the catalogue of shapes with
Go code. All snippets ran on Go 1.24.5 against LeetCode's own examples.

```arch
%% caption: The six 1D shapes. The wording of the question picks the family; the family fixes the loop order and the direction.
grid 200x80
node q "1D DP problem" at 0,1 shape=pill
node a "What varies?" at 0,2 shape=diamond color=amber
node l "Linear recurrence" at 1,0 color=green w=400 sub="position i, FIXED look-back window · Fibonacci, Stairs, Tribonacci"
node t "Take-or-skip" at 1,1 color=green w=400 sub="position i, take or skip · House Robber I and II"
node u "Unbounded knapsack: ascending" at 1,2 color=amber w=400 sub="a target VALUE, items reusable · Coin Change, Perfect Squares, Comb. Sum IV"
node z "0/1 knapsack: sums scanned DOWN" at 1,3 color=amber w=400 sub="a target VALUE, each item once · Partition Equal Subset Sum"
node s "Sequence DP" at 1,4 color=green w=400 sub="best answer ENDING at i · LIS, Word Break, Decode Ways, Max Product"
node p "Substring DP" at 1,5 color=green w=400 sub="a centre or an interval · palindromes: expand or table"
q -> a
a:R -> l:L
a:R -> t:L
a:R -> u:L
a:R -> z:L
a:R -> s:L
a:R -> p:L
```

### Take or skip — House Robber I and II

```go
take, skip := 0, 0
for _, x := range nums {
    take, skip = skip+x, max(take, skip)        // tuple assignment: BOTH right-hand sides use the OLD values
}
return max(take, skip)                          // [1 2 3 1] -> 4     [2 7 9 3 1] -> 12
```

The circular version is **two linear runs** — `max(rob(nums[1:]), rob(nums[:len(nums)-1]))` — and in Go those sub-slices
are O(1) headers (Python's copy). Handle `len(nums) == 1` first. `[2 3 2]` → 3, `[1 2 3 1]` → 4.

### Unbounded knapsack — and the loop-order fork

Coin Change (minimise) works either way round. Use a headroom sentinel — `unreachable := math.MaxInt / 2` — because
`dp[i-c] + 1` on a raw `math.MaxInt` **wraps negative** (measured: `math.MaxInt + 1 < 0` is `true`) and wins the `min`:

```go
dp[i] = unreachable
for _, c := range coins { if c <= i && dp[i-c]+1 < dp[i] { dp[i] = dp[i-c] + 1 } }
// [1 2 5],11 -> 3     [2],3 -> -1     amount 0 -> 0     [1 3 4],6 -> 2 (greedy would say 3: 4+1+1)
```

When you **count**, the loop order decides *what* is counted:

```go
for _, c := range coins { for a := c; a <= amount; a++ { dp[a] += dp[a-c] } }        // coins OUTER: combinations
for t := 1; t <= target; t++ { for _, x := range nums { if x <= t { dp[t] += dp[t-x] } } }   // target OUTER: sequences
// coins [1 2 5], amount 5: 4 combinations vs 9 sequences      [1 2 3], target 4: 7 sequences (Combination Sum IV)
```

Copying Coin Change II's structure into Combination Sum IV — whose name says "combination" but which counts **ordered**
sequences — silently under-counts.

### 0/1 knapsack in one dimension — the scan direction is the missing axis

Each item used **once** means scanning sums **downward**, so `dp[s-x]` still reflects the state *before* this item:

```go
for _, x := range nums {
    for s := target; s >= x; s-- { if dp[s-x] { dp[s] = true } }     // DOWN: 0/1.   UP would be unbounded.
}
```

Items `[2]`, target `4`: downward → `false` (correct), upward → `true` (wrong — the 2 was used twice). An odd total is an
immediate `false`. The whole `dp` can also be **one big integer** with `bits.Or(bits, new(big.Int).Lsh(bits, uint(x)))` per
item and `bits.Bit(target) == 1` at the end (`math/big`) — one shift processes every sum at once.

### Sequence DP: LIS, Word Break, Decode Ways

**LIS in O(n log n)** — `tails[k]` is the smallest tail of any increasing subsequence of length `k + 1`. `slices.BinarySearch`
returns the leftmost index with `tails[i] >= x`, which is exactly what a **strict** LIS needs:

```go
i, _ := slices.BinarySearch(tails, x)               // strict LIS: leftmost >= x
if i == len(tails) { tails = append(tails, x) } else { tails[i] = x }
// non-decreasing needs the FIRST tails[i] > x:  i := sort.Search(len(tails), func(i int) bool { return tails[i] > x })
```

`[10 9 2 5 3 7 101 18]` → 4; `[7 7 7 7]` → 1 strict, 4 non-decreasing. `tails` is not the subsequence — store an index per length and
a `prev` array to reconstruct it. Using the non-strict search on a strict LIS lets equal values extend the tail.

**Word Break** — a `map[string]struct{}` of words and a loop bounded by the longest word:

```go
for j := max(0, i-maxLen); j < i; j++ {
    if _, ok := set[s[j:i]]; ok && dp[j] { dp[i] = true; break }        // s[j:i] is a free substring header
}
```

`s[j:i]` costs nothing in Go (Python copies), so the map lookup is the only cost — but it *does* hash the substring, so keep
`maxLen` small. **Decode Ways:** the last token is one digit (valid iff not `'0'`) or two digits (valid iff `10..26`); a lone
`'0'` never decodes but `"10"` and `"20"` do. `"12"` → 2, `"226"` → 3, `"06"` → 0, `"10"` → 1, `"2101"` → 1:

```go
if s[i-1] != '0' { cur += prev1 }                                     // last char alone
if two := int(s[i-2]-'0')*10 + int(s[i-1]-'0'); two >= 10 && two <= 26 { cur += prev2 }
```

### Substring DP and Maximum Product

Palindromes have `2n − 1` centres (characters and gaps): expand outward — O(n²) time, **O(1) space** — and remember the *even*
centres (`"cbbd"` → `"bb"`). Counting palindromic substrings counts every successful expansion, not the longest per centre.

**Maximum Product Subarray** tracks the running max *and* min, because a negative flips them; `min`/`max` take three arguments
in Go 1.21+:

```go
best, hi, lo := nums[0], nums[0], nums[0]
for _, x := range nums[1:] {
    a, b := hi*x, lo*x
    hi, lo = max(x, a, b), min(x, a, b)                 // start fresh, extend the max, or extend the min
    best = max(best, hi)
}                                                       // [2 3 -2 4] -> 6    [-2 0 -1] -> 0    [-2 3 -4] -> 24
```

### Reconstructing the answer

Store the choice that produced each `dp[a]` and walk it back: coins `[1 2 5]`, amount 11 gives `[1 5 5]`. The same trick
reconstructs an LIS, a decoding, a segmentation.

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `dp := make([]int, n)` sized one short | `dp[n]` panics (Python: an `IndexError` too, but `dp[-1]` wraps silently). | Size `n+1` when indices run `0..n`. |
| Raw `math.MaxInt` as "unreachable", then `+ 1` | Wraps negative and wins every `min`. | `math.MaxInt / 2`, or guard before adding. |
| `-7 % 3` in a modular DP | `-1` in Go, `2` in Python. | `(x % mod + mod) % mod`. |
| Coins-outer loop for *ordered* counts | Counts combinations — under-counts. | Target outer, items inner. |
| Scanning sums upward in a 0/1 knapsack | Reuses an item. | `for s := target; s >= x; s--`. |
| Memo sentinel `0` when `0` is a valid answer | Recomputes forever, or wrong. | `-1`, or a parallel `computed []bool`. |
| `nums[1:]` "to copy" | It is a *view* — writes alias the original. | `slices.Clone` when you mutate. |
| Recursive memo on a 10⁶-deep chain | Fatal `stack overflow` (1 GB), unrecoverable. | Tabulate bottom-up. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Return the solution." | Store the choice per state; walk it back. |
| "Count modulo 10⁹+7." | Reduce after every addition; add `mod` before `%` after a subtraction. |
| "Reduce the space." | Rolling variables (fixed window) or one array scanned in the right direction. |
| "Bounded coins?" | Binary-split the counts into 0/1 items. |
| "Why is Coin Change not greedy?" | `[1 3 4]`, amount 6: greedy = 4+1+1 (3 coins), optimum = 3+3 (2). |
| "Top-down or bottom-up?" | Top-down: mirrors the recurrence, only reachable states; bottom-up: no stack, rolling arrays, tighter loop. |

---
<!-- /block:16_go_1_families -->

<!-- problem-map:start -->
## Part 11 · Every Problem in This Topic, by Pattern

Seventeen problems, six families (linear recurrence · take-or-skip · unbounded knapsack · 0/1 knapsack · sequence DP · substring DP) — the Python guide's map in Go, with the Go-only traps. Topic 16's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · N-th Tribonacci Number](GoDSA/16_dp_1d/001_n_th_tribonacci_number/solution.go) <br>LC 1137 · Easy | Linear recurrence, window 3 | `a, b, c = b, c, a+b+c` rolling variables. **Trap:** treating `T2 = 1` as derived; `i < n` instead of `i <= n`; overflow on large `n` (say so). |
| [002 · Climbing Stairs](GoDSA/16_dp_1d/002_climbing_stairs/solution.go) <br>LC 70 · Easy | Linear recurrence, window 2 | `prev, curr = curr, prev+curr` — shifted Fibonacci. **Trap:** returning `fib(n)` instead of `fib(n+1)`. |
| [003 · Min Cost Climbing Stairs](GoDSA/16_dp_1d/003_min_cost_climbing_stairs/solution.go) <br>LC 746 · Easy | Minimum cost to *reach* a step | `dp[i] = min(dp[i-1]+cost[i-1], dp[i-2]+cost[i-2])`. **Trap:** adding `cost[i]` (the step you land on). |
| [004 · Pascal's Triangle](GoDSA/16_dp_1d/004_pascals_triangle/solution.go) <br>LC 118 · Easy | Rows from the previous row | Build each row from the last; `make([]int, i+1)` per row. **Trap:** off-by-one in the interior loop; reusing one row slice for every row (all rows alias). |
| [005 · House Robber](GoDSA/16_dp_1d/005_house_robber/solution.go) <br>LC 198 · Medium | Take or skip | `take, skip = skip+x, max(take, skip)`. **Trap:** reading the *new* value on the right (use the tuple assignment). |
| [006 · House Robber II](GoDSA/16_dp_1d/006_house_robber_ii/solution.go) <br>LC 213 · Medium | Circular = two linear runs | `max(rob(nums[1:]), rob(nums[:len(nums)-1]))` — free sub-slices. **Trap:** the single-house case; running on the whole slice. |
| [007 · Longest Palindromic Substring](GoDSA/16_dp_1d/007_longest_palindromic_substring/solution.go) <br>LC 5 · Medium | Expand around each centre | `2n − 1` centres, `[2][2]int{{c, c}, {c, c+1}}`; `s[bl:br]` is a free substring. **Trap:** only odd centres; the window off-by-one. |
| [008 · Palindromic Substrings](GoDSA/16_dp_1d/008_palindromic_substrings/solution.go) <br>LC 647 · Medium | Count every expansion | Every successful expansion is one palindrome. **Trap:** longest-per-centre only; even centres. |
| [009 · Decode Ways](GoDSA/16_dp_1d/009_decode_ways/solution.go) <br>LC 91 · Medium | Ways to decode a prefix | Two rolling values; one digit iff not `'0'`, two digits iff `10..26`. **Trap:** a lone `'0'` decodable; rejecting `"10"`/`"20"`. |
| [010 · Coin Change](GoDSA/16_dp_1d/010_coin_change/solution.go) <br>LC 322 · Medium | Unbounded knapsack, minimise | `unreachable := math.MaxInt / 2`; `dp[0] = 0`. **Trap:** raw `math.MaxInt + 1` overflow; assuming greedy works. |
| [011 · Maximum Product Subarray](GoDSA/16_dp_1d/011_maximum_product_subarray/solution.go) <br>LC 152 · Medium | Two rolling states | `hi, lo = max(x, a, b), min(x, a, b)` (three-argument builtins). **Trap:** a single running max. |
| [012 · Word Break](GoDSA/16_dp_1d/012_word_break/solution.go) <br>LC 139 · Medium | Prefix segmentation | `map[string]struct{}` set, loop bounded by the longest word; free substring headers. **Trap:** a `[]string` scan per check. |
| [013 · Longest Increasing Subsequence](GoDSA/16_dp_1d/013_longest_increasing_subsequence/solution.go) <br>LC 300 · Medium | LIS ending at `i` / patience sorting | `slices.BinarySearch(tails, x)` (strict) or `sort.Search` with `>` (non-decreasing). **Trap:** the wrong bound (equal values extend the tail); reading `tails` as the sequence. |
| [014 · Partition Equal Subset Sum](GoDSA/16_dp_1d/014_partition_equal_subset_sum/solution.go) <br>LC 416 · Medium | 0/1 knapsack in 1D | `for s := target; s >= x; s--`; odd total → false. **Trap:** scanning upward (item reused). |
| [015 · Combination Sum IV](GoDSA/16_dp_1d/015_combination_sum_iv/solution.go) <br>LC 377 · Medium | Unbounded knapsack, count sequences | Target outer, items inner. **Trap:** the coins-outer loop (counts combinations). |
| [016 · Perfect Squares](GoDSA/16_dp_1d/016_perfect_squares/solution.go) <br>LC 279 · Medium | Unbounded knapsack over squares | `for j := 1; j*j <= i; j++` — integer loop, no `math.Sqrt`. **Trap:** a float square-root test. |
| [017 · Russian Doll Envelopes](GoDSA/16_dp_1d/017_russian_doll_envelopes/solution.go) <br>LC 354 · Hard | Reduce 2D nesting to LIS | `slices.SortFunc`: width ascending, height **descending**; strict LIS of heights. **Trap:** ascending heights on equal widths; the non-strict search. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] State the DP recurrence in one sentence before writing any code
- [ ] Explain why Go has no `lru_cache` and what you write instead
- [ ] Justify slice-cache vs map-cache for a given problem's key shape
- [ ] Show the space-optimized rolling-variable version of a Fibonacci-shaped DP
- [ ] Explain why iteration order matters and how it follows the transition
- [ ] Know Go's `%` keeps the dividend's sign, and add `mod` before reducing a subtraction
- [ ] Explain why the LIS `tails` array is not the actual subsequence
- [ ] Write Coin Change bottom-up in under 10 minutes, sentinel-safe
- [ ] Use `unreachable := math.MaxInt / 2` so `dp[i-c] + 1` cannot overflow <!--ca-->
- [ ] Pick the loop order for counting (coins outside = combinations, target outside = sequences) <!--ca-->
- [ ] Scan a 0/1 knapsack downward, and give the `[2]`, target 4 counter-example <!--ca-->
- [ ] Use `slices.BinarySearch` for strict LIS and `sort.Search` with `>` for non-decreasing <!--ca-->
- [ ] Say why `nums[1:]` is free in Go (a view) and what that means for mutation <!--ca-->
