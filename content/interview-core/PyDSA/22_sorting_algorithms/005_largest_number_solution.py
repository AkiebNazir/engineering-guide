"""
================================================================================
SOLUTION · LeetCode 179 · Largest Number                              [Medium]
https://leetcode.com/problems/largest-number/
================================================================================

THE CORE IDEA
--------------
This is a sort, but not by NUMERIC value -- it's a sort by a custom
CONCATENATION order, and the whole problem is finding the right comparator.
Sorting numerically descending is wrong: `9` vs `30` numerically says `30`
comes first, but `"930" > "309"`, so `9` should actually come first. The
correct comparator between two numbers `a` and `b` (as strings) asks: which
STRING CONCATENATION is bigger, `a+b` or `b+a`? Sort every number
descending by that pairwise rule, join the results, and that ordering is
provably optimal (an exchange-argument proof: if `a+b > b+a` for every
adjacent pair in the sorted order, no adjacent swap can improve the whole
concatenation, and this pairwise property is transitive for this specific
comparator, so a global sort by it is valid, not just locally greedy).

    def compare(a: str, b: str) -> int:      # for functools.cmp_to_key
        if a + b > b + a:
            return -1   # a should come first
        elif a + b < b + a:
            return 1    # b should come first
        else:
            return 0

    strs = [str(n) for n in nums]
    strs.sort(key=functools.cmp_to_key(compare))
    result = "".join(strs)
    return "0" if result[0] == "0" else result   # all-zeros edge case

The final `"0" if result[0] == "0"` guard exists because if the LARGEST
number sorts to have a leading "0" digit, then EVERY number in the input
must be 0 (nonzero numbers never produce a leading zero when sorted to the
front by this comparator) -- so the whole answer collapses to the single
string `"0"`, not `"000...0"`.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): sort the numbers numerically descending
(`sorted(nums, reverse=True)`), then concatenate their string forms. Fails
on inputs like `[3, 30, 34, 5, 9]` -- numeric-descending order gives
`34,30,9,5,3` -> `"3430953"`, but the correct answer is `"9534330"`. Wrong
because numeric magnitude doesn't determine which digit sequence produces
the bigger concatenation.

Approach 1 (chosen) -- custom pairwise comparator (`a+b` vs `b+a`), sorted
via `functools.cmp_to_key`. O(n log n) comparisons, each comparison costs
O(k) string work (k = max digit length, since string concatenation and
comparison are linear in length), giving O(n log n * k) total. Space
O(n * k) for the string forms. The answer; shown above and coded below.

Approach 2 -- same comparator, but implemented as a from-scratch merge
sort (reusing problem 002's merge-sort skeleton, comparator-injected
instead of `<=`) rather than relying on Python's `sort`/`cmp_to_key`.
Demonstrates that the comparator is the only moving part -- the sorting
ENGINE underneath is interchangeable, whether it's Timsort via
`cmp_to_key` or a hand-rolled merge sort. Same O(n log n * k) complexity.
Coded below as a variant, and cross-checked against Approach 1.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [3, 30, 34, 5, 9]  ->  strs = ["3","30","34","5","9"]

    pairwise comparisons the sort needs (illustrative, not the full sort's
    exact comparison sequence, which depends on Timsort's internals):

    "9"  vs "34": "934" > "349" -> "9" first
    "34" vs "3" : "343" > "334" -> "34" first
    "34" vs "30": "3430" > "3034" -> "34" first
    "5"  vs "34": "534" > "345" -> "5" first
    "9"  vs "5" : "95" > "59" -> "9" first
    "30" vs "3" : "303" < "330" -> "3" first (30 loses to plain "3")

    sorted descending by this comparator: ["9","5","34","3","30"]
    join: "9" + "5" + "34" + "3" + "30" = "9534330"

    result[0] = "9" != "0" -> no all-zero correction needed
    final: "9534330"  ✓ matches expected output


nums = [0, 0]  ->  strs = ["0","0"]
    "0"+"0" == "0"+"0" -> tie, order doesn't matter
    join: "00"
    result[0] == "0" -> collapse to "0"
    final: "0"


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time                Space    Mutates input?
    -----------------------------------------------------------------------------
    Numeric-descending sort [wrong]  O(n log n)           O(n)     no
    Comparator sort (cmp_to_key) ✅  O(n log n * k)        O(n * k) no
    Comparator merge sort (custom)   O(n log n * k)        O(n * k) no

    n = count of numbers, k = max digit-string length among them
    (string concatenation/comparison inside the comparator costs O(k)).


================================================================================
EDGE CASES
================================================================================
    all zeros, e.g. [0,0,0]  -> every pairwise concatenation ties ("00" ==
                                "00"); sorted output is "000", but the
                                correct answer is "0" -- the leading-zero
                                guard MUST catch this, not just single-zero
                                inputs.
    single element             -> no comparisons happen; `str(nums[0])` is
                                already the (trivially correct) answer,
                                including the n==1, nums[0]==0 case.
    numbers that are prefixes
    of each other, e.g. 3,34   -> exactly the case the wrong numeric sort
                                gets backwards; the comparator handles it
                                correctly because it compares the ACTUAL
                                concatenations, not the numeric values.
    numbers of very different
    lengths, e.g. 9 vs 987654  -> "9987654" vs "9879549"... in general the
                                comparator still resolves correctly since
                                it always compares equal-length strings
                                (`a+b` and `b+a` have the same total
                                length by construction, `len(a)+len(b)`).
    duplicate numbers            -> ties in the comparator (return 0) are
                                harmless; any order among exact duplicates
                                produces the same concatenation either way.


================================================================================
COMMON MISTAKES
================================================================================
1. Sorting numerically (by int value) instead of by the `a+b` vs `b+a`
   string comparator -- the single most common wrong-first-instinct
   approach; fails immediately on `[3, 30, 34, 5, 9]`.
2. Sorting the string forms LEXICOGRAPHICALLY (plain string sort, no
   custom comparator) instead of by concatenation -- also wrong, e.g.
   `"9" < "90"` lexicographically would sort "9" before "90", but
   `"990" > "909"` means "9" should come first, which lexicographic
   ordering gets right here by accident but gets WRONG on cases like
   `["10", "2"]` (lexicographic puts "10" first, but "210" > "102" means
   "2" should be first).
3. Forgetting the all-zeros edge case entirely -- returns `"000"` instead
   of `"0"` for `[0, 0, 0]`, a leading-zero result that fails the judge.
4. Implementing the comparator backwards (returning 1 when `a+b > b+a`
   instead of -1) -- silently sorts ascending by the concatenation rule
   instead of descending, producing the SMALLEST valid concatenation
   instead of the largest.
5. Comparing the numbers as ints after concatenating as strings
   (`int(a+b) > int(b+a)`) -- works but throws away the O(k) string-length
   bound and does unnecessary int parsing; also risks mishandling leading
   zeros inside the concatenation during the comparison itself if not
   careful (usually still correct here since it's back to a full string
   round-trip, but it's needless extra work).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why does the `a+b` vs `b+a` comparator actually produce a GLOBALLY
  optimal ordering, not just a locally good pairwise choice?" -> The
  relation "a should precede b" defined by `a+b > b+a` is provably
  transitive for this construction (if a should precede b, and b should
  precede c, then a should precede c) -- that transitivity is exactly what
  makes it valid to feed into a general-purpose comparison sort at all;
  without transitivity, a comparator-based sort's result would be
  order-dependent and not well-defined.
- "What if numbers can be arbitrarily large (bigger than a 64-bit int)?"
  -> No change needed -- the whole approach already operates on STRING
  forms throughout and never parses back to a fixed-width integer, so
  arbitrarily long digit strings work unmodified.
- "Smallest number instead of largest?" -> Flip the comparator's sign
  (ascending by the same `a+b` vs `b+a` rule), then handle a symmetric
  edge case: a result with LEADING zeros followed by nonzero digits is
  actually valid for "smallest" framed as a raw digit string, but if the
  problem means "smallest number, no leading zeros," you'd need to permute
  a nonzero digit to the front separately -- a genuinely different problem
  shape (closer to LC 402/"Remove K Digits" territory), worth flagging as
  not a trivial comparator flip.


================================================================================
RELATED PROBLEMS
================================================================================
- Sort an Array (LC 912, this topic, 002) -- same sorting engine
  (comparator-driven merge sort shown as this problem's Approach 2), here
  fed a domain-specific comparator instead of `<=`.
- Group Anagrams / custom hashable keys (topic 01) -- another case where
  the graded skill is designing the right KEY or comparator, not the
  container operations around it.
- Meeting Rooms / Merge Intervals (topic 19) -- also solved via sorting
  with a custom key (start time), then a greedy scan; different key
  design, same "sort is a means, the key/comparator is the insight" shape.
================================================================================
"""

import functools
import random
import time
from typing import List


class Solution:
    def largestNumber(self, nums: List[int]) -> str:
        """Custom pairwise comparator (a+b vs b+a), sorted via
        functools.cmp_to_key. O(n log n * k) time, O(n * k) space. The
        answer. See THE CORE IDEA above."""
        strs = [str(n) for n in nums]

        def compare(a: str, b: str) -> int:
            if a + b > b + a:
                return -1
            elif a + b < b + a:
                return 1
            return 0

        strs.sort(key=functools.cmp_to_key(compare))
        result = "".join(strs)
        return "0" if result[0] == "0" else result

    # ------------------------------------------------------------------
    # Variant: same comparator, hand-rolled merge sort instead of
    # cmp_to_key -- demonstrates the comparator is the only domain-
    # specific piece; the sorting engine underneath is interchangeable.
    # ------------------------------------------------------------------
    def largestNumber_merge_sort(self, nums: List[int]) -> str:
        strs = [str(n) for n in nums]
        sorted_strs = self._merge_sort(strs)
        result = "".join(sorted_strs)
        return "0" if result[0] == "0" else result

    def _merge_sort(self, arr: List[str]) -> List[str]:
        if len(arr) <= 1:
            return arr
        mid = len(arr) // 2
        left = self._merge_sort(arr[:mid])
        right = self._merge_sort(arr[mid:])
        return self._merge(left, right)

    @staticmethod
    def _merge(left: List[str], right: List[str]) -> List[str]:
        result = []
        i = j = 0
        while i < len(left) and j < len(right):
            # descending order: left[i] should come first if left[i]+right[j] wins
            if left[i] + right[j] >= right[j] + left[i]:
                result.append(left[i])
                i += 1
            else:
                result.append(right[j])
                j += 1
        result.extend(left[i:])
        result.extend(right[j:])
        return result

    # ------------------------------------------------------------------
    # Naive baseline -- priced, not the answer, demonstrably wrong.
    # ------------------------------------------------------------------
    def largestNumber_numeric_sort(self, nums: List[int]) -> str:
        """✗ WRONG -- sorts by numeric value descending, not by
        concatenation order. Kept only to demonstrate the failure live."""
        strs = [str(n) for n in sorted(nums, reverse=True)]
        result = "".join(strs)
        return "0" if result[0] == "0" else result


# ==============================================================================
# TESTS -- run:  python 005_largest_number_solution.py
# ==============================================================================
CASES = [
    ([10, 2], "210"),
    ([3, 30, 34, 5, 9], "9534330"),
    ([0, 0], "0"),
    ([0], "0"),
    ([1], "1"),
    ([432, 43243], "43243432"),
    ([0, 0, 0, 0], "0"),
    ([9, 99, 999], "999999"),
    ([1, 10], "110"),
    ([121, 12], "12121"),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: comparator sort (cmp_to_key) ---")
    for nums, expected in CASES:
        got = sol.largestNumber(nums)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  largestNumber({nums}) -> {got!r} (expected {expected!r})")

    print("\n--- correctness: hand-rolled merge sort with same comparator, cross-checked ---")
    for nums, expected in CASES:
        got = sol.largestNumber_merge_sort(nums)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  merge_sort({nums}) -> {got!r}")

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: [3, 30, 34, 5, 9] ---")
    strs = [str(n) for n in [3, 30, 34, 5, 9]]
    pairs_shown = [("9", "34"), ("34", "3"), ("34", "30"), ("5", "34"), ("9", "5"), ("30", "3")]
    for a, b in pairs_shown:
        winner = a if a + b > b + a else b
        print(f"  compare {a!r} vs {b!r}: {a+b!r} vs {b+a!r} -> {winner!r} first")
    final = sol.largestNumber([3, 30, 34, 5, 9])
    print(f"  sorted order: {sorted(strs, key=functools.cmp_to_key(lambda a, b: -1 if a+b>b+a else (1 if a+b<b+a else 0)))}")
    print(f"  final: {final!r}")

    # ----------------------------------------------------------------------
    # Demo: the naive numeric sort actually failing.
    # ----------------------------------------------------------------------
    print("\n--- demo: numeric-descending sort gives the WRONG answer ---")
    for nums, expected in [([3, 30, 34, 5, 9], "9534330"), ([1, 10], "110"), ([121, 12], "12121")]:
        wrong = sol.largestNumber_numeric_sort(nums)
        right = sol.largestNumber(nums)
        status = "differs from correct (as expected)" if wrong != right else "happens to match here"
        print(f"  nums={nums}: numeric-sort gives {wrong!r}, correct is {right!r} -- {status}")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check (cmp_to_key vs hand-rolled merge sort), 1000 trials ---")
    random.seed(179)
    mismatches = 0
    for _ in range(1000):
        n = random.randint(1, 12)
        nums = [random.randint(0, 9999) for _ in range(n)]
        r1 = sol.largestNumber(nums)
        r2 = sol.largestNumber_merge_sort(nums)
        if r1 != r2:
            mismatches += 1
    print(f"  1000 random arrays: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # Correctness proof via brute force on small inputs (try every
    # permutation, confirm the comparator sort finds the true maximum).
    # ----------------------------------------------------------------------
    import itertools
    print("\n--- brute-force verification: comparator result vs best of all permutations, n<=7 ---")
    random.seed(5)
    brute_mismatches = 0
    trials = 300
    for _ in range(trials):
        n = random.randint(1, 7)
        nums = [random.randint(0, 99) for _ in range(n)]
        got = sol.largestNumber(nums)
        best = max("".join(p) for p in itertools.permutations([str(x) for x in nums]))
        if best[0] == "0":
            best = "0"
        if got != best:
            brute_mismatches += 1
    print(f"  {trials} small random arrays, brute-forced over all permutations: {brute_mismatches} mismatches")
    all_ok &= (brute_mismatches == 0)

    # ----------------------------------------------------------------------
    # Benchmark: comparator sort vs naive numeric sort (naive is WRONG but
    # still timed, to show the comparator's overhead cost of correctness).
    # ----------------------------------------------------------------------
    print("\n--- comparator sort vs numeric sort: measured overhead of correctness ---")
    print(f"  {'n':>10} {'comparator sort':>18} {'numeric sort':>14} {'ratio':>8}")
    random.seed(2)
    for n in (2_000, 8_000, 32_000):
        nums = [random.randint(0, 10**6) for _ in range(n)]
        t0 = time.perf_counter(); sol.largestNumber(nums); t1 = time.perf_counter()
        sol.largestNumber_numeric_sort(nums); t2 = time.perf_counter()
        cmp_ms = (t1 - t0) * 1000
        num_ms = (t2 - t1) * 1000
        ratio = cmp_ms / num_ms if num_ms > 0 else float("inf")
        print(f"  {n:>10} {cmp_ms:>16.2f}ms {num_ms:>12.2f}ms {ratio:>7.2f}x")
    print("  (the comparator sort is slower -- each comparison does O(k) string")
    print("   concatenation work instead of an O(1) int compare -- that overhead")
    print("   is the price of correctness the naive numeric sort skips and fails on.)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
