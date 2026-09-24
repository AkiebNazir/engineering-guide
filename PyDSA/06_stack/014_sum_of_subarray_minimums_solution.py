"""
================================================================================
SOLUTION · LeetCode 907 · Sum of Subarray Minimums                      [Medium]
https://leetcode.com/problems/sum-of-subarray-minimums/
================================================================================

THE CORE IDEA
--------------
CONTRIBUTION TECHNIQUE. Each element arr[i] is the minimum of exactly
left[i] * right[i] subarrays, where

    left[i]  = distance to the previous element STRICTLY smaller  (or to -1)
    right[i] = distance to the next element SMALLER OR EQUAL      (or to n)

    answer = sum(arr[i] * left[i] * right[i])  mod 1e9+7

Previous/next smaller elements come from a monotonic increasing stack in
O(n). The asymmetric tie-break (strict on one side, non-strict on the other)
makes sure a subarray with repeated minimum values is credited to exactly one
of them.


================================================================================
APPROACH 1 · Enumerate subarrays (priced, used as an oracle)
================================================================================
    for i in range(n):
        m = inf
        for j in range(i, n):
            m = min(m, arr[j]); total += m

    Time: O(n^2) — 4.5 * 10^8 steps at n = 3 * 10^4.    Space: O(1)


================================================================================
APPROACH 2 · Monotonic stack + contribution ✅ (the answer)
================================================================================
One pass computes both distances. Keep a stack of indices with increasing
values. When arr[i] <= arr[top], pop `top`: arr[i] is top's next
smaller-or-equal, and the element now below top on the stack is top's previous
strictly-smaller. So top's contribution is known the moment it's popped.

    stack = []
    total = 0
    for i in range(n + 1):
        cur = arr[i] if i < n else 0          # sentinel 0 flushes the stack
        while stack and arr[stack[-1]] >= cur:
            mid = stack.pop()
            left = mid - (stack[-1] if stack else -1)
            right = i - mid
            total += arr[mid] * left * right
        stack.append(i)
    return total % MOD

The sentinel 0 at i = n is smaller than every value (arr[i] >= 1), so every
remaining index gets popped and credited with right = n - mid.

WHY THE TIE-BREAK MATTERS. We pop on `>=`, so an equal element to the RIGHT
ends mid's range (non-strict on the right), and an equal element left on the
stack BELOW mid... can't exist, because it would have been popped when mid
arrived. So mid's left boundary is the previous STRICTLY smaller element.
Strict on one side, non-strict on the other: each subarray's minimum is
credited to its RIGHTMOST occurrence of the minimum value, exactly once.

    Time: O(n) — each index pushed and popped once    Space: O(n)


================================================================================
APPROACH 3 · Monotonic stack + DP
================================================================================
Let dp[i] = sum of minimums of subarrays ENDING at i. If p is the previous
strictly-smaller index, then subarrays ending at i and starting after p have
min arr[i], and those starting at or before p have the same mins as the
subarrays ending at p:

    dp[i] = dp[p] + arr[i] * (i - p)          (dp[-1] = 0)
    answer = sum(dp)

    Time: O(n)    Space: O(n)


================================================================================
STEP BY STEP TRACE · arr = [3, 1, 2, 4]  (Approach 2)
================================================================================
    i  cur  pops (arr[top] >= cur)                         total   stack after
    -  ---  ---------------------------------------------  -----   -----------
    0   3   —                                                  0   [0]
    1   1   pop 0 (3): left = 0-(-1) = 1, right = 1-0 = 1
                       3 * 1 * 1 = 3                           3   [1]
    2   2   —                                                  3   [1,2]
    3   4   —                                                  3   [1,2,3]
    4   0   pop 3 (4): left = 3-2 = 1, right = 4-3 = 1 -> 4    7
            pop 2 (2): left = 2-1 = 1, right = 4-2 = 2 -> 4   11
            pop 1 (1): left = 1-(-1) = 2, right = 4-1 = 3 -> 6 17  [4]

    answer: 17

    Check element 1 (index 1): it's the min of every subarray containing
    index 1: start in {0, 1} (2 choices) x end in {1, 2, 3} (3 choices) = 6. ✓


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time     Space   Mutates input?
    ---------------------------  -------  ------  --------------
    Enumerate subarrays          O(n^2)   O(1)    No
    Stack + contribution ✅      O(n)     O(n)    No
    Stack + DP                   O(n)     O(n)    No


================================================================================
EDGE CASES
================================================================================
    n == 1                 The single element is its own min: arr[0].
    All equal [3,3,3]      6 subarrays * 3 = 18. The tie-break is what makes
                            this right.
    Strictly increasing     Each arr[i] extends only right... check with the
                            oracle; the stack pops everything at the sentinel.
    Large answer            Python ints don't overflow; still return % MOD.
                            In Go/Java/C++ apply mod as you accumulate.


================================================================================
COMMON MISTAKES
================================================================================
1. STRICT comparisons on BOTH sides. [2, 2] then counts the subarray [2, 2]
   for both 2s and returns 8 instead of 6. Demo below.

2. NON-STRICT on both sides. The subarray [2, 2] is credited to neither and
   the answer is too small.

3. Forgetting the sentinel (or the final flush), so elements still on the
   stack at the end never contribute.

4. In fixed-width languages, computing arr[i] * left * right without 64-bit
   math: 3 * 10^4 * 3 * 10^4 * 3 * 10^4 = 2.7 * 10^13 overflows 32 bits.

5. Thinking "each subarray has one min, so just pick the smallest element".
   The question is a SUM over all subarrays.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Sum of subarray MAXIMUMS?
A: Same code with the comparisons flipped (a monotonic DECREASING stack).

Q: Sum of subarray RANGES, max - min (LC 2104)?
A: sum of maximums minus sum of minimums. Two passes of this algorithm.

Q: Maximum of min(subarray) * sum(subarray) (LC 1856)?
A: Same previous/next smaller boundaries give each element's widest range as
   the minimum; combine with prefix sums.

Q: Why not a segment tree?
A: A sparse table or segment tree gives O(1) / O(log n) range-min queries, but
   you'd still have O(n^2) subarrays to query. The win here comes from never
   enumerating subarrays at all.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 84    Largest Rectangle in Histogram (010) — same previous/next smaller
    LC 2104  Sum of Subarray Ranges
    LC 1856  Maximum Subarray Min-Product
    LC 2281  Sum of Total Strength of Wizards — contribution + prefix of prefix
================================================================================
"""

import random
import time
from typing import List

MOD = 10**9 + 7


class Solution:
    def sumSubarrayMins(self, arr: List[int]) -> int:
        n = len(arr)
        stack: List[int] = []
        total = 0
        for i in range(n + 1):
            cur = arr[i] if i < n else 0
            while stack and arr[stack[-1]] >= cur:
                mid = stack.pop()
                left = mid - (stack[-1] if stack else -1)
                total += arr[mid] * left * (i - mid)
            stack.append(i)
        return total % MOD


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def sum_mins_brute(arr: List[int]) -> int:
    total = 0
    for i in range(len(arr)):
        m = arr[i]
        for j in range(i, len(arr)):
            if arr[j] < m:
                m = arr[j]
            total += m
    return total % MOD


def sum_mins_dp(arr: List[int]) -> int:
    n = len(arr)
    dp = [0] * n
    stack: List[int] = []
    for i, x in enumerate(arr):
        while stack and arr[stack[-1]] >= x:
            stack.pop()
        p = stack[-1] if stack else -1
        dp[i] = (dp[p] if p >= 0 else 0) + x * (i - p)
        stack.append(i)
    return sum(dp) % MOD


def sum_mins_strict_both_bug(arr: List[int]) -> int:
    """Mistake 1: previous STRICTLY smaller AND next STRICTLY smaller."""
    n = len(arr)
    left = [0] * n
    right = [0] * n
    stack: List[int] = []
    for i in range(n):
        while stack and arr[stack[-1]] >= arr[i]:
            stack.pop()
        left[i] = i - (stack[-1] if stack else -1)
        stack.append(i)
    stack = []
    for i in range(n - 1, -1, -1):
        while stack and arr[stack[-1]] >= arr[i]:     # BUG: should be >
            stack.pop()
        right[i] = (stack[-1] if stack else n) - i
        stack.append(i)
    return sum(arr[i] * left[i] * right[i] for i in range(n)) % MOD


# ==============================================================================
# TESTS — run:  python 014_sum_of_subarray_minimums_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: contribution vs DP vs brute force ---")
    cases = [
        ([3, 1, 2, 4], 17),
        ([11, 81, 94, 43, 3], 444),
        ([1], 1),
        ([2, 2], 6),
        ([3, 3, 3], 18),
        ([1, 2, 3], 10),
        ([3, 2, 1], 10),
    ]
    for arr, want in cases:
        results = (sol.sumSubarrayMins(arr), sum_mins_dp(arr), sum_mins_brute(arr))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  arr={arr}  got={results}  want={want}")

    print("\n--- randomized cross-check (800 arrays, heavy duplicates) ---")
    rng = random.Random(907)
    bad = 0
    for _ in range(800):
        arr = [rng.randint(1, 4) for _ in range(rng.randint(1, 20))]
        want = sum_mins_brute(arr)
        if sol.sumSubarrayMins(arr) != want or sum_mins_dp(arr) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  800 random arrays agree with brute force")

    print("\n--- mistake 1 LIVE: strict on both sides double-counts ties ---")
    wrong, right = sum_mins_strict_both_bug([2, 2]), sol.sumSubarrayMins([2, 2])
    ok = wrong == 8 and right == 6
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  [2, 2]: strict-both gives {wrong}, correct {right}")
    print("      subarrays [2],[2],[2,2]; the [2,2] min was credited to BOTH twos")
    over = sum(sum_mins_strict_both_bug(a) != sum_mins_brute(a)
               for a in ([rng.randint(1, 4) for _ in range(rng.randint(1, 20))] for _ in range(300)))
    print(f"      wrong on {over} of 300 random arrays with duplicates")

    print("\n--- benchmark: O(n^2) vs O(n) ---")
    for n in (2_000, 4_000, 8_000):
        arr = [rng.randint(1, 30_000) for _ in range(n)]
        t0 = time.perf_counter(); a = sum_mins_brute(arr); tb = time.perf_counter() - t0
        t0 = time.perf_counter(); b = sol.sumSubarrayMins(arr); ts = time.perf_counter() - t0
        all_ok &= a == b
        print(f"      n={n:>5}  brute {tb * 1000:8.1f} ms   stack {ts * 1000:6.2f} ms   ratio {tb / ts:6.0f}x")
    arr = [rng.randint(1, 30_000) for _ in range(30_000)]
    t0 = time.perf_counter(); sol.sumSubarrayMins(arr); ts = time.perf_counter() - t0
    print(f"      n=30,000 (constraint max): stack {ts * 1000:.1f} ms; brute force would be ~14x the n=8,000 time")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
