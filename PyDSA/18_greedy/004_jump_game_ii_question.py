"""
================================================================================
QUESTION · LeetCode 45 · Jump Game II                                  [Medium]
https://leetcode.com/problems/jump-game-ii/
================================================================================

You are given a 0-indexed array of integers `nums` of length n. You are
initially positioned at index 0. Each element `nums[i]` represents the
maximum length of a forward jump from index i.

Return the MINIMUM number of jumps to reach `nums[n - 1]`. The test cases
are generated such that you can always reach the last index.

--------------------------------------------------------------------------------
EXAMPLES
--------------------------------------------------------------------------------
Input: nums = [2,3,1,1,4]
Output: 2
Explanation: Jump 1 step from index 0 to 1, then 3 steps to the last index.

Input: nums = [2,3,0,1,4]
Output: 2

--------------------------------------------------------------------------------
CONSTRAINTS
--------------------------------------------------------------------------------
- 1 <= nums.length <= 10^4
- 0 <= nums[i] <= 1000
- It is guaranteed that you can reach nums[n - 1].
"""


class Solution:
    def jump(self, nums: list[int]) -> int:
        # YOUR CODE HERE
        pass


def run_tests():
    sol = Solution()
    assert sol.jump([2, 3, 1, 1, 4]) == 2
    assert sol.jump([2, 3, 0, 1, 4]) == 2
    assert sol.jump([0]) == 0
    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
