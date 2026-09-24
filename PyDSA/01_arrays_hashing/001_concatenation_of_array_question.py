"""
================================================================================
LeetCode 1929 · Concatenation of Array                                   [Easy]
https://leetcode.com/problems/concatenation-of-array/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an integer array `nums` of length n, you want to create an array `ans` of
length 2n where `ans[i] == nums[i]` and `ans[i + n] == nums[i]` for
0 <= i < n (0-indexed).

Specifically, `ans` is the concatenation of two `nums` arrays.

Return the array `ans`.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,1]
    Output: [1,2,1,1,2,1]
    Explanation: The array ans is formed as follows:
      - ans = [nums[0],nums[1],nums[2],nums[0],nums[1],nums[2]]
      - ans = [1,2,1,1,2,1]

Example 2:
    Input:  nums = [1,3,2,1]
    Output: [1,3,2,1,1,3,2,1]
    Explanation: The array ans is formed as follows:
      - ans = [nums[0],nums[1],nums[2],nums[3],nums[0],nums[1],nums[2],nums[3]]
      - ans = [1,3,2,1,1,3,2,1]


CONSTRAINTS
-----------
    n == nums.length
    1 <= n <= 1000
    1 <= nums[i] <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the gentlest problem in the entire set. Its job is not to challenge you —
it is to make you write an array-building loop deliberately and to introduce the
index arithmetic `ans[i + n]` that shows up constantly later (circular arrays,
rotations, doubled arrays for "next greater element in a circular array").

Read the requirement literally:

    ans[i]     == nums[i]        <- first copy, at offset 0
    ans[i + n] == nums[i]        <- second copy, at offset n

So position `i` in the second half is position `i + n` in the output. That single
"+ n offset" idea is the whole problem.

    nums  = [1, 2, 1]                n = 3
             0  1  2

    ans   = [1, 2, 1, 1, 2, 1]
             0  1  2  3  4  5
             └──first──┘ └─second─┘
                          i+n where i = 0,1,2


WHAT TO THINK ABOUT
-------------------
1. What is the length of the output? You know it up front — can you preallocate?
2. Can you do it in ONE loop instead of two?
3. Python has a one-liner for this. Do you know it? Do you also know how to
   write it manually, in case an interviewer asks you not to use the shortcut?


PROGRESSIVE HINTS
-----------------
Hint 1: The output has exactly 2 * len(nums) elements. You never need to grow
        the array by guessing.

Hint 2: A single loop over `i` in range(n) can write BOTH copies per iteration:
        one at index i, one at index i + n.

Hint 3: In Python, `nums + nums` or `nums * 2` already does this. Know that,
        but also be able to write the explicit loop.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n) for the output (this is required, so it does not count against
           you — "O(1) extra space" would mean beyond the output).
================================================================================
"""

from typing import List


class Solution:
    def getConcatenation(self, nums: List[int]) -> List[int]:
        n = len(nums)
        output = [0] * (2*n)
        for i in range(n):
            output[i] = nums[i]
            output[i+n] = nums[i]
        return output


# ==============================================================================
# TESTS — run this file directly:  python 001_concatenation_of_array_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 1], [1, 2, 1, 1, 2, 1]),
        ([1, 3, 2, 1], [1, 3, 2, 1, 1, 3, 2, 1]),
        ([1], [1, 1]),
        ([7, 7], [7, 7, 7, 7]),
    ]
    passed = 0
    for nums, expected in cases:
        got = sol.getConcatenation(list(nums))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums}")
        print(f"      expected={expected}")
        print(f"      got     ={got}")
    print(f"\n{passed}/{len(cases)} passed")


def modulo(num1, num2: int) -> int:
    return num1 % num2

if __name__ == "__main__":
    # i should not be greater or equal to 3
    print(f"Modulo: {modulo(20, 6)}")
    # run_tests()
