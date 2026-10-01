package main

/*
================================================================================
QUESTION · LeetCode 733 · Flood Fill                                   [Easy]
https://leetcode.com/problems/flood-fill/
================================================================================

PROBLEM
-------
You are given an `image` represented by an `m x n` grid of integers, where
`image[i][j]` is the pixel value of the pixel at (i, j). You are also given
three integers `sr`, `sc`, and `color`. Your task is to perform a "flood
fill" on the image starting from the pixel `image[sr][sc]`.

To perform the flood fill:
    1. Begin with the starting pixel and change its color to `color`.
    2. Perform the same process for each pixel that is DIRECTLY adjacent
       (up, down, left, right) to the starting pixel, either horizontally
       or vertically, and shares the SAME COLOR as the starting pixel.
    3. Keep repeating this process (step by step, expanding outward from the
       original pixel) as long as pixels match the original color of the
       starting pixel.

Return the modified image after performing the flood fill.


EXAMPLES
--------
Example 1:
    Input:  image = [[1,1,1],[1,1,0],[1,0,1]], sr = 1, sc = 1, color = 2
    Output: [[2,2,2],[2,2,0],[2,0,1]]

        start=1 1 1        1 (1,1)=1, flood from here with color=2
              1[1]0   ->   2 2 2
              1 0 1        2 2 0
                            2 0 1

    From (1,1) (value 1), the connected component of 1's reachable via
    4-directional moves is: (0,0)(0,1)(0,2)(1,0)(1,1). The 0 at (1,2) and
    (2,1) block the flood (different color), so they and the isolated 1 at
    (2,0)... wait — (2,0) IS connected via (1,0). Only (2,2)=1 is isolated
    from the start (blocked by 0's on both sides it would need to cross),
    so it stays 1.

Example 2:
    Input:  image = [[0,0,0],[0,0,0]], sr = 0, sc = 0, color = 0
    Output: [[0,0,0],[0,0,0]]

    The start pixel's color already equals `color`. Nothing visibly changes,
    but watch out: naively flooding anyway when old == new can infinite-loop
    (see hints).


CONSTRAINTS
-----------
    m == image.length
    n == image[i].length
    1 <= m, n <= 50
    0 <= image[i][j], color < 2^16
    0 <= sr < m
    0 <= sc < n


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This is graph traversal in disguise: every pixel is a node, and an edge
connects two orthogonally-adjacent pixels of the SAME starting color. Flood
fill = "visit every node reachable from (sr, sc) in this implicit graph and
relabel it." See the topic guide §6 (Islands / Grid-as-Graph) — this is the
simplest member of that family, with only one starting node instead of many.


PROGRESSIVE HINTS
------------------
Hint 1: DFS or BFS from (sr, sc), only stepping onto a neighbor whose current
        value equals `image[sr][sc]` (the ORIGINAL color, captured before you
        start overwriting).

Hint 2: What if `color == image[sr][sc]` already? If you flood-fill by
        checking "value == old color" and then immediately overwrite that
        cell to `color`, and `color == old color`, every cell still matches
        the condition forever — you never make progress and (with a naive
        recursive-revisit) can loop or blow the stack. Guard for this case
        up front and return immediately.

Hint 3: Use a `visited` set OR mutate in place and let the color-mismatch
        check double as the visited check — once a cell is repainted to
        `color`, it will only still equal the OLD color if old == new, which
        is exactly the case Hint 2 tells you to special-case away.


COMPLEXITY TARGET
------------------
    Time:  O(rows * cols) — every pixel visited at most once
    Space: O(rows * cols) worst case (recursion stack or BFS queue), for a
           grid that is entirely one color
================================================================================
*/

// TODO: Implement the stub
