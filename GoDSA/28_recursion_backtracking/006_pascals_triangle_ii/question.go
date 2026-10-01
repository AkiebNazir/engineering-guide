package main

/*
================================================================================
LeetCode 119 · Pascal's Triangle II                                      [Easy]
https://leetcode.com/problems/pascals-triangle-ii/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given an integer `rowIndex`, return the `rowIndex`-th row (0-indexed) of
Pascal's triangle.

In Pascal's triangle, each number is the sum of the two numbers directly
above it:

    row 0:          [1]
    row 1:         [1,1]
    row 2:        [1,2,1]
    row 3:       [1,3,3,1]
    row 4:      [1,4,6,4,1]

EXAMPLES
--------
Example 1:
    Input:  rowIndex = 3
    Output: [1,3,3,1]

Example 2:
    Input:  rowIndex = 0
    Output: [1]

Example 3:
    Input:  rowIndex = 1
    Output: [1,1]

CONSTRAINTS
-----------
    0 <= rowIndex <= 33

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Everything before this problem in the folder (001-005) recurses down to a
single SCALAR answer: a count, a digit sum, a boolean. This is the first
problem where the COMBINE step has to produce a whole LIST as its output,
built from the previous level's list.

The recursive idea is exactly the definition: `row(n)` is derived entirely
from `row(n - 1)` by sliding a window of two and summing —

    row(n-1) = [1, 3, 3, 1]                  (n-1 = 3)
                1  1+3 3+3 3+1  1
    row(n)   = [1,  4,  6,  4, 1]             (n = 4)

The base case is the smallest row that needs no derivation: `row(0) = [1]`.
Everything else is "take the row one smaller, then build this row from it."

Notice this is a LINEAR recursion (one call to a strictly smaller n), same
shape as 004/005 — the only thing that changed is what a "combine step"
means when the value flowing up is a list instead of a number.

WHAT TO THINK ABOUT
--------------------
1. What is the base case here, concretely — what is `row(0)`?
2. Given `row(n-1)` as a list, how do you build `row(n)` from it without
   any extra state besides that one list?
3. The classic O(1)-extra-space trick for the ITERATIVE version is updating
   the row IN PLACE from right to left — why right to left, and not left to
   right? (Try it left to right on paper and see what breaks.)
4. Do you actually need to keep every previous row around, or only the most
   recent one? What does that say about the space the recursive version
   pays versus the iterative one?

PROGRESSIVE HINTS
------------------
Hint 1: Base case: `row(0) = [1]`.
Hint 2: Get `row(n-1)` via a recursive call, then build `row(n)` by summing
        adjacent pairs of `row(n-1)`, with a `1` bookending both ends.
Hint 3: `row(n)[i] = row(n-1)[i-1] + row(n-1)[i]` for `0 < i < n`, and
        `row(n)[0] = row(n)[n] = 1`.
Hint 4: The in-place iterative trick: start `row = [1]`, and for each new
        row index, walk the CURRENT row from right to left inserting/adding
        so you never overwrite a value you still need to read.

COMPLEXITY TARGET
------------------
    Recursive (new list per level): O(rowIndex^2) time, O(rowIndex^2) space
                                     (every intermediate row is kept alive on
                                     the call stack simultaneously)
    Iterative in-place:             O(rowIndex^2) time, O(rowIndex) space
================================================================================
*/

// TODO: Implement the stub
