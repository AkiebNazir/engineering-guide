# Complexity Analysis — Big-O, Recursion, Amortization, and Reading Constraints

This is the vocabulary every other file in this module uses to talk about "fast" and
"slow" — start here if you're new to CS fundamentals in general, even before the other
files. This chapter starts from first principles — what complexity analysis measures,
what it deliberately ignores, and how its parts fit together — then goes as deep as
Google interviewers expect: they expect you to state time AND space complexity
**before being asked**, including recursion stack space and hidden costs like slicing.
It covers the reasoning, not just the table: how to derive the bound, how to handle
recursion (recursion trees and the master theorem), amortized analysis, how to use the
input constraints to predict the intended algorithm, how to check a bound by
measuring it, why some problems have provable lower bounds, and what to say when a
problem is NP-hard. Corrections of common myths are marked **Precision note**. A
side-by-side breakdown of what Junior through Staff+ engineers are expected to know
closes out the chapter, just before the interview checklist.

## Foundations — What Is Complexity Analysis, and How Does It Work?

### Why Complexity Analysis Exists

Suppose two engineers each write a function that finds duplicates in a list, and you
want to know which is better. You could time them — but on whose laptop, on what
input, with which other programs running? One is faster on 100 items and slower on
a million; one is written in C and the other in Python. Timings answer "how fast was
this run," not "how good is this algorithm."

What survives all those differences is **how the work grows as the input grows**. An
algorithm whose work doubles when the input doubles will, sooner or later, beat one
whose work quadruples, no matter the language or machine. Complexity analysis is the
discipline of describing that growth precisely, from the code alone, before running
anything. It's how you compare approaches at a whiteboard, how you know a solution
will survive production-sized input, and how an interviewer checks that you
understand what you wrote.

### What Complexity Analysis Actually Is

It's counting, with deliberate simplifications:

1. **Pick the input size** `n` (or several: `m` and `n` for two strings, `V` and `E`
   for a graph).
2. **Pick a cost model**: which operations count as one step. The standard one (the
   *RAM model*) treats each arithmetic operation, comparison, array index and
   assignment on a fixed-size number as one step of constant cost.
3. **Count the steps as a function of `n`** — for example `T(n) = 3n² + 10n + 7`.
4. **Keep only the shape of growth**: drop constant factors and lower-order terms,
   giving `O(n²)`.

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

### Why the Ordering of Growth Rates Is the Most Useful Fact Here

`O(1)` ("constant") means the work doesn't depend on `n` — looking up one hash-map key,
say. `O(log n)` ("logarithmic") means the work grows *very* slowly: binary search on a
billion items takes about 30 steps, not a billion — every step throws away half of
what's left. From slowest-growing to fastest-growing: `O(1) < O(log n) < O(n) <
O(n log n) < O(n²) < O(2ⁿ) < O(n!)`. The numbers show why the ordering dominates
everything else:

| Growth | n = 10 | n = 1,000 | n = 1,000,000 | At ~10⁸ simple steps/s, n = 10⁶ takes about |
|---|---|---|---|---|
| log₂ n | 3.3 | 10 | 20 | nothing measurable |
| n | 10 | 1,000 | 10⁶ | 10 ms |
| n log₂ n | 33 | ~10⁴ | ~2 × 10⁷ | 0.2 s |
| n² | 100 | 10⁶ | 10¹² | ~3 hours |
| 2ⁿ | 1,024 | a 302-digit number | — | never |
| n! | 3,628,800 | — | — | never |

(The time column is an order-of-magnitude estimate; Python is roughly 10× slower than
the 10⁸ figure, see §8.) A constant factor of 10 or even 100 in front of `n log n`
doesn't rescue an `n²` algorithm at a million items. That's what lets you say "an
`O(n log n)` sort beats an `O(n²)` approach on a large input" without measuring
anything.

**Why "drop the constants" is allowed, and why it's still worth caring about constants
in practice.** `O(2n)` and `O(n)` are both called `O(n)` — Big-O describes the *shape*
of growth, not the exact operation count, because for large enough `n` the shape is
what dominates. But real interview answers still say things like "this is O(n) but
with a lot of work per element" when it matters, and at realistic sizes a C-level
`O(n log n)` built-in regularly beats a pure-Python `O(n)` loop (§1, §10).

**Time vs. space.** Everything above measures *time* (how much work). The exact same
notation measures *space* (how much extra memory an algorithm uses beyond its input) —
a hash-map-based solution might be `O(n)` time and `O(n)` space, while a two-pointer
solution on the same problem might be `O(n)` time and `O(1)` space. §7 covers space
precisely, including a detail beginners usually miss: recursion itself uses space
(each pending call takes memory until it returns).

**Try it: race the growth rates.** Drag `n` from 20 up to a billion and switch the machine between Python and a compiled language. Three things to notice: below about n = 20 every class is instant, so brute force is a fine answer; `O(n²)` crosses the one-second line near n = 10⁴ in a compiled language and earlier in Python; and nothing exponential ever comes back once it leaves the chart. The chips under the chart are §8's “read the constraints” table, computed live.

<div class="lab" data-viz="cs-growth"></div>

### The Core Components of a Complexity Analysis

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **Input size variables** | What `n` is — and naming each independent size separately (`m`, `n`, `k`, `V`, `E`) | §1 |
| **Cost model** | Which operations count as one step; where hidden non-constant costs live (slicing, hashing long keys, big integers) | §3, §13 |
| **Case** | Worst, average/expected, or amortized — a bound means little until you say which | §1, §6 |
| **Bound type** | O (at most), Ω (at least), Θ (exactly, up to constants) | §1, §11 |
| **Derivation technique** | Loop counting, "each pointer moves at most n times", recursion trees, the master theorem | §2, §4, §5 |
| **Resource** | Time, and space (auxiliary structures + recursion stack + output) | §7 |
| **Evidence** | Measuring growth to confirm (or refute) a derived bound | §10 |

### How the Pieces Fit Together

```arch
%% caption: Analysis turns code into a step count, keeps its dominant term, and reports a bound for a stated case, resource and set of input sizes.
grid 175x110
node size "Input sizes" at 0,0 shape=pill color=slate sub="n, m, k, V, E"
node code "Your code" at 1,0 icon=code sub="loops, recursion, calls"
node model "Cost model" at 2,0 shape=pill color=slate sub="what is one step?"
group derive "Derive" color=blue icon=sigma
node loops "Count loops" at 0,1 in derive shape=card icon=sigma sub="add in sequence, multiply when nested"
node rec "Recursion" at 1,1 in derive shape=card icon=tree sub="tree or master theorem"
node amort "Amortize" at 2,1 in derive shape=card icon=counter sub="total ÷ operations"
node tn "T(n)" at 1,2 shape=pill color=amber sub="e.g. 3n² + 10n + 7 steps"
node bound "O(n²)" at 1,3 shape=pill color=green sub="worst-case time, O(1) space"
code -> loops
code -> rec
code -> amort
loops -> tn
rec -> tn
amort -> tn
size ..> loops : "in terms of"
model ..> amort : "what counts"
tn -> bound : "keep dominant term"
```

### Vocabulary You'll Meet Below, in One Table

| Term | One-line meaning |
|---|---|
| Big-O, O(f) | Grows no faster than f, up to a constant factor (an upper bound) |
| Ω(f), Θ(f) | Lower bound; tight bound (both O and Ω) |
| Worst / average case | The most expensive input of size n; the expected cost over a stated input distribution or random choices |
| Amortized | Total cost of any sequence of operations ÷ their number |
| Auxiliary space | Extra memory beyond the input (and usually beyond the output) |
| Recursion tree | A picture of every call a recursive function makes, with the work at each |
| Master theorem | A formula for divide-and-conquer recurrences T(n) = a·T(n/b) + O(n^d) |
| Output-sensitive | A bound that depends on the size of the answer, e.g. O(n + k) |
| Lower bound (of a problem) | No algorithm in a given model can do better, e.g. Ω(n log n) comparison sorting |
| Pseudo-polynomial | Polynomial in a numeric *value* (like a capacity W), exponential in its bit length |
| NP-hard | At least as hard as every problem in NP; no polynomial algorithm is known |

With that foundation — what Big-O measures, why the ordering above holds, and that
time and space are measured the same way — the rest of this file is the precise,
interview-depth version: deriving bounds from code, handling recursion, amortized
analysis, reading a problem's constraints to predict the intended algorithm, checking
a bound empirically, and knowing where no algorithm can do better.

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
%% caption: The full call tree of naive fib(4): 9 calls, with fib(2) computed twice. Time is the number of nodes; stack space is only the depth.
route straight
grid 80x80
node f4 "f(4)" at 2.5,0 shape=circle color=blue
node f3 "f(3)" at 1.25,1 shape=circle color=blue
node f2b "f(2)" at 3.5,1 shape=circle color=amber
node f2a "f(2)" at 0.5,2 shape=circle color=amber
node l2 "f(1)" at 2,2 shape=circle color=green
node l3 "f(1)" at 3,2 shape=circle color=green
node l4 "f(0)" at 4,2 shape=circle color=green
node l0 "f(1)" at 0,3 shape=circle color=green
node l1 "f(0)" at 1,3 shape=circle color=green
f4 -- f3
f4 -- f2b
f3 -- f2a
f3 -- l2
f2b -- l3
f2b -- l4
f2a -- l0
f2a -- l1
```

Naive `fib(n)` branches about twice per call and is n levels deep, so it makes about
φⁿ ≈ 1.618ⁿ calls (O(2ⁿ) is a valid, looser upper bound; fib(5) already makes 15
calls and fib(30) about 2.7 million), while the stack never holds more than n frames
at once. The amber nodes are the repeated work memoization removes: with a cache,
each of the n + 1 distinct subproblems is computed once, O(n) total.

| Pattern | Calls | Work per call | Time | Space (stack) |
|---|---|---|---|---|
| Linear recursion f(n-1) | n | O(1) | O(n) | O(n) |
| Binary tree traversal | n nodes | O(1) | O(n) | O(h): O(log n) balanced, O(n) skewed |
| Naive Fibonacci | ~φ^n | O(1) | O(φ^n) | O(n) |
| Memoized DP with S states | S | O(transitions) | O(S × transitions) | O(S) cache + O(depth) stack |
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

**Try it: build the recursion tree level by level.** Each row is one level of the tree and its bar is the total work on that level. Pick merge sort and every bar is equal (case 2: equal work × log n levels). Pick Karatsuba and the bars grow towards the leaves (case 1). Pick quickselect and they shrink (case 3: the root's O(n) pays for almost everything). That picture *is* the master theorem: the three cases just name which end of the tree is heaviest.

<div class="lab" data-viz="cs-master"></div>

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

**Try it: watch the bill for appends.** Press play with doubling, then with “+4”. With doubling, the red spikes (resizes) get rarer exactly as fast as they get taller, so the green average line flattens below 3. With a constant increment the spikes keep coming every 4 appends and the average climbs forever: O(n) per append and O(n²) to build the list. The same geometric-growth argument is why hash-table resizing is O(1) amortized.

<div class="lab" data-viz="cs-amortized"></div>

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

## 10. Measure It: Checking a Bound Empirically

A derived bound is a claim; a quick experiment checks it. The trick is the **growth
experiment**: time the function at n and at 4n. If the cost is ~c·nᵏ, the ratio is
4ᵏ, so log₄(ratio) estimates the exponent k. You don't need the absolute times to mean
anything — only the ratio. Inputs are built outside the timed region, the garbage
collector is paused, and each time is the best of five (`python3 growth_exp.py`):

```python
"""Growth experiment: time f(n) and f(4n); log4 of the ratio estimates k in O(n^k)."""
import gc
import math
import random
import time
from collections import deque

def drain_list(xs):                    # list.pop(0) shifts every remaining element left
    while xs:
        xs.pop(0)

def drain_deque(xs):                   # deque.popleft() is O(1)
    q = deque(xs)
    while q:
        q.popleft()

def concat_str(xs):                    # s = s + "x" builds a brand-new string every time
    s = ""
    for _ in xs:
        s = s + "x"
        keep = s                       # a second reference defeats CPython's in-place resize trick
    return keep

def join_str(xs):
    return "".join("x" for _ in xs)

def sort_shuffled(xs):                 # Timsort on random order: O(n log n)
    xs.sort()

def sort_descending(xs):               # Timsort finds one descending run and reverses it: O(n)
    xs.sort()

CASES = [  # (function, n, input builder) - inputs are built outside the timed region
    (drain_list, 25_000, lambda n: list(range(n))),
    (drain_deque, 500_000, lambda n: list(range(n))),
    (concat_str, 25_000, lambda n: range(n)),
    (join_str, 500_000, lambda n: range(n)),
    (sort_shuffled, 250_000, lambda n: random.Random(n).sample(range(n), n)),
    (sort_descending, 1_000_000, lambda n: list(range(n, 0, -1))),
]

def best_time(f, build, n, repeat=5):
    best = math.inf
    for _ in range(repeat):
        data = build(n)
        gc.collect(); gc.disable()     # keep the garbage collector out of the timed region
        t = time.perf_counter(); f(data); best = min(best, time.perf_counter() - t)
        gc.enable()
    return best

print(f"{'function':16} {'n':>7} {'t(n) ms':>9} {'t(4n) ms':>9}  exponent k")
for f, n, build in CASES:
    f(build(4 * n))                    # warm-up: let the allocator grab its memory arenas first
    t1, t2 = best_time(f, build, n), best_time(f, build, 4 * n)
    print(f"{f.__name__:16} {n:7} {t1 * 1e3:9.1f} {t2 * 1e3:9.1f}  {math.log(t2 / t1, 4):5.2f}")
```

One run (verified with Python 3.11 on a shared cloud VM; the times and the second
decimal of k vary from run to run):

```text
function               n   t(n) ms  t(4n) ms  exponent k
drain_list         25000      47.5     814.2   2.05
drain_deque       500000      12.9      45.6   0.91
concat_str         25000       3.6     115.4   2.51
join_str          500000      13.7      63.2   1.10
sort_shuffled     250000      48.7     273.8   1.25
sort_descending  1000000       7.0      39.7   1.25
```

How to read it:

- **The estimates cluster near 1 or near 2**, which is all the experiment needs to
  tell you. `list.pop(0)` and `s = s + "x"` are quadratic (memory traffic can push
  the string case a little above 2); their fixes (`deque`,
  `join`) are linear. Timing noise moves k by a few tenths; it never turns a 1 into
  a 2.
- **O(n log n) looks like k slightly above 1.** Going from n to 4n multiplies
  log n by only about 1.1 at these sizes, and cache effects on larger arrays add a
  little more. Don't expect a growth experiment to separate n from n log n cleanly.
- **Input shape matters.** The same `sort` is O(n) on already-ordered data because
  Timsort/Powersort detects runs — a real best case, not a measuring error. State the
  worst case in an interview, then mention the adaptive best case.
- **Precision note:** the quadratic string build only shows up because the loop keeps
  a second reference to `s`. Without it, CPython often resizes the string in place
  and the loop looks linear — an implementation detail you must not rely on (§3).

## 11. Lower Bounds: When No Algorithm Can Do Better

An upper bound describes *your algorithm*. A lower bound describes *the problem*: no
algorithm in a stated model can beat it. Knowing the main ones stops you hunting for
an impossible improvement, and knowing their assumptions shows you how to escape them.

**Comparison sorting is Ω(n log n).** A sort that learns about its input only by
comparing pairs can be drawn as a **decision tree**: each internal node is one
comparison, each leaf is one final ordering. For three items:

```arch
%% caption: Any comparison sort is a decision tree; with n! possible orderings as leaves, some path must be at least log2(n!) comparisons long.
route straight
grid 130x95
node r "a < b?" at 2,0 shape=diamond color=amber
node d1 "b < c?" at 1,1 shape=diamond color=amber
node d2 "a < c?" at 3,1 shape=diamond color=amber
node abc "a b c" at 0,2 shape=pill color=green
node d3 "a < c?" at 1,2 shape=diamond color=amber
node bac "b a c" at 2,2 shape=pill color=green
node d4 "b < c?" at 3,2 shape=diamond color=amber
node acb "a c b" at 0,3 shape=pill color=green
node cab "c a b" at 1,3 shape=pill color=green
node bca "b c a" at 2,3 shape=pill color=green
node cba "c b a" at 3,3 shape=pill color=green
r -> d1 : "yes"
r -> d2 : "no"
d1 -> abc : "yes"
d1 -> d3 : "no"
d2 -> bac : "yes"
d2 -> d4 : "no"
d3 -> acb : "yes"
d3 -> cab : "no"
d4 -> bca : "yes"
d4 -> cba : "no"
```

The tree must have at least one leaf per possible ordering, n! of them, and a binary
tree with n! leaves has a path of length at least log₂(n!). By Stirling's formula
log₂(n!) ≈ n log₂ n − 1.44n, which is Θ(n log n). The same argument bounds the
*average* case too, because the average leaf depth of a binary tree with N leaves is
also at least log₂ N. Counting the comparisons real sorts make shows how close they
get (`python3 comparisons.py`):

```python
"""Count the comparisons a real sort makes and compare with the log2(n!) lower bound."""
import math
import random

class Counted:
    """Wraps a value and counts every < comparison made on it."""
    count = 0
    __slots__ = ("v",)
    def __init__(self, v): self.v = v
    def __lt__(self, other):
        Counted.count += 1
        return self.v < other.v

def merge_sort(xs):
    if len(xs) <= 1:
        return xs
    mid = len(xs) // 2
    left, right = merge_sort(xs[:mid]), merge_sort(xs[mid:])
    out, i, j = [], 0, 0
    while i < len(left) and j < len(right):
        if right[j] < left[i]:
            out.append(right[j]); j += 1
        else:
            out.append(left[i]); i += 1
    return out + left[i:] + right[j:]

rng = random.Random(3)
print(f"{'n':>7} {'log2(n!)':>10} {'merge sort':>11} {'sorted()':>9} {'n*log2 n':>10}")
for n in (10, 100, 1_000, 10_000, 100_000):
    data = [Counted(rng.random()) for _ in range(n)]
    Counted.count = 0; merge_sort(data); ms = Counted.count
    Counted.count = 0; sorted(data); ts = Counted.count
    lower = math.lgamma(n + 1) / math.log(2)          # log2(n!) without computing n!
    print(f"{n:7} {lower:10.0f} {ms:11} {ts:9} {n * math.log2(n):10.0f}")
```

Output (verified with Python 3.11):

```text
      n   log2(n!)  merge sort  sorted()   n*log2 n
     10         22          21        23         33
    100        525         544       535        664
   1000       8529        8705      8622       9966
  10000     118458      120477    119836     132877
 100000    1516704     1536248   1528969    1660964
```

Both sorts stay within about 2% of log₂(n!) at large n — well below the looser
n·log₂ n. (At n = 10 merge sort used 21 comparisons, under the bound of 22: the bound
is on the worst and average case, and one lucky input can beat it.)

**Escaping a lower bound means leaving its model.** Counting sort (O(n + k) for values
in a range of size k) and radix sort (O(d·(n + b)) for d-digit keys in base b) never
compare two elements; they index by value, so the decision-tree argument doesn't
apply. That's the precise answer to "can you sort faster than n log n?": *yes, if the
keys are small integers or fixed-length strings, because then you're not limited to
comparisons.*

Other lower bounds worth quoting:

| Problem | Lower bound | Why / escape hatch |
|---|---|---|
| Search in an unsorted array | Ω(n) | Any unread element might be the target; escape by sorting or hashing first |
| Search in a sorted array, by comparisons | Ω(log n) | Decision tree with n + 1 outcomes; hashing escapes it for exact lookups |
| Element distinctness, by comparisons | Ω(n log n) | Algebraic decision trees; hashing gives O(n) expected |
| Merge two sorted lists of n | Ω(n) | Must output 2n items (output-sensitive) |
| Any algorithm producing k results | Ω(k) | Can't write k things in less than k steps |
| Finding the max | n − 1 comparisons exactly | Every non-max element must lose at least once |

## 12. When the Problem Is NP-Hard

Some interview problems (or their follow-ups) are NP-hard: travelling salesman,
0/1 knapsack, subset sum, graph colouring, Hamiltonian path, set cover. No
polynomial-time algorithm is known for any of them, and finding one would prove
P = NP. You won't be asked to prove NP-hardness, but you will earn signal for
recognising it and knowing the standard responses:

| Response | When it works | Example |
|---|---|---|
| Exponential but optimized exact search | Small n (constraints say n ≤ ~20) | TSP by Held–Karp bitmask DP: O(n²·2ⁿ) instead of O(n!) — n = 20 is ~4 × 10⁸ steps, n! is ~2.4 × 10¹⁸ |
| Pseudo-polynomial DP | Numbers are small | 0/1 knapsack in O(n·W) for capacity W |
| Backtracking with pruning | Solutions are rare or constraints prune hard | Sudoku, N-Queens, graph colouring |
| Approximation with a guarantee | "Close to optimal" is fine | Greedy set cover (within a ln n factor), 2-approximation for vertex cover, Christofides-style bounds for metric TSP |
| Heuristics / local search | Large instances, no guarantee needed | 2-opt for routing, simulated annealing |
| Hand it to a solver | Production scheduling and planning | ILP (OR-Tools, Gurobi), SAT/SMT solvers |

**Precision note — pseudo-polynomial is not polynomial.** Knapsack's O(n·W) looks
polynomial, but input size is measured in *bits*: W takes only log₂ W bits to write
down, so O(n·W) = O(n·2^(bits of W)), exponential in the input size. That's why
knapsack DP is fast when W ≤ 10⁴ and hopeless when W = 10¹⁸, and why knapsack is
NP-hard despite having a "polynomial-looking" DP. The same logic explains why
checking whether a number N is prime by trial division in O(√N) is *not* a
polynomial algorithm (it's exponential in the number of digits); AKS (2002) is the
polynomial one.

## 13. Bounds to Quote Exactly

Interviewers notice when a bound is almost right. The ones most often misquoted:

| Algorithm / operation | Correct bound | Common mistake |
|---|---|---|
| BFS / DFS on an adjacency list | O(V + E) | "O(V²)" (that's the adjacency matrix) or "O(E)" (forgets isolated vertices) |
| Dijkstra with a binary heap | O((V + E) log V) | "O(V log V)"; also: wrong with negative edges |
| Dijkstra with a Fibonacci heap | O(E + V log V) | Quoting it as the practical choice (binary heaps win in practice) |
| Bellman-Ford | O(V·E) | — |
| Floyd-Warshall | O(V³) time, O(V²) space | — |
| Kruskal | O(E log E) = O(E log V) | Forgetting the sort dominates |
| Topological sort (Kahn / DFS) | O(V + E) | — |
| Union-Find, both optimizations | O(α(n)) amortized per op | "O(log n)" (that's with only one of the two) |
| Sorting n strings of length L | O(L · n log n) worst case | "O(n log n)": each comparison can cost O(L) |
| Hashing a string key | O(L) | "O(1)": the hash reads every character (CPython caches `str` hashes afterwards) |
| Quickselect | O(n) expected, O(n²) worst | "O(n)" without saying expected; median-of-medians is worst-case O(n) |
| Building a heap / `heapify` | O(n) | "O(n log n)" (see `06` §12) |
| `bisect.insort` into a list | O(n) (O(log n) search + O(n) shift) | "O(log n)" |
| KMP / Z-algorithm | O(n + m) | — |
| Rabin-Karp | O(n + m) expected, O(n·m) worst | Forgetting collision verification |
| Trie insert / search | O(L) per key | "O(log n)" |
| Counting sort / radix sort | O(n + k) / O(d·(n + b)) | Ignoring k when values are huge |

**Two small precision notes.** The base of a logarithm doesn't matter inside Big-O
(log₂ n and log₁₀ n differ by a constant factor), but it does matter in an exponent
(2^(log₂ n) = n, while 2^(log₁₀ n) = n^0.3). And O(n + m) is not O(n) unless you
know m ≤ c·n: a graph with E = V² edges makes O(V + E) quadratic in V.

## What Each Engineering Level Should Know

Not everyone reading this file needs every sentence of it cold. This table maps this
chapter's material onto a standard industry ladder *and* the Google-style ladder this
repo's interview content is written against, side by side. The mapping between
company-specific titles and levels is approximate and varies by company, but the
*depth of understanding* described in each row is a reliable signal regardless of
which company uses which label. Use it as a syllabus (read down a column) or as a
self-assessment (find the cell that matches where a real interview would place you).

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **What Big-O measures** (Foundations, §1) | Knows O(1), O(n), O(n²) and their order | Separates worst, average and amortized; keeps separate variables for separate inputs | Uses O/Ω/Θ precisely and states the cost model when it matters (string hashing, big integers) | Explains when asymptotics mislead (constants, caches, small n) and decides by measurement |
| **Deriving bounds from code** (§2–§3) | Counts nested loops | Applies "each pointer moves at most n times" and spots slicing/`in list` costs | Derives tight bounds for any interview solution, hidden costs included, before being asked | Spots accidental quadratic behaviour in code review and production profiles |
| **Recursion & the master theorem** (§4–§5) | Knows recursion uses stack space | Draws a recursion tree and counts memoized states | Applies the master theorem and knows where it doesn't apply (uneven splits) | Reasons about recursive algorithms' memory and depth limits in production runtimes |
| **Amortized analysis** (§6) | Has heard "amortized O(1) append" | Explains the doubling argument | Uses the aggregate and accounting methods on stacks, windows, Union-Find | Chooses amortized vs. worst-case-bounded structures for latency-sensitive systems (resize pauses, GC) |
| **Space** (§7) | Counts extra arrays | Counts the recursion stack and the output separately | States all three parts and whether the input is mutated | Budgets memory for a service by structure and object overhead |
| **Constraints & measurement** (§8, §10) | Uses the constraints table when reminded | Predicts the intended complexity from n | Predicts the technique from constraints and verifies a bound with a growth experiment | Designs benchmarks that isolate the effect being measured (warm-up, GC, input shape) |
| **Lower bounds & hardness** (§11–§13) | Knows sorting is "n log n" | Knows comparison sorting can't beat n log n | Proves the decision-tree bound, escapes it with counting/radix sort, recognises NP-hard problems and pseudo-polynomial DPs, quotes graph/string bounds exactly | Picks approximation, solver or heuristic strategies for NP-hard product problems and defends the trade-off |

**Reading this table as a study plan:** if you're aiming at a Senior/L5 bar, your
target is the whole "Senior" column, which the numbered sections (1–13) deliver in
full. The Foundations section alone takes you to roughly the "Mid-Level" column. The
"Staff+" column is judgment that mostly comes from operating real systems at scale;
this file gives you the vocabulary to have that conversation, not a substitute for
having had it.

## Interview checklist

- [ ] I can explain what Big-O measures, what it ignores, and why the growth ordering beats constant factors at scale.
- [ ] I can distinguish O, Ω and Θ, and worst, average and amortized cases, and say which one I mean.
- [ ] I can derive loop bounds, including the "each pointer moves at most n times" argument.
- [ ] I can list the hidden costs (slicing, string building, `in list`, hashing long keys) and spot them in my own code.
- [ ] I can draw a recursion tree, count memoized states, and apply the master theorem.
- [ ] I can prove amortized O(1) for a dynamic array and a monotonic stack.
- [ ] I can state space as auxiliary + stack + output, and say whether I mutate the input.
- [ ] I can predict the intended complexity from the constraints.
- [ ] I can check a bound with a growth experiment and read its result sensibly.
- [ ] I can prove comparison sorting is Ω(n log n) and explain how counting/radix sort escape it.
- [ ] I can recognise an NP-hard problem, explain why knapsack's O(n·W) is pseudo-polynomial, and name the standard responses.

Related: [MAANG/FAANG DSA Master Plan](../master_dsa_plan.md) §3 and §5, [Data Structure Internals](06_data_structure_internals_deep_dive.md), [Running the 45-Minute Coding Round](09_coding_round_execution_deep_dive.md) §2 (when to state complexity), [Google-Style Follow-Ups — Scaling a Coding Answer](10_google_follow_ups_deep_dive.md).
