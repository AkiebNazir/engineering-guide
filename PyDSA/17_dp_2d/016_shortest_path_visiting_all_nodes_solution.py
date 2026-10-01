"""
================================================================================
SOLUTION · LeetCode 847 · Shortest Path Visiting All Nodes                [Hard]
https://leetcode.com/problems/shortest-path-visiting-all-nodes/
================================================================================

THE CORE IDEA
--------------
Search over STATES, not nodes: state = (current node, bitmask of visited
nodes). Revisiting a node is fine; revisiting a STATE never helps. Every edge
costs 1, so multi-source BFS from (i, 1 << i) for every i finds the shortest
walk. The answer is the BFS level at which some state first has the full mask.


================================================================================
APPROACH 1 · Brute force over visiting orders (priced, used as oracle)
================================================================================
Compute all-pairs shortest distances with BFS from each node. Try every
permutation of the nodes and sum consecutive distances.

    Time: O(n! * n) — 12! is ~479 million.    Space: O(n^2)


================================================================================
APPROACH 2 · Multi-source BFS over (node, mask) ✅ (the answer)
================================================================================
    n = len(graph)
    if n == 1: return 0
    goal = (1 << n) - 1
    queue = deque((i, 1 << i) for i in range(n))
    seen = {(i, 1 << i) for i in range(n)}
    steps = 0
    while queue:
        steps += 1
        for _ in range(len(queue)):
            u, mask = queue.popleft()
            for v in graph[u]:
                nxt = mask | (1 << v)
                if nxt == goal:
                    return steps
                if (v, nxt) not in seen:
                    seen.add((v, nxt))
                    queue.append((v, nxt))

WHY THE STATE NEEDS THE MASK. BFS's guarantee ("first arrival is shortest")
holds per STATE. Arriving at node 0 with mask {0,1} and later with mask
{0,1,2} are different states: the second is strictly more progress. A visited
set of plain nodes would forbid that second arrival. Demo below.

    Time: O(2^n * n) states, each scanning up to n neighbors -> O(2^n * n^2)
    Space: O(2^n * n)

At n = 12 that's 49,152 states: a few hundred thousand edge checks.


================================================================================
APPROACH 3 · All-pairs distances + bitmask DP (Held-Karp style)
================================================================================
    dist = all-pairs shortest path lengths (BFS from each node)
    dp[mask][v] = shortest walk that visits exactly the nodes in mask, ending at v
    dp[1 << v][v] = 0
    dp[mask | 1 << w][w] = min(dp[mask][v] + dist[v][w])
    answer = min(dp[goal][v])

    Time: O(2^n * n^2)    Space: O(2^n * n)

Same complexity; this is the version that generalizes to weighted graphs,
where BFS no longer applies (Dijkstra over states, or this DP with weighted
distances).


================================================================================
STEP BY STEP TRACE · Example 1, graph = [[1,2,3],[0],[0],[0]]
================================================================================
    goal = 1111

    level 0: (0,0001) (1,0010) (2,0100) (3,1000)
    level 1: from (1,0010) -> (0,0011); from (2,0100) -> (0,0101);
             from (3,1000) -> (0,1001); from (0,0001) -> (1,0011),(2,0101),(3,1001)
    level 2: from (0,0011) -> (2,0111),(3,1011); from (1,0011) -> (0,0011) seen ...
    level 3: from (2,0111) -> (0,0111); from (3,1011) -> (0,1011) ...
    level 4: from (0,0111) -> (3,1111) = goal -> return 4

    Walk found: 1 -> 0 -> 2 -> 0 -> 3


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time           Space        Mutates input?
    ------------------------------  -------------  -----------  --------------
    Permutations + all-pairs dist   O(n! * n)      O(n^2)       No
    BFS over (node, mask) ✅        O(2^n * n^2)   O(2^n * n)   No
    All-pairs + bitmask DP          O(2^n * n^2)   O(2^n * n)   No


================================================================================
EDGE CASES
================================================================================
    n == 1               0 — already visited everything. (The BFS loop would
                          never find a NEW goal mask, so special-case it.)
    Star graph           Must return through the center repeatedly.
    Path graph           n - 1, starting at an end.
    Complete graph       n - 1.


================================================================================
COMMON MISTAKES
================================================================================
1. `visited` keyed by node alone. Example 1 returns -1/None because node 0
   can't be re-entered. Demo below.

2. Single-source BFS from node 0 only. You may start anywhere; starting at a
   leaf is often shorter. Demo below.

3. Forgetting n == 1.

4. Checking the goal when POPPING instead of when generating, and returning
   steps off by one. Either works if you're consistent.

5. Encoding states as tuples in a set is fine at this size; for speed use a
   2D list seen[mask][node].


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Weighted edges?
A: Dijkstra over (node, mask), or Approach 3 with weighted all-pairs
   distances (Floyd-Warshall).

Q: Must return to the start (a tour)?
A: Held-Karp TSP: dp as in Approach 3, answer min(dp[goal][v] + dist[v][start]).

Q: n = 30?
A: 2^30 states is ~10^9: infeasible exactly. Use heuristics or approximation
   (Christofides for metric TSP gives <= 1.5x optimal), or branch-and-bound.

Q: Visit only a required SUBSET of k nodes in a big graph?
A: Mask over the k required nodes only; BFS/Dijkstra over (node, mask) is
   O(2^k * (V + E)). "Shortest path collecting all keys" (LC 864) is this.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 864   Shortest Path to Get All Keys        — BFS over (cell, keys mask)
    LC 943   Find the Shortest Superstring        — Held-Karp over strings
    LC 1125  Smallest Sufficient Team             — bitmask DP over skills
    LC 698   Partition to K Equal Sum Subsets     — bitmask DP
================================================================================
"""

import random
import time
from collections import deque
from itertools import permutations
from typing import List, Optional


class Solution:
    def shortestPathLength(self, graph: List[List[int]]) -> int:
        n = len(graph)
        if n == 1:
            return 0
        goal = (1 << n) - 1
        seen = [[False] * n for _ in range(1 << n)]
        queue = deque()
        for i in range(n):
            seen[1 << i][i] = True
            queue.append((i, 1 << i))
        steps = 0
        while queue:
            steps += 1
            for _ in range(len(queue)):
                u, mask = queue.popleft()
                for v in graph[u]:
                    nxt = mask | (1 << v)
                    if nxt == goal:
                        return steps
                    if not seen[nxt][v]:
                        seen[nxt][v] = True
                        queue.append((v, nxt))
        return -1


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def all_pairs(graph: List[List[int]]) -> List[List[int]]:
    n = len(graph)
    dist = [[-1] * n for _ in range(n)]
    for s in range(n):
        dist[s][s] = 0
        q = deque([s])
        while q:
            u = q.popleft()
            for v in graph[u]:
                if dist[s][v] < 0:
                    dist[s][v] = dist[s][u] + 1
                    q.append(v)
    return dist


def shortest_held_karp(graph: List[List[int]]) -> int:
    n = len(graph)
    dist = all_pairs(graph)
    INF = float("inf")
    full = (1 << n) - 1
    dp = [[INF] * n for _ in range(1 << n)]
    for v in range(n):
        dp[1 << v][v] = 0
    for mask in range(1 << n):
        row = dp[mask]
        for v in range(n):
            if row[v] == INF:
                continue
            for w in range(n):
                if not mask >> w & 1:
                    cand = row[v] + dist[v][w]
                    if cand < dp[mask | 1 << w][w]:
                        dp[mask | 1 << w][w] = cand
    return int(min(dp[full]))


def shortest_permutations(graph: List[List[int]]) -> int:
    dist = all_pairs(graph)
    n = len(graph)
    best = float("inf")
    for order in permutations(range(n)):
        total = sum(dist[order[i]][order[i + 1]] for i in range(n - 1))
        best = min(best, total)
    return int(best)


def shortest_node_visited_bug(graph: List[List[int]]) -> Optional[int]:
    """Mistake 1: BFS state is (node, mask) but `seen` is keyed by node only."""
    n = len(graph)
    goal = (1 << n) - 1
    if n == 1:
        return 0
    queue = deque((i, 1 << i) for i in range(n))
    seen = set(range(n))
    steps = 0
    while queue:
        steps += 1
        for _ in range(len(queue)):
            u, mask = queue.popleft()
            for v in graph[u]:
                nxt = mask | 1 << v
                if nxt == goal:
                    return steps
                if v not in seen:                   # BUG
                    seen.add(v)
                    queue.append((v, nxt))
    return None


def shortest_single_source_bug(graph: List[List[int]]) -> int:
    """Mistake 2: always starts at node 0."""
    n = len(graph)
    if n == 1:
        return 0
    goal = (1 << n) - 1
    queue = deque([(0, 1)])
    seen = {(0, 1)}
    steps = 0
    while queue:
        steps += 1
        for _ in range(len(queue)):
            u, mask = queue.popleft()
            for v in graph[u]:
                nxt = mask | 1 << v
                if nxt == goal:
                    return steps
                if (v, nxt) not in seen:
                    seen.add((v, nxt))
                    queue.append((v, nxt))
    return -1


def random_connected_graph(rng: random.Random, n: int, extra: float) -> List[List[int]]:
    adj = [set() for _ in range(n)]
    for v in range(1, n):
        u = rng.randrange(v)
        adj[u].add(v); adj[v].add(u)
    for u in range(n):
        for v in range(u + 1, n):
            if rng.random() < extra:
                adj[u].add(v); adj[v].add(u)
    return [sorted(a) for a in adj]


# ==============================================================================
# TESTS — run:  python 016_shortest_path_visiting_all_nodes_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: BFS over states vs Held-Karp DP ---")
    cases = [
        ([[1, 2, 3], [0], [0], [0]], 4),
        ([[1], [0, 2, 4], [1, 3, 4], [2], [1, 2]], 4),
        ([[]], 0),
        ([[1], [0]], 1),
        ([[1, 2], [0, 2], [0, 1]], 2),
        ([[1], [0, 2], [1, 3], [2, 4], [3]], 4),
    ]
    for graph, want in cases:
        a, b = sol.shortestPathLength(graph), shortest_held_karp(graph)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  graph={graph}  bfs={a}  held-karp={b}  want={want}")

    print("\n--- randomized cross-check vs permutations of visiting order (300 graphs, n <= 7) ---")
    rng = random.Random(847)
    bad = 0
    for _ in range(300):
        g = random_connected_graph(rng, rng.randint(1, 7), rng.choice((0.0, 0.15, 0.4)))
        want = shortest_permutations(g)
        if sol.shortestPathLength(g) != want or shortest_held_karp(g) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  300 random connected graphs agree")

    print("\n--- mistakes LIVE ---")
    star = [[1, 2, 3], [0], [0], [0]]
    w1 = shortest_node_visited_bug(star)
    ok = w1 != 4
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  visited-by-node on the star: returns {w1}, want 4")
    print("      node 0 can't be re-entered once seen, so leaves 2 and 3 are unreachable")
    path = [[1], [0, 2], [1, 3], [2, 4], [3]]
    path_middle = [[1, 2], [0], [0, 3], [2, 4], [3]]        # node 0 sits in the middle
    w2 = shortest_single_source_bug(path_middle)
    right2 = sol.shortestPathLength(path_middle)
    ok = w2 > right2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  start at node 0 only, path 1-0-2-3-4: returns {w2}, true answer {right2}")

    print("\n--- worst case n = 12: state count and time ---")
    for name, g in (("path (sparse)", [[j for j in (i - 1, i + 1) if 0 <= j < 12] for i in range(12)]),
                    ("complete     ", [[j for j in range(12) if j != i] for i in range(12)]),
                    ("random       ", random_connected_graph(rng, 12, 0.2))):
        t0 = time.perf_counter(); a = sol.shortestPathLength(g); tb = time.perf_counter() - t0
        t0 = time.perf_counter(); b = shortest_held_karp(g); th = time.perf_counter() - t0
        all_ok &= a == b
        print(f"      {name}  answer {a:>2}   BFS {tb * 1000:7.1f} ms   Held-Karp {th * 1000:7.1f} ms   "
              f"(states: 12 * 4096 = 49,152)")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
