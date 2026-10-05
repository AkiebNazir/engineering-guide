"""
================================================================================
SOLUTION · LeetCode 94 · Binary Tree Inorder Traversal                  [Easy]
https://leetcode.com/problems/binary-tree-inorder-traversal/
================================================================================

THE CORE IDEA
--------------
Same recursion as 001 with the record step moved between the two descents:

    def dfs(node):
        if not node: return
        dfs(node.left)            # LEFT
        out.append(node.val)      # NODE   <- inorder puts it HERE
        dfs(node.right)           # RIGHT

Why this order is the one worth memorising: **inorder on a Binary Search Tree
emits the values in ascending order.** That single fact is the engine behind
most of topic 11 (LC 98, 230, 173, 530, 700...). If you can produce an inorder
walk from memory, iteratively, you can solve those on the spot.

The iterative form is genuinely different from preorder's, because a node
cannot be recorded when first met — its left subtree is still unwalked. So
the loop alternates between "dive left, pushing everything" and "pop one,
record it, then owe its right subtree the same treatment":

    curr, stack, out = root, [], []
    while curr or stack:
        while curr:                  # dive down the LEFT SPINE, pushing
            stack.append(curr)
            curr = curr.left
        curr = stack.pop()           # its left subtree is provably finished
        out.append(curr.val)
        curr = curr.right             # start over from the right child
    return out

O(n) time, O(h) space. The stack holds exactly the ancestors whose value has
not been emitted yet — the same set the call stack holds in the recursion.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): collect the values with any traversal and
`sorted()` them. This gives the right answer for a BST *by accident* and the
wrong answer for every other tree, since inorder is a structural order, not a
numeric one. Naming this trap is useful: it is the reason a BST question that
"just needs sorted values" is really an inorder question.

Approach 1 (recursion) ✅ — three lines, lead with it. O(n) / O(h).

Approach 2 (one stack, left-spine loop) ✅ — the shape above. O(n) / O(h),
no recursion limit. This is the version to have memorised, because pausing it
mid-flight IS the BST iterator (LC 173): keep `stack` as object state, and
each `next()` does one pop + one left dive.

Approach 3 (Morris traversal) — O(n) time, **O(1) space**, at the price of
temporarily mutating the tree. For each node with a left child, find that
subtree's rightmost node (the inorder PREDECESSOR) and point its unused
`.right` at the current node — a "thread" back up. Follow the thread later to
return without a stack, and unthread on the way through, so the tree is
restored when the walk finishes:

    curr = root
    while curr:
        if curr.left is None:
            out.append(curr.val)        # nothing to the left: emit and go right
            curr = curr.right
        else:
            pred = curr.left
            while pred.right and pred.right is not curr:
                pred = pred.right        # rightmost node of the left subtree
            if pred.right is None:
                pred.right = curr        # THREAD: remember the way back up
                curr = curr.left
            else:
                pred.right = None        # UNTHREAD: left subtree is done
                out.append(curr.val)
                curr = curr.right

    Each edge is walked at most three times, so still O(n) — but in CPython it
    measures SLOWER than the stack version (the benchmark below finds roughly
    1.5x), because the extra predecessor walks cost more than `list.append`.
    Morris is an answer to "O(1) space", not to "make it fast", and it is
    unusable if the tree is shared with another thread or must not be written
    to at all.

Approach 4 (a "visited" flag per node, or a stack of (node, bool) pairs) —
push `(node, False)`, and on pop either re-push `(node, True)` between its
children or emit. O(n) time, O(n) space, and it generalises to all three
orders with the record position as data. Slower and bulkier; useful mainly as
the "one loop, any order" party trick (see 003, where it is the honest
one-stack postorder).


================================================================================
STEP BY STEP TRACE — the left-spine loop
================================================================================
    Tree [4,2,6,1,3,5,7]:              inorder = 1 2 3 4 5 6 7

              4
            ╱   ╲
           2     6
          ╱ ╲   ╱ ╲
         1   3 5   7

    curr  stack (bottom..top)  action
    ----  --------------------  -----------------------------------------
    4     []                    dive: push 4, curr=2
    2     [4]                   dive: push 2, curr=1
    1     [4,2]                 dive: push 1, curr=None
    None  [4,2,1]               pop 1 -> out=[1], curr=1.right=None
    None  [4,2]                 pop 2 -> out=[1,2], curr=2.right=3
    3     [4]                   dive: push 3, curr=None
    None  [4,3]                 pop 3 -> out=[1,2,3], curr=None
    None  [4]                   pop 4 -> out=[1,2,3,4], curr=4.right=6
    6     []                    dive: push 6, curr=5
    5     [6]                   dive: push 5, curr=None
    None  [6,5]                 pop 5 -> out=[..,5], curr=None
    None  [6]                   pop 6 -> out=[..,6], curr=6.right=7
    7     []                    dive: push 7, curr=None
    None  [7]                   pop 7 -> out=[..,7], curr=None
    None  []                    curr is None AND stack empty -> done

    Watch the loop condition do its job on the last two rows: `curr` is None
    for most of the walk, so `while curr:` alone would have stopped at row 4.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time    Space (aux)  Mutates input?     Note
    ------------------------  ------  -----------  -----------------  --------------------
    Traverse + sorted()       O(n log n) O(n)      no                 WRONG unless BST
    Recursion ✅              O(n)    O(h)         no                 ~1000-frame ceiling
    One stack, left spine ✅  O(n)    O(h)         no                 = LC 173 iterator
    Morris                    O(n)    O(1)         YES, then restores  slower in CPython
    (node, visited) stack     O(n)    O(n)         no                 generalises to all 3

    Morris's "mutates input" is the entry that matters in an interview: it is
    O(1) space only because it writes into the tree it is reading. Say that
    out loud, and say that the tree is left exactly as it was found — the test
    below asserts the restoration.


================================================================================
EDGE CASES
================================================================================
    root = None       -> []       `while curr or stack` never runs a body.
    single node        -> [val]    dives, pushes, pops, records, curr=None, ends.
    left-only chain     -> the entire chain is pushed before anything is emitted:
                          peak stack = n. This is the O(h)=O(n) space case, and
                          the one the recursive version dies on.
    right-only chain     -> emits immediately at every step; peak stack = 1.
                          Inorder and preorder produce the SAME list here, which
                          makes right-chains useless as a test of your ordering.
    BST                  -> sorted output; asserted below.
    duplicate values      -> fine; inorder is structural, ties keep their
                            structural positions.


================================================================================
COMMON MISTAKES
================================================================================
1. `while stack:` or `while curr:` as the loop condition instead of
   `while curr or stack:`. The first exits before the first dive has pushed
   anything (empty output); the second exits the moment a leaf's `.right` is
   None, leaving ancestors stranded on the stack. Both are demoed below.
2. Recording on the way DOWN (`out.append` inside the dive loop) — that is
   preorder, wearing inorder's clothes. It even produces sorted-looking output
   on a left chain, so it can survive a careless test.
3. Forgetting `curr = curr.right` after the pop, or writing `curr = None` —
   the right subtree is then silently dropped. On a BST that shows up as
   "the answer is sorted but missing half the values".
4. In Morris: forgetting the unthread branch (`pred.right = None`). This one
   is measured live below and the result is worse than it sounds: the FIRST
   traversal still returns the correct list, so the bug passes its own test.
   What it leaves behind is a tree with permanent upward edges — a cyclic
   graph — so the *next* thing that touches the tree breaks. In the demo the
   second (correct) Morris run returns 3 of 7 values, and the plain stack walk
   never terminates at all. A "correct output" from Morris is not evidence
   that it unthreaded; assert the tree is unchanged afterwards.
5. In Morris: writing `while pred.right and pred.right != curr`. It happens to
   work here because `TreeNode` does not define `__eq__` (so `!=` falls back to
   identity), but the intent is identity — write `is not curr`. If a subclass
   ever defines value equality, `!=` matches the wrong node.
6. Calling `sorted()` on the output "to be safe". On a BST it hides an ordering
   bug; on a non-BST it invents an answer the problem never asked for.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Do it iteratively.
A: Approach 2. Explain that a node may not be emitted until its left subtree
   is done, which is why the loop has a dive phase and a pop phase.

Q: Do it in O(1) space.
A: Morris (Approach 3). Lead with the caveat: it mutates `.right` pointers
   during the walk and restores them, so it is unsafe on a shared tree.

Q: Now expose it as an iterator with `next()` and `hasNext()` in O(1)
   amortised time and O(h) space.
A: That is LC 173, and it is literally Approach 2 with the `stack` promoted to
   a field: `hasNext()` is `bool(stack)`, `next()` pops, records, and dives
   down the popped node's right child. Implemented below as `BSTIterator`.

Q: The tree is a BST — validate it.
A: LC 98: run inorder and check each value is strictly greater than the
   previous one. Keep only the previous value, not the whole list — O(1) extra.
   Implemented and demonstrated below.

Q: Kth smallest element of a BST?
A: LC 230: the same iterative walk, stopped after k pops. O(h + k), not O(n).


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 144   Preorder Traversal              — record BEFORE descending (001)
    LC 145   Postorder Traversal             — record AFTER both (003)
    LC 98    Validate BST                    — inorder must be increasing (topic 11)
    LC 230   Kth Smallest in a BST           — inorder, stop after k (topic 11)
    LC 173   BST Iterator                    — this stack, paused (topic 11)
    LC 530   Minimum Absolute Difference     — adjacent inorder pairs (topic 11)
    LC 105   Build Tree from Preorder+Inorder — inorder locates the root's split (016)
    LC 99    Recover BST                     — find the two inorder inversions
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
    def inorderTraversal(self, root: Optional[TreeNode]) -> List[int]:
        """Recursion: LEFT, NODE, RIGHT. O(n) time, O(h) space."""
        out: List[int] = []

        def dfs(node: Optional[TreeNode]) -> None:
            if not node:
                return
            dfs(node.left)           # LEFT
            out.append(node.val)     # NODE
            dfs(node.right)          # RIGHT

        dfs(root)
        return out

    def inorderTraversal_iterative(self, root: Optional[TreeNode]) -> List[int]:
        """One stack, left-spine loop. O(n) time, O(h) space. Memorise this —
        it is also the BST iterator of LC 173."""
        out: List[int] = []
        stack: List[TreeNode] = []
        curr = root
        while curr or stack:
            while curr:                  # dive left, pushing everything
                stack.append(curr)
                curr = curr.left
            curr = stack.pop()           # left subtree finished
            out.append(curr.val)
            curr = curr.right             # owe the right subtree the same
        return out

    def inorderTraversal_morris(self, root: Optional[TreeNode]) -> List[int]:
        """Morris traversal. O(n) time, O(1) space, temporarily rewires
        `.right` pointers and restores every one of them."""
        out: List[int] = []
        curr = root
        while curr:
            if curr.left is None:
                out.append(curr.val)
                curr = curr.right
            else:
                pred = curr.left
                while pred.right and pred.right is not curr:
                    pred = pred.right     # rightmost node of the left subtree
                if pred.right is None:
                    pred.right = curr     # THREAD back up
                    curr = curr.left
                else:
                    pred.right = None     # UNTHREAD: left subtree done
                    out.append(curr.val)
                    curr = curr.right
        return out

    def inorderTraversal_visited_flags(self, root: Optional[TreeNode]) -> List[int]:
        """(node, already_expanded) stack. O(n) time, O(n) space. The shape
        that generalises to all three orders by moving one push."""
        out: List[int] = []
        stack = [(root, False)] if root else []
        while stack:
            node, expanded = stack.pop()
            if node is None:
                continue
            if expanded:
                out.append(node.val)
            else:
                stack.append((node.right, False))
                stack.append((node, True))       # record position = inorder
                stack.append((node.left, False))
        return out

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def inorder_broken_loop_condition(self, root: Optional[TreeNode]) -> List[int]:
        """✗ BROKEN ON PURPOSE — `while curr` instead of `while curr or stack`.
        Stops as soon as a node's right child is None, abandoning every
        ancestor still parked on the stack."""
        out: List[int] = []
        stack: List[TreeNode] = []
        curr = root
        while curr:                     # <-- the bug
            while curr:
                stack.append(curr)
                curr = curr.left
            curr = stack.pop()
            out.append(curr.val)
            curr = curr.right
        return out

    def inorder_broken_record_on_the_way_down(self, root: Optional[TreeNode]) -> List[int]:
        """✗ BROKEN ON PURPOSE — records during the dive, which is preorder."""
        out: List[int] = []
        stack: List[TreeNode] = []
        curr = root
        while curr or stack:
            while curr:
                out.append(curr.val)     # <-- recorded too early
                stack.append(curr)
                curr = curr.left
            curr = stack.pop().right
        return out


class BSTIterator:
    """LC 173, for free: the iterative inorder walk with its stack promoted to
    object state. next() is O(1) amortised, space is O(h)."""

    def __init__(self, root: Optional[TreeNode]):
        self.stack: List[TreeNode] = []
        self._dive(root)

    def _dive(self, node: Optional[TreeNode]) -> None:
        while node:
            self.stack.append(node)
            node = node.left

    def hasNext(self) -> bool:
        return bool(self.stack)

    def next(self) -> int:
        node = self.stack.pop()
        self._dive(node.right)
        return node.val


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


def bst_from_sorted(values):
    """Balanced BST from a sorted list — so inorder is guaranteed sorted."""
    if not values:
        return None
    mid = len(values) // 2
    return TreeNode(values[mid],
                    bst_from_sorted(values[:mid]),
                    bst_from_sorted(values[mid + 1:]))


# ==============================================================================
# TESTS — run:  python 002_binary_tree_inorder_traversal_solution.py
# ==============================================================================
CASES = [
    ([1, None, 2, 3], [1, 3, 2]),
    ([], []),
    ([1], [1]),
    ([4, 2, 6, 1, 3, 5, 7], [1, 2, 3, 4, 5, 6, 7]),
    ([1, 2, 3, 4, 5, None, 8, None, None, 6, 7, 9], [4, 2, 6, 5, 7, 1, 3, 9, 8]),
    ([1, 2], [2, 1]),
    ([1, None, 2], [1, 2]),
    ([3, 1, None, None, 2], [1, 2, 3]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: recursion ---")
    for values, want in CASES:
        got = sol.inorderTraversal(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}  (want {want})")

    print("\n--- correctness: the other three implementations ---")
    impls = [
        ("iterative (left spine) ", sol.inorderTraversal_iterative),
        ("Morris (O(1) space)    ", sol.inorderTraversal_morris),
        ("(node, visited) stack  ", sol.inorderTraversal_visited_flags),
    ]
    for name, fn in impls:
        ok = all(fn(build(v)) == want for v, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- randomised cross-check: all four agree on 400 random trees ---")
    rng = random.Random(94)
    mismatches = 0
    for _ in range(400):
        t = random_tree(rng.randint(0, 60), rng)
        a = sol.inorderTraversal(t)
        if (sol.inorderTraversal_iterative(t) != a
                or sol.inorderTraversal_morris(t) != a
                or sol.inorderTraversal_visited_flags(t) != a):
            mismatches += 1
    print(f"  400 random trees: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # trace: the left-spine loop.
    # ----------------------------------------------------------------------
    print("\n--- trace: iterative inorder of [4,2,6,1,3,5,7] ---")
    curr, stack, out = build([4, 2, 6, 1, 3, 5, 7]), [], []
    print(f"  {'curr':>5}  {'stack':<14} action")
    while curr or stack:
        cv = curr.val if curr else None
        if curr:
            print(f"  {str(cv):>5}  {str([n.val for n in stack]):<14} dive: push {cv}")
            stack.append(curr)
            curr = curr.left
            continue
        node = stack.pop()
        out.append(node.val)
        curr = node.right
        print(f"  {str(cv):>5}  {str([n.val for n in stack] + [node.val]):<14} "
              f"pop {node.val} -> out={out}")
    print(f"  done: {out}")

    # ----------------------------------------------------------------------
    # ⚠️  Why the loop condition is `curr or stack`.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: `while curr` instead of `while curr or stack` ---")
    values = [4, 2, 6, 1, 3, 5, 7]
    good = sol.inorderTraversal_iterative(build(values))
    bad = sol.inorder_broken_loop_condition(build(values))
    print(f"  tree              : {values}")
    print(f"  while curr or stack: {good}   <- correct")
    print(f"  while curr         : {bad}   <- WRONG: quit with nodes still on the stack")
    print(f"  values silently lost: {len(good) - len(bad)}")
    all_ok &= (len(bad) < len(good))

    print("\n--- ⚠️  live demo: recording during the DIVE gives preorder, not inorder ---")
    bad2 = sol.inorder_broken_record_on_the_way_down(build(values))
    print(f"  record on the way down: {bad2}")
    print(f"  that is the preorder of the same tree: "
          f"{bad2 == [4, 2, 1, 3, 6, 5, 7]}")
    bug_right = sol.inorder_broken_record_on_the_way_down(build_skewed(5, "right"))
    ok_right = sol.inorderTraversal_iterative(build_skewed(5, "right"))
    print(f"  on a RIGHT chain the bug is INVISIBLE: broken={bug_right} "
          f"correct={ok_right} equal={bug_right == ok_right}")
    bug_left = sol.inorder_broken_record_on_the_way_down(build_skewed(5, "left"))
    ok_left = sol.inorderTraversal_iterative(build_skewed(5, "left"))
    print(f"  on a LEFT chain it is exactly backwards: broken={bug_left} "
          f"correct={ok_left}")
    print("  So a right-skewed test case proves nothing about your ordering —")
    print("  preorder and inorder agree on it. Always test a LEFT-leaning tree.")
    all_ok &= (bug_right == ok_right and bug_left != ok_left)
    all_ok &= (bad2 == [4, 2, 1, 3, 6, 5, 7])

    # ----------------------------------------------------------------------
    # Morris: the tree really is mutated mid-flight, and really is restored.
    # ----------------------------------------------------------------------
    print("\n--- Morris: mutates the tree mid-walk, then puts it back ---")
    root = build([4, 2, 6, 1, 3, 5, 7])
    before = to_level_order(root)
    # One hand-run step: thread 3 (predecessor of 4) up to 4.
    curr = root
    pred = curr.left
    while pred.right and pred.right is not curr:
        pred = pred.right
    pred.right = curr                       # the thread
    print(f"  before threading : node {pred.val}.right = None")
    print(f"  after  threading : node {pred.val}.right = {pred.right.val}  "
          f"<- an UPWARD edge; the tree is momentarily cyclic")
    walk, seen, node = [], set(), root
    while node and id(node) not in seen and len(walk) < 10:
        seen.add(id(node))
        walk.append(node.val)
        node = node.right
    print(f"  walking .right from the root now revisits: {walk} "
          f"(stopped on a repeat)")
    pred.right = None                        # undo the hand-run step
    after = to_level_order(root)
    full = sol.inorderTraversal_morris(root)
    restored = to_level_order(root)
    print(f"  tree before Morris: {before}")
    print(f"  tree after  Morris: {restored}")
    print(f"  Morris output     : {full}")
    print(f"  structure fully restored: {restored == before == after}")
    all_ok &= (restored == before == after)

    # ----------------------------------------------------------------------
    # ⚠️  Morris without the unthread step never terminates.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: Morris that forgets to unthread — the delayed bomb ---")
    root = build([4, 2, 6, 1, 3, 5, 7])
    out, curr = [], root
    while curr:
        if curr.left is None:
            out.append(curr.val)
            curr = curr.right
        else:
            pred = curr.left
            while pred.right and pred.right is not curr:
                pred = pred.right
            if pred.right is None:
                pred.right = curr
                curr = curr.left
            else:
                # pred.right = None   <-- the missing unthread
                out.append(curr.val)
                curr = curr.right
    print(f"  first run output  : {out}  <- CORRECT, which is what makes this bug nasty")
    leftovers = [(n.val, n.right.val) for n in
                 (root.left.left, root.left.right, root.right.left)
                 if n.right is not None]
    print(f"  leftover upward edges: {leftovers}")
    print(f"  the tree is now a cyclic graph, not a tree: {len(leftovers) == 3}")
    # A SECOND traversal of the same tree is now broken. Step caps so the
    # non-termination can be shown instead of hanging the test run.
    out2, curr, steps, cap = [], root, 0, 40
    while curr and steps < cap:
        steps += 1
        if curr.left is None:
            out2.append(curr.val)
            curr = curr.right
        else:
            pred = curr.left
            while pred.right and pred.right is not curr:
                pred = pred.right
            if pred.right is None:
                pred.right = curr
                curr = curr.left
            else:
                pred.right = None
                out2.append(curr.val)
                curr = curr.right
    print(f"  second run (CORRECT Morris, corrupted tree): {out2}  "
          f"<- {7 - len(out2)} values lost")
    out3, stack, curr, steps = [], [], root, 0
    while (curr or stack) and steps < cap:
        steps += 1
        while curr and steps < cap:
            steps += 1
            stack.append(curr)
            curr = curr.left
        if not stack:
            break
        curr = stack.pop()
        out3.append(curr.val)
        curr = curr.right
    print(f"  the stack version on the corrupted tree, capped at {cap} steps: {out3}")
    print(f"  it never terminates — {out3.count(out3[0])} copies of the same value")
    print("  Lesson: a Morris walk that emits the right answer is NOT evidence")
    print("  that it unthreaded. Verify the tree is unchanged afterwards, which")
    print("  is exactly what the previous demo asserts.")
    all_ok &= (len(leftovers) == 3 and len(out2) < 7 and steps >= cap)

    # ----------------------------------------------------------------------
    # The payoff: inorder of a BST is sorted; LC 98 and LC 173 fall out.
    # ----------------------------------------------------------------------
    print("\n--- the payoff: inorder of a BST is SORTED (LC 98 / 173 / 230) ---")
    bst = bst_from_sorted(list(range(0, 40, 3)))
    walk = sol.inorderTraversal_iterative(bst)
    print(f"  BST level-order : {to_level_order(bst)}")
    print(f"  BST inorder     : {walk}")
    print(f"  sorted?          {walk == sorted(walk)}")
    all_ok &= (walk == sorted(walk))

    non_bst = build([4, 2, 6, 1, 9, 5, 7])   # 9 sits under 2: not a BST
    walk2 = sol.inorderTraversal_iterative(non_bst)
    print(f"  non-BST inorder : {walk2}  sorted? {walk2 == sorted(walk2)}  "
          f"<- the inversion 9 > 4 is exactly what LC 98 looks for")
    all_ok &= (walk2 != sorted(walk2))

    it = BSTIterator(bst)
    pulled = []
    while it.hasNext():
        pulled.append(it.next())
    print(f"  BSTIterator (LC 173) pulls the same sequence lazily: {pulled == walk}")
    all_ok &= (pulled == walk)

    it2 = BSTIterator(bst)
    k = 4
    kth = [it2.next() for _ in range(k)][-1]
    print(f"  kth smallest (k={k}) after only {k} pops, no full walk: {kth} "
          f"(== walk[{k-1}] = {walk[k-1]})  {kth == walk[k-1]}")
    all_ok &= (kth == walk[k - 1])

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(1)-space Morris is not the fast one.
    # ----------------------------------------------------------------------
    print("\n--- measured: recursion vs stack vs Morris vs (node,visited) ---")
    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        bench_rng = random.Random(7)
        print(f"  {'n':>7} {'recursive':>11} {'stack':>11} {'Morris':>11} {'flags':>11}")
        for n in (5_000, 20_000, 50_000):
            t = random_tree(n, bench_rng)
            reps = 5
            times = []
            for fn in (sol.inorderTraversal, sol.inorderTraversal_iterative,
                       sol.inorderTraversal_morris, sol.inorderTraversal_visited_flags):
                t0 = time.perf_counter()
                for _ in range(reps):
                    fn(t)
                times.append((time.perf_counter() - t0) / reps * 1000)
            print(f"  {n:>7} " + " ".join(f"{ms:>9.2f}ms" for ms in times))
        print("  Morris trades O(h) space for O(1) space and PAYS for it in time:")
        print("  every node with a left child triggers a walk down that subtree's")
        print("  right edge to find the predecessor — twice (thread, unthread).")
        print("  It is the answer to 'O(1) space', never the answer to 'faster'.")
    finally:
        sys.setrecursionlimit(saved)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
