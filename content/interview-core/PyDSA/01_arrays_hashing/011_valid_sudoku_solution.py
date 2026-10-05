"""
================================================================================
SOLUTION · LeetCode 36 · Valid Sudoku                                  [Medium]
https://leetcode.com/problems/valid-sudoku/
================================================================================

THE CORE IDEA
-------------
This is LC 217 (Contains Duplicate) wearing a costume. The only real content is:

    EVERY CELL BELONGS TO EXACTLY THREE GROUPS — its row, its column, its box.
    A board is valid iff no group contains a repeated digit.

So keep 27 sets (9 rows + 9 cols + 9 boxes), make ONE pass over the 81 cells,
and for each filled cell check-then-insert into all three of its groups. A
collision anywhere means invalid.

The one piece of actual arithmetic is mapping (r, c) to a box index:

    box = (r // 3) * 3 + (c // 3)

    `// 3` collapses {0,1,2} -> 0, {3,4,5} -> 1, {6,7,8} -> 2, turning a
    coordinate into a BLOCK coordinate. Then `* 3 +` flattens the 3x3 grid of
    blocks into a single 0..8 index — the same row-major flattening you use to
    index a 2D array stored as 1D.

        c//3 =   0     1     2
        r//3 ┌─────┬─────┬─────┐
          0  │  0  │  1  │  2  │
             ├─────┼─────┼─────┤
          1  │  3  │  4  │  5  │
             ├─────┼─────┼─────┤
          2  │  6  │  7  │  8  │
             └─────┴─────┴─────┘

If the arithmetic makes you nervous, `boxes[(r//3, c//3)]` with a tuple key is
equally correct and self-documenting. Use it — clarity beats cleverness, and
the interviewer cares that you knew a box needs its own identity, not that you
flattened it by hand.

⚠️  WHAT THIS PROBLEM IS NOT
    Not solving. Not backtracking. Not checking satisfiability. A board with
    one 5 and eighty dots is VALID, and a board can be valid yet unsolvable.
    Candidates lose time writing a solver. Read the word "valid" carefully.


================================================================================
APPROACH 0 · Three separate scans (perfectly good — say it first)
================================================================================
    for each row:    if duplicates -> False
    for each col:    if duplicates -> False
    for each box:    if duplicates -> False
    return True

Three passes over 81 cells instead of one. Same O(1) here, same asymptotics in
general, and arguably the most readable version — each rule is checked by code
that looks like the rule. The nine-line Pythonic form:

    def ok(group): vals = [v for v in group if v != '.']; return len(vals) == len(set(vals))

    rows  = board
    cols  = zip(*board)
    boxes = [[board[r+i][c+j] for i in range(3) for j in range(3)]
             for r in (0,3,6) for c in (0,3,6)]
    return all(ok(g) for g in (*rows, *cols, *boxes))

Know this. It is what you would actually write in review. Then offer the
one-pass version as the "if you want early exit and a single traversal" answer.


================================================================================
APPROACH 1 · One pass, 27 sets ✅✅ (the answer)
================================================================================

    rows  = [set() for _ in range(9)]
    cols  = [set() for _ in range(9)]
    boxes = [set() for _ in range(9)]

    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == '.':
                continue
            b = (r // 3) * 3 + (c // 3)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v); cols[c].add(v); boxes[b].add(v)
    return True

    Time:  O(81) = O(1)      (O(n²) for a general n x n board)
    Space: O(27 * 9) = O(1)  (O(n²) generalised)

STEP BY STEP — the first few filled cells of the example board:

    board row 0 = 5 3 . . 7 . . . .

    (r,c)   v    b = (r//3)*3 + (c//3)    check                       action
    -----   ---  ----------------------   -------------------------   ----------
    (0,0)   '5'  (0)*3 + (0) = 0          not in rows[0]/cols[0]/b0   add to all
    (0,1)   '3'  (0)*3 + (0) = 0          not in rows[0]/cols[1]/b0   add to all
    (0,2)   '.'  —                        skipped                     —
    (0,4)   '7'  (0)*3 + (1) = 1          not in rows[0]/cols[4]/b1   add to all
    (1,0)   '6'  (0)*3 + (0) = 0          rows[1] empty, cols[0]={5}, add to all
                                          boxes[0]={5,3}
    (1,3)   '1'  (0)*3 + (1) = 1          ...                         add to all

    ...81 cells later, no collision -> True

AND THE FAILING BOARD (example 2, the 5 at (0,0) becomes 8):

    (0,0)  '8'  box 0   -> boxes[0] = {'8'}
    ...
    (3,0)  '8'  box (3//3)*3 + 0 = 3   -> different box, fine
    ...
    the actual clash is at (2,2)='8' vs (0,0)='8', both in box 0:
    (2,2)  '8'  box (2//3)*3 + (2//3) = 0   -> '8' IS in boxes[0]  -> False ✓

    Note the row check and column check both PASS for that cell. Only the box
    check catches it — which is exactly why example 2 exists.

⚠️  CHECK BEFORE YOU INSERT
    If you add first and then test membership, the digit you just inserted is
    always present and every filled cell reports a duplicate. Same shape as the
    Two Sum "insert before check" bug. Test, then insert.

⚠️  SKIP '.' BEFORE THE BOX MATH, NOT AFTER
    Not a correctness issue (the math is fine for any cell) but if you forget
    to skip dots entirely, the second '.' in any row collides and you return
    False for the empty board. The all-dots test case below catches it.


================================================================================
APPROACH 2 · Single set of encoded keys (the compact trick)
================================================================================
Instead of 27 sets, use ONE set holding self-describing strings:

    seen = set()
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == '.': continue
            keys = (f"row{r}-{v}", f"col{c}-{v}", f"box{r//3}{c//3}-{v}")
            if any(k in seen for k in keys): return False
            seen.update(keys)
    return True

Cute, and it fits on a slide. Two honest caveats:
  - The key strings must be UNAMBIGUOUS. `f"{r}{v}"` for row and `f"{v}{c}"`
    for column will eventually collide across categories and produce a wrong
    answer. Prefix with the category name; do not golf it.
  - Building three f-strings per cell is slower than three set lookups.

It is a legitimate answer, but 27 sets is clearer and faster. Show this one as
a variation, not as your primary.


================================================================================
APPROACH 3 · Bitmasks (the O(1)-space, no-allocation answer)
================================================================================
A group only needs to remember WHICH of nine digits it has seen — that is nine
bits, so one small integer per group. 27 integers, no sets at all.

    rows = [0] * 9; cols = [0] * 9; boxes = [0] * 9

    bit = 1 << (int(v) - 1)              # digit 1 -> bit 0, ..., digit 9 -> bit 8
    if rows[r] & bit or cols[c] & bit or boxes[b] & bit:
        return False
    rows[r] |= bit; cols[c] |= bit; boxes[b] |= bit

    `&` asks "have I seen it?", `|=` records it. No hashing, no allocation, no
    pointer chasing — just integer ops on values that stay in registers.

This is how you would write it in C or Go, and it is a genuinely good answer to
"can you reduce the space?". It also generalises: any "seen a member of a small
fixed universe" question can be a bitmask instead of a set.

⚠️  BUT IT IS NOT FASTER IN CPYTHON — MEASURE BEFORE YOU CLAIM
    The benchmark at the bottom of this file runs all four versions 100k times
    and the bitmask LOSES to the plain 27 sets. Why: `int(v)` parses a string
    to an int and `1 << k` allocates a new Python int object, both of which
    cost more than one hash lookup of a 1-character interned string. The
    "registers, no allocation" story is true of C and of Go — in CPython every
    integer is a heap object and there are no registers to speak of.

    So: bitmasks are the right answer for SPACE, and for a compiled language,
    and for the incremental/solver follow-up. They are not automatically the
    right answer for speed in Python. Say "fewer bytes and O(1) updates",
    not "faster", unless you have measured on the runtime you are using.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    The board is FIXED at 9x9. Everything here is O(1) — 81 cells, 27 trackers.
    Saying "O(n²)" without qualification is a small red flag; say "O(1) because
    the board size is fixed by the constraints; O(n²) time and space if you
    generalise to n x n with n boxes."

    Approach              Time      Extra space    Passes   Mutates input?
    --------------------  --------  -------------  -------  --------------
    Three scans           O(1)      O(1)           3        no
    27 sets           ✅✅  O(1)      O(1) ~27 sets  1        no
    Encoded key set       O(1)      O(1) ~81 strs  1        no
    27 bitmasks       ✅✅  O(1)      O(1) 27 ints   1        no

    Generalised to n x n (n a perfect square): all are O(n²) time. The set
    versions are O(n²) space; the bitmask version is O(n) integers of n bits,
    i.e. O(n²) bits — same order, far smaller constant.


================================================================================
EDGE CASES
================================================================================
    all '.'            -> True
                          An empty board breaks no rule. This catches code
                          that forgets to skip dots (the second '.' in a row
                          "collides") and code that requires completeness.

    one digit only     -> True
                          Valid boards need not be solvable or full.

    dup in a row       -> False  — the easy one, everyone catches it.

    dup in a column    -> False  — caught by transposing or by cols[c].

    dup in a box only  -> False  — different row AND different column, so both
                          of the easy checks pass. This is the case that
                          exposes a wrong box formula, and it is exactly what
                          LeetCode's example 2 tests.

    same digit at (0,0) and (3,3)  -> True
                          Different row, different column, different box, so
                          the board is legal. But (r%3, c%3) is (0,0) for both,
                          so a `%`-based box formula rejects it. Note that
                          distinct digits at those spots would NOT expose the
                          bug — the collision needs the SAME digit. The
                          BOX_SPREAD case below is built exactly for this.

    board is VALID but UNSOLVABLE -> True
                          Because "valid" only means no rule is currently
                          broken. Do not write a solver.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `%` instead of `//` in the box formula. `r % 3` cycles 0,1,2,0,1,2...
   which mixes cells from vertically distant boxes. It happens to give the
   right answer on many boards, which is what makes it dangerous.

2. Inserting before checking, so every filled cell looks like a duplicate.

3. Forgetting to skip '.', so any board with two empty cells in a row is
   "invalid".

4. Writing a Sudoku SOLVER. The problem says validate.

5. Ambiguous encoded keys in the single-set approach — `f"{r}{v}"` for rows and
   `f"{v}{c}"` for cols collide (row 1 digit 2 -> "12"; digit 1 col 2 -> "12").

6. Rebuilding the box contents from scratch for each of the nine boxes with
   nested slicing inside the main loop. Correct but pointlessly re-reads cells.

7. Claiming O(n²) time without noting the board is fixed-size, or claiming
   O(1) without being able to say what it would be if generalised.

8. Treating '0' as empty. The constraints say the empty marker is '.', and '0'
   is not a legal digit here at all.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Generalise to an n x n board with sqrt(n) x sqrt(n) boxes.
A: Same algorithm; `k = isqrt(n)` and `box = (r // k) * k + (c // k)`. The
   bitmask version needs n-bit integers, which Python gives you free and Go
   does not (you would use a []uint64 or a [n]bool).

Q: Reduce the space further.
A: Bitmasks (approach 3) — 27 machine integers total. You cannot do better
   than remembering, for each group, which digits it holds; that IS the
   information content.

Q: Now actually SOLVE it.
A: Backtracking, and this validator becomes the constraint check inside it.
   Keep the 27 bitmasks as incremental state so placing and un-placing a digit
   is `|=` and `&= ^bit` in O(1) rather than a rescan — that single change is
   the difference between a solver that runs in milliseconds and one that
   times out. (LC 37.)

Q: The board arrives as a stream of (row, col, digit) placements. Validate
   incrementally.
A: Exactly the 27-bitmask state, updated per placement in O(1). This is why
   the bitmask formulation is worth knowing — it is the incremental one.

Q: Multiple threads validating different regions?
A: Rows, columns, and boxes are three independent partitions of the same 81
   cells, so the three checks can run in parallel with no shared state. Within
   one category, each group is independent too. It parallelises trivially —
   and pointlessly, at 81 cells.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 217  Contains Duplicate      — the primitive this whole problem is
                                       built from
    LC 37   Sudoku Solver [Hard]    — backtracking on top of this validator
    LC 289  Game of Life            — the other classic grid-with-neighbourhood
                                       problem; in-place encoding trick
    LC 73   Set Matrix Zeroes       — row/col bookkeeping over a grid
    LC 48   Rotate Image            — index arithmetic on a square grid
    LC 2133 Check if Every Row and Column Contains All Numbers — the same
                                       validation minus the boxes
================================================================================
"""

import time
from typing import List


class Solution:
    def isValidSudoku(self, board: List[List[str]]) -> bool:
        """One pass, 27 sets. O(1) time and space for a fixed 9x9 board."""
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]

        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":                       # empty cells break no rule
                    continue
                b = (r // 3) * 3 + (c // 3)        # // collapses to a block index
                if v in rows[r] or v in cols[c] or v in boxes[b]:
                    return False                   # CHECK before insert
                rows[r].add(v)
                cols[c].add(v)
                boxes[b].add(v)
        return True

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def isValidSudoku_bitmask(self, board: List[List[str]]) -> bool:
        """27 integers instead of 27 sets. Same logic, no allocation."""
        rows = [0] * 9
        cols = [0] * 9
        boxes = [0] * 9

        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":
                    continue
                bit = 1 << (int(v) - 1)            # digit d -> bit d-1
                b = (r // 3) * 3 + (c // 3)
                if rows[r] & bit or cols[c] & bit or boxes[b] & bit:
                    return False
                rows[r] |= bit
                cols[c] |= bit
                boxes[b] |= bit
        return True

    def isValidSudoku_three_scans(self, board: List[List[str]]) -> bool:
        """Three independent scans — the most readable version."""
        def ok(group) -> bool:
            vals = [v for v in group if v != "."]
            return len(vals) == len(set(vals))

        rows = board
        cols = zip(*board)
        boxes = [[board[r + i][c + j] for i in range(3) for j in range(3)]
                 for r in (0, 3, 6) for c in (0, 3, 6)]
        return all(ok(g) for g in (*rows, *cols, *boxes))

    def isValidSudoku_encoded(self, board: List[List[str]]) -> bool:
        """One set of category-prefixed keys."""
        seen = set()
        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":
                    continue
                keys = (f"row{r}-{v}", f"col{c}-{v}", f"box{r // 3}{c // 3}-{v}")
                if any(k in seen for k in keys):
                    return False
                seen.update(keys)
        return True

    def isValidSudoku_modbug(self, board: List[List[str]]) -> bool:
        """✗ BROKEN ON PURPOSE — uses % instead of // in the box formula."""
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]
        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":
                    continue
                b = (r % 3) * 3 + (c % 3)          # THE BUG
                if v in rows[r] or v in cols[c] or v in boxes[b]:
                    return False
                rows[r].add(v)
                cols[c].add(v)
                boxes[b].add(v)
        return True


# ==============================================================================
# TESTS — run:  python 011_valid_sudoku_solution.py
# ==============================================================================
def _b(rows: List[str]) -> List[List[str]]:
    return [list(r) for r in rows]


VALID = _b([
    "53..7....",
    "6..195...",
    ".98....6.",
    "8...6...3",
    "4..8.3..1",
    "7...2...6",
    ".6....28.",
    "...419..5",
    "....8..79",
])

DUP_BOX = _b([
    "83..7....",
    "6..195...",
    ".98....6.",
    "8...6...3",
    "4..8.3..1",
    "7...2...6",
    ".6....28.",
    "...419..5",
    "....8..79",
])

EMPTY = _b(["." * 9] * 9)
ONE_DIGIT = _b(["....5...."] + ["." * 9] * 8)

DUP_ROW = _b(["5.......5"] + ["." * 9] * 8)
DUP_COL = _b(["5........"] + ["." * 9] * 7 + ["5........"])

# Duplicate inside a box only: (1,1) and (2,2) are different rows AND different
# columns, so only the box check can catch it.
DUP_BOX_ONLY = _b([
    ".........",
    ".4.......",
    "..4......",
    ".........",
    ".........",
    ".........",
    ".........",
    ".........",
    ".........",
])

# VALID: the same digit at (0,0) and (3,3). Different row, different column,
# different real box — so the board breaks no rule. But (r%3, c%3) is (0,0) for
# BOTH, so a `%`-based box formula puts them in the same pseudo-box and rejects
# a legal board. This is the false-NEGATIVE direction of the bug.
BOX_SPREAD = _b([
    "1........",
    ".........",
    ".........",
    "...1.....",
    ".........",
    ".........",
    ".........",
    ".........",
    ".........",
])


def run_tests() -> None:
    sol = Solution()
    cases = [
        ("example 1 (valid)", VALID, True),
        ("example 2 (dup in box)", DUP_BOX, False),
        ("all empty", EMPTY, True),
        ("single digit", ONE_DIGIT, True),
        ("dup in row", DUP_ROW, False),
        ("dup in col", DUP_COL, False),
        ("dup in box only", DUP_BOX_ONLY, False),
        ("digits spread across boxes", BOX_SPREAD, True),
    ]
    impls = [
        ("27 sets     ", sol.isValidSudoku),
        ("27 bitmasks ", sol.isValidSudoku_bitmask),
        ("three scans ", sol.isValidSudoku_three_scans),
        ("encoded keys", sol.isValidSudoku_encoded),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn([row[:] for row in b]) == exp for _, b, exp in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} boards)")

    # ----------------------------------------------------------------------
    # The box formula, drawn.
    # ----------------------------------------------------------------------
    print("\n--- box index = (r // 3) * 3 + (c // 3) ---")
    print("      c: 0 1 2  3 4 5  6 7 8")
    for r in range(9):
        cells = "  ".join(
            " ".join(str((r // 3) * 3 + (c // 3)) for c in range(g * 3, g * 3 + 3))
            for g in range(3)
        )
        sep = "\n     " + "-" * 27 if r in (2, 5) else ""
        print(f"  r={r}:  {cells}{sep}")

    # ----------------------------------------------------------------------
    # ⚠️  % instead of // — right on many boards, wrong on this one.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  (r % 3) * 3 + (c % 3) instead of // ---")
    print("      c: 0 1 2  3 4 5  6 7 8      <- note every box row REPEATS")
    for r in range(9):
        cells = "  ".join(
            " ".join(str((r % 3) * 3 + (c % 3)) for c in range(g * 3, g * 3 + 3))
            for g in range(3)
        )
        print(f"  r={r}:  {cells}")
    print("\n  % groups cells that are FAR APART (note r=0 and r=3 share a row of")
    print("  labels above) and splits cells that are genuinely adjacent. It gets")
    print("  the answer wrong in BOTH directions:")
    print(f"    {'board':<34} {'correct (//)':<14} buggy (%)")
    for label, bd in (
        ("BOX_SPREAD    (valid: 1 at 0,0 & 3,3)", BOX_SPREAD),
        ("DUP_BOX_ONLY  (invalid: box clash)   ", DUP_BOX_ONLY),
        ("VALID         (the example board)    ", VALID),
    ):
        good = sol.isValidSudoku([r[:] for r in bd])
        bad = sol.isValidSudoku_modbug([r[:] for r in bd])
        flag = "" if good == bad else "   <- WRONG"
        print(f"    {label:<34} {str(good):<14} {bad}{flag}")
    print("  Row 1: rejects a legal board (false negative).")
    print("  Row 2: ACCEPTS an illegal board (false positive) — the dangerous one.")
    print("  Row 3: rejects the problem's own example board.")

    # ----------------------------------------------------------------------
    # ⚠️  Insert-before-check.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  inserting before checking ---")

    def insert_first(board):
        rows = [set() for _ in range(9)]
        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":
                    continue
                rows[r].add(v)                     # added FIRST
                if v in rows[r]:                   # ...so always True
                    return False
        return True

    print(f"  valid board, check-then-insert -> {sol.isValidSudoku([r[:] for r in VALID])}")
    print(f"  valid board, insert-then-check -> {insert_first(VALID)}   ✗")
    print("  The digit you just added is always present. Every board is invalid.")

    # ----------------------------------------------------------------------
    # ⚠️  Forgetting to skip '.'.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  not skipping '.' ---")

    def no_skip(board):
        rows = [set() for _ in range(9)]
        for r in range(9):
            for c in range(9):
                v = board[r][c]                    # no `if v == '.': continue`
                if v in rows[r]:
                    return False
                rows[r].add(v)
        return True

    print(f"  empty board, skipping '.'     -> {sol.isValidSudoku([r[:] for r in EMPTY])}")
    print(f"  empty board, NOT skipping '.' -> {no_skip(EMPTY)}   ✗")
    print("  The second '.' in row 0 looks like a duplicate.")

    # ----------------------------------------------------------------------
    # Only the box check catches DUP_BOX_ONLY.
    # ----------------------------------------------------------------------
    print("\n--- which of the three rules actually fires? ---")
    for name, board in (("DUP_ROW", DUP_ROW), ("DUP_COL", DUP_COL),
                        ("DUP_BOX_ONLY", DUP_BOX_ONLY)):
        fired = []
        rows = [set() for _ in range(9)]
        cols = [set() for _ in range(9)]
        boxes = [set() for _ in range(9)]
        for r in range(9):
            for c in range(9):
                v = board[r][c]
                if v == ".":
                    continue
                b = (r // 3) * 3 + (c // 3)
                if v in rows[r]:
                    fired.append("row")
                if v in cols[c]:
                    fired.append("col")
                if v in boxes[b]:
                    fired.append("box")
                rows[r].add(v)
                cols[c].add(v)
                boxes[b].add(v)
        print(f"  {name:<14} rules violated: {sorted(set(fired)) or ['none']}")
    print("  DUP_BOX_ONLY passes BOTH the row and column checks. Drop the box")
    print("  rule and you accept an invalid board.")

    # ----------------------------------------------------------------------
    # Bitmasks vs sets.
    # ----------------------------------------------------------------------
    print("\n--- sets vs bitmasks vs encoded keys (100k validations) ---")
    board = VALID
    for name, fn in (("27 sets     ", sol.isValidSudoku),
                     ("27 bitmasks ", sol.isValidSudoku_bitmask),
                     ("three scans ", sol.isValidSudoku_three_scans),
                     ("encoded keys", sol.isValidSudoku_encoded)):
        t0 = time.perf_counter()
        for _ in range(100_000):
            fn(board)
        print(f"  {name} {(time.perf_counter() - t0) * 1000:8.1f}ms")
    print("  All are O(1) — the board is 81 cells. What differs is the constant.")
    print("  Note the ORDER: bitmasks lose to plain sets here. int(v) plus a")
    print("  shift allocates Python int objects, which costs more than hashing")
    print("  a 1-character interned string. In C or Go the ranking flips.")
    print("  f-string keys lose badly everywhere — 3 string builds per cell.")
    print("  Bitmasks still win on SPACE (27 ints vs 27 sets) and are the right")
    print("  structure for the incremental/solver follow-up.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
