"""
================================================================================
SOLUTION · LeetCode 42 · Trapping Rain Water                              [Hard]
https://leetcode.com/problems/trapping-rain-water/
================================================================================

THE CORE IDEA
--------------
Water above column i fills to the lower of the tallest wall on its left and
the tallest wall on its right:

    water[i] = min(max_left[i], max_right[i]) - height[i]

Every approach computes that formula; they differ only in how they get the
two maxima. The two-pointer version needs O(1) space thanks to one
observation: if the running `left_max` is smaller than the running
`right_max`, then column `lo` is capped by `left_max`. It doesn't matter how
tall the right side really is — we already know it's at least `right_max`,
which is enough.


================================================================================
APPROACH 1 · Brute force per column (priced, used only as an oracle)
================================================================================
For each i, scan left for the max and scan right for the max.

    Time: O(n^2)    Space: O(1)


================================================================================
APPROACH 2 · Prefix max + suffix max arrays
================================================================================
    left  = running max from the left   (left[i]  = max(height[0..i]))
    right = running max from the right  (right[i] = max(height[i..n-1]))
    answer = sum(min(left[i], right[i]) - height[i])

    Time: O(n) — three passes    Space: O(n) — two extra arrays

This is the clearest version to explain first. The two-pointer version is
this exact formula with the arrays replaced by two running numbers.


================================================================================
APPROACH 3 · Two pointers ✅ (the answer)
================================================================================
    lo, hi = 0, n - 1
    left_max = right_max = water = 0
    while lo < hi:
        left_max  = max(left_max,  height[lo])
        right_max = max(right_max, height[hi])
        if left_max <= right_max:
            water += left_max - height[lo]
            lo += 1
        else:
            water += right_max - height[hi]
            hi -= 1

WHY THIS IS CORRECT. Suppose left_max <= right_max.
  - left_max is the TRUE max_left[lo]: lo has scanned everything to its left.
  - right_max is the max of height[hi..n-1] only. The true max_right[lo] also
    includes the bars between lo and hi, so it's >= right_max >= left_max.
  - Therefore min(max_left[lo], max_right[lo]) = left_max EXACTLY, and the
    formula gives water at lo = left_max - height[lo]. We never needed the
    real max_right[lo].
The else-branch is the mirror image.

Note the final column where lo == hi is never added. That's fine: it's the
tallest bar seen (the pointers stop at the global max), and the tallest bar
holds no water.

    Time: O(n) — one pass    Space: O(1)


================================================================================
APPROACH 4 · Monotonic decreasing stack (fills horizontal layers)
================================================================================
Keep indices of bars with decreasing height. When a taller bar arrives at i,
pop the top (the "floor"). The new top is the left wall, i is the right
wall; the layer holds
    width  = i - left - 1
    depth  = min(height[left], height[i]) - height[floor]
Repeat while the current bar is taller than the stack top.

    Time: O(n) — each index pushed and popped once    Space: O(n)

Worth knowing because it's the same monotonic-stack skeleton as Largest
Rectangle in Histogram (06_stack/010), and some interviewers ask for it.


================================================================================
STEP BY STEP TRACE · two pointers, height = [4, 2, 0, 3, 2, 5]
================================================================================
    lo hi  h[lo] h[hi]  left_max right_max  branch      add   water
    -- --  ----- -----  -------- ---------  ----------  ---   -----
     0  5     4     5        4        5      left<=right  0      0   lo=1
     1  5     2     5        4        5      left<=right  2      2   lo=2
     2  5     0     5        4        5      left<=right  4      6   lo=3
     3  5     3     5        4        5      left<=right  1      7   lo=4
     4  5     2     5        4        5      left<=right  2      9   lo=5
     5  5                                   lo == hi, stop

    answer: 9
        5 |                █
        4 | █ ~  ~  ~  ~  █
        3 | █ ~  ~  █  ~  █
        2 | █ █  ~  █  █  █
        1 | █ █  ~  █  █  █
          +-----------------
            0 1  2  3  4  5


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time     Space   Mutates input?
    ---------------------------  -------  ------  --------------
    Brute force per column       O(n^2)   O(1)    No
    Prefix/suffix max arrays     O(n)     O(n)    No
    Two pointers ✅              O(n)     O(1)    No
    Monotonic stack              O(n)     O(n)    No


================================================================================
EDGE CASES
================================================================================
    n < 3                   Can't form a basin; answer 0. The loop handles it.
    Monotonic heights        Always 0 — one side never has a wall.
    Plateau walls [5,5,0,5]  Equal maxima: `<=` sends the left pointer; either
                              choice is correct.
    All zeros                0.
    Single deep basin        [5,0,0,0,5] -> 15.


================================================================================
COMMON MISTAKES
================================================================================
1. Using `max(max_left, max_right)` instead of `min`. Water spills over the
   LOWER wall. The demo shows the overcount on Example 1.

2. Forgetting to subtract height[i]. You'd count the bar itself as water.

3. Comparing height[lo] < height[hi] but then adding `left_max - height[lo]`
   without having updated left_max first. Update the running max BEFORE
   computing water, or the result can go negative.

4. Mixing this up with Container With Most Water (009). There, only two
   lines matter and the rest are ignored. Here, every column holds its own
   water.

5. In the stack version, forgetting that a popped floor with an EMPTY stack
   below it has no left wall and holds nothing.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: 2D elevation map (LC 407, Trapping Rain Water II)?
A: Column-wise reasoning breaks because water can escape in four directions.
   Use a min-heap seeded with the border cells; repeatedly pop the lowest
   boundary cell, and for each unvisited neighbor add max(0, boundary - h)
   water and push max(boundary, h). O(mn log(mn)).

Q: Heights arrive as a stream and you must report water so far?
A: Water at a column can grow later when a taller right wall appears, so you
   can't finalize columns eagerly. The monotonic stack version handles this
   naturally: it adds a layer as soon as its right wall shows up.

Q: Which version would you write in an interview?
A: Explain the min(max_left, max_right) formula, write prefix/suffix arrays
   if nervous (easy to get right), then improve to two pointers when asked
   about space.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 11   Container With Most Water (009)
    LC 407  Trapping Rain Water II          — heap + BFS
    LC 84   Largest Rectangle in Histogram  — same monotonic stack skeleton
    LC 238  Product of Array Except Self    — same prefix/suffix pass idea
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def trap(self, height: List[int]) -> int:
        lo, hi = 0, len(height) - 1
        left_max = right_max = water = 0
        while lo < hi:
            if height[lo] > left_max:
                left_max = height[lo]
            if height[hi] > right_max:
                right_max = height[hi]
            if left_max <= right_max:
                water += left_max - height[lo]
                lo += 1
            else:
                water += right_max - height[hi]
                hi -= 1
        return water


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def trap_brute(height: List[int]) -> int:
    n = len(height)
    total = 0
    for i in range(n):
        total += min(max(height[: i + 1]), max(height[i:])) - height[i]
    return total


def trap_prefix_arrays(height: List[int]) -> int:
    n = len(height)
    if n == 0:
        return 0
    left = [0] * n
    right = [0] * n
    left[0] = height[0]
    for i in range(1, n):
        left[i] = max(left[i - 1], height[i])
    right[-1] = height[-1]
    for i in range(n - 2, -1, -1):
        right[i] = max(right[i + 1], height[i])
    return sum(min(left[i], right[i]) - height[i] for i in range(n))


def trap_stack(height: List[int]) -> int:
    stack: List[int] = []   # indices, heights non-increasing
    water = 0
    for i, h in enumerate(height):
        while stack and h > height[stack[-1]]:
            floor = stack.pop()
            if not stack:
                break                    # no left wall
            left = stack[-1]
            width = i - left - 1
            depth = min(height[left], h) - height[floor]
            water += width * depth
        stack.append(i)
    return water


def trap_max_instead_of_min(height: List[int]) -> int:
    """Mistake 1: water rises to the TALLER wall. Overcounts."""
    n = len(height)
    left = [0] * n
    right = [0] * n
    left[0] = height[0]
    for i in range(1, n):
        left[i] = max(left[i - 1], height[i])
    right[-1] = height[-1]
    for i in range(n - 2, -1, -1):
        right[i] = max(right[i + 1], height[i])
    return sum(max(left[i], right[i]) - height[i] for i in range(n))   # BUG


# ==============================================================================
# TESTS — run:  python 010_trapping_rain_water_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: all four approaches on examples and edge cases ---")
    cases = [
        ([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1], 6),
        ([4, 2, 0, 3, 2, 5], 9),
        ([1], 0),
        ([3, 2, 1], 0),
        ([1, 2, 3], 0),
        ([5, 0, 5], 5),
        ([2, 0, 3, 0, 1], 3),
        ([5, 0, 0, 0, 5], 15),
        ([5, 5, 0, 5], 5),
    ]
    for height, want in cases:
        results = (sol.trap(height), trap_prefix_arrays(height), trap_stack(height), trap_brute(height))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {str(height):<40} two-ptr/prefix/stack/brute={results}  want={want}")

    print("\n--- randomized cross-check, 600 inputs ---")
    rng = random.Random(42)
    bad = 0
    for _ in range(600):
        h = [rng.randint(0, 8) for _ in range(rng.randint(1, 30))]
        r = {sol.trap(h), trap_prefix_arrays(h), trap_stack(h), trap_brute(h)}
        if len(r) != 1:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  all four approaches agree on 600 random maps")

    print("\n--- mistake 1 LIVE: max instead of min ---")
    ex = [0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1]
    wrong = trap_max_instead_of_min(ex)
    ok = wrong != 6 and sol.trap(ex) == 6
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  example 1: max-version returns {wrong}, correct is 6")
    print("      every column 'fills' to the tallest bar (3) on either side,")
    print("      as if water could stand above the lower wall without spilling")

    print("\n--- space: two pointers allocate nothing per column ---")
    import tracemalloc
    h = [rng.randint(0, 10**5) for _ in range(20_000)]
    for name, fn in (("prefix arrays", trap_prefix_arrays), ("two pointers ", sol.trap)):
        tracemalloc.start()
        fn(h)
        _, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        print(f"      {name}  peak extra memory {peak / 1024:8.1f} KiB  (n = 20,000)")

    print("\n--- benchmark at n = 20,000 (the constraint maximum) ---")
    for name, fn in (("brute O(n^2)  ", trap_brute), ("prefix arrays ", trap_prefix_arrays),
                     ("stack         ", trap_stack), ("two pointers  ", sol.trap)):
        hh = h if fn is not trap_brute else h[:2_000]
        t0 = time.perf_counter(); fn(hh); dt = time.perf_counter() - t0
        note = "  (n = 2,000 only; O(n^2) with slicing)" if fn is trap_brute else ""
        print(f"      {name} {dt * 1000:8.2f} ms{note}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
