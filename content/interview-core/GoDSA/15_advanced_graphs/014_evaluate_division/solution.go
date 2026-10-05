package main

import "fmt"

/*
================================================================================
LeetCode 399 · Evaluate Division                                        [Medium]
https://leetcode.com/problems/evaluate-division/
Topic: 15 · Advanced Graphs
================================================================================

PROBLEM
-------
You are given an array of variable pairs `equations` and an array of real
numbers `values`, where equations[i] = [Ai, Bi] and values[i] represent the
equation Ai / Bi = values[i]. Each Ai or Bi is a string naming a variable.

You are also given `queries` where queries[j] = [Cj, Dj] asks for Cj / Dj.

Return the answers to all queries. If a single answer cannot be determined,
return -1.0.

The input is always valid: no division by zero and no contradictions.
A variable that does not appear in any equation is UNDEFINED, so even x / x is
-1.0 for such a variable.


EXAMPLES
--------
Example 1:
    Input:  equations = [["a","b"],["b","c"]], values = [2.0, 3.0]
            queries = [["a","c"],["b","a"],["a","e"],["a","a"],["x","x"]]
    Output: [6.0, 0.5, -1.0, 1.0, -1.0]
    Explanation: a/b = 2, b/c = 3 -> a/c = 6, b/a = 0.5.
                 e and x are undefined -> -1.0.

Example 2:
    Input:  equations = [["a","b"],["b","c"],["bc","cd"]], values = [1.5,2.5,5.0]
            queries = [["a","c"],["c","b"],["bc","cd"],["cd","bc"]]
    Output: [3.75, 0.4, 5.0, 0.2]


CONSTRAINTS
-----------
    1 <= equations.length <= 20
    equations[i].length == 2, 1 <= Ai.length, Bi.length <= 5
    values.length == equations.length, 0.0 < values[i] <= 20.0
    1 <= queries.length <= 20
    Ai, Bi, Cj, Dj consist of lowercase English letters and digits.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Turn equations into a WEIGHTED DIRECTED GRAPH:

    a / b = 2   ->   edge a -> b with weight 2, and edge b -> a with weight 1/2

Then a / c is the PRODUCT of weights along any path from a to c:

    a --2--> b --3--> c        a / c = 2 * 3 = 6

Because the input has no contradictions, every path between two nodes gives
the same product, so any path works. No path means different components, so
the ratio is unknown: -1.0.


WHAT TO THINK ABOUT
--------------------
1. Why do you need the reverse edge with weight 1 / value?

2. With at most 20 equations and 20 queries, is a DFS per query fast enough?

3. What should x / x return when x appeared in an equation? When it didn't?

4. Could Union-Find store "my value relative to my root" as a weight?


PROGRESSIVE HINTS
------------------
Hint 1: graph[a].append((b, v)); graph[b].append((a, 1 / v)).

Hint 2: For each query (c, d): if either is not in graph, -1.0. Otherwise
        DFS/BFS from c multiplying weights until you reach d.

Hint 3: Keep a visited set per query to avoid cycling.


COMPLEXITY TARGET
------------------
    Time:  O(Q * (V + E))
    Space: O(V + E)
================================================================================
*/

func main() {
	fmt.Println("Solution for Evaluate Division not implemented yet")
}
