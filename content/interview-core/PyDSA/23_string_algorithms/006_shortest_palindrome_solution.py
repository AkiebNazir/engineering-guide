"""
================================================================================
SOLUTION · LeetCode 214 · Shortest Palindrome                          [Hard]
https://leetcode.com/problems/shortest-palindrome/
================================================================================

THE CORE IDEA
--------------
You may only PREPEND characters, never insert them in the middle or
append at the end. That constraint pins down exactly what the optimal
prepend has to be: find the LONGEST prefix of `s` that is already a
palindrome, of length `L`. Everything after that prefix, `s[L:]`, has to
become a mirrored "cap" on the front -- prepend `reverse(s[L:])` and the
whole thing reads the same forwards and backwards, and it's provably the
SHORTEST such palindrome (any shorter prepend would have to leave some
suffix of `s[L:]` unmirrored, breaking symmetry; the palindromic prefix
of length `L` is exactly the part of `s` that doesn't need any help).

Finding "the longest palindromic PREFIX" (not substring -- specifically
anchored at index 0) in O(n) is a beautiful reuse of the KMP failure
function from problem 001 in this topic, applied to a CONSTRUCTED string
rather than a literal pattern-search: build

    t = s + '#' + reverse(s)

(the `'#'` is a separator character guaranteed not to appear in `s`,
which prevents any overlap match from crossing between the two halves in
a way that would over-count). Compute `t`'s KMP failure array `lps` the
usual way. The value `lps[-1]` -- the longest proper prefix of `t` that's
also a suffix of `t` -- turns out to be EXACTLY the length of the longest
palindromic prefix of `s`. Why: a suffix of `t` of length `k <= len(s)`
is the last `k` characters of `reverse(s)`, which is `reverse(s[:k])`.
For that suffix to also equal a prefix of `t` of the same length (which,
since `k <= len(s)`, must be `s[:k]`, because `t` begins with `s` itself),
we need `reverse(s[:k]) == s[:k]` -- i.e. `s[:k]` IS a palindrome. `lps`
finds the LARGEST such `k` in one linear pass, and the separator ensures
`k` can never spuriously reach `len(s) + 1` or beyond (matching across
the `'#'` boundary is structurally impossible since `'#'` appears nowhere
else in `t`).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, coded below only for the cross-check
demo): try candidate cut points from the LARGEST possible palindromic
prefix downward -- for `i` from 0 up to `len(s)`, check whether `s[:len(s)
- i]` is a palindrome (a direct `s == s[::-1]`-style O(n) check per
candidate); the first (largest-prefix) one found wins. O(n^2) worst case
(up to n candidate cut points, each an O(n) palindrome check) -- e.g. `s =
"aaaa...ab"` forces almost every cut point to be checked.

Approach 1 (chosen) -- KMP failure function on `s + '#' + reverse(s)`:
build the concatenation in O(n), compute its `lps` array in O(n), read
off the longest palindromic prefix length directly as `lps[-1]`, then
construct the answer as `reverse(s[L:]) + s` in O(n). O(n) total time,
O(n) extra space for the concatenated string and its `lps` array.

Approach 2 (variant, described, not separately coded) -- Manacher's
algorithm: compute the longest palindromic substring CENTERED at (or
including) index 0 directly, without ever concatenating `s` with its own
reverse. Same O(n) time bound via a different mechanism (Manacher expands
palindromes around centers with a clever "don't re-expand what a
previous center already proved" reuse, rather than a failure function on
a concatenated string). Worth naming as an alternative O(n) route to the
same answer, but KMP-on-concatenation is the more directly transferable
skill within this topic since it reuses machinery you already built for
problem 001.

Approach 3 (variant, priced, not coded) -- Rabin-Karp double hashing:
binary search on candidate prefix length `k`, and for each candidate
check `hash(s[:k]) == hash(reverse(s[:k]))` using a precomputed rolling
hash of `s` and of `reverse(s)` (O(1) per check after O(n) preprocessing).
O(n log n) total -- strictly worse than the O(n) KMP approach here, but
the exact same rolling-hash machinery as problem 007's Longest Duplicate
Substring, worth naming as "the same tool, different assembly."


================================================================================
STEP BY STEP TRACE
================================================================================
s = "abcd"  (Example 2)

    reverse(s) = "dcba"
    t = "abcd" + "#" + "dcba" = "abcd#dcba"   (indices 0..8)

    Building lps for t = a b c d # d c b a :
        lps[0] = 0
        i=1: t[1]='b' vs t[0]='a' -> mismatch, length=0 -> lps[1]=0
        i=2: t[2]='c' vs t[0]='a' -> mismatch -> lps[2]=0
        i=3: t[3]='d' vs t[0]='a' -> mismatch -> lps[3]=0
        i=4: t[4]='#' vs t[0]='a' -> mismatch -> lps[4]=0
        i=5: t[5]='d' vs t[0]='a' -> mismatch -> lps[5]=0
        i=6: t[6]='c' vs t[0]='a' -> mismatch -> lps[6]=0
        i=7: t[7]='b' vs t[0]='a' -> mismatch -> lps[7]=0
        i=8: t[8]='a' vs t[length=0]='a' -> MATCH -> length=1, lps[8]=1

        lps = [0,0,0,0,0,0,0,0,1]   ->   lps[-1] = 1

    Longest palindromic prefix length L = 1 (just "a" -- a single
    character is trivially a palindrome; "ab" is not).

    Answer = reverse(s[1:]) + s = reverse("bcd") + "abcd"
           = "dcb" + "abcd" = "dcbabcd"     matches expected output.

s = "aacecaaa"  (Example 1)

    reverse(s) = "aaacecaa"
    Longest palindromic PREFIX of "aacecaaa": check candidates from the
    full string down:
        "aacecaaa" (len 8) reversed = "aaacecaa" -- NOT equal, not a
            palindrome.
        "aacecaa"  (len 7) reversed = "aacecaa"  -- EQUAL, IS a
            palindrome. This is the longest one (verified by the KMP
            construction on t = s + '#' + reverse(s) giving lps[-1] = 7,
            following the exact same mechanism traced above for "abcd").

    L = 7. Answer = reverse(s[7:]) + s = reverse("a") + "aacecaaa"
                   = "a" + "aacecaaa" = "aaacecaaa"   matches expected.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                             Time        Space   Mutates input?
    -----------------------------------------------------------------------
    Try every cut point [priced]         O(n^2)      O(n)     no
    KMP on s+'#'+reverse(s) [chosen]     O(n)        O(n)     no
    Manacher's algorithm [variant]       O(n)        O(n)     no
    Rabin-Karp + binary search [priced]  O(n log n)  O(n)     no

    n = len(s).


================================================================================
EDGE CASES
================================================================================
    s == ""                     -> already a (trivial, empty) palindrome;
                                    L = len(s) = 0 falls out naturally
                                    (t degenerates to just "#", lps[-1]=0,
                                    reverse(s[0:]) + s = "" + "" = "").
    s already a palindrome
    (e.g. "racecar")            -> L = len(s), s[L:] is empty, nothing
                                    to prepend -> return s unchanged.
    single character            -> trivially a palindrome, L=1, return
                                    s unchanged.
    no palindromic prefix longer
    than 1 char (e.g. "abcd")   -> L=1 (a single character is ALWAYS a
                                    palindrome, so L is never 0 for
                                    nonempty s) -- the whole rest of the
                                    string gets mirrored and prepended,
                                    worst case for output length.
    the separator character
    itself appearing in `s`     -> would break the "no spurious overlap"
                                    guarantee; must pick a `'#'`-like
                                    character NOT in the problem's
                                    allowed alphabet (lowercase English
                                    letters only, so any non-letter works
                                    safely -- '#' is a safe, conventional
                                    choice here).


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the separator character between `s` and `reverse(s)` --
   without it, the failure function can find spurious overlaps that
   cross the boundary between the two halves, over-counting `L` and
   producing a "palindrome" that isn't actually one.
2. Using a separator that CAN appear in `s` (e.g. reusing a regular
   letter, or no separator at all) -- same corruption as above, just
   harder to notice since it only breaks on specific adversarial inputs.
3. Confusing "longest palindromic SUBSTRING" (any position) with "longest
   palindromic PREFIX" (anchored at index 0) -- this problem needs the
   latter specifically, since only prepending is allowed; a palindrome
   buried in the middle of `s` is irrelevant to the answer.
4. Off-by-one when slicing: the answer is `reverse(s[L:]) + s`, NOT
   `reverse(s[:L]) + s` (that would re-mirror the part that's already a
   palindrome, which is redundant but also usually just wrong length) --
   the part being mirrored and prepended is the part AFTER the
   palindromic prefix, not the prefix itself.
5. Recomputing the palindrome check from scratch for every candidate cut
   point (the O(n^2) brute force) after already having built `lps` once
   -- once `lps[-1]` is known, the whole answer is O(n) construction,
   no further palindrome-checking needed.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why does concatenating with a separator work here but plain
  concatenation wouldn't?" -> Without a separator, the boundary between
  `s` and `reverse(s)` could accidentally align in a way that makes the
  failure function believe a longer prefix/suffix overlap exists than is
  actually justified by `s`'s own internal palindrome structure -- the
  separator (a character guaranteed absent from `s`) makes any such
  cross-boundary match impossible by construction.
- "Could you solve this with Manacher's algorithm instead?" -> Yes:
  Manacher's gives the longest palindrome CENTERED at or extending from
  index 0 directly, in O(n), without ever building a concatenated
  string -- functionally equivalent output, different mechanism (center
  expansion with reuse of previously computed radii, vs. a failure
  function over a constructed string).
- "What if you could prepend OR append?" -> That's a materially different
  (and generally harder/different) problem -- you'd be looking for the
  longest palindromic SUBSTRING anchored at either end, or in the general
  "minimum insertions to make a palindrome" formulation, an edit-distance
  / interval DP problem entirely, not a single-pass failure-function
  trick.


================================================================================
RELATED PROBLEMS
================================================================================
- Find the Index of the First Occurrence in a String (LC 28, this topic,
  001) -- the `_build_lps` helper is reused completely unchanged; this
  problem is really "apply the KMP failure function to a CONSTRUCTED
  string instead of a literal needle/haystack pair," the same mechanism
  wearing a different hat.
- Repeated Substring Pattern (LC 459, this topic, 002) -- another problem
  that reads global structural information (there: periodicity; here:
  longest palindromic prefix) out of the SAME `lps` array shape, applied
  to a different constructed string.
- Longest Palindromic Substring (LC 5) -- the general (not
  prefix-anchored) version of "find a long palindrome in `s`," typically
  solved with expand-around-center (O(n^2)) or Manacher's (O(n)).
- Valid Palindrome (LC 125, topic 02) and Valid Palindrome II (LC 680,
  topic 02) -- the two-pointer palindrome CHECK that this problem's
  brute-force baseline calls repeatedly per candidate.
================================================================================
"""

import time


class Solution:
    def shortestPalindrome(self, s: str) -> str:
        if len(s) <= 1:
            return s

        t = s + '#' + s[::-1]
        lps = self._build_lps(t)
        longest_pal_prefix = lps[-1]

        return s[longest_pal_prefix:][::-1] + s

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


def _brute_force_shortest_palindrome(s: str) -> str:
    """Priced O(n^2) baseline: try every cut point from the longest
    possible palindromic prefix downward, used only for the measured
    comparison demo below."""
    n = len(s)
    for cut in range(n + 1):
        prefix = s[:n - cut]
        if prefix == prefix[::-1]:
            return s[n - cut:][::-1] + s
    return s  # unreachable for n >= 0 since cut == n gives an empty prefix


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    def is_palindrome(x: str) -> bool:
        return x == x[::-1]

    cases = [
        ("aacecaaa", "aaacecaaa"),
        ("abcd", "dcbabcd"),
        ("", ""),
        ("a", "a"),
        ("aa", "aa"),
        ("ab", "bab"),
        ("racecar", "racecar"),
        ("aabba", "abbaabba"),
    ]

    for s, expected in cases:
        got = sol.shortestPalindrome(s)
        ok = got == expected and is_palindrome(got) and got.endswith(s)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  shortestPalindrome({s!r}) -> {got!r} "
              f"(expected {expected!r}, is_palindrome={is_palindrome(got)}, "
              f"ends_with_s={got.endswith(s)})")

    print()
    print("CROSS-CHECK -- KMP-based vs brute force, 800 random strings")
    print("-" * 72)
    import random
    random.seed(37)
    alphabet = "ab"
    mismatch = 0
    for _ in range(800):
        n = random.randint(0, 20)
        s = "".join(random.choice(alphabet) for _ in range(n))
        r1 = sol.shortestPalindrome(s)
        r2 = _brute_force_shortest_palindrome(s)
        if r1 != r2 or not is_palindrome(r1) or not r1.endswith(s):
            mismatch += 1
            print(f"  MISMATCH on {s!r}: kmp={r1!r} brute={r2!r}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {800 - mismatch}/800 agree "
          f"({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- KMP-on-concatenation vs brute force on a worst-case input")
    print("-" * 72)
    # A single palindromic character at the front followed by all-distinct
    # noise forces the O(n^2) brute force to check almost every cut point.
    n = 3000
    s = "a" + "".join("bc"[i % 2] for i in range(n))  # "a" then alternating "bcbcbc..."

    t0 = time.perf_counter()
    kmp_result = sol.shortestPalindrome(s)
    kmp_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    brute_result = _brute_force_shortest_palindrome(s)
    brute_ms = (time.perf_counter() - t0) * 1000

    agree = kmp_result == brute_result
    all_ok &= agree
    print(f"len(s)={len(s)}")
    print(f"  KMP on s+'#'+reverse(s): {kmp_ms:9.3f} ms")
    print(f"  brute force cut points:  {brute_ms:9.3f} ms")
    if kmp_ms > 0:
        print(f"  measured: KMP is {brute_ms / max(kmp_ms, 1e-6):.1f}x faster here.")
    print(f"{'PASS' if agree else 'FAIL'}  both approaches agree")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
