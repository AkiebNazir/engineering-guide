"""
================================================================================
SOLUTION · LeetCode 398 · Random Pick Index                         [Medium]
https://leetcode.com/problems/random-pick-index/
================================================================================

THE CORE IDEA
--------------
Reservoir sampling with reservoir size 1. Walk `nums` left to right. Keep a
running counter `m` of how many matches of `target` have been seen so far.
When the m-th match is found, replace the currently-held answer with this
index with probability 1/m (equivalently: draw a uniform random integer in
[1, m] and keep the new index iff it equals 1).

PROOF OF UNIFORMITY (induction on the number of matches seen)
Let there be K total matches at indices i_1 < i_2 < ... < i_K. Claim: after
processing all of them, P(answer == i_k) = 1/K for every k.

Base case, the LAST match i_K: by construction it is kept with probability
exactly 1/K (it's the K-th match seen). That's 1/K, matching the claim
directly.

Inductive step, an earlier match i_k (k < K): P(i_k is held right after it
is seen) = 1/k. For i_k to SURVIVE to the end, it must not be replaced by
any of the K-k matches seen after it. Match i_{k+1} replaces the current
holder with probability 1/(k+1), so i_k survives that step with probability
k/(k+1). Chaining survival through i_{k+1}, i_{k+2}, ..., i_K:

    P(i_k final) = (1/k) * (k/(k+1)) * ((k+1)/(k+2)) * ... * ((K-1)/K)

This is a telescoping product -- every numerator cancels the previous
denominator -- leaving exactly 1/K. So every one of the K matches ends up
held with probability exactly 1/K, regardless of position. QED.

O(n) time per pick() (must scan to find and count all matches), O(1) extra
space -- no index list is ever materialized.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (precompute a dict, price it but understand why the curriculum
skips it here): in __init__, build {value: [i for i, v in enumerate(nums)
if v == value]}. Then pick(target) is O(1): random.choice(index_dict[target]).
Costs O(n) space beyond the input, entirely valid for THIS problem's small
constraints, and honestly the pragmatic answer if this were a real system.
NOT implemented here -- see the note below -- because the point of pairing
this problem with 003 is building reservoir sampling BEFORE you need it for
a data source (a linked list, a stream) where "collect all matches into a
list first" is not always cheap or even possible.

Approach 1 (chosen) -- reservoir sampling with reservoir size 1: O(n) time
per call (must scan the full array every time to be correct against
constraints below), O(1) extra space. This is what `pick()` implements.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [1, 2, 3, 3, 3], target = 3. Matches are at indices 2, 3, 4.

    i=0: nums[0]=1, no match
    i=1: nums[1]=2, no match
    i=2: nums[2]=3, MATCH #1. count=1. keep with prob 1/1 -> always keep.
         result = 2
    i=3: nums[3]=3, MATCH #2. count=2. keep with prob 1/2.
         say the coin flip says "keep" -> result = 3
    i=4: nums[4]=3, MATCH #3. count=3. keep with prob 1/3.
         say the coin flip says "don't keep" -> result stays 3

    final: result = 3

Over many repeated pick(3) calls, index 2 is chosen with probability
1/1 * (1 - 1/2) * (1 - 1/3) = 1 * 1/2 * 2/3 = 1/3 -- matching the K=3
uniform claim proven above.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                     Time      Space    Mutates input?
    ----------------------------  --------  -------  --------------
    Precompute index dict          O(1)*    O(n)     no (*after O(n) setup)
    Reservoir sampling [chosen]    O(n)      O(1)     no


================================================================================
EDGE CASES
================================================================================
    target has exactly one match  -> count reaches 1 exactly once, that
                                     index is always kept (prob 1/1 = certain).
    target is the value at index 0 AND recurs later -> the algorithm does
                                     not special-case position, only match
                                     ORDER, so this is handled uniformly.
    all elements equal target      -> every index is a match; the proof
                                     above applies with K = len(nums).
    pick() called many times on the same Solution instance -> each call is
                                     independent; no state persists between
                                     calls (only nums itself is stored).


================================================================================
COMMON MISTAKES
================================================================================
1. Using `random.randint(0, m)` (inclusive range of size m+1) instead of
   `random.randint(1, m)` -- an off-by-one that changes the keep
   probability from 1/m to something else and breaks uniformity.
2. Resetting the match counter incorrectly across separate pick() calls --
   the counter must be LOCAL to each pick() invocation, not accumulated
   across different target values or repeated calls.
3. Assuming "just take the LAST match" or "just take the FIRST match" is
   fine because "it's still one of the valid indices" -- the problem
   requires EQUAL probability across all matches, not just validity.
4. Forgetting that pick() must return an index even for a single match
   (count-of-1 case) -- reservoir sampling with probability 1/1 handles
   this correctly by construction, but it's easy to special-case it
   incorrectly if you don't trust the general formula.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "What if pick() is called far more often than __init__?" -> then the
  O(n) dict-precompute approach amortizes better (O(1) per pick after one
  O(n) setup) -- name that trade-off explicitly.
- "What if nums were a stream you could only read once, of unknown
  length?" -> that's exactly reservoir sampling's real use case, and it's
  problem 003 (Linked List Random Node) in this same folder.
- "Extend this to picking k indices uniformly at random (not just 1)."
  -> reservoir sampling generalizes: keep a reservoir of size k, and for
  the m-th match (m > k) replace a uniformly random slot in the reservoir
  with probability k/m.


================================================================================
RELATED PROBLEMS
================================================================================
- 001 Shuffle an Array (LC 384) -- Fisher-Yates, a different uniformity proof.
- 003 Linked List Random Node (LC 382) -- reservoir sampling over a stream
  of unknown length, the direct generalization of this technique.
- Random Pick with Weight (LC 528) -- prefix sum + binary search instead.
================================================================================
"""

import random
import time
from collections import Counter


class Solution:
    def __init__(self, nums: list[int]):
        self.nums = nums

    def pick(self, target: int) -> int:
        count = 0
        result = -1
        for i, value in enumerate(self.nums):
            if value == target:
                count += 1
                # keep this index with probability 1/count
                if random.randint(1, count) == 1:
                    result = i
        return result


def run_tests() -> None:
    all_ok = True

    sol = Solution([1, 2, 3, 3, 3])

    got = sol.pick(1)
    ok = got == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  pick(1) -> {got}  (want 0, unique match)")

    valid_for_3 = {2, 3, 4}
    got = sol.pick(3)
    ok = got in valid_for_3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  pick(3) -> {got}  (want one of {valid_for_3})")

    for _ in range(50):
        got = sol.pick(3)
        if got not in valid_for_3:
            all_ok = False
            print(f"FAIL  pick(3) -> {got} not in {valid_for_3}")
            break
    else:
        print("PASS  50 more pick(3) calls all landed in the valid set")

    print()
    print("RUNTIME DEMO -- empirical frequency converging to 1/K, measured live")
    print("-" * 72)
    nums = [1, 2, 3, 3, 3, 3, 3]  # target 3 has K=5 matches: indices 2..6
    target = 3
    K = sum(1 for v in nums if v == target)
    trials = 50_000
    sol2 = Solution(nums)

    t0 = time.perf_counter()
    counts = Counter()
    for _ in range(trials):
        counts[sol2.pick(target)] += 1
    elapsed_ms = (time.perf_counter() - t0) * 1000

    expected = trials / K
    print(f"K = {K} matching indices, expected count each if uniform: {expected:.1f}\n")
    max_dev = 0.0
    for idx in sorted(counts):
        c = counts[idx]
        dev_pct = abs(c - expected) / expected * 100
        max_dev = max(max_dev, dev_pct)
        print(f"  index {idx} -> {c:6d}  (dev {dev_pct:5.1f}%)")

    print(f"\nmax deviation from uniform: {max_dev:.1f}%  over {trials} trials  "
          f"({elapsed_ms:.1f} ms total)")

    uniform_enough = max_dev < 10.0
    all_ok &= uniform_enough
    print(f"{'PASS' if uniform_enough else 'FAIL'}  "
          f"empirical frequencies stay within 10% of the 1/K expectation")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
