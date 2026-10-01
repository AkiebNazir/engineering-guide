package main

/*
================================================================================
LeetCode 1448 · Count Good Nodes in Binary Tree                        [Medium]
https://leetcode.com/problems/count-good-nodes-in-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given a binary tree root, a node X in the tree is named GOOD if in the path
from root to X there are no nodes with a value greater than X's value.

Return the number of good nodes in the binary tree.


EXAMPLES
--------
Example 1:
    Input:  root = [3,1,4,3,null,1,5]
    Output: 4
    Explanation: Nodes in blue are good: root (3), 4, 5, and the rightmost 3.
    The left 3 is not good because 4 is on the path from root and 4 > 3.

Example 2:
    Input:  root = [3,3,null,4,2]
    Output: 3

Example 3:
    Input:  root = [1]
    Output: 1


CONSTRAINTS
-----------
    The number of nodes is in the range [1, 10^5].
    Each node's value is between [-10^4, 10^4].


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Good" depends entirely on ANCESTORS, not descendants — the opposite
direction from problem 018 (Max Path Sum), where the answer at a node
depends on its children. That makes this a TOP-DOWN problem: the only state
a node needs is "the maximum value seen on the path from the root to my
parent," and that must travel DOWN as a recursion parameter, not bubble up
as a return value.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. This is the direct mirror of problem 011 (Path Sum)'s top-down shape:
   thread "maxSoFar" down through the call, exactly like "remaining budget"
   was threaded down there.

2. The root is always good (empty path above it -> vacuously no ancestor
   exceeds it) — seed maxSoFar with root.Val itself, or with -inf/math.MinInt
   and let the root's own comparison naturally succeed.

3. Counting: return an int and sum children's counts, OR close over a
   counter variable like the topic guide's diameter closure — either is
   fine here since there's no second, distinct "recorded vs returned" value
   the way problem 018 needs.


PROGRESSIVE HINTS
-----------------
Hint 1: Recurse with a parameter: the max value seen so far on this path.

Hint 2: A node is good iff node.Val >= maxSoFar (using the path INCLUDING
        itself, so equal values still count as good).

Hint 3: Recurse into children with max(maxSoFar, node.Val) as the new
        threshold, and sum 1 (if good) + good count from left + good count
        from right.


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

// YourGoodNodes is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/015_count_good_nodes_in_binary_tree
func YourGoodNodes(root *TreeNode) int {
	// YOUR CODE HERE
	return 0
}
