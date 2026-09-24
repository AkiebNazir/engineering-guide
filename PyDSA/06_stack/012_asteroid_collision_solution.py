"""
================================================================================
SOLUTION · LeetCode 735 · Asteroid Collision                            [Medium]
https://leetcode.com/problems/asteroid-collision/
================================================================================

THE CORE IDEA
--------------
The stack holds survivors in left-to-right order. The ONLY collision is a
right-mover on top of the stack meeting an incoming left-mover
(`stack[-1] > 0 > a`). Resolve that in a loop: the incoming asteroid keeps
destroying smaller right-movers until it dies, ties, or runs out of
right-movers, in which case it survives and is pushed.

This is not a MONOTONIC stack problem, but it uses the same accounting: each
asteroid is pushed once and popped at most once, so the nested loop is O(n).


================================================================================
APPROACH 1 · Simulate rounds (priced, used only as an oracle)
================================================================================
Repeatedly scan the row for an adjacent (positive, negative) pair, resolve it,
and rescan until no pair remains.

    Time: O(n^2) — up to n resolutions, each after an O(n) scan
    Space: O(n)


================================================================================
APPROACH 2 · Stack of survivors ✅ (the answer)
================================================================================
    stack = []
    for a in asteroids:
        while stack and a < 0 < stack[-1]:
            if stack[-1] < -a:
                stack.pop()          # top explodes; a keeps flying
                continue
            if stack[-1] == -a:
                stack.pop()          # both explode
            break                    # a exploded (tie or smaller)
        else:
            stack.append(a)          # loop ended without break: a survived

`while ... else` in Python: the else block runs only if the loop condition
became false, not if we `break`. That's exactly "a survived all collisions".

WHY LEFT-TO-RIGHT ORDER IS ENOUGH. Every asteroid in the stack below the top
right-mover is either a left-mover (which will never meet anything to its
right) or a right-mover shielded by the ones above it. The new asteroid can
only reach them by destroying the ones above first, which is exactly what the
loop does, in order.

    Time: O(n) amortized    Space: O(n)


================================================================================
STEP BY STEP TRACE · asteroids = [10, 2, -5]
================================================================================
    a    stack before   collision?           action               stack after
    ---  ------------   -------------------  -------------------  -----------
    10   []             no (empty)           push                 [10]
     2   [10]           no (a > 0)           push                 [10, 2]
    -5   [10, 2]        yes: 2 > 0 > -5      2 < 5 -> pop 2       [10]
         [10]           yes: 10 > 0 > -5     10 > 5 -> a explodes [10]

    answer: [10]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time     Space   Mutates input?
    ------------------------  -------  ------  --------------
    Simulate rounds           O(n^2)   O(n)    No (works on a copy)
    Stack of survivors ✅     O(n)     O(n)    No


================================================================================
EDGE CASES
================================================================================
    Left-mover on an empty stack   Survives forever (nothing to its left).
    [-2, 1]                        Moving apart; both survive.
    Chain destruction              [1, 2, 3, -10] -> [-10].
    Tie                            Both removed; the loop must stop.
    Big left-mover after a tie     [5, -5, 5, -5] -> [] (each pair cancels).


================================================================================
COMMON MISTAKES
================================================================================
1. Colliding on ANY sign difference (`stack[-1] * a < 0`). [-2, 1] are flying
   apart but get resolved as a crash. Demo below.

2. Resolving only ONE collision per incoming asteroid (`if` instead of
   `while`). [1, 2, 3, -10] leaves 1 and 2 behind.

3. On a tie, popping the top but then pushing `a` too. Both must explode.

4. Forgetting that a destroyed incoming asteroid must not be pushed. Without
   while/else, track it with an `alive` flag.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the survivors' original indices?
A: Push (value, index) pairs.

Q: Asteroids have different speeds?
A: Order of collisions now depends on meeting times, not just adjacency. You'd
   need an event simulation with a priority queue of predicted collision times
   between adjacent pairs (like Car Fleet II, LC 1776, which also uses a stack).

Q: Count how many asteroids each survivor destroyed?
A: Keep a counter alongside each stack entry and add to it on every pop it
   causes.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 853   Car Fleet (008)            — stack of arrival times
    LC 1776  Car Fleet II               — collisions with speeds
    LC 20    Valid Parentheses (001)    — push/pop matching pairs
    LC 2211  Count Collisions on a Road — same direction logic, counting
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def asteroidCollision(self, asteroids: List[int]) -> List[int]:
        stack: List[int] = []
        for a in asteroids:
            while stack and a < 0 < stack[-1]:
                if stack[-1] < -a:
                    stack.pop()
                    continue
                if stack[-1] == -a:
                    stack.pop()
                break
            else:
                stack.append(a)
        return stack


# ------------------------------------------------------------------------
# Oracle and broken version for the demos.
# ------------------------------------------------------------------------
def collide_simulate(asteroids: List[int]) -> List[int]:
    row = list(asteroids)
    changed = True
    while changed:
        changed = False
        for i in range(len(row) - 1):
            a, b = row[i], row[i + 1]
            if a > 0 > b:
                if a > -b:
                    row = row[:i + 1] + row[i + 2:]
                elif a < -b:
                    row = row[:i] + row[i + 1:]
                else:
                    row = row[:i] + row[i + 2:]
                changed = True
                break
    return row


def collide_any_sign_bug(asteroids: List[int]) -> List[int]:
    """Mistake 1: treats every opposite-sign neighbour as a collision."""
    stack: List[int] = []
    for a in asteroids:
        alive = True
        while alive and stack and stack[-1] * a < 0:     # BUG
            if abs(stack[-1]) < abs(a):
                stack.pop()
            elif abs(stack[-1]) == abs(a):
                stack.pop()
                alive = False
            else:
                alive = False
        if alive:
            stack.append(a)
    return stack


# ==============================================================================
# TESTS — run:  python 012_asteroid_collision_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        ([5, 10, -5], [5, 10]),
        ([8, -8], []),
        ([10, 2, -5], [10]),
        ([-2, -1, 1, 2], [-2, -1, 1, 2]),
        ([1, -2, -2, -2], [-2, -2, -2]),
        ([-2, 1], [-2, 1]),
        ([1, 2, 3, -10], [-10]),
        ([5, -5, 5, -5], []),
    ]
    for asteroids, want in cases:
        got = sol.asteroidCollision(asteroids)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {asteroids}  got={got}  want={want}")

    print("\n--- randomized cross-check vs round-by-round simulation (800 rows) ---")
    rng = random.Random(735)
    bad = 0
    for _ in range(800):
        row = [rng.choice([-1, 1]) * rng.randint(1, 5) for _ in range(rng.randint(2, 15))]
        if sol.asteroidCollision(row) != collide_simulate(row):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  800 random rows agree with the simulation")

    print("\n--- mistake 1 LIVE: colliding on any sign difference ---")
    wrong, right = collide_any_sign_bug([-2, 1]), sol.asteroidCollision([-2, 1])
    ok = wrong != right and right == [-2, 1]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  [-2, 1] (flying apart): buggy returns {wrong}, correct {right}")

    print("\n--- amortized O(n): pops never exceed pushes ---")
    row = [rng.choice([-1, 1]) * rng.randint(1, 1000) for _ in range(10_000)]
    pushes = pops = 0
    stack: List[int] = []
    for a in row:
        while stack and a < 0 < stack[-1]:
            if stack[-1] < -a:
                stack.pop(); pops += 1
                continue
            if stack[-1] == -a:
                stack.pop(); pops += 1
            break
        else:
            stack.append(a); pushes += 1
    ok = pops <= pushes <= len(row)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=10,000: {pushes} pushes, {pops} pops — total work <= 2n")

    print("\n--- benchmark: worst case for the simulation (many right-movers, then one huge left-mover) ---")
    row = [1] * 3000 + [-1001]
    for name, fn in (("simulate rounds", collide_simulate), ("stack          ", sol.asteroidCollision)):
        t0 = time.perf_counter(); r = fn(row); dt = time.perf_counter() - t0
        print(f"      {name}  {dt * 1000:9.2f} ms   result={r}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
