"""
================================================================================
SOLUTION · LeetCode 1851 · Minimum Interval to Include Each Query       [Hard]
https://leetcode.com/problems/minimum-interval-to-include-each-query/
================================================================================

THE CORE IDEA
--------------
Answer queries in SORTED order and maintain a min-heap of "currently active"
intervals (those whose `left <= current query`), keyed by SIZE. As the query
value grows, admit any newly-eligible intervals into the heap, and lazily
discard heap entries whose `right < current query` (they've expired — they
no longer contain this or any future, larger query). The heap's root after
that cleanup is the smallest surviving active interval — exactly the
answer. This is the same "sort + min-heap of currently relevant candidates,
advanced by a pointer" shape as problem 008 (Single-Threaded CPU), with an
added LAZY DELETION step (see _TOPIC_GUIDE.md's cross-cutting note on
`heapq` having no O(log n) arbitrary delete).

Answering queries OUT of their original order (sorted by value) is safe
because each query's answer only depends on which intervals contain it —
never on other queries — so we just remember, per query, where in the
original array to write the answer.

================================================================================
APPROACH 0 · For each query, scan all intervals (brute force, priced not coded)
================================================================================
For every query, linearly scan all intervals, keep the smallest one whose
`[left, right]` contains it.
    Time:  O(q * n) — q queries times n intervals each.
    Space: O(1) extra.
With q, n up to 10^5 each, O(q*n) is up to 10^10 — far too slow. Correct,
trivially simple, the canonical "obviously right, obviously too slow" start.

================================================================================
APPROACH 1 · Sort both + min-heap of active intervals by size ✅ (the answer)
================================================================================
  1. Sort `intervals` by `left`.
  2. Sort query INDICES by query VALUE (need to answer in ascending query
     order but must report answers back in the ORIGINAL query order).
  3. Sweep query values ascending. For each query `q`:
     a. Push every interval whose `left <= q` into a min-heap keyed by
        `(size, right)` — advance a pointer through the left-sorted
        intervals, don't rescan from the start each time.
     b. Pop (lazily discard) any heap-top interval whose `right < q` — it
        can never contain this query or any LARGER query that comes later
        in the sweep, so it's safe to throw away permanently, not just skip.
     c. The heap's new top (if any) is the smallest interval that still
        contains `q` — record its size as the answer for this query's
        ORIGINAL position; record -1 if the heap is empty.

    Time:  O((n + q) log n) — each interval is pushed once and popped at
           most once (amortized across the whole sweep, not per query); each
           query does O(log n) heap work for its own lazy-pop cleanup.
    Space: O(n) for the heap + O(q) for the answer array and sorted index.

================================================================================
APPROACH 2 · Variants worth naming
================================================================================
- Coordinate-compressed segment tree / Fenwick tree over interval sizes can
  answer this with a similar O((n+q) log n) bound via a different
  mechanism (offline range-min queries) — more machinery, same complexity
  class; the heap version is simpler to implement correctly under time
  pressure.
- Answering queries in their ORIGINAL order with a persistent/interval
  structure (e.g. a balanced BST keyed by interval size, removing expired
  intervals as you go) is equivalent in spirit to Approach 1 but usually
  more code for the same asymptotics — a heap is the natural fit because we
  only ever need the CURRENT minimum, never arbitrary-rank queries.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — intervals=[[1,4],[2,4],[3,6],[4,4]], queries=[2,3,4,5]
--------------------------------------------------------------------------------
Sizes: [1,4]->4  [2,4]->3  [3,6]->4  [4,4]->1
Sort intervals by left (already sorted): (1,4,sz4) (2,4,sz3) (3,6,sz4) (4,4,sz1)
Sort query indices by value: all already ascending -> order = [0,1,2,3]
                              (queries[0]=2, [1]=3, [2]=4, [3]=5)

  q=2 (orig idx 0): admit intervals with left<=2 -> push (4,4)[sz,right] for
    [1,4], push (3,4) for [2,4]. heap={(3,4),(4,4)} root=(3,4).
    lazy-pop check: root's right=4 >= 2, keep. answer[0] = 3.

  q=3 (orig idx 1): admit intervals with left<=3 -> push (4,6) for [3,6].
    heap={(3,4),(4,4),(4,6)} root still (3,4).
    lazy-pop check: right=4 >= 3, keep. answer[1] = 3.

  q=4 (orig idx 2): admit intervals with left<=4 -> push (1,4) for [4,4].
    heap={(1,4),(3,4),(4,4),(4,6)} root=(1,4).
    lazy-pop check: right=4 >= 4, keep. answer[2] = 1.

  q=5 (orig idx 3): no new intervals to admit (all already pushed).
    lazy-pop check: root=(1,4), right=4 < 5 -> EXPIRED, pop it.
      next root=(3,4), right=4 < 5 -> EXPIRED, pop it.
      next root=(4,4) [this is interval [1,4]], right=4 < 5 -> EXPIRED, pop.
      next root=(4,6) [interval [3,6]], right=6 >= 5 -> keep.
    answer[3] = 4.

  Final answers in original order: [3, 3, 1, 4]. Matches expected output.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                                  | Time                | Space | Mutates input? |
|----------------------------------------------|---------------------|-------|--------------------|
| 0 · scan all intervals per query (brute)      | O(q * n)            | O(1)  | No                 |
| 1 · sort + min-heap w/ lazy deletion ✅       | O((n + q) log n)    | O(n+q)| No — sorts copies of index lists |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Query with no containing interval at all: heap ends up empty after lazy
  cleanup (or never received any eligible interval) -> answer -1 (see
  `queries=[19]` in the question file's second example).
- Query exactly equal to an interval's `left` or `right`: inclusive bounds
  (`left <= q <= right`), so admission uses `<=` and the lazy-expiry check
  uses `right < q` (strict) — an interval whose right EQUALS the query is
  still valid and must NOT be expired.
- Single-point interval, e.g. `[4,4]` (size 1): correctly the smallest
  possible answer whenever a query lands exactly on it.
- Duplicate intervals (same left/right): heap handles duplicates fine
  (no uniqueness assumption); both entries admitted and independently
  expired at the same time, harmless redundancy.
- Query values not sorted in the input, and queries containing duplicates:
  the original-index bookkeeping (`sorted(range(q), key=lambda i:
  queries[i])`) must handle repeated query VALUES correctly (each original
  index still gets its own answer slot, even if two indices share a value
  and thus get the same answer independently).

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Forgetting to write answers back to the ORIGINAL query positions after
   sorting query values for the sweep — the sweep must process queries in
   ascending VALUE order (for correctness of the pointer + lazy-expiry
   logic) but the RETURNED array must be in original input order; mixing
   these up silently misassigns every answer.
2. Using EAGER deletion (scanning the whole heap to remove expired
   intervals every query) instead of LAZY deletion (only popping from the
   TOP when it's expired, and only when this specific query needs a fresh
   read) — eager deletion needs O(n) heap rebuilding, since `heapq` has no
   O(log n) arbitrary-position delete; lazy deletion exploits the fact that
   query values only ever INCREASE during the sweep, so any interval popped
   for being too small a `right` is correctly gone forever, not just for
   this query.
3. Off-by-one on interval admission (`left <= q` vs `left < q`) or on
   expiry (`right < q` vs `right <= q`) — both bounds in this problem are
   INCLUSIVE, so getting either comparison's strictness backwards either
   drops a valid interval or keeps an invalid one.
4. Pushing `(size, left, right)` or similar without confirming the tuple's
   FIRST element is what should drive the min-heap ordering — if `left` or
   `right` accidentally sorts before `size` in the tuple, the heap
   optimizes for the wrong quantity entirely (smallest `left`/`right`
   instead of smallest interval SIZE).
5. Re-scanning intervals from the start of the `left`-sorted array on every
   query instead of advancing a single shared pointer — still technically
   correct but reintroduces an O(n) per-query cost, defeating the whole
   point of the amortized single pass.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if intervals or queries arrive as a live stream (can't pre-sort)?"
  — queries can no longer be safely reordered for the sweep; you'd need an
  online interval-containment structure (e.g. a balanced BST or segment
  tree over the value range) instead of the offline sort-both-then-sweep
  trick this solution relies on.
- "What if you need the interval ITSELF, not just its size?" — trivial
  extension: carry the full `[left, right]` (or an index into `intervals`)
  as extra heap payload alongside `(size, right)`.
- "What if intervals can be added/removed dynamically between queries?" —
  breaks the offline sort assumption; would need a dynamic order-statistics
  structure supporting insert/delete/min-by-size, e.g. a balanced BST keyed
  by size with left/right stored per node.
- "Can you avoid the extra O(n) space for the heap?" — not while keeping
  O((n+q) log n) time; you could trade toward O(q*n) with less memory by
  going back to Approach 0's brute scan, but that's rarely the right trade
  at this problem's scale.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/008 Single-Threaded CPU — same "sort + min-heap of currently eligible
  candidates, advanced by a shared pointer" sweep shape.
- 12/009 Find Median from Data Stream — a different application of lazy
  heap bookkeeping (there, size-balance invariant; here, expiry-by-value).
- LC 253 Meeting Rooms II (topic 19, Intervals) — another sort + heap
  sweep over interval boundaries, tracking overlap count instead of a
  per-query containment answer.
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def minInterval(self, intervals: List[List[int]], queries: List[int]) -> List[int]:
        intervals_sorted = sorted(intervals, key=lambda iv: iv[0])
        query_order = sorted(range(len(queries)), key=lambda i: queries[i])

        answers = [-1] * len(queries)
        heap: List[tuple] = []   # (size, right)
        i = 0
        n = len(intervals_sorted)

        for qi in query_order:
            q = queries[qi]
            while i < n and intervals_sorted[i][0] <= q:
                left, right = intervals_sorted[i]
                heapq.heappush(heap, (right - left + 1, right))
                i += 1

            while heap and heap[0][1] < q:
                heapq.heappop(heap)

            if heap:
                answers[qi] = heap[0][0]

        return answers


# --------------------------------------------------------------------------
# Baseline for the runtime demo: scan every interval for every query.
# --------------------------------------------------------------------------
class SolutionBruteForce:
    def minInterval(self, intervals: List[List[int]], queries: List[int]) -> List[int]:
        answers = []
        for q in queries:
            best = -1
            for left, right in intervals:
                if left <= q <= right:
                    size = right - left + 1
                    if best == -1 or size < best:
                        best = size
            answers.append(best)
        return answers


def run_tests():
    sol = Solution()

    assert sol.minInterval([[1, 4], [2, 4], [3, 6], [4, 4]], [2, 3, 4, 5]) == [3, 3, 1, 4]
    assert sol.minInterval([[2, 3], [2, 5], [1, 8], [20, 25]], [2, 19, 5, 22]) == [2, -1, 4, 6]
    assert sol.minInterval([[1, 1]], [1]) == [1]
    assert sol.minInterval([[1, 5]], [10]) == [-1]

    # queries not sorted, with duplicates
    assert sol.minInterval([[1, 4], [2, 4], [3, 6], [4, 4]], [5, 4, 4, 2]) == [4, 1, 1, 3]

    # input not mutated
    original_iv = [[1, 4], [2, 4], [3, 6], [4, 4]]
    original_q = [2, 3, 4, 5]
    snap_iv = [row[:] for row in original_iv]
    snap_q = original_q[:]
    sol.minInterval(original_iv, original_q)
    assert original_iv == snap_iv, "minInterval must not mutate intervals"
    assert original_q == snap_q, "minInterval must not mutate queries"

    # cross-check against brute force on randomized inputs
    random.seed(13)
    brute = SolutionBruteForce()
    for _ in range(150):
        n = random.randint(1, 15)
        intervals = []
        for _ in range(n):
            a = random.randint(1, 30)
            b = random.randint(a, 30)
            intervals.append([a, b])
        queries = [random.randint(1, 30) for _ in range(random.randint(1, 15))]
        assert sol.minInterval([iv[:] for iv in intervals], queries[:]) == brute.minInterval(
            [iv[:] for iv in intervals], queries[:]
        )

    # --- measured runtime demo: sort+heap sweep vs brute scan ---
    random.seed(42)
    n_intervals = 5000
    n_queries = 5000
    intervals = []
    for _ in range(n_intervals):
        a = random.randint(1, 10**6)
        b = a + random.randint(0, 10**4)
        intervals.append([a, b])
    queries = [random.randint(1, 10**6) for _ in range(n_queries)]

    t0 = time.perf_counter()
    fast_result = sol.minInterval(intervals, queries)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = brute.minInterval(intervals, queries)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result, "both approaches must agree"

    print(f"n_intervals={n_intervals}, n_queries={n_queries} (this machine, CPython):")
    print(f"  sort + min-heap sweep:  {fast_time*1000:8.2f} ms")
    print(f"  brute force (n*q scan): {slow_time*1000:8.2f} ms")
    print(f"  heap sweep is {slow_time / fast_time:.0f}x faster")
    assert fast_time < slow_time, (
        "expected the O((n+q) log n) heap sweep to crush the O(n*q) brute scan"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
