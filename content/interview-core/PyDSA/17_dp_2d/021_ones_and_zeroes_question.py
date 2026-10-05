"""
================================================================================
LeetCode 474 · Ones and Zeroes                                          [Medium]
https://leetcode.com/problems/ones-and-zeroes/
Topic: 17 · Dynamic Programming (2D)
================================================================================

PROBLEM
-------
You are given an array of binary strings strs and two integers m and n.

Return the size of the largest subset of strs such that there are AT MOST m
'0's and AT MOST n '1's in the subset, counting all its strings together.


EXAMPLES
--------
Example 1:   strs = ["10", "0001", "111001", "1", "0"], m = 5, n = 3   ->  4
    {"10", "0001", "1", "0"} uses 5 zeros and 3 ones.

Example 2:   strs = ["10", "0", "1"], m = 1, n = 1   ->  2
    {"0", "1"}.


CONSTRAINTS
-----------
    1 <= strs.length <= 600
    1 <= strs[i].length <= 100
    strs[i] consists only of '0' and '1'.
    1 <= m, n <= 100


================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Each string is an ITEM that costs (zeros, ones) and is worth 1. You have two
budgets, m zeros and n ones, and each item can be taken at most once.

That is the 0/1 KNAPSACK with TWO capacities instead of one:

    dp[i][j] = the most strings you can take using at most i zeros and j ones

Taking a string with z zeros and o ones:

    dp[i][j] = max(dp[i][j], dp[i - z][j - o] + 1)

It is the same move as Partition Equal Subset Sum (16_dp_1d/014) and Coin
Change II (007), with one more dimension of capacity.


WHAT TO THINK ABOUT
--------------------
1. Why does "take the shortest strings first" fail? Try
   strs = ["11", "001", "01"], m = 3, n = 2.

2. Each string may be used once. In which direction must the capacity loops
   run so a string can't be counted twice in the same pass?

3. The table is (m+1) x (n+1). Do you need a third dimension for the items?


PROGRESSIVE HINTS
------------------
Hint 1: Count zeros and ones per string first.

Hint 2: For each string, loop i from m DOWN to z and j from n DOWN to o.

Hint 3: dp starts as all zeros; the answer is dp[m][n].


COMPLEXITY TARGET
------------------
    Time:  O(L * m * n) for L strings (plus the counting)
    Space: O(m * n)
================================================================================
"""
from typing import List


class Solution:
    def findMaxForm(self, strs: List[str], m: int, n: int) -> int:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 021_ones_and_zeroes_question.py
# ==============================================================================
def run_tests() -> None:
    cases = [
        (["10", "0001", "111001", "1", "0"], 5, 3, 4),
        (["10", "0", "1"], 1, 1, 2),
        (["11", "001", "01"], 3, 2, 2),
        (["0"], 3, 0, 1),
        (["111", "1000", "1000", "1000"], 9, 3, 3),
        (["00", "000"], 1, 10, 0),
    ]
    all_ok = True
    for strs, m, n, want in cases:
        got = Solution().findMaxForm(list(strs), m, n)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  strs={strs} m={m} n={n}  got={got}  want={want}")
    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
