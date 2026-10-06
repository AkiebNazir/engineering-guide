# Google-Style Follow-Ups — Scaling a Coding Answer

This is the capstone of the module — read it after files `01`–`09`, once you can
already solve a base coding problem confidently. It takes that solved problem and
stretches it exactly the way a strong interviewer does. This chapter starts from first
principles — why interviewers ask follow-ups at all, what a follow-up really changes,
and how the toolkits fit together — then gives you a toolkit for each of the five
common follow-ups, works through six problems with all five, and ends with runnable,
verified code for the streaming and out-of-memory techniques you're most likely to be
asked to sketch. Corrections of common myths are marked **Precision note**. A
side-by-side breakdown of what Junior through Staff+ engineers are expected to know
closes out the chapter, just before the interview checklist.

## Foundations — What Is a Follow-Up, and How Do You Answer One?

### Why Follow-Ups Exist

A single coding problem is a weak signal on its own. Popular problems get memorised;
a candidate who has seen Two Sum before and one who derived it on the spot can produce
identical code. And the base problem rarely separates levels: a new grad and a senior
engineer may both solve it in 20 minutes.

A follow-up fixes both problems at once. It changes one thing about the problem and
watches what you do. Memorisation doesn't transfer to the changed problem; engineering
judgment does. And the *kind* of answer you give — a patch to the code, a new data
structure, or a small system design with trade-offs — is one of the clearest level
signals in the whole loop. That's why the same five questions come up again and
again after you've solved the problem:

1. **What if the input is a stream and you can't store it all?**
2. **What if the data doesn't fit in memory, or is spread across many machines?**
3. **What if there are millions of queries? What would you precompute?**
4. **What if multiple threads call this at once? What needs locking?**
5. **What if a constraint changes — negative numbers, duplicates, a graph with cycles?**

These follow-ups are where coding rounds turn into small system-design conversations,
and they're a strong L5 signal.

### What a Follow-Up Actually Is

Every solution rests on assumptions nobody said out loud. Two Sum's hash-map solution
assumes the whole array is available up front, fits in one machine's memory, is
queried once, is used by one thread, and contains ordinary integers. **A follow-up
removes one of those assumptions.** Your job is to notice which one, say what breaks
because of it, and pick a technique from the family that handles that kind of change.

| Silent assumption in the base solution | The follow-up that removes it | Toolkit |
|---|---|---|
| All input is available before you start, and you can keep it | "It's a stream" | §1 |
| It fits in one machine's RAM | "It's 10 TB" / "It's on 1,000 machines" | §2 |
| You answer once | "There are millions of queries" | §3 |
| One thread calls your code | "Many threads call it at once" | §4 |
| The input has the properties your trick relies on | "Now values can be negative / repeated / cyclic" | §5 |

### The Core Components of a Good Follow-Up Answer

| Component | What it's responsible for | Covered deeper in |
|---|---|---|
| **What breaks** | Naming the exact part of the current solution that fails under the new assumption | §12 |
| **Technique family** | Streaming summaries, partitioning, precomputation, synchronization, or a different algorithm | §1–§5 |
| **Trade-off** | What you give up: exactness, memory, latency, update cost, simplicity | §1–§5, §12 |
| **Guarantee** | The bound you can still promise: "error ≤ εn", "O(k) memory", "exact after the shuffle" | §13–§15 |
| **Simple first** | The obvious version before the scalable one, so the interviewer can steer | §12 |

### How the Pieces Fit Together

```arch
%% caption: A follow-up changes one assumption; name what breaks, pick the matching technique family, and state what you trade for it.
grid 175x90
node base "Solved problem" at 0,1 shape=pill color=green sub="the base answer"
node fu "What changed?" at 0,3 shape=diamond color=amber
group fam "Technique families" color=blue icon=layers
node st "Stream" at 1,0 in fam shape=card icon=stream sub="sketches, O(k) state (§1)"
node big "Too big" at 1,1 in fam shape=card icon=server sub="partition + merge (§2)"
node q "Many queries" at 1,2 in fam shape=card icon=search sub="precompute (§3)"
node thr "Threads" at 1,3 in fam shape=card icon=lock sub="lock what's shared (§4)"
node con "Constraint" at 1,4 in fam shape=card icon=edit sub="new algorithm (§5)"
node trade "State the trade-off" at 2,2 shape=pill color=slate sub="exactness, memory, latency"
base -> fu
fu -> st
fu -> big
fu -> q
fu -> thr
fu -> con
st -> trade
big -> trade
q -> trade
thr -> trade
con -> trade
```

### Precision: Exact vs. Approximate, and What ε Means

Many of the scalable answers below are **approximate**: they give up exactness to fit
in a fixed amount of memory. That's only a good answer if you can say *how*
approximate. Streaming algorithms state it as an error bound with a parameter ε
(epsilon): "the count is at most ε·n too high" or "the quantile is within ε of the
true rank", and memory grows like 1/ε. Halving the error typically doubles the memory.
Some bounds also hold only "with probability 1 − δ". Saying "approximate, error ≤ ε·n
with probability 1 − δ, in O((1/ε)·log(1/δ)) memory" for a count-min sketch is the
difference between a buzzword and an answer.

### Vocabulary You'll Meet Below, in One Table

| Term | One-line meaning |
|---|---|
| Stream | Input that arrives one item at a time, possibly forever; you see each item once |
| Sketch | A small, fixed-size summary of a stream that answers one kind of query approximately (count-min, HyperLogLog, t-digest) |
| Mergeable | Two sketches built on different data can be combined into the sketch of the union — what makes them distributable |
| ε, δ | Error bound and failure probability of an approximate answer |
| Partition / shard | Split data by a key so each piece can be processed independently |
| Shuffle | Moving every record to the partition that owns its key (the expensive network step in MapReduce/Spark) |
| Skew | One key (or partition) with far more data than the rest |
| External sort | Sorting data larger than memory with sorted runs on disk plus a k-way merge |
| Precompute | Pay once up front (prefix sums, indexes) so each query is cheap |
| Single-flight | Concurrent requests for the same missing value wait on one computation |
| Online / offline | Answering each query as it arrives vs. seeing all queries first |

With the "which assumption changed?" habit in place, the toolkits below are the
catalogue of answers, the worked examples show them applied, and §13–§15 are the
implementations you should be able to write.

## 1. Toolkit: Stream (Can't Store Everything)

| Need | Technique | Memory | Notes |
|---|---|---|---|
| Running sum / count / mean | Running aggregates | O(1) | Variance too (Welford's algorithm) |
| Max/min of last k | Monotonic deque | O(k) | `PyDSA/03_sliding_window/015` |
| Top-k largest seen | Min-heap of size k | O(k) | O(log k) per element |
| Median / percentiles, exact | Two heaps | O(n) | Not bounded |
| Median / percentiles, approximate | t-digest, KLL, GK sketches | O(1/ε) | Mergeable across machines |
| Distinct count | HyperLogLog | ~KB for ~1-2% error | Mergeable |
| Frequency of items / heavy hitters | Count-min sketch (+ heap), Misra-Gries | O(1/ε) | Overestimates only |
| Membership ("seen before?") | Bloom filter | ~10 bits/item for 1% false positives | No false negatives |
| Uniform random sample of k | Reservoir sampling | O(k) | `PyDSA/27_algorithms/002`, `003` |
| Majority element | Boyer–Moore voting | O(1) | Needs a verification pass if a majority isn't guaranteed |
| Sliding time window counts | Circular buckets | O(window / granularity) | `PyDSA/25_design/011` |

Details on the probabilistic structures: [Specialized Data Structures and Indexes](../SystemDesign/building_blocks/20_specialized_data_structures.md).

**Try it: trade accuracy for memory.** A Bloom filter answers “have I seen this?” and a count-min sketch answers “roughly how many times?”, both in a fixed, small amount of memory. Shrink the structure and watch the false-positive rate or the over-count grow: that is the ε in “exact vs. approximate”, made visible.

<div class="lab" data-viz="sd-sketch"></div>

## 2. Toolkit: Doesn't Fit in Memory / Many Machines

| Problem shape | Technique |
|---|---|
| Sort huge data | **External merge sort**: sort chunks that fit in RAM, write runs, k-way merge with a heap (`PyDSA` merge k sorted lists) |
| Count / group / join | **Hash partitioning**: route each record to one of P files/machines by `hash(key) % P` so equal keys meet; process each partition independently (**MapReduce** shuffle) |
| Top-k over huge data | Partition by key, compute per-partition counts, keep per-partition top-k, merge. For approximate: count-min sketches merged across machines |
| Deduplicate | Hash partition, then dedupe within each partition; or a Bloom filter pass first |
| Two-sum style lookups | Partition both sides by the same hash so matching pairs land together |
| Graph too big | Partition vertices; iterative message passing (Pregel-style BSP), label propagation for connected components |
| Median of huge data | Binary search on the value: count elements ≤ mid in a distributed pass (log(range) passes), or approximate quantile sketches |
| Data spread over machines, need a global order | Range partitioning with sampled split points (like TeraSort) |

Always mention: **network is the bottleneck** (minimize shuffles), **skew** (one hot key overloads a partition — salt it), and **stragglers/failures** (retries, speculative execution).

```arch
%% caption: Hash partitioning: each mapper pre-aggregates its own records, then the shuffle sends every key to the one reducer that owns hash(key) % 2, so all counts for a key meet in one place.
grid 190x120
group m "Map + combine (per machine)" color=slate style=dashed icon=worker
node m1 "Mapper 1" at 0,0 in m icon=worker sub="A, B, A → A:2 B:1"
node m2 "Mapper 2" at 0,1 in m icon=worker sub="B, A → A:1 B:1"
group r "Reduce (owns a key range)" color=amber style=dashed icon=worker
node w1 "Reducer 1" at 2,0 in r icon=worker sub="hash(A) % 2: A = 3"
node w2 "Reducer 2" at 2,1 in r icon=worker sub="hash(B) % 2: B = 2"
node out "Merge results" at 3,0.5 shape=pill color=green sub="exact global counts"
m1 -> w1 : "A:2"
m1 -> w2 : "B:1" straight
m2 -> w1 : "A:1" straight
m2 -> w2 : "B:1"
w1 -> out
w2 -> out
```

## 3. Toolkit: Millions of Queries (Precompute)

| Query | Precompute | Query time |
|---|---|---|
| Range sum, static array | Prefix sums (2D prefix sums for grids) | O(1) |
| Range sum with updates | Fenwick tree / segment tree | O(log n) |
| Range min/max, static | Sparse table | O(1) |
| Range min/max with updates | Segment tree | O(log n) |
| "Is x present?" / "count of x" | Hash set / Counter | O(1) |
| Prefix / autocomplete | Trie with top-k per node, or sorted list + bisect | O(prefix length) |
| k-th smallest in a range | Merge sort tree / wavelet tree / persistent segment tree | O(log² n) |
| Shortest path between any pair, small graph | Floyd–Warshall | O(1) |
| Shortest path, large sparse graph | Landmarks (ALT), contraction hierarchies (how map routing works) | fast in practice |
| Tree distance / LCA | Binary lifting or Euler tour + sparse table | O(log n) / O(1) |
| Connectivity with only edge additions | Union-Find | ~O(1) |
| Repeated identical queries | Memoization / caching (LRU) | O(1) on hit |
| Geo "nearby" | Geohash / quadtree / S2 index | O(log n + results) |

Name the trade-off: **precomputation time and memory vs query latency**, and how updates invalidate precomputed data.

## 4. Toolkit: Concurrency (What Needs Locking?)

See [Concurrency](05_concurrency_deep_dive.md) for primitives. The answer structure:
1. **What's shared and mutable?**
2. **Which invariants span multiple fields** (must change under one lock)?
3. **Which check-then-act sequences exist** (race even if each step is thread-safe)?
4. **Coarse lock first**, then refine: RW lock for read-heavy, **lock striping** (shards) for hot maps, **atomics** for counters, **immutable snapshots / copy-on-write** for read-mostly data, **confinement** (per-thread state merged later).
5. **Don't hold locks during slow work** (I/O, expensive compute); use single-flight for cache misses.

## 5. Toolkit: A Constraint Changes

| Change | What breaks | Typical fix |
|---|---|---|
| Negative numbers | Sliding window's monotone validity (sum no longer grows with the window); Dijkstra | Prefix sums + hash map; Bellman-Ford / SPFA |
| Zeros | Division-based tricks (product except self) | Count zeros; prefix/suffix products |
| Duplicates | Binary search on rotated arrays (worst case O(n)); permutations/combinations (dedupe); strict vs non-strict comparisons | Skip equal neighbors after sorting; `bisect_left` vs `bisect_right` |
| Cycles in a graph/"tree" | Plain recursion revisits forever; topological order doesn't exist | Visited sets; cycle detection (three colors / Kahn's leftover nodes) |
| Directed instead of undirected | Union-Find for cycle detection doesn't apply | DFS with recursion-stack colors |
| Weighted instead of unweighted | BFS no longer gives shortest paths | Dijkstra; 0-1 BFS if weights are 0/1 |
| Unsorted instead of sorted | Two pointers / binary search | Sort first (O(n log n)) or hash map (O(n)) |
| Online (items arrive one at a time) | Offline sorting tricks | Heaps, balanced BSTs, streaming algorithms |
| k is huge vs tiny | Heap of size k becomes O(n) memory | Quickselect for one-shot; switch structure by k |
| Values bounded small | — (an opportunity) | Counting sort, arrays instead of hash maps, bitsets |
| Exact answer → approximate OK | — (an opportunity) | Sampling, sketches |

## 6. Worked Example: Two Sum

**Base:** one pass with a hash map value → index. O(n) time, O(n) space.

| Follow-up | Answer |
|---|---|
| Stream | Keep the hash map of seen values; each arriving x checks `target - x`. Memory grows with distinct values; if bounded memory, you must accept approximation (Bloom filter gives "maybe", then verify against storage). |
| Doesn't fit / distributed | Sort externally and use two pointers over sorted runs, or hash-partition by `value mod P` where pair partitions are `p` and `(target - p) mod P`, then solve each partition pair in memory. |
| Many queries with different targets | If the array is static: sort once, each query O(n) with two pointers; or precompute all pair sums if n is small (O(n²) space). With many queries for *membership of a pair sum*, precompute a hash set of all pair sums when n² fits. |
| Concurrent inserts + queries (LC 170 Two Sum III design) | Counter of values under a lock; `find` iterates keys — expensive under a lock; for read-heavy use a RW lock or copy-on-write snapshot. |
| Constraint change: duplicates, or return all pairs | Use a Counter; handle `x == target - x` needing count ≥ 2; for all unique pairs sort + two pointers skipping duplicates. |

## 7. Worked Example: Top K Frequent Elements

**Base:** Counter + heap of size k: O(n log k); or bucket sort O(n).

| Follow-up | Answer |
|---|---|
| Stream | Exact: maintain counts + a structure ordered by count (hash map + count buckets gives O(1) increments, like LFU). Bounded memory: **count-min sketch + min-heap of k candidates**, or **Misra–Gries / Space-Saving** (guaranteed to find items with frequency > n/k). |
| Too big / distributed | MapReduce word count: map emits (item, 1), combiner sums locally, shuffle by item hash, reduce sums; then each reducer keeps a local top-k and a final merge takes the global top-k. **Precision:** local top-k then merge is exact only if you merge full counts for candidates; with approximation, oversample (keep top 10k per shard). |
| Many queries for different k | Sort items by count once (O(u log u)); each query is a prefix. |
| Concurrent | Sharded counters (lock per shard) + periodic merge into a published snapshot that queries read lock-free. |
| Time-windowed ("top k in the last hour") | Per-minute buckets of counts (or sketches) in a ring; sum the last 60 buckets; subtract the expiring bucket. This is the top-K trending system design problem. |

## 8. Worked Example: Merge Intervals

**Base:** sort by start, merge overlapping. O(n log n).

| Follow-up | Answer |
|---|---|
| Stream of intervals | Keep merged disjoint intervals in a balanced BST / sorted list keyed by start; each insert finds neighbors by binary search and merges with the (possibly several) overlapping ones. O(log n + merged) per insert (LC 352, LC 715 Range Module). |
| Doesn't fit | External sort by start, then a single streaming merge pass (only the current merged interval is held in memory). |
| Many "is point x covered?" queries | Binary search over the merged, sorted list: O(log n). |
| Concurrent inserts | Lock around the sorted structure; or per-range shards (by coordinate) with care for intervals crossing shard boundaries. |
| Constraint change: touching intervals [1,2],[2,3] | Decide whether closed or half-open; the comparison changes from `<` to `<=`. |

## 9. Worked Example: LRU Cache

**Base:** hash map + doubly linked list, O(1) get/put.

| Follow-up | Answer |
|---|---|
| Thread-safe | One mutex around both operations (`get` mutates recency). Scale with lock striping: N independent LRU shards chosen by key hash (approximate global LRU). |
| Too big for one machine | Distributed cache: consistent hashing across nodes, per-node LRU. Replication for hot keys. That's the distributed cache design problem. |
| Values expensive to compute | Single-flight: concurrent misses for the same key wait on one in-flight computation. |
| TTL expiry | Store expiry time; check lazily on `get`; a background sweeper or a timing wheel / heap for proactive eviction. |
| Constraint change: evict least *frequently* used | LFU: key → node, frequency → doubly linked list, track `min_freq` (`PyDSA/25_design/008`). |
| Cache miss storms after restart | Warm-up from a snapshot or gradual traffic ramp. |

## 10. Worked Example: Number of Islands

**Base:** BFS/DFS flood fill, O(m·n).

| Follow-up | Answer |
|---|---|
| Grid arrives row by row (stream) | Keep only the previous row's component labels + a Union-Find for merges; count components that close (no continuation in the new row). O(n) memory per row. |
| Grid too big for one machine | Split into tiles; label islands within each tile; then Union-Find merges labels across tile boundaries using only the border rows/columns. |
| Many queries: "which island is (r, c) in?" | Precompute a label per cell once; O(1) per query. |
| Land added over time (LC 305 Number of Islands II) | Union-Find: each new land cell unions with land neighbors; count = components. ~O(α) per addition. |
| Concurrent updates | Union-Find with a lock (or lock-free concurrent union-find in research systems); readers of the count read an atomic. |
| Very deep recursion | Iterative BFS/stack; recursive DFS hits Python's recursion limit on large grids. |

## 11. Worked Example: Median of a Data Stream

**Base:** two heaps, O(log n) add, O(1) median.

| Follow-up | Answer |
|---|---|
| All values in [0, 100] | Counting array of 101 buckets; median by scanning counts: O(100) query, O(1) add. |
| 99% of values in [0, 100] | Counting array for the range + two counters (or small heaps) for outliers below/above. |
| Can't store the stream | Approximate quantiles: t-digest / KLL sketch, mergeable across machines, error bounded by ε. |
| Distributed | Each machine keeps a mergeable sketch; merge sketches for the global median. Exact distributed median: binary search on value with counting passes. |
| Sliding window | Two heaps with lazy deletion (`PyDSA/12_heap_priority_queue/012`). |
| Concurrent | Lock around both heaps (they must stay balanced together). |

## 12. How to Answer Any Follow-up in 60 Seconds

1. **Name what breaks** in the current solution ("the hash map grows without bound").
2. **Name the technique family** from the toolkits above.
3. **State the trade-off** (exact → approximate, O(1) memory → error bound, latency → precomputation cost).
4. **Offer the simple version first**, then the scalable one if they want more.

> "Storing every value won't work for an unbounded stream. If an approximate answer is acceptable, I'd keep a count-min sketch with a size-k heap of candidates: fixed memory, overestimates bounded by ε·n. If it must be exact, we need memory proportional to distinct items, so I'd partition by item hash across machines and merge per-shard top-k."

## 13. Stream Algorithms You Can Write in the Interview

Naming a sketch earns some credit; writing a small one correctly earns much more. These
three fit in a few lines each, and each comes with a guarantee you should state along
with it. The script checks every guarantee against the exact answer
(`python3 streaming.py`):

```python
"""Three stream algorithms you can write in an interview, each checked against the exact answer."""
import random
from collections import Counter


def reservoir_sample(stream, k, rng):
    """Uniform random sample of k items from a stream of unknown length, in O(k) memory."""
    sample = []
    for i, x in enumerate(stream):               # i = number of items seen before x
        if i < k:
            sample.append(x)
        else:
            j = rng.randrange(i + 1)              # keep x with probability k / (i + 1)
            if j < k:
                sample[j] = x                     # it evicts a uniformly chosen current member
    return sample


def misra_gries(stream, k):
    """At most k-1 counters. Every item with frequency > n/k is guaranteed to survive;
    each surviving count underestimates the true count by at most n/k."""
    counters = {}
    for x in stream:
        if x in counters:
            counters[x] += 1
        elif len(counters) < k - 1:
            counters[x] = 1
        else:                                     # no room: decrement everyone (x's own +1 cancels too)
            for key in list(counters):
                counters[key] -= 1
                if counters[key] == 0:
                    del counters[key]
    return counters


class CountMin:
    """Count-min sketch: d rows of w counters. Never underestimates; overestimates by at most
    (e/w) * n with probability >= 1 - e^-d."""
    def __init__(self, w, d, seed=0):
        rng = random.Random(seed)
        self.w, self.rows = w, [[0] * w for _ in range(d)]
        # One independent hash per row: ((a*h + b) mod p) mod w, a universal hash family.
        self.p = (1 << 61) - 1
        self.coeffs = [(rng.randrange(1, self.p), rng.randrange(self.p)) for _ in range(d)]

    def _cols(self, x):
        h = hash(x)
        return [((a * h + b) % self.p) % self.w for a, b in self.coeffs]

    def add(self, x):
        for row, c in zip(self.rows, self._cols(x)):
            row[c] += 1

    def estimate(self, x):
        return min(row[c] for row, c in zip(self.rows, self._cols(x)))


if __name__ == "__main__":
    rng = random.Random(0)

    # Reservoir: each of 10 items should appear in a size-3 sample 30% of the time.
    hits = Counter()
    for _ in range(100_000):
        hits.update(reservoir_sample(range(10), 3, rng))
    print("reservoir inclusion rates:", " ".join(f"{hits[i] / 100_000:.3f}" for i in range(10)))

    # A skewed stream: a few heavy hitters and a long tail.
    stream = ["a"] * 3_000 + ["b"] * 2_000 + ["c"] * 1_200 + [f"t{i % 3_000}" for i in range(13_800)]
    rng.shuffle(stream)
    n, exact = len(stream), Counter(stream)

    k = 10                                        # guarantee: anything above n/k = 2,000 survives
    mg = misra_gries(stream, k)
    print(f"misra-gries kept {len(mg)} counters; true heavy (> n/k={n // k}):",
          sorted(x for x, c in exact.items() if c > n / k),
          "| a:", mg.get("a"), "of", exact["a"], "b:", mg.get("b"), "of", exact["b"])

    cm = CountMin(w=272, d=5)                     # e/w ~ 1% of n
    for x in stream:
        cm.add(x)
    errors = [cm.estimate(x) - c for x, c in exact.items()]
    bound = 2.718 / 272 * n                       # e/w * n, per query with prob >= 1 - e^-5
    assert min(errors) >= 0                       # never underestimates
    print(f"count-min: {5 * 272} counters for {len(exact)} distinct items; "
          f"bound e/w*n = {bound:.0f}; items over it: {sum(e > bound for e in errors)}; "
          f"a ~ {cm.estimate('a')} (true {exact['a']})")
```

Output (verified with Python 3.11; the count-min numbers vary slightly between runs
because Python randomizes `str` hashes per process):

```text
reservoir inclusion rates: 0.300 0.300 0.300 0.301 0.298 0.299 0.301 0.298 0.302 0.302
misra-gries kept 9 counters; true heavy (> n/k=2000): ['a'] | a: 1128 of 3000 b: 131 of 2000
count-min: 1360 counters for 3003 distinct items; bound e/w*n = 200; items over it: 0; a ~ 3037 (true 3000)
```

What to say about each:

- **Reservoir sampling (Algorithm R).** After seeing i + 1 items, every item is in the
  sample with probability k/(i + 1). Proof sketch by induction: the new item enters
  with probability k/(i + 1); an item already in the sample survives this step unless
  the new item enters *and* picks its slot, so it stays with probability
  1 − (k/(i + 1))·(1/k) = i/(i + 1), and k/i · i/(i + 1) = k/(i + 1). The measured
  inclusion rates are all 0.300 ± 0.002, as they should be. Use it for "pick k random
  lines from a file you can read only once" (LeetCode 382 and 398 are the k = 1 case).
- **Misra–Gries (heavy hitters).** With k − 1 counters, every item that occurs more than
  n/k times is guaranteed to be among the survivors, and each surviving counter
  undercounts by at most n/k (here "a" kept 1,128 of 3,000: an undercount of 1,872,
  within the bound of 2,000). It gives **candidates, not counts**: make a second pass
  (or keep exact counts only for the candidates) when the answer must be exact. It is
  the k-counter generalisation of Boyer–Moore majority voting (k = 2).
- **Count-min sketch (frequencies).** d rows of w counters, one hash function per row;
  add increments one counter in each row, and the estimate is the minimum across rows.
  Collisions only ever *add*, so it never underestimates; with w = ⌈e/ε⌉ and
  d = ⌈ln(1/δ)⌉ the overestimate is at most ε·n with probability at least 1 − δ.
  Here 1,360 counters summarized 3,003 distinct items. The guarantee is *per query*:
  with d = 5, each estimate exceeds the bound with probability at most e⁻⁵ ≈ 0.7%, so
  across 3,000 items a few outliers are allowed, and the script counts them. Note the
  row hashes come from a universal family ((a·h + b) mod p) mod w with independent
  random a, b per row. A first version of this script instead hashed `(salt, x)`
  tuples with Python's built-in `hash`, and on some runs a tail item collided with a
  heavy item in every row: built-in hashes aren't designed to act as independent hash
  functions, and the analysis assumes they are. Pair it with a size-k min-heap of candidates for "top-k in a
  stream". Sketches built with the same hash functions **merge** by adding counters,
  which is what makes them work across machines.

For distinct counts (HyperLogLog), quantiles (t-digest, KLL) and membership (Bloom
filters), see [Specialized Data Structures and Indexes](../SystemDesign/building_blocks/20_specialized_data_structures.md); you're
rarely asked to write those, but you should know their memory/error trade-offs from
§1's table.

## 14. External Merge Sort, Runnable

"Sort 1 TB with 16 GB of RAM" is the canonical doesn't-fit-in-memory follow-up, and
it's also how databases sort for `ORDER BY` and merge joins when data exceeds their
work memory ([Database Storage Engines & Advanced Structures](03_databases_deep_dive.md) §8). Two passes:

1. **Run generation:** read memory-sized chunks, sort each in RAM, write each as a
   sorted **run** to disk.
2. **k-way merge:** open all runs and repeatedly emit the smallest head, using a
   min-heap of size k (one entry per run) — exactly "merge k sorted lists".

Scaled down so it runs in a second: one million numbers with a budget of 100,000 in
memory (`python3 external_sort.py`):

```python
"""External merge sort: sort a file far larger than the memory budget, then check the result."""
import heapq
import os
import random
import tempfile

MEMORY_BUDGET = 100_000                     # at most this many numbers held in RAM at once

def write_input(path, n, seed=0):
    rng = random.Random(seed)
    with open(path, "w") as f:
        for _ in range(n):
            f.write(f"{rng.randrange(10**9)}\n")

def make_runs(path, tmpdir):
    """Pass 1: read budget-sized chunks, sort each in memory, write each as a sorted run."""
    runs, chunk = [], []
    def flush():
        chunk.sort()
        run = os.path.join(tmpdir, f"run{len(runs)}.txt")
        with open(run, "w") as out:
            out.writelines(f"{x}\n" for x in chunk)
        runs.append(run)
        chunk.clear()
    with open(path) as f:
        for line in f:
            chunk.append(int(line))
            if len(chunk) == MEMORY_BUDGET:
                flush()
    if chunk:
        flush()
    return runs

def merge_runs(runs, out_path):
    """Pass 2: k-way merge. heapq.merge keeps one 'current' line per run in a size-k heap."""
    files = [open(r) for r in runs]
    try:
        with open(out_path, "w") as out:
            for x in heapq.merge(*((int(line) for line in f) for f in files)):
                out.write(f"{x}\n")
    finally:
        for f in files:
            f.close()

with tempfile.TemporaryDirectory() as tmp:
    src, dst = os.path.join(tmp, "input.txt"), os.path.join(tmp, "sorted.txt")
    write_input(src, 1_000_000)
    runs = make_runs(src, tmp)
    merge_runs(runs, dst)
    with open(dst) as f:
        prev, count = -1, 0
        for line in f:                      # verify in one streaming pass, O(1) memory
            x = int(line); assert x >= prev; prev, count = x, count + 1
    print(f"sorted {count:,} numbers with a {MEMORY_BUDGET:,}-number budget: "
          f"{len(runs)} runs, one {len(runs)}-way merge, output verified in order")
```

Output (verified with Python 3.11):

```text
sorted 1,000,000 numbers with a 100,000-number budget: 10 runs, one 10-way merge, output verified in order
```

The numbers to reason with in the interview: both passes read and write the data once,
so the cost is about **4 × data size of sequential I/O** (read + write per pass); with
16 GB of memory and 1 TB of data there are ~64 runs, and a 64-way merge needs only a
buffer per run. If the runs outnumber the file handles or buffers you can afford, merge
in several rounds (each round multiplies the run length by the fan-in, so
log_fan-in(runs) rounds). The same structure appears as the sort-and-spill phase in
MapReduce/Spark and as compaction in LSM trees.

## 15. Distributed Top-K: the Merge That Looks Right and Isn't

The most common mistake in the distributed follow-up to Top K Frequent (§7): "each
machine computes its local top-k and a coordinator merges them." That's only correct
when every key's full count lives on one machine. If each web server logged its own
events, an item that's moderately popular *everywhere* can be the global winner while
never making any single machine's top-k (`python3 topk_shards.py`):

```python
"""Distributed top-k: why 'top-k per machine, then merge' is wrong unless each key lives on one machine."""
import heapq
from collections import Counter

K, MACHINES = 3, 4
# Each web server logged its own events. "x" is the most popular item overall (4 x 5 = 20),
# but on every single server three local items beat it.
logs = [["x"] * 5 + [f"a{m}"] * (9 + m) + [f"b{m}"] * 7 + [f"c{m}"] * 6 for m in range(MACHINES)]

def top_k(counter, k):
    return heapq.nlargest(k, counter.items(), key=lambda kv: kv[1])

truth = [item for item, _ in top_k(Counter(e for log in logs for e in log), K)]

# Wrong: each server sends only its local top-k; the coordinator adds them up.
merged = Counter()
for log in logs:
    for item, n in top_k(Counter(log), K):
        merged[item] += n
wrong = [item for item, _ in top_k(merged, K)]

# Right: shuffle first. Route every event to reducer hash(item) % MACHINES, so each item's
# FULL count is on exactly one reducer; a reducer's local top-k is then exact for its keys.
reducers = [Counter() for _ in range(MACHINES)]
for log in logs:
    for e in log:
        reducers[hash(e) % MACHINES][e] += 1
candidates = [kv for r in reducers for kv in top_k(r, K)]
right = [item for item, _ in heapq.nlargest(K, candidates, key=lambda kv: kv[1])]

print("true top-3:           ", truth)
print("local top-3, merged:  ", wrong, "  <- x never made a local top-3")
print("shuffle, then top-3:  ", right)
assert right == truth and wrong != truth
```

Output (verified with Python 3.11):

```text
true top-3:            ['x', 'a3', 'a2']
local top-3, merged:   ['a3', 'a2', 'a1']   <- x never made a local top-3
shuffle, then top-3:   ['x', 'a3', 'a2']
```

"x" has 20 events in total, more than any other item, but only 5 on each server, where
three local items beat it. The local-top-k merge never sees it. The fix is the
**shuffle** from §2: route each event by `hash(item)` first so one reducer holds each
item's *complete* count; then per-reducer top-k followed by a merge is exact. The
shuffle moves data over the network, which is why a **combiner** (pre-aggregating
`(item, count)` per machine before the shuffle, as in §2's diagram) matters: it sends
one record per distinct item per machine instead of one per event.

**Precision note:** if you can't afford the shuffle, the approximate answers are
(a) per-machine count-min sketches merged by adding counters, plus candidate lists
that are oversampled (keep far more than k per machine) and then counted exactly in a
second pass, or (b) threshold algorithms that bound what an unseen item could have
scored. Say which guarantee you're keeping.

## Practice

After every problem in the curriculum, write one line per follow-up (stream / memory / queries / threads / constraint). If you can't, that's the next thing to study.

## What Each Engineering Level Should Know

Not everyone reading this file needs every sentence of it cold. This table maps this
chapter's material onto a standard industry ladder *and* the Google-style ladder this
repo's interview content is written against, side by side. The mapping between
company-specific titles and levels is approximate and varies by company, but the
*depth of understanding* described in each row is a reliable signal regardless of
which company uses which label. Use it as a syllabus (read down a column) or as a
self-assessment (find the cell that matches where a real interview would place you).

| Topic in this chapter | Junior / New Grad (Google L3) | Mid-Level (Google L4) | Senior (Google L5) | Staff+ (Google L6–L7) |
|---|---|---|---|---|
| **Reading the follow-up** (Foundations, §12) | Treats a follow-up as a new problem and starts over | Recognises which assumption changed, with a nudge | Names what breaks, the technique family and the trade-off within a minute, simple version first | Reframes the follow-up into the production question behind it (SLOs, cost, failure modes) |
| **Streams** (§1, §13) | Knows you can keep running totals | Uses a heap of size k and a monotonic deque for windows | Writes reservoir sampling and Misra–Gries, and explains count-min's ε/δ guarantee and mergeability | Chooses sketches and accuracy budgets for a real metrics or analytics pipeline |
| **Too big / distributed** (§2, §14–§15) | Says "use more machines" | Knows external sort and hash partitioning exist | Walks through external merge sort with I/O cost, shuffles by key, and explains why local top-k merging is wrong | Designs around skew, stragglers and shuffle cost; knows when approximate is the right product answer |
| **Many queries** (§3) | Caches results | Uses prefix sums and hash sets to precompute | Picks Fenwick/segment trees, sparse tables or indexes by update/query mix and states the precompute cost | Weighs precomputation storage and invalidation against query latency across a system |
| **Concurrency** (§4) | Adds a lock around everything | Identifies shared mutable state and check-then-act races | Locks invariants, not fields; shards hot structures; uses single-flight and snapshots | Chooses consistency and contention strategies for shared services, not just in-process structures |
| **Changed constraints** (§5) | Tries the same algorithm again | Knows negatives break sliding windows and Dijkstra | Maps each constraint change to what breaks and the replacement algorithm immediately | Uses the constraint change to discuss product requirements and edge cases the spec missed |
| **Worked problems** (§6–§11) | Solves the base problems | Answers one or two follow-ups per problem | Answers all five follow-ups for each worked problem with bounds | Connects each follow-up to the matching system-design problem and its trade-offs |

**Reading this table as a study plan:** if you're aiming at a Senior/L5 bar, your
target is the whole "Senior" column, which the numbered sections (1–15) deliver in
full. The Foundations section alone takes you to roughly the "Mid-Level" column. The
"Staff+" column is judgment that mostly comes from operating real systems at scale;
this file gives you the vocabulary to have that conversation, not a substitute for
having had it.

## Interview checklist

- [ ] I can name the assumption a follow-up removes and what breaks in my solution because of it.
- [ ] I can answer stream, too-big, many-queries, threads and changed-constraint follow-ups for any problem I've solved.
- [ ] I can write reservoir sampling and Misra–Gries, and state their guarantees.
- [ ] I can explain a count-min sketch's error bound (ε·n with probability 1 − δ) and why sketches merge.
- [ ] I can walk through external merge sort and estimate its I/O cost.
- [ ] I can explain hash partitioning, the shuffle, combiners and skew.
- [ ] I can show why "local top-k, then merge" is wrong unless keys are partitioned, and fix it.
- [ ] I can pick a precomputation (prefix sums, Fenwick tree, sparse table) from the query/update mix.
- [ ] I can say what needs locking, lock invariants rather than fields, and name single-flight.
- [ ] I always offer the simple version first and state the trade-off of the scalable one.

Related: [Concurrency](05_concurrency_deep_dive.md), [Complexity Analysis](07_complexity_analysis_deep_dive.md), [Data Structure Internals](06_data_structure_internals_deep_dive.md) §14, [Specialized Data Structures and Indexes](../SystemDesign/building_blocks/20_specialized_data_structures.md), [Batch and Stream Processing](../SystemDesign/building_blocks/21_batch_and_stream_processing.md).
