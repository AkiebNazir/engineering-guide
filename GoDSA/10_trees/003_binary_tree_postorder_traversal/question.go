package main

/*
================================================================================
LeetCode 145 · Binary Tree Postorder Traversal                           [Easy]
https://leetcode.com/problems/binary-tree-postorder-traversal/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, return the postorder traversal of its
nodes' values: visit LEFT subtree, then RIGHT subtree, then ROOT.

EXAMPLES
--------
Example 1:
    Input:  root = [1,null,2,3]
    Output: [3,2,1]

Example 2:
    Input:  root = []
    Output: []

Example 3:
    Input:  root = [1]
    Output: [1]

CONSTRAINTS
-----------
    Number of nodes in [0, 100]
    -100 <= Node.Val <= 100

FOLLOW UP
---------
    Recursive solution is trivial; could you do it iteratively?

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Postorder visits a node LAST, after both its children. That ordering is
exactly what you need whenever a node's answer depends on its children's
answers first — height, diameter, "is this subtree balanced," deleting a
tree bottom-up (free children before their parent), evaluating an
expression tree. Every "bottom-up" tree algorithm in this topic (005, 006,
009, 010) is a postorder traversal wearing different clothes.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. Same pointer-accumulator recursive shape as 001/002; the visit line
   moves to LAST.
2. The iterative form is the awkward one of the three orders. The standard
   trick: do a MODIFIED preorder that visits root, then RIGHT, then LEFT
   (the mirror image of normal preorder), and REVERSE the result at the
   end. Root-right-left reversed is left-right-root — postorder.
3. There is also a genuine two-stack or single-stack-with-a
   "last visited" pointer iterative form that avoids the reverse — shown
   for completeness, but the reverse trick is the one to reach for under
   time pressure.

PROGRESSIVE HINTS
------------------
Hint 1: Postorder = recurse(left), recurse(right), THEN visit(node).
Hint 2: Iteratively, it's easier to build root-right-left (a preorder
        variant) and reverse it at the end than to build left-right-root
        directly with one stack.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(h)
================================================================================
*/

type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourPostorderTraversal is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/003_binary_tree_postorder_traversal
func YourPostorderTraversal(root *TreeNode) []int {
	// YOUR CODE HERE
	return nil
}
