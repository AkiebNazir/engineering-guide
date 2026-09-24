"""
================================================================================
SOLUTION · LeetCode 459 · Repeated Substring Pattern                  [Easy]
https://leetcode.com/problems/repeated-substring-pattern/
================================================================================

THE CORE IDEA
--------------
`s` is built from repeated copies of some substring `p` if and only if `s`
has a "period" `k < len(s)` such that `s[i] == s[i + k]` for every valid
`i`, AND `len(s)` is a multiple of `k`. Two completely different-looking
techniques both nail this in O(n):

1. **The KMP failure function IS a period detector.** Build the standard
   `lps` array for `s` treated as its own pattern (see problem 001 in this
   topic). `lps[-1]` is the length of the longest proper prefix of `s`
   that is also a suffix. The value `k = len(s) - lps[-1]` is `s`'s
   SMALLEST period (smallest shift under which the string maps onto
   itself). `s` is built from repeats of a substring exactly when that
   period evenly divides the whole length AND is strictly shorter than
   the string (`k < len(s)` -- otherwise the "period" is the whole string
   itself, which isn't a repetition of anything smaller).

2. **The `(s + s)` trick** -- pure cleverness, no explicit failure
   function: concatenate `s` with itself, strip the FIRST and LAST
   character, and check whether the original `s` still occurs as a
   substring somewhere in the middle. If `s` is periodic, doubling it and
   trimming one character off each end can't destroy every occurrence
   (there's always a "shifted" copy landing safely inside); if `s` is NOT
   periodic, no shifted copy can survive the trim. This is a one-liner in
   Python but the reasoning behind WHY it works is exactly the same
   periodicity argument as approach 1 -- it's worth being able to explain
   it, not just recite it.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): try every candidate substring
length `k` that divides `len(s)`, from 1 up to `len(s) // 2`, and check
whether repeating `s[:k]` exactly `len(s) // k` times reconstructs `s`.
O(n^2) worst case (up to O(n) candidate lengths, each an O(n) reconstruct-
and-compare). Correct, but does redundant work the KMP failure function
avoids entirely.

Approach 1 (chosen) -- KMP failure function: build `lps` for `s` in O(n),
then check `lps[-1] != 0 and len(s) % (len(s) - lps[-1]) == 0`. O(n) time,
O(n) extra space for `lps`. This is the answer that demonstrates you
understand WHY it works, and directly reuses the exact same `_build_lps`
helper from problem 001.

Approach 2 (variant, also coded below for the demo) -- the `(s+s)[1:-1]`
substring trick: O(n) time for the concatenation/slice, and Python's
`str.find` (or `in`) is itself an efficient (Boyer-Moore-ish / two-way)
C-level substring search, so this is O(n) in practice despite doing a
"substring search" as its only step. Extremely short to write, but the
correctness argument is subtler and easier to get wrong under pressure
than the failure-function version.


================================================================================
STEP BY STEP TRACE
================================================================================
s = "abcabcabcabc"  (len = 12)

Building lps for "abcabcabcabc" (KMP approach):
    The longest proper prefix that's also a suffix is "abcabcabc"
    (length 9) -- e.g. prefix "abcabcabc" (first 9 chars) equals suffix
    "abcabcabc" (last 9 chars). So lps[-1] = 9.

    period k = len(s) - lps[-1] = 12 - 9 = 3
    len(s) % k == 0?  12 % 3 == 0  -> yes
    k < len(s)?  3 < 12  -> yes
    -> REPEATED (period-3 substring "abc", repeated 4 times)

s = "aba"  (len = 3)
    lps for "aba" = [0, 0, 1]   (prefix "a" == suffix "a", length 1)
    period k = 3 - 1 = 2
    len(s) % k == 0?  3 % 2 = 1 -> NO -> NOT repeated

(s+s)[1:-1] trick on s = "abab":
    s + s            = "abababab"
    [1:-1]           = "bababa"          (drop first 'a', drop last 'b')
    "abab" in "bababa"?  yes, at index 1: b[abab]a -> found
    -> REPEATED

(s+s)[1:-1] trick on s = "aba":
    s + s            = "abaaba"
    [1:-1]           = "baab"
    "aba" in "baab"?  substrings of length 3 are "baa", "aab" -> no match
    -> NOT repeated


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                        Time     Space    Mutates input?
    -------------------------------------------------------------------
    Try every divisor [priced]      O(n^2)   O(n)      no
    KMP failure function [chosen]   O(n)     O(n)      no
    (s+s)[1:-1] substring [variant] O(n)*    O(n)      no

    n = len(s). *`str.find`/`in` on CPython strings runs a highly-tuned
    C-level search (effectively linear in practice for this use), not a
    naive O(n^2) double loop.


================================================================================
EDGE CASES
================================================================================
    len(s) == 1             -> a single character can never be built from
                               a SMALLER repeated substring (the only
                               candidate period is the whole string
                               itself, k < len(s) fails); always False.
                               Both approaches handle this without a
                               special case: lps[-1] for a 1-char string
                               is 0, so k = 1 - 0 = 1 = len(s), which
                               fails the `k < len(s)` check.
    all identical characters
    (e.g. "aaaa")            -> maximally periodic, period = 1; True.
    s itself has no shorter
    period (e.g. "abcd")     -> lps[-1] = 0 for a string with no
                               internal prefix/suffix overlap at all;
                               k = len(s) - 0 = len(s), fails
                               `k < len(s)` -> correctly False.
    period exists but doesn't
    evenly divide the length
    (e.g. "abcabca", period-3
    "abc" but len=7)         -> lps[-1] would be 4 ("abca" prefix/suffix
                               overlap is NOT actually the true period
                               here -- walk it by hand if unsure), the
                               `len(s) % k == 0` check is what rejects
                               false positives like this.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the `lps[-1] != 0` (equivalently `k < len(s)`) guard --
   without it, a string with NO internal repetition still "passes" the
   modulo check trivially (`len(s) % len(s) == 0` is always true), giving
   a false positive on every input.
2. In the `(s+s)[1:-1]` trick, forgetting to slice off BOTH ends -- slicing
   only one end can produce false positives (the untrimmed original `s`
   trivially finds itself at the boundary).
3. Confusing "the longest prefix-suffix overlap" with "the period" without
   the subtraction -- `lps[-1]` is NOT the period, `len(s) - lps[-1]` is.
4. Re-deriving the brute-force O(n^2) divisor-trial approach in an
   interview after already having built `lps` for problem 001 in this
   topic -- the failure function is a two-line reuse once you've written
   it once; re-deriving from scratch under time pressure wastes the
   signal that you retain techniques across problems.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you find the actual repeated substring, not just True/False?" ->
  Yes: once you have the period `k = len(s) - lps[-1]` and know it divides
  `len(s)` evenly, `s[:k]` IS the repeated unit (verify by reconstructing:
  `s[:k] * (len(s) // k) == s`, though it's mathematically already
  established once the modulo check passes).
- "Why does the `(s+s)[1:-1]` trick work?" -> If `s = p * r` for `r >= 2`,
  then `s + s` contains `s` starting at offset `k` (one full copy of `p`)
  as well as offset 0; trimming one char off each end kills the offset-0
  and offset-(len(s)) occurrences but the offset-`k` occurrence (which
  needs `k <= len(s) - 1`, guaranteed since `k < len(s)` when `r >= 2`)
  survives untouched. If `s` has NO period, no shifted self-overlap
  exists anywhere in `s+s` outside those two trivial trimmed-off
  positions, so nothing survives the trim.
- "What's the difference between this and the Z-function approach?" ->
  The Z-function gives, for every position `i`, the length of the longest
  substring starting at `i` that matches a prefix of `s` -- from that you
  can also derive periods (`s` has period `k` iff `Z[k] >= len(s) - k`).
  Same underlying idea (self-overlap structure), different array.


================================================================================
RELATED PROBLEMS
================================================================================
- Find the Index of the First Occurrence in a String (LC 28, this topic,
  001) -- the KMP failure function reused verbatim; this problem is a
  direct application of understanding what `lps` actually measures.
- Shortest Palindrome (LC 214, this topic, 006) -- another problem that
  builds an `lps`-style failure function over a CONCATENATED string
  (`s + '#' + reverse(s)`) to extract a global structural property in
  O(n), the same meta-technique as "the failure function encodes more
  than just where the next KMP-search jump should land."
- Sliding Window topic (03) -- periodicity checks like this one
  occasionally show up disguised as "smallest repeating unit" window
  problems; the failure-function trick is the O(n) escape hatch whenever
  brute-force divisor enumeration would be too slow.
================================================================================
"""

import time


class Solution:
    def repeatedSubstringPattern(self, s: str) -> bool:
        lps = self._build_lps(s)
        n = len(s)
        period = n - lps[-1]
        return lps[-1] != 0 and n % period == 0

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


def _double_and_trim(s: str) -> bool:
    """Priced variant approach, used for the cross-check demo below."""
    return (s + s)[1:-1].find(s) != -1


def _brute_force_divisors(s: str) -> bool:
    """Priced-not-shipped O(n^2) baseline, used only for the measured
    comparison demo below."""
    n = len(s)
    for k in range(1, n // 2 + 1):
        if n % k != 0:
            continue
        candidate = s[:k] * (n // k)
        if candidate == s:
            return True
    return False


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ("abab", True),
        ("aba", False),
        ("abcabcabcabc", True),
        ("a", False),
        ("aa", True),
        ("aaaa", True),
        ("abcd", False),
        ("abcabca", False),
        ("abaababaab", True),   # period 5: "abaab" * 2
        ("xyzxyzxyzxyzxyz", True),
    ]
    for s, expected in cases:
        got = sol.repeatedSubstringPattern(s)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  repeatedSubstringPattern({s!r}) "
              f"-> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- KMP vs (s+s)[1:-1] vs brute force, 3000 random strings")
    print("-" * 72)
    import random
    random.seed(11)
    alphabet = "ab"
    mismatch = 0
    for _ in range(3000):
        n = random.randint(1, 30)
        s = "".join(random.choice(alphabet) for _ in range(n))
        r1 = sol.repeatedSubstringPattern(s)
        r2 = _double_and_trim(s)
        r3 = _brute_force_divisors(s)
        if not (r1 == r2 == r3):
            mismatch += 1
            print(f"  MISMATCH on {s!r}: kmp={r1} trick={r2} brute={r3}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {3000 - mismatch}/3000 agree "
          f"({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- KMP vs brute-force divisor trial on a long periodic string")
    print("-" * 72)
    unit = "abcdefghij"
    s = unit * 2000  # length 20000, period 10 -- brute force checks many divisors

    t0 = time.perf_counter()
    kmp_result = sol.repeatedSubstringPattern(s)
    kmp_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    brute_result = _brute_force_divisors(s)
    brute_ms = (time.perf_counter() - t0) * 1000

    agree = kmp_result == brute_result
    all_ok &= agree
    print(f"len(s)={len(s)}, true period={len(unit)}")
    print(f"  KMP failure function: {kmp_ms:9.3f} ms -> {kmp_result}")
    print(f"  brute force divisors: {brute_ms:9.3f} ms -> {brute_result}")
    if brute_ms > 0:
        print(f"  measured: KMP is {brute_ms / max(kmp_ms, 1e-6):.1f}x faster here.")
    print(f"{'PASS' if agree else 'FAIL'}  both approaches agree")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
