"""
================================================================================
SOLUTION · LeetCode 300 · Longest Increasing Subsequence               [Medium]
https://leetcode.com/problems/longest-increasing-subsequence/
================================================================================

THE CORE IDEA
--------------
dp[i] MEANS "the length of the longest increasing subsequence ENDING
exactly at index i". The last decision was "which earlier, SMALLER
element does this one extend":

    dp[i] = 1 + max(dp[j] for j < i if nums[j] < nums[i], default=0)
    answer = max(dp)             # NOT necessarily dp[n-1]

O(n^2) DP is the natural first answer. The O(n log n) approach (patience
sorting) is a DIFFERENT technique, not a space optimization of the DP --
it maintains a "tails" array and binary-searches it, only recovering the
LENGTH directly (not the DP table itself).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive recursion over subsequences, price it, don't ship it):
enumerate include/exclude decisions for every element like a subset-sum
backtracking tree, checking the increasing constraint along the way.
O(2^n) -- the raw combinatorial explosion of all subsequences.

Approach 1 (memoized top-down) [`lis_memo`] -- dp(i) = longest increasing
subsequence starting or ending at i, cached. O(n^2) time, O(n) space +
recursion depth.

Approach 2 (tabulated O(n^2) DP) [`lis_dp_tab`] -- the dp[i] recurrence
above, filled left to right. O(n^2) time, O(n) space. This is the version
most people should be able to derive and code correctly under interview
time pressure.

Approach 3 (patience sorting / binary search on tails) [chosen] --
maintain `tails`, where tails[k] is the SMALLEST tail value achievable by
an increasing subsequence of length k+1 seen so far. For each new number
x: binary-search tails for the leftmost position where x could sit
(bisect_left), and either extend tails (x is bigger than everything seen)
or replace that position (x gives a smaller/equal tail for that length,
which is strictly better for extending later). `len(tails)` at the end IS
the answer. O(n log n) time, O(n) space. tails is NOT itself a valid
subsequence of nums -- it only tracks achievable tail VALUES per length.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [10, 9, 2, 5, 3, 7, 101, 18]

O(n^2) DP table:
 i     : 0   1  2  3  4  5  6    7
nums[i]: 10  9  2  5  3  7  101  18
dp[i]  : 1   1  1  2  2  3  4    4
              (dp[3]=1+dp[2]=2 since nums[2]=2<5; dp[5]=1+max(dp[2],dp[3],dp[4])=1+2=3
               since nums[2..4] < 7; dp[6]=1+max over all j<6 with nums[j]<101 =1+3=4)
answer = max(dp) = 4    (subsequence [2,3,7,101] or [2,5,7,101] etc.)

Patience-sorting `tails` walkthrough:
    x=10:  tails=[]        -> append           -> tails=[10]
    x=9:   bisect_left([10],9)=0 -> replace idx0 -> tails=[9]
    x=2:   bisect_left([9],2)=0  -> replace idx0 -> tails=[2]
    x=5:   bisect_left([2],5)=1  -> append        -> tails=[2,5]
    x=3:   bisect_left([2,5],3)=1 -> replace idx1  -> tails=[2,3]
    x=7:   bisect_left([2,3],7)=2 -> append        -> tails=[2,3,7]
    x=101: bisect_left([2,3,7],101)=3 -> append    -> tails=[2,3,7,101]
    x=18:  bisect_left([2,3,7,101],18)=3 -> replace idx3 -> tails=[2,3,7,18]
    final len(tails) = 4                                  <- answer

(Note tails ends as [2,3,7,18] -- NOT the actual LIS [2,3,7,101] found by
the DP table; tails only tracks the smallest achievable tail per length,
which is exactly enough to get the LENGTH right without reconstructing
the sequence.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time      Space   Mutates input?
    -------------------------------------  --------  ------  --------------
    Naive subsequence recursion             O(2^n)   O(n)    no
    Memoized top-down                       O(n^2)   O(n)    no
    Tabulated O(n^2) DP                     O(n^2)   O(n)    no
    Patience sorting (binary search) [chosen] O(n log n) O(n) no


================================================================================
EDGE CASES
================================================================================
    all elements equal ([7]*7)   -> STRICTLY increasing required, so no
                                    element can extend another; every dp[i]=1,
                                    tails only ever has length 1 (each new
                                    equal value replaces tails[0] via
                                    bisect_left, never appends).
    strictly increasing input     -> the whole array is the answer;
                                    tails grows by one element every step,
                                    never replacing.
    strictly decreasing input     -> answer is 1; tails[0] gets replaced
                                    by every new (smaller) element, never
                                    grows past length 1.
    the LIS doesn't end at the
    last element ([10,9,2,5,3,7,101,18]
    ends with 18, but LIS ends at 101)
                                   -> confirms the answer must be max(dp),
                                    not dp[-1].


================================================================================
COMMON MISTAKES
================================================================================
1. Using bisect_right instead of bisect_left in the patience-sorting
   version -- since the subsequence must be STRICTLY increasing, equal
   values must NOT extend the previous tail; bisect_left finds the
   correct replace-vs-append position for that (bisect_right would be
   correct for a NON-decreasing / "longest non-decreasing subsequence"
   variant instead).
2. Believing `tails` after the algorithm IS a valid LIS of nums -- it is
   only a per-length bookkeeping array of smallest achievable tails, as
   shown in the trace above; reconstructing the actual subsequence needs
   separate parent-pointer bookkeeping.
3. Returning dp[n-1] instead of max(dp) in the O(n^2) version -- the
   longest increasing subsequence need not end at the last element.
4. Confusing "subsequence" (elements can be non-contiguous, order
   preserved) with "subarray" (must be contiguous) -- this problem is
   explicitly the former.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you reconstruct the actual LIS, not just its length?" -> in the
  O(n^2) DP, track a `prev[i]` parent pointer alongside dp[i] pointing at
  the j that gave the best extension, then walk it back from
  argmax(dp). In the O(n log n) version, also track parent pointers
  per-append/replace to reconstruct via the tails' history.
- "What about the longest NON-decreasing subsequence (duplicates allowed
  to extend)?" -> switch bisect_left to bisect_right in the tails version;
  in the DP version change the strict `<` to `<=`.
- "Russian Doll Envelopes (LC 354)?" -> sort by one dimension, then this
  exact LIS algorithm on the other dimension (with a tie-breaking twist
  to avoid illegally "nesting" equal-width envelopes).


================================================================================
RELATED PROBLEMS
================================================================================
- Russian Doll Envelopes (LC 354) -- LIS applied after a 2D sort.
- Longest Increasing Path in a Matrix (LC 329) -- LIS's DAG-shortest-path
  generalization onto a grid, memoized DFS instead of a 1D scan.
- 012 Word Break -- same "scan valid earlier positions" variable-range look-back.
================================================================================
"""

import bisect
import time
from typing import List


class Solution:
    def lengthOfLIS(self, nums: List[int]) -> int:
        tails: List[int] = []
        for x in nums:
            pos = bisect.bisect_left(tails, x)
            if pos == len(tails):
                tails.append(x)
            else:
                tails[pos] = x
        return len(tails)


def lis_naive(nums: List[int]) -> int:
    n = len(nums)

    def solve(i: int, prev: int) -> int:
        if i == n:
            return 0
        skip = solve(i + 1, prev)
        take = 0
        if prev is None or nums[i] > prev:
            take = 1 + solve(i + 1, nums[i])
        return max(skip, take)

    return solve(0, None)


def lis_dp_tab(nums: List[int]) -> int:
    n = len(nums)
    dp = [1] * n
    for i in range(n):
        for j in range(i):
            if nums[j] < nums[i]:
                dp[i] = max(dp[i], dp[j] + 1)
    return max(dp) if dp else 0


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([10, 9, 2, 5, 3, 7, 101, 18], 4),
        ([0, 1, 0, 3, 2, 3], 4),
        ([7, 7, 7, 7, 7, 7, 7], 1),
        ([1], 1),
        ([1, 2, 3, 4, 5], 5),
        ([5, 4, 3, 2, 1], 1),
        ([4, 10, 4, 3, 8, 9], 3),
    ]
    for nums, want in cases:
        got = sol.lengthOfLIS(nums[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")
        assert lis_dp_tab(nums[:]) == want

    # naive recursion only on the smaller cases -- exponential
    for nums, want in cases[:4] + [cases[6]]:
        assert lis_naive(nums[:]) == want

    print()
    print("RUNTIME DEMO -- O(n^2) DP vs O(n log n) patience sorting, measured live")
    print("-" * 72)
    import random
    random.seed(0)
    for n in (500, 2000, 6000):
        arr = [random.randint(0, 10 ** 6) for _ in range(n)]
        t0 = time.perf_counter()
        dp_result = lis_dp_tab(arr)
        dp_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        fast_result = sol.lengthOfLIS(arr)
        fast_ms = (time.perf_counter() - t0) * 1000

        assert dp_result == fast_result
        print(f"n={n:5d}  O(n^2)_dp={dp_ms:9.3f} ms   O(n log n)_tails={fast_ms:7.4f} ms   "
              f"ratio={dp_ms / max(fast_ms, 1e-6):8.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
