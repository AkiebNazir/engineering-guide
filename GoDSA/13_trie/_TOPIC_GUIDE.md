# Topic 13 · Trie — Go Deep Dive

> A trie trades the hash map's O(1)-average, O(n)-worst lookup for O(L)
> *guaranteed* lookup, where L is the length of the word — not the size of the
> dictionary. In Go the interesting question isn't the algorithm (it's the same
> tree-of-characters everywhere); it's how you represent a node, because that
> single struct-field choice changes every allocation, every cache line, and
> every big-O constant in the whole structure.

---

## Part 1 · The Central Decision: Array vs. Map Children

A trie node needs a way to answer "do I have a child for character `c`?" There
are exactly two idiomatic choices in Go, and picking wrong costs you real
performance, not just style points.

### 1.1 `children [26]*TrieNode` — the array

```go
type TrieNode struct {
    children [26]*TrieNode   // index c - 'a'
    isEnd    bool
}
```

- **O(1) truly constant-time** lookup: `node.children[c-'a']` is a single
  pointer-array index, no hashing, no bucket walk.
- **One allocation per node, no hashing**: a `[26]*TrieNode` is 26 × 8 bytes = 208 bytes (224 with the allocator's
  size class), zero-value `nil` for every absent child, with no map header or group bookkeeping. **But it is not
  always the smaller representation** — every node pays for all 26 slots however few children it has. Measured on Go
  1.24.5 with 20,000 random words of 4–10 letters (a 92,146-node trie): the array trie used **20.7 MB**, the
  `map[byte]*node` trie **15.7 MB**, because most random-word nodes have exactly one child. The array's win is
  **speed**: 1,000,000 lookups took **11 ms** against **106 ms** for the map trie (about 10× faster). Measure both on your
  own data when memory matters — a denser trie (more shared prefixes, more children per node) moves the balance
  toward the array.
- **Restricted alphabet**: only works cleanly when you know the character set
  in advance — lowercase English (`a`-`z`) is by far the most common LeetCode
  case, hence 26.

✅ **Default to the array for ASCII-lowercase interview problems.** It's what
interviewers expect and it's about 10× faster on lookups; say out loud that it can cost more memory than the
map on sparse data.

### 1.2 `children map[byte]*TrieNode` (or `map[rune]*TrieNode`) — the map

```go
type TrieNode struct {
    children map[byte]*TrieNode
    isEnd    bool
}
```

- Handles **arbitrary or unknown alphabets** — mixed case, digits, unicode,
  or a sparse set of characters where allocating 26+ slots per node would
  waste memory (e.g. a trie of file paths using every byte value).
- Costs more per node: a map lookup hashes the key and walks a bucket
  (Topic 1 Part 2.1) instead of doing raw pointer arithmetic — slower and less
  cache-friendly than the array.
- For `rune` keys (multi-byte <abbr title="Unicode Transformation Format. A family of character encodings capable of encoding all possible Unicode code points.">UTF</abbr>-8 characters), the map is close to
  mandatory — you cannot size a fixed array to "all Unicode code points."

> ⚠️ **Don't default to the map out of habit.** Go engineers coming from
> Python reach for `map[byte]*TrieNode` because Python tries are almost always
> built on `dict`. In Go, if the alphabet is small and known, the array is
> strictly better on every axis that matters (speed, memory, and simplicity of
> the zero value). Reach for the map only when the alphabet genuinely doesn't
> fit in a small fixed array.

**Rule of thumb:** `[26]*TrieNode` for lowercase-English word problems (the
large majority of trie problems on LeetCode); `map[rune]*TrieNode` when the
problem statement says "any printable character" or similar.

---

## Part 2 · Memory Layout: Why the Array Field Doesn't Cost a Separate Allocation

This is a genuinely subtle Go point that trips people up, and it connects
directly to Topic 1 Part 1.1 ("arrays are values").

```go
type TrieNode struct {
    children [26]*TrieNode   // ✅ inlined — 26 pointer slots live INSIDE this struct's allocation
    isEnd    bool
}

type TrieNodeBad struct {
    children []*TrieNode     // ⚠️ a slice header — points to a SEPARATE heap allocation
    isEnd    bool
}
```

Because a Go array is a value type embedded directly in its containing struct
(Topic 1 Part 1.1), `[26]*TrieNode` is laid out as 26 contiguous pointer-sized
slots *inside* the `TrieNode` allocation itself — one `new(TrieNode)` call
gets you the node **and** its full children table in a single allocation. A
`[]*TrieNode` slice field, by contrast, is a 24-byte header (Topic 1 Part 1.2)
whose `array` pointer references a *second*, separately-allocated backing
array — creating a node would cost two allocations and an extra pointer hop on
every child lookup.

```
TrieNode (array field)              TrieNode (slice field)
┌─────────────────────────┐         ┌───────────────────────┐
│ children: [26]*TrieNode │         │ children: slice header│──┐
│   [nil][nil][ptr]...    │         │   ptr,len=26,cap=26   │  │
│ isEnd: bool             │         ├───────────────────────┤  │
└─────────────────────────┘         │ isEnd: bool           │  │
   ONE allocation                   └───────────────────────┘  │
                                        SECOND allocation ◄─────┘
                                        [nil][nil][ptr]...
```

⚡ One allocation per node instead of two, and one fewer pointer dereference
per child lookup — this is exactly why `[26]*TrieNode` beats `[]*TrieNode`
even before you consider the map alternative.

---

```arch
%% caption: Words: car, cat, cow, do. Green nodes end a word. Words sharing a prefix share a path, and search costs O(length of the word), independent of how many words are stored.
route straight
grid 80x80
node root "root" at 2,0 shape=circle color=blue
node c "c" at 1,1 shape=circle color=blue
node d "d" at 3,1 shape=circle color=blue
node ca "a" at 0.5,2 shape=circle color=blue
node co "o" at 1.5,2 shape=circle color=blue
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

## Part 3 · Insert, Search, StartsWith

```go
func (t *Trie) Insert(word string) {
    node := t.root
    for i := 0; i < len(word); i++ {
        idx := word[i] - 'a'
        if node.children[idx] == nil {
            node.children[idx] = &TrieNode{}   // lazy creation — only allocate what's used
        }
        node = node.children[idx]
    }
    node.isEnd = true
}
```

`node.children[idx] == nil` works for free because Go zero-initializes every
pointer to `nil` — an untouched `TrieNode` already has a fully "empty" 26-slot
children table with no explicit setup (Topic 1 Part 1.1's zero-value theme
applies here too).

```go
// walk returns the node reached by following word, or nil if the path breaks.
func (t *Trie) walk(word string) *TrieNode {
    node := t.root
    for i := 0; i < len(word); i++ {
        idx := word[i] - 'a'
        if node.children[idx] == nil {
            return nil
        }
        node = node.children[idx]
    }
    return node
}

func (t *Trie) Search(word string) bool {
    node := t.walk(word)
    return node != nil && node.isEnd   // ⚠️ must be a WORD END, not just reachable
}

func (t *Trie) StartsWith(prefix string) bool {
    return t.walk(prefix) != nil       // any reachable node is enough
}
```

> ⚠️ **The classic trie bug**: `Search` and `StartsWith` share the same
> traversal but differ in exactly one check — `node.isEnd`. Forgetting it in
> `Search` makes every inserted *prefix* look like a complete word (e.g. after
> inserting `"apple"`, `Search("app")` would wrongly return `true`). This is
> the single most common trie mistake in interviews — say the distinction out
> loud before you code it.

---

## Part 4 · Complexity

| Operation | Time | Space | Note |
|---|:--:|:--:|---|
| `Insert(word)` | **O(L)** | O(L) worst case | L = `len(word)`; O(1) extra if the path already exists |
| `Search(word)` | **O(L)** | O(1) | Independent of dictionary size N |
| `StartsWith(prefix)` | **O(L)** | O(1) | Same traversal as Search, minus the `isEnd` check |
| Build trie of N words, avg length L | O(N·L) | O(ALPHABET · N · L) worst case | Shared prefixes reduce real usage well below the worst case |

The headline value proposition: **lookup cost depends only on the word's own
length, never on how many other words are stored.** A hash set of N words
also gives O(L) average lookup (hashing the string), but a trie additionally
gives you `StartsWith` — a prefix query — in the same O(L), which a hash set
cannot do without scanning.

---

## Part 5 · Applications

### 5.1 Word Search II — trie + backtracking on a grid (LC 212)

Build one trie from the whole word list, then <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>/backtrack from every grid
cell, walking the trie in lockstep with the grid path instead of re-checking
each candidate word from scratch. This reuses the Topic 9 choose→recurse→
un-choose template: "choose" a cell, recurse into the trie node one level
deeper, "un-choose" (mark the cell unvisited again) on the way back.

```go
func dfs(board [][]byte, r, c int, node *TrieNode, path []byte, found *[]string) {
    ch := board[r][c]
    idx := ch - 'a'
    next := node.children[idx]
    if next == nil {
        return
    }
    path = append(path, ch)
    if next.isEnd {
        *found = append(*found, string(path)) // string(path) COPIES the bytes — safe
        next.isEnd = false                    // avoid duplicate results
    }

    board[r][c] = '#'                          // mark visited in place
    for _, d := range [][2]int{{-1, 0}, {1, 0}, {0, -1}, {0, 1}} {
        nr, nc := r+d[0], c+d[1]
        if nr >= 0 && nr < len(board) && nc >= 0 && nc < len(board[0]) && board[nr][nc] != '#' {
            dfs(board, nr, nc, next, path, found)
        }
    }
    board[r][c] = ch                            // un-choose: restore the cell
}
```

> ⚠️ Note `string(path)` — not `append(result, path)`. This is Topic 1 Part
> 1.2's aliasing warning wearing a trie costume: `path` is a `[]byte` mutated
> in place across the whole <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>, so appending it *directly* to the result
> would alias one shared backing array across every match. `string(path)`
> allocates and copies the bytes at the moment of the match, which is exactly
> the fix the exemplar prescribes (`cp := make(...); copy(...)`), just spelled
> via a builtin conversion instead of a manual copy.

### 5.2 Replace Words (LC 648) — shortest-prefix lookup

Insert every "root" into a trie; for each word in a sentence, walk the trie
one character at a time and stop at the **first** `isEnd` you hit — that's
the shortest matching root, found in O(L) without scanning the whole root
list per word.

### 5.3 Bit trie (bridge to Topic 20)

The same node-per-branch idea works over the **binary representation** of
integers instead of characters: a trie of depth 32 (or 64) where each node has
exactly 2 children (`children [2]*TrieNode`, bit 0 or bit 1). Inserting all
numbers and then, for a query `x`, greedily walking the *opposite* bit at each
level maximizes `x XOR (something in the trie)` in O(32) — the standard
"Maximum <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> of Two Numbers in an Array" technique. Same array-vs-map
reasoning applies, but here the branching factor is always 2, so the array
choice is never in question.

---

## Part 6 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Node children | `dict` (or `defaultdict(dict)`) — always a hash map | Choose `[26]*TrieNode` (array) or `map[rune]*TrieNode` — a real design decision |
| Zero-value child | `dict.get(c)` returns `None` for free | `nil` pointer for an untouched array slot — same idea, no setup needed |
| Node allocation | One object per node, <abbr title="Garbage Collection. A form of automatic memory management that attempts to reclaim garbage, or memory occupied by objects that are no longer in use by the program.">GC</abbr>-managed like everything else | One allocation per node with the array design; two with the slice-field design (Part 2) |
| String building for matches | `''.join(path)` — implicit copy on join | `string(path)` — implicit copy on conversion; forgetting this aliases (Part 5.1) |
| Alphabet flexibility | `dict` handles any hashable key with zero code change | Switching alphabets means switching node representation entirely |

---

## Part 7 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Trie insert / search / startsWith | O(L) | O(ALPHABET·N·L) worst | LC 208 Implement Trie |
| Trie + backtracking grid search | O(rows·cols·4^L) bounded by trie pruning | O(N·L) for the trie | LC 212 Word Search II |
| Shortest-prefix root lookup | O(L) per word | O(ALPHABET·N·L) | LC 648 Replace Words |
| Binary (<abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr>) trie | O(32) per query | O(32·N) | LC 421 Maximum <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> of Two Numbers |
| Prefix-count trie (augmented with a counter) | O(L) | O(ALPHABET·N·L) | LC 677 Map Sum Pairs |

---

## Part 8 · Building a Trie From Scratch (LC 208)

```go
package main

type TrieNode struct {
    children [26]*TrieNode
    isEnd    bool
}

type Trie struct {
    root *TrieNode
}

func Constructor() Trie {
    return Trie{root: &TrieNode{}}
}

func (t *Trie) Insert(word string) {
    node := t.root
    for i := 0; i < len(word); i++ {
        idx := word[i] - 'a'
        if node.children[idx] == nil {
            node.children[idx] = &TrieNode{}
        }
        node = node.children[idx]
    }
    node.isEnd = true
}

// walk is the shared traversal for Search and StartsWith — the only
// difference between the two callers is whether they check isEnd.
func (t *Trie) walk(word string) *TrieNode {
    node := t.root
    for i := 0; i < len(word); i++ {
        idx := word[i] - 'a'
        if node.children[idx] == nil {
            return nil
        }
        node = node.children[idx]
    }
    return node
}

func (t *Trie) Search(word string) bool {
    node := t.walk(word)
    return node != nil && node.isEnd
}

func (t *Trie) StartsWith(prefix string) bool {
    return t.walk(prefix) != nil
}
```

**Talk track while writing:** the array is one allocation per node and O(1)
child lookup with no hashing; lazy creation means you never allocate a slot
you don't use; `walk` is factored out because `Search` and `StartsWith` are
the same traversal with one different terminal check — say that out loud so
the interviewer sees you noticed the shared structure instead of
copy-pasting the loop twice.

---

<!-- block:13_go_1_problems -->
## Part 9 · The Seven Problems in Go, Plus Delete, Pruning and the Trie Family

All code below ran on Go 1.24.5 against LeetCode's own examples; the numbers are measurements from this machine.

```arch
%% caption: One node type, three shapes. The alphabet decides the children field; the problem decides what else the node carries.
grid 210x90
node q "Design the trie node" at 1,0 shape=pill
node a "Alphabet?" at 1,1 shape=diamond color=amber
node b "children [26]*Node" at 0,2 color=green w=200 sub="fastest lookup, 224 B per node"
node c "children [2]*Node" at 1,2 color=green w=200 sub="Max XOR"
node d "children map[rune]*Node" at 2,2 color=amber w=200 sub="smaller per node when sparse"
node e "What else does a node carry?" at 1,3 shape=diamond color=amber
node f "isEnd bool" at 0,4 color=green w=200 sub="Implement Trie, Wildcards"
node g "word string" at 1,4 color=green w=200 sub="Word Search II"
node h "sum / passCount int" at 2,4 color=green w=200 sub="Map Sum Pairs"
q -> a
a -> b : "a-z, dense"
a -> c : "bits of an integer"
a -> d : "sparse, mixed case, Unicode"
b -> e
c -> e
d -> e
e -> f : "is this a word?"
e -> g : "the word itself"
e -> h : "an aggregate"
```

### Wildcards (LC 211): a method on a `nil` receiver

`Add` is Insert unchanged. `Search` becomes a <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> where `.` tries every live child. Go lets you call a method on a `nil`
pointer, so the "dead branch" guard can live at the *top* of `Search` — the recursive call needs no `if child != nil`:

```go
func (t *WD) Search(w string) bool {
    if t == nil { return false }                       // a dead branch: the guard at the TOP of every call
    if len(w) == 0 { return t.isEnd }                  // the length check comes BEFORE isEnd
    if w[0] == '.' {
        for _, ch := range t.children { if ch.Search(w[1:]) { return true } }   // nil children hit the guard
        return false
    }
    return t.children[w[0]-'a'].Search(w[1:])
}                                                      // bad,dad,mad: pad→false bad→true .ad→true b..→true b→false
```

This is the deliberate use of Topic 08's nil-receiver behaviour. Checking `isEnd` before `len(w) == 0` returns `true` for a
pattern with characters left to match; forgetting the nil guard panics on `t.children`. (`w[1:]` is an O(1) header.)

### Map Sum Pairs (LC 677): store the **delta**

Keep a `sum` on every node — the total of all keys passing through it — plus a `map[string]int` of the last value per
key. On insert add `val - old` (a missing key reads `0`, so the first insert's delta is `val`); `Sum(prefix)` is one walk
and one read:

```go
delta := val - m.vals[key]                             // NOT val: a re-insert would double-count
m.vals[key] = val
for i := 0; i < len(key); i++ { n = n.children[key[i]-'a'] /* create if nil */; n.sum += delta }
```

`insert("apple",3)`, `sum("ap") = 3`; `insert("app",2)`, `sum("ap") = 5`; `insert("apple",2)` → `sum("ap") = 4`.

### Maximum <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> (LC 421): a trie over bits, **most significant first**

```go
type bitNode struct{ ch [2]*bitNode }

// insert every number: bits 31..0, MSB first — a FIXED width, so every path has the same depth
// query: at each level prefer the OPPOSITE bit (it puts a 1 in the result)
for b := 31; b >= 0; b-- {
    bit := x >> b & 1
    if n.ch[1-bit] != nil { cur |= 1 << b; n = n.ch[1-bit] } else { n = n.ch[bit] }
}                                                       // [3 10 5 25 2 8] -> 28
```

MSB first is not optional: one 1 in a high bit outweighs every combination of lower bits, which is what makes the greedy
choice safe. Walking LSB first, or iterating a variable number of bits per number, misaligns the levels.

### Replace Words (LC 648): the first hit is the shortest

Build one trie of the roots; for each sentence word walk it and **stop at the first `isEnd`** — the first hit is by
construction the shortest root. Return `w[:j+1]` (a substring header, no copy). Rebuilding the trie per word, or going on
to the longest match, are the two failures. `["cat","bat","rat"]` on `"the cattle was rattled by the battery"` →
`"the cat was rat by the bat"`.

### Search Suggestions (LC 1268): a trie is not required

Sorted products make every prefix's matches **one contiguous block**: `sort.SearchStrings` finds where the block starts
and you take up to three that still `strings.HasPrefix`. Two traps: taking `products[i:i+3]` without the prefix check
(a non-matching word sneaks in), and forgetting to sort first.

```go
start := sort.SearchStrings(products, prefix)          // first product >= prefix
for j := start; j < len(products) && len(s) < 3 && strings.HasPrefix(products[j], prefix); j++ { s = append(s, products[j]) }
```

O(n log n) once, then O(log n + 3) per prefix, with no extra structure.

### Word Search II: store the word at the node, and prune exhausted branches

Keep the **whole word** on its end node (`word string`), so no path buffer is needed and no `string(path)` copy. Take it
once (`node.word = ""` after appending — this also dedupes) and, when a node has no word and no children left after its
<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>, **cut it from its parent** so later searches never enter it:

```go
if node.word != "" { res = append(res, node.word); node.word = "" }      // take it ONCE
...
if prune && node.word == "" && isEmpty(node) { parent.children[ch-'a'] = nil }   // exhausted: cut it off
```

On a random 6×6 grid over `{a, b}` with 200 words of length 3–8, both versions returned the same 126 words, but <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> visits
fell from **13,005 to 569** (about 23×). The gain grows with how many words get found. Restore `board[r][c]` after
every call, and mark cells with the in-place `'#'` sentinel rather than a `visited` set.

### Delete, with pruning

Unmark the word, then prune bottom-up only nodes that are childless **and** not words — never a node that is still a prefix
of another surviving word. The recursion returns "am I now empty?" so each level decides for itself:

```go
func (n *Node) delete(w string, i int) (empty bool) {
    if i == len(w) { n.isEnd = false; return n.isLeaf() }
    c := w[i] - 'a'
    child := n.children[c]
    if child == nil { return false }                          // the word was never stored
    if child.delete(w, i+1) { n.children[c] = nil }           // the child became empty: detach it
    return !n.isEnd && n.isLeaf()
}
```

(`isLeaf` reports whether all 26 children are `nil`.)

### The family around the trie

| Structure | What it changes | Use it for |
|---|---|---|
| **Radix / Patricia tree** | Collapse single-child chains into one labelled edge | Far fewer nodes on sparse data; routing tables. |
| **Ternary search tree** | Three pointers per node (`<`, `=`, `>`) | Compact and ordered for any alphabet. |
| **DAWG / DAFSA** | Merge identical *suffixes* too | The smallest exact word-set automaton (dictionaries, Scrabble). |
| **Aho–Corasick** | A trie plus failure links (<abbr title="Knuth-Morris-Pratt. A string-searching algorithm that searches for occurrences of a word within a main text string in optimal time.">KMP</abbr>'s idea, topic 23) | All occurrences of many patterns in one pass. |
| **Suffix trie / tree / array** | Index every suffix of a text | Substring search, longest repeated substring. |

### Go traps in this topic

| Trap | What happens | The fix |
|---|---|---|
| `word[i] - 'a'` on a non-lowercase byte | Index out of range **panic** (or a wrong slot for `A`–`Z`). | Validate the input, or use a `map[rune]` node. |
| Iterating `for _, ch := range t.children` and calling a method on `nil` | Fine *only* if the method has a nil guard. | Put `if t == nil` at the top, or check `ch != nil`. |
| `[]*TrieNode` field instead of `[26]*TrieNode` | Two allocations per node and an extra pointer hop (Part 2). | The array field. |
| Appending the mutating `path []byte` to results | Every match aliases one backing array. | Store `node.word`, or `string(path)` (which copies). |
| Rebuilding the trie per query | O(queries · N · L). | Build once, query many times. |
| Assuming the array trie is always smaller | 20.7 MB vs 15.7 MB for the map trie on random words. | Measure on your data. |

### Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Delete a word." | Unmark, then prune bottom-up only nodes that are childless and not words. |
| "Top-k suggestions." | Precompute the top-k per node at insert time (O(k) per node), or <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> the subtree with a heap. |
| "Unicode / case-insensitive." | `map[rune]*Node` and normalise first (`strings.ToLower`, `golang.org/x/text/unicode/norm`). |
| "Doesn't fit in memory." | Radix tree / DAFSA, shard by first letter, or an on-disk index. |
| "Count words with a prefix." | A `pass` count on each node. |
| "Concurrent access?" | Immutable tries are safe to read concurrently; guard updates with `sync.RWMutex`, or swap in a new root atomically (`atomic.Pointer`). |

---
<!-- /block:13_go_1_problems -->

<!-- problem-map:start -->
## Part 10 · Every Problem in This Topic, by Pattern

Seven problems, four moves (the basic trie · wildcards · augmenting nodes · a trie as a search index) — the Python guide's map in Go, with the Go-only traps. Topic 13's solutions are Python-first; the Go column is the plan you would write.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Implement Trie (Prefix Tree)](GoDSA/13_trie/001_implement_trie_prefix_tree/solution.go) <br>LC 208 · Medium | The basic trie | `children [26]*TrieNode` (one allocation per node) and `isEnd`; a shared `walk` for `Search` and `StartsWith`. **Trap:** `Search` without the `isEnd` check (`"app"` after inserting `"apple"`); a `[]*TrieNode` field (two allocations). |
| [002 · Design Add and Search Words Data Structure](GoDSA/13_trie/002_design_add_and_search_words_data_structure/solution.go) <br>LC 211 · Medium | Wildcard search by <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> | A method with a `nil`-receiver guard at the top; `.` loops over the children; check `len(w) == 0` before `isEnd`. **Trap:** checking `isEnd` too early; no nil guard (panic on `t.children`). |
| [003 · Replace Words](GoDSA/13_trie/003_replace_words/solution.go) <br>LC 648 · Medium | First hit is the shortest | One trie of the roots; stop at the first `isEnd`; return `w[:j+1]` (no copy). **Trap:** continuing to the longest match; rebuilding per word. |
| [004 · Map Sum Pairs](GoDSA/13_trie/004_map_sum_pairs/solution.go) <br>LC 677 · Medium | Augmented nodes | A `sum` per node plus a `map[string]int` of last values; add the **delta** `val - m.vals[key]` (a missing key reads 0). **Trap:** adding `val` on a re-insert (double-counts). |
| [005 · Maximum XOR of Two Numbers in an Array](GoDSA/13_trie/005_maximum_xor_of_two_numbers_in_an_array/solution.go) <br>LC 421 · Medium | A bit trie | `children [2]*bitNode`, bits 31→0, prefer the *opposite* bit. **Trap:** LSB-first; a variable bit width per number. |
| [006 · Word Search II](GoDSA/13_trie/006_word_search_ii/solution.go) <br>LC 212 · Hard | Trie + grid backtracking | `word string` on the end node, take it once, prune exhausted branches, `'#'` sentinel restored after every call. **Trap:** forgetting the restore; appending the mutating `path`; a `visited` set. |
| [007 · Search Suggestions System](GoDSA/13_trie/007_search_suggestions_system/solution.go) <br>LC 1268 · Medium | Two designs for autocomplete | `sort.Strings` + `sort.SearchStrings` + `strings.HasPrefix` (a contiguous block), or a trie. **Trap:** no prefix filter on the slice; not sorting first. |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain why `[26]*TrieNode` beats `map[byte]*TrieNode` for ASCII-lowercase problems, and when the map wins instead
- [ ] Explain why an array field is one allocation but a slice field is two
- [ ] State the `Search` vs `StartsWith` distinction (`isEnd` check) without hesitating
- [ ] Explain why trie lookup is O(L), independent of dictionary size N
- [ ] Trace the Word Search II grid-<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr>-with-trie-pruning approach, including why `string(path)` (not appending the mutating slice) avoids aliasing
- [ ] Know at least one non-string trie application (binary/<abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> trie) and why the branching factor forces the array design
- [ ] Write Insert/Search/StartsWith with lazy node creation in under 10 minutes
- [ ] Quote the array-vs-map trie trade-off with numbers: ~10× faster lookups, but *more* memory on sparse data <!--ca-->
- [ ] Use a nil-receiver guard so a wildcard <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> needs no `if child != nil` <!--ca-->
- [ ] Store the word at its end node, take it once, and prune exhausted branches in Word Search II <!--ca-->
- [ ] Add the delta (not the value) in Map Sum Pairs, and walk bits MSB-first in Max <abbr title="Exclusive OR. A bitwise operation that evaluates to true if and only if its arguments differ.">XOR</abbr> <!--ca-->
- [ ] Delete a word and prune only childless non-word nodes <!--ca-->
