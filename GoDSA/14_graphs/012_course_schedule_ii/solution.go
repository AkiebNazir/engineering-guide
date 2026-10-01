package main

import "fmt"

/*
================================================================================
QUESTION · LeetCode 210 · Course Schedule II                         [Medium]
https://leetcode.com/problems/course-schedule-ii/
================================================================================

PROBLEM
-------
There are a total of `numCourses` courses you have to take, labeled from `0`
to `numCourses - 1`. You are given an array `prerequisites` where
`prerequisites[i] = [ai, bi]` indicates that you MUST take course `bi`
FIRST if you want to take course `ai`.

    e.g. the pair [0, 1] means: to take course 0 you must first take
    course 1.

Return the ORDERING of courses you should take to finish all courses. If
there are many valid answers, return ANY of them. If it is impossible to
finish all courses, return an EMPTY array.

This is problem 011 (LC 207) with the yes/no answer upgraded to "produce
the actual order."


EXAMPLES
--------
Example 1:
    Input:  numCourses = 2, prerequisites = [[1,0]]
    Output: [0,1]

        0 ---> 1        (must take 0 before 1; [0,1] is the only order)

Example 2:
    Input:  numCourses = 4, prerequisites = [[1,0],[2,0],[3,1],[3,2]]
    Output: [0,1,2,3]   (or [0,2,1,3] — both valid)

               0
              / \
             1   2
              \ /
               3

        0 must come first, 3 must come last; 1 and 2 can go in either
        order relative to each other. Either output is accepted.

Example 3:
    Input:  numCourses = 1, prerequisites = []
    Output: [0]

Example 4 — impossible:
    Input:  numCourses = 2, prerequisites = [[1,0],[0,1]]
    Output: []

        0 ---> 1
        ^      |
        |______|

        A 2-node cycle — no valid order exists, so return [].


CONSTRAINTS
-----------
    1 <= numCourses <= 2000
    0 <= prerequisites.length <= numCourses * (numCourses - 1)
    prerequisites[i].length == 2
    0 <= ai, bi < numCourses
    ai != bi
    All the pairs [ai, bi] are DISTINCT.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is problem 011's directed-cycle-detection question with the output
upgraded from "does a valid order exist" to "produce one" — exactly the
relationship topic guide §4.3 describes between cycle detection and
topological sort: **a directed graph has a valid topological order if and
only if it is a DAG.**

Two ways to actually PRODUCE the order (topic guide Part 5):

    - Kahn's algorithm (BFS on in-degree zero, §5.1): repeatedly take
      courses with zero remaining prerequisites; the order courses are
      DEQUEUED in IS a valid topological order, for free. `len(order) <
      numCourses` means a cycle blocked the rest -> return [].

    - DFS-based (postorder, then reverse, §5.2): a node is only "finished"
      (appended to the result) after ALL of its descendants are finished,
      so the finishing order is the REVERSE of a valid topological order —
      reverse it once at the end. A cycle (reaching a GRAY node) means no
      valid order exists -> return [].

Multiple correct outputs are possible whenever two courses have no
dependency relationship to each other (1 and 2 in Example 2) — the
`run_tests` checker below verifies any candidate order against the
prerequisite constraints directly, rather than comparing to one fixed
"the" answer.


PROGRESSIVE HINTS
------------------
Hint 1: Everything from problem 011 applies unchanged for detecting
        whether an order exists. The new piece is: instead of returning a
        boolean the moment you know the answer, you need to RECORD the
        order as you go.

Hint 2: In Kahn's algorithm, the sequence nodes are POPPED from the queue
        already IS a valid topological order — you don't need to compute
        anything extra, just append each popped node to your result list.

Hint 3: In DFS, the natural recursive finishing order (postorder: append a
        node to the result only after recursing into ALL of its
        neighbors) is the topological order BACKWARDS. Reverse the whole
        list once, at the very end, not per-node.


COMPLEXITY TARGET
------------------
    Time:  O(V + E)
    Space: O(V + E)
================================================================================
*/

func main() {
	fmt.Println("Solution for Course Schedule II not implemented yet")
}
