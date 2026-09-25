# Complexity Analysis — Big-O, Recursion, Amortization, and Reading Constraints

This is the vocabulary every other file in this module uses to talk about
"fast" and "slow" — start here if you're new to CS fundamentals in general, even
before the other nine files. This file starts with what Big-O actually measures and
why it matters, then goes as deep as Google interviewers expect: they expect you to
state time AND space complexity **before being asked**, including recursion stack
space and hidden costs like slicing. This file covers the reasoning, not just the
table: how to derive the bound, how to handle recursion (recursion trees and the
master theorem), amortized analysis, and how to use the input constraints to predict
the intended algorithm.

## Foundations — Start Here If You're New to Complexity Analysis

**The question Big-O answers.** If your input has `n` items, how does the amount of
*work* grow as `n` grows? Not "how many seconds does it take" (that depends on the
machine) — but "if I double the input, does the work double, quadruple, or barely
change?" Big-O answers that question by naming a *shape of growth*, ignoring
machine-specific constants.

**Two worked examples, side by side.**

```python
# Example A — O(n): work grows in a straight line with n
def contains(nums, target):
    for x in nums:            # runs at most n times
        if x == target:
            return True
    return False
# Double the list -> roughly double the worst-case work. That's O(n): "linear."

# Example B — O(n^2): work grows with the SQUARE of n
def has_duplicate_pair(nums):
    for i in range(len(nums)):        # n times
        for j in range(len(nums)):    # n times, for EACH i
            if i != j and nums[i] == nums[j]:
                return True
    return False
# Double the list -> roughly QUADRUPLE the worst-case work (2n x 2n = 4 x n x n).
# That's O(n^2): "quadratic" — the nested loop is why.
```

**Why `O(1)` and `O(log n)` barely grow at all.** `O(1)` ("constant") means the work
doesn't depend on `n` — looking up one hash-map key, say. `O(log n)` ("logarithmic")
means the work grows *very* slowly: binary search on a billion items takes about 30
steps, not a billion — every step throws away half of what's left. Going from
"fastest to describe" to "slowest": `O(1) < O(log n) < O(n) < O(n log n) < O(n²) <
O(2ⁿ) < O(n!)`. That ordering is the single most useful fact in this file — it's
what lets you say "an `O(n log n)` sort beats an `O(n²)` approach on a large input"
without measuring anything.

**Why "drop the constants" is allowed, and why it's still worth caring about
constants in practice.** `O(2n)` and `O(n)` are both called `O(n)` — Big-O describes
the *shape* of growth, not the exact operation count, because for large enough `n`
the shape is what dominates. But real interview answers still say things like "this
is O(n) but with a lot of work per element" when it matters — the rest of this file
(§1's rules of thumb) makes that precise instead of hand-wavy.

**Time vs. space.** Everything above measures *time* (how much work). The exact same
notation measures *space* (how much extra memory an algorithm uses beyond its
input) — a hash-map-based solution might be `O(n)` time and `O(n)` space, while a
two-pointer solution on the same problem might be `O(n)` time and `O(1)` space. §7
covers space complexity precisely, including a detail beginners usually miss:
recursion itself uses space (each pending call takes memory until it returns).

With that foundation — what Big-O measures, why the ordering above holds, and that
time and space are measured the same way — the rest of this file is the precise,
interview-depth version: deriving bounds from code, handling recursion, amortized
analysis, and reading a problem's constraints to predict the intended algorithm.

## 1. What Big-O Actually Says

| Notation | Meaning | Informal |
|---|---|---|
| O(f) | Upper bound: grows no faster than f (up to a constant) | "at most" |
| Ω(f) | Lower bound | "at least" |
| Θ(f) | Tight bound: both | "exactly, up to constants" |

In interviews "O" usually means the tight worst-case bound. Say which case you mean when it differs:
- **Worst case** — quicksort O(n²), hash lookup O(n).
- **Average / expected case** — quicksort O(n log n) with random pivots, hash lookup O(1).
- **Amortized** — dynamic array append O(1) averaged over a sequence (a single append may be O(n)).

Rules of thumb:
- Drop constants and lower-order terms: O(3n² + 10n) = O(n²). But **constants matter in practice**: this repo's benchmarks repeatedly show a C-implemented O(n log n) sort beating a pure-Python O(n) algorithm at realistic sizes.
- **Multiple inputs keep separate variables:** comparing two strings of lengths m and n is O(m + n), a grid is O(m·n) — don't collapse to O(n²).
- **Sequential steps add; nested steps multiply.**

## 2. Deriving Loop Complexity

```python
for i in range(n):              # O(n)
    for j in range(i, n):       # runs n - i times
        ...                     # total: n + (n-1) + ... + 1 = n(n+1)/2 = O(n²)

i = 1
while i < n:                    # i doubles: runs log2(n) times → O(log n)
    i *= 2

for i in range(n):              # outer n
    j = 1
    while j < n:                # inner log n
        j *= 2                  # total O(n log n)
```

**Two pointers / sliding window — the "each pointer moves at most n times" argument.** A `while` loop inside a `for` loop is not automatically O(n²):

```python
l = 0
for r in range(n):              # r moves n times total
    while window_invalid():     # l only moves forward, at most n times TOTAL
        l += 1
```

Total work is O(n + n) = O(n) because the inner loop's work is bounded across the whole run, not per outer iteration. Same argument for monotonic stacks: **each element is pushed once and popped at most once.**

## 3. Hidden Costs That Change the Answer

| Innocent-looking code | Real cost | Why |
|---|---|---|
| `s[1:]`, `nums[i:j]` | O(length) time and space | Python slices copy |
| `s += ch` in a loop | O(n²) total (in general) | Strings are immutable |
| `x in list` | O(n) | Linear scan; use a set |
| `list.pop(0)`, `list.insert(0, x)` | O(n) | Shifts every element; use `deque` |
| `sorted(x)` inside a loop | O(n log n) per iteration | Sort once outside |
| `min(lst)` / `max(lst)` / `sum(lst)` in a loop | O(n) per call | Maintain a running value |
| `str(n)` / `int(s)` on huge numbers | Not O(1) | Big-integer conversion is superlinear |
| Hash of a string / tuple key | O(length of key) | Tuple keys of size k cost O(k) to hash |
| Recursion depth d | O(d) **space** | Each frame holds locals |
| `copy.deepcopy`, `list(set)` | O(size) | Copies everything |
| Building a result of size k | Ω(k) | Output-sensitive: can't beat the output size |

## 4. Recursion: Draw the Recursion Tree

**Time = (number of calls) × (work per call, excluding recursive calls).** Draw the tree: branching factor b, depth d, work per node w.

```arch
%% caption: A naive Fibonacci recursion tree branches exponentially; time complexity is the total number of nodes, while space is just the maximum depth (the call stack).
route straight
grid 90x60
node f5 "f(5)" at 3,0 shape=circle color=blue
node f4 "f(4)" at 1.5,1 shape=circle color=blue
node f3a "f(3)" at 4.5,1 shape=circle color=blue
node f3b "f(3)" at 0.5,2 shape=circle color=blue
node f2a "f(2)" at 2.5,2 shape=circle color=blue

f5 -- f4
f5 -- f3a
f4 -- f3b
f4 -- f2a
```

```text
fib(n) naive:            fib(5)
                       /        \
                  fib(4)        fib(3)
                 /     \        /     \
             fib(3)  fib(2)  fib(2)  fib(1)     branching ≈ 2, depth n
             ...                                calls ≈ φ^n ≈ O(1.618^n)
                                                (O(2^n) is a valid, looser upper bound)
```

| Pattern | Calls | Work per call | Time | Space (stack) |
|---|---|---|---|---|
| Linear recursion f(n-1) | n | O(1) | O(n) | O(n) |
| Binary tree traversal | n nodes | O(1) | O(n) | O(h): O(log n) balanced, O(n) skewed |
| Naive Fibonacci | ~φ^n | O(1) | O(φ^n) | O(n) |
| Memoized <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> with S states | S | O(transitions) | O(S × transitions) | O(S) cache + O(depth) stack |
| Subsets (include/exclude) | 2^n leaves | O(n) to copy each subset | O(n · 2^n) | O(n) |
| Permutations | n! leaves | O(n) copy | O(n · n!) | O(n) |
| N-Queens / sudoku backtracking | exponential, pruned | — | state the unpruned bound, mention pruning | O(n) |
| Binary search f(n/2) | log n | O(1) | O(log n) | O(log n) recursive, O(1) iterative |
| Merge sort 2·f(n/2) + O(n) | — | — | O(n log n) | O(n) auxiliary + O(log n) stack |

**Memoization rule:** time = number of distinct states × work per state. For `dp(i, j)` over a string of length n with O(1) transitions: O(n²) states × O(1) = O(n²). With an inner loop over k (like Burst Balloons): O(n³).

**Python recursion depth:** CPython's default limit is 1000 frames. Recursion depth equal to n on inputs of 10^4–10^5 raises `RecursionError`; say so and offer the iterative version (examples measured live in `PyDSA/14_graphs`, `PyDSA/17_dp_2d/015`).

## 5. The Master Theorem

For divide-and-conquer recurrences **T(n) = a·T(n/b) + O(n^d)** (a ≥ 1 subproblems, each of size n/b, plus O(n^d) work to split and combine), compare d with log_b(a):

| Case | Condition | Result | Intuition |
|---|---|---|---|
| 1 | d < log_b a | T(n) = O(n^(log_b a)) | Leaves dominate |
| 2 | d = log_b a | T(n) = O(n^d log n) | Every level does equal work |
| 3 | d > log_b a | T(n) = O(n^d) | Root dominates |

| Algorithm | Recurrence | a, b, d | log_b a | Result |
|---|---|---|---|---|
| Binary search | T(n/2) + O(1) | 1, 2, 0 | 0 | Case 2: O(log n) |
| Merge sort | 2T(n/2) + O(n) | 2, 2, 1 | 1 | Case 2: O(n log n) |
| Tree traversal (balanced) | 2T(n/2) + O(1) | 2, 2, 0 | 1 | Case 1: O(n) |
| Karatsuba multiplication | 3T(n/2) + O(n) | 3, 2, 1 | ≈1.585 | Case 1: O(n^1.585) |
| Strassen | 7T(n/2) + O(n²) | 7, 2, 2 | ≈2.807 | Case 1: O(n^2.807) |
| Quickselect (good pivot) | T(n/2) + O(n) | 1, 2, 1 | 0 | Case 3: O(n) |
| Closest pair of points | 2T(n/2) + O(n) | 2, 2, 1 | 1 | Case 2: O(n log n) |

The master theorem doesn't cover uneven splits (quicksort's worst case T(n-1) + O(n) = O(n²)) or subtract-style recurrences; draw the recursion tree for those.

## 6. Amortized Analysis

Amortized cost = total cost of a sequence of operations ÷ number of operations, **guaranteed for every sequence** (unlike average case, which depends on the input distribution).

| Structure | Expensive operation | Amortized argument | Amortized cost |
|---|---|---|---|
| Dynamic array append | Resize copies n elements | Capacity doubles: copies total 1 + 2 + 4 + … + n < 2n over n appends | O(1) |
| Monotonic stack / deque | A single push may pop many | Each element pushed once, popped at most once: ≤ 2n operations total | O(1) |
| Sliding window | Inner while moves `l` many times | `l` moves at most n times total | O(1) per step |
| Union-Find with path compression + union by rank | A single find may walk a long path | Proven O(α(n)) per operation; α (inverse Ackermann) ≤ 4 for any practical n | O(α(n)) ≈ O(1) |
| Hash map with resizing | Rehash all entries | Same geometric-growth argument | O(1) expected |
| Two-stack queue | Moving the in-stack to the out-stack | Each element moved at most once | O(1) |
| Lazy-deletion heap | One pop discards many stale entries | Each pushed entry popped at most once | O(log n) |

The **accounting method** in one sentence: charge each cheap operation a little extra (e.g., 3 units for an append) and bank the surplus to pay for the occasional expensive one (the resize).

## 7. Space Complexity: Say All Three Parts

1. **Auxiliary data structures** (hash maps, DP tables, visited sets).
2. **Recursion stack** (depth × frame size).
3. **Output** — usually stated separately ("O(1) extra space not counting the output").

Also say whether the algorithm **mutates the input**. In-place algorithms that sort or overwrite the input have a cost the caller may not accept; this repo's solution tables include a "Mutates input?" column for that reason.

## 8. Reading the Constraints: Predict the Algorithm

A rough budget: **~10^8 simple operations per second in C++/Java/Go, ~10^7 in Python.** Interview judges usually allow 1–2 seconds.

| n up to | Affordable complexity | Typical techniques |
|---|---|---|
| ≤ 10–12 | O(n!), O(n · n!) | Permutations, brute-force backtracking |
| ≤ 20–25 | O(2^n), O(n · 2^n) | Subsets, bitmask DP, meet in the middle (≤ 40) |
| ≤ 100–500 | O(n³) | Floyd-Warshall, interval DP, triple loops |
| ≤ 2,000–5,000 | O(n²) | 2D DP, all pairs, O(n²) with small constants |
| ≤ 10^5–10^6 | O(n log n), O(n) | Sorting, heaps, binary search, two pointers, hashing, segment trees |
| ≤ 10^7–10^8 | O(n), small constant | Single pass, counting, sieve |
| ≥ 10^9 | O(log n), O(√n), O(1) | Binary search on the answer, math, digit DP, matrix exponentiation |

Other constraint tells:
- **Values up to 10^9 but n small** → coordinate compression or sorting, not arrays indexed by value.
- **Values small (≤ 10^4)** → counting arrays, bucket sort, DP over values.
- **"Return modulo 10^9 + 7"** → counting problem, usually DP or combinatorics; the true answer overflows.
- **Queries up to 10^5 on a static array** → precompute (prefix sums, sparse table); with updates → Fenwick/segment tree.
- **k ≤ 20 special items in a large graph** → bitmask over the k items.
- **Grid ≤ 100×100** → BFS/DP over cells is fine; with an extra state dimension ≤ ~50 still fine.
- **"Follow up: O(1) space"** → two pointers, in-place marking, bit tricks, Morris traversal.

Mastery drill: take 10 random problems, read only the constraints, predict the technique, then check.

## 9. How to Say It in the Interview

> "Sorting is O(n log n). The two-pointer scan is O(n) because each pointer only moves inward, so overall O(n log n) time. Space is O(1) extra, but Python's `sorted` allocates O(n) and I'm not mutating your input. If the input were already sorted it would be O(n)."

Checklist:
- [ ] Time AND space, before coding.
- [ ] Recursion stack counted.
- [ ] Hidden costs (slicing, string building, `in list`) checked.
- [ ] Worst vs average vs amortized stated when they differ.
- [ ] Each input size named separately (m, n, k).
- [ ] Mutation of input stated.

Related: `master_dsa_plan.md` §3 and §5, `06_data_structure_internals_deep_dive.md`.
