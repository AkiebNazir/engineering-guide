package main

/*
================================================================================
QUESTION · LeetCode 221 · Maximal Square                             [Medium]
https://leetcode.com/problems/maximal-square/
================================================================================

PROBLEM
-------
Given an m x n binary matrix filled with 0's and 1's, find the largest square
containing only 1's, and return its area.


EXAMPLES
--------
Example 1:
    Input:  matrix = [["1","0","1","0","0"],
                       ["1","0","1","1","1"],
                       ["1","1","1","1","1"],
                       ["1","0","0","1","0"]]
    Output: 4
    Explanation: the largest all-1s square is 2x2, area 4.

Example 2:
    Input:  matrix = [["0","1"],["1","0"]]
    Output: 1

Example 3:
    Input:  matrix = [["0"]]
    Output: 0


CONSTRAINTS
-----------
    m == matrix.length
    n == matrix[i].length
    1 <= m, n <= 300
    matrix[i][j] is '0' or '1'.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Let dp[i][j] = the SIDE LENGTH of the largest all-1s square whose BOTTOM-RIGHT
corner is exactly at (i, j). A square of side k ending at (i, j) requires a
square of side (k-1) ending at each of the three cells (i-1, j), (i, j-1),
and (i-1, j-1) -- all three must support at least a (k-1)-square, or the
square ending at (i, j) is capped by whichever of the three is weakest.

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][j] means "side length of the biggest square with its
        bottom-right corner AT (i, j)", not "biggest square anywhere in the
        top-left i x j subgrid."
Hint 2: If matrix[i][j] == '0', dp[i][j] = 0 (no square can end here).
Hint 3: If matrix[i][j] == '1':
        dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
        (the MIN, not the max -- a square is only as big as its weakest
        supporting corner).
Hint 4: The final answer is max(dp) ** 2 (area), not max(dp) itself.

COMPLEXITY TARGET
------------------
    Time:  O(m * n)
    Space: O(n)  (rolling row -- needs the diagonal too, one extra scalar)
================================================================================
*/

// TODO: Implement the stub
