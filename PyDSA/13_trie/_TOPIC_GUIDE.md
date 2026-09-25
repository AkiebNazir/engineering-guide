# Topic 13 · Trie (Prefix Tree) — Python Deep Dive

> A trie (prefix tree) is a tree of characters where the path from the root to
> any node spells a prefix, and a boolean flag marks which prefixes are also
> complete words. It trades the hash set's O(1)-average lookup for O(L)
> *guaranteed* lookup (L = word length, independent of dictionary size N) —
> and, unlike a hash set, it answers "does anything start with this prefix?"
> in the same O(L) instead of a full scan.

---

## Part 1 · Node Representation: dict-of-children vs fixed-26-array

This is Topic 01's array-vs-hashmap debate (`01_arrays_hashing` §2.1) replayed
one level deeper — instead of choosing a container for *counts*, you're
choosing a container for *child pointers*.

```arch
%% caption: Words: car, cat, cow, do. Green nodes end a word. Words sharing a prefix share a path, and search costs O(length of the word), independent of how many words are stored.
route straight
grid 80x80
node root "root" at 2.125,0 shape=circle color=blue
node c "c" at 1.25,1 shape=circle color=blue
node d "d" at 3,1 shape=circle color=blue
node ca "a" at 0.5,2 shape=circle color=blue
node co "o" at 2,2 shape=circle color=blue
node do "o" at 3,2 shape=circle color=green
node car "r" at 0,3 shape=circle color=green
node cat "t" at 1,3 shape=circle color=green
node cow "w" at 2,3 shape=circle color=green
root -> c
root -> d
c -> ca
c -> co
ca -> car
ca -> cat
co -> cow
d -> do
```


### 1.1 `dict`-of-children (the idiomatic Python default)

```python
class TrieNode:
    def __init__(self):
        self.children = {}      # char -> TrieNode
        self.is_word = False
```

- Handles **any alphabet** (uppercase, digits, unicode) with zero code change.
- No wasted space: a node with 2 children stores exactly 2 dict entries, not
  26 (or 128, or 1M) slots.
- Cost: each lookup hashes a 1-character string and walks a dict — slower
  per-op than raw index arithmetic, though Python's C-level dict is fast
  enough that this rarely matters versus the interpreter overhead of the
  method calls around it.

### 1.2 Fixed `[26]`-array-of-children (list, ASCII-lowercase only)

```python
class TrieNode:
    def __init__(self):
        self.children = [None] * 26     # index = ord(c) - ord('a')
        self.is_word = False
```

- O(1) truly constant-time indexing, no hashing.
- Every node pre-allocates 26 slots whether used or not — wasteful when the
  trie is sparse (e.g. one word per branch), fine when it's dense
  (overlapping prefixes, e.g. a real dictionary).
- **Only works when you know the alphabet is exactly `a`-`z`.** A digit, a
  space, or an uppercase letter throws `IndexError` or silently corrupts data
  if you don't guard `ord(c) - ord('a')` staying in `[0, 25]`.

**Measured on this machine** (see `001_implement_trie_prefix_tree_solution.py`
DEMO 2 — build + query 100,000 lowercase words, random lengths 3-10):

| | build | query (2k searches) | total |
|---|--:|--:|--:|
| dict-of-children | 182.8 ms | 1.5 ms | 184.4 ms |
| `[26]`-array | 277.9 ms | 3.9 ms | 281.8 ms |

The **dict won on both halves** on this run — not just "wins-or-ties
overall" but outright faster to build AND to query. `[None] * 26` allocates
26 list slots per node whether used or not, and this word list is sparse
enough (short words, low branching) that the array's per-node allocation
cost dominates and its O(1)-indexing advantage never gets to pay for
itself. **This is the opposite ordering from Go**, where the array is
unambiguously faster because Go avoids per-node object/pointer-boxing
overhead entirely (see `GoDSA/13_trie/_TOPIC_GUIDE.md` Part 1 — read that
file for the contrast). Don't assume the C-level intuition ports to
CPython — the guide's rule: **measure on the language you're actually
shipping**, and don't assume last run's numbers hold on a denser trie
either (a real dictionary with heavy prefix overlap would favor the array
more than this sparse random word list does).

**Rule of thumb for interviews:** default to the `dict` in Python — it's what
interviewers expect from Python candidates, it's alphabet-agnostic, and the
measured difference doesn't justify the array's rigidity. Mention the array
alternative only if asked to optimize for a known small alphabet.

---

## Part 2 · Insert / Search / StartsWith — the shared traversal

```arch
%% caption: The three operations share one walk down the trie and differ only in what they do at a missing child and at the end.
grid 150x90
node S "node = root" at 1,0 shape=pill
node L "for each char c in the word" at 1,1 w=200
node Q "c in node.children?" at 1,2 shape=diamond color=amber
node M "node = node.children[c]" at 0,2 w=130
node N "operation?" at 1,3 shape=diamond color=amber
node I "create the child, then move" at 0,3 w=130
node F "return False" at 1,4 color=red
node E "operation?" at 2.5,2 shape=diamond color=amber
node E1 "node.is_end = True" at 2,3 color=green w=130
node E2 "return node.is_end" at 3,3 color=green w=130
node E3 "return True" at 2.5,4 color=green
S -> L
L -> Q
Q:L -> M:R : "yes"
Q -> N : "no"
N:L -> I:R : "insert"
N -> F : "search or startsWith"
I:L -> L:L
M:T -> L:L
L:R -> E:T : "all chars consumed"
E:L -> E1:T : "insert"
E:R -> E2:T : "search"
E:B -> E3:T : "startsWith"
```


```python
class TrieNode:
    def __init__(self):
        self.children = {}
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
        """Shared traversal. Returns the node reached, or None if the path breaks."""
        node = self.root
        for ch in s:
            if ch not in node.children:
                return None
            node = node.children[ch]
        return node

    def search(self, word: str) -> bool:
        node = self._walk(word)
        return node is not None and node.is_word   # must be a WORD END

    def starts_with(self, prefix: str) -> bool:
        return self._walk(prefix) is not None       # any reachable node is enough
```

> ⚠️ **The classic trie bug:** `search` and `starts_with` share the exact
> same traversal and differ in exactly one check — `node.is_word`. Skip it in
> `search` and every inserted *prefix* silently looks like a complete word
> (insert `"apple"`, and a buggy `search("app")` returns `True`). Say the
> distinction out loud in an interview before you code it — it is the single
> most common trie mistake.

---

## Part 3 · When a Trie Beats a hashset/hashmap

A `set[str]` gives O(L) average membership (hashing the whole string) — same
asymptotic as a trie for exact-word lookup. The trie wins specifically when
the problem needs one of:

1. **Prefix queries** (`starts_with`) — a hash set cannot answer "does
   anything start with `pre`?" without scanning every element; a trie
   answers it in O(len(pre)), the same cost as an exact lookup.
2. **Autocomplete / "all words with this prefix"** — walk to the prefix node
   once, then <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> the subtree below it; a hash set has no notion of "subtree."
3. **Multi-pattern search over a fixed grid/text** (Word Search II, 006) —
   build ONE trie from the whole word list, then walk it in lockstep with a
   single grid <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>. Checking each of N words independently against the grid
   would repeat shared work (a shared prefix like `"cat"`/`"car"`/`"cap"`
   would be walked three separate times); the trie shares that walk.
4. **Wildcard search** (`.` matches any character, 002) — a hash set has no
   way to skip the unknown character; a trie <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> branches over all children
   at a `.` position, pruning the ones that don't lead anywhere.
5. **Shortest-prefix / longest-prefix matching** (Replace Words, 003) — walk
   character by character and stop at the first `is_word` — trivial on a
   trie, awkward with a hash set (would need to try every prefix length as a
   separate lookup: O(L) hash lookups instead of one O(L) walk).

A hash set/map remains strictly better when the problem is pure exact-match
membership with no prefix/wildcard/subtree structure — don't reach for a trie
by default; reach for it when one of the five patterns above is present.

---

## Part 4 · Wildcard Search — <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> Over the Trie

```python
def wildcard_search(root: TrieNode, word: str) -> bool:
    def dfs(node, i):
        if node is None:
            return False
        if i == len(word):
            return node.is_word
        ch = word[i]
        if ch == '.':
            return any(dfs(child, i + 1) for child in node.children.values())
        return dfs(node.children.get(ch), i + 1)
    return dfs(root, 0)
```

Every `.` fans the search out over every live child instead of following one
edge — worst case O(26^(number of dots) · remaining length), but in practice
bounded tightly by how sparse the trie actually is (most branches die
immediately because `node.children.get(ch)` returns `None`).

---

## Part 5 · End-of-Word Marking — Why a Boolean, Not "Is Leaf"

A word being a prefix of a longer word is completely normal (`"app"` and
`"apple"` both inserted) — the node for `"app"` has children (`p` -> `l` ->
...) AND is a valid word end. **"Is this a leaf" and "is this a word" are
unrelated questions.** Conflating them (e.g. treating "no children" as "is a
word") is a second classic trie bug distinct from the `search`/`starts_with`
mixup in Part 2.

---

## Part 6 · Augmenting Nodes (Map Sum Pairs, 004)

A trie node can carry more than a boolean — 004 augments each node with a
running `value` sum so that `sum(prefix)` is answered by one O(L) walk to the
prefix node, reading a pre-aggregated field, instead of an O(N·L) rescan of
every inserted key on every query. This is the same "pay at insert time to
save at query time" trade you've seen with prefix sums (Topic 04) — here the
prefix structure IS the trie's shape instead of an array index.

---

## Part 7 · Bit Trie (Bridge to Topic 20)

The same node-per-branch idea works over the **binary representation** of
integers: a trie of fixed depth (32 for a 32-bit int) where each node has
exactly 2 children (bit 0 / bit 1). Insert every number's bit pattern
top-down from the most significant bit; to maximize `x XOR y` over the
stored set (005 Maximum <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> of Two Numbers), greedily walk the *opposite*
bit of `x` at each level when it exists — that greedy choice is what a
straightforward "check all pairs" O(n^2) approach cannot do, and it drops
the cost to O(32·n) — a fixed-depth trie walk per number instead of a
quadratic pairwise scan.

---

## Part 8 · Complexity Summary

| Operation | Time | Space | Mutates input? | Note |
|---|:--:|:--:|:--:|---|
| `insert(word)` | O(L) | O(L) worst case | No (mutates the trie, not the caller's string) | O(1) extra if the path already exists |
| `search(word)` | O(L) | O(1) | No | Independent of dictionary size N |
| `starts_with(prefix)` | O(L) | O(1) | No | Same traversal as search, minus `is_word` |
| Wildcard search (`.`) | O(26^dots · L) worst, much less in practice | O(L) recursion | No | Fans out only at `.` positions |
| Build trie of N words, avg length L | O(N·L) | O(ALPHABET · N · L) worst | No | Shared prefixes reduce real usage well below the worst case |

---

## Part 9 · Edge Cases

- **Empty string** — inserting `""` marks the *root* as a word; searching
  `""` should return `True` after that insert. Easy to miss because the loop
  body never runs.
- **Single character** — smallest non-trivial path; a good sanity check that
  `is_word` is set on the *first* node reached, not skipped.
- **A word that is a prefix of another** (`"app"` then `"apple"`) — both must
  independently report `search(...) == True`; verifies Part 5's "leaf ≠
  word" distinction.
- **Duplicate insert** — inserting the same word twice must not create
  duplicate nodes or break `is_word` (idempotent by construction if you
  always do `node.children.setdefault` / `if ch not in children`).
- **Prefix that is never a word** (`starts_with` true, `search` false) — the
  distinguishing case for Part 2's bug.

---

## Part 10 · Common Mistakes

1. Skipping the `is_word` check in `search`, making every prefix look like a
   full word (Part 2).
2. Treating "no children" as "is a word" instead of tracking `is_word`
   explicitly (Part 5).
3. Using `[None] * 26` with unvalidated input containing non-lowercase
   characters — silent `IndexError` or wrong-slot corruption (Part 1.2).
4. Rebuilding the trie from scratch per query instead of building it once
   and reusing it across all queries (Word Search II) — turns an O(N·L) build
   + O(rows·cols·4^L) search into a repeated, much slower O(queries · N · L).
5. In wildcard search, forgetting the `i == len(word)` base case check
   `node.is_word` — returning `True` just for reaching a live node at the end
   of the pattern, which wrongly matches a prefix as a full word (same root
   bug as #1, in <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> form).
6. Off-by-one in the bit trie: iterating bits from the wrong end (must walk
   most-significant-bit first for the greedy-<abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> trick in Part 7 to be
   correct).

---

## Part 11 · Follow-Ups Interviewers May Ask

- "Delete a word from the trie" — requires tracking whether a node is now
  both `is_word == False` and childless, and pruning bottom-up (careful:
  don't prune a node that's still a prefix of another surviving word).
- "How would you support autocomplete (top-k suggestions by frequency)?" —
  augment nodes with a counter (Part 6 pattern) and <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> the subtree collecting
  the top-k, or cache the top-k per node at insert time for O(1) query.
- "What if the alphabet is Unicode, not just lowercase ASCII?" — `dict`
  handles it for free (Part 1.1); the fixed array does not.
- "Compress the trie" — a radix tree / Patricia trie collapses single-child
  chains into one edge labeled with a substring, trading traversal simplicity
  for reduced node count on sparse tries.

---

## Part 12 · Related Problems / Pattern Family

- **Topic 01 (Arrays & Hashing)** — the array-vs-map node-representation
  debate is the same trade-off as `01_arrays_hashing`'s array-vs-map guide,
  one level deeper (child pointers instead of counts).
- **Topic 04 (Prefix Sum)** — augmenting trie nodes with a running aggregate
  (Part 6) is the same "precompute once, answer many queries cheaply" idea as
  prefix sums, applied to a tree of prefixes instead of an array of indices.
- **Topic 09 (Recursion & Backtracking)** — Word Search II (006) reuses the
  choose → recurse → un-choose template directly, walking the trie and the
  grid in lockstep.
- **Topic 20 (Bit Manipulation)** — the binary/<abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> trie (Part 7) is the
  bridge problem; expect it to reappear there framed as a greedy bit trick.

---

<!-- block:13_py_1_beyond -->
## Part 13 · A Trie in Practice: Memory, Deletion, Pruning, Autocomplete and Cousins

The guide so far builds the structure and its standard uses. This Part covers what an interviewer asks *after* you have
written `insert`/`search`: what it costs, how you delete, how you make Word Search II fast, and what else exists. Every
number below was measured on this machine (CPython 3.13); every snippet was run.

### 13.1 What a trie actually costs in memory

A trie trades memory for prefix queries, and in CPython it trades a *lot* of it. 20,000 random lowercase words of 4–10
letters (140,043 characters) make a trie of **92,228 nodes** — about 0.66 nodes per character, because random words
share only short prefixes. Measured with `tracemalloc`:

| Representation | Memory |
|---|---:|
| a plain `set` of the 20,000 words | 2.1 MB |
| nested dicts (`node.setdefault(ch, {})`, `"$"` marks a word end) | 17.2 MB |
| class node + `__slots__` + `children` dict | 19.2 MB |
| class node + `children` dict (no `__slots__`) | 22.9 MB |
| class node + `__slots__` + `[None] * 26` | **28.8 MB** |

Three lessons. A trie is **about 8× a hash set** of the same words on random data — worth it only when you need *prefix*
operations (Part 3). The fixed 26-slot array is the **most** memory-hungry here, not the least: every node pays for 26
pointers although a typical node has one child, so the array wins on *speed* and loses on *space* for sparse data. And
`__slots__` is a cheap ~16% saving on the class-based version. (Real word lists share far more prefixes than random
strings, which is why dictionary tries compress better than these numbers suggest — measure your own data.)

The nested-dict form is also the shortest to write:

```python
END = "$"
def add(root, w):
    node = root
    for ch in w: node = node.setdefault(ch, {})
    node[END] = True                               # the end marker lives in the same dict as the children
def contains(root, w):
    node = root
    for ch in w:
        if ch not in node: return False
        node = node[ch]
    return END in node
```

Use a marker key that cannot be a character (`"$"` is safe for lowercase letters; pick something else if `$` can occur).

### 13.2 Deleting a word — and only pruning what is now useless

Delete has two halves: **unmark** the word, then **prune bottom-up** any node that is now both childless and not itself a
word. The rule that trips people up: never prune a node that is still a prefix of *another* surviving word.

```python
def delete(root, word):
    def rec(node, i):                                   # returns True if `node` is now empty and can be cut off
        if i == len(word):
            if END not in node: return False           # the word was never stored
            del node[END]
            return not node                             # prune only if nothing hangs below
        child = node.get(word[i])
        if child is None or not rec(child, i + 1): return False
        del node[word[i]]                               # the child became empty: detach it
        return not node and END not in node             # and tell the parent whether WE are now empty
    rec(root, 0)
```

With `app`, `apple`, `apply`, `apt`: deleting `apple` keeps `app` and `apply` intact; deleting `apply` next leaves
`app` a word but removes the `l`, `y` branch entirely; deleting a word that was never stored changes nothing.

### 13.3 Word Search II: prune exhausted branches

The trie already prunes the *search* (only walk a neighbour if the trie has that letter). The second optimisation
prunes the *trie*: store the **whole word at its end node** (so you need no path string), take it once
(`node.pop(END)` — which also dedupes results), and when a node has no words and no children left after its <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>,
**delete it from its parent** so no later search wastes a step entering it:

```python
w = node.pop(END, None)                     # take the word ONCE
if w: res.append(w)
...
if prune and not node:                      # nothing left below: remove this branch from the parent
    del parent[ch]
```

On a random 6×6 grid over `{a, b}` with 200 words of length 3–8, both versions return the *same 98 words*, but the <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>
visits drop from **11,538 to 1,159** with pruning (about 10×). The gain grows with the number of words that get found
(their branches disappear as they are collected) and shrinks on inputs where few words match.

### 13.4 Autocomplete: precompute the top-k at every node

Walking to the prefix node is O(L); *collecting* the best completions from its subtree is not. The design-problem answer
is to store the **top-k at each node at insert time** — a handful of `(−count, word)` pairs — so a query is O(L) with no
subtree walk:

```python
def record(self, word):                                     # one more occurrence of `word`
    self.count[word] = self.count.get(word, 0) + 1
    key = (-self.count[word], word)                          # more frequent first, then alphabetical
    node = self.root
    for ch in word:
        node = node.children.setdefault(ch, Node())
        node.best = [b for b in node.best if b[1] != word]   # replace this word's old entry
        node.best.append(key); node.best.sort(); del node.best[3:]     # keep 3: O(1) per node
def suggest(self, prefix):
    node = self.root
    for ch in prefix:
        node = node.children.get(ch)
        if node is None: return []
    return [w for _, w in node.best]
```

Feeding it `"i love you"` ×5, `"island"` ×3, `"i love leetcode"` ×2 and `"iroman"` ×1 gives
`suggest("i") == ["i love you", "island", "i love leetcode"]` and `suggest("i l") == ["i love you", "i love leetcode"]`.
The cost moves from query time to **update time and memory** (`k` entries per node) — the standard read-heavy trade-off.

### 13.5 The family around the trie

| Structure | What it changes | Use it for |
|---|---|---|
| **Radix / Patricia tree** | Collapse every single-child chain into one edge labelled with a substring | Far fewer nodes on sparse data; <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> routing tables, some in-memory databases. |
| **Ternary search tree** | Three pointers per node (`<`, `=`, `>`) instead of an alphabet table | Compact, ordered, works for any alphabet; slower than a hash trie. |
| **DAWG / DAFSA** | Merge *identical suffixes* as well as shared prefixes | The smallest exact word-set automaton (spell-check dictionaries, Scrabble solvers). |
| **Aho–Corasick** | A trie plus *failure links* (like <abbr title="Knuth-Morris-Pratt. A string-searching algorithm that searches for occurrences of a word within a main text string in optimal time.">KMP</abbr>'s table, topic 23) | Find *all* occurrences of *many* patterns in one pass over a text: O(text + matches). |
| **Suffix trie / tree / array** | Index every *suffix* of a text | Substring search, longest repeated substring, bioinformatics. |
| **Bit trie** | 2 children per node, keys are integers | Max <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> (Part 7), <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> longest-prefix match. |

### 13.6 When *not* to use a trie

| Situation | Better tool |
|---|---|
| Exact membership only | A `set` — ~8× less memory (13.1), same O(L) average. |
| Prefix queries over a *static* sorted list | Sort once and `bisect` — words sharing a prefix are one contiguous block (Problem 007's first design). |
| Very large dictionary, memory-bound | A radix tree or DAFSA; or an on-disk index. |
| Numeric keys, range queries | A B-tree / sorted structure (topic 11), not a character trie. |

### 13.7 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Delete a word." | Unmark, then prune bottom-up only nodes that are childless *and* not words (13.2). |
| "Top-k suggestions." | Precompute the top-k per node (13.4), or <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> the subtree with a heap. |
| "Case-insensitive / Unicode." | `dict` children handle it; normalise (`casefold`, NFC) before inserting. |
| "The trie no longer fits in memory." | Radix/DAFSA, sharded tries by first letter, or an on-disk structure. |
| "Count words with a given prefix." | A `pass_count` on each node (Map Sum Pairs' augmentation, Problem 004). |
| "Thread safety." | Reads are safe on an immutable trie; use a lock or copy-on-write for updates. |

---
<!-- /block:13_py_1_beyond -->

<!-- problem-map:start -->
## Part 14 · Every Problem in This Topic, by Pattern

Seven problems, four moves (the basic trie · wildcards · augmenting nodes · a trie as a search index). Each **Trap** is a mistake documented in that problem's solution file.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Implement Trie (Prefix Tree)](PyDSA/13_trie/001_implement_trie_prefix_tree_solution.py) <br>LC 208 · Medium | The basic trie | A path from the root spells a string, one character per edge; an `is_word` flag marks where a whole word ends — the only thing separating a stored word from a mere prefix. **Trap:** skipping the `is_word` check in `search` (insert `"apple"`, and `search("app")` wrongly returns `True`). |
| [002 · Design Add and Search Words Data Structure](PyDSA/13_trie/002_design_add_and_search_words_data_structure_solution.py) <br>LC 211 · Medium | Wildcard search by <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> | `addWord` is 001's `insert`; `search` becomes a <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> where `.` tries every live child. **Trap:** no `node is None` guard at the top of the recursion; checking `is_word` before confirming `i == len(word)`. |
| [003 · Replace Words](PyDSA/13_trie/003_replace_words_solution.py) <br>LC 648 · Medium | First hit is the shortest | Build one trie from the roots; for each sentence word walk it and **stop at the first `is_word`** — that is the shortest root. **Trap:** continuing to the longest match; rebuilding the trie (or rescanning the dictionary) per word. |
| [004 · Map Sum Pairs](PyDSA/13_trie/004_map_sum_pairs_solution.py) <br>LC 677 · Medium | Augmented nodes | Store a pre-aggregated `value` on every node so `sum(prefix)` is one O(L) walk plus an O(1) read. **Trap:** adding `val` instead of the **delta** `val - old_val` on a re-insert (double-counts); not remembering old values in a side dict. |
| [005 · Maximum XOR of Two Numbers in an Array](PyDSA/13_trie/005_maximum_xor_of_two_numbers_in_an_array_solution.py) <br>LC 421 · Medium | A bit trie | A fixed-depth trie over the bits of each number, most significant first; for each `x` greedily walk the *opposite* bit to maximise the <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>. **Trap:** not padding to a fixed bit width (misaligned bits); walking least-significant first (the greedy argument only holds MSB-first). |
| [006 · Word Search II](PyDSA/13_trie/006_word_search_ii_solution.py) <br>LC 212 · Hard | Trie + grid backtracking | One trie from all words, then one <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> over the grid walking trie and grid in lockstep; stop descending the moment the trie has no such child. **Trap:** forgetting to restore `board[r][c]` after the call; a separate `visited` set instead of the in-place sentinel. |
| [007 · Search Suggestions System](PyDSA/13_trie/007_search_suggestions_system_solution.py) <br>LC 1268 · Medium | Two designs for autocomplete | A sorted list plus `bisect_left` (prefix words are one contiguous block), or a trie with a <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>. **Trap:** taking `products[i:i+3]` without the `startswith` filter (`"b"` sneaks into `"ap"`); not sorting first. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain dict-of-children vs fixed-array-of-children, and why Python
      measures differently from Go on this trade-off
- [ ] State the `search` vs `starts_with` distinction (`is_word` check)
      without hesitating
- [ ] Explain why "is a leaf" and "is a word" are unrelated
- [ ] Name at least 3 problem shapes where a trie beats a hash set
      (prefix query, wildcard, multi-pattern grid search)
- [ ] Trace a wildcard <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> search including the fan-out at `.`
- [ ] Explain the bit-trie / max-<abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> greedy walk
- [ ] Write insert/search/starts_with with lazy node creation in under
      10 minutes
- [ ] Quote the memory cost of a trie against a hash set (about 8× on random words) and say when it is still worth it <!--ca-->
- [ ] Delete a word and prune only nodes that are childless *and* not words <!--ca-->
- [ ] Prune exhausted branches in Word Search II, and say why storing the word at its end node helps <!--ca-->
- [ ] Precompute top-k suggestions per node, and name the update-time cost <!--ca-->
- [ ] Name a radix tree, DAFSA and Aho–Corasick, and what each adds <!--ca-->

---

## Added Problem (007) · Search Suggestions System — Tiny Autocomplete, Two Designs

Added 16 Sep 2026 from the Google prep plan.

- **Sort + binary search.** Words sharing a prefix are contiguous in sorted order;
  `bisect_left(products, prefix)` is where that block would start. Take up to three, but filter with
  `startswith` — the landing word may not match (`"b"` for prefix `"ap"`).
- **Trie with top-3 at each node.** Insert words in sorted order and keep the first three that pass
  through each node. Each keystroke is one step down.

Measured in the file: re-sorting per query (as the LeetCode signature forces) took ~230 ms for 5,000
queries over 1,000 products; building the trie once took ~3 ms and all 5,000 trie queries ~2 ms. That
gap is the whole argument for precomputed top-k per prefix in the autocomplete system design problem.

- [ ] I can explain why prefix matches are contiguous in sorted order, and when to build a trie instead.
