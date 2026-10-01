package main

/*
================================================================================
LeetCode 101 · Symmetric Tree                                            [Easy]
https://leetcode.com/problems/symmetric-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, check whether it is a mirror of itself
(symmetric around its center).


EXAMPLES
--------
Example 1:
    Input:  root = [1,2,2,3,4,4,3]
    Output: true

Example 2:
    Input:  root = [1,2,2,null,3,null,3]
    Output: false


CONSTRAINTS
-----------
    The number of nodes is in the range [1, 1000].
    -100 <= Node.Val <= 100

FOLLOW UP
---------
    Could you solve it both recursively and iteratively?


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Symmetric" is NOT "same tree" (problem 007) applied to one tree — it is
"the LEFT subtree is a MIRROR of the RIGHT subtree", where mirror means: at
every level, left's-left matches right's-right, and left's-right matches
right's-left. So the comparison must walk two subtrees in lockstep with
CROSSED recursive calls, not the two straight calls same-tree uses.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. This is a two-pointer-over-two-trees recursion: compare(left, right), not
   a single-tree traversal. You'll pass two *TreeNode into every call.

2. nil handling has four cases, not two: both nil (match), exactly one nil
   (mismatch), both non-nil (compare Val then recurse crossed).

3. Iteratively, you need an explicit queue/stack holding PAIRS of nodes to
   compare — a single flat queue of nodes loses the pairing information a
   plain level-order BFS would give you for free.


PROGRESSIVE HINTS
-----------------
Hint 1: Write a helper isMirror(a, b *TreeNode) bool comparing two subtrees.

Hint 2: isMirror(a, b) = (a.Val == b.Val) && isMirror(a.Left, b.Right) &&
        isMirror(a.Right, b.Left) — note the CROSS.

Hint 3: Call isMirror(root.Left, root.Right) from the top, with root itself
        implicitly symmetric to itself.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(h)
================================================================================
*/

// TreeNode mirrors the topic guide's shape; each package redeclares it.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourIsSymmetric is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/012_symmetric_tree
func YourIsSymmetric(root *TreeNode) bool {
	// YOUR CODE HERE
	return false
}
