package main

/*
================================================================================
LeetCode 94 · Binary Tree Inorder Traversal                              [Easy]
https://leetcode.com/problems/binary-tree-inorder-traversal/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, return the inorder traversal of its nodes'
values: visit LEFT subtree, then ROOT, then RIGHT subtree.

EXAMPLES
--------
Example 1:
    Input:  root = [1,null,2,3]
    Output: [1,3,2]

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
Inorder visits left, then node, then right. It's the traversal with the
special property: run it on a Binary SEARCH Tree and the values come out
SORTED — that's the reason inorder gets its own topic (11 · BST) instead of
being just one of three interchangeable orders. Here, on a plain binary
tree with no ordering invariant, there's nothing sorted about the output —
it's simply "left subtree's values, then this node, then right subtree's
values," recursively.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. Same nil-as-empty-subtree, pointer-accumulator patterns as 001 — reuse
   the shape, change WHERE the visit line sits relative to the two
   recursive calls.
2. The iterative version is the one worth knowing cold: "push down the left
   spine, pop, visit, step right" — a fundamentally different stack
   discipline from preorder's "push right then left."

PROGRESSIVE HINTS
------------------
Hint 1: Inorder = recurse(left), then visit(node), then recurse(right).
Hint 2: Iteratively: walk all the way left, pushing every node onto a stack
        as you go, THEN pop-visit-step-right.
Hint 3: The loop condition needs both `curr != nil` (still descending) and
        `len(stack) > 0` (nodes waiting to be visited) — dropping either
        misses part of the tree.

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

// YourInorderTraversal is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/002_binary_tree_inorder_traversal
func YourInorderTraversal(root *TreeNode) []int {
	// YOUR CODE HERE
	return nil
}
