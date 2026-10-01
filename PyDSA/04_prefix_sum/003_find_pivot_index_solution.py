"""
================================================================================
SOLUTION · LeetCode 724 · Find Pivot Index                              [Easy]
https://leetcode.com/problems/find-pivot-index/
================================================================================

THE CORE IDEA
--------------
Compute the array's total sum ONCE. Then walk left to right carrying a
running `leftSum`; at each index, derive `rightSum` algebraically instead of
re-summing it:

    rightSum = total - leftSum - nums[i]

    total = sum(nums)
    leftSum = 0
    for i, x in enumerate(nums):
        rightSum = total - leftSum - x
        if leftSum == rightSum:
            return i
        leftSum += x
    return -1

This is the topic guide's Part 4 complexity-table trap ("recompute
sum(a[l:r+1]) per query — O(r-l) — the trap: O(nq) over q queries"), staged
as a single-pass interview problem: the naive version re-sums `nums[:i]`
and `nums[i+1:]` from scratch at every index (O(n) work per index -> O(n^2)
total); the fix keeps a running total instead, so each index does O(1) work.


================================================================================
MULTIPLE APPROACHES
================================================================================

APPROACH 0 · NAIVE — RE-SUM BOTH SIDES EVERY INDEX (priced, then coded)
    For each i: `left = sum(nums[:i])`, `right = sum(nums[i+1:])`. Correct,
    and cheap enough to write in two lines, so we code it and benchmark it
    below rather than only pricing it. O(n) work per index x n indices =
    O(n^2) overall.

APPROACH 1 · RUNNING TOTAL ✅ (the answer)
    Precompute `total = sum(nums)` once (O(n)). Then a single pass carries
    `leftSum`, deriving `rightSum = total - leftSum - nums[i]` in O(1) per
    step instead of re-summing it. O(n) overall, O(1) extra space — no
    prefix ARRAY is needed here (contrast problem 002, which needed random
    access to every historical prefix for out-of-order queries; this
    problem only ever needs the running total at the CURRENT index, so a
    single variable suffices — topic guide Part 4's space note on 001/003).


================================================================================
STEP BY STEP TRACE — nums = [1, 7, 3, 6, 5, 6]
================================================================================
    total = 1+7+3+6+5+6 = 28

    i   nums[i]   leftSum (before)   rightSum = total-leftSum-nums[i]   equal?   leftSum (after)
    -   -------   -----------------  ---------------------------------  -------  -----------------
    0      1             0            28 -  0 - 1 = 27                   no            1
    1      7             1            28 -  1 - 7 = 20                   no            8
    2      3             8            28 -  8 - 3 = 17                   no           11
    3      6            11            28 - 11 - 6 = 11                  YES <- PIVOT   17
    4      5            17               (loop stops at i=3)
    5      6

    Sanity check by direct summation:
        left  of index 3 = nums[0]+nums[1]+nums[2] = 1+7+3  = 11
        right of index 3 = nums[4]+nums[5]         = 5+6    = 11    ✓ matches


================================================================================
WHY RECOMPUTING sum(left)/sum(right) EACH ITERATION IS O(n^2) VS O(n)
================================================================================
The naive version does this at every index i:

    left  = sum(nums[:i])       # O(i) work
    right = sum(nums[i+1:])     # O(n-i-1) work

Summed across all n indices: `sum(i for i in range(n)) = O(n^2/2) = O(n^2)`.
Each index re-derives information the PREVIOUS index already had — `leftSum`
at index i is just `leftSum` at index i-1 plus `nums[i-1]`, one addition
away. Recomputing it from scratch throws that away and redoes O(i) work
every single step.

The O(n) fix carries exactly one number (`leftSum`) forward and updates it
incrementally — the same "one running total, no re-derivation" idea as
problem 001's core loop, now paired with a single precomputed `total` so the
right side never needs its own running variable at all. The benchmark below
measures this gap directly, the way the topic guide's Part 4 table predicts.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time      Space    Mutates input?
    ------------------------------  --------  -------  -----------------
    Naive: re-sum both sides        O(n^2)    O(1)     no
    Running total ✅                 O(n)      O(1)     no
    Prefix ARRAY + subtraction      O(n)      O(n)      no  (works, but the
                                                              array is never
                                                              needed twice —
                                                              a running total
                                                              is strictly
                                                              enough here)


================================================================================
EDGE CASES
================================================================================
    [1,2,3]              -> -1    No pivot exists. leftSum never equals
                                   rightSum at any index; loop exhausts and
                                   falls through to `return -1`.

    [2,1,-1]              -> 0    Pivot at index 0: leftSum = 0 (nothing to
                                   the left) must equal rightSum = 1+(-1) = 0.
                                   Exercises leftSum's initial value as a
                                   real operand, not a special case.

    [-1,-1,0,1,1,0]        -> 5    Pivot at the LAST index: rightSum = 0
                                   (nothing to the right). Exercises the
                                   formula at the opposite edge.

    [5]                    -> 0    Single element. leftSum = 0, rightSum =
                                   total - 0 - 5 = 0 (since total = 5).
                                   Trivially the pivot.

    [0,0,0,0]              -> 0    All zeros. EVERY index satisfies
                                   leftSum == rightSum == 0, so the LEFTMOST
                                   one (index 0) must win — the loop returns
                                   on the first match, it does not scan for
                                   "the best" one.

    Negative numbers        e.g. [1,-1,1,-1,1] -> 0 (leftSum=0 equals
                                   rightSum=(-1+1-1+1)=0 right away).
                                   leftSum and rightSum
                                   can each go negative; equality is checked
                                   on the numeric VALUE, sign included.


================================================================================
COMMON MISTAKES
================================================================================
1. Recomputing `sum(nums[:i])` and `sum(nums[i+1:])` inside the loop instead
   of carrying `leftSum` and deriving `rightSum` algebraically — the whole
   O(n^2)-vs-O(n) point of this problem.

2. Updating `leftSum += nums[i]` BEFORE comparing it to `rightSum`, so the
   comparison silently includes the current element on both sides (or
   neither, depending on how rightSum was derived) instead of strictly
   left vs. strictly right.

3. Deriving `rightSum` as `total - leftSum` (forgetting to subtract
   `nums[i]` itself) — this leaves the current element attached to the
   right side and never finds a real pivot except by accident.

4. Returning the LAST matching index instead of the first, by continuing
   the loop past a match to "make sure." The problem asks for the leftmost;
   return immediately on the first equality.

5. Assuming an all-zero array has no pivot because "every index is a tie" —
   a tie IS a valid pivot; the leftmost one is index 0, not "no answer."

6. Computing `total` INSIDE the loop (e.g. `sum(nums)` called on every
   iteration) instead of once before it — silently reintroduces O(n^2).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Could you solve this with a prefix ARRAY instead of a running total?
A: Yes — build `prefix` per the topic guide §1.0, then at index i,
   `leftSum = prefix[i]` and `rightSum = prefix[n] - prefix[i+1]`, both O(1)
   lookups after an O(n) build. Same time complexity, but O(n) space instead
   of O(1) — worth it only if you need random access to arbitrary indices'
   left/right sums repeatedly, which this problem does not (each index is
   visited once, in order).

Q: What if the array is a stream and you must answer as elements arrive?
A: You cannot find the LEFTMOST pivot without eventually knowing the total,
   which requires having seen the whole array — so this specific problem
   inherently needs a full pass before (or during, with a second pass) any
   answer is final. You could, however, stream in the total first and then
   re-stream for the pivot scan, still O(n) total work, O(1) extra space.

Q: Multiple pivots can exist — how would you return ALL of them instead of
   just the leftmost?
A: Drop the early `return i`; instead append every matching index to a
   result list and continue the loop to the end. Still O(n).

Q: How does this generalize to matrices?
A: Not directly a topic-04 follow-up, but conceptually: an analogous "pivot
   row/column" question in 2D would use the 2D prefix sums from problem 006
   (topic guide Part 2) to get row-sum and column-sum totals in O(1) each
   after an O(mn) precompute, rather than re-summing rows/columns from
   scratch.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1480  Running Sum of 1d Array   — problem 001: the same running-total
                                          mechanism, with no comparison layer
    LC 303   Range Sum Query - Immutable — problem 002: when a full prefix
                                          ARRAY (not just a running total)
                                          is actually the right tool
    LC 238   Product of Except Self    — topic 01: the multiplicative
                                          left/right split, same shape
    LC 1991  Find the Middle Index in Array — literally the same problem,
                                          renamed
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def pivotIndex(self, nums: List[int]) -> int:
        """Running total, O(n) time, O(1) space. The version to write."""
        total = sum(nums)
        left_sum = 0
        for i, x in enumerate(nums):
            right_sum = total - left_sum - x
            if left_sum == right_sum:
                return i
            left_sum += x
        return -1

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def pivotIndex_prefix_array(self, nums: List[int]) -> int:
        """Explicit prefix array (topic guide §1.0), O(n) time, O(n) space.
        Correct, but the array is overkill: each index is visited once, in
        order, so a running total is strictly sufficient here."""
        n = len(nums)
        prefix = [0] * (n + 1)
        for i, x in enumerate(nums):
            prefix[i + 1] = prefix[i] + x
        for i in range(n):
            left_sum = prefix[i]
            right_sum = prefix[n] - prefix[i + 1]
            if left_sum == right_sum:
                return i
        return -1

    def pivotIndex_brute(self, nums: List[int]) -> int:
        """O(n^2) oracle: re-sum the left and right sides at every index."""
        n = len(nums)
        for i in range(n):
            left = sum(nums[:i])
            right = sum(nums[i + 1:])
            if left == right:
                return i
        return -1


# ==============================================================================
# TESTS — run:  python 003_find_pivot_index_solution.py
# ==============================================================================
CASES = [
    [1, 7, 3, 6, 5, 6],
    [1, 2, 3],
    [2, 1, -1],
    [-1, -1, 0, 1, 1, 0],
    [5],
    [0, 0, 0, 0],
    [-1, -1, -1, -1, -1, -1],
    [1, -1, 1, -1, 1],
    [0],
    [1, 0],
    [10, -10, 10, -10],
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("running total  ", sol.pivotIndex),
        ("prefix array   ", sol.pivotIndex_prefix_array),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(c)) == sol.pivotIndex_brute(list(c)) for c in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(9)
    trials, mismatches = 4000, 0
    for _ in range(trials):
        n = random.randint(1, 25)
        arr = [random.randint(-20, 20) for _ in range(n)]
        want = sol.pivotIndex_brute(arr)
        for _, fn in impls:
            if fn(list(arr)) != want:
                mismatches += 1
    print(f"  {trials} random arrays x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The trace, requested explicitly: running leftSum vs rightSum.
    # ----------------------------------------------------------------------
    nums = [1, 7, 3, 6, 5, 6]
    total = sum(nums)
    print(f"\n--- running leftSum vs rightSum over {nums} (total={total}) ---")
    print(f"  {'i':>2} {'nums[i]':>8} {'leftSum before':>15} "
          f"{'rightSum':>9} {'equal?':>7} {'leftSum after':>14}")
    left_sum = 0
    found = None
    for i, x in enumerate(nums):
        right_sum = total - left_sum - x
        eq = left_sum == right_sum
        before = left_sum
        left_sum += x
        print(f"  {i:>2} {x:>8} {before:>15} {right_sum:>9} "
              f"{'YES <-' if eq else 'no':>7} {left_sum:>14}")
        if eq and found is None:
            found = i
    print(f"  leftmost pivot index: {found}")

    # ----------------------------------------------------------------------
    # O(n^2) recompute vs O(n) running total.
    # ----------------------------------------------------------------------
    print("\n--- O(n^2) recompute-each-iteration vs O(n) running total ---")
    print(f"  {'n':>7} {'running total':>15} {'naive recompute':>17}")
    random.seed(1)
    for n in (2_000, 4_000, 8_000):
        arr = [random.randint(-1000, 1000) for _ in range(n)]
        t0 = time.perf_counter(); sol.pivotIndex(arr)
        t1 = time.perf_counter(); sol.pivotIndex_brute(arr)
        t2 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>13.2f}ms {(t2 - t1) * 1000:>15.2f}ms")
    print("  Both scans terminate early on a match, so these arrays were")
    print("  constructed to have NO pivot (random ints rarely balance),")
    print("  forcing both implementations to run to completion — the fair")
    print("  worst-case comparison.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
