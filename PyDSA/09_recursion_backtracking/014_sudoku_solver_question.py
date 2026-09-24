"""
================================================================================
LeetCode 37 · Sudoku Solver                                               [Hard]
https://leetcode.com/problems/sudoku-solver/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Write a program to solve a Sudoku puzzle by filling the empty cells.

A sudoku solution must satisfy all of the following rules:
1. Each of the digits `1-9` must occur exactly once in each row.
2. Each of the digits `1-9` must occur exactly once in each column.
3. Each of the digits `1-9` must occur exactly once in each of the 9 3x3 sub-boxes of the grid.

The `.` character indicates empty cells.

EXAMPLES
--------
Example 1:
    Input: board = [
      ["5","3",".",".","7",".",".",".","."],
      ["6",".",".","1","9","5",".",".","."],
      [".","9","8",".",".",".",".","6","."],
      ["8",".",".",".","6",".",".",".","3"],
      ["4",".",".","8",".","3",".",".","1"],
      ["7",".",".",".","2",".",".",".","6"],
      [".","6",".",".",".",".","2","8","."],
      [".",".",".","4","1","9",".",".","5"],
      [".",".",".",".","8",".",".","7","9"]
    ]
    Output: The board modified in-place to contain the valid 9x9 solution.

CONSTRAINTS
-----------
    board.length == 9
    board[i].length == 9
    board[i][j] is a digit or '.'.
    It is guaranteed that the input board has only one solution.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Like N-Queens (013), this is a Constraint Satisfaction Problem[cite: 2]. We 
cannot just throw numbers onto the board and check if the final 9x9 grid is 
valid. We must prune dead-end branches early.

The "state" is the 9x9 grid itself. The "choices" at any empty cell are the 
digits "1" through "9". 

To solve this, we need to:
1. Find an empty cell.
2. Identify which numbers are "safe" to place there.
3. Place a number (CHOOSE), recursively try to solve the rest of the board 
   (EXPLORE), and if it fails, remove the number (UNCHOOSE)[cite: 2].

THE DECISION TREE
------------------
- Root: The initial board.
- Level 1: Find the first empty cell (e.g., r=0, c=2). Try placing '1', '2', '4'.
  (Assume '3' is blocked by the row).
- Level 2: Find the NEXT empty cell. Try valid digits.
- Leaf: There are no more empty cells. The board is solved.

WHAT TO THINK ABOUT
--------------------
1. Finding the next cell: You can just scan left-to-right, top-to-bottom. 
2. The 3x3 Box Math: A grid has 9 boxes. How do you map a coordinate (r, c) to 
   its specific box? 
   Formula: `box_index = (r // 3) * 3 + (c // 3)`.
3. Stop condition: When the recursive function finishes the last cell, it must 
   return `True` all the way up the call stack to prevent further backtracking 
   from erasing the correct answer.

PROGRESSIVE HINTS
------------------
Hint 1: Write a helper function `is_valid(r, c, digit)` that checks the row `r`, 
        column `c`, and the 3x3 sub-box for the presence of `digit`.
Hint 2: Write a recursive `backtrack()` function. Inside, use a nested loop to 
        find the first cell where `board[r][c] == '.'`.
Hint 3: Once an empty cell is found, loop `char` from '1' to '9'. If 
        `is_valid(r, c, char)`, place it and call `if backtrack(): return True`.
Hint 4: If none of the 1-9 choices work, reset the cell to `.` and return `False`.
Hint 5: If the nested loop finishes without finding any `.`, the board is solved 
        (return `True`).

COMPLEXITY TARGET
------------------
    Time:  O(9^m) where m is the number of empty cells, heavily pruned.
    Space: O(m) for the recursion stack depth.
================================================================================
"""

from typing import List


class Solution:
    def solveSudoku(self, board: List[List[str]]) -> None:
        """
        Do not return anything, modify board in-place instead.
        """
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 014_sudoku_solver_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    board = [
        ["5","3",".",".","7",".",".",".","."],
        ["6",".",".","1","9","5",".",".","."],
        [".","9","8",".",".",".",".","6","."],
        ["8",".",".",".","6",".",".",".","3"],
        ["4",".",".","8",".","3",".",".","1"],
        ["7",".",".",".","2",".",".",".","6"],
        [".","6",".",".",".",".","2","8","."],
        [".",".",".","4","1","9",".",".","5"],
        [".",".",".",".","8",".",".","7","9"]
    ]
    expected_row_0 = ["5","3","4","6","7","8","9","1","2"]
    
    # Pass a deep copy so we can verify output
    import copy
    board_copy = copy.deepcopy(board)
    sol.solveSudoku(board_copy)
    
    ok = board_copy[0] == expected_row_0
    print(f"{'PASS' if ok else 'FAIL'}  Sudoku Solver")
    if not ok:
        print(f"    Expected row 0: {expected_row_0}")
        print(f"    Got row 0:      {board_copy[0]}")


if __name__ == "__main__":
    run_tests()