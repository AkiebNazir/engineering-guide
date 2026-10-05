"""
================================================================================
LeetCode 238 · Product of Array Except Self                            [Medium]
https://leetcode.com/problems/product-of-array-except-self/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an integer array `nums`, return an array `answer` such that `answer[i]`
is equal to the product of all the elements of `nums` EXCEPT `nums[i]`.

The product of any prefix or suffix of `nums` is guaranteed to fit in a
32-bit integer.

You must write an algorithm that runs in O(n) time and WITHOUT USING THE
DIVISION operation.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3,4]
    Output: [24,12,8,6]

Example 2:
    Input:  nums = [-1,1,0,-3,3]
    Output: [0,0,9,0,0]


CONSTRAINTS
-----------
    2 <= nums.length <= 10^5
    -30 <= nums[i] <= 30
    The product of any prefix or suffix of nums is guaranteed to fit in a
    32-bit integer.


FOLLOW UP
---------
    Can you solve the problem in O(1) extra space complexity? (The output array
    does NOT count as extra space for space complexity analysis.)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

The instinct is total product ÷ nums[i]. The problem bans division — and the
ban is not arbitrary decoration. Ask what division would break on:

    nums = [1, 2, 0, 4]      total = 0
    answer[0] = 0 / 1 = 0    ✓ by luck
    answer[2] = 0 / 0        ✗ ZeroDivisionError

Zeros destroy the division trick. You can patch it by counting zeros and
special-casing (one zero → only that slot is nonzero; two zeros → all zeros),
but that is three branches of fiddly logic. The ban pushes you toward an
approach that has no special cases at all.

So: what IS answer[i], structurally?

    answer[i] = (everything to the LEFT of i)  ×  (everything to the RIGHT of i)

    nums   = [ 1,  2,  3,  4 ]
               ↑
             i = 2
    left  of index 2 = 1 × 2 = 2
    right of index 2 = 4     = 4
    answer[2]        = 2 × 4 = 8      ✓

Nothing about that formula mentions nums[i] at all — it is EXCLUDED by
construction, not by dividing it back out. That is the whole idea.

Now the efficiency question: computing "everything to the left of i" from
scratch for each i is O(n) per element, O(n²) total. But the left product for
index i+1 is just the left product for index i times nums[i]. Each one is one
multiply away from the previous. That is a RUNNING PRODUCT.


WHAT TO THINK ABOUT
-------------------
1. Define prefix[i] = product of nums[0..i-1] and suffix[i] = product of
   nums[i+1..n-1]. What is prefix[0]? What is suffix[n-1]? (Careful — the
   answer is not 0.)

2. Can you build the whole prefix array in one left-to-right pass, and the
   whole suffix array in one right-to-left pass? What is the recurrence?

3. That uses two extra arrays. The follow-up wants O(1) extra space. You are
   allowed to write into the OUTPUT array. Can you store the prefixes there
   first, then fold the suffixes in during a second pass using just one
   scalar variable?

4. Check your approach against [0, 0]: no division, so does it just work?


PROGRESSIVE HINTS
-----------------
Hint 1: answer[i] = (product of everything left of i) × (product of everything
        right of i). Two independent halves.

Hint 2: The identity for an empty product is 1, not 0. prefix[0] = 1 because
        there is nothing to the left of index 0. Starting at 0 zeroes your
        entire answer.

Hint 3: Pass 1 — walk left to right, writing the running prefix product into
        answer[i] BEFORE multiplying nums[i] into the runner.
        Pass 2 — walk right to left with a scalar `suffix = 1`, doing
        `answer[i] *= suffix` then `suffix *= nums[i]`.
        The order matters in both passes: write, THEN update.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1) extra, excluding the output array
================================================================================
"""

from typing import List


class Solution:
    def productExceptSelf(self, nums: List[int]) -> List[int]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 010_product_of_array_except_self_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 3, 4], [24, 12, 8, 6]),
        ([-1, 1, 0, -3, 3], [0, 0, 9, 0, 0]),
        ([2, 3], [3, 2]),                       # minimum length
        ([0, 0], [0, 0]),                       # two zeros
        ([1, 0], [0, 1]),                       # exactly one zero
        ([0, 4, 0], [0, 0, 0]),                 # two zeros, spread out
        ([-1, -1, -1], [1, 1, 1]),              # sign bookkeeping
        ([1, 1, 1, 1], [1, 1, 1, 1]),
        ([5, 2, 1, 3], [6, 15, 30, 10]),
    ]
    passed = 0
    for nums, expected in cases:
        got = sol.productExceptSelf(list(nums))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} -> {got} (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
