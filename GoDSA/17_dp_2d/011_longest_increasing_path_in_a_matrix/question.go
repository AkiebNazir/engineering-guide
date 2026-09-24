package main

/*
================================================================================
QUESTION · LeetCode 329 · Longest Increasing Path in a Matrix           [Hard]
https://leetcode.com/problems/longest-increasing-path-in-a-matrix/
================================================================================

PROBLEM
-------
Given an m x n integers matrix, return the length of the longest increasing
path in matrix.

From each cell, you can either move in four directions: left, right, up, or
down. You may not move diagonally or move outside the boundary (i.e.,
wrap-around is not allowed).


EXAMPLES
--------
Example 1:
    Input:  matrix = [[9,9,4],[6,6,8],[2,1,1]]
    Output: 4
    Explanation: the longest increasing path is [1, 2, 6, 9].

Example 2:
    Input:  matrix = [[3,4,5],[3,2,6],[2,2,1]]
    Output: 4
    Explanation: the longest increasing path is [3, 4, 5, 6]. Moving
    diagonally is not allowed.

Example 3:
    Input:  matrix = [[1]]
    Output: 1


CONSTRAINTS
-----------
    m == matrix.length
    n == matrix[i].length
    1 <= m, n <= 200
    0 <= matrix[i][j] <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This looks like a graph-DFS problem (and it is), but it's ALSO 2D DP: the
key insight is that because every move must go to a STRICTLY LARGER value,
the "can I revisit a cell" cycle-detection problem that plagues generic DFS
memoization SIMPLY CANNOT HAPPEN here -- you can never walk back to a cell
you've already visited, because that would require the values to both
increase and decrease. This means a plain memo dict/table (no separate
"visited" set) is both correct AND sufficient.

dp[i][j] = length of the longest increasing path STARTING at (i, j) (going
outward to strictly larger neighbors). dp[i][j] = 1 + max over the (up to 4)
neighbors with a strictly larger value of dp[neighbor], or just 1 if no
neighbor qualifies (this cell is a "local peak," dead end).

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][j] = longest increasing path length starting AT (i, j).
Hint 2: A DFS from (i, j) only ever visits STRICTLY larger values -- this
        graph of "increasing moves" is a DAG (no cycles possible), so
        memoized DFS is safe with no extra visited-set bookkeeping.
Hint 3: dp[i][j] = 1 + max(dp[neighbor] for each of the 4 neighbors with
        matrix[neighbor] > matrix[i][j]), defaulting to 1 if none qualify.
Hint 4: The answer is max(dp[i][j] for all cells) -- you don't know in
        advance which cell starts the longest path, so compute dp for every
        cell (each one memoized once) and take the overall max.

COMPLEXITY TARGET
------------------
    Time:  O(m * n)   (each cell's dp value computed exactly once, memoized)
    Space: O(m * n)   (memo table + recursion stack up to m*n deep)
================================================================================
*/

// TODO: Implement the stub
