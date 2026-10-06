"""
================================================================================
SOLUTION · LeetCode 54 · Spiral Matrix                               [Medium]
https://leetcode.com/problems/spiral-matrix/
================================================================================

THE CORE IDEA
--------------
Track four shrinking boundaries -- `top`, `bottom`, `left`, `right` -- and
walk one full side at a time: right along the top row, down along the
right column, left along the bottom row, up along the left column. After
each side, tighten the boundary that side just exhausted (`top += 1`,
`right -= 1`, `bottom -= 1`, `left += 1`) so the next side never re-visits
already-collected cells. The two guards `if top <= bottom` (before the
bottom-row pass) and `if left <= right` (before the left-column pass) are
not optional bookkeeping -- without them, a matrix with only one row or
one column gets walked back over itself and every cell is double-counted.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (priced, not coded) -- simulate a "turtle" with a direction
vector, turning 90 degrees whenever the next cell would be out of bounds
or already visited (tracked via a parallel `visited` boolean grid). Same
O(mn) time, but O(mn) EXTRA space for the visited grid -- unnecessary,
since the four-boundary approach gets the same guarantee purely from
arithmetic on shrinking integer bounds, no extra grid required.

Approach 1 (chosen) -- four shrinking boundaries, walk one side per loop
iteration in a fixed right/down/left/up order, with the two guards above
to protect single-row/single-column remainders. O(mn) time, O(1) extra
space (excluding the O(mn) output list, which is mandatory -- it IS the
answer).


================================================================================
STEP BY STEP TRACE
================================================================================
matrix (3x3):
    [1, 2, 3]
    [4, 5, 6]
    [7, 8, 9]

top=0 bottom=2 left=0 right=2, result=[]

Round 1:
    top row (row 0, cols 0..2):    append 1,2,3      -> top=1
    right col (col 2, rows 1..2):  append 6,9         -> right=1
    top(1)<=bottom(2): bottom row (row 2, cols 1..0):  append 8,7  -> bottom=1
    left(0)<=right(1): left col (col 0, rows 1..1):    append 4    -> left=1

    result so far: [1,2,3,6,9,8,7,4]

Now top=1 bottom=1 left=1 right=1 -- loop condition top<=bottom AND
left<=right still holds (1<=1 both), so it runs once more:

Round 2:
    top row (row 1, cols 1..1):    append 5           -> top=2
    right col (col 1, rows 2..1):  range(2,2) is EMPTY -> right=0
    top(2)<=bottom(1)? NO -> skip bottom-row pass, bottom stays 1
    left(1)<=right(0)? NO -> skip left-col pass, left stays 1

    result so far: [1,2,3,6,9,8,7,4,5]

top(2)<=bottom(1)? NO -> outer loop ends.

Final: [1, 2, 3, 6, 9, 8, 7, 4, 5] -- matches the expected spiral exactly.
The two guards are what prevented Round 2 from re-appending row 1's `5`
a second time as a fake "bottom row."


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space    Mutates input?
    ---------------------------------------------------------------------
    Turtle + visited grid [priced]    O(mn)    O(mn)     no
    Four shrinking boundaries[chosen] O(mn)    O(1)*     no

    * excluding the O(mn) output list, which every correct solution must
      produce since it IS the requested answer.


================================================================================
EDGE CASES
================================================================================
    Single row (1 x n)     -> after the top-row pass, top becomes 1 while
                              bottom is still 0, so `top <= bottom` is
                              False and the bottom-row guard correctly
                              skips a duplicate pass over the same row.
    Single column (n x 1)  -> symmetric: after the right-column pass,
                              `left <= right` goes False and the
                              left-column guard skips duplicating it.
    1x1 matrix              -> top row pass appends the single cell; every
                              later pass is empty or guarded off.
    Non-square (e.g. 3x4)   -> boundaries just shrink asymmetrically; the
                              algorithm doesn't assume m == n anywhere.
    Empty matrix / empty row -> guarded by the `if not matrix or not
                              matrix[0]: return []` check up front.


================================================================================
COMMON MISTAKES
================================================================================
1. Omitting the `if top <= bottom` / `if left <= right` guards before the
   bottom-row and left-column passes -- causes every single-row or
   single-column matrix to have its last row/column emitted TWICE.
2. Using `range(left, right)` (exclusive of `right`) instead of
   `range(left, right + 1)` for the top-row pass -- silently drops the
   last column's value from the top row every time.
3. Shrinking a boundary (e.g. `right -= 1`) BEFORE using it in that same
   pass instead of after -- shifts every subsequent pass's bounds by one
   and corrupts the whole spiral, not just one cell.
4. Getting the `range(right, left - 1, -1)` step direction wrong for the
   reverse passes (bottom row right-to-left, left column bottom-to-top)
   -- a plain `range(right, left, -1)` (missing the `-1` in the stop
   argument) silently drops the first cell of that pass.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you generate a matrix in spiral order instead of reading one?" ->
  Yes -- that's exactly 004 Spiral Matrix II, the same four-boundary
  machinery with an incrementing counter written into each visited cell
  instead of being appended to a result list.
- "What if you needed counter-clockwise spiral order?" -> Swap the walk
  order to down/right/up/left (start by walking the LEFT column instead
  of the top row), keeping the same four-boundary shrink discipline.
- "Could you do this recursively instead of iteratively?" -> Yes -- strip
  off the outer ring (top row + right column + bottom row + left column),
  recurse on the strictly interior submatrix, and concatenate; correct
  but easy to fumble the interior-submatrix slicing indices, and offers
  no complexity advantage over the iterative version.


================================================================================
RELATED PROBLEMS
================================================================================
- Spiral Matrix II (LC 59, this topic, 004) -- the inverse operation:
  writing a spiral instead of reading one, same boundary machinery.
- Rotate Image (LC 48, this topic, 002) -- another "walk the matrix ring
  by ring" technique (its layer-by-layer variant), useful to compare
  boundary bookkeeping style against this problem's.
- Diagonal Traverse (LC 498, this topic, 008) -- a different
  non-row-major traversal order over the same kind of grid.
================================================================================
"""

import time
from typing import List


class Solution:
    def spiralOrder(self, matrix: List[List[int]]) -> List[int]:
        if not matrix or not matrix[0]:
            return []

        result = []
        top, bottom = 0, len(matrix) - 1
        left, right = 0, len(matrix[0]) - 1

        while top <= bottom and left <= right:
            for col in range(left, right + 1):
                result.append(matrix[top][col])
            top += 1

            for row in range(top, bottom + 1):
                result.append(matrix[row][right])
            right -= 1

            if top <= bottom:
                for col in range(right, left - 1, -1):
                    result.append(matrix[bottom][col])
                bottom -= 1

            if left <= right:
                for row in range(bottom, top - 1, -1):
                    result.append(matrix[row][left])
                left += 1

        return result


def _spiral_visited_grid(matrix: List[List[int]]) -> List[int]:
    """Priced-not-shipped alternative (turtle + O(mn) visited grid), used
    only as a cross-check oracle."""
    if not matrix or not matrix[0]:
        return []
    m, n = len(matrix), len(matrix[0])
    visited = [[False] * n for _ in range(m)]
    directions = [(0, 1), (1, 0), (0, -1), (-1, 0)]  # right, down, left, up
    d = 0
    row = col = 0
    result = []
    for _ in range(m * n):
        result.append(matrix[row][col])
        visited[row][col] = True
        dr, dc = directions[d]
        nr, nc = row + dr, col + dc
        if not (0 <= nr < m and 0 <= nc < n and not visited[nr][nc]):
            d = (d + 1) % 4
            dr, dc = directions[d]
            nr, nc = row + dr, col + dc
        row, col = nr, nc
    return result


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1, 2, 3, 6, 9, 8, 7, 4, 5]),
        (
            [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]],
            [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7],
        ),
        ([[1]], [1]),
        ([[1, 2, 3, 4]], [1, 2, 3, 4]),
        ([[1], [2], [3], [4]], [1, 2, 3, 4]),
        ([[1, 2], [3, 4]], [1, 2, 4, 3]),
    ]
    for matrix, expected in cases:
        got = sol.spiralOrder(matrix)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  spiralOrder({matrix}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- four-boundary walk vs turtle+visited-grid, 300 random matrices")
    print("-" * 72)
    import random
    random.seed(54)
    mismatch = 0
    for _ in range(300):
        m = random.randint(1, 12)
        n = random.randint(1, 12)
        mat = [[random.randint(-50, 50) for _ in range(n)] for _ in range(m)]
        a = sol.spiralOrder(mat)
        b = _spiral_visited_grid(mat)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {300 - mismatch}/300 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- four-boundary walk vs turtle+visited-grid, measured live")
    print("-" * 72)
    big = [[i * 300 + j for j in range(300)] for i in range(300)]

    t0 = time.perf_counter()
    sol.spiralOrder(big)
    boundary_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    _spiral_visited_grid(big)
    turtle_ms = (time.perf_counter() - t0) * 1000

    print(f"300x300 matrix, one full spiral read:")
    print(f"  four shrinking boundaries: {boundary_ms:8.2f} ms")
    print(f"  turtle + visited grid:     {turtle_ms:8.2f} ms")
    if boundary_ms < turtle_ms:
        print(f"  measured: four-boundary is {turtle_ms / boundary_ms:.2f}x FASTER here -- it "
              f"never allocates the O(mn) visited grid and never pays for a bounds/visited "
              f"check on every single step, only at the four corners of each side.")
    else:
        print(f"  measured: turtle+visited-grid is {boundary_ms / turtle_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
