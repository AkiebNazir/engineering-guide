"""
================================================================================
SOLUTION · LeetCode 74 · Search a 2D Matrix                            [Medium]
https://leetcode.com/problems/search-a-2d-matrix/
================================================================================

THE CORE IDEA
--------------
The two invariants ("each row sorted", "each row's first element exceeds the
previous row's last element") together mean the ENTIRE matrix, read
row-by-row left-to-right, is one long sorted sequence — exactly as if you
had flattened it into a single 1D array. So this is 001's plain binary
search, over a virtual flat index space that is never actually materialised
(topic guide §1.5):

    rows, cols = len(matrix), len(matrix[0])
    lo, hi = 0, rows * cols - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        r, c = divmod(mid, cols)        # flat index -> (row, col)
        if matrix[r][c] == target: return True
        elif matrix[r][c] < target: lo = mid + 1
        else: hi = mid - 1
    return False

`divmod(mid, cols)` converts a flat index back to `(row, col)` in O(1):
`mid // cols` is the row (how many full rows of width `cols` fit before this
index), `mid % cols` is the offset within that row. O(log(rows*cols)) time,
O(1) space — no flattened array is ever built.


================================================================================
ALTERNATIVE: TWO SEPARATE BINARY SEARCHES
================================================================================
Equally valid, and worth knowing because it generalises differently: first
binary-search for the row whose range could contain `target` (the last row
whose first element is <= target), then binary-search within that row.

    row_lo, row_hi = 0, rows - 1
    while row_lo < row_hi:
        mid = (row_lo + row_hi + 1) // 2        # bias UP: looking for rightmost True
        if matrix[mid][0] <= target: row_lo = mid
        else: row_hi = mid - 1
    row = row_lo
    # then a plain binary search on matrix[row]

This costs O(log rows + log cols) = O(log(rows*cols)) — same asymptotic
complexity, more code. The flatten-to-1D approach (above) is simpler and is
what this file's `Solution` uses; the two-search approach is what you'd
adapt for LC 240 (Search a 2D Matrix II), where rows are ONLY individually
sorted (no cross-row ordering guarantee) and flattening no longer works —
that variant needs a staircase search from a corner instead, a genuinely
different technique, not just this one applied twice.


================================================================================
STEP BY STEP TRACE
================================================================================
matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 16
rows=3, cols=4, flat size = 12

    flat index:   0  1  2  3   4   5   6   7   8   9  10  11
    value:        1  3  5  7  10  11  16  20  23  30  34  60
    (row,col):  (0,0)(0,1)(0,2)(0,3)(1,0)(1,1)(1,2)(1,3)(2,0)(2,1)(2,2)(2,3)

    lo=0  hi=11  mid=5   (r,c)=(1,1)  matrix[1][1]=11   11 < 16 -> lo = 6
    lo=6  hi=11  mid=8   (r,c)=(2,0)  matrix[2][0]=23   23 > 16 -> hi = 7
    lo=6  hi=7   mid=6   (r,c)=(1,2)  matrix[1][2]=16   16 == 16 -> return True


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time              Space   Mutates input?  Note
    ---------------------------------  ----------------  ------  ---------------  --------------------
    Scan every cell                    O(rows*cols)      O(1)    no               correct, too slow
    Per-row binary search               O(rows*log cols)  O(1)    no               doesn't use the
                                                                                    cross-row guarantee
    Flatten to 1D binary search ✅     O(log(rows*cols)) O(1)    no               the answer
    Two binary searches (row, then col) O(log rows +
                                          log cols)         O(1)    no               same complexity,
                                                                                    more code; needed
                                                                                    when generalising
                                                                                    to LC 240


================================================================================
EDGE CASES
================================================================================
    1x1 matrix                 -> flat size 1; a single comparison decides it.
    single row (1 x n)          -> divmod always yields row 0; degenerates to 001.
    single column (m x 1)       -> divmod always yields col 0.
    target smaller than every element -> hi collapses to -1, return False.
    target larger than every element  -> lo grows past the last flat index, False.
    target exactly matrix[0][0] or matrix[-1][-1] -> the two flat-index extremes,
                                                       must not be skipped by an
                                                       off-by-one.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting `divmod` and treating `mid` as a row or column index directly
   — `mid` is a FLAT index over the whole matrix; it must be converted.
2. Swapping `mid // cols` and `mid % cols` — silently transposes row/col and
   only fails to show up on a square matrix; always test with a non-square
   matrix (the trace above uses 3x4 specifically to catch this).
3. Doing a per-row binary search without checking the cross-row invariant
   first — technically works but is O(rows * log cols) instead of
   O(log(rows*cols)), missing the entire point of the two guarantees the
   problem gives you.
4. Confusing this problem (LC 74, cross-row sorted, flattenable) with LC 240
   (only row/column-wise sorted, NOT flattenable) — LC 240 needs a
   staircase search starting from a corner, not this technique.
5. Computing `rows * cols - 1` when either dimension could be 0 — guard for
   an empty matrix (`not matrix or not matrix[0]`) before indexing `matrix[0]`.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if rows are individually sorted but there's no cross-row guarantee
   (LC 240)?
A: Flattening breaks. Start at the top-right corner: if the corner is bigger
   than target, move left (eliminate a column); if smaller, move down
   (eliminate a row). O(rows + cols), not O(log(rows*cols)) — a genuinely
   different, non-binary-search technique.

Q: Which is better in practice, flatten-to-1D or two-searches?
A: Flatten-to-1D — same complexity, simpler code, one loop instead of two.
   The two-search form is worth mentioning only because it's the natural
   stepping stone toward understanding why LC 240 needs something else.

Q: How would you support insertions while keeping O(log(rows*cols)) search?
A: A flat sorted array structure like this doesn't support O(log n) insert
   (shifting costs O(rows*cols)); you'd want a balanced BST or a B-tree-like
   structure instead — a different data structure question entirely.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 704  Binary Search                — the 1D mechanism this generalises (001)
    LC 240  Search a 2D Matrix II        — looks similar, needs a different
                                            (staircase) technique
    LC 378  Kth Smallest Element in a
             Sorted Matrix                — Family B binary search (topic guide
                                            §1.1) over VALUE space, using this
                                            matrix's row/column sortedness to
                                            count how many elements are <= mid
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        """Flatten-to-1D binary search. O(log(rows*cols)) time, O(1) space.
        See THE CORE IDEA above."""
        if not matrix or not matrix[0]:
            return False
        rows, cols = len(matrix), len(matrix[0])
        lo, hi = 0, rows * cols - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            r, c = divmod(mid, cols)
            val = matrix[r][c]
            if val == target:
                return True
            elif val < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return False

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def searchMatrix_linear(self, matrix: List[List[int]], target: int) -> bool:
        """O(rows*cols) oracle: scan every cell."""
        for row in matrix:
            for x in row:
                if x == target:
                    return True
        return False

    def searchMatrix_two_searches(self, matrix: List[List[int]], target: int) -> bool:
        """O(log rows + log cols): binary search for the row, then within it.
        See ALTERNATIVE above."""
        if not matrix or not matrix[0]:
            return False
        rows, cols = len(matrix), len(matrix[0])
        if target < matrix[0][0] or target > matrix[rows - 1][cols - 1]:
            return False
        row_lo, row_hi = 0, rows - 1
        while row_lo < row_hi:
            mid = (row_lo + row_hi + 1) // 2  # bias up: rightmost True search
            if matrix[mid][0] <= target:
                row_lo = mid
            else:
                row_hi = mid - 1
        row = matrix[row_lo]
        lo, hi = 0, cols - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if row[mid] == target:
                return True
            elif row[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return False


# ==============================================================================
# TESTS — run:  python 005_search_a_2d_matrix_solution.py
# ==============================================================================
CASES = [
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3, True),
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13, False),
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 16, True),
    ([[1]], 1, True),
    ([[1]], 2, False),
    ([[1, 3]], 3, True),
    ([[1], [3]], 3, True),
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 1, True),
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 60, True),
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 0, False),
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 61, False),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for matrix, target, expected in CASES:
        got = sol.searchMatrix(matrix, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  target={target:<5} -> {got}  (want {expected})")

    print("\n--- two-searches variant cross-check ---")
    for matrix, target, expected in CASES:
        got = sol.searchMatrix_two_searches(matrix, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  two_searches target={target:<5} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: matrix=[[1,3,5,7],[10,11,16,20],[23,30,34,60]], target=16 ---")
    matrix, target = [[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 16
    rows, cols = len(matrix), len(matrix[0])
    lo, hi = 0, rows * cols - 1
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'(r,c)':>7} {'value':>6}")
    while lo <= hi:
        mid = (lo + hi) // 2
        r, c = divmod(mid, cols)
        val = matrix[r][c]
        print(f"  {lo:>3} {hi:>3} {mid:>4} {f'({r},{c})':>7} {val:>6}")
        if val == target:
            print(f"  match -> True")
            break
        elif val < target:
            lo = mid + 1
        else:
            hi = mid - 1

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. linear scan ---")
    random.seed(5)
    trials, mismatches = 2000, 0
    for _ in range(trials):
        rows = random.randint(1, 10)
        cols = random.randint(1, 10)
        flat = sorted(random.sample(range(-200, 200), rows * cols))
        matrix = [flat[i * cols:(i + 1) * cols] for i in range(rows)]
        target = random.choice(flat) if random.random() < 0.5 else random.randint(-250, 250)
        a = sol.searchMatrix(matrix, target)
        b = sol.searchMatrix_linear(matrix, target)
        c = sol.searchMatrix_two_searches(matrix, target)
        if not (a == b == c):
            mismatches += 1
    print(f"  {trials} random matrices: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(log(rows*cols)) vs O(rows*cols) full scan.
    # ----------------------------------------------------------------------
    print("\n--- O(log(rows*cols)) binary search vs O(rows*cols) full scan ---")
    print(f"  {'matrix':>10} {'binary(us)':>12} {'linear(us)':>12} {'speedup':>10}")
    for size in (50, 200, 1000):
        flat = list(range(size * size))
        matrix = [flat[i * size:(i + 1) * size] for i in range(size)]
        target = flat[-1]  # worst case for linear scan
        reps = 50
        t0 = time.perf_counter()
        for _ in range(reps):
            sol.searchMatrix(matrix, target)
        t1 = time.perf_counter()
        for _ in range(reps):
            sol.searchMatrix_linear(matrix, target)
        t2 = time.perf_counter()
        bin_us = (t1 - t0) / reps * 1_000_000
        lin_us = (t2 - t1) / reps * 1_000_000
        speedup = lin_us / bin_us if bin_us > 0 else float("inf")
        print(f"  {size}x{size:<5} {bin_us:>10.2f}us {lin_us:>10.2f}us {speedup:>9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
