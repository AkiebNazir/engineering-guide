"""
================================================================================
QUESTION · LeetCode 1192 · Critical Connections in a Network             [Hard]
https://leetcode.com/problems/critical-connections-in-a-network/
================================================================================

PROBLEM
-------
There are n servers numbered from 0 to n - 1 connected by undirected
server-to-server connections forming a network where connections[i] =
[ai, bi] represents a connection between servers ai and bi. Any server can
reach other servers directly or indirectly through the network.

A critical connection is a connection that, if removed, will make some
servers unable to reach some other server.

Return all critical connections in the network in any order.


EXAMPLES
--------
Example 1:
    Input:  n = 4, connections = [[0,1],[1,2],[2,0],[1,3]]
    Output: [[1,3]]
    Explanation: [[3,1]] is also accepted.

Example 2:
    Input:  n = 2, connections = [[0,1]]
    Output: [[0,1]]


CONSTRAINTS
-----------
    2 <= n <= 10^5
    n - 1 <= connections.length <= 10^5
    0 <= ai, bi <= n - 1
    ai != bi
    There are no repeated connections.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A "critical connection" is exactly a BRIDGE in graph theory: an edge whose
removal disconnects the graph (equivalently, an edge that lies on NO
cycle). This is Tarjan's bridge-finding algorithm (topic guide Part 6):
one DFS pass tracking each node's DISCOVERY TIME (`disc[]`) and LOW-LINK
VALUE (`low[]` -- the earliest discovery time reachable from that node's
subtree via at most one back-edge to an ancestor). An edge (u, child) is a
bridge iff `low[child] > disc[u]` -- nothing in child's subtree can reach
back up to u or higher through any OTHER route.

With n up to 10^5, a naive "remove each edge, check connectivity" approach
(O(E) removals x O(V+E) connectivity check each = O(E*(V+E))) is far too
slow. Tarjan's finds every bridge in a SINGLE O(V+E) pass.

CRITICAL IMPLEMENTATION NOTE: with n up to 10^5, a recursive DFS can
exceed Python's default recursion limit on a long chain (a path graph is
exactly the worst case). Implement this ITERATIVELY with an explicit
stack (topic guide Part 6's closing note).

PROGRESSIVE HINTS
------------------
Hint 1: Build an adjacency list. Track disc[] (discovery order) and low[]
        (lowest reachable discovery time) per node, both initialized to
        "unvisited"/infinity.
Hint 2: Standard DFS: when visiting neighbor v from u, if v is unvisited,
        recurse (conceptually) and afterward set low[u] = min(low[u],
        low[v]); if v IS visited and v is NOT u's immediate parent (avoid
        walking straight back the edge you just came from), it's a back-
        edge: low[u] = min(low[u], disc[v]).
Hint 3: The bridge test: after fully processing child v of u (in the DFS
        tree), (u, v) is a bridge iff low[v] > disc[u].
Hint 4: Implement the DFS with an EXPLICIT STACK, tracking each frame's
        "which neighbor index am I paused at" so you can resume and do the
        low-link update against the child after it "returns."

COMPLEXITY TARGET
------------------
    Time:  O(V + E)
    Space: O(V + E)
================================================================================
"""

from typing import List


class Solution:
    def criticalConnections(self, n: int, connections: List[List[int]]) -> List[List[int]]:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    def normalize(edges):
        return sorted(tuple(sorted(e)) for e in (edges or []))

    cases = [
        (4, [[0, 1], [1, 2], [2, 0], [1, 3]], [[1, 3]]),
        (2, [[0, 1]], [[0, 1]]),
        (6, [[0, 1], [1, 2], [2, 0], [1, 3], [3, 4], [4, 5], [5, 3]], [[1, 3]]),
    ]
    for n, connections, want in cases:
        got = sol.criticalConnections(n, [c[:] for c in connections])
        ok = normalize(got) == normalize(want)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
