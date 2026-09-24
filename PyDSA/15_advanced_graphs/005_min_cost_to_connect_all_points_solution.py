"""
================================================================================
SOLUTION · LeetCode 1584 · Min Cost to Connect All Points             [Medium]
https://leetcode.com/problems/min-cost-to-connect-all-points/
================================================================================

THE CORE IDEA
--------------
Every pair of points is an implicit edge (Manhattan distance), making this
a COMPLETE, DENSE graph -- n points, C(n,2) edges. This is textbook MST
territory (topic guide Part 4), and dense graphs favor array-based Prim's:
grow a tree from one point, tracking `min_dist[j]` = the cheapest known
edge from the IN-TREE set to each not-yet-in-tree point j, updating that
array in O(n) per round instead of pushing O(n^2) edges into a heap.

    min_dist = [inf] * n; min_dist[0] = 0
    in_tree = [False] * n
    total = 0
    for _ in range(n):
        u = argmin over not-in-tree j of min_dist[j]
        in_tree[u] = True
        total += min_dist[u]
        for v not in_tree: min_dist[v] = min(min_dist[v], manhattan(u, v))
    return total

O(n^2) time, O(n) space -- no adjacency list, no edge list, ever built.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): try every one of the
n^(n-2) labeled spanning trees (Cayley's formula) and take the cheapest.
Astronomically infeasible past single-digit n; named only to make clear
why "spanning tree" needs a greedy/incremental algorithm at all.

Approach 1 (Kruskal's: build all C(n,2) edges, sort, Union-Find) --
correct, but at n=1000 that's ~500,000 edges to build AND sort:
O(n^2 log n) just for the sort, plus O(n^2) space to hold them. Legitimate
for SPARSE graphs (topic guide Part 4) but strictly worse here.

Approach 2 (Prim's, array-based, no heap) [checked] -- the answer above.
O(n^2) time, O(n) space, never materializes an edge list at all -- the
graph is defined implicitly by the coordinate array and a distance
function.

Approach 3 (Prim's with a binary heap) -- O(E log V) = O(n^2 log n) here,
because a complete graph has O(n^2) edges to push. WORSE than the
array-based version specifically because the graph is dense -- the heap's
per-operation log factor is paid on every one of O(n^2) edges, while the
array version pays a flat O(n) scan per round with NO log factor at all.
This is the textbook case where "use a heap, it's asymptotically better"
is the wrong instinct -- demoed live below.


================================================================================
STEP BY STEP TRACE
================================================================================
points = [[0,0],[2,2],[3,10],[5,2],[7,0]]   indices 0,1,2,3,4

min_dist = [0, inf, inf, inf, inf]   in_tree = [F,F,F,F,F]

ROUND 1: cheapest not-in-tree min_dist is index 0 (0). Add point 0.
    in_tree=[T,F,F,F,F]  total=0
    update min_dist using distances FROM point 0:
        d(0,1)=|0-2|+|0-2|=4   -> min_dist[1]=4
        d(0,2)=|0-3|+|0-10|=13 -> min_dist[2]=13
        d(0,3)=|0-5|+|0-2|=7   -> min_dist[3]=7
        d(0,4)=|0-7|+|0-0|=7   -> min_dist[4]=7
    min_dist = [0, 4, 13, 7, 7]

ROUND 2: cheapest not-in-tree is index 1 (4). Add point 1.
    in_tree=[T,T,F,F,F]  total=0+4=4
    update using distances FROM point 1:
        d(1,2)=|2-3|+|2-10|=9    < 13 -> min_dist[2]=9
        d(1,3)=|2-5|+|2-2|=3     < 7  -> min_dist[3]=3
        d(1,4)=|2-7|+|2-0|=7     not  < 7 -> unchanged
    min_dist = [0, 4, 9, 3, 7]

ROUND 3: cheapest not-in-tree is index 3 (3). Add point 3.
    in_tree=[T,T,F,T,F]  total=4+3=7
    update using distances FROM point 3:
        d(3,2)=|5-3|+|2-10|=10   not < 9 -> unchanged
        d(3,4)=|5-7|+|2-0|=4     < 7  -> min_dist[4]=4
    min_dist = [0, 4, 9, 3, 4]

ROUND 4: cheapest not-in-tree is index 4 (4). Add point 4.
    in_tree=[T,T,F,T,T]  total=7+4=11
    update using distances FROM point 4:
        d(4,2)=|7-3|+|0-10|=14   not < 9 -> unchanged
    min_dist = [0, 4, 9, 3, 4]

ROUND 5: cheapest not-in-tree is index 2 (9). Add point 2.
    in_tree=[T,T,T,T,T]  total=11+9=20

All 5 points connected. total = 20.  MATCHES expected output.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time            Space  Mutates input?
    -------------------------------  --------------  -------  --------------
    Brute force (all spanning trees)  O(n^(n-2))      O(n)     no
    Kruskal's (build+sort all edges)  O(n^2 log n)    O(n^2)   no
    Prim's, array-based [chosen]      O(n^2)          O(n)     no
    Prim's, binary heap               O(n^2 log n)    O(n^2)   no


================================================================================
EDGE CASES
================================================================================
    n == 1                    -> a single point needs zero edges to be
                                  "fully connected" with itself. Cost 0.
    n == 2                    -> exactly one edge, cost = their distance.
    all points collinear       -> still just an MST over 1D-projected
                                  distances; the algorithm doesn't care
                                  about geometric shape, only pairwise cost.
    duplicate coordinates      -> excluded by the constraints ("All pairs
                                  are distinct"), but if it happened, that
                                  edge would have weight 0 and Prim's would
                                  happily take it first.
    negative coordinates       -> Manhattan distance via abs() handles this
                                  correctly regardless of sign.
    very large coordinate       -> up to 2 * 2*10^6 = 4*10^6 per edge, times
    magnitudes                   up to 999 edges in the tree -- total fits
                                  comfortably in a Python int (arbitrary
                                  precision) or even a 64-bit int elsewhere.


================================================================================
COMMON MISTAKES
================================================================================
1. Reaching for a heap-based Prim's or Kruskal's "because MST textbooks
   default to a heap" without noticing the graph here is DENSE (complete),
   where the O(n^2) array-scan Prim's beats both asymptotically AND in
   practice -- demoed live below with actual timings.

2. Treating this as a shortest-PATH problem (single source to single
   destination) instead of a spanning-TREE problem (connect everyone as
   cheaply as possible). Dijkstra minimizes cost to reach one target from
   one source; MST minimizes TOTAL cost of a tree touching every node --
   different objective, different algorithm, similar-looking heap code.

3. Recomputing Manhattan distance from scratch inside the innermost loop
   without caching anything, and calling a Euclidean-distance formula by
   habit (sqrt of squares) instead of the Manhattan `abs+abs` the problem
   actually specifies -- silently produces a different, wrong cost.

4. Off-by-one in "how many rounds": needing exactly n rounds (one per
   point, including the arbitrary starting point) to visit every node --
   not n-1 (that's the number of EDGES added, a subtlety worth stating out
   loud: n nodes, n-1 edges, but n rounds of "pick the next cheapest
   node," since round 1 just plants the starting node for free at cost 0).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if n were small (say <= 20) but the edges were given explicitly
   and sparse?
A: Then Kruskal's with Union-Find (topic guide Part 4/5) is the better
   fit -- sort the given (sparse) edge list once, greedily add non-cycle-
   forming edges. No reason to build C(n,2) implicit edges when the real
   edge count is already small.

Q: How would you also report WHICH edges were chosen, not just the total
   cost?
A: Track, alongside `min_dist[j]`, a `min_edge_from[j]` parent pointer
   recording which in-tree node currently offers j its cheapest edge;
   collect `(min_edge_from[u], u)` every time a node u is added.

Q: Can this go below O(n^2)?
A: Not in general for a dense/complete graph -- MST needs to consider
   enough structure to guarantee optimality, and a complete graph has
   Theta(n^2) edges, so any algorithm examining every point pair at least
   once is inherently Omega(n^2). (Specialized geometric MST algorithms
   using a k-d tree / Delaunay triangulation can do better for Euclidean
   or Manhattan metrics specifically, O(n log n), but that is well beyond
   interview scope -- worth naming as "exists" without implementing it.)


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 1135  Connecting Cities With Minimum Cost (identical MST shape, edges
             given explicitly instead of geometric)
    LC 1168  Optimize Water Distribution in a Village (MST with an extra
             "virtual node 0" trick for the well-connection cost)
    LC 1489  Find Critical and Pseudo-Critical Edges in MST (011 -- MST run
             repeatedly with one edge forced in/out)
    LC 1697  Checking Existence of Edge Length Limited Paths (Kruskal's-style
             incremental Union-Find, offline queries sorted by limit)
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def minCostConnectPoints(self, points: List[List[int]]) -> int:
        """✅ Prim's, array-based, no heap. O(n^2) time, O(n) space --
        appropriate because the graph is dense (complete)."""
        n = len(points)
        if n <= 1:
            return 0

        def manhattan(i: int, j: int) -> int:
            return (abs(points[i][0] - points[j][0]) +
                    abs(points[i][1] - points[j][1]))

        in_tree = [False] * n
        min_dist = [float('inf')] * n
        min_dist[0] = 0
        total = 0

        for _ in range(n):
            u, best = -1, float('inf')
            for cand in range(n):
                if not in_tree[cand] and min_dist[cand] < best:
                    u, best = cand, min_dist[cand]
            in_tree[u] = True
            total += best
            for v in range(n):
                if not in_tree[v]:
                    d = manhattan(u, v)
                    if d < min_dist[v]:
                        min_dist[v] = d

        return total

    def minCostConnectPoints_heap(self, points: List[List[int]]) -> int:
        """Alternative: Prim's with a binary heap. O(n^2 log n) here since
        a complete graph has O(n^2) edges -- WORSE on this dense input,
        demoed below."""
        n = len(points)
        if n <= 1:
            return 0

        def manhattan(i: int, j: int) -> int:
            return (abs(points[i][0] - points[j][0]) +
                    abs(points[i][1] - points[j][1]))

        visited = [False] * n
        heap = [(0, 0)]
        total, count = 0, 0

        while heap and count < n:
            d, u = heapq.heappop(heap)
            if visited[u]:
                continue
            visited[u] = True
            total += d
            count += 1
            for v in range(n):
                if not visited[v]:
                    heapq.heappush(heap, (manhattan(u, v), v))

        return total


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        ([[0, 0], [2, 2], [3, 10], [5, 2], [7, 0]], 20),
        ([[3, 12], [-2, 5], [-4, 1]], 18),
        ([[0, 0]], 0),
        ([[0, 0], [1, 1]], 2),
        ([[-1000000, -1000000], [1000000, 1000000]], 4000000),
    ]

    print("--- correctness: array-based vs heap-based Prim's agree ---")
    for points, want in cases:
        got_arr = sol.minCostConnectPoints([p[:] for p in points])
        got_heap = sol.minCostConnectPoints_heap([p[:] for p in points])
        ok = got_arr == want and got_heap == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={len(points)}  arr={got_arr} "
              f"heap={got_heap}  (want {want})")

    # --------------------------------------------------------------------
    # RUNTIME DEMO: array-based vs heap-based Prim's on a DENSE (complete)
    # graph near LC's own upper bound -- proves the "no heap needed on
    # dense graphs" claim rather than just asserting it.
    # --------------------------------------------------------------------
    print("\n--- DEMO: array-based vs heap-based Prim's, n=600 (dense) ---")
    random.seed(1584)
    n = 600
    pts = [[random.randint(-10**6, 10**6), random.randint(-10**6, 10**6)]
           for _ in range(n)]

    t0 = time.perf_counter()
    r1 = sol.minCostConnectPoints(pts)
    t_arr = time.perf_counter() - t0

    t0 = time.perf_counter()
    r2 = sol.minCostConnectPoints_heap(pts)
    t_heap = time.perf_counter() - t0

    print(f"  n={n} points (complete graph, ~{n*(n-1)//2:,} implicit edges):")
    print(f"    array-based Prim's (O(n^2)):        {t_arr * 1000:8.1f} ms")
    print(f"    heap-based Prim's (O(n^2 log n)):    {t_heap * 1000:8.1f} ms")
    print(f"    both agree on total cost: {r1 == r2}  (both -> {r1:,})")
    print(f"    array-based is {t_heap / t_arr:.1f}x faster on this dense "
          f"input -- the heap pays a log factor on every one of the O(n^2)")
    print(f"    edges it pushes, while the array scan never builds an edge "
          f"list at all.")
    all_ok &= (r1 == r2) and (t_arr < t_heap)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
