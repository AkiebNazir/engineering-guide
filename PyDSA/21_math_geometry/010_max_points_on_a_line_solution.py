"""
================================================================================
SOLUTION · LeetCode 149 · Max Points on a Line                        [Hard]
https://leetcode.com/problems/max-points-on-a-line/
================================================================================

THE CORE IDEA
--------------
For each point used as an "anchor," group every OTHER point by the
direction (slope) from the anchor to it -- points sharing the same slope
from the same anchor lie on the same line through that anchor. The
maximum line through this anchor is `1 + (largest group size)`. Repeating
this for every point as anchor and taking the overall max finds the
answer, since any line with >= 2 points will be discovered when ANY one
of its points is used as the anchor.

The critical detail is HOW to key "same slope" in the grouping hash map.
A float slope (`dy / dx`) is the WRONG key: floating-point division can
round two genuinely EQUAL slopes to different floats (false negative --
undercounts a real line) or round two genuinely DIFFERENT slopes to the
same float (false positive -- overcounts). The fix: reduce the direction
vector `(dx, dy)` to lowest terms by dividing both by their `gcd`, and use
a FIXED SIGN CONVENTION (e.g. always make `dx` non-negative, flipping
both signs together if it started negative) so that `(2, 4)` and `(-1,
-2)` -- which represent the SAME direction -- reduce to the identical key
`(1, 2)`. This is an exact integer key with zero rounding, never a float.

Two cases need explicit handling outside the generic slope formula:
    - VERTICAL lines (`dx == 0`): no slope value exists ("infinite
      slope"); key these as a fixed sentinel like `(0, 1)` after sign-
      normalizing (`dy` made non-negative when `dx == 0`).
    - DUPLICATE points (`dx == dy == 0`): the problem's constraints
      guarantee all input points are unique, so this can't occur here --
      but if it could, a duplicate of the anchor doesn't define any slope
      at all; it would need to be counted as augmenting EVERY line through
      the anchor equally (added to the anchor's own count, not grouped
      under any one slope key), handled as a separate running counter.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (float slope as the hash key, price it -- and show it's
actually broken): `slope = (y2-y1) / (x2-x1)` as a dict key (with a
sentinel for vertical lines). Looks reasonable and passes small examples,
but is a genuine, not merely theoretical, correctness bug -- demonstrated
live below with real (dx, dy) pairs whose float division either
incorrectly agrees or incorrectly disagrees.

Approach 1 (chosen) -- gcd-reduced (dx, dy) integer pair as the hash key,
sign-normalized so a direction and its exact opposite (which represent
the same line) map to the identical key. O(n^2) time overall (n anchors,
each doing an O(n) scan grouping the other n-1 points), O(n) extra space
per anchor's grouping map.


================================================================================
STEP BY STEP TRACE
================================================================================
points = [[1,1],[3,2],[5,3],[4,1],[2,3],[1,4]]

    Using anchor = (1,1):
        to (3,2): dx=2, dy=1, gcd(2,1)=1 -> key=(2,1)
        to (5,3): dx=4, dy=2, gcd(4,2)=2 -> key=(2,1)
        to (4,1): dx=3, dy=0, gcd(3,0)=3 -> key=(1,0)  (horizontal)
        to (2,3): dx=1, dy=2, gcd(1,2)=1 -> key=(1,2)
        to (1,4): dx=0, dy=3, gcd(0,3)=3 -> key=(0,1)  (vertical, sign-
            normalized: dx==0 forces dy non-negative)

        slope groups from this anchor:
            (2,1): {(3,2),(5,3)}       -> 2 points
            (1,0): {(4,1)}             -> 1 point
            (1,2): {(2,3)}             -> 1 point
            (0,1): {(1,4)}             -> 1 point

        best group size from this anchor = 2 (the (2,1) direction)
        line through this anchor = 1 (anchor itself) + 2 = 3
        (this is the line through (1,1),(3,2),(5,3))

    ... continuing over every anchor eventually finds a 4-point line:
    (3,2),(4,1),(2,3),(1,4) all lie on the line x + y = 5 (verify:
    3+2=5, 4+1=5, 2+3=5, 1+4=5 -- yes). Using anchor=(3,2):
        to (4,1): dx=1, dy=-1 -> sign-normalize (dx negative? no, dx=1
            positive already) -> gcd(1,-1)=1 -> key=(1,-1)
        to (2,3): dx=-1, dy=1 -> dx negative, flip both signs ->
            dx=1, dy=-1 -> key=(1,-1)  (SAME key as above -- correctly
            recognized as the same direction, opposite sign)
        to (1,4): dx=-2, dy=2 -> flip -> dx=2, dy=-2 -> gcd(2,-2)=2 ->
            key=(1,-1)  (SAME key again)

        group (1,-1) from anchor (3,2): {(4,1),(2,3),(1,4)} -> 3 points
        line through this anchor = 1 + 3 = 4  -- matches example 2's
        expected output of 4.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time      Space      Mutates input?
    ------------------------------------------------------------------------
    Float slope as key [priced,
    demonstrably buggy]                O(n^2)   O(n)         no
    gcd-reduced (dx,dy) key [chosen]   O(n^2)   O(n)         no

    n = number of points. Both share the same asymptotic complexity; the
    float version is rejected for CORRECTNESS, not speed.


================================================================================
EDGE CASES
================================================================================
    n == 1                  -> a single point trivially forms a "line" of
                             size 1 (no second point needed to define
                             degenerate max); must return 1 without
                             entering the anchor loop's grouping logic
                             (which needs at least 2 points to group).
    n == 2                  -> any 2 distinct points always lie on exactly
                             one line together; answer is always 2.
    all points collinear     -> the answer equals n itself; every anchor
                             finds the same one giant slope group.
    vertical line among the
    points (shared x, varying
    y)                       -> dx == 0 case; must not attempt `dy / dx`
                             (division by zero) and must sign-normalize
                             the vertical sentinel key the same way
                             regardless of whether points are above or
                             below the anchor.
    two nearly-equal slopes
    that are NOT actually
    equal, e.g. from anchor
    (0,0): direction (1,
    10000) vs (1, 9999)      -> float division gives 10000.0 vs 9999.0,
                             correctly distinct in THIS case -- but this
                             is the exact shape of pair that becomes
                             ambiguous once large enough coordinates make
                             float rounding lossy; the gcd-integer key
                             never has this risk regardless of magnitude.
    all points are guaranteed
    UNIQUE by the problem's
    own constraints           -> the (dx==dy==0) duplicate-point case
                             described in "the core idea" above cannot
                             occur with this problem's actual input, but
                             is worth naming as what WOULD need separate
                             handling if the constraint were relaxed.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `dy / dx` as a float hash key -- demonstrably wrong: floats can
   both FALSE-MATCH two different slopes and FALSE-SPLIT two identical
   slopes once numerators/denominators get large enough that floating
   point precision runs out (proven live in the demo below, not just
   asserted).
2. Reducing `(dx, dy)` by their gcd WITHOUT a fixed sign convention --
   `(2, 4)` reduces to `(1, 2)` but `(-2, -4)` reduces to `(-1, -2)`,
   which is the SAME direction but a DIFFERENT dict key unless the sign is
   normalized consistently (e.g. always force dx >= 0, or dx==0 and dy>0
   for vertical lines).
3. Forgetting the vertical-line case (`dx == 0`) entirely -- a plain
   `dy // gcd(dx, dy)` style formula crashes on division by zero if dx is
   used as a denominator anywhere; must be branched out explicitly.
4. Recomputing the O(n^2) all-pairs slope grouping without the "1 +
   group size" adjustment -- forgetting to add the anchor point itself
   back into each line's count undercounts every answer by exactly 1.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do better than O(n^2)?" -> Not asymptotically for the general
  case -- any pair of points could potentially be the two extreme points
  of the best line, so some form of O(n^2) pairwise reasoning is
  essentially required; this is considered near-optimal for this problem.
- "What if coordinates could be non-integer (floats)?" -> The gcd-
  reduction trick specifically needs INTEGER coordinates to be exact;
  with float coordinates you'd need a rational-approximation or
  epsilon-tolerance scheme, which reintroduces precision trade-offs the
  integer version avoids entirely.
- "How would duplicate points change the algorithm?" -> Track a separate
  `duplicate_count` of points identical to the anchor; add it to EVERY
  slope group's count (since a duplicate of the anchor lies on every line
  through the anchor), and also to the "just the anchor itself" baseline
  when no other points share a slope at all.


================================================================================
RELATED PROBLEMS
================================================================================
- Detect Squares (LC 2013, this topic, 009) -- another hash-map-of-
  geometric-relationship problem, keyed by coordinate tuple instead of a
  reduced slope.
- Line Reflection (LC 356) -- another geometry problem relying on exact
  integer/hash-map reasoning to avoid float precision issues.
- Valid Boomerang (LC 1037) -- simpler "are these 3 points collinear"
  check, same underlying cross-product-instead-of-slope-division idea
  for avoiding float division.
================================================================================
"""

import random
import time
from collections import defaultdict
from math import gcd


class Solution:
    def maxPoints(self, points: list[list[int]]) -> int:
        n = len(points)
        if n <= 2:
            return n

        best = 1
        for i in range(n):
            xi, yi = points[i]
            slopes: dict[tuple[int, int], int] = defaultdict(int)
            local_best = 0
            for j in range(n):
                if i == j:
                    continue
                xj, yj = points[j]
                dx, dy = xj - xi, yj - yi
                g = gcd(dx, dy)
                # g is always >= 1 here since points are guaranteed unique
                # (dx, dy != (0, 0)); gcd() handles a zero component fine
                # (gcd(0, dy) == abs(dy)).
                dx //= g
                dy //= g
                # fixed sign convention: dx > 0, or dx == 0 and dy > 0.
                if dx < 0 or (dx == 0 and dy < 0):
                    dx, dy = -dx, -dy
                slopes[(dx, dy)] += 1
                if slopes[(dx, dy)] > local_best:
                    local_best = slopes[(dx, dy)]
            best = max(best, local_best + 1)
        return best


def _via_float_slope(points: list[list[int]]) -> int:
    """Priced-not-shipped, demonstrably buggy alternative: float slope as
    the hash key. Kept only for the live correctness-bug demonstration
    below -- NEVER the shipped answer."""
    n = len(points)
    if n <= 2:
        return n

    best = 1
    for i in range(n):
        xi, yi = points[i]
        slopes: dict[float, int] = defaultdict(int)
        local_best = 0
        for j in range(n):
            if i == j:
                continue
            xj, yj = points[j]
            if xj == xi:
                key = float("inf")
            else:
                key = (yj - yi) / (xj - xi)
            slopes[key] += 1
            if slopes[key] > local_best:
                local_best = slopes[key]
        best = max(best, local_best + 1)
    return best


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([[1, 1], [2, 2], [3, 3]], 3),
        ([[1, 1], [3, 2], [5, 3], [4, 1], [2, 3], [1, 4]], 4),
        ([[0, 0]], 1),
        ([[0, 0], [1, 1]], 2),
        ([[1, 1], [1, 2], [1, 3], [1, 4]], 4),  # vertical line
        ([[1, 1], [2, 1], [3, 1]], 3),           # horizontal line
        ([[0, 0], [1, 1], [1, -1]], 2),          # no 3 collinear
        ([[2, 3], [3, 3], [-5, 3]], 3),          # horizontal, negative x
    ]
    for points, expected in cases:
        got = sol.maxPoints([list(p) for p in points])
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  maxPoints({points}) -> {got} (expected {expected})")

    print()
    print("BUG DEMO -- float slope key vs gcd-reduced integer key, a VERIFIED collision")
    print("-" * 72)
    # Consecutive Fibonacci-number ratios converge to the golden ratio, and
    # because they're all coprime (gcd(F(n+1), F(n)) == 1 always), every
    # ratio F(n+1)/F(n) is a genuinely DIFFERENT exact fraction from
    # F(n+2)/F(n+1) -- yet once n is large enough, IEEE-754 double division
    # rounds both to the EXACT SAME float. This is a real, checked-in-this-
    # file collision (verified independently below with a plain `==`
    # check), not a hypothetical:
    def fib_pair(k: int) -> tuple[int, int]:
        a, b = 1, 1
        for _ in range(k):
            a, b = b, a + b
        return b, a  # (F(k+1), F(k))

    p39, q39 = fib_pair(39)   # F(40), F(39)
    p40, q40 = fib_pair(40)   # F(41), F(40)
    float_collision = (p39 / q39 == p40 / q40)
    exact_fractions_differ = (p39, q39) != (p40, q40)
    from math import gcd as _gcd
    reduced_differ = (p39 // _gcd(p39, q39), q39 // _gcd(p39, q39)) != \
                      (p40 // _gcd(p40, q40), q40 // _gcd(p40, q40))
    print(f"F(40)/F(39) = {p39}/{q39} = {p39/q39!r}")
    print(f"F(41)/F(40) = {p40}/{q40} = {p40/q40!r}")
    verified_ok = float_collision and exact_fractions_differ and reduced_differ
    all_ok &= verified_ok
    print(f"{'PASS' if verified_ok else 'FAIL'}  verified: these are two DIFFERENT, already-"
          f"lowest-terms fractions (gcd=1 each, consecutive Fibonacci numbers are always "
          f"coprime) whose float division produces the IDENTICAL double -- a real false-"
          f"positive collision, not a contrived edge case.")

    # Build points: anchor at the origin, one point on each Fibonacci ray.
    # A float-slope grouping will (wrongly) treat both as "the same line
    # through the origin"; the gcd-reduced integer key will not.
    anchor = [0, 0]
    on_ray_39 = [q39, p39]
    on_ray_40 = [q40, p40]
    off_ray = [1, 2]  # unrelated third point, not on either ray
    pts_bug = [anchor, on_ray_39, on_ray_40, off_ray]

    exact = sol.maxPoints([list(p) for p in pts_bug])
    floaty = _via_float_slope([list(p) for p in pts_bug])
    print(f"points = [origin, point on F(40)/F(39) ray, point on F(41)/F(40) ray, unrelated point]")
    print(f"  gcd-reduced integer key (chosen): maxPoints -> {exact}  (correct: origin + one "
          f"Fibonacci-ray point per line = 2, since the two rays are genuinely different lines)")
    print(f"  float slope key [priced, buggy]:  maxPoints -> {floaty}  (wrongly merges both "
          f"Fibonacci-ray points into ONE group, since they collide to the same float key)")
    bug_confirmed = (floaty != exact) and (floaty > exact)
    all_ok &= bug_confirmed
    print(f"{'PASS' if bug_confirmed else 'FAIL'}  measured: the float-key version overcounts "
          f"here -- a real, reproducible float-precision bug caused by two distinct exact "
          f"slopes rounding to the same double.")

    print()
    print("RUNTIME DEMO -- gcd-reduced integer key, measured live at the problem's max n=300")
    print("-" * 72)
    random.seed(99)
    seen = set()
    big_points = []
    while len(big_points) < 300:
        p = (random.randint(-10_000, 10_000), random.randint(-10_000, 10_000))
        if p not in seen:
            seen.add(p)
            big_points.append(list(p))

    t0 = time.perf_counter()
    result = sol.maxPoints([list(p) for p in big_points])
    elapsed_ms = (time.perf_counter() - t0) * 1000
    print(f"n=300 random unique points (the problem's max n): {elapsed_ms:.2f} ms, "
          f"max points on a line = {result}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
