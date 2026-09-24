package main

import "fmt"

/*
================================================================================
LeetCode 2034 · Stock Price Fluctuation                                 [Medium]
https://leetcode.com/problems/stock-price-fluctuation/
Topic: 25 · Design
================================================================================

PROBLEM
-------
You are given a stream of records about a particular stock. Each record
contains a timestamp and the corresponding price of the stock at that
timestamp.

Unfortunately, the stream is not ordered, and some records may be INCORRECT.
Another record with the same timestamp may appear later, CORRECTING the
previous wrong record.

Design an algorithm that:
    - Updates the price at a timestamp, correcting the previous price if any.
    - Finds the LATEST price (price at the maximum timestamp recorded).
    - Finds the MAXIMUM price across all current records.
    - Finds the MINIMUM price across all current records.

Implement the StockPrice class:

    StockPrice()                   Initializes the object with no records.
    update(timestamp, price)       Updates the price at timestamp.
    current() -> int               Price at the latest timestamp.
    maximum() -> int               Maximum price among current records.
    minimum() -> int               Minimum price among current records.


EXAMPLES
--------
    update(1, 10)    records {1: 10}
    update(2, 5)     records {1: 10, 2: 5}
    current()   -> 5
    maximum()   -> 10
    update(1, 3)     CORRECTION: records {1: 3, 2: 5}
    maximum()   -> 5       (the old 10 no longer exists)
    update(4, 2)     records {1: 3, 2: 5, 4: 2}
    minimum()   -> 2


CONSTRAINTS
-----------
    1 <= timestamp, price <= 10^9
    At most 10^5 calls will be made in total to update, current, maximum, and
    minimum.
    current, maximum, and minimum will be called only after update has been
    called at least once.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Three questions, three different tools:

    current()   -> keep the max timestamp seen, and a dict timestamp -> price.
    maximum()   -> a max-heap of prices...
    minimum()   -> ...and a min-heap of prices.

The twist is CORRECTIONS. A heap can't delete an arbitrary old price. So use
LAZY DELETION: push (price, timestamp) pairs, and when reading the top, check
whether that timestamp's CURRENT price in the dict still equals the heap
entry's price. If not, the entry is stale: pop it and look again.

(Same trick as Sliding Window Median, 12_heap/012.)


WHAT TO THINK ABOUT
--------------------
1. Why store (price, timestamp) in the heap and not just price?

2. Two different timestamps can have the same price. Could a stale entry
   accidentally pass the validity check? Does it matter?

3. An alternative is a sorted multiset of prices with a count per price. What
   would it cost in Python?


PROGRESSIVE HINTS
------------------
Hint 1: prices = {}, latest = 0, max_heap = [], min_heap = [].

Hint 2: update: prices[t] = p; latest = max(latest, t); push (-p, t) and (p, t).

Hint 3: maximum: while prices[max_heap[0][1]] != -max_heap[0][0]: pop.
        Return -max_heap[0][0]. Same for minimum.


COMPLEXITY TARGET
------------------
    update O(log n), current O(1), maximum/minimum O(log n) amortized
    Space: O(number of updates)
================================================================================
*/

func main() {
	fmt.Println("Solution for Stock Price Fluctuation not implemented yet")
}
