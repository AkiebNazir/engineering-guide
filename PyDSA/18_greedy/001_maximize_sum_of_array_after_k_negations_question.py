"""
================================================================================
QUESTION · LeetCode 1005 · Maximize Sum Of Array After K Negations       [Easy]
https://leetcode.com/problems/maximize-sum-of-array-after-k-negations/
================================================================================

Given an integer array `nums` and an integer `k`, modify the array in the
following way: choose an index `i` and replace `nums[i]` with `-nums[i]`.
You must do this exactly `k` times (you may choose the same index more than
once).

Return the largest possible sum of the array after modifying it in this way.

--------------------------------------------------------------------------------
EXAMPLES
--------------------------------------------------------------------------------
Input: nums = [4,2,3], k = 1
Output: 5
Explanation: Negate index 1, nums becomes [4,-2,3], sum = 5.

Input: nums = [3,-1,0,2], k = 3
Output: 6
Explanation: Negate index 1, then 2, then 1 (or any 3 negations that end up
negating every negative once). One optimal end state: [3,1,0,2], sum = 6.

Input: nums = [2,-3,-1,5,-4], k = 2
Output: 13

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
- 1 <= nums.length <= 10^4
- -100 <= nums[i] <= 100
- 1 <= k <= 10^4
"""


class Solution:
    def largestSumAfterKNegations(self, nums: list[int], k: int) -> int:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.largestSumAfterKNegations([4, 2, 3], 1) == 5
    assert sol.largestSumAfterKNegations([3, -1, 0, 2], 3) == 6
    assert sol.largestSumAfterKNegations([2, -3, -1, 5, -4], 2) == 13
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
