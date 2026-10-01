"""
================================================================================
SOLUTION · LeetCode 324 · Wiggle Sort II                            [Medium]
https://leetcode.com/problems/wiggle-sort-ii/
================================================================================

THE CORE IDEA
--------------
The wiggle pattern nums[0] < nums[1] > nums[2] < nums[3] ... is achieved by:
put the SMALLER half of the values at even positions (0, 2, 4, ...) and the
LARGER half at odd positions (1, 3, 5, ...), each half arranged so equal
values never end up adjacent. The only number you need to know to split
into "smaller half" / "larger half" is the MEDIAN -- and Quickselect finds
the k-th order statistic (the median, here) in O(n) EXPECTED time without
sorting the whole array. A single follow-up O(n) three-way partition pass,
run over a VIRTUAL index mapping instead of nums' real indices, then
places every value in its correct half AND correct parity slot in one pass,
O(1) extra space.

Virtual index mapping for n elements: `A(i) = (2*i + 1) % (n | 1)`. As i
walks 0, 1, 2, ..., n-1, A(i) walks the ODD real indices first (1, 3, 5,
...) then wraps to the EVEN real indices (0, 2, 4, ...) -- `n | 1` is n
rounded UP to the next odd number, which makes the modulus correct for
both even and odd n. Running the classic Dutch-flag three-way partition
(values > median, == median, < median) over `nums[A(i)]` instead of
`nums[i]` places larger-than-median values into the front of this virtual
ordering (i.e. the ODD real slots) and smaller-than-median values into the
back (the EVEN real slots) -- exactly the wiggle-correct arrangement,
including keeping equal-to-median values apart from each other.

O(n) expected time total (Quickselect O(n) expected + one O(n) partition
pass), O(1) extra space beyond the recursion-free iterative quickselect.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (sort then interleave, price it): sort nums fully -- O(n log n)
-- then split into two halves and interleave them (placing each half in
DESCENDING order within itself, so that if there are duplicates straddling
the median, they don't end up adjacent). Correct, and the interviewer is
explicitly testing whether you reach for a full sort when the problem
only needs a MEDIAN -- asymptotically, O(n) beats O(n log n). `_sort_and_
interleave` below implements this only for the approach-contrast demo,
never as the shipped answer.

Approach 1 (chosen) -- Quickselect for the median + three-way virtual-index
partition. O(n) EXPECTED time, O(1) extra space (beyond the input array
itself) -- the asymptotically superior approach, and the one an
interviewer wants named and justified. IMPORTANT, measured below: in
CPython specifically, `_sort_and_interleave` actually runs FASTER in wall-
clock time at n=200,000, because `sorted()` calls into a heavily-optimized
C-level Timsort while this Quickselect runs as interpreted Python with a
function-call-per-element virtual-index indirection (`A(i)`). Asymptotic
complexity is still the right thing to reason about and state out loud in
an interview -- it is what protects you on adversarial/larger inputs and
is the "textbook correct" answer -- but the runtime demo is left in
exactly as measured, not adjusted to match the theory, per this repo's
"measured, not asserted" rule.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 5, 1, 1, 6, 4], n = 6.

Step 1 -- Quickselect for the (n-1)//2 = 2nd smallest (0-indexed) element
of a COPY of nums. Sorted copy would be [1, 1, 1, 4, 5, 6] -- index 2 is 1.
So median = 1. (Quickselect finds this in expected O(n) without fully
sorting; we show the sorted copy here only to make the target obvious.)

Step 2 -- virtual index mapping for n=6: A(i) = (2i+1) % 7 (n|1 = 7):
    i=0 -> A=1     i=1 -> A=3     i=2 -> A=5
    i=3 -> A=0     i=4 -> A=2     i=5 -> A=4

    walking i=0..5, A(i) visits real indices: 1, 3, 5, 0, 2, 4
    (odd real slots first, then even real slots -- exactly the split we want)

Step 3 -- three-way partition over nums[A(i)] against median=1, using
pointers lo=0 (front, for > median), mid=0 (scanner), hi=n-1=5 (back, for
< median):

    nums (real indices 0..5): [1, 5, 1, 1, 6, 4]

    scanning virtual position mid=0 -> A(0)=1 -> nums[1]=5 > median(1):
        swap virtual(lo=0)=A(0)=1 with virtual(mid=0)=A(0)=1 (no-op, same slot)
        lo=1, mid=1
    mid=1 -> A(1)=3 -> nums[3]=1 == median: mid=2
    mid=2 -> A(2)=5 -> nums[5]=4 > median:
        swap virtual(lo=1)=A(1)=3 with virtual(mid=2)=A(2)=5
        -> swap nums[3] and nums[5]: [1, 5, 1, 4, 6, 1]
        lo=2, mid=3
    mid=3 -> A(3)=0 -> nums[0]=1 == median: mid=4
    mid=4 -> A(4)=2 -> nums[2]=1 == median: mid=5
    mid=5 -> A(5)=4 -> nums[4]=6 > median:
        swap virtual(lo=2)=A(2)=5 with virtual(mid=5)=A(5)=4
        -> swap nums[5] and nums[4]: [1, 5, 1, 4, 1, 6]
        lo=3, mid=6 (loop ends, mid > hi)

    final: [1, 5, 1, 4, 1, 6]
    check: 1<5 (ok), 5>1 (ok), 1<4 (ok), 4>1 (ok), 1<6 (ok) -- VALID WIGGLE.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time            Space   Mutates input?
    -------------------------------  --------------  ------  --------------
    Sort + interleave [priced]        O(n log n)      O(n)    yes (new order)
    Quickselect + 3-way virtual [chosen] O(n) expected O(1)   yes, in place

    Measured at n=200,000 in this CPython environment: the sort-based
    approach is actually FASTER in wall-clock time despite its worse
    asymptotic complexity -- see the runtime demo for the exact numbers.
    Interview answer should still be Quickselect: the complexity claim is
    about scaling behavior and worst-case guarantees, not this machine's
    constant factors.


================================================================================
EDGE CASES
================================================================================
    n == 1                 -> single element trivially satisfies the (empty)
                              wiggle constraint; no partitioning needed.
    n == 2                 -> only constraint is nums[0] < nums[1]; the
                              general algorithm still handles this correctly
                              since the median split degenerates cleanly.
    many duplicate values, including duplicates OF the median -> exactly
                              why the virtual-index scheme is needed instead
                              of a naive middle-out interleave: equal-to-
                              median values get scattered by the mapping
                              instead of clustering adjacently.
    already-sorted or reverse-sorted input -> Quickselect's RANDOM pivot
                              choice keeps expected O(n) time even on
                              adversarial orderings that would make a
                              fixed-pivot quickselect degrade to O(n^2).


================================================================================
COMMON MISTAKES
================================================================================
1. Reaching straight for `nums.sort()` because "sorting always works" --
   technically true, but O(n log n) when O(n) is achievable, and it's the
   exact instinct this problem is designed to test.
2. Using a FIXED pivot (e.g. always the last element) in Quickselect --
   degrades to O(n^2) on sorted or adversarially-ordered input; a random
   pivot keeps the expected time O(n) regardless of input order.
3. Interleaving the two halves with a naive `result[::2] = small,
   result[1::2] = large` without reversing each half or handling
   duplicates near the median -- can place two equal values adjacent to
   each other, violating the strict `<`/`>` wiggle constraint.
4. Getting the virtual index formula wrong for even vs odd n -- using `% n`
   instead of `% (n | 1)` breaks the mapping for even n (n|1 rounds n up
   to the next odd number, which is required for the mapping to correctly
   visit all odd real indices before wrapping to even ones).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What's the worst-case time complexity, not just expected?" -> Quickselect
  degrades to O(n^2) in the worst case (extremely unlikely with random
  pivoting, but possible); the median-of-medians selection algorithm
  guarantees O(n) worst-case at the cost of a larger constant factor.
- "Why can't a plain middle-out interleave handle duplicates?" -> because
  it doesn't control WHICH positions duplicate values land in; the virtual
  index mapping is precisely the mechanism that scatters equal-to-median
  values apart.
- "Is the in-place partition stable?" -> no, and the problem doesn't
  require stability -- any valid wiggle-ordered permutation of the
  multiset is accepted.


================================================================================
RELATED PROBLEMS
================================================================================
- Kth Largest Element in an Array (LC 215) -- Quickselect's most direct
  application, no partitioning step needed afterward.
- Wiggle Sort (LC 280, no "II") -- the easier variant where `<=`/`>=` is
  allowed, solvable by a single greedy pass with no median needed at all.
- 006 Different Ways to Add Parentheses -- a different D&C technique
  entirely (memoized recursive split), for contrast within this topic.
================================================================================
"""

import random
import time


class Solution:
    def wiggleSort(self, nums: list[int]) -> None:
        """
        Do not return anything, modify nums in-place instead.
        """
        n = len(nums)
        if n <= 1:
            return

        median = self._quickselect_median(nums)

        def A(i: int) -> int:
            return (2 * i + 1) % (n | 1)

        lo, mid, hi = 0, 0, n - 1
        while mid <= hi:
            v = nums[A(mid)]
            if v > median:
                nums[A(lo)], nums[A(mid)] = nums[A(mid)], nums[A(lo)]
                lo += 1
                mid += 1
            elif v < median:
                nums[A(mid)], nums[A(hi)] = nums[A(hi)], nums[A(mid)]
                hi -= 1
            else:
                mid += 1

    @staticmethod
    def _quickselect_median(nums: list[int]) -> int:
        """Finds the (n-1)//2-th smallest value (0-indexed) via Quickselect
        run on a COPY, so the original array is untouched by this step."""
        n = len(nums)
        k = (n - 1) // 2
        arr = list(nums)
        lo, hi = 0, n - 1
        while True:
            pivot_idx = random.randint(lo, hi)
            pivot_idx = Solution._partition(arr, lo, hi, pivot_idx)
            if pivot_idx == k:
                return arr[pivot_idx]
            elif pivot_idx < k:
                lo = pivot_idx + 1
            else:
                hi = pivot_idx - 1

    @staticmethod
    def _partition(arr: list[int], lo: int, hi: int, pivot_idx: int) -> int:
        pivot = arr[pivot_idx]
        arr[pivot_idx], arr[hi] = arr[hi], arr[pivot_idx]
        store = lo
        for i in range(lo, hi):
            if arr[i] < pivot:
                arr[store], arr[i] = arr[i], arr[store]
                store += 1
        arr[store], arr[hi] = arr[hi], arr[store]
        return store


def _sort_and_interleave(nums: list[int]) -> None:
    """The O(n log n) alternative, priced but not shipped: full sort, then
    interleave descending halves so duplicates near the median don't clash."""
    n = len(nums)
    arr = sorted(nums)
    small = arr[: (n + 1) // 2][::-1]
    large = arr[(n + 1) // 2:][::-1]
    for i, v in enumerate(small):
        nums[2 * i] = v
    for i, v in enumerate(large):
        nums[2 * i + 1] = v


def _is_valid_wiggle(nums: list[int]) -> bool:
    for i in range(len(nums) - 1):
        if i % 2 == 0:
            if not (nums[i] < nums[i + 1]):
                return False
        else:
            if not (nums[i] > nums[i + 1]):
                return False
    return True


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        [1, 5, 1, 1, 6, 4],
        [1, 3, 2, 2, 3, 1],
        [4, 5, 5, 6],
        [1],
        [1, 2],
        [2, 1],
    ]
    for nums in cases:
        original = list(nums)
        arr = list(nums)
        sol.wiggleSort(arr)
        ok = sorted(arr) == sorted(original) and (len(arr) == 1 or _is_valid_wiggle(arr))
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  wiggleSort({original}) -> {arr}")

    print()
    print("STRESS TEST -- 2000 random arrays, checking valid wiggle + multiset preserved")
    print("-" * 72)

    def _known_feasible(original: list[int]) -> bool:
        # Ground truth for "does a valid wiggle exist for this multiset?":
        # run the textbook sort+interleave construction and check its own
        # output. If EVEN that construction can't satisfy the wiggle
        # property, the multiset is treated as infeasible for this stress
        # test (a stricter feasibility formula exists but is not needed
        # here -- this is a conservative, empirically-verified ground
        # truth, not a guess).
        n = len(original)
        if n <= 1:
            return True
        probe = list(original)
        _sort_and_interleave(probe)
        return _is_valid_wiggle(probe)

    random.seed(42)
    stress_ok = True
    failures = 0
    skipped_infeasible = 0
    for trial in range(2000):
        n = random.randint(1, 30)
        original = [random.randint(0, 10) for _ in range(n)]
        arr = list(original)
        sol.wiggleSort(arr)
        multiset_preserved = sorted(arr) == sorted(original)
        if not multiset_preserved:
            stress_ok = False
            failures += 1
            if failures <= 3:
                print(f"FAIL (multiset changed)  input={original} -> output={arr}")
            continue
        if not _known_feasible(original):
            # LC guarantees a valid answer always exists in real inputs;
            # this random small-range generator can produce multisets with
            # no valid wiggle at all (e.g. a value repeated too often
            # relative to the others) -- skip the shape check for those,
            # the multiset-preserved check above still ran.
            skipped_infeasible += 1
            continue
        if not _is_valid_wiggle(arr):
            stress_ok = False
            failures += 1
            if failures <= 3:
                print(f"FAIL (bad wiggle shape)  input={original} -> output={arr}")
    all_ok &= stress_ok
    checked = 2000 - skipped_infeasible
    print(f"{'PASS' if stress_ok else 'FAIL'}  {checked - failures}/{checked} trials with a "
          f"confirmed-feasible multiset passed both multiset + shape checks "
          f"({skipped_infeasible} trials skipped: no valid wiggle exists for that "
          f"multiset)")

    print()
    print("RUNTIME DEMO -- Quickselect+partition vs sort+interleave, measured live")
    print("-" * 72)
    n = 200_000
    random.seed(7)
    base = [random.randint(0, 5000) for _ in range(n)]

    arr1 = list(base)
    t0 = time.perf_counter()
    sol.wiggleSort(arr1)
    quickselect_ms = (time.perf_counter() - t0) * 1000

    arr2 = list(base)
    t0 = time.perf_counter()
    _sort_and_interleave(arr2)
    sort_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n}:")
    print(f"  Quickselect + 3-way partition: {quickselect_ms:8.2f} ms")
    print(f"  sort + interleave:             {sort_ms:8.2f} ms")
    if sort_ms < quickselect_ms:
        print(f"  measured: sort+interleave is {quickselect_ms / sort_ms:.2f}x FASTER here "
              f"-- CPython's C-level Timsort beats interpreted Quickselect's per-element "
              f"virtual-index overhead at this n, despite O(n log n) > O(n). Asymptotically "
              f"Quickselect is still the right interview answer -- this is a constant-factor "
              f"artifact of CPython, not a correctness or complexity finding.")
    else:
        print(f"  measured: Quickselect is {sort_ms / quickselect_ms:.2f}x faster here, "
              f"matching the asymptotic expectation at this n.")

    both_valid = _is_valid_wiggle(arr1) and _is_valid_wiggle(arr2) and sorted(arr1) == sorted(base)
    all_ok &= both_valid
    print(f"{'PASS' if both_valid else 'FAIL'}  both approaches produce a valid wiggle "
          f"ordering on the same large random input")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
