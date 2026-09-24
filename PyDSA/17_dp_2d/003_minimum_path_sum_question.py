"""
================================================================================
QUESTION · LeetCode 64 · Minimum Path Sum                            [Medium]
https://leetcode.com/problems/minimum-path-sum/
================================================================================

PROBLEM
-------
Given an m x n grid filled with non-negative numbers, find a path from top
left to bottom right which minimizes the sum of all numbers along the path.

You can only move either down or right at any point in time.


EXAMPLES
--------
Example 1:
    Input:  grid = [[1,3,1],[1,5,1],[4,2,1]]
    Output: 7
    Explanation: path 1 -> 3 -> 1 -> 1 -> 1 sums to 7.

Example 2:
    Input:  grid = [[1,2,3],[4,5,6]]
    Output: 12


CONSTRAINTS
-----------
    m == grid.length
    n == grid[i].length
    1 <= m, n <= 200
    0 <= grid[i][j] <= 200


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Same predecessor shape as 001/002 (only "up" and "left" feed a cell), but now
each cell carries a COST instead of a count of 1, and you take the CHEAPER of
the two predecessors instead of SUMMING them.

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][j] = the minimum cost to reach (i, j) from (0, 0).
Hint 2: dp[i][j] = grid[i][j] + min(dp[i-1][j], dp[i][j-1]).
Hint 3: Base case: dp[0][0] = grid[0][0]. Top row and left column are forced
        (only one predecessor each) -- they're running cumulative sums.
Hint 4: Same rolling-row space optimization as 001 applies here too.

COMPLEXITY TARGET
------------------
    Time:  O(m * n)
    Space: O(n)  (rolling row)
================================================================================
"""


class Solution:
    def minPathSum(self, grid: list[list[int]]) -> int:
        # YOUR CODE HERE
        pass


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
    for grid, want in cases:
        grid_copy = [row[:] for row in grid]
        got = sol.minPathSum(grid_copy)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  grid={grid}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
