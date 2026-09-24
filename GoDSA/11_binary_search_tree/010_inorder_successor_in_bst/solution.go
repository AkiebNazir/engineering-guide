package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 285 · Inorder Successor in BST                     [Medium]
https://leetcode.com/problems/inorder-successor-in-bst/
================================================================================

PROBLEM
-------
Given the `root` of a binary search tree and a node `p` in it, return the
in-order successor of that node in the BST. If the given node has no
in-order successor in the tree, return `null`.

The successor of a node `p` is the node with the smallest key GREATER THAN
`p.val`.


EXAMPLES
--------
Example 1:
    Input:  root = [2,1,3], p = 1
    Output: 2
    Explanation: 1's in-order successor node is 2. Note that both p and the
    return value is of TreeNode type.

              2
            ╱   ╲
          1       3

Example 2:
    Input:  root = [5,3,6,2,4,null,null,1], p = 6
    Output: null
    Explanation: There is no in-order successor of the current node, so the
    answer is null.

                5
              ╱   ╲
            3       6
          ╱   ╲
        2       4
      ╱
    1


CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 10^4].
    -10^5 <= Node.val <= 10^5
    All Nodes will have unique values.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"In-order successor" means: the next value you'd visit AFTER `p` during an
in-order walk. Problem 007's in-order-with-early-exit could answer this by
walking from the start and stopping one step past `p` — but that's O(n) in
the worst case (if `p` is near the end) and ignores the one fact that makes
this problem interesting: a BST lets you find the successor with a single
O(h) descent, no traversal needed at all.

Two cases, driven purely by comparison against `p.val` (you never even need
to find `p`'s tree position first):

  Case A: `p` HAS a right child. The successor is the SMALLEST value in
          that right subtree — walk `right`, then `left` all the way down.

              5                    p=3: right child is 4, and 4 has no
            ╱   ╲                  left child, so successor = 4.
          3       8
            ╲
              4

  Case B: `p` has NO right child. The successor is the closest ANCESTOR
          for which `p` is in the LEFT subtree — i.e., walk down from the
          root comparing against `p.val`, and remember the last node where
          you turned LEFT (went into a left subtree because the current
          node's value was bigger than `p.val`). That remembered node is
          the answer; if you never turn left, there is no successor.

              5                    p=8: no right child. Walking from root:
            ╱   ╲                  at 5, 8 > 5, go right (no left turn
          3       8                remembered). At 8, target found, no
                                   further descent. No left turn was ever
                                   recorded -> successor = null (8 is the
                                   max value in this tree).

This mirrors problem 005's LCA: pure comparison descent from the root,
O(h) time, no separate step to "find p first."


PROGRESSIVE HINTS
------------------
Hint 1: You are given `p` as a node with a `.val`, and you're also given
        `root`. You do NOT need a separate search to locate `p` in the
        tree before starting — the comparison descent IS the search.

Hint 2: If `p.right` exists, the answer never requires touching `root` at
        all — it's purely "leftmost node in `p.right`'s subtree."

Hint 3: If `p.right` is None, descend from `root` comparing each node's
        value to `p.val`. Every time the current node's value is GREATER
        than `p.val`, that node is a CANDIDATE successor — remember it and
        go left (there might be an even closer one). Every time it's
        smaller or equal, go right (the answer, if any, is further right).

Hint 4: The two cases can be written as one unified loop if you like (many
        solutions do), or kept as two clean branches — try both and see
        which reads clearer to you.


COMPLEXITY TARGET
------------------
    Time:  O(h) — at most one descent, no traversal of the whole tree
    Space: O(1) iterative
================================================================================
*/

func main() {
	fmt.Println("Solution for Inorder Successor in BST not implemented yet")
}
