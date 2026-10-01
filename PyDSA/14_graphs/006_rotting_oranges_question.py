"""
================================================================================
QUESTION · LeetCode 994 · Rotting Oranges                          [Medium]
https://leetcode.com/problems/rotting-oranges/
================================================================================

PROBLEM
-------
You are given an `m x n` grid where each cell can have one of three values:

    0   empty cell
    1   fresh orange
    2   rotten orange

Every minute, any fresh orange that is 4-directionally ADJACENT to a rotten
orange becomes rotten. Return the minimum number of minutes that must elapse
until no cell has a fresh orange. If this is impossible, return -1.


EXAMPLES
--------
Example 1:
    Input:
        2 1 1
        1 1 0
        0 1 1
    Output: 4

        minute 0:  2 1 1        minute 1:  2 2 1        minute 2:  2 2 2
                   1 1 0                   2 1 0                   2 2 0
                   0 1 1                   0 1 1                   0 2 1

        minute 3:  2 2 2        minute 4:  2 2 2
                   2 2 0                   2 2 0
                   0 2 2                   0 2 2   <- last fresh orange rots
                                                       at minute 4

Example 2:
    Input:
        2 1 1
        0 1 1
        1 0 1
    Output: -1
        The orange in the bottom-left corner (row 2, col 0) is never
        adjacent to a rotten orange — it stays fresh forever, impossible.

Example 3:
    Input:  [[0,2]]
    Output: 0
        No fresh oranges to begin with — 0 minutes needed.


CONSTRAINTS
-----------
    m == grid.length
    n == grid[i].length
    1 <= m, n <= 10
    grid[i][j] is 0, 1, or 2


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"How many minutes until a value has spread everywhere it can reach" is
multi-source BFS in disguise (topic guide §6.3): every rotten orange present
at minute 0 is a simultaneous BFS source. Seed the queue with ALL of them at
once, then run BFS wave by wave — each wave IS one minute, since every fresh
orange adjacent to the current wave's rotten set turns rotten together. The
answer is the number of waves it took, or -1 if any fresh orange is left
over once the queue drains (unreachable = never adjacent to any rotten path).


PROGRESSIVE HINTS
------------------
Hint 1: Multi-source BFS again (topic guide §6.3, same shape as 005 Walls
        and Gates) — scan the whole grid first, push every `2` onto the
        queue before the first pop, and count fresh oranges as you go so you
        know whether you're done.

Hint 2: Process the queue LEVEL BY LEVEL (drain the current queue size
        before incrementing your minute counter) rather than cell by cell —
        that level boundary is what turns "BFS depth" into "minutes elapsed."

Hint 3: Track a running count of fresh oranges. Decrement it every time one
        rots. If it hits 0, you're done; if the queue empties and it hasn't
        hit 0, some oranges were unreachable — return -1.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — every cell is enqueued and dequeued at most once
    Space: O(rows * cols) — the BFS queue in the worst case
================================================================================
"""

from collections import deque
from typing import List


class Solution:
    def orangesRotting(self, grid: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True

    cases = [
        ([[2, 1, 1], [1, 1, 0], [0, 1, 1]], 4),
        ([[2, 1, 1], [0, 1, 1], [1, 0, 1]], -1),
        ([[0, 2]], 0),
        ([[0]], 0),
        ([[1]], -1),
        ([[2]], 0),
        ([[0, 0, 0], [0, 0, 0]], 0),
        ([[2, 1, 1], [1, 1, 1], [1, 1, 1]], 4),
    ]

    for i, (grid, expected) in enumerate(cases):
        working = [row[:] for row in grid]
        got = sol.orangesRotting(working)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: grid={grid} -> {got} (want {expected})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
