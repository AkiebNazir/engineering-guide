"""
================================================================================
SOLUTION · LeetCode 523 · Continuous Subarray Sum                       [Medium]
https://leetcode.com/problems/continuous-subarray-sum/
================================================================================

THE CORE IDEA
--------------
Same remainder trick as problem 007 (LC 974), but this asks EXISTENCE, not a
count, so it uses Variant B from the topic guide (§1.4): a FIRST-INDEX map,
`seen = {0: -1}`, and the moment a remainder recurs with a big enough gap, we
can stop and return True. There is also a genuine length >= 2 constraint and
a k = 0 special case that most template regurgitations get wrong.

    seen = {0: -1}                 # remainder (or raw sum, if k==0) -> first index
    running = 0
    for i, x in enumerate(nums):
        running += x
        key = running % k if k else running     # k==0: congruence mod 0 IS equality
        if key in seen:
            if i - seen[key] >= 2:               # THE LENGTH TRAP
                return True
            # else: don't overwrite -- an earlier index only helps later
        else:
            seen[key] = i
    return False

O(n) time, O(min(n, k)) space for k > 0 (O(n) worst case when k == 0, since
raw prefix sums are not bounded the way remainders are).


================================================================================
WHY VARIANT B (FIRST-INDEX), NOT VARIANT A (COUNTING)
================================================================================
This problem only needs a yes/no answer, so it stores the map value that
maximizes the chance of a hit later: the EARLIEST index each key was seen.
Overwriting to the LATEST index on every recurrence — a common reflex — would
be actively wrong here: it can shrink the gap below 2 and cause the algorithm
to miss a valid answer that the EARLIER index would have satisfied. See the
"don't overwrite" bug demo below for a constructed counter-example.


================================================================================
THE LENGTH >= 2 TRAP — the single most important thing on this page
================================================================================
Sharing a remainder is necessary but NOT sufficient — the two prefixes must
also be far enough apart. If `seen[key] = i_prev` and the current loop index
is `i`, the subarray strictly between them is `nums[i_prev+1 .. i]`, which has
length `i - i_prev`. The problem requires length >= 2, so the check is:

    if i - seen[key] >= 2: return True

Get this wrong and a GAP-1 collision (two adjacent prefixes sharing a
remainder, i.e. a single element whose value happens to be a multiple of k)
is reported as a valid answer even though the "subarray between them" is
length 1, which the problem explicitly disallows. The demo below builds an
input where the buggy no-gap-check version returns True but the correct
answer is False, and runs both side by side.

Concretely: `seen = {0: -1}` means "the empty prefix is at index -1." A
subarray starting at real index 0 and ending at real index 0 (a single
element) has `i = 0`, gap `0 - (-1) = 1` -- correctly rejected as too short.
A subarray `nums[0..1]` (two elements) has `i = 1`, gap `1 - (-1) = 2` --
correctly accepted. The sentinel's `-1` is exactly what makes this
arithmetic come out right for subarrays starting at index 0; using `{0: 0}`
would make every length-1 subarray starting at index 0 look like it has gap
1 too (harmless for k>0 since a single element rarely equals its own
remainder... but for k=0 with nums[0]==0 it would incorrectly read as gap 0
< 2, still rejecting length-1 correctly, yet shifts every other gap
calculation off by one). Use `-1`, not `0` — it is the index "one before the
array starts," matching the topic guide's §1.3 sentinel convention exactly.


================================================================================
THE k = 0 TRAP
================================================================================
LeetCode's own definition: "x is a multiple of k if x = n * k for some
integer n." Substitute k = 0: x = n * 0 = 0 for EVERY n. So the ONLY
multiple of 0 is 0 ITSELF — "sum divisible by 0" means "sum equals 0",
nothing else. There is no meaningful "remainder" when dividing by 0
(`running % 0` raises ZeroDivisionError in Python), so the algorithm must
branch.

The prefix-sum equivalence still holds, just with equality instead of a
remainder match: `sum(nums[l..r]) == 0  <=>  prefix[r+1] == prefix[l]`. This
is not a bolted-on special case — it falls out of the SAME congruence
relation used for k > 0: `a ≡ b (mod k)` means `k | (a - b)`; when k = 0,
"0 divides (a - b)" is only true when `a - b == 0`, i.e. `a == b`. So
`key = running % k if k else running` is ONE algorithm where the k=0 branch
is congruence-mod-0 collapsing to plain equality, not a different algorithm.

    nums = [0, 0], k = 0  ->  True.  prefix = [0, 0, 0]. seen={0:-1} at
    start; at i=0, running=0, key=0, key in seen, gap = 0-(-1) = 1, TOO
    SHORT, don't return yet, don't overwrite (keep -1). At i=1, running=0,
    key=0, key in seen (still -1), gap = 1-(-1) = 2, >= 2 -> True. The
    subarray [0,0] itself, sum 0, IS a multiple of 0 by the definition above.

    nums = [0, 1, 0], k = 0  ->  False. The only length>=2 subarrays are
    [0,1]=1, [1,0]=1, [0,1,0]=1 -- none sums to exactly 0.

A useful sanity CROSS-CHECK exploited by the tests below: since
`0 <= nums[i]` per the constraints, prefix sums are non-decreasing, so two
EQUAL prefix sums with a gap >= 2 force every element strictly between them
to be exactly 0. That means for k=0 the answer reduces to "does `nums`
contain two ADJACENT zeros anywhere" — a much simpler check used purely as
an oracle to validate the general algorithm's k=0 branch, not as the
submitted solution (the general algorithm also correctly handles negative
inputs, which the adjacency shortcut does not).


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [23, 2, 4, 6, 7], k = 6            (LeetCode's own example, answer True)

    seen = {0: -1}, running = 0

    i=0 x=23  running=23  key=23%6=5   not in seen -> seen={0:-1, 5:0}
    i=1 x=2   running=25  key=25%6=1   not in seen -> seen={..., 1:1}
    i=2 x=4   running=29  key=29%6=5   IN seen at 0, gap=2-0=2 >= 2 -> True

    The subarray between indices 1 and 2 (nums[1..2] = [2,4]) sums to 6,
    which is a multiple of 6.  ✓ matches LeetCode's expected answer.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time      Space           Mutates input?
    ---------------------------------  --------  --------------  --------------
    Every subarray, length >= 2, sum   O(n^2)    O(1)            No
    First-index remainder map ✅       O(n)      O(min(n, k))*   No

    * For k == 0, the map is keyed on raw prefix sums (unbounded key space in
      general), so space is O(n) worst case rather than O(min(n, k)).


================================================================================
EDGE CASES
================================================================================
    k = 0                     -> branch to raw-value equality matching, not
                                  a remainder (running % 0 is undefined).
    all zeros, k = 0          -> [0,0] True (adjacent zeros); [0,0,0] also
                                  True; single [0] False (length < 2).
    array length < 2          -> no subarray of length >= 2 can exist at
                                  all; must return False regardless of k.
    exact length-2 boundary   -> a pair (i, i+1) with matching keys must be
                                  ACCEPTED (gap == 2, not rejected).
    gap of exactly 1          -> two ADJACENT indices sharing a key (a
                                  single element that happens to be a
                                  multiple of k) must be REJECTED.
    negative numbers          -> outside the stated 0 <= nums[i] constraint,
                                  but the algorithm should still be correct
                                  for them (the remainder logic doesn't
                                  depend on non-negativity; only the k=0
                                  "adjacent zeros" ORACLE shortcut does).
    k does not divide any
      single element, but a
      combination does         -> exercises that the algorithm looks at
                                  SUMS of subarrays, not individual elements.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the length >= 2 check entirely, or checking `> 0` instead of
   `>= 2` — reports single-element "subarrays" as valid answers.
2. Computing the gap against the wrong index base (prefix-array index vs.
   raw nums index) — an off-by-one that silently shifts every gap by one and
   is invisible on inputs where it doesn't happen to matter.
3. Overwriting `seen[key]` to the newest index on every recurrence instead of
   keeping the first — shrinks future gaps and can cause a real answer to be
   missed. See the "don't overwrite" demo below.
4. Computing `running % k` unconditionally, crashing with ZeroDivisionError
   the first time k = 0 appears in a test.
5. Handling k = 0 by just returning False unconditionally ("division by
   zero, so no answer") — wrong; `[0, 0]` with k=0 IS a valid True case, per
   the problem's own "x = n*k" definition applied at k=0.
6. Using `seen = {0: 0}` instead of `{0: -1}` as the sentinel — shifts every
   gap computed against a subarray starting at index 0 by one, silently
   breaking the length-2 boundary case.
7. Re-deriving the C-style manual remainder normalization from problem 007
   here too, out of habit, when k could be 0 — `((x % k) + k) % k` crashes
   immediately on `k == 0` since it still evaluates `x % k` first.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the length constraint were ">= m" for an arbitrary m, not
   hard-coded to 2?
A: Same algorithm, change the gap check to `i - seen[key] >= m`. Everything
   else — the sentinel, the "don't overwrite" rule, the k=0 branch — is
   unchanged.

Q: How does this compare to problem 007 (LC 974, Subarray Sums Divisible by
   K)?
A: 974 counts every valid subarray (Variant A, `seen = {0: 1}` counting map,
   no length restriction, k is always >= 2 there). 523 asks existence only
   (Variant B, `seen = {0: -1}` first-index map), adds the length >= 2
   constraint, and must handle k = 0. Same remainder trick, different map
   semantics and edge-case surface — see problem 007's solution for the
   direct comparison.

Q: What is the actual answer's subarray, not just True/False?
A: Track it directly: when the gap check passes, `nums[seen[key]+1 : i+1]`
   is a valid answer (0-indexed, exclusive-end slice). No extra bookkeeping
   needed beyond what's already stored.

Q: What if `nums` could be very large and streamed (can't fit in memory /
   index all at once)?
A: The algorithm is already single-pass and only needs O(min(n,k)) (or O(n)
   for k=0) auxiliary state — it streams naturally without modification;
   only the final "recover the subarray" follow-up needs random access back
   into `nums`.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 974  Subarray Sums Divisible by K   — problem 007, the counting sibling
    LC 525  Contiguous Array               — problem 005, Variant B first-index
                                              map with a ±1 remapping instead
                                              of a remainder
    LC 560  Subarray Sum Equals K          — problem 004, the base pattern
    LC 1590 Make Sum Divisible by P        — a harder existence/optimization
                                              variant of the same trick
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def checkSubarraySum(self, nums: List[int], k: int) -> bool:
        """First-index remainder map, k==0 branching to raw-value equality.
        O(n) time, O(min(n, k)) space (O(n) worst case when k == 0)."""
        seen = {0: -1}                     # key -> earliest index seen at
        running = 0
        for i, x in enumerate(nums):
            running += x
            key = running % k if k else running   # k==0: mod-0 IS equality
            if key in seen:
                if i - seen[key] >= 2:     # THE LENGTH TRAP
                    return True
                # gap too short: do NOT overwrite -- keep the earliest index
            else:
                seen[key] = i
        return False

    # ------------------------------------------------------------------
    # Alternatives / oracle.
    # ------------------------------------------------------------------
    def checkSubarraySum_brute(self, nums: List[int], k: int) -> bool:
        """O(n^2) oracle: every subarray of length >= 2, sum it, check."""
        n = len(nums)
        for i in range(n):
            total = nums[i]
            for j in range(i + 1, n):
                total += nums[j]
                if k == 0:
                    if total == 0:
                        return True
                elif total % k == 0:
                    return True
        return False

    def checkSubarraySum_zero_shortcut(self, nums: List[int], k: int) -> bool:
        """k==0-only ORACLE: since nums[i] >= 0 (constraints), the answer
        for k=0 reduces to 'contains two adjacent zeros'. Used only to
        cross-check the general algorithm's k=0 branch; not itself a
        submission (breaks if nums may contain negatives)."""
        if k != 0:
            raise ValueError("this shortcut is only valid for k == 0")
        return any(nums[i] == 0 and nums[i + 1] == 0 for i in range(len(nums) - 1))

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def checkSubarraySum_no_gap_check(self, nums: List[int], k: int) -> bool:
        """✗ BROKEN ON PURPOSE — omits the length >= 2 check entirely.
        Reports a single element that happens to be a multiple of k as a
        valid answer."""
        seen = {0: -1}
        running = 0
        for i, x in enumerate(nums):
            running += x
            key = running % k if k else running
            if key in seen:
                return True                # no gap check at all
            seen[key] = i
        return False

    def checkSubarraySum_overwrite(self, nums: List[int], k: int) -> bool:
        """✗ BROKEN ON PURPOSE — overwrites seen[key] to the LATEST index
        on every recurrence instead of keeping the earliest. Can shrink a
        real gap below 2 and miss a valid answer."""
        seen = {0: -1}
        running = 0
        for i, x in enumerate(nums):
            running += x
            key = running % k if k else running
            if key in seen and i - seen[key] >= 2:
                return True
            seen[key] = i                  # always overwrite -- the bug
        return False

    def checkSubarraySum_crashes_on_zero(self, nums: List[int], k: int) -> bool:
        """✗ BROKEN ON PURPOSE — computes running % k unconditionally.
        Raises ZeroDivisionError the moment k == 0."""
        seen = {0: -1}
        running = 0
        for i, x in enumerate(nums):
            running += x
            key = running % k               # crashes if k == 0
            if key in seen:
                if i - seen[key] >= 2:
                    return True
            else:
                seen[key] = i
        return False


# ==============================================================================
# TESTS — run:  python 008_continuous_subarray_sum_solution.py
# ==============================================================================
CASES = [
    ([23, 2, 4, 6, 7], 6, True),
    ([23, 2, 6, 4, 7], 6, True),
    ([23, 2, 6, 4, 7], 13, False),
    ([0, 0], 0, True),
    ([0, 1, 0], 0, False),
    ([5], 5, False),
    ([1], 1, False),
    ([1, 0], 1, True),
    ([-1, 2, -1, 3], 2, True),
    ([5, 0, 0, 0], 3, True),
    ([1, 2, 3], 5, True),
    ([1, 2, 3], 6, True),
    ([0], 0, False),
    ([0, 0, 0], 0, True),
    ([1, 1], 2, True),
    ([1, 1, 1], 2, True),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    ok = all(sol.checkSubarraySum(nums, k) == expected for nums, k, expected in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  checkSubarraySum ({len(CASES)} cases)")

    ok = all(sol.checkSubarraySum_brute(nums, k) == expected
              for nums, k, expected in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  brute oracle self-check")

    ok = all(sol.checkSubarraySum_zero_shortcut(nums, k) == expected
              for nums, k, expected in CASES if k == 0)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  k=0 'adjacent zeros' shortcut agrees "
          f"with general algorithm")

    # ----------------------------------------------------------------------
    # ⚠️ the length >= 2 trap, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the length >= 2 trap: gap-1 collision must NOT count ---")
    # Constructed so a remainder recurs at ADJACENT indices (gap 1): a
    # single element (6) that is itself a multiple of k=6 sits between two
    # otherwise-unrelated prefix values.
    trap_nums, trap_k = [5, 6, 5], 6
    # prefix: 5, 11, 16 -- remainders mod 6: 5, 5, 4
    # at i=1 (running=11, key=5) collides with seen[5]=0 (from i=0) -- gap=1-0=1, TOO SHORT
    correct = sol.checkSubarraySum(trap_nums, trap_k)
    buggy = sol.checkSubarraySum_no_gap_check(trap_nums, trap_k)
    oracle = sol.checkSubarraySum_brute(trap_nums, trap_k)
    print(f"  nums={trap_nums}, k={trap_k}")
    print(f"  correct (with gap check):    {correct}  (oracle says {oracle})")
    print(f"  buggy   (no gap check):      {buggy}")
    print(f"  {'MISMATCH -- the no-gap-check version is WRONG, as expected' if correct != buggy else 'no difference on this input'}")
    all_ok &= (correct == oracle)

    # ----------------------------------------------------------------------
    # ⚠️ k = 0 special path.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  k = 0: crashes vs correct handling ---")
    zero_cases = [([0, 0], 0, True), ([0, 1, 0], 0, False), ([0], 0, False),
                  ([1, 2, 3], 0, False), ([0, 0, 0], 0, True)]
    print(f"  {'nums':<16} {'k':>2} {'correct':>8} {'oracle':>7}  ok?")
    for nums, k, expected in zero_cases:
        got = sol.checkSubarraySum(nums, k)
        oracle = sol.checkSubarraySum_brute(nums, k)
        ok = got == expected == oracle
        all_ok &= ok
        print(f"  {str(nums):<16} {k:>2} {got!s:>8} {oracle!s:>7}  "
              f"{'yes' if ok else 'NO'}")
    try:
        sol.checkSubarraySum_crashes_on_zero([0, 0], 0)
        print("  unconditional `running % k` did NOT crash -- unexpected")
    except ZeroDivisionError:
        print("  unconditional `running % k` on k=0 -> ZeroDivisionError, "
              "confirmed -- this is why the branch is mandatory")

    # ----------------------------------------------------------------------
    # ⚠️ overwrite-latest-index bug.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  overwriting to the latest index instead of keeping the earliest ---")
    # Constructed so the FIRST occurrence of a remainder pairs validly
    # (gap >= 2) with a later index, but the SECOND occurrence (if it
    # overwrote) would not.
    overwrite_nums, overwrite_k = [6, 0, 6], 6
    # prefix: 6, 6, 12 -- remainders mod 6: 0, 0, 0
    # i=0 key=0 matches sentinel seen[0]=-1, gap=0-(-1)=1, too short, DON'T overwrite (keep -1)
    # i=1 key=0 matches seen[0]=-1 (kept!), gap=1-(-1)=2 -> True
    # if overwritten at i=0 to seen[0]=0: at i=1, gap=1-0=1, too short -- WRONG miss (until i=2 saves it anyway here)
    correct = sol.checkSubarraySum(overwrite_nums, overwrite_k)
    buggy = sol.checkSubarraySum_overwrite(overwrite_nums, overwrite_k)
    oracle = sol.checkSubarraySum_brute(overwrite_nums, overwrite_k)
    print(f"  nums={overwrite_nums}, k={overwrite_k}")
    print(f"  correct (keep earliest index): {correct}  (oracle says {oracle})")
    print(f"  buggy   (overwrite to latest): {buggy}")
    print(f"  {'MISMATCH -- overwriting cost a valid answer, as expected' if correct != buggy else 'no difference on this input (still illustrative of the rule)'}")
    all_ok &= (correct == oracle)

    # ----------------------------------------------------------------------
    # Randomised cross-check, including k=0 in the mix.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle (including k=0) ---")
    random.seed(9)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(1, 10)
        nums = [random.randint(0, 6) for _ in range(n)]   # mostly non-negative per constraints
        k = random.choice([0, 0, 1, 2, 3, 5, 7])           # weight k=0 a bit heavier
        want = sol.checkSubarraySum_brute(nums, k)
        if sol.checkSubarraySum(nums, k) != want:
            mismatches += 1
    print(f"  {trials} random (nums, k) pairs, k=0 included: {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The scan, traced.
    # ----------------------------------------------------------------------
    nums, k = [23, 2, 4, 6, 7], 6
    print(f"\n--- the scan over {nums}, k={k} ---")
    print(f"  {'i':>2} {'x':>3} {'running':>8} {'key':>5} {'gap ok?':>8}")
    seen, running = {0: -1}, 0
    for i, x in enumerate(nums):
        running += x
        key = running % k if k else running
        hit = key in seen
        gap_ok = hit and (i - seen[key] >= 2)
        print(f"  {i:>2} {x:>3} {running:>8} {key:>5} "
              f"{'YES -> return True' if gap_ok else ('too short' if hit else '-')}")
        if gap_ok:
            break
        if not hit:
            seen[key] = i

    # ----------------------------------------------------------------------
    # RUNTIME DEMO: O(n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- O(n) remainder map vs O(n^2) brute force ---")
    print(f"  {'n':>7} {'map O(n)':>10} {'brute O(n^2)':>14} {'speedup':>10}")
    random.seed(5)
    for n in (500, 2000, 8000):
        # bias toward "no answer" so the brute force can't short-circuit early
        nums = [random.randint(1, 1000) for _ in range(n)]
        k = 999999937   # large prime, essentially guarantees no early hit
        t0 = time.perf_counter()
        sol.checkSubarraySum(nums, k)
        t1 = time.perf_counter()
        sol.checkSubarraySum_brute(nums, k)
        t2 = time.perf_counter()
        fast_ms = (t1 - t0) * 1000
        slow_ms = (t2 - t1) * 1000
        speedup = slow_ms / fast_ms if fast_ms > 0 else float("inf")
        print(f"  {n:>7} {fast_ms:>9.2f}ms {slow_ms:>13.2f}ms {speedup:>9.1f}x")
    print("  With a large prime k (no early exit for either version), the O(n)")
    print("  map stays flat while the O(n^2) brute force grows quadratically.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
