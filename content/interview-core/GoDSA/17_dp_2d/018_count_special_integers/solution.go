package main

import "fmt"

/*
================================================================================
LeetCode 2376 · Count Special Integers                                    [Hard]
https://leetcode.com/problems/count-special-integers/
Topic: 17 · Dynamic Programming (2D) — DIGIT DP
================================================================================

PROBLEM
-------
We call a positive integer SPECIAL if all of its digits are distinct.

Given a positive integer n, return the number of special integers that belong
to the interval [1, n].


EXAMPLES
--------
Example 1:   n = 20     ->  19    (every number 1..20 except 11)
Example 2:   n = 5      ->  5
Example 3:   n = 135    ->  110
             (1..99 has 90 special numbers; 100..135 adds 20 more)


CONSTRAINTS
-----------
    1 <= n <= 2 * 10^9


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Digit DP again (see 017 for the gentler warm-up). Build numbers from the most
significant digit, with three pieces of state:

    pos       which position you're filling
    mask      which digits 0-9 are already used (10 bits)
    tight     is the prefix still equal to n's prefix?

plus one more that trips everyone up:

    started   have you placed a real (non-leading-zero) digit yet?

Why `started`? Shorter numbers like 7 can be thought of as "007" padded to
n's length. Those leading zeros are NOT digits of the number, so they must not
mark 0 as used. Without the flag, 10 written as "010" looks like it repeats 0
and gets wrongly rejected.

A second solution is pure combinatorics: count shorter lengths with
permutations, then walk n's digits like problem 017.


WHAT TO THINK ABOUT
--------------------
1. How many special numbers have exactly k digits? (First digit 1-9, then
   choose from the remaining digits without reuse.)

2. In the same-length walk, at position i with prefix already fixed, how many
   unused digits are smaller than n[i]? What's left to fill afterwards?

3. In the memoized version, which states actually need memoizing? (Tight
   states occur once per position; only non-tight states repeat.)


PROGRESSIVE HINTS
------------------
Hint 1 (combinatorics): shorter = sum over k < L of 9 * P(9, k - 1), where
        P(a, b) = a! / (a - b)!.

Hint 2: Same length: for position i, candidates are digits d < n[i], not used,
        and d != 0 when i == 0. Each contributes P(10 - i - 1, L - i - 1).
        Then if n[i] is already used, stop; else mark it and continue.

Hint 3: If the walk finishes, n itself is special: +1.


COMPLEXITY TARGET
------------------
    Time:  O(L * 10) combinatorics, or O(L * 2^10 * 10) digit DP
    Space: O(1) / O(L * 2^10)
================================================================================
*/

func main() {
	fmt.Println("Solution for Count Special Integers not implemented yet")
}
