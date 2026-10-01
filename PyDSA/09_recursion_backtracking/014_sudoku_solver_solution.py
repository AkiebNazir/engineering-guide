"""
================================================================================
SOLUTION · LeetCode 37 · Sudoku Solver                                    [Hard]
https://leetcode.com/problems/sudoku-solver/
================================================================================

THE CORE IDEA
--------------
Sudoku is a constraint satisfaction problem[cite: 2]. We systematically scan for 
empty cells and attempt to place digits '1' through '9'. We heavily prune the 
decision tree by ensuring we NEVER recurse into an invalid board state[cite: 2].

The critical mechanical difference between Sudoku and previous backtracking 
problems is the short-circuit return. Once a solution is found deep in the tree, 
we must immediately cascade `True` back up the call stack. If we don't, the 
algorithm will "unchoose" the correct answer to look for other solutions, 
ultimately returning an empty board.


================================================================================
MULTIPLE APPROACHES & TRADE-OFFS
================================================================================
1. NAIVE VALIDATION (Check on the fly) 
   At every empty cell, iterate over its entire row (9 cells), column (9 cells), 
   and 3x3 box (9 cells) to see if a digit is safe.
   - Trade-off: Zero extra memory and zero setup time. However, every validation 
     takes O(N) operations (where N=9). 

2. SET / BITMASK PRUNING (O(1) Validation) — The Optimal Strategy
   Maintain three arrays of sets (or bitmasks): `rows`, `cols`, and `boxes`. 
   During an initial O(N^2) pass, populate these sets with the existing numbers. 
   Now, validating a digit takes O(1) time.
   - Trade-off: Requires O(N^2) extra space and a preliminary pass over the grid. 
     However, it executes significantly fewer CPU instructions during the massive 
     recursion phase.


================================================================================
STEP BY STEP TRACE (Dry Run) — Initial Cell (0, 2)
================================================================================
Let's trace the O(1) Set Pruning approach for the first empty cell at (0, 2).
Board state: 
row 0 has '5', '3', '7'
col 2 has '8'
box 0 has '5', '3', '6'

Sets tracking:
rows[0] = {'5', '3', '7'}
cols[2] = {'8'}
boxes[0] = {'5', '3', '6'}

    backtrack()
      Finds first empty cell: r=0, c=2. Box index = (0//3)*3 + (2//3) = 0.
      
      Try digit '1':
        Is '1' in rows[0]? No. cols[2]? No. boxes[0]? No. -> SAFE.
        CHOOSE: board[0][2] = '1'. Add '1' to rows[0], cols[2], boxes[0].
        EXPLORE: call backtrack().
          (Assume eventually this leads to a dead end...)
          backtrack() returns False.
        UNCHOOSE: board[0][2] = '.'. Remove '1' from sets.
        
      Try digit '2':
        Is '2' in sets? No. -> SAFE.
        CHOOSE: board[0][2] = '2'. Add '2' to sets.
        EXPLORE: call backtrack()...
        
      Try digit '3':
        Is '3' in sets? YES (rows[0] and boxes[0]). -> PRUNE immediately[cite: 2].


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach               Time                 Space          Mutates input?
    ---------------------  -------------------  -------------  ---------------
    Naive Validation       O(9^m) worst-case    O(m) stack     Yes
    Set/Array Pruning      O(9^m) worst-case    O(m) stack     Yes

    WHERE O(9^m) comes from: 
    Let m be the number of empty cells (at most 81). For each empty cell, there 
    are up to 9 choices. The raw unpruned tree size is $9^{81}$. Because we enforce 
    constraints BEFORE recursing, the explored tree collapses to a tiny fraction 
    of this size[cite: 2]. Since the grid size is strictly fixed at 9x9, the 
    asymptotic complexity is technically O(1), but O(9^m) effectively communicates 
    how the algorithm scales relative to the number of missing blanks.


================================================================================
COMMON MISTAKES
================================================================================
1. The 3x3 Box Formula: Miscalculating the sub-box index is the #1 bug. 
   The correct formula maps a 9x9 grid to a 3x3 layout of boxes:
   `box_index = (r // 3) * 3 + (c // 3)`
2. Forgetting the Cascade Return: If `backtrack()` returns `True`, the parent 
   caller must also immediately `return True`. If you just call `backtrack()` 
   without capturing the success state, the algorithm will erase the winning 
   board during its unchoose step.
3. Returning False Too Early: Only return `False` AFTER trying all 9 digits and 
   exhausting all valid choices for a specific cell.


================================================================================
SIMILAR PROBLEMS
================================================================================
    LC 51   N-Queens                        — The sister problem. Exact same 
                                              "prune constraints via sets" logic.
    LC 36   Valid Sudoku                    — Validating a board without solving 
                                              it (the exact logic used in the 
                                              Setup phase of Solution 2).
    Graph Coloring (Standard CS)            — Assigning colors (digits) to nodes 
                                              (cells) such that no adjacent nodes 
                                              (row/col/box) share a color.
================================================================================
"""

import time
from typing import List


class Solution:
    def solveSudoku(self, board: List[List[str]]) -> None:
        """
        Optimal Approach: O(1) Set Pruning.
        Pre-computes constraints into sets, drastically speeding up validation.
        """
        # 1. Setup Phase: Track existing numbers
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]

        # Populate the sets with the initial board state
        for r in range(9):
            for c in range(9):
                if board[r][c] != '.':
                    val = board[r][c]
                    box_idx = (r // 3) * 3 + (c // 3)
                    rows[r].add(val)
                    cols[c].add(val)
                    boxes[box_idx].add(val)

        # 2. Backtracking Phase
        def backtrack(r=0, c=0) -> bool:
            # Advance to the next row if we reach the end of a column
            if c == 9:
                c = 0
                r += 1
            
            # Base Case: We've successfully passed the last row
            if r == 9:
                return True

            # If cell is already filled, skip to the next cell
            if board[r][c] != '.':
                return backtrack(r, c + 1)

            box_idx = (r // 3) * 3 + (c // 3)

            # Try placing digits 1-9
            for digit in map(str, range(1, 10)):
                # VALIDATE (O(1) time)
                if digit not in rows[r] and digit not in cols[c] and digit not in boxes[box_idx]:
                    
                    # 1. CHOOSE
                    board[r][c] = digit
                    rows[r].add(digit)
                    cols[c].add(digit)
                    boxes[box_idx].add(digit)

                    # 2. EXPLORE (Cascade return on success)
                    if backtrack(r, c + 1):
                        return True

                    # 3. UNCHOOSE
                    board[r][c] = '.'
                    rows[r].remove(digit)
                    cols[c].remove(digit)
                    boxes[box_idx].remove(digit)

            # Exhausted all 1-9 without success -> trigger backtracking
            return False

        backtrack()

    # ------------------------------------------------------------------
    # Alternative Approach
    # ------------------------------------------------------------------
    def solveSudoku_naive(self, board: List[List[str]]) -> None:
        """
        Naive Approach: Validates dynamically on the fly.
        Requires zero extra space, but checks take O(N) operations.
        """
        def is_valid(r, c, digit):
            # Check row and column
            for i in range(9):
                if board[r][i] == digit: return False
                if board[i][c] == digit: return False
                
            # Check 3x3 box
            start_row, start_col = 3 * (r // 3), 3 * (c // 3)
            for i in range(3):
                for j in range(3):
                    if board[start_row + i][start_col + j] == digit:
                        return False
            return True

        def backtrack():
            for r in range(9):
                for c in range(9):
                    if board[r][c] == '.':
                        for digit in map(str, range(1, 10)):
                            if is_valid(r, c, digit):
                                # CHOOSE
                                board[r][c] = digit
                                
                                # EXPLORE
                                if backtrack():
                                    return True
                                
                                # UNCHOOSE
                                board[r][c] = '.'
                                
                        return False # Tried 1-9, none worked
            
            return True # No empty cells left

        backtrack()


# ==============================================================================
# TESTS — run:  python 014_sudoku_solver_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    
    # Standard hard Sudoku board
    base_board = [
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
    expected_row_8 = ["3","4","5","2","8","6","1","7","9"]

    impls = [
        ("O(1) Set Pruning  ", sol.solveSudoku),
        ("Naive Validation  ", sol.solveSudoku_naive),
    ]

    all_ok = True
    import copy
    
    print("--- Correctness Tests ---")
    for name, fn in impls:
        test_board = copy.deepcopy(base_board)
        t0 = time.perf_counter()
        fn(test_board)
        t1 = time.perf_counter()
        
        ok = (test_board[0] == expected_row_0) and (test_board[8] == expected_row_8)
        all_ok &= ok
        
        ms = (t1 - t0) * 1000
        print(f"{'PASS' if ok else 'FAIL'}  {name} | Executed in {ms:.2f} ms")

    print("\nNote: Because N is strictly 9, both approaches execute extremely fast.")
    print("However, the Set Pruning method avoids redundant array traversals deep")
    print("within the search tree, making it theoretically and practically optimal.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()