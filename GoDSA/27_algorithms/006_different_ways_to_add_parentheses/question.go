package main

/*
================================================================================
QUESTION · LeetCode 241 · Different Ways to Add Parentheses         [Medium]
https://leetcode.com/problems/different-ways-to-add-parentheses/
================================================================================

PROBLEM
-------
Given a string `expression` of numbers and operators, return all possible
results from computing all the different possible ways to group numbers
and operators. You may return the answer in any order.

The results should fit in a 32-bit integer, and the input string only
contains digits '0'-'9', and the operators '+', '-', and '*'.


EXAMPLES
--------
Example 1:
    Input:  expression = "2-1-1"
    Output: [0, 2]
    Explanation:
        ((2-1)-1) = 0
        (2-(1-1)) = 2

Example 2:
    Input:  expression = "2*3-4*5"
    Output: [-34, -14, -10, -10, 10]
    Explanation:
        (2*(3-(4*5))) = -34
        ((2*3)-(4*5)) = -14
        ((2*(3-4))*5) = -10
        (2*((3-4)*5)) = -10
        (((2*3)-4)*5) = 10


CONSTRAINTS
-----------
    1 <= expression.length <= 20
    expression consists of digits and the operators '+', '-', and '*'.
    All the integer values in the input expression are in the range [0, 99].


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Every operator in the expression is a candidate "last operation applied" --
split the string at that operator into a left sub-expression and a right
sub-expression, recursively compute ALL possible results for each side, and
combine every (left result, right result) pair with that operator. Do this
for EVERY operator position and union all the results. The recursion
overlaps: the same substring (e.g. "3-4*5" inside "2*3-4*5") gets asked for
independently by different top-level splits, so memoize by SUBSTRING (or by
a (start, end) index pair into the original string) to avoid recomputing
it. This is divide & conquer with memoization, NOT array-indexed DP -- the
cache key is "which slice of the expression string," and the recursion
DECIDES WHERE TO SPLIT, unlike DP-1D/2D (topics 16/17) where the state is a
fixed index (or index pair) into an array and the recursion decides how far
back to look, not where to cut.

PROGRESSIVE HINTS
------------------
Hint 1: Base case -- if the (sub)expression has no operators (it's just
        digits), its only possible value is that number itself.
Hint 2: Otherwise, for every operator character at position i, recursively
        solve the LEFT slice [0:i) and the RIGHT slice (i:end), then
        combine every pair of (left_value, right_value) with that operator.
Hint 3: The same substring can be asked for multiple times across
        different top-level splits -- memoize on the substring (a dict
        keyed by the string itself is simplest given the small input size).
Hint 4: Contrast with DP: here the "state" is a slice of a STRING, and the
        recursion's job is to choose a SPLIT POINT, not to look up a fixed
        number of previous array cells.

COMPLEXITY TARGET
------------------
    Time:  bounded by Catalan-number growth in the number of operators,
           memoization collapses repeated substrings
    Space: O(number of distinct substrings x results per substring)
================================================================================
*/

// TODO: Implement the stub
