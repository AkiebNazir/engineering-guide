package main

/*
================================================================================
QUESTION · LeetCode 416 · Partition Equal Subset Sum                  [Medium]
https://leetcode.com/problems/partition-equal-subset-sum/
================================================================================

PROBLEM
-------
Given an integer array nums, return true if you can partition the array
into two subsets such that the sum of the elements in both subsets is
equal, or false otherwise.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,5,11,5]
    Output: true
    Explanation: the array can be partitioned as [1, 5, 5] and [11].

Example 2:
    Input:  nums = [1,2,3,5]
    Output: false
    Explanation: the array cannot be partitioned into equal sum subsets.


CONSTRAINTS
-----------
    1 <= nums.length <= 200
    1 <= nums[i] <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
If the total sum is odd, an equal split is impossible immediately -- return
false without doing any DP. Otherwise the question becomes "can some
subset of nums sum to EXACTLY total/2" (if one subset hits that target,
the rest of the array automatically sums to the same target). This is
0/1 KNAPSACK collapsed onto a single axis: dp[s] MEANS "is subset-sum s
achievable using the items considered SO FAR":

    dp[0] = True   (the empty subset always sums to 0)
    for each num in nums:
        for s from target DOWN TO num:
            dp[s] = dp[s] or dp[s - num]

The FULL 2D knapsack would be dp[item][sum]; this collapses the item axis
away, but ONLY works correctly if the sum axis is scanned HIGH to LOW --
see `_TOPIC_GUIDE.md` Part 4 Trap A for exactly why, and the solution
file's live demo of what goes wrong scanning the other direction.

PROGRESSIVE HINTS
------------------
Hint 1: If sum(nums) is odd, immediately return false -- no integer target
        can split it evenly.
Hint 2: The target for each subset is sum(nums) // 2. The question reduces
        to: does any subset of nums sum to exactly that target?
Hint 3: This is 0/1 knapsack (each number used AT MOST ONCE) collapsed to
        1D over the sum axis. Iterate the sum axis from HIGH to LOW for
        each item so you never "reuse" the same number twice within one
        item's own update pass.
Hint 4: A single boolean array of size target+1 suffices -- no need for a
        2D dp[item][sum] table.

COMPLEXITY TARGET
------------------
    Time:  O(n * target)   where target = sum(nums) // 2
    Space: O(target)
================================================================================
*/

// TODO: Implement the stub
