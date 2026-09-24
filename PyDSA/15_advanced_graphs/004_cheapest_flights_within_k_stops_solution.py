"""
================================================================================
SOLUTION · LeetCode 787 · Cheapest Flights Within K Stops             [Medium]
https://leetcode.com/problems/cheapest-flights-within-k-stops/
================================================================================

THE CORE IDEA
--------------
"At most k stops" = "at most k+1 edges". Bellman-Ford relaxes every edge
once per ROUND, and round r finds every shortest path using AT MOST r
edges -- so capping it at k+1 rounds directly enforces the hop limit that
Dijkstra's priority queue has no way to express (topic guide Part 2).

    dist = [inf] * n; dist[src] = 0
    for _ in range(k + 1):
        snapshot = dist[:]                       # THE critical line
        for u, v, w in flights:
            if snapshot[u] + w < dist[v]:
                dist[v] = snapshot[u] + w
    return dist[dst] if dist[dst] < inf else -1

O(k * E) time, O(V) space.


================================================================================
WHY THE SNAPSHOT IS THE WHOLE PROBLEM
================================================================================
Relax against a SNAPSHOT of last round's distances, not the live `dist`
array being written in the SAME round. Without the snapshot, a single
round can silently chain multiple edges together:

    round r relaxes edge (a,b): dist[b] updated using dist[a] from round r-1  OK
    SAME round r then relaxes edge (b,c) using the JUST-UPDATED dist[b] --
    that is TWO edges (a->b->c) being applied within what was supposed to
    be a single one-edge-per-round pass. Do this for k+1 rounds and the
    algorithm secretly explores paths with far more than k+1 edges,
    silently returning an answer with too many stops as if it were legal.

The snapshot pins each round to "everything I could reach using AT MOST
the PREVIOUS round's hop count, plus exactly one more edge" -- which is
precisely the guarantee Bellman-Ford's round structure is built to give.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, name it and reject it): DFS/backtrack every
simple path from src to dst with <= k+1 edges, take the minimum cost.
Exponential in the worst case (up to (n-1)! paths) -- correct for tiny
graphs, unusable at n=100.

Approach 1 (Bellman-Ford, capped + snapshotted) [checked] -- the answer
above. O(k*E) time, O(V) space, handles the hop limit natively.

Approach 2 (modified Dijkstra, state = (cost, node, stops_used)) -- push
(cost, node, stops) onto the heap instead of just (cost, node); pop the
cheapest, and if stops_used <= k, relax neighbors with stops_used+1.
CANNOT prune with a simple "already finalized this node" check the way
plain Dijkstra does -- a node may need to be revisited with a WORSE cost
but FEWER remaining stops, because that state might still unlock a
cheaper path later. Track best-cost-seen PER (node, stops) pair instead of
per node. Same asymptotic ballpark as Bellman-Ford here, more delicate to
get right; worth naming as the "Dijkstra can be adapted, but only by
folding stops into the state" answer to a likely follow-up.


================================================================================
STEP BY STEP TRACE
================================================================================
n=4, flights=[[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]]
src=0, dst=3, k=1  (at most k+1 = 2 edges)

dist = [0, inf, inf, inf]

ROUND 1 (uses up to 1 edge):
    snapshot = [0, inf, inf, inf]
    (0,1,100): snapshot[0]+100=100 < dist[1]=inf -> dist[1]=100
    (1,2,100): snapshot[1]+100=inf -> no change (snapshot[1] is still inf,
               NOT the 100 just written this round -- that's the point)
    (2,0,100): snapshot[2]+100=inf -> no change
    (1,3,600): snapshot[1]+600=inf -> no change
    (2,3,200): snapshot[2]+200=inf -> no change
    dist = [0, 100, inf, inf]

ROUND 2 (uses up to 2 edges = k+1):
    snapshot = [0, 100, inf, inf]
    (0,1,100): snapshot[0]+100=100, dist[1] already 100 -> no improvement
    (1,2,100): snapshot[1]+100=200 < dist[2]=inf -> dist[2]=200
    (2,0,100): snapshot[2]+100=inf -> no change
    (1,3,600): snapshot[1]+600=700 < dist[3]=inf -> dist[3]=700
    (2,3,200): snapshot[2]+200=inf -> no change (snapshot[2] is still inf;
               the 200 just computed for dist[2] THIS round cannot feed
               into ANOTHER relaxation this same round)
    dist = [0, 100, 200, 700]

k+1=2 rounds done. dist[3] = 700. MATCHES expected output.

    (Without the snapshot, round 2 would ALSO see dist[2]=200 as usable
    input for (2,3,200), producing dist[3] = 200+200 = 400 -- the 3-edge
    path 0->1->2->3, which uses 2 STOPS and violates k=1. 400 is what a
    naive unbounded Dijkstra/Bellman-Ford would return; 700 is correct.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time         Space   Mutates input?
    -------------------------------------  -----------  ------  --------------
    Brute-force DFS over all paths         O((n-1)!)    O(n)    no
    Bellman-Ford, capped+snapshot [chosen] O(k * E)     O(V)    no
    Modified Dijkstra, (node, stops) state O(E*k*log)   O(V*k)  no


================================================================================
EDGE CASES
================================================================================
    k == 0                    -> only the direct flight counts (0 rounds of
                                  chaining beyond the first edge); Example 3.
    no path exists at all      -> dist[dst] stays inf after k+1 rounds -> -1.
    a path exists but only      -> dist[dst] stays inf within the cap even
    with MORE than k+1 edges      though a longer, cheaper-looking path
                                  technically connects src to dst -> -1
                                  (the hop limit is a hard constraint, not
                                  a preference).
    src == dst                  -> excluded by the constraints (src != dst),
                                  would otherwise be 0 trivially.
    n == 1                      -> excluded implicitly (src != dst needs
                                  >= 2 cities).
    multiple edges relax the     the snapshot handles this correctly by
    SAME node in one round        construction -- both compete against the
                                  SAME baseline, only the smaller wins.
    the cheapest path uses       correctly rejected -- Example 1: 400 via
    MORE stops than allowed       2 stops is cheaper than 700 via 1 stop,
                                  but only 700 respects k=1.


================================================================================
COMMON MISTAKES
================================================================================
1. Relaxing against the LIVE `dist` array instead of a per-round snapshot
   -- silently allows more than one extra edge per round, producing an
   answer that violates the stop limit with no error raised. Demoed live
   below using Example 1.

2. Reaching for plain Dijkstra without folding "stops used" into the
   state. A cheap-but-many-stops path can get finalized first and block
   Dijkstra from ever reconsidering a pricier-but-fewer-stops alternative
   that the stop limit actually requires.

3. Off-by-one between "stops" and "edges" -- k stops means k+1 edges, not
   k edges. Running only k rounds instead of k+1 silently under-counts the
   allowed hops and can miss the true cheapest route (or wrongly return -1
   when a valid route exists).

4. Early-exiting the round loop the moment `dist[dst]` becomes finite.
   WRONG -- a later round (still within the k+1 cap) might find something
   even cheaper via a different, longer-but-still-legal route; only exit
   early if this round made literally zero improvements (a valid
   optimization, but "found ANY path" is not the same as "found the
   cheapest legal path").


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why not just use Dijkstra? Cost is non-negative here.
A: Dijkstra's greedy lock-in optimizes for GLOBAL cheapest cost, blind to
   hop count. A 1-stop $700 path can get finalized as "the" shortest path
   to a node before a cheaper-but-2-stop alternative is even considered,
   and plain Dijkstra has no mechanism to reconsider a node once
   finalized -- even though here that "worse" path is the only one that
   respects the stop limit. Folding stops into Dijkstra's state (Approach
   2) fixes this, at the cost of the elegance that makes Dijkstra
   attractive in the first place.

Q: What's the actual time complexity difference vs. unbounded Dijkstra?
A: Unbounded Dijkstra: O((V+E) log V), independent of any hop cap.
   Capped Bellman-Ford: O(k * E) -- scales with k, which is bounded by n
   here (k < n per constraints) so worst case O(n * E), generally worse
   than Dijkstra's bound but the ONLY one of the two that is even
   CORRECT under a hop limit.

Q: How would you return the actual cheapest ROUTE, not just its price?
A: Track a `prev[v]` parent pointer alongside each successful relaxation
   (careful: must also snapshot `prev` per round, same reasoning as
   `dist`), then walk backwards from dst once the rounds finish.


================================================================================
RELATED PROBLEMS -- THE PATTERN FAMILY
================================================================================
    LC 743  Network Delay Time (003 -- Dijkstra, no hop limit, the
            un-constrained sibling of this problem)
    LC 787  (this problem) -- Bellman-Ford's signature use case: bounded
            hop count
    LC 505  The Maze II (Dijkstra with a rolling-ball movement rule
            instead of a hop cap)
    LC 1928 Minimum Cost to Reach Destination in Time (Dijkstra/Bellman-
            Ford hybrid with BOTH a cost AND a separate time budget --
            two-dimensional constraint, same family as this problem)
================================================================================
"""

from typing import List


class Solution:
    def findCheapestPrice(self, n: int, flights: List[List[int]], src: int,
                          dst: int, k: int) -> int:
        """✅ Bellman-Ford, capped at k+1 rounds, snapshotted per round.
        O(k * E) time, O(V) space."""
        INF = float('inf')
        dist = [INF] * n
        dist[src] = 0

        for _ in range(k + 1):
            snapshot = dist[:]          # THE critical line -- see prose above
            for u, v, w in flights:
                if snapshot[u] + w < dist[v]:
                    dist[v] = snapshot[u] + w

        return dist[dst] if dist[dst] < INF else -1

    def findCheapestPrice_no_snapshot_BROKEN(self, n: int, flights: List[List[int]],
                                              src: int, dst: int, k: int) -> int:
        """✗ BROKEN ON PURPOSE -- mistake #1. Relaxes against the LIVE
        dist array, letting one round silently chain more than one edge.
        Demoed live below."""
        INF = float('inf')
        dist = [INF] * n
        dist[src] = 0

        for _ in range(k + 1):
            for u, v, w in flights:
                if dist[u] + w < dist[v]:          # no snapshot -- BUG
                    dist[v] = dist[u] + w

        return dist[dst] if dist[dst] < INF else -1


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (4, [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]], 0, 3, 1, 700),
        (3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 1, 200),
        (3, [[0, 1, 100], [1, 2, 100], [0, 2, 500]], 0, 2, 0, 500),
        (3, [[0, 1, 100], [1, 2, 100]], 0, 2, 0, -1),
        (5, [[0, 1, 5], [1, 2, 5], [0, 3, 2], [3, 1, 2], [1, 4, 1], [4, 2, 1]], 0, 2, 2, 7),
    ]

    print("--- correctness ---")
    for n, flights, src, dst, k, want in cases:
        got = sol.findCheapestPrice(n, [f[:] for f in flights], src, dst, k)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  src={src} dst={dst} k={k}  "
              f"-> {got}  (want {want})")

    # --------------------------------------------------------------------
    # ⚠️ LIVE DEMO: no-snapshot relaxation silently violates the stop cap.
    # --------------------------------------------------------------------
    print("\n--- ⚠️  live demo: mistake #1, relaxing without a snapshot ---")
    n = 4
    flights = [[0, 1, 100], [1, 2, 100], [2, 0, 100], [1, 3, 600], [2, 3, 200]]
    src, dst, k = 0, 3, 1
    correct = sol.findCheapestPrice(n, flights, src, dst, k)
    broken = sol.findCheapestPrice_no_snapshot_BROKEN(n, flights, src, dst, k)
    print(f"  n={n} src={src} dst={dst} k={k} (at most {k+1} edges)")
    print(f"  correct (snapshotted):   {correct}   (the legal 1-stop route, "
          f"0->1->3, cost 700)")
    print(f"  broken (no snapshot):    {broken}   (secretly uses the 2-stop "
          f"route 0->1->2->3, cost 400)")
    exposed = broken != correct
    print(f"  the broken version returned a price that needs MORE stops "
          f"than k={k} allows: {exposed}  (no exception raised)")
    all_ok &= exposed and (correct == 700) and (broken == 400)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
