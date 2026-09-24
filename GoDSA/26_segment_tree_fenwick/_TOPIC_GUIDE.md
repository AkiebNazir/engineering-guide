# Topic 26 · Segment Tree & Fenwick Tree — Go Deep Dive

> Topic 04 gave you O(1) range-sum queries with a prefix-sum array — as long as the
> array never changes. The moment a single element is *mutated*, that prefix array
> is entirely stale and rebuilding it costs O(n). This document is about the two
> structures that fix that: they give up a little query speed (O(log n) instead of
> O(1)) in exchange for O(log n) **updates**, which prefix sums cannot do at all.
> If your problem statement contains both "update" and "range query" in the same
> sentence, this is the topic that applies.

---

## Part 1 · The Gap This Topic Fills

### 1.1 Why the prefix sum from Topic 04 isn't enough

```
prefix[i] = prefix[i-1] + nums[i-1]      // O(n) to build, O(1) to query a range

nums[3] = 99   // one write...
// ...and now prefix[4], prefix[5], ..., prefix[n] are ALL stale.
// Fixing it means recomputing the suffix of the prefix array: O(n).
```

| Structure | Build | Point Update | Range Query | Handles non-sum ops? |
|---|:--:|:--:|:--:|:--:|
| Prefix sum array (Topic 04) | O(n) | **O(n)** | O(1) | No — sum/XOR only, and even those need a full rebuild on update |
| Fenwick Tree (BIT) | O(n log n) / O(n) | **O(log n)** | O(log n) | Only invertible ops (sum, XOR) |
| Segment Tree | O(n) | **O(log n)** | O(log n) | ✅ Any associative op: sum, min, max, gcd |

A static, never-mutated array should still just use a prefix sum — it's simpler
code and a smaller constant factor. Reach for the structures in this guide only
when the array is genuinely mutated between queries. That trade-off is the entire
reason these two structures exist.

### 1.2 Decision table

| Situation | Use |
|---|---|
| Array is static, only range-sum queries | Prefix sum (Topic 04) |
| Array is mutated, need range-sum + point-update | **Fenwick Tree** — simplest code, smallest constant |
| Array is mutated, need range-min/max/gcd + point-update | **Segment Tree** — Fenwick's trick doesn't work here (see 2.5) |
| Need range-update **and** range-query, not just point-update | **Segment Tree + lazy propagation** |
| Need "are these two elements connected" style queries, not numeric ranges | Union-Find (Topic 14) — different problem shape entirely |

---

## Part 2 · Fenwick Tree (Binary Indexed Tree)

### 2.1 The trick: `i & (-i)` isolates the lowest set bit

A Fenwick tree is an implicit tree hidden inside a single 1-indexed array, where
each index `i` is made "responsible for" summing a specific range of the
original array, determined entirely by the position of `i`'s lowest set bit.

Recall from Topic 20: Go integers are two's complement, so `-i` is `^i + 1`.
That means `i & (-i)` clears every bit except the lowest set one:

```go
i := 12          // binary: 1100
lsb := i & (-i)  // binary: 0100 = 4   — the lowest set bit, isolated
```

`lsb` tells you exactly how many array elements index `i` is responsible for.

### 2.2 What each index is "responsible for"

```
index (binary)   lowest set bit   responsible for nums[]
   1   (0001)          1          [1]
   2   (0010)          2          [1..2]
   3   (0011)          1          [3]
   4   (0100)          4          [1..4]
   5   (0101)          1          [5]
   6   (0110)          2          [5..6]
   7   (0111)          1          [7]
   8   (1000)          8          [1..8]
```

```
tree[8] ─────────────────────────────────► sums nums[1..8]
tree[4] ──────────────► sums nums[1..4]        tree[6] ──► sums nums[5..6]
tree[2] ──► [1..2]   tree[3]:[3]   tree[5]:[5]  tree[7]:[7]   tree[8] above
tree[1]:[1]
```

Index `6` = `0110` has lowest set bit `2`, so `tree[6]` covers `nums[5..6]` — the
2 elements ending at 6. Index `4` = `0100` has lowest set bit `4`, so `tree[4]`
covers `nums[1..4]` — the 4 elements ending at 4. This is exactly the pattern in
the diagram above.

> ⚠️ **Fenwick trees are 1-indexed by convention, not by accident.** The `i & (-i)`
> trick breaks down at index 0: `0 & (-0)` is `0`, so index 0 could never make
> progress walking up or down the implicit tree. Always allocate `tree` of size
> `n+1` and ignore index 0.

```arch
%% caption: Update at i walks UP with i += i & -i (3, 4, 8). A prefix query walks the other way with i -= i & -i (7, 6, 4). Each tree[i] covers the last (i & -i) elements ending at i.
route straight
grid 88x80
node t8 "tree[8]" at 7,0 color=blue w=72 sub="a1..a8"
node t4 "tree[4]" at 3,1 color=blue w=72 sub="a1..a4"
node t2 "tree[2]" at 1,2 color=blue w=72 sub="a1..a2"
node t6 "tree[6]" at 5,2 color=blue w=72 sub="a5..a6"
node t1 "tree[1]" at 0,3 color=blue w=72 sub="a1"
node t3 "tree[3]" at 2,3 color=blue w=72 sub="a3"
node t5 "tree[5]" at 4,3 color=blue w=72 sub="a5"
node t7 "tree[7]" at 6,3 color=blue w=72 sub="a7"
t1 -> t2
t2 -> t4
t3 -> t4
t4 -> t8
t5 -> t6
t6 -> t8
t7 -> t8
```

### 2.3 Update: walk UP by repeatedly adding the lowest set bit

```go
func (f *Fenwick) Update(i int, delta int) {
    for ; i <= f.n; i += i & (-i) {
        f.tree[i] += delta
    }
}
```

Adding `delta` at position `i` must propagate to every `tree[]` slot whose range
of responsibility includes `i` — those are found by repeatedly jumping to
`i + (i & (-i))`, climbing toward the root. This terminates in at most
`O(log n)` steps because each jump strictly increases `i`'s number of trailing
zero bits.

### 2.4 Prefix query: walk DOWN by repeatedly clearing the lowest set bit

```go
func (f *Fenwick) Query(i int) int {
    sum := 0
    for ; i > 0; i -= i & (-i) {
        sum += f.tree[i]
    }
    return sum
}
```

To sum `nums[1..i]`, you don't visit every element — you visit at most
`O(log n)` `tree[]` slots, each contributing a disjoint chunk of the range,
found by repeatedly *removing* the lowest set bit from `i` until it reaches 0.

A range sum `[l, r]` (inclusive, 1-indexed) is then just:

```go
func (f *Fenwick) RangeQuery(l, r int) int {
    return f.Query(r) - f.Query(l-1)
}
```

> ✅ This subtraction is exactly why Fenwick trees only work for **invertible**
> operations — see 2.5.

### 2.5 Why Fenwick trees can't do range-min/max

`RangeQuery(l, r) = Query(r) - Query(l-1)` relies on subtraction *undoing* the
part of `Query(r)` that overlaps `[1, l-1]`. That only works because addition
has an inverse (subtraction). `min` and `max` have **no inverse** — knowing
`min(nums[1..r])` and `min(nums[1..l-1])` tells you nothing about
`min(nums[l..r])`, because the overall minimum might have come from an index
you can't "subtract back out." This is the fundamental limitation that pushes
min/max/gcd range problems to a segment tree instead.

### 2.6 Complexity

| Operation | Complexity |
|---|:--:|
| Build (naive: n calls to `Update`) | O(n log n) |
| Build (optimized linear build, Part 7.1) | O(n) |
| Point update | **O(log n)** |
| Prefix query | **O(log n)** |
| Range query | O(log n) (two prefix queries) |
| Space | O(n) |

---

## Part 3 · Segment Tree

### 3.1 A different array-as-tree convention than Topic 12's heap

Both a binary heap (Topic 12) and a segment tree store a tree inside a flat
array, but they are **not the same idea** — a common source of confusion:

| | Binary Heap | Segment Tree |
|---|---|---|
| Node holds | A single value | An **aggregate** (sum/min/max) over an entire subrange |
| Ordering guarantee | Weak: parent ≤/≥ children only | None between siblings — only "this node summarizes its children's ranges" |
| Index convention used here | 0-indexed, children `2i+1`/`2i+2` | 1-indexed, children `2i`/`2i+1` |

This guide uses the classic **1-indexed, root at `1`** convention: node `i`
covers some range `[lo, hi]`, its left child `2i` covers `[lo, mid]`, and its
right child `2i+1` covers `[mid+1, hi]`.

```
                    tree[1]: sum[0..7]
              ┌─────────────┴─────────────┐
        tree[2]: sum[0..3]           tree[3]: sum[4..7]
        ┌──────┴──────┐              ┌──────┴──────┐
   tree[4]:[0..1] tree[5]:[2..3] tree[6]:[4..5] tree[7]:[6..7]
```

```arch
%% caption: Query [2..5] needs only the two highlighted nodes, [2..3] and [4..5]: O(log n) nodes are ever visited. Lazy propagation postpones a range update on a node until a query must look at its children.
route straight
grid 72x85
node r "[0..7]" at 4,0 shape=box color=blue w=64
node l1 "[0..3]" at 2,1 shape=box color=blue w=64
node r1 "[4..7]" at 6,1 shape=box color=blue w=64
node a "[0..1]" at 1,2 shape=box color=blue w=64
node b "[2..3]" at 3,2 shape=box color=amber w=64
node c "[4..5]" at 5,2 shape=box color=amber w=64
node d "[6..7]" at 7,2 shape=box color=blue w=64
node a0 "0" at 0,3 shape=circle color=slate
node a1 "1" at 1,3 shape=circle color=slate
node b2 "2" at 2,3 shape=circle color=slate
node b3 "3" at 3,3 shape=circle color=slate
node c4 "4" at 4,3 shape=circle color=slate
node c5 "5" at 5,3 shape=circle color=slate
node d6 "6" at 6,3 shape=circle color=slate
node d7 "7" at 7,3 shape=circle color=slate
r -> l1
r -> r1
l1 -> a
l1 -> b
r1 -> c
r1 -> d
a -> a0
a -> a1
b -> b2
b -> b3
c -> c4
c -> c5
d -> d6
d -> d7
```

### 3.2 Why the array is over-allocated to `4*n`

With root `1` and children `2i`/`2i+1`, a recursive segment tree over `n` leaves reaches node indexes up to `2^(⌈log₂ n⌉+1) − 1` — the deepest leaf sits at
depth `⌈log₂ n⌉`, and depth `d` tops out at index `2^(d+1) − 1`. Since `2^⌈log₂ n⌉ < 2n`, that is always below `4n`, which is why `4*n` is the safe allocation.
Measured by walking the recursion for every `n` from 1 to 4,096: the largest index touched never exceeded that bound and never reached `4n`. Two facts worth remembering:
**`2n` is not enough** — `n = 6` already touches index 13 — and the worst ratio in that range was 3.88, at `n = 2,080` (index 8,065). (`n = 2^k + 1` needs only about `2n`, so the
"one over a power of two" story is not the worst case.) If memory matters, allocate `2 * nextPowerOfTwo(n)`; the iterative bottom-up layout in Part 7.5 needs exactly `2n` slots.

```go
tree := make([]int, 4*n)   // ✅ safe for any n, recursive index math never overflows
```

### 3.3 Build, query, update — all recursive, all O(log n) per level

```go
func build(tree, nums []int, node, lo, hi int) {
    if lo == hi {
        tree[node] = nums[lo]
        return
    }
    mid := lo + (hi-lo)/2                 // overflow-safe midpoint (Topic 05)
    build(tree, nums, 2*node, lo, mid)
    build(tree, nums, 2*node+1, mid+1, hi)
    tree[node] = tree[2*node] + tree[2*node+1]   // aggregate = combine(children)
}
```

Query and update each visit only the `O(log n)` nodes whose ranges are needed
to cover the query range or reach the target leaf — never the full tree.

### 3.4 Lazy propagation, conceptually

Point updates above are already O(log n): change one leaf, recompute `O(log n)`
ancestors. But a **range** update (e.g. "add 5 to every element in `[3, 9]`")
naively touches every leaf in that range — O(n) worst case.

Lazy propagation fixes this by **deferring** work: when a range update fully
covers a node's range, instead of recursing all the way to that node's leaves
immediately, you apply the aggregate effect to the node itself and stash a
"pending" marker (the lazy value) saying *"this subtree still owes its children
this update."* That marker is only pushed down one level — and cleared — the
next time a query or update actually needs to descend into that subtree. Every
node ends up doing O(1) amortized deferred work instead of the update touching
every leaf, bringing range updates down to O(log n) as well.

This is the most intricate piece of machinery in this entire guide series. A
correct conceptual grasp of *why* deferring is safe (a range fully "under" a
node doesn't need to be pushed further until something needs to see inside it)
matters more here than memorizing a lazy-propagation implementation — get the
idea solid, then §3.5a is the full implementation.

### 3.5a Lazy propagation — the full implementation (range-add, range-sum)

Two arrays now, same `4*n` sizing: `tree[node]` holds the aggregate for that
node's range **as if every pending lazy value on it had already been
applied**, and `lazy[node]` holds an amount still owed to that node's
**children** (never to the node itself — the node's own `tree[node]` is
already correct).

```go
type SegTree struct {
    tree, lazy []int
    size       int
}

func NewSegTree(nums []int) *SegTree {
    n := len(nums)
    st := &SegTree{tree: make([]int, 4*n), lazy: make([]int, 4*n), size: n}
    st.build(nums, 1, 0, n-1)
    return st
}

func (st *SegTree) build(nums []int, node, lo, hi int) {
    if lo == hi {
        st.tree[node] = nums[lo]
        return
    }
    mid := lo + (hi-lo)/2
    st.build(nums, 2*node, lo, mid)
    st.build(nums, 2*node+1, mid+1, hi)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

// push applies node's pending lazy value to itself (already done at write
// time — see update) and hands a COPY of the debt down to both children,
// halving nothing: an "add v to every element" debt of v applies to EVERY
// element a child covers too, so the child's own tree[] value shifts by
// v * (child's range length), while the lazy value handed down stays v
// (a per-element amount, not a per-range total).
func (st *SegTree) push(node, lo, hi int) {
    if st.lazy[node] == 0 {
        return
    }
    mid := lo + (hi-lo)/2
    left, right := 2*node, 2*node+1
    leftLen, rightLen := mid-lo+1, hi-mid
    st.tree[left] += st.lazy[node] * leftLen
    st.tree[right] += st.lazy[node] * rightLen
    st.lazy[left] += st.lazy[node]
    st.lazy[right] += st.lazy[node]
    st.lazy[node] = 0 // fully handed off — this node owes its children nothing now
}

// UpdateRange adds val to every element in [l, r].
func (st *SegTree) UpdateRange(l, r, val int) {
    st.updateRange(1, 0, st.size-1, l, r, val)
}

func (st *SegTree) updateRange(node, lo, hi, l, r, val int) {
    if r < lo || hi < l {
        return // no overlap
    }
    if l <= lo && hi <= r {
        // TOTAL overlap: this node's whole range is inside [l, r] — apply
        // now, defer the push to children until someone actually descends.
        st.tree[node] += val * (hi - lo + 1)
        st.lazy[node] += val
        return
    }
    // PARTIAL overlap: must recurse into children, so first push down
    // whatever this node still owes them, or their stale tree[] values
    // would be read before the update they're due gets applied.
    st.push(node, lo, hi)
    mid := lo + (hi-lo)/2
    st.updateRange(2*node, lo, mid, l, r, val)
    st.updateRange(2*node+1, mid+1, hi, l, r, val)
    st.tree[node] = st.tree[2*node] + st.tree[2*node+1]
}

// QueryRange returns the sum over [l, r].
func (st *SegTree) QueryRange(l, r int) int {
    return st.queryRange(1, 0, st.size-1, l, r)
}

func (st *SegTree) queryRange(node, lo, hi, l, r int) int {
    if r < lo || hi < l {
        return 0
    }
    if l <= lo && hi <= r {
        return st.tree[node]
    }
    st.push(node, lo, hi) // same reason as updateRange: don't read stale children
    mid := lo + (hi-lo)/2
    return st.queryRange(2*node, lo, mid, l, r) + st.queryRange(2*node+1, mid+1, hi, l, r)
}
```

**Why `push` is correct, stated as an invariant:** at every point *before* a
node's children are read (recursed into), that node's `lazy` value has been
fully pushed — so a child is only ever read once its own `tree[]` is
accurate for every update applied so far. `push` is called exactly at the
two places children are about to be read (`updateRange` and `queryRange`,
both on the PARTIAL-overlap branch — TOTAL overlap returns without touching
children at all, which is the entire point). Each individual update/query
call pushes at most `O(log n)` nodes (one per level on the recursion path),
so the amortized per-call cost stays `O(log n)` despite the extra pushes.

**Range-min/range-max instead of range-sum:** only `tree[node] =
combine(...)` and the push arithmetic change — for range-**assign** (not
range-add) lazy semantics, `push` overwrites the child's value instead of
adding to it, and a sentinel (e.g. `math.MinInt` meaning "no pending assign")
replaces `0` as the "no pending update" marker, since `0` is a valid assign
target.

### 3.5b Complexity

| Operation | Complexity |
|---|:--:|
| Build | O(n) |
| Point update | O(log n) |
| Range query | O(log n) |
| Range update (no lazy propagation) | O(n) worst case |
| Range update (with lazy propagation) | **O(log n)** |
| Space | O(n) (4·n array) |

---

## Part 4 · Python vs. Go — Where They Diverge

| | Python | Go |
|---|---|---|
| Built-in Fenwick/segment tree | None (hand-roll, or `sortedcontainers`-adjacent libs for some cases) | None — hand-roll, same as Python |
| Negative-number bit trick `i & (-i)` | Works identically — Python ints are arbitrary precision but two's-complement bit ops on `-i` are defined consistently | Works identically — relies on fixed-width two's complement (Topic 20) |
| Array pre-sizing (`4*n`) | Lists grow dynamically, no need to pre-size | Must `make([]int, 4*n)` up front — no implicit growth mid-recursion |
| Recursion depth | Same O(log n) depth, but Python's default recursion limit (~1000) can bite on very large `n` if the tree is written recursively | Go's growable goroutine stack (Topic 09) tolerates the same O(log n) depth with no practical limit |
| Integer overflow in sums | Never (arbitrary precision) | Wraps silently at 64 bits (Topic 01/21) — use `int64` for large-sum problems |

---

## Part 5 · Algorithms Owned by This Topic

| Algorithm | Time | Space | Problem |
|---|:--:|:--:|---|
| Fenwick Tree — point update, prefix/range sum query | O(log n) per op | O(n) | LC 307 Range Sum Query - Mutable |
| Fenwick Tree — inversion counting (via BIT over value ranks) | O(n log n) | O(n) | LC 315 Count of Smaller Numbers After Self |
| Segment Tree — range sum with point update | O(log n) per op | O(n) | LC 307 (alternate solution) |
| Segment Tree — range min/max query | O(log n) per op | O(n) | LC 2407 style range-max problems |
| Segment Tree + lazy propagation — range update, range query | O(log n) per op | O(n) | LC 370-style range-add problems |

---

## Part 6 · Building a Fenwick Tree From Scratch (LC 307)

```go
package main

// Fenwick supports point updates and O(log n) prefix/range sum queries over
// a 1-indexed internal array. n is the number of elements.
type Fenwick struct {
    n    int
    tree []int
}

func NewFenwickTree(n int) *Fenwick {
    return &Fenwick{n: n, tree: make([]int, n+1)}  // index 0 unused, see 2.2
}

// Update adds delta at 1-indexed position i, propagating to every tree[]
// slot whose range of responsibility includes i.
func (f *Fenwick) Update(i int, delta int) {
    for ; i <= f.n; i += i & (-i) {   // walk UP: jump to the next responsible index
        f.tree[i] += delta
    }
}

// Query returns the sum of nums[1..i] (1-indexed, inclusive).
func (f *Fenwick) Query(i int) int {
    sum := 0
    for ; i > 0; i -= i & (-i) {      // walk DOWN: strip the lowest set bit each step
        sum += f.tree[i]
    }
    return sum
}

// RangeQuery returns the sum of nums[l..r] (1-indexed, inclusive).
// Relies on prefix-sum subtraction, which only works because + has an
// inverse (-) — this is why Fenwick trees can't support min/max (see 2.5).
func (f *Fenwick) RangeQuery(l, r int) int {
    if l > 1 {
        return f.Query(r) - f.Query(l-1)
    }
    return f.Query(r)
}

// NumArray wraps Fenwick to match LC 307's expected interface.
type NumArray struct {
    nums []int   // 0-indexed original values, kept to compute deltas on Update
    bit  *Fenwick
}

func Constructor(nums []int) NumArray {
    na := NumArray{nums: make([]int, len(nums)), bit: NewFenwickTree(len(nums))}
    for i, v := range nums {
        na.Update(i, v)   // seeds the tree one element at a time — O(n log n) build
    }
    return na
}

// Update sets nums[i] = val (0-indexed, matching LC's signature) by pushing
// only the DELTA into the Fenwick tree, then remembering the new value.
func (na *NumArray) Update(i int, val int) {
    delta := val - na.nums[i]
    na.nums[i] = val
    na.bit.Update(i+1, delta)   // +1 to convert to the tree's 1-indexed space
}

func (na *NumArray) SumRange(left, right int) int {
    return na.bit.RangeQuery(left+1, right+1)   // +1 for the same reason
}
```

**Talk track while writing:** the tree only ever stores *deltas* relative to
what it already knows — that's why `Update` computes `val - na.nums[i]` instead
of pushing `val` itself; `i & (-i)` walks up on write and down on read, and
both directions terminate in `O(log n)` steps because each step strictly
changes the number of trailing zero bits in `i`; the `+1` conversions exist
purely because LC's array is 0-indexed but the Fenwick tree's math requires
1-indexing to make `i & (-i)` well-defined at every position.

---

<!-- block:26_go_1_toolkit -->
## Part 7 · The Toolkit in Full — Fenwick Variants, a Generic Iterative Segment Tree, a Sparse Table, Overflow, and the Numbers

Parts 2–6 give the two structures; this Part writes out what an interview asks about around them, in Go, and measures it. Every type below was compiled with `go vet` and checked against a brute-force reference on hundreds of random operation sequences
(non-power-of-two sizes included), on Go 1.24 (darwin/arm64).

```arch
%% caption: Which range structure? Invertible aggregate and point updates: Fenwick. Anything else, or range updates: segment tree. Static data: prefix sums or a sparse table.
grid 200x85
node q "Range query problem" at 1,0 shape=pill
node a "Does the array\nchange?" at 1,1 shape=diamond color=amber
node b "Aggregate?" at 0,2 shape=diamond color=amber
node p "Prefix sums" at 0,3 color=green w=180 sub="O(1) per query"
node sp "Sparse table" at 0,4 color=green w=180 sub="O(1) per query"
node c "Aggregate has\nan inverse?" at 2,2 shape=diamond color=amber
node f "Fenwick tree" at 2,3 color=green w=180
node f2 "Two Fenwick trees" at 2,4 color=amber w=180 sub="or a lazy segment tree"
node s "Segment tree" at 1,3 color=amber w=180 sub="iterative if no lazy tags"
q -> a
a:L -> b:T : "no"
a:R -> c:T : "yes"
b -> p : "sum / xor"
b:L -> sp:L : "min / max / gcd"
c -> f : "yes, point updates"
c:R -> f2:R : "yes, range updates"
c:L -> s:T : "no (min, max, gcd)"
```

### 7.1 The Fenwick tree, complete — linear build, delta updates, and the `k`-th element

```go
type Fenwick struct {
    n int
    t []int
}

func NewFenwickFrom(a []int) *Fenwick { // O(n): push each node's total to its parent once
    f := &Fenwick{n: len(a), t: make([]int, len(a)+1)}
    copy(f.t[1:], a)
    for i := 1; i <= f.n; i++ {
        if j := i + i&-i; j <= f.n {
            f.t[j] += f.t[i]
        }
    }
    return f
}

func (f *Fenwick) Add(i, delta int) { // i is 1-indexed; delta is a CHANGE
    for ; i <= f.n; i += i & -i {
        f.t[i] += delta
    }
}

func (f *Fenwick) Prefix(i int) int {
    s := 0
    for ; i > 0; i -= i & -i {
        s += f.t[i]
    }
    return s
}

func (f *Fenwick) RangeSum(l, r int) int { return f.Prefix(r) - f.Prefix(l-1) }

// Kth returns the smallest i with Prefix(i) >= k; every stored value must be >= 0.
func (f *Fenwick) Kth(k int) int {
    pos := 0
    for step := 1 << bits.Len(uint(f.n)); step > 0; step >>= 1 {
        if next := pos + step; next <= f.n && f.t[next] < k {
            pos = next
            k -= f.t[next]
        }
    }
    return pos + 1
}
```

`NewFenwickFrom` pushes each node's total to its parent once, so the build is O(n) instead of `n` calls to `Add`; it produced exactly the same tree as the `n` calls on 500 random arrays, and `Add`/`RangeSum` matched a running sum over 15,000 random operations.
Two habits. **`Add` takes a delta** — a wrapper that receives a *new value* must add `v - a[i]` and then store `v` (Problem 001's first trap; in the Python run, adding the new value directly was wrong in 500 of 500 random sessions). And **every call converts to 1-indexed**: LeetCode's `i` becomes `i+1`.
In Go `i + i&-i` means `i + (i & -i)`, because `&` has *multiplication* precedence and binds tighter than `+` — the code is correct, but write the parentheses when you explain it.

`Kth` finds the smallest `i` whose prefix count reaches `k` by binary lifting — no binary search over `Prefix`. With a tree of *counts* (`a[v]` = times `v` was inserted) it is the "k-th smallest in a dynamic set" query; it matched a brute-force scan for every `k` on 300 random count arrays.
`bits.Len` (from `math/bits`) gives the highest power of two to start the descent.

### 7.2 Range add with range sum — two Fenwick trees

```go
type RangeBIT struct {
    n      int
    b1, b2 []int
}

func NewRangeBIT(n int) *RangeBIT { return &RangeBIT{n, make([]int, n+1), make([]int, n+1)} }
func (r *RangeBIT) add(b []int, i, v int) {
    for ; i <= r.n; i += i & -i {
        b[i] += v
    }
}
func (r *RangeBIT) sum(b []int, i int) int {
    s := 0
    for ; i > 0; i -= i & -i {
        s += b[i]
    }
    return s
}
func (r *RangeBIT) RangeAdd(l, rr, v int) { // add v to a[l..rr]
    r.add(r.b1, l, v)
    r.add(r.b1, rr+1, -v)
    r.add(r.b2, l, v*(l-1))
    r.add(r.b2, rr+1, -v*rr)
}
func (r *RangeBIT) Prefix(i int) int      { return r.sum(r.b1, i)*i - r.sum(r.b2, i) }
func (r *RangeBIT) RangeSum(l, rr int) int { return r.Prefix(rr) - r.Prefix(l-1) }
```

A BIT over the difference array gives range-add with point queries; keeping a second one gives range **sums**: `prefix(x) = B1(x)·x − B2(x)`. It matched a naive array on 500 random sessions. It replaces the lazy segment tree of Part 3.5a for *sum* in a fifth of the code — but only for sum;
range-add with range-min needs the segment tree.

A Fenwick tree *can* answer **prefix**-min if every update only lowers a value (`t[i] = min(t[i], v)` on the same upward walk), but not range-min and not a value that rises again — Part 2.5's limitation, stated precisely.

### 7.3 The 2D tree (Problem 002)

```go
type Fenwick2D struct {
    m, n int
    t    [][]int
}

func NewFenwick2D(m, n int) *Fenwick2D {
    t := make([][]int, m+1)
    for i := range t {
        t[i] = make([]int, n+1)
    }
    return &Fenwick2D{m, n, t}
}
func (f *Fenwick2D) Add(r, c, d int) { // 1-indexed
    for i := r; i <= f.m; i += i & -i {
        for j := c; j <= f.n; j += j & -j {
            f.t[i][j] += d
        }
    }
}
func (f *Fenwick2D) Prefix(r, c int) int { // sum of the top-left r × c block
    s := 0
    for i := r; i > 0; i -= i & -i {
        for j := c; j > 0; j -= j & -j {
            s += f.t[i][j]
        }
    }
    return s
}
func (f *Fenwick2D) Region(r1, c1, r2, c2 int) int { // inclusion–exclusion: +D −B −C +A
    return f.Prefix(r2, c2) - f.Prefix(r1-1, c2) - f.Prefix(r2, c1-1) + f.Prefix(r1-1, c1-1)
}
```

Each operation is O(log m · log n). It was tested on 1–6 rows and columns — non-square shapes are where the classic bugs (swapped axes, the `+1` on one axis only) show up — against a direct sum.

### 7.4 A generic iterative segment tree

Without lazy propagation, the bottom-up layout is shorter and faster than the recursive one: leaves live at `n … 2n−1`, node `i` has children `2i` and `2i+1`, and a query walks two boundaries upward. Go generics let one type serve min, max, sum and gcd:

```go
type SegTree[T any] struct {
    n        int
    t        []T
    identity T
    op       func(a, b T) T
}

func NewSegTree[T any](a []T, identity T, op func(a, b T) T) *SegTree[T] {
    n := len(a)
    s := &SegTree[T]{n: n, t: make([]T, 2*n), identity: identity, op: op}
    copy(s.t[n:], a)
    for i := n - 1; i > 0; i-- {
        s.t[i] = op(s.t[2*i], s.t[2*i+1])
    }
    return s
}
func (s *SegTree[T]) Update(i int, v T) { // 0-indexed point assignment
    for i += s.n; ; i >>= 1 {
        s.t[i] = v
        if i == 1 {
            break
        }
        v = s.op(s.t[i&^1], s.t[i|1]) // recompute the parent from both children
    }
}
func (s *SegTree[T]) Query(l, r int) T { // a[l..r] inclusive; op must be commutative here
    res := s.identity
    for l, r = l+s.n, r+s.n+1; l < r; l, r = l>>1, r>>1 {
        if l&1 == 1 {
            res = s.op(res, s.t[l])
            l++
        }
        if r&1 == 1 {
            r--
            res = s.op(res, s.t[r])
        }
    }
    return res
}
```

```go
mn := NewSegTree(a, math.MaxInt, func(x, y int) int { return min(x, y) }) // range minimum
sm := NewSegTree(a, 0, func(x, y int) int { return x + y })              // range sum:  Query(0, 4) = 15, then Update(2, 10) → 22
```

It needs `2n` slots and works for any `n` (tested on sizes 1–40 against `slices.Min`). `identity` must satisfy `op(identity, x) == x` (`math.MaxInt` for min, `0` for sum). `Query` combines in boundary order, so `op` must be **commutative** as written; for a
non-commutative operation keep separate left and right accumulators.

### 7.5 Static range minimum: the sparse table

```go
type Sparse struct{ t [][]int }

func NewSparse(a []int) *Sparse {
    t := [][]int{slices.Clone(a)}
    for j := 1; 1<<j <= len(a); j++ {
        p := t[j-1]
        row := make([]int, len(a)-1<<j+1)
        for i := range row {
            row[i] = min(p[i], p[i+1<<(j-1)])
        }
        t = append(t, row)
    }
    return &Sparse{t}
}
func (s *Sparse) Query(l, r int) int { // inclusive; two overlapping blocks are fine because min is idempotent
    k := bits.Len(uint(r-l+1)) - 1
    return min(s.t[k][l], s.t[k][r-1<<k+1])
}
```

`t[k][i]` is the minimum of `a[i … i + 2^k − 1]`; a query uses two overlapping blocks, legal because `min` is idempotent. O(n log n) build, O(1) query; correct on 500 random arrays. It does not work for sum (overlap would double-count) — use prefix sums.
Mind the precedence in `1<<j` and `len(a)-1<<j+1`: Go's shift binds tighter than `+`/`-`, so that expression is `len(a) - (1<<j) + 1`.

### 7.6 Integer overflow, the Go version of "why did my count go negative"

Go's `int` is 64-bit, so sums of up to 10⁵ values of size 2³¹ (Problem 004's prefix sums) fit comfortably. The trap is a narrower type — `int32` because the LeetCode statement says "32-bit integer":

- `x > 2*y` in `int32` with `x = y = 1<<30`: `2*x` wraps to `-2147483648`, so the comparison is **true** where the arithmetic says false (measured; the same comparison in `int64` is `false`). Problem 003's condition needs the wider type: `int64(x) > 2*int64(y)`, or just work in `int`.
- Prefix sums in `int32`: `math.MaxInt32 + math.MaxInt32` wraps to `-2`; in `int64` it is `4294967294`.
- Constant expressions are checked at compile time, runtime arithmetic is not: `2 * int32(1<<30)` as a constant is a compile error (`overflows int32`); the same product of two variables silently wraps.

### 7.7 The numbers

`n = 10⁵` values, 20,000 mixed operations (half point updates, half range sums), best of five runs:

| Approach | Time |
|---|--:|
| Re-sum the slice for every query | 77.5 ms |
| Rebuild a prefix-sum array after every update | 327.9 ms |
| **Fenwick tree** (including the linear build) | **0.45 ms** |

The prefix rebuild is *worse* than naive summing because every update pays O(n) and half the operations are updates. At a million operations on the same array:

| Structure | Time for 1,000,000 mixed operations (sum) |
|---|--:|
| Fenwick tree | **17 ms** |
| Iterative segment tree (generic, above) | 48 ms |
| Recursive segment tree (Part 3.3) | 107 ms |

So the Fenwick tree is about 3× faster than the iterative segment tree and 6× faster than the recursive one for sums — the reason Part 1's rule says "default to Fenwick when the aggregate has an inverse". The generic tree pays for its `func` call per combine.

### 7.8 Follow-ups the interviewer reaches for

| Follow-up | The answer |
|---|---|
| "Range add *and* range sum." | Two Fenwick trees (`prefix(x) = B1(x)·x − B2(x)`) or a lazy segment tree. |
| "The k-th smallest in a changing multiset." | A Fenwick tree of counts with `Kth`, over compressed values. |
| "Range minimum, values never change." | A sparse table: O(n log n) build, O(1) query. |
| "Range minimum with point updates." | A segment tree (iterative is fine); a Fenwick tree cannot do range-min. |
| "Values up to 10⁹, only n distinct." | Coordinate-compress before indexing a BIT: `slices.Sort` → `slices.Compact` → `slices.BinarySearch`. |
| "Why `4n` for the recursive tree?" | Indexes reach `2^(⌈log₂ n⌉+1) − 1 < 4n`; `2n` fails already at `n = 6`. |

---
<!-- /block:26_go_1_toolkit -->

<!-- block:26_go_2_problems -->
## Part 8 · The Six Problems in Go — Fenwick, Merge-Sort Counting, Compression, and the Sweep

The Go solution files for this topic are still placeholders, so these are the plans: each compiled with `go vet` and compared with a brute-force reference on 1,500–2,000 random small inputs (500 for the Fenwick classes).

### 8.1 Problem 001: Range Sum Query – Mutable

```go
type NumArray struct {
    a []int
    f *Fenwick
}

func Constructor(nums []int) NumArray { return NumArray{slices.Clone(nums), NewFenwickFrom(nums)} }
func (n *NumArray) Update(i, v int)  { n.f.Add(i+1, v-n.a[i]); n.a[i] = v } // the DELTA, and 1-indexed
func (n *NumArray) SumRange(l, r int) int { return n.f.RangeSum(l+1, r+1) }
```

(`Fenwick` is the type from Part 7.1.) The three `+1`s convert LeetCode's 0-indexed positions into the tree's 1-indexed space; the difference `v - n.a[i]` is what the tree stores. Problem 002 is Part 7.3's `Fenwick2D` wrapped the same way: `Add(r+1, c+1, v-g[r][c])` and
`Region(r1+1, c1+1, r2+1, c2+1)`.

### 8.2 Problem 003: Reverse Pairs — count *before* you merge

```go
func reversePairs(nums []int) int {
    a := slices.Clone(nums)
    buf := make([]int, len(a))
    var sort func(lo, hi int) int
    sort = func(lo, hi int) int {
        if hi-lo <= 1 {
            return 0
        }
        mid := lo + (hi-lo)/2
        cnt := sort(lo, mid) + sort(mid, hi)
        j := mid
        for i := lo; i < mid; i++ { // both halves are sorted, so j only moves forward
            for j < hi && a[i] > 2*a[j] {
                j++
            }
            cnt += j - mid
        }
        copy(buf[lo:hi], a[lo:hi]) // merge AFTER counting, with the ordinary <= comparison
        i, k, w := lo, mid, lo
        for i < mid && k < hi {
            if buf[i] <= buf[k] {
                a[w] = buf[i]
                i++
            } else {
                a[w] = buf[k]
                k++
            }
            w++
        }
        for i < mid {
            a[w] = buf[i]
            i++
            w++
        }
        for k < hi {
            a[w] = buf[k]
            k++
            w++
        }
        return cnt
    }
    return sort(0, len(a))
}
// reversePairs([1 3 2 3 1]) = 2      reversePairs([2 4 3 5 1]) = 3
```

Both halves are sorted, so `j` only moves forward and the count per level is O(n). The counting condition `a[i] > 2*a[j]` and the merge order `buf[i] <= buf[k]` are **different comparisons** — using the first as the merge comparison corrupts the sortedness the next level depends on.
Counting *after* the merge — the third documented trap — was wrong on **906 of 1,000** random arrays, because once the halves are mixed there is no way to tell which pairs cross the split. Use `int` (64-bit): with an `int32` element type `2*a[j]` can wrap (Part 7.6). A BIT over compressed values *and* their doubles gives the same
answer scanning right to left.

### 8.3 Problem 004: Count of Range Sum — two pointers per left element

```go
func countRangeSum(nums []int, lower, upper int) int {
    a := make([]int, len(nums)+1) // a[0] = 0 is a real prefix
    for i, v := range nums {
        a[i+1] = a[i] + v
    }
    buf := make([]int, len(a))
    var sortc func(l, r int) int
    sortc = func(l, r int) int {
        if r-l <= 1 {
            return 0
        }
        m := l + (r-l)/2
        cnt := sortc(l, m) + sortc(m, r)
        j, k := m, m
        for i := l; i < m; i++ { // window of right-half j with lower <= a[j]-a[i] <= upper
            for j < r && a[j]-a[i] < lower {
                j++
            }
            for k < r && a[k]-a[i] <= upper {
                k++
            }
            cnt += k - j
        }
        copy(buf[l:r], a[l:r])
        i, p, w := l, m, l
        for i < m && p < r {
            if buf[i] <= buf[p] {
                a[w] = buf[i]
                i++
            } else {
                a[w] = buf[p]
                p++
            }
            w++
        }
        for i < m {
            a[w] = buf[i]
            i++
            w++
        }
        for p < r {
            a[w] = buf[p]
            p++
            w++
        }
        return cnt
    }
    return sortc(0, len(a))
}
// countRangeSum([-2 5 -1], -2, 2) = 3
```

Subarray sums are differences of **prefix** sums, so the recursion runs on the prefix array (with `a[0] = 0` as a real entry), not on `nums`. For each left element, `j` is the first right index whose difference is `>= lower` and `k` the first whose difference is `> upper`; the window `[j, k)` is inclusive of both
bounds. Neither pointer resets per `i`, which is what keeps each merge level linear. Sums up to `10⁵ × 2³¹` fit `int`.

### 8.4 Problem 005: Falling Squares — compress, then a segment tree with a "raise the floor" tag

```go
func fallingSquares(positions [][]int) []int {
    xs := make([]int, 0, 2*len(positions))
    for _, p := range positions {
        xs = append(xs, p[0], p[0]+p[1])
    }
    slices.Sort(xs)
    xs = slices.Compact(xs)
    n := len(xs) - 1 // elementary segments [xs[i], xs[i+1])
    mx, lz := make([]int, 4*n), make([]int, 4*n)
    var upd func(node, lo, hi, l, r, h int)
    upd = func(node, lo, hi, l, r, h int) {
        if r < lo || hi < l {
            return
        }
        if l <= lo && hi <= r {
            mx[node], lz[node] = max(mx[node], h), max(lz[node], h)
            return
        }
        mid := lo + (hi-lo)/2
        upd(2*node, lo, mid, l, r, h)
        upd(2*node+1, mid+1, hi, l, r, h)
        mx[node] = max(mx[2*node], mx[2*node+1], lz[node])
    }
    var qry func(node, lo, hi, l, r int) int
    qry = func(node, lo, hi, l, r int) int {
        if r < lo || hi < l {
            return 0
        }
        if l <= lo && hi <= r {
            return mx[node]
        }
        mid := lo + (hi-lo)/2
        return max(lz[node], qry(2*node, lo, mid, l, r), qry(2*node+1, mid+1, hi, l, r))
    }
    out, best := make([]int, 0, len(positions)), 0
    for _, p := range positions {
        a, _ := slices.BinarySearch(xs, p[0])
        b, _ := slices.BinarySearch(xs, p[0]+p[1])
        b-- // the right edge needs the - 1: segments sit BETWEEN coordinates
        h := qry(1, 0, n-1, a, b) + p[1]
        upd(1, 0, n-1, a, b, h)
        best = max(best, h)
        out = append(out, best)
    }
    return out
}
// fallingSquares([[1 2] [2 3] [6 1]]) = [2 5 5]      fallingSquares([[100 100] [200 100]]) = [100 100]
```

Compression is `slices.Sort` → `slices.Compact` → `slices.BinarySearch`; the tree is indexed by the *segments between* coordinates, so the right edge converts with a `- 1`. The tag never needs pushing down: it only raises a floor, and a query takes the maximum of the tags along its path. The running maximum (`best`),
not this square's own height, is appended. Treating the intervals as **closed** (touching squares overlap) turned `[[100 100] [200 100]]` into `[100 200]` instead of `[100 100]`; the half-open `[left, left+size)` convention must be used everywhere, including the brute-force oracle.

### 8.5 Problem 006: The Skyline — resolve all events at an `x`, then compare

```go
type bld struct{ h, right int }
type maxHeap []bld

func (h maxHeap) Len() int           { return len(h) }
func (h maxHeap) Less(i, j int) bool { return h[i].h > h[j].h }
func (h maxHeap) Swap(i, j int)      { h[i], h[j] = h[j], h[i] }
func (h *maxHeap) Push(x any)        { *h = append(*h, x.(bld)) }
func (h *maxHeap) Pop() any {
    old := *h
    x := old[len(old)-1]
    *h = old[:len(old)-1]
    return x
}

func getSkyline(buildings [][]int) [][]int {
    xs := make([]int, 0, 2*len(buildings))
    for _, b := range buildings {
        xs = append(xs, b[0], b[1])
    }
    slices.Sort(xs)
    xs = slices.Compact(xs)
    bs := slices.Clone(buildings)
    slices.SortFunc(bs, func(a, b []int) int { return cmp.Compare(a[0], b[0]) })
    h := &maxHeap{}
    i := 0
    out := [][]int{}
    for _, x := range xs {
        for i < len(bs) && bs[i][0] <= x { // add everything that starts by x
            heap.Push(h, bld{bs[i][2], bs[i][1]})
            i++
        }
        for h.Len() > 0 && (*h)[0].right <= x { // lazily drop expired tops
            heap.Pop(h)
        }
        height := 0
        if h.Len() > 0 {
            height = (*h)[0].h
        }
        if len(out) == 0 || out[len(out)-1][1] != height { // only emit a change
            out = append(out, []int{x, height})
        }
    }
    return out
}
// getSkyline([[2 9 10] [3 7 15] [5 12 12] [15 20 10] [19 24 8]]) = [[2 10] [3 15] [7 12] [12 0] [15 10] [20 8] [24 0]]
```

`container/heap` has no removal by value, so expired buildings are dropped **lazily** — only when they reach the top. The order inside one `x` is load-bearing: add the buildings that start there *before* reading the top (reading first gave `[[0 0]]` instead of `[[0 3] [5 0]]` on
`[[0 2 3] [2 5 3]]`), the right edge is exclusive, an empty heap means height `0`, and a key point is emitted only when the height changes. Building the critical-`x` list from *both* edges (then `Sort` + `Compact`) is what makes the final `[24 0]` appear.

### 8.6 Which approach for which problem

| Problem | Structure | Why not the other |
|---|---|---|
| 001 | Fenwick | Sum has an inverse, point updates only |
| 002 | 2D Fenwick | Same, in two axes — O(log m · log n) |
| 003, 004 | Merge sort counting (or BIT + compression) | Static array: no live updates, so no structure is needed |
| 005 | Compression + segment tree (or an O(n²) scan for n ≤ 1,000) | Range-max with range assignment: not invertible |
| 006 | Sweep + heap with lazy deletion (or the same segment tree) | Only the *top* of the active set is ever needed |

---
<!-- /block:26_go_2_problems -->

<!-- problem-map:start -->
## Part 9 · Every Problem in This Topic, by Pattern

Six problems, three tools (a Fenwick tree for invertible aggregates · merge-sort counting when the array is static · compression plus a max-structure for sparse coordinates) — the Python guide's map in Go. Each **Trap** is a mistake documented in that problem's solution file, plus Go-specific hazards. Topic 26's Go solutions are still placeholders; Part 8 has a tested plan for each.

| Problem | Move | The idea — and the trap it sets |
|---|---|---|
| [001 · Range Sum Query - Mutable](GoDSA/26_segment_tree_fenwick/001_range_sum_query_mutable/solution.go) <br>LC 307 · Medium | Point update, range sum: Fenwick | `Add(i+1, v-a[i])`, `SumRange = RangeSum(l+1, r+1)`; keep the current values in a slice. **Trap:** passing `val` instead of `val - a[i]`; forgetting the tree is 1-indexed (`0 & -0 == 0` loops forever); mixing the count and endpoint conventions of `Prefix`; an O(n log n) build when O(n) is available. |
| [002 · Range Sum Query 2D - Mutable](GoDSA/26_segment_tree_fenwick/002_range_sum_query_2d_mutable/solution.go) <br>LC 308 · Hard | The same in two axes | Nested `i & -i` / `j & -j` loops; `Region` = `+D −B −C +A`. **Trap:** wrong inclusion–exclusion signs; swapped row and column (only visible on non-square matrices); the `+1` on one axis only; rebuilding the tree on every update. |
| [003 · Reverse Pairs](GoDSA/26_segment_tree_fenwick/003_reverse_pairs/solution.go) <br>LC 493 · Hard | Count during merge sort | Both halves sorted → a forward-only `j` counts `a[i] > 2*a[j]` per left element, *then* merge with `<=`. **Trap:** using the count condition as the merge comparison; resetting `j` per `i` (O(n²)); counting after merging (wrong on 906 of 1,000 random arrays); `>=` instead of `>`; `int32` where `2*x` wraps. |
| [004 · Count of Range Sum](GoDSA/26_segment_tree_fenwick/004_count_of_range_sum/solution.go) <br>LC 327 · Hard | The same on prefix sums, two pointers | Run on the prefix array (with `a[0] = 0`); `j` = first difference `>= lower`, `k` = first `> upper`; add `k - j`. **Trap:** running on `nums`; resetting the pointers per `i`; one pointer instead of two; an inclusive/exclusive slip; dropping `a[0]`; `int32` prefix sums. |
| [005 · Falling Squares](GoDSA/26_segment_tree_fenwick/005_falling_squares/solution.go) <br>LC 699 · Hard | Compress, then a max-structure | `slices.Sort` + `Compact` the edges; a square covers segments `idx(l) … idx(r) - 1`; height = query + side; keep a running maximum. **Trap:** a tree over raw coordinates; the missing `- 1`; treating touching squares as overlapping (`[100 200]` instead of `[100 100]`); returning this square's own height instead of the running max. |
| [006 · The Skyline Problem](GoDSA/26_segment_tree_fenwick/006_the_skyline_problem/solution.go) <br>LC 218 · Hard | Sweep over critical x's with a heap | At each `x`: push everything starting by `x`, pop expired tops, read the max, emit only on change. **Trap:** emitting after every push/pop; removing from the middle of the heap (lazy deletion instead); emitting every `x`; an inclusive right edge; forgetting the empty-heap height `0`; reading the top before pushing the starts (`[[0 0]]` on two touching buildings). |

---
<!-- problem-map:end -->

## Checklist Before Leaving This Topic

- [ ] Explain why a static prefix sum (Topic 04) is insufficient the moment the array is mutated
- [ ] Derive `i & (-i)` from two's complement and explain what it isolates
- [ ] Draw the "responsible range" diagram for a Fenwick tree and place index 6 and index 4 on it
- [ ] Explain why Fenwick trees must be 1-indexed
- [ ] Explain why `RangeQuery = Query(r) - Query(l-1)` only works for invertible operations
- [ ] State why Fenwick trees cannot support range-min/max, and what to use instead
- [ ] Contrast segment tree index math (`2i`/`2i+1`, aggregate per node) with Topic 12's heap index math
- [ ] Explain why segment tree arrays are over-allocated to `4*n`
- [ ] Explain lazy propagation conceptually: what is deferred, and when it gets pushed down
- [ ] Write a Fenwick tree with `Update`/`Query`/`RangeQuery` from memory in under 15 minutes
- [ ] Write a Fenwick tree with the O(n) build, `Add(i, delta)` with a *delta*, and `Kth` by binary lifting <!--ca-->
- [ ] Build range-add / range-sum from two Fenwick trees, and state what a BIT can do with min (prefix-min, lowering only) and what it cannot <!--ca-->
- [ ] Write the 2D tree's four-term inclusion–exclusion and test it on a non-square matrix <!--ca-->
- [ ] Write a generic iterative segment tree (`n + i` leaves, an `identity`, an `op`) and know when `op` must be commutative <!--ca-->
- [ ] Explain the recursive tree's `4n` (index `< 2^(⌈log₂ n⌉+1)`) and why `2n` fails at `n = 6` <!--ca-->
- [ ] Quote the measured ranking for sums: Fenwick 17 ms, iterative segment tree 48 ms, recursive 107 ms per million operations <!--ca-->
- [ ] Use `int` (not `int32`) for `2*x` and prefix sums, and know that constant overflow is a compile error while runtime overflow wraps <!--ca-->
- [ ] Count Reverse Pairs *before* merging with a forward-only pointer, and run Count of Range Sum on the prefix array <!--ca-->
- [ ] Use half-open intervals and a `- 1` when converting to compressed segment indexes; emit skyline key points only after resolving every event at an `x` <!--ca-->
