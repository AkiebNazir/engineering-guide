package main

/*
================================================================================
QUESTION · LeetCode 743 · Network Delay Time                         [Medium]
https://leetcode.com/problems/network-delay-time/
================================================================================

PROBLEM
-------
You are given a network of n nodes, labeled from 1 to n. You are also given
times, a list of travel times as directed edges times[i] = (ui, vi, wi),
where ui is the source node, vi is the target node, and wi is the time it
takes for a signal to travel from source to target.

We will send a signal from a given node k. Return the minimum time it takes
for all the n nodes to receive the signal. If it is impossible for all the
n nodes to receive the signal, return -1.


EXAMPLES
--------
Example 1:
    Input:  times = [[2,1,1],[2,3,1],[3,4,1]], n = 4, k = 2
    Output: 2

Example 2:
    Input:  times = [[1,2,1]], n = 2, k = 1
    Output: 1

Example 3:
    Input:  times = [[1,2,1]], n = 2, k = 2
    Output: -1


CONSTRAINTS
-----------
    1 <= k <= n <= 100
    1 <= times.length <= 6000
    times[i].length == 3
    1 <= ui, vi <= n
    ui != vi
    0 <= wi <= 100
    All the pairs (ui, vi) are unique. (i.e., no multiple edges.)


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Minimum time for the signal to reach ALL nodes" = the maximum of the
shortest-path distances from k to every other node (the whole network is
"informed" only once its SLOWEST-to-reach node has been informed). If any
node is unreachable, the answer is -1.

All weights are non-negative (0 <= wi <= 100) -- textbook Dijkstra.

PROGRESSIVE HINTS
------------------
Hint 1: Build an adjacency list: node -> list of (neighbor, weight).
Hint 2: Run single-source Dijkstra from k with a min-heap of
        (distance, node).
Hint 3: Skip a popped (d, u) if d is already worse than the best known
        dist[u] -- see topic guide Part 1, "stale heap entries."
Hint 4: The answer is max(dist.values()) if every node was reached,
        else -1. Nodes are labeled 1..n, not 0..n-1 -- watch the indexing.

COMPLEXITY TARGET
------------------
    Time:  O((V + E) log V)
    Space: O(V + E)
================================================================================
*/

// TODO: Implement the stub
