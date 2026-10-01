"""
================================================================================
SOLUTION · LeetCode 145 · Binary Tree Postorder Traversal               [Easy]
https://leetcode.com/problems/binary-tree-postorder-traversal/
================================================================================

THE CORE IDEA
--------------
Same recursion as 001 and 002, with the record step moved to the end:

    def dfs(node):
        if not node: return
        dfs(node.left)            # LEFT
        dfs(node.right)           # RIGHT
        out.append(node.val)      # NODE   <- postorder puts it LAST

Postorder is "children before parent", which makes it the engine of every
BOTTOM-UP tree algorithm in this folder — 005 max depth, 009 balanced, 010
diameter, 017 LCA, 018 max path sum. The rule of thumb: *if answering for a
node requires both children's answers, you are writing a postorder traversal
whether you call it that or not.*

Iteratively there are two accepted answers and they are NOT interchangeable:

  (a) REVERSED PREORDER — run preorder with the pushes swapped (node, right,
      left) and reverse the output, because
      reverse(node, right, left) == (left, right, node):

          stack, out = [root], []
          while stack:
              node = stack.pop()
              out.append(node.val)
              if node.left:  stack.append(node.left)     # LEFT first now
              if node.right: stack.append(node.right)
          out.reverse()

      Shortest to write, fastest of the three in CPython. But it VISITS the
      nodes top-down; only the emitted list is postorder. Any work that must
      genuinely happen after a node's children — freeing nodes, writing a
      subtree aggregate into the node — is wrong in this order. Demonstrated
      live below with subtree sums that come out wrong.

  (b) THE HONEST ONE-STACK VERSION with a `last_visited` pointer — dives the
      left spine, then peeks:

          out, stack, curr, last = [], [], root, None
          while curr or stack:
              while curr:                        # dive down the left spine
                  stack.append(curr)
                  curr = curr.left
              peek = stack[-1]
              if peek.right and peek.right is not last:
                  curr = peek.right               # right subtree still owed
              else:
                  out.append(peek.val)            # both children done
                  last = stack.pop()

      This one visits nodes in true postorder, so it can replace the
      recursion in a bottom-up algorithm. It is also the slowest of the three
      here (measured below), because each node is peeked at twice.

O(n) time, O(h) space for all of them.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): compute the preorder, then try to
rearrange it into postorder without the tree. Impossible in general — a
preorder sequence alone does not determine the tree (that is exactly why LC
105 needs preorder AND inorder). Worth saying out loud: traversal order is a
property of the structure, not a permutation you can recover from one list.

Approach 1 (recursion) ✅ — lead with it. O(n) / O(h).
Approach 2 (reversed preorder, one stack + one reverse) ✅ — O(n) / O(h),
   fastest measured. Values only; visit order is top-down.
Approach 3 (two stacks) — the same trick, written as "push to stack2 instead
   of appending, then drain stack2". Identical work, an extra O(n) list; the
   `out.reverse()` version is strictly simpler. Mentioned because "the
   two-stack solution" is what interviewers often call it.
Approach 4 (one stack + `last_visited`) ✅ — O(n) / O(h), true postorder
   visit order. The one to use when the *work*, not just the output list,
   has to be bottom-up.
Approach 5 ((node, expanded) flag stack) — push `(node, False)`; on pop,
   either re-push `(node, True)` after its children or record. O(n) time,
   O(n) space, and one shape that serves all three orders by moving the
   `(node, True)` push. Bulkier but the easiest to derive under pressure.


================================================================================
STEP BY STEP TRACE — the `last_visited` version on [1,2,3]
================================================================================
    Tree:      1          postorder = 2 3 1
              ╱ ╲
             2   3

    curr  stack  last  peek  decision
    ----  -----  ----  ----  ------------------------------------------
    1     []     -     -     dive: push 1, curr=1.left=2
    2     [1]    -     -     dive: push 2, curr=None
    None  [1,2]  -     2     2.right is None -> record 2, pop, last=2
    None  [1]    2     1     1.right=3 and 3 is not last -> curr=3
    3     [1]    2     -     dive: push 3, curr=None
    None  [1,3]  2     3     3.right is None -> record 3, pop, last=3
    None  [1]    3     1     1.right=3 IS last -> record 1, pop, last=1
    None  []     1     -     loop ends.   out = [2,3,1]

    The `peek.right is not last` test is the entire mechanism: it is how the
    loop distinguishes "arriving at 1 from below-left" (row 4, go right) from
    "arriving at 1 from below-right" (row 7, record it). Drop it and you
    descend into the right subtree forever.

    And the reversed-preorder trick on the same tree:

        push order right-then-left reversed to left-then-right:
        pop 1 -> out=[1], push 2, push 3
        pop 3 -> out=[1,3]
        pop 2 -> out=[1,3,2]
        reverse -> [2,3,1]                    same answer, opposite visit order


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                   Time   Space (aux)  Mutates input?  Visit order
    -------------------------  -----  -----------  --------------  ---------------
    Recursion ✅               O(n)   O(h)         no              true postorder
    Reversed preorder ✅       O(n)   O(h)         no              TOP-DOWN (!)
    Two stacks                 O(n)   O(n)         no              TOP-DOWN (!)
    One stack + last_visited ✅ O(n)  O(h)         no              true postorder
    (node, expanded) flags     O(n)   O(n)         no              true postorder

    Measured on a 50k-node random tree (numbers from this machine, see the
    demo): reversed preorder is the fastest, recursion sits in the middle, and
    the `last_visited` version is the slowest — it peeks at every node twice
    and does more branching per node. All three are O(n); the constant factor
    is the only thing separating them.


================================================================================
EDGE CASES
================================================================================
    root = None        -> []       every version must guard before `stack=[root]`.
    single node         -> [val]    recorded on the first peek, `last` still None.
    left-only chain      -> peak stack = n (the whole spine is pushed before
                           anything is recorded). The `last_visited` version's
                           worst case for space, and the shape that makes the
                           recursion raise RecursionError.
    right-only chain      -> the `last_visited` version still pushes the whole
                           chain, because it must return through every node to
                           record it. Unlike preorder (001), postorder has no
                           cheap skew direction: BOTH chains cost O(n) space.
                           Measured below.
    a node with only a RIGHT child -> the case that breaks a `last_visited`
                           implementation missing the `is not last` guard: it
                           keeps re-descending into the same right subtree.


================================================================================
COMMON MISTAKES
================================================================================
1. Using the reversed-preorder trick for work that must be bottom-up. The
   returned LIST is postorder; the nodes were VISITED parent-first. Freeing
   nodes, or writing `node.subtree_sum` as you go, silently produces garbage.
   Demonstrated live below: subtree sums computed in that visit order are
   wrong for every internal node.
2. Forgetting the final `out.reverse()` (or reversing the input instead of the
   output). You then return node-right-left, which for a single-node tree and
   for any right chain is indistinguishable from the correct answer.
3. Swapping only one of the two pushes in the trick: pushing right-then-left
   AND reversing gives you (node,left,right) reversed = (right,left,node),
   which is not postorder. Both pushes must swap relative to preorder.
4. In the `last_visited` version, comparing `peek.right == last` instead of
   `is not last` — the intent is identity, and value equality would match a
   different node with the same value if `TreeNode.__eq__` were ever defined.
5. In the `last_visited` version, popping before recording (`node = stack.pop()`
   then deciding) — once popped you have lost the parent you may still need to
   return to. Peek first, pop only when you record.
6. Recording `peek.val` but forgetting `last = stack.pop()` — infinite loop on
   the same node.
7. Assuming postorder can be derived from preorder without the tree (see
   Approach 0). It cannot.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Give the reversed-preorder trick first (it is four lines), then volunteer
   that it visits nodes top-down and offer the `last_visited` version as the
   one that is a true postorder *visit*. That distinction is the interesting
   answer, and almost nobody says it.

Q: Which traversal would you use to delete/free every node of a tree?
A: Postorder — a true one. You must release the children before the parent,
   or you lose the pointers you need. In Python, `node.left = node.right =
   None` in postorder makes each subtree unreachable exactly once; the
   reversed-preorder trick would drop the references before the recursion had
   read them.

Q: Which traversal computes a subtree aggregate (size, sum, height)?
A: Postorder. That is problem 005 (max depth) and 009/010/018 in this folder:
   return a value up from each child, combine at the parent.

Q: N-ary tree postorder (LC 590)?
A: The same trick: push children left-to-right and reverse, or the
   `last_visited` idea generalised to "index of the next child to visit".

Q: Can postorder + inorder rebuild the tree?
A: Yes — LC 106, the mirror image of LC 105 (problem 016 here). The LAST
   postorder value is the root, then inorder splits the remaining values into
   the two subtrees. Preorder + postorder together cannot, in general.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 144   Preorder Traversal            — record FIRST (001 here)
    LC 94    Inorder Traversal             — record BETWEEN (002 here)
    LC 104   Maximum Depth                 — postorder combine (005 here)
    LC 110   Balanced Binary Tree          — postorder + sentinel (009 here)
    LC 543   Diameter of Binary Tree       — postorder + nonlocal best (010 here)
    LC 124   Binary Tree Maximum Path Sum  — the same shape, Hard (018 here)
    LC 236   Lowest Common Ancestor        — postorder bubble-up (017 here)
    LC 106   Build Tree from Inorder+Postorder — postorder's root is LAST
    LC 590   N-ary Tree Postorder          — same trick, k children
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def postorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        """Recursion: LEFT, RIGHT, NODE. O(n) time, O(h) space."""
        out: List[int] = []

        def dfs(node: Optional[TreeNode]) -> None:
            if not node:
                return
            dfs(node.left)            # LEFT
            dfs(node.right)           # RIGHT
            out.append(node.val)      # NODE

        dfs(root)
        return out

    def postorderTraversal_reversed_preorder(self, root: Optional[TreeNode]) -> List[int]:
        """Reversed-preorder trick: (node, right, left) reversed is postorder.
        O(n) time, O(h) space, fastest here — but the nodes are VISITED
        top-down, so use it for the output list only."""
        if not root:
            return []
        out: List[int] = []
        stack = [root]
        while stack:
            node = stack.pop()
            out.append(node.val)
            if node.left:
                stack.append(node.left)       # LEFT pushed first (mirror of 001)
            if node.right:
                stack.append(node.right)
        out.reverse()
        return out

    def postorderTraversal_two_stacks(self, root: Optional[TreeNode]) -> List[int]:
        """The same trick written the way interviewers name it: a second
        stack instead of a reverse. O(n) time, O(n) space."""
        if not root:
            return []
        stack, out_stack = [root], []
        while stack:
            node = stack.pop()
            out_stack.append(node)
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
        return [node.val for node in reversed(out_stack)]

    def postorderTraversal_last_visited(self, root: Optional[TreeNode]) -> List[int]:
        """Honest one-stack postorder: a `last_visited` pointer tells you
        whether you are arriving from the left or coming back from the right.
        O(n) time, O(h) space, TRUE postorder visit order."""
        out: List[int] = []
        stack: List[TreeNode] = []
        curr = root
        last: Optional[TreeNode] = None
        while curr or stack:
            while curr:                       # dive down the left spine
                stack.append(curr)
                curr = curr.left
            peek = stack[-1]
            if peek.right and peek.right is not last:
                curr = peek.right              # right subtree still owed
            else:
                out.append(peek.val)           # both children finished
                last = stack.pop()
        return out

    def postorderTraversal_flags(self, root: Optional[TreeNode]) -> List[int]:
        """(node, expanded) stack. O(n) time, O(n) space. Move the
        `(node, True)` push to get any of the three orders."""
        out: List[int] = []
        stack = [(root, False)] if root else []
        while stack:
            node, expanded = stack.pop()
            if node is None:
                continue
            if expanded:
                out.append(node.val)
            else:
                stack.append((node, True))          # record position = postorder
                stack.append((node.right, False))
                stack.append((node.left, False))
        return out

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def post_broken_no_reverse(self, root: Optional[TreeNode]) -> List[int]:
        """✗ BROKEN ON PURPOSE — the trick without the final reverse."""
        if not root:
            return []
        out: List[int] = []
        stack = [root]
        while stack:
            node = stack.pop()
            out.append(node.val)
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
        return out                              # <-- missing out.reverse()

    def post_broken_wrong_push_then_reverse(self, root: Optional[TreeNode]) -> List[int]:
        """✗ BROKEN ON PURPOSE — preorder's push order (right, then left) with
        a reverse: gives (right, left, node), not (left, right, node)."""
        if not root:
            return []
        out: List[int] = []
        stack = [root]
        while stack:
            node = stack.pop()
            out.append(node.val)
            if node.right:
                stack.append(node.right)
            if node.left:
                stack.append(node.left)
        out.reverse()
        return out

    def post_broken_no_last_guard(self, root: Optional[TreeNode], cap: int = 200) -> List[int]:
        """✗ BROKEN ON PURPOSE — `last_visited` version without the
        `is not last` test, so it re-descends the right subtree forever.
        Step-capped so the test run can show it instead of hanging."""
        out: List[int] = []
        stack: List[TreeNode] = []
        curr = root
        steps = 0
        while (curr or stack) and steps < cap:
            steps += 1
            while curr and steps < cap:
                steps += 1
                stack.append(curr)
                curr = curr.left
            if not stack:
                break
            peek = stack[-1]
            if peek.right:                     # <-- no "and peek.right is not last"
                curr = peek.right
            else:
                out.append(peek.val)
                stack.pop()
        return out


# ==============================================================================
# TEST HELPERS — standard tree kit (documented in 001)
# ==============================================================================
def build(values):
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


def build_skewed(n, side="left"):
    if n == 0:
        return None
    root = TreeNode(0)
    curr = root
    for i in range(1, n):
        node = TreeNode(i)
        if side == "left":
            curr.left = node
        else:
            curr.right = node
        curr = node
    return root


def random_tree(n, rng):
    if n == 0:
        return None
    root = TreeNode(rng.randrange(100))
    nodes = [root]
    for _ in range(n - 1):
        parent = rng.choice(nodes)
        while parent.left is not None and parent.right is not None:
            parent = rng.choice(nodes)
        node = TreeNode(rng.randrange(100))
        if parent.left is None and (parent.right is not None or rng.random() < 0.5):
            parent.left = node
        else:
            parent.right = node
        nodes.append(node)
    return root


# ==============================================================================
# TESTS — run:  python 003_binary_tree_postorder_traversal_solution.py
# ==============================================================================
CASES = [
    ([1, None, 2, 3], [3, 2, 1]),
    ([], []),
    ([1], [1]),
    ([4, 2, 6, 1, 3, 5, 7], [1, 3, 2, 5, 7, 6, 4]),
    ([1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9], [4, 6, 7, 5, 2, 9, 8, 3, 1]),
    ([1, 2], [2, 1]),
    ([1, None, 2], [2, 1]),
    ([1, None, 2, None, 3], [3, 2, 1]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: recursion ---")
    for values, want in CASES:
        got = sol.postorderTraversal(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<46} -> {got}  (want {want})")

    print("\n--- correctness: all four iterative variants ---")
    impls = [
        ("reversed preorder      ", sol.postorderTraversal_reversed_preorder),
        ("two stacks             ", sol.postorderTraversal_two_stacks),
        ("one stack + last_visited", sol.postorderTraversal_last_visited),
        ("(node, expanded) flags ", sol.postorderTraversal_flags),
    ]
    for name, fn in impls:
        ok = all(fn(build(v)) == want for v, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- randomised cross-check: all five agree on 400 random trees ---")
    rng = random.Random(145)
    mismatches = 0
    for _ in range(400):
        t = random_tree(rng.randint(0, 60), rng)
        want = sol.postorderTraversal(t)
        if any(fn(t) != want for _, fn in impls):
            mismatches += 1
    print(f"  400 random trees: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # trace: the last_visited mechanism.
    # ----------------------------------------------------------------------
    print("\n--- trace: last_visited postorder of [1,2,3] ---")
    out, stack, curr, last = [], [], build([1, 2, 3]), None
    print(f"  {'curr':>5} {'stack':<10} {'last':>5} {'peek':>5}  decision")
    while curr or stack:
        if curr:
            print(f"  {curr.val:>5} {str([n.val for n in stack]):<10} "
                  f"{str(last.val if last else None):>5} {'-':>5}  dive: push {curr.val}")
            stack.append(curr)
            curr = curr.left
            continue
        peek = stack[-1]
        if peek.right and peek.right is not last:
            print(f"  {'None':>5} {str([n.val for n in stack]):<10} "
                  f"{str(last.val if last else None):>5} {peek.val:>5}  "
                  f"right={peek.right.val} not last -> go right")
            curr = peek.right
        else:
            out.append(peek.val)
            last = stack.pop()
            print(f"  {'None':>5} {str([n.val for n in stack] + [last.val]):<10} "
                  f"{str(last.val):>5} {peek.val:>5}  record {peek.val} -> out={out}")
    print(f"  done: {out}")

    # ----------------------------------------------------------------------
    # ⚠️  The two ways to get the trick wrong.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the reversed-preorder trick, mis-executed ---")
    values = [1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9]
    want = sol.postorderTraversal(build(values))
    no_rev = sol.post_broken_no_reverse(build(values))
    wrong_push = sol.post_broken_wrong_push_then_reverse(build(values))
    print(f"  tree                         : {values}")
    print(f"  correct postorder             : {want}")
    print(f"  forgot out.reverse()          : {no_rev}   <- (node,right,left)")
    print(f"  kept preorder's push order    : {wrong_push}   <- (right,left,node)")
    print(f"  both wrong, both n values long: "
          f"{no_rev != want and wrong_push != want and len(no_rev) == len(want)}")
    shapes = [("left chain", build_skewed(4, "left")),
              ("right chain", build_skewed(4, "right")),
              ("single node", build([7]))]
    print("  which shapes hide the missing reverse?")
    for label, tree in shapes:
        ref = sol.postorderTraversal(tree)
        hidden = sol.post_broken_no_reverse(tree) == ref
        print(f"    {label:<12} correct={str(ref):<16} bug hidden? {hidden}")
    print("  Only a single node hides it: (node,right,left) equals")
    print("  (left,right,node) for exactly one node and no other shape — so")
    print("  ANY two-node test catches this one. The push-order mistake above")
    print("  is the dangerous one, because it survives more shapes.")
    all_ok &= (no_rev != want and wrong_push != want)

    print("\n--- ⚠️  live demo: last_visited without the `is not last` guard ---")
    capped = sol.post_broken_no_last_guard(build([1, None, 2]), cap=50)
    print(f"  tree [1,null,2] (a node with only a RIGHT child)")
    print(f"  correct              : {sol.postorderTraversal(build([1, None, 2]))}")
    print(f"  no `is not last` test: {capped}  (step-capped at 50)")
    print(f"  it never records the root — it keeps descending into 2: "
          f"{capped != sol.postorderTraversal(build([1, None, 2]))}")
    all_ok &= (capped != sol.postorderTraversal(build([1, None, 2])))

    # ----------------------------------------------------------------------
    # ⚠️  THE point of this file: the trick's VISIT order is top-down.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the trick gives postorder VALUES, not postorder VISITS ---")
    print("  Task: write each node's subtree sum into the node, using only")
    print("  already-computed children (the classic bottom-up job).")

    def annotate_in_visit_order(root, visit_sequence):
        """Set node.total = node.val + children's totals, in the given order."""
        for node in visit_sequence:
            left = node.left.total if node.left is not None else 0
            right = node.right.total if node.right is not None else 0
            node.total = node.val + left + right

    def visit_order_trick(root):
        """Node objects in the order the reversed-preorder trick TOUCHES them."""
        seq, stack = [], [root]
        while stack:
            node = stack.pop()
            seq.append(node)
            node.total = 0
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
        return seq

    def visit_order_true_postorder(root):
        """Node objects in true postorder (the last_visited walk)."""
        seq, stack, curr, last = [], [], root, None
        while curr or stack:
            while curr:
                stack.append(curr)
                curr.total = 0
                curr = curr.left
            peek = stack[-1]
            if peek.right and peek.right is not last:
                curr = peek.right
            else:
                seq.append(peek)
                last = stack.pop()
        return seq

    sums_tree = [1, 2, 3, 4, 5, 6, 7]        # complete tree, total sum 28
    t_trick = build(sums_tree)
    annotate_in_visit_order(t_trick, visit_order_trick(t_trick))
    t_true = build(sums_tree)
    annotate_in_visit_order(t_true, visit_order_true_postorder(t_true))
    print(f"  tree {sums_tree}, true subtree sums = [28, 11, 16, 4, 5, 6, 7]")
    print(f"  reversed-preorder VISIT order: root.total = {t_trick.total}, "
          f"left.total = {t_trick.left.total}   <- WRONG")
    print(f"  true postorder VISIT order   : root.total = {t_true.total}, "
          f"left.total = {t_true.left.total}   <- correct")
    print(f"  yet both emit the same postorder LIST: "
          f"{sol.postorderTraversal_reversed_preorder(build(sums_tree)) == sol.postorderTraversal_last_visited(build(sums_tree))}")
    print("  The trick reverses the OUTPUT, not the traversal. When the work at")
    print("  a node needs its children's results (009, 010, 018) you need a true")
    print("  postorder visit: the recursion, or the last_visited loop.")
    all_ok &= (t_true.total == 28 and t_trick.total != 28)

    # ----------------------------------------------------------------------
    # Peak stack: postorder has no cheap skew direction.
    # ----------------------------------------------------------------------
    print("\n--- peak stack size, postorder vs preorder, n = 2000 ---")
    print(f"  {'shape':<20} {'postorder peak':>15} {'preorder peak':>14}")
    for label, side in (("left-skewed", "left"), ("right-skewed", "right")):
        t = build_skewed(2000, side)
        # postorder (last_visited) peak
        stack, curr, last, peak = [], t, None, 0
        while curr or stack:
            while curr:
                stack.append(curr)
                peak = max(peak, len(stack))
                curr = curr.left
            peek = stack[-1]
            if peek.right and peek.right is not last:
                curr = peek.right
            else:
                last = stack.pop()
        # preorder peak
        pre_stack, pre_peak = [t], 0
        while pre_stack:
            pre_peak = max(pre_peak, len(pre_stack))
            node = pre_stack.pop()
            if node.right:
                pre_stack.append(node.right)
            if node.left:
                pre_stack.append(node.left)
        print(f"  {label:<20} {peak:>15} {pre_peak:>14}")
    print("  Preorder can discard a node the moment it is recorded, so a chain")
    print("  costs it O(1). Postorder must keep every ancestor alive until its")
    print("  subtrees finish, so both chains cost O(n). That asymmetry is worth")
    print("  a sentence in an interview — it is why postorder is the expensive")
    print("  traversal to make iterative.")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: the three iterative forms, measured.
    # ----------------------------------------------------------------------
    print("\n--- measured: recursion vs reversed-preorder vs last_visited vs flags ---")
    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        bench_rng = random.Random(7)
        print(f"  {'n':>7} {'recursive':>11} {'rev-preorder':>14} "
              f"{'last_visited':>14} {'flags':>11}")
        for n in (5_000, 20_000, 50_000):
            t = random_tree(n, bench_rng)
            reps = 5
            times = []
            for fn in (sol.postorderTraversal,
                       sol.postorderTraversal_reversed_preorder,
                       sol.postorderTraversal_last_visited,
                       sol.postorderTraversal_flags):
                t0 = time.perf_counter()
                for _ in range(reps):
                    fn(t)
                times.append((time.perf_counter() - t0) / reps * 1000)
            print(f"  {n:>7} {times[0]:>9.2f}ms {times[1]:>12.2f}ms "
                  f"{times[2]:>12.2f}ms {times[3]:>9.2f}ms")
        print("  The four-line trick is the fastest AND the easiest to remember,")
        print("  which is why it is the popular answer. It is also the one that")
        print("  cannot be used for bottom-up work — say both halves out loud.")
    finally:
        sys.setrecursionlimit(saved)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
