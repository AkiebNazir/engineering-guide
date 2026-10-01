package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 695 · Max Area of Island                         [Medium]
https://leetcode.com/problems/max-area-of-island/
================================================================================

PROBLEM
-------
You are given an `m x n` binary matrix `grid`. An island is a group of `1`s
(representing land) connected 4-directionally (horizontal or vertical). You
may assume all four edges of the grid are surrounded by water.

The AREA of an island is the number of cells with value `1` in the island.

Return the maximum area of an island in `grid`. If there is no island,
return `0`.


EXAMPLES
--------
Example 1:
    Input:
        grid = [[0,0,1,0,0,0,0,1,0,0,0,0,0],
                [0,0,0,0,0,0,0,1,1,1,0,0,0],
                [0,1,1,0,1,0,0,0,0,0,0,0,0],
                [0,1,0,0,1,1,0,0,1,0,1,0,0],
                [0,1,0,0,1,1,0,0,1,1,1,0,0],
                [0,0,0,0,0,0,0,0,0,0,1,0,0],
                [0,0,0,0,0,0,0,1,1,1,0,0,0],
                [0,0,0,0,0,0,0,1,1,0,0,0,0]]
    Output: 6

        The island of area 6 is the block around rows 2-4, columns 1-2
        plus row 3-4 column 4-5's separate blob... (the classic LC diagram —
        see below for a compact ASCII version this file actually tests):

Example 2 (compact, exactly what run_tests() below uses):
    Input:
        grid = [[1,1,0,0,0],
                [1,1,0,0,0],
                [0,0,0,1,1],
                [0,0,0,1,1],
                [0,0,0,0,1]]
    Output: 5

        1 1 . . .      island A: (0,0)(0,1)(1,0)(1,1) -> area 4
        1 1 . . .
        . . . 1 1      island B: (2,3)(2,4)(3,3)(3,4)(4,4) -> area 5  <- max
        . . . 1 1
        . . . . 1

Example 3:
    Input:  grid = [[0,0,0,0,0,0,0,0]]
    Output: 0                              (no land at all)


CONSTRAINTS
-----------
    m == grid.length
    n == grid[i].length
    1 <= m, n <= 50
    grid[i][j] is either 0 or 1     (NOTE: these are INTEGERS, not strings —
                                     contrast 002 where the grid holds chars)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Exactly 002's connected-components scan, generalized: instead of counting
HOW MANY components exist, each flood must also report HOW BIG it is (the
number of cells it touched), and you keep a running max instead of a
running count. The flood routine from 001/002 needs one change — return an
integer (cells visited) instead of returning nothing.


PROGRESSIVE HINTS
------------------
Hint 1: Same outer scan as 002: for every unvisited land cell, start a new
        flood. The difference is entirely inside the flood: have it COUNT
        the cells it visits and return that count.

Hint 2: `area(r, c)` for an out-of-bounds or water/visited cell should
        contribute 0 and stop the recursion/expansion there. For a valid
        land cell it contributes 1 (itself) plus the sum of what each of
        its 4 neighbors' floods contribute.

Hint 3: Track `best = max(best, area(r, c))` at the outer scan level, once
        per newly-discovered island.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — every cell visited at most once
    Space: O(rows * cols) worst case — recursion/stack/queue depth for a
           grid that is entirely land
================================================================================
*/

func main() {
	fmt.Println("Solution for Max Area of Island not implemented yet")
}
