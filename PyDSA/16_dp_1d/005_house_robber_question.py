"""
================================================================================
QUESTION · LeetCode 198 · House Robber                                [Medium]
https://leetcode.com/problems/house-robber/
================================================================================

PROBLEM
-------
You are a professional robber planning to rob houses along a street. Each
house has a certain amount of money stashed, the only constraint stopping
you from robbing each of them is that adjacent houses have connected
security systems and it will automatically contact the police if two
adjacent houses were broken into on the same night.

Given an integer array nums representing the amount of money of each
house, return the maximum amount of money you can rob tonight WITHOUT
alerting the police (ie. no two robbed houses may be adjacent).


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3,1]
    Output: 4
    Explanation: rob house 0 (money=1) and house 2 (money=3): 1+3=4.

Example 2:
    Input:  nums = [2,7,9,3,1]
    Output: 12
    Explanation: rob house 0 (2), house 2 (9), house 4 (1): 2+9+1=12.


CONSTRAINTS
-----------
    1 <= nums.length <= 100
    0 <= nums[i] <= 400


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[i] MEANS "the max loot achievable using only houses 0..i". At house i
you make exactly one decision: skip it (carry forward dp[i-1] unchanged),
or rob it (take nums[i] plus the best you could do up through i-2, since
i-1 is now off-limits). Take whichever is bigger:

    dp[i] = max(dp[i-1], dp[i-2] + nums[i])

This is the same fixed-window-of-2 shape as climbing stairs, but each cell
is a MAX-of-two-choices instead of a SUM.

PROGRESSIVE HINTS
------------------
Hint 1: At each house, you either skip it or rob it -- never anything else.
Hint 2: If you rob house i, house i-1 is forbidden, so you add nums[i] to
        the best total using houses 0..i-2, not 0..i-1.
Hint 3: dp[i] = max(dp[i-1], dp[i-2] + nums[i]); dp[-1]=0 (no houses),
        dp[0] = nums[0] as base cases if using a real array from index 0.
Hint 4: Fixed window of 2 back -- roll it down to O(1) space.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
"""

from typing import List


class Solution:
    def rob(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 2, 3, 1], 4),
        ([2, 7, 9, 3, 1], 12),
        ([2, 1, 1, 2], 4),
        ([5], 5),
        ([5, 5], 5),
        ([0, 0, 0], 0),
        ([200, 3, 140, 20, 10], 350),
    ]
    for nums, want in cases:
        got = sol.rob(nums[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
