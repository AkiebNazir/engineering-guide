"""
================================================================================
QUESTION · LeetCode 323 · Number of Connected Components in an Undirected
                            Graph                                    [Medium]
https://leetcode.com/problems/number-of-connected-components-in-an-undirected-graph/
(Premium/locked on LeetCode — still a standard, frequently-asked interview
 question; write and solve it fully like any other problem in this folder.)
================================================================================

PROBLEM
-------
You have a graph of `n` nodes, labeled `0` to `n - 1`. You are given an
integer `n` and an array `edges` where `edges[i] = [ai, bi]` indicates that
there is an UNDIRECTED edge between nodes `ai` and `bi` in the graph.

Return the number of connected components in the graph.


EXAMPLES
--------
Example 1:
    Input:  n = 5, edges = [[0,1],[1,2],[3,4]]
    Output: 2

        0 --- 1 --- 2          3 --- 4

        Component A: {0,1,2}     Component B: {3,4}

Example 2:
    Input:  n = 5, edges = [[0,1],[1,2],[2,3],[3,4]]
    Output: 1

        0 --- 1 --- 2 --- 3 --- 4      (one chain, one component)

Example 3:
    Input:  n = 4, edges = []
    Output: 4

        0     1     2     3            (no edges at all -> every node is
                                         its own component)


CONSTRAINTS
-----------
    1 <= n <= 2000
    1 <= edges.length <= n * (n - 1) / 2
    edges[i].length == 2
    0 <= ai, bi < n
    ai != bi
    There are no repeated edges.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
You are handed a graph as a raw EDGE LIST — no adjacency structure is built
for you (topic guide Part 1). Step one, always, is to convert that edge list
into an adjacency list: O(E) to build, paid once, amortized over every
traversal that follows.

Once you have the adjacency list, this is Part 3 of the topic guide,
verbatim: "How many separate pieces is this graph in?" Walk the whole graph
starting from node 0. Every node that traversal reaches belongs to ONE
component. Then look for the next node you have NOT yet visited — if one
exists, it must belong to a DIFFERENT component (if it were reachable from
node 0, the first traversal would already have found it), so start a fresh
traversal from it and count one more component. Repeat until every node has
been visited. The number of times you were FORCED to start a fresh traversal
is the answer.

This is exactly the same shape as Number of Islands (002) — the only
difference is the graph arrives as an edge list here instead of being
implicit in a grid.


PROGRESSIVE HINTS
------------------
Hint 1: Build an adjacency list first: `graph = {i: [] for i in range(n)}`,
        then for each `[u, v]` append `v` to `graph[u]` AND `u` to
        `graph[v]` — it's undirected, both directions matter (topic guide
        §Part 10, mistake #7).

Hint 2: Keep one `visited` set across the WHOLE graph, not reset per node.
        Loop `for node in range(n)`: if `node` is not in `visited`, that is
        the start of a brand-new component — increment your counter and run
        a full DFS/BFS from it, marking everything it reaches as visited.

Hint 3: n can be up to 2000, and a graph built from unlucky edges (e.g. all
        edges forming one long chain) can have a traversal path of length n.
        Recursive DFS on such a chain recurses n frames deep — think about
        whether that's safe against Python's default recursion limit, or
        whether you should use an iterative stack / BFS queue instead.


COMPLEXITY TARGET
------------------
    Time:  O(V + E)  — build the adjacency list once (O(E)), then one
                        traversal total across all components (O(V + E))
    Space: O(V + E)  — adjacency list + visited set + stack/queue
================================================================================
"""

from typing import List


class Solution:
    def countComponents(self, n: int, edges: List[List[int]]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 009_number_of_connected_components_in_an_undirected_graph_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    all_ok = True
    cases = [
        (5, [[0, 1], [1, 2], [3, 4]], 2),
        (5, [[0, 1], [1, 2], [2, 3], [3, 4]], 1),
        (4, [], 4),
        (1, [], 1),
        (2, [[0, 1]], 1),
        (6, [[0, 1], [2, 3], [4, 5]], 3),
        (6, [[0, 1], [1, 2], [2, 0], [3, 4]], 3),
    ]
    for n, edges, want in cases:
        got = sol.countComponents(n, [row[:] for row in edges])
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n} edges={edges!r:<32} "
              f"-> {got} (want {want})")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
