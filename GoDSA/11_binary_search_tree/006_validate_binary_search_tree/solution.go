package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 98 · Validate Binary Search Tree                 [Medium]
https://leetcode.com/problems/validate-binary-search-tree/
================================================================================

PROBLEM
-------
Given the `root` of a binary tree, determine if it is a valid binary search
tree (BST).

A valid BST is defined as follows:
    · The left subtree of a node contains only nodes with keys LESS THAN the
      node's key.
    · The right subtree of a node contains only nodes with keys GREATER THAN
      the node's key.
    · Both the left and right subtrees must also be binary search trees.


EXAMPLES
--------
Example 1:
    Input:  root = [2,1,3]
    Output: true

              2
            ╱   ╲
          1       3

Example 2:
    Input:  root = [5,1,4,null,null,3,6]
    Output: false
    Explanation: the root's value is 5 but its right child's value is 4.

              5
            ╱   ╲
          1       4
                ╱   ╲
              3       6


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 10^4].
    -2^31 <= Node.val <= 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Read the definition once more, slowly. It says "the left SUBTREE contains
only nodes with keys less than the node's key" — the whole subtree, every
node in it, not just the immediate child.

⚠️  THIS IS THE PROBLEM. Nearly every failed attempt at LC 98 checks only
    parent-against-child:

              5
            ╱   ╲
          1       7
                ╱   ╲
              3       8

    Every parent-child pair here is fine: 1 < 5, 7 > 5, 3 < 7, 8 > 7.
    But the tree is NOT a BST — 3 sits in the RIGHT subtree of 5, and 3 < 5.
    A search for 3 starting at the root would turn LEFT at 5 and never find
    it. The tree is unusable as a BST, and a parent-child-only checker calls
    it valid.

Two correct approaches, and you should know both:

  A. BOUNDS. Carry an allowed open interval down the recursion. The root may
     be anything; going left tightens the upper bound to the parent's value,
     going right tightens the lower bound. A node is valid iff its value is
     strictly inside its interval.

         node 5: (-inf, +inf)   ok
           node 1: (-inf, 5)     ok
           node 7: (5, +inf)     ok
             node 3: (5, 7)      3 <= 5  ->  INVALID ✅ caught

  B. IN-ORDER. An in-order traversal of a valid BST is a strictly increasing
     sequence. Traverse in-order and check each value against the previous
     one. This is the topic's one big idea used as a test.

         in-order of the tree above: 1, 5, 3, 8  ->  3 < 5, not increasing
                                                     ->  INVALID ✅ caught


PROGRESSIVE HINTS
------------------
Hint 1: Whatever you write must reject a tree whose every parent-child pair
        is individually fine. Build that tree on paper first and test against
        it.

Hint 2: For the bounds approach the recursive signature is
        `valid(node, low, high)`, and only ONE of the two bounds changes per
        recursive call.

Hint 3: For the in-order approach you only need to remember the PREVIOUS
        value, not the whole list.

Hint 4: "Less than", not "less than or equal to" — duplicates make the tree
        invalid under this problem's definition.


COMPLEXITY TARGET
------------------
    Time:  O(n) — every node must be checked; there is no pruning here
    Space: O(h) — the recursion stack, or the explicit stack for in-order
================================================================================
*/

func main() {
	fmt.Println("Solution for Validate Binary Search Tree not implemented yet")
}
