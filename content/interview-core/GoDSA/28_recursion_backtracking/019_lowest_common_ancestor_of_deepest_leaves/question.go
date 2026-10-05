package main

/*
================================================================================
LeetCode 1123 · Lowest Common Ancestor of Deepest Leaves                [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-deepest-leaves/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
Given the root of a binary tree, return the lowest common ancestor of
its deepest leaves.

Recall that:
- The node of a binary tree is a leaf if and only if it has no
  children.
- The depth of the root of the tree is 0. If the depth of a node is d,
  the depth of each of its children is d + 1.
- The lowest common ancestor of a set S of nodes, is the node A with
  the largest depth such that every node in S is in the subtree with
  root A.

EXAMPLES
--------
Example 1:
    Input:  root = [3,5,1,6,2,0,8,null,null,7,4]
    Output: [2,7,4]
    Explanation: The deepest leaves are the nodes with values 7 and 4.
    The lowest common ancestor of these leaves is the node with value 2.

Example 2:
    Input:  root = [1]
    Output: [1]

Example 3:
    Input:  root = [0,1,3,null,2]
    Output: [2]
    Explanation: The deepest leaf, of every leaf in the tree, has depth
    2, and the LCA of a single node is itself.

CONSTRAINTS
-----------
    The number of nodes in the tree will be between 1 and 1000.
    0 <= Node.val <= 1000
    The values of the nodes in the tree are unique.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is 014's "return a pair" pattern taken further: each call must
return BOTH a depth AND a candidate LCA node — two DIFFERENT KINDS of
information (a number, and a node reference) bundled into one pair,
because a parent can't decide which subtree is "deeper" without the
depth, and can't report an answer without the node.

At any node, compare the two children's depths:
- If they're EQUAL, this node itself IS the LCA of the deepest leaves
  in its own subtree (both sides go equally deep, so this is the
  deepest point that still contains all of them).
- If they're UNEQUAL, whichever side is deeper "wins" — that side's
  own reported (depth, LCA) pair is passed straight up unchanged,
  because the shallower side's leaves aren't among the tree's overall
  deepest leaves at all.

    dfs(node) -> (depth, lca):
        if node is None: return (0, None)                  <- base case
        leftDepth, leftLCA = dfs(node.left)
        rightDepth, rightLCA = dfs(node.right)
        if leftDepth == rightDepth:
            return (leftDepth + 1, node)                     <- THIS node is the answer, for now
        elif leftDepth > rightDepth:
            return (leftDepth + 1, leftLCA)                   <- left side's answer propagates up unchanged
        else:
            return (rightDepth + 1, rightLCA)                  <- right side's answer propagates up unchanged

WHAT TO THINK ABOUT
--------------------
1. Why does `leftDepth == rightDepth` mean the CURRENT node is
   (provisionally) the answer, rather than either child?
2. When `leftDepth != rightDepth`, why does the DEEPER side's LCA get
   passed straight through, completely unchanged, rather than being
   recombined with something from the current node?
3. Why is the final answer returned by the TOP-LEVEL call guaranteed to
   be correct, even though many DIFFERENT nodes along the way might
   each have briefly looked like "the answer" during the recursion?
4. What is `dfs(None)`'s depth, and why must it be `0` specifically
   (not `-1` or some other value)? (An empty subtree contributes depth
   0, so a LEAF's own depth-relative-to-itself, via
   `max(leftDepth, rightDepth) + 1`, comes out as exactly 1 — leaves
   are 1 "level" deep from their own perspective in this bookkeeping,
   even though the problem statement defines the ROOT's absolute depth
   as 0; this function tracks RELATIVE depth from each node downward,
   not absolute depth from the root.)

PROGRESSIVE HINTS
------------------
Hint 1: Design a helper returning `(depth, node)` for the subtree
        rooted at the current node — depth relative to THIS node
        (i.e., "how many levels deeper does the deepest leaf under me
        go").
Hint 2: Base case: `node is None` -> `(0, None)`.
Hint 3: Compare `leftDepth` and `rightDepth`. Equal -> this node is the
        provisional LCA, depth is `leftDepth + 1`. Otherwise, propagate
        the DEEPER side's `(depth + 1, lca)` pair up unchanged.
Hint 4: The public method's answer is simply the `lca` half of the
        pair returned by the top-level call on `root`.

COMPLEXITY TARGET
------------------
    Recursive: O(n) time (every node visited once), O(h) space (call
               stack, h = tree height)
================================================================================
*/

// TODO: Implement the stub
