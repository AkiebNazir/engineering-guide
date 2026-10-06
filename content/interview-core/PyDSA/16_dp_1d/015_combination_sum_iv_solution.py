"""
================================================================================
SOLUTION · LeetCode 377 · Combination Sum IV                          [Medium]
https://leetcode.com/problems/combination-sum-iv/
================================================================================

THE CORE IDEA
--------------
dp[t] MEANS "the number of ORDERED sequences (despite the misleading name
"combination") that sum to exactly t". Numbers are reusable (unbounded),
and the LAST number placed could be any num in nums:

    dp[0] = 1
    dp[t] = sum(dp[t - num] for num in nums if num <= t)

Because order matters, TARGET must be the OUTER loop and NUMS the INNER
loop -- swapping them collapses permutations into combinations (undercounts),
demonstrated live below.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, price it, don't ship it): `ways(t) = sum(ways(t-num)
for num in nums if num <= t)`, base case ways(0)=1. Exponential without
memoization -- the same remainder t gets reached via many different
orderings of numbers already used, and each one re-triggers the full
recursive search from scratch.

Approach 1 (memoized top-down) [`combination_sum4_memo`] -- cache each
target value the first time it's solved. O(target * len(nums)) time,
O(target) space + recursion depth up to `target`.

Approach 2 (tabulated bottom-up, TARGET outer, NUMS inner) [chosen] --
fill dp[0..target] left to right; for each target value, sum over every
number as the "last placed." O(target * len(nums)) time, O(target) space,
no recursion depth risk.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 2, 3], target = 4

dp[0] = 1
t=1: num=1<=1: dp1 += dp0=1                         -> dp1 = 1
     num=2,3 > 1: skip
t=2: num=1<=2: dp2 += dp1=1
     num=2<=2: dp2 += dp0=1
     num=3>2: skip                                  -> dp2 = 2
t=3: num=1<=3: dp3 += dp2=2
     num=2<=3: dp3 += dp1=1
     num=3<=3: dp3 += dp0=1                          -> dp3 = 4
t=4: num=1<=4: dp4 += dp3=4
     num=2<=4: dp4 += dp2=2
     num=3<=4: dp4 += dp1=1                          -> dp4 = 7   <- answer

 t     : 0  1  2  3  4
dp[t]  : 1  1  2  4  7

Matches the 7 orderings listed in the problem statement: (1,1,1,1),
(1,1,2), (1,2,1), (1,3), (2,1,1), (2,2), (3,1).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time                    Space   Mutates input?
    -------------------------------------  ----------------------  ------  --------------
    Naive recursion                         exponential            O(target) depth  no
    Memoized top-down                       O(target * len(nums))  O(target)        no
    Tabulated, target-outer [chosen]        O(target * len(nums))  O(target)        no


================================================================================
EDGE CASES
================================================================================
    target unreachable
    (nums=[9], target=3)          -> dp[3] stays 0 forever since 9>3
                                     blocks every contribution; answer 0.
    target == 0 conceptually       -> dp[0]=1 is the base case (though the
                                     problem's own constraints guarantee
                                     target>=1, dp[0] still matters as the
                                     seed every other dp[t] builds from).
    a single num of value 1        -> exactly one way for any target (use
                                     1 repeated target times) -- dp[t]=1
                                     for all t, confirming the recurrence
                                     collapses correctly for a singleton set.
    large target with multiple
    reusable nums (combinatorial
    blowup in the TRUE count)       -> dp[t] can grow very fast (the
                                     "tribonacci-like" growth for
                                     nums=[1,2,3] approaches a growth
                                     rate matching the characteristic root
                                     of x^3=x^2+x+1) -- the DP handles this
                                     fine since it's just integer
                                     arithmetic, but it's why the naive
                                     recursion is genuinely exponential,
                                     not just "large recursion".


================================================================================
COMMON MISTAKES
================================================================================
1. Putting NUMS in the outer loop and TARGET in the inner loop (copying
   Coin Change II's structure without noticing the problem changed from
   counting UNORDERED combinations to counting ORDERED ones) -- this
   silently undercounts, treating (1,2) and (2,1) as the same combination
   instead of two. Demonstrated live below.
2. Confusing this with 0/1 knapsack (014) and scanning HIGH to LOW --
   that direction trick is for BOUNDED reuse; this problem is UNBOUNDED
   (numbers reusable), so target-outer/nums-inner with natural LOW-to-HIGH
   target progression is correct, no direction reversal needed within a
   single num's contribution.
3. Forgetting dp[0] = 1 is a real, necessary base case (not a degenerate
   edge case to special-case away) -- every dp[t] that uses the full
   count of `num` to exactly reach t depends on it.
4. Off-by-one: `num <= t` (not `num < t`) is required to allow a single
   number to exactly equal the remaining target.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if you wanted UNORDERED combinations instead (order doesn't
  matter)?" -> that's Coin Change II (LC 518) -- same recurrence shape,
  but swap the loop nesting: NUMS outer, TARGET inner, so each number's
  contribution can only be "layered in" once per position, not
  re-permuted at every target value.
- "What if negative numbers were allowed?" (the problem's own official
  follow-up) -> the target space is no longer bounded -- you could
  oscillate between positive and negative numbers indefinitely to hit
  the same target infinitely many ways, so the problem becomes
  ill-defined / infinite without an added constraint (e.g. a cap on
  sequence length).
- "Can you get O(log target) per query with matrix exponentiation?" -> if
  the SET of nums is FIXED and you need dp for a specific huge target
  (not the whole prefix), the linear recurrence dp[t] = sum(dp[t-num])
  can be expressed as a companion-matrix power, similar to problem 001's
  Tribonacci follow-up.


================================================================================
RELATED PROBLEMS
================================================================================
- 010 Coin Change (LC 322) -- same unbounded-reuse DP shape, but
  minimizing COUNT of coins rather than counting orderings; order
  doesn't matter for a min, so no outer/inner distinction bites there.
- Coin Change II (LC 518) -- the UNORDERED counterpart; the loop-nesting
  contrast IS the whole lesson connecting these three problems.
- 001 N-th Tribonacci Number -- nums=[1,2,3] with unlimited reuse and
  ORDER mattering literally reduces to the Tribonacci recurrence.
================================================================================
"""

import sys
import time
from typing import List


class Solution:
    def combinationSum4(self, nums: List[int], target: int) -> int:
        dp = [0] * (target + 1)
        dp[0] = 1
        for t in range(1, target + 1):
            for num in nums:
                if num <= t:
                    dp[t] += dp[t - num]
        return dp[target]


def combination_sum4_naive(nums: List[int], target: int) -> int:
    def solve(t: int) -> int:
        if t == 0:
            return 1
        return sum(solve(t - num) for num in nums if num <= t)

    return solve(target)


def combination_sum4_memo(nums: List[int], target: int) -> int:
    memo = {0: 1}

    def solve(t: int) -> int:
        if t in memo:
            return memo[t]
        memo[t] = sum(solve(t - num) for num in nums if num <= t)
        return memo[t]

    return solve(target)


def combination_sum4_wrong_nesting(nums: List[int], target: int) -> int:
    """Copies Coin Change II's loop nesting (nums outer, target inner) --
    correct for counting UNORDERED combinations, but WRONG here since this
    problem wants ORDERED sequences counted separately. Kept purely to
    demonstrate the undercount live in run_tests().
    """
    dp = [0] * (target + 1)
    dp[0] = 1
    for num in nums:
        for t in range(num, target + 1):
            dp[t] += dp[t - num]
    return dp[target]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 2, 3], 4, 7),
        ([9], 3, 0),
        ([1], 1, 1),
        ([1], 5, 1),
        ([2, 3], 7, 3),
        ([1, 2], 4, 5),
    ]
    for nums, target, want in cases:
        got = sol.combinationSum4(nums[:], target)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} target={target}  -> {got}  (want {want})")
        assert combination_sum4_memo(nums[:], target) == want

    print()
    print("CORRECTNESS DEMO -- wrong loop nesting (nums outer) undercounts orderings")
    print("-" * 72)
    trap_nums, trap_target = [1, 2, 3], 4
    correct = sol.combinationSum4(trap_nums[:], trap_target)
    wrong = combination_sum4_wrong_nesting(trap_nums[:], trap_target)
    print(f"nums={trap_nums} target={trap_target}")
    print(f"  target-outer, nums-inner (correct, counts ORDER): {correct}")
    print(f"  nums-outer, target-inner (Coin Change II style):  {wrong}   "
          f"(this is actually the UNORDERED combination count, a different question)")
    assert correct == 7
    assert wrong != correct, "expected the wrong-nesting version to diverge on this input"

    print()
    print("RUNTIME DEMO -- naive exponential recursion vs tabulated DP, measured live")
    print("-" * 72)
    sys.setrecursionlimit(10000)
    nums = [1, 2, 3]
    for target in (18, 21, 24):
        t0 = time.perf_counter()
        naive_result = combination_sum4_naive(nums, target)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        dp_result = sol.combinationSum4(nums[:], target)
        dp_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == dp_result
        print(f"target={target:3d}  naive={naive_ms:9.3f} ms   tabulated_dp={dp_ms:7.4f} ms   "
              f"ratio={naive_ms / max(dp_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
