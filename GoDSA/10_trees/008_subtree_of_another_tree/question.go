package main

/*
================================================================================
LeetCode 572 · Subtree of Another Tree                                   [Easy]
https://leetcode.com/problems/subtree-of-another-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given the roots of two binary trees `root` and `subRoot`, return true if
there is a subtree of `root` with the same structure and node values as
`subRoot`. A subtree of `root` is a node PLUS ALL of that node's
descendants.

EXAMPLES
--------
Example 1:
    Input:  root = [3,4,5,1,2], subRoot = [4,1,2]
    Output: true

Example 2:
    Input:  root = [3,4,5,1,2,null,null,null,null,0], subRoot = [4,1,2]
    Output: false

CONSTRAINTS
-----------
    Number of nodes in root:    [1, 2000]
    Number of nodes in subRoot: [1, 1000]
    -10^4 <= Node.Val <= 10^4

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Subtree" means a node together with ALL its descendants — so the question
isn't "does this pattern appear somewhere," it's "is there a node of `root`
from which the two trees are IDENTICAL." That's problem 007 (Same Tree)
called at every node of `root`:

    func isSubtree(root, subRoot *TreeNode) bool {
        if root == nil { return subRoot == nil }
        if isSameTree(root, subRoot) { return true }
        return isSubtree(root.Left, subRoot) || isSubtree(root.Right, subRoot)
    }

This is COMPOSITION — recognizing you already solved the hard half in 007.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. Reuse `isSameTree`'s exact shape from 007 as a helper; don't reinvent it.
2. The alternative approach — serialize both trees to strings with null
   markers and search for one inside the other — needs `strings.Builder`
   (topic 1's idiom) to avoid O(n^2) string concatenation, and needs BOTH a
   null marker AND a delimiter before every value, or the encoding is not
   injective (two different trees can produce the same string).
3. `strings.Contains` in Go is a real linear-time (Rabin-Karp-ish/optimized)
   substring search in the standard library — unlike relying on a naive
   nested loop, it's a legitimate O(n+m)-ish tool to reach for here.

PROGRESSIVE HINTS
------------------
Hint 1: You already know how to check "are these two trees identical" (007).
Hint 2: Call that check at EVERY node of `root` — the first success wins.
Hint 3: For O(n+m) instead of O(n*m): encode both trees as strings with
        null markers AND delimiters, then check if one string contains
        the other.

COMPLEXITY TARGET
------------------
    Time:  O(n * m) with the composition approach; O(n + m) with encoding
    Space: O(h)
================================================================================
*/

type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourIsSubtree is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/008_subtree_of_another_tree
func YourIsSubtree(root, subRoot *TreeNode) bool {
	// YOUR CODE HERE
	return false
}
