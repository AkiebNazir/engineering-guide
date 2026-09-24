"""
================================================================================
SOLUTION · LeetCode 1 · Two Sum                                          [Easy]
https://leetcode.com/problems/two-sum/
================================================================================

THE CORE IDEA
-------------
The brute force treats this as "find a PAIR," which is n^2 possibilities. The
insight is that it is not a pair search at all:

    once you fix nums[i], the partner is FORCED:  complement = target - nums[i]

So the question at each index collapses from "which other element works?" to
"have I already seen this one specific value?" — and that is exactly what a
hash map answers in O(1).

This is the smallest possible example of the single most valuable move in
interview algorithms: TRADE SPACE FOR TIME BY REMEMBERING WHAT YOU HAVE SEEN.
Recognising it here is what lets you recognise it in LC 15 (3Sum), LC 560
(Subarray Sum Equals K), and LC 454 (4Sum II).


================================================================================
APPROACH 1 · Brute force (state it, then improve)
================================================================================
    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] + nums[j] == target:
                return [i, j]

    Time:  O(n^2)
    Space: O(1)

For n = 10^4 that is ~5 x 10^7 comparisons — it actually passes on LeetCode,
but it is the answer that ends the interview early. Say it out loud with its
complexity, note the follow-up explicitly asks for better, then improve.


================================================================================
APPROACH 2 · One-pass hash map ✅ (the answer)
================================================================================

    seen = {}                       # value -> index
    for i, n in enumerate(nums):
        complement = target - n
        if complement in seen:
            return [seen[complement], i]
        seen[n] = i

STEP BY STEP for nums = [2, 7, 11, 15], target = 9:

    seen = {}

    i=0  n=2   complement = 9-2 = 7    7 in seen? NO    seen = {2: 0}
    i=1  n=7   complement = 9-7 = 2    2 in seen? YES at 0
               -> return [0, 1]   ✓

STEP BY STEP for nums = [3, 2, 4], target = 6  (the case that catches people):

    i=0  n=3   complement = 3         3 in seen? NO    seen = {3: 0}
    i=1  n=2   complement = 4         4 in seen? NO    seen = {3: 0, 2: 1}
    i=2  n=4   complement = 2         2 in seen? YES at 1
               -> return [1, 2]   ✓

    Note it did NOT return [0, 0]. Checking BEFORE inserting is what prevents
    element 3 from pairing with itself.

STEP BY STEP for nums = [3, 3], target = 6  (the duplicate case):

    i=0  n=3   complement = 3         3 in seen? NO    seen = {3: 0}
    i=1  n=3   complement = 3         3 in seen? YES at 0
               -> return [0, 1]   ✓

    The second 3 finds the first one. Note that `seen[3] = 1` would have
    OVERWRITTEN index 0 — but we returned before that could happen. Even if a
    later duplicate did overwrite, the problem guarantees exactly one solution,
    so it cannot cost us the answer.

    Time:  O(n)   — one pass, O(1) average per lookup and insert
    Space: O(n)   — the map holds at most n entries


================================================================================
⚠️  WHY CHECK-BEFORE-INSERT IS NOT OPTIONAL
================================================================================
Flip the two lines and the algorithm breaks:

    seen[n] = i                     # WRONG ORDER
    if target - n in seen:
        return [seen[target - n], i]

    nums = [3, 2, 4], target = 6
    i=0: seen = {3: 0}; complement 3 IS in seen (it is the element itself!)
         -> returns [0, 0], using nums[0] twice. Violates the problem statement.

Checking first means the map only ever contains STRICTLY EARLIER elements, so a
hit is always a genuine second element. This ordering argument is worth stating
out loud — it shows you reasoned about correctness rather than pattern-matched.


================================================================================
APPROACH 3 · Sort + two pointers (usually the WRONG answer here)
================================================================================
    pairs = sorted((v, i) for i, v in enumerate(nums))
    lo, hi = 0, len(nums) - 1
    while lo < hi:
        s = pairs[lo][0] + pairs[hi][0]
        if s == target: return sorted([pairs[lo][1], pairs[hi][1]])
        if s < target:  lo += 1
        else:           hi -= 1

    Time:  O(n log n)
    Space: O(n) to keep original indices alongside the values

Slower than the hash map, and it needs the same O(n) space *because the problem
asks for indices*. If it asked for the VALUES, this becomes O(n log n) time and
O(1) space, and it is the right answer when the input is already sorted — which
is exactly LC 167, Two Sum II.

Knowing when this approach wins is more valuable than the approach itself:
  - Input already sorted?        -> two pointers, O(n) time, O(1) space
  - Need values, not indices?    -> two pointers viable
  - Need indices, unsorted?      -> hash map


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time         Space   Notes
    --------------------  -----------  ------  ---------------------------
    Brute force           O(n^2)       O(1)    ends the interview
    Hash map        ✅    O(n)         O(n)    the expected answer
    Sort + 2 pointers     O(n log n)   O(n)    O(1) space only if values


================================================================================
EDGE CASES
================================================================================
    [3, 3], target 6        -> [0, 1]. Duplicates: the later one finds the
                               earlier one. Works because we check first.
    [0, 4, 3, 0], target 0  -> [0, 3]. Zeroes and a zero target — no special
                               casing needed; 0 is a value like any other.
    Negatives, e.g.
    [-1,-2,-3,-4,-5], -8    -> [2, 4]. Negative complements hash fine.
    n = 2                   -> minimum input; loop runs twice.

    No solution: the problem guarantees exactly one, so the loop cannot fall
    through in valid input. Returning [] after the loop is defensive and costs
    nothing — but say that you know it is unreachable given the constraints.


================================================================================
COMMON MISTAKES
================================================================================
1. Inserting before checking — allows an element to pair with itself. See the
   warning block above. This is the single most common bug in this problem.

2. Returning VALUES instead of INDICES. Re-read the problem statement.

3. Using a list for `seen` and calling `.index()` — that is O(n) inside an O(n)
   loop, so you have rebuilt the O(n^2) brute force with extra steps.

4. Building the map in a first pass, then searching in a second, without
   guarding i != seen[complement]. Two passes can work, but only if you skip
   the self-match:
       if complement in seen and seen[complement] != i
   The one-pass version needs no such guard, which is why it is preferred.

5. Saying the complexity is "O(1) lookup" flatly. It is O(1) AVERAGE, O(n)
   worst case on pathological collisions.


================================================================================
RELATED PROBLEMS — the complement/"remember what you've seen" family
================================================================================
    LC 167  Two Sum II (sorted)   — two pointers, O(1) space
    LC 15   3Sum                  — fix one, two-pointer the rest
    LC 18   4Sum                  — fix two, two-pointer the rest
    LC 454  4Sum II               — hash the sums of two arrays
    LC 560  Subarray Sum Equals K — the same complement trick on PREFIX SUMS
    LC 1    is the seed of all of the above. Own it cold.
================================================================================
"""

from typing import Dict, List


class Solution:
    def twoSum(self, nums: List[int], target: int) -> List[int]:
        """One-pass hash map. Time O(n) average, space O(n)."""
        seen: Dict[int, int] = {}            # value -> index
        for i, n in enumerate(nums):
            complement = target - n
            if complement in seen:           # CHECK before INSERT — see notes
                return [seen[complement], i]
            seen[n] = i
        return []                            # unreachable given the constraints

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def twoSum_two_pass(self, nums: List[int], target: int) -> List[int]:
        """Build the map first, then search. Needs an explicit self-match guard."""
        seen = {n: i for i, n in enumerate(nums)}
        for i, n in enumerate(nums):
            j = seen.get(target - n)
            if j is not None and j != i:     # the guard the one-pass avoids
                return [i, j]
        return []

    def twoSum_sort_two_pointers(self, nums: List[int], target: int) -> List[int]:
        """O(n log n). Carries indices alongside values, so still O(n) space."""
        pairs = sorted((v, i) for i, v in enumerate(nums))
        lo, hi = 0, len(pairs) - 1
        while lo < hi:
            s = pairs[lo][0] + pairs[hi][0]
            if s == target:
                return sorted([pairs[lo][1], pairs[hi][1]])
            if s < target:
                lo += 1
            else:
                hi -= 1
        return []

    def twoSum_bruteforce(self, nums: List[int], target: int) -> List[int]:
        """O(n^2). Contrast only."""
        for i in range(len(nums)):
            for j in range(i + 1, len(nums)):
                if nums[i] + nums[j] == target:
                    return [i, j]
        return []


# ==============================================================================
# TESTS — run:  python 004_two_sum_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([2, 7, 11, 15], 9, [0, 1]),
        ([3, 2, 4], 6, [1, 2]),
        ([3, 3], 6, [0, 1]),
        ([-1, -2, -3, -4, -5], -8, [2, 4]),
        ([0, 4, 3, 0], 0, [0, 3]),
        ([1, 2], 3, [0, 1]),
    ]
    impls = [
        ("one-pass map ", sol.twoSum),
        ("two-pass map ", sol.twoSum_two_pass),
        ("sort + 2ptr  ", sol.twoSum_sort_two_pointers),
        ("brute force  ", sol.twoSum_bruteforce),
    ]
    all_ok = True
    for name, fn in impls:
        ok = True
        for nums, target, expected in cases:
            got = fn(list(nums), target)
            # Verify the ANSWER, not just a fixed index pair: the two indices
            # must be distinct and their values must sum to target.
            valid = (got and len(got) == 2 and got[0] != got[1]
                     and nums[got[0]] + nums[got[1]] == target)
            ok &= bool(valid)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases, verified by summing)")

    # Show exactly why check-before-insert matters.
    print("\n--- why check-before-insert is not optional ---")

    def broken(nums, target):
        seen = {}
        for i, n in enumerate(nums):
            seen[n] = i                       # WRONG: insert first
            if target - n in seen:
                return [seen[target - n], i]
        return []

    nums, target = [3, 2, 4], 6
    bad = broken(nums, target)
    good = sol.twoSum(nums, target)
    print(f"  nums={nums} target={target}")
    print(f"  insert-then-check -> {bad}  <- uses nums[0] TWICE (3+3), invalid")
    print(f"  check-then-insert -> {good}  <- nums[1]+nums[2] = 2+4 = 6 ✓")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
