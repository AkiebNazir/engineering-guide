"""
================================================================================
SOLUTION · LeetCode 1268 · Search Suggestions System                    [Medium]
https://leetcode.com/problems/search-suggestions-system/
================================================================================

THE CORE IDEA
--------------
Two correct designs:

    SORT + BINARY SEARCH   Words sharing a prefix form one contiguous block in
                           sorted order. bisect_left(products, prefix) finds
                           where the block would start; take up to three words
                           from there that really start with the prefix.

    TRIE WITH TOP-3        Insert words in sorted order; every node keeps the
                           first three words that pass through it, which are
                           therefore its three smallest. Each keystroke moves
                           one node down and reads the list.

The trie is the shape of a real autocomplete service: precomputed top-k per
prefix, O(1) work per keystroke. The sorted list is the least code.


================================================================================
APPROACH 1 · Filter all products per prefix (priced, used as oracle)
================================================================================
    for each prefix: sorted(p for p in products if p.startswith(prefix))[:3]

    Time: O(m * n * L) — m prefixes, n products, L compare length
    Space: O(n)


================================================================================
APPROACH 2 · Sort + binary search ✅ (the answer for this problem)
================================================================================
    products.sort()
    out, prefix = [], ""
    for ch in searchWord:
        prefix += ch
        i = bisect_left(products, prefix)
        out.append([p for p in products[i:i + 3] if p.startswith(prefix)])

WHY CONTIGUOUS. If a < b < c in sorted order and a and c both start with
prefix P, then b is sandwiched between two strings that begin with P, so b
must begin with P too. So the matches are one block.

WHY bisect_left IS THE START. Any string starting with P is >= P, and any
string < P doesn't start with P. So the first index with products[i] >= P is
where the block starts, IF the block is non-empty. That "if" is why the
startswith filter is required: products[i] might be "b" when the prefix is
"ap".

    Time: O(n log n * L) sort + O(m * L * log n) searches    Space: O(n) for sort


================================================================================
APPROACH 3 · Trie with top-3 lists
================================================================================
    root = Node()
    for word in sorted(products):
        node = root
        for ch in word:
            node = node.children.setdefault(ch, Node())
            if len(node.top) < 3:
                node.top.append(word)

    answer: walk searchWord; once a character is missing, every remaining
            prefix gets [].

    Time: O(n log n * L) sort + O(total chars) build + O(m) query
    Space: O(total chars) nodes + O(3 * total chars) references

This wins when you answer MANY queries against the same products.


================================================================================
APPROACH 4 · Two pointers narrowing a sorted range
================================================================================
Keep lo, hi over the sorted list. For the i-th typed character, advance lo
while products[lo] is too short or its i-th char < ch; retreat hi similarly.
The window [lo, hi] always holds exactly the matching words.

    Time: O(n log n * L) sort + O(n + m) narrowing    Space: O(1) extra


================================================================================
STEP BY STEP TRACE · products sorted = [mobile, moneypot, monitor, mouse, mousepad]
================================================================================
    prefix  bisect_left  products[i:i+3]                  startswith filter
    ------  -----------  -------------------------------  ----------------------------
    m       0            mobile, moneypot, monitor        all three
    mo      0            mobile, moneypot, monitor        all three
    mou     3            mouse, mousepad                  both
    mous    3            mouse, mousepad                  both
    mouse   3            mouse, mousepad                  both


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                    Build             Per keystroke       Mutates input?
    --------------------------  ----------------  ------------------  ---------------
    Filter per prefix           —                 O(n * L)            No
    Sort + bisect ✅            O(n log n * L)    O(L log n)          YES if sorted
                                                                       in place (we copy)
    Trie with top-3             O(total chars)    O(1) + output       No
    Two-pointer narrowing       O(n log n * L)    amortized O(1)      No


================================================================================
EDGE CASES
================================================================================
    No match at all            Every list is [].
    Match stops mid-word        Once empty, stays empty for longer prefixes.
    Fewer than three matches    Return what exists.
    Word equals a product       That product is included (it has the prefix).
    Prefix sorts before a
      non-matching word         bisect lands on e.g. "b" for "ap" — filter it.


================================================================================
COMMON MISTAKES
================================================================================
1. Taking products[i:i+3] without the startswith filter. Demo: ["apple",
   "apricot", "b"] with "ap" returns "b" as a suggestion.

2. Forgetting to sort first. The binary search and the "three smallest"
   requirement both depend on it.

3. In the trie, inserting UNSORTED words and keeping the first three. You'd
   get insertion order, not lexicographic order.

4. Rebuilding `prefix` with a fresh slice each time is fine (length <= 1000);
   rebuilding by searching the whole product list each time is the slow part.


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Rank by popularity instead of alphabetically?
A: Store (score, word) and keep a top-3 by score at each trie node. Updates
   must bubble changes up the path. Design Search Autocomplete System
   (25_design/010) is exactly this.

Q: Millions of products, thousands of QPS?
A: Precompute top-k per prefix offline (MapReduce/Dataflow over query logs),
   store in a key-value store keyed by prefix, cache hot prefixes at the edge.
   Shard by prefix. That's the autocomplete system design problem.

Q: Typo tolerance?
A: Fuzzy search: walk the trie with an edit-distance budget (Levenshtein
   automaton), or use n-gram indexes.


================================================================================
RELATED PROBLEMS
================================================================================
    LC 208   Implement Trie (001)
    LC 642   Design Search Autocomplete System (25_design/010)
    LC 720   Longest Word in Dictionary
    LC 35    Search Insert Position (05_binary_search) — the bisect_left idea
================================================================================
"""

import bisect
import random
import time
from typing import Dict, List


class Solution:
    def suggestedProducts(self, products: List[str], searchWord: str) -> List[List[str]]:
        products = sorted(products)
        out: List[List[str]] = []
        prefix = ""
        for ch in searchWord:
            prefix += ch
            i = bisect.bisect_left(products, prefix)
            out.append([p for p in products[i:i + 3] if p.startswith(prefix)])
        return out


# ------------------------------------------------------------------------
# Alternatives / oracle / broken version for the demos.
# ------------------------------------------------------------------------
class TrieNode:
    __slots__ = ("children", "top")

    def __init__(self) -> None:
        self.children: Dict[str, "TrieNode"] = {}
        self.top: List[str] = []


def build_trie(products: List[str]) -> TrieNode:
    root = TrieNode()
    for word in sorted(products):
        node = root
        for ch in word:
            node = node.children.setdefault(ch, TrieNode())
            if len(node.top) < 3:
                node.top.append(word)
    return root


def suggest_trie(root: TrieNode, word: str) -> List[List[str]]:
    out: List[List[str]] = []
    node = root
    for ch in word:
        node = node.children.get(ch) if node else None
        out.append(list(node.top) if node else [])
    return out


def suggest_two_pointers(products: List[str], word: str) -> List[List[str]]:
    products = sorted(products)
    lo, hi = 0, len(products) - 1
    out: List[List[str]] = []
    for i, ch in enumerate(word):
        while lo <= hi and (len(products[lo]) <= i or products[lo][i] != ch):
            lo += 1
        while lo <= hi and (len(products[hi]) <= i or products[hi][i] != ch):
            hi -= 1
        out.append(products[lo:min(lo + 3, hi + 1)])
    return out


def suggest_filter(products: List[str], word: str) -> List[List[str]]:
    return [sorted(p for p in products if p.startswith(word[:i]))[:3] for i in range(1, len(word) + 1)]


def suggest_no_filter_bug(products: List[str], word: str) -> List[List[str]]:
    """Mistake 1: trusts the three words after bisect_left without checking the prefix."""
    products = sorted(products)
    return [products[bisect.bisect_left(products, word[:i]):][:3] for i in range(1, len(word) + 1)]


# ==============================================================================
# TESTS — run:  python 007_search_suggestions_system_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True
    sol = Solution()

    print("--- correctness: bisect vs trie vs two pointers ---")
    cases = [
        (["mobile", "mouse", "moneypot", "monitor", "mousepad"], "mouse",
         [["mobile", "moneypot", "monitor"], ["mobile", "moneypot", "monitor"],
          ["mouse", "mousepad"], ["mouse", "mousepad"], ["mouse", "mousepad"]]),
        (["havana"], "havana", [["havana"]] * 6),
        (["havana"], "tatiana", [[]] * 7),
        (["bags", "baggage", "banner", "box", "cloths"], "bags",
         [["baggage", "bags", "banner"], ["baggage", "bags", "banner"], ["baggage", "bags"], ["bags"]]),
        (["apple", "apricot", "b"], "ap", [["apple", "apricot"], ["apple", "apricot"]]),
    ]
    for products, word, want in cases:
        a = sol.suggestedProducts(products, word)
        b = suggest_trie(build_trie(products), word)
        c = suggest_two_pointers(products, word)
        ok = a == b == c == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  word={word!r:<10} {a}")

    print("\n--- randomized cross-check vs filtering (400 inputs) ---")
    rng = random.Random(1268)
    bad = 0
    for _ in range(400):
        products = list({"".join(rng.choice("abc") for _ in range(rng.randint(1, 5))) for _ in range(rng.randint(1, 15))})
        word = "".join(rng.choice("abc") for _ in range(rng.randint(1, 6)))
        want = suggest_filter(products, word)
        got = (sol.suggestedProducts(products, word), suggest_trie(build_trie(products), word),
               suggest_two_pointers(products, word))
        if any(g != want for g in got):
            bad += 1
    ok = bad == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  400 random inputs: all three approaches match filtering")

    print("\n--- mistake 1 LIVE: no startswith filter after bisect ---")
    wrong = suggest_no_filter_bug(["apple", "apricot", "b"], "ap")
    right = sol.suggestedProducts(["apple", "apricot", "b"], "ap")
    ok = wrong != right and "b" in wrong[0]
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  products [apple, apricot, b], 'ap': unfiltered {wrong}, correct {right}")

    print("\n--- benchmark: 1000 products, 5000 different search words ---")
    products = list({"".join(rng.choice("abcdefgh") for _ in range(rng.randint(3, 20))) for _ in range(1000)})
    words = ["".join(rng.choice("abcdefgh") for _ in range(rng.randint(1, 12))) for _ in range(5000)]
    t0 = time.perf_counter()
    for w in words:
        sol.suggestedProducts(products, w)
    t_bisect = time.perf_counter() - t0
    t0 = time.perf_counter()
    root = build_trie(products)
    t_build = time.perf_counter() - t0
    t0 = time.perf_counter()
    for w in words:
        suggest_trie(root, w)
    t_trie = time.perf_counter() - t0
    print(f"      sort + bisect (re-sorts each call, as the LC signature forces): {t_bisect * 1000:8.1f} ms")
    print(f"      trie: build once {t_build * 1000:6.1f} ms, then 5000 queries {t_trie * 1000:8.1f} ms")
    print("      one query: either is fine. Many queries on the same products: build the index once.")

    print("\nALL PASSED" if all_ok else "\nFAILURES PRESENT")


if __name__ == "__main__":
    run_tests()
