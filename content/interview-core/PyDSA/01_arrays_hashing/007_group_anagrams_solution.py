"""
================================================================================
SOLUTION · LeetCode 49 · Group Anagrams                                [Medium]
https://leetcode.com/problems/group-anagrams/
================================================================================

THE CORE IDEA
-------------
Grouping by a property means hashing by a CANONICAL FORM — a function that
collapses every member of a group onto one identical representative:

    f(s1) == f(s2)   ⟺   s1 and s2 are anagrams

Pick f, then the algorithm is mechanical:

    buckets = defaultdict(list)
    for s in strs:
        buckets[f(s)].append(s)
    return list(buckets.values())

That skeleton — *canonical key → defaultdict → return values* — solves an
entire family of problems. The only design decision is f.

    "eat" ─┐
    "tea" ─┼──► f ──► KEY_A ──► ["eat","tea","ate"]
    "ate" ─┘
    "tan" ─┐
    "nat" ─┴──► f ──► KEY_B ──► ["tan","nat"]
    "bat" ────► f ──► KEY_C ──► ["bat"]

Note what you are NOT doing: comparing pairs. The naive instinct is "for each
string, scan every group and test if it's an anagram of that group's first
member" — that is O(n²k) and it is the answer this problem exists to kill.
Hashing turns "find my group" from a SEARCH into a LOOKUP.


================================================================================
APPROACH 0 · Pairwise comparison (the brute force — state it, don't code it)
================================================================================
For each string, walk the groups built so far and test membership:

    for s in strs:
        for g in groups:
            if is_anagram(s, g[0]): g.append(s); break
        else: groups.append([s])

    Time:  O(n² · k)     Space: O(nk)

With n = 10^4 that is 10^8 anagram checks. Say it out loud in the interview,
price it, then say "but 'find my group' should be a hash lookup, not a scan."


================================================================================
APPROACH 1 · Sorted-string key ✅ (the one to write first)
================================================================================
An anagram is a PERMUTATION. Every permutation of a multiset of characters has
exactly one sorted ordering, so sorting IS the canonical form.

    key = "".join(sorted(s))        # "eat" -> "aet",  "tea" -> "aet"

    Time:  O(n · k log k)
    Space: O(n · k)

STEP BY STEP for strs = ["eat","tea","tan","ate","nat","bat"]:

    s       sorted(s)   key      buckets after this step
    ------  ----------  -----    ---------------------------------------------
    "eat"   a,e,t       "aet"    {"aet": ["eat"]}
    "tea"   a,e,t       "aet"    {"aet": ["eat","tea"]}
    "tan"   a,n,t       "ant"    {"aet": ["eat","tea"], "ant": ["tan"]}
    "ate"   a,e,t       "aet"    {"aet": ["eat","tea","ate"], "ant": ["tan"]}
    "nat"   a,n,t       "ant"    {"aet": [...3...], "ant": ["tan","nat"]}
    "bat"   a,b,t       "abt"    {"aet": [...3...], "ant": [...2...],
                                  "abt": ["bat"]}

    return list(buckets.values())
         -> [["eat","tea","ate"], ["tan","nat"], ["bat"]]        ✓

Note the keys "aet"/"ant"/"abt" are never returned — they are scaffolding. The
problem accepts any group ordering, and since Python 3.7 dicts preserve
insertion order, groups come back in first-appearance order. Do not rely on
that being required; it just makes output stable and easy to eyeball.


================================================================================
APPROACH 2 · Count-vector key ✅✅ (the optimal one)
================================================================================
Sorting costs k log k, but the constraint says lowercase a–z only — a 26-letter
alphabet. Counting is O(k) and just as canonical: two strings are anagrams
exactly when their letter-count vectors are equal.

    counts = [0] * 26
    for ch in s:
        counts[ord(ch) - ord('a')] += 1
    key = tuple(counts)             # tuple, because list is unhashable

    Time:  O(n · k)          <- the k log k is gone
    Space: O(n · k)

    "eat"  ->  a b c d e ... n ... t ... z
               1 0 0 0 1     0     1     0     -> (1,0,0,0,1,0,...,1,...,0)
    "tea"  ->  same vector, because counting does not care about order.

⚠️  WHY `tuple(...)` AND NOT THE LIST ITSELF
    A dict key must be hashable, and hashable in Python means immutable-by-
    contract. `list` defines `__hash__ = None`, so:

        buckets[[1,0,...]]  ->  TypeError: unhashable type: 'list'

    `tuple` is hashable. This is the single most common runtime error people
    hit on this problem. The tests below trigger it live.

⚠️  IS O(k) ACTUALLY FASTER HERE?
    Not always — and the crossover is measurable. `sorted` is optimised C;
    the counting loop is interpreted Python bytecode. So at SHORT lengths the
    worse-big-O approach wins on constant factors alone. The benchmark at the
    bottom of this file measures it live; on this machine it reports roughly:

        k = 10     sorted wins      (C sort beats an interpreted loop)
        k = 100    count wins       (crossover is somewhere in 10 < k < 100)
        k = 1000   count wins ~2x   (asymptotics take over)

    Quote O(n·k) as THE answer — it is the correct asymptotic claim and the
    one the interviewer wants. But knowing that a 10-character string sorts
    faster than it counts is what separates a memorised answer from an
    understood one. If they ask "which is actually faster?", the honest reply
    is "depends on k; let me tell you where the crossover is."


================================================================================
APPROACH 3 · Frozen Counter (the "I know the stdlib" one-liner)
================================================================================
    key = frozenset(Counter(s).items())

Correct and hashable, but slower than both of the above (builds a Counter, then
a set of tuples) and it obscures the idea. Mention it, don't lead with it.

A common WRONG variant:

    key = frozenset(s)              # ✗ BROKEN

`frozenset("aab") == frozenset("ab")` — a set drops multiplicity, so "aab" and
"ab" collide and get grouped together. The tests below demonstrate this failing
on real input. Multiplicity is exactly what an anagram is about.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    n = number of strings, k = max string length, A = alphabet size (26)

    Approach            Time            Extra space   Mutates input?
    ------------------  --------------  ------------  --------------
    Pairwise compare    O(n²·k)         O(nk)         no
    Sorted key      ✅  O(n·k log k)    O(nk)         no
    Count vector  ✅✅  O(n·k)          O(nk + n·A)   no
    Frozen Counter      O(n·k)          O(nk)         no

    "Extra space" here is dominated by the output, which is unavoidable: every
    input string appears exactly once in the result.


================================================================================
EDGE CASES
================================================================================
    [""]              -> [[""]]
                         The empty string is its own anagram class. sorted("")
                         is "" and the count vector is all zeros — both handle
                         it with no special case. Do NOT add an `if not s`
                         branch; it is dead code.

    ["a"]             -> [["a"]]
                         Single string, single group. Guards against code that
                         assumes a group has >= 2 members.

    ["a","a","a"]     -> [["a","a","a"]]
                         DUPLICATES ARE NOT DEDUPLICATED. A string is an
                         anagram of itself. If you reached for a set anywhere
                         in the bucket, you lose copies. Buckets are lists.

    ["ab","ba","abc"] -> [["ab","ba"],["abc"]]
                         Different lengths can never be anagrams — and both key
                         functions get this for free (different key length /
                         different count sum). No length pre-check needed.


================================================================================
COMMON MISTAKES
================================================================================
1. Using a list as the dict key —> `TypeError: unhashable type: 'list'`.
   Wrap it: `tuple(counts)`.

2. Using `sorted(s)` (a list) as the key instead of `"".join(sorted(s))` or
   `tuple(sorted(s))`. Same unhashable error.

3. `frozenset(s)` as the key — silently WRONG, not an error. It discards
   letter counts, so "aab" and "ab" merge. Silent wrong answers are worse than
   crashes.

4. Building groups by pairwise anagram checks. Correct but O(n²k); it is the
   thing the problem is testing you *not* to do.

5. Deduplicating with a set inside a bucket, dropping legitimate repeats.

6. Returning `buckets` (the dict) instead of `list(buckets.values())`.

7. Reinitialising `counts = [0]*26` OUTSIDE the per-string loop, so counts
   accumulate across strings and every key after the first is garbage.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if the strings are Unicode, not just a–z?
A: The [26] array dies — you cannot index arbitrary code points. Fall back to
   the sorted key, or `tuple(sorted(Counter(s).items()))`. Also beware that
   Unicode has multiple encodings of the same grapheme; normalise with
   `unicodedata.normalize("NFC", s)` first or "é" vs "é" compare unequal.

Q: What if the input does not fit in memory?
A: External grouping — map each string to its key, write (key, string) pairs to
   disk sharded by hash(key) % M, then group each shard independently. This is
   literally MapReduce's canonical example.

Q: Can you avoid storing all groups, and just return the LARGEST group?
A: Yes — keep only a running max bucket. Still O(nk) time but O(k) extra beyond
   the winner.

Q: How would you make this parallel?
A: The key function is pure and per-string, so map it across threads/processes,
   then merge dicts. Merging is associative, so it parallelises cleanly.


================================================================================
RELATED PROBLEMS — the canonical-key family
================================================================================
    LC 242  Valid Anagram              — the 2-string case; same canonical form
    LC 438  Find All Anagrams          — canonical form + SLIDING WINDOW over
                                          the count vector
    LC 567  Permutation in String      — same as 438, boolean answer
    LC 249  Group Shifted Strings      — key = tuple of consecutive char deltas
    LC 1002 Find Common Characters     — element-wise MIN of count vectors
    LC 205  Isomorphic Strings         — canonical form = pattern of first
                                          occurrence indices, e.g. "egg"->(0,1,1)
    LC 890  Word Pattern Match         — same normalise-then-compare idea
================================================================================
"""

import time
from collections import Counter, defaultdict
from typing import List


class Solution:
    def groupAnagrams(self, strs: List[str]) -> List[List[str]]:
        """Count-vector key. Time O(n*k), space O(n*k). Does not mutate input."""
        buckets = defaultdict(list)
        for s in strs:
            counts = [0] * 26                       # INSIDE the loop — one per string
            for ch in s:
                counts[ord(ch) - ord("a")] += 1
            buckets[tuple(counts)].append(s)        # tuple(): list is unhashable
        return list(buckets.values())

    # ------------------------------------------------------------------
    # Alternatives.
    # ------------------------------------------------------------------
    def groupAnagrams_sorted(self, strs: List[str]) -> List[List[str]]:
        """Sorted-string key. Time O(n*k log k). The one to write first."""
        buckets = defaultdict(list)
        for s in strs:
            buckets["".join(sorted(s))].append(s)
        return list(buckets.values())

    def groupAnagrams_counter(self, strs: List[str]) -> List[List[str]]:
        """frozenset of Counter items — correct, hashable, slower."""
        buckets = defaultdict(list)
        for s in strs:
            buckets[frozenset(Counter(s).items())].append(s)
        return list(buckets.values())

    def groupAnagrams_broken_frozenset(self, strs: List[str]) -> List[List[str]]:
        """✗ BROKEN ON PURPOSE — frozenset(s) discards letter multiplicity."""
        buckets = defaultdict(list)
        for s in strs:
            buckets[frozenset(s)].append(s)
        return list(buckets.values())


# ==============================================================================
# TESTS — run:  python 007_group_anagrams_solution.py
# ==============================================================================
def _norm(groups):
    """Order-insensitive comparison: sort within each group, then sort groups."""
    return sorted(sorted(g) for g in groups)


def run_tests() -> None:
    sol = Solution()
    cases = [
        (["eat", "tea", "tan", "ate", "nat", "bat"],
         [["ate", "eat", "tea"], ["bat"], ["nat", "tan"]]),
        ([""], [[""]]),
        (["a"], [["a"]]),
        (["abc", "cba", "bac", "xyz"], [["abc", "bac", "cba"], ["xyz"]]),
        (["a", "a", "a"], [["a", "a", "a"]]),
        (["ab", "ba", "abc", "cab", "bca"], [["ab", "ba"], ["abc", "bca", "cab"]]),
        (["aab", "ab"], [["aab"], ["ab"]]),      # the frozenset trap
    ]
    impls = [
        ("count vector ", sol.groupAnagrams),
        ("sorted key   ", sol.groupAnagrams_sorted),
        ("frozen Counter", sol.groupAnagrams_counter),
    ]
    all_ok = True
    for name, fn in impls:
        ok = all(_norm(fn(list(strs))) == _norm(exp) for strs, exp in cases)
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {name} ({len(cases)} cases)")

    # ----------------------------------------------------------------------
    # The canonical form, made visible.
    # ----------------------------------------------------------------------
    print("\n--- the two canonical keys, side by side ---")
    print(f"  {'word':<6} {'sorted key':<12} {'count-vector key (nonzero slots only)'}")
    for w in ["eat", "tea", "ate", "tan", "nat", "bat"]:
        c = [0] * 26
        for ch in w:
            c[ord(ch) - ord("a")] += 1
        nonzero = {chr(i + 97): n for i, n in enumerate(c) if n}
        print(f"  {w:<6} {''.join(sorted(w)):<12} {nonzero}")
    print("  -> identical keys within a group, distinct keys across groups")

    # ----------------------------------------------------------------------
    # ⚠️  A list cannot be a dict key. Watch it fail.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  why tuple() and not the raw list ---")
    d = {}
    try:
        d[[1, 0, 1]] = "eat"
        print("  list key accepted?!  (should never print)")
    except TypeError as e:
        print(f"  d[[1,0,1]] = ...   -> TypeError: {e}")
    d[(1, 0, 1)] = "eat"
    print(f"  d[(1,0,1)] = ...   -> OK, dict is now {d}")

    # ----------------------------------------------------------------------
    # ⚠️  frozenset(s) is silently wrong — it drops multiplicity.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  frozenset(s) as the key: WRONG, and it does not crash ---")
    trap = ["aab", "ab", "ba", "aba"]
    print(f"  input                {trap}")
    print(f"  frozenset('aab')  =  {sorted(frozenset('aab'))}")
    print(f"  frozenset('ab')   =  {sorted(frozenset('ab'))}   <- same set!")
    print(f"  broken result        {sol.groupAnagrams_broken_frozenset(list(trap))}")
    print(f"  correct result       {sol.groupAnagrams(list(trap))}")
    print("  'aab' is NOT an anagram of 'ab' — sets forget how many times.")

    # ----------------------------------------------------------------------
    # ⚠️  Hoisting counts out of the loop poisons every later key.
    # ----------------------------------------------------------------------
    print("\n--- ⚠️  counts = [0]*26 declared OUTSIDE the loop ---")
    buckets = defaultdict(list)
    counts = [0] * 26                      # the bug: shared across strings
    for s in ["eat", "tea", "bat"]:
        for ch in s:
            counts[ord(ch) - ord("a")] += 1
        nz = {chr(i + 97): n for i, n in enumerate(counts) if n}
        print(f"  after {s!r:<6} key = {nz}")
        buckets[tuple(counts)].append(s)
    print(f"  result {list(buckets.values())}  <- 3 groups; every key is unique")
    print("  counts accumulated across strings, so no two words can ever match.")

    # ----------------------------------------------------------------------
    # Asymptotics vs constant factors — the honest benchmark.
    # ----------------------------------------------------------------------
    print("\n--- O(k) vs O(k log k): asymptotics are not the whole story ---")
    import random
    random.seed(7)
    for k in (10, 100, 1000):
        words = ["".join(random.choice("abcdefghijklmnopqrstuvwxyz")
                         for _ in range(k)) for _ in range(2000)]
        t0 = time.perf_counter()
        sol.groupAnagrams_sorted(words)
        t_sort = time.perf_counter() - t0
        t0 = time.perf_counter()
        sol.groupAnagrams(words)
        t_count = time.perf_counter() - t0
        winner = "count" if t_count < t_sort else "sorted"
        print(f"  k={k:<5} sorted {t_sort*1000:7.1f}ms   count {t_count*1000:7.1f}ms"
              f"   -> {winner} wins")
    print("  At small k, sorted's C implementation beats an interpreted count")
    print("  loop despite the worse big-O. Quote O(n·k) as the answer, and know")
    print("  the constant factors when they ask 'which is actually faster?'.")

    # ----------------------------------------------------------------------
    # Duplicates survive; the empty string is a real group.
    # ----------------------------------------------------------------------
    print("\n--- edge cases that break naive code ---")
    for strs in ([""], ["a", "a", "a"], ["ab", "ba", "abc"]):
        print(f"  {str(strs):<22} -> {sol.groupAnagrams(list(strs))}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
