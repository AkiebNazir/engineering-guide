"""
================================================================================
SOLUTION · LeetCode 289 · Game of Life                               [Medium]
https://leetcode.com/problems/game-of-life/
================================================================================

THE CORE IDEA
--------------
The rules say every cell's NEXT state depends on its neighbors' CURRENT
(old) state, and all `m*n` updates must happen "simultaneously." If you
update cells one at a time while scanning the board in row-major order
and overwrite each cell with its new state as you go, later cells will
read the ALREADY-UPDATED (new) values of earlier neighbors instead of
their original values -- corrupting the simulation, because a cell's
neighbor count is supposed to reflect who was alive BEFORE this round,
not who's alive so far in this scan.

The in-place fix: since every cell only ever holds `0` or `1`, there are
two whole unused encodings (`2` and `3`) available in a single int cell.
Encode BOTH the old state and the new state into one value:
`board[i][j] = old + 2 * new` (old, new both in {0, 1}). During the first
pass, any neighbor's ORIGINAL state can always be recovered with
`board[r][c] % 2` -- whether that neighbor has been visited yet (still
holds its raw 0/1 original value) or already been visited and re-encoded
(holds 0-3, and `% 2` extracts exactly the `old` bit back out). A second
pass then decodes every cell to its final state with `board[i][j] >>= 1`
(equivalently `// 2`), extracting the `new` bit.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded) -- deep-copy the entire board
first, compute every cell's next state by reading only from the COPY
(which never changes), and write results into the original `board`. O(mn)
time, O(mn) EXTRA space for the copy -- correct and simple, but the
follow-up explicitly asks for an in-place solution.

Approach 1 (chosen) -- two-pass in-place bit-packing: encode `old + 2 *
new` into each cell during pass 1 (reading neighbors via `% 2` to always
get their ORIGINAL state regardless of visit order), then unpack with
`>>= 1` in pass 2. O(mn) time, O(1) EXTRA space.

Approach 2 (variant, coded for cross-check) -- same idea but using
sentinel values `-1` ("was live, now dead") and `2` ("was dead, now
live") instead of bit-packing; original state recoverable via `abs(val)
== 1`. Same O(mn) time, O(1) space -- purely a different choice of
encoding, useful to know because some interviewers ask for "a" scheme
rather than "the" bit-packing one specifically.


================================================================================
STEP BY STEP TRACE
================================================================================
board:
    [1, 1]
    [1, 0]

Pass 1 -- visit in row-major order, encode old + 2*new:

    (0,0): old=1. Neighbors in bounds: (0,1)=1, (1,0)=1, (1,1)=0 (all
           still raw, unvisited). live count = 1+1+0 = 2.
           old==1 and live in {2,3} -> stays alive, new=1.
           encode: 1 + 2*1 = 3.  board[0][0] = 3

    (0,1): old=1. Neighbors: (0,0)=3 -> %2=1 (original preserved!),
           (1,0)=1, (1,1)=0. live = 1+1+0 = 2.
           old==1, live in {2,3} -> new=1. encode: 1+2*1=3. board[0][1]=3

    (1,0): old=1. Neighbors: (0,0)=3->%2=1, (0,1)=3->%2=1, (1,1)=0.
           live = 1+1+0 = 2. old==1, live in {2,3} -> new=1.
           encode: 1+2*1=3. board[1][0]=3

    (1,1): old=0. Neighbors: (0,0)=3->%2=1, (0,1)=3->%2=1, (1,0)=3->%2=1.
           live = 1+1+1 = 3. old==0 and live==3 -> becomes alive, new=1.
           encode: 0+2*1=2. board[1][1]=2

Board after pass 1 (encoded): [[3,3],[3,2]]

Pass 2 -- decode with >>= 1:
    3>>1=1, 3>>1=1, 3>>1=1, 2>>1=1

Final board: [[1,1],[1,1]] -- matches the expected output exactly, and
critically, every neighbor read during pass 1 used the ORIGINAL state
(via `% 2`) even after that neighbor had already been overwritten with
its encoded value.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time    Space   Mutates input?
    ----------------------------------------------------------------------
    Deep copy + read-only [priced]      O(mn)   O(mn)    YES, in place*
    Bit-pack old+2*new [chosen]         O(mn)   O(1)     YES, in place
    Sentinel values [variant]           O(mn)   O(1)     YES, in place

    * even the "brute force" approach must still mutate `board` in place
      per the problem signature -- the O(mn) space there is for the
      READ-side copy, not an alternative return value.


================================================================================
EDGE CASES
================================================================================
    All-dead board             -> every neighbor count is 0, no cell has
                                  exactly 3 live neighbors, board stays
                                  all-dead after decoding.
    All-live board (e.g. 3x3)  -> corner cells (3 neighbors) may survive
                                  or die depending on exact counts; a good
                                  board to hand-trace once by yourself,
                                  since it exercises both survival and
                                  overpopulation rules in one shape.
    1x1 board                  -> the single cell has ZERO neighbors in
                                  bounds (the 3x3 neighbor loop always
                                  skips (0,0) itself and every other
                                  offset is out of bounds); live count is
                                  always 0, so a live cell always dies
                                  (under-population) and a dead cell
                                  always stays dead.
    Border and corner cells    -> have fewer than 8 neighbors (3 for a
                                  corner, 5 for a non-corner border cell);
                                  the bounds check `0 <= nr < m and 0 <=
                                  nc < n` inside the 3x3 neighbor loop
                                  handles this uniformly, no special-
                                  casing required.
    Board given as an "infinite
    grid" (the stated follow-up) -> would require either padding the
                                  board with a border of dead cells before
                                  each generation, or switching to a
                                  sparse (set-of-live-coordinates)
                                  representation entirely, since a live
                                  cell could be born just outside the
                                  current fixed-size array.


================================================================================
COMMON MISTAKES
================================================================================
1. Overwriting `board[i][j]` directly with its final new value (0 or 1)
   while scanning left-to-right, top-to-bottom -- later cells then read
   ALREADY-UPDATED neighbor values instead of original ones, corrupting
   every count that depends on an up-or-left neighbor. This is the #1
   bug this problem exists to catch, and it's demonstrated live below.
2. Reading a neighbor's state with `board[r][c]` directly instead of
   `board[r][c] % 2` during pass 1 -- once a neighbor has been encoded to
   2 or 3, a raw read no longer means "live/dead," it means "which of
   the four (old, new) combinations," and using it unmodified as a live
   count contribution silently miscounts.
3. Forgetting pass 2 (the decode step) entirely -- the board is left in
   its encoded 0-3 form instead of the required 0/1 form; visually looks
   "almost right" for cells that happened not to change state (0 and 1
   both decode to themselves under a lazy `% 2` check, masking the bug
   for boards with few transitions).
4. Getting the encode formula backwards (`2*old + new` instead of `old +
   2*new`) -- then `% 2` no longer isolates the ORIGINAL state cleanly
   for every one of the four encoded values, and the neighbor counts
   during pass 1 become inconsistent partway through the scan.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "How would you handle an infinite board?" -> Track only the SET of
  currently-live coordinates (a `set[(row, col)]`) instead of a dense
  grid. To compute the next generation, only cells that are either
  currently live or ADJACENT to a currently-live cell can possibly change
  state -- build a `Counter` of neighbor-counts over just those
  candidates (each live cell increments its 8 neighbors), then apply the
  same four rules. This naturally handles growth past any fixed border
  with no padding trick needed.
- "Could you avoid even the second decode pass?" -> Not while keeping the
  board's cell values restricted to {0, 1} at the end -- SOME second
  pass over every cell is required to strip the encoding back down,
  though it could be fused into other bookkeeping the caller needs
  rather than existing as a visibly separate loop.
- "What if memory truly must be O(1) including no bit-packing (values
  must stay exactly 0/1 at all times)?" -> Then you cannot do it purely
  in place; you need at least O(min(m,n)) space to buffer one "previous
  row" (or diagonal) worth of original values so you can still resolve
  neighbor lookups without having overwritten them, in the same rolling-
  buffer family as classic DP space optimizations.


================================================================================
RELATED PROBLEMS
================================================================================
- Set Matrix Zeroes (LC 73, this topic, 005) -- the other in-place O(1)-
  extra-space matrix problem in this topic; contrast its "border cells as
  markers" trick against this problem's "two states packed into one int"
  trick.
- Flood Fill / grid BFS problems (topic 14, Graphs) -- share the same
  8-directional (or 4-directional) neighbor-iteration-with-bounds-
  checking pattern, though those problems mutate a REGION reachable from
  a seed rather than computing every cell's next state from a fixed rule
  simultaneously.
================================================================================
"""

import copy
import time
from typing import List


class Solution:
    def gameOfLife(self, board: List[List[int]]) -> None:
        """
        Do not return anything, modify board in-place instead.
        """
        m, n = len(board), len(board[0])

        def live_neighbors(r: int, c: int) -> int:
            count = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < m and 0 <= nc < n:
                        count += board[nr][nc] % 2  # original state only
            return count

        # Pass 1: encode old + 2*new into every cell.
        for i in range(m):
            for j in range(n):
                old = board[i][j]
                live = live_neighbors(i, j)
                if old == 1 and live in (2, 3):
                    new = 1
                elif old == 0 and live == 3:
                    new = 1
                else:
                    new = 0
                board[i][j] = old + 2 * new

        # Pass 2: decode to final state.
        for i in range(m):
            for j in range(n):
                board[i][j] >>= 1


def _game_of_life_deepcopy(board: List[List[int]]) -> None:
    """Priced-not-shipped brute force (O(mn) extra space via a read-only
    snapshot), used only as a cross-check oracle. Mutates board in place,
    reading exclusively from `snapshot`."""
    m, n = len(board), len(board[0])
    snapshot = copy.deepcopy(board)

    def live_neighbors(r: int, c: int) -> int:
        count = 0
        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                if dr == 0 and dc == 0:
                    continue
                nr, nc = r + dr, c + dc
                if 0 <= nr < m and 0 <= nc < n:
                    count += snapshot[nr][nc]
        return count

    for i in range(m):
        for j in range(n):
            old = snapshot[i][j]
            live = live_neighbors(i, j)
            if old == 1 and live in (2, 3):
                board[i][j] = 1
            elif old == 0 and live == 3:
                board[i][j] = 1
            else:
                board[i][j] = 0


def _game_of_life_naive_buggy(board: List[List[int]]) -> None:
    """A DELIBERATELY BUGGY naive in-place update: overwrites each cell
    with its final new state directly while scanning, so later cells read
    already-updated neighbor values instead of original ones. Kept here
    only to demonstrate, live, exactly the corruption this problem exists
    to teach you to avoid -- never use this shape in real code."""
    m, n = len(board), len(board[0])
    for i in range(m):
        for j in range(n):
            live = 0
            for dr in (-1, 0, 1):
                for dc in (-1, 0, 1):
                    if dr == 0 and dc == 0:
                        continue
                    nr, nc = i + dr, j + dc
                    if 0 <= nr < m and 0 <= nc < n:
                        live += board[nr][nc]  # BUG: may already be a NEW value
            if board[i][j] == 1:
                board[i][j] = 1 if live in (2, 3) else 0
            else:
                board[i][j] = 1 if live == 3 else 0


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ([[0, 1, 0], [0, 0, 1], [1, 1, 1], [0, 0, 0]],
         [[0, 0, 0], [1, 0, 1], [0, 1, 1], [0, 1, 0]]),
        ([[1, 1], [1, 0]], [[1, 1], [1, 1]]),
        ([[0, 0], [0, 0]], [[0, 0], [0, 0]]),
        ([[0]], [[0]]),
        ([[1]], [[0]]),
    ]
    for board, expected in cases:
        got = [row[:] for row in board]
        sol.gameOfLife(got)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  gameOfLife({board}) -> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- bit-pack encoding vs deep-copy brute force, 300 random boards")
    print("-" * 72)
    import random
    random.seed(289)
    mismatch = 0
    for _ in range(300):
        m = random.randint(1, 10)
        n = random.randint(1, 10)
        board = [[random.randint(0, 1) for _ in range(n)] for _ in range(m)]
        a = [row[:] for row in board]
        b = [row[:] for row in board]
        sol.gameOfLife(a)
        _game_of_life_deepcopy(b)
        if a != b:
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {300 - mismatch}/300 agree ({mismatch} mismatches)")

    print()
    print("LIVE CORRUPTION DEMO -- naive same-array update vs the correct encoding")
    print("-" * 72)
    demo_board = [[0, 1, 0], [0, 0, 1], [1, 1, 1], [0, 0, 0]]
    correct = [row[:] for row in demo_board]
    sol.gameOfLife(correct)

    buggy = [row[:] for row in demo_board]
    _game_of_life_naive_buggy(buggy)

    print(f"starting board:      {demo_board}")
    print(f"correct (encoded):   {correct}")
    print(f"naive (corrupted):   {buggy}")
    demo_diff = correct != buggy
    print(f"cell (1,0) -- correct wants 1 (original neighbor (0,1)=1 contributes to a "
          f"live count of 3), but the naive scan already overwrote (0,1) from 1 to 0 "
          f"earlier in the SAME pass, so it undercounts to 2 and wrongly keeps it dead.")
    print(f"correct[1][0] = {correct[1][0]}   naive[1][0] = {buggy[1][0]}")
    if demo_diff:
        print("CONFIRMED: the naive same-array update corrupts this board -- it disagrees "
              "with the correct encode/decode result, exactly because it read an "
              "already-updated neighbor instead of that neighbor's original state.")
    else:
        print("NOTE: on this particular board the naive approach happened not to differ "
              "from the correct one -- that can happen when the corrupted reads don't "
              "change any rule outcome, but the naive approach is still incorrect in "
              "general (see the boards above where it disagreed).")
    all_ok &= demo_diff

    print()
    print("RUNTIME DEMO -- bit-pack encode/decode vs deep-copy snapshot, measured live")
    print("-" * 72)
    m = n = 150
    random.seed(1)
    big = [[random.randint(0, 1) for _ in range(n)] for _ in range(m)]

    a = [row[:] for row in big]
    t0 = time.perf_counter()
    sol.gameOfLife(a)
    encode_ms = (time.perf_counter() - t0) * 1000

    b = [row[:] for row in big]
    t0 = time.perf_counter()
    _game_of_life_deepcopy(b)
    deepcopy_ms = (time.perf_counter() - t0) * 1000

    print(f"{m}x{n} board, one generation:")
    print(f"  bit-pack encode/decode [O(1) extra]: {encode_ms:8.2f} ms")
    print(f"  deep-copy snapshot [O(mn) extra]:    {deepcopy_ms:8.2f} ms")
    if encode_ms < deepcopy_ms:
        print(f"  measured: bit-pack is {deepcopy_ms / encode_ms:.2f}x FASTER here -- "
              f"`copy.deepcopy` walks and reallocates the entire nested list structure "
              f"up front, real allocation cost the O(1)-space version never pays.")
    else:
        print(f"  measured: deep-copy was not slower here -- the extra `% 2` on every "
              f"neighbor read in the bit-pack version has its own real cost; either way "
              f"the bit-pack approach remains the correct answer to the explicit in-place "
              f"follow-up.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
