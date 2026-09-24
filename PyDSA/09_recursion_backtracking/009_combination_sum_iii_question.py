"""
================================================================================
LeetCode 216 · Combination Sum III                                      [Medium]
https://leetcode.com/problems/combination-sum-iii/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Find all valid combinations of `k` numbers that sum up to `n`, such that:

    - Only numbers 1 through 9 are used.
    - Each number is used AT MOST ONCE.

Return a list of all possible valid combinations. The list must not contain
the same combination twice, and the combinations may be returned in any
order.

EXAMPLES
--------
Example 1:
    Input:  k = 3, n = 7
    Output: [[1,2,4]]
    Explanation: 1 + 2 + 4 = 7. There are no other valid combinations.

Example 2:
    Input:  k = 3, n = 9
    Output: [[1,2,6],[1,3,5],[2,3,4]]
    Explanation:
        1 + 2 + 6 = 9
        1 + 3 + 5 = 9
        2 + 3 + 4 = 9
        There are no other valid combinations.

Example 3:
    Input:  k = 4, n = 1
    Output: []
    Explanation: no valid combination. Using 4 different numbers in the
    range [1,9], the smallest sum we can get is 1+2+3+4 = 10, and since
    10 > 1 there are no valid combinations.

CONSTRAINTS
-----------
    2 <= k <= 9
    1 <= n <= 60

    Both bounds are tiny, and both are informative:
      k <= 9 because there are only 9 distinct digits to choose from.
      The largest achievable sum is 1+2+...+9 = 45, so any n > 45 is
      impossible — note the constraint allows n up to 60 precisely so that
      you have to handle the impossible cases.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the third and last member of the Combination Sum family, and it is
the most CONSTRAINED of the three — which makes it the best pruning exercise
in the topic.

    LC 39  (007)  sum target,  reuse allowed,   any length,  arbitrary input
    LC 40  (008)  sum target,  no reuse,        any length,  duplicate input
    LC 216 (009)  sum target,  no reuse,        LENGTH == k,  input is 1..9

Notice what the fixed input buys you: the digits 1..9 are DISTINCT and
already sorted, so there is no dedupe idiom to write (no duplicate values can
exist) and no `sort()` call to remember. What you gain instead is a second,
independent constraint — the exact length k — and therefore a second,
independent source of pruning.

THE POINT OF THIS PROBLEM: TWO-SIDED PRUNING
---------------------------------------------
At any node you know two things about what is left:

    need = k - len(path)          how many more digits you must pick
    rem  = n - sum(path)          how much more sum you must produce

A branch is hopeless if EITHER of those cannot be satisfied, and each gives a
different test:

  (a) COUNT feasibility (this is problem 006's bound, unchanged):
      starting at digit `i` there are `9 - i + 1` digits left. If that is
      fewer than `need`, no branch from here can ever reach length k.
          require   9 - i + 1 >= need     i.e.   i <= 9 - need + 1

  (b) SUM feasibility (new here — and it cuts BOTH ways):
      with `need` digits all >= i, the SMALLEST reachable sum is
          i + (i+1) + ... + (i+need-1) = need*i + need*(need-1)/2
      and with `need` digits all <= 9, the LARGEST reachable sum is
          9 + 8 + ... + (9-need+1) = need*(19-need)/2
      If `rem` is below the minimum, you have already overshot: prune.
      If `rem` is above the maximum, you can never catch up: prune.

Test (b)'s "too small" direction is the one people forget, and it is the one
that does most of the work on inputs like k=2, n=45.

WHAT TO THINK ABOUT
--------------------
1. Start from problem 006 (Combinations): this is literally LC 77 with n
   fixed at 9 and a sum condition added at the leaf. Write that first, then
   add pruning.

2. The leaf test needs BOTH conditions: `len(path) == k AND remaining == 0`.
   What goes wrong if you check only one of them? Try it — both failure modes
   are instructive, and one of them silently returns combinations of the
   wrong length.

3. Derive the minimum and maximum reachable sums above for yourself rather
   than memorising the formulas. The formula for the largest sum of `need`
   digits from 1..9 is the sum of the top `need` values; the smallest, given
   you must start at `i` or later, is the run `i, i+1, ..., i+need-1`.

4. How many nodes does the tree have WITHOUT any pruning? With only the count
   bound? With both? Guess the numbers before measuring them; the answer for
   k=2, n=45 is much starker than most people expect.

5. Is there any dedupe to do? No — 1..9 are distinct and ascending, so the
   increasing-index rule alone guarantees each combination is generated once.
   Say why out loud; it is the contrast that makes 008's idiom memorable.

6. Total number of combinations across ALL (k, n) pairs is just 2^9 = 512
   (every subset of 1..9 has exactly one k and one n). What does that tell you
   about the size of the search space, and about whether pruning matters for
   PASSING versus for demonstrating skill?

PROGRESSIVE HINTS
------------------
Hint 1: Copy problem 006's solution. Replace `n` (the range end) with the
        literal 9, and add a `remaining` parameter for the sum.

Hint 2: Base case: `if need == 0: if remaining == 0: record; return`. Or
        equivalently record when `len(path) == k and remaining == 0`.

Hint 3: In the loop, `if digit > remaining: break` — the digits ascend, so
        once one is too big, all the later ones are too.

Hint 4: Add the count bound to the loop's upper limit:
            for digit in range(start, 9 - need + 2)
        (that is `i <= 9 - need + 1`, written as a `range` bound).

Hint 5: Add the sum bound. Before (or inside) the loop, compute
            lo = need * digit + need * (need - 1) // 2
            hi = need * (19 - need) // 2
        and skip/break when `remaining < lo` or `remaining > hi`. The `hi`
        test only depends on `need`, so it can be checked ONCE per node
        rather than per digit — a small but real optimisation.

COMPLEXITY TARGET
------------------
    Time:  O(C(9,k) * k) to produce the output, and the whole search space is
           bounded by 2^9 = 512 subsets no matter what. This problem is
           SMALL — the pruning is not what makes it pass, it is what
           demonstrates you can reason about search-space size. Say that
           distinction out loud in an interview; it is the mature answer.
    Space: O(k) for the recursion stack and `path`, excluding output.
================================================================================
"""

from typing import List


class Solution:
    def combinationSum3(self, k: int, n: int) -> List[List[int]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 009_combination_sum_iii_question.py
# ==============================================================================
def _oracle(k: int, n: int) -> List[List[int]]:
    """Independent reference: itertools over all k-subsets of 1..9."""
    from itertools import combinations
    return [list(c) for c in combinations(range(1, 10), k) if sum(c) == n]


def run_tests() -> None:
    sol = Solution()
    cases = [(3, 7), (3, 9), (4, 1), (2, 18), (9, 45), (9, 44), (2, 3),
             (5, 15), (4, 30), (3, 60), (2, 45), (8, 40)]
    passed = 0
    for k, n in cases:
        expected = sorted(sorted(c) for c in _oracle(k, n))
        got = sol.combinationSum3(k, n)
        got_norm = sorted(sorted(c) for c in got) if got else []
        ok = got_norm == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k}, n={n}")
        if not ok:
            print(f"    Expected: {expected}")
            print(f"    Got:      {got_norm}")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
