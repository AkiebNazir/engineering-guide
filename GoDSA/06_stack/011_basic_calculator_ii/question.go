package main

/*
================================================================================
LeetCode 227 · Basic Calculator II                                      [Medium]
https://leetcode.com/problems/basic-calculator-ii/
Topic: 06 · Stack & Monotonic Stack
================================================================================

PROBLEM
-------
Given a string `s` which represents an expression, evaluate this expression
and return its value.

The integer division should TRUNCATE TOWARD ZERO.

You may assume the given expression is always valid. All intermediate results
will be in the range [-2^31, 2^31 - 1].

You are NOT allowed to use any built-in function which evaluates strings as
mathematical expressions, such as eval().


EXAMPLES
--------
Example 1:   s = "3+2*2"       ->  7
Example 2:   s = " 3/2 "       ->  1
Example 3:   s = " 3+5 / 2 "   ->  5


CONSTRAINTS
-----------
    1 <= s.length <= 3 * 10^5
    s consists of integers and operators ('+', '-', '*', '/') separated by
      some number of spaces.
    s represents a valid expression.
    All the integers in the expression are non-negative in [0, 2^31 - 1].
    The answer is guaranteed to fit in a 32-bit integer.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
No parentheses, just precedence: * and / bind tighter than + and -.

Rewrite the expression as a SUM OF TERMS, where each term is a run of
numbers joined by * and /:

    3 + 5 / 2 - 4 * 2 * 3
    = (+3) + (+5 / 2) + (-4 * 2 * 3)

A stack holds finished-or-growing terms. + and - start a NEW term (push the
number with its sign). * and / modify the MOST RECENT term (pop, combine,
push). At the end, sum the stack.


WHAT TO THINK ABOUT
--------------------
1. Numbers can have many digits. How do you parse them as you scan?

2. When you finish reading a number, which operator decides what to do with
   it — the one before it or the one after it?

3. Python's `//` rounds toward negative infinity. -3 // 2 == -2, but
   truncation toward zero gives -1. When can a negative number be divided?

4. Do you need the whole stack, or just the last term?


PROGRESSIVE HINTS
------------------
Hint 1: Keep `num` (digits read so far) and `op` (the operator seen BEFORE
        num, initially '+').

Hint 2: When you hit an operator or the end of the string, apply `op` to num:
        '+' push num, '-' push -num, '*' push pop()*num, '/' push
        truncate(pop(), num). Then set op to the new operator, num = 0.

Hint 3: Truncating division: int(a / b) works here (values fit in 53 bits),
        or use sign-aware integer division.


COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(n) stack, or O(1) keeping only the running total and last term
================================================================================
*/

// TODO: Implement the stub
