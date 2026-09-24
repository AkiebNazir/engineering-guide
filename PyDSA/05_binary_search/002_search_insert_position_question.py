"""
================================================================================
QUESTION · LeetCode 35 · Search Insert Position                         [Easy]
https://leetcode.com/problems/search-insert-position/
================================================================================
Given a sorted array of distinct integers `nums` and a `target` value, return
the index if the target is found. If not, return the index where it would be
if it were inserted in order.

You must write an algorithm with O(log n) runtime complexity.

Example 1:
    Input:  nums = [1,3,5,6], target = 5
    Output: 2

Example 2:
    Input:  nums = [1,3,5,6], target = 2
    Output: 1

Example 3:
    Input:  nums = [1,3,5,6], target = 7
    Output: 4

Constraints:
    1 <= nums.length <= 10^4
    -10^4 <= nums[i] <= 10^4
    nums contains distinct values sorted in ascending order.
    -10^4 <= target <= 10^4
================================================================================
"""

from typing import List


class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 002_search_insert_position_question.py
# ==============================================================================
CASES = [
    ([1, 3, 5, 6], 5, 2),
    ([1, 3, 5, 6], 2, 1),
    ([1, 3, 5, 6], 7, 4),
    ([1, 3, 5, 6], 0, 0),
    ([1], 1, 0),
    ([1], 0, 0),
    ([1], 2, 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for nums, target, expected in CASES:
        got = sol.searchInsert(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<20} target={target:<5} "
              f"-> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
