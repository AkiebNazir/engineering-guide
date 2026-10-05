"""
================================================================================
LeetCode 85 · Maximal Rectangle                                           [Hard]
https://leetcode.com/problems/maximal-rectangle/
Topic: 06 · Stack & Monotonic Stack
================================================================================

PROBLEM
-------
Given a rows x cols binary matrix filled with the CHARACTERS '0' and '1', find
the largest rectangle containing only '1's and return its area.


EXAMPLES
--------
Example 1:
    matrix = [["1","0","1","0","0"],
              ["1","0","1","1","1"],
              ["1","1","1","1","1"],
              ["1","0","0","1","0"]]
    ->  6     (rows 1-2, columns 2-4)

Example 2:   matrix = [["0"]]   ->  0
Example 3:   matrix = [["1"]]   ->  1


CONSTRAINTS
-----------
    rows == matrix.length, cols == matrix[i].length
    1 <= rows, cols <= 200
    matrix[i][j] is '0' or '1'  (strings, not integers)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Fix the BOTTOM row of the rectangle. For each column, count how many
consecutive '1's stand directly above and including that row — a column
"height". The heights of one row form a histogram:

    row 2 of Example 1:          heights = [3, 1, 3, 2, 2]

      #   #
      #   # # #
      # # # # #

The best rectangle whose bottom edge is on this row is exactly the
Largest Rectangle in Histogram (06_stack/010) of those heights: area 6 from
the three bars [3, 2, 2] at height 2.

So: update heights row by row (height + 1 on '1', reset to 0 on '0') and run
the monotonic-stack histogram algorithm on each row. The best over all rows is
the answer.


WHAT TO THINK ABOUT
--------------------
1. Why is fixing the bottom row enough to see every rectangle exactly once?

2. How do the heights change from one row to the next?

3. The cells are the strings "0" and "1". What does `if cell:` do with "0"?

4. Why doesn't the Maximal Square DP (17_dp_2d/004) generalise to rectangles?


PROGRESSIVE HINTS
------------------
Hint 1: heights[j] = heights[j] + 1 if cell == "1" else 0.

Hint 2: Largest rectangle in a histogram: keep a stack of indices with
        increasing heights; when a lower bar arrives, pop and compute each
        popped bar's area with the new stack top as its left boundary.

Hint 3: Append a height-0 sentinel so every bar is popped at the end.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols)
    Space: O(cols)
================================================================================
"""
from typing import List


class Solution:
    def maximalRectangle(self, matrix: List[List[str]]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 016_maximal_rectangle_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([["1", "0", "1", "0", "0"],
          ["1", "0", "1", "1", "1"],
          ["1", "1", "1", "1", "1"],
          ["1", "0", "0", "1", "0"]], 6),
        ([["0"]], 0),
        ([["1"]], 1),
        ([["1", "1", "1", "1"]], 4),
        ([["1"], ["1"], ["1"]], 3),
        ([["0", "1"], ["1", "0"]], 1),
        ([["1", "1", "0", "1"],
          ["1", "1", "0", "1"],
          ["1", "1", "1", "1"]], 6),
    ]
    all_ok = True
    for matrix, want in cases:
        got = Solution().maximalRectangle([row[:] for row in matrix])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {len(matrix)}x{len(matrix[0])} matrix  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
