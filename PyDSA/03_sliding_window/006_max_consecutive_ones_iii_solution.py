"""
================================================================================
SOLUTION · LeetCode 1004 · Max Consecutive Ones III                     [Medium]
https://leetcode.com/problems/max-consecutive-ones-iii/
================================================================================

THE CORE IDEA
-------------
Do the reframe first — it is the whole problem:

    "flip at most k zeros to maximise a run of ones"
                        ==
    "find the longest subarray containing at most k zeros"

Flipping is a red herring. For ANY subarray you pick, making it all-ones costs
exactly (number of zeros inside) flips, and spending your budget anywhere else
is wasted. So there is no choice to make about WHICH zeros to flip — only about
where the subarray goes. That is a plain Shape-B window:

    l = zeros = best = 0
    for r, x in enumerate(nums):
        zeros += x == 0                       # ENTER
        while zeros > k:                      # RESTORE
            zeros -= nums[l] == 0
            l += 1
        best = max(best, r - l + 1)           # RECORD
    return best

O(n) time, O(1) space.

Whenever a problem describes an OPERATION you may perform, ask whether the
operation is actually a constraint in disguise. "Flip k zeros", "replace k
characters" (LC 424), "delete one element" (LC 1493), "swap k adjacent
pairs" — all of them reduce to "a window with at most k violations", and
none of them requires you to decide which elements to change.


THE GENERAL FORM — worth writing it this way in your head
---------------------------------------------------------
    LONGEST SUBARRAY WITH AT MOST k ELEMENTS FAILING PREDICATE P

        violations = 0
        for r, x in enumerate(a):
            violations += not P(x)
            while violations > k:
                violations -= not P(a[l]); l += 1
            best = max(best, r - l + 1)

Here P(x) is `x == 1`. Nothing in the argument used the fact that the array is
binary — swap P and you have LC 2401, LC 2024, LC 1493 and half a dozen others.


WHY THE WINDOW IS LEGAL
-----------------------
"contains at most k zeros" is HEREDITARY: dropping elements can only lower the
zero count. Contrapositive — if a window has too many zeros, so does every
wider window containing it. Therefore shrinking from the left is the only
possible repair and every left endpoint passed is eliminated forever, which is
why `l` never backtracks and the pass is O(n) by amortization.

⚠️  Contrast with LC 209 (problem 008 in this folder), where the analogous
    claim needs `nums[i] >= 0` to hold. Here the counter is a COUNT, and counts
    are non-negative by construction, so the property is automatic. That is why
    "at most k violations" windows never have a sign caveat.


================================================================================
THE NEVER-SHRINKING WINDOW — Shape D
================================================================================
Because the question asks only for the LENGTH of the best window, there is a
sharper version:

    l = zeros = 0
    for r, x in enumerate(nums):
        zeros += x == 0
        if zeros > k:                  # `if`, NOT `while`
            zeros -= nums[l] == 0
            l += 1
    return len(nums) - l               # the FINAL width. No max() anywhere.

WHY IT WORKS. Consider the window width `w = r - l + 1` after each iteration:

    * If the window was still valid after r entered, `l` did not move, so the
      width grew by exactly 1.
    * If it was invalid, `l` advanced by exactly 1 as well — one element in,
      one element out — so the width is UNCHANGED.

The width therefore NEVER DECREASES. It is a monotone non-decreasing sequence
that increases only on steps that ended valid. So its final value equals the
largest valid width ever reached, and `len(nums) - l` is the answer.

⚠️  The window at the END may itself be INVALID (it can contain more than k
    zeros). That is not a bug and not a contradiction. The claim is not "the
    final window is a valid answer"; it is "the final WIDTH equals the maximum
    valid width", and an invalid window of width w is simply carrying forward
    the memory of a valid window of width w that occurred earlier. The demo at
    the bottom of this file prints exactly such a run.

WHEN YOU MAY USE IT:
    ✅ the answer is a maximal LENGTH
    ✗  you must return the subarray, its indices, or a COUNT of valid windows
       — then you need the honest `while` version, whose window is always valid

Both are O(n). The `while` version is easier to defend; the `if` version is
what makes LC 424 elegant. Know both, and know which question each answers.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(nums)

    Approach                        Time      Space  Note
    ------------------------------  --------  -----  -----------------------
    Every subarray, count zeros     O(n^3)    O(1)   or O(n^2) if incremental
    Extend from every start, break  O(n^2)    O(1)   the natural brute force
    Prefix sums + binary search     O(n logn) O(n)   works; needlessly slow
    Window (`while`) ✅             O(n)      O(1)   window always valid
    Window (`if`, never shrinks) ✅ O(n)      O(1)   fewer ops, length only

    ⚠️  The `if` version does strictly fewer operations than the `while`
        version — `l` advances at most once per iteration rather than
        potentially many times — but both are O(n) overall, so this is a
        constant factor, not a complexity win. Measured at the bottom.

    ⚠️  Prefix sums + binary search on the answer is a real alternative worth
        naming (find the largest w such that some window of width w has <= k
        zeros; the predicate is monotone in w). O(n log n) — mention it, then
        say the window gets it in O(n) without the search.


================================================================================
EDGE CASES
================================================================================
    k = 0            No flips allowed. The answer is the longest EXISTING run
                     of ones. The window still works: any zero entering makes
                     zeros = 1 > 0, and `l` is pushed past it. Test [1,0,1] -> 1.

    k = 0, no ones   [0,0,0,0] -> 0. The window is repeatedly emptied; `best`
                     must be able to stay at 0. Watch for `best` initialised
                     to 1 or to `nums[0]`.

    k >= zero count  The window never breaks and the answer is n. Test
                     [0,0,0] with k=3 (exactly enough) and k=5 (more than
                     enough) — both give 3.

    all ones         [1]*10, k=3 -> 10. The budget is never spent; the `while`
                     never fires.

    n = 1            [0] with k=1 -> 1; [1] with k=0 -> 1. Exercises
                     `r - l + 1` at r = l = 0.

    best at the ends [0,1,1,1,0,0] k=1 -> 4 (starts at index 0)
                     [0,0,1,1,1,0] k=1 -> 4 (ends at the last index)
                     Together they catch loops that skip the first or last
                     window.


================================================================================
COMMON MISTAKES
================================================================================
1. Trying to DECIDE which zeros to flip — greedy over the zeros, DP over the
   flip budget, etc. The reframe removes the decision entirely. If you find
   yourself writing a nested loop over "which zeros", stop and re-read.

2. `r - l` instead of `r - l + 1`.

3. Recording before restoring, so `best` can be set from a window with more
   than k zeros.

4. Decrementing the wrong element on shrink: `zeros -= nums[r] == 0` instead of
   `nums[l] == 0`.

5. Crossing the two templates in the WRONG direction: `while`-shrink combined
   with Shape D's "return the final width". A full shrink makes the width
   non-monotone, so the last width is not the maximum. [1,0,0,0,0] with k=1
   returns 1 instead of 2.
   (The other cross — `if`-shrink WITH `max()` — is harmless: the width is
   monotone, so its max IS its final value. Redundant, not wrong. Know which
   direction is the bug.)

6. Resetting `zeros = 0` and `l = r` when the budget is exceeded. That throws
   away the valid tail of the window and gives short answers.

7. Reporting O(n^2) because of the nested `while`. Amortization: `l` advances
   at most n times TOTAL.

8. Special-casing k = 0. It needs no special case; if yours does, the template
   is wrong somewhere.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the actual subarray (or its indices), not just the length.
A: Use the `while` version — its window is always valid — and track
   `(best_l, best_r)` when you improve. The never-shrink version cannot answer
   this, because its final window may be invalid.

Q: Longest run after flipping at most k zeros, in a CIRCULAR array?
A: Concatenate the array with itself and cap the window width at n. The zero
   count logic is unchanged.

Q: What if you may also flip ones to zeros — maximise the longest run of EITHER
   value (LC 2024, "maximum consecutive answers")?
A: Run the same window twice: once counting 0s as violations, once counting 1s,
   and take the max. Two O(n) passes. Or maintain both counters in one pass.

Q: Exactly k flips instead of at most k?
A: "At most" is monotone in k, so if there are at least k zeros the answers
   coincide (spend the whole budget inside the best window). If the array has
   fewer than k zeros the answer is still n — you can waste flips by flipping
   a 1 to 0 and back only if the problem allows it; otherwise say the
   constraint is unsatisfiable. Nail down what "exactly" means before coding.

Q: Delete AT MOST ONE element and maximise the run of ones (LC 1493)?
A: This problem with k = 1, minus one from the answer (the deleted element does
   not count towards the run), with the special case of an all-ones array.
   Worth doing right after this one.

Q: The array is a stream.
A: The `while` version needs `nums[l]`, i.e. random access to the window's
   left end. Buffer the window in a deque and you are online in O(window)
   memory.

Q: Prove the `if`-only version is correct.
A: The width argument above: the width never decreases, and it increases only
   on iterations that ended valid. Being able to give that in three sentences
   is the point of the follow-up.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 485  Max Consecutive Ones          — this problem with k = 0
    LC 487  Max Consecutive Ones II       — this problem with k = 1
    LC 424  Longest Repeating Char Repl   — problem 007; same shape, harder
                                            validity test
    LC 1493 Longest Subarray of 1s After  — k = 1, answer minus one
            Deleting One Element
    LC 2024 Maximize the Confusion of an  — run it twice (T and F)
            Exam
    LC 2401 Longest Nice Subarray         — same template, bitmask validity
    LC 3   Longest Substring No Repeat    — problem 005; the same template
    LC 209  Minimum Size Subarray Sum     — problem 008; the SHORTEST mirror
================================================================================
"""

import random
import time
from typing import List, Tuple


class Solution:
    def longestOnes(self, nums: List[int], k: int) -> int:
        """Shape B: longest window with at most k zeros. O(n) time, O(1) space.

        The window is ALWAYS valid when `best` is updated.
        """
        l = zeros = best = 0
        for r, x in enumerate(nums):
            zeros += x == 0                       # ENTER
            while zeros > k:                      # RESTORE
                zeros -= nums[l] == 0
                l += 1
            best = max(best, r - l + 1)           # RECORD
        return best

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def longestOnes_never_shrink(self, nums: List[int], k: int) -> int:
        """Shape D: the window never shrinks, so the FINAL width is the answer.

        No max(). The window may end up invalid — that is fine, see the module
        docstring. Length-only; cannot report the subarray.
        """
        l = zeros = 0
        for r, x in enumerate(nums):
            zeros += x == 0
            if zeros > k:                         # `if`, not `while`
                zeros -= nums[l] == 0
                l += 1                            # slide, keeping the width
        return len(nums) - l

    def longestOnes_bounds(self, nums: List[int], k: int) -> Tuple[int, int, int]:
        """Follow-up: return (length, l, r) of a best window. Needs the
        `while` version, because its window is always valid."""
        l = zeros = best = 0
        bl = br = -1
        for r, x in enumerate(nums):
            zeros += x == 0
            while zeros > k:
                zeros -= nums[l] == 0
                l += 1
            if r - l + 1 > best:                  # `>` keeps the EARLIEST best
                best, bl, br = r - l + 1, l, r
        return best, bl, br

    def longestOnes_binary_search(self, nums: List[int], k: int) -> int:
        """Prefix sums + binary search on the ANSWER WIDTH. O(n log n), O(n).

        Feasibility is monotone in the width w: if some window of width w has
        <= k zeros, then some window of width w-1 does too.
        """
        n = len(nums)
        pre = [0] * (n + 1)
        for i, x in enumerate(nums):
            pre[i + 1] = pre[i] + (x == 0)

        def feasible(w: int) -> bool:
            return any(pre[i + w] - pre[i] <= k for i in range(n - w + 1))

        lo, hi, ans = 1, n, 0
        while lo <= hi:
            mid = (lo + hi) // 2
            if feasible(mid):
                ans, lo = mid, mid + 1
            else:
                hi = mid - 1
        return ans

    def longestOnes_brute(self, nums: List[int], k: int) -> int:
        """O(n^2) oracle: extend from every start until the budget is gone."""
        best = 0
        for i in range(len(nums)):
            zeros = 0
            for j in range(i, len(nums)):
                zeros += nums[j] == 0
                if zeros > k:
                    break
                best = max(best, j - i + 1)
        return best

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def longestOnes_if_with_max(self, nums: List[int], k: int) -> int:
        """CORRECT, but the max() is REDUNDANT.

        `if`-shrink makes the width monotone non-decreasing, and the maximum of
        a non-decreasing sequence is its LAST value — which is exactly what
        `longestOnes_never_shrink` returns. So this agrees with it always. It
        looks like it should overcount (it does measure windows that are
        momentarily invalid) but such a window's width is only ever equal to a
        valid width already achieved, so the max is never inflated.
        """
        l = zeros = best = 0
        for r, x in enumerate(nums):
            zeros += x == 0
            if zeros > k:
                zeros -= nums[l] == 0
                l += 1
            best = max(best, r - l + 1)
        return best

    def longestOnes_while_final_width(self, nums: List[int], k: int) -> int:
        """✗ BROKEN ON PURPOSE — the OTHER cross of the two templates:
        `while`-shrink (so the width CAN decrease) with Shape D's
        "return the final width" ending.

        With a full shrink the width is no longer monotone, so the last width
        is not the maximum. [1,0,0,0,0], k=1 -> returns 1, answer is 2.
        """
        l = zeros = 0
        for r, x in enumerate(nums):
            zeros += x == 0
            while zeros > k:
                zeros -= nums[l] == 0
                l += 1
        return len(nums) - l

    def longestOnes_reset(self, nums: List[int], k: int) -> int:
        """✗ BROKEN ON PURPOSE — restarts the window instead of shrinking,
        discarding the still-valid tail."""
        l = zeros = best = 0
        for r, x in enumerate(nums):
            zeros += x == 0
            if zeros > k:
                l, zeros = r + 1, 0          # throw the whole window away
            else:
                best = max(best, r - l + 1)
        return best


# ==============================================================================
# TESTS — run:  python 006_max_consecutive_ones_iii_solution.py
# ==============================================================================
CASES = [
    ([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2),
    ([0, 0, 1, 1, 0, 0, 1, 1, 1, 0, 1, 1, 0, 0, 0, 1, 1, 1, 1], 3),
    ([0, 0, 0, 0], 0), ([1, 1, 1], 0), ([1, 0, 1], 0), ([0], 1), ([1], 0),
    ([0, 0, 0], 3), ([0, 0, 0], 5), ([1, 0, 0, 1, 1, 0, 1], 2),
    ([0, 1, 1, 1, 0, 0], 1), ([0, 0, 1, 1, 1, 0], 1),
    ([1, 1, 0, 0, 0, 0, 1, 1], 2), ([1] * 10, 3),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("while-shrink (Shape B)", sol.longestOnes),
        ("never-shrink (Shape D)", sol.longestOnes_never_shrink),
        ("binary search on width", sol.longestOnes_binary_search),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(a), k) == sol.longestOnes_brute(a, k) for a, k in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # the bounds variant must return a window that is both the right length
    # AND actually valid
    ok = True
    for a, k in CASES:
        ln, bl, br = sol.longestOnes_bounds(list(a), k)
        if ln != sol.longestOnes_brute(a, k):
            ok = False
        if ln > 0 and (br - bl + 1 != ln or sum(1 for x in a[bl:br+1] if x == 0) > k):
            ok = False
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  bounds variant (right length AND a "
          f"genuinely valid window)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(1004)
    trials, mismatches = 5000, 0
    for _ in range(trials):
        n = random.randint(1, 16)
        arr = [random.randint(0, 1) for _ in range(n)]
        k = random.randint(0, n)
        want = sol.longestOnes_brute(arr, k)
        for _, fn in impls:
            if fn(list(arr), k) != want:
                mismatches += 1
    print(f"  {trials} random (array, k) x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced.
    # ----------------------------------------------------------------------
    nums, k = [1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2
    print(f"\n--- Shape B on {nums}, k={k} ---")
    print(f"  {'r':>2} {'x':>2} {'zeros':>6} {'shrank':>7} {'l':>2}"
          f" {'window':>26} {'len':>4} {'best':>5}")
    l = zeros = best = 0
    for r, x in enumerate(nums):
        zeros += x == 0
        moved = 0
        while zeros > k:
            zeros -= nums[l] == 0
            l += 1
            moved += 1
        best = max(best, r - l + 1)
        print(f"  {r:>2} {x:>2} {zeros:>6} {moved or '-':>7} {l:>2} "
              f"{str(nums[l:r+1]):>26} {r - l + 1:>4} {best:>5}")

    # ----------------------------------------------------------------------
    # Shape D: the width never decreases, and the final window may be invalid.
    # ----------------------------------------------------------------------
    print(f"\n--- Shape D (never shrinks) on the same input ---")
    print(f"  {'r':>2} {'x':>2} {'zeros':>6} {'l':>2} {'width':>6}"
          f" {'valid?':>7}  note")
    l = zeros = 0
    prev_w = 0
    for r, x in enumerate(nums):
        zeros += x == 0
        note = ""
        if zeros > k:
            zeros -= nums[l] == 0
            l += 1
            note = "slid (width held)"
        else:
            note = "grew"
        w = r - l + 1
        assert w >= prev_w, "width DECREASED — the Shape D argument is broken"
        prev_w = w
        print(f"  {r:>2} {x:>2} {zeros:>6} {l:>2} {w:>6} "
              f"{str(zeros <= k):>7}  {note}")
    print(f"  final width = len - l = {len(nums)} - {l} = {len(nums) - l}")
    print("  Look at r=5..7: the window is INVALID there (3 zeros > k=2) and is")
    print("  still measured. That is not a bug — an invalid window of width w is")
    print("  only carrying forward the memory of a VALID window of width w seen")
    print("  earlier, so the width is never inflated.")
    print("  It can also end invalid — [1,1,1,0,0,0] with k=2 does:")
    l2 = z2 = 0
    probe = [1, 1, 1, 0, 0, 0]
    for r, x in enumerate(probe):
        z2 += x == 0
        if z2 > 2:
            z2 -= probe[l2] == 0
            l2 += 1
    print(f"    final window {probe[l2:]} has {z2} zeros > k=2, width "
          f"{len(probe) - l2} — and {len(probe) - l2} IS the right answer.")

    # ----------------------------------------------------------------------
    # ⚠️  Mixing the two templates.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  crossing the two templates: only ONE direction is a bug ---")
    print(f"  {'input':<34} {'k':>2} {'correct':>8} {'if+max':>7} "
          f"{'while+final':>12} {'reset':>6}")
    for a, k in ([1, 1, 1, 0, 0, 0, 1, 1, 1, 1, 0], 2), ([0, 0, 0, 0], 0), \
                ([1, 0, 1], 0), ([1, 0, 0, 0, 0], 1), ([0, 0, 1, 1, 1, 0], 1):
        print(f"  {str(a):<34} {k:>2} {sol.longestOnes(list(a), k):>8} "
              f"{sol.longestOnes_if_with_max(list(a), k):>7} "
              f"{sol.longestOnes_while_final_width(list(a), k):>12} "
              f"{sol.longestOnes_reset(list(a), k):>6}")
    print("  `if + max`      : CORRECT but redundant. The width is monotone, so")
    print("                    its running max IS its final value.")
    print("  `while + final` : ✗ BROKEN. A full shrink makes the width")
    print("                    non-monotone, so the last width is not the max.")
    print("  `reset`         : ✗ BROKEN. Throws away the still-valid tail.")
    random.seed(1)
    d_ifmax = d_whilefinal = 0
    for _ in range(20_000):
        n = random.randint(1, 12)
        a = [random.randint(0, 1) for _ in range(n)]
        k = random.randint(0, n)
        w = sol.longestOnes_brute(a, k)
        d_ifmax += sol.longestOnes_if_with_max(list(a), k) != w
        d_whilefinal += sol.longestOnes_while_final_width(list(a), k) != w
    print(f"  over 20000 random inputs:  if+max {d_ifmax} disagreements, "
          f"while+final {d_whilefinal}")

    # ----------------------------------------------------------------------
    # The reframe: you never decide WHICH zeros to flip.
    # ----------------------------------------------------------------------
    print("\n--- the reframe, verified: 'flip k zeros' == 'window with k zeros' ---")
    random.seed(4)
    bad = 0
    for _ in range(300):
        n = random.randint(1, 11)
        arr = [random.randint(0, 1) for _ in range(n)]
        k = random.randint(0, 3)
        # exhaustive: try every subset of zero-positions of size <= k, flip it,
        # and measure the longest run of ones.
        zero_pos = [i for i, x in enumerate(arr) if x == 0]
        best_exhaustive = 0
        from itertools import combinations
        for size in range(min(k, len(zero_pos)) + 1):
            for combo in combinations(zero_pos, size):
                flipped = list(arr)
                for i in combo:
                    flipped[i] = 1
                run = cur = 0
                for x in flipped:
                    cur = cur + 1 if x == 1 else 0
                    run = max(run, cur)
                best_exhaustive = max(best_exhaustive, run)
        if best_exhaustive != sol.longestOnes(list(arr), k):
            bad += 1
    print(f"  300 random arrays, brute-forcing EVERY choice of which zeros to")
    print(f"  flip and comparing against the window: {bad} disagreements.")
    print("  The choice never mattered — which is why there is no DP here.")
    all_ok &= (bad == 0)

    # ----------------------------------------------------------------------
    # Shape B vs Shape D: operation counts.
    # ----------------------------------------------------------------------
    print("\n--- how much work each shape does ---")

    def count_moves(nums, k, never_shrink):
        l = zeros = moves = 0
        for r, x in enumerate(nums):
            zeros += x == 0
            if never_shrink:
                if zeros > k:
                    zeros -= nums[l] == 0; l += 1; moves += 1
            else:
                while zeros > k:
                    zeros -= nums[l] == 0; l += 1; moves += 1
        return moves

    random.seed(6)
    print(f"  {'input shape':<28} {'n':>7} {'while-shrink':>13} {'never-shrink':>13}")
    for label, arr, k in (
        ("mostly ones", [1 if random.random() < .9 else 0 for _ in range(20_000)], 5),
        ("half and half", [random.randint(0, 1) for _ in range(20_000)], 5),
        ("mostly zeros", [1 if random.random() < .1 else 0 for _ in range(20_000)], 5),
    ):
        print(f"  {label:<28} {len(arr):>7} "
              f"{count_moves(arr, k, False):>13} {count_moves(arr, k, True):>13}")
    print("  Both are bounded by n — that is the amortization argument. The")
    print("  never-shrink form moves `l` at most ONCE per step, so it does")
    print("  slightly less work, but the complexity is identical.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2) vs O(n log n).
    # ----------------------------------------------------------------------
    print("\n--- window vs binary search vs brute force ---")
    print(f"  {'n':>7} {'window O(n)':>13} {'bsearch O(nlogn)':>17} {'brute O(n^2)':>14}")
    random.seed(0)
    for n in (2_000, 4_000, 8_000):
        arr = [random.randint(0, 1) for _ in range(n)]
        k = n // 20
        t0 = time.perf_counter(); sol.longestOnes(arr, k)
        t1 = time.perf_counter(); sol.longestOnes_binary_search(arr, k)
        t2 = time.perf_counter(); sol.longestOnes_brute(arr, k)
        t3 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>11.1f}ms {(t2 - t1) * 1000:>15.1f}ms "
              f"{(t3 - t2) * 1000:>12.1f}ms")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
