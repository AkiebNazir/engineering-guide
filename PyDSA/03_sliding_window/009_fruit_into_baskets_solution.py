"""
================================================================================
SOLUTION · LeetCode 904 · Fruit Into Baskets                            [Medium]
https://leetcode.com/problems/fruit-into-baskets/
================================================================================

THE CORE IDEA
-------------
Strip the story: two baskets each holding one type, picking contiguously to the
right, means

    THE LONGEST SUBARRAY WITH AT MOST 2 DISTINCT VALUES.

which is LC 340 with K = 2, and the Shape-B template with a frequency map:

    count = Counter()
    l = best = 0
    for r, f in enumerate(fruits):
        count[f] += 1                              # ENTER
        while len(count) > 2:                      # RESTORE
            count[fruits[l]] -= 1
            if count[fruits[l]] == 0:
                del count[fruits[l]]               # <- THE LINE
            l += 1
        best = max(best, r - l + 1)                # RECORD
    return best

O(n) time, O(1) space (the map holds at most 3 keys at any moment).

Write it with K as a parameter, not hard-coded to 2. "Two baskets" is data, not
algorithm — and the parameterised version IS LC 340, LC 159 and LC 3 (K = the
alphabet size... no: K distinct is a different axis from "no repeats", but the
template is identical).


================================================================================
⚠️  `del` ON ZERO — the whole reason this problem is instructive
================================================================================
Your validity test is `len(count) > 2`, so `len(count)` MUST equal the number
of distinct values currently in the window. Decrementing a count to zero does
NOT remove the key:

    >>> c = Counter("aab")
    >>> c['b'] -= 1
    >>> c
    Counter({'a': 2, 'b': 0})
    >>> len(c)
    2                      # <- 'b' is gone from the window but still a key

So without the `del`, `len(count)` never decreases. And the consequence is
worse than a wrong answer:

    THE `while` LOOP CANNOT EXIT.

Once three distinct types have been seen, `len(count) > 2` stays true forever,
so `l` keeps advancing — past `r`, and then past the end of the array —
until `fruits[l]` raises IndexError. On [3,0,2,3,3,2,3] a version without the
`del` (and without an artificial `l < n` guard) crashes outright.

If you *do* add a guard like `while len(count) > 2 and l < n`, the crash turns
into silent wrongness: the window is emptied on every step and you get answers
far too small (measured in the test suite: wrong on ~39% of random inputs).

    THE INVARIANT, SAY IT OUT LOUD:
    `len(count)` IS THE NUMBER OF DISTINCT VALUES IN THE WINDOW.
    Anything that breaks that invariant breaks the loop's exit condition.

This is topic-guide §3.2 in its natural habitat, and the same `del` is required
in problems 013 (K distinct) and 015 (minimum window substring).


⚠️  AND THE OTHER HALF: `Counter` vs `defaultdict(int)`
--------------------------------------------------------
    >>> from collections import Counter, defaultdict
    >>> c = Counter();        _ = c['q'];  len(c)    # 0  — no insert
    >>> d = defaultdict(int); _ = d['q'];  len(d)    # 1  — !!! key created

READING a missing key from a `defaultdict` INSERTS it. `Counter.__missing__`
returns 0 without inserting.

Be precise about what this does here, because it is easy to overstate: in the
standard loop shape above, every read of a new key is immediately followed by
an increment, so a `defaultdict` produces the same answers — the test suite
confirms it disagrees on 0 of 20000 random inputs. It is a LATENT hazard, not
an active bug in this exact code.

It becomes an ACTIVE bug the moment you inspect a key you are not about to
write — a debug print, an `if count[x] == 0:` check on a value that is leaving,
a helper that peeks at a neighbour. Then `len(count)` silently gains a phantom
key and your validity test is wrong, with nothing in the code looking suspect.

    RULE: when `len()` of a map is part of your loop condition, use `Counter`
    (or a plain dict with `.get`), never `defaultdict`.


================================================================================
WHY THE WINDOW IS LEGAL
================================================================================
"at most 2 distinct values" is HEREDITARY: removing elements from a subarray
cannot increase its number of distinct values. So a broken window cannot be
repaired by widening, shrinking from the left is the only move, and every left
endpoint passed is eliminated forever. `l` is monotone, and the pass is O(n) by
amortization.

⚠️  Note what this rules out: "EXACTLY 2 distinct" is NOT hereditary (shrink a
    2-distinct window and you may land on 1), so it has no direct window. That
    is the `atMost(k) - atMost(k-1)` situation, and it is problems 012 and 013.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(fruits)

    Approach                         Time      Space   Note
    -------------------------------  --------  ------  ---------------------
    Every start, extend until 3rd    O(n^2)    O(1)    the natural brute force
    Window + Counter ✅              O(n)      O(1)    <= 3 keys ever
    Window + last-occurrence trick   O(n)      O(1)    two scalars, K=2 only
    Run-length + two-type scan       O(n)      O(1)    elegant, K=2 only

    SPACE IS O(1), not O(n): the map is bounded by K+1 = 3 entries, because the
    `while` restores `len <= 2` before the next iteration. Say "O(K)" for the
    general version and note K is a constant here — claiming O(n) suggests you
    have not noticed the bound.

    ⚠️  For general K, `len(count)` is still O(1) (a dict stores its size), so
        the validity test does not cost O(K). The only O(K) thing would be
        scanning the map, which the template never does.


================================================================================
EDGE CASES
================================================================================
    [1]                  -> 1   Single tree.

    [1,1,1,1]            -> 4   One type. `len(count)` is 1 throughout; the
                                `while` never fires.

    [1,2]                -> 2   Exactly two types, exactly at the limit.

    [1,2,3]              -> 2   Three distinct: the window must break exactly
                                once and land on length 2.

    [0,1,2,3,4,5]        -> 2   Every tree a new type. The `while` fires on
                                every step from r=2 onward — the worst case for
                                the shrink loop, still O(n) overall.

    [1,2,1,2,1,2]        -> 6   Two types alternating: the answer is the whole
                                array. Catches anyone who resets on a "change
                                of type" rather than on a third type.

    [3,0,2,3,3,2,3]      -> 5   THE NO-`del` DETECTOR. Without the delete this
                                either crashes with IndexError or returns 2.

    [0,0,0,0]            -> 4   Type 0 is a legal fruit type. Anyone using 0 as
                                an "unset" sentinel in the two-scalar solution
                                breaks here. (Constraint: 0 <= fruits[i].)

    best at either end   [1,2,2,2,3] -> 4 and [3,1,2,2,2] -> 4 together catch
                                loops that skip the first or last window.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting `del count[x]` when the count hits zero. Infinite shrink ->
   IndexError, or (with a bounds guard) badly wrong answers. THE mistake here.

2. Using `defaultdict(int)` where `len()` gates the loop. It happens to work in
   the canonical shape, but any stray read of a missing key inserts a phantom.
   Use `Counter`.

3. Testing `len(count) >= 2` instead of `> 2`. Off by one: two types is legal.

4. Hard-coding two variables for "the two basket types" and trying to update
   which is which. Doable (see `totalFruit_two_scalars`) but fiddly, and it
   does not generalise to K. Lead with the Counter.

5. Resetting the window (`l = r`) when a third type appears, instead of
   shrinking. That throws away the valid tail: on [1,2,3,2,2] it misses
   [2,3,2,2].

6. Restarting from the LAST OCCURRENCE of the previous type rather than from
   the correct boundary. Close, but the boundary is "one past the last
   occurrence of the type being evicted", which is not always the same thing.

7. Treating this as a distinct problem from LC 340. It is LC 340 with K=2.
   Solve the general one.

8. Reporting O(n) space for the Counter. It holds at most K+1 = 3 entries.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: K baskets instead of 2 (LC 340)?
A: Change the 2 to K. That is the entire diff — which is why you should have
   written it parameterised from the start.

Q: EXACTLY K distinct types?
A: Not hereditary, so no direct window. Use
   `exactly(K) = atMost(K) - atMost(K-1)`, two O(n) passes. Problems 012/013.

Q: O(1) space without a hash map?
A: For K=2, track the two current types and the length of the trailing run of
   the most recent type. When a third type appears, the new window starts at
   (r - trailing_run). See `totalFruit_two_scalars`. It is genuinely O(1) and a
   nice party trick, but it does not generalise and it is easy to get wrong —
   mention it, do not lead with it.

Q: Return the actual subarray?
A: Track `best_l` when you improve, slice once at the end.

Q: The fruits arrive as a stream?
A: The window needs `fruits[l]` to evict, so buffer the window in a deque. The
   state is O(K) plus the window itself.

Q: Maximise the SUM of the collected fruits (each tree has a value) rather than
   the count, still at most 2 types?
A: Same window, but carry a running sum alongside the counts and record
   `max(best, window_sum)`. The validity test is unchanged. That is LC 1695's
   idea applied here.

Q: Why is "at most K" a window but "exactly K" is not?
A: Heredity. "At most" survives shrinking; "exactly" does not. Being able to
   answer this cleanly is worth more than the code.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 340  Longest Substring with At Most K Distinct — this, parameterised
    LC 159  Longest Substring with At Most Two        — the string twin
            Distinct Characters
    LC 3    Longest Substring No Repeat               — problem 005, same shape
    LC 992  Subarrays with K Different Integers       — problem 013; EXACTLY K
    LC 1695 Maximum Erasure Value                     — distinct + maximise sum
    LC 2107 Number of Unique Flavors After Sharing    — fixed window + distinct
    LC 76   Minimum Window Substring                  — problem 015; `del` again
================================================================================
"""

import random
import time
from collections import Counter, defaultdict
from typing import List


class Solution:
    def totalFruit(self, fruits: List[int]) -> int:
        """Longest window with at most 2 distinct values. O(n) time, O(1) space."""
        return self.longestAtMostKDistinct(fruits, 2)

    def longestAtMostKDistinct(self, fruits: List[int], k: int) -> int:
        """The general version (LC 340). K=2 is just an argument."""
        count = Counter()
        l = best = 0
        for r, f in enumerate(fruits):
            count[f] += 1                              # ENTER
            while len(count) > k:                      # RESTORE
                out = fruits[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]                     # keep len() == distinct
                l += 1
            best = max(best, r - l + 1)                # RECORD
        return best

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def totalFruit_two_scalars(self, fruits: List[int]) -> int:
        """O(1) space with no map at all — K = 2 only.

        Track the two current types and the length of the trailing run of the
        most recent type. When a third type appears, the new window can only
        start where that trailing run began.

        Note `None` is the "unset" sentinel, NOT 0 — 0 is a legal fruit type.
        """
        best = 0
        last = None           # the most recent type
        prev = None           # the other type in the window
        run = 0               # length of the trailing run of `last`
        width = 0             # current window width
        for f in fruits:
            if f == last:
                run += 1
            elif f == prev:
                prev, last = last, f
                run = 1
            else:                                  # a third type appears
                width = run                        # restart from the trailing run
                prev, last = last, f
                run = 1
            width += 1
            best = max(best, width)
        return best

    def totalFruit_brute(self, fruits: List[int], k: int = 2) -> int:
        """O(n^2) oracle."""
        best = 0
        for i in range(len(fruits)):
            seen = set()
            for j in range(i, len(fruits)):
                seen.add(fruits[j])
                if len(seen) > k:
                    break
                best = max(best, j - i + 1)
        return best

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    def totalFruit_no_del(self, fruits: List[int]) -> int:
        """✗ BROKEN — never deletes zero-valued keys, so `len(count)` never
        falls back to 2 and the `while` cannot exit.

        The `l < n` guard below is ARTIFICIAL: without it this raises
        IndexError. It is here only so the demo can print a wrong number
        instead of crashing.
        """
        count = Counter()
        l = best = 0
        n = len(fruits)
        for r, f in enumerate(fruits):
            count[f] += 1
            while len(count) > 2 and l < n:        # `l < n` prevents the crash
                count[fruits[l]] -= 1              # ...but nothing is deleted
                l += 1
            best = max(best, r - l + 1)
        return best

    def totalFruit_no_del_unguarded(self, fruits: List[int]) -> int:
        """✗ BROKEN — the same, without the artificial guard. Raises
        IndexError on any input with 3+ distinct types."""
        count = Counter()
        l = best = 0
        for r, f in enumerate(fruits):
            count[f] += 1
            while len(count) > 2:
                count[fruits[l]] -= 1
                l += 1
            best = max(best, r - l + 1)
        return best

    def totalFruit_reset(self, fruits: List[int]) -> int:
        """✗ BROKEN — restarts the window at r when a third type appears,
        discarding the still-valid tail."""
        count = Counter()
        l = best = 0
        for r, f in enumerate(fruits):
            count[f] += 1
            if len(count) > 2:
                count = Counter([f])
                l = r
            best = max(best, r - l + 1)
        return best


# ==============================================================================
# TESTS — run:  python 009_fruit_into_baskets_solution.py
# ==============================================================================
CASES = [
    [1, 2, 1], [0, 1, 2, 2], [1, 2, 3, 2, 2],
    [3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4], [1], [1, 1, 1, 1], [1, 2], [1, 2, 3],
    [0, 1, 2, 3, 4, 5], [1, 2, 1, 2, 1, 2], [3, 0, 2, 3, 3, 2, 3],
    [1, 1, 2, 2, 3, 3], [1, 2, 2, 2, 3], [3, 1, 2, 2, 2], [0, 0, 0, 0],
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("window + Counter   ", sol.totalFruit),
        ("two scalars, O(1)  ", sol.totalFruit_two_scalars),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(list(a)) == sol.totalFruit_brute(a) for a in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # the general K version must agree with the oracle for every K
    ok = all(sol.longestAtMostKDistinct(list(a), k) == sol.totalFruit_brute(a, k)
             for a in CASES for k in range(1, 5))
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  general 'at most K distinct' "
          f"(K = 1..4, {len(CASES)} arrays)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(904)
    trials, mismatches = 6000, 0
    for _ in range(trials):
        a = [random.randint(0, 4) for _ in range(random.randint(1, 14))]
        want = sol.totalFruit_brute(a)
        for _, fn in impls:
            if fn(list(a)) != want:
                mismatches += 1
        for k in range(1, 4):
            if sol.longestAtMostKDistinct(list(a), k) != sol.totalFruit_brute(a, k):
                mismatches += 1
    print(f"  {trials} random arrays x {len(impls) + 3} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced.
    # ----------------------------------------------------------------------
    fruits = [1, 2, 3, 2, 2]
    print(f"\n--- the window over {fruits} ---")
    print(f"  {'r':>2} {'f':>2} {'l':>2} {'count':>22} {'distinct':>9}"
          f" {'window':>16} {'best':>5}")
    count = Counter()
    l = best = 0
    for r, f in enumerate(fruits):
        count[f] += 1
        while len(count) > 2:
            out = fruits[l]
            count[out] -= 1
            if count[out] == 0:
                del count[out]
            l += 1
        best = max(best, r - l + 1)
        print(f"  {r:>2} {f:>2} {l:>2} {str(dict(count)):>22} {len(count):>9} "
              f"{str(fruits[l:r+1]):>16} {best:>5}")

    # ----------------------------------------------------------------------
    # ⚠️  Forgetting `del`.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  what happens without `del count[x]` ---")
    print("  First: it CRASHES. `len(count)` never falls back to 2, so the")
    print("  `while` runs `l` off the end of the array.")
    try:
        sol.totalFruit_no_del_unguarded([3, 0, 2, 3, 3, 2, 3])
        print("    (no exception — unexpected)")
    except IndexError as e:
        print(f"    IndexError raised on [3,0,2,3,3,2,3]: {e}")

    print("\n  Add an artificial `l < n` guard and the crash becomes silent")
    print("  wrongness — the window is emptied on every step:")
    print(f"  {'input':<32} {'correct':>8} {'no del':>7}  ok?")
    for a in ([3, 0, 2, 3, 3, 2, 3], [1, 2, 3, 2, 2], [1, 2, 1], [1, 2, 1, 2, 1, 2],
              [0, 1, 2, 3, 4, 5]):
        good = sol.totalFruit(list(a))
        bad = sol.totalFruit_no_del(list(a))
        print(f"  {str(a):<32} {good:>8} {bad:>7}  "
              f"{'yes' if good == bad else 'NO'}")
    random.seed(1)
    wrong = 0
    for _ in range(20_000):
        a = [random.randint(0, 3) for _ in range(random.randint(1, 12))]
        if sol.totalFruit_no_del(list(a)) != sol.totalFruit_brute(a):
            wrong += 1
    print(f"  over 20000 random arrays: {wrong} wrong "
          f"({100 * wrong / 20000:.0f}%)")

    # ----------------------------------------------------------------------
    # Counter vs defaultdict: be precise about what actually breaks.
    # ----------------------------------------------------------------------
    print("\n--- Counter vs defaultdict(int): the LATENT hazard ---")
    c = Counter()
    _ = c['q']
    d = defaultdict(int)
    _ = d['q']
    print(f"  after merely READING a missing key:")
    print(f"    Counter        -> len = {len(c)}, contents {dict(c)}")
    print(f"    defaultdict    -> len = {len(d)}, contents {dict(d)}   <- phantom key")

    def with_defaultdict(fruits):
        count = defaultdict(int)
        l = best = 0
        for r, f in enumerate(fruits):
            count[f] += 1
            while len(count) > 2:
                out = fruits[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]
                l += 1
            best = max(best, r - l + 1)
        return best

    random.seed(2)
    diff = 0
    for _ in range(20_000):
        a = [random.randint(0, 3) for _ in range(random.randint(1, 12))]
        if with_defaultdict(list(a)) != sol.totalFruit(list(a)):
            diff += 1
    print(f"  In the CANONICAL loop shape, defaultdict disagrees on {diff} / 20000")
    print("  inputs — because every read of a new key is immediately followed by")
    print("  an increment, so the phantom is filled in at once. It is a LATENT")
    print("  hazard, not an active bug here. It becomes active the moment you")
    print("  inspect a key you are not about to write:")
    d2 = defaultdict(int)
    d2[1] = 2
    d2[2] = 1
    print(f"    window {{1:2, 2:1}}, len = {len(d2)}  (2 distinct — valid)")
    _ = d2[7]                       # an innocent-looking peek at another type
    print(f"    after `if count[7] == 0:` -> len = {len(d2)}  "
          f"contents {dict(d2)}")
    print("    ...the validity test now says 3 distinct and shrinks a valid window.")
    print("  RULE: if len() of the map gates your loop, use Counter.")

    # ----------------------------------------------------------------------
    # ⚠️  Resetting instead of shrinking.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  resetting the window instead of shrinking it ---")
    print(f"  {'input':<28} {'correct':>8} {'reset':>6}  ok?")
    for a in ([1, 2, 3, 2, 2], [3, 3, 3, 1, 2, 1, 1, 2, 3, 3, 4], [0, 1, 2, 2],
              [1, 2, 1]):
        good = sol.totalFruit(list(a))
        bad = sol.totalFruit_reset(list(a))
        print(f"  {str(a):<28} {good:>8} {bad:>6}  "
              f"{'yes' if good == bad else 'NO  <- discarded the valid tail'}")

    # ----------------------------------------------------------------------
    # The map never exceeds K+1 entries — hence O(1) space.
    # ----------------------------------------------------------------------
    print("\n--- the Counter never holds more than K+1 keys ---")
    print(f"  {'K':>3} {'n':>8} {'peak len(count)':>17}")
    random.seed(3)
    for k in (1, 2, 3, 5):
        a = [random.randint(0, 50) for _ in range(50_000)]
        count = Counter()
        l = peak = 0
        for r, f in enumerate(a):
            count[f] += 1
            peak = max(peak, len(count))
            while len(count) > k:
                out = a[l]
                count[out] -= 1
                if count[out] == 0:
                    del count[out]
                l += 1
        print(f"  {k:>3} {len(a):>8} {peak:>17}")
    print("  Bounded by K+1 regardless of n or the number of distinct values in")
    print("  the array — so the space is O(K) = O(1) here, NOT O(n).")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- window vs extending from every start ---")
    print(f"  {'n':>7} {'window O(n)':>13} {'brute O(n^2)':>14}")
    random.seed(0)
    for n in (2_000, 4_000, 8_000):
        a = [random.randint(0, 1) for _ in range(n)]     # TWO types: never breaks
        t0 = time.perf_counter(); sol.totalFruit(a)
        t1 = time.perf_counter(); sol.totalFruit_brute(a)
        t2 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>11.1f}ms {(t2 - t1) * 1000:>12.1f}ms")
    print("  An array with only TWO types is the brute force's worst case: a")
    print("  third type never appears, so the inner loop never breaks and it")
    print("  scans to the end from every start — a genuine n^2/2 comparisons.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
