"""
================================================================================
LeetCode 303 · Range Sum Query - Immutable                              [Easy]
https://leetcode.com/problems/range-sum-query-immutable/
Topic: 04 · Prefix Sum
================================================================================

PROBLEM
-------
Given an integer array `nums`, handle multiple queries of the following type:
    Calculate the sum of the elements of `nums` between indices `left` and
    `right` INCLUSIVE, where `left <= right`.

Implement the `NumArray` class:
    NumArray(nums: List[int])            initializes the object with the
                                           integer array `nums`.
    sumRange(left: int, right: int)       returns the sum of the elements of
                                           `nums` between indices `left` and
                                           `right` INCLUSIVE
                                           (i.e. nums[left] + ... + nums[right]).


EXAMPLES
--------
Example 1:
    Input:
        ["NumArray", "sumRange", "sumRange", "sumRange"]
        [[[-2, 0, 3, -5, 2, -1]], [0, 2], [2, 5], [0, 5]]
    Output:
        [null, 1, -1, -3]

    Explanation:
        NumArray numArray = new NumArray([-2, 0, 3, -5, 2, -1]);
        numArray.sumRange(0, 2); // (-2) + 0 + 3 = 1
        numArray.sumRange(2, 5); // 3 + (-5) + 2 + (-1) = -1
        numArray.sumRange(0, 5); // (-2) + 0 + 3 + (-5) + 2 + (-1) = -3


CONSTRAINTS
-----------
    1 <= nums.length <= 10^4
    -10^5 <= nums[i] <= 10^5
    0 <= left <= right < nums.length
    At most 10^4 calls will be made to sumRange.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a DESIGN problem, not a single function — you build a class that gets
constructed ONCE and then queried MANY times (the problem explicitly warns
"at most 10^4 calls to sumRange"). That number is the whole point: whatever
work you do per query gets paid up to 10,000 times, so it had better be as
cheap as possible.

This is THE canonical demonstration of the topic guide's central trade
(§1.0): pay O(n) ONCE, up front, in the constructor, to make every future
`sumRange` call O(1). Compare that to the naive approach — slicing and
summing `nums[left:right+1]` fresh on every call — which pays O(right-left)
EVERY time, and over thousands of queries that adds up to real, measurable
time. The runtime demo in the solution file benchmarks exactly this gap.

    nums   = [-2, 0, 3, -5, 2, -1]
    index     0   1  2   3  4   5

    prefix = [0, -2, -2, 1, -4, -2, -3]
    index     0   1   2  3   4   5   6

    sumRange(0, 2) = prefix[3] - prefix[0] = 1 - 0 = 1     ✓
    sumRange(2, 5) = prefix[6] - prefix[2] = -3 - (-2) = -1 ✓
    sumRange(0, 5) = prefix[6] - prefix[0] = -3 - 0 = -3    ✓

See the topic guide §1.0 for the derivation of `prefix[r+1] - prefix[l]`.


WHAT TO THINK ABOUT
--------------------
1. What work belongs in `__init__`, and what work belongs in `sumRange`?
   Getting this split right IS the problem.

2. Why build a prefix array of length `n + 1` (with a leading 0) rather than
   length `n`? What would the query formula look like if you didn't?

3. What if `sumRange` is called with `left == right` (a single element)?
   Does your formula still work without a special case?

4. What if `sumRange(0, len(nums)-1)` is called — the WHOLE array? Same
   question: no special case should be needed.

5. What if `nums` has only one element? The constructor still runs, and
   the only legal query is `sumRange(0, 0)`.


PROGRESSIVE HINTS
------------------
Hint 1: In `__init__`, build `self.prefix = [0] * (len(nums) + 1)`, then
        `self.prefix[i+1] = self.prefix[i] + nums[i]` for each i.

Hint 2: In `sumRange(left, right)`, return
        `self.prefix[right + 1] - self.prefix[left]`.
        No loop, no slicing — one subtraction.

Hint 3: Resist the urge to slice `nums[left:right+1]` and call `sum()` on
        it inside `sumRange`. It gives the right ANSWER but defeats the
        entire purpose of precomputing — that is Approach 0 in the solution
        file, benchmarked to show exactly how much it costs at scale.


COMPLEXITY TARGET
------------------
    __init__:   O(n) time,  O(n) space  — build the prefix array once
    sumRange:   O(1) time                — one subtraction per call
================================================================================
"""

from typing import List


class NumArray:
    def __init__(self, nums: List[int]):
        # YOUR CODE HERE
        pass

    def sumRange(self, left: int, right: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 002_range_sum_query_immutable_question.py
# ==============================================================================
class _NumArrayBrute:
    """O(right-left) per query reference: slice and sum every call."""

    def __init__(self, nums):
        self.nums = nums

    def sumRange(self, left, right):
        return sum(self.nums[left:right + 1])


def run_tests() -> None:
    cases = [
        ([-2, 0, 3, -5, 2, -1], [(0, 2), (2, 5), (0, 5)], [1, -1, -3]),
        ([1], [(0, 0)], [1]),                       # single-element array
        ([5, 5, 5, 5], [(0, 0), (1, 1), (0, 3)], [5, 5, 20]),  # left==right, whole array
        ([-1, -1, -1], [(0, 2)], [-3]),              # all negative
        ([0, 0, 0], [(0, 1), (1, 2)], [0, 0]),        # all zeros
        ([7, -3, 4, -8, 2, 9], [(0, 5), (3, 3), (1, 4)], [11, -8, -5]),
    ]

    passed = total = 0
    for nums, queries, expected in cases:
        oracle = _NumArrayBrute(list(nums))
        # cross-check the hand-written expectation against the oracle
        for (l, r), exp in zip(queries, expected):
            assert oracle.sumRange(l, r) == exp, (
                f"bad test expectation for nums={nums} range=({l},{r}): "
                f"oracle says {oracle.sumRange(l, r)}, test says {exp}")

        na = NumArray(list(nums))
        for (l, r), exp in zip(queries, expected):
            total += 1
            got = na.sumRange(l, r)
            ok = got == exp
            passed += ok
            print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<28} "
                  f"sumRange({l},{r}) -> {got}  (want {exp})")

    print(f"\n{passed}/{total} passed")


if __name__ == "__main__":
    run_tests()
