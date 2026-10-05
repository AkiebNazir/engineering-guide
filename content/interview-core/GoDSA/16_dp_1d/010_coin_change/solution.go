package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 322 · Coin Change                                 [Medium]
https://leetcode.com/problems/coin-change/
================================================================================

PROBLEM
-------
You are given an integer array coins representing coins of different
denominations and an integer amount representing a total amount of money.

Return the fewest number of coins that you need to make up that amount.
If that amount of money cannot be made up by any combination of the
coins, return -1.

You may assume that you have an infinite number of each kind of coin.


EXAMPLES
--------
Example 1:
    Input:  coins = [1,2,5], amount = 11
    Output: 3
    Explanation: 11 = 5 + 5 + 1

Example 2:
    Input:  coins = [2], amount = 3
    Output: -1

Example 3:
    Input:  coins = [1], amount = 0
    Output: 0


CONSTRAINTS
-----------
    1 <= coins.length <= 12
    1 <= coins[i] <= 2^31 - 1
    0 <= amount <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
dp[a] MEANS "the minimum number of coins to make EXACTLY amount a" -- a
VALUE-indexed 1D DP (the "index" is a target amount, not a position in an
array; see `_TOPIC_GUIDE.md` Part 2's index-indexed vs value-indexed
split). Since coins are UNLIMITED (unbounded knapsack), the last coin used
to reach amount a could be ANY coin c in coins, as long as a-c was already
achievable:

    dp[0] = 0
    dp[a] = 1 + min(dp[a - c] for c in coins if c <= a and dp[a-c] != inf)

Unlike the fixed-window problems so far, this recurrence SCANS all coins
at every amount -- a variable-range look-back, not a fixed 1 or 2 back.

PROGRESSIVE HINTS
------------------
Hint 1: dp[0] = 0 (zero coins needed to make amount 0).
Hint 2: For each amount a from 1 up to the target, try using EACH coin c
        as the LAST coin: candidate = 1 + dp[a-c], but only if a-c >= 0
        and dp[a-c] is reachable.
Hint 3: Initialize unreachable amounts to a sentinel (infinity, or amount+1)
        so "impossible" cleanly loses every min() comparison.
Hint 4: Iterate amounts LOW to HIGH (unlike the 0/1 knapsack direction in
        problem 014) -- each coin can be reused within the same amount's
        build-up, which is exactly what "unlimited coins" requires.

COMPLEXITY TARGET
------------------
    Time:  O(amount * len(coins))
    Space: O(amount)
================================================================================
*/

func main() {
	fmt.Println("Solution for Coin Change not implemented yet")
}
