"""
================================================================================
SOLUTION · LeetCode 912 · Sort an Array                              [Medium]
https://leetcode.com/problems/sort-an-array/
================================================================================

THE CORE IDEA
--------------
This problem is really "implement a comparison sort from scratch, and prove
it's O(n log n)." There is exactly one shape that guarantees O(n log n) in
the WORST case: divide the array into halves, recursively sort each half,
then MERGE the two sorted halves in O(n) -- merge sort. The recursion has
depth log n (halving each time) and does O(n) work per level, for O(n log
n) total, with no data-dependent degeneration: no input can make merge sort
worse than O(n log n), unlike quicksort (see below). That worst-case
GUARANTEE is exactly what this problem is testing, because the built-in
`sorted()`/`.sort()` are explicitly banned -- the interviewer wants to see
you reconstruct the guarantee, not just cite it.

    def merge_sort(arr):
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = merge_sort(arr[:mid])
        right = merge_sort(arr[mid:])
        return merge(left, right)          # O(n) two-pointer merge, LC 21's core

The merge step is IDENTICAL to `mergeTwoLists` (topic 08, LC 21) and to
problem 001 in this folder -- same two-pointer "take the smaller front"
logic, just writing into a fresh array instead of splicing linked-list
pointers or writing from the back of a padded array.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (banned by the problem, price it anyway): `sorted(nums)` /
`nums.sort()`. Python's Timsort is O(n log n) worst case, adaptive
(O(n) on already-sorted or few-run data), and extremely well
constant-factor-tuned in C. The problem explicitly forbids it because the
point is to prove you can build the guarantee yourself.

Approach 1 (chosen) -- merge sort, top-down recursive. O(n log n) worst
case ALWAYS, O(n) extra space (the merge buffers), stable. The answer for
"give me a guarantee," shown above and coded below.

Approach 2 -- quicksort with a RANDOM pivot and a 3-way (Dutch-flag)
partition. O(n log n) EXPECTED time, O(1) extra space beyond the call stack
(in-place partitioning), O(log n) expected stack depth. A fixed pivot
choice (always first/last element) degrades to O(n^2) on adversarial or
already-sorted input; randomizing the pivot makes that adversarial input
impossible to construct in advance. The 3-way partition (grouping
`< pivot`, `== pivot`, `> pivot` in one pass) additionally protects against
the classic "all duplicates" quicksort pathology (a 2-way partition on an
array of all-equal values degenerates to O(n^2); 3-way handles it in
O(n)). Coded below as a variant, since this problem's constraints
(`nums[i]` in [-5*10^4, 5*10^4], n up to 5*10^4 -- lots of possible
duplicates) make that pathology realistic to raise.

Approach 3 -- counting sort, exploiting the BOUNDED value range. Since
`-5*10^4 <= nums[i] <= 5*10^4` is a fixed, small (10^5-wide) range
independent of n, you can count occurrences of every possible value in one
pass and rebuild the sorted array by reading the counts off in order.
O(n + k) time and O(k) space where k = 10^5 is the range width -- a
genuinely different, faster (for this specific bounded-range problem)
complexity class than any comparison sort, at the cost of only working
because the range happens to be small and known. Coded below as a
non-comparison variant and benchmarked against merge sort.

Approach 4 -- heap sort (cross-ref topic 12): build a max-heap in O(n),
then repeatedly pop the max and place it at the end, shrinking the heap.
O(n log n) worst case, TRUE O(1) extra space (sorts in place, unlike merge
sort's O(n) buffers) -- the trade a real systems-programming sort makes
when memory, not time, is the binding constraint. Not coded here (it's
`heapq`'s job in Python and topic 12's focus); named for completeness.


================================================================================
STEP BY STEP TRACE
================================================================================
merge sort on nums = [5, 2, 3, 1]

    split([5,2,3,1])
      -> split([5,2]) -> split([5])=[5]  split([2])=[2]  -> merge([5],[2])=[2,5]
      -> split([3,1]) -> split([3])=[3]  split([1])=[1]  -> merge([3],[1])=[1,3]
    merge([2,5], [1,3]):
      i=0,j=0: 2 vs 1 -> take 1            result=[1]           j=1
      i=0,j=1: 2 vs 3 -> take 2            result=[1,2]         i=1
      i=1,j=1: 5 vs 3 -> take 3            result=[1,2,3]       j=2 (right exhausted)
      left remainder [5] appended          result=[1,2,3,5]

    final: [1,2,3,5]  ✓

quicksort (3-way) on nums = [5,1,1,2,0,0], random pivot happens to pick 1:

    partition around pivot=1:
      < 1 group: [0, 0]
      == 1 group: [1, 1]
      > 1 group: [5, 2]
    recurse on < group ([0,0], already trivially sorted, all equal)
    recurse on > group ([5,2] -> pivot=2 -> <:[] ==:[2] >:[5] -> [2,5])
    concatenate: [0,0] + [1,1] + [2,5] = [0,0,1,1,2,5]  ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time (worst)     Space      Stable?  Mutates input?
    ---------------------------------------------------------------------------------
    Merge sort ✅ (guarantee)       O(n log n)        O(n)       yes      no (new list)
    Quicksort, random+3-way pivot   O(n log n) exp.*  O(log n)   no       yes (in place)
    Counting sort (bounded range)   O(n + k)          O(k)       yes      no (new list)
    Heap sort (named, not coded)    O(n log n)        O(1)       no       yes (in place)

    * Quicksort's worst case is O(n^2); random pivot selection makes that
      worst case have vanishing PROBABILITY rather than eliminating it --
      it is an expected-time guarantee, not a worst-case one, which is the
      key distinction from merge sort's unconditional O(n log n).
    k = value-range width (10^5 for this problem's constraints).


================================================================================
EDGE CASES
================================================================================
    n == 1                -> merge_sort's base case (`len(arr) <= 1`)
                             returns immediately; no merge ever runs.
    all elements equal     -> the pathological case for naive 2-way
                             quicksort (partitions become maximally
                             unbalanced, O(n^2)); 3-way partitioning routes
                             the entire array into the "== pivot" bucket in
                             one pass and recurses on nothing, O(n).
    already sorted          -> a FIXED-pivot quicksort (always first or last
                             element) degrades to O(n^2) here; random pivot
                             selection is specifically the fix, since it
                             makes this input no different from any other
                             from the algorithm's perspective.
    negative numbers        -> counting sort must offset by `-min(nums)`
                             before indexing into the count array; forgetting
                             the offset indexes negative into a Python list,
                             which wraps around silently instead of crashing.
    empty array (n == 0)    -> not reachable per this problem's constraints
                             (n >= 1), but merge_sort's base case handles it
                             for free anyway (`len(arr) <= 1`).


================================================================================
COMMON MISTAKES
================================================================================
1. Using a fixed pivot (e.g. always `arr[0]` or `arr[-1]`) in quicksort --
   passes random test data but is O(n^2) on sorted or reverse-sorted input,
   exactly the kind of adversarial case a judge or interviewer will probe.
2. Using a 2-way (Lomuto/Hoare) partition on data with many duplicates --
   correctness holds but performance degrades toward O(n^2) as duplicate
   density rises; 3-way partitioning is the fix, not a "nice to have."
3. Forgetting the `-min(nums)` offset in counting sort, or hardcoding the
   value range instead of computing it from the actual input -- either
   crashes (IndexError) or silently drops out-of-range values.
4. In merge sort, slicing `arr[:mid]` / `arr[mid:]` recursively without
   noticing this itself costs O(n) per level (Python slicing copies) --
   still O(n log n) total, but worth being able to say out loud, since an
   interviewer may ask you to convert to index-range recursion over ONE
   shared array to avoid the slicing overhead.
5. Forgetting to append the LEFTOVER elements after one side of the merge
   exhausts (`result.extend(left[i:]); result.extend(right[j:])`) -- silently
   truncates the tail of whichever half finishes second, same bug class as
   LC 21's merge.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why merge sort over quicksort here?" -> The problem's own phrasing ("you
  must solve... in O(n log n)") is a worst-case time bound; quicksort only
  offers that in expectation. Merge sort is the textbook-correct answer
  when a WORST-CASE bound is explicitly demanded, at the cost of O(n) extra
  space vs quicksort's in-place O(log n) stack.
- "Can you sort in O(1) extra space?" -> Heap sort: O(n log n) worst case,
  truly in-place, unstable. In-place merge sort exists but is significantly
  more complex (in-place merging is not straightforward) and rarely worth
  implementing by hand in an interview.
- "The value range is small and known -- can you beat O(n log n)?" ->
  Counting sort, O(n + k). This is the direct bridge to topic 21's Sieve of
  Eratosthenes idea: trade a little extra space for a fundamentally
  different, faster complexity class when the domain is bounded.
- "What if the array doesn't fit in memory?" -> External merge sort: sort
  chunks that DO fit in memory, write each sorted chunk to disk, then
  k-way merge the chunks -- the same merge-sort recursion, just with the
  base case being "chunk fits in RAM" instead of "array length <= 1".


================================================================================
RELATED PROBLEMS
================================================================================
- Merge Two Sorted Lists (LC 21, topic 08, 002) and Merge Sorted Array
  (this topic, 001) -- both ARE the merge step used here, in different
  containers.
- Sort List (LC 148, this topic, 004) -- this exact merge sort, applied to
  a linked list instead of an array (splitting via fast/slow pointer
  instead of index midpoint).
- Kth Largest Element (topic 27, Quickselect family) -- the partition step
  used here in quicksort, without the "recurse on both sides" -- recursing
  on only the side that contains the target index turns O(n log n) into
  expected O(n).
- Count of Smaller Numbers After Self (this topic, 008) -- an augmented
  merge sort: counts cross-inversions DURING the merge step instead of
  just producing sorted output.
- Sieve of Eratosthenes (topic 21, 008) -- the same "trade space for a
  faster complexity class over a bounded domain" idea as counting sort.
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def sortArray(self, nums: List[int]) -> List[int]:
        """Merge sort. O(n log n) worst-case time, O(n) extra space,
        stable, does NOT mutate the input (returns a new list). The
        answer -- the only shape here with an unconditional worst-case
        guarantee. See THE CORE IDEA above."""
        if len(nums) <= 1:
            return list(nums)
        return self._merge_sort(nums)

    def _merge_sort(self, arr: List[int]) -> List[int]:
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = self._merge_sort(arr[:mid])
        right = self._merge_sort(arr[mid:])
        return self._merge(left, right)

    @staticmethod
    def _merge(left: List[int], right: List[int]) -> List[int]:
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            if left[i] <= right[j]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    # ------------------------------------------------------------------
    # Variant: quicksort, random pivot + 3-way (Dutch-flag) partition.
    # O(n log n) expected time, O(log n) expected extra space, in-place,
    # unstable. Protected against both adversarial-order AND duplicate-
    # heavy pathologies.
    # ------------------------------------------------------------------
    def sortArray_quicksort(self, nums: List[int]) -> List[int]:
        arr = list(nums)
        self._quicksort(arr, 0, len(arr) - 1)
        return arr

    def _quicksort(self, arr: List[int], lo: int, hi: int) -> None:
        while lo < hi:
            pivot_idx = random.randint(lo, hi)
            arr[lo], arr[pivot_idx] = arr[pivot_idx], arr[lo]
            pivot = arr[lo]

            lt, gt, i = lo, hi, lo  # arr[lo:lt] < pivot, arr[lt:i] == pivot, arr[gt+1:hi+1] > pivot
            while i <= gt:
                if arr[i] < pivot:
                    arr[lt], arr[i] = arr[i], arr[lt]
                    lt += 1
                    i += 1
                elif arr[i] > pivot:
                    arr[gt], arr[i] = arr[i], arr[gt]
                    gt -= 1
                else:
                    i += 1

            # Recurse on the smaller side, loop on the larger side, to
            # cap the call stack at O(log n) expected depth.
            if lt - lo < hi - gt:
                self._quicksort(arr, lo, lt - 1)
                lo = gt + 1
            else:
                self._quicksort(arr, gt + 1, hi)
                hi = lt - 1

    # ------------------------------------------------------------------
    # Variant: counting sort, exploiting the bounded value range.
    # O(n + k) time, O(k) space, where k = value-range width.
    # ------------------------------------------------------------------
    def sortArray_counting(self, nums: List[int]) -> List[int]:
        if not nums:
            return []
        lo, hi = min(nums), max(nums)
        k = hi - lo + 1
        counts = [0] * k
        for v in nums:
            counts[v - lo] += 1
        result = []
        for offset, c in enumerate(counts):
            if c:
                result.extend([offset + lo] * c)
        return result

    # ------------------------------------------------------------------
    # Naive baseline -- priced, not the answer, forbidden by the problem.
    # ------------------------------------------------------------------
    def sortArray_builtin(self, nums: List[int]) -> List[int]:
        """✗ FORBIDDEN by the problem statement. Timsort, O(n log n)
        worst case, adaptive, C-implemented. Used only as an oracle for
        the cross-checks below."""
        return sorted(nums)


# ==============================================================================
# TESTS -- run:  python 002_sort_an_array_solution.py
# ==============================================================================
CASES = [
    [5, 2, 3, 1],
    [5, 1, 1, 2, 0, 0],
    [1],
    [2, 1],
    [-5, -1, -3, 0, 4, 2],
    list(range(20, 0, -1)),
    [7] * 10,
    [3, -3, 3, -3, 0],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: merge sort ---")
    for nums in CASES:
        want = sorted(nums)
        got = sol.sortArray(nums)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  sortArray({nums!r}) -> {got}")

    print("\n--- correctness: quicksort (random+3-way), cross-checked ---")
    random.seed(912)
    for nums in CASES:
        want = sorted(nums)
        got = sol.sortArray_quicksort(nums)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  quicksort({nums!r}) -> {got}")

    print("\n--- correctness: counting sort, cross-checked ---")
    for nums in CASES:
        want = sorted(nums)
        got = sol.sortArray_counting(nums)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  counting({nums!r}) -> {got}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: merge sort on [5,2,3,1] ---")

    def traced_merge_sort(arr, depth=0):
        indent = "  " * depth
        if len(arr) <= 1:
            print(f"{indent}base case: {arr}")
            return arr
        mid = len(arr) // 2
        print(f"{indent}split {arr} -> {arr[:mid]} | {arr[mid:]}")
        left = traced_merge_sort(arr[:mid], depth + 1)
        right = traced_merge_sort(arr[mid:], depth + 1)
        merged = sol._merge(left, right)
        print(f"{indent}merge {left} + {right} -> {merged}")
        return merged

    traced_merge_sort([5, 2, 3, 1])

    # ----------------------------------------------------------------------
    # Randomised cross-check, all four implementations vs sorted().
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (merge / quicksort / counting), 1000 trials ---")
    random.seed(42)
    mismatches = 0
    for _ in range(1000):
        n = random.randint(0, 40)
        nums = [random.randint(-100, 100) for _ in range(n)]
        want = sorted(nums)
        r1 = sol.sortArray(nums)
        r2 = sol.sortArray_quicksort(nums)
        r3 = sol.sortArray_counting(nums)
        if not (r1 == r2 == r3 == want):
            mismatches += 1
    print(f"  1000 random arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Duplicate-heavy pathology: 2-way vs 3-way partition quicksort.
    # ----------------------------------------------------------------------
    print("\n--- demo: all-duplicates input, why 3-way partitioning matters ---")
    dup_heavy = [7] * 5000
    t0 = time.perf_counter()
    sol.sortArray_quicksort(dup_heavy)
    dup_ms = (time.perf_counter() - t0) * 1000
    print(f"  3-way quicksort on 5000 identical values: {dup_ms:.2f}ms")
    print("  (a naive 2-way Lomuto partition on this input recurses n times with")
    print("   each partition removing only 1 element -- O(n^2) -- 3-way removes")
    print("   the whole array into the '== pivot' bucket in a single pass, O(n).)")

    # ----------------------------------------------------------------------
    # Benchmark: O(n log n) merge sort vs O(n^2) insertion sort.
    # ----------------------------------------------------------------------
    def insertion_sort(nums):
        arr = list(nums)
        for i in range(1, len(arr)):
            key = arr[i]
            j = i - 1
            while j >= 0 and arr[j] > key:
                arr[j + 1] = arr[j]
                j -= 1
            arr[j + 1] = key
        return arr

    print("\n--- O(n log n) merge sort vs O(n^2) insertion sort: measured runtime ---")
    print(f"  {'n':>8} {'merge sort':>12} {'insertion sort':>16} {'ratio':>8}")
    random.seed(7)
    for n in (500, 1_000, 2_000):
        data = [random.randint(-10**6, 10**6) for _ in range(n)]
        t0 = time.perf_counter(); sol.sortArray(data); t1 = time.perf_counter()
        insertion_sort(data); t2 = time.perf_counter()
        ms_ms = (t1 - t0) * 1000
        is_ms = (t2 - t1) * 1000
        ratio = is_ms / ms_ms if ms_ms > 0 else float("inf")
        print(f"  {n:>8} {ms_ms:>10.2f}ms {is_ms:>14.2f}ms {ratio:>7.2f}x")
    print("  (as n doubles, insertion sort's O(n^2) cost should roughly quadruple")
    print("   while merge sort's O(n log n) cost barely more than doubles -- this")
    print("   growing ratio IS the complexity gap made visible, not asserted.)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
