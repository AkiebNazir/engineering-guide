"""
================================================================================
SOLUTION · LeetCode 354 · Russian Doll Envelopes                          [Hard]
https://leetcode.com/problems/russian-doll-envelopes/
================================================================================

THE CORE IDEA
--------------
Reduce 2D nesting to 1D LIS with one sort:

    sort by (width ascending, height DESCENDING)
    answer = length of the longest STRICTLY increasing subsequence of heights

Width ascending means any nesting chain reads left to right. Height descending
within equal widths means two envelopes of the same width can never both be in
a strictly increasing height sequence, so equal widths never falsely nest.
Then LIS in O(n log n) with the patience-sorting `tails` array.


================================================================================
APPROACH 1 · O(n^2) DP (priced, used as oracle and benchmark)
================================================================================
Sort by width. dp[i] = longest chain ending at envelope i:
    dp[i] = 1 + max(dp[j] for j < i if w[j] < w[i] and h[j] < h[i])

    Time: O(n^2) — 10^10 at n = 10^5.    Space: O(n)


================================================================================
APPROACH 2 · Sort trick + LIS with binary search ✅ (the answer)
================================================================================
    envelopes.sort(key=lambda e: (e[0], -e[1]))
    tails = []
    for _, h in envelopes:
        i = bisect_left(tails, h)
        if i == len(tails): tails.append(h)
        else:               tails[i] = h
    return len(tails)

WHAT `tails` MEANS. tails[L] is the smallest height that can END an increasing
subsequence of length L + 1 seen so far. It's always sorted. A new height h
either extends the longest (append) or improves some tail (replace), which can
only help future elements. tails is NOT itself a valid subsequence; only its
LENGTH is meaningful.

WHY bisect_left. Strictly increasing: an equal height must REPLACE the equal
tail, not extend past it. bisect_left returns the index of the first tail >= h.
bisect_right would allow equal heights to extend a chain.

WHY HEIGHT DESCENDING FOR EQUAL WIDTHS. Take [3,4], [3,5]. Sorted as
[3,5], [3,4]: heights 5 then 4 — not increasing, so LIS can't use both. Sorted
ascending, 4 then 5 would be counted as a nest. Demo below.

    Time: O(n log n)    Space: O(n)


================================================================================
STEP BY STEP TRACE · envelopes = [[5,4],[6,4],[6,7],[2,3]]
================================================================================
    sorted (w asc, h desc): [2,3], [5,4], [6,7], [6,4]
    heights:                  3,     4,     7,     4

    h   bisect_left(tails, h)   action          tails
    --  ---------------------   --------------  ---------
    3   0 (empty)               append          [3]
    4   1                       append          [3, 4]
    7   2                       append          [3, 4, 7]
    4   1 (tails[1] == 4)       replace 4 -> 4  [3, 4, 7]

    answer: 3   ([2,3] -> [5,4] -> [6,7])

    Note [6,4] was processed AFTER [6,7] thanks to height-descending order, so
    it couldn't extend a chain ending in the same width.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time         Space   Mutates input?
    ------------------------------  -----------  ------  ---------------------
    O(n^2) DP                       O(n^2)       O(n)    YES if sorted in place
    Sort trick + binary-search LIS ✅ O(n log n) O(n)    YES if sorted in place
                                                          (we sort a copy)


================================================================================
EDGE CASES
================================================================================
    One envelope              1.
    All identical             1 — strictness on both dimensions.
    All same width            1 — descending heights give no increasing pair.
    All same height           1 — bisect_left replaces instead of extending.
    Already a perfect chain   n.


================================================================================
COMMON MISTAKES
================================================================================
1. Sorting heights ASCENDING for equal widths. [[3,4],[3,5]] returns 2. Demo.

2. bisect_right instead of bisect_left. [[1,1],[2,1]] (equal heights, bigger
   width) returns 2. Demo.

3. Treating `tails` as the actual chain and returning it. It's not a valid
   subsequence in general.

4. O(n^2) DP at n = 10^5. Correct and times out.

5. Forgetting that rotation is NOT allowed (don't sort each pair internally).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the actual chain?
A: Keep, for each element, the index it replaced/appended at and a parent
   pointer to the element currently at tails[pos - 1]; walk back from the last.

Q: Three dimensions (boxes)?
A: Sorting only fixes one dimension; the remaining 2D dominance problem needs
   O(n^2) DP, or O(n log^2 n) with CDQ divide-and-conquer / a 2D Fenwick tree.

Q: Non-strict nesting (>=)?
A: Sort heights ASCENDING for equal widths and use bisect_right.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 300   Longest Increasing Subsequence (013)
    LC 1691  Maximum Height by Stacking Cuboids — 3D, rotation allowed, O(n^2)
    LC 673   Number of Longest Increasing Subsequence
    LC 1964  Longest Obstacle Course at Each Position — bisect_right variant
================================================================================
"""

import bisect
import random
import time
from typing import List


class Solution:
    def maxEnvelopes(self, envelopes: List[List[int]]) -> int:
        ordered = sorted(envelopes, key=lambda e: (e[0], -e[1]))
        tails: List[int] = []
        for _, h in ordered:
            i = bisect.bisect_left(tails, h)
            if i == len(tails):
                tails.append(h)
            else:
                tails[i] = h
        return len(tails)


# ------------------------------------------------------------------------
# Alternatives / broken versions for the demos.
# ------------------------------------------------------------------------
def envelopes_dp(envelopes: List[List[int]]) -> int:
    env = sorted(envelopes)
    n = len(env)
    dp = [1] * n
    for i in range(n):
        wi, hi = env[i]
        best = 0
        for j in range(i):
            if env[j][0] < wi and env[j][1] < hi and dp[j] > best:
                best = dp[j]
        dp[i] = best + 1
    return max(dp)


def envelopes_height_asc_bug(envelopes: List[List[int]]) -> int:
    """Mistake 1: equal widths sorted with heights ascending."""
    tails: List[int] = []
    for _, h in sorted(envelopes):
        i = bisect.bisect_left(tails, h)
        if i == len(tails):
            tails.append(h)
        else:
            tails[i] = h
    return len(tails)


def envelopes_bisect_right_bug(envelopes: List[List[int]]) -> int:
    """Mistake 2: bisect_right lets equal heights extend a chain."""
    tails: List[int] = []
    for _, h in sorted(envelopes, key=lambda e: (e[0], -e[1])):
        i = bisect.bisect_right(tails, h)
        if i == len(tails):
            tails.append(h)
        else:
            tails[i] = h
    return len(tails)


# ==============================================================================
# TESTS — run:  python 017_russian_doll_envelopes_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: LIS trick vs O(n^2) DP ---")
    cases = [
        ([[5, 4], [6, 4], [6, 7], [2, 3]], 3),
        ([[1, 1], [1, 1], [1, 1]], 1),
        ([[3, 4], [3, 5], [4, 6]], 2),
        ([[1, 2]], 1),
        ([[4, 5], [4, 6], [6, 7], [2, 3], [1, 1]], 4),
        ([[1, 3], [3, 5], [6, 7], [6, 8], [8, 4], [9, 5]], 3),
    ]
    for env, want in cases:
        a, b = sol.maxEnvelopes(env), envelopes_dp(env)
        ok = a == b == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  envelopes={env}  lis={a}  dp={b}  want={want}")

    print("\n--- randomized cross-check (800 inputs, many ties) ---")
    rng = random.Random(354)
    bad = 0
    for _ in range(800):
        env = [[rng.randint(1, 6), rng.randint(1, 6)] for _ in range(rng.randint(1, 15))]
        if sol.maxEnvelopes(env) != envelopes_dp(env):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  800 random inputs agree with the O(n^2) DP")

    print("\n--- mistakes LIVE ---")
    w1 = envelopes_height_asc_bug([[3, 4], [3, 5]])
    ok = w1 == 2 and sol.maxEnvelopes([[3, 4], [3, 5]]) == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  heights ascending on ties: [[3,4],[3,5]] -> {w1} (same width can't nest; want 1)")
    w2 = envelopes_bisect_right_bug([[1, 1], [2, 1]])
    ok = w2 == 2 and sol.maxEnvelopes([[1, 1], [2, 1]]) == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  bisect_right:             [[1,1],[2,1]] -> {w2} (same height can't nest; want 1)")

    print("\n--- benchmark: O(n^2) DP vs O(n log n) ---")
    for n in (1_000, 2_000, 4_000):
        env = [[rng.randint(1, 10**5), rng.randint(1, 10**5)] for _ in range(n)]
        t0 = time.perf_counter(); a = envelopes_dp(env); td = time.perf_counter() - t0
        t0 = time.perf_counter(); b = sol.maxEnvelopes(env); tl = time.perf_counter() - t0
        all_ok &= a == b
        print(f"      n={n:>5}  DP {td * 1000:8.1f} ms   LIS {tl * 1000:6.2f} ms   ratio {td / tl:6.0f}x")
    env = [[rng.randint(1, 10**5), rng.randint(1, 10**5)] for _ in range(100_000)]
    t0 = time.perf_counter(); r = sol.maxEnvelopes(env); tl = time.perf_counter() - t0
    print(f"      n=100,000 (constraint max): LIS {tl * 1000:.1f} ms, chain length {r}")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
