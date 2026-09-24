"""
================================================================================
SOLUTION · LeetCode 308 · Range Sum Query 2D - Mutable                    [Hard]
https://leetcode.com/problems/range-sum-query-2d-mutable/
================================================================================

THE CORE IDEA
--------------
A 2D Fenwick tree is literally a Fenwick tree of Fenwick trees: `tree[i][j]`
plays the same role as 001's `tree[i]`, except now BOTH the row and column
indices are walked with the `i & -i` trick. `update(row, col, delta)` walks
UP in rows, and for each ancestor row, walks UP in columns (nested loop).
`_prefix(row, col)` — "sum of the rectangle from (0,0) to (row-1, col-1)
inclusive" — walks DOWN in rows, and for each ancestor row, walks DOWN in
columns.

`sumRegion` reduces to FOUR prefix queries combined by 2D
inclusion-exclusion — the identical `+D +A -B -C` formula from topic 04's
static 2D prefix sum, just computed via tree walks instead of read from a
precomputed table:

    sumRegion(r1, c1, r2, c2)
        = prefix(r2+1, c2+1)        [D: everything up to the far corner]
          - prefix(r1, c2+1)         [A: subtract the rows above r1]
          - prefix(r2+1, c1)         [B: subtract the columns left of c1]
          + prefix(r1, c1)           [add back the doubly-subtracted corner]


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): raw matrix, O(1) update,
O(m*n) sumRegion (scan the whole rectangle every call). With up to 5000
calls over a 200x200 matrix, worst case ~2*10^8 cell reads.

Approach 0b (full 2D prefix-sum table, priced, not coded): O(1) sumRegion,
but a single `update` must propagate through every prefix-sum cell
"downstream" of it (up to O(m*n) cells) to stay correct. Fails once
`update` is called repeatedly.

Approach 1 (chosen) — 2D Fenwick tree: O(log m * log n) for both update and
sumRegion. See THE CORE IDEA.

Approach 2 (alternative, not coded) — a 2D segment tree, or an array of `m`
independent 1D BITs (one per row) combined with a per-column merge: more
code for the same asymptotic bound; the row-major 2D BIT above is the
standard, leanest answer for a SUM-only 2D range-update/range-query
problem.


================================================================================
STEP BY STEP TRACE — matrix = [[1, 2], [3, 4]], m=n=2
================================================================================
All indices below are the 1-indexed tree's; tree[i][j] for i,j in 1..2.
Build via four update() calls in row-major order.

    update(0, 0, 1):  delta=1, i starts at row+1=1, j starts at col+1=1
        i=1: j=1: tree[1][1]+=1 -> 1;  j += (1&-1)=1 -> j=2
             j=2: tree[1][2]+=1 -> 1;  j += (2&-2)=2 -> j=4>2, stop inner
             i += (1&-1)=1 -> i=2
        i=2: j=1: tree[2][1]+=1 -> 1;  j=2: tree[2][2]+=1 -> 1;  j=4 stop
             i += (2&-2)=2 -> i=4>2, stop
        tree = { [1][1]:1, [1][2]:1, [2][1]:1, [2][2]:1 }

    update(0, 1, 2):  delta=2, i starts 1, j starts col+1=2
        i=1: j=2: tree[1][2]+=2 -> 3;  j=4 stop;  i=2
        i=2: j=2: tree[2][2]+=2 -> 3;  j=4 stop;  i=4 stop
        tree = { [1][1]:1, [1][2]:3, [2][1]:1, [2][2]:3 }

    update(1, 0, 3):  delta=3, i starts row+1=2, j starts 1
        i=2: j=1: tree[2][1]+=3 -> 4;  j=2: tree[2][2]+=3 -> 6;  j=4 stop
             i=4 stop
        tree = { [1][1]:1, [1][2]:3, [2][1]:4, [2][2]:6 }

    update(1, 1, 4):  delta=4, i=2, j=2
        i=2: j=2: tree[2][2]+=4 -> 10;  j=4 stop;  i=4 stop
        tree = { [1][1]:1, [1][2]:3, [2][1]:4, [2][2]:10 }   <- FINAL

sumRegion(0, 0, 1, 1)  (whole matrix, want 1+2+3+4=10)
    prefix(2, 2): i=2: j=2: s += tree[2][2]=10 -> s=10;
                       j -= (2&-2)=2 -> j=0, stop inner
                  i -= (2&-2)=2 -> i=0, stop         => prefix(2,2) = 10
    prefix(0, 2) = 0  (row loop never runs, row1=0)
    prefix(2, 0) = 0  (col loop never runs, col1=0)
    prefix(0, 0) = 0
    sumRegion = 10 - 0 - 0 + 0 = 10                          MATCHES [OK]

sumRegion(0, 0, 0, 1)  (row 0 only, want 1+2=3)
    prefix(1, 2): i=1: j=2: s += tree[1][2]=3 -> s=3;
                       j -= 2 -> j=0, stop
                  i -= (1&-1)=1 -> i=0, stop          => prefix(1,2) = 3
    prefix(0, 2) = 0, prefix(1, 0) = 0, prefix(0, 0) = 0
    sumRegion = 3 - 0 - 0 + 0 = 3                             MATCHES [OK]

update(0, 0, 10):  delta = 10 - 1 = 9, propagate same paths as the first update
    tree[1][1] -> 10, tree[1][2] -> 12, tree[2][1] -> 13, tree[2][2] -> 19

sumRegion(0, 0, 1, 1) now (want 10+2+3+4=19)
    prefix(2,2): tree[2][2] = 19  => 19 - 0 - 0 + 0 = 19       MATCHES [OK]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          update            sumRegion         Space
    --------------------------------------------------------------------------
    Raw matrix, resum each query      O(1)              O(m*n)            O(m*n)
    Full 2D prefix-sum table          O(m*n) worst case  O(1)              O(m*n)
    2D Fenwick tree ✅                O(log m * log n)  O(log m * log n)  O(m*n)

    "Mutates input?" n/a — design problem, state lives inside the class.


================================================================================
EDGE CASES
================================================================================
    1x1 matrix                  Degenerate BIT (size 2x2 internal), still
                                 correct — exercises the base case of both
                                 nested loops.
    Single row or single column Only one dimension's `i & -i` loop ever
                                 does real work; the other dimension's loop
                                 still runs but over a size-1 range.
    Full-matrix sumRegion       (0, 0, m-1, n-1) — the A/B correction terms
                                 both collapse to 0, reducing to a single
                                 prefix(m, n) call; a good sanity check that
                                 inclusion-exclusion is wired correctly.
    Repeated update to the
    same cell                   Delta must be computed against the CURRENT
                                 stored value, not the ORIGINAL one — same
                                 caution as 001.
    Negative values              -1000..1000; sums and deltas must handle
                                 negative numbers throughout.


================================================================================
COMMON MISTAKES
================================================================================
1. Getting the inclusion-exclusion SIGNS wrong in sumRegion — the most
   common bug here. Draw the rectangle: D (0,0)-to-(r2,c2) minus the strip
   ABOVE row1 minus the strip LEFT of col1 double-subtracts the corner
   rectangle above-and-left of (row1, col1), so it must be added back once.

2. Swapping row/col index order somewhere in the nested loops (using
   `tree[col][row]` in one place and `tree[row][col]` in another) — silently
   produces plausible-looking but wrong sums on non-square matrices, which
   is why testing with a non-square matrix (not just square, per topic
   guide's general discipline) matters.

3. Mixing 001's 1D convention accidentally: forgetting BOTH dimensions need
   the `+1` 1-indexing offset (row+1 for the tree's row axis, col+1 for the
   tree's column axis), not just one.

4. Rebuilding the WHOLE tree from scratch on every `update` call (easy to
   accidentally do if `update` re-runs the full constructor logic) instead
   of doing the O(log m * log n) delta-propagation walk — defeats the
   entire point of the structure.

5. Off-by-one on the prefix() boundary convention, exactly as in 001:
   `_prefix(row, col)` here means "sum of the first `row` rows and first
   `col` columns" (1-indexed COUNTS), so `sumRegion`'s calls need `r2+1`,
   `c2+1` etc., not `r2`, `c2` directly.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
Q: What if the matrix were mostly zeros (sparse) and enormous
   (e.g. 10^6 x 10^6)?
A: A hashmap-backed BIT (only storing nonzero tree entries) or coordinate
   compression of the nonzero rows/columns, same idea as 005/006's
   coordinate compression for a sparse coordinate axis.

Q: Could you support range UPDATE (add delta to every cell in a rectangle)
   as well as range query?
A: Generalizes 001's difference-array-BIT trick to 2D: four coordinated
   point updates on a difference-array 2D BIT, using a slightly more
   involved (but standard) 2D range-update/range-query BIT formula.

Q: Why not a 2D segment tree?
A: Same reasoning as 001 vs a 1D segment tree — sum has an inverse, so a
   BIT is strictly simpler and smaller-constant than a segment tree here. A
   2D segment tree would be the right call only if the aggregate were
   something without an inverse, like range max.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 307  Range Sum Query - Mutable        — this topic, 001, the 1D version
    LC 304  Range Sum Query 2D - Immutable   — topic 04, the STATIC version
    LC 699  Falling Squares                  — this topic, 005, segment tree, non-invertible aggregate
    LC 218  The Skyline Problem              — this topic, 006, sweep-line / segment tree
================================================================================
"""

import random
import time


class NumMatrix:
    """2D Fenwick tree. O(log m * log n) update / sumRegion. See THE CORE IDEA."""

    def __init__(self, matrix: list[list[int]]):
        self.m = len(matrix)
        self.n = len(matrix[0]) if self.m else 0
        self.matrix = [[0] * self.n for _ in range(self.m)]  # current values
        self.tree = [[0] * (self.n + 1) for _ in range(self.m + 1)]  # 1-indexed
        for r in range(self.m):
            for c in range(self.n):
                self.update(r, c, matrix[r][c])

    def update(self, row: int, col: int, val: int) -> None:
        delta = val - self.matrix[row][col]
        self.matrix[row][col] = val
        i = row + 1
        while i <= self.m:
            j = col + 1
            while j <= self.n:
                self.tree[i][j] += delta
                j += j & (-j)
            i += i & (-i)

    def _prefix(self, row: int, col: int) -> int:
        """Sum of the rectangle (0,0)..(row-1,col-1) inclusive."""
        s = 0
        i = row
        while i > 0:
            j = col
            while j > 0:
                s += self.tree[i][j]
                j -= j & (-j)
            i -= i & (-i)
        return s

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        return (
            self._prefix(row2 + 1, col2 + 1)
            - self._prefix(row1, col2 + 1)
            - self._prefix(row2 + 1, col1)
            + self._prefix(row1, col1)
        )


# ------------------------------------------------------------------------
# Oracles / alternatives used only for the tests and benchmark below.
# ------------------------------------------------------------------------
class NumMatrixNaive:
    """✗ Priced-not-shipped: O(1) update, O(m*n) sumRegion. Correctness
    oracle and the subject of the benchmark below."""

    def __init__(self, matrix: list[list[int]]):
        self.matrix = [row[:] for row in matrix]

    def update(self, row: int, col: int, val: int) -> None:
        self.matrix[row][col] = val

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        return sum(
            self.matrix[r][c]
            for r in range(row1, row2 + 1)
            for c in range(col1, col2 + 1)
        )


def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # LeetCode's example.
    # ------------------------------------------------------------------
    print("--- LeetCode example ---")
    matrix = [
        [3, 0, 1, 4, 2],
        [5, 6, 3, 2, 1],
        [1, 2, 0, 1, 5],
        [4, 1, 0, 1, 7],
        [1, 0, 3, 0, 5],
    ]
    nm = NumMatrix(matrix)
    ok = nm.sumRegion(2, 1, 4, 3) == 8
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  sumRegion(2,1,4,3) before update -> {nm.sumRegion(2, 1, 4, 3)} (want 8)")

    nm.update(3, 2, 2)
    ok = nm.sumRegion(2, 1, 4, 3) == 10
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  sumRegion(2,1,4,3) after update(3,2,2) -> {nm.sumRegion(2, 1, 4, 3)} (want 10)")

    # ------------------------------------------------------------------
    # Edge cases.
    # ------------------------------------------------------------------
    print("\n--- edge cases ---")
    single = NumMatrix([[7]])
    ok = single.sumRegion(0, 0, 0, 0) == 7
    single.update(0, 0, -3)
    ok &= single.sumRegion(0, 0, 0, 0) == -3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1x1 matrix, update to negative value")

    row_vec = NumMatrix([[1, 2, 3, 4]])  # 1 row, 4 cols
    ok = row_vec.sumRegion(0, 1, 0, 2) == 5
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  single-row matrix region sum")

    col_vec = NumMatrix([[1], [2], [3], [4]])  # 4 rows, 1 col
    ok = col_vec.sumRegion(1, 0, 3, 0) == 9
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  single-column matrix region sum")

    non_square = NumMatrix([[1, 2, 3], [4, 5, 6]])  # 2 rows, 3 cols
    ok = non_square.sumRegion(0, 0, 1, 2) == 21
    non_square.update(1, 1, 100)
    ok &= non_square.sumRegion(0, 0, 1, 2) == 21 - 5 + 100
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  non-square matrix: row/col index order not swapped")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the O(m*n) naive oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs naive oracle (300 ops, 15x12 matrix) ---")
    rng = random.Random(308)
    m, n = 15, 12
    start = [[rng.randint(-1000, 1000) for _ in range(n)] for _ in range(m)]
    fast = NumMatrix(start)
    slow = NumMatrixNaive(start)
    mismatch = False
    for _ in range(300):
        if rng.random() < 0.5:
            r, c = rng.randint(0, m - 1), rng.randint(0, n - 1)
            v = rng.randint(-1000, 1000)
            fast.update(r, c, v)
            slow.update(r, c, v)
        else:
            r1, r2 = sorted((rng.randint(0, m - 1), rng.randint(0, m - 1)))
            c1, c2 = sorted((rng.randint(0, n - 1), rng.randint(0, n - 1)))
            if fast.sumRegion(r1, c1, r2, c2) != slow.sumRegion(r1, c1, r2, c2):
                mismatch = True
    ok = not mismatch
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 randomized ops, no mismatch vs naive oracle")

    # ------------------------------------------------------------------
    # BENCHMARK — O(log m * log n) 2D BIT vs O(m*n) naive resum.
    # ------------------------------------------------------------------
    print("\n--- benchmark: 2D BIT vs naive O(m*n) resum, mixed workload ---")
    print(f"  {'m x n':>10} {'ops':>8} {'BIT (ms)':>12} {'naive (ms)':>12} {'speedup':>10}")
    for dim in (20, 60, 150):
        rng = random.Random(2)
        m = n = dim
        start = [[rng.randint(-1000, 1000) for _ in range(n)] for _ in range(m)]
        n_ops = 400
        ops = []
        for _ in range(n_ops):
            if rng.random() < 0.5:
                ops.append(("update", rng.randint(0, m - 1), rng.randint(0, n - 1), rng.randint(-1000, 1000)))
            else:
                r1, r2 = sorted((rng.randint(0, m - 1), rng.randint(0, m - 1)))
                c1, c2 = sorted((rng.randint(0, n - 1), rng.randint(0, n - 1)))
                ops.append(("query", r1, c1, r2, c2))

        fast = NumMatrix(start)
        t0 = time.perf_counter()
        for op in ops:
            if op[0] == "update":
                _, r, c, v = op
                fast.update(r, c, v)
            else:
                _, r1, c1, r2, c2 = op
                fast.sumRegion(r1, c1, r2, c2)
        bit_ms = (time.perf_counter() - t0) * 1000

        slow = NumMatrixNaive(start)
        t0 = time.perf_counter()
        for op in ops:
            if op[0] == "update":
                _, r, c, v = op
                slow.update(r, c, v)
            else:
                _, r1, c1, r2, c2 = op
                slow.sumRegion(r1, c1, r2, c2)
        naive_ms = (time.perf_counter() - t0) * 1000

        speedup = naive_ms / bit_ms if bit_ms > 0 else float("inf")
        print(f"  {f'{m}x{n}':>10} {n_ops:>8} {bit_ms:>12.2f} {naive_ms:>12.2f} {speedup:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
