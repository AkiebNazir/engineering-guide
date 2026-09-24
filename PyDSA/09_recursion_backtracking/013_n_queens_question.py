"""
================================================================================
LeetCode 51 · N-Queens                                                    [Hard]
https://leetcode.com/problems/n-queens/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
The n-queens puzzle is the problem of placing `n` queens on an `n x n` 
chessboard such that no two queens attack each other.

Given an integer `n`, return all distinct solutions to the n-queens puzzle. 
You may return the answer in any order.

Each solution contains a distinct board configuration of the n-queens' placement, 
where 'Q' and '.' both indicate a queen and an empty space, respectively.

EXAMPLES
--------
Example 1:
    Input:  n = 4
    Output: [[".Q..",  // Solution 1
              "...Q",
              "Q...",
              "..Q."],
             ["..Q.",  // Solution 2
              "Q...",
              "...Q",
              ".Q.."]]

Example 2:
    Input:  n = 1
    Output: [["Q"]]

CONSTRAINTS
-----------
    1 <= n <= 9

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the archetype of Constraint Satisfaction backtracking. 

If you approach this like Word Search and just try to place 'Q's in any empty 
cell, the search space for n=8 is massive (64 choose 8 = ~4.4 billion). 

Instead, we use logic to structure our choices:
1. Two queens cannot share the same row. Therefore, we should place exactly 
   ONE queen per row. Our decision tree depth is `n` (the rows), and at each 
   level, our choices are the `n` columns. This immediately drops the raw 
   search space to n^n (8^8 = 16,777,216)[cite: 2].
2. Two queens cannot share the same column.
3. Two queens cannot share the same diagonal.

The magic of this algorithm lies in checking these constraints BEFORE we recurse. 
If we are at row 3, and column 2 is under attack by a queen placed in row 0, 
we do NOT place a queen there. We skip it. This prevents us from exploring 
millions of dead-end branches[cite: 2].

WHAT TO THINK ABOUT
--------------------
1. Tracking Columns: How do you know if a column is safe? (A simple `set` or 
   boolean array `cols` works perfectly).
2. Tracking Diagonals: This is the tricky part. How do you identify if a cell 
   (r, c) shares a diagonal with another cell?
    - Look at a grid. As you move top-right to bottom-left (Negative Diagonal), 
      what stays constant? The difference between row and col: `(r - c)`.
    - As you move top-left to bottom-right (Positive Diagonal), what stays 
      constant? The sum of row and col: `(r + c)`.
3. If you maintain three sets (`cols`, `pos_diag`, `neg_diag`), you can check 
   if a cell is safe in O(1) time[cite: 2]!

PROGRESSIVE HINTS
------------------
Hint 1: Create three sets: `col_used`, `pos_diag_used`, `neg_diag_used`.
Hint 2: Create a backtracking function `backtrack(row)`.
Hint 3: Inside `backtrack(row)`, iterate `col` from 0 to n-1. 
Hint 4: If `col` is in `col_used`, or `(row + col)` is in `pos_diag_used`, or 
        `(row - col)` is in `neg_diag_used`, `continue` (skip this choice).
Hint 5: If it is safe, CHOOSE: add to all three sets, add the position to your 
        path. EXPLORE: call `backtrack(row + 1)`. UNCHOOSE: remove from all 
        sets and path.

COMPLEXITY TARGET
------------------
    Time:  O(N!) worst case, but practically vastly faster due to pruning.
    Space: O(N) for the tracking sets and recursion stack.
================================================================================
"""

from typing import List


class Solution:
    def solveNQueens(self, n: int) -> List[List[str]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 013_n_queens_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (4, [[".Q..","...Q","Q...","..Q."],["..Q.","Q...","...Q",".Q.."]]),
        (1, [["Q"]]),
        (2, []),  # No solution for 2x2
        (3, []),  # No solution for 3x3
    ]
    passed = 0
    for n, expected in cases:
        got = sol.solveNQueens(n)
        # Sort to ensure order doesn't fail the test
        got_sorted = sorted(["".join(board) for board in got]) if got else []
        exp_sorted = sorted(["".join(board) for board in expected])
        
        ok = got_sorted == exp_sorted
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n} -> found {len(got)} solutions")
        if not ok:
            print(f"    Expected: {expected}")
            print(f"    Got:      {got}")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()