package main

/*
================================================================================
LeetCode 16 · 3Sum Closest                                              [Medium]
https://leetcode.com/problems/3sum-closest/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given an integer array `nums` of length n and an integer `target`, find three
integers in `nums` at DIFFERENT indices such that their sum is closest to
`target`. Return that sum.

You may assume each input has exactly one closest answer.


EXAMPLES
--------
Example 1:
    Input:  nums = [-1, 2, 1, -4], target = 1
    Output: 2
    Explanation: -1 + 2 + 1 = 2 is the closest sum to 1 (distance 1).

Example 2:
    Input:  nums = [0, 0, 0], target = 1
    Output: 0


CONSTRAINTS
-----------
    3 <= nums.length <= 500
    -1000 <= nums[i] <= 1000
    -10^4 <= target <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is 3Sum (007) with the equality test replaced by a DISTANCE test. In
3Sum you were hunting for sum == 0 and could throw away every other sum. Here
every sum you look at is a candidate, and you keep the one with the smallest
`abs(sum - target)`.

The two-pointer mechanics are identical: sort, fix the first element, and
walk two pointers inward over the rest. What changes is what you do at each
step — you RECORD the sum, then move the pointer that pushes the sum TOWARD
the target.


WHAT TO THINK ABOUT
--------------------
1. Why does sorting make the inner search O(n)? If `sum < target`, moving
   the LEFT pointer right is the only move that can increase the sum.

2. What should `closest` start as? It must be a real sum of three elements,
   or a sentinel you're careful never to return.

3. Compare DISTANCES to the target, not the sums themselves.

4. If you ever hit `sum == target`, can you stop immediately?


PROGRESSIVE HINTS
------------------
Hint 1: Sort. For each index i, run two pointers lo = i + 1, hi = n - 1.

Hint 2: At each step compute s = nums[i] + nums[lo] + nums[hi]. If
        abs(s - target) < abs(closest - target), record s.

Hint 3: If s < target, lo += 1. If s > target, hi -= 1. If s == target,
        return s — nothing can be closer than distance 0.


COMPLEXITY TARGET
------------------
    Time:  O(n^2)
    Space: O(1) extra beyond the sort (O(n) for Python's Timsort)
================================================================================
*/

// TODO: Implement the stub
