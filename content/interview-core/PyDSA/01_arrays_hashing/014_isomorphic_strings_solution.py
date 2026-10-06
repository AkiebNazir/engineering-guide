"""
================================================================================
SOLUTION · LeetCode 205 · Isomorphic Strings                              [Easy]
https://leetcode.com/problems/isomorphic-strings/
================================================================================

THE CORE IDEA
--------------
Isomorphic means the character mapping is a BIJECTION. Check both directions
while walking the strings together: s_to_t catches one s-char mapping to two
t-chars, t_to_s catches two s-chars mapping to the same t-char. A single map
only checks half the definition.


================================================================================
APPROACH 1 · One map only (the common WRONG answer)
================================================================================
Keep s_to_t; fail if a character is remapped. This passes "egg"/"add" and
"foo"/"bar", and wrongly returns True for "badc"/"baba" (b->b and d->b).
Coded below only as a broken example.


================================================================================
APPROACH 2 · Two maps ✅ (the answer)
================================================================================
    s_to_t, t_to_s = {}, {}
    for a, b in zip(s, t):
        if s_to_t.get(a, b) != b or t_to_s.get(b, a) != a:
            return False
        s_to_t[a] = b
        t_to_s[b] = a
    return True

`.get(a, b) != b` reads as "a is already mapped, and not to b". The default
makes the unseen case pass without a separate branch (same trick as the
Logger Rate Limiter in 25_design/003).

    Time: O(n)    Space: O(alphabet)


================================================================================
APPROACH 3 · First-occurrence pattern
================================================================================
Map each string to its "shape": the index at which each character first
appeared. Two strings are isomorphic exactly when their shapes are equal.

    def shape(x):
        first = {}
        return [first.setdefault(c, i) for i, c in enumerate(x)]
    return shape(s) == shape(t)

    "paper" -> [0, 1, 0, 3, 4]      "title" -> [0, 1, 0, 3, 4]   equal -> True
    "badc"  -> [0, 1, 2, 3]         "baba"  -> [0, 1, 0, 1]      differ -> False

This is the approach that generalizes: to GROUP many strings by isomorphism
class (like Group Anagrams, 007), use tuple(shape(x)) as the dict key.

    Time: O(n)    Space: O(n) for the two shape lists


================================================================================
APPROACH 4 · Set-size one-liner
================================================================================
    len(set(s)) == len(set(t)) == len(set(zip(s, t)))

If the mapping is a bijection, the number of distinct PAIRS equals the number
of distinct characters on each side. If any character maps to two things (or
two things map to one), the pair count exceeds one of the side counts. Neat,
and easy to get wrong under pressure if you can't explain why it works.


================================================================================
STEP BY STEP TRACE · s = "badc", t = "baba"
================================================================================
    pair   s_to_t before   t_to_s before   check                     action
    -----  --------------  --------------  ------------------------  -------------
    b->b   {}              {}              ok                        record b<->b
    a->a   {b:b}           {b:b}           ok                        record a<->a
    d->b   {b:b,a:a}       {b:b,a:a}       t_to_s[b] = b, not d      return False

    A one-map solution never looks at t_to_s, sees d is unmapped, and continues.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                   Time   Space       Mutates input?
    -------------------------  -----  ----------  ---------------------------
    One map (WRONG)            O(n)   O(alpha)    No
    Two maps ✅                O(n)   O(alpha)    No (strings are immutable)
    First-occurrence shape     O(n)   O(n)        No
    Set-size one-liner         O(n)   O(alpha)    No


================================================================================
EDGE CASES
================================================================================
    Single character          Always isomorphic.
    Character maps to itself   Allowed: "ab"/"ab" -> True.
    Non-letters                Digits, spaces, punctuation are all valid ASCII.
    Different lengths          Constraints say equal; a defensive check is cheap.


================================================================================
COMMON MISTAKES
================================================================================
1. Checking only s -> t. Fails "badc"/"baba". Demo below.

2. Checking `set(s) ... == set(t)` sizes only. "ab"/"ba"-style inputs pass, but
   so does "aab"/"abb", which is NOT isomorphic. Sizes of the pair set matter.

3. Using `if a in s_to_t and s_to_t[a] != b` and then forgetting to write both
   maps on success. Keep the writes in one place after the checks.

4. Confusing isomorphic with anagram. Anagrams compare character COUNTS;
   isomorphism compares STRUCTURE.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Group a list of words by isomorphism class?
A: Key each word by tuple(shape(word)) in a defaultdict(list).
   (LC 890 Find and Replace Pattern is the single-pattern version.)

Q: Unicode strings?
A: Dict-based versions work unchanged. Fixed-size arrays of 128 don't.

Q: Word pattern: "abba" vs "dog cat cat dog" (LC 290)?
A: Identical two-map logic, with words on one side instead of characters.
   Also check the counts match first.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 290  Word Pattern                    — characters to words
    LC 890  Find and Replace Pattern        — shape comparison over a list
    LC 49   Group Anagrams (007)            — canonical-key grouping
    LC 242  Valid Anagram (003)             — counts, not structure
================================================================================
"""

import random
import time
from typing import List


class Solution:
    def isIsomorphic(self, s: str, t: str) -> bool:
        if len(s) != len(t):
            return False
        s_to_t: dict = {}
        t_to_s: dict = {}
        for a, b in zip(s, t):
            if s_to_t.get(a, b) != b or t_to_s.get(b, a) != a:
                return False
            s_to_t[a] = b
            t_to_s[b] = a
        return True


# ------------------------------------------------------------------------
# Alternatives / broken version for the demos.
# ------------------------------------------------------------------------
def iso_one_map_bug(s: str, t: str) -> bool:
    """Approach 1: checks only s -> t consistency. WRONG."""
    s_to_t: dict = {}
    for a, b in zip(s, t):
        if s_to_t.get(a, b) != b:
            return False
        s_to_t[a] = b
    return True


def shape(x: str) -> List[int]:
    first: dict = {}
    return [first.setdefault(c, i) for i, c in enumerate(x)]


def iso_shape(s: str, t: str) -> bool:
    return shape(s) == shape(t)


def iso_set_sizes(s: str, t: str) -> bool:
    return len(set(s)) == len(set(t)) == len(set(zip(s, t)))


def iso_brute(s: str, t: str) -> bool:
    """Oracle straight from the definition: build the map, then check it."""
    m = {}
    for a, b in zip(s, t):
        m.setdefault(a, b)
    return "".join(m[a] for a in s) == t and len(set(m.values())) == len(m)


# ==============================================================================
# TESTS — run:  python 014_isomorphic_strings_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: two maps vs shape vs set-size ---")
    cases = [
        ("egg", "add", True),
        ("foo", "bar", False),
        ("paper", "title", True),
        ("badc", "baba", False),
        ("a", "a", True),
        ("ab", "aa", False),
        ("aa", "ab", False),
        ("13", "42", True),
        ("aab", "abb", False),
    ]
    for s, t, want in cases:
        results = (sol.isIsomorphic(s, t), iso_shape(s, t), iso_set_sizes(s, t))
        ok = all(r == want for r in results)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  s={s!r:<8} t={t!r:<8} got={results}  want={want}")

    print("\n--- randomized cross-check vs definition oracle (2000 pairs) ---")
    rng = random.Random(205)
    bad = 0
    trues = 0
    for _ in range(2000):
        n = rng.randint(1, 8)
        s = "".join(rng.choice("abc") for _ in range(n))
        t = "".join(rng.choice("xyz") for _ in range(n))
        want = iso_brute(s, t)
        trues += want
        if sol.isIsomorphic(s, t) != want or iso_shape(s, t) != want or iso_set_sizes(s, t) != want:
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  2000 random pairs ({trues} isomorphic) — all three agree with the oracle")

    print("\n--- mistake 1 LIVE: one map only ---")
    wrong = iso_one_map_bug("badc", "baba")
    ok = wrong is True and sol.isIsomorphic("badc", "baba") is False
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  'badc'/'baba': one-map returns {wrong}, two maps return False")
    rng = random.Random(7)
    fooled = 0
    for _ in range(2000):
        n = rng.randint(1, 8)
        s = "".join(rng.choice("abc") for _ in range(n))
        t = "".join(rng.choice("xyz") for _ in range(n))
        if iso_one_map_bug(s, t) and not iso_brute(s, t):
            fooled += 1
    print(f"      on 2000 random pairs the one-map version wrongly says True {fooled} times")

    print("\n--- benchmark: n = 50,000, isomorphic inputs (full scan, no early exit) ---")
    alphabet = [chr(c) for c in range(32, 127)]
    perm = alphabet[:]
    rng.shuffle(perm)
    table = dict(zip(alphabet, perm))
    s = "".join(rng.choice(alphabet) for _ in range(50_000))
    t = "".join(table[c] for c in s)
    for name, fn in (("two maps   ", sol.isIsomorphic), ("shape lists", iso_shape), ("set sizes  ", iso_set_sizes)):
        t0 = time.perf_counter()
        for _ in range(5):
            r = fn(s, t)
        dt = (time.perf_counter() - t0) / 5
        all_ok &= r is True
        print(f"      {name}  {dt * 1000:7.2f} ms per call")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
