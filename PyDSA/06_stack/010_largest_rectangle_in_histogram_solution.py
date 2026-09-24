"""
================================================================================
SOLUTION · LeetCode 84 · Largest Rectangle in Histogram                  [Hard]
https://leetcode.com/problems/largest-rectangle-in-histogram/
================================================================================

THE CORE IDEA
--------------
Every rectangle is capped by its SHORTEST bar. So the optimal rectangle,
whatever it is, has some bar `i` as its shortest bar — and given that bar,
the best rectangle is the WIDEST one that keeps `i` as the shortest. So:

    for each bar i:  area_i = heights[i] * (widest span in which i is the
                                            shortest bar)
    answer = max(area_i)

This is exhaustive (the optimum's shortest bar is one of the n bars) and
it replaces "enumerate O(n^2) rectangles" with "answer one question per
bar." That question is:

    left  boundary = index of the nearest bar to the LEFT  that is SHORTER
    right boundary = index of the nearest bar to the RIGHT that is SHORTER
    width          = right - left - 1

**Nearest smaller element on both sides, for every element** is the
monotonic stack's native question (topic guide §2.0-2.5). One pass
computes both boundaries at once, because the moment a shorter bar arrives
it IS the right boundary for everything taller waiting on the stack, and
what remains on the stack below a popped bar IS its left boundary.

```python
def largestRectangleArea(heights):
    stack = []                      # indices; heights INCREASE bottom -> top
    best = 0
    for i, h in enumerate(heights + [0]):        # 0 = sentinel, flushes all
        while stack and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            width = i if not stack else i - stack[-1] - 1
            best = max(best, height * width)
        stack.append(i)
    return best
```

O(n) time, O(n) space.


================================================================================
THE WIDTH FORMULA — `i - stack[-1] - 1`, DERIVED, NOT MEMORISED
================================================================================
This is the line everybody gets wrong under pressure. Derive it from the
picture and it becomes obvious.

Say bar `j` is being popped because bar `i` is shorter than it. After the
pop, let `L = stack[-1]` be the new top.

    indices:   ... L   L+1  L+2  ...  j  ... i-1   i
                   ^                            ^
                   |                            |
        nearest SHORTER bar                nearest SHORTER bar
        to the LEFT of j                   to the RIGHT of j
        (everything between L and j        (i is the first bar shorter
         is TALLER than j — that is         than j scanning right, which
         the stack's invariant: it was       is exactly why j is being
         popped away already, or was        popped right now)
         never taller-blocking)

    So bar j's rectangle occupies the CLOSED index range [L+1, i-1]:
        width = (i - 1) - (L + 1) + 1 = i - L - 1 = i - stack[-1] - 1

    And if the stack is EMPTY after the pop, there is no shorter bar to the
    left at all, so the rectangle starts at index 0:
        width = (i - 1) - 0 + 1 = i

Two sanity checks you can do in your head:
    - popping j when `i == j + 1` and the stack is empty gives width 1
      (a single bar) — the smallest possible rectangle. ✓
    - popping the last remaining bar at the sentinel index `i == n` with an
      empty stack gives width `n` — the full histogram, which is right for
      the global minimum bar. ✓

⚠️ It is `stack[-1]` AFTER the pop, not before, and not `j - 1`. Using
`j - 1` gives width 0-ish nonsense; using the pre-pop top gives `j`
itself. Pop first, then read the stack.


================================================================================
THE SENTINEL BAR — WHY, AND WHAT HAPPENS WITHOUT IT
================================================================================
When the loop ends, bars may still be on the stack: every bar with no
shorter bar anywhere to its right. Their rectangles were never computed,
so their areas were never considered. The fix is either

    (a) a second loop after the main one that drains the stack with
        `i = n` as the right boundary, or
    (b) **append a zero-height sentinel bar** and let the main loop do it.

(b) is strictly better in an interview: zero is `<=` every possible height
(the constraints allow `heights[i] == 0`, and 0 >= 0 still pops), so the
sentinel pops EVERYTHING, and the right boundary it supplies is exactly
`i = n`, which is what version (a) would have hard-coded. One fewer block
of code, one fewer place to get the boundary wrong.

**Without the sentinel the answer is silently too small.** Measured in the
runtime demo:

    heights = [1,2,3,4,5]   with sentinel: 9    without: 0
    heights = [2,1,2]        with sentinel: 3    without: 2
    heights = [2,4]          with sentinel: 4    without: 0
    heights = [4,2,0,3,2,5]  with sentinel: 6    without: 4

    ... and over 3000 random histograms the sentinel-free version is wrong
    on 1226 of them. Note the pattern: it is wrong exactly when the answer
    involves a bar that never meets a shorter bar on its right — which
    includes every strictly increasing histogram, where it returns 0.

⚠️ Implementation detail: with `heights + [0]` the loop variable `i`
reaches `n`, which is a valid index of the EXTENDED list but not of
`heights`. Iterate `enumerate(heights + [0])` and index only
`heights[stack[-1]]` (always a real bar, since only real indices are ever
pushed before the sentinel) — or bind `ext = heights + [0]` and use `ext`
everywhere. Do NOT write `heights[i]` inside the loop; that is an
IndexError on the sentinel step. This file's implementation avoids
allocating the concatenated list at all by treating `i == n` as height 0.


================================================================================
`>=` OR `>` IN THE POP CONDITION? BOTH WORK — HERE IS WHY
================================================================================
With `heights[stack[-1]] >= h` (this file's choice) equal-height bars pop
each other. That means an earlier bar in a run of equal heights is
resolved with a width that is TOO SMALL — its true right boundary is
further along, past its equal-height twins.

That does not break the answer, and the reason is worth saying out loud:
**the LAST bar of a run of equal heights gets the full, correct span**, and
since all bars in the run have the same height, the maximum area over the
run is computed correctly by that last bar. The under-measured earlier
pops are dominated, never chosen.

Trace `[3,3,3,3]` (this file's tests include it):

    i=1: pops bar 0 -> width 1 -> area 3    (too small, harmless)
    i=2: pops bar 1 -> width 2 -> area 6    (too small, harmless)
    i=3: pops bar 2 -> width 3 -> area 9    (too small, harmless)
    i=4 (sentinel): pops bar 3 -> stack empty -> width 4 -> area 12  ✓

With strict `>` instead, equal bars accumulate on the stack and the
EARLIEST one of the run is popped with the full span — also correct, and
it computes fewer, larger intermediate areas. Both variants are
implemented here and cross-checked against each other on thousands of
random inputs: 0 disagreements. Pick one and be able to justify it; what
you must NOT do is claim `>=` is a bug.


================================================================================
THE ALTERNATIVES — state them, price them
================================================================================
**Brute force, expand from each bar.** For every `i`, walk left and right
while tracking the running minimum:

    for i: mn = heights[i]; for j >= i: mn = min(mn, heights[j]);
           best = max(best, mn * (j - i + 1))

O(n^2) time, O(1) space. Correct, and it times out at n = 10^5 (10^10
operations). Measured here: at n = 3200 the stack takes ~0.4ms and the
brute force ~220ms, about **520x**; the ratio grows linearly with n
(58x at n = 400, 126x at 800, 272x at 1600, 520x at 3200).

**Two explicit passes (previous-smaller, then next-smaller).** Compute two
arrays with two separate monotonic stacks, then combine:

    left[i]  = (index of previous strictly-smaller bar) + 1
    right[i] = (index of next strictly-smaller bar) - 1
    best     = max over i of heights[i] * (right[i] - left[i] + 1)

Same O(n) time, O(n) extra space, three loops instead of one. It is SLOWER
and longer — but it is the version to write when the interviewer asks for
the boundaries themselves, or when you want to make the
"previous-smaller / next-smaller" framing explicit and auditable. It is
also the shape that generalises to LC 907 (sum of subarray minimums),
where you need each element's span as a value, not just the max area. Both
are implemented and cross-checked in this file.

**Divide and conquer.** Find the minimum bar, take the best of
{full width x min height, best in the left part, best in the right part}.
O(n log n) average with an O(1) range-minimum structure (sparse
table/segment tree), but **O(n^2) worst case** on a sorted histogram if
you find the minimum by scanning. Worth naming; never the answer you code.


================================================================================
STEP BY STEP TRACE
================================================================================
heights = [2, 1, 5, 6, 2, 3]   (n = 6; the sentinel is a virtual bar of
                                height 0 at index 6)

        6 |          ##
        5 |       ## ##
        4 |       ## ##
        3 |       ## ##       ##
        2 | ##    ## ##  ##   ##
        1 | ## ## ## ##  ##   ##
          +----------------------
       idx   0  1  2  3  4  5    (6 = sentinel, height 0)

    i  h   stack before  action                                              stack after  best
    -  --  ------------  --------------------------------------------------  -----------  ----
    0   2  []            nothing shorter to compare; push 0                   [0]           0
    1   1  [0]           h[0]=2 >= 1: pop 0. stack now empty -> width = i = 1
                         area = 2 * 1 = 2                                     -             2
                         h... stack empty, stop; push 1                       [1]           2
    2   5  [1]           h[1]=1 >= 5? no; push 2                              [1,2]         2
    3   6  [1,2]         h[2]=5 >= 6? no; push 3                              [1,2,3]       2
    4   2  [1,2,3]       h[3]=6 >= 2: pop 3. new top = 2
                         width = 4 - 2 - 1 = 1, area = 6 * 1 = 6              [1,2]         6
                         h[2]=5 >= 2: pop 2. new top = 1
                         width = 4 - 1 - 1 = 2, area = 5 * 2 = 10  <-- ANSWER [1]          10
                         h[1]=1 >= 2? no, stop; push 4                        [1,4]        10
    5   3  [1,4]         h[4]=2 >= 3? no; push 5                              [1,4,5]      10
    6   0  [1,4,5]       SENTINEL — pops everything:
       (sentinel)        h[5]=3 >= 0: pop 5. new top = 4
                         width = 6 - 4 - 1 = 1, area = 3 * 1 = 3              [1,4]        10
                         h[4]=2 >= 0: pop 4. new top = 1
                         width = 6 - 1 - 1 = 4, area = 2 * 4 = 8              [1]          10
                         h[1]=1 >= 0: pop 1. stack empty -> width = i = 6
                         area = 1 * 6 = 6                                     []           10
                         push 6                                               [6]          10

    answer = 10   ✓

    The two rectangles the sentinel found — height 2 x width 4 = 8 and
    height 1 x width 6 = 6 — did not win here, but they are the only
    rectangles anchored on bars that never meet a shorter bar to their
    right. Delete the sentinel and they are never even considered. On
    [1,2,3,4,5] that is EVERY bar, and the sentinel-free answer is 0.

    Also note bar 3 (height 6) got width 1, and bar 2 (height 5) got
    width 2 spanning indices [2,3] — bar 2's rectangle is allowed to
    include bar 3 because bar 3 is TALLER. That is what "widest span in
    which I am the shortest" means, and it is why the left boundary is
    read from the stack (which has already discarded all the taller bars
    in between) rather than from `j - 1`.


================================================================================
LC 85 AND LC 42 ARE THE SAME FAMILY
================================================================================
This is not a standalone puzzle; it is the engine for two other classics.

**LC 85 · Maximal Rectangle** (largest all-1s rectangle in a binary
matrix) is *this function called once per row*. Maintain a running
histogram where `heights[c]` = the number of consecutive 1s ending at the
current row in column `c` (reset to 0 on a '0'), and take the max over
rows of `largestRectangleArea(heights)`. O(rows x cols) total. The
runtime demo below does exactly this — importing nothing new, calling this
file's own solution — and gets 6 on the standard LC 85 example. If you can
do 84, you have already done 85; that is worth saying in an interview
before the interviewer asks.

**LC 42 · Trapping Rain Water** is the mirror image: instead of the
nearest SHORTER bar on each side bounding an area, the highest bar on each
side bounds the water level, and water at `i` is
`min(maxLeft, maxRight) - heights[i]`. The monotonic-stack solution is the
same push/pop/resolve skeleton with a DECREASING stack and "water above
the popped bar" as the payload (topic guide §2.3's table, one more row).
The usual two-pointer solution is 42's own trick and does not transfer to
84 — because 84 needs both boundaries per bar, not a single global water
level.

**The general framing to carry away:** whenever a problem asks for
something computed over a maximal span bounded by "the nearest element
that breaks a monotonic condition," it is this stack. The payload changes
(a value in 496, a distance in 739, a span in 901, an area here, a volume
in 42, a count of subarrays in 907); the skeleton does not.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time         Space   Mutates input?  Note
    ------------------------------------  -----------  ------  --------------  ------------------------
    Brute force: expand from each bar     O(n^2)       O(1)    no              times out at n = 10^5;
      tracking the running min                                                   ~600x slower at n=3200
    Divide and conquer on the minimum     O(n log n)   O(n)    no              O(n^2) worst case
      bar                                   average                              without a range-min
                                                                                 structure; never code it
    Two passes: previous-smaller +        O(n)         O(n)    no              correct, more code; the
      next-smaller arrays, then combine                                          version to write when
                                                                                 you need the boundaries
    One-pass monotonic stack + sentinel ✅ O(n)        O(n)    no              the answer
    Same, sentinel omitted                O(n)         O(n)    no              ✗ WRONG (undercounts —
                                                                                 wrong on 1226/3000
                                                                                 random inputs)

    No approach here mutates `heights`. The sentinel is applied as a
    virtual bar (`i == n` treated as height 0), so not even a copy of the
    input is made — worth mentioning, since `heights.append(0)` WOULD
    mutate the caller's list, and `heights + [0]` allocates a full copy.


================================================================================
EDGE CASES
================================================================================
    Single bar [5]              -> the sentinel pops it with an empty
                                   stack, width = i = 1, area 5.
    Strictly INCREASING          -> nothing pops until the sentinel; the
      [1,2,3,4,5]                  stack holds all n indices (worst case for
                                   space), and EVERY area is discovered
                                   during the sentinel flush. Without the
                                   sentinel the answer is 0 — the single
                                   most important test in this problem.
    Strictly DECREASING           -> every bar pops the previous one
      [5,4,3,2,1]                  immediately; the stack never holds more
                                   than one or two entries. Answer 9
                                   (height 1 x width 5 = 5, height 3 x
                                   width 3 = 9).
    ALL EQUAL [3,3,3,3]           -> the `>=` vs `>` case; the last pop is
                                   the one that measures the full width.
                                   Answer 12.
    ZEROS present [4,2,0,3,2,5]   -> heights[i] == 0 is allowed by the
                                   constraints. A zero bar contributes area
                                   0 itself and acts as a hard divider,
                                   because nothing can span across it. Note
                                   `>= 0` still pops equal-zero bars, which
                                   is why the sentinel's 0 flushes a
                                   trailing zero bar too.
    ALL ZEROS [0,0,0]             -> answer 0. Exercises that `best` starts
                                   at 0 and that a 0-height pop does not
                                   crash the width arithmetic.
    A valley [6,7,5,2,4,5,9,3]    -> the answer (16) spans the valley floor;
                                   good check that the left boundary comes
                                   from the stack rather than from j-1.
    n = 10^5, heights up to 10^4  -> the max possible area is 10^9, which
                                   overflows 32-bit int in C/Java/Go but is
                                   fine in Python's arbitrary-precision
                                   ints. Worth naming when interviewing in
                                   another language.


================================================================================
COMMON MISTAKES
================================================================================
1. **Omitting the sentinel** (and not draining the stack afterwards).
   Silently undercounts; returns 0 on any strictly increasing histogram.
   Measured: wrong on 1226 of 3000 random inputs.

2. **`width = i - j - 1`** (using the POPPED index) or **`width = j - stack[-1]`**.
   The width is measured between the two BOUNDARIES, and `j` is inside the
   rectangle, not a boundary. It is `i - stack[-1] - 1` with `stack[-1]`
   read AFTER the pop.

3. **Forgetting the empty-stack case** (`width = i`). When nothing remains
   below the popped bar, there is no left boundary and the rectangle runs
   to index 0. Writing `i - stack[-1] - 1` unguarded raises IndexError on
   an empty stack, or — worse, in Python — silently reads `stack[-1]` of a
   non-empty stack you thought was empty.

4. **Pushing heights instead of indices.** The width needs positions.
   Same lesson as problem 007's mistake 1; a monotonic stack that computes
   a width or a distance must hold indices.

5. **`heights[i]` inside the loop when the sentinel is in play.**
   IndexError at `i == n`. Either iterate the extended list, or treat
   `i == n` as height 0 (this file does the latter).

6. **`heights.append(0)`** to add the sentinel — mutates the caller's
   list. Use `heights + [0]` (a copy) or a virtual sentinel.

7. **Believing `>=` is a bug** because early equal-height pops measure
   narrow widths. They do, and it does not matter — see the `>=` vs `>`
   section. Being able to explain this is a differentiator; "I use `>=`
   because that's what I memorised" is not.

8. **Trying to track the running minimum inside the stack loop** ("keep
   the min height of the current span"). The stack already encodes it:
   the popped bar IS the limiting height of its own rectangle. Extra
   bookkeeping here is a sign the invariant is not clear yet.

9. **Resetting `best` or the stack per bar.** One pass, one stack, one
   running maximum. If your loop reinitialises anything per bar you have
   written the O(n^2) version with extra steps.

10. **Not stating the reduction** ("for each bar, the widest span where it
    is the shortest") before coding. Without it the code looks like magic
    and you cannot recover if you slip; with it, the width formula is
    re-derivable at the whiteboard.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the rectangle itself (left index, right index, height), not just
   the area.
A: At each pop, the rectangle is `[stack[-1] + 1, i - 1]` at height
   `heights[j]`. Keep the best triple alongside the best area. No change
   in complexity.

Q: Now solve LC 85, Maximal Rectangle in a binary matrix.
A: Run this function once per row on a running per-column count of
   consecutive 1s. O(rows x cols). Demonstrated at runtime in this file.

Q: What if bars had varying widths (bar i has width w[i])?
A: The same stack works with prefix sums of widths: the "width" of a
   popped bar's rectangle becomes `prefix[i] - prefix[stack[-1] + 1]`
   instead of a count of indices. Positions become coordinates; nothing
   else changes.

Q: Can you do it in O(1) extra space?
A: Not with this technique — the stack is inherent. The O(n^2) brute force
   is O(1) space, so there is a real time/space trade to name, but at
   n = 10^5 the O(n) stack (800KB of Python ints, far less in C) is
   obviously the right side of it.

Q: What if the histogram arrives as a stream, one bar at a time?
A: Reporting the best-so-far after each bar is fine — but only for bars
   already resolved. A bar still on the stack has no right boundary yet,
   so its area is not final. You can maintain "best among resolved" in
   O(1) amortized and finalise with a virtual sentinel whenever the
   caller asks for the current answer. Contrast with problem 009, where
   every call's answer IS final because it only looks backwards.

Q: How is this different from Trapping Rain Water?
A: Both are "bounded by the nearest breaking bar on each side," but 42
   bounds by the nearest TALLER bar and accumulates a volume, while 84
   bounds by the nearest SHORTER bar and maximises an area. See the
   LC 85 / LC 42 section above.

Q: Why is the total work O(n) when the inner `while` can run n times?
A: Each index is pushed exactly once and popped at most once, so total
   pops across the whole run are at most n — topic guide §2.1's amortized
   argument, identical to the sliding window's inner loop in topic 03.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
Directly built on this function:

    LC 84    Largest Rectangle in Histogram — THIS FILE
    LC 85    Maximal Rectangle              — this function once per row of
                                               a binary matrix (demoed here)
    LC 1793  Maximum Score of a Good         — same "expand while I stay the
             Subarray                          minimum" span logic, with the
                                               constraint that the span must
                                               contain a given index
    LC 907   Sum of Subarray Minimums        — each element's span, but
                                               COUNTED (left x right
                                               subarrays) instead of maxed
    LC 2818  Apply Operations to Maximize     — previous/next-greater spans
             Score                             again, with a product payload

Same monotonic-stack skeleton, different payload (topic guide §2.3):

    LC 42    Trapping Rain Water             — nearest TALLER on each side,
                                               payload = trapped volume
    LC 496   Next Greater Element I          — 003 here: the bare template
    LC 739   Daily Temperatures              — 007 here: payload = distance
    LC 853   Car Fleet                       — 008 here: sort first, then
                                               absorb instead of pop
    LC 901   Online Stock Span               — 009 here: streaming, spans
    LC 962   Maximum Width Ramp              — a monotonic stack built in one
                                               direction and consumed in the
                                               other
    LC 1019  Next Greater Node in a           — the template over a linked
             Linked List                       list

Adjacent but NOT this pattern (know the difference):

    LC 221   Maximal Square                  — DP on the matrix, O(rows x
                                               cols); the square constraint
                                               makes a stack unnecessary
    LC 11    Container With Most Water        — two pointers converging, not
                                               a stack: the height is
                                               min(left, right), not a
                                               nearest-smaller boundary
================================================================================
"""

import random
import time
from typing import List, Tuple


class Solution:
    def largestRectangleArea(self, heights: List[int]) -> int:
        """One-pass monotonic increasing stack with a virtual zero-height
        sentinel bar. O(n) time, O(n) space. The answer.
        See THE CORE IDEA above."""
        n = len(heights)
        stack: List[int] = []            # indices; heights increase bottom -> top
        best = 0
        for i in range(n + 1):           # i == n is the virtual sentinel bar
            h = heights[i] if i < n else 0
            while stack and heights[stack[-1]] >= h:
                height = heights[stack.pop()]
                # width spans [stack[-1] + 1, i - 1]; if the stack is empty
                # there is no shorter bar to the left, so it starts at 0.
                width = i if not stack else i - stack[-1] - 1
                best = max(best, height * width)
            stack.append(i)
        return best

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def largestRectangleArea_strict(self, heights: List[int]) -> int:
        """Same algorithm with STRICT `>` in the pop condition: equal bars
        accumulate and the earliest of a run measures the full span. Also
        correct — see the `>=` or `>` section."""
        n = len(heights)
        stack: List[int] = []
        best = 0
        for i in range(n + 1):
            h = heights[i] if i < n else -1     # -1 so even zero bars pop
            while stack and heights[stack[-1]] > h:
                height = heights[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                best = max(best, height * width)
            stack.append(i)
        return best

    def largestRectangleArea_two_pass(self, heights: List[int]) -> int:
        """Explicit previous-smaller / next-smaller arrays, then combine.
        O(n) time, O(n) space, three loops. The version to write when the
        interviewer wants the boundaries themselves."""
        n = len(heights)
        if n == 0:
            return 0
        left = [0] * n           # leftmost index the rectangle at i can reach
        right = [0] * n          # rightmost index it can reach
        stack: List[int] = []
        for i in range(n):
            while stack and heights[stack[-1]] >= heights[i]:
                stack.pop()
            left[i] = stack[-1] + 1 if stack else 0
            stack.append(i)
        stack = []
        for i in range(n - 1, -1, -1):
            while stack and heights[stack[-1]] >= heights[i]:
                stack.pop()
            right[i] = stack[-1] - 1 if stack else n - 1
            stack.append(i)
        return max(heights[i] * (right[i] - left[i] + 1) for i in range(n))

    def largestRectangleArea_brute(self, heights: List[int]) -> int:
        """O(n^2) oracle: for every start, extend right tracking the running
        minimum height."""
        best = 0
        n = len(heights)
        for i in range(n):
            mn = heights[i]
            for j in range(i, n):
                if heights[j] < mn:
                    mn = heights[j]
                area = mn * (j - i + 1)
                if area > best:
                    best = area
        return best

    def largestRectangleArea_no_sentinel(self, heights: List[int]) -> int:
        """✗ BUGGY on purpose: no sentinel bar and no drain loop, so bars
        left on the stack at the end are never resolved."""
        stack: List[int] = []
        best = 0
        for i, h in enumerate(heights):
            while stack and heights[stack[-1]] >= h:
                height = heights[stack.pop()]
                width = i if not stack else i - stack[-1] - 1
                best = max(best, height * width)
            stack.append(i)
        return best

    def largestRectangleArea_bad_width(self, heights: List[int]) -> int:
        """✗ BUGGY on purpose: `width = i - j - 1` using the POPPED index
        instead of the new stack top."""
        n = len(heights)
        stack: List[int] = []
        best = 0
        for i in range(n + 1):
            h = heights[i] if i < n else 0
            while stack and heights[stack[-1]] >= h:
                j = stack.pop()
                width = i - j - 1                     # <-- wrong boundary
                best = max(best, heights[j] * width)
            stack.append(i)
        return best

    # ------------------------------------------------------------------
    # LC 85 · Maximal Rectangle, built ON TOP of the solution above.
    # ------------------------------------------------------------------
    def maximalRectangle(self, matrix: List[List[str]]) -> int:
        """LC 85 in six lines, by reusing largestRectangleArea per row:
        heights[c] = consecutive 1s ending at this row in column c."""
        if not matrix or not matrix[0]:
            return 0
        cols = len(matrix[0])
        heights = [0] * cols
        best = 0
        for row in matrix:
            for c, cell in enumerate(row):
                heights[c] = heights[c] + 1 if cell == "1" else 0
            best = max(best, self.largestRectangleArea(heights))
        return best

    @staticmethod
    def boundaries(heights: List[int]) -> List[Tuple[int, int, int]]:
        """For the trace/demo: (prev-smaller index, next-smaller index,
        width) per bar, computed the slow obvious way."""
        n = len(heights)
        out = []
        for i in range(n):
            lo = i - 1
            while lo >= 0 and heights[lo] >= heights[i]:
                lo -= 1
            hi = i + 1
            while hi < n and heights[hi] >= heights[i]:
                hi += 1
            out.append((lo, hi, hi - lo - 1))
        return out


# ==============================================================================
# TESTS — run:  python 010_largest_rectangle_in_histogram_solution.py
# ==============================================================================
CASES = [
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
    ([0], 0),
    ([10000] * 10, 100000),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: one-pass stack + sentinel ---")
    for heights, expected in CASES:
        got = sol.largestRectangleArea(list(heights))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  heights={heights!r:<32} -> {got}  (want {expected})")

    print("\n--- the four CORRECT approaches must agree ---")
    print(f"  {'heights':<32} {'one-pass':>9} {'strict >':>9} {'two-pass':>9} {'brute':>7}")
    for heights, expected in CASES:
        a = sol.largestRectangleArea(list(heights))
        b = sol.largestRectangleArea_strict(list(heights))
        c = sol.largestRectangleArea_two_pass(list(heights))
        d = sol.largestRectangleArea_brute(list(heights))
        ok = a == b == c == d == expected
        all_ok &= ok
        print(f"  {str(heights):<32} {a:>9} {b:>9} {c:>9} {d:>7}  {'PASS' if ok else 'FAIL'}")

    print("\n--- the input must NOT be mutated (the sentinel is virtual) ---")
    hs = [2, 1, 5, 6, 2, 3]
    sol.largestRectangleArea(hs)
    untouched = hs == [2, 1, 5, 6, 2, 3]
    all_ok &= untouched
    print(f"  heights still {hs} -> {untouched}")

    # ----------------------------------------------------------------------
    # The nearest-smaller boundaries, printed per bar.
    # ----------------------------------------------------------------------
    print("\n--- the reduction: for each bar, the widest span where it is "
          "the SHORTEST ---")
    heights = [2, 1, 5, 6, 2, 3]
    print(f"  heights = {heights}")
    print(f"  {'i':>2} {'h':>3} {'prev smaller':>13} {'next smaller':>13} "
          f"{'width':>6} {'area':>6}")
    best_by_hand = 0
    for i, (lo, hi, w) in enumerate(sol.boundaries(heights)):
        area = heights[i] * w
        best_by_hand = max(best_by_hand, area)
        lo_s = str(lo) if lo >= 0 else "none (-1)"
        hi_s = str(hi) if hi < len(heights) else f"none ({hi})"
        print(f"  {i:>2} {heights[i]:>3} {lo_s:>13} {hi_s:>13} {w:>6} {area:>6}")
    print(f"  max over all bars = {best_by_hand}  (the stack computes exactly this "
          f"in ONE pass)")
    all_ok &= (best_by_hand == 10)

    # ----------------------------------------------------------------------
    # Step-by-step trace.
    # ----------------------------------------------------------------------
    print("\n--- trace: heights = [2,1,5,6,2,3]  (index 6 = zero sentinel) ---")
    n = len(heights)
    stack: List[int] = []
    best = 0
    print(f"  {'i':>2} {'h':>3}  {'stack before':<14} {'pops (h x w = area)':<34} "
          f"{'stack after':<14} best")
    for i in range(n + 1):
        h = heights[i] if i < n else 0
        before = str(stack)
        notes = []
        while stack and heights[stack[-1]] >= h:
            j = stack.pop()
            width = i if not stack else i - stack[-1] - 1
            area = heights[j] * width
            best = max(best, area)
            notes.append(f"{heights[j]}x{width}={area}")
        stack.append(i)
        label = f"{i:>2} {h if i < n else 0:>3}" + ("*" if i == n else " ")
        print(f"  {label} {before:<14} {(', '.join(notes) or '-'):<34} "
              f"{str(stack):<14} {best}")
    print(f"  (* = the sentinel step)   answer = {best}")

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 1: omit the sentinel / mis-write the width formula.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ omitting the SENTINEL, and mis-writing the WIDTH formula ---")
    print("  no sentinel: bars left on the stack are never resolved")
    print("  bad width:   `i - j - 1` (popped index) instead of `i - stack[-1] - 1`")
    print(f"  {'heights':<32} {'CORRECT':>8} {'no sentinel':>12} {'bad width':>10}   verdict")
    sentinel_demo_ok = width_demo_ok = False
    for heights_d, expected in CASES:
        good = sol.largestRectangleArea(list(heights_d))
        nos = sol.largestRectangleArea_no_sentinel(list(heights_d))
        badw = sol.largestRectangleArea_bad_width(list(heights_d))
        marks = []
        if nos != good:
            marks.append("sentinel-free UNDERCOUNTS")
            sentinel_demo_ok = True
        if badw != good:
            marks.append("bad width WRONG")
            width_demo_ok = True
        print(f"  {str(heights_d):<32} {good:>8} {nos:>12} {badw:>10}   "
              f"{' + '.join(marks) if marks else 'both happen to agree'}")

    random.seed(11)
    trials = nos_wrong = badw_wrong = 0
    for _ in range(3000):
        k = random.randint(1, 14)
        hs = [random.randint(0, 9) for _ in range(k)]
        want = sol.largestRectangleArea_brute(hs)
        trials += 1
        nos_wrong += sol.largestRectangleArea_no_sentinel(hs) != want
        badw_wrong += sol.largestRectangleArea_bad_width(hs) != want
    print(f"  randomised over {trials} histograms: sentinel-free is wrong on "
          f"{nos_wrong},")
    print(f"  the bad width formula on {badw_wrong}.")
    print("  Sentinel-free fails whenever the winning bar has NO shorter bar to")
    print("  its right — it returns 0 for every strictly increasing histogram,")
    print("  because nothing is ever popped inside the loop.")
    all_ok &= (sentinel_demo_ok and width_demo_ok)

    # ----------------------------------------------------------------------
    # Randomised cross-check of the correct variants vs the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(84)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        k = random.randint(1, 16)
        hs = [random.randint(0, 9) for _ in range(k)]     # ties are common
        want = sol.largestRectangleArea_brute(hs)
        if (sol.largestRectangleArea(hs) != want
                or sol.largestRectangleArea_strict(hs) != want
                or sol.largestRectangleArea_two_pass(hs) != want):
            mismatches += 1
    print(f"  {trials} random histograms (len 1-16, heights 0-9): {mismatches} mismatches")
    print("  -> `>=` and `>` in the pop condition agree on all of them; so does")
    print("     the explicit two-pass previous-smaller/next-smaller version.")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 2: LC 85 Maximal Rectangle IS this function per row.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ same family, proven: LC 85 solved by calling THIS function "
          "once per row ---")
    matrix = [
        ["1", "0", "1", "0", "0"],
        ["1", "0", "1", "1", "1"],
        ["1", "1", "1", "1", "1"],
        ["1", "0", "0", "1", "0"],
    ]
    cols = len(matrix[0])
    running = [0] * cols
    print(f"  {'row':<26} {'histogram of 1s above':<26} {'largestRectangleArea':>20}")
    lc85 = 0
    for row in matrix:
        for c, cell in enumerate(row):
            running[c] = running[c] + 1 if cell == "1" else 0
        area = sol.largestRectangleArea(running)
        lc85 = max(lc85, area)
        print(f"  {''.join(row):<26} {str(running):<26} {area:>20}")
    ok85 = lc85 == 6 and sol.maximalRectangle(matrix) == 6
    all_ok &= ok85
    print(f"  max over rows = {lc85}  (LC 85's expected answer is 6) -> {ok85}")
    print("  Nothing new was written: the running per-column count of")
    print("  consecutive 1s IS a histogram, and the largest all-1s rectangle")
    print("  ending at a row IS that histogram's largest rectangle.")

    # ----------------------------------------------------------------------
    # ⚠️ RUNTIME DEMO 3: O(n) stack vs O(n^2) brute force.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️ O(n) monotonic stack vs O(n^2) brute force: measured ---")
    print("  (increasing histogram: worst case for stack SPACE — nothing pops")
    print("   until the sentinel — and worst case for the brute force too)")
    print(f"  {'n':>6} {'one-pass':>11} {'two-pass':>11} {'brute O(n^2)':>14} {'speedup':>8}")
    random.seed(7)
    for k in (400, 800, 1600, 3200):
        hs = sorted(random.randint(1, 10 ** 4) for _ in range(k))
        t0 = time.perf_counter(); a = sol.largestRectangleArea(hs)
        t1 = time.perf_counter(); b = sol.largestRectangleArea_two_pass(hs)
        t2 = time.perf_counter(); c = sol.largestRectangleArea_brute(hs)
        t3 = time.perf_counter()
        ok = a == b == c
        all_ok &= ok
        one_ms = (t1 - t0) * 1000
        print(f"  {k:>6} {one_ms:>9.2f}ms {(t2 - t1) * 1000:>9.2f}ms "
              f"{(t3 - t2) * 1000:>12.2f}ms {(t3 - t2) / (t1 - t0):>7.0f}x"
              f"  {'agree' if ok else 'MISMATCH'}")
    print("  The brute-force column quadruples when n doubles; the stack columns")
    print("  double. At the real constraint n = 10^5 the brute force is ~10^10")
    print("  operations — the wall this problem exists to test.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
