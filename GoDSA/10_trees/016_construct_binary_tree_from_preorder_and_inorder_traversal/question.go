package main

/*
================================================================================
LeetCode 105 · Construct Binary Tree from Preorder and Inorder Traversal
                                                                         [Medium]
https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given two integer slices preorder and inorder, where preorder is the preorder
traversal of a binary tree and inorder is the inorder traversal of the SAME
tree, construct and return the binary tree.


EXAMPLES
--------
Example 1:
    Input:  preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]
    Output: [3,9,20,null,null,15,7]

Example 2:
    Input:  preorder = [-1], inorder = [-1]
    Output: [-1]


CONSTRAINTS
-----------
    1 <= preorder.length <= 3000
    inorder.length == preorder.length
    -3000 <= preorder[i], inorder[i] <= 3000
    preorder and inorder consist of UNIQUE values.
    Each value of inorder also appears in preorder.
    preorder is guaranteed to be the preorder traversal of the tree.
    inorder is guaranteed to be the inorder traversal of the tree.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
preorder[0] tells you WHO the root is. Its position in inorder tells you HOW
MANY nodes belong to the left subtree — everything to its left in inorder is
the left subtree, everything to its right is the right subtree. That single
split, applied recursively, rebuilds the whole tree.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Python's dict + slicing makes "pop the front of preorder" and "index into
   inorder" both trivially cheap-looking, but repeated `inorder.index(v)` is
   O(n) per call there too — the same O(n) index-map trick applies in Go.
   Go's harder edge: there's no `list.pop(0)`-flavored built-in and no easy
   "return multiple things and unpack" the way Python's tuple return gives a
   node-plus-updated-index in one expression — you either (a) advance a
   shared cursor via a closure the way the topic guide's serialize/
   deserialize does, or (b) return the node AND an updated bound explicitly.
   This solution uses (a): a closure-captured cursor into preorder.

2. Precompute `valToInorderIdx := make(map[int]int, len(inorder))` once, up
   front — O(1) lookups instead of O(n) `slices.Index` per node, which is
   what makes this O(n) instead of O(n^2).

3. Recurse on INDEX BOUNDS into inorder (lo, hi), never re-slice inorder
   itself — slicing copies nothing in Go (slices share backing arrays) but
   passing bounds is still clearer than juggling shrinking sub-slices here,
   and avoids any accidental aliasing surprises.


PROGRESSIVE HINTS
-----------------
Hint 1: preorder[0] is always the current subtree's root.

Hint 2: Look up that value's position in inorder — everything left of it (in
        the current inorder window) is the left subtree, everything right is
        the right subtree.

Hint 3: A single index into preorder advances in exactly the order nodes are
        CREATED (root, then entire left subtree, then entire right subtree)
        — build the left child before the right child, or the cursor will
        hand the right subtree the wrong values.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(n)
================================================================================
*/

// TreeNode mirrors the topic guide's shape; each package redeclares it.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourBuildTree is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/016_construct_binary_tree_from_preorder_and_inorder_traversal
func YourBuildTree(preorder []int, inorder []int) *TreeNode {
	// YOUR CODE HERE
	return nil
}
