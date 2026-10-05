package main

/*
================================================================================
QUESTION · LeetCode 518 · Coin Change II                             [Medium]
https://leetcode.com/problems/coin-change-ii/
================================================================================

PROBLEM
-------
You are given an integer array coins representing coins of different
denominations and an integer amount representing a total amount of money.

Return the number of combinations that make up that amount. If that amount
of money cannot be made up by any combination of the coins, return 0.

You may assume that you have an infinite number of each kind of coin.

The answer is guaranteed to fit into a signed 32-bit integer.


EXAMPLES
--------
Example 1:
    Input:  amount = 5, coins = [1,2,5]
    Output: 4
    Explanation: 5=5 5=2+2+1 5=2+1+1+1 5=1+1+1+1+1

Example 2:
    Input:  amount = 3, coins = [2]
    Output: 0

Example 3:
    Input:  amount = 10, coins = [10]
    Output: 1


CONSTRAINTS
-----------
    1 <= coins.length <= 300
    1 <= coins[i] <= 5000
    All the values of coins are unique.
    0 <= amount <= 5000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is UNBOUNDED KNAPSACK counting COMBINATIONS (order doesn't matter --
[1,2,2] and [2,1,2] are the SAME combination, counted once), which makes it
genuinely 2D: dp[i][a] = number of ways to make amount `a` using only the
FIRST i coin types (each usable unlimited times). The coin-type axis matters
because it's what prevents [1,2] and [2,1] from being double-counted --
"first i coin types" fixes an order in which coins are CONSIDERED, not the
order they're spent in.

    dp[i][a] = dp[i-1][a]              # don't use coin i at all
             + dp[i][a - coins[i-1]]   # use coin i at least once (note:
                                       #   dp[i], not dp[i-1] -- unbounded,
                                       #   coin i can repeat)

PROGRESSIVE HINTS
------------------
Hint 1: dp[i][a] = number of combinations summing to `a` using only coin
        TYPES 1..i (not a count of coins used).
Hint 2: For each coin type, decide "how many times to use it" implicitly by
        looping amounts LOW to HIGH after fixing that coin -- this is what
        allows unlimited reuse within a single coin type's pass.
Hint 3: Space-optimize to dp[a] (1D), but the OUTER loop must be over COINS
        and the INNER loop over amounts -- reversing the loop order counts
        permutations (order matters) instead of combinations (order
        doesn't), a different, larger number.
Hint 4: Base case dp[0] = 1 (exactly one way to make amount 0: use no coins).

COMPLEXITY TARGET
------------------
    Time:  O(len(coins) * amount)
    Space: O(amount)  (rolling 1D array over amounts)
================================================================================
*/

// TODO: Implement the stub
