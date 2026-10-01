"""
================================================================================
SOLUTION · LeetCode 187 · Repeated DNA Sequences                    [Medium]
https://leetcode.com/problems/repeated-dna-sequences/
================================================================================

THE CORE IDEA
--------------
Every 10-letter window is a substring of a string drawn from only FOUR
possible characters ('A', 'C', 'G', 'T'). That tiny alphabet is the whole
trick: encode each nucleotide as a 2-bit code (A=00, C=01, G=10, T=11), and
a 10-character window becomes exactly a 20-bit integer -- small enough to
fit comfortably in a machine word, and because the mapping is a bijection
(every 10-mer maps to exactly one 20-bit integer and vice versa), this is
a **perfect hash**: two different 10-mers can NEVER collide to the same
integer, unlike a generic modular rolling hash (used in problems 005/007
in this topic) which always carries a nonzero collision probability.

Sliding the window one character to the right is then an O(1) bit
operation, not an O(L) substring re-slice: drop the oldest 2 bits by
`(h << 2)`, OR in the new character's 2-bit code, and mask down to the
low 20 bits to discard the bits that just fell off the top
(`& ((1 << 20) - 1)`). This is the exact same "maintain a running value
as a window slides" shape as Rabin-Karp rolling hashes and as the sliding
window techniques in topic 03 -- the aggregate here is an integer encoding
instead of a sum, but the amortized O(1)-per-slide mechanism is identical.

Track every hash seen once in a `seen` set; the moment a hash is seen a
SECOND time, its window is a repeat -- add the hash (not yet the string)
to a `repeated` set to avoid emitting the same repeated sequence more than
once even if it occurs 3+ times. Only at the very end decode the winning
hashes back into strings, since decoding a 20-bit int into 10 characters
is itself O(1) (fixed L=10) and there's no reason to pay for string
materialization on windows that never repeat.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, not coded as primary): for every pair of
window start indices `(i, j)` with `i < j`, compare `s[i:i+10] ==
s[j:j+10]`. O(n^2 * 10) time, O(1) extra space beyond the two slices being
compared at a time. Wildly too slow for n up to 10^5.

Approach 1 (variant, coded below for the runtime demo) -- naive hashmap of
materialized substrings: for each window, slice `s[i:i+10]` into an actual
Python string, and track which strings have been seen in a `set`/`dict`.
O(n) time (10 is a constant, so O(10n) = O(n)), O(n) extra space for up to
n stored 10-character strings. Correct and simple, but does real work
(string slicing + string hashing) on every single window even though 10
is small.

Approach 2 (chosen) -- 2-bit rolling perfect hash: encode each window as a
20-bit integer, slide via O(1) bit-shift/mask instead of O(10) string
slicing, decode only the winning hashes back to strings at the end. O(n)
time with a much smaller constant factor (integer ops vs. string
allocation/hashing), O(n) extra space for the hash sets in the worst case
(a string with no repeats at all still stores one hash per window).


================================================================================
STEP BY STEP TRACE
================================================================================
Encoding: A=0b00, C=0b01, G=0b10, T=0b11 (2 bits each, L=10 chars -> 20
bits total per window).

s = "AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT"  (this is LC's own example 1;
the answer is ["AAAAACCCCC", "CCCCCAAAAA"])

Building the FIRST window's hash, s[0:10] = "AAAAACCCCC":
    h = 0
    'A'(0): h = (0<<2)|0 = 0b00000000000000000000
    'A'(0): h = (h<<2)|0 = still 0 (all A's contribute 0 bits)
    ... (5 A's contribute nothing, all zero bits)
    'C'(1): h = (h<<2)|1 = 0b00000000000000000001
    'C'(1): h = (h<<2)|1 = 0b00000000000000000101
    'C'(1): h = 0b00000000000000010101
    'C'(1): h = 0b00000000000001010101
    'C'(1): h = 0b00000000000101010101   (= 341 decimal)
    seen = {341}          (hash for window "AAAAACCCCC")

Sliding to window starting at i=1, s[1:11] = "AAAACCCCCA" (drops leading
'A', appends the 11th character which is 'A'):
    new_char = s[10] = 'A' -> code 0
    h = ((341 << 2) | 0) & ((1<<20)-1) = (1364 | 0) & mask = 1364
    1364 not in seen -> seen.add(1364)

... sliding continues one character at a time, O(1) per step ...

At window start i=10, s[10:20] = "AAAAACCCCC" again (this repeat is
visible directly in the input: characters 10-14 are "AAAAA" and
characters 15-19 are the first five of the six "CCCCCC" run):
    The rolling hash recomputed at i=10 equals 341 again (same 10 letters
    encode to the same 20-bit integer -- guaranteed, since the encoding
    is a bijection, not a lossy hash).
    341 IS already in seen (from window i=0) -> repeated.add(341)

At window start i=16, s[16:26] = "CCCCCAAAAA" (characters 16-20 are the
last five C's of the six-run, characters 21-25 are the next "AAAAA" run)
recomputes to the SAME hash as window i=5 ("CCCCCAAAAA", the first
occurrence of that 10-mer) -> repeated.add(hash_of_CCCCCAAAAA)

Final step -- decode only the two hashes in `repeated` back into strings:
    341               -> "AAAAACCCCC"
    hash_of_CCCCCAAAAA -> "CCCCCAAAAA"

Return ["AAAAACCCCC", "CCCCCAAAAA"] (order may vary; LC accepts any
order), matching the expected output exactly.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                       Time      Space    Mutates input?
    ---------------------------------------------------------------
    Pairwise compare [priced]      O(n^2)    O(1)      no
    Naive substring hashmap        O(n)      O(n)      no
    Rolling 2-bit hash [chosen]    O(n)      O(n)      no

    n = len(s). Both O(n) approaches store one hash/string per window in
    the worst case (a string with zero repeats), so O(n) space is
    unavoidable for either; the win of the chosen approach is constant
    factor (integer ops vs. repeated string allocation) plus the
    collision-free guarantee.


================================================================================
EDGE CASES
================================================================================
    len(s) < 10               -> no valid 10-letter window exists at all;
                                  return [] immediately without entering
                                  the main loop (guards against building a
                                  malformed/short initial hash).
    len(s) == 10 exactly       -> exactly one window, can never repeat
                                  against itself -> [].
    no repeats anywhere         -> `repeated` set stays empty -> [].
    a sequence repeating 3+
    times (not just 2)          -> the hash is only ADDED to `repeated`
                                  once (it's a set), so the output lists
                                  it once regardless of how many times it
                                  actually recurs -- this matches the
                                  problem's requirement to return each
                                  qualifying sequence once.
    overlapping repeats (e.g.
    "AAAAAAAAAAAAA", all A's)   -> windows starting at every consecutive
                                  index all encode to hash 0 and all
                                  match each other; only ONE decoded
                                  string ("AAAAAAAAAA") appears in the
                                  output, per LC's own example 2.


================================================================================
COMMON MISTAKES
================================================================================
1. Masking AFTER sliding instead of before use, or forgetting the mask
   entirely -- without `& ((1<<20)-1)`, `h` grows unboundedly as more bits
   accumulate from every character ever seen, corrupting comparisons
   between windows (two genuinely-identical 10-mers would stop matching
   because their high, supposedly-discarded bits differ).
2. Building the INITIAL window hash with the wrong bit order (e.g.
   shifting the wrong direction), which is harmless AS LONG AS the same
   convention is used consistently for encode and decode -- but decoding
   with the opposite convention from encoding silently returns scrambled
   strings that still happen to have the right multiset of characters
   (easy to miss in testing if the test set only checks membership, not
   exact string equality).
3. Adding every window's hash to `repeated` the FIRST time it's seen
   instead of the second -- inverts the logic and reports every unique
   window as "repeated," or (if done the other way) never reports any
   real repeat, depending on which branch is swapped.
4. Using a plain (non-perfect) rolling hash with a small modulus for this
   problem "for style points" -- unnecessary here since the 4-letter
   alphabet already gives a PERFECT hash for free at L=10 (20 bits, no
   modulus needed, zero collision risk) -- reaching for modular
   Rabin-Karp here adds a real (if small) chance of a false positive that
   the bit-encoding approach structurally cannot have.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Why does this technique specifically NOT need a modulus, unlike Rabin-
  Karp in general?" -> Because the alphabet is fixed at 4 symbols and the
  window length is fixed at 10, so `4^10 = 2^20` possible windows fit
  losslessly in a machine integer -- the encoding IS the value, not a
  hash of it, so there's no pigeonhole collision possible. Generic
  Rabin-Karp (problems 005, 007 in this topic) needs a modulus because
  its key space (all possible substrings of arbitrary text) is far larger
  than any fixed-width integer.
- "What if the window length were, say, 20 instead of 10?" -> `4^20 =
  2^40` still fits in a 64-bit integer, so the same perfect-hash trick
  still works unmodified; it would stop being lossless only once
  `2 * L` exceeded the machine word size (or Python's practical bigint
  comfort zone), at which point you'd fall back to a modular hash and
  accept a small collision probability, verified with an explicit string
  compare on hash matches.
- "Could you solve this with a suffix automaton or suffix array instead?"
  -> Yes, either would also find all repeated length-10 substrings (and
  generalizes to arbitrary/variable lengths, which this fixed-hash trick
  does not) but at higher constant cost and implementation complexity for
  a problem that doesn't need that generality.


================================================================================
RELATED PROBLEMS
================================================================================
- Repeated String Match (LC 686, this topic, 005) and Longest Duplicate
  Substring (LC 1044, this topic, 007) -- both use Rabin-Karp-style
  rolling hashes over an ARBITRARY alphabet, where a modulus and
  collision-checking are unavoidable (contrast with this problem's
  alphabet-of-4 perfect hash shortcut).
- Sliding Window topic (03) -- the O(1)-per-slide "maintain a running
  aggregate" mechanism is identical in spirit; here the aggregate is a
  bit-packed integer instead of a running sum/count.
- Find All Anagrams in a String (LC 438, topic 03) -- another fixed-size
  sliding window over a small alphabet, there tracked via a 26-length
  count array rather than a single packed integer, since anagram
  membership needs multiset equality rather than exact substring
  identity.
================================================================================
"""

import time


class Solution:
    _CODE = {'A': 0, 'C': 1, 'G': 2, 'T': 3}
    _DECODE = 'ACGT'
    _L = 10

    def findRepeatedDnaSequences(self, s: str) -> list:
        n = len(s)
        L = self._L
        if n < L:
            return []

        code = self._CODE
        mask = (1 << (2 * L)) - 1

        h = 0
        for i in range(L):
            h = (h << 2) | code[s[i]]

        seen = {h}
        repeated_hashes = set()

        for i in range(1, n - L + 1):
            new_char = s[i + L - 1]
            h = ((h << 2) | code[new_char]) & mask
            if h in seen:
                repeated_hashes.add(h)
            else:
                seen.add(h)

        return [self._decode(h) for h in repeated_hashes]

    @classmethod
    def _decode(cls, h: int) -> str:
        chars = []
        for _ in range(cls._L):
            chars.append(cls._DECODE[h & 3])
            h >>= 2
        return ''.join(reversed(chars))


def _naive_substring_hashmap(s: str) -> list:
    """Priced Approach 1: real string slicing + hashing per window, used
    only for the measured comparison demo below."""
    L = 10
    n = len(s)
    if n < L:
        return []
    seen = set()
    repeated = set()
    for i in range(n - L + 1):
        window = s[i:i + L]
        if window in seen:
            repeated.add(window)
        else:
            seen.add(window)
    return list(repeated)


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    cases = [
        ("AAAAACCCCCAAAAACCCCCCAAAAAGGGTTT",
         {"AAAAACCCCC", "CCCCCAAAAA"}),
        ("AAAAAAAAAAAAA", {"AAAAAAAAAA"}),
        ("AAAAAAAAAAA", {"AAAAAAAAAA"}),
        ("A", set()),
        ("AAAAAAAAAA", set()),          # exactly one window, no repeat possible
        ("ACGTACGTACGTACGT", {"ACGTACGTAC", "CGTACGTACG", "GTACGTACGT"}),
    ]
    for s, expected in cases:
        got = set(sol.findRepeatedDnaSequences(s))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  findRepeatedDnaSequences({s!r}) "
              f"-> {sorted(got)} (expected {sorted(expected)})")

    print()
    print("CROSS-CHECK -- rolling bit-hash vs naive substring hashmap, 500 random DNA strings")
    print("-" * 72)
    import random
    random.seed(23)
    bases = "ACGT"
    mismatch = 0
    for _ in range(500):
        n = random.randint(0, 60)
        s = "".join(random.choice(bases) for _ in range(n))
        r1 = set(sol.findRepeatedDnaSequences(s))
        r2 = set(_naive_substring_hashmap(s))
        if r1 != r2:
            mismatch += 1
            print(f"  MISMATCH on {s!r}: bit-hash={r1} naive={r2}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {500 - mismatch}/500 agree "
          f"({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- rolling bit-hash vs naive substring hashmap on a long DNA string")
    print("-" * 72)
    random.seed(29)
    n = 100_000
    long_s = "".join(random.choice(bases) for _ in range(n))

    t0 = time.perf_counter()
    r_bit = sol.findRepeatedDnaSequences(long_s)
    bit_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    r_naive = _naive_substring_hashmap(long_s)
    naive_ms = (time.perf_counter() - t0) * 1000

    agree = set(r_bit) == set(r_naive)
    all_ok &= agree
    print(f"len(s)={n}, distinct repeated sequences found = {len(r_bit)}")
    print(f"  rolling 2-bit hash:      {bit_ms:9.2f} ms")
    print(f"  naive substring hashmap: {naive_ms:9.2f} ms")
    if naive_ms > 0:
        faster = "rolling hash" if bit_ms < naive_ms else "naive hashmap"
        ratio = max(bit_ms, naive_ms) / max(min(bit_ms, naive_ms), 1e-6)
        print(f"  measured: {faster} is {ratio:.2f}x faster here. Both are O(n); "
              f"this is a constant-factor gap from avoiding per-window string "
              f"allocation, not a complexity difference.")
    print(f"{'PASS' if agree else 'FAIL'}  both approaches agree on the result set")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
