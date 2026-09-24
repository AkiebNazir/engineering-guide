package main

/*
================================================================================
QUESTION · LeetCode 684 · Redundant Connection                       [Medium]
https://leetcode.com/problems/redundant-connection/
================================================================================

PROBLEM
-------
In this problem, a tree is an undirected graph that is connected and has no
cycles.

You are given a graph that started as a tree with `n` nodes labeled `1` to
`n`, with one additional edge added. The added edge has two different
vertices chosen from `1` to `n`, and was not an edge that already existed.
The graph is represented as an array `edges` of length `n` where
`edges[i] = [ai, bi]` indicates that there is an edge between nodes `ai` and
`bi` in the graph.

Return an edge that can be removed so that the resulting graph is a tree of
`n` nodes. If there are multiple answers, return the answer that occurs
LAST in the input.


EXAMPLES
--------
Example 1:
    Input:  edges = [[1,2],[1,3],[2,3]]
    Output: [2,3]

        1           1
       / \\           \\
      2   3    -->     2---3   (removing [2,3] restores a tree)
       \\ /
        (2-3 closes the cycle)

    Adding edges one at a time:
        [1,2] -> tree so far: 1-2
        [1,3] -> tree so far: 1-2, 1-3          (still a tree)
        [2,3] -> 2 and 3 are ALREADY connected (via 1) -> this edge is redundant

Example 2:
    Input:  edges = [[1,2],[2,3],[3,4],[1,4],[1,5]]
    Output: [1,4]

        1---2
        |   |
        5   3
         \\  |
          (4)-- 4 connects back to 1, closing the 1-2-3-4 cycle

    Adding one at a time:
        [1,2] -> ok          [2,3] -> ok          [3,4] -> ok
        [1,4] -> 1 and 4 already connected (1-2-3-4) -> redundant
        [1,5] -> never reached, but by then we already found the answer


CONSTRAINTS
-----------
    n == edges.length
    3 <= n <= 1000
    edges[i].length == 2
    1 <= ai < bi <= edges.length
    ai != bi
    There are no repeated edges.
    The given graph is connected.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A tree with `n` nodes has exactly `n-1` edges and no cycles. This input has
`n` edges — exactly one too many — which means exactly one edge closes a
cycle. That edge is "redundant": removing it restores a tree.

The key reframe: **process edges in input order, adding each one to a
graph you're building incrementally.** Before adding edge (u, v), check
whether u and v are ALREADY connected by some path using the edges added
so far. If they are, this new edge doesn't connect anything new — it closes
a cycle, and it's a valid answer. Because you must return the cycle-closing
edge that occurs LAST if there are multiple candidates, and a graph built
from a spanning tree plus exactly one extra edge has exactly ONE such edge,
this stop-at-the-first-hit approach is also naturally correct: there is only
one edge in the whole list whose endpoints are already connected at the
moment it's processed.

NOTE ON UNION-FIND: this topic's guide (see _TOPIC_GUIDE.md, Part 11) is
explicit that Union-Find / Disjoint Set Union is topic 15's subject
(Advanced Graphs), not this one. Solve this problem with plain DFS/BFS
"are these two nodes already connected?" checks — do not implement a DSU
class here, even as a bonus/alternate approach.


PROGRESSIVE HINTS
------------------
Hint 1: Process `edges` in order. Maintain an adjacency list of only the
        edges added SO FAR.

Hint 2: Before adding edge (u, v), ask: "using only the edges already in my
        graph, can I already reach v starting from u?" That's a single
        DFS/BFS reachability check (topic guide Part 2/3).

Hint 3: If u and v are already connected, do NOT add this edge — return it
        immediately. Since exactly one edge in the input is the "extra"
        one, and you check in input order, the first edge you find whose
        endpoints are already connected IS the one to return (and it is
        also the last-occurring valid answer, since it's unique).


COMPLEXITY TARGET
------------------
    Time:  O(E * (V + E)) — a full traversal per edge, in the worst case
    Space: O(V + E)

    (Union-Find would get this to near O(E * alpha(V)) ~ O(E) — that's
    topic 15's territory, not this one.)
================================================================================
*/

// TODO: Implement the stub
