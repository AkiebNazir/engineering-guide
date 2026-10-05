"""
================================================================================
QUESTION · LeetCode 542 · 01 Matrix                                  [Medium]
https://leetcode.com/problems/01-matrix/
================================================================================

PROBLEM
-------
Given an `m x n` binary matrix `mat`, return the distance of the nearest `0`
for each cell.

The distance between two adjacent cells is 1 (up/down/left/right only — no
diagonals).


EXAMPLES
--------
Example 1:
    Input:
        mat = [[0,0,0],
               [0,1,0],
               [0,0,0]]
    Output:
        [[0,0,0],
         [0,1,0],
         [0,0,0]]

    Every 1-cell has a 0-neighbor, so every distance is 1... except here the
    single 1 at (1,1) has four 0-neighbors, distance 1 — matches.

Example 2:
    Input:
        mat = [[0,0,0],
               [0,1,0],
               [1,1,1]]
    Output:
        [[0,0,0],
         [0,1,0],
         [1,2,1]]

    Grid (0 = zero cell, 1 = one cell, distances shown for the 1s):
        0  0  0
        0  1  0
        1  1  1

    (2,0)=1 -> nearest 0 is (1,0), distance 1
    (2,1)=1 -> nearest 0 is (1,1)? no that's a 1. Nearest 0 is (0,1) or
               (2,0)/(2,2)'s neighbors... actual nearest 0 path: (2,1) ->
               (1,1)[1, not 0] -> need to go around: (2,1)->(2,0)->(1,0)[0]
               = distance 2, matching output.
    (2,2)=1 -> nearest 0 is (1,2), distance 1


CONSTRAINTS
-----------
    m == mat.length
    n == mat[i].length
    1 <= m, n <= 10^4
    1 <= m * n <= 10^4
    mat[i][j] is either 0 or 1.
    There is at least one 0 in mat.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is "distance to nearest gate" (problem 005, Walls and Gates) with 0s
playing the role of gates. The topic guide's §6.3 multi-source BFS pattern
applies directly: seed a BFS queue with EVERY 0-cell at once (distance 0
each), then expand outward level by level. The first time BFS reaches a
1-cell, that IS its distance to the nearest 0 — because BFS explores in
strictly increasing distance order (topic guide Part 2).

Running single-source BFS from every 1-cell separately to find its nearest
0 would also be correct, but costs O(ones * cells) instead of O(cells) —
this problem's runtime demo measures exactly that gap.


PROGRESSIVE HINTS
------------------
Hint 1: Don't compute distance-to-nearest-0 one 1-cell at a time. Flip the
        direction: start BFS from ALL the 0-cells simultaneously.

Hint 2: Seed the queue with every (row, col) where mat[row][col] == 0,
        each with a starting distance of 0. Mark them all visited before the
        first pop.

Hint 3: Standard grid BFS from here (topic guide §6.2): pop a cell, look at
        its 4 orthogonal neighbors, if unvisited set distance = current + 1
        and enqueue. First arrival = shortest distance, guaranteed by BFS
        order.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — every cell enqueued and processed once
    Space: O(rows * cols) — queue + answer matrix
================================================================================
"""

from typing import List


class Solution:
    def updateMatrix(self, mat: List[List[int]]) -> List[List[int]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[0, 0, 0], [0, 1, 0], [0, 0, 0]],
         [[0, 0, 0], [0, 1, 0], [0, 0, 0]]),
        ([[0, 0, 0], [0, 1, 0], [1, 1, 1]],
         [[0, 0, 0], [0, 1, 0], [1, 2, 1]]),
        ([[0]], [[0]]),
        ([[1, 1, 1], [1, 1, 1], [1, 1, 0]],
         [[4, 3, 2], [3, 2, 1], [2, 1, 0]]),
        ([[0, 1], [1, 1]], [[0, 1], [1, 2]]),
    ]
    for mat, expected in cases:
        result = sol.updateMatrix([row[:] for row in mat])
        ok = result == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  mat={mat!r:<40} "
              f"-> {result} (want {expected})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
