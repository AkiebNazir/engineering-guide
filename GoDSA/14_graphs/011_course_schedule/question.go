package main

/*
================================================================================
QUESTION · LeetCode 207 · Course Schedule                            [Medium]
https://leetcode.com/problems/course-schedule/
================================================================================

PROBLEM
-------
There are a total of `numCourses` courses you have to take, labeled from `0`
to `numCourses - 1`. You are given an array `prerequisites` where
`prerequisites[i] = [ai, bi]` indicates that you MUST take course `bi`
FIRST if you want to take course `ai`.

    e.g. the pair [0, 1] means: to take course 0 you must first take
    course 1.

Return `true` if you can finish ALL courses. Otherwise, return `false`.


EXAMPLES
--------
Example 1:
    Input:  numCourses = 2, prerequisites = [[1,0]]
    Output: true

        0 ---> 1        (take 0, then 1 — no conflict)

Example 2:
    Input:  numCourses = 2, prerequisites = [[1,0],[0,1]]
    Output: false

        0 ---> 1
        ^      |
        |______|

        0 needs 1 first, but 1 needs 0 first — a two-node CYCLE. Neither
        course can ever be first, so neither can ever be taken.

Example 3 — the trap this problem is built to test (topic guide §4.2):
    Input:  numCourses = 4,
            prerequisites = [[1,0],[2,0],[3,1],[3,2]]
    Output: true

               0
              / \
             1   2
              \ /
               3

        0 -> 1, 0 -> 2, 1 -> 3, 2 -> 3.  Node 3 is reached via TWO
        different paths (0->1->3 and 0->2->3) — that is NOT a cycle, it's
        a shared dependency (a "diamond"). A naive "have I visited this
        node before" check would wrongly flag this as a cycle the second
        time it reaches node 3. See the solution file's live demo.


CONSTRAINTS
-----------
    1 <= numCourses <= 2000
    0 <= prerequisites.length <= 5000
    prerequisites[i].length == 2
    0 <= ai, bi < numCourses
    All the pairs prerequisites[i] are UNIQUE.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Model each course as a node, and each prerequisite pair `[a, b]` ("a needs b
first") as a DIRECTED edge `b -> a` ("b must come before a"). "Can you
finish all courses" is then exactly the question topic guide §4.3 poses:
**a valid order to take all courses exists if and only if this directed
graph is acyclic (a DAG).** If there's a cycle anywhere — course X needs Y,
which (through some chain) eventually needs X again — then every course on
that cycle is stuck waiting for a course that is itself waiting on it, and
none of them can ever be first.

So the whole problem reduces to: **directed cycle detection.** Topic guide
Part 4 is explicit that this needs a DIFFERENT technique than undirected
cycle detection — a single `visited` set gives FALSE POSITIVES on a
directed graph the moment two different paths lead to the same downstream
node (Example 3 above), because "I've seen this node before" doesn't
distinguish "it's still on my current path" (a real cycle) from "it's a
shared descendant I already fully explored" (not a cycle at all). The fix
is 3-color DFS (WHITE/GRAY/BLACK) — or, equivalently, Kahn's BFS-based
topological sort, which sidesteps the coloring question entirely by only
processing nodes whose prerequisites are ALL satisfied.


PROGRESSIVE HINTS
------------------
Hint 1: Build a directed adjacency list from `prerequisites`: for each
        `[a, b]`, add an edge `b -> a` (b before a). This is NOT
        symmetric like problems 009/010 — do not add both directions.

Hint 2: "Can all courses be finished" is the same question as "does this
        directed graph have a cycle" (topic guide §4.3). A single
        `visited` set is NOT enough to detect a directed cycle correctly —
        think about what distinguishes "currently on my path" from
        "already fully explored and safe."

Hint 3: Two techniques both work: (a) 3-color DFS — WHITE/GRAY/BLACK,
        cycle iff you reach a GRAY node (topic guide §4.2); or (b) Kahn's
        algorithm — repeatedly take courses with zero remaining
        prerequisites; if you can't process all `numCourses` this way,
        a cycle blocked the rest (topic guide §5.1). Try both.


COMPLEXITY TARGET
------------------
    Time:  O(V + E)  where V = numCourses, E = len(prerequisites)
    Space: O(V + E)
================================================================================
*/

// TODO: Implement the stub
