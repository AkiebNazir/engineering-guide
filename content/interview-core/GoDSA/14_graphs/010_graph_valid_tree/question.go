package main

/*
================================================================================
QUESTION · LeetCode 261 · Graph Valid Tree                           [Medium]
https://leetcode.com/problems/graph-valid-tree/
(Premium/locked on LeetCode — still a standard, frequently-asked interview
 question; write and solve it fully like any other problem in this folder.)
================================================================================

PROBLEM
-------
You have a graph of `n` nodes labeled `0` to `n - 1`. You are given an
integer `n` and a list of `edges` where `edges[i] = [ai, bi]` indicates that
there is an UNDIRECTED edge between nodes `ai` and `bi` in the graph.

Return `true` if the edges of the given graph make up a valid TREE, and
`false` otherwise.


WHAT MAKES A GRAPH A "TREE"
----------------------------
A tree, here, means: connected (every node reachable from every other node)
AND acyclic (no cycles). Equivalently — and this is the operational
definition you will actually use — a graph with n nodes is a valid tree if
and only if BOTH of these hold:

    1. It has EXACTLY n - 1 edges.
    2. It is fully connected (exactly ONE connected component).

Neither condition alone is sufficient. See EXAMPLES below for a graph that
satisfies each one individually while still failing to be a tree.


EXAMPLES
--------
Example 1:
    Input:  n = 5, edges = [[0,1],[0,2],[0,3],[1,4]]
    Output: true

            0
           /|\
          1 2 3
          |
          4

        4 edges, n-1 = 4 ✅. One component ✅. Valid tree.

Example 2:
    Input:  n = 5, edges = [[0,1],[1,2],[2,3],[1,3],[1,4]]
    Output: false

            0     4
             \   /
              1
             /|
            2 |
             \|
              3

        5 edges but n-1 = 4 — one edge TOO MANY. Nodes 1,2,3 form a
        triangle (a cycle), so this fails the tree definition even though
        every node IS reachable from every other node (it's connected).

Example 3 — edge count alone is NOT enough (the trap this problem tests):
    Input:  n = 5, edges = [[0,1],[2,3],[3,4],[2,4]]
    Output: false

        0 --- 1        2 --- 3
                         \   /
                          \ /
                           4

        4 edges, n-1 = 4 ✅ — the edge COUNT matches a tree's. But this is
        TWO components: {0,1} (a valid little tree) and {2,3,4} (a
        triangle — a cycle, not a tree), and 2 components != 1. A cycle in
        one part of the graph and a missing edge in another part CANCEL OUT
        in the total edge count, so counting edges alone proves nothing —
        you must also check connectivity.


CONSTRAINTS
-----------
    1 <= n <= 2000
    0 <= edges.length <= 5000
    edges[i].length == 2
    0 <= ai, bi < n
    ai != bi
    There are no self-loops or repeated edges.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is Part 3 (connected components) of the topic guide, plus one counting
check, glued together by a graph-theory fact worth knowing cold: **any
connected undirected graph on n nodes has AT LEAST n-1 edges, and it has
EXACTLY n-1 edges if and only if it has no cycles.** A connected graph with
n-1 edges is, by definition, a tree. A connected graph with MORE than n-1
edges must contain a cycle (there's "extra" connectivity somewhere). A graph
with FEWER than n-1 edges cannot possibly be connected (too few edges to
reach every node).

So the fast check is: count the edges. If `len(edges) != n - 1`, you can
return `false` immediately, no traversal needed. If it DOES equal `n - 1`,
that alone still isn't proof — Example 3 above shows a graph with exactly
n-1 edges that is disconnected (a cycle in one piece "pays for" a missing
edge in another piece). You still have to run one connectivity check
(exactly problem 009's algorithm) to be sure there's only ONE component.


PROGRESSIVE HINTS
------------------
Hint 1: What is the minimum number of edges required to connect n nodes
        into one piece? What happens to that count the moment ANY cycle
        exists?

Hint 2: Check `len(edges) == n - 1` first — it's O(1) and eliminates most
        invalid inputs without any traversal at all.

Hint 3: A graph can have exactly n-1 edges and still not be a tree (a cycle
        in one component, canceled out by a missing edge in another). The
        edge-count check is necessary but NOT sufficient — you still need
        to confirm the graph is a single connected component (problem 009's
        algorithm, reused here).


COMPLEXITY TARGET
------------------
    Time:  O(V + E)
    Space: O(V + E)
================================================================================
*/

// TODO: Implement the stub
