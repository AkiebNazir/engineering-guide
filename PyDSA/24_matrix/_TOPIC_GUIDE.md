# Topic 24 · Matrix — Python Deep Dive

> Every matrix problem in this topic reduces to one of three skills:
> **exact `(row, col)` index arithmetic** (know precisely which cell you
> mean at every step), **boundary-tracked traversal** (walk a shrinking or
> bouncing frontier instead of naive nested loops), and **finding scratch
> space INSIDE the structure you're transforming** when the problem
> explicitly forbids allocating a second one. None of these are new data
> structures — a matrix is just `List[List[int]]` — the graded skill is
> discipline: can you reason correctly about a 2D coordinate system under
> constraints (in-place, one pass, simultaneous updates) without an
> off-by-one costing you the whole traversal.

---

## Part 0 · The eight problems and their tricks

**Index arithmetic as the whole problem** (001 Transpose Matrix): the
transpose is one line, `result[j][i] = matrix[i][j]` — but it's the
cleanest illustration in the topic of the fact that a matrix's SHAPE
(`m x n` vs `n x m`) is part of its identity. Transposing a non-square
matrix cannot be done in place because the output literally doesn't fit
in the input's array-of-rows structure; only when `m == n` does the
output shape coincide with the input shape, which is precisely the
precondition 002 relies on.

**Two O(1)-space passes compose into a rotation** (002 Rotate Image):
neither "transpose" nor "reverse each row" alone rotates anything — but
composed in that exact order, on a matrix guaranteed square by the
problem, they algebraically equal the closed-form 90-degree clockwise
rotation formula `rotated[i][j] = matrix[n-1-j][i]`. This is the topic's
first taste of "in-place transformation via decomposition": break one
hard spatial operation into two easy ones that each only need O(1) extra
memory (a swap, a two-pointer reverse), because the matrix being SQUARE
is what makes doing this without a second array possible at all.

```arch
%% caption: Rotate 90° clockwise = transpose, then reverse every row. Both passes work in place.
grid 200x100
node A "1 2 3\n4 5 6\n7 8 9" at 0,0 color=slate
node B "1 4 7\n2 5 8\n3 6 9" at 1,0 color=slate
node C "7 4 1\n8 5 2\n9 6 3" at 2,0 color=green
A -> B : "transpose"
B -> C : "reverse each row"
```


**Boundary-tracked traversal, shrinking inward** (003 Spiral Matrix, 004
Spiral Matrix II): maintain `top`, `bottom`, `left`, `right` and walk one
full side per loop iteration, tightening the boundary that side just
exhausted. 003 reads a spiral out of an existing grid; 004 writes an
increasing counter INTO an empty grid in spiral order — literally the
same boundary machinery with `result.append(matrix[...])` swapped for
`matrix[...] = num; num += 1`. The two guards (`if top <= bottom` before
the bottom-row pass, `if left <= right` before the left-column pass)
exist for exactly one reason: without them, a matrix with a single
remaining row or column gets traversed twice once the boundaries cross.

```arch
%% caption: Spiral traversal: four shrinking boundaries. The two inner checks stop a single leftover row or column from being walked twice.
grid 200x80
node A "top, bottom = 0, m - 1" at 1,0 w=300 sub="left, right = 0, n - 1"
node B "top ≤ bottom and left ≤ right ?" at 1,1 shape=diamond color=amber
node Z "done" at 2,1 color=green
node C "row top: left to right, top += 1" at 1,2 w=300
node D "column right: top to bottom, right -= 1" at 1,3 w=300
node E "top ≤ bottom ?" at 1,4 shape=diamond color=amber
node F "row bottom: right to left, bottom -= 1" at 1,5 w=300
node G "left ≤ right ?" at 1,6 shape=diamond color=amber
node H "column left: bottom to top, left += 1" at 1,7 w=300
A -> B
B -> Z : "no"
B -> C : "yes"
C -> D -> E
E -> F : "yes"
E:L -> B:L : "no"
F -> G
G -> H : "yes"
G:L -> B:L : "no"
H:L -> B:L
```


**The matrix's own border as O(1) scratch memory** (005 Set Matrix
Zeroes): you need to remember which rows/columns contained a zero in the
ORIGINAL matrix, but aren't allowed extra O(m)/O(n) arrays to hold that
memory. The fix: use row 0 and column 0 of the matrix ITSELF as marker
arrays, with two standalone booleans capturing whether row 0 / column 0
originally had a zero (captured BEFORE the marking pass overwrites
exactly those cells). This is the topic's clearest example of "the
structure you're transforming can BE your extra memory, if you're
careful about ordering reads before writes."

**Staircase search exploiting two independent sort invariants** (006
Search a 2D Matrix II): start at the top-right corner, the only position
where a "too big" comparison safely eliminates an entire column AND a
"too small" comparison safely eliminates an entire row. This is
deliberately NOT true binary search — it eliminates one row or column per
step (O(m+n) total), not half the remaining search space per step — and
that distinction matters: the weaker "each row sorted, each column
sorted independently" guarantee here does not imply one global sorted
order, so flattening the matrix and binary-searching it (the LC 74
technique, a different and stricter problem) is simply wrong here.

```arch
%% caption: Staircase search from the top-right corner: every comparison eliminates a whole row or a whole column, so O(m + n).
grid 190x100
node A "start at the top-right cell" at 1,0
node B "cell compared with target" at 1,1 shape=diamond color=amber
node C "found" at 2,1 color=green
node D "move left: col -= 1" at 0.5,2 w=190 sub="the rest of this column is bigger too"
node E "move down: row += 1" at 1.5,2 w=190 sub="the rest of this row is smaller too"
node F "still inside the matrix?" at 1,3 shape=diamond color=amber
node G "not present" at 1,4 color=red
A -> B
B:R -> C:L : "equal"
B:B -> D:T : "cell is bigger"
B:B -> E:T : "cell is smaller"
D:B -> F:L
E:B -> F:R
F:L -> B:L : "yes"
F -> G : "no"
```


**Two states packed into one cell to fake simultaneity** (007 Game of
Life): the rules require every cell's next state to depend only on
everyone's OLD state, "simultaneously" — but a naive in-place scan
overwrites cells as it goes, so later cells read already-updated
neighbors and the simulation corrupts silently. The fix: since every
cell only ever holds 0 or 1, encode `old + 2*new` into the same int
during pass 1 (recovering any neighbor's true original state via `% 2`
regardless of visit order), then decode with `>>= 1` in pass 2. This is
the topic's second "structure as scratch space" trick, but a different
flavor from 005's border-as-marker — here the SAME cell holds both the
input and the output at once, disambiguated by which bit you read.

**Boundary-bounce simulation for a non-row-major order** (008 Diagonal
Traverse): every cell belongs to exactly one anti-diagonal (`d = row +
col` is constant along it), and this problem alternates walking
direction every diagonal. Rather than bucket cells by `d` and reverse
every other bucket (a correct but O(mn)-extra-space approach), simulate
the zigzag directly with two coordinates and a `going_up` flag, bouncing
off whichever of the four boundaries is hit next. It's the same
"boundary tracking" idea as 003/004, except the boundary being tracked is
a bounce condition per-step rather than a shrinking rectangle.

---

## Part 1 · The three skills, and which problems exercise which

| Skill | Problems | What "getting it right" looks like |
|---|---|---|
| **Exact 2D index arithmetic** | 001, 002, 008 | Knowing which formula maps `(row, col)` to its destination (or its diagonal group) without an off-by-one |
| **Boundary-tracked traversal** | 003, 004, 006, 008 | Walking a shrinking rectangle or a bouncing frontier instead of naive nested loops, with correct guard conditions at the edges |
| **In-place scratch space discipline** | 002, 005, 007 | Finding memory INSIDE the structure being transformed, and getting the read-before-overwrite ordering right so the "scratch" doesn't destroy data you still need |

Several problems appear in more than one row on purpose — 002 and 008
both need precise index formulas AND a form of boundary discipline; the
overlap is the point, not noise.

---

## Part 2 · Problem-by-problem map

| # | Problem | Difficulty | Core trick | In-place? |
|---|---|---|---|:--:|
| 001 | Transpose Matrix | Easy | `result[j][i] = matrix[i][j]`, output shape swaps | no (can't, in general) |
| 002 | Rotate Image | Medium | transpose + reverse each row (or 4-way ring swap) | **yes** |
| 003 | Spiral Matrix | Medium | four shrinking boundaries, read order | no |
| 004 | Spiral Matrix II | Medium | four shrinking boundaries, write order | no (builds new) |
| 005 | Set Matrix Zeroes | Medium | row 0 / col 0 as marker arrays | **yes** |
| 006 | Search a 2D Matrix II | Medium | staircase search from top-right corner | no |
| 007 | Game of Life | Medium | bit-pack `old + 2*new` into each cell | **yes** |
| 008 | Diagonal Traverse | Medium | boundary-bounce zigzag simulation | no |

Three of the eight (002, 005, 007) are explicitly O(1)-extra-space,
mutate-in-place problems — the highest concentration of that constraint
of any topic in this curriculum, which is why the "mutates input?" column
in every one of this topic's solution files carries real weight, not
boilerplate.

---

## Part 3 · Cross-references worth remembering

- **006 ↔ topic 05 (Binary Search)**: deliberately contrasted, not
  equated. True binary search halves the remaining search space with
  ONE global monotone order; 006's staircase search eliminates one row
  or column with two INDEPENDENT per-axis sort invariants, giving
  O(m+n), not O(log(mn)). Confusing the two — trying to flatten-and-
  binary-search a matrix that's only row/column-sorted independently —
  is the single most common mistake on this problem.
- **007's neighbor-counting loop ↔ topic 14 (Graphs, grid BFS/flood
  fill)**: both iterate a cell's 4- or 8-directional neighbors with the
  same `0 <= nr < m and 0 <= nc < n` bounds-check idiom. The difference
  is what the neighbor scan is FOR — flood fill spreads a REGION outward
  from a seed; Game of Life computes every cell's next state from a
  fixed rule applied everywhere at once, with no traversal order that
  matters once the encode/decode trick removes the ordering dependency.
- **002 and 005 ↔ each other, directly**: both are this topic's
  clearest lessons in "the matrix can be its own scratch memory" — 002
  via decomposing one spatial operation into two in-place passes, 005 via
  repurposing its own border cells as marker storage. Worth studying
  back to back for the shared discipline of capturing what you need to
  know BEFORE you start overwriting the place you're about to read it
  from.
- **001 ↔ 002, directly**: 001 is what happens when you try to do 002's
  first step (transpose) on a matrix that ISN'T square — you can't do it
  in place, full stop, because the output shape genuinely differs from
  the input shape. Rotate Image's "DO NOT allocate another 2D matrix"
  constraint is only satisfiable because LC 48 guarantees `n x n`.
- **003/004 ↔ 002's ring-based variant**: 003 and 004's shrinking-
  rectangle boundaries and 002's layer-by-layer 4-way ring swap are both
  "peel the matrix from the outside in" techniques; comparing their
  bookkeeping styles (four independent scalar boundaries vs. an explicit
  `first`/`last`/`offset` per ring) is a good gut-check for which style
  you personally get right faster under interview pressure.

---

## Part 4 · Where this topic ends

Eight problems, three recurring skills, no single "extensible pattern"
the way sliding window or binary search have one canonical template —
each problem's trick is specific to what its constraints allow (square
vs. non-square, read vs. write, one global order vs. two independent
per-axis orders, true simultaneity vs. simulated simultaneity). The
transferable instinct across all eight: before writing a single loop,
ask (1) does this operation preserve the matrix's shape, and if not, can
it possibly be in place, (2) is there a boundary that should shrink or
bounce rather than a plain nested `for` over the whole grid, and (3) if
the problem demands O(1) extra space, where INSIDE the existing
structure can I stash what I need to remember, and in what order do I
need to read it before I start overwriting it.

<!-- block:24_py_1_toolkit -->
## Part 5 · The Matrix Toolkit — Construction, Copying, Rotation by Formula, Bounds, Diagonals

Parts 0–4 explain the eight tricks. This Part is what you need *around* them: how to build and copy a grid without aliasing, every
rotation and flip as a one-line formula (and its in-place version), the silent index-wrap trap, and the diagonal arithmetic. Every
snippet was run on CPython 3.13; the rotations were checked against `zip`-based references on square matrices of size 0–7.

```arch
%% caption: Read the matrix problem's constraints first: shape, in-place, and which ordering the rows and columns guarantee decide the technique.
grid 230x80
node Q "A matrix problem" at 0,0 shape=pill
node A "Must the answer be computed in place?" at 0,2 shape=diamond color=amber
node qb "yes, and it is square" at 1,1 shape=pill w=190
node qc "yes, but a cell's new value needs old neighbours" at 1,2 shape=pill w=190
node qd "yes, and rows/columns must be remembered" at 1,3 shape=pill w=190
node B "rotate/reflect with swaps" at 2,1 color=green w=250 sub="transpose + reverse, or 4-way ring cycles"
node C "encode old + 2*new in the cell" at 2,2 color=amber w=250 sub="decode in a second pass"
node D "use row 0 and column 0 as markers" at 2,3 color=amber w=250 sub="capture them first"
node E "Is it a traversal order?" at 0,4 shape=diamond color=amber
node F "four shrinking boundaries" at 2,4 color=green w=250 sub="or direction vectors with a turn rule"
node G "Is it ONE global sorted order?" at 0,5 shape=diamond color=amber
node H "binary search on the flattened index" at 2,5 color=green w=250 sub="r*n + c"
node I "staircase from the top-right corner" at 2,6 color=amber w=250 sub="O(m + n)"
Q -> A
A:R -> qb:L
A:R -> qc:L
A:R -> qd:L
qb -> B
qc -> C
qd -> D
A -> E : "no"
E -> F : "yes"
E -> G : "no: a search"
G -> H : "yes"
G:B -> I:L : "only rows and columns sorted"
```

### 5.1 Building and copying without aliasing

`[[0] * 3] * 3` is three references to **one** row: after `g[0][0] = 1`, `g` is `[[1,0,0], [1,0,0], [1,0,0]]` (the rows even share an `id`).
The comprehension `[[0] * 3 for _ in range(3)]` builds three rows and gives `[[1,0,0], [0,0,0], [0,0,0]]`. (`[0] * 3` is safe because the
elements are immutable ints; it is the outer `*` that repeats a *reference*.)

Copying has the same trap one level up. `copy.copy(a)` is **shallow** — the rows are shared, so `sh[0][0] = 99` also changes `a`. Copy the rows:
`[r[:] for r in a]` (or `list(map(list, a))`), which is what an "input must survive" solution needs. Measured on 500 × 500: both row-wise
copies took **0.18 ms**, `copy.deepcopy` took **25.9 ms** (about 140× slower, for no benefit on a grid of ints).

### 5.2 Transposes and rotations as formulas

`zip(*m)` transposes any rectangular matrix — but yields **tuples**, so wrap each: `[list(r) for r in zip(*m)]` (Problem 001's documented trap).
On a ragged input it silently truncates to the shortest row (`zip(*[[1,2,3],[4,5]])` → `[(1,4), (2,5)]`). It is also fast: on a 1000 × 1000 matrix
the `zip` version took **4.7 ms** against **18.2 ms** for a nested comprehension.

| Operation | One-liner | Where `a[i][j]` ends up (n × n) |
|---|---|---|
| Transpose | `[list(r) for r in zip(*a)]` | `(j, i)` |
| Rotate 90° clockwise | `[list(r) for r in zip(*a[::-1])]` | `(j, n-1-i)` |
| Rotate 90° counter-clockwise | `[list(r) for r in zip(*a)][::-1]` | `(n-1-j, i)` |
| Rotate 180° | `[r[::-1] for r in a[::-1]]` | `(n-1-i, n-1-j)` |

For `[[1,2,3],[4,5,6],[7,8,9]]`: clockwise `[[7,4,1],[8,5,2],[9,6,3]]`, counter-clockwise `[[3,6,9],[2,5,8],[1,4,7]]`, 180° `[[9,8,7],[6,5,4],[3,2,1]]`.
The two-step recipes are order-sensitive (this is Problem 002's documented trap): **transpose, then reverse each row** is clockwise, but **reverse each
row, then transpose** — and equally **transpose, then reverse the row order** — is *counter*-clockwise.

```python
def rotate_cw(a):                                # in place: transpose the upper triangle, then reverse every row
    n = len(a)
    for i in range(n):
        for j in range(i + 1, n): a[i][j], a[j][i] = a[j][i], a[i][j]     # j > i only, or every pair is swapped twice
    for r in a: r.reverse()

def rotate_cw_rings(a):                          # in place: one 4-cycle per cell of each ring
    n = len(a)
    for i in range(n // 2):
        for j in range(i, n - 1 - i):
            a[i][j], a[j][n-1-i], a[n-1-i][n-1-j], a[n-1-j][i] = a[n-1-j][i], a[i][j], a[j][n-1-i], a[n-1-i][n-1-j]
```

Both agreed with the `zip` reference on 400 random square matrices (sizes 0–7); `rotate_cw_rings` runs the inner loop over `range(i, n-1-i)` — inclusive of the
ring's first corner, exclusive of the last, so no corner is cycled twice. A non-square matrix cannot be rotated in place at all (the shape changes), so
return a new one.

### 5.3 Bounds: negative indexes wrap, silently

A neighbour scan without bounds checks does **not** always crash: `g[-1]` is the *last* row. On `[[1,0,0],[0,0,0],[0,0,1]]` the corner cell `(0,0)` has no
live neighbours, but scanning `(r+dr, c+dc)` without a check reads `g[-1][-1]` — the opposite corner — and reports **1**. The top and left edges wrap
silently while the bottom and right edges raise `IndexError`, which is why the bug survives small tests. Always write the check:

```python
DIRS4 = ((0, 1), (1, 0), (0, -1), (-1, 0))              # right, down, left, up — also the spiral's turn order
DIRS8 = DIRS4 + ((1, 1), (1, -1), (-1, 1), (-1, -1))

def neighbours(g, r, c, dirs=DIRS8):
    m, n = len(g), len(g[0])
    return [(r + dr, c + dc) for dr, dc in dirs if 0 <= r + dr < m and 0 <= c + dc < n]
```

Empty inputs: `[]` makes `len(matrix[0])` raise `IndexError`, while `[[]]` gives `0` columns — guard with `if not m or not m[0]`. A flat index round-trips as
`i = r * n + c` and `r, c = divmod(i, n)`.

### 5.4 Diagonals

In an `m × n` grid there are `m + n − 1` anti-diagonals (constant `r + c`, cells `(r, d − r)` for `0 <= d − r < n`) and the same number of main diagonals
(constant `r − c`, from `−(n−1)` to `m−1`). For `m = 3, n = 4`: `d = 0` → `[(0,0)]`; `d = 3` → `[(0,3), (1,2), (2,1)]`; `d = 5` → `[(2,3)]`. The same
constants identify the diagonals a queen attacks (topic 09) and, together with row and column, the boxes and lines in Sudoku-style validity checks.

---
<!-- /block:24_py_1_toolkit -->

<!-- block:24_py_2_problems -->
## Part 6 · The Eight Problems in Code — Spiral Two Ways, Markers, Staircase vs Binary Search, Encoding, Bounce

The solution files carry the full versions; these are the compact, tested forms of the parts that decide correctness, together with what happens when the key
line is wrong. Each was compared with a brute-force reference on hundreds of random matrices.

### 6.1 Spiral (003, 004): boundaries, or "turn when blocked"

```python
def spiral_bounds(m):
    if not m or not m[0]: return []
    top, bottom, left, right = 0, len(m) - 1, 0, len(m[0]) - 1
    out = []
    while top <= bottom and left <= right:
        out += m[top][left:right + 1]; top += 1                                  # top row, left → right
        out += [m[r][right] for r in range(top, bottom + 1)]; right -= 1         # right column, top → bottom
        if top <= bottom: out += m[bottom][left:right + 1][::-1]; bottom -= 1    # bottom row, right → left (guarded)
        if left <= right: out += [m[r][left] for r in range(bottom, top - 1, -1)]; left += 1   # left column (guarded)
    return out

def spiral_fill(n):                              # Problem 004 — turn clockwise when the next cell is off-grid or already written
    g = [[0] * n for _ in range(n)]
    dr, dc = (0, 1, 0, -1), (1, 0, -1, 0)
    r = c = d = 0
    for k in range(1, n * n + 1):
        g[r][c] = k
        nr, nc = r + dr[d], c + dc[d]
        if not (0 <= nr < n and 0 <= nc < n and g[nr][nc] == 0):
            d = (d + 1) % 4; nr, nc = r + dr[d], c + dc[d]
        r, c = nr, nc
    return g
# spiral_bounds([[1,2,3],[4,5,6],[7,8,9]]) = [1,2,3,6,9,8,7,4,5]     spiral_fill(3) = [[1,2,3],[8,9,4],[7,6,5]]
```

A second read-side version that *turns when blocked* (using a `seen` grid) gave the same output as the boundary version on 500 random shapes with 0–6 rows and columns.
The two guards are not optional: with them removed, `[[1, 2, 3]]` returns `[1, 2, 3, 2, 1]` and `[[1], [2], [3]]` returns `[1, 2, 3, 2]` — the last row or column is emitted twice. In
Problem 004 the same mistake is a double *write*, which is worse because nothing looks too long.

### 6.2 Set Matrix Zeroes (005): the border as scratch memory

```python
def set_zeroes(m):
    rows, cols = len(m), len(m[0])
    first_row = any(m[0][c] == 0 for c in range(cols))    # capture BEFORE the markers overwrite row 0 and column 0
    first_col = any(m[r][0] == 0 for r in range(rows))
    for r in range(1, rows):
        for c in range(1, cols):
            if m[r][c] == 0: m[r][0] = m[0][c] = 0        # mark this row and this column
    for r in range(1, rows):
        for c in range(1, cols):
            if m[r][0] == 0 or m[0][c] == 0: m[r][c] = 0  # apply markers to the interior only
    if first_row: m[0] = [0] * cols                       # last: the border itself
    if first_col:
        for r in range(rows): m[r][0] = 0
```

The order is the whole problem: capture the two flags first, mark and apply on the *interior* only (`range(1, …)`), and zero the border last. Matched a brute force that
uses two sets on 1,500 random matrices with zeros mixed in.

### 6.3 Search a 2D Matrix II (006): staircase, and why flattening is wrong

```python
def staircase(m, target):
    if not m or not m[0]: return False
    r, c = 0, len(m[0]) - 1                       # top-right: bigger to the left, smaller below
    while r < len(m) and c >= 0:
        v = m[r][c]
        if v == target: return True
        if v > target: c -= 1                     # everything below in this column is even bigger: drop the column
        else: r += 1                              # everything to the left in this row is even smaller: drop the row
    return False
```

Each step discards a row or a column, so at most `m + n − 1` cells are read. It matched a brute-force membership test for every target `0…39` on 2,000 random
row-and-column-sorted matrices. **Flattening and binary searching is a different problem's solution** (LC 74, where every row starts above the previous one's end): on the LC 240 example
matrix a flat binary search disagreed with the staircase for **12 of 32** targets. The top-right or bottom-left corner works; the top-left does not, because a "too small" verdict there
eliminates nothing.

### 6.4 Game of Life (007): old + 2·new

```python
def life(b):
    rows, cols = len(b), len(b[0])
    for r in range(rows):
        for c in range(cols):
            live = sum(b[r + dr][c + dc] % 2 for dr in (-1, 0, 1) for dc in (-1, 0, 1)
                       if (dr or dc) and 0 <= r + dr < rows and 0 <= c + dc < cols)     # % 2 recovers the ORIGINAL state
            if b[r][c] % 2 == 1 and live in (2, 3): b[r][c] += 2       # live and stays live: 1 → 3
            elif b[r][c] % 2 == 0 and live == 3:    b[r][c] += 2       # dead and is born:   0 → 2
    for r in range(rows):
        for c in range(cols): b[r][c] >>= 1                            # decode: the new state is the high bit
```

Overwriting each cell with its final value while scanning makes later cells read already-updated neighbours: on 800 random boards (2–6 per side) that naive in-place update was **wrong on 662**,
the encoded version on none. Reading a neighbour as `b[r][c]` instead of `b[r][c] % 2` during pass 1 miscounts as soon as a neighbour holds 2 or 3.

### 6.5 Diagonal Traverse (008): bounce, or bucket by `r + c`

```python
def diag_bounce(m):
    if not m or not m[0]: return []
    rows, cols = len(m), len(m[0]); r = c = 0; up = True; out = []
    for _ in range(rows * cols):
        out.append(m[r][c])
        if up:
            if c == cols - 1: r += 1; up = False       # right wall first (it also covers the corner) …
            elif r == 0:      c += 1; up = False       # … then the top wall
            else:             r -= 1; c += 1
        else:
            if r == rows - 1: c += 1; up = True        # bottom wall first …
            elif c == 0:      r += 1; up = True        # … then the left wall
            else:             r += 1; c -= 1
    return out
# diag_bounce([[1,2,3],[4,5,6],[7,8,9]]) = [1, 2, 4, 7, 5, 3, 6, 8, 9]
```

It equalled the bucket version (group by `r + c`, reverse the even buckets) on 800 random shapes. The order of the wall checks matters at the corners: checking the top wall *before*
the right wall when going up (and the left before the bottom when going down) sends the walk off the matrix — on a 3 × 3 input that variant raised `IndexError`.

### 6.6 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Rotate counter-clockwise / 180°." | Reverse each row then transpose (or transpose then reverse the row order) / reverse rows and each row. |
| "Rotate a non-square matrix." | Return a new matrix: `zip(*m[::-1])` — the shape changes, so it cannot be in place. |
| "Rotate `k` times." | Reduce `k` mod 4 first. |
| "Search a matrix sorted as one sequence (LC 74)." | Binary search on the flat index, `m[mid // n][mid % n]` — O(log mn). |
| "Count live neighbours efficiently." | A `dirs` tuple plus a bounds check; for huge sparse boards, a set of live cells. |
| "Sum of any rectangle, repeatedly." | A 2-D prefix-sum table (topic 04). |

---
<!-- /block:24_py_2_problems -->

<!-- problem-map:start -->
## Part 7 · Every Problem in This Topic, by Pattern

Eight problems, three skills (exact index arithmetic · boundary-tracked traversal · scratch space inside the structure). Each **Trap** is a mistake documented in that problem's solution file.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Transpose Matrix](PyDSA/24_matrix/001_transpose_matrix_solution.py) <br>LC 867 · Easy | Transpose is a shape change | `result` is `n × m`: `result[j][i] = matrix[i][j]` (or `[list(r) for r in zip(*m)]`). Only a square matrix could be transposed in place. **Trap:** writing back in place for a non-square input; sizing `result` as `m × n`; returning `zip` tuples instead of lists. |
| [002 · Rotate Image](PyDSA/24_matrix/002_rotate_image_solution.py) <br>LC 48 · Medium | Transpose, then reverse each row | Swap the upper triangle only (`j > i`), then reverse every row: clockwise. Or cycle four cells per ring position. **Trap:** transposing all pairs (each swap undone); reversing the rows before transposing, or reversing the row *order* after (counter-clockwise); allocating a new matrix; double-cycling a ring's corner. |
| [003 · Spiral Matrix](PyDSA/24_matrix/003_spiral_matrix_solution.py) <br>LC 54 · Medium | Four shrinking boundaries | `top/bottom/left/right`; each side is walked, then the boundary it exhausted moves in; the last two passes are guarded. **Trap:** no `top <= bottom` / `left <= right` guards (the last row or column is emitted twice); `range(left, right)` dropping the last cell; shrinking a boundary before using it; a reverse `range` missing the `-1` stop. |
| [004 · Spiral Matrix II](PyDSA/24_matrix/004_spiral_matrix_ii_solution.py) <br>LC 59 · Medium | The same boundaries, writing | Write `1..n²` in spiral order, incrementing after *every* write; or turn clockwise when the next cell is off-grid or non-zero. **Trap:** incrementing per side instead of per write; the missing guards, now a double *write*; `[[0] * n] * n`. |
| [005 · Set Matrix Zeroes](PyDSA/24_matrix/005_set_matrix_zeroes_solution.py) <br>LC 73 · Medium | The border as markers | Capture "row 0 / column 0 had a zero", mark from the interior, apply markers to the interior, zero the border last. **Trap:** capturing the flags after marking; passes that include row 0 / column 0; zeroing the border before the interior; allocating a copy. |
| [006 · Search a 2D Matrix II](PyDSA/24_matrix/006_search_a_2d_matrix_ii_solution.py) <br>LC 240 · Medium | Staircase from the top-right | Compare with the corner: bigger → drop the column, smaller → drop the row; O(m + n). **Trap:** starting top-left (eliminates nothing); flattening and binary searching (LC 74's technique — wrong here); inconsistent bounds; moving in the wrong direction. |
| [007 · Game of Life](PyDSA/24_matrix/007_game_of_life_solution.py) <br>LC 289 · Medium | Encode `old + 2*new` | Count neighbours with `% 2`, add 2 to the cells whose new state is live, then `>>= 1`. **Trap:** overwriting with the final value while scanning (wrong on 662 of 800 random boards); reading a neighbour without `% 2`; forgetting the decode pass; the encoding backwards (`2*old + new`). |
| [008 · Diagonal Traverse](PyDSA/24_matrix/008_diagonal_traverse_solution.py) <br>LC 498 · Medium | Bounce off four walls | A `going_up` flag; check the right/bottom wall before the top/left wall so corners resolve; or bucket by `r + c` and reverse the even buckets. **Trap:** inconsistent wall-check order between the two directions; not flipping the direction on a bounce; reversing the odd buckets instead of the even; iterating the bucket build in the wrong order. |

---
<!-- problem-map:end -->


## Checklist Before Leaving This Topic <!--ca-->

- [ ] Build a grid with a comprehension, and copy it row by row (`[r[:] for r in g]`) — never `copy.copy` or `*` on the outer list <!--ca-->
- [ ] Write all four rotations as `zip` one-liners and as in-place swaps, and derive the `(i, j)` destinations <!--ca-->
- [ ] Explain why negative indexes make a missing bounds check wrong *silently* on the top and left edges only <!--ca-->
- [ ] Write the spiral both ways (four boundaries with two guards; direction vectors turning when blocked) <!--ca-->
- [ ] Order the Set Matrix Zeroes passes correctly: capture the border flags, mark, apply to the interior, zero the border last <!--ca-->
- [ ] Explain why LC 240 uses a staircase and LC 74 a flat binary search, and why the top-left corner cannot start a staircase <!--ca-->
- [ ] Encode Game of Life as `old + 2*new` and read neighbours with `% 2` <!--ca-->
- [ ] Count `m + n − 1` diagonals and use `r + c` / `r − c` as their keys <!--ca-->
