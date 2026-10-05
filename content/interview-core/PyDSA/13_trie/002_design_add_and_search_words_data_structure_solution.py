"""
================================================================================
SOLUTION · LeetCode 211 · Design Add and Search Words Data Structure     [Medium]
https://leetcode.com/problems/design-add-and-search-words-data-structure/
================================================================================

THE CORE IDEA
--------------
`addWord` is exactly problem 001's `insert`, unchanged. `search` can no
longer be a straight-line walk, because a `.` doesn't name one edge to
follow — it means "any live child is a candidate". So `search` becomes a
DFS: at a normal character, follow the one matching edge (if it exists,
same as before); at a `.`, FAN OUT and recurse into every child, returning
True the moment any branch succeeds. This is a direct generalisation of
001's `_walk`, replacing "one edge or fail" with "one edge, or all edges,
or fail" (topic guide Part 4).


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): keep a `list[str]` of
added words. `addWord` is O(1). `search(word)` scans every stored word and
character-matches it against the pattern (treating '.' as wildcard),
O(N*L) per query where N = words stored, L = word length. With up to 10^4
calls this is up to 10^8 character comparisons in the worst case — the
demo below prices exactly this scan against the trie.

Approach 1 (regex): compile `word.replace('.', '.')` (already regex syntax)
with `^...$` anchors and re.match against every stored word — same O(N*L)
class as approach 0, with added regex-engine overhead per call. No
different in asymptotics; slower in practice due to compilation and the
regex engine's own bookkeeping.

Approach 2 (trie + DFS fan-out) ✅ — the answer. `addWord` is O(L). `search`
without any '.' is O(L), identical to a plain trie search. `search` WITH
'.' explores every live branch at each dot position: worst case
O(26^(number of dots) * L), but LeetCode explicitly caps dots at 2 per
query, so the real worst case is O(26^2 * L) = O(676*L) — small and
constant, and in practice far less because most branches die immediately
(topic guide Part 4).


================================================================================
STEP BY STEP TRACE
================================================================================
addWord("bad"), addWord("dad"), addWord("mad")

              root
             / | \\
            b  d  m
            |  |  |
            a  a  a
            |  |  |
       d(word) d(word) d(word)

search(".ad")
    dfs(root, i=0), pattern[0] = '.'  -> FAN OUT over ALL of root's children
        try 'b': dfs(b-node, i=1), pattern[1]='a' -> follow edge 'a' (exists)
            dfs(a-node, i=2), pattern[2]='d' -> follow edge 'd' (exists)
                dfs(d-node, i=3), i==len(pattern) -> return d-node.is_word -> True
            branch 'b' returns True -> ANY() short-circuits, no need to try
            'd' or 'm' at all
    overall -> True

search("b..")
    dfs(root,i=0), pattern[0]='b' -> follow edge 'b' (exists), no fan-out yet
        dfs(b-node,i=1), pattern[1]='.' -> FAN OUT over b-node's children:
            only 'a' exists -> dfs(a-node, i=2), pattern[2]='.' -> FAN OUT
            over a-node's children: only 'd' exists -> dfs(d-node, i=3),
            i==len(pattern) -> return d-node.is_word -> True
    overall -> True   (both dots had exactly ONE live child each here, so
                        the fan-out degenerated to a straight walk)

search("pad")
    dfs(root,i=0), pattern[0]='p' -> 'p' not in root.children -> dead
    overall -> False   (no fan-out ever triggered, dies in one step)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    addWord   search (no dots)  search (k dots)  Mutates input?
    ---------------------------  --------  -----------------  ---------------  --------------
    list[str] brute force        O(1)      O(N*L)             O(N*L)           no
    regex over list[str]         O(1)      O(N*L)+regex ovhd  O(N*L)+regex ovhd no
    Trie + DFS fan-out ✅        O(L)      O(L)               O(26^k * L)      no

    N = words stored, L = pattern length, k = number of '.' in the query
    (LeetCode bounds k <= 2, so 26^k <= 676 — effectively a small constant).
    Space: O(total characters inserted) for the trie (shared prefixes
    reduce this), O(recursion depth) = O(L) extra per search call.


================================================================================
EDGE CASES
================================================================================
    search("...") all dots      -> fans out at every level; degenerates
                                    toward "does any word of this exact
                                    length exist" — exercises full fan-out.
    search on empty trie        -> dfs(root, 0) immediately hits i==0==len
                                    only if pattern is also "" (see below);
                                    otherwise the first char's fan-out finds
                                    no children -> False.
    search("")                  -> i == len(word) == 0 on the ROOT itself
                                    -> True only if "" was addWord'ed.
    pattern longer than any      -> every branch dies before reaching the
    stored word                     base case; DFS returns False cleanly,
                                     no crash on running past a leaf (node
                                     is None check happens BEFORE indexing).
    all-dots pattern matching     -> the demo below builds a case where a
    many candidate words            fan-out must explore several branches
                                     before finding the one that is_word.


================================================================================
COMMON MISTAKES
================================================================================
1. Forgetting the `node is None` guard before recursing — chasing
   `node.children.get(ch)` into a dead branch and then calling `.children`
   on `None` crashes. Must check `if node is None: return False` at the
   TOP of every recursive call, mirroring the wildcard pattern in the
   topic guide Part 4.

2. Checking `node.is_word` at the WRONG point — e.g. checking it before
   confirming `i == len(word)`. A node can be `is_word=True` while the
   query pattern still has characters left to match; the length check must
   come first (identical root-bug to 001's search/startsWith mixup, just
   inside a DFS instead of a loop).

3. Not short-circuiting the fan-out — using `all(...)` instead of
   `any(...)` for the `.` case, or iterating without early return, wastes
   work by exploring dead branches after a match was already found. `any()`
   with a generator expression stops at the first True.

4. Off-by-one on `i`: incrementing `i` in the wrong place, or passing the
   remaining SUBSTRING (`word[i+1:]`) as a new string each recursive call
   instead of an index — the substring version silently works but is
   O(L^2) extra from the repeated slicing, and doesn't compose cleanly if
   you also memoize.

5. Rebuilding the "any live child" iteration as `node.children.values()`
   fresh on every call when it could be captured once — a performance nit,
   not a correctness bug, but worth mentioning if asked to optimize.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: What if '.' could match ZERO or more characters (glob-style '*'), not
   exactly one?
A: Different problem shape — that needs a 2D DP or a different recursion
   that also tries "consume the '*' and stay at the same trie node" in
   addition to "consume one character and advance", closer to LC 44/10
   (Wildcard/Regex Matching) than to a pure trie walk.

Q: How would you bound the fan-out cost if dots weren't capped at 2?
A: The bound becomes O(26^k * L) which is exponential in the number of
   dots — for large k you'd want to fall back to scanning the word list
   directly (approach 0) once k crosses some threshold, since the trie's
   advantage evaporates when almost every level fans out.

Q: Support deleting a word?
A: Same idea as 001's follow-up — walk to the word's end (no wildcards
   involved in addWord), clear is_word, prune dead branches bottom-up.

Q: Compare to just using a `set` of words and, for '.' patterns, grouping
   by LENGTH first?
A: Grouping stored words by length narrows a brute-force scan to only
   same-length candidates (O(len-bucket size * L) instead of O(N*L)), which
   helps when lengths vary a lot but doesn't change the asymptotics when
   most words share a length — the trie's DFS fan-out still generally wins
   because it prunes per-CHARACTER, not just per-length.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 208  Implement Trie (this topic, 001)     — the straight-line walk
            this problem generalises with wildcard fan-out
    LC 212  Word Search II (this topic, 006)     — trie DFS again, this time
            walking a 2D grid in lockstep instead of a linear pattern
    LC 44   Wildcard Matching                     — '*' and '?' over two
            strings, a DP problem, NOT a trie problem — good contrast case
    LC 425  Word Squares                          — trie prefix lookups
            driving a backtracking search over a grid of words
================================================================================
"""

import random
import string
import time


class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_word = False


class WordDictionary:
    def __init__(self):
        self.root = TrieNode()

    def addWord(self, word: str) -> None:
        node = self.root
        for ch in word:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
        node.is_word = True

    def search(self, word: str) -> bool:
        def dfs(node, i):
            if node is None:
                return False
            if i == len(word):
                return node.is_word
            ch = word[i]
            if ch == '.':
                return any(dfs(child, i + 1) for child in node.children.values())
            return dfs(node.children.get(ch), i + 1)

        return dfs(self.root, 0)


# ==============================================================================
# Brute-force baseline used only by the runtime demo below.
# ==============================================================================
class BruteForceWordDictionary:
    def __init__(self):
        self.words = []

    def addWord(self, word: str) -> None:
        self.words.append(word)

    def search(self, word: str) -> bool:
        for w in self.words:
            if len(w) != len(word):
                continue
            if all(p == '.' or p == c for p, c in zip(word, w)):
                return True
        return False


# ==============================================================================
# TESTS — run:  python 002_design_add_and_search_words_data_structure_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness ---")
    wd = WordDictionary()
    for w in ("bad", "dad", "mad"):
        wd.addWord(w)
    cases = [
        ("pad", False), ("bad", True), (".ad", True), ("b..", True),
        ("...", True), ("....", False), ("", False),
        ("ba.", True), ("..d", True), ("b.d", True),
    ]
    for pattern, want in cases:
        got = wd.search(pattern)
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  search({pattern!r:8}) -> {got}  (want {want})")

    print("\n--- edge case: search('') true only after addWord('') ---")
    wd2 = WordDictionary()
    ok = wd2.search("") is False
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  search('') before addWord('') -> False")
    wd2.addWord("")
    ok = wd2.search("") is True
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  search('') after addWord('')  -> True")

    # --------------------------------------------------------------------
    # Trace, printed explicitly.
    # --------------------------------------------------------------------
    print("\n--- trace: addWord(bad,dad,mad), search('.ad') ---")

    def traced_search(root, word):
        def dfs(node, i, path):
            if node is None:
                print(f"  {path}: dead branch -> False")
                return False
            if i == len(word):
                print(f"  {path}: end of pattern, is_word={node.is_word}")
                return node.is_word
            ch = word[i]
            if ch == '.':
                print(f"  {path}: '.' at i={i} -> fan out over {sorted(node.children)}")
                for c, child in node.children.items():
                    if dfs(child, i + 1, path + c):
                        return True
                return False
            print(f"  {path}: follow '{ch}' -> {'exists' if ch in node.children else 'MISSING'}")
            return dfs(node.children.get(ch), i + 1, path + ch)

        return dfs(root, 0, "")

    result = traced_search(wd.root, ".ad")
    print(f"  result: {result}")

    # --------------------------------------------------------------------
    # Cross-check: trie DFS agrees with the brute-force scanner.
    # --------------------------------------------------------------------
    print("\n--- randomised cross-check: trie DFS vs brute-force scanner ---")
    random.seed(211)
    alphabet = string.ascii_lowercase
    words = list({"".join(random.choices(alphabet, k=random.randint(2, 6)))
                  for _ in range(200)})
    real_wd, brute_wd = WordDictionary(), BruteForceWordDictionary()
    for w in words:
        real_wd.addWord(w)
        brute_wd.addWord(w)
    mismatches, trials = 0, 3000
    for _ in range(trials):
        base = random.choice(words)
        pattern = list(base)
        for _ in range(random.randint(0, 2)):
            idx = random.randrange(len(pattern))
            pattern[idx] = '.'
        pattern = "".join(pattern)
        if real_wd.search(pattern) != brute_wd.search(pattern):
            mismatches += 1
    ok = mismatches == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  {trials} trials, {mismatches} mismatches")

    # --------------------------------------------------------------------
    # DEMO: trie DFS vs brute-force scan on a bigger dictionary.
    # --------------------------------------------------------------------
    print("\n--- DEMO: wildcard search — trie DFS fan-out vs brute-force scan ---")
    random.seed(2)
    n_words = 15_000
    big_words = list({"".join(random.choices(alphabet, k=random.randint(4, 8)))
                       for _ in range(n_words)})
    fast_wd, slow_wd = WordDictionary(), BruteForceWordDictionary()
    for w in big_words:
        fast_wd.addWord(w)
        slow_wd.addWord(w)

    # Build queries with exactly 2 dots (LeetCode's stated cap), a realistic
    # worst case for the trie's fan-out.
    queries = []
    for w in random.sample(big_words, 200):
        chars = list(w)
        idxs = random.sample(range(len(chars)), min(2, len(chars)))
        for idx in idxs:
            chars[idx] = '.'
        queries.append("".join(chars))

    t0 = time.perf_counter()
    trie_out = [fast_wd.search(q) for q in queries]
    t1 = time.perf_counter()
    brute_out = [slow_wd.search(q) for q in queries]
    t2 = time.perf_counter()

    same = trie_out == brute_out
    all_ok &= same
    trie_t, brute_t = t1 - t0, t2 - t1
    print(f"  dictionary size N = {len(big_words)}, {len(queries)} two-dot queries")
    print(f"  trie DFS:      {trie_t * 1000:8.2f} ms")
    print(f"  brute scan:    {brute_t * 1000:8.2f} ms")
    print(f"  trie is {brute_t / trie_t:6.1f}x faster; results identical: {same}")
    print("  (both dots per query bound the fan-out to <= 26^2, so the trie")
    print("   still wins decisively even in its documented worst case)")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
