package main

/*
================================================================================
LeetCode 236 · Lowest Common Ancestor of a Binary Tree                 [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given a binary tree, find the lowest common ancestor (LCA) of two given nodes
p and q.

The LCA is defined as the lowest node in the tree that has both p and q as
descendants (where a node is allowed to be a descendant of itself).


EXAMPLES
--------
Example 1:
    Input:  root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 1
    Output: 3
    Explanation: The LCA of 5 and 1 is 3.

Example 2:
    Input:  root = [3,5,1,6,2,0,8,null,null,7,4], p = 5, q = 4
    Output: 5
    Explanation: The LCA of 5 and 4 is 5, since a node can be a descendant of
    itself per the LCA definition.

Example 3:
    Input:  root = [1,2], p = 1, q = 2
    Output: 1


CONSTRAINTS
-----------
    The number of nodes is in the range [2, 10^5].
    -10^9 <= Node.Val <= 10^9
    All Node.Val are unique.
    p != q
    p and q both exist in the tree.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a general binary tree — no ordering guarantee, so you cannot compare
values to decide which side to search (that shortcut is BST-only, topic 11).
The general solution searches BOTH subtrees at every node and looks at what
comes back: if p and q were found on DIFFERENT sides, the current node is
where their paths split — the LCA.


WHAT TO THINK ABOUT (Go specifically)
-------------------------------------
1. Pointer identity: `node == p` compares addresses, exactly like Python's
   `is`. This is cheap and correct here — you're never comparing by value.

2. This is a bottom-up (postorder) problem: the answer at a node depends on
   what its children report back, so information flows UP via return values
   — the opposite of problem 015 (Count Good Nodes), where ancestor state
   had to flow DOWN as a parameter.

3. The return value is deliberately OVERLOADED — nil means "neither found
   here", p-or-q means "exactly one found, and this IS it", anything else
   means "the LCA has already been decided inside this subtree, just keep
   passing it up unchanged." Three meanings, one `*TreeNode` return type —
   no algebraic sum type needed, Go leans on nil + pointer identity to carry
   all three cases.


PROGRESSIVE HINTS
-----------------
Hint 1: Base case: if the current node IS p, IS q, or is nil, return it
        immediately without recursing further — this implements "a node can
        be its own ancestor."

Hint 2: Recurse into both children. If BOTH sides return non-nil, the
        current node is the split point — the LCA.

Hint 3: If only one side returns non-nil, pass that result straight up
        unchanged — it might already be the final answer, or just "found p"
        /"found q" waiting for the other one.


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

// YourLowestCommonAncestor is your attempt.
// Implement it, then run:
//
//	cd GoDSA && go run ./10_trees/017_lowest_common_ancestor_of_a_binary_tree
func YourLowestCommonAncestor(root, p, q *TreeNode) *TreeNode {
	// YOUR CODE HERE
	return nil
}
