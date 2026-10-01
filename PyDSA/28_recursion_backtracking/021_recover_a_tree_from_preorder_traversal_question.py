r"""
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
"""

from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right

    def __eq__(self, other):
        if other is None:
            return False
        return (
            self.val == other.val
            and self.left == other.left
            and self.right == other.right
        )

    def __repr__(self):
        return f"TreeNode({self.val})"


def build_tree(rows):
    """Level-order (LeetCode-style, with None gaps) -> TreeNode, for test data."""
    if not rows:
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
    def recoverFromPreorder(self, traversal: str) -> Optional[TreeNode]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 021_recover_a_tree_from_preorder_traversal_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ("1-2--3--4-5--6--7", [1, 2, 5, 3, 4, 6, 7]),
        ("1-2--3---4-5--6---7", [1, 2, 5, 3, None, 6, None, 4, None, 7, None]),
        ("1", [1]),
        ("1-401--349---90", [1, 401, None, 349, None, 90, None]),
    ]
    passed = 0
    for traversal, expected_rows in cases:
        expected = build_tree(expected_rows)
        got = sol.recoverFromPreorder(traversal)
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  recoverFromPreorder({traversal!r})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
