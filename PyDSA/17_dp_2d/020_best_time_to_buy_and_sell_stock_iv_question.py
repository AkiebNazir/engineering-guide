"""
================================================================================
LeetCode 188 · Best Time to Buy and Sell Stock IV                         [Hard]
https://leetcode.com/problems/best-time-to-buy-and-sell-stock-iv/
Topic: 17 · Dynamic Programming (2D)
================================================================================

PROBLEM
-------
You are given an integer k and an array prices where prices[i] is the price of
a stock on day i.

Find the maximum profit you can achieve with AT MOST k transactions: you may
buy at most k times and sell at most k times. You may not hold more than one
share at a time (you must sell before you buy again).


EXAMPLES
--------
Example 1:   k = 2, prices = [2, 4, 1]            ->  2
    Buy on day 0 (price 2), sell on day 1 (price 4).

Example 2:   k = 2, prices = [3, 2, 6, 5, 0, 3]   ->  7
    Buy at 2, sell at 6 (+4); buy at 0, sell at 3 (+3).


CONSTRAINTS
-----------
    1 <= k <= 100
    1 <= prices.length <= 1000
    0 <= prices[i] <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This generalises a whole family:

    LC 121  one transaction           (k = 1)
    LC 122  unlimited transactions    (k = infinity)
    LC 123  two transactions          (k = 2)
    LC 309  unlimited, with cooldown  (17_dp_2d/006)

On any day you are in one of two situations for each transaction count:
HOLDING a share, or NOT holding one. That is a small STATE MACHINE:

    not holding --buy--> holding --sell--> not holding (one more transaction used)

For each j = 1..k keep the best profit so far in each state:

    hold[j] = best profit while holding, having started j transactions
    free[j] = best profit while not holding, having completed j transactions


WHAT TO THINK ABOUT
--------------------
1. When is "at most k" the same as "unlimited"? (How many profitable
   transactions can n days contain at most?)

2. On day p, how does buying move you between states? Selling?

3. Can a single day's price be used for both a sell and a buy of the next
   transaction? Does it matter?


PROGRESSIVE HINTS
------------------
Hint 1: If k >= n // 2 you can take every upward step: sum of positive
        differences.

Hint 2: For each price p and j from 1 to k:
            hold[j] = max(hold[j], free[j-1] - p)
            free[j] = max(free[j], hold[j] + p)

Hint 3: Initialise hold[j] = -infinity, free[j] = 0. Answer: free[k].


COMPLEXITY TARGET
------------------
    Time:  O(n * k)   (or O(n) when k >= n // 2)
    Space: O(k)
================================================================================
"""
from typing import List


class Solution:
    def maxProfit(self, k: int, prices: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 020_best_time_to_buy_and_sell_stock_iv_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        (2, [2, 4, 1], 2),
        (2, [3, 2, 6, 5, 0, 3], 7),
        (1, [7, 1, 5, 3, 6, 4], 5),
        (2, [3, 3, 5, 0, 0, 3, 1, 4], 6),
        (100, [1, 2, 3, 4, 5], 4),
        (2, [7, 6, 4, 3, 1], 0),
        (1, [5], 0),
        (3, [1, 3, 2, 8, 4, 9, 2, 5], 15),
    ]
    all_ok = True
    for k, prices, want in cases:
        got = Solution().maxProfit(k, list(prices))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k} prices={prices}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
