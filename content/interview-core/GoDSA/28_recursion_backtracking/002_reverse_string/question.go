package main

/*
================================================================================
LeetCode 344 · Reverse String                                             [Easy]
https://leetcode.com/problems/reverse-string/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Write a function that reverses a string. The input string is given as an
array of characters `s`, and you must do it **in place** with O(1) extra
space (not counting the recursion's own call stack).

EXAMPLES
--------
Example 1:
    Input:  s = ["h","e","l","l","o"]
    Output: ["o","l","l","e","h"]

Example 2:
    Input:  s = ["H","a","n","n","a","h"]
    Output: ["h","a","n","n","a","H"]

CONSTRAINTS
-----------
    1 <= s.length <= 10^5
    s[i] is a printable ASCII character.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Problem 001 recursed on a shrinking NUMBER. This is the first problem in the
folder that recurses on a shrinking INDEX RANGE into a fixed-size structure —
a slightly different (and very common) way to make progress toward a base
case: instead of transforming the value itself, two pointers `lo` and `hi`
close in on each other from opposite ends of a fixed array.

    reverse(s, lo, hi):
        if lo >= hi: return                       <- base case: pointers met/crossed
        swap s[lo], s[hi]
        reverse(s, lo + 1, hi - 1)                 <- both ends move inward

Each call does ONE swap, then recurses on a range that is strictly smaller
by 2 (one from each end). The base case is "no range left to swap" — either
the pointers meet (odd length) or cross (even length).

WHAT TO THINK ABOUT
--------------------
1. What are the two things that need to shrink here, and what's the exact
   condition under which there's nothing left to do?
2. Since this must be in place, what does the recursive call return, if
   anything? (Compare to 001, where every call returned a step count.)
3. Recursion depth here is `len(s) // 2` — for `len(s)` up to 10^5, does that
   fit inside Python's default recursion limit? What would you have to do
   about it if it didn't?
4. This is a textbook case where the iterative twin is strictly better in
   Python (no call-stack risk, same time complexity) — why teach the
   recursive version at all? (Because the two-pointer index-range pattern
   recurs constantly in later problems — 008, 023 — even when the ultimate
   answer is iterative.)

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `lo >= hi` (pointers met or crossed) — nothing to swap.
Hint 2: Swap `s[lo]` and `s[hi]`, then recurse with `lo + 1, hi - 1`.
Hint 3: The top-level call is `reverse(s, 0, len(s) - 1)`; the function
        mutates `s` in place and returns `None`.
Hint 4: For `len(s) = 10^5`, recursion depth is `5 * 10^4` — this WILL hit
        Python's default recursion limit (~1000) and raise `RecursionError`.
        The iterative twin has no such limit; this is demonstrated live in
        the tests.

COMPLEXITY TARGET
------------------
    Recursive (two-pointer index range): O(n) time, O(n) space (call stack) —
                                          and will overflow for large n
    Iterative twin:                      O(n) time, O(1) space
================================================================================
*/

// TODO: Implement the stub
