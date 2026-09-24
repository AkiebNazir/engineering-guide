package main

/*
================================================================================
LeetCode 235 · Lowest Common Ancestor of a Binary Search Tree            [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/
Topic: 11 · Binary Search Tree
================================================================================

PROBLEM
-------
Given the root of a BST and two nodes p and q that both exist in the tree,
return their lowest common ancestor (LCA). Per LeetCode's definition, a node
can be a descendant of itself, so if p is an ancestor of q, p is the answer.

EXAMPLES
--------
Example 1:
    Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8
    Output: 6

Example 2:
    Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 4
    Output: 2
    Explanation: p (2) is an ancestor of q (4), so p itself is the LCA.

CONSTRAINTS
-----------
    Number of nodes in [2, 10^5]
    -10^9 <= Node.Val <= 10^9
    All Node.Val are unique.
    p != q, p and q both exist in the BST.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is LC 236 (topic 10) with one extra fact: the tree is ORDERED. On a
general binary tree you must search both subtrees to find the split point
(O(n)). On a BST you can tell which subtree p and q are BOTH in with a single
comparison against the current node's value, no searching required.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. p and q are passed as *TreeNode (LeetCode compares node identity), but the
   descent only ever reads p.Val and q.Val — never anything about *node*
   identity. Don't overthink it into a search for p or q.
2. Use `<` and `>`, not `<=`/`>=` — the equal case must fall into the "they
   split here, or one of them IS this node" branch.
3. Iterative, O(1) space, is the answer here — no need for recursion or a
   stack.

PROGRESSIVE HINTS
------------------
Hint 1: At the current node, are p.Val and q.Val both smaller? Both bigger?
        Or does one land on each side (or equal the node)?
Hint 2: While they agree on a side, descend that side — a lower ancestor
        still exists. The moment they disagree, you've found the split.
Hint 3: "One of them equals the current node" must also stop the descent,
        not be folded into "less than or equal" — think about why.

COMPLEXITY TARGET
------------------
    Time:  O(h)  (O(log n) balanced, O(n) skewed)
    Space: O(1) iterative
================================================================================
*/

type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourLowestCommonAncestorBST is your attempt.
// Implement it, then run:  cd GoDSA && go run ./11_binary_search_tree/005_lowest_common_ancestor_of_a_binary_search_tree
func YourLowestCommonAncestorBST(root, p, q *TreeNode) *TreeNode {
	// YOUR CODE HERE
	return nil
}
