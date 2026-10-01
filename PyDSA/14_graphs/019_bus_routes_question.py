"""
================================================================================
LeetCode 815 · Bus Routes                                                 [Hard]
https://leetcode.com/problems/bus-routes/
Topic: 14 · Graphs (BFS)
================================================================================

PROBLEM
-------
You are given an array routes representing bus routes, where routes[i] is the
list of stops bus i visits (it repeats that loop forever).

You start at the bus stop source (not on a bus) and want to reach the stop
target. You can travel between stops only by bus.

Return the LEAST NUMBER OF BUSES you must take to travel from source to
target, or -1 if it is not possible.


EXAMPLES
--------
Example 1:   routes = [[1, 2, 7], [3, 6, 7]], source = 1, target = 6   ->  2
    Take bus 0 to stop 7, then bus 1 to stop 6.

Example 2:   routes = [[7, 12], [4, 5, 15], [6], [15, 19], [9, 12, 13]],
             source = 15, target = 12                                      ->  -1


CONSTRAINTS
-----------
    1 <= routes.length <= 500
    1 <= routes[i].length <= 10^5, and all stops on one route are distinct
    sum(routes[i].length) <= 10^5
    0 <= routes[i][j] < 10^6
    0 <= source, target < 10^6


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The cost is the number of BUSES, not stops. Riding a bus from its first stop
to its last costs 1, however many stops it passes. So the natural graph is
not "stop -> next stop":

    node = a bus route
    edge = two routes share a stop (you can change buses there)

Unweighted edges -> BFS gives the fewest buses. Start from every route that
serves source (1 bus), and stop at the first route that serves target.

An equivalent formulation runs BFS over stops but expands a WHOLE route at
once, and marks the route as used so it is never scanned again.


WHAT TO THINK ABOUT
--------------------
1. Why is "stop -> neighbouring stop" the wrong graph for counting buses?

2. If you connect every pair of stops on the same route, how many edges does
   a route with 10^5 stops create?

3. In a BFS over stops, what must you remember besides visited stops, so a
   long route isn't re-scanned from each of its stops?

4. source == target?


PROGRESSIVE HINTS
------------------
Hint 1: Build stop -> list of routes that serve it.

Hint 2: BFS level = number of buses. Queue the routes through source; when a
        route is dequeued, look at each of its stops; any unused route at
        those stops is the next level.

Hint 3: Keep a set of used routes (and optionally visited stops).


COMPLEXITY TARGET
------------------
    Time:  O(sum of route lengths)
    Space: O(sum of route lengths)
================================================================================
"""
from typing import List


class Solution:
    def numBusesToDestination(self, routes: List[List[int]], source: int, target: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 019_bus_routes_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        ([[1, 2, 7], [3, 6, 7]], 1, 6, 2),
        ([[7, 12], [4, 5, 15], [6], [15, 19], [9, 12, 13]], 15, 12, -1),
        ([[1, 2, 3]], 1, 1, 0),
        ([[1, 2, 3]], 1, 3, 1),
        ([[1, 2], [2, 3], [3, 4], [4, 5]], 1, 5, 4),
        ([[1, 7], [3, 5]], 5, 5, 0),
        ([[1, 2], [3, 4]], 1, 4, -1),
        ([[1, 2, 3, 4, 5, 6, 7], [7, 8], [2, 8]], 1, 8, 2),
    ]
    all_ok = True
    for routes, source, target, want in cases:
        got = Solution().numBusesToDestination([r[:] for r in routes], source, target)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  routes={routes} {source}->{target}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
