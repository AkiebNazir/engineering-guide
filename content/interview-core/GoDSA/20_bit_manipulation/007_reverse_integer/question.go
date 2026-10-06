package main

/*
================================================================================
QUESTION · LeetCode 7 · Reverse Integer                              [Medium]
https://leetcode.com/problems/reverse-integer/
================================================================================

PROBLEM
-------
Given a signed 32-bit integer x, return x with its digits reversed. If
reversing x causes the value to go outside the signed 32-bit integer
range [-2^31, 2^31 - 1], then return 0.

Assume the environment does not allow you to store 64-bit integers
(signed or unsigned).


EXAMPLES
--------
Example 1:
    Input:  x = 123
    Output: 321

Example 2:
    Input:  x = -123
    Output: -321

Example 3:
    Input:  x = 120
    Output: 21

Example 4:
    Input:  x = 0
    Output: 0


CONSTRAINTS
-----------
    -2^31 <= x <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a DECIMAL-digit reversal (not a bit reversal -- contrast with
004), but it belongs in this topic because the overflow-detection
discipline is identical: the input and output both live in the signed
32-bit range [-2147483648, 2147483647], and Python's ints don't know
that range exists. Building the reversed number digit by digit
(`rev = rev * 10 + digit`) can silently produce a value LARGER than
2^31 - 1 or smaller than -2^31 in Python, where it just keeps existing
as a bigger int with no error -- the problem demands you detect that and
return 0 instead. There is no wraparound to lean on (unlike some
languages where int32 overflow wraps); you must CHECK the bound
explicitly after building the value (or, more robustly, before each
multiply-and-add step, to avoid ever holding a value that momentarily
exceeds even Python's own comfort in a hypothetical fixed-width port).

PROGRESSIVE HINTS
------------------
Hint 1: Work with abs(x), strip and reverse decimal digits one at a time
        with `% 10` and `// 10`, then restore the sign at the end.
Hint 2: Do the overflow check using the actual INT32_MIN/INT32_MAX
        constants, not by mimicking C's silent-wrap behavior -- Python
        never wraps, so you must compare explicitly.
Hint 3: `if rev > 2**31 - 1 or rev < -2**31: return 0`.

COMPLEXITY TARGET
------------------
    Time:  O(log x) -- one iteration per decimal digit
    Space: O(1)
================================================================================
*/

// TODO: Implement the stub
