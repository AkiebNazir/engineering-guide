# Google-Style Follow-Ups — Scaling a Coding Answer

This is the capstone of the module — read it after files `01`–`09`, once you can
already solve a base coding problem confidently. It takes that solved problem and
stretches it exactly the way a strong interviewer does. After you solve the problem,
a Google interviewer often changes it:

1. **What if the input is a stream and you can't store it all?**
2. **What if the data doesn't fit in memory, or is spread across many machines?**
3. **What if there are millions of queries? What would you precompute?**
4. **What if multiple threads call this at once? What needs locking?**
5. **What if a constraint changes — negative numbers, duplicates, a graph with cycles?**

These follow-ups are where coding rounds turn into small system-design conversations, and they're a strong L5 signal. This file gives you a toolkit for each, then works through six common problems with all five follow-ups.

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

Details on the probabilistic structures: `SystemDesign/building_blocks/20_specialized_data_structures.md`.

## 2. Toolkit: Doesn't Fit in Memory / Many Machines

| Problem shape | Technique |
|---|---|
| Sort huge data | **External merge sort**: sort chunks that fit in <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>, write runs, k-way merge with a heap (`PyDSA` merge k sorted lists) |
| Count / group / join | **Hash partitioning**: route each record to one of P files/machines by `hash(key) % P` so equal keys meet; process each partition independently (**MapReduce** shuffle) |
| Top-k over huge data | Partition by key, compute per-partition counts, keep per-partition top-k, merge. For approximate: count-min sketches merged across machines |
| Deduplicate | Hash partition, then dedupe within each partition; or a Bloom filter pass first |
| Two-sum style lookups | Partition both sides by the same hash so matching pairs land together |
| Graph too big | Partition vertices; iterative message passing (Pregel-style BSP), label propagation for connected components |
| Median of huge data | Binary search on the value: count elements ≤ mid in a distributed pass (log(range) passes), or approximate quantile sketches |
| Data spread over machines, need a global order | Range partitioning with sampled split points (like TeraSort) |

Always mention: **network is the bottleneck** (minimize shuffles), **skew** (one hot key overloads a partition — salt it), and **stragglers/failures** (retries, speculative execution).

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
| Tree distance / <abbr title="Lowest Common Ancestor. In a tree or directed acyclic graph, the lowest node that has both given nodes as descendants.">LCA</abbr> | Binary lifting or Euler tour + sparse table | O(log n) / O(1) |
| Connectivity with only edge additions | Union-Find | ~O(1) |
| Repeated identical queries | Memoization / caching (<abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr>) | O(1) on hit |
| Geo "nearby" | Geohash / quadtree / S2 index | O(log n + results) |

Name the trade-off: **precomputation time and memory vs query latency**, and how updates invalidate precomputed data.

## 4. Toolkit: Concurrency (What Needs Locking?)

See `05_concurrency_deep_dive.md` for primitives. The answer structure:
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
| Directed instead of undirected | Union-Find for cycle detection doesn't apply | <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> with recursion-stack colors |
| Weighted instead of unweighted | <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> no longer gives shortest paths | Dijkstra; 0-1 <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr> if weights are 0/1 |
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
| Stream | Exact: maintain counts + a structure ordered by count (hash map + count buckets gives O(1) increments, like <abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr>). Bounded memory: **count-min sketch + min-heap of k candidates**, or **Misra–Gries / Space-Saving** (guaranteed to find items with frequency > n/k). |
| Too big / distributed | MapReduce word count: map emits (item, 1), combiner sums locally, shuffle by item hash, reduce sums; then each reducer keeps a local top-k and a final merge takes the global top-k. **Precision:** local top-k then merge is exact only if you merge full counts for candidates; with approximation, oversample (keep top 10k per shard). |
| Many queries for different k | Sort items by count once (O(u log u)); each query is a prefix. |
| Concurrent | Sharded counters (lock per shard) + periodic merge into a published snapshot that queries read lock-free. |
| Time-windowed ("top k in the last hour") | Per-minute buckets of counts (or sketches) in a ring; sum the last 60 buckets; subtract the expiring bucket. This is the top-K trending system design problem. |

## 8. Worked Example: Merge Intervals

**Base:** sort by start, merge overlapping. O(n log n).

| Follow-up | Answer |
|---|---|
| Stream of intervals | Keep merged disjoint intervals in a balanced <abbr title="Binary Search Tree. A node-based binary tree data structure where the left subtree has smaller values and the right subtree has larger values than the parent node.">BST</abbr> / sorted list keyed by start; each insert finds neighbors by binary search and merges with the (possibly several) overlapping ones. O(log n + merged) per insert (LC 352, LC 715 Range Module). |
| Doesn't fit | External sort by start, then a single streaming merge pass (only the current merged interval is held in memory). |
| Many "is point x covered?" queries | Binary search over the merged, sorted list: O(log n). |
| Concurrent inserts | Lock around the sorted structure; or per-range shards (by coordinate) with care for intervals crossing shard boundaries. |
| Constraint change: touching intervals [1,2],[2,3] | Decide whether closed or half-open; the comparison changes from `<` to `<=`. |

## 9. Worked Example: <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> Cache

**Base:** hash map + doubly linked list, O(1) get/put.

| Follow-up | Answer |
|---|---|
| Thread-safe | One mutex around both operations (`get` mutates recency). Scale with lock striping: N independent <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> shards chosen by key hash (approximate global <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr>). |
| Too big for one machine | Distributed cache: consistent hashing across nodes, per-node <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr>. Replication for hot keys. That's the distributed cache design problem. |
| Values expensive to compute | Single-flight: concurrent misses for the same key wait on one in-flight computation. |
| TTL expiry | Store expiry time; check lazily on `get`; a background sweeper or a timing wheel / heap for proactive eviction. |
| Constraint change: evict least *frequently* used | <abbr title="Least Frequently Used. A cache replacement policy that discards the least frequently used items first.">LFU</abbr>: key → node, frequency → doubly linked list, track `min_freq` (`PyDSA/25_design/008`). |
| Cache miss storms after restart | Warm-up from a snapshot or gradual traffic ramp. |

## 10. Worked Example: Number of Islands

**Base:** <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/<abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> flood fill, O(m·n).

| Follow-up | Answer |
|---|---|
| Grid arrives row by row (stream) | Keep only the previous row's component labels + a Union-Find for merges; count components that close (no continuation in the new row). O(n) memory per row. |
| Grid too big for one machine | Split into tiles; label islands within each tile; then Union-Find merges labels across tile boundaries using only the border rows/columns. |
| Many queries: "which island is (r, c) in?" | Precompute a label per cell once; O(1) per query. |
| Land added over time (LC 305 Number of Islands II) | Union-Find: each new land cell unions with land neighbors; count = components. ~O(α) per addition. |
| Concurrent updates | Union-Find with a lock (or lock-free concurrent union-find in research systems); readers of the count read an atomic. |
| Very deep recursion | Iterative <abbr title="Breadth-First Search. An algorithm for traversing or searching tree or graph data structures level by level.">BFS</abbr>/stack; recursive <abbr title="Depth-First Search. An algorithm for traversing or searching tree or graph data structures by exploring as far as possible along each branch before backtracking.">DFS</abbr> hits Python's recursion limit on large grids. |

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

## Practice

After every problem in the curriculum, write one line per follow-up (stream / memory / queries / threads / constraint). If you can't, that's the next thing to study.

Related: `05_concurrency_deep_dive.md`, `07_complexity_analysis_deep_dive.md`, `SystemDesign/building_blocks/20_specialized_data_structures.md`, `21_batch_and_stream_processing.md`.
