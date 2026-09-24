"""
================================================================================
LeetCode 169 · Majority Element                                          [Easy]
https://leetcode.com/problems/majority-element/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an array `nums` of size n, return the majority element.

The majority element is the element that appears more than ⌊n / 2⌋ times. You
may assume that the majority element always exists in the array.


EXAMPLES
--------
Example 1:
    Input:  nums = [3,2,3]
    Output: 3

Example 2:
    Input:  nums = [2,2,1,1,1,2,2]
    Output: 2


CONSTRAINTS
-----------
    n == nums.length
    1 <= n <= 5 * 10^4
    -10^9 <= nums[i] <= 10^9

FOLLOW UP
---------
    Could you solve the problem in linear time and in O(1) space?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Read "more than ⌊n/2⌋ times" precisely — this is a STRICT majority, not merely
the most common element. That is a much stronger guarantee than it looks, and
the whole trick depends on it:

    n = 7  ->  majority appears at least 4 times
               all other elements COMBINED appear at most 3 times

So the majority element outnumbers everything else put together. That single
fact is what makes the O(1)-space algorithm possible.

    [2, 2, 1, 1, 1, 2, 2]     n=7, need > 3 occurrences
     2 appears 4 times  -> majority ✓
     1 appears 3 times  -> not a majority


WHAT TO THINK ABOUT
-------------------
1. The easy answers first: count with a hash map (O(n) time, O(n) space), or
   sort and take the middle (O(n log n) time, O(1) space). Why does sorting
   and taking nums[n//2] work at all? Convince yourself.

2. The follow-up asks for O(n) time AND O(1) space, which rules out both.
   That combination should make you suspect a counting/cancellation trick
   rather than a data structure.

3. Think of it as a fight. Every time two DIFFERENT elements meet, they cancel
   each other out. If one element has more than half the population, can it
   ever be fully cancelled?


PROGRESSIVE HINTS
-----------------
Hint 1: Sorting works because an element occupying more than half the array
        must cover the middle index, whatever the arrangement.

Hint 2: For O(1) space: keep ONE candidate and ONE counter. When the counter
        hits zero, adopt the current element as the new candidate.

Hint 3: Increment when the current element equals the candidate, decrement
        when it differs. Because the majority outnumbers all others combined,
        it cannot be reduced to zero overall — it is the last one standing.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1)
================================================================================
"""

from typing import List


class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 005_majority_element_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([3, 2, 3], 3),
        ([2, 2, 1, 1, 1, 2, 2], 2),
        ([1], 1),
        ([1, 2, 1], 1),
        ([6, 5, 5], 5),
        ([-1, -1, -1, 2, 3], -1),
    ]
    passed = 0
    for nums, expected in cases:
        got = sol.majorityElement(list(nums))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} -> {got} (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
