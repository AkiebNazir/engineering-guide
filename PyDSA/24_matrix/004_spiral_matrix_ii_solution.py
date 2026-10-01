"""
================================================================================
SOLUTION · LeetCode 59 · Spiral Matrix II                            [Medium]
https://leetcode.com/problems/spiral-matrix-ii/
================================================================================

THE CORE IDEA
--------------
This is 003 Spiral Matrix run BACKWARDS: instead of reading values out of
an existing grid in spiral order, WRITE an increasing counter (`1, 2, 3,
...`) into an empty grid in spiral order. The four-shrinking-boundary
machinery is identical, cell for cell -- only `result.append(matrix[...])`
becomes `matrix[...] = num; num += 1`. Recognizing that this is the same
traversal skeleton as 003 with reads swapped for writes is the entire
insight; there is no new algorithmic idea here.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (priced, not coded) -- pre-compute the full list of `(row,
col)` coordinates in spiral order (e.g. by adapting the turtle+visited-
grid walk from 003), then zip that coordinate list against `range(1, n*n
+ 1)` and assign. Correct, but needlessly two-phase: O(n^2) time, O(n^2)
extra space for the coordinate list, when the boundaries can be
maintained with O(1) extra state while writing directly.

Approach 1 (chosen) -- four shrinking boundaries (`top`, `bottom`, `left`,
`right`), walking right/down/left/up exactly as in 003, writing an
incrementing `num` into each visited cell instead of reading one out.
O(n^2) time (every cell is written exactly once), O(1) extra space beyond
the mandatory `n x n` output grid.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 3, matrix pre-filled with zeros:
    [0, 0, 0]
    [0, 0, 0]
    [0, 0, 0]

top=0 bottom=2 left=0 right=2, num=1

Round 1:
    top row (row 0, cols 0..2): write 1,2,3           -> num=4, top=1
        [1, 2, 3]
        [0, 0, 0]
        [0, 0, 0]
    right col (col 2, rows 1..2): write 4,5            -> num=6, right=1
        [1, 2, 3]
        [0, 0, 4]
        [0, 0, 5]
    top(1)<=bottom(2): bottom row (row 2, cols 1..0): write 6,7 -> num=8, bottom=1
        [1, 2, 3]
        [0, 0, 4]
        [7, 6, 5]
    left(0)<=right(1): left col (col 0, rows 1..1): write 8    -> num=9, left=1
        [1, 2, 3]
        [8, 0, 4]
        [7, 6, 5]

top=1 bottom=1 left=1 right=1 -- loop condition still holds (1<=1 both).

Round 2:
    top row (row 1, col 1..1): write 9                -> num=10, top=2
        [1, 2, 3]
        [8, 9, 4]
        [7, 6, 5]
    right col (col 1, rows 2..1): range(2,2) EMPTY      -> right=0
    top(2)<=bottom(1)? NO -> skip bottom-row pass
    left(1)<=right(0)? NO -> skip left-col pass

top(2)<=bottom(1)? NO -> outer loop ends.

Final:
    [1, 2, 3]
    [8, 9, 4]
    [7, 6, 5]

Matches the expected output exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time     Space    Mutates input?
    ------------------------------------------------------------------------
    Coordinate-list-then-zip [priced]     O(n^2)   O(n^2)    n/a -- builds new
    Four shrinking boundaries [chosen]    O(n^2)   O(1)*     n/a -- builds new

    * excluding the mandatory O(n^2) `n x n` output grid, which IS the
      requested answer. There is no "input" to mutate here (the only
      input is the scalar `n`), so the mutates-input column doesn't apply
      the way it does for 002/005/007 -- it's included in this table only
      for consistency with the rest of the topic.


================================================================================
EDGE CASES
================================================================================
    n == 1                  -> single cell, top row pass writes `1` and
                               every subsequent pass is empty or guarded
                               off; matrix is `[[1]]`.
    n == 2                  -> matrix is `[[1,2],[4,3]]` -- exercises the
                               "single remaining row after the top pass"
                               guard exactly the way 003's 2x2 trace does.
    Odd n (e.g. 3, 5, 7)     -> the true center cell gets written last, by
                               a top-row pass of length 1 in the final
                               round (never by a left/right/bottom pass,
                               since those get guarded off once the
                               boundaries cross).
    Even n (e.g. 2, 4)       -> no single "center" cell; the spiral
                               terminates the round after the last ring
                               collapses to zero width.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting to increment `num` after EVERY write (not just after every
   side) -- produces a matrix where some values repeat and the maximum
   never reaches `n^2`.
2. Copy-pasting 003's guards (`if top <= bottom`, `if left <= right`) but
   forgetting them here too -- the exact same single-row/single-column
   double-write bug reappears, except now it's a double WRITE, silently
   overwriting an earlier-placed correct value with a later, wrong one
   rather than duplicating an output entry (which would at least have
   been visible as a too-long result list in 003).
3. Initializing `matrix` with an `n x n` list of a SHARED inner list
   (`[[0] * n] * n` instead of `[[0] * n for _ in range(n)]`) -- all `n`
   "rows" alias the same underlying list object, so writing to row 0
   silently corrupts every other row too.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you generalize this to an `m x n` (non-square) spiral fill?" ->
  Yes -- nothing about the four-boundary technique assumes `m == n`;
  only the "generate a square of size n" framing in THIS problem is
  square-specific. Initialize an `m x n` zero grid and reuse the same
  loop unchanged.
- "What's the relationship between this and 003 Spiral Matrix?" -> They
  are inverse operations sharing one traversal skeleton -- 003 reads
  values out in spiral order, this problem writes values in in spiral
  order. If asked to implement both back to back, write the shared
  four-boundary walk once and parameterize whether each visited cell is
  a read or a write.
- "Could you avoid the O(n^2) fresh-grid allocation?" -> No -- the
  problem's return value IS an `n x n` grid; that allocation is the
  answer itself, not overhead to optimize away.


================================================================================
RELATED PROBLEMS
================================================================================
- Spiral Matrix (LC 54, this topic, 003) -- the read-direction twin of
  this exact traversal.
- Rotate Image (LC 48, this topic, 002) -- another ring-based matrix
  technique, useful to contrast boundary-shrinking style against
  layer-peeling style.
================================================================================
"""

import time
from typing import List


class Solution:
    def generateMatrix(self, n: int) -> List[List[int]]:
        matrix = [[0] * n for _ in range(n)]
        top, bottom = 0, n - 1
        left, right = 0, n - 1
        num = 1

        while top <= bottom and left <= right:
            for col in range(left, right + 1):
                matrix[top][col] = num
                num += 1
            top += 1

            for row in range(top, bottom + 1):
                matrix[row][right] = num
                num += 1
            right -= 1

            if top <= bottom:
                for col in range(right, left - 1, -1):
                    matrix[bottom][col] = num
                    num += 1
                bottom -= 1

            if left <= right:
                for row in range(bottom, top - 1, -1):
                    matrix[row][left] = num
                    num += 1
                left += 1

        return matrix


def _generate_via_coordinate_list(n: int) -> List[List[int]]:
    """Priced-not-shipped alternative: build the spiral coordinate order
    first (adapted from 003's boundary walk, but collecting coordinates
    instead of values), then zip against 1..n^2. Used only as a
    cross-check oracle."""
    coords = []
    top, bottom, left, right = 0, n - 1, 0, n - 1
    while top <= bottom and left <= right:
        for col in range(left, right + 1):
            coords.append((top, col))
        top += 1
        for row in range(top, bottom + 1):
            coords.append((row, right))
        right -= 1
        if top <= bottom:
            for col in range(right, left - 1, -1):
                coords.append((bottom, col))
            bottom -= 1
        if left <= right:
            for row in range(bottom, top - 1, -1):
                coords.append((row, left))
            left += 1

    matrix = [[0] * n for _ in range(n)]
    for num, (r, c) in enumerate(coords, start=1):
        matrix[r][c] = num
    return matrix


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (3, [[1, 2, 3], [8, 9, 4], [7, 6, 5]]),
        (1, [[1]]),
        (2, [[1, 2], [4, 3]]),
        (4, [[1, 2, 3, 4], [12, 13, 14, 5], [11, 16, 15, 6], [10, 9, 8, 7]]),
    ]
    for n, expected in cases:
        got = sol.generateMatrix(n)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  generateMatrix({n}) -> {got} (expected {expected})")

    print()
    print("SELF-CHECK -- every value 1..n^2 appears exactly once, for n=1..20")
    print("-" * 72)
    coverage_ok = True
    for n in range(1, 21):
        mat = sol.generateMatrix(n)
        flat = sorted(v for row in mat for v in row)
        expected_flat = list(range(1, n * n + 1))
        if flat != expected_flat:
            coverage_ok = False
            print(f"FAIL  n={n}: values do not form a clean 1..{n * n} permutation")
    all_ok &= coverage_ok
    print(f"{'PASS' if coverage_ok else 'FAIL'}  all n=1..20 produce a clean 1..n^2 permutation")

    print()
    print("CROSS-CHECK -- direct boundary write vs coordinate-list-then-zip, n=1..25")
    print("-" * 72)
    mismatch = 0
    for n in range(1, 26):
        a = sol.generateMatrix(n)
        b = _generate_via_coordinate_list(n)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {25 - mismatch}/25 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- direct boundary write vs coordinate-list-then-zip")
    print("-" * 72)
    n = 600
    t0 = time.perf_counter()
    sol.generateMatrix(n)
    direct_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    _generate_via_coordinate_list(n)
    twophase_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n}:")
    print(f"  direct boundary write [chosen]:      {direct_ms:8.2f} ms")
    print(f"  coordinate-list-then-zip [priced]:   {twophase_ms:8.2f} ms")
    if direct_ms < twophase_ms:
        print(f"  measured: direct write is {twophase_ms / direct_ms:.2f}x FASTER here -- the "
              f"two-phase version pays for materializing an n^2-length coordinate list AND "
              f"then a second enumerate() pass over it, real O(n^2) extra allocation the "
              f"single-pass version never does.")
    else:
        print(f"  measured: the two-phase version is {direct_ms / twophase_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
