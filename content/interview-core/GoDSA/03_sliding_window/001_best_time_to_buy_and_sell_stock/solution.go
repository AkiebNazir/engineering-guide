package main

import "fmt"

/*
================================================================================
LeetCode 121 · Best Time to Buy and Sell Stock                            [Easy]
https://leetcode.com/problems/best-time-to-buy-and-sell-stock/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
You are given an array `prices` where `prices[i]` is the price of a given stock
on the `i`-th day.

You want to maximize your profit by choosing a SINGLE day to buy one stock and
choosing a DIFFERENT DAY IN THE FUTURE to sell that stock.

Return the maximum profit you can achieve from this transaction. If you cannot
achieve any profit, return 0.


EXAMPLES
--------
Example 1:
    Input:  prices = [7,1,5,3,6,4]
    Output: 5
    Explanation:
        Buy on day 2 (price = 1) and sell on day 5 (price = 6),
        profit = 6 - 1 = 5.
        Note that buying on day 2 and selling on day 1 is not allowed because
        you must buy before you sell.

Example 2:
    Input:  prices = [7,6,4,3,1]
    Output: 0
    Explanation: In this case, no transaction is done and the max profit = 0.


CONSTRAINTS
-----------
    1 <= prices.length <= 10^5
    0 <= prices[i] <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Restated in window language: find the pair of indices (buy, sell) with
`buy < sell` that maximises `prices[sell] - prices[buy]`.

The brute force is the entire n x n upper triangle:

    for buy in range(n):
        for sell in range(buy + 1, n):
            best = max(best, prices[sell] - prices[buy])

    O(n^2). At n = 10^5 that is 5 x 10^9 pairs. Far too slow.

THE KEY REFRAME. Walk the array once, treating each day in turn as the SELL day.
For a fixed sell day `r`, the best possible profit is

    prices[r] - (the minimum price seen anywhere before r)

and that minimum is something you can carry forward in a single variable. You
never need to look backwards, because "the cheapest day so far" is the only fact
about the past that can ever matter.

    prices = [7, 1, 5, 3, 6, 4]

    r=0  p=7   min_so_far=inf -> buy today. min=7.  profit today: -
    r=1  p=1   min=7  -> profit 1-7 = -6 (negative; ignore). New min=1.
    r=2  p=5   min=1  -> profit 4    best=4
    r=3  p=3   min=1  -> profit 2    best=4
    r=4  p=6   min=1  -> profit 5    best=5
    r=5  p=4   min=1  -> profit 3    best=5                       -> answer 5


WHY THIS FOLDER? — this is the DEGENERATE sliding window
--------------------------------------------------------
Think of `[l, r]` as a window where `l` is the buy day and `r` is the sell day.
The window's "aggregate" is `prices[r] - prices[l]`.

    * r always advances by one.  (expand)
    * l jumps to r the moment prices[r] < prices[l], because a cheaper buy day
      makes every earlier buy day permanently worthless.  (contract)

That second line is the elimination argument, and it is why the whole thing is
O(n). It is worth doing this problem first not because it is hard, but because
it is the smallest possible instance of "one pointer sweeps, the other one only
ever moves forward" — the amortization argument of Part 1.1 of the topic guide,
with an aggregate so simple it fits in one integer.

Some people insist this is not "really" a sliding window and call it a running
minimum, or a one-state DP (`best_profit_ending_here`). They are right. All
three descriptions are the same three lines of code. Being able to say that is
better than picking a side.


WHAT TO THINK ABOUT
-------------------
1. Which variable do you carry: the minimum price so far, or the maximum profit
   so far? (You need both — but only one of them is a scan over the past.)

2. ORDER OF OPERATIONS inside the loop. If you update `min_price` BEFORE
   computing today's profit, you allow buying and selling on the same day.
   Does that break anything here? Work out what it yields on [7,1,5,3,6,4] and
   on [5,4,3]. This is the single most instructive bug in the problem.

3. What is the answer when prices only ever fall? The problem says return 0, so
   what must you initialise `best` to, and what must you NOT do with negative
   profits?

4. `prices.length` can be 1. Does your loop handle a single day without an
   IndexError?

5. Try writing it as an explicit two-pointer loop (`l` = buy, `r` = sell) as
   well as the running-minimum version. They compile to the same work; make
   sure you can produce either on request.


PROGRESSIVE HINTS
-----------------
Hint 1: You only need ONE pass. Ask, for each day r: "if I sold today, what is
        the best I could have done?"

Hint 2: That question needs exactly one fact about days 0..r-1 — the smallest
        price among them. Keep it in a variable, update it as you go.

Hint 3: In the loop body, compute the profit FIRST, then update the minimum:

            best = max(best, price - min_price)
            min_price = min(min_price, price)

        Initialise `min_price = prices[0]` (or `float('inf')`) and `best = 0`.
        Never let a negative profit reach `best`.


COMPLEXITY TARGET
-----------------
    Time:  O(n)   — one pass, no inner loop
    Space: O(1)   — two scalars
================================================================================
*/

func main() {
	fmt.Println("Solution for Best Time to Buy and Sell Stock not implemented yet")
}
