"""
================================================================================
QUESTION · LeetCode 215 · Kth Largest Element in an Array             [Medium]
https://leetcode.com/problems/kth-largest-element-in-an-array/
================================================================================

Given an integer array `nums` and an integer `k`, return the kth largest
element in the array.

Note: it is the kth largest element in SORTED ORDER, not the kth distinct
element. Duplicates count individually.

You must solve it without sorting, in linear time (average case is fine).

Example 1:
    Input:  nums = [3,2,1,5,6,4], k = 2
    Output: 5

Example 2:
    Input:  nums = [3,2,3,1,2,4,5,5,6], k = 4
    Output: 4

Constraints:
    1 <= k <= nums.length <= 10^5
    -10^4 <= nums[i] <= 10^4
"""

from typing import List


class Solution:
    def findKthLargest(self, nums: List[int], k: int) -> int:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.findKthLargest([3, 2, 1, 5, 6, 4], 2) == 5
    assert sol.findKthLargest([3, 2, 3, 1, 2, 4, 5, 5, 6], 4) == 4
    assert sol.findKthLargest([1], 1) == 1
    assert sol.findKthLargest([2, 1], 2) == 1
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
