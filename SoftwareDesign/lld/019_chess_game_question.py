"""
================================================================================
LLD 019 · Chess (move validation + check / checkmate)                [Tier 2]
Time box: 45 minutes (5 clarify · 7 model · 5 API · 20 code · 8 extend)
================================================================================

PROBLEM
-------
Design the rules engine for a two-player chess game: legal move generation
per piece, check/checkmate/stalemate detection, and the three special moves
(castling, en passant, promotion). No UI, no clock, no notation parsing —
just "is this move legal, and what does the position look like after it."

The interviewer says: "Design the move-validation engine, not a chess AI and
not a full PGN/algebraic-notation system." These are the agreed requirements.

REQUIREMENTS
------------
  1. Standard 8x8 board, 2 colors, 6 piece types, White moves first.
  2. Each piece type must generate its own candidate moves (polymorphism) —
     no single function with a big if/elif on piece type.
  3. move(from_sq, to_sq, promotion=None) -> Status. Rejects with IllegalMove
     and changes nothing on: the wrong color's turn, an empty source square,
     or a destination that is not in that piece's legal-move set — including
     a pseudo-legal move (one that follows the piece's pattern) that would
     leave the mover's own king in check.
  4. in_check(color); checkmate = zero legal moves while in check;
     stalemate = zero legal moves while NOT in check.
  5. Castling (both sides), en passant, and promotion — each with its real
     preconditions:
       - Castling: neither king nor that rook has moved, no piece between
         them, the king is not currently in check, and the king does not
         pass through or land on an attacked square.
       - En passant: only legal on the ply immediately after the enemy pawn's
         qualifying two-square push; any other move in between forfeits it.
       - Promotion: required (not optional) the moment a pawn reaches the
         last rank; the caller supplies which piece it becomes.
  Out of scope (follow-ups, not implemented here): the 50-move rule,
  threefold repetition, algebraic notation (SAN) parsing/generation, draw
  offers, a clock.

WHAT THE INTERVIEWER IS LOOKING FOR
------------------------------------
  * Genuine polymorphism for movement: a `Piece` base type with one method
    concrete piece classes override, not a switch on an enum.
  * Recognising that "does my own pattern reach this square" and "is this
    move actually SAFE (doesn't leave my king in check)" are two different
    questions — the second one needs simulating the move and checking the
    result, and is the mechanism that also happens to catch pinned pieces,
    without any separate "is this piece pinned" code path.
  * Treating castling, en passant, and promotion as their own explicit rules
    with their own preconditions, rather than smearing special-case checks
    into the general move code (or, worse, into `King`/`Pawn` themselves).
  * A pawn's *attacked* squares are not the same as its *move* squares (it
    threatens diagonals whether or not anything is standing there yet, but
    can only move diagonally when there's something to capture).
  * Telling this apart from `008_tic_tac_toe`: win detection there is a
    static check over a fixed board; here, "does the side to move have any
    legal move at all" has to account for every piece's pattern AND every
    piece's own king-safety filter, so it can't be a simple static scan.

FOLLOW-UPS TO PREPARE
----------------------
  50-move rule / threefold repetition (position-hash + halfmove counters) ·
  SAN parsing/generation · a clock / time controls · an AI opponent
  (minimax/alpha-beta) · distributed/online play (optimistic concurrency on
  the ply number) · draw by insufficient material.

THE API BELOW IS FIXED so the tests at the bottom can run against your code.
Run this file: all checks should print PASS, then ALL PASSED.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


# ----------------------------------------------------------------------------
# Enums, exceptions, and small data types — given, not part of the exercise.
# ----------------------------------------------------------------------------
class Color(Enum):
    WHITE = "white"
    BLACK = "black"

    @property
    def other(self) -> "Color":
        return Color.BLACK if self is Color.WHITE else Color.WHITE


class PieceType(Enum):
    KING = "K"
    QUEEN = "Q"
    ROOK = "R"
    BISHOP = "B"
    KNIGHT = "N"
    PAWN = "P"


class Status(Enum):
    IN_PROGRESS = "in_progress"
    WHITE_WINS = "white_wins"       # White delivered checkmate
    BLACK_WINS = "black_wins"       # Black delivered checkmate
    STALEMATE = "stalemate"


class IllegalMove(Exception): ...


Position = tuple[int, int]          # (row, col); row 0 = rank 1, col 0 = file a
FILES = "abcdefgh"


def square_to_pos(square: str) -> Position:
    if len(square) != 2 or square[0] not in FILES or square[1] not in "12345678":
        raise ValueError(f"invalid square: {square!r}")
    return (int(square[1]) - 1, FILES.index(square[0]))


def pos_to_square(pos: Position) -> str:
    r, c = pos
    return f"{FILES[c]}{r + 1}"


@dataclass(frozen=True, slots=True)
class Move:
    frm: Position
    to: Position
    is_castle_kingside: bool = False
    is_castle_queenside: bool = False
    is_en_passant: bool = False


# ----------------------------------------------------------------------------
# Pieces -- each concrete type owns its movement pattern. ChessGame must
# never branch on piece type; it only calls these polymorphically.
# ----------------------------------------------------------------------------
class Piece:
    """Shared piece state. Concrete subclasses implement `pseudo_legal_moves`:
    the squares this piece could move to on the given board, following its
    own pattern and never landing on a friendly piece. It does NOT know
    about king safety -- that filter belongs in ChessGame."""

    type: PieceType

    def __init__(self, color: Color) -> None:
        self.color = color
        self.has_moved = False

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        raise NotImplementedError

    def attacked_squares(self, board: "Board", pos: Position) -> list[Position]:
        """Squares this piece threatens, for check detection. Identical to
        its move pattern for every piece except the pawn (see Pawn)."""
        return self.pseudo_legal_moves(board, pos)

    def __repr__(self) -> str:
        return f"{self.color.value[0]}{self.type.value}"


def _sliding_moves(board: "Board", pos: Position, color: Color,
                    directions: tuple[tuple[int, int], ...]) -> list[Position]:
    """YOUR CODE HERE — shared helper for Rook, Bishop, Queen: walk each
    direction until the edge of the board, a capture (include it, then
    stop), or a friendly piece (stop before it)."""
    raise NotImplementedError


class King(Piece):
    type = PieceType.KING

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        raise NotImplementedError


class Queen(Piece):
    type = PieceType.QUEEN
    DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        raise NotImplementedError


class Rook(Piece):
    type = PieceType.ROOK
    DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        raise NotImplementedError


class Bishop(Piece):
    type = PieceType.BISHOP
    DIRECTIONS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        raise NotImplementedError


class Knight(Piece):
    type = PieceType.KNIGHT
    OFFSETS = ((1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        raise NotImplementedError


class Pawn(Piece):
    type = PieceType.PAWN

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        raise NotImplementedError

    def attacked_squares(self, board: "Board", pos: Position) -> list[Position]:
        # A pawn threatens both diagonals regardless of whether anything is
        # actually there -- different from its move pattern above.
        raise NotImplementedError


_PIECE_CLASSES: dict[PieceType, type[Piece]] = {
    PieceType.KING: King, PieceType.QUEEN: Queen, PieceType.ROOK: Rook,
    PieceType.BISHOP: Bishop, PieceType.KNIGHT: Knight, PieceType.PAWN: Pawn,
}


# ----------------------------------------------------------------------------
# Board
# ----------------------------------------------------------------------------
class Board:
    def __init__(self) -> None:
        # YOUR CODE HERE — an 8x8 grid of Piece | None, set to the standard
        # starting position (back rank + pawns, both colors).
        raise NotImplementedError

    def piece_at(self, pos: Position) -> Piece | None:
        raise NotImplementedError

    def set_piece(self, pos: Position, piece: Piece | None) -> None:
        raise NotImplementedError

    def king_position(self, color: Color) -> Position:
        raise NotImplementedError

    def is_square_attacked(self, pos: Position, by_color: Color) -> bool:
        raise NotImplementedError

    def is_in_check(self, color: Color) -> bool:
        raise NotImplementedError

    def clone(self) -> "Board":
        """A deep-enough copy for a throwaway legality check: same piece
        types, colors, and has_moved flags, but mutating the clone must
        never affect the original."""
        raise NotImplementedError

    def apply_move(self, mv: Move, promotion: PieceType | None = None) -> None:
        """The one place that mutates a board: ordinary moves, captures,
        castling's rook hop, en passant's removal of the captured pawn (not
        on `to`), and promotion's piece replacement."""
        raise NotImplementedError

    def pieces_of(self, color: Color) -> list[tuple[Position, Piece]]:
        raise NotImplementedError


# ----------------------------------------------------------------------------
# Special-move rule objects -- deliberately NOT methods on King/Pawn, so each
# rule's real preconditions live in exactly one place.
# ----------------------------------------------------------------------------
class CastlingRule:
    @staticmethod
    def candidate_moves(board: Board, color: Color, king_pos: Position) -> list[Move]:
        """King and rook never moved, path between them clear, king not
        currently in check, and king does not pass through or land on an
        attacked square. Returns 0, 1, or 2 castling Moves."""
        raise NotImplementedError


class EnPassantRule:
    @staticmethod
    def candidate_move(board: Board, color: Color, pawn_pos: Position,
                        target: Position | None) -> Move | None:
        """`target` is the current en-passant target square, if any (the
        square a pawn just double-stepped through). Returns a Move only if
        `pawn_pos` is one of the two pawns that could capture onto it."""
        raise NotImplementedError


class PromotionRule:
    LAST_RANK = {Color.WHITE: 7, Color.BLACK: 0}
    PROMOTABLE = (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT)

    @staticmethod
    def requires_promotion(piece: Piece, to_pos: Position) -> bool:
        raise NotImplementedError

    @staticmethod
    def validate(promotion: PieceType | None) -> None:
        """Raises IllegalMove if `promotion` isn't one of PROMOTABLE."""
        raise NotImplementedError


# ----------------------------------------------------------------------------
# Game
# ----------------------------------------------------------------------------
class ChessGame:
    def __init__(self) -> None:
        # YOUR CODE HERE — the tests below reach into these attributes
        # directly (via the _set_position test helper and _all_legal_moves),
        # so name them exactly: self._board (a Board), self.turn (a Color,
        # White first), self.status (a Status), self._en_passant_target
        # (Position | None, the square a pawn just double-stepped through).
        raise NotImplementedError

    def piece_at(self, square: str) -> tuple[Color, PieceType] | None:
        raise NotImplementedError

    def in_check(self, color: Color | None = None) -> bool:
        """Defaults to the side to move."""
        raise NotImplementedError

    def legal_moves(self, square: str) -> list[str]:
        """Every square this piece may legally move to right now (empty if
        it's not this piece's turn, the square is empty, or there simply
        are none)."""
        raise NotImplementedError

    def move(self, from_sq: str, to_sq: str, promotion: PieceType | None = None) -> Status:
        """Applies the move if legal and returns the game's Status
        afterward; otherwise raises IllegalMove and changes nothing."""
        raise NotImplementedError

    @property
    def winner(self) -> Color | None:
        raise NotImplementedError

    def _all_legal_moves(self, color: Color) -> list[Move]:
        """Every legal move for every one of `color`'s pieces — the tests
        call this directly, and `move()`/checkmate/stalemate detection need
        it too: the side to move has zero legal moves iff this is empty."""
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


def _set_position(game: ChessGame, placement: dict[str, Piece], turn: Color) -> ChessGame:
    """Test-only helper: wipe the board and place exactly `placement`, so
    check/checkmate/stalemate/pin/castling positions can be built directly
    instead of forced through a long move sequence."""
    for r in range(8):
        for c in range(8):
            game._board.set_piece((r, c), None)
    for square, piece in placement.items():
        game._board.set_piece(square_to_pos(square), piece)
    game.turn = turn
    game._en_passant_target = None
    game.status = game._compute_status()
    return game


def run_tests() -> bool:
    all_ok = True

    print("--- piece movement and capturing, one representative position per type ---")
    rook_expected = {"d5", "d6", "d7", "d3", "d2", "d1", "e4", "f4", "g4", "h4", "c4", "b4", "a4"}
    g = _set_position(ChessGame(), {
        "a1": King(Color.WHITE), "d4": Rook(Color.WHITE),
        "d7": Pawn(Color.BLACK), "a8": King(Color.BLACK),
    }, Color.WHITE)
    all_ok &= _check("rook: slides any direction, stops at the edge or a capture",
                     set(g.legal_moves("d4")) == rook_expected)
    g.move("d4", "d7")
    all_ok &= _check("rook capture removes the enemy piece",
                     g.piece_at("d7") == (Color.WHITE, PieceType.ROOK) and g.piece_at("d4") is None)

    bishop_expected = {"e5", "f6", "g7", "c5", "b6", "a7", "e3", "f2", "g1", "c3", "b2"}
    g = _set_position(ChessGame(), {
        "a1": King(Color.WHITE), "d4": Bishop(Color.WHITE),
        "g7": Pawn(Color.BLACK), "a8": King(Color.BLACK),
    }, Color.WHITE)
    all_ok &= _check("bishop: diagonals only, blocked by its own king on a1",
                     set(g.legal_moves("d4")) == bishop_expected)
    g.move("d4", "g7")
    all_ok &= _check("bishop capture removes the enemy piece", g.piece_at("g7") == (Color.WHITE, PieceType.BISHOP))

    knight_expected = {"f5", "b5", "f3", "b3", "e6", "c6", "e2", "c2"}
    g = _set_position(ChessGame(), {
        "a1": King(Color.WHITE), "d4": Knight(Color.WHITE),
        "e6": Pawn(Color.BLACK), "a8": King(Color.BLACK),
    }, Color.WHITE)
    all_ok &= _check("knight: the eight L-shaped jumps", set(g.legal_moves("d4")) == knight_expected)
    g.move("d4", "e6")
    all_ok &= _check("knight capture removes the enemy piece", g.piece_at("e6") == (Color.WHITE, PieceType.KNIGHT))

    queen_expected = rook_expected | bishop_expected
    g = _set_position(ChessGame(), {
        "a1": King(Color.WHITE), "d4": Queen(Color.WHITE),
        "d7": Pawn(Color.BLACK), "g7": Pawn(Color.BLACK), "a8": King(Color.BLACK),
    }, Color.WHITE)
    all_ok &= _check("queen: rook moves union bishop moves", set(g.legal_moves("d4")) == queen_expected)

    g = _set_position(ChessGame(), {"d4": King(Color.WHITE), "a8": King(Color.BLACK)}, Color.WHITE)
    all_ok &= _check("king: the eight adjacent squares",
                     set(g.legal_moves("d4")) == {"c3", "d3", "e3", "c4", "e4", "c5", "d5", "e5"})

    g = ChessGame()
    all_ok &= _check("pawn: one or two squares from its start rank", set(g.legal_moves("e2")) == {"e3", "e4"})
    g.move("e2", "e4")
    g.move("d7", "d5")
    g.move("e4", "d5")
    all_ok &= _check("pawn capture is diagonal-only",
                     g.piece_at("d5") == (Color.WHITE, PieceType.PAWN) and g.piece_at("e4") is None)

    print("\n--- a pinned piece may not move even though its own pattern allows it ---")
    g = _set_position(ChessGame(), {
        "e1": King(Color.WHITE), "e2": Bishop(Color.WHITE),
        "e8": Rook(Color.BLACK), "a8": King(Color.BLACK),
    }, Color.WHITE)
    all_ok &= _check("pinned bishop has zero legal moves (every one opens the e-file)",
                     g.legal_moves("e2") == [])
    all_ok &= _check("moving the pinned bishop raises IllegalMove",
                     _raises(IllegalMove, lambda: g.move("e2", "d3")))
    all_ok &= _check("the rejected move changed nothing",
                     g.piece_at("e2") == (Color.WHITE, PieceType.BISHOP) and g.piece_at("e8") == (Color.BLACK, PieceType.ROOK))

    print("\n--- Fool's Mate: a real checkmate played out move by move ---")
    g = ChessGame()
    g.move("f2", "f3")
    g.move("e7", "e5")
    g.move("g2", "g4")
    g.move("d8", "h4")
    all_ok &= _check("White is checkmated in two moves", g.status is Status.BLACK_WINS)
    all_ok &= _check("White is in check and has no legal moves anywhere",
                     g.in_check(Color.WHITE) and not g._all_legal_moves(Color.WHITE))
    all_ok &= _check("winner is Black", g.winner is Color.BLACK)

    print("\n--- a constructed stalemate: zero legal moves, and NOT in check ---")
    g = _set_position(ChessGame(), {
        "h8": King(Color.BLACK), "f7": King(Color.WHITE), "g6": Queen(Color.WHITE),
    }, Color.BLACK)
    all_ok &= _check("stalemate, not checkmate", g.status is Status.STALEMATE)
    all_ok &= _check("the stalemated side is not in check", not g.in_check(Color.BLACK))
    all_ok &= _check("no legal moves for the lone king", g.legal_moves("h8") == [])
    all_ok &= _check("stalemate has no winner", g.winner is None)

    print("\n--- castling: legal kingside and queenside ---")
    g = _set_position(ChessGame(), {
        "e1": King(Color.WHITE), "h1": Rook(Color.WHITE), "e8": King(Color.BLACK),
    }, Color.WHITE)
    g.move("e1", "g1")
    all_ok &= _check("kingside castle moves both the king and the rook",
                     g.piece_at("g1") == (Color.WHITE, PieceType.KING)
                     and g.piece_at("f1") == (Color.WHITE, PieceType.ROOK)
                     and g.piece_at("h1") is None and g.piece_at("e1") is None)

    g = _set_position(ChessGame(), {
        "e1": King(Color.WHITE), "a1": Rook(Color.WHITE), "e8": King(Color.BLACK),
    }, Color.WHITE)
    g.move("e1", "c1")
    all_ok &= _check("queenside castle moves both the king and the rook",
                     g.piece_at("c1") == (Color.WHITE, PieceType.KING)
                     and g.piece_at("d1") == (Color.WHITE, PieceType.ROOK)
                     and g.piece_at("a1") is None)

    print("--- castling: illegal once the king has moved (even back to start) ---")
    g = _set_position(ChessGame(), {
        "e1": King(Color.WHITE), "h1": Rook(Color.WHITE), "e8": King(Color.BLACK),
    }, Color.WHITE)
    g.move("e1", "f1")
    g.move("e8", "d8")
    g.move("f1", "e1")
    g.move("d8", "e8")
    all_ok &= _check("king back on e1, but has_moved sticks -> castling is illegal",
                     _raises(IllegalMove, lambda: g.move("e1", "g1")))

    print("--- castling: illegal through/into check ---")
    g = _set_position(ChessGame(), {
        "e1": King(Color.WHITE), "h1": Rook(Color.WHITE),
        "f8": Rook(Color.BLACK), "a8": King(Color.BLACK),
    }, Color.WHITE)
    all_ok &= _check("f1 is attacked by the black rook -> can't castle through it",
                     _raises(IllegalMove, lambda: g.move("e1", "g1")))
    all_ok &= _check("the rejected castle changed nothing",
                     g.piece_at("e1") == (Color.WHITE, PieceType.KING) and g.piece_at("h1") == (Color.WHITE, PieceType.ROOK))

    print("\n--- en passant: legal on the very next move ---")
    g = ChessGame()
    g.move("e2", "e4")
    g.move("a7", "a6")
    g.move("e4", "e5")
    g.move("d7", "d5")
    g.move("e5", "d6")
    all_ok &= _check("en passant captures the pawn beside it, not on the landing square",
                     g.piece_at("d6") == (Color.WHITE, PieceType.PAWN) and g.piece_at("d5") is None and g.piece_at("e5") is None)

    print("--- en passant: illegal once the window has passed ---")
    g = ChessGame()
    g.move("e2", "e4")
    g.move("a7", "a6")
    g.move("e4", "e5")
    g.move("d7", "d5")
    g.move("a2", "a3")
    g.move("a6", "a5")
    all_ok &= _check("one move later, the same capture is no longer legal",
                     _raises(IllegalMove, lambda: g.move("e5", "d6")))

    print("\n--- promotion: to a queen, and the promoted piece moves like one ---")
    g = _set_position(ChessGame(), {
        "e7": Pawn(Color.WHITE), "g1": King(Color.WHITE), "a1": King(Color.BLACK),
    }, Color.WHITE)
    all_ok &= _check("promotion is required, not optional", _raises(IllegalMove, lambda: g.move("e7", "e8")))
    g.move("e7", "e8", promotion=PieceType.QUEEN)
    all_ok &= _check("the pawn is now a queen", g.piece_at("e8") == (Color.WHITE, PieceType.QUEEN))
    g.turn = Color.WHITE   # peek at the promoted piece's own moves before Black replies
    all_ok &= _check("it immediately moves like a queen (diagonal and straight both work)",
                     "a4" in g.legal_moves("e8") and "e2" in g.legal_moves("e8"))

    print("--- promotion: to a knight ---")
    g = _set_position(ChessGame(), {
        "h7": Pawn(Color.WHITE), "g1": King(Color.WHITE), "a1": King(Color.BLACK),
    }, Color.WHITE)
    g.move("h7", "h8", promotion=PieceType.KNIGHT)
    all_ok &= _check("the pawn is now a knight", g.piece_at("h8") == (Color.WHITE, PieceType.KNIGHT))
    g.turn = Color.WHITE   # peek at the promoted piece's own moves before Black replies
    all_ok &= _check("it immediately moves like a knight, not a rook",
                     set(g.legal_moves("h8")) == {"f7", "g6"})

    print("\n--- rejected moves change nothing ---")
    fresh = ChessGame()
    all_ok &= _check("Black may not move first", _raises(IllegalMove, lambda: fresh.move("e7", "e5")))
    all_ok &= _check("still White's turn", fresh.turn is Color.WHITE)
    all_ok &= _check("moving from an empty square", _raises(IllegalMove, lambda: fresh.move("e4", "e5")))
    all_ok &= _check("a pawn cannot jump three squares", _raises(IllegalMove, lambda: fresh.move("e2", "e5")))
    all_ok &= _check("nothing about the position changed",
                     fresh.piece_at("e2") == (Color.WHITE, PieceType.PAWN)
                     and fresh.status is Status.IN_PROGRESS and fresh.turn is Color.WHITE)
    return all_ok
# ================================================================= END TESTS ==


if __name__ == "__main__":
    ok = run_tests()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
