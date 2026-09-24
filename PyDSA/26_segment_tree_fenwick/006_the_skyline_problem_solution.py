"""
================================================================================
SOLUTION · LeetCode 218 · The Skyline Problem                             [Hard]
https://leetcode.com/problems/the-skyline-problem/
================================================================================

THE CORE IDEA
--------------
The skyline's height only changes at a building's left or right edge, so
sweep left to right over the SORTED set of critical x-coordinates (every
edge, from every building), and at each one ask "what's the tallest
building currently alive?" A max-heap of `(-height, right_edge)` answers
that in O(log n) per operation: push a building the moment its left edge
is reached, and lazily pop from the top whenever the top entry's
`right_edge <= current x` (it has expired and is no longer covering this
position). Process ALL pushes-then-pops for a given x together before
reading the heap's current max — that's what prevents emitting spurious
intermediate key points when several buildings start or end at the exact
same x.

A key point is emitted only when the current max height DIFFERS from the
previously emitted one — this single check is what naturally merges
adjacent same-height buildings (Example 2) and collapses "nothing actually
changed at this x" into a no-op, without any special-casing.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, CODED BELOW as a test oracle only): for
every critical x-coordinate, scan ALL buildings and take the max height of
those covering it (`left <= x < right`). O(n^2) time (n critical points,
n buildings scanned each), O(n) space. Correct and simple, but far too
slow at n = 10^4 (up to ~10^8 checks) — used here purely as an independent
oracle for the randomized cross-check below.

Approach 1 (chosen) — sweep line + max-heap with lazy deletion: O(n log n)
time (n edges, O(log n) heap push/pop each), O(n) space. See THE CORE
IDEA.

Approach 2 (alternative, not coded) — coordinate compression + segment
tree with lazy range-max assignment (the same structure 005 Falling
Squares uses): coordinate-compress every edge, assign each building's
height across its `[left, right)` span on the compressed axis (later
buildings correctly overwrite only where they're actually taller, so this
needs a general "assign, but only where it raises the max" — or simply
insert buildings SHORTEST first so taller ones always safely overwrite),
then read the height at every compressed boundary to reconstruct the key
points. Also O(n log n); heavier machinery (build + lazy propagation) for
the same result the heap sweep gets more directly — worth naming because
it reuses 005's exact toolkit, and because a segment tree DOES generalize
more easily if buildings needed to be inserted incrementally with live
queries interleaved (which this problem's batch input doesn't need).


================================================================================
STEP BY STEP TRACE
================================================================================
buildings = [[2,9,10], [3,7,15], [5,12,12], [15,20,10], [19,24,8]]

Group by left edge:
    starts = { 2: [(10, 9)], 3: [(15, 7)], 5: [(12, 12)],
               15: [(10, 20)], 19: [(8, 24)] }
    (each entry is (height, right_edge))

Critical x's (all lefts + all rights), sorted:
    [2, 3, 5, 7, 9, 12, 15, 19, 20, 24]

heap = []  (of (-height, right_edge));  result = []

x=2:  push (10,9)  -> heap: {(-10,9)}
      pop stale (top.right<=2)? 9<=2 no.
      cur_max = 10.  result empty -> append [2,10]

x=3:  push (15,7)  -> heap: {(-15,7), (-10,9)}, top=(-15,7)
      pop stale? 7<=3 no.
      cur_max = 15.  differs from 10 -> append [3,15]

x=5:  push (12,12) -> heap: {(-15,7), (-10,9), (-12,12)}, top still (-15,7)
      pop stale? 7<=5 no.
      cur_max = 15.  same as last (15) -> no append

x=7:  no new starts.
      pop stale: top=(-15,7), 7<=7 YES -> pop.
                 new top=(-12,12) (since -12 < -10), 12<=7? no -> stop.
      cur_max = 12.  differs from 15 -> append [7,12]

x=9:  no new starts.
      pop stale: top=(-12,12), 12<=9? no -> stop
      (the (-10,9) entry is still buried in the heap, NOT at top — it
       will be correctly lazy-popped later once it rises to the top)
      cur_max = 12.  same as last -> no append

x=12: no new starts.
      pop stale: top=(-12,12), 12<=12 YES -> pop.
                 new top=(-10,9), 9<=12 YES -> pop.
                 heap now empty -> stop.
      cur_max = 0 (heap empty).  differs from 12 -> append [12,0]

x=15: push (10,20) -> heap: {(-10,20)}
      pop stale? 20<=15 no.
      cur_max = 10.  differs from 0 -> append [15,10]

x=19: push (8,24)  -> heap: {(-10,20), (-8,24)}, top=(-10,20)
      pop stale? 20<=19 no.
      cur_max = 10.  same as last -> no append   (building D still wins)

x=20: no new starts.
      pop stale: top=(-10,20), 20<=20 YES -> pop.
                 new top=(-8,24), 24<=20? no -> stop.
      cur_max = 8.  differs from 10 -> append [20,8]

x=24: no new starts.
      pop stale: top=(-8,24), 24<=24 YES -> pop. heap empty -> stop.
      cur_max = 0.  differs from 8 -> append [24,0]

RESULT = [[2,10],[3,15],[7,12],[12,0],[15,10],[20,8],[24,0]]   MATCHES expected


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time         Space   Mutates input?
    -------------------------------------------------------------------------
    Brute force per-critical-x [priced]   O(n^2)       O(n)    no (read-only)
    Sweep line + max-heap ✅              O(n log n)   O(n)    no (read-only)
    Coord. compression + segment tree     O(n log n)   O(n)    no (read-only)


================================================================================
EDGE CASES
================================================================================
    Single building                Two key points: `[left, height]` and
                                    `[right, 0]`.
    Adjacent same-height buildings
    (Example 2)                    Must merge into one segment — no key
                                    point at the shared boundary, handled
                                    automatically by the "differs from
                                    previous" check.
    Fully nested buildings          A short-and-wide building fully
                                    containing a tall-and-narrow one: the
                                    tall one's start/end each produce a key
                                    point, but ONLY if it's taller than
                                    what's already alive (a short building
                                    nested inside a taller one produces NO
                                    visible key points at all — the
                                    "differs from previous" check hides it
                                    completely, which is correct: it's not
                                    visible in the skyline).
    Overlapping buildings of equal
    height with a GAP between them   Height drops to 0 between them
                                    (a separate `[x, 0]` key point), then
                                    rises again — NOT merged, because the
                                    gap means height genuinely changes
                                    twice.
    Building height ties at the SAME
    x where one starts as another
    ends                            Must push new starts before popping
                                    expired ones at the same x, or a
                                    legitimate still-alive building could
                                    be momentarily (and wrongly) treated as
                                    absent.


================================================================================
COMMON MISTAKES
================================================================================
1. Emitting a key point after EVERY individual push/pop instead of after
   resolving ALL pushes and pops for a given x first — produces spurious
   extra key points at x's where multiple buildings start or end
   simultaneously (violates "no two consecutive key points share an x").

2. Using a plain heap without lazy deletion, and instead trying to
   physically remove an expired building from the middle of the heap —
   Python's `heapq` has no O(log n) arbitrary-element removal; lazy
   deletion (check-and-pop only from the top) is the standard workaround.

3. Forgetting the "differs from previous height" check and appending a
   key point at every critical x unconditionally — produces a technically
   "correct outline" but violates the problem's exact output contract (no
   two consecutive key points with the same height) and fails LeetCode's
   grader, which compares exact output.

4. Treating a building's right edge as INCLUSIVE (`left <= x <= right`)
   instead of exclusive (`left <= x < right`) — causes two adjacent
   buildings sharing an edge to incorrectly overlap by one unit at that
   boundary, corrupting the max-height computation exactly there.

5. Not handling the empty-heap case (current max = 0) explicitly — after
   the last building's right edge is swept past and the heap empties, the
   height must correctly read 0, which is the required final key point's
   y-value.

6. Building the critical-x list only from LEFT edges (or only from RIGHT
   edges) instead of both — misses exactly the x's where the ONLY thing
   happening is a building ending with nothing new starting, silently
   dropping the corresponding downward key point.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
Q: How would 005 Falling Squares' segment-tree approach solve this
   instead?
A: Coordinate-compress every edge, then for each building (processed in
   any order, since the final read-out only cares about the MAX height at
   each point) do a range-chmax update (raise `[left,right)` to `height`
   only where it's taller than what's already there — a proper lazy-max
   tag, unlike 005's simpler unconditional assign, since here a shorter
   building processed after a taller overlapping one must NOT overwrite
   it), then read the height at every compressed boundary point to
   reconstruct the key-point list. Same asymptotic bound, heavier
   machinery.

Q: What if buildings could be added incrementally with a live query after
   each insertion ("what's the skyline so far")?
A: That's exactly when the segment-tree alternative (Approach 2) starts to
   win over the batch sweep-line: a segment tree supports one more
   incremental range update in O(log n) without recomputing the whole
   sweep from scratch, while the heap-based sweep here assumes the full
   batch of buildings is known up front.

Q: Could a monotonic stack solve this instead of a heap?
A: Not directly — "the tallest currently-alive building" isn't a monotone
   quantity with respect to sweep position the way, say, "next greater
   element" is; buildings expire in an order determined by their RIGHT
   edges, not by the order they were pushed, so a heap keyed on expiry is
   needed rather than a stack's LIFO discipline.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 699  Falling Squares                — this topic, 005, same coordinate-compression family
    LC 56   Merge Intervals (topic 19)     — the same "sort by edge, sweep" shape, simpler (no heights)
    LC 253  Meeting Rooms II               — sweep line + heap counting overlapping intervals, no heights either
    Topic 06 Stack & Monotonic Stack       — contrast: monotone problems use a stack; non-monotone "alive set" problems need a heap
================================================================================
"""

import heapq
import random
import time
from collections import defaultdict


class Solution:
    def getSkyline(self, buildings: list[list[int]]) -> list[list[int]]:
        if not buildings:
            return []

        starts = defaultdict(list)  # left edge -> [(height, right_edge), ...]
        xs = set()
        for left, right, height in buildings:
            starts[left].append((height, right))
            xs.add(left)
            xs.add(right)

        result: list[list[int]] = []
        live: list[tuple[int, int]] = []  # max-heap via (-height, right_edge)

        for x in sorted(xs):
            for height, right in starts.get(x, ()):
                heapq.heappush(live, (-height, right))

            while live and live[0][1] <= x:
                heapq.heappop(live)

            cur_max = -live[0][0] if live else 0
            if not result or result[-1][1] != cur_max:
                result.append([x, cur_max])

        return result


# ------------------------------------------------------------------------
# Oracle used only for the tests and benchmark below.
# ------------------------------------------------------------------------
def _brute_force_skyline(buildings: list[list[int]]) -> list[list[int]]:
    """✗ Priced-not-shipped: O(n^2) per-critical-x scan. Correctness oracle."""
    if not buildings:
        return []
    xs = sorted({x for l, r, h in buildings for x in (l, r)})
    result = []
    for x in xs:
        cur_max = 0
        for left, right, height in buildings:
            if left <= x < right and height > cur_max:
                cur_max = height
        if not result or result[-1][1] != cur_max:
            result.append([x, cur_max])
    return result


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    # ------------------------------------------------------------------
    # LeetCode's examples.
    # ------------------------------------------------------------------
    print("--- LeetCode examples ---")
    cases = [
        ([[2, 9, 10], [3, 7, 15], [5, 12, 12], [15, 20, 10], [19, 24, 8]],
         [[2, 10], [3, 15], [7, 12], [12, 0], [15, 10], [20, 8], [24, 0]]),
        ([[0, 2, 3], [2, 5, 3]], [[0, 3], [5, 0]]),
    ]
    for buildings, expected in cases:
        got = sol.getSkyline([b[:] for b in buildings])
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  getSkyline({buildings}) -> {got}")
        if not ok:
            print(f"       want {expected}")

    # ------------------------------------------------------------------
    # Edge cases.
    # ------------------------------------------------------------------
    print("\n--- edge cases ---")
    ok = sol.getSkyline([[3, 8, 5]]) == [[3, 5], [8, 0]]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  single building -> two key points")

    # Fully nested SHORTER building inside a taller one -- invisible.
    ok = sol.getSkyline([[1, 10, 20], [3, 5, 5]]) == [[1, 20], [10, 0]]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  shorter nested building produces no visible key points")

    # Same-height buildings with a GAP -- must NOT merge across the gap.
    ok = sol.getSkyline([[0, 3, 5], [6, 9, 5]]) == [[0, 5], [3, 0], [6, 5], [9, 0]]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  same-height buildings with a gap stay separate")

    # One building ends exactly where an equal/lower one starts.
    ok = sol.getSkyline([[0, 5, 4], [5, 10, 4]]) == [[0, 4], [10, 0]]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  touching equal-height buildings merge into one segment")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the O(n^2) brute-force oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs brute-force oracle (100 trials, n<=8) ---")
    rng = random.Random(218)
    mismatch = 0
    for _ in range(100):
        n = rng.randint(1, 8)
        buildings = []
        for _ in range(n):
            left = rng.randint(0, 30)
            right = left + rng.randint(1, 15)
            height = rng.randint(1, 20)
            buildings.append([left, right, height])
        buildings.sort(key=lambda b: b[0])  # respect the "sorted by left" constraint
        fast = sol.getSkyline([b[:] for b in buildings])
        slow = _brute_force_skyline(buildings)
        if fast != slow:
            mismatch += 1
    ok = mismatch == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {100 - mismatch}/100 random trials agree with brute force")

    # ------------------------------------------------------------------
    # BENCHMARK — O(n log n) sweep + heap vs O(n^2) brute force.
    # ------------------------------------------------------------------
    print("\n--- benchmark: sweep-line + heap vs O(n^2) brute force ---")
    print(f"  {'n':>8} {'sweep+heap (ms)':>18} {'brute force (ms)':>18} {'speedup':>10}")
    for n in (100, 400, 900):
        rng = random.Random(1)
        buildings = []
        for _ in range(n):
            left = rng.randint(0, 5000)
            right = left + rng.randint(1, 500)
            height = rng.randint(1, 1000)
            buildings.append([left, right, height])
        buildings.sort(key=lambda b: b[0])

        t0 = time.perf_counter()
        sol.getSkyline([b[:] for b in buildings])
        fast_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        _brute_force_skyline(buildings)
        slow_ms = (time.perf_counter() - t0) * 1000

        speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {n:>8} {fast_ms:>18.2f} {slow_ms:>18.2f} {speedup:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
