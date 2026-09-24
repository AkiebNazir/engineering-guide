"""
================================================================================
LeetCode 47 · Permutations II                                          [Medium]
https://leetcode.com/problems/permutations-ii/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given a collection of numbers `nums` that MIGHT contain duplicates, return all
possible UNIQUE permutations, in any order.

EXAMPLES
--------
Example 1:
    Input:  nums = [1,1,2]
    Output: [[1,1,2],[1,2,1],[2,1,1]]

Example 2:
    Input:  nums = [1,2,3]
    Output: [[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]

CONSTRAINTS
-----------
    1 <= nums.length <= 8
    -10 <= nums[i] <= 10

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Same tree shape as 004 (permutations, used[] array), but with duplicate values
in the input. Without a dedupe guard, [1, 1, 2] would produce 3! = 6 raw
permutations, but only 3 are actually DISTINCT ([1,1,2], [1,2,1], [2,1,1]) —
swapping the two identical 1's produces the same sequence twice.

The fix is the same FAMILY of trick as problem 003 (Subsets II), adapted to
this tree's shape: sort first, then at each node, skip trying a value if an
IDENTICAL value was already tried as a SIBLING at this exact node AND that
earlier sibling's subtree has already been fully explored (i.e. it is
currently unused again). That second condition — "currently unused" — is new
compared to subsets/combinations, because here `start` doesn't exist; the
guard has to use the `used[]` array itself to tell "sibling already tried and
finished" apart from "ancestor currently in use further up the path."

    nums.sort()
    def backtrack():
        if len(path) == len(nums):
            results.append(path[:]); return
        for i in range(len(nums)):
            if used[i]:
                continue
            if i > 0 and nums[i] == nums[i-1] and not used[i-1]:
                continue                      # skip duplicate SIBLING
            used[i] = True; path.append(nums[i])
            backtrack()
            path.pop(); used[i] = False

WHAT TO THINK ABOUT
--------------------
1. Why does the guard check `not used[i-1]` here, when problem 003's guard
   only needed `i > start`? What role does `start` play in subsets that
   doesn't exist in permutations?
2. Concretely: for nums = [1, 1, 2], at the root, why is choosing index 0
   (the first 1) allowed, but choosing index 1 (the second 1) at the SAME
   root call skipped?
3. Is it legal to use the second 1 LATER, deeper in the tree, once the first
   1 is already placed? Why does the guard permit that but not the sibling
   case?
4. Naive alternative: generate all n! raw permutations (even with the
   used[]-only version from 004), then dedupe the result list with a set of
   tuples. How much more work does this do on [1,1,1,1,1,1,1,2]?

PROGRESSIVE HINTS
------------------
Hint 1: Sort `nums` first so identical values are adjacent.
Hint 2: The guard is `i > 0 and nums[i] == nums[i-1] and not used[i-1]` — the
        `not used[i-1]` part is what makes this specific to permutations: it
        distinguishes "the previous identical value is a SIBLING that already
        finished its subtree" (skip) from "the previous identical value is
        currently PLACED higher up the current path" (allow — this is a
        different, legal branch).
Hint 3: Trace [1, 1, 2] by hand at the root before writing any code.

COMPLEXITY TARGET
------------------
    Time:  up to O(n * n!) worst case (all distinct), fewer nodes visited
           when duplicates let the guard prune branches
    Space: O(n) auxiliary (path + used[] + recursion depth), O(output size)
================================================================================
"""

from typing import List


class Solution:
    def permuteUnique(self, nums: List[int]) -> List[List[int]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 005_permutations_ii_question.py
# ==============================================================================
def _normalize(perms):
    return sorted(tuple(p) for p in perms)


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 1, 2], [[1, 1, 2], [1, 2, 1], [2, 1, 1]]),
        ([1, 2, 3], [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]),
        ([1, 1, 1], [[1, 1, 1]]),
        ([2, 2], [[2, 2]]),
    ]
    passed = 0
    for nums, expected in cases:
        got = sol.permuteUnique(nums)
        ok = _normalize(got) == _normalize(expected)
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  permuteUnique({nums}) -> "
              f"{len(got) if got else 0} perms (want {len(expected)})")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
</content>
