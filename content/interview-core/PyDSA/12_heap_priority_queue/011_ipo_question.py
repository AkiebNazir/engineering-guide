"""
================================================================================
LeetCode 502 · IPO                                                        [Hard]
https://leetcode.com/problems/ipo/
Topic: 12 · Heap / Priority Queue
================================================================================

PROBLEM
-------
A company is about to IPO. Before that, it wants to finish at most k distinct
projects to maximize its capital.

You are given n projects. The i-th project has a pure profit profits[i] and
needs a minimum capital of capital[i] to start. You start with capital w.
When you finish a project, its profit is added to your capital (the capital
requirement is not spent — it's a threshold, not a cost).

Pick at most k distinct projects to maximize your final capital, and return
that final capital.


EXAMPLES
--------
Example 1:
    Input:  k = 2, w = 0, profits = [1, 2, 3], capital = [0, 1, 1]
    Output: 4
    Explanation: With w = 0 only project 0 is affordable -> w = 1.
                 Now projects 1 and 2 are affordable; take project 2 (profit 3)
                 -> w = 4.

Example 2:
    Input:  k = 3, w = 0, profits = [1, 2, 3], capital = [0, 1, 2]
    Output: 6


CONSTRAINTS
-----------
    1 <= k <= 10^5
    0 <= w <= 10^9
    n == profits.length == capital.length
    1 <= n <= 10^5
    0 <= profits[i] <= 10^4
    0 <= capital[i] <= 10^9


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Capital only ever GROWS (profits are non-negative, and the threshold isn't
spent). So the set of affordable projects only ever grows too.

With that, the greedy is natural: at every step, among the projects you can
currently afford, take the one with the biggest profit. Taking a smaller
profit now can never unlock something the bigger profit wouldn't also unlock
(more capital unlocks a superset).

The data-structure problem: "affordable set grows over time, repeatedly
extract the max profit". That's a max-heap fed by a sorted list of thresholds.


WHAT TO THINK ABOUT
--------------------
1. If you sort projects by capital requirement, how do you add newly
   affordable projects to the candidate pool without rescanning?

2. heapq is a MIN-heap. How do you get the max profit?

3. What if no project is affordable before you've done k rounds?


PROGRESSIVE HINTS
------------------
Hint 1: Sort (capital, profit) pairs by capital. Pointer i into that list.

Hint 2: Each round: while i < n and sorted[i].capital <= w, push -profit and
        advance i.

Hint 3: If the heap is empty, stop. Otherwise pop the max profit into w.


COMPLEXITY TARGET
------------------
    Time:  O(n log n + k log n)
    Space: O(n)
================================================================================
"""

from typing import List


class Solution:
    def findMaximizedCapital(self, k: int, w: int, profits: List[int], capital: List[int]) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 011_ipo_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        (2, 0, [1, 2, 3], [0, 1, 1], 4),
        (3, 0, [1, 2, 3], [0, 1, 2], 6),
        (1, 0, [1, 2, 3], [1, 1, 2], 0),
        (10, 0, [1, 2, 3], [0, 1, 2], 6),
        (1, 2, [1, 2, 3], [1, 1, 2], 5),
        (2, 1, [5, 1, 1], [5, 0, 0], 3),
    ]
    all_ok = True
    for k, w, profits, capital, want in cases:
        got = Solution().findMaximizedCapital(k, w, list(profits), list(capital))
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  k={k} w={w} profits={profits} capital={capital}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
