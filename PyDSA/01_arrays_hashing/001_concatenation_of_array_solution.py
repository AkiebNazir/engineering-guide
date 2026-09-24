"""
================================================================================
SOLUTION · LeetCode 1929 · Concatenation of Array                        [Easy]
https://leetcode.com/problems/concatenation-of-array/
================================================================================

THE CORE IDEA
-------------
The output length is known before you start: exactly 2n. That means you never
have to grow the array by guessing — preallocate and fill.

The only real insight is the index mapping:

    output index  ->  source index
    ------------      -------------
    i        (i < n)   nums[i]
    i + n              nums[i]

which is the same as saying: for output index j in [0, 2n),
`ans[j] = nums[j % n]`. The modulo view is worth noticing because it generalises
to "repeat k times" and to circular-array problems later in this curriculum.


================================================================================
APPROACH 1 · Two explicit loops (the most literal reading)
================================================================================
Walk nums once writing the first half, then walk it again writing the second.

    ans = []
    for x in nums: ans.append(x)
    for x in nums: ans.append(x)

Correct, O(n), and completely clear. Nothing wrong with it. But we can do
better on allocation behaviour.


================================================================================
APPROACH 2 · One loop, preallocated (the version to write in an interview)
================================================================================
Allocate 2n slots up front, then a single pass writes both copies.

STEP BY STEP for nums = [1, 2, 1], n = 3:

    ans = [0, 0, 0, 0, 0, 0]        preallocated, 2n = 6 slots

    i = 0:  ans[0]     = nums[0] = 1   ->  [1, 0, 0, 0, 0, 0]
            ans[0 + 3] = nums[0] = 1   ->  [1, 0, 0, 1, 0, 0]

    i = 1:  ans[1]     = nums[1] = 2   ->  [1, 2, 0, 1, 0, 0]
            ans[1 + 3] = nums[1] = 2   ->  [1, 2, 0, 1, 2, 0]

    i = 2:  ans[2]     = nums[2] = 1   ->  [1, 2, 1, 1, 2, 0]
            ans[2 + 3] = nums[2] = 1   ->  [1, 2, 1, 1, 2, 1]

    return [1, 2, 1, 1, 2, 1]   ✓

Why preallocating matters: `[0] * (2 * n)` is a single allocation. Repeated
`append` starts at capacity 0 and reallocates roughly log_1.125(2n) times,
copying as it goes. Both are O(n) overall, but the preallocated version does
one allocation instead of ~20 and is measurably faster. Interviewers notice
when you preallocate a known-size output.


================================================================================
APPROACH 3 · Pythonic one-liner
================================================================================
    return nums * 2        # or:  return nums + nums

`list.__mul__` allocates the exact final size and memcpy's the pointer block
twice. It is the fastest option in CPython because the copying happens in C.

⚠️ Know the shallow-copy caveat: `nums * 2` copies POINTERS, not objects. For a
list of ints that is irrelevant (ints are immutable). For a list of lists,
`inner * 2` would give you two references to the SAME inner list — a classic
bug source, e.g. `grid = [[0] * cols] * rows` creates `rows` references to one
row. Use `[[0] * cols for _ in range(rows)]` instead.


================================================================================
COMPLEXITY
================================================================================
    All three approaches:
      Time:  O(n)   — every element is written a constant number of times
      Space: O(n)   — the output array (required by the problem)

    "Extra" space beyond the output: O(1). If an interviewer asks for O(1)
    space, they mean beyond the output, and all three already satisfy that.


================================================================================
EDGE CASES
================================================================================
    n = 1           -> [x, x].            Handled: loop runs once.
    All identical   -> [7,7] -> [7,7,7,7]. Nothing special.
    Empty input     -> Constraints say n >= 1, so it cannot happen. But
                       `[] * 2 == []`, so the code is correct anyway.


================================================================================
COMMON MISTAKES
================================================================================
1. `ans = nums` then `ans.extend(nums)` — this MUTATES the caller's list,
   because `ans` and `nums` are the same object. Always build a new list.

2. Using `ans.append()` inside a loop that also indexes `ans[i + n]` — you
   cannot index a slot that does not exist yet. Pick one strategy: preallocate
   and index, OR append only.

3. Writing `for i in range(2 * n): ans.append(nums[i])` — IndexError once
   i >= n. You need `nums[i % n]`.


================================================================================
RELATED PROBLEMS (the "+n offset" / doubled-array idea)
================================================================================
    LC 503  Next Greater Element II   — iterate 2n and use i % n for a circle
    LC 189  Rotate Array              — index arithmetic with an offset
    LC 213  House Robber II           — circular constraint handled by splitting
================================================================================
"""

from typing import List


class Solution:
    def getConcatenation(self, nums: List[int]) -> List[int]:
        """One pass, preallocated. Time O(n), space O(n) for the output."""
        n = len(nums)
        ans = [0] * (2 * n)          # single allocation, exact final size
        for i in range(n):
            ans[i] = nums[i]         # first copy
            ans[i + n] = nums[i]     # second copy, shifted by n
        return ans

    # ------------------------------------------------------------------
    # Alternative implementations, for comparison.
    # ------------------------------------------------------------------
    def getConcatenation_two_loops(self, nums: List[int]) -> List[int]:
        """The most literal reading. Same complexity, more reallocations."""
        ans: List[int] = []
        for x in nums:
            ans.append(x)
        for x in nums:
            ans.append(x)
        return ans

    def getConcatenation_modulo(self, nums: List[int]) -> List[int]:
        """Generalises to 'repeat k times' — the circular-array view."""
        n = len(nums)
        return [nums[j % n] for j in range(2 * n)]

    def getConcatenation_pythonic(self, nums: List[int]) -> List[int]:
        """Fastest in CPython: the copy loop runs in C."""
        return nums * 2


# ==============================================================================
# TESTS — run:  python 001_concatenation_of_array_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    impls = [
        ("preallocated ", sol.getConcatenation),
        ("two loops    ", sol.getConcatenation_two_loops),
        ("modulo       ", sol.getConcatenation_modulo),
        ("pythonic     ", sol.getConcatenation_pythonic),
    ]
    cases = [
        ([1, 2, 1], [1, 2, 1, 1, 2, 1]),
        ([1, 3, 2, 1], [1, 3, 2, 1, 1, 3, 2, 1]),
        ([1], [1, 1]),
        ([7, 7], [7, 7, 7, 7]),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(nums)) == expected for nums, expected in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # Confirm the input is never mutated — a real bug in a common wrong answer.
    original = [1, 2, 3]
    sol.getConcatenation(original)
    mutation_ok = original == [1, 2, 3]
    all_ok &= mutation_ok
    print(f"{'PASS' if mutation_ok else 'FAIL'}  input not mutated")
    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
