"""
================================================================================
LeetCode 39 · Combination Sum                                            [Medium]
https://leetcode.com/problems/combination-sum/
Topic: 09 · Recursion / Backtracking
================================================================================
PROBLEM
-------
Given an array of DISTINCT integers `candidates` and a target integer `target`,
return a list of all UNIQUE combinations of `candidates` where the chosen
numbers sum to `target`. You may return the combinations in any order.

The SAME number may be chosen from `candidates` an UNLIMITED number of times.
Two combinations are unique if the frequency of at least one of the chosen
numbers is different.

The test cases are generated such that the number of unique combinations that
sum up to `target` is less than 150 combinations for the given input.

EXAMPLES
--------
Example 1:
    Input:  candidates = [2,3,6,7], target = 7
    Output: [[2,2,3],[7]]
    Explanation:
        2 + 2 + 3 = 7. Note 2 is used twice — that is allowed.
        7 = 7.
        These are the only two combinations.

Example 2:
    Input:  candidates = [2,3,5], target = 8
    Output: [[2,2,2,2],[2,3,3],[3,5]]

Example 3:
    Input:  candidates = [2], target = 1
    Output: []
    Explanation: No combination of 2s sums to 1.

CONSTRAINTS
-----------
    1 <= candidates.length <= 30
    2 <= candidates[i] <= 40
    All elements of `candidates` are DISTINCT.
    1 <= target <= 40

    Read those constraints carefully. `candidates[i] >= 2` is doing real work:
    it guarantees the recursion terminates. If 0 or a negative number were
    allowed, "reuse an element unlimited times" would mean infinite recursion.

================================================================================
UNDERSTANDING THE PROBLEM
================================================================================
You have just written Combinations (LC 77), where the rule was
`backtrack(i + 1)` — "only pick things strictly after me".

This problem changes ONE character. Here an element may be reused, so the
recursive call becomes `backtrack(i)` — "you may pick me again".

That single change is the entire difference between:

    backtrack(i + 1)  -> each element at most once   (LC 77, LC 40, LC 90)
    backtrack(i)      -> each element unlimited      (LC 39, THIS ONE)
    backtrack(0)      -> WRONG: generates every ORDERING of every answer

Understand why the third one is wrong before you write any code. If you restart
the loop at 0 on every call, you will produce [2,2,3], [2,3,2] and [3,2,2] as
three separate answers. They are the same combination. The `start` index is
what makes each multiset reachable by exactly one path.

Also note what is NOT here: no `used[]` array (elements are reusable, so
"used" is meaningless), and no dedupe pass at the end (the structure prevents
duplicates, it does not clean them up afterwards).

WHAT TO THINK ABOUT
--------------------
1. What is the state? The running `path` plus how much target is left.
   Prefer passing `remaining` down rather than re-summing `path` every call —
   re-summing turns an O(1) check into O(k) and is a real, avoidable cost.

2. What are the base cases? There are two, and both matter:
       remaining == 0  -> found one, record a COPY of path, return
       remaining <  0  -> overshot, this branch is dead, return
   You can instead check before recursing, which prunes one level earlier.

3. Why does the recursion terminate? Every chosen element is >= 2, so
   `remaining` strictly decreases on every call. Maximum depth is
   target // min(candidates).

4. Can you prune? Yes, and it is the interesting part. Sort `candidates`
   first. Then inside the loop, the moment `candidates[i] > remaining`, every
   LATER candidate is also too big — so `break` out of the loop entirely
   instead of `continue`. Sorting costs O(n log n) once and converts a
   per-element test into a whole-loop exit.

5. What does the answer NOT depend on? The order of `candidates`. Sorting is
   safe. Convince yourself of that before relying on the `break`.

PROGRESSIVE HINTS
------------------
Hint 1: Start from your LC 77 template: choose / explore / unchoose, with a
        `start` parameter and `path.append` / `path.pop`.

Hint 2: The only structural change is the recursive call. In LC 77 you wrote
        `backtrack(i + 1)`. Here, because reuse is allowed, write
        `backtrack(i)`. Everything else about the skeleton stays.

Hint 3: Track `remaining = target - sum(path)` as a parameter. Record an answer
        when `remaining == 0`; abandon the branch when `remaining < 0`.

Hint 4: Sort `candidates` up front. Now in the loop, if
        `candidates[i] > remaining`, you can `break` rather than `continue`,
        because the array is ascending and nothing later can fit either.

Hint 5: Remember `results.append(path[:])`, not `results.append(path)`. This is
        the same trap as every other backtracking problem.

COMPLEXITY TARGET
------------------
    Time:  O(n^(target/min)) in the worst case — the tree has branching factor
           up to n and depth up to target/min(candidates). This is a genuinely
           exponential problem; there is no polynomial algorithm, because the
           OUTPUT itself can be exponentially large.
    Space: O(target/min) for the recursion stack and `path`, excluding output.

    Do not let the ugly bound scare you off — state it plainly in an interview,
    then point out the output-size lower bound. That is the correct analysis.
================================================================================
"""

from typing import List


class Solution:
    def combinationSum(self, candidates: List[int], target: int) -> List[List[int]]:
        # YOUR CODE HERE
        pass


# ==============================================================================
# TESTS — run:  python 007_combination_sum_question.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([2, 3, 6, 7], 7, [[2, 2, 3], [7]]),
        ([2, 3, 5], 8, [[2, 2, 2, 2], [2, 3, 3], [3, 5]]),
        ([2], 1, []),
        ([7, 3, 2], 7, [[2, 2, 3], [7]]),      # unsorted input must still work
        ([8], 8, [[8]]),
    ]
    passed = 0
    for candidates, target, expected in cases:
        got = sol.combinationSum(candidates, target)
        got_norm = sorted(sorted(c) for c in got) if got else []
        exp_norm = sorted(sorted(c) for c in expected)
        ok = got_norm == exp_norm
        passed += ok
        print(f"{'PASS' if ok else 'FAIL'}  candidates={candidates}, target={target}")
        if not ok:
            print(f"    Expected: {exp_norm}")
            print(f"    Got:      {got_norm}")
    print(f"\n{passed}/{len(cases)} passed")


if __name__ == "__main__":
    run_tests()
