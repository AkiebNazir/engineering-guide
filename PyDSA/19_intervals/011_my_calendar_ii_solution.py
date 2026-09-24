"""
================================================================================
SOLUTION · LeetCode 731 · My Calendar II                                [Medium]
https://leetcode.com/problems/my-calendar-ii/
================================================================================

THE CORE IDEA
--------------
Maintain two lists: all accepted `bookings`, and the `overlaps` (regions that
are already double booked). A new event triple-books exactly when it intersects
some overlap region. If it doesn't, accept it and add its intersections with
existing bookings to `overlaps`. Store the INTERSECTION, never the whole
booking.


================================================================================
APPROACH 1 · Bookings + overlaps lists ✅ (the answer)
================================================================================
    for s, e in self.overlaps:
        if start < e and s < end:
            return False                               # would be triple
    for s, e in self.bookings:
        if start < e and s < end:
            self.overlaps.append((max(start, s), min(end, e)))
    self.bookings.append((start, end))
    return True

WHY CHECKING `overlaps` IS ENOUGH. A moment x is triple booked after adding
[start, end) iff x is in the new event AND x was already covered twice. The
regions covered twice are exactly the union of `overlaps`. So the test is
"does the new event touch any overlap region".

    Time: O(n) per book (overlaps may hold more entries than bookings)
    Space: O(n^2) worst case for overlaps, O(n) typical


================================================================================
APPROACH 2 · Sweep line over a difference map
================================================================================
Keep a sorted map boundary -> delta (+1 at start, -1 at end). To book, add the
event, walk the boundaries in order with a running sum, and if the sum ever
exceeds 2, undo the event and return False.

    Time: O(n) per book (O(n log n) if you re-sort a plain dict each time)
    Space: O(n)

This generalizes directly to "at most K overlapping events" and to My Calendar
III (report the max overlap). Approach 1 doesn't generalize past K = 2.


================================================================================
APPROACH 3 · Segment tree with lazy propagation
================================================================================
Over compressed (or dynamic) coordinates: range add +1, query range max. Book if
max over [start, end) is < 2. O(log C) per call. Worth naming for My Calendar
III follow-ups; overkill for 1000 calls.


================================================================================
STEP BY STEP TRACE · LC example
================================================================================
    call          overlap check          new overlaps added          result
    ------------  ---------------------  --------------------------  ------
    (10,20)       overlaps []            —                           True
    (50,60)       []                     none (no booking intersects) True
    (10,40)       []                     (10,20) with [10,20)        True
    (5,15)        hits (10,20)           —                           False
    (5,10)        (10,20)? 5<20, 10<10? no                           True
                                         (5,10)∩(10,20) empty, none added
    (25,55)       (10,20)? 25<20? no     (25,40) with [10,40)
                                         (50,55) with [50,60)        True


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Per book          Space      Mutates input?
    ------------------------------  ----------------  ---------  --------------
    Bookings + overlaps ✅          O(n)              O(n^2) wc  n/a (design)
    Sweep over difference map       O(n) (sorted map) O(n)       n/a
    Segment tree (lazy)             O(log C)          O(n log C) n/a


================================================================================
EDGE CASES
================================================================================
    Touching intervals            Half-open: no intersection at the boundary.
    Identical event three times   Third is rejected.
    Rejected event                Must not be added to bookings OR overlaps.
    Overlap inside overlap        (10,20),(15,25): overlap (15,20); a third
                                  event [16,18) is rejected, [20,22) is fine.


================================================================================
COMMON MISTAKES
================================================================================
1. Storing the whole BOOKING in overlaps instead of the intersection.
   (10,20),(15,25) stores (10,25); then [20,22) is wrongly rejected. Demo.

2. Adding overlaps BEFORE checking the new event against overlaps, then
   finding the event "overlaps itself".

3. Checking against bookings instead of overlaps: that implements My Calendar I
   (no double booking), rejecting valid events. Demo.

4. Forgetting to undo the difference-map update when rejecting in the sweep
   version.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: At most K overlapping bookings?
A: Sweep line with running sum <= K, or segment tree with range max < K.

Q: Return the maximum overlap after each booking (My Calendar III)?
A: Sweep line tracking the max running sum; or segment tree range add + global
   max in O(log C).

Q: Thousands of rooms and concurrent requests?
A: Per-resource interval index plus a database constraint or per-room lock so
   two concurrent requests can't both see "free". See the seat reservation
   design (SystemDesign/problems/010).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 729   My Calendar I (010)
    LC 732   My Calendar III                  — max overlap
    LC 1094  Car Pooling (009)                — difference array sweep
    LC 253   Meeting Rooms II (005)           — max overlap, batch
================================================================================
"""

import bisect
import random
import time
from typing import Dict, List, Tuple


class MyCalendarTwo:
    def __init__(self):
        self.bookings: List[Tuple[int, int]] = []
        self.overlaps: List[Tuple[int, int]] = []

    def book(self, start: int, end: int) -> bool:
        for s, e in self.overlaps:
            if start < e and s < end:
                return False
        for s, e in self.bookings:
            if start < e and s < end:
                self.overlaps.append((max(start, s), min(end, e)))
        self.bookings.append((start, end))
        return True


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
class CalendarTwoSweep:
    """Sorted boundary list + delta map; running sum must stay <= 2."""

    def __init__(self, limit: int = 2):
        self.keys: List[int] = []
        self.delta: Dict[int, int] = {}
        self.limit = limit

    def _add(self, x: int, d: int) -> None:
        if x not in self.delta:
            bisect.insort(self.keys, x)
            self.delta[x] = 0
        self.delta[x] += d

    def book(self, start: int, end: int) -> bool:
        self._add(start, 1)
        self._add(end, -1)
        running = 0
        for k in self.keys:
            running += self.delta[k]
            if running > self.limit:
                self._add(start, -1)
                self._add(end, 1)
                return False
        return True


class CalendarTwoOracle:
    def __init__(self, size: int):
        self.count = [0] * size

    def book(self, start: int, end: int) -> bool:
        if any(c >= 2 for c in self.count[start:end]):
            return False
        for x in range(start, end):
            self.count[x] += 1
        return True


class CalendarTwoWholeBookingBug:
    """Mistake 1: records the whole existing booking as the overlap region."""

    def __init__(self):
        self.bookings: List[Tuple[int, int]] = []
        self.overlaps: List[Tuple[int, int]] = []

    def book(self, start: int, end: int) -> bool:
        for s, e in self.overlaps:
            if start < e and s < end:
                return False
        for s, e in self.bookings:
            if start < e and s < end:
                self.overlaps.append((min(start, s), max(end, e)))   # BUG: union, not intersection
        self.bookings.append((start, end))
        return True


class CalendarTwoChecksBookingsBug:
    """Mistake 3: tests against bookings (that's My Calendar I)."""

    def __init__(self):
        self.bookings: List[Tuple[int, int]] = []

    def book(self, start: int, end: int) -> bool:
        for s, e in self.bookings:
            if start < e and s < end:
                return False
        self.bookings.append((start, end))
        return True


# ==============================================================================
# TESTS — run:  python 011_my_calendar_ii_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: overlaps list vs sweep line ---")
    scripts = [
        [((10, 20), True), ((50, 60), True), ((10, 40), True), ((5, 15), False), ((5, 10), True), ((25, 55), True)],
        [((10, 20), True), ((15, 25), True), ((20, 22), True), ((16, 18), False)],
        [((1, 5), True), ((1, 5), True), ((1, 5), False), ((5, 6), True)],
    ]
    for script in scripts:
        want = [w for _, w in script]
        a, b = MyCalendarTwo(), CalendarTwoSweep()
        ga = [a.book(s, e) for (s, e), _ in script]
        gb = [b.book(s, e) for (s, e), _ in script]
        ok = ga == gb == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {[iv for iv, _ in script]}  got={ga}  want={want}")

    print("\n--- randomized cross-check vs per-point counter (300 scripts) ---")
    rng = random.Random(731)
    bad = 0
    for _ in range(300):
        cals = (MyCalendarTwo(), CalendarTwoSweep(), CalendarTwoOracle(60))
        for _ in range(rng.randint(1, 40)):
            s = rng.randint(0, 55)
            e = rng.randint(s + 1, min(60, s + 10))
            if len({c.book(s, e) for c in cals}) != 1:
                bad += 1
                break
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random scripts agree with the oracle")

    print("\n--- mistake 1 LIVE: storing the union instead of the intersection ---")
    good, bug = MyCalendarTwo(), CalendarTwoWholeBookingBug()
    seq = [(10, 20), (15, 25), (20, 22)]
    g = [good.book(*iv) for iv in seq]
    b = [bug.book(*iv) for iv in seq]
    ok = g == [True, True, True] and b == [True, True, False]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {seq}: intersection {g}, union {b}")
    print("      the only double-booked region is [15, 20); [20, 22) never touches it")

    print("\n--- mistake 3 LIVE: checking bookings instead of overlaps ---")
    good, bug = MyCalendarTwo(), CalendarTwoChecksBookingsBug()
    seq = [(10, 20), (10, 40)]
    g = [good.book(*iv) for iv in seq]
    b = [bug.book(*iv) for iv in seq]
    ok = g == [True, True] and b == [True, False]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {seq}: correct {g}, bookings-check {b} (that's 'no double booking')")

    print("\n--- benchmark: 1,000 random bookings (the constraint max) ---")
    ops = []
    for _ in range(1000):
        s = rng.randint(0, 10**6)
        ops.append((s, s + rng.randint(1, 20_000)))
    for name, cls in (("overlaps list", MyCalendarTwo), ("sweep line   ", CalendarTwoSweep)):
        cal = cls()
        t0 = time.perf_counter()
        accepted = sum(cal.book(s, e) for s, e in ops)
        dt = time.perf_counter() - t0
        print(f"      {name}  {dt * 1000:7.1f} ms   accepted {accepted}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
