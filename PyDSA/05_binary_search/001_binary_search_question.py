"""
================================================================================
QUESTION · LeetCode 704 · Binary Search                                 [Easy]
https://leetcode.com/problems/binary-search/
================================================================================
Given an array of integers `nums` which is sorted in ascending order, and an
integer `target`, write a function to search `target` in `nums`. If `target`
exists, return its index. Otherwise, return -1.

You must write an algorithm with O(log n) runtime complexity.

Example 1:
    Input:  nums = [-1,0,3,5,9,12], target = 9
    Output: 4
    (9 exists in nums and its index is 4)

Example 2:
    Input:  nums = [-1,0,3,5,9,12], target = 2
    Output: -1
    (2 does not exist in nums so return -1)

Constraints:
    1 <= nums.length <= 10^4
    -10^4 < nums[i], target < 10^4
    All the integers in nums are UNIQUE.
    nums is sorted in ascending order.
================================================================================
"""

from typing import List


class Solution:
    def search(self, nums: List[int], target: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 001_binary_search_question.py
# ==============================================================================
CASES = [
    ([-1, 0, 3, 5, 9, 12], 9, 4),
    ([-1, 0, 3, 5, 9, 12], 2, -1),
    ([5], 5, 0),
    ([5], -5, -1),
    ([2, 5], 2, 0),
    ([2, 5], 5, 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for nums, target, expected in CASES:
        got = sol.search(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<28} target={target:<5} "
              f"-> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
