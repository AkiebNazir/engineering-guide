"""
================================================================================
QUESTION · LeetCode 63 · Unique Paths II                              [Medium]
https://leetcode.com/problems/unique-paths-ii/
================================================================================

PROBLEM
-------
You are given an m x n integer array grid. There is a robot initially
located at the top-left corner (grid[0][0]). The robot tries to move to the
bottom-right corner (grid[m-1][n-1]). The robot can only move either down or
right at any point in time.

An obstacle and space are marked as 1 (obstacle) or 0 (empty) respectively
in grid. A path that the robot takes cannot include any square that is an
obstacle.

Return the number of possible unique paths that the robot can take to reach
the bottom-right corner.


EXAMPLES
--------
Example 1:
    Input:  obstacleGrid = [[0,0,0],[0,1,0],[0,0,0]]
    Output: 2
    Explanation: There is one obstacle in the middle of the 3x3 grid. There
    are two ways to reach the bottom-right corner:
        1. Right -> Right -> Down -> Down
        2. Down -> Down -> Right -> Right

Example 2:
    Input:  obstacleGrid = [[0,1],[0,0]]
    Output: 1


CONSTRAINTS
-----------
    m == obstacleGrid.length
    n == obstacleGrid[i].length
    1 <= m, n <= 100
    obstacleGrid[i][j] is 0 or 1.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Same recurrence as Unique Paths (001), plus one rule: an obstacle cell has
ZERO ways to reach it (nothing may land there), and it also contributes zero
to anything downstream of it. This single tweak kills the closed-form
binomial-coefficient shortcut from 001 entirely -- the DP table is now the
only tool.

PROGRESSIVE HINTS
------------------
Hint 1: Same dp[i][j] = dp[i-1][j] + dp[i][j-1] recurrence as 001.
Hint 2: Except: if grid[i][j] == 1 (obstacle), force dp[i][j] = 0 regardless
        of what the recurrence would otherwise compute.
Hint 3: The base case changes too -- dp[0][0] = 1 ONLY if grid[0][0] == 0.
        If the very start cell is itself an obstacle, the answer is 0.
Hint 4: The top row and left column are no longer automatically all 1s --
        an obstacle anywhere along the top row blocks every cell after it in
        that row (there's no way around it when you can only move right).

COMPLEXITY TARGET
------------------
    Time:  O(m * n)
    Space: O(n)   (rolling row)
================================================================================
"""

from typing import List


class Solution:
    def uniquePathsWithObstacles(self, obstacleGrid: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[0, 0, 0], [0, 1, 0], [0, 0, 0]], 2),
        ([[0, 1], [0, 0]], 1),
        ([[1]], 0),
        ([[0]], 1),
        ([[1, 0]], 0),
        ([[0], [1], [0]], 0),
        ([[0, 0], [1, 1], [0, 0]], 0),
    ]
    for grid, want in cases:
        got = sol.uniquePathsWithObstacles([row[:] for row in grid])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  grid={grid}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
