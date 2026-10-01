"""
================================================================================
SOLUTION · LeetCode 75 · Sort Colors                                  [Medium]
https://leetcode.com/problems/sort-colors/
================================================================================

THE CORE IDEA
--------------
This is the exact 3-way partition used INSIDE problem 002's 3-way
quicksort, except the "pivot" is fixed in advance to the value 1 (since
there are only ever three possible values, 0/1/2) -- so you never need to
choose or compare against an arbitrary pivot, and one linear pass with
THREE pointers finishes the job: `low` is the boundary past which
everything is a confirmed 0, `high` is the boundary before which
everything is a confirmed 2, and `mid` is the current scan cursor walking
through the unclassified middle region.

    low, mid, high = 0, 0, len(nums) - 1
    while mid <= high:
        if nums[mid] == 0:
            nums[low], nums[mid] = nums[mid], nums[low]
            low += 1; mid += 1        # low's old value is 0 or 1, safe to advance mid too
        elif nums[mid] == 2:
            nums[mid], nums[high] = nums[high], nums[mid]
            high -= 1                  # do NOT advance mid -- the swapped-in value is unexamined
        else:  # nums[mid] == 1
            mid += 1

The asymmetry between the `== 0` and `== 2` branches is the entire trick:
swapping with `low` is safe to also advance `mid`, because everything
`nums[low]` could have held before the swap is already known to be 0 or 1
(never a 2) -- `low` never runs ahead of `mid`. Swapping with `high` is
NOT safe to advance `mid`, because `nums[high]` could hold anything (0, 1,
or 2) that hasn't been classified yet; the freshly swapped-in value at
`mid` must be re-examined on the NEXT loop iteration.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (banned by the problem, price it anyway): `nums.sort()`. Correct,
O(n log n) -- wildly more work than necessary for a value domain of size 3;
a general-purpose comparison sort doesn't know or exploit that there are
only 3 distinct values possible.

Approach 1 -- counting sort (two-pass): count 0s, 1s, 2s in one pass, then
overwrite the array with that many 0s, then 1s, then 2s in a second pass.
O(n) time, O(1) extra space (just 3 counters), fully correct and simple to
reason about -- but it's TWO passes over the array, and the problem's
follow-up specifically asks for one pass.

Approach 2 (chosen) -- Dutch National Flag, three pointers, ONE pass. O(n)
time, O(1) extra space, exactly one linear scan. The answer; shown above
and coded below. Named after Dijkstra's original formulation of this exact
partitioning problem (sorting a flag's three colored stripes).


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [2, 0, 2, 1, 1, 0]

    low=0 mid=0 high=5   nums=[2,0,2,1,1,0]
    mid=0: nums[0]=2 -> swap(mid,high)=swap(0,5) -> [0,0,2,1,1,2], high=4 (mid NOT advanced)
    mid=0: nums[0]=0 -> swap(low,mid)=swap(0,0) -> [0,0,2,1,1,2], low=1, mid=1
    mid=1: nums[1]=0 -> swap(low,mid)=swap(1,1) -> [0,0,2,1,1,2], low=2, mid=2
    mid=2: nums[2]=2 -> swap(mid,high)=swap(2,4) -> [0,0,1,1,2,2], high=3 (mid NOT advanced)
    mid=2: nums[2]=1 -> mid=3
    mid=3: nums[3]=1 -> mid=4
    mid(4) > high(3) -> STOP

    final: [0,0,1,1,2,2]  ✓ matches expected output


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time         Space   Passes   Mutates input?
    -------------------------------------------------------------------------
    Built-in sort [priced]         O(n log n)   O(1)*    1(?)     yes
    Counting sort, 2-pass          O(n)         O(1)     2        yes
    Dutch flag, 3-pointer ✅       O(n)         O(1)     1        yes


================================================================================
EDGE CASES
================================================================================
    all one color            -> e.g. all 1s: mid walks the whole array
                                 through the `== 1` branch, low/high never
                                 move; already-sorted output, no swaps.
    already sorted             -> [0,0,1,1,2,2]: every comparison takes the
                                 "correct" branch with a no-op self-swap
                                 where low==mid; still O(n), no bug from
                                 swapping an element with itself.
    reverse sorted              -> [2,2,1,1,0,0]: exercises the `high`
                                 swap-and-recheck path heavily, the part
                                 most likely to be coded wrong (advancing
                                 mid when it shouldn't).
    single element               -> loop body runs at most once (or zero
                                 times if mid > high immediately, impossible
                                 here since mid=0=high for n=1).
    n == 2, e.g. [1, 0]          -> low=0,mid=0,high=1: nums[0]=1 -> mid=1;
                                 nums[1]=0 -> swap(low=0,mid=1) -> [0,1],
                                 low=1,mid=2; mid>high, stop. Correct.


================================================================================
COMMON MISTAKES
================================================================================
1. Advancing `mid` after the `== 2` swap-with-high branch (treating it
   symmetrically with the `== 0` branch) -- the freshly swapped-in value at
   `mid` from the high end is unexamined and could itself be a 0 or another
   2; skipping it silently leaves elements unsorted.
2. Using `mid < high` as the loop condition instead of `mid <= high` --
   drops the very last unexamined element from being classified when
   `mid == high`.
3. Reaching for a full comparison sort out of habit, missing that a
   bounded 3-value domain makes this a partitioning problem, not a general
   sorting problem -- a red flag to an interviewer that you didn't
   recognize the pattern.
4. Two-pass counting sort presented as the final answer without being
   asked to also give the one-pass version -- correct and O(n), but
   doesn't address the explicit one-pass follow-up if the interviewer asks.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Could you come up with a one-pass algorithm using only O(1) constant
  space?" -> Yes -- that's literally the Dutch flag solution above; the
  two-pass counting-sort version is the natural first correct answer, and
  the interviewer is prompting you to collapse it to one pass.
- "Generalize to k colors (k > 3), not just 3." -> The 3-pointer trick is
  specific to exactly 3 buckets. For general k, a two-pass counting sort
  (count each of the k values, then overwrite) is the standard O(n + k)
  answer; a single-pass in-place generalization exists but is
  significantly more intricate (repeated 2-way partitions, one per
  boundary) and rarely expected live.
- "How does this relate to quicksort?" -> It IS quicksort's 3-way
  partition step (problem 002's `_quicksort` in this folder), specialized
  to a pivot value fixed at 1 in advance instead of chosen from the data --
  which is exactly why it can finish in one deterministic pass instead of
  needing recursion.


================================================================================
RELATED PROBLEMS
================================================================================
- Sort an Array (LC 912, this topic, 002) -- the general 3-way quicksort
  partition this problem specializes; also covers counting sort over an
  unbounded-but-small value range.
- Kth Largest Element / Quickselect (topic 27) -- another algorithm built
  from the SAME partition primitive, used to find a rank instead of fully
  sorting.
- Move Zeroes (LC 283, topic 02) -- a simpler 2-way version of this exact
  "partition in place with a slow/fast pointer" pattern.
- Wiggle Sort II (topic 27, 005) -- another problem whose core technique is
  a virtual-index 3-way partition.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def sortColors(self, nums: List[int]) -> None:
        """Dutch National Flag, 3-pointer, one pass. O(n) time, O(1)
        space, in place. The answer. See THE CORE IDEA above."""
        low, mid, high = 0, 0, len(nums) - 1
        while mid <= high:
            if nums[mid] == 0:
                nums[low], nums[mid] = nums[mid], nums[low]
                low += 1
                mid += 1
            elif nums[mid] == 2:
                nums[mid], nums[high] = nums[high], nums[mid]
                high -= 1
            else:
                mid += 1

    # ------------------------------------------------------------------
    # Variant: counting sort, two passes. Simpler, still O(n)/O(1), but
    # not the one-pass answer the follow-up asks for.
    # ------------------------------------------------------------------
    def sortColors_counting(self, nums: List[int]) -> None:
        counts = [0, 0, 0]
        for v in nums:
            counts[v] += 1
        i = 0
        for color in (0, 1, 2):
            for _ in range(counts[color]):
                nums[i] = color
                i += 1


# ==============================================================================
# TESTS -- run:  python 003_sort_colors_solution.py
# ==============================================================================
CASES = [
    [2, 0, 2, 1, 1, 0],
    [2, 0, 1],
    [0],
    [1],
    [2],
    [1, 0],
    [0, 0, 0],
    [2, 2, 2],
    [1, 1, 1],
    [0, 1, 2, 0, 1, 2, 0, 1, 2],
    [2, 1, 0],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: Dutch National Flag, one pass ---")
    for nums in CASES:
        original = list(nums)
        want = sorted(nums)
        arr = list(nums)
        sol.sortColors(arr)
        ok = arr == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  sortColors({original}) -> {arr}")

    print("\n--- correctness: two-pass counting sort, cross-checked ---")
    for nums in CASES:
        want_arr = list(nums)
        sol.sortColors(want_arr)
        got_arr = list(nums)
        sol.sortColors_counting(got_arr)
        ok = got_arr == want_arr
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {nums} -> {got_arr}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [2,0,2,1,1,0] ---")
    arr = [2, 0, 2, 1, 1, 0]
    low, mid, high = 0, 0, len(arr) - 1
    while mid <= high:
        if arr[mid] == 0:
            print(f"  mid={mid} val=0 -> swap(low={low},mid={mid})", end="")
            arr[low], arr[mid] = arr[mid], arr[low]
            low += 1
            mid += 1
            print(f" -> {arr}  low={low} mid={mid} high={high}")
        elif arr[mid] == 2:
            print(f"  mid={mid} val=2 -> swap(mid={mid},high={high})", end="")
            arr[mid], arr[high] = arr[high], arr[mid]
            high -= 1
            print(f" -> {arr}  low={low} mid={mid} high={high} (mid unchanged)")
        else:
            print(f"  mid={mid} val=1 -> mid += 1")
            mid += 1
    print(f"  final: {arr}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (one-pass vs two-pass), 2000 trials ---")
    random.seed(75)
    mismatches = 0
    for _ in range(2000):
        n = random.randint(0, 30)
        nums = [random.randint(0, 2) for _ in range(n)]
        want = sorted(nums)
        a1 = list(nums); sol.sortColors(a1)
        a2 = list(nums); sol.sortColors_counting(a2)
        if not (a1 == a2 == want):
            mismatches += 1
    print(f"  2000 random arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Demo: what breaks if you (wrongly) advance mid on the ==2 branch.
    # ----------------------------------------------------------------------
    print("\n--- demo: the classic bug -- advancing mid after a high-swap ---")

    def buggy_sort_colors(nums):
        low, mid, high = 0, 0, len(nums) - 1
        while mid <= high:
            if nums[mid] == 0:
                nums[low], nums[mid] = nums[mid], nums[low]
                low += 1
                mid += 1
            elif nums[mid] == 2:
                nums[mid], nums[high] = nums[high], nums[mid]
                high -= 1
                mid += 1  # BUG: skips re-examining the swapped-in value
            else:
                mid += 1

    buggy_input = [2, 0, 2, 1, 1, 0]
    correct_input = list(buggy_input)
    buggy_sort_colors(buggy_input)
    sol.sortColors(correct_input)
    print(f"  input:            {[2, 0, 2, 1, 1, 0]}")
    print(f"  buggy (mid++ too): {buggy_input}")
    print(f"  correct:           {correct_input}")
    if buggy_input != correct_input:
        print("  CONFIRMED: the buggy version leaves the array unsorted --")
        print("  the value swapped in from `high` gets skipped instead of re-checked.")
    else:
        print("  (this particular input happened not to expose the bug; the trace")
        print("   above shows structurally why advancing mid there is unsafe.)")

    # ----------------------------------------------------------------------
    # Benchmark: one-pass Dutch flag vs O(n log n) built-in sort.
    # ----------------------------------------------------------------------
    print("\n--- O(n) Dutch flag vs O(n log n) built-in sort: measured runtime ---")
    print(f"  {'n':>10} {'dutch flag':>12} {'built-in sort':>14} {'ratio':>8}")
    random.seed(3)
    for n in (50_000, 200_000, 800_000):
        data = [random.randint(0, 2) for _ in range(n)]
        arr1 = list(data)
        t0 = time.perf_counter(); sol.sortColors(arr1); t1 = time.perf_counter()
        arr2 = list(data)
        t1b = time.perf_counter(); arr2.sort(); t2 = time.perf_counter()
        df_ms = (t1 - t0) * 1000
        bs_ms = (t2 - t1b) * 1000
        ratio = bs_ms / df_ms if df_ms > 0 else float("inf")
        print(f"  {n:>10} {df_ms:>10.2f}ms {bs_ms:>12.2f}ms {ratio:>7.2f}x")
    print("  (built-in Timsort is C-implemented and often still competitive at")
    print("   these sizes despite doing asymptotically more comparisons -- the")
    print("   Dutch flag win is about being ASYMPTOTICALLY correct and one-pass,")
    print("   report whatever this machine actually measures, not intuition.)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
