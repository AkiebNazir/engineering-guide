package main

/*
================================================================================
QUESTION · LeetCode 494 · Target Sum                                 [Medium]
https://leetcode.com/problems/target-sum/
================================================================================

PROBLEM
-------
You are given an integer array nums and an integer target.

You want to build an expression out of nums by adding one of the symbols
'+' and '-' before each integer in nums and then concatenate all the
integers.

Return the number of different expressions that you can build, which
evaluates to target.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,1,1,1,1], target = 3
    Output: 5
    Explanation: -1+1+1+1+1 = 3, +1-1+1+1+1 = 3, +1+1-1+1+1 = 3,
                 +1+1+1-1+1 = 3, +1+1+1+1-1 = 3

Example 2:
    Input:  nums = [1], target = 1
    Output: 1


CONSTRAINTS
-----------
    1 <= nums.length <= 20
    0 <= nums[i] <= 1000
    0 <= sum(nums[i]) <= 1000
    -1000 <= target <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The brute-force view is 2^n sign assignments (topic 09 backtracking
territory) -- but it reduces to counting SUBSETS, a 0/1 knapsack shape.
Split nums into a "positive" subset P (assigned '+') and "negative" subset N
(assigned '-'). Then:

    sum(P) - sum(N) = target
    sum(P) + sum(N) = sum(nums)          (every number is in exactly one)

Adding these: 2*sum(P) = target + sum(nums), so
    sum(P) = (target + sum(nums)) / 2

This is now "count subsets of nums that sum to exactly sum(P)" -- CLASSIC
0/1 knapsack counting, which is dp[i][s] = ways to reach sum `s` using only
the first i numbers, each used AT MOST once (unlike 007's unbounded reuse).

PROGRESSIVE HINTS
------------------
Hint 1: Reframe "assign +/- to each number" as "partition into a
        POSITIVE-subset and a NEGATIVE-subset."
Hint 2: sum(positive) - sum(negative) = target and sum(positive) +
        sum(negative) = total  =>  sum(positive) = (target + total) / 2.
Hint 3: If (target + total) is ODD, or its absolute value exceeds total,
        there is NO valid partition -- return 0 immediately (no subset can
        have a non-integer or out-of-range sum).
Hint 4: dp[i][s] = number of subsets of the first i numbers summing to s.
        dp[i][s] = dp[i-1][s] (skip num i) + dp[i-1][s - nums[i-1]] (take
        it) -- note dp[i-1] on BOTH branches, unlike 007's unbounded reuse.
Hint 5: Space-optimizing to 1D requires iterating sums HIGH to LOW (0/1
        knapsack direction) to avoid reusing the same number twice within
        one pass -- the OPPOSITE direction from 007's unbounded coin change.

COMPLEXITY TARGET
------------------
    Time:  O(len(nums) * total_sum)
    Space: O(total_sum)  (rolling 1D array over subset sums)
================================================================================
*/

// TODO: Implement the stub
