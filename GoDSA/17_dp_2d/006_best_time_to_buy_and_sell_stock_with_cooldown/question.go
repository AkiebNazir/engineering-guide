package main

/*
================================================================================
QUESTION · LeetCode 309 · Best Time to Buy and Sell Stock with Cooldown
                                                                       [Medium]
https://leetcode.com/problems/best-time-to-buy-and-sell-stock-with-cooldown/
================================================================================

PROBLEM
-------
You are given an array prices where prices[i] is the price of a given stock
on the i-th day.

Find the maximum profit you can achieve. You may complete as many
transactions as you like (buy one and sell one share of the stock multiple
times) with the following restrictions:
- After you sell your stock, you cannot buy stock on the next day (i.e.,
  cooldown one day).
- You may not engage in multiple transactions simultaneously (i.e., you must
  sell the stock before you buy again).


EXAMPLES
--------
Example 1:
    Input:  prices = [1,2,3,0,2]
    Output: 3
    Explanation: transactions = [buy, sell, cooldown, buy, sell]

Example 2:
    Input:  prices = [1]
    Output: 0


CONSTRAINTS
-----------
    1 <= prices.length <= 5000
    0 <= prices[i] <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is STATE-MACHINE DP: on each day you're in exactly one of three states,
and the "2D" shape is (day, state) rather than (day, day) like the two-string
family. Define, for day i:

    held[i] = max profit on day i while HOLDING a share
    sold[i] = max profit on day i having just SOLD (today)
    rest[i] = max profit on day i while NOT holding and NOT just sold
              (in cooldown OR simply idle)

Transitions (what could have been true YESTERDAY to reach each state today):
    held[i] = max(held[i-1],            # did nothing, still holding
                   rest[i-1] - price[i]) # bought today (must have been resting
                                         #   yesterday -- can't buy right after
                                         #   selling, that's the cooldown rule)
    sold[i] = held[i-1] + price[i]       # sold today -- must have held yesterday
    rest[i] = max(rest[i-1], sold[i-1])  # stayed resting, or cooldown just ended

PROGRESSIVE HINTS
------------------
Hint 1: Three states per day, not one -- this is why it's "2D DP" (day x
        state) even though there's only one input array.
Hint 2: The cooldown rule means `held[i]` can only draw its "just bought"
        transition from `rest[i-1]`, never from `sold[i-1]` directly.
Hint 3: Base case day 0: held[0] = -prices[0] (bought on day 0), sold[0] = 0
        (can't sell before buying), rest[0] = 0 (did nothing).
Hint 4: Final answer is max(sold[n-1], rest[n-1]) -- you'd never end holding
        a share you could have sold for more.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)  (only need yesterday's three values)
================================================================================
*/

// TODO: Implement the stub
