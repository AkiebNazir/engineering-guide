package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 1091 · Shortest Path in Binary Matrix             [Medium]
https://leetcode.com/problems/shortest-path-in-binary-matrix/
================================================================================

PROBLEM
-------
Given an `n x n` binary matrix `grid`, return the length of the shortest
CLEAR path from top-left to bottom-right. If no clear path exists, return
-1.

A clear path is a path from (0, 0) to (n-1, n-1) such that:
    - All visited cells have value 0.
    - All adjacent cells in the path are 8-directionally connected (i.e.
      they are different and share an edge OR a corner — up, down, left,
      right, and all four diagonals).

The length of a clear path is the number of visited cells in it.


EXAMPLES
--------
Example 1:
    Input:  grid = [[0,1],
                     [1,0]]
    Output: 2

        0  1
        1  0

    (0,0) is directly diagonal-adjacent to (1,1) -> path = [(0,0),(1,1)],
    length 2. 4-directional movement alone could NOT do this — (0,0) has no
    orthogonal neighbor that is 0 except (1,1) is diagonal, not orthogonal.

Example 2:
    Input:  grid = [[0,0,0],
                     [1,1,0],
                     [1,1,0]]
    Output: 4

        0  0  0
        1  1  0
        1  1  0

    Path: (0,0) -> (0,1) -> (0,2) -> (1,2)/(2,2)... shortest is
    (0,0)->(0,1)->(1,2)[diagonal]->(2,2), length 4.

Example 3:
    Input:  grid = [[1,0,0],
                     [1,1,0],
                     [1,1,0]]
    Output: -1

    (0,0) itself is a 1 -> no clear path can even start. Return -1.


CONSTRAINTS
-----------
    n == grid.length == grid[i].length
    1 <= n <= 100
    grid[i][j] is 0 or 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Unweighted shortest path on a grid == BFS (topic guide Part 2). The one
twist versus every earlier grid problem in this folder: movement is
8-directional, not 4-directional — diagonals count as adjacent. That means
the `DIRECTIONS` list (topic guide §6.2) must include all 8 offsets, not
just the usual 4. Using only 4-directional movement on this problem can
turn a real path into a false "no path exists" — this file's runtime demo
constructs exactly such a grid.


PROGRESSIVE HINTS
------------------
Hint 1: This is grid BFS (topic guide Part 2/§6.2), same shape as Flood
        Fill / Number of Islands, but check the problem statement's
        adjacency rule carefully before copying the usual DIRECTIONS list.

Hint 2: Extend DIRECTIONS to 8 entries: the 4 orthogonal plus the 4
        diagonal offsets, (dr, dc) in {-1,0,1} x {-1,0,1} minus (0,0).

Hint 3: Edge cases first: if grid[0][0] or grid[n-1][n-1] is 1, no path can
        exist — return -1 immediately. Track path length as "number of
        cells visited", starting the source cell at length 1, not 0.


COMPLEXITY TARGET
------------------
    Time:  O(n^2) — every cell visited once, each with up to 8 neighbor checks
    Space: O(n^2) — queue + visited set
================================================================================
*/

func main() {
	fmt.Println("Solution for Shortest Path in Binary Matrix not implemented yet")
}
