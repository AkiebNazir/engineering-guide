package main

/*
================================================================================
LeetCode 543 · Diameter of Binary Tree                                   [Easy]
https://leetcode.com/problems/diameter-of-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the root of a binary tree, return the length of the diameter: the
length (number of EDGES) of the longest path between any two nodes. This
path may or may not pass through the root.

EXAMPLES
--------
Example 1:
    Input:  root = [1,2,3,4,5]
    Output: 3
    Explanation: the path [4,2,1,3] or [5,2,1,3] has length 3.

Example 2:
    Input:  root = [1,2]
    Output: 1

CONSTRAINTS
-----------
    Number of nodes in [1, 10^4]
    -100 <= Node.Val <= 100

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The trap in the problem statement is "may or may not pass through the
root" — the longest path is not necessarily the one you'd find by only
looking at the root's two subtree heights. It could be entirely nested
inside a subtree, far from the root. So every node needs to ask "what's
the longest path THROUGH ME" (left height + right height), and the answer
is the MAXIMUM of that quantity over every node in the tree — not just the
root.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. This needs TWO things out of one recursive walk: (a) a value to hand
   back up to the parent (height, so the parent can compute ITS OWN
   left+right sum), and (b) a side effect — updating a running maximum
   that isn't naturally "the return value" of any single call. Go's tool
   for "recursion needs a side channel besides its return value" is a
   CLOSURE capturing a variable by reference.
2. `var depth func(*TreeNode) int` must be declared BEFORE being assigned
   the closure literal that calls itself — a Go closure cannot reference
   its own name on the right-hand side of a `:=` in the same statement,
   because the name doesn't exist yet at that point.
3. Because the closure captures the running-max variable by REFERENCE
   (not by value), every recursive call sees and can update the SAME
   variable — this is the direct Go analogue of Python needing `nonlocal`
   to get the same effect, except Go gives it to you for free.

PROGRESSIVE HINTS
------------------
Hint 1: The answer is NOT `1 + max(diameter(Left), diameter(Right))` — that
        under- or over-counts. Diameter through a node is
        height(Left) + height(Right), independent of what "diameter" means
        at the children.
Hint 2: Compute height recursively (postorder), and at every node, check
        whether height(Left) + height(Right) beats a running best.
Hint 3: The running best needs to live OUTSIDE the recursive function's
        return value — a captured closure variable is the idiomatic tool.

COMPLEXITY TARGET
------------------
    Time:  O(n)
    Space: O(h)
================================================================================
*/

type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourDiameterOfBinaryTree is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/010_diameter_of_binary_tree
func YourDiameterOfBinaryTree(root *TreeNode) int {
	// YOUR CODE HERE
	return 0
}
