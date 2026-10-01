"""
================================================================================
SOLUTION · LeetCode 448 · Find All Numbers Disappeared in an Array       [Easy]
https://leetcode.com/problems/find-all-numbers-disappeared-in-an-array/
================================================================================

THE CORE IDEA
-------------
The constraint `1 <= nums[i] <= n` is the whole problem. Values and indices
occupy the same range, so:

    THE ARRAY IS ITS OWN HASH TABLE.

Value v has a natural home: index v-1. To record "I saw v", mutate slot v-1 in
a way that is reversible and does not destroy the value stored there. Since all
values are guaranteed positive, the SIGN BIT is free real estate.

This technique — INDEX-AS-HASH — is how you hit "O(1) extra space" on a whole
family of problems (LC 41, 442, 448, 645). It only works when values are
bounded by the array length, so the first thing to check is always that
constraint.


================================================================================
APPROACH 1 · Hash set (the obvious answer)
================================================================================
    seen = set(nums)
    return [v for v in range(1, len(nums) + 1) if v not in seen]

    Time:  O(n)      Space: O(n)

Correct, readable, and what most people write. Fails the follow-up, which
explicitly asks for no extra space. State it, then improve.


================================================================================
APPROACH 2 · Sign marking (index-as-hash) ✅✅ (the follow-up answer)
================================================================================

    # Pass 1 — mark
    for v in nums:
        i = abs(v) - 1
        if nums[i] > 0:
            nums[i] = -nums[i]

    # Pass 2 — collect
    return [i + 1 for i, v in enumerate(nums) if v > 0]

STEP BY STEP for nums = [4, 3, 2, 7, 8, 2, 3, 1]:

    PASS 1 — for each value v, negate the slot at index |v|-1

    v=4  -> i=3  nums[3]=7  positive  -> negate  [ 4  3  2 -7  8  2  3  1]
    v=3  -> i=2  nums[2]=2  positive  -> negate  [ 4  3 -2 -7  8  2  3  1]
    v=-2 -> i=1  nums[1]=3  positive  -> negate  [ 4 -3 -2 -7  8  2  3  1]
            ^^^ note v is ALREADY NEGATIVE here — abs() is what saves us
    v=-7 -> i=6  nums[6]=3  positive  -> negate  [ 4 -3 -2 -7  8  2 -3  1]
    v=8  -> i=7  nums[7]=1  positive  -> negate  [ 4 -3 -2 -7  8  2 -3 -1]
    v=2  -> i=1  nums[1]=-3 already negative -> skip
    v=-3 -> i=2  nums[2]=-2 already negative -> skip
    v=-1 -> i=0  nums[0]=4  positive  -> negate  [-4 -3 -2 -7  8  2 -3 -1]

    PASS 2 — positive slots were never marked

    index:   0   1   2   3   4   5   6   7
    value:  -4  -3  -2  -7   8   2  -3  -1
                             ^^  ^^
                          positive at indices 4 and 5
                          -> values 5 and 6 never appeared

    return [5, 6]   ✓

    Time:  O(n)   — two passes
    Space: O(1)   — excluding the output, as the problem allows


⚠️  WHY abs() IS MANDATORY
    By the time you read nums[k] in pass 1, an earlier iteration may already
    have flipped it negative. Without abs():

        v = -2  ->  i = v - 1 = -3   ->  indexes from the END of the list
                                          (Python) or panics (Go)

    You are using the value only as an ADDRESS, and the sign is metadata you
    added, not part of the address. abs() strips the metadata back off.

⚠️  WHY THE `if nums[i] > 0` GUARD MATTERS
    Duplicates exist (that is why numbers go missing). Negating twice returns a
    slot to positive, which would make a present value look absent. The guard
    makes marking idempotent. An equivalent formulation is
    `nums[i] = -abs(nums[i])`, which is also idempotent and needs no branch.

⚠️  IT MUTATES THE INPUT
    The caller's list comes back with scrambled signs. Say this out loud. If it
    matters, restore in a third O(n) pass: `nums[i] = abs(nums[i])`.


================================================================================
APPROACH 3 · Cyclic sort (swap into place)
================================================================================
Instead of flagging, physically move each value to its home slot:

    i = 0
    while i < len(nums):
        home = nums[i] - 1
        if nums[i] != nums[home]:      # compare VALUES, not indices
            nums[i], nums[home] = nums[home], nums[i]
        else:
            i += 1
    return [i + 1 for i, v in enumerate(nums) if v != i + 1]

    Time:  O(n)  — each swap places at least one value permanently, so total
                   swaps <= n even though the loop is nested-looking
    Space: O(1)

Also destructive, and it does not preserve the original values at all (sign
marking at least keeps magnitudes). But cyclic sort generalises to LC 41
(First Missing Positive), LC 268, and LC 287, so it is worth owning.

⚠️ The swap condition must be `nums[i] != nums[home]`, NOT `i != home`. With
duplicates, `i != home` loops forever because the swap makes no progress.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach              Time    Extra space   Mutates input?
    --------------------  ------  ------------  --------------
    Hash set              O(n)    O(n)          no
    Sign marking    ✅✅  O(n)    O(1)          YES (restorable)
    Cyclic sort           O(n)    O(1)          YES (destructive)


================================================================================
EDGE CASES
================================================================================
    [1]            -> [].       Single element, present. Nothing missing.
    [2, 2]         -> [1].      1 never appears; 2 appears twice.
    [1, 1]         -> [2].      Mirror of the above.
    [1, 2, 3, 4]   -> [].       Complete permutation, nothing missing.
    [3, 3, 3, 3]   -> [1,2,4].  Heavy duplication — this is the case that
                                breaks a marking loop with no idempotence guard.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting abs() when computing the index. Python silently indexes from the
   end (no error, wrong answer) — the nastiest kind of bug.

2. Negating unconditionally, so a duplicate flips a slot back to positive and
   a present number is reported missing.

3. Off-by-one between values and indices. Value v lives at index v-1; index i
   corresponds to value i+1. Write it down before you code.

4. Claiming O(1) space while building a set. The OUTPUT is exempt from the
   space bound; an auxiliary set is not.

5. In cyclic sort, using `i != home` as the swap condition — infinite loop on
   duplicates.


================================================================================
RELATED PROBLEMS — the index-as-hash family
================================================================================
    LC 442  Find All Duplicates in an Array — same marking, collect the slots
                                              you find ALREADY negative
    LC 41   First Missing Positive [Hard]   — same idea, but values are
                                              unbounded, so you first discard
                                              anything outside [1, n]
    LC 268  Missing Number                  — one missing value; XOR or Gauss
                                              sum is simpler
    LC 287  Find the Duplicate Number       — Floyd's cycle detection, because
                                              there you may NOT modify the array
    LC 645  Set Mismatch                    — one duplicate AND one missing
================================================================================
"""

from typing import List


class Solution:
    def findDisappearedNumbers(self, nums: List[int]) -> List[int]:
        """Sign marking. Time O(n), O(1) extra space. MUTATES nums."""
        # Pass 1: for value v, mark slot |v|-1 as "seen" by making it negative.
        for v in nums:
            i = abs(v) - 1          # abs() — v may already have been negated
            if nums[i] > 0:         # guard keeps marking idempotent
                nums[i] = -nums[i]

        # Pass 2: a still-positive slot was never marked.
        return [i + 1 for i, v in enumerate(nums) if v > 0]

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def findDisappearedNumbers_restoring(self, nums: List[int]) -> List[int]:
        """Same algorithm, but leaves the caller's list exactly as it found it."""
        for v in nums:
            i = abs(v) - 1
            nums[i] = -abs(nums[i])          # branch-free idempotent marking
        missing = [i + 1 for i, v in enumerate(nums) if v > 0]
        for i in range(len(nums)):           # third pass: restore
            nums[i] = abs(nums[i])
        return missing

    def findDisappearedNumbers_set(self, nums: List[int]) -> List[int]:
        """The obvious O(n)-space answer."""
        seen = set(nums)
        return [v for v in range(1, len(nums) + 1) if v not in seen]

    def findDisappearedNumbers_cyclic(self, nums: List[int]) -> List[int]:
        """Cyclic sort: put every value in its home slot, then read off gaps."""
        i = 0
        while i < len(nums):
            home = nums[i] - 1
            if nums[i] != nums[home]:        # compare VALUES, not indices
                nums[i], nums[home] = nums[home], nums[i]
            else:
                i += 1
        return [i + 1 for i, v in enumerate(nums) if v != i + 1]


# ==============================================================================
# TESTS — run:  python 006_..._solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ([4, 3, 2, 7, 8, 2, 3, 1], [5, 6]),
        ([1, 1], [2]),
        ([1], []),
        ([2, 2], [1]),
        ([1, 2, 3, 4], []),
        ([3, 3, 3, 3], [1, 2, 4]),
        ([2, 1], []),
    ]
    impls = [
        ("sign marking ", sol.findDisappearedNumbers),
        ("+ restoring  ", sol.findDisappearedNumbers_restoring),
        ("hash set     ", sol.findDisappearedNumbers_set),
        ("cyclic sort  ", sol.findDisappearedNumbers_cyclic),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(sorted(fn(list(nums))) == e for nums, e in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # Watch the array become its own hash table.
    print("\n--- sign marking, pass 1 on [4,3,2,7,8,2,3,1] ---")
    nums = [4, 3, 2, 7, 8, 2, 3, 1]
    print(f"  start                  {nums}")
    for k in range(len(nums)):          # iterate LIVE, as the real algorithm does
        v = nums[k]                     # so v may already be negative
        i = abs(v) - 1
        if nums[i] > 0:
            nums[i] = -nums[i]
            print(f"  v={v:>2} -> negate idx {i}  {nums}")
        else:
            print(f"  v={v:>2} -> idx {i} already marked, skip")
    print(f"  positive slots -> {[i + 1 for i, v in enumerate(nums) if v > 0]}")

    # abs() is not optional.
    print("\n--- ⚠️  what happens without abs() ---")
    v = -2
    print(f"  a value already negated: v = {v}")
    print(f"  correct index:  abs(v) - 1 = {abs(v) - 1}")
    print(f"  without abs():      v - 1 = {v - 1}  <- negative index; Python")
    print(f"                                          silently reads from the END")

    # Restoring version really does restore.
    print("\n--- input mutation ---")
    a = [4, 3, 2, 7, 8, 2, 3, 1]
    sol.findDisappearedNumbers(a)
    print(f"  after findDisappearedNumbers:            {a}")
    b = [4, 3, 2, 7, 8, 2, 3, 1]
    sol.findDisappearedNumbers_restoring(b)
    print(f"  after findDisappearedNumbers_restoring:  {b}  <- unchanged")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
