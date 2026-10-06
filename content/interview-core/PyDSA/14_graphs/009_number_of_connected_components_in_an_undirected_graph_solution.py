"""
================================================================================
SOLUTION · LeetCode 323 · Number of Connected Components in an Undirected
                            Graph                                    [Medium]
https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/
================================================================================

THE CORE IDEA
--------------
Build an adjacency list from the edge list (topic guide Part 1, O(E), pay
once). Then scan `node in range(n)`; every time you find a node that has
never been visited, that is proof it belongs to a component no earlier
traversal reached — increment the counter and flood-fill everything
reachable from it. The number of times you were FORCED to start a new
traversal IS the number of connected components (topic guide Part 3).

    components = 0
    visited = set()
    for node in range(n):
        if node not in visited:
            components += 1
            <walk everything reachable from node, marking visited>
    return components

Nothing more subtle than that — the whole problem is "count how many times
you had to restart."


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every pair of nodes (i, j), run a
fresh BFS/DFS to test reachability, then union pairs that are mutually
reachable into groups. That's O(V^2 * (V+E)) and duplicates work the single
full-graph traversal already gives you for free. Never coded below — it's
worth stating out loud in an interview and then discarding.

Approach 1 (iterative DFS, explicit stack) ✅ — the answer used as the
primary implementation. O(V + E) time, O(V + E) space, and — critically — no
recursion depth risk. n can be up to 2000, and an adversarial edge list can
chain every node into one path, so an iterative stack is the safe default.

Approach 2 (BFS, `collections.deque`) — identical complexity and identical
correctness, marks `visited` at enqueue time per the topic guide's BFS rule
(Part 2). Interchangeable with Approach 1; pick BFS if the interviewer later
adds a "shortest path within a component" follow-up, since BFS is already
the right tool for that.

Approach 3 (recursive DFS) — the textbook-shortest code, and DANGEROUS here:
Python's default recursion limit is ~1000 frames, and a graph whose edges
form one long chain (0-1, 1-2, ..., (n-2)-(n-1)) makes the recursion go n
frames deep. At this problem's own n=2000 ceiling, recursive DFS raises
`RecursionError` on legal input. Demoed live below — this is not a
contrived edge case, it's inside the stated constraints.

Approach 4 (Union-Find / Disjoint Set Union) — union every edge's two
endpoints, then count distinct roots. This is the textbook-optimal way to
solve 323 in general (near O(E * alpha(V)), effectively linear, and it
needs no adjacency list or traversal stack at all), but Union-Find as a
data structure belongs to topic 15 (Advanced Graphs) per this repo's
curriculum split — the topic guide's note on problem 013 makes the same
call. It's implemented below as `countComponents_unionfind` purely so you
can see it agrees with the DFS/BFS answer on every test case; treat it as a
preview, not the "primary" technique to reach for while still inside topic
14.


================================================================================
STEP BY STEP TRACE
================================================================================
n = 5, edges = [[0,1],[1,2],[3,4]]

Build adjacency list:
    0: [1]
    1: [0, 2]
    2: [1]
    3: [4]
    4: [3]

Scan node 0..4, visited = {}

    node=0: not visited -> components=1, DFS from 0
        stack=[0] -> pop 0, visited={0}, push neighbors [1]
        stack=[1] -> pop 1, visited={0,1}, push neighbors [0(skip via visited later),2]
        stack=[2,0] -> pop 0 -> already visited, skip
        stack=[2]   -> pop 2, visited={0,1,2}, neighbors [1] already visited
        stack empty -> component #1 = {0,1,2}

    node=1: visited -> skip
    node=2: visited -> skip

    node=3: not visited -> components=2, DFS from 3
        stack=[3] -> pop 3, visited={0,1,2,3}, push [4]
        stack=[4] -> pop 4, visited={0,1,2,3,4}, neighbors [3] already visited
        stack empty -> component #2 = {3,4}

    node=4: visited -> skip

Loop ends. components = 2.  Matches the two disjoint pieces drawn in the
question file: {0,1,2} and {3,4}.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time          Space      Mutates input?  Note
    --------------------------  ------------  ---------  --------------  ----------------------------
    Brute force (all-pairs)      O(V^2*(V+E))  O(V^2)     no              never coded, too slow
    Iterative DFS ✅              O(V + E)      O(V + E)   no              answer; no recursion risk
    BFS (deque)                  O(V + E)      O(V + E)   no              same complexity, safer for
                                                                          "shortest path" follow-ups
    Recursive DFS                O(V + E)      O(V + E)   no              RecursionError on chain
                                                                          shaped input at n~1000+
    Union-Find (topic 15 preview) ~O(E*alpha(V)) O(V)      no              fastest in practice, no
                                                                          adjacency list needed

    None of these mutate the input `edges` list or the caller's data —
    everything reachable/visited lives in a fresh adjacency dict and a
    fresh `visited` set built inside the function.


================================================================================
EDGE CASES
================================================================================
    n = 1, edges = []          -> exactly 1 component (a single isolated
                                   node is still a component of size 1).
    edges = [] (n > 1)          -> every node is its own component, answer
                                   is n. Tests that the "not visited" scan
                                   correctly counts nodes with NO edges at
                                   all, not just edges that fail to connect.
    all nodes already connected -> answer is 1; the scan visits node 0,
                                   reaches everything in one traversal, and
                                   every subsequent iteration of the outer
                                   loop finds `node in visited`.
    a cycle inside a component  -> must not be double-counted. The `visited`
                                   check on every neighbor before pushing/
                                   recursing prevents walking the same node
                                   twice within one component's traversal.
    duplicate detection of an   -> constraints guarantee no repeated edges,
    edge                          but the algorithm would be correct even
                                   if one slipped through: `visited` absorbs
                                   the redundancy silently.
    chain-shaped graph, n large -> the adversarial case for recursion depth;
                                   see DEMO below. Iterative DFS/BFS handle
                                   it identically to any other shape; only
                                   the recursive variant is at risk.


================================================================================
COMMON MISTAKES
================================================================================
1. Building the adjacency list with only ONE direction
   (`graph[u].append(v)` but not `graph[v].append(u)`). `edges` is
   UNDIRECTED — forgetting the reverse direction silently turns the graph
   directed and can inflate the component count, because a node might now
   be unreachable from its true component's other members even though the
   original edge connects them both ways.

2. Resetting `visited` inside the outer loop instead of keeping ONE set
   across the whole scan. If you reset it per node, every node "rediscovers"
   its own component from scratch and the count is wildly wrong (usually
   equal to n).

3. Counting a component every time you touch a node that already has
   neighbors, instead of only when the OUTER scan finds an unvisited node.
   The increment belongs exactly once per fresh traversal start, not once
   per edge or per neighbor.

4. Choosing recursive DFS without checking the recursion-depth budget
   against the stated constraints. n <= 2000 is enough to blow the default
   ~1000-frame limit on a chain-shaped adjacency list — this is demoed
   live below, not a theoretical worry.

5. Forgetting that an isolated node (no edges at all) is still its own
   component. If your algorithm only ever visits nodes that appear in
   `edges`, isolated nodes get silently skipped and the count comes back
   too low.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the graph were DIRECTED instead?
A: "Connected components" as stated only makes sense for undirected graphs.
   The directed analogue is STRONGLY connected components (Tarjan's or
   Kosaraju's algorithm) — every node in a strongly connected component
   must be mutually reachable both ways. That's a materially harder
   algorithm, out of scope for this topic (topic 15 territory).

Q: Can you do it without building an adjacency list, e.g. straight from the
   edge list with Union-Find?
A: Yes — Approach 4 above. Union the two endpoints of every edge; the final
   answer is the number of distinct roots (`find(i)` values) across
   `range(n)`. Near-linear with path compression + union by rank/size, and
   it needs no explicit graph structure. This is the standard "optimal"
   answer to 323 in most interview rubrics; DFS/BFS is the "safe, obviously
   correct" answer this topic's toolkit produces.

Q: What's the size of the LARGEST component, not just the count?
A: Track the size of each traversal (count nodes visited during that
   particular DFS/BFS) and keep a running max — identical shape to Max Area
   of Island (003), just off a grid instead of an edge list.

Q: Could you answer "are nodes u and v in the same component?" for MANY
   (u, v) queries efficiently?
A: Precompute a `component_id` array in one O(V+E) pass (label every node
   with which traversal found it), then each query is O(1):
   `component_id[u] == component_id[v]`. Or, if edges arrive incrementally
   over time (streaming), Union-Find with path compression answers each
   query in ~O(alpha(V)) without ever rebuilding from scratch — the
   scenario Union-Find is built for.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Pattern 3 (connected components) from the topic guide's decision table.

    LC 200  Number of Islands                — identical pattern, on a grid (002)
    LC 261  Graph Valid Tree                  — components==1 AND edges==V-1 (010, next)
    LC 547  Number of Provinces               — components, given as an adjacency MATRIX
    LC 1319 Number of Operations to Make      — components again: need components-1
            Network Connected                  extra cables to connect everything
    LC 684  Redundant Connection              — Union-Find teaser (013 in this folder)
================================================================================
"""

import sys
import time
from collections import deque
from typing import List


class Solution:
    def countComponents(self, n: int, edges: List[List[int]]) -> int:
        """✅ THE ANSWER — iterative DFS, explicit stack.
        O(V + E) time, O(V + E) space. No recursion depth risk."""
        graph = {i: [] for i in range(n)}
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)

        visited = set()
        components = 0
        for start in range(n):
            if start in visited:
                continue
            components += 1
            stack = [start]
            while stack:
                node = stack.pop()
                if node in visited:
                    continue
                visited.add(node)
                for nxt in graph[node]:
                    if nxt not in visited:
                        stack.append(nxt)
        return components

    def countComponents_bfs(self, n: int, edges: List[List[int]]) -> int:
        """Same idea, BFS with a deque. Marks visited at ENQUEUE time
        (topic guide Part 2's rule). O(V + E) time/space."""
        graph = {i: [] for i in range(n)}
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)

        visited = set()
        components = 0
        for start in range(n):
            if start in visited:
                continue
            components += 1
            visited.add(start)
            queue = deque([start])
            while queue:
                node = queue.popleft()
                for nxt in graph[node]:
                    if nxt not in visited:
                        visited.add(nxt)
                        queue.append(nxt)
        return components

    def countComponents_recursive(self, n: int, edges: List[List[int]]) -> int:
        """The textbook-shortest version — recursive DFS. RISKY: a
        chain-shaped adjacency list recurses n frames deep and can raise
        RecursionError well inside this problem's own n <= 2000 constraint.
        Demoed live in run_tests()."""
        graph = {i: [] for i in range(n)}
        for u, v in edges:
            graph[u].append(v)
            graph[v].append(u)

        visited = set()

        def dfs(node):
            visited.add(node)
            for nxt in graph[node]:
                if nxt not in visited:
                    dfs(nxt)

        components = 0
        for start in range(n):
            if start not in visited:
                components += 1
                dfs(start)
        return components

    def countComponents_unionfind(self, n: int, edges: List[List[int]]) -> int:
        """Union-Find / DSU preview (topic 15's actual subject — used here
        only for a cross-check, not as the topic-14 "reach for this"
        technique). Path compression + union by size.
        ~O(E * alpha(V)) time, O(V) space, needs no adjacency list."""
        parent = list(range(n))
        size = [1] * n

        def find(x):
            while parent[x] != x:
                parent[x] = parent[parent[x]]   # path compression
                x = parent[x]
            return x

        def union(a, b):
            ra, rb = find(a), find(b)
            if ra == rb:
                return
            if size[ra] < size[rb]:
                ra, rb = rb, ra
            parent[rb] = ra
            size[ra] += size[rb]

        for u, v in edges:
            union(u, v)

        return len({find(i) for i in range(n)})


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def build_chain_edges(n):
    """n nodes wired into ONE long path: 0-1, 1-2, ..., (n-2)-(n-1).
    Worst case for recursion depth: a DFS from node 0 must recurse n
    frames deep before it can unwind."""
    return [[i, i + 1] for i in range(n - 1)]


# ==============================================================================
# TESTS — run:  python 009_number_of_connected_components_in_an_undirected_graph_solution.py
# ==============================================================================
CASES = [
    (5, [[0, 1], [1, 2], [3, 4]], 2),
    (5, [[0, 1], [1, 2], [2, 3], [3, 4]], 1),
    (4, [], 4),
    (1, [], 1),
    (2, [[0, 1]], 1),
    (6, [[0, 1], [2, 3], [4, 5]], 3),
    (6, [[0, 1], [1, 2], [2, 0], [3, 4]], 3),
    (10, [[0, 1], [1, 2], [2, 3], [4, 5], [6, 7], [7, 8], [8, 9]], 3),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: iterative DFS ---")
    for n, edges, want in CASES:
        got = sol.countComponents(n, [row[:] for row in edges])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n} edges={edges!r:<40} "
              f"-> {got} (want {want})")

    print("\n--- all four implementations agree ---")
    for n, edges, want in CASES:
        a = sol.countComponents(n, [r[:] for r in edges])
        b = sol.countComponents_bfs(n, [r[:] for r in edges])
        c = sol.countComponents_recursive(n, [r[:] for r in edges])
        d = sol.countComponents_unionfind(n, [r[:] for r in edges])
        ok = a == b == c == d == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n:<3} iterative={a} bfs={b} "
              f"recursive={c} union-find={d}")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: recursive DFS vs a chain-shaped graph inside n <= 2000.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: recursive DFS on a CHAIN-shaped graph ---")
    limit = sys.getrecursionlimit()
    print(f"  sys.getrecursionlimit() = {limit}")
    for n in (500, 1500, 2000):
        chain = build_chain_edges(n)
        t0 = time.perf_counter()
        iter_result = sol.countComponents(n, chain)
        t1 = time.perf_counter()
        print(f"  n={n:<5} iterative DFS -> {iter_result} component(s) "
              f"in {(t1 - t0) * 1000:.2f} ms")

        t2 = time.perf_counter()
        try:
            rec_result = sol.countComponents_recursive(n, chain)
            t3 = time.perf_counter()
            print(f"  n={n:<5} recursive DFS -> {rec_result} component(s) "
                  f"in {(t3 - t2) * 1000:.2f} ms  (did NOT raise)")
        except RecursionError as e:
            print(f"  n={n:<5} recursive DFS -> RecursionError: {e!r}")

    print("\n  Confirming the boundary: iterative succeeds at n=2000 (this")
    print("  problem's own ceiling), recursive DFS fails on that exact same")
    print("  legal input the moment the chain length crosses the recursion")
    print("  limit. Same algorithm, same graph — only the call mechanism differs.")
    n_big = 2000
    chain = build_chain_edges(n_big)
    iter_ok = sol.countComponents(n_big, chain) == 1
    recursion_failed = False
    try:
        sol.countComponents_recursive(n_big, chain)
    except RecursionError:
        recursion_failed = True
    print(f"  n={n_big}: iterative correct -> {iter_ok}; "
          f"recursive raised RecursionError -> {recursion_failed}")
    all_ok &= iter_ok and recursion_failed

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
