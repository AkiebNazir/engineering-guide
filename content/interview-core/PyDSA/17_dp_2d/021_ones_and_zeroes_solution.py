"""
================================================================================
SOLUTION · LeetCode 474 · Ones and Zeroes                               [Medium]
https://leetcode.com/problems/ones-and-zeroes/
================================================================================

THE CORE IDEA
--------------
0/1 knapsack with two capacities. Each string is an item costing (zeros, ones)
and worth 1:

    dp[i][j] = most strings using at most i zeros and j ones

    for each string (z zeros, o ones):
        for i from m DOWN to z:
            for j from n DOWN to o:
                dp[i][j] = max(dp[i][j], dp[i - z][j - o] + 1)

Looping capacities DOWNWARD is what makes each string usable once: dp[i-z][j-o]
is read before this string could have updated it.


================================================================================
APPROACH 1 · Try every subset (priced, used as oracle)
================================================================================
2^L subsets, each checked in O(L).

    Time: O(2^L * L)    Space: O(L)


================================================================================
APPROACH 2 · Memoised recursion over (item, zeros left, ones left)
================================================================================
    @cache
    def best(k, zeros, ones):
        if k == L: return 0
        skip = best(k + 1, zeros, ones)
        z, o = cost[k]
        if z <= zeros and o <= ones:
            return max(skip, 1 + best(k + 1, zeros - z, ones - o))
        return skip

    Time: O(L * m * n)    Space: O(L * m * n) — the third dimension is the item


================================================================================
APPROACH 3 · 2D table, capacities downward ✅ (the answer)
================================================================================
The item dimension is dropped exactly as in 1D knapsack: process items one at a
time and let the table hold "best using the items seen so far".

    Time: O(L * m * n)    Space: O(m * n)


================================================================================
STEP BY STEP TRACE · strs = ["10", "0", "1"], m = 1, n = 1
================================================================================
    dp[i][j], i = zeros budget (rows), j = ones budget (cols)

    start          after "10" (1,1)    after "0" (1,0)     after "1" (0,1)
      j: 0 1          j: 0 1              j: 0 1              j: 0 1
    i=0  0 0        i=0  0 0            i=0  0 0            i=0  0 1
    i=1  0 0        i=1  0 1            i=1  1 1            i=1  1 2

    "1" at (1,1): dp[1][0] + 1 = 1 + 1 = 2   -> answer dp[1][1] = 2


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time           Space        Mutates input?
    ---------------------------  -------------  -----------  --------------
    All subsets                  O(2^L * L)     O(L)         No
    Memo (item, zeros, ones)     O(L * m * n)   O(L * m * n) No
    2D table, downward ✅        O(L * m * n)   O(m * n)     No


================================================================================
EDGE CASES
================================================================================
    A string needing more zeros than m (or ones than n) — never taken.
    Duplicate strings — distinct items; each may be taken once.
    Budgets far larger than needed — the answer is simply L.


================================================================================
COMMON MISTAKES
================================================================================
1. Looping capacities UPWARD: that's UNBOUNDED knapsack, so one string is
   counted many times. ["0"], m=3, n=0 -> 3 instead of 1. Demo.

2. Greedy shortest-first. ["11", "001", "01"], m=3, n=2: greedy takes "11",
   spends both ones, then fits nothing: 1. Taking "001" and "01" gives 2. Demo.

3. Greedy by fewest zeros (or fewest ones) fails the same way on other inputs;
   any single ordering can be beaten when two budgets interact. Demo counts
   how often on random inputs.

4. Recounting zeros and ones inside the inner loops: correct, but it
   multiplies the cost by the string length.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Maximise total length (or any weight) instead of count?
A: Replace "+ 1" with "+ weight". The structure is unchanged.

Q: Each string may be used any number of times?
A: Loop the capacities upward — the unbounded knapsack (Coin Change, 16_dp_1d/010).

Q: Which strings were chosen?
A: Keep the 3D table (or a choice flag per item and capacity) and walk back
   from (L, m, n).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 416  Partition Equal Subset Sum (16_dp_1d/014)  — 0/1 knapsack, 1 capacity
    LC 518  Coin Change II (007)                       — unbounded, counting
    LC 494  Target Sum (008)                           — knapsack on a shifted sum
    LC 879  Profitable Schemes                         — two dimensions again
================================================================================
"""

import random
import time
from functools import cache
from itertools import combinations
from typing import List


class Solution:
    def findMaxForm(self, strs: List[str], m: int, n: int) -> int:
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        for s in strs:
            z = s.count("0")
            o = len(s) - z
            if z > m or o > n:
                continue
            for i in range(m, z - 1, -1):                # downward: each string once
                row, src = dp[i], dp[i - z]
                for j in range(n, o - 1, -1):
                    cand = src[j - o] + 1
                    if cand > row[j]:
                        row[j] = cand
        return dp[m][n]


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def fits(chosen, m, n) -> bool:
    zeros = sum(s.count("0") for s in chosen)
    return zeros <= m and sum(len(s) for s in chosen) - zeros <= n


def subsets_brute(strs: List[str], m: int, n: int) -> int:
    for size in range(len(strs), 0, -1):
        if any(fits(c, m, n) for c in combinations(strs, size)):
            return size
    return 0


def form_memo(strs: List[str], m: int, n: int) -> int:
    cost = [(s.count("0"), len(s) - s.count("0")) for s in strs]

    @cache
    def best(k: int, zeros: int, ones: int) -> int:
        if k == len(cost):
            return 0
        skip = best(k + 1, zeros, ones)
        z, o = cost[k]
        if z <= zeros and o <= ones:
            return max(skip, 1 + best(k + 1, zeros - z, ones - o))
        return skip

    return best(0, m, n)


def upward_bug(strs: List[str], m: int, n: int) -> int:
    """Mistake 1: capacities upward -> each string reusable."""
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    for s in strs:
        z = s.count("0"); o = len(s) - z
        for i in range(z, m + 1):
            for j in range(o, n + 1):
                dp[i][j] = max(dp[i][j], dp[i - z][j - o] + 1)
    return dp[m][n]


def greedy(strs: List[str], m: int, n: int, key) -> int:
    """Mistakes 2 and 3: take strings in one fixed order while they fit."""
    count = 0
    for s in sorted(strs, key=key):
        z = s.count("0"); o = len(s) - z
        if z <= m and o <= n:
            m, n, count = m - z, n - o, count + 1
    return count


# ==============================================================================
# TESTS — run:  python 021_ones_and_zeroes_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: 2D table vs memoised recursion vs all subsets ---")
    cases = [(["10", "0001", "111001", "1", "0"], 5, 3, 4), (["10", "0", "1"], 1, 1, 2),
             (["11", "001", "01"], 3, 2, 2), (["0"], 3, 0, 1),
             (["111", "1000", "1000", "1000"], 9, 3, 3), (["00", "000"], 1, 10, 0)]
    for strs, m, n, want in cases:
        results = (sol.findMaxForm(strs, m, n), form_memo(strs, m, n), subsets_brute(strs, m, n))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  strs={strs!s:<34} m={m} n={n:<2} got={results}  want={want}")

    print("\n--- randomized cross-check vs all subsets (1,000 cases) ---")
    rng = random.Random(474)
    bad = 0
    for _ in range(1000):
        strs = ["".join(rng.choice("01") for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(1, 9))]
        m, n = rng.randint(0, 8), rng.randint(0, 8)
        if sol.findMaxForm(strs, m, n) != subsets_brute(strs, m, n):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1,000 random cases agree with brute force")

    print("\n--- mistakes LIVE ---")
    w1 = upward_bug(["0"], 3, 0)
    ok = w1 == 3 and sol.findMaxForm(["0"], 3, 0) == 1
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  capacities upward: ['0'], m=3 -> {w1} (string reused), want 1")
    w2 = greedy(["11", "001", "01"], 3, 2, key=len)
    ok = w2 == 1 and sol.findMaxForm(["11", "001", "01"], 3, 2) == 2
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  shortest-first greedy: ['11','001','01'] -> {w2}, want 2")
    counts = {"shortest first": len, "fewest zeros": lambda s: s.count("0"),
              "fewest ones": lambda s: s.count("1")}
    trials = [(["".join(rng.choice("01") for _ in range(rng.randint(1, 5))) for _ in range(8)],
               rng.randint(2, 8), rng.randint(2, 8)) for _ in range(1000)]
    for name, key in counts.items():
        wrong = sum(greedy(s, m, n, key) != sol.findMaxForm(s, m, n) for s, m, n in trials)
        ok = wrong > 0
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  greedy '{name}' is wrong on {wrong} of 1,000 random cases")

    print("\n--- scale: 600 strings of length 100, m = n = 100 ---")
    strs = ["".join(rng.choice("01") for _ in range(rng.randint(1, 100))) for _ in range(600)]
    t0 = time.perf_counter(); r = sol.findMaxForm(strs, 100, 100); dt = time.perf_counter() - t0
    print(f"      answer {r} in {dt * 1000:.0f} ms  (600 x 101 x 101 = {600 * 101 * 101:,} cell updates at most)")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
