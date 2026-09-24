"""
================================================================================
SOLUTION · LeetCode 1985 · Find the Kth Largest Integer in a String  [Medium]
https://leetcode.com/problems/find-the-kth-largest-integer-in-a-string/
================================================================================

THE CORE IDEA
--------------
These are digit strings representing non-negative integers with NO leading
zeros, and they must be compared NUMERICALLY, not lexicographically. Python's
default string `<`/`>` compares character by character, which agrees with
numeric order ONLY when the two strings have equal length -- the moment
lengths differ, string comparison is wrong: `"9" > "10"` as strings (because
`'9' > '1'` at position 0) but `9 < 10` as numbers. The fix is a single
two-part comparator: **compare lengths first; only fall back to plain string
comparison when lengths are equal** (equal-length numeric strings compare
correctly digit-by-digit, since that's the same as place-by-place). This
comparator, once correct, plugs into Quickselect exactly the way `<` plugs
into a numeric Quickselect -- the "k-th order statistic without a full sort"
technique this topic already established in 005 Wiggle Sort II, here applied
to a custom ordering instead of the natural one.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (sort by int value, price it): `sorted(nums, key=int,
reverse=True)[k-1]` -- O(n log n) time, always correct because `int()`
side-steps the comparator trap entirely. This is a perfectly reasonable
answer to open with; the interviewer's real question is whether you can beat
O(n log n) when only ONE order statistic is needed, same framing as 005.

Approach 0b (heap of size k, price it): push onto a min-heap keyed by
`(len(s), s)` and pop when size exceeds k -- O(n log k) time, O(k) space.
Better than full sort when k is small relative to n, worse than Quickselect
asymptotically when k is a substantial fraction of n. `_heap_kth_largest`
below implements this for the comparison demo.

Approach 1 (chosen) -- Quickselect with a custom `(length, value)` comparator.
Partition nums (on a COPY) using "greater than" defined as: longer string
wins; equal length falls back to plain string comparison. Recurse into the
side containing the k-th largest, same random-pivot partition-and-discard
scheme as 005's median-finding step. O(n) expected time, O(n) space for the
working copy (or O(1) extra beyond it, in place on that copy).


================================================================================
STEP BY STEP TRACE
================================================================================
nums = ["2", "21", "12", "1"], k = 3. We want the value at position k-1 = 2
when nums is conceptually sorted DESCENDING by numeric value.

Comparator `_greater(a, b)`: True if a is numerically greater than b.
    _greater("21", "2")  -> len 2 > len 1           -> True  (21 > 2)
    _greater("12", "2")  -> len 2 > len 1           -> True  (12 > 2)
    _greater("2", "1")   -> len 1 == len 1, "2">"1"  -> True  (2 > 1)

Quickselect target index (descending order, 0-indexed): k - 1 = 2.

arr = ["2", "21", "12", "1"], lo=0, hi=3.
Pick pivot_idx = 1 (value "21"). Partition so everything "greater than 21"
(by our comparator) moves left, everything else moves right, pivot lands at
its sorted-descending position:
    compare "2"  vs "21" -> not greater -> stays right side
    compare "12" vs "21" -> len 2 == len 2, "12" < "21" -> not greater
    compare "1"  vs "21" -> not greater
    no element is greater than "21" -> pivot "21" swaps to position 0.
    arr becomes: ["21", "2", "12", "1"], pivot final index = 0.

pivot index 0 < target 2 -> recurse into arr[1:], target shifts to 2-1=1...
(implementation recurses with an absolute k' relative to the subrange, shown
here conceptually) -- keep lo=1, hi=3, target index (absolute) = 2.

arr = ["21", "2", "12", "1"], lo=1, hi=3.
Pick pivot_idx = 2 (value "12"). Compare arr[1]="2" and arr[3]="1" against
"12":
    "2" vs "12"  -> len 1 < len 2 -> not greater
    "1" vs "12"  -> len 1 < len 2 -> not greater
    nothing greater than "12" in [1,3) -> pivot "12" swaps to position 1.
    arr becomes: ["21", "12", "2", "1"], pivot final index = 1.

pivot index 1 < target 2 -> recurse into [2, 3], lo=2, hi=3.
Pick pivot_idx=2 (value "2"). Range [2,2) is empty to scan -> pivot "2"
stays at index 2, which EQUALS target index 2 -> return arr[2] = "2".

Result: "2" -- matches the expected 3rd-largest value from the fully sorted
descending list ["21", "12", "2", "1"].


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time            Space   Mutates input?
    --------------------------------  --------------  ------  --------------
    Sort by int(s), reverse [priced]   O(n log n)      O(n)    no (new list)
    Heap of size k [priced]            O(n log k)      O(k)    no
    Quickselect + comparator [chosen]  O(n) expected   O(n)    no (copy only)

    Quickselect runs on an internal COPY of nums specifically so the
    original input list is never reordered -- matching this problem's
    signature, which returns a value rather than sorting in place.


================================================================================
EDGE CASES
================================================================================
    all same length             -> comparator degenerates to plain string
                                    comparison, which is already numerically
                                    correct for equal-length digit strings.
    k == 1                      -> largest value; Quickselect still recurses
                                    correctly, just skews to the "always
                                    greater" side.
    k == len(nums)              -> smallest value; symmetric to k == 1.
    single-element input        -> Quickselect's base case (lo == hi)
                                    returns immediately, no partitioning.
    "0" present alongside multi-digit numbers -> "0" has length 1, so it is
                                    correctly treated as smaller than any
                                    longer numeric string, and no leading-
                                    zero ambiguity exists per the problem's
                                    "no leading zeros" guarantee.
    duplicate values             -> counted distinctly per the problem
                                    statement (e.g. ["2","2"] with k=2 must
                                    return "2", not treat duplicates as one
                                    entry) -- the comparator and Quickselect
                                    both naturally handle duplicates as
                                    equal-priority elements, no special case
                                    needed.


================================================================================
COMMON MISTAKES
================================================================================
1. Using plain `sorted(nums, reverse=True)` or `max(nums)` directly on the
   strings -- this is the entire trap: `"9" > "10"` lexicographically but
   `9 < 10` numerically, so any mixed-length input silently returns a wrong
   answer. Demonstrated live below.
2. Converting every string to `int` unconditionally for comparisons buried
   deep in a hot loop -- correct, but throws away the O(n) Quickselect
   opportunity and repeatedly re-parses the same strings; fine for the O(n
   log n) baseline, wasteful if you were asked to beat it.
3. Writing the comparator as "compare string values, then break ties by
   length" (backwards order) -- length must be checked FIRST; comparing
   string values first re-introduces the exact lexicographic bug this
   problem tests for.
4. Off-by-one on which index Quickselect targets for "k-th LARGEST" --
   easy to accidentally target the k-th SMALLEST (index k-1 ascending)
   instead of descending; verify against a small hand-traced example before
   trusting the index arithmetic.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if the strings could have leading zeros?" -> the length-first
  comparator breaks, since "007" and "7" represent the same value with
  different lengths; you'd need to strip leading zeros before comparing (or
  compare by int value directly), losing the string-comparator's O(1)
  length check as a numeric proxy.
- "What if k is very large and nums is a live stream, not a fixed array?" ->
  Quickselect assumes random access to a fixed collection; a streaming
  version would need a min-heap of size k (this problem's Approach 0b),
  which handles insertion order naturally at O(log k) per element.
- "Can you avoid the O(n) auxiliary copy?" -> yes, partition nums itself in
  place with the comparator instead of a copy -- trades "does not mutate
  input" for O(1) extra space; a valid trade to discuss if the interviewer
  says mutation is acceptable.


================================================================================
RELATED PROBLEMS
================================================================================
- Kth Largest Element in an Array (LC 215) -- the same Quickselect skeleton
  with the NATURAL numeric comparator instead of a custom one.
- 005 Wiggle Sort II (this topic) -- Quickselect finding a median instead of
  an arbitrary k-th order statistic, same random-pivot partition scheme.
- Top K Frequent Elements (LC 347, topic 01/12) -- another "don't fully sort,
  you only need k of them" problem, usually solved with a heap instead.
================================================================================
"""

import random
import time


class Solution:
    def kthLargestNumber(self, nums: list[str], k: int) -> str:
        arr = list(nums)
        n = len(arr)
        # k-th LARGEST, 0-indexed from the front of a DESCENDING ordering.
        target = k - 1
        lo, hi = 0, n - 1
        while True:
            pivot_idx = random.randint(lo, hi)
            pivot_idx = self._partition(arr, lo, hi, pivot_idx)
            if pivot_idx == target:
                return arr[pivot_idx]
            elif pivot_idx < target:
                lo = pivot_idx + 1
            else:
                hi = pivot_idx - 1

    @staticmethod
    def _greater(a: str, b: str) -> bool:
        """True if numeric string a > numeric string b. Length decides it
        first; equal-length numeric strings compare correctly as plain
        strings (same as comparing digit by digit / place by place)."""
        if len(a) != len(b):
            return len(a) > len(b)
        return a > b

    @classmethod
    def _partition(cls, arr: list[str], lo: int, hi: int, pivot_idx: int) -> int:
        """Lomuto partition ordering arr[lo:hi+1] so that everything
        NUMERICALLY GREATER than the pivot ends up to its left (i.e.
        partitions for a DESCENDING arrangement, matching 'k-th largest')."""
        pivot = arr[pivot_idx]
        arr[pivot_idx], arr[hi] = arr[hi], arr[pivot_idx]
        store = lo
        for i in range(lo, hi):
            if cls._greater(arr[i], pivot):
                arr[store], arr[i] = arr[i], arr[store]
                store += 1
        arr[store], arr[hi] = arr[hi], arr[store]
        return store


def _sort_by_int_reverse(nums: list[str], k: int) -> str:
    """The O(n log n) baseline: convert to int for comparison, sort
    descending, take index k-1. Always correct, never fooled by length."""
    return sorted(nums, key=int, reverse=True)[k - 1]


def _heap_kth_largest(nums: list[str], k: int) -> str:
    """O(n log k) alternative: maintain a min-heap of the k largest seen so
    far, keyed by (length, value) so the heap orders numerically too."""
    import heapq

    heap: list[tuple[int, str]] = []
    for s in nums:
        key = (len(s), s)
        if len(heap) < k:
            heapq.heappush(heap, (key, s))
        elif key > heap[0][0]:
            heapq.heapreplace(heap, (key, s))
    return heap[0][1]


def _buggy_lexicographic_kth_largest(nums: list[str], k: int) -> str:
    """The bug this whole problem is about: plain string sort, no length
    awareness. Kept only to demonstrate the failure live, never shipped."""
    return sorted(nums, reverse=True)[k - 1]


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        (["3", "6", "7", "10"], 4, "3"),
        (["2", "21", "12", "1"], 3, "2"),
        (["1", "1", "1"], 2, "1"),
        (["0"], 1, "0"),
        (["9", "10"], 1, "10"),
        (["9", "10"], 2, "9"),
        (["100", "10", "2", "3"], 1, "100"),
    ]
    for nums, k, expected in cases:
        result = sol.kthLargestNumber(list(nums), k)
        ok = result == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  kthLargestNumber({nums}, {k}) "
              f"-> {result!r} (expected {expected!r})")

    print()
    print("CROSS-CHECK -- Quickselect vs sort-by-int vs heap agree on random inputs")
    print("-" * 72)
    random.seed(11)
    cross_ok = True
    mismatches = 0
    for _ in range(500):
        n = random.randint(1, 40)
        nums = [str(random.randint(0, 10 ** random.randint(1, 6))) for _ in range(n)]
        k = random.randint(1, n)
        qs = sol.kthLargestNumber(list(nums), k)
        base = _sort_by_int_reverse(nums, k)
        heap = _heap_kth_largest(nums, k)
        if not (qs == base == heap):
            cross_ok = False
            mismatches += 1
            if mismatches <= 3:
                print(f"MISMATCH  nums={nums} k={k} -> quickselect={qs!r} "
                      f"sort={base!r} heap={heap!r}")
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  500/500 random trials agree across all "
          f"three approaches" if cross_ok else f"FAIL  {mismatches}/500 trials disagreed")

    print()
    print("COMPARATOR BUG DEMO -- plain lexicographic sort vs length-aware order")
    print("-" * 72)
    trap_input = ["9", "10", "2", "100"]
    k = 1
    buggy = _buggy_lexicographic_kth_largest(trap_input, k)
    correct = sol.kthLargestNumber(list(trap_input), k)
    print(f"input={trap_input}, k={k}")
    print(f"  plain string sort (reverse=True): {sorted(trap_input, reverse=True)} "
          f"-> kth-largest = {buggy!r}  [WRONG: ignores numeric length]")
    print(f"  length-aware Quickselect:                              "
          f"-> kth-largest = {correct!r}  [CORRECT: 100 is numerically largest]")
    bug_demonstrated = buggy != correct and correct == "100"
    all_ok &= bug_demonstrated
    print(f"{'PASS' if bug_demonstrated else 'FAIL'}  the comparator bug is real and "
          f"our chosen approach avoids it")

    print()
    print("RUNTIME DEMO -- Quickselect vs full sort-by-int, measured live")
    print("-" * 72)
    n = 200_000
    random.seed(3)
    big = [str(random.randint(0, 10 ** 12)) for _ in range(n)]
    k = n // 2

    t0 = time.perf_counter()
    qs_result = sol.kthLargestNumber(big, k)
    qs_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    sort_result = _sort_by_int_reverse(big, k)
    sort_ms = (time.perf_counter() - t0) * 1000

    print(f"n={n}, k={k}:")
    print(f"  Quickselect (custom comparator): {qs_ms:8.2f} ms")
    print(f"  sort by int(s), reverse=True:    {sort_ms:8.2f} ms")
    if qs_ms < sort_ms:
        print(f"  measured: Quickselect is {sort_ms / qs_ms:.2f}x faster here, "
              f"matching the asymptotic expectation (O(n) vs O(n log n)).")
    else:
        print(f"  measured: sort-by-int is {qs_ms / sort_ms:.2f}x faster here -- "
              f"CPython's C-level Timsort + int() beating a pure-Python "
              f"per-element comparator, a constant-factor artifact like 005's "
              f"finding, not a correctness or asymptotic issue.")
    results_agree = qs_result == sort_result
    all_ok &= results_agree
    print(f"{'PASS' if results_agree else 'FAIL'}  both approaches agree on the answer "
          f"({qs_result!r})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
