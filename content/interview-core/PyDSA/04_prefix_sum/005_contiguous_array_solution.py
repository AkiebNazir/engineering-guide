"""
================================================================================
SOLUTION · LeetCode 525 · Contiguous Array                             [Medium]
https://leetcode.com/problems/contiguous-array/
================================================================================

THE CORE IDEA
--------------
Map 0 -> -1 and 1 -> +1. A subarray has equal 0s and 1s exactly when its
transformed sum is 0, which — same prefix-sum algebra as problem 004 — means
two EQUAL prefix values bracket it:

    prefix[r+1] - prefix[l] == 0   <=>   prefix[r+1] == prefix[l]

Walk the array keeping a running transformed sum and a hashmap from prefix
value to the EARLIEST index it was seen at. Every time the running value
recurs, the span back to its first occurrence is a candidate answer:

    seen = {0: -1}                          # sentinel: empty prefix at index -1
    running = best = 0
    for i, x in enumerate(nums):
        running += 1 if x == 1 else -1
        if running in seen:
            best = max(best, i - seen[running])   # pair with the FIRST occurrence
        else:
            seen[running] = i                     # record ONLY the first time

O(n) time, O(n) space. This is Variant B ("first-index map") from the topic
guide §1.4 — the opposite tool from problem 004's counting map, because this
problem wants the longest span, not a count, and the widest span always comes
from pairing with the EARLIEST occurrence of a repeated prefix value.


================================================================================
WHY THIS IS NOT A SLIDING WINDOW, EVEN THOUGH THE ALPHABET IS {0, 1}
================================================================================
It's tempting to think "only two values, must be a window." But the
condition "equal count of 0s and 1s" is not monotone: adding a 0 to the
window can only ever push the balance toward 0s, and adding a 1 can only
push it toward 1s — there is no single direction to shrink that is
guaranteed to restore balance, because whether you're over on 0s or over on
1s changes as you scan. Topic guide §1.1's rule applies here even without
literal negative numbers: the underlying TRANSFORMED values (-1, +1) are
signed, and it's the transform's sign — not the raw input's sign — that
determines whether a hashmap is needed instead of a window.


================================================================================
⚠️  THE SEED BUG — seen = {0: -1}, and why -1 specifically (topic guide §1.3)
================================================================================
Seed the map with `{0: -1}`: the empty prefix (before any element) has
transformed sum 0, and it is conceptually located at index -1 — one position
before the array. Without this sentinel, a balanced subarray that STARTS AT
INDEX 0 has no earlier occurrence of prefix value 0 to pair against, and it
is silently missed.

Trace nums = [0, 1] with the BROKEN `seen = {}` (no sentinel):

    i=0  x=0  running=-1   -1 not in seen -> seen={-1: 0}
    i=1  x=1  running=0    0 not in seen (!)  -> seen={-1: 0, 0: 1}
                            (correct behaviour needs 0 already in seen, at -1,
                             so the pair (i=-1, i=1) gives length 2 — the
                             whole array. Without the sentinel this pairing
                             never happens, and best stays 0.)

    No-sentinel answer: 0.  Correct answer: 2.

The demo below runs this live.

Note the seed value here is `-1` (an INDEX), while problem 004's seed value
was `1` (a COUNT) — same sentinel idea, different shape, because Variant A
counts occurrences and Variant B records positions. Confusing the two seed
shapes is a direct symptom of confusing the two variants (§1.4).


================================================================================
⚠️  THE #2 BUG IN THIS TOPIC — overwriting the first-seen index
================================================================================
Topic guide §1.4 calls this out by name: this problem needs the map to keep
ONLY the first index a prefix value was seen at. If you write
`seen[running] = i` unconditionally (no `if running in seen: ... else: ...`
guard), every later occurrence of the same prefix value overwrites the
earlier, smaller index — the map "forgets" the earliest occurrence and can
only pair against the MOST RECENT one, which always gives a SHORTER or EQUAL
span than the true answer, sometimes strictly shorter.

Construct an input where this is visible: nums = [0, 0, 1, 0, 0, 1, 1, 1]

    transformed = [-1, -1, 1, -1, -1, 1, 1, 1]
    running:        -1  -2  -1  -2  -3  -2  -1   0

    prefix value -1 occurs at indices 0, 2, 5   (running after that index)
    prefix value -2 occurs at indices 1, 3
    prefix value  0 occurs at index 7 (and the sentinel, index -1)

    CORRECT (keep first occurrence of -1, which is index 0):
        at i=5, running=-1, first seen at i=0 -> span = 5 - 0 = 5
        at i=7, running=0,  first seen at -1  -> span = 7 - (-1) = 8   <- best

    BROKEN (overwrite -1's index every time it recurs, so by i=5 the map
    thinks -1 was last seen at i=2, not i=0):
        at i=5, running=-1, "seen" at i=2 (overwritten!) -> span = 5-2 = 3
        at i=7, running=0, still pairs correctly with sentinel -> span = 8

    In THIS specific array the final answer (8, the whole array) survives
    because the winning pair (running=0) never gets overwritten — but the
    demo below constructs a case where the overwrite bug DOES change the
    final reported answer, using a prefix value that only reaches its
    maximum span through the EARLIEST occurrence and nothing later beats it.


================================================================================
STEP BY STEP TRACE
================================================================================
nums = [0, 1, 0, 0, 1, 1, 0]

    idx   nums[i]  transformed  running  seen before this step   action
    -     -        -            0        {0: -1}                  (sentinel)
    0     0        -1           -1       {0: -1}                  new -> seen[-1]=0
    1     1        +1            0        {0:-1, -1:0}             HIT seen[0]=-1 -> span=1-(-1)=2, best=2
    2     0        -1           -1       {0:-1, -1:0}             HIT seen[-1]=0  -> span=2-0=2,   best=2
    3     0        -1           -2       {0:-1, -1:0}             new -> seen[-2]=3
    4     1        +1           -1       {..., -2:3}              HIT seen[-1]=0  -> span=4-0=4,   best=4
    5     1        +1            0        {..., -2:3}              HIT seen[0]=-1  -> span=5-(-1)=6, best=6
    6     0        -1           -1       {..., -2:3}              HIT seen[-1]=0  -> span=6-0=6,   best=6

    Final best: 6, matching the problem's own example. The winning pair is
    (index -1 sentinel, index 5) via running=0 -> subarray nums[0..5],
    six elements, three 0s and three 1s.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                            Time    Space   Mutates input?  Note
    -----------------------------------  ------  ------  ---------------  ----------------
    Every (l, r), count 0s/1s directly   O(n^2)  O(1)    no               brute force here
    Prefix array + nested equal search    O(n^2)  O(n)    no               array alone doesn't help
    Transform + hashmap, first-index ✅  O(n)    O(n)    no               the answer
    Transform + hashmap, no sentinel     O(n)    O(n)    no               ✗ WRONG — misses index-0 spans
    Transform + hashmap, overwrite bug   O(n)    O(n)    no               ✗ WRONG — shorter spans


================================================================================
EDGE CASES
================================================================================
    [0]                  -> 0   Single element, never balanced. Minimum length.
    [1]                  -> 0   Same, other value.
    [0,0,0]              -> 0   All same value: never balanced anywhere.
    [1,1,1]              -> 0   Same, other value.
    [0,1]                -> 2   Smallest possible balanced subarray, and it
                                 IS the whole array — exercises the sentinel
                                 directly (pairs with index -1).
    [1,0,1,0,1,0]         -> 6   Alternating: the whole array balances, and
                                 also many smaller balanced subarrays exist —
                                 the algorithm must find the LONGEST, not just
                                 any.
    [1,0,0,1,0,0,1,1]     -> 6   Best subarray is NOT the whole array and does
                                 NOT start at index 0 — catches any solution
                                 that anchors incorrectly at the start.
    Answer of 0 is legal   the whole point of testing all-0 / all-1 arrays:
                                 there is no requirement that SOME balanced
                                 subarray exists beyond the trivial empty one,
                                 which does not count (subarrays are non-empty).


================================================================================
COMMON MISTAKES
================================================================================
1. `seen = {}` instead of `seen = {0: -1}`. Misses every balanced subarray
   that starts at index 0. See the seed-bug trace above.

2. Using `seen[running] = i` unconditionally instead of only on first sight.
   Overwrites the earliest occurrence and returns a shorter span than the
   true answer. See the "#2 bug in this topic" section above.

3. Using a COUNTING map (problem 004's tool, Variant A) here instead of a
   first-index map (Variant B). A counting map answers "how many," not "how
   far back" — it has no notion of index at all, so it cannot produce a
   length.

4. Recomputing `count of zeros` and `count of ones` per subarray with nested
   loops — correct but O(n^2), throwing away the whole benefit of the prefix
   transform.

5. Forgetting the `+1 if x == 1 else -1` transform and instead trying to
   track `zeros - ones` as two separate counters without collapsing them
   into one running value — works but is needlessly more state to manage and
   easy to get the sign backwards on.

6. `i - seen[running] + 1` instead of `i - seen[running]`. The stored index
   is the LEFT ENDPOINT'S prefix (i.e., "before" the subarray starts), so the
   +1 is already implicitly accounted for by prefix-vs-element indexing — see
   the trace above, or problem 004's `prefix[r+1] - prefix[l]` derivation.

7. Assuming the answer must be even. It always IS (equal 0s and 1s implies an
   even total), but computing it via `len // 2 * 2` or similar special-casing
   is unnecessary — the algorithm naturally produces an even number without
   help.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the actual subarray, not just its length.
A: Track `best_l, best_r` alongside `best` (updating them whenever `best`
   updates), then slice once at the end: `nums[best_l:best_r+1]`.

Q: What if the array had three symbols instead of two (e.g. -1, 0, +1) and
   you wanted equal counts of all three?
A: A single running sum no longer works — one number can't capture two
   independent balances. Track two running counts (e.g. count(sym A) -
   count(sym B) and count(sym B) - count(sym C)) and key the map on the PAIR
   `(diff1, diff2)`. Same first-index-map idea, 2D key.

Q: Count how many subarrays are balanced, instead of finding the longest?
A: Switch from Variant B back to Variant A (problem 004's counting map):
   `seen = {0: 1}`, and accumulate `count += seen.get(running, 0)` each step
   instead of tracking a max span.

Q: What's the relationship between this problem and LC 560?
A: Same transform-to-prefix-sum trick, different map shape. LC 560 counts
   (Variant A), this problem finds a longest span (Variant B) — see topic
   guide §1.4 for the general rule of which variant a problem wants.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 560  Subarray Sum Equals K            — Variant A, counting map
                                                (problem 004 here)
    LC 523  Continuous Subarray Sum          — mod-K + first-index map + a
                                                length-2 trap (problem 008)
    LC 1004 Max Consecutive Ones III         — a genuine sliding window (the
                                                condition IS monotone there)
    LC 325  Maximum Size Subarray Sum Equals k — the general (non-binary)
                                                version of this exact pattern
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def findMaxLength(self, nums: List[int]) -> int:
        """Transform 0->-1, 1->+1; prefix sum + first-index hashmap.
        O(n) time, O(n) space. The answer. See THE CORE IDEA above."""
        seen = {0: -1}                              # sentinel: empty prefix at index -1
        running = best = 0
        for i, x in enumerate(nums):
            running += 1 if x == 1 else -1
            if running in seen:
                best = max(best, i - seen[running])  # pair with FIRST occurrence
            else:
                seen[running] = i                     # record ONLY the first time
        return best

    # ------------------------------------------------------------------
    # Alternatives / oracles.
    # ------------------------------------------------------------------
    def findMaxLength_brute(self, nums: List[int]) -> int:
        """O(n^2) oracle: for every (l, r), count 0s and 1s directly."""
        n = len(nums)
        best = 0
        for i in range(n):
            zeros = ones = 0
            for j in range(i, n):
                if nums[j] == 0:
                    zeros += 1
                else:
                    ones += 1
                if zeros == ones:
                    best = max(best, j - i + 1)
        return best

    # ------------------------------------------------------------------
    # Deliberate breakage.
    # ------------------------------------------------------------------
    def findMaxLength_no_sentinel(self, nums: List[int]) -> int:
        """✗ BROKEN ON PURPOSE — seen = {} instead of {0: -1}. Misses every
        balanced subarray that starts at index 0."""
        seen = {}                                    # NO sentinel
        running = best = 0
        for i, x in enumerate(nums):
            running += 1 if x == 1 else -1
            if running in seen:
                best = max(best, i - seen[running])
            else:
                seen[running] = i
        return best

    def findMaxLength_overwrite(self, nums: List[int]) -> int:
        """✗ BROKEN ON PURPOSE — overwrites the first-seen index on every
        recurrence instead of keeping only the earliest. Pairs against a
        LATER occurrence and can return a shorter-than-true span."""
        seen = {0: -1}
        running = best = 0
        for i, x in enumerate(nums):
            running += 1 if x == 1 else -1
            if running in seen:
                best = max(best, i - seen[running])
            seen[running] = i                          # unconditional overwrite (BUG)
        return best


# ==============================================================================
# TESTS — run:  python 005_contiguous_array_solution.py
# ==============================================================================
CASES = [
    [0, 1], [0, 1, 0], [0, 1, 0, 0, 1, 1, 0], [0], [1], [0, 0, 0], [1, 1, 1],
    [0, 1, 1, 0], [1, 0, 1, 0, 1, 0], [1, 1, 0, 0, 1, 0, 1, 1],
    [1, 1, 1, 0, 0, 0], [0, 0, 1, 0, 0, 1, 1, 1], [1, 0, 0, 1, 0, 0, 1, 1],
    [1, 1, 0, 1, 1, 1, 0, 0, 1, 1],
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    print("--- correctness: O(n) prefix+hashmap vs O(n^2) direct-count oracle ---")
    for nums in CASES:
        want = sol.findMaxLength_brute(nums)
        got = sol.findMaxLength(nums)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  nums={nums!r:<38} -> {got}  (want {want})")

    # ----------------------------------------------------------------------
    # ⚠️  The seed-sentinel bug, demonstrated live.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  seen={} vs seen={0:-1}: the sentinel bug (topic guide §1.3) ---")
    print(f"  {'input':<24} {'correct':>8} {'no sentinel':>12}  ok?")
    sentinel_mismatch = False
    for nums in ([0, 1], [1, 0, 1, 0, 1, 0], [0, 1, 1, 0], [1, 1, 0, 0]):
        good = sol.findMaxLength(nums)
        bad = sol.findMaxLength_no_sentinel(nums)
        mismatch = good != bad
        sentinel_mismatch |= mismatch
        print(f"  {str(nums):<24} {good:>8} {bad:>12}  "
              f"{'yes' if not mismatch else 'NO  <- missed index-0 span'}")
    print(f"  sentinel bug reproduced: {sentinel_mismatch}")
    all_ok &= sentinel_mismatch

    print("\n  [0,1] traced with NO sentinel:")
    nums = [0, 1]
    seen, running, best = {}, 0, 0
    print(f"  {'i':>2} {'x':>3} {'running':>8} {'in seen?':>9} {'best':>5}")
    for i, x in enumerate(nums):
        running += 1 if x == 1 else -1
        hit = running in seen
        if hit:
            best = max(best, i - seen[running])
        else:
            seen[running] = i
        print(f"  {i:>2} {x:>3} {running:>8} {str(hit):>9} {best:>5}")
    print(f"  no-sentinel answer: {best}  (correct answer: {sol.findMaxLength(nums)})")

    # ----------------------------------------------------------------------
    # ⚠️  The overwrite bug, demonstrated live with a case that flips the
    #     FINAL answer (not just an intermediate span).
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  overwriting the first-seen index (topic guide §1.4, bug #2) ---")
    # Constructed so the overwrite bug strictly shortens the reported answer:
    # after a long run back to -1's ORIGINAL index (0), a later recurrence of
    # -1 at index 2 overwrites it, so the true widest pairing (0 -> 7) is lost
    # and the broken version can only find a shorter one.
    overwrite_case = [0, 0, 1, 0, 1, 1, 1, 0]
    print(f"  worked example: nums = {overwrite_case}")
    print(f"  {'input':<28} {'correct':>8} {'overwrite bug':>14}  ok?")
    overwrite_mismatch = False
    shown = 0
    test_inputs = [overwrite_case, [0, 0, 1, 1, 0, 1, 0, 0], [0, 1, 0, 1, 1, 0]]
    random.seed(42)
    for _ in range(200):
        n = random.randint(4, 12)
        test_inputs.append([random.randint(0, 1) for _ in range(n)])
    for nums in test_inputs:
        good = sol.findMaxLength(nums)
        bad = sol.findMaxLength_overwrite(nums)
        mismatch = good != bad
        overwrite_mismatch |= mismatch
        if mismatch and shown < 5:                 # only print a handful, not all
            print(f"  {str(nums):<28} {good:>8} {bad:>14}  NO  <- shorter span, first index lost")
            shown += 1
    print(f"  ... ({sum(sol.findMaxLength(n) != sol.findMaxLength_overwrite(n) for n in test_inputs)}"
          f"/{len(test_inputs)} sampled inputs show the bug)")
    print(f"  overwrite bug reproduced: {overwrite_mismatch}")
    all_ok &= overwrite_mismatch

    # ----------------------------------------------------------------------
    # Step-by-step trace + brute-force cross-check side by side.
    # ----------------------------------------------------------------------
    text = [0, 1, 0, 0, 1, 1, 0]
    print(f"\n--- the running sum / map state over nums={text} ---")
    print(f"  {'i':>2} {'x':>3} {'Δ':>3} {'running':>8} {'hit?':>5} {'span':>6} {'best':>5}")
    seen, running, best = {0: -1}, 0, 0
    for i, x in enumerate(text):
        delta = 1 if x == 1 else -1
        running += delta
        hit = running in seen
        span = (i - seen[running]) if hit else 0
        if hit:
            best = max(best, span)
        else:
            seen[running] = i
        print(f"  {i:>2} {x:>3} {delta:>3} {running:>8} {str(hit):>5} {span:>6} {best:>5}")
    print(f"  final best: {best}  (brute force cross-check: {sol.findMaxLength_brute(text)})")

    # ----------------------------------------------------------------------
    # Randomised cross-check.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(11)
    trials, mismatches = 3000, 0
    for _ in range(trials):
        n = random.randint(1, 14)
        nums = [random.randint(0, 1) for _ in range(n)]
        if sol.findMaxLength(nums) != sol.findMaxLength_brute(nums):
            mismatches += 1
    print(f"  {trials} random binary arrays (length 1-14): {mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2) runtime demo.
    # ----------------------------------------------------------------------
    print("\n--- O(n) prefix+hashmap vs O(n^2) direct count: measured runtime ---")
    print(f"  {'n':>7} {'hashmap O(n)':>14} {'brute O(n^2)':>14} {'ratio':>8}")
    random.seed(1)
    for n in (500, 2_000, 8_000):
        nums = [random.randint(0, 1) for _ in range(n)]
        t0 = time.perf_counter(); sol.findMaxLength(nums)
        t1 = time.perf_counter(); sol.findMaxLength_brute(nums)
        t2 = time.perf_counter()
        hm_ms = (t1 - t0) * 1000
        br_ms = (t2 - t1) * 1000
        ratio = br_ms / hm_ms if hm_ms > 0 else float("inf")
        print(f"  {n:>7} {hm_ms:>12.2f}ms {br_ms:>12.2f}ms {ratio:>7.1f}x")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
