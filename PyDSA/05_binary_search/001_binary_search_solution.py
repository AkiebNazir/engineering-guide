"""
================================================================================
SOLUTION · LeetCode 704 · Binary Search                                 [Easy]
https://leetcode.com/problems/binary-search/
================================================================================

THE CORE IDEA
--------------
`nums` is sorted, so `a[mid]` compared to `target` tells you which HALF the
target could possibly be in — the other half can be discarded entirely,
without ever looking at it. See the topic guide §1.0 for the general
statement (a monotone predicate, of which "sorted array" is the common case)
and §1.1 for why this is "Family A": lo/hi are indices INTO the array.

    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if nums[mid] == target: return mid
        elif nums[mid] < target: lo = mid + 1
        else: hi = mid - 1
    return -1

Each iteration discards at least half the remaining candidates, so the loop
runs at most O(log n) times. This is the bare mechanism every other problem
in this folder builds on.


================================================================================
WHY `lo <= hi`, NOT `lo < hi` (topic guide §1.2a)
================================================================================
This problem is an EXACT match search that may legitimately fail (the target
may not be in the array at all). `lo <= hi` keeps searching as long as the
range `[lo, hi]` contains at least one candidate index; the loop naturally
exits with `lo > hi` (an empty range) when nothing matched, and that is
exactly the "-1" case. Using `lo < hi` here would exit one iteration too
early, on the very last remaining candidate, without ever testing it.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [-1, 0, 3, 5, 9, 12], target = 9
index:   0   1  2  3  4   5

    lo=0 hi=5   mid=2   nums[2]=3    3 < 9  -> lo = 3
    lo=3 hi=5   mid=4   nums[4]=9    9 == 9 -> return 4

    [-1  0  3][5  9  12]
     lo    hi
              lo    mid  hi     <- after lo=3, hi still 5
                    ^
                 mid=4, nums[4]=9 -> match, return 4

nums = [-1, 0, 3, 5, 9, 12], target = 2 (not present)

    lo=0 hi=5   mid=2   nums[2]=3    3 > 2  -> hi = 1
    lo=0 hi=1   mid=0   nums[0]=-1  -1 < 2  -> lo = 1
    lo=1 hi=1   mid=1   nums[1]=0    0 < 2  -> lo = 2
    lo=2 hi=1   lo > hi -> loop ends -> return -1


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time      Space   Mutates input?  Note
    ---------------------  --------  ------  ---------------  --------------------
    Linear scan             O(n)      O(1)    no               correct, too slow
    Binary search ✅        O(log n)  O(1)    no               the answer


================================================================================
EDGE CASES
================================================================================
    n == 1, target present    -> single-element array; mid == lo == hi immediately.
    n == 1, target absent     -> loop runs once, returns -1.
    target < nums[0]           -> hi shrinks to -1 on the first useful comparison.
    target > nums[-1]          -> lo grows past len(nums)-1, loop exits via lo > hi.
    target == nums[0] / nums[-1] -> boundary values must be found, not skipped by
                                     an off-by-one in the initial lo/hi.


================================================================================
COMMON MISTAKES
================================================================================
1. `while lo < hi` instead of `while lo <= hi` — silently drops the last
   candidate index from consideration (topic guide §1.2a).
2. `hi = mid` instead of `hi = mid - 1` when `nums[mid] > target` — `mid` has
   been conclusively ruled out (it's too big), so it must be excluded, or the
   loop can spin without progress.
3. Writing `mid = (lo + hi) / 2` and forgetting Python 3's `/` returns a
   float — must be `//` (integer floor division) since `mid` indexes a list.
4. In C/Java/Go, `(lo + hi)` can overflow 32-bit int when both are near
   INT_MAX; the idiomatic fix is `mid = lo + (hi - lo) // 2`. Python's
   arbitrary-precision ints make this a non-issue here (topic guide §1.2b) —
   worth saying out loud, not worth "fixing" in Python.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the array has duplicates and you want the FIRST occurrence?
A: Problem 002's `bisect_left` template: don't return immediately on a match,
   instead treat "found or too big" as one branch (`hi = mid`) and narrow to
   the leftmost matching index with `while lo < hi`.

Q: What if you only have a black-box comparator, not a materialised array?
A: Same algorithm; see the oracle pattern in problems 003/004 and topic guide
   §1.6 — `nums[mid]` becomes a function call instead of an array read.

Q: Can you do this recursively?
A: Yes, `search(nums, target, lo, hi)` with the same three branches, base case
   `lo > hi -> -1`. Same O(log n) time, but O(log n) call-stack space instead
   of O(1) — worth naming as a real tradeoff, not "equivalent."


================================================================================
RELATED PROBLEMS
================================================================================
    LC 35   Search Insert Position          — leftmost-True variant (002 here)
    LC 34   Find First and Last Position    — bisect_left AND bisect_right
    LC 74   Search a 2D Matrix              — this mechanism over a flattened
                                              2D index space (005 here)
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def search(self, nums: List[int], target: int) -> int:
        """Classic Family A binary search. O(log n) time, O(1) space."""
        lo, hi = 0, len(nums) - 1
        while lo <= hi:
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                lo = mid + 1
            else:
                hi = mid - 1
        return -1

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def search_linear(self, nums: List[int], target: int) -> int:
        """O(n) oracle: linear scan. Used only to cross-check and benchmark."""
        for i, x in enumerate(nums):
            if x == target:
                return i
        return -1

    def search_recursive(self, nums: List[int], target: int) -> int:
        """O(log n) time but O(log n) call-stack space, not O(1)."""
        def helper(lo, hi):
            if lo > hi:
                return -1
            mid = (lo + hi) // 2
            if nums[mid] == target:
                return mid
            elif nums[mid] < target:
                return helper(mid + 1, hi)
            else:
                return helper(lo, mid - 1)
        return helper(0, len(nums) - 1)


# ==============================================================================
# TESTS — run:  python 001_binary_search_solution.py
# ==============================================================================
CASES = [
    ([-1, 0, 3, 5, 9, 12], 9, 4),
    ([-1, 0, 3, 5, 9, 12], 2, -1),
    ([5], 5, 0),
    ([5], -5, -1),
    ([2, 5], 2, 0),
    ([2, 5], 5, 1),
    ([-9999, -1, 0, 1, 9999], -9999, 0),
    ([-9999, -1, 0, 1, 9999], 9999, 4),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for nums, target, expected in CASES:
        got = sol.search(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<28} target={target:<6} "
              f"-> {got}  (want {expected})")

    print("\n--- recursive variant cross-check ---")
    for nums, target, expected in CASES:
        got = sol.search_recursive(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  recursive nums={nums!r:<24} target={target:<6} -> {got}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums=[-1,0,3,5,9,12], target=9 ---")
    nums, target = [-1, 0, 3, 5, 9, 12], 9
    lo, hi = 0, len(nums) - 1
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'nums[mid]':>10}")
    while lo <= hi:
        mid = (lo + hi) // 2
        print(f"  {lo:>3} {hi:>3} {mid:>4} {nums[mid]:>10}")
        if nums[mid] == target:
            print(f"  match at index {mid}")
            break
        elif nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. linear-scan oracle ---")
    random.seed(11)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(1, 30)
        nums = sorted(random.sample(range(-100, 100), n))
        target = random.choice(nums) if random.random() < 0.5 else random.randint(-150, 150)
        if sol.search(nums, target) != sol.search_linear(nums, target):
            mismatches += 1
    print(f"  {trials} random sorted arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(log n) binary search vs O(n) linear scan.
    # ----------------------------------------------------------------------
    print("\n--- O(log n) binary search vs O(n) linear scan: measured runtime ---")
    print(f"  {'n':>9} {'binary(us)':>12} {'linear(us)':>12} {'speedup':>10}")
    for n in (10_000, 100_000, 1_000_000, 5_000_000):
        nums = list(range(n))          # sorted, dense
        target = n - 1                  # worst case for linear scan: last element
        # Average over repeated calls for a stable measurement.
        reps = 200
        t0 = time.perf_counter()
        for _ in range(reps):
            sol.search(nums, target)
        t1 = time.perf_counter()
        for _ in range(reps):
            sol.search_linear(nums, target)
        t2 = time.perf_counter()
        bin_us = (t1 - t0) / reps * 1_000_000
        lin_us = (t2 - t1) / reps * 1_000_000
        speedup = lin_us / bin_us if bin_us > 0 else float("inf")
        print(f"  {n:>9} {bin_us:>10.2f}us {lin_us:>10.2f}us {speedup:>9.1f}x")
    print("  Binary search's cost barely grows as n scales up 500x (log growth);")
    print("  linear scan's cost grows in direct proportion to n. The gap widens")
    print("  exactly as the topic guide predicts.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
