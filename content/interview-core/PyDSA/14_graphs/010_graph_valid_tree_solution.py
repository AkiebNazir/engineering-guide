r"""
================================================================================
SOLUTION · LeetCode 261 · Graph Valid Tree                           [Medium]
https://leetcode.com/problems/graph-valid-tree/
================================================================================

THE CORE IDEA
--------------
A graph with n nodes is a valid tree if and only if BOTH hold:

    1. It has EXACTLY n - 1 edges.
    2. It is fully connected — exactly ONE connected component.

Neither condition alone is sufficient — this file's whole point is to PROVE
that live, with two concrete counterexamples, not just assert it:

    - A graph can have exactly n-1 edges and still be DISCONNECTED, if a
      cycle in one part of the graph "pays for" a missing edge somewhere
      else. Edge count matches, connectivity does not. NOT a tree.
    - A graph can be fully CONNECTED and still not be a tree, if it has one
      edge more than n-1 — that extra edge is, by the pigeonhole-style
      argument below, guaranteed to close a cycle somewhere. Connected,
      but NOT a tree.

    def validTree(n, edges):
        if len(edges) != n - 1:
            return False                       # necessary, cheap, O(1)
        <run one connectivity check (problem 009's algorithm)>
        return <is exactly one component>

Why "exactly n-1 edges" is the right threshold, not just a rule to
memorize: connecting n nodes into a single piece requires at least n-1
edges (induction: 1 node needs 0 edges to be "connected" to itself; adding
node k+1 to an already-connected group of k nodes needs at least 1 new
edge). Every edge beyond that minimum connects two nodes that a shorter
path ALREADY reaches — and a second path between two already-connected
nodes is, by definition, a cycle. So: n-1 edges is the exact edge count of
a connected graph with ZERO cycles, which is precisely the definition of a
tree.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): run full cycle detection (topic guide
§4.1, undirected parent-skip DFS) across every component AND separately
count components (Part 3) — two full traversals instead of one, and no
edge-count shortcut. Correct, but does strictly more work than necessary
for no benefit; the count check below gets one of the two facts for O(1)
instead of a whole traversal.

Approach 1 (edge count + one connectivity pass) ✅ — the answer. Check
`len(edges) == n - 1` in O(1); if that fails, return `False` immediately
without touching the graph at all. Otherwise run exactly ONE connectivity
traversal (problem 009's `countComponents` logic, short-circuited to a
boolean): if it reaches all n nodes, the graph is connected AND (because
the edge count already matches) acyclic, so it's a tree. O(V + E) time,
O(V + E) space.

Approach 2 (Union-Find, cycle-as-you-go) — process edges one at a time; if
`find(u) == find(v)` for an edge you're about to add, its two endpoints are
ALREADY connected by some earlier edge, so this edge would create a cycle
-> return `False` immediately. If all edges union cleanly, finish with one
more check: the number of distinct roots must be 1 (equivalently: after
`len(edges)` successful unions, the whole thing collapsed to one root before
even needing the n-1 count). This catches a cycle without ever finishing
the edge list, and it's the natural setup for problem 013 (Redundant
Connection), which is the SAME check but the question is "which edge is
the redundant one" instead of "is the final graph a tree". Union-Find
proper is topic 15's subject — implemented below only as a cross-check
against Approach 1, per this folder's convention (topic guide's 013 note).


================================================================================
⚠️  WHY YOU CANNOT DROP EITHER CHECK — TWO LIVE COUNTEREXAMPLES
================================================================================
This is the entire teaching point of LC 261, and the demo in run_tests()
below constructs both graphs and runs the real algorithm on them so the
claim is measured, not just stated.

Counterexample A — exactly n-1 edges, but DISCONNECTED (edge-count check
alone is NOT sufficient):

    n = 5, edges = [[0,1],[2,3],[3,4],[2,4]]

        0 --- 1        2 --- 3
                         \   /
                          \ /
                           4

    len(edges) = 4 = n - 1  ✅ passes the count check
    components: {0,1} and {2,3,4}  -> 2 components, NOT 1  ✗ fails connectivity

    The triangle {2,3,4} has one cycle (one edge "too many" for that piece
    in isolation), and the missing edge between {0,1} and {2,3,4} is
    exactly one edge "too few" — they cancel in the TOTAL count. A checker
    that only counts edges reports this as a tree. It is not: node 0 cannot
    reach node 2 at all.

Counterexample B — fully CONNECTED, but has n edges, one too many
(connectivity check alone is NOT sufficient):

    n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]

            0     4
             \   /
              1
             /|
            2 |
             \|
              3

    Every node IS reachable from every other node — 1 component ✅
    len(edges) = 5, n - 1 = 4  -> 5 != 4  ✗ fails the count check

    Nodes {1,2,3} form a triangle: 1-2, 2-3, 1-3 is a cycle. A checker that
    only verifies connectivity (and skips the edge count) reports this as a
    tree. It is not: there are two distinct paths from 1 to 3 (direct, and
    via 2), which is exactly what a cycle means.

Both graphs are constructed and run through the real `validTree` below,
alongside two DELIBERATELY INCOMPLETE checkers — one that only counts edges,
one that only checks connectivity — to show each incomplete checker gets
EXACTLY ONE of the two counterexamples wrong.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]   (Example 1, a real tree)

    Step 1 — edge count: len(edges) = 4, n - 1 = 4  ->  4 == 4  ✅ continue

    Step 2 — build adjacency list:
        0: [1,2,3]   1: [0,4]   2: [0]   3: [0]   4: [1]

    Step 3 — one connectivity traversal from node 0:
        visited={0} -> push 1,2,3
        pop 3 -> visited={0,3}, neighbor 0 seen
        pop 2 -> visited={0,2,3}, neighbor 0 seen
        pop 1 -> visited={0,1,2,3}, push 4 (0 seen)
        pop 4 -> visited={0,1,2,3,4}, neighbor 1 seen
        stack empty. len(visited) = 5 = n  ✅

    Both checks pass -> True. Draw it: 0 is the root with three children
    (1,2,3), and 4 hangs off 1 — a clean tree shape, no cycles, everyone
    reachable from node 0 in a single pass.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time        Space    Mutates input?  Note
    ------------------------------ ----------  -------  --------------  ------------------------
    Cycle-detect + components       O(V+E)      O(V+E)   no              correct but 2 full passes
    (brute force)
    Edge count + 1 connectivity      O(V + E)    O(V+E)   no              answer; count check short-
    pass ✅                                                                circuits most invalid input
    Union-Find, cycle-as-you-go       O(E*alpha(V)) O(V)   no              can bail out EARLY on the
                                                                          first cycle-closing edge

    Neither check alone is in this table as a "valid approach" — the demo
    below shows exactly why: each one, used alone, is WRONG on one of the
    two counterexample graphs.


================================================================================
EDGE CASES
================================================================================
    n = 1, edges = []           -> True. A single node with no edges is,
                                    by definition, a (trivial, one-node)
                                    tree: n-1 = 0 edges, 1 component.
    n = 2, edges = []            -> False. n-1 = 1 edge required to connect
                                    2 nodes; 0 edges means disconnected —
                                    caught by the O(1) count check alone,
                                    no traversal even needed.
    len(edges) != n - 1           -> always False, and always detectable in
                                    O(1) before touching the graph at all —
                                    the cheapest possible short-circuit.
    exactly n-1 edges, cycle       -> the counterexample this whole problem
    hidden in one component,         is built to test: MUST run the
    disconnected elsewhere            connectivity check, not stop at the
                                     count. (Counterexample A above.)
    self-loop / duplicate edge     -> excluded by the constraints (ai != bi,
                                    no repeated edges); if one slipped
                                    through, it would silently make the
                                    edge count look higher than the true
                                    number of DISTINCT connections and the
                                    n-1 check would (correctly) reject it.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking ONLY `len(edges) == n - 1` and skipping connectivity, assuming
   the count alone proves it's a tree. Counterexample A above is a graph
   with exactly n-1 edges that is two disconnected pieces (a cycle in one
   piece cancels a missing edge in the other) — the count check alone
   reports `True` and is wrong.

2. Checking ONLY connectivity (one full traversal reaches all n nodes) and
   skipping the edge count, assuming "everyone is reachable" is enough.
   Counterexample B above is fully connected with one cycle — the
   connectivity check alone reports `True` and is wrong.

3. Building the adjacency list with only one direction for an undirected
   edge (topic guide Part 10, mistake #7) — breaks the connectivity check
   silently, usually making the graph LOOK disconnected when it is not.

4. Forgetting the O(1) short-circuit: `len(edges) != n - 1` is by far the
   cheapest check and eliminates most malformed inputs before any traversal
   — always run it first.

5. Off-by-one on `n - 1`, e.g. comparing against `n` or `len(edges) - 1`.
   Get the base case (n=1, 0 edges) right first and the formula falls out
   naturally.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the graph is DIRECTED — is it a valid rooted tree?
A: Different, harder problem: every node except the root must have
   in-degree exactly 1, the root has in-degree 0, and the underlying
   undirected graph must be connected and acyclic. Simple edge counting no
   longer suffices on its own because direction matters (see LC 1462-style
   "minimum height trees" and LC 685 "Redundant Connection II" for the
   directed analogue).

Q: Given the edges are NOT necessarily a tree, find the one redundant edge
   that, if removed, WOULD make it a tree.
A: LC 684, problem 013 in this folder — add edges one at a time with
   Union-Find; the first edge whose two endpoints are already connected
   (same root) is the redundant one. Same underlying fact as Approach 2
   here, turned into "which edge" instead of "is it a tree".

Q: How would you check this without ever materializing an adjacency list,
   e.g. edges arrive as a stream and you need the answer to update online?
A: Union-Find is the right structure for streaming/incremental
   connectivity: maintain `parent`/`size` arrays across calls; each new
   edge is one `union`, each connectivity query is O(alpha(V)). A rebuilt
   adjacency-list DFS would redo O(V+E) work on every update; Union-Find
   amortizes it.

Q: What's the minimum number of edges to add to make an arbitrary
   (possibly disconnected, possibly cyclic) graph connected?
A: `components - 1`, where `components` is the connected-component count
   from problem 009 — you need one bridging edge per extra component,
   regardless of how many cycles exist inside any of them (LC 1319).


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 3 (connected components) + Part 4's cycle-detection machinery,
combined into one decision.

    LC 323  Number of Connected Components — the connectivity half, alone (009)
    LC 684  Redundant Connection            — Union-Find, "which edge" (013)
    LC 685  Redundant Connection II         — the directed, harder cousin
    LC 1319 Number of Operations to Make    — components - 1 bridging edges
            Network Connected
    LC 1466 Reorder Routes to Make All      — directed connectivity + edge
            Paths Lead to the City Zero        direction counting
================================================================================
"""

from collections import deque
from typing import List


class Solution:
    def validTree(self, n: int, edges: List[List[int]]) -> bool:
        """✅ THE ANSWER — O(1) edge-count short-circuit, then ONE
        connectivity traversal (iterative BFS). O(V + E) time/space."""
        if len(edges) != n - 1:
            return False
        if n <= 1:
            return True

        graph = {i: [] for i in range(n)}
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)

        visited = {0}
        queue = deque([0])
        while queue:
            node = queue.popleft()
            for nxt in graph[node]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)

        return len(visited) == n

    def validTree_unionfind(self, n: int, edges: List[List[int]]) -> bool:
        """Union-Find preview (topic 15's actual subject; used here only
        as a cross-check, per this folder's convention). Detects a cycle
        the moment it would close one, then confirms the edge count."""
        if len(edges) != n - 1:
            return False
        if n <= 1:
            return True

        parent = list(range(n))

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        for u, v in edges:
            ru, rv = find(u), find(v)
            if ru == rv:
                return False              # this edge closes a cycle
            parent[ru] = rv

        return True

    # ------------------------------------------------------------------
    # ✗ DELIBERATELY INCOMPLETE — for the counterexample demo only.
    # ------------------------------------------------------------------
    def _edge_count_only(self, n: int, edges: List[List[int]]) -> bool:
        """✗ BROKEN ON PURPOSE — checks only `len(edges) == n - 1`,
        never verifies connectivity. Wrong on Counterexample A."""
        return len(edges) == n - 1

    def _connectivity_only(self, n: int, edges: List[List[int]]) -> bool:
        """✗ BROKEN ON PURPOSE — checks only that the graph is one
        connected component, never verifies the edge count. Wrong on
        Counterexample B."""
        if n <= 1:
            return True
        graph = {i: [] for i in range(n)}
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)
        visited = {0}
        queue = deque([0])
        while queue:
            node = queue.popleft()
            for nxt in graph[node]:
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append(nxt)
        return len(visited) == n


# ==============================================================================
# TESTS — run:  python 010_graph_valid_tree_solution.py
# ==============================================================================
CASES = [
    (5, [[0, 1], [0, 2], [0, 3], [1, 4]], True),
    (5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]], False),
    (5, [[0, 1], [2, 3], [3, 4], [2, 4]], False),
    (1, [], True),
    (2, [], False),
    (2, [[0, 1]], True),
    (4, [[0, 1], [2, 3]], False),
    (6, [[0, 1], [1, 2], [2, 3], [3, 4], [4, 5]], True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: edge-count + connectivity ---")
    for n, edges, want in CASES:
        got = sol.validTree(n, [r[:] for r in edges])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n} edges={edges!r:<40} "
              f"-> {got} (want {want})")

    print("\n--- both implementations agree ---")
    for n, edges, want in CASES:
        a = sol.validTree(n, [r[:] for r in edges])
        b = sol.validTree_unionfind(n, [r[:] for r in edges])
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<3} bfs+count={a} union-find={b}")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: two counterexamples proving BOTH checks are required.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: why neither check alone suffices ---")

    # Counterexample A: exactly n-1 edges, but disconnected.
    n_a, edges_a = 5, [[0, 1], [2, 3], [3, 4], [2, 4]]
    real_a = sol.validTree(n_a, edges_a)
    count_only_a = sol._edge_count_only(n_a, edges_a)
    conn_only_a = sol._connectivity_only(n_a, edges_a)
    print(f"\n  Counterexample A: n={n_a}, edges={edges_a}")
    print(f"    len(edges)={len(edges_a)}, n-1={n_a - 1} "
          f"-> edge count MATCHES a tree's")
    print(f"    real components: {{0,1}} and {{2,3,4}} -> disconnected")
    print(f"    real validTree()              -> {real_a}  (correct: False)")
    print(f"    edge-count-ONLY checker        -> {count_only_a}  "
          f"(WRONG — says tree, but node 0 can't reach node 2)")
    print(f"    connectivity-ONLY checker      -> {conn_only_a}  "
          f"(correctly says not-a-tree here, but for the wrong reason "
          f"— it never even looked at the edge count)")
    a_proves_point = (real_a is False and count_only_a is True)
    print(f"    edge-count-only checker gave a FALSE POSITIVE: {a_proves_point}")

    # Counterexample B: fully connected, but n edges (one cycle too many).
    n_b, edges_b = 5, [[0, 1], [1, 2], [2, 3], [1, 3], [1, 4]]
    real_b = sol.validTree(n_b, edges_b)
    count_only_b = sol._edge_count_only(n_b, edges_b)
    conn_only_b = sol._connectivity_only(n_b, edges_b)
    print(f"\n  Counterexample B: n={n_b}, edges={edges_b}")
    print(f"    every node reachable from every other -> fully CONNECTED")
    print(f"    len(edges)={len(edges_b)}, n-1={n_b - 1} "
          f"-> one edge too many (cycle among 1,2,3)")
    print(f"    real validTree()              -> {real_b}  (correct: False)")
    print(f"    connectivity-ONLY checker      -> {conn_only_b}  "
          f"(WRONG — says tree, but 1-2-3-1 is a cycle)")
    print(f"    edge-count-ONLY checker        -> {count_only_b}  "
          f"(correctly says not-a-tree here, but for the wrong reason "
          f"— it never traversed the graph)")
    b_proves_point = (real_b is False and conn_only_b is True)
    print(f"    connectivity-only checker gave a FALSE POSITIVE: {b_proves_point}")

    print(f"\n  Each incomplete checker is fooled by exactly the counterexample")
    print(f"  built to defeat it, and the real validTree() (both checks) gets")
    print(f"  BOTH graphs right: {real_a is False and real_b is False}.")
    all_ok &= a_proves_point and b_proves_point and real_a is False and real_b is False

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
