"""
================================================================================
QUESTION · LeetCode 300 · Longest Increasing Subsequence               [Medium]
https://leetcode.com/problems/longest-increasing-subsequence/
================================================================================

PROBLEM
-------
Given an integer array nums, return the length of the longest strictly
increasing subsequence.


EXAMPLES
--------
Example 1:
    Input:  nums = [10,9,2,5,3,7,101,18]
    Output: 4
    Explanation: the longest increasing subsequence is [2,3,7,101], length 4.

Example 2:
    Input:  nums = [0,1,0,3,2,3]
    Output: 4

Example 3:
    Input:  nums = [7,7,7,7,7,7,7]
    Output: 1


CONSTRAINTS
-----------
    1 <= nums.length <= 2500
    -10^4 <= nums[i] <= 10^4

FOLLOW-UP: Can you come up with an algorithm that runs in O(n log n) time?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[i] MEANS "the length of the longest increasing subsequence ENDING
exactly at index i" (not "using the first i elements" -- the anchor is
"ends here," which matters because the true answer is the MAX over all
dp[i], not necessarily dp[n-1]). The last decision at i is "which earlier,
SMALLER element does this one extend" -- scan every j < i with
nums[j] < nums[i]:

    dp[i] = 1 + max(dp[j] for j < i if nums[j] < nums[i], default=0)
    answer = max(dp)

Variable-range look-back (same shape as Word Break/Coin Change), O(n^2)
worst case. The O(n log n) approach (patience sorting / binary search on
a "tails" array) is a genuinely different technique, not a DP
space-optimization -- see Approach 2 below.

PROGRESSIVE HINTS
------------------
Hint 1: Every single element is trivially an increasing subsequence of
        length 1 by itself -- that's the base value for every dp[i].
Hint 2: For each i, look at every earlier j: if nums[j] < nums[i], you
        COULD extend that subsequence by appending nums[i] -- try all such
        j and take the best (longest) one to extend.
Hint 3: The overall answer is max(dp), NOT dp[n-1] -- the longest
        subsequence might not end at the last element.
Hint 4: For O(n log n): maintain a "tails" array where tails[k] is the
        SMALLEST possible tail value of an increasing subsequence of
        length k+1 seen so far. For each new number, binary-search for
        where it belongs in tails and either extend or replace.

COMPLEXITY TARGET
------------------
    Time:  O(n log n)  (O(n^2) DP also acceptable to start with)
    Space: O(n)
================================================================================
"""

from typing import List


class Solution:
    def lengthOfLIS(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([10, 9, 2, 5, 3, 7, 101, 18], 4),
        ([0, 1, 0, 3, 2, 3], 4),
        ([7, 7, 7, 7, 7, 7, 7], 1),
        ([1], 1),
        ([1, 2, 3, 4, 5], 5),
        ([5, 4, 3, 2, 1], 1),
        ([4, 10, 4, 3, 8, 9], 3),
    ]
    for nums, want in cases:
        got = sol.lengthOfLIS(nums[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
