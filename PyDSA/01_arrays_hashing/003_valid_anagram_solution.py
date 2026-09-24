"""
================================================================================
SOLUTION · LeetCode 242 · Valid Anagram                                  [Easy]
https://leetcode.com/problems/valid-anagram/
================================================================================

THE CORE IDEA
-------------
Anagram == identical character MULTISET. Not "same set of letters" — counts
matter. "aacc" and "ccac" use exactly the letters {a, c} but are not anagrams,
because a appears twice in one and once in the other.

So: count characters in both, compare the counts.

And before any of that: if the lengths differ, it is impossible. That single
line is O(1) and eliminates a large fraction of real inputs.


================================================================================
APPROACH 1 · Sort and compare
================================================================================
    return sorted(s) == sorted(t)

Anagrams have identical sorted forms, so this is correct and it fits on one
line.

    Time:  O(n log n)  — dominated by the two sorts
    Space: O(n)        — sorted() builds two new lists of characters

Worth mentioning as the "obvious" answer, then improving. Its one genuine
advantage: it needs no assumption about the alphabet, so it handles the Unicode
follow-up unchanged.


================================================================================
APPROACH 2 · Hash map counting ✅
================================================================================

    if len(s) != len(t): return False
    counts = {}
    for c in s: counts[c] = counts.get(c, 0) + 1
    for c in t:
        if c not in counts or counts[c] == 0: return False
        counts[c] -= 1
    return True

STEP BY STEP for s = "anagram", t = "nagaram":

    lengths: 7 == 7  ✓  continue

    Build counts from s:
      a -> {a:1}
      n -> {a:1, n:1}
      a -> {a:2, n:1}
      g -> {a:2, n:1, g:1}
      r -> {a:2, n:1, g:1, r:1}
      a -> {a:3, n:1, g:1, r:1}
      m -> {a:3, n:1, g:1, r:1, m:1}

    Drain with t:
      n -> counts[n] 1 -> 0
      a -> counts[a] 3 -> 2
      g -> counts[g] 1 -> 0
      a -> counts[a] 2 -> 1
      r -> counts[r] 1 -> 0
      a -> counts[a] 1 -> 0
      m -> counts[m] 1 -> 0

    Never hit a missing or zero count -> return True   ✓

And for s = "rat", t = "car":
      c -> 'c' not in counts -> return False   ✓  (exits on the FIRST character)

    Time:  O(n)
    Space: O(k), k = number of distinct characters

WHY THE LENGTH CHECK MATTERS BEYOND SPEED: without it, the decrement loop alone
is not sufficient. s="ab", t="a" would drain cleanly and wrongly return True.
The length guard is what makes "every count reaches exactly zero" equivalent to
"anagram."


================================================================================
APPROACH 3 · Fixed 26-slot array — the fastest ✅✅
================================================================================
The constraint promises lowercase English letters only. That means at most 26
distinct keys, so the hash map is overkill: use a list indexed by letter.

    counts = [0] * 26
    for a, b in zip(s, t):
        counts[ord(a) - 97] += 1      # 97 == ord('a')
        counts[ord(b) - 97] -= 1      # one pass, both strings
    return all(c == 0 for c in counts)

Because the lengths are already known equal, you can walk both strings
simultaneously, incrementing for s and decrementing for t. Every count lands on
zero exactly when they are anagrams.

    Time:  O(n)
    Space: O(1) — 26 ints, independent of n

This beats the dict version on constant factor: array indexing is pointer
arithmetic, whereas a dict lookup hashes the key, masks it to a slot, and may
probe. Same big-O, meaningfully faster in practice.

⚠️ This is the approach that BREAKS on the Unicode follow-up — see below.


================================================================================
APPROACH 4 · Counter one-liner
================================================================================
    from collections import Counter
    return Counter(s) == Counter(t)

`Counter` is a dict subclass; `==` compares them as mappings. Clean and fast
(the counting loop runs in C). Note it needs no explicit length check —
different lengths necessarily produce different count mappings.

Interviewers usually want to see you can write the manual version too, so lead
with Approach 2 or 3 and mention this.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach            Time         Space   Unicode-safe?
    ------------------  -----------  ------  -------------
    Sort                O(n log n)   O(n)    yes
    Hash map      ✅    O(n)         O(k)    yes
    26-array      ✅✅  O(n)         O(1)    NO
    Counter             O(n)         O(k)    yes


================================================================================
THE UNICODE FOLLOW-UP (they will ask)
================================================================================
`counts[ord(c) - 97]` assumes every character lies in 'a'..'z'. Give it 'A',
'é', or '日' and you index out of range or, worse, corrupt a neighbouring slot.

The fix is to go back to a hash map (Approach 2 or 4), which has no alphabet
assumption. Cost: O(k) space instead of O(1), and hashing per character.

There is a second, subtler Unicode issue worth raising if you want to stand
out: Python iterates a `str` by CODE POINT, so "é" written as U+00E9 (one code
point) and as "e" + U+0301 combining accent (two code points) compare unequal
even though they render identically. A fully correct answer normalises first:

    import unicodedata
    s = unicodedata.normalize("NFC", s)
    t = unicodedata.normalize("NFC", t)

Mentioning normalisation is a strong signal in a senior interview.


================================================================================
EDGE CASES
================================================================================
    ("a", "a")        -> True.   Minimum input.
    ("a", "ab")       -> False.  Caught by the length guard.
    ("aacc", "ccac")  -> False.  Same letter SET, different counts. This is the
                                 case that catches anyone who used a set.
    ("ab", "ba")      -> True.   Order genuinely irrelevant.


================================================================================
COMMON MISTAKES
================================================================================
1. Using a SET instead of counts: `set(s) == set(t)` returns True for
   ("aacc", "ccac"). Sets discard multiplicity; anagrams depend on it.

2. Omitting the length check in the decrement version — s="ab", t="a" drains
   cleanly and wrongly returns True.

3. `counts[c] -= 1` without first checking membership — KeyError on a character
   that never appeared in s.

4. Claiming O(1) space for the dict version. It is O(k). Only the fixed-size
   array version is genuinely O(1), and only because the alphabet is bounded.

5. Sorting and then claiming O(n). sorted() is O(n log n).


================================================================================
RELATED PROBLEMS
================================================================================
    LC 49   Group Anagrams        — the canonical key idea, applied to grouping
    LC 438  Find All Anagrams in a String — anagram + sliding window
    LC 567  Permutation in String — fixed-window count matching
    LC 383  Ransom Note           — one-directional version of this count check
================================================================================
"""

from collections import Counter


class Solution:
    def isAnagram(self, s: str, t: str) -> bool:
        """Fixed 26-slot table, one pass. Time O(n), space O(1)."""
        if len(s) != len(t):
            return False
        counts = [0] * 26
        for a, b in zip(s, t):          # lengths equal, so one loop covers both
            counts[ord(a) - 97] += 1
            counts[ord(b) - 97] -= 1
        return all(c == 0 for c in counts)

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def isAnagram_hashmap(self, s: str, t: str) -> bool:
        """No alphabet assumption — survives the Unicode follow-up."""
        if len(s) != len(t):
            return False
        counts: dict[str, int] = {}
        for c in s:
            counts[c] = counts.get(c, 0) + 1
        for c in t:
            if counts.get(c, 0) == 0:
                return False
            counts[c] -= 1
        return True

    def isAnagram_sort(self, s: str, t: str) -> bool:
        """O(n log n), but needs no counting structure at all."""
        return sorted(s) == sorted(t)

    def isAnagram_counter(self, s: str, t: str) -> bool:
        """Idiomatic Python. Counting loop runs in C."""
        return Counter(s) == Counter(t)

    def isAnagram_unicode(self, s: str, t: str) -> bool:
        """The follow-up answer: normalise, then count with no alphabet bound."""
        import unicodedata
        s = unicodedata.normalize("NFC", s)
        t = unicodedata.normalize("NFC", t)
        return Counter(s) == Counter(t)


# ==============================================================================
# TESTS — run:  python 003_valid_anagram_solution.py
# ==============================================================================
def run_tests() -> None:
    sol = Solution()
    cases = [
        ("anagram", "nagaram", True),
        ("rat", "car", False),
        ("a", "a", True),
        ("a", "ab", False),
        ("aacc", "ccac", False),
        ("ab", "ba", True),
        ("", "", True),
    ]
    impls = [
        ("26-array ", sol.isAnagram),
        ("hash map ", sol.isAnagram_hashmap),
        ("sort     ", sol.isAnagram_sort),
        ("Counter  ", sol.isAnagram_counter),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(fn(s, t) == e for s, t, e in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # The trap that a set-based solution falls into.
    print("\n--- why a set is the wrong tool ---")
    s, t = "aacc", "ccac"
    print(f"  s={s!r} t={t!r}")
    print(f"  set(s) == set(t)      -> {set(s) == set(t)}   <- WRONG")
    print(f"  correct answer        -> {sol.isAnagram(s, t)}")

    # The Unicode follow-up: the 26-array approach cannot handle it.
    print("\n--- the Unicode follow-up ---")
    a, b = "école", "eécol"
    try:
        sol.isAnagram(a, b)
        print("  26-array: (did not raise, but the indices are meaningless)")
    except IndexError as e:
        print(f"  26-array: IndexError -> {e}")
    print(f"  hash map: {sol.isAnagram_hashmap(a, b)}  <- correct, no alphabet bound")
    combining = "école"                 # e + combining acute
    precomposed = "école"                # é as one code point
    print(f"  'école' spelled two ways, naive compare -> "
          f"{sol.isAnagram_counter(combining, precomposed)}")
    print(f"  with NFC normalisation           -> "
          f"{sol.isAnagram_unicode(combining, precomposed)}  <- correct")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
