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

```arch
%% caption: Geohashing converts 2D coordinates into a 1D string where a shared prefix implies spatial proximity, allowing B-tree range queries.
node latlon "Point (Lat, Lon)" at 0,1 icon=internet color=blue
node hash "Geohash (e.g. 9q8yy)" at 2,1 icon=code color=amber
group db "Standard B-Tree DB" color=slate style=dashed
node prefix "Prefix Range Query\n(WHERE hash LIKE '9q8%')" at 4,0 in db icon=search color=green
node pts "Points in bounding box" at 4,2 in db icon=db color=green

latlon -> hash : "encode\n(interleave bits)"
hash -> prefix : "query\nneighborhood"
prefix -> pts : "returns"
```

## Inverted indexes and ranking

An inverted index maps each **term** to a **posting list**: the sorted document IDs containing it, often with positions and term frequencies. A query `"distributed cache"` intersects the posting lists for both terms (sorted lists intersect in linear time, and skip pointers make it faster).

Ranking basics to name:

- **TF-IDF**: a term matters more if it appears often in the document (term frequency) and rarely across the corpus (inverse document frequency).
- **BM25**: the practical successor — term frequency saturates (the 10th occurrence adds little) and scores are normalised by document length. The default in Elasticsearch/Lucene.
- Real web search combines hundreds of signals (links such as PageRank, freshness, click data, learned models) in a multi-stage pipeline: cheap retrieval of thousands of candidates, then expensive re-ranking of the top few hundred.

At scale the index is **sharded by document** (each shard holds a complete mini-index over a subset of documents, a query fans out to all shards and merges the top results) rather than by term (which creates huge hot shards for common words). Fan-out makes tail latency the dominant concern — see [Back-of-the-Envelope Estimation](18_back_of_envelope_estimation.md).

## Sorted sets and leaderboards

A sorted set keeps members ordered by score with `O(log n)` insert, update, and rank queries. Redis implements it with a **skip list** (a linked list with express lanes) plus a hash map from member to score.

- `ZINCRBY leaderboard 50 alice` updates a score; `ZREVRANK leaderboard alice` gives her rank; `ZREVRANGE leaderboard 0 99` gives the top 100.
- One Redis instance comfortably holds tens of millions of members. Beyond that, shard by a natural boundary (per game, per region, per week) so each board fits on one node.
- A *global* rank across shards is the hard part: either keep a single top-N board fed by per-shard top-Ns, or bucket scores into ranges (a histogram of how many players have each score band) and compute approximate rank for everyone outside the top.

## Merkle trees

A Merkle tree hashes data blocks at the leaves and hashes pairs of children up to a single root. Two copies of a dataset are identical if their roots match; if not, comparing children finds the differing blocks in `O(log n)` hash comparisons. Uses: replica anti-entropy in Dynamo-style stores ([Consensus and Coordination](19_consensus_and_coordination.md)), Git objects, blockchains, and verifiable logs.

## LSM trees and SSTables

A **log-structured merge tree** turns random writes into sequential ones: writes go to a write-ahead log and an in-memory sorted **memtable**; when it fills, it is flushed to an immutable sorted file (**SSTable**). Background **compaction** merges SSTables, dropping overwritten and deleted values.

| | LSM tree | B-tree |
|---|---|---|
| Writes | Sequential appends; very high throughput | In-place page updates; random I/O |
| Reads | May check several files (Bloom filters help) | One root-to-leaf path |
| Write amplification | Compaction rewrites data several times | Page splits, full-page WAL writes |
| Space | Temporary duplicates until compaction | Fragmentation in partially full pages |
| Good fit | Write-heavy, time series, logs, wide-column (Bigtable, Cassandra) | Read-heavy OLTP with many updates (PostgreSQL, MySQL) |

## Build the sketches, and check them against their theory

The formulas above are easy to recite and easy to misapply. Here are the three probabilistic
structures built from scratch in about 100 lines, each measured against the error its theory
predicts:

```python
"""Bloom filter, HyperLogLog and count-min sketch, built from scratch and
checked against the error their theory predicts."""
import hashlib, heapq, itertools, math, random
from collections import Counter

def hashes(item, k, salt=""):
    d = hashlib.sha256(f"{salt}{item}".encode()).digest()
    h1, h2 = int.from_bytes(d[:8], "big"), int.from_bytes(d[8:16], "big")
    return [h1 + i * h2 for i in range(k)]          # double hashing: k hashes from two


class Bloom:
    def __init__(self, n, bits_per_item):
        self.m = n * bits_per_item
        self.k = max(1, round(bits_per_item * math.log(2)))    # optimal k = (m/n) ln 2
        self.bits = bytearray(self.m // 8 + 1)
    def add(self, x):
        for h in hashes(x, self.k):
            i = h % self.m
            self.bits[i >> 3] |= 1 << (i & 7)
    def __contains__(self, x):
        return all(self.bits[(h % self.m) >> 3] >> ((h % self.m) & 7) & 1 for h in hashes(x, self.k))


class HyperLogLog:
    def __init__(self, p=14):
        self.p, self.m = p, 1 << p
        self.reg = bytearray(self.m)
    def add(self, x):
        h = int.from_bytes(hashlib.sha256(str(x).encode()).digest()[:8], "big")
        j = h >> (64 - self.p)                         # first p bits pick a register
        rest = h & ((1 << (64 - self.p)) - 1)
        rank = (64 - self.p) - rest.bit_length() + 1   # position of the first 1-bit
        self.reg[j] = max(self.reg[j], rank)
    def count(self):
        alpha = 0.7213 / (1 + 1.079 / self.m)
        est = alpha * self.m * self.m / sum(2.0 ** -r for r in self.reg)
        zeros = self.reg.count(0)
        if est <= 2.5 * self.m and zeros:              # small-range correction
            est = self.m * math.log(self.m / zeros)
        return est
    def merge(self, other):
        self.reg = bytearray(max(a, b) for a, b in zip(self.reg, other.reg))


class CountMin:
    def __init__(self, eps, delta):
        self.w, self.d = math.ceil(math.e / eps), math.ceil(math.log(1 / delta))
        self.t = [[0] * self.w for _ in range(self.d)]
    def add(self, x, c=1):
        for row, h in enumerate(hashes(x, self.d, "cm")):
            self.t[row][h % self.w] += c
    def estimate(self, x):
        return min(self.t[row][h % self.w] for row, h in enumerate(hashes(x, self.d, "cm")))


# ---- Bloom filter: false-positive rate vs bits per item --------------------------
n = 100_000
print("Bloom filter, 100,000 items:")
for bpi in (5, 10, 15):
    b = Bloom(n, bpi)
    for i in range(n):
        b.add(f"member-{i}")
    assert all(f"member-{i}" in b for i in range(0, n, 97))      # never a false negative
    fp = sum(f"other-{i}" in b for i in range(100_000)) / 100_000
    theory = (1 - math.exp(-b.k * n / b.m)) ** b.k
    print(f"  {bpi:2} bits/item, k={b.k}: {b.m // 8 // 1024:4} KB  measured FP {fp:.3%}  theory {theory:.3%}")

# ---- HyperLogLog: 12 KB of registers, any cardinality -------------------------------
print("HyperLogLog, 2^14 registers (16 KB here, ~12 KB with 6-bit registers):")
for true in (1_000, 100_000, 1_000_000):
    hll = HyperLogLog()
    for i in range(true):
        hll.add(f"user-{i}")
    print(f"  {true:9,} distinct -> estimate {hll.count():11,.0f}  error {hll.count() / true - 1:+.2%}"
          f"  (standard error 1.04/sqrt(m) = {1.04 / math.sqrt(hll.m):.2%})")
a, b = HyperLogLog(), HyperLogLog()
for i in range(600_000):
    a.add(f"user-{i}")                                 # server A saw users 0..599,999
for i in range(400_000, 1_000_000):
    b.add(f"user-{i}")                                 # server B saw 400,000..999,999
a.merge(b)
print(f"  merged sketches of two overlapping servers: {a.count():,.0f} (true 1,000,000)")

# ---- Count-min sketch + heap: top-K in a Zipf stream --------------------------------
rng = random.Random(7)
N_KEYS, N = 50_000, 500_000
cum = list(itertools.accumulate(1 / (r + 1) for r in range(N_KEYS)))
stream = rng.choices(range(N_KEYS), cum_weights=cum, k=N)
cms, heap, in_heap = CountMin(eps=0.001, delta=0.01), [], {}
K = 10
for x in stream:
    cms.add(x)
    est = cms.estimate(x)
    if x in in_heap:                                   # lazily refresh this key's entry
        in_heap[x] = est
    elif len(in_heap) < K:
        in_heap[x] = est
    elif est > min(in_heap.values()):
        del in_heap[min(in_heap, key=in_heap.get)]
        in_heap[x] = est
exact = Counter(stream)
true_top = {k for k, _ in exact.most_common(K)}
over = [cms.estimate(k) - exact[k] for k in exact]
beyond = sum(o > 0.001 * N for o in over)
print(f"Count-min, eps=0.001 delta=0.01 ({cms.d} x {cms.w} counters = {cms.d * cms.w:,} vs {len(exact):,} exact keys):")
print(f"  top-{K} found {len(true_top & set(in_heap))}/{K} correctly; undercounts: {sum(o < 0 for o in over)}")
print(f"  overcount beyond eps*N = {0.001 * N:.0f}: {beyond} of {len(over):,} keys "
      f"({beyond / len(over):.3%}; the bound allows delta = 1%); worst {max(over)}")
```

```text
Bloom filter, 100,000 items:
   5 bits/item, k=3:   61 KB  measured FP 9.193%  theory 9.185%
  10 bits/item, k=7:  122 KB  measured FP 0.820%  theory 0.819%
  15 bits/item, k=10:  183 KB  measured FP 0.059%  theory 0.074%
HyperLogLog, 2^14 registers (16 KB here, ~12 KB with 6-bit registers):
      1,000 distinct -> estimate         992  error -0.75%  (standard error 1.04/sqrt(m) = 0.81%)
    100,000 distinct -> estimate      99,727  error -0.27%  (standard error 1.04/sqrt(m) = 0.81%)
  1,000,000 distinct -> estimate   1,003,079  error +0.31%  (standard error 1.04/sqrt(m) = 0.81%)
  merged sketches of two overlapping servers: 1,003,079 (true 1,000,000)
Count-min, eps=0.001 delta=0.01 (5 x 2719 counters = 13,595 vs 41,148 exact keys):
  top-10 found 10/10 correctly; undercounts: 0
  overcount beyond eps*N = 500: 2 of 41,148 keys (0.005%; the bound allows delta = 1%); worst 991
```

What to take from the numbers:

- **Bloom filters behave exactly as the formula says.** At 10 bits per item and 7 hashes the
  measured false-positive rate is 0.820% against 0.819% predicted — 122 KB for 100,000 items of any
  size. Each extra 5 bits per item cuts false positives about tenfold. No member was ever reported
  absent. The implementation derives all *k* hashes from two (`h1 + i·h2`), a standard trick that
  doesn't hurt accuracy.
- **HyperLogLog's error doesn't grow with the count.** With 16,384 registers, estimates stayed within
  the 0.8% standard error from a thousand to a million distinct users, in constant memory. Merging two
  servers' sketches that overlapped by 200,000 users gave exactly the sketch you'd get from one server
  seeing everyone — the union is counted once, which is what makes HLL work for "distinct users
  across all servers this week."
- **Count-min never undercounts, and the top of a skewed stream is easy.** 13,595 counters (a third
  of the 41,148 distinct keys) found the true top 10 exactly. The εN bound is probabilistic: 2 of
  41,148 keys exceeded it, far fewer than the δ = 1% allowed. Heavy hitters are estimated well
  because collisions add the same absolute error to every key, which is negligible relative to a big
  count and large relative to a small one — so a count-min sketch is for finding the *frequent*
  items, not for counting rare ones.

## Geohash boundaries, demonstrated

The geospatial table above warns that close points can straddle a cell boundary. The encoding makes
it concrete:

```python
"""Geohash: nearby points share a prefix — except across a cell boundary."""
BASE32 = "0123456789bcdefghjkmnpqrstuvwxyz"

def geohash(lat, lon, precision=7):
    lat_rng, lon_rng, bits, out, even = [-90.0, 90.0], [-180.0, 180.0], 0, "", True
    for i in range(precision * 5):
        rng, val = (lon_rng, lon) if even else (lat_rng, lat)
        mid = (rng[0] + rng[1]) / 2
        bit = val >= mid
        rng[0 if bit else 1] = mid                      # keep the half containing the point
        bits = bits * 2 + bit
        even = not even
        if i % 5 == 4:
            out += BASE32[bits]
            bits = 0
    return out

sf = (37.7749, -122.4194)
print("San Francisco        ", geohash(*sf))
print("~100 m north         ", geohash(sf[0] + 0.0009, sf[1]))
import os
a, b = (0.00001, 0.00001), (-0.00001, -0.00001)          # ~3 m apart, on either side of 0°N 0°E
print(f"two points ~3 m apart: {geohash(*a)} vs {geohash(*b)}  shared prefix: "
      f"{len(os.path.commonprefix([geohash(*a), geohash(*b)]))} characters")
```

```text
San Francisco         9q8yyk8
~100 m north          9q8yykb
two points ~3 m apart: s000000 vs 7zzzzzz  shared prefix: 0 characters
```

A 7-character geohash is a cell of roughly 150 m × 150 m at the equator (narrower east–west further north), and a point 100 m away usually shares 6 of
7 characters. But two points 3 m apart on either side of the equator and prime meridian share **no**
prefix at all, because the very first bit of longitude and latitude differ. The same happens, less
dramatically, at every cell edge. That is why a proximity query always searches the target cell
**and its eight neighbours** at a precision where a cell is at least as large as the search radius,
and then filters by true distance — never "all points with the same prefix."

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Picking a structure** | Knows these structures exist | Names the right one for the question and what it gives up | Designs systems around sketches (merge across servers and time windows) |
| **Bloom, HLL, count-min** | Explains "maybe in the set, definitely not" | Sizes each from its error formula; explains no deletes, mergeability, never undercounting | Chooses cuckoo filters, windowed sketches or exact structures from cost and accuracy targets |
| **Geospatial** | Knows geohash prefixes mean proximity | Handles boundaries with neighbour cells; compares geohash, quadtree and S2 | Designs sharded geo indexes for moving objects at city scale |
| **Search and ranking** | Knows an inverted index maps terms to documents | Explains posting-list intersection, BM25, document-sharded fan-out | Designs multi-stage retrieval and ranking with latency budgets |
| **Leaderboards, Merkle, LSM** | Uses a sorted set | Explains skip lists, global rank across shards, Merkle anti-entropy, LSM vs B-tree | Chooses storage engines and repair strategies for a platform |

## Interview checklist

- [ ] I can match each question ("seen before?", "how many distinct?", "how often?", "what's nearby?", "which documents?", "what rank?") to its structure and name what it gives up.
- [ ] I can size a Bloom filter from bits per item and state its false-positive rate.
- [ ] I can explain how HyperLogLog estimates cardinality, its error, and why sketches merge.
- [ ] I can build top-K with a count-min sketch and a heap, and say why it never undercounts.
- [ ] I can explain geohash, why boundaries force neighbour-cell queries, and when to use quadtrees or S2 instead.
- [ ] I can explain inverted indexes, BM25, and why search indexes are sharded by document.
- [ ] I can explain sorted sets for leaderboards, Merkle trees for anti-entropy, and LSM trees vs B-trees.

## Related building blocks

- [Database Internals: How They Actually Work](06_database_internals.md)
- [Caching](07_caching.md)
- [Batch and Stream Processing](21_batch_and_stream_processing.md)
- [Partitioning, Shard Keys, and Hot Keys](25_partitioning_and_hot_keys.md)
