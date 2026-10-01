"""
================================================================================
LeetCode 1480 · Running Sum of 1d Array                                 [Easy]
https://leetcode.com/problems/running-sum-of-1d-array/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given an array `nums`, return its RUNNING SUM, where

    runningSum[i] = nums[0] + nums[1] + ... + nums[i]


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3,4]
    Output: [1,3,6,10]
    Explanation: Running sum is [1, 1+2, 1+2+3, 1+2+3+4] = [1, 3, 6, 10].

Example 2:
    Input:  nums = [1,1,1,1,1]
    Output: [1,2,3,4,5]

Example 3:
    Input:  nums = [3,1,2,10,1]
    Output: [3,4,6,16,17]


CONSTRAINTS
-----------
    1 <= nums.length <= 1000
    -10^6 <= nums[i] <= 10^6


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the whole topic with nothing hidden. Every later problem in this
folder computes a `prefix` array and then does SOMETHING clever with it (an
O(1) range query, a hashmap lookup, a running-total comparison). Here, the
prefix array IS the output. There is no second step.

    nums   = [1, 2,  3,  4]
    output = [1, 3,  6, 10]
             ^   ^   ^   ^
             |   |   |   +-- 1+2+3+4
             |   |   +------ 1+2+3
             |   +---------- 1+2
             +-------------- 1

The topic guide (§1.0) defines a SHIFTED prefix array with an extra leading
0 so that `prefix[i]` means "sum of the first i elements" and range sums
become a clean subtraction. This problem asks for the UNSHIFTED version —
`output[i] = sum(nums[0..i])` inclusive of index i — which is just
`prefix[i+1]` from that convention. Notice both: they are the same idea, one
index apart.


WHAT TO THINK ABOUT
--------------------
1. Do you need to look ahead, or only remember what came before? A running
   total only needs ONE number carried from the previous index.

2. Can you build the output IN PLACE (mutate `nums` itself, or build into
   `nums` as you go) instead of allocating a second array? LeetCode's own
   editorial highlights this. What are the trade-offs of doing so? (Hint:
   it changes what the CALLER sees if they hold a reference to the same
   list — see the complexity table's "mutates input?" column in the
   solution file.)

3. What happens if you recompute `sum(nums[:i+1])` fresh at every index
   instead of carrying a running total? Time yourself against a running
   accumulator at a few sizes and see if you can tell the difference — the
   solution file measures this for real.

4. Edge cases: an empty array, a single-element array, negative numbers,
   an array of all zeros. Does your approach handle each without a special
   case?


PROGRESSIVE HINTS
------------------
Hint 1: Keep a running variable `total = 0`. For each `x` in `nums`:
        `total += x`; append `total` to the result.

Hint 2: `itertools.accumulate(nums)` does exactly this in one call, but write
        the loop by hand first — the loop IS the algorithm this topic is
        built on.

Hint 3: In-place: `nums[i] += nums[i - 1]` for `i` from 1 upward, then return
        `nums`. This uses O(1) EXTRA space (beyond the output itself) but
        destroys the caller's original array — decide if that is acceptable.


COMPLEXITY TARGET
------------------
    Time:  O(n)  — one pass, one running total
    Space: O(n)  — for the output array (O(1) extra if mutating in place)
================================================================================
"""

from typing import List


class Solution:
    def runningSum(self, nums: List[int]) -> List[int]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 001_running_sum_of_1d_array_question.py
# ==============================================================================
def _brute(nums):
    """O(n^2) reference: re-sum the prefix from scratch at every index."""
    return [sum(nums[:i + 1]) for i in range(len(nums))]


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 3, 4], [1, 3, 6, 10]),
        ([1, 1, 1, 1, 1], [1, 2, 3, 4, 5]),
        ([3, 1, 2, 10, 1], [3, 4, 6, 16, 17]),
        ([5], [5]),                          # single element
        ([0, 0, 0, 0], [0, 0, 0, 0]),        # all zeros
        ([-1, -2, -3], [-1, -3, -6]),        # negative numbers
        ([-1, 2, -3, 4], [-1, 1, -2, 2]),    # mixed signs
        ([1000000, 1000000], [1000000, 2000000]),  # near the constraint bound
    ]

    passed = 0
    for nums, expected in cases:
        # cross-check the hand-written expectation against the oracle
        assert _brute(nums) == expected, (
            f"bad test expectation for {nums!r}: "
            f"oracle says {_brute(nums)}, test says {expected}")
        got = sol.runningSum(list(nums))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  {nums!r:<24} -> {got}  "
              f"(want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
