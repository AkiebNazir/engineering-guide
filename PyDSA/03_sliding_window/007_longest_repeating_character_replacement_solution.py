"""
================================================================================
SOLUTION · LeetCode 424 · Longest Repeating Character Replacement       [Medium]
https://leetcode.com/problems/longest-repeating-character-replacement/
================================================================================

THE CORE IDEA
-------------
For any window, the cost to make it a single repeated letter is

    cost = (window length) - (frequency of the most common letter in it)

because the optimal move is always to keep the letter that is already most
common and replace everything else. So the window is valid iff

    (r - l + 1) - max_freq <= k

and the problem is the Shape-B template with that validity test:

    count = Counter()
    l = best = max_freq = 0
    for r, ch in enumerate(s):
        count[ch] += 1                              # ENTER
        max_freq = max(max_freq, count[ch])         # (never decreased — see below)
        if (r - l + 1) - max_freq > k:              # RESTORE
            count[s[l]] -= 1
            l += 1
        best = max(best, r - l + 1)                 # RECORD
    return best

O(n) time, O(26) = O(1) space.


WHY "KEEP THE MOST FREQUENT LETTER" IS OPTIMAL
----------------------------------------------
One line: if you unify the window to letter X, you must replace every character
that is not X, which costs `len - count[X]`. That is minimised by maximising
`count[X]`, i.e. by picking the most frequent letter. There is nothing to
search over — the choice is forced by arithmetic.

This is the same "the operation is a constraint in disguise" move as problem
006. Notice you never need to know WHICH characters get replaced, only how
many.


================================================================================
THE STALE `max_freq` — the whole reason this problem is a Medium
================================================================================
When the window shrinks, the true maximum frequency may drop. The famous
solution DOES NOT RECOMPUTE IT:

    max_freq = max(max_freq, count[ch])     # monotone non-decreasing, forever

so `max_freq` can be larger than the window's real maximum frequency. That
makes `len - max_freq` an UNDERESTIMATE of the cost, so the window can pass the
validity test when it should have failed. And the answer is still correct.

WHY. Two facts, and together they close the argument:

  1. THE ANSWER CAN ONLY GROW WHEN `max_freq` GENUINELY GROWS.
     `best` improves only when the window widens, and the window widens only on
     a step where the validity test passed. If `max_freq` is stale (say its
     true value is m, and the stored value is M > m), the window's width is at
     most `M + k` — but a width of `M + k` was ALREADY ACHIEVED, legitimately,
     back when `max_freq` really was M. So the reported width is never one that
     was not truly attainable.

  2. A TOO-WIDE WINDOW IS HARMLESS BECAUSE ITS WIDTH IS NEVER INFLATED.
     The window slides rather than shrinks, carrying its width forward. It is
     "remembering" the best legitimate width, not inventing a new one.

This is exactly the Shape-D argument from the topic guide, and it is why the
`max()` at the end is optional: the width is non-decreasing, so its running
maximum equals its final value, and `return len(s) - l` works too.

    ⚠️  The window at the end may be INVALID. That is not a contradiction —
        the claim is about the WIDTH, not about the window being a witness.
        If you must return the actual substring, use the honest version.


================================================================================
`while` VS `if` — WITH A STALE max_freq THEY ARE THE SAME CODE
================================================================================
A genuinely surprising fact, and a good thing to be able to prove:

    With a stale (non-decreasing) `max_freq`, the shrink step can fire AT MOST
    ONCE per iteration — so `while` and `if` are equivalent.

PROOF. Let `w = r - l + 1` after the enter step. Suppose the window was valid
on the previous iteration, i.e. `(w - 1) - max_freq_old <= k`. Entering one
character increases `w` by 1 and can only increase `max_freq`. So

    w - max_freq  <=  (w - 1 + 1) - max_freq_old  =  (w - 1) - max_freq_old + 1
                  <=  k + 1

The violation is therefore at most 1, and removing a single character from the
left restores `w - max_freq <= k`. A second shrink is never needed.

This is why the four "obvious" ways to write this problem all work, and it is
a much better answer than "I memorised that it's an `if`". The empirical
confirmation is in the test suite: all of

    stale  + if    + max()         stale  + if    + final width
    stale  + while + max()         stale  + while + final width
    honest + if    + max()         honest + if    + final width
    honest + while + max()

agree on thousands of random inputs. Exactly ONE of the eight is broken:

    ✗ honest + while + final width

because recomputing `max_freq` lets the window genuinely SHRINK, which makes
the width non-monotone, so the final width is no longer the maximum. That is
the same single failing cross as in problem 006 — memorise the shape of the
bug, not a list of allowed templates:

    A FULL SHRINK (`while` + honest state) MAKES THE WIDTH NON-MONOTONE.
    ONLY THEN IS "RETURN THE FINAL WIDTH" WRONG.


================================================================================
THE HONEST VERSION IS ALSO FINE — SAY ITS COMPLEXITY PROPERLY
================================================================================
    while (r - l + 1) - max(count.values()) > k:
        count[s[l]] -= 1
        l += 1

`max(count.values())` scans at most 26 entries, so this is O(26n) — which IS
O(n) for a fixed alphabet. It is a completely acceptable interview answer, and
it is easier to justify. The right way to present it:

    "Recomputing the max is O(26) per step, so O(26n) = O(n) for a fixed
     alphabet. I can also avoid the rescan entirely by never decreasing
     max_freq — here's why that's still correct..."

That ordering — correct first, clever second, with the reason — is much
stronger than leading with the trick and being unable to defend it.

⚠️  If the alphabet were unbounded, `max(count.values())` would be O(Σ) and the
    stale trick would be the only O(n) option. Worth saying.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(s), Σ = 26

    Approach                          Time      Space  Note
    --------------------------------  --------  -----  ----------------------
    Every substring, recount          O(n^3)    O(Σ)
    Every substring, incremental      O(n^2)    O(Σ)    the natural brute force
    Try each of 26 target letters,    O(26n)    O(1)    ← nice alternative:
      run a "at most k others" window                     26 runs of LC 1004
    Window + honest max_freq ✅       O(26n)    O(Σ)    rescan on shrink
    Window + stale max_freq ✅        O(n)      O(Σ)    no rescan at all

    The "26 separate LC 1004 windows" solution deserves a mention: fix the
    target letter c, then run problem 006's window with "not c" as the
    violation. Take the best over all 26. It is embarrassingly simple, provably
    correct, and O(26n). If you cannot remember the max_freq argument under
    pressure, THIS is the fallback that still gets you a linear solution.


================================================================================
EDGE CASES
================================================================================
    "A", k=0        -> 1   Single character. `r - l + 1` at r = l = 0.

    "AB", k=0       -> 1   No budget: the answer is the longest existing run.

    "AAAA", k=0     -> 4   No budget needed; the window never breaks.

    "ABCDE", k=4    -> 5   Budget exactly covers the whole string
                           (cost = 5 - 1 = 4).

    "ABCDE", k=100  -> 5   k > n. The answer is capped at n — make sure you do
                           not return k or k+1.

    "AAAB", k=0     -> 3   Best run at the FRONT.
    "BAAA", k=0     -> 3   Best run at the END. The pair catches loops that
                           skip the first or last window.

    "XYZXYZXYZ",k=2 -> 4   No repeated letters adjacent anywhere; the answer
                           comes entirely from the budget ("XYZX" costs 2).
                           A good check that you are not special-casing runs.

    "AABABBA", k=1  -> 4   The example whose answer window ("AABA", cost 1)
                           is NOT where the longest run of a single letter is.


================================================================================
COMMON MISTAKES
================================================================================
1. Tracking "the most frequent letter" as an identity rather than a COUNT, and
   then trying to update which letter it is. You only ever need the number.

2. Using `while` with an honest recomputed max_freq and then returning
   `len(s) - l`. THE one broken cross. Returns 3 instead of 4 on "AABABBA".

3. Recomputing `max_freq` as `max(count.values())` when `count` may be empty —
   `max()` on an empty sequence raises ValueError. Use `default=0`, or keep
   zero-valued keys, or guard the call.

4. Decrementing but never deleting zero-valued keys, then using `len(count)` as
   if it were the number of distinct letters in the window. It is not — see
   topic guide §3.2. (For THIS problem it does not matter, because you only use
   `count.values()`, but the habit matters for problems 009 and 013.)

5. `(r - l + 1) - max_freq >= k` instead of `> k`. Off by one: a window whose
   cost is exactly k is VALID.

6. Believing the stale `max_freq` is a hack that "happens to work". It has a
   proof. Give the proof.

7. Claiming the stale version is needed for O(n). For a 26-letter alphabet the
   honest version is already O(n) with a constant of 26. Be precise.

8. Assuming the answer window contains the most frequent letter of the WHOLE
   string. It need not.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return the actual substring.
A: Use the HONEST version — its window is always valid — and record
   `(best_l, best_r)`. The stale/never-shrink version's window may be invalid,
   so it cannot produce a witness.

Q: Prove the stale max_freq is correct.
A: The two-fact argument above. The key sentence: "a window that survives on a
   stale max_freq has a width that was already legitimately achieved, so the
   reported maximum is never inflated."

Q: How many times can the shrink fire per iteration?
A: At most once, by the `k + 1` bound above. Hence `while` == `if` here.

Q: The alphabet is unbounded (Unicode).
A: `max(count.values())` becomes O(Σ) and the honest version degrades. The
   stale version stays O(n). Alternatively keep a max-heap or a
   count-of-counts array, but the stale trick is simpler.

Q: At most k replacements AND at most m distinct characters?
A: Two conditions on the same window. Both are hereditary, so the same shrink
   loop restores both — `while cost > k or len(count) > m:`. That is where the
   `del count[ch]` on zero becomes mandatory.

Q: Longest substring with the same letter after at most k DELETIONS?
A: Different problem — deletions change the indices, so the result is not a
   contiguous substring of the original. That breaks the window entirely.

Q: Do it without the Counter.
A: A 26-slot list with `ord(ch) - 65` ('A' is 65, not 97 — this problem is
   UPPERCASE). Same code, smaller constant, and `max(arr)` is a fixed 26 steps.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 1004 Max Consecutive Ones III   — problem 006; this with a 2-letter
                                          alphabet and a fixed target
    LC 3    Longest Substring No Rep   — problem 005; the same template
    LC 340  Longest Substring with At  — validity is `len(count) > k`
            Most K Distinct
    LC 1004/2024 Maximize Confusion    — run it twice for T and F
    LC 2260 Minimum Consecutive Cards  — the SHORTEST-window mirror
    LC 1493 Longest Subarray of 1s     — k = 1, answer minus one
    LC 76   Minimum Window Substring   — problem 015; shortest + have/need
================================================================================
"""

import random
import time
from collections import Counter
from typing import Tuple


class Solution:
    def characterReplacement(self, s: str, k: int) -> int:
        """Shape D with a STALE max_freq. O(n) time, O(26) space.

        `max_freq` is never decreased; see the module docstring for why that is
        correct, and why `if` and `while` are equivalent here.
        """
        count = Counter()
        l = best = max_freq = 0
        for r, ch in enumerate(s):
            count[ch] += 1                                  # ENTER
            max_freq = max(max_freq, count[ch])             # only ever grows
            if (r - l + 1) - max_freq > k:                  # cost exceeds budget
                count[s[l]] -= 1
                l += 1                                      # slide, keep width
            best = max(best, r - l + 1)                     # (redundant: see below)
        return best

    # ------------------------------------------------------------------
    # Alternatives — all correct.
    # ------------------------------------------------------------------
    def characterReplacement_final_width(self, s: str, k: int) -> int:
        """The same, returning the final width. No max() at all."""
        count = Counter()
        l = max_freq = 0
        for r, ch in enumerate(s):
            count[ch] += 1
            max_freq = max(max_freq, count[ch])
            if (r - l + 1) - max_freq > k:
                count[s[l]] -= 1
                l += 1
        return len(s) - l

    def characterReplacement_honest(self, s: str, k: int) -> int:
        """Recomputes max_freq on every shrink. O(26n) — also O(n) for a fixed
        alphabet, and much easier to justify. The window is ALWAYS valid."""
        count = Counter()
        l = best = 0
        for r, ch in enumerate(s):
            count[ch] += 1
            while (r - l + 1) - max(count.values(), default=0) > k:
                count[s[l]] -= 1
                if count[s[l]] == 0:
                    del count[s[l]]
                l += 1
            best = max(best, r - l + 1)
        return best

    def characterReplacement_honest_bounds(self, s: str, k: int) -> Tuple[int, int, int]:
        """Follow-up: return (length, l, r). Needs the honest version, because
        only its window is guaranteed valid."""
        count = Counter()
        l = best = 0
        bl = br = -1
        for r, ch in enumerate(s):
            count[ch] += 1
            while (r - l + 1) - max(count.values(), default=0) > k:
                count[s[l]] -= 1
                if count[s[l]] == 0:
                    del count[s[l]]
                l += 1
            if r - l + 1 > best:
                best, bl, br = r - l + 1, l, r
        return best, bl, br

    def characterReplacement_26_windows(self, s: str, k: int) -> int:
        """The fallback worth knowing: fix the target letter, then run problem
        006's 'at most k violations' window. 26 passes, O(26n), obviously
        correct — no max_freq argument required."""
        best = 0
        for target in set(s):
            l = bad = 0
            for r, ch in enumerate(s):
                bad += ch != target
                while bad > k:
                    bad -= s[l] != target
                    l += 1
                best = max(best, r - l + 1)
        return best

    def characterReplacement_array(self, s: str, k: int) -> int:
        """26-slot list instead of a Counter. 'A' is chr(65), not chr(97)."""
        count = [0] * 26
        l = best = max_freq = 0
        for r, ch in enumerate(s):
            c = ord(ch) - 65
            count[c] += 1
            max_freq = max(max_freq, count[c])
            if (r - l + 1) - max_freq > k:
                count[ord(s[l]) - 65] -= 1
                l += 1
            best = max(best, r - l + 1)
        return best

    def characterReplacement_brute(self, s: str, k: int) -> int:
        """O(n^2 * 26) oracle."""
        best = 0
        for i in range(len(s)):
            c = Counter()
            for j in range(i, len(s)):
                c[s[j]] += 1
                if (j - i + 1) - max(c.values()) <= k:
                    best = max(best, j - i + 1)
        return best

    # ------------------------------------------------------------------
    # The ONE broken cross.
    # ------------------------------------------------------------------
    def characterReplacement_honest_final_width(self, s: str, k: int) -> int:
        """✗ BROKEN ON PURPOSE — honest max_freq (so the window really SHRINKS)
        combined with Shape D's 'return the final width'.

        A full shrink makes the width non-monotone, so the last width is not
        the maximum. "AABABBA", k=1 -> returns 3, answer is 4.
        """
        count = Counter()
        l = 0
        for r, ch in enumerate(s):
            count[ch] += 1
            while (r - l + 1) - max(count.values(), default=0) > k:
                count[s[l]] -= 1
                if count[s[l]] == 0:
                    del count[s[l]]
                l += 1
        return len(s) - l


# ==============================================================================
# TESTS — run:  python 007_longest_repeating_character_replacement_solution.py
# ==============================================================================
CASES = [
    ("ABAB", 2), ("AABABBA", 1), ("A", 0), ("AB", 0), ("AAAA", 0),
    ("ABCDE", 0), ("ABCDE", 4), ("ABCDE", 100), ("AABA", 0), ("BAAAB", 2),
    ("ABBB", 2), ("ABAA", 0), ("AAAB", 0), ("BAAA", 0), ("ABABBA", 1),
    ("XYZXYZXYZ", 2), ("AAAABBBB", 2),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("stale max_freq + max()   ", sol.characterReplacement),
        ("stale max_freq, no max() ", sol.characterReplacement_final_width),
        ("honest max_freq (O(26n)) ", sol.characterReplacement_honest),
        ("26 separate LC1004 passes", sol.characterReplacement_26_windows),
        ("26-slot array            ", sol.characterReplacement_array),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(t, k) == sol.characterReplacement_brute(t, k)
                 for t, k in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    # the bounds variant must return a window that is genuinely affordable
    ok = True
    for t, k in CASES:
        ln, bl, br = sol.characterReplacement_honest_bounds(t, k)
        if ln != sol.characterReplacement_brute(t, k):
            ok = False
        if ln > 0:
            win = t[bl:br + 1]
            if len(win) != ln or len(win) - max(Counter(win).values()) > k:
                ok = False
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  bounds variant (right length AND a "
          f"genuinely affordable window)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the O(n^2) oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the O(n^2) oracle ---")
    random.seed(424)
    trials, mismatches = 4000, 0
    for _ in range(trials):
        t = "".join(random.choice("ABC")
                    for _ in range(random.randint(1, 14)))
        k = random.randint(0, 4)
        want = sol.characterReplacement_brute(t, k)
        for _, fn in impls:
            if fn(t, k) != want:
                mismatches += 1
    print(f"  {trials} random (string, k) x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced.
    # ----------------------------------------------------------------------
    text, k = "AABABBA", 1
    print(f"\n--- the window over {text!r}, k={k} ---")
    print(f"  {'r':>2} {'ch':>4} {'maxf':>5} {'true maxf':>10} {'len':>4}"
          f" {'cost':>5} {'l':>2} {'window':>10} {'best':>5}")
    count = Counter()
    l = best = max_freq = 0
    for r, ch in enumerate(text):
        count[ch] += 1
        max_freq = max(max_freq, count[ch])
        if (r - l + 1) - max_freq > k:
            count[text[l]] -= 1
            l += 1
        w = r - l + 1
        true_maxf = max(count.values())
        best = max(best, w)
        stale = " (STALE)" if max_freq > true_maxf else ""
        print(f"  {r:>2} {ch!r:>4} {max_freq:>5} {true_maxf:>10} {w:>4} "
              f"{w - true_maxf:>5} {l:>2} {text[l:r+1]!r:>10} {best:>5}{stale}")
    print("  Where max_freq is STALE the recorded cost is understated — and the")
    print("  width there was already achieved legitimately, so `best` is safe.")

    # ----------------------------------------------------------------------
    # `while` == `if` with a stale max_freq: the violation is at most 1.
    # ----------------------------------------------------------------------
    print("\n--- with a stale max_freq the shrink fires AT MOST ONCE ---")
    random.seed(9)
    worst = 0
    for _ in range(4000):
        t = "".join(random.choice("ABCD") for _ in range(random.randint(1, 40)))
        k = random.randint(0, 4)
        count = Counter()
        l = max_freq = 0
        for r, ch in enumerate(t):
            count[ch] += 1
            max_freq = max(max_freq, count[ch])
            fires = 0
            while (r - l + 1) - max_freq > k:      # written as a WHILE on purpose
                count[t[l]] -= 1
                l += 1
                fires += 1
            worst = max(worst, fires)
    print(f"  max shrinks in a single iteration, over 4000 random strings: {worst}")
    print("  Never more than 1 — because entering one character raises the")
    print("  violation by at most 1, and max_freq never falls. So `while` and")
    print("  `if` are literally the same program here.")
    all_ok &= (worst <= 1)

    # ----------------------------------------------------------------------
    # ⚠️  The one broken cross.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  honest max_freq + 'return the final width' ---")
    print(f"  {'input':<14} {'k':>2} {'correct':>8} {'honest+final':>13}  ok?")
    for t, k in ("AABABBA", 1), ("ABAB", 2), ("ABCAAC", 0), ("AAAB", 0), \
                ("BAAA", 0), ("XYZXYZXYZ", 2):
        good = sol.characterReplacement(t, k)
        bad = sol.characterReplacement_honest_final_width(t, k)
        print(f"  {t!r:<14} {k:>2} {good:>8} {bad:>13}  "
              f"{'yes' if good == bad else 'NO  <- width is not monotone'}")

    print("\n  Seven of the eight combinations agree; only ONE is wrong:")
    def variant(t, k, stale, use_if, final_width):
        c = Counter(); l = best = maxf = 0
        for r, ch in enumerate(t):
            c[ch] += 1
            maxf = max(maxf, c[ch]) if stale else max(c.values())
            if use_if:
                if (r - l + 1) - maxf > k:
                    c[t[l]] -= 1; l += 1
                    if not stale:
                        maxf = max(c.values()) if sum(c.values()) else 0
            else:
                while (r - l + 1) - maxf > k:
                    c[t[l]] -= 1; l += 1
                    if not stale:
                        maxf = max(c.values()) if sum(c.values()) else 0
            best = max(best, r - l + 1)
        return len(t) - l if final_width else best

    combos = {
        (True, True, False): "stale  + if    + max()",
        (True, True, True): "stale  + if    + final width",
        (True, False, False): "stale  + while + max()",
        (True, False, True): "stale  + while + final width",
        (False, True, False): "honest + if    + max()",
        (False, True, True): "honest + if    + final width",
        (False, False, False): "honest + while + max()",
        (False, False, True): "honest + while + final width",
    }
    random.seed(7)
    bad_counts = {c: 0 for c in combos}
    for _ in range(4000):
        t = "".join(random.choice("ABC") for _ in range(random.randint(1, 14)))
        k = random.randint(0, 4)
        want = sol.characterReplacement_brute(t, k)
        for c in combos:
            if variant(t, k, *c) != want:
                bad_counts[c] += 1
    print(f"  {'combination':<32} {'disagreements / 4000':>21}")
    for c, name in combos.items():
        mark = "  ✗" if bad_counts[c] else "  ✅"
        print(f"  {name:<32} {bad_counts[c]:>21}{mark}")
    print("  The rule to remember is not a list — it is: a FULL shrink makes the")
    print("  width non-monotone, and only then is 'final width' wrong.")

    # ----------------------------------------------------------------------
    # What the stale trick actually saves.
    # ----------------------------------------------------------------------
    print("\n--- what skipping the max_freq rescan buys ---")
    print(f"  {'n':>7} {'stale O(n)':>12} {'honest O(26n)':>15} {'26 passes':>11}")
    random.seed(0)
    for n in (20_000, 40_000, 80_000):
        t = "".join(random.choice("ABCDEFGHIJKLMNOPQRSTUVWXYZ") for _ in range(n))
        k = n // 50
        t0 = time.perf_counter(); sol.characterReplacement(t, k)
        t1 = time.perf_counter(); sol.characterReplacement_honest(t, k)
        t2 = time.perf_counter(); sol.characterReplacement_26_windows(t, k)
        t3 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>10.1f}ms {(t2 - t1) * 1000:>13.1f}ms "
              f"{(t3 - t2) * 1000:>9.1f}ms")
    print("  All three are LINEAR in n — the gaps are the constants 1, ~26 and")
    print("  26. Any of them passes; only the first needs the staleness proof.")

    # ----------------------------------------------------------------------
    # O(n) vs O(n^2).
    # ----------------------------------------------------------------------
    print("\n--- window vs checking every substring ---")
    print(f"  {'n':>7} {'window O(n)':>13} {'brute O(n^2)':>14}")
    for n in (1_000, 2_000, 4_000):
        t = "".join(random.choice("ABCD") for _ in range(n))
        t0 = time.perf_counter(); sol.characterReplacement(t, 3)
        t1 = time.perf_counter(); sol.characterReplacement_brute(t, 3)
        t2 = time.perf_counter()
        print(f"  {n:>7} {(t1 - t0) * 1000:>11.1f}ms {(t2 - t1) * 1000:>12.1f}ms")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
