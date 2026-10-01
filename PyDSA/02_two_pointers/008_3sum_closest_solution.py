"""
================================================================================
SOLUTION · LeetCode 16 · 3Sum Closest                                   [Medium]
https://leetcode.com/problems/3sum-closest/
================================================================================

THE CORE IDEA
--------------
Sort, fix the first element, then run opposite-end two pointers over the rest.
Sortedness gives every step a DIRECTION: if the current sum is below target,
only moving `lo` right can raise it; if above, only moving `hi` left can lower
it. Every sum visited is a candidate; keep the one with the smallest distance
`abs(sum - target)`. A sum exactly equal to target ends the search — distance
0 cannot be beaten.


================================================================================
APPROACH 1 · Brute force, all triples (priced, used only as an oracle)
================================================================================
Three nested loops over i < j < k, tracking the closest sum.

    Time: O(n^3)   — n = 500 is ~20.7 million triples.
    Space: O(1)

Correct, and at n = 500 it's too slow in Python for an interview answer. The
benchmark below measures how it scales against the two-pointer version.


================================================================================
APPROACH 2 · Sort + two pointers ✅ (the answer)
================================================================================
    nums.sort()
    closest = nums[0] + nums[1] + nums[2]          # a REAL sum, not a sentinel
    for i in range(n - 2):
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if abs(s - target) < abs(closest - target):
                closest = s
            if s < target:   lo += 1
            elif s > target: hi -= 1
            else:            return s               # distance 0: done

WHY THE POINTER MOVE IS SAFE. Suppose s < target. Every pair (lo, hi') with
hi' < hi has nums[hi'] <= nums[hi], so its sum is <= s < target — FARTHER
from target than s (or equal). None of them can beat s, so we lose nothing by
discarding `lo` and moving it right. The symmetric argument covers s > target.
This is the same "discard a whole row of the search matrix" argument as Two
Sum II (006).

    Time:  O(n log n) sort + O(n^2) scan = O(n^2)
    Space: O(1) extra (Timsort itself uses O(n) auxiliary memory)


================================================================================
VARIANT · Skip duplicate anchors
================================================================================
`if i > 0 and nums[i] == nums[i - 1]: continue` skips anchors whose two-
pointer scan would be identical to the previous one. It never changes the
answer (the same sums get visited) and only helps when there are many
duplicates. Unlike 3Sum, it is NOT required for correctness here, because we
return one number, not a de-duplicated list of triples.


================================================================================
STEP BY STEP TRACE · nums = [-1, 2, 1, -4], target = 1
================================================================================
    sorted:  [-4, -1, 1, 2]        closest starts as -4 + -1 + 1 = -4

    i=0 (-4)   lo=1 (-1)  hi=3 (2)   s = -3   |s-1| = 4 < |-4-1| = 5 -> closest=-3
                                     s < 1 -> lo=2
               lo=2 (1)   hi=3 (2)   s = -1   |−1−1| = 2 < 4        -> closest=-1
                                     s < 1 -> lo=3, loop ends
    i=1 (-1)   lo=2 (1)   hi=3 (2)   s =  2   |2-1| = 1 < 2         -> closest= 2
                                     s > 1 -> hi=2, loop ends

    answer: 2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                   Time      Space           Mutates input?
    -------------------------  --------  --------------  ---------------------
    Brute force (3 loops)      O(n^3)    O(1)            No
    Sort + two pointers ✅     O(n^2)    O(1) + sort     YES (sorts in place;
                                                          use sorted(nums) if
                                                          the caller cares)


================================================================================
EDGE CASES
================================================================================
    n == 3                     Exactly one triple; the loop runs once and the
                                initial `closest` is already the answer.
    All elements equal          Every sum is the same; duplicates must not
                                break the pointer loop.
    target far below / above    Answer is the three smallest / three largest.
                                Pointers march all the way to one end.
    Exact hit                   Return immediately; distance 0 is optimal.
    Two sums equidistant        The problem promises a unique answer, so this
                                cannot happen in valid input.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing `abs(s) < abs(closest)` instead of `abs(s - target) <
   abs(closest - target)`. It passes whenever target == 0 and fails otherwise.
   The demo below shows it returning the wrong answer on LeetCode's own
   Example 1.

2. Initializing `closest = float('inf')`. The comparison
   `abs(s - target) < abs(inf - target)` still works, but if anything goes
   wrong you return `inf`, which isn't an int. Seed it with a real triple.

3. Forgetting to sort. The pointer-move argument depends entirely on order.

4. Moving BOTH pointers after a non-matching sum. This skips pairs and can
   miss the closest one.

5. Using `lo <= hi` — lets lo == hi, which reuses one element twice.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the triple itself, not the sum?
A: Record (nums[i], nums[lo], nums[hi]) whenever closest updates.

Q: k-Sum Closest for general k?
A: Recurse: fix one element and solve (k-1)-Sum Closest on the suffix, down to
   the two-pointer base case. O(n^(k-1)).

Q: Can you prune?
A: For anchor i, the smallest possible sum is nums[i] + nums[i+1] + nums[i+2].
   If that is already > target, record it and stop the WHOLE loop — every later
   anchor is larger. Symmetrically, if nums[i] + nums[n-2] + nums[n-1] <
   target, record it and skip to the next anchor.

Q: What if nums doesn't fit in memory?
A: The O(n^2) pair scan needs random access to sorted data. Past memory you
   would sort externally and bound the search differently. In practice you'd
   ask whether an approximate answer (sampling) is acceptable.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1    Two Sum                  — hash map, unsorted
    LC 167  Two Sum II (006)         — two pointers on sorted input
    LC 15   3Sum (007)               — same skeleton, equality + dedupe
    LC 18   4Sum                     — one more fixed loop
    LC 259  3Sum Smaller             — counting pairs instead of tracking best
================================================================================
"""

import random
import time
from itertools import combinations
from typing import List


class Solution:
    def threeSumClosest(self, nums: List[int], target: int) -> int:
        nums = sorted(nums)          # don't mutate the caller's list
        n = len(nums)
        closest = nums[0] + nums[1] + nums[2]
        for i in range(n - 2):
            lo, hi = i + 1, n - 1
            while lo < hi:
                s = nums[i] + nums[lo] + nums[hi]
                if abs(s - target) < abs(closest - target):
                    closest = s
                if s < target:
                    lo += 1
                elif s > target:
                    hi -= 1
                else:
                    return s
        return closest


# ------------------------------------------------------------------------
# Alternatives / oracles / broken versions used by the demos.
# ------------------------------------------------------------------------
def closest_brute(nums: List[int], target: int) -> int:
    """Approach 1: every triple. O(n^3). Used as the correctness oracle."""
    best = None
    for a, b, c in combinations(nums, 3):
        s = a + b + c
        if best is None or abs(s - target) < abs(best - target):
            best = s
    return best


def closest_wrong_distance(nums: List[int], target: int) -> int:
    """Mistake 1: compares |s| against |closest| — distance from 0, not target."""
    nums = sorted(nums)
    n = len(nums)
    closest = nums[0] + nums[1] + nums[2]
    for i in range(n - 2):
        lo, hi = i + 1, n - 1
        while lo < hi:
            s = nums[i] + nums[lo] + nums[hi]
            if abs(s) < abs(closest):          # BUG
                closest = s
            if s < target:
                lo += 1
            elif s > target:
                hi -= 1
            else:
                return s
    return closest


# ==============================================================================
# TESTS — run:  python 008_3sum_closest_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        ([-1, 2, 1, -4], 1, 2),
        ([0, 0, 0], 1, 0),
        ([1, 1, 1, 0], -100, 2),
        ([1, 1, 1, 0], 100, 3),
        ([4, 0, 5, -5, 3, 3, 0, -4, -5], -2, -2),
        ([-1000, -1000, 1000, 1000], 0, -1000),
    ]
    for nums, target, want in cases:
        original = list(nums)
        got = sol.threeSumClosest(nums, target)
        ok = got == want and nums == original
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={original} target={target}  got={got}  want={want}")
    print("      (input list left unmodified: sorted() copy, not nums.sort())")

    print("\n--- randomized cross-check vs O(n^3) brute force (400 inputs) ---")
    rng = random.Random(16)
    mismatches = 0
    for _ in range(400):
        n = rng.randint(3, 12)
        nums = [rng.randint(-20, 20) for _ in range(n)]
        target = rng.randint(-60, 60)
        got = sol.threeSumClosest(nums, target)
        oracle = closest_brute(nums, target)
        # Ties are possible in random data; both answers must be equally close.
        if abs(got - target) != abs(oracle - target):
            mismatches += 1
    ok = mismatches == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  400 random inputs, distance always matches brute force")

    print("\n--- mistake 1 LIVE: comparing |s| instead of |s - target| ---")
    wrong = closest_wrong_distance([-1, 2, 1, -4], 1)
    right = sol.threeSumClosest([-1, 2, 1, -4], 1)
    ok = wrong != right and right == 2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  LeetCode example 1: buggy returns {wrong}, correct returns {right}")
    print("      the bug prefers the sum nearest ZERO; it only 'works' when target == 0")

    print("\n--- benchmark: O(n^3) brute force vs O(n^2) two pointers ---")
    rng = random.Random(1)
    prev = None
    for n in (60, 120, 240):
        nums = [rng.randint(-1000, 1000) for _ in range(n)]
        target = 10_001  # unreachable -> no early exit; worst case for both
        t0 = time.perf_counter(); closest_brute(nums, target); tb = time.perf_counter() - t0
        t0 = time.perf_counter(); sol.threeSumClosest(nums, target); tp = time.perf_counter() - t0
        grow = f"  brute grew {tb / prev:.1f}x vs previous n" if prev else ""
        print(f"      n={n:>4}  brute {tb * 1000:8.2f} ms   two-pointer {tp * 1000:6.2f} ms   "
              f"ratio {tb / tp:6.1f}x{grow}")
        prev = tb
    print("      doubling n multiplies brute force by ~8x (cubic) and two pointers by ~4x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
