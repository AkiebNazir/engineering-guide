"""
================================================================================
SOLUTION · LeetCode 968 · Binary Tree Cameras                            [Hard]
https://leetcode.com/problems/binary-tree-cameras/
================================================================================

THE CORE IDEA
--------------
Greedy post-order DFS returning one of three states per subtree: 0 (not
covered), 1 (covered, no camera here), 2 (has a camera). At each node: if
either child is uncovered (0), you MUST place a camera here right now (return
2, count it) — deferring would leave that child permanently unmonitored once
its own subtree is done being processed. Else if either child has a camera
(2), this node is covered by it (return 1). Otherwise (both children covered-
without-a-camera, or this is a leaf) this node is itself uncovered (return 0)
and the decision is deferred to its parent. After the traversal, if the ROOT
ends up at state 0, add one final camera (nothing above it to rescue it).


================================================================================
MULTIPLE APPROACHES
================================================================================
1. BRUTE-FORCE / EXHAUSTIVE SUBSET SEARCH — try every subset of nodes as
   camera locations, check coverage, keep the smallest valid subset. Priced,
   not written: O(2^n) subsets, each requiring an O(n) coverage check —
   utterly infeasible past a handful of nodes, and the problem allows up to
   1000 nodes.
2. TREE DP WITH EXPLICIT DP VALUES per node (min cameras for the subtree
   under each of 3 assumptions about this node's own state) — this is the
   textbook DP framing of the SAME greedy insight; mathematically equivalent
   to approach 3 but usually written more verbosely with three explicit
   integer return values per node instead of one state code plus a shared
   counter. Not written separately here since it collapses to the same
   algorithm; the greedy states already ARE the DP states.
3. GREEDY POST-ORDER WITH 3 STATES (the intended answer) — O(n) time,
   written below as the primary solution.


================================================================================
STEP BY STEP TRACE — root = [0,0,None,0,0]  (a "root with one child, that
child has two leaf children" shape: root -> left child -> two grandchildren)
================================================================================
Tree shape:
            root
            /
          mid
         /   \
       leafL leafR

    dfs(leafL): no children (both None -> treated as state 1) ->
                neither child is 0, neither is 2 -> return 0 (leaf, uncovered)
    dfs(leafR): same reasoning -> return 0
    dfs(mid):   children are leafL=0, leafR=0 -> AT LEAST ONE CHILD IS 0
                -> place a camera at mid. cameras=1. return 2.
    dfs(root):  children are mid=2, (right=None -> state 1)
                -> no child is 0; at least one child (mid) is 2
                -> root is covered by mid's camera. return 1. (no new camera)

    Final check: dfs(root) == 1, not 0 -> no extra camera needed for root.
    Total cameras = 1.                                    (matches expected)

Notice the single camera at `mid` covers `mid` itself, both its leaf
children, AND its parent `root` — exactly the "camera at parent, itself, and
children" rule from the problem statement, achieved by pushing the camera as
low as possible instead of, say, putting it at `root` (which would leave
`leafL`/`leafR` uncovered and need 2 more cameras).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time     Space   Mutates input?  Note
    ---------------------------  -------  ------  ---------------  --------------------------------
    Greedy post-order, 3 states  O(n)     O(h)    no               h = tree height (recursion stack)
    Brute-force subset search   O(2^n * n)  O(n)  no               priced only; infeasible for n=1000


================================================================================
EDGE CASES
================================================================================
    Single node, root=[0]        -> root has no children (both treated as
                                    state 1); root itself returns state 0
                                    (leaf-like), triggers the FINAL root-check
                                    -> exactly 1 camera.
    Root with one child, [0,0]   -> child is a leaf (state 0); root sees a
                                    0-state child and places a camera at the
                                    ROOT (not the child!) -> 1 camera total,
                                    covering both nodes.
    A missing child (None)       -> must be treated as state 1 (covered, no
                                    camera), NEVER as state 0 — otherwise a
                                    node with only one real child would think
                                    its (nonexistent) other child is
                                    uncovered and place an unnecessary camera.
    Long right-skewed chain      -> exercises that cameras get placed at
                                    every OTHER level (roughly), not every
                                    node and not just at the very top —
                                    demonstrated below with a 4-node chain.


================================================================================
COMMON MISTAKES
================================================================================
1. Treating a missing (`None`) child as state 0 instead of state 1 — this is
   the single most common bug in this problem, and it causes a camera to be
   placed at EVERY leaf-parent unnecessarily (since a real leaf child at
   state 0 combined with a phantom "missing child is also state 0" still
   triggers the camera rule, but so does a node with a SINGLE real child
   whose sibling doesn't exist — the None child must never demand coverage).
2. Checking "either child is 2 -> covered" BEFORE checking "either child is
   0 -> place camera" — if a node has one child at state 0 and the other at
   state 2, checking the state-2 branch first would incorrectly mark this
   node "covered" and skip placing the camera the state-0 child actually
   needs; the state-0 check must run first and take priority.
3. Placing a camera at every LEAF preemptively (a tempting "cover the
   hardest-to-reach nodes first" instinct) — this is never optimal, since a
   single camera one level up (at the leaf's parent) covers the same leaf
   plus its sibling plus the parent itself plus the grandparent, strictly
   dominating a leaf-only camera in coverage per camera placed.
4. Forgetting the FINAL root-level check — if the whole traversal finishes
   with the root at state 0 (nothing forced a camera onto it or its
   children), the count as computed during the traversal UNDER-counts by
   exactly one; this final check is not optional bookkeeping, it's a real
   case (e.g. the single-node tree).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is greedily placing cameras as deep as possible always optimal, not
   just a reasonable-sounding heuristic?
A: Any valid camera placement can be transformed into a "cameras pushed as
   low as possible" placement of AT MOST the same size: whenever a camera
   sits at a node whose subtree has no uncovered node forcing it there, it
   can be removed or pushed down without breaking coverage above (its
   parent, if it needs coverage, can get its own camera at the parent
   level, no worse than before). This exchange argument is the standard
   proof that the greedy post-order rule never does worse than optimal, and
   by construction it also never places a redundant camera, so it matches
   optimal exactly.

Q: How would this change for an n-ary tree instead of binary?
A: The same 3-state post-order rule applies unchanged — check whether ANY
   child (out of however many there are) is state 0, then whether ANY child
   is state 2, else return 0 — the binary-specific part is only "children"
   being named `left`/`right` instead of a list.

Q: What if some nodes could never hold a camera (e.g. a "no-camera-zone"
   constraint)?
A: The pure greedy 3-state trick breaks down — you'd need actual DP with
   explicit min-cost values per node under each coverage assumption (the
   "approach 2" framing mentioned above), since the greedy exchange argument
   relies on being able to place a camera at ANY node that needs one.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 337  House Robber III (this folder, 014) — same post-order "combine
            children's answers into this node's answer" tree-DP shape,
            simpler (no coverage/monitoring state, just include/exclude).
    LC 979  Distribute Coins in Binary Tree (this folder, 018) — another
            post-order tree problem where each node's contribution depends
            on a running "excess/deficit" passed up from children.
    Topic 10 (Trees) — the general post-order "compute children first,
            combine at parent" family this problem's core technique belongs
            to.
================================================================================
"""

from typing import List, Optional


class TreeNode:
    def __init__(self, val=0, left=None, right=None):
        self.val = val
        self.left = left
        self.right = right


def build_tree(rows: List[Optional[int]]) -> Optional[TreeNode]:
    if not rows or rows[0] is None:
        return None
    it = iter(rows)
    root = TreeNode(next(it))
    queue = [root]
    while queue:
        node = queue.pop(0)
        try:
            lv = next(it)
        except StopIteration:
            break
        if lv is not None:
            node.left = TreeNode(lv)
            queue.append(node.left)
        try:
            rv = next(it)
        except StopIteration:
            break
        if rv is not None:
            node.right = TreeNode(rv)
            queue.append(node.right)
    return root


NOT_COVERED, COVERED_NO_CAMERA, HAS_CAMERA = 0, 1, 2


class Solution:
    def minCameraCover(self, root: Optional[TreeNode]) -> int:
        """Greedy post-order with 3 states. O(n) time, O(h) space."""
        cameras = 0

        def dfs(node: Optional[TreeNode]) -> int:
            nonlocal cameras
            if node is None:
                return COVERED_NO_CAMERA
            left_state = dfs(node.left)
            right_state = dfs(node.right)
            if left_state == NOT_COVERED or right_state == NOT_COVERED:
                cameras += 1
                return HAS_CAMERA
            if left_state == HAS_CAMERA or right_state == HAS_CAMERA:
                return COVERED_NO_CAMERA
            return NOT_COVERED

        if dfs(root) == NOT_COVERED:
            cameras += 1
        return cameras

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def minCameraCover_brute_force(self, root: Optional[TreeNode]) -> int:
        """WRONG SCALING, kept only to demonstrate correctness on tiny trees
        via exhaustive subset search. O(2^n * n) time."""
        nodes: List[TreeNode] = []

        def collect(node: Optional[TreeNode]) -> None:
            if node is None:
                return
            nodes.append(node)
            collect(node.left)
            collect(node.right)

        collect(root)
        n = len(nodes)
        parent = {}

        def link(node, par):
            if node is None:
                return
            parent[node] = par
            link(node.left, node)
            link(node.right, node)

        link(root, None)

        def covers(camera_set):
            covered = set()
            for node in camera_set:
                covered.add(id(node))
                if node.left is not None:
                    covered.add(id(node.left))
                if node.right is not None:
                    covered.add(id(node.right))
                if parent.get(node) is not None:
                    covered.add(id(parent[node]))
            return all(id(node) in covered for node in nodes)

        best = n  # worst case: a camera on every node always works
        for mask in range(1 << n):
            chosen = [nodes[i] for i in range(n) if (mask >> i) & 1]
            if len(chosen) < best and covers(chosen):
                best = len(chosen)
        return best


# ==============================================================================
# TESTS — run:  python 025_binary_tree_cameras_solution.py
# ==============================================================================
CASES = [
    ([0, 0, None, 0, 0], 1),
    ([0, 0, None, 0, None, 0, None, None, 0], 2),
    ([0], 1),
    ([0, 0], 1),
    ([0, None, 0, None, 0, None, 0], 2),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    ok = True
    for rows, expected in CASES:
        root = build_tree(rows)
        got = sol.minCameraCover(root)
        if got != expected:
            ok = False
        print(f"{'PASS' if got == expected else 'FAIL'}  minCameraCover({rows}) -> {got}  (want {expected})")
    all_ok &= ok

    # ----------------------------------------------------------------------
    # Cross-check the greedy answer against brute-force exhaustive search on
    # every small tree above (n <= 9, so 2^9 = 512 subsets — fast).
    # ----------------------------------------------------------------------
    print("\n--- greedy vs brute-force exhaustive search, cross-checked live ---")
    for rows, _ in CASES:
        root = build_tree(rows)
        greedy = sol.minCameraCover(root)
        brute = sol.minCameraCover_brute_force(root)
        match = greedy == brute
        all_ok &= match
        print(f"  {'PASS' if match else 'FAIL'}  {rows}: greedy={greedy}, brute-force={brute}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
