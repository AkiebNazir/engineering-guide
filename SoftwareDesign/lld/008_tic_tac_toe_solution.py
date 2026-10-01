"""
================================================================================
SOLUTION · LLD 008 · Tic-Tac-Toe (N x N, K in a row)               [Tier 1]
================================================================================

THE CORE IDEA
--------------
The algorithmic heart is WIN DETECTION after each move, and the design heart is
keeping the three things that vary out of the Game class:

    1. HOW a win is detected      -> WinDetector strategy
         CounterDetector   O(1) per move, only for K == N (classic LC 348):
                           rows[r] += ±1, cols[c] += ±1, diag, anti-diag;
                           |count| == N means a win.
         LineScanDetector  O(K) per move, any K (Gomoku, Connect-4 style):
                           from the new stone, count same marks in both
                           directions along 4 axes.
         Full-board rescan O(N^2) per move — the answer to avoid.
    2. WHO picks the move         -> Player strategy (scripted, random, perfect)
    3. UNDO                       -> a move history stack (Command); detectors
                                     reverse their counters in O(1).

Only the move that was just played can create a win, so never rescan the board.
Demo 2 measures the difference on a 1000 x 1000 board.

Having undo pays off immediately: the minimax PerfectPlayer searches by calling
game.move() / game.undo() on the real game — no board copying — and demo 3
shows it never loses.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. N x N board (N >= 3), K in a row wins (default K = N).
  2. X moves first; players alternate.
  3. move(row, col) -> Status; InvalidMove for out-of-bounds, occupied cell,
     or any move after the game ended.
  4. Status: IN_PROGRESS, X_WINS, O_WINS, DRAW (board full, no winner).
  5. undo() takes back the last move (also after a win).
  6. Pluggable players; play(game, x, o) runs a whole game.
  Out of scope: networking, UI, time controls, ratings.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    Mark                 enum X / O (with .other)
    Status               enum
    TicTacToe            board, turn, status, history
                         INVARIANT: |#X - #O| <= 1 and X count >= O count;
                         status != IN_PROGRESS => no further moves accepted;
                         the detector's state always matches the board
    WinDetector          on_move(board, r, c, mark) -> bool; on_undo(...)
    Player               choose(game) -> (r, c)


================================================================================
COUNTER TRACE · N = 3, X = +1, O = -1
================================================================================
    move      rows        cols        diag  anti   result
    X (0,0)   [1, 0, 0]   [1, 0, 0]    1     0
    O (1,1)   [1,-1, 0]   [1,-1, 0]    0    -1
    X (0,1)   [2,-1, 0]   [1, 0, 0]    0    -1
    O (2,2)   [2,-1,-1]   [1, 0,-1]   -1    -1
    X (0,2)   [3,-1,-1]   [1, 0, 1]   -1     0     rows[0] == 3 -> X wins
    A row holding X X O sums to 1, never ±3, so mixed lines can't false-positive.


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * Detector as strategy chosen at construction; CounterDetector refuses K != N
    loudly instead of silently giving wrong answers.
  * Board as list of lists of Mark | None. Bitboards are faster for 3x3 AI
    search; mention as an optimisation, not the first answer.
  * Players don't mutate the game directly in play(); the loop asks for a move
    and applies it, so an illegal choice raises InvalidMove at one place.
  * History stack of (r, c, mark) gives undo, replays, and "show move list".
  * No class per piece or per cell — cells have no behaviour.


================================================================================
COMPLEXITY
================================================================================
    Operation          CounterDetector   LineScanDetector   Full rescan
    move (win check)   O(1)              O(K)               O(N^2)
    undo               O(1)              O(1)               O(1)
    Space              O(N)              O(1) extra         O(1) extra
    PerfectPlayer 3x3  <= 5,478 reachable positions, memoised


================================================================================
EDGE CASES
================================================================================
  * Win on the very last cell -> WIN, not DRAW (check win before full).
  * Anti-diagonal on even N ((0,3),(1,2),(2,1),(3,0) for N=4).
  * Cell on both diagonals (centre of odd N) updates both counters.
  * K < N: a win anywhere, including off the main diagonals.
  * Undo after a win reopens the game; undo with no moves -> InvalidMove.
  * Negative indices (Python would silently wrap!) -> InvalidMove.


================================================================================
COMMON MISTAKES
================================================================================
  1. Rescanning the whole board after every move.
  2. Using a single counter per line without signs (X X O looks like 3 marks).
  3. Forgetting the anti-diagonal condition r + c == N - 1.
  4. Accepting board[-1][-1] because Python allows negative indexing.
  5. Checking DRAW before checking WIN on the last move.
  6. Player subclasses that reach into the board and write to it.
  7. Game class that also prints, reads input, and runs the AI.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * Connect Four      -> gravity: move(col) finds the lowest empty row; detector
                         is LineScanDetector with K = 4.
  * Gomoku (15x15, 5) -> LineScanDetector; exactly-five rules as a detector option.
  * AI for large N    -> minimax is hopeless; depth-limited alpha-beta with a
                         heuristic, or MCTS.
  * Online multiplayer-> Game behind a service; moves carry the expected move
                         number (optimistic concurrency) so stale clients fail.
  * Replays / spectators -> history is the event log; Observer on move.
  * Early draw detection -> track lines still winnable by someone.


================================================================================
RELATED
================================================================================
  PyDSA 25_design  LC 348 Design Tic-Tac-Toe (the counter trick in isolation)
  SoftwareDesign/04_design_patterns_in_practice.md  §3 Strategy, §8 Command
  lld/002_elevator_system (state as enum)
"""

from __future__ import annotations

import random
import time
from enum import Enum
from typing import Protocol


# ----------------------------------------------------------------------------
# Enums and errors
# ----------------------------------------------------------------------------
class Mark(Enum):
    X = "X"
    O = "O"

    @property
    def other(self) -> Mark:
        return Mark.O if self is Mark.X else Mark.X


class Status(Enum):
    IN_PROGRESS = "in_progress"
    X_WINS = "x_wins"
    O_WINS = "o_wins"
    DRAW = "draw"


class InvalidMove(Exception): ...


Board = list[list["Mark | None"]]


# ----------------------------------------------------------------------------
# Win detectors
# ----------------------------------------------------------------------------
class WinDetector(Protocol):
    def on_move(self, board: Board, r: int, c: int, mark: Mark) -> bool: ...
    def on_undo(self, board: Board, r: int, c: int, mark: Mark) -> None: ...


class CounterDetector:
    """O(1) per move. Valid only when K == N."""

    def __init__(self, n: int, k: int) -> None:
        if k != n:
            raise ValueError("CounterDetector needs K == N; use LineScanDetector")
        self.n = n
        self.rows = [0] * n
        self.cols = [0] * n
        self.diag = 0
        self.anti = 0

    def _apply(self, r: int, c: int, delta: int) -> None:
        self.rows[r] += delta
        self.cols[c] += delta
        if r == c:
            self.diag += delta
        if r + c == self.n - 1:
            self.anti += delta

    def on_move(self, board, r, c, mark):
        sign = 1 if mark is Mark.X else -1
        self._apply(r, c, sign)
        target = sign * self.n
        return (self.rows[r] == target or self.cols[c] == target
                or self.diag == target or self.anti == target)

    def on_undo(self, board, r, c, mark):
        self._apply(r, c, -1 if mark is Mark.X else 1)


class LineScanDetector:
    """O(K) per move for any K: walk out from the new stone along 4 axes."""

    AXES = ((0, 1), (1, 0), (1, 1), (1, -1))

    def __init__(self, n: int, k: int) -> None:
        self.n, self.k = n, k

    def on_move(self, board, r, c, mark):
        for dr, dc in self.AXES:
            run = 1
            for sign in (1, -1):
                rr, cc = r + sign * dr, c + sign * dc
                while 0 <= rr < self.n and 0 <= cc < self.n and board[rr][cc] is mark and run < self.k:
                    run += 1
                    rr, cc = rr + sign * dr, cc + sign * dc
            if run >= self.k:
                return True
        return False

    def on_undo(self, board, r, c, mark):
        pass


# ----------------------------------------------------------------------------
# Game
# ----------------------------------------------------------------------------
class TicTacToe:
    def __init__(self, n: int = 3, k: int | None = None, detector: type | None = None) -> None:
        k = n if k is None else k
        if n < 3 or not 3 <= k <= n:
            raise ValueError("need N >= 3 and 3 <= K <= N")
        self.n, self.k = n, k
        self._board: Board = [[None] * n for _ in range(n)]
        self._detector: WinDetector = (detector or (CounterDetector if k == n else LineScanDetector))(n, k)
        self._history: list[tuple[int, int, Mark, Status]] = []
        self.turn = Mark.X
        self.status = Status.IN_PROGRESS

    def move(self, row: int, col: int) -> Status:
        if self.status is not Status.IN_PROGRESS:
            raise InvalidMove(f"game over: {self.status.value}")
        if not (0 <= row < self.n and 0 <= col < self.n):
            raise InvalidMove(f"({row}, {col}) is off the board")
        if self._board[row][col] is not None:
            raise InvalidMove(f"({row}, {col}) is taken")
        mark = self.turn
        self._board[row][col] = mark
        self._history.append((row, col, mark, self.status))
        if self._detector.on_move(self._board, row, col, mark):
            self.status = Status.X_WINS if mark is Mark.X else Status.O_WINS
        elif len(self._history) == self.n * self.n:
            self.status = Status.DRAW
        self.turn = mark.other
        return self.status

    def undo(self) -> None:
        if not self._history:
            raise InvalidMove("nothing to undo")
        row, col, mark, previous = self._history.pop()
        self._detector.on_undo(self._board, row, col, mark)
        self._board[row][col] = None
        self.turn = mark
        self.status = previous

    @property
    def winner(self) -> Mark | None:
        return {Status.X_WINS: Mark.X, Status.O_WINS: Mark.O}.get(self.status)

    def cell(self, row: int, col: int) -> Mark | None:
        return self._board[row][col]

    def legal_moves(self) -> list[tuple[int, int]]:
        if self.status is not Status.IN_PROGRESS:
            return []
        return [(r, c) for r in range(self.n) for c in range(self.n) if self._board[r][c] is None]

    def key(self) -> tuple:
        return tuple(tuple(m.value if m else "." for m in row) for row in self._board)

    def __str__(self) -> str:
        return "\n".join(" ".join(m.value if m else "." for m in row) for row in self._board)


# ----------------------------------------------------------------------------
# Players
# ----------------------------------------------------------------------------
class Player(Protocol):
    def choose(self, game: TicTacToe) -> tuple[int, int]: ...


class ScriptedPlayer:
    def __init__(self, moves: list[tuple[int, int]]) -> None:
        self._moves = iter(moves)

    def choose(self, game):
        return next(self._moves)


class RandomPlayer:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def choose(self, game):
        return self._rng.choice(game.legal_moves())


class PerfectPlayer:
    """Memoised minimax using the game's own move/undo. Practical for 3x3."""

    def __init__(self) -> None:
        self._memo: dict[tuple, int] = {}

    def choose(self, game):
        me = game.turn
        best, best_score = None, -2
        for r, c in game.legal_moves():
            game.move(r, c)
            score = -self._value(game)
            game.undo()
            if score > best_score:
                best, best_score = (r, c), score
        return best

    def _value(self, game: TicTacToe) -> int:
        """Score from the perspective of the player to move: +1 win, 0 draw, -1 loss."""
        if game.status is not Status.IN_PROGRESS:
            return 0 if game.status is Status.DRAW else -1      # previous mover won
        key = (game.key(), game.turn)
        if key not in self._memo:
            best = -2
            for r, c in game.legal_moves():
                game.move(r, c)
                best = max(best, -self._value(game))
                game.undo()
                if best == 1:
                    break
            self._memo[key] = best
        return self._memo[key]


def play(game: TicTacToe, x: Player, o: Player) -> Status:
    players = {Mark.X: x, Mark.O: o}
    while game.status is Status.IN_PROGRESS:
        game.move(*players[game.turn].choose(game))
    return game.status


# ===================================================================== TESTS ==
def _check(label: str, ok: bool) -> bool:
    print(f"{'PASS' if ok else 'FAIL'}  {label}")
    return ok


def _raises(exc, fn) -> bool:
    try:
        fn()
    except exc:
        return True
    return False


def _run(moves, n=3, k=None, detector=None) -> TicTacToe:
    g = TicTacToe(n, k, detector)
    for r, c in moves:
        g.move(r, c)
    return g


def run_tests() -> bool:
    all_ok = True
    print("--- wins on every kind of line ---")
    for detector in (CounterDetector, LineScanDetector):
        name = detector.__name__
        all_ok &= _check(f"[{name}] row (the docstring trace)",
                         _run([(0, 0), (1, 1), (0, 1), (2, 2), (0, 2)], detector=detector).status is Status.X_WINS)
        all_ok &= _check(f"[{name}] column for O",
                         _run([(0, 0), (0, 1), (1, 0), (1, 1), (2, 2), (2, 1)], detector=detector).status is Status.O_WINS)
        all_ok &= _check(f"[{name}] main diagonal 4x4",
                         _run([(0, 0), (0, 1), (1, 1), (0, 2), (2, 2), (0, 3), (3, 3)], n=4,
                              detector=detector).winner is Mark.X)
        all_ok &= _check(f"[{name}] anti-diagonal 4x4",
                         _run([(0, 3), (0, 0), (1, 2), (0, 1), (2, 1), (1, 1), (3, 0)], n=4,
                              detector=detector).winner is Mark.X)
        mixed = _run([(0, 0), (0, 2), (0, 1)], detector=detector)
        all_ok &= _check(f"[{name}] X X O in a row is not a win", mixed.status is Status.IN_PROGRESS)
        last = _run([(0, 0), (0, 1), (0, 2), (1, 1), (1, 0), (1, 2), (2, 1), (2, 0), (2, 2)], detector=detector)
        all_ok &= _check(f"[{name}] full board, no line -> DRAW", last.status is Status.DRAW)
        win_last = _run([(0, 0), (0, 1), (0, 2), (1, 1), (1, 0), (1, 2), (2, 1), (2, 2), (2, 0)], detector=detector)
        all_ok &= _check(f"[{name}] win on the last cell is a WIN, not a draw", win_last.status is Status.X_WINS)

    print("\n--- K < N ---")
    g = _run([(3, 1), (0, 0), (2, 2), (0, 1), (1, 3)], n=5, k=3)
    all_ok &= _check("5x5, K=3: off-centre anti-diagonal wins", g.winner is Mark.X)
    all_ok &= _check("CounterDetector refuses K != N",
                     _raises(ValueError, lambda: TicTacToe(5, 3, CounterDetector)))

    print("\n--- invalid moves ---")
    g = _run([(1, 1)])
    all_ok &= _check("occupied cell", _raises(InvalidMove, lambda: g.move(1, 1)))
    all_ok &= _check("off the board, including negative indices",
                     _raises(InvalidMove, lambda: g.move(3, 0)) and _raises(InvalidMove, lambda: g.move(-1, 0)))
    all_ok &= _check("failed moves don't change the turn", g.turn is Mark.O)
    done = _run([(0, 0), (1, 0), (0, 1), (1, 1), (0, 2)])
    all_ok &= _check("no moves after the game ends", _raises(InvalidMove, lambda: done.move(2, 2)))

    print("\n--- undo ---")
    done.undo()
    all_ok &= _check("undo the winning move reopens the game with X to play",
                     done.status is Status.IN_PROGRESS and done.turn is Mark.X and done.cell(0, 2) is None)
    done.move(2, 2)
    done.move(1, 2)
    all_ok &= _check("counters were reversed: O now wins row 1", done.status is Status.O_WINS)
    fresh = TicTacToe()
    all_ok &= _check("undo with no moves", _raises(InvalidMove, fresh.undo))

    print("\n--- players ---")
    status = play(TicTacToe(), ScriptedPlayer([(0, 0), (1, 0), (2, 0)]), ScriptedPlayer([(0, 1), (1, 1)]))
    all_ok &= _check("scripted game: X wins column 0 after five moves", status is Status.X_WINS)
    g = _run([(0, 0), (2, 2), (0, 1)])
    all_ok &= _check("PerfectPlayer as O blocks the open row at (0, 2)", PerfectPlayer().choose(g) == (0, 2))
    g = _run([(0, 0), (1, 0), (0, 1), (1, 1)])
    all_ok &= _check("PerfectPlayer as X takes the immediate win at (0, 2)", PerfectPlayer().choose(g) == (0, 2))
    all_ok &= _check("search leaves the game unchanged", g.key() == _run([(0, 0), (1, 0), (0, 1), (1, 1)]).key()
                     and g.turn is Mark.X)
    return all_ok
# ================================================================= END TESTS ==


def _brute_winner(game: TicTacToe) -> Mark | None:
    n, k = game.n, game.k
    for r in range(n):
        for c in range(n):
            m = game.cell(r, c)
            if m is None:
                continue
            for dr, dc in LineScanDetector.AXES:
                if all(0 <= r + i * dr < n and 0 <= c + i * dc < n and game.cell(r + i * dr, c + i * dc) is m
                       for i in range(k)):
                    return m
    return None


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO 1: 3,000 random games, both detectors vs a brute-force rescan ---")
    rng = random.Random(1)
    disagreements = 0
    for i in range(3000):
        n = rng.choice([3, 4, 5, 6])
        a, b = TicTacToe(n, n, CounterDetector), TicTacToe(n, n, LineScanDetector)
        while a.status is Status.IN_PROGRESS:
            r, c = rng.choice(a.legal_moves())
            a.move(r, c)
            b.move(r, c)
            if rng.random() < 0.1 and len(a._history) > 1:
                a.undo(); b.undo()
            if not (a.status == b.status and a.winner == _brute_winner(a)):
                disagreements += 1
    all_ok &= _check(f"detectors and brute force agree after every move and undo ({disagreements} disagreements)",
                     disagreements == 0)

    print("\n--- DEMO 2: win-check cost on a 1000 x 1000 board ---")
    n, k_moves = 1000, 2000
    rng = random.Random(2)
    cells = rng.sample([(r, c) for r in range(0, n, 7) for c in range(0, n, 7)], k_moves)
    timings = {}
    for label, det in (("counter", CounterDetector), ("line scan", LineScanDetector)):
        g = TicTacToe(n, n, det)
        start = time.perf_counter()
        for r, c in cells:
            g.move(r, c)
        timings[label] = time.perf_counter() - start
    g = TicTacToe(n, n, CounterDetector)
    for r, c in cells[:-3]:
        g.move(r, c)
    start = time.perf_counter()
    for r, c in cells[-3:]:
        g.move(r, c)
        _brute_winner(g)                         # visit every cell after the move
    rescan_per_move = (time.perf_counter() - start) / 3
    print(f"      {k_moves} moves: counter {timings['counter'] * 1000:.1f} ms, "
          f"line scan {timings['line scan'] * 1000:.1f} ms (runs stop at the first gap on a sparse board), "
          f"full rescan ~{rescan_per_move * k_moves:.0f} s projected")
    all_ok &= _check("O(1) counters beat an O(N^2) rescan by orders of magnitude",
                     timings["counter"] * 100 < rescan_per_move * k_moves)

    print("\n--- DEMO 3: PerfectPlayer (minimax over move/undo) ---")
    rng = random.Random(3)
    results = {"perfect_loss": 0, "perfect_win": 0, "draw": 0}
    perfect = PerfectPlayer()
    for i in range(300):
        game = TicTacToe()
        rand = RandomPlayer(rng.randrange(10**9))
        if i % 2 == 0:
            status = play(game, perfect, rand)
            me = Status.X_WINS
        else:
            status = play(game, rand, perfect)
            me = Status.O_WINS
        if status is Status.DRAW:
            results["draw"] += 1
        elif status is me:
            results["perfect_win"] += 1
        else:
            results["perfect_loss"] += 1
    self_play = play(TicTacToe(), perfect, perfect)
    print(f"      300 games vs random: {results}; perfect vs perfect: {self_play.value}; "
          f"positions memoised: {len(perfect._memo)}")
    all_ok &= _check("perfect player never loses, and self-play is a draw",
                     results["perfect_loss"] == 0 and self_play is Status.DRAW)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
