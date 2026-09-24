"""
================================================================================
SOLUTION · LeetCode 498 · Diagonal Traverse                          [Medium]
https://leetcode.com/problems/diagonal-traverse/
================================================================================

THE CORE IDEA
--------------
Every cell `(row, col)` belongs to exactly one anti-diagonal, identified
by `d = row + col` (constant along that diagonal). LC 498's traversal
order visits diagonal `d = 0`, then `d = 1`, then `d = 2`, ... up through
`d = m + n - 2`, but ALTERNATES the walking direction within each
diagonal: even-indexed diagonals are walked bottom-left to top-right
("going up"), odd-indexed diagonals are walked top-right to bottom-left
("going down"). Rather than group cells by `d` and reverse every other
group (an easy-to-explain but O(mn) EXTRA space approach), you can
simulate the zigzag directly with two live coordinates and one boolean
flag, bouncing off whichever boundary (`row == 0`, `col == n-1`, `row ==
m-1`, `col == 0`) is hit next -- the classic O(1)-extra-space "diagonal
walk" used in every real implementation of this problem.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (priced, not coded) -- generate all `(value, row, col)`
triples, sort by `(row + col, sign depending on parity)` as a composite
key. Technically produces the right order but pays an unnecessary
O(mn log(mn)) sort for a pattern that's fully deterministic in advance --
never actually the right tool here, mentioned only to rule it out
explicitly.

Approach 1 (grouping + conditional reverse, coded for cross-check) --
bucket every cell into a dict keyed by `d = row + col` (natural row-major
order within each bucket, since `row` increases as you scan), then when
emitting diagonal `d`, reverse the bucket if `d` is even (even diagonals
are walked "upward," which is the REVERSE of the row-increasing order the
buckets were built in) and leave it as-is if `d` is odd. O(mn) time,
O(mn) EXTRA space for the dict of buckets.

Approach 2 (chosen) -- direct simulation: maintain `(row, col)` and a
`going_up` flag. At each step, append the current cell, then move
according to direction, bouncing off a boundary by switching direction
AND stepping into the next diagonal exactly at the corner (moving right
when going up hits the top or right edge; moving down when going down
hits the left or bottom edge, with a tie-break for hitting the opposite
corner exactly). O(mn) time, O(1) EXTRA space (excluding the mandatory
output list).


================================================================================
STEP BY STEP TRACE
================================================================================
mat (3x3):
    [1, 2, 3]
    [4, 5, 6]
    [7, 8, 9]

row=0, col=0, going_up=True

    step 1: append mat[0][0]=1
        going_up: col==n-1(2)? no. row==0? YES -> col+=1 (col=1),
        going_up flips to False
    step 2: append mat[0][1]=2
        going_down: row==m-1(2)? no. col==0? no (col=1) ->
        row+=1(1), col-=1(0)
    step 3: append mat[1][0]=4
        going_down: row==m-1? no(1). col==0? YES -> row+=1 (row=2),
        going_up flips to True
    step 4: append mat[2][0]=7
        going_up: col==n-1? no(0). row==0? no(2) -> row-=1(1), col+=1(1)
    step 5: append mat[1][1]=5
        going_up: col==n-1? no(1). row==0? no(1) -> row-=1(0), col+=1(2)
    step 6: append mat[0][2]=3
        going_up: col==n-1(2)? YES -> row+=1(1), going_up flips to False
    step 7: append mat[1][2]=6
        going_down: row==m-1? no(1). col==0? no(2) -> row+=1(2), col-=1(1)
    step 8: append mat[2][1]=8
        going_down: row==m-1(2)? YES -> col+=1(2), going_up flips to True
    step 9: append mat[2][2]=9  (loop ends, m*n=9 cells visited)

Result: [1, 2, 4, 7, 5, 3, 6, 8, 9] -- matches the expected zigzag order
exactly: diagonal d=0 is [1] (trivial), d=1 goes DOWN as [2,4], d=2 goes
UP as [7,5,3], d=3 goes DOWN as [6,8], d=4 is [9] (trivial) -- the even
diagonals (d=0, d=2, d=4) are the "going up" ones by this problem's
convention, matching the `row == 0` bounce rule firing first at d=0.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time            Space    Mutates input?
    -------------------------------------------------------------------------------
    Sort by composite key [priced]        O(mn log(mn))   O(mn)     no
    Group by d, reverse evens [variant]   O(mn)           O(mn)     no
    Boundary-bounce simulation [chosen]   O(mn)           O(1)*     no

    * excluding the O(mn) output list, which every correct solution must
      produce since it IS the requested answer.


================================================================================
EDGE CASES
================================================================================
    Single row (1 x n)    -> every cell is its own diagonal (`d` ranges
                             0..n-1, one cell per diagonal); the "going
                             up"/"going down" alternation never actually
                             has more than one cell to walk, and the walk
                             degenerates to a left-to-right scan.
    Single column (n x 1) -> symmetric: degenerates to a top-to-bottom
                             scan, one cell per diagonal.
    1x1 matrix             -> single cell, loop runs once, no boundary
                             bounce logic ever triggers.
    Square vs. rectangular -> the boundary conditions (`row == 0`, `col ==
                             n-1`, `row == m-1`, `col == 0`) are written
                             generically in terms of `m` and `n`
                             independently, so no special-casing is needed
                             for non-square shapes.
    Exact corner hits      -> when the walk reaches `(0, n-1)` (top-right)
                             while going up, the `col == n - 1` check must
                             be tested BEFORE (or with priority over) the
                             `row == 0` check in that branch (or vice
                             versa consistently) -- both conditions can be
                             true simultaneously only at that single
                             corner, and only one of the two bounce rules
                             should fire.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking `row == 0` before `col == n - 1` (or the mirrored pair for
   the going-down case) inconsistently between the two directions --
   produces a subtly wrong path near the corners of non-square matrices,
   where one boundary is reached "one step early" relative to the other.
2. Forgetting to flip `going_up` when bouncing off a boundary -- the walk
   keeps trying to move in the same diagonal direction forever and either
   throws an IndexError or loops on the same cell.
3. Using the grouping approach but reversing the ODD-indexed diagonals
   instead of the EVEN ones (or vice versa) -- produces the exact
   zigzag pattern backwards; easy to get flipped since it depends on
   which corner the traversal starts from and which direction word
   ("up"/"down") the problem statement uses for that starting corner.
4. Off-by-one in the grouping approach's dict construction -- iterating
   `i, j` in the wrong nested order so that a bucket's natural order is
   column-increasing instead of row-increasing, which silently reverses
   every bucket's default order and inverts which diagonals need the
   explicit reversal.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Could you do this without the `going_up` boolean, using only `d =
  row + col` parity?" -> Yes -- `going_up = (d % 2 == 0)` recomputed at
  the start of each new diagonal is an equivalent, sometimes clearer,
  formulation; the boolean-flag version above is just the more common
  interview phrasing since it reads as "continue in the current
  direction until you hit a wall."
- "What if the matrix were given as a stream (rows arriving one at a
  time, can't look ahead)?" -> The boundary-bounce simulation reads
  cells in an order that jumps between rows unpredictably, so it
  fundamentally needs random access to the whole matrix; a streaming
  variant would need to buffer at least the diagonal-sized window of
  recent rows, more like an online algorithm over a sliding set of
  diagonals.
- "How would you print the diagonals as separate lists instead of one
  flattened list?" -> That's exactly the grouping approach's
  intermediate `diagonals` dict -- just skip the flattening/reversal
  step and return `list(diagonals.values())` (with the per-diagonal
  reversal still applied if the zigzag convention needs to be preserved
  per group).


================================================================================
RELATED PROBLEMS
================================================================================
- Spiral Matrix (LC 54, this topic, 003) -- another non-row-major
  traversal order defined by shrinking/alternating boundaries rather than
  simple nested loops.
- Transpose Matrix (LC 867, this topic, 001) -- another problem whose
  entire content is getting `(row, col)` index arithmetic exactly right;
  contrast the MAIN diagonal (`row - col` constant) used implicitly by
  transpose against this problem's ANTI-diagonal (`row + col` constant).
================================================================================
"""

import time
from typing import List


class Solution:
    def findDiagonalOrder(self, mat: List[List[int]]) -> List[int]:
        if not mat or not mat[0]:
            return []

        m, n = len(mat), len(mat[0])
        result = []
        row, col = 0, 0
        going_up = True

        for _ in range(m * n):
            result.append(mat[row][col])
            if going_up:
                if col == n - 1:
                    row += 1
                    going_up = False
                elif row == 0:
                    col += 1
                    going_up = False
                else:
                    row -= 1
                    col += 1
            else:
                if row == m - 1:
                    col += 1
                    going_up = True
                elif col == 0:
                    row += 1
                    going_up = True
                else:
                    row += 1
                    col -= 1

        return result


def _diagonal_order_grouping(mat: List[List[int]]) -> List[int]:
    """Priced-as-a-variant alternative (group by d=row+col, reverse the
    even-indexed groups), O(mn) extra space, used only as a cross-check
    oracle."""
    if not mat or not mat[0]:
        return []
    m, n = len(mat), len(mat[0])
    diagonals: dict = {}
    for i in range(m):
        for j in range(n):
            d = i + j
            diagonals.setdefault(d, []).append(mat[i][j])

    result = []
    for d in range(m + n - 1):
        group = diagonals[d]
        if d % 2 == 0:
            group = group[::-1]
        result.extend(group)
    return result


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [1, 2, 4, 7, 5, 3, 6, 8, 9]),
        ([[1, 2], [3, 4]], [1, 2, 3, 4]),
        ([[1]], [1]),
        ([[1, 2, 3]], [1, 2, 3]),
        ([[1], [2], [3]], [1, 2, 3]),
        (
            [[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]],
            [1, 2, 5, 9, 6, 3, 4, 7, 10, 11, 8, 12],
        ),
    ]
    for mat, expected in cases:
        got = sol.findDiagonalOrder(mat)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  findDiagonalOrder({mat}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- boundary-bounce simulation vs group-and-reverse, 300 random matrices")
    print("-" * 72)
    import random
    random.seed(498)
    mismatch = 0
    for _ in range(300):
        m = random.randint(1, 12)
        n = random.randint(1, 12)
        mat = [[random.randint(-50, 50) for _ in range(n)] for _ in range(m)]
        a = sol.findDiagonalOrder(mat)
        b = _diagonal_order_grouping(mat)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {300 - mismatch}/300 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- boundary-bounce (O(1) extra) vs group-and-reverse (O(mn) extra)")
    print("-" * 72)
    big = [[i * 300 + j for j in range(300)] for i in range(300)]

    t0 = time.perf_counter()
    sol.findDiagonalOrder(big)
    bounce_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    _diagonal_order_grouping(big)
    group_ms = (time.perf_counter() - t0) * 1000

    print(f"300x300 matrix, one full diagonal traversal:")
    print(f"  boundary-bounce simulation [chosen]: {bounce_ms:8.2f} ms")
    print(f"  group-by-d + reverse [variant]:      {group_ms:8.2f} ms")
    if bounce_ms < group_ms:
        print(f"  measured: boundary-bounce is {group_ms / bounce_ms:.2f}x FASTER here -- the "
              f"grouping version pays real dict-insertion (hashing an int key) and a "
              f"`setdefault` list-append for every one of the mn cells before it can even "
              f"start emitting output, overhead the direct simulation skips entirely.")
    else:
        print(f"  measured: group-by-d was not slower here -- both remain O(mn) time; the "
              f"boundary-bounce version's O(1) extra space is still the answer worth "
              f"knowing cold for the space-constrained framing of this problem.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
