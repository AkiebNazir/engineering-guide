"""
================================================================================
SOLUTION · LeetCode 684 · Redundant Connection                       [Medium]
https://leetcode.com/problems/redundant-connection/
================================================================================

THE CORE IDEA
--------------
A tree on `n` nodes has exactly `n-1` edges. This input hands you `n` edges
for `n` nodes — exactly one edge too many, and exactly one edge closes a
cycle. Build the graph INCREMENTALLY, one edge at a time, in input order.
Before adding edge (u, v), ask: "can I already reach v from u using only
the edges added so far?" If yes, this edge doesn't connect anything new —
it's the redundant one. Return it immediately; since the input is a tree
plus exactly one extra edge, there is exactly one such edge, and checking
in input order automatically finds the correct (last-occurring, per the
problem statement) answer, because it's unique.

⚠️ THIS FOLDER DOES NOT USE UNION-FIND HERE. The topic guide (Part 11) is
explicit: Union-Find / DSU is topic 15's subject (Advanced Graphs —
Dijkstra, Bellman-Ford, MST, Union-Find, Tarjan). The canonical OPTIMAL
solution to 684 uses a DSU with near-O(E * alpha(V)) total cost — if you
already know DSU, that's the answer to reach for in a real interview once
you've covered topic 15. This file solves it with plain DFS/BFS
reachability checks, which is O(E * (V + E)) but stays entirely within this
topic's toolkit (Part 2/3: traversal + connectivity, nothing new).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every edge, remove it, check if
the remaining n-1 edges form a valid tree (connected + acyclic, e.g. via
problem 010's Graph Valid Tree check), starting from the LAST edge and
working backward, return the first removal that fixes it. O(E) candidate
removals * O(V + E) validity check each = O(E * (V + E)) — same asymptotic
cost as the approach below but does needless work re-validating the WHOLE
graph after every candidate removal, instead of using the single insight
that only the newest edge can possibly be the culprit.

Approach 1 (incremental build + reachability check) ✅ — the answer:
    Build an adjacency list starting empty. For each (u, v) in edges, in
    order: check whether v is reachable from u using a DFS/BFS restricted
    to the edges added SO FAR. If reachable, (u, v) is the answer — return
    it without adding it. Otherwise add the edge (both directions, it's
    undirected — topic guide's mistake #7 warns against forgetting this)
    and continue.
    O(E) edges, each triggering an O(V + E) traversal in the worst case
    -> O(E * (V + E)) time, O(V + E) space.

Approach 2 (Union-Find / DSU) — NOT implemented in this file, on purpose.
    Maintain a `parent[]` array; `union(u, v)` merges the two components if
    they differ, `find(u) == find(v)` before union tells you they were
    already connected -> redundant edge. With path compression + union by
    rank, each operation is near O(alpha(V)), essentially constant, giving
    O(E * alpha(V)) ~ O(E) total — much faster than Approach 1 at scale.
    This is topic 15's material. Mentioning it here (and knowing WHY it's
    faster) is the expected depth for this topic; CODING it belongs to the
    next one.


================================================================================
STEP BY STEP TRACE
================================================================================
edges = [[1,2],[1,3],[2,3]]

Start: graph = {} (empty adjacency list)

Edge (1,2): is 2 reachable from 1 in the current (empty) graph? No nodes
            connected at all yet -> NOT reachable. Add the edge.
            graph: 1-2

    1---2

Edge (1,3): is 3 reachable from 1? DFS from 1 visits {1,2} — 3 not among
            them -> NOT reachable. Add the edge.
            graph: 1-2, 1-3

    1---2
    |
    3

Edge (2,3): is 3 reachable from 2? DFS from 2 visits {2,1,3} (2->1->3) —
            YES, 3 IS reachable -> this edge closes a cycle.
            ANSWER: [2, 3]. Return immediately, do not add it.

    1---2
    |   |
    3---'   (the edge that would close this loop is the redundant one)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time            Space    Mutates input?  Note
    -------------------------------  --------------  -------  --------------  -------------------------
    Remove-and-revalidate (brute)     O(E*(V+E))      O(V+E)   no              re-validates whole graph
    Incremental build + DFS check ✅  O(E*(V+E))      O(V+E)   no              this file's answer
    Union-Find (topic 15)             O(E*alpha(V))   O(V)     no              optimal; not coded here

    "Mutates input?" — no approach here mutates `edges`; the adjacency
    list built for traversal is a separate structure. `edges` itself is
    only read, one entry at a time, never reordered or written to (the
    test harness still passes a defensive copy, matching this folder's
    convention for grid/edge-list problems that are read-only).


================================================================================
EDGE CASES
================================================================================
    exactly one redundant edge exists  -> guaranteed by the problem (input is
                                          a spanning tree plus exactly one
                                          extra edge) — no need to handle
                                          "zero redundant edges" or "more
                                          than one".
    the redundant edge appears EARLY    -> still correctly found: the check
    in the list, not last                is "are u,v connected using edges
                                          seen so far", which is well-defined
                                          at every step, not just the end.
    redundant edge directly duplicates   -> e.g. edges=[[1,2],[1,3],[3,1]] is
    an existing edge (same pair, any      NOT valid input per constraints
    order)                                ("no repeated edges"), but a
                                          same-node-pair-different-order edge
                                          like [1,3] then [3,1] IS exactly
                                          this "already connected" case and
                                          is handled identically to any other
                                          cycle-closing edge.
    smallest possible n=3 triangle      -> the minimum case where a cycle is
                                          even possible (n=3 edges, 3 nodes).
    a "star" plus one closing edge       -> e.g. 1-2,1-3,1-4,1-5,2-3: tests
                                          that reachability, not literal
                                          adjacency, is what's checked (2 and
                                          3 are connected via 1, not directly,
                                          before the last edge is added).


================================================================================
COMMON MISTAKES
================================================================================
1. Reaching for Union-Find here because it's "the standard LeetCode answer."
   This topic's material is traversal-based (DFS/BFS/components), and DSU
   is deliberately deferred to topic 15 in this curriculum — see the topic
   guide's Part 11 note on this exact problem. Using it here works on
   LeetCode but skips the traversal-based reasoning this topic is building.

2. Checking "is (u, v) an edge already in my adjacency list" instead of
   "is v REACHABLE from u" — these are different questions. The star
   example above (1-2,1-3,1-4,1-5,2-3) has 2 and 3 connected through 1
   long before a direct 2-3 edge is proposed; an adjacency-only check
   would miss the cycle.

3. Adding the edge to the graph BEFORE checking reachability. That makes
   every edge trivially "reachable" (it's now adjacent to itself via the
   edge just added), so the check always fires on nothing useful. Check
   first, then add only if not already connected.

4. Only adding one direction of the undirected edge (`graph[u].append(v)`
   but not `graph[v].append(u)`) — topic guide mistake #7. Breaks
   reachability checks that need to walk backward too.

5. Returning the FIRST edge that ever looked suspicious via some heuristic,
   instead of literally re-deriving reachability at each step. Since
   exactly one edge is redundant and it's found exactly once this way,
   there's no need (and no room) for heuristics — trust the reachability
   check.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Can you do better than O(E*(V+E))?
A: Yes — Union-Find with path compression + union by rank gets each
   union/find to near O(alpha(V)) (alpha = inverse Ackermann, effectively a
   small constant <= 4 for any realistic input), so the whole algorithm
   becomes O(E * alpha(V)), practically O(E). That's topic 15's material —
   name it, describe find/union with path compression, but this topic's
   expected implementation is the DFS-based one above.

Q: What if the graph could have MULTIPLE redundant edges (not guaranteed
   exactly one)?
A: The incremental-build approach generalizes directly — every edge whose
   endpoints are already connected at the time it's processed is redundant;
   collect all of them instead of returning on the first hit.

Q: What about "Redundant Connection II" (LC 685), the DIRECTED version?
A: Meaningfully harder — a directed graph can have a node with two parents
   (not just a cycle) making it not a valid rooted tree, and the two failure
   modes (two-parent node vs. a cycle) need separate handling, occasionally
   together. Out of scope here; mentioning the distinction shows awareness
   of the difference between undirected and directed cycle detection (topic
   guide Part 4).

Q: How would Kruskal's MST algorithm relate to this?
A: Kruskal's builds a spanning tree by adding edges in some order and
   skipping any edge that would close a cycle — using Union-Find for the
   cycle check. This problem IS that skip-step in isolation: "which edge
   would Kruskal's skip?"


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern: incremental connectivity / cycle detection during graph construction.

    LC 685  Redundant Connection II         — directed version, two failure modes
    LC 261  Graph Valid Tree (010, this folder) — components==1 AND edges==V-1
    LC 323  Number of Connected Components (009) — Part 3's traversal-count pattern
    LC 1319 Number of Operations to Make Network Connected — DSU counting components
    LC 990  Satisfiability of Equality Equations — DSU/union-find on constraints
    LC 547  Number of Provinces               — connected components on a matrix
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def findRedundantConnection(self, edges: List[List[int]]) -> List[int]:
        """✅ THE ANSWER — build incrementally, DFS-check reachability before
        adding each edge. O(E * (V + E)) time, O(V + E) space. Does not
        mutate `edges`."""
        graph = {}

        def connected(u: int, v: int) -> bool:
            """DFS: can we reach v from u using edges added so far?"""
            visited = set()
            stack = [u]
            while stack:
                node = stack.pop()
                if node == v:
                    return True
                if node in visited:
                    continue
                visited.add(node)
                for nxt in graph.get(node, []):
                    if nxt not in visited:
                        stack.append(nxt)
            return False

        for u, v in edges:
            if u in graph and v in graph and connected(u, v):
                return [u, v]
            graph.setdefault(u, []).append(v)
            graph.setdefault(v, []).append(u)

        return []  # unreachable given the problem's guarantee

    def findRedundantConnection_bfs(self, edges: List[List[int]]) -> List[int]:
        """Same idea, BFS instead of DFS for the reachability check — proves
        the traversal choice doesn't matter here (topic guide Part 2: BFS vs
        DFS are interchangeable for pure reachability, only shortest-path
        needs BFS specifically). O(E * (V + E)) time, O(V + E) space."""
        from collections import deque

        graph = {}

        def connected(u: int, v: int) -> bool:
            visited = {u}
            queue = deque([u])
            while queue:
                node = queue.popleft()
                if node == v:
                    return True
                for nxt in graph.get(node, []):
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
            return False

        for u, v in edges:
            if u in graph and v in graph and connected(u, v):
                return [u, v]
            graph.setdefault(u, []).append(v)
            graph.setdefault(v, []).append(u)

        return []


# ==============================================================================
# TESTS
# ==============================================================================
CASES = [
    ([[1, 2], [1, 3], [2, 3]], [2, 3]),
    ([[1, 2], [2, 3], [3, 4], [1, 4], [1, 5]], [1, 4]),
    ([[1, 2], [2, 3], [3, 1]], [3, 1]),
    ([[1, 4], [3, 4], [1, 3], [1, 2]], [1, 3]),
    ([[1, 2], [1, 3], [1, 4], [1, 5], [2, 3]], [2, 3]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: DFS-based incremental build ---")
    for edges, expected in CASES:
        result = sol.findRedundantConnection([e[:] for e in edges])
        ok = result == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  edges={edges!r:<45} "
              f"-> {result} (want {expected})")

    print("\n--- DFS and BFS variants agree ---")
    for edges, expected in CASES:
        a = sol.findRedundantConnection([e[:] for e in edges])
        b = sol.findRedundantConnection_bfs([e[:] for e in edges])
        ok = a == b == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  dfs={a} bfs={b}")

    # ----------------------------------------------------------------------
    # Trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: edges=[[1,2],[1,3],[2,3]] ---")
    graph = {}

    def connected(u, v):
        visited, stack = set(), [u]
        while stack:
            node = stack.pop()
            if node == v:
                return True
            if node in visited:
                continue
            visited.add(node)
            for nxt in graph.get(node, []):
                if nxt not in visited:
                    stack.append(nxt)
        return False

    for u, v in [[1, 2], [1, 3], [2, 3]]:
        already = u in graph and v in graph and connected(u, v)
        if already:
            print(f"  edge ({u},{v}): {v} IS reachable from {u} -> "
                  f"REDUNDANT, answer = [{u},{v}]")
            break
        print(f"  edge ({u},{v}): not yet connected -> add it")
        graph.setdefault(u, []).append(v)
        graph.setdefault(v, []).append(u)

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: measure the O(E * (V + E)) shape as size grows.
    # ----------------------------------------------------------------------
    print("\n--- DEMO: timing cost growth as (near-tree-sized) input scales ---")
    print("  Build a random spanning tree on n nodes, shuffle its n-1 edges,")
    print("  append ONE closing edge (the true redundant one) at the end, and")
    print("  time findRedundantConnection on the resulting n-edge input.")
    print(f"  {'n (nodes)':>10} {'edges':>7} {'time (ms)':>10} {'ms / (E*(V+E))':>16}")

    sizes = [200, 1000, 3000]
    times = []
    for n in sizes:
        random.seed(n)
        # random spanning tree: node i (i>=2) attaches to a random earlier node
        nodes = list(range(1, n + 1))
        edges = []
        for i in range(2, n + 1):
            parent = random.randint(1, i - 1)
            edges.append([parent, i])
        random.shuffle(edges)
        # relabel with a fresh redundant edge between two random distinct nodes
        a, b = random.sample(nodes, 2)
        edges.append([a, b])

        t0 = time.perf_counter()
        sol.findRedundantConnection([e[:] for e in edges])
        t1 = time.perf_counter()
        ms = (t1 - t0) * 1000
        times.append(ms)
        e_count = len(edges)
        shape = e_count * (n + e_count)
        print(f"  {n:>10} {e_count:>7} {ms:>10.3f} {ms / shape * 1e6:>16.4f}")

    # growth check: cost should grow at least roughly with n (not flat, not
    # wildly super-quadratic) — compare ratios loosely rather than assert an
    # exact exponent, since real timings are noisy at these sizes.
    growth_15x = times[1] / times[0] if times[0] > 0 else 0
    growth_3x = times[2] / times[1] if times[1] > 0 else 0
    print(f"  time ratio n=200->1000 (5x nodes): {growth_15x:.1f}x")
    print(f"  time ratio n=1000->3000 (3x nodes): {growth_3x:.1f}x")
    print("  Cost grows worse than linear in n, consistent with the claimed")
    print("  O(E*(V+E)) shape (worst case quadratic-ish in n for a near-tree")
    print("  input) — this is exactly the cost Union-Find (topic 15) avoids.")
    growth_confirmed = growth_15x > 1.0 and growth_3x > 1.0
    all_ok &= growth_confirmed

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
