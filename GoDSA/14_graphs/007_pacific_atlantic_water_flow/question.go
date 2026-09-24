package main

/*
================================================================================
QUESTION · LeetCode 417 · Pacific Atlantic Water Flow               [Medium]
https://leetcode.com/problems/pacific-atlantic-water-flow/
================================================================================

PROBLEM
-------
There is an `m x n` rectangular island bordering both the Pacific Ocean and
the Atlantic Ocean. The Pacific touches the island's LEFT and TOP edges; the
Atlantic touches the RIGHT and BOTTOM edges.

`heights[r][c]` is the height of cell `(r, c)` above sea level. Rain water
can flow from a cell to any of its 4 orthogonal neighbors if the neighbor's
height is LESS THAN OR EQUAL to the current cell's height (water flows
downhill or along flat ground, never uphill).

Return a list of grid coordinates `[r, c]` where water can flow to BOTH the
Pacific and the Atlantic.


EXAMPLES
--------
Example 1:
    Input:
        heights =
            1 2 2 3 5
            3 2 3 4 4
            2 4 5 3 1
            6 7 1 4 5
            5 1 1 2 4

    Output: [[0,4],[1,3],[1,4],[2,2],[3,0],[3,1],[4,0]]

        Pacific touches the top row and left column. Atlantic touches the
        bottom row and right column:

              Pacific ~ ~ ~ ~ ~
                      1 2 2 3 5 ~
                      3 2 3 4 4 ~
                      2 4 5 3 1 ~     Atlantic
                      6 7 1 4 5 ~
                      5 1 1 2 4 ~
                      ~ ~ ~ ~ ~
                            Atlantic

        Cell (0,4)=5 can flow rightward off the top edge into the Pacific
        (already touching it) and downhill to the right edge into the
        Atlantic. Both oceans reachable -> included in the answer.

Example 2:
    Input:  heights = [[1]]
    Output: [[0,0]]
        The single cell touches all 4 borders simultaneously (it IS the
        entire island) -> reaches both oceans trivially.


CONSTRAINTS
-----------
    m == heights.length
    n == heights[r].length
    1 <= m, n <= 200
    0 <= heights[r][c] <= 10^5


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Flowing "downhill from a cell to the ocean" for every one of up to 40,000
cells and checking if BOTH oceans are reachable is the brute-force framing —
and it is O((rows*cols)^2) if done as a fresh flood fill from every cell.

The standard trick is to REVERSE the question: instead of asking "from this
cell, can water reach the ocean," ask "starting AT the ocean, which cells
could water have flowed FROM" — i.e. flood-fill INWARD from the border,
walking to a neighbor only if the neighbor's height is >= the current
height (this is the reverse of the forward flow rule, because you're
walking the path backward). Do this once seeded from every Pacific-border
cell, once seeded from every Atlantic-border cell, and intersect the two
reachable sets.

This problem is also this folder's canonical example of why grid mutation as
a visited-marker is dangerous (topic guide §6.1): the flood fill runs TWICE
on the SAME grid (heights), once for each ocean. Mutating `heights` in place
during the Pacific pass would corrupt the data the Atlantic pass reads —
you need a SEPARATE visited set per ocean. The solution file demonstrates
this breaking, live.


PROGRESSIVE HINTS
------------------
Hint 1: Don't flood-fill outward from every cell toward the ocean — flood
        fill INWARD from the ocean borders instead, twice (once per ocean).

Hint 2: The reversed flow condition is `neighbor_height >= current_height`
        (water could have flowed from the taller/equal neighbor down to
        here) — NOT the forward `<=` rule from the problem statement.

Hint 3: You need two separate `visited` sets, one for cells reachable from
        the Pacific border and one for the Atlantic border — then the
        answer is their INTERSECTION. Do not mutate `heights` itself to mark
        either, since the same grid is read for both flood fills.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — two flood fills, each visits every cell once
    Space: O(rows * cols) — two visited sets plus the BFS/DFS frontier
================================================================================
*/

// TODO: Implement the stub
