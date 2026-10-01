"""
================================================================================
SOLUTION · LeetCode 1899 · Merge Triplets to Form Target Triplet        [Medium]
https://leetcode.com/problems/merge-triplets-to-form-target-triplet/
================================================================================

THE CORE IDEA
--------------
Merging is coordinate-wise max, so no merge can ever push any coordinate
ABOVE the maximum of that coordinate across ALL triplets you choose to
involve. That means: any triplet with even ONE coordinate strictly greater
than the corresponding target coordinate is immediately USELESS (worse than
useless — including it in any merge chain would overshoot that coordinate
past the target, and max only ever grows, never shrinks, so an overshoot
can never be undone). Filter those out. Among the remaining "usable"
triplets (every coordinate <= target's), take the coordinate-wise max
across all of them. If that max equals `target` exactly, it's achievable;
otherwise some coordinate never got hit by any usable triplet, and it's
impossible.

EXCHANGE ARGUMENT (why discarding any triplet with an over-target
coordinate is always safe, and why taking the max of everything else is
optimal)
-------------------------------------------------------------------
Part 1 — discarding is safe: suppose an optimal merge sequence uses a
triplet `t` where `t[k] > target[k]` for some coordinate `k`, as one of the
inputs feeding (possibly transitively) into the final target-producing
triplet. Because merge is `max`, the coordinate `k` of every triplet
downstream of `t` in that merge chain is `>= t[k] > target[k]`. So the
final result's coordinate `k` would ALSO be `> target[k]` — it can never
equal `target[k]` exactly. Contradiction (we assumed the sequence
successfully produces `target`). So no valid solution EVER uses a triplet
with an over-target coordinate — discarding them removes zero valid
options, it's not a heuristic trade-off at all.

Part 2 — taking the max of all usable triplets is optimal: among usable
triplets (every coordinate <= target), the achievable coordinate-wise max
using ANY subset via ANY sequence of merges is exactly the coordinate-wise
max of that WHOLE subset — merging is associative, commutative, and
idempotent (`max(max(a,b),c) == max(a,max(b,c)) == max(a,b,c)`), so no
merge ORDER or SUBSET CHOICE among usable triplets can beat simply taking
the max of ALL of them; using every usable triplet is never worse than
using a subset, since `max` only grows or stays the same as you add sources
in per coordinate. So the coordinate-wise max of every usable triplet is
the best you can achieve, and if that best doesn't equal `target`, nothing
does.

================================================================================
APPROACH 0 · Brute force — try every subset and merge order (priced, not
coded)
================================================================================
Try every subset of triplets, every order of merging them, check if any
produces `target`. Since merge is associative/commutative/idempotent (Part
2 above), order never matters and only the SUBSET matters — still 2^n
subsets in the worst case if you didn't know that filtering by
over-target coordinates removes all the "always useless" ones first.
Exponential; never the coded answer.

================================================================================
APPROACH 1 · Filter usable triplets, take coordinate-wise max ✅ (the answer)
================================================================================
    def mergeTriplets(triplets, target):
        tx, ty, tz = target
        rx = ry = rz = 0
        for a, b, c in triplets:
            if a > tx or b > ty or c > tz:
                continue           # unusable: would overshoot some coordinate
            rx = max(rx, a)
            ry = max(ry, b)
            rz = max(rz, c)
        return (rx, ry, rz) == (tx, ty, tz)

    Time:  O(n) — single pass over the triplets (3 comparisons + up to 3
           max updates each)
    Space: O(1) extra

================================================================================
APPROACH 2 (for contrast, not needed here) · Explore all subsets
================================================================================
There is no meaningful DP formulation that beats Approach 1 — the moment
you notice `max` is associative/commutative/idempotent, the "which subset
to merge" search collapses entirely (Part 2 of the exchange argument), so
there's no partial-state exploration worth memoizing. This is a case where
the greedy insight doesn't just avoid DP's extra factor, it eliminates the
combinatorial structure that would have motivated DP in the first place.

--------------------------------------------------------------------------------
STEP BY STEP TRACE
--------------------------------------------------------------------------------
triplets = [[2,5,3],[1,8,4],[1,7,5]], target = [2,7,5]

  tx,ty,tz = 2,7,5;  rx=ry=rz=0

  [2,5,3]: 2>2? no. 5>7? no. 3>5? no.  -> usable
           rx=max(0,2)=2, ry=max(0,5)=5, rz=max(0,3)=3
  [1,8,4]: 1>2? no. 8>7? YES           -> unusable, skip entirely
  [1,7,5]: 1>2? no. 7>7? no. 5>5? no.  -> usable
           rx=max(2,1)=2, ry=max(5,7)=7, rz=max(3,5)=5

  result = (2,7,5) == target (2,7,5) -> True

triplets = [[3,4,5],[4,5,6]], target = [3,2,5]

  tx,ty,tz = 3,2,5

  [3,4,5]: 3>3? no. 4>2? YES  -> unusable, skip
  [4,5,6]: 4>3? YES           -> unusable, skip

  result = (0,0,0) == (3,2,5)? No -> False
  (no triplet ever contributes a 2 in the y-coordinate, matching the
  problem's own explanation)

--------------------------------------------------------------------------------
COMPLEXITY SUMMARY
--------------------------------------------------------------------------------
| Approach                              | Time  | Space | Mutates input? |
|-------------------------------------------|------|-------|------------------|
| 0 · brute force (all subsets/orders)      | O(2^n) | O(n) | No             |
| 1 · filter + coordinate-wise max ✅        | O(n)  | O(1) | No — reads only |

--------------------------------------------------------------------------------
EDGE CASES
--------------------------------------------------------------------------------
- A triplet EXACTLY equal to `target` already present: it's usable (no
  coordinate exceeds target), and its own coordinates alone achieve the
  max — correctly returns True even with only that one triplet contributing.
- Every triplet unusable (all have some over-target coordinate): `rx=ry=rz=0`
  stays at the initial value, which only matches `target` if `target ==
  [0,0,0]` — but constraints guarantee target coordinates are >= 1, so this
  always correctly returns False when nothing is usable.
- A coordinate that no usable triplet ever reaches high enough (present in
  example 2): correctly caught by the final equality check.
- All triplets identical: filtering and max-taking both degrade gracefully
  (repeated identical contributions to the max change nothing, matching
  idempotency).

--------------------------------------------------------------------------------
COMMON MISTAKES
--------------------------------------------------------------------------------
1. **Looks-greedy-but-wrong: taking the coordinate-wise max of ALL triplets
   without first filtering out over-target ones** — an over-target
   coordinate in ANY triplet would silently poison the final max for that
   coordinate, making it impossible to ever equal `target` even when a
   valid subset of OTHER triplets could have. Filtering first is not an
   optional optimization, it's required for correctness.
2. Filtering by checking only ONE or two of the three coordinates against
   target instead of all three — a triplet can be usable-looking on two
   coordinates and still be poisoned by the third.
3. Comparing `>=` instead of `>` when filtering — a coordinate EQUAL to the
   target's is perfectly fine to include (it won't overshoot); only
   STRICTLY greater disqualifies a triplet. Using `>=` would wrongly reject
   the exact triplet needed if it also happens to already match target on
   some coordinate.
4. Forgetting the final equality check and returning True as soon as any
   usable triplet is found — usability alone doesn't guarantee the max
   across ALL usable triplets actually reaches every target coordinate;
   you need to accumulate across every usable triplet and compare at the
   end.

--------------------------------------------------------------------------------
RUNTIME DEMO — O(n) filter-and-max vs. exponential subset brute force,
measured on this machine
--------------------------------------------------------------------------------
See the code below.

--------------------------------------------------------------------------------
FOLLOW-UPS AN INTERVIEWER MAY ASK
--------------------------------------------------------------------------------
- "What if the merge operation were MIN instead of MAX?" — symmetric
  argument: discard any triplet with a coordinate BELOW target, take the
  coordinate-wise min of the rest, compare to target.
- "What if you needed to know WHICH triplets to merge, not just
  True/False?" — collect the usable triplets as you filter; any subset of
  them whose max equals target works (not necessarily all of them, though
  using all usable ones is always sufficient per the exchange argument).
- "What if triplets had more than 3 coordinates (n-tuples)?" — identical
  argument generalizes directly to n coordinates, same O(n * k) algorithm
  for k coordinates.

--------------------------------------------------------------------------------
RELATED PROBLEMS
--------------------------------------------------------------------------------
- 18/007 Hand of Straights — different mechanism, same theme of "some
  candidates are provably useless and can be filtered before the real
  decision."
- 01 Arrays & Hashing topic — coordinate-wise aggregation patterns.
================================================================================
"""

import itertools
import random
import time


class Solution:
    def mergeTriplets(self, triplets: list[list[int]], target: list[int]) -> bool:
        tx, ty, tz = target
        rx = ry = rz = 0
        for a, b, c in triplets:
            if a > tx or b > ty or c > tz:
                continue
            rx = max(rx, a)
            ry = max(ry, b)
            rz = max(rz, c)
        return (rx, ry, rz) == (tx, ty, tz)


def merge_triplets_brute_force(triplets: list[list[int]], target: list[int]) -> bool:
    """Try every non-empty subset, coordinate-wise max it (order never
    matters since max is associative/commutative/idempotent). Exponential
    -- used only as a ground-truth oracle on tiny inputs."""
    n = len(triplets)
    for r in range(1, n + 1):
        for combo in itertools.combinations(triplets, r):
            rx = max(t[0] for t in combo)
            ry = max(t[1] for t in combo)
            rz = max(t[2] for t in combo)
            if (rx, ry, rz) == tuple(target):
                return True
    return False


def run_tests():
    sol = Solution()
    assert sol.mergeTriplets([[2, 5, 3], [1, 8, 4], [1, 7, 5]], [2, 7, 5]) is True
    assert sol.mergeTriplets([[3, 4, 5], [4, 5, 6]], [3, 2, 5]) is False
    assert (
        sol.mergeTriplets([[2, 5, 3], [2, 3, 4], [1, 2, 5], [5, 2, 3]], [5, 5, 5])
        is True
    )
    assert sol.mergeTriplets([[5, 5, 5]], [5, 5, 5]) is True
    assert sol.mergeTriplets([[6, 5, 5]], [5, 5, 5]) is False

    # cross-check against exhaustive subset brute force on random small inputs
    random.seed(31)
    for _ in range(150):
        n = random.randint(1, 5)
        triplets = [[random.randint(1, 4) for _ in range(3)] for _ in range(n)]
        target = [random.randint(1, 4) for _ in range(3)]
        assert sol.mergeTriplets(triplets, target) == merge_triplets_brute_force(
            triplets, target
        ), f"mismatch on triplets={triplets} target={target}"

    original = [[2, 5, 3], [1, 8, 4], [1, 7, 5]]
    sol.mergeTriplets(original, [2, 7, 5])
    assert original == [[2, 5, 3], [1, 8, 4], [1, 7, 5]]

    # --- Runtime demo: O(n) filter-and-max vs exponential brute force -------
    small_n = 14
    random.seed(37)
    triplets = [[random.randint(1, 6) for _ in range(3)] for _ in range(small_n)]
    target = [6, 6, 6]

    t0 = time.perf_counter()
    fast_result = sol.mergeTriplets(triplets, target)
    fast_time = time.perf_counter() - t0

    t0 = time.perf_counter()
    slow_result = merge_triplets_brute_force(triplets, target)
    slow_time = time.perf_counter() - t0

    assert fast_result == slow_result
    print(f"n={small_n} triplets: O(n) filter-and-max took {fast_time*1000:.4f} ms")
    print(f"n={small_n} triplets: exponential subset search took {slow_time*1000:.2f} ms")
    print(f"greedy is {slow_time / fast_time:.1f}x faster on this run")
    assert fast_time < slow_time

    print("ALL PASSED")


if __name__ == "__main__":
    run_tests()
