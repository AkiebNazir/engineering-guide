"""
================================================================================
LeetCode 353 · Design Snake Game                                        [Medium]
https://leetcode.com/problems/design-snake-game/
Topic: 25 · Design
================================================================================

PROBLEM
-------
Design a Snake game on an `width x height` board, played on a device
without a screen. The snake starts at position `(0, 0)` (top-left cell),
with an initial length of 1.

You are given `food`, a list of positions in the order the snake should
eat them. Each food item appears ONE AT A TIME (the next one only appears
after the previous one is eaten), and always at a position NOT currently
occupied by the snake.

Implement the `SnakeGame` class:

    SnakeGame(width, height, food)   Initializes the object.
    move(direction) -> int           `direction` is one of "U", "D", "L",
                                      "R". Moves the snake one cell.
                                      - If the snake's head lands on a food
                                        position, the snake EATS it (grows
                                        by one, score increases by 1, the
                                        food is not "used up" as an
                                        obstacle so the tail does NOT move
                                        off this turn).
                                      - If the snake goes out of bounds, or
                                        its head collides with its OWN
                                        body, the game is OVER: return -1.
                                      - Otherwise return the current score.


EXAMPLES
--------
Example 1:
    Input:
        ["SnakeGame", "move", "move", "move", "move", "move", "move"]
        [[3, 2, [[1,2],[0,1]]], ["R"], ["D"], ["R"], ["U"], ["L"], ["U"]]
    Output:
        [null, 0, 0, 1, 1, 2, -1]

    Explanation:
        Board is width=3, height=2.  food = [[1,2], [0,1]]
        Snake starts at (0,0).
        move("R")  -> head (0,1), no food there yet -> score 0
        move("D")  -> head (1,1), no food -> score 0
        move("R")  -> head (1,2), EATS food[0]=(1,2) -> score 1, snake grows
        move("U")  -> head (0,2), no food -> score 1
        move("L")  -> head (0,1), EATS food[1]=(0,1) -> score 2, snake grows
        move("U")  -> head (-1,1), OUT OF BOUNDS -> game over, -1


CONSTRAINTS
-----------
    1 <= width, height <= 10^4
    1 <= food.length <= 50
    food[i].length == 2
    0 <= food[i][0] < height, 0 <= food[i][1] < width
    At most 10^4 calls will be made to move.


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

This is a design problem around a GROWING, ORDERED sequence with O(1)
membership checks — exactly the "two structures, kept in sync" pattern
(topic guide Part 0): a `deque` holds the snake's body in ORDER (head at
one end, tail at the other, so moving the head and popping the tail are
both O(1)), while a `set` mirrors the SAME cells for O(1) "does my new
head collide with my own body" checks — a deque alone would need an O(n)
scan to answer that.

The subtlety that trips people up: the TAIL cell must be freed (removed
from both the deque and the set) BEFORE checking the new head for
self-collision, UNLESS the snake just ate food this move (in which case
the tail does NOT move, so it must stay counted as occupied) — moving
into the cell your own tail is VACATING this turn is legal; moving into a
cell that will still be occupied is not.


WHAT TO THINK ABOUT
--------------------
1. Direction deltas: "U" decreases row, "D" increases row, "L" decreases
   column, "R" increases column — get row/col swapped and every move goes
   the wrong way.

2. Food is consumed strictly IN ORDER — track a single `food_index`
   pointer into the `food` list; the snake eats `food[food_index]` only
   when its NEW head lands exactly there, then increments the pointer.
   There is at most one "current" food target at a time.

3. Growth mechanics: eating food means the OLD tail stays put (snake gets
   longer) while a new head is added; NOT eating means the old tail is
   removed and a new head is added (snake stays the same length, just
   slides forward).

4. Self-collision must be checked AFTER accounting for whether the tail
   vacated this turn — checking against the body set BEFORE removing the
   about-to-vacate tail would falsely report a collision when the snake
   moves into the cell its own tail just left.


PROGRESSIVE HINTS
------------------
Hint 1: `deque` for the body (O(1) push-head / pop-tail) PLUS a `set`
        mirroring the same cells (O(1) self-collision check) — same
        two-structures-in-sync idea as several other problems in this
        topic.

Hint 2: Compute the new head position first. Check out-of-bounds
        immediately (cheapest check, no state to touch yet).

Hint 3: THEN decide: does the new head equal the next food position? If
        yes, grow (don't remove tail). If no, remove the tail from BOTH
        structures FIRST, then check if the new head collides with what's
        left of the body, THEN add the new head to both structures.


COMPLEXITY TARGET
------------------
    move:  O(1) time (deque push/pop + set membership are all O(1))
    Space: O(width * height) worst case (snake can occupy nearly every cell)
================================================================================
"""

from collections import deque


class SnakeGame:
    def __init__(self, width: int, height: int, food: list[list[int]]):
        # YOUR CODE HERE
        pass

    def move(self, direction: str) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 007_design_snake_game_question.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    game = SnakeGame(3, 2, [[1, 2], [0, 1]])
    ops = [
        (game.move("R"), 0),
        (game.move("D"), 0),
        (game.move("R"), 1),
        (game.move("U"), 1),
        (game.move("L"), 2),
        (game.move("U"), -1),
    ]
    for got, want in ops:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  got={got}  want={want}")

    # Snake moving into the cell its own tail just vacated must be legal.
    # Grow to length 2 first (eat food at (0,1)), then loop a 2-cell cycle
    # repeatedly — each move re-enters the cell the tail just vacated.
    g2 = SnakeGame(4, 4, [[0, 1]])
    ok = g2.move("R") == 1  # eats (0,1) -> body: [(0,1), (0,0)], length 2
    ok &= g2.move("D") != -1  # head (1,1), tail (0,0) vacates -> body: [(1,1),(0,1)]
    ok &= g2.move("L") != -1  # head (1,0), tail (0,1) vacates -> body: [(1,0),(1,1)]
    ok &= g2.move("U") != -1  # head (0,0), tail (1,1) vacates -> body: [(0,0),(1,0)]
    ok &= g2.move("R") != -1  # head (0,1), re-enters a cell the body held two moves ago -> legal
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  looping back into a cell vacated by the moving tail is legal, not a collision")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
