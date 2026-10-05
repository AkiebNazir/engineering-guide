"""
================================================================================
LeetCode 1368 · Minimum Cost to Make at Least One Valid Path in a Grid    [Hard]
https://leetcode.com/problems/minimum-cost-to-make-at-least-one-valid-path-in-a-grid/
Topic: 15 · Advanced Graphs
================================================================================

PROBLEM
-------
Given an m x n grid. Each cell has a sign pointing to the next cell you
should visit if you are currently in that cell:

    1 -> go right   (i, j + 1)
    2 -> go left    (i, j - 1)
    3 -> go down    (i + 1, j)
    4 -> go up      (i - 1, j)

Some signs may point outside the grid.

You start at the upper-left cell (0, 0). A valid path starts at (0, 0) and
ends at the bottom-right cell (m - 1, n - 1), following the signs. You can
modify the sign on a cell at a cost of 1, once per cell.

Return the minimum cost to make the grid have at least one valid path.


EXAMPLES
--------
Example 1:
    Input:  grid = [[1,1,1,1],[2,2,2,2],[1,1,1,1],[2,2,2,2]]
    Output: 3

        → → → →        follow row 0 right, change (0,3) to ↓   cost 1
        ← ← ← ←        row 1 goes left; change (1,0) to ↓      cost 2
        → → → →        follow row 2 right, change (2,3) to ↓   cost 3
        ← ← ← ←        land on (3,3)

Example 2:
    Input:  grid = [[1,1,3],[3,2,2],[1,1,4]]
    Output: 0          (the signs already lead there)

Example 3:
    Input:  grid = [[1,2],[4,3]]
    Output: 1


CONSTRAINTS
-----------
    m == grid.length, n == grid[i].length
    1 <= m, n <= 100
    1 <= grid[i][j] <= 4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Every cell has four possible moves:

    the move its sign points to   costs 0
    any of the other three moves  costs 1 (you change the sign)

So this is a shortest path on a grid graph whose edges weigh 0 or 1.

Plain BFS assumes every edge weighs 1: wrong here.
Dijkstra works: O(mn log(mn)).
0-1 BFS is Dijkstra specialized for 0/1 weights with a DEQUE: push 0-cost
neighbors to the FRONT, 1-cost neighbors to the BACK. The deque stays sorted
by distance, so it runs in O(mn).


WHAT TO THINK ABOUT
--------------------
1. Why does pushing a 0-weight neighbor to the FRONT keep the deque sorted?

2. When is a cell's distance final: when you push it or when you pop it?

3. Changing a cell's sign "once": does that restriction ever matter for a
   shortest path? (Would an optimal path visit a cell twice?)


PROGRESSIVE HINTS
------------------
Hint 1: dist = [[inf] * n for _ in range(m)]; dist[0][0] = 0; deque([(0, 0)]).

Hint 2: Pop left. For each direction d (1..4): cost = 0 if d == grid[i][j]
        else 1. If dist[i][j] + cost < dist[ni][nj], update and push left
        (cost 0) or right (cost 1).

Hint 3: Return dist[m-1][n-1].


COMPLEXITY TARGET
------------------
    Time:  O(m * n)
    Space: O(m * n)
================================================================================
"""

from typing import List


class Solution:
    def minCost(self, grid: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 015_minimum_cost_to_make_at_least_one_valid_path_in_a_grid_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([[1, 1, 1, 1], [2, 2, 2, 2], [1, 1, 1, 1], [2, 2, 2, 2]], 3),
        ([[1, 1, 3], [3, 2, 2], [1, 1, 4]], 0),
        ([[1, 2], [4, 3]], 1),
        ([[4]], 0),
        ([[2, 2, 2], [2, 2, 2]], 3),
        ([[3, 4, 3], [2, 2, 2], [2, 1, 1], [4, 3, 2], [2, 1, 4], [2, 4, 1], [3, 3, 3], [1, 4, 2], [2, 2, 1], [2, 1, 1], [3, 3, 1], [4, 1, 4], [2, 1, 4], [3, 2, 2], [3, 3, 1], [4, 4, 1], [1, 2, 2], [1, 1, 1], [1, 3, 4], [1, 2, 1], [2, 2, 4], [2, 1, 3], [1, 2, 1], [4, 3, 2], [3, 3, 4], [2, 2, 1], [3, 4, 3], [4, 2, 3], [4, 4, 4]], 18),
    ]
    all_ok = True
    for grid, want in cases:
        got = Solution().minCost([row[:] for row in grid])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {len(grid)}x{len(grid[0])} grid  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
