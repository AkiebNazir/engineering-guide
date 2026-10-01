"""
================================================================================
QUESTION · LeetCode 153 · Find Minimum in Rotated Sorted Array         [Medium]
https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/
================================================================================
Suppose an array of length n sorted in ascending order is rotated between 1
and n times. For example, the array nums = [0,1,2,4,5,6,7] might become:
    [4,5,6,7,0,1,2] if it was rotated 4 times.
    [0,1,2,4,5,6,7] if it was rotated 7 times.

Given the sorted rotated array `nums` of UNIQUE elements, return the minimum
element of this array.

You must write an algorithm that runs in O(log n) time.

Example 1:
    Input:  nums = [3,4,5,1,2]
    Output: 1

Example 2:
    Input:  nums = [4,5,6,7,0,1,2]
    Output: 0

Example 3:
    Input:  nums = [11,13,15,17]
    Output: 11

Constraints:
    n == nums.length
    1 <= n <= 5000
    -5000 <= nums[i] <= 5000
    All the integers of nums are UNIQUE.
    nums is sorted and rotated between 1 and n times.
================================================================================
"""

from typing import List


class Solution:
    def findMin(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 007_find_minimum_in_rotated_sorted_array_question.py
# ==============================================================================
CASES = [
    ([3, 4, 5, 1, 2], 1),
    ([4, 5, 6, 7, 0, 1, 2], 0),
    ([11, 13, 15, 17], 11),
    ([1], 1),
    ([2, 1], 1),
    ([1, 2], 1),
    ([5, 1, 2, 3, 4], 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for nums, expected in CASES:
        got = sol.findMin(nums)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<24} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
