"""
================================================================================
LeetCode 643 · Maximum Average Subarray I                                 [Easy]
https://leetcode.com/problems/maximum-average-subarray-i/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
You are given an integer array `nums` consisting of `n` elements, and an
integer `k`.

Find a contiguous subarray whose LENGTH IS EQUAL TO `k` that has the maximum
average value and return this value. Any answer with a calculation error less
than 10^-5 will be accepted.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,12,-5,-6,50,3], k = 4
    Output: 12.75000
    Explanation:
        Maximum average is (12 - 5 - 6 + 50) / 4 = 51 / 4 = 12.75

Example 2:
    Input:  nums = [5], k = 1
    Output: 5.00000


CONSTRAINTS
-----------
    n == nums.length
    1 <= k <= n <= 10^5
    -10^4 <= nums[i] <= 10^4          <- NOTE: values may be NEGATIVE


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the FIXED-SIZE window in its purest form. The window is always exactly
`k` wide — it never grows, never shrinks, and there is no validity condition to
restore. Every step does exactly one enter and one leave.

The brute force recomputes each window from scratch:

    for i in range(n - k + 1):
        best = max(best, sum(nums[i:i + k]))     # O(k) EVERY iteration

    That is O(n*k). With n = 10^5 and k = 5*10^4 it is 5*10^9 operations.

The fix is to notice that consecutive windows OVERLAP in k-1 elements:

    nums = [1, 12, -5, -6, 50, 3],  k = 4

      [1  12  -5  -6] 50   3        sum = 2
       1 [12  -5  -6  50]  3        sum = 2  + 50 - 1  = 51
       1  12 [-5  -6  50   3]       sum = 51 + 3  - 12 = 42
                                                 ^      ^
                                            entering  leaving

    Each slide is TWO arithmetic operations, not k additions. O(n) total.


THE ONE SIMPLIFICATION THAT MATTERS
-----------------------------------
Do not track the average. Every window has the SAME divisor `k`, so

    average(A) > average(B)   <=>   sum(A) > sum(B)

Maximise the integer SUM through the whole loop and divide exactly once, at the
end. Two reasons, and the second is the one interviewers care about:

    1. Fewer operations (no division per step).
    2. NO FLOATING-POINT ERROR ACCUMULATES. If you carry a float sum and
       add/subtract into it n times, rounding error compounds and two windows
       whose true sums differ can compare equal — or worse, backwards. Integer
       arithmetic in Python is exact and unbounded, so the comparison is exact.


A NOTE ON THE NEGATIVE VALUES
-----------------------------
`nums[i]` may be negative, and here that is COMPLETELY FINE — unlike LC 209
later in this folder, where negatives would break the algorithm outright.

Why the difference? A fixed-size window never makes a *decision* about where to
put `l`. It has no "shrink while invalid" step, so it never needs the
hereditary property from Part 1.2 of the topic guide. Sign only matters when
the sum's monotonicity is what licenses moving `l`.

Be ready to say that in one sentence: *"fixed windows are sign-agnostic because
they never shrink conditionally."*


WHAT TO THINK ABOUT
-------------------
1. What do you initialise `best` to? `0` is wrong. Find the input that proves
   it. (Hint: the constraints permit every element to be negative.)

2. Write the loop with `r` as the ENTERING index. Then:
       - which index LEAVES the window?
       - on which iterations is the window exactly k wide?
   Get these two bounds explicitly right before you write any code.

3. Can you write it without the `sum(nums[:k])` priming step, in one loop?
   That form generalises to every other problem in this folder.

4. What is the return TYPE? The judge wants a float. Python 3's `/` gives a
   float even for ints, but be deliberate about it.

5. Sanity check: how many windows of length k are there in an array of length
   n? Your loop must produce exactly that many candidate sums.


PROGRESSIVE HINTS
-----------------
Hint 1: Compute the sum of the FIRST window once: `s = sum(nums[:k])`. That is
        the only O(k) work you are allowed.

Hint 2: To slide from window starting at i to the one starting at i+1:
            s += nums[i + k] - nums[i]
        One element enters on the right, one leaves on the left.

Hint 3: Track `best = max(best, s)` as an INTEGER, initialised to the first
        window's sum (not 0). Return `best / k` after the loop.

Hint 4: The single-loop form, if you prefer it:
            s = 0
            for r, x in enumerate(nums):
                s += x
                if r >= k:  s -= nums[r - k]
                if r >= k - 1:  best = max(best, s)


COMPLEXITY TARGET
-----------------
    Time:  O(n)   — one pass; each element enters once and leaves once
    Space: O(1)   — one running sum, one best
================================================================================
"""

from typing import List


class Solution:
    def findMaxAverage(self, nums: List[int], k: int) -> float:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 002_maximum_average_subarray_i_question.py
# ==============================================================================
def _brute(nums, k):
    """O(n*k) reference: recompute every window from scratch."""
    return max(sum(nums[i:i + k]) for i in range(len(nums) - k + 1)) / k


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 12, -5, -6, 50, 3], 4),
        ([5], 1),
        ([0, 1, 1, 3, 3], 4),
        ([-1], 1),                        # all negative, k = 1
        ([-5, -3, -8, -2], 2),            # ALL NEGATIVE -> catches best = 0
        ([4, 0, 4, 3, 3], 5),             # k == n: exactly one window
        ([1, 2, 3, 4, 5], 1),             # k == 1: the plain maximum
        ([1, 2, 3, 4, 5], 2),
        ([8, 9, 1, 1, 1, 1], 2),          # best window is at the very front
        ([1, 1, 1, 1, 9, 8], 2),          # best window is at the very end
        ([-10000] * 5, 3),                # constraint extremes
        ([10000, -10000, 10000], 2),
        ([3, 3, 3, 3, 3], 3),             # flat: every window ties
    ]

    passed = 0
    for nums, k in cases:
        expected = _brute(nums, k)
        got = sol.findMaxAverage(list(nums), k)
        ok = got is not None and abs(got - expected) < 1e-5
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k:<2} {nums}\n"
              f"      -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
