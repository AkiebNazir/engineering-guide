"""
================================================================================
QUESTION · LeetCode 33 · Search in Rotated Sorted Array                [Medium]
https://leetcode.com/problems/search-in-rotated-sorted-array/
================================================================================
There is an integer array `nums` sorted in ascending order (with DISTINCT
values). Prior to being passed to your function, `nums` is possibly rotated
at an unknown pivot index k (1 <= k < nums.length) such that the resulting
array is [nums[k], nums[k+1], ..., nums[n-1], nums[0], nums[1], ..., nums[k-1]]
(0-indexed). For example, [0,1,2,4,5,6,7] might be rotated at pivot index 3
and become [4,5,6,7,0,1,2].

Given the array `nums` after the possible rotation and an integer `target`,
return the index of `target` if it is in `nums`, or -1 if it is not.

You must write an algorithm with O(log n) runtime complexity.

Example 1:
    Input:  nums = [4,5,6,7,0,1,2], target = 0
    Output: 4

Example 2:
    Input:  nums = [4,5,6,7,0,1,2], target = 3
    Output: -1

Example 3:
    Input:  nums = [1], target = 0
    Output: -1

Constraints:
    1 <= nums.length <= 5000
    -10^4 <= nums[i] <= 10^4
    All values of nums are UNIQUE.
    nums is an ascending array that is possibly rotated.
    -10^4 <= target <= 10^4
================================================================================
"""

from typing import List


class Solution:
    def search(self, nums: List[int], target: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 008_search_in_rotated_sorted_array_question.py
# ==============================================================================
CASES = [
    ([4, 5, 6, 7, 0, 1, 2], 0, 4),
    ([4, 5, 6, 7, 0, 1, 2], 3, -1),
    ([1], 0, -1),
    ([1], 1, 0),
    ([5, 1, 3], 5, 0),
    ([3, 1], 1, 1),
    ([4, 5, 6, 7, 8, 1, 2, 3], 8, 4),
    ([1, 2, 3, 4, 5, 6, 7], 5, 4),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for nums, target, expected in CASES:
        got = sol.search(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<28} target={target:<5} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
