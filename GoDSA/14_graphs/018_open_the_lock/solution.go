package main

import "fmt"

/*
================================================================================
LeetCode 752 · Open the Lock                                            [Medium]
https://leetcode.com/problems/open-the-lock/
Topic: 14 · Graphs
================================================================================

PROBLEM
-------
You have a lock with 4 circular wheels. Each wheel has the digits '0' to '9'
and can turn freely and wrap around: '9' turns to '0' and '0' turns to '9'.
Each MOVE turns one wheel by one slot.

The lock starts at "0000". You are given a list of `deadends`: if the lock
ever displays one of these codes, the wheels stop turning and you can't open
it.

Given a `target`, return the minimum number of moves required to open the
lock, or -1 if it is impossible.


EXAMPLES
--------
Example 1:
    Input:  deadends = ["0201","0101","0102","1212","2002"], target = "0202"
    Output: 6
    Explanation: 0000 -> 1000 -> 1100 -> 1200 -> 1201 -> 1202 -> 0202.
                 The shorter 0000 -> 0001 -> 0002 -> 0102 -> 0202 passes
                 through the deadend 0102.

Example 2:
    Input:  deadends = ["8888"], target = "0009"
    Output: 1   (turn the last wheel backwards: 0 -> 9)

Example 3:
    Input:  deadends = ["8887","8889","8878","8898","8788","8988","7888","9888"],
            target = "8888"
    Output: -1  (every neighbor of the target is a deadend)


CONSTRAINTS
-----------
    1 <= deadends.length <= 500
    deadends[i].length == 4, target.length == 4
    target will not be in the list deadends.
    target and deadends[i] consist of digits only.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Nothing here looks like a graph, which is the point. Google likes these.

    NODES   the 10,000 possible codes "0000".."9999"
    EDGES   one move: any of 4 wheels, +1 or -1 -> 8 neighbors per code
    BLOCKED the deadends (you may not step on them)
    WANT    the fewest edges from "0000" to target

Unweighted shortest path = BFS. The graph is IMPLICIT: you never build it,
you generate a node's 8 neighbors when you visit it.


WHAT TO THINK ABOUT
--------------------
1. What if "0000" itself is a deadend?

2. Mark codes as visited when you ENQUEUE them or when you DEQUEUE them? Does
   it change the answer, the work done, or both?

3. You know both the start and the target. Can you search from both ends?


PROGRESSIVE HINTS
------------------
Hint 1: seen = set(deadends). If "0000" in seen, return -1.

Hint 2: BFS level by level from "0000". For each code, generate 8 neighbors
        with (digit ± 1) % 10.

Hint 3: Return the level at which you dequeue target.


COMPLEXITY TARGET
------------------
    Time:  O(10^4 * 8 * 4) — every code, every neighbor, building a 4-char string
    Space: O(10^4)
================================================================================
*/

func main() {
	fmt.Println("Solution for Open the Lock not implemented yet")
}
