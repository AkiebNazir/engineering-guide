"""
================================================================================
SOLUTION · LeetCode 64 · Minimum Path Sum                             [Medium]
https://leetcode.com/problems/minimum-path-sum/
================================================================================

THE CORE IDEA
--------------
Same predecessor rule as 001 (Unique Paths) -- (i, j) is only reachable from
above or from the left -- but the objective changes from COUNT to COST, and
the combinator changes from SUM to MIN:

    dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1])

The first row and first column have only one predecessor each, so they are
forced running sums, not a "1" base case like 001.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): recurse right/down from (0,0),
try every path, keep the min sum. O(2^(m+n)) time -- exponential re-exploration
of the same cells, exactly like 001's uncached recursion.

Approach 1 (memoized top-down, 2D cache) -- recurse with an (m x n) memo of
"min cost to reach the BOTTOM-RIGHT from here", or equivalently from (0,0)
forward with a visited-cache. O(m*n) time, O(m*n) space.

Approach 2 (bottom-up tabulation, full 2D table) [checked] -- fill row by
row, first row/col are running sums, interior cells take grid[i][j] +
min(above, left). O(m*n) time, O(m*n) space.

Approach 3 (space-optimized, rolling 1D row) [checked, shipped] -- dp[i][j]
only reads the row above (row[j], not yet overwritten) and the current row's
own left neighbor (row[j-1], already updated). One array of length n, updated
left to right in place. O(m*n) time, O(n) space.


================================================================================
STEP BY STEP TRACE
================================================================================
grid = [[1,3,1],
        [1,5,1],
        [4,2,1]]

Full 2D table:
        j=0  j=1  j=2
    i=0:  1    4    5     <- running sum along the top row: 1, 1+3, 1+3+1
    i=1:  2    7    6     dp[1][0]=1+1=2 (left col, running sum)
                          dp[1][1]=5+min(4,2)=5+2=7
                          dp[1][2]=1+min(5,7)=1+5=6
    i=2:  6    8    7     dp[2][0]=4+2=6
                          dp[2][1]=2+min(7,6)=2+6=8
                          dp[2][2]=1+min(6,8)=1+6=7

Answer: dp[2][2] = 7.  MATCHES expected.

Rolling-row version, same grid:
    start (row 0):      row = [1, 4, 5]
    after row 1: row[0]=1+row[0](=1)=2
                 row[1]=5+min(row[1](=4,old), row[0](=2,new))=5+2=7
                 row[2]=1+min(row[2](=5,old), row[1](=7,new))=1+5=6
                 row = [2, 7, 6]
    after row 2: row[0]=4+row[0](=2)=6
                 row[1]=2+min(row[1](=7,old), row[0](=6,new))=2+6=8
                 row[2]=1+min(row[2](=6,old), row[1](=8,new))=1+6=7
                 row = [6, 8, 7]
    return row[-1] = 7.  MATCHES.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time        Space      Mutates input?
    ---------------------------------  ----------  ---------  --------------
    Brute force recursion (no memo)    O(2^(m+n))  O(m+n)     no
    Memoized top-down, 2D cache        O(m*n)      O(m*n)     no
    Bottom-up tabulation, full table   O(m*n)      O(m*n)     no
    Rolling row [chosen]               O(m*n)      O(n)       no


================================================================================
EDGE CASES
================================================================================
    1x1 grid              -> answer is just grid[0][0], no moves needed --
                              the rolling row of length 1 returns it directly.
    Single row or column  -> forced straight-line path, dp degenerates to a
                              running cumulative sum -- no min() ever fires.
    All zeros              -> answer 0, sanity check that min-of-zeros stays 0
                              (not accidentally short-circuited by falsy checks).
    Large values (up to 200 per cell, 200x200 grid) -> max possible sum
                              200*400 = 80,000, nowhere near overflow in
                              Python's unbounded ints.


================================================================================
COMMON MISTAKES
================================================================================
1. Reusing 001's "sum both predecessors" recurrence out of muscle memory
   instead of "min of the two, plus this cell's own cost" -- the two
   problems share a skeleton but combine predecessors differently.

2. Forgetting the first row/column are forced CUMULATIVE SUMS, not copies of
   grid[0][j] or grid[i][0] in isolation -- dp[0][2] must include dp[0][1],
   not just grid[0][2].

3. In the rolling-row version, updating right-to-left -- breaks the same way
   as 001: row[j-1] must already be THIS row's value when row[j] reads it.

4. Off-by-one when initializing the rolling row to grid[0] verbatim rather
   than its running-sum version -- row = grid[0][:] is WRONG; row[0] must
   stay grid[0][0] but row[1] must already be grid[0][0]+grid[0][1].


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if negative numbers were allowed?
A: Min-path-sum DP still works (it's not a shortest-path-with-negative-cycles
   problem since the DAG of moves is acyclic) -- the recurrence is unchanged.

Q: Can you reconstruct the actual minimizing path, not just its cost?
A: Keep the full 2D table (Approach 2, not the rolling row) and walk
   backwards from (m-1,n-1), at each step moving to whichever predecessor
   equals dp[i][j] - grid[i][j].

Q: How does this relate to Dijkstra's algorithm?
A: This grid IS a DAG shortest-path problem where every edge only points
   down or right -- DP here is exactly Dijkstra specialized to a DAG with no
   need for a priority queue, since the topological order (row-major) is
   already known in advance.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 62   Unique Paths (001 -- same predecessor shape, sum-of-counts
            instead of min-of-costs)
    LC 63   Unique Paths II (002 -- same shape + obstacle zeroing)
    LC 120  Triangle (min path sum on a triangular grid)
    LC 931  Minimum Falling Path Sum (three predecessors instead of two)
================================================================================
"""


class Solution:
    def minPathSum(self, grid: list[list[int]]) -> int:
        """✅ Rolling-row DP. O(m*n) time, O(n) space. Does not mutate grid."""
        m, n = len(grid), len(grid[0])
        row = [0] * n
        row[0] = grid[0][0]
        for j in range(1, n):
            row[j] = row[j - 1] + grid[0][j]

        for i in range(1, m):
            row[0] += grid[i][0]
            for j in range(1, n):
                row[j] = grid[i][j] + min(row[j], row[j - 1])
        return row[-1]

    def minPathSum_full_table(self, grid: list[list[int]]) -> int:
        """Alternative: full 2D tabulation, O(m*n) time and space -- useful
        when the actual path also needs to be reconstructed."""
        m, n = len(grid), len(grid[0])
        dp = [[0] * n for _ in range(m)]
        dp[0][0] = grid[0][0]
        for j in range(1, n):
            dp[0][j] = dp[0][j - 1] + grid[0][j]
        for i in range(1, m):
            dp[i][0] = dp[i - 1][0] + grid[i][0]
            for j in range(1, n):
                dp[i][j] = grid[i][j] + min(dp[i - 1][j], dp[i][j - 1])
        return dp[m - 1][n - 1]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[1, 3, 1], [1, 5, 1], [4, 2, 1]], 7),
        ([[1, 2, 3], [4, 5, 6]], 12),
        ([[1]], 1),
        ([[1, 2], [1, 1]], 3),
        ([[0, 0, 0], [0, 0, 0]], 0),
        ([[5]], 5),
    ]

    print("--- correctness: rolling-row vs full-table agree ---")
    for grid, want in cases:
        got_roll = sol.minPathSum([row[:] for row in grid])
        got_full = sol.minPathSum_full_table([row[:] for row in grid])
        ok = got_roll == want and got_full == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  grid={grid}  roll={got_roll} "
              f"full={got_full}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: confirm the rolling-row solution never mutates the
    # caller's grid (a common bug: writing dp values back into grid in
    # place "to save space" corrupts the caller's data).
    # --------------------------------------------------------------------
    print("\n--- DEMO: input grid is never mutated ---")
    grid = [[1, 3, 1], [1, 5, 1], [4, 2, 1]]
    before = [row[:] for row in grid]
    sol.minPathSum(grid)
    print(f"  grid before: {before}")
    print(f"  grid after:  {grid}")
    unchanged = grid == before
    print(f"  unchanged: {unchanged}")
    all_ok &= unchanged

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
