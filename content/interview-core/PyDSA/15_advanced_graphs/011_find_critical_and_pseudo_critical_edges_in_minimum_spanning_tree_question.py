"""
================================================================================
QUESTION · LeetCode 1489 · Find Critical and Pseudo-Critical Edges in
Minimum Spanning Tree                                                   [Hard]
https://leetcode.com/problems/find-critical-and-pseudo-critical-edges-in-minimum-spanning-tree/
================================================================================

PROBLEM
-------
Given a weighted undirected connected graph with n vertices numbered from
0 to n - 1, and an array `edges` where edges[i] = [ai, bi, weighti]
represents a bidirectional and weighted edge between nodes ai and bi. A
minimum spanning tree (MST) is a subset of the graph's edges that connects
all vertices without cycles and with the minimum possible total edge
weight.

Find ALL the critical and pseudo-critical edges in the given graph's
minimum spanning tree (MST). An MST edge whose deletion from the graph
would cause the MST weight to increase is called a CRITICAL edge. On the
other hand, a PSEUDO-CRITICAL edge is that which can appear in SOME MSTs
but not all.

Return a list of two lists [critical, pseudo-critical], containing the
indices of the critical and pseudo-critical edges, respectively (both in
non-decreasing order, per LeetCode's own examples).


EXAMPLES
--------
Example 1:
    Input:  n = 5, edges = [[0,1,1],[1,2,1],[2,3,2],[0,3,2],[0,4,3],
                            [3,4,3],[1,4,6]]
    Output: [[0,1],[2,3,4,5]]

Example 2:
    Input:  n = 4, edges = [[0,1,1],[1,2,1],[2,3,1],[0,3,1]]
    Output: [[],[0,1,2,3]]


CONSTRAINTS
-----------
    2 <= n <= 100
    1 <= edges.length <= min(200, n * (n - 1) / 2)
    edges[i].length == 3
    0 <= ai < bi < n
    1 <= weighti <= 1000
    All pairs (ai, bi) are distinct.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Compute the true MST weight once (Kruskal's, topic guide Part 4). Then, for
EVERY edge index i, ask two separate questions by re-running Kruskal's:

    CRITICAL:  exclude edge i entirely, run Kruskal's on the rest. If the
               resulting MST is heavier than the true MST weight (or no
               longer spans all n nodes at all), edge i was IRREPLACEABLE
               -- critical.

    PSEUDO-CRITICAL: force edge i into the MST FIRST (union its two
               endpoints before running Kruskal's normally on everything
               else). If the resulting total weight equals the true MST
               weight, edge i CAN participate in an optimal MST (even
               though 001 already knows it isn't critical, since excluding
               it didn't hurt) -- pseudo-critical.

Every edge falls into exactly one of three buckets: critical, pseudo-
critical, or neither (irrelevant to any optimal MST).

PROGRESSIVE HINTS
------------------
Hint 1: Write one reusable helper: `mst_weight(edges, exclude=None,
        include=None)` that runs Kruskal's while skipping the `exclude`
        edge and pre-unioning the `include` edge's endpoints before
        anything else.
Hint 2: Compute `base = mst_weight()` first -- the true MST weight, no
        exclusions or forced inclusions.
Hint 3: For each edge i: if `mst_weight(exclude=i)` is worse than `base`
        (or the graph becomes disconnected), i is critical.
Hint 4: For each remaining edge i: if `mst_weight(include=i) == base`, i
        is pseudo-critical.

COMPLEXITY TARGET
------------------
    Time:  O(E^2 * alpha(V)) -- E edges, each requiring one O(E*alpha(V))
           Kruskal's run
    Space: O(V + E)
================================================================================
"""

from typing import List


class Solution:
    def findCriticalAndPseudoCriticalEdges(self, n: int,
                                           edges: List[List[int]]) -> List[List[int]]:
        # YOUR CODE HERE
        pass


def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (5, [[0, 1, 1], [1, 2, 1], [2, 3, 2], [0, 3, 2], [0, 4, 3], [3, 4, 3], [1, 4, 6]],
         [[0, 1], [2, 3, 4, 5]]),
        (4, [[0, 1, 1], [1, 2, 1], [2, 3, 1], [0, 3, 1]],
         [[], [0, 1, 2, 3]]),
    ]
    for n, edges, want in cases:
        got = sol.findCriticalAndPseudoCriticalEdges(n, [e[:] for e in edges])
        ok = (got is not None and len(got) == 2
              and [sorted(got[0]), sorted(got[1])] == [sorted(want[0]), sorted(want[1])])
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}  -> {got}  (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
