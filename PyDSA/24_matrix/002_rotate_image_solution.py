"""
================================================================================
SOLUTION · LeetCode 48 · Rotate Image                                [Medium]
https://leetcode.com/problems/rotate-image/
================================================================================

THE CORE IDEA
--------------
A 90-degree clockwise rotation can be decomposed into two simpler, fully
in-place operations: TRANSPOSE (flip over the main diagonal, `matrix[i][j]
<-> matrix[j][i]`), then REVERSE EACH ROW. Because the matrix is
guaranteed square (`n x n`), the transpose never changes the shape, so it
can genuinely be done with in-place swaps (unlike 001 Transpose Matrix,
where a non-square input forces a fresh array). Composing the two:
    rotated[i][j] = transpose(matrix)[i][n-1-j]   (reverse row i)
                  = matrix[n-1-j][i]               (definition of transpose)
and `matrix[n-1-j][i]` is exactly the closed-form formula for "rotate
`(row, col)` 90 degrees clockwise" -- the element that used to be `n-1-j`
rows down and `i` columns across moves to `(i, j)`. Two O(n^2) passes,
zero extra memory.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded) -- allocate a fresh `n x n`
matrix and directly place `rotated[i][j] = matrix[n-1-j][i]` for every
cell, then copy back. Trivially correct, O(n^2) time, O(n^2) EXTRA space
-- and the problem statement explicitly forbids this ("DO NOT allocate
another 2D matrix").

Approach 1 (chosen) -- transpose in place (swap across the diagonal, only
visiting `j > i` so each pair is swapped exactly once), then reverse each
row in place (`row.reverse()` or a two-pointer swap). O(n^2) time, O(1)
extra space, exactly two clean passes.

Approach 2 (variant, coded for cross-check) -- layer-by-layer 4-way
rotation: peel the matrix into concentric square "rings" (`n // 2` of
them); for each ring, walk its top edge and, for every position, cycle
FOUR cells at once (top -> right -> bottom -> left -> top) directly into
their rotated destinations. Same O(n^2) time and O(1) space as Approach 1,
but does the rotation in a single conceptual pass over each ring instead
of two passes over the whole matrix -- the classic "harder to get right
the first time, but the one interviewers sometimes ask for by name"
version.


================================================================================
STEP BY STEP TRACE
================================================================================
matrix (3x3):
    [1, 2, 3]
    [4, 5, 6]
    [7, 8, 9]

Step 1 -- transpose in place, swapping only (i, j) with j > i:
    swap (0,1)<->(1,0): 2<->4
        [1, 4, 3]
        [2, 5, 6]
        [7, 8, 9]
    swap (0,2)<->(2,0): 3<->7
        [1, 4, 7]
        [2, 5, 6]
        [3, 8, 9]
    swap (1,2)<->(2,1): 6<->8
        [1, 4, 7]
        [2, 5, 8]
        [3, 6, 9]

Step 2 -- reverse each row:
    row 0: [1,4,7] -> [7,4,1]
    row 1: [2,5,8] -> [8,5,2]
    row 2: [3,6,9] -> [9,6,3]

Final:
    [7, 4, 1]
    [8, 5, 2]
    [9, 6, 3]

Matches: the top-left `1` moved to the top-right corner, exactly what a
clockwise 90-degree turn does to a corner element.

Layer-by-layer cross-check (same input, ring 0 only since n=3 has one
full ring plus an untouched center cell):
    first=0, last=2. For offset i=0: top=matrix[0][0]=1.
        matrix[0][0] = matrix[2][0] = 7      -> left column feeds top row
        matrix[2][0] = matrix[2][2] = 9      -> bottom row feeds left column
        matrix[2][2] = matrix[0][2] = 3      -> right column feeds bottom row
        matrix[0][2] = top = 1               -> saved top feeds right column
    for offset i=1: top=matrix[0][1]=2, same 4-way cycle with the middle
    edge cells. Center cell (1,1) belongs to no ring and is never touched
    -- correctly, since the center of an odd-sized matrix maps to itself
    under any rotation.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time     Space   Mutates input?
    --------------------------------------------------------------------
    Fresh matrix [priced, forbidden]  O(n^2)   O(n^2)   no (writes a copy)
    Transpose + reverse rows [chosen] O(n^2)   O(1)     YES, in place
    Layer-by-layer 4-way [variant]    O(n^2)   O(1)     YES, in place


================================================================================
EDGE CASES
================================================================================
    n == 1              -> single cell, transpose loop body never runs
                            (no j > 0 when i == 0), row-reverse of a
                            length-1 row is a no-op; rotation is trivially
                            itself.
    n even (e.g. 4)      -> every cell belongs to some ring; layer-by-layer
                            runs `n // 2` full rings with no leftover
                            center cell.
    n odd (e.g. 3, 5)    -> the exact center cell `(n//2, n//2)` belongs to
                            no ring and must be left untouched by the
                            layer-by-layer approach -- it maps to itself
                            under rotation, which transpose+reverse handles
                            automatically (it's on the diagonal, so the
                            transpose swap loop naturally skips it since
                            `j > i` excludes `i == j`).
    Rotating 4 times      -> should return to the original matrix; a good
                            self-check (`rotate` applied n=4 times is the
                            identity operation for ANY square matrix).


================================================================================
COMMON MISTAKES
================================================================================
1. Transposing with `for i in range(n): for j in range(n):` (all pairs,
   not just `j > i`) -- swaps every pair TWICE, which undoes the
   transpose entirely and leaves the matrix unchanged.
2. Reversing rows BEFORE transposing, or reversing columns instead of
   rows after transposing -- either produces a COUNTER-clockwise rotation
   instead of clockwise; the two operations do not commute.
3. Allocating a new matrix "to make it easier" despite the explicit
   in-place constraint -- functionally correct but violates the stated
   requirement and loses the interview signal being tested.
4. In the layer-by-layer variant, using `range(first, last)` (inclusive
   of `last`) for the offset loop instead of `range(first, last)` used
   correctly with `last` EXCLUSIVE of the corner already covered by
   offset 0 -- double-swaps the corner cell of each ring.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "How would you rotate counter-clockwise instead?" -> Either transpose
  then reverse each COLUMN (instead of each row), or reverse each row
  FIRST and then transpose -- order matters and flips the rotation
  direction.
- "How would you rotate by 180 degrees?" -> Reverse every row AND reverse
  the row order (or equivalently, rotate 90 degrees clockwise twice) --
  no transpose needed at all, since 180 degrees is just "flip both axes."
- "What if the matrix weren't square?" -> In-place is then IMPOSSIBLE --
  an `m x n` matrix rotates into an `n x m` matrix, a different shape, so
  a fresh array is mandatory; this is precisely 001 Transpose Matrix's
  situation.
- "Can you do it with only O(1) auxiliary variables, not even a
  temporary row buffer?" -> Yes -- that's exactly what the layer-by-layer
  4-way swap achieves; `row.reverse()` also uses O(1) auxiliary space
  even though it looks like it needs a buffer, since Python reverses a
  list in place with a two-pointer swap internally.


================================================================================
RELATED PROBLEMS
================================================================================
- Transpose Matrix (LC 867, this topic, 001) -- step one of this
  algorithm in isolation; contrast the "must allocate for non-square" vs
  "square permits fully in-place" distinction.
- Set Matrix Zeroes (LC 73, this topic, 005) -- another matrix problem
  whose entire point is doing real work in O(1) extra space using the
  matrix itself as scratch storage.
- Spiral Matrix (LC 54, this topic, 003) -- another "walk the matrix ring
  by ring" technique, useful to compare against this problem's
  layer-by-layer variant.
================================================================================
"""

import copy
import time
from typing import List


class Solution:
    def rotate(self, matrix: List[List[int]]) -> None:
        """
        Do not return anything, modify matrix in-place instead.
        """
        n = len(matrix)

        # Step 1: transpose in place (swap across the main diagonal).
        for i in range(n):
            for j in range(i + 1, n):
                matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]

        # Step 2: reverse each row in place.
        for row in matrix:
            row.reverse()


def _rotate_layer_by_layer(matrix: List[List[int]]) -> None:
    """Priced-as-a-variant alternative, used only as a cross-check oracle.
    Rotates ring by ring with a 4-way cell cycle, O(1) extra space."""
    n = len(matrix)
    for layer in range(n // 2):
        first, last = layer, n - 1 - layer
        for i in range(first, last):
            offset = i - first
            top = matrix[first][i]
            # left -> top
            matrix[first][i] = matrix[last - offset][first]
            # bottom -> left
            matrix[last - offset][first] = matrix[last][last - offset]
            # right -> bottom
            matrix[last][last - offset] = matrix[i][last]
            # saved top -> right
            matrix[i][last] = top


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([[1, 2, 3], [4, 5, 6], [7, 8, 9]], [[7, 4, 1], [8, 5, 2], [9, 6, 3]]),
        (
            [[5, 1, 9, 11], [2, 4, 8, 10], [13, 3, 6, 7], [15, 14, 12, 16]],
            [[15, 13, 2, 5], [14, 3, 4, 1], [12, 6, 8, 9], [16, 7, 10, 11]],
        ),
        ([[1]], [[1]]),
        ([[1, 2], [3, 4]], [[3, 1], [4, 2]]),
    ]
    for matrix, expected in cases:
        got = [row[:] for row in matrix]
        sol.rotate(got)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  rotate({matrix}) -> {got} (expected {expected})")

    print()
    print("SELF-CHECK -- rotating 4 times returns the original matrix")
    print("-" * 72)
    original = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    working = [row[:] for row in original]
    for _ in range(4):
        sol.rotate(working)
    four_ok = working == original
    all_ok &= four_ok
    print(f"{'PASS' if four_ok else 'FAIL'}  4x rotate({original}) -> {working}")

    print()
    print("CROSS-CHECK -- transpose+reverse vs layer-by-layer 4-way, 300 random matrices")
    print("-" * 72)
    import random
    random.seed(48)
    mismatch = 0
    for _ in range(300):
        n = random.randint(1, 15)
        mat = [[random.randint(-500, 500) for _ in range(n)] for _ in range(n)]
        a = copy.deepcopy(mat)
        b = copy.deepcopy(mat)
        sol.rotate(a)
        _rotate_layer_by_layer(b)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {300 - mismatch}/300 agree ({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- transpose+reverse (2 passes) vs layer-by-layer (1 pass)")
    print("-" * 72)
    n = 800
    big = [[i * n + j for j in range(n)] for i in range(n)]

    a = copy.deepcopy(big)
    t0 = time.perf_counter()
    sol.rotate(a)
    two_pass_ms = (time.perf_counter() - t0) * 1000

    b = copy.deepcopy(big)
    t0 = time.perf_counter()
    _rotate_layer_by_layer(b)
    one_pass_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n} matrix, one full rotation:")
    print(f"  transpose + reverse rows (2 passes): {two_pass_ms:8.2f} ms")
    print(f"  layer-by-layer 4-way (1 pass):       {one_pass_ms:8.2f} ms")
    if two_pass_ms < one_pass_ms:
        print(f"  measured: transpose+reverse is {one_pass_ms / two_pass_ms:.2f}x FASTER here -- "
              f"both passes lean on `row.reverse()`, a C-level list method, while the "
              f"layer-by-layer version does four separate Python-level indexed "
              f"assignments per cell. Fewer, chunkier C-level operations beat more, "
              f"smaller pure-Python ones in CPython -- both are still O(n^2)/O(1),"
              f" this is a constant-factor artifact of this machine, not a complexity "
              f"difference.")
    else:
        print(f"  measured: layer-by-layer is {two_pass_ms / one_pass_ms:.2f}x faster here.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
