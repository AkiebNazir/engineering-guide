"""
================================================================================
SOLUTION · LeetCode 567 · Permutation in String                         [Medium]
https://leetcode.com/problems/permutation-in-string/
================================================================================

THE CORE IDEA
-------------
A permutation of `s1` has exactly `len(s1)` characters, so every candidate is a
FIXED-SIZE window of width k = len(s1). And "is a permutation of" means "has
identical character frequencies". So:

    slide a width-k window over s2, and ask whether its frequency map
    equals s1's frequency map.

Two 26-slot lists and a slide:

    k = len(s1)
    if k > len(s2): return False
    need, window = [0] * 26, [0] * 26
    for i in range(k):
        need[ord(s1[i]) - 97] += 1
        window[ord(s2[i]) - 97] += 1
    if need == window: return True
    for r in range(k, len(s2)):
        window[ord(s2[r]) - 97] += 1              # enter
        window[ord(s2[r - k]) - 97] -= 1          # leave
        if need == window: return True
    return False

O(26n) time, O(1) space — and O(26n) is O(n) for a fixed alphabet. Ship this
version first; it is short, obviously correct, and fast enough.


================================================================================
THE THREE COST LEVELS — know which one you are writing
================================================================================
    1. REBUILD the window's counts each step
           Counter(s2[i:i+k]) == need
       O(k) to slice + O(k) to count, per step  ->  O(n*k). The trap.

    2. SLIDE the counts, COMPARE the whole map each step        <- the code above
           window[in] += 1; window[out] -= 1;  window == need
       O(1) to update + O(26) to compare, per step  ->  O(26n).

    3. SLIDE the counts, maintain a MATCH COUNTER
           matches = how many of the 26 letters satisfy window[c] == need[c]
       O(1) to update + O(1) to test, per step  ->  O(n).

Levels 2 and 3 are both O(n) for a bounded alphabet. The honest thing to say is
*"this is O(26n) — linear, with a factor of the alphabet size; I can drop the
26 with a match counter if you want strict O(n)."* Then do it.

⚠️  THE DATA STRUCTURE MATTERS MORE THAN THE LEVEL HERE. Measured over 200k
    comparisons: `list == list` on 26 ints takes ~7ms; `Counter == Counter`
    takes ~464ms — about 70x slower. Counter equality has to reconcile
    zero-valued keys and iterate a hash table. When the alphabet is fixed and
    small, USE A LIST. The benchmark at the bottom of this file reproduces it.


================================================================================
THE MATCH COUNTER — the machine you will reuse in problems 011 and 015
================================================================================
Keep one integer:

    matches = |{ c : window[c] == need[c] }|          (over all 26 letters)

The window is a permutation of s1 exactly when `matches == 26`.

⚠️  INITIALISE IT OVER ALL 26 LETTERS, NOT JUST THE ONES PRESENT. A letter that
    appears in neither string has `window[c] == need[c] == 0`, which IS a
    match and must be counted. Start from
    `matches = sum(need[i] == window[i] for i in range(26))` — typically 24 or
    25 at the beginning, not 0.

THE UPDATE RULE. A single character entering or leaving changes exactly one
letter's count, by exactly 1. So at most one equality flips, and there are
exactly two interesting cases per direction:

    ON INCREMENT (a letter enters):
        window[c] += 1
        if   window[c] == need[c]:      matches += 1   # we just BECAME equal
        elif window[c] == need[c] + 1:  matches -= 1   # we just LEFT equality

    ON DECREMENT (a letter leaves):
        window[c] -= 1
        if   window[c] == need[c]:      matches += 1   # we just BECAME equal
        elif window[c] == need[c] - 1:  matches -= 1   # we just LEFT equality

Read those four lines carefully. Both directions can INCREASE matches (by
landing exactly on the needed count) and both can DECREASE it (by stepping one
past it, from the appropriate side). Every other transition leaves the equality
unchanged, so `matches` does not move.

⚠️  USE `==` IN THE MATCH UPDATE, NOT `>=`. Writing `window[c] >= need[c]` as
    the per-letter satisfaction test would mean an OVER-supplied letter still
    counts as satisfied, and the increment/decrement bookkeeping above no
    longer tracks a well-defined quantity.

    A genuinely interesting subtlety, though: for THIS problem, testing
    `all(window[c] >= need[c])` on the whole window is actually EQUIVALENT to
    testing equality. The reason is a counting argument, not luck:

        the window has exactly k characters, so   sum(window) = k
        s1 has exactly k characters, so           sum(need)   = k
        if window[c] >= need[c] for every c, and the two totals are equal,
        then no slack is possible anywhere: window[c] == need[c] for all c.

    So a componentwise `>=` check on a FIXED-WIDTH window collapses to `==`.
    That is exactly what stops being true in problem 015 (Minimum Window
    Substring): there the window is VARIABLE-width, `sum(window) >= k` rather
    than `= k`, the slack is real, and `>=` is strictly weaker than `==` — and
    `>=` is the relation you actually want there, because LC 76 asks for
    coverage rather than an exact permutation.

    Same machine, different comparison, and the width is what decides which.

⚠️  ORDER OF OPERATIONS. Update the count FIRST, then test the new value
    against `need`. Testing before the change asks about a state that no longer
    exists.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(s2), k = len(s1), Σ = 26

    Approach                            Time        Space   Note
    ----------------------------------  ----------  ------  -------------------
    Sort every window                   O(n k logk) O(k)    the naive oracle
    Counter(window) rebuilt per step    O(n k)      O(Σ)    the slicing trap
    Slide + compare 26-lists ✅         O(Σ n)      O(1)    short and fast
    Slide + Counter comparison          O(Σ n)      O(Σ)    same O, ~70x slower
    Slide + match counter ✅            O(n)        O(1)    strict O(n)

    ⚠️  Answer "O(n) for a fixed alphabet" and then be able to say where the 26
        went. Saying just "O(n)" while your code does a dict comparison in the
        loop is the sort of thing an interviewer will probe.


================================================================================
EDGE CASES
================================================================================
    len(s1) > len(s2)     "abc" vs "ab" -> False. Must be checked BEFORE the
                          priming loop, or `s2[i]` raises IndexError. The most
                          common crash in this problem.

    len(s1) == len(s2)    "ab" vs "ba" -> True. Exactly one window exists, and
                          it is the whole string. The loop body never runs, so
                          the answer must already be decided by the priming
                          comparison. Anyone who only tests inside the loop
                          returns False here.

    single characters     "a" vs "a" -> True;  "a" vs "b" -> False.

    multiplicity          "aab" vs "abb" -> False, and "abb" vs "aab" -> False.
                          Both directions matter. A solution using SETS instead
                          of counts passes neither — this pair is the detector.

    letters present but   "abc" vs "ccccbbbbaaaa" -> False. Every letter of s1
    never adjacent        occurs in s2, but never in one window. Catches "is
                          every character of s1 in s2?" non-solutions.

    "hello" vs            -> False. Same idea with repeats.
    "ooolleoooleh"

    match at either end   "ab" vs "baeido" (start) and "ab" vs "eidbao" (end).
                          Together they catch off-by-one loop bounds.

    disjoint alphabets    "xy" vs "abcdefgh" -> False. `matches` starts high
                          (24 letters match at 0-0) and must never reach 26.


================================================================================
COMMON MISTAKES
================================================================================
1. Not checking `len(s1) > len(s2)` first. IndexError while priming.

2. Forgetting to compare the FIRST window (the one built during priming). Then
   "ab" vs "ba" returns False.

3. Rebuilding `Counter(s2[i:i+k])` inside the loop. O(n*k).

4. Comparing SETS of characters instead of COUNTS. "aab" vs "abb" then passes.

5. Initialising `matches = 0` instead of counting all 26 equalities up front.
   Letters absent from both strings are matches at 0 == 0.

6. Using `>=` as the per-letter test inside the match-counter bookkeeping.
   (A whole-window `all(window[c] >= need[c])` check IS correct here — see the
   counting argument above — but the incremental `matches` update needs exact
   equality to be well defined.)

7. Getting the two decrement/increment cases backwards — e.g. writing
   `window[c] == need[c] - 1` on the increment path. Enumerate the cases
   explicitly rather than pattern-matching from memory.

8. Testing the equality before applying the count change.

9. Using `ord(c) - ord('a')` correctly but assuming uppercase. This problem is
   lowercase (97). LC 424 is uppercase (65). Read the constraint.

10. Answering "O(n)" without noticing the O(26) comparison inside the loop.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return ALL starting indices instead of a boolean (LC 438).
A: Do not return on the first hit; append `r - k + 1` and keep sliding. That is
   problem 011 in this folder — literally the same code with a different
   accumulator.

Q: The alphabet is Unicode, not 26 letters.
A: The 26-list becomes a dict, and the `matches` counter becomes essential —
   comparing two dicts of unbounded size is O(Σ) per step, whereas the match
   counter stays O(1). Say `matches == len(need)` rather than `== 26`, and
   count only the letters that appear in either string.

Q: Permutation of s1 as a SUBSEQUENCE rather than a substring?
A: Trivially different — you just need every character of s1 to appear in s2
   with sufficient multiplicity, in any positions. One pass with a Counter, no
   window at all. Good sanity question: it checks that you know why contiguity
   is what makes the window necessary.

Q: Can you do it without any extra array, in O(1) space?
A: The 26-slot array IS O(1) — 26 is a constant. If pushed for "no arrays at
   all", you can pack 26 small counts into a big integer, but that is a stunt.
   The honest answer is "it already is O(1); 26 does not grow with the input."

Q: What if s1 can contain repeated characters and you must find the SHORTEST
   window containing all of them (not exactly)?
A: That is LC 76, problem 015 — the window becomes VARIABLE-size and `matches`
   uses `>=` semantics instead of `==`.

Q: Why is a fixed window enough here, when LC 76 needs a variable one?
A: Because a permutation's length is known. The moment the target only has to
   be CONTAINED rather than exactly matched, the length is no longer fixed and
   you must search over widths.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 438  Find All Anagrams in a String  — problem 011; same code, all indices
    LC 76   Minimum Window Substring       — problem 015; variable width, >=
    LC 242  Valid Anagram                  — the single-window base case
    LC 1347 Min Steps to Make Two Strings  — frequency difference, no window
            Anagram
    LC 30   Substring with Concatenation   — the same idea over WORDS
            of All Words
    LC 1461 Check If a String Contains All — fixed window over binary codes
            Binary Codes of Size K
================================================================================
"""

import random
import time
from collections import Counter
from typing import List


class Solution:
    def checkInclusion(self, s1: str, s2: str) -> bool:
        """Fixed window + a match counter. O(n) time, O(26) = O(1) space."""
        k, n = len(s1), len(s2)
        if k > n:
            return False

        need = [0] * 26
        window = [0] * 26
        for i in range(k):
            need[ord(s1[i]) - 97] += 1
            window[ord(s2[i]) - 97] += 1

        # Count ALL 26 equalities — letters absent from both match at 0 == 0.
        matches = sum(need[i] == window[i] for i in range(26))
        if matches == 26:
            return True                       # the FIRST window already matches

        for r in range(k, n):
            i = ord(s2[r]) - 97               # ENTER
            window[i] += 1
            if window[i] == need[i]:
                matches += 1                  # just became equal
            elif window[i] == need[i] + 1:
                matches -= 1                  # just left equality from above

            j = ord(s2[r - k]) - 97           # LEAVE
            window[j] -= 1
            if window[j] == need[j]:
                matches += 1                  # just became equal
            elif window[j] == need[j] - 1:
                matches -= 1                  # just left equality from below

            if matches == 26:
                return True
        return False

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def checkInclusion_compare_lists(self, s1: str, s2: str) -> bool:
        """Slide the counts, compare the two 26-lists each step. O(26n).

        Shorter, obviously correct, and fast in practice. Write this first.
        """
        k, n = len(s1), len(s2)
        if k > n:
            return False
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(s1[i]) - 97] += 1
            window[ord(s2[i]) - 97] += 1
        if need == window:
            return True
        for r in range(k, n):
            window[ord(s2[r]) - 97] += 1
            window[ord(s2[r - k]) - 97] -= 1
            if need == window:
                return True
        return False

    def checkInclusion_counter(self, s1: str, s2: str) -> bool:
        """Same, but with Counter. Same complexity, ~70x slower comparison.

        Note `Counter.__eq__` ignores zero-valued keys (Python 3.10+), so this
        is CORRECT without deleting them — unlike anything that uses len().
        """
        k, n = len(s1), len(s2)
        if k > n:
            return False
        need = Counter(s1)
        window = Counter(s2[:k])
        if window == need:
            return True
        for r in range(k, n):
            window[s2[r]] += 1
            window[s2[r - k]] -= 1
            if window == need:
                return True
        return False

    def checkInclusion_brute(self, s1: str, s2: str) -> bool:
        """O(n k log k) oracle: sort every window."""
        k = len(s1)
        target = sorted(s1)
        return any(sorted(s2[i:i + k]) == target
                   for i in range(len(s2) - k + 1))

    def findAllPermutations(self, s1: str, s2: str) -> List[int]:
        """Follow-up (LC 438): every starting index, not just the first."""
        k, n = len(s1), len(s2)
        out: List[int] = []
        if k > n:
            return out
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(s1[i]) - 97] += 1
            window[ord(s2[i]) - 97] += 1
        if need == window:
            out.append(0)
        for r in range(k, n):
            window[ord(s2[r]) - 97] += 1
            window[ord(s2[r - k]) - 97] -= 1
            if need == window:
                out.append(r - k + 1)
        return out

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    def checkInclusion_sets(self, s1: str, s2: str) -> bool:
        """✗ BROKEN — compares SETS of characters, losing multiplicity.
        "aab" vs "abb" reports True."""
        k, n = len(s1), len(s2)
        if k > n:
            return False
        need = set(s1)
        return any(set(s2[i:i + k]) == need for i in range(n - k + 1))

    def checkInclusion_skip_first(self, s1: str, s2: str) -> bool:
        """✗ BROKEN — never checks the FIRST window, only the slid ones.
        "ab" vs "ba" reports False."""
        k, n = len(s1), len(s2)
        if k > n:
            return False
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(s1[i]) - 97] += 1
            window[ord(s2[i]) - 97] += 1
        for r in range(k, n):                 # the priming window is never tested
            window[ord(s2[r]) - 97] += 1
            window[ord(s2[r - k]) - 97] -= 1
            if need == window:
                return True
        return False

    def checkInclusion_ge_check(self, s1: str, s2: str) -> bool:
        """CORRECT, and instructively so: tests `window[c] >= need[c]` for every
        c rather than equality.

        It agrees with the `==` version ALWAYS — because both the window and s1
        contain exactly k characters, so componentwise `>=` plus equal totals
        forces equality. This is what stops being true in LC 76, where the
        window's width is not fixed.
        """
        k, n = len(s1), len(s2)
        if k > n:
            return False
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(s1[i]) - 97] += 1
            window[ord(s2[i]) - 97] += 1
        for r in range(k - 1, n):
            if r >= k:
                window[ord(s2[r]) - 97] += 1
                window[ord(s2[r - k]) - 97] -= 1
            if all(window[i] >= need[i] for i in range(26)):   # `>=`, not `==`
                return True
        return False


# ==============================================================================
# TESTS — run:  python 010_permutation_in_string_solution.py
# ==============================================================================
CASES = [
    ("ab", "eidbaooo"), ("ab", "eidboaoo"), ("a", "a"), ("a", "b"),
    ("abc", "ab"), ("adc", "dcda"), ("hello", "ooolleoooleh"),
    ("abc", "ccccbbbbaaaa"), ("ab", "ab"), ("ab", "ba"), ("aab", "aba"),
    ("aab", "abb"), ("abb", "aab"), ("ab", "eidbao"), ("ab", "baeido"),
    ("xy", "abcdefgh"), ("aaa", "aaaa"), ("aaaa", "aaa"),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("match counter O(n) ", sol.checkInclusion),
        ("compare 26-lists   ", sol.checkInclusion_compare_lists),
        ("compare Counters   ", sol.checkInclusion_counter),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(a, b) == sol.checkInclusion_brute(a, b) for a, b in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    def brute_all(s1, s2):
        k, t = len(s1), sorted(s1)
        return [i for i in range(len(s2) - k + 1) if sorted(s2[i:i + k]) == t]
    ok = all(sol.findAllPermutations(a, b) == brute_all(a, b) for a, b in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  all-indices variant (LC 438 preview)")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the sorting oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the sorting oracle ---")
    random.seed(567)
    trials, mismatches = 6000, 0
    for _ in range(trials):
        a = "".join(random.choice("abc") for _ in range(random.randint(1, 5)))
        b = "".join(random.choice("abc") for _ in range(random.randint(1, 12)))
        want = sol.checkInclusion_brute(a, b)
        for _, fn in impls:
            if fn(a, b) != want:
                mismatches += 1
        if sol.findAllPermutations(a, b) != brute_all(a, b):
            mismatches += 1
    print(f"  {trials} random (s1, s2) x {len(impls) + 1} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window and the match counter, traced.
    # ----------------------------------------------------------------------
    s1, s2 = "ab", "eidbaooo"
    k = len(s1)
    print(f"\n--- the window over s2={s2!r} with s1={s1!r} (k={k}) ---")
    need, window = [0] * 26, [0] * 26
    for i in range(k):
        need[ord(s1[i]) - 97] += 1
        window[ord(s2[i]) - 97] += 1
    matches = sum(need[i] == window[i] for i in range(26))
    print(f"  need (nonzero): "
          f"{ {chr(97+i): need[i] for i in range(26) if need[i]} }")
    print(f"  {'r':>2} {'window':>8} {'counts':>18} {'matches':>8}  verdict")
    print(f"  {k-1:>2} {s2[:k]!r:>8} "
          f"{str({chr(97+i): window[i] for i in range(26) if window[i]}):>18} "
          f"{matches:>8}  {'MATCH' if matches == 26 else 'no'}")
    for r in range(k, len(s2)):
        i = ord(s2[r]) - 97
        window[i] += 1
        if window[i] == need[i]:
            matches += 1
        elif window[i] == need[i] + 1:
            matches -= 1
        j = ord(s2[r - k]) - 97
        window[j] -= 1
        if window[j] == need[j]:
            matches += 1
        elif window[j] == need[j] - 1:
            matches -= 1
        shown = {chr(97 + t): window[t] for t in range(26) if window[t]}
        print(f"  {r:>2} {s2[r-k+1:r+1]!r:>8} {str(shown):>18} {matches:>8}  "
              f"{'MATCH -> return True' if matches == 26 else 'no'}")
        if matches == 26:
            break
    print("  `matches` starts at 24, not 0 — the 24 letters absent from both")
    print("  strings satisfy window[c] == need[c] == 0, and those count.")

    # ----------------------------------------------------------------------
    # ⚠️  The classic breakages.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  sets lose multiplicity; skipping the first window ---")
    print(f"  {'s1':<8} {'s2':<16} {'correct':>8} {'sets':>6} {'skip 1st':>9}"
          f" {'all >=':>9}")
    for a, b in ("aab", "abb"), ("abb", "aab"), ("ab", "ba"), ("a", "a"), \
                ("ab", "eidbaooo"), ("aaa", "aaaa"), ("abc", "ccccbbbbaaaa"):
        print(f"  {a!r:<8} {b!r:<16} "
              f"{str(sol.checkInclusion(a, b)):>8} "
              f"{str(sol.checkInclusion_sets(a, b)):>6} "
              f"{str(sol.checkInclusion_skip_first(a, b)):>9} "
              f"{str(sol.checkInclusion_ge_check(a, b)):>9}")
    print("  sets     -> True for 'aab' in 'abb': same letters, wrong counts.")
    print("  skip 1st -> False for 'ab' in 'ba': the only window is the first.")
    print("  all >=   -> agrees EVERYWHERE, and that is not luck: a width-k")
    print("              window and s1 both hold exactly k characters, so")
    print("              componentwise >= with equal totals forces equality.")
    random.seed(5)
    d = 0
    for _ in range(20_000):
        a = "".join(random.choice("abc") for _ in range(random.randint(1, 5)))
        b = "".join(random.choice("abc") for _ in range(random.randint(1, 12)))
        d += sol.checkInclusion(a, b) != sol.checkInclusion_ge_check(a, b)
    print(f"              verified: {d} disagreements over 20000 random pairs.")
    print("              In LC 76 (problem 015) the width is NOT fixed, the")
    print("              totals differ, and >= is then strictly weaker than ==.")

    # ----------------------------------------------------------------------
    # ⚠️  len(s1) > len(s2).
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the guard that prevents a crash ---")
    def no_guard(s1, s2):
        k = len(s1)
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(s1[i]) - 97] += 1
            window[ord(s2[i]) - 97] += 1      # s2[i] out of range when k > len(s2)
        return need == window
    try:
        no_guard("abc", "ab")
        print("  (no exception — unexpected)")
    except IndexError as e:
        print(f"  without `if len(s1) > len(s2): return False` -> IndexError: {e}")
    print(f"  with the guard: checkInclusion('abc', 'ab') = "
          f"{sol.checkInclusion('abc', 'ab')}")

    # ----------------------------------------------------------------------
    # list == list vs Counter == Counter.
    # ----------------------------------------------------------------------
    print("\n--- comparing frequency maps: list vs Counter ---")
    a26, b26 = [1] * 26, [1] * 26
    ca, cb = Counter("abcdefghijklmnopqrstuvwxyz"), Counter("abcdefghijklmnopqrstuvwxyz")
    t0 = time.perf_counter()
    for _ in range(200_000):
        a26 == b26
    t1 = time.perf_counter()
    for _ in range(200_000):
        ca == cb
    t2 = time.perf_counter()
    print(f"  200000 comparisons:  list {(t1 - t0) * 1000:>7.1f}ms    "
          f"Counter {(t2 - t1) * 1000:>7.1f}ms   "
          f"({(t2 - t1) / (t1 - t0):.0f}x)")
    print("  Same complexity, wildly different constant. With a fixed 26-letter")
    print("  alphabet there is no reason to pay for a hash table.")

    # ----------------------------------------------------------------------
    # The three cost levels, measured.
    # ----------------------------------------------------------------------
    print("\n--- the three cost levels ---")
    print(f"  {'n':>7} {'k':>6} {'match ctr':>11} {'26-list cmp':>13} "
          f"{'Counter cmp':>13} {'sort each':>11}")
    random.seed(0)
    for n, k in ((20_000, 5), (20_000, 100), (20_000, 1_000)):
        s2 = "".join(random.choice("abcde") for _ in range(n))
        s1 = "".join(random.choice("abcde") for _ in range(k))
        t0 = time.perf_counter(); sol.checkInclusion(s1, s2)
        t1 = time.perf_counter(); sol.checkInclusion_compare_lists(s1, s2)
        t2 = time.perf_counter(); sol.checkInclusion_counter(s1, s2)
        t3 = time.perf_counter(); sol.checkInclusion_brute(s1, s2)
        t4 = time.perf_counter()
        print(f"  {n:>7} {k:>6} {(t1 - t0) * 1000:>9.1f}ms "
              f"{(t2 - t1) * 1000:>11.1f}ms {(t3 - t2) * 1000:>11.1f}ms "
              f"{(t4 - t3) * 1000:>9.1f}ms")
    print("  Only the last column grows with k — that is the O(n*k) trap. The")
    print("  first three are all linear in n; they differ by the constant only.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
