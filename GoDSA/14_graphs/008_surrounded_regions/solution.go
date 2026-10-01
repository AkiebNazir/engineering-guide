package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 130 · Surrounded Regions                        [Medium]
https://leetcode.com/problems/surrounded-regions/
================================================================================

PROBLEM
-------
You are given an `m x n` matrix `board` containing letters `'X'` and `'O'`.

Capture all regions that are 4-directionally SURROUNDED by `'X'`: flip every
`'O'` in such a region to `'X'`. A region is NOT surrounded (and stays `'O'`)
if it touches the border of the board, directly or by being connected
through a chain of other `'O'`s to a border cell.

Modify `board` IN PLACE. Return nothing.


EXAMPLES
--------
Example 1:
    Input:
        X X X X
        X O O X
        X X O X
        X O X X

    Output:
        X X X X
        X X X X
        X X X X
        X O X X

        The 'O's at (1,1),(1,2),(2,2) form one connected region that never
        touches the border -> captured (flipped to X).
        The 'O' at (3,1) is isolated and also doesn't touch the border ->
        wait, actually check connectivity: (3,1) is NOT adjacent to any
        other O and is not on the border itself (row 3 is the LAST row,
        which IS a border row) -> (3,1) is ON the border (bottom row) ->
        stays 'O'.

Example 2:
    Input:  [["X"]]
    Output: [["X"]]

Example 3 (region touching the border stays O):
    Input:
        O O O
        O X O
        O O O
    Output:
        O O O
        O X O
        O O O
        Every 'O' is on the border or connected to one -> nothing captured.


CONSTRAINTS
-----------
    m == board.length
    n == board[i].length
    1 <= m, n <= 200
    board[i][j] is 'X' or 'O'


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The trap: flood-filling from an arbitrary interior 'O' and flipping
everything you find EAGERLY (before knowing whether that region touches the
border) is wrong — you'd have to undo the flip if it later turns out to
reach the border, and "later" can be arbitrarily deep into the flood fill.

The clean fix REVERSES the direction of the search, the same idea as 007
(Pacific Atlantic): flood fill from every BORDER cell that is 'O', marking
everything reachable from a border as SAFE (never touches an 'X' wall
because it IS connected to the edge, by definition, not captured). Once
every border-connected 'O' is marked safe, one final pass flips every
UNMARKED 'O' to 'X' (captured) and restores every marked-safe cell back to
'O'. No guessing, no undoing.


PROGRESSIVE HINTS
------------------
Hint 1: Don't flood-fill from the interior and try to decide "is this region
        surrounded" mid-fill. Flood fill from the OUTSIDE IN instead —
        start from every 'O' that is already ON the border.

Hint 2: Use a temporary marker (e.g. `'#'`   ) to mark every cell reached
        from a border 'O' as SAFE. Border-reachable 'O's must never be
        flipped to 'X'.

Hint 3: One final full-grid pass: any remaining `'O'` (never marked safe) ->
        flip to `'X'` (it's captured). Any `'#'` (marked safe) -> flip back
        to `'O'` (restore it).


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — one flood fill from all border O's, plus one
                             final linear pass
    Space: O(rows * cols) — worst case, if the entire board is 'O'
================================================================================
*/

func main() {
	fmt.Println("Solution for Surrounded Regions not implemented yet")
}
