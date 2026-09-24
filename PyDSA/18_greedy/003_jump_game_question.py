"""
================================================================================
QUESTION · LeetCode 55 · Jump Game                                     [Medium]
https://leetcode.com/problems/jump-game/
================================================================================

You are given an integer array `nums`. You are initially positioned at the
array's first index, and each element in the array represents your maximum
jump length at that position.

Return `True` if you can reach the last index, or `False` otherwise.

--------------------------------------------------------------------------------
EXAMPLES
--------------------------------------------------------------------------------
Input: nums = [2,3,1,1,4]
Output: True
Explanation: Jump 1 step from index 0 to 1, then 3 steps to the last index.

Input: nums = [3,2,1,0,4]
Output: False
Explanation: You will always arrive at index 3 with a jump length of 0, which
makes it impossible to reach the last index.

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
- 1 <= nums.length <= 10^4
- 0 <= nums[i] <= 10^5
"""


class Solution:
    def canJump(self, nums: list[int]) -> bool:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.canJump([2, 3, 1, 1, 4]) is True
    assert sol.canJump([3, 2, 1, 0, 4]) is False
    assert sol.canJump([0]) is True
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
