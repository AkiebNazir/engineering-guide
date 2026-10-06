"""
================================================================================
SOLUTION · LeetCode 450 · Delete Node in a BST                       [Medium]
https://leetcode.com/problems/delete-node-in-a-bst/
================================================================================

THE CORE IDEA
--------------
Finding the node is problem 001. The entire problem is what fills the hole,
and there are exactly THREE cases — say all three out loud before you write
a line, because skipping one is how this problem is failed:

    1. LEAF          -> return None. The parent's child slot becomes empty.
    2. ONE CHILD      -> return that child. It is promoted into the hole, and
                        its whole subtree is already on the correct side of
                        every ancestor, so nothing else needs to change.
    3. TWO CHILDREN   -> neither child can be promoted (each has its own two
                        subtrees and the hole holds one node). So:
                          a. successor = MIN of the right subtree
                          b. copy successor.val into this node
                          c. recursively delete successor.val from the right
                             subtree — which is guaranteed to be case 1 or 2,
                             because a subtree minimum has NO LEFT CHILD.

    def deleteNode(root, key):
        if root is None:
            return None
        if key < root.val:
            root.left = self.deleteNode(root.left, key)      # RE-ATTACH
        elif key > root.val:
            root.right = self.deleteNode(root.right, key)    # RE-ATTACH
        else:
            if root.left is None:
                return root.right          # covers case 1 AND case 2
            if root.right is None:
                return root.left           # case 2, other side
            succ = root.right              # case 3
            while succ.left:
                succ = succ.left
            root.val = succ.val
            root.right = self.deleteNode(root.right, succ.val)
        return root

O(h) time, O(h) stack. Case 3's recursive call walks DOWN the same path the
successor search just walked, so it is one O(h) descent, not O(h) squared.


================================================================================
WHY `root.left = self.deleteNode(root.left, key)` IS THE WHOLE TRICK
================================================================================
A delete can change WHICH NODE is the root of a subtree — that is the one
thing insert never does, and it is why 450 is so much harder than 701.

    deleting 6 from        5              the subtree rooted at 6
                          ╱ ╲             becomes the subtree rooted at 7.
                         3   6            Someone has to tell node 5 about
                              ╲           that. Node 5's `.right` pointer is
                               7          the only thing pointing at 6.

Python cannot pass "a reference to node 5's `.right` slot" into a function
(there are no pointers-to-pointers). So the recursion inverts the problem:
each call RETURNS the new root of the subtree it was given, and the caller
assigns that return value straight back into the child slot it came from.

    root.left = deleteNode(root.left, key)
    ^^^^^^^^^   ^^^^^^^^^^^^^^^^^^^^^^^^^
    the parent  "here is the subtree's root, possibly a different node now"
    re-attaches

On the levels where nothing changed, that assignment writes the same node
back — a harmless no-op. On the ONE level where the subtree root changed, it
is the only line in the program that keeps the tree connected. Write
`self.deleteNode(root.left, key)` without the assignment and the delete
appears to work on the returned value while the caller's tree is silently
unchanged; the demo below runs exactly that bug and prints the result.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): in-order traverse to a
sorted list, drop the key, rebuild with problem 002. O(n) time, O(n) space,
and it re-shapes the entire tree. It is a legitimate answer to "delete AND
rebalance" and a terrible answer to "delete".

Approach 1 (recursive, successor-swap) ✅ — the answer above. The successor
is copied by VALUE, so no pointer surgery is needed at the deleted node at
all; the actual node removal happens one level down, in the easy case.

Approach 2 (recursive, PREDECESSOR-swap) — identical, mirrored: take the MAX
of the left subtree (walk left once, then right forever), copy its value up,
delete it from the left subtree. It is guaranteed to have no RIGHT child, so
again case 1 or 2. Produces a DIFFERENT but equally valid tree — LeetCode
accepts both, and its own Example 1 lists both outputs. Worth knowing
because always taking the successor biases the tree left-heavy over many
deletes; alternating is a real (if minor) balancing heuristic.

Approach 3 (iterative with a parent pointer) — no recursion, O(1) space.
More code, and the case analysis is identical; the extra work is remembering
whether the node you are removing is its parent's left or right child. Worth
writing once so you are not afraid of it, and worth choosing when h can
reach 10^4 (the stated limit) because the recursive version raises
RecursionError there — demoed below.

Approach 4 (pointer surgery instead of value copy, case 3) — instead of
copying the successor's value, actually splice the successor node in: detach
it from its parent, give it the deleted node's two children, and re-attach.
Same result, four or five pointer writes instead of one value write, and
several more ways to get it wrong. Only necessary when nodes carry identity
that must not be overwritten (e.g. external references point at the node
objects, or nodes carry extra payload). Say that caveat out loud — it is a
good senior-level observation — then write the value-copy version.


================================================================================
STEP BY STEP TRACE — ALL THREE CASES
================================================================================
Start from        5
                 ╱ ╲
                3   6
               ╱ ╲   ╲
              2   4   7


CASE 1 · delete 7 (a LEAF)
    at 5: 7 > 5 -> root.right = delete(6-subtree, 7)
      at 6: 7 > 6 -> root.right = delete(7-subtree, 7)
        at 7: match. left is None -> return root.right, which is also None
      so 6.right = None
    result:      5            in-order [2,3,4,5,6] ✅
                ╱ ╲
               3   6
              ╱ ╲
             2   4


CASE 2 · delete 6 (ONE child, on the right)
    at 5: 6 > 5 -> root.right = delete(6-subtree, 6)
      at 6: match. left is None -> return root.right == node 7
    so 5.right = 7   <-- the re-attachment doing real work
    result:      5            in-order [2,3,4,5,7] ✅
                ╱ ╲
               3   7
              ╱ ╲
             2   4


CASE 3 · delete 3 (TWO children)
    at 5: 3 < 5 -> root.left = delete(3-subtree, 3)
      at 3: match, both children exist.
        succ = min(right subtree of 3) = walk to 4, 4.left is None -> succ = 4
        copy: node 3 becomes node 4  ->  the tree now has TWO 4s, briefly:
                     4(was 3)
                    ╱       ╲
                   2         4
        delete 4 from the right subtree: at 4, match, leaf -> return None
        so (was-3).right = None
      return the node (now holding 4)
    so 5.left = that node (unchanged identity, changed value)
    result:      5            in-order [2,4,5,6,7] ✅
                ╱ ╲
               4   6
              ╱     ╲
             2       7

    The predecessor variant would instead copy 2 up and delete 2:
                 5
                ╱ ╲
               2   6
                ╲   ╲
                 4   7        in-order [2,4,5,6,7] ✅ — same values, different shape


CASE 3 · delete the ROOT (5) — the case people forget to test
    at 5: match, two children.
      succ = min(6-subtree) = 6 (6.left is None)
      5.val = 6; delete 6 from the right subtree -> 6 has one child (7) ->
      return 7
    result:      6            in-order [2,3,4,6,7] ✅
                ╱ ╲
               3   7
              ╱ ╲
             2   4


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time     Space   Mutates input?  Note
    -----------------------------  -------  ------  --------------  ------------
    Flatten, drop, rebuild (002)   O(n)     O(n)    no (new tree)   rebalances too
    Recursive successor-swap ✅     O(h)     O(h)    YES             the answer
    Recursive predecessor-swap     O(h)     O(h)    YES             mirror image,
                                                                     different tree
    Iterative + parent pointer     O(h)     O(1)    YES             no recursion
                                                                     ceiling
    Pointer-splice (no value copy) O(h)     O(h)    YES             preserves node
                                                                     IDENTITY

    "Mutates input?" is the column that matters most in this file. The
    recursive versions MUTATE the caller's tree in place AND may return a
    different root object than they were given. Both facts must be handled
    by the caller: `root = deleteNode(root, key)`, never a bare
    `deleteNode(root, key)`. And note the value-copy version overwrites
    `node.val` on a node the caller may hold a reference to — if the caller
    cached "the node holding 3", it now holds 4. Approach 4 exists for
    exactly that situation.


================================================================================
EDGE CASES
================================================================================
    root is None                 -> return None. Also the recursion's base case.
    key not present               -> the descent falls off the bottom and the
                                     re-attachment writes back unchanged nodes
                                     all the way up. Tree unchanged, no error.
    delete the ROOT, no children  -> returns None; the whole tree is gone. Any
                                     caller ignoring the return value now holds
                                     a stale root.
    delete the ROOT, two children -> the root OBJECT survives but its value
                                     changes (value-copy version). Tested above.
    delete the ROOT, one child    -> the returned root is a DIFFERENT object.
                                     This is the case that punishes ignoring
                                     the return value.
    successor is root.right itself -> happens when root.right has no left
                                     child. The `while succ.left` loop runs
                                     zero times. Very easy to get wrong if you
                                     write `succ = root.right.left` first.
    node with only a LEFT child    -> the mirror of case 2; both branches must
                                     exist in your code or half the trees break.
    a chain of 10^4 nodes          -> legal input; the recursive version raises
                                     RecursionError. Demoed below.
    delete every node in turn      -> the strongest test there is; run below,
                                     re-checking the invariant after each one.


================================================================================
COMMON MISTAKES
================================================================================
1. Calling `self.deleteNode(root.left, key)` WITHOUT assigning the result
   back to `root.left`. The subtree is rebuilt correctly and then thrown
   away. Silent wrong answer, no exception. Demoed live below.

2. Handling only two cases (leaf, two children) and forgetting the
   one-child case — or handling "one child" only on the right. `if root.left
   is None: return root.right` covers leaf AND right-only in a single line
   precisely because a leaf's `root.right` is also None; that compression is
   elegant but it hides the case count, so name all three anyway.

3. Taking the successor as `root.right.left` directly instead of walking left
   until `None`. Correct only when the right child has exactly one left
   descendant; wrong in general, and it crashes with AttributeError when
   `root.right.left` is None.

4. Taking the MIN of the LEFT subtree (or the MAX of the right) as the
   replacement. Those are not the neighbours of the deleted value; the
   result is not a BST. The two correct choices are min-of-right (successor)
   and max-of-left (predecessor).

5. After copying the successor's value up, deleting `key` from the right
   subtree instead of `succ.val`. `key` is not in the right subtree — the
   delete becomes a no-op and the tree ends up with the successor's value
   twice.

6. Deleting the successor from `root` rather than from `root.right`. Since
   `root.val` is now the successor's value, the descent matches at the root
   again — infinite recursion.

7. Ignoring the return value in the CALLER (`deleteNode(root, key)` then
   using the old `root`). Deleting the root with 0 or 1 children changes
   which object is the root; the caller's variable is then stale.

8. Trying to do case 3 by moving pointers before you have thought about
   where the successor's own right subtree goes. The value-copy formulation
   exists exactly to avoid that thought.

9. Not re-testing the invariant after the delete. This problem has enough
   cases that "it worked on the example" means very little — the demo below
   deletes every node of many random trees and re-verifies.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do it iteratively, in O(1) space?
A: Yes — walk down with a trailing `parent` pointer, remember whether the
   target is the parent's left or right child, then apply the same three
   cases and write the replacement into `parent.left`/`parent.right` (or
   into your local `root` variable when the target IS the root).
   Implemented in this file as `deleteNode_iterative` and cross-checked
   against the recursive version on thousands of random trees.

Q: Use the predecessor instead.
A: Symmetric: max of the left subtree, guaranteed no right child. Different
   valid tree. Alternating successor/predecessor across deletes keeps the
   tree from drifting one-sided, which is a cheap poor-man's balancing.

Q: What happens to the tree's height after many deletes?
A: It never increases, but it does not self-correct either: repeatedly
   deleting with the successor rule biases the tree left-heavy. Genuine
   balance needs AVL/red-black rotations after each delete (harder than the
   insert case — a delete can require O(log n) rotations, not O(1)).

Q: The nodes carry a payload and other code holds references to them.
A: Then the value-copy trick is wrong: it mutates a node the caller may be
   holding. Use Approach 4, the pointer splice, so node identity is
   preserved. This is a genuinely good thing to raise unprompted.

Q: Delete a whole RANGE of keys, or all keys outside [low, high]?
A: LC 669 Trim a BST — one post-order recursion with the same re-attachment
   idiom, no successor logic needed, because trimming always promotes one
   side.

Q: Delete in a plain binary tree instead (no ordering)?
A: LC 1110 / the classic "delete node and return forest" shape. Without an
   ordering there is no successor to promote, so the standard trick is to
   move the DEEPEST/last node into the hole (that is how a binary heap
   deletes) — a different algorithm entirely, and a good illustration of
   what the BST invariant was buying you.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 3 of the topic guide's taxonomy: structural surgery.

    LC 701  Insert into a BST              — the easy counterpart (003)
    LC 669  Trim a Binary Search Tree       — same re-attachment idiom, no
                                               successor case
    LC 285  Inorder Successor in BST         — the successor, standalone
    LC 510  Inorder Successor in BST II      — successor with parent pointers
                                               and no root
    LC 99   Recover Binary Search Tree       — surgery driven by the in-order
                                               sequence (two nodes swapped)
    LC 1110 Delete Nodes And Return Forest   — deletion in a PLAIN tree, where
                                               no successor exists to promote
    LC 776  Split BST                        — split into two BSTs at a value;
                                               the same recursive re-attachment
    LC 1038 BST to Greater Sum Tree          — reverse in-order accumulation
================================================================================
"""

import random
import sys
from collections import deque
from typing import List, Optional, Tuple


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def deleteNode(self, root: Optional[TreeNode], key: int) -> Optional[TreeNode]:
        """✅ THE ANSWER — recursive, successor-swap, re-attachment idiom.
        O(h) time, O(h) stack. MUTATES in place and may return a different
        root object than it was given."""
        if root is None:
            return None
        if key < root.val:
            root.left = self.deleteNode(root.left, key)          # RE-ATTACH
        elif key > root.val:
            root.right = self.deleteNode(root.right, key)        # RE-ATTACH
        else:
            # ---- found it: the three cases ----
            if root.left is None:
                return root.right       # case 1 (leaf: right is None too) + case 2
            if root.right is None:
                return root.left        # case 2, mirrored
            succ = root.right           # case 3: min of the right subtree
            while succ.left:
                succ = succ.left
            root.val = succ.val         # copy the value up ...
            root.right = self.deleteNode(root.right, succ.val)   # ... delete it below
        return root

    def deleteNode_predecessor(self, root: Optional[TreeNode],
                               key: int) -> Optional[TreeNode]:
        """Equally correct mirror image: promote the in-order PREDECESSOR
        (max of the left subtree, guaranteed to have no right child).
        Produces a different — also valid — tree."""
        if root is None:
            return None
        if key < root.val:
            root.left = self.deleteNode_predecessor(root.left, key)
        elif key > root.val:
            root.right = self.deleteNode_predecessor(root.right, key)
        else:
            if root.right is None:
                return root.left
            if root.left is None:
                return root.right
            pred = root.left
            while pred.right:
                pred = pred.right
            root.val = pred.val
            root.left = self.deleteNode_predecessor(root.left, pred.val)
        return root

    def deleteNode_iterative(self, root: Optional[TreeNode],
                             key: int) -> Optional[TreeNode]:
        """O(h) time, O(1) space — no recursion, so no ceiling on a chain.
        The three cases are the same; the extra bookkeeping is remembering
        which side of its parent the target hangs on."""
        parent: Optional[TreeNode] = None
        node = root
        while node and node.val != key:
            parent = node
            node = node.left if key < node.val else node.right
        if node is None:
            return root                                  # key not present

        # Reduce the two-children case to the one-child/leaf case first.
        if node.left and node.right:
            succ_parent, succ = node, node.right
            while succ.left:
                succ_parent, succ = succ, succ.left
            node.val = succ.val                          # copy the value up
            # now physically remove `succ`, which has no LEFT child
            if succ_parent is node:
                succ_parent.right = succ.right
            else:
                succ_parent.left = succ.right
            return root

        # Leaf or single child: the replacement is whichever child exists.
        child = node.left if node.left else node.right
        if parent is None:
            return child                                 # deleted the root
        if parent.left is node:
            parent.left = child
        else:
            parent.right = child
        return root

    def deleteNode_no_reattach(self, root: Optional[TreeNode],
                               key: int) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — mistake #1. Recurses but throws the returned
        subtree away instead of assigning it back into the child slot. The
        work is done correctly and then discarded; no exception is raised."""
        if root is None:
            return None
        if key < root.val:
            self.deleteNode_no_reattach(root.left, key)      # result DISCARDED
        elif key > root.val:
            self.deleteNode_no_reattach(root.right, key)     # result DISCARDED
        else:
            if root.left is None:
                return root.right
            if root.right is None:
                return root.left
            succ = root.right
            while succ.left:
                succ = succ.left
            root.val = succ.val
            self.deleteNode_no_reattach(root.right, succ.val)  # DISCARDED
        return root

    def deleteNode_wrong_replacement(self, root: Optional[TreeNode],
                                     key: int) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — mistake #4. Uses the MINIMUM OF THE LEFT
        subtree as the replacement instead of the minimum of the RIGHT
        (or the maximum of the left). Produces a tree that is no longer a
        BST, again with no exception."""
        if root is None:
            return None
        if key < root.val:
            root.left = self.deleteNode_wrong_replacement(root.left, key)
        elif key > root.val:
            root.right = self.deleteNode_wrong_replacement(root.right, key)
        else:
            if root.left is None:
                return root.right
            if root.right is None:
                return root.left
            wrong = root.left
            while wrong.left:                    # MIN of the LEFT subtree ✗
                wrong = wrong.left
            root.val = wrong.val
            root.left = self.deleteNode_wrong_replacement(root.left, wrong.val)
        return root


# ==============================================================================
# TEST HELPERS — shared with topic 10 (plain binary trees), verbatim
# ==============================================================================
def build(values):
    """LeetCode level-order list (with `None` holes) -> root TreeNode."""
    if not values or values[0] is None:
        return None
    root = TreeNode(values[0])
    queue = deque([root])
    i = 1
    while queue and i < len(values):
        node = queue.popleft()
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.left = TreeNode(v)
                queue.append(node.left)
        if i < len(values):
            v = values[i]
            i += 1
            if v is not None:
                node.right = TreeNode(v)
                queue.append(node.right)
    return root


def to_level_order(root):
    """Inverse of build(): level-order list with `None` for absent children,
    trailing `None`s trimmed."""
    if root is None:
        return []
    out, queue = [], deque([root])
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


# ------------------------------------------------------------------------------
# THE INVARIANT CHECKER — the real test for this problem. Fixed expected
# outputs are weak here (successor and predecessor give different valid
# trees); "is this still a BST containing exactly the right values" is not.
# ------------------------------------------------------------------------------
def inorder_iterative(root):
    out, stack, node = [], [], root
    while stack or node:
        while node:
            stack.append(node)
            node = node.left
        node = stack.pop()
        out.append(node.val)
        node = node.right
    return out


def check_bst_invariant(root) -> Tuple[bool, str]:
    """Verify the SUBTREE-WIDE invariant properly, with min/max bounds — not
    just parent-vs-child (see problem 006). Iterative, so it survives chains.
    Returns (ok, reason)."""
    stack = [(root, None, None)]              # (node, low, high) exclusive bounds
    while stack:
        node, low, high = stack.pop()
        if node is None:
            continue
        if low is not None and node.val <= low:
            return False, f"node {node.val} violates low bound {low}"
        if high is not None and node.val >= high:
            return False, f"node {node.val} violates high bound {high}"
        stack.append((node.left, low, node.val))
        stack.append((node.right, node.val, high))
    return True, "ok"


def height_iterative(root):
    if root is None:
        return 0
    best, stack = 0, [(root, 1)]
    while stack:
        node, d = stack.pop()
        best = max(best, d)
        if node.left:
            stack.append((node.left, d + 1))
        if node.right:
            stack.append((node.right, d + 1))
    return best


def bst_insert_iterative(root, val):
    node = TreeNode(val)
    if root is None:
        return node
    curr = root
    while True:
        if val < curr.val:
            if curr.left is None:
                curr.left = node
                return root
            curr = curr.left
        else:
            if curr.right is None:
                curr.right = node
                return root
            curr = curr.right


def make_random_bst(values):
    root = None
    for v in values:
        root = bst_insert_iterative(root, v)
    return root


# ==============================================================================
# TESTS — run:  python 004_delete_node_in_a_bst_solution.py
# ==============================================================================
BASE = [5, 3, 6, 2, 4, None, 7]
CASES = [
    (BASE, 3),      # case 3: two children
    (BASE, 0),      # not present
    ([], 0),        # empty tree
    (BASE, 5),      # case 3 at the ROOT
    (BASE, 7),      # case 1: leaf
    (BASE, 6),      # case 2: one child (right)
    (BASE, 2),      # case 1: leaf, left side
    (BASE, 4),      # case 1: leaf, right side
    ([1], 1),       # delete the only node
    ([2, 1], 2),    # case 2 at the ROOT (one LEFT child)
    ([1, None, 2], 1),   # case 2 at the ROOT (one RIGHT child)
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 3),
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 10),
    ([8, 3, 10, 1, 6, None, 14, None, None, 4, 7, 13], 8),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: invariant holds and exactly the key is gone ---")
    for values, key in CASES:
        present = [v for v in values if v is not None]
        want = sorted(v for v in present if v != key)
        root = sol.deleteNode(build(values), key)
        io = inorder_iterative(root)
        inv, why = check_bst_invariant(root)
        ok = io == want and inv
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  tree={values!r:<48} key={key:<4} "
              f"-> {to_level_order(root)}  bst={inv}")

    print("\n--- predecessor variant: different tree, equally valid ---")
    for values, key in CASES:
        present = [v for v in values if v is not None]
        want = sorted(v for v in present if v != key)
        a = sol.deleteNode(build(values), key)
        b = sol.deleteNode_predecessor(build(values), key)
        la, lb = to_level_order(a), to_level_order(b)
        ok = (inorder_iterative(b) == want and check_bst_invariant(b)[0])
        all_ok &= ok
        marker = "SAME shape" if la == lb else "DIFFERENT shape, both valid"
        print(f"{'PASS' if ok else 'FAIL'}  key={key:<4} succ={la}  "
              f"pred={lb}  <- {marker}")

    print("\n--- iterative variant: same values, invariant holds ---")
    for values, key in CASES:
        present = [v for v in values if v is not None]
        want = sorted(v for v in present if v != key)
        c = sol.deleteNode_iterative(build(values), key)
        ok = inorder_iterative(c) == want and check_bst_invariant(c)[0]
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  key={key:<4} iterative -> "
              f"{to_level_order(c)}")

    # ----------------------------------------------------------------------
    # Trace: all three cases, printed from the live tree.
    # ----------------------------------------------------------------------
    print("\n--- trace: the three cases on [5,3,6,2,4,null,7] ---")
    for key, label in ((7, "CASE 1 · leaf"),
                       (6, "CASE 2 · one child"),
                       (3, "CASE 3 · two children"),
                       (5, "CASE 3 · at the ROOT")):
        before = build(BASE)
        node = before
        path = []
        while node and node.val != key:
            path.append(node.val)
            node = node.left if key < node.val else node.right
        kids = 0 if node is None else (bool(node.left) + bool(node.right))
        succ_val = None
        if kids == 2:
            s = node.right
            while s.left:
                s = s.left
            succ_val = s.val
        after = sol.deleteNode(before, key)
        print(f"  {label:<24} key={key}  descent={path or '[root]'}  "
              f"children={kids}"
              + (f"  successor={succ_val}" if succ_val is not None else ""))
        print(f"      before {to_level_order(build(BASE))}  ->  after "
              f"{to_level_order(after)}   in-order {inorder_iterative(after)}")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO A: mistake #1 — recursing without re-attaching.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo A: mistake #1, no re-attachment ---")
    for values, key, why in (
        ([5, 3, 6, 2, 4, None, 7], 6, "case 2 below the root: 5.right must become 7"),
        ([5, 3, 6, 2, 4, None, 7], 7, "case 1 below the root: 6.right must become None"),
    ):
        good = sol.deleteNode(build(values), key)
        bad = sol.deleteNode_no_reattach(build(values), key)
        gio, bio = inorder_iterative(good), inorder_iterative(bad)
        print(f"  delete {key} — {why}")
        print(f"    correct        -> {to_level_order(good)}  in-order {gio}")
        print(f"    no re-attach   -> {to_level_order(bad)}  in-order {bio}")
        still_there = key in bio
        print(f"    the key is STILL IN THE TREE after the broken delete: "
              f"{still_there}  (no exception raised)")
        all_ok &= still_there

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO B: mistake #4 — wrong replacement node.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo B: mistake #4, min-of-LEFT as the replacement ---")
    print("  NOTE it takes the right INPUT to expose this. On [5,3,6,2,4,null,7]")
    print("  the deleted node's left subtree is the single node 2, so min-of-left")
    print("  and max-of-left coincide and the wrong code accidentally produces a")
    print("  valid tree. The bug only shows when the left subtree has >= 2 levels:")
    exposed = False
    for values, key in (([5, 3, 6, 2, 4, None, 7], 3),
                        ([10, 5, 15, 2, 7, None, None, 1, 3], 5)):
        bad = sol.deleteNode_wrong_replacement(build(values), key)
        good = sol.deleteNode(build(values), key)
        inv, why = check_bst_invariant(bad)
        io = inorder_iterative(bad)
        sorted_io = io == sorted(io)
        print(f"\n  delete {key} from {values}")
        print(f"    correct (min-of-RIGHT) -> {to_level_order(good)}  "
              f"in-order {inorder_iterative(good)}")
        print(f"    wrong   (min-of-LEFT)  -> {to_level_order(bad)}  "
              f"in-order {io}")
        print(f"    still a BST? {inv}   in-order sorted? {sorted_io}"
              + (f"   reason: {why}" if not inv else "   (got lucky here)"))
        if not inv:
            exposed = True
    print("\n  On the second tree the promoted value (1, the MINIMUM of the left")
    print("  subtree) is smaller than 2 and 3, which stay in the left subtree —")
    print("  so the left child now exceeds its parent and the in-order sequence")
    print("  comes out unsorted, with no exception raised anywhere. The")
    print("  replacement must be a NEIGHBOUR of the deleted value in sorted")
    print("  order: min of the RIGHT subtree, or max of the LEFT subtree.")
    print("  Lesson for your own tests: one example is not coverage. This is")
    print("  why DEMO 1 below deletes every node of hundreds of random trees.")
    all_ok &= exposed          # we WANT to have proven the bug is real

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 1: THE strong test — delete every node in turn, re-check.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 1: delete EVERY node in turn, re-verifying the invariant ---")
    random.seed(450)
    total_deletes, violations = 0, 0
    for trial in range(300):
        vals = random.sample(range(-300, 300), random.randint(1, 40))
        for victim in vals:                       # delete each value from a
            root = make_random_bst(vals)          # freshly built identical tree
            root = sol.deleteNode(root, victim)
            total_deletes += 1
            inv, why = check_bst_invariant(root)
            want = sorted(v for v in vals if v != victim)
            if not inv or inorder_iterative(root) != want:
                violations += 1
    print(f"  {total_deletes} single deletes across 300 random BSTs: "
          f"{violations} invariant violations")
    all_ok &= (violations == 0)

    print("\n  ... and now deleting the whole tree, one node at a time, "
          "in random order:")
    drain_violations = 0
    for trial in range(200):
        vals = random.sample(range(-300, 300), random.randint(1, 40))
        root = make_random_bst(vals)
        order = vals[:]
        random.shuffle(order)
        remaining = set(vals)
        for victim in order:
            root = sol.deleteNode(root, victim)
            remaining.discard(victim)
            inv, _ = check_bst_invariant(root)
            if not inv or inorder_iterative(root) != sorted(remaining):
                drain_violations += 1
        if root is not None:
            drain_violations += 1
    print(f"  200 trees fully drained node-by-node: {drain_violations} violations "
          f"(and every tree ended as None)")
    all_ok &= (drain_violations == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 2: all three implementations agree on 5000 random deletes.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 2: successor / predecessor / iterative all stay valid ---")
    random.seed(7)
    disagreements, shape_differences = 0, 0
    for _ in range(5000):
        vals = random.sample(range(-100, 100), random.randint(1, 25))
        victim = (random.choice(vals) if random.random() < 0.8
                  else random.randint(-150, 150))
        want = sorted(v for v in vals if v != victim)
        trees = [sol.deleteNode(make_random_bst(vals), victim),
                 sol.deleteNode_predecessor(make_random_bst(vals), victim),
                 sol.deleteNode_iterative(make_random_bst(vals), victim)]
        for t in trees:
            if inorder_iterative(t) != want or not check_bst_invariant(t)[0]:
                disagreements += 1
        if len({tuple(to_level_order(t)) for t in trees}) > 1:
            shape_differences += 1
    print(f"  5000 random deletes x 3 implementations: {disagreements} failures")
    print(f"  cases where the three produced DIFFERENT shapes: "
          f"{shape_differences} / 5000")
    print("  All three are correct. They just disagree on the shape — which is")
    print("  exactly why this file tests the invariant, not a fixed output.")
    all_ok &= (disagreements == 0)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO 3: recursion depth on a legal (degenerate) input.
    # ----------------------------------------------------------------------
    print("\n--- DEMO 3: a legal 4000-node chain breaks the recursive version ---")
    chain = None
    for v in range(4_000):
        chain = bst_insert_iterative(chain, v)
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}, "
          f"chain height = {height_iterative(chain)}")
    it = sol.deleteNode_iterative(chain, 3_999)
    it_ok = check_bst_invariant(it)[0] and 3_999 not in inorder_iterative(it)
    print(f"  iterative delete of the deepest node: succeeded -> {it_ok}")
    raised = False
    try:
        sol.deleteNode(it, 3_998)
        print("  recursive delete of the deepest node: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive delete of the deepest node: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: {it_ok and raised}")
    all_ok &= it_ok and raised

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
