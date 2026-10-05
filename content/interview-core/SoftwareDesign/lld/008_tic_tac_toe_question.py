"""
================================================================================
LLD 008 · Tic-Tac-Toe (N x N, K in a row)                          [Tier 1]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design and implement a generalised tic-tac-toe game.

The interviewer says: "Design tic-tac-toe. Then make it N x N." These are the
agreed requirements.

REQUIREMENTS
------------
  1. TicTacToe(n=3, k=None, detector=None). N >= 3, 3 <= K <= N, K defaults to
     N; otherwise ValueError. X moves first; turns alternate.
  2. move(row, col) -> Status. Raise InvalidMove (and change nothing) if the
     cell is off the board (negative indices included), taken, or the game is
     already over.
  3. Status: IN_PROGRESS, X_WINS, O_WINS, DRAW. A move that completes a line
     on the last empty cell is a win, not a draw.
  4. Win detection is pluggable. `detector` is a class called as
     detector(n, k):
        CounterDetector   O(1) per move; raises ValueError unless K == N
        LineScanDetector  O(K) per move; works for any K
     Default: CounterDetector when K == N, else LineScanDetector.
     Neither may rescan the whole board.
  5. undo() takes back the last move (also a winning one), restoring turn and
     status. InvalidMove if there is nothing to undo.
  6. Properties/queries: turn (Mark), status, winner (Mark or None),
     cell(r, c) -> Mark | None, legal_moves() -> [(r, c)] (empty when over),
     key() -> a hashable snapshot of the board.
  7. Players: choose(game) -> (r, c).
        ScriptedPlayer(moves)   plays the given moves in order
        PerfectPlayer()         never loses on 3x3 (minimax); must leave the
                                game exactly as it found it
     play(game, x_player, o_player) -> final Status.

  Out of scope: UI, networking.

WHAT THE INTERVIEWER IS LOOKING FOR
-----------------------------------
  * How do you detect a win in O(1) after each move?
  * Why must X and O count with opposite signs?
  * What changes for K < N (Gomoku) or gravity (Connect Four)?
  * How does undo interact with the win detector?
  * Where does AI logic live, and can it reuse move/undo?

FOLLOW-UPS TO PREPARE
---------------------
  Connect Four · Gomoku · AI on large boards · online play with stale
  clients · replays / spectators · early draw detection.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

from enum import Enum


class Mark(Enum):
    X = "X"
    O = "O"


class Status(Enum):
    IN_PROGRESS = "in_progress"
    X_WINS = "x_wins"
    O_WINS = "o_wins"
    DRAW = "draw"


class InvalidMove(Exception): ...


class CounterDetector:
    def __init__(self, n: int, k: int) -> None:
        raise NotImplementedError


class LineScanDetector:
    def __init__(self, n: int, k: int) -> None:
        raise NotImplementedError


class TicTacToe:
    def __init__(self, n: int = 3, k: int | None = None, detector: type | None = None) -> None:
        # YOUR CODE HERE
        raise NotImplementedError

    def move(self, row: int, col: int) -> Status:
        raise NotImplementedError

    def undo(self) -> None:
        raise NotImplementedError

    @property
    def winner(self) -> Mark | None:
        raise NotImplementedError

    def cell(self, row: int, col: int) -> Mark | None:
        raise NotImplementedError

    def legal_moves(self) -> list[tuple[int, int]]:
        raise NotImplementedError

    def key(self) -> tuple:
        raise NotImplementedError


class ScriptedPlayer:
    def __init__(self, moves: list[tuple[int, int]]) -> None:
        raise NotImplementedError


class PerfectPlayer:
    def choose(self, game: TicTacToe) -> tuple[int, int]:
        raise NotImplementedError


def play(game: TicTacToe, x, o) -> Status:
    raise NotImplementedError


# ===================================================================== TESTS ==
# Identical to the solution file's tests. Make them all PASS.
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


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
