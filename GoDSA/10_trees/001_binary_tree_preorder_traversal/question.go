package main

/*
================================================================================
LeetCode 144 · Binary Tree Preorder Traversal                            [Easy]
https://leetcode.com/problems/binary-tree-preorder-traversal/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, return the preorder traversal of its nodes'
values: visit ROOT, then LEFT subtree, then RIGHT subtree.

EXAMPLES
--------
Example 1:
    Input:  root = [1,null,2,3]
    Output: [1,2,3]

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
Preorder means "visit before you descend": print the node, then walk left,
then walk right. It is the traversal that mirrors how you'd write the tree
back out as nested parentheses, and it's the shape LC 297 (serialize/
deserialize) leans on — a node's value comes before its children's, so a
decoder reading the sequence left-to-right always knows what to build next.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. `*TreeNode` is a pointer; `nil` is the empty-tree/empty-subtree signal,
   exactly like Python's `None` — but dereferencing a nil pointer PANICS in
   Go instead of raising a catchable exception.
2. Accumulating into a slice: either thread a `*[]int` pointer through the
   recursion, or return a new slice at each call and `append` the caller's
   copy to it. The first avoids repeated small allocations; the second is
   easier to read. Both are shown in the solution.
3. The iterative version needs an EXPLICIT stack (`[]*TreeNode`) because Go
   has no tail-call optimization — a hand-rolled stack is how you trade a
   call-stack-depth risk for a heap-allocated one you control.

PROGRESSIVE HINTS
------------------
Hint 1: Preorder = visit(node), then recurse(left), then recurse(right).
Hint 2: The base case is `node == nil` — return without visiting anything.
Hint 3: For the iterative form, push right child before left child so left
        pops (and is visited) first.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(h)  (h = height; call stack or explicit stack)
================================================================================
*/

// TreeNode is LeetCode's binary tree node shape, redeclared per package.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourPreorderTraversal is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/001_binary_tree_preorder_traversal
func YourPreorderTraversal(root *TreeNode) []int {
	// YOUR CODE HERE
	return nil
}
