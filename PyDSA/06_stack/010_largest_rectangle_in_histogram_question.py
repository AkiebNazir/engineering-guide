"""
================================================================================
LeetCode 84 · Largest Rectangle in Histogram                             [Hard]
https://leetcode.com/problems/largest-rectangle-in-histogram/
Topic: 06 · Stack
================================================================================

PROBLEM
-------
Given an array of integers `heights` representing the histogram's bar
heights where the width of each bar is 1, return the area of the largest
rectangle in the histogram.


EXAMPLES
--------
Example 1:
    Input:  heights = [2,1,5,6,2,3]
    Output: 10
    Explanation: the largest rectangle spans bars 2 and 3, limited to the
    shorter of them (height 5), giving 5 x 2 = 10.

        6 |          ##
        5 |       ## ##
        4 |       ## ##
        3 |       ## ##       ##
        2 | ##    ## ##  ##   ##
        1 | ## ## ## ##  ##   ##
          +----------------------
            2  1  5  6  2  3
                 ^^^^^
                 height 5 x width 2 = 10

Example 2:
    Input:  heights = [2,4]
    Output: 4
    Explanation: two candidates tie at 4 — height 4 over width 1, and
    height 2 over width 2.


CONSTRAINTS
-----------
    1 <= heights.length <= 10^5
    0 <= heights[i] <= 10^4


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================

Every candidate rectangle is limited in height by its SHORTEST bar. So
turn the question around: instead of enumerating rectangles, ask for each
bar `i`, "what is the widest rectangle in which bar `i` is the shortest
bar?" The maximum over all i of `heights[i] * that width` is the answer,
because the optimal rectangle's shortest bar is one of the bars.

That widest span is bounded by the NEAREST SHORTER BAR on each side:

    left  boundary = the nearest bar to the left  that is SHORTER than i
    right boundary = the nearest bar to the right that is SHORTER than i
    width = (right boundary index) - (left boundary index) - 1

"Nearest smaller element on each side, for every element" is the
monotonic stack's native question (topic guide §2.0-2.5). The stack holds
indices of bars in INCREASING height; when a shorter bar arrives, every
taller bar on the stack has just found its right boundary and can be
resolved and popped, with its left boundary being whatever the stack
exposes underneath it.


WHAT TO THINK ABOUT
--------------------
1. Why does considering "the widest rectangle in which bar i is the
   shortest" find the global optimum? What is the shortest bar of the
   optimal rectangle?
2. When bar `i` pops bar `j` off the stack, what exactly are `j`'s two
   boundaries — and why is the one on the left equal to whatever is left
   on the stack after the pop, rather than `j - 1`?
3. Write the width as `i - stack[-1] - 1` and then ask what happens when
   the stack becomes EMPTY after the pop. What is the left boundary then?
4. At the end of the loop some bars are still on the stack (nobody ever
   popped them). What is their right boundary, and what is the cheapest
   way to make the main loop handle them without a second block of code?
   (This is the SENTINEL trick, and running without it undercounts — try
   `[1,2,3,4,5]`.)


PROGRESSIVE HINTS
------------------
Hint 1: `stack = []` holding INDICES; bar heights on the stack increase
        from bottom to top. Iterate over `heights + [0]` — the appended
        zero-height sentinel bar is shorter than everything and flushes
        the stack at the end.

Hint 2: For each `(i, h)`: `while stack and heights[stack[-1]] >= h:` pop
        `j`, then `height = heights[j]` and
        `width = i if not stack else i - stack[-1] - 1`. Track the max of
        `height * width`. Then push `i`.

Hint 3: Careful with `heights[stack[-1]]` when `i == len(heights)` (the
        sentinel index is out of range for `heights`) — either index a
        local `extended = heights + [0]` list, or special-case the
        sentinel's height as 0.


COMPLEXITY TARGET
------------------
    Time:  O(n) — each index is pushed exactly once and popped at most
           once (topic guide §2.1), and every pop does O(1) work.
    Space: O(n) for the stack. Worst case is a strictly increasing
           histogram, where nothing pops until the sentinel arrives.

    The brute force to beat: for every bar, expand left and right while
    tracking the running minimum height — O(n^2), which times out at
    n = 10^5.
================================================================================
"""

from typing import List


class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 010_largest_rectangle_in_histogram_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([2, 1, 5, 6, 2, 3], 10),
        ([2, 4], 4),
        ([1], 1),
        ([1, 2, 3, 4, 5], 9),
        ([5, 4, 3, 2, 1], 9),
        ([2, 1, 2], 3),
        ([0, 0, 0], 0),
        ([4, 2, 0, 3, 2, 5], 6),
        ([6, 7, 5, 2, 4, 5, 9, 3], 16),
        ([3, 3, 3, 3], 12),
    ]

    passed = 0
    for heights, expected in cases:
        got = sol.largestRectangleArea(list(heights))
        ok = got == expected
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  heights={heights!r:<30} -> {got}  (want {expected})")

    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
