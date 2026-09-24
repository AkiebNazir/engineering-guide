"""
================================================================================
SOLUTION · LeetCode 130 · Surrounded Regions                        [Medium]
https://leetcode.com/problems/surrounded-regions/
================================================================================

THE CORE IDEA
--------------
Flood fill from the OUTSIDE IN, not the inside out. Any `'O'` that is on the
border, or connected through a chain of `'O'`s to a border cell, can NEVER
be captured — by definition it touches the edge. Flood fill from every
border `'O'` and mark everything reached as SAFE. Whatever `'O'` is left
UNMARKED after that single pass is, by construction, fully enclosed by `'X'`
and gets flipped. One pass out from the border, one pass to flip — no
guessing mid-fill about whether a region "will turn out" to reach the edge.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force / naive and WRONG, don't ship): flood-fill from
every interior 'O' region and flip cells to 'X' as you go, THEN check if the
region ever touched a border and undo the flips if so. This requires either
buffering every flip until the region is fully explored (extra memory, and
still error-prone) or a second "undo" pass that re-derives which cells
belonged to which region — the fragile, easy-to-get-wrong version of this
problem. The border-outward approach below sidesteps the whole issue.

Approach 1 (border-outward flood fill, recursive DFS) — CORRECT, but risks
`RecursionError` on a large, single-file corridor of `'O'` cells, because
Python's default recursion limit (`sys.getrecursionlimit()`, usually 1000)
is far smaller than this problem's stated bound of 200*200 = 40,000 cells.
Demonstrated blowing up, live, below.

Approach 2 (border-outward flood fill, iterative BFS/DFS) ✅ — the answer.
Same algorithm, an explicit stack or `collections.deque` instead of the call
stack, so there is no recursion depth to exceed.

    def solve(board):
        rows, cols = len(board), len(board[0])
        SAFE = "#"

        def flood(r, c):
            stack = [(r, c)]
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < rows and 0 <= cc < cols) or board[cr][cc] != "O":
                    continue
                board[cr][cc] = SAFE
                stack.extend([(cr - 1, cc), (cr + 1, cc), (cr, cc - 1), (cr, cc + 1)])

        for r in range(rows):
            for c in (0, cols - 1):
                if board[r][c] == "O":
                    flood(r, c)
        for c in range(cols):
            for r in (0, rows - 1):
                if board[r][c] == "O":
                    flood(r, c)

        for r in range(rows):
            for c in range(cols):
                if board[r][c] == "O":
                    board[r][c] = "X"          # never reached from a border -> captured
                elif board[r][c] == SAFE:
                    board[r][c] = "O"           # restore border-connected cells


================================================================================
STEP BY STEP TRACE
================================================================================
board =
    X X X X
    X O O X
    X X O X
    X O X X

Border 'O' scan: row 0 all X, row 3 (last row) has 'O' at (3,1) -> flood from there.
Left/right columns: col 0 all X, col 3 all X. No other border O's.

flood(3,1): mark (3,1)='#'. Neighbors: (2,1)=X skip, (4,1) out of bounds,
            (3,0)=X skip, (3,2)=X skip. Region has exactly one cell.

    X X X X
    X O O X
    X X O X
    X # X X

Interior region (1,1),(1,2),(2,2) was NEVER reached by the border flood
(it's fully enclosed by X on every side) -> stays plain 'O' through the
whole flood-fill phase.

Final pass: every remaining 'O' -> 'X' (captured); every '#' -> 'O' (restored).

    X X X X
    X X X X
    X X X X
    X O X X

Matches Example 1 exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time         Space           Mutates input?
    ------------------------------------  -----------  --------------  --------------
    Naive flood-then-undo (Approach 0)    O(R*C)        O(R*C)           YES, in place, fragile
    Border-outward, recursive DFS         O(R*C)        O(R*C) call stack YES, in place — but can CRASH
    Border-outward, iterative DFS/BFS ✅   O(R*C)        O(R*C)           YES, in place

    "Mutates input?" is YES for every real approach — the problem explicitly
    requires in-place modification with no return value, matching LC's exact
    signature `solve(self, board) -> None`. The temporary `'#'` marker never
    survives past the function; it's flipped back to `'O'` in the final pass.


================================================================================
EDGE CASES
================================================================================
    entire board is 'X'          -> no border 'O's to seed the flood fill,
                                    final pass finds nothing to flip. Board
                                    unchanged.
    entire board is 'O'          -> every border cell is 'O', the flood
                                    fill reaches the WHOLE board (it's one
                                    connected region touching every edge) ->
                                    nothing is captured, board unchanged
                                    after the restore pass.
    single row or single column   -> EVERY cell is a border cell by
                                    definition (topmost/bottommost/leftmost/
                                    rightmost simultaneously) -> nothing can
                                    ever be captured; exists to check the
                                    border-seeding loop doesn't double-count
                                    or crash when rows==1 or cols==1.
    1x1 board                    -> the single cell is trivially on every
                                    border at once; 'O' stays 'O', 'X' stays
                                    'X'.
    a region that touches the border through a LONG chain, not directly ->
                                    the flood fill must actually walk the
                                    whole chain (BFS/DFS reachability, not
                                    "is any cell of this region literally on
                                    row 0/col 0/etc.") — this is exactly what
                                    breaks a "check each O's own position"
                                    shortcut and exactly what makes a deep
                                    corridor dangerous for recursion (demo below).


================================================================================
COMMON MISTAKES
================================================================================
1. Flood-filling from INTERIOR 'O' cells first and flipping eagerly, then
   trying to detect "oh, this region touched the border after all" and undo
   — fragile, and the undo logic itself is a second flood fill's worth of
   bookkeeping. Flood from the border INWARD instead; nothing needs undoing.
2. Checking only whether an 'O' cell's OWN coordinates are on the border,
   without following the chain of connected 'O's — a region can be captured-
   looking at first glance (no cell of it visually "looks like" the border)
   while still being connected to a border cell through a winding path.
3. Forgetting the temporary marker step and instead trying to flip
   border-reachable cells directly to a FINAL 'O' while capturable cells are
   flipped to 'X' in the SAME pass — you cannot yet tell which is which
   until the border flood fill is fully done; the two-phase marker approach
   exists precisely to defer that decision.
4. **Recursive flood fill on a large, corridor-shaped board** — correct
   algorithm, but Python's default recursion limit is far smaller than the
   40,000-cell worst case this problem allows. Demonstrated crashing, live,
   below.
5. Iterating `for c in (0, cols-1)` and `for r in (0, rows-1)` without
   guarding against `rows==1` or `cols==1`, which would visit the single
   row/column twice — harmless here (flood fill is idempotent on an already-
   marked cell) but wasteful, and a sign the border-seeding logic wasn't
   thought through for the degenerate single-row/column case.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why does the border-outward direction avoid the "undo" problem entirely?
A: A cell's SAFE status (border-connected) can only be discovered by
   walking a path that starts AT the border. Walking inward-out, you don't
   know the answer until you've explored everything; walking outward-in,
   you know the answer (safe) the instant you reach the cell, because you
   started at a cell that's already known-safe (it IS on the border).

Q: How does this relate to 007 (Pacific Atlantic Water Flow)?
A: Same "flood fill from the border inward, mark a status" skeleton. 007
   runs it TWICE (once per ocean) and intersects two SAFE sets; 008 runs it
   ONCE (there's only one "safe" category: border-connected) and then flips
   everything NOT marked. 007 needs a separate visited set per pass because
   the grid is read twice; 008 mutates in place because the board is only
   ever flood-filled once, in one direction, then finalized.

Q: What if the board could also connect diagonally?
A: Extend the neighbor deltas to all 8 directions (015's pattern) — nothing
   else in the two-phase (mark-safe, then flip) structure changes.

Q: How would you avoid the recursion-depth risk without switching to an
   explicit stack?
A: `sys.setrecursionlimit(...)` raised high enough — works, but trades a
   Python-level limit for a real OS stack-size limit that can segfault
   instead of raising a catchable exception, and is generally considered
   a smell in interview code. The honest fix is the iterative version.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Border-seeded flood fill, "mark safe from the edge, then finalize":

    LC 417  Pacific Atlantic Water Flow  — same border-outward flood fill,
                                            run twice, intersected (007)
    LC 1020 Number of Enclaves           — border flood fill + count what's
                                            left un-reached (the counting
                                            sibling of this exact algorithm)
    LC 200  Number of Islands            — plain (non-border-seeded) flood
                                            fill / connected components (002)
    LC 733  Flood Fill                   — the single-region, in-place-safe
                                            baseline this problem builds on (001)
================================================================================
"""

import sys
import time
from typing import List

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]
SAFE = "#"


class Solution:
    def solve(self, board: List[List[str]]) -> None:
        """✅ THE ANSWER — border-outward flood fill, ITERATIVE (explicit
        stack). O(rows*cols) time, O(rows*cols) space. Mutates in place."""
        if not board or not board[0]:
            return
        rows, cols = len(board), len(board[0])

        def flood_iterative(r: int, c: int) -> None:
            stack = [(r, c)]
            while stack:
                cr, cc = stack.pop()
                if not (0 <= cr < rows and 0 <= cc < cols) or board[cr][cc] != "O":
                    continue
                board[cr][cc] = SAFE
                for dr, dc in DIRECTIONS:
                    stack.append((cr + dr, cc + dc))

        for r in range(rows):
            for c in (0, cols - 1):
                if board[r][c] == "O":
                    flood_iterative(r, c)
        for c in range(cols):
            for r in (0, rows - 1):
                if board[r][c] == "O":
                    flood_iterative(r, c)

        for r in range(rows):
            for c in range(cols):
                if board[r][c] == "O":
                    board[r][c] = "X"
                elif board[r][c] == SAFE:
                    board[r][c] = "O"

    def solve_recursive(self, board: List[List[str]]) -> None:
        """Same algorithm, RECURSIVE DFS instead of an explicit stack.
        Correct in principle, but the recursion depth equals the size of
        the largest connected border region — on a long corridor-shaped
        board this exceeds Python's default recursion limit and raises
        RecursionError. Demonstrated below. O(rows*cols) time/space."""
        if not board or not board[0]:
            return
        rows, cols = len(board), len(board[0])

        def flood_recursive(r: int, c: int) -> None:
            if not (0 <= r < rows and 0 <= c < cols) or board[r][c] != "O":
                return
            board[r][c] = SAFE
            for dr, dc in DIRECTIONS:
                flood_recursive(r + dr, c + dc)

        for r in range(rows):
            for c in (0, cols - 1):
                if board[r][c] == "O":
                    flood_recursive(r, c)
        for c in range(cols):
            for r in (0, rows - 1):
                if board[r][c] == "O":
                    flood_recursive(r, c)

        for r in range(rows):
            for c in range(cols):
                if board[r][c] == "O":
                    board[r][c] = "X"
                elif board[r][c] == SAFE:
                    board[r][c] = "O"


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def make_corridor(length: int) -> List[List[str]]:
    """A single row of 'O's, length cells long — every cell is a border
    cell (single row means top AND bottom row simultaneously), so nothing
    gets captured, but the flood fill must still walk the entire corridor,
    one recursive call deep per cell."""
    return [["O"] * length]


# ==============================================================================
# TESTS — run:  python 008_surrounded_regions_solution.py
# ==============================================================================
CASES = [
    (
        [
            ["X", "X", "X", "X"],
            ["X", "O", "O", "X"],
            ["X", "X", "O", "X"],
            ["X", "O", "X", "X"],
        ],
        [
            ["X", "X", "X", "X"],
            ["X", "X", "X", "X"],
            ["X", "X", "X", "X"],
            ["X", "O", "X", "X"],
        ],
    ),
    ([["X"]], [["X"]]),
    ([["O"]], [["O"]]),
    (
        [["O", "O", "O"], ["O", "X", "O"], ["O", "O", "O"]],
        [["O", "O", "O"], ["O", "X", "O"], ["O", "O", "O"]],
    ),
    ([["O", "O"], ["O", "O"]], [["O", "O"], ["O", "O"]]),
    ([["X", "X"], ["X", "X"]], [["X", "X"], ["X", "X"]]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: primary iterative border-outward flood fill ---")
    for i, (board, expected) in enumerate(CASES):
        working = [row[:] for row in board]
        sol.solve(working)
        ok = working == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: -> {working}")

    print("\n--- correctness: recursive variant agrees (small boards) ---")
    for i, (board, expected) in enumerate(CASES):
        working = [row[:] for row in board]
        sol.solve_recursive(working)
        ok = working == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: -> {working}")

    # ----------------------------------------------------------------------
    # STEP BY STEP trace, printed live.
    # ----------------------------------------------------------------------
    print("\n--- trace: Example 1 board, phase by phase ---")
    trace_board = [row[:] for row in CASES[0][0]]
    rows, cols = len(trace_board), len(trace_board[0])
    print(f"  before:  {trace_board}")
    stack = []
    for r in range(rows):
        for c in (0, cols - 1):
            if trace_board[r][c] == "O":
                stack.append((r, c))
    for c in range(cols):
        for r in (0, rows - 1):
            if trace_board[r][c] == "O":
                stack.append((r, c))
    print(f"  border 'O' seeds found: {stack}")
    while stack:
        cr, cc = stack.pop()
        if not (0 <= cr < rows and 0 <= cc < cols) or trace_board[cr][cc] != "O":
            continue
        trace_board[cr][cc] = SAFE
        for dr, dc in DIRECTIONS:
            stack.append((cr + dr, cc + dc))
    print(f"  after border flood fill (SAFE marked '#'): {trace_board}")
    for r in range(rows):
        for c in range(cols):
            if trace_board[r][c] == "O":
                trace_board[r][c] = "X"
            elif trace_board[r][c] == SAFE:
                trace_board[r][c] = "O"
    print(f"  after final flip/restore pass:  {trace_board}")
    print(f"  matches expected: {trace_board == CASES[0][1]}")

    # ----------------------------------------------------------------------
    # LIVE DEMO: recursion depth. A long single-row corridor of 'O's forces
    # recursive DFS depth == corridor length, which exceeds the default
    # recursion limit; the iterative version handles it fine.
    # ----------------------------------------------------------------------
    print("\n--- LIVE DEMO: recursive flood fill blows the stack, iterative doesn't ---")
    limit = sys.getrecursionlimit()
    corridor_len = limit * 3          # comfortably past the default limit
    print(f"  sys.getrecursionlimit() = {limit}; corridor length = {corridor_len}")
    print("  a single row of all 'O' -> every cell is a border cell (single-row")
    print("  board), so nothing should be captured; the flood fill must still")
    print("  walk the WHOLE corridor, and recursive DFS descends one call per cell.")

    corridor_iter = make_corridor(corridor_len)
    expected_corridor = [["O"] * corridor_len]
    t0 = time.perf_counter()
    sol.solve(corridor_iter)
    t1 = time.perf_counter()
    iter_ok = corridor_iter == expected_corridor
    print(f"  iterative: succeeded in {(t1 - t0) * 1000:.2f} ms, "
          f"result correct (still all 'O'): {iter_ok}")

    corridor_rec = make_corridor(corridor_len)
    raised = False
    try:
        sol.solve_recursive(corridor_rec)
        print("  recursive: did NOT raise this run (limit not exceeded)")
    except RecursionError as e:
        raised = True
        print(f"  recursive: RecursionError -> {e!r}")
    print(f"  iterative succeeded where recursive failed: {iter_ok and raised}")
    print("  The problem's own constraints allow boards up to 200x200 = 40,000")
    print("  cells, and a long thin corridor of connected 'O's is legal input —")
    print("  this is a real failure mode inside the stated bounds, not a")
    print("  contrived adversarial case. Prefer the iterative version.")
    all_ok &= iter_ok and raised

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
