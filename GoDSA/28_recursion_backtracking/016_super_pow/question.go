package main

/*
================================================================================
LeetCode 372 · Super Pow                                                [Medium]
https://leetcode.com/problems/super-pow/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Your task is to calculate `a^b` mod 1337, where `a` is a positive integer
and `b` is an extremely large positive integer given in the form of an
array (`b` may have thousands of digits, far too large to fit in a
normal integer type).

EXAMPLES
--------
Example 1:
    Input:  a = 2, b = [3]
    Output: 8

Example 2:
    Input:  a = 2, b = [1,0]
    Output: 1024

Example 3:
    Input:  a = 1, b = [4,3,3,8,5,2,4,3,7,9,8,2,3,8,9,7,9,2,3,8,4,7,9,2,2,3]
    Output: 1

CONSTRAINTS
-----------
    1 <= a <= 2^31 - 1
    1 <= b.length <= 2000
    0 <= b[i] <= 9
    b does not contain leading zeros.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
`b` is too large to convert into a normal exponent and use fast
exponentiation directly on — but you don't need to. Treat `b` (an array
of digits) as a NUMBER-TO-PROCESS-DIGIT-BY-DIGIT, and use the identity:

    a^(10*x + d) = (a^x)^10 * a^d

So peeling off `b`'s LAST digit `d` and recursing on the REMAINING digits
(everything except the last) reduces the problem to a strictly smaller
one, combining via the "raise the smaller answer to the 10th power, then
multiply by a^d" rule — all done MOD 1337 at every step, since
`(x * y) mod m = ((x mod m) * (y mod m)) mod m`, which keeps every
intermediate number small regardless of how many digits `b` has.

    superPow(a, b):
        if b is empty: return 1                            <- base case: a^0 = 1
        lastDigit = b[-1]
        rest = b[:-1]
        return (pow(superPow(a, rest), 10, 1337) * pow(a, lastDigit, 1337)) % 1337

WHAT TO THINK ABOUT
--------------------
1. Why is it safe (and necessary) to take everything mod 1337 at EVERY
   step, not just at the very end? (Numbers would otherwise grow
   astronomically large — `a` up to 2^31-1 raised to a power with 2000
   digits is a number with millions of digits.)
2. Why does peeling off the LAST digit (not the first) make the
   recursive identity `a^(10x+d) = (a^x)^10 * a^d` come out cleanly?
3. `pow(base, exp, mod)` in Python computes modular exponentiation in
   O(log exp) time — since `exp` here is always either 10 or a single
   digit (0-9), each individual `pow()` call inside the recursion is
   essentially O(1) work; where does the REAL cost of this algorithm
   come from, then? (The number of RECURSIVE calls — one per digit of
   `b` — not the cost of any single `pow()` call.)
4. Why would using `**` (plain Python exponentiation, no modulus)
   anywhere in this recursion, even just for `a**lastDigit`, be a
   correctness/performance trap given `a` can be up to 2^31-1?

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `b` empty (no digits left) means the exponent
        contributed so far is 0 -> return 1.
Hint 2: Peel off the LAST digit of `b`: `lastDigit = b[-1]`, and recurse
        on `b[:-1]` (everything except the last digit).
Hint 3: Combine: `(superPow(a, b[:-1]) ** 10) * (a ** lastDigit)`... but
        apply `% 1337` at EVERY multiplication/exponentiation step, not
        just at the end, using Python's 3-argument `pow(base, exp, mod)`.
Hint 4: `pow(a, lastDigit, 1337)` handles `a^lastDigit mod 1337`
        directly; `pow(recursiveResult, 10, 1337)` handles raising the
        smaller answer to the 10th power, both mod 1337, in one call
        each.

COMPLEXITY TARGET
------------------
    Recursive: O(len(b)) recursive calls, each doing O(1) work via
               Python's built-in modular `pow()` — O(len(b)) total time,
               O(len(b)) space (call stack, one frame per digit)
================================================================================
*/

// TODO: Implement the stub
