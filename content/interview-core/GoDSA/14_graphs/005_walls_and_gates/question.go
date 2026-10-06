package main

/*
================================================================================
QUESTION · LeetCode 286 · Walls and Gates                          [Medium]
https://leetcode.com/problems/walls-and-gates/  (premium/locked — standard
interview problem regardless, written here at full depth)
================================================================================

PROBLEM
-------
You are given an `m x n` grid `rooms`. Each cell holds one of three values:

    -1              a WALL or an obstacle — cannot be walked through
     0              a GATE
     2147483647     INF — an empty room (2^31 - 1, used as "infinity")

Fill each empty room with the distance to its NEAREST gate. If a room cannot
reach any gate, it should remain `INF`.

Modify `rooms` IN PLACE. Return nothing.


EXAMPLES
--------
Example 1:
    Input:
        INF  -1   0  INF
        INF INF INF   -1
        INF  -1 INF   -1
          0  -1 INF INF

    Output:
          3  -1   0   1
          2   2   1   -1
          1  -1   2   -1
          0  -1   3   4

        Grid legend:  INF = empty room, -1 = wall, 0 = gate.
        Every INF cell above became the walking distance (up/down/left/right,
        no diagonals) to the CLOSEST 0, walls block movement entirely.

Example 2:
    Input:  [[-1]]
    Output: [[-1]]                (single wall, nothing to fill)

Example 3:
    Input:  [[0]]
    Output: [[0]]                 (single gate, nothing to fill)


CONSTRAINTS
-----------
    m == rooms.length
    n == rooms[i].length
    1 <= m, n <= 250
    rooms[i][j] is -1, 0, or 2^31 - 1


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
"Distance to the NEAREST of several targets, unweighted grid" is the classic
signature of MULTI-SOURCE BFS (topic guide §6.3): instead of running BFS once
per gate and taking the min per cell, seed a single BFS queue with EVERY gate
at distance 0 simultaneously. Because BFS explores in strictly increasing
distance order, the first time any cell is reached, it is being reached by
its closest gate — full stop. There is no case where visiting it again later
finds something better, so cells are marked visited (their INF overwritten)
on first arrival and never revisited.

Walls simply block movement, same as any other grid problem — a wall is
never enqueued and its neighbors don't get to go THROUGH it.


PROGRESSIVE HINTS
------------------
Hint 1: This is exactly the grid-as-graph pattern from Part 6 of the topic
        guide, except with more than one starting node. What if the BFS
        queue started with ALL the gates already in it, each at distance 0?

Hint 2: You do not need a separate `visited` set here — `rooms[r][c]` IS the
        distance once written, and INF is the "not yet visited" marker. Once
        you overwrite a cell with a real distance, never enqueue it again
        (check `rooms[nr][nc] == INF` before pushing).

Hint 3: Walls (-1) and already-gates (0) should never be pushed onto the
        queue as starting points other than the gates themselves — a wall is
        not walkable, and a gate's distance to itself is fixed at 0 already.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — every empty room is enqueued and dequeued once
    Space: O(rows * cols) — the BFS queue in the worst case (all gates, or
                             one giant open room)
================================================================================
*/

// TODO: Implement the stub
