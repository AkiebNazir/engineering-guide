"""
================================================================================
SOLUTION · LeetCode 226 · Invert Binary Tree                            [Easy]
https://leetcode.com/problems/invert-binary-tree/
================================================================================

THE CORE IDEA
--------------
At every node, swap the two CHILD REFERENCES. Nothing else.

    def invertTree(root):
        if not root:
            return None
        root.left, root.right = root.right, root.left     # the whole algorithm
        self.invertTree(root.left)
        self.invertTree(root.right)
        return root

O(n) time, O(h) space. What makes this problem instructive is what it does
NOT need: the swap at a node depends on no other node's result, so the
traversal order is free — preorder, postorder and level order all give the
same tree. This is the only problem in 001-012 with that property. From 005
onwards, every problem needs a child's answer before the parent can answer,
and the order stops being free.

Two related traps, both about doing the swap in two steps instead of one:

    node.left = node.right        # left is now the OLD right
    node.right = node.left        # ... and right is now the NEW left = OLD right

The subtree that used to be on the left is gone and both sides point at the
same object. Python's tuple assignment `a, b = b, a` evaluates the whole
right-hand side into a temporary tuple before assigning, so the one-line form
is safe. Its recursive twin is the same bug in disguise:

    node.left = invert(node.right)
    node.right = invert(node.left)     # ✗ reads the value just written

and it is measured live below — the result contains the same node object in
several places at once, which is not even a tree any more.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): serialise the tree to a level-order list,
reverse each level, rebuild. O(n) time but O(n) extra space, and rebuilding a
tree from a level-order list with gaps is fiddly enough that people get it
wrong. It also allocates n new nodes to achieve what n pointer swaps do in
place. Name it, price it, move on.

Approach 1 (recursion, swap then descend) ✅ — the shape above.
   O(n) time, O(h) space, in place.

Approach 2 (recursion, descend then swap) ✅ — postorder instead of
   preorder. Identical result. Useful in an interview to say out loud "the
   order doesn't matter here, and here is why", because that is the actual
   insight being tested.

Approach 3 (iterative BFS with a deque) ✅ — pop a node, swap, push both
   children. O(n) time, O(w) space where w is the widest level (up to ~n/2 on
   a complete tree — WIDER than the recursion's O(h) = O(log n) on the same
   tree, so BFS is not automatically the cheaper choice).

Approach 4 (iterative DFS with a stack) ✅ — the same loop with `pop()`
   instead of `popleft()`. O(n) time, O(h) space. This is the version to
   reach for when the tree may be 10^5 nodes deep, since the recursion dies
   at ~1000 frames (demoed below).

Approach 5 (pure function, no mutation) — build a NEW tree instead:
   `return TreeNode(root.val, invert_copy(root.right), invert_copy(root.left))`.
   O(n) time, O(n) space, and it leaves the caller's tree untouched. Worth
   offering when the interviewer says the input is shared or immutable; it is
   also exactly the shape of "mirror" used by problem 012.


================================================================================
STEP BY STEP TRACE — preorder invert of [4,2,7,1,3,6,9]
================================================================================
            4                          4
          ╱   ╲                      ╱   ╲
         2     7                    7     2
        ╱ ╲   ╱ ╲                  ╱ ╲   ╱ ╲
       1   3 6   9                9   6 3   1

    visit 4: swap children      -> 4.left=7, 4.right=2
      visit 7 (now the left):    swap -> 7.left=9, 7.right=6
        visit 9: no children, nothing to swap
        visit 6: no children, nothing to swap
      visit 2 (now the right):   swap -> 2.left=3, 2.right=1
        visit 3: nothing
        visit 1: nothing

    Level order after each step:
        start                 [4, 2, 7, 1, 3, 6, 9]
        after swapping at 4   [4, 7, 2, 6, 9, 1, 3]    <- subtrees moved whole
        after swapping at 7   [4, 7, 2, 9, 6, 1, 3]
        after swapping at 2   [4, 7, 2, 9, 6, 3, 1]    <- the answer

    Note the middle line: swapping at 4 moves node 7 and *everything under
    it* to the left in one assignment. References move subtrees; the values
    inside them are never touched.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time  Space (aux)  Mutates input?  Note
    ---------------------------  ----  -----------  --------------  --------------------
    Serialise, reverse, rebuild  O(n)  O(n)         no              allocates n nodes
    Recursion, swap-then-descend O(n)  O(h)         YES             the answer
    Recursion, descend-then-swap O(n)  O(h)         YES             same result
    Iterative BFS (deque)        O(n)  O(w)         YES             w up to ~n/2
    Iterative DFS (stack)        O(n)  O(h)         YES             no recursion limit
    Pure copy (no mutation)      O(n)  O(n)         no              for shared trees

    h = height, w = widest level. On a COMPLETE tree, h = log n but
    w = (n+1)/2, so the BFS version uses vastly more memory than the DFS one —
    the demo below measures the peak worklist size of both, and it is a good
    answer to "which iterative version would you pick?".


================================================================================
EDGE CASES
================================================================================
    root = None       -> None       must return None, not crash; the recursion's
                                      base case doubles as the answer.
    single node        -> unchanged   both children are None, the swap is a no-op.
    one-sided node      -> [1,2] becomes [1,null,2]: the None participates in
                          the swap. Code that only swaps "when both children
                          exist" leaves these nodes un-mirrored.
    perfectly symmetric tree -> comes back IDENTICAL. This makes symmetric
                          trees useless as a test case for this problem (and is
                          the basis of problem 012 — see the demo).
    duplicate values     -> irrelevant; only references move.
    tree of 10^5 in a chain -> RecursionError for the recursive version;
                          the stack version is fine. Demoed below.


================================================================================
COMMON MISTAKES
================================================================================
1. Swapping in two statements instead of one:
       node.left = node.right ; node.right = node.left
   Both sides end up pointing at the ORIGINAL right subtree and the original
   left subtree is dropped. In Python, `a, b = b, a` is the fix and it is the
   idiom for a reason.
2. The recursive version of the same bug:
       node.left = invert(node.right) ; node.right = invert(node.left)
   The second call re-inverts the subtree the first line just installed, and
   both fields end up referencing the same node objects. The demo prints the
   resulting level order (`[4, 7, 7, 9, 9, 9, 9]` on the LeetCode example) and
   shows, by object identity, that one node now appears twice in the tree.
3. Swapping the VALUES instead of the children (`a.val, b.val = b.val, a.val`
   across the two subtrees). That only mirrors a perfectly-shaped tree; on any
   tree with an asymmetric shape it produces something that is not a mirror at
   all, because the structure never moved.
4. Forgetting to `return root`. LeetCode's signature returns the tree, and a
   `None` return makes every test fail even though the mutation was correct.
5. Guarding the swap with `if node.left and node.right:` — one-sided nodes
   then keep their orientation. Swap unconditionally; `None` swaps fine.
6. Doing it in place when the interviewer said the tree is shared/read-only.
   Say "this mutates the input" out loud and offer Approach 5.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Now do it iteratively.
A: Approaches 3/4 — one worklist, swap on pop, push children. Volunteer that
   the stack version needs O(h) and the queue version O(w), and that on a wide
   tree those are very different numbers.

Q: Does the traversal order matter?
A: No, and that is the point: the swap at a node is independent of every other
   node's result. Contrast it with 005/009/010, where the parent needs the
   children's answers, so the order becomes forced (postorder).

Q: Do it without mutating the input.
A: Approach 5 — build new nodes with the children crossed over. O(n) space.

Q: How would you check whether a tree is symmetric?
A: Compare the tree with its own inverse — or, better, don't mutate anything
   and run the mirror recursion of problem 012, pairing `(a.left, b.right)`
   and `(a.right, b.left)`. The demo below shows the invert-and-compare
   version working and notes what it costs.

Q: Invert only the bottom k levels / every other level?
A: Same traversal, with the swap made conditional on depth. Passing `depth`
   down is the top-down half of the pattern you will use throughout 005-012.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 101   Symmetric Tree                — mirror-compare, no mutation (012)
    LC 100   Same Tree                     — the un-mirrored twin (007)
    LC 951   Flip Equivalent Binary Trees  — invert only where it helps
    LC 971   Flip Binary Tree To Match Preorder — targeted flips, top-down
    LC 814   Binary Tree Pruning           — same "mutate every node" shape
    LC 617   Merge Two Binary Trees        — two trees, mutate in place
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
    def invertTree(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """Recursion, swap then descend. O(n) time, O(h) space, in place."""
        if not root:
            return None
        root.left, root.right = root.right, root.left    # simultaneous swap
        self.invertTree(root.left)
        self.invertTree(root.right)
        return root

    def invertTree_postorder(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """Recursion, descend then swap. Same result — the order is free."""
        if not root:
            return None
        self.invertTree_postorder(root.left)
        self.invertTree_postorder(root.right)
        root.left, root.right = root.right, root.left
        return root

    def invertTree_bfs(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """Iterative BFS. O(n) time, O(w) space (w = widest level)."""
        if not root:
            return None
        queue = deque([root])
        while queue:
            node = queue.popleft()
            node.left, node.right = node.right, node.left
            if node.left:
                queue.append(node.left)
            if node.right:
                queue.append(node.right)
        return root

    def invertTree_stack(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """Iterative DFS. O(n) time, O(h) space, no recursion limit."""
        if not root:
            return None
        stack = [root]
        while stack:
            node = stack.pop()
            node.left, node.right = node.right, node.left
            if node.left:
                stack.append(node.left)
            if node.right:
                stack.append(node.right)
        return root

    def invert_copy(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """Pure version: builds a new mirrored tree, input untouched.
        O(n) time, O(n) space."""
        if not root:
            return None
        return TreeNode(root.val,
                        self.invert_copy(root.right),
                        self.invert_copy(root.left))

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def invert_broken_two_statements(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — swap in two statements: the second reads the
        field the first just overwrote."""
        if not root:
            return None
        root.left = root.right
        root.right = root.left           # <-- already the new left
        self.invert_broken_two_statements(root.left)
        self.invert_broken_two_statements(root.right)
        return root

    def invert_broken_recursive_alias(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — the same bug wearing recursion's clothes.
        `invert(node.left)` on the second line reads the subtree the FIRST
        line installed, so nodes end up shared between both branches."""
        if not root:
            return None
        root.left = self.invert_broken_recursive_alias(root.right)
        root.right = self.invert_broken_recursive_alias(root.left)
        return root

    def invert_broken_values_only(self, root: Optional[TreeNode]) -> Optional[TreeNode]:
        """✗ BROKEN ON PURPOSE — mirrors the VALUES level by level without
        moving any subtree. Correct on a perfectly-shaped tree, wrong the
        moment the shape is asymmetric."""
        if not root:
            return None
        level = [root]
        while level:
            vals = [n.val for n in level][::-1]
            for node, v in zip(level, vals):
                node.val = v
            nxt = []
            for node in level:
                if node.left:
                    nxt.append(node.left)
                if node.right:
                    nxt.append(node.right)
            level = nxt
        return root


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


def build_complete(n, start=0):
    if n == 0:
        return None
    nodes = [TreeNode(start + i) for i in range(n)]
    for i in range(n):
        if 2 * i + 1 < n:
            nodes[i].left = nodes[2 * i + 1]
        if 2 * i + 2 < n:
            nodes[i].right = nodes[2 * i + 2]
    return nodes[0]


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


def count_distinct_nodes(root, limit=10_000):
    """Number of DISTINCT node objects reachable — detects aliasing/cycles."""
    seen, stack, steps = set(), [root] if root else [], 0
    while stack and steps < limit:
        steps += 1
        node = stack.pop()
        if node is None or id(node) in seen:
            continue
        seen.add(id(node))
        stack.append(node.left)
        stack.append(node.right)
    return len(seen)


def count_slots(root, limit=10_000):
    """Number of child slots filled — if it exceeds the distinct node count,
    some node object is referenced from more than one place."""
    total, stack, steps = 0, [root] if root else [], 0
    while stack and steps < limit:
        steps += 1
        node = stack.pop()
        if node is None:
            continue
        total += 1
        stack.append(node.left)
        stack.append(node.right)
    return total


# ==============================================================================
# TESTS — run:  python 004_invert_binary_tree_solution.py
# ==============================================================================
CASES = [
    ([4, 2, 7, 1, 3, 6, 9], [4, 7, 2, 9, 6, 3, 1]),
    ([2, 1, 3], [2, 3, 1]),
    ([], []),
    ([1], [1]),
    ([1, 2], [1, None, 2]),
    ([1, None, 2, 3], [1, 2, None, None, 3]),
    ([1, 2, 2, 3, 4, 4, 3], [1, 2, 2, 3, 4, 4, 3]),   # symmetric: unchanged
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: recursion (swap then descend) ---")
    for values, want in CASES:
        got = to_level_order(sol.invertTree(build(values)))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<26} -> {got}  (want {want})")

    print("\n--- correctness: the other four implementations ---")
    impls = [
        ("recursion, postorder ", sol.invertTree_postorder),
        ("iterative BFS (deque)", sol.invertTree_bfs),
        ("iterative DFS (stack)", sol.invertTree_stack),
        ("pure copy            ", sol.invert_copy),
    ]
    for name, fn in impls:
        ok = all(to_level_order(fn(build(v))) == want for v, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- randomised cross-check: 400 random trees, all four agree ---")
    rng = random.Random(226)
    mismatches = 0
    for _ in range(400):
        values = to_level_order(random_tree(rng.randint(0, 50), rng))
        want = to_level_order(sol.invertTree(build(values)))
        if any(to_level_order(fn(build(values))) != want for _, fn in impls):
            mismatches += 1
    print(f"  400 random trees: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    print("\n--- property: inverting twice is the identity ---")
    rng = random.Random(2)
    twice_ok = True
    for _ in range(200):
        values = to_level_order(random_tree(rng.randint(0, 40), rng))
        t = build(values)
        sol.invertTree(sol.invertTree(t))
        twice_ok &= (to_level_order(t) == values)
    print(f"  200 random trees: invert(invert(t)) == t  -> {twice_ok}")
    all_ok &= twice_ok

    # ----------------------------------------------------------------------
    # trace: the level order after each swap.
    # ----------------------------------------------------------------------
    print("\n--- trace: [4,2,7,1,3,6,9], one swap at a time (preorder) ---")
    root = build([4, 2, 7, 1, 3, 6, 9])
    print(f"  start                {to_level_order(root)}")
    order = []

    def dfs(node):
        if not node:
            return
        node.left, node.right = node.right, node.left
        order.append(node.val)
        print(f"  after swap at {node.val:<6} {to_level_order(root)}")
        dfs(node.left)
        dfs(node.right)

    dfs(root)
    print(f"  swap order visited: {order}")
    print(f"  final              {to_level_order(root)}  "
          f"(want [4, 7, 2, 9, 6, 3, 1])")
    all_ok &= (to_level_order(root) == [4, 7, 2, 9, 6, 3, 1])

    # ----------------------------------------------------------------------
    # ⚠️  Two-statement swap and its recursive twin.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: swapping in two statements ---")
    values = [4, 2, 7, 1, 3, 6, 9]
    good = to_level_order(sol.invertTree(build(values)))
    bad = to_level_order(sol.invert_broken_two_statements(build(values)))
    print(f"  input                        : {values}")
    print(f"  a, b = b, a (one statement)  : {good}   <- correct")
    print(f"  a = b then b = a (two lines) : {bad}   <- WRONG")
    print(f"  the original left subtree is gone: {2 not in bad or bad.count(7) > 1}")
    all_ok &= (bad != good)

    print("\n--- ⚠️  live demo: node.left = invert(node.right); node.right = invert(node.left) ---")
    aliased = sol.invert_broken_recursive_alias(build(values))
    lvl = to_level_order(aliased)
    distinct = count_distinct_nodes(aliased)
    slots = count_slots(aliased)
    print(f"  correct                : {good}")
    print(f"  reads the new .left    : {lvl}   <- WRONG")
    print(f"  distinct node OBJECTS reachable: {distinct}")
    print(f"  child slots filled              : {slots}")
    print(f"  so {slots - distinct} slot(s) point at a node that is already "
          f"somewhere else in the 'tree': {slots > distinct}")
    print("  This is not a wrong tree — it is not a tree at all: the same node")
    print("  object hangs off two parents. In C++ that is a double free; in")
    print("  Python it is a silently shared subtree that mutations will corrupt.")
    all_ok &= (lvl != good and slots > distinct)

    print("\n--- ⚠️  live demo: mirroring the VALUES instead of the subtrees ---")
    shaped = [1, 2, 3, 4]                     # asymmetric shape: 4 hangs off 2
    want_struct = to_level_order(sol.invertTree(build(shaped)))
    got_values = to_level_order(sol.invert_broken_values_only(build(shaped)))
    print(f"  input                 : {shaped}")
    print(f"  swap child references : {want_struct}   <- correct")
    print(f"  swap values per level : {got_values}   <- WRONG: the shape never moved")
    sym = [1, 2, 2, 3, 4, 4, 3]
    print(f"  and on a perfectly-shaped tree {sym} the value-swap looks right: "
          f"{to_level_order(sol.invert_broken_values_only(build(sym))) == to_level_order(sol.invertTree(build(sym)))}")
    all_ok &= (got_values != want_struct)

    # ----------------------------------------------------------------------
    # Peak worklist: BFS is O(w), DFS is O(h) — a real difference.
    # ----------------------------------------------------------------------
    print("\n--- peak worklist size: BFS O(w) vs DFS O(h), complete tree n = 8191 ---")
    root = build_complete(8191)
    q, peak_bfs = deque([root]), 0
    while q:
        peak_bfs = max(peak_bfs, len(q))
        node = q.popleft()
        node.left, node.right = node.right, node.left
        if node.left:
            q.append(node.left)
        if node.right:
            q.append(node.right)
    root = build_complete(8191)
    st, peak_dfs = [root], 0
    while st:
        peak_dfs = max(peak_dfs, len(st))
        node = st.pop()
        node.left, node.right = node.right, node.left
        if node.left:
            st.append(node.left)
        if node.right:
            st.append(node.right)
    print(f"  BFS peak queue : {peak_bfs:>6}   (~n/2, the widest level)")
    print(f"  DFS peak stack : {peak_dfs:>6}   (~h, the height)")
    print(f"  ratio          : {peak_bfs / peak_dfs:>6.0f}x more memory for BFS")
    print("  'Iterative' does not mean 'cheaper'. For a wide tree the stack is")
    print("  the right worklist; for a deep one BFS is what saves you.")
    all_ok &= (peak_bfs > peak_dfs)

    # ----------------------------------------------------------------------
    # Recursion limit, and the iterative escape.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  a 10,000-node chain: recursion vs stack ---")
    deep = build_skewed(10_000, "left")
    raised = False
    try:
        sol.invertTree(deep)
        print("  recursive: did NOT raise (limit not reached this run)")
    except RecursionError:
        raised = True
        print(f"  recursive: RecursionError at limit {sys.getrecursionlimit()} "
              f"— and the tree is now HALF-INVERTED, not restored")
    deep = build_skewed(10_000, "left")
    sol.invertTree_stack(deep)
    # A left chain inverted becomes a right chain.
    node, seen = deep, 0
    while node:
        seen += 1
        node = node.right
    print(f"  stack    : inverted the whole chain; left-chain became a "
          f"right-chain of {seen} nodes: {seen == 10_000}")
    print("  Note the extra hazard: the recursive version raised PART WAY")
    print("  THROUGH, so the caller's tree is left in a mixed state. In-place")
    print("  mutation plus an exception is a bad combination — another argument")
    print("  for the iterative version (or for the pure copy).")
    all_ok &= (raised and seen == 10_000)

    # ----------------------------------------------------------------------
    # The link to 012: a symmetric tree is its own inverse.
    # ----------------------------------------------------------------------
    print("\n--- the link to 012: symmetric  <=>  tree equals its own inverse ---")
    for values in ([1, 2, 2, 3, 4, 4, 3], [1, 2, 2, None, 3, None, 3], [1, 2, 3]):
        original = to_level_order(build(values))
        inverted = to_level_order(sol.invert_copy(build(values)))
        print(f"  {str(values):<32} inverse == original ? {inverted == original}")
    print("  That is a correct O(n)-time solution to LC 101 — but it costs O(n)")
    print("  extra space for the copy (or mutates the input if you invert in")
    print("  place). Problem 012 does it with no copy at all, by recursing on")
    print("  PAIRS of nodes: (a.left, b.right) and (a.right, b.left).")

    # ----------------------------------------------------------------------
    # RUNTIME: all four in-place variants, measured.
    # ----------------------------------------------------------------------
    print("\n--- measured: recursion vs BFS vs stack vs pure copy ---")
    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        bench_rng = random.Random(7)
        print(f"  {'n':>7} {'recursion':>11} {'BFS':>11} {'stack':>11} {'copy':>11}")
        for n in (5_000, 20_000, 50_000):
            t = random_tree(n, bench_rng)
            reps = 5
            times = []
            for fn in (sol.invertTree, sol.invertTree_bfs,
                       sol.invertTree_stack, sol.invert_copy):
                t0 = time.perf_counter()
                for _ in range(reps):
                    fn(t)
                times.append((time.perf_counter() - t0) / reps * 1000)
            print(f"  {n:>7} " + " ".join(f"{ms:>9.2f}ms" for ms in times))
        print("  All four are O(n) and the spread is a constant factor: the two")
        print("  worklist loops avoid Python function calls, and the pure copy")
        print("  pays for n object allocations. Nothing here changes the")
        print("  asymptotics — the interesting axis in this problem is SPACE.")
    finally:
        sys.setrecursionlimit(saved)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
