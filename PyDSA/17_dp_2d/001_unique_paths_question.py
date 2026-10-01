"""
================================================================================
QUESTION · LeetCode 62 · Unique Paths                                [Medium]
https://leetcode.com/problems/unique-paths/
================================================================================

PROBLEM
-------
A robot is located at the top-left corner of an m x n grid. The robot can
only move either down or right at any point in time. The robot is trying to
reach the bottom-right corner of the grid.

Return the number of possible unique paths.


EXAMPLES
--------
Example 1:
    Input:  m = 3, n = 7
    Output: 28

Example 2:
    Input:  m = 3, n = 2
    Output: 3
    Explanation: From top-left to bottom-right, there are 3 paths:
        Right -> Down -> Down
        Down -> Right -> Down
        Down -> Down -> Right


CONSTRAINTS
-----------
    1 <= m, n <= 100
    The answer is guaranteed to fit in a 32-bit integer.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the seed problem of the whole "2D grid DP" family. Every cell's
answer is the number of ways to REACH that cell, which is simply the sum of
the ways to reach the cell directly above it and the cell directly to its
left (those are the only two cells that can step into it).

PROGRESSIVE HINTS
------------------
Hint 1: Let dp[i][j] = number of distinct paths from (0,0) to (i,j).
Hint 2: dp[i][j] = dp[i-1][j] + dp[i][j-1] — the last move into (i,j) was
        either "down" (from above) or "right" (from the left).
Hint 3: The entire top row and entire left column can only be reached one
        way (a straight line of rights, or a straight line of downs) — base
        case dp[0][j] = dp[i][0] = 1.
Hint 4: You only ever read the row directly above the current row — you
        don't need the full 2D table. One rolling 1D array of length n
        suffices.

COMPLEXITY TARGET
------------------
    Time:  O(m * n)
    Space: O(n)   (rolling row; O(1) extra is possible via closed-form math)
================================================================================
"""


class Solution:
    def uniquePaths(self, m: int, n: int) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (3, 7, 28),
        (3, 2, 3),
        (1, 1, 1),
        (1, 10, 1),
        (10, 1, 1),
        (7, 3, 28),
        (23, 12, 193536720),
    ]
    for m, n, want in cases:
        got = sol.uniquePaths(m, n)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  m={m} n={n}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
