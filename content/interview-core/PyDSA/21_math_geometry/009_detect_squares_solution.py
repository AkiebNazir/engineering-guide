"""
================================================================================
SOLUTION · LeetCode 2013 · Detect Squares                          [Medium]
https://leetcode.com/problems/detect-squares/
================================================================================

THE CORE IDEA
--------------
Keep a hash map `count[(x, y)] -> how many times this exact point has
been added` (a `Counter` keyed by coordinate tuple). To answer
`count(query_x, query_y)`: any axis-aligned square that includes the
query point as one CORNER has its DIAGONALLY OPPOSITE corner at some
`(other_x, other_y)` where `other_x != query_x` and `other_y != query_y`
and `abs(other_x - query_x) == abs(other_y - query_y)` (a square's
diagonal has equal horizontal and vertical extent). So instead of
scanning every stored point, only consider points that share the query's
x-coordinate OR its y-coordinate -- those are the only candidates for the
OTHER two corners of a square with the query point, and from any one such
"same x, different y" point you can derive the two remaining corners
algebraically (using the vertical distance as the side length, going
LEFT or RIGHT), then just look up their counts in the map, O(1) each.

Concretely: for the query point `(px, py)`, and for every stored point
`(px, y)` with the SAME x but `y != py` (a candidate for the corner
directly above/below the query, i.e. one full SIDE of the square, side
length `d = abs(y - py)`), the square's other two corners are
`(px + d, py)` / `(px + d, y)` (square to the right) and
`(px - d, py)` / `(px - d, y)` (square to the left). Each candidate
contributes `count[(px, y)] * count[(px+d, py)] * count[(px+d, y)]` (or
the mirrored left-side product) to the running total -- multiplying
COUNTS handles duplicate points directly, since each duplicate at a
corner multiplies the number of distinct square selections through that
corner.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (scan every pair of stored points, price it): for `count`,
check every pair of stored points as candidate diagonal partners for the
query point, verify the square property, and look up the 4th corner.
O(k^2) per `count` call where k = number of distinct stored points --
correct, but does a huge amount of unnecessary work checking pairs that
share neither coordinate axis with the query and can never form a valid
square with it.

Approach 1 (chosen) -- hash map of point counts, iterate only points
SHARING THE QUERY'S X-COORDINATE as diagonal-adjacent candidates (one
full side of the square), derive the other two corners algebraically, and
look up their counts. `add` is O(1). `count` is O(k) in the worst case (k
= number of DISTINCT points sharing the query's x-coordinate, generally
much smaller than the total point count), never touching points that
share neither axis with the query.


================================================================================
STEP BY STEP TRACE
================================================================================
add([3,10]); add([11,2]); add([3,2])
    count map: {(3,10):1, (11,2):1, (3,2):1}

count([11,10])   -- query = (11, 10)

    look for stored points with x == 11 (same x as query), y != 10:
        (11, 2) is stored, count=1. d = abs(2 - 10) = 8.

    for this candidate (side length d=8, "below" the query since
    2 < 10):
        square to the LEFT (px - d, ...):  corner A = (11-8, 10) = (3,10)
                                            corner B = (11-8, 2)  = (3,2)
            product = count[(11,2)] * count[(3,10)] * count[(3,2)]
                     = 1 * 1 * 1 = 1
        square to the RIGHT (px + d, ...): corner A = (19,10), corner B
            = (19,2) -- neither stored, count=0, contributes 0.

    total = 1   -- matches the expected output: [3,10],[11,2],[3,2],
    [11,10] indeed forms one axis-aligned square (side length 8).


count([14,8])   -- query = (14, 8)

    no stored point has x == 14 at all -> zero candidates -> total = 0.
    matches expected output.


add([11,2]) again -- duplicate point, count map: {..., (11,2):2, ...}

count([11,10])   -- query = (11, 10)

    candidate (11,2), count=2 now. d=8.
    square to the LEFT: product = count[(11,2)] * count[(3,10)] *
        count[(3,2)] = 2 * 1 * 1 = 2

    total = 2   -- matches expected output (the duplicate at (11,2) gives
    two distinct ways to pick the square, since the "which (11,2) did you
    use" choice counts as a different selection).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Operation                        Time                Space  Mutates state?
    ---------------------------------------------------------------------------
    add(point)                       O(1)                O(1)   yes (adds to map)
    count(point) [priced: all-pairs]  O(k^2)              O(1)    no
    count(point) [chosen: same-x only] O(k) worst case*   O(1)    no

    k = number of distinct points stored so far. *In practice bounded by
    the number of DISTINCT y-values sharing the query's x-coordinate,
    which is usually far smaller than k -- but worst case (all points
    share the query's x) it's O(k).


================================================================================
EDGE CASES
================================================================================
    count() before any points
    added                     -> map is empty, loop over candidates finds
                                none, correctly returns 0.
    duplicate points added
    (explicitly allowed)       -> handled by storing COUNTS, not a set --
                                each duplicate multiplies the number of
                                distinct square selections through that
                                corner, exactly as shown in the trace.
    query point coincides with
    a stored point             -> the candidate-search explicitly SKIPS
                                `y == py` (a point can't be its own
                                diagonal-adjacent corner with zero side
                                length -- "positive area" is required by
                                the problem, ruling out degenerate
                                zero-side squares).
    query point shares NEITHER
    x nor y with any stored
    point                      -> zero candidates found, correctly
                                returns 0 without a special case.
    two candidates on the SAME
    x giving overlapping
    squares (one to the left,
    one to the right of the
    same candidate)             -> both are checked independently and
                                summed; they represent genuinely distinct
                                squares (different sets of 4 corners) even
                                though they share the same side.


================================================================================
COMMON MISTAKES
================================================================================
1. Scanning ALL stored points (not just same-x ones) as diagonal
   candidates in `count` -- correct but wasteful; the same-x restriction
   is what keeps the per-query cost down to only genuinely relevant
   points.
2. Forgetting to skip the case `y == py` (the query's own y-coordinate)
   when scanning same-x candidates -- would treat the query point itself
   (or a duplicate stored at the exact same coordinates) as a valid
   "opposite corner," producing a zero-side, zero-area "square" that
   should not count.
3. Only checking ONE direction (e.g. only squares to the right of the
   candidate) instead of BOTH left and right -- undercounts by missing
   half the valid squares that could be formed from a given same-x
   candidate.
4. Using a `set` of points instead of a `Counter`/dict of counts --
   silently collapses duplicate points into one, breaking the explicit
   requirement that duplicates be treated as separate, individually
   countable points (the LC example's final `count` call, expecting 2,
   would wrongly return 1).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if squares didn't have to be axis-aligned?" -> Much harder -- you'd
  need to consider all rotation angles, and the diagonal/candidate-
  restriction trick used here (which relies specifically on axis-aligned
  sides having equal horizontal/vertical extents) no longer applies
  directly; a different geometric approach (e.g. checking all point pairs
  as one SIDE and rotating 90 degrees to find the other two corners) would
  be needed instead.
- "How would you extend this to axis-aligned RECTANGLES (not just
  squares)?" -> Same same-x-candidate scan, but the "other side length"
  is now an independent second dimension rather than forced equal to the
  first -- you'd need a second coordinate axis's data (e.g. a nested map)
  to look up valid rectangle widths instead of only checking `px +/- d`.
- "What's the space complexity as points accumulate?" -> O(k) where k =
  number of distinct points ever added (duplicates increment an existing
  key's count rather than adding a new key), bounded by the problem's "at
  most 3000 calls total" constraint.


================================================================================
RELATED PROBLEMS
================================================================================
- Max Points on a Line (LC 149, this topic, 010) -- another "hash map
  keyed by a derived geometric relationship" problem, keyed by a
  gcd-reduced slope instead of a coordinate.
- Number of Boomerangs (LC 447) -- hash map of pairwise distances from
  each point, a related "count geometric configurations via a hash map"
  technique.
================================================================================
"""

import random
import time
from collections import Counter
from itertools import combinations


class DetectSquares:
    def __init__(self):
        self.counts: Counter = Counter()

    def add(self, point: list[int]) -> None:
        self.counts[(point[0], point[1])] += 1

    def count(self, point: list[int]) -> int:
        px, py = point
        total = 0
        # only points sharing the query's x-coordinate can be the corner
        # diagonally-adjacent-by-one-side to the query (i.e. one full side
        # of the square, running vertically at x == px).
        # Collect distinct y-values sharing this x, along with their counts.
        for (x, y), c in list(self.counts.items()):
            if x != px or y == py:
                continue
            d = abs(y - py)
            # square extending to the right of this vertical side
            total += c * self.counts.get((px + d, py), 0) * self.counts.get((px + d, y), 0)
            # square extending to the left of this vertical side
            total += c * self.counts.get((px - d, py), 0) * self.counts.get((px - d, y), 0)
        return total


class DetectSquaresBruteForce:
    """Priced-not-shipped, genuinely independent reference implementation:
    literally enumerate every ordered triple of DISTINCT stored points
    (respecting duplicates, since the list stores every add() call
    separately) and check directly whether that triple plus the query
    point forms an axis-aligned square with positive area. O(k^3) per
    count() call. Used only for the cross-check demo below -- never the
    shipped answer."""

    def __init__(self):
        self.points: list[tuple[int, int]] = []

    def add(self, point: list[int]) -> None:
        self.points.append((point[0], point[1]))

    def count(self, point: list[int]) -> int:
        px, py = point
        query = (px, py)
        total = 0
        n = len(self.points)
        for i, j, k in combinations(range(n), 3):
            pts = [query, self.points[i], self.points[j], self.points[k]]
            if self._is_axis_aligned_square(pts):
                total += 1
        return total

    @staticmethod
    def _is_axis_aligned_square(pts: list[tuple[int, int]]) -> bool:
        xs = sorted(set(p[0] for p in pts))
        ys = sorted(set(p[1] for p in pts))
        if len(xs) != 2 or len(ys) != 2:
            return False
        side = xs[1] - xs[0]
        if side == 0 or side != ys[1] - ys[0]:
            return False
        expected = {(xs[0], ys[0]), (xs[0], ys[1]), (xs[1], ys[0]), (xs[1], ys[1])}
        return set(pts) == expected and len(pts) == 4


def run_tests() -> None:
    all_ok = True

    ds = DetectSquares()
    ds.add([3, 10])
    ds.add([11, 2])
    ds.add([3, 2])
    checks = [
        (ds.count([11, 10]), 1),
        (ds.count([14, 8]), 0),
    ]
    ds.add([11, 2])
    checks.append((ds.count([11, 10]), 2))

    for got, expected in checks:
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  count(...) -> {got} (expected {expected})")

    print()
    print("EXTRA CASES")
    print("-" * 72)
    ds2 = DetectSquares()
    ok = ds2.count([0, 0]) == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  count on empty structure -> 0")

    ds2.add([0, 0])
    ok = ds2.count([0, 0]) == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  query coincides with the only stored point -> 0 "
          f"(no positive-area square possible)")

    ds2.add([2, 0])
    ds2.add([0, 2])
    ds2.add([2, 2])
    ok = ds2.count([0, 0]) == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  a single clean unit square -> 1")

    print()
    print("CROSS-CHECK -- hash-map same-x approach vs independent brute-force rebuild")
    print("-" * 72)
    random.seed(29)
    fast = DetectSquares()
    slow = DetectSquaresBruteForce()
    mismatch = 0
    trials = 120
    for _ in range(trials):
        if random.random() < 0.5 and len(slow.points) < 25:
            p = [random.randint(0, 5), random.randint(0, 5)]
            fast.add(p)
            slow.add(p)
        else:
            q = [random.randint(0, 5), random.randint(0, 5)]
            a = fast.count(q)
            b = slow.count(q)
            if a != b:
                mismatch += 1
                if mismatch <= 3:
                    print(f"  FAIL example: count({q}) -> fast={a}, brute={b}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  0 mismatches across {trials} random add/count calls "
          f"({mismatch} found)")

    print()
    print("RUNTIME DEMO -- same-x hash-map scan vs all-triples brute force, measured live")
    print("-" * 72)
    # Brute force is O(k^3) per query, so it only stays feasible for a
    # modest k here (60 points -> C(60,3) = 34,220 triples per query) --
    # the hash-map approach has no such ceiling, which is the whole point.
    random.seed(41)
    fast2 = DetectSquares()
    slow2 = DetectSquaresBruteForce()
    pts = [[random.randint(0, 40), random.randint(0, 40)] for _ in range(60)]
    for p in pts:
        fast2.add(p)
        slow2.add(p)

    queries = [[random.randint(0, 40), random.randint(0, 40)] for _ in range(50)]

    t0 = time.perf_counter()
    fast_results = [fast2.count(q) for q in queries]
    fast_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    slow_results = [slow2.count(q) for q in queries]
    slow_ms = (time.perf_counter() - t0) * 1000

    print(f"60 stored points, 50 count() queries:")
    print(f"  same-x hash-map scan (chosen):        {fast_ms:8.2f} ms")
    print(f"  all-triples brute force [priced]:     {slow_ms:8.2f} ms")
    speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
    print(f"  measured: the same-x scan is {speedup:.1f}x faster here, and unlike the brute "
          f"force it would stay fast even at k in the thousands, since it never inspects a "
          f"point that shares neither axis with the query.")
    demo_ok = fast_results == slow_results
    all_ok &= demo_ok
    print(f"{'PASS' if demo_ok else 'FAIL'}  both approaches agree on every query result")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
