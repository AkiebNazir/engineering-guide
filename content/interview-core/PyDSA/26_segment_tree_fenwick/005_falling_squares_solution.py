"""
================================================================================
SOLUTION · LeetCode 699 · Falling Squares                                 [Hard]
https://leetcode.com/problems/falling-squares/
================================================================================

THE CORE IDEA
--------------
Coordinate-compress the O(n) distinct left/right edges across all squares
to dense indices, then build a segment tree over that compressed axis
supporting: range-MAX query (what's the tallest stack under this square's
footprint right now?) and range ASSIGNMENT with lazy propagation (raise
that whole footprint to the new landing height). Max has no inverse, so a
Fenwick tree (right tool for 001/002's SUM problems) cannot do this
directly — a segment tree, which stores the aggregate value itself at each
node rather than a prefix-invertible partial sum, is the structure that
generalizes to non-invertible aggregates like max (topic guide Part 1).

The physical setup makes the UPDATE simple: `landing_height = query_max +
side_length` is, by construction, `>=` every height already present in
that exact horizontal span (each existing height there is `<= query_max <
landing_height`). So "raise this range" is always a plain, unconditional
RANGE ASSIGNMENT — no need for a general "assign only if greater" (chmax)
lazy tag, which keeps the lazy-propagation logic in this specific problem
simpler than the fully general version.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force / sorted-interval sweep, priced, CODED BELOW as a
test oracle and benchmark subject): for each new square, scan every
PREVIOUS square, and if its horizontal span overlaps the new square's span,
take the max of its already-landed height. O(n^2) time overall (n squares,
up to n prior squares each), O(n) space. This is fully correct and, at the
problem's actual constraint (`n <= 1000`), genuinely fast enough to submit
on LeetCode — it's listed as "priced, not the taught answer" here because
it doesn't scale past a few thousand squares and because the topic exists
specifically to teach the coordinate-compression + segment-tree machinery
that DOES scale.

Approach 1 (chosen) — coordinate compression + segment tree with lazy range
assignment and range-max query: O(n log n) time, O(n) space. See THE CORE
IDEA.


================================================================================
STEP BY STEP TRACE — positions = [[1,2],[2,3],[6,1]]
================================================================================
Squares occupy x-ranges: [1,3), [2,5), [6,7).

Collect all edges: {1, 3, 2, 5, 6, 7} -> sorted coords = [1, 2, 3, 5, 6, 7]
(k = 6 coordinates -> segment tree covers k-1 = 5 intervals, indices 0..4):

    interval index:   0      1      2      3      4
    covers x-range: [1,2)  [2,3)  [3,5)  [5,6)  [6,7)

Segment tree starts all-zero (no squares landed yet).

Square 1: left=1, size=2 -> occupies [1,3).
    compressed range: idx(1)=0, idx(3)=2  -> tree indices [0, 2-1] = [0, 1]
    query max over [0,1]  -> 0 (nothing landed yet)
    landing_height = 0 + 2 = 2
    assign [0,1] = 2
    running max so far = max(0, 2) = 2      -> output[0] = 2

    tree state (by interval index): [2, 2, 0, 0, 0]

Square 2: left=2, size=3 -> occupies [2,5).
    compressed range: idx(2)=1, idx(5)=3  -> tree indices [1, 3-1] = [1, 2]
    query max over [1,2]  -> max(tree[1]=2, tree[2]=0) = 2
    landing_height = 2 + 3 = 5
    assign [1,2] = 5
    running max so far = max(2, 5) = 5      -> output[1] = 5

    tree state: [2, 5, 5, 0, 0]

Square 3: left=6, size=1 -> occupies [6,7).
    compressed range: idx(6)=4, idx(7)=5  -> tree indices [4, 5-1] = [4, 4]
    query max over [4,4]  -> 0 (untouched)
    landing_height = 0 + 1 = 1
    assign [4,4] = 1
    running max so far = max(5, 1) = 5      -> output[2] = 5 (unchanged)

    tree state: [2, 5, 5, 0, 1]

RESULT = [2, 5, 5]                                       MATCHES expected


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time        Space   Mutates input?
    ------------------------------------------------------------------------
    Sorted-interval sweep [priced]        O(n^2)      O(n)    no (read-only)
    Coord. compression + segment tree ✅  O(n log n)  O(n)    no (read-only)


================================================================================
EDGE CASES
================================================================================
    n == 1                       Single square always lands on the ground;
                                  output is `[sideLength_0]`.
    All squares disjoint          No horizontal overlap between any pair —
                                  every square lands independently on the
                                  ground; each query returns 0.
    All squares fully stacked
    at the SAME left edge         e.g. same `left`, growing sizes — every
                                  query sees the full running stack height.
    Touching but not overlapping  e.g. square A occupies [1,3), square B
                                  occupies [3,5) — they share only the
                                  single point x=3, which does NOT count as
                                  overlap ("brushing the side... does not
                                  count as landing on it"); the
                                  half-open-interval convention
                                  `[left, left+size)` for BOTH the axis
                                  coverage and the coordinate compression
                                  handles this correctly automatically.
    Very large left coordinates
    (up to 10^8)                  Coordinate compression is what makes this
                                  tractable at all — a segment tree built
                                  directly over raw coordinates would need
                                  an array of size ~10^8.


================================================================================
COMMON MISTAKES
================================================================================
1. Building the segment tree over RAW x-coordinates instead of compressed
   indices — either uses far too much memory, or (if bounded to just the
   coordinates seen so far without a proper compression pass) silently
   handles new/unseen coordinates incorrectly.

2. Off-by-one converting `[left, left+size)` into a compressed INDEX range:
   the right edge's compressed index needs a `- 1` (`idx(right) - 1`)
   because the segment tree is indexed by the INTERVALS BETWEEN
   coordinates, not the coordinates themselves — forgetting the `-1`
   either includes one interval too many or queries/updates an
   out-of-bounds index.

3. Treating "touching" (`right_A == left_B`) as overlap — the half-open
   interval convention must be applied consistently everywhere (query
   range, update range, AND the brute-force oracle's overlap check) or the
   two will disagree exactly at shared boundaries.

4. Using the current square's OWN landing height as the running answer
   instead of `max(previous running max, this landing height)` — earlier
   squares can still be part of the tallest stack even after a shorter
   square lands elsewhere.

5. Implementing the lazy tag as "only overwrite if incoming value is
   greater" (a general chmax) when a plain unconditional assignment
   suffices here — not wrong, just needless extra complexity, given the
   physical guarantee that `landing_height` always dominates the queried
   range (see THE CORE IDEA).

6. Forgetting to push the lazy tag down to children BEFORE recursing
   further during either update or query — reading `tree[node]` at an
   ancestor without pushing it down first leaves descendants holding STALE
   values whenever the tree is later refined below that pending lazy tag.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
Q: Why can't a Fenwick tree (BIT) solve this?
A: Max has no inverse — a BIT's whole trick (`sumRange = prefix(r) -
   prefix(l-1)`) depends on being able to "subtract off" a range, which
   works for sum/XOR but not for max/min. A segment tree stores the
   aggregate directly per range instead of relying on an invertible
   prefix, so it generalizes to max/min/gcd/anything associative.

Q: How would this change if `sideLength` could be 0 or squares could be
   removed later?
A: Zero side length isn't in the actual constraints (`sideLength_i >= 1`),
   but if it were, it would just mean a landing height equal to the
   existing max with no growth — handled automatically by the same
   formula. Removal would need a fundamentally different structure (a
   segment tree with lazy assignment can't easily "undo" one specific
   assignment layered under later ones) — likely a persistent or
   version-tracked structure, or reprocessing from scratch.

Q: Could you avoid the segment tree entirely given n <= 1000?
A: Yes — the O(n^2) sorted-interval sweep (Approach 0) is fast enough to
   pass at this constraint and is simpler to write correctly under
   interview time pressure. The segment-tree version is what's worth
   knowing because the SAME machinery (coordinate compression + lazy
   range structure) is required the moment `n` grows past a few thousand,
   or the coordinate range is queried far more times than it's updated.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 218  The Skyline Problem      — this topic, 006, same coordinate-compression family
    LC 307  Range Sum Query - Mutable — this topic, 001, Fenwick tree for an INVERTIBLE aggregate
    Topic 19 Intervals (adjacent)     — coordinate compression is the same "only O(n)
                                        endpoints matter" idea used there
================================================================================
"""

import random
import time
from bisect import bisect_left


class _SegTreeMaxAssign:
    """Segment tree over `n` leaf intervals: range MAX query, range
    (unconditional) ASSIGNMENT update, lazy propagation. See THE CORE IDEA
    for why an unconditional assign is safe for this specific problem."""

    def __init__(self, n: int):
        self.n = n
        self.tree = [0] * (4 * n)
        self.lazy = [0] * (4 * n)

    def _push_down(self, node: int) -> None:
        if self.lazy[node]:
            for child in (2 * node + 1, 2 * node + 2):
                self.tree[child] = self.lazy[node]
                self.lazy[child] = self.lazy[node]
            self.lazy[node] = 0

    def update(self, l: int, r: int, val: int, node: int = 0, start: int = 0, end: int = None) -> None:
        if end is None:
            end = self.n - 1
        if r < start or end < l:
            return
        if l <= start and end <= r:
            self.tree[node] = val
            self.lazy[node] = val
            return
        self._push_down(node)
        mid = (start + end) // 2
        self.update(l, r, val, 2 * node + 1, start, mid)
        self.update(l, r, val, 2 * node + 2, mid + 1, end)
        self.tree[node] = max(self.tree[2 * node + 1], self.tree[2 * node + 2])

    def query(self, l: int, r: int, node: int = 0, start: int = 0, end: int = None) -> int:
        if end is None:
            end = self.n - 1
        if r < start or end < l:
            return 0
        if l <= start and end <= r:
            return self.tree[node]
        self._push_down(node)
        mid = (start + end) // 2
        return max(
            self.query(l, r, 2 * node + 1, start, mid),
            self.query(l, r, 2 * node + 2, mid + 1, end),
        )


class Solution:
    def fallingSquares(self, positions: list[list[int]]) -> list[int]:
        # Coordinate-compress every left/right edge.
        coords = sorted({x for left, size in positions for x in (left, left + size)})
        seg = _SegTreeMaxAssign(len(coords) - 1)

        result = []
        running_max = 0
        for left, size in positions:
            right = left + size
            l_idx = bisect_left(coords, left)
            r_idx = bisect_left(coords, right) - 1  # last interval INSIDE [left, right)

            base = seg.query(l_idx, r_idx)
            landing_height = base + size
            seg.update(l_idx, r_idx, landing_height)

            running_max = max(running_max, landing_height)
            result.append(running_max)

        return result


# ------------------------------------------------------------------------
# Oracle / alternative used only for the tests and benchmark below.
# ------------------------------------------------------------------------
def _brute_force_falling_squares(positions: list[list[int]]) -> list[int]:
    """Approach 0: O(n^2) sorted-interval sweep, priced above. Correctness
    oracle and benchmark subject."""
    n = len(positions)
    landed_heights = [0] * n
    result = []
    running_max = 0
    for i in range(n):
        left_i, size_i = positions[i]
        right_i = left_i + size_i
        base = 0
        for j in range(i):
            left_j, size_j = positions[j]
            right_j = left_j + size_j
            if left_i < right_j and left_j < right_i:  # half-open overlap
                base = max(base, landed_heights[j])
        landed_heights[i] = base + size_i
        running_max = max(running_max, landed_heights[i])
        result.append(running_max)
    return result


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    # ------------------------------------------------------------------
    # LeetCode's examples.
    # ------------------------------------------------------------------
    print("--- LeetCode examples ---")
    cases = [
        ([[1, 2], [2, 3], [6, 1]], [2, 5, 5]),
        ([[100, 100], [200, 100]], [100, 100]),
    ]
    for positions, expected in cases:
        got = sol.fallingSquares([p[:] for p in positions])
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  fallingSquares({positions}) -> {got} (want {expected})")

    # ------------------------------------------------------------------
    # Edge cases.
    # ------------------------------------------------------------------
    print("\n--- edge cases ---")
    ok = sol.fallingSquares([[5, 7]]) == [7]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  n=1 -> [sideLength]")

    # Touching but NOT overlapping: [1,3) then [3,5) — must NOT stack.
    ok = sol.fallingSquares([[1, 2], [3, 2]]) == [2, 2]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  touching (not overlapping) squares land independently")

    # Same left edge, fully stacking every time.
    ok = sol.fallingSquares([[0, 3], [0, 2], [0, 1]]) == [3, 5, 6]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  identical left edge -> full stacking")

    # Very large coordinates -- coordinate compression must not blow up.
    big = [[1, 1], [10**8 - 1, 1]]
    ok = sol.fallingSquares(big) == [1, 1]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  very large left coordinates (10^8) handled via compression")

    # ------------------------------------------------------------------
    # Randomized cross-check vs the O(n^2) sorted-interval oracle.
    # ------------------------------------------------------------------
    print("\n--- randomized cross-check vs brute-force oracle (60 trials, n<=25) ---")
    rng = random.Random(699)
    mismatch = 0
    for _ in range(60):
        n = rng.randint(1, 25)
        positions = [[rng.randint(1, 30), rng.randint(1, 10)] for _ in range(n)]
        fast = sol.fallingSquares([p[:] for p in positions])
        slow = _brute_force_falling_squares(positions)
        if fast != slow:
            mismatch += 1
    ok = mismatch == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {60 - mismatch}/60 random trials agree with brute force")

    # ------------------------------------------------------------------
    # BENCHMARK — O(n log n) segment tree vs O(n^2) sorted-interval sweep.
    # ------------------------------------------------------------------
    print("\n--- benchmark: coord-compressed segment tree vs O(n^2) sweep ---")
    print(f"  {'n':>8} {'segment tree (ms)':>20} {'O(n^2) sweep (ms)':>20} {'speedup':>10}")
    for n in (100, 400, 900):
        rng = random.Random(1)
        positions = [[rng.randint(1, 10_000), rng.randint(1, 100)] for _ in range(n)]

        t0 = time.perf_counter()
        sol.fallingSquares([p[:] for p in positions])
        fast_ms = (time.perf_counter() - t0) * 1000

        t0 = time.perf_counter()
        _brute_force_falling_squares(positions)
        slow_ms = (time.perf_counter() - t0) * 1000

        speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {n:>8} {fast_ms:>20.2f} {slow_ms:>20.2f} {speedup:>9.1f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
