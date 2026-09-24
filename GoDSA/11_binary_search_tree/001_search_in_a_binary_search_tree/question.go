package main

/*
================================================================================
LeetCode 700 · Search in a Binary Search Tree                            [Easy]
https://leetcode.com/problems/search-in-a-binary-search-tree/
Topic: 11 · Binary Search Tree
================================================================================

PROBLEM
-------
You are given the root of a binary SEARCH tree and an integer val. Find the
node in the BST whose value equals val and return the subtree rooted at that
node. If no such node exists, return nil.

EXAMPLES
--------
Example 1:
    Input:  root = [4,2,7,1,3], val = 2
    Output: [2,1,3]

Example 2:
    Input:  root = [4,2,7,1,3], val = 5
    Output: []

CONSTRAINTS
-----------
    Number of nodes in [1, 5000]
    1 <= Node.Val <= 10^7
    root is a valid BST
    1 <= val <= 10^7

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is NOT the general binary-tree search from topic 10 (where you must
check both children because there's no ordering to exploit). The BST
invariant tells you, at every node, exactly ONE side that could possibly
contain val — the other side is provably empty of it. That turns an O(n)
worst-case tree search into an O(h) descent.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. A nil *TreeNode is a completely valid "not found" answer in Go — unlike
   Python's None which unifies with everything, a nil pointer here still has
   a concrete zero-value type (*TreeNode), so comparisons like `n == nil` are
   exactly what terminate the loop/recursion.
2. Iterative is O(1) auxiliary space here — no need for a stack, since at
   each step you know which single child to move to.

PROGRESSIVE HINTS
------------------
Hint 1: What does it mean for a value to be "not here" once you know left
        subtree < node < right subtree?
Hint 2: Compare val to root.Val, move into exactly one child, repeat.
Hint 3: Stop the moment val == node.Val (return node) or node == nil
        (return nil, not found).

COMPLEXITY TARGET
------------------
    Time:  O(h)  (O(log n) balanced, O(n) skewed)
    Space: O(1) iterative / O(h) recursive
================================================================================
*/

type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourSearchBST is your attempt.
// Implement it, then run:  cd GoDSA && go run ./11_binary_search_tree/001_search_in_a_binary_search_tree
func YourSearchBST(root *TreeNode, val int) *TreeNode {
	// YOUR CODE HERE
	return nil
}
