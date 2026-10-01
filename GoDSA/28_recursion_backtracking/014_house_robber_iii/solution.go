package main

import "fmt"

/*
================================================================================
LeetCode 337 · House Robber III                                         [Medium]
https://leetcode.com/problems/house-robber-iii/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
The thief has found a new place for his thievery again. There is only
one entrance to this area, called root.

Besides the root, each house has one and only one parent house. After a
tour, the smart thief realized that all houses in this place form a
binary tree. It will automatically contact the police if two directly-
linked houses were broken into on the same night.

Given the root of the binary tree, return the maximum amount of money
the thief can rob without alerting the police.

EXAMPLES
--------
Example 1:
    Input:  root = [3,2,3,null,3,null,1]
    Output: 7
    Explanation: Rob houses 3 (root), 3, and 1: 3 + 3 + 1 = 7.

Example 2:
    Input:  root = [3,4,5,1,3,null,1]
    Output: 9
    Explanation: Rob houses 4 and 5: 4 + 5 = 9.

CONSTRAINTS
-----------
    The number of nodes in the tree is in the range [1, 10^4].
    0 <= Node.val <= 10^4

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The naive recursion — "return max(rob this node + skip both children,
skip this node + best of children)" — RE-EXPLORES each child's subtree
twice (once assuming the child is robbed, once assuming it isn't),
causing exponential blowup, exactly like naive Fibonacci and 011's
unmemoized BST count. The fix here is the "return a pair" combine
pattern: instead of returning ONE number ("best answer for this
subtree"), each call returns TWO numbers — `(bestIfRobbed, bestIfNotRobbed)`
— so a PARENT can combine BOTH of a child's answers without needing to
recompute either one.

    dfs(node) -> (robbed, notRobbed):
        if node is None: return (0, 0)                     <- base case
        leftRobbed, leftNotRobbed = dfs(node.left)
        rightRobbed, rightNotRobbed = dfs(node.right)
        robbed = node.val + leftNotRobbed + rightNotRobbed   <- rob HERE -> children can't be robbed
        notRobbed = max(leftRobbed, leftNotRobbed) + max(rightRobbed, rightNotRobbed)  <- skip HERE -> children free to choose either
        return (robbed, notRobbed)

WHAT TO THINK ABOUT
--------------------
1. If you rob the CURRENT node, what are you forced to assume about
   both of its children? What are you free to assume if you DON'T rob
   the current node?
2. Why does returning a PAIR avoid the exponential blowup that a naive
   single-value version would hit? (Each child subtree is visited
   EXACTLY ONCE, producing both answers it could ever be asked for, so
   no re-exploration is needed.)
3. What does the top-level caller do with the final pair returned from
   the root? (Take `max()` of the two — the thief is free to rob the
   root or not.)
4. This is structurally the SAME decision (rob/skip with a "can't rob
   two adjacent" constraint) as the classic linear House Robber (LC
   198) — what's different about doing it on a tree instead of an
   array, mechanically?

PROGRESSIVE HINTS
------------------
Hint 1: Design a helper that returns a PAIR of numbers for the subtree
        rooted at `node`: the best total if this node IS robbed, and the
        best total if it is NOT.
Hint 2: Base case: `node is None` -> `(0, 0)`.
Hint 3: If robbing `node`: `node.val + leftNotRobbed + rightNotRobbed`
        (children must be skipped). If not robbing `node`: each child is
        free to be robbed or not, so take `max(leftRobbed,
        leftNotRobbed) + max(rightRobbed, rightNotRobbed)`.
Hint 4: The public method's final answer is `max(dfs(root))`.

COMPLEXITY TARGET
------------------
    Naive (no pair, re-explores subtrees): exponential in tree height
    Pair-returning recursion:              O(n) time, O(h) space (call
                                            stack, h = tree height)
================================================================================
*/

func main() {
	fmt.Println("Solution for House Robber III not implemented yet")
}
