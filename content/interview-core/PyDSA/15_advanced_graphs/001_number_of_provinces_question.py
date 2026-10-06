"""
================================================================================
QUESTION · LeetCode 547 · Number of Provinces                        [Medium]
https://leetcode.com/problems/number-of-provinces/
================================================================================

PROBLEM
-------
There are n cities. Some of them are connected, while some are not. If city
a is connected directly with city b, and b is connected directly with c,
then a is connected indirectly with c.

A province is a group of directly or indirectly connected cities and no
other cities outside of the group.

You are given an n x n matrix `isConnected` where `isConnected[i][j] = 1`
if the ith city and the jth city are directly connected, and
`isConnected[i][j] = 0` otherwise.

Return the total number of provinces.


EXAMPLES
--------
Example 1:
    Input:  isConnected = [[1,1,0],[1,1,0],[0,0,1]]
    Output: 2

Example 2:
    Input:  isConnected = [[1,0,0],[0,1,0],[0,0,1]]
    Output: 3


CONSTRAINTS
-----------
    1 <= n <= 200
    n == isConnected.length == isConnected[i].length
    isConnected[i][j] is 1 or 0
    isConnected[i][i] == 1
    isConnected[i][j] == isConnected[j][i]


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is "count connected components," dressed up as an adjacency MATRIX
(so no adjacency list needs to be built — row i IS city i's neighbor list).
A "province" is exactly a connected component. Two classic tools apply:

    1. DFS/BFS flood fill from every unvisited city, counting the number
       of times you have to start a fresh flood fill.
    2. Union-Find: union every pair (i, j) with isConnected[i][j] == 1,
       then count the number of distinct roots.

This folder is about Union-Find, so build it here — it is the simplest
possible use of the data structure and the natural on-ramp before 002 uses
it to check *unsatisfiable* constraints instead of just counting groups.

PROGRESSIVE HINTS
------------------
Hint 1: Initialize n separate sets, one per city.
Hint 2: Scan the upper triangle of the matrix (i < j) — the matrix is
        symmetric, so the lower triangle repeats the same information.
Hint 3: Union(i, j) whenever isConnected[i][j] == 1.
Hint 4: The answer is the number of cities that are still their own root
        after every union (or: the number of distinct `find(i)` values).

COMPLEXITY TARGET
------------------
    Time:  O(n^2 * alpha(n)) -- scanning the matrix dominates
    Space: O(n)
================================================================================
"""

from typing import List


class Solution:
    def findCircleNum(self, isConnected: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[1, 1, 0], [1, 1, 0], [0, 0, 1]], 2),
        ([[1, 0, 0], [0, 1, 0], [0, 0, 1]], 3),
        ([[1]], 1),
        ([[1, 1, 1], [1, 1, 1], [1, 1, 1]], 1),
        ([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 1], [0, 0, 1, 1]], 3),
    ]
    for matrix, want in cases:
        got = sol.findCircleNum([row[:] for row in matrix])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(matrix)}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
