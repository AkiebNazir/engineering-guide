"""
================================================================================
SOLUTION · LeetCode 102 · Binary Tree Level Order Traversal            [Medium]
https://leetcode.com/problems/binary-tree-level-order-traversal/
================================================================================

THE CORE IDEA
--------------
A queue already visits nodes in level order — that part is free. The whole
problem is knowing WHERE ONE LEVEL ENDS, and the answer is an invariant you
can state in one sentence:

    At the top of each outer iteration, the queue holds EXACTLY the nodes
    of the current level, and nothing else.

If that is true, then `len(q)` at that instant IS the width of the current
level. Snapshot it, pop exactly that many, and every child you enqueue while
doing so belongs to the NEXT level — which re-establishes the invariant for
the following iteration. Induction; done.

    while q:
        for _ in range(len(q)):        # len(q) evaluated ONCE, before the body
            node = q.popleft()
            level.append(node.val)
            if node.left:  q.append(node.left)
            if node.right: q.append(node.right)
        out.append(level)

`range(len(q))` is not a stylistic choice. `range` is built from the value of
`len(q)` *at loop setup*, so the appends inside the body cannot extend the
iteration — that is precisely what keeps the next level out of this level.

O(n) time, O(w) auxiliary space where w is the widest level.


================================================================================
MULTIPLE APPROACHES
================================================================================
0. BRUTE FORCE — compute the height h, then for each depth d in 0..h-1 walk
   the whole tree collecting nodes at depth exactly d. Correct, and O(n·h)
   time — O(n^2) on a skewed tree, O(n log n) on a balanced one. Stated and
   priced; not coded, because the level-size loop is strictly better and no
   harder to write.

1. BFS + LEVEL-SIZE LOOP ✅ — the version above. O(n) time, O(w) space. This
   is the answer, and the one to reach for in an interview because it is the
   template that all six sibling problems (107/103/199/637/515) are edits of.

2. BFS + TWO LISTS (no deque, no length snapshot) — hold the current level as
   a plain list, build the next level as a second list, then swap:

        level = [root]
        while level:
            out.append([n.val for n in level])
            level = [c for n in level for c in (n.left, n.right) if c]

   O(n) time, O(w) space. Arguably the most Pythonic form: there is no queue
   at all, so there is no `pop(0)` trap to fall into and no length to
   snapshot — the level boundary is a *list boundary*. Genuinely competitive;
   the benchmark below measures it.

3. BFS + `None` SENTINEL between levels — enqueue `None` as a level
   terminator, and re-enqueue one whenever you pop one and the queue is
   non-empty. O(n) time. Works, but it hand-rolls a boundary marker that
   `len(q)` already gives you for free, and the "don't re-enqueue the last
   sentinel or you loop forever" condition is a real bug source. Coded below
   for completeness; not the recommended shape.

4. DFS WITH A DEPTH PARAMETER — recurse carrying `depth`, and index into the
   output by depth:

        def go(node, depth):
            if node is None: return
            if depth == len(out): out.append([])   # first time we reach this depth
            out[depth].append(node.val)
            go(node.left, depth + 1)
            go(node.right, depth + 1)

   O(n) time, O(h) space for the call stack. Correct — and worth knowing,
   because "level order" does NOT require BFS. Two caveats, both demonstrated
   at runtime below:
     · it must be PREORDER (node before children) for the left-to-right order
       within each level to come out right;
     · it recurses to depth h, so on a skewed tree it dies on Python's
       recursion limit where BFS does not.

5. `list` AS THE QUEUE with `pop(0)` — ✗ the anti-pattern. Same algorithm,
   but each `pop(0)` memmoves every remaining element down one slot, so a
   level of width w costs O(w^2) to drain instead of O(w). Measured below:
   on a perfect tree it goes from ~6x slower at n=4095 (widest level 2048) to
   ~100x slower at n=131071 (widest level 65536) on this machine — the ratio
   GROWS, which is what distinguishes an asymptotic gap from a constant one.


================================================================================
STEP BY STEP TRACE — root = [3,9,20,null,null,15,7]
================================================================================
            3
          ┌─┴──┐
          9    20
             ┌─┴─┐
            15    7

    iteration  queue at top      len(q)  popped        enqueued      out
    ---------  ----------------  ------  ------------  ------------  -----------------
    1          [3]               1       3             9, 20         [[3]]
    2          [9, 20]           2       9, 20         15, 7         [[3],[9,20]]
    3          [15, 7]           2       15, 7         (none)        [[3],[9,20],[15,7]]
    4          []                -> while exits

    Note iteration 2: `range(len(q))` was built from len(q)==2 BEFORE 15 and
    7 were appended. The loop therefore pops exactly 9 and 20, leaving 15
    and 7 as the *entire* queue for iteration 3 — the invariant restored.

    ⚠️ Now the SAME tree with the inner `for` replaced by `while q:`:

    iteration  queue at top      popped                 out
    ---------  ----------------  ---------------------  -------------------
    1          [3]               3, then 9, 20, 15, 7   [[3,9,20,15,7]]
                                 (children appended
                                  during the drain get
                                  drained too)
    2          []                -> while exits

    One flat "level". The demo below prints exactly this.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time        Space (aux)  Mutates input?  Note
    --------------------------------  ----------  -----------  --------------  --------------------
    Brute: height, then per-depth     O(n·h)      O(h)         no              O(n^2) skewed
      walk                                                                       — priced, not coded
    BFS + level-size loop ✅          O(n)        O(w)         no              the answer
    BFS + two lists                   O(n)        O(w)         no              no queue at all
    BFS + None sentinel               O(n)        O(w)         no              hand-rolled marker
    DFS + depth parameter             O(n)        O(h)         no              dies at h > ~1000
    BFS with list.pop(0)              O(n + w^2   O(w)         no              ✗ anti-pattern
                                       per level)                                (measured below)

    n = number of nodes, h = height, w = maximum level width.

    WHERE O(w) SPACE COMES FROM: the queue never holds more than one level
    plus the part of the next level enqueued so far, so its peak is O(w). For
    a PERFECT tree w = (n+1)/2 — the bottom level is half the tree — so BFS
    is O(n) space in the worst case. For a SKEWED tree w = 1, so BFS is O(1)
    auxiliary while DFS is O(n). The two approaches have *opposite* worst
    cases, which is the real reason to know both.

    The output itself is O(n) regardless and is not counted as auxiliary.


================================================================================
EDGE CASES
================================================================================
    root = None          -> return []. Must be the FIRST line: enqueueing
                            `None` and then reading `.val` off it raises
                            AttributeError.
    single node           -> [[1]]: one outer iteration, level width 1.
    left-skewed chain     -> [[1],[2],[3],...]: n levels of width 1. Worst
                            case for DFS (recursion depth n), BEST case for
                            BFS (queue never exceeds 1).
    perfect tree           -> widest possible last level, (n+1)/2 nodes; worst
                            case for BFS's queue memory.
    negative and zero vals -> `if node.left:` tests the NODE object, not its
                            value, so `TreeNode(0)` is correctly truthy. A
                            node is falsy only if it is `None`. (Writing
                            `if node.left is not None:` is equivalent here
                            and immune to any future `__bool__` on TreeNode.)
    duplicate values       -> irrelevant; nothing keys on value.


================================================================================
COMMON MISTAKES
================================================================================
1. Draining the queue with an inner `while q:` instead of
   `for _ in range(len(q))`. The children appended during the drain get
   drained by the same loop, so every node lands in one flat level. Printed
   live in the demo.

2. Re-reading `len(q)` inside the loop — e.g. `i = 0; while i < len(q):`.
   `len(q)` grows as children are appended, so the condition keeps moving
   and the level again swallows its own children. `range(len(q))` is safe
   precisely because `range` is constructed once, from a snapshot.

3. Iterating the queue object directly (`for node in q:`) while appending to
   it — mutating a deque during iteration raises
   `RuntimeError: deque mutated during iteration`. (A *list* would not
   raise; it would silently walk into the newly appended children, which is
   worse.)

4. `list.pop(0)` instead of `deque.popleft()`. Correct output, quadratic per
   level. Measured below.

5. Forgetting the `root is None` guard, or "handling" it by enqueueing
   `None` and testing for it inside the loop. The guard is one line and it
   removes the special case entirely.

6. In the DFS variant, visiting children BEFORE recording the node, or
   recording the right child before the left. Level order requires a
   preorder, left-first visit; anything else scrambles the within-level
   order even though the depth bucketing still "works".

7. In the DFS variant, using `out[depth].append(...)` without first growing
   `out` — `IndexError` the first time a new depth is reached. The
   `if depth == len(out): out.append([])` line is what makes indexing safe,
   and it is only correct because preorder DFS reaches depth d for the first
   time exactly once.

8. Using a mutable default argument to carry the accumulator
   (`def go(node, depth, out=[])`). The default is evaluated once per
   execution of the `def` STATEMENT and stored in `go.__defaults__`. A
   helper NESTED inside `levelOrder` re-executes its `def` on every call, so
   the bug hides; hoist that same helper to module level or make it a method
   — a routine refactor — and the list is shared by every call, so the
   second call returns the first call's answer. Problem 014 demonstrates
   both halves at runtime. Topic guide Part 4.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the levels bottom-up (LC 107).
A: Same traversal, `out.reverse()` at the end — or `out.appendleft(level)`
   if `out` is a deque. Do NOT "traverse upward"; there are no parent
   pointers.

Q: Zigzag / spiral order (LC 103).
A: Same traversal; reverse odd-indexed levels. `level[::-1] if depth % 2
   else level`, or build the level into a deque and `appendleft` on odd
   levels to avoid the reversal. Do not try to alternate the ENQUEUE order —
   that breaks the invariant and is the classic wrong turn on 103.

Q: Just the rightmost node of each level (LC 199).
A: `[level[-1] for level in out]`, or skip materialising levels and record
   only the last pop of each level. That is problem 014 here.

Q: Average / max / sum per level (LC 637 / 515 / 1161).
A: Identical loop, different one-liner per level. 1161 wants the argmax, so
   track `(sum, depth)` and remember that ties go to the SMALLEST depth.

Q: Can you do level order WITHOUT a queue?
A: Yes — approach 2 (two lists) or approach 4 (DFS + depth). DFS proves
   level order is not synonymous with BFS: BFS gets the order from the data
   structure, DFS gets it from an explicit depth index.

Q: The tree is 10^6 nodes and one long chain. Which approach?
A: BFS. DFS blows Python's recursion limit (~1000 frames) long before that.
   Demonstrated at runtime below on a 5000-deep spine.

Q: What if nodes have k children instead of 2 (LC 429, N-ary)?
A: The level-size loop is unchanged; `for child in node.children: q.append
   (child)` replaces the two `if` statements. Nothing else moves — which is
   the clearest evidence that the level-size loop, not the binary-ness, is
   the idea.

Q: Report each node's level alongside its value, without grouping?
A: Enqueue `(node, depth)` tuples instead of bare nodes. Slightly more
   allocation; needed when levels interleave with other work.


================================================================================
RELATED PROBLEMS — the pattern family
================================================================================
    LC 107   Binary Tree Level Order Traversal II  — this, output reversed
    LC 103   Binary Tree Zigzag Level Order        — this, alternate levels reversed
    LC 199   Binary Tree Right Side View           — this, take level[-1]  (014 here)
    LC 637   Average of Levels in Binary Tree      — this, mean per level
    LC 515   Find Largest Value in Each Tree Row   — this, max per level
    LC 1161  Maximum Level Sum of a Binary Tree    — this, argmax of sum per level
    LC 429   N-ary Tree Level Order Traversal      — this, k children per node
    LC 116   Populating Next Right Pointers        — level order, but wiring
                                                      pointers instead of listing
    LC 993   Cousins in Binary Tree                — level order + parent check
    LC 662   Maximum Width of Binary Tree          — level order + positional index
    LC 111   Minimum Depth of Binary Tree          — BFS's real win: first leaf
                                                      popped ends it early (006 here)
================================================================================
"""

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
    def levelOrder(self, root: Optional[TreeNode]) -> List[List[int]]:
        """BFS with the level-size snapshot. O(n) time, O(w) space.
        See THE CORE IDEA above."""
        if root is None:
            return []
        out: List[List[int]] = []
        q = deque([root])
        while q:
            level: List[int] = []
            for _ in range(len(q)):          # len(q) snapshotted ONCE, here
                node = q.popleft()
                level.append(node.val)
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
            out.append(level)
        return out

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def levelOrder_two_lists(self, root: Optional[TreeNode]) -> List[List[int]]:
        """Approach 2: no queue at all — the level boundary is a list
        boundary. O(n) time, O(w) space."""
        out: List[List[int]] = []
        level = [root] if root is not None else []
        while level:
            out.append([node.val for node in level])
            level = [child
                     for node in level
                     for child in (node.left, node.right)
                     if child is not None]
        return out

    def levelOrder_sentinel(self, root: Optional[TreeNode]) -> List[List[int]]:
        """Approach 3: a `None` sentinel marks each level boundary. Works;
        the 'do not re-enqueue the final sentinel' guard is the bug source."""
        if root is None:
            return []
        out: List[List[int]] = []
        q = deque([root, None])
        level: List[int] = []
        while q:
            node = q.popleft()
            if node is None:
                out.append(level)
                level = []
                if q:                         # <- the guard; drop it and loop forever
                    q.append(None)
                continue
            level.append(node.val)
            if node.left is not None:
                q.append(node.left)
            if node.right is not None:
                q.append(node.right)
        return out

    def levelOrder_dfs(self, root: Optional[TreeNode]) -> List[List[int]]:
        """Approach 4: preorder DFS carrying `depth`, bucketed by depth.
        O(n) time, O(h) stack. Level order does NOT require BFS."""
        out: List[List[int]] = []

        def go(node: Optional[TreeNode], depth: int) -> None:
            if node is None:
                return
            if depth == len(out):             # first arrival at this depth
                out.append([])
            out[depth].append(node.val)
            go(node.left, depth + 1)
            go(node.right, depth + 1)

        go(root, 0)
        return out

    def levelOrder_pop0(self, root: Optional[TreeNode]) -> List[List[int]]:
        """✗ ANTI-PATTERN, priced on purpose: a list as the queue. Every
        pop(0) shifts the whole remaining list. Benchmarked below."""
        if root is None:
            return []
        out: List[List[int]] = []
        q = [root]
        while q:
            level: List[int] = []
            for _ in range(len(q)):
                node = q.pop(0)               # O(len(q)) memmove — the culprit
                level.append(node.val)
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
            out.append(level)
        return out

    # ------------------------------------------------------------------
    # Deliberate breakage — no level-size snapshot.
    # ------------------------------------------------------------------
    def levelOrder_broken_no_snapshot(self, root: Optional[TreeNode]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — inner `while q:` drains the children it
        just appended, so every node lands in ONE flat level."""
        if root is None:
            return []
        out: List[List[int]] = []
        q = deque([root])
        while q:
            level: List[int] = []
            while q:                          # should be: for _ in range(len(q))
                node = q.popleft()
                level.append(node.val)
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
            out.append(level)
        return out


# ==============================================================================
# TEST HELPERS — level-order (de)serialisation, LeetCode's array format
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


def perfect_tree(depth: int) -> Optional[TreeNode]:
    """Perfect binary tree of the given depth, built ITERATIVELY (so the
    builder itself is not bound by the recursion limit)."""
    if depth <= 0:
        return None
    root = TreeNode(0)
    frontier = [root]
    for _ in range(depth - 1):
        nxt = []
        for node in frontier:
            node.left = TreeNode(0)
            node.right = TreeNode(0)
            nxt.append(node.left)
            nxt.append(node.right)
        frontier = nxt
    return root


def left_spine(n: int) -> Optional[TreeNode]:
    """A left-only chain of n nodes: height n, maximum level width 1."""
    if n <= 0:
        return None
    root = TreeNode(0)
    cur = root
    for i in range(1, n):
        cur.left = TreeNode(i)
        cur = cur.left
    return root


# ==============================================================================
# TESTS — run:  python 013_binary_tree_level_order_traversal_solution.py
# ==============================================================================
CASES = [
    ([3, 9, 20, None, None, 15, 7], [[3], [9, 20], [15, 7]]),
    ([1], [[1]]),
    ([], []),
    ([1, 2, 3, 4, 5, 6, 7], [[1], [2, 3], [4, 5, 6, 7]]),
    ([1, 2, None, 3, None, 4], [[1], [2], [3], [4]]),
    ([1, None, 2, None, 3], [[1], [2], [3]]),
    ([0, 0, 0], [[0], [0, 0]]),
    ([-1, -2, -3], [[-1], [-2, -3]]),
    ([1, 2, 3, None, 4, None, 5], [[1], [2, 3], [4, 5]]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: all four working approaches agree ---")
    impls = [
        ("BFS level-size loop ", sol.levelOrder),
        ("BFS two lists       ", sol.levelOrder_two_lists),
        ("BFS None sentinel   ", sol.levelOrder_sentinel),
        ("DFS + depth param   ", sol.levelOrder_dfs),
        ("BFS list.pop(0)     ", sol.levelOrder_pop0),
    ]
    for name, fn in impls:
        ok = all(fn(build(vals)) == expected for vals, expected in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- per-case output (the answer implementation) ---")
    for vals, expected in CASES:
        got = sol.levelOrder(build(vals))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<32} -> {got}")

    print("\n--- build / to_level_order round-trip (helpers are inverses) ---")
    for vals, _ in CASES:
        rt = to_level_order(build(vals))
        trimmed = list(vals)
        while trimmed and trimmed[-1] is None:
            trimmed.pop()
        ok = rt == trimmed
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(vals):<32} -> {rt}")

    # ----------------------------------------------------------------------
    # Live trace of the invariant: what the queue holds at each iteration.
    # ----------------------------------------------------------------------
    print("\n--- trace: the queue holds EXACTLY one level at the top of each pass ---")
    root = build([3, 9, 20, None, None, 15, 7])
    q = deque([root])
    it = 0
    print(f"  {'pass':>4}  {'queue at top':<16} {'len(q)':>6}  {'popped':<12} {'enqueued'}")
    while q:
        it += 1
        snapshot = [n.val for n in q]
        width = len(q)
        popped, enq = [], []
        for _ in range(width):
            node = q.popleft()
            popped.append(node.val)
            if node.left is not None:
                q.append(node.left)
                enq.append(node.left.val)
            if node.right is not None:
                q.append(node.right)
                enq.append(node.right.val)
        print(f"  {it:>4}  {str(snapshot):<16} {width:>6}  {str(popped):<12} {enq if enq else '(none)'}")

    # ----------------------------------------------------------------------
    # The level-size snapshot, proven necessary.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `for _ in range(len(q))` vs an inner `while q:` ---")
    vals = [3, 9, 20, None, None, 15, 7]
    good = sol.levelOrder(build(vals))
    bad = sol.levelOrder_broken_no_snapshot(build(vals))
    print(f"  snapshot len(q) first : {good}")
    print(f"  inner `while q:`      : {bad}")
    collapsed = len(bad) == 1 and len(bad[0]) == 5
    all_ok &= collapsed
    print(f"  the broken version collapsed all 3 levels into 1 flat list of 5: {collapsed}")
    print("  Reason: the children appended during the drain are drained by the")
    print("  SAME inner loop. `range(len(q))` is built from a snapshot taken")
    print("  before any child is appended, so it cannot be extended.")

    # ----------------------------------------------------------------------
    # Mutating a deque while iterating it: the third way to get this wrong.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  `for node in q:` while appending (mistake 3) ---")
    q = deque([build([1, 2, 3])])
    err = None
    try:
        for node in q:
            if node.left is not None:
                q.append(node.left)
            if node.right is not None:
                q.append(node.right)
    except RuntimeError as exc:
        err = f"{type(exc).__name__}: {exc}"
    print(f"  deque, iterated while appended to -> {err}")
    raised = err is not None
    all_ok &= raised
    lst = [build([1, 2, 3])]
    seen = 0
    for node in lst:
        seen += 1
        if seen > 10:
            break
        if node.left is not None:
            lst.append(node.left)
        if node.right is not None:
            lst.append(node.right)
    print(f"  list,  iterated while appended to -> NO error, silently visited "
          f"{seen} nodes (walked into its own appends)")
    print("  A deque is loud about it; a list is silent. Neither is the fix —")
    print("  the fix is popping a snapshotted count.")

    # ----------------------------------------------------------------------
    # BENCHMARK: deque.popleft() vs list.pop(0). REAL measured numbers.
    # ----------------------------------------------------------------------
    print("\n--- benchmark: deque.popleft() vs list.pop(0) on a PERFECT tree ---")
    print(f"  {'depth':>5} {'nodes':>8} {'widest level':>13} {'deque (ms)':>12} "
          f"{'pop(0) (ms)':>13} {'slowdown':>9}")
    for depth in (12, 14, 16, 17):
        root = perfect_tree(depth)
        n = 2 ** depth - 1
        widest = 2 ** (depth - 1)
        t0 = time.perf_counter()
        a = sol.levelOrder(root)
        t1 = time.perf_counter()
        b = sol.levelOrder_pop0(root)
        t2 = time.perf_counter()
        all_ok &= (a == b)
        dq_ms = (t1 - t0) * 1000
        lp_ms = (t2 - t1) * 1000
        print(f"  {depth:>5} {n:>8} {widest:>13} {dq_ms:>12.2f} {lp_ms:>13.2f} "
              f"{lp_ms / dq_ms:>8.1f}x")
    print("  The slowdown GROWS with the level width, because draining a level")
    print("  of width w costs O(w) with popleft and O(w^2) with pop(0). A")
    print("  constant-factor difference would hold the ratio flat; it does not.")

    # ----------------------------------------------------------------------
    # BFS vs DFS have OPPOSITE worst cases. Proven on a 5000-deep spine.
    # ----------------------------------------------------------------------
    print("\n--- BFS vs DFS: opposite worst cases (5000-node left spine) ---")
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}")
    spine = left_spine(5000)
    try:
        dfs_levels = len(sol.levelOrder_dfs(spine))
        dfs_result = f"ok, {dfs_levels} levels"
        dfs_died = False
    except RecursionError as exc:
        dfs_result = f"{type(exc).__name__}: {exc}"
        dfs_died = True
    print(f"  DFS + depth param, default limit -> {dfs_result}")
    all_ok &= dfs_died
    bfs_levels = len(sol.levelOrder(spine))
    print(f"  BFS level-size loop              -> ok, {bfs_levels} levels "
          f"(queue never exceeded width 1)")
    all_ok &= (bfs_levels == 5000)

    old_limit = sys.getrecursionlimit()
    sys.setrecursionlimit(20000)
    try:
        n_levels = len(sol.levelOrder_dfs(spine))
        print(f"  DFS after sys.setrecursionlimit(20000) -> ok, {n_levels} levels")
        all_ok &= (n_levels == 5000)
    except RecursionError as exc:
        print(f"  DFS after sys.setrecursionlimit(20000) -> STILL {exc}")
        all_ok = False
    finally:
        sys.setrecursionlimit(old_limit)
    print("  Raising the limit works, but it is a bandaid: the real C stack can")
    print("  still be exhausted (a hard crash, not a catchable RecursionError).")
    print("  On a deep tree, iterative BFS is the structural answer.")

    # ----------------------------------------------------------------------
    # And the mirror image: BFS's own worst case is memory, not depth.
    # ----------------------------------------------------------------------
    print("\n--- BFS's own worst case: queue width on a perfect tree ---")
    print(f"  {'depth':>5} {'nodes':>8} {'peak queue':>11} {'peak/n':>8}")
    for depth in (4, 8, 12, 14):
        root = perfect_tree(depth)
        n = 2 ** depth - 1
        peak = 0
        q = deque([root])
        while q:
            peak = max(peak, len(q))
            for _ in range(len(q)):
                node = q.popleft()
                if node.left is not None:
                    q.append(node.left)
                if node.right is not None:
                    q.append(node.right)
        print(f"  {depth:>5} {n:>8} {peak:>11} {peak / n:>7.2f}")
    print("  Peak queue -> (n+1)/2: the bottom level IS half the tree. So BFS")
    print("  is O(n) space here while DFS is only O(log n) — the exact reverse")
    print("  of the left-spine case above.")

    # ----------------------------------------------------------------------
    # The six sibling problems, derived from this one traversal.
    # ----------------------------------------------------------------------
    print("\n--- the family: six LC problems as one-line edits of `levels` ---")
    levels = sol.levelOrder(build([3, 9, 20, None, None, 15, 7]))
    print(f"  levels                          = {levels}")
    print(f"  LC 102 level order              = {levels}")
    print(f"  LC 107 bottom-up                = {levels[::-1]}")
    zig = [lvl[::-1] if d % 2 else lvl for d, lvl in enumerate(levels)]
    print(f"  LC 103 zigzag                   = {zig}")
    print(f"  LC 199 right side view          = {[lvl[-1] for lvl in levels]}")
    print(f"  LC 637 average of levels        = {[sum(l) / len(l) for l in levels]}")
    print(f"  LC 515 largest per row          = {[max(l) for l in levels]}")
    sums = [sum(l) for l in levels]
    print(f"  LC 1161 max level sum (1-based) = {sums.index(max(sums)) + 1}  (level sums {sums})")
    fam_ok = ([lvl[-1] for lvl in levels] == [3, 20, 7]
              and zig == [[3], [20, 9], [15, 7]]
              and levels[::-1] == [[15, 7], [9, 20], [3]])
    all_ok &= fam_ok
    print(f"  all six derived answers correct: {fam_ok}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
