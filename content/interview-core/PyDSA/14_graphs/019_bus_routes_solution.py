"""
================================================================================
SOLUTION · LeetCode 815 · Bus Routes                                      [Hard]
https://leetcode.com/problems/bus-routes/
================================================================================

THE CORE IDEA
--------------
Count buses, so make BUSES the nodes. Two routes are adjacent if they share a
stop. BFS from the routes serving `source`; the first level that contains a
route serving `target` is the answer.

    stop_to_routes = {stop: [routes through it]}
    frontier = routes through source           (1 bus)
    each level: for every stop on those routes, every UNUSED route there
                joins the next level

Each route is dequeued once and each of its stops read once:
O(sum of route lengths).


================================================================================
APPROACH 1 · Stop graph with an edge between every pair on a route (priced)
================================================================================
Connect every two stops on the same route with weight 1 and BFS over stops.
A route with L stops creates L(L-1)/2 edges: 5 * 10^9 for one route of 10^5
stops. The demo counts the edges instead of building them.


================================================================================
APPROACH 2 · BFS over stops, without remembering used routes
================================================================================
From a stop, ride every route through it to all its stops. Correct, but a
route is re-scanned from EVERY one of its stops the BFS reaches — up to
O(L^2) work for a single long route. The demo counts stop visits.


================================================================================
APPROACH 3 · BFS over routes (or stops + used-route set) ✅ (the answer)
================================================================================
    if source == target: return 0
    stop_to_routes = defaultdict(list)
    for r, stops in enumerate(routes):
        for s in stops: stop_to_routes[s].append(r)
    used = set(stop_to_routes[source])
    frontier = list(used)
    buses = 1
    while frontier:
        nxt = []
        for r in frontier:
            for s in routes[r]:
                if s == target: return buses
                for r2 in stop_to_routes[s]:
                    if r2 not in used:
                        used.add(r2); nxt.append(r2)
        frontier, buses = nxt, buses + 1
    return -1

A stop can be reached by many routes, so the inner scan of stop_to_routes[s]
can repeat; clearing stop_to_routes[s] after its first scan keeps the total
work linear.

    Time: O(sum of route lengths)    Space: O(sum of route lengths)


================================================================================
STEP BY STEP TRACE · routes = [[1, 2, 7], [3, 6, 7]], 1 -> 6
================================================================================
    stop_to_routes: 1:[0] 2:[0] 7:[0,1] 3:[1] 6:[1]

    buses = 1, frontier [route 0]
      stops 1, 2, 7 — none is 6
      stop 7 -> route 1 unused: next [route 1]
    buses = 2, frontier [route 1]
      stops 3, 6 — 6 is the target -> return 2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time               Space        Mutates input?
    ------------------------------  -----------------  -----------  --------------
    All-pairs stop graph            O(sum L^2)         O(sum L^2)   No
    Stop BFS, routes re-scanned     O(sum L^2) worst   O(sum L)     No
    Route BFS ✅                    O(sum L)           O(sum L)     No


================================================================================
EDGE CASES
================================================================================
    source == target            0, even if no route serves it.
    source served by no route   -1.
    target on the source route  1.
    Disconnected route groups   -1.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning the number of STOPS (or stop-to-stop hops) instead of buses.
   [[1,2,3,4,5,6,7]], 1 -> 7 is one bus, not six hops. Demo.

2. Forgetting source == target -> 0. Without the check, [[1,7],[3,5]], 5 -> 5
   returns 1 (it boards a bus to reach where it already is). Demo.

3. Not remembering used routes: correct answers, but one long route is
   re-read from every stop on it. Demo counts the work.

4. Building the all-pairs stop graph: the edge count is quadratic in the
   route length. Demo counts edges for a 10^5-stop route.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Minimise total travel time instead, with transfer penalties?
A: Weighted edges: Dijkstra over (stop, route) states, with a cost for
   changing route (15_advanced_graphs/003).

Q: Many queries on the same routes?
A: Precompute the route graph once (routes as nodes), then BFS per query; or
   all-pairs BFS on the route graph if the number of routes is small (500).

Q: Return the actual sequence of buses?
A: Record each route's parent route in the BFS and walk back from the route
   that reached the target.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 127  Word Ladder (016)             — BFS where the graph must be built cleverly
    LC 752  Open the Lock (018)           — BFS over states
    LC 1345 Jump Game IV                  — clear a group after using it once
    LC 787  Cheapest Flights Within K Stops (15_advanced_graphs/004)
================================================================================
"""

import random
import time
from collections import defaultdict, deque
from typing import List


class Solution:
    def numBusesToDestination(self, routes: List[List[int]], source: int, target: int) -> int:
        if source == target:
            return 0
        stop_to_routes = defaultdict(list)
        for r, stops in enumerate(routes):
            for s in stops:
                stop_to_routes[s].append(r)
        used = set(stop_to_routes.get(source, ()))
        frontier = list(used)
        buses = 1
        while frontier:
            nxt = []
            for r in frontier:
                for s in routes[r]:
                    if s == target:
                        return buses
                    for r2 in stop_to_routes[s]:
                        if r2 not in used:
                            used.add(r2)
                            nxt.append(r2)
                    stop_to_routes[s] = []            # this stop's routes are all handled
            frontier = nxt
            buses += 1
        return -1


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
WORK = 0


def stop_bfs_no_used_routes(routes: List[List[int]], source: int, target: int) -> int:
    """Approach 2 (and the oracle): BFS over (stop, buses); counts stop reads."""
    global WORK
    if source == target:
        return 0
    stop_to_routes = defaultdict(list)
    for r, stops in enumerate(routes):
        for s in stops:
            stop_to_routes[s].append(r)
    seen = {source}
    q = deque([(source, 0)])
    while q:
        stop, buses = q.popleft()
        for r in stop_to_routes[stop]:
            for s in routes[r]:                       # the whole route, every time
                WORK += 1
                if s not in seen:
                    if s == target:
                        return buses + 1
                    seen.add(s)
                    q.append((s, buses + 1))
    return -1


def count_stop_hops(routes: List[List[int]], source: int, target: int) -> int:
    """Mistake 1: shortest number of stop-to-stop hops along routes."""
    adj = defaultdict(set)
    for stops in routes:
        for a, b in zip(stops, stops[1:]):
            adj[a].add(b); adj[b].add(a)
    dist, q = {source: 0}, deque([source])
    while q:
        u = q.popleft()
        if u == target:
            return dist[u]
        for v in adj[u]:
            if v not in dist:
                dist[v] = dist[u] + 1
                q.append(v)
    return -1


def no_same_stop_check(routes: List[List[int]], source: int, target: int) -> int:
    """Mistake 2: always boards at least one bus."""
    stop_to_routes = defaultdict(list)
    for r, stops in enumerate(routes):
        for s in stops:
            stop_to_routes[s].append(r)
    used = set(stop_to_routes[source]); frontier = list(used); buses = 1
    while frontier:
        nxt = []
        for r in frontier:
            if target in routes[r]:
                return buses
            for s in routes[r]:
                for r2 in stop_to_routes[s]:
                    if r2 not in used:
                        used.add(r2); nxt.append(r2)
        frontier, buses = nxt, buses + 1
    return -1


# ==============================================================================
# TESTS — run:  python 019_bus_routes_solution.py
# ==============================================================================
def run_tests() -> None:
    global WORK
    all_ok = True
    sol = Solution()

    print("--- correctness: route BFS vs stop BFS ---")
    cases = [([[1, 2, 7], [3, 6, 7]], 1, 6, 2), ([[7, 12], [4, 5, 15], [6], [15, 19], [9, 12, 13]], 15, 12, -1),
             ([[1, 2, 3]], 1, 1, 0), ([[1, 2, 3]], 1, 3, 1), ([[1, 2], [2, 3], [3, 4], [4, 5]], 1, 5, 4),
             ([[1, 7], [3, 5]], 5, 5, 0), ([[1, 2], [3, 4]], 1, 4, -1),
             ([[1, 2, 3, 4, 5, 6, 7], [7, 8], [2, 8]], 1, 8, 2)]
    for routes, source, target, want in cases:
        results = (sol.numBusesToDestination([r[:] for r in routes], source, target),
                   stop_bfs_no_used_routes(routes, source, target))
        ok = all(x == want for x in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {source}->{target} on {len(routes)} routes  got={results}  want={want}")

    print("\n--- randomized cross-check (2,000 random networks) ---")
    rng = random.Random(815)
    bad = 0
    for _ in range(2000):
        routes = [rng.sample(range(30), rng.randint(1, 6)) for _ in range(rng.randint(1, 8))]
        s, t = rng.randrange(30), rng.randrange(30)
        if sol.numBusesToDestination([r[:] for r in routes], s, t) != stop_bfs_no_used_routes(routes, s, t):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  2,000 random networks: both BFS forms agree")

    print("\n--- mistakes LIVE ---")
    one = [[1, 2, 3, 4, 5, 6, 7]]
    w1 = count_stop_hops(one, 1, 7)
    ok = w1 == 6 and sol.numBusesToDestination([r[:] for r in one], 1, 7) == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  counting stop hops: one route 1..7 -> {w1}, want 1 bus")
    w2 = no_same_stop_check([[1, 7], [3, 5]], 5, 5)
    ok = w2 == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no source == target check: 5 -> 5 gives {w2}, want 0")

    print("\n--- the cost of not remembering used routes: one route of 3,000 stops ---")
    long_route = [list(range(3000)), [2999, 5000]]
    WORK = 0
    t0 = time.perf_counter(); r1 = stop_bfs_no_used_routes(long_route, 0, 5000); t1 = time.perf_counter()
    r2 = sol.numBusesToDestination([r[:] for r in long_route], 0, 5000); t2 = time.perf_counter()
    ok = r1 == r2 == 2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  stop BFS read {WORK:,} stops in {1000 * (t1 - t0):.0f} ms; "
          f"route BFS read 3,002 in {1000 * (t2 - t1):.1f} ms; both answer {r1}")

    print("\n--- all-pairs stop graph, counted not built ---")
    for L in (1_000, 10_000, 100_000):
        print(f"      one route of {L:>7,} stops -> {L * (L - 1) // 2:>13,} edges")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
