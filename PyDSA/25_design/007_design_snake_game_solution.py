"""
================================================================================
SOLUTION · LeetCode 353 · Design Snake Game                             [Medium]
https://leetcode.com/problems/design-snake-game/
================================================================================

THE CORE IDEA
--------------
A `deque` for the snake's body (O(1) push-head, O(1) pop-tail — a list
would need O(n) `pop(0)`) PLUS a `set` mirroring the same cells (O(1)
self-collision check — a deque alone needs an O(n) scan to check "is this
cell already occupied"). Same two-structures-kept-in-sync discipline as
LRU Cache and Insert Delete GetRandom O(1) in this topic, applied to a
growing/sliding sequence instead of a cache or a random-access set.

The one subtlety: the TAIL must be freed from BOTH structures BEFORE the
self-collision check, UNLESS food is eaten this move (the tail stays put,
snake grows) — moving into a cell the tail is vacating THIS turn is legal;
moving into a cell the tail is NOT vacating (because it just grew) is not.


================================================================================
APPROACH 1 · List for the body, O(n) collision scan (brute force, priced,
not coded)
================================================================================
A plain Python list for the body; `move` does `list.pop(0)` to drop the
tail (O(n) — every remaining element shifts) and scans the whole list
(`new_head in body`) to check self-collision (O(n)).

    Time: O(n) per move, n = current snake length.     Space: O(n).

Both costs (the pop-from-front shift AND the linear collision scan)
disappear with a deque+set — not coded separately since it's a strict
subset of Approach 2 with the "wrong" container choices.


================================================================================
APPROACH 2 · deque (body, ordered) + set (body, O(1) lookup) ✅ (the answer)
================================================================================
    from collections import deque

    class SnakeGame:
        def __init__(self, width, height, food):
            self.width, self.height = width, height
            self.food = food
            self.food_index = 0
            self.score = 0
            self.body = deque([(0, 0)])
            self.body_set = {(0, 0)}
            self.deltas = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

        def move(self, direction):
            dr, dc = self.deltas[direction]
            r, c = self.body[0]
            new_head = (r + dr, c + dc)
            nr, nc = new_head

            if not (0 <= nr < self.height and 0 <= nc < self.width):
                return -1                                          # out of bounds

            ate_food = (self.food_index < len(self.food)
                        and new_head == tuple(self.food[self.food_index]))

            if not ate_food:
                tail = self.body.pop()          # tail vacates THIS turn
                self.body_set.discard(tail)

            if new_head in self.body_set:        # collides with what's LEFT of the body
                # Restore the tail we speculatively removed, so game state
                # stays consistent for any caller that inspects it after -1.
                if not ate_food:
                    self.body.append(tail)
                    self.body_set.add(tail)
                return -1

            self.body.appendleft(new_head)
            self.body_set.add(new_head)

            if ate_food:
                self.score += 1
                self.food_index += 1

            return self.score

Removing the tail BEFORE the collision check (when not eating) is what
makes "the snake can legally move into the cell its own tail is leaving"
work; keeping the tail (when eating) is what makes "growing into a cell
that's about to become permanently occupied" correctly flagged as a
collision if the new head lands on the snake's own (still fully present)
body.

    Time: O(1) per move.     Space: O(width * height) worst case.


================================================================================
STEP BY STEP TRACE — width=3, height=2, food=[[1,2],[0,1]]
================================================================================
    init            body=[(0,0)]  body_set={(0,0)}  food_index=0  score=0

    move("R")       new_head=(0,1). in bounds. ate_food? food[0]=(1,2) != (0,1) -> No.
                    pop tail (0,0) -> body_set={}. (0,1) not in body_set -> OK.
                    body=[(0,1)]  body_set={(0,1)}                 returns 0

    move("D")       new_head=(1,1). ate_food? (1,2) != (1,1) -> No.
                    pop tail (0,1) -> body_set={}. OK.
                    body=[(1,1)]  body_set={(1,1)}                 returns 0

    move("R")       new_head=(1,2). ate_food? food[0]=(1,2) == (1,2) -> YES!
                    tail NOT removed (still (1,1) in body_set={(1,1)}).
                    (1,2) not in body_set -> OK.
                    body=[(1,2),(1,1)]  body_set={(1,2),(1,1)}  score=1  food_index=1
                                                                       returns 1

    move("U")       new_head=(0,2). ate_food? food[1]=(0,1) != (0,2) -> No.
                    pop tail (1,1) -> body_set={(1,2)}. OK.
                    body=[(0,2),(1,2)]  body_set={(0,2),(1,2)}       returns 1

    move("L")       new_head=(0,1). ate_food? food[1]=(0,1) == (0,1) -> YES!
                    tail NOT removed (still (1,2)).
                    (0,1) not in body_set -> OK.
                    body=[(0,1),(0,2),(1,2)]  score=2  food_index=2   returns 2

    move("U")       new_head=(-1,1). OUT OF BOUNDS.                  returns -1

    ASCII, board right after move("R") that eats food[0]=(1,2):

        row0:  .  .  .
        row1:  .  H  T      H=head(1,2) (just ate food here), T=tail(1,1)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        move (time)    Space              Mutates input?
    ----------------------------  --------------  -----------------  ---------------
    List body, O(n) scan          O(n)            O(n)               n/a — design problem
    deque + set ✅                O(1)            O(width * height)  n/a — design problem


================================================================================
EDGE CASES
================================================================================
    Snake length 1, self-collision  Can never happen with length 1 —
                                    there's no body cell besides the head
                                    itself to collide with; must not
                                    false-positive.
    Head lands exactly on food AND
      that cell is also the snake's
      own tail-about-to-vacate       Impossible per constraints (food
                                    never spawns on the snake's current
                                    body), but the eat-check happens
                                    BEFORE the tail-removal branch either
                                    way, so eating always takes priority
                                    correctly if it ever came up.
    Food list exhausted              `food_index >= len(food)` must stop
                                    triggering "ate_food" — the snake just
                                    keeps moving/scoring nothing further,
                                    never index-erroring into `food`.
    Out-of-bounds check happens
      FIRST                          Must be checked before any
                                    tail-removal or collision logic —
                                    otherwise a wall hit could corrupt
                                    body/body_set state before returning -1.
    Looping the body back through
      a cell it occupied SEVERAL
      moves ago (not just last
      turn's tail)                   Must correctly flag as a collision —
                                    the body_set doesn't care WHEN a cell
                                    was occupied, only whether it's
                                    CURRENTLY in the live body.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking self-collision BEFORE removing the tail (on a non-eating
   move) — false-positives every ordinary "move forward without growing"
   as a collision, since the tail cell (which is about to be vacated) is
   still in the set at check time.

2. Using only a set (no deque, or no ordered structure at all) to store
   the body — you then have NO way to know which cell is the tail (the
   one to remove on a non-eating move) without also tracking insertion
   order somehow; a bare set can't answer "what came in first."

3. Comparing `new_head` to `self.food[self.food_index]` as a LIST instead
   of a tuple (or vice versa) — `[1, 2] == (1, 2)` is False in Python even
   though they "look" equal; the head/body must consistently use ONE
   representation (tuples here) for both storage and comparison.

4. Forgetting `food_index` can run off the end of `self.food` once every
   food item has been eaten — indexing `self.food[self.food_index]`
   without the `food_index < len(self.food)` guard raises `IndexError` on
   any move after the last food is eaten.

5. Checking out-of-bounds AFTER already mutating `body`/`body_set` — wastes
   work and, if not carefully unwound, can leave inconsistent state for a
   caller that inspects the snake after a -1 return (some implementations
   don't bother, since -1 conventionally means "game over, no further
   calls," but it's a real correctness question worth raising explicitly).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: How would multiple food items on the board SIMULTANEOUSLY (not one at
   a time) change the design?
A: Replace the single `food_index` pointer with a set/dict of live food
   positions; eating removes just that one position from the set (O(1))
   instead of advancing a linear pointer — the deque+set body logic is
   unchanged.

Q: How would you support a snake that can pass through walls and
   reappear on the opposite side (wraparound / "Pac-Man" boundaries)?
A: Replace the out-of-bounds check with modular arithmetic:
   `new_head = ((r + dr) % height, (c + dc) % width)` — the rest of the
   collision/growth logic is untouched, since it only cares about the
   FINAL head cell, not how it was computed.

Q: Could `body_set` become a memory concern on a very large board
   (`width, height` up to 10^4)?
A: Only if the snake actually grows to a large fraction of the board —
   `body_set`'s size is bounded by the CURRENT snake length, not the
   board's total cell count, so it stays proportional to how much food
   has actually been eaten (at most 50 per constraints), not to
   `width * height`.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1197 Minimum Knight Moves                — grid BFS with delta-based moves, different goal
    LC 146  LRU Cache (topic 08)                — same deque/dict-analog "two structures in sync" discipline
    LC 1472 Design Browser History (this topic) — another "sequence + pointer" design, simpler (no growth)
    Topic 07 · Queue & Deque                    — deque as the O(1) both-ends structure this problem relies on
================================================================================
"""

import time
from collections import deque


class SnakeGame:
    """deque (ordered body) + set (O(1) collision lookup). See THE CORE
    IDEA above."""

    _DELTAS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

    def __init__(self, width: int, height: int, food: list[list[int]]):
        self.width = width
        self.height = height
        self.food = food
        self.food_index = 0
        self.score = 0
        self.body: deque = deque([(0, 0)])
        self.body_set: set = {(0, 0)}

    def move(self, direction: str) -> int:
        dr, dc = self._DELTAS[direction]
        r, c = self.body[0]
        new_head = (r + dr, c + dc)
        nr, nc = new_head

        if not (0 <= nr < self.height and 0 <= nc < self.width):
            return -1

        ate_food = (
            self.food_index < len(self.food)
            and new_head == tuple(self.food[self.food_index])
        )

        tail = None
        if not ate_food:
            tail = self.body.pop()
            self.body_set.discard(tail)

        if new_head in self.body_set:
            if tail is not None:
                self.body.append(tail)
                self.body_set.add(tail)
            return -1

        self.body.appendleft(new_head)
        self.body_set.add(new_head)

        if ate_food:
            self.score += 1
            self.food_index += 1

        return self.score


# ------------------------------------------------------------------------
# Alternatives / oracles.
# ------------------------------------------------------------------------
class SnakeGameListScan:
    """Approach 1: plain list body, O(n) tail-pop and O(n) collision scan.
    Used as a correctness oracle and for the benchmark."""

    _DELTAS = {"U": (-1, 0), "D": (1, 0), "L": (0, -1), "R": (0, 1)}

    def __init__(self, width: int, height: int, food: list[list[int]]):
        self.width = width
        self.height = height
        self.food = food
        self.food_index = 0
        self.score = 0
        self.body: list = [(0, 0)]  # index 0 = head

    def move(self, direction: str) -> int:
        dr, dc = self._DELTAS[direction]
        r, c = self.body[0]
        new_head = (r + dr, c + dc)
        nr, nc = new_head

        if not (0 <= nr < self.height and 0 <= nc < self.width):
            return -1

        ate_food = (
            self.food_index < len(self.food)
            and new_head == tuple(self.food[self.food_index])
        )

        body_without_tail = self.body if ate_food else self.body[:-1]

        if new_head in body_without_tail:  # O(n) linear scan
            return -1

        self.body = [new_head] + body_without_tail

        if ate_food:
            self.score += 1
            self.food_index += 1

        return self.score


# ==============================================================================
# TESTS — run:  python 007_design_snake_game_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    # ------------------------------------------------------------------
    # Correctness: LeetCode's canonical example, cross-checked against the
    # list-scan alternative.
    # ------------------------------------------------------------------
    print("--- correctness: deque+set vs list-scan ---")
    script = ["R", "D", "R", "U", "L", "U"]
    wants = [0, 0, 1, 1, 2, -1]
    for name, cls in (("deque+set ", SnakeGame), ("list-scan ", SnakeGameListScan)):
        g = cls(3, 2, [[1, 2], [0, 1]])
        results = [g.move(d) for d in script]
        ok = results == wants
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name}  results={results}  (want {wants})")

    # ------------------------------------------------------------------
    # Moving into the cell the tail just vacated is legal.
    # ------------------------------------------------------------------
    print("\n--- moving into a cell the tail vacates this turn is legal ---")
    g = SnakeGame(4, 4, [[0, 1]])
    ok = g.move("R") == 1  # eats (0,1) -> body: head(0,1), tail(0,0), length 2
    ok &= g.move("D") != -1
    ok &= g.move("L") != -1
    ok &= g.move("U") != -1
    ok &= g.move("R") != -1  # re-enters a cell the body occupied two moves ago -> legal
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  four-move loop with a length-2 snake never false-positives a collision")

    # ------------------------------------------------------------------
    # Snake grows to length 4, then slides its head through cells its own
    # tail is actively vacating each turn — hand-traced exactly (see the
    # solution docstring's STEP BY STEP style reasoning): every one of
    # these moves is legal because the tail always vacates in time.
    # ------------------------------------------------------------------
    print("\n--- growing snake sliding: tail always vacates in time, never a false collision ---")
    food = [[0, 1], [0, 2], [1, 2]]
    g2 = SnakeGame(4, 4, food)
    moves = ["R", "R", "D"]  # eats all three foods; snake now length 4: head(1,2)...tail(0,0)
    results = [g2.move(m) for m in moves]
    ok = results == [1, 2, 3]
    # Continue sliding (no more food) — hand-traced: L -> (1,1), U -> (0,1),
    # L -> (0,0). At each step the tail vacates the cell before the head
    # arrives there, so none of these three slides collide; score stays 3.
    ok &= g2.move("L") == 3
    ok &= g2.move("U") == 3
    ok &= g2.move("L") == 3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  grow-to-4 then 3 more slides, all legal (score frozen at 3), results={results}")

    # ------------------------------------------------------------------
    # Food list exhausted: further moves must not IndexError and must
    # keep returning the frozen score.
    # ------------------------------------------------------------------
    print("\n--- food list exhausted: no IndexError, score stays frozen ---")
    g3 = SnakeGame(5, 5, [[0, 1]])
    g3.move("R")  # eats the only food -> score 1
    ok = g3.move("R") == 1 and g3.move("R") == 1  # no more food, score unchanged, no crash
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  moves after food exhausted don't crash and don't add score")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the list-scan oracle on a snake that
    # actually grows (small board, dense food, so collisions get tested).
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs list-scan oracle (small board, dense food) ---")
    import random
    rng = random.Random(31)
    mismatch = False
    for trial in range(15):
        w, h = 4, 4
        food = [[rng.randrange(h), rng.randrange(w)] for _ in range(10)]
        fast = SnakeGame(w, h, food)
        slow = SnakeGameListScan(w, h, food)
        for _ in range(40):
            d = rng.choice(["U", "D", "L", "R"])
            r1 = fast.move(d)
            r2 = slow.move(d)
            if r1 != r2:
                mismatch = True
            if r1 == -1:
                break  # game over, stop this trial
    all_ok &= not mismatch
    print(f"{'PASS' if not mismatch else 'FAIL'}  15 randomized trials of 40 moves each, deque+set matches list-scan")

    # ------------------------------------------------------------------
    # BENCHMARK — deque+set vs list-scan as the snake grows long. REAL
    # measured numbers.
    # ------------------------------------------------------------------
    print("\n--- benchmark: snake growing to length N, then sliding many moves ---")
    for n_food in (20, 40, 50):
        # Lay food in a straight line so the snake reliably grows to n_food+1
        # without self-colliding, then keep it sliding along the same row.
        w = h = 100
        food = [[0, i + 1] for i in range(n_food)]
        n_slides = 3000

        fast = SnakeGame(w, h, food)
        t0 = time.perf_counter()
        for i in range(n_food):
            fast.move("R")
        for i in range(n_slides):
            fast.move("R" if i % 2 == 0 else "L")
        t1 = time.perf_counter()
        fast_ms = (t1 - t0) * 1000

        slow = SnakeGameListScan(w, h, food)
        t0 = time.perf_counter()
        for i in range(n_food):
            slow.move("R")
        for i in range(n_slides):
            slow.move("R" if i % 2 == 0 else "L")
        t1 = time.perf_counter()
        slow_ms = (t1 - t0) * 1000

        slowdown = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  snake length~{n_food+1:>3}   deque+set: {fast_ms:>8.2f}ms   list-scan: {slow_ms:>8.2f}ms   {slowdown:>6.1f}x slower")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
