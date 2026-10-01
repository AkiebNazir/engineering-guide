"""
================================================================================
SOLUTION · LeetCode 88 · Merge Sorted Array                          [Easy]
https://leetcode.com/problems/merge-sorted-array/
================================================================================

THE CORE IDEA
--------------
This is the MERGE step of merge sort, with a twist: the destination buffer
(`nums1`) already has room for the answer baked in (its trailing `n` slots
are padding), which means you can merge WITHOUT extra space -- but only if
you fill it from the BACK. Filling from the front (the natural way to write
a merge) would overwrite `nums1` values you haven't read yet, because the
real data and the write cursor both start at index 0. Filling from the back
never has that problem: the largest values are placed last-first, and by
the time the write cursor reaches an index that still holds a live `nums1`
value, that value has already been read and compared.

    i, j, k = m - 1, n - 1, m + n - 1      # read-tails of nums1, nums2; write-tail
    while j >= 0:                           # nums2 must be fully drained
        if i >= 0 and nums1[i] > nums2[j]:
            nums1[k] = nums1[i]; i -= 1
        else:
            nums1[k] = nums2[j]; j -= 1
        k -= 1

Note the loop condition is `j >= 0`, not `i >= 0 and j >= 0`. Once `nums2`
is exhausted, whatever remains at the front of `nums1[0:i+1]` is ALREADY in
its correct sorted position relative to itself and needs no copying. But if
`nums1` is exhausted first, the leftover `nums2` values still need to be
written -- so the loop must keep running on `j` alone.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): overwrite `nums1[m:]` with `nums2`, then
call `nums1.sort()`. Correct, O((m+n) log(m+n)) time because it throws away
the fact that both halves are ALREADY sorted -- a full comparison sort is
strictly more work than necessary. Priced and shown in the benchmark below,
never the answer.

Approach 1 (merge into a new array, front-to-back): allocate a temp list,
walk both arrays with two pointers from the front (exactly like LC 21's
`mergeTwoLists`), write the smaller of the two fronts each step, then copy
the temp array back into `nums1`. Correct and O(m+n) time, but O(m+n) EXTRA
space for the temp buffer -- doesn't need it.

Approach 2 (chosen) -- three-pointer merge from the BACK, in place. O(m+n)
time, O(1) extra space. The answer; shown above and coded below.


================================================================================
STEP BY STEP TRACE
================================================================================
nums1 = [1,2,3,0,0,0], m=3     nums2 = [2,5,6], n=3

    i=2 (nums1 tail=3)  j=2 (nums2 tail=6)  k=5 (write tail)

    step 1: nums1[i]=3 vs nums2[j]=6 -> 6 is bigger -> write nums1[5]=6, j=1
            nums1 = [1,2,3,0,0,6]
    step 2: nums1[i]=3 vs nums2[j]=5 -> 5 is bigger -> write nums1[4]=5, j=0
            nums1 = [1,2,3,0,5,6]
    step 3: nums1[i]=3 vs nums2[j]=2 -> 3 is bigger -> write nums1[3]=3, i=1
            nums1 = [1,2,3,3,5,6]
    step 4: nums1[i]=2 vs nums2[j]=2 -> tie, nums1[i] is NOT > nums2[j],
            so nums2 wins the tie -> write nums1[2]=2, j=-1
            nums1 = [1,2,2,3,5,6]
    j < 0 -> loop ends. Remaining nums1[0..1] = [1,2] already in place.

    final: [1,2,2,3,5,6]  ✓ matches expected output


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time            Space    Mutates input?
    ---------------------------------------------------------------------------
    Overwrite tail + built-in sort     O((m+n)log(m+n)) O(1)*    yes (nums1)
    Merge to new array, copy back      O(m+n)          O(m+n)   yes (nums1)
    Three-pointer merge from back ✅   O(m+n)          O(1)     yes (nums1)

    * Python's Timsort itself is in-place on the list but the problem
      constraints call this the version that "wastes" the free structure.


================================================================================
EDGE CASES
================================================================================
    n == 0 (nums2 empty)   -> loop condition `j >= 0` is false immediately;
                              nums1 is already correct, no work needed.
    m == 0 (nums1's real
    data is empty)          -> the `i >= 0` guard short-circuits every
                              comparison to "take nums2"; this correctly
                              copies all of nums2 into nums1's front.
    duplicate / tied values -> the tie-break (`nums1[i] > nums2[j]`, strict)
                              must pick a consistent winner on `==`; picking
                              nums2 on ties happens to preserve nums2's
                              relative order for equal values (a "stable"
                              merge), though the problem doesn't require
                              stability since the values are indistinguishable.
    all of nums2 smaller
    than all of nums1       -> `i` never gets exhausted before `j`; every
                              step goes through the `nums1[i] > nums2[j]`
                              branch until nums2 drains.
    all of nums2 larger
    than all of nums1       -> `i` exhausts immediately (i becomes -1 after
                              one wrong guess); need `i >= 0` in the
                              condition or this indexes nums1[-1] by mistake.


================================================================================
COMMON MISTAKES
================================================================================
1. Merging from the FRONT in place -- overwrites live `nums1` values before
   they've been read, corrupting the merge (the exact reason a from-the-back
   pass is required when merging into the larger of the two buffers).
2. Looping `while i >= 0 and j >= 0` instead of `while j >= 0` -- stops the
   merge early whenever `nums1`'s real values exhaust first, leaving
   unwritten `nums2` values sitting in memory rather than copied into
   `nums1`'s front slots (silently wrong output, e.g. leftover zeros).
3. Forgetting the `i >= 0` guard inside the comparison -- once `i` goes
   negative, `nums1[i]` wraps around to `nums1[-1]`, a subtle
   out-of-bounds-that-doesn't-crash bug specific to Python's negative
   indexing (a language like C/Go would segfault or return garbage instead,
   which is arguably easier to catch).
4. Allocating a new array "to be safe" -- passes the tests but violates the
   O(1) extra space follow-up and misses the whole point of the problem
   (nums1's padding exists specifically to enable an in-place merge).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why merge from the back instead of the front?" -> Because nums1 is both
  the SOURCE (its first m real values) and the DESTINATION (all m+n slots).
  Writing from the front while reading from the front collides -- the write
  cursor catches up to and overwrites unread data. Writing from the back
  never collides because the write cursor always stays at or ahead of both
  read cursors.
- "What if nums1 did NOT have extra padding -- you had to return a new
  merged array instead?" -> Then it degenerates to LC 21's `mergeTwoLists`
  merge, O(m+n) time O(m+n) space, no in-place trick applicable or needed.
- "What if you needed the merge to be stable and nums1/nums2 held records,
  not plain ints?" -> Same algorithm; the tie-break rule (which side wins
  on equal keys) determines which original ordering survives. Comparing
  `<` vs `<=` on the tie flips which array "wins" a tie.


================================================================================
RELATED PROBLEMS
================================================================================
- Merge Two Sorted Lists (LC 21, topic 08 problem 002) -- the same merge
  logic, front-to-back, on linked lists instead of arrays; no "in-place
  from the back" trick applies there because linked lists don't have the
  padding/overwrite problem (you just splice pointers).
- Sort List (LC 148, this topic, problem 004) -- merge sort where THIS
  merge step (front-to-back, into a fresh list) is the inner primitive.
- Sort Colors (LC 75, this topic, problem 003) -- a different in-place,
  O(1)-space rearrangement trick (three-way partition) for a bounded value
  domain.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def merge(self, nums1: List[int], m: int, nums2: List[int], n: int) -> None:
        """Three-pointer merge from the back, in place. O(m+n) time, O(1)
        extra space. The answer. See THE CORE IDEA above."""
        i, j, k = m - 1, n - 1, m + n - 1
        while j >= 0:
            if i >= 0 and nums1[i] > nums2[j]:
                nums1[k] = nums1[i]
                i -= 1
            else:
                nums1[k] = nums2[j]
                j -= 1
            k -= 1

    # ------------------------------------------------------------------
    # Naive baseline -- priced, not the answer.
    # ------------------------------------------------------------------
    def merge_naive_sort(self, nums1: List[int], m: int, nums2: List[int], n: int) -> None:
        """✗ NAIVE -- overwrite the padding, then run a full comparison
        sort. O((m+n) log(m+n)) time; wastes the fact both halves are
        already sorted."""
        nums1[m:] = nums2[:n]
        nums1.sort()


# ==============================================================================
# TESTS -- run:  python 001_merge_sorted_array_solution.py
# ==============================================================================
CASES = [
    ([1, 2, 3, 0, 0, 0], 3, [2, 5, 6], 3),
    ([1], 1, [], 0),
    ([0], 0, [1], 1),
    ([4, 5, 6, 0, 0, 0], 3, [1, 2, 3], 3),
    ([2, 0], 1, [1], 1),
    ([0, 0, 0], 0, [1, 2, 3], 3),
    ([-3, -1, 0, 0, 0], 2, [-2, 2, 4], 3),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: three-pointer merge from the back ---")
    for a, m, b, n in CASES:
        nums1 = list(a)
        want = sorted(a[:m] + b[:n])
        sol.merge(nums1, m, b, n)
        ok = nums1 == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  merge({a!r}, {m}, {b!r}, {n}) -> {nums1}  (want {want})")

    print("\n--- correctness: naive overwrite+sort, cross-checked ---")
    for a, m, b, n in CASES:
        nums1, nums1b = list(a), list(a)
        sol.merge(nums1, m, b, n)
        sol.merge_naive_sort(nums1b, m, b, n)
        ok = nums1 == nums1b
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {a!r} + {b!r} -> {nums1b}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: nums1=[1,2,3,0,0,0] m=3, nums2=[2,5,6] n=3 ---")
    nums1, nums2, m, n = [1, 2, 3, 0, 0, 0], [2, 5, 6], 3, 3
    i, j, k = m - 1, n - 1, m + n - 1
    step = 0
    while j >= 0:
        if i >= 0 and nums1[i] > nums2[j]:
            print(f"  step {step}: nums1[{i}]={nums1[i]} > nums2[{j}]={nums2[j]} -> write {nums1[i]} at k={k}")
            nums1[k] = nums1[i]
            i -= 1
        else:
            print(f"  step {step}: nums2[{j}]={nums2[j]} wins -> write {nums2[j]} at k={k}")
            nums1[k] = nums2[j]
            j -= 1
        k -= 1
        step += 1
        print(f"           nums1 = {nums1}")
    print(f"  final: {nums1}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (three-pointer vs naive), 2000 trials ---")
    random.seed(88)
    mismatches = 0
    for _ in range(2000):
        m = random.randint(0, 15)
        n = random.randint(0, 15)
        a = sorted(random.randint(-50, 50) for _ in range(m))
        b = sorted(random.randint(-50, 50) for _ in range(n))
        nums1a = a + [0] * n
        nums1b = a + [0] * n
        sol.merge(nums1a, m, list(b), n)
        sol.merge_naive_sort(nums1b, m, list(b), n)
        if nums1a != nums1b or nums1a != sorted(a + b):
            mismatches += 1
    print(f"  2000 random (m, n) pairs: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: in-place O(m+n) vs overwrite+sort O((m+n)log(m+n)).
    # ----------------------------------------------------------------------
    print("\n--- in-place back-merge O(n) vs overwrite+sort O(n log n): measured runtime ---")
    print(f"  {'n (each half)':>14} {'back-merge':>14} {'overwrite+sort':>16} {'ratio':>8}")
    random.seed(1)
    for size in (5_000, 20_000, 80_000):
        a = sorted(random.randint(-10**6, 10**6) for _ in range(size))
        b = sorted(random.randint(-10**6, 10**6) for _ in range(size))
        nums1a = a + [0] * size
        t0 = time.perf_counter()
        sol.merge(nums1a, size, list(b), size)
        t1 = time.perf_counter()
        nums1b = a + [0] * size
        sol.merge_naive_sort(nums1b, size, list(b), size)
        t2 = time.perf_counter()
        bm_ms = (t1 - t0) * 1000
        os_ms = (t2 - t1) * 1000
        ratio = os_ms / bm_ms if bm_ms > 0 else float("inf")
        print(f"  {size:>14} {bm_ms:>12.2f}ms {os_ms:>14.2f}ms {ratio:>7.2f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
