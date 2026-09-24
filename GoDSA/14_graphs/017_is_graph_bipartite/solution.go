package main

import "fmt"

/*
================================================================================
LeetCode 785 · Is Graph Bipartite?                                      [Medium]
https://leetcode.com/problems/is-graph-bipartite/
Topic: 14 · Graphs
================================================================================

PROBLEM
-------
There is an UNDIRECTED graph with n nodes numbered 0..n-1. You are given
`graph`, where graph[u] is the list of nodes adjacent to u. There are no
self-edges and no parallel edges; if v is in graph[u], u is in graph[v]. The
graph may be DISCONNECTED.

A graph is bipartite if the nodes can be split into two sets A and B such that
every edge connects a node in A to a node in B.

Return true if and only if the graph is bipartite.


EXAMPLES
--------
Example 1:
    Input:  graph = [[1,2,3],[0,2],[0,1,3],[0,2]]
    Output: false

        0 ─── 1
        │ ╲   │
        │  ╲  │        0-1-2 is a triangle: an odd cycle.
        3 ─── 2

Example 2:
    Input:  graph = [[1,3],[0,2],[1,3],[0,2]]
    Output: true

        0 ─── 1
        │     │        A = {0, 2}, B = {1, 3}
        3 ─── 2


CONSTRAINTS
-----------
    graph.length == n
    1 <= n <= 100
    0 <= graph[u].length < n
    0 <= graph[u][i] <= n - 1
    graph[u] does not contain u; all values in graph[u] are unique.
    If graph[u] contains v, then graph[v] contains u.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Bipartite = 2-colorable: paint every node red or blue so that no edge joins
two nodes of the same color.

Start anywhere, paint it red. Its neighbors are forced to be blue, their
neighbors forced red, and so on. There's never a choice after the first node
of a component, so either the forced coloring works or you find an edge whose
two ends were forced to the same color.

A graph is bipartite exactly when it has NO ODD-LENGTH CYCLE. Going around an
odd cycle flips color an odd number of times and lands on the wrong color.


WHAT TO THINK ABOUT
--------------------
1. BFS or DFS both work. What do you store per node?

2. The graph may be disconnected. What happens if you only start from node 0?

3. Can union-find express "u and every neighbor of u are on opposite sides"?


PROGRESSIVE HINTS
------------------
Hint 1: color = [-1] * n (uncolored).

Hint 2: For every node s still uncolored, color it 0 and BFS. For each edge
        (u, v): if v uncolored, color[v] = 1 - color[u] and enqueue; if
        color[v] == color[u], return False.

Hint 3: Return True after all components pass.


COMPLEXITY TARGET
------------------
    Time:  O(V + E)
    Space: O(V)
================================================================================
*/

func main() {
	fmt.Println("Solution for Is Graph Bipartite? not implemented yet")
}
