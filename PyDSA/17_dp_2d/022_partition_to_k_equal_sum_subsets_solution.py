"""
================================================================================
SOLUTION · LeetCode 698 · Partition to K Equal Sum Subsets              [Medium]
https://leetcode.com/problems/partition-to-k-equal-sum-subsets/
================================================================================

THE CORE IDEA
--------------
Fill buckets one at a time, and let the SET OF USED NUMBERS be the state:

    target = sum(nums) / k
    dp[mask] = how full the current bucket is after using the numbers in mask
               (-1 if no valid order reaches mask)

Because buckets fill in order, sum(mask) decides everything: sum // target
buckets are done and sum % target is in the current one. So each of the 2^n
masks is solved once:

    for mask with dp[mask] >= 0:
        for each unused i with dp[mask] + nums[i] <= target:
            dp[mask | 1<<i] = (dp[mask] + nums[i]) % target

    answer: dp[(1 << n) - 1] == 0


================================================================================
APPROACH 1 · Assign every number to one of k buckets (priced, oracle)
================================================================================
k^n assignments. For n = 16, k = 4 that is 4^16 ≈ 4.3 billion.

    Time: O(k^n)    Space: O(n)


================================================================================
APPROACH 2 · Backtracking with pruning
================================================================================
Place numbers largest first; for each, try every bucket that has room. Two
prunings make it practical:
  - Largest first: big numbers fail fast.
  - Symmetry: if a number doesn't fit into an EMPTY bucket, trying the other
    empty buckets is identical work — stop after the first empty bucket.
Without the symmetry rule, the search explores k! equivalent labelings of
every partial answer. The demo counts calls with and without it.

    Time: exponential in the worst case, fast in practice with pruning.


================================================================================
APPROACH 3 · Bitmask DP ✅ (the answer)
================================================================================
    total = sum(nums)
    if total % k: return False
    target = total // k
    if max(nums) > target: return False
    dp = [-1] * (1 << n)
    dp[0] = 0
    for mask in range(1 << n):
        if dp[mask] < 0: continue
        for i in range(n):
            if not mask >> i & 1 and dp[mask] + nums[i] <= target:
                dp[mask | 1 << i] = (dp[mask] + nums[i]) % target
    return dp[-1] == 0

Masks are visited in increasing numeric order, and adding a bit always makes
a larger number, so every predecessor is finished before its successors.

    Time: O(n * 2^n)    Space: O(2^n)


================================================================================
STEP BY STEP TRACE · nums = [2, 2, 3, 3, 4], k = 2, target = 7
================================================================================
    Indices 0..4 hold [2, 2, 3, 3, 4]. One path through the masks:

    used {}                fill 0
    used {4}               fill 4     (+4)
    used {2, 4}            fill 0     (+3: 4 + 3 = 7, bucket 1 done, fill resets)
    used {1, 2, 4}         fill 2     (+2)
    used {0, 1, 2, 4}      fill 4     (+2)
    used {0, 1, 2, 3, 4}   fill 0     (+3: 4 + 3 = 7, bucket 2 done) -> true

    A blocked move: used {2, 3} has fill 6; adding a 2 would make 8 > 7.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time          Space    Mutates input?
    ------------------------------  ------------  -------  --------------
    Assign each number to a bucket  O(k^n)        O(n)     No
    Backtracking + pruning          exponential   O(n)     Sorts a copy
    Bitmask DP ✅                   O(n * 2^n)    O(2^n)   No


================================================================================
EDGE CASES
================================================================================
    k = 1                 Always true.
    sum % k != 0          False immediately.
    max(nums) > target    False immediately (that number fits nowhere).
    k == n                True only if every number equals target.


================================================================================
COMMON MISTAKES
================================================================================
1. Greedy "largest number into the emptiest bucket". [2, 2, 3, 3, 4], k = 2:
   buckets end as {4, 2, 2} = 8 and {3, 3} = 6, so greedy says false;
   {4, 3} and {3, 2, 2} works. Demo.

2. Backtracking without the empty-bucket symmetry rule: correct, but on an
   infeasible input (where every branch must be refuted) it made 24x more
   calls here, and the gap grows with k. Demo counts them.

3. Forgetting the modulo when a bucket completes (storing sum instead of
   sum % target): the next number can never "fit". Demo.

4. Skipping the early checks: correct, but the DP runs 2^n steps to discover
   what `sum % k` says in O(n).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the actual subsets?
A: Store the index added to reach each mask (a parent pointer) and walk back
   from the full mask; each time the fill resets to 0, a bucket is complete.

Q: Matchsticks to Square (LC 473)?
A: The same problem with k = 4.

Q: n = 40?
A: 2^40 masks is too many. Meet in the middle for k = 2 (split the array,
   enumerate each half's sums), or a heavily pruned search; in general this
   is NP-hard (it generalises Partition).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 416  Partition Equal Subset Sum (16_dp_1d/014)   — k = 2, pseudo-polynomial DP
    LC 473  Matchsticks to Square                       — k = 4
    LC 847  Shortest Path Visiting All Nodes (016)      — another bitmask state
    LC 1723 Find Minimum Time to Finish All Jobs        — bitmask DP over subsets
================================================================================
"""

import random
import time
from itertools import product
from typing import List


class Solution:
    def canPartitionKSubsets(self, nums: List[int], k: int) -> bool:
        total = sum(nums)
        if total % k:
            return False
        target = total // k
        if max(nums) > target:
            return False
        n = len(nums)
        dp = [-1] * (1 << n)
        dp[0] = 0
        for mask in range(1 << n):
            fill = dp[mask]
            if fill < 0:
                continue
            for i in range(n):
                bit = 1 << i
                if not mask & bit and fill + nums[i] <= target:
                    dp[mask | bit] = (fill + nums[i]) % target
        return dp[-1] == 0


# ------------------------------------------------------------------------
# Alternatives / oracle / broken versions for the demos.
# ------------------------------------------------------------------------
def assign_brute(nums: List[int], k: int) -> bool:
    """Oracle: try all k^n bucket assignments (small n only)."""
    total = sum(nums)
    if total % k:
        return False
    target = total // k
    for labels in product(range(k), repeat=len(nums)):
        sums = [0] * k
        for x, b in zip(nums, labels):
            sums[b] += x
        if all(s == target for s in sums):
            return True
    return False


CALLS = 0


def backtrack(nums: List[int], k: int, symmetry: bool = True) -> bool:
    """Approach 2; counts its calls."""
    global CALLS
    total = sum(nums)
    if total % k or max(nums) > total // k:
        return False
    target = total // k
    order = sorted(nums, reverse=True)
    buckets = [0] * k

    def place(idx: int) -> bool:
        global CALLS
        CALLS += 1
        if idx == len(order):
            return True
        x = order[idx]
        for b in range(k):
            if buckets[b] + x <= target:
                buckets[b] += x
                if place(idx + 1):
                    return True
                buckets[b] -= x
            if symmetry and buckets[b] == 0:
                break                       # every other empty bucket is the same
        return False

    return place(0)


def greedy_emptiest(nums: List[int], k: int) -> bool:
    """Mistake 1."""
    total = sum(nums)
    if total % k:
        return False
    buckets = [0] * k
    for x in sorted(nums, reverse=True):
        i = min(range(k), key=lambda j: buckets[j])
        buckets[i] += x
    return all(b == total // k for b in buckets)


def no_modulo_bug(nums: List[int], k: int) -> bool:
    """Mistake 3: stores the running sum, never resetting a completed bucket."""
    total = sum(nums)
    if total % k:
        return False
    target, n = total // k, len(nums)
    dp = [-1] * (1 << n)
    dp[0] = 0
    for mask in range(1 << n):
        if dp[mask] < 0:
            continue
        for i in range(n):
            if not mask >> i & 1 and dp[mask] + nums[i] <= target:
                dp[mask | 1 << i] = dp[mask] + nums[i]          # BUG: no % target
    return dp[-1] == target if k == 1 else dp[-1] == 0


# ==============================================================================
# TESTS — run:  python 022_partition_to_k_equal_sum_subsets_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: bitmask DP vs backtracking vs all assignments ---")
    cases = [([4, 3, 2, 3, 5, 2, 1], 4, True), ([1, 2, 3, 4], 3, False), ([2, 2, 3, 3, 4], 2, True),
             ([5], 1, True), ([1, 1, 1, 1, 2, 2, 2, 2], 4, True), ([2, 2, 2, 2, 3, 4, 5], 4, False),
             ([10, 10, 10, 7, 7, 7, 7, 7, 7, 6, 6, 6], 3, True)]
    for nums, k, want in cases:
        brute = assign_brute(nums, k) if len(nums) <= 8 else want
        results = (sol.canPartitionKSubsets(nums, k), backtrack(nums, k), brute)
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!s:<40} k={k} got={results}  want={want}")

    print("\n--- randomized cross-check vs all assignments (1,500 cases, n <= 8) ---")
    rng = random.Random(698)
    bad = 0
    for _ in range(1500):
        nums = [rng.randint(1, 9) for _ in range(rng.randint(1, 8))]
        k = rng.randint(1, min(4, len(nums)))
        want = assign_brute(nums, k)
        if sol.canPartitionKSubsets(nums, k) != want or backtrack(nums, k) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1,500 random cases agree with brute force")

    print("\n--- mistakes LIVE ---")
    g = greedy_emptiest([2, 2, 3, 3, 4], 2)
    ok = g is False and sol.canPartitionKSubsets([2, 2, 3, 3, 4], 2)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  greedy largest-into-emptiest on [2,2,3,3,4], k=2 -> {g}, want True")
    m = no_modulo_bug([2, 2, 3, 3, 4], 2)
    ok = m is False
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  no modulo when a bucket fills: [2,2,3,3,4], k=2 -> {m}, want True")

    print("\n--- the empty-bucket symmetry rule: calls made by backtracking ---")
    global CALLS
    hard = [10, 10, 10, 7, 7, 7, 7, 7, 7, 6, 6, 6]
    for label, sym in (("with symmetry rule   ", True), ("without symmetry rule", False)):
        CALLS = 0
        t0 = time.perf_counter(); r = backtrack(hard, 3, symmetry=sym); dt = time.perf_counter() - t0
        print(f"      {label}: {CALLS:>9,} calls, {dt * 1000:7.1f} ms -> {r}")
    impossible = [10, 7, 8, 5, 5, 5, 8, 7, 8, 8, 12, 5]              # sum 88, target 22, no partition
    for label, sym in (("with symmetry rule   ", True), ("without symmetry rule", False)):
        CALLS = 0
        t0 = time.perf_counter(); r = backtrack(impossible, 4, symmetry=sym); dt = time.perf_counter() - t0
        print(f"      infeasible, {label}: {CALLS:>9,} calls, {dt * 1000:7.1f} ms -> {r}")
    ok = sol.canPartitionKSubsets(impossible, 4) == backtrack(impossible, 4)
    all_ok &= ok

    print("\n--- bitmask DP at the limit: n = 16 ---")
    nums = [rng.randint(1, 10**4) for _ in range(16)]
    nums[-1] += -sum(nums) % 4                                    # make the total divisible by k
    t0 = time.perf_counter(); r = sol.canPartitionKSubsets(nums, 4); dt = time.perf_counter() - t0
    print(f"      n=16, k=4: {r} in {dt * 1000:.0f} ms ({16 * 2**16:,} transitions at most)")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
