"""
================================================================================
LeetCode 77 · Combinations                                               [Medium]
https://leetcode.com/problems/combinations/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given two integers `n` and `k`, return all possible combinations of `k` numbers
chosen from the range `[1, n]`.

You may return the answer in any order.

EXAMPLES
--------
Example 1:
    Input:  n = 4, k = 2
    Output: [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]
    Explanation: There are 4 choose 2 = 6 combinations.

Example 2:
    Input:  n = 1, k = 1
    Output: [[1]]

CONSTRAINTS
-----------
    1 <= n <= 20
    1 <= k <= n

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
This introduces the third base shape of backtracking: COMBINATIONS.
Unlike Subsets (where you decide in/out for each element sequentially) or 
Permutations (where order matters and you track `used` elements), 
Combinations focus on fixed-size sets where order does NOT matter.

To prevent generating duplicate combinations (e.g., [1, 2] and [2, 1]),
we impose a strict index-ordering constraint: the next element chosen
MUST be strictly greater than the last element chosen.

WHAT TO THINK ABOUT
--------------------
1. What does a partial `state` look like? A list of numbers chosen so far.
2. What is the `is_leaf` condition? When `len(path) == k`.
3. What are the `choices` at a given node? Any number from `[start, n]` 
   where `start` is `last_chosen + 1`. This strict increasing order is what
   prevents [2, 1] from being generated after [1, 2].
4. Can we PRUNE the search space? Yes! If we need `k - len(path)` more elements,
   but there aren't that many left in `[start, n]`, we can stop immediately.

PROGRESSIVE HINTS
------------------
Hint 1: Write the standard choose/explore/unchoose template.
Hint 2: Your backtracking function needs a `start` parameter. In the `for` loop,
        iterate from `start` to `n + 1`.
Hint 3: In the recursive call, pass `choice + 1` as the new `start`.
Hint 4: For optimization, if `len(path) + (n - i + 1) < k`, you don't have enough
        numbers left to form a combination of size `k`. Prune it!

COMPLEXITY TARGET
------------------
    Time:  O(k * C(n, k))  — C(n, k) leaves, copying `k` elements at each leaf.
    Space: O(k)            — depth of the recursion tree and space for `path`.
================================================================================
"""

from typing import List


class Solution:
    def combine(self, n: int, k: int) -> List[List[int]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 006_combinations_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        (4, 2, [[1,2],[1,3],[1,4],[2,3],[2,4],[3,4]]),
        (1, 1, [[1]]),
        (3, 3, [[1,2,3]]),
    ]
    passed = 0
    for n, k, expected in cases:
        got = sol.combine(n, k)
        # Sort inner lists and outer list to ignore return order
        got_normalized = sorted([sorted(lst) for lst in got]) if got else []
        exp_normalized = sorted([sorted(lst) for lst in expected])
        ok = got_normalized == exp_normalized
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  n={n}, k={k}")
        if not ok:
            print(f"    Expected: {exp_normalized}")
            print(f"    Got:      {got_normalized}")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
