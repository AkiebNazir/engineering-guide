"""
================================================================================
SOLUTION · LeetCode 73 · Set Matrix Zeroes                           [Medium]
https://leetcode.com/problems/set-matrix-zeroes/
================================================================================

THE CORE IDEA
--------------
You need to remember WHICH rows and columns contained a zero in the
ORIGINAL matrix, but you're not allowed extra O(m) / O(n) arrays to
record that. The trick: use the matrix's own FIRST ROW and FIRST COLUMN
as that memory. `matrix[0][j] = 0` means "column j must be zeroed";
`matrix[i][0] = 0` means "row i must be zeroed." The one wrinkle: the
first row and first column are ALSO real data that might need to be
zeroed for their own sake, and they'd get overwritten by the marking
process before you've recorded whether THEY originally contained a zero.
The fix is to snapshot `first_row_has_zero` and `first_col_has_zero`
INTO two plain booleans before doing any marking, then apply them last.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded) -- copy the whole matrix,
scan the COPY for zeros, and for every zero found, zero the corresponding
row/column in the ORIGINAL. O(mn) time, O(mn) EXTRA space for the copy
(needed so you're not reading already-zeroed cells while still
searching for more original zeros).

Approach 1 (simple improvement, priced, not coded) -- use two separate
sets, `zero_rows` and `zero_cols`, populated by one scan, then a second
scan zeros any cell whose row or column is in either set. O(mn) time,
O(m + n) extra space -- much better than Approach 0, still not optimal.

Approach 2 (chosen) -- use row 0 and column 0 of the matrix ITSELF as the
`zero_rows` / `zero_cols` marker arrays from Approach 1, with two
standalone booleans capturing whether row 0 / column 0 themselves
originally held a zero (captured BEFORE marking begins, since marking
overwrites exactly those cells). O(mn) time, O(1) EXTRA space -- the
matrix is its own scratch space.


================================================================================
STEP BY STEP TRACE
================================================================================
matrix:
    [0, 1, 2, 0]
    [3, 4, 5, 2]
    [1, 3, 1, 5]

Snapshot BEFORE touching anything:
    first_row_has_zero = any(row 0 has a 0)  -> row 0 = [0,1,2,0] -> True
    first_col_has_zero = any(col 0 has a 0)  -> col 0 = [0,3,1]   -> True

Pass 1 -- scan the INTERIOR (i >= 1, j >= 1) and mark row 0 / col 0:
    interior = [[4,5,2],[3,1,5]] -- no zeros in the interior at all, so
    no NEW marks get written; row 0 and col 0 are untouched by this pass
    (they already carry their own original values, which is exactly what
    we want -- they double as both data and markers simultaneously).

Pass 2 -- zero interior cells whose row-marker OR col-marker is 0:
    matrix[1][3]: row-marker matrix[1][0]=3 (not 0), col-marker
        matrix[0][3]=0 (IS 0, from the ORIGINAL top-right corner) -> zero it
    matrix[2][3]: col-marker matrix[0][3]=0 -> zero it
    all other interior cells: both markers non-zero -> untouched

    matrix now:
    [0, 1, 2, 0]
    [3, 4, 5, 0]
    [1, 3, 1, 0]

Pass 3 -- apply the snapshotted booleans last:
    first_row_has_zero (True) -> zero the whole of row 0
    first_col_has_zero (True) -> zero the whole of column 0

    [0, 0, 0, 0]
    [0, 4, 5, 0]
    [0, 3, 1, 0]

Matches the expected output exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time     Space    Mutates input?
    -----------------------------------------------------------------------
    Copy + rescan [priced]               O(mn)    O(mn)     YES, in place
    Two sets (zero_rows/zero_cols)       O(mn)    O(m+n)    YES, in place
    First row/col as markers [chosen]    O(mn)    O(1)      YES, in place


================================================================================
EDGE CASES
================================================================================
    Zero in row 0 or col 0 itself -> exactly why the two booleans must be
                                     captured BEFORE the marking pass
                                     begins; otherwise the marking pass's
                                     writes into row 0 / col 0 get
                                     confused with "was this originally a
                                     zero" and the signal is lost.
    Entire matrix is zeros already -> both booleans True, every marker
                                     stays 0, everything gets zeroed --
                                     already correct, a no-op in effect.
    No zeros anywhere               -> both booleans False, no markers
                                     ever get set, matrix is returned
                                     completely unchanged.
    1x1 matrix                      -> row 0 IS the whole matrix and col 0
                                     IS the whole matrix simultaneously;
                                     both booleans read the same single
                                     cell, and the marking/zero passes over
                                     the (empty) interior are no-ops --
                                     correctness rests entirely on Pass 3.
    Single row (1 x n)              -> no interior exists (`range(1, m)` is
                                     empty), so Passes 1-2 do nothing; the
                                     entire result depends on
                                     `first_row_has_zero`.
    Single column (n x 1)           -> symmetric, depends entirely on
                                     `first_col_has_zero`.


================================================================================
COMMON MISTAKES
================================================================================
1. Capturing `first_row_has_zero` / `first_col_has_zero` AFTER the
   marking pass instead of before -- by then row 0 / col 0 have already
   been overwritten with marker zeros for unrelated interior cells, so
   the "did row 0 ORIGINALLY have a zero" question can no longer be
   answered correctly.
2. Letting Pass 1 and Pass 2 iterate over the FULL matrix (`range(0, m)`,
   `range(0, n)`) instead of just the interior (`range(1, m)`, `range(1,
   n)`) -- this treats row 0 / col 0 as ordinary data cells to be zeroed
   by Pass 2 using their OWN just-written marker values, corrupting the
   marker information before Pass 3 can read it.
3. Applying Pass 3 (the row 0 / col 0 zeroing) BEFORE Pass 2 instead of
   after -- Pass 2 reads `matrix[i][0]` and `matrix[0][j]` as markers, so
   if row 0 / col 0 have already been fully zeroed, every marker reads as
   "zero," incorrectly zeroing the entire matrix.
4. Forgetting this is a mutate-IN-PLACE problem and building a brand new
   matrix "for safety" -- works, but throws away the O(1)-space technique
   the problem exists to teach.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do it in one pass instead of three?" -> Not really in the
  strict sense -- you fundamentally need to know ALL the original zero
  positions before you can safely start zeroing (otherwise a
  zero-created-by-zeroing gets misread as an original zero and cascades
  incorrectly), so at least one full read pass has to precede any write.
  The three passes here are already the minimal information-theoretic
  shape: (1) discover, (2) apply to the interior, (3) apply to the
  border.
- "What if you couldn't use even the matrix's own first row/column as
  scratch space?" -> Then O(m + n) space (two sets or two boolean lists)
  is the best you can do without extra passes; that's exactly the
  "simple improvement" priced above.
- "How does this generalize to a 3D tensor?" -> Same idea, one marker
  axis per dimension, though "the first slice along each axis" as
  combined marker+data gets trickier to keep straight with 3 dimensions
  instead of 2 -- worth mentioning to show the technique's boundary.


================================================================================
RELATED PROBLEMS
================================================================================
- Rotate Image (LC 48, this topic, 002) -- another explicitly O(1)-extra-
  space, mutate-in-place matrix problem; compare how each finds scratch
  space inside the very structure it's transforming.
- Game of Life (LC 289, this topic, 007) -- the other in-place matrix
  problem in this topic; contrast its "encode two states in one cell"
  trick against this problem's "use the border as a marker array" trick
  -- both solve the same underlying tension (need extra memory, must
  stay in-place) with a different piece of the existing structure.
================================================================================
"""

import copy
import time
from typing import List


class Solution:
    def setZeroes(self, matrix: List[List[int]]) -> None:
        """
        Do not return anything, modify matrix in-place instead.
        """
        m, n = len(matrix), len(matrix[0])

        first_row_has_zero = any(matrix[0][j] == 0 for j in range(n))
        first_col_has_zero = any(matrix[i][0] == 0 for i in range(m))

        # Pass 1: mark using row 0 / col 0, scanning only the interior.
        for i in range(1, m):
            for j in range(1, n):
                if matrix[i][j] == 0:
                    matrix[i][0] = 0
                    matrix[0][j] = 0

        # Pass 2: zero the interior based on the markers.
        for i in range(1, m):
            for j in range(1, n):
                if matrix[i][0] == 0 or matrix[0][j] == 0:
                    matrix[i][j] = 0

        # Pass 3: apply the snapshotted border decision last.
        if first_row_has_zero:
            for j in range(n):
                matrix[0][j] = 0
        if first_col_has_zero:
            for i in range(m):
                matrix[i][0] = 0


def _set_zeroes_two_sets(matrix: List[List[int]]) -> None:
    """Priced-as-a-variant alternative (O(m+n) extra space via two sets),
    used only as a cross-check oracle."""
    m, n = len(matrix), len(matrix[0])
    zero_rows, zero_cols = set(), set()
    for i in range(m):
        for j in range(n):
            if matrix[i][j] == 0:
                zero_rows.add(i)
                zero_cols.add(j)
    for i in range(m):
        for j in range(n):
            if i in zero_rows or j in zero_cols:
                matrix[i][j] = 0


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([[1, 1, 1], [1, 0, 1], [1, 1, 1]], [[1, 0, 1], [0, 0, 0], [1, 0, 1]]),
        (
            [[0, 1, 2, 0], [3, 4, 5, 2], [1, 3, 1, 5]],
            [[0, 0, 0, 0], [0, 4, 5, 0], [0, 3, 1, 0]],
        ),
        ([[1]], [[1]]),
        ([[0]], [[0]]),
        ([[1, 2, 3]], [[1, 2, 3]]),
        ([[0, 2, 3]], [[0, 0, 0]]),
    ]
    for matrix, expected in cases:
        got = [row[:] for row in matrix]
        sol.setZeroes(got)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  setZeroes({matrix}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- first-row/col markers vs two-sets, 300 random sparse matrices")
    print("-" * 72)
    import random
    random.seed(73)
    mismatch = 0
    for _ in range(300):
        m = random.randint(1, 15)
        n = random.randint(1, 15)
        mat = [[random.choice([0, 0, 1, 2, 3, 4, 5]) for _ in range(n)] for _ in range(m)]
        a = [row[:] for row in mat]
        b = [row[:] for row in mat]
        sol.setZeroes(a)
        _set_zeroes_two_sets(b)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {300 - mismatch}/300 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- O(1)-space markers vs O(m+n)-space two sets")
    print("-" * 72)
    m = n = 500
    big = [[1 if (i * 37 + j * 53) % 997 != 0 else 0 for j in range(n)] for i in range(m)]

    a = copy.deepcopy(big)
    t0 = time.perf_counter()
    sol.setZeroes(a)
    markers_ms = (time.perf_counter() - t0) * 1000

    b = copy.deepcopy(big)
    t0 = time.perf_counter()
    _set_zeroes_two_sets(b)
    sets_ms = (time.perf_counter() - t0) * 1000

    scale_cross_ok = a == b
    all_ok &= scale_cross_ok
    print(f"{'PASS' if scale_cross_ok else 'FAIL'}  both approaches still agree at {m}x{n} scale")

    print(f"{m}x{n} matrix:")
    print(f"  first-row/col markers [O(1) extra]:  {markers_ms:8.2f} ms")
    print(f"  two sets [O(m+n) extra]:              {sets_ms:8.2f} ms")
    if markers_ms < sets_ms:
        print(f"  measured: markers is {sets_ms / markers_ms:.2f}x FASTER here -- Python set "
              f"membership tests (`i in zero_rows`) cost real hashing overhead per cell that "
              f"a direct list-index marker read (`matrix[i][0] == 0`) doesn't pay.")
    else:
        print(f"  measured: two-sets is {markers_ms / sets_ms:.2f}x faster here -- a plausible "
              f"CPython artifact (set lookups on small int sets can beat extra list indexing "
              f"in some builds); either way both are O(mn) and the marker approach remains "
              f"the right answer for the explicit O(1)-extra-space follow-up.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
