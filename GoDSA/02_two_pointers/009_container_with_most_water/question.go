package main

/*
================================================================================
LeetCode 11 · Container With Most Water                                 [Medium]
https://leetcode.com/problems/container-with-most-water/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
You are given an integer array `height` of length n. There are n vertical
lines drawn such that the two endpoints of the i-th line are (i, 0) and
(i, height[i]).

Find two lines that, together with the x-axis, form a container that holds
the most water. Return the maximum amount of water the container can store.

You may not slant the container.


EXAMPLES
--------
Example 1:
    Input:  height = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    Output: 49
    Explanation: lines at index 1 (height 8) and index 8 (height 7).
                 width = 8 - 1 = 7, water level = min(8, 7) = 7, area = 49.

         8 |    █                   █
         7 |    █ ~  ~  ~  ~  ~  ~  █  ~  █
         6 |    █  █                █     █
         5 |    █  █     █          █     █
         4 |    █  █     █  █       █     █
         3 |    █  █     █  █       █  █  █
         2 |    █  █  █  █  █       █  █  █
         1 | █  █  █  █  █  █       █  █  █
           +---------------------------------
             0  1  2  3  4  5       6  7  8

Example 2:
    Input:  height = [1, 1]
    Output: 1


CONSTRAINTS
-----------
    n == height.length
    2 <= n <= 10^5
    0 <= height[i] <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Area between lines i < j is  (j - i) * min(height[i], height[j]).

The lines BETWEEN i and j don't matter — they don't block water in this
problem (that's Trapping Rain Water, 010, which is a different problem that
people often confuse with this one).

Checking every pair is O(n^2) = 5 * 10^9 at n = 10^5. You need to rule out
most pairs without ever looking at them.


WHAT TO THINK ABOUT
--------------------
1. Start with the WIDEST container: i = 0, j = n - 1. Any other container is
   narrower. What must be true for a narrower one to hold more?

2. The water level is capped by the SHORTER line. If you keep the shorter
   line and move the taller one inward, can the area ever increase?

3. So which pointer should move?


PROGRESSIVE HINTS
------------------
Hint 1: Two pointers at both ends. Record the area.

Hint 2: Move the pointer at the SHORTER line inward. Moving the taller one
        makes the width smaller while the level stays capped by the same
        short line — the area can only go down.

Hint 3: If both heights are equal, moving either one is safe.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

// TODO: Implement the stub
