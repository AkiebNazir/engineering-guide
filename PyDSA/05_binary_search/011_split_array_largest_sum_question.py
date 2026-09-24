"""
================================================================================
QUESTION · LeetCode 410 · Split Array Largest Sum                        [Hard]
https://leetcode.com/problems/split-array-largest-sum/
================================================================================
Given an integer array `nums` and an integer `k`, split `nums` into `k`
non-empty contiguous subarrays such that the largest sum of any subarray is
minimized.

Return the minimized largest sum of the split.

A subarray is a contiguous part of the array.

Example 1:
    Input:  nums = [7,2,5,10,8], k = 2
    Output: 18
    Explanation: There are four ways to split nums into two subarrays. The
    best way is to split it into [7,2,5] and [10,8], where the largest sum
    among the two subarrays is only 18.

Example 2:
    Input:  nums = [1,2,3,4,5], k = 2
    Output: 9

Constraints:
    1 <= nums.length <= 1000
    0 <= nums[i] <= 10^6
    1 <= k <= min(50, nums.length)
================================================================================
"""

from typing import List


class Solution:
    def splitArray(self, nums: List[int], k: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 011_split_array_largest_sum_question.py
# ==============================================================================
CASES = [
    ([7, 2, 5, 10, 8], 2, 18),
    ([1, 2, 3, 4, 5], 2, 9),
    ([1, 4, 4], 3, 4),
    ([1], 1, 1),
    ([1, 2, 3, 4, 5], 1, 15),
    ([1, 2, 3, 4, 5], 5, 5),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for nums, k, expected in CASES:
        got = sol.splitArray(nums, k)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<24} k={k:<3} -> {got}  (want {expected})")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
