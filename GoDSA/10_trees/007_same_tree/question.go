package main

/*
================================================================================
LeetCode 100 · Same Tree                                                 [Easy]
https://leetcode.com/problems/same-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the roots of two binary trees `p` and `q`, return true if they are
structurally identical AND the nodes have the same values.

EXAMPLES
--------
Example 1:
    Input:  p = [1,2,3], q = [1,2,3]
    Output: true

Example 2:
    Input:  p = [1,2], q = [1,null,2]
    Output: false

Example 3:
    Input:  p = [1,2,1], q = [1,1,2]
    Output: false

CONSTRAINTS
-----------
    Number of nodes in both trees in [0, 100]
    -10^4 <= Node.Val <= 10^4

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Same" means both SHAPE and VALUES match at every position, recursively.
This is two trees walked in lock-step: at each pair of positions, either
both are nil (fine, keep going), exactly one is nil (shape mismatch, done),
or both exist and their values must match before recursing into both pairs
of children.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. Two `*TreeNode` parameters walked together — this is the shape LC 572
   (Subtree of Another Tree, 008) calls repeatedly, and the shape LC 101
   (Symmetric Tree) uses with a CROSSED pairing instead of a parallel one.
2. Pointer equality (`p == q`) in Go compares ADDRESSES, exactly like
   Python's `is`. Two nodes with equal `.Val` but different identities are
   NOT `==`; don't reach for it as a shortcut for value equality.
3. Short-circuit `&&` matters here for both correctness and a cheap
   performance win: a value mismatch at the root should skip recursing
   into children entirely.

PROGRESSIVE HINTS
------------------
Hint 1: If both nodes are nil, that's a match at this position. If exactly
        one is nil, that's an instant mismatch.
Hint 2: Otherwise compare `.Val`, then recurse into (p.Left, q.Left) AND
        (p.Right, q.Right) — both must be true.
Hint 3: `&&` short-circuits, so put the cheapest check first.

COMPLEXITY TARGET
------------------
    Time:  O(min(n, m))
    Space: O(min(h_p, h_q))
================================================================================
*/

type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourIsSameTree is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/007_same_tree
func YourIsSameTree(p, q *TreeNode) bool {
	// YOUR CODE HERE
	return false
}
