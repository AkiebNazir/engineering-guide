"""
================================================================================
QUESTION · LeetCode 74 · Search a 2D Matrix                            [Medium]
https://leetcode.com/problems/search-a-2d-matrix/
================================================================================
You are given an m x n integer matrix `matrix` with the following two
properties:
    - Each row is sorted in non-decreasing order.
    - The first integer of each row is greater than the last integer of the
      previous row.

Given an integer `target`, return true if `target` is in `matrix` or false
otherwise.

You must write a solution in O(log(m * n)) time complexity.

Example 1:
    Input:  matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 3
    Output: true

Example 2:
    Input:  matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 13
    Output: false

Constraints:
    m == matrix.length
    n == matrix[i].length
    1 <= m, n <= 100
    -10^4 <= matrix[i][j], target <= 10^4
================================================================================
"""

from typing import List


class Solution:
    def searchMatrix(self, matrix: List[List[int]], target: int) -> bool:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 005_search_a_2d_matrix_question.py
# ==============================================================================
CASES = [
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3, True),
    ([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13, False),
    ([[1]], 1, True),
    ([[1]], 2, False),
    ([[1, 3]], 3, True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for matrix, target, expected in CASES:
        got = sol.searchMatrix(matrix, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  target={target:<5} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
