"""
================================================================================
LeetCode 1 · Two Sum                                                     [Easy]
https://leetcode.com/problems/two-sum/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an array of integers `nums` and an integer `target`, return indices of the
two numbers such that they add up to `target`.

You may assume that each input would have exactly one solution, and you may not
use the same element twice.

You can return the answer in any order.


EXAMPLES
--------
Example 1:
    Input:  nums = [2,7,11,15], target = 9
    Output: [0,1]
    Explanation: Because nums[0] + nums[1] == 9, we return [0, 1].

Example 2:
    Input:  nums = [3,2,4], target = 6
    Output: [1,2]

Example 3:
    Input:  nums = [3,3], target = 6
    Output: [0,1]


CONSTRAINTS
-----------
    2 <= nums.length <= 10^4
    -10^9 <= nums[i] <= 10^9
    -10^9 <= target <= 10^9
    Only one valid answer exists.

FOLLOW UP
---------
    Can you come up with an algorithm that is less than O(n^2) time complexity?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is the most-asked interview question in existence, and the reason is that
it is the smallest possible demonstration of one idea:

    Turn "search for the thing I need" into "look up the thing I need."

The brute force asks, for every pair (i, j), "do these sum to target?" That is
n^2 questions. But notice you are not really looking for a PAIR — once you fix
nums[i], the partner you need is completely determined:

    complement = target - nums[i]

So the real question at each index is "have I already seen `complement`?"
That is a membership question, and membership questions belong in a hash map.

    nums = [2, 7, 11, 15], target = 9

    i=0, nums[0]=2  ->  I need 9 - 2 = 7.  Seen 7 before? No.  Remember 2@0.
    i=1, nums[1]=7  ->  I need 9 - 7 = 2.  Seen 2 before? YES, at index 0.
                        return [0, 1]

Note two things that make this work:
  - We store VALUE -> INDEX, because the problem wants indices back.
  - We check BEFORE inserting the current element, which is what stops an
    element from pairing with itself.


WHAT TO THINK ABOUT
-------------------
1. Read the return type carefully: INDICES, not values. That rules out any
   approach that reorders the array unless you track original positions.

2. Sorting + two pointers is O(n log n) and O(1) space. Why is it usually the
   wrong answer here, and when would it be the right one?

3. What breaks if you insert into the map before checking? Test yourself on
   nums = [3, 3], target = 6, and on nums = [3, 2, 4], target = 6.

4. Do you need two passes, or can one pass do it?


PROGRESSIVE HINTS
-----------------
Hint 1: For each element, the number you need is fully determined:
        target - nums[i]. You are not searching for a pair, you are searching
        for one value.

Hint 2: A dict mapping value -> index answers "have I seen this value, and
        where?" in O(1) average.

Hint 3: Walk once. At each i: if (target - nums[i]) is already in the dict,
        you are done. Otherwise record nums[i] -> i and continue.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n)
================================================================================
"""

from typing import List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 004_two_sum_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([2, 7, 11, 15], 9, [0, 1]),
        ([3, 2, 4], 6, [1, 2]),
        ([3, 3], 6, [0, 1]),
        ([-1, -2, -3, -4, -5], -8, [2, 4]),
        ([0, 4, 3, 0], 0, [0, 3]),
    ]
    passed = 0
    for nums, target, expected in cases:
        got = sol.twoSum(list(nums), target)
        # Any order is acceptable; compare as a set of indices.
        ok = got is not None and sorted(got) == sorted(expected)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} target={target} "
              f"-> {got} (want {expected} in any order)")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
