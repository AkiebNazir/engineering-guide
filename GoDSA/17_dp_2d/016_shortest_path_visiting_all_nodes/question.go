package main

/*
================================================================================
LeetCode 847 · Shortest Path Visiting All Nodes                           [Hard]
https://leetcode.com/problems/shortest-path-visiting-all-nodes/
Topic: 17 · Dynamic Programming (2D)
================================================================================

PROBLEM
-------
You have an undirected, connected graph of n nodes labeled 0..n-1. You are
given `graph` where graph[i] is a list of all the nodes connected with node i.

Return the length of the shortest path that visits every node. You may start
and stop at any node, you may revisit nodes multiple times, and you may reuse
edges.


EXAMPLES
--------
Example 1:
    Input:  graph = [[1,2,3],[0],[0],[0]]
    Output: 4
    Explanation: one possible path is [1,0,2,0,3].

            1
            │
        2 ─ 0 ─ 3

Example 2:
    Input:  graph = [[1],[0,2,4],[1,3,4],[2],[1,2]]
    Output: 4
    Explanation: one possible path is [0,1,4,2,3].


CONSTRAINTS
-----------
    n == graph.length
    1 <= n <= 12
    0 <= graph[i].length < n
    graph[i] does not contain i.
    If graph[a] contains b, then graph[b] contains a.
    The input graph is always connected.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
n <= 12 is a loud hint: 2^12 = 4096. Bitmask state.

Plain BFS over nodes doesn't work, because revisiting a node is allowed and
often necessary (Example 1 goes back through 0 twice). Being at node 0 having
visited {1} is a different situation from being at node 0 having visited
{1, 2}. So the STATE must include what you've visited:

    state = (current node, mask of visited nodes)       12 * 4096 = 49,152 states

Every move costs 1, so BFS over these states finds the shortest path. Start
from ALL nodes at once (multi-source BFS), since you may start anywhere. The
first time you reach any state whose mask has all n bits set, you're done.

This is a relative of the Traveling Salesman Problem, made tractable by the
tiny n.


WHAT TO THINK ABOUT
--------------------
1. Why can't `visited` be a set of nodes? What goes wrong?

2. Start state for node i: (i, 1 << i). What's the goal mask?

3. How big is the state space, and is BFS over it fast enough?

4. Alternative: all-pairs shortest distances, then DP over (mask, last node).


PROGRESSIVE HINTS
------------------
Hint 1: goal = (1 << n) - 1. If n == 1, return 0.

Hint 2: queue = [(i, 1 << i) for i in range(n)], seen = set of those states.

Hint 3: BFS level by level. For (u, mask), each neighbor v gives
        (v, mask | 1 << v). Return the level when a new mask == goal.


COMPLEXITY TARGET
------------------
    Time:  O(2^n * n^2)   (states * edges per node)
    Space: O(2^n * n)
================================================================================
*/

// TODO: Implement the stub
