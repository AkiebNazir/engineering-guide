"""
================================================================================
SOLUTION · LeetCode 104 · Maximum Depth of Binary Tree                  [Easy]
https://leetcode.com/problems/maximum-depth-of-binary-tree/
================================================================================

THE CORE IDEA
--------------
The longest root-to-leaf path through a node runs down one of its two
subtrees, so the answer for a node is one more than the better of its two
children's answers:

    def maxDepth(root):
        if not root:
            return 0                                        # empty tree: 0 nodes
        return 1 + max(maxDepth(root.left), maxDepth(root.right))

O(n) time (each node answered once), O(h) space (the call stack). Depth is
counted in NODES, so a single node is depth 1 — that `1 +` and the `return 0`
are the whole boundary condition.

This is the topic's canonical **bottom-up** recursion, and it is the right
place to learn the vocabulary that decides problems 009, 010, 011 and 018:

    BOTTOM-UP ("return a value up")     TOP-DOWN ("carry state down")
    ---------------------------------   -----------------------------------
    the child RETURNS a number          the parent PASSES depth as an argument
    the parent COMBINES the numbers     the leaf RECORDS into a nonlocal
    answer emerges at the root          answer accumulates as you descend
    = a postorder traversal (003)       = a preorder traversal (001)

    def top_down(node, depth):          # equally correct here
        nonlocal best
        if not node: return
        best = max(best, depth)
        top_down(node.left, depth + 1)
        top_down(node.right, depth + 1)

For MAX DEPTH the two are interchangeable — both O(n), both O(h). That is
exactly why this is the problem to learn them on. In 009 (balanced) and 010
(diameter) they are NOT interchangeable: the top-down version recomputes
heights and becomes O(n^2), which those files measure at over 1000x.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): enumerate every root-to-leaf path into a
list and take the longest. O(n) paths, each up to O(h) long, so O(n*h) time
and O(n*h) space to materialise paths you immediately throw away. It IS the
right shape for problems that need the paths themselves (LC 257, LC 113), so
name it and say why it is overkill here: you only need the length, and length
composes with a `max`, so nothing needs to be stored.

Approach 1 (bottom-up recursion) ✅ — the two-liner above. O(n) / O(h).
Approach 2 (top-down recursion with a nonlocal) ✅ — same cost here; the
   shape to know because most "collect something along the path" problems
   (011 path sum, 015 good nodes) need it.
Approach 3 (BFS, count levels) ✅ — pop a whole level at a time
   (`for _ in range(len(queue))`) and add one per level. O(n) time, O(w)
   space. This is the version that survives a 10^5-deep tree, and it is the
   template for 013 (level order) and 014 (right side view).
Approach 4 (iterative DFS with a stack of `(node, depth)`) ✅ — O(n) time,
   O(h) space, no recursion limit. Simplest escape hatch when the tree is
   deep AND narrow.


================================================================================
STEP BY STEP TRACE — bottom-up on [3,9,20,null,null,15,7]
================================================================================
            3
          ╱   ╲
         9     20
              ╱  ╲
            15    7

    maxDepth(3)
      maxDepth(9)
        maxDepth(None) -> 0
        maxDepth(None) -> 0
        returns 1 + max(0, 0) = 1
      maxDepth(20)
        maxDepth(15)
          returns 1 + max(0, 0) = 1
        maxDepth(7)
          returns 1 + max(0, 0) = 1
        returns 1 + max(1, 1) = 2
      returns 1 + max(1, 2) = 3          <- the answer

    Values flow UPWARD, one number per node, and each number is computed
    exactly once. That is what "O(n), not O(n^2)" looks like: nobody asks a
    subtree the same question twice.

    The same tree, top-down:

        dfs(3, 1)   best = 1
          dfs(9, 2)    best = 2
          dfs(20, 2)   best = 2
            dfs(15, 3) best = 3
            dfs(7, 3)  best = 3          <- the answer, recorded at the leaves


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time   Space (aux)  Mutates input?  Note
    ---------------------------  -----  -----------  --------------  ----------------
    Enumerate all paths          O(n*h) O(n*h)       no              needed for LC 257
    Bottom-up recursion ✅       O(n)   O(h)         no              the answer
    Top-down recursion ✅        O(n)   O(h)         no              same cost HERE
    BFS by levels ✅             O(n)   O(w)         no              survives deep trees
    Iterative DFS (node, depth) ✅ O(n) O(h)         no              no recursion limit

    h = height, w = widest level. Nothing here mutates the tree, which is why
    all five can be cross-checked against each other on the same object — the
    tests below do exactly that.


================================================================================
EDGE CASES
================================================================================
    root = None      -> 0     the ONLY case where the answer is 0; if your base
                                case returns 1 you will be off by one everywhere.
    single node       -> 1     depth is in NODES, not edges. "1" here is the
                                single most common off-by-one in the topic.
    one-sided node     -> [1,null,2] is 2: `max` naturally ignores the missing
                             side because `maxDepth(None)` is 0. This is exactly
                             where MIN depth breaks (006) — `min(0, 2)` would
                             give 0, and 006 is entirely about that trap.
    left-only chain of 10^4 -> inside the LeetCode constraints, outside the
                             CPython recursion limit. RecursionError, demoed
                             below, with two working escapes.
    perfectly balanced        -> h = log2(n)+1; the recursion is cheap and BFS's
                             O(w) is the expensive one (w ~ n/2).


================================================================================
COMMON MISTAKES
================================================================================
1. Returning `1` for `None` (or forgetting the `1 +`). Both are off-by-one:
   the first makes the empty tree 1 deep, the second makes every tree 0 deep.
   The demo prints both broken variants next to the correct answer.
2. `if not node.left and not node.right: return 1` as a *separate* leaf base
   case, on top of `if not node: return 0`. Harmless duplication here — but it
   is how people end up writing the two base cases inconsistently in 006,
   where the leaf case is genuinely required.
3. Using `min` instead of `max` by muscle memory. It compiles, it returns a
   number, and on a perfect tree it even returns the right one — see the demo,
   where a complete tree gives the same answer for min and max, and an
   asymmetric tree does not.
4. Reaching for `max(depth(l), depth(r))` and then, in 006, reusing
   `min(depth(l), depth(r))`. That is the single most-failed easy tree
   problem; 006 exists to burn it in.
5. Choosing recursion on a tree that may be 10^4 nodes deep without saying
   anything about the recursion limit. LeetCode's own constraint allows it.
6. In the BFS version, forgetting to snapshot `len(queue)` before the inner
   loop (`for _ in range(len(queue))`). If you read `len(queue)` while
   appending to it, levels merge and the count is wrong. Demoed live.
7. Counting depth as EDGES (returning `max(...)` without `1 +`) because the
   phrase "depth of a node" in textbooks often means edges. Read the problem's
   definition; LeetCode 104 counts nodes.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Iteratively?
A: BFS counting levels (Approach 3), or a `(node, depth)` stack (Approach 4).
   Say which space bound each has: O(w) vs O(h).

Q: The tree has 10^5 nodes and might be a straight line. Now what?
A: The recursion raises RecursionError. Use the explicit stack (or BFS), or
   raise `sys.setrecursionlimit` and accept the risk. Demonstrated below.

Q: Minimum depth instead?
A: NOT symmetric — a node with one child is not a leaf, so `min` over a
   missing side is wrong. That is problem 006, and it is the trap that catches
   most people.

Q: Return the deepest LEAF's value, or the whole deepest path?
A: Carry the path top-down (Approach 2 with a list, appending/popping) or
   return `(depth, value)` pairs bottom-up. LC 1123 / LC 257 territory.

Q: Diameter of the tree — the longest path between ANY two nodes?
A: Problem 010. Same postorder skeleton: return the height up, and record
   `left + right` in a nonlocal at every node. The insight is that max depth
   is the sub-computation the diameter is built out of.

Q: How would you compute the depth of an N-ary tree?
A: `1 + max((maxDepth(c) for c in node.children), default=0)` — the `default`
   handles the leaf case, standing in for `maxDepth(None) == 0`.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 111   Minimum Depth of Binary Tree   — the trap version (006 here)
    LC 110   Balanced Binary Tree           — heights + a sentinel (009 here)
    LC 543   Diameter of Binary Tree        — heights + a nonlocal max (010 here)
    LC 124   Binary Tree Maximum Path Sum   — the same shape, Hard (018 here)
    LC 102   Level Order Traversal          — the BFS half of this file (013 here)
    LC 559   Maximum Depth of N-ary Tree    — same recursion, k children
    LC 1123  Lowest Common Ancestor of Deepest Leaves — depth returned upward
================================================================================
"""

import random
import sys
import time
from collections import deque
from typing import Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


class Solution:
    def maxDepth(self, root: Optional[TreeNode]) -> int:
        """Bottom-up recursion. O(n) time, O(h) space. The answer."""
        if not root:
            return 0
        return 1 + max(self.maxDepth(root.left), self.maxDepth(root.right))

    def maxDepth_top_down(self, root: Optional[TreeNode]) -> int:
        """Top-down recursion: carry the depth down, record it in a nonlocal.
        Same O(n) / O(h) here — and the shape 011/015 need."""
        best = 0

        def dfs(node: Optional[TreeNode], depth: int) -> None:
            nonlocal best
            if not node:
                return
            if depth > best:
                best = depth
            dfs(node.left, depth + 1)
            dfs(node.right, depth + 1)

        dfs(root, 1)
        return best

    def maxDepth_bfs(self, root: Optional[TreeNode]) -> int:
        """BFS, one level per iteration. O(n) time, O(w) space. Survives trees
        deeper than the recursion limit."""
        if not root:
            return 0
        queue = deque([root])
        depth = 0
        while queue:
            depth += 1
            for _ in range(len(queue)):        # snapshot the level size FIRST
                node = queue.popleft()
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
        return depth

    def maxDepth_stack(self, root: Optional[TreeNode]) -> int:
        """Iterative DFS over (node, depth) pairs. O(n) time, O(h) space."""
        if not root:
            return 0
        best = 0
        stack = [(root, 1)]
        while stack:
            node, depth = stack.pop()
            if depth > best:
                best = depth
            if node.left:
                stack.append((node.left, depth + 1))
            if node.right:
                stack.append((node.right, depth + 1))
        return best

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def maxDepth_broken_base_one(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — `return 1` for the empty tree. Off by one on
        every input, including claiming the empty tree has a node."""
        if not root:
            return 1
        return 1 + max(self.maxDepth_broken_base_one(root.left),
                       self.maxDepth_broken_base_one(root.right))

    def maxDepth_broken_edges(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — counts EDGES, not nodes (no `1 +`)."""
        if not root:
            return 0
        return max(self.maxDepth_broken_edges(root.left),
                   self.maxDepth_broken_edges(root.right))

    def maxDepth_broken_min(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — `min` instead of `max`. Right answer on a
        perfect tree, wrong on anything lopsided (and NOT the same thing as
        problem 006's minimum depth either)."""
        if not root:
            return 0
        return 1 + min(self.maxDepth_broken_min(root.left),
                       self.maxDepth_broken_min(root.right))

    def maxDepth_broken_bfs_live_len(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — reads the queue length WHILE appending to it,
        so levels merge into one pass."""
        if not root:
            return 0
        queue = deque([root])
        depth = 0
        while queue:
            depth += 1
            i = 0
            while i < len(queue):              # live length, not a snapshot
                node = queue[i]
                i += 1
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
            for _ in range(i):
                queue.popleft()
        return depth


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


# ==============================================================================
# TESTS — run:  python 005_maximum_depth_of_binary_tree_solution.py
# ==============================================================================
CASES = [
    ([3, 9, 20, None, None, 15, 7], 3),
    ([1, None, 2], 2),
    ([], 0),
    ([0], 1),
    ([1, 2, 3, 4, None, None, 5], 3),
    ([1, 2, 2, 3, 3, None, None, 4, 4], 4),
    ([1, 2], 2),
    ([1, 2, 3, 4, 5, 6, 7], 3),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: bottom-up recursion ---")
    for values, want in CASES:
        got = sol.maxDepth(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<38} -> {got}  (want {want})")

    print("\n--- correctness: top-down, BFS, iterative DFS ---")
    impls = [
        ("top-down + nonlocal   ", sol.maxDepth_top_down),
        ("BFS by levels         ", sol.maxDepth_bfs),
        ("iterative (node, depth)", sol.maxDepth_stack),
    ]
    for name, fn in impls:
        ok = all(fn(build(v)) == want for v, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- randomised cross-check: all four agree on 400 random trees ---")
    rng = random.Random(104)
    mismatches = 0
    for _ in range(400):
        t = random_tree(rng.randint(0, 60), rng)
        want = sol.maxDepth(t)
        if any(fn(t) != want for _, fn in impls):
            mismatches += 1
    print(f"  400 random trees: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # trace: values flowing upward, one per node.
    # ----------------------------------------------------------------------
    print("\n--- trace: bottom-up on [3,9,20,null,null,15,7] ---")
    root = build([3, 9, 20, None, None, 15, 7])
    order = []

    def traced(node, indent=0):
        if not node:
            return 0
        left = traced(node.left, indent + 1)
        right = traced(node.right, indent + 1)
        result = 1 + max(left, right)
        order.append((node.val, left, right, result))
        print(f"  {'  ' * indent}node {node.val:<3} left={left} right={right} "
              f"-> returns 1 + max({left}, {right}) = {result}")
        return result

    total = traced(root)
    print(f"  answer: {total}")
    print(f"  nodes answered: {len(order)} (one number per node — no node was "
          f"asked twice)")
    all_ok &= (total == 3 and len(order) == 5)

    print("\n--- trace: the same tree, top-down (depth carried DOWN) ---")
    best = 0

    def traced_td(node, depth):
        nonlocal best
        if not node:
            return
        best = max(best, depth)
        print(f"  {'  ' * depth}dfs(node {node.val}, depth={depth})  best={best}")
        traced_td(node.left, depth + 1)
        traced_td(node.right, depth + 1)

    traced_td(root, 1)
    print(f"  answer: {best}")
    all_ok &= (best == 3)

    # ----------------------------------------------------------------------
    # ⚠️  The off-by-ones, live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the three off-by-one / wrong-operator variants ---")
    print(f"  {'tree':<32} {'correct':>8} {'base=1':>8} {'no 1+':>7} {'min()':>7}")
    for values in ([], [0], [1, None, 2], [3, 9, 20, None, None, 15, 7],
                   [1, 2, 3, 4, 5, 6, 7]):
        t = build(values)
        print(f"  {str(values):<32} {sol.maxDepth(t):>8} "
              f"{sol.maxDepth_broken_base_one(t):>8} "
              f"{sol.maxDepth_broken_edges(t):>7} {sol.maxDepth_broken_min(t):>7}")
    print("  base=1 : claims the EMPTY tree has depth 1 and adds a phantom level")
    print("           to every other answer.")
    print("  no 1+   : counts EDGES; always exactly one less than the answer, and")
    print("           correct-looking on the empty tree.")
    print("  min()   : identical to the answer on the PERFECT tree [1..7] — which")
    print("           is why a perfect tree is a useless test case here.")
    perfect = build([1, 2, 3, 4, 5, 6, 7])
    lopsided = build([3, 9, 20, None, None, 15, 7])
    print(f"  min == max on the perfect tree : "
          f"{sol.maxDepth_broken_min(perfect) == sol.maxDepth(perfect)}")
    print(f"  min == max on the lopsided one : "
          f"{sol.maxDepth_broken_min(lopsided) == sol.maxDepth(lopsided)}")
    all_ok &= (sol.maxDepth_broken_min(perfect) == sol.maxDepth(perfect)
               and sol.maxDepth_broken_min(lopsided) != sol.maxDepth(lopsided))

    # ----------------------------------------------------------------------
    # ⚠️  BFS: snapshot the level size.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: BFS that reads len(queue) while appending ---")
    for values in ([3, 9, 20, None, None, 15, 7], [1, 2, 3, 4, 5, 6, 7]):
        t = build(values)
        good = sol.maxDepth_bfs(t)
        bad = sol.maxDepth_broken_bfs_live_len(t)
        print(f"  {str(values):<34} snapshot={good}  live len={bad}  "
              f"{'MERGED LEVELS' if bad != good else ''}")
    t = build([1, 2, 3, 4, 5, 6, 7])
    all_ok &= (sol.maxDepth_broken_bfs_live_len(t) != sol.maxDepth_bfs(t))
    print("  Reading the length live lets the children you just appended join")
    print("  the level you are still draining, so several levels collapse into")
    print("  one pass. `for _ in range(len(queue))` is the fix, and it is the")
    print("  same line every level-order problem (013, 014, 199) depends on.")

    # ----------------------------------------------------------------------
    # ⚠️  A 10,000-node chain is INSIDE the LeetCode constraints.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  RecursionError on a chain of 10,000 (LC 104 allows 10^4) ---")
    deep = build_skewed(10_000, "left")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    raised = False
    try:
        sol.maxDepth(deep)
        print("  recursive : did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive : RecursionError -> {e}")
    bfs_ok = sol.maxDepth_bfs(deep) == 10_000
    stack_ok = sol.maxDepth_stack(deep) == 10_000
    print(f"  BFS        : {sol.maxDepth_bfs(deep)}   correct = {bfs_ok}")
    print(f"  DFS stack  : {sol.maxDepth_stack(deep)}   correct = {stack_ok}")
    saved = sys.getrecursionlimit()
    try:
        sys.setrecursionlimit(30_000)
        raised_ok = sol.maxDepth(deep) == 10_000
        print(f"  recursion with the limit raised to 30000: {raised_ok}")
    finally:
        sys.setrecursionlimit(saved)
    print(f"  limit restored to {sys.getrecursionlimit()}")
    all_ok &= (raised and bfs_ok and stack_ok)

    # ----------------------------------------------------------------------
    # Which iterative version? It depends on the SHAPE.
    # ----------------------------------------------------------------------
    print("\n--- peak worklist: BFS is O(w), DFS is O(h) — pick by shape ---")
    print(f"  {'shape':<28} {'BFS peak queue':>16} {'DFS peak stack':>16}")
    for label, tree in (("complete, n=8191", build_complete(8191)),
                        ("left chain, n=8191", build_skewed(8191, "left"))):
        q, peak_b = deque([tree]), 0
        while q:
            peak_b = max(peak_b, len(q))
            node = q.popleft()
            if node.left:
                q.append(node.left)
            if node.right:
                q.append(node.right)
        st, peak_d = [(tree, 1)], 0
        while st:
            peak_d = max(peak_d, len(st))
            node, d = st.pop()
            if node.left:
                st.append((node.left, d + 1))
            if node.right:
                st.append((node.right, d + 1))
        print(f"  {label:<28} {peak_b:>16} {peak_d:>16}")
    print("  On the WIDE tree the stack is ~300x cheaper: BFS holds an entire")
    print("  level (~n/2 nodes) at once while DFS holds only the height. On the")
    print("  CHAIN both worklists peak at 1 — a chain node has one child — so")
    print("  the deep case is not a BFS-vs-DFS question at all: it is the")
    print("  RECURSION that dies there, at h frames, while either explicit")
    print("  worklist walks it in O(1) memory.")

    # ----------------------------------------------------------------------
    # RUNTIME: the four correct versions, measured.
    # ----------------------------------------------------------------------
    print("\n--- measured: bottom-up vs top-down vs BFS vs DFS stack ---")
    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        bench_rng = random.Random(7)
        print(f"  {'n':>7} {'bottom-up':>11} {'top-down':>11} {'BFS':>11} {'DFS stack':>11}")
        for n in (5_000, 20_000, 50_000):
            t = random_tree(n, bench_rng)
            reps = 5
            times = []
            for fn in (sol.maxDepth, sol.maxDepth_top_down,
                       sol.maxDepth_bfs, sol.maxDepth_stack):
                t0 = time.perf_counter()
                for _ in range(reps):
                    fn(t)
                times.append((time.perf_counter() - t0) / reps * 1000)
            print(f"  {n:>7} " + " ".join(f"{ms:>9.2f}ms" for ms in times))
        print("  All four are O(n) and within a small constant of each other —")
        print("  for THIS problem the choice is about space and the recursion")
        print("  limit, not speed. Problems 009 and 010 are where picking")
        print("  top-down instead of bottom-up costs a factor of n; those files")
        print("  measure it at over 1000x on the same machine.")
    finally:
        sys.setrecursionlimit(saved)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
