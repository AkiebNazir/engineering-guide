package main

/*
================================================================================
QUESTION · LeetCode 1584 · Min Cost to Connect All Points             [Medium]
https://leetcode.com/problems/min-cost-to-connect-all-points/
================================================================================

PROBLEM
-------
You are given an array points representing integer coordinates of some
points on a 2D-plane, where points[i] = [xi, yi].

The cost of connecting two points [xi, yi] and [xj, yj] is the manhattan
distance between them: |xi - xj| + |yi - yj|.

Return the minimum cost to make all points connected. All points are
connected if there is exactly one simple path between any two points.


EXAMPLES
--------
Example 1:
    Input:  points = [[0,0],[2,2],[3,10],[5,2],[7,0]]
    Output: 20

Example 2:
    Input:  points = [[3,12],[-2,5],[-4,1]]
    Output: 18


CONSTRAINTS
-----------
    1 <= points.length <= 1000
    -10^6 <= xi, yi <= 10^6
    All pairs (xi, yi) are distinct.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Connect all points as cheaply as possible, exactly one simple path between
any two" is the textbook definition of a MINIMUM SPANNING TREE: connect all
n nodes using exactly n-1 edges, minimizing total edge weight, no cycles.

Every pair of points is an implicit edge (the graph is COMPLETE -- n points
means C(n,2) possible edges) with weight = Manhattan distance. This is
DENSE (E = O(n^2)), which per the topic guide Part 4 favors Prim's over
Kruskal's: building and sorting O(n^2) edges for Kruskal's costs more than
Prim's array-based O(n^2) approach, which never needs to materialize the
edge list at all.

PROGRESSIVE HINTS
------------------
Hint 1: This is MST. n <= 1000 means up to ~500,000 implicit edges --
        think about whether you actually need to construct them all.
Hint 2: Prim's grows a tree from one starting point, always adding the
        cheapest edge crossing the frontier (in-tree <-> not-yet-in-tree).
Hint 3: With a dense graph, maintain min_dist[j] = cheapest known edge
        from ANY in-tree point to point j, and update it in O(n) each
        round instead of pushing into a heap -- O(n^2) total, no log factor.
Hint 4: Manhattan distance: |x1-x2| + |y1-y2|.

COMPLEXITY TARGET
------------------
    Time:  O(n^2) -- array-based Prim's, appropriate for a dense/complete graph
    Space: O(n)
================================================================================
*/

// TODO: Implement the stub
