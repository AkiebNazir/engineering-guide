"""
================================================================================
LeetCode 31 · Next Permutation                                          [Medium]
https://leetcode.com/problems/next-permutation/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
A permutation of an array of integers is an arrangement of its members into a
sequence. The NEXT PERMUTATION is the next arrangement in lexicographic
(dictionary) order. If the array is already the largest arrangement, the next
permutation wraps around to the smallest one (sorted ascending).

Given an array `nums`, rearrange it IN PLACE into its next permutation, using
only constant extra memory.


EXAMPLES
--------
Example 1:   [1, 2, 3]  ->  [1, 3, 2]
Example 2:   [3, 2, 1]  ->  [1, 2, 3]     (largest wraps to smallest)
Example 3:   [1, 1, 5]  ->  [1, 5, 1]

All permutations of [1, 2, 3] in order:
    [1,2,3] -> [1,3,2] -> [2,1,3] -> [2,3,1] -> [3,1,2] -> [3,2,1] -> [1,2,3]


CONSTRAINTS
-----------
    1 <= nums.length <= 100
    0 <= nums[i] <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Think of the array as a number, e.g. 1 5 8 4 7 6 5 3 1. The next permutation
is the smallest number bigger than it using the same digits.

To make the SMALLEST increase, change digits as far to the RIGHT as possible.
Look at the tail: 7 6 5 3 1 is decreasing, which means it's already the
largest arrangement of those digits. Nothing inside the tail can be bumped up.
So the digit just before the tail (the 4) must increase.

    1 5 8 [4] 7 6 5 3 1
           ^ pivot: first position from the right with nums[i] < nums[i+1]

Bump it up by the SMALLEST possible amount: swap it with the smallest tail
digit that is bigger than 4 (the 5). Then make the tail as small as possible.


WHAT TO THINK ABOUT
--------------------
1. How do you find the pivot in one right-to-left scan?

2. The tail is decreasing. Where is "the smallest element bigger than the
   pivot"? Can you find it scanning from the right?

3. After the swap, is the tail still decreasing? What's the cheapest way to
   turn a decreasing run into an increasing one?

4. What if there's no pivot at all?


PROGRESSIVE HINTS
------------------
Hint 1: i = n - 2; while i >= 0 and nums[i] >= nums[i + 1]: i -= 1.

Hint 2: If i >= 0: j = n - 1; while nums[j] <= nums[i]: j -= 1; swap i, j.

Hint 3: Reverse nums[i + 1:] in place (two pointers). If i == -1 this reverses
        the whole array, which handles the wrap-around.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
"""

from typing import List


class Solution:
    def nextPermutation(self, nums: List[int]) -> None:
        """Do not return anything, modify nums in-place instead."""
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 013_next_permutation_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([1, 2, 3], [1, 3, 2]),
        ([3, 2, 1], [1, 2, 3]),
        ([1, 1, 5], [1, 5, 1]),
        ([1], [1]),
        ([2, 1, 1], [1, 1, 2]),
        ([1, 2, 1], [2, 1, 1]),
        ([1, 5, 8, 4, 7, 6, 5, 3, 1], [1, 5, 8, 5, 1, 3, 4, 6, 7]),
    ]
    all_ok = True
    for nums, want in cases:
        arr = list(nums)
        Solution().nextPermutation(arr)
        ok = arr == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {nums} -> {arr}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
