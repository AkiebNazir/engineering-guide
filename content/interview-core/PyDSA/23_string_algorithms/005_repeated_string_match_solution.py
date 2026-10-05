"""
================================================================================
SOLUTION · LeetCode 686 · Repeated String Match                     [Medium]
https://leetcode.com/problems/repeated-string-match/
================================================================================

THE CORE IDEA
--------------
Don't search for how many times `b` "fits" -- bound the answer with basic
length arithmetic, then only test the (at most two) candidate counts that
can possibly be correct.

If `b` is ever a substring of `a` repeated `N` times, its occurrence
starts at SOME offset within that big repeated string. Because the big
string is just `a` glued to itself over and over, that starting offset is
equivalent (mod `len(a)`) to starting somewhere inside a single copy of
`a` -- i.e. WLOG the match starts at an offset strictly less than
`len(a)`. From that starting offset, covering `len(b)` more characters
needs at most `len(a) + len(b) - 1` total characters available, which
requires at most `ceil(len(b) / len(a)) + 1` full copies of `a`. So the
answer, if one exists, is ALWAYS either:

    q = ceil(len(b) / len(a))          -- the bare minimum length-wise, or
    q + 1                               -- one extra copy to cover a
                                            boundary-straddling match

Test `b in (a * q)` first; if that fails, test `b in (a * (q + 1))`; if
that also fails, no number of repeats will ever work, so return -1. This
collapses what looks like an open-ended "try increasing repeat counts"
search into exactly two substring checks.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded): start with `repeated = a`,
and while `len(repeated) < len(b)`, keep appending another copy of `a`
and re-checking `b in repeated` after every append, up to some safe bound
(e.g. `len(repeated) > len(b) + len(a)`) before giving up. Correct, but
re-runs a substring search on a growing string after almost every append
-- wasted work compared to knowing in advance exactly which two lengths
can possibly work.

Approach 1 (chosen) -- bounded candidate counts, built-in substring
search: compute `q = ceil(len(b) / len(a))`, test only `a*q` and
`a*(q+1)` using Python's `in` operator (which runs an efficient C-level
substring search, not a naive O(n*m) scan). O(len(a) + len(b)) total work
for the two candidate string constructions and searches; O(len(a) +
len(b)) extra space for the built repeated strings.

Approach 2 (variant, coded below for the cross-check demo) -- same
bounded-candidate-count idea, but substitute an explicit KMP search (the
`_build_lps`/scan machinery from problem 001 in this topic) instead of
relying on the interpreter's built-in `in`. Same asymptotic complexity,
guarantees worst-case-linear substring search independent of the host
language's string implementation -- worth knowing for languages without
a highly-optimized built-in substring search, or when an interviewer
explicitly wants to see you NOT lean on a library call.

Approach 3 (optimization layered on top of either) -- an O(len(a) +
len(b)) early-exit: if `set(b)` contains any character not present in
`set(a)`, `b` can never be a substring of any number of repeats of `a`,
so return -1 immediately without building or searching any string at all.
Cheap and catches a common "obviously impossible" case fast.


================================================================================
STEP BY STEP TRACE
================================================================================
a = "abcd", b = "cdabcdab"

    len(a) = 4, len(b) = 8
    q = ceil(8 / 4) = 2

    Candidate 1: a * 2 = "abcdabcd"  (length 8)
        Is "cdabcdab" a substring of "abcdabcd"? The only length-8
        substring of an 8-character string is the whole string itself,
        "abcdabcd" != "cdabcdab" -> NOT found.

    Candidate 2: a * 3 = "abcdabcdabcd"  (length 12)
        Search for "cdabcdab" inside "abcdabcdabcd":
            index 0: "abcdabcd" -- no
            index 1: "bcdabcda" -- no
            index 2: "cdabcdab" -- MATCH (chars 2..9: c,d,a,b,c,d,a,b)
        Found at index 2 -> b IS a substring of a repeated 3 times.

    Return 3. (Repeating a exactly q=2 times was NOT enough because the
    match straddles the boundary between the 2nd and 3rd copy of "abcd";
    the +1 candidate exists precisely to cover this boundary case.)

a = "a", b = "aa"

    len(a)=1, len(b)=2, q = ceil(2/1) = 2
    Candidate 1: a*2 = "aa". Is "aa" a substring of "aa"? Yes (itself).
    Return 2. (q alone already sufficed here -- the +1 candidate is only
    tried when q fails, so this returns in a single substring check.)

a = "abc", b = "wxyz" (impossible case, character-set early exit)

    set(b) = {'w','x','y','z'}, set(a) = {'a','b','c'}
    set(b) - set(a) = {'w','x','y','z'} -- nonempty -> return -1
    immediately, without ever constructing a*q or a*(q+1).


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                          Time              Space   Mutates input?
    ------------------------------------------------------------------------
    Incremental append+search [priced] O((n+m)^2 / n)*   O(n+m)   no
    Bounded candidates, built-in `in`
    [chosen]                           O(n + m)          O(n+m)   no
    Bounded candidates, explicit KMP
    [variant]                          O(n + m)          O(n+m)   no

    n = len(a), m = len(b). *The incremental approach re-searches a
    string that grows by `n` characters on every iteration, roughly
    `m/n` iterations, each search costing up to O(n+m) -- the product is
    strictly worse than doing exactly two bounded searches.


================================================================================
EDGE CASES
================================================================================
    len(b) < len(a)              -> q = ceil(len(b)/len(a)) = 1; still
                                     might need q+1=2 if the match
                                     straddles a boundary even though b
                                     is shorter than a (e.g. a="abcd",
                                     b="da" needs 2 repeats: "abcdabcd"
                                     contains "da" only at the boundary).
    a == b                       -> q = 1, a*1 contains b trivially -> 1.
    b's character set not a
    subset of a's character set  -> impossible regardless of repeat
                                     count -> -1 (the O(1)-ish early-exit
                                     optimization catches this without
                                     building any string).
    b is a single repeated
    character not in a at all    -> covered by the same character-set
                                     check above.
    very large q (e.g. len(a)=1,
    len(b)=10^4)                  -> q = 10^4; still only TWO candidate
                                     strings of bounded total length are
                                     ever built, never an unbounded
                                     incremental search.


================================================================================
COMMON MISTAKES
================================================================================
1. Only testing `q = ceil(len(b)/len(a))` and stopping there -- misses the
   boundary-straddling case (see the a="abcd", b="cdabcdab" trace above,
   where q=2 fails but q+1=3 succeeds). Both candidates must be checked
   before declaring -1.
2. Using floor division instead of ceiling for `q` -- e.g. `len(b) //
   len(a)` instead of `-(-len(b) // len(a))` (the standard Python
   ceiling-division idiom) under-counts whenever `len(b)` isn't an exact
   multiple of `len(a)`, producing a string too short to possibly contain
   `b` even before considering the +1 boundary case.
3. Forgetting the character-set feasibility check (or skipping it and
   just relying on q/q+1 substring search) -- not a CORRECTNESS bug (the
   substring search still correctly returns "not found"), but wastes time
   building potentially large strings for inputs that are obviously
   impossible in O(1).
4. Testing an unbounded number of increasing repeat counts "to be safe"
   instead of proving (or trusting) that q and q+1 are always sufficient
   -- correct but throws away the actual insight the problem is testing.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you prove q+1 repeats is always enough, if any answer exists at
  all?" -> Any valid match's start offset, taken modulo `len(a)`, is
  equivalent to a start offset strictly less than `len(a)` in a
  sufficiently repeated string (periodicity). From such an offset,
  `len(a) - 1 + len(b)` characters suffice to contain the whole match,
  which needs at most `ceil(len(b)/len(a)) + 1` copies of `a` -- see THE
  CORE IDEA for the full argument.
- "What if `a` and `b` could be enormous (millions of characters)?" ->
  The bounded-candidate approach still only ever builds strings of length
  O(len(a) + len(b)), never something unbounded, so it scales linearly;
  swap the built-in `in` for explicit KMP (Approach 2) if you need a
  language/engine-independent worst-case guarantee.
- "How is this related to Rabin-Karp or KMP more directly?" -> The
  SEARCH step (does `b` occur in the candidate string) is exactly the
  same substring-search problem as LC 28 (this topic, 001) -- everything
  specific to THIS problem is the length-arithmetic that bounds which
  candidate strings are even worth searching.


================================================================================
RELATED PROBLEMS
================================================================================
- Find the Index of the First Occurrence in a String (LC 28, this topic,
  001) -- the actual substring-search subroutine reused here in Approach
  2 (explicit KMP).
- Repeated Substring Pattern (LC 459, this topic, 002) -- "is `s` built
  from repeats of a shorter string" is the INVERSE question of this
  problem's "how many repeats of `a` are needed to contain `b`."
- Rotate String (LC 796) -- another "search inside a doubled/repeated
  string" trick: `s2` is a rotation of `s1` iff `s2` is a substring of
  `s1 + s1`, the same "concatenate to expose boundary-straddling matches"
  idea used here at the +1 candidate.
================================================================================
"""

import time


class Solution:
    def repeatedStringMatch(self, a: str, b: str) -> int:
        if not set(b) <= set(a):
            return -1

        q = -(-len(b) // len(a))  # ceiling division

        candidate = a * q
        if b in candidate:
            return q

        candidate += a
        if b in candidate:
            return q + 1

        return -1


def _incremental_append_baseline(a: str, b: str) -> int:
    """Priced Approach 0: grow the repeated string one copy at a time,
    re-checking after every append, used only for the cross-check demo
    below."""
    if not set(b) <= set(a):
        return -1

    repeated = ""
    count = 0
    limit = len(b) + len(a) + 1  # safe stopping bound
    while len(repeated) < limit:
        repeated += a
        count += 1
        if b in repeated:
            return count
    return -1


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


def _kmp_contains(haystack: str, needle: str) -> bool:
    n, m = len(haystack), len(needle)
    if m == 0:
        return True
    if m > n:
        return False
    lps = _build_lps(needle)
    i = j = 0
    while i < n:
        if haystack[i] == needle[j]:
            i += 1
            j += 1
            if j == m:
                return True
        elif j != 0:
            j = lps[j - 1]
        else:
            i += 1
    return False


def _bounded_candidates_kmp(a: str, b: str) -> int:
    """Priced Approach 2: same bounded-candidate idea, explicit KMP
    search instead of the built-in `in`, used only for the cross-check
    demo below."""
    if not set(b) <= set(a):
        return -1

    q = -(-len(b) // len(a))

    candidate = a * q
    if _kmp_contains(candidate, b):
        return q

    candidate += a
    if _kmp_contains(candidate, b):
        return q + 1

    return -1


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ("abcd", "cdabcdab", 3),
        ("a", "aa", 2),
        ("a", "a", 1),
        ("abc", "wxyz", -1),
        ("abcd", "da", 2),
        ("aaaaaaaaaaaaaaaaaaaaaab", "ba", 2),
        ("abababab", "abababab", 1),
        ("ab", "ababab", 3),
    ]
    for a, b, expected in cases:
        got = sol.repeatedStringMatch(a, b)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  repeatedStringMatch({a!r}, {b!r}) "
              f"-> {got} (expected {expected})")

    print()
    print("CROSS-CHECK -- bounded-candidates vs incremental-append vs KMP variant")
    print("-" * 72)
    import random
    random.seed(31)
    alphabet = "ab"
    mismatch = 0
    for _ in range(1000):
        na = random.randint(1, 8)
        nb = random.randint(1, 12)
        a = "".join(random.choice(alphabet) for _ in range(na))
        b = "".join(random.choice(alphabet) for _ in range(nb))
        r1 = sol.repeatedStringMatch(a, b)
        r2 = _incremental_append_baseline(a, b)
        r3 = _bounded_candidates_kmp(a, b)
        if not (r1 == r2 == r3):
            mismatch += 1
            print(f"  MISMATCH a={a!r} b={b!r}: chosen={r1} incremental={r2} kmp={r3}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {1000 - mismatch}/1000 agree "
          f"({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- bounded-candidates vs incremental-append on a long boundary case")
    print("-" * 72)
    a = "xy" * 4999 + "z"     # length 9999, no short internal period matching 'z' placement
    b = a[-50:] + a[:50]      # straddles the wrap-around boundary by construction
    n_calls = 200

    t0 = time.perf_counter()
    for _ in range(n_calls):
        r_bounded = sol.repeatedStringMatch(a, b)
    bounded_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    for _ in range(n_calls):
        r_incremental = _incremental_append_baseline(a, b)
    incremental_ms = (time.perf_counter() - t0) * 1000

    agree = r_bounded == r_incremental
    all_ok &= agree
    print(f"len(a)={len(a)}, len(b)={len(b)}, result = {r_bounded}")
    print(f"  bounded candidates (q, q+1): {bounded_ms:9.2f} ms for {n_calls} calls")
    print(f"  incremental append:          {incremental_ms:9.2f} ms for {n_calls} calls")
    if bounded_ms > 0:
        print(f"  measured: bounded candidates is "
              f"{incremental_ms / max(bounded_ms, 1e-6):.2f}x faster here -- it builds "
              f"and searches exactly two strings instead of re-searching a string that "
              f"grows on every iteration.")
    print(f"{'PASS' if agree else 'FAIL'}  both approaches agree on the result")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
