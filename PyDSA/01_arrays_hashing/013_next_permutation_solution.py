"""
================================================================================
SOLUTION · LeetCode 31 · Next Permutation                               [Medium]
https://leetcode.com/problems/next-permutation/
================================================================================

THE CORE IDEA
--------------
Three steps, all from the right:

    1. PIVOT   Find the rightmost i with nums[i] < nums[i + 1]. Everything
               after i is a decreasing run, i.e. already its largest
               arrangement, so position i is the rightmost place that can grow.
    2. SWAP    Find the rightmost j with nums[j] > nums[i] (the smallest tail
               element bigger than the pivot, because the tail is decreasing)
               and swap them.
    3. REVERSE The tail is STILL decreasing after the swap. Reverse it to make
               it increasing, i.e. its smallest arrangement.

If there's no pivot, the whole array is decreasing (the last permutation);
step 3 alone reverses it to the first permutation.


================================================================================
APPROACH 1 · Generate all permutations (priced, not coded as the answer)
================================================================================
Generate every distinct permutation, sort them, find the current one, return
the next.

    Time: O(n! * n)  — n = 100 is hopeless; even n = 12 is 479 million.
    Space: O(n! * n)

Used in the tests only for tiny n, as an oracle.


================================================================================
APPROACH 2 · Pivot, swap, reverse ✅ (the answer)
================================================================================
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] <= nums[i]:
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    lo, hi = i + 1, n - 1
    while lo < hi:
        nums[lo], nums[hi] = nums[hi], nums[lo]
        lo += 1; hi -= 1

WHY THE TAIL STAYS DECREASING AFTER THE SWAP. nums[j] is the rightmost element
greater than nums[i]. Everything to j's left in the tail is >= nums[j] (tail
decreasing) and everything to its right is <= nums[i] (otherwise j would be
further right). Putting nums[i] at position j keeps the order decreasing.
That's why a reverse (O(n)) is enough and no sort (O(n log n)) is needed.

WHY `>=` AND `<=` (NOT `>` AND `<`). Duplicates. The pivot must be STRICTLY
smaller than its right neighbour, and the swap target must be STRICTLY bigger
than the pivot. Swapping equal values changes nothing, and the reverse then
produces a SMALLER permutation. Demonstrated live below.

    Time: O(n) — at most three linear passes    Space: O(1)


================================================================================
STEP BY STEP TRACE · nums = [1, 5, 8, 4, 7, 6, 5, 3, 1]
================================================================================
    index:  0  1  2  3  4  5  6  7  8
    value:  1  5  8  4  7  6  5  3  1

    1. PIVOT   scan from right: 3>=1, 5>=3, 6>=5, 7>=6, 4<7 -> i = 3 (value 4)
                        1  5  8 [4] 7  6  5  3  1
                                     └────────────┘ decreasing tail

    2. SWAP    rightmost value > 4 in the tail: 1 no, 3 no, 5 YES -> j = 6
                        1  5  8 [5] 7  6 [4] 3  1
                                     tail 7 6 4 3 1 still decreasing

    3. REVERSE tail [4..8]:
                        1  5  8  5  1  3  4  6  7

    result: [1, 5, 8, 5, 1, 3, 4, 6, 7]


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time         Space        Mutates input?
    ------------------------------  -----------  -----------  ---------------
    Generate + sort all perms       O(n! * n)    O(n! * n)    No
    Pivot, swap, reverse ✅         O(n)         O(1)         YES (required)


================================================================================
EDGE CASES
================================================================================
    n == 1                  Nothing changes. i starts at -1; reverse is a no-op.
    Fully decreasing         No pivot -> reverse everything -> smallest.
    All equal [2,2,2]        Only one distinct permutation; stays the same.
    Duplicates next to pivot [1,2,1] -> [2,1,1]. Needs the strict comparisons.
    Pivot is index 0         Works the same; tail is nums[1:].


================================================================================
COMMON MISTAKES
================================================================================
1. Swap target found with `nums[j] >= nums[i]` (or `<` in the skip loop). With
   duplicates it swaps equal values and the result goes BACKWARDS. The demo
   shows [1, 2, 1] becoming [1, 1, 2] instead of [2, 1, 1].

2. Sorting the tail instead of reversing it. Correct, but O(n log n) and it
   hides that you understood why the tail is decreasing.

3. Searching for the swap target from the LEFT of the tail. You'd pick the
   LARGEST bigger element, not the smallest, and skip permutations.

4. Forgetting the no-pivot case and indexing nums[-1] (Python happily wraps
   around to the last element, so the bug is silent).

5. Returning a new list. The problem requires in-place modification and the
   judge reads `nums`.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Previous permutation?
A: Mirror everything: pivot is the rightmost i with nums[i] > nums[i + 1];
   swap with the rightmost j with nums[j] < nums[i]; reverse the tail.

Q: The k-th permutation of 1..n directly (LC 60)?
A: Factorial number system: the first digit is index k // (n-1)! into the
   remaining sorted digits, and so on. O(n^2) with a list, O(n log n) with a
   Fenwick tree.

Q: Next greater number using the same digits (LC 556)?
A: Exactly this algorithm on the digit array, then check for 32-bit overflow.

Q: How many times can you call it before returning to the start?
A: The number of DISTINCT permutations: n! / (c1! * c2! * ...) for value
   counts c1, c2, .... The tests verify this cycle length.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 46   Permutations (09_recursion)     — generate all, backtracking
    LC 47   Permutations II                 — with duplicates
    LC 60   Permutation Sequence            — k-th directly
    LC 556  Next Greater Element III        — same algorithm on digits
================================================================================
"""

import random
from collections import Counter
from itertools import permutations
from math import factorial
from typing import List


class Solution:
    def nextPermutation(self, nums: List[int]) -> None:
        n = len(nums)
        i = n - 2
        while i >= 0 and nums[i] >= nums[i + 1]:
            i -= 1
        if i >= 0:
            j = n - 1
            while nums[j] <= nums[i]:
                j -= 1
            nums[i], nums[j] = nums[j], nums[i]
        lo, hi = i + 1, n - 1
        while lo < hi:
            nums[lo], nums[hi] = nums[hi], nums[lo]
            lo += 1
            hi -= 1


# ------------------------------------------------------------------------
# Oracle and broken version for the demos.
# ------------------------------------------------------------------------
def next_perm_oracle(nums: List[int]) -> List[int]:
    perms = sorted(set(permutations(nums)))
    idx = perms.index(tuple(nums))
    return list(perms[(idx + 1) % len(perms)])


def next_perm_non_strict_swap(nums: List[int]) -> None:
    """Mistake 1: swap target allows EQUAL values."""
    n = len(nums)
    i = n - 2
    while i >= 0 and nums[i] >= nums[i + 1]:
        i -= 1
    if i >= 0:
        j = n - 1
        while nums[j] < nums[i]:         # BUG: stops on an equal value
            j -= 1
        nums[i], nums[j] = nums[j], nums[i]
    nums[i + 1:] = reversed(nums[i + 1:])


def distinct_perm_count(nums: List[int]) -> int:
    total = factorial(len(nums))
    for c in Counter(nums).values():
        total //= factorial(c)
    return total


# ==============================================================================
# TESTS — run:  python 013_next_permutation_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: examples and edge cases ---")
    cases = [
        ([1, 2, 3], [1, 3, 2]),
        ([3, 2, 1], [1, 2, 3]),
        ([1, 1, 5], [1, 5, 1]),
        ([1], [1]),
        ([2, 1, 1], [1, 1, 2]),
        ([1, 2, 1], [2, 1, 1]),
        ([2, 2, 2], [2, 2, 2]),
        ([1, 5, 8, 4, 7, 6, 5, 3, 1], [1, 5, 8, 5, 1, 3, 4, 6, 7]),
    ]
    for nums, want in cases:
        arr = list(nums)
        sol.nextPermutation(arr)
        ok = arr == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {nums} -> {arr}  want={want}")

    print("\n--- randomized cross-check vs sorted list of all permutations ---")
    rng = random.Random(31)
    bad = 0
    for _ in range(400):
        nums = [rng.randint(0, 3) for _ in range(rng.randint(1, 6))]
        arr = list(nums)
        sol.nextPermutation(arr)
        if arr != next_perm_oracle(nums):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  400 random arrays with duplicates match the oracle")

    print("\n--- cycle length equals the number of DISTINCT permutations ---")
    for start in ([1, 2, 3, 4], [1, 1, 2, 2, 3], [0, 0, 0, 1]):
        arr = sorted(start)
        first = list(arr)
        steps = 0
        while True:
            sol.nextPermutation(arr)
            steps += 1
            if arr == first:
                break
        want = distinct_perm_count(start)
        ok = steps == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {start}: back to start after {steps} calls  (n!/prod(c!) = {want})")

    print("\n--- mistake 1 LIVE: non-strict swap target with duplicates ---")
    wrong = [1, 2, 1]
    next_perm_non_strict_swap(wrong)
    right = [1, 2, 1]
    sol.nextPermutation(right)
    ok = wrong == [1, 1, 2] and right == [2, 1, 1]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  [1,2,1]: buggy gives {wrong} (SMALLER than the input), correct gives {right}")
    print("      the bug swaps the pivot 1 with the other 1 (no change), then reversing")
    print("      the tail [2,1] -> [1,2] moves the permutation backwards")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
