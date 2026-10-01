"""
================================================================================
SOLUTION · LeetCode 1192 · Critical Connections in a Network             [Hard]
https://leetcode.com/problems/critical-connections-in-a-network/
================================================================================

THE CORE IDEA
--------------
A "critical connection" IS a bridge (topic guide Part 6): an edge whose
removal disconnects the graph, equivalently an edge on NO cycle. Tarjan's
algorithm finds every bridge in ONE DFS pass using two per-node values:

    disc[u] -- the DFS discovery time of u (assigned once, in visit order)
    low[u]  -- the lowest discovery time reachable from u's subtree,
               including via AT MOST ONE back-edge to an ancestor (never
               back through the tree edge to u's own immediate parent)

    low[u] = min(disc[u],
                  min(disc[v] for each back-edge u->v to a visited ancestor),
                  min(low[c]  for each DFS-tree child c of u))

Bridge test: after fully exploring DFS-tree child c of u, edge (u,c) is a
bridge iff `low[c] > disc[u]` -- nothing in c's ENTIRE subtree can reach
back up to u or higher through any other route, so (u,c) is the only
connection holding that subtree on.

MUST be ITERATIVE, not recursive -- n up to 10^5, and a path graph (the
worst case for bridge-finding, since every edge in a path IS a bridge) is
exactly the shape that blows Python's default 1000-frame recursion limit.
The iterative version uses an explicit stack that stores, per frame,
which neighbor-iterator position it was paused at, so the low-link update
against a child can still happen after that child's "virtual return."

O(V + E) time, O(V + E) space.


================================================================================
WHY THE PARENT EDGE MUST BE SKIPPED (NOT TREATED AS A BACK-EDGE)
================================================================================
In an undirected graph, the edge you just walked DOWN from u to child c
also appears in c's own adjacency list, pointing back at u -- but that is
the TREE EDGE you arrived on, not a genuine back-edge to an ancestor. If
c's DFS naively treats "u is already visited" as a back-edge and folds
`disc[u]` into `low[c]`, then `low[c]` becomes <= `disc[u]` FOR EVERY
SINGLE EDGE in the entire graph, and the bridge test `low[c] > disc[u]`
NEVER fires -- the algorithm silently reports ZERO bridges, even ones that
obviously exist (e.g. a single edge connecting two otherwise-disconnected
halves). This is catastrophic and easy to miss because it produces a
plausible-looking EMPTY list rather than an exception. Demoed live below.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): for EACH of the E edges,
remove it, run a fresh BFS/DFS to check whether the graph is still fully
connected, put it back. O(E * (V+E)) -- at E up to 10^5, roughly 10^10
operations worst case. Correct, hopelessly slow at this problem's bounds.

Approach 1 (Tarjan's bridges, iterative) [checked] -- the answer above.
O(V+E), a single pass.

Approach 2 (Tarjan's bridges, RECURSIVE) -- textbook-elegant, identical
logic, but raises RecursionError on the exact worst-case input this
problem is MOST likely to stress-test (a long path graph). Demoed live
below breaking on a 5,000-node chain.


================================================================================
STEP BY STEP TRACE
================================================================================
n=6, connections = [[0,1],[1,2],[2,0],[1,3],[3,4],[4,5],[5,3]]
(two triangles {0,1,2} and {3,4,5}, joined by the single edge 1-3)

DFS from 0 (adjacency order as given, e.g. adj[0]=[1,2], adj[1]=[0,2,3], ...):
    visit 0: disc[0]=low[0]=0
      visit 1 (child of 0): disc[1]=low[1]=1
        visit 2 (child of 1): disc[2]=low[2]=2
          neighbor 0 of 2: visited, NOT parent(1) -> back-edge!
            low[2] = min(low[2], disc[0]) = min(2, 0) = 0
          neighbor 1 of 2: that's 2's parent -> skip
        2 fully explored. Pop back to 1: low[1] = min(low[1], low[2]) = min(1,0) = 0
        bridge check (1,2): low[2]=0 > disc[1]=1? NO -> not a bridge
        neighbor 2 of 1: already visited (just finished) -> would be back-
          edge check but disc[2] > disc[1] so this doesn't lower low[1]
          further than it already is (harmless either way)
        visit 3 (child of 1): disc[3]=low[3]=3
          visit 4 (child of 3): disc[4]=low[4]=4
            visit 5 (child of 4): disc[5]=low[5]=5
              neighbor 3 of 5: visited, NOT parent(4) -> back-edge!
                low[5] = min(low[5], disc[3]) = min(5,3) = 3
              neighbor 4 of 5: that's 5's parent -> skip
            5 fully explored. Pop to 4: low[4] = min(low[4], low[5]) = min(4,3) = 3
            bridge check (4,5): low[5]=3 > disc[4]=4? NO -> not a bridge
          4 fully explored. Pop to 3: low[3] = min(low[3], low[4]) = min(3,3) = 3
          bridge check (3,4): low[4]=3 > disc[3]=3? NO -> not a bridge
          neighbor 5 of 3: visited (already fully explored), not parent(1)
            -> back-edge: low[3] = min(low[3], disc[5]) = min(3,5) = 3 (no change)
        3 fully explored. Pop to 1: low[1] = min(low[1], low[3]) = min(0,3) = 0
        bridge check (1,3): low[3]=3 > disc[1]=1? YES -> BRIDGE (1,3)!
      1 fully explored. Pop to 0: low[0] = min(low[0], low[1]) = min(0,0) = 0
      bridge check (0,1): low[1]=0 > disc[0]=0? NO -> not a bridge
      neighbor 2 of 0: visited, not parent(-1, 0 is the DFS root) -> back-edge:
        low[0] = min(low[0], disc[2]) = min(0,2) = 0 (no change)

Result: [[1,3]]  MATCHES expected output. The single edge joining the two
triangles is correctly identified as the only bridge; every triangle edge
has a second route around it (the other two sides) and is correctly
rejected.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time            Space  Mutates input?
    -------------------------------------  --------------  -----  --------------
    Brute-force remove-edge-and-check       O(E*(V+E))      O(V+E) no
    Tarjan's bridges, iterative [chosen]    O(V+E)          O(V+E) no
    Tarjan's bridges, recursive             O(V+E)          O(V+E) no -- but
                                                                    can RecursionError


================================================================================
EDGE CASES
================================================================================
    n == 2, single edge          -> that one edge is trivially the only
                                    connection AND trivially a bridge --
                                    Example 2.
    a graph that is ALREADY a    -> every single edge is a bridge; there
    tree (no cycles at all)         are no back-edges anywhere, so every
                                    child's low[] equals its own disc[],
                                    which is always > its parent's disc[].
    a graph with no bridges at    -> a single large cycle, or a 2-edge-
    all (fully "2-edge-connected") connected graph in general -- every
                                    node has an alternate route, result is
                                    the empty list.
    disconnected graph            -> excluded by this problem's own
                                    framing ("any server can reach any
                                    other"), but the algorithm handles it
                                    correctly regardless by looping the
                                    outer DFS start over every unvisited
                                    node (multiple DFS trees, one per
                                    component).
    a long PATH graph (worst      -> every single edge is a bridge (n-1 of
    case for both correctness       them); this is ALSO the worst case for
    stress-testing and for          recursion depth, since the DFS goes
    recursion depth)                 exactly n levels deep with no
                                    branching at all. Demoed live below.
    multiple back-edges from the  -> `low[u]` takes the MINIMUM across ALL
    same node to different           of them, not just the first found --
    ancestors                        important detail, easy to get right
                                    by just always taking `min(...)`.


================================================================================
COMMON MISTAKES
================================================================================
1. Treating the tree edge back to the IMMEDIATE PARENT as if it were a
   genuine back-edge (folding `disc[parent]` into the child's `low[]`
   unconditionally). This silently makes EVERY bridge test fail, so the
   algorithm reports zero bridges on any graph, including ones with
   obvious ones. Demoed live below -- catastrophic and easy to miss since
   it raises no exception.

2. Writing this recursively without checking against this problem's own
   stated bounds (n up to 10^5). A path-shaped input -- exactly the input
   most likely to appear in a bridge-finding stress test, since every one
   of its edges IS a bridge -- forces recursion depth equal to n, blowing
   Python's default 1000-frame limit. Demoed live below.

3. Updating `low[u]` using `disc[v]` for a TREE edge (child not yet fully
   explored) instead of `low[child]` once it IS fully explored. These are
   different quantities: `disc[child]` is fixed at discovery time and
   never reflects what the child's own subtree can reach; `low[child]` is
   what must be propagated up once the child's entire subtree has been
   walked.

4. In the iterative version, discarding the neighbor-iterator's position
   when "returning" from a child instead of resuming it exactly where it
   left off (e.g., rebuilding a fresh `iter(adj[u])` from scratch after a
   child returns) -- silently reprocesses already-visited neighbors,
   which doesn't necessarily corrupt the disc/low VALUES (those are
   idempotent to re-relaxation) but can push the same child onto the
   stack twice, corrupting the traversal.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would you find ARTICULATION POINTS (cut vertices) instead of
   bridges?
A: The same disc[]/low[] machinery, with a different test: a non-root
   node u is an articulation point if it has some DFS-tree child c with
   `low[c] >= disc[u]` (note: `>=`, not strict `>` -- a shared boundary
   still cuts the node itself, even if the EDGE isn't a bridge). The root
   of a DFS tree is a special case: it's an articulation point iff it has
   TWO OR MORE DFS-tree children (removing it splits its children's
   subtrees apart from each other).

Q: What if the graph could have multiple parallel edges between the same
   pair of nodes?
A: The parent-skip must be done by EDGE IDENTITY (track which specific
   edge index you arrived on), not by NODE identity -- with a node-based
   "is this neighbor my parent" check, a second parallel edge back to the
   same parent would be wrongly skipped as if it were the tree edge, when
   it is actually a genuine alternate route (meaning the original tree
   edge would then NOT be a bridge, since the parallel edge provides a
   second connection). This problem's constraints rule this out ("no
   repeated connections"), but it's worth flagging as a real-world gotcha.

Q: Could you solve this with Union-Find instead?
A: Not directly for arbitrary graphs -- Union-Find naturally answers
   "does adding this edge create a cycle," which is closer to Kruskal's
   MST territory (problems 005/011) than to bridge-finding, which
   inherently needs the DFS TREE STRUCTURE (parent/child/ancestor
   relationships) that Union-Find's flat set representation doesn't
   preserve.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 1568 Minimum Number of Days to Disconnect Island (a different but
            related "how fragile is this connectivity" question, grid-
            shaped, uses articulation-point-style reasoning)
    LC 928  Minimize Malware Spread II (articulation-point-flavored
            reasoning about which single node's removal changes reachability)
    LC 261  Graph Valid Tree (topic 14 -- the plain "is this connected and
            acyclic" check that a graph WITHOUT any bridges would fail in
            a different way)
    LC 332  Reconstruct Itinerary (010 -- a different DFS-with-careful-
            bookkeeping graph algorithm, Hierholzer's Eulerian path)
================================================================================
"""

import sys
from collections import defaultdict
from typing import List


class Solution:
    def criticalConnections(self, n: int, connections: List[List[int]]) -> List[List[int]]:
        """✅ Tarjan's bridge-finding, iterative (explicit stack).
        O(V+E) time, O(V+E) space."""
        adj = defaultdict(list)
        for a, b in connections:
            adj[a].append(b)
            adj[b].append(a)

        disc = [-1] * n
        low = [0] * n
        timer = 0
        bridges = []

        for start in range(n):
            if disc[start] != -1:
                continue
            disc[start] = low[start] = timer
            timer += 1
            stack = [(start, -1, iter(adj[start]))]

            while stack:
                u, parent, it = stack[-1]
                advanced = False
                for v in it:
                    if v == parent:
                        continue                        # skip the tree edge back
                    if disc[v] == -1:
                        disc[v] = low[v] = timer
                        timer += 1
                        stack.append((v, u, iter(adj[v])))
                        advanced = True
                        break
                    else:
                        low[u] = min(low[u], disc[v])   # genuine back-edge
                if not advanced:
                    stack.pop()
                    if stack:
                        low[parent] = min(low[parent], low[u])
                        if low[u] > disc[parent]:
                            bridges.append([parent, u])

        return bridges

    def criticalConnections_recursive(self, n: int,
                                      connections: List[List[int]]) -> List[List[int]]:
        """Alternative: the textbook RECURSIVE form. Elegant, but can
        raise RecursionError on a long chain -- demoed below."""
        adj = defaultdict(list)
        for a, b in connections:
            adj[a].append(b)
            adj[b].append(a)

        disc = [-1] * n
        low = [0] * n
        timer = 0
        bridges = []

        def dfs(u: int, parent: int) -> None:
            nonlocal timer
            disc[u] = low[u] = timer
            timer += 1
            for v in adj[u]:
                if v == parent:
                    continue
                if disc[v] == -1:
                    dfs(v, u)
                    low[u] = min(low[u], low[v])
                    if low[v] > disc[u]:
                        bridges.append([u, v])
                else:
                    low[u] = min(low[u], disc[v])

        for start in range(n):
            if disc[start] == -1:
                dfs(start, -1)

        return bridges

    def criticalConnections_no_parent_skip_BROKEN(self, n: int,
                                                   connections: List[List[int]]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE -- mistake #1. Treats the tree edge back to
        the immediate parent as a genuine back-edge instead of skipping
        it. Demoed live below."""
        adj = defaultdict(list)
        for a, b in connections:
            adj[a].append(b)
            adj[b].append(a)

        disc = [-1] * n
        low = [0] * n
        timer = 0
        bridges = []

        def dfs(u: int, parent: int) -> None:
            nonlocal timer
            disc[u] = low[u] = timer
            timer += 1
            for v in adj[u]:
                # NOTE: no `if v == parent: continue` -- BUG
                if disc[v] == -1:
                    dfs(v, u)
                    low[u] = min(low[u], low[v])
                    if low[v] > disc[u]:
                        bridges.append([u, v])
                else:
                    low[u] = min(low[u], disc[v])   # wrongly includes parent

        for start in range(n):
            if disc[start] == -1:
                dfs(start, -1)

        return bridges


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def normalize(edges):
        return sorted(tuple(sorted(e)) for e in edges)

    cases = [
        (4, [[0, 1], [1, 2], [2, 0], [1, 3]], [[1, 3]]),
        (2, [[0, 1]], [[0, 1]]),
        (6, [[0, 1], [1, 2], [2, 0], [1, 3], [3, 4], [4, 5], [5, 3]], [[1, 3]]),
    ]

    print("--- correctness: iterative vs recursive Tarjan's agree ---")
    for n, connections, want in cases:
        got_iter = sol.criticalConnections(n, [c[:] for c in connections])
        got_rec = sol.criticalConnections_recursive(n, [c[:] for c in connections])
        ok = (normalize(got_iter) == normalize(want) and
              normalize(got_rec) == normalize(want))
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}  iter={got_iter} "
              f"rec={got_rec}  (want {want})")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: skipping the parent-edge check entirely.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, no parent-edge skip ---")
    n, connections = 4, [[0, 1], [1, 2], [2, 0], [1, 3]]
    correct = sol.criticalConnections(n, connections)
    broken = sol.criticalConnections_no_parent_skip_BROKEN(n, connections)
    print(f"  n={n}, connections={connections}  (two triangles/cycles joined "
          f"by one true bridge, edge 1-3)")
    print(f"  correct (skips parent edge):     {sorted(normalize(correct))}")
    print(f"  broken  (no parent-edge skip):    {sorted(normalize(broken))}")
    exposed = len(broken) == 0 and len(correct) > 0
    print(f"  the broken version reports ZERO bridges on a graph that "
          f"clearly has one: {exposed}  (no exception raised, just an "
          f"empty, plausible-looking list)")
    all_ok &= exposed

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: recursion depth on a long path graph (worst case for
    # BOTH correctness stress-testing and recursion depth simultaneously).
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: recursive Tarjan's on a 5000-node path ---")
    n = 5000
    connections = [[i, i + 1] for i in range(n - 1)]
    print(f"  sys.getrecursionlimit() = {sys.getrecursionlimit()}, "
          f"path length = {n} nodes ({n - 1} edges, ALL of them bridges)")
    it_result = sol.criticalConnections(n, connections)
    it_ok = len(it_result) == n - 1
    print(f"  iterative: found all {len(it_result)} bridges (expected "
          f"{n - 1}) -> {it_ok}")
    raised = False
    try:
        sol.criticalConnections_recursive(n, connections)
        print("  recursive: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: {it_ok and raised}")
    all_ok &= it_ok and raised

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
