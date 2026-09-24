"""
================================================================================
SOLUTION · LeetCode 336 · Palindrome Pairs                             [Hard]
https://leetcode.com/problems/palindrome-pairs/
================================================================================

THE CORE IDEA
--------------
`words[i] + words[j]` is a palindrome exactly when the concatenation
splits into a palindromic "core" flanked by two pieces that are exact
reverses of each other. Concretely, split `words[i]` at every possible
position `j` into `prefix = words[i][:j]` and `suffix = words[i][j:]`.
Two symmetric cases cover every way a palindrome pair can arise:

- **Case A -- `prefix` is itself a palindrome.** Then for ANY other word
  `words[k]` that equals `reverse(suffix)`, the concatenation
  `words[k] + words[i] = reverse(suffix) + prefix + suffix` is a
  palindrome. Proof by direct reversal: reversing that string gives
  `reverse(suffix) + reverse(prefix) + suffix`, and since `prefix` is a
  palindrome `reverse(prefix) == prefix`, so the reversed string equals
  the original.
- **Case B -- `suffix` is itself a palindrome.** Then for any other word
  `words[k]` that equals `reverse(prefix)`, the concatenation
  `words[i] + words[k] = prefix + suffix + reverse(prefix)` is a
  palindrome, by the mirror-image of the same argument (`suffix` being a
  palindrome plays the role `prefix` played above).

So the whole problem reduces to: for every word and every split point,
check "is the prefix a palindrome?" / "is the suffix a palindrome?" (an
O(L) two-pointer check), and if so, look up whether the EXACT REVERSE of
the other half exists elsewhere in the word list (an O(1) hashmap lookup,
after building `word -> index` once up front). No pairwise comparison of
whole words against each other is ever needed -- every candidate partner
is found by reversing a PIECE of the current word and asking the hashmap
"does this exact string exist?"


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, priced, coded below only for the cross-check
demo on small inputs): for every ordered pair `(i, j)` with `i != j`,
concatenate `words[i] + words[j]` and check directly whether it's a
palindrome. O(n^2 * L) time (n^2 pairs, each an O(L) concatenation +
check), O(1) extra space beyond the output. Correct, but the problem
explicitly demands sub-quadratic-in-`n` behavior, which this fails at
`n` up to 5000.

Approach 1 (chosen) -- hashmap of `word -> index` plus a per-word,
per-split-point two-pointer palindrome check, exactly as derived above.
For each of the `n` words, try all `L+1` split points; at each split,
an O(L) two-pointer palindrome check on the shorter piece plus an O(1)
hashmap lookup on the reversed other piece. O(n * L^2) total time in the
worst case (each split's palindrome check and string reversal costs up
to O(L), times O(L) split points, times `n` words), O(n * L) extra space
for the hashmap and the reversed-piece strings. This is the standard,
widely-accepted solution to this exact LeetCode problem and the one most
interviewers expect.

Approach 2 (variant, described, not coded) -- trie of REVERSED words:
insert every word, REVERSED, into a trie (see topic 13), and at each trie
node store the index of any word whose remaining unconsumed suffix (at
that point in the trie) is itself a palindrome. Walking `words[i]`
character by character down this trie of reversed words finds every
partner `words[k]` such that `words[k] + words[i]` or `words[i] +
words[k]` is a palindrome, in time proportional to `words[i]`'s length
plus the number of palindromic-suffix matches encountered along the way.
This achieves the problem's literally-stated O(sum of `words[i].length`)
bound (ignoring the output size), at the cost of a considerably more
intricate trie structure (storing "is the remaining suffix at this node
a palindrome" per node, and handling both directions of concatenation) --
worth naming as the theoretically optimal answer, but the hashmap
approach above is what's actually expected to be hand-coded under
interview time pressure.


================================================================================
STEP BY STEP TRACE
================================================================================
words = ["abcd", "dcba", "lls", "s", "sssll"]   (LC's own Example 1)
word_to_idx = {"abcd":0, "dcba":1, "lls":2, "s":3, "sssll":4}

Processing i=1, word="dcba" (finding the [0,1] pair):
    split j=0: prefix="" (trivially a palindrome), suffix="dcba"
        Case A: reverse(suffix) = reverse("dcba") = "abcd"
        "abcd" IS in word_to_idx, at index 0, and 0 != 1
        -> pair (word_to_idx["abcd"]=0, i=1) = [0, 1]  ADDED

Processing i=0, word="abcd" (finding the [1,0] pair, symmetric to above):
    split j=0: prefix="", suffix="abcd"
        Case A: reverse(suffix) = reverse("abcd") = "dcba"
        "dcba" IS in word_to_idx, at index 1, and 1 != 0
        -> pair (1, 0) = [1, 0]  ADDED

Processing i=2, word="lls" (finding the [3,2] pair):
    split j=0: prefix="", suffix="lls" -> reverse="sll", not in map.
               suffix "lls" is NOT a palindrome (Case B skipped).
    split j=1: prefix="l" (palindrome), suffix="ls" -> reverse="sl",
               not in map.
               suffix "ls" is NOT a palindrome (Case B skipped).
    split j=2: prefix="ll" (palindrome, two-pointer check: 'l'=='l' at
               the two ends, collapses to nothing in the middle) ->
               reverse(suffix="s") = "s"
        "s" IS in word_to_idx, at index 3, and 3 != 2
        -> pair (word_to_idx["s"]=3, i=2) = [3, 2]  ADDED

               Case B at j=2 (j != n=3): suffix="s" is a palindrome,
               reverse(prefix="ll") = "ll" -- NOT in word_to_idx (only
               "lls" exists, not "ll") -> no pair.
    split j=3 (=n, full word): prefix="lls" is NOT a palindrome (skip
               Case A); Case B skipped entirely since j == n.

Processing i=2, word="lls" continued (finding the [2,4] pair -- the
fourth pair in this example, easy to miss on a first read):
    split j=2: prefix="ll" (palindrome) -> reverse(suffix="s") = "s"
               (this is the SAME split that found [3,2] above -- Case A
               at this split point can only ever add one pair, the "s"
               lookup, already covered).
    split j=0: prefix="" (palindrome) -> reverse(suffix="lls") = "sll"
               -- not in word_to_idx, no pair from here.

    The [2,4] pair is actually found while processing i=4,
    word="sssll" instead:
    split j=2: prefix="ss" (palindrome, two-pointer check on "ss"
               passes trivially) -> reverse(suffix="sll") = "lls"
        "lls" IS in word_to_idx, at index 2, and 2 != 4
        -> pair (word_to_idx["lls"]=2, i=4) = [2, 4]  ADDED
        (sanity check: words[2] + words[4] = "lls" + "sssll" =
        "llssssll", which reads identically forwards and backwards --
        "ll" mirrors "ll" on the outside, "ssss" mirrors itself in the
        middle.)

Final result: [[0,1], [1,0], [3,2], [2,4]]  -- matches LC's expected
output exactly (order may vary; this is one valid enumeration order).
Note that [4,2] is correctly NOT produced: "sssll"+"lls" = "ssslllls",
which is NOT a palindrome (its own reverse is "sllllsss") -- only ONE
of the two concatenation orders happens to work here, and the algorithm
must -- and does -- distinguish them.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              Time         Space   Mutates input?
    -----------------------------------------------------------------------
    All-pairs concatenate+check [priced]  O(n^2 * L)   O(1)*    no
    Hashmap + per-split palindrome
    check [chosen]                        O(n * L^2)   O(n*L)   no
    Trie of reversed words [variant]      O(sum L)     O(sum L) no

    n = len(words), L = max word length. *Beyond the output list itself.
    The chosen approach trades an `n^2` factor for an `L^2` factor,
    which is the right trade when `n` is large relative to `L` (here
    `n` up to 5000 vs `L` up to 300) -- exactly the regime this
    problem's constraints are set up to reward.


================================================================================
EDGE CASES
================================================================================
    the empty string "" is one
    of the words                -> every other word `w` that is ITSELF a
                                    palindrome pairs with "" in both
                                    orders: `"" + w = w` (palindrome iff
                                    `w` is) and `w + "" = w` (same). The
                                    algorithm handles this without any
                                    special case: at word `w`'s own split
                                    j=0, prefix="" is trivially a
                                    palindrome and reverse(suffix) =
                                    reverse(w); if `w` is itself a
                                    palindrome, reverse(w) == w, so the
                                    lookup finds `w` itself at its OWN
                                    index -- explicitly rejected by the
                                    `k != i` guard, which is exactly why
                                    that guard exists. The pairing with
                                    the SEPARATE empty-string word is
                                    instead found by processing word `w`
                                    at split j=len(w): Case A there needs
                                    reverse(suffix="") = "" to be in the
                                    map (true, it's the empty-string
                                    word) and prefix=w to be a palindrome
                                    -- giving pair (empty_idx, w_idx).
    two words are exact reverses
    of each other but NEITHER is
    individually a palindrome
    (e.g. "abcd"/"dcba")        -> both directions found independently,
                                    one from each word's own j=0 split
                                    (see the trace above) -- neither word
                                    needs to BE a palindrome itself.
    duplicate-looking words     -> constraints guarantee `words` is a
                                    list of UNIQUE strings, so the
                                    hashmap lookup is never ambiguous
                                    about which index a matched string
                                    belongs to.
    a word that is a palindrome
    all by itself, alone (no
    empty string, no reverse
    partner in the list)        -> produces zero pairs from that word,
                                    correctly -- being a palindrome alone
                                    is not sufficient, it needs an actual
                                    partner (itself concatenated with
                                    itself is excluded by `i != j`).
    words containing only 1
    character                   -> always palindromes; still need an
                                    actual reverse-match partner (which,
                                    for length 1, is themselves) to form
                                    a pair -- correctly produces nothing
                                    unless duplicated content exists
                                    elsewhere (impossible here since
                                    words are unique) or paired with "".


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the `k != i` self-match guard -- Case A's lookup can find
   the CURRENT word's own index when its reversed suffix happens to
   equal a substring of itself in a way that maps back to `i` (most
   commonly when the whole word is a palindrome and `j=0`), incorrectly
   pairing a word with itself.
2. Not excluding `j == n` (full-length split) from Case B -- produces an
   exact DUPLICATE of a pair already found by Case A at `j=0` on the
   OTHER word (see the CORE IDEA / trace: the "whole word is an exact
   reverse of another whole word" scenario is fully covered by Case A
   alone, processed from both words' own j=0 splits).
3. Materializing and reversing substrings unnecessarily inside the
   palindrome CHECK itself -- checking whether `word[a:b]` is a
   palindrome via `word[a:b] == word[a:b][::-1]` works but allocates two
   extra strings per check; a two-pointer scan directly over index range
   `[a, b)` on the original string avoids that allocation (a minor
   constant-factor point, but the kind of detail that shows up in a
   careful interview answer).
4. Treating this as "find all pairs whose reverse relationship holds
   globally" (i.e. just checking `reverse(words[i]) == words[j]`) --
   that only catches the SPECIAL case where the two words are exact
   reverses of each other with no leftover palindromic core; it misses
   the general case (like `"lls"`/`"s"` in the trace above) where one
   word is longer and only part of it needs to reverse-match.
5. Building the O(n^2 * L) all-pairs solution and calling it done despite
   the problem's explicit complexity requirement -- passes on tiny test
   inputs but times out (or is flagged) at `n` near 5000.


================================================================================
FOLLOW-UPS AN INTERVIEWER MAY ASK
================================================================================
- "Can you actually hit the stated O(sum of `words[i].length`) bound?" ->
  Only with the trie-of-reversed-words approach (Approach 2): build once
  in O(sum L), then each word's own lookup costs O(its own length) plus
  O(number of matches found), with no per-word L^2 factor. Worth naming
  even if you implement the hashmap approach as your primary answer.
- "What if `words` could contain duplicates?" -> The hashmap needs to
  map each string to a LIST of indices (not a single index), since a
  duplicate word could pair with either the K != i` guard would then need
  to allow the SAME string at a DIFFERENT index (two separate list
  entries with identical content but distinct positions are a valid
  pair) -- this problem's constraints rule that out by guaranteeing
  uniqueness, but it's a natural generalization to ask about.
- "How would you extend this to return palindrome TRIPLES (i, j, k) with
  `words[i]+words[j]+words[k]` a palindrome?" -> Meaningfully harder;
  the clean two-case split argument here relies on there being exactly
  ONE join point between two strings, and generalizing it to two join
  points (three strings) breaks the simple "one piece must already be a
  palindrome" structure -- this is a good signal that the interviewer is
  probing whether you understand WHY the 2-string version works, not
  just how to code it.


================================================================================
RELATED PROBLEMS
================================================================================
- Trie topic (13) -- Approach 2's "trie of reversed words with
  palindrome-suffix annotations per node" is a direct, if advanced,
  application of that topic's trie-as-a-prefix-index pattern, here
  walked in REVERSE to turn "does a suffix match" into "does a prefix of
  the reversed word match."
- Shortest Palindrome (LC 214, this topic, 006) -- also hinges on
  "is THIS piece of the string a palindrome," there answered via a KMP
  failure function over a constructed string instead of a direct
  two-pointer scan; different mechanism, same underlying question shape.
- Valid Palindrome (LC 125, topic 02) and Valid Palindrome II (LC 680,
  topic 02) -- the exact two-pointer palindrome CHECK used per split
  point here, at the single-string level rather than embedded inside a
  pairing search.
- Group Anagrams (LC 49, topic 01) -- another "index the collection by a
  transformed key, then do O(1) lookups instead of O(n^2) pairwise
  comparisons" problem; here the transform is "reverse a piece," there
  it's "sort the characters."
================================================================================
"""

import random
import string
import time


class Solution:
    def palindromePairs(self, words: list) -> list:
        word_to_idx = {w: i for i, w in enumerate(words)}
        result = []

        for i, word in enumerate(words):
            n = len(word)
            for j in range(n + 1):
                # Case A: word[:j] is a palindrome -> look for
                # reverse(word[j:]) elsewhere; pair is (that_index, i).
                if self._is_palindrome(word, 0, j - 1):
                    rev_suffix = word[j:][::-1]
                    k = word_to_idx.get(rev_suffix)
                    if k is not None and k != i:
                        result.append([k, i])

                # Case B: word[j:] is a palindrome (and j isn't the
                # full-length split, to avoid duplicating Case A's
                # whole-word-reversal pairs) -> look for reverse(word[:j])
                # elsewhere; pair is (i, that_index).
                if j != n and self._is_palindrome(word, j, n - 1):
                    rev_prefix = word[:j][::-1]
                    k = word_to_idx.get(rev_prefix)
                    if k is not None and k != i:
                        result.append([i, k])

        return result

    @staticmethod
    def _is_palindrome(word: str, lo: int, hi: int) -> bool:
        """Two-pointer palindrome check over word[lo..hi] inclusive,
        with no substring materialized."""
        while lo < hi:
            if word[lo] != word[hi]:
                return False
            lo += 1
            hi -= 1
        return True


def _brute_force_palindrome_pairs(words: list) -> list:
    """Priced O(n^2 * L) baseline: check every ordered pair directly,
    used only for the cross-check demo below."""
    result = []
    n = len(words)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            combined = words[i] + words[j]
            if combined == combined[::-1]:
                result.append([i, j])
    return result


def run_tests() -> None:
    all_ok = True
    sol = Solution()

    def as_set(pairs):
        return {tuple(p) for p in pairs}

    cases = [
        (["abcd", "dcba", "lls", "s", "sssll"],
         {(0, 1), (1, 0), (3, 2), (2, 4)}),
        (["bat", "tab", "cat"],
         {(0, 1), (1, 0)}),
        (["a", ""],
         {(0, 1), (1, 0)}),
        (["ab", "ba"],
         {(0, 1), (1, 0)}),
        (["abc", "def"],
         set()),
    ]
    for words, expected in cases:
        got = as_set(sol.palindromePairs(words))
        ok = got == expected
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  palindromePairs({words!r}) "
              f"-> {sorted(got)} (expected {sorted(expected)})")

    print()
    print("CROSS-CHECK -- hashmap+two-pointer vs brute force, 200 random word lists")
    print("-" * 72)
    random.seed(47)
    mismatch = 0
    for _ in range(200):
        count = random.randint(1, 8)
        seen_words = set()
        words = []
        while len(words) < count:
            length = random.randint(0, 5)
            w = "".join(random.choice("ab") for _ in range(length))
            if w not in seen_words:
                seen_words.add(w)
                words.append(w)
        r1 = as_set(sol.palindromePairs(words))
        r2 = as_set(_brute_force_palindrome_pairs(words))
        if r1 != r2:
            mismatch += 1
            print(f"  MISMATCH on {words!r}: chosen={sorted(r1)} brute={sorted(r2)}")
    cross_ok = mismatch == 0
    all_ok &= cross_ok
    print(f"{'PASS' if cross_ok else 'FAIL'}  {200 - mismatch}/200 agree "
          f"({mismatch} mismatches)")

    print()
    print("RUNTIME DEMO -- hashmap+two-pointer vs O(n^2 L) brute force")
    print("-" * 72)
    random.seed(53)
    seen_words = set()
    words = []
    while len(words) < 600:
        length = random.randint(1, 10)
        w = "".join(random.choice(string.ascii_lowercase[:4]) for _ in range(length))
        if w not in seen_words:
            seen_words.add(w)
            words.append(w)

    t0 = time.perf_counter()
    fast_result = as_set(sol.palindromePairs(words))
    fast_ms = (time.perf_counter() - t0) * 1000

    t0 = time.perf_counter()
    brute_result = as_set(_brute_force_palindrome_pairs(words))
    brute_ms = (time.perf_counter() - t0) * 1000

    agree = fast_result == brute_result
    all_ok &= agree
    print(f"n={len(words)} words, pairs found = {len(fast_result)}")
    print(f"  hashmap + two-pointer: {fast_ms:9.2f} ms")
    print(f"  brute force O(n^2 L):  {brute_ms:9.2f} ms")
    if fast_ms > 0:
        print(f"  measured: hashmap approach is {brute_ms / max(fast_ms, 1e-6):.1f}x "
              f"faster here -- the gap grows roughly linearly with n as n increases "
              f"further, since brute force is quadratic in n and this approach is "
              f"linear in n (quadratic only in the much smaller word length L).")
    print(f"{'PASS' if agree else 'FAIL'}  both approaches agree on the pair set")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
