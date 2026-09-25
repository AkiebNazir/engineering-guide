# Topic 24 · Matrix — Go Deep Dive

> A `[][]int` looks like a grid. It is not one. It is a slice of row headers, each pointing at its own separately allocated
> row — nothing in the type promises the rows sit next to each other (in practice rows allocated back to back usually do; the
> measurement in Part 9.1 shows what that does and does not cost). Every algorithm in this topic — transpose, rotate, spiral, flood-fill —
> either works around that fact or pays for ignoring it.

---

## Part 1 · `[][]int` Is Not a 2D Array

### 1.1 The layout, drawn

Topics 4 and 17 touched this in passing for prefix sums and <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> tables. Here it's
the main event.

```go
grid := make([][]int, 3)
for i := range grid {
    grid[i] = make([]int, 4)
}
```

```
   grid ──► ┌──────────┬──────────┬──────────┐
            │ ptr len  │ ptr len  │ ptr len  │   outer slice: 3 row-headers,
            │ cap      │ cap      │ cap      │   contiguous (24 bytes each)
            └────┬─────┴────┬─────┴────┬─────┘
                 │          │          │
                 ▼          ▼          ▼
            ┌─────────┐┌─────────┐┌─────────┐
            │0 0 0 0  ││0 0 0 0  ││0 0 0 0  │  ← three SEPARATE heap
            └─────────┘└─────────┘└─────────┘    allocations, unrelated
              row 0        row 1       row 2      addresses, no guarantee
                                                   they're even nearby
```

The outer slice is one contiguous block of 3-word row headers. Each row's data
is its **own** `runtime.mallocgc` call. Nothing here promises row 1 lives next
to row 0 in memory — the allocator is free to put them anywhere, and after a few rounds
of <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr> and reallocation elsewhere in the program, it may.

Compare to a **flattened** representation:

```go
data := make([]int, rows*cols)   // ONE allocation
at := func(r, c int) int { return r*cols + c }

data[at(1, 2)] = 5
```

`data` is one contiguous block, and the layout *guarantee* is real: a `[][]int` gives you no promise about where row 1 lives relative to row 0.
What the guarantee is *worth* is a different question — measured in Part 9.1, and smaller than folklore suggests.

> ⚡ **`[][]int` is fine for almost every interview problem.** Measured on a 4096 × 4096 grid (134 MB) built with one `make` per row, a
> row-major sweep took the same time over `[][]int` and over a flat `[]int` (3.8 ms both); the thing that changed the running time was the
> **traversal order** — the column-major sweep took 46 ms, about 12× slower, again identically for both layouts. Default to `[][]int`; get the loop order
> right (rows outermost); reach for `data[r*cols+c]` when you want a single allocation, not because you expect a speed-up.

### 1.2 Building a fresh grid — the same aliasing bug, in a new house

Topic 17 flagged this for <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> tables; it bites just as hard when a matrix
problem asks you to *construct* output, not just read input.

```go
// ⚠️ WRONG — leaves every row nil, or worse, shares one row
grid := make([][]int, rows)
// grid[0], grid[1], ... are all nil right now. make([][]int, rows) only
// allocates the OUTER slice of row-pointers.

row := make([]int, cols)
grid := make([][]int, rows)
for i := range grid {
    grid[i] = row              // ⚠️ every row IS row — same backing array
}
grid[0][0] = 1                 // grid[1][0], grid[2][0]... all become 1 too
```

```go
// ✅ CORRECT — allocate each row independently
grid := make([][]int, rows)
for i := range grid {
    grid[i] = make([]int, cols)   // a fresh, independent backing array per row
}
```

There is no shortcut here. Go has no `[][]int` literal-fill convenience the way
Python's (broken, for the same reason) `[[0]*cols]*rows` looks like a shortcut.
Write the loop.

---

## Part 2 · In-Place Transforms

### 2.1 Transpose — swap the upper triangle, not the whole grid

```go
func transpose(m [][]int) {
    n := len(m)
    for i := 0; i < n; i++ {
        for j := i + 1; j < n; j++ {   // j starts at i+1, NOT 0
            m[i][j], m[j][i] = m[j][i], m[i][j]
        }
    }
}
```

> ⚠️ **The classic off-by-one: `j := 0` instead of `j := i+1`.** Loop over the
> *full* grid and you swap `(i,j)` with `(j,i)`, then later swap `(j,i)` with
> `(i,j)` again when the outer loop reaches row `j` — netting zero change. Only
> the upper triangle (`j > i`) may be visited, and each swap must use Go's
> tuple-assignment idiom (`a, b = b, a`) so both values are read before either write lands.

### 2.2 Rotate 90° — transpose, then reverse each row

```
1 2 3        1 4 7        7 4 1
4 5 6  ──►   2 5 8   ──►  8 5 2      (transpose)      (reverse each row)
7 8 9        3 6 9        9 6 3
```

```go
func rotate(m [][]int) {
    transpose(m)
    for i := range m {
        row := m[i]
        for l, r := 0, len(row)-1; l < r; l, r = l+1, r-1 {
            row[l], row[r] = row[r], row[l]
        }
    }
}
```

"In place" means **O(1) extra space**, not "nothing is mutated" — every element
of `m` is overwritten. Rotating the other direction (counter-clockwise) swaps the roles: reverse each row *first*, then
transpose — or, equivalently, transpose and then reverse the **order of the rows**. Reversing the row order *before* transposing gives a clockwise
rotation again, so the recipes are easy to mix up — trace a 2×2 example (or the table in Part 9.4) rather than memorizing them.

---

## Part 3 · Traversal Orders

### 3.1 Spiral — four shrinking boundaries

```go
func spiralOrder(m [][]int) []int {
    if len(m) == 0 || len(m[0]) == 0 {
        return nil
    }
    top, bottom := 0, len(m)-1
    left, right := 0, len(m[0])-1
    result := make([]int, 0, len(m)*len(m[0]))

    for top <= bottom && left <= right {
        for c := left; c <= right; c++ {
            result = append(result, m[top][c])
        }
        top++
        for r := top; r <= bottom; r++ {
            result = append(result, m[r][right])
        }
        right--

        // ⚠️ re-check bounds here — a single remaining row or column
        // must not be walked twice (once left-to-right above, once
        // right-to-left below).
        if top <= bottom {
            for c := right; c >= left; c-- {
                result = append(result, m[bottom][c])
            }
            bottom--
        }
        if left <= right {
            for r := bottom; r >= top; r-- {
                result = append(result, m[r][left])
            }
            left++
        }
    }
    return result
}
```

The two guard checks (`if top <= bottom`, `if left <= right`) right before the
third and fourth passes are the whole difficulty of this problem. Without them,
a single-row or single-column remainder gets traversed twice — once going
right-to-left along what's now a degenerate "bottom" row that's the same as
the top row already emitted. Trace a 1×n and an n×1 input by hand once; the
need for the guards becomes obvious.

```arch
%% caption: Spiral traversal: four shrinking boundaries. The two inner checks stop a single leftover row or column from being walked twice.
grid 200x78
node a "top, bottom = 0, m - 1" at 1,0 shape=pill w=240 sub="left, right = 0, n - 1"
node b "top ≤ bottom and\nleft ≤ right ?" at 1,1 shape=diamond color=amber
node z "done" at 0,1 color=green
node c "row top: left to right" at 1,2 w=260 sub="top += 1"
node d "column right: top to bottom" at 1,3 w=260 sub="right -= 1"
node e "top ≤ bottom ?" at 1,4 shape=diamond color=amber
node f "row bottom: right to left" at 1,5 w=260 sub="bottom -= 1"
node g "left ≤ right ?" at 1,6 shape=diamond color=amber
node h "column left: bottom to top" at 1,7 w=260 sub="left += 1"
a -> b
b -> z : "no"
b -> c : "yes"
c -> d -> e
e -> f : "yes"
e:R -> b:R : "no"
f -> g
g -> h : "yes"
g:R -> b:R : "no"
h:R -> b:R
```

### 3.2 Diagonal — `r+c` is constant along a diagonal, `r-c` along an anti-diagonal

```
(0,0)(0,1)(0,2)      diagonal index r+c:
(1,0)(1,1)(1,2)        0   1   2
(2,0)(2,1)(2,2)        1   2   3
                       2   3   4
```

Every cell with the same `r+c` lies on the same anti-diagonal (top-right to
bottom-left); every cell with the same `r-c` lies on the same main-diagonal
(top-left to bottom-right). LC 498's zigzag diagonal traversal groups cells by
`r+c` into buckets, then reverses alternate buckets:

```go
func findDiagonalOrder(m [][]int) []int {
    if len(m) == 0 || len(m[0]) == 0 {
        return nil
    }
    rows, cols := len(m), len(m[0])
    diagonals := make([][]int, rows+cols-1)
    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            d := r + c
            diagonals[d] = append(diagonals[d], m[r][c])
        }
    }
    result := make([]int, 0, rows*cols)
    for d, vals := range diagonals {
        if d%2 == 0 {
            for i := len(vals) - 1; i >= 0; i-- {
                result = append(result, vals[i])
            }
        } else {
            result = append(result, vals...)
        }
    }
    return result
}
```

---

## Part 4 · Flood Fill — Visited Grid vs. Mutate-in-Place

Grid <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> (number of islands, flood fill, rotting oranges) reuses topic 14's
<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> mechanics wholesale — see that guide for the queue/recursion tradeoffs.
The one matrix-specific decision is **how to track "visited"**:

```go
// Option A: separate visited grid — O(rows·cols) extra space,
// input left untouched.
visited := make([][]bool, rows)
for i := range visited {
    visited[i] = make([]bool, cols)
}

// Option B: mutate the input in place — zero extra space,
// but destroys the input.
grid[r][c] = 0   // or a sentinel like 2, distinct from "land" and "water"
```

> ✅ Mutate in place when the problem is a single pass over a grid you own and
> won't need again (most "count the islands" style problems). Use a separate
> `visited` grid when the input must survive the call — multiple queries
> against the same grid, or a test harness that asserts the input is
> unchanged. State which one you're choosing out loud in an interview; it's a
> real tradeoff, not a stylistic footnote.

---

## Part 5 · Complexity Table

| Operation | Time | Extra Space | Note |
|---|:--:|:--:|---|
| Transpose | O(rows·cols) | O(1) | Upper-triangle swaps only |
| Rotate 90° in place | O(rows·cols) | O(1) | Transpose + per-row reverse |
| Spiral traversal | O(rows·cols) | O(1)* | Four shrinking boundaries |
| Diagonal traversal | O(rows·cols) | O(rows+cols) | Bucket by `r+c`, then flatten |
| Flood fill (<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>) | O(rows·cols) | O(rows·cols) worst case | Visited grid or recursion stack |
| Row-major flattened access | O(1) per cell | — | `data[r*cols+c]`, one allocation |

\* excluding the output slice

---

## Part 6 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| 2D array | `list` of `list`s (also pointer-chasing!) or NumPy (genuinely contiguous) | `[][]int`: pointer-chasing by default; flatten for contiguity |
| Fresh grid literal | `[[0]*cols for _ in range(rows)]` (comprehension avoids the shared-row trap) | Must loop `make([]int, cols)` per row — no comprehension shortcut |
| The shared-row trap | `[[0]*cols]*rows` is the SAME bug, well-known Python gotcha too | `for i := range grid { grid[i] = row }` — identical failure mode |
| Rotate in place | `zip(*matrix[::-1])` one-liner (allocates a new structure anyway) | Explicit transpose + reverse loop |
| Tuple swap | `a, b = b, a` | `a, b = b, a` — same idiom, no temp needed either language |

---

## Part 7 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| In-place transpose | O(n²) | O(1) | Building block for rotate |
| In-place 90° rotation | O(n²) | O(1) | LC 48 Rotate Image |
| Boundary-shrinking spiral | O(rows·cols) | O(1)* | LC 54 Spiral Matrix |
| Diagonal bucketing | O(rows·cols) | O(rows+cols) | LC 498 Diagonal Traverse |
| Grid flood fill (<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>) | O(rows·cols) | O(rows·cols) | LC 200 Number of Islands, LC 733 Flood Fill |
| Row/column zero-marking | O(rows·cols) | O(1)† | LC 73 Set Matrix Zeroes |

\* excluding output · † using first row/column as sentinels instead of a separate boolean grid

---

## Part 8 · Building Rotate Image + Spiral Matrix From Scratch

```go
package main

// Rotate Image (LC 48): rotate an n×n matrix 90° clockwise, in place.
func rotate(matrix [][]int) {
	n := len(matrix)

	// Step 1: transpose — swap across the main diagonal, upper triangle only.
	for i := 0; i < n; i++ {
		for j := i + 1; j < n; j++ {
			matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
		}
	}

	// Step 2: reverse each row — transpose + row-reverse = clockwise rotation.
	for i := 0; i < n; i++ {
		l, r := 0, n-1
		for l < r {
			matrix[i][l], matrix[i][r] = matrix[i][r], matrix[i][l]
			l++
			r--
		}
	}
}

// Spiral Matrix (LC 54): read an m×n matrix in spiral order.
func spiralOrder(matrix [][]int) []int {
	if len(matrix) == 0 || len(matrix[0]) == 0 {
		return nil
	}
	top, bottom := 0, len(matrix)-1
	left, right := 0, len(matrix[0])-1
	result := make([]int, 0, len(matrix)*len(matrix[0])) // preallocate: exact size known

	for top <= bottom && left <= right {
		// left -> right along the top row
		for c := left; c <= right; c++ {
			result = append(result, matrix[top][c])
		}
		top++

		// top -> bottom along the right column
		for r := top; r <= bottom; r++ {
			result = append(result, matrix[r][right])
		}
		right--

		// right -> left along the bottom row —
		// guarded: `top` may have already passed `bottom` for a single
		// remaining row, and that row was just fully emitted above.
		if top <= bottom {
			for c := right; c >= left; c-- {
				result = append(result, matrix[bottom][c])
			}
			bottom--
		}

		// bottom -> top along the left column —
		// same guard, for a single remaining column.
		if left <= right {
			for r := bottom; r >= top; r-- {
				result = append(result, matrix[r][left])
			}
			left++
		}
	}
	return result
}
```

**Talk track while writing:** rotate is two well-known O(n²) passes, not a
clever one-liner — say so and derive the transpose-then-reverse order from a
3×3 example rather than reciting it. For spiral, name the four-boundary
invariant up front, then explicitly call out *why* the third and fourth passes
need their own bound checks (a degenerate single row or column would otherwise
be double-counted) before you write them — that's the one place this problem
actually bites people.

---

<!-- block:24_go_1_layout -->
## Part 9 · Layout Measured, Construction Traps, Bounds, Directions, and Rotations by Formula

Part 1 draws the `[][]int` layout. This Part measures what the layout does and does not cost, lists the construction traps Go adds (nil rows, shallow clones, value
arrays), and gives every rotation as an index formula. All numbers are Go 1.24 on darwin/arm64, best of seven runs; all code was compiled with `go vet`, and the
rotations were checked against the formulas on 400 random square matrices (sizes 0–7).

```arch
%% caption: Read the constraints first: shape, in-place, and which ordering the rows and columns guarantee decide the technique.
grid 210x85
node q "A matrix problem" at 0,0 shape=pill
node a "Must the answer be\ncomputed in place?" at 0,1 shape=diamond color=amber w=280
node b "Rotate/reflect with swaps" at 1,0 color=green w=300 sub="yes, and it is square · transpose + reverse, or 4-way ring cycles"
node c "Encode old + 2*new in the cell" at 1,1 color=amber w=300 sub="yes, but a new value needs old neighbours · decode in a second pass"
node d "Row 0 and column 0 as markers" at 1,2 color=amber w=300 sub="yes, and rows/columns must be remembered · capture them first"
node e "A traversal order?" at 0,3 shape=diamond color=amber
node f "Four shrinking boundaries" at 1,3 color=green w=300 sub="or dirs with a turn rule"
node g "ONE global sorted order?" at 0,4 shape=diamond color=amber
node h "Binary search on the flat index" at 1,4 color=green w=300 sub="r*cols + c"
node i "Staircase from the top-right corner" at 0,5 color=amber w=260 sub="O(m + n)"
q -> a
a:R -> b:L
a:R -> c:L
a:R -> d:L
a -> e : "no"
e -> f : "yes"
e -> g : "a search"
g -> h : "yes"
g -> i : "only rows and columns sorted"
```

### 9.1 What the layout costs — measured

Summing every cell of an `n × n` `[]int` grid, direct loops (no closure in the loop), rows allocated one `make` at a time:

| Grid | Order | `[][]int` | flat `[]int` |
|---|---|--:|--:|
| 512 × 512 (2 MB) | row-major | 0.10 ms | 0.09 ms |
| 512 × 512 | column-major | 0.31 ms | 0.28 ms |
| 4096 × 4096 (134 MB) | row-major | 3.79 ms | 3.84 ms |
| 4096 × 4096 | column-major | **46.2 ms** | **46.1 ms** |

Two conclusions. **The layout barely mattered:** rows allocated back to back sat next to each other, so the pointer-per-row structure cost nothing measurable
(a third variant — a `[][]int` whose rows are sub-slices of one backing array — measured the same again). **The loop order mattered a great deal:** walking down
columns was about 3× slower at 2 MB and about **12× slower at 134 MB**, for either layout, because each step lands on a different cache line. So write the row index in the
outer loop, and treat "flatten it" as an allocation and ergonomics decision, not a speed-up. (In topic 21 or 14 this shows up as "why is my grid <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> slow": the
neighbour order is fine, the *sweep* order is what to check.)

If you want one contiguous block *and* `grid[r][c]` syntax, slice a single backing array — with a **full slice expression** so a row cannot grow into its neighbour:

```go
backing := make([]int, rows*cols)
grid := make([][]int, rows)
for i := range grid {
    grid[i] = backing[i*cols : (i+1)*cols : (i+1)*cols] // capacity capped at the row's end
}
```

Without the third index, `append(rows[0], 42)` on a row that still has room in the backing array silently **overwrites the first element of the next row**
(measured: `backing` became `[0 0 0 42 0 0]`); with `backing[0:3:3]` the same append reallocated and `backing` stayed all zeros.

### 9.2 Construction and copying traps

- `make([][]int, 3)` allocates the outer slice only; every row is `nil`, and `grid[0][0] = 1` panics: `index out of range [0] with length 0` (measured).
- `slices.Clone(grid)` is **shallow**: it copies the row headers, so the clone's rows are the *same* rows — `sh[0][0] = 99` changed the original (measured). A deep copy
  clones each row: `out[i] = slices.Clone(grid[i])`.
- A fixed array `[3][3]int` is a **value**: `b := a` copies all nine ints (after `b[0][0] = 99`, `a[0][0]` is still `1`), `a == b` compares element by element (`false` here),
  and passing it to a function copies it — use a slice or `*[3][3]int` to mutate in place. A slice of slices is the opposite: assignment copies only the header.
- Rows of a `[][]int` may have different lengths (a ragged grid: `{{1,2,3},{4},{5,6}}` has 6 cells); use `len(m[r])`, not `len(m[0])`, when rows can differ.

### 9.3 Bounds and directions: Go panics where Python wraps

An index of `-1` does not wrap in Go — it panics (`index out of range [-1]`, measured). That is *safer* than Python's silent `g[-1]` wrap, but it still means every neighbour
scan needs a check. The one-comparison idiom converts to unsigned, so a negative number becomes huge:

```go
var dirs = [4][2]int{{0, 1}, {1, 0}, {0, -1}, {-1, 0}} // right, down, left, up — also the spiral's turn order

func inBounds(r, c, rows, cols int) bool { return uint(r) < uint(rows) && uint(c) < uint(cols) }
```

Guard empty input with `if len(m) == 0 || len(m[0]) == 0`. A flat index is `i = r*cols + c`, and back again `r, c = i/cols, i%cols`. `for range n` (Go 1.22) loops `n` times when you
only need a counter.

### 9.4 Transposes and rotations as formulas

A rectangle's transpose has a new shape, so it must allocate; a square one can be done in place:

```go
func transposeNew(m [][]int) [][]int { // any rows × cols; the result is cols × rows
    if len(m) == 0 { return nil }
    rows, cols := len(m), len(m[0])
    out := make([][]int, cols)
    for j := range out {
        out[j] = make([]int, rows)
        for i := 0; i < rows; i++ { out[j][i] = m[i][j] }
    }
    return out
}

func transposeInPlace(m [][]int) { // square only
    n := len(m)
    for i := 0; i < n; i++ {
        for j := i + 1; j < n; j++ { m[i][j], m[j][i] = m[j][i], m[i][j] } // j > i only, or every pair is swapped twice
    }
}

func rotateCW(m [][]int)  { transposeInPlace(m); for _, row := range m { slices.Reverse(row) } }
func rotateCCW(m [][]int) { for _, row := range m { slices.Reverse(row) }; transposeInPlace(m) }
func rotate180(m [][]int) { slices.Reverse(m); for _, row := range m { slices.Reverse(row) } }

func rotateCWRings(m [][]int) { // one 4-cycle per cell of each ring
    n := len(m)
    for i := 0; i < n/2; i++ {
        for j := i; j < n-1-i; j++ {
            m[i][j], m[j][n-1-i], m[n-1-i][n-1-j], m[n-1-j][i] =
                m[n-1-j][i], m[i][j], m[j][n-1-i], m[n-1-i][n-1-j]
        }
    }
}
```

| Operation | Where `m[i][j]` ends up (n × n) | Recipe |
|---|---|---|
| Transpose | `(j, i)` | swap across the main diagonal |
| Rotate 90° clockwise | `(j, n-1-i)` | transpose, then reverse each row |
| Rotate 90° counter-clockwise | `(n-1-j, i)` | reverse each row, then transpose — or transpose, then reverse the row order |
| Rotate 180° | `(n-1-i, n-1-j)` | reverse the row order and each row |

For `[[1,2,3],[4,5,6],[7,8,9]]`: clockwise `[[7 4 1] [8 5 2] [9 6 3]]`, counter-clockwise `[[3 6 9] [2 5 8] [1 4 7]]`, 180° `[[9 8 7] [6 5 4] [3 2 1]]`, and the transpose of the 2 × 3
`[[1,2,3],[4,5,6]]` is `[[1 4] [2 5] [3 6]]`. The ring version's inner loop runs over `j := i; j < n-1-i` — inclusive of the ring's first corner, exclusive of the last — so no corner is cycled
twice; all four agreed with the formulas on every random matrix. `slices.Reverse` (Go 1.21) reverses a slice in place, and works on the row order too because a `[][]int` is a slice of row headers.

---
<!-- /block:24_go_1_layout -->

<!-- block:24_go_2_problems -->
## Part 10 · The Eight Problems in Go — Spiral Two Ways, Markers, Staircase vs Binary Search, Encoding, Bounce

The Go solution files for this topic are still placeholders, so these are the plans, each compared with a brute-force or formula reference (600 random rectangles up to
6 × 6 for the traversals, 2,000 random sorted matrices × 40 targets for the staircase). Each block was compiled with `go vet`.

### 10.1 Spiral (003, 004): boundaries, or "turn when blocked"

Part 8 has the boundary version. The direction-vector version handles both reading a grid and writing one (Problem 004):

```go
func spiralFill(n int) [][]int { // Problem 004: write 1..n² in spiral order
    g := make([][]int, n)
    for i := range g { g[i] = make([]int, n) }
    r, c, d := 0, 0, 0
    for k := 1; k <= n*n; k++ {
        g[r][c] = k
        nr, nc := r+dirs[d][0], c+dirs[d][1]
        if !inBounds(nr, nc, n, n) || g[nr][nc] != 0 { // blocked: off-grid or already written → turn clockwise
            d = (d + 1) % 4
            nr, nc = r+dirs[d][0], c+dirs[d][1]
        }
        r, c = nr, nc
    }
    return g
}
// spiralFill(3) = [[1 2 3] [8 9 4] [7 6 5]]     spiralOrder([[1 2 3] [4 5 6] [7 8 9]]) = [1 2 3 6 9 8 7 4 5]
```

A read-side "turn when blocked" version (with a `seen` grid) produced the same output as the four-boundary function on 600 random shapes with 0–6 rows and columns. The two guards in the
boundary version are load-bearing: without them `[[1,2,3]]` produced `[1 2 3 2 1]` and `[[1],[2],[3]]` produced `[1 2 3 2]` — the last row or column is emitted twice. In Problem 004 the same mistake
is a double *write*, which leaves no visible sign of the error.

### 10.2 Set Matrix Zeroes (005): the border as scratch memory

```go
func setZeroes(m [][]int) {
    rows, cols := len(m), len(m[0])
    firstRow, firstCol := false, false // capture BEFORE the markers overwrite row 0 and column 0
    for c := 0; c < cols; c++ { if m[0][c] == 0 { firstRow = true } }
    for r := 0; r < rows; r++ { if m[r][0] == 0 { firstCol = true } }
    for r := 1; r < rows; r++ {
        for c := 1; c < cols; c++ {
            if m[r][c] == 0 { m[r][0], m[0][c] = 0, 0 } // mark this row and this column
        }
    }
    for r := 1; r < rows; r++ {
        for c := 1; c < cols; c++ {
            if m[r][0] == 0 || m[0][c] == 0 { m[r][c] = 0 } // apply the markers to the interior only
        }
    }
    if firstRow { for c := 0; c < cols; c++ { m[0][c] = 0 } } // the border last
    if firstCol { for r := 0; r < rows; r++ { m[r][0] = 0 } }
}
```

The order is the whole problem: flags first, marks and applications on `range 1…`, the border last. Checked against a two-map reference on random matrices with zeros.

### 10.3 Search a 2D Matrix II (006): staircase, and why flattening is wrong

```go
func staircase(m [][]int, target int) bool {
    if len(m) == 0 || len(m[0]) == 0 { return false }
    r, c := 0, len(m[0])-1 // top-right: bigger to the left, smaller below
    for r < len(m) && c >= 0 {
        switch v := m[r][c]; {
        case v == target: return true
        case v > target:  c-- // everything below in this column is even bigger: drop the column
        default:          r++ // everything to the left in this row is even smaller: drop the row
        }
    }
    return false
}
```

Each step discards a row or a column, so at most `m + n − 1` cells are read. It matched a brute-force membership test for every target `0…39` on 2,000 random row-and-column-sorted matrices. The flat
`m[mid/cols][mid%cols]` binary search belongs to LC 74, where each row starts above the previous one's end; on the LC 240 example matrix it disagreed with the staircase for **12 of 32** targets. Only
the top-right (or bottom-left) corner has the two-way elimination property; from the top-left a "too small" verdict eliminates nothing.

### 10.4 Game of Life (007): old | new<<1

```go
func gameOfLife(b [][]int) {
    rows, cols := len(b), len(b[0])
    for r := 0; r < rows; r++ {
        for c := 0; c < cols; c++ {
            live := 0
            for dr := -1; dr <= 1; dr++ {
                for dc := -1; dc <= 1; dc++ {
                    nr, nc := r+dr, c+dc
                    if (dr != 0 || dc != 0) && inBounds(nr, nc, rows, cols) {
                        live += b[nr][nc] & 1 // the low bit is the ORIGINAL state
                    }
                }
            }
            if b[r][c]&1 == 1 && (live == 2 || live == 3) {
                b[r][c] |= 2 // live and stays live: 1 → 3
            } else if b[r][c]&1 == 0 && live == 3 {
                b[r][c] |= 2 // dead and is born: 0 → 2
            }
        }
    }
    for r := range b { for c := range b[r] { b[r][c] >>= 1 } } // decode: the new state is the high bit
}
```

The naive alternative — overwrite each cell with its final value as you scan — was **wrong on 281 of 460** random boards (sizes 1–6 per side); the encoded version matched a copy-based reference on all of them.
Reading a neighbour as `b[nr][nc]` instead of `b[nr][nc] & 1` during the first pass miscounts as soon as a neighbour already holds 2 or 3. In Go, mind the precedence: `b[r][c]&1 == 1` parses
as `(b[r][c] & 1) == 1` (unlike C, `&` binds tighter than `==` in Go), so the parentheses are optional here.

### 10.5 Diagonal Traverse (008): bounce, or bucket by `r + c`

```go
func findDiagonalOrder(m [][]int) []int {
    if len(m) == 0 || len(m[0]) == 0 { return nil }
    rows, cols := len(m), len(m[0])
    out := make([]int, 0, rows*cols)
    r, c, up := 0, 0, true
    for range rows * cols {
        out = append(out, m[r][c])
        if up {
            switch {
            case c == cols-1: r++; up = false // right wall first (it also covers the corner) …
            case r == 0:      c++; up = false // … then the top wall
            default:          r--; c++
            }
        } else {
            switch {
            case r == rows-1: c++; up = true // bottom wall first …
            case c == 0:      r++; up = true // … then the left wall
            default:          r++; c--
            }
        }
    }
    return out
}
// [[1 2 3] [4 5 6] [7 8 9]] → [1 2 4 7 5 3 6 8 9]
```

It equalled the bucket version (group by `r + c`, reverse the even buckets — Part 3.2) on every random shape. Swapping the order of the wall checks (top before right when going up, left before bottom
going down) sends the walk off the grid: on a 3 × 3 input it panicked with `index out of range [3] with length 3`.

### 10.6 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Rotate counter-clockwise / 180°." | Reverse each row then transpose (or transpose then reverse the row order) / reverse the row order and each row. |
| "Rotate a non-square matrix." | Allocate the `cols × rows` result (`transposeNew` plus a row reverse) — the shape changes, so it cannot be in place. |
| "Rotate `k` times." | Reduce `k` mod 4 first. |
| "Search a matrix sorted as one sequence (LC 74)." | Binary search on the flat index — O(log mn). |
| "The grid is huge and sweeps are slow." | Check the loop order first (rows outermost); the measured column-major penalty was 12× at 134 MB. |
| "Sum of any rectangle, repeatedly." | A 2-D prefix-sum table (topic 04). |

---
<!-- /block:24_go_2_problems -->

<!-- problem-map:start -->
## Part 11 · Every Problem in This Topic, by Pattern

Eight problems, three skills (exact index arithmetic · boundary-tracked traversal · scratch space inside the structure) — the Python guide's map in Go. Each **Trap** is a mistake documented in that problem's solution file, plus Go-specific hazards. Topic 24's Go solutions are still placeholders; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Transpose Matrix](GoDSA/24_matrix/001_transpose_matrix/solution.go) <br>LC 867 · Easy | Transpose is a shape change | Allocate the `cols × rows` result and copy `out[j][i] = m[i][j]`; only a square matrix can be transposed in place. **Trap:** writing back in place for a non-square input; sizing the result `rows × cols`; leaving the inner rows `nil` (`index out of range [0] with length 0`). |
| [002 · Rotate Image](GoDSA/24_matrix/002_rotate_image/solution.go) <br>LC 48 · Medium | Transpose, then reverse each row | Swap the upper triangle only (`j > i`), then `slices.Reverse` every row: clockwise. Or one 4-cycle per ring cell. **Trap:** transposing all pairs (each swap undone); reversing the rows before transposing, or the row *order* after (counter-clockwise); allocating a new matrix; cycling a ring's corner twice. |
| [003 · Spiral Matrix](GoDSA/24_matrix/003_spiral_matrix/solution.go) <br>LC 54 · Medium | Four shrinking boundaries | `top/bottom/left/right`; walk a side, then move in the boundary it exhausted; guard the last two passes. **Trap:** no `top <= bottom` / `left <= right` guards (`[[1,2,3]]` gives `[1 2 3 2 1]`); an exclusive `c < right` dropping the last cell; shrinking a boundary before using it; a reverse loop stopping one cell early; `len(m[0])` on an empty matrix. |
| [004 · Spiral Matrix II](GoDSA/24_matrix/004_spiral_matrix_ii/solution.go) <br>LC 59 · Medium | The same boundaries, writing | Write `1..n²`, incrementing after *every* write; or turn clockwise (`dirs[d]`) when the next cell is off-grid or non-zero. **Trap:** incrementing per side instead of per write; the missing guards, now a double *write*; one `row` slice shared by every row of the result. |
| [005 · Set Matrix Zeroes](GoDSA/24_matrix/005_set_matrix_zeroes/solution.go) <br>LC 73 · Medium | The border as markers | Capture "row 0 / column 0 had a zero", mark from the interior, apply to the interior, zero the border last. **Trap:** capturing the flags after marking; loops that start at 0 instead of 1; zeroing the border before the interior; allocating a copy. |
| [006 · Search a 2D Matrix II](GoDSA/24_matrix/006_search_a_2d_matrix_ii/solution.go) <br>LC 240 · Medium | Staircase from the top-right | `switch` on the corner: bigger → `c--`, smaller → `r++`; O(m + n). **Trap:** starting top-left; flattening and binary searching (LC 74's technique — wrong here, 12 of 32 targets on the LC 240 example); inconsistent bounds; moving in the wrong direction. |
| [007 · Game of Life](GoDSA/24_matrix/007_game_of_life/solution.go) <br>LC 289 · Medium | Encode old and new in one cell | Count neighbours with `& 1`, `\|= 2` on the cells whose new state is live, then `>>= 1`. **Trap:** overwriting with the final value while scanning (wrong on 281 of 460 random boards); reading a neighbour without `& 1`; forgetting the decode pass; the encoding backwards. |
| [008 · Diagonal Traverse](GoDSA/24_matrix/008_diagonal_traverse/solution.go) <br>LC 498 · Medium | Bounce off four walls | A `up` flag; check the right/bottom wall before the top/left wall so corners resolve; or bucket by `r + c` and reverse the even buckets. **Trap:** an inconsistent wall-check order (a panic on a 3 × 3 input); not flipping `up` on a bounce; reversing the odd buckets; `len(m[0])` on an empty matrix. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Draw the `[][]int` layout: contiguous row-headers, scattered row data
- [ ] Explain when a flattened `[]int` with `r*cols+c` indexing actually pays off
- [ ] Allocate every row of a fresh `[][]int` individually — never share one row slice
- [ ] Transpose only the upper triangle (`j := i+1`), not the full grid
- [ ] Derive rotate-90° as transpose + per-row reverse from a small example
- [ ] Explain why spiral traversal needs bounds checks before its 3rd/4th passes
- [ ] Know the `r+c` (diagonal) / `r-c` (anti-diagonal) grouping trick
- [ ] State the visited-grid-vs-mutate-input tradeoff out loud before choosing one
- [ ] Preallocate output slices with `make([]int, 0, rows*cols)` when size is known
- [ ] Quote the measured layout facts: `[][]int` and flat `[]int` tied (3.8 ms row-major at 134 MB) while column-major was ~12× slower (46 ms) <!--ca-->
- [ ] Cap a sub-slice's capacity (`backing[a:b:b]`) so `append` on one row cannot overwrite the next <!--ca-->
- [ ] Know the construction traps: nil rows panic, `slices.Clone` of a `[][]int` is shallow, `[3][3]int` is a value <!--ca-->
- [ ] Bounds-check with `uint(r) < uint(rows)`, and remember Go panics on `-1` where Python silently wraps <!--ca-->
- [ ] Write all four rotations as swaps and as `(i, j)` destinations, and keep clockwise and counter-clockwise recipes straight <!--ca-->
- [ ] Write the spiral both ways and reproduce the double-emission bug without the two guards <!--ca-->
- [ ] Order the Set Matrix Zeroes passes: flags, mark, apply to the interior, border last <!--ca-->
- [ ] Explain why LC 240 uses a staircase and LC 74 a flat binary search <!--ca-->
- [ ] Encode Game of Life as `old | new<<1`, read neighbours with `& 1`, and quote the naive version's failure rate <!--ca-->
