"""
================================================================================
LeetCode 287 · Find the Duplicate Number                               [Medium]
https://leetcode.com/problems/find-the-duplicate-number/
Topic: 08 · Linked List
================================================================================

PROBLEM
-------
Given an array `nums` of length n+1 where every integer is in the range
[1, n] inclusive, there is exactly ONE repeated number (it may repeat more
than twice). Find that number.

You must solve it WITHOUT modifying the array `nums` and using only O(1)
extra space.


EXAMPLES
--------
Example 1:
    Input:  nums = [1,3,4,2,2]
    Output: 2

Example 2:
    Input:  nums = [3,1,3,4,2]
    Output: 3

Example 3:
    Input:  nums = [3,3,3,3,3]
    Output: 3


CONSTRAINTS
-----------
    1 <= n <= 10^5
    nums.length == n + 1
    1 <= nums[i] <= n
    All the integers in nums appear only once except for precisely one
    integer which appears two or more times.

FOLLOW UP
---------
    How can you prove that at least one duplicate must exist?
    Can you solve it in linear runtime complexity, without modifying the
    array, and using only O(1) extra space?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This LOOKS like a pure array problem. It is secretly a linked-list problem in
disguise — see this topic's guide, "012 is the surprise of the folder."

Every value nums[i] is itself a valid INDEX into nums (because values are in
[1, n] and the array has n+1 slots, indices 0..n). So you can treat the array
as defining a function:

    next(i) = nums[i]

Starting from index 0 and repeatedly applying `next` is EXACTLY like walking
a linked list where node i's ".next" pointer is nums[i]. Because two different
indices can point at the SAME value (the duplicate), this "list" must contain
a cycle — and finding the duplicate is the same problem as finding where a
cycle STARTS, which is Floyd's cycle detection (topic 08 problem 003), reused
verbatim.


WHAT TO THINK ABOUT
--------------------
1. Why must a cycle exist? Pigeonhole: n+1 values are drawn from range
   [1, n], so by pigeonhole at least one value repeats. Under the "value is
   next pointer" reinterpretation, the repeated value means two different
   array slots point at the same next node — a merge point, which forces a
   cycle in the functional graph.

2. The "obvious" solutions (sort, or a seen-set) are O(n log n) or O(n)
   space respectively. Both are disallowed by the O(1)-space constraint but
   worth naming as the baseline.

3. Once you see it as Floyd's, the two phases are identical to cycle
   detection: phase 1 finds a meeting point inside the cycle, phase 2 finds
   the cycle's ENTRANCE — which is provably the duplicate value.


PROGRESSIVE HINTS
------------------
Hint 1: Treat nums[i] as a pointer: i -> nums[i]. This defines a "linked
        list" over indices 0..n, and it MUST contain a cycle (pigeonhole).

Hint 2: The duplicate value is exactly the entry point of that cycle — every
        index that maps to the duplicate value is like a node pointing INTO
        the cycle from outside, or the cycle itself.

Hint 3: Run Floyd's tortoise-and-hare (topic 08 problem 003) starting from
        index 0, using nums[i] as ".next". Phase 1 finds a meeting point;
        phase 2 (reset one pointer to the start, advance both by one step
        at a time) finds the cycle entrance.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1), array not modified
================================================================================
"""

from typing import List


class Solution:
    def findDuplicate(self, nums: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 012_find_the_duplicate_number_question.py
# ==============================================================================
CASES = [
    ([1, 3, 4, 2, 2], 2),
    ([3, 1, 3, 4, 2], 3),
    ([3, 3, 3, 3, 3], 3),
    ([1, 1], 1),
    ([2, 2, 2, 2, 2], 2),
    ([1, 2, 3, 4, 4], 4),
    ([2, 1, 3, 4, 5, 6, 7, 8, 9, 10, 5], 5),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    for nums, want in CASES:
        got = sol.findDuplicate(list(nums))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<40} -> {got}  (want {want})")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
