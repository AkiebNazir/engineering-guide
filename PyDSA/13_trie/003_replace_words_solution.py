"""
================================================================================
SOLUTION · LeetCode 648 · Replace Words                                 [Medium]
https://leetcode.com/problems/replace-words/
================================================================================

THE CORE IDEA
--------------
Build ONE trie from the whole root dictionary. For each word in the
sentence, walk the trie character by character and STOP at the first
`is_word` you hit — that first hit is guaranteed to be the SHORTEST root
that prefixes this word, precisely because you haven't gone any deeper into
the trie yet than necessary. If the walk runs off the trie (or off the
word) before ever hitting `is_word`, no root applies and the original word
survives unchanged. This is topic guide Part 3, reason 5: "walk once, stop
at the first match" replaces what would otherwise be "try every prefix
length as a separate lookup".


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): for each word in the
sentence, for each root in the dictionary, check `word.startswith(root)`
and keep the shortest match. O(W * R * L) where W = words in sentence,
R = number of roots, L = average length. With W and R both up to 1000 and
L up to 100, that's on the order of 10^8 character comparisons — the demo
below prices this against the trie on a smaller but still telling scale
(the full LeetCode bound would take too long to run in a test suite).

Approach 1 (sort roots by length, first startswith match wins): sorting
the dictionary once by length (O(R log R)) lets a per-word scan stop at
the first match in sorted order, guaranteeing shortest-wins without
re-comparing lengths — but the per-word scan is still O(R * L) in the
worst case (a word matching no root scans the whole sorted list). Same
asymptotic class as approach 0, just with a friendlier tie-break.

Approach 2 (trie, stop at first is_word) ✅ — the answer. Build the trie
once: O(sum of root lengths). Then each sentence word costs O(word length)
regardless of how many roots exist — R drops OUT of the per-word cost
entirely. Overall O(sum of root lengths + sum of sentence word lengths).


================================================================================
STEP BY STEP TRACE
================================================================================
dictionary = ["cat", "bat", "rat"], word = "cattle"

trie:
    root
     ├─c─a─t(word)
     ├─b─a─t(word)
     └─r─a─t(word)

walk "cattle" from the root, one character at a time:
    i=0 'c': root.children has 'c' -> move to c-node. c-node.is_word? No.
    i=1 'a': c-node.children has 'a' -> move to a-node. is_word? No.
    i=2 't': a-node.children has 't' -> move to t-node. is_word? YES.
             STOP HERE. Return "cat" (word[:3]), ignore "tle".

word = "battery" -> same shape: b-a-t hits is_word at i=2 -> "bat".
word = "the"     -> root.children has no 't' matching a root path that
                    ends in is_word before the string runs out (there is
                    no root "the", "th", or "t" in the dictionary) -> walk
                    breaks with no is_word ever seen -> keep "the" as-is.

Tie-break trace: dictionary = ["cat", "cattle"], word = "cattle"
    walk hits is_word=True at i=2 (end of "cat") FIRST, and returns
    IMMEDIATELY without continuing to i=5 where "cattle" is also a word.
    Stopping at the first hit IS the shortest-root rule — no length
    comparison needed, it falls out of the walk order for free.


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                         Time                               Space   Mutates input?
    --------------------------------  ---------------------------------  ------  --------------
    Brute force (per word, per root)  O(W * R * L)                       O(1)    no
    Sorted roots, first startswith    O(R log R + W * R * L) worst case  O(1)    no
    Trie, stop-at-first-is_word ✅    O(sum(root lens) + sum(word lens)) O(sum(root lens)) no

    W = words in sentence, R = number of roots, L = average word/root
    length. The trie's per-word cost is bounded by that WORD's own length,
    completely independent of how many roots are in the dictionary.


================================================================================
EDGE CASES
================================================================================
    word has no matching root       -> walk breaks (missing edge) or runs
                                        out of trie depth without ever
                                        hitting is_word -> word unchanged.
    word IS itself exactly a root    -> the walk hits is_word exactly at
                                        the word's own last character ->
                                        replaced by itself (no visible
                                        change, but exercises the boundary).
    multiple roots match, keep       -> "cat" AND "cattle" both roots of
    shortest                            "cattle" -> stop-at-first-hit
                                        naturally returns "cat" (see trace).
    root longer than the word it      -> walk runs off the END of the word
    might have matched                  before reaching the root's own
                                        is_word node -> no match, word kept.
    single-word sentence              -> `.split()`/`.join()` must handle a
                                        sentence with no spaces at all.
    root equals a whole dictionary     -> repeated/duplicate roots in the
    word repeated in dictionary          input dictionary must not break
                                        insertion (idempotent, same as 001).


================================================================================
COMMON MISTAKES
================================================================================
1. Not stopping at the FIRST `is_word` — continuing the walk to find the
   LONGEST match instead, which silently violates the "shortest root wins"
   requirement (e.g. wrongly returning "cattle" full-length instead of
   "cat" when both are roots).

2. Building a NEW trie (or re-scanning the whole dictionary) per sentence
   word instead of once up front — turns an O(R) one-time cost into an
   O(W * R) repeated cost, defeating the entire point of using a trie here.

3. Forgetting to preserve words that have NO matching root — a walk that
   runs off the trie (missing edge) must fall back to the ORIGINAL word,
   not an empty string or a partial prefix.

4. Off-by-one when slicing the matched root out of the word: using
   `word[:i]` vs `word[:i+1]` — get this wrong and either the last matched
   character is dropped or one extra unmatched character is kept.

5. Using `str.split(" ")` when the input could (in general trie/string
   problems) have irregular whitespace — this problem guarantees exactly
   one space between words, but the plain `.split()` (no argument) is the
   safer default habit since it also collapses accidental repeats.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if ties should prefer the LEXICOGRAPHICALLY SMALLEST root instead
   of the shortest?
A: Stopping at the first is_word no longer suffices on its own for a tie
   at the SAME depth (same length, different content) — but two roots of
   the same word can't both be prefixes of it unless they're identical, so
   this variant doesn't actually arise for prefix roots; it would matter
   for a DIFFERENT problem (e.g. picking among several equal-length exact
   matches from a separate structure).

Q: The dictionary is huge (millions of roots) and rebuilt per query batch.
   How do you avoid rebuilding the trie every time?
A: Amortize it — build the trie once from the dictionary, keep it in
   memory (or persist and reload it) across sentence batches. Only rebuild
   when the ROOT dictionary itself changes, not per sentence.

Q: How would you support Unicode words, not just lowercase ASCII?
A: The dict-of-children TrieNode handles it with zero code changes (topic
   guide Part 1.1) — the fixed-array variant would not.

Q: What's the worst case for trie SIZE here (space, not time)?
A: O(sum of all root character counts) if roots share no prefixes at all;
   shared prefixes (e.g. "cat", "cats", "catnip") reduce this because they
   share trie nodes — same shared-prefix saving as any other trie build.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 208  Implement Trie (this topic, 001)        — the base walk this
            problem specializes with an early-stop condition
    LC 677  Map Sum Pairs (this topic, 004)          — augmenting nodes
            with data instead of stopping early
    LC 14   Longest Common Prefix                    — the mirror problem:
            shortest COMMON prefix across many strings, not per-word lookup
    LC 720  Longest Word in Dictionary                — trie DFS collecting
            the deepest fully-buildable chain of is_word nodes
================================================================================
"""

import random
import string
import time


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False


class Solution:
    def replaceWords(self, dictionary: list[str], sentence: str) -> str:
        root = TrieNode()
        for w in dictionary:
            node = root
            for ch in w:
                if ch not in node.children:
                    node.children[ch] = TrieNode()
                node = node.children[ch]
            node.is_word = True

        def shortest_root(word: str) -> str:
            node = root
            for i, ch in enumerate(word):
                if ch not in node.children:
                    return word           # no root matches; keep as-is
                node = node.children[ch]
                if node.is_word:
                    return word[:i + 1]   # first hit == shortest root
            return word                    # ran off the end, never hit is_word

        return " ".join(shortest_root(w) for w in sentence.split())


# ==============================================================================
# Brute-force baseline used only by the runtime demo below.
# ==============================================================================
def replace_words_brute_force(dictionary, sentence):
    roots_by_len = sorted(dictionary, key=len)

    def shortest_root(word):
        for r in roots_by_len:
            if word.startswith(r):
                return r
        return word

    return " ".join(shortest_root(w) for w in sentence.split())


# ==============================================================================
# TESTS — run:  python 003_replace_words_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness ---")
    sol = Solution()
    cases = [
        (["cat", "bat", "rat"], "the cattle was rattled by the battery",
         "the cat was rat by the bat"),
        (["a", "b", "c"], "aadsfasf absbs bbab cadsfafs", "a a b c"),
        (["cat", "cattle"], "cattle", "cat"),          # tie -> shortest wins
        (["ca", "cat"], "catnip", "ca"),                # shortest of two matches
        ([], "the quick fox", "the quick fox"),          # no roots at all
        (["xyz"], "the quick fox", "the quick fox"),      # no root applies
        (["a"], "a", "a"),                                # word == root exactly
    ]
    for dictionary, sentence, want in cases:
        got = sol.replaceWords(dictionary, sentence)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  dict={dictionary!r:<22} -> {got!r}  (want {want!r})")

    # --------------------------------------------------------------------
    # Trace, printed explicitly.
    # --------------------------------------------------------------------
    print("\n--- trace: dict=[cat,bat,rat], word='cattle' ---")
    root = TrieNode()
    for w in ("cat", "bat", "rat"):
        node = root
        for ch in w:
            node = node.children.setdefault(ch, TrieNode())
        node.is_word = True
    node, word = root, "cattle"
    for i, ch in enumerate(word):
        if ch not in node.children:
            print(f"  i={i} '{ch}': missing edge -> keep '{word}' unchanged")
            break
        node = node.children[ch]
        hit = node.is_word
        print(f"  i={i} '{ch}': edge exists, is_word={hit}"
              + (f"  -> STOP, return {word[:i+1]!r}" if hit else ""))
        if hit:
            break

    # --------------------------------------------------------------------
    # Cross-check vs the sorted-brute-force baseline.
    # --------------------------------------------------------------------
    print("\n--- randomised cross-check: trie vs sorted brute-force ---")
    random.seed(648)
    alphabet = string.ascii_lowercase
    dictionary = list({"".join(random.choices(alphabet, k=random.randint(1, 4)))
                        for _ in range(60)})
    words = ["".join(random.choices(alphabet, k=random.randint(1, 8)))
             for _ in range(400)]
    sentence = " ".join(words)
    got_trie = sol.replaceWords(dictionary, sentence)
    got_brute = replace_words_brute_force(dictionary, sentence)
    ok = got_trie == got_brute
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  400-word sentence, 60 roots: "
          f"trie and brute-force agree: {ok}")

    # --------------------------------------------------------------------
    # DEMO: trie replace vs brute-force replace, larger scale.
    # --------------------------------------------------------------------
    print("\n--- DEMO: trie O(word len) per word vs brute-force O(R*L) per word ---")
    print("  (many roots, many sentence words -- the shape where R stops")
    print("   mattering for the trie but keeps costing the scanner)")
    random.seed(3)
    big_dict = list({"".join(random.choices(alphabet, k=random.randint(3, 8)))
                      for _ in range(500)})
    # Most sentence words are built by extending a real root, so a
    # brute-force scan usually can't bail out on the very first comparison
    # -- it has to walk deep into the sorted root list before matching.
    big_words = []
    for _ in range(80_000):
        base = random.choice(big_dict) if random.random() < 0.7 else ""
        suffix = "".join(random.choices(alphabet, k=random.randint(0, 6)))
        big_words.append(base + suffix if base else suffix or "x")
    big_sentence = " ".join(big_words)

    t0 = time.perf_counter()
    out_trie = sol.replaceWords(big_dict, big_sentence)
    t1 = time.perf_counter()
    out_brute = replace_words_brute_force(big_dict, big_sentence)
    t2 = time.perf_counter()

    same = out_trie == out_brute
    all_ok &= same
    trie_t, brute_t = t1 - t0, t2 - t1
    print(f"  {len(big_dict)} roots, {len(big_words)} sentence words")
    print(f"  trie:          {trie_t * 1000:8.2f} ms")
    print(f"  sorted brute:  {brute_t * 1000:8.2f} ms")
    print(f"  trie is {brute_t / trie_t:6.1f}x faster; results identical: {same}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
