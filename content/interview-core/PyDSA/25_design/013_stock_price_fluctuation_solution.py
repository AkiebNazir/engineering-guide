"""
================================================================================
SOLUTION · LeetCode 2034 · Stock Price Fluctuation                      [Medium]
https://leetcode.com/problems/stock-price-fluctuation/
================================================================================

THE CORE IDEA
--------------
A dict timestamp -> price is the source of truth. Two heaps answer max and min,
and they're allowed to contain STALE entries. Each heap entry is (price,
timestamp); an entry is valid only if prices[timestamp] still equals its price.
When reading a top, pop invalid entries until a valid one surfaces. Corrections
become one dict write plus two heap pushes; old entries die lazily.


================================================================================
APPROACH 1 · Dict + scan on every query (priced, used as oracle)
================================================================================
    maximum(): max(prices.values())

    update O(1), current O(1), maximum/minimum O(n)
    With 10^5 calls that's up to ~10^10 / 4 operations if queries dominate.


================================================================================
APPROACH 2 · Dict + two heaps with lazy deletion ✅ (the answer)
================================================================================
    update(t, p):
        prices[t] = p
        latest = max(latest, t)
        heappush(max_heap, (-p, t))
        heappush(min_heap, (p, t))

    maximum():
        while prices[max_heap[0][1]] != -max_heap[0][0]:
            heappop(max_heap)
        return -max_heap[0][0]

    minimum(): mirror image.
    current(): prices[latest]

WHY STORE THE TIMESTAMP. The validity check needs to look up the record the
entry came from. A bare price can't tell you whether it's still somebody's
current price.

WHAT ABOUT EQUAL PRICES? Suppose timestamp 1 was corrected 10 -> 3 and
timestamp 7 also has price 10. The stale (10, t=1) fails its check
(prices[1] == 3), and (10, t=7) passes. Each entry is checked against its OWN
timestamp, so there's no confusion.

AMORTIZED COST. Every pushed entry is popped at most once, so the total heap
work over the whole run is O(U log U) for U updates, no matter how queries are
interleaved.

    update O(log U), current O(1), max/min O(log U) amortized
    Space: O(U) — stale entries linger until they reach a top


================================================================================
APPROACH 3 · Sorted multiset of prices (count per price)
================================================================================
Keep price -> count in a sorted structure. On correction, decrement the old
price's count (delete at zero) and increment the new. max/min are the ends.
With a balanced BST / SortedList: O(log n) for everything and no stale entries.
Python's stdlib has no sorted multiset, so heaps are the usual interview answer.


================================================================================
STEP BY STEP TRACE
================================================================================
    update(1,10)  prices {1:10}        max_heap [(-10,1)]          min_heap [(10,1)]
    update(2,5)   prices {1:10,2:5}    max_heap [(-10,1),(-5,2)]   min_heap [(5,2),(10,1)]
    current()  -> prices[2] = 5
    maximum()  -> top (-10,1): prices[1] == 10 valid -> 10
    update(1,3)   prices {1:3,2:5}     max_heap [(-10,1),(-5,2),(-3,1)]
    maximum()  -> top (-10,1): prices[1] == 3 != 10 -> pop
                  top (-5,2):  prices[2] == 5 valid -> 5
    update(4,2)   prices {1:3,2:5,4:2}
    minimum()  -> top (2,4) valid -> 2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    update      current  max / min          Space
    --------------------------  ----------  -------  -----------------  -----
    Dict + scan                 O(1)        O(1)     O(n)               O(n)
    Dict + lazy heaps ✅        O(log U)    O(1)     O(log U) amortized O(U)
    Dict + sorted multiset      O(log n)    O(1)     O(log n)           O(n)


================================================================================
EDGE CASES
================================================================================
    Correction of the latest timestamp   current() reflects it immediately.
    Correction to the same price         Duplicate valid entries; harmless.
    Many corrections to one timestamp    Heaps grow; stale entries pop lazily.
    Out-of-order timestamps              latest = max(...), not "last seen".


================================================================================
COMMON MISTAKES
================================================================================
1. Heaps without the validity check: maximum() returns a price that was
   corrected away. The LC example returns 10 instead of 5. Demo below.

2. current() returns the price from the most recent update CALL instead of the
   largest TIMESTAMP. Out-of-order updates break it. Demo below.

3. Validity check compares only prices ("is this price present anywhere?")
   using a Counter, then forgets to decrement on correction.

4. Trying to remove the stale entry from the heap directly (list.remove +
   heapify): O(n) per correction.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Max price within a time RANGE [t1, t2]?
A: Segment tree (or sparse table if static) indexed by compressed timestamps;
   updates are point assignments, queries range max. O(log n).

Q: Memory is bounded; heaps accumulate stale entries?
A: Rebuild the heaps from the dict when stale entries exceed, say, 2x the live
   count. Amortized cost stays O(log n).

Q: Millions of tickers, real-time dashboards?
A: Per-ticker state in a stream processor keyed by symbol, with late/corrected
   events handled by event-time windows and watermarks. See the stream
   processing building block in SystemDesign.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 480   Sliding Window Median (12_heap/012) — lazy deletion
    LC 2353  Design a Food Rating System         — per-category lazy heaps
    LC 1845  Seat Reservation Manager            — heap of free seats
    LC 895   Maximum Frequency Stack
================================================================================
"""

import heapq
import random
import time
from typing import Dict, List, Tuple


class StockPrice:
    def __init__(self):
        self.prices: Dict[int, int] = {}
        self.latest = 0
        self.max_heap: List[Tuple[int, int]] = []
        self.min_heap: List[Tuple[int, int]] = []

    def update(self, timestamp: int, price: int) -> None:
        self.prices[timestamp] = price
        if timestamp > self.latest:
            self.latest = timestamp
        heapq.heappush(self.max_heap, (-price, timestamp))
        heapq.heappush(self.min_heap, (price, timestamp))

    def current(self) -> int:
        return self.prices[self.latest]

    def maximum(self) -> int:
        heap, prices = self.max_heap, self.prices
        while prices[heap[0][1]] != -heap[0][0]:
            heapq.heappop(heap)
        return -heap[0][0]

    def minimum(self) -> int:
        heap, prices = self.min_heap, self.prices
        while prices[heap[0][1]] != heap[0][0]:
            heapq.heappop(heap)
        return heap[0][0]


# ------------------------------------------------------------------------
# Alternatives / broken versions for the demos.
# ------------------------------------------------------------------------
class StockPriceScan:
    def __init__(self):
        self.prices: Dict[int, int] = {}
        self.latest = 0

    def update(self, timestamp: int, price: int) -> None:
        self.prices[timestamp] = price
        self.latest = max(self.latest, timestamp)

    def current(self) -> int:
        return self.prices[self.latest]

    def maximum(self) -> int:
        return max(self.prices.values())

    def minimum(self) -> int:
        return min(self.prices.values())


class StockPriceNoValidationBug(StockPrice):
    """Mistake 1: trusts the heap tops."""

    def maximum(self) -> int:
        return -self.max_heap[0][0]

    def minimum(self) -> int:
        return self.min_heap[0][0]


class StockPriceLastCallBug(StockPrice):
    """Mistake 2: 'current' = the most recent update call."""

    def update(self, timestamp: int, price: int) -> None:
        super().update(timestamp, price)
        self.last_call_price = price

    def current(self) -> int:
        return self.last_call_price


# ==============================================================================
# TESTS — run:  python 013_stock_price_fluctuation_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: lazy heaps vs scan ---")
    for cls in (StockPrice, StockPriceScan):
        sp = cls()
        sp.update(1, 10); sp.update(2, 5)
        got = [sp.current(), sp.maximum()]
        sp.update(1, 3)
        got.append(sp.maximum())
        sp.update(4, 2)
        got.append(sp.minimum())
        sp.update(4, 7)
        got += [sp.current(), sp.minimum(), sp.maximum()]
        ok = got == [5, 10, 5, 2, 7, 3, 7]
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {cls.__name__:<15} {got}")

    print("\n--- randomized cross-check (300 scripts, heavy corrections, out-of-order) ---")
    rng = random.Random(2034)
    bad = 0
    for _ in range(300):
        fast, slow = StockPrice(), StockPriceScan()
        have = False
        for _ in range(rng.randint(1, 120)):
            op = rng.random()
            if op < 0.5 or not have:
                t, p = rng.randint(1, 15), rng.randint(1, 20)
                fast.update(t, p); slow.update(t, p)
                have = True
            else:
                name = rng.choice(("current", "maximum", "minimum"))
                if getattr(fast, name)() != getattr(slow, name)():
                    bad += 1
                    break
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random scripts agree with the scanning oracle")

    print("\n--- mistakes LIVE ---")
    bug = StockPriceNoValidationBug()
    bug.update(1, 10); bug.update(2, 5); bug.update(1, 3)
    w = bug.maximum()
    ok = w == 10
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no validity check: after correcting 10 -> 3, maximum() = {w} (want 5)")
    bug2 = StockPriceLastCallBug()
    bug2.update(5, 100); bug2.update(2, 1)          # older timestamp arrives later
    w2 = bug2.current()
    good = StockPrice(); good.update(5, 100); good.update(2, 1)
    ok = w2 == 1 and good.current() == 100
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  current = last call: update(5,100), update(2,1) -> {w2} (want 100)")

    print("\n--- benchmark: 50,000 updates then 50,000 max/min queries ---")
    ops = [(rng.randint(1, 20_000), rng.randint(1, 10**9)) for _ in range(50_000)]
    for name, cls in (("scan values  ", StockPriceScan), ("lazy heaps   ", StockPrice)):
        sp = cls()
        t0 = time.perf_counter()
        for i, (t, p) in enumerate(ops):
            sp.update(t, p)
            if i % 2:
                sp.maximum()
                sp.minimum()
        dt = time.perf_counter() - t0
        print(f"      {name}  {dt * 1000:8.1f} ms")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
