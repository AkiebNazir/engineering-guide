package main

/*
================================================================================
LeetCode 218 · The Skyline Problem                                        [Hard]
https://leetcode.com/problems/the-skyline-problem/
Topic: 26 · Segment Tree & Fenwick (BIT)
================================================================================

PROBLEM
-------
A city's skyline is the outer contour of the silhouette formed by all the
buildings in that city when viewed from a distance.

You are given `buildings` where `buildings[i] = [left_i, right_i, height_i]`:

    left_i    the X coordinate of the left edge of the i-th building
    right_i   the X coordinate of the right edge of the i-th building
    height_i  the height of the i-th building

All buildings sit on a flat ground with height 0.

Return the skyline as a list of "key points" `[[x1, y1], [x2, y2], ...]`,
sorted by x-coordinate, that uniquely define it. A key point is the LEFT
endpoint of a horizontal line segment in the final skyline outline (the
last key point always has a y-coordinate of 0 and marks the skyline's
right-most extent). No two consecutive key points may have the same
x-coordinate, and no two consecutive key points may have the same
y-coordinate (except the required last one).


EXAMPLES
--------
Example 1:
    Input:  buildings = [[2,9,10],[3,7,15],[5,12,12],[15,20,10],[19,24,8]]
    Output: [[2,10],[3,15],[7,12],[12,0],[15,10],[20,8],[24,0]]
    Explanation:
        Building A: x in [2,9), height 10
        Building B: x in [3,7), height 15
        Building C: x in [5,12), height 12
        Building D: x in [15,20), height 10
        Building E: x in [19,24), height 8

        At x=2, building A appears -> height jumps to 10.
        At x=3, building B (taller) appears -> height jumps to 15.
        At x=7, building B ends; the tallest remaining covering x=7 is C
            (height 12) -> height drops to 12.
        At x=12, building C ends and nothing covers x=12 -> height drops
            to 0.
        At x=15, building D appears -> height jumps to 10.
        At x=19, building E appears but D (height 10) still covers x=19
            and is taller than E (height 8), so no visible change yet...
            (verified: no key point emitted at x=19, since max height at
            19 is still 10, same as the previous key point).
        At x=20, building D ends; only E remains -> height drops to 8.
        At x=24, building E ends; nothing remains -> height drops to 0.

Example 2:
    Input:  buildings = [[0,2,3],[2,5,3]]
    Output: [[0,3],[5,0]]
    Explanation: Two adjacent buildings of the SAME height with no gap
        between them merge into one continuous segment in the skyline —
        no key point is emitted at x=2 since the height doesn't change
        there.


CONSTRAINTS
-----------
    1 <= buildings.length <= 10^4
    0 <= left_i < right_i <= 2^31 - 1
    1 <= height_i <= 2^31 - 1
    `buildings` is sorted by left_i in non-decreasing order.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
The skyline's height can only CHANGE at a building's left or right edge —
nowhere else. That means the entire problem reduces to a SWEEP over the
sorted set of critical x-coordinates (every building's left and right
edge), asking at each one: "what's the tallest building currently alive
(covering this x)?" — and emitting a key point only when that answer
differs from the previous one.

"Currently alive" naturally suggests a max-heap of active building
heights, each tagged with when it expires (its right edge) — push a
building's height when its left edge is reached, and lazily discard
heights from the top of the heap once their building has expired (its
right edge is `<=` the current sweep position). This is the same
event-driven "process critical points left to right, maintain a running
best-so-far" shape as topic 06's monotonic-stack problems and topic 19's
interval-merging — just with a heap instead of a stack, because "the
tallest CURRENTLY ALIVE building" isn't monotone the way a stack invariant
would need.

A coordinate-compressed segment tree with lazy range-max updates (topic
guide Part 1, same tool as 005 Falling Squares) is a fully valid
alternative: assign each building's height across `[left, right)` on the
compressed axis, then read off the height at every compressed boundary
point to build the key-point list. Heavier machinery for the same result —
the sweep-line + heap approach below is the cleaner one to trace by hand.


WHAT TO THINK ABOUT
--------------------
1. Collect ALL left and right edges into one sorted list of critical
   x-coordinates — process them left to right, one x at a time.

2. At each critical x: first push every building whose LEFT edge equals
   this x (they start being "alive" here), THEN pop every heap-top entry
   whose RIGHT edge is `<= x` (they've expired) — order matters only in
   that both must be resolved before reading "the current max," not in
   which happens first, since a freshly-pushed building's own right edge
   is always `> x`.

3. After resolving pushes/pops for this x, the current max height (0 if
   the heap is empty) is this x's true height. Only emit a key point
   `[x, height]` if it DIFFERS from the last emitted key point's height.

4. Two buildings of the same height directly adjacent (Example 2) must NOT
   produce a key point at their shared boundary — the "differs from
   previous" check handles this automatically as long as the sweep visits
   every critical x, including ones where nothing actually changes.


PROGRESSIVE HINTS
------------------
Hint 1: Group buildings by their LEFT edge first, so at each critical x you
        can push every building starting there in one step, before
        checking what's expired.

Hint 2: A python `heapq` is a MIN-heap — store `(-height, right_edge)` so
        the largest height sorts first (most negative first).

Hint 3: Lazy deletion: don't try to remove an EXPIRED building from the
        middle of the heap — just check-and-pop from the TOP whenever its
        right edge is `<=` the current x, repeating until the top is
        valid (or the heap is empty).


COMPLEXITY TARGET
------------------
    Time:  O(n log n)
    Space: O(n)
================================================================================
*/

// TODO: Implement the stub
