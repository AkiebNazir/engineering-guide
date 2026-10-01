"""
================================================================================
SOLUTION · LeetCode 438 · Find All Anagrams in a String                 [Medium]
https://leetcode.com/problems/find-all-anagrams-in-a-string/
================================================================================

THE CORE IDEA
-------------
Problem 010 (LC 567) with the verdict line changed:

    LC 567:   if matches == 26:  return True
    LC 438:   if matches == 26:  out.append(r - k + 1)

Fixed window of width k = len(p), frequency counts slid one in / one out, and a
match test per position:

    k, n = len(p), len(s)
    if k > n: return []
    need, window = [0] * 26, [0] * 26
    for i in range(k):
        need[ord(p[i]) - 97] += 1
        window[ord(s[i]) - 97] += 1
    out = [0] if need == window else []            # the FIRST window counts
    for r in range(k, n):
        window[ord(s[r]) - 97] += 1                # enter
        window[ord(s[r - k]) - 97] -= 1            # leave
        if need == window:
            out.append(r - k + 1)                  # START index of [r-k+1, r]
    return out

O(26n) time as written, O(n) with the match counter, O(1) auxiliary space plus
the output.


================================================================================
THE INDEX — derive it, do not guess it
================================================================================
After `s[r]` enters and `s[r-k]` leaves, the window spans the k indices

        r-k+1,  r-k+2,  ...,  r

so its START is `r - k + 1`. Sanity-check it on the smallest case: k = 1 and
r = 0 gives `0 - 1 + 1 = 0`. ✓

The three wrong answers people write, and what each produces:

    r          -> the window's LAST index; every answer is too large by k-1
    r - k      -> one before the window; every answer is too small by 1
    l          -> correct only if you are also maintaining an explicit `l`
                  (this is a fixed window, so l is not a separate variable
                  unless you chose to make it one)

⚠️  Unlike LC 567, this error CANNOT HIDE. There the answer was a boolean, so
    an off-by-one in the index was invisible. Here it corrupts every result.
    That is the main reason to do 438 right after 567: it audits the version of
    the algorithm you thought you already knew.

⚠️  AND CHECK THE PRIMED WINDOW. The window built during priming is the one
    starting at index 0, and the loop `for r in range(k, n)` never tests it.
    "abc"/"abc" and "aab"/"aa" both return [] if you forget. Test it before the
    loop, or restructure into a single loop that records when `r >= k-1`.


================================================================================
OCCURRENCES OVERLAP — so you cannot skip ahead
================================================================================
    s = "abab", p = "ab"   ->   [0, 1, 2]

The windows at 0, 1 and 2 overlap heavily. A tempting "optimisation" after a
hit is to jump `r += k` and resume; it is WRONG, and this example is the
counterexample. Anagram occurrences are not disjoint and every start position
must be tested independently.

(Contrast string-search problems where you legitimately skip — KMP's failure
function, Boyer-Moore's bad-character rule. Those skips are justified by a
mismatch, not by a match.)


================================================================================
THE OUTPUT CAN BE Θ(n) — state your space convention
================================================================================
    s = "aaaa...a" (n copies), p = "aa"   ->   n - 1 results

So the answer array alone is Θ(n) in the worst case. The correct statement is:

    Time  O(n)
    Space O(1) AUXILIARY (two 26-slot arrays), plus O(#answers) for the output

Saying "O(1) space" without the qualifier invites the follow-up "but you return
a list that can be length n". Saying "O(n) space" undersells the algorithm.
Name the convention and move on — the usual one is that output does not count
against auxiliary space.

Also note there is NO EARLY EXIT here. LC 567 could return on the first hit and
finish in O(k) on a lucky input; this one is Θ(n) on every input, because every
position must be classified.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = len(s), k = len(p), Σ = 26

    Approach                              Time          Space   Note
    ------------------------------------  ------------  ------  ---------------
    Sort each window                      O(n k log k)  O(k)    the oracle
    Counter(s[i:i+k]) rebuilt per step    O(n k)        O(Σ)    the slicing trap
    Slide + compare 26-lists ✅           O(Σ n)        O(1)    short, fast
    Slide + Counter comparison            O(Σ n)        O(Σ)    ~100x slower cmp
    Slide + match counter ✅              O(n)          O(1)    strict O(n)

    (plus O(#answers) output in every row)

    ⚠️  `Counter == Counter` measured ~100x slower than `list == list` over
        200k comparisons. Same complexity class, very different wall clock. With
        a guaranteed 26-letter alphabet, use a list.


================================================================================
EDGE CASES
================================================================================
    len(p) > len(s)   "ab"/"abc" -> []. Must be checked BEFORE priming or
                      `s[i]` raises IndexError.

    len(p) == len(s)  "abc"/"abc" -> [0]. Exactly one window, and it is the
                      primed one — the loop body never executes. THE detector
                      for "forgot to test the first window".

    k == 1            "bbbbb"/"b" -> [0,1,2,3,4]. Every position. Exercises
                      `r - k + 1` at its smallest.

    overlapping hits  "abab"/"ab" -> [0,1,2]. Rules out skipping ahead by k.

    max output        "aaaaa"/"aa" -> [0,1,2,3]. The Θ(n) output case.

    match at the ends "aab"/"aa" -> [0] (start) and "baa"/"aa" -> [1] (end).
                      Together they pin both loop bounds.

    no common letters "zzz"/"aa" -> []. `matches` stays below 26 throughout.

    empty result      Return `[]`, not `None`. A function that falls off the
                      end returns None and fails the judge with a confusing
                      error.


================================================================================
COMMON MISTAKES
================================================================================
1. Appending `r` instead of `r - k + 1`. Every index is off by k-1.

2. Never testing the primed window, so a match at index 0 is missed. "abc"/"abc"
   returns [] instead of [0].

3. Rebuilding the window's Counter each step — O(n*k).

4. Skipping ahead after a hit. Occurrences overlap; "abab"/"ab" proves it.

5. Not guarding `len(p) > len(s)` -> IndexError during priming.

6. Comparing sorted substrings inside the loop (`sorted(s[i:i+k]) == sorted(p)`).
   Correct but O(n k log k), and it re-sorts `p` every iteration unless you
   hoist it.

7. Returning a set, or the substrings themselves, instead of a list of start
   indices.

8. Claiming O(1) space without the "auxiliary, excluding output" qualifier when
   the output can be Θ(n).

9. Using `defaultdict(int)` and then comparing with `==` against a `Counter`.
   That comparison can behave differently from a Counter-to-Counter comparison
   once zero-valued keys appear — Counter equality ignores zeros, plain dict
   equality does not. Keep both sides the same type, or use lists.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Return just the COUNT of anagram occurrences.
A: Replace the list with an integer. Space drops to a true O(1) with no output
   caveat.

Q: The alphabet is Unicode.
A: Swap the 26-lists for dicts, and use the match counter (`matches ==
   len(need)`) so you never compare whole maps — that comparison is O(Σ) and Σ
   is now unbounded. Count only the characters that appear in `p`.

Q: Find anagrams of p in a STREAM of characters.
A: Keep the last k characters in a `deque(maxlen=k)` and read the element about
   to be evicted before appending. State is O(k + Σ).

Q: Find all anagrams of ANY of m different patterns, all of the same length?
A: One window, and a hash of the frequency vector looked up in a set of the m
   target hashes. O(n + m*k). If the patterns have different lengths you need
   one window per distinct length.

Q: What if p can contain characters not in s at all?
A: Nothing changes — those letters simply never reach their required count, so
   `matches` never hits 26.

Q: Could you use a rolling hash instead?
A: Yes — hash the frequency vector, or use a product/sum of prime codes per
   character, which is order-independent by construction. It buys nothing here
   (the frequency array is already O(1) to compare for a fixed alphabet) and it
   introduces collision risk. Worth naming as the technique that DOES matter
   when the alphabet is huge.

Q: How does this relate to LC 567?
A: Identical algorithm; 567 short-circuits on the first hit. Being able to say
   "it's the same window, one line different" is exactly the right answer.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 567  Permutation in String          — problem 010; the boolean version
    LC 242  Valid Anagram                  — the single-window base case
    LC 76   Minimum Window Substring       — problem 015; variable width, >=
    LC 30   Substring with Concatenation   — the same idea over WORDS
            of All Words
    LC 1002 Find Common Characters         — frequency intersection, no window
    LC 49   Group Anagrams                 — canonical form as a hash key
            (topic 01, problem 007)
================================================================================
"""

import random
import time
from collections import Counter
from typing import List


class Solution:
    def findAnagrams(self, s: str, p: str) -> List[int]:
        """Fixed window + match counter. O(n) time, O(1) auxiliary space."""
        k, n = len(p), len(s)
        out: List[int] = []
        if k > n:
            return out

        need = [0] * 26
        window = [0] * 26
        for i in range(k):
            need[ord(p[i]) - 97] += 1
            window[ord(s[i]) - 97] += 1

        matches = sum(need[i] == window[i] for i in range(26))
        if matches == 26:
            out.append(0)                          # the PRIMED window counts

        for r in range(k, n):
            i = ord(s[r]) - 97                     # ENTER
            window[i] += 1
            if window[i] == need[i]:
                matches += 1
            elif window[i] == need[i] + 1:
                matches -= 1

            j = ord(s[r - k]) - 97                 # LEAVE
            window[j] -= 1
            if window[j] == need[j]:
                matches += 1
            elif window[j] == need[j] - 1:
                matches -= 1

            if matches == 26:
                out.append(r - k + 1)              # START of the span [r-k+1, r]
        return out

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def findAnagrams_compare_lists(self, s: str, p: str) -> List[int]:
        """Slide the counts, compare the two 26-lists each step. O(26n).

        The version to write first: three fewer branches to get wrong.
        """
        k, n = len(p), len(s)
        if k > n:
            return []
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(p[i]) - 97] += 1
            window[ord(s[i]) - 97] += 1
        out = [0] if need == window else []
        for r in range(k, n):
            window[ord(s[r]) - 97] += 1
            window[ord(s[r - k]) - 97] -= 1
            if need == window:
                out.append(r - k + 1)
        return out

    def findAnagrams_single_loop(self, s: str, p: str) -> List[int]:
        """One loop, no priming — the shape that cannot forget the first window.

        Uses the LC 643 bounds: evict when `r >= k`, record when `r >= k-1`.
        """
        k, n = len(p), len(s)
        if k > n:
            return []
        need, window = [0] * 26, [0] * 26
        for ch in p:
            need[ord(ch) - 97] += 1
        out = []
        for r, ch in enumerate(s):
            window[ord(ch) - 97] += 1                  # enter
            if r >= k:
                window[ord(s[r - k]) - 97] -= 1        # leave
            if r >= k - 1 and window == need:          # window is exactly k wide
                out.append(r - k + 1)
        return out

    def findAnagrams_counter(self, s: str, p: str) -> List[int]:
        """Counter version. Same complexity, much slower comparison.

        Counter equality ignores zero-valued keys, so no `del` is needed here —
        but do NOT mix a Counter with a plain dict on the two sides.
        """
        k, n = len(p), len(s)
        if k > n:
            return []
        need = Counter(p)
        window = Counter(s[:k])
        out = [0] if window == need else []
        for r in range(k, n):
            window[s[r]] += 1
            window[s[r - k]] -= 1
            if window == need:
                out.append(r - k + 1)
        return out

    def countAnagrams(self, s: str, p: str) -> int:
        """Follow-up: just the count. True O(1) space, no output caveat."""
        return len(self.findAnagrams(s, p))

    def findAnagrams_brute(self, s: str, p: str) -> List[int]:
        """O(n k log k) oracle: sort every window."""
        k, target = len(p), sorted(p)
        return [i for i in range(len(s) - k + 1) if sorted(s[i:i + k]) == target]

    # ------------------------------------------------------------------
    # Deliberate breakages.
    # ------------------------------------------------------------------
    def findAnagrams_wrong_index(self, s: str, p: str) -> List[int]:
        """✗ BROKEN — appends `r` (the window's LAST index) instead of the
        first. Every answer is too large by k-1."""
        k, n = len(p), len(s)
        if k > n:
            return []
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(p[i]) - 97] += 1
            window[ord(s[i]) - 97] += 1
        out = [0] if need == window else []
        for r in range(k, n):
            window[ord(s[r]) - 97] += 1
            window[ord(s[r - k]) - 97] -= 1
            if need == window:
                out.append(r)                       # should be r - k + 1
        return out

    def findAnagrams_skip_first(self, s: str, p: str) -> List[int]:
        """✗ BROKEN — never tests the primed window. Misses a match at 0."""
        k, n = len(p), len(s)
        if k > n:
            return []
        need, window = [0] * 26, [0] * 26
        for i in range(k):
            need[ord(p[i]) - 97] += 1
            window[ord(s[i]) - 97] += 1
        out = []                                     # the primed window is lost
        for r in range(k, n):
            window[ord(s[r]) - 97] += 1
            window[ord(s[r - k]) - 97] -= 1
            if need == window:
                out.append(r - k + 1)
        return out

    def findAnagrams_skip_ahead(self, s: str, p: str) -> List[int]:
        """✗ BROKEN — jumps k positions after a hit. Occurrences OVERLAP."""
        k, n = len(p), len(s)
        if k > n:
            return []
        need = Counter(p)
        out, i = [], 0
        while i <= n - k:
            if Counter(s[i:i + k]) == need:
                out.append(i)
                i += k                               # ✗ overlapping hits lost
            else:
                i += 1
        return out


# ==============================================================================
# TESTS — run:  python 011_find_all_anagrams_in_a_string_solution.py
# ==============================================================================
CASES = [
    ("cbaebabacd", "abc"), ("abab", "ab"), ("a", "a"), ("a", "b"),
    ("ab", "abc"), ("aaaaa", "aa"), ("abc", "abc"), ("baa", "aa"),
    ("aab", "aa"), ("aabb", "ab"), ("xxyyzz", "xy"), ("abacbabc", "abc"),
    ("zzz", "aa"), ("aaab", "ab"), ("bbbbb", "b"),
]


def run_tests() -> None:
    sol = Solution()
    impls = [
        ("match counter O(n) ", sol.findAnagrams),
        ("compare 26-lists   ", sol.findAnagrams_compare_lists),
        ("single loop, no prime", sol.findAnagrams_single_loop),
        ("Counter comparison ", sol.findAnagrams_counter),
    ]

    all_ok = True
    for name, fn in impls:
        ok = all(fn(a, b) == sol.findAnagrams_brute(a, b) for a, b in CASES)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(CASES)} cases)")

    ok = all(sol.countAnagrams(a, b) == len(sol.findAnagrams_brute(a, b))
             for a, b in CASES)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  count-only variant")

    # ----------------------------------------------------------------------
    # Randomised cross-check against the sorting oracle.
    # ----------------------------------------------------------------------
    print("\n--- randomised cross-check vs the sorting oracle ---")
    random.seed(438)
    trials, mismatches = 6000, 0
    for _ in range(trials):
        a = "".join(random.choice("abc") for _ in range(random.randint(1, 14)))
        b = "".join(random.choice("abc") for _ in range(random.randint(1, 5)))
        want = sol.findAnagrams_brute(a, b)
        for _, fn in impls:
            if fn(a, b) != want:
                mismatches += 1
    print(f"  {trials} random (s, p) x {len(impls)} implementations: "
          f"{mismatches} mismatches")
    all_ok &= (mismatches == 0)

    # ----------------------------------------------------------------------
    # The window, traced — with the index arithmetic spelled out.
    # ----------------------------------------------------------------------
    s, p = "cbaebabacd", "abc"
    k = len(p)
    print(f"\n--- the window over s={s!r} with p={p!r} (k={k}) ---")
    print(f"  {'r':>2} {'span':>8} {'r-k+1':>6} {'window':>7} {'match?':>7}")
    need, window = [0] * 26, [0] * 26
    for i in range(k):
        need[ord(p[i]) - 97] += 1
        window[ord(s[i]) - 97] += 1
    hit = need == window
    print(f"  {k-1:>2} {f'[0, {k-1}]':>8} {0:>6} {s[:k]!r:>7} "
          f"{'YES' if hit else 'no':>7}")
    for r in range(k, len(s)):
        window[ord(s[r]) - 97] += 1
        window[ord(s[r - k]) - 97] -= 1
        hit = need == window
        print(f"  {r:>2} {f'[{r-k+1}, {r}]':>8} {r-k+1:>6} "
              f"{s[r-k+1:r+1]!r:>7} {'YES' if hit else 'no':>7}")
    print(f"  answer = {sol.findAnagrams(s, p)}")
    print("  The window spans [r-k+1, r], so the START index is r-k+1. Derive")
    print("  it from the span; do not memorise it.")

    # ----------------------------------------------------------------------
    # ⚠️  The three index/structure errors.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  the errors that a boolean answer (LC 567) would have hidden ---")
    print(f"  {'s':<13} {'p':<6} {'correct':>14} {'append r':>14} "
          f"{'skip first':>12} {'jump by k':>12}")
    for a, b in ("cbaebabacd", "abc"), ("abab", "ab"), ("abc", "abc"), \
                ("aab", "aa"), ("aaaaa", "aa"):
        print(f"  {a!r:<13} {b!r:<6} {str(sol.findAnagrams(a, b)):>14} "
              f"{str(sol.findAnagrams_wrong_index(a, b)):>14} "
              f"{str(sol.findAnagrams_skip_first(a, b)):>12} "
              f"{str(sol.findAnagrams_skip_ahead(a, b)):>12}")
    print("  append r   -> every index too large by k-1.")
    print("  skip first -> a match at index 0 is silently dropped.")
    print("  jump by k  -> loses OVERLAPPING occurrences ('abab' / 'ab').")

    # ----------------------------------------------------------------------
    # The output can be Theta(n).
    # ----------------------------------------------------------------------
    print("\n--- how big can the answer be? ---")
    print(f"  {'n':>7} {'p':>5} {'#answers':>10}  s")
    for n in (5, 10, 20):
        s_all = "a" * n
        res = sol.findAnagrams(s_all, "aa")
        print(f"  {n:>7} {'aa':>5} {len(res):>10}  {s_all!r}")
    print("  n - k + 1 results. So: TIME O(n), AUXILIARY space O(1), OUTPUT")
    print("  space O(#answers) = O(n). State the convention you are using.")
    print("  There is also no early exit here — unlike LC 567, every position")
    print("  must be classified, so this is Theta(n) on every input.")

    # ----------------------------------------------------------------------
    # list vs Counter comparison.
    # ----------------------------------------------------------------------
    print("\n--- comparing frequency maps: list vs Counter ---")
    a26, b26 = [1] * 26, [1] * 26
    ca = Counter("abcdefghijklmnopqrstuvwxyz")
    cb = Counter("abcdefghijklmnopqrstuvwxyz")
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

    # ----------------------------------------------------------------------
    # The four implementations, timed.
    # ----------------------------------------------------------------------
    print("\n--- the implementations at scale ---")
    print(f"  {'n':>7} {'k':>6} {'match ctr':>11} {'26-list':>10} "
          f"{'Counter':>10} {'sort each':>11}")
    random.seed(0)
    for n, k in ((30_000, 5), (30_000, 100), (30_000, 1_000)):
        s_big = "".join(random.choice("abcde") for _ in range(n))
        p_big = "".join(random.choice("abcde") for _ in range(k))
        t0 = time.perf_counter(); sol.findAnagrams(s_big, p_big)
        t1 = time.perf_counter(); sol.findAnagrams_compare_lists(s_big, p_big)
        t2 = time.perf_counter(); sol.findAnagrams_counter(s_big, p_big)
        t3 = time.perf_counter(); sol.findAnagrams_brute(s_big, p_big)
        t4 = time.perf_counter()
        print(f"  {n:>7} {k:>6} {(t1 - t0) * 1000:>9.1f}ms "
              f"{(t2 - t1) * 1000:>8.1f}ms {(t3 - t2) * 1000:>8.1f}ms "
              f"{(t4 - t3) * 1000:>9.1f}ms")
    print("  Only the last column grows with k. The match counter beats the")
    print("  26-list comparison by roughly the alphabet factor.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
