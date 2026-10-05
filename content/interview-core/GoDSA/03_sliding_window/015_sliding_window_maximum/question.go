package main

/*
================================================================================
LeetCode 239 · Sliding Window Maximum                                     [Hard]
https://leetcode.com/problems/sliding-window-maximum/
Topic: 03 · Sliding Window
================================================================================

PROBLEM
-------
You are given an array of integers `nums` and a sliding window of size k that
moves from the very left of the array to the very right. You can only see the
k numbers in the window. Each time the window moves right by one position.

Return the max of each window.


EXAMPLES
--------
Example 1:
    Input:  nums = [1, 3, -1, -3, 5, 3, 6, 7], k = 3
    Output: [3, 3, 5, 5, 6, 7]

    Window position                Max
    ---------------               -----
    [1  3  -1] -3  5  3  6  7       3
     1 [3  -1  -3] 5  3  6  7       3
     1  3 [-1  -3  5] 3  6  7       5
     1  3  -1 [-3  5  3] 6  7       5
     1  3  -1  -3 [5  3  6] 7       6
     1  3  -1  -3  5 [3  6  7]      7

Example 2:
    Input:  nums = [1], k = 1
    Output: [1]


CONSTRAINTS
-----------
    1 <= nums.length <= 10^5
    -10^4 <= nums[i] <= 10^4
    1 <= k <= nums.length


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A running SUM is easy to slide (add the new, subtract the old). A running MAX
is not: when the current maximum leaves the window, you need to know the
next-largest, and the one after that.

Key observation: if a new element x arrives and some older element y in the
window is <= x, then y can NEVER be the maximum again. x is at least as big
and will stay in the window longer. So y can be thrown away right now.

What survives is a list of candidates that is DECREASING from oldest to
newest. The front is the current maximum.


WHAT TO THINK ABOUT
--------------------
1. Which data structure lets you remove from both ends in O(1)?

2. Store values or indices? How will you know when the front has fallen out
   of the window?

3. Why is the total work O(n) even though there's an inner while loop?


PROGRESSIVE HINTS
------------------
Hint 1: collections.deque of INDICES, values decreasing front to back.

Hint 2: For each i: pop from the back while nums[back] <= nums[i]; append i.
        If the front index is <= i - k, pop it from the front.

Hint 3: Once i >= k - 1, nums[deque[0]] is the answer for the window ending at i.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(k)
================================================================================
*/

// TODO: Implement the stub
