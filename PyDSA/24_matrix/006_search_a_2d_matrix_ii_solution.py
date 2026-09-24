"""
================================================================================
SOLUTION · LeetCode 240 · Search a 2D Matrix II                      [Medium]
https://leetcode.com/problems/search-a-2d-matrix-ii/
================================================================================

THE CORE IDEA
--------------
Start at the TOP-RIGHT corner. From there, the matrix's two sort
invariants (rows ascend left-to-right, columns ascend top-to-bottom) give
you a full ROW elimination or a full COLUMN elimination on every
comparison:
    - if the current cell is LARGER than target, target cannot be
      anywhere in this COLUMN below the current cell (everything below is
      even bigger) -- but it might still be further left in this row, so
      move LEFT (`col -= 1`).
    - if the current cell is SMALLER than target, target cannot be
      anywhere in this ROW to the left of the current cell (everything to
      the left is even smaller) -- but it might still be further down in
      this column, so move DOWN (`row += 1`).
The top-right corner is the only cell where BOTH of these eliminations
are simultaneously safe: it's the largest element in its row and the
smallest element in its column, so every comparison rules out an entire
line at once. (The bottom-left corner has the same property, symmetric
direction; the top-left and bottom-right corners do NOT -- from
top-left, `matrix[0][0]` being smaller than target rules out nothing,
since target could be anywhere.)


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded) -- scan every cell. O(mn)
time, O(1) space. Correct but ignores both sort invariants entirely.

Approach 1 (improvement, priced, not coded) -- binary search each row
independently (each row is individually sorted). O(m log n) time, O(1)
space. Better than brute force, but still doesn't exploit the COLUMN
ordering at all -- it's leaving information on the table.

Approach 2 (chosen) -- staircase search from the top-right corner,
eliminating one full row or column per comparison. O(m + n) time, O(1)
space. This explicitly is NOT classic binary search (it doesn't halve a
sorted array each step) -- it's a linear "staircase" walk, but each step
does O(1) work and the walk is bounded by `m + n` total steps (at most
`m` down-moves and `n` left-moves before falling off an edge), which
beats `m log n` once `n` is large enough that `log n > (m+n)/m` roughly
-- but more importantly it's simpler to state correctly and is the
canonical answer this problem is testing for.


================================================================================
STEP BY STEP TRACE
================================================================================
matrix:
    [ 1,  4,  7, 11, 15]
    [ 2,  5,  8, 12, 19]
    [ 3,  6,  9, 16, 22]
    [10, 13, 14, 17, 24]
    [18, 21, 23, 26, 30]

target = 5, start row=0, col=4 (top-right corner, value 15)

    (0,4)=15 > 5  -> move left:  col=3
    (0,3)=11 > 5  -> move left:  col=2
    (0,2)=7  > 5  -> move left:  col=1
    (0,1)=4  < 5  -> move down:  row=1
    (1,1)=5  == 5 -> FOUND, return True

Each ">" step eliminated an entire COLUMN (nothing below 15, 11, or 7 in
those columns could ever equal 5, since columns only grow downward); the
one "<" step eliminated an entire ROW (nothing to the left of 4 in row 0
could ever equal 5, since rows only grow rightward).

target = 20, same matrix, start row=0, col=4

    (0,4)=15 < 20 -> row=1
    (1,4)=19 < 20 -> row=2
    (2,4)=22 > 20 -> col=3
    (2,3)=16 < 20 -> row=3
    (3,3)=17 < 20 -> row=4
    (4,3)=26 > 20 -> col=2
    (4,2)=23 > 20 -> col=1
    (4,1)=21 > 20 -> col=0
    (4,0)=18 < 20 -> row=5

    row == 5 == m -> walked off the bottom edge -> return False


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time         Space  Mutates input?
    --------------------------------------------------------------------------
    Full scan [priced]                    O(mn)        O(1)    no
    Per-row binary search [priced]        O(m log n)   O(1)    no
    Staircase from top-right [chosen]     O(m + n)     O(1)    no


================================================================================
EDGE CASES
================================================================================
    Target smaller than every element   -> walks left across row 0 until
                                            col < 0, returns False without
                                            ever moving down.
    Target larger than every element    -> walks down column (n-1) until
                                            row == m, returns False without
                                            ever moving left.
    Target equals the top-right corner  -> found immediately, one
                                            comparison.
    Target equals the bottom-left
    corner                              -> worst case for this starting
                                            corner: walks the full "L"
                                            shape, up to `m + n - 1` steps.
    1x1 matrix                          -> single comparison decides it.
    Single row / single column matrix   -> degenerates to a pure linear
                                            scan in one direction, still
                                            O(m + n) = O(max(m, n)).
    Empty matrix / empty row            -> guarded by the `if not matrix
                                            or not matrix[0]` check.


================================================================================
COMMON MISTAKES
================================================================================
1. Starting from the TOP-LEFT corner instead of top-right (or
   bottom-left) -- from top-left, a "smaller than target" comparison
   rules out NOTHING (target could still be to the right OR below), so
   there's no valid move to make that preserves correctness; this
   corner simply doesn't have the elimination property.
2. Trying to apply true binary search across the whole flattened matrix
   -- this only works when the ENTIRE matrix is one global sorted
   sequence (as in LC 74 Search a 2D Matrix, a DIFFERENT, stricter
   problem); LC 240's matrix is row-sorted and column-sorted
   independently, which is a strictly weaker guarantee that does NOT
   imply a single global sorted order (e.g. `matrix[0][4]=15` is larger
   than `matrix[3][0]=10`, so flattening row-major does not yield a
   sorted array).
3. Off-by-one on the walk-off-edge termination: using `row <= m` /
   `col >= 0` inconsistently, or forgetting to check BOTH bounds each
   iteration (the walk can exit via either edge depending on the target).
4. Mutating `row`/`col` in the wrong direction (e.g. moving right when
   larger, or up when smaller) -- silently turns the staircase into an
   infinite loop or a walk that never reaches the target's actual
   location.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why not binary search the whole thing?" -> Because row-sorted +
  column-sorted independently is weaker than "fully sorted when
  flattened" -- that stronger guarantee is a DIFFERENT LeetCode problem
  (74, this topic doesn't include it, but it's the classic contrast).
  Flattening this matrix row-major does not produce a sorted sequence,
  so binary search over the flattened array is simply incorrect here.
- "Is the staircase search itself a form of binary search?" -> No --
  it's a linear elimination walk. It shares the *spirit* of topic 05
  (each comparison discards information you'll never need to check
  again), but it discards one row/column per step, not half the
  remaining SEARCH SPACE per step, so it's O(m+n), not O(log(mn)).
- "Could you start from the bottom-left corner instead?" -> Yes,
  symmetric: move UP when the current cell is smaller than target
  (eliminate the row to the right you've already ruled bigger), RIGHT
  when larger (eliminate the column above). Same O(m+n) guarantee.
- "What if the matrix were fully sorted (one global order)?" -> Then
  treat it as one logical sorted array of length `m*n` and binary search
  by mapping a flat index `k` to `(k // n, k % n)` -- true O(log(mn)).


================================================================================
RELATED PROBLEMS
================================================================================
- Binary Search (topic 05) -- contrast directly: true binary search
  halves the remaining SEARCH SPACE each comparison and requires one
  global monotone order; this problem's staircase search eliminates one
  ROW or COLUMN each comparison and only requires two INDEPENDENT
  per-axis sort invariants -- a strictly weaker precondition that rules
  out true binary search but still gives a sub-quadratic algorithm.
- Kth Smallest Element in a Sorted Matrix (not in this curriculum's
  TSV, but the canonical companion problem) -- reuses this exact
  row/column-sorted-independently structure with a counting binary
  search over VALUES instead of a direct staircase search over
  POSITIONS.
================================================================================
"""

import time
from typing import List


class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        if not matrix or not matrix[0]:
            return False

        m, n = len(matrix), len(matrix[0])
        row, col = 0, n - 1

        while row < m and col >= 0:
            val = matrix[row][col]
            if val == target:
                return True
            elif val > target:
                col -= 1
            else:
                row += 1

        return False


def _search_full_scan(matrix: List[List[int]], target: int) -> bool:
    """Priced-not-shipped brute force, used only as a cross-check oracle."""
    for row in matrix:
        for val in row:
            if val == target:
                return True
    return False


def _search_per_row_binary(matrix: List[List[int]], target: int) -> bool:
    """Priced-not-shipped improvement (binary search each row), used only
    as a cross-check oracle."""
    import bisect

    for row in matrix:
        idx = bisect.bisect_left(row, target)
        if idx < len(row) and row[idx] == target:
            return True
    return False


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    matrix = [
        [1, 4, 7, 11, 15],
        [2, 5, 8, 12, 19],
        [3, 6, 9, 16, 22],
        [10, 13, 14, 17, 24],
        [18, 21, 23, 26, 30],
    ]

    cases = [
        (matrix, 5, True),
        (matrix, 20, False),
        (matrix, 1, True),
        (matrix, 30, True),
        (matrix, 15, True),
        (matrix, 18, True),
        (matrix, 0, False),
        (matrix, 31, False),
        ([[1]], 1, True),
        ([[1]], 0, False),
        ([[1, 3, 5]], 3, True),
        ([[1], [3], [5]], 3, True),
    ]
    for mat, target, expected in cases:
        got = sol.searchMatrix(mat, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  searchMatrix(target={target}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- staircase vs full scan vs per-row binary search, 400 random cases")
    print("-" * 72)
    import random
    random.seed(240)
    mismatch = 0
    for _ in range(400):
        m = random.randint(1, 12)
        n = random.randint(1, 12)
        # Build a matrix that is genuinely row- and column-sorted: sort
        # m*n random values and lay them out row-major (row-major layout
        # of a fully sorted sequence is always both row- and column-sorted).
        vals = sorted(random.randint(-100, 100) for _ in range(m * n))
        mat = [vals[i * n:(i + 1) * n] for i in range(m)]
        target = random.choice(vals) if random.random() < 0.7 else random.randint(-150, 150)
        a = sol.searchMatrix(mat, target)
        b = _search_full_scan(mat, target)
        c = _search_per_row_binary(mat, target)
        if not (a == b == c):
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {400 - mismatch}/400 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- staircase O(m+n) vs full scan O(mn) vs per-row binary O(m log n)")
    print("-" * 72)
    m, n = 1000, 1000
    vals = list(range(m * n))
    big = [vals[i * n:(i + 1) * n] for i in range(m)]
    target = -1  # guaranteed absent -- forces every approach into its full worst case

    t0 = time.perf_counter()
    sol.searchMatrix(big, target)
    stair_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    _search_per_row_binary(big, target)
    binary_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    _search_full_scan(big, target)
    scan_ms = (time.perf_counter() - t0) * 1000

    print(f"{m}x{n} matrix, absent target (worst case for all three):")
    print(f"  staircase O(m+n) [chosen]:        {stair_ms:8.3f} ms")
    print(f"  per-row binary search O(m log n): {binary_ms:8.3f} ms")
    print(f"  full scan O(mn):                  {scan_ms:8.3f} ms")
    if stair_ms < scan_ms:
        print(f"  measured: staircase beats full scan by {scan_ms / stair_ms:.1f}x here, "
              f"consistent with O(m+n)=2000 steps vs O(mn)=1,000,000 cell visits -- a real "
              f"algorithmic gap, not a constant-factor artifact.")
    else:
        print(f"  measured: full scan was not slower here (unexpected at this scale) -- "
              f"still O(mn) vs O(m+n) asymptotically; the number below is what this "
              f"machine actually produced.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
