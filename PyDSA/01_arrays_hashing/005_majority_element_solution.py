"""
================================================================================
SOLUTION · LeetCode 169 · Majority Element                               [Easy]
https://leetcode.com/problems/majority-element/
================================================================================

THE CORE IDEA
-------------
Everything here hinges on one word in the problem statement: the majority
element appears MORE THAN ⌊n/2⌋ times. Strictly more than half. Which means:

    count(majority)  >  count(everything else COMBINED)

Once you see it that way, the O(1)-space algorithm almost writes itself. If you
repeatedly cancel one majority element against one non-majority element, you
run out of non-majority elements first. The majority is the last one standing.


================================================================================
APPROACH 1 · Hash map counting
================================================================================
    counts = Counter(nums)
    return max(counts, key=counts.get)

    Time:  O(n)      Space: O(n)

Correct and obvious. Fails the follow-up on space. Say it, then improve.


================================================================================
APPROACH 2 · Sort and take the middle
================================================================================
    nums.sort()
    return nums[len(nums) // 2]

    Time:  O(n log n)    Space: O(1) if sorted in place (⚠️ mutates input)

WHY THIS WORKS — worth being able to justify, it is a common follow-up:
an element occupying more than half the positions must, once sorted, form a
contiguous block longer than n/2. A block longer than half the array cannot
avoid covering index n//2, no matter where it starts.

    n = 7, majority appears 4 times. The block is 4 long in a 7-slot array:
      best case it starts at 0:  [M M M M _ _ _]   covers index 3 ✓
      worst case it ends at 6:   [_ _ _ M M M M]   covers index 3 ✓
    Any 4-length block in a 7-array must straddle index 3.

Clean, but O(n log n) and it reorders the caller's data.


================================================================================
APPROACH 3 · Boyer–Moore Majority Vote ✅✅ (the follow-up answer)
================================================================================

    count, candidate = 0, None
    for v in nums:
        if count == 0:
            candidate = v
        count += 1 if v == candidate else -1
    return candidate

THE MENTAL MODEL — a battle where opposites annihilate:
Think of each element as a soldier. Soldiers of different armies kill each
other one-for-one. The majority army has more soldiers than every other army
combined, so when the dust settles, only majority soldiers can remain.

`count` is "how many soldiers of the current candidate's army are still
standing, unopposed." When it hits 0, the current candidate has been fully
cancelled, so we adopt whoever we see next.

STEP BY STEP for nums = [2, 2, 1, 1, 1, 2, 2]:

    idx  v   count==0?  candidate  count   note
    ---  --  ---------  ---------  -----   ----------------------------
      0   2  yes        2          1       adopt 2
      1   2  no         2          2       matches, +1
      2   1  no         2          1       differs, -1  (a 1 kills a 2)
      3   1  no         2          0       differs, -1  (candidate wiped out)
      4   1  yes        1          1       adopt 1
      5   2  no         1          0       differs, -1  (candidate wiped out)
      6   2  yes        2          1       adopt 2

    return 2   ✓   (2 appears 4 times out of 7 — a true majority)

Notice the candidate changed three times. That is fine. The algorithm does not
track "the most frequent so far" at any intermediate point — the invariant is
weaker and subtler:

    INVARIANT: after processing a prefix, if a majority element exists in the
    FULL array, then it is either the current candidate, or its surplus was
    spent cancelling an equal number of non-majority elements in the discarded
    prefix — and the remaining suffix still contains it as a majority.

Each cancellation removes ONE majority and ONE non-majority element. Since the
majority strictly outnumbers all others, cancellations run out of non-majority
elements before they run out of majority ones.

    Time:  O(n)   — single pass
    Space: O(1)   — two scalars, regardless of n

⚠️ CRITICAL CAVEAT: Boyer–Moore returns a candidate, NOT a verified majority.
If no majority exists it returns garbage. Here the problem guarantees one
exists, so a single pass suffices. If that guarantee is removed (LC 229, or any
real-world use), you MUST add a second verification pass:

    if nums.count(candidate) > len(nums) // 2: return candidate
    return -1   # or whatever "no majority" means

That is still O(n) time and O(1) space. Volunteering this caveat is the
difference between reciting the algorithm and understanding it.


================================================================================
APPROACH 4 · Bit voting (the "if I can't use extra space at all" flex)
================================================================================
Since the majority element occupies > n/2 positions, for EVERY bit position the
majority's bit value is the one that appears in more than half the numbers. So
you can reconstruct it bit by bit:

    result = 0
    for bit in range(32):
        ones = sum((v >> bit) & 1 for v in nums)
        if ones > len(nums) // 2:
            result |= 1 << bit

    Time:  O(32n) = O(n)     Space: O(1)

Slower in practice, and negative numbers need sign handling. Worth knowing as a
demonstration that the majority property holds independently at every bit.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time         Space   Mutates?  Needs guarantee?
    --------------------  -----------  ------  --------  ----------------
    Hash map              O(n)         O(n)    no        no
    Sort + middle         O(n log n)   O(1)    YES       no
    Boyer–Moore     ✅✅  O(n)         O(1)    no        YES (or verify)
    Bit voting            O(n)         O(1)    no        no


================================================================================
EDGE CASES
================================================================================
    [1]              -> 1.  Single element is trivially a majority (1 > 0).
    [1, 2, 1]        -> 1.  Candidate flips, then recovers.
    [6, 5, 5]        -> 5.  Majority is NOT the first element — this catches
                            anyone who forgot the count==0 re-adoption.
    [-1,-1,-1,2,3]   -> -1. Negatives work; Boyer–Moore never inspects values
                            beyond equality.
    All identical    -> that element; count only ever increments.


================================================================================
COMMON MISTAKES
================================================================================
1. Returning `count` instead of `candidate`. The counter is scaffolding, not
   the answer.

2. Only adopting a new candidate at the start. You must re-adopt EVERY time
   count reaches 0 — see [6, 5, 5], where the first candidate (6) is wrong.

3. Assuming the candidate is always the most frequent element seen SO FAR. It
   is not, at intermediate steps. Only the final value is meaningful.

4. Using Boyer–Moore where no majority is guaranteed, without the verification
   pass. It will confidently return nonsense.

5. Claiming the sort approach is O(1) space in Python. Timsort uses O(n)
   auxiliary space in the worst case.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 229  Majority Element II — elements appearing > n/3 times. Generalised
                                  Boyer–Moore with TWO candidates and two
                                  counters, plus a MANDATORY verification pass.
                                  (For > n/k you need k-1 candidates.)
    LC 1150 Check If a Number Is Majority Element in a Sorted Array
    LC 面试题 39 (LCOF) — the same problem, different judge
================================================================================
"""

from collections import Counter
from typing import List


class Solution:
    def majorityElement(self, nums: List[int]) -> int:
        """Boyer–Moore majority vote. Time O(n), space O(1)."""
        count = 0
        candidate = None
        for v in nums:
            if count == 0:              # current candidate fully cancelled
                candidate = v           # adopt whoever we see next
            count += 1 if v == candidate else -1
        return candidate

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def majorityElement_verified(self, nums: List[int]) -> int:
        """Boyer–Moore WITH the verification pass — use this when no majority
        is guaranteed. Still O(n) time, O(1) space. Returns -1 if none."""
        count, candidate = 0, None
        for v in nums:
            if count == 0:
                candidate = v
            count += 1 if v == candidate else -1
        # Second pass: confirm the candidate is genuinely a majority.
        if sum(1 for v in nums if v == candidate) > len(nums) // 2:
            return candidate
        return -1

    def majorityElement_hashmap(self, nums: List[int]) -> int:
        """O(n) time, O(n) space. Needs no majority guarantee."""
        counts = Counter(nums)
        return max(counts, key=counts.get)

    def majorityElement_sort(self, nums: List[int]) -> int:
        """A block longer than n/2 must cover index n//2. MUTATES the input."""
        nums.sort()
        return nums[len(nums) // 2]


# ==============================================================================
# TESTS — run:  python 005_majority_element_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([3, 2, 3], 3),
        ([2, 2, 1, 1, 1, 2, 2], 2),
        ([1], 1),
        ([1, 2, 1], 1),
        ([6, 5, 5], 5),
        ([-1, -1, -1, 2, 3], -1),
        ([8, 8, 7, 7, 7], 7),
    ]
    impls = [
        ("Boyer-Moore ", sol.majorityElement),
        ("BM+verify   ", sol.majorityElement_verified),
        ("hash map    ", sol.majorityElement_hashmap),
        ("sort+middle ", sol.majorityElement_sort),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(nums)) == e for nums, e in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # Trace the candidate flipping — the part people find unintuitive.
    print("\n--- Boyer-Moore trace: [2,2,1,1,1,2,2] ---")
    print("  idx  v   candidate  count  note")
    count, candidate = 0, None
    for i, v in enumerate([2, 2, 1, 1, 1, 2, 2]):
        note = ""
        if count == 0:
            candidate = v
            note = f"adopt {v}"
        count += 1 if v == candidate else -1
        if count == 0 and not note:
            note = "candidate wiped out"
        print(f"  {i:>3}  {v}   {candidate:>9}  {count:>5}  {note}")
    print(f"  -> returns {candidate}")

    # The caveat: without a guaranteed majority it returns garbage.
    print("\n--- ⚠️  no majority exists: candidate is meaningless ---")
    no_majority = [1, 2, 3, 4]
    print(f"  nums={no_majority}  (no element appears > 2 times)")
    print(f"  bare Boyer-Moore -> {sol.majorityElement(no_majority)}  <- GARBAGE")
    print(f"  with verification -> {sol.majorityElement_verified(no_majority)}  "
          f"<- correctly reports 'none'")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
