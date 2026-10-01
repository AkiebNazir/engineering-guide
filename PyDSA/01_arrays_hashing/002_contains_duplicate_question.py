"""
================================================================================
LeetCode 217 · Contains Duplicate                                        [Easy]
https://leetcode.com/problems/contains-duplicate/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an integer array `nums`, return true if any value appears at least twice
in the array, and return false if every element is distinct.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,3,1]
    Output: true
    Explanation: The element 1 occurs at indices 0 and 3.

Example 2:
    Input:  nums = [1,2,3,4]
    Output: false
    Explanation: All elements are distinct.

Example 3:
    Input:  nums = [1,1,1,3,3,4,3,2,4,2]
    Output: true


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    -10^9 <= nums[i] <= 10^9


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is THE canonical "reach for a hash set" problem, and the first place the
array-vs-set complexity difference actually decides whether you pass.

Note the constraint: n up to 10^5. Look that up in the constraints table in
_TOPIC_GUIDE.md — 10^5 means O(n log n) is comfortable and O(n) is ideal, but
O(n^2) (10^10 operations) will time out. That single line rules out the
brute-force double loop before you write anything.


WHAT TO THINK ABOUT
-------------------
1. The brute force is "compare every pair." What is its complexity? Why does
   the constraint rule it out?

2. What single question are you asking, over and over? It is "have I seen this
   value before?" Which data structure answers that in O(1)?

3. There is also a sorting-based answer. What does it cost, and what does it
   buy you? (Hint: think about SPACE, and about whether you may modify input.)

4. Can you return early? You do not need to finish scanning once you have found
   one duplicate.


PROGRESSIVE HINTS
-----------------
Hint 1: `x in some_list` is O(n). `x in some_set` is O(1) average. Putting the
        first inside a loop is how you accidentally write O(n^2).

Hint 2: Walk the array once. Keep a set of everything seen so far. If the
        current value is already in the set, you are done — return True.

Hint 3: There is a one-liner using len() and set(). Know it, but be ready to
        write the explicit loop, because the explicit loop returns EARLY and
        the one-liner does not.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n)
    (Ask the interviewer whether O(1) space is required — if so, sorting is the
     answer, at O(n log n) time, and it modifies the input.)
================================================================================
"""

from typing import List


class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        seen = set()
        for num in nums:
            if num in seen:
                return True
            seen.add(num)
        return False
        # YOUR CODE HERE
        # pass


# ==============================================================================
# TESTS — run:  python 002_contains_duplicate_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 3, 1], True),
        ([1, 2, 3, 4], False),
        ([1, 1, 1, 3, 3, 4, 3, 2, 4, 2], True),
        ([1], False),
        ([-1, -1], True),
        ([0, 1, -1, 2, -2], False),
    ]
    passed = 0
    for nums, expected in cases:
        got = sol.containsDuplicate(list(nums))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} -> {got} (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
