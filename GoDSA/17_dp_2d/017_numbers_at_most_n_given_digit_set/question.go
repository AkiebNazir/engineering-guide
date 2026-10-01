package main

/*
================================================================================
LeetCode 902 · Numbers At Most N Given Digit Set                          [Hard]
https://leetcode.com/problems/numbers-at-most-n-given-digit-set/
Topic: 17 · Dynamic Programming (2D) — DIGIT DP
================================================================================

PROBLEM
-------
Given an array of `digits` sorted in non-decreasing order, you can write
numbers using each digits[i] as many times as you want. For example, if
digits = ['1','3','5'], you may write numbers such as '13', '551', and
'1351315'.

Return the number of positive integers that can be generated that are less
than or equal to a given integer n.


EXAMPLES
--------
Example 1:
    Input:  digits = ["1","3","5","7"], n = 100
    Output: 20
    Explanation: 1, 3, 5, 7, 11, 13, 15, 17, 31, ..., 75, 77 (4 + 16 = 20)

Example 2:
    Input:  digits = ["1","4","9"], n = 1000000000
    Output: 29523
    Explanation: 3 one-digit + 9 two-digit + 27 three-digit + ... + 3^9
                 nine-digit numbers = 29523.

Example 3:
    Input:  digits = ["7"], n = 8
    Output: 1


CONSTRAINTS
-----------
    1 <= digits.length <= 9
    digits[i].length == 1
    digits[i] is a digit from '1' to '9'.
    All the values in digits are unique.
    digits is sorted in non-decreasing order.
    1 <= n <= 10^9


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the gentlest DIGIT DP problem: count numbers <= n whose digits satisfy
a rule. You can't enumerate up to 10^9. Instead, build the number one digit at
a time from the MOST significant position, tracking one bit of state:

    TIGHT: is the prefix so far exactly equal to n's prefix?
      - If tight, the next digit may be at most n's digit at this position.
      - If not tight (already smaller), every later digit is free.

Split the count into two parts:

    1. Numbers with FEWER digits than n: all of them are < n.
       With D allowed digits and length L: D^L numbers.  Sum over L < len(n).

    2. Numbers with the SAME number of digits: walk n's digits left to right.
       At position i, every allowed digit SMALLER than n[i] makes the number
       free from there on: that's (count of smaller digits) * D^(remaining).
       If n[i] itself is allowed, stay tight and continue. If not, stop.
       If you stayed tight through every position, n itself counts: +1.


WHAT TO THINK ABOUT
--------------------
1. Why can't the answer include numbers with leading zeros here? (No '0' in
   digits.)

2. When n[i] is not in the digit set, why does the walk stop?

3. Write it as a memoized recursion f(pos, tight) too. That template solves
   every digit DP problem.


PROGRESSIVE HINTS
------------------
Hint 1: s = str(n), L = len(s), D = len(digits).
        total = sum(D ** k for k in range(1, L)).

Hint 2: For i, c in enumerate(s):
            smaller = number of digits < c
            total += smaller * D ** (L - i - 1)
            if c not in digits: return total

Hint 3: After the loop (every digit of n was allowed): return total + 1.


COMPLEXITY TARGET
------------------
    Time:  O(log10(n) * |digits|)
    Space: O(1)
================================================================================
*/

// TODO: Implement the stub
