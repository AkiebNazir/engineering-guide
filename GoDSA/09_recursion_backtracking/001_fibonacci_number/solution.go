package main

import "fmt"

/*
================================================================================
LeetCode 509 · Fibonacci Number                                          [Easy]
https://leetcode.com/problems/fibonacci-number/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
The Fibonacci numbers, commonly denoted F(n), form a sequence such that each
number is the sum of the two preceding ones, starting from 0 and 1:

    F(0) = 0,  F(1) = 1
    F(n) = F(n - 1) + F(n - 2),  for n > 1

Given `n`, calculate F(n).

EXAMPLES
--------
Example 1:
    Input:  n = 2
    Output: 1
    Explanation: F(2) = F(1) + F(0) = 1 + 0 = 1.

Example 2:
    Input:  n = 3
    Output: 2
    Explanation: F(3) = F(2) + F(1) = 1 + 1 = 2.

Example 3:
    Input:  n = 4
    Output: 3
    Explanation: F(4) = F(3) + F(2) = 2 + 1 = 3.

CONSTRAINTS
-----------
    0 <= n <= 30

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is not a backtracking problem — there is no decision tree, no set of
choices to explore, and no leaf to validate. It is here as the BRIDGE into the
topic: the vehicle for seeing, with real numbers, why naive recursion over
OVERLAPPING subproblems is exponential, and why remembering an answer you have
already computed (memoization) collapses that to linear. This is the exact idea
DP (topics 16-17) is built entirely around.

The naive recursive translation of the definition:

    def fib(n):
        if n < 2: return n
        return fib(n - 1) + fib(n - 2)

looks correct and IS correct — but trace the call tree for fib(5):

    fib(5)
    +-- fib(4)
    |   +-- fib(3)
    |   |   +-- fib(2) -- fib(1), fib(0)
    |   |   +-- fib(1)
    |   +-- fib(2) -- fib(1), fib(0)        <- fib(2) AGAIN
    +-- fib(3)                               <- fib(3) AGAIN
        +-- fib(2) -- fib(1), fib(0)
        +-- fib(1)

fib(3) is computed twice, fib(2) three times. The redundancy compounds with n:
the number of calls roughly doubles each time n increases by 1, giving O(2^n)
(more precisely O(phi^n), phi = the golden ratio ~1.618) total calls.

WHAT TO THINK ABOUT
--------------------
1. What is the actual shape of the call tree? Is fib(k) ever called more than
   once for the same k? Count it, don't guess.
2. If you remember the result of fib(k) the first time you compute it, what
   happens to every LATER call that asks for fib(k) again?
3. Two ways to remember: a dict/array cache checked before recursing
   (top-down/"memoization"), or building the answer from the bottom up in a
   loop with no recursion at all (bottom-up/"tabulation"). Which uses less
   call-stack depth?
4. Can you get O(1) extra space, forgetting even the array?

PROGRESSIVE HINTS
------------------
Hint 1: Base cases first: F(0) = 0, F(1) = 1.
Hint 2: Naive recursion is correct but exponential — measure it, don't take it
        on faith.
Hint 3: A dict `memo = {}` checked at the top of the function, populated before
        returning, turns the exponential call tree into a linear one: each
        distinct n is computed once.
Hint 4: You don't need recursion OR a full array at all — two rolling
        variables and a loop get you O(n) time, O(1) space.

COMPLEXITY TARGET
------------------
    Naive recursion:  O(2^n) time (really O(phi^n)), O(n) space (call stack)
    Memoized:          O(n) time, O(n) space
    Iterative rolling: O(n) time, O(1) space
================================================================================
*/

func main() {
	fmt.Println("Solution for Fibonacci Number not implemented yet")
}
