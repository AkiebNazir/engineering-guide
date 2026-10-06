"""
================================================================================
SOLUTION · LeetCode 198 · House Robber                                [Medium]
https://leetcode.com/problems/house-robber/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "the max loot achievable using only houses 0..i". At house i
there are exactly two options -- skip it (dp[i-1]) or rob it (nums[i] plus
the best using houses 0..i-2, since i-1 becomes forbidden):

    dp[i] = max(dp[i-1], dp[i-2] + nums[i])

Fixed window of 2 back, MAX instead of SUM -- same shape as climbing
stairs and min-cost-climbing-stairs, different combining operator.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion, price it, don't ship it):
    def rob(i): return 0 if i < 0 else max(rob(i-1), nums[i] + rob(i-2))
called as rob(n-1). O(2^n) -- rob(i-2) is recomputed once directly and
once more inside the rob(i-1) branch, identical duplication pattern to
every earlier problem in this folder.

Approach 1 (memoized top-down) [`rob_memo`] -- cache each index. O(n)
time, O(n) space.

Approach 2 (tabulated bottom-up) [`rob_tab`] -- fill dp[0..n-1] left to
right. O(n) time, O(n) space.

Approach 3 (space-optimized) [chosen] -- dp[i] only reads dp[i-1] and
dp[i-2], roll two variables. O(n) time, O(1) space.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [2, 7, 9, 3, 1]

 i     : 0  1  2   3   4
nums[i]: 2  7  9   3   1
dp[i]  : 2  7  11  11  12
                ^        ^
    dp[2]=max(dp1, dp0+nums2)=max(7, 2+9)=11
    dp[4]=max(dp3, dp2+nums4)=max(11, 11+1)=12   <- answer

Rolling trace (prev2, prev1) = (dp[i-2], dp[i-1]) just before dp[i]:
    start:            prev2=2, prev1=7       (dp0, dp1)
    i=2: dp2=max(7,2+9)=11   -> prev2=7,  prev1=11
    i=3: dp3=max(11,7+3)=11  -> prev2=11, prev1=11
    i=4: dp4=max(11,11+1)=12 -> prev2=11, prev1=12
    return prev1 = 12


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
    len(nums) == 1        -> only one house, answer is nums[0] itself; no
                              "adjacent" constraint can even apply.
    len(nums) == 2         -> can only take one of the two (they're
                              adjacent); answer is max(nums[0], nums[1]).
    all zeros               -> robbing nothing is as good as robbing
                              anything; answer 0.
    alternating high/low
    values (2,7,9,3,1)       -> forces the max() to genuinely choose between
                              skip vs rob rather than one dominant strategy.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting dp[i-1] itself might already include robbing house i-2 (or
   not) -- dp[i-1] is a MAX over both possibilities already, so
   dp[i] = max(dp[i-1], dp[i-2] + nums[i]) is correct without needing to
   separately track "did I rob the previous house."
2. Trying to track a boolean "robbed previous house?" as extra state --
   unnecessary; dp[i-1] already encodes the best answer regardless of
   whether house i-1 itself was robbed.
3. Off-by-one when initializing: dp[0] = nums[0], NOT max(nums[0], nums[1])
   or 0 -- must match "using only houses 0..0."
4. Not handling len(nums) == 1 as a special case before indexing nums[1].


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if the houses are arranged in a CIRCLE?" -> House Robber II
  (problem 006): first and last houses become adjacent too, so run this
  exact function twice (excluding house 0, excluding house n-1) and take
  the max -- see 006 for why that decomposition is valid.
- "Can you reconstruct WHICH houses were robbed, not just the total?" ->
  track a parallel `choice[i]` boolean during tabulation, then walk it
  backwards from the end.
- "What if you could rob at most k houses total, still no two adjacent?"
  -> needs a genuinely 2D state (index, houses used so far) -- this no
  longer collapses to 1D.


================================================================================
RELATED PROBLEMS
================================================================================
- 006 House Robber II (LC 213) -- circular version, two linear passes.
- 002 Climbing Stairs (LC 70) -- same window-of-2 shape, SUM not MAX.
- 013 Longest Increasing Subsequence -- another "skip or take" 1D decision,
  but with an unbounded look-back instead of a fixed window.
================================================================================
"""

import sys
import time
from typing import List


class Solution:
    def rob(self, nums: List[int]) -> int:
        prev2, prev1 = 0, 0  # dp[i-2], dp[i-1], treating "before index 0" as 0
        for x in nums:
            prev2, prev1 = prev1, max(prev1, prev2 + x)
        return prev1


def rob_naive(nums: List[int], i: int = None) -> int:
    if i is None:
        i = len(nums) - 1
    if i < 0:
        return 0
    return max(rob_naive(nums, i - 1), nums[i] + rob_naive(nums, i - 2))


def rob_memo(nums: List[int]) -> int:
    memo = {}

    def solve(i: int) -> int:
        if i < 0:
            return 0
        if i in memo:
            return memo[i]
        memo[i] = max(solve(i - 1), nums[i] + solve(i - 2))
        return memo[i]

    return solve(len(nums) - 1)


def rob_tab(nums: List[int]) -> int:
    n = len(nums)
    if n == 1:
        return nums[0]
    dp = [0] * n
    dp[0] = nums[0]
    dp[1] = max(nums[0], nums[1])
    for i in range(2, n):
        dp[i] = max(dp[i - 1], dp[i - 2] + nums[i])
    return dp[n - 1]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([1, 2, 3, 1], 4),
        ([2, 7, 9, 3, 1], 12),
        ([2, 1, 1, 2], 4),
        ([5], 5),
        ([5, 5], 5),
        ([0, 0, 0], 0),
        ([200, 3, 140, 20, 10], 350),
    ]
    for nums, want in cases:
        got = sol.rob(nums[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")
        assert rob_memo(nums[:]) == want
        assert rob_tab(nums[:]) == want

    print()
    print("RUNTIME DEMO -- naive O(2^n) recursion vs memoized O(n), measured live")
    print("-" * 72)
    sys.setrecursionlimit(10000)
    import random
    random.seed(0)
    for n in (10, 20, 28):
        arr = [random.randint(0, 400) for _ in range(n)]
        t0 = time.perf_counter()
        naive_result = rob_naive(arr)
        naive_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        memo_result = rob_memo(arr)
        memo_ms = (time.perf_counter() - t0) * 1000

        assert naive_result == memo_result
        print(f"n={n:3d}  naive={naive_ms:9.3f} ms   memo={memo_ms:7.4f} ms   "
              f"ratio={naive_ms / max(memo_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
