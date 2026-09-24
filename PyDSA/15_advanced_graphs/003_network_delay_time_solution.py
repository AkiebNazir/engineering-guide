"""
================================================================================
SOLUTION · LeetCode 743 · Network Delay Time                         [Medium]
https://leetcode.com/problems/network-delay-time/
================================================================================

THE CORE IDEA
--------------
"Time for ALL nodes to receive the signal" = time for the SLOWEST node to
receive it = max over every node of its shortest-path distance from k.
All weights are non-negative -> Dijkstra, straight off the topic guide's
Part 1 skeleton.

    dist = dijkstra(n, adj, k)
    return max(dist) if every node was reached else -1

O((V + E) log V) time, O(V + E) space.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): Bellman-Ford, relax every
edge V-1 times. Works (weights happen to be non-negative here, so it's not
even needed for correctness), but O(V * E) = O(100 * 6000) = 600,000 vs.
Dijkstra's O((V+E) log V) ~= O(6100 * 7) ~= 42,700 -- 14x more work for no
benefit, since nothing here requires negative-weight tolerance.

Approach 1 (Dijkstra, binary heap) [checked] -- the answer above.

Approach 2 (Dijkstra, O(V^2) array scan, no heap) -- for each of V rounds,
linearly scan all V nodes for the unvisited one with smallest tentative
distance. O(V^2 + E) total. WORSE here (V=100, E up to 6000: V^2=10,000 vs.
heap's ~42,700 log-weighted... actually competitive at this V) but this is
exactly the regime where the two approaches trade places -- see the runtime
demo below, which times both on this machine and shows where the heap's
"O(log V) per operation" overhead stops paying for itself on a SMALL,
DENSE graph.


================================================================================
STEP BY STEP TRACE
================================================================================
times = [[2,1,1],[2,3,1],[3,4,1]], n=4, k=2
adjacency: 2 -> [(1,1), (3,1)]     3 -> [(4,1)]     1 -> []     4 -> []

dist = [inf, inf, inf, inf, inf]  (index 0 unused; nodes are 1..4)
dist[2] = 0
heap = [(0, 2)]

pop (0, 2): d=0 matches dist[2]=0, proceed.
    neighbor 1, w=1: nd = 0+1 = 1 < dist[1]=inf -> dist[1]=1, push (1, 1)
    neighbor 3, w=1: nd = 0+1 = 1 < dist[3]=inf -> dist[3]=1, push (1, 3)
    heap = [(1,1), (1,3)]

pop (1, 1) [or (1,3) -- ties broken by heap order, either is fine]:
    d=1 matches dist[1]=1, proceed. Node 1 has no outgoing edges. Nothing to do.

pop (1, 3): d=1 matches dist[3]=1, proceed.
    neighbor 4, w=1: nd = 1+1 = 2 < dist[4]=inf -> dist[4]=2, push (2, 4)

pop (2, 4): d=2 matches dist[4]=2, proceed. No outgoing edges. Done.

Final dist[1..4] = [1, 0, 1, 2]. Every node reached (no inf remaining).
Answer = max(1, 0, 1, 2) = 2.  MATCHES the expected output.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time              Space   Mutates input?
    -------------------------------  ----------------  ------  --------------
    Bellman-Ford (V-1 rounds)        O(V * E)          O(V)    no
    Dijkstra, binary heap [chosen]   O((V+E) log V)     O(V+E)  no
    Dijkstra, O(V^2) array scan      O(V^2 + E)         O(V+E)  no


================================================================================
EDGE CASES
================================================================================
    n == 1                      -> the single node IS k, trivially reached
                                    at time 0. dist[k]=0, max = 0.
    k unreachable from itself    -> impossible; k always reaches itself at
                                    distance 0 by initialization, not travel.
    a node with no incoming edge -> stays at dist = inf forever -> answer -1
                                    (Example 3).
    disconnected graph            -> some dist[] entries remain inf -> -1.
    weight 0 edges                -> perfectly legal (0 <= wi); Dijkstra's
                                    correctness argument only needs weights
                                    to be NON-NEGATIVE, zero is fine.
    duplicate best distances       heap ties are broken arbitrarily by
    reaching a node                Python's tuple comparison (falls through
                                    to comparing node ids) -- harmless, since
                                    Dijkstra doesn't care WHICH shortest path
                                    is found, only its length.
    self-loops                    excluded by the constraints (ui != vi),
                                    but even if present they'd never improve
                                    dist[u] (relaxing u->u can't beat dist[u]
                                    itself when weights are non-negative).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the "skip stale heap entries" guard (`if d > dist[u]:
   continue`). Without it the algorithm still terminates and is still
   correct (the final dist[] values end up right regardless), but it may
   re-process a node's edge list more times than necessary -- the guard
   is what keeps the heap-pop count bounded by O(E) rather than growing
   unboundedly on graphs with many relaxations per node.

2. Treating "all nodes receive the signal" as SUM of distances instead of
   MAX. The signal propagates in PARALLEL along every path simultaneously
   -- the network is fully informed the moment its slowest node hears,
   not after every node has cumulatively heard one at a time.

3. Off-by-one on node labels: nodes are 1..n, not 0..n-1. Sizing
   `dist = [inf] * n` and indexing with the raw node id crashes (or
   silently reads the wrong slot) on node n. Size `n + 1` and leave index
   0 unused, or remap ids -- both are fine as long as it's done consistently.

4. Returning -1 by checking `if inf in dist` using Python's default float
   `inf` sentinel incorrectly (e.g., checking `dist[i] == 100000` with an
   arbitrary "big number" sentinel that a legitimate path could actually
   reach on a large weighted graph -- not possible here given the stated
   bounds, but a real bug pattern in other Dijkstra problems). Use
   `float('inf')` and compare against literally that.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if some edge weights could be negative?
A: Dijkstra's greedy lock-in breaks (topic guide Part 1) -- switch to
   Bellman-Ford, O(V * E), which also detects negative cycles as a side
   effect (a V-th improving round).

Q: What if you only cared about reaching a SPECIFIC target node, not all
   of them?
A: Same Dijkstra loop, just an early return the moment the target is
   popped off the heap with its final (non-stale) distance -- no need to
   drain the whole heap.

Q: How would you reconstruct the actual shortest PATH, not just its length?
A: Track a `prev[v] = u` parent pointer every time `dist[v]` is improved,
   then walk `prev` backwards from the target to k once Dijkstra finishes.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 787  Cheapest Flights Within K Stops (004 -- Dijkstra's greedy
            shortcut breaks under a hop-count limit; Bellman-Ford instead)
    LC 1631 Path With Minimum Effort (006 -- Dijkstra's skeleton, minimax
            relax instead of sum relax)
    LC 778  Swim in Rising Water (008 -- another minimax-Dijkstra)
    LC 1976 Number of Ways to Arrive at Destination (Dijkstra + counting
            the number of tied-shortest paths)
================================================================================
"""

import heapq
import random
import time
from collections import defaultdict
from typing import List


class Solution:
    def networkDelayTime(self, times: List[List[int]], n: int, k: int) -> int:
        """✅ Dijkstra, binary heap. O((V+E) log V) time, O(V+E) space."""
        adj = defaultdict(list)
        for u, v, w in times:
            adj[u].append((v, w))

        dist = [float('inf')] * (n + 1)
        dist[k] = 0
        heap = [(0, k)]
        while heap:
            d, u = heapq.heappop(heap)
            if d > dist[u]:                       # stale entry -- skip
                continue
            for v, w in adj[u]:
                nd = d + w
                if nd < dist[v]:
                    dist[v] = nd
                    heapq.heappush(heap, (nd, v))

        reachable = dist[1:n + 1]
        return max(reachable) if float('inf') not in reachable else -1

    def networkDelayTime_array_scan(self, times: List[List[int]], n: int, k: int) -> int:
        """Alternative: O(V^2 + E) Dijkstra with a linear scan instead of a
        heap -- no log factor, competitive on small/dense graphs (demoed
        below)."""
        adj = defaultdict(list)
        for u, v, w in times:
            adj[u].append((v, w))

        dist = [float('inf')] * (n + 1)
        dist[k] = 0
        visited = [False] * (n + 1)

        for _ in range(n):
            u, best = -1, float('inf')
            for cand in range(1, n + 1):
                if not visited[cand] and dist[cand] < best:
                    u, best = cand, dist[cand]
            if u == -1:
                break
            visited[u] = True
            for v, w in adj[u]:
                if dist[u] + w < dist[v]:
                    dist[v] = dist[u] + w

        reachable = dist[1:n + 1]
        return max(reachable) if float('inf') not in reachable else -1


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[2, 1, 1], [2, 3, 1], [3, 4, 1]], 4, 2, 2),
        ([[1, 2, 1]], 2, 1, 1),
        ([[1, 2, 1]], 2, 2, -1),
        ([[1, 2, 1], [2, 3, 2], [1, 3, 4]], 3, 1, 3),
        ([[1, 2, 1], [2, 1, 3]], 2, 2, 3),
        ([[1, 2, 0]], 2, 1, 0),
    ]

    print("--- correctness: heap-based vs array-scan Dijkstra agree ---")
    for times, n, k, want in cases:
        got_heap = sol.networkDelayTime([row[:] for row in times], n, k)
        got_scan = sol.networkDelayTime_array_scan([row[:] for row in times], n, k)
        ok = got_heap == want and got_scan == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n} k={k}  heap={got_heap} "
              f"scan={got_scan}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: heap vs. array scan, at the problem's own stated
    # bounds (n=100, up to 6000 edges) -- a SMALL, DENSE graph, exactly
    # the regime where the array scan's lack of a log factor can compete
    # with (or beat) the heap's extra O(log V) per operation.
    # --------------------------------------------------------------------
    print("\n--- DEMO: heap vs O(V^2) array scan at LC's own bounds ---")
    random.seed(743)
    n = 100
    edges = set()
    while len(edges) < 5900:
        u, v = random.randint(1, n), random.randint(1, n)
        if u != v:
            edges.add((u, v))
    times = [[u, v, random.randint(1, 100)] for u, v in edges]
    trials = 200

    t0 = time.perf_counter()
    for _ in range(trials):
        r1 = sol.networkDelayTime(times, n, 1)
    t_heap = time.perf_counter() - t0

    t0 = time.perf_counter()
    for _ in range(trials):
        r2 = sol.networkDelayTime_array_scan(times, n, 1)
    t_scan = time.perf_counter() - t0

    print(f"  n={n} nodes, {len(times)} edges, {trials} runs each:")
    print(f"    heap-based Dijkstra:  {t_heap * 1000:8.2f} ms total "
          f"({t_heap / trials * 1e6:7.1f} us/run)")
    print(f"    array-scan Dijkstra:  {t_scan * 1000:8.2f} ms total "
          f"({t_scan / trials * 1e6:7.1f} us/run)")
    print(f"    both agree on the answer: {r1 == r2} (both -> {r1})")
    print("    at n=100 with a near-complete edge set, O(V^2)=10,000 array")
    print("    reads competes directly with O(E log V)~=6000*7=42,000 heap")
    print("    operations -- this is exactly the crossover the complexity")
    print("    table predicts, not a fixed universal winner.")
    all_ok &= (r1 == r2)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
