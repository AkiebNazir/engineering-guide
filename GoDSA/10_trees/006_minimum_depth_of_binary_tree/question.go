package main

/*
================================================================================
LeetCode 111 · Minimum Depth of Binary Tree                              [Easy]
https://leetcode.com/problems/minimum-depth-of-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, return its minimum depth: the number of
nodes along the shortest path from the root down to the nearest LEAF. A
leaf is a node with no children.

EXAMPLES
--------
Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: 2

Example 2:
    Input:  root = [2,null,3,null,4,null,5,null,6]
    Output: 5

CONSTRAINTS
-----------
    Number of nodes in [0, 10^5]
    -1000 <= Node.Val <= 1000

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This LOOKS like 005 with min instead of max — it is not that simple, and
that gap is the entire problem. "Nearest LEAF" is not "nearest node with a
missing child." A one-sided node (exactly one child nil) is NOT a leaf, so
its depth must come from its ONE real child, never from the nil side —
naively taking `min(depth(Left), depth(Right))` on such a node returns 0
from the nil side and reports a false minimum of 1.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. The recursion needs a case split most people don't expect from skimming
   005: nil child (`1 + <the other child's depth>`), leaf (base case, both
   children nil), and general node (`1 + min` over BOTH real children).
2. BFS is arguably the NATURAL fit here, more than for 005 — it finds the
   FIRST leaf level by level and can return as soon as it sees one, without
   visiting the rest of the tree. That's a real early-exit win 005's BFS
   form doesn't get (005 must visit every node no matter what).

PROGRESSIVE HINTS
------------------
Hint 1: Try `[2,null,3]`: node 2 has one child, 3. What's the minimum depth?
        It is NOT 1 (2 is not a leaf — it has a child).
Hint 2: If a node has only one child, the answer must come from THAT child,
        not from the empty side.
Hint 3: BFS naturally finds the shallowest leaf — return as soon as you pop
        a node with no children.

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

// YourMinDepth is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/006_minimum_depth_of_binary_tree
func YourMinDepth(root *TreeNode) int {
	// YOUR CODE HERE
	return 0
}
