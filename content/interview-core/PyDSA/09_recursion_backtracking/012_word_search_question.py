"""
================================================================================
LeetCode 79 · Word Search                                               [Medium]
https://leetcode.com/problems/word-search/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given an `m x n` grid of characters `board` and a string `word`, return `True` 
if `word` exists in the grid.

The word can be constructed from letters of sequentially adjacent cells, where 
adjacent cells are horizontally or vertically neighboring. The same letter cell 
may not be used more than once in a word.

EXAMPLES
--------
Example 1:
    Input: board = [
             ["A","B","C","E"],
             ["S","F","C","S"],
             ["A","D","E","E"]
           ], 
           word = "ABCCED"
    Output: True

Example 2:
    Input: board = [
             ["A","B","C","E"],
             ["S","F","C","S"],
             ["A","D","E","E"]
           ], 
           word = "SEE"
    Output: True

Example 3:
    Input: board = [
             ["A","B","C","E"],
             ["S","F","C","S"],
             ["A","D","E","E"]
           ], 
           word = "ABCB"
    Output: False

CONSTRAINTS
-----------
    m == board.length
    n = board[i].length
    1 <= m, n <= 6
    1 <= word.length <= 15
    board and word consists of only lowercase and uppercase English letters.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the first true "Grid Backtracking" problem. In previous problems (like 
Subsets or Permutations), the "state" being managed was a growing `path` list. 
Here, the state is which cells are currently "in use" on this exact path[cite: 2].

Instead of a `choices_at()` function returning elements from an array, your 
choices are always the up to 4 neighboring cells (up, down, left, right)[cite: 2]. 
Because a cell cannot be reused within the same word, you must track what has 
been visited. 

You can allocate a separate `visited` matrix, but mutating the board in place 
(e.g., swapping the character to `'#'`) is the standard O(1) space optimization.

THE DECISION TREE
------------------
For every cell in the grid, you attempt to start the word.
Each step down the decision tree checks if the current cell matches `word[i]`.
If it matches:
    1. CHOOSE: Mark the cell as visited (e.g., `board[r][c] = '#'`).
    2. EXPLORE: Recursively check the 4 neighbors for `word[i + 1]`.
    3. UNCHOOSE: Restore the cell to its original character.

WHAT TO THINK ABOUT
--------------------
1. What is the base case? (When your word index `i` equals `len(word)`).
2. What are the out-of-bounds or failure conditions? (Row/col out of bounds, 
   or the character doesn't match `word[i]`).
3. Why is the UNCHOOSE step unconditionally required, even if the explore step 
   failed? (Because the board is shared global state; an abandoned path must 
   clean up after itself so a completely different valid path can use those 
   same cells later)[cite: 2].

PROGRESSIVE HINTS
------------------
Hint 1: Write a nested loop to find the first character. Call a `dfs(r, c, i)` 
        helper from any cell that matches `word[0]`.
Hint 2: Inside `dfs`, handle the base cases first: if `i == len(word)`, return 
        True. If out of bounds or `board[r][c] != word[i]`, return False.
Hint 3: Temporarily store `board[r][c]` in a variable, then overwrite it with `'#'`.
Hint 4: Recursively call `dfs` on `(r+1, c)`, `(r-1, c)`, `(r, c+1)`, `(r, c-1)`. 
        If any return True, return True.
Hint 5: Unconditionally restore `board[r][c]` to the stored variable before 
        returning False.

COMPLEXITY TARGET
------------------
    Time:  O(rows * cols * 3^L) where L is the length of the word[cite: 2].
    Space: O(L) for the recursion stack depth.
================================================================================
"""

from typing import List


class Solution:
    def exist(self, board: List[List[str]], word: str) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 012_word_search_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (
            [["A","B","C","E"], ["S","F","C","S"], ["A","D","E","E"]],
            "ABCCED", True
        ),
        (
            [["A","B","C","E"], ["S","F","C","S"], ["A","D","E","E"]],
            "SEE", True
        ),
        (
            [["A","B","C","E"], ["S","F","C","S"], ["A","D","E","E"]],
            "ABCB", False
        ),
        (
            [["a"]], "a", True
        )
    ]
    passed = 0
    for board, word, expected in cases:
        # Deep copy board to prevent mutation across tests if user code is buggy
        board_copy = [row[:] for row in board]
        got = sol.exist(board_copy, word)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  word={word!r} -> {got} (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()