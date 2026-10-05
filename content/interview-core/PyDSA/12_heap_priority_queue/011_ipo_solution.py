"""
================================================================================
SOLUTION · LeetCode 502 · IPO                                             [Hard]
https://leetcode.com/problems/ipo/
================================================================================

THE CORE IDEA
--------------
Capital never decreases, so the set of affordable projects only grows. Sort
projects by required capital and sweep a pointer forward as capital rises,
pushing newly affordable profits into a MAX-heap. Each round, take the
largest affordable profit. Two structures, one for each axis: the sorted list
answers "what just became affordable?", the heap answers "what's the best
among the affordable?".


================================================================================
APPROACH 1 · Try every order (priced, used only as an oracle)
================================================================================
DFS over sequences of up to k distinct affordable projects.

    Time: O(n^k)-ish    Space: O(k)


================================================================================
APPROACH 2 · Rescan every round
================================================================================
Each round, scan all unused projects for the max profit with capital <= w.

    Time: O(n * k) — 10^10 at the constraint limits    Space: O(n)

Same greedy as the answer, wrong data structure. The benchmark below shows
the gap.


================================================================================
APPROACH 3 · Sort by capital + max-heap of profits ✅ (the answer)
================================================================================
    projects = sorted(zip(capital, profits))
    heap, i = [], 0
    for _ in range(k):
        while i < n and projects[i][0] <= w:
            heapq.heappush(heap, -projects[i][1])     # negate: max-heap
            i += 1
        if not heap:
            break                                     # nothing affordable, ever
        w -= heapq.heappop(heap)
    return w

WHY GREEDY IS OPTIMAL. Suppose an optimal plan's first choice is project B
while a more profitable affordable project A exists. Swap A in first: after
it, capital is at least as high as after B, so every project the plan did
afterwards is still affordable, and if A appears later in the plan, B can
take its slot. The final capital doesn't decrease. Repeat for each round.

WHY `break` IS SAFE. If the heap is empty, nothing is affordable now, and
capital can't grow without a project, so nothing will ever be affordable.

    Time: O(n log n) sort + O(n log n) pushes + O(k log n) pops
    Space: O(n)


================================================================================
SHORTCUT · Everything affordable from the start
================================================================================
If max(capital) <= w, the answer is w + sum of the k largest profits:
heapq.nlargest(k, profits), O(n log k). A nice early exit, not needed for
correctness.


================================================================================
STEP BY STEP TRACE · k = 2, w = 0, profits = [1, 2, 3], capital = [0, 1, 1]
================================================================================
    sorted by capital: [(0,1), (1,2), (1,3)]

    round  w   push (capital <= w)          heap (as profits)  pop  w after
    -----  --  ---------------------------  -----------------  ---  -------
    1      0   (0,1)                        {1}                1    1
    2      1   (1,2), (1,3)                 {2, 3}             3    4

    answer: 4


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time                  Space   Mutates input?
    ------------------------------  --------------------  ------  --------------
    Try every order                 exponential           O(k)    No
    Rescan every round              O(n * k)              O(n)    No (used flags)
    Sort + max-heap ✅              O((n + k) log n)      O(n)    No


================================================================================
EDGE CASES
================================================================================
    Nothing affordable at start    Return w unchanged.
    k > n                          Stop when the heap empties.
    Zero-profit projects           Allowed; they don't raise w but still cost a
                                    round. The heap puts them last.
    Duplicate capitals              The sweep pushes all of them at once.
    Huge w (10^9)                   Everything affordable; pure top-k.


================================================================================
COMMON MISTAKES
================================================================================
1. Picking the CHEAPEST affordable project (smallest capital) to "unlock more
   later". Suboptimal. Demo below on Example 1 variants.

2. Subtracting capital[i] from w when starting a project. The requirement is a
   threshold, not a cost.

3. Pushing positive profits into heapq (a min-heap) and popping the SMALLEST.

4. Re-sorting or rescanning each round instead of advancing the pointer.

5. Looping k times without the empty-heap break and crashing on pop.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Projects COST their capital (w -= capital, w += profit)?
A: The monotonic "affordable set only grows" property breaks. The problem
   becomes a knapsack-style search; greedy is no longer provably optimal.

Q: Projects arrive online over time?
A: Keep a min-heap keyed by capital for "not yet affordable" and a max-heap by
   profit for "affordable". Move items between them as w grows.

Q: Return the chosen project indices?
A: Push (-profit, index) and record indices as you pop.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1834  Single-Threaded CPU (008)     — sort by availability + heap
    LC 630   Course Schedule III           — sort by deadline + max-heap
    LC 871   Minimum Number of Refueling Stops — sweep + max-heap of passed stations
    LC 1851  Minimum Interval to Include Each Query (010) — sweep + heap
================================================================================
"""

import heapq
import random
import time
from typing import List


class Solution:
    def findMaximizedCapital(self, k: int, w: int, profits: List[int], capital: List[int]) -> int:
        n = len(profits)
        projects = sorted(zip(capital, profits))
        heap: List[int] = []
        i = 0
        for _ in range(k):
            while i < n and projects[i][0] <= w:
                heapq.heappush(heap, -projects[i][1])
                i += 1
            if not heap:
                break
            w -= heapq.heappop(heap)
        return w


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
def ipo_brute(k: int, w: int, profits: List[int], capital: List[int]) -> int:
    n = len(profits)
    best = w

    def dfs(rounds: int, cap: int, used: int) -> None:
        nonlocal best
        best = max(best, cap)
        if rounds == 0:
            return
        for j in range(n):
            if not used >> j & 1 and capital[j] <= cap:
                dfs(rounds - 1, cap + profits[j], used | 1 << j)

    dfs(k, w, 0)
    return best


def ipo_rescan(k: int, w: int, profits: List[int], capital: List[int]) -> int:
    used = [False] * len(profits)
    for _ in range(k):
        best_j = -1
        for j in range(len(profits)):
            if not used[j] and capital[j] <= w and (best_j < 0 or profits[j] > profits[best_j]):
                best_j = j
        if best_j < 0:
            break
        used[best_j] = True
        w += profits[best_j]
    return w


def ipo_cheapest_first_bug(k: int, w: int, profits: List[int], capital: List[int]) -> int:
    """Mistake 1: among affordable projects, pick the smallest capital requirement."""
    used = [False] * len(profits)
    for _ in range(k):
        best_j = -1
        for j in range(len(profits)):
            if not used[j] and capital[j] <= w and (best_j < 0 or capital[j] < capital[best_j]):
                best_j = j
        if best_j < 0:
            break
        used[best_j] = True
        w += profits[best_j]
    return w


# ==============================================================================
# TESTS — run:  python 011_ipo_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        (2, 0, [1, 2, 3], [0, 1, 1], 4),
        (3, 0, [1, 2, 3], [0, 1, 2], 6),
        (1, 0, [1, 2, 3], [1, 1, 2], 0),
        (10, 0, [1, 2, 3], [0, 1, 2], 6),
        (1, 2, [1, 2, 3], [1, 1, 2], 5),
        (2, 1, [5, 1, 1], [5, 0, 0], 3),
    ]
    for k, w, profits, capital, want in cases:
        got = sol.findMaximizedCapital(k, w, profits, capital)
        ok = got == want == ipo_rescan(k, w, profits, capital)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k:<2} w={w} profits={profits} capital={capital}  got={got}  want={want}")

    print("\n--- greedy optimality checked against exhaustive search (400 inputs) ---")
    rng = random.Random(502)
    bad = 0
    for _ in range(400):
        n = rng.randint(1, 7)
        profits = [rng.randint(0, 6) for _ in range(n)]
        capital = [rng.randint(0, 8) for _ in range(n)]
        k, w = rng.randint(1, 4), rng.randint(0, 3)
        if sol.findMaximizedCapital(k, w, profits, capital) != ipo_brute(k, w, profits, capital):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  400 random inputs: heap greedy equals the best of all orders")

    print("\n--- mistake 1 LIVE: cheapest-first instead of most-profitable-first ---")
    args = (2, 0, [1, 2, 3], [0, 1, 1])
    wrong, right = ipo_cheapest_first_bug(*args), sol.findMaximizedCapital(*args)
    ok = wrong < right == 4
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  example 1: cheapest-first ends with {wrong}, max-profit greedy with {right}")
    print("      round 2 has projects (cap 1, profit 2) and (cap 1, profit 3); cheapest-first")
    print("      can't tell them apart and takes the first one")

    print("\n--- benchmark: rescan O(n*k) vs heap O((n+k) log n) ---")
    for n in (1_000, 2_000, 4_000):
        profits = [rng.randint(0, 10_000) for _ in range(n)]
        capital = [rng.randint(0, 10**6) for _ in range(n)]
        k, w = n // 2, 10**5
        t0 = time.perf_counter(); a = ipo_rescan(k, w, profits, capital); tr = time.perf_counter() - t0
        t0 = time.perf_counter(); b = sol.findMaximizedCapital(k, w, profits, capital); th = time.perf_counter() - t0
        all_ok &= a == b
        print(f"      n={n:>5} k={k:>5}  rescan {tr * 1000:8.1f} ms   heap {th * 1000:6.2f} ms   ratio {tr / th:6.0f}x")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
