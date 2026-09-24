package main

/*
================================================================================
LeetCode 863 · All Nodes Distance K in Binary Tree                      [Medium]
https://leetcode.com/problems/all-nodes-distance-k-in-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, the target node `target`, and an integer k,
return a slice of the values of all nodes that have a distance k from the
target node. You can return the answer in any order.


EXAMPLES
--------
Example 1:
    Input:  root = [3,5,1,6,2,0,8,null,null,7,4], target = 5, k = 2
    Output: [7 4 1]

                3
              /   \
             5     1
            / \   / \
           6   2 0   8
              / \
             7   4

Example 2:
    Input:  root = [1], target = 1, k = 3
    Output: []


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 500].
    0 <= Node.Val <= 500, all values unique.
    target is a node in the tree.
    0 <= k <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Distance counts edges, and paths may go UP through parents. Tree nodes only
point down, so add the missing upward edges with a parent map, then BFS from
target for k levels.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Maps can be keyed by pointer: map[*TreeNode]*TreeNode. Pointer keys compare
   by address, so this is identity, exactly like Python's dict keyed by node.

2. Reading a missing key returns the zero value, nil — so parent[root] is nil
   without having to store it. That's "make the zero value useful" working
   for you.

3. A slice used as a queue: `queue = queue[1:]` is O(1) but keeps the
   backing array alive. For level-order BFS it's simpler to build a fresh
   `next` slice per level.


PROGRESSIVE HINTS
-----------------
Hint 1: DFS once to fill parent.

Hint 2: BFS level by level from target over Left, Right, parent[node], with a
        visited map[*TreeNode]bool.

Hint 3: After k levels, the current level is the answer.


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

// YourDistanceK is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/020_all_nodes_distance_k_in_binary_tree
func YourDistanceK(root, target *TreeNode, k int) []int {
	// YOUR CODE HERE
	return nil
}
