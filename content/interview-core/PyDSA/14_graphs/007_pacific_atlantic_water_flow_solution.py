"""
================================================================================
SOLUTION · LeetCode 417 · Pacific Atlantic Water Flow               [Medium]
https://leetcode.com/problems/pacific-atlantic-water-flow/
================================================================================

THE CORE IDEA
--------------
Don't ask "from each cell, can water reach the ocean" (that means one flood
fill PER cell). Reverse the question: "starting AT the ocean's border, which
cells could water have flowed FROM" — flood fill INWARD from every Pacific
border cell, and separately from every Atlantic border cell, walking to a
neighbor whenever `neighbor_height >= current_height` (the reverse of the
problem's forward `<=` flow rule, since we're replaying the path backward).
Two flood fills total, not one per cell. The answer is the INTERSECTION of
the two reachable sets.

**This is the folder's canonical example of why mutating the grid in place
as a visited marker breaks correctness (topic guide §6.1).** The SAME
`heights` grid is flood-filled TWICE — once from the Pacific border, once
from the Atlantic border. If the Pacific pass mutates `heights` to mark
cells visited, the Atlantic pass then reads CORRUPTED heights and produces a
wrong answer. This file builds that broken version, runs it, and shows the
actual wrong output — not just a claim (see the runtime demo below).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): for every cell, run its own flood fill
(BFS/DFS) forward along the `<=` downhill rule and check if it reaches the
top/left border (Pacific) and separately the bottom/right border (Atlantic).
O(rows*cols) flood fills, each up to O(rows*cols) -> O((rows*cols)^2) worst
case. Never do this at 200x200 = 40,000 cells.

Approach 1 (reverse flood fill, TWO separate visited sets) ✅ — the answer.
Flood fill inward from the Pacific border into one visited set, inward from
the Atlantic border into a second, independent visited set, intersect them.
O(rows*cols) time — each flood fill visits every cell at most once.

    from collections import deque

    DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]

    def pacificAtlantic(heights):
        rows, cols = len(heights), len(heights[0])

        def flood(starts):
            visited = set(starts)
            queue = deque(starts)
            while queue:
                r, c = queue.popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and (nr, nc) not in visited
                            and heights[nr][nc] >= heights[r][c]):   # reversed rule
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return visited

        pacific_starts = [(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)]
        atlantic_starts = ([(rows - 1, c) for c in range(cols)]
                            + [(r, cols - 1) for r in range(rows)])

        pacific = flood(pacific_starts)      # SEPARATE set — heights is read-only
        atlantic = flood(atlantic_starts)    # SEPARATE set — Atlantic pass sees
                                              #   the ORIGINAL, uncorrupted heights
        return [list(cell) for cell in pacific & atlantic]

Approach 2 (✗ broken on purpose — mutate `heights` as the visited marker):
overwrite each visited cell's height with a sentinel instead of using a
`visited` set, to save the O(rows*cols) set memory. This is a real
temptation — Flood Fill (001) explicitly allows exactly this trick. It
breaks HERE because the grid is read a second time by the Atlantic pass,
and the sentinel has already destroyed the real heights the second flood
fill needs to make its own `>=` comparisons. Implemented and demonstrated
failing, live, below.


================================================================================
STEP BY STEP TRACE
================================================================================
heights =
    1 2 2 3 5
    3 2 3 4 4
    2 4 5 3 1
    6 7 1 4 5
    5 1 1 2 4

PACIFIC flood fill (seeded from row 0 and column 0, reversed rule >=):
  start set: (0,0)(0,1)(0,2)(0,3)(0,4) row0, (0,0)(1,0)(2,0)(3,0)(4,0) col0
  from (0,4)=5: neighbor (1,4)=4, 4>=5? NO -> blocked (can't flow further in)
  from (0,3)=3: neighbor (0,4)=5 already visited; (1,3)=4, 4>=3 YES -> visit (1,3)
  from (1,3)=4: neighbor (1,4)=4, 4>=4 YES -> visit (1,4)
  from (3,0)=6: neighbor (3,1)=7, 7>=6 YES -> visit (3,1); (4,0)=5 already in col0 seed
  from (3,1)=7: neighbor (2,1)=4, 4>=7? NO -> blocked
  ... (full BFS omitted for brevity; final Pacific-reachable set matches the
  solution's printed set below)

ATLANTIC flood fill (seeded from last row and last column, same reversed rule),
run on the SAME, UNMODIFIED heights grid (this is exactly what the separate
visited-set design guarantees, and exactly what the broken mutate-in-place
version fails to guarantee — see the live demo).

Intersection of the two reachable sets -> [[0,4],[1,3],[1,4],[2,2],[3,0],
[3,1],[4,0]], matching Example 1 exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time              Space    Mutates input?
    ------------------------------------  ---------------   -------  --------------
    Brute force (flood fill per cell)     O((R*C)^2)         O(R*C)   no
    Reverse flood fill, 2 SEPARATE sets ✅ O(R*C)             O(R*C)   no
    Reverse flood fill, mutate in place ✗ O(R*C)             O(1) extra  YES — and WRONG

    "Mutates input?" — the correct approach deliberately does NOT mutate
    `heights`, because it is read twice (once per ocean). The in-place
    version saves the visited-set memory but corrupts the SECOND flood
    fill's view of the grid, producing a wrong answer — demonstrated below,
    not just asserted.


================================================================================
EDGE CASES
================================================================================
    1x1 grid                    -> the single cell touches all 4 borders at
                                    once, so it trivially reaches both
                                    oceans. Both seed lists include (0,0)
                                    from two different border edges;
                                    de-duplication (a set) handles that.
    flat grid (all equal heights) -> every neighbor comparison is `>=`
                                    trivially true, so BOTH flood fills reach
                                    every cell -> every cell is in the
                                    answer. Exists to check the `>=` (not
                                    `>`) boundary is correctly inclusive.
    a cell reachable by ONLY one ocean -> correctly excluded from the
                                    intersection; this is the common case
                                    for most interior cells.
    corner cells                -> touch TWO border edges simultaneously
                                    (e.g. (0,0) is both top-row and
                                    left-column) — must appear only ONCE in
                                    each ocean's start list/set, not counted
                                    twice.
    very flat interior surrounded by a rim that only drains one way ->
                                    stresses that the flood fill correctly
                                    stops at the first `<` drop, not just at
                                    the first unequal neighbor.


================================================================================
COMMON MISTAKES
================================================================================
1. Using the FORWARD flow rule (`neighbor <= current`) for the reverse
   flood fill instead of the reversed rule (`neighbor >= current`) — this
   silently computes "where a drop AT this cell could flow to," which is a
   different (and here, useless) question. The whole trick depends on
   flipping the inequality.
2. **Mutating `heights` in place as the visited marker** (§6.1's headline
   example) — correct-looking on a SINGLE flood fill, wrong the instant a
   second flood fill reads the same grid. Demonstrated failing live below.
3. Forgetting a cell can be BOTH a Pacific-border and Atlantic-adjacent-via-
   flow-path cell — the answer is a set INTERSECTION, not a union or an
   either/or check.
4. Re-adding a start cell to its own visited set's queue twice because it
   appears in both the row-0 and column-0 seed lists (or row-(m-1) and
   column-(n-1)) — must dedupe with a set, not a list, before seeding.
5. Running one BFS starting from a single "combined ocean" queue and trying
   to track "reached which ocean" with a 2-bit flag per cell instead of two
   independent flood fills — conflates the two searches and makes the
   `>=` frontier expansion of one ocean incorrectly block the other's.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why can't you just mutate the grid to save memory, like Flood Fill (001)
   does?
A: 001 reads the grid exactly once. Here the SAME grid is read by two
   independent flood fills, and the second one needs the ORIGINAL heights to
   make its own correct `>=` comparisons — see the live demo, where mutating
   in place makes the Atlantic pass silently drop cells it should have
   reached.

Q: Could you do this with a single combined BFS instead of two?
A: You can seed one BFS with both border sets tagged by origin ocean and
   track a 2-bit "reachable-from" flag per cell instead of returning early —
   it still visits O(rows*cols) cells total and gives the same answer, but
   two independent, simpler flood fills is the standard, more readable
   presentation and avoids the flag-merging edge cases above.

Q: What if the flow rule were strict (`<` not `<=`), i.e. water cannot flow
   onto perfectly flat ground?
A: Flip the reversed comparison to strict `>` as well — flat regions would
   then never spread between each other, changing the flat-grid edge case
   above from "everything reachable" to "nothing beyond the seeded border
   cells reachable."

Q: How would you extend this to K oceans instead of 2?
A: Run K independent reverse flood fills (one per ocean's border cells) and
   intersect all K reachable sets — same algorithm, generalizes directly,
   still O(K * rows * cols).


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Reverse flood fill / multi-region flood fill and intersection:

    LC 130  Surrounded Regions        — flood fill from the border INWARD to
                                         find the "safe" region, then flip
                                         the rest (008, same border-seeded
                                         flood-fill idea, one region not two)
    LC 200  Number of Islands         — plain flood fill / connected components (002)
    LC 733  Flood Fill                — the single-flood-fill baseline where
                                         in-place mutation IS safe (001)
    LC 1020 Number of Enclaves        — border flood fill + count what's left,
                                         the single-ocean sibling of 007/008
================================================================================
"""

import random
import time
from collections import deque
from typing import List, Set, Tuple

DIRECTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]


class Solution:
    def pacificAtlantic(self, heights: List[List[int]]) -> List[List[int]]:
        """✅ THE ANSWER — reverse flood fill from both borders, TWO
        SEPARATE visited sets. O(rows*cols) time, O(rows*cols) space.
        Does NOT mutate heights (it is read twice, once per ocean)."""
        if not heights or not heights[0]:
            return []
        rows, cols = len(heights), len(heights[0])

        def flood(starts: List[Tuple[int, int]]) -> Set[Tuple[int, int]]:
            visited = set(starts)
            queue = deque(starts)
            while queue:
                r, c = queue.popleft()
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if (0 <= nr < rows and 0 <= nc < cols
                            and (nr, nc) not in visited
                            and heights[nr][nc] >= heights[r][c]):
                        visited.add((nr, nc))
                        queue.append((nr, nc))
            return visited

        pacific_starts = [(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)]
        atlantic_starts = ([(rows - 1, c) for c in range(cols)]
                            + [(r, cols - 1) for r in range(rows)])

        pacific = flood(pacific_starts)
        atlantic = flood(atlantic_starts)     # heights UNTOUCHED by the pacific pass

        return [list(cell) for cell in pacific & atlantic]

    def pacificAtlantic_broken_mutate_inplace(
        self, heights: List[List[int]]
    ) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — mistake #2. Uses `heights` itself as the
        visited marker (overwrite each visited cell with a sentinel) instead
        of a separate set, to "save memory" the way Flood Fill (001) safely
        does on a SINGLE pass. It is unsafe here because the Atlantic flood
        fill runs on the SAME grid the Pacific flood fill already corrupted.
        MUTATES heights in place — and gives the WRONG answer."""
        if not heights or not heights[0]:
            return []
        rows, cols = len(heights), len(heights[0])
        SENTINEL = -1   # below the valid height range [0, 1e5]; marks "visited"

        def flood_mutate(starts: List[Tuple[int, int]]) -> Set[Tuple[int, int]]:
            reached = set()
            stack = list(starts)
            # snapshot each start cell's real height BEFORE any mutation,
            # since a cell might already have been sentineled by an earlier
            # (other-ocean) flood fill on this same grid.
            original = {(r, c): heights[r][c] for r, c in starts if heights[r][c] != SENTINEL}
            while stack:
                r, c = stack.pop()
                if (r, c) in reached:
                    continue
                reached.add((r, c))
                cur = original.get((r, c), heights[r][c])
                for dr, dc in DIRECTIONS:
                    nr, nc = r + dr, c + dc
                    if 0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in reached:
                        nh = heights[nr][nc]
                        if nh == SENTINEL:
                            # already claimed by an earlier flood fill on this
                            # same corrupted grid — its real height is LOST,
                            # so this flood fill cannot correctly decide
                            # whether it could have flowed here too.
                            continue
                        if nh >= cur:
                            original[(nr, nc)] = nh
                            stack.append((nr, nc))
            for (r, c) in reached:
                heights[r][c] = SENTINEL         # <-- the corrupting mutation
            return reached

        pacific_starts = [(0, c) for c in range(cols)] + [(r, 0) for r in range(rows)]
        atlantic_starts = ([(rows - 1, c) for c in range(cols)]
                            + [(r, cols - 1) for r in range(rows)])

        pacific = flood_mutate(pacific_starts)      # corrupts `heights` as it goes
        atlantic = flood_mutate(atlantic_starts)    # reads the CORRUPTED grid

        return [list(cell) for cell in pacific & atlantic]


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def normalize(coords):
    return sorted(tuple(c) for c in coords)


def make_random_heights(rows: int, cols: int, seed: int, max_h: int = 9) -> List[List[int]]:
    rng = random.Random(seed)
    return [[rng.randint(0, max_h) for _ in range(cols)] for _ in range(rows)]


# ==============================================================================
# TESTS — run:  python 007_pacific_atlantic_water_flow_solution.py
# ==============================================================================
CASES = [
    (
        [
            [1, 2, 2, 3, 5],
            [3, 2, 3, 4, 4],
            [2, 4, 5, 3, 1],
            [6, 7, 1, 4, 5],
            [5, 1, 1, 2, 4],
        ],
        [[0, 4], [1, 3], [1, 4], [2, 2], [3, 0], [3, 1], [4, 0]],
    ),
    ([[1]], [[0, 0]]),
    ([[1, 1], [1, 1]], [[0, 0], [0, 1], [1, 0], [1, 1]]),
    (
        [[3, 3, 3], [3, 3, 3], [3, 3, 3]],
        [[r, c] for r in range(3) for c in range(3)],
    ),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: primary two-separate-sets approach ---")
    for i, (heights, expected) in enumerate(CASES):
        working = [row[:] for row in heights]
        got = sol.pacificAtlantic(working)
        ok = normalize(got) == normalize(expected)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  case {i}: {normalize(got)}")

    print("\n--- randomised cross-check: brute force vs reverse flood fill ---")
    def brute_force(heights):
        rows, cols = len(heights), len(heights[0])

        def reaches(r, c, target):
            visited = set()
            stack = [(r, c)]
            while stack:
                cr, cc = stack.pop()
                if (cr, cc) in visited:
                    continue
                visited.add((cr, cc))
                if target == "pacific" and (cr == 0 or cc == 0):
                    return True
                if target == "atlantic" and (cr == rows - 1 or cc == cols - 1):
                    return True
                for dr, dc in DIRECTIONS:
                    nr, nc = cr + dr, cc + dc
                    if (0 <= nr < rows and 0 <= nc < cols and (nr, nc) not in visited
                            and heights[nr][nc] <= heights[cr][cc]):
                        stack.append((nr, nc))
            return False

        out = []
        for r in range(rows):
            for c in range(cols):
                if reaches(r, c, "pacific") and reaches(r, c, "atlantic"):
                    out.append([r, c])
        return out

    mismatches = 0
    for i in range(60):
        rows_r, cols_r = random.Random(i).randint(1, 6), random.Random(i + 1).randint(1, 6)
        heights = make_random_heights(rows_r, cols_r, seed=i, max_h=5)
        a = normalize(sol.pacificAtlantic([row[:] for row in heights]))
        b = normalize(brute_force(heights))
        if a != b:
            mismatches += 1
    print(f"  60 random grids, reverse flood fill vs brute force: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # LIVE DEMO: mistake #2 — mutating heights as the visited marker BREAKS
    # the second flood fill, on the SAME grid. Print the actual wrong output.
    # ----------------------------------------------------------------------
    print("\n--- LIVE DEMO: in-place mutation corrupts the second (Atlantic) flood fill ---")
    demo_heights, demo_expected = CASES[0]
    correct = normalize(sol.pacificAtlantic([row[:] for row in demo_heights]))

    broken_grid = [row[:] for row in demo_heights]
    print(f"  heights BEFORE broken run: {broken_grid}")
    broken_result = normalize(sol.pacificAtlantic_broken_mutate_inplace(broken_grid))
    print(f"  heights AFTER  broken run: {broken_grid}   <-- corrupted with -1 sentinels")
    print(f"  correct answer (2 separate sets): {correct}")
    print(f"  broken answer (mutate in place):  {broken_result}")
    is_wrong = broken_result != correct
    missing = sorted(set(correct) - set(broken_result))
    print(f"  broken version's answer differs from correct: {is_wrong}")
    if missing:
        print(f"  cells the broken version WRONGLY OMITTED: {missing}")
    print("  Why: the Pacific pass overwrites every cell it reaches with -1.")
    print("  The Atlantic pass then reads a grid where those cells' REAL")
    print("  heights are gone — its flood fill treats -1 as \"already claimed,")
    print("  stop here\" instead of comparing real heights, so it silently")
    print("  fails to expand through cells the Pacific pass already touched,")
    print("  undercounting the Atlantic-reachable set and breaking the")
    print("  intersection. This is exactly topic guide §6.1's warning: use a")
    print("  SEPARATE visited set whenever a grid is read more than once.")
    all_ok &= is_wrong   # the whole point of this demo: prove it IS wrong

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: reverse flood fill vs brute force, MEASURED.
    # ----------------------------------------------------------------------
    print("\n--- RUNTIME DEMO: reverse flood fill (2 passes) vs brute force (per-cell) ---")
    rows, cols = 30, 30
    heights = make_random_heights(rows, cols, seed=99, max_h=50)
    print(f"  grid {rows}x{cols} = {rows*cols} cells")

    t0 = time.perf_counter()
    fast = sol.pacificAtlantic([row[:] for row in heights])
    t1 = time.perf_counter()
    fast_ms = (t1 - t0) * 1000

    t2 = time.perf_counter()
    slow = brute_force(heights)
    t3 = time.perf_counter()
    slow_ms = (t3 - t2) * 1000

    same = normalize(fast) == normalize(slow)
    speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
    print(f"  reverse flood fill (2 passes):  {fast_ms:8.3f} ms")
    print(f"  brute force (flood fill/cell):  {slow_ms:8.3f} ms")
    print(f"  speedup:                        {speedup:8.1f}x")
    print(f"  both approaches produced the same answer: {same}")
    all_ok &= same
    all_ok &= (fast_ms < slow_ms)

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
