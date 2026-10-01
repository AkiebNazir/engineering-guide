"""
================================================================================
SOLUTION · LeetCode 733 · Flood Fill                                   [Easy]
https://leetcode.com/problems/flood-fill/
================================================================================

THE CORE IDEA
--------------
Flood fill is graph traversal where the graph is implicit: node (r, c),
edges to its up-to-4 orthogonal neighbors, but ONLY when the neighbor's
current pixel value equals the STARTING pixel's original color. Traverse
from (sr, sc) with DFS or BFS, repaint every node you visit to `color`, and
stop expanding the moment a neighbor doesn't match. See topic guide §6 —
this is the grid-as-graph pattern with a single source, the simplest member
of the family (002/003 generalize it to many sources / whole-grid scanning).

    old_color = image[sr][sc]
    if old_color == color: return image        # see "the trap" below
    flood(sr, sc): repaint, then flood into every same-old-color neighbor


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, don't ship): BFS/DFS from EVERY pixel to rebuild
connected components from scratch, then repaint the one containing (sr, sc).
O(rows*cols) either way, but throws away the fact you're already GIVEN the
start — pure wasted work, never something to actually write.

Approach 1 (recursive DFS) — the textbook answer:

    def flood(r, c):
        if not in_bounds or image[r][c] != old_color: return
        image[r][c] = color
        for dr, dc in DIRECTIONS: flood(r+dr, c+dc)

Clean and short, but the recursion depth equals the number of connected
pixels in the worst case (a single-file snake through the grid touches every
cell exactly once, one stack frame per cell) — RecursionError territory,
demoed live below.

Approach 2 (iterative DFS with an explicit stack) ✅:
Same traversal order as Approach 1, same simplicity, but the "stack" is a
Python list instead of the interpreter's call stack — no recursion depth
ceiling. This is the version to actually type in an interview once you've
said out loud "I'd use DFS; going iterative avoids a recursion-depth issue
on a long thin grid."

Approach 3 (BFS with a deque) — also ✅, same complexity, explores
level-by-level instead of depth-first. No behavioral difference for flood
fill (order doesn't matter, only the final color assignment does), but BFS
is the natural choice the moment a problem also wants "distance from start"
(topic guide Part 2) — worth having both ready.


================================================================================
⚠️  THE TRAP: color == old color MUST be special-cased
================================================================================
If `color` already equals `image[sr][sc]`, the naive recursive version still
"works" in the sense that every visited cell gets repainted to the same
value it already had — but with the WRONG guard order it can spiral. Picture
checking "already visited" by comparing to the OLD color instead of using a
separate `visited` set: once you repaint a cell to `color` and `color ==
old_color`, the repainted cell STILL matches "equals old_color" on the next
pass and gets pushed again. A naive implementation that doesn't special-case
this, or that revisits neighbors without any visited tracking at all, either
loops forever (iterative) or re-enters cells recursively and re-derives the
same recursion depth as before doing zero useful work — for a same-color
grid this can be much deeper recursion than expected. The one-line guard
`if color == old_color: return image` at the top sidesteps the entire
question and is also just correct: there is nothing to change.


================================================================================
STEP BY STEP TRACE
================================================================================
image = [[1,1,1],
         [1,1,0],
         [1,0,1]],  sr=1, sc=1, color=2   (old_color = image[1][1] = 1)

    flood(1,1): image[1][1]==1==old -> repaint 2
        1 1 1          push neighbors of (1,1): (0,1)(2,1)(1,0)(1,2)
        1[2]0
        1 0 1

    flood(0,1): ==1 -> repaint 2, push (0,0)(0,2) (and (1,1), already 2 -> skip)
        1[2]1
        1 2 0
        1 0 1

    flood(0,0): ==1 -> repaint 2         flood(0,2): ==1 -> repaint 2
        2 2 1                                2 2[2]
        1 2 0                                1 2 0
        1 0 1                                1 0 1

    flood(2,1): image[2][1]==0 != old(1) -> stop, no repaint
    flood(1,0): ==1 -> repaint 2, push (2,0)
        2 2 2
       [2]2 0
        1 0 1
    flood(2,0): ==1 -> repaint 2
        2 2 2
        2 2 0
       [2]0 1
    flood(1,2): image[1][2]==0 != old -> stop

    (2,2)=1 is never reached (boxed in by 0's at (1,2) and (2,1)) -> stays 1.

    final: [[2,2,2],[2,2,0],[2,0,1]]   — matches Example 1.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Time              Space              Mutates input?
    ---------------------------  ----------------  -----------------  --------------
    Rebuild all components       O(rows*cols)      O(rows*cols)       no (fresh copy)
    Recursive DFS                O(rows*cols)      O(rows*cols) stack YES, in place
    Iterative DFS (stack) ✅      O(rows*cols)      O(rows*cols)       YES, in place
    BFS (deque) ✅                O(rows*cols)      O(rows*cols)       YES, in place

    "Mutates input?" is YES for the shipped approaches — `floodFill` returns
    the SAME `image` object it was given, repainted, matching LeetCode's own
    reference solution and signature. If a caller needs the original
    afterward, copy first (topic guide §6.1) — this problem never asks for
    that, but 007 (Pacific Atlantic) does, and mutating there is a bug.


================================================================================
EDGE CASES
================================================================================
    color == image[sr][sc]     -> must return immediately. Without the guard,
                                  a naive implementation can loop or process
                                  every same-colored cell for zero benefit.
                                  Exercised directly below.
    1x1 grid                   -> single cell, immediate base case either way.
    start pixel isolated        -> component of size 1; nothing else changes.
    (blocked by different colors on all sides)
    entire grid one color       -> every cell visited; recursion depth ==
                                  rows*cols in the worst (snake) layout —
                                  exactly the case the live demo below hits.
    sr, sc at a grid corner/edge -> bounds check must not wrap via Python's
                                  negative indexing (topic guide mistake #8).


================================================================================
COMMON MISTAKES
================================================================================
1. Comparing against the CURRENT value of `image[sr][sc]` inside the
   recursive helper instead of capturing `old_color` once, up front. After
   the first repaint, `image[sr][sc]` no longer equals the original color,
   so a helper that re-reads it mid-traversal gets confused about what it's
   even matching.

2. Forgetting the `color == old_color` guard (see "THE TRAP" above).

3. Off-by-one / missing bounds check on grid neighbors — `r-1` going
   negative doesn't crash in Python, it silently reads the LAST row
   (topic guide mistake #8). Always bounds-check before indexing.

4. Choosing plain recursion without checking `sys.getrecursionlimit()`
   against the grid's max possible size (up to 50x50 = 2500 cells here, but
   this pattern generalizes to 002/003 where LeetCode's real grid caps run
   to 300x300 = 90,000 — well past CPython's default ~1000-frame limit).

5. Using a `visited` SET alongside in-place repainting is redundant and a
   common source of bugs when the two get out of sync — once you repaint to
   `color`, the repainted cell already reads as "not old_color" for any
   later visit (as long as color != old_color, guarded above), so the grid
   itself IS the visited marker. Don't maintain both unless the problem
   forbids mutation.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the grid can't be mutated?
A: Copy it once up front (O(rows*cols) extra space) or keep a separate
   `visited` set of (r, c) pairs and consult it instead of `image[r][c] ==
   old_color`. Topic guide §6.1 — the tradeoff generalizes to every grid
   problem in this folder.

Q: Can you do it without recursion, and why would you?
A: Yes — Approach 2/3. A long thin grid (imagine a 1x2500 strip, or a
   hand-drawn spiral/snake) makes the connected component's DFS recursion
   depth equal to its size, which can exceed Python's default recursion
   limit and raise RecursionError with input well inside 733's own
   constraints once you imagine this pattern at LeetCode's larger grid caps
   (002/003 go up to 300x300). Iterative DFS or BFS has no such ceiling.
   Demoed live below.

Q: DFS or BFS — does it matter here?
A: Not for correctness or asymptotic complexity — final coloring is
   identical either way, since every reachable same-colored cell gets
   painted regardless of visit order. It matters the moment you also need
   "distance from source" (BFS gives that for free) or want early exit on
   first match (BFS if you want nearest, DFS if any match is fine).

Q: How would you extend this to 8-directional (diagonals) fill?
A: Add the four diagonal deltas to `DIRECTIONS` (topic guide §6.2 notes 015
   does exactly this for a different problem). Nothing else changes.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Grid-as-graph, single source (topic guide Part 6).

    LC 200  Number of Islands             — same traversal, but scan every
                                             unvisited land cell as a NEW
                                             source (002, next in this folder)
    LC 695  Max Area of Island            — same traversal, count cells (003)
    LC 130  Surrounded Regions            — flood fill from the BORDER inward
    LC 1254 Number of Closed Islands      — flood fill to eliminate
                                             border-touching islands first
    LC 694  Number of Distinct Islands    — flood fill + shape fingerprinting
================================================================================
"""

import sys
import time
from collections import deque
from typing import List


class Solution:
    def floodFill(self, image: List[List[int]], sr: int, sc: int,
                   color: int) -> List[List[int]]:
        """✅ THE ANSWER — iterative DFS with an explicit stack.
        O(rows*cols) time, O(rows*cols) space. MUTATES `image` in place and
        returns the same object."""
        rows, cols = len(image), len(image[0])
        old_color = image[sr][sc]
        if old_color == color:
            return image                     # THE TRAP — must short-circuit

        stack = [(sr, sc)]
        image[sr][sc] = color
        while stack:
            r, c = stack.pop()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and image[nr][nc] == old_color:
                    image[nr][nc] = color
                    stack.append((nr, nc))
        return image

    def floodFill_bfs(self, image: List[List[int]], sr: int, sc: int,
                       color: int) -> List[List[int]]:
        """BFS variant with a deque — same result, breadth-first order.
        O(rows*cols) time, O(rows*cols) space. MUTATES `image` in place."""
        rows, cols = len(image), len(image[0])
        old_color = image[sr][sc]
        if old_color == color:
            return image

        queue = deque([(sr, sc)])
        image[sr][sc] = color
        while queue:
            r, c = queue.popleft()
            for dr, dc in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < rows and 0 <= nc < cols and image[nr][nc] == old_color:
                    image[nr][nc] = color
                    queue.append((nr, nc))
        return image

    def floodFill_recursive(self, image: List[List[int]], sr: int, sc: int,
                             color: int) -> List[List[int]]:
        """Textbook recursive DFS. O(rows*cols) time, O(rows*cols) CALL
        STACK — can raise RecursionError on a large single-file component.
        MUTATES `image` in place."""
        rows, cols = len(image), len(image[0])
        old_color = image[sr][sc]
        if old_color == color:
            return image

        def dfs(r, c):
            if not (0 <= r < rows and 0 <= c < cols):
                return
            if image[r][c] != old_color:
                return
            image[r][c] = color
            dfs(r - 1, c)
            dfs(r + 1, c)
            dfs(r, c - 1)
            dfs(r, c + 1)

        dfs(sr, sc)
        return image


# ==============================================================================
# TEST HELPERS
# ==============================================================================
def make_strip(length: int) -> List[List[int]]:
    """A 1-row, `length`-column grid, all zeros — a single connected
    component of size `length`, forcing recursion depth == length for a
    naive recursive flood fill."""
    return [[0] * length]


# ==============================================================================
# TESTS — run:  python 001_flood_fill_solution.py
# ==============================================================================
CASES = [
    ([[1, 1, 1], [1, 1, 0], [1, 0, 1]], 1, 1, 2,
     [[2, 2, 2], [2, 2, 0], [2, 0, 1]]),
    ([[0, 0, 0], [0, 0, 0]], 0, 0, 0,
     [[0, 0, 0], [0, 0, 0]]),
    ([[0, 0, 0], [0, 1, 1]], 1, 1, 1,
     [[0, 0, 0], [0, 1, 1]]),
    ([[1]], 0, 0, 9, [[9]]),
    ([[0, 0, 0], [0, 0, 0], [0, 0, 0]], 1, 1, 2,
     [[2, 2, 2], [2, 2, 2], [2, 2, 2]]),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: all three implementations agree with expected output ---")
    for image, sr, sc, color, want in CASES:
        a = sol.floodFill([row[:] for row in image], sr, sc, color)
        b = sol.floodFill_bfs([row[:] for row in image], sr, sc, color)
        c = sol.floodFill_recursive([row[:] for row in image], sr, sc, color)
        ok = a == want and b == want and c == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  sr={sr} sc={sc} color={color} -> {a} "
              f"(want {want})")

    # ----------------------------------------------------------------------
    # Trace-style check: old_color == color guard fires with zero mutation.
    # ----------------------------------------------------------------------
    print("\n--- edge case: color == old color must be a no-op, not a loop ---")
    grid = [[5, 5], [5, 5]]
    original = [row[:] for row in grid]
    t0 = time.perf_counter()
    result = sol.floodFill(grid, 0, 0, 5)
    elapsed_ms = (time.perf_counter() - t0) * 1000
    ok = result == original and elapsed_ms < 50
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  same-color fill returned instantly "
          f"({elapsed_ms:.3f} ms), grid unchanged: {result == original}")

    # ----------------------------------------------------------------------
    # ⚠️  LIVE DEMO: recursion depth vs sys.getrecursionlimit() on a snake.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  live demo: recursive DFS vs a long thin single-file grid ---")
    limit = sys.getrecursionlimit()
    # Pick a strip longer than the recursion limit so the recursive DFS's
    # call-stack depth (one frame per connected cell) provably exceeds it.
    n = limit + 500
    strip = make_strip(n)
    print(f"  sys.getrecursionlimit() = {limit}; strip length (component size) = {n}")

    raised = False
    try:
        sol.floodFill_recursive([row[:] for row in strip], 0, 0, 9)
        print("  recursive flood fill on the strip: did NOT raise this run")
    except RecursionError as e:
        raised = True
        print(f"  recursive flood fill on the strip: RecursionError -> {e!r}")

    iter_result = sol.floodFill([row[:] for row in strip], 0, 0, 9)
    iter_ok = iter_result == [[9] * n]
    print(f"  iterative (stack-based) flood fill on the SAME strip: "
          f"succeeded -> {iter_ok}, all {n} cells repainted")

    bfs_result = sol.floodFill_bfs([row[:] for row in strip], 0, 0, 9)
    bfs_ok = bfs_result == [[9] * n]
    print(f"  BFS flood fill on the SAME strip: succeeded -> {bfs_ok}")

    print(f"  iterative succeeded where recursive raised RecursionError: "
          f"{iter_ok and bfs_ok and raised}")
    all_ok &= iter_ok and bfs_ok and raised
    print("  Recursion depth for a flood fill equals the connected component's")
    print("  size in the worst (single-file) layout — a real trap once grids")
    print("  scale past a few hundred cells, which 002/003's own LeetCode")
    print("  constraints (up to 300x300 = 90,000 cells) reach easily.")

    # ----------------------------------------------------------------------
    # DFS vs BFS: identical final grid, different visit order.
    # ----------------------------------------------------------------------
    print("\n--- DFS vs BFS: same final grid, timing on a mid-size grid ---")
    side = 200
    big = [[7] * side for _ in range(side)]
    t0 = time.perf_counter()
    dfs_out = sol.floodFill([row[:] for row in big], 0, 0, 1)
    t1 = time.perf_counter()
    bfs_out = sol.floodFill_bfs([row[:] for row in big], 0, 0, 1)
    t2 = time.perf_counter()
    same = dfs_out == bfs_out
    all_ok &= same
    print(f"  {side}x{side} grid, {side * side} cells: DFS {1000*(t1-t0):.2f} ms, "
          f"BFS {1000*(t2-t1):.2f} ms, identical output: {same}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
