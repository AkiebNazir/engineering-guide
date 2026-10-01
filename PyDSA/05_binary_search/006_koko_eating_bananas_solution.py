"""
================================================================================
SOLUTION · LeetCode 875 · Koko Eating Bananas                          [Medium]
https://leetcode.com/problems/koko-eating-bananas/
================================================================================

THE CORE IDEA
--------------
This is the topic's Family B debut (topic guide §1.1): there is no array to
search ON — `piles` is an INPUT used to evaluate candidates, not the search
space itself. The search space is Koko's possible EATING SPEEDS, `k`, from 1
to `max(piles)`.

Define the feasibility predicate:

    feasible(k) = "can Koko finish every pile within h hours, eating at
                   speed k?"
                = sum(ceil(pile / k) for pile in piles) <= h

`feasible` is MONOTONE in k: a faster speed can only finish piles in fewer or
equal hours per pile, never more — so if speed k works, every speed > k also
works. This is the fact that licenses binary search here; state it before
writing any code:

    "If Koko can finish at speed k, she can finish at any speed > k too,
     because eating faster only shrinks (or keeps flat) the hours needed
     per pile. That makes feasible() monotone, so the smallest working
     speed can be found by binary search over k."

We want the SMALLEST k with feasible(k) == True — the leftmost-True template
again (topic guide §1.1's Family B box):

    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid              # mid works; a smaller k might also work
        else:
            lo = mid + 1          # mid too slow; rule it out
    return lo


================================================================================
WHY `lo, hi = 1, max(piles)`, NOT INDICES INTO `piles`
================================================================================
This is the detail that trips people who are only fluent in Family A: `lo`
and `hi` bound the ANSWER (a possible eating speed), not any position in
`piles`. `lo = 1` is the slowest speed that makes any progress at all (speed
0 never finishes anything). `hi = max(piles)` is fast enough to finish the
single largest pile in exactly one hour — going any faster than that wastes
speed on every pile, since no pile needs more than `max(piles)` bananas/hour
to clear in one hour. There is no reason to search beyond it.


================================================================================
STEP BY STEP TRACE
================================================================================
piles = [3, 6, 7, 11], h = 8

    lo=1  hi=11  mid=6   hours = ceil(3/6)+ceil(6/6)+ceil(7/6)+ceil(11/6)
                        = 1 + 1 + 2 + 2 = 6      6 <= 8 -> feasible -> hi = 6
    lo=1  hi=6   mid=3   hours = ceil(3/3)+ceil(6/3)+ceil(7/3)+ceil(11/3)
                        = 1 + 2 + 3 + 4 = 10    10 > 8 -> infeasible -> lo = 4
    lo=4  hi=6   mid=5   hours = ceil(3/5)+ceil(6/5)+ceil(7/5)+ceil(11/5)
                        = 1 + 2 + 2 + 3 = 8      8 <= 8 -> feasible -> hi = 5
    lo=4  hi=5   mid=4   hours = ceil(3/4)+ceil(6/4)+ceil(7/4)+ceil(11/4)
                        = 1 + 2 + 2 + 3 = 8      8 <= 8 -> feasible -> hi = 4
    lo=4  hi=4   loop ends -> return 4   ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                                  Time                Space   Mutates input?  Note
    -----------------------------------------  ------------------  ------  ---------------  --------------------
    Try every speed from 1 upward, linearly     O(max(piles) * n)  O(1)    no               correct, far too slow
    Binary search on speed + feasible() ✅      O(n log(max(piles))) O(1)  no               the answer;
                                                                                            feasible() itself
                                                                                            costs O(n)


================================================================================
EDGE CASES
================================================================================
    Single pile                 -> hi = that pile's size; feasible(hi) is
                                    trivially True in one hour, forces the
                                    search down toward the true minimum.
    h == len(piles)              -> the absolute minimum time budget (one hour
                                    per pile, no slack); k must be large enough
                                    to clear each pile's own size in one hour,
                                    i.e. the true answer equals max(piles).
    h very large (lots of slack) -> the smallest valid k could be 1, if Koko
                                    has enough hours to eat one banana at a
                                    time from every pile.
    pile of size 1                -> ceil(1/k) == 1 for any k >= 1; never the
                                    bottleneck.
    all piles equal                -> feasible() is symmetric across piles;
                                    good for stress-testing ceiling-division.


================================================================================
COMMON MISTAKES
================================================================================
1. Not recognising this as Family B at all — trying to binary search INDICES
   into `piles` instead of VALUES of k. There is no "sorted piles array" to
   search; the piles don't even need to be sorted for feasible() to work.
2. Using `pile // k` instead of `ceil(pile / k)` — floor division undercounts
   hours whenever a pile isn't an exact multiple of k, e.g. pile=7, k=6 needs
   2 hours (`7 // 6 == 1` is WRONG; `-(-7 // 6) == 2`, or
   `(7 + 6 - 1) // 6 == 2`, is right).
3. `hi = mid - 1` instead of `hi = mid` when `feasible(mid)` is True — throws
   away a `mid` that might BE the minimum working speed.
4. Setting `hi` to `sum(piles)` or some other loose bound instead of
   `max(piles)` — not wrong (still correct), but wastes iterations; the
   tight bound follows directly from the one-pile-per-hour observation above.
5. Not stating the monotonicity argument before coding — an interviewer will
   often ask "why does binary search apply here?" and "there's no array"
   is not an acceptable non-answer; the predicate IS the array's replacement.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if h could be less than len(piles)?
A: Impossible to finish — every pile needs at least 1 hour regardless of
   speed. The problem's constraint `piles.length <= h` guarantees this can't
   happen, but naming the check shows you understand WHY the constraint
   exists.

Q: How does this generalise to LC 1011 (Capacity To Ship Packages) and
   LC 410 (Split Array Largest Sum)?
A: Same Family B template with a different feasible(): "can I ship
   everything in D days at capacity k?" (010) and "can I split into k parts
   with max part-sum <= x?" (011) are both monotone in their respective `k`
   for the same reason bananas are — a bigger capacity/threshold can only
   make the simulation easier, never harder.

Q: Can you compute feasible(k) faster than O(n)?
A: Not in general — you must inspect every pile to sum its hours. O(n) per
   feasibility check is intrinsic here, giving O(n log(max(piles))) overall,
   which the constraints (n <= 10^4, piles[i] <= 10^9) comfortably allow.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1011  Capacity To Ship Packages Within D Days — same template, ship
                                                          capacity instead of
                                                          eating speed (010)
    LC 410   Split Array Largest Sum                 — same template, split
                                                          threshold instead of
                                                          eating speed (011)
    LC 1482  Minimum Number of Days to Make m
              Bouquets                                — same template family
    LC 774   Minimize Max Distance to Gas Station     — Family B over a
                                                          continuous (float)
                                                          answer space
================================================================================
"""

import math
import random
import time
from typing import List


class Solution:
    def minEatingSpeed(self, piles: List[int], h: int) -> int:
        """Binary search on the answer (eating speed), Family B. O(n log(max
        (piles))) time, O(1) space. See THE CORE IDEA above."""
        def feasible(k: int) -> bool:
            hours = 0
            for p in piles:
                hours += -(-p // k)     # ceil(p / k) without importing math
            return hours <= h

        lo, hi = 1, max(piles)
        while lo < hi:
            mid = (lo + hi) // 2
            if feasible(mid):
                hi = mid
            else:
                lo = mid + 1
        return lo

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def minEatingSpeed_linear(self, piles: List[int], h: int) -> int:
        """O(max(piles) * n) oracle: try every speed from 1 upward."""
        def hours_needed(k: int) -> int:
            return sum(-(-p // k) for p in piles)

        k = 1
        while hours_needed(k) > h:
            k += 1
        return k

    @staticmethod
    def feasible_for_demo(piles: List[int], h: int, k: int) -> bool:
        """Exposed standalone so the demo can print feasible(k) across a range."""
        return sum(math.ceil(p / k) for p in piles) <= h


# ==============================================================================
# TESTS — run:  python 006_koko_eating_bananas_solution.py
# ==============================================================================
CASES = [
    ([3, 6, 7, 11], 8, 4),
    ([30, 11, 23, 4, 20], 5, 30),
    ([30, 11, 23, 4, 20], 6, 23),
    ([1], 1, 1),
    ([1000000000], 2, 500000000),
    ([1, 1, 1, 1], 4, 1),
    ([312884470], 968709470, 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for piles, h, expected in CASES:
        got = sol.minEatingSpeed(piles, h)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  piles={piles!r:<24} h={h:<6} -> {got}  (want {expected})")

    print("\n--- cross-check vs. linear (try every speed) oracle, small cases ---")
    for piles, h in [([3, 6, 7, 11], 8), ([30, 11, 23, 4, 20], 5), ([1, 2, 3, 4], 6)]:
        a = sol.minEatingSpeed(piles, h)
        b = sol.minEatingSpeed_linear(piles, h)
        ok = a == b
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  piles={piles!r:<20} h={h:<3} binary={a} linear={b}")

    # ----------------------------------------------------------------------
    # ⚠️ Prove feasible() is actually monotone — print it across a range.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ proving feasible(k) is monotone: piles=[3,6,7,11], h=8 ---")
    piles, h = [3, 6, 7, 11], 8
    print(f"  {'k':>3}  hours_needed  feasible(k)")
    seen_true = False
    monotone_ok = True
    for k in range(1, 12):
        hours = sum(math.ceil(p / k) for p in piles)
        f = hours <= h
        if f:
            seen_true = True
        elif seen_true:
            monotone_ok = False  # a False AFTER a True would break monotonicity
        print(f"  {k:>3}  {hours:>12}  {f}")
    print(f"  pattern is False...False,True...True (never flips back): {monotone_ok}")
    all_ok &= monotone_ok

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: piles=[3,6,7,11], h=8 ---")
    lo, hi = 1, max(piles)
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'hours':>6} {'feasible':>9}")
    while lo < hi:
        mid = (lo + hi) // 2
        hours = sum(math.ceil(p / mid) for p in piles)
        f = hours <= h
        print(f"  {lo:>3} {hi:>3} {mid:>4} {hours:>6} {str(f):>9}")
        if f:
            hi = mid
        else:
            lo = mid + 1
    print(f"  final lo == hi == {lo} -> minimum eating speed is {lo}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. linear oracle ---")
    random.seed(9)
    trials, mismatches = 500, 0
    for _ in range(trials):
        n = random.randint(1, 8)
        piles = [random.randint(1, 50) for _ in range(n)]
        h = random.randint(n, n * 20)
        if sol.minEatingSpeed(piles, h) != sol.minEatingSpeed_linear(piles, h):
            mismatches += 1
    print(f"  {trials} random (piles, h) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: search-the-answer vs brute-force try-every-speed.
    # ----------------------------------------------------------------------
    print("\n--- binary search on the answer vs. brute-force every speed ---")
    print(f"  {'#piles':>7} {'max(piles)':>11} {'binary(ms)':>11} {'brute(ms)':>10} {'speedup':>10}")
    random.seed(2)
    for n, max_pile in ((200, 5000), (500, 20000), (1000, 50000)):
        piles = [random.randint(1, max_pile) for _ in range(n)]
        h = n * 5  # some slack, forces a real search rather than an instant answer
        t0 = time.perf_counter()
        a = sol.minEatingSpeed(piles, h)
        t1 = time.perf_counter()
        b = sol.minEatingSpeed_linear(piles, h)
        t2 = time.perf_counter()
        assert a == b, f"mismatch: {a} vs {b}"
        bin_ms = (t1 - t0) * 1000
        brute_ms = (t2 - t1) * 1000
        speedup = brute_ms / bin_ms if bin_ms > 0 else float("inf")
        print(f"  {n:>7} {max_pile:>11} {bin_ms:>10.2f}ms {brute_ms:>9.2f}ms {speedup:>9.1f}x")
    print("  Binary search evaluates feasible() ~log2(max(piles)) times; brute")
    print("  force evaluates hours_needed() up to (answer - 1) extra times before")
    print("  it. The gap grows with max(piles), exactly as the topic guide predicts.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
