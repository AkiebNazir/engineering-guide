# Topic 04 · Prefix Sum — Go Deep Dive

> A prefix sum trades O(n) of one-time work for O(1) answers to "what's the sum
> of this range?" forever after. That trade is trivial in any language, but Go's
> memory model changes *how* you build the 2D version: `[][]int` is not a matrix,
> it's a slice of independently-allocated row slices, and that fact quietly
> determines whether your inner loop is fast or cache-hostile. This is the
> document that makes that decision on purpose instead of by accident.

---

## Part 1 · The 1D Prefix Sum

### 1.1 The core trick: shift the array by one

Given `nums`, define `prefix[i]` as the sum of the first `i` elements — with
`prefix[0] = 0` as a sentinel:

```go
prefix := make([]int, len(nums)+1)   // preallocate: exact size is known
for i, v := range nums {
    prefix[i+1] = prefix[i] + v
}
```

```
nums:   [ 3,  1,  4,  1,  5,  9 ]
prefix: [0,  3,  4,  8,  9,  14, 23]
         ▲   ▲               ▲
       sentinel          prefix[6] = sum of all 6 elements
```

Range sum of `nums[l..r]` inclusive is then one subtraction:

```go
sum := prefix[r+1] - prefix[l]        // O(1), no bounds juggling
```

The **length-`n+1` sentinel** is the whole point: without it, `sum(0, r)` would
need a special case (`if l == 0 { return prefix[r] }`) because there'd be no
"sum of zero elements" entry to subtract. Paying one extra `int` up front buys
away every edge case in every query. This is the same instinct as the dummy
head node in a linked list — sacrifice one slot to delete a branch.

> ✅ **Always `make([]int, n+1)` up front.** Appending in a loop (`prefix =
> append(prefix, ...)`) works but invites a reallocation Go has to grow into;
> you already know the final size, so there's no reason to let `append` guess.

### 1.2 Difference arrays — the mirror image

A prefix sum answers "sum of a range" in O(1) after O(n) build. A **difference
array** answers the opposite problem: apply O(1) *range updates*, then read the
final array once in O(n). It's the same idea run backwards.

```go
diff := make([]int, len(nums)+1)

// add `val` to every element in nums[l..r] inclusive — O(1)
addRange := func(l, r, val int) {
    diff[l] += val
    diff[r+1] -= val        // the "undo" that stops the effect after r
}

// materialize the final array — O(n), done once at the end
result := make([]int, len(nums))
running := 0
for i := range nums {
    running += diff[i]
    result[i] = nums[i] + running
}
```

```
range-add(1, 3, +5) on a zero array of length 6:

diff:   [0, +5,  0,  0, -5,  0,  0]
                              ▲
                    cancels the +5 the instant we step past index 3

running sum walk:  0, 5, 5, 5, 0, 0   → applied to nums[0..5]
```

The insight: instead of writing `+val` to every cell in `[l, r]` (O(range) per
update), you write to exactly **two** cells and let a single running-sum pass
at the end expand the effect. n range updates cost O(n) total instead of
O(n·range). This is the technique behind "apply k bookings, then report the
final state" problems (LC 370-style range addition, meeting-room-style sweep
counting).

### 1.3 Prefix XOR

The same shifting trick works for any associative, invertible operation — XOR
included, because `a ^ b ^ b = a`:

```go
px := make([]int, len(nums)+1)
for i, v := range nums {
    px[i+1] = px[i] ^ v
}
xorRange := func(l, r int) int { return px[r+1] ^ px[l] }   // O(1)
```

This is the whole trick behind "XOR of range" problems and shows up again
inside subarray-XOR-equals-K (map from prefix-XOR value → count, same shape as
the hash-map complement lookup from Topic 01).

### 1.4 Complexity

| Operation | Complexity | Note |
|---|:--:|---|
| Build `prefix` (1D) | **O(n)** | One pass |
| `sum(l, r)` after build | **O(1)** | The entire payoff |
| Brute-force range sum, no prefix | O(n) per query | What you're avoiding |
| Build `diff` + apply k updates | **O(k)** | Two writes per update |
| Materialize `diff` → final array | **O(n)** | One pass, once |
| Build 2D prefix sum | **O(rows·cols)** | One pass over the grid |
| `sumRegion` after 2D build | **O(1)** | Four array reads, one formula |

> ⚡ **The value proposition in one line:** pay O(n) once, then every query —
> and there can be up to O(q) of them — is O(1) instead of O(n). For q queries
> that's O(n + q) instead of O(n·q). This is the entire reason the pattern
> exists; if a problem does one query, don't bother building a prefix array.

---

## Part 2 · 2D Prefix Sums — Where Go's Memory Model Bites

### 2.1 `[][]int` is not a matrix — it's a slice of slices

This is the section that doesn't exist in a Python or C guide, because it's a
Go-specific consequence of Part 1's slice-header lesson from Topic 01.

In C, `int grid[rows][cols]` is one contiguous block — `rows*cols*4` bytes,
row-major, and `grid[r][c]` is pointer arithmetic into that single block. In
Go, `[][]int` is:

```go
type slice struct { array unsafe.Pointer; len, cap int }  // outer slice header
```

...where **each element of the outer slice is itself a slice header pointing
at its own, separately heap-allocated backing array**:

```go
grid := make([][]int, rows)
for r := range grid {
    grid[r] = make([]int, cols)   // A SEPARATE allocation, per row
}
```

```
grid ──► ┌──────┬──────┬──────┐
         │ hdr0 │ hdr1 │ hdr2 │   outer slice: 3 headers, contiguous
         └──┬───┴──┬───┴──┬───┘
            ▼      ▼      ▼
         [row 0] [row 1] [row 2]   ← three UNRELATED heap allocations,
                                      no guarantee they're even nearby
```

**There is no guarantee row 0's backing array is adjacent to row 1's.** The Go
allocator may place them anywhere. Walking `grid[r][c]` for fixed `r`, varying
`c` is cache-friendly (that row *is* contiguous). But walking column-major
(`grid[r][c]` for fixed `c`, varying `r`) chases a pointer to a new, possibly
distant allocation on every single step — there is no row-major/column-major
symmetry the way there sort of is in a true 2D array. This is worse than C's
column-major penalty, which at least stays within one contiguous block.

> ⚠️ **`make([][]int, rows, cols)` is a classic bug**, not an optimization —
> the third argument to `make` on a slice is capacity of the *outer* slice
> (how many rows you can `append` before reallocating), not the row length.
> You still must allocate each row separately. There's no shortcut.

### 2.2 Flattening: `data[r*cols+c]` instead of `grid[r][c]`

For large matrices or hot loops, allocate **one** backing array and compute
the index yourself:

```go
data := make([]int, rows*cols)      // ONE allocation, truly contiguous
at := func(r, c int) int { return data[r*cols+c] }
set := func(r, c, v int) { data[r*cols+c] = v }
```

```
rows=3, cols=4, flattened:

data: [ (0,0) (0,1) (0,2) (0,3) | (1,0) (1,1) (1,2) (1,3) | (2,0) (2,1) (2,2) (2,3) ]
        └──────── row 0 ────────┘└──────── row 1 ────────┘└──────── row 2 ────────┘

at(r, c) = data[r*cols + c]     — one multiply, one add, one contiguous read
```

This removes the outer indirection entirely: **one** allocation instead of
`rows+1`, one cache-line-friendly block instead of `rows` scattered ones, and
one bounds check instead of two (Go still checks `data[i]` against `len(data)`,
but there's no separate check on the outer slice). For a 1000×1000 `int`
matrix that's the difference between 1 allocation and 1001.

**When to use which:**

| Use `[][]int` when | Use flattened `[]int` when |
|---|---|
| Interview / LeetCode — readability under time pressure | Matrix is large (≥ a few hundred cells per side) |
| Rows have genuinely different lengths (jagged) | You do millions of accesses (hot path, competitive programming) |
| The problem statement hands you `[][]int` already | You control the construction and care about allocations |

> ✅ For this repo's interview-style problems, `[][]int` is the right default —
> it matches the LeetCode signature and the readability cost of `r*cols+c`
> arithmetic usually isn't worth it unless a problem's constraints (n up to
> 10⁵ per dimension, say) make allocation count or cache behavior the
> bottleneck. Know the flattened form exists and say so; don't over-engineer
> the common case.

### 2.3 Building the 2D prefix sum

Define `ps[r][c]` as the sum of the rectangle from `(0,0)` to `(r-1,c-1)`
inclusive — same one-row/one-column sentinel trick as Part 1, now in two
dimensions:

```go
rows, cols := len(matrix), len(matrix[0])
ps := make([][]int, rows+1)
for i := range ps {
    ps[i] = make([]int, cols+1)
}

for r := 1; r <= rows; r++ {
    for c := 1; c <= cols; c++ {
        ps[r][c] = matrix[r-1][c-1] +
            ps[r-1][c] +   // rectangle above
            ps[r][c-1] -   // rectangle to the left
            ps[r-1][c-1]   // subtract double-counted overlap
    }
}
```

```
                 ps[r-1][c-1] ┐
                 ┌────────────┼────────────┐
                 │  overlap   │ ps[r-1][c] │   ← added twice by the two terms
                 │ (subtract  │  (added)   │      above, so subtract it once
                 │   once)    │            │
                 ├────────────┼────────────┤
                 │ ps[r][c-1] │ matrix[r-1]│
                 │  (added)   │  [c-1]     │
                 └────────────┴────────────┘
```

This is **inclusion-exclusion**: adding the rectangle above and the rectangle
to the left double-counts their shared top-left overlap, so that overlap is
subtracted back out once.

The flattened equivalent computes the same values into one `[]int` of size
`(rows+1)*(cols+1)`, indexed via `ps[r*(cols+1)+c]` — same formula, one
allocation instead of `rows+1`.

### 2.4 Querying any rectangle in O(1)

Once `ps` is built, the sum of the rectangle from `(r1,c1)` to `(r2,c2)`
inclusive (0-indexed against the original matrix) is four lookups and the same
inclusion-exclusion formula, run in reverse:

```go
sumRegion := func(r1, c1, r2, c2 int) int {
    return ps[r2+1][c2+1] - ps[r1][c2+1] - ps[r2+1][c1] + ps[r1][c1]
}
```

```
   c1        c2
r1 ┌──────────┐
   │  target  │
r2 └──────────┘

ps[r2+1][c2+1]           = everything above-left of the bottom-right corner
- ps[r1][c2+1]            removes everything above the target rows
- ps[r2+1][c1]            removes everything left of the target columns
+ ps[r1][c1]               adds back the corner removed by BOTH subtractions
```

### 2.5 Overflow — carry the habit forward from Topic 01

Go's `int` is 64-bit on amd64/arm64 (platform-dependent per the spec — it's
whatever's fastest for the architecture, which today means 64-bit everywhere
you'll actually run this). A prefix sum over `10^5` elements each up to `10^9`
can reach `~10^14` — well inside 64-bit range, but **silently wraps** rather
than erroring if you ever *do* overflow it, exactly like the `(left+right)/2`
warning from Topic 01's Part 3. Two habits carry over directly:

- If a problem's stated bounds could plausibly exceed `~9.2×10^18` (rare, but
  competitive-programming problems sometimes push into it, especially with
  products or squared sums), declare `int64` explicitly rather than trusting
  the platform default.
- Never assume "it fit in testing" means it can't wrap on a larger judge input
  — Go won't panic on signed overflow, it'll just hand you the wrong (wrapped)
  answer.

---

## Part 3 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| 2D array | `list` of `list` — same pointer-chasing structure as Go | `[][]int` — pointer-chasing rows, **or** flatten to `[]int` |
| Contiguous 2D memory | Only via NumPy (`ndarray`) | Only via manual flattening — no stdlib equivalent |
| `itertools.accumulate` | Built-in running-sum/XOR/etc. iterator | No stdlib equivalent — write the loop yourself |
| Fixed-size preallocation | `[0]*n` is idiomatic and common | `make([]int, n)` is idiomatic and common — same instinct |
| Integer overflow | Never (arbitrary precision) | **Wraps silently** at 64 bits — carry `int64` discipline in |
| Slicing for a sub-row | `row[c1:c2]` copies O(k) | `row[c1:c2]` is an O(1) aliasing view (Topic 01, §1.2) |

Python's `list`-of-`list`s has the *identical* non-contiguity problem Go's
`[][]int` has — this is one of the few places the two languages actually agree,
because both use arrays-of-pointers-to-objects/slices for nested containers.
NumPy is the one that changes the game in Python, by giving you a true
contiguous, typed, flattenable buffer; Go has no batteries-included answer —
you flatten by hand when it matters, per §2.2.

---

## Part 4 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| 1D prefix sum + O(1) range query | O(n) build, O(1)/query | O(n) | LC 303 Range Sum Query - Immutable |
| Difference array (range update) | O(1)/update, O(n) materialize | O(n) | LC 370-style range addition |
| Prefix XOR | O(n) build, O(1)/query | O(n) | XOR of a range, subarray-XOR-K |
| Prefix sum + hash map (subarray sum = K) | O(n) | O(n) | LC 560 Subarray Sum Equals K |
| 2D prefix sum + O(1) region query | O(rows·cols) build, O(1)/query | O(rows·cols) | LC 304 Range Sum Query 2D - Immutable |
| Running total without storing full prefix array | O(n) | O(1) | Any single-query total (max subarray via Kadane, etc.) |

---

## Part 5 · Building `NumMatrix` From Scratch (LC 304)

```go
package main

// NumMatrix answers arbitrary rectangle-sum queries against an immutable
// matrix in O(1) after an O(rows*cols) one-time build.
type NumMatrix struct {
    ps [][]int // ps[r][c] = sum of matrix[0..r-1][0..c-1]; ps has one extra
               // row and column of zero sentinels, same trick as the 1D case
}

func Constructor(matrix [][]int) NumMatrix {
    rows := len(matrix)
    if rows == 0 {
        return NumMatrix{ps: [][]int{{0}}}
    }
    cols := len(matrix[0])

    ps := make([][]int, rows+1)
    for i := range ps {
        ps[i] = make([]int, cols+1) // zero-valued: row 0 and col 0 sentinels
    }

    for r := 1; r <= rows; r++ {
        for c := 1; c <= cols; c++ {
            ps[r][c] = matrix[r-1][c-1] +
                ps[r-1][c] + // rectangle strictly above (0..r-2, 0..c-1)
                ps[r][c-1] - // rectangle strictly left  (0..r-1, 0..c-2)
                ps[r-1][c-1] // their shared overlap, counted twice above
        }
    }

    return NumMatrix{ps: ps}
}

// SumRegion returns the sum of matrix[row1..row2][col1..col2] inclusive,
// 0-indexed against the ORIGINAL matrix. Four O(1) lookups, no loop.
func (m *NumMatrix) SumRegion(row1, col1, row2, col2 int) int {
    return m.ps[row2+1][col2+1] - // everything above-left of the far corner
        m.ps[row1][col2+1] - // minus everything above the target rows
        m.ps[row2+1][col1] + // minus everything left of the target columns
        m.ps[row1][col1] // plus the corner subtracted by both of the above
}
```

**Talk track while writing:** build once at construction time since the matrix
is immutable — that's the whole premise of the "Immutable" in the problem
name; the `+1` sizing on both dimensions of `ps` kills every edge case at
`row1==0` or `col1==0` the same way the 1D sentinel did in Part 1; `SumRegion`
is pure arithmetic on already-computed values, so it's O(1) regardless of how
big the queried rectangle is — that's the entire point of paying for the
build up front.

---

<!-- block:04_go_1_hashmap -->
## Part 6 · Prefix Sum + Hash Map — the Flagship Idea, in Go

Everything so far answered *"what is the sum of this range?"*. The most-asked prefix-sum problems ask the
inverse: *"which ranges have this sum?"* — and they are asked with **negative numbers allowed**, where a
sliding window (topic 03) is not legal. All code below ran on Go 1.24.5 against LeetCode's own examples.

```arch
%% caption: Turn "subarrays with sum k" into a lookup: one pass, one map. No window, so the numbers may be negative.
grid 230x100
node a "want: subarrays with sum = k" at 0,0 shape=pill
node b "sum(l..r) = P[r+1] - P[l]" at 1,0 shape=box
node c "An earlier prefix" at 2,0 shape=card icon=sigma sub="so it must equal P[r+1] - k"
node d "Scan once" at 0,1 shape=card icon=kv color=orange sub="at each r look up running - k in a map"
node e "count += seen[running - k]" at 1,1 shape=box w=220
node f "seen[running]++" at 2,1 shape=box
a -> b -> c
c:B -> d:T
d -> e -> f
```

### Variant A — count occurrences (LC 560)

```go
func subarraySum(nums []int, k int) int {
    seen := map[int]int{0: 1}        // the EMPTY prefix has been seen once — the sentinel
    running, count := 0, 0
    for _, x := range nums {
        running += x
        count += seen[running-k]     // a missing key reads 0: no comma-ok, no initialisation
        seen[running]++              // lookup FIRST, record AFTER
    }
    return count                     // ([1 1 1], 2) -> 2      ([1 2 3], 3) -> 2
}
```

Go quietly improves on Python here: `seen[running-k]` on a missing key is just `0`, and `seen[running]++` needs no
`get(…, 0) + 1` dance — the zero value does what `defaultdict(int)` does.

**The sentinel is the #1 bug.** Seed `map[int]int{0: 1}`, not `map[int]int{}`. Without it every subarray that
starts at index 0 vanishes: `[1 1 1]`, `k = 2` returns **1** instead of 2 (run it). `{0: 1}` means "the empty
prefix before index 0 has occurred once".

### Variant B — remember the *first* index (LC 525, LC 523)

When you want the **longest** span, or just existence, store the earliest index a prefix was seen and never
overwrite it. The seed changes to `{0: -1}` — the empty prefix sits *one before* index 0:

```go
func findMaxLength(nums []int) int {          // Contiguous Array: equal 0s and 1s
    first := map[int]int{0: -1}
    running, best := 0, 0
    for i, x := range nums {
        if x == 0 { running-- } else { running++ }    // map 0 -> -1, 1 -> +1
        if j, ok := first[running]; ok {              // comma-ok: index 0 is a REAL answer here
            best = max(best, i-j)
        } else {
            first[running] = i                        // only on first sight
        }
    }
    return best                                        // [0 1] -> 2     [0 1 0] -> 2
}
```

Confusing the two variants is the #2 bug: an incrementing counter where you wanted the earliest index returns a
shorter span; `if _, ok := …; !ok` (Variant B) where you wanted a count caps every bucket at 1.

### The mod-K family — and Go's `%` sign

```go
func subarraysDivByK(nums []int, k int) int {       // LC 974
    seen := map[int]int{0: 1}
    running, count := 0, 0
    for _, x := range nums {
        running += x
        rem := ((running % k) + k) % k              // ← normalise: Go's % keeps the sign of the DIVIDEND
        count += seen[rem]
        seen[rem]++
    }
    return count                                     // [4 5 0 -2 -3 1], 5 -> 7
}
```

> ⚠️ **This is a real Python-vs-Go difference.** Python's `%` returns a result with the sign of the *divisor*:
> `-7 % 5 == 3`. Go, like C and Java, gives `-7 % 5 == -2`. With negative numbers in the input a prefix can go
> negative, and `-2` and `3` are the *same* remainder class mod 5 but **different map keys**. Skip the
> `((x % k) + k) % k` fix-up and you silently split one bucket into two and undercount. Do not "fix" it with
> `abs(running) % k` — that is a different operation.

Continuous Subarray Sum (LC 523) is Variant B on remainders — existence plus a length `>= 2` condition, and `k == 0`
handled separately (a remainder of `running` itself):

```go
func checkSubarraySum(nums []int, k int) bool {
    first := map[int]int{0: -1}
    running := 0
    for i, x := range nums {
        running += x
        rem := running
        if k != 0 { rem = ((running % k) + k) % k }
        if j, ok := first[rem]; ok {
            if i-j >= 2 { return true }               // NOT > 0: single elements do not count
        } else {
            first[rem] = i                            // never overwrite the earliest index
        }
    }
    return false     // [23 2 4 6 7],6 -> true   [23 2 6 4 7],13 -> false   [0],0 -> false
}
```

### Choosing between the three tools

| Question | Numbers | Tool |
|---|---|---|
| Sum of a range, many queries | any | prefix array (Part 1) |
| Subarray sum **≥ / ≤** with a monotone rule | **non-negative** | sliding window (topic 03) |
| Subarray sum **== k**, count or longest | **any sign** | prefix sum + map (this Part) |
| Range *updates* then one read | any | difference array (Part 1.2) |
| Point updates between queries | any | Fenwick / segment tree (topic 26) |

```arch
%% caption: Choosing the prefix-sum tool. The sign of the numbers and whether the data changes decide it — not the wording of the question.
grid 260x100
node q "A question about ranges of an array" at 0,0 shape=pill
node a "Does the data change between queries?" at 0,1 shape=diamond color=amber
node f "Fenwick or segment tree" at 1,1 shape=card icon=tree color=green sub="topic 26"
node b "A range sum, or ranges WITH a sum?" at 0,2 shape=diamond color=amber
node p "Prefix array" at 1,2 shape=card icon=sigma color=green sub="P[r+1] - P[l]"
node c "Numbers all non-negative?" at 0,3 shape=diamond color=amber sub="and a monotone rule"
node w "Sliding window" at 1,3 shape=card icon=filter color=green sub="topic 03"
node h "Prefix sum + hash map" at 0,4 shape=card icon=kv color=orange sub="seed {0:1} or {0:-1}"
q -> a
a -> f : "yes"
a -> b : "no"
b -> p : "range sum"
b -> c : "ranges with property"
c -> w : "yes"
c -> h : "no, any sign"
```

---
<!-- /block:04_go_1_hashmap -->

<!-- block:04_go_2_beyond -->
## Part 7 · Beyond the Sum in Go: XOR, Kadane, Binary Search and 2D + Map

### Which aggregates can be "prefixed"?

A prefix trick needs an operation you can **undo**:

| Operation | Invertible? | O(1) range query? |
|---|---|---|
| sum, count | ✅ subtract | ✅ |
| XOR | ✅ `a ^ b ^ b == a` | ✅ |
| product | ⚠️ divide, but not through `0` | only with zero bookkeeping |
| **min / max**, gcd | ❌ | ❌ sparse table or segment tree (topic 26) |

Subarray-XOR-equals-K is the flagship with `+` swapped for `^`: `seen[px^k]` instead of `seen[running-k]`
(`[4 2 2 6 4]`, `k = 6` → 4).

### Kadane is "prefix minus the smallest earlier prefix"

```go
func maxSubArray(nums []int) int {
    best, prefix, minPrefix := math.MinInt, 0, 0
    for _, x := range nums {
        prefix += x
        best = max(best, prefix-minPrefix)     // best subarray ending here
        minPrefix = min(minPrefix, prefix)     // update AFTER using it
    }
    return best                                // [-2 1 -3 4 -1 2 1 -5 4] -> 6
}
```

### Prefix sums + binary search (all-positive input)

With positive numbers the prefix array is strictly increasing, so the shortest subarray reaching `target` from
`l` is a binary search. `slices.BinarySearch` returns the leftmost index whose value is `>=` the target — the
same as Python's `bisect_left`:

```go
prefix := make([]int, len(nums)+1)
for i, v := range nums { prefix[i+1] = prefix[i] + v }
for l := range nums {
    j, _ := slices.BinarySearch(prefix, prefix[l]+target)
    if j <= len(nums) { best = min(best, j-l) }        // (7, [2 3 1 2 4 3]) -> 2
}
```

O(n log n) — slower than the window, but it survives a static array queried many times. The identical idea picks
a random index by weight (Random Pick with Weight, topic 27).

### 2D prefix sum + hash map (LC 1074)

Fix a top row and a bottom row, collapse the columns between them into one slice of column sums, then run the
flagship on it. O(rows² · cols):

```go
func numSubmatrixSumTarget(m [][]int, target int) int {
    R, C := len(m), len(m[0])
    total := 0
    for top := 0; top < R; top++ {
        col := make([]int, C)
        for bottom := top; bottom < R; bottom++ {
            for c := 0; c < C; c++ { col[c] += m[bottom][c] }
            seen := map[int]int{0: 1}
            run := 0
            for _, x := range col {
                run += x
                total += seen[run-target]
                seen[run]++
            }
        }
    }
    return total     // [[0 1 0] [1 1 1] [0 1 0]], 0 -> 4
}
```

### The flattened 2D prefix, written out

Part 2.2 said to flatten when it matters; here is the whole thing, with the row width `cols+1` baked in (the
easy place to slip is using `cols` instead of `cols+1` as the stride):

```go
type NumMatrixFlat struct {
    ps []int
    w  int                          // stride = cols + 1
}

func NewFlat(m [][]int) NumMatrixFlat {
    R, C := len(m), len(m[0])
    w := C + 1
    ps := make([]int, (R+1)*w)      // ONE allocation
    for r := 1; r <= R; r++ {
        for c := 1; c <= C; c++ {
            ps[r*w+c] = m[r-1][c-1] + ps[(r-1)*w+c] + ps[r*w+c-1] - ps[(r-1)*w+c-1]
        }
    }
    return NumMatrixFlat{ps, w}
}

func (n NumMatrixFlat) Sum(r1, c1, r2, c2 int) int {
    w := n.w
    return n.ps[(r2+1)*w+c2+1] - n.ps[r1*w+c2+1] - n.ps[(r2+1)*w+c1] + n.ps[r1*w+c1]
}
```

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `seen := map[int]int{}` (no seed) | Subarrays starting at index 0 are missed: `[1 1 1]`, `k=2` → 1, not 2. | `map[int]int{0: 1}` (count) or `{0: -1}` (first index). |
| `running % k` with negatives | Negative remainder: `-2` and `3` become different keys. | `((running % k) + k) % k`. |
| `seen[running] = i` unconditionally in Variant B | Overwrites the earliest index → a shorter span. | `if _, ok := seen[v]; !ok { seen[v] = i }`. |
| `first[running]` without comma-ok when 0 is a legal index | Absent and "index 0" both read `0`. | `if j, ok := first[running]; ok`. |
| `make([][]int, rows, cols)` | Length `rows`, capacity `cols`; every row is `nil`. | Allocate each row: `ps[i] = make([]int, cols+1)`. |
| Stride `cols` instead of `cols+1` in a flattened prefix | Rows bleed into each other — wrong sums, no panic until the last row. | One named variable `w := cols + 1`. |
| Prefix over `10⁵` values up to `10⁹` | ~10¹⁴: fits in `int` (64-bit) but a 32-bit `int32` would wrap silently. | Keep `int`/`int64`; never `int32` for a running total. |

---
<!-- /block:04_go_2_beyond -->

<!-- problem-map:start -->
## Part 8 · Every Problem in This Topic, by Pattern

Eight problems, five moves — the Python guide's map in Go, with the Go-only traps. Topic 04's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Running Sum of 1d Array](GoDSA/04_prefix_sum/001_running_sum_of_1d_array/solution.go) <br>LC 1480 · Easy | Running total | `total += x; out[i] = total` into a preallocated `make([]int, len(nums))` (or mutate a copy). **Trap:** re-summing `nums[:i+1]` each step; mutating the caller's slice in place when a new one was expected. |
| [002 · Range Sum Query - Immutable](GoDSA/04_prefix_sum/002_range_sum_query_immutable/solution.go) <br>LC 303 · Easy | Prefix array, length n + 1 | `prefix := make([]int, n+1)`; query `prefix[r+1] - prefix[l]`; keep it in a struct built by `Constructor`. **Trap:** a length-`n` prefix (special case for `l = 0`); `prefix[right] - prefix[left]`. |
| [003 · Find Pivot Index](GoDSA/04_prefix_sum/003_find_pivot_index/solution.go) <br>LC 724 · Easy | Total − left − self | `right := total - left - nums[i]` — derive, don't re-sum. **Trap:** updating `left` before comparing; `sum(nums[:i])` inside the loop. |
| [004 · Subarray Sum Equals K](GoDSA/04_prefix_sum/004_subarray_sum_equals_k/solution.go) <br>LC 560 · Medium | Prefix + count map | `seen := map[int]int{0: 1}`; `count += seen[running-k]`; `seen[running]++` — the zero value replaces `defaultdict(int)`. **Trap:** `map[int]int{}` with no seed (returns 1 for `[1 1 1]`, `k=2`); recording before the lookup. |
| [005 · Contiguous Array](GoDSA/04_prefix_sum/005_contiguous_array/solution.go) <br>LC 525 · Medium | Prefix + first-index map | `first := map[int]int{0: -1}`; `if j, ok := first[running]; ok { best = max(best, i-j) } else { first[running] = i }`. **Trap:** comma-ok skipped (index 0 is legal); overwriting the first index. |
| [006 · Range Sum Query 2D - Immutable](GoDSA/04_prefix_sum/006_range_sum_query_2d_immutable/solution.go) <br>LC 304 · Medium | 2D prefix sum | `[][]int` of `(rows+1) × (cols+1)`, or one flat `[]int` with stride `cols+1`; four-term query. **Trap:** `make([][]int, rows, cols)` (rows stay `nil`); dropping the overlap term; a wrong stride. |
| [007 · Subarray Sums Divisible by K](GoDSA/04_prefix_sum/007_subarray_sums_divisible_by_k/solution.go) <br>LC 974 · Medium | Prefix `% k` + count map | `rem := ((running % k) + k) % k` — **Go's `%` keeps the dividend's sign**. **Trap:** no seed; unnormalised negatives split one remainder class across two keys; `abs(running) % k`. |
| [008 · Continuous Subarray Sum](GoDSA/04_prefix_sum/008_continuous_subarray_sum/solution.go) <br>LC 523 · Medium | Prefix `% k` + first index | First-index map `{0: -1}`, remainder normalised, `i - j >= 2`, `k == 0` special-cased. **Trap:** `> 0` accepts single elements; overwriting the earliest index. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain why the prefix array is length `n+1`, not `n`
- [ ] Derive `sum(l, r) = prefix[r+1] - prefix[l]` without looking it up
- [ ] Build a difference array and explain why `diff[r+1] -= val` is the "undo"
- [ ] Explain why `[][]int` in Go is not contiguous, unlike C's `int[n][m]`
- [ ] Know when to flatten to `[]int` with `data[r*cols+c]` and when not to
- [ ] Derive the 2D prefix-sum build formula via inclusion-exclusion, from a
      drawn picture, not from memory
- [ ] Derive `SumRegion` (the four-term query formula) the same way
- [ ] State why Go's `int` overflow is silent, and when to reach for `int64`
- [ ] Recognize "sum of a range, many queries" as the trigger for this pattern
      vs. brute-force O(n) per query
- [ ] Write `NumMatrix` (LC 304) end to end in under 10 minutes
- [ ] Write Subarray Sum Equals K with the `{0: 1}` seed, and say what breaks without it <!--ca-->
- [ ] Tell the count-map variant (`{0: 1}`) from the first-index variant (`{0: -1}`) and pick by the question <!--ca-->
- [ ] Normalise a remainder in Go (`((x % k) + k) % k`) and say why Python does not need to <!--ca-->
- [ ] Say which aggregates can be prefixed (sum, XOR) and which cannot (min, max, gcd) <!--ca-->
- [ ] Write the flattened 2D prefix with the correct `cols+1` stride <!--ca-->
