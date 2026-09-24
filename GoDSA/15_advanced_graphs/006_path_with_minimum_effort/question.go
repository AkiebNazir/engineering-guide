package main

/*
================================================================================
QUESTION · LeetCode 1631 · Path With Minimum Effort                   [Medium]
https://leetcode.com/problems/path-with-minimum-effort/
================================================================================

PROBLEM
-------
You are a hiker preparing for an upcoming hike. You are given `heights`, a
2D array of size rows x columns, where heights[row][col] represents the
height of cell (row, col). You are situated in the top-left cell,
(0, 0), and you hope to travel to the bottom-right cell, (rows-1, columns-1)
(i.e., 0-indexed). You can move up, down, left, or right, and you wish to
find a route that requires the minimum effort.

A route's effort is the MAXIMUM absolute difference in heights between two
consecutive cells of the route.

Return the minimum effort required to travel from the top-left cell to the
bottom-right cell.


EXAMPLES
--------
Example 1:
    Input:  heights = [[1,2,2],[3,8,2],[5,3,5]]
    Output: 2
    Explanation: Route [1,3,5,3,5] has a maximum absolute difference of 2
    in consecutive cells. This route is better than [1,2,2,2,5], where the
    maximum absolute difference is 3.

Example 2:
    Input:  heights = [[1,2,3],[3,8,4],[5,3,5]]
    Output: 1

Example 3:
    Input:  heights = [[1,2,1,1,1],[1,2,1,2,1],[1,2,1,2,1],[1,2,1,2,1],
                       [1,1,1,2,1]]
    Output: 0


CONSTRAINTS
-----------
    rows == heights.length
    columns == heights[i].length
    1 <= rows, columns <= 100
    1 <= heights[i][j] <= 10^6


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A grid IS a graph (topic 14): each cell is a node, its up-to-4 orthogonal
neighbors are edges, edge weight = |height difference|. The twist is the
COST FUNCTION: minimize the path's MAXIMUM edge weight ("effort"), not the
SUM of edge weights. This is the "minimax path" variant covered in the
topic guide Part 3 -- Dijkstra's exact skeleton, with `max(d, w)` in place
of `d + w` as the relax rule. The greedy argument still holds: whichever
frontier cell has the smallest running max-so-far is safe to finalize,
because no route through a currently-farther cell can produce a smaller
max.

PROGRESSIVE HINTS
------------------
Hint 1: Model the grid as a graph; (0,0) is the source, (rows-1,cols-1) is
        the target.
Hint 2: Use Dijkstra's heap skeleton, but the "distance" being tracked is
        the max edge weight seen so far on the best route to each cell.
Hint 3: Relax rule: effort[neighbor] = min(effort[neighbor],
        max(effort[cell], |height[cell]-height[neighbor]|)).
Hint 4: Don't forget the stale-entry guard from Dijkstra's skeleton --
        it applies unchanged here.

COMPLEXITY TARGET
------------------
    Time:  O(R*C * log(R*C))
    Space: O(R*C)
================================================================================
*/

// TODO: Implement the stub
