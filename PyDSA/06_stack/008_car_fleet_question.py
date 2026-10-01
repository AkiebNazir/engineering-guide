"""
================================================================================
LeetCode 853 · Car Fleet                                               [Medium]
https://leetcode.com/problems/car-fleet/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
There are `n` cars at given miles away from the starting mile 0, travelling
to reach the mile `target`.

You are given two integer arrays `position` and `speed`, both of length
`n`, where `position[i]` is the starting mile of the i-th car and
`speed[i]` is the speed of the i-th car in miles per hour.

A car cannot pass another car, but it can catch up and then travel next to
it at the speed of the slower car.

A CAR FLEET is a car or cars driving next to each other. The speed of the
car fleet is the MINIMUM speed of any car in the fleet.

If a car catches up to a car fleet at the mile `target`, it will still be
considered as one car fleet.

Return the number of car fleets that will arrive at the destination.


EXAMPLES
--------
Example 1:
    Input:  target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]
    Output: 3
    Explanation:
        - The cars starting at 10 (speed 2) and 8 (speed 4) become a fleet,
          meeting each other at mile 12. The fleet forms at target, so they
          are still counted as one fleet.
        - The car starting at 0 (speed 1) does not catch up to any other
          car, so it is a fleet by itself.
        - The cars starting at 5 (speed 1) and 3 (speed 3) become a fleet,
          meeting each other at mile 6. The fleet moves at speed 1 until it
          reaches target.

Example 2:
    Input:  target = 10, position = [3], speed = [3]
    Output: 1
    Explanation: There is only one car, hence there is only one fleet.

Example 3:
    Input:  target = 100, position = [0,2,4], speed = [4,2,1]
    Output: 1
    Explanation:
        - The cars starting at 0 (speed 4) and 2 (speed 2) become a fleet,
          meeting each other at mile 4. The car starting at 4 (speed 1)
          travels to mile 5.
        - Then, the fleet at mile 4 (speed 2) and the car at mile 5 (speed
          1) become one fleet, moving at speed 1 until it reaches target.


CONSTRAINTS
-----------
    n == position.length == speed.length
    1 <= n <= 10^5
    0 < target <= 10^6
    0 <= position[i] < target
    All the values of `position` are UNIQUE.
    0 < speed[i] <= 10^6


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

There is no array to scan for "next greater element" and the word "stack"
appears nowhere. This is the DISGUISED monotonic stack (topic guide §2.4),
and the disguise is the entire difficulty. Three reframes unlock it:

1. Forget speeds and positions. What matters about a car is the TIME it
   would take to reach the target if the road ahead were empty:

        t_i = (target - position[i]) / speed[i]

2. Cars cannot pass. So a car's ACTUAL arrival time is decided entirely by
   the cars AHEAD of it (closer to the target) — never by the cars behind.
   That means: process cars in order of DESCENDING position, front car
   first.

3. Walking front-to-back, keep a stack of the arrival times of the fleets
   already formed. For the next car back, with unobstructed time `t`:

        t <= (time of the fleet ahead)  ->  it catches that fleet
                                            (it is faster and behind, so it
                                            arrives no later) -> ABSORBED,
                                            do not push
        t >  (time of the fleet ahead)  ->  it can never catch up ->
                                            it starts a NEW fleet -> push t

The answer is the final size of the stack.


WHAT TO THINK ABOUT
--------------------
1. Why DESCENDING position and not ascending? What information does a car
   behind you have that could possibly change your arrival time? (Try
   Example 1 sorted the other way and see what number you get.)
2. Why is comparing unobstructed TIMES enough, even though a car that gets
   absorbed physically slows down? Hint: an absorbed car adopts the fleet's
   arrival time, which is exactly the value already sitting on the stack —
   so nothing needs updating.
3. "If a car catches up to a car fleet AT the mile target, it is still one
   fleet." Which comparison does that force — `<` or `<=`? Which side of
   the boundary does an exactly-equal arrival time belong to?
4. Do you actually need the stack, or only its SIZE? What single variable
   could replace it?


PROGRESSIVE HINTS
------------------
Hint 1: Pair the arrays up: `sorted(zip(position, speed), reverse=True)`.
        Descending by position (positions are unique, so no tie-breaking
        worry).

Hint 2: For each `(p, s)` in that order compute `t = (target - p) / s`.
        Maintain `stack`; push `t` only when the stack is empty or
        `t > stack[-1]`. Otherwise the car merges into the fleet ahead and
        is dropped.

Hint 3: Return `len(stack)`. The stack's arrival times end up strictly
        increasing bottom-to-top — the same monotonic-stack invariant as
        problem 003, except the "resolve" step here is "silently absorb
        this car" rather than "pop and record an answer".


COMPLEXITY TARGET
------------------
    Time:  O(n log n) — dominated by the SORT. The stack pass itself is
           O(n) by the usual argument (each car is considered once and
           pushed at most once). Note this is the one monotonic-stack
           problem in the folder that is not O(n) overall: the sort is the
           bottleneck and it is unavoidable, because "who is ahead of whom"
           is exactly what the sort establishes.
    Space: O(n) for the stack (worst case: every car forms its own fleet)
           plus O(n) for the sorted pairs.
================================================================================
"""

from typing import List


class Solution:
    def carFleet(self, target: int, position: List[int], speed: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 008_car_fleet_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3], 3),
        (10, [3], [3], 1),
        (100, [0, 2, 4], [4, 2, 1], 1),
        (10, [0, 4, 2], [2, 3, 1], 2),
        (10, [6, 8], [3, 2], 2),
        (10, [8, 3, 7, 4, 6, 5], [4, 4, 4, 4, 4, 4], 6),   # all equal speeds
        (10, [0, 2, 4], [1, 1, 1], 3),                      # nobody catches up
        (10, [4, 2, 0], [1, 2, 3], 1),                      # everyone merges
        (1, [0], [1], 1),
    ]

    passed = 0
    for target, position, speed, expected in cases:
        got = sol.carFleet(target, list(position), list(speed))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  target={target:<5} position={position!r:<24} "
              f"speed={speed!r:<22} -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
