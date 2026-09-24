"""
================================================================================
SOLUTION · LeetCode 1094 · Car Pooling                                [Medium]
https://leetcode.com/problems/car-pooling/
================================================================================

THE CORE IDEA
--------------
This is Meeting Rooms II's "peak concurrent count" question (005), but
WEIGHTED — each trip doesn't occupy "1 room," it occupies `numPassengers`
seats. The min-heap sweep from 005 still works (push/pop weighted
occupancy instead of a bare count). But because the coordinate range here
is small and BOUNDED (`0 <= from, to <= 1000` per the constraints), there's
a strictly simpler and faster tool: a **difference array over pickup/dropoff
events**. At each location, passengers get ON (`+numPassengers` at `from`)
or OFF (`-numPassengers` at `to`); a prefix sum over that difference array
at every location IS the number of passengers in the car at that instant.
If the running total ever exceeds `capacity`, the trip plan is infeasible.

================================================================================
APPROACH 0 · Brute-force per-kilometer simulation (priced, not coded)
================================================================================
For each of the up to 1000 locations, sum `numPassengers` over every trip
whose `[from, to)` range covers that location, and check against capacity.
O(1000 * len(trips)) = O(V * n). Correct (V=1000 is small enough this would
even pass), but re-scans all trips at every location instead of processing
each trip's boundary just twice.

================================================================================
APPROACH 1 · Difference array over pickup/dropoff events ✅ (the answer)
================================================================================
    def carPooling(trips, capacity):
        diff = [0] * 1001                     # bounded coordinate range
        for passengers, start, end in trips:
            diff[start] += passengers          # passenger(s) get ON here
            diff[end] -= passengers            # passenger(s) get OFF here
        occupancy = 0
        for delta in diff:
            occupancy += delta
            if occupancy > capacity:
                return False
        return True

Time:  O(n + V) where n = len(trips), V = the bounded coordinate range
       (1001 here) — no sort needed at all, since array indices ARE the
       sorted order (a counting-sort-like trick).
Space: O(V) for the difference array.

Why `diff[end] -= passengers` and not `diff[end - 1]`: dropoff at `to`
means the passenger is OUT of the car starting exactly at kilometer `to` —
touching trips `[1,5]` and `[5,7]` do NOT overlap (the passenger from the
first trip is already dropped off by the time the second trip's pickup
happens at the same point), matching the non-strict "touching is not a
conflict" rule this array formulation encodes for free.

================================================================================
APPROACH 2 · Sort by start, min-heap of (end, passengers) — general variant
================================================================================
Exactly 005 Meeting Rooms II's sweep, generalized to weighted occupancy:
    def carPooling(trips, capacity):
        trips = sorted(trips, key=lambda t: t[1])
        heap = []                              # (end, passengers) min-heap by end
        occupancy = 0
        for passengers, start, end in trips:
            while heap and heap[0][0] <= start:
                _, p = heapq.heappop(heap)
                occupancy -= p
            occupancy += passengers
            if occupancy > capacity:
                return False
            heapq.heappush(heap, (end, passengers))
        return True

Time:  O(n log n) — needed when coordinates are NOT small/bounded (e.g. up
       to 10^9), where a difference array of that size would be infeasible.
Space: O(n) for the heap.

**When to use which**: bounded, small integer coordinates -> difference
array (Approach 1, faster and simpler). Arbitrary/large or non-integer
coordinates, or a need to know WHICH resource (trip) is occupying a seat,
not just the count -> the heap sweep (Approach 2). This exact trade-off is
called out as an interviewer follow-up in `_TOPIC_GUIDE.md` §3.

--------------------------------------------------------------------------------
STEP BY STEP TRACE — trips = [[2,1,5],[3,3,7]], capacity = 4
--------------------------------------------------------------------------------
Number line (passenger counts as weight, not just presence):
     1        3        5        7
     [2 pax.......5)
              [3 pax............7)

diff array (only nonzero entries shown, index = location):
  diff[1] += 2   -> diff[1] = 2
  diff[5] -= 2   -> diff[5] = -2
  diff[3] += 3   -> diff[3] = 3
  diff[7] -= 3   -> diff[7] = -3

Prefix sweep (occupancy after each location):
  loc 0: +0  -> occupancy=0
  loc 1: +2  -> occupancy=2   (2 <= 4, ok)
  loc 2: +0  -> occupancy=2
  loc 3: +3  -> occupancy=5   (5 > 4 !!)  -> return False immediately

Result: False — matches expected output; at kilometer 3, both trips are
active simultaneously (2+3=5 passengers), exceeding capacity=4.

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                              | Time        | Space | Mutates input? |
|-------------------------------------------|------------|-------|-------------------|
| 0 · brute-force per-kilometer (brute)     | O(V*n)     | O(V)  | No               |
| 1 · difference array over events ✅       | O(n+V)     | O(V)  | No               |
| 2 · sort + min-heap (weighted 005) variant| O(n log n) | O(n)  | No (`sorted()` copy) |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- Single trip exactly at capacity, e.g. `[[10,0,1]], capacity=10` — occupancy
  hits exactly 10, `10 > 10` is False -> True (capacity is inclusive, not a
  strict upper bound).
- Single trip one passenger over, e.g. `[[10,0,1]], capacity=9` -> False.
- Touching trips, e.g. `[[2,1,5],[3,5,7]]` — dropoff at 5 (`diff[5] -= 2`)
  and pickup at 5 (`diff[5] += 3`, net after both: `+1`) land on the SAME
  index; prefix sum at loc 5 reflects the passenger from trip 1 already
  gone before/exactly-as trip 2's passengers board — NOT double-counted as
  simultaneous. This is why the difference-array boundary naturally treats
  touching as non-overlapping without any extra `<` vs `<=` reasoning —
  the array formulation bakes in the correct semantics automatically.
- `from == 0` — valid per constraints (`0 <= fromi`); `diff[0] +=
  passengers` works fine, no special-casing needed.
- Many trips all overlapping at one point — occupancy accumulates the sum
  of ALL their passenger counts at that shared location; if it ever
  exceeds capacity, return False as soon as that peak is crossed (early
  exit, don't need to finish the sweep).
- `capacity` very large relative to any single trip — always True unless
  the sum of ALL simultaneously-active trips' passengers exceeds it; no
  edge case beyond the general logic.

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. Using `diff[end - 1] -= passengers` instead of `diff[end] -=
   passengers` — conflates "the passenger occupies kilometer `to`" with
   "the passenger has left by kilometer `to`"; per this problem `to` is
   the drop-off point, exclusive of continued occupancy, so decrementing
   AT `end` (not `end - 1`) is correct and matches the touching-trips
   edge case above.
2. Sizing the difference array too small — must cover up to the maximum
   possible `to` value (1000 per constraints, so size 1001 to safely index
   `diff[1000]`); an off-by-one array size causes an `IndexError` on the
   maximum-boundary test case.
3. Checking `occupancy >= capacity` (non-strict) instead of `occupancy >
   capacity` — capacity is the number of SEATS, so occupancy exactly equal
   to capacity is fine (car is full, not over capacity); using `>=` would
   incorrectly reject a trip plan that exactly fills the car.
4. Forgetting to reset/scope `occupancy` correctly across the WHOLE swept
   range (0 to V) rather than stopping early at the highest `to` value seen
   — usually harmless since nothing changes past the last dropoff, but a
   sweep that stops too early could miss a peak if trips aren't
   pre-validated to be well-formed.
5. In Approach 2, forgetting `occupancy -= p` when popping expired
   entries from the heap — leaves the running occupancy permanently
   inflated after a trip's passengers should have disembarked.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if the coordinate range were unbounded (e.g. GPS coordinates, not
  km markers 0-1000)?" -> the difference array no longer fits in memory
  directly; fall back to Approach 2's sort + min-heap sweep, or
  coordinate-compress the distinct from/to values first and run the
  difference array over the compressed indices (O(n log n) for the
  compression sort, same asymptotics as the heap approach but often a
  lower constant factor).
- "How does this generalize to variable capacity over time (e.g. some
  segments of road allow more passengers)?" -> a genuinely different
  problem — becomes a resource-constrained scheduling problem, no longer a
  simple threshold check.
- "Can you identify WHICH trip causes the overflow?" -> track trip
  identity alongside the diff-array approach isn't natural (it only tracks
  aggregate counts); switch to Approach 2's heap, which naturally knows
  which trips are "in the car" at each step.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 19/005 Meeting Rooms II — the unweighted (each interval counts as
  exactly 1) version of this exact "peak concurrent count" question.
- Topic 04 (Prefix Sum) — the difference-array-then-prefix-sum trick is the
  same mechanism used there for range-update problems in general.
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def carPooling(self, trips: List[List[int]], capacity: int) -> bool:
        diff = [0] * 1001
        for passengers, start, end in trips:
            diff[start] += passengers
            diff[end] -= passengers
        occupancy = 0
        for delta in diff:
            occupancy += delta
            if occupancy > capacity:
                return False
        return True


class SolutionHeapSweep:
    def carPooling(self, trips: List[List[int]], capacity: int) -> bool:
        ordered = sorted(trips, key=lambda t: t[1])
        heap = []  # (end, passengers)
        occupancy = 0
        for passengers, start, end in ordered:
            while heap and heap[0][0] <= start:
                _, p = heapq.heappop(heap)
                occupancy -= p
            occupancy += passengers
            if occupancy > capacity:
                return False
            heapq.heappush(heap, (end, passengers))
        return True


class SolutionBruteForce:
    def carPooling(self, trips: List[List[int]], capacity: int) -> bool:
        for loc in range(1001):
            total = sum(p for p, s, e in trips if s <= loc < e)
            if total > capacity:
                return False
        return True


def run_tests():
    sol = Solution()
    assert sol.carPooling([[2, 1, 5], [3, 3, 7]], 4) is False
    assert sol.carPooling([[2, 1, 5], [3, 3, 7]], 5) is True
    assert sol.carPooling([[2, 1, 5], [3, 5, 7]], 3) is True
    assert sol.carPooling([[3, 2, 7], [3, 7, 9], [8, 3, 9]], 11) is True
    assert sol.carPooling([[10, 0, 1]], 9) is False
    assert sol.carPooling([[10, 0, 1]], 10) is True

    # cross-check all three approaches against each other
    heap_sol = SolutionHeapSweep()
    brute = SolutionBruteForce()
    random.seed(29)
    for _ in range(200):
        n = random.randint(0, 10)
        trips = []
        for _ in range(n):
            s = random.randint(0, 20)
            e = s + random.randint(1, 10)
            p = random.randint(1, 10)
            trips.append([p, s, e])
        cap = random.randint(1, 40)
        r1 = sol.carPooling([t[:] for t in trips], cap)
        r2 = heap_sol.carPooling([t[:] for t in trips], cap)
        r3 = brute.carPooling([t[:] for t in trips], cap)
        assert r1 == r2 == r3, f"mismatch: trips={trips} cap={cap} diff={r1} heap={r2} brute={r3}"

    # --- measured runtime demo: difference array O(n+V) vs heap O(n log n) ---
    random.seed(37)
    n = 1000
    trips = []
    for _ in range(n):
        s = random.randint(0, 990)
        e = s + random.randint(1, 10)
        p = random.randint(1, 4)
        trips.append([p, s, min(e, 1000)])
    capacity = 10**5  # never trips False -- pure throughput measurement

    t0 = time.perf_counter()
    for _ in range(200):
        diff_result = sol.carPooling([t[:] for t in trips], capacity)
    diff_time = (time.perf_counter() - t0) / 200

    t0 = time.perf_counter()
    for _ in range(200):
        heap_result = heap_sol.carPooling([t[:] for t in trips], capacity)
    heap_time = (time.perf_counter() - t0) / 200

    assert diff_result == heap_result is True

    print(f"n={n} trips, coordinate range V=1000 (this machine, CPython, "
          f"averaged over 200 runs):")
    print(f"  difference array O(n+V):  {diff_time*1000:8.4f} ms")
    print(f"  sort + heap sweep O(n log n): {heap_time*1000:8.4f} ms")
    ratio = heap_time / diff_time
    print(f"  difference array is {ratio:.1f}x faster when the coordinate "
          f"range is small and bounded")
    assert diff_time < heap_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
