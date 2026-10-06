"""
================================================================================
SOLUTION · LeetCode 295 · Find Median from Data Stream                  [Hard]
https://leetcode.com/problems/find-median-from-data-stream/
================================================================================

THE CORE IDEA
--------------
The median only cares about the boundary between the "lower half" and the
"upper half" of the data — it never needs the full sorted order. Split the
stream into two heaps that always straddle that boundary:

  - `lo`: a MAX-heap (negated) holding the smaller half.
  - `hi`: a MIN-heap holding the larger half.

Keep them balanced (`len(lo) == len(hi)` or `len(lo) == len(hi) + 1`) after
every insert. Then the median is always O(1) to read: `lo`'s root alone (odd
total) or the average of both roots (even total). See _TOPIC_GUIDE.md §5 for
the full derivation — this file focuses on the trace and the demo.

================================================================================
APPROACH 0 · Keep a sorted list, `bisect.insort` on every addNum (brute force, priced not coded)
================================================================================
Maintain the full stream in a sorted list. `addNum` inserts in sorted
position with `bisect.insort` — O(n) per insert because, although the
INSERTION POINT is found in O(log n) via binary search, shifting the
elements after it is O(n). `findMedian` is then O(1) (read the middle
index/indices). Correct, and `findMedian` is actually cheap here — the cost
is entirely in `addNum`, which degrades badly as the stream grows.

================================================================================
APPROACH 1 · Two heaps (max-heap of lower half + min-heap of upper half) ✅
================================================================================
    import heapq

    class MedianFinder:
        def __init__(self):
            self.lo = []   # max-heap (negated): smaller half
            self.hi = []   # min-heap: larger half

        def addNum(self, num):
            heapq.heappush(self.lo, -heapq.heappushpop(self.hi, num))
            if len(self.lo) > len(self.hi) + 1:
                heapq.heappush(self.hi, -heapq.heappop(self.lo))

        def findMedian(self):
            if len(self.lo) > len(self.hi):
                return float(-self.lo[0])
            return (-self.lo[0] + self.hi[0]) / 2.0

The `addNum` trick: ALWAYS route the new number through `hi` first
(`heappushpop` handles "push then pop the min" in one O(log n) sift), then
move `hi`'s new min over to `lo` (negated). This guarantees every value in
`lo` is <= every value in `hi` without a manual comparison branch — pushing
into the min-heap and immediately extracting its min is equivalent to
"insert num, then move whichever is currently smallest across the boundary
into lo," which is exactly the invariant we need. If that leaves `lo`
oversized by more than one, rebalance by moving `lo`'s max back to `hi`.

    Time:  addNum O(log n) (two heap ops). findMedian O(1).
    Space: O(n) total across both heaps.

================================================================================
APPROACH 2 · Variants worth naming
================================================================================
- A single sorted-container / order-statistics tree (e.g. a balanced BST
  augmented with subtree sizes) gives O(log n) `addNum` AND O(log n)
  arbitrary-rank queries (not just the median) — overkill here since we only
  ever need rank n/2, which two heaps answer with a simpler structure.
- The bounded-range follow-up mentioned in the question file (values in
  [0, 100]) can be solved with a COUNTING ARRAY of size 101 instead of
  heaps: O(1) addNum, O(100) findMedian (scan for the boundary) — trades an
  unbounded value range for constant extra work per query, a good answer
  to that specific follow-up.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — addNum(1), addNum(2), findMedian(), addNum(3), findMedian()
--------------------------------------------------------------------------------
Start: lo=[] (max-heap, negated), hi=[] (min-heap)

  addNum(1):
    heappushpop(hi, 1) -> hi was empty, so push 1 then immediately pop it
                           back out -> returns 1, hi stays []
    heappush(lo, -1) -> lo = [-1]   (i.e. lo holds {1})
    len(lo)=1, len(hi)=0 -> 1 <= 0+1, balanced, no rebalance needed.

  addNum(2):
    heappushpop(hi, 2) -> hi=[2] then pop min -> returns 2, hi becomes []
    heappush(lo, -2) -> lo = [-2, -1]   (lo holds {1, 2}, root -2 -> max is 2)
    len(lo)=2, len(hi)=0 -> 2 > 0+1 -> REBALANCE:
      heappush(hi, -heappop(lo)) -> pop lo's root -2 -> negate -> push 2 into hi
      lo = [-1] (holds {1}), hi = [2] (holds {2})

  findMedian(): len(lo)=1 == len(hi)=1 -> not len(lo) > len(hi) ->
    (-lo[0] + hi[0]) / 2.0 = (1 + 2) / 2.0 = 1.5   Matches expected: 1.5

  addNum(3):
    heappushpop(hi, 3) -> hi=[2] currently; push 3 -> hi=[2,3], pop min=2
                           -> returns 2, hi becomes [3]
    heappush(lo, -2) -> lo = [-2, -1]   (lo holds {1, 2})
    len(lo)=2, len(hi)=1 -> 2 <= 1+1, balanced, no rebalance needed.

  findMedian(): len(lo)=2 > len(hi)=1 -> return float(-lo[0]) = float(2) = 2.0
    Matches expected: 2.0

  Final state: lo holds {1,2} (the lower half), hi holds {3} (the upper
  half) — exactly straddling the true sorted order [1,2,3].

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                          | addNum          | findMedian | Space | Mutates input? |
|--------------------------------------|-----------------|------------|-------|-------------------|
| 0 · sorted list + bisect.insort       | O(n)            | O(1)       | O(n)  | N/A (owns its own state) |
| 1 · two heaps ✅                      | O(log n)        | O(1)       | O(n)  | N/A               |
| Bounded-range counting array (0-100)  | O(1)            | O(100)=O(1)| O(1)  | N/A               |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- First call ever: `addNum(x)` on empty heaps — `heappushpop(hi, x)` on an
  empty `hi` correctly returns `x` immediately (push then pop leaves it
  empty again), so `lo` ends up holding just `x`; no special-casing needed.
- All identical values, e.g. addNum(5) five times: heaps still balance
  correctly since ties compare fine (min-heap/max-heap don't need strict
  ordering); median stays 5.0 throughout.
- Negative numbers: negation for the max-heap (`lo`) works uniformly on
  negatives — `-(-3) == 3`, no sign-related special case.
- Two-element stream, e.g. [5, 15]: after balancing, lo={5}, hi={15},
  median = (5+15)/2 = 10.0 — exercises the even-count averaging branch.
- Strictly increasing / strictly decreasing insert order: the rebalancing
  step (moving the max of `lo` to `hi` or vice versa) handles both without
  degrading — the heap invariant doesn't care about insertion order, unlike
  an unbalanced BST (see _TOPIC_GUIDE.md §4's comparison table).

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Forgetting to negate values going into `lo` (the max-heap simulated via
   `heapq`, see _TOPIC_GUIDE.md §2.1) — or negating on the way in but
   forgetting to negate back when reading `lo[0]` in `findMedian`, silently
   returning the wrong sign / wrong value.
2. Routing the new number DIRECTLY into `lo` or `hi` based on a manual
   `if num < median` comparison instead of the `heappushpop`-through-`hi`
   trick — a manual comparison against a STALE median (computed before this
   insert) can misroute the boundary, especially on the very first few
   inserts before a stable median exists; the fused approach sidesteps
   needing to know the median at all during insert.
3. Letting the size imbalance grow past 1 — only ever checking `len(lo) >
   len(hi)` without capping the difference at exactly 1 breaks the O(1)
   `findMedian` read, since `findMedian` assumes the imbalance is AT MOST
   one element.
4. Off-by-one in `findMedian`'s odd/even branch — using `>=` instead of `>`
   when comparing `len(lo)` and `len(hi)` can double-count or read from the
   wrong heap when the two are exactly equal.
5. Using `heappush` + separate `heappop` (two O(log n) calls) instead of
   the fused `heappushpop`/`heapreplace` — still O(log n) each so same
   asymptotic complexity, but doubles the constant-factor heap-sift work
   per insert; the fused calls do the equivalent job in one sift (see
   _TOPIC_GUIDE.md §2.2).

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "If all integers in the stream are in the range [0, 100], how would you
  optimize?" — use a fixed-size counting array of length 101 instead of
  heaps: O(1) `addNum` (increment a bucket), O(100) `findMedian` (scan
  buckets to find the middle rank(s)) — both effectively O(1) since 101 is
  a constant, and the space drops to O(1) instead of O(n).
- "If 99% of integers are in [0, 100] but the rest can be anything?" —
  hybrid: a counting array for the common range plus the two-heap structure
  (or even a plain sorted overflow list, since it's rare) for the outliers,
  routing each `addNum` to whichever structure covers its value.
- "How would you support REMOVING a value from the stream?" — plain
  `heapq` has no O(log n) arbitrary delete; needs lazy deletion (a
  tombstone/count map checked when a heap's root is read, discarding stale
  entries) — see _TOPIC_GUIDE.md's broader note on this limitation.
- "What if you need percentiles other than the 50th (median)?" — generalize
  to an order-statistics structure (e.g. a Fenwick tree over value ranks, or
  a skip list with rank queries) — two heaps are specialized to exactly the
  50/50 split and don't generalize cleanly to arbitrary percentiles.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/001 Kth Largest Element in a Stream — single size-k heap tracking one
  moving boundary; this problem generalizes to TWO heaps tracking a
  50/50 boundary.
- 12/010 Minimum Interval to Include Each Query — a different heap-over-
  a-stream pattern (queries against currently-active intervals).
- LC 4 Median of Two Sorted Arrays — a related "find the median" problem
  solved with binary search instead, because there the two inputs are
  already fully sorted and static (no streaming insert to support).
================================================================================
"""

import heapq
import bisect
import random
import time


class MedianFinder:
    def __init__(self):
        self.lo: list = []   # max-heap (negated): holds the smaller half
        self.hi: list = []   # min-heap: holds the larger half

    def addNum(self, num: int) -> None:
        heapq.heappush(self.lo, -heapq.heappushpop(self.hi, num))
        if len(self.lo) > len(self.hi) + 1:
            heapq.heappush(self.hi, -heapq.heappop(self.lo))

    def findMedian(self) -> float:
        if len(self.lo) > len(self.hi):
            return float(-self.lo[0])
        return (-self.lo[0] + self.hi[0]) / 2.0


# --------------------------------------------------------------------------
# Baseline for the runtime demo: sorted list + bisect.insort on every addNum.
# --------------------------------------------------------------------------
class MedianFinderSorted:
    def __init__(self):
        self.data: list = []

    def addNum(self, num: int) -> None:
        bisect.insort(self.data, num)

    def findMedian(self) -> float:
        n = len(self.data)
        mid = n // 2
        if n % 2 == 1:
            return float(self.data[mid])
        return (self.data[mid - 1] + self.data[mid]) / 2.0


def run_tests():
    mf = MedianFinder()
    mf.addNum(1)
    mf.addNum(2)
    assert mf.findMedian() == 1.5
    mf.addNum(3)
    assert mf.findMedian() == 2.0

    mf2 = MedianFinder()
    for n in [5, 15, 1, 3]:
        mf2.addNum(n)
    assert mf2.findMedian() == 4.0

    mf3 = MedianFinder()
    mf3.addNum(-1)
    assert mf3.findMedian() == -1.0
    mf3.addNum(-2)
    assert mf3.findMedian() == -1.5
    mf3.addNum(-3)
    assert mf3.findMedian() == -2.0

    # all identical values
    mf4 = MedianFinder()
    for _ in range(5):
        mf4.addNum(7)
    assert mf4.findMedian() == 7.0

    # cross-check against the sorted-list baseline on a long randomized stream
    random.seed(1)
    fast, slow = MedianFinder(), MedianFinderSorted()
    for _ in range(2000):
        x = random.randint(-10**5, 10**5)
        fast.addNum(x)
        slow.addNum(x)
        assert fast.findMedian() == slow.findMedian()

    # --- measured runtime demo: two-heap addNum vs bisect.insort addNum ---
    random.seed(42)
    n_adds = 20_000
    values = [random.randint(-10**6, 10**6) for _ in range(n_adds)]

    fast2 = MedianFinder()
    t0 = time.perf_counter()
    for v in values:
        fast2.addNum(v)
    fast_time = time.perf_counter() - t0

    slow2 = MedianFinderSorted()
    t0 = time.perf_counter()
    for v in values:
        slow2.addNum(v)
    slow_time = time.perf_counter() - t0

    assert fast2.findMedian() == slow2.findMedian()

    print(f"n_adds={n_adds} (this machine, CPython):")
    print(f"  two heaps addNum:        {fast_time*1000:8.2f} ms total")
    print(f"  bisect.insort addNum:    {slow_time*1000:8.2f} ms total")
    print(f"  two heaps is {slow_time / fast_time:.1f}x faster over the whole stream")
    assert fast_time < slow_time, (
        "expected the O(log n)-per-insert two-heap approach to beat "
        "O(n)-per-insert bisect.insort over a long stream"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
