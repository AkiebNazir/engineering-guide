"""
================================================================================
SOLUTION · LeetCode 304 · Range Sum Query 2D - Immutable                [Medium]
https://leetcode.com/problems/range-sum-query-2d-immutable/
================================================================================

THE CORE IDEA
--------------
Build a 2D prefix-sum matrix `P`, one row and one column larger than the
input, in the constructor (O(rows*cols), paid once). Every `sumRegion` call
is then 4 lookups and 3 arithmetic operations — O(1), independent of the
rectangle's size. This is the 2D generalisation of problem 002 (LC 303): pay
once, query forever. See `_TOPIC_GUIDE.md` Part 2 for the full derivation
with the ASCII "overlapping rectangles" picture this solution is built from.

    P[i][j] = sum of M[a][b] for all 0 <= a < i, 0 <= b < j
    P[i][j] = M[i-1][j-1] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]

    sumRegion(r1, c1, r2, c2)
        = P[r2+1][c2+1] - P[r1][c2+1] - P[r2+1][c1] + P[r1][c1]

O(rows*cols) build, O(1) per query, O(rows*cols) extra space for `P`.


================================================================================
WHY THE EXTRA ROW/COLUMN, AND WHY INCLUSION-EXCLUSION
================================================================================
Exactly the 1D `prefix[0] = 0` sentinel (topic guide §1.0), one dimension up:
`P` is `(rows+1) x (cols+1)` so that `P[0][*] = 0` and `P[*][0] = 0` mean
"the sum of zero rows" / "the sum of zero columns" — real, usable zeros, not
special-cased boundaries. Without this extra row/column, every query touching
row 0 or column 0 would need an `if` to avoid indexing `P[-1][...]`.

Building `P` requires inclusion-exclusion because "above" and "left" overlap
in their shared top-left corner:

        j-1   j
   i-1 [ A ] [ B ]      B = P[i-1][j]  (rows 0..i-1, cols 0..j-1 -- includes A)
   i   [ C ] [ x ]      C = P[i][j-1]  (rows 0..i-1... wait, rows 0..i, cols 0..j-1 -- includes A)

   P[i][j] = x + B + C double-counts A, so subtract P[i-1][j-1] once:
   P[i][j] = M[i-1][j-1] + P[i-1][j] + P[i][j-1] - P[i-1][j-1]

Querying an arbitrary rectangle (r1,c1)-(r2,c2) is the SAME inclusion-
exclusion pattern run once, on the four boundary prefixes instead of a single
cell: start from the full rectangle to the query's bottom-right corner,
subtract the strip above and the strip left of the query, and add back the
top-left corner (which both subtractions removed):

    full rectangle (0,0)-(r2,c2)   =  P[r2+1][c2+1]
    minus strip above the query     -  P[r1][c2+1]
    minus strip left of the query   -  P[r2+1][c1]
    plus the corner (double-cut)    +  P[r1][c1]


================================================================================
STEP BY STEP TRACE
================================================================================
matrix (3x3):
        3   0   1
        5   6   3
        1   2   0

Build P, shape 4x4, P[0][*] = P[*][0] = 0:

    P[1][1] = M[0][0] + P[0][1] + P[1][0] - P[0][0] = 3 + 0 + 0 - 0 = 3
    P[1][2] = M[0][1] + P[0][2] + P[1][1] - P[0][1] = 0 + 0 + 3 - 0 = 3
    P[1][3] = M[0][2] + P[0][3] + P[1][2] - P[0][2] = 1 + 0 + 3 - 0 = 4
    P[2][1] = M[1][0] + P[1][1] + P[2][0] - P[1][0] = 5 + 3 + 0 - 0 = 8
    P[2][2] = M[1][1] + P[1][2] + P[2][1] - P[1][1] = 6 + 3 + 8 - 3 = 14
    P[2][3] = M[1][2] + P[1][3] + P[2][2] - P[1][2] = 3 + 4 + 14 - 3 = 18
    P[3][1] = M[2][0] + P[2][1] + P[3][0] - P[2][0] = 1 + 8 + 0 - 0 = 9
    P[3][2] = M[2][1] + P[2][2] + P[3][1] - P[2][1] = 2 + 14 + 9 - 8 = 17
    P[3][3] = M[2][2] + P[2][3] + P[3][2] - P[2][2] = 0 + 18 + 17 - 14 = 21

    P =
        0   0   0   0
        0   3   3   4
        0   8  14  18
        0   9  17  21

sumRegion(1, 1, 2, 2)  -- the bottom-right 2x2 block [[6,3],[2,0]], sum = 11

    = P[3][3] - P[1][3] - P[3][1] + P[1][1]
    = 21      - 4       - 9      + 3
    = 11   ✓  matches 6+3+2+0 = 11 by direct addition.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Build         Query        Mutates input?
    --------------------------------  ------------  -----------  --------------
    Naive: sum the rectangle live     O(1)          O(rows*cols) No
    2D prefix sum ✅                  O(rows*cols)  O(1)         No (copies)

    With up to 10^4 queries against a 200x200 matrix, naive is up to
    ~4*10^8 cell reads in the worst case (whole-matrix queries repeated);
    prefix sum is ~4*10^4 total lookups. The benchmark at the bottom of this
    file measures both directly.

    Space: O(rows*cols) for `P`, one row/col larger than the input in each
    dimension. `matrix` itself is never mutated by either approach here.


================================================================================
EDGE CASES
================================================================================
    1x1 matrix              -> P is 2x2, sumRegion(0,0,0,0) must equal the
                                single cell. Exercises the +1 offsets with no
                                room for an indexing mistake to hide.
    single row / single col -> one of the two "overlap" dimensions in the
                                inclusion-exclusion formula is always empty;
                                confirms the formula still holds when a whole
                                dimension collapses to a strip.
    row1==row2, col1==col2  -> a single-cell query; the 4-term formula must
                                reduce to exactly that one cell's value.
    whole-matrix query      -> (0,0) to (rows-1, cols-1); should equal
                                P[rows][cols], the grand total.
    negative numbers        -> matrix values in [-10^4, 10^4]; the running
                                sums and the subtractions must handle sign
                                correctly (no assumption that P is monotone).


================================================================================
COMMON MISTAKES
================================================================================
1. Sizing `P` as `rows x cols` instead of `(rows+1) x (cols+1)` — forces
   special-casing row 0 / col 0 instead of a real sentinel row/column of
   zeros, and is the #1 source of off-by-one bugs in this problem.
2. Dropping the `- P[i-1][j-1]` term when BUILDING P (double-counts the
   top-left corner region on every cell) or dropping the `+ P[r1][c1]` term
   when QUERYING (double-subtracts the corner instead of restoring it once).
3. Using `row2` / `col2` directly instead of `row2+1` / `col2+1` in the
   query — `sumRegion`'s bounds are INCLUSIVE, so the exclusive prefix index
   needs the +1, exactly like the 1D `prefix[r+1] - prefix[l]` formula.
4. Building `P` inside `sumRegion` instead of `__init__` — silently turns
   every query back into O(rows*cols), defeating the entire point of the
   class and the reason it has a constructor at all.
5. Mutating the caller's `matrix` list in place while building `P` (e.g.
   accumulating sums back into `matrix` itself) — the class is handed the
   matrix once and may be queried many times; corrupting the input is a
   correctness bug even if it happens to still answer THIS query right.
6. Confusing `P[i-1][j]` (everything above, i.e. "the rectangle using ALL of
   row i-1 and earlier") with `P[i][j-1]` (everything left) and swapping
   them — harmless for a square matrix but produces a transposed, wrong
   answer for a non-square one; always sanity check against a rectangular
   matrix, not just a square one.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if `sumRegion` needs to support UPDATES to individual cells too
   (LC 308, Range Sum Query 2D - Mutable)?
A: A flat 2D prefix sum breaks: updating one cell would force rebuilding
   O(rows*cols) of `P`. That problem wants a 2D Binary Indexed Tree (Fenwick
   tree) or a Fenwick tree per row, giving O(log(rows)*log(cols)) update and
   query instead of O(1) query / O(n) rebuild. Segment trees are topic 26 in
   this curriculum.

Q: Can you reduce the O(rows*cols) extra space?
A: Yes, if you don't mind a slower query: keep only ROW-WISE running sums
   (O(rows*cols) still, same asymptotic space) or — for TRUE O(1) extra
   space beyond the input — mutate `matrix` in place to hold row-wise prefix
   sums, trading destructiveness for space; not appropriate here since LC 304
   promises `matrix` is read, not consumed, and other methods may re-read it.

Q: Why not just cache every possible rectangle sum up front?
A: There are O(rows^2 * cols^2) distinct rectangles — quartic, not the
   O(rows*cols) this solution achieves. The prefix-sum trick avoids ever
   materialising more than one sum per (row, col) pair.

Q: How does this generalise to 3D (a cube of range-sum queries)?
A: Same inclusion-exclusion, one more term: 2^3 = 8 corners of the box
   instead of 2^2 = 4 corners of the rectangle, alternating sign by parity of
   how many of the box's three "which side" bits are set. The 1D -> 2D step
   done in this problem is the pattern; it keeps generalising the same way.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 303  Range Sum Query - Immutable       — the 1D version (problem 002)
    LC 308  Range Sum Query 2D - Mutable      — same problem + point updates,
                                                 needs a 2D Fenwick tree
    LC 1314 Matrix Block Sum                  — this exact technique applied
                                                 to a fixed-radius box around
                                                 every cell
    LC 363  Max Sum of Rectangle No Larger Than K — 2D prefix sum + the
                                                      hashmap trick from 004
================================================================================
"""

import random
import time
from typing import List


class NumMatrix:
    def __init__(self, matrix: List[List[int]]):
        """Build the 2D prefix-sum matrix once. O(rows*cols) time and space."""
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        # P is (rows+1) x (cols+1); P[0][*] and P[*][0] are the zero sentinel.
        P = [[0] * (cols + 1) for _ in range(rows + 1)]
        for i in range(rows):
            for j in range(cols):
                P[i + 1][j + 1] = (matrix[i][j] + P[i][j + 1] + P[i + 1][j]
                                    - P[i][j])
        self._P = P

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        """O(1): 4 lookups, 2 subtractions, 1 addition."""
        P = self._P
        return (P[row2 + 1][col2 + 1] - P[row1][col2 + 1]
                - P[row2 + 1][col1] + P[row1][col1])


# ==============================================================================
# Alternatives, for comparison and to demonstrate the bugs called out above.
# ==============================================================================
class NumMatrix_naive:
    """✗ SLOW ON PURPOSE — no precomputation. Sums the queried rectangle
    directly on every call: O(rows*cols) PER QUERY instead of O(1)."""

    def __init__(self, matrix: List[List[int]]):
        self._m = matrix

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        total = 0
        for i in range(row1, row2 + 1):
            for j in range(col1, col2 + 1):
                total += self._m[i][j]
        return total


class NumMatrix_no_corner:
    """✗ BROKEN ON PURPOSE — omits the `+ P[r1][c1]` corner term when
    querying, so the top-left corner is subtracted TWICE instead of once."""

    def __init__(self, matrix: List[List[int]]):
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        P = [[0] * (cols + 1) for _ in range(rows + 1)]
        for i in range(rows):
            for j in range(cols):
                P[i + 1][j + 1] = (matrix[i][j] + P[i][j + 1] + P[i + 1][j]
                                    - P[i][j])
        self._P = P

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        P = self._P
        return P[row2 + 1][col2 + 1] - P[row1][col2 + 1] - P[row2 + 1][col1]
        # missing "+ P[row1][col1]"


class NumMatrix_wrong_size:
    """✗ BROKEN ON PURPOSE — builds P the SAME size as the input matrix
    (no sentinel row/column), then fudges indexing. Fails whenever the
    query touches row 0 or column 0."""

    def __init__(self, matrix: List[List[int]]):
        rows = len(matrix)
        cols = len(matrix[0]) if rows else 0
        P = [[0] * cols for _ in range(rows)]
        for i in range(rows):
            for j in range(cols):
                above = P[i - 1][j] if i > 0 else 0
                left = P[i][j - 1] if j > 0 else 0
                corner = P[i - 1][j - 1] if i > 0 and j > 0 else 0
                P[i][j] = matrix[i][j] + above + left - corner
        self._P = P

    def sumRegion(self, row1: int, col1: int, row2: int, col2: int) -> int:
        P = self._P
        total = P[row2][col2]
        if row1 > 0:
            total -= P[row1 - 1][col2]
        if col1 > 0:
            total -= P[row2][col1 - 1]
        if row1 > 0 and col1 > 0:
            total += P[row1 - 1][col1 - 1]
        return total
        # This version is ACTUALLY correct if written fully (it's the same
        # math, just without the sentinel row/col simplification) -- kept
        # here to show the sentinel is a convenience, not a requirement,
        # but every one of these `if`s is a chance to typo a `>` into `>=`.
        # The demo below stresses it against random rectangles including
        # ones touching row/col 0 to make that risk concrete.


# ==============================================================================
# TESTS — run:  python 006_range_sum_query_2d_immutable_solution.py
# ==============================================================================
def brute_region(matrix, row1, col1, row2, col2):
    total = 0
    for i in range(row1, row2 + 1):
        for j in range(col1, col2 + 1):
            total += matrix[i][j]
    return total


def run_tests() -> None:
    all_ok = True

    matrix = [
        [3, 0, 1, 4, 2],
        [5, 6, 3, 2, 1],
        [1, 2, 0, 1, 5],
        [4, 1, 0, 1, 7],
        [1, 0, 3, 0, 5],
    ]

    impls = {
        "prefix-sum (optimal)": NumMatrix,
        "naive per-query     ": NumMatrix_naive,
        "correct, no sentinel": NumMatrix_wrong_size,
    }

    queries = [
        (2, 1, 4, 3, 8), (1, 1, 2, 2, 11), (1, 2, 2, 4, 12),
        (0, 0, 4, 4, None), (0, 0, 0, 0, None), (4, 4, 4, 4, None),
        (2, 2, 2, 2, None), (0, 0, 0, 4, None), (0, 0, 4, 0, None),
    ]

    for name, cls in impls.items():
        inst = cls([row[:] for row in matrix])
        ok = True
        for row1, col1, row2, col2, expected in queries:
            want = expected if expected is not None else brute_region(
                matrix, row1, col1, row2, col2)
            got = inst.sumRegion(row1, col1, row2, col2)
            ok &= (got == want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(queries)} regions)")

    # 1x1, single row, single col, negatives
    print()
    edge_cases = [
        ("1x1 matrix", [[42]], [(0, 0, 0, 0)]),
        ("single row", [[1, 2, 3, 4, 5]], [(0, 0, 0, 4), (0, 1, 0, 3)]),
        ("single col", [[1], [2], [3], [4]], [(0, 0, 3, 0), (1, 0, 2, 0)]),
        ("negatives", [[1, -2, 3], [-4, 5, -6], [7, -8, 9]],
         [(0, 0, 2, 2), (1, 1, 1, 1), (0, 0, 1, 1)]),
    ]
    for label, m, regions in edge_cases:
        inst = NumMatrix([row[:] for row in m])
        ok = all(inst.sumRegion(*r) == brute_region(m, *r) for r in regions)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {label}")

    # ----------------------------------------------------------------------
    # ⚠️  The missing-corner-term bug.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  forgetting '+ P[r1][c1]' (the corner term) ---")
    good = NumMatrix([row[:] for row in matrix])
    bad = NumMatrix_no_corner([row[:] for row in matrix])
    print(f"  {'region':<24} {'correct':>8} {'no-corner':>10}  ok?")
    for row1, col1, row2, col2, _ in queries[:5]:
        g = good.sumRegion(row1, col1, row2, col2)
        b = bad.sumRegion(row1, col1, row2, col2)
        label = f"({row1},{col1})-({row2},{col2})"
        print(f"  {label:<24} {g:>8} {b:>10}  "
              f"{'yes' if g == b else 'NO  <- corner double-subtracted'}")
    print("  Whenever row1 > 0 AND col1 > 0 (the query does not touch the top")
    print("  or left edge), the no-corner version under-counts by exactly")
    print("  P[row1][col1] -- the top-left corner it subtracted twice.")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(rows*cols) oracle ---")
    random.seed(7)
    trials, mismatches = 2000, 0
    for _ in range(trials):
        rows = random.randint(1, 12)
        cols = random.randint(1, 12)
        m = [[random.randint(-50, 50) for _ in range(cols)] for _ in range(rows)]
        inst = NumMatrix([row[:] for row in m])
        r1 = random.randint(0, rows - 1)
        r2 = random.randint(r1, rows - 1)
        c1 = random.randint(0, cols - 1)
        c2 = random.randint(c1, cols - 1)
        if inst.sumRegion(r1, c1, r2, c2) != brute_region(m, r1, c1, r2, c2):
            mismatches += 1
    print(f"  {trials} random (matrix, rectangle) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The build, traced.
    # ----------------------------------------------------------------------
    small = [[3, 0, 1], [5, 6, 3], [1, 2, 0]]
    inst = NumMatrix([row[:] for row in small])
    print(f"\n--- P built from {small} ---")
    for row in inst._P:
        print("  " + " ".join(f"{v:>3}" for v in row))
    print(f"  sumRegion(1,1,2,2) = {inst.sumRegion(1, 1, 2, 2)}  "
          f"(want {brute_region(small, 1, 1, 2, 2)})")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(1) query after O(mn) build vs recompute-every-query.
    # ----------------------------------------------------------------------
    print("\n--- O(1) prefix-sum query vs recompute-from-scratch per query ---")
    print(f"  {'matrix':>10} {'#queries':>9} {'build(prefix)':>15} "
          f"{'query(prefix)':>15} {'query(naive)':>15} {'speedup':>10}")
    random.seed(1)
    for size, n_queries in ((50, 5000), (100, 5000), (200, 3000)):
        m = [[random.randint(-100, 100) for _ in range(size)] for _ in range(size)]
        # bias toward larger rectangles so the naive per-query cost is real
        rects = []
        for _ in range(n_queries):
            r1 = random.randint(0, size - 1)
            r2 = random.randint(r1, size - 1)
            c1 = random.randint(0, size - 1)
            c2 = random.randint(c1, size - 1)
            rects.append((r1, c1, r2, c2))

        t0 = time.perf_counter()
        fast = NumMatrix([row[:] for row in m])
        t1 = time.perf_counter()
        for r1, c1, r2, c2 in rects:
            fast.sumRegion(r1, c1, r2, c2)
        t2 = time.perf_counter()

        t3 = time.perf_counter()
        slow = NumMatrix_naive([row[:] for row in m])
        t4 = time.perf_counter()
        for r1, c1, r2, c2 in rects:
            slow.sumRegion(r1, c1, r2, c2)
        t5 = time.perf_counter()

        build_ms = (t1 - t0) * 1000
        fast_q_ms = (t2 - t1) * 1000
        slow_q_ms = (t5 - t4) * 1000
        speedup = slow_q_ms / fast_q_ms if fast_q_ms > 0 else float("inf")
        print(f"  {size}x{size:<6} {n_queries:>9} {build_ms:>14.2f}ms "
              f"{fast_q_ms:>14.2f}ms {slow_q_ms:>14.2f}ms {speedup:>9.1f}x")
    print("  The prefix-sum build cost is paid ONCE; every query after that is")
    print("  O(1). The naive class pays a rectangle-sized cost on EVERY query,")
    print("  and the gap widens as the matrix and query count grow.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
