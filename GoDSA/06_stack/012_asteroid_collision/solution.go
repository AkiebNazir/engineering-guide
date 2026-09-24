package main

import "fmt"

/*
================================================================================
LeetCode 735 · Asteroid Collision                                       [Medium]
https://leetcode.com/problems/asteroid-collision/
Topic: 06 · Stack & Monotonic Stack
================================================================================

PROBLEM
-------
We are given an array `asteroids` of integers representing asteroids in a row.
The asteroids are equally spaced.

For each asteroid, the absolute value represents its size, and the sign
represents its direction (positive = moving RIGHT, negative = moving LEFT).
Each asteroid moves at the same speed.

Find the state of the asteroids after all collisions. If two asteroids meet,
the smaller one explodes. If both are the same size, both explode. Two
asteroids moving in the same direction never meet.


EXAMPLES
--------
Example 1:   [5, 10, -5]   ->  [5, 10]    (10 and -5 collide; 10 survives)
Example 2:   [8, -8]       ->  []         (equal size, both explode)
Example 3:   [10, 2, -5]   ->  [10]       (2 and -5 -> -5; 10 and -5 -> 10)
Example 4:   [-2, -1, 1, 2] -> [-2, -1, 1, 2]   (nobody meets)


CONSTRAINTS
-----------
    2 <= asteroids.length <= 10^4
    -1000 <= asteroids[i] <= 1000
    asteroids[i] != 0


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
A collision happens ONLY when a right-mover is to the LEFT of a left-mover:

    →  ←     collide
    ←  →     drift apart forever
    →  →     same direction, never meet
    ←  ←     same direction, never meet

Scan left to right. The survivors so far form a stack. A new LEFT-moving
asteroid can crash into right-movers on top of the stack, one after another,
until it dies, they all die, or it reaches a left-mover (or an empty stack)
and survives.


WHAT TO THINK ABOUT
--------------------
1. Exactly which (top, current) sign combination collides?

2. A single incoming asteroid can destroy several stack entries. How do you
   loop that, and how do you remember whether it survived?

3. What happens on a tie?


PROGRESSIVE HINTS
------------------
Hint 1: For each asteroid a: while stack and a < 0 < stack[-1], resolve.

Hint 2: If stack[-1] < -a: pop and keep looping (a survives so far).
        If stack[-1] == -a: pop and a dies. Stop.
        Otherwise a dies. Stop.

Hint 3: Python's while ... else runs the else only if the loop wasn't broken —
        a clean way to say "push a if it survived."


COMPLEXITY TARGET
------------------
    Time:  O(n) — each asteroid pushed and popped at most once
    Space: O(n)
================================================================================
*/

func main() {
	fmt.Println("Solution for Asteroid Collision not implemented yet")
}
