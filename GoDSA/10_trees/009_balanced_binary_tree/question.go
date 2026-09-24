package main

/*
================================================================================
LeetCode 110 · Balanced Binary Tree                                      [Easy]
https://leetcode.com/problems/balanced-binary-tree/
Topic: 10 · Trees
================================================================================

PROBLEM
-------
Given a binary tree, determine if it is height-balanced: for EVERY node,
the heights of its two subtrees differ by no more than 1.

EXAMPLES
--------
Example 1:
    Input:  root = [3,9,20,null,null,15,7]
    Output: true

Example 2:
    Input:  root = [1,2,2,3,3,null,null,4,4]
    Output: false

Example 3:
    Input:  root = []
    Output: true

CONSTRAINTS
-----------
    Number of nodes in [0, 5000]
    -10^4 <= Node.Val <= 10^4

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The naive reading is "compute height(node) for every node and compare the
two sides" — which recomputes height(subtree) from scratch at every node
along the way, height itself being an O(size-of-subtree) walk. That's
O(n) work done O(n) times: O(n^2) overall on a skewed tree. The fix is to
compute height and check balance in the SAME single postorder pass: return
-1 as a sentinel meaning "already unbalanced somewhere below," and let it
propagate up without doing any more work.

WHAT TO THINK ABOUT (Go specifically)
--------------------------------------
1. The "-1 sentinel meaning failure" trick is doing the job a
   `(height int, balanced bool)` pair return or a Python-style `(int, int)`
   tuple would do more explicitly — Go can return multiple values, and
   that's the cleaner idiom (shown as the primary solution); the sentinel
   version is shown too because it's the version people reach for under
   pressure and it's worth knowing both.
2. This is another postorder problem: you cannot know if a node is
   balanced until you know both children's heights.
3. `time.Now()` / `time.Since` are how you'll MEASURE the O(n^2) vs O(n)
   gap live in this file, on a real skewed tree — not just claim it.

PROGRESSIVE HINTS
------------------
Hint 1: What if `height(node)` also told you, in the same pass, whether
        anything below `node` was already unbalanced?
Hint 2: Have the recursive height function return two things: the height,
        and whether the subtree is balanced (or fold both into one int: a
        real height, or -1 meaning "already broken, stop checking").
Hint 3: The instant a child reports "broken," don't bother computing
        anything further for the parent — just propagate the failure up.

COMPLEXITY TARGET
------------------
    Time:  O(n)     (naive: O(n^2))
    Space: O(h)
================================================================================
*/

type TreeNode struct {
	Val         int
	Left, Right *TreeNode
}

// YourIsBalanced is your attempt.
// Implement it, then run:  cd GoDSA && go run ./10_trees/009_balanced_binary_tree
func YourIsBalanced(root *TreeNode) bool {
	// YOUR CODE HERE
	return false
}
