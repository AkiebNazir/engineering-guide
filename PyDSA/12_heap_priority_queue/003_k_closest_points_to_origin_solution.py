"""
================================================================================
SOLUTION · LeetCode 973 · K Closest Points to Origin                  [Medium]
https://leetcode.com/problems/k-closest-points-to-origin/
================================================================================

THE CORE IDEA
--------------
This is the exact top-k-heap pattern from _TOPIC_GUIDE.md §3, keyed by a
DERIVED value (squared distance) instead of the raw element. Two extra
wrinkles versus problem 004's plain-number version:

  1. Never call `sqrt` — comparing squared distances gives the same ordering
     (all distances are non-negative, and x -> x^2 is monotonic on [0, inf)),
     so `sqrt` is pure wasted floating-point work done once per point for no
     benefit.
  2. `points[i]` is a `list`, which has NO `__lt__` defined against another
     list of the same length in a way that matters here (lists DO compare
     lexicographically, but that's a distraction, not the ordering we want)
     — worse, heap tuples `(dist, point)` will try to compare `point`s
     directly the instant two distances tie, and if `point` were something
     truly incomparable (e.g. a dict) that would raise `TypeError`. The
     guide's Common Mistake #3 applies directly: always carry a cheap,
     totally-ordered tiebreaker (the original index) as the *second* tuple
     slot so ties never reach the point itself.

================================================================================
APPROACH 0 · Sort everything by distance (brute force, priced not coded)
================================================================================
Compute distance for every point, sort ascending, take the first k.
    Time:  O(n log n) for the sort.
    Space: O(n) for the sorted copy.
Correct and simple; wasteful because it fully orders all n points when we
only need a boundary at rank k.

================================================================================
APPROACH 1 · Max-heap of size k ✅ (the answer, coded below)
================================================================================
Maintain a max-heap capped at k holding the k closest points seen so far,
keyed by NEGATIVE squared distance so the heap's root is the FARTHEST of the
current top-k (heapq is min-heap only — negate to simulate max, see guide
§2.1). For each point: push if the heap has room; otherwise, if this point
is closer than the current farthest kept point, evict the root and admit it.

    Time:  O(n log k) — n points, O(log k) per heap operation.
    Space: O(k) for the heap.

================================================================================
APPROACH 2 · heapq.nsmallest with a key function
================================================================================
`heapq.nsmallest(k, points, key=lambda p: p[0]**2 + p[1]**2)` does exactly
Approach 1 internally (maintains a size-k heap while sweeping the iterable),
written in C, with no manual negation needed because `nsmallest` handles the
"smallest k" framing directly without a max-heap trick. Convenient, same
O(n log k) asymptotics, faster constant factor — but the point of this file
is to build the size-k-heap mechanism by hand.

================================================================================
APPROACH 3 · Quickselect on squared distance
================================================================================
Same idea as problem 004's `findKthLargest_quickselect`, but partitioning by
squared distance and returning everything with rank < k after partitioning
around the kth position. O(n) average, O(n^2) worst case (mitigated by a
random pivot). Better than the heap when k is a large FRACTION of n (say
k > n/2), since O(n) average beats O(n log k) once log k approaches log n;
worse when k is small, where O(n log k)'s constant is tiny.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — points = [[3,3],[5,-1],[-2,4]], k = 2 (max-heap approach)
--------------------------------------------------------------------------------
Squared distances: (3,3)->18   (5,-1)->26   (-2,4)->20

  Start: heap = [] (capacity 2)

  i=0, p=(3,3), d2=18: heap not full -> push (-18, 0, (3,3))
       heap: [(-18, 0, (3,3))]

  i=1, p=(5,-1), d2=26: heap not full -> push (-26, 1, (5,-1))
       heap (min-heap array by first element): [(-26,1,(5,-1)), (-18,0,(3,3))]
       root = (-26, ...) -> the CURRENT farthest of the kept set is (5,-1)
       (since -26 < -18, i.e. 26 > 18 in real distance)

  i=2, p=(-2,4), d2=20: heap FULL (size 2). Compare 20 vs root's real
       distance 26 -> 20 < 26, this point is CLOSER than the current
       farthest kept point -> heapreplace: pop (-26,1,(5,-1)), push
       (-20, 2, (-2,4)).
       heap now holds negated-distance entries for (3,3) [d2=18] and
       (-2,4) [d2=20] -> these ARE the 2 closest points.

  End: extract points from heap -> {(3,3), (-2,4)}. Matches expected output
  (order doesn't matter per the problem statement).

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                         | Time            | Space | Mutates input `points`? |
|------------------------------------|-----------------|-------|----------------------------|
| 0 · sort by distance (brute)       | O(n log n)      | O(n)  | No (sorted() copies)     |
| 1 · max-heap of size k ✅          | O(n log k)      | O(k)  | No                       |
| 2 · heapq.nsmallest(key=...)       | O(n log k)      | O(k)  | No                       |
| 3 · quickselect on squared dist    | O(n) average    | O(n)  | No — copies before partition |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- k == len(points): every point is kept; heap grows to size n, still correct
  (just no rejections ever happen).
- k == 1: heap of size 1 — degenerates to "closest single point," equivalent
  to a running-min scan.
- Duplicate points (same coordinates): squared distances tie exactly; the
  index tiebreaker in the tuple resolves the comparison deterministically
  without ever touching the point itself, so no `TypeError` — see the Common
  Mistake this file's tuple shape specifically avoids.
- Points forming a perfect symmetric ring (e.g. (1,0),(0,1),(-1,0),(0,-1),
  all distance 1 from origin) with k == len(points): all four must be kept;
  covered explicitly in the test cases below.
- Negative coordinates: squaring makes sign irrelevant automatically — no
  special-casing needed, `x*x` and `x**2` both fold sign away.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Calling `math.sqrt` when computing distance for comparison purposes —
   monotonic transforms preserve ordering, so squared distance sorts
   identically to true distance and skips a `sqrt` call per point for free.
2. Pushing `(dist, point)` tuples without an index tiebreaker — the instant
   two points tie on distance, Python falls through to comparing `point`
   (a `list`), which works today (lists ARE comparable) but is fragile: if
   the payload were ever a `dict`, a custom object, or any two points
   compared with an ambiguous partial order, this raises `TypeError` at
   runtime on a tie. Always carry `(dist, idx, point)`.
3. Using a MIN-heap of ALL n points and popping k times without negation —
   a plain min-heap of squared distances gives you the k SMALLEST distances
   correctly if you just heapify all n and pop k times (O(n + k log n)) —
   that's actually fine and arguably simpler than the negated max-heap; the
   mistake is combining the two ideas incorrectly, e.g. negating when you
   didn't need to, or forgetting to negate when you built a max-heap
   variant on purpose to keep only k in memory (Approach 1 needs the
   negation specifically because it bounds memory to O(k), not O(n)).
4. Off-by-one / wrong direction on "closest" vs "farthest" when deciding the
   eviction condition — Approach 1's heap root represents the FARTHEST of
   the currently-kept top-k (that's the one candidate for eviction), not
   the closest; getting this backwards silently keeps the k FARTHEST points
   instead of the k closest.
5. Returning distances instead of points, or converting points to tuples in
   the output when the caller expects lists (LeetCode's harness typically
   accepts either, but a strict-list contract elsewhere might not).

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if points arrive as a live stream and k is fixed?" — Approach 1
  generalizes directly (same shape as problem 001); Approach 0 and 3 do not,
  since they need the whole array up front.
- "What if the distance metric changes (Manhattan instead of Euclidean)?"
  — only the key function changes (`abs(x) + abs(y)` instead of `x*x+y*y`);
  the heap mechanism is metric-agnostic as long as the metric is
  computable per-point and totally ordered.
- "Can you avoid floating point entirely?" — yes, squared distance for
  integer coordinates is itself an integer; this solution already never
  touches a float.
- "What if k is very large (close to n) and this runs in a memory-
  constrained environment?" — quickselect (Approach 3) uses O(n) but no
  extra heap bookkeeping, and can be done truly in-place on the input array
  if mutating it is acceptable, avoiding the O(k) extra heap allocation.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 12/004 Kth Largest Element in an Array — same size-k min/max-heap pattern
  on a raw value instead of a derived distance key.
- 12/001 Kth Largest Element in a Stream — same pattern, but must persist
  across repeated live inserts instead of a one-shot batch call.
- LC 347 Top K Frequent Elements (topic 01) — top-k by a derived frequency
  key instead of a derived distance key; same heap-of-size-k shape.
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def kClosest(self, points: List[List[int]], k: int) -> List[List[int]]:
        # Max-heap of size k on negative squared distance, with an index
        # tiebreaker so tied distances never fall back to comparing `point`
        # (a list) directly.
        heap: List[tuple] = []
        for i, (x, y) in enumerate(points):
            d2 = x * x + y * y
            if len(heap) < k:
                heapq.heappush(heap, (-d2, i, [x, y]))
            elif -d2 > heap[0][0]:          # d2 < current farthest kept distance
                heapq.heapreplace(heap, (-d2, i, [x, y]))
        return [point for _, _, point in heap]

    def kClosest_nsmallest(self, points: List[List[int]], k: int) -> List[List[int]]:
        # Alternative: let the stdlib do the size-k-heap sweep internally.
        return heapq.nsmallest(k, points, key=lambda p: p[0] ** 2 + p[1] ** 2)

    def kClosest_quickselect(self, points: List[List[int]], k: int) -> List[List[int]]:
        # Alternative: quickselect by squared distance, O(n) average.
        pts = [p[:] for p in points]          # never mutate caller's points

        def d2(p):
            return p[0] * p[0] + p[1] * p[1]

        def partition(lo, hi):
            pivot_idx = random.randint(lo, hi)
            pivot = d2(pts[pivot_idx])
            lt, gt, i = lo, hi, lo
            while i <= gt:
                if d2(pts[i]) < pivot:
                    pts[lt], pts[i] = pts[i], pts[lt]
                    lt += 1
                    i += 1
                elif d2(pts[i]) > pivot:
                    pts[gt], pts[i] = pts[i], pts[gt]
                    gt -= 1
                else:
                    i += 1
            return lt, gt

        lo, hi = 0, len(pts) - 1
        target = k - 1  # we want everything with rank < k, i.e. indices [0, k-1]
        while True:
            lt, gt = partition(lo, hi)
            if target < lt:
                hi = lt - 1
            elif target > gt:
                lo = gt + 1
            else:
                break
        return pts[:k]


def run_tests():
    sol = Solution()

    def as_set(pts):
        return {tuple(p) for p in pts}

    cases = [
        ([[1, 3], [-2, 2]], 1, {(-2, 2)}),
        ([[3, 3], [5, -1], [-2, 4]], 2, {(3, 3), (-2, 4)}),
        ([[0, 1]], 1, {(0, 1)}),
        ([[1, 0], [0, 1], [-1, 0], [0, -1]], 4, {(1, 0), (0, 1), (-1, 0), (0, -1)}),
    ]
    for points, k, expected in cases:
        assert as_set(sol.kClosest([p[:] for p in points], k)) == expected
        assert as_set(sol.kClosest_nsmallest([p[:] for p in points], k)) == expected
        assert as_set(sol.kClosest_quickselect([p[:] for p in points], k)) == expected

    # tie-breaking: duplicate points must not raise TypeError
    dup_points = [[1, 1], [1, 1], [2, 2]]
    result = sol.kClosest(dup_points, 2)
    assert as_set(result) == {(1, 1), (1, 1)} or as_set(result) == {(1, 1), (2, 2)}
    assert len(result) == 2

    # input not mutated
    original = [[3, 3], [5, -1], [-2, 4]]
    snapshot = [p[:] for p in original]
    sol.kClosest(original, 2)
    assert original == snapshot, "kClosest must not mutate its input"

    # --- measured runtime demo: sort-all vs size-k max-heap ---
    def sort_based(points, k):
        return sorted(points, key=lambda p: p[0] ** 2 + p[1] ** 2)[:k]

    random.seed(42)
    n = 200_000
    k = 20
    data = [[random.randint(-10**4, 10**4), random.randint(-10**4, 10**4)] for _ in range(n)]

    t0 = time.perf_counter()
    heap_result = sol.kClosest(data, k)
    heap_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    sort_result = sort_based(data, k)
    sort_time = time.perf_counter() - t0

    assert as_set(heap_result) == as_set(sort_result), "both approaches must agree"

    print(f"n={n} points, k={k} (this machine, CPython):")
    print(f"  size-k max-heap:  {heap_time*1000:8.2f} ms")
    print(f"  sort all by dist: {sort_time*1000:8.2f} ms")
    print(f"  heap is {sort_time / heap_time:.1f}x faster")
    assert heap_time < sort_time, (
        "expected the size-k heap to beat sorting all n points when k << n"
    )

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
