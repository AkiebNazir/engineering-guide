"""
================================================================================
SOLUTION · LeetCode 1137 · N-th Tribonacci Number                    [Easy]
https://leetcode.com/problems/n-th-tribonacci-number/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "the tribonacci value at index i". The recurrence reaches back
exactly THREE cells (dp[i-1], dp[i-2], dp[i-3]) so it is a fixed-window
linear DP -- compute left to right, keep only the last three values.

    dp[0], dp[1], dp[2] = 0, 1, 1
    dp[i] = dp[i-1] + dp[i-2] + dp[i-3]     for i >= 3

O(n) time, O(1) space once rolled.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, name it and price it, do not ship it):
    def trib(n):
        if n == 0: return 0
        if n in (1, 2): return 1
        return trib(n-1) + trib(n-2) + trib(n-3)
Every trib(k) for k < n-3 gets recomputed many times over -- the call tree
branches 3-wide at every level, giving O(3^n) time. See the runtime demo
below for exactly how fast this becomes unusable.

Approach 1 (memoized top-down) [checked, see `tribonacci_memo`] -- cache
each n the first time it's computed. O(n) time, O(n) space (memo dict +
call stack up to depth n).

Approach 2 (tabulated bottom-up) [checked, see `tribonacci_tab`] -- fill an
array dp[0..n] left to right, no recursion. O(n) time, O(n) space, no
recursion-depth ceiling.

Approach 3 (space-optimized, rolling variables) [chosen, `tribonacci`] --
dp[i] only reads the three cells directly before it, so keep three rolling
variables instead of a whole array. O(n) time, O(1) space.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 6, target dp[6].

 i   : 0  1  2  3  4  5  6
dp[i]: 0  1  1  2  4  7  13
                ^        ^
          dp[3]=0+1+1=2       dp[6]=4+7+2=13  (dp[3..5] = 2,4,7)

Rolling-variable version, tracking (a, b, c) = (dp[i-3], dp[i-2], dp[i-1])
just before computing dp[i]:

    start:      a=0, b=1, c=1        (dp0, dp1, dp2)
    i=3: dp3=0+1+1=2   -> a,b,c = 1,1,2
    i=4: dp4=1+1+2=4   -> a,b,c = 1,2,4
    i=5: dp5=1+2+4=7   -> a,b,c = 2,4,7
    i=6: dp6=2+4+7=13  -> a,b,c = 4,7,13
    return c = 13


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time      Space   Mutates input?
    -----------------------  --------  ------  --------------
    Naive recursion           O(3^n)   O(n)    n/a (no input array)
    Memoized top-down         O(n)     O(n)    n/a
    Tabulated bottom-up       O(n)     O(n)    n/a
    Rolling variables [chosen] O(n)    O(1)    n/a


================================================================================
EDGE CASES
================================================================================
    n == 0                -> direct base case, must return 0 (not fall
                              through to the loop which assumes n >= 3).
    n == 1 or n == 2       -> both are 1; a naive "if n == 0 return 0 else
                              loop" would mis-handle these without an
                              explicit early return.
    n == 3                 -> the smallest input that actually exercises the
                              recurrence (0+1+1=2); good first loop-body check.
    n == 37 (max per constraints) -> largest input; confirms no overflow
                              behavior issues (Python ints are unbounded, but
                              the expected value is checked exactly).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting T2 = 1 is a GIVEN base case, not something the recurrence
   derives -- trying to compute dp[2] from dp[-1] etc. is undefined.
2. Off-by-one in the loop range: iterating `range(3, n)` instead of
   `range(3, n+1)` leaves dp[n] one step short.
3. Shipping the naive recursive version because "n <= 37 is small" -- 3^37
   is billions of calls; it will not finish in any reasonable time even
   though the input bound looks tiny.
4. Using a mutable default argument (`def trib(n, memo={})`) for memoization
   without resetting it between calls -- fine for a single run but a classic
   Python footgun if the function is reused across test cases with different
   expected fresh state (not an issue here since none of the calls need
   isolation, but worth naming).


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do this without an array?" -> yes, three rolling variables (shown).
- "What if the recurrence reached back k terms instead of 3?" -> generalizes
  to k rolling variables / a fixed-size ring buffer, still O(n) time O(k) space.
- "What if n could be 10^9?" -> matrix exponentiation on the 3x3 companion
  matrix gets this to O(log n) time.


================================================================================
RELATED PROBLEMS
================================================================================
- 002 Climbing Stairs (LC 70) -- same shape, window of 2 instead of 3.
- 003 Min Cost Climbing Stairs (LC 746) -- window of 2, but minimizing
  instead of counting.
- Fibonacci Number (LC 509) -- the degenerate window-of-2 case.
================================================================================
"""

import sys
import time


class Solution:
    def tribonacci(self, n: int) -> int:
        if n == 0:
            return 0
        if n in (1, 2):
            return 1
        a, b, c = 0, 1, 1  # dp[i-3], dp[i-2], dp[i-1]
        for _ in range(3, n + 1):
            a, b, c = b, c, a + b + c
        return c


def tribonacci_naive(n: int) -> int:
    if n == 0:
        return 0
    if n in (1, 2):
        return 1
    return tribonacci_naive(n - 1) + tribonacci_naive(n - 2) + tribonacci_naive(n - 3)


def tribonacci_memo(n: int, memo=None) -> int:
    if memo is None:
        memo = {}
    if n == 0:
        return 0
    if n in (1, 2):
        return 1
    if n in memo:
        return memo[n]
    memo[n] = tribonacci_memo(n - 1, memo) + tribonacci_memo(n - 2, memo) + tribonacci_memo(n - 3, memo)
    return memo[n]


def tribonacci_tab(n: int) -> int:
    if n == 0:
        return 0
    if n in (1, 2):
        return 1
    dp = [0] * (n + 1)
    dp[1], dp[2] = 1, 1
    for i in range(3, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2] + dp[i - 3]
    return dp[n]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (0, 0),
        (1, 1),
        (2, 1),
        (3, 2),
        (4, 4),
        (25, 1389537),
        (37, 2082876103),
    ]
    for n, want in cases:
        got = sol.tribonacci(n)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:2d}  -> {got}  (want {want})")
        assert tribonacci_memo(n) == want
        assert tribonacci_tab(n) == want

    print()
    print("RUNTIME DEMO -- naive O(3^n) recursion vs memoized O(n), measured live")
    print("-" * 72)
    sys.setrecursionlimit(10000)
    for n in (10, 20, 27):
        t0 = time.perf_counter()
        naive_result = tribonacci_naive(n)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        memo_result = tribonacci_memo(n)
        memo_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == memo_result
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   memo={memo_ms:7.4f} ms   "
              f"ratio={naive_ms / max(memo_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
