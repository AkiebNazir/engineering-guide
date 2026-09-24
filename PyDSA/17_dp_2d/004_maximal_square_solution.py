"""
================================================================================
SOLUTION · LeetCode 221 · Maximal Square                              [Medium]
https://leetcode.com/problems/maximal-square/
================================================================================

THE CORE IDEA
--------------
dp[i][j] = side length of the largest all-1s square whose BOTTOM-RIGHT corner
is AT (i, j) (not "anywhere in the top-left subrectangle" -- that distinction
is the whole problem). A square of side k ending at (i, j) needs a square of
side (k-1) ending at all THREE of (i-1,j), (i,j-1), and (i-1,j-1) --
extending a square down-and-right by one ring requires the entire L-shaped
border to already be square-supported on all three neighboring corners:

    dp[i][j] = 0                                              if cell is '0'
    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1   if cell is '1'

The MIN is the key insight -- a square is only as large as its weakest
supporting neighbor, exactly like a chain being as strong as its weakest link.
Track the running max of dp[i][j] while filling the table; answer = max^2.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): for every cell that's '1', try
every possible square size k = 1, 2, 3, ... and check all k^2 cells are '1'.
O((m*n) * min(m,n)^2) time -- to check a size-k square you re-scan k^2 cells
from scratch instead of reusing smaller squares already verified. Correct
but redundant across overlapping sub-squares.

Approach 1 (memoized top-down, 2D cache) -- recurse on
"largest square ending at (i,j)", cache each cell. O(m*n) time, O(m*n) space.

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill dp row by
row using the min-of-three-neighbors recurrence, track the running max.
O(m*n) time, O(m*n) space.

Approach 3 (space-optimized, rolling 1D row + one diagonal scalar) [checked,
shipped] -- dp[i][j] reads (i-1,j), (i,j-1), (i-1,j-1). Keep one row plus a
single scalar holding "the pre-overwrite value of dp[i-1][j-1]" (the diagonal
would otherwise be clobbered the instant row[j-1] is updated in place).
O(m*n) time, O(n) space.


================================================================================
STEP BY STEP TRACE
================================================================================
matrix = [["1","0","1","0","0"],
          ["1","0","1","1","1"],
          ["1","1","1","1","1"],
          ["1","0","0","1","0"]]

Full 2D dp table (side lengths):
        j=0 j=1 j=2 j=3 j=4
    i=0:  1   0   1   0   0
    i=1:  1   0   1   1   1
    i=2:  1   1   1   2   2      <- dp[2][3]=min(dp[1][3]=1,dp[2][2]=1,dp[1][2]=1)+1=2
    i=3:  1   0   0   1   0      <- dp[2][4]=min(dp[1][4]=1,dp[2][3]=2,dp[1][3]=1)+1=2

max(dp) = 2  ->  area = 2*2 = 4.  MATCHES expected.

The 2x2 square of 1's lives at rows 1-2, cols 2-3 -- exactly where dp hits 2.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time        Space      Mutates input?
    ---------------------------------  ----------  ---------  --------------
    Brute force (re-scan every size)   O(mn*min(m,n)^2)  O(1)  no
    Memoized top-down, 2D cache        O(m*n)      O(m*n)     no
    Bottom-up tabulation, full table   O(m*n)      O(m*n)     no
    Rolling row + diagonal [chosen]    O(m*n)      O(n)       no


================================================================================
EDGE CASES
================================================================================
    All zeros              -> dp stays all 0, answer 0 -- max() over an
                               all-zero table correctly returns 0, not an
                               error on an "empty" max.
    Single row or column   -> no 2x2+ square possible, every '1' contributes
                               dp=1 at best, answer is 0 or 1 (area 0 or 1).
    Entire grid all 1's    -> dp grows diagonally, min(m,n) is the cap
                               (e.g. 3x3 all ones -> dp[2][2]=3, area 9).
    matrix cells as strings ('1'/'0', not ints) -- must compare to the
                               string '1', an int-vs-str bug silently makes
                               every comparison false.


================================================================================
COMMON MISTAKES
================================================================================
1. Using MAX of the three neighbors instead of MIN -- produces a square
   larger than what the weakest corner can actually support, silently
   overcounting the area on grids where the three neighbor squares differ.

2. Forgetting the diagonal term dp[i-1][j-1] entirely and only looking at
   up/left -- that recurrence is 001/003's "path" shape, not this problem's
   "square" shape; it produces a plausible but wrong number since it never
   checks the corner cell is actually part of a square, not just a path.

3. Returning max(dp) (the side length) instead of max(dp) ** 2 (the area) --
   the problem asks for area explicitly.

4. In the rolling-row space optimization, forgetting to snapshot the
   pre-update diagonal value BEFORE overwriting row[j-1] in place -- by the
   time row[j] is computed, row[j-1] already holds THIS row's new value,
   not the old dp[i-1][j-1] the recurrence actually needs.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if you needed the largest RECTANGLE of 1's, not square?
A: Different problem (LC 85, Maximal Rectangle) -- typically solved with a
   monotonic-stack "largest rectangle in histogram" pass per row, not this
   min-of-three-neighbors recurrence (rectangles don't have the square's
   symmetric-growth property).

Q: Can you return the actual coordinates of the largest square, not just
   its area?
A: Keep the full 2D table (Approach 2) and track (i, j) where the max was
   achieved -- the square spans rows [i-side+1, i], cols [j-side+1, j].

Q: How would this change for a matrix of arbitrary non-negative weights
   instead of binary 0/1?
A: It wouldn't reduce cleanly to this recurrence -- "largest square" is
   inherently a binary/threshold notion; a weighted version becomes a
   different problem (e.g. max sum square submatrix, solved via 2D prefix
   sums, not this DP).


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 85   Maximal Rectangle (harder cousin, monotonic stack per row)
    LC 1277 Count Square Submatrices with All Ones (same recurrence, SUM
            the dp table instead of taking its max -- every dp[i][j] value
            counts that many distinct squares ending there)
    LC 64   Minimum Path Sum (003 -- same "look at up/left/diag neighbors"
            2D DP family, different combinator)
================================================================================
"""


class Solution:
    def maximalSquare(self, matrix: list[list[str]]) -> int:
        """✅ Rolling-row + diagonal scalar DP. O(m*n) time, O(n) space."""
        m, n = len(matrix), len(matrix[0])
        row = [0] * n
        best = 0
        for i in range(m):
            prev_diag = 0  # dp[i-1][-1] before this row starts, i.e. 0
            for j in range(n):
                # snapshot dp[i-1][j] BEFORE it gets overwritten by dp[i][j]
                up = row[j]
                if matrix[i][j] == "1":
                    left = row[j - 1] if j > 0 else 0
                    row[j] = min(up, left, prev_diag) + 1
                else:
                    row[j] = 0
                prev_diag = up
                best = max(best, row[j])
        return best * best

    def maximalSquare_full_table(self, matrix: list[list[str]]) -> int:
        """Alternative: full 2D tabulation, O(m*n) time and space -- useful
        when the coordinates of the winning square are also needed."""
        m, n = len(matrix), len(matrix[0])
        dp = [[0] * n for _ in range(m)]
        best = 0
        for i in range(m):
            for j in range(n):
                if matrix[i][j] == "1":
                    if i == 0 or j == 0:
                        dp[i][j] = 1
                    else:
                        dp[i][j] = min(dp[i - 1][j], dp[i][j - 1],
                                        dp[i - 1][j - 1]) + 1
                    best = max(best, dp[i][j])
        return best * best


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([["1", "0", "1", "0", "0"],
          ["1", "0", "1", "1", "1"],
          ["1", "1", "1", "1", "1"],
          ["1", "0", "0", "1", "0"]], 4),
        ([["0", "1"], ["1", "0"]], 1),
        ([["0"]], 0),
        ([["1"]], 1),
        ([["1", "1"], ["1", "1"]], 4),
        ([["1", "1", "1"], ["1", "1", "1"], ["1", "1", "1"]], 9),
    ]

    print("--- correctness: rolling-row vs full-table agree ---")
    for matrix, want in cases:
        got_roll = sol.maximalSquare([row[:] for row in matrix])
        got_full = sol.maximalSquare_full_table([row[:] for row in matrix])
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  matrix={matrix}  roll={got_roll} "
              f"full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: prove the "MAX of neighbors" bug (mistake #1) actually
    # produces a wrong, inflated answer on a case where the three neighbor
    # squares genuinely differ.
    # --------------------------------------------------------------------
    print("\n--- DEMO: min-of-three (correct) vs max-of-three (buggy) ---")

    def maximal_square_buggy_max(matrix):
        m, n = len(matrix), len(matrix[0])
        dp = [[0] * n for _ in range(m)]
        best = 0
        for i in range(m):
            for j in range(n):
                if matrix[i][j] == "1":
                    if i == 0 or j == 0:
                        dp[i][j] = 1
                    else:
                        dp[i][j] = max(dp[i - 1][j], dp[i][j - 1],
                                        dp[i - 1][j - 1]) + 1  # BUG: max not min
                    best = max(best, dp[i][j])
        return best * best

    tricky = [["1", "1", "1", "0"],
              ["1", "1", "1", "0"],
              ["1", "1", "0", "1"],
              ["0", "0", "1", "1"]]
    correct = sol.maximalSquare_full_table([row[:] for row in tricky])
    buggy = maximal_square_buggy_max([row[:] for row in tricky])
    print(f"  grid: {tricky}")
    print(f"  correct (min-of-three): {correct}")
    print(f"  buggy   (max-of-three): {buggy}")
    diverged = buggy != correct
    print(f"  buggy version diverges from correct: {diverged}")
    all_ok &= (correct == 4)  # 2x2 square at rows0-1,cols0-1 is the real max

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
