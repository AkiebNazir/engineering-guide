"""
================================================================================
SOLUTION · LeetCode 217 · Contains Duplicate                             [Easy]
https://leetcode.com/problems/contains-duplicate/
================================================================================

THE CORE IDEA
-------------
You are repeatedly asking one question: "have I seen this value before?"

That question has exactly one good answer in an interview: a HASH SET. It turns
an O(n) membership check into an O(1) average one, which collapses the whole
problem from O(n^2) to O(n).

This problem is worth taking seriously despite being Easy, because the
reasoning here — "identify the repeated question, then pick the structure that
answers it in O(1)" — is the reasoning behind roughly a third of all interview
problems.


================================================================================
APPROACH 1 · Brute force (state it, do NOT code it)
================================================================================
Compare every pair:

    for i in range(n):
        for j in range(i + 1, n):
            if nums[i] == nums[j]:
                return True
    return False

    Time:  O(n^2)   — n(n-1)/2 comparisons
    Space: O(1)

With n = 10^5 that is about 5 * 10^9 comparisons. At roughly 10^7 Python
operations per second that is over an hour. It will time out.

In an interview you SAY this approach out loud, give its complexity, and say
"that won't fit the constraint, so let me improve it." You do not spend time
writing it.


================================================================================
APPROACH 2 · Hash set, single pass ✅ (the answer)
================================================================================

    seen = set()
    for n in nums:
        if n in seen:
            return True
        seen.add(n)
    return False

STEP BY STEP for nums = [1, 2, 3, 1]:

    seen = set()

    n = 1:  1 in seen? NO   -> add 1     seen = {1}
    n = 2:  2 in seen? NO   -> add 2     seen = {1, 2}
    n = 3:  3 in seen? NO   -> add 3     seen = {1, 2, 3}
    n = 1:  1 in seen? YES  -> return True   ✓

    Note we never examined index 3's neighbours, never sorted, and stopped the
    instant we had an answer.

And for nums = [1, 2, 3, 4]:

    n = 1: add    seen = {1}
    n = 2: add    seen = {1, 2}
    n = 3: add    seen = {1, 2, 3}
    n = 4: add    seen = {1, 2, 3, 4}
    loop ends -> return False   ✓

    Time:  O(n)  — one pass, O(1) average per lookup and insert
    Space: O(n)  — the set holds up to n elements

WHY THE EARLY RETURN MATTERS: on [1, 1, 1, ..., 1] this returns after 2
elements. The set-length one-liner (Approach 3) always consumes the entire
array. Same big-O, very different real-world behaviour on adversarial input.


================================================================================
APPROACH 3 · Set-length one-liner
================================================================================

    return len(set(nums)) != len(nums)

Building a set drops duplicates, so a shorter set means duplicates existed.

    Time:  O(n)
    Space: O(n)

Elegant, and fastest in CPython for the all-distinct case because set
construction runs in C. But it ALWAYS scans everything — no early exit.
Mention it; prefer Approach 2 when the interviewer cares about early termination.


================================================================================
APPROACH 4 · Sort first — the O(1) SPACE answer
================================================================================

    nums.sort()
    for i in range(1, len(nums)):
        if nums[i] == nums[i - 1]:
            return True
    return False

After sorting, equal values are adjacent, so one linear scan of neighbours is
enough.

    Time:  O(n log n)   — dominated by the sort
    Space: O(1) extra if sorting in place  ⚠️ but see below

⚠️ Two honest caveats to raise yourself:
   - It MUTATES the input. If the caller still needs the original order, you
     must copy first — and then you are back to O(n) space.
   - CPython's Timsort uses O(n) auxiliary space in the worst case, so "O(1)
     space" is really "O(1) beyond the sort's own temp buffer."

This is the approach to give when the interviewer says "now do it without extra
space." Naming the tradeoff (time up, space down, input reordered) is the point.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach          Time         Space    Early exit?  Mutates input?
    ----------------  -----------  -------  -----------  --------------
    Brute force       O(n^2)       O(1)     yes          no
    Hash set     ✅   O(n)         O(n)     yes          no
    set() length      O(n)         O(n)     no           no
    Sort + scan       O(n log n)   O(1)*    yes          YES


================================================================================
EDGE CASES
================================================================================
    [1]                 -> False.  Single element cannot duplicate.
    [1, 1]              -> True.   Smallest true case.
    [-1, -1]            -> True.   Negatives hash fine.
    All distinct        -> False.  Full scan, worst case for Approach 2.
    All identical       -> True.   Best case for Approach 2 (exits at i=1).
    Empty               -> Constraints say n >= 1, but the code returns False
                           correctly anyway.


================================================================================
COMMON MISTAKES
================================================================================
1. Using a LIST instead of a set for `seen`:
       seen = []
       if n in seen:        # ← O(n) scan inside an O(n) loop = O(n^2)
   This is the single most common way to accidentally write a quadratic
   solution, and it looks almost identical to the correct code.

2. Adding to the set BEFORE checking:
       seen.add(n)
       if n in seen: return True     # ← always True on the first element!
   Order matters: check, then add.

3. Using a dict when a set will do. `{}` works but stores useless values.
   Reach for `set` when you only need membership.

4. Claiming the complexity is "O(1) lookup" flatly. It is O(1) AVERAGE; the
   worst case is O(n) on adversarial hash collisions. Say the word "average."


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
    "What if the array is already sorted?"
        -> Skip the set entirely: scan adjacent pairs. O(n) time, O(1) space.

    "What if values are guaranteed to be in 1..n?"
        -> Index-as-hash: negate nums[abs(v)-1] as a seen-marker. O(1) space,
           no sort. See LC 442 / 448 (problem 006 in this folder).

    "What if it doesn't fit in memory?"
        -> External sort, or a Bloom filter for a probabilistic answer with
           no false negatives.

    "Return the duplicate, not just whether one exists?"
        -> Same scan, return `n` instead of True. See LC 287.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 219  Contains Duplicate II   — duplicates within distance k (sliding set)
    LC 220  Contains Duplicate III  — within value distance t (buckets / SortedList)
    LC 287  Find the Duplicate Number — O(1) space via Floyd's cycle detection
    LC 442  Find All Duplicates in an Array — index-as-hash
================================================================================
"""

from typing import List


class Solution:
    def containsDuplicate(self, nums: List[int]) -> bool:
        """Hash set, single pass with early exit. Time O(n), space O(n)."""
        seen: set[int] = set()
        for n in nums:
            if n in seen:      # O(1) average — NOT a list!
                return True
            seen.add(n)
        return False

    # ------------------------------------------------------------------
    # Alternatives, for comparison.
    # ------------------------------------------------------------------
    def containsDuplicate_setlen(self, nums: List[int]) -> bool:
        """One-liner. Same O(n)/O(n), but no early exit."""
        return len(set(nums)) != len(nums)

    def containsDuplicate_sort(self, nums: List[int]) -> bool:
        """O(1) extra space, but O(n log n) and MUTATES the input."""
        nums.sort()
        for i in range(1, len(nums)):
            if nums[i] == nums[i - 1]:
                return True
        return False

    def containsDuplicate_bruteforce(self, nums: List[int]) -> bool:
        """O(n^2). Here for contrast only — never submit this."""
        n = len(nums)
        for i in range(n):
            for j in range(i + 1, n):
                if nums[i] == nums[j]:
                    return True
        return False


# ==============================================================================
# TESTS — run:  python 002_contains_duplicate_solution.py
# ==============================================================================
def run_tests() -> None:
    import time

    sol = Solution()
    cases = [
        ([1, 2, 3, 1], True),
        ([1, 2, 3, 4], False),
        ([1, 1, 1, 3, 3, 4, 3, 2, 4, 2], True),
        ([1], False),
        ([-1, -1], True),
        ([0, 1, -1, 2, -2], False),
        ([2, 2], True),
    ]
    impls = [
        ("hash set  ", sol.containsDuplicate),
        ("set length", sol.containsDuplicate_setlen),
        ("sort+scan ", sol.containsDuplicate_sort),
        ("brute forc", sol.containsDuplicate_bruteforce),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(nums)) == expected for nums, expected in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # Show the O(n) vs O(n^2) gap the constraint is protecting you from.
    print("\n--- why the brute force is ruled out (all-distinct input) ---")
    for n in (1_000, 4_000):
        data = list(range(n))
        t0 = time.perf_counter()
        sol.containsDuplicate(data)
        t_set = time.perf_counter() - t0
        t0 = time.perf_counter()
        sol.containsDuplicate_bruteforce(data)
        t_bf = time.perf_counter() - t0
        print(f"  n={n:>5}  hash set {t_set * 1000:7.2f} ms   "
              f"brute force {t_bf * 1000:8.2f} ms   "
              f"({t_bf / max(t_set, 1e-9):.0f}x slower)")
    print("  (brute force scales x4 when n doubles; the hash set scales x2)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
