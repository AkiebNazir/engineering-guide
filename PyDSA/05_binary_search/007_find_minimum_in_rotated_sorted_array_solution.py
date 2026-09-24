"""
================================================================================
SOLUTION · LeetCode 153 · Find Minimum in Rotated Sorted Array         [Medium]
https://leetcode.com/problems/find-minimum-in-rotated-sorted-array/
================================================================================

THE CORE IDEA
--------------
A rotated sorted array is not globally ordered, but topic guide §1.4's fact
holds: cut it anywhere, and at least one of the two halves is a clean
ascending run. The minimum element is exactly the ROTATION POINT — the one
place where a bigger element is immediately followed by a smaller one (or,
if the array wasn't rotated at all, index 0 itself).

The key comparison at each step is `nums[mid]` vs. `nums[hi]` (NOT
`nums[lo]` — see below for why):

    if nums[mid] > nums[hi]:
        # mid is on the "big" side of the rotation point — the minimum is
        # somewhere to the RIGHT of mid (mid itself cannot be the minimum,
        # since something smaller than it exists further right)
        lo = mid + 1
    else:
        # nums[mid] <= nums[hi] means mid is already on the "small" side —
        # the minimum is at mid or to its LEFT; keep mid in range
        hi = mid

This is the Family B "leftmost True" shape again (topic guide §1.1), with
`f(i) = (nums[i] <= nums[hi_original])` as the flipping predicate: false for
every index in the "big" left segment, true for every index in the "small"
right segment (including the minimum itself, at the boundary).

    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]


================================================================================
WHY COMPARE AGAINST `nums[hi]`, NOT `nums[lo]`
================================================================================
Comparing `nums[mid]` to `nums[lo]` is ambiguous in one case that
`nums[mid]` vs. `nums[hi]` is not: when the array segment `[lo, mid]` happens
to be sorted (`nums[lo] <= nums[mid]`), that alone doesn't tell you whether
the ENTIRE array from lo to hi is sorted (no rotation point in this range at
all) or whether the rotation point is further right. Comparing to `nums[hi]`
avoids the ambiguity: `nums[mid] <= nums[hi]` unconditionally means "no
rotation point exists strictly between mid and hi" (that segment is a clean
ascending run, or a single element), so the minimum is at `mid` or to its
left. `nums[mid] > nums[hi]` unconditionally means the rotation point (and
therefore the minimum) is strictly after mid. Both branches are airtight
against `hi`; neither is airtight against `lo`.


================================================================================
STEP BY STEP TRACE — WHICH HALF IS SORTED, AT EACH STEP
================================================================================
nums = [4, 5, 6, 7, 0, 1, 2]
index:   0  1  2  3  4  5  6

    lo=0 hi=6   mid=3   nums[mid]=7  nums[hi]=2   7 > 2
        -> left half [4,5,6,7] (lo..mid) IS the sorted run; rotation point
           is in the right half -> lo = 4

    lo=4 hi=6   mid=5   nums[mid]=1  nums[hi]=2   1 <= 2
        -> right half [1,2] (mid..hi) IS the sorted run; rotation point
           is at mid or earlier -> hi = 5

    lo=4 hi=5   mid=4   nums[mid]=0  nums[hi]=1   0 <= 1
        -> [0,1] (mid..hi) sorted; minimum at mid or earlier -> hi = 4

    lo=4 hi=4   loop ends -> return nums[4] = 0   ✓

    [4  5  6  7][0  1  2]
     "big" side  "small" side
                 ^ rotation point / minimum


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time      Space   Mutates input?  Note
    ---------------------------------  --------  ------  ---------------  --------------------
    Linear scan for the minimum        O(n)      O(1)    no               correct, ignores
                                                                            the sorted structure
    Binary search on the pivot ✅      O(log n)  O(1)    no               the answer


================================================================================
EDGE CASES
================================================================================
    Not actually rotated (nums already fully ascending) -> nums[mid] <= nums[hi]
                                                            every step, hi collapses
                                                            straight to lo == 0.
    Rotated by exactly 1 (minimum at the very end)        -> the "big" segment is
                                                            almost the whole array.
    Rotated by n-1 (minimum at index 1)                    -> the "small" segment
                                                            is almost the whole array.
    Single element                                          -> lo == hi immediately,
                                                            loop body never runs.
    Two elements, either order                              -> exercises the smallest
                                                            possible non-trivial mid.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing `nums[mid]` to `nums[lo]` instead of `nums[hi]` — ambiguous in
   the case explained above; leads to subtly wrong branch decisions that
   only surface on specific rotation amounts.
2. `hi = mid - 1` when `nums[mid] <= nums[hi]` — throws away a `mid` that
   might BE the minimum itself.
3. Assuming duplicates don't change anything — LC 153 (this problem)
   guarantees UNIQUE values, but the closely related LC 154 allows
   duplicates, where `nums[mid] == nums[hi]` is genuinely ambiguous (could
   be on either side) and requires a fallback `hi -= 1` that costs the
   O(log n) guarantee in the worst case. Don't silently assume this
   solution ports to that problem unchanged.
4. Returning `nums[mid]` at the end instead of `nums[lo]` (or vice versa,
   depending on which variable you tracked) without checking that
   `lo == hi` at loop exit — they are the same value there, but writing the
   wrong one out of habit from a different template is a common typo.
5. Treating this as "just find the smallest element" and reaching for a
   plain O(n) min() scan instead of exploiting the array's partial order —
   correct but throws away the entire point of the constraint.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if duplicates are allowed (LC 154)?
A: The `nums[mid] > nums[hi]` / `<=` split becomes ambiguous when
   `nums[mid] == nums[hi]`; the fix is to fall back to `hi -= 1` (shrink by
   one, safely, since a duplicate of the boundary value can't be the unique
   answer we're eliminating) in that case. Worst case degrades to O(n) — an
   array of all-equal values makes every comparison ambiguous.

Q: Can you find the index of the minimum instead of its value?
A: Track `lo` and return it directly instead of `nums[lo]` — the algorithm
   is identical, only the return value changes.

Q: How does this generalise to problem 008 (search for an arbitrary target,
   not just the minimum)?
A: 008 uses the same "which half is sorted" test but compares against
   `nums[lo]` because it also needs to know the array's normal-order bounds
   to decide if `target` falls inside the sorted half — see 008's solution
   file for the full argument.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 154  Find Minimum in Rotated Sorted Array II — duplicates allowed,
                                                        O(n) worst case
    LC 33   Search in Rotated Sorted Array          — find a target, not the
                                                        minimum (008 here)
    LC 81   Search in Rotated Sorted Array II       — 008's problem, with
                                                        duplicates allowed
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def findMin(self, nums: List[int]) -> int:
        """Binary search on the rotation point. O(log n) time, O(1) space.
        See THE CORE IDEA above."""
        lo, hi = 0, len(nums) - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] > nums[hi]:
                lo = mid + 1
            else:
                hi = mid
        return nums[lo]

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def findMin_linear(self, nums: List[int]) -> int:
        """O(n) oracle: plain min() scan, ignores the sorted structure."""
        return min(nums)


# ==============================================================================
# TESTS — run:  python 007_find_minimum_in_rotated_sorted_array_solution.py
# ==============================================================================
CASES = [
    ([3, 4, 5, 1, 2], 1),
    ([4, 5, 6, 7, 0, 1, 2], 0),
    ([11, 13, 15, 17], 11),
    ([1], 1),
    ([2, 1], 1),
    ([1, 2], 1),
    ([5, 1, 2, 3, 4], 1),
    ([1, 2, 3, 4, 5], 1),
    ([2, 3, 4, 5, 1], 1),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for nums, expected in CASES:
        got = sol.findMin(nums)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<24} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # Step-by-step trace: which half is sorted, at each step.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums=[4,5,6,7,0,1,2] — which half is sorted at each step ---")
    nums = [4, 5, 6, 7, 0, 1, 2]
    lo, hi = 0, len(nums) - 1
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'nums[mid]':>9} {'nums[hi]':>8}  which half is sorted")
    while lo < hi:
        mid = (lo + hi) // 2
        big_side = nums[mid] > nums[hi]
        which = "LEFT [lo..mid] sorted -> go right" if big_side else "RIGHT [mid..hi] sorted -> stay/go left"
        print(f"  {lo:>3} {hi:>3} {mid:>4} {nums[mid]:>9} {nums[hi]:>8}  {which}")
        if big_side:
            lo = mid + 1
        else:
            hi = mid
    print(f"  final lo == hi == {lo} -> minimum is nums[{lo}] = {nums[lo]}")

    # ----------------------------------------------------------------------
    # Randomised cross-check across every possible rotation of a base array.
    # ----------------------------------------------------------------------
    print("\n--- cross-check across every rotation amount of a fixed base array ---")
    base = [10, 20, 30, 40, 50, 60, 70]
    mismatches = 0
    for k in range(len(base)):
        rotated = base[k:] + base[:k]
        want = min(base)
        got = sol.findMin(rotated)
        ok = got == want
        mismatches += (0 if ok else 1)
        print(f"  {'PASS' if ok else 'FAIL'}  rotation k={k}: {rotated} -> {got}")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Randomised cross-check, general.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. min() oracle ---")
    random.seed(13)
    trials, rand_mismatches = 2000, 0
    for _ in range(trials):
        n = random.randint(1, 20)
        base_nums = sorted(random.sample(range(-100, 100), n))
        k = random.randint(0, n - 1)
        rotated = base_nums[k:] + base_nums[:k]
        if sol.findMin(rotated) != sol.findMin_linear(rotated):
            rand_mismatches += 1
    print(f"  {trials} random rotated arrays: {rand_mismatches} mismatches")
    all_ok &= (rand_mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO.
    # ----------------------------------------------------------------------
    print("\n--- O(log n) binary search vs O(n) min() scan: measured runtime ---")
    print(f"  {'n':>9} {'binary(us)':>12} {'linear(us)':>12} {'speedup':>10}")
    for n in (10_000, 100_000, 1_000_000):
        base_nums = list(range(n))
        k = n // 3
        rotated = base_nums[k:] + base_nums[:k]
        reps = 200
        t0 = time.perf_counter()
        for _ in range(reps):
            sol.findMin(rotated)
        t1 = time.perf_counter()
        for _ in range(reps):
            sol.findMin_linear(rotated)
        t2 = time.perf_counter()
        bin_us = (t1 - t0) / reps * 1_000_000
        lin_us = (t2 - t1) / reps * 1_000_000
        speedup = lin_us / bin_us if bin_us > 0 else float("inf")
        print(f"  {n:>9} {bin_us:>10.2f}us {lin_us:>10.2f}us {speedup:>9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
