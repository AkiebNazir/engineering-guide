# Specialized Data Structures and Indexes

General-purpose databases answer "give me the row with this key" very well. Many system design problems hinge on a different question — "have I seen this before?", "how many distinct users?", "which drivers are within 2 km?", "which documents contain these words?", "who is in the top 100?" — where a purpose-built structure is orders of magnitude cheaper. Naming the right one, and its trade-off, is a strong depth signal.

> 💡 The pattern behind almost all of these: give up exactness, generality, or update cost in exchange for bounded memory or sub-linear query time. Say which one you are giving up.

| Question | Structure | Gives up | Used in |
|---|---|---|---|
| Is X definitely not in the set? | Bloom filter | Occasional false "maybe yes" | LSM-tree reads, crawler URL dedup, CDN cache filters |
| How many distinct items? | HyperLogLog | ~1–2% error | Unique visitors, distinct search queries |
| How often has X occurred? | Count-min sketch | Overcounts, never undercounts | Heavy hitters, top-K trending, rate limiting at scale |
| What is nearby? | Geohash, quadtree, S2 cells | Boundary handling, cell-size tuning | Maps, ride dispatch, delivery |
| Which documents contain these terms? | Inverted index | Write cost, index size | Web search, log search, product search |
| Who is in the top N / what is my rank? | Sorted set (skip list) | Memory; sharding makes global rank hard | Leaderboards, priority queues, delayed jobs |
| Have two replicas diverged, and where? | Merkle tree | Maintenance on every write | Anti-entropy, Git, certificate transparency |
| Write-optimised key-value storage | LSM tree (memtable + SSTables) | Read and space amplification, compaction | Bigtable, Cassandra, RocksDB |

## Bloom filters

A Bloom filter is a bit array of `m` bits and `k` hash functions. To insert an item, set the `k` bits it hashes to. To query, check those `k` bits: if any is 0, the item was **definitely never inserted**; if all are 1, it was **probably** inserted.

- False-positive rate ≈ `(1 − e^(−kn/m))^k`. The optimal `k ≈ (m/n) · ln 2`.
- Rule of thumb: about **10 bits per item** with `k = 7` gives roughly a 1% false-positive rate — a few megabytes for a million items, regardless of item size.
- No false negatives, but no deletes either (use a counting Bloom filter or a cuckoo filter if you need them).

Where it earns its place:

1. **LSM-tree reads** — each SSTable carries a Bloom filter so a lookup skips files that cannot contain the key (Bigtable, Cassandra, RocksDB).
2. **Web crawler** — "have I already queued this URL?" across billions of URLs without a giant hash set; an occasional false positive just skips a page.
3. **Avoiding expensive lookups** — check a local filter before a network call to a cache or database for keys that mostly do not exist.

## HyperLogLog

HyperLogLog estimates the number of distinct elements using a few kilobytes. It hashes each item and tracks, per bucket, the maximum number of leading zeros seen; long runs of zeros are unlikely, so they reveal how many distinct hashes must have been seen. With 2¹⁴ buckets (~12 KB) the standard error is about 0.8%.

Two properties make it ideal for distributed counting: sketches **merge** (take the per-bucket maximum), so you can count per server, per hour, or per shard and combine them later; and the size is **constant** no matter how many items you add. Redis (`PFADD`/`PFCOUNT`) and BigQuery's `APPROX_COUNT_DISTINCT` use it.

## Count-min sketch

A count-min sketch is a `d × w` grid of counters with one hash function per row. To add an item, increment one counter in each row. To estimate its count, take the **minimum** across its `d` counters. Collisions only add, so estimates never undercount; with `w = ⌈e/ε⌉` and `d = ⌈ln(1/δ)⌉` the overcount is at most `εN` with probability `1 − δ`.

Typical use: **top-K / heavy hitters** in a stream. Keep a count-min sketch for frequencies plus a small min-heap of the current top K candidates; when an item's estimate exceeds the heap minimum, swap it in. Sketches from many servers merge by adding counters cell by cell, and windowed variants (one sketch per minute, sum the last 60) give "trending in the last hour".

## Geospatial indexes

Latitude and longitude are two dimensions; B-trees index one. The trick is to map 2D space into keys where nearby points get nearby keys.

| Approach | How it works | Strengths | Weaknesses |
|---|---|---|---|
| Geohash | Interleave latitude and longitude bits and base-32 encode them; each extra character narrows the cell ~32×. Nearby points share a prefix. | Plain strings: store in any key-value store or B-tree, range-scan by prefix, shard by prefix. | Cells are rectangles of fixed size; two close points can straddle a boundary, so query the cell and its 8 neighbours. Uneven density. |
| Quadtree | Recursively split a square into four children when it holds more than `k` points. | Adapts to density: small cells downtown, big cells in the countryside. | An in-memory tree that must be rebuilt or rebalanced as points move. |
| S2 cells (Google) | Project the sphere onto a cube, then a Hilbert curve orders cells at 30 levels; each cell ID is a 64-bit integer. | Works on the sphere without pole distortion; a region is a small set of cell ID ranges; cell IDs sort locality-preserving. | More complex; you use the library rather than re-derive it. |
| R-tree / PostGIS | Bounding-box tree over shapes. | Arbitrary polygons, intersections. | Heavier updates; less natural to shard. |

For moving objects (drivers updating every few seconds) the usual design is: an in-memory index per region keyed by cell ID, drivers re-indexed on each update, and queries that scan the rider's cell plus neighbours at a precision where each cell holds a manageable number of drivers.

## Inverted indexes and ranking

An inverted index maps each **term** to a **posting list**: the sorted document IDs containing it, often with positions and term frequencies. A query `"distributed cache"` intersects the posting lists for both terms (sorted lists intersect in linear time, and skip pointers make it faster).

Ranking basics to name:

- **TF-IDF**: a term matters more if it appears often in the document (term frequency) and rarely across the corpus (inverse document frequency).
- **BM25**: the practical successor — term frequency saturates (the 10th occurrence adds little) and scores are normalised by document length. The default in Elasticsearch/Lucene.
- Real web search combines hundreds of signals (links such as PageRank, freshness, click data, learned models) in a multi-stage pipeline: cheap retrieval of thousands of candidates, then expensive re-ranking of the top few hundred.

At scale the index is **sharded by document** (each shard holds a complete mini-index over a subset of documents, a query fans out to all shards and merges the top results) rather than by term (which creates huge hot shards for common words). Fan-out makes tail latency the dominant concern — see [18_back_of_envelope_estimation.md](18_back_of_envelope_estimation.md).

## Sorted sets and leaderboards

A sorted set keeps members ordered by score with `O(log n)` insert, update, and rank queries. Redis implements it with a **skip list** (a linked list with express lanes) plus a hash map from member to score.

- `ZINCRBY leaderboard 50 alice` updates a score; `ZREVRANK leaderboard alice` gives her rank; `ZREVRANGE leaderboard 0 99` gives the top 100.
- One Redis instance comfortably holds tens of millions of members. Beyond that, shard by a natural boundary (per game, per region, per week) so each board fits on one node.
- A *global* rank across shards is the hard part: either keep a single top-N board fed by per-shard top-Ns, or bucket scores into ranges (a histogram of how many players have each score band) and compute approximate rank for everyone outside the top.

## Merkle trees

A Merkle tree hashes data blocks at the leaves and hashes pairs of children up to a single root. Two copies of a dataset are identical if their roots match; if not, comparing children finds the differing blocks in `O(log n)` hash comparisons. Uses: replica anti-entropy in Dynamo-style stores ([19_consensus_and_coordination.md](19_consensus_and_coordination.md)), Git objects, blockchains, and verifiable logs.

## LSM trees and SSTables

A **log-structured merge tree** turns random writes into sequential ones: writes go to a write-ahead log and an in-memory sorted **memtable**; when it fills, it is flushed to an immutable sorted file (**SSTable**). Background **compaction** merges SSTables, dropping overwritten and deleted values.

| | LSM tree | B-tree |
|---|---|---|
| Writes | Sequential appends; very high throughput | In-place page updates; random I/O |
| Reads | May check several files (Bloom filters help) | One root-to-leaf path |
| Write amplification | Compaction rewrites data several times | Page splits, full-page WAL writes |
| Space | Temporary duplicates until compaction | Fragmentation in partially full pages |
| Good fit | Write-heavy, time series, logs, wide-column (Bigtable, Cassandra) | Read-heavy OLTP with many updates (PostgreSQL, MySQL) |

## Related building blocks

- [06_database_internals.md](06_database_internals.md)
- [07_caching.md](07_caching.md)
- [21_batch_and_stream_processing.md](21_batch_and_stream_processing.md)
- [25_partitioning_and_hot_keys.md](25_partitioning_and_hot_keys.md)
