"""
================================================================================
SOLUTION · LeetCode 1480 · Running Sum of 1d Array                      [Easy]
https://leetcode.com/problems/running-sum-of-1d-array/
================================================================================

THE CORE IDEA
--------------
Carry a running total and append it at every index:

    total = 0
    out = []
    for x in nums:
        total += x
        out.append(total)
    return out

That loop IS the prefix sum from the topic guide's §1.0, unshifted by one:
`out[i] = prefix[i+1]` in the guide's `prefix[0] = 0` convention. Here there
is no query to answer afterward — the running sum itself is the deliverable,
so the "preprocess once, query O(1) forever" trade from §1.0 collapses to
just the preprocessing half. Problems 002 and 003 are what happens when you
keep the array around and DO something with it.


================================================================================
MULTIPLE APPROACHES
================================================================================

APPROACH 0 · BRUTE FORCE (priced, not really "coded" as a serious option)
    For each index i, re-sum nums[0..i] from scratch:
        out[i] = sum(nums[:i+1])
    That is a fresh O(i) scan for every i, so total work is
    0 + 1 + 2 + ... + (n-1) = O(n^2). It is trivial to write in Python
    (`sum(nums[:i+1])`), which is exactly why it is worth coding here and
    benchmarking against the O(n) version below — the "don't code the brute
    force" advice in the topic guide's siblings applies when coding it is
    expensive; here it is one line, so we code it and MEASURE the gap live.

APPROACH 1 · RUNNING TOTAL INTO A NEW LIST (the one to write in an interview)
    Carry one running total, append into a fresh output list. O(n) time,
    O(n) space for the output (which the problem requires you to return
    anyway, so this is not "extra" space beyond the answer itself).

APPROACH 2 · IN-PLACE ACCUMULATION (LeetCode's own official approach)
    `nums[i] += nums[i-1]` for i from 1 upward, then `return nums`.
    Same O(n) time, but O(1) EXTRA space — no second array is allocated,
    because the output overwrites the input as it is computed. The catch:
    it MUTATES the caller's list. If the caller still holds a reference to
    `nums` after calling `runningSum`, they see it silently changed. This is
    the first problem in this topic to raise "does this approach mutate the
    input?" as an explicit interview question — see the complexity table.


================================================================================
STEP BY STEP TRACE — Approach 1, nums = [3, 1, 2, 10, 1]
================================================================================
    i   nums[i]   total (before -> after)   out
    -   -------   ------------------------  ----------------
    0      3       0  -> 3                  [3]
    1      1       3  -> 4                  [3, 4]
    2      2       4  -> 6                  [3, 4, 6]
    3     10       6  -> 16                 [3, 4, 6, 16]
    4      1      16  -> 17                 [3, 4, 6, 16, 17]

    Final: [3, 4, 6, 16, 17]  — matches LeetCode's Example 3.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time      Space    Mutates input?
    --------------------------------  --------  -------  -----------------
    Brute: re-sum nums[:i+1] each i   O(n^2)    O(n)     no
    Running total -> new list ✅       O(n)      O(n)     no
    In-place accumulation ✅           O(n)      O(1)*    YES — overwrites nums

    * O(1) EXTRA space; the output itself is still O(n), it just reuses the
      input array's storage instead of allocating a second one.

    The "mutates input?" column matters here specifically because this
    problem, unlike 002/003 later in the folder, has an official LeetCode
    approach that trades a real behavioral change (destroying the caller's
    array) for O(1) extra space. State the trade-off out loud rather than
    picking the in-place version by default — in an interview, ask whether
    the caller still needs the original array before mutating it.


================================================================================
EDGE CASES
================================================================================
    []            -> []    Empty array. The problem's constraint says
                           `1 <= nums.length`, but code defensively: the loop
                           simply never runs and an empty list is returned.

    [5]           -> [5]   Single element. Running sum of one element is
                           itself; exercises the very first accumulation
                           step in isolation.

    [-1,-2,-3]    -> [-1,-3,-6]   Negative numbers. `total` must be allowed
                           to go negative and stay negative — no assumption
                           that the running sum is monotone increasing (it
                           is NOT, in general, once negatives are allowed;
                           this quietly foreshadows why sliding window
                           needs non-negative data per the topic guide §1.1
                           while a plain running sum does not).

    [0,0,0,0]     -> [0,0,0,0]   All zeros. `total` never moves; a naive
                           implementation using `if total:` as a truthiness
                           check anywhere would misfire here — there is no
                           reason to branch on `total` at all, which is the
                           point of including this case.


================================================================================
COMMON MISTAKES
================================================================================
1. Re-summing `nums[:i+1]` at every step instead of carrying a running
   total. Correct, but O(n^2) — the whole reason this topic exists is to
   replace that pattern with O(n).

2. Off-by-one on the slice: `sum(nums[:i])` (excludes index i) instead of
   `sum(nums[:i+1])` (includes it) when writing the brute-force oracle.
   `runningSum[i]` is inclusive of `nums[i]` per the problem statement.

3. Mutating `nums` in place (Approach 2) without realizing it, then being
   surprised the caller's array changed. Not wrong for THIS problem, but a
   real bug if `nums` is reused elsewhere in the caller's code.

4. Building the output with repeated `+=` on a Python list via
   `out = out + [total]` inside the loop instead of `out.append(total)` —
   the former reallocates the whole list every iteration, turning an O(n)
   algorithm into O(n^2) list-building.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it without allocating a new array?
A: Yes — Approach 2, in-place accumulation. Trade: mutates the caller's
   input. Always name that trade rather than silently taking it.

Q: What if `nums` is a generator / one-pass stream, not a list?
A: You still only need O(1) state (the running total) to produce each
   output value as it streams in; you cannot do in-place accumulation
   (Approach 2) on a stream since there is no array to overwrite, so you
   are back to Approach 1's shape — yield each running total instead of
   appending it.

Q: How does this relate to the rest of the prefix-sum topic?
A: Every later problem in this folder builds this exact running-total array
   (or its `prefix[0]=0`-shifted twin, topic guide §1.0) and then answers a
   further question with it — an O(1) range query (002), a running
   left/right comparison (003), or a hashmap lookup keyed on prefix values
   (004+). This problem is that array with nothing added on top.

Q: What is the maximum possible running-sum value, and could it overflow?
A: `n <= 1000` and `|nums[i]| <= 10^6`, so the maximum magnitude is
   `1000 * 10^6 = 10^9`, well within a 64-bit integer and Python's
   arbitrary-precision ints — no overflow concern here, but it is the right
   question to ask in a fixed-width-integer language.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 303  Range Sum Query - Immutable    — problem 002: precompute this
                                              exact array, then O(1) queries
    LC 724  Find Pivot Index               — problem 003: running total vs.
                                              a mirrored running total
    LC 238  Product of Except Self         — topic 01, the multiplicative
                                              analogue of a running aggregate
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def runningSum(self, nums: List[int]) -> List[int]:
        """Running total into a new list. O(n) time, O(n) space, does NOT
        mutate the caller's array. The version to write by default."""
        total = 0
        out = []
        for x in nums:
            total += x
            out.append(total)
        return out

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def runningSum_inplace(self, nums: List[int]) -> List[int]:
        """LeetCode's official in-place approach. O(n) time, O(1) EXTRA
        space — but MUTATES the caller's `nums` list."""
        for i in range(1, len(nums)):
            nums[i] += nums[i - 1]
        return nums

    def runningSum_accumulate(self, nums: List[int]) -> List[int]:
        """itertools.accumulate does the running-total loop in C. Same idea
        as the primary approach, just delegated to the stdlib."""
        from itertools import accumulate
        return list(accumulate(nums))

    def runningSum_brute(self, nums: List[int]) -> List[int]:
        """O(n^2) oracle: re-sum nums[:i+1] from scratch at every index."""
        return [sum(nums[:i + 1]) for i in range(len(nums))]


# ==============================================================================
# TESTS — run:  python 001_running_sum_of_1d_array_solution.py
# ==============================================================================
CASES = [
    [1, 2, 3, 4],
    [1, 1, 1, 1, 1],
    [3, 1, 2, 10, 1],
    [5],
    [],
    [0, 0, 0, 0],
    [-1, -2, -3],
    [-1, 2, -3, 4],
    [1000000, 1000000],
    [-1000000, -1000000],
    [7, -7, 7, -7, 7],
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("running total  ", sol.runningSum),
        ("accumulate     ", sol.runningSum_accumulate),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(c)) == sol.runningSum_brute(list(c)) for c in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # in-place variant checked separately since it also must equal the oracle
    ok = all(sol.runningSum_inplace(list(c)) == sol.runningSum_brute(list(c))
              for c in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  in-place       ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Prove the in-place variant actually mutates the caller's array.
    # ----------------------------------------------------------------------
    print("\n--- 'mutates input?' — proven, not asserted ---")
    original = [1, 2, 3, 4]
    caller_ref = original          # caller keeps a reference, as real code does
    result = sol.runningSum_inplace(original)
    mutated = caller_ref == [1, 3, 6, 10]
    print(f"  before: [1, 2, 3, 4]")
    print(f"  after runningSum_inplace(original): caller_ref = {caller_ref}")
    print(f"  caller_ref is result: {caller_ref is result}  "
          f"(same object -> the caller's array WAS changed)")
    all_ok &= mutated

    fresh = [1, 2, 3, 4]
    caller_ref2 = fresh
    _ = sol.runningSum(fresh)
    unmutated = caller_ref2 == [1, 2, 3, 4]
    print(f"  after runningSum(fresh):            caller_ref2 = {caller_ref2}"
          f"  (unchanged, as expected)")
    all_ok &= unmutated

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(4)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(0, 30)
        arr = [random.randint(-1_000_000, 1_000_000) for _ in range(n)]
        want = sol.runningSum_brute(arr)
        for _, fn in impls:
            if fn(list(arr)) != want:
                mismatches += 1
        if sol.runningSum_inplace(list(arr)) != want:
            mismatches += 1
    print(f"  {trials} random arrays x {len(impls) + 1} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The trace.
    # ----------------------------------------------------------------------
    nums = [3, 1, 2, 10, 1]
    print(f"\n--- the running total over {nums} ---")
    print(f"  {'i':>2} {'nums[i]':>8} {'total before':>13} {'total after':>12} "
          f"{'out':>22}")
    total, out = 0, []
    for i, x in enumerate(nums):
        before = total
        total += x
        out.append(total)
        print(f"  {i:>2} {x:>8} {before:>13} {total:>12} {out!s:>22}")

    # ----------------------------------------------------------------------
    # O(n) running total vs O(n^2) re-summing.
    # ----------------------------------------------------------------------
    print("\n--- running total O(n) vs re-sum-from-scratch O(n^2) ---")
    print(f"  {'n':>7} {'running total':>15} {'brute re-sum':>14}")
    for n in (2_000, 4_000, 8_000):
        arr = [random.randint(-1000, 1000) for _ in range(n)]
        t0 = time.perf_counter(); sol.runningSum(arr)
        t1 = time.perf_counter(); sol.runningSum_brute(arr)
        t2 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>13.1f}ms {(t2 - t1) * 1000:>12.1f}ms")
    print("  The gap widens with n: O(n) does a constant amount of work per")
    print("  element, O(n^2) does more work per element as i grows.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
