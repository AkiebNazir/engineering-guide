package main

/*
================================================================================
LeetCode 124 · Binary Tree Maximum Path Sum                              [Hard]
https://leetcode.com/problems/binary-tree-maximum-path-sum/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
A path in a binary tree is a sequence of nodes where each pair of adjacent
nodes in the sequence has an edge connecting them. A node can only appear in
the sequence at most once. The path does NOT need to pass through the root.

The path sum of a path is the sum of the node's values in the path.

Given the root of a binary tree, return the maximum path sum of any
non-empty path.


EXAMPLES
--------
Example 1:
    Input:  root = [1,2,3]
    Output: 6
    Explanation: The optimal path is 2 -> 1 -> 3, sum = 2+1+3 = 6.

Example 2:
    Input:  root = [-10,9,20,null,null,15,7]
    Output: 42
    Explanation: The optimal path is 15 -> 20 -> 7, sum = 15+20+7 = 42.
    (It does NOT pass through the root, whose value -10 would only hurt.)


CONSTRAINTS
-----------
    The number of nodes is in the range [1, 3 * 10^4].
    -1000 <= Node.Val <= 1000


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A legal path is a "V" shape: it climbs up from somewhere, turns around at
exactly ONE node (its peak), and descends. It cannot branch twice at the same
node in a way that would make it fork. So every valid path has exactly one
turning point — maximize over all n nodes as candidate turning points.

At a node, "best path turning here" needs the best straight-DOWN sum from
each child (not the best path anywhere in each child's subtree). That
distinction — "value to RECORD as a candidate answer" vs. "value to RETURN
to the parent for further extension" — is the one hard idea in this problem.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Go can't quietly return two different numbers up through a single
   recursive call the way a tuple-return language makes tempting to fake —
   you need a genuinely separate channel for "the running best" versus "the
   value handed to my parent." A closure-captured variable (topic guide
   §3.2's diameter pattern), a pointer to an int, or a small struct field
   are the three idiomatic options; this solution uses a closure.

2. A negative-sum branch should be DROPPED, not included — `max(gain, 0)`
   on each child's returned value. Not dropping negative branches is the
   single most common way to get this wrong.

3. Global negative tree, e.g. all values negative: the answer is still some
   single node's value (the least negative one, taken alone) — never 0 and
   never "no path," because the path must be non-empty. Seed your running
   best at negative infinity, not 0.


PROGRESSIVE HINTS
-----------------
Hint 1: Write a postorder helper `gain(node) int` that returns the best sum
        of a path starting at node and going straight down into AT MOST one
        child.

Hint 2: Inside gain(), compute `left = max(gain(node.Left), 0)` and
        `right = max(gain(node.Right), 0)` — clamp negative contributions to
        zero so a bad branch is simply not taken.

Hint 3: Update a running best with `node.Val + left + right` (the full "V"
        turning at this node, using BOTH children) BEFORE returning
        `node.Val + max(left, right)` (only ONE child, so the parent can
        still extend the path upward).


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

// YourMaxPathSum is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/018_binary_tree_maximum_path_sum
func YourMaxPathSum(root *TreeNode) int {
	// YOUR CODE HERE
	return 0
}
