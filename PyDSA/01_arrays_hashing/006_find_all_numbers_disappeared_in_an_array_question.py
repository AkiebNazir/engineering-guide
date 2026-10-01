"""
================================================================================
LeetCode 448 · Find All Numbers Disappeared in an Array                  [Easy]
https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/
Topic: 01 · Arrays & Hashing
================================================================================

PROBLEM
-------
Given an array `nums` of n integers where nums[i] is in the range [1, n],
return an array of all the integers in the range [1, n] that do not appear in
`nums`.


EXAMPLES
--------
Example 1:
    Input:  nums = [4,3,2,7,8,2,3,1]
    Output: [5,6]

Example 2:
    Input:  nums = [1,1]
    Output: [2]


CONSTRAINTS
-----------
    n == nums.length
    1 <= n <= 10^5
    1 <= nums[i] <= n

FOLLOW UP
---------
    Could you do it without extra space and in O(n) runtime? You may assume the
    returned list does not count as extra space.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Read the constraint that makes this problem special:

    1 <= nums[i] <= n        every value is a valid INDEX (after -1 shift)

That is not incidental — it is the entire problem. When your values are exactly
the range of your indices, the array can serve as its own hash table. You do
not need a separate structure to record "have I seen value v"; you can record
it inside the slot that v points to.

    nums = [4, 3, 2, 7, 8, 2, 3, 1]      n = 8, values are all in [1, 8]
            0  1  2  3  4  5  6  7       so value v ↔ index v-1

    Present: 1,2,3,4,7,8      Missing: 5, 6   ->  output [5, 6]

The obvious solution uses a set and is O(n) space. The follow-up removes that,
which is a strong hint that the answer lives inside the input array itself.


WHAT TO THINK ABOUT
-------------------
1. Value v maps to index v-1. What could you write into nums[v-1] to mean
   "value v was seen" — without destroying the value already stored there,
   which you still need to read later?

2. All values are POSITIVE. Does that leave a spare bit of information you can
   use as a flag?

3. If you mark by negating, then later read nums[i] to compute its index, what
   goes wrong? How do you protect against it?

4. Alternative family: instead of flagging, physically SWAP each value into its
   home slot (cyclic sort). Then any index i where nums[i] != i+1 is missing.


PROGRESSIVE HINTS
-----------------
Hint 1: Use the SIGN of nums[v-1] as a one-bit "seen" marker. Values are
        guaranteed positive, so a negative value can only mean "marked".

Hint 2: First pass — for each value v, negate nums[abs(v) - 1]. The abs() is
        mandatory: by the time you reach a slot it may already be negative.

Hint 3: Second pass — any index i still holding a POSITIVE value was never
        marked, so i+1 never appeared. Collect i+1.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(1) extra, excluding the output list
================================================================================
"""

from typing import List


class Solution:
    def findDisappearedNumbers(self, nums: List[int]) -> List[int]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 006_..._question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([4, 3, 2, 7, 8, 2, 3, 1], [5, 6]),
        ([1, 1], [2]),
        ([1], []),
        ([2, 2], [1]),
        ([1, 2, 3, 4], []),
        ([3, 3, 3, 3], [1, 2, 4]),
    ]
    passed = 0
    for nums, expected in cases:
        got = sol.findDisappearedNumbers(list(nums))
        ok = got is not None and sorted(got) == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums} -> {got} (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
