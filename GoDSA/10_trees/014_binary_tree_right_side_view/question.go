package main

/*
================================================================================
LeetCode 199 · Binary Tree Right Side View                             [Medium]
https://leetcode.com/problems/binary-tree-right-side-view/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, imagine yourself standing on the RIGHT side
of it. Return the values of the nodes you can see, ordered from top to
bottom.


EXAMPLES
--------
Example 1:
    Input:  root = [1,2,3,null,5,null,4]
    Output: [1,3,4]

Example 2:
    Input:  root = [1,null,3]
    Output: [1,3]

Example 3:
    Input:  root = []
    Output: []


CONSTRAINTS
-----------
    The number of nodes is in the range [0, 100].
    -100 <= Node.Val <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Rightmost visible node per level" is a one-line addition to problem 013's
BFS skeleton: keep only the LAST value popped in each level's inner loop.
It can also be done with DFS (right-before-left), taking the first node
reached at each new depth — a genuinely different traversal order arriving
at the same answer, useful to show you understand both families.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. BFS version: reuse the levelSize-snapshot pattern from problem 013
   exactly, just record `level[len(level)-1]` instead of the whole level.

2. DFS version: visit Right BEFORE Left, and record a node's value only the
   first time its depth is reached (`depth == len(result)`) — this is the
   opposite bias from problem 013's DFS variant, which visited Left first
   and recorded every node.

3. nil root: no view exists — return nil, not [0] or an empty non-nil slice
   that differs semantically from "no nodes."


PROGRESSIVE HINTS
-----------------
Hint 1: BFS by level, keep only the last node's value per level.

Hint 2: Or DFS with (node, depth), visiting Right child before Left, and
        only recording a value when depth is being seen for the first time.

Hint 3: Both are O(n) time; they differ only in whether the "first-seen"
        value at a depth happens to be encountered via BFS's last-pop or
        DFS's right-biased first-visit.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(h) or O(w) depending on approach
================================================================================
*/

// TreeNode mirrors the topic guide's shape; each package redeclares it.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourRightSideView is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/014_binary_tree_right_side_view
func YourRightSideView(root *TreeNode) []int {
	// YOUR CODE HERE
	return nil
}
