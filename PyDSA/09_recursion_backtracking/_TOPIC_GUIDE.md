# Topic 09 · Recursion / Backtracking — Python Deep Dive

> Backtracking is not a new algorithm. It is DFS over a **decision tree you build
> as you go**: each recursive call is a node, each choice you try is an edge, and
> a leaf is either a complete valid answer or a dead end. The entire topic is one
> template — **choose → explore → unchoose** — instantiated with fourteen
> different "what are my choices here?" functions. Learn the template once;
> everything below is that template wearing a different choice function.
>
> You already know recursion (per CONTEXT.md — this guide will not re-explain
> what a call stack is). The depth here goes into the parts interviews actually
> probe: the template's exact shape, why the "unchoose" step exists at all,
> pruning as a search-tree-size argument (not vibes), and duplicate handling as
> a precise sort-then-skip mechanism.

---

## Part 0 · Fibonacci is not backtracking — it is the bridge to DP

001 sits in this topic because it is **recursion without a decision tree** — no
choices, no leaves, no path to build. It exists here to demonstrate the single
most important fact about naive recursion before you need it for real: **naive
recursion recomputes the same subproblem exponentially many times**, and
memoization turns the call *graph* (a DAG with massive overlap) into a call
*tree* traversal that visits each distinct subproblem once.

```
fib(5)
├── fib(4)
│   ├── fib(3)
│   │   ├── fib(2) ── fib(1), fib(0)
│   │   └── fib(1)
│   └── fib(2) ── fib(1), fib(0)     <-- fib(2) computed AGAIN
└── fib(3)                            <-- fib(3) computed AGAIN
    ├── fib(2) ── fib(1), fib(0)
    └── fib(1)
```

`fib(3)` is computed twice, `fib(2)` three times — and the redundancy compounds:
naive `fib(n)` makes `O(2^n)` calls (technically `O(φ^n)`, φ ≈ 1.618) because the
recursion tree has no memory across branches. Memoizing collapses it to `O(n)`
distinct subproblems, each solved once. Problem 001's runtime demo measures the
actual call count for both versions — this is not asserted, it is counted live.
**This is the exact idea DP topics 16–17 build an entire toolkit around: naive
recursion over overlapping subproblems is exponential; caching results (top-down
memoization) or filling them bottom-up (tabulation) makes it polynomial.** Keep
001 in mind when you get there — it is the smallest possible example of the
pattern, stripped of everything else.

Everything from 002 onward is a true decision tree: no subproblem overlap to
exploit, because the "state" (the partial path chosen so far) is different at
every node. That is why memoization does not apply to combinatorial
enumeration — there is nothing to reuse, you must visit every valid leaf because
the problem asks you to *produce* them, not just count or optimize one.

---

## Part 1 · The universal template

```arch
%% caption: The choose, explore, un-choose loop that every backtracking problem shares.
grid 220x100
node S "backtrack(state)" at 0,0 shape=pill
node B "complete answer?" at 0,1 shape=diamond color=amber
node R "Record a COPY of state" at 1,1 shape=card icon=doc color=green
node L "for each choice available now" at 0,2 shape=box
node P "breaks a constraint?" at 1,2 shape=diamond color=amber
node SK "skip it" at 2,2 color=red sub="prune"
node C "1. choose" at 1,3 shape=card icon=check sub="modify state"
node E "2. explore" at 1,4 shape=card icon=tree sub="backtrack(state)"
node U "3. un-choose" at 0,4 shape=card icon=delete color=amber sub="undo the change"
S -> B
B -> R : "yes"
B -> L : "no"
L -> P
P -> SK : "yes"
P -> C : "no"
C -> E -> U
U -> L
```


```python
def backtrack(state, choices_remaining):
    if is_leaf(state):              # base case: a complete candidate
        if is_valid(state):         # (often the same test as "reached full length")
            record(state)           # usually: results.append(state[:])  <- COPY, see §4
        return

    for choice in choices_at(state, choices_remaining):
        if not allowed(choice, state):     # PRUNE: skip illegal/dominated choices
            continue

        choose(state, choice)              # 1. CHOOSE  — mutate shared state
        backtrack(state, choices_remaining_after(choice))   # 2. EXPLORE — recurse
        unchoose(state, choice)            # 3. UNCHOOSE — undo the mutation
```

Three lines matter more than the rest of the file: **choose, explore, unchoose.**
Every problem below is this loop with a different `choices_at()` and a different
`is_leaf()` / `allowed()`. If you can name those two functions for a problem, you
can write the solution without re-deriving the template.

**Why "unchoose" exists at all — the part people skip past too fast.** The
`state` object (a `path` list, a `board` grid, a `used` boolean array) is
typically **one shared, mutable object reused across the entire search**, not a
fresh copy handed to each recursive call. That is a deliberate memory trade
(§4): copying `state` at every node costs `O(depth)` per node and multiplies out
to the same order as the tree size itself, which is often the dominant cost.
Reusing one object means every recursive call sees the *exact* partial state
its parent left behind — so when a branch is exhausted, you must manually put
`state` back to how it was before you go try the sibling branch. Forgetting
`unchoose` does not crash; it silently corrupts every subsequent sibling branch
with leftover state from a branch that is supposed to be gone. This is the
single most common bug in the whole topic (see the "common mistakes" section of
nearly every file here).

**The decision tree, made literal.** Draw it for `subsets([1,2])`:

```
                          []
              choose 1 /        \ skip 1
            [1]                    []
       choose 2/ \skip2      choose 2/ \skip 2
      [1,2]      [1]        [2]         []
      leaf       leaf       leaf        leaf
```

Four leaves = `2^2` subsets. Every node is a call to `backtrack`; every edge is
one iteration of the `for choice in choices_at(...)` loop; every leaf is one
`record(state)`. **The size of this tree, not the length of the code, is the
complexity of the algorithm** — this is why every solution file below prices
its complexity by counting tree nodes/leaves, not by eyeballing the loops.

---

## Part 2 · The single most useful mental model: three base shapes

Every enumeration problem in this folder (002–006, 009) is one of exactly three
shapes. **The only thing that differs between subsets, permutations, and
combinations is the shape of `choices_at()`.** Everything else — the template,
the recursion, the leaf test — is identical. Internalize this table before
memorizing any individual solution:

```arch
%% caption: Subsets as a decision tree: each level is one element, each branch is a choice, and the leaves are the answers.
route straight
grid 100x100
node r "[ ]" at 1.5,0 shape=circle color=blue
node a "[1]" at 0.5,1 shape=circle color=blue
node b "[ ]" at 2.5,1 shape=circle color=blue
node a1 "[1, 2]" at 0,2 shape=circle color=green
node a2 "[1]" at 1,2 shape=circle color=green
node b1 "[2]" at 2,2 shape=circle color=green
node b2 "[ ]" at 3,2 shape=circle color=green
r -> a : "take 1"
r -> b : "skip 1"
a -> a1 : "take 2"
a -> a2 : "skip 2"
b -> b1 : "take 2"
b -> b2 : "skip 2"
```


| Shape | Question asked **at each node** | Choices at a node | Tree shape | Leaf count |
|---|---|---|---|---|
| **Subsets** (002, 003, 009-ish) | "include element `i`, or skip it?" | exactly 2: `{include, skip}`, one per *remaining element in order* | binary tree, depth = n | `2^n` |
| **Permutations** (004, 005) | "which *unused* element goes in this slot next?" | up to `n - depth` choices: any element not yet in `path` | tree with branching factor shrinking by 1 each level | `n!` |
| **Combinations** (006, 009, and the sum family 007/008) | "which element `>= last chosen index` goes next?" | only elements *after* the last one picked (never look backward) | tree pruned to be strictly increasing index order | `C(n, k)` |

The reason combinations only look forward (`>= last chosen`) is exactly what
avoids generating `[1,2]` and `[2,1]` as two different results when order does
not matter — the index-ordering constraint *is* the deduplication mechanism for
plain combinations, before any "II"-style duplicate values are even involved.

**010 (Letter Combinations) and 011 (Palindrome Partitioning) are combinations
in disguise**: 010's choice function is "which of this digit's 3-4 letters
comes next," 011's is "where does the next partition cut fall, given the prefix
up to the cut is a palindrome." Same template, `choices_at()` reads from a
digit→letter map or a substring-palindrome check instead of an index range.

**007–009 (Combination Sum family) are the combinations shape with the leaf
test changed from "path length == k" to "running sum == target," and the choice
set trimmed to whatever does not overrun the target.** 007 allows reusing the
same element (choices stay `>= last chosen`, not `> last chosen`), 008 does not
(strictly increasing index, plus the "II" dedupe below), 009 adds both a sum
target and a fixed length k simultaneously.

---

## Part 3 · The "II" duplicate-handling trick — sort, then skip adjacent equal siblings

003 (Subsets II), 005 (Permutations II), and 008 (Combination Sum II) all take
an input with **duplicate values** and must not emit duplicate results. The
naive fix — generate everything, dedupe the result set (e.g. via a `set` of
tuples) — technically works but is wasteful: it still builds the *entire*
oversized tree (including every duplicate branch) before throwing away the
duplicates at the end. On `[1,1,1,1,1,1,1,1,1,1]` (subsets), that naive
approach constructs and discards `2^10 = 1024` branches to arrive at 11 unique
results.

```arch
%% caption: Sort first, then skip a value equal to the previous one at the same level of the tree. Deeper levels may still use it.
route straight
grid 250x160
node r "[ ]" at 1,0 color=blue sub="nums sorted = [1, 1, 2]"
node a "[1]" at 0,1 color=blue
node x "skip" at 1,1 color=red
node c "[2]" at 2,1 color=blue
node a1 "[1, 1]" at 0,2 color=green
node a2 "[1, 2]" at 1,2 color=green
r -> a : "i=0: pick the first 1"
r -> x : "i=1: equals nums[0]\nat the same level"
r -> c : "i=2: pick 2"
a -> a1 : "i=1: second 1\n(deeper, allowed)"
a -> a2 : "i=2: pick 2"
```


**The fix prunes duplicate branches at generation time, not after.** Sort the
input first, then at each level of the tree, skip a choice if it is equal to
the *previous sibling already tried at this same depth*:

```python
nums.sort()
def backtrack(start, path):
    results.append(path[:])
    for i in range(start, len(nums)):
        if i > start and nums[i] == nums[i - 1]:   # skip duplicate SIBLING
            continue
        path.append(nums[i])
        backtrack(i + 1, path)
        path.pop()
```

**Why `i > start` and not `i > 0`.** `i > start` means "this is not the first
choice being tried at this node" — the first occurrence of a value at any given
tree depth is always allowed, because it is the value's first appearance as a
*sibling choice*, not a repeat of one already explored from this exact parent.
Only the second, third, ... occurrence of the same value at the same level is
skipped, because trying it would explore a subtree that is structurally
identical to the one just finished — same value chosen, same remaining choices
available — and would produce exactly the same set of leaves underneath it.

**Concrete example — `nums = [1, 1, 2]`, subsets:**

```
                              []
              i=0: choose 1 /   \ i=1: nums[1]==nums[0] AND i>start(0) -> SKIP
            [1]                (this branch never explored)
         i=1/    \i=2
       [1,1]     [1,2]
       i=2/          \i=2(none left)
    [1,1,2]

Without the skip, the i=1 branch at the root would explore choosing the SECOND
'1' first, producing [1] again (a duplicate of the i=0 branch's [1]), then
[1,1] again reached a different way, and [1,2] again — the entire subtree
under i=0 gets rebuilt under i=1, byte-for-byte identical in VALUE even though
the indices differ. The skip prunes that whole redundant subtree before it is
built, not after.
```

**This is the key distinction to say out loud in an interview**: the rule is
about skipping duplicate *choices at the same tree depth*, not about
deduplicating the final list of values overall. A duplicate value picked at
*different* depths (e.g. the first `1` at depth 0 versus a second `1` picked
later at depth 1, after the first `1` was already consumed) is completely
legal and necessary — `[1, 1, 2]` itself is a valid subset that uses both 1s.
The rule only forbids re-trying an *already-tried value as a sibling at the
same node*.

Each solution file below (003, 005, 008) benchmarks sort+skip against
generate-then-dedupe-with-a-set on an input with heavy duplication, with real
measured numbers.

---

## Part 4 · Grid backtracking (012 · Word Search) — mark, recurse, UNMARK

012 moves the choice function onto a 2D grid: "which of up to 4 neighboring
cells continues the word?" The state that must be choose/unchosen here is not a
`path` list but **which cells are currently "in use" on this exact path** —
almost always represented as mutating the board cell itself (e.g. to `'#'`) or a
parallel `visited` grid.

```arch
%% caption: Grid backtracking: mark the cell on the way in, and always restore it on the way out.
grid 230x100
node A "at cell (r, c)" at 0,0 shape=pill
node B "in bounds, letter matches, not visited?" at 0,1 shape=diamond color=amber
node X "return False" at 1,1 color=red
node C "MARK the cell as visited" at 0,2
node D "try the 4 neighbours" at 0,3
node E "UNMARK: restore the letter" at 0,4 color=amber
node F "return True if any neighbour succeeded" at 0,5 shape=pill color=green
A -> B
B -> X : "no"
B -> C : "yes"
C -> D -> E -> F
```


```python
def dfs(r, c, i):                      # i = index into the target word
    if board[r][c] != word[i]:
        return False
    if i == len(word) - 1:
        return True

    tmp, board[r][c] = board[r][c], '#'          # CHOOSE: mark visited
    found = any(
        0 <= nr < R and 0 <= nc < C and dfs(nr, nc, i + 1)
        for nr, nc in ((r+1,c), (r-1,c), (r,c+1), (r,c-1))
    )
    board[r][c] = tmp                              # UNCHOOSE: restore, ALWAYS
    return found
```

**Why this must run unconditionally, not just on the failure path.** The
"unchoose" step here is the exact same idea as `path.pop()` in the list-based
problems — the shared, mutated `state` (the board itself) must be restored
before control returns to the caller, *regardless of whether this branch
succeeded or failed*, because the caller is about to try a *different* neighbor
from the *same* cell, and that sibling exploration needs the board back to its
pre-recursion state. **Forgetting to unmark is the single most common bug in
grid backtracking**: the symptom is not a crash, it is silent
under-counting/false negatives — a word that should be found is reported
missing because an earlier, abandoned path left cells permanently marked
`'#'`, blocking a *different, valid* path through those same cells later in the
search. The bug is invisible on inputs where the correct path never needs to
revisit a marked-and-later-unmarked cell, which is exactly why it survives
casual testing — the solution file constructs a case that specifically exposes
it.

---

## Part 5 · Constraint satisfaction (013 N-Queens, 014 Sudoku) — prune BEFORE recursing, not after

N-Queens and Sudoku are the same three-line template, but the choice sets are
astronomically large if generated blindly, and the entire reason these run in
milliseconds instead of geological time is that **validity is checked before
the recursive call is made**, not by generating a complete candidate and
checking it after the fact.

```python
for col in range(n):
    if is_safe(row, col):        # <- PRUNE HERE, before recursing at all
        place(row, col)
        if backtrack(row + 1):
            return True
        remove(row, col)
return False
```

`is_safe` is `O(row)` (or `O(1)` with the column/diagonal `set`s described in
013's solution), and it is called *before* `backtrack(row + 1)` — the moment a
placement is invalid, the entire subtree beneath it (which could contain up to
`n^(n - row)` further placements) is never visited at all. Compare that to
generating every full `n x n` placement (`n^n` raw configurations, or `n!` if
you at least constrain one queen per row) and checking each after the fact —
astronomically more work for the same answer.

**Quantified, measured on this machine (013's solution file runs this live):**
for `n = 8`, the raw one-queen-per-row search space is `8^8 = 16{,}777{,}216`
row-by-row placements (or `8! = 40{,}320` if you additionally fix one queen per
column with no other pruning). With column/diagonal pruning applied *before*
each recursive call, the actual number of tree nodes visited is measured and
reported by the runtime demo — several orders of magnitude smaller, because
invalid branches are cut at their root, not walked to their leaves. The same
argument, with vastly larger raw numbers (`9^81` possible grids vs. an
actually-explored node count in the thousands, both measured), is why 014's
Sudoku solver terminates on a real "hard" puzzle in well under a second despite
Sudoku being NP-complete in general.

**This is THE takeaway from constraint-satisfaction backtracking**: pruning is
not an optimization bolted onto a working brute force — it is what makes the
approach *tractable at all*. The complexity of the tree you actually walk
depends entirely on how early you can detect "this partial assignment can never
lead to a valid leaf" and refuse to descend into it.

---

## Part 6 · Pattern decision tree

```
1. Does the problem ask you to enumerate/produce ALL valid arrangements,
   subsets, paths, or placements (not just count them, not just find one
   optimal value)?
       NO, it wants ONE optimal number and has OVERLAPPING subproblems
              (same (i, remaining) state reachable multiple ways)
              -> memoize. This is DP (topics 16/17), not this topic.
              001 Fibonacci is the toy example of exactly this fork.
       YES -> continue. You are doing backtracking / decision-tree DFS.

2. What does one PATH from root to leaf represent?
       a growing SUBSET of elements, order doesn't matter, each element
       decided independently (in/out)          -> Shape: SUBSETS (§2)
       a full-length ARRANGEMENT using every element exactly once,
       order matters                            -> Shape: PERMUTATIONS (§2)
       a fixed-size or sum-constrained SELECTION, order doesn't matter,
       never revisit an earlier index            -> Shape: COMBINATIONS (§2)

3. Can the same VALUE appear more than once in the input, and must the
   output avoid duplicate results?
       YES -> sort first, then skip adjacent-equal SIBLINGS at each tree
              depth (`i > start and nums[i] == nums[i-1]`) — §3.
       NO  -> plain shape from step 2, no dedupe needed.

4. Is the state a 2D GRID where a choice is "move to an adjacent cell"?
       YES -> mark the cell as visited before recursing, unmark on the way
              back out, unconditionally — §4. (012)

5. Does a choice at one position CONSTRAIN what is legal at other, not-yet-
   -decided positions (a row of queens threatening a column; a Sudoku cell
   constraining its row/column/box)?
       YES -> constraint satisfaction. Check validity of a placement BEFORE
              recursing into it, not after building a full candidate — §5.
              (013, 014)
       NO  -> plain enumeration, shapes 1-4 above are sufficient.
```

---

## Part 7 · Complexity is the size of the search tree

Every complexity claim in this topic's solution files is a tree-size argument,
not a loop-counting one:

| Shape | Tree size (nodes/leaves) | Where the bound comes from |
|---|---|---|
| Subsets | `O(2^n)` leaves, `O(2^n)` total nodes | binary choice at each of n elements |
| Permutations | `O(n!)` leaves, `O(n \cdot n!)` total work incl. copies | n choices, then n-1, then n-2, ... |
| Combinations `C(n,k)` | `O(C(n,k))` leaves | choose k of n, order-free |
| Combination Sum (reuse allowed) | up to `O(2^target)` in the worst case (unbounded reuse) | branching factor = candidates, depth bounded by `target / min(candidate)` |
| Word Search | `O(rows*cols*4^L)` where L = word length | 4 neighbor choices at each of L steps, from every starting cell |
| N-Queens | raw `O(n^n)`; pruned tree is far smaller (measured, not closed-form) | pruning depends on the data, no clean formula — this is WHY you measure it |
| Sudoku | raw `O(9^{81})`; pruned tree is far smaller (measured) | same reason — constraint propagation collapses it empirically |

Every solution file's "COMPLEXITY SUMMARY" table states which of these bounds
applies and why, and — where the guide above promises it — a runtime demo
actually counts the nodes visited so the stated bound is *confirmed*, not
merely asserted.

---

## Part 8 · Mutate-in-place vs copy-on-every-call — the memory argument, benchmarked

Nearly every solution here mutates one shared `path` (or `board`) list in place
across the whole recursion, rather than constructing and passing a new list to
each recursive call. This is not a style preference — it changes the space
complexity of the recursion itself:

- **Copy at every call**: each of the `O(2^n)` / `O(n!)` / `O(C(n,k))` nodes
  allocates a new list of size up to `O(n)`, so the *total* allocation work
  across the whole tree is an extra factor of `O(n)` beyond the leaf count —
  turning, say, subsets' `O(2^n)` leaf-generation cost into `O(n \cdot 2^n)`
  just for the copying, on top of whatever copying the result-recording step
  needs anyway.
- **Mutate in place, `append`/`pop`**: each `choose`/`unchoose` pair is `O(1)`
  amortized (Python list `append`/`pop` from the end), and the *only* place an
  `O(n)`-sized copy is unavoidable is the leaf, where the current path must be
  recorded into the results list — which is one copy per leaf, not one copy
  per node.

Every solution file benchmarks this directly on subsets/permutations, with real
timings, and it is also where the **copy-on-append trap** (per CONTEXT.md §1)
gets its backtracking-specific form: appending the *reference* to the shared
`path` list instead of a `path[:]` copy at the leaf means every entry in
`results` ends up **pointing at the same list object**, which is then mutated
back to `[]` (or garbage) by the time the whole recursion finishes — every
recorded "answer" silently becomes identical (usually all empty, or all equal
to the last leaf visited). This is demonstrated live, not just described, in
002's and 004's solution files, since those are where the trap first appears
and where the runtime demo constructs the corrupted output for you to see.

---

## Part 9 · The progression in this folder

```
  001  LC 509  Fibonacci Number                bridge topic: naive exp. recursion
                                                vs memoization, measured call counts
  002  LC 78   Subsets                         Shape: subsets, the archetype
  003  LC 90   Subsets II                      + sort/skip dedupe (§3)
  004  LC 46   Permutations                    Shape: permutations, `used[]` tracking
  005  LC 47   Permutations II                 + sort/skip dedupe on permutations
  006  LC 77   Combinations                    Shape: combinations, C(n,k) leaves
  007  LC 39   Combination Sum                 combinations + sum target, reuse allowed
  008  LC 40   Combination Sum II               007 + sort/skip dedupe, no reuse
  009  LC 216  Combination Sum III              combinations + sum target + fixed k
  010  LC 17   Letter Combos of a Phone Number  combinations shape, digit->letter map
  011  LC 131  Palindrome Partitioning          combinations shape, cut-point choices
  012  LC 79   Word Search                      grid backtracking, mark/unmark (§4)
  013  LC 51   N-Queens                         constraint satisfaction, prune-before (§5)
  014  LC 37   Sudoku Solver                     constraint satisfaction, harder constraints
```

002 → 006 → 009 is the same "combinations" shape sharpened three times. 003,
005, 008 are the same dedupe trick applied to three different base shapes —
do them in that relative order (right after their non-dedupe sibling) so the
diff is obvious. 012–014 are the three "state beyond a simple path" problems
and should be done last.

### Where this goes next

- **Topic 10 - Trees (DFS).** A binary tree traversal IS this same template
  with the pool of choices fixed at exactly {left child, right child} and
  usually no unchoose step for the tree itself (you're not mutating tree
  structure) -- though you still push/pop a `path` list the same way when
  collecting root-to-leaf paths (e.g. LC 113 Path Sum II). Recognize 012
  Word Search as the missing link: it's tree-shaped DFS over a grid where
  the "tree" is generated on the fly from 4-way adjacency instead of
  `.left`/`.right` pointers.
- **Topics 16/17 - DP.** 001 Fibonacci already showed the mechanism: when a
  backtracking-shaped recursion's calls form a DAG with repeated
  subproblems (not a tree of genuinely distinct paths), add a memo dict
  keyed by the recursion's state signature and you've turned exponential
  backtracking into polynomial DP. The test is always the one from Part 0:
  do sibling branches ever recompute the *same* subproblem? Subsets/
  Permutations/Combinations never do (every leaf is a distinct answer, so
  there's nothing to memoize) -- that's what makes them backtracking and not
  DP. Combination-Sum-style problems with a numeric target (007, 009) are
  the borderline case: memoizing (index, remaining_target) is exactly how
  you'd convert 007 into the unbounded-knapsack DP you'll meet in topic 17.


---

<!-- block:09_py_1_tools -->
## Part 10 · Pruning, Ordering and the Tools Around Backtracking

Parts 1–8 give the template and the shapes. These are the tools that separate a correct solution from one that
finishes in time — and the standard follow-ups. Every snippet below was run, and every number is a measurement
from this machine.

### 10.1 What pruning actually prunes

Two cheap prunes cover most problems, and it matters *what each one saves*.

**Sort the candidates, then `break` — not `continue`.** In Combination Sum, once a sorted candidate exceeds the
remaining target, every later one does too:

```python
cands.sort()
for i in range(start, len(cands)):
    c = cands[i]
    if c > remain: break               # not `continue`: everything after is larger still
    path.append(c); bt(i, remain - c); path.pop()
```

It does **not** shrink the recursion tree — the number of recursive calls is *identical* (4,035 for `[8,7,4,3,2,5,6,9,10,11]`,
target 30; 215,308 for `1..40`, target 40). It shrinks the *scanning*: loop iterations fell from 13,348 to 6,959, and
for `1..40` from **5,393,015 to 393,276** (13.7×). Say which one you are claiming.

**Bound the loop by what is still needed.** In Combinations, if you need `k - len(path)` more numbers, starting later
than `n - (k - len(path)) + 1` can never finish:

```python
hi = n - (k - len(path)) + 1
for i in range(start, hi + 1): ...
```

Same 184,756 results for `C(20, 10)`, but recursive calls fell from **616,666 to 352,716** (−43%). For tiny `k` the
effect is negligible (1,351 → 1,330 at `k = 3`) — which is why you measure instead of assuming.

The interview sentence: *"pruning cuts the typical case a lot; the worst-case class is still the unpruned tree."*

### 10.2 Bitmasks for constraint problems (N-Queens without sets)

Three integers replace three sets: which columns are taken, and which two diagonal directions are attacked. The lowest
set bit of the "available" mask is the next legal column, and the diagonal masks shift one step per row:

```python
def n_queens_count(n):
    full = (1 << n) - 1
    def bt(cols, d1, d2):
        if cols == full: return 1
        total, avail = 0, full & ~(cols | d1 | d2)
        while avail:
            bit = avail & -avail                       # lowest set bit = a legal column
            avail ^= bit
            total += bt(cols | bit, ((d1 | bit) << 1) & full, (d2 | bit) >> 1)
        return total
    return bt(0, 0, 0)
# n = 1..8 -> [1, 0, 0, 2, 10, 4, 40, 92]
```

Choose, test and undo are single integer operations — nothing to `remove()` on the way back, because the masks are
passed by value. It also makes "count the solutions" trivial (no boards stored). Sudoku uses the same idea with one
9-bit mask per row, column and box; the classic speed-up on top is the **most-constrained-cell heuristic**: pick the
empty cell with the fewest legal digits next, so dead ends appear near the root instead of the leaves.

### 10.3 New choice shapes: segments and lengths (LC 93)

Restore IP Addresses has no shared pool: at each step you choose the **length** (1–3) of the next segment, with two
validity rules (`<= 255`, no leading zero). The path is the four segments so far:

```python
def restore_ip(s):
    res = []
    def bt(i, parts):
        if len(parts) == 4:
            if i == len(s): res.append(".".join(parts))          # used ALL the digits
            return
        for ln in (1, 2, 3):
            if i + ln > len(s): break
            seg = s[i:i+ln]
            if (len(seg) > 1 and seg[0] == "0") or int(seg) > 255: continue
            parts.append(seg); bt(i + ln, parts); parts.pop()
    bt(0, [])
    return res
# "25525511135" -> ['255.255.11.135', '255.255.111.35']     "0000" -> ['0.0.0.0']
```

The depth limit (exactly 4 parts) is what keeps this tiny: the tree has at most `3⁴ = 81` leaves.

### 10.4 Precompute what the tree keeps re-asking (Palindrome Partitioning)

The naive solution re-checks `s[start:end+1] == s[start:end+1][::-1]` at every node. Precompute a table once — an
`O(n²)` DP — and each test is `O(1)`:

```python
is_pal = [[False] * n for _ in range(n)]
for i in range(n - 1, -1, -1):
    for j in range(i, n):
        is_pal[i][j] = s[i] == s[j] and (j - i < 2 or is_pal[i + 1][j - 1])
```

The output is still exponential (`"aaaa"` has `2³ = 8` partitions), but the per-node cost drops from `O(n)` to `O(1)`.
This is the bridge to DP: when a *sub-question* repeats, tabulate it.

### 10.5 When the state repeats, backtracking becomes DP

If two different paths can arrive at the **same state** (`index`, `remaining`, a bitmask of used items) and the question
is a *count* or a *yes/no* rather than "list every path", memoise the state. Word Break, Partition to K Equal Sum
Subsets and "target sum" all live on this fork. For enumeration of *every* answer, memoisation cannot help — the output
is the cost. Partition to K Equal Sum Subsets shows the pruning tricks that make raw search viable:

```python
nums.sort(reverse=True)                          # place the big items first: fail fast
...
for b in range(k):
    if buckets[b] + nums[i] > target or buckets[b] in seen: continue   # `seen`: skip a bucket whose fill equals one already tried
    seen.add(buckets[b]); buckets[b] += nums[i]
    if bt(i + 1): return True
    buckets[b] -= nums[i]
```

### 10.6 Generators, iterators and oracles

`yield from` streams solutions without building the whole result list — useful when the caller wants the first few, or
the total will not fit in memory:

```python
def subsets_gen(nums):
    def bt(start, path):
        yield path[:]                            # still a COPY: the path list is reused
        for i in range(start, len(nums)):
            path.append(nums[i]); yield from bt(i + 1, path); path.pop()
    yield from bt(0, [])
```

`itertools` is your **test oracle**: `list(itertools.permutations(nums))` matches the used-array permutations *in the
same order*, and `chain.from_iterable(combinations(nums, r) for r in range(len(nums) + 1))` matches the subsets as a
set. Compare your output against them before you trust it. Iterative one-liners exist too — subsets by cascading:

```python
res = [[]]
for x in nums: res += [r + [x] for r in res]      # [1,2,3] -> [[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]
```

### 10.7 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Only count them / only find one." | Count: return an integer up the stack (no path stored). Find one: return `True` up the stack and stop at the first success (the *cascade return* of Sudoku). |
| "Can you do better than exponential?" | For *enumeration* no — the output has `2ⁿ` / `n!` entries. For counting or existence, look for repeating states (DP) or structure (N-Queens counting has no closed form). |
| "It is too slow." | Prune earlier (validity before recursing), order the choices (sort, most-constrained first), bound the loop, use bitmasks, exploit symmetry (N-Queens: solve the left half, mirror it). |
| "Recursion limit / very deep." | CPython stops at ~1000 frames. Backtracking depth is usually small (`n`), but convert to an explicit stack if not. |
| "Parallelise it." | Split at the first level: each first choice is an independent subtree, so give each to a worker and merge the results. |
| "Duplicates in the input." | Sort, then skip equal *siblings* — never equal values across depths (Part 3). |
| "Return in lexicographic order." | Sorted input plus an increasing-index loop produces lexicographic order for free. |

---
<!-- /block:09_py_1_tools -->

<!-- problem-map:start -->
## Part 11 · Every Problem in This Topic, by Pattern

Fourteen problems, five moves (memoisation as the bridge · the three base shapes · duplicate handling · grid backtracking · constraint satisfaction). Each **Trap** is one the tests in that problem's solution file actually trigger.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Fibonacci Number](PyDSA/09_recursion_backtracking/001_fibonacci_number_solution.py) <br>LC 509 · Easy | The bridge to DP | Naive recursion recomputes overlapping subproblems exponentially; caching each result the first time turns O(2ⁿ) into O(n). This is *not* backtracking — there is one answer, not a tree of distinct paths. **Trap:** off-by-one base cases (`F(0) = F(1) = 1`); a cache that is rebuilt on every call. |
| [002 · Subsets](PyDSA/09_recursion_backtracking/002_subsets_solution.py) <br>LC 78 · Medium | Subsets — every node is an answer | Record the current path at *every* node, then extend it with each later index: `2ⁿ` results. **Trap:** `results.append(path)` instead of `path[:]` — every entry aliases the one list that is later popped empty. |
| [003 · Subsets II](PyDSA/09_recursion_backtracking/003_subsets_ii_solution.py) <br>LC 90 · Medium | Sort, then skip equal siblings | Sort so equal values are adjacent, then skip a value that repeats the previous *sibling at the same node*: `i > start and nums[i] == nums[i-1]`. **Trap:** not sorting (`[2, 1, 2]`); `i > 0` instead of `i > start` (forbids legitimate reuse across depths). |
| [004 · Permutations](PyDSA/09_recursion_backtracking/004_permutations_solution.py) <br>LC 46 · Medium | Permutations | At each slot choose any *unused* element (a `used[]` array or an in-place swap); leaves are complete arrangements: `n!`. **Trap:** appending the shared `path` instead of a copy. |
| [005 · Permutations II](PyDSA/09_recursion_backtracking/005_permutations_ii_solution.py) <br>LC 47 · Medium | Permutations II | 004 plus the sibling guard adapted to a tree with no `start`: `i > 0 and nums[i] == nums[i-1] and not used[i-1]`. **Trap:** dropping `not used[i-1]` — it forbids permutations that are perfectly valid. |
| [006 · Combinations](PyDSA/09_recursion_backtracking/006_combinations_solution.py) <br>LC 77 · Medium | Combinations | An increasing start index separates *which* elements from *what order*: loop `range(start, n + 1)` and recurse with `i + 1`. **Trap:** `range(1, n + 1)` (every combination reappears in every ordering); appending the path itself. |
| [007 · Combination Sum](PyDSA/09_recursion_backtracking/007_combination_sum_solution.py) <br>LC 39 · Medium | Combination Sum (reuse) | 006 with one character changed — recurse with `i`, not `i + 1`, so an element may be reused. **Trap:** `i + 1` (silently forbids reuse: `[2,2,3]` vanishes); a `start` that never advances (every *ordering* of every combination). |
| [008 · Combination Sum II](PyDSA/09_recursion_backtracking/008_combination_sum_ii_solution.py) <br>LC 40 · Medium | Combination Sum II | Two changes from 007, and both are required: back to `i + 1` (each element once) **and** the sibling skip for duplicate values. **Trap:** keeping `i`; dropping the skip (4 correct answers become 6, with 2 duplicates). |
| [009 · Combination Sum III](PyDSA/09_recursion_backtracking/009_combination_sum_iii_solution.py) <br>LC 216 · Medium | Combinations + two constraints | 006 over `1..9` where the leaf must satisfy *both* length `k` and sum `n`. **Trap:** testing only the sum (also emits `[9]` and `[4, 5]` for `k = 3`) or only the length (every `k`-subset). |
| [010 · Letter Combinations of a Phone Number](PyDSA/09_recursion_backtracking/010_letter_combinations_of_a_phone_number_solution.py) <br>LC 17 · Medium | The pool changes with depth | The first problem where the legal choices at depth `i` are the letters of `digits[i]`, not one shared pool. **Trap:** returning `[""]` for empty input — no digits means no combinations, so the answer is `[]`. |
| [011 · Palindrome Partitioning](PyDSA/09_recursion_backtracking/011_palindrome_partitioning_solution.py) <br>LC 131 · Medium | Combinations shape over a string | `start` marks the unpartitioned suffix; try each `end` where `s[start:end+1]` is a palindrome. Precomputing a palindrome table makes each test O(1). **Trap:** the slice bound (`end + 1`); re-checking palindromes by hand at every node. |
| [012 · Word Search](PyDSA/09_recursion_backtracking/012_word_search_solution.py) <br>LC 79 · Medium | Grid: mark, recurse, unmark | Mutate the board in place to mark visited, then **unmark on every return path**. **Trap:** leaving cells marked when a branch fails (poisons later branches); an incorrect bounds check. |
| [013 · N-Queens](PyDSA/09_recursion_backtracking/013_n_queens_solution.py) <br>LC 51 · Hard | Constraint satisfaction | One queen per row; reject a placement *before* recursing, with sets for columns and both diagonals (`r - c`, `r + c`). **Trap:** generating full boards and filtering afterwards; forgetting to remove from the sets when backtracking. |
| [014 · Sudoku Solver](PyDSA/09_recursion_backtracking/014_sudoku_solver_solution.py) <br>LC 37 · Hard | CSP + cascade return | Find an empty cell, try `1..9` against its row, column and box; return `True` up the whole stack as soon as the board fills. **Trap:** the box index `(r // 3) * 3 + c // 3`; forgetting the cascade return (keeps searching after success). |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] I can write choose / explore / unchoose from memory, and I can say in one
      sentence why the unchoose step is necessary (shared mutable state, not a
      copy per call).
- [ ] I can name, for any of the three base shapes, exactly what `choices_at()`
      returns and why — without looking it up.
- [ ] I can explain why `i > start` (not `i > 0`) is the correct guard for
      duplicate-sibling skipping, and why it does not forbid using the same
      value at different depths.
- [ ] I know the grid-backtracking bug (forgetting to unmark) produces silent
      false negatives, not a crash, and I can construct an input that exposes it.
- [ ] I can state why pruning BEFORE recursing (not after generating a full
      candidate) is what makes N-Queens/Sudoku tractable, with the raw-vs-pruned
      search space numbers to back it up.
- [ ] I never `results.append(path)` — always `path[:]` or `list(path)` — and I
      can explain exactly what breaks if I forget (§8).
- [ ] I can distinguish "overlapping subproseblems -> DP" from "disjoint paths in
      a decision tree -> backtracking" using Fibonacci vs. Subsets as the two
      reference points.
- [ ] Say what a `break` on sorted candidates saves (loop iterations) and what it does *not* (recursive calls) <!--ca-->
- [ ] Bound a combinations loop by what is still needed, and quote the measured effect <!--ca-->
- [ ] Write N-Queens with bitmasks, and explain the most-constrained-cell heuristic for Sudoku <!--ca-->
- [ ] Precompute a palindrome table for Palindrome Partitioning, and say why the output is still exponential <!--ca-->
- [ ] Say when backtracking becomes DP (repeated state + a count or yes/no question) <!--ca-->
