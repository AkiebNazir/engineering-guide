package main

/*
================================================================================
LeetCode 112 · Path Sum                                                  [Easy]
https://leetcode.com/problems/path-sum/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree and an integer targetSum, return true if the
tree has a root-to-LEAF path such that adding up all the values along the
path equals targetSum. Otherwise return false.

A leaf is a node with no children.


EXAMPLES
--------
Example 1:
    Input:  root = [5,4,8,11,null,13,4,7,2,null,null,null,1], targetSum = 22
    Output: true
    Explanation: 5 -> 4 -> 11 -> 2 sums to 22.

Example 2:
    Input:  root = [1,2,3], targetSum = 5
    Output: false
    Explanation: No root-to-leaf path sums to 5.

Example 3:
    Input:  root = [], targetSum = 0
    Output: false
    Explanation: An empty tree has no leaf, hence no path at all.


CONSTRAINTS
-----------
    The number of nodes is in the range [0, 5000].
    -1000 <= Node.Val <= 1000
    -1000 <= targetSum <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is not "does any subtree sum to targetSum" — it is specifically
root-to-LEAF. A node with only one child does NOT count as a stopping point;
you must keep going until Left AND Right are both nil.

The natural move: push the "remaining budget" DOWN as you recurse, and only
ask "did I hit exactly 0?" once you are standing on a leaf.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. nil root: the problem defines an empty tree as having NO paths, so the
   answer is false even if targetSum happens to be 0. Handle this before
   touching node.Val.

2. Leaf test is `node.Left == nil && node.Right == nil` — both nil pointers,
   checked explicitly. There is no "isLeaf()" method Go hands you for free.

3. Watch the trap of checking `node.Val == remaining` too early: a node with
   ONE nil child and one non-nil child is not a leaf, even though recursing
   into the nil side would (if you let it) look like success at the wrong
   level if you're not careful about what "remaining" means at a nil node.


PROGRESSIVE HINTS
-----------------
Hint 1: Recurse with a shrinking target: remaining = targetSum - node.Val.

Hint 2: Base case for a genuine leaf: remaining == 0 after subtracting the
        leaf's own value.

Hint 3: A nil node itself is never where you succeed — only real leaves are.
        So check "is this a leaf" before recursing into children, and return
        false (not true) for a nil node reached directly.


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

// YourHasPathSum is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/011_path_sum
func YourHasPathSum(root *TreeNode, targetSum int) bool {
	// YOUR CODE HERE
	return false
}
