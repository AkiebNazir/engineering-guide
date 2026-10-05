r"""
================================================================================
SOLUTION · LeetCode 1123 · LCA of Deepest Leaves                        [Medium]
https://leetcode.com/problems/lowest-common-ancestor-of-deepest-leaves/
================================================================================

THE CORE IDEA
--------------
Each call returns a PAIR of two DIFFERENT KINDS of information: a depth
(a number) and a candidate LCA (a node reference) — the depth lets a
parent decide which side is deeper; the node is the actual answer to
report. When both children report EQUAL depth, the current node is
exactly the deepest point still containing both sides' leaves, so it
becomes the (possibly provisional) answer. When depths differ, the
deeper side's own answer is passed straight up UNCHANGED — the
shallower side's leaves are provably not among the tree's overall
deepest leaves, so nothing from that side can be part of the true LCA.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, ONE PASS, (depth, lca) PAIR — the version above. O(n)
   time (every node visited exactly once), O(h) space (call stack).
   The version taught here.
2. TWO PASSES — first compute the tree's maximum depth with a plain DFS,
   then do a second DFS that recurses only while both children could
   still reach that maximum depth, returning the deepest node where the
   recursion "forks." O(n) time (two full-ish passes), O(h) space, but
   conceptually two separate ideas glued together instead of one clean
   pass.
3. BFS + PARENT POINTERS — level-order traverse to find the deepest
   level's nodes, then walk up parent pointers from all of them
   simultaneously until they converge on one common ancestor. O(n)
   time, O(n) space for parent pointers and the queue — a much more
   mechanical approach, useful mainly to contrast with how directly the
   pair-returning recursion reaches the same answer.


================================================================================
STEP BY STEP TRACE — lcaDeepestLeaves([3,5,1,6,2,0,8,null,null,7,4])
================================================================================
Tree:                    3
                       /     \
                      5       1
                     / \     / \
                    6   2   0   8
                       / \
                      7   4

    call dfs(3)
      call dfs(5)
        call dfs(6) -> (0,None) both children null -> depth=0+1=1, lca=node(6)
        call dfs(2)
          call dfs(7) -> depth=1, lca=node(7)   (leaf, both children null)
          call dfs(4) -> depth=1, lca=node(4)   (leaf, both children null)
          leftDepth=1, rightDepth=1 -> EQUAL -> return (1+1=2, node(2))
        dfs(5): leftDepth=1 (from 6), rightDepth=2 (from 2) -> UNEQUAL, right deeper
          -> propagate right's pair UNCHANGED except depth+1: return (2+1=3, node(2))
      call dfs(1)
        call dfs(0) -> depth=1, lca=node(0)
        call dfs(8) -> depth=1, lca=node(8)
        leftDepth=1, rightDepth=1 -> EQUAL -> return (1+1=2, node(1))
      dfs(3): leftDepth=3 (from 5's branch), rightDepth=2 (from 1's branch) -> UNEQUAL, left deeper
        -> propagate left's pair UNCHANGED except depth+1: return (3+1=4, node(2))

Final answer: node(2) — the LCA propagated all the way from the point
where it was first "decided" (at node 2, where 7 and 4 tied) straight up
through node 5 and node 3 without ever being recomputed, exactly because
the right subtree (rooted at 1) was shallower and got discarded once
its lesser depth was detected.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space          Mutates input?  Note
    ---------------------------------  -----  -------------  ---------------  --------------------------------
    Recursive, one pass, pair return  O(n)   O(h) stack     no               the version taught here
    Two passes (max depth, then LCA)  O(n)   O(h) stack     no               same result, two separate ideas
    BFS + parent pointers              O(n)   O(n)           no               more mechanical, no recursion


================================================================================
EDGE CASES
================================================================================
    a single node        -> that node IS its own deepest leaf and its
                            own LCA; `dfs`'s base case correctly makes
                            both children report `(0, None)`, so the
                            root reports `(1, root)` via the "equal
                            depths" branch.
    a tree with only ONE deepest leaf (no tie) -> the LCA is exactly
                            that leaf itself, and the "equal depths"
                            branch never fires for it directly (its own
                            two null children ARE equal at 0, so it
                            technically ties with itself, correctly
                            becoming its own provisional LCA, which then
                            propagates up unchanged as the deeper side
                            at every ancestor).
    a perfectly balanced tree, all leaves at the same depth -> ties
                            happen all the way up to the root, so the
                            root itself ends up as the LCA — matching
                            the intuitive answer.
    a completely lopsided (skewed) tree -> the "deeper side always
                            wins" branch fires at every single level,
                            propagating the one true deepest leaf's
                            trivial "LCA of itself" answer all the way
                            to the root.


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing depths but then returning the WRONG node — e.g. when
   `leftDepth > rightDepth`, returning `node` (the current node) instead
   of `leftLCA` (the deeper child's own already-computed answer) — this
   incorrectly reports an ancestor higher up the tree than the true LCA,
   since the current node might not even be on the path to the deepest
   leaves if the shallower side happens to be the one still visited.
2. Forgetting the `+1` when propagating depth upward in the UNEQUAL
   case — depth must always increase by exactly one level per call
   regardless of whether the current node becomes the new provisional
   LCA or just passes a deeper answer through; omitting it desyncs
   depth comparisons at higher ancestors.
3. Treating `node is None`'s depth as anything other than `0` — using
   `-1` (a seemingly reasonable choice to represent "no leaf here")
   changes what a LEAF's own computed depth becomes and breaks the
   depth-equality comparisons used to decide provisional LCAs
   throughout the whole tree, unless every other formula is
   consistently adjusted to match.
4. Assuming the FIRST node that ever looks like a provisional answer
   (deep in the recursion) is automatically the FINAL answer without
   letting it propagate all the way to the top — only the TOP-LEVEL
   call's returned pair is guaranteed correct; every node along the way
   that briefly "became" the LCA might later be overridden if it turns
   out one side is actually shallower than a sibling further up.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you solve this without recursion?
A: Yes — BFS to find the deepest level's nodes, tracking parent
   pointers along the way, then repeatedly move the shallower branch of
   nodes up toward the root (or intersect ancestor sets) until they
   converge on a single common node.

Q: Why does this problem need to track BOTH depth and a node reference,
   when 011/012 only ever needed one kind of information (a count or a
   built structure)?
A: Because deciding "which side wins" (deeper) and "what to actually
   report" (the LCA node) are two logically separate questions that
   both depend on recursing into the SAME subtree — bundling them into
   one pair avoids doing two separate traversals to answer each
   question independently.

Q: How would this generalize to finding the LCA of a GIVEN SET of nodes
   (not necessarily the deepest leaves)?
A: That's the classic LCA problem (e.g. LC 236) — same "return
   information from both children, combine at the current node" shape,
   but the combine rule checks whether the TARGET nodes were found in
   each subtree instead of comparing depths.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 236  Lowest Common Ancestor of a Binary Tree — the more general
                                       LCA-of-a-given-set problem this
                                       one specializes.
    Topic 28, 014 House Robber III / 018 Distribute Coins in Binary Tree
                                     — other "return derived information
                                       per subtree" recursions, each
                                       combining differently at the
                                       parent.
    Topic 10 Binary Trees (topic-level, Maximum Depth of Binary Tree)
                                     — the plain depth computation this
                                       problem's depth half is built on.
================================================================================
"""

from typing import Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def lcaDeepestLeaves(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """Recursive, one pass, (depth, lca) pair. O(n) time, O(h) space."""
        return self._dfs(root)[1]

    def _dfs(self, node: Optional[TreeNode]) -> Tuple[int, Optional[TreeNode]]:
        if node is None:
            return 0, None
        left_depth, left_lca = self._dfs(node.left)
        right_depth, right_lca = self._dfs(node.right)
        if left_depth == right_depth:
            return left_depth + 1, node
        if left_depth > right_depth:
            return left_depth + 1, left_lca
        return right_depth + 1, right_lca


# ==============================================================================
# TESTS — run:  python 019_lowest_common_ancestor_of_deepest_leaves_solution.py
# ==============================================================================
def build(values):
    if not values or values[0] is None:
        return None
    nodes = [TreeNode(v) if v is not None else None for v in values]
    kids = iter(nodes[1:])
    for node in nodes:
        if node is None:
            continue
        node.left = next(kids, None)
        node.right = next(kids, None)
    return nodes[0]


CASES = [
    ([3, 5, 1, 6, 2, 0, 8, None, None, 7, 4], 2),
    ([1], 1),
    ([0, 1, 3, None, 2], 2),
    ([1, 2, 3, 4, 5, 6, 7], 1),  # perfectly balanced -> root is the LCA
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    for values, expected_val in CASES:
        root = build(values)
        result = sol.lcaDeepestLeaves(root)
        got = result.val if result else None
        ok = got == expected_val
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  lcaDeepestLeaves({values}) -> {got}  (want {expected_val})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
