# Partitioning, Shard Keys, and Hot Keys

Partitioning (sharding) is how a dataset larger than one machine — or a write rate higher than one machine can take — gets split across many. It is also where many designs quietly fail: a shard key that looked reasonable sends 40% of traffic to one shard, or a rebalance moves half the data at peak. This file covers choosing the key, secondary indexes, rebalancing, and the hot-key problem that no shard key solves on its own.

> 🎯 In an interview, name the shard key explicitly and test it against your top two access patterns: "Partition messages by `conversation_id` — every read is 'messages in this conversation', so a read touches one shard, and no single conversation is large enough to be a hotspot."

## Foundations — Partitioning, Replication, and Routing

### Two tools, two different problems

Distributed data uses two techniques that are easy to confuse:

- **Replication** keeps *copies of the same data* on several machines — for availability and
  read throughput ([Distributed Systems Fundamentals](../../CSFundamentals/15_distributed_systems_deep_dive.md) §5).
- **Partitioning** (sharding) splits the data so each machine holds *a different subset* — for
  capacity and write throughput. More replicas never add write capacity, because every replica
  must apply every write; only partitioning does.

Real systems do both: each partition is itself replicated, often as its own Raft or Paxos group
(CockroachDB ranges, Spanner splits, Kafka partitions, DynamoDB partitions).

### The routing problem

Once data is split, every request must reach the partition that owns its key. Three designs:

| Who routes | How | Examples |
|---|---|---|
| **A routing tier** | Clients call a proxy that knows the partition map | Vitess `vtgate`, MongoDB `mongos`, Twemproxy |
| **Any node** | Clients call any node; it forwards or redirects | Cassandra (any node coordinates), Redis Cluster (`MOVED` redirects) |
| **The client** | A smart client caches the partition map and goes direct | DynamoDB and Bigtable client libraries, Kafka producers |

Whichever it is, the **partition map** — which key range or hash slot lives on which node —
is small, critical metadata. It is usually kept in a consensus store (ZooKeeper, etcd, a
metadata Raft group) and versioned, so that a client holding a stale map gets a clear "moved"
error and refreshes instead of writing to the wrong place.

### Vocabulary

| Term | Meaning |
|---|---|
| Partition, shard, range, tablet, vnode | One piece of the data, owned by one node (plus its replicas) at a time |
| Shard key, partition key | The field whose value decides the partition |
| Hash slot / virtual partition | A fixed unit of the key space, many per node, moved as a whole |
| Skew | Some partitions getting much more data or traffic than others |
| Hot key / hot partition | A single key or partition receiving a disproportionate share of traffic |
| Scatter-gather | A query sent to every partition and merged |
| Rebalancing / resharding | Moving partitions between nodes, or changing the partitioning itself |

## Choosing a shard key

A good shard key has three properties:

1. **High cardinality** — many distinct values, so data can spread over many shards.
2. **Even load** — no small set of values receives a large share of reads or writes.
3. **Aligned with the dominant query** — the most frequent reads can be served from a single shard.

| Candidate key | Problem it avoids | Problem it creates |
|---|---|---|
| `user_id` | User-scoped reads hit one shard. | Celebrity or bot users become hotspots; cross-user queries fan out. |
| `created_at` (timestamp) | Range scans by time are cheap. | Every new write goes to the newest shard — a moving hotspot. |
| `hash(entity_id)` | Even spread of keys. | Range queries over entity IDs fan out to every shard. |
| `(tenant_id, entity_id)` | Tenant isolation, tenant-scoped queries. | A few huge tenants dominate; needs per-tenant splitting. |
| Geohash / S2 cell prefix | Nearby queries hit few shards. | Dense cities are hot; boundaries need neighbour lookups. |

## Range vs hash partitioning

| | Range partitioning | Hash partitioning |
|---|---|---|
| How | Contiguous key ranges per shard (`A–F`, `G–M`…); split when a range grows. | `hash(key)` decides the shard, usually via consistent hashing or fixed virtual partitions. |
| Range scans | Efficient (one or few shards). | Scatter to all shards. |
| Load distribution | Follows key distribution — skewed keys make skewed shards. | Even by construction, except for individual hot keys. |
| Rebalancing | Split/merge ranges; move the busy half. | Move virtual partitions between nodes. |
| Examples | Bigtable, HBase, Spanner, CockroachDB | Cassandra, DynamoDB, Redis Cluster |

Bigtable-style systems use range partitioning and push the burden onto **row-key design**: prefix a timestamp key with a hashed or salted bucket, or use reversed domain names, so writes spread while related rows stay together.

## Secondary indexes: local vs global

A query on a non-key attribute ("orders by status", "users by email") needs a secondary index, and there are two ways to partition it:

| | Local (document-partitioned) index | Global (term-partitioned) index |
|---|---|---|
| Where the index lives | On each data shard, covering only that shard's rows. | In its own partitions, keyed by the indexed value. |
| Write cost | Updated in the same local transaction — cheap and consistent. | A write may update a different partition — needs a distributed transaction or async update. |
| Read cost | Query every shard and merge (scatter-gather). | Read one index partition, then fetch rows. |
| Consistency | Immediately consistent with the row. | Often eventually consistent (DynamoDB global secondary indexes). |
| Choose when | Queries also filter by the shard key, or fan-out is acceptable. | Selective lookups on the indexed field at high read volume. |

```arch
%% caption: Local indexes force a scatter-gather read across all shards; Global indexes allow a targeted read but complicate writes.
grid 170x110
group local "Local Indexes (Scatter-Gather Read)" color=slate style=dashed
node client1 "Client" at 0,1 in local icon=client color=blue
node s1 "Shard A" at 1,0 in local icon=db color=amber sub="data + index"
node s2 "Shard B" at 1,2 in local icon=db color=amber sub="data + index"

client1 -> s1 : "query index"
client1 -> s2 : "query index"

group global "Global Index (Targeted Read)" color=slate style=dashed
node client2 "Client" at 0,3 in global icon=client color=blue
node gidx "Global Index Shard" at 1,3 in global icon=search color=green
node s3 "Data Shard" at 2,3 in global icon=db color=amber

client2 -> gidx : "1. query index"
gidx -> s3 : "2. fetch row"
```

A **covering index** stores the columns a query needs alongside the index key, so the query never has to fetch the base row — valuable when the base row lives on another shard.

## Rebalancing

Data and traffic change, so partitions must move. The approaches, from worst to best:

1. **`hash(key) mod N`** — changing `N` moves almost every key. Avoid for anything persistent or cached.
2. **Fixed virtual partitions** — create many more partitions than nodes up front (e.g. 1,024 or 16,384 hash slots) and move whole partitions between nodes. Redis Cluster and Couchbase do this; simple and predictable.
3. **Consistent hashing with virtual nodes** — adding a node takes over only the arcs of the ring next to its virtual nodes, about `1/N` of the keys, drawn evenly from the other nodes.
4. **Dynamic range splitting** — split a range when it exceeds a size or load threshold, and move the busy half (Bigtable, Spanner, CockroachDB).

Operational rules: throttle data movement so it does not eat serving capacity, move during low traffic when possible, keep the old owner serving until the new one has caught up, and make routing metadata (which shard owns what) highly available — clients cache it and handle "moved" redirects.

## Hot keys

Even a perfect shard key cannot fix one key that receives 400× the traffic of the rest — a celebrity's profile, a viral video's view counter, a flash-sale product. The fixes depend on whether the hot traffic is reads or writes.

**Hot reads**

- **Cache in front of the shard**, with the hot key replicated across many cache nodes (key suffix `#0…#9`, client picks one at random) so a single cache node is not the new bottleneck.
- **Local in-process caching** for a few seconds on each app server — even a 1-second TTL collapses thousands of identical reads per second into one.
- **Read replicas** for that partition.

**Hot writes**

- **Key salting / splitting**: write to `key#0 … key#k−1` chosen at random or round-robin, spreading the load over `k` shards. Reads must query all `k` sub-keys and merge. Only salt keys you know (or detect) to be hot, because salting every key multiplies read cost everywhere.
- **Buffered counters**: for counters (views, likes), increment in memory or in a stream and flush aggregated deltas every second, instead of writing the database on every event.
- **Write-behind queue** for non-critical updates, with coalescing per key.

**Detecting hot keys**: sample request logs, keep a count-min sketch or top-K per shard ([Specialized Data Structures and Indexes](20_specialized_data_structures.md)), and alert when a key's share of shard traffic crosses a threshold. Some systems (DynamoDB adaptive capacity, Bigtable's load-based splitting) partly handle this automatically.

## Cross-shard operations

Once data is partitioned, some operations become expensive, and it pays to say so:

- **Scatter-gather queries** (no shard key in the filter) add latency proportional to the slowest shard; limit them or precompute.
- **Cross-shard transactions** need two-phase commit on a consistent store (Spanner) or a saga ([Transactions, Isolation, Locking, and Sagas](11_transactions_and_concurrency.md)).
- **Global uniqueness** (e.g. unique usernames) needs a single authoritative partition for that value (partition the uniqueness table by the value itself) rather than checking every shard.
- **Global ordering and ranking** (leaderboards, global feeds) need either a separate aggregated structure or approximation.

## Mapping keys to nodes, measured

The rebalancing list above ranks the ways to map keys to nodes. Measuring them on 200,000 keys
makes the ranking concrete: start with 10 nodes, add an 11th, and count how many keys change
owner and how even the result is.

```python
"""How much data moves when a node joins, and how evenly keys spread,
for four ways of mapping keys to nodes."""
import bisect, hashlib, statistics

def h(s):
    return int.from_bytes(hashlib.md5(s.encode()).digest()[:8], "big")

KEYS = [f"user:{i}" for i in range(200_000)]

def mod_n(nodes):
    return lambda k: nodes[h(k) % len(nodes)]

def ring(nodes, vnodes):
    points = sorted((h(f"{n}#{v}"), n) for n in nodes for v in range(vnodes))
    hashes = [p for p, _ in points]
    def owner(k):
        i = bisect.bisect(hashes, h(k)) % len(points)   # first point clockwise
        return points[i][1]
    return owner

def rendezvous(nodes):
    return lambda k: max(nodes, key=lambda n: h(f"{n}|{k}"))  # highest random weight

def evaluate(name, make):
    before, after = [f"n{i}" for i in range(10)], [f"n{i}" for i in range(11)]
    f0, f1 = make(before), make(after)
    a, b = [f0(k) for k in KEYS], [f1(k) for k in KEYS]
    moved = sum(x != y for x, y in zip(a, b)) / len(KEYS)
    loads = [b.count(n) for n in after]
    mean = len(KEYS) / len(after)
    print(f"{name:24} moved {100 * moved:5.1f}%   busiest node {max(loads) / mean:4.2f}x mean   "
          f"spread (stdev/mean) {statistics.pstdev(loads) / mean:5.1%}")

print("adding an 11th node to 10 (ideal: move 1/11 = 9.1% of keys, every node at 1.00x):")
evaluate("hash mod N", mod_n)
evaluate("ring, 1 point per node", lambda ns: ring(ns, 1))
evaluate("ring, 16 vnodes", lambda ns: ring(ns, 16))
evaluate("ring, 256 vnodes", lambda ns: ring(ns, 256))
evaluate("rendezvous hashing", rendezvous)
```

```text
adding an 11th node to 10 (ideal: move 1/11 = 9.1% of keys, every node at 1.00x):
hash mod N               moved  90.7%   busiest node 1.01x mean   spread (stdev/mean)  0.7%
ring, 1 point per node   moved  12.2%   busiest node 2.39x mean   spread (stdev/mean) 63.2%
ring, 16 vnodes          moved   7.2%   busiest node 1.26x mean   spread (stdev/mean) 21.9%
ring, 256 vnodes         moved   9.3%   busiest node 1.09x mean   spread (stdev/mean)  5.8%
rendezvous hashing       moved   9.1%   busiest node 1.01x mean   spread (stdev/mean)  0.5%
```

- **`hash mod N` moves 91% of keys** to add one node, because nearly every `h % 10` differs from
  `h % 11`. For a cache that is a near-total cold start; for a database it is a full reshuffle.
  Its balance is excellent — which is why it's fine for a *fixed* number of slots (Redis
  Cluster's 16,384 hash slots are `CRC16(key) mod 16384`, and slots, not keys, move between
  nodes).
- **A ring with one point per node moves little but balances badly.** The 11th node took only
  12% of keys, but random point positions give random arc lengths: the busiest node held 2.4× its
  fair share.
- **Virtual nodes fix the balance.** With 256 points per node the busiest node is at 1.09×, and
  a joining node takes almost exactly 1/11 of the keys, drawn from all the others. More vnodes
  mean a bigger ring to store and search; 100–256 per node is typical. Vnodes also let you weight
  a bigger machine with more points.
- **Rendezvous (highest-random-weight) hashing** is optimal on both counts — exactly 1/11 moved,
  1.01× balance — with no ring at all: each key goes to the node with the highest `hash(node, key)`.
  The cost is computing one hash per node per lookup, fine for tens of nodes (and used by many
  CDNs and client-side balancers), wasteful for thousands.

The consistent-hashing lab under **Rebalancing** above lets you add and remove nodes and change
the number of virtual nodes to watch exactly this.

## Skewed load, measured

Every scheme above spreads **keys** evenly. None of them spreads **load** evenly, because real
traffic is skewed: a few keys get most of the requests. A Zipf workload (the *k*-th most popular
key gets traffic proportional to 1/*k*, a good model for URLs, products and users) on 16 hash
partitions:

```python
"""Hash partitioning spreads keys evenly, not load. A Zipf workload
(a few keys get most requests) on 16 shards, before and after splitting
the hottest keys across several sub-keys."""
import hashlib, itertools, random
from collections import Counter

def h(s):
    return int.from_bytes(hashlib.md5(s.encode()).digest()[:8], "big")

SHARDS, KEYS, REQUESTS = 16, 100_000, 1_000_000
rng = random.Random(4)
weights = [1 / (rank + 1) for rank in range(KEYS)]           # Zipf, s = 1
cum = list(itertools.accumulate(weights))
reqs = rng.choices(range(KEYS), cum_weights=cum, k=REQUESTS)
top = Counter(reqs).most_common(1)[0]
print(f"hottest key receives {100 * top[1] / REQUESTS:.1f}% of all requests")

def shard_loads(route):
    loads = Counter(route(k) for k in reqs)
    return max(loads.values()) / (REQUESTS / SHARDS)

plain = lambda k: h(f"k{k}") % SHARDS
print(f"hash partitioning:              busiest shard {shard_loads(plain):.2f}x the mean")

for hot_n, split in ((10, 8), (100, 8), (100, 16)):
    hot = {k for k, _ in Counter(reqs).most_common(hot_n)}
    salted = lambda k: h(f"k{k}#{rng.randrange(split)}") % SHARDS if k in hot else plain(k)
    print(f"top {hot_n:3} keys split {split:2} ways:    busiest shard {shard_loads(salted):.2f}x the mean"
          f"   (a read of a split key now fans out to {split} sub-keys)")
```

```text
hottest key receives 8.3% of all requests
hash partitioning:              busiest shard 2.31x the mean
top  10 keys split  8 ways:    busiest shard 1.30x the mean   (a read of a split key now fans out to 8 sub-keys)
top 100 keys split  8 ways:    busiest shard 1.26x the mean   (a read of a split key now fans out to 8 sub-keys)
top 100 keys split 16 ways:    busiest shard 1.24x the mean   (a read of a split key now fans out to 16 sub-keys)
```

- **One key can outweigh a whole shard.** The hottest key alone receives 8.3% of all requests;
  a perfectly fair shard would receive 6.25%. No shard key and no hash function can fix that —
  the key's own shard is at 2.3× the average before any other key is counted.
- **Splitting just the top 10 keys** across 8 sub-keys each brings the busiest shard down to
  1.3×. Splitting 100 keys, or splitting 16 ways, adds little more: the remaining imbalance is
  the ordinary randomness of which keys land together, not any single hot key.
- **The price is on reads**: a read of a split key must query all its sub-keys and merge. That is
  why the text above says to split only keys you know (or detect) to be hot — in practice
  a count-min sketch or top-K per shard feeds a small "hot key" list, and only those keys are
  salted, cached more aggressively, or given dedicated capacity.

## Resharding a live system, step by step

Moving partitions between nodes is routine. Changing *how* data is partitioned — a new shard key,
splitting one database into many — while serving traffic is one of the riskiest operations in
data infrastructure, and a common staff-level interview question. The standard procedure:

1. **Decide the new layout and a routing version.** The partition map gets a new version number;
   every write will carry the version it was routed with.
2. **Start copying new writes.** Either dual-write from the application (to the old and new
   locations, with the old one authoritative) or, more safely, stream the old store's change log
   (CDC: PostgreSQL logical replication, MySQL binlog, DynamoDB Streams) into the new layout.
3. **Backfill existing data** from a consistent snapshot, applying the change stream on top so
   nothing written during the copy is lost. Throttle it to protect production latency.
4. **Verify.** Compare row counts and checksums per range; run **shadow reads** that query both
   layouts and log mismatches without affecting users.
5. **Cut over reads**, gradually — per key range or percentage — watching error rates and latency,
   with the old layout still available for rollback.
6. **Cut over writes.** Briefly block or fence writes to a range (the routing version rejects
   writes carrying the old version), let the change stream drain, then make the new location
   authoritative. This is the only moment that needs care; done per range, each pause is short.
7. **Clean up** only after a soak period: stop the stream, delete old data, remove dual-write
   code.

The recurring ideas are the same as everywhere in distributed systems: a versioned source of
truth for ownership, a change log to catch up, verification before trust, small reversible steps,
and a fence so two owners never accept writes at once
([Distributed Systems Fundamentals](../../CSFundamentals/15_distributed_systems_deep_dive.md) §7).

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Shard key choice** | Picks a key with high cardinality | Tests the key against the top access patterns and skew; names the fan-out it creates | Chooses keys that survive years of product change; plans for tenant and celebrity skew |
| **Range vs hash, mapping schemes** | Knows hash partitioning spreads keys | Explains mod N, consistent hashing, vnodes and rendezvous with their movement and balance | Chooses fixed slots vs dynamic splitting for a storage platform |
| **Secondary indexes** | Knows non-key queries need an index | Compares local and global indexes and their consistency | Designs index maintenance pipelines across partitions |
| **Hot keys** | Adds a cache | Separates hot reads from hot writes; salts detected hot keys; quantifies the read cost | Builds hot-key detection and automatic mitigation into the platform |
| **Rebalancing and resharding** | Knows data must move | Explains throttled moves, routing metadata and "moved" redirects | Runs a live reshard: CDC, backfill, shadow reads, fenced cut-over, rollback plan |

## Interview checklist

- [ ] I can explain why partitioning, not replication, adds write capacity, and how requests are routed to partitions.
- [ ] I can pick a shard key and test it against the dominant queries and skew.
- [ ] I can compare `hash mod N`, consistent hashing with and without vnodes, and rendezvous hashing, with the measured movement and balance.
- [ ] I can explain why hash partitioning doesn't fix hot keys, and handle hot reads and hot writes differently.
- [ ] I can compare local and global secondary indexes.
- [ ] I can list what gets expensive once data is partitioned: scatter-gather, cross-shard transactions, uniqueness, global ordering.
- [ ] I can walk through a live reshard: versioned routing, change capture, backfill, verification, gradual and fenced cut-over.

## Related building blocks

- [Database Internals: How They Actually Work](06_database_internals.md)
- [Scaling and Load Balancing](13_scaling_and_load_balancing.md)
- [Consensus and Coordination](19_consensus_and_coordination.md)
- [Specialized Data Structures and Indexes](20_specialized_data_structures.md)
