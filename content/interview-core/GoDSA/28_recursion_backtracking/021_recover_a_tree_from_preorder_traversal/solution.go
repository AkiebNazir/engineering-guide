package main

import "fmt"

/*
================================================================================
LeetCode 1028 · Recover a Tree From Preorder Traversal                   [Hard]
https://leetcode.com/problems/recover-a-tree-from-preorder-traversal/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
We run a preorder depth-first search on a binary tree, and at each node we
append to a string a number of dashes equal to the node's depth, followed by
the value of that node. If the depth of a node is `D`, the depth of its
immediate child is `D + 1`. The depth of the root node is 0.

Given the string `traversal` produced this way, recover the original tree and
return its root.

EXAMPLES
--------
Example 1:
    Input:  traversal = "1-2--3--4-5--6--7"
    Output: root of the tree
              1
             / \
            2   5
           / \  / \
          3  4 6  7

Example 2:
    Input:  traversal = "1-2--3---4-5--6---7"
    Output: root of a tree where 3's child is 4 (depth 3), and 6's child is 7
            (depth 3), i.e. deeper than example 1.

CONSTRAINTS
-----------
    The number of nodes is in [1, 1000].
    1 <= Node.val <= 10^9

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a PARSE-then-BUILD problem: the string encodes depth as a run-length of
dashes immediately before each number. Two operations, glued together:

1. TOKENIZE: walk the string once, splitting it into (depth, value) pairs.
   Depth = count of consecutive dashes right before the number.
2. RECONSTRUCT: the tree is a preorder sequence, so the FIRST child seen after
   a node at depth D that itself has depth D+1 is that node's LEFT child; the
   SECOND such child (if any) is its RIGHT child. A node at depth <= D seen
   later means we've popped back up — that node belongs to some ancestor, not
   to the node we were just building.

The key data structure is a STACK OF ANCESTORS BY DEPTH: `stack[i]` holds the
node currently sitting at depth `i`. When a new (depth, value) token arrives:
  - pop the stack down to size == depth (those nodes are "closed" — nothing
    else will attach under them at a shallower level than this token)
  - the new node's parent is `stack[-1]` (top of what remains)
  - attach as `.left` if the parent has no left child yet, else `.right`
    (preorder guarantees left is discovered before right)
  - push the new node onto the stack at its own depth

WHAT TO THINK ABOUT
--------------------
1. How do you tell "how many dashes" apart from "what is the number" in one
   scan, given values can be multi-digit and dashes only ever appear as a
   contiguous run immediately before a number (never inside one)?
2. Why does popping the stack down to exactly `depth` entries, then reading
   `stack[-1]`, always give the correct parent — never a grandparent, never a
   sibling?
3. Why is `.left` the correct slot the FIRST time a node acquires a child at
   depth+1, and `.right` the correct slot the SECOND time?
4. Could you solve this recursively instead of with an explicit stack, by
   having a helper that consumes tokens as it goes and returns as soon as it
   sees a depth it doesn't own? What state would it need to carry between
   sibling calls?

PROGRESSIVE HINTS
------------------
Hint 1: Tokenize first, independently of tree-building: produce a list of
        `(depth, value)` in traversal order.
Hint 2: Use a list `stack` where `stack[d]` is the node currently at depth d.
        For each token, `del stack[depth:]` truncates back to that depth.
Hint 3: `parent = stack[-1]` after truncating (or the root if the stack is
        now empty, i.e. depth == 0). Attach left-first, then right.
Hint 4: Always `stack.append(node)` after attaching — this token's node is
        now the "current owner" of its own depth for whatever comes next.

COMPLEXITY TARGET
------------------
    O(n) time (single pass to tokenize, single pass to build, n = len(traversal))
    O(depth) space for the stack, worst case O(n) for a degenerate single-branch
    tree encoded with a very long string.
================================================================================
*/

func main() {
	fmt.Println("Solution for Recover a Tree From Preorder Traversal not implemented yet")
}
