package main

/*
================================================================================
QUESTION · LeetCode 338 · Counting Bits                              [Easy]
https://leetcode.com/problems/counting-bits/
================================================================================

PROBLEM
-------
Given an integer n, return an array `ans` of length n + 1 such that for
each i (0 <= i <= n), ans[i] is the number of 1's in the binary
representation of i.


EXAMPLES
--------
Example 1:
    Input:  n = 2
    Output: [0,1,1]
    (0 -> 0b0 -> 0 bits, 1 -> 0b1 -> 1 bit, 2 -> 0b10 -> 1 bit)

Example 2:
    Input:  n = 5
    Output: [0,1,1,2,1,2]
    (0,1,2,3,4,5 -> 0b0,0b1,0b10,0b11,0b100,0b101)


CONSTRAINTS
-----------
    0 <= n <= 10^5

Follow up:
    - It is very easy to come up with a solution with a runtime of
      O(n log n). Can you do it in linear time O(n) and possibly in a
      single pass?
    - Can you do it without using any built-in function (i.e., like
      `__builtin_popcount` in C++)?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Calling 002's popcount on every i from 0 to n is O(n) calls * O(popcount)
each = O(n log n) worst case. The follow-up wants O(n) total by REUSING
already-computed answers: popcount(i) relates to popcount of a SMALLER,
already-known index via one bit operation.

Two equivalent O(n) DP recurrences (both single-pass, both O(1) work per
index):
    ans[i] = ans[i >> 1] + (i & 1)        # drop the lowest bit by shifting
    ans[i] = ans[i & (i - 1)] + 1         # drop the lowest SET bit directly

PROGRESSIVE HINTS
------------------
Hint 1: popcount(i) and popcount(i // 2) differ by exactly whether i's
        lowest bit is 1 or 0.
Hint 2: `i >> 1` is `i // 2` with the lowest bit dropped; `i & 1` recovers
        that dropped bit.
Hint 3: `ans[i] = ans[i >> 1] + (i & 1)` -- build the array left to right,
        each entry uses an index strictly smaller than i, already computed.

COMPLEXITY TARGET
------------------
    Time:  O(n), single pass
    Space: O(n) for the output (required), O(1) auxiliary
================================================================================
*/

// TODO: Implement the stub
