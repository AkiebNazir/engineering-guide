"""
================================================================================
SOLUTION · LeetCode 729 · My Calendar I                                 [Medium]
https://leetcode.com/problems/my-calendar-i/
================================================================================

THE CORE IDEA
--------------
Half-open intervals [s1, e1) and [s2, e2) overlap exactly when
`s1 < e2 and s2 < e1`. Booked events never overlap each other, so kept in
sorted order, a new event can only collide with its two NEIGHBORS: the last
event starting at or before it and the first event starting after it. Binary
search finds both.


================================================================================
APPROACH 1 · Linear scan
================================================================================
    for s, e in self.events:
        if start < e and s < end:
            return False
    self.events.append((start, end))
    return True

    Time: O(n) per book -> O(n^2) total    Space: O(n)

With at most 1000 calls this passes easily. It's the right FIRST answer; the
interviewer will then ask how to make it faster.


================================================================================
APPROACH 2 · Sorted starts/ends + bisect ✅ (the answer)
================================================================================
    i = bisect_right(self.starts, start)
    if i > 0 and self.ends[i - 1] > start:          # previous event runs past start
        return False
    if i < len(self.starts) and self.starts[i] < end: # next event begins before end
        return False
    self.starts.insert(i, start)
    self.ends.insert(i, end)
    return True

WHY ONLY TWO NEIGHBORS. Events are disjoint and sorted, so their ends are sorted
too. Every event before i-1 ends by starts[i-1] <= start: no overlap. Every event
after i starts at or after starts[i]; if starts[i] >= end, so do they.

    Time: O(log n) search + O(n) list insert    Space: O(n)

The insert is a C memmove over pointers, cheap in practice. For O(log n)
inserts, use a balanced BST (Java TreeMap floorKey/ceilingKey, C++ std::map
lower_bound) or sortedcontainers.SortedList in Python.


================================================================================
APPROACH 3 · Binary search tree of intervals
================================================================================
Each node holds [start, end). To insert, go left if end <= node.start, right if
start >= node.end, otherwise it overlaps: reject.

    Time: O(h) per book — O(log n) balanced, O(n) if bookings arrive sorted
    Space: O(n)

Elegant, but an unbalanced BST degrades on sorted input. The demo builds a
degenerate tree to show the depth.


================================================================================
STEP BY STEP TRACE · book(10,20), book(15,25), book(20,30)
================================================================================
    book(10, 20): starts [] -> i = 0; no neighbours           -> True
                  starts [10] ends [20]
    book(15, 25): i = bisect_right([10], 15) = 1
                  previous: ends[0] = 20 > 15                   -> False
    book(20, 30): i = bisect_right([10], 20) = 1
                  previous: ends[0] = 20 > 20? no
                  next: none                                    -> True
                  starts [10, 20] ends [20, 30]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                 Per book                         Space   Mutates input?
    -----------------------  -------------------------------  ------  --------------
    Linear scan              O(n)                             O(n)    n/a (design)
    Sorted lists + bisect ✅ O(log n) search, O(n) insert     O(n)    n/a
    Balanced BST / TreeMap   O(log n)                         O(n)    n/a
    Plain BST                O(h), O(n) worst                 O(n)    n/a


================================================================================
EDGE CASES
================================================================================
    Touching intervals       [10,20) then [20,30): allowed (half-open).
    Containment              [1,100) then [2,3): rejected.
    Identical interval       Rejected.
    Before everything        i = 0, only the "next" check applies.
    After everything         i = n, only the "previous" check applies.
    Rejected booking         Must NOT be inserted.


================================================================================
COMMON MISTAKES
================================================================================
1. Treating intervals as CLOSED: `s1 <= e2 and s2 <= e1`. Rejects touching
   bookings like [10,20) and [20,30). Demo below.

2. Enumerating overlap cases by hand (left overlap, right overlap, contains,
   contained) and missing one.

3. bisect_left vs bisect_right on starts: with bisect_left, an existing event
   with the SAME start lands at index i instead of i - 1; the "next" check still
   catches it (starts[i] == start < end), so both work — but be sure you can
   explain why.

4. Inserting before checking, then forgetting to remove on failure.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Allow double booking but not triple (My Calendar II)?
A: Problem 011: track overlaps separately, or a sweep over a difference map.

Q: Return the maximum number of overlapping events after each booking
   (My Calendar III)?
A: Difference map over sorted boundaries (O(n) per call), or a segment tree
   with lazy propagation over compressed coordinates (O(log n)).

Q: Meeting room booking system for a company?
A: Store per-room interval trees / sorted sets; for "find any free room"
   index rooms by next-free time. At scale, bookings live in a database with
   an exclusion constraint (PostgreSQL EXCLUDE USING gist on tstzrange) so
   concurrent requests can't both succeed.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 731   My Calendar II (011)
    LC 732   My Calendar III                  — max overlap, sweep / segment tree
    LC 252   Meeting Rooms (001)              — same overlap test, batch
    LC 715   Range Module                     — sorted disjoint intervals with merge/split
================================================================================
"""

import bisect
import random
import time
from typing import List, Optional, Tuple


class MyCalendar:
    def __init__(self):
        self.starts: List[int] = []
        self.ends: List[int] = []

    def book(self, start: int, end: int) -> bool:
        i = bisect.bisect_right(self.starts, start)
        if i > 0 and self.ends[i - 1] > start:
            return False
        if i < len(self.starts) and self.starts[i] < end:
            return False
        self.starts.insert(i, start)
        self.ends.insert(i, end)
        return True


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
class CalendarLinear:
    def __init__(self):
        self.events: List[Tuple[int, int]] = []

    def book(self, start: int, end: int) -> bool:
        for s, e in self.events:
            if start < e and s < end:
                return False
        self.events.append((start, end))
        return True


class _Node:
    __slots__ = ("start", "end", "left", "right")

    def __init__(self, start: int, end: int):
        self.start, self.end = start, end
        self.left: Optional["_Node"] = None
        self.right: Optional["_Node"] = None


class CalendarBST:
    def __init__(self):
        self.root: Optional[_Node] = None
        self.max_depth = 0

    def book(self, start: int, end: int) -> bool:
        if self.root is None:
            self.root = _Node(start, end)
            self.max_depth = 1
            return True
        node, depth = self.root, 1
        while True:
            depth += 1
            if end <= node.start:
                if node.left is None:
                    node.left = _Node(start, end)
                    break
                node = node.left
            elif start >= node.end:
                if node.right is None:
                    node.right = _Node(start, end)
                    break
                node = node.right
            else:
                return False
        self.max_depth = max(self.max_depth, depth)
        return True


class CalendarClosedBug:
    """Mistake 1: closed-interval overlap test."""

    def __init__(self):
        self.events: List[Tuple[int, int]] = []

    def book(self, start: int, end: int) -> bool:
        for s, e in self.events:
            if start <= e and s <= end:                  # BUG
                return False
        self.events.append((start, end))
        return True


class CalendarOracle:
    """Marks every covered integer point. Only for small coordinates."""

    def __init__(self, size: int):
        self.used = [False] * size

    def book(self, start: int, end: int) -> bool:
        if any(self.used[start:end]):
            return False
        for x in range(start, end):
            self.used[x] = True
        return True


# ==============================================================================
# TESTS — run:  python 010_my_calendar_i_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: bisect vs linear vs BST ---")
    scripts = [
        [((10, 20), True), ((15, 25), False), ((20, 30), True)],
        [((5, 10), True), ((0, 5), True), ((0, 6), False), ((10, 11), True), ((9, 10), False)],
        [((1, 100), True), ((2, 3), False), ((0, 1), True), ((100, 101), True)],
    ]
    for script in scripts:
        want = [w for _, w in script]
        results = []
        for cls in (MyCalendar, CalendarLinear, CalendarBST):
            cal = cls()
            results.append([cal.book(s, e) for (s, e), _ in script])
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {[iv for iv, _ in script]}  got={results[0]}  want={want}")

    print("\n--- randomized cross-check vs point-marking oracle (300 scripts) ---")
    rng = random.Random(729)
    bad = 0
    for _ in range(300):
        cals = (MyCalendar(), CalendarLinear(), CalendarBST(), CalendarOracle(60))
        for _ in range(rng.randint(1, 40)):
            s = rng.randint(0, 55)
            e = rng.randint(s + 1, min(60, s + 8))
            answers = {c.book(s, e) for c in cals}
            if len(answers) != 1:
                bad += 1
                break
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random booking scripts: all implementations agree with the oracle")

    print("\n--- mistake 1 LIVE: closed intervals reject touching bookings ---")
    good, bug = MyCalendar(), CalendarClosedBug()
    g = [good.book(10, 20), good.book(20, 30)]
    b = [bug.book(10, 20), bug.book(20, 30)]
    ok = g == [True, True] and b == [True, False]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  book(10,20), book(20,30): half-open {g}, closed {b}")

    print("\n--- plain BST degenerates when bookings arrive in sorted order ---")
    bst = CalendarBST()
    for k in range(1000):
        bst.book(k * 10, k * 10 + 5)
    ok = bst.max_depth == 1000
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1000 sorted bookings -> BST depth {bst.max_depth} (a linked list)")

    print("\n--- benchmark: 20,000 random bookings ---")
    ops = []
    for _ in range(20_000):
        s = rng.randint(0, 10**9)
        ops.append((s, s + rng.randint(1, 50_000)))
    for name, cls in (("linear scan     ", CalendarLinear), ("sorted + bisect ", MyCalendar),
                      ("plain BST       ", CalendarBST)):
        cal = cls()
        t0 = time.perf_counter()
        accepted = sum(cal.book(s, e) for s, e in ops)
        dt = time.perf_counter() - t0
        print(f"      {name} {dt * 1000:8.1f} ms   accepted {accepted:,}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
