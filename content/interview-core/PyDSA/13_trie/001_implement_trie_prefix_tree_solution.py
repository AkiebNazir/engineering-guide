"""
================================================================================
SOLUTION · LeetCode 208 · Implement Trie (Prefix Tree)                  [Medium]
https://leetcode.com/problems/implement-trie-prefix-tree/
================================================================================

THE CORE IDEA
--------------
A trie is a tree where the PATH from the root spells a string, one character
per edge. Every node along a path is a prefix of whatever word(s) run through
it; a boolean `is_word` on a node marks "a full inserted word ends exactly
here" — that flag is the only thing that separates "app" being a stored word
from "app" being merely a prefix of "apple". Insert walks the path, creating
missing nodes lazily; search/startsWith walk the same path and differ in
exactly one check at the end (topic guide Part 2).

    insert("apple")     root -a-> a -p-> p -p-> p -l-> l -e-> e(is_word=True)
    search("apple")     walk the same path, end reached, is_word? -> True
    search("app")       walk root-a-p-p, end reached, is_word? -> FALSE
                         ("app" node exists as a PATH but was never marked)
    startsWith("app")   walk root-a-p-p, end reached -> True (existence only,
                                                               is_word ignored)


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): keep a plain `list[str]`
of inserted words. `insert` is O(1) append. `search(word)` is `word in
words` -> O(N) worst case (compare against every stored word, each
comparison up to O(L)). `startsWith(prefix)` is even worse: O(N*L), a scan
of every word checking `w.startswith(prefix)` since no data structure
groups words by shared prefix. With N = 30,000 calls per LeetCode's own
constraint, and each search scanning up to N stored words, this is
O(N^2*L) across a full test run — the demo below prices this literally.

Approach 1 (hash set for search, still nothing for prefix): a `set[str]`
fixes `search` to O(L) average (hash the whole string once). It does NOT
help `startsWith` at all — a hash set has no notion of "things that start
with X" short of scanning every element, same O(N*L) as approach 0. This is
exactly topic guide Part 3, reason 1: prefix queries are the trie's whole
reason to exist over a hash set.

Approach 2 (trie, dict-of-children) ✅ — the answer. `TrieNode.children` is
a `dict[str, TrieNode]`; `is_word` marks word ends. All three operations are
one O(L) walk, independent of how many words N are stored. See topic guide
Part 1.1 for why `dict` is the right default in Python.

Approach 3 (trie, fixed `[26]`-array-of-children): identical algorithm,
`children = [None] * 26` indexed by `ord(c) - ord('a')`. Same O(L) time.
Only valid because this problem's constraint guarantees lowercase-only
input; see topic guide Part 1.2 for when this breaks. Demo 2 below measures
both variants on this machine.


================================================================================
STEP BY STEP TRACE
================================================================================
Trie() -> root = TrieNode(children={}, is_word=False)

insert("apple")
    node=root, ch='a': 'a' not in root.children -> create it. node = a-node
    node=a,    ch='p': create.                     node = p1-node
    node=p1,   ch='p': create.                     node = p2-node
    node=p2,   ch='l': create.                     node = l-node
    node=l,    ch='e': create.                      node = e-node
    loop ends -> e-node.is_word = True

    root
     └─a
        └─p
           └─p
              └─l
                 └─e (is_word=True)

search("apple")
    walk root -a-> a -p-> p1 -p-> p2 -l-> l -e-> e   (every edge exists)
    reached e-node, e-node.is_word is True -> return True

search("app")
    walk root -a-> a -p-> p1 -p-> p2                 (every edge exists)
    reached p2-node, p2-node.is_word is False -> return False
    ("app" is a real PATH in the trie, just never marked as a full word)

startsWith("app")
    same walk as above, reaches p2-node successfully
    startsWith does NOT check is_word -> return True

insert("app")
    node=root, ch='a': exists, reuse.                node = a
    node=a,    ch='p': exists, reuse.                node = p1
    node=p1,   ch='p': exists, reuse.                node = p2
    loop ends -> p2.is_word = True     (NO new nodes created — path already
                                          existed from inserting "apple")

    root
     └─a
        └─p
           └─p (is_word=True)   <-- now also a word
              └─l
                 └─e (is_word=True)

search("app")   -> now walks to p2, p2.is_word is True -> True
    (Same traversal as before insert; only the flag changed.)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    insert    search      startsWith   Mutates input?
    ---------------------------  --------  ----------  -----------  --------------
    list[str] (brute force)      O(1)      O(N*L)      O(N*L)       no
    set[str]                     O(L) avg  O(L) avg    O(N*L)       no
    Trie, dict-of-children ✅    O(L)      O(L)        O(L)         no
    Trie, [26]-array             O(L)      O(L)        O(L)         no

    N = number of stored words, L = length of the word/prefix being
    inserted or queried. The trie's O(L) is independent of N — that
    independence is the entire point (topic guide Part 1 intro).
    Space: O(total characters across all inserted words) worst case for
    the trie (shared prefixes reduce this below the naive sum), O(sum of
    word lengths) for list/set either way.


================================================================================
EDGE CASES
================================================================================
    insert same word twice     -> idempotent: the path already exists, only
                                   `is_word` gets set (again) to True. No
                                   duplicate nodes, no crash. Tested below.
    search before any insert   -> `_walk` returns None on the very first
                                   character -> False. Root always exists,
                                   even in a fresh Trie.
    startsWith("") / search("")-> loop body never runs (empty string), so
                                   `_walk` returns the ROOT itself. search("")
                                   is True only if "" was explicitly inserted
                                   (root.is_word); startsWith("") is always
                                   True (every trie "starts with" nothing).
    one word is a prefix of    -> "app" and "apple" both inserted must each
    another                       independently report search()==True (this
                                   IS the test above; see topic guide Part 5,
                                   "leaf" and "is_word" are unrelated).
    prefix that's never a word -> startsWith True, search False — the
                                   defining case that catches the is_word bug.
    single character            -> smallest non-trivial path; sanity-checks
                                   is_word is set on the FIRST node reached.


================================================================================
COMMON MISTAKES
================================================================================
1. Skipping the `is_word` check in `search`, so it returns True for any
   PREFIX of an inserted word, not just a fully inserted word (insert
   "apple", search("app") wrongly -> True). This is the single most common
   trie bug — see topic guide Part 2's warning box.

2. Using `node.children.get(ch) or TrieNode()` in `insert` — the `or`
   discards a legitimately falsy-but-existing node object incorrectly is
   not actually possible here since TrieNode objects are always truthy, but
   the more common variant of this mistake is calling `.setdefault(ch,
   TrieNode())` which ALWAYS constructs a new TrieNode (wasteful — it just
   gets thrown away when the key already exists) instead of checking `if ch
   not in node.children` first.

3. Conflating "no children" with "is a word" (topic guide Part 5) instead
   of tracking `is_word` as its own field — breaks the moment one inserted
   word is a strict prefix of another.

4. Reusing a single `TrieNode()` instance as the default for multiple dict
   keys (a classic "mutable default" mistake) — every branch would then
   alias the SAME node, corrupting the whole trie. Always construct a fresh
   `TrieNode()` per missing edge.

5. For the `[26]`-array variant: not validating input stays within
   `a`-`z`, letting `ord(c) - ord('a')` produce an out-of-range or negative
   index — silent corruption or `IndexError` (topic guide Part 1.2).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Support delete(word)?
A: Walk to the word's end node, clear `is_word`. Then prune bottom-up: walk
   back up along the path just used, deleting each node that now has zero
   children AND is not itself a word-end for some OTHER word. Must stop
   pruning the moment a node is still a live prefix of something else.

Q: Support "get all words with this prefix" (autocomplete)?
A: Walk to the prefix's node (same O(L) as startsWith), then DFS the
   subtree below it collecting every node with is_word=True, prepending the
   prefix. Cost is O(L + number of matches).

Q: What if the alphabet isn't lowercase ASCII (unicode, digits, symbols)?
A: The dict-of-children implementation needs zero changes — a dict key can
   be any hashable character. The `[26]`-array variant breaks immediately;
   this is the concrete reason to default to dict in Python.

Q: How would you reduce memory for a huge, sparse dictionary?
A: A radix tree / Patricia trie collapses chains of single-child nodes into
   one edge labeled with a substring instead of one node per character —
   trading a bit of code complexity for far fewer node objects when many
   words share nothing but rare short prefixes.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 211  Design Add and Search Words (this topic, 002) — same trie, DFS
            fan-out to handle '.' wildcards instead of a straight walk
    LC 648  Replace Words (this topic, 003)                — walk to the
            first is_word instead of the full word
    LC 677  Map Sum Pairs (this topic, 004)                — augment nodes
            with a value instead of just is_word
    LC 212  Word Search II (this topic, 006)               — one trie shared
            across a whole grid DFS
    LC 421  Maximum XOR of Two Numbers (this topic, 005)   — the same
            node-per-branch idea over bits instead of characters
================================================================================
"""

import random
import string
import time


class TrieNode:
    def __init__(self):
        self.children = {}   # char -> TrieNode
        self.is_word = False


class Trie:
    def __init__(self):
        self.root = TrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_word = True

    def _walk(self, s: str):
        """Shared traversal for search/startsWith. Returns the node reached,
        or None if the path breaks partway through."""
        node = self.root
        for ch in s:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and node.is_word

    def startsWith(self, prefix: str) -> bool:
        return self._walk(prefix) is not None


# ==============================================================================
# Variants used only by the runtime demos below — not part of the required API.
# ==============================================================================
class BruteForceWordSet:
    """Approach 0: plain list. search/startsWith are O(N*L)."""

    def __init__(self):
        self.words = []

    def insert(self, word: str) -> None:
        self.words.append(word)

    def search(self, word: str) -> bool:
        return word in self.words

    def startsWith(self, prefix: str) -> bool:
        return any(w.startswith(prefix) for w in self.words)


class ArrayTrieNode:
    __slots__ = ("children", "is_word")

    def __init__(self):
        self.children = [None] * 26
        self.is_word = False


class ArrayTrie:
    """Approach 3: fixed [26]-array-of-children. Lowercase ASCII only."""

    def __init__(self):
        self.root = ArrayTrieNode()

    def insert(self, word: str) -> None:
        node = self.root
        for ch in word:
            i = ord(ch) - 97
            if node.children[i] is None:
                node.children[i] = ArrayTrieNode()
            node = node.children[i]
        node.is_word = True

    def search(self, word: str) -> bool:
        node = self.root
        for ch in word:
            node = node.children[ord(ch) - 97]
            if node is None:
                return False
        return node.is_word

    def startsWith(self, prefix: str) -> bool:
        node = self.root
        for ch in prefix:
            node = node.children[ord(ch) - 97]
            if node is None:
                return False
        return True


# ==============================================================================
# TESTS — run:  python 001_implement_trie_prefix_tree_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness: dict-based trie (the answer) ---")
    trie = Trie()
    trie.insert("apple")
    checks = [
        (trie.search("apple"), True, 'search("apple") after insert("apple")'),
        (trie.search("app"), False, 'search("app") before it is inserted'),
        (trie.startsWith("app"), True, 'startsWith("app")'),
    ]
    trie.insert("app")
    checks.append((trie.search("app"), True, 'search("app") after insert("app")'))
    for got, want, label in checks:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<45} -> {got}  (want {want})")

    print("\n--- edge cases ---")
    t2 = Trie()
    edge_checks = [
        (t2.search("x"), False, "search on empty trie"),
        (t2.startsWith(""), True, 'startsWith("") on any trie'),
        (t2.search(""), False, 'search("") before "" inserted'),
    ]
    t2.insert("")
    edge_checks.append((t2.search(""), True, 'search("") after insert("")'))
    t3 = Trie()
    t3.insert("a")
    edge_checks.append((t3.search("a"), True, "single-character word"))
    t3.insert("a")  # duplicate insert
    edge_checks.append((t3.search("a"), True, "duplicate insert stays correct"))
    for got, want, label in edge_checks:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<45} -> {got}  (want {want})")

    print("\n--- cross-check: ArrayTrie agrees with the dict Trie ---")
    random.seed(208)
    alphabet = string.ascii_lowercase
    words = ["".join(random.choices(alphabet, k=random.randint(1, 8)))
             for _ in range(500)]
    dict_trie, arr_trie = Trie(), ArrayTrie()
    for w in words:
        dict_trie.insert(w)
        arr_trie.insert(w)
    mismatches = 0
    for _ in range(2000):
        probe = ("".join(random.choices(alphabet, k=random.randint(1, 8)))
                 if random.random() < 0.5 else random.choice(words))
        if dict_trie.search(probe) != arr_trie.search(probe):
            mismatches += 1
        if dict_trie.startsWith(probe) != arr_trie.startsWith(probe):
            mismatches += 1
    ok = mismatches == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  2000 random search/startsWith probes, "
          f"dict vs array trie: {mismatches} mismatches")

    # --------------------------------------------------------------------
    # DEMO 1: trie startsWith vs brute-force scan-every-word.
    # --------------------------------------------------------------------
    print("\n--- DEMO 1: startsWith — trie O(L) vs brute-force O(N*L) scan ---")
    random.seed(1)
    n_words = 20_000
    dictionary = list({"".join(random.choices(alphabet, k=random.randint(3, 10)))
                        for _ in range(n_words)})
    trie_big = Trie()
    brute = BruteForceWordSet()
    for w in dictionary:
        trie_big.insert(w)
        brute.insert(w)

    queries = [w[:3] for w in random.sample(dictionary, 300)]

    t0 = time.perf_counter()
    trie_results = [trie_big.startsWith(q) for q in queries]
    t1 = time.perf_counter()
    brute_results = [brute.startsWith(q) for q in queries]
    t2 = time.perf_counter()

    trie_time = t1 - t0
    brute_time = t2 - t1
    same = trie_results == brute_results
    all_ok &= same
    print(f"  dictionary size N = {len(dictionary)}, {len(queries)} startsWith queries")
    print(f"  trie:         {trie_time * 1000:8.2f} ms")
    print(f"  brute force:  {brute_time * 1000:8.2f} ms")
    print(f"  trie is {brute_time / trie_time:6.0f}x faster; results identical: {same}")

    # --------------------------------------------------------------------
    # DEMO 2: dict-of-children vs [26]-array-of-children, build + query.
    # --------------------------------------------------------------------
    print("\n--- DEMO 2: dict-of-children vs [26]-array-of-children (this machine) ---")
    words_100k = ["".join(random.choices(alphabet, k=random.randint(3, 10)))
                  for _ in range(100_000)]
    probe_words = random.sample(words_100k, 2000)

    t0 = time.perf_counter()
    dt = Trie()
    for w in words_100k:
        dt.insert(w)
    t1 = time.perf_counter()
    for w in probe_words:
        dt.search(w)
    t2 = time.perf_counter()
    dict_build, dict_query = t1 - t0, t2 - t1

    t0 = time.perf_counter()
    at = ArrayTrie()
    for w in words_100k:
        at.insert(w)
    t1 = time.perf_counter()
    for w in probe_words:
        at.search(w)
    t2 = time.perf_counter()
    arr_build, arr_query = t1 - t0, t2 - t1

    print(f"  100,000 words, {len(probe_words)} search() probes (all times in ms)")
    print(f"  {'':<10}{'build':>12}{'query':>12}{'total':>12}")
    print(f"  {'dict':<10}{dict_build*1000:12.1f}{dict_query*1000:12.1f}"
          f"{(dict_build+dict_query)*1000:12.1f}")
    print(f"  {'array':<10}{arr_build*1000:12.1f}{arr_query*1000:12.1f}"
          f"{(arr_build+arr_query)*1000:12.1f}")
    faster = "array" if (arr_build + arr_query) < (dict_build + dict_query) else "dict"
    print(f"  faster overall on THIS run: {faster} "
          f"({abs((dict_build+dict_query)-(arr_build+arr_query))*1000:.1f} ms apart)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
