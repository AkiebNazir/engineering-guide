package main

/*
================================================================================
LeetCode 104 · Maximum Depth of Binary Tree                              [Easy]
https://leetcode.com/problems/maximum-depth-of-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, return its maximum depth: the number of
nodes along the longest path from the root down to the farthest leaf.

EXAMPLES
--------
Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: 3

Example 2:
    Input:  root = [1,null,2]
    Output: 2

Example 3:
    Input:  root = []
    Output: 0

CONSTRAINTS
-----------
    Number of nodes in [0, 10^4]
    -100 <= Node.Val <= 100

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Every node's depth is "1 + the deeper of my two children's depths." A leaf
has no children, so its depth is 1; an empty subtree has depth 0. That
recurrence is postorder: you need BOTH children's answers before you can
compute the parent's — exactly the shape from 003, with the visit step
replaced by "combine, don't just record."

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. `max` is a Go 1.21+ builtin for ordered types — use it directly, no
   helper function needed (older code bases hand-roll one; this file
   doesn't need to).
2. This is the O(h) SPACE bound made concrete: the recursion depth IS the
   height being measured. A skewed tree of n nodes means n stack frames.
3. BFS level-order counting levels is an equally valid O(n) time solution
   with a DIFFERENT space profile — O(w), the tree's width, not O(h). Worth
   comparing against the recursive form explicitly.

PROGRESSIVE HINTS
------------------
Hint 1: What is the depth of an empty tree (nil)? What's the depth of a leaf?
Hint 2: depth(node) = 1 + max(depth(node.Left), depth(node.Right)).
Hint 3: Iteratively, count how many BFS levels you pop before the queue
        empties.

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

// YourMaxDepth is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/005_maximum_depth_of_binary_tree
func YourMaxDepth(root *TreeNode) int {
	// YOUR CODE HERE
	return 0
}
