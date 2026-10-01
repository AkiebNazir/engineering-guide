package main

/*
================================================================================
LeetCode 901 · Online Stock Span                                       [Medium]
https://leetcode.com/problems/online-stock-span/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
Design an algorithm that collects daily price quotes for some stock and
returns the SPAN of that stock's price for the current day.

The SPAN of the stock's price in one day is the maximum number of
consecutive days (starting from that day and going backwards) for which the
stock price was LESS THAN OR EQUAL TO the price of that day.

    For example, if the prices of the stock in the last four days is
    [7,2,1,2] and the price of the stock today is 2, then the span of today
    is 4 because starting from today, the price of the stock was less than
    or equal to today's price for 4 consecutive days.

    Also, if the prices of the stock in the last four days is [7,34,1,2]
    and the price of the stock today is 8, then the span of today is 3
    because starting from today, the price of the stock was less than or
    equal to today's price for 3 consecutive days.

Implement the `StockSpanner` class:
    StockSpanner()      initializes the object of the class.
    int next(int price)  returns the SPAN of the stock's price given that
                         today's price is `price`.


EXAMPLES
--------
Example 1:
    Input:
        ["StockSpanner","next","next","next","next","next","next","next"]
        [[],[100],[80],[60],[70],[60],[75],[85]]
    Output:
        [null,1,1,1,2,1,4,6]
    Explanation:
        StockSpanner stockSpanner = new StockSpanner();
        stockSpanner.next(100); // return 1
        stockSpanner.next(80);  // return 1
        stockSpanner.next(60);  // return 1
        stockSpanner.next(70);  // return 2
        stockSpanner.next(60);  // return 1
        stockSpanner.next(75);  // return 4, because the last 4 prices
                                //    (including today's price of 75) were
                                //    less than or equal to today's price
        stockSpanner.next(85);  // return 6


CONSTRAINTS
-----------
    1 <= price <= 10^5
    At most 10^4 calls will be made to `next`.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

"How many consecutive days back was the price <= today's?" is the same
question as "where is the PREVIOUS STRICTLY GREATER price?" — the span
runs from just after that day up to today. So this is problem 003's
monotonic stack (topic guide §2.0-2.3) with two twists:

    TWIST 1 · STREAMING. The array does not exist. Prices arrive one at a
    time and you must answer immediately, with no lookahead. That is fine:
    the monotonic stack only ever looks BACKWARDS, so it works unchanged
    online. In 003/007 the answer for day j is emitted when a LATER day
    pops it; here the answer for today is emitted at PUSH time, from what
    today pops.

    TWIST 2 · SPAN COLLAPSING. A day that today's price beats can never
    matter again — anything that beats today also beat it. So instead of
    keeping every day on the stack, keep (price, span) PAIRS and fold the
    popped day's span into today's:

        span = 1
        while stack and stack[-1].price <= price:
            span += stack.pop().span      # inherit everything it covered
        stack.push((price, span))
        return span

    The stack ends up holding strictly DECREASING prices, one entry per
    "still relevant" day, each carrying the total number of days it
    represents.


WHAT TO THINK ABOUT
--------------------
1. Why is it safe to throw away a day whose price is <= today's? What
   future price could ever need it?
2. If you popped days one at a time WITHOUT accumulating their spans,
   what would you have to store to still get the right answer — and how
   would that change the cost of a `next` call?
3. The definition says "less than or equal to". Does the pop condition use
   `<` or `<=`? Feed [60, 60, 60] through both and compare.
4. Each `next` call can pop many entries, so a single call is NOT O(1).
   Why is the AMORTIZED cost still O(1)? (Topic guide §2.1 — say it in one
   sentence.)


PROGRESSIVE HINTS
------------------
Hint 1: `self.stack = []`, holding `(price, span)` tuples.

Hint 2: In `next(price)`: start `span = 1` (today always counts itself),
        then `while self.stack and self.stack[-1][0] <= price:` pop and
        add the popped span to `span`.

Hint 3: Push `(price, span)` and return `span`. The prices on the stack are
        strictly decreasing bottom-to-top — that is the invariant that
        makes the `while` terminate early.


COMPLEXITY TARGET
------------------
    Time:  O(1) AMORTIZED per `next` call, O(n) for n calls total. Each
           price is pushed exactly once and popped at most once, so the
           total pop work across all calls is bounded by the number of
           calls — not by calls-squared. A single call can still cost
           O(n) in the worst case (a new all-time high collapses the whole
           stack), which is worth stating precisely.
    Space: O(n) worst case for the stack (strictly decreasing prices:
           nothing is ever popped). Best case O(1) — a strictly increasing
           stream keeps exactly ONE entry on the stack, no matter how long
           the stream is.
================================================================================
*/

// TODO: Implement the stub
