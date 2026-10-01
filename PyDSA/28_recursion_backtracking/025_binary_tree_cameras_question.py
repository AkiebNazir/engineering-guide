"""
================================================================================
LeetCode 968 · Binary Tree Cameras                                       [Hard]
https://leetcode.com/problems/binary-tree-cameras/
Topic: 28 · Recursion Mastery
================================================================================
PROBLEM
-------
You are given the root of a binary tree. We install cameras on tree nodes,
where each camera at a node can monitor its parent, itself, and its
immediate children.

Return the minimum number of cameras needed to monitor all nodes of the
tree.

EXAMPLES
--------
Example 1:
    Input:  root = [0,0,null,0,0]
    Output: 1
    Explanation: one camera on the middle node covers itself, its parent, and
    both of its children.

Example 2:
    Input:  root = [0,0,null,0,null,0,null,null,0]
    Output: 2

CONSTRAINTS
-----------
    The number of nodes is in [1, 1000].
    Node.val == 0
    (Node values are irrelevant to the problem — every node is a candidate
    camera location, and the tree's SHAPE is the only thing that matters.)

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is a GREEDY POST-ORDER problem disguised as an optimization problem. The
key insight: cameras should be placed as deep as possible (near the leaves),
never one level higher than necessary, because a camera one level up only
ever covers the SAME node-count-or-fewer at strictly greater cost of also
needing to cover everything above it separately.

Formalize with a POST-ORDER traversal returning one of three STATES for each
subtree root:

    0 = NOT COVERED  — this node is not monitored by any camera yet
    1 = COVERED, NO CAMERA HERE — a child has a camera that covers this node
    2 = HAS CAMERA — this node itself holds a camera

The decision at each node, built from its children's states (already
computed, post-order):
    - If EITHER child is state 0 (not covered) -> this node MUST place a
      camera right now (greedily, before returning up) to cover that child;
      return state 2, and increment the camera count.
    - Else if EITHER child is state 2 (has a camera) -> this node is covered
      by that child's camera; return state 1 (covered, no camera needed
      here).
    - Else (both children are state 1, or this is a leaf with no children at
      all) -> this node is NOT YET covered; return state 0, deferring the
      decision to the PARENT (a leaf always starts at state 0 — placing a
      camera at every leaf would be wasteful, since leaves get covered by
      their parent placing one camera that covers both leaf children AND
      itself AND its own parent).

Finally, after the traversal finishes at the ROOT: if the root itself ends
up in state 0 (nothing above it to place a camera, so no parent will ever
rescue it), one FINAL camera must be added for the root.

WHAT TO THINK ABOUT
--------------------
1. Why must a LEAF start at state 0 (not covered) rather than immediately
   getting a camera — what would go wrong (in terms of camera count) if
   every leaf got its own camera?
2. Why does "if either child is 0, place a camera here" have to be checked
   BEFORE "if either child is 2, I'm covered" — what breaks if the order is
   reversed?
3. Why is a single post-order pass with this greedy rule guaranteed OPTIMAL,
   not just a reasonable heuristic — what's the argument that pushing
   cameras as low as possible never costs more than placing them higher?
4. Why does the root need special-case handling after the traversal ends,
   when no other node does?

PROGRESSIVE HINTS
------------------
Hint 1: Define states 0 (not covered), 1 (covered, no camera), 2 (has
        camera). Post-order: compute both children's states before deciding
        this node's state.
Hint 2: `None` children (missing left/right) should be treated as state 1
        (covered, no camera) — a missing child needs no camera and imposes
        no obligation on its parent, so it must NOT be treated as state 0.
Hint 3: Priority order at each node: (a) either child is 0 -> place camera,
        return 2; (b) else either child is 2 -> return 1; (c) else -> return 0.
Hint 4: After the full traversal, if `dfs(root) == 0`, add one more camera
        for the root itself (there's no parent left to place one for it).

COMPLEXITY TARGET
------------------
    O(n) time, O(h) space (recursion stack, h = tree height) — every node
    visited exactly once, O(1) work per node.
================================================================================
"""

from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def build_tree(rows: List[Optional[int]]) -> Optional[TreeNode]:
    """Level-order (LeetCode-style, with None gaps) -> TreeNode."""
    if not rows or rows[0] is None:
        return None
    it = iter(rows)
    root = TreeNode(next(it))
    queue = [root]
    while queue:
        node = queue.pop(0)
        try:
            lv = next(it)
        except StopIteration:
            break
        if lv is not None:
            node.left = TreeNode(lv)
            queue.append(node.left)
        try:
            rv = next(it)
        except StopIteration:
            break
        if rv is not None:
            node.right = TreeNode(rv)
            queue.append(node.right)
    return root


class Solution:
    def minCameraCover(self, root: Optional[TreeNode]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 025_binary_tree_cameras_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([0, 0, None, 0, 0], 1),
        ([0, 0, None, 0, None, 0, None, None, 0], 2),
        ([0], 1),
        ([0, 0], 1),
        ([0, None, 0, None, 0, None, 0], 2),  # right-skewed chain of 4
    ]
    passed = 0
    for rows, expected in cases:
        root = build_tree(rows)
        got = sol.minCameraCover(root)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  minCameraCover({rows}) -> {got}  (want {expected})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
