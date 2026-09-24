package main

/*
================================================================================
LeetCode 42 · Trapping Rain Water                                         [Hard]
https://leetcode.com/problems/trapping-rain-water/
Topic: 02 · Two Pointers
================================================================================

PROBLEM
-------
Given n non-negative integers representing an elevation map where the width
of each bar is 1, compute how much water it can trap after raining.


EXAMPLES
--------
Example 1:
    Input:  height = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
    Output: 6

        3 |                       █
        2 |           █ ~  ~  ~  █  █  ~  █
        1 |     █  ~  █  █  ~  █  █  █  █  █  █
          +------------------------------------
            0  1  2  3  4  5  6  7  8  9 10 11

    Water (~) sits at index 2 (1), 4 (1), 5 (2), 6 (1), 9 (1) = 6 units.

Example 2:
    Input:  height = [4, 2, 0, 3, 2, 5]
    Output: 9


CONSTRAINTS
-----------
    n == height.length
    1 <= n <= 2 * 10^4
    0 <= height[i] <= 10^5


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Think about ONE column at a time. The water above column i rises to the
lower of two walls: the tallest bar anywhere to its left and the tallest bar
anywhere to its right. So:

    water[i] = min(max_left[i], max_right[i]) - height[i]

(where max_left and max_right include height[i] itself, so the result is
never negative).

The whole problem is computing those two maxima efficiently. The brute force
rescans left and right for every column: O(n^2). The rest of the approaches
are ways to avoid that rescan.


WHAT TO THINK ABOUT
--------------------
1. Can you precompute max_left for every index in one pass? max_right?

2. With two pointers from both ends: if left_max < right_max, do you actually
   need to know the EXACT max on the right to fill the left column?

3. A monotonic stack can also solve it, filling water in horizontal layers
   instead of vertical columns. How would that work?


PROGRESSIVE HINTS
------------------
Hint 1: Prefix max array from the left, suffix max array from the right,
        then sum min(...) - height. O(n) time, O(n) space.

Hint 2: Two pointers lo, hi and running left_max, right_max. Whichever side
        has the SMALLER max is the bottleneck for its column — the other side
        is guaranteed to have a wall at least that tall.

Hint 3: If left_max <= right_max: water at lo is left_max - height[lo]; move
        lo right. Otherwise do the same on the right side.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(1)
================================================================================
*/

// TODO: Implement the stub
