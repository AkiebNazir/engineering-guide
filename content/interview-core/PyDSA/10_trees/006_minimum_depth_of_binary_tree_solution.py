"""
================================================================================
SOLUTION · LeetCode 111 · Minimum Depth of Binary Tree                  [Easy]
https://leetcode.com/problems/minimum-depth-of-binary-tree/
================================================================================

THE CORE IDEA
--------------
A node with ONE child is not a leaf, so the missing side must not be allowed
to win the `min`. That single sentence is the whole problem.

    minDepth(node) = 1 + min(minDepth(left), minDepth(right))        ✗ WRONG

because `minDepth(None) == 0` and 0 beats every real depth. On `[1,2]` the
left child is a leaf (depth 1) and the right child is missing (0), so this
returns `1 + min(1, 0) = 1`, claiming the root itself is a leaf. The demo below
runs it on a 5-node chain and prints `1` next to the correct `5`.

The correct recursion promotes "exactly one child" to its own branch:

    def minDepth(root):
        if not root:        return 0                  # empty tree
        if not root.left:   return 1 + minDepth(root.right)   # one child: go right
        if not root.right:  return 1 + minDepth(root.left)    # one child: go left
        return 1 + min(minDepth(root.left), minDepth(root.right))

An equivalent and often cleaner way to say it — the one to write if you want
the leaf condition to be visible rather than implied:

    if not root:                              return 0
    if not root.left and not root.right:       return 1        # a LEAF
    best = inf
    if root.left:   best = min(best, minDepth(root.left))
    if root.right:  best = min(best, minDepth(root.right))
    return 1 + best

But the better answer to give is BFS. "Shortest path to a leaf" is literally
a shortest-path problem, and BFS can stop at the FIRST leaf it meets:

    queue = deque([(root, 1)])
    while queue:
        node, depth = queue.popleft()
        if not node.left and not node.right:
            return depth                       # first leaf found = the answer
        if node.left:  queue.append((node.left, depth + 1))
        if node.right: queue.append((node.right, depth + 1))

Both are O(n) worst case, but BFS's early exit is not a micro-optimisation:
on a tree with a shallow leaf on one side and a huge subtree on the other,
the measured demo below has DFS visiting 131,073 nodes where BFS visits 2 —
and running about 1500x longer on this machine. This is the one problem in
001-012 where DFS vs BFS is a real algorithmic choice, not a style
preference.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (naive, don't code it): reuse the max-depth code with `min`. It is
not a slow solution, it is a WRONG one — see above. Worth stating explicitly
in an interview ("the obvious substitution is wrong, here's the input that
breaks it") because that is the actual thing being tested.

Approach 1 (DFS, one-child cases handled) ✅ — O(n) time, O(h) space.
   Correct on every shape; explores the whole tree even when the answer is 1
   level down.

Approach 2 (DFS, leaf base case + `inf`) ✅ — the same thing written so the
   "is a leaf" test appears literally. Slightly longer, harder to get wrong.

Approach 3 (BFS with early exit) ✅ — O(n) worst case but returns at the
   first leaf. O(w) space. THE answer to give, with Approach 1 as the "and
   here it is recursively" follow-up.

Approach 4 (iterative DFS with a stack, plus pruning) — a `(node, depth)`
   stack, skipping any branch whose depth already exceeds the best leaf found
   so far. No recursion limit, and the pruning helps on some shapes; still
   O(n) worst case, and it never beats BFS's level-order early exit on the
   adversarial shape. Implemented and measured below.


================================================================================
STEP BY STEP TRACE
================================================================================
Tree [2,null,3,null,4,null,5,null,6] — a right chain, one leaf at depth 5:

    2 -> 3 -> 4 -> 5 -> 6

    THE BROKEN VERSION                    THE CORRECT VERSION
    minDepth(2)                            minDepth(2)
      left  = minDepth(None) = 0             2 has no left child
      right = minDepth(3)   = 4              -> return 1 + minDepth(3)
      return 1 + min(0, 4) = 1  ✗            minDepth(3) = 1 + minDepth(4) = 4
                                             ...
                                             return 5  ✓

Tree [3,9,20,null,null,15,7] — BFS stops early:

            3            queue: [(3,1)]
          ╱   ╲          pop (3,1): not a leaf, push (9,2), (20,2)
         9     20        pop (9,2): 9 has no children -> LEAF -> return 2
              ╱  ╲
            15    7      15 and 7 are never visited at all

    DFS on the same tree visits all 5 nodes; BFS visits 2. Scale that gap up
    (a shallow leaf next to a 131,071-node subtree) and it is the difference
    the runtime demo measures.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time            Space  Mutates?  Note
    --------------------------  --------------  -----  --------  -----------------
    max-depth code with `min`   O(n)            O(h)   no        WRONG ANSWER
    DFS, one-child branches ✅  O(n)            O(h)   no        visits every node
    DFS, leaf base + inf ✅     O(n)            O(h)   no        same, clearer
    BFS, early exit ✅          O(n) worst,     O(w)   no        stops at the first
                                 O(k) typical                     leaf; k = nodes
                                                                  above that level
    Iterative DFS + pruning     O(n)            O(h)   no        no recursion limit

    "O(k) typical" is the whole point: BFS's work is bounded by the number of
    nodes ABOVE the shallowest leaf, which can be tiny even when n is huge.
    DFS has no such bound — it can walk a million-node subtree before finding
    the leaf that was two steps away.


================================================================================
EDGE CASES
================================================================================
    root = None        -> 0     the only 0. Note BFS must check this BEFORE
                                  seeding the queue, or it dereferences None.
    single node         -> 1     the root is itself a leaf.
    [1,2]                -> 2     THE test case. `min` gives 1. If your solution
                                  gets this right, it probably gets the problem
                                  right; if you never test it, you will ship the
                                  bug.
    a straight chain      -> depth == n. Both the broken version (answer 1) and
                                  the recursion limit (n = 10^5) bite here.
    shallow leaf + huge other subtree -> where BFS wins big; measured below.
    a perfect tree         -> every leaf is at the same depth, so min == max and
                                  the bug is INVISIBLE. Never test this problem
                                  on a perfect tree only.


================================================================================
COMMON MISTAKES
================================================================================
1. `1 + min(minDepth(left), minDepth(right))`. The headline bug of this
   problem: a missing child contributes 0 and wins the `min`, so any node with
   one child is treated as a leaf. Measured live below on `[1,2]`,
   `[2,null,3,null,4,null,5,null,6]` and a 5-node left chain — the broken
   version answers 1 for all three.
2. "Fixing" it with `min(...)` over only the non-None children but forgetting
   the empty-tree case, so `minDepth(None)` returns `inf` or crashes.
3. Testing only on a perfect/complete tree, where min == max, and concluding
   the `min` version is correct. The demo shows both versions agreeing on
   `[1,2,3,4,5,6,7]` and disagreeing on everything lopsided.
4. Using DFS and never mentioning that BFS has an early exit. The interviewer
   is usually looking for "shortest path -> BFS"; DFS-only is a correct answer
   that misses the point of the question.
5. In the BFS version, checking `if not node.left and not node.right` AFTER
   pushing the children, or forgetting the leaf test entirely and returning
   the number of levels (that computes MAX depth, not min).
6. Recursing on a 10^5-node chain — RecursionError, inside LeetCode's stated
   constraints. The BFS version has no such limit.
7. Off-by-one from counting edges: depth is in NODES, so a leaf found on the
   first pop has depth 1, not 0.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why doesn't max depth need the one-child special case?
A: Because `max` ignores a 0 from a missing side, while `min` prefers it. The
   asymmetry is in the operator, not the tree.

Q: Which is better, DFS or BFS, and why?
A: BFS. Both are O(n) worst case, but BFS's work is bounded by the depth of
   the shallowest leaf, and it can exit at the first one. Give the measured
   example: a shallow leaf beside a large subtree.

Q: What if the tree is 10^5 nodes in a chain?
A: BFS is unaffected (its queue holds one node at a time on a chain); the
   recursion raises RecursionError. Say it before being asked.

Q: Return the VALUE of the nearest leaf, or the path to it.
A: Same BFS, but enqueue `(node, depth, path)` or keep parent pointers and
   walk back up from the leaf. Enqueuing full paths costs O(n*h) memory;
   parent pointers keep it O(n).

Q: Minimum depth of an N-ary tree?
A: Same structure: `1 + min(minDepth(c) for c in children)` when there is at
   least one child, and `1` when there are none — the "one child" trap
   becomes "at least one child", handled by the same leaf test.

Q: Now the SUM along the shortest root-to-leaf path?
A: BFS carrying `(node, depth, running_sum)`, still stopping at the first
   leaf. This is the bridge to 011 (path sum), where the running value has to
   be carried down top-down.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 104   Maximum Depth of Binary Tree   — the symmetric-looking twin (005)
    LC 112   Path Sum                       — leaf definition again (011 here)
    LC 102   Level Order Traversal          — the BFS skeleton (013 here)
    LC 863   All Nodes Distance K           — BFS on a tree, early exit by level
    LC 993   Cousins in Binary Tree         — BFS levels + parent identity
    LC 1161  Maximum Level Sum              — BFS levels, aggregate per level
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
    def minDepth(self, root: Optional[TreeNode]) -> int:
        """BFS with an early exit at the first leaf. O(n) worst case, O(w)
        space — and typically far less work than DFS. The answer."""
        if not root:
            return 0
        queue = deque([(root, 1)])
        while queue:
            node, depth = queue.popleft()
            if not node.left and not node.right:
                return depth                      # first leaf reached
            if node.left:
                queue.append((node.left, depth + 1))
            if node.right:
                queue.append((node.right, depth + 1))
        return 0                                   # unreachable for a real tree

    def minDepth_dfs(self, root: Optional[TreeNode]) -> int:
        """DFS with the one-child cases promoted to their own branches.
        O(n) time, O(h) space."""
        if not root:
            return 0
        if not root.left:
            return 1 + self.minDepth_dfs(root.right)
        if not root.right:
            return 1 + self.minDepth_dfs(root.left)
        return 1 + min(self.minDepth_dfs(root.left), self.minDepth_dfs(root.right))

    def minDepth_dfs_leaf_base(self, root: Optional[TreeNode]) -> int:
        """DFS written so the LEAF test is literal rather than implied.
        O(n) time, O(h) space."""
        if not root:
            return 0
        if not root.left and not root.right:
            return 1                               # a leaf
        best = float("inf")
        if root.left:
            best = min(best, self.minDepth_dfs_leaf_base(root.left))
        if root.right:
            best = min(best, self.minDepth_dfs_leaf_base(root.right))
        return 1 + int(best)

    def minDepth_stack_pruned(self, root: Optional[TreeNode]) -> int:
        """Iterative DFS over (node, depth), pruning branches already deeper
        than the best leaf found. O(n) worst case, O(h) space, no recursion
        limit."""
        if not root:
            return 0
        best = float("inf")
        stack = [(root, 1)]
        while stack:
            node, depth = stack.pop()
            if depth >= best:
                continue                           # cannot improve
            if not node.left and not node.right:
                best = depth
                continue
            if node.left:
                stack.append((node.left, depth + 1))
            if node.right:
                stack.append((node.right, depth + 1))
        return int(best)

    # ------------------------------------------------------------------
    # Deliberate breakage — THE mistake this problem exists to teach.
    # ------------------------------------------------------------------
    def minDepth_broken_min(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — the max-depth recursion with `min`. Treats
        every one-child node as a leaf, because minDepth(None) == 0 wins."""
        if not root:
            return 0
        return 1 + min(self.minDepth_broken_min(root.left),
                       self.minDepth_broken_min(root.right))

    def minDepth_broken_bfs_levels(self, root: Optional[TreeNode]) -> int:
        """✗ BROKEN ON PURPOSE — BFS that counts levels but forgets to stop
        at the first leaf: that computes the MAXIMUM depth."""
        if not root:
            return 0
        queue = deque([root])
        depth = 0
        while queue:
            depth += 1
            for _ in range(len(queue)):
                node = queue.popleft()
                if node.left:
                    queue.append(node.left)
                if node.right:
                    queue.append(node.right)
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


def brute_min_depth(root):
    """Independent oracle: enumerate every root-to-leaf path length."""
    if not root:
        return 0
    depths = []
    stack = [(root, 1)]
    while stack:
        node, d = stack.pop()
        if not node.left and not node.right:
            depths.append(d)
        if node.left:
            stack.append((node.left, d + 1))
        if node.right:
            stack.append((node.right, d + 1))
    return min(depths)


# ==============================================================================
# TESTS — run:  python 006_minimum_depth_of_binary_tree_solution.py
# ==============================================================================
CASES = [
    ([3, 9, 20, None, None, 15, 7], 2),
    ([2, None, 3, None, 4, None, 5, None, 6], 5),
    ([], 0),
    ([1], 1),
    ([1, 2], 2),
    ([1, None, 2], 2),
    ([1, 2, 3, 4, 5], 2),
    ([1, 2, 3, 4, None, None, 5], 3),
    ([1, 2, 3, 4, 5, 6, 7], 3),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: BFS with early exit ---")
    for values, want in CASES:
        got = sol.minDepth(build(values))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {values!r:<44} -> {got}  (want {want})")

    print("\n--- correctness: the three DFS variants ---")
    impls = [
        ("DFS, one-child branches", sol.minDepth_dfs),
        ("DFS, leaf base + inf   ", sol.minDepth_dfs_leaf_base),
        ("iterative DFS + pruning", sol.minDepth_stack_pruned),
    ]
    for name, fn in impls:
        ok = all(fn(build(v)) == want for v, want in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    print("\n--- randomised cross-check vs a path-enumerating oracle ---")
    rng = random.Random(111)
    mismatches = 0
    for _ in range(500):
        t = random_tree(rng.randint(1, 60), rng)
        want = brute_min_depth(t)
        if sol.minDepth(t) != want or any(fn(t) != want for _, fn in impls):
            mismatches += 1
    print(f"  500 random trees: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # ⚠️  THE demo: `1 + min(left, right)` on a one-child chain.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: the min-depth trap, `1 + min(left, right)` ---")
    print(f"  {'tree':<42} {'correct':>8} {'1+min(l,r)':>11}  verdict")
    trap_cases = [
        [1, 2],
        [2, None, 3, None, 4, None, 5, None, 6],
        to_level_order(build_skewed(5, "left")),
        [3, 9, 20, None, None, 15, 7],
        [1, 2, 3, 4, 5, 6, 7],
    ]
    wrong_count = 0
    for values in trap_cases:
        t = build(values)
        good = sol.minDepth(t)
        bad = sol.minDepth_broken_min(build(values))
        if bad != good:
            wrong_count += 1
        print(f"  {str(values):<42} {good:>8} {bad:>11}  "
              f"{'WRONG' if bad != good else 'agrees'}")
    print(f"  the broken version was wrong on {wrong_count} of "
          f"{len(trap_cases)} shapes")
    print("  Every failure is a chain of ONE-child nodes: minDepth(None)=0 wins")
    print("  the min, so the recursion reports a path that stops at an internal")
    print("  node — it answers 1 for all three, no matter how deep the tree.")
    print("  The two rows where it AGREES are the dangerous ones: whenever the")
    print("  shallowest leaf happens to sit above every one-child node (row 4)")
    print("  or the tree is perfect (row 5), the bug is completely invisible.")
    print("  A test suite built from LeetCode's Example 1 alone passes it.")
    all_ok &= (wrong_count == 3)

    print("\n--- ⚠️  live demo: BFS that counts levels instead of stopping ---")
    for values in ([3, 9, 20, None, None, 15, 7], [1, 2, 3, 4, None, None, 5]):
        t = build(values)
        print(f"  {str(values):<38} min={sol.minDepth(t)}  "
              f"count-all-levels={sol.minDepth_broken_bfs_levels(t)}  "
              f"<- that is MAX depth")
    t = build([3, 9, 20, None, None, 15, 7])
    all_ok &= (sol.minDepth_broken_bfs_levels(t) != sol.minDepth(t))

    # ----------------------------------------------------------------------
    # trace: BFS stops at the first leaf.
    # ----------------------------------------------------------------------
    print("\n--- trace: BFS on [3,9,20,null,null,15,7] ---")
    root = build([3, 9, 20, None, None, 15, 7])
    queue, visited = deque([(root, 1)]), []
    while queue:
        node, depth = queue.popleft()
        visited.append(node.val)
        leaf = not node.left and not node.right
        print(f"  pop (node {node.val}, depth {depth})  leaf? {leaf}  "
              f"queue now {[(n.val, d) for n, d in queue]}")
        if leaf:
            print(f"  -> first leaf, return {depth}")
            break
        if node.left:
            queue.append((node.left, depth + 1))
        if node.right:
            queue.append((node.right, depth + 1))
    print(f"  nodes BFS touched: {visited}  (15 and 7 were never visited)")

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: the adversarial shape — shallow leaf, huge sibling.
    # ----------------------------------------------------------------------
    print("\n--- measured: DFS explores everything, BFS exits at the first leaf ---")
    print("  Shape: root, whose LEFT child is a lone leaf and whose RIGHT child")
    print("  is a complete tree of 131,071 nodes. The answer is 2 either way.")
    root = TreeNode(0)
    root.left = TreeNode(1)                       # a leaf at depth 2
    root.right = build_complete(131_071, start=100)

    counted = [0]

    def dfs_counting(node):
        """The correct DFS, instrumented to count node visits."""
        if not node:
            return 0
        counted[0] += 1
        if not node.left:
            return 1 + dfs_counting(node.right)
        if not node.right:
            return 1 + dfs_counting(node.left)
        return 1 + min(dfs_counting(node.left), dfs_counting(node.right))

    bfs_counted = [0]

    def bfs_counting(node):
        if not node:
            return 0
        queue = deque([(node, 1)])
        while queue:
            nd, depth = queue.popleft()
            bfs_counted[0] += 1
            if not nd.left and not nd.right:
                return depth
            if nd.left:
                queue.append((nd.left, depth + 1))
            if nd.right:
                queue.append((nd.right, depth + 1))
        return 0

    saved = sys.getrecursionlimit()
    sys.setrecursionlimit(60_000)
    try:
        t0 = time.perf_counter()
        dfs_answer = dfs_counting(root)
        t1 = time.perf_counter()
        bfs_answer = bfs_counting(root)
        t2 = time.perf_counter()
    finally:
        sys.setrecursionlimit(saved)
    dfs_ms, bfs_ms = (t1 - t0) * 1000, (t2 - t1) * 1000
    print(f"  DFS: answer={dfs_answer}  nodes visited={counted[0]:>7}  "
          f"{dfs_ms:>8.2f}ms")
    print(f"  BFS: answer={bfs_answer}  nodes visited={bfs_counted[0]:>7}  "
          f"{bfs_ms:>8.3f}ms")
    print(f"  BFS visited {counted[0] / bfs_counted[0]:.0f}x fewer nodes and ran "
          f"{dfs_ms / bfs_ms:.0f}x faster on this machine")
    print("  Same O(n) worst case, wildly different real work: DFS commits to a")
    print("  whole subtree before it can compare, BFS is bounded by the level of")
    print("  the shallowest leaf. THIS is why the answer to 'shortest path to a")
    print("  leaf' is BFS.")
    all_ok &= (dfs_answer == 2 and bfs_answer == 2
               and bfs_counted[0] < counted[0])

    # ----------------------------------------------------------------------
    # And the reverse shape: BFS is not free.
    # ----------------------------------------------------------------------
    print("\n--- the other side of the trade: a wide tree with only deep leaves ---")
    wide = build_complete(131_071)
    q, peak = deque([(wide, 1)]), 0
    while q:
        peak = max(peak, len(q))
        nd, d = q.popleft()
        if not nd.left and not nd.right:
            break
        if nd.left:
            q.append((nd.left, d + 1))
        if nd.right:
            q.append((nd.right, d + 1))
    st, peak_dfs = [(wide, 1)], 0
    while st:
        peak_dfs = max(peak_dfs, len(st))
        nd, d = st.pop()
        if nd.left:
            st.append((nd.left, d + 1))
        if nd.right:
            st.append((nd.right, d + 1))
    print(f"  complete tree, n = 131071: BFS peak queue = {peak} entries "
          f"(~n/2)")
    print(f"  the same tree, DFS peak stack = {peak_dfs} entries (~the height)")
    print("  BFS's early exit costs memory proportional to the widest level it")
    print("  reaches. On a tree that is wide and uniformly deep you pay O(n)")
    print("  space to save nothing — mention the trade, don't pretend BFS wins")
    print("  everywhere.")

    # ----------------------------------------------------------------------
    # Recursion limit: 10^5 is inside LeetCode's constraints.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  a chain of 100,000 nodes (LC 111 allows 10^5) ---")
    deep = build_skewed(100_000, "left")
    raised = False
    try:
        sol.minDepth_dfs(deep)
        print("  DFS recursion: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  DFS recursion: RecursionError -> {e}")
    t0 = time.perf_counter()
    bfs_answer = sol.minDepth(deep)
    bfs_ms = (time.perf_counter() - t0) * 1000
    print(f"  BFS          : {bfs_answer} in {bfs_ms:.1f}ms, queue never held "
          f"more than 1 node")
    print(f"  iterative DFS: {sol.minDepth_stack_pruned(deep)}")
    all_ok &= (raised and bfs_answer == 100_000)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
