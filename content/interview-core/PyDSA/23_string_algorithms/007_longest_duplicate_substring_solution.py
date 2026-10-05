"""
================================================================================
SOLUTION · LeetCode 1044 · Longest Duplicate Substring                 [Hard]
https://leetcode.com/problems/longest-duplicate-substring/
================================================================================

THE CORE IDEA
--------------
Two separate ideas stack on top of each other here, and BOTH are required:

1. **Binary search on the ANSWER LENGTH, not the answer itself.** The
   predicate "does `s` contain SOME duplicated substring of length `L`?"
   is MONOTONE: if a duplicate of length `L` exists, a duplicate of every
   shorter length `L' < L` also exists (just truncate the match). So as
   `L` increases from 1 to `n-1`, the predicate flips from True to False
   exactly once -- textbook "search on the answer space" (see topic 05).
   Binary search over `L` turns "find the longest working length" into
   O(log n) calls to a "does a length-L duplicate exist?" checker.

2. **Rabin-Karp rolling hash to answer that checker in O(n).** For a
   fixed `L`, slide a window of length `L` across `s`, maintaining a
   polynomial rolling hash updated in O(1) per slide (exactly the
   sliding-window-as-a-running-aggregate mechanism from topic 03, with
   the aggregate being a hash instead of a sum). Store every hash seen in
   a dict; the moment a hash repeats, you have a CANDIDATE duplicate.

The subtlety that makes this a Hard problem, not just "KMP but bigger":
a hash match is not proof of an actual substring match -- two genuinely
different length-L substrings CAN hash to the same value (a pigeonhole
collision). With `n` up to 3*10^4 and `L` up to `n-1`, a naive small
modulus WILL produce real collisions on adversarial or even just
moderately large random inputs. The fix used here is two-layered: use a
large modulus (`2^61 - 1`, a Mersenne prime, giving ~2*10^18 buckets) to
make collisions rare, AND -- non-negotiably -- verify every hash match
with a direct `s[i:i+L] == s[j:j+L]` character comparison before trusting
it. The big modulus keeps verification cheap (rare, not the common case);
the verification step is what makes the algorithm CORRECT regardless of
modulus, not just "probably correct." The demo below deliberately uses a
tiny modulus to manufacture a real collision and show why skipping
verification would silently return a wrong answer.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, coded below only for the cross-check
demo on small inputs): for each length `L` from `n-1` down to 1, hash (or
directly set-compare) every length-`L` substring; return the first `L`
with a real duplicate. Materializing and hashing full substrings costs
O(L) each, over O(n) candidates per length, over up to O(n) lengths ->
O(n^3) worst case. Only usable for small `n` (a few hundred), used here
purely to independently verify correctness.

Approach 1 (chosen) -- binary search on length + Rabin-Karp rolling hash
with a large prime modulus and mandatory verification: O(n log n)
expected time (O(log n) binary search steps, each an O(n) rolling-hash
pass; verification is O(L) per hash match but hash matches are rare with
a 61-bit modulus), O(n) extra space per search call for the hash-bucket
dict. This is the standard accepted solution to this exact LeetCode
problem.

Approach 2 (variant, described, not coded) -- suffix array + Kasai's LCP
(longest common prefix) array: build a suffix array of `s` (O(n log n)
with a doubling/radix-sort construction, or O(n) with more advanced
techniques), then Kasai's algorithm computes the LCP between every pair
of LEXICOGRAPHICALLY ADJACENT suffixes in O(n) total. The longest
duplicated substring is exactly the maximum value in the LCP array (two
substrings share the longest common prefix precisely when their suffixes
are lexicographically adjacent after sorting -- a classical, deep result
about suffix arrays). O(n log n) total, the "fully rigorous, no
collision risk at all" answer -- more machinery to implement correctly
under interview time pressure than the binary-search + rolling-hash
approach, which is why it's named here as the alternative rather than
the primary answer.

Approach 3 (variant, described, not coded) -- suffix automaton: an O(n)-
size automaton built in O(n) time that implicitly represents every
substring of `s`; the longest duplicated substring corresponds to a
specific structural property of the automaton's states (a state reached
by more than one path corresponds to a substring occurring more than
once). Asymptotically optimal, but by far the most complex to implement
from scratch -- named for completeness, genuinely out of scope to hand-
code in an interview.


================================================================================
STEP BY STEP TRACE
================================================================================
The trace below uses a SMALL illustrative modulus (`base=5, mod=101`)
purely so the arithmetic is readable by hand -- the real implementation
uses `mod = 2**61 - 1`, far too large to hand-trace, but the mechanism is
identical.

s = "banana"  (Example 1), nums = [b,a,n,a,n,a] -> [1, 0, 13, 0, 13, 0]
(0-indexed: a=0, b=1, ..., n=13)

search(L=3): does a duplicated length-3 substring exist?
    power = base^(L-1) mod 101 = 5^2 mod 101 = 25

    Initial window, start=0, "ban" = nums[0:3] = [1, 0, 13]:
        h = 0
        h = (0*5 + 1) % 101 = 1
        h = (1*5 + 0) % 101 = 5
        h = (5*5 + 13) % 101 = 38
        seen = {38: [0]}

    Slide to start=1, "ana" = nums[1:4] = [0, 13, 0]:
        h = (38 - nums[0]*25) % 101 = (38 - 25) % 101 = 13
        h = (13*5 + nums[3]) % 101 = (65 + 0) % 101 = 65
        65 not in seen -> seen[65] = [1]

    Slide to start=2, "nan" = nums[2:5] = [13, 0, 13]:
        h = (65 - nums[1]*25) % 101 = (65 - 0) % 101 = 65
        h = (65*5 + nums[4]) % 101 = (325 + 13) % 101 = 338 % 101 = 35
        35 not in seen -> seen[35] = [2]

    Slide to start=3, "ana" = nums[3:6] = [0, 13, 0]:
        h = (35 - nums[2]*25) % 101 = (35 - 325) % 101 = -290 % 101 = 13
        h = (13*5 + nums[5]) % 101 = (65 + 0) % 101 = 65
        65 IS in seen -> seen[65] = [1] (window "ana" starting at index 1)
        VERIFY: s[1:4] = "ana", s[3:6] = "ana" -> equal, confirmed real
        duplicate (not a collision) -> return start = 3

    search(3) returns 3 -> a length-3 duplicate exists ("ana" at indices
    1 and 3).

search(L=4): checking "bana"(0), "anan"(1), "nana"(2) -- all three are
distinct strings, no hash match survives verification -> returns -1.

Binary search over L in [1, 5]:
    the predicate is True for L=1,2,3 and False for L=4,5 (monotone, as
    guaranteed) -> binary search converges to the boundary at L=3,
    keeping the last successful (start=3, length=3).

Final answer: s[3:3+3] = s[3:6] = "ana".   Matches expected output "ana".


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                           Time          Space    Mutates input?
    --------------------------------------------------------------------
    Try every length, hash substrings
    directly [priced]                  O(n^3)        O(n^2)    no
    Binary search + Rabin-Karp,
    large modulus + verify [chosen]    O(n log n)*   O(n)      no
    Suffix array + Kasai's LCP
    [variant]                          O(n log n)    O(n)      no
    Suffix automaton [variant]         O(n)          O(n)      no

    n = len(s). *Expected/amortized: verification cost is O(L) per hash
    COLLISION, which is rare with a 61-bit modulus; a pathological
    adversarial input engineered to defeat this specific hash function
    could in principle push verification cost higher, which is exactly
    why suffix automata (worst-case O(n), no probabilistic assumption)
    exist as the fully rigorous alternative.


================================================================================
EDGE CASES
================================================================================
    no duplicate substring at all
    (e.g. "abcd")                 -> binary search's predicate is False
                                      even at L=1 -> best_start stays -1
                                      -> return "".
    entire string is one repeated
    character (e.g. "aaaa")       -> every length up to n-1 has a
                                      duplicate (overlapping is allowed
                                      per the problem statement) ->
                                      answer is `s[:-1]`, the longest
                                      substring that still fits twice.
    duplicate substrings OVERLAP
    (e.g. "aaa" -- "aa" at index 0
    and index 1 overlap)          -> explicitly allowed by the problem;
                                      the rolling hash and verification
                                      logic don't care whether the two
                                      matched windows overlap in the
                                      original string, only that their
                                      CONTENTS are equal.
    hash collision on a length
    that has NO real duplicate    -> verification (`s[i:i+L] ==
                                      s[j:j+L]`) rejects the false match
                                      and the search continues scanning
                                      -- this is the entire reason
                                      verification is not optional; see
                                      the runtime demo below for a
                                      concrete manufactured example.
    multiple substrings tie for
    longest duplicate length      -> the problem accepts ANY correct
                                      answer at the longest length; this
                                      implementation returns whichever
                                      one the rolling hash scan happens
                                      to find first at that length.


================================================================================
COMMON MISTAKES
================================================================================
1. Trusting a hash match as proof of a duplicate WITHOUT verifying via a
   direct substring comparison -- the single most dangerous bug in this
   problem, because it can pass small/lucky test cases and then silently
   return a WRONG substring on a larger or adversarial input. See the
   collision demo below for a concrete, measured example of this failure.
2. Using a small or "convenient" modulus (e.g. a 32-bit prime, or worse, a
   power of 2) -- power-of-2 moduli are especially bad because they only
   depend on the low bits of the polynomial hash, making collisions far
   more likely than the modulus size alone suggests; always prefer a
   large prime, ideally a Mersenne prime like `2^61 - 1` for fast modular
   reduction properties.
3. Recomputing the rolling hash from scratch for every window instead of
   updating it in O(1) via the "subtract old, shift, add new" formula --
   turns the O(n)-per-length checker into O(n*L), destroying the whole
   point of the rolling hash.
4. Binary searching on the SUBSTRING itself (e.g. trying to compare
   candidate strings lexicographically) instead of on the LENGTH -- the
   monotone predicate this problem needs is specifically "does a
   duplicate of length >= L exist," a property of an integer, not of a
   string; conflating the two loses the clean binary-search structure
   entirely.
5. Forgetting that overlapping occurrences are explicitly ALLOWED --
   accidentally excluding a window from comparison against nearby/
   overlapping windows (e.g. requiring `start2 >= start1 + L`) rejects
   valid answers like `"aa"` inside `"aaa"`.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "How do you make this fully collision-proof, not just 'probably'
  correct?" -> Either verify every hash match with a real substring
  comparison (what's done here -- deterministically correct regardless of
  hash quality), or switch to a suffix array + Kasai's LCP array
  (deterministically correct AND with no verification step needed at
  all, since it never hashes in the first place).
- "What if you used double hashing (two independent mod/base pairs)
  instead of verification?" -> Reduces collision probability further
  (multiplies the two individual collision probabilities), but does NOT
  eliminate it the way direct verification does -- it's still
  probabilistic. Verification against the ACTUAL string is the only
  deterministic guarantee; double hashing is a reasonable choice when
  verification itself would be expensive (e.g. comparing over a network
  or against un-materialized data), which isn't the case here since `s`
  is fully in memory.
- "Why is the predicate over length monotone -- can you prove it?" -> If
  two equal length-L substrings exist at positions `i` and `j`, then
  their length-`(L-1)` prefixes are also equal (trivially, a prefix of
  two equal strings is equal), giving a duplicate at length `L-1` too.
  Induction extends this down to length 1. This monotonicity is exactly
  what licenses binary search per topic 05's "search on the answer
  space" family.


================================================================================
RELATED PROBLEMS
================================================================================
- Repeated DNA Sequences (LC 187, this topic, 004) -- the same rolling-
  hash-over-a-sliding-window mechanism, but at a FIXED length (10) over a
  tiny 4-letter alphabet, which gives a perfect hash and needs no
  verification at all; contrast that with THIS problem's arbitrary
  alphabet and arbitrary length, which forces the large-modulus +
  verification discipline.
- Repeated String Match (LC 686, this topic, 005) -- also relies on
  efficient substring search, though via bounded candidate construction
  rather than hashing.
- Binary Search topic (05) -- "search on the answer space" (a monotone
  predicate over a value, not an index into a sorted array) is the exact
  meta-pattern this problem's outer loop is built on.
- Sliding Window topic (03) -- the rolling hash's O(1) update-per-slide
  is the same amortized mechanism as every fixed/variable window problem
  there, just with a polynomial hash as the running aggregate instead of
  a sum or count.
================================================================================
"""

import random
import string
import time


class Solution:
    _BASE = 26
    _MOD = (1 << 61) - 1  # large Mersenne prime modulus

    def longestDupSubstring(self, s: str) -> str:
        n = len(s)
        nums = [ord(c) - ord('a') for c in s]

        def search(length: int):
            """Return a start index of a duplicated substring of this
            exact length, using a Rabin-Karp rolling hash with a large
            modulus and mandatory direct-comparison verification on every
            hash match. Returns -1 if no duplicate of this length exists."""
            if length == 0:
                return 0

            base, mod = self._BASE, self._MOD
            power = pow(base, length - 1, mod)

            h = 0
            for i in range(length):
                h = (h * base + nums[i]) % mod

            seen = {h: [0]}
            for start in range(1, n - length + 1):
                h = (h - nums[start - 1] * power) % mod
                h = (h * base + nums[start + length - 1]) % mod
                if h in seen:
                    for idx in seen[h]:
                        if s[idx:idx + length] == s[start:start + length]:
                            return start
                    seen[h].append(start)
                else:
                    seen[h] = [start]
            return -1

        lo, hi = 1, n - 1
        best_start, best_len = -1, 0
        while lo <= hi:
            mid = (lo + hi) // 2
            pos = search(mid)
            if pos != -1:
                best_start, best_len = pos, mid
                lo = mid + 1
            else:
                hi = mid - 1

        return s[best_start:best_start + best_len] if best_start != -1 else ""


def _brute_force_longest_dup(s: str) -> str:
    """Priced O(n^3)-ish baseline: try every length from longest to
    shortest, checking all substrings of that length via a plain set.
    Only usable on small inputs; used purely as an independent oracle in
    the cross-check demo below."""
    n = len(s)
    for length in range(n - 1, 0, -1):
        seen = set()
        for start in range(n - length + 1):
            sub = s[start:start + length]
            if sub in seen:
                return sub
            seen.add(sub)
    return ""


def _demonstrate_rolling_hash_collision():
    """Deliberately uses a TINY modulus to manufacture a real rolling-hash
    collision between two genuinely different substrings, proving why the
    Solution's verification step is not optional. Returns
    (s, length, idx_a, idx_b, hash_value) for a found collision, or None."""
    random.seed(5)
    s = "".join(random.choice(string.ascii_lowercase) for _ in range(1500))
    length = 5
    small_base, small_mod = 131, 97  # deliberately tiny modulus
    nums = [ord(c) - ord('a') for c in s]
    power = pow(small_base, length - 1, small_mod)

    h = 0
    for i in range(length):
        h = (h * small_base + nums[i]) % small_mod

    buckets = {h: [0]}
    for start in range(1, len(s) - length + 1):
        h = (h - nums[start - 1] * power) % small_mod
        h = (h * small_base + nums[start + length - 1]) % small_mod
        buckets.setdefault(h, []).append(start)

    for h, starts in buckets.items():
        if len(starts) < 2:
            continue
        base_idx = starts[0]
        base_sub = s[base_idx:base_idx + length]
        for other in starts[1:]:
            if s[other:other + length] != base_sub:
                return s, length, base_idx, other, h
    return None


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    def is_valid_answer(s: str, ans: str) -> bool:
        if ans == "":
            return _brute_force_longest_dup(s) == ""
        # ans must actually be a substring occurring at least twice in s,
        # and no strictly longer duplicate may exist.
        occurrences = 0
        start = 0
        while True:
            idx = s.find(ans, start)
            if idx == -1:
                break
            occurrences += 1
            start = idx + 1
        oracle = _brute_force_longest_dup(s)
        return occurrences >= 2 and len(ans) == len(oracle)

    cases = ["banana", "abcd", "aaaaa", "aa", "abcabcabc", "aabbaabb"]
    for s in cases:
        got = sol.longestDupSubstring(s)
        ok = is_valid_answer(s, got)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  longestDupSubstring({s!r}) -> {got!r}")

    print()
    print("CROSS-CHECK -- binary-search+Rabin-Karp vs brute force, 150 random small strings")
    print("-" * 72)
    random.seed(41)
    alphabet = "ab"
    mismatch = 0
    for _ in range(150):
        n = random.randint(2, 40)
        s = "".join(random.choice(alphabet) for _ in range(n))
        r1 = sol.longestDupSubstring(s)
        r2 = _brute_force_longest_dup(s)
        if len(r1) != len(r2):
            mismatch += 1
            print(f"  MISMATCH on {s!r}: chosen={r1!r} (len {len(r1)}) "
                  f"brute={r2!r} (len {len(r2)})")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {150 - mismatch}/150 agree on the "
          f"longest-duplicate LENGTH ({mismatch} mismatches)")

    print()
    print("ROLLING-HASH COLLISION DEMO -- why verification is not optional")
    print("-" * 72)
    collision = _demonstrate_rolling_hash_collision()
    if collision is None:
        print("  (no collision found under this seed/modulus -- skipping demo)")
        collision_ok = True
    else:
        s, length, idx_a, idx_b, h = collision
        sub_a = s[idx_a:idx_a + length]
        sub_b = s[idx_b:idx_b + length]
        print(f"  tiny modulus (mod=97, base=131) on a 1500-char random string:")
        print(f"    substring at index {idx_a}: {sub_a!r}")
        print(f"    substring at index {idx_b}: {sub_b!r}")
        print(f"    both hash to {h} under the tiny modulus, but {sub_a!r} != {sub_b!r}")
        print(f"  A hash-only (no verification) search would have wrongly reported "
              f"these as a duplicate.")
        print(f"  The Solution class's real modulus is 2**61-1 (not this tiny demo "
              f"value) precisely to make such collisions astronomically rare -- but "
              f"the verification step (`s[i:i+L] == s[j:j+L]`) is what makes "
              f"correctness a GUARANTEE rather than a probability, regardless of "
              f"modulus size.")
        collision_ok = sub_a != sub_b
    all_ok &= collision_ok
    print(f"{'PASS' if collision_ok else 'FAIL'}  collision correctly demonstrates a "
          f"same-hash-different-string pair")

    print()
    print("RUNTIME DEMO -- binary-search+Rabin-Karp vs O(n^3) brute force")
    print("-" * 72)
    random.seed(43)
    n = 300
    s = "".join(random.choice("ab") for _ in range(n))

    t0 = time.perf_counter()
    fast_result = sol.longestDupSubstring(s)
    fast_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    brute_result = _brute_force_longest_dup(s)
    brute_ms = (time.perf_counter() - t0) * 1000

    agree = len(fast_result) == len(brute_result)
    all_ok &= agree
    print(f"len(s)={n}, longest duplicate length found = {len(fast_result)}")
    print(f"  binary search + Rabin-Karp: {fast_ms:9.2f} ms")
    print(f"  brute force (O(n^3)-ish):   {brute_ms:9.2f} ms")
    if fast_ms > 0:
        print(f"  measured: fast approach is {brute_ms / max(fast_ms, 1e-6):.1f}x "
              f"faster here, and the gap grows sharply as n grows further since the "
              f"brute force is cubic while the chosen approach is O(n log n).")
    print(f"{'PASS' if agree else 'FAIL'}  both approaches agree on the answer length")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
