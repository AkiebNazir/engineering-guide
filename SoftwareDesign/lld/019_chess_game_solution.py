"""
================================================================================
SOLUTION · LLD 019 · Chess (move validation + check / checkmate)   [Tier 2]
================================================================================

THE CORE IDEA
--------------
Two things vary, so both get their own seam:

    1. HOW a piece moves           -> Piece.pseudo_legal_moves(board, pos)
                                       overridden per concrete piece type
                                       (King, Queen, Rook, Bishop, Knight,
                                       Pawn). Sliding pieces (Rook, Bishop,
                                       Queen) share a `_sliding_moves` helper
                                       for "walk a direction until you hit
                                       the edge, an enemy (capture, stop), or
                                       a friendly piece (stop before it)".
    2. WHETHER a pseudo-legal move is actually LEGAL -> simulate it.
       A pseudo-legal move follows the piece's pattern and doesn't move
       through/onto your own pieces, but it is only legal if playing it does
       not leave your own king in check. ChessGame._legal_moves_at() clones
       the board, applies the candidate move to the clone, checks
       `clone.is_in_check(mover_color)`, and discards the clone. This is the
       one mechanism every other rule builds on -- it is also exactly how a
       pinned piece is caught (see the pin trace below) and how "does this
       castle pass through check" and "checkmate vs. stalemate" both reduce
       to "count how many candidates survive simulation".

The three special moves are each their own rule object, not baked into a
piece's movement pattern:
    CastlingRule    -- king/rook never moved, path clear, king not in/through/
                       into check. Emits a Move with is_castle_kingside/
                       queenside=True; Board.apply_move moves the rook too.
    EnPassantRule   -- needs one bit of history (the file a pawn just double-
                       stepped through), tracked as ChessGame._en_passant_target
                       and cleared on every move that isn't a new double step.
    PromotionRule   -- a pawn reaching the last rank must be replaced; the
                       caller's `promotion` argument picks which piece.


================================================================================
REQUIREMENTS (agreed in the first 5 minutes)
================================================================================
  1. Standard 8x8 board, 2 colors, 6 piece types, White moves first.
  2. Each piece type generates its own moves (polymorphism), not one big
     if/elif on piece type.
  3. move(from_sq, to_sq, promotion=None) -> Status. Rejects (IllegalMove,
     board unchanged): wrong color's turn, empty square, a destination not
     in that piece's legal-move set -- including a pseudo-legal move that
     would leave the mover's own king in check.
  4. is_in_check(color); checkmate = zero legal moves while in check;
     stalemate = zero legal moves while NOT in check.
  5. Castling (both sides), en passant, promotion -- each as an explicit
     rule, with their real preconditions (see above).
  Out of scope (see the question file's docstring): 50-move rule, threefold
  repetition, algebraic notation (SAN) parsing/generation, draw offers, a
  clock -- these are FOLLOW-UPS, not implemented here.


================================================================================
ENTITIES AND INVARIANTS
================================================================================
    Color, PieceType, Status    enums
    Position                    (row, col), row 0 = rank 1, col 0 = file a
    Move                        frm, to, + which special rule (if any) applies
    Piece                       color, has_moved, pseudo_legal_moves(),
                                 attacked_squares() (same as moves, except
                                 Pawn: it attacks diagonally regardless of
                                 whether that square is occupied)
    Board                       8x8 grid of Piece | None
                                 INVARIANT: exactly one king per color, always
                                 (a move that would capture the enemy king can
                                 never be legal, because it would mean the
                                 previous ply ended in checkmate and the game
                                 would already be over)
    CastlingRule / EnPassantRule / PromotionRule   stateless rule objects
    ChessGame                   board, turn, status, en_passant_target
                                 INVARIANT: status != IN_PROGRESS => move()
                                 always raises; the side to move always has
                                 >= 1 legal move whenever status == IN_PROGRESS


================================================================================
TRACE · why a pinned piece is illegal to move (the simulate-then-check step)
================================================================================
    White King e1, White Bishop e2, Black Rook e8 (rook "sees" e1 through the
    e-file once the bishop steps aside).

    legal_moves("e2") candidates from Bishop.pseudo_legal_moves: d3, c4, b5,
    a6, f3, g4, h5, d1, f1 (the bishop's own pattern doesn't know about pins).

    For EVERY candidate, e.g. e2->d3:
        clone = board.clone()
        clone.apply_move(Move(e2, d3))       # bishop leaves the e-file
        clone.is_in_check(WHITE)?            # king_position(WHITE) = e1
                                              # is_square_attacked(e1, BLACK)?
                                              # rook e8's pseudo_legal_moves
                                              # now reach all the way to e1
                                              # -> True
        -> discarded, not legal

    Every candidate fails the same way (moving off the e-file always opens
    the file), so legal_moves("e2") == [] even though the bishop "can" move
    nine different ways per its own pattern. That's the whole point of
    simulating rather than special-casing pins: no separate "is this piece
    pinned" code path exists, it falls out of the general check.


================================================================================
DESIGN DECISIONS AND ALTERNATIVES
================================================================================
  * pseudo_legal_moves() never checks king safety -- it only knows "my own
    pattern, don't land on my own piece". King safety is one shared filter
    in ChessGame, applied uniformly to every piece type and every special
    move. Alternative (rejected): give every piece a `legal_moves` that
    checks king safety itself -- duplicates the same clone-and-check logic
    six times and makes castling/en passant harder to slot in.
  * attacked_squares() is a separate method from pseudo_legal_moves() only
    because of the pawn: a pawn threatens its diagonals whether or not an
    enemy piece is standing there (needed to know if a king may not step
    there), but it may only *move* diagonally when there IS an enemy piece
    there. Every other piece's attacked_squares() is just its move pattern.
  * Castling/en passant/promotion are rule objects invoked from ChessGame,
    not methods on King/Pawn -- keeps each Piece subclass to "my movement
    pattern" only, and keeps each special rule's preconditions in one place
    instead of smeared across piece classes and the game loop.
  * Board.apply_move() is the single place that mutates a board (capture,
    castling's rook hop, en passant's removal, promotion's replacement). It
    is used both for real moves and for the throwaway clones legality
    checks simulate on, so there is exactly one implementation of "what a
    move does to a board" to get right.
  * No undo stack (unlike 008/017): nothing here needs to replay history,
    and legality checking clones instead of make/unmake, trading some speed
    for a much smaller Board API.
  * Board is a flat 8x8 list of Piece | None, not bitboards -- bitboards are
    the right answer for a real engine's search speed, worth mentioning as
    an optimisation, not the first design.


================================================================================
COMPLEXITY
================================================================================
    legal_moves(square)   O(moves for that piece x board clone O(64))
    _all_legal_moves()    O(pieces x moves each x clone O(64)) ~ a few
                           thousand basic ops per call at a normal board
                           density -- fine for an interview-scale engine,
                           not for a search-heavy chess AI (which would want
                           make/unmake instead of cloning).
    is_square_attacked    O(64) -- scan every square, ask its piece
    Space                 O(64) for the board, O(1) extra per legal-move check


================================================================================
EDGE CASES
================================================================================
  * A pseudo-legal move that exposes your own king (the pin trace above).
  * Castling: king or rook has moved (even if it moved back); king in check
    right now; king passes through an attacked square; king lands on an
    attacked square; a piece stands between king and rook.
  * En passant only on the ply immediately after the qualifying two-square
    push -- any other move in between clears the eligibility.
  * Promotion is required, not optional, once a pawn reaches the last rank;
    the promoted piece's new movement applies immediately (a promoted queen
    can move like a queen on the very next legal_moves() call).
  * Checkmate vs. stalemate differ only in `is_in_check` -- both are "zero
    legal moves for the side to move".
  * A capture on the last empty escape square still has to be verified with
    the same simulate-then-check step as any other move (capturing doesn't
    get a legality shortcut).


================================================================================
COMMON MISTAKES
================================================================================
  1. Generating "legal" moves straight from each piece's pattern and never
     simulating -- silently allows moving a pinned piece, or "escaping"
     check by making an unrelated move.
  2. Baking castling into King.pseudo_legal_moves -- then the king "can"
     castle out of check because the general king-move code has no concept
     of "the rook hasn't moved" or "passes through check".
  3. Treating a pawn's attacked squares as identical to its move squares --
     then a king is allowed to step next to a pawn it isn't actually safe
     from (the diagonal-empty-square case), or, in the other direction, a
     forward pawn push is wrongly treated as covering the square ahead.
  4. En passant with no expiry -- capturable forever once the flag is set,
     instead of only on the very next move.
  5. Mutating the real board to "try" a move, checking check, and forgetting
     to always undo it on every code path (including exceptions) -- cloning
     sidesteps this whole class of bug at some memory cost.
  6. Off-by-one on promotion rank per color (white promotes on rank 8 / row
     7, black on rank 1 / row 0 -- easy to swap).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
  * 50-move rule / threefold repetition -> a position-hash counter and a
    halfmove-since-capture-or-pawn-move counter; both are pure additions on
    top of the same Board/Move machinery, no change to legality checking.
  * SAN (e.g. "Nxf6+") parsing/generation -> a formatting/parsing layer on
    top of legal_moves(), disambiguating by rank/file only when two like
    pieces can reach the same square.
  * A clock / time controls -> orthogonal to legality; a wrapper around
    move() that also stops the mover's clock and starts the opponent's.
  * Distributed/online play -> ChessGame behind a service; moves carry an
    expected ply number (optimistic concurrency) so a stale client's move
    is rejected instead of silently desyncing both sides.
  * AI opponent -> minimax/alpha-beta over _all_legal_moves(); cloning is
    too slow for deep search, so a real engine swaps to make/unmake plus
    bitboards for attack generation.
  * Draw by insufficient material -> a static check on the remaining piece
    set (e.g. king + bishop vs. king) run after every capture.


================================================================================
RELATED
================================================================================
  lld/008_tic_tac_toe        (win/status detection, polymorphic players)
  lld/002_elevator_system    (state as enum)
  SoftwareDesign/04_design_patterns_in_practice.md  §3 Strategy (rule objects),
                                                     §7 Template Method (_sliding_moves)
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum


# ----------------------------------------------------------------------------
# Enums, exceptions, and small data types
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
# Pieces -- each concrete type owns its movement pattern (the polymorphism
# the key design point asks for). ChessGame never branches on piece type.
# ----------------------------------------------------------------------------
class Piece:
    """Shared piece state, plus the default 'what does this piece attack'
    rule. Concrete subclasses implement `pseudo_legal_moves`: the squares
    this piece could move to on the given board, following its own pattern
    and never landing on a friendly piece. It does NOT know about king
    safety -- that filter lives in ChessGame (see the module docstring)."""

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
    """Shared 'walk each direction until the edge / a capture / a friendly
    piece' helper for Rook, Bishop, and Queen."""
    r, c = pos
    moves: list[Position] = []
    for dr, dc in directions:
        nr, nc = r + dr, c + dc
        while 0 <= nr < 8 and 0 <= nc < 8:
            occupant = board.piece_at((nr, nc))
            if occupant is None:
                moves.append((nr, nc))
            else:
                if occupant.color != color:
                    moves.append((nr, nc))          # capture, then stop
                break
            nr, nc = nr + dr, nc + dc
    return moves


class King(Piece):
    type = PieceType.KING

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        r, c = pos
        moves = []
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < 8 and 0 <= nc < 8:
                    occ = board.piece_at((nr, nc))
                    if occ is None or occ.color != self.color:
                        moves.append((nr, nc))
        return moves


class Queen(Piece):
    type = PieceType.QUEEN
    DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1), (1, 1), (1, -1), (-1, 1), (-1, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        return _sliding_moves(board, pos, self.color, self.DIRECTIONS)


class Rook(Piece):
    type = PieceType.ROOK
    DIRECTIONS = ((1, 0), (-1, 0), (0, 1), (0, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        return _sliding_moves(board, pos, self.color, self.DIRECTIONS)


class Bishop(Piece):
    type = PieceType.BISHOP
    DIRECTIONS = ((1, 1), (1, -1), (-1, 1), (-1, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        return _sliding_moves(board, pos, self.color, self.DIRECTIONS)


class Knight(Piece):
    type = PieceType.KNIGHT
    OFFSETS = ((1, 2), (1, -2), (-1, 2), (-1, -2), (2, 1), (2, -1), (-2, 1), (-2, -1))

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        r, c = pos
        moves = []
        for dr, dc in self.OFFSETS:
            nr, nc = r + dr, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                occ = board.piece_at((nr, nc))
                if occ is None or occ.color != self.color:
                    moves.append((nr, nc))
        return moves


class Pawn(Piece):
    type = PieceType.PAWN

    def pseudo_legal_moves(self, board: "Board", pos: Position) -> list[Position]:
        r, c = pos
        direction = 1 if self.color is Color.WHITE else -1
        start_row = 1 if self.color is Color.WHITE else 6
        moves = []
        one = (r + direction, c)
        if 0 <= one[0] < 8 and board.piece_at(one) is None:
            moves.append(one)
            two = (r + 2 * direction, c)
            if r == start_row and board.piece_at(two) is None:
                moves.append(two)
        for dc in (-1, 1):
            nr, nc = r + direction, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                occ = board.piece_at((nr, nc))
                if occ is not None and occ.color != self.color:
                    moves.append((nr, nc))
        return moves

    def attacked_squares(self, board: "Board", pos: Position) -> list[Position]:
        # A pawn threatens both diagonals regardless of whether anything is
        # actually there -- this is what keeps an enemy king from stepping
        # next to it, and is different from its move pattern above.
        r, c = pos
        direction = 1 if self.color is Color.WHITE else -1
        squares = []
        for dc in (-1, 1):
            nr, nc = r + direction, c + dc
            if 0 <= nr < 8 and 0 <= nc < 8:
                squares.append((nr, nc))
        return squares


_PIECE_CLASSES: dict[PieceType, type[Piece]] = {
    PieceType.KING: King, PieceType.QUEEN: Queen, PieceType.ROOK: Rook,
    PieceType.BISHOP: Bishop, PieceType.KNIGHT: Knight, PieceType.PAWN: Pawn,
}


# ----------------------------------------------------------------------------
# Board
# ----------------------------------------------------------------------------
class Board:
    def __init__(self) -> None:
        self._grid: list[list[Piece | None]] = [[None] * 8 for _ in range(8)]
        back_rank = [Rook, Knight, Bishop, Queen, King, Bishop, Knight, Rook]
        for col, cls in enumerate(back_rank):
            self._grid[0][col] = cls(Color.WHITE)
            self._grid[7][col] = cls(Color.BLACK)
        for col in range(8):
            self._grid[1][col] = Pawn(Color.WHITE)
            self._grid[6][col] = Pawn(Color.BLACK)

    def piece_at(self, pos: Position) -> Piece | None:
        r, c = pos
        return self._grid[r][c]

    def set_piece(self, pos: Position, piece: Piece | None) -> None:
        r, c = pos
        self._grid[r][c] = piece

    def king_position(self, color: Color) -> Position:
        for r in range(8):
            for c in range(8):
                p = self._grid[r][c]
                if p is not None and p.type is PieceType.KING and p.color is color:
                    return (r, c)
        raise ValueError(f"no {color.value} king on the board")

    def is_square_attacked(self, pos: Position, by_color: Color) -> bool:
        for r in range(8):
            for c in range(8):
                p = self._grid[r][c]
                if p is not None and p.color is by_color and pos in p.attacked_squares(self, (r, c)):
                    return True
        return False

    def is_in_check(self, color: Color) -> bool:
        return self.is_square_attacked(self.king_position(color), color.other)

    def clone(self) -> "Board":
        new = Board.__new__(Board)
        new._grid = [[None] * 8 for _ in range(8)]
        for r in range(8):
            for c in range(8):
                p = self._grid[r][c]
                if p is not None:
                    copy = type(p)(p.color)
                    copy.has_moved = p.has_moved
                    new._grid[r][c] = copy
        return new

    def apply_move(self, mv: Move, promotion: PieceType | None = None) -> None:
        piece = self.piece_at(mv.frm)
        if piece is None:
            raise ValueError(f"no piece on {mv.frm} to move")
        self.set_piece(mv.frm, None)
        if mv.is_en_passant:
            self.set_piece((mv.frm[0], mv.to[1]), None)     # the captured pawn, not on `to`
        if mv.is_castle_kingside or mv.is_castle_queenside:
            row = mv.frm[0]
            rook_from = (row, 7) if mv.is_castle_kingside else (row, 0)
            rook_to = (row, 5) if mv.is_castle_kingside else (row, 3)
            rook = self.piece_at(rook_from)
            self.set_piece(rook_from, None)
            self.set_piece(rook_to, rook)
            if rook is not None:
                rook.has_moved = True
        if piece.type is PieceType.PAWN and mv.to[0] in (0, 7):
            piece = _PIECE_CLASSES[promotion or PieceType.QUEEN](piece.color)
        piece.has_moved = True
        self.set_piece(mv.to, piece)

    def pieces_of(self, color: Color) -> list[tuple[Position, Piece]]:
        return [((r, c), p) for r in range(8) for c in range(8)
                if (p := self._grid[r][c]) is not None and p.color is color]


# ----------------------------------------------------------------------------
# Special-move rule objects -- deliberately NOT methods on King/Pawn, so each
# rule's real preconditions live in exactly one place.
# ----------------------------------------------------------------------------
class CastlingRule:
    @staticmethod
    def candidate_moves(board: Board, color: Color, king_pos: Position) -> list[Move]:
        king = board.piece_at(king_pos)
        if king is None or king.has_moved or board.is_in_check(color):
            return []
        row = king_pos[0]
        moves: list[Move] = []
        rook = board.piece_at((row, 7))
        if (rook is not None and rook.type is PieceType.ROOK and not rook.has_moved
                and board.piece_at((row, 5)) is None and board.piece_at((row, 6)) is None
                and not board.is_square_attacked((row, 5), color.other)
                and not board.is_square_attacked((row, 6), color.other)):
            moves.append(Move(king_pos, (row, 6), is_castle_kingside=True))
        rook = board.piece_at((row, 0))
        if (rook is not None and rook.type is PieceType.ROOK and not rook.has_moved
                and board.piece_at((row, 1)) is None and board.piece_at((row, 2)) is None
                and board.piece_at((row, 3)) is None
                and not board.is_square_attacked((row, 3), color.other)
                and not board.is_square_attacked((row, 2), color.other)):
            moves.append(Move(king_pos, (row, 2), is_castle_queenside=True))
        return moves


class EnPassantRule:
    @staticmethod
    def candidate_move(board: Board, color: Color, pawn_pos: Position,
                        target: Position | None) -> Move | None:
        if target is None:
            return None
        r, c = pawn_pos
        direction = 1 if color is Color.WHITE else -1
        if target in ((r + direction, c - 1), (r + direction, c + 1)):
            return Move(pawn_pos, target, is_en_passant=True)
        return None


class PromotionRule:
    LAST_RANK = {Color.WHITE: 7, Color.BLACK: 0}
    PROMOTABLE = (PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP, PieceType.KNIGHT)

    @staticmethod
    def requires_promotion(piece: Piece, to_pos: Position) -> bool:
        return piece.type is PieceType.PAWN and to_pos[0] == PromotionRule.LAST_RANK[piece.color]

    @staticmethod
    def validate(promotion: PieceType | None) -> None:
        if promotion not in PromotionRule.PROMOTABLE:
            raise IllegalMove(f"invalid promotion piece: {promotion}")


# ----------------------------------------------------------------------------
# Game
# ----------------------------------------------------------------------------
class ChessGame:
    def __init__(self) -> None:
        self._board = Board()
        self.turn = Color.WHITE
        self.status = Status.IN_PROGRESS
        self._en_passant_target: Position | None = None

    def piece_at(self, square: str) -> tuple[Color, PieceType] | None:
        piece = self._board.piece_at(square_to_pos(square))
        return None if piece is None else (piece.color, piece.type)

    def in_check(self, color: Color | None = None) -> bool:
        return self._board.is_in_check(color or self.turn)

    def legal_moves(self, square: str) -> list[str]:
        pos = square_to_pos(square)
        piece = self._board.piece_at(pos)
        if piece is None or piece.color is not self.turn:
            return []
        return [pos_to_square(mv.to) for mv in self._legal_moves_at(pos)]

    def move(self, from_sq: str, to_sq: str, promotion: PieceType | None = None) -> Status:
        if self.status is not Status.IN_PROGRESS:
            raise IllegalMove(f"the game is over: {self.status.value}")
        try:
            frm, to = square_to_pos(from_sq), square_to_pos(to_sq)
        except ValueError as exc:
            raise IllegalMove(str(exc)) from exc
        piece = self._board.piece_at(frm)
        if piece is None:
            raise IllegalMove(f"no piece on {from_sq}")
        if piece.color is not self.turn:
            raise IllegalMove(f"it is {self.turn.value}'s move, not {piece.color.value}'s")
        matching = [mv for mv in self._legal_moves_at(frm) if mv.to == to]
        if not matching:
            raise IllegalMove(f"{from_sq}-{to_sq} is not a legal move")
        mv = matching[0]
        if PromotionRule.requires_promotion(piece, to):
            if promotion is None:
                raise IllegalMove(f"a pawn reaching {to_sq} must be promoted; pass `promotion=`")
            PromotionRule.validate(promotion)

        self._board.apply_move(mv, promotion=promotion)
        self._en_passant_target = None
        if piece.type is PieceType.PAWN and abs(to[0] - frm[0]) == 2:
            self._en_passant_target = ((frm[0] + to[0]) // 2, frm[1])
        self.turn = self.turn.other
        self.status = self._compute_status()
        return self.status

    @property
    def winner(self) -> Color | None:
        return {Status.WHITE_WINS: Color.WHITE, Status.BLACK_WINS: Color.BLACK}.get(self.status)

    # -- internals ------------------------------------------------------
    def _legal_moves_at(self, pos: Position) -> list[Move]:
        piece = self._board.piece_at(pos)
        color = piece.color
        candidates = [Move(pos, dest) for dest in piece.pseudo_legal_moves(self._board, pos)]
        if piece.type is PieceType.KING:
            candidates += CastlingRule.candidate_moves(self._board, color, pos)
        if piece.type is PieceType.PAWN:
            ep = EnPassantRule.candidate_move(self._board, color, pos, self._en_passant_target)
            if ep is not None:
                candidates.append(ep)
        legal = []
        for mv in candidates:
            trial = self._board.clone()
            trial.apply_move(mv, promotion=PieceType.QUEEN)   # choice is irrelevant to king safety
            if not trial.is_in_check(color):
                legal.append(mv)
        return legal

    def _all_legal_moves(self, color: Color) -> list[Move]:
        moves = []
        for pos, _piece in self._board.pieces_of(color):
            moves.extend(self._legal_moves_at(pos))
        return moves

    def _compute_status(self) -> Status:
        if self._all_legal_moves(self.turn):
            return Status.IN_PROGRESS
        if self._board.is_in_check(self.turn):
            return Status.BLACK_WINS if self.turn is Color.WHITE else Status.WHITE_WINS
        return Status.STALEMATE


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


def _random_legal_move(game: ChessGame, rng: random.Random) -> tuple[str, str]:
    candidates: list[tuple[str, str]] = []
    for r in range(8):
        for c in range(8):
            sq = pos_to_square((r, c))
            info = game.piece_at(sq)
            if info is not None and info[0] is game.turn:
                for dest in game.legal_moves(sq):
                    candidates.append((sq, dest))
    return rng.choice(candidates)


def run_demos() -> bool:
    all_ok = True
    print("\n--- DEMO: random legal-move self-play, invariants checked after every ply ---")
    rng = random.Random(7)
    n_games, max_plies = 15, 90
    total_plies = 0
    piece_count_violations = 0
    king_count_violations = 0
    move_after_over_violations = 0
    endings = {"checkmate": 0, "stalemate": 0, "move_cap": 0}
    for _ in range(n_games):
        game = ChessGame()
        prev_piece_count = 32
        reached_end = False
        for _ply in range(max_plies):
            if game.status is not Status.IN_PROGRESS:
                reached_end = True
                break
            frm, to = _random_legal_move(game, rng)
            before = game.status
            game.move(frm, to, promotion=PieceType.QUEEN)   # ignored when promotion isn't in play
            total_plies += 1
            if before is not Status.IN_PROGRESS:
                move_after_over_violations += 1

            piece_count, kings = 0, {Color.WHITE: 0, Color.BLACK: 0}
            for r in range(8):
                for c in range(8):
                    p = game._board.piece_at((r, c))
                    if p is not None:
                        piece_count += 1
                        if p.type is PieceType.KING:
                            kings[p.color] += 1
            if piece_count > prev_piece_count:
                piece_count_violations += 1
            prev_piece_count = piece_count
            if kings[Color.WHITE] != 1 or kings[Color.BLACK] != 1:
                king_count_violations += 1
        if not reached_end:
            endings["move_cap"] += 1
            continue
        if game.status is Status.STALEMATE:
            endings["stalemate"] += 1
        else:
            endings["checkmate"] += 1
    print(f"      {n_games} games, {total_plies} total plies played; endings={endings}")
    all_ok &= _check("piece count never increases across any ply", piece_count_violations == 0)
    all_ok &= _check("exactly one king per color present after every ply", king_count_violations == 0)
    all_ok &= _check("move() was never accepted once a game had already ended", move_after_over_violations == 0)
    return all_ok


if __name__ == "__main__":
    ok = run_tests()
    ok &= run_demos()
    print("\nALL PASSED" if ok else "\nFAILURES PRESENT")
