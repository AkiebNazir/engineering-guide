"""
================================================================================
SOLUTION · LeetCode 867 · Transpose Matrix                           [Easy]
https://leetcode.com/problems/transpose-matrix/
================================================================================

THE CORE IDEA
--------------
The transpose swaps rows and columns: the element at `(i, j)` in the input
lands at `(j, i)` in the output. That single line of index arithmetic is
the entire problem -- `result[j][i] = matrix[i][j]` for every cell. The
only trap is dimensions: an `m x n` matrix transposes to an `n x m`
matrix, so unless the input happens to be square, you CANNOT write the
result back into the same array shape -- a fresh `n x m` container is
required (this is exactly why 002 Rotate Image, which IS always square,
can do its transpose step truly in place while this problem, in general,
cannot).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (priced, not coded) -- build the result with nested list
comprehensions indexed by hand, one cell at a time via
`[[matrix[i][j] for i in range(m)] for j in range(n)]`. Same O(mn) time and
O(mn) space as the chosen approach; purely a style choice, not a different
algorithm, so there's nothing to "price" beyond noting it reads worse.

Approach 1 (chosen) -- explicit double loop writing `result[j][i] =
matrix[i][j]`. O(mn) time, O(mn) space for the output (unavoidable -- the
output IS the answer). Clearest to explain out loud in an interview.

Approach 2 (variant, coded for cross-check) -- `zip(*matrix)` transposes
in one C-level call: it treats each row as an iterable and regroups "the
i-th element of every row" into a new tuple. `[list(row) for row in
zip(*matrix)]` is the idiomatic Pythonic one-liner and is used below only
as an independent cross-check oracle, not as the primary teaching
solution (an interviewer wants to see you can do the index arithmetic by
hand, not that you know a stdlib trick).

Approach 3 (variant, square-only, NOT applicable here in general) --
in-place swap `matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]`
for `j > i`. Only valid when `m == n`, because only then does the output
shape match the input shape. This is exactly the first half of 002 Rotate
Image's technique.


================================================================================
STEP BY STEP TRACE
================================================================================
matrix (2x3):
    [1, 2, 3]
    [4, 5, 6]

m = 2 rows, n = 3 cols -> result is 3x2, prefilled with zeros:
    [0, 0]
    [0, 0]
    [0, 0]

    i=0,j=0: result[0][0] = matrix[0][0] = 1
    i=0,j=1: result[1][0] = matrix[0][1] = 2
    i=0,j=2: result[2][0] = matrix[0][2] = 3
    i=1,j=0: result[0][1] = matrix[1][0] = 4
    i=1,j=1: result[1][1] = matrix[1][1] = 5
    i=1,j=2: result[2][1] = matrix[1][2] = 6

result:
    [1, 4]
    [2, 5]
    [3, 6]

Read it visually: column 0 of the input (1, 4) became row 0 of the
output; column 1 (2, 5) became row 1; column 2 (3, 6) became row 2.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time     Space     Mutates input?
    ------------------------------------------------------------------
    Nested comprehension            O(mn)    O(mn)     no
    Explicit double loop [chosen]   O(mn)    O(mn)     no
    zip(*matrix) [cross-check]      O(mn)    O(mn)     no
    In-place swap (square only)     O(n^2)   O(1)      YES (but n==m required)

    m, n = input row/col counts. The O(mn) output space is mandatory for
    any non-square input -- there is no way to produce a differently-
    shaped answer without allocating it.


================================================================================
EDGE CASES
================================================================================
    1x1 matrix        -> transpose of a single cell is itself; loop bodies
                          run exactly once, result == input by value.
    Single row (1xn)   -> transposes to a single column (nx1); output
                          shape genuinely differs from input shape.
    Single column (nx1) -> transposes to a single row (1xn); same point,
                          mirrored.
    Square matrix      -> the only case where in-place swapping is even
                          possible, since only then do input and output
                          shapes coincide.
    Negative / large
    values             -> pure data movement, no arithmetic on the values
                          themselves, so sign and magnitude never matter.


================================================================================
COMMON MISTAKES
================================================================================
1. Trying to write the transpose back into `matrix` in place for a
   non-square input -- the shapes don't match (`m x n` vs `n x m`), so
   there's no cell to swap with once you're past the last valid index of
   the shorter dimension.
2. Swapping `result[i][j] = matrix[j][i]` while iterating `i` over
   `range(n)` and `j` over `range(m)` but forgetting to size `result` as
   `n x m` (not `m x n`) first -- causes an `IndexError` the moment the
   matrix isn't square.
3. Using `zip(*matrix)` and forgetting to wrap each tuple in `list(...)`
   -- LeetCode (and most callers) expect a list of lists, not a list of
   tuples; this passes locally but fails type-strict graders.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do this in place?" -> Only if the matrix is square; walk
  through why (shape must be invariant), then show the `j > i` swap loop,
  which is precisely half of 002 Rotate Image's technique.
- "What if the matrix is a numpy array?" -> `matrix.T` or `np.transpose`
  is O(1) -- it returns a VIEW with swapped strides, no data is copied at
  all until something forces materialization. Worth mentioning to show
  awareness that the "must copy" story is specific to plain Python lists.
- "How would you transpose a huge matrix that doesn't fit in memory?" ->
  Block/tile the matrix and transpose sub-blocks in place, or transpose
  on disk in chunks (this is the real technique behind cache-oblivious
  transpose algorithms) -- outside interview scope but worth naming.


================================================================================
RELATED PROBLEMS
================================================================================
- Rotate Image (LC 48, this topic, 002) -- transpose is literally step one
  of the standard in-place 90-degree rotation, which only works because
  Rotate Image's matrix is always square.
- Diagonal Traverse (LC 498, this topic, 008) -- another problem whose
  entire difficulty is getting the `(row, col)` index arithmetic exactly
  right across a 2D grid.
================================================================================
"""

import time
from typing import List


class Solution:
    def transpose(self, matrix: List[List[int]]) -> List[List[int]]:
        m, n = len(matrix), len(matrix[0])
        result = [[0] * m for _ in range(n)]
        for i in range(m):
            for j in range(n):
                result[j][i] = matrix[i][j]
        return result


def _zip_transpose(matrix: List[List[int]]) -> List[List[int]]:
    """Priced-not-shipped alternative, used only as a cross-check oracle."""
    return [list(row) for row in zip(*matrix)]


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[1, 4, 7], [2, 5, 8], [3, 6, 9]]),
        ([[1, 2, 3], [4, 5, 6]], [[1, 4], [2, 5], [3, 6]]),
        ([[1]], [[1]]),
        ([[1, 2]], [[1], [2]]),
        ([[1], [2]], [[1, 2]]),
        ([[-1, -2], [3, 4]], [[-1, 3], [-2, 4]]),
    ]
    for matrix, expected in cases:
        got = sol.transpose([row[:] for row in matrix])
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  transpose({matrix}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- explicit double loop vs zip(*matrix), 500 random matrices")
    print("-" * 72)
    import random
    random.seed(24)
    mismatch = 0
    for _ in range(500):
        m = random.randint(1, 12)
        n = random.randint(1, 12)
        mat = [[random.randint(-1000, 1000) for _ in range(n)] for _ in range(m)]
        a = sol.transpose([row[:] for row in mat])
        b = _zip_transpose([row[:] for row in mat])
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {500 - mismatch}/500 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- explicit double loop vs zip(*matrix), measured live")
    print("-" * 72)
    big = [[i * 100 + j for j in range(100)] for i in range(1000)]

    t0 = time.perf_counter()
    sol.transpose([row[:] for row in big])
    loop_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    _zip_transpose([row[:] for row in big])
    zip_ms = (time.perf_counter() - t0) * 1000

    print(f"1000x100 matrix, one transpose call:")
    print(f"  explicit Python double loop: {loop_ms:8.3f} ms")
    print(f"  zip(*matrix) [C-level]:      {zip_ms:8.3f} ms")
    if zip_ms < loop_ms:
        print(f"  measured: zip(*matrix) is {loop_ms / zip_ms:.2f}x FASTER here -- CPython's "
              f"C-level iterator protocol behind zip() beats an interpreted nested "
              f"Python loop, the same shape of result seen throughout this repo when "
              f"an index-juggling loop is compared against a built-in doing the same "
              f"work in C. The explicit loop remains the right thing to WRITE in an "
              f"interview, since it demonstrates the index arithmetic rather than a "
              f"library trick.")
    else:
        print(f"  measured: the explicit loop is {zip_ms / loop_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
