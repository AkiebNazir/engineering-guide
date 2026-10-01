"""
================================================================================
SOLUTION · LeetCode 152 · Maximum Product Subarray                    [Medium]
https://leetcode.com/problems/maximum-product-subarray/
================================================================================

THE CORE IDEA
--------------
maxEnd[i] / minEnd[i] MEAN "the max / min product of a subarray ENDING
exactly at index i". Two rolling states are required (not one, unlike sum
-- Kadane's algorithm) because multiplying by a NEGATIVE number can flip
the smallest running product into the largest:

    candidates = (nums[i], maxEnd[i-1]*nums[i], minEnd[i-1]*nums[i])
    maxEnd[i] = max(candidates)
    minEnd[i] = min(candidates)
    answer = max(maxEnd[i] for all i)


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): compute the product of
every one of the O(n^2) subarrays directly. O(n^2) time (or O(n^3) if each
product is recomputed from scratch instead of extended incrementally),
O(1) space. Correct, quadratic, and the runtime demo below shows exactly
how it degrades.

Approach 1 (single running max, WRONG -- named as the classic trap):
copying Kadane's sum algorithm verbatim (`best = max(nums[i], best*nums[i])`,
tracking only a max) silently gives the WRONG answer whenever a negative
number should flip a very negative running product into the new best --
demonstrated live in the runtime/correctness demo below.

Approach 2 (max+min pair, rolling variables) [chosen] -- the fix: track
BOTH running extremes, as derived above. O(n) time, O(1) space.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [2, 3, -2, 4]

 i   : 0   1   2    3
num  : 2   3   -2   4
maxEnd: 2   6   -2*(-2)=4? let's expand:

i=0: maxEnd=2, minEnd=2
i=1 (num=3): candidates(3, 2*3=6, 2*3=6) -> maxEnd=6, minEnd=3
i=2 (num=-2): candidates(-2, 6*-2=-12, 3*-2=-6) -> maxEnd=-2, minEnd=-12
i=3 (num=4): candidates(4, -2*4=-8, -12*4=-48) -> maxEnd=4, minEnd=-48

 i     : 0  1  2   3
maxEnd : 2  6  -2  4
minEnd : 2  3  -12 -48

overall answer = max(2, 6, -2, 4) = 6   <- matches [2,3]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time    Space   Mutates input?
    ---------------------------------  ------  ------  --------------
    Brute force (every subarray)       O(n^2)  O(1)    no
    Single running max (WRONG)         O(n)    O(1)    no (but incorrect)
    Max+min rolling pair [chosen]      O(n)    O(1)    no


================================================================================
EDGE CASES
================================================================================
    a single negative flips a very
    negative running min into the
    new max ([-2,3,-4] -> 24)      -> exactly the scenario a single
                                      running-max approach gets wrong;
                                      demonstrated live below.
    a zero in the array              -> zero must "reset" both running
                                      products (nums[i] alone as one of
                                      the three candidates handles this:
                                      once a running product hits 0, the
                                      next index's candidates include the
                                      element alone, effectively starting
                                      a fresh subarray).
    all negative, even count         -> the full-array product is
                                      positive and IS the answer -- min
                                      and max must be tracked correctly
                                      across every sign flip to find it.
    all negative, odd count           -> the full array's product is
                                      negative; the true answer excludes
                                      either the first or last element to
                                      drop one negative factor.
    single element                    -> answer is that element itself,
                                      whether positive, negative, or zero.


================================================================================
COMMON MISTAKES
================================================================================
1. Tracking only a running MAX (copy-pasting Kadane's sum algorithm) --
   this is the single most common mistake on this problem; a negative
   number can turn the WORST running product into the BEST one, which a
   max-only tracker can never see coming. See the live correctness demo.
2. Forgetting to include `nums[i]` ALONE as one of the three candidates --
   without it, a subarray can never legally "restart" after a zero
   (or after a product that's become disadvantageous to extend).
3. Updating maxEnd using the ALREADY-UPDATED minEnd (or vice versa) within
   the same iteration -- both new values must be computed from the OLD
   (previous-iteration) maxEnd/minEnd simultaneously, e.g. via tuple
   assignment, not sequential reassignment.
4. Confusing "maximum product subarray" with "maximum product SUBSEQUENCE"
   -- the subarray must be CONTIGUOUS; picking non-adjacent elements
   (example 2's [-2,0,-1] tempting a "pick both negatives" answer of 2)
   is not allowed.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why doesn't Kadane's single-max trick work here?" -> because addition
  is monotmüonic in sign (a negative summand never helps), but
  multiplication is NOT -- two negatives make a positive, so the
  worst-so-far can become the best-so-far in one step.
- "Can you do it without extra space beyond two variables?" -> yes, shown.
- "What if the array can contain zero AND you need the actual subarray,
  not just the product?" -> track start/end indices alongside maxEnd,
  resetting them whenever a fresh single-element candidate wins.


================================================================================
RELATED PROBLEMS
================================================================================
- Maximum Subarray (LC 53, Kadane's algorithm) -- the SUM analog; single
  running max suffices there specifically because addition doesn't flip sign.
- 005 House Robber (LC 198) -- another "extend or restart" rolling-state
  1D DP, but MAX not MAX+MIN since there's no sign-flip hazard there.
================================================================================
"""

import time
from typing import List


class Solution:
    def maxProduct(self, nums: List[int]) -> int:
        max_end = min_end = result = nums[0]
        for num in nums[1:]:
            candidates = (num, max_end * num, min_end * num)
            max_end, min_end = max(candidates), min(candidates)
            result = max(result, max_end)
        return result


def max_product_brute_force(nums: List[int]) -> int:
    n = len(nums)
    best = nums[0]
    for i in range(n):
        prod = 1
        for j in range(i, n):
            prod *= nums[j]
            best = max(best, prod)
    return best


def max_product_single_max_WRONG(nums: List[int]) -> int:
    """The classic bug: copies Kadane's sum algorithm, tracking only a
    running MAX. Kept here purely to demonstrate it gives the WRONG
    answer whenever a negative number should flip the running MIN into
    the new best -- see the correctness demo in run_tests().
    """
    best_end = result = nums[0]
    for num in nums[1:]:
        best_end = max(num, best_end * num)
        result = max(result, best_end)
    return result


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([2, 3, -2, 4], 6),
        ([-2, 0, -1], 0),
        ([-2, 3, -4], 24),
        ([0, 2], 2),
        ([-1], -1),
        ([2, -5, -2, -4, 3], 24),
        ([-2, -3, 7], 42),
    ]
    for nums, want in cases:
        got = sol.maxProduct(nums[:])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}  -> {got}  (want {want})")
        assert max_product_brute_force(nums[:]) == want

    print()
    print("CORRECTNESS DEMO -- single-running-max (Kadane copy-paste) is WRONG here")
    print("-" * 72)
    trap_nums = [-2, 3, -4]
    correct = sol.maxProduct(trap_nums)
    wrong = max_product_single_max_WRONG(trap_nums)
    print(f"nums={trap_nums}")
    print(f"  max+min rolling pair (correct): {correct}   (the whole array: -2*3*-4=24)")
    print(f"  single running max (WRONG):     {wrong}")
    assert correct == 24
    assert wrong != correct, "expected the single-max version to actually be wrong here"

    print()
    print("RUNTIME DEMO -- brute force O(n^2) vs rolling max+min O(n), measured live")
    print("-" * 72)
    import random
    random.seed(0)
    for n in (200, 800, 3000):
        arr = [random.randint(-10, 10) or 1 for _ in range(n)]  # avoid zeros
        t0 = time.perf_counter()
        max_product_brute_force(arr)
        brute_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        sol.maxProduct(arr)
        fast_ms = (time.perf_counter() - t0) * 1000

        print(f"n={n:5d}  brute={brute_ms:9.3f} ms   rolling={fast_ms:7.4f} ms   "
              f"ratio={brute_ms / max(fast_ms, 1e-6):9.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
