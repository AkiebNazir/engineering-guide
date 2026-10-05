"""
================================================================================
SOLUTION · LeetCode 746 · Min Cost Climbing Stairs                   [Easy]
https://leetcode.com/problems/min-cost-climbing-stairs/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "the minimum cost to REACH step i" (before paying to leave it).
You reach step i either from i-1 (having paid cost[i-1] to leave it) or
from i-2 (having paid cost[i-2]) -- take the cheaper option:

    dp[0] = dp[1] = 0                        # free starting steps
    dp[i] = min(dp[i-1] + cost[i-1], dp[i-2] + cost[i-2])
    answer = dp[len(cost)]                   # one step PAST the array


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, price it, don't ship it): recurse from the
top backwards, `minCost(i) = cost[i] + min(minCost(i+1), minCost(i+2))`,
trying both starting points. O(2^n) -- same repeated-subproblem blowup as
every problem in this topic, see the runtime demo below.

Approach 1 (memoized top-down) [`min_cost_memo`] -- cache each index the
first time it's solved. O(n) time, O(n) space.

Approach 2 (tabulated bottom-up) [`min_cost_tab`] -- fill dp[0..n] left to
right. O(n) time, O(n) space.

Approach 3 (space-optimized) [chosen] -- dp[i] only reads dp[i-1] and
dp[i-2], roll two variables forward. O(n) time, O(1) space.


================================================================================
STEP BY STEP TRACE
================================================================================
cost = [1, 100, 1, 1, 1, 100, 1, 1, 100, 1]   (len = 10, top = index 10)

 i     : 0  1  2  3  4  5  6  7  8  9  10
dp[i]  : 0  0  1  2  2  3  3  4  4  5  6
                ^              ^        ^
      dp[2]=min(dp1+cost1, dp0+cost0)
           =min(0+100, 0+1)=1
      dp[7]=min(dp6+cost6, dp5+cost5)=min(3+1,3+1)=4
      dp[10]=min(dp9+cost9, dp8+cost8)=min(5+1,4+100)=6   <- answer

Rolling trace (prev2, prev1) = (dp[i-2], dp[i-1]) just before computing dp[i]:
    start: prev2=0, prev1=0        (dp0, dp1)
    i=2: dp2=min(0+1,0+100)=1   -> prev2=0, prev1=1
    i=3: dp3=min(1+100,0+1)=1... (trace continues identically to the table)
    ... i=10: dp10=6 -> return 6


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time     Space   Mutates input?
    ---------------------------  -------  ------  --------------
    Naive recursion               O(2^n)  O(n)    no
    Memoized top-down             O(n)    O(n)    no
    Tabulated bottom-up           O(n)    O(n)    no
    Rolling variables [chosen]    O(n)    O(1)    no


================================================================================
EDGE CASES
================================================================================
    len(cost) == 2         -> smallest allowed input; answer is
                              min(cost[0], cost[1]) since you can start at
                              either and jump straight to the top.
    all zeros               -> every path is free; answer 0. Confirms the
                              recurrence doesn't accidentally add a phantom
                              base cost.
    cheapest path alternates start points -> example 2 above; forces the
                              min() to actually pick between two genuinely
                              different-cost routes rather than one obviously
                              dominant path.
    cost[i] can be 0         -> a free step must still be reachable and
                              usable as a stepping stone, not skipped.


================================================================================
COMMON MISTAKES
================================================================================
1. Confusing "cost to reach step i" with "cost including step i" -- the
   recurrence pays cost[i-1] / cost[i-2] (the step you LEAVE), not cost[i]
   (the step you land on). Indexing dp[i] = min(dp[i-1], dp[i-2]) + cost[i]
   gives a different (also valid-looking but wrong for this exact LC
   phrasing) answer -- always re-derive against the problem's own definition.
2. Forgetting the top is ONE PAST the last index -- answer is dp[len(cost)],
   not dp[len(cost)-1].
3. Assuming you must start at index 0 -- the problem explicitly allows
   starting at 0 OR 1 for free, which is why both dp[0] and dp[1] are 0.
4. Off-by-one in the loop range: `range(2, len(cost))` stops one short of
   the top; must be `range(2, len(cost) + 1)`.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if you could jump 1, 2, or 3 steps?" -> dp[i] = min over the last
  THREE cells + their costs, same technique.
- "Can you reconstruct the actual path taken, not just the cost?" -> track
  a `choice[i]` array alongside dp recording which predecessor won, then
  walk it backwards from the top.
- "Can you do it in O(1) space?" -> yes, shown above.


================================================================================
RELATED PROBLEMS
================================================================================
- 002 Climbing Stairs (LC 70) -- same window-of-2 recurrence, counting
  paths (sum) instead of minimizing cost.
- 005 House Robber (LC 198) -- also a "min/max over including-or-not the
  previous window" 1D DP.
================================================================================
"""

import sys
import time
from typing import List


class Solution:
    def minCostClimbingStairs(self, cost: List[int]) -> int:
        n = len(cost)
        prev2, prev1 = 0, 0  # dp[0], dp[1]
        for i in range(2, n + 1):
            prev2, prev1 = prev1, min(prev1 + cost[i - 1], prev2 + cost[i - 2])
        return prev1


def min_cost_naive(cost: List[int], i: int = 0) -> int:
    n = len(cost)
    if i >= n:
        return 0
    return cost[i] + min(min_cost_naive(cost, i + 1), min_cost_naive(cost, i + 2))


def min_cost_memo(cost: List[int]) -> int:
    n = len(cost)
    memo = {}

    def solve(i: int) -> int:
        if i >= n:
            return 0
        if i in memo:
            return memo[i]
        memo[i] = cost[i] + min(solve(i + 1), solve(i + 2))
        return memo[i]

    return min(solve(0), solve(1))


def min_cost_tab(cost: List[int]) -> int:
    n = len(cost)
    dp = [0] * (n + 1)
    for i in range(2, n + 1):
        dp[i] = min(dp[i - 1] + cost[i - 1], dp[i - 2] + cost[i - 2])
    return dp[n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([10, 15, 20], 15),
        ([1, 100, 1, 1, 1, 100, 1, 1, 100, 1], 6),
        ([0, 0, 0, 0], 0),
        ([1, 2], 1),
        ([0, 2, 2, 1], 2),
    ]
    for cost, want in cases:
        got = sol.minCostClimbingStairs(cost[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  cost={cost}  -> {got}  (want {want})")
        assert min_cost_memo(cost[:]) == want
        assert min_cost_tab(cost[:]) == want

    print()
    print("RUNTIME DEMO -- naive O(2^n) recursion vs memoized O(n), measured live")
    print("-" * 72)
    sys.setrecursionlimit(10000)
    import random
    random.seed(0)
    for n in (10, 20, 28):
        c = [random.randint(0, 999) for _ in range(n)]
        t0 = time.perf_counter()
        naive_result = min(min_cost_naive(c, 0), min_cost_naive(c, 1))
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        memo_result = min_cost_memo(c)
        memo_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == memo_result
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   memo={memo_ms:7.4f} ms   "
              f"ratio={naive_ms / max(memo_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
