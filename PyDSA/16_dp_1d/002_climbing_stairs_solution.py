"""
================================================================================
SOLUTION · LeetCode 70 · Climbing Stairs                             [Easy]
https://leetcode.com/problems/climbing-stairs/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "the number of distinct ways to reach step i". The last move to
reach step i is either a 1-step from i-1 or a 2-step from i-2, and those
two path-sets never overlap, so:

    dp[i] = dp[i-1] + dp[i-2],   dp[1] = 1, dp[2] = 2

This is literally Fibonacci shifted by one. See `_TOPIC_GUIDE.md` Part 0
for the full naive -> memo -> tabulation -> rolling-variables walkthrough
on this exact problem.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, price it, don't ship it):
    def ways(n): return n if n <= 2 else ways(n-1) + ways(n-2)
O(2^n) (really O(phi^n)) -- ways(n-2) is recomputed once directly and once
more inside the ways(n-1) branch, and that duplication compounds every level.

Approach 1 (memoized top-down) [`climb_memo`] -- cache each n the first
time it's solved. O(n) time, O(n) space (memo + call stack).

Approach 2 (tabulated bottom-up) [`climb_tab`] -- fill dp[1..n] left to
right, no recursion, no stack-depth ceiling. O(n) time, O(n) space.

Approach 3 (space-optimized) [chosen] -- dp[i] only reads dp[i-1], dp[i-2],
so roll two variables forward instead of keeping the whole array.
O(n) time, O(1) space -- the version to actually say out loud in an interview.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 5

 i   : 1  2  3  4  5
dp[i]: 1  2  3  5  8
             ^^^^^^^ dp[3]=1+2=3, dp[4]=2+3=5, dp[5]=3+5=8

Rolling-variable trace, (prev2, prev1) = (dp[i-2], dp[i-1]) just before dp[i]:

    start:            prev2=1, prev1=2      (dp1, dp2)
    i=3: dp3=1+2=3  -> prev2=2, prev1=3
    i=4: dp4=2+3=5  -> prev2=3, prev1=5
    i=5: dp5=3+5=8  -> prev2=5, prev1=8
    return prev1 = 8


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time      Space   Mutates input?
    ---------------------------  --------  ------  --------------
    Naive recursion               O(phi^n) O(n)    n/a (no input array)
    Memoized top-down             O(n)     O(n)    n/a
    Tabulated bottom-up           O(n)     O(n)    n/a
    Rolling variables [chosen]    O(n)     O(1)    n/a


================================================================================
EDGE CASES
================================================================================
    n == 1              -> only one way (single 1-step); must be a direct
                            base case, the loop below assumes n >= 3.
    n == 2               -> two ways (1+1, 2); the second base case.
    n == 45 (max)         -> confirms no recursion-limit or overflow issue at
                            the upper bound; Python ints are unbounded so
                            only performance matters here.


================================================================================
COMMON MISTAKES
================================================================================
1. Off-by-one: treating this as 0-indexed Fibonacci and returning fib(n)
   instead of fib(n+1) -- climbStairs(1)=1 but a raw fib(1)=1, fib(2)=1
   would wrongly give climbStairs(2)=1 instead of 2 if the base cases
   aren't shifted correctly.
2. Recursing without memoizing "because n <= 45 is small" -- phi^45 is
   still tens of millions of redundant calls; see the runtime demo below.
3. Forgetting the recursion-depth risk on the memoized version for large n
   in general DP problems (n=45 is safe, but the habit of reaching for
   tabulation instead of memoization at scale is the one worth building --
   Trap B in `_TOPIC_GUIDE.md`).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if you could climb 1, 2, or 3 steps at a time?" -> dp[i] = dp[i-1]
  + dp[i-2] + dp[i-3], same technique, window of 3 (Tribonacci, problem 001).
- "What if some steps are broken and can't be landed on?" -> zero out
  dp[i] for broken steps, same recurrence otherwise.
- "Can you do it with O(1) space?" -> yes, shown above.


================================================================================
RELATED PROBLEMS
================================================================================
- 001 N-th Tribonacci Number (LC 1137) -- window of 3 instead of 2.
- 003 Min Cost Climbing Stairs (LC 746) -- same shape, minimizing cost
  instead of counting paths.
- Fibonacci Number (LC 509) -- the base recurrence this problem shifts by 1.
================================================================================
"""

import sys
import time


class Solution:
    def climbStairs(self, n: int) -> int:
        if n <= 2:
            return n
        prev2, prev1 = 1, 2  # dp[1], dp[2]
        for _ in range(3, n + 1):
            prev2, prev1 = prev1, prev2 + prev1
        return prev1


def climb_naive(n: int) -> int:
    if n <= 2:
        return n
    return climb_naive(n - 1) + climb_naive(n - 2)


def climb_memo(n: int, memo=None) -> int:
    if memo is None:
        memo = {}
    if n <= 2:
        return n
    if n in memo:
        return memo[n]
    memo[n] = climb_memo(n - 1, memo) + climb_memo(n - 2, memo)
    return memo[n]


def climb_tab(n: int) -> int:
    if n <= 2:
        return n
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 2
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (1, 1),
        (2, 2),
        (3, 3),
        (4, 5),
        (5, 8),
        (10, 89),
        (45, 1836311903),
    ]
    for n, want in cases:
        got = sol.climbStairs(n)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:2d}  -> {got}  (want {want})")
        assert climb_memo(n) == want
        assert climb_tab(n) == want

    print()
    print("RUNTIME DEMO -- naive O(phi^n) recursion vs memoized O(n), measured live")
    print("-" * 72)
    sys.setrecursionlimit(10000)
    for n in (10, 20, 30):
        t0 = time.perf_counter()
        naive_result = climb_naive(n)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        memo_result = climb_memo(n)
        memo_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == memo_result
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   memo={memo_ms:7.4f} ms   "
              f"ratio={naive_ms / max(memo_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
