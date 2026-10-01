"""
================================================================================
SOLUTION · LeetCode 85 · Maximal Rectangle                                [Hard]
https://leetcode.com/problems/maximal-rectangle/
================================================================================

THE CORE IDEA
--------------
Every rectangle has a bottom row. Fix it, and the problem becomes
Largest Rectangle in Histogram (06_stack/010) on the column heights of 1s
ending at that row:

    heights[j] = heights[j] + 1   if matrix[r][j] == "1"
               = 0                otherwise

    answer = max over rows of largest_rectangle(heights)

One monotonic-stack pass per row, so O(rows * cols) in total.


================================================================================
APPROACH 1 · Every rectangle, counted with 2D prefix sums (priced, oracle)
================================================================================
Pick top-left and bottom-right corners (O(rows^2 * cols^2) choices) and check
"all ones" in O(1) with a prefix-sum table (area == count of ones).

    Time: O(rows^2 * cols^2)    Space: O(rows * cols)
    200 x 200 means 1.6 * 10^9 rectangles.


================================================================================
APPROACH 2 · Widths per cell, extend upward
================================================================================
width[r][c] = consecutive '1's ending at (r, c) in its row. For each cell,
walk upward taking the minimum width so far; area = min_width * rows_walked.

    Time: O(rows^2 * cols)    Space: O(rows * cols)


================================================================================
APPROACH 3 · Histogram per row + monotonic stack ✅ (the answer)
================================================================================
    heights = [0] * (cols + 1)                  # the extra slot stays 0: a sentinel
    best = 0
    for row in matrix:
        for j in range(cols):
            heights[j] = heights[j] + 1 if row[j] == "1" else 0
        stack = []                              # indices of increasing heights
        for j in range(cols + 1):               # the sentinel flushes the stack
            while stack and heights[stack[-1]] >= heights[j]:
                top = stack.pop()
                left = stack[-1] + 1 if stack else 0
                best = max(best, heights[top] * (j - left))
            stack.append(j)

When a bar is popped, the bar that pops it is the first lower bar to its
RIGHT, and the new stack top is the first lower bar to its LEFT: the widest
rectangle at that bar's height fits exactly between them. Each index is
pushed and popped once per row.

    Time: O(rows * cols)    Space: O(cols)


================================================================================
STEP BY STEP TRACE · Example 1, bottom row = row 2
================================================================================
    heights after row 0: [1, 0, 1, 0, 0]
    heights after row 1: [2, 0, 2, 1, 1]
    heights after row 2: [3, 1, 3, 2, 2]

    histogram [3, 1, 3, 2, 2, 0(sentinel)]:
      j=0 push 0                              stack [0]
      j=1 h=1: pop 0 (h=3): width 1 -> 3      stack [1]
      j=2 push 2                              stack [1, 2]
      j=3 h=2: pop 2 (h=3): width 1 -> 3      stack [1, 3]
      j=4 h=2: pop 3 (h=2): left=2, width 2 -> 4    stack [1, 4]
      j=5 h=0: pop 4 (h=2): left=2, width 3 -> 6    <- the answer
               pop 1 (h=1): left=0, width 5 -> 5

    best over all rows = 6


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time                 Space        Mutates input?
    -----------------------------  -------------------  -----------  --------------
    All rectangles + prefix sums   O(r^2 * c^2)         O(r * c)     No
    Widths, extend upward          O(r^2 * c)           O(r * c)     No
    Histogram + stack ✅           O(r * c)             O(c)         No


================================================================================
EDGE CASES
================================================================================
    All '0'           0.
    All '1'           rows * cols.
    One row / column  The longest run of '1's.
    Checkerboard      1 — no two adjacent ones.


================================================================================
COMMON MISTAKES
================================================================================
1. Truthiness of strings. `if cell:` is True for "0" as well as "1", because
   any non-empty string is truthy — every cell counts as a one. Demo.

2. Not resetting the height on a '0' (heights[j] += cell == "1"): bars keep
   ones from above a gap, forming rectangles through zeros. Demo.

3. No sentinel: bars still on the stack at the end of the row are never
   measured, so rectangles touching the right edge are missed. Demo.

4. Reusing Maximal Square's DP (min of three neighbours + 1). It finds the
   largest SQUARE; a 1 x 4 row of ones has area 4 but square 1. Demo.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the rectangle's coordinates?
A: When a pop improves `best`, record (row, left, right, height): the top row
   is row - height + 1.

Q: Largest rectangle containing only '0's?
A: Swap the roles of '0' and '1' in the height update.

Q: Count all all-ones submatrices (LC 1504)?
A: The same per-row heights with a monotonic stack that accumulates counts
   instead of a maximum.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 84   Largest Rectangle in Histogram (010)  — the inner routine
    LC 221  Maximal Square (17_dp_2d/004)         — squares only: a simpler DP
    LC 1504 Count Submatrices With All Ones       — counting version
    LC 42   Trapping Rain Water (02_two_pointers/010) — another histogram problem
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def maximalRectangle(self, matrix: List[List[str]]) -> int:
        if not matrix or not matrix[0]:
            return 0
        cols = len(matrix[0])
        heights = [0] * (cols + 1)                      # last slot stays 0: the sentinel
        best = 0
        for row in matrix:
            for j in range(cols):
                heights[j] = heights[j] + 1 if row[j] == "1" else 0
            stack = []
            for j in range(cols + 1):
                h = heights[j]
                while stack and heights[stack[-1]] >= h:
                    top = stack.pop()
                    left = stack[-1] + 1 if stack else 0
                    area = heights[top] * (j - left)
                    if area > best:
                        best = area
                stack.append(j)
        return best


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def all_rectangles(matrix: List[List[str]]) -> int:
    """Oracle: every rectangle, checked with a 2D prefix sum."""
    r, c = len(matrix), len(matrix[0])
    P = [[0] * (c + 1) for _ in range(r + 1)]
    for i in range(r):
        for j in range(c):
            P[i + 1][j + 1] = P[i][j + 1] + P[i + 1][j] - P[i][j] + (matrix[i][j] == "1")
    best = 0
    for i1 in range(r):
        for i2 in range(i1, r):
            for j1 in range(c):
                for j2 in range(j1, c):
                    area = (i2 - i1 + 1) * (j2 - j1 + 1)
                    ones = P[i2 + 1][j2 + 1] - P[i1][j2 + 1] - P[i2 + 1][j1] + P[i1][j1]
                    if ones == area and area > best:
                        best = area
    return best


def widths_upward(matrix: List[List[str]]) -> int:
    """Approach 2."""
    r, c = len(matrix), len(matrix[0])
    width = [[0] * c for _ in range(r)]
    best = 0
    for i in range(r):
        for j in range(c):
            if matrix[i][j] == "1":
                width[i][j] = (width[i][j - 1] if j else 0) + 1
                w = width[i][j]
                for k in range(i, -1, -1):
                    w = min(w, width[k][j])
                    if w == 0:
                        break
                    best = max(best, w * (i - k + 1))
    return best


def histogram(heights: List[int], sentinel: bool = True) -> int:
    hs = heights + [0] if sentinel else heights
    stack, best = [], 0
    for j, h in enumerate(hs):
        while stack and hs[stack[-1]] >= h:
            top = stack.pop()
            left = stack[-1] + 1 if stack else 0
            best = max(best, hs[top] * (j - left))
        stack.append(j)
    return best


def truthy_bug(matrix: List[List[str]]) -> int:
    """Mistake 1: `if cell` — "0" is a non-empty string, so it's truthy."""
    heights, best = [0] * len(matrix[0]), 0
    for row in matrix:
        heights = [h + 1 if cell else 0 for h, cell in zip(heights, row)]
        best = max(best, histogram(heights))
    return best


def no_reset_bug(matrix: List[List[str]]) -> int:
    """Mistake 2: heights never drop to 0."""
    heights, best = [0] * len(matrix[0]), 0
    for row in matrix:
        heights = [h + (cell == "1") for h, cell in zip(heights, row)]
        best = max(best, histogram(heights))
    return best


def no_sentinel_bug(matrix: List[List[str]]) -> int:
    """Mistake 3: bars left on the stack are never measured."""
    heights, best = [0] * len(matrix[0]), 0
    for row in matrix:
        heights = [h + 1 if cell == "1" else 0 for h, cell in zip(heights, row)]
        best = max(best, histogram(heights, sentinel=False))
    return best


def max_square_area(matrix: List[List[str]]) -> int:
    """Mistake 4: Maximal Square's DP."""
    r, c = len(matrix), len(matrix[0])
    dp = [[0] * (c + 1) for _ in range(r + 1)]
    side = 0
    for i in range(r):
        for j in range(c):
            if matrix[i][j] == "1":
                dp[i + 1][j + 1] = min(dp[i][j], dp[i][j + 1], dp[i + 1][j]) + 1
                side = max(side, dp[i + 1][j + 1])
    return side * side


# ==============================================================================
# TESTS — run:  python 016_maximal_rectangle_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()
    ex1 = [["1", "0", "1", "0", "0"], ["1", "0", "1", "1", "1"],
           ["1", "1", "1", "1", "1"], ["1", "0", "0", "1", "0"]]

    print("--- correctness: histogram+stack vs widths-upward vs all rectangles ---")
    cases = [(ex1, 6), ([["0"]], 0), ([["1"]], 1), ([["1", "1", "1", "1"]], 4), ([["1"], ["1"], ["1"]], 3),
             ([["0", "1"], ["1", "0"]], 1),
             ([["1", "1", "0", "1"], ["1", "1", "0", "1"], ["1", "1", "1", "1"]], 6)]
    for matrix, want in cases:
        results = (sol.maximalRectangle(matrix), widths_upward(matrix), all_rectangles(matrix))
        ok = all(x == want for x in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {len(matrix)}x{len(matrix[0])}  got={results}  want={want}")

    print("\n--- randomized cross-check vs all rectangles (500 matrices up to 7x7) ---")
    rng = random.Random(85)
    bad = 0
    for _ in range(500):
        r, c = rng.randint(1, 7), rng.randint(1, 7)
        p = rng.random()
        m = [["1" if rng.random() < p else "0" for _ in range(c)] for _ in range(r)]
        want = all_rectangles(m)
        if sol.maximalRectangle(m) != want or widths_upward(m) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 random matrices agree with brute force")

    print("\n--- mistakes LIVE ---")
    w1 = truthy_bug(ex1)
    ok = w1 == 20 and sol.maximalRectangle(ex1) == 6
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  `if cell` (\"0\" is truthy): example 1 -> {w1} (the whole 4x5 grid), want 6")
    gap = [["1", "1"], ["0", "0"], ["1", "1"]]
    w2 = no_reset_bug(gap)
    ok = w2 == 4 and sol.maximalRectangle(gap) == 2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  heights never reset on '0': rows 11/00/11 -> {w2} "
          f"(a rectangle through the zero row), want 2")
    edge = [["0", "1", "1", "1"]]
    w3 = no_sentinel_bug(edge)
    ok = w3 != 3 and sol.maximalRectangle(edge) == 3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no sentinel: [0,1,1,1] -> {w3}, want 3 (it touches the right edge)")
    row = [["1", "1", "1", "1"]]
    w4 = max_square_area(row)
    ok = w4 == 1 and sol.maximalRectangle(row) == 4
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  Maximal Square DP on a 1x4 row -> {w4}, want 4")

    print("\n--- scale: 200 x 200, 70% ones ---")
    big = [["1" if rng.random() < 0.7 else "0" for _ in range(200)] for _ in range(200)]
    t0 = time.perf_counter(); a = sol.maximalRectangle(big); t1 = time.perf_counter()
    b = widths_upward(big); t2 = time.perf_counter()
    ok = a == b
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  histogram+stack {1000 * (t1 - t0):.0f} ms vs widths-upward "
          f"{1000 * (t2 - t1):.0f} ms, both {a}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
