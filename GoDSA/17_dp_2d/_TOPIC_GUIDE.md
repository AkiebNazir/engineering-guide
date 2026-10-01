# Topic 17 · Dynamic Programming (2D) — Go Deep Dive

> A 2D DP table looks like one clean allocation. In Go it's actually N+1 separate
> allocations wearing a trench coat — one slice-of-slices header, plus one
> backing array per row. Get the allocation loop wrong and every row silently
> becomes the same row. This is the document that stops that bug, and teaches
> you when to flatten the grid instead.

---

## Part 1 · Allocating a 2D Grid — The Bug Everyone Writes Once

### 1.1 `[][]int` is not a matrix. It's a slice of slices.

Go has no native 2D array type for dynamic sizes. `[][]int` is a slice whose
elements are themselves slices — an **outer header** pointing at N **inner
headers**, each of which points at its own separately-allocated backing array.

```go
dp := make([][]int, rows)   // allocates ONLY the outer slice: rows headers,
                             // each currently {array: nil, len: 0, cap: 0}
dp[0][0] = 1                 // ⚠️ PANIC: index out of range — dp[0] is nil
```

`make([][]int, rows)` gives you `rows` empty (nil) inner slices. You must
allocate every row yourself:

```go
dp := make([][]int, rows)
for i := range dp {
    dp[i] = make([]int, cols)   // ✅ each row gets its OWN backing array
}
```

### 1.2 The classic bug: sharing one row across all of them

This compiles, runs, and produces wrong answers — no panic, no crash, just
silently corrupted state:

```go
row := make([]int, cols)
dp := make([][]int, rows)
for i := range dp {
    dp[i] = row          // ⚠️ every dp[i] is the SAME slice header,
}                         //    pointing at the SAME backing array

dp[0][0] = 1
fmt.Println(dp[1][0])    // 1 — "row 1" changed because it IS row 0
```

```
        dp ──► ┌──────┬──────┬──────┐
               │ dp[0]│ dp[1]│ dp[2]│   outer slice (3 headers)
               └──┬───┴──┬───┴──┬───┘
                  │      │      │
                  ▼      ▼      ▼
               ┌────────────────────┐
               │   ONE backing array │  ← all three headers point HERE
               └────────────────────┘
```

This is the exact same aliasing family as topic 1's sub-slice bug (§1.2) and
topic 9's backtracking-append bug — the recurring Go lesson: **a slice
assignment copies the header, never the data.** In 2D DP it shows up as row 0
and row 1 mysteriously reporting identical values.

> ✅ **The fix is always the per-row loop from §1.1.** If you ever see `dp[i] =
> someSharedSlice` instead of `dp[i] = make([]int, cols)`, stop and fix it.

### 1.3 Cache locality: `[][]int` vs. a flattened `[]int`

Because each row is a separate heap allocation, the rows are **not
guaranteed to be contiguous in memory** — row 0 and row 1 can live anywhere the
allocator put them. Traversing row-major (`for i { for j { dp[i][j] } }`) is
cache-friendly *within* a row (that backing array is contiguous) but every row
transition is a pointer dereference to a potentially distant address.

Contrast with a **flattened 1D array**, extending topic 4's 2D-prefix-sum
discussion to DP tables:

```go
data := make([]int, rows*cols)
get := func(i, j int) int      { return data[i*cols+j] }
set := func(i, j, v int)       { data[i*cols+j] = v }
```

One allocation, fully contiguous, no pointer-chasing between rows — genuinely
faster on large grids or in a hot loop evaluated many times (e.g. inside a
larger search). It reads less naturally as `dp[i][j]`, so:

**The cache-line math, made concrete.** A CPU cache line is typically 64
bytes. An `int` in Go's flattened `[]int` is 8 bytes (on a 64-bit
platform), so **one cache line holds 8 consecutive `int`s**. Row-major
traversal (`for i { for j { ... dp[i*cols+j] ... } }`) on the flattened
array touches `data[i*cols]`, `data[i*cols+1]`, ..., `data[i*cols+7]`
from a *single* cache-line fetch, then the next 8 from the next line —
each 64-byte fetch from main memory (~100+ cycles on a miss) serves 8
subsequent reads (~4 cycles each on a hit), so the amortized cost per
element approaches the hit cost, not the miss cost. Column-major access
on the same flattened array (`dp[i*cols+j]` with `j` fixed, `i` varying)
strides `cols*8` bytes between reads — if `cols` is large enough that
`cols*8` exceeds the line size (it almost always is), **every single
read is a fresh cache-line fetch**, which is why the iteration order in
§2.2 ("iteration order is the transition's dependency graph") is not
just a correctness constraint but a performance one: row-major fill order
on a row-major layout is the only combination that gets the free reads.

With `[][]int`, each row is its own heap allocation, so consecutive rows
are not guaranteed adjacent — row-major traversal is still fast *within*
a row (that backing array is contiguous, same 8-ints-per-line math
applies) but pays one additional pointer dereference (`dp[i]` — a slice
header lookup, itself likely cache-resident but a separate memory
access) at every row boundary, and offers no guarantee that `dp[i+1]`'s
backing array is anywhere near `dp[i]`'s, so a row transition **can**
be a fresh cache-line fetch even when the previous row's tail was hot.
On grids small enough to fit the working set in L1/L2 (roughly:
`rows*cols*8` bytes under 32–256 KB) this difference is noise; it only
shows up as measurable at genuinely large `rows*cols`, which is exactly
why the recommendation below is "don't bother by default."

> ⚡ **Recommendation:** use `[][]int` for interview code and most solutions —
> clarity wins and the sizes in these problems rarely justify the flattening.
> Reach for the flattened form only when profiling (or problem constraints,
> e.g. rows/cols in the thousands evaluated repeatedly) says it matters.

---

## Part 2 · The (m+1)×(n+1) Offset Trick

Nearly every 2D string-DP problem (LCS, Edit Distance, Interleaving String)
sizes its table `(m+1) × (n+1)` instead of `m × n`. Row 0 and column 0
represent the **empty prefix** of each string:

```go
dp := make([][]int, m+1)
for i := range dp {
    dp[i] = make([]int, n+1)
}
// dp[0][j] = "comparing empty s1-prefix against s2[:j]"
// dp[i][0] = "comparing s1[:i] against empty s2-prefix"
```

Without the offset, you'd need to special-case `i == 0` or `j == 0` inside the
transition to avoid indexing `dp[i-1][...]` at `i = 0` (a negative index —
`dp[-1]` is a compile-time impossibility in Go anyway, since slice indices are
`int` but bounds-checked at runtime: `dp[-1]` panics, it does not wrap like
Python's negative indexing does). The offset turns "index -1 means empty
string" into "index 0 means empty string," which is a real, valid index.

> ⚠️ **This is the single biggest source of off-by-one bugs in 2D DP.** When a
> transition reads `dp[i-1][j-1]`, ask: *if `i` and `j` are actual string
> indices (0-based), what does `i-1` mean when `i=0`?* With the +1 offset, `i`
> in the DP table represents "the first `i` characters," so `i=0` cleanly means
> "zero characters," and `dp[i-1]` is always in bounds for `i ≥ 1`.

---

## Part 3 · Space Optimization — O(rows·cols) → O(cols)

Most 2D DP transitions only ever look at the **current row** and the
**immediately previous row** (`dp[i-1][j]`, `dp[i][j-1]`, `dp[i-1][j-1]`).
That means you never need to keep more than two rows alive.

### 3.1 Two rolling 1D slices

```go
prev := make([]int, n+1)
curr := make([]int, n+1)
for i := 1; i <= m; i++ {
    curr[0] = i   // base case for this row
    for j := 1; j <= n; j++ {
        if s1[i-1] == s2[j-1] {
            curr[j] = prev[j-1] + 1
        } else {
            curr[j] = max(prev[j], curr[j-1])
        }
    }
    prev, curr = curr, prev   // swap headers — O(1), no copy
}
// answer is in prev[n] after the final swap
```

Swapping `prev, curr = curr, prev` swaps two 24-byte slice headers — the same
O(1) header-swap idiom from topic 1's tuple-assignment discussion, not a data
copy.

### 3.2 A single 1D slice — when direction of iteration matters

Some problems (0/1 knapsack is the canonical example) can go one step further
and reuse **a single row in place**, but only if you iterate the inner
dimension in the **correct direction**:

```go
dp := make([]int, capacity+1)
for i := 0; i < n; i++ {
    for w := capacity; w >= weights[i]; w-- {   // ⚠️ must go RIGHT TO LEFT
        dp[w] = max(dp[w], dp[w-weights[i]]+values[i])
    }
}
```

> ⚠️ **Get the iteration direction backwards and you silently solve the wrong
> problem.** 0/1 knapsack (each item used at most once) requires iterating `w`
> **downward** so that `dp[w-weights[i]]` still refers to *last iteration's*
> (item `i` not yet applied) value. Iterating upward turns this into the
> **unbounded** knapsack (each item reusable any number of times), because by
> the time you reach a larger `w`, `dp[w-weights[i]]` has already been updated
> to include item `i`. This is the most common silent-wrong-answer bug in
> knapsack DP, and it produces no crash — just a subtly wrong number.

---

## Part 4 · Canonical Patterns

### 4.1 Grid traversal — Unique Paths / Minimum Path Sum

`dp[i][j]` depends only on `dp[i-1][j]` (from above) and `dp[i][j-1]` (from
the left). Base case: the first row and first column can only be reached one
way (straight line), so they're seeded before the main loop, not handled with
an `if` inside it:

```go
dp := make([][]int, m)
for i := range dp {
    dp[i] = make([]int, n)
    dp[i][0] = 1               // first column: exactly one path (straight down)
}
for j := 0; j < n; j++ {
    dp[0][j] = 1                // first row: exactly one path (straight across)
}
for i := 1; i < m; i++ {
    for j := 1; j < n; j++ {
        dp[i][j] = dp[i-1][j] + dp[i][j-1]
    }
}
```

### 4.2 0/1 Knapsack — the 2D shape before you collapse it

`dp[i][w]` = best value using the first `i` items with capacity `w`:

```go
dp[i][w] = dp[i-1][w]                                  // skip item i
if weights[i-1] <= w {
    dp[i][w] = max(dp[i][w], dp[i-1][w-weights[i-1]]+values[i-1])  // take it
}
```

Collapsing this to 1D (§3.2) only works because `dp[i][*]` only ever reads
from row `i-1` — verify that property before attempting the collapse on any
new DP you write.

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

### 4.3 LCS / Edit Distance — the two-string diagonal

```go
if s1[i-1] == s2[j-1] {
    dp[i][j] = dp[i-1][j-1] + 1                         // LCS: extend the match
} else {
    dp[i][j] = max(dp[i-1][j], dp[i][j-1])              // LCS: skip a character
}
```

Edit Distance adds a third option (substitution) and a different base case
(`dp[i][0] = i`, `dp[0][j] = j` — the cost of inserting/deleting everything),
but the (m+1)×(n+1) offset and the diagonal-lookup shape are identical.

---

## Part 5 · Complexity Table

| Problem | Time | Space (naive) | Space (optimized) |
|---|:--:|:--:|:--:|
| Unique Paths / Min Path Sum | O(m·n) | O(m·n) | O(n) (one rolling row) |
| 0/1 Knapsack | O(n·W) | O(n·W) | O(W) (single 1D slice) |
| Longest Common Subsequence | O(m·n) | O(m·n) | O(min(m,n)) (two rows) |
| Edit Distance | O(m·n) | O(m·n) | O(min(m,n)) (two rows) |
| Interleaving String | O(m·n) | O(m·n) | O(n) (one rolling row) |
| Floyd–Warshall (topic 15) | O(V³) | O(V²) | — (needs the full table) |

---

## Part 6 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| 2D grid allocation | `[[0]*n for _ in range(m)]` — comprehension forces fresh rows | `make([][]T, m)` + **explicit per-row loop** — easy to forget |
| Row-sharing bug | `[[0]*n]*m` is the equivalent trap (all rows alias) | `row := make(...); dp[i] = row` in a loop — same trap, same fix |
| Negative indexing | `dp[-1]` silently wraps to the last row | `dp[-1]` is a **compile error** (constant) or **runtime panic** (variable) — no wraparound |
| Memory contiguity | `list` of `list`s — pointers to heap objects either way | `[][]int` — non-contiguous rows; a flattened `[]int` is fully contiguous |
| Swapping rolling rows | `prev, curr = curr, prev` — rebinds two names | `prev, curr = curr, prev` — swaps two slice **headers**, O(1), identical idiom |
| Tabulation default | Lists are dynamic; easy to `append` a new DP row | Must `make` the exact size upfront — no implicit growth mid-loop |

---

## Part 7 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Grid path counting | O(m·n) | O(n) | LC 62 Unique Paths, LC 64 Min Path Sum |
| 0/1 Knapsack | O(n·W) | O(W) | LC 416 Partition Equal Subset Sum |
| Unbounded Knapsack | O(n·W) | O(W) | LC 322 Coin Change (also topic 16) |
| Longest Common Subsequence | O(m·n) | O(min(m,n)) | LC 1143 |
| Edit Distance | O(m·n) | O(min(m,n)) | LC 72 |
| Interleaving String | O(m·n) | O(n) | LC 97 |
| Longest Palindromic Substring (2D) | O(n²) | O(n²) | LC 5 |

---

## Part 8 · Building Edit Distance From Scratch (LC 72)

Full table version first — clearest to write under interview pressure:

```go
func minDistance(word1, word2 string) int {
    m, n := len(word1), len(word2)
    dp := make([][]int, m+1)
    for i := range dp {
        dp[i] = make([]int, n+1)
        dp[i][0] = i          // delete all i characters of word1
    }
    for j := 0; j <= n; j++ {
        dp[0][j] = j          // insert all j characters of word2
    }

    for i := 1; i <= m; i++ {
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                dp[i][j] = dp[i-1][j-1]              // characters match, no op needed
            } else {
                dp[i][j] = 1 + min3(
                    dp[i-1][j-1], // substitute
                    dp[i-1][j],   // delete from word1
                    dp[i][j-1],   // insert into word1
                )
            }
        }
    }
    return dp[m][n]
}

func min3(a, b, c int) int {
    return min(a, min(b, c))   // Go 1.21+ builtin min
}
```

Now the space-optimized version — same recurrence, two rolling rows instead of
`m+1` full rows, since row `i` only ever reads row `i-1`:

```go
func minDistanceOptimized(word1, word2 string) int {
    m, n := len(word1), len(word2)
    prev := make([]int, n+1)
    curr := make([]int, n+1)
    for j := 0; j <= n; j++ {
        prev[j] = j            // row 0 base case
    }

    for i := 1; i <= m; i++ {
        curr[0] = i             // column 0 base case for this row
        for j := 1; j <= n; j++ {
            if word1[i-1] == word2[j-1] {
                curr[j] = prev[j-1]
            } else {
                curr[j] = 1 + min3(prev[j-1], prev[j], curr[j-1])
            }
        }
        prev, curr = curr, prev   // O(1) header swap, not a copy
    }
    return prev[n]                // last real write ended up in prev after the swap
}
```

**Talk track while writing:** size the table `(m+1)×(n+1)` so index 0 means
"empty prefix" and every `dp[i-1]`/`dp[j-1]` lookup stays in bounds; seed row 0
and column 0 as the cost of pure insertions/deletions; the diagonal branch is
a free move when characters match; once it works, note aloud that row `i` only
reads row `i-1`, which is the license to collapse to two rolling slices.

---

## Part 9 · Bitmask DP — a fifth shape, for "which SUBSET have I used"

None of Parts 1–8's shapes fit a problem where the state is "which of up
to ~20 elements have I already used/visited" — the subset count is
exponential, but that's exactly what makes it tractable: a subset of up
to ~20 items fits in one machine integer (Go's `int` is 64-bit on every
platform this curriculum targets), turning "which subset" into an O(1)
array index instead of an intractable dimension.

### 9.1 Representation and the exact complexity bound

```go
n := 4
fullMask := (1 << n) - 1                 // 0b1111 — every element included

isIn := func(mask, i int) bool { return mask&(1<<i) != 0 }
add := func(mask, i int) int   { return mask | (1 << i) }
popcount := bits.OnesCount(uint(mask))   // math/bits — compiles to a POPCNT instruction
```

`dp[mask][i]` (Held–Karp's TSP shape — "visited exactly `mask`, currently
at city `i`") has `2^n * n` states, each with up to `n` transitions:
**`O(2^n * n^2)` time, `O(2^n * n)` space.** For `n=15`: brute-force
permutations is `15! ≈ 1.3*10^12`; Held–Karp is `2^15 * 15^2 ≈ 7.4*10^6`
— roughly five orders of magnitude fewer operations, though still
exponential, which caps this technique at `n` ≈ 20–22 in practice.
**`n ≤ ~20` in the constraints is itself the tell** for this shape — as
reliable a signal as "sorted array" is for binary search.

### 9.2 Held–Karp TSP, idiomatic Go

```go
func tsp(dist [][]int) int {
	n := len(dist)
	const INF = math.MaxInt32
	size := 1 << n
	dp := make([][]int, size)
	for i := range dp {
		dp[i] = make([]int, n)
		for j := range dp[i] {
			dp[i][j] = INF
		}
	}
	dp[1][0] = 0 // start at city 0, mask = {0} = 0b1

	for mask := 0; mask < size; mask++ {
		for i := 0; i < n; i++ {
			if dp[mask][i] == INF || mask&(1<<i) == 0 {
				continue
			}
			for j := 0; j < n; j++ {
				if mask&(1<<j) != 0 {
					continue // j already visited
				}
				newMask := mask | (1 << j)
				if newCost := dp[mask][i] + dist[i][j]; newCost < dp[newMask][j] {
					dp[newMask][j] = newCost
				}
			}
		}
	}

	full := size - 1
	best := INF
	for i := 0; i < n; i++ {
		if cost := dp[full][i] + dist[i][0]; cost < best {
			best = cost
		}
	}
	return best
}
```

Fill order is simply increasing `mask`: every transition moves from
`mask` to a strictly larger one (`popcount` strictly increases, since `j`
was, by construction, absent from `mask`), so ascending-`mask` iteration
guarantees every source state is finalized before it's read — the
bitmask analogue of §2.2's "iteration order is the transition's
dependency graph."

### 9.3 Submask enumeration — the `(sub-1)&mask` trick

When a transition needs to split a mask into two disjoint pieces (e.g.
"partition this set of jobs between two workers, minimize the max
load"), iterate every subset of `mask`:

```go
for sub := mask; sub > 0; sub = (sub - 1) & mask {
    // process sub, a non-empty subset of mask
}
// handle the empty subset separately if the problem needs it
```

`sub - 1` flips the lowest set bit and sets every bit below it; `& mask`
clamps back to a genuine subset. Total work across every mask's subset
enumeration is `O(3^n)` (each bit independently: absent from mask,
present in mask but absent from submask, or present in both — three
choices per bit) — worth having cold as the point this technique stops
being practical (`3^20 ≈ 3.5*10^9`), well before plain bitmask DP's
`2^n` ceiling.

### 9.4 Go-specific: `math/bits` over hand-rolled popcount

```go
import "math/bits"

popcount := bits.OnesCount(uint(mask))   // compiles to a single POPCNT instruction
                                          // on any target that has one — faster and
                                          // clearer than bin(mask).count("1")'s Go
                                          // equivalent (a manual loop-and-shift)
```

Python's `int.bit_count()` (3.10+) and Go's `bits.OnesCount` are the
same operation; reach for the stdlib one in both languages rather than
hand-rolling a Brian Kernighan loop unless the interviewer specifically
wants the bit-trick explained.

---

<!-- block:17_go_1_problems -->
## Part 10 · The Eighteen Problems in Go, Shape by Shape

Parts 1–9 give the Go mechanics (allocating grids, the `(m+1)×(n+1)` offset, rolling rows, bitmask DP). This Part is
the catalogue of problems with Go code, grouped by shape. All snippets ran on Go 1.24.5 against LeetCode's own examples.

```arch
%% caption: Choosing the 2D shape. What the two indices range over decides the table, its fill order and whether it can be rolled.
grid 200x80
node q "A 2D DP problem" at 0,2 shape=pill
node a "What are the two indices?" at 0,3 shape=diamond color=amber
node g "Grid DP" at 1,0 color=green w=400 sub="a row and a column of a GRID · Unique Paths, Min Path Sum, Maximal Square"
node s "Two-string DP" at 1,1 color=green w=400 sub="a position in EACH of two strings · LCS, Edit Distance, Interleaving, Regex"
node m "State machine" at 1,2 color=green w=400 sub="a day and a STATE · Stock with Cooldown"
node k "Knapsack, rolled to 1D" at 1,3 color=amber w=400 sub="an item count and a SUM · Coin Change II (up), Target Sum (down)"
node i "Interval DP, fill by LENGTH" at 1,4 color=amber w=400 sub="a range [l, r] · Burst Balloons, Palindromic Subsequence"
node b "Bitmask / state-space BFS" at 1,5 color=green w=400 sub="a node and a SET of nodes · Visiting All Nodes"
node d "Digit DP" at 1,6 color=green w=400 sub="a digit position and a TIGHT flag · Count Special Integers"
q -> a
a:R -> g:L
a:R -> s:L
a:R -> m:L
a:R -> k:L
a:R -> i:L
a:R -> b:L
a:R -> d:L
```

### Grid shapes: Unique Paths I/II, Minimum Path Sum, Maximal Square

A cell is reachable only from above or from the left. One **rolling row** is enough: before you update `row[j]` it still
holds the value from *above*, and `row[j-1]` is the *new* value from the left — so `row[j] += row[j-1]` is the whole
recurrence:

```go
row := make([]int, n)
for j := range row { row[j] = 1 }                    // the top row: one way to each cell (NOT 0)
for i := 1; i < m; i++ { for j := 1; j < n; j++ { row[j] += row[j-1] } }    // (3, 7) -> 28   (3, 2) -> 3
```

**Obstacles** force a cell to `0` and break 001's "first row and column are all 1s" — seed `row[0]` from the *start cell*
(`if g[0][0] == 0 { row[0] = 1 }`) and let the obstacle rule do the rest. **Minimum Path Sum** changes the combinator to
`g[i][j] + min(up, left)`, and the first row/column are **cumulative** sums, not copies (`[[1 3 1] [1 5 1] [4 2 1]]` → 7).
**Maximal Square** is `1 + min(up, left, diagonal)` — `min`, not `max`, and the diagonal is what makes it a *square*:

```go
dp := make([][]int, R+1)                              // the (R+1) x (C+1) offset: row 0 / column 0 are free zeros
...
if m[i-1][j-1] == '1' { dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]); side = max(side, dp[i][j]) }
return side * side                                     // the LeetCode grid -> 4
```

### Two-string shapes: LCS, Edit Distance, Interleaving, Distinct Subsequences, Regex

`dp[i][j]` indexes **prefix lengths** (so `0` is the empty prefix), which means the characters being compared are
`a[i-1]` and `b[j-1]` — comparing `a[i]` with `b[j]` is the classic off-by-one. LCS, with reconstruction by walking back
from the corner:

```go
if a[i-1] == b[j-1] { dp[i][j] = dp[i-1][j-1] + 1 } else { dp[i][j] = max(dp[i-1][j], dp[i][j-1]) }
// walk back: match -> diagonal; else follow the larger neighbour;  "abcde","ace" -> 3 "ace"   "AGGTAB","GXTXAYB" -> 4 "GTAB"
```

Longest common *substring* is the same table with a **mismatch resetting to 0**. Edit Distance is in Part 8 — a match costs
`dp[i-1][j-1]` with **no** `+1`, and the rolling-row version must save the diagonal before overwriting it.

**Interleaving String:** the third index is *always* `i + j` — not a free dimension — and the two sources combine with **OR**:

```go
dp[j] = (dp[j] && s1[i-1] == s3[i+j-1]) || (dp[j-1] && s2[j-1] == s3[i+j-1])     // one row is enough
```

Check `len(s1)+len(s2) == len(s3)` first. **Distinct Subsequences** *counts*, so when characters match you **add** "use it" and
"skip it" (they are different subsequences), never `max`; scan `j` **downward** in the rolled row so `dp[j-1]` is still last
row's value:

```go
if s[i-1] == t[j-1] { dp[j] += dp[j-1] }              // dp[j] already holds "skip it"; "rabbbit"/"rabbit" -> 3
```

**Regular Expression Matching** cases on the last pattern character. `*` means *zero or more of the previous element*:
zero occurrences is `dp[i][j-2]`; one more is `dp[i-1][j]` (**not** `dp[i-1][j-2]`, which would cap `*` at one extra
character) — and only if `p[j-2]` is `.` or equals `s[i-1]`. Seed `dp[0][j]` for `a*b*` patterns matching the empty string:

```go
if p[j-1] == '*' {
    dp[i][j] = dp[i][j-2]
    if p[j-2] == '.' || p[j-2] == s[i-1] { dp[i][j] = dp[i][j] || dp[i-1][j] }
} else if p[j-1] == '.' || p[j-1] == s[i-1] { dp[i][j] = dp[i-1][j-1] }
```

### State machine: Best Time to Buy and Sell Stock with Cooldown

Three states — *held*, *just sold*, *resting* — and every right-hand side must read **yesterday's** values; Go's tuple
assignment does exactly that:

```go
held, sold, rest = max(held, rest-p), held+p, max(rest, sold)     // buy comes from REST, never from sold (that is the cooldown)
```

Seed `held` with `math.MinInt / 2` (headroom, so `held + p` cannot overflow). `[1 2 3 0 2]` → 3.

### Knapsack, rolled to one dimension: Coin Change II vs Target Sum

The **direction** of the inner loop is the difference. **Coin Change II** (coins reusable; combinations) has coins outermost
and amounts **ascending**; **Target Sum** is 0/1 — each number once — so it scans **descending**:

```go
for _, c := range coins { for a := c; a <= amount; a++ { dp[a] += dp[a-c] } }      // unbounded: UP.  (5,[1 2 5]) -> 4
want := (total + target) / 2                                                         // reframe: a positive subset P
for _, x := range nums { for s := want; s >= x; s-- { dp[s] += dp[s-x] } }           // 0/1: DOWN.       ([1 1 1 1 1], 3) -> 5
```

Guard `(total + target)` odd and `|target| > total` before computing `want` — otherwise you size a negative or fractional
array. Looping amounts outermost in Coin Change II counts *sequences*; scanning up in Target Sum reuses a number.

### Memoised DFS on a grid: Longest Increasing Path

Neither row-by-row nor column-by-column is a valid order, so memoise a DFS. The path is **strictly** increasing, so it can
never revisit a cell — no `visited` set is needed (adding one only invites bugs). `0` is a safe "not computed" sentinel
because every real answer is at least 1:

```go
if m[nr][nc] > m[r][c] { best = max(best, 1+dfs(nr, nc)) }         // '>' not '>=': plateaus are not "increasing"
```

`[[9 9 4] [6 6 8] [2 1 1]]` → 4 and `[[3 4 5] [3 2 6] [2 2 1]]` → 4.

### Interval DP: Burst Balloons and Longest Palindromic Subsequence

Fill by **increasing length** and try every split. Burst Balloons thinks about the balloon burst **last** in `(l, r)` — so
the two sides are independent — and pads the array with a virtual `1` at each end:

```go
p := append(append([]int{1}, nums...), 1)
for length := 2; length < n; length++ { for l := 0; l+length < n; l++ {
    r := l + length
    for k := l + 1; k < r; k++ { dp[l][r] = max(dp[l][r], dp[l][k]+p[l]*p[k]*p[r]+dp[k][r]) }
} }                                                   // [3 1 5 8] -> 167
```

Reasoning about the *first* burst leaves order-dependent neighbours that do not decompose. **Longest Palindromic Subsequence**
fills `i` **descending** (`dp[i+1][j-1]` must already exist): `dp[i][j] = dp[i+1][j-1] + 2` on matching ends, else
`max(dp[i+1][j], dp[i][j-1])`, `dp[i][i] = 1`. Ascending `i` reads cells not yet computed; solving the *substring* problem
gives 3 instead of 4 on `"bbbab"`.

### State-space BFS: Shortest Path Visiting All Nodes

The search runs over **states** `(node, mask)`, not nodes — revisiting a node is fine, revisiting a *state* never helps — and
starts from **every** node at once (the walk may begin anywhere):

```go
for i := range seen { seen[i] = make([]bool, 1<<n); seen[i][1<<i] = true; q = append(q, st{i, 1 << i, 0}) }
...
if !seen[nb][nm] { seen[nb][nm] = true; q = append(q, st{nb, nm, cur.d + 1}) }      // done when mask == 1<<n - 1
```

Keying `seen` by node alone fails the first example; starting only at node 0 misses shorter walks. Both examples → 4.

### Digit DP: Numbers At Most N Given Digit Set, Count Special Integers

Build numbers from the most significant digit while a **`tight`** flag says "the prefix still equals `n`'s prefix". For the
digit-set problem, count *shorter* lengths (`D^L`, all below `n`), then walk `n` counting smaller-digit choices per
position — stopping if `n`'s digit is not in the set — and add **1** for `n` itself:

```go
for l := 1; l < len(s); l++ { res += pow(D, l) }                 // every shorter number is < n
... per position: res += smaller * pow(D, len(s)-i-1);  if !hasSame { return res } ...
return res + 1                                                    // n itself.  ["1","3","5","7"], 100 -> 20
```

Forgetting the `+1`, or the shorter lengths, are the two classic misses (`["7"]`, `7` returns 0). **Count Special Integers**
(distinct digits) adds a `mask` of used digits and a **`started`** flag so leading zeros are free padding rather than "used"
digits — without it `n = 100` gives 72 instead of 90. The memo key is `(pos, mask, tight, started)`; a struct of those four is a
valid `map` key in Go:

```go
type key struct { pos, mask int; tight, started bool }          // comparable struct = free composite key
```

`countSpecialNumbers(20) = 19`, `(135) = 110`, `(100) = 90`.

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `dp := make([][]int, m)` then `dp[i][j]` | Every row is `nil` — **panic**. | Allocate each row in a loop (or one flat slice). |
| One row slice shared across all rows | Every row aliases; writes bleed everywhere. | `make` a fresh row per iteration. |
| `a[i]` vs `a[i-1]` in prefix-length tables | Off-by-one, often only failing on edge cases. | Say "prefix length" aloud; compare `a[i-1]`, `b[j-1]`. |
| Rolling one row and overwriting the diagonal | The diagonal `dp[i-1][j-1]` is gone. | Save `prev := dp[j]` before the write. |
| `math.MinInt` / `math.MaxInt` as `-inf` / `+inf` | `+ p` wraps. | `math.MinInt / 2`. |
| `math.Pow` for integer powers | A `float64` — precision loss for large results. | An integer loop (or `1 << k` for base 2). |
| Recursing 10⁶ deep for a memo DFS | Fatal `stack overflow` (1 GB), unrecoverable. | Iterate in a dependency order, or cap the depth. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Return the path / subsequence." | Keep the full table and walk back from the corner. |
| "Reduce the space." | Rolling rows — only when you need the value, not the path. |
| "Huge strings." | Hirschberg's divide-and-conquer recovers an LCS in linear space. |
| "Weighted operations?" | Per-operation costs in the `min`. |
| "Why O(n³)?" | Interval DP: O(n²) states × an O(n) split. |
| "Parallelise?" | Anti-diagonals of an LCS/edit table are independent — a wavefront. |

---
<!-- /block:17_go_1_problems -->

<!-- problem-map:start -->
## Part 11 · Every Problem in This Topic, by Pattern

Eighteen problems, six shapes (grid position · two strings · day × state · knapsack-as-2D · interval · bitmask/digit) — the Python guide's map in Go, with the Go-only traps. Topic 17's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Unique Paths](GoDSA/17_dp_2d/001_unique_paths/solution.go) <br>LC 62 · Medium | Grid: sum of two predecessors | One rolling `row []int` seeded with 1s; `row[j] += row[j-1]`. **Trap:** seeding 0; an `m × m` table; `make([][]int, m)` without allocating rows (panic). |
| [002 · Unique Paths II](GoDSA/17_dp_2d/002_unique_paths_ii/solution.go) <br>LC 63 · Medium | Grid with an obstacle override | Seed `row[0]` from the *start cell*; an obstacle sets `row[j] = 0`. **Trap:** the "first row is all 1s" assumption; ignoring a blocked start. |
| [003 · Minimum Path Sum](GoDSA/17_dp_2d/003_minimum_path_sum/solution.go) <br>LC 64 · Medium | Grid: min of two, plus own cost | `g[i][j] + min(dp[j], dp[j-1])`; the first row/column are cumulative. **Trap:** summing predecessors; copying the first row/column. |
| [004 · Maximal Square](GoDSA/17_dp_2d/004_maximal_square/solution.go) <br>LC 221 · Medium | Grid: side of the square ending here | `(R+1) × (C+1)` offset table; `1 + min(up, left, diag)`. **Trap:** `max`; dropping the diagonal; returning the side, not `side * side`. |
| [005 · Longest Common Subsequence](GoDSA/17_dp_2d/005_longest_common_subsequence/solution.go) <br>LC 1143 · Medium | Two strings: LCS | Prefix-length table; compare `a[i-1]`, `b[j-1]`; walk back for the string. **Trap:** `a[i]` vs `b[j]`; substring vs subsequence. |
| [006 · Best Time to Buy and Sell Stock with Cooldown](GoDSA/17_dp_2d/006_best_time_to_buy_and_sell_stock_with_cooldown/solution.go) <br>LC 309 · Medium | Day × state machine | `held, sold, rest = max(held, rest-p), held+p, max(rest, sold)`. **Trap:** buying from `sold`; `math.MinInt` overflow on `held + p`. |
| [007 · Coin Change II](GoDSA/17_dp_2d/007_coin_change_ii/solution.go) <br>LC 518 · Medium | Unbounded knapsack, combinations | Coins outermost, `for a := c; a <= amount; a++`. **Trap:** amounts outermost (sequences); scanning downward (0/1). |
| [008 · Target Sum](GoDSA/17_dp_2d/008_target_sum/solution.go) <br>LC 494 · Medium | 0/1 knapsack via a reframe | `want := (total+target)/2`; `for s := want; s >= x; s--`; guard odd/`\|target\| > total`. **Trap:** scanning upward; a negative array size. |
| [009 · Interleaving String](GoDSA/17_dp_2d/009_interleaving_string/solution.go) <br>LC 97 · Medium | Two strings, interleaving | One `dp []bool` row; `k` is always `i+j`; `\|\|` between the two sources. **Trap:** a third dimension; `&&`. |
| [010 · Edit Distance](GoDSA/17_dp_2d/010_edit_distance/solution.go) <br>LC 72 · Medium | Two strings, edit distance | Match → diagonal (no `+1`); else `1 + min(...)`. **Trap:** `+1` on a match; overwriting the diagonal in the rolling row. |
| [011 · Longest Increasing Path in a Matrix](GoDSA/17_dp_2d/011_longest_increasing_path_in_a_matrix/solution.go) <br>LC 329 · Hard | Memoised DFS on a grid | `memo[r][c]` with `0` as "not computed"; `>` only. **Trap:** `>=`; a `visited` set. |
| [012 · Distinct Subsequences](GoDSA/17_dp_2d/012_distinct_subsequences/solution.go) <br>LC 115 · Hard | Two strings, counting | `dp[j] += dp[j-1]` on a match, `j` downward in the rolled row. **Trap:** `max`; scanning `j` upward (uses this row's value). |
| [013 · Burst Balloons](GoDSA/17_dp_2d/013_burst_balloons/solution.go) <br>LC 312 · Hard | Interval DP: the *last* balloon | Pad with `1`s; fill by length; `k` is the last burst. **Trap:** the *first*-burst view; no padding. |
| [014 · Regular Expression Matching](GoDSA/17_dp_2d/014_regular_expression_matching/solution.go) <br>LC 10 · Hard | Two strings, pattern-driven | `*` → `dp[i][j-2]` or (`dp[i-1][j]` if the previous element matches). **Trap:** no zero branch; `dp[i-1][j-2]`. |
| [015 · Longest Palindromic Subsequence](GoDSA/17_dp_2d/015_longest_palindromic_subsequence/solution.go) <br>LC 516 · Medium | Interval DP on a string | `i` **descending**; `dp[i][i] = 1`; `+2` on matching ends. **Trap:** ascending `i`; the substring problem. |
| [016 · Shortest Path Visiting All Nodes](GoDSA/17_dp_2d/016_shortest_path_visiting_all_nodes/solution.go) <br>LC 847 · Hard | BFS over `(node, mask)` | `seen[node][mask]`, seeded from every node. **Trap:** `seen` by node alone; one source. |
| [017 · Numbers At Most N Given Digit Set](GoDSA/17_dp_2d/017_numbers_at_most_n_given_digit_set/solution.go) <br>LC 902 · Hard | Digit DP: shorter, then same length | `D^L` per shorter length; walk `n` with a smaller-digit count; `+1`. **Trap:** forgetting `n` itself or the shorter lengths; `math.Pow` precision. |
| [018 · Count Special Integers](GoDSA/17_dp_2d/018_count_special_integers/solution.go) <br>LC 2376 · Hard | Digit DP with a used-digit mask | `map[key]int` with a comparable struct key `(pos, mask, tight, started)`. **Trap:** no `started` flag (`100` → 72); `0` as the first digit. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Allocate every row of a `[][]int` explicitly — never share one row slice across `dp[i]`
- [ ] Explain why `[][]int` rows are non-contiguous, and when a flattened `[]int` is worth it
- [ ] Use the `(m+1)×(n+1)` offset trick and explain what index 0 represents
- [ ] Collapse O(m·n) space to O(n) with two rolling slices when row `i` only reads row `i-1`
- [ ] Know why 0/1 knapsack's inner loop must iterate `w` downward, and what breaks if it doesn't
- [ ] Write Edit Distance or LCS both as a full table and as the space-optimized rolling version
- [ ] Verify a Python DP port doesn't rely on negative-index wraparound (`dp[-1]`) — Go panics instead
- [ ] Recognize `n ≤ ~20` as the bitmask-DP tell and state Held-Karp's O(2^n · n^2) bound
- [ ] Write the `(sub-1)&mask` submask-enumeration loop and state its O(3^n) total cost
- [ ] State prefix-length indexing aloud and compare `a[i-1]` with `b[j-1]` <!--ca-->
- [ ] Roll a grid DP into one row (`row[j] += row[j-1]`) and explain what each side holds <!--ca-->
- [ ] Scan a knapsack up (unbounded) or down (0/1) and say why, with the Coin Change II / Target Sum contrast <!--ca-->
- [ ] Fill an interval DP by length (or `i` descending) and pad Burst Balloons <!--ca-->
- [ ] Use a comparable struct as a memo key for digit DP, with the `started` flag <!--ca-->
