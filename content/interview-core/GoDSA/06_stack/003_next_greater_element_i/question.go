package main

/*
================================================================================
LeetCode 496 · Next Greater Element I                                    [Easy]
https://leetcode.com/problems/next-greater-element-i/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
The next greater element of some element `x` in an array is the first
greater element that is to the RIGHT of `x` in the same array.

You are given two DISTINCT 0-indexed integer arrays `nums1` and `nums2`,
where `nums1` is a subset of `nums2`.

For each `0 <= i < nums1.length`, find the index `j` such that
`nums1[i] == nums2[j]` and determine the next greater element of `nums2[j]`
in `nums2`. If there is no next greater element, that answer is -1.

Return an array `ans` of length `nums1.length` such that `ans[i]` is the
next greater element as described above.


EXAMPLES
--------
Example 1:
    Input:  nums1 = [4,1,2], nums2 = [1,3,4,2]
    Output: [-1,3,-1]
    Explanation:
        For 4 in nums2: no element to its right is greater -> -1.
        For 1 in nums2: the next greater to its right is 3.
        For 2 in nums2: no element to its right is greater -> -1.

Example 2:
    Input:  nums1 = [2,4], nums2 = [1,2,3,4]
    Output: [3,-1]


CONSTRAINTS
-----------
    1 <= nums1.length <= nums2.length <= 1000
    0 <= nums1[i], nums2[i] <= 10^4
    All integers in nums1 and nums2 are unique.
    All the integers of nums1 also appear in nums2.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Strip away the nums1/nums2 indirection first: the real task is "for every
element of nums2, find its next greater element to the right" — a single,
self-contained computation over nums2 alone. nums1 is just asking about a
subset of the answers afterward (a dict lookup once you have them all).

The naive way to answer "next greater to the right" for one index is a
forward scan — O(n) per index, O(n^2) for the whole array. This is the
CANONICAL problem for the monotonic stack (topic guide Part 2): process
nums2 left to right, keeping a stack of "elements still waiting for their
answer," and resolve several of them at once whenever a big enough new
value arrives.


WHAT TO THINK ABOUT
--------------------
1. If you scan nums2 left to right, and the current stack holds values in
   DECREASING order (top = smallest), what should happen when the new
   value is bigger than the top?
2. Can ONE new value resolve MORE than one waiting element? Try
   nums2 = [5, 4, 3, 10] by hand.
3. What happens to elements that are NEVER resolved by the time you reach
   the end of nums2?
4. Once you have "next greater for every value in nums2," how do you answer
   nums1's query in O(1) per element rather than re-scanning?


PROGRESSIVE HINTS
------------------
Hint 1: Use a dict `next_greater = {}` to map value -> its answer, plus a
        stack of VALUES (all values are guaranteed unique, so you can push
        raw values instead of indices here).

Hint 2: For each x in nums2: while stack and stack[-1] < x: pop it, and
        record next_greater[popped] = x. Then push x.

Hint 3: Anything still on the stack after the loop never found a next
        greater element — its answer is -1. You can prefill the dict with
        -1 for every value, or check `.get(x, -1)` at query time.

Hint 4: Final answer: `[next_greater.get(x, -1) for x in nums1]`.


COMPLEXITY TARGET
------------------
    Time:  O(n + m) where n = len(nums2), m = len(nums1) — the monotonic
           stack pass over nums2 is O(n) total (topic guide §2.1), plus an
           O(1) dict lookup per nums1 query.
    Space: O(n) for the stack and the answer map.
================================================================================
*/

// TODO: Implement the stub
