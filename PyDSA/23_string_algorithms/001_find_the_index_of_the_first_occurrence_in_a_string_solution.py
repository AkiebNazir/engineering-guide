"""
================================================================================
SOLUTION · LeetCode 28 · Find the Index of the First Occurrence in a String  [Easy]
https://leetcode.com/problems/find-the-index-of-the-first-occurrence-in-a-string/
================================================================================

THE CORE IDEA
--------------
This is "implement `strStr()`," and it exists specifically to test whether
you know KNUTH-MORRIS-PRATT (KMP): the canonical linear-time substring
search. The naive double loop (try every start index `i` in `haystack`,
compare `needle` character by character) is O(n*m) in the worst case,
because a partial match can be thrown away and re-checked from scratch on
every failure -- e.g. matching `needle = "aaaab"` against
`haystack = "aaaaaaaaaa...b"` re-scans up to `len(needle)` characters after
EVERY mismatch.

KMP's insight: when a mismatch happens after matching `j` characters of
`needle`, you already know exactly what the last `j` characters of
`haystack` look like (they equal `needle[0:j]`). Instead of restarting the
needle pointer at 0 and re-comparing characters you've already seen, use a
precomputed **failure function** (`lps`, "longest proper prefix that is
also a suffix") to jump the needle pointer directly to the longest prefix
of `needle` that could still match, WITHOUT ever moving the haystack
pointer backwards. Both pointers only ever move forward, so the whole
search is O(n + m): O(m) to build `lps`, O(n) to scan `haystack` once.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded as the primary answer): for each
start index `i` in `0..n-m`, compare `haystack[i:i+m]` to `needle`
character by character, bail on the first mismatch. O(n*m) worst case
(e.g. `haystack = "aaaa...a"`, `needle = "aaa...ab"`), O(1) extra space
(or O(m) if you slice). Passes LeetCode's test data because it isn't
adversarial, but is the wrong answer to give cold in an interview once
asked to beat O(n*m).

Approach 1 (chosen) -- Knuth-Morris-Pratt: build the `lps` failure array
for `needle` in O(m), then scan `haystack` once in O(n), using `lps` to
skip re-comparisons on a mismatch. O(n + m) time, O(m) extra space for
`lps`. Never backtracks the haystack pointer.

Approach 2 (variant, also coded below for the runtime demo) -- Rabin-Karp
rolling hash: hash `needle` once and every length-`m` window of `haystack`
using a rolling polynomial hash (O(1) to slide the window one character),
compare hashes first and only do a full character-by-character check on a
hash match (to rule out false positives from hash collisions). O(n + m)
expected time, O(1) extra space. Simpler to reason about than KMP's `lps`
array, and the technique generalizes better to *multiple pattern* search
and to problems 004/007 in this same topic, which is why it's worth
knowing alongside KMP rather than instead of it.


================================================================================
STEP BY STEP TRACE
================================================================================
needle = "sad"

Building lps (the failure function):
    lps[0] is always 0 (a single character has no proper prefix).
    length = 0 (length of the current matching prefix), i = 1

    i=1: needle[1]='a' vs needle[length=0]='s' -> mismatch, length==0
         -> lps[1] = 0, i = 2
    i=2: needle[2]='d' vs needle[length=0]='s' -> mismatch, length==0
         -> lps[2] = 0, i = 3 (loop ends, i == len(needle))

    lps = [0, 0, 0]   (no repeated prefix structure in "sad" at all)

haystack = "sadbutsad", needle = "sad", lps = [0, 0, 0]

    i (haystack ptr) = 0, j (needle ptr) = 0
    i=0 j=0: h[0]='s' == n[0]='s' -> i=1, j=1
    i=1 j=1: h[1]='a' == n[1]='a' -> i=2, j=2
    i=2 j=2: h[2]='d' == n[2]='d' -> i=3, j=3
             j == len(needle)=3 -> MATCH at i-j = 3-3 = 0

    Return 0. ("sad" also occurs at index 6, but the FIRST occurrence
    wins -- the scan stops at the first `j == len(needle)`.)

A trace where lps actually matters -- needle = "aabaa", haystack has
"aabaabaa...":

    lps for "aabaa": [0, 1, 0, 1, 2]
    (prefix "a" repeats as a suffix at index 1; after "aabaa" fails to
    extend, the longest prefix that is also a suffix of "aaba" is "a",
    length 1, etc.)

    Suppose haystack = "aabaabaaa" and we're mid-match: we've matched
    "aabaa" (j=5) starting at haystack index 0, then haystack[5]='b' but
    needle would want... actually the mismatch case: after matching
    "aaba" (j=4) the next haystack char differs from needle[4]='a'.
    On mismatch with j=4 != 0: j = lps[j-1] = lps[3] = 1. The needle
    pointer jumps to 1 (not back to 0!) because the algorithm already
    knows the last matched characters end in "a", which is also
    needle's own prefix "a" -- so it re-uses that knowledge instead of
    re-comparing "a" against haystack again. The haystack pointer `i`
    never moves backwards during any of this.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                Time         Space    Mutates input?
    ---------------------------------------------------------------
    Brute force [priced]    O(n*m)       O(1)      no
    KMP [chosen]            O(n + m)     O(m)      no
    Rabin-Karp [variant]    O(n + m) exp O(1)      no

    n = len(haystack), m = len(needle). KMP is worst-case O(n+m) always;
    Rabin-Karp is expected O(n+m) but can degrade to O(n*m) under an
    adversarial hash collision (mitigated with a large prime modulus or
    double hashing, see problems 004 and 007 in this topic).


================================================================================
EDGE CASES
================================================================================
    needle == ""           -> LeetCode's actual constraints guarantee
                               `needle.length >= 1`, but defensively an
                               empty needle matches at index 0 by
                               convention (matches Python's own
                               `"".find("")` behavior and C's `strstr`).
    len(needle) > len(haystack) -> impossible to match; return -1
                               immediately without scanning (the KMP loop
                               naturally returns -1 here too, but an
                               early-exit avoids wasted lps construction
                               on a needle that can never fit).
    needle == haystack     -> match at index 0.
    no match at all        -> e.g. "leetcode" / "leeto" -- KMP's lps-based
                               jumps still terminate in O(n+m), just never
                               hit `j == len(needle)`.
    needle occurs multiple
    times                  -> return the FIRST occurrence's start index;
                               the scan must stop at the first full match,
                               not continue looking for a "better" one.
    repetitive needle
    (e.g. "aaaa")          -> exactly the case that makes brute force
                               O(n*m) and is where lps has real non-zero
                               values that save work.


================================================================================
COMMON MISTAKES
================================================================================
1. Moving the haystack pointer `i` backwards on a mismatch (the brute-force
   instinct) -- defeats the entire point of KMP; `i` must only ever
   increase.
2. Off-by-one in the `lps` construction, e.g. comparing `needle[i]` to
   `needle[length]` but forgetting to only increment `i` in the branch
   where a comparison actually happened (the `length != 0` branch must NOT
   advance `i`, only shrink `length` via `lps[length - 1]`).
3. Returning `i` instead of `i - j` on a full match -- `i` has already
   advanced past the end of the match, the match's START index is
   `i - len(needle)` (equivalently `i - j` once `j == len(needle)`).
4. Forgetting to reset/guard `j` when `needle` is empty -- indexing
   `lps[j - 1]` or `needle[j]` with `j == 0` and no guard raises an
   IndexError.
5. Using Python's built-in `str.find()` in an interview setting -- correct
   answer but demonstrates nothing about string-matching algorithms, which
   is explicitly what this problem tests.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you do this without extra space for `lps`?" -> Not while staying at
  O(n+m) worst case; Rabin-Karp gets you to O(1) extra space but only
  EXPECTED O(n+m) time (an adversarial input can force hash collisions).
  There is a genuine time/space/worst-case trade-off here, not a free
  lunch.
- "What if you need to search for the SAME needle inside many different
  haystacks?" -> Build `lps` (or the rolling hash of `needle`) once,
  reuse it across every search -- amortizes the O(m) preprocessing cost.
- "What if you need to search for MULTIPLE needles in one haystack?" ->
  That's the Aho-Corasick automaton (KMP generalized to a trie of
  patterns with failure links) -- out of scope here but worth naming.
- "How does KMP relate to the Z-function?" -> Both are O(n) preprocessing
  structures over a string; the Z-function directly gives, for every
  suffix, its longest common prefix with the whole string, and can also
  be used to implement substring search (concatenate `needle + '#' +
  haystack` and look for a Z-value equal to `len(needle)`). See problem
  006 (Shortest Palindrome) in this topic, which uses the closely related
  KMP-failure-function-on-a-concatenation trick.


================================================================================
RELATED PROBLEMS
================================================================================
- Repeated Substring Pattern (LC 459, this topic, 002) -- uses the SAME
  `lps`/failure-function idea: `len(s) - lps[-1]` is the smallest period
  of `s`.
- Shortest Palindrome (LC 214, this topic, 006) -- KMP's failure function
  computed on `s + '#' + reverse(s)`.
- Repeated DNA Sequences (LC 187, this topic, 004) and Longest Duplicate
  Substring (LC 1044, this topic, 007) -- both use Rabin-Karp rolling
  hashes, the variant approach here, as their core technique.
- Sliding Window topic (03) -- Rabin-Karp's rolling hash is literally a
  sliding window of fixed width `m`, recomputed in O(1) per slide instead
  of O(m); the "maintain a running aggregate as the window slides" idea
  is identical, just the aggregate is a hash instead of a sum/count.
================================================================================
"""

import time


class Solution:
    def strStr(self, haystack: str, needle: str) -> int:
        n, m = len(haystack), len(needle)
        if m == 0:
            return 0
        if m > n:
            return -1

        lps = self._build_lps(needle)

        i = j = 0
        while i < n:
            if haystack[i] == needle[j]:
                i += 1
                j += 1
                if j == m:
                    return i - j
            elif j != 0:
                j = lps[j - 1]
            else:
                i += 1

        return -1

    @staticmethod
    def _build_lps(pattern: str) -> list:
        m = len(pattern)
        lps = [0] * m
        length = 0
        i = 1
        while i < m:
            if pattern[i] == pattern[length]:
                length += 1
                lps[i] = length
                i += 1
            elif length != 0:
                length = lps[length - 1]
            else:
                lps[i] = 0
                i += 1
        return lps


def _brute_force_strstr(haystack: str, needle: str) -> int:
    """Priced-not-shipped O(n*m) baseline, used only for the measured
    comparison demo below."""
    n, m = len(haystack), len(needle)
    if m == 0:
        return 0
    for i in range(n - m + 1):
        if haystack[i:i + m] == needle:
            return i
    return -1


_RK_BASE = 256
_RK_MOD = (1 << 61) - 1  # large Mersenne prime, avoids collisions in practice


def _rabin_karp_strstr(haystack: str, needle: str) -> int:
    """Priced Rabin-Karp variant, used only for the measured comparison
    demo below (and named in MULTIPLE APPROACHES as Approach 2)."""
    n, m = len(haystack), len(needle)
    if m == 0:
        return 0
    if m > n:
        return -1

    high = pow(_RK_BASE, m - 1, _RK_MOD)

    needle_hash = 0
    window_hash = 0
    for i in range(m):
        needle_hash = (needle_hash * _RK_BASE + ord(needle[i])) % _RK_MOD
        window_hash = (window_hash * _RK_BASE + ord(haystack[i])) % _RK_MOD

    for start in range(n - m + 1):
        if window_hash == needle_hash and haystack[start:start + m] == needle:
            return start
        if start < n - m:
            window_hash = (
                (window_hash - ord(haystack[start]) * high) * _RK_BASE
                + ord(haystack[start + m])
            ) % _RK_MOD

    return -1


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ("sadbutsad", "sad", 0),
        ("leetcode", "leeto", -1),
        ("hello", "ll", 2),
        ("a", "a", 0),
        ("mississippi", "issip", 4),
        ("mississippi", "a", -1),
        ("aaaaa", "bba", -1),
        ("aabaabaaa", "aabaa", 0),
        ("abc", "abc", 0),
        ("abc", "abcd", -1),
    ]
    for haystack, needle, expected in cases:
        got = sol.strStr(haystack, needle)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  strStr({haystack!r}, {needle!r}) "
              f"-> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- KMP vs brute force vs Rabin-Karp, 2000 random cases")
    print("-" * 72)
    import random
    random.seed(7)
    alphabet = "ab"
    mismatch = 0
    for _ in range(2000):
        n = random.randint(1, 40)
        m = random.randint(1, 10)
        h = "".join(random.choice(alphabet) for _ in range(n))
        nd = "".join(random.choice(alphabet) for _ in range(m))
        r1 = sol.strStr(h, nd)
        r2 = _brute_force_strstr(h, nd)
        r3 = _rabin_karp_strstr(h, nd)
        if not (r1 == r2 == r3):
            mismatch += 1
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {2000 - mismatch}/2000 agree "
          f"({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- brute force vs KMP on an adversarial worst-case input")
    print("-" * 72)
    # haystack of many 'a's followed by a 'b'; needle of many 'a's followed
    # by a 'b' -- forces the brute force to re-scan almost the whole
    # needle length after every failed attempt (classic O(n*m) trap).
    n = 20_000
    m = 10_000
    haystack = "a" * n + "b"
    needle = "a" * m + "b"

    t0 = time.perf_counter()
    brute_result = _brute_force_strstr(haystack, needle)
    brute_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    kmp_result = sol.strStr(haystack, needle)
    kmp_ms = (time.perf_counter() - t0) * 1000

    agree = brute_result == kmp_result
    all_ok &= agree
    print(f"haystack len={len(haystack)}, needle len={len(needle)}, "
          f"expected match index = {n - m}")
    print(f"  brute force: {brute_ms:9.2f} ms  -> result {brute_result}")
    print(f"  KMP:         {kmp_ms:9.2f} ms  -> result {kmp_result}")
    if brute_ms > 0:
        print(f"  measured: KMP is {brute_ms / max(kmp_ms, 1e-6):.1f}x faster "
              f"on this adversarial 'almost-all-a-then-b' input.")
    print(f"{'PASS' if agree else 'FAIL'}  brute force and KMP agree on the match index")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
