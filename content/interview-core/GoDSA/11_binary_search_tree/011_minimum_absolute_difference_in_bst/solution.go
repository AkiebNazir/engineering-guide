package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 530 · Minimum Absolute Difference in BST             [Easy]
https://leetcode.com/problems/minimum-absolute-difference-in-bst/
================================================================================

PROBLEM
-------
Given the `root` of a Binary Search Tree (BST), return the minimum absolute
difference between the values of any two DIFFERENT nodes in the tree.


EXAMPLES
--------
Example 1:
    Input:  root = [4,2,6,1,3]
    Output: 1

              4
            ╱   ╲
          2       6
        ╱   ╲
      1       3

Example 2:
    Input:  root = [1,0,48,null,null,12,49]
    Output: 1

              1
            ╱   ╲
          0       48
                ╱    ╲
              12       49


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [2, 10^4].
    0 <= Node.val <= 10^5

Note: This question is the same as LC 783 "Minimum Distance Between BST
Nodes" — identical problem, different number.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The brute-force reading of "minimum absolute difference between ANY two
nodes" is O(n^2): compare every pair. But this is a BST, and Part 1 of the
topic guide is exactly the tool that turns this into something much
cheaper: in-order traversal produces values in SORTED order.

Once you have a sorted sequence, the minimum absolute difference between
ANY two elements can ONLY occur between two ADJACENT elements — this is
worth being able to justify, not just apply: if `a < b < c` are any three
values, `c - a = (c - b) + (b - a)`, and both terms on the right are
non-negative, so `c - a >= max(c - b, b - a)`. The gap between two
non-adjacent elements is never smaller than the gap between some pair that
IS adjacent. So you never need to check all O(n^2) pairs — you only need to
compare each in-order value to the one immediately before it, exactly like
problem 006's "strictly increasing" check, but tracking the minimum GAP
instead of a boolean.


PROGRESSIVE HINTS
------------------
Hint 1: Sorted order turns "check all pairs" into "check only neighbors."
        Prove to yourself why the true minimum can never come from two
        non-adjacent sorted values (see the inequality above) before
        coding anything.

Hint 2: This is another in-order walk tracking a running `prev`, same
        skeleton as problem 006 (validate) and problem 009 (recover) — the
        only thing that changes is what you DO with `prev` and `curr` at
        each step.

Hint 3: You don't need to store the whole sorted list — just the previous
        value and a running minimum, updated as you go.

Hint 4: The problem guarantees at least 2 nodes, so there is always at
        least one adjacent pair to compare — you don't need to guard
        against "no pairs exist."


COMPLEXITY TARGET
------------------
    Time:  O(n) — one in-order pass, not O(n^2) pairwise comparison
    Space: O(h) for the traversal (recursion stack or explicit stack)
================================================================================
*/

func main() {
	fmt.Println("Solution for Minimum Absolute Difference in BST not implemented yet")
}
