"""
================================================================================
SOLUTION · LeetCode 33 · Search in Rotated Sorted Array                [Medium]
https://leetcode.com/problems/search-in-rotated-sorted-array/
================================================================================

THE CORE IDEA
--------------
Same "one half is always sorted" fact as problem 007 (topic guide §1.4), but
now we're searching for an arbitrary TARGET, not just the rotation point —
so at each step we must decide which half is clean AND whether target falls
inside that half's value range.

    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:                 # LEFT half is sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1                       # target in the sorted left half
            else:
                lo = mid + 1                       # target must be in the right half
        else:                                       # RIGHT half is sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1                       # target in the sorted right half
            else:
                hi = mid - 1                       # target must be in the left half

Still one O(log n) elimination per step — just with an extra "does target
fall in this range" check before deciding which way to go.


================================================================================
WHY THIS COMPARES AGAINST `nums[lo]`, WHILE 007 COMPARED AGAINST `nums[hi]`
================================================================================
007 only needed to know WHICH side has the rotation point — comparing `mid`
to `hi` was sufficient and unambiguous for that narrower question. Here we
additionally need the actual VALUE RANGE of whichever half is sorted, so we
can test whether `target` falls inside it. `nums[lo] <= nums[mid]` is the
natural way to express "the left half, from lo to mid inclusive, is a clean
ascending run" — and once you know that, `nums[lo]` and `nums[mid]` together
give you that half's exact value range to test target against. Comparing
`nums[mid]` to `nums[hi]` would work too (symmetric logic, testing the right
half's sortedness instead) — the version here tests the left half first,
which is the more common way this is written; both are equally valid designs.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [4, 5, 6, 7, 0, 1, 2], target = 0
index:   0  1  2  3  4  5  6

    lo=0 hi=6   mid=3   nums[mid]=7
        nums[lo]=4 <= nums[mid]=7 -> LEFT half [4,5,6,7] is sorted
        is target(0) in [4, 7)?  No  -> search right -> lo = 4

    lo=4 hi=6   mid=5   nums[mid]=1
        nums[lo]=0 <= nums[mid]=1 -> LEFT half [0,1] (mid..hi still search
                                     space, but lo..mid=[0,1]) is sorted
        is target(0) in [0, 1)?  Yes -> search left -> hi = 4

    lo=4 hi=4   mid=4   nums[mid]=0
        0 == target -> return 4   ✓

    [4  5  6  7][0  1  2]
     "sorted"    target is here (0)
      but 0 not in [4,7) -> go right first, then narrow into the small side


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time      Space   Mutates input?  Note
    ---------------------------------  --------  ------  ---------------  --------------------
    Linear scan                        O(n)      O(1)    no               correct, ignores
                                                                            the sorted structure
    Find pivot (007), then search      O(log n)  O(1)    no               correct, but two
    each half separately                                                  passes when one
                                                                            suffices
    Single-pass rotated search ✅      O(log n)  O(1)    no               the answer — one
                                                                            binary search,
                                                                            deciding the sorted
                                                                            half on the fly


================================================================================
EDGE CASES
================================================================================
    Not actually rotated               -> nums[lo] <= nums[mid] every step;
                                          degenerates to plain 001-style search.
    Target equals nums[lo] or nums[hi]  -> boundary of the sorted-half range
                                          check (`<=` vs `<`) must include it.
    Target not present at all           -> loop exits via lo > hi, return -1.
    Single element, target present       -> lo == hi == mid on the first check.
    Single element, target absent        -> immediate -1.
    Rotation point at index 0 (no rotation) or index n-1 -> both extremes of
                                          the "how much was it rotated" range.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `<` instead of `<=` (or vice versa) in the range checks
   (`nums[lo] <= target < nums[mid]`) — half-open vs. closed intervals matter
   here because `nums[lo]` and `nums[mid]` are both real, checkable values;
   getting the boundary wrong misses target when it equals an endpoint.
2. Checking `nums[lo] < nums[mid]` (strict) instead of `<=` — with a
   two-element left half where `nums[lo] == nums[mid]` cannot happen under
   this problem's distinct-values guarantee, but writing `<` out of habit
   from a duplicate-allowing variant subtly changes which half is trusted
   when `mid == lo`.
3. Forgetting the `nums[mid] == target` early return — not wrong (the range
   checks would eventually still land on it), but slower and easy to fumble
   under time pressure; checking it explicitly first is simpler to reason
   about.
4. Conflating this problem with 007 — this needs the extra "does target fall
   in this half's range" test that 007 (which only needs the pivot location)
   does not.
5. Assuming duplicates don't matter — this problem (LC 33) guarantees
   distinct values; LC 81 (duplicates allowed) breaks the
   `nums[lo] <= nums[mid]` sortedness test the same way LC 154 breaks 007's,
   and needs the same `lo += 1` fallback with the same worst-case O(n) cost.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if duplicates are allowed (LC 81)?
A: `nums[lo] <= nums[mid]` becomes ambiguous when `nums[lo] == nums[mid]`
   but the array isn't actually sorted end-to-end (e.g. [1,0,1,1,1]). Fall
   back to `lo += 1` (shrink by one) in that case, accepting O(n) worst case.

Q: Could you find the pivot first (007's algorithm), then run a plain
   binary search on the correct half?
A: Yes — two O(log n) passes instead of one. Same asymptotic complexity,
   more code, and it computes the pivot even when target is found near
   `mid` on the very first comparison. The single-pass version here is
   strictly at least as good and usually simpler to write from scratch.

Q: How would you return the pivot index itself as a byproduct?
A: The single-pass version doesn't track it directly, but 007's algorithm
   run first gives it to you for free if you need both the pivot AND the
   search in the same call.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 153  Find Minimum in Rotated Sorted Array — find the pivot itself,
                                                     not an arbitrary target (007)
    LC 81   Search in Rotated Sorted Array II    — this problem with
                                                     duplicates allowed
    LC 154  Find Minimum in Rotated Sorted Array II — 007's problem, with
                                                     duplicates allowed
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def search(self, nums: List[int], target: int) -> int:
        """Single-pass binary search over a rotated sorted array. O(log n)
        time, O(1) space. See THE CORE IDEA above."""
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            if nums[lo] <= nums[mid]:          # left half [lo..mid] is sorted
                if nums[lo] <= target < nums[mid]:
                    hi = mid - 1
                else:
                    lo = mid + 1
            else:                                # right half [mid..hi] is sorted
                if nums[mid] < target <= nums[hi]:
                    lo = mid + 1
                else:
                    hi = mid - 1
        return -1

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def search_linear(self, nums: List[int], target: int) -> int:
        """O(n) oracle: linear scan, ignores the sorted structure."""
        for i, x in enumerate(nums):
            if x == target:
                return i
        return -1

    def search_two_pass(self, nums: List[int], target: int) -> int:
        """O(log n), two passes: find the pivot (007's algorithm), then a
        plain binary search on the correct half. Correct, more code than
        the single-pass version."""
        n = len(nums)
        lo, hi = 0, n - 1
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] > nums[hi]:
                lo = mid + 1
            else:
                hi = mid
        pivot = lo  # index of the minimum element

        def plain_search(a_lo, a_hi):
            while a_lo <= a_hi:
                mid = (a_lo + a_hi) // 2
                if nums[mid] == target:
                    return mid
                elif nums[mid] < target:
                    a_lo = mid + 1
                else:
                    a_hi = mid - 1
            return -1

        if nums[pivot] <= target <= nums[n - 1]:
            return plain_search(pivot, n - 1)
        else:
            return plain_search(0, pivot - 1)


# ==============================================================================
# TESTS — run:  python 008_search_in_rotated_sorted_array_solution.py
# ==============================================================================
CASES = [
    ([4, 5, 6, 7, 0, 1, 2], 0, 4),
    ([4, 5, 6, 7, 0, 1, 2], 3, -1),
    ([1], 0, -1),
    ([1], 1, 0),
    ([5, 1, 3], 5, 0),
    ([3, 1], 1, 1),
    ([4, 5, 6, 7, 8, 1, 2, 3], 8, 4),
    ([1, 2, 3, 4, 5, 6, 7], 5, 4),
    ([4, 5, 6, 7, 0, 1, 2], 4, 0),
    ([4, 5, 6, 7, 0, 1, 2], 2, 6),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for nums, target, expected in CASES:
        got = sol.search(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<28} target={target:<5} -> {got}  (want {expected})")

    print("\n--- two-pass variant cross-check ---")
    for nums, target, expected in CASES:
        got = sol.search_two_pass(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  two_pass target={target:<5} -> {got}  (want {expected})")

    # ----------------------------------------------------------------------
    # Step-by-step trace: which half is sorted, at each step.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums=[4,5,6,7,0,1,2], target=0 ---")
    nums, target = [4, 5, 6, 7, 0, 1, 2], 0
    lo, hi = 0, len(nums) - 1
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'nums[mid]':>9}  which half sorted / decision")
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target:
            print(f"  {lo:>3} {hi:>3} {mid:>4} {nums[mid]:>9}  MATCH -> return {mid}")
            break
        if nums[lo] <= nums[mid]:
            in_range = nums[lo] <= target < nums[mid]
            decision = f"LEFT sorted; target in [{nums[lo]},{nums[mid]})? {in_range}"
            print(f"  {lo:>3} {hi:>3} {mid:>4} {nums[mid]:>9}  {decision}")
            if in_range:
                hi = mid - 1
            else:
                lo = mid + 1
        else:
            in_range = nums[mid] < target <= nums[hi]
            decision = f"RIGHT sorted; target in ({nums[mid]},{nums[hi]}]? {in_range}"
            print(f"  {lo:>3} {hi:>3} {mid:>4} {nums[mid]:>9}  {decision}")
            if in_range:
                lo = mid + 1
            else:
                hi = mid - 1

    # ----------------------------------------------------------------------
    # Cross-check across every rotation of a base array, every target.
    # ----------------------------------------------------------------------
    print("\n--- cross-check across every rotation and target of a base array ---")
    base = [1, 2, 3, 4, 5, 6, 7]
    mismatches = 0
    for k in range(len(base)):
        rotated = base[k:] + base[:k]
        for target in list(base) + [0, 8]:
            want = rotated.index(target) if target in rotated else -1
            got = sol.search(rotated, target)
            if got != want:
                mismatches += 1
                print(f"  FAIL  rotation k={k} target={target}: got {got}, want {want}")
    print(f"  {len(base) * (len(base) + 2)} (rotation, target) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. linear scan ---")
    random.seed(21)
    trials, rand_mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(1, 20)
        base_nums = sorted(random.sample(range(-100, 100), n))
        k = random.randint(0, n - 1)
        rotated = base_nums[k:] + base_nums[:k]
        target = random.choice(rotated) if random.random() < 0.6 else random.randint(-150, 150)
        a = sol.search(rotated, target)
        b = sol.search_linear(rotated, target)
        if a != b:
            rand_mismatches += 1
    print(f"  {trials} random (rotated array, target) pairs: {rand_mismatches} mismatches")
    all_ok &= (rand_mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO.
    # ----------------------------------------------------------------------
    print("\n--- O(log n) rotated search vs O(n) linear scan: measured runtime ---")
    print(f"  {'n':>9} {'binary(us)':>12} {'linear(us)':>12} {'speedup':>10}")
    for n in (10_000, 100_000, 1_000_000):
        base_nums = list(range(n))
        k = n // 3
        rotated = base_nums[k:] + base_nums[:k]
        target = 0  # forces linear scan to walk deep into the array
        reps = 200
        t0 = time.perf_counter()
        for _ in range(reps):
            sol.search(rotated, target)
        t1 = time.perf_counter()
        for _ in range(reps):
            sol.search_linear(rotated, target)
        t2 = time.perf_counter()
        bin_us = (t1 - t0) / reps * 1_000_000
        lin_us = (t2 - t1) / reps * 1_000_000
        speedup = lin_us / bin_us if bin_us > 0 else float("inf")
        print(f"  {n:>9} {bin_us:>10.2f}us {lin_us:>10.2f}us {speedup:>9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
