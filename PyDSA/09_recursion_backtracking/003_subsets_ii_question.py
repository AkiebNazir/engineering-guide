"""
================================================================================
LeetCode 90 · Subsets II                                               [Medium]
https://leetcode.com/problems/subsets-ii/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given an integer array `nums` that MAY contain duplicates, return all possible
subsets (the power set). The solution set must NOT contain duplicate subsets.
Return the solution in any order.

EXAMPLES
--------
Example 1:
    Input:  nums = [1,2,2]
    Output: [[],[1],[1,2],[1,2,2],[2],[2,2]]

Example 2:
    Input:  nums = [0]
    Output: [[],[0]]

CONSTRAINTS
-----------
    1 <= nums.length <= 10
    -10 <= nums[i] <= 10

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
Same shape as problem 002 (subsets, extend-by-index), but the input can now
repeat values, e.g. [1, 2, 2]. Generating subsets the plain way and deduping
the RESULT SET afterward (e.g. via a `set` of tuples) works, but it is
wasteful: it still builds the entire oversized tree, INCLUDING every duplicate
branch, before throwing the duplicates away at the end.

The fix — sort first, then at each tree depth skip a choice if it repeats the
PREVIOUS SIBLING already tried at that same node — prunes duplicate branches
at generation time. See topic guide Part 3 for the full argument and a worked
example on [1, 1, 2]. The short version:

    nums.sort()
    def backtrack(start, path):
        results.append(path[:])
        for i in range(start, len(nums)):
            if i > start and nums[i] == nums[i - 1]:   # skip duplicate SIBLING
                continue
            path.append(nums[i]); backtrack(i + 1, path); path.pop()

`i > start` (not `i > 0`) is the guard: it means "this is not the FIRST choice
tried at this node." The first occurrence of a value at any depth is always
explored; only repeated occurrences AS A SIBLING CHOICE are skipped.

WHAT TO THINK ABOUT
--------------------
1. Why must the array be sorted first? What would go wrong with the skip rule
   on an unsorted [2, 1, 2]?
2. Why `i > start` and not `i > 0`? Trace what `i > 0` would incorrectly skip.
3. Does the skip rule forbid using two 2's in the SAME subset (e.g. [1,2,2])?
   Why or why not?
4. Naive approach: generate everything (as if all elements were distinct),
   then deduplicate the final list with a `set` of `tuple(subset)`. How much
   MORE work does this do on an input like [1,1,1,1,1,1,1,1,1,1] compared to
   the sort+skip approach? Estimate before you measure.

PROGRESSIVE HINTS
------------------
Hint 1: Sort `nums` first. Duplicate values become ADJACENT, which is what
        makes "compare to the previous sibling" a correct dedupe test.
Hint 2: At each level of the `for` loop (not across levels), skip `nums[i]` if
        it equals `nums[i-1]` AND `i` is not the first index tried at this
        node (i.e. `i > start`).
Hint 3: The guard is NOT "skip if this value appeared anywhere before in path"
        — that would incorrectly forbid legitimate subsets like [1,1,2] that
        use the same value at different depths.
Hint 4: Compare against generate-all + `set(tuple(...))` dedupe on a
        heavily-duplicated input; count how many (wasted) branches each
        approach actually visits.

COMPLEXITY TARGET
------------------
    Time:  up to O(n * 2^n) worst case (all distinct), fewer nodes visited
           when duplicates let the sort+skip rule prune branches
    Space: O(n) auxiliary (path + recursion depth), O(output size) for results
================================================================================
"""

from typing import List


class Solution:
    def subsetsWithDup(self, nums: List[int]) -> List[List[int]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 003_subsets_ii_question.py
# ==============================================================================
def _normalize(subsets_list):
    return sorted(sorted(s) for s in subsets_list)


def run_tests() -> None:
    sol = Solution()
    cases = [
        ([1, 2, 2], [[], [1], [1, 2], [1, 2, 2], [2], [2, 2]]),
        ([0], [[], [0]]),
        ([1, 1, 1], [[], [1], [1, 1], [1, 1, 1]]),
        ([4, 4, 4, 1, 4], None),   # checked via distinctness + size below
        ([1, 2, 3], [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]),
    ]
    passed = 0
    for nums, expected in cases:
        got = sol.subsetsWithDup(nums)
        if expected is not None:
            ok = _normalize(got) == _normalize(expected)
        else:
            norm = _normalize(got)
            ok = len(norm) == len(set(map(tuple, norm)))
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  subsetsWithDup({nums}) -> "
              f"{len(got) if got else 0} subsets")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
