package main

/*
================================================================================
LeetCode 102 · Binary Tree Level Order Traversal                       [Medium]
https://leetcode.com/problems/binary-tree-level-order-traversal/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, return the level order traversal of its
nodes' values (i.e., from left to right, level by level), as a slice of
per-level slices.


EXAMPLES
--------
Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: [[3],[9,20],[15,7]]

Example 2:
    Input:  root = [1]
    Output: [[1]]

Example 3:
    Input:  root = []
    Output: []


CONSTRAINTS
-----------
    The number of nodes is in the range [0, 2000].
    -1000 <= Node.Val <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is the topic guide's canonical BFS: a queue seeded with the root, and
the key trick is capturing `levelSize := len(queue)` BEFORE the inner loop
starts appending children — that snapshot is what tells you where one level
ends and the next begins. Without it, children get mixed into the same
"level" as their parents.

Connect this to topic 07 (queue/deque): a plain Go slice used with
`queue[1:]` IS a queue for this purpose — see the topic guide §2.3 for why
the classic "leaky slice" concern from topic 07 doesn't matter for a
single BFS pass whose whole queue is discarded when the function returns.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. nil root must return nil (or an empty [][]int), not a slice containing
   one empty level.

2. Preallocate each level with `make([]int, 0, levelSize)` since you already
   know its exact size from the queue snapshot — no guessing capacity.

3. `queue = queue[1:]` is O(1) (a header slide, not a copy) — this is what
   makes the slice-as-queue viable at all; a `container/list` is not needed
   for a single bounded pass.


PROGRESSIVE HINTS
-----------------
Hint 1: Seed a queue (slice) with just the root.

Hint 2: While the queue isn't empty: snapshot levelSize = len(queue), pop
        exactly that many nodes, appending each one's non-nil children to
        the SAME queue as you go (they become next level's contents).

Hint 3: Collect each level's popped values into its own []int before moving
        to the next iteration of the outer loop.


COMPLEXITY TARGET
-----------------
    Time:  O(n)
    Space: O(w)  where w is the tree's maximum width
================================================================================
*/

// TreeNode mirrors the topic guide's shape; each package redeclares it.
type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourLevelOrder is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/013_binary_tree_level_order_traversal
func YourLevelOrder(root *TreeNode) [][]int {
	// YOUR CODE HERE
	return nil
}
