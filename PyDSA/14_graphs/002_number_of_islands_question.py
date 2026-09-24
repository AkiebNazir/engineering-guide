"""
================================================================================
QUESTION · LeetCode 200 · Number of Islands                          [Medium]
https://leetcode.com/problems/number-of-islands/
================================================================================

PROBLEM
-------
Given an `m x n` 2D binary grid `grid` which represents a map of `'1'`s
(land) and `'0'`s (water), return the number of islands.

An island is surrounded by water and is formed by connecting adjacent lands
horizontally or vertically. You may assume all four edges of the grid are
all surrounded by water.


EXAMPLES
--------
Example 1:
    Input:
        grid = [
          ["1","1","1","1","0"],
          ["1","1","0","1","0"],
          ["1","1","0","0","0"],
          ["0","0","0","0","0"]
        ]
    Output: 1

        1 1 1 1 0
        1 1 0 1 0      one connected blob of '1's touching the grid's
        1 1 0 0 0      right column at row 0-1 through the middle spur
        0 0 0 0 0      -> a single island

Example 2:
    Input:
        grid = [
          ["1","1","0","0","0"],
          ["1","1","0","0","0"],
          ["0","0","1","0","0"],
          ["0","0","0","1","1"]
        ]
    Output: 3

        1 1 0 0 0      island A: (0,0)(0,1)(1,0)(1,1)
        1 1 0 0 0      island B: (2,2) alone
        0 0 1 0 0      island C: (3,3)(3,4)
        0 0 0 1 1


CONSTRAINTS
-----------
    m == grid.length
    n == grid[i].length
    1 <= m, n <= 300
    grid[i][j] is '0' or '1'    (NOTE: these are STRING characters, not ints)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is "count connected components" (topic guide Part 3) on the implicit
grid graph from Part 6: land cells are nodes, edges connect orthogonally
adjacent land cells. Scan every cell; whenever you find an UNVISITED land
cell, that's the first sighting of a brand-new island — increment the
count and flood-fill (001) outward from it to mark the whole island visited
so you never count it again.


PROGRESSIVE HINTS
------------------
Hint 1: Reuse 001's flood fill as the inner routine, but here you don't get
        told the start cell — you find it by scanning row by row, column by
        column, and triggering a flood the first time you see an unvisited
        `'1'`.

Hint 2: You need SOME way to mark a land cell as "already counted" so the
        outer scan doesn't fire a second flood on it. Two options (topic
        guide §6.1): flip visited `'1'`s to `'0'` in place (destroys the
        input), or keep a separate `visited` set of (r, c) pairs.

Hint 3: The answer is just: for each unvisited `'1'` the outer double loop
        finds, `islands += 1`, then flood-mark its entire component so it's
        never re-triggered. That's the whole algorithm.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — every cell visited a constant number of times
    Space: O(rows * cols) worst case — visited set or recursion/queue depth
           for a grid that is entirely land
================================================================================
"""

from collections import deque
from typing import List


class Solution:
    def numIslands(self, grid: List[List[str]]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 002_number_of_islands_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([["1", "1", "1", "1", "0"],
          ["1", "1", "0", "1", "0"],
          ["1", "1", "0", "0", "0"],
          ["0", "0", "0", "0", "0"]], 1),
        ([["1", "1", "0", "0", "0"],
          ["1", "1", "0", "0", "0"],
          ["0", "0", "1", "0", "0"],
          ["0", "0", "0", "1", "1"]], 3),
        ([["0"]], 0),
        ([["1"]], 1),
        ([["1", "0", "1", "0", "1"]], 3),
    ]
    for grid, want in cases:
        g = [row[:] for row in grid]
        got = sol.numIslands(g)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  grid={grid!r} -> {got} (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
