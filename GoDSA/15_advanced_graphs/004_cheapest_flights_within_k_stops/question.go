package main

/*
================================================================================
QUESTION · LeetCode 787 · Cheapest Flights Within K Stops             [Medium]
https://leetcode.com/problems/cheapest-flights-within-k-stops/
================================================================================

PROBLEM
-------
There are n cities connected by some number of flights. You are given an
array `flights` where flights[i] = [fromi, toi, pricei] indicates that
there is a flight from city fromi to city toi with cost pricei.

You are also given three integers src, dst, and k, return the cheapest
price from src to dst with at most k stops. If there is no such route,
return -1.


EXAMPLES
--------
Example 1:
    Input:  n=4, flights=[[0,1,100],[1,2,100],[2,0,100],[1,3,600],[2,3,200]],
            src=0, dst=3, k=1
    Output: 700
    Explanation: 0 -> 1 -> 3 costs 100+600=700. 0 -> 1 -> 2 -> 3 costs
    100+100+200=400 but uses 2 stops, more than k=1.

Example 2:
    Input:  n=3, flights=[[0,1,100],[1,2,100],[0,2,500]], src=0, dst=2, k=1
    Output: 200

Example 3:
    Input:  n=3, flights=[[0,1,100],[1,2,100],[0,2,500]], src=0, dst=2, k=0
    Output: 500


CONSTRAINTS
-----------
    1 <= n <= 100
    0 <= flights.length <= (n * (n - 1) / 2)
    flights[i].length == 3
    0 <= fromi, toi < n
    fromi != toi
    1 <= pricei <= 10^4
    There will not be any multiple flights between two cities.
    0 <= src, dst, k < n
    src != dst


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"At most k STOPS" means at most k+1 EDGES (a stop is an intermediate city;
0 stops means one direct flight = 1 edge; k stops means up to k+1 edges).
This "bounded number of edges" constraint is exactly what plain Dijkstra
CANNOT express cleanly (see the topic guide Part 2) -- its priority queue
optimizes for globally cheapest cost regardless of hop count, so it can
permanently lock in a cheap-but-too-many-stops path and never revisit a
more-expensive-but-fewer-stops alternative.

Bellman-Ford's round-by-round structure is the natural fit: cap it at k+1
rounds, and use a SNAPSHOT of the distance array each round so that a
relaxation made during round r never leaks into another relaxation within
the SAME round r (which would let one round secretly use more than 1 hop).

PROGRESSIVE HINTS
------------------
Hint 1: k stops = at most k+1 edges. Bellman-Ford relaxes every edge once
        per round; cap it at k+1 rounds.
Hint 2: Within a single round, use a COPY of last round's distances to
        decide what's relaxable -- don't let round r's own updates feed
        into round r's other relaxations, or you'll silently allow more
        than 1 additional edge per round.
Hint 3: Initialize dist[src] = 0, everything else infinity.
Hint 4: The answer is dist[dst] if finite, else -1.

COMPLEXITY TARGET
------------------
    Time:  O(k * E)
    Space: O(V)
================================================================================
*/

// TODO: Implement the stub
