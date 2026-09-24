package main

/*
================================================================================
LeetCode 226 · Invert Binary Tree                                        [Easy]
https://leetcode.com/problems/invert-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, invert the tree (mirror it left-to-right)
and return its root.

EXAMPLES
--------
Example 1:
    Input:  root = [4,2,7,1,3,6,9]
    Output: [4,7,2,9,6,3,1]

Example 2:
    Input:  root = [2,1,3]
    Output: [2,3,1]

Example 3:
    Input:  root = []
    Output: []

CONSTRAINTS
-----------
    Number of nodes in [0, 100]
    -100 <= Node.Val <= 100

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
At every node, swap the two CHILD POINTERS. That's the whole algorithm —
the subtrees move as whole units (a pointer swap moves everything beneath
it in one assignment), the values inside them never change.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. `node.Left, node.Right = node.Right, node.Left` is a SIMULTANEOUS
   assignment in Go, just like Python's tuple-unpacking swap — the
   right-hand side is fully evaluated before either field is written. Doing
   it as two separate statements is a real, distinct bug (see COMMON
   MISTAKES).
2. This mutates the ORIGINAL tree in place through its pointers — LeetCode
   expects that, but it's worth being explicit that the caller's `*TreeNode`
   the function was handed now points into a different-shaped tree. Contrast
   with a "pure" version that allocates a whole new tree and leaves the
   input untouched.
3. Because the swap at a node doesn't depend on any other node's result,
   the traversal ORDER is free here — preorder, postorder, and level order
   all produce the same final tree. That's unusual; most tree problems in
   this topic force a specific order.

PROGRESSIVE HINTS
------------------
Hint 1: At each node, what do you do to its two children?
Hint 2: `node.Left, node.Right = node.Right, node.Left` — one line, in place.
Hint 3: Recurse into both children (order doesn't matter) so the swap
        happens at every level, not just the root.

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

// YourInvertTree is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/004_invert_binary_tree
func YourInvertTree(root *TreeNode) *TreeNode {
	// YOUR CODE HERE
	return nil
}
