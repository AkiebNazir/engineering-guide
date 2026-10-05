package main

/*
================================================================================
LeetCode 739 · Daily Temperatures                                      [Medium]
https://leetcode.com/problems/daily-temperatures/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
Given an array of integers `temperatures` representing the daily
temperatures, return an array `answer` such that `answer[i]` is the number
of days you have to wait after the i-th day to get a WARMER temperature.
If there is no future day for which this is possible, keep `answer[i] == 0`
instead.


EXAMPLES
--------
Example 1:
    Input:  temperatures = [73,74,75,71,69,72,76,73]
    Output: [1,1,4,2,1,1,0,0]

Example 2:
    Input:  temperatures = [30,40,50,60]
    Output: [1,1,1,0]

Example 3:
    Input:  temperatures = [30,60,90]
    Output: [1,1,0]


CONSTRAINTS
-----------
    1 <= temperatures.length <= 10^5
    30 <= temperatures[i] <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is problem 003 (Next Greater Element) wearing a different payload:
instead of returning the VALUE of the next greater element, return the
DISTANCE (number of days) to it. Same monotonic-stack template, same
push/pop/resolve skeleton (topic guide §2.3) — only what gets recorded on
a resolve changes.

    stack holds INDICES of days still waiting for a warmer day, in
    decreasing temperature order top-to-bottom... i.e. the stack's
    temperatures DECREASE as you go from bottom to top, same invariant as
    problem 003.

    when today's temperature beats the day on top of the stack:
        pop that day's index j
        answer[j] = i - j        <- the DISTANCE, not temperatures[i]


WHAT TO THINK ABOUT
--------------------
1. What do you push onto the stack — the temperature, or the index? Why
   does this problem specifically need the index (hint: what do you need
   to compute a distance)?
2. Days that are NEVER resolved by the end keep `answer[i] == 0` — how
   does that follow naturally from how `answer` is initialized, without
   any extra code at the end?
3. Walk `[73, 74, 75, 71, 69, 72, 76, 73]` by hand and check day 2
   (temperature 75, 0-indexed) — how many days does IT wait, and why does
   it NOT resolve against day 5's 72?


PROGRESSIVE HINTS
------------------
Hint 1: `answer = [0] * n` (this pre-fills the "never resolved" case).
        `stack = []` holding INDICES.

Hint 2: For each day i with temperature t: while stack and
        temperatures[stack[-1]] < t: pop j, set answer[j] = i - j. Then
        push i.

Hint 3: This is EXACTLY problem 003's template with two substitutions:
        `nums2` becomes `temperatures`, and the resolve step records
        `i - j` (a distance) instead of `x` (a value).


COMPLEXITY TARGET
------------------
    Time:  O(n) — the monotonic stack argument from the topic guide §2.1:
           each index is pushed once and popped at most once.
    Space: O(n) for the stack (worst case: strictly decreasing
           temperatures, nothing ever resolves until the very last day, if
           at all) plus O(n) for the answer array.
================================================================================
*/

// TODO: Implement the stub
