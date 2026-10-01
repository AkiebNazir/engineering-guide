"""
================================================================================
SOLUTION · LeetCode 761 · Special Binary String                          [Hard]
https://leetcode.com/problems/special-binary-string/
================================================================================

THE CORE IDEA
--------------
Split `s` into its TOP-LEVEL special pieces using a running balance counter
(+1 per '1', -1 per '0'; a piece boundary is exactly where the balance
returns to 0). Recursively make the INSIDE of each piece (everything between
its outer '1' and outer '0') as large as possible, rewrap it as
`'1' + inside + '0'`, then sort the wrapped pieces in DESCENDING order and
concatenate — because a swap of two adjacent special substrings is exactly
the legal move that lets any permutation of the top-level pieces be reached,
so putting the largest piece first (then the next largest, etc.) is both
achievable and optimal for lexicographic order.


================================================================================
MULTIPLE APPROACHES
================================================================================
1. BRUTE-FORCE SWAP SEARCH — actually try swapping every pair of adjacent
   special substrings, repeat until no swap improves the string, treating it
   like bubble sort on pieces. Priced, not written: correct but does not
   scale, and re-discovers "sort descending" the hard way through repeated
   swaps instead of proving it once and doing it directly.
2. RECURSIVE DECOMPOSE + SORT (the intended answer) — O(n log n) time,
   written below as the primary solution.


================================================================================
STEP BY STEP TRACE — s = "11011000"
================================================================================
Balance scan of the WHOLE string (+1 per '1', -1 per '0'):
    idx:    0    1    2    3    4    5    6    7
    char:   1    1    0    1    1    0    0    0
    bal:   +1   +2   +1   +2   +3   +2   +1    0

Balance hits 0 only at the LAST index (7), so "11011000" is a single
top-level piece, exactly as the problem states (the whole input is one
special string). Its inside is s[1:7] = "101100":

    recurse on "101100":
        idx:  0  1  2  3  4  5
        char: 1  0  1  1  0  0
        bal:  1  0  1  2  1  0
        balance hits 0 at idx 1 -> piece "10"   (inside = "")
        balance hits 0 at idx 5 -> piece "1100" (inside = "10")

        piece "10":    inside="" -> recurse returns "" -> wrap "1"+""+"0" = "10"
        piece "1100":  inside="10" -> recurse on "10":
                           idx 0..1, balance 1,0 -> single piece "10",
                           inside="" -> wraps to "10" -> only one piece,
                           sorted/joined -> "10"
                       wrap outer: "1" + "10" + "0" = "1100"

        two wrapped pieces: ["10", "1100"] -> sort DESCENDING -> ["1100", "10"]
        join -> "110010"

    wrap the outer shell: "1" + "110010" + "0" = "11100100"

Only one top-level piece at the very top ("11011000" itself), so the final
answer is exactly that wrapped inside: "11100100" — matching the expected
output, and matching this file's own test run below.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                  Time         Space    Mutates input?  Note
    -------------------------  -----------  -------  ---------------  --------------------------------
    Recursive decompose+sort   O(n log n)   O(n)     no               sort cost sums to O(n log n)
                                                                       across all recursion levels
    Brute-force repeated swap  worse, unbounded in the worst case      priced only, not written


================================================================================
EDGE CASES
================================================================================
    s = ""              -> base case, returns "" immediately (only reached via
                           recursive calls on an empty inside, never as the
                           top-level input per constraints length >= 1).
    s = "10"             -> smallest non-trivial special string: one top-level
                           piece, empty inside, returns unchanged.
    s made of many equal-length pieces at the same level, e.g. "10" + "10" ->
                           "1010": sorting is a no-op when pieces already tie
                           lexicographically, but the sort must still run —
                           skipping "single piece" fast paths incorrectly
                           would silently miss multi-piece top levels.
    Deeply nested single-piece chain (e.g. "111...000" fully nested, one giant
                           shell wrapping one smaller shell wrapping one
                           smaller shell...) -> recursion depth grows to
                           O(n/2); exercised below with a synthetic 50-char
                           (the max constraint) fully-nested string.


================================================================================
COMMON MISTAKES
================================================================================
1. Sorting the top-level pieces in ASCENDING order (the default for `sorted`/
   `.sort()` without `reverse=True`) — this produces the lexicographically
   SMALLEST arrangement instead of the largest; easy to get backwards since
   "sort the pieces" is the memorable part and "descending" is easy to drop.
2. Forgetting to RECURSE on each piece's inside before wrapping — just
   sorting the raw top-level pieces as-is (without first maximizing what's
   inside each one) gets the top level right but leaves nested pieces
   sub-optimally ordered, silently passing small tests that happen to have
   only one level of nesting while failing deeper ones.
3. Splitting into top-level pieces using the char '0'/'1' directly as a
   boundary marker (e.g. "split after any '0'") instead of the running
   balance — a '0' can appear in the MIDDLE of a piece (balance still
   positive) and is not, by itself, a boundary.
4. Comparing pieces of DIFFERENT lengths as if shorter-with-larger-prefix
   always loses — Python's default string comparison already handles this
   correctly char-by-char (it does NOT special-case length), so no custom
   comparator is needed; writing one anyway is unnecessary complexity that a
   reviewer would flag as scope creep, not a bug per se, but worth being able
   to say why it's unnecessary if asked.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Why is greedy "put the biggest piece first" provably optimal, not just a
   good heuristic?
A: Because all top-level pieces are independent — no character from one
   piece can ever end up interleaved inside another via legal swaps (a swap
   only ever exchanges two WHOLE adjacent special substrings) — so the
   lexicographic order of the final string is entirely determined by the
   order the top-level pieces are placed in, and lexicographic ordering of
   a sequence of independent blocks is always maximized by sorting blocks
   descending.

Q: What's the recursion depth in the worst case, and is there a
   RecursionError risk at the max constraint (n=50)?
A: Worst case is a single fully-nested chain ("111...000..." one shell
   inside another), giving depth O(n/2) = 25 for n=50 — nowhere near
   Python's default recursion limit. Demonstrated live below.

Q: Could this be done iteratively, bottom-up, instead of top-down recursion?
A: Yes, in principle — process the string in one pass identifying the
   smallest ("10") pieces first, merge and re-sort neighboring groups as
   pairs balance out, working outward. It's substantially harder to get
   right than the recursive top-down version and isn't the standard
   approach; not written here.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 22   Generate Parentheses — same "balance must never go negative,
            ends at zero" structural rule, applied to generation rather
            than to rearrangement.
    LC 301  Remove Invalid Parentheses — another balance-driven recursive
            decomposition, this time removing rather than reordering.
    Topic 06 (Stack & Monotonic Stack) — the general balance-counter /
            valid-parentheses family this problem's structural rule belongs to.
================================================================================
"""

from typing import List


class Solution:
    def makeLargestSpecial(self, s: str) -> str:
        """Recursive decompose + sort. O(n log n) time, O(n) space."""
        if s == "":
            return ""

        pieces: List[str] = []
        balance = 0
        start = 0
        for i, ch in enumerate(s):
            balance += 1 if ch == "1" else -1
            if balance == 0:
                inside = self.makeLargestSpecial(s[start + 1 : i])
                pieces.append("1" + inside + "0")
                start = i + 1

        pieces.sort(reverse=True)
        return "".join(pieces)


# ==============================================================================
# TESTS — run:  python 022_special_binary_string_solution.py
# ==============================================================================
CASES = [
    ("11011000", "11100100"),
    ("10", "10"),
    ("1100", "1100"),
    ("110100", "110100"),
]


def run_tests() -> None:
    sol = Solution()
    all_ok = True

    for s, expected in CASES:
        got = sol.makeLargestSpecial(s)
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  makeLargestSpecial({s!r}) -> {got!r}  (want {expected!r})")

    # ----------------------------------------------------------------------
    # Property check: the result must itself be a valid special string with
    # the same multiset of characters as the input (a swap can never change
    # length or character counts).
    # ----------------------------------------------------------------------
    print("\n--- property check: same length/char-counts, still 'special' ---")
    for s, _ in CASES:
        got = sol.makeLargestSpecial(s)
        same_counts = sorted(s) == sorted(got)
        balance = 0
        min_balance = 0
        for ch in got:
            balance += 1 if ch == "1" else -1
            min_balance = min(min_balance, balance)
        is_special = balance == 0 and min_balance == 0
        ok = same_counts and is_special
        all_ok &= ok
        print(f"  {'PASS' if ok else 'FAIL'}  {s!r} -> {got!r}  "
              f"(same char counts: {same_counts}, still special: {is_special})")

    # ----------------------------------------------------------------------
    # Recursion depth: measured live on a fully-nested worst case at the max
    # constraint length (n = 50).
    # ----------------------------------------------------------------------
    print("\n--- recursion depth on a fully-nested chain, n=50 (max constraint) ---")
    depth = 25  # 25 nested shells -> string length 50
    nested = "1" * depth + "0" * depth
    result = sol.makeLargestSpecial(nested)
    print(f"  input:  {nested}")
    print(f"  output: {result}")
    ok = len(result) == len(nested) and sorted(result) == sorted(nested)
    all_ok &= ok
    print(f"  {'PASS' if ok else 'FAIL'} — completed without RecursionError at depth {depth}.")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
