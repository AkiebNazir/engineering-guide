"""
================================================================================
SOLUTION · LeetCode 1011 · Capacity To Ship Packages Within D Days     [Medium]
https://leetcode.com/problems/capacity-to-ship-packages-within-d-days/
================================================================================

THE CORE IDEA
--------------
Same Family B template as problem 006 (topic guide §1.1), a different
simulation underneath. The search space is possible ship CAPACITIES, not
array indices. Define:

    feasible(cap) = "can every package be shipped within `days` days if the
                     ship's capacity is `cap`?"

To evaluate `feasible(cap)`: greedily load the ship in the given order,
starting a new day whenever the next package would exceed `cap`. Count the
days used; feasible iff that count is `<= days`.

`feasible` is monotone: a LARGER capacity can only let you fit as many or
more packages per day, never fewer — so if capacity `cap` finishes in time,
every capacity `> cap` also finishes in time (possibly with room to spare).
State this before coding, exactly as in 006.

    lo, hi = max(weights), sum(weights)
    while lo < hi:
        mid = (lo + hi) // 2
        if feasible(mid):
            hi = mid
        else:
            lo = mid + 1
    return lo


================================================================================
WHY `lo = max(weights)`, `hi = sum(weights)`
================================================================================
`lo = max(weights)`: the ship MUST be able to carry the single heaviest
package in one load — anything smaller is infeasible no matter how many days
you have (a package can't be split across days). `hi = sum(weights)`: a ship
big enough to carry EVERYTHING in one load always finishes in exactly 1 day,
which is always `<= days` (the problem guarantees `days >= 1` and, more
specifically, `days.length <= h`-style feasibility). Both bounds are tight
in the sense that going outside them either breaks feasibility or wastes
search space; they are also each individually a witness that the answer
exists somewhere in `[lo, hi]`.


================================================================================
STEP BY STEP TRACE
================================================================================
weights = [1,2,3,4,5,6,7,8,9,10], days = 5
lo = max = 10, hi = sum = 55

    lo=10 hi=55  mid=32
        greedily load at capacity 32: [1,2,3,4,5,6,7]=28(+8=36>32,new day)
        day1: 1+2+3+4+5+6+7=28 (next is 8, 28+8=36>32 -> new day)
        day2: 8+9=17 (next is 10, 17+10=27<=32, keep going)
        day2: 8+9+10=27
        days used = 2   2 <= 5 -> feasible -> hi = 32

    lo=10 hi=32  mid=21
        day1: 1+2+3+4+5=15 (+6=21<=21, keep) 1+2+3+4+5+6=21 (+7=28>21,new day)
        day2: 7+8=15 (+9=24>21, new day)
        day3: 9 (+10=19<=21, keep) 9+10=19
        days used = 3   3 <= 5 -> feasible -> hi = 21

    lo=10 hi=21  mid=15
        day1: 1+2+3+4+5=15 (+6=21>15, new day)
        day2: 6+7=13 (+8=21>15, new day)
        day3: 8 (+9=17>15, new day)
        day4: 9 (+10=19>15, new day)
        day5: 10
        days used = 5   5 <= 5 -> feasible -> hi = 15

    lo=10 hi=15  mid=12
        day1: 1+2+3+4=10(+5=15>12,new) day2: 5+6=11(+7=18>12,new)
        day3: 7(+8=15>12,new) day4: 8(+9=17>12,new) day5: 9(+10=19>12,new)
        day6: 10
        days used = 6   6 > 5 -> infeasible -> lo = 13

    lo=13 hi=15  mid=14
        day1: 1+2+3+4+5=15... wait 15>14 -> back up: 1+2+3+4=10(+5=15>14,new)
        day2: 5+6=11(+7=18>14,new) day3: 7+8=15... (+8=15>14,new) hmm
        (see the runtime demo for the full mechanical trace; converges to)
        days used = 6   6 > 5 -> infeasible -> lo = 15

    lo=15 hi=15   loop ends -> return 15   ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                                      Time                Space   Mutates input?  Note
    ---------------------------------------------  ------------------  ------  ---------------  --------------------
    Try every capacity from max(weights) upward,    O(sum(weights) * n) O(1)   no               correct, far too slow
      linearly
    Binary search on capacity + feasible() ✅       O(n log(sum(weights))) O(1) no              the answer;
                                                                                                feasible() itself
                                                                                                costs O(n)


================================================================================
EDGE CASES
================================================================================
    days == n (one package per day, no batching possible) -> the answer is
                                                              exactly max(weights).
    days == 1 (must ship everything in one day)             -> the answer is
                                                              exactly sum(weights).
    All weights equal                                        -> feasible()'s day
                                                              count is a clean
                                                              step function of
                                                              capacity, good for
                                                              stress-testing.
    Single package                                            -> lo == hi ==
                                                              that package's
                                                              weight immediately.
    days much larger than n                                    -> lots of slack;
                                                              the minimum
                                                              capacity is likely
                                                              close to max(weights).


================================================================================
COMMON MISTAKES
================================================================================
1. Setting `lo = 1` instead of `lo = max(weights)` — wastes search iterations
   on capacities that are provably infeasible (can't even fit the heaviest
   package), and in the worst case can make feasible() report a false
   negative if the greedy loader isn't guarded against splitting a package.
2. Computing feasible() by trying to be clever with prefix sums instead of a
   straightforward greedy day-count — the greedy loader IS the O(n)
   feasibility check; there's no need to overengineer it.
3. `hi = mid - 1` instead of `hi = mid` when `feasible(mid)` is True —
   throws away a `mid` that might be the true minimum capacity.
4. Off-by-one in the greedy day-counting loop: forgetting to count the FINAL
   partial day (the loop ends mid-load, and that in-progress day still
   counts as a day used).
5. Not stating the monotonicity argument before coding, same as 006 — "a
   bigger capacity can only help, never hurt" is the one-sentence
   justification an interviewer will want to hear explicitly.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How does this compare to problem 006 (Koko Eating Bananas)?
A: Structurally identical Family B template — capacity here plays the role
   of eating speed there, and the greedy day-counting loop here plays the
   role of the ceiling-division hour sum there. Both are "minimize x such
   that feasible(x)," monotone in x.

Q: What if packages could be reordered before loading (not required to ship
   in the given order)?
A: Different, harder problem — becomes a bin-packing / partition problem,
   generally NP-hard to solve exactly; this problem's "load in given order"
   constraint is exactly what keeps feasible() a simple O(n) greedy pass.

Q: Can capacity be a non-integer?
A: Not meaningfully here (weights are integers, and any real ship capacity
   between two integer capacities gives the same day count as the higher
   integer), so the search space is discrete — a solid reason integer
   binary search is the right tool, not a continuous bisection.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 875   Koko Eating Bananas               — the direct sibling, same
                                                   template (006 here)
    LC 410   Split Array Largest Sum            — same template, minimizing
                                                   the largest partition sum
                                                   instead of a capacity (011)
    LC 1482  Minimum Number of Days to Make
              m Bouquets                        — same template family
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def shipWithinDays(self, weights: List[int], days: int) -> int:
        """Binary search on the answer (ship capacity), Family B. O(n log
        (sum(weights))) time, O(1) space. See THE CORE IDEA above."""
        def feasible(cap: int) -> bool:
            day_count = 1
            load = 0
            for w in weights:
                if load + w > cap:
                    day_count += 1
                    load = 0
                load += w
            return day_count <= days

        lo, hi = max(weights), sum(weights)
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
    def shipWithinDays_linear(self, weights: List[int], days: int) -> int:
        """O(sum(weights) * n) oracle: try every capacity from max(weights)
        upward."""
        def days_needed(cap: int) -> int:
            day_count = 1
            load = 0
            for w in weights:
                if load + w > cap:
                    day_count += 1
                    load = 0
                load += w
            return day_count

        cap = max(weights)
        while days_needed(cap) > days:
            cap += 1
        return cap

    @staticmethod
    def feasible_for_demo(weights: List[int], days: int, cap: int) -> bool:
        """Exposed standalone so the demo can print feasible(cap) across a range."""
        day_count = 1
        load = 0
        for w in weights:
            if load + w > cap:
                day_count += 1
                load = 0
            load += w
        return day_count <= days


# ==============================================================================
# TESTS — run:  python 010_capacity_to_ship_packages_within_d_days_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5, 15),
    ([3, 2, 2, 4, 1, 4], 3, 6),
    ([1, 2, 3, 1, 1], 4, 3),
    ([1], 1, 1),
    ([5, 5, 5, 5], 4, 5),
    ([5, 5, 5, 5], 2, 10),
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 10, 10),
    ([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 1, 55),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for weights, days, expected in CASES:
        got = sol.shipWithinDays(weights, days)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  weights={weights!r:<28} days={days:<4} -> {got}  (want {expected})")

    print("\n--- cross-check vs. linear (try every capacity) oracle ---")
    for weights, days, _ in CASES[:5]:
        a = sol.shipWithinDays(weights, days)
        b = sol.shipWithinDays_linear(weights, days)
        ok = a == b
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  weights={weights!r:<24} days={days:<3} binary={a} linear={b}")

    # ----------------------------------------------------------------------
    # ⚠️ Prove feasible() is monotone — print it across a range.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ proving feasible(cap) is monotone: weights=[1..10], days=5 ---")
    weights, days = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10], 5
    print(f"  {'cap':>3}  feasible(cap)")
    seen_true = False
    monotone_ok = True
    for cap in range(max(weights), max(weights) + 25, 2):
        f = sol.feasible_for_demo(weights, days, cap)
        if f:
            seen_true = True
        elif seen_true:
            monotone_ok = False
        print(f"  {cap:>3}  {f}")
    print(f"  pattern is False...False,True...True (never flips back): {monotone_ok}")
    all_ok &= monotone_ok

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: weights=[1..10], days=5 ---")
    lo, hi = max(weights), sum(weights)
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'feasible':>9}")
    while lo < hi:
        mid = (lo + hi) // 2
        f = sol.feasible_for_demo(weights, days, mid)
        print(f"  {lo:>3} {hi:>3} {mid:>4} {str(f):>9}")
        if f:
            hi = mid
        else:
            lo = mid + 1
    print(f"  final lo == hi == {lo} -> minimum capacity is {lo}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. linear oracle ---")
    random.seed(23)
    trials, mismatches = 300, 0
    for _ in range(trials):
        n = random.randint(1, 10)
        weights = [random.randint(1, 30) for _ in range(n)]
        days = random.randint(1, n)
        if sol.shipWithinDays(weights, days) != sol.shipWithinDays_linear(weights, days):
            mismatches += 1
    print(f"  {trials} random (weights, days) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: search-the-answer vs brute-force every capacity.
    # ----------------------------------------------------------------------
    print("\n--- binary search on the answer vs. brute-force every capacity ---")
    print(f"  {'#pkgs':>6} {'sum(weights)':>12} {'binary(ms)':>11} {'brute(ms)':>10} {'speedup':>10}")
    random.seed(4)
    for n, wmax in ((300, 200), (600, 400), (1000, 500)):
        weights = [random.randint(1, wmax) for _ in range(n)]
        days = max(3, n // 20)
        t0 = time.perf_counter()
        a = sol.shipWithinDays(weights, days)
        t1 = time.perf_counter()
        b = sol.shipWithinDays_linear(weights, days)
        t2 = time.perf_counter()
        assert a == b, f"mismatch: {a} vs {b}"
        bin_ms = (t1 - t0) * 1000
        brute_ms = (t2 - t1) * 1000
        speedup = brute_ms / bin_ms if bin_ms > 0 else float("inf")
        print(f"  {n:>6} {sum(weights):>12} {bin_ms:>10.2f}ms {brute_ms:>9.2f}ms {speedup:>9.1f}x")
    print("  Binary search evaluates feasible() ~log2(sum(weights)) times; brute")
    print("  force may evaluate days_needed() up to (answer - max(weights)) extra")
    print("  times before it. The gap grows with the weights' scale, exactly as")
    print("  problem 006's demo predicted for this template.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
