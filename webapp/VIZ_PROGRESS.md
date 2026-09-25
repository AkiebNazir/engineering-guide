# Visualization coverage — progress tracker

Read this before touching `webapp/static/dsa-viz*.js`. Regenerate the numbers below with
`node <scratch>/gap_report.js` (recreate from this file's "How to regenerate" section if the
scratch copy is gone) any time you're not sure they're current — do not trust stale digits.

## What "exact" means

Each DSA problem's solution page shows a "Watch it run" animation if a `defineAlgo`/
`defineAlgoDom` spec's `title` (in any `webapp/static/dsa-viz*.js` file) normalizes
(lowercase, strip non-alphanumerics) to match the problem's LeetCode title exactly, OR the
problem's id is listed against some spec's title in `SOLUTION_ALGO_FOR` in
`webapp/static/solution-gate.js`. Without either, the problem falls back to its topic's
generic "Pattern animation" — present, but not problem-specific. **New work should just use
the exact LeetCode title as `title:`** so it auto-matches without touching solution-gate.js.

## Coverage as of 2026-09-23: 345/345 — DONE

Every DSA problem now has an exact, problem-specific "Watch it run" animation (not a generic
topic fallback). This session went from 157/345 missing to 0/345 missing across 13 topics (12
Heap, 13 Trie, 10 Trees, 11 <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>, 14 Graphs, 15 Advanced Graphs, 26 Segment Tree & Fenwick, 05
Binary Search, 16 <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> 1D, 23 String Algorithms, 24 Matrix, 25 Design, 28 Recursion Mastery); 27
Classic Algorithms turned out to already be done pre-session (see correction note near the
bottom of this file). Re-run the gap report (below) before starting any NEW visualization work
to confirm this is still true — it's a point-in-time snapshot, not a guarantee against future
regressions.

| Topic | Exact / Total | Status |
|---|---:|---|
| 01 Arrays & Hashing | 14/14 | done |
| 02 Two Pointers | 11/11 | done |
| 03 Sliding Window | 15/15 | done |
| 04 Prefix Sum | 8/8 | done |
| 05 Binary Search | 12/12 | done — `dsa-viz23.js` |
| 06 Stack | 14/14 | done |
| 07 Queue & Deque | 6/6 | done |
| 08 Linked List | 15/15 | done |
| 09 Recursion & Backtracking | 14/14 | done |
| 10 Binary Trees | 20/20 | done — `dsa-viz18.js` |
| 11 Binary Search Tree | 11/11 | done — `dsa-viz19.js` |
| 12 Heap / Priority Queue | 12/12 | done — `dsa-viz16.js` |
| 13 Trie | 7/7 | done — `dsa-viz17.js` |
| 14 Graphs | 18/18 | done — `dsa-viz20.js` |
| 15 Advanced Graphs | 15/15 | done — `dsa-viz21.js` |
| 16 <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> (1D) | 17/17 | done — `dsa-viz24.js` |
| 17 <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> (2D) | 18/18 | done |
| 18 Greedy | 10/10 | done |
| 19 Intervals | 11/11 | done |
| 20 Bit Manipulation | 10/10 | done |
| 21 Math & Geometry | 10/10 | done |
| 22 Sorting Algorithms | 8/8 | done |
| 23 String Algorithms | 8/8 | done — `dsa-viz25.js` |
| 24 Matrix | 8/8 | done — `dsa-viz26.js` |
| 25 Design | 13/13 | done — `dsa-viz27.js` |
| 26 Segment Tree & Fenwick | 6/6 | done — `dsa-viz22.js` |
| 27 Classic Algorithms | 9/9 | done — `viz-algorithms.js` (see correction note below) |
| 28 Recursion Mastery | 25/25 | done — `dsa-viz28.js`, `dsa-viz29.js` |

## Planned order of attack

1. ~~12 Heap / Priority Queue (12)~~ — **done**, `webapp/static/dsa-viz16.js`
2. ~~13 Trie (6 remaining)~~ — **done**, `webapp/static/dsa-viz17.js`
3. ~~10 Binary Trees (16)~~ — **done**, `webapp/static/dsa-viz18.js`
4. ~~11 Binary Search Tree (9)~~ — **done**, `webapp/static/dsa-viz19.js`
5. ~~14 Graphs (15)~~ — **done**, `webapp/static/dsa-viz20.js`
6. ~~15 Advanced Graphs (13)~~ — **done**, `webapp/static/dsa-viz21.js`
7. ~~26 Segment Tree & Fenwick (5)~~ — **done**, `webapp/static/dsa-viz22.js`
8. ~~05 Binary Search (8 remaining)~~ — **done**, `webapp/static/dsa-viz23.js`
9. ~~16 <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> 1D (14)~~ — **done**, `webapp/static/dsa-viz24.js`
10. ~~23 String Algorithms (7)~~ — **done**, `webapp/static/dsa-viz25.js`
11. ~~24 Matrix (7)~~ — **done**, `webapp/static/dsa-viz26.js`
12. ~~25 Design (13)~~ — **done**, `webapp/static/dsa-viz27.js`
13. ~~28 Recursion Mastery (25)~~ — **done**, `webapp/static/dsa-viz28.js` (groups 1-2: math/
    array/linked-list recursion) + `webapp/static/dsa-viz29.js` (groups 3-5: tree recursion,
    hard backtracking)

**All 14 topics done. Full coverage: 345/345.**

(27 Classic Algorithms was removed from this list — see correction note below, it was
already fully done before this session's work started.)

Next free viz file number: `dsa-viz30.js`.

**Note on topic 28 (Recursion Mastery, `dsa-viz28.js` + `dsa-viz29.js`) — the closing batch,
full coverage reached (345/345):** split into two files by shape. `dsa-viz28.js` (DOM engine)
covers the 11 problems that are math/array/linked-list recursion (001, 002, 003, 004, 005, 006,
007, 008, 009, 010, 016) using a new shared helper, a generic **call-stack tracer**
(`mkTracer(seq, ctx)` — `.call(label, arg)`/`.ret(val)`/`.pop()`/`.snap(...)` — and
`stackFrameHTML(stack)`/`stackPanelHTML(s)`), since showing the literal call stack growing then
shrinking is the single most on-topic visual for a topic that's explicitly about recursion
itself. Also added `llNodesHTML`/`llPanelHTML` for the linked-list ones (007, 008, 010) — a
thinner version of the array-node chain already used everywhere else, with a `→`/`null`
arrow-index instead of a plain index. `dsa-viz29.js` (canvas engine, reusing
`avTreeFromLevel`/`avLayoutBinary`/`avDrawBinary`/`avDrawBinaryIn` as-is) covers the 10
tree-recursion problems (011, 012, 013, 014, 015, 017, 018, 019, 021, 025) plus one DOM-engine
array/range problem (020, not tree-shaped — reuses the group-1/2 call-stack tracer instead) and
3 hard string-backtracking problems (022, 023, 024, DOM engine, also reusing the call-stack
tracer). New canvas helper: `avDrawForest(ctx, c, P, trees, {curIdx})`, for problems whose
answer is a LIST of trees (012 Unique <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> II, 015 All Possible Full Binary Trees) — lays out up
to 5 completed trees as side-by-side thumbnails via `avDrawBinaryIn`, growing as the recursion
completes each one. 011 (Unique <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> count) and the pre-existing "Recursion tree vs
memoisation" fib spec share the same memoized-call-tree-with-memo-table shape; 011's draw
function was modeled directly on that existing spec rather than invented fresh.
**One real algorithmic bug found and fixed** (caught only by cross-checking against an
independent from-scratch re-implementation of the real Python solution's exact split logic, not
just "does it run" — see the <abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr> Cache lesson noted under topic 25 above, which applied again
here): Split <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>'s "node.val > target" branch attached the wrong half of the recursive result to
the reconstructed node's left child — `greater[0].left` was set from `smallerSub` instead of
`greaterSub` (a copy-paste-style variable mix-up from writing the symmetric branch first).
Symptom: for input `4,2,6,1,3,5,7` split at target `2`, the "greater" (>2) result tree
incorrectly included values `1` and `2` alongside the correct `3,4,5,6,7` — plausible-looking,
wrong. Fixed by swapping to `greaterSub`; re-verified afterward that `smaller = {1,2}` and
`greater = {3,4,5,6,7}` exactly, matching a hand-traced walk of the real Python `_split` method.
**Lesson reinforced again: for any spec with two symmetric recursive branches (this pattern
recurs in binary-search-style "which half" code), write out which named variable goes into which
slot explicitly and check it against a manual trace of the real algorithm — the two branches
looking almost identical is exactly what makes a swapped variable easy to write and easy to miss
on a read-through.** All other new specs in this closing batch were cross-checked against
independent from-scratch computations of their default inputs and matched: Unique <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> count(5) =
42 (Catalan number), Unique <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> II / All Possible Full Binary Trees both produced exactly 5
completed trees for their n=3 / n=7 inputs (Catalan(3) = 5 either way), Sum Root to Leaf Numbers
= 1026 (traced by hand against `avTreeFromLevel`'s actual <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> child-assignment order — an easy
place to get the tree shape wrong when eyeballing a level-order list), House Robber III = 9,
Distribute Coins = 2 moves, <abbr title="Lowest Common Ancestor. In a tree or directed acyclic graph, the lowest node that has both given nodes as descendants.">LCA</abbr> of Deepest Leaves = node value 2, Binary Tree Cameras = 1,
Special Binary String("11011000") = "11100100", Scramble String("great","rgeat") = true,
Expression Add Operators("123", 6) = {"1+2+3","1*2*3"}, Minimum Cost Tree From Leaf
Values([6,2,4]) = 32. Frame counts for the enumeration-heavy problems (Unique <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>/<abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> II, All
Possible Full Binary Trees, memoized-fib) run 42-73 — higher than most other specs in this
codebase but not runaway, and inherent to the problem (they enumerate a genuinely
combinatorial number of cases even for tiny n); every other spec in this batch stayed in the
usual 7-24 frame range.

**Note on topic 25 (Design, `dsa-viz27.js`):** all 13 done as `defineAlgoDom`, using the
operation-sequence input pattern established by Design Twitter/<abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> Iterator/Time Based
Key-Value Store — every problem here is a stateful class, so the animation shows its real
internal data structure across a sequence of calls. New shared helper: `dllChainHTML(items,
{label, cls, headTag, tailTag})`, a generalization of the <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> cache spec's dummy-head/dummy-tail
doubly-linked-chain rendering (used by Design Linked List; <abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr> Cache uses per-frequency chains
built from the same box style directly). `hqPush`/`hqClone`/`heapTreeHTML` from `dsa-viz16.js`
were reused as-is for Stock Price Fluctuation's twin lazy-deletion heaps — no new heap code
needed, it's the exact same `heapq` usage pattern.
One real algorithmic bug found and fixed **before** this file was ever committed (caught by
cross-checking <abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr> Cache's classic LeetCode example against a from-scratch Python simulation of
the real solution, not just "does it run"): the first draft tracked each key's frequency in a
plain `Map<key, freq>` and reconstructed per-frequency buckets by filtering that map's iteration
order — but `Map.set()` on an *existing* key does not move it in iteration order, so this could
never correctly reflect "most/least recently bumped within a frequency," which is exactly what
<abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr>'s tie-breaking needs. Symptom: wrong eviction choice, silently returning the wrong `get()`
value two calls later (`[1,-1,3,1,-1,4]` instead of the correct `[1,-1,3,-1,3,4]` on the
canonical cap=2 example) — a bug that `node --check` and a "does it throw" execution check both
miss completely, since it produces a plausible-looking wrong answer, not a crash. Fixed by
maintaining explicit `Map<freq, Array<key>>` buckets with real `unshift`/`splice`/`pop`
(front = MRU, back = <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr>), mirroring the real solution's `_DLList.push_front`/`pop_back`
exactly. **Lesson for topic 28 (Recursion Mastery) and any future stateful-class or
multi-structure spec: execution-without-error is not enough verification for anything with
non-trivial internal state ordering — hand-trace or independently re-simulate the real
algorithm (e.g. run the actual Python solution, or a from-scratch port) on the example input
and diff every intermediate return value, not just the last one.** Stock Price Fluctuation and
Snapshot Array were also cross-checked this way (hand-traced against the real solution's
exact heap/bisect behavior) and were correct as first written.

**Note on topic 24 (Matrix, `dsa-viz26.js`):** all 7 done as canvas-engine `defineAlgo` specs
(matching the existing "Spiral order: four shrinking walls" spec already in this topic), using
`avDrawGrid`/`avParts`/`avNum` from `dsa-viz.js`/`dsa-viz2.js`. Added one small new helper,
`mtxDrawGridIn(ctx, P, c, leftX, widthPx, grid, style, opts)`, for drawing two grids side by
side in one canvas (used by Transpose Matrix to show source + result) — a thinner version of
topic 10's `avDrawBinaryIn` two-tree trick, same idea applied to plain grids instead of trees.
Rotate Image and Game of Life final answers were cross-checked against known-correct results
(rotate([[1,2,3],[4,5,6],[7,8,9]]) and the classic LC289 example) and matched exactly. The
existing "Spiral order" spec was checked for the `renderDOM`-without-`type:'dom'` bug class
found in three earlier batches (Advanced Graphs, <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> 1D) — not present here, it's a pure canvas
spec with no `renderDOM`/`type` mismatch.

**Note on topic 23 (String Algorithms, `dsa-viz25.js`):** all 7 done as `defineAlgoDom` (DOM
engine), not canvas — even the 3 that reuse the <abbr title="Knuth-Morris-Pratt. A string-searching algorithm that searches for occurrences of a word within a main text string in optimal time.">KMP</abbr> failure-function trick (Repeated Substring
Pattern, Shortest Palindrome share a new local helper `saBuildLpsTraced(pat, emit)`; Longest
Duplicate Substring is unrelated, binary-search-on-length + Rabin-Karp). This differs from the
pre-existing "<abbr title="Knuth-Morris-Pratt. A string-searching algorithm that searches for occurrences of a word within a main text string in optimal time.">KMP</abbr>: never re-read the text" spec (seq 001, canvas engine, `dsa-viz3.js`) — both
engines can show the same failure-table concept equally well; picked DOM here for consistency
with this file's other 4 specs and to reuse `dpBox`/`dpStrip`/`dpPanel`/`dpWrap` (`dsa-viz24.js`)
and `chipRow` (`dsa-viz16.js`) directly rather than the canvas `AV.row`/`AV.ptr` primitives.
Added `saCharStrip`/`saCharBox`/`saPtrHTML` (small character-array wrappers around the same
`array-node`/`node-index`/`pointer` classes) — reuse these for any future character-by-character
string visualization instead of rewriting per-char box markup again.
Matched each spec to what the *real* solution does, which varies: Longest Duplicate Substring
uses binary search on the answer's length + Rabin-Karp rolling hash with mandatory
direct-comparison verification on every hash hit (the animation keys its `seen` map by the raw
substring rather than a numeric hash, for teaching clarity — the collision/verify shape taught
is identical either way, noted in a code comment); Repeated DNA Sequences uses two hash sets
("seen"/"repeated") over a sliding 10-window; Palindrome Pairs enumerates every split point of
every word with the two symmetric prefix/suffix-palindrome cases from the real solution, not a
simplified single-case version. All 7 outputs cross-checked against known-correct answers on
their default inputs (e.g. `shortestPalindrome("aacecaaa") == "aaacecaaa"`,
`longestDupSubstring("banana") == "ana"`, `repeatedStringMatch("abcd","cdabcdab") == 3`) — not
just "it runs without throwing."
No `renderDOM`-without-`type:'dom'` bug found in the topic's 1 pre-existing spec (already
correctly typed as canvas with `run`/`draw`, no mismatch).

**Note on topic 16 (<abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> 1D, `dsa-viz24.js`):** plain DOM-engine array-strip visualizations
throughout (no new shared helper file needed beyond this file's own local `dpBox`/`dpStrip`/
`dpPanel`/`dpWrap`, a small generalization of the existing array-node/node-index pattern) —
1D <abbr title="Dynamic Programming. A method for solving complex problems by breaking them down into simpler overlapping subproblems and storing the results.">DP</abbr> rarely needs anything more than an array/table strip with the current cell and its
recurrence-dependency cells highlighted. Matched each spec to what the *real* solution
actually does, which varies more than the topic name suggests: Longest Palindromic Substring
and Palindromic Substrings both use expand-around-center (not a 2D dp table); Longest
Increasing Subsequence and Russian Doll Envelopes both use the O(n log n) patience-sorting
`tails` array with `bisect_left` (not the O(n²) `dp[i]` table — visualizing the wrong one
would teach the wrong algorithm); Partition Equal Subset Sum scans its sum axis HIGH→LOW,
which is load-bearing (low→high would silently turn 0/1 knapsack into unbounded knapsack) and
is shown as such; Combination Sum IV loops target-outer/nums-inner specifically because order
matters, the opposite nesting from Coin Change, and the visualization's `idea` text calls
this out explicitly.
**Found and fixed two more pre-existing broken specs** (same bug class as topic 15's
Network Delay Time/Number of Provinces): `webapp/static/dsa-viz.js`'s "Climbing Stairs" and
"Coin Change" (both already counted in this topic's original 3/17) defined `run()` +
`avRecorder()`/`snap()` (the canvas-engine convention) AND a `renderDOM()` method, but had no
`type` field at all — so the player's dispatch defaulted them to the canvas path, which needs
`draw()`/`height()` (neither existed), silently rendering nothing. Fixed by adding
`type: 'dom'` AND renaming `run(...)` → `buildStates(...)` with a corrected local recorder
(`const snap = (line, note, state) => F.push({ line, explTitle: '<Title>', explText: note,
...state })`) so the frame shape matches what `renderDomAlgo` actually reads
(`explTitle`/`explText`, not `note`) — adding `type: 'dom'` ALONE is not sufficient when the
spec still only has `run()`, since `renderDomAlgo` calls `spec.buildStates(parsed)`
unconditionally; verified both by executing `parse→buildStates→renderDOM` end to end, not
just `node --check`. **When checking for this bug class elsewhere (topics 23, 24, 25, 28
still to do), check for THREE things together: (1) `type: 'dom'` present, (2) `buildStates`
present (not just `run`), (3) if `run`/`snap` is what exists, the frame shape needs
`explTitle`/`explText` fields, not `note` — a spec can fail on any one of these independently.**

**Note on topic 05 (Binary Search, `dsa-viz23.js`):** no new shared helper needed — reused
`ggGridHTML`/`ggPanel` (from `dsa-viz20.js`) for the 2D-matrix-as-flat-array problem and
`chipRow` (from `dsa-viz16.js`) for the per-candidate feasibility breakdowns, plus one small
new local helper in this file, `bsArrayHTML(arr, style)` / `bsPointerHTML(label, color)`, a
generalization of the existing "Binary Search" spec's inline array-box+pointer rendering —
reuse it for any future array-with-l/r/mid-pointers visualization instead of rewriting that
box markup again. Three problems (Koko Eating Bananas, Capacity To Ship Packages, Split Array
Largest Sum) share the exact same "binary search on the answer" shape (candidate value → a
greedy feasibility check → monotonic hi=mid/lo=mid+1) and are visualized identically in
structure, only the feasibility check's rendering differs (per-pile hours vs. day-groups vs.
piece-groups). Median of Two Sorted Arrays partitions rather than searches a value — pointers
mark a *cut* position on each of two arrays, not a shrinking [l,r] range. Checked the topic's
4 pre-existing specs (Binary Search, Search Insert Position, First Bad Version, Guess Number
Higher or Lower) for the `renderDOM`-without-`type:'dom'` bug class found in earlier batches —
none had it, all correctly typed. (Also noticed, but left alone as out of scope: each of those
4 titles has a harmless duplicate spec in both `dsa-viz-dom.js` and `dsa-viz4.js` — not a bug,
just dead/unreachable redundancy, since `solutionAlgosFor` only ever uses the first title match
it finds.)

**Note on topic 26 (Segment Tree & Fenwick, `dsa-viz22.js`):** no single shared rendering
approach fit all 5 — this topic's problems are genuinely different shapes, so it used three
different reuse paths: (1) "Range Sum Query 2D - Mutable" (a 2D BIT, not tree-shaped at all)
reuses `ggGridHTML`/`ggPanel`/`agParseIntGrid` from topics 14/15 to show the matrix and the
BIT array as two grids, with the `i += i & -i` / `j += j & -j` walk highlighted cell by cell.
(2) "Reverse Pairs" and "Count of Range Sum" are plain DOM array-track visualizations (same
`array-node`/`node-index`/`pointer` style as topics 1-9), showing the merge-sort recursion's
current [lo,hi] range, the counting two-pointer(s), and the merge — no new helper needed.
(3) "Falling Squares" reuses the exact segment-tree layout/draw shape from the pre-existing
001 spec in `dsa-viz3.js` (1-indexed keys, level computed via `floor(log2(key))`) even though
the real Python solution is 0-indexed internally — the visualization renumbers tree node keys
to 1-indexed purely for layout purposes, since the recursive splitting shape is identical
either way; **this is a reusable trick for any future 0-indexed segment/BIT tree** — don't
build a second layout system for 0-indexed trees, just relabel keys as `realNode + 1` (or
similar) when constructing the `ranges`/`tree` state objects passed to `snap()`/`draw()`.
(4) "The Skyline Problem" is sweep-line + heap, not tree-shaped — new canvas code using
`D.view()` for world-to-pixel mapping (buildings as translucent rects, a moving sweep line,
the live max-heap as a sorted array shown as text, and the growing skyline as a step
polyline). One real bug caught only by executing every spec (not just `node --check`): the
recursive `query`/`update` snap calls in Falling Squares used a local `S(extra)` state-builder
that didn't include `result`/`running` by default, so any frame from *inside* the recursion
(as opposed to the outer per-square loop) had `f.result === undefined`, and `draw()` crashed
on `f.result.join(...)`. Fixed by giving `S()` sane defaults for every field `draw()` reads,
not just the ones the outermost call site happens to pass. **Any spec whose `draw()`/
`renderDOM()` reads a field that isn't set on literally every `snap()`/`domPushState()` call
site has this same class of bug — give the state-builder helper full defaults, don't rely on
every call site remembering every field.**

**Note on topic 15 (Advanced Graphs, `dsa-viz21.js`):** used the DOM engine throughout
(`defineAlgoDom`), reusing `ggGridHTML`/`ggGraphSVG`/`ggPanel` from `dsa-viz20.js` plus one
new helper in this file, `agParseIntGrid(s, {max})` (rows separated by `;`, cells by `,` —
distinct from `ggParseGrid`'s single-digit-string-per-row format, needed here because
elevations/heights are multi-digit integers). Also added `agChip`/`agChips` for small
label/value pill rows (heap contents, dist arrays, stack contents, etc.) — reuse both for
topic 26 (Segment Tree & Fenwick), which will want similar array/pill displays.
**Found and fixed two real, pre-existing (not introduced this session) broken visualizations**
while working this topic: `webapp/static/dsa-viz.js`'s "Network Delay Time" and "Number of
Provinces" specs (the two problems this topic's coverage count already included before this
batch) defined `renderDOM` but were missing `type: 'dom'`, so the player's dispatch logic
(`renderAlgoTab`, which branches on `spec.type === 'dom'`) treated them as canvas specs and
called the nonexistent `spec.draw`, silently failing inside a try/catch — **the canvas
rendered nothing at all**, though the code panel and controls still appeared, so it looked
"almost working." Fixed by adding `type: 'dom'` to both, plus a `buildStates(parsed) {
return this.run(parsed).map(f => ({ ...f, explTitle, explText: f.note })); }` adapter, since
both specs generate frames with `run()`/`snap()` (the canvas-engine convention, `{line, note,
...state}`) rather than `buildStates()`/`domPushState()` (the DOM-engine convention, which
also expects `explTitle`/`explText`/`pause` fields) — confirmed via a from-scratch execution
test that both now produce real HTML through `renderDOM`. **If you find another spec with
`renderDOM` defined but no `type: 'dom'`, or `type: 'dom'` set but only a `run()` method and
no `buildStates()`, it has this exact same bug — check for both mismatches, not just one.**
Also: for `run`/`snap`-style state generation, `avRecorder()`'s frames are `{line, note,
...state}` via `structuredClone` — plain data only, no functions/Sets/Maps in the state
object passed to `snap()`, unlike `domPushState` frames which just push the object as-is
(a `Set`/`Map` in DOM-engine state is fine, e.g. this batch's Alien Dictionary uses `Set`
adjacency lists directly in state).

**Note on topic 14 (Graphs, `dsa-viz20.js`):** added two new small reusable DOM-engine
helpers at the top of that file — `ggGridHTML(grid, cellFn)` (generic box grid, cellFn
returns `{content, bg, border, color, opacity, extra}` per cell) and `ggGraphSVG(n, edges,
nodeFn, edgeFn)` (small node-link graph on a circle layout, drawn with inline SVG — nodeFn/
edgeFn return `{fill, stroke, color, label}`/`{stroke, width}`). Plus `ggPanel(title, body)`
and `ggParseGrid(s, {max})` for the common "comma-separated equal-length digit rows" input
format. These cover every grid- and graph-shaped DOM problem — reuse them for topic 15
(Advanced Graphs) rather than rebuilding grid/graph rendering again. One real bug this batch
caught only by actually executing every spec (not just `node --check`): a <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>-by-level
problem (Open the Lock) that snapshots one state per node popped can produce 800+ frames on
a plausible input, since the frontier grows multiplicatively — fixed by snapshotting once per
<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> *level* instead of once per popped node. **Apply the same per-level (not per-node)
snapshotting rule to any <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/multi-source-<abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> spec in topic 15 or 26** where the frontier
could grow large, or run the same "execute every spec, check the frame count is sane" check
this batch used.

**Note on topic 11 (<abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>, `dsa-viz19.js`):** reused `avTreeFromLevel`/`avLayoutBinary`/
`avDrawBinary`/`avParts`/`avNums`/`avNum` as-is, no new helpers needed — <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> problems are
plain binary trees, the only difference is the ordering invariant driving the algorithm.
One real bug caught only by actually executing `draw()` per frame (not just `node --check`):
"Convert Sorted Array to <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>" grows the tree from nothing, so its first frame(s) have an
empty `nodes` array — calling `avLayoutBinary`/`avDrawBinary` on an empty array crashes
(`avLayoutBinary` defaults to `root=0` and dereferences `nodes[0]` unconditionally). Fixed by
guarding `draw()` with `if (f.nodes.length) { ... } else { draw an "(empty so far)" placeholder }`.
**Any spec that builds a tree up from nothing (rather than starting from a full `avTreeFromLevel`
parse) needs this same empty-array guard** — check for it in topics 14/15/26 if any sub-step
builds a structure incrementally.

**Note on `charTrieDraw` (added in `dsa-viz17.js`):** a reusable canvas-engine helper
(`charTrieLayout`/`charTrieHeightFromFrames`/`charTrieDraw`) that lays out any trie-shaped
`nodes: [{ch, kids:{label->id}, ...}]` array as an actual tree, with an optional `subLabel`
(per-node annotation, e.g. a running value) and `region` (so two of these — or one of these
plus a grid — can share one canvas, as `006 Word Search II` does). It works for a binary bit
-trie too (`005 Maximum XOR`) since kids are just keyed `'0'`/`'1'` instead of letters —
reuse it for anything trie-shaped rather than rewriting the layout math again.

**Note on binary-tree drawing (topic 10, `dsa-viz18.js`):** the general single-binary-tree
layout/draw helpers already existed in `dsa-viz.js` before this batch — `avTreeFromLevel(str)`
(parses level-order input like `"3, 9, 20, null, null, 15, 7"` into a flat `nodes:
[{val,left,right}]` array, `-1` for a missing child, root always index 0), `avLayoutBinary
(nodes, root=0)` (returns `{pos, count, depth}`), and `avDrawBinary(ctx, P, c, nodes, lay,
style, opts)` (draws edges + `AV.node` circles, `style(id)` returns `{fill, stroke, sub,
edge, label, hidden}`) — no need to build a new one, just call these. `dsa-viz18.js` adds one
small addition, `avDrawBinaryIn(ctx, P, region, nodes, lay, style, opts)`, which translates
the canvas and calls `avDrawBinary` with a narrower fake `c.w` so two trees can sit side by
side in one canvas (used for Same Tree, Subtree of Another Tree, Serialize/Deserialize) —
reuse this for topic 11 (<abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>) if any of its 9 need two trees at once, and generally prefer
`avTreeFromLevel`/`avLayoutBinary`/`avDrawBinary`/`avDrawBinaryIn` over `charTrieLayout`/
`charTrieDraw` for anything that's a plain binary tree (not char/bit-keyed like a trie).

## Two rendering engines already in the codebase — reuse, don't reinvent

- **DOM engine** (`defineAlgoDom`, files `dsa-viz-dom.js`, `dsa-viz4.js`–`dsa-viz15.js`):
  boxes/arrays/stacks/lists via HTML. Pattern: `type: 'dom'`, `parse(input)` → data,
  `buildStates(data)` → array of frames built with `domPushState(seq, {...fields, line,
  color, explTitle, explText, pause?}, ctx)`, `renderDOM(container, s, spec)` → sets
  `container.innerHTML` to ONLY the canvas markup (glass-panel/array-track/array-node/
  node-index/pointer classes already in `dsa-viz.css`) — **no code panel, no explanation
  block inside renderDOM**; the shared player (`renderAlgoTab` in `dsa-viz.js`) renders the
  code panel from `spec.code` + `s.line`/`s.color`, and the explanation strip from
  `s.explTitle`/`s.explText`, once, itself. (A prior session's `fix-viz.js` — since deleted —
  fixed this exact duplication; if you see a per-frame code-panel or `.viz-expl` block inside
  a `renderDOM`, that's leftover duplication, not a new bug to reintroduce.)
- **Canvas node-link engine** (`defineAlgo`, files `dsa-viz.js`, `dsa-viz2.js`, `dsa-viz3.js`,
  `dsa-viz6.js`): trees/graphs/tries via `run({...}) → { F, snap }` from `avRecorder()`,
  `height(w, last, frames)`, `draw(ctx, c, f, P)` using `AV.node`, `D.line`, `D.text`, `P.*`
  palette. See `13_trie` in `dsa-viz2.js:62` for the full pattern (insert/search a trie drawn
  as an actual tree) — use this engine, not the DOM one, for anything tree- or graph-shaped
  (10, 11, 12-as-tree, 13, 14, 15, 26).

Both engines are registered into the same global `ALGOS[topicId]` array via `defineAlgo`/
`defineAlgoDom`, and both are driven by the one shared player in `dsa-viz.js`.

**Update from doing topic 12 (Heap):** the DOM engine turned out fine for tree-shaped data
too — `dsa-viz16.js` adds file-level shared helpers (`heapTreeHTML`, `heapNodePositions`,
`heapArrayStripHTML`, `chipRow`) that lay a heap array out as an actual binary tree (SVG
lines + absolutely-positioned circular `array-node` divs) inside the DOM engine, no canvas
needed. It also ports CPython's real `heapq` sift algorithm to JS (`hqPush`/`hqPop`/
`hqReplace`/`hqPushPop`/`hqify` in that file) so every heap snapshot shown is the exact array
layout the real Python `heapq` module would produce, not an approximation — reuse these
instead of re-deriving heap mechanics for topics 26 (segment tree, different structure) or
anywhere else a heap shows up as a sub-step. For topics 10/11/14/15 (trees/graphs proper,
with many-node structures and traversal-order layout needs), the canvas engine is still
likely the better fit — decide per-topic, don't assume DOM-with-SVG is always right just
because it worked for heaps.

## Verification checklist per problem/topic before marking done

1. `title:` matches the LeetCode title in `tools/problems.tsv` exactly (case as given there).
2. `node --check webapp/static/<file>.js` passes.
3. Re-run the gap report (see below) and confirm the topic's exact count increased by the
   number of problems you added.
4. Add the new `<script src="/dsa-vizNN.js"></script>` tag to `webapp/static/index.html`
   anywhere after `dsa-viz-dom.js` (DOM engine specs need `defineAlgoDom` already defined)
   or after `dsa-viz.js` (canvas engine specs need `defineAlgo`/`AV`/`D`/`P` already defined).
5. Never re-run old one-off migration scripts found lying around the repo without reading
   them fully first — one already caused real damage this session (see git history / ask the
   user) before being deleted.

## How to regenerate the gap report

```js
// Loads every webapp/static/dsa-viz*.js in real <script> order (order matters — dsa-viz.js
// declares ALGOS/defineAlgo/avNums etc. as top-level const, later files rely on it existing
// already), then diffs registered titles against tools/problems.tsv per topic.
// 1) collect titles: concatenate all dsa-viz*.js (in index.html's script order) into one
//    string, eval it once (so top-level const declarations are shared like real <script>
//    tags), then read the ALGOS object it built.
// 2) cross-reference tools/problems.tsv rows against those titles (normalized: lowercase,
//    strip non-alphanumerics) and SOLUTION_ALGO_FOR from solution-gate.js.
// Ask Claude to recreate this if the scratchpad copy is gone — it's about 40 lines, built
// once already this session.
```

**CORRECTION (found while doing topic 11/<abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr>):** the very first gap report built this
session missed `webapp/static/viz-algorithms.js` — a pre-existing, unrelated-looking file
(not named `dsa-viz*`) that fully implements all 9 problems of topic `27_algorithms` via
`defineAlgoDom(ALGOS_ALGORITHMS, ...)` where `const ALGOS_ALGORITHMS = '27_algorithms'`. It
predates this whole session (file mtime 20 Sep) — topic 27 was never actually missing
anything; it was a false gap caused by the gap-report script's file-discovery regex only
matching `<script src="/dsa-viz...">` tags. **When regenerating the gap report, collect
`<script src="/...">` tags more broadly and eval every file that calls `defineAlgo`/
`defineAlgoDom` (grep the candidate file for that string first), not just files matching
`dsa-viz*`.** Checked the other non-`dsa-viz*` script tags in `index.html`
(`viz.js`, `viz-ml.js`, `viz-llm.js`, `viz-csfund.js`, `viz-sd*.js`, `sd-flow.js`,
`viz-api*.js`, `roadmap.js`) — none of those besides `viz-algorithms.js` define any
`defineAlgo`/`defineAlgoDom` calls, so this was the only miscount. `viz.js` (loaded before
`dsa-viz.js`) is a shared drawing-primitives file (`TAU`, `D.*`) with no specs of its own —
include it in the eval bundle for its side effects, but it registers nothing.
