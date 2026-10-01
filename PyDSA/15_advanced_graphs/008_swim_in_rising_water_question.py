"""
================================================================================
QUESTION · LeetCode 778 · Swim in Rising Water                          [Hard]
https://leetcode.com/problems/swim-in-rising-water/
================================================================================

PROBLEM
-------
You are given an n x n integer matrix grid where each value grid[i][j]
represents the elevation at that point (i, j).

The rain starts to fall. At time t, the depth of the water everywhere is
t. You can swim from a square to another 4-directionally adjacent square
if and only if the elevation of both squares individually are at most t.
You can swim infinite distances in zero time. Of course, you must stay
within the boundaries of the grid during your swim.

Return the least time until you can reach the bottom right square
(n - 1, n - 1) if you start at the top left square (0, 0).


EXAMPLES
--------
Example 1:
    Input:  grid = [[0,2],[1,3]]
    Output: 3

Example 2:
    Input:  grid = [[0,1,2,3,4],[24,23,22,21,5],[12,13,14,15,16],
                    [11,17,18,19,20],[10,9,8,7,6]]
    Output: 16


CONSTRAINTS
-----------
    n == grid.length == grid[i].length
    1 <= n <= 50
    0 <= grid[i][j] < n^2
    Each value grid[i][j] is unique.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The answer is the smallest T such that a path from (0,0) to (n-1,n-1)
exists using ONLY cells with elevation <= T -- equivalently, the smallest T
such that a path exists whose MAXIMUM cell elevation is <= T. That "minimize
the max along a path" shape is the same minimax structure as problem 006
(Path With Minimum Effort), just with the cost attached to NODES (cell
elevation) instead of EDGES (height difference) -- fold each cell's
elevation into the cost the moment you step onto it and the algorithm is
identical.

PROGRESSIVE HINTS
------------------
Hint 1: Same minimax-Dijkstra skeleton as 006: track the max elevation
        seen so far on the best route to each cell.
Hint 2: Relax rule: cost[neighbor] = min(cost[neighbor],
        max(cost[cell], grid[neighbor])) -- the neighbor's OWN elevation
        matters, not a difference between cells.
Hint 3: A second valid angle: sort all cells by elevation, union
        4-adjacent already-placed cells with Union-Find as each cell
        "appears" (becomes <= current water level t); the answer is the t
        at which (0,0) and (n-1,n-1) first land in the same set.
Hint 4: A third valid angle: binary search on T, feasibility = BFS/DFS
        using only cells with elevation <= T.

COMPLEXITY TARGET
------------------
    Time:  O(n^2 log(n^2))
    Space: O(n^2)
================================================================================
"""

from typing import List


class Solution:
    def swimInWater(self, grid: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[0, 2], [1, 3]], 3),
        ([[0, 1, 2, 3, 4], [24, 23, 22, 21, 5], [12, 13, 14, 15, 16],
          [11, 17, 18, 19, 20], [10, 9, 8, 7, 6]], 16),
        ([[0]], 0),
        ([[3, 2], [0, 1]], 3),
    ]
    for grid, want in cases:
        got = sol.swimInWater([row[:] for row in grid])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(grid)}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
