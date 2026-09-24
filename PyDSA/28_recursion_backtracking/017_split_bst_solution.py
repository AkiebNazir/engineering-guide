"""
================================================================================
SOLUTION · LeetCode 776 · Split BST                                     [Medium]
https://leetcode.com/problems/split-bst/
================================================================================

THE CORE IDEA
--------------
The BST property does most of the work: if `node.val <= target`, the
node's ENTIRE left subtree is automatically `<= target` too (BST
ordering guarantees it), so only the RIGHT subtree can possibly straddle
the target and needs recursive splitting. Each call returns a PAIR of
tree ROOTS (not numbers, unlike 014) — `(smallerOrEqualRoot,
greaterRoot)` — and only follows ONE path down the tree, never both
children, because the other child is already known to belong entirely
to one side.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. RECURSIVE, ONE-SIDED DESCENT — the version above, following only the
   child that might straddle `target` at each step. O(h) time (a single
   path from root to the eventual "split point"), O(h) space (call
   stack). The version taught here.
2. ITERATIVE, MANUAL POINTER SURGERY — walk down maintaining "the
   attachment point on the small side" and "the attachment point on the
   large side," rewiring `.left`/`.right` pointers directly as you go,
   no recursion. O(h) time, O(1) space. What to write if recursion isn't
   allowed.
3. FULL TRAVERSAL + REBUILD FROM SCRATCH — collect ALL values via an
   in-order traversal, partition them by `target`, then rebuild two
   balanced (or arbitrary-shape) BSTs from each partition. O(n) time,
   O(n) space — priced as far more expensive and NOT preserving the
   original structure (the problem explicitly requires keeping existing
   parent-child relationships intact wherever possible), included only
   to show why it fails the problem's actual requirement.


================================================================================
STEP BY STEP TRACE — splitBST([4,2,6,1,3,5,7], target=2)
================================================================================
Tree:            4
               /   \
              2     6
             / \   / \
            1   3 5   7

    call splitBST(node=4, target=2)
      4 > 2 (target)  -> only LEFT subtree (rooted at 2) can straddle
      call splitBST(node=2, target=2)
        2 <= 2 (target) -> only RIGHT subtree (rooted at 3) can straddle
        call splitBST(node=3, target=2)
          3 > 2 -> only LEFT subtree (None) can straddle
          call splitBST(None, target=2) -> base case, return (None, None)
          node(3).left = greater(None) -> stays None
          return (smaller=None, greater=node(3))
        smaller, greater = (None, node(3))
        node(2).right = smaller = None      [3 goes to the "greater" bucket, detached from 2]
        return (node(2), greater=node(3))   [2 stays, keeping its left child 1 untouched]
      smaller, greater = (node(2), node(3))
      node(4).left = greater = node(3)      [4 keeps 3 as its new left child]
      return (smaller=node(2), node(4))     [4 stays on the "greater" side, keeping 6,5,7 untouched]

Final split: smaller side = 2 -> left child 1  (values {1, 2})
             greater side = 4 -> left child 3, right child 6 -> {5, 7}  (values {3,4,5,6,7})

Notice: nodes 1, 6, 5, 7 were NEVER TOUCHED at all — their original
parent-child relationships survive completely untouched, exactly as the
problem requires ("most of the structure... should remain").


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time   Space          Mutates input?  Note
    ---------------------------------  -----  -------------  ---------------  --------------------------------
    Recursive, one-sided descent      O(h)   O(h) stack     yes (relinks)    only ONE child ever recursed into
    Iterative, manual pointer surgery O(h)   O(1)           yes (relinks)    same idea, no recursion
    Full traversal + rebuild          O(n)   O(n)           no (new trees)   discards original structure — wrong per spec


================================================================================
EDGE CASES
================================================================================
    root value equals target exactly   -> root itself belongs on the
                                "smaller-or-equal" side; only its RIGHT
                                subtree needs checking (the left
                                subtree, and the root itself, are
                                automatically safe).
    target smaller than every node    -> every node ends up on the
                                "greater" side; the "smaller" root
                                returned is `None`.
    target larger than every node      -> every node ends up on the
                                "smaller-or-equal" side; the "greater"
                                root returned is `None`.
    a single-node tree, target equal to it -> `([root], [])`, exercising
                                the base case one level up from the very
                                top call.


================================================================================
COMMON MISTAKES
================================================================================
1. Recursing into BOTH children at every node "to be safe," instead of
   recognizing that only ONE side can ever straddle `target` given the
   BST property — this still produces a correct final split (the
   untouched side's recursive call just returns it unchanged
   immediately), but wastes O(n) work walking subtrees that provably
   need no splitting at all, defeating the O(h) complexity the BST
   property is specifically there to enable.
2. Reattaching the WRONG half after recursing — e.g. when
   `node.val <= target`, setting `node.right = greater` instead of
   `node.right = smaller` — this puts values that belong on the
   "greater" side back underneath a node that's supposed to be on the
   "smaller" side, producing a tree that's no longer a valid BST split.
3. Returning `(node, smaller)` or some other mismatched ordering instead
   of consistently returning `(smallerRoot, greaterRoot)` in that fixed
   order from every call — since the caller destructures the pair by
   POSITION, a single inconsistent return breaks every level above it.
4. Forgetting that `node` itself belongs on ONE specific side depending
   on whether `node.val <= target` or `node.val > target` — treating
   `node` as always needing to be part of whichever recursive call it
   made, rather than as the piece that STAYS attached to whichever half
   its own value places it in.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is this O(h) instead of O(n), unlike most BST-modifying problems
   that touch every node?
A: At every level, one entire child subtree is known — by the BST
   invariant alone — to already be entirely on one side, so the
   recursion only ever descends along a SINGLE path (toward wherever
   `target` would sit), never branching into both children.

Q: Can you do this without recursion?
A: Yes — track two "attachment points" (one for the growing small-side
   tree, one for the growing large-side tree) while walking down with a
   loop, rewiring `.left`/`.right` directly instead of via return values.

Q: How would MERGING two split BSTs back into one work, as the inverse
   operation?
A: Given a "smaller" BST and a "greater" BST where every value in the
   first is less than every value in the second, attach the greater
   tree's root as the rightmost descendant's right child of the smaller
   tree (or vice versa) — itself another one-sided-descent recursion,
   structurally the mirror image of this problem's split.


================================================================================
RELATED PROBLEMS
================================================================================
    Topic 28, 014 House Robber III     — another "return a pair per
                                        node" recursion, there returning
                                        two numbers instead of two tree
                                        roots.
    Topic 11 Binary Search Tree (topic-level) — general BST insertion/
                                        deletion, which share the "only
                                        one side can possibly need
                                        touching" reasoning.
    LC 1038 Binary Search Tree to Greater Sum Tree — another BST
                                        problem that exploits ordering
                                        to avoid full traversal cost.
================================================================================
"""

from typing import List, Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def splitBST(self, root: Optional[TreeNode], target: int) -> List[Optional[TreeNode]]:
        """Recursive, one-sided descent. O(h) time/space."""
        smaller, greater = self._split(root, target)
        return [smaller, greater]

    def _split(self, node: Optional[TreeNode], target: int) -> Tuple[Optional[TreeNode], Optional[TreeNode]]:
        if node is None:
            return None, None
        if node.val <= target:
            smaller, greater = self._split(node.right, target)
            node.right = smaller
            return node, greater
        else:
            smaller, greater = self._split(node.left, target)
            node.left = greater
            return smaller, node


# ==============================================================================
# TESTS — run:  python 017_split_bst_solution.py
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


def inorder_values(node):
    if node is None:
        return []
    return inorder_values(node.left) + [node.val] + inorder_values(node.right)


def is_valid_bst(node, lo=float("-inf"), hi=float("inf")):
    if node is None:
        return True
    if not (lo < node.val < hi):
        return False
    return is_valid_bst(node.left, lo, node.val) and is_valid_bst(node.right, node.val, hi)


CASES = [
    ([4, 2, 6, 1, 3, 5, 7], 2, [1, 2], [3, 4, 5, 6, 7]),
    ([1], 1, [1], []),
    ([1], 0, [], [1]),
    ([4, 2, 6, 1, 3, 5, 7], 10, [1, 2, 3, 4, 5, 6, 7], []),
    ([4, 2, 6, 1, 3, 5, 7], -1, [], [1, 2, 3, 4, 5, 6, 7]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    for values, target, expected_small, expected_large in CASES:
        root = build(values)
        small_root, large_root = sol.splitBST(root, target)
        small_vals = sorted(inorder_values(small_root))
        large_vals = sorted(inorder_values(large_root))
        ok = (small_vals == expected_small and large_vals == expected_large
              and is_valid_bst(small_root) and is_valid_bst(large_root))
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  splitBST({values}, target={target}) -> "
              f"small={small_vals} large={large_vals}")

    print("\n--- confirming untouched subtrees keep their exact original node identity ---")
    root = build([4, 2, 6, 1, 3, 5, 7])
    node6 = root.right  # the subtree rooted at 6 should never be touched for target=2
    small_root, large_root = sol.splitBST(root, 2)
    untouched = large_root.right is node6 and node6.left.val == 5 and node6.right.val == 7
    all_ok &= untouched
    print(f"  {'PASS' if untouched else 'FAIL'}  subtree rooted at 6 kept its original object identity")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
