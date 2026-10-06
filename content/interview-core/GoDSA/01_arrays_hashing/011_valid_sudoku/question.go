package main

/*
================================================================================
LeetCode 36 · Valid Sudoku                                             [Medium]
https://leetcode.com/problems/valid-sudoku/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Determine if a 9 x 9 Sudoku board is valid. Only the filled cells need to be
validated according to the following rules:

    1. Each ROW must contain the digits 1-9 without repetition.
    2. Each COLUMN must contain the digits 1-9 without repetition.
    3. Each of the nine 3 x 3 SUB-BOXES must contain the digits 1-9 without
       repetition.

Note:
    - A Sudoku board (partially filled) could be valid but is not necessarily
      solvable.
    - Only the filled cells need to be validated according to the rules.


EXAMPLES
--------
Example 1:
    Input: board =
    [["5","3",".",".","7",".",".",".","."]
    ,["6",".",".","1","9","5",".",".","."]
    ,[".","9","8",".",".",".",".","6","."]
    ,["8",".",".",".","6",".",".",".","3"]
    ,["4",".",".","8",".","3",".",".","1"]
    ,["7",".",".",".","2",".",".",".","6"]
    ,[".","6",".",".",".",".","2","8","."]
    ,[".",".",".","4","1","9",".",".","5"]
    ,[".",".",".",".","8",".",".","7","9"]]
    Output: true

Example 2:
    Same as Example 1 except with the 5 in the top left corner being modified
    to 8.
    Output: false
    Explanation: There are two 8's in the top left 3x3 sub-box.


CONSTRAINTS
-----------
    board.length == 9
    board[i].length == 9
    board[i][j] is a digit 1-9 or '.'


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Read the task precisely, because two words do a lot of work:

    "VALID"        — no rule is currently broken. NOT "solvable".
    "only FILLED   — '.' is not a value. Nine dots in a row is perfectly
     cells"          valid; nine 5s is not.

A board can be valid and still be impossible to finish. You are not solving
anything, not backtracking, not checking satisfiability. You are checking a
single property: does any digit appear twice within a row, a column, or a box?

    THE PROBLEM IS "FIND A DUPLICATE", RUN THREE TIMES OVER THREE GROUPINGS.

That reduction matters. You already know how to detect duplicates in a
collection — a set (LC 217, Contains Duplicate). The only new thing here is
mapping each cell to the three groups it belongs to.

    ┌───────┬───────┬───────┐
    │ 5 3 . │ . 7 . │ . . . │   cell (0,0) belongs to:
    │ 6 . . │ 1 9 5 │ . . . │       row 0
    │ . 9 8 │ . . . │ . 6 . │       col 0
    ├───────┼───────┼───────┤       box 0   ← the new part
    │ 8 . . │ . 6 . │ . . 3 │
    │ 4 . . │ 8 . 3 │ . . 1 │   cell (4,4) belongs to:
    │ 7 . . │ . 2 . │ . . 6 │       row 4, col 4, box 4
    ├───────┼───────┼───────┤
    │ . 6 . │ . . . │ 2 8 . │   boxes are numbered
    │ . . . │ 4 1 9 │ . . 5 │       0 1 2
    │ . . . │ . 8 . │ . 7 9 │       3 4 5
    └───────┴───────┴───────┘       6 7 8


WHAT TO THINK ABOUT
-------------------
1. The naive plan is three separate scans: check all rows, then all columns,
   then all boxes. That works. Can you instead do ONE pass over the 81 cells,
   updating all three group-trackers as you go?

2. For one pass you need, given (r, c), the index of its 3x3 box. Rows 0-2 are
   box-row 0, rows 3-5 are box-row 1, rows 6-8 are box-row 2. What integer
   operation collapses 0,1,2 -> 0 and 3,4,5 -> 1? How do you combine box-row
   and box-col into a single index 0-8? (A tuple key works too.)

3. What is the complexity? Careful: the board is FIXED at 9x9. Think about
   what n even means here before you say O(n²).

4. Do you need to store the digits at all, or just detect a collision? Would a
   9-bit integer per group work instead of a set?


PROGRESSIVE HINTS
-----------------
Hint 1: Keep three collections of nine sets: `rows[9]`, `cols[9]`, `boxes[9]`.
        Walk every cell once. Skip '.'.

Hint 2: The box index is `(r // 3) * 3 + (c // 3)`. Integer division collapses
        three consecutive indices into one; multiplying the box-row by 3
        flattens the 3x3 grid of boxes into 0-8.

Hint 3: For each filled cell, if the digit is already in rows[r] OR cols[c] OR
        boxes[b], return False immediately. Otherwise add it to all three and
        continue. If you finish the loop, return True.


COMPLEXITY TARGET
-----------------
    The board is fixed at 9x9 = 81 cells, so this is O(1) by the constraints.
    Generalised to an n x n board: O(n²) time, O(n²) space.
================================================================================
*/

// TODO: Implement the stub
