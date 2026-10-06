"""
================================================================================
SOLUTION · LeetCode 105 · Construct Binary Tree from Preorder and Inorder
                          Traversal                                    [Medium]
https://leetcode.com/problems/construct-binary-tree-from-preorder-and-inorder-traversal/
================================================================================

THE CORE IDEA
--------------
Each traversal contributes exactly one fact, and together the two facts are
enough to split the problem:

    preorder = [ROOT] [.... left subtree ....] [.... right subtree ....]
    inorder  = [.... left subtree ....] [ROOT] [.... right subtree ....]

    preorder[0]  ->  WHO the root is.
    root's position k in inorder  ->  HOW MANY nodes are in the left
                                       subtree (exactly k of them).

Knowing the root and the left-subtree SIZE lets you cut both arrays in the
same place and recurse. That is the entire algorithm; everything below is
about not paying O(n) per cut.

    def go(lo, hi):                     # bounds into INORDER
        if lo > hi: return None
        val = preorder[cursor]; cursor += 1
        node = TreeNode(val)
        k = pos[val]                     # O(1): prebuilt {value -> inorder index}
        node.left  = go(lo, k - 1)       # LEFT FIRST — the cursor demands it
        node.right = go(k + 1, hi)
        return node

O(n) time, O(n) space for the index map plus O(h) for the stack.

TWO IDEAS MAKE IT O(n) INSTEAD OF O(n^2):
  1. `pos = {v: i for i, v in enumerate(inorder)}` replaces `inorder.index(v)`
     — O(1) instead of an O(n) scan, per node.
  2. Index BOUNDS `(lo, hi)` replace slices — no copying, so the recursion
     touches O(1) memory per node instead of O(size-of-subtree).

AND ONE SUBTLETY THAT MAKES THE CURSOR LEGAL: preorder lists nodes in exactly
the order this recursion CREATES them (node, then all of the left subtree,
then all of the right subtree). So a single monotonically advancing cursor
into `preorder` is always pointing at the next node to build — no per-subtree
preorder bounds needed at all. This is why the left child must be built
BEFORE the right: swap the two lines and the cursor hands the right subtree
the values that belong to the left. Demonstrated at runtime below.


================================================================================
WHY PREORDER + POSTORDER IS NOT ENOUGH (and inorder + postorder is)
================================================================================
Think about WHERE each traversal puts the root and what that leaves you:

    preorder  : [root]  L  R          root at the FRONT     -> identifies root
    postorder :   L  R  [root]        root at the BACK      -> identifies root
    inorder   :   L  [root]  R        root in the MIDDLE    -> gives the SPLIT

Preorder and postorder BOTH only identify the root. Neither says how the
remainder divides between L and R, so the pair is ambiguous:

    tree A:   1            tree B:   1
                └┐                  ┌┘
                 2                  2

    tree A: preorder [1,2]  postorder [2,1]  inorder [1,2]
    tree B: preorder [1,2]  postorder [2,1]  inorder [2,1]
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^  identical!   ^^^^^^ different

Inorder is the ONLY one of the three that carries the split, which is why
every unambiguous pair must include it:

    preorder + inorder   -> unique tree  (LC 105, this problem)
    inorder  + postorder -> unique tree  (LC 106)
    preorder + postorder -> AMBIGUOUS in general

The ambiguity is exactly the "one-child" case: a node with a single child
looks the same in pre+post whichever side the child is on. Remove that case
and the pair becomes sufficient — which is precisely LC 889's extra
guarantee, a FULL binary tree (every node has 0 or 2 children). The demo
below enumerates every binary tree shape up to 6 nodes and COUNTS the
collisions for each pair, then verifies that pre+post has zero collisions
once restricted to full trees.

Also worth stating: unique values matter. The index map `{value: index}`
assumes values are distinct — the constraints guarantee it. With duplicates,
`pos[val]` (or `inorder.index(val)`) picks one of several positions and the
reconstruction can silently produce a DIFFERENT tree with the same
traversals. Demonstrated below.


================================================================================
MULTIPLE APPROACHES
================================================================================
0. BRUTE FORCE — enumerate all Catalan(n) binary tree shapes, label each by
   the preorder, and keep the one whose inorder matches. Catalan(n) ~ 4^n /
   n^1.5, so this is astronomically bad (Catalan(20) is already 6.5 billion);
   stated only to note that the problem *has* a search-space framing, and to
   make clear how much the recursive split buys. Not coded.

1. RECURSIVE SPLIT WITH SLICING — the natural first solution:

        root.val = preorder[0]
        k = inorder.index(preorder[0])
        root.left  = build(preorder[1:k+1], inorder[:k])
        root.right = build(preorder[k+1:],  inorder[k+1:])

   Correct, and honestly the version to WRITE FIRST in an interview because
   it is transparently right. O(n^2) time and O(n^2) space in the worst case:
   `.index()` is a linear scan and each of the four slices copies. Measured
   below on a left chain: 4x slower than the O(n) version at n = 200, 37x at
   n = 2000, 93x at n = 4000 — still climbing. On a BALANCED tree of 16383
   nodes the same comparison is only ~1.4x, which is why this has to be
   benchmarked on skewed input to be visible at all.

2. INDEX MAP + BOUNDS + SHARED PREORDER CURSOR ✅ — the answer, above. O(n)
   time, O(n) space.

3. INDEX MAP + BOUNDS ON BOTH ARRAYS (no cursor) — pass `(pre_lo, in_lo,
   in_hi)` and compute the right subtree's preorder start as
   `pre_lo + 1 + (k - in_lo)`. Also O(n), no shared mutable cursor, and it
   makes the arithmetic explicit rather than implicit. Some people find this
   easier to trust; it is the same algorithm with the cursor written out by
   hand. Coded below.

4. ITERATIVE, O(n), NO RECURSION — walk `preorder` once with a stack of
   "nodes whose right child is not yet placed", using `inorder` (with its own
   cursor) to decide when to stop going left and start going right. Coded
   below. Worth knowing as the answer to "can you do it without recursion?"
   (n <= 3000 here, so a chain would exceed the default recursion limit
   anyway — this version does not care).


================================================================================
STEP BY STEP TRACE — preorder = [3,9,20,15,7], inorder = [9,3,15,20,7]
================================================================================
    pos = {9:0, 3:1, 15:2, 20:3, 7:4}       (built once, O(n))

    call            cursor  val  k=pos[val]  left bounds  right bounds  builds
    --------------  ------  ---  ----------  -----------  ------------  --------------
    go(0, 4)        0 -> 1  3    1           (0, 0)       (2, 4)        3
      go(0, 0)      1 -> 2  9    0           (0, -1)      (1, 0)        9  (leaf)
        go(0,-1)                                                         None (lo>hi)
        go(1, 0)                                                         None (lo>hi)
      go(2, 4)      2 -> 3  20   3           (2, 2)       (4, 4)        20
        go(2, 2)    3 -> 4  15   2           (2, 1)       (3, 2)        15 (leaf)
        go(4, 4)    4 -> 5  7    4           (4, 3)       (5, 4)        7  (leaf)

    The cursor reads preorder strictly left to right: 3, 9, 20, 15, 7 — the
    same order the nodes are created. That is not a coincidence, it is the
    definition of preorder.

            3                       inorder bounds owned by each node:
          ┌─┴──┐                        3  : [0..4]  (whole array)
          9    20                       9  : [0..0]
             ┌─┴─┐                      20 : [2..4]
            15    7                     15 : [2..2]
                                        7  : [4..4]

    ⚠️ Now build the RIGHT child first instead (same code, two lines
    swapped). The cursor still hands out 3, 9, 20, 15, 7 in order, but now
    the second value goes to the RIGHT subtree:

        go(0,4): val=3, k=1  -> right = go(2,4) FIRST, which takes 9 ...
        ... and 9 has no business being in the right subtree at all.

    Result: a mis-shaped tree whose inorder no longer matches the input.
    Printed live below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time      Space (aux)  Mutates input?  Note
    ------------------------------------  --------  -----------  --------------  -------------------
    Enumerate all shapes, keep the match  O(4^n·n)  O(n)         no              priced, not coded
    Recursive split with slicing          O(n^2)    O(n^2)       no              index() + 4 copies
                                                                                  per node
    Index map + bounds + cursor ✅        O(n)      O(n) + O(h)  no              the answer
    Index map + bounds on both arrays     O(n)      O(n) + O(h)  no              cursor written out
    Iterative with a stack                O(n)      O(n)         no              no recursion at all

    n = number of nodes, h = height. None of these mutates `preorder` or
    `inorder` — the slicing version copies them, the others only read.

    WHERE O(n^2) COMES FROM in the slicing version, both halves independently:
      · `inorder.index(val)` is a linear scan: O(n) per node -> O(n^2).
      · the four slices copy O(size of subtree) per node. On a CHAIN the
        subtree sizes are n, n-1, n-2, ... summing to O(n^2). On a BALANCED
        tree the same sum is O(n log n) — which is why the quadratic
        behaviour only shows up on skewed input. The benchmark below runs
        both shapes to make that visible.

    WHY THE INDEX MAP IS O(n) SPACE AND WHY THAT IS FINE: it is one dict of
    n entries built once, versus O(n^2) total slice copies. Trading O(n)
    space for an O(n) factor of time is the whole move.


================================================================================
EDGE CASES
================================================================================
    n == 1                  -> preorder == inorder == [v]; k == 0, both
                               recursive calls hit lo > hi.
    two nodes, left child    -> pre=[1,2], in=[2,1]
    two nodes, right child   -> pre=[1,2], in=[1,2]
                               THE minimal pair that distinguishes the two
                               shapes, and the pair that pre+post cannot.
    left-only chain           -> pre=[1,2,3,...], in=[...,3,2,1]; h == n, so
                               the recursion depth equals n. n <= 3000 here
                               and the default recursion limit is 1000, so a
                               legal input CAN blow the stack. Demonstrated.
    right-only chain          -> pre == in == [1,2,3,...]; k == 0 every time.
    negative values           -> irrelevant; nothing assumes signs, and the
                               dict handles negatives as keys fine.
    empty input               -> the constraints say n >= 1, but `if lo > hi:
                               return None` handles it anyway; a version that
                               reads `preorder[0]` unguarded raises IndexError.
    DUPLICATE values          -> excluded by the constraints. If they occur,
                               the index map is not well defined and the
                               reconstruction can differ from the original
                               tree while still being *consistent* with the
                               two traversals. Demonstrated below.


================================================================================
COMMON MISTAKES
================================================================================
1. Slicing `preorder[1:k]` instead of `preorder[1:k+1]`. The left subtree has
   k nodes, so its preorder is the k elements AFTER the root: indices 1
   through k inclusive. The off-by-one silently drops the last node of the
   left subtree and shifts everything after it.

2. Using the INORDER index `k` to slice `preorder` without converting it.
   With slices this happens to work because each recursive call re-bases its
   arrays at 0. With BOUNDS it does not: `k` is an absolute index into the
   original `inorder`, and the left subtree's size is `k - lo`, not `k`.
   Mixing the two conventions is the single most common bug in the O(n)
   version.

3. Building the RIGHT child before the LEFT with a shared preorder cursor.
   The cursor is only correct if consumed in preorder order. Python evaluates
   statements top to bottom, so the source order of the two assignments IS
   the consumption order. Demonstrated live.

4. Rebuilding the `{value: index}` map inside the recursion instead of once
   outside it. That reintroduces O(n) work per node — O(n^2) again, now with
   a dict allocation per node on top.

5. `cursor` as a plain integer in the enclosing function without `nonlocal`
   — `cursor += 1` then raises `UnboundLocalError`. Either declare
   `nonlocal cursor`, or use a one-element list, or use `iter(preorder)` and
   `next(it)` (which needs neither, because `next` MUTATES the iterator
   rather than rebinding a name — the same distinction as topic 015's
   mistake 8).

6. Forgetting `if lo > hi: return None` and instead testing `if lo == hi`,
   or testing emptiness of a slice you no longer have. `lo > hi` is the empty
   interval; `lo == hi` is a one-node interval and must still create a node.

7. Assuming preorder + postorder would work the same way. It does not, in
   general — see the section above, and note that LC 889 only works because
   of its full-binary-tree guarantee.

8. Recursing without worrying about depth. n <= 3000 and a chain is a legal
   input, so h can be 3000 against a default limit of 1000. Either say
   "iterative" or say "sys.setrecursionlimit" — but say something.

9. Comparing reconstructed trees by identity or by `==`. `TreeNode` has no
   `__eq__`, so `==` is identity and always False for distinct objects.
   Compare serialisations (level order, or the traversal pair) instead. The
   tests below compare level order.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Same problem from INORDER + POSTORDER (LC 106).
A: Mirror image. `postorder[-1]` is the root, so consume postorder from the
   RIGHT with a descending cursor, and build the RIGHT child FIRST (postorder
   reversed is node, right, left). Getting the order wrong there is the same
   bug as mistake 3, mirrored. Coded below as `buildTree106`.

Q: From PREORDER + POSTORDER (LC 889).
A: Only unambiguous if the tree is FULL (every node has 0 or 2 children),
   which 889 guarantees. Then `preorder[0]` is the root, `preorder[1]` is the
   root of the left subtree, and finding `preorder[1]` in postorder gives the
   left subtree's size. Coded below as `buildTree889`, with the ambiguity of
   the general case demonstrated.

Q: From the LEVEL ORDER plus inorder.
A: Also unique. Harder to implement: you must partition the level-order
   array by membership in each subtree (a set per side) while preserving
   relative order, which is O(n^2) naively or O(n) with a value->side map
   per level.

Q: Do it without recursion.
A: The iterative stack version (approach 4). Also mention that a chain of
   3000 nodes exceeds Python's default recursion limit, so this is a real
   answer, not a stunt.

Q: What if values may repeat?
A: The problem is no longer well posed — several distinct trees can share
   both traversals. If the interviewer insists, you must reconstruct one
   consistent tree, which means backtracking over the candidate positions of
   the root inside inorder (exponential in the worst case). Say that the
   uniqueness constraint is what makes the O(n) map legal.

Q: Preorder of a BST, with no inorder given (LC 1008 / 449).
A: A BST's inorder is its SORTED values, so you can recover inorder for free
   by sorting — O(n log n) — and then apply this algorithm. Better: use the
   BST's value bounds directly and build in O(n) with a single pass, no
   inorder at all. That is topic 11's lesson: the ordering invariant replaces
   one of the two traversals.

Q: Verify your reconstruction.
A: Re-derive both traversals from the built tree and compare with the
   inputs. That is exactly what the randomised round-trip test below does —
   and it is the right answer to "how do you know it is correct?"

Q: How many distinct trees have a given preorder?
A: Catalan(n) — one per shape, since the preorder labels are then forced.
   That is the size of the ambiguity a single traversal leaves, and the demo
   below enumerates it for small n.


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
  CONSTRUCT FROM TRAVERSALS (this pattern):
    LC 105   Preorder + Inorder                — this problem
    LC 106   Inorder + Postorder                — the mirror image
    LC 889   Preorder + Postorder               — needs the FULL-tree guarantee
    LC 1008  Construct BST from Preorder         — BST bounds replace inorder
    LC 108   Sorted Array to BST                 — inorder alone + "make it balanced"
    LC 109   Sorted List to BST                  — 108 over a linked list
    LC 1028  Recover a Tree From Preorder Traversal — preorder + depth prefixes

  SERIALISE / ENCODE (the inverse direction — problem 019 here):
    LC 297   Serialize and Deserialize Binary Tree — preorder + null markers
    LC 449   Serialize and Deserialize BST         — no markers needed
    LC 428   Serialize and Deserialize N-ary Tree

  THE TRAVERSALS THEMSELVES (problems 001-003 here):
    LC 144   Binary Tree Preorder Traversal
    LC 94    Binary Tree Inorder Traversal
    LC 145   Binary Tree Postorder Traversal
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import Dict, List, Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def buildTree(self, preorder: List[int], inorder: List[int]) -> Optional[TreeNode]:
        """Index map + inorder bounds + one shared preorder cursor.
        O(n) time, O(n) space. See THE CORE IDEA above."""
        pos: Dict[int, int] = {v: i for i, v in enumerate(inorder)}
        cursor = 0

        def go(lo: int, hi: int) -> Optional[TreeNode]:
            nonlocal cursor
            if lo > hi:                       # empty interval
                return None
            val = preorder[cursor]
            cursor += 1
            node = TreeNode(val)
            k = pos[val]                       # O(1) split point
            node.left = go(lo, k - 1)          # LEFT FIRST — cursor order
            node.right = go(k + 1, hi)
            return node

        return go(0, len(inorder) - 1)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def buildTree_slicing(self, preorder: List[int],
                          inorder: List[int]) -> Optional[TreeNode]:
        """Approach 1: the transparent O(n^2) version. `.index()` scans and
        every slice copies. Write this first, then optimise."""
        if not preorder:
            return None
        val = preorder[0]
        node = TreeNode(val)
        k = inorder.index(val)                       # O(n) scan
        node.left = self.buildTree_slicing(preorder[1:k + 1], inorder[:k])
        node.right = self.buildTree_slicing(preorder[k + 1:], inorder[k + 1:])
        return node

    def buildTree_bounds_both(self, preorder: List[int],
                              inorder: List[int]) -> Optional[TreeNode]:
        """Approach 3: bounds on BOTH arrays, no shared cursor. The right
        subtree's preorder start is computed explicitly."""
        pos = {v: i for i, v in enumerate(inorder)}

        def go(pre_lo: int, in_lo: int, in_hi: int) -> Optional[TreeNode]:
            if in_lo > in_hi:
                return None
            val = preorder[pre_lo]
            node = TreeNode(val)
            k = pos[val]
            left_size = k - in_lo                     # NOT k — bounds are absolute
            node.left = go(pre_lo + 1, in_lo, k - 1)
            node.right = go(pre_lo + 1 + left_size, k + 1, in_hi)
            return node

        return go(0, 0, len(inorder) - 1)

    def buildTree_iterator(self, preorder: List[int],
                           inorder: List[int]) -> Optional[TreeNode]:
        """Same as the answer, but the cursor is an ITERATOR — `next(it)`
        mutates the iterator rather than rebinding a name, so no `nonlocal`
        is needed (mistake 5)."""
        pos = {v: i for i, v in enumerate(inorder)}
        it = iter(preorder)

        def go(lo: int, hi: int) -> Optional[TreeNode]:
            if lo > hi:
                return None
            val = next(it)
            node = TreeNode(val)
            k = pos[val]
            node.left = go(lo, k - 1)
            node.right = go(k + 1, hi)
            return node

        return go(0, len(inorder) - 1)

    def buildTree_iterative(self, preorder: List[int],
                            inorder: List[int]) -> Optional[TreeNode]:
        """Approach 4: O(n), no recursion. The stack holds nodes whose right
        child is not yet placed; `inorder[j]` says when to stop going left."""
        if not preorder:
            return None
        root = TreeNode(preorder[0])
        stack = [root]
        j = 0                                        # cursor into inorder
        for val in preorder[1:]:
            node = stack[-1]
            if node.val != inorder[j]:
                # still descending left: the current top has an unplaced left
                node.left = TreeNode(val)
                stack.append(node.left)
            else:
                # unwind every node whose subtree is fully inorder-consumed
                while stack and stack[-1].val == inorder[j]:
                    node = stack.pop()
                    j += 1
                node.right = TreeNode(val)
                stack.append(node.right)
        return root

    # ------------------------------------------------------------------
    # The sibling problems (LC 106 / LC 889), for the follow-ups.
    # ------------------------------------------------------------------
    def buildTree106(self, inorder: List[int],
                     postorder: List[int]) -> Optional[TreeNode]:
        """LC 106: inorder + postorder. Mirror image — consume postorder
        from the RIGHT and build the RIGHT child FIRST."""
        pos = {v: i for i, v in enumerate(inorder)}
        cursor = len(postorder) - 1

        def go(lo: int, hi: int) -> Optional[TreeNode]:
            nonlocal cursor
            if lo > hi:
                return None
            val = postorder[cursor]
            cursor -= 1
            node = TreeNode(val)
            k = pos[val]
            node.right = go(k + 1, hi)                # RIGHT FIRST here
            node.left = go(lo, k - 1)
            return node

        return go(0, len(inorder) - 1)

    def buildTree889(self, preorder: List[int],
                     postorder: List[int]) -> Optional[TreeNode]:
        """LC 889: preorder + postorder, valid ONLY for a FULL binary tree
        (every node has 0 or 2 children). `preorder[1]` is the left child's
        root; its position in postorder gives the left subtree's size."""
        pos = {v: i for i, v in enumerate(postorder)}
        cursor = 0

        def go(lo: int, hi: int) -> Optional[TreeNode]:
            """lo..hi are bounds into POSTORDER."""
            nonlocal cursor
            if lo > hi:
                return None
            val = preorder[cursor]
            cursor += 1
            node = TreeNode(val)
            if lo == hi:                               # leaf
                return node
            left_root = preorder[cursor]                # the left child's value
            k = pos[left_root]                          # end of the left subtree
            node.left = go(lo, k)
            node.right = go(k + 1, hi - 1)              # hi is this node itself
            return node

        return go(0, len(postorder) - 1)

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def buildTree_broken_right_first(self, preorder: List[int],
                                     inorder: List[int]) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — right child built before the left, so the
        shared cursor hands out preorder values to the wrong subtree."""
        pos = {v: i for i, v in enumerate(inorder)}
        cursor = 0

        def go(lo, hi):
            nonlocal cursor
            if lo > hi:
                return None
            val = preorder[cursor]
            cursor += 1
            node = TreeNode(val)
            k = pos[val]
            node.right = go(k + 1, hi)                 # WRONG ORDER
            node.left = go(lo, k - 1)
            return node

        return go(0, len(inorder) - 1)

    def buildTree_broken_offbyone(self, preorder: List[int],
                                  inorder: List[int]) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — `preorder[1:k]` instead of
        `preorder[1:k+1]`; the left subtree loses its last node."""
        if not preorder:
            return None
        val = preorder[0]
        node = TreeNode(val)
        k = inorder.index(val)
        node.left = self.buildTree_broken_offbyone(preorder[1:k], inorder[:k])
        node.right = self.buildTree_broken_offbyone(preorder[k + 1:], inorder[k + 1:])
        return node

    def buildTree_broken_relative_k(self, preorder: List[int],
                                    inorder: List[int]) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — mistake 2: uses the ABSOLUTE inorder index
        `k` as the left-subtree SIZE in the bounds version."""
        pos = {v: i for i, v in enumerate(inorder)}

        def go(pre_lo, in_lo, in_hi):
            if in_lo > in_hi:
                return None
            val = preorder[pre_lo]
            node = TreeNode(val)
            k = pos[val]
            node.left = go(pre_lo + 1, in_lo, k - 1)
            node.right = go(pre_lo + 1 + k, k + 1, in_hi)   # k, not k - in_lo
            return node

        return go(0, 0, len(inorder) - 1)


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build(vals: List[Optional[int]]) -> Optional[TreeNode]:
    """Level-order list with `None` for absent children -> root node."""
    if not vals or vals[0] is None:
        return None
    root = TreeNode(vals[0])
    queue = deque([root])
    i = 1
    while queue and i < len(vals):
        node = queue.popleft()
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(vals):
            v = vals[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root: Optional[TreeNode]) -> List[Optional[int]]:
    """Root -> level-order list with `None`s, trailing `None`s trimmed."""
    if root is None:
        return []
    out: List[Optional[int]] = []
    queue = deque([root])
    while queue:
        node = queue.popleft()
        if node is None:
            out.append(None)
            continue
        out.append(node.val)
        queue.append(node.left)
        queue.append(node.right)
    while out and out[-1] is None:
        out.pop()
    return out


def preorder_of(root: Optional[TreeNode]) -> List[int]:
    """Iterative preorder — safe on chains of any depth."""
    out, stack = [], [root] if root is not None else []
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.right is not None:
            stack.append(node.right)
        if node.left is not None:
            stack.append(node.left)
    return out


def inorder_of(root: Optional[TreeNode]) -> List[int]:
    """Iterative inorder — safe on chains of any depth."""
    out, stack, node = [], [], root
    while stack or node is not None:
        while node is not None:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out


def postorder_of(root: Optional[TreeNode]) -> List[int]:
    """Iterative postorder (reverse of a modified preorder)."""
    out, stack = [], [root] if root is not None else []
    while stack:
        node = stack.pop()
        out.append(node.val)
        if node.left is not None:
            stack.append(node.left)
        if node.right is not None:
            stack.append(node.right)
    out.reverse()
    return out


def attempt(fn, *args):
    """Run a (possibly broken) builder and report either its level order or
    the exception it raised. The broken versions below fail in BOTH ways."""
    try:
        return to_level_order(fn(*args))
    except RecursionError:
        return "RecursionError"
    except Exception as exc:  # noqa: BLE001 — the point is to show the failure
        return f"{type(exc).__name__}: {exc}"


def all_shapes(n: int) -> List[Optional[TreeNode]]:
    """Every binary tree shape with n nodes, labelled 0..n-1 in PREORDER.
    Catalan(n) of them."""
    if n == 0:
        return [None]
    trees: List[Optional[TreeNode]] = []
    for left_size in range(n):
        right_size = n - 1 - left_size
        for left in all_shapes(left_size):
            for right in all_shapes(right_size):
                root = TreeNode(0)
                root.left = _relabel(left, 1)
                root.right = _relabel(right, 1 + left_size)
                trees.append(root)
    return trees


def _relabel(root: Optional[TreeNode], start: int) -> Optional[TreeNode]:
    """Deep-copy `root`, renumbering its nodes 0..k-1 -> start..start+k-1."""
    if root is None:
        return None
    return TreeNode(root.val + start,
                    _relabel(root.left, start),
                    _relabel(root.right, start))


def is_full(root: Optional[TreeNode]) -> bool:
    """Every node has 0 or 2 children (LC 889's guarantee)."""
    if root is None:
        return True
    if (root.left is None) != (root.right is None):
        return False
    return is_full(root.left) and is_full(root.right)


def random_tree(n: int, rng: random.Random) -> Optional[TreeNode]:
    """A random binary tree with n distinct values."""
    if n == 0:
        return None
    vals = rng.sample(range(-3000, 3000), n)
    root = TreeNode(vals[0])
    nodes = [root]
    for v in vals[1:]:
        while True:
            parent = rng.choice(nodes)
            if parent.left is None and (parent.right is None or rng.random() < 0.5):
                parent.left = TreeNode(v)
                nodes.append(parent.left)
                break
            if parent.right is None:
                parent.right = TreeNode(v)
                nodes.append(parent.right)
                break
    return root


def chain(n: int, left: bool = True) -> Optional[TreeNode]:
    """A one-sided chain of n nodes (h == n)."""
    if n == 0:
        return None
    root = TreeNode(0)
    cur = root
    for i in range(1, n):
        child = TreeNode(i)
        if left:
            cur.left = child
        else:
            cur.right = child
        cur = child
    return root


def balanced(n_depth: int) -> Optional[TreeNode]:
    """Perfect tree of the given depth, values distinct, built iteratively."""
    if n_depth <= 0:
        return None
    counter = [0]
    root = TreeNode(0)
    frontier = [root]
    for _ in range(n_depth - 1):
        nxt = []
        for node in frontier:
            counter[0] += 1
            node.left = TreeNode(counter[0])
            counter[0] += 1
            node.right = TreeNode(counter[0])
            nxt.append(node.left)
            nxt.append(node.right)
        frontier = nxt
    return root


# ==============================================================================
# TESTS — run:  python 016_construct_binary_tree_from_preorder_and_inorder_traversal_solution.py
# ==============================================================================
CASES = [
    ([3, 9, 20, 15, 7], [9, 3, 15, 20, 7], [3, 9, 20, None, None, 15, 7]),
    ([-1], [-1], [-1]),
    ([1, 2], [2, 1], [1, 2]),
    ([1, 2], [1, 2], [1, None, 2]),
    ([1, 2, 3, 4, 5], [4, 3, 5, 2, 1], [1, 2, None, 3, None, 4, 5]),
    ([1, 2, 4, 5, 3, 6, 7], [4, 2, 5, 1, 6, 3, 7], [1, 2, 3, 4, 5, 6, 7]),
    ([1, 2, 3], [3, 2, 1], [1, 2, None, 3]),
    ([1, 2, 3], [1, 2, 3], [1, None, 2, None, 3]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: five working implementations agree ---")
    impls = [
        ("map + bounds + cursor ", sol.buildTree),
        ("slicing (O(n^2))      ", sol.buildTree_slicing),
        ("bounds on both arrays ", sol.buildTree_bounds_both),
        ("cursor as an iterator ", sol.buildTree_iterator),
        ("iterative, no recursion", sol.buildTree_iterative),
    ]
    for name, fn in impls:
        ok = all(to_level_order(fn(pre, ino)) == want for pre, ino, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output ---")
    for pre, ino, want in CASES:
        got = to_level_order(sol.buildTree(pre, ino))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  pre={str(pre):<22} in={str(ino):<22} -> {got}")

    # ----------------------------------------------------------------------
    # Live trace of the cursor and the bounds.
    # ----------------------------------------------------------------------
    print("\n--- trace: cursor into preorder, bounds into inorder ---")
    pre, ino = [3, 9, 20, 15, 7], [9, 3, 15, 20, 7]
    pos = {v: i for i, v in enumerate(ino)}
    print(f"  preorder = {pre}")
    print(f"  inorder  = {ino}")
    print(f"  pos      = {pos}")
    print(f"  {'call':<14} {'cursor':>7} {'val':>4} {'k':>3} {'left bounds':>13} "
          f"{'right bounds':>13}")
    cursor = [0]

    def trace(lo, hi, depth=0):
        if lo > hi:
            return None
        c0 = cursor[0]
        val = pre[c0]
        cursor[0] += 1
        k = pos[val]
        print(f"  {'  ' * depth + f'go({lo},{hi})':<14} {f'{c0}->{c0 + 1}':>7} "
              f"{val:>4} {k:>3} {f'({lo},{k - 1})':>13} {f'({k + 1},{hi})':>13}")
        node = TreeNode(val)
        node.left = trace(lo, k - 1, depth + 1)
        node.right = trace(k + 1, hi, depth + 1)
        return node

    traced = trace(0, len(ino) - 1)
    ok = to_level_order(traced) == [3, 9, 20, None, None, 15, 7]
    all_ok &= ok
    print(f"  -> level order {to_level_order(traced)}  correct: {ok}")

    # ----------------------------------------------------------------------
    # ⚠️ RIGHT-before-LEFT breaks the shared cursor.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  build RIGHT child first with a shared cursor (mistake 3) ---")
    print(f"  {'preorder':<22} {'inorder':<22} {'correct':<28} {'right-first'}")
    rf_seen = False
    for pre, ino, want in CASES[:6]:
        good = to_level_order(sol.buildTree(pre, ino))
        bad = attempt(sol.buildTree_broken_right_first, pre, ino)
        rf_seen |= good != bad
        print(f"  {str(pre):<22} {str(ino):<22} {str(good):<28} {bad}")
    all_ok &= rf_seen
    print("  The cursor still hands out preorder values 0,1,2,... in order — but")
    print("  now the right subtree consumes the values that belong to the left.")
    print("  Exhaustively, over every shape up to n = 6:")
    print(f"  {'n':>2} {'shapes':>7} {'agrees':>7} {'IndexError':>11} "
          f"{'silently wrong':>15}")
    total_wrong = 0
    for n in range(1, 7):
        shapes = all_shapes(n)
        agree = crash = wrong = 0
        for t in shapes:
            pre_t, in_t = preorder_of(t), inorder_of(t)
            try:
                got = to_level_order(sol.buildTree_broken_right_first(pre_t, in_t))
            except (IndexError, KeyError, RecursionError):
                crash += 1
                continue
            if got == to_level_order(t):
                agree += 1
            else:
                wrong += 1
        total_wrong += wrong
        print(f"  {n:>2} {len(shapes):>7} {agree:>7} {crash:>11} {wrong:>15}")
    print("  Measured result, and NOT what this demo was written expecting: the")
    print("  right-first bug never produces a silently wrong tree — it either")
    print("  raises IndexError or is genuinely correct. It is correct exactly")
    print("  when every node's RIGHT subtree is empty (a left-only chain), because")
    print("  then the swapped call visits an empty interval first and the cursor")
    print("  is never disturbed. Everywhere else the extra recursion mis-sizes an")
    print("  interval, creates more than n nodes, and runs off the end of")
    print("  `preorder`. A loud bug — but only because the cursor is bounds-")
    print("  checked by the list; the same swap in a language with raw pointers")
    print("  would read garbage instead.")
    all_ok &= (total_wrong == 0)

    print("\n--- ⚠️  `preorder[1:k]` instead of `preorder[1:k+1]` (mistake 1) ---")
    ob_seen = False
    for pre, ino, _ in CASES[:6]:
        good = to_level_order(sol.buildTree(pre, ino))
        bad = attempt(sol.buildTree_broken_offbyone, pre, ino)
        ob_seen |= good != bad
        print(f"  pre={str(pre):<22} correct={str(good):<28} off-by-one={bad}")
    all_ok &= ob_seen

    print("\n--- ⚠️  absolute inorder index used as a SIZE (mistake 2) ---")
    rk_seen = False
    for pre, ino, _ in CASES[:6]:
        good = to_level_order(sol.buildTree(pre, ino))
        bad = attempt(sol.buildTree_broken_relative_k, pre, ino)
        rk_seen |= good != bad
        print(f"  pre={str(pre):<22} correct={str(good):<28} k-as-size={bad}")
    all_ok &= rk_seen
    print("  `k` is an index into the WHOLE inorder array; the left subtree's")
    print("  size is `k - in_lo`. They coincide only when in_lo == 0, i.e. on")
    print("  the leftmost spine — so the bug hides on left-skewed input.")

    # ----------------------------------------------------------------------
    # WHICH PAIRS OF TRAVERSALS DETERMINE A TREE? Enumerate and count.
    # ----------------------------------------------------------------------
    print("\n--- which traversal PAIRS are unambiguous? (enumerated, not asserted) ---")
    print(f"  {'n':>2} {'shapes':>7} {'distinct pre+in':>16} {'distinct pre+post':>18} "
          f"{'distinct in+post':>17}")
    ambiguity_seen = False
    for n in range(1, 7):
        shapes = all_shapes(n)
        pre_in, pre_post, in_post = set(), set(), set()
        for t in shapes:
            p, i, q = tuple(preorder_of(t)), tuple(inorder_of(t)), tuple(postorder_of(t))
            pre_in.add((p, i))
            pre_post.add((p, q))
            in_post.add((i, q))
        if len(pre_post) < len(shapes):
            ambiguity_seen = True
        all_ok &= (len(pre_in) == len(shapes) and len(in_post) == len(shapes))
        print(f"  {n:>2} {len(shapes):>7} {len(pre_in):>16} {len(pre_post):>18} "
              f"{len(in_post):>17}")
    all_ok &= ambiguity_seen
    print("  pre+in and in+post always separate every shape. pre+post does NOT —")
    print("  the shortfall is the count of trees it cannot tell apart. INORDER is")
    print("  the only traversal that reveals the left/right SPLIT.")

    print("\n--- the smallest collision, in full ---")
    a = TreeNode(1, None, TreeNode(2))          # 1 with a RIGHT child
    b = TreeNode(1, TreeNode(2), None)          # 1 with a LEFT child
    print(f"  tree A (right child) level order {to_level_order(a)}: "
          f"pre={preorder_of(a)} post={postorder_of(a)} in={inorder_of(a)}")
    print(f"  tree B (left  child) level order {to_level_order(b)}: "
          f"pre={preorder_of(b)} post={postorder_of(b)} in={inorder_of(b)}")
    collide = (preorder_of(a) == preorder_of(b) and postorder_of(a) == postorder_of(b)
               and inorder_of(a) != inorder_of(b))
    all_ok &= collide
    print(f"  identical pre AND post, different inorder: {collide}")
    print("  A node with exactly ONE child is the entire source of ambiguity, and")
    print("  it is why LC 889 must guarantee a FULL binary tree.")

    print("\n--- restricted to FULL binary trees, pre+post becomes unambiguous ---")
    print(f"  {'n':>2} {'full shapes':>12} {'distinct pre+post':>18}  LC 889 rebuild ok?")
    for n in (1, 3, 5, 7, 9):
        full = [t for t in all_shapes(n) if is_full(t)]
        sigs = {(tuple(preorder_of(t)), tuple(postorder_of(t))) for t in full}
        rebuilt_ok = all(
            to_level_order(sol.buildTree889(preorder_of(t), postorder_of(t)))
            == to_level_order(t)
            for t in full)
        all_ok &= (len(sigs) == len(full)) and rebuilt_ok
        print(f"  {n:>2} {len(full):>12} {len(sigs):>18}  {rebuilt_ok}")
    print("  Zero collisions among full trees, and buildTree889 reconstructs every")
    print("  one of them exactly.")

    # ----------------------------------------------------------------------
    # LC 106 cross-check.
    # ----------------------------------------------------------------------
    print("\n--- LC 106 (inorder + postorder), the mirror image ---")
    ok106 = True
    for n in range(1, 7):
        for t in all_shapes(n):
            if to_level_order(sol.buildTree106(inorder_of(t), postorder_of(t))) \
                    != to_level_order(t):
                ok106 = False
    all_ok &= ok106
    total = sum(len(all_shapes(n)) for n in range(1, 7))
    print(f"  every shape up to n=6 ({total} trees) rebuilt from in+post: {ok106}")
    t = build([3, 9, 20, None, None, 15, 7])
    print(f"  example: in={inorder_of(t)} post={postorder_of(t)} -> "
          f"{to_level_order(sol.buildTree106(inorder_of(t), postorder_of(t)))}")

    # ----------------------------------------------------------------------
    # DUPLICATES break the index map.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  duplicate values: the constraint that makes the map legal ---")
    d1 = TreeNode(1, TreeNode(1), None)         # 1 with a LEFT child 1
    d2 = TreeNode(1, None, TreeNode(1))         # 1 with a RIGHT child 1
    for label, t in (("left child ", d1), ("right child", d2)):
        p, i = preorder_of(t), inorder_of(t)
        rebuilt = attempt(sol.buildTree, p, i)
        print(f"  original ({label}) {to_level_order(t)}: pre={p} in={i}")
        print(f"    -> rebuilt {rebuilt}   same as the original? "
              f"{rebuilt == to_level_order(t)}")
    p1, i1 = preorder_of(d1), inorder_of(d1)
    p2, i2 = preorder_of(d2), inorder_of(d2)
    same_traversals = (p1 == p2 and i1 == i2)
    all_ok &= same_traversals
    print(f"  BOTH trees have pre={p1} AND in={i1}: {same_traversals}")
    print("  With duplicates, pre+inorder no longer identifies a tree at all, so")
    print("  no algorithm can be 'correct' — which is exactly why LC 105")
    print("  guarantees unique values. `pos` keeps the LAST index for a repeated")
    print("  key, so the dict picks one candidate position; here that choice")
    print("  mis-sizes an interval and the build fails outright rather than")
    print("  returning the wrong tree. Note the slicing version behaves")
    print("  differently on the same input, because `.index()` returns the FIRST")
    print("  match while the dict comprehension keeps the LAST:")
    for label, t in (("left child ", d1), ("right child", d2)):
        p, i = preorder_of(t), inorder_of(t)
        print(f"    slicing, original ({label}) -> "
              f"{attempt(sol.buildTree_slicing, p, i)}")
    print("  Two 'correct' implementations disagreeing is the signature of an")
    print("  ill-posed input, not of a bug in either one.")

    # ----------------------------------------------------------------------
    # Round-trip on random trees: the real correctness argument.
    # ----------------------------------------------------------------------
    print("\n--- round-trip: random tree -> (pre, in) -> rebuild -> compare ---")
    rng = random.Random(105)
    bad = 0
    trials = 1500
    for _ in range(trials):
        t = random_tree(rng.randint(1, 25), rng)
        p, i = preorder_of(t), inorder_of(t)
        for _name, fn in impls:
            if to_level_order(fn(p, i)) != to_level_order(t):
                bad += 1
    all_ok &= (bad == 0)
    print(f"  {trials} random trees x {len(impls)} implementations: {bad} mismatches")
    print("  Round-tripping is the honest test: it never hard-codes an expected")
    print("  tree, so it cannot agree with a bug by accident.")

    # ----------------------------------------------------------------------
    # BENCHMARK: slicing O(n^2) vs index-map O(n), on a SKEWED tree.
    # ----------------------------------------------------------------------
    print("\n--- benchmark: slicing O(n^2) vs index map + bounds O(n) ---")
    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(30000)
    try:
        print("  LEFT-SKEWED chain (h == n): the worst case for slicing")
        print(f"  {'n':>6} {'slicing (ms)':>14} {'index map (ms)':>15} "
              f"{'iterative (ms)':>15} {'slicing/map':>12}")
        for n in (200, 500, 1000, 2000, 4000):
            t = chain(n, left=True)
            p, i = preorder_of(t), inorder_of(t)
            t0 = time.perf_counter()
            a = sol.buildTree_slicing(p, i)
            t1 = time.perf_counter()
            b = sol.buildTree(p, i)
            t2 = time.perf_counter()
            c = sol.buildTree_iterative(p, i)
            t3 = time.perf_counter()
            all_ok &= (preorder_of(a) == p and preorder_of(b) == p
                       and preorder_of(c) == p)
            s_ms, m_ms, i_ms = (t1 - t0) * 1000, (t2 - t1) * 1000, (t3 - t2) * 1000
            print(f"  {n:>6} {s_ms:>14.2f} {m_ms:>15.2f} {i_ms:>15.2f} "
                  f"{s_ms / m_ms:>11.1f}x")
        print("  RIGHT-SKEWED chain: preorder == inorder, k == 0 at every step")
        print(f"  {'n':>6} {'slicing (ms)':>14} {'index map (ms)':>15} "
              f"{'slicing/map':>12}")
        for n in (200, 500, 1000, 2000, 4000):
            t = chain(n, left=False)
            p, i = preorder_of(t), inorder_of(t)
            t0 = time.perf_counter()
            sol.buildTree_slicing(p, i)
            t1 = time.perf_counter()
            sol.buildTree(p, i)
            t2 = time.perf_counter()
            s_ms, m_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
            print(f"  {n:>6} {s_ms:>14.2f} {m_ms:>15.2f} {s_ms / m_ms:>11.1f}x")
        print("  BALANCED tree: where the O(n^2) hides")
        print(f"  {'depth':>6} {'nodes':>7} {'slicing (ms)':>14} "
              f"{'index map (ms)':>15} {'slicing/map':>12}")
        for depth in (10, 12, 14):
            t = balanced(depth)
            p, i = preorder_of(t), inorder_of(t)
            t0 = time.perf_counter()
            sol.buildTree_slicing(p, i)
            t1 = time.perf_counter()
            sol.buildTree(p, i)
            t2 = time.perf_counter()
            s_ms, m_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
            print(f"  {depth:>6} {2 ** depth - 1:>7} {s_ms:>14.2f} {m_ms:>15.2f} "
                  f"{s_ms / m_ms:>11.1f}x")
    finally:
        sys.setrecursionlimit(old_limit)
    print("  On a chain the ratio climbs steadily with n — an asymptotic gap. On")
    print("  a balanced tree the slice sizes sum to O(n log n) and `.index()`")
    print("  scans a subtree, not the whole array, so the gap is far milder.")
    print("  Benchmarking only on balanced input would understate the problem.")

    # ----------------------------------------------------------------------
    # Recursion depth: a legal input (n <= 3000, chain) blows the stack.
    # ----------------------------------------------------------------------
    print("\n--- a legal LC 105 input that kills the recursive versions ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    t = chain(3000, left=True)
    p, i = preorder_of(t), inorder_of(t)
    print(f"  input: a 3000-node left chain (n <= 3000 is allowed), h = 3000")
    for name, fn in (("map + bounds + cursor", sol.buildTree),
                     ("slicing              ", sol.buildTree_slicing),
                     ("iterative            ", sol.buildTree_iterative)):
        try:
            r = fn(p, i)
            msg = f"ok, {len(preorder_of(r))} nodes"
            died = False
        except RecursionError as exc:
            msg = f"{type(exc).__name__}: {exc}"
            died = True
        print(f"  {name} -> {msg}")
        if name.startswith("iterative"):
            all_ok &= not died
        else:
            all_ok &= died
    print("  Only the iterative version survives at the default limit. The O(n)")
    print("  time fix and the O(h) stack problem are INDEPENDENT — fixing one")
    print("  does not fix the other.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
