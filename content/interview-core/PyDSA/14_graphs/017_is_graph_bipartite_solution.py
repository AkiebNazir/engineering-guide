"""
================================================================================
SOLUTION · LeetCode 785 · Is Graph Bipartite?                           [Medium]
https://leetcode.com/problems/is-graph-bipartite/
================================================================================

THE CORE IDEA
--------------
Two-coloring by BFS. In each connected component, the first node's color is
free; every other color is FORCED (neighbors get the opposite color). The
graph is bipartite exactly when the forced coloring never puts the same color
on both ends of an edge, which is exactly when there is no odd cycle. Run it
from every uncolored node, because the graph may be disconnected.


================================================================================
APPROACH 1 · Try every 2-coloring (priced, used as oracle)
================================================================================
Enumerate all 2^n colorings and check every edge.

    Time: O(2^n * E)    Space: O(n)


================================================================================
APPROACH 2 · BFS two-coloring ✅ (the answer)
================================================================================
    color = [-1] * n
    for s in range(n):
        if color[s] != -1:
            continue
        color[s] = 0
        queue = deque([s])
        while queue:
            u = queue.popleft()
            for v in graph[u]:
                if color[v] == -1:
                    color[v] = 1 - color[u]
                    queue.append(v)
                elif color[v] == color[u]:
                    return False
    return True

WHY BFS NEVER NEEDS TO BACKTRACK. After the start node, every color is a
consequence, not a choice. If a conflict appears, EVERY coloring of this
component conflicts (flip the start color and all colors flip with it, so the
same edge still conflicts). So returning False immediately is correct.

WHY CONFLICT == ODD CYCLE. With BFS, color[v] = depth[v] mod 2. An edge between
two nodes of equal depth parity, plus their two BFS-tree paths up to the common
ancestor, forms a cycle of odd length.

    Time: O(V + E)    Space: O(V)


================================================================================
APPROACH 3 · Union-Find
================================================================================
In a bipartite graph, all neighbors of u are on the SAME side (opposite to u).
So for each u: union all of graph[u] together, and if find(u) == find(v) for
any neighbor v, u and its neighbor were forced to the same side -> False.

    Time: O((V + E) * α(V))    Space: O(V)

Useful when edges arrive one at a time. Use the parity (weighted) union-find
variant if you need to answer "still bipartite?" after each added edge.


================================================================================
STEP BY STEP TRACE · Example 1, graph = [[1,2,3],[0,2],[0,1,3],[0,2]]
================================================================================
    start s=0: color[0]=0, queue [0]
    pop 0: v=1 uncolored -> color 1     queue [1]
           v=2 uncolored -> color 1     queue [1, 2]
           v=3 uncolored -> color 1     queue [1, 2, 3]
    pop 1: v=0 color 0 != 1 ok
           v=2 color 1 == color[1] = 1  -> CONFLICT -> return False

    The conflicting edge 1-2 plus the tree edges 0-1 and 0-2 is the triangle.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time             Space   Mutates input?
    ------------------------  ---------------  ------  --------------
    All 2-colorings           O(2^n * E)       O(n)    No
    BFS two-coloring ✅       O(V + E)         O(V)    No
    DFS two-coloring          O(V + E)         O(V)    No (recursion depth O(V))
    Union-Find                O((V+E) α(V))    O(V)    No


================================================================================
EDGE CASES
================================================================================
    Single node, no edges     True.
    Isolated nodes            Each is its own trivially bipartite component.
    Disconnected, odd cycle   Only found if you start BFS in that component.
    Even cycle                True. Odd cycle: False.
    Tree / forest             Always bipartite (no cycles at all).


================================================================================
COMMON MISTAKES
================================================================================
1. Starting BFS only from node 0. A triangle in another component goes
   unchecked. Demo below.

2. Marking colors on DEQUEUE instead of ENQUEUE: a node can be enqueued twice
   with different colors before either is processed.

3. Treating "visited" and "color" separately and forgetting to compare colors
   for already-visited neighbors.

4. Thinking self-loops or parallel edges need handling. The constraints rule
   them out (a self-loop would make the graph non-bipartite).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the two sets?
A: Partition by color after a successful run.

Q: Return an odd cycle as proof when it's NOT bipartite?
A: Keep BFS parents. On conflict edge (u, v), walk both up to their lowest
   common ancestor; the two paths plus (u, v) form the odd cycle.

Q: Possible Bipartition (LC 886) — people who dislike each other?
A: Same algorithm on the dislike graph.

Q: Edges arrive online; answer after each?
A: Union-find with parity bits: store each node's parity relative to its root.
   Adding (u, v) with equal parity inside the same set breaks bipartiteness.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 886   Possible Bipartition
    LC 1042  Flower Planting With No Adjacent — greedy 4-coloring
    LC 207   Course Schedule (011)             — directed cycle detection
    LC 990   Satisfiability of Equality Equations (15/002) — union-find constraints
================================================================================
"""

import random
from collections import deque
from itertools import product
from typing import List


class Solution:
    def isBipartite(self, graph: List[List[int]]) -> bool:
        n = len(graph)
        color = [-1] * n
        for s in range(n):
            if color[s] != -1:
                continue
            color[s] = 0
            queue = deque([s])
            while queue:
                u = queue.popleft()
                for v in graph[u]:
                    if color[v] == -1:
                        color[v] = 1 - color[u]
                        queue.append(v)
                    elif color[v] == color[u]:
                        return False
        return True


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def bipartite_union_find(graph: List[List[int]]) -> bool:
    parent = list(range(len(graph)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for u, nbrs in enumerate(graph):
        for v in nbrs:
            if find(u) == find(v):
                return False
            parent[find(v)] = find(nbrs[0])       # all neighbours on one side
    return True


def bipartite_brute(graph: List[List[int]]) -> bool:
    n = len(graph)
    for colors in product((0, 1), repeat=n):
        if all(colors[u] != colors[v] for u in range(n) for v in graph[u]):
            return True
    return False


def bipartite_from_zero_only_bug(graph: List[List[int]]) -> bool:
    """Mistake 1: one BFS from node 0 — ignores other components."""
    color = [-1] * len(graph)
    color[0] = 0
    queue = deque([0])
    while queue:
        u = queue.popleft()
        for v in graph[u]:
            if color[v] == -1:
                color[v] = 1 - color[u]
                queue.append(v)
            elif color[v] == color[u]:
                return False
    return True


def random_graph(rng: random.Random, n: int, p: float) -> List[List[int]]:
    g: List[List[int]] = [[] for _ in range(n)]
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < p:
                g[u].append(v)
                g[v].append(u)
    return g


# ==============================================================================
# TESTS — run:  python 017_is_graph_bipartite_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: BFS vs union-find ---")
    cases = [
        ([[1, 2, 3], [0, 2], [0, 1, 3], [0, 2]], False),
        ([[1, 3], [0, 2], [1, 3], [0, 2]], True),
        ([[]], True),
        ([[1], [0], [3, 4], [2, 4], [2, 3]], False),
        ([[], [2], [1]], True),
        ([[1], [0, 2], [1, 3], [2, 4], [3]], True),
        ([[1, 4], [0, 2], [1, 3], [2, 4], [3, 0]], False),
    ]
    for graph, want in cases:
        a, b = sol.isBipartite(graph), bipartite_union_find(graph)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  graph={graph}  bfs={a}  union-find={b}  want={want}")

    print("\n--- randomized cross-check vs trying all 2^n colorings (500 graphs) ---")
    rng = random.Random(785)
    bad = trues = 0
    for _ in range(500):
        g = random_graph(rng, rng.randint(1, 10), rng.choice((0.1, 0.2, 0.35)))
        want = bipartite_brute(g)
        trues += want
        if sol.isBipartite(g) != want or bipartite_union_find(g) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 random graphs ({trues} bipartite) match brute force")

    print("\n--- mistake 1 LIVE: BFS from node 0 only ---")
    g = [[1], [0], [3, 4], [2, 4], [2, 3]]     # edge 0-1, plus a triangle 2-3-4
    wrong, right = bipartite_from_zero_only_bug(g), sol.isBipartite(g)
    ok = wrong is True and right is False
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  0-1 edge + separate triangle 2-3-4: from-0-only says {wrong}, correct {right}")

    print("\n--- odd cycle <=> not bipartite (cycles of length 3..10) ---")
    for length in range(3, 11):
        cyc = [[(i - 1) % length, (i + 1) % length] for i in range(length)]
        got = sol.isBipartite(cyc)
        ok = got == (length % 2 == 0)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  cycle of length {length:>2}: bipartite={got}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
