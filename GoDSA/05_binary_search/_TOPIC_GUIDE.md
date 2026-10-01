# Topic 05 · Binary Search — Go Deep Dive

> Binary search is three lines of logic wrapped in a hundred off-by-one bugs.
> Go doesn't hide the index arithmetic behind a `bisect` module the way Python
> does — you write the loop yourself, which means you also write the bugs
> yourself. This is the document that gives you templates you don't have to
> re-derive under interview pressure, plus the handful of Go-specific traps
> (integer overflow, `sort.Search`'s inverted signature, no O(1) indexing on
> linked structures) that don't exist in the Python version of this topic.

---

## Part 1 · The Midpoint, and Why You Write It That Way

### 1.1 `left + (right-left)/2`, never `(left+right)/2`

```go
mid := left + (right-left)/2   // ✅ always safe
mid := (left + right) / 2      // ⚠️ can overflow
```

Both compute the same mathematical value when there's no overflow, and on a
64-bit Go `int` (which is what `int` is on every modern platform Go targets),
overflow requires `left+right` to exceed `math.MaxInt64 ≈ 9.2×10^18`. You will
never build a slice with that many elements — you'd run out of RAM millions of
times over first. So in practice, **for slice indices this specific bug cannot
fire on 64-bit Go**.

Write it the safe way anyway, for three reasons:

1. **It's the reflexive interview question.** "Why did you write it that way?"
   is asked specifically to see if you understand *why*, not to catch a bug
   that will actually occur. Answering "muscle memory" instead of explaining
   the overflow mechanics reads as not understanding your own code.
2. **`int` is not always 64 bits.** Go's spec only guarantees `int` is at
   least 32 bits and matches the platform word size. On a 32-bit build target
   (`GOARCH=386`, or WASM in some configurations), `math.MaxInt32 ≈ 2.1×10^9`,
   and `left+right` overflowing becomes reachable with large-but-plausible
   index values — think large generated test fixtures, not just adversarial
   input.
3. **The values aren't always indices.** The moment you reuse this pattern for
   binary-search-on-answer over `int64` bounds (capacity, timestamps, money in
   cents), the safe range shrinks and the overflow becomes a real, silent bug:
   wraps to a negative number, and your `mid` lands outside `[left, right]`.

```
left, right near MaxInt64:
  left+right            → wraps around to a large-magnitude NEGATIVE number
  mid = (left+right)/2  → negative, or nonsensical — comparisons go haywire
                           silently: no panic, no crash, just a wrong answer

  left + (right-left)/2 → (right-left) is small and positive by construction
                           (right >= left in every correct binary search),
                           so no intermediate value ever leaves [left, right]
```

> ⚠️ Go **wraps** on signed integer overflow — it does not panic and does not
> promote to a bigger type, unlike Python's arbitrary-precision integers. See
> topic 1's Part 3 table: this is the same "integer overflow" row, and binary
> search is the canonical place it bites in practice, because the whole
> algorithm is built out of index arithmetic.

---

## Part 2 · The Standard Library's Three Binary Searches

Go's standard library gives you binary search as **a predicate over an index
range**, not as a "find this value" function. This is the single biggest
mental shift coming from Python's `bisect` module.

### 2.1 `sort.Search` — the general form

```go
func Search(n int, f func(int) bool) int
```

Contract: `f` must be **monotonic** over `[0, n)` — false for a prefix, then
true for the rest (`FFFFTTTT`, never `FTFT`). `sort.Search` returns the
**smallest index `i` in `[0, n]` for which `f(i)` is true**, or `n` if `f` is
never true. It does binary search on the *predicate*, not on your data — your
data only enters through what `f` closes over.

```go
nums := []int{1, 3, 3, 5, 7, 9}
target := 3

// leftmost index where nums[i] >= target  ("lower_bound")
i := sort.Search(len(nums), func(i int) bool { return nums[i] >= target })
// i == 1

// leftmost index where nums[i] > target   ("upper_bound")
j := sort.Search(len(nums), func(i int) bool { return nums[i] > target })
// j == 3  →  [i, j) is the run of 3s: this is how you get COUNT of a value
count := j - i   // 2
```

This is exactly `bisect.bisect_left` / `bisect.bisect_right` from Python — Go
just makes you assemble them from the primitive instead of importing them.
**Write `lowerBound`/`upperBound` helpers once and reuse them** (Part 5 below).

> ⚠️ If `f` is not actually monotonic, `sort.Search` doesn't error — it just
> returns a meaningless index, silently. There's no runtime check. This is the
> Go standard library trusting you the way `append` trusts you not to alias
> incorrectly (topic 1, Part 1.2): a documented precondition, unchecked.

### 2.2 `sort.SearchInts`, `sort.SearchStrings`, `sort.SearchFloat64s`

Thin convenience wrappers over `sort.Search` for the common case of "find
where `target` belongs in a sorted slice":

```go
nums := []int{1, 3, 5, 7, 9}
i := sort.SearchInts(nums, 5)   // 2 — index of 5, or where it would insert
i2 := sort.SearchInts(nums, 4)  // 2 — 4 isn't present; this is its insertion point
```

Note this **always gives you lower_bound semantics** (leftmost insertion
point) — there's no `SearchIntsRight`. For rightmost, drop back to
`sort.Search` with `>` instead of `>=`.

### 2.3 `slices.BinarySearch` (Go 1.21+) — the modern, generic form

```go
func BinarySearch[S ~[]E, E cmp.Ordered](x S, target E) (int, bool)
```

```go
nums := []int{1, 3, 5, 7, 9}
i, found := slices.BinarySearch(nums, 5)   // i=2, found=true
i, found  = slices.BinarySearch(nums, 4)   // i=2, found=false — insertion point
```

This is the one difference from `sort.SearchInts` worth internalizing: you get
a `found bool` back directly instead of having to re-check `nums[i] == target`
yourself. `slices.BinarySearchFunc` takes a custom comparator (returns
negative/zero/positive, like `slices.SortFunc` — see topic 1, Part 1.6) for
searching slices of structs.

**Which to reach for:**

| Situation | Use |
|---|---|
| Custom monotonic condition (not a plain value lookup) | `sort.Search` |
| Plain value lookup, need the `bool`, Go 1.21+ available | `slices.BinarySearch` |
| Plain value lookup, older Go / already importing `sort` | `sort.SearchInts` et al. |
| Searching structs / custom ordering | `slices.BinarySearchFunc` |
| Binary search **on the answer space**, not on a slice | `sort.Search` (Part 3.3) |

---

## Part 3 · The Four Templates

### 3.1 Exact match

```go
func binarySearch(nums []int, target int) int {
    left, right := 0, len(nums)-1
    for left <= right {
        mid := left + (right-left)/2
        switch {
        case nums[mid] == target:
            return mid
        case nums[mid] < target:
            left = mid + 1
        default:
            right = mid - 1
        }
    }
    return -1
}
```

`left <= right` (not `<`) because with a single remaining element
(`left == right`) there's still one candidate to check. This is the template
every other one is a variation of.

### 3.2 Rotated sorted array — "which half is sorted"

The array is sorted, then rotated at an unknown pivot:
`[4,5,6,7,0,1,2]`. The key insight: **at least one half of `[left, mid]` /
`[mid, right]` is always normally sorted**, even though the whole array isn't.
Determine which half is sorted by comparing the endpoints, then check whether
the target lies in that sorted half's range — if so recurse into it, otherwise
recurse into the other half.

```
[4, 5, 6, 7, 0, 1, 2]     target = 0
 L        M        R
nums[L]=4 <= nums[M]=7  →  LEFT half [4,5,6,7] is sorted
is target(0) in [nums[L]..nums[M]] = [4..7]?  No → search RIGHT half instead
```

Full implementation in Part 5.

### 3.3 Binary search on the answer space

The predicate isn't `nums[i] >= target` over slice indices — it's a monotonic
*feasibility* function over a numeric range you're searching, e.g. "can I ship
all packages within `D` days using capacity `c`?" (LC 1011) or "can I eat all
bananas in `H` hours at speed `k`?" (LC 875). The shape is identical to
`sort.Search`; only the domain changes.

```go
// LC 875 Koko Eating Bananas: minimum eating speed k such that
// Koko finishes all piles within h hours.
func minEatingSpeed(piles []int, h int) int {
    maxPile := slices.Max(piles)

    // feasible(k): can Koko finish at speed k?  Monotonic: if k works, k+1 works.
    feasible := func(k int) bool {
        hours := 0
        for _, p := range piles {
            hours += (p + k - 1) / k   // ceil(p / k) without float math
        }
        return hours <= h
    }

    // sort.Search wants indices [0, n); shift the domain to [1, maxPile].
    // f(i) here tests speed (i+1), so the returned index i maps back to speed i+1.
    return 1 + sort.Search(maxPile, func(i int) bool { return feasible(i + 1) })
}
```

**Recognizing this pattern in an interview:** the problem asks for a minimum
(or maximum) value satisfying some condition, brute force would be "try every
possible value and check," and checking one candidate value is itself cheap
(usually O(n)) while the *range* of candidate values is large. That's binary
search on the answer, giving O(n log(range)) instead of O(n · range).

### 3.4 Floating-point binary search — fixed iterations, not epsilon

For continuous domains (e.g., "find x such that f(x) = target" over reals),
there's no natural integer index to hand `sort.Search`, so you write the loop
by hand — and the termination condition changes:

```go
func sqrtBinarySearch(x float64) float64 {
    lo, hi := 0.0, math.Max(x, 1.0)
    for i := 0; i < 100; i++ {   // ✅ fixed iteration count
        mid := lo + (hi-lo)/2
        if mid*mid < x {
            lo = mid
        } else {
            hi = mid
        }
    }
    return lo
}
```

> ⚠️ **Don't terminate on `hi-lo < epsilon`.** Float64 has ~15-17 significant
> decimal digits; picking an epsilon that's meaningful across every possible
> magnitude of `x` your function might see is genuinely hard — too large and
> you under-converge, too small and `hi-lo` may never get that close due to
> floating-point rounding, looping until you hit an unrelated iteration cap
> anyway. A **fixed count of ~100 iterations** halves the search interval 100
> times regardless of its starting width — that's precision far beyond
> float64's mantissa (52 bits ⇒ full convergence in ~60 iterations), it's
> `O(1)` extra iterations relative to any epsilon scheme, and it can't loop
> forever. This is idiomatic in competitive Go; reach for it over epsilon
> comparisons by default.

---

## Part 4 · Complexity, and Why Binary Search Needs Random Access

| Structure | Binary search complexity | Why |
|---|:--:|---|
| `[]T` (slice) | **O(log n)** | `s[mid]` is O(1) — direct pointer arithmetic (topic 1, Part 1.2) |
| Sorted array (any language) | **O(log n)** | Same reason — contiguous, indexable memory |
| `container/list` (Go's linked list) | **O(n)** | No O(1) index — reaching "the middle" means walking `n/2` pointers *every time* |
| `map[K]V` | N/A | Unordered — there's no "half" to discard (topic 1, Part 2) |

This is exactly why `sort.Search(n, f)` takes an `int` count and an index
predicate rather than a container: **the algorithm has no way to be generic
over "a middle element" unless the container promises O(1) access to it.**
For a `[]T` that promise is free (it's a value type with a length, topic 1,
Part 1.4). For `container/list.List` it would silently become O(n) per probe,
O(n log n) total — no better than a linear scan with extra bookkeeping, which
is exactly why the standard library doesn't offer a binary search over it.

**The rule to state in an interview:** binary search's O(log n) bound is
conditional on O(1) random access to the middle element. If your data lives in
a structure without that (a linked list, a stream, a b-tree you're walking
node-by-node), you are not doing O(log n) binary search anymore, even if the
control flow looks the same.

| Operation | Complexity |
|---|:--:|
| `sort.Search` / `slices.BinarySearch` | **O(log n)** probes, each O(1) |
| Binary search on answer space | **O(log(range) · cost-of-feasibility-check)** |
| Floating-point, fixed iterations | **O(iterations)**, iterations is a constant |
| Linear scan (for comparison) | O(n) |

---

## Part 5 · Building From Scratch

### 5.1 `lowerBound` / `upperBound` — the two primitives everything else composes from

```go
package search

import "sort"

// lowerBound returns the leftmost index i in [0, len(nums)] such that
// nums[i] >= target (or len(nums) if no such index exists).
// Equivalent to Python's bisect.bisect_left.
func lowerBound(nums []int, target int) int {
    return sort.Search(len(nums), func(i int) bool { return nums[i] >= target })
}

// upperBound returns the leftmost index i in [0, len(nums)] such that
// nums[i] > target (or len(nums) if no such index exists).
// Equivalent to Python's bisect.bisect_right.
func upperBound(nums []int, target int) int {
    return sort.Search(len(nums), func(i int) bool { return nums[i] > target })
}

// countTarget uses both to answer "how many times does target appear?"
// in O(log n) instead of an O(n) scan.
func countTarget(nums []int, target int) int {
    return upperBound(nums, target) - lowerBound(nums, target)
}

// insertPos: where would target go to keep nums sorted? Same as lowerBound —
// this is literally what Python's bisect.insort uses under the hood.
func insertPos(nums []int, target int) int {
    return lowerBound(nums, target)
}
```

### 5.2 Search in Rotated Sorted Array (LC 33)

```go
func search(nums []int, target int) int {
    left, right := 0, len(nums)-1

    for left <= right {
        mid := left + (right-left)/2

        if nums[mid] == target {
            return mid
        }

        if nums[left] <= nums[mid] {
            // Left half [left, mid] is normally sorted.
            if nums[left] <= target && target < nums[mid] {
                right = mid - 1   // target in the sorted left half
            } else {
                left = mid + 1    // target must be in the right half
            }
        } else {
            // Right half [mid, right] is normally sorted instead.
            if nums[mid] < target && target <= nums[right] {
                left = mid + 1    // target in the sorted right half
            } else {
                right = mid - 1   // target must be in the left half
            }
        }
    }

    return -1
}
```

**Talk track while writing:** exactly one of the two halves around `mid` is
guaranteed to be in normal sorted order (the rotation point can only fall in
one of them); use the endpoint comparison `nums[left] <= nums[mid]` to
identify which one, then a plain range check tells you whether `target` can
possibly be in that sorted half — if yes, recurse there, if no, it must be in
the other (still-rotated) half, so recurse there instead.

---

## Part 6 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Value lookup | `bisect.bisect_left/right(a, x)` | Build on `sort.Search`, or `slices.BinarySearch` |
| Returns "found" as a bool | No — check `a[i] == x` yourself | `slices.BinarySearch` gives you `found bool` directly |
| Generality | Operates on a sequence | `sort.Search` operates on an **abstract predicate**, decoupled from any container |
| Custom comparator | `key=` argument (3.10+) | `slices.BinarySearchFunc` with a `cmp`-style function |
| Midpoint overflow | Never — arbitrary precision ints | Must write `left + (right-left)/2` (Part 1) |
| Float search termination idiom | Same fixed-iteration idiom applies | Same — not language-specific, but worth stating explicitly |
| Linked-list binary search | Same O(n) trap conceptually | No stdlib temptation to try it — no binary-search helper ships for `container/list` |

---

## Part 7 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Exact-match binary search | O(log n) | O(1) | LC 704 |
| `lowerBound` / `upperBound` | O(log n) | O(1) | LC 34 Find First and Last Position |
| Rotated-array search | O(log n) | O(1) | LC 33, 81, 153, 154 |
| Binary search on answer space | O(n log(range)) | O(1) | LC 875 Koko, LC 1011 Ship Packages, LC 410 Split Array |
| 2D matrix search (treat as flattened 1D) | O(log(m·n)) | O(1) | LC 74 |
| Peak finding (compare to neighbor, discard half) | O(log n) | O(1) | LC 162 Find Peak Element |
| Floating-point search, fixed iterations | O(iterations) | O(1) | LC 69 Sqrt(x), "kth smallest ratio" style problems |

---

<!-- block:05_go_1_families -->
## Part 8 · Two Families and the Three Boundary Templates

Everything in Parts 2–5 is a *tool* (`sort.Search`, `slices.BinarySearch`). This Part is the *decision*: what
`lo` and `hi` are moving over, and which boundary you are hunting. All code below ran on Go 1.24.5.

```arch
%% caption: Two families of binary search. The only question is what lo and hi are moving over.
grid 240x100
node q "What are lo and hi moving over?" at 0.5,0 shape=pill
node a "Indices of a sorted slice" at 0,1 shape=box
node b "Candidate answers" at 1,1 shape=box sub="speed, capacity, days, distance ..."
node a1 "Family A: search ON the data" at 0,2 shape=card icon=search color=green sub="value lookup, insertion point, rotated, 2D"
node b1 "Family B: search ON the answer" at 1,2 shape=card icon=check color=orange sub="needs feasible(x), monotone: F F F T T T"
node b2 "The slice is USED INSIDE feasible" at 1,3 shape=card icon=filter sub="never searched directly"
q -> a
q -> b
a -> a1
b -> b1 -> b2
```

**The most-missed skill in this topic:** people fluent in Family A do not recognise Family B, because there is
no sorted slice in sight. If the question asks for the *minimum (or maximum) value that satisfies a condition*,
and checking one candidate is cheap, the candidate is what you search.

### The three boundary templates

```arch
%% caption: Three templates. What differs is which side keeps mid and which mid you compute. Pair them wrongly and the loop never ends.
grid 235x140
node q "Find a boundary in a monotone predicate" at 1,0 shape=pill
node a "Which boundary?" at 1,1 shape=diamond color=amber
node l "Smallest x that works" at 0,2 shape=card icon=code color=green w=215 sub="lo, hi := 0, n; mid := lo + (hi-lo)/2 (LOWER mid); if ok(mid) { hi = mid } else { lo = mid + 1 }"
node r "Largest x that works" at 1,2 shape=card icon=code color=orange w=215 sub="lo, hi := 0, n; mid := lo + (hi-lo+1)/2 (UPPER mid); if ok(mid) { lo = mid } else { hi = mid - 1 }"
node e "Exact match" at 2,2 shape=card icon=code color=green w=215 sub="lo, hi := 0, n-1; for lo <= hi; mid+1 and mid-1 on the two sides"
q -> a
a:L -> l:T : "leftmost True"
a -> r : "rightmost True"
a:R -> e:T : "exact match"
```

```go
// leftmost True — what sort.Search does for you. "smallest x with ok(x)".
lo, hi := 0, n
for lo < hi {
    mid := lo + (hi-lo)/2
    if ok(mid) { hi = mid } else { lo = mid + 1 }     // keep mid: it might BE the answer
}
// lo == hi == the answer (or n if none)

// rightmost True — "largest x with ok(x)". Note the UPPER mid.
lo, hi = 0, n
for lo < hi {
    mid := lo + (hi-lo+1)/2
    if ok(mid) { lo = mid } else { hi = mid - 1 }
}
```

**The infinite-loop rule.** `lo = mid` with a lower mid never advances once `hi == lo + 1` (`mid == lo`, so
`lo = lo`). Whenever a branch keeps `mid` on the *low* side, round the midpoint **up**; whenever it keeps `mid` on the
*high* side (`hi = mid`), round **down**. `sort.Search` is the leftmost form, and it is safe by construction — one
reason to prefer it over a hand-rolled loop.

### Family B recipe

1. Name the answer and its range: `lo` = the smallest value that could possibly work (`max(weights)`, not `1`),
   `hi` = one that certainly works (`sum(weights)`).
2. Write `feasible(x)` as an O(n) greedy check.
3. **State the monotonicity in one sentence** ("a bigger capacity can only help"), out loud, before coding.
4. Leftmost True for a *minimum*; rightmost True for a *maximum*.

```go
// LC 410 Split Array Largest Sum: minimise the largest piece over k splits.
func splitArray(nums []int, k int) int {
    lo, hi := slices.Max(nums), 0                  // an answer below max(nums) is impossible
    for _, x := range nums { hi += x }             // one piece holding everything always works
    feasible := func(cap int) bool {
        pieces, cur := 1, 0
        for _, x := range nums {
            if cur+x > cap { pieces++; cur = 0 }
            cur += x
        }
        return pieces <= k
    }
    return lo + sort.Search(hi-lo+1, func(i int) bool { return feasible(lo + i) })
}                                                   // [7 2 5 10 8], k=2 -> 18
```

A "tighter" `hi = sum / k` is wrong — nothing proves a perfectly balanced split exists (`[7 2 5 10 8]`, k=2
would return 16 instead of 18). Use a bound you can *prove* feasible.

---
<!-- /block:05_go_1_families -->

<!-- block:05_go_2_shapes -->
## Part 9 · The Problem Shapes, in Go

### Both edges of a run (LC 34)

```go
func searchRange(nums []int, target int) []int {
    lo := sort.SearchInts(nums, target)                 // first index with nums[i] >= target
    if lo == len(nums) || nums[lo] != target { return []int{-1, -1} }   // absent
    hi := sort.Search(len(nums), func(i int) bool { return nums[i] > target }) - 1
    return []int{lo, hi}                                 // [5 7 7 8 8 10], 8 -> [3 4]
}
```

`hi - lo + 1` is the count of `target` — O(log n) instead of a scan.

### Interactive oracles: the closure *is* the predicate (LC 278, 374)

There is no slice, so `sort.Search`'s "index" is just a number line. First Bad Version over versions `1..n`:

```go
func firstBadVersion(n int) int {
    return 1 + sort.Search(n, func(i int) bool { return isBadVersion(i + 1) })   // domain shifted to 1..n
}
```

Guess Number's three-way `guess` collapses to a boolean: `f(mid) = guess(mid) <= 0`. `<= 0` and `< 0` are **not**
interchangeable — an exact match (`0`) must fold into "go left or stay".

### A matrix as one sorted line (LC 74)

```go
func searchMatrix(matrix [][]int, target int) bool {
    rows, cols := len(matrix), len(matrix[0])
    i := sort.Search(rows*cols, func(i int) bool { return matrix[i/cols][i%cols] >= target })
    return i < rows*cols && matrix[i/cols][i%cols] == target
}
```

`i/cols` is the row and `i%cols` the column (integer division — no `//`). Swap them and you silently transpose,
which only fails on non-square input.

### A sorted-by-construction slice (LC 981 — Time Based Key-Value Store)

Timestamps per key are strictly increasing, so appending keeps each slice sorted for free. The latest entry `<= ts`
is the one *before* the first entry `> ts`:

```go
type entry struct { ts int; val string }
type TimeMap struct{ m map[string][]entry }

func (t *TimeMap) Set(k, v string, ts int) { t.m[k] = append(t.m[k], entry{ts, v}) }

func (t *TimeMap) Get(k string, ts int) string {
    es := t.m[k]
    i := sort.Search(len(es), func(i int) bool { return es[i].ts > ts })   // upper bound
    if i == 0 { return "" }                                                // nothing at or before ts
    return es[i-1].val
}
```

Unlike Python, `es[i-1]` with `i == 0` **panics** rather than silently wrapping to the last element — but check
`i == 0` anyway; the guard is the point. `slices.BinarySearchFunc(es, ts, func(e entry, t int) int { return cmp.Compare(e.ts, t) })`
is the same search over structs (note the comparator's argument order: element first, target second).

### Rightmost True: integer square root — and the overflow that is *not* the midpoint

```go
func mySqrt(x int) int {
    lo, hi := 0, x
    for lo < hi {
        mid := lo + (hi-lo+1)/2                     // UPPER mid
        if mid <= x/mid { lo = mid } else { hi = mid - 1 }   // mid*mid <= x, without multiplying
    }
    return lo                                        // 8 -> 2   4 -> 2   0 -> 0   10^12 -> 1000000
}
```

> ⚠️ **Written the obvious way (`mid*mid <= x`) this returns garbage in Go.** With `x = 10¹²`, `mid` reaches `10¹²`
> and `mid*mid` is `10²⁴` — far past `int64`'s 9.2×10¹⁸ — so it **wraps silently** (we measured `712602252916` instead
> of `1000000`). The midpoint was safe; the *feasibility arithmetic* overflowed. Python cannot show this bug. Divide
> (`mid <= x/mid`), or cap `hi` at `3037000499` (the largest `int64` whose square fits).

### Maximise the minimum (rightmost True): LC 1552 / Aggressive Cows

```go
lo, hi := 1, position[len(position)-1]-position[0]
for lo < hi {
    mid := lo + (hi-lo+1)/2                          // UPPER mid, because lo = mid keeps the low side
    if feasible(mid) { lo = mid } else { hi = mid - 1 }
}                                                     // [1 2 3 4 7], 3 balls -> 3
```

with `feasible(d)` greedily placing each ball at least `d` past the previous one.

### Peak finding: no sorted order, still a safe half (LC 162)

```go
func findPeak(nums []int) int {
    lo, hi := 0, len(nums)-1
    for lo < hi {
        mid := lo + (hi-lo)/2
        if nums[mid] < nums[mid+1] { lo = mid + 1 } else { hi = mid }   // rising: a peak lies right
    }
    return lo                                        // [1 2 3 1] -> 2    [1 2 1 3 5 6 4] -> 5
}
```

### A counting predicate: k-th smallest in a sorted matrix (LC 378)

Search the **value** range; `feasible(x)` is *"are there at least `k` elements `<= x`?"*, counted in O(n) with a
staircase walk. O(n · log(range)) — the pattern behind k-th smallest pair distance and k-th smallest fraction.

```go
countLE := func(x int) int {
    c, r, col := 0, n-1, 0
    for r >= 0 && col < n {
        if matrix[r][col] <= x { c += r + 1; col++ } else { r-- }
    }
    return c
}
lo, hi := matrix[0][0], matrix[n-1][n-1]
for lo < hi {
    mid := lo + (hi-lo)/2
    if countLE(mid) >= k { hi = mid } else { lo = mid + 1 }
}                                                     // [[1 5 9] [10 11 13] [12 13 15]], k=8 -> 13
```

### Rotated with duplicates (LC 154 / 81) — the log guarantee breaks

```go
switch {
case nums[mid] > nums[hi]: lo = mid + 1
case nums[mid] < nums[hi]: hi = mid
default:                   hi--                        // ambiguous: shrink, and accept O(n) worst case
}                                                       // [2 2 2 0 1] -> 0     [3 1 3] -> 1
```

### Unknown size (LC 702): gallop, then search

Double the upper bound until it passes the target, then binary-search inside `[hi/2, hi]` — O(log p) for a target
at position `p`. (Timsort's galloping mode is the same idea.)

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `sort.Search` with a non-monotone `f` | No error — a meaningless index, silently. | Test the predicate on a tiny input; state the monotonicity. |
| `sort.Search`'s domain is `[0, n)` | Off by one when the real domain is `1..n` or `lo..hi`. | Shift: `lo + sort.Search(hi-lo+1, func(i int) bool { return ok(lo+i) })`. |
| `mid*mid`, `mid*x`, `sum` inside `feasible` | Wraps silently at 64 bits — the *feasibility arithmetic* overflows even when the midpoint does not. | Divide instead of multiply, or cap the bounds. |
| `hi = mid - 1` in leftmost-True | Discards a `mid` that may be the answer. | `hi = mid`, or use `sort.Search`. |
| Lower mid with `lo = mid` | Infinite loop once `hi == lo + 1`. | Upper mid: `lo + (hi-lo+1)/2`. |
| `slices.BinarySearchFunc` argument order | The comparator gets `(element, target)`, not `(target, element)`. | `func(e entry, t int) int { return cmp.Compare(e.ts, t) }`. |
| `sort.SearchInts` on a descending slice | Wrong index, no error. | Sort ascending first, or use `sort.Search` with the flipped comparison. |

---
<!-- /block:05_go_2_shapes -->

<!-- block:05_go_3_followups -->
## Part 10 · Follow-ups the Interviewer Reaches For

| Follow-up | The answer |
|---|---|
| "Why is this O(log n)?" | Each probe discards half the candidates; `n` halves to `1` in `⌊log₂ n⌋ + 1` probes. |
| "Why not `(lo+hi)/2`?" | It can overflow (a real risk on `int32` builds and on `int64` answer ranges); `lo + (hi-lo)/2` cannot. |
| "It is a linked list." | No O(1) index — each probe costs O(n) (`container/list`). Copy to a slice, or use a skip list / balanced tree. |
| "Duplicates?" | Decide what to return (first, last, any) and use the matching bound. Rotated arrays lose the log guarantee. |
| "Real numbers." | A fixed count of iterations (~100), not `hi-lo > eps`. |
| "The data is huge / on disk." | Binary search touches `log n` pages — the reason B-trees exist; keep the top levels cached. |
| "Search many times as the data changes." | A static slice wants binary search; a changing set wants a balanced tree or a heap. |
| "Can you avoid the closure?" | `slices.BinarySearch` (values) or a hand-written loop; `sort.Search`'s closure is cheap but not free in a hot path. |

---
<!-- /block:05_go_3_followups -->

<!-- problem-map:start -->
## Part 11 · Every Problem in This Topic, by Pattern

Twelve problems in three groups — Family A (search on the data: 001–005, 007–009), Family B (search on the answer: 006, 010, 011) and one partition search (012). The Python guide's map in Go, with the Go-only traps. Topic 05's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Binary Search](GoDSA/05_binary_search/001_binary_search/solution.go) <br>LC 704 · Easy | Family A · exact match | Closed interval, `mid := lo + (hi-lo)/2`, `nums[mid] < target → lo = mid + 1`, else `hi = mid - 1`. **Trap:** `for lo < hi` drops the last candidate; `hi = mid` loops forever. |
| [002 · Search Insert Position](GoDSA/05_binary_search/002_search_insert_position/solution.go) <br>LC 35 · Easy | Leftmost True (lower bound) | `sort.SearchInts(nums, target)` *is* the answer; hand-rolled, `hi = len(nums)` (not `- 1`). **Trap:** `hi = n - 1` makes "insert at the end" unreachable; `hi = mid - 1` throws away a candidate. |
| [003 · First Bad Version](GoDSA/05_binary_search/003_first_bad_version/solution.go) <br>LC 278 · Easy | Oracle, boolean | `1 + sort.Search(n, func(i int) bool { return isBadVersion(i + 1) })` — shift the domain to `1..n`. **Trap:** calling `isBadVersion(0)`; forgetting the `+1` on the way back. |
| [004 · Guess Number Higher or Lower](GoDSA/05_binary_search/004_guess_number_higher_or_lower/solution.go) <br>LC 374 · Easy | Oracle, three-way | Turn `guess` into a boolean: `guess(mid) <= 0`, then leftmost True. **Trap:** `< 0` instead of `<= 0`. |
| [005 · Search a 2D Matrix](GoDSA/05_binary_search/005_search_a_2d_matrix/solution.go) <br>LC 74 · Medium | Virtual flat index | `sort.Search(rows*cols, …matrix[i/cols][i%cols] >= target)`; integer division and remainder decode the index. **Trap:** swapping `/` and `%` (a silent transpose that only fails on non-square input). |
| [006 · Koko Eating Bananas](GoDSA/05_binary_search/006_koko_eating_bananas/solution.go) <br>LC 875 · Medium | Family B · answer space | `1 + sort.Search(maxPile, …feasible(i+1))`; `hours += (p + k - 1) / k` is `ceil(p/k)` without floats. **Trap:** searching *indices* of `piles`; floor division; overflowing the hour total on huge inputs. |
| [007 · Find Minimum in Rotated Sorted Array](GoDSA/05_binary_search/007_find_minimum_in_rotated_sorted_array/solution.go) <br>LC 153 · Medium | Rotated · find the pivot | Compare `nums[mid]` with **`nums[hi]`**; `>` → `lo = mid + 1`, else `hi = mid`. **Trap:** comparing with `nums[lo]` (ambiguous); `hi = mid - 1`; duplicates (LC 154) need `hi--`. |
| [008 · Search in Rotated Sorted Array](GoDSA/05_binary_search/008_search_in_rotated_sorted_array/solution.go) <br>LC 33 · Medium | Rotated · search a target | Decide the sorted half by `nums[lo] <= nums[mid]`, then range-check the target. **Trap:** `<` vs `<=` at the edges. |
| [009 · Time Based Key-Value Store](GoDSA/05_binary_search/009_time_based_key_value_store/solution.go) <br>LC 981 · Medium | Sorted-by-construction slice | Per-key `[]entry` appended in time order; `sort.Search(len(es), …es[i].ts > ts)` is the upper bound; return `es[i-1]`. **Trap:** the `i == 0` guard; a single global slice instead of one per key. |
| [010 · Capacity To Ship Packages Within D Days](GoDSA/05_binary_search/010_capacity_to_ship_packages_within_d_days/solution.go) <br>LC 1011 · Medium | Family B · capacity | `lo = slices.Max(weights)`, `hi = sum`; `feasible(cap)` counts days greedily. **Trap:** `lo = 1`; forgetting the final partly loaded day. |
| [011 · Split Array Largest Sum](GoDSA/05_binary_search/011_split_array_largest_sum/solution.go) <br>LC 410 · Hard | Family B · minimise the maximum | `sort.Search(hi-lo+1, func(i int) bool { return feasible(lo + i) })` with `lo = max(nums)`, `hi = sum(nums)`. **Trap:** an unproven "tight" `hi` (`sum / k` returns 16, not 18); an unguarded greedy when one element exceeds `cap`. |
| [012 · Median of Two Sorted Arrays](GoDSA/05_binary_search/012_median_of_two_sorted_arrays/solution.go) <br>LC 4 · Hard | Search a partition | Binary-search the cut of the *shorter* slice; use `math.MinInt`/`math.MaxInt` sentinels for the empty sides. **Trap:** searching the longer slice (index panic in Go — louder than Python's silent wrap); dropping the sentinels. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Write `mid := left + (right-left)/2` reflexively and explain why, including the 32-bit vs 64-bit `int` nuance
- [ ] Explain `sort.Search`'s contract: monotonic predicate, returns smallest true index
- [ ] Build `lowerBound`/`upperBound` on top of `sort.Search` without looking them up
- [ ] Know when to reach for `slices.BinarySearch` vs `sort.SearchInts` vs raw `sort.Search`
- [ ] Solve rotated-sorted-array search by identifying the sorted half first
- [ ] Recognize "minimize/maximize a value subject to a feasibility check" as binary search on the answer space
- [ ] Justify fixed-iteration-count termination over epsilon comparison for float search
- [ ] Explain why binary search degrades to O(n) on `container/list` and why `sort.Search` only makes sense on O(1)-indexable data
- [ ] Write the rotated-array search template in under 5 minutes
- [ ] Say whether a problem is Family A or B by what `lo` and `hi` move over <!--ca-->
- [ ] Write leftmost-True and rightmost-True, and say why the latter needs the upper mid <!--ca-->
- [ ] Recognise that `mid*mid` / `mid*x` inside `feasible` can overflow even when the midpoint cannot <!--ca-->
- [ ] Shift `sort.Search`'s `[0, n)` domain onto `lo..hi` correctly <!--ca-->
- [ ] Explain why peak finding works without a sorted array, and what duplicates do to a rotated search <!--ca-->
