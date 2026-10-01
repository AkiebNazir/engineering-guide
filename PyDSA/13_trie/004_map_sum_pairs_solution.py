"""
================================================================================
SOLUTION · LeetCode 677 · Map Sum Pairs                                  [Medium]
https://leetcode.com/problems/map-sum-pairs/
================================================================================

THE CORE IDEA
--------------
Augment every trie node with a `value` field that holds the PRE-AGGREGATED
sum of all inserted keys passing through it. `sum(prefix)` then costs one
O(L) walk to the prefix's node followed by an O(1) read of that field —
none of the words BELOW the prefix need to be revisited, because their
contribution was already folded in at insert time. This is topic guide
Part 6's "pay at insert time to save at query time" trade, the trie
analogue of Topic 04's prefix-sum arrays.

The one wrinkle the problem statement calls out explicitly: re-inserting an
existing key OVERWRITES its value, it does not add to it. So a naive
"add val to every node along the path on every insert" is wrong on a
re-insert — you must first know the OLD contribution of this exact key
(delta = new_val - old_val) and add only the delta, otherwise the second
insert of the same key double-counts the old value forever.


================================================================================
MULTIPLE APPROACHES
================================================================================
Approach 0 (brute force, price it, don't ship it): keep a `dict[str, int]`
of key -> val (this ALSO correctly handles overwrite-not-add for free,
since a dict assignment naturally replaces). `sum(prefix)` scans every
stored key and sums the values of the ones that start with `prefix`:
O(N*L) per query, N = number of distinct keys. With up to 50 calls this is
small here, but the demo below scales it up to show the growth.

Approach 1 (trie storing ONLY is_word, no augmentation): walk to the
prefix's node (O(L)), then DFS the ENTIRE subtree below it summing every
is_word leaf's associated value (kept in a side dict). Better than
approach 0 when the prefix is long/specific (small subtree) but degrades
to O(subtree size) which can still be O(N) for a short/common prefix like
`""`.

Approach 2 (trie, node.value pre-aggregated, delta-corrected insert) ✅ —
the answer. Keep a separate `key -> val` dict ONLY to detect re-inserts and
compute the delta; walk the trie once per insert adding `delta` to every
node.value along the path (O(L)), and once per sum query reading one
node's value (O(L) walk + O(1) read).


================================================================================
STEP BY STEP TRACE
================================================================================
insert("apple", 3)
    previous value of "apple": none -> delta = 3 - 0 = 3
    walk root -a-> a -p-> p1 -p-> p2 -l-> l -e-> e, adding +3 to EVERY
    node's .value along the way (including the root, conventionally skipped
    or included depending on implementation -- here we add to every node
    the walk passes AFTER the root, i.e. a,p1,p2,l,e each get +3)
    key_values["apple"] = 3

sum("ap")
    walk root -a-> a -p-> p1.  p1.value == 3 (only "apple" has passed
    through here so far) -> return 3

insert("app", 2)
    previous value of "app": none -> delta = 2 - 0 = 2
    walk root -a-> a -p-> p1 -p-> p2, adding +2 to a, p1, p2
    key_values["app"] = 2

    node values now:      a=5   p1=5   p2=2   l=3   e=3
                           (a and p1 are on BOTH "apple" and "app"'s paths,
                            so they carry the sum of both: 3+2=5)

sum("ap")
    walk root -a-> a -p-> p1.  p1.value == 5  -> return 5  (3 + 2)

Re-insert trace: insert("apple", 5)  (OVERWRITES, does not add)
    previous value of "apple": 3 -> delta = 5 - 3 = 2
    walk the SAME path a,p1,p2,l,e, adding +2 (the DELTA, not +5) to each
    key_values["apple"] = 5

    node values now:      a=7   p1=7   p2=4   l=5   e=5
    sum("ap") -> walk to p1 -> 7   (== 5 [new apple] + 2 [app], correct;
                                     NOT 3+2+5=10, which is what a naive
                                     "always add val" insert would give)


================================================================================
COMPLEXITY SUMMARY
================================================================================
    Approach                              insert  sum(prefix)         Mutates input?
    -------------------------------------  ------  ------------------  --------------
    dict[str,int], scan on sum             O(1)    O(N*L)              no
    Trie, is_word only, DFS subtree on sum O(L)    O(L + subtree size) no
    Trie, augmented node.value ✅          O(L)    O(L)                no

    N = distinct keys stored, L = key/prefix length. The augmented version
    makes sum() independent of both N and the subtree size — the entire
    saving Part 6 of the topic guide describes.
    Space: O(sum of key lengths) for the trie plus O(N) for the side dict
    tracking old values (needed only to compute re-insert deltas).


================================================================================
EDGE CASES
================================================================================
    sum(prefix) with NOTHING inserted   -> walk breaks on the first
                                            character (or prefix is
                                            non-empty but root has no such
                                            child) -> return 0, not a crash.
    sum("") empty prefix                -> every inserted key "starts with"
                                            "" -> should return the sum of
                                            ALL values; the root node's own
                                            .value must be updated too, or
                                            you special-case prefix=="" to
                                            walk zero steps and read root.
    re-insert same key with SAME value   -> delta == 0, a no-op walk that
                                            still must complete safely (not
                                            skipped), tested below.
    re-insert same key with SMALLER      -> delta is NEGATIVE; every node
    value                                    on the path must correctly
                                            subtract, tested below (this is
                                            the case a "just add" bug hides
                                            until you specifically test it).
    prefix longer than any inserted key -> walk runs off the trie ->
                                            return 0.
    two keys, one a prefix of the other -> ("ap", 1) then ("apple", 2):
                                            sum("ap") must count BOTH (3),
                                            proving the value lives on every
                                            node on the path, not just leaves.


================================================================================
COMMON MISTAKES
================================================================================
1. Always adding `val` on insert instead of the DELTA `val - old_val` —
   correct on first insert, silently wrong (double-counts) the moment a
   key is re-inserted. This is the problem's headline trap; the EXAMPLE in
   the question file's docstring exists specifically to catch it.

2. Forgetting to track old values at all (no side `dict[str,int]`), making
   it IMPOSSIBLE to compute the delta on re-insert — you cannot special-case
   what you don't remember.

3. Only updating `is_word`/leaf-level data and then DFS-ing the subtree on
   every `sum()` call — correct, but throws away the entire point of
   augmenting the nodes (approach 1 vs approach 2 above); still passes
   correctness tests, fails the "why is this a trie problem" framing.

4. Not updating the ROOT's own value/never handling `sum("")` — walking
   zero characters means the loop body never runs, so if you don't seed
   the root itself the empty-prefix case returns 0 instead of the grand
   total.

5. Applying the delta only to the LAST node (the word-end) instead of
   every node ALONG the path — breaks every non-trivial prefix query
   (`sum("ap")` when only `p2`/leaf carries the value would miss `"apple"`
   contributing to a shorter prefix like `"a"`).


================================================================================
FOLLOW-UPS THE INTERVIEWER MAY ASK
================================================================================
Q: Support DELETE(key)?
A: Look up the key's current value in the side dict (0 if absent), apply
   delta = -old_val along the path (mirrors insert's delta logic), then
   remove the key from the side dict. Node pruning (topic guide's earlier
   delete follow-up) is optional here since a value of 0 is harmless to
   leave behind, but pruning avoids unbounded memory growth.

Q: What if `val` could be negative?
A: Nothing in this design assumes `val >= 0` — the delta arithmetic is
   sign-agnostic; it already has to handle negative deltas (this file's
   re-insert-with-smaller-value edge case) so negative val works
   identically.

Q: Can this support "top-k keys by value with a given prefix" instead of
   just the sum?
A: Different augmentation: instead of (or in addition to) a running sum,
   maintain a small max-heap or sorted structure per node of the top-k
   (key, val) pairs seen through it, updated on every insert -- classic
   autocomplete-with-ranking extension mentioned in the topic guide's
   general "delete/autocomplete" follow-ups.

Q: Compare this to just using a `Counter`/`defaultdict` keyed by prefix
   directly (precompute every prefix's sum eagerly)?
A: That's O(sum of L^2) space/time up front (every key contributes L
   distinct prefixes) versus the trie's O(sum of L) — the trie shares
   prefix STORAGE across keys for free; a flat prefix->sum dict does not.


================================================================================
RELATED PROBLEMS — THE PATTERN FAMILY
================================================================================
    LC 208  Implement Trie (this topic, 001)   — the base is_word-only trie
            this problem augments with a numeric field
    LC 648  Replace Words (this topic, 003)    — also walks to a prefix,
            but stops at the FIRST is_word rather than aggregating
    LC 304  Range Sum Query 2D (topic 04)      — same "precompute once,
            answer many queries in O(1) extra" idea over a grid instead
    LC 1268 Search Suggestions System          — trie augmented for
            top-k-by-prefix instead of sum-by-prefix
================================================================================
"""

import random
import string
import time


class TrieNode:
    def __init__(self):
        self.children = {}
        self.value = 0     # sum of all values whose key passes through here


class MapSum:
    def __init__(self):
        self.root = TrieNode()
        self.key_values = {}   # key -> current val, needed to compute deltas

    def insert(self, key: str, val: int) -> None:
        delta = val - self.key_values.get(key, 0)
        self.key_values[key] = val
        node = self.root
        node.value += delta        # root itself accumulates the grand total,
                                    # so sum("") reads it in O(1) with no
                                    # special-casing of the empty prefix
        for ch in key:
            if ch not in node.children:
                node.children[ch] = TrieNode()
            node = node.children[ch]
            node.value += delta

    def sum(self, prefix: str) -> int:
        node = self.root
        for ch in prefix:
            if ch not in node.children:
                return 0
            node = node.children[ch]
        return node.value


# ==============================================================================
# Brute-force baseline used only by the runtime demo / cross-check below.
# ==============================================================================
class BruteForceMapSum:
    def __init__(self):
        self.pairs = {}

    def insert(self, key: str, val: int) -> None:
        self.pairs[key] = val   # overwrite, not add -- dict assignment does this for free

    def sum(self, prefix: str) -> int:
        return sum(v for k, v in self.pairs.items() if k.startswith(prefix))


# ==============================================================================
# TESTS — run:  python 004_map_sum_pairs_solution.py
# ==============================================================================
def run_tests() -> None:
    all_ok = True

    print("--- correctness ---")
    m = MapSum()
    m.insert("apple", 3)
    ok = m.sum("ap") == 3
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  insert(apple,3); sum(ap) -> {m.sum('ap')}  (want 3)")
    m.insert("app", 2)
    ok = m.sum("ap") == 5
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  insert(app,2); sum(ap) -> {m.sum('ap')}  (want 5)")

    print("\n--- overwrite-not-add: re-insert the SAME key ---")
    m.insert("apple", 5)   # was 3, now 5: delta should be +2, not +5
    got = m.sum("ap")
    ok = got == 7          # 5 (new apple) + 2 (app)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  insert(apple,5) [was 3]; sum(ap) -> {got}  (want 7, "
          f"NOT 10)")

    print("\n--- re-insert with a SMALLER value (negative delta) ---")
    m.insert("apple", 1)   # was 5, now 1: delta = -4
    got = m.sum("ap")
    ok = got == 3           # 1 (new apple) + 2 (app)
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  insert(apple,1) [was 5]; sum(ap) -> {got}  (want 3)")

    print("\n--- edge cases ---")
    m2 = MapSum()
    edge = [
        (m2.sum("x"), 0, "sum on empty MapSum"),
        (m2.sum(""), 0, "sum('') on empty MapSum"),
    ]
    m2.insert("a", 1)
    m2.insert("b", 2)
    edge.append((m2.sum(""), 3, "sum('') == grand total after two inserts"))
    m2.insert("a", 1)   # same key, same value: delta == 0, must be a safe no-op
    edge.append((m2.sum(""), 3, "re-insert same key/value: total unchanged"))
    m2.insert("ap", 10)
    m2.insert("apple", 20)
    edge.append((m2.sum("ap"), 30, "prefix that is itself a stored key sums BOTH"))
    for got, want, label in edge:
        ok = got == want
        all_ok &= ok
        print(f"{'PASS' if ok else 'FAIL'}  {label:<52} -> {got}  (want {want})")

    # --------------------------------------------------------------------
    # Trace, printed explicitly.
    # --------------------------------------------------------------------
    print("\n--- trace: insert(apple,3), insert(app,2), sum('ap') ---")
    trace_ms = MapSum()
    for key, val in (("apple", 3), ("app", 2)):
        delta = val - trace_ms.key_values.get(key, 0)
        trace_ms.key_values[key] = val
        node, path = trace_ms.root, ""
        node.value += delta
        print(f"  insert({key!r}, {val}), delta={delta}")
        for ch in key:
            node = node.children.setdefault(ch, TrieNode())
            node.value += delta
            path += ch
            print(f"    node[{path!r}].value = {node.value}")
    print(f"  sum('ap') = {trace_ms.sum('ap')}")

    # --------------------------------------------------------------------
    # Randomised cross-check vs the brute-force dict scanner.
    # --------------------------------------------------------------------
    print("\n--- randomised cross-check: trie vs brute-force ---")
    random.seed(677)
    alphabet = string.ascii_lowercase
    real, brute = MapSum(), BruteForceMapSum()
    keys = list({"".join(random.choices(alphabet, k=random.randint(1, 5)))
                 for _ in range(150)})
    mismatches = 0
    for _ in range(1000):
        if random.random() < 0.6:
            k = random.choice(keys)
            v = random.randint(-50, 50)
            real.insert(k, v)
            brute.insert(k, v)
        else:
            prefix = random.choice(keys)[:random.randint(0, 3)]
            if real.sum(prefix) != brute.sum(prefix):
                mismatches += 1
    ok = mismatches == 0
    all_ok &= ok
    print(f"{'PASS' if ok else 'FAIL'}  1000 mixed insert/sum ops, {mismatches} mismatches")

    # --------------------------------------------------------------------
    # DEMO: augmented-trie sum() vs brute-force dict scan, at scale.
    # --------------------------------------------------------------------
    print("\n--- DEMO: sum(prefix) — augmented trie O(L) vs brute-force scan O(N*L) ---")
    random.seed(4)
    fast, slow = MapSum(), BruteForceMapSum()
    n_keys = 30_000
    big_keys = list({"".join(random.choices(alphabet, k=random.randint(3, 10)))
                      for _ in range(n_keys)})
    for k in big_keys:
        v = random.randint(1, 1000)
        fast.insert(k, v)
        slow.insert(k, v)

    queries = [k[:2] for k in random.sample(big_keys, 300)]

    t0 = time.perf_counter()
    fast_results = [fast.sum(q) for q in queries]
    t1 = time.perf_counter()
    slow_results = [slow.sum(q) for q in queries]
    t2 = time.perf_counter()

    same = fast_results == slow_results
    all_ok &= same
    fast_t, slow_t = t1 - t0, t2 - t1
    print(f"  {len(big_keys)} keys, {len(queries)} sum(prefix) queries")
    print(f"  augmented trie:  {fast_t * 1000:8.2f} ms")
    print(f"  brute-force scan:{slow_t * 1000:8.2f} ms")
    print(f"  trie is {slow_t / fast_t:6.0f}x faster; results identical: {same}")

    print(f"\n{'ALL PASSED' if all_ok else 'FAILURES PRESENT'}")


if __name__ == "__main__":
    run_tests()
