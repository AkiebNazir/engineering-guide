package main

/*
================================================================================
QUESTION · LeetCode 1462 · Course Schedule IV                        [Medium]
https://leetcode.com/problems/course-schedule-iv/
================================================================================

PROBLEM
-------
There are a total of numCourses courses you have to take, labeled from 0 to
numCourses - 1. You are given an array prerequisites where
prerequisites[i] = [ai, bi] indicates that you must first take course ai
before taking course bi.

Note that if course a is a prerequisite of course b, and course b is a
prerequisite of course c, then course a is a prerequisite of course c
(prerequisites are TRANSITIVE).

You are also given an array queries where queries[j] = [uj, vj]. For the
jth query, you should answer whether course uj is a prerequisite of course
vj or not.

Return a boolean array `answer`, where answer[j] is the answer to the jth
query.


EXAMPLES
--------
Example 1:
    Input:  numCourses = 2, prerequisites = [[1,0]],
            queries = [[0,1],[1,0]]
    Output: [false, true]
    Explanation: course 0 is not a prerequisite of course 1, but the
    opposite is true.

Example 2:
    Input:  numCourses = 2, prerequisites = [],
            queries = [[1,0],[0,1]]
    Output: [false, false]
    Explanation: There are no prerequisites, so no answer is "true".

Example 3:
    Input:  numCourses = 3, prerequisites = [[1,2],[1,0],[2,0]],
            queries = [[1,0],[1,2]]
    Output: [true, true]


CONSTRAINTS
-----------
    2 <= numCourses <= 100
    0 <= prerequisites.length <= (numCourses * (numCourses - 1) / 2)
    prerequisites[i].length == 2
    0 <= ai, bi <= numCourses - 1
    ai != bi
    All the pairs [ai, bi] are unique.
    The prerequisites graph has no cycles.
    1 <= queries.length <= 10^4
    0 <= ui, vi <= numCourses - 1
    ui != vi


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Is a a (possibly INDIRECT) prerequisite of b" is exactly reachability in
a DAG, with the wrinkle that prerequisites are explicitly TRANSITIVE. With
numCourses <= 100 and up to 10^4 queries, precomputing ALL-PAIRS
reachability once and answering each query in O(1) beats re-running a
traversal per query. Two ways to build that all-pairs table:

    1. Floyd-Warshall-style transitive closure: reach[i][j] |= reach[i][k]
       and reach[k][j], for every intermediate k -- O(V^3).
    2. V independent BFS/DFS runs, one per starting course, each marking
       every course reachable from it -- O(V * (V + E)).

Both fit comfortably at V <= 100.

PROGRESSIVE HINTS
------------------
Hint 1: Build reach[i][j] = "is j reachable from i" for all pairs, ONCE,
        before answering any query.
Hint 2: Floyd-Warshall's inner loop order matters: k (intermediate) must
        be the OUTERMOST loop, or the closure is computed incorrectly.
Hint 3: Initialize reach[a][b] = True for every direct prerequisite edge
        (a,b) first.
Hint 4: Each query is then just an O(1) lookup: reach[u][v].

COMPLEXITY TARGET
------------------
    Time:  O(V^3 + Q)
    Space: O(V^2)
================================================================================
*/

// TODO: Implement the stub
