package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 235 · Lowest Common Ancestor of a BST            [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-a-binary-search-tree/
================================================================================

PROBLEM
-------
Given a binary search tree (BST), find the lowest common ancestor (LCA) node
of two given nodes in the BST.

According to the definition of LCA on Wikipedia: "The lowest common ancestor
is defined between two nodes p and q as the lowest node in T that has both p
and q as descendants (where we allow A NODE TO BE A DESCENDANT OF ITSELF)."


EXAMPLES
--------
Example 1:
    Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 8
    Output: 6

                    6
              ╱          ╲
            2              8
          ╱   ╲          ╱   ╲
        0      4       7      9
              ╱ ╲
             3   5

    Explanation: the LCA of nodes 2 and 8 is 6.

Example 2:
    Input:  root = [6,2,8,0,4,7,9,null,null,3,5], p = 2, q = 4
    Output: 2
    Explanation: the LCA of nodes 2 and 4 is 2, since a node can be a
    descendant of itself according to the LCA definition.

Example 3:
    Input:  root = [2,1], p = 2, q = 1
    Output: 2


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [2, 10^5].
    -10^9 <= Node.val <= 10^9
    All Node.val are UNIQUE.
    p != q
    p and q will exist in the BST.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Do NOT reach for the general binary-tree LCA algorithm (LC 236) here. That
one is a full O(n) post-order traversal, because in a plain tree you have no
way to know which side a value is on without looking. A BST tells you the
side with one comparison — so this is an O(h) descent, and the whole
question is what "lowest" means in terms of comparisons.

Stand at some node and ask where p and q are:

    both p.val and q.val  <  node.val   ->  both are in the LEFT subtree.
                                             This node is an ancestor, but
                                             not the LOWEST one. Go left.
    both p.val and q.val  >  node.val   ->  both in the RIGHT subtree. Go right.
    otherwise (they SPLIT, or one of them
    IS this node)                        ->  STOP. This node is the LCA.

That third case is the insight: the LCA is exactly the first node where the
two search paths diverge — the SPLIT POINT. Above it, the two values agree on
which way to turn; below it they never share a node again. And if one of the
two values equals the current node, that node is the LCA by the "a node is
its own descendant" clause in the definition.


PROGRESSIVE HINTS
------------------
Hint 1: Walk down from the root. At each node, both values being on the SAME
        side tells you the answer is deeper.

Hint 2: You do not need to find p or q at all, and you do not need to
        compare node identities — only the two values against `node.val`.

Hint 3: The loop is `while True` with three cases and no backtracking, so it
        is O(1) space. You never need a stack, a parent map, or a second
        pass.


COMPLEXITY TARGET
------------------
    Time:  O(h)  — compare with O(n) for LC 236 on a plain binary tree
    Space: O(1) iterative, O(h) recursive
================================================================================
*/

func main() {
	fmt.Println("Solution for Lowest Common Ancestor of a Binary Search Tree not implemented yet")
}
