"""
================================================================================
SOLUTION · LeetCode 11 · Container With Most Water                      [Medium]
https://leetcode.com/problems/container-with-most-water/
================================================================================

THE CORE IDEA
--------------
Start with the widest container (both ends) and always move the pointer at
the SHORTER line inward. The shorter line caps the water level. Every
container that keeps the shorter line and moves the taller one is narrower,
and its level is still capped by that same short line, so its area can't be
bigger. The short line has therefore been fully used up and can be dropped.
Each step discards one line for good, so the whole scan is O(n).


================================================================================
APPROACH 1 · Brute force, every pair (priced, used only as an oracle)
================================================================================
    for i in range(n):
        for j in range(i + 1, n):
            best = max(best, (j - i) * min(height[i], height[j]))

    Time: O(n^2) — about 5 * 10^9 pair checks at n = 10^5.   Space: O(1)


================================================================================
APPROACH 2 · Two pointers, move the shorter side ✅ (the answer)
================================================================================
    lo, hi = 0, n - 1
    best = 0
    while lo < hi:
        best = max(best, (hi - lo) * min(height[lo], height[hi]))
        if height[lo] < height[hi]:
            lo += 1
        else:
            hi -= 1

THE PROOF, CAREFULLY. Say height[lo] <= height[hi]. Look at every container
that uses `lo` together with some hi' where lo < hi' < hi:

    width  (hi' - lo)                  <  (hi - lo)
    level  min(height[lo], height[hi']) <= height[lo] = min(height[lo], height[hi])

Both factors are no bigger than the current container's, and width is
strictly smaller. So no container that pairs `lo` with anything left of `hi`
beats the one we just measured. `lo` has no untested pair that could win, so
we drop it. The same argument with roles swapped covers moving `hi`.

Seen as an n x n grid of pairs (i, j), each move deletes a whole row or
column of that grid. That's why n - 1 moves cover all n(n-1)/2 pairs.

    Time: O(n)    Space: O(1)


================================================================================
STEP BY STEP TRACE · height = [1, 8, 6, 2, 5, 4, 8, 3, 7]
================================================================================
    lo hi  h[lo] h[hi]  width  level  area   best   move
    -- --  ----- -----  -----  -----  ----   ----   ---------------------
     0  8     1     7      8      1      8      8   h[lo] < h[hi] -> lo++
     1  8     8     7      7      7     49     49   h[lo] >= h[hi] -> hi--
     1  7     8     3      6      3     18     49   hi--
     1  6     8     8      5      8     40     49   equal -> hi--
     1  5     8     4      4      4     16     49   hi--
     1  4     8     5      3      5     15     49   hi--
     1  3     8     2      2      2      4     49   hi--
     1  2     8     6      1      6      6     49   hi--
     1  1                                            lo == hi, stop

    answer: 49   (8 area checks instead of 36 pairs)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time     Space   Mutates input?
    ---------------------------  -------  ------  --------------
    Brute force, every pair      O(n^2)   O(1)    No
    Two pointers, move shorter ✅ O(n)     O(1)    No


================================================================================
EDGE CASES
================================================================================
    n == 2                  Only one container; loop runs once.
    Zero-height lines        Area 0 containers are fine; best may stay 0.
    Equal heights at ends    Moving either pointer is safe (the proof holds
                              with <=). Pick one consistently.
    Strictly increasing      lo keeps moving; hi never moves until the end.
    Tallest line in middle   Pointers converge on it from both sides.


================================================================================
COMMON MISTAKES
================================================================================
1. Moving the TALLER pointer. Feels reasonable ("look for something even
   taller") but it throws away the wrong line. The demo below shows it
   returning a smaller area on LeetCode's own Example 1.

2. Confusing this with Trapping Rain Water. Here only the two chosen lines
   matter; lines in between are ignored. In 010, every bar holds water.

3. Using `max` for the level instead of `min`. Water spills over the SHORTER
   line.

4. Width off by one: width is `hi - lo`, not `hi - lo + 1`. The lines are
   at x = lo and x = hi.

5. Trying to "skip" more than one line when heights repeat without a proof.
   Skipping lines no taller than the one you just dropped IS safe (they can't
   do better at a smaller width), but it's an optimization, not the answer.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the two indices too?
A: Record (lo, hi) whenever `best` improves.

Q: Can you make it faster in practice?
A: After moving past a short line, keep moving while the new line is no
   taller than the one just dropped — those can't win at a narrower width.
   Still O(n) worst case, fewer area computations on typical data.

Q: What if the lines in between DID block water?
A: Then it's Trapping Rain Water (LC 42, problem 010) — a different question
   about the total water held by every bar, solved with prefix maxima or two
   pointers tracking left_max / right_max.

Q: What if heights arrive as a stream?
A: The two-pointer proof needs both ends up front. For a stream you'd need
   to keep candidates: a line only matters if no earlier line is both taller
   and to its left (a monotonic structure), which gives an O(n log n) method.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 42   Trapping Rain Water (010)   — lines in between DO matter
    LC 167  Two Sum II (006)            — same "each move deletes a row" proof
    LC 84   Largest Rectangle in Histogram (06_stack/010) — area under bars
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def maxArea(self, height: List[int]) -> int:
        lo, hi = 0, len(height) - 1
        best = 0
        while lo < hi:
            h_lo, h_hi = height[lo], height[hi]
            if h_lo < h_hi:
                area = (hi - lo) * h_lo
                lo += 1
            else:
                area = (hi - lo) * h_hi
                hi -= 1
            if area > best:
                best = area
        return best


# ------------------------------------------------------------------------
# Oracle and broken variant for the demos.
# ------------------------------------------------------------------------
def max_area_brute(height: List[int]) -> int:
    best = 0
    n = len(height)
    for i in range(n):
        for j in range(i + 1, n):
            best = max(best, (j - i) * min(height[i], height[j]))
    return best


def max_area_move_taller(height: List[int]) -> int:
    """Mistake 1: moves the TALLER pointer. Wrong."""
    lo, hi = 0, len(height) - 1
    best = 0
    while lo < hi:
        best = max(best, (hi - lo) * min(height[lo], height[hi]))
        if height[lo] > height[hi]:   # BUG: should drop the shorter line
            lo += 1
        else:
            hi -= 1
    return best


# ==============================================================================
# TESTS — run:  python 009_container_with_most_water_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        ([1, 8, 6, 2, 5, 4, 8, 3, 7], 49),
        ([1, 1], 1),
        ([4, 3, 2, 1, 4], 16),
        ([1, 2, 1], 2),
        ([0, 0], 0),
        ([2, 3, 10, 5, 7, 8, 9], 36),
    ]
    for height, want in cases:
        got = sol.maxArea(height)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  height={height}  got={got}  want={want}")

    print("\n--- randomized cross-check vs O(n^2) brute force (500 inputs) ---")
    rng = random.Random(11)
    bad = 0
    for _ in range(500):
        h = [rng.randint(0, 15) for _ in range(rng.randint(2, 25))]
        if sol.maxArea(h) != max_area_brute(h):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  500 random inputs agree with brute force")

    print("\n--- mistake 1 LIVE: moving the taller pointer ---")
    ex = [1, 8, 6, 2, 5, 4, 8, 3, 7]
    wrong, right = max_area_move_taller(ex), sol.maxArea(ex)
    ok = wrong < right == 49
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  example 1: move-taller returns {wrong}, move-shorter returns {right}")
    print("      moving hi first (height 7 >= 1) throws away the right end before")
    print("      index 1 (height 8) ever gets paired with it")

    print("\n--- benchmark: O(n^2) vs O(n) ---")
    rng = random.Random(3)
    for n in (1_000, 2_000, 4_000):
        h = [rng.randint(0, 10_000) for _ in range(n)]
        t0 = time.perf_counter(); a = max_area_brute(h); tb = time.perf_counter() - t0
        t0 = time.perf_counter(); b = sol.maxArea(h); tp = time.perf_counter() - t0
        assert a == b
        print(f"      n={n:>5}  brute {tb * 1000:8.1f} ms   two-pointer {tp * 1000:6.3f} ms   ratio {tb / tp:8.0f}x")
    print("      the gap roughly doubles with n: quadratic vs linear")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
