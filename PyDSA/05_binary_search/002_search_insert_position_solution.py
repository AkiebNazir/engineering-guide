"""
================================================================================
SOLUTION · LeetCode 35 · Search Insert Position                         [Easy]
https://leetcode.com/problems/search-insert-position/
================================================================================

THE CORE IDEA
--------------
"Where should target be inserted to keep nums sorted" is exactly "the
smallest index i such that nums[i] >= target" — if target is present, that
index IS target's position; if absent, it's the first position bigger than
target, which is precisely where it belongs. This is the "leftmost True"
template from the topic guide §1.3: define

    f(i) = (nums[i] >= target)

`f` is False, False, ..., False, True, True, ..., True over the index range
(sorted array => monotone), and we want the flip point.

    lo, hi = 0, len(nums)          # hi = len(nums), NOT len(nums)-1 —
                                    # target may belong AFTER every element
    while lo < hi:
        mid = (lo + hi) // 2
        if nums[mid] >= target:
            hi = mid                # mid might BE the answer — keep it in range
        else:
            lo = mid + 1            # mid is too small, rule it out
    return lo                       # lo == hi == the leftmost i with f(i) == True

This is exactly `bisect.bisect_left(nums, target)` — Python's standard
library implements this identical template in C. Writing it by hand here is
the point of the exercise; naming the stdlib equivalent shows you know where
it lives.


================================================================================
WHY `hi = len(nums)`, NOT `len(nums) - 1` (the detail 001 didn't need)
================================================================================
001 searched for an exact match that might not exist, and −1 was an
acceptable "give up" answer covering the whole "not found" case. Here every
input has a definite CORRECT insertion index, including "insert after
everything" (target bigger than every element) — and that valid answer is
`len(nums)`, one past the last index. If `hi` started at `len(nums) - 1`,
that answer could never be reached: `mid` would never be evaluated at index
`len(nums)`, and the loop would incorrectly cap out at `len(nums) - 1`.


================================================================================
WHY `while lo < hi` WITH `hi = mid` (not `lo <= hi` WITH `hi = mid - 1`)
================================================================================
Topic guide §1.2a/c: this is a boundary search, not an exact-match search —
the answer is GUARANTEED to exist somewhere in `[0, len(nums)]`, so the loop
narrows until `lo == hi`, and that shared value IS the answer; there's no
"not found" case to fall through to. Because `nums[mid] >= target` being true
means `mid` COULD be the final answer (it might be the very leftmost True),
we must keep it in range with `hi = mid`, never discard it with `hi = mid - 1`.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 3, 5, 6], target = 5
index:   0  1  2  3

    lo=0 hi=4   mid=2   nums[2]=5    5 >= 5 -> hi = 2
    lo=0 hi=2   mid=1   nums[1]=3    3 >= 5? no -> lo = 2
    lo=2 hi=2   loop ends (lo == hi) -> return 2   ✓ (target found at index 2)

nums = [1, 3, 5, 6], target = 2 (not present, belongs between 1 and 3)

    lo=0 hi=4   mid=2   nums[2]=5    5 >= 2 -> hi = 2
    lo=0 hi=2   mid=1   nums[1]=3    3 >= 2 -> hi = 1
    lo=0 hi=1   mid=0   nums[0]=1    1 >= 2? no -> lo = 1
    lo=1 hi=1   loop ends -> return 1   ✓ (insert between index 0 and 1)

nums = [1, 3, 5, 6], target = 7 (belongs after everything)

    lo=0 hi=4   mid=2   nums[2]=5    5 >= 7? no -> lo = 3
    lo=3 hi=4   mid=3   nums[3]=6    6 >= 7? no -> lo = 4
    lo=4 hi=4   loop ends -> return 4   ✓ (one past the last index)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time      Space   Mutates input?  Note
    -------------------------------  --------  ------  ---------------  --------------------
    Linear scan for first >= target  O(n)      O(1)    no               correct, too slow
    Binary search (leftmost True) ✅ O(log n)  O(1)    no               the answer
    bisect.bisect_left (stdlib)      O(log n)  O(1)    no               same algorithm, in C


================================================================================
EDGE CASES
================================================================================
    target smaller than every element -> answer is 0; hi collapses all the
                                          way down on the first useful step.
    target larger than every element   -> answer is len(nums); THIS is exactly
                                          why hi starts at len(nums), not -1.
    target present at index 0           -> loop must not skip past index 0.
    target present at the last index    -> loop must not skip past len(nums)-1.
    single-element array, target equal  -> lo/hi collapse to 0 on the first step.
    single-element array, target smaller/larger -> answer 0 or 1 respectively.


================================================================================
COMMON MISTAKES
================================================================================
1. `hi = len(nums) - 1` instead of `len(nums)` — makes "insert after
   everything" unreachable; the answer silently caps at len(nums)-1.
2. `hi = mid - 1` instead of `hi = mid` when `nums[mid] >= target` — throws
   away a `mid` that might BE the correct leftmost answer.
3. `while lo <= hi` instead of `lo < hi` — for this boundary-search shape,
   the loop needs to converge to a single index (lo == hi), not fall through
   an empty range; using `<=` here risks off-by-one on the final answer.
4. Treating this as "find target, else -1" (001's shape) and bolting on
   special-case logic for "not found" afterward, instead of recognising it
   as a single leftmost-True search from the start.
5. Confusing this with `bisect_right` (rightmost valid insertion point when
   duplicates are allowed) — LC 35 guarantees distinct values, so
   `bisect_left` and `bisect_right` coincide here, but they diverge the
   moment duplicates are allowed (see the follow-up below).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if nums has duplicates and you want the insertion point AFTER all
   equal elements, not before?
A: Flip the predicate to `nums[mid] > target` (strict), i.e. bisect_right —
   the leftmost index where the array is strictly greater than target.

Q: Can you find the first AND last position of target if it may repeat
   (LC 34)?
A: Run bisect_left(target) and bisect_right(target); if they're equal, target
   isn't present, otherwise the range [bisect_left, bisect_right) is every
   occurrence.

Q: Why is this the same as Python's `bisect.bisect_left`?
A: Because it computes exactly the same leftmost-True boundary; `bisect_left`
   is this template, implemented in C for speed. Worth citing to show you
   know the stdlib exists, while still being able to write it by hand.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 704  Binary Search                    — the exact-match shape (001 here)
    LC 34   Find First and Last Position     — bisect_left AND bisect_right together
    LC 981  Time Based Key-Value Store       — bisect_right - 1 over timestamps
                                                 (009 here)
================================================================================
"""

import bisect
import random
import time
from typing import List


class Solution:
    def searchInsert(self, nums: List[int], target: int) -> int:
        """Leftmost-True binary search (bisect_left by hand). O(log n) time,
        O(1) space. See THE CORE IDEA above."""
        lo, hi = 0, len(nums)
        while lo < hi:
            mid = (lo + hi) // 2
            if nums[mid] >= target:
                hi = mid
            else:
                lo = mid + 1
        return lo

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def searchInsert_linear(self, nums: List[int], target: int) -> int:
        """O(n) oracle: first index whose value is >= target."""
        for i, x in enumerate(nums):
            if x >= target:
                return i
        return len(nums)

    def searchInsert_stdlib(self, nums: List[int], target: int) -> int:
        """The stdlib equivalent, for cross-checking. Same algorithm, in C."""
        return bisect.bisect_left(nums, target)


# ==============================================================================
# TESTS — run:  python 002_search_insert_position_solution.py
# ==============================================================================
CASES = [
    ([1, 3, 5, 6], 5, 2),
    ([1, 3, 5, 6], 2, 1),
    ([1, 3, 5, 6], 7, 4),
    ([1, 3, 5, 6], 0, 0),
    ([1], 1, 0),
    ([1], 0, 0),
    ([1], 2, 1),
    ([1, 3, 5, 6], 6, 3),
    ([1, 3, 5, 6], 1, 0),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness ---")
    for nums, target, expected in CASES:
        got = sol.searchInsert(nums, target)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<20} target={target:<5} "
              f"-> {got}  (want {expected})")

    print("\n--- cross-check vs. bisect.bisect_left ---")
    for nums, target, _ in CASES:
        want = sol.searchInsert_stdlib(nums, target)
        got = sol.searchInsert(nums, target)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  vs stdlib nums={nums!r:<20} target={target:<5} -> {got} (stdlib {want})")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums=[1,3,5,6], target=2 (not present) ---")
    nums, target = [1, 3, 5, 6], 2
    lo, hi = 0, len(nums)
    print(f"  {'lo':>3} {'hi':>3} {'mid':>4} {'nums[mid]':>10}")
    while lo < hi:
        mid = (lo + hi) // 2
        cond = nums[mid] >= target
        print(f"  {lo:>3} {hi:>3} {mid:>4} {nums[mid]:>10}   nums[mid]>=target? {cond}")
        if cond:
            hi = mid
        else:
            lo = mid + 1
    print(f"  final lo == hi == {lo} -> insert at index {lo}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs. linear-scan and bisect_left ---")
    random.seed(3)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(0, 30)
        nums = sorted(random.sample(range(-100, 100), n))
        target = random.randint(-150, 150)
        a = sol.searchInsert(nums, target)
        b = sol.searchInsert_linear(nums, target)
        c = sol.searchInsert_stdlib(nums, target)
        if not (a == b == c):
            mismatches += 1
    print(f"  {trials} random sorted arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(log n) vs O(n).
    # ----------------------------------------------------------------------
    print("\n--- O(log n) binary search vs O(n) linear scan: measured runtime ---")
    print(f"  {'n':>9} {'binary(us)':>12} {'linear(us)':>12} {'speedup':>10}")
    for n in (10_000, 100_000, 1_000_000, 5_000_000):
        nums = list(range(0, 2 * n, 2))     # sorted, dense, even numbers
        target = n - 1                       # forces a real mid-array insertion
        reps = 200
        t0 = time.perf_counter()
        for _ in range(reps):
            sol.searchInsert(nums, target)
        t1 = time.perf_counter()
        for _ in range(reps):
            sol.searchInsert_linear(nums, target)
        t2 = time.perf_counter()
        bin_us = (t1 - t0) / reps * 1_000_000
        lin_us = (t2 - t1) / reps * 1_000_000
        speedup = lin_us / bin_us if bin_us > 0 else float("inf")
        print(f"  {n:>9} {bin_us:>10.2f}us {lin_us:>10.2f}us {speedup:>9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
