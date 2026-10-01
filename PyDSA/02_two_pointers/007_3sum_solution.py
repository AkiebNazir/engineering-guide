"""
================================================================================
SOLUTION · LeetCode 15 · 3Sum                                          [Medium]
https://leetcode.com/problems/3sum/
================================================================================

THE CORE IDEA
-------------
Reduce 3Sum to 2Sum. Sort, then fix the first element and run LC 167's
converging scan on everything to its right:

    nums.sort()
    for i in range(len(nums) - 2):
        # find pairs in nums[i+1:] that sum to -nums[i]
        l, r = i + 1, len(nums) - 1
        while l < r:
            ...

    O(n) anchors × O(n) scan = O(n²).

That part is mechanical. The part that makes 3Sum a Medium is the one sentence
in the statement:

    "The solution set must NOT CONTAIN DUPLICATE TRIPLETS."

    THREE POINTERS IS EASY. DEDUPLICATION IS THE PROBLEM.

WHY SORTING IS THE RIGHT FIRST MOVE — it buys two things with one purchase:
    1. The elimination argument (LC 167) requires sortedness.
    2. Equal values become ADJACENT, so duplicates are cheap to skip.
It costs O(n log n), which is dominated by the O(n²) scan anyway, so it is
effectively free. It destroys the original indices — irrelevant here, because
the problem asks for VALUES, not positions. (Contrast LC 1, where sorting is
forbidden precisely because indices are the answer.)


================================================================================
THE TWO SKIPS — this is the whole problem
================================================================================
There are exactly two places a duplicate triplet can be born, and each needs
its own skip.

SKIP 1 · DUPLICATE ANCHORS (before the scan)

    if i > 0 and nums[i] == nums[i - 1]:
        continue

    sorted: [-4, -1, -1, 0, 1, 2]
                  i=1  i=2
                   ^    ^ same value

    i=1 anchors on -1 and finds [-1,-1,2] and [-1,0,1].
    i=2 anchors on -1 again and would find [-1,0,1] a second time.

    ⚠️  `i > 0 and` IS MANDATORY. Without it, i=0 evaluates `nums[0] == nums[-1]`
        — Python reads nums[-1] as the LAST element and does not raise. On an
        array that starts and ends with the same value (e.g. [0,0,0]) the very
        first anchor is skipped and you return []. Same negative-index hazard
        as LC 125 and LC 26.

SKIP 2 · DUPLICATE PARTNERS (after recording a hit)

    out.append([nums[i], nums[l], nums[r]])
    l += 1
    while l < r and nums[l] == nums[l - 1]:
        l += 1

    sorted: [-2, 0, 0, 0, 2]     anchor i=0 (-2), looking for pairs summing to 2
    l=1 r=4: 0 + 2 = 2  ✓ record [-2,0,2]
    l=2 r=3: 0 + 0 = 0  — if you had only done l += 1 you would be at l=2 with
             nums[2] == 0 == nums[1], and on a different input that re-finds the
             SAME pair. The skip advances l past the whole run of equal values.

    ⚠️  SKIP *AFTER* RECORDING, NEVER BEFORE. Skipping first drops the valid
        triplet entirely.

⚠️  YOU ONLY NEED TO SKIP ON *ONE* SIDE — AND HERE IS WHY
    A tempting symmetric version also skips r:

        while l < r and nums[r] == nums[r + 1]: r -= 1

    It is harmless but REDUNDANT. Once you advance l past its duplicates, the
    sum nums[l] + nums[r] has strictly increased (nums[l] grew). For the sum to
    return to the target, r must move down. So r is forced to move by the
    arithmetic; it cannot linger on a duplicate and re-form the same pair.

    Knowing the r-skip is unnecessary — rather than adding it defensively — is
    exactly the signal that you understand the invariant rather than having
    memorised the code. The demo below verifies both versions agree on 1000
    random inputs.


================================================================================
APPROACH 0 · Triple loop (state it, price it)
================================================================================
    for i, j, k in all combinations: if sum == 0: add sorted tuple to a set

    Time: O(n³)   Space: O(k)

At n = 3000 that is 4.5·10^9 triples. It is the correctness oracle (the tests
below use it as one) and nothing else.


================================================================================
APPROACH 1 · Sort + anchor + two pointers ✅✅ (the answer)
================================================================================

    nums.sort()
    out = []
    n = len(nums)
    for i in range(n - 2):
        if nums[i] > 0:                       # early exit (see below)
            break
        if i > 0 and nums[i] == nums[i - 1]:  # SKIP 1
            continue
        l, r = i + 1, n - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s < 0:
                l += 1
            elif s > 0:
                r -= 1
            else:
                out.append([nums[i], nums[l], nums[r]])
                l += 1
                while l < r and nums[l] == nums[l - 1]:   # SKIP 2
                    l += 1
    return out

    Time: O(n²)   Space: O(1) beyond the output

STEP BY STEP for nums = [-1,0,1,2,-1,-4]  ->  sorted [-4,-1,-1,0,1,2]:

    i=0  nums[i]=-4   need pair summing to 4, in [-1,-1,0,1,2]
         l=1 r=5:  -4 + -1 + 2 = -3  < 0  ->  l=2
         l=2 r=5:  -4 + -1 + 2 = -3  < 0  ->  l=3
         l=3 r=5:  -4 +  0 + 2 = -2  < 0  ->  l=4
         l=4 r=5:  -4 +  1 + 2 = -1  < 0  ->  l=5
         l=5 == r, stop.  no triplet with -4.

    i=1  nums[i]=-1   need pair summing to 1, in [-1,0,1,2]
         l=2 r=5:  -1 + -1 + 2 =  0  ==  ->  RECORD [-1,-1,2]
                   l=3; nums[3]=0 != nums[2]=-1, no skip needed
         l=3 r=5:  -1 +  0 + 2 =  1  > 0  ->  r=4
         l=3 r=4:  -1 +  0 + 1 =  0  ==  ->  RECORD [-1,0,1]
                   l=4; l == r, stop.

    i=2  nums[i]=-1 == nums[1]  ->  SKIP 1 fires, continue
         (without it, this anchor re-discovers [-1,0,1])

    i=3  nums[i]=0 -> not > 0, so no early break; scans [1,2], finds nothing.

    result: [[-1,-1,2], [-1,0,1]]                                          ✓

THE EARLY EXIT — `if nums[i] > 0: break`
    The array is sorted, so once the anchor is positive, nums[l] and nums[r]
    are both >= nums[i] > 0 and the sum of three positives can never be zero.
    Every remaining anchor is hopeless, so `break` (not `continue`).

    This does not change the O(n²) bound — worst case is an all-negative array
    where it never fires. But on realistic mixed input it prunes roughly half
    the anchors, and the demo below measures the reduction.

⚠️  THE OUTER LOOP BOUND IS `n - 2`
    An anchor needs two elements to its right. `range(n)` would set l = n-1 and
    r = n-1 on the last iteration, `while l < r` is immediately false, so it is
    harmless — but `n - 2` states the intent.


================================================================================
APPROACH 2 · Hash set for the inner search
================================================================================
Replace the two-pointer scan with a Two-Sum-style hash lookup per anchor:

    for i in range(n):
        seen = set()
        for j in range(i + 1, n):
            want = -nums[i] - nums[j]
            if want in seen:
                out.add(tuple(sorted((nums[i], nums[j], want))))
            seen.add(nums[j])

    Time: O(n²)   Space: O(n) for the set, plus O(k) for dedupe

Same time complexity and it does NOT require sorting. But it needs O(n) extra
space, and deduplication now has to go through a set of tuples rather than the
cheap adjacency skip. It is the answer to give if someone forbids sorting;
otherwise the two-pointer version is cleaner and uses O(1) extra space.


================================================================================
APPROACH 3 · No-skip + set dedupe (works, but it is the weaker answer)
================================================================================
    Drop both skips, collect every hit, and dedupe at the end:

        found = set()
        ... found.add((nums[i], nums[l], nums[r]))
        return [list(t) for t in found]

Correct, because sorting means each triplet is generated in canonical order.
But:
  - It does strictly MORE work — duplicate anchors re-run whole inner scans.
    On duplicate-heavy input that is a real slowdown, measured below.
  - It costs O(k) extra space for the set.
  - It reads as "I could not work out the invariant, so I cleaned up
    afterwards."

Know it as a fallback. Do not lead with it.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums), k = number of output triplets

    Approach                Time         Extra space   Sorts?  Mutates input?
    ----------------------  -----------  ------------  ------  --------------
    Triple loop             O(n³)        O(k)          no      no
    Hash set inner          O(n²)        O(n + k)      no      no
    No-skip + set dedupe    O(n²)        O(k)          yes     YES (sort)
    Sort + 2 ptr + skips ✅ O(n²)        O(1) + output yes     YES (sort)

    ⚠️  `nums.sort()` MUTATES THE CALLER'S LIST. If that matters, use
        `nums = sorted(nums)` — O(n) extra space, but the caller's array is
        left alone. Say which one you chose and why; silently reordering a
        caller's data is a real bug in real code.

    ⚠️  Quote the honest total: **O(n²)**, with the O(n log n) sort dominated.
        Saying "O(n)" because "it's two pointers" is a red flag.


================================================================================
EDGE CASES
================================================================================
    [0,0,0]        -> [[0,0,0]]
                      Exactly one triplet, all identical. THE `i > 0` GUARD
                      DETECTOR: without it, nums[0] == nums[-1] is 0 == 0, the
                      only anchor is skipped, and you return [].

    [0,0,0,0]      -> [[0,0,0]]
                      Four zeroes, still ONE triplet. Anchors i=1,2 are skipped
                      by SKIP 1; SKIP 2 stops the inner scan re-finding it.

    [0,1,1]        -> []
                      No valid triplet. Must return [], not None.

    [-1,0,1]       -> [[-1,0,1]]
                      MINIMUM LENGTH (n=3). Exercises the `n - 2` bound.

    [-2,-2,0,2,2]  -> duplicates on BOTH sides of the anchor. The case that
                      distinguishes "skip one side" from "skip neither".

    [1,2,3]        -> []
                      All positive. The early exit fires on the very first
                      anchor and the whole function is O(n log n).

    all-negative   -> []
                      The early exit NEVER fires. This is the worst case for
                      the pruning, and it is why the bound stays O(n²).


================================================================================
COMMON MISTAKES
================================================================================
1. Omitting `i > 0 and` from the anchor skip. `nums[-1]` does not raise; on
   [0,0,0] you silently return [].

2. Forgetting SKIP 2, so repeated partner values emit the same triplet twice.

3. Doing SKIP 2 *before* appending, which drops the valid triplet.

4. Using `continue` instead of `break` for the `nums[i] > 0` early exit. Still
   correct, just pointless work — and it signals you did not notice that
   sortedness makes every LATER anchor hopeless too.

5. Not sorting at all, then trying to use two pointers. The elimination
   argument is invalid on unsorted data and you get wrong answers, not just
   slow ones.

6. `nums.sort()` when the caller needed their array intact.

7. Returning a set of tuples instead of a list of lists. Match the required
   output type.

8. Adding the redundant `nums[r] == nums[r+1]` skip and believing it is
   required. Harmless, but be able to say it is redundant and why.

9. Comparing test output with `==` on the raw nested list. Both the triplet
   order and the order within a triplet are unspecified; normalise both sides.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: 4Sum? kSum?
A: Add another outer loop for 4Sum: O(n³). In general kSum is O(n^(k-1)) —
   recurse, peeling one anchor per level, until k == 2 and you run the
   two-pointer base case. Write it as `kSum(nums, target, k)` with the same
   two skips at every level. LC 18.

Q: Sum to an arbitrary target T instead of 0?
A: Look for pairs summing to `T - nums[i]`. The ONLY thing that breaks is the
   `nums[i] > 0` early exit — it assumed a zero target. The general guard is
   `if nums[i] * 3 > T: break` (the smallest possible remaining sum already
   exceeds T). Getting that right shows you understood the pruning rather than
   copying it.

Q: Return the COUNT of triplets rather than the triplets?
A: On a hit you can count a whole block at once: if there are `a` copies of
   nums[l] and `b` copies of nums[r], that is a*b triplets, and you jump both
   pointers past their runs. Still O(n²) but it avoids materialising output
   that can be O(n³) in size... which is also the answer to "why can't this be
   faster than O(n²)?" — the OUTPUT alone can be Θ(n²) triplets, so no
   algorithm that lists them can beat it.

Q: Can you do better than O(n²)?
A: Not for listing them, by the output-size argument above. 3SUM is also a
   classic conjectured-hard problem: the best known algorithms are only
   marginally sub-quadratic (n²/polylog), and "3SUM-hardness" is used as a
   lower-bound assumption for a whole family of computational-geometry
   problems. Saying that is a strong signal.

Q: The array has huge duplicate runs (e.g. a million zeroes).
A: The skips already collapse each run to one anchor, so the effective n is
   the number of DISTINCT values. Deduplicating into (value, count) pairs
   first makes that explicit and can turn a million elements into a handful.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1    Two Sum                  — unsorted, return indices -> hash map
    LC 167  Two Sum II               — the inner scan; problem 006 in this folder
    LC 16   3Sum Closest             — same walk, track the best difference
    LC 18   4Sum                     — one more outer loop; same two skips
    LC 259  3Sum Smaller             — count pairs, not enumerate: on a hit,
                                        (r - l) triplets at once
    LC 923  3Sum With Multiplicity   — the counting variant, with combinatorics
    LC 611  Valid Triangle Number    — sort + two pointers, different predicate
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def threeSum(self, nums: List[int]) -> List[List[int]]:
        """Sort + anchor + converging scan, with both dedupe skips.

        Time O(n^2), space O(1) beyond the output. MUTATES nums (sorts it).
        """
        nums.sort()
        out: List[List[int]] = []
        n = len(nums)

        for i in range(n - 2):
            if nums[i] > 0:                          # sorted: no zero-sum left
                break
            if i > 0 and nums[i] == nums[i - 1]:     # SKIP 1: duplicate anchors
                continue

            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1                           # need more
                elif s > 0:
                    r -= 1                           # need less
                else:
                    out.append([nums[i], nums[l], nums[r]])
                    l += 1
                    # SKIP 2: duplicate partners. AFTER recording, never before.
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
        return out

    # ------------------------------------------------------------------
    # Alternatives and deliberate breakages.
    # ------------------------------------------------------------------
    def threeSum_nonmutating(self, nums: List[int]) -> List[List[int]]:
        """Same algorithm, but leaves the caller's list alone. O(n) extra."""
        return self.threeSum(sorted(nums))

    def threeSum_hashset(self, nums: List[int]) -> List[List[int]]:
        """Hash-set inner search. O(n^2) time, O(n) space, no sorting needed."""
        found = set()
        n = len(nums)
        for i in range(n):
            seen = set()
            for j in range(i + 1, n):
                want = -nums[i] - nums[j]
                if want in seen:
                    found.add(tuple(sorted((nums[i], nums[j], want))))
                seen.add(nums[j])
        return [list(t) for t in found]

    def threeSum_noskip(self, nums: List[int]) -> List[List[int]]:
        """No skips; dedupe with a set at the end. Correct but does more work."""
        nums = sorted(nums)
        found = set()
        n = len(nums)
        for i in range(n - 2):
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    found.add((nums[i], nums[l], nums[r]))
                    l += 1
        return [list(t) for t in found]

    def threeSum_both_skips(self, nums: List[int]) -> List[List[int]]:
        """Adds the REDUNDANT right-side skip. Correct — just unnecessary."""
        nums = sorted(nums)
        out: List[List[int]] = []
        n = len(nums)
        for i in range(n - 2):
            if nums[i] > 0:
                break
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    out.append([nums[i], nums[l], nums[r]])
                    l += 1
                    r -= 1
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
                    while l < r and nums[r] == nums[r + 1]:      # redundant
                        r -= 1
        return out

    def threeSum_no_i_guard(self, nums: List[int]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — anchor skip without the `i > 0` guard."""
        nums = sorted(nums)
        out: List[List[int]] = []
        n = len(nums)
        for i in range(n - 2):
            if nums[i] == nums[i - 1]:               # i=0 reads nums[-1]!
                continue
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    out.append([nums[i], nums[l], nums[r]])
                    l += 1
                    while l < r and nums[l] == nums[l - 1]:
                        l += 1
        return out

    def threeSum_no_skip2(self, nums: List[int]) -> List[List[int]]:
        """✗ BROKEN ON PURPOSE — anchor skip only, no partner skip."""
        nums = sorted(nums)
        out: List[List[int]] = []
        n = len(nums)
        for i in range(n - 2):
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            l, r = i + 1, n - 1
            while l < r:
                s = nums[i] + nums[l] + nums[r]
                if s < 0:
                    l += 1
                elif s > 0:
                    r -= 1
                else:
                    out.append([nums[i], nums[l], nums[r]])
                    l += 1                            # no duplicate skip
        return out


# ==============================================================================
# TESTS — run:  python 007_3sum_solution.py
# ==============================================================================
def _norm(triplets):
    return sorted(sorted(t) for t in triplets)


def _brute(nums):
    """O(n^3) correctness oracle."""
    found = set()
    n = len(nums)
    for a in range(n):
        for b in range(a + 1, n):
            for c in range(b + 1, n):
                if nums[a] + nums[b] + nums[c] == 0:
                    found.add(tuple(sorted((nums[a], nums[b], nums[c]))))
    return [list(t) for t in sorted(found)]


HARD = [-4, -2, -2, -2, 0, 1, 2, 2, 2, 3, 3, 4, 4, 6, 6]


def run_tests() -> None:
    sol = Solution()
    cases = [
        [-1, 0, 1, 2, -1, -4],
        [0, 1, 1],
        [0, 0, 0],
        [0, 0, 0, 0],
        [-2, 0, 1, 1, 2],
        [1, 2, -2, -1],
        [-1, 0, 1],
        [3, 0, -2, -1, 1, 2],
        [1, 1, -2],
        [-2, -2, 0, 2, 2],
        [1, 2, 3],
        [-3, -2, -1],
        HARD,
    ]
    impls = [
        ("sort+2ptr+skips", sol.threeSum),
        ("non-mutating   ", sol.threeSum_nonmutating),
        ("hash set inner ", sol.threeSum_hashset),
        ("no-skip + dedupe", sol.threeSum_noskip),
        ("both skips     ", sol.threeSum_both_skips),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(_norm(fn(list(c))) == _norm(_brute(c)) for c in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^3) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^3) oracle ---")
    random.seed(15)
    trials, mismatches = 1000, 0
    for _ in range(trials):
        n = random.randint(3, 12)
        arr = [random.randint(-6, 6) for _ in range(n)]
        want = _norm(_brute(arr))
        for _, fn in impls:
            if _norm(fn(list(arr))) != want:
                mismatches += 1
    print(f"  {trials} random arrays x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The two skips, traced.
    # ----------------------------------------------------------------------
    print("\n--- where each skip fires, nums = [-1,0,1,2,-1,-4] ---")
    nums = sorted([-1, 0, 1, 2, -1, -4])
    print(f"  sorted: {nums}")
    n = len(nums)
    for i in range(n - 2):
        if nums[i] > 0:
            print(f"  i={i} nums[i]={nums[i]:>3}  EARLY BREAK (positive anchor)")
            break
        if i > 0 and nums[i] == nums[i - 1]:
            print(f"  i={i} nums[i]={nums[i]:>3}  SKIP 1 (same as nums[{i-1}])")
            continue
        print(f"  i={i} nums[i]={nums[i]:>3}  scan for pair summing to "
              f"{-nums[i]}")
        l, r = i + 1, n - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s < 0:
                print(f"      l={l} r={r}  {nums[i]}+{nums[l]}+{nums[r]}={s} <0"
                      f"  -> l={l+1}")
                l += 1
            elif s > 0:
                print(f"      l={l} r={r}  {nums[i]}+{nums[l]}+{nums[r]}={s} >0"
                      f"  -> r={r-1}")
                r -= 1
            else:
                print(f"      l={l} r={r}  {nums[i]}+{nums[l]}+{nums[r]}=0"
                      f"   RECORD [{nums[i]},{nums[l]},{nums[r]}]")
                l += 1
                skipped = 0
                while l < r and nums[l] == nums[l - 1]:
                    l += 1
                    skipped += 1
                if skipped:
                    print(f"          SKIP 2: advanced l past {skipped} "
                          f"duplicate(s) -> l={l}")

    # ----------------------------------------------------------------------
    # ⚠️  The `i > 0` guard.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  anchor skip without the `i > 0` guard ---")
    print(f"  {'input':<22} {'correct':<26} {'no i>0 guard':<26} ok?")
    for probe in ([0, 0, 0], [0, 0, 0, 0], [-1, 0, 1], [-1, 0, 1, 2, -1, -4],
                  [-2, -2, 0, 2, 2]):
        good = _norm(sol.threeSum(list(probe)))
        bad = _norm(sol.threeSum_no_i_guard(list(probe)))
        print(f"  {str(probe):<22} {str(good):<26} {str(bad):<26} "
              f"{'yes' if good == bad else 'NO  ✗'}")
    print("  At i=0 the test becomes `nums[0] == nums[-1]` — first vs LAST.")
    print("  On [0,0,0] that is 0 == 0, the only anchor is skipped, and the")
    print("  answer comes back empty. No IndexError; Python reads nums[-1]")
    print("  happily. This is LeetCode's own example 3, so the bug is caught")
    print("  immediately — but only if you actually run that example.")

    # ----------------------------------------------------------------------
    # ⚠️  Missing SKIP 2.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  no partner skip (SKIP 2 missing) ---")
    print(f"  {'input':<26} {'correct':<24} {'no SKIP 2 (raw output)'}")
    for probe in ([-2, 0, 0, 0, 2], [0, 0, 0, 0], [-2, -2, 0, 2, 2],
                  [-1, -1, 0, 0, 1, 1]):
        good = sol.threeSum(list(probe))
        bad = sol.threeSum_no_skip2(list(probe))
        flag = "" if _norm(good) == _norm(bad) else "   <- DUPLICATES"
        print(f"  {str(probe):<26} {str(good):<24} {bad}{flag}")
    print("  Without SKIP 2 the same triplet is emitted once per duplicate")
    print("  partner value. The problem explicitly forbids duplicate triplets,")
    print("  so this is a wrong answer, not a performance issue.")

    # ----------------------------------------------------------------------
    # The right-side skip really is redundant.
    # ----------------------------------------------------------------------
    print("\n--- is the right-side skip needed? (1000 random arrays) ---")
    random.seed(99)
    diff = 0
    for _ in range(1000):
        arr = [random.randint(-8, 8) for _ in range(random.randint(3, 14))]
        if _norm(sol.threeSum(list(arr))) != _norm(sol.threeSum_both_skips(list(arr))):
            diff += 1
    print(f"  one-sided skip vs both-sided skip: {diff} disagreements / 1000")
    print("  Zero. Advancing l past its duplicates strictly INCREASES the sum,")
    print("  so r is forced downward by the arithmetic — it cannot linger on a")
    print("  duplicate and re-form the same pair. The r-skip is dead code.")

    # ----------------------------------------------------------------------
    # What the early exit prunes.
    # ----------------------------------------------------------------------
    print("\n--- what `if nums[i] > 0: break` prunes ---")

    def anchors_scanned(nums, early_exit):
        nums = sorted(nums)
        n, count = len(nums), 0
        for i in range(n - 2):
            if early_exit and nums[i] > 0:
                break
            if i > 0 and nums[i] == nums[i - 1]:
                continue
            count += 1
        return count

    random.seed(7)
    print(f"  {'input shape':<26} {'anchors, no exit':>17} {'with exit':>11}")
    for label, arr in (
        ("all positive", [random.randint(1, 50) for _ in range(400)]),
        ("all negative", [random.randint(-50, -1) for _ in range(400)]),
        ("mixed", [random.randint(-50, 50) for _ in range(400)]),
    ):
        print(f"  {label:<26} {anchors_scanned(arr, False):>17} "
              f"{anchors_scanned(arr, True):>11}")
    print("  All-negative is the worst case: the exit never fires, which is")
    print("  why the bound stays O(n^2). On mixed input it removes about half")
    print("  the anchors. On all-positive input it breaks at the very first")
    print("  anchor and scans NONE, collapsing the whole call to the O(n log n)")
    print("  sort — a genuine best case, not just a constant-factor trim.")

    # ----------------------------------------------------------------------
    # ⚠️  sort() mutates the caller's list.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  nums.sort() mutates the caller's array ---")
    caller = [-1, 0, 1, 2, -1, -4]
    before = list(caller)
    sol.threeSum(caller)
    print(f"  before threeSum:            {before}")
    print(f"  after  threeSum:            {caller}   <- reordered")
    caller2 = [-1, 0, 1, 2, -1, -4]
    sol.threeSum_nonmutating(caller2)
    print(f"  after  threeSum_nonmutating: {caller2}   <- untouched")
    print("  Fine for LeetCode, a real bug in real code. Use sorted(nums) if")
    print("  the caller still needs their data, and say which you chose.")

    # ----------------------------------------------------------------------
    # Skipping is not just about correctness — it is faster too.
    # ----------------------------------------------------------------------
    print("\n--- skips vs set-dedupe, on duplicate-heavy input ---")
    for label, arr in (
        ("few duplicates ", [random.randint(-500, 500) for _ in range(600)]),
        ("many duplicates", [random.randint(-8, 8) for _ in range(600)]),
    ):
        row = []
        for fn in (sol.threeSum, sol.threeSum_noskip, sol.threeSum_hashset):
            t0 = time.perf_counter()
            fn(list(arr))
            row.append((time.perf_counter() - t0) * 1000)
        print(f"  {label}  skips {row[0]:7.1f}ms   no-skip+set {row[1]:7.1f}ms"
              f"   hashset {row[2]:7.1f}ms")
    print("  On duplicate-heavy input the skips avoid re-running whole inner")
    print("  scans for anchors that can only reproduce known triplets.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
