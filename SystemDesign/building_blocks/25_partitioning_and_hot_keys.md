# Partitioning, Shard Keys, and Hot Keys

Partitioning (sharding) is how a dataset larger than one machine — or a write rate higher than one machine can take — gets split across many. It is also where many designs quietly fail: a shard key that looked reasonable sends 40% of traffic to one shard, or a rebalance moves half the data at peak. This file covers choosing the key, secondary indexes, rebalancing, and the hot-key problem that no shard key solves on its own.

> 🎯 In an interview, name the shard key explicitly and test it against your top two access patterns: "Partition messages by `conversation_id` — every read is 'messages in this conversation', so a read touches one shard, and no single conversation is large enough to be a hotspot."

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

**Detecting hot keys**: sample request logs, keep a count-min sketch or top-K per shard ([20_specialized_data_structures.md](20_specialized_data_structures.md)), and alert when a key's share of shard traffic crosses a threshold. Some systems (DynamoDB adaptive capacity, Bigtable's load-based splitting) partly handle this automatically.

## Cross-shard operations

Once data is partitioned, some operations become expensive, and it pays to say so:

- **Scatter-gather queries** (no shard key in the filter) add latency proportional to the slowest shard; limit them or precompute.
- **Cross-shard transactions** need two-phase commit on a consistent store (Spanner) or a saga ([11_transactions_and_concurrency.md](11_transactions_and_concurrency.md)).
- **Global uniqueness** (e.g. unique usernames) needs a single authoritative partition for that value (partition the uniqueness table by the value itself) rather than checking every shard.
- **Global ordering and ranking** (leaderboards, global feeds) need either a separate aggregated structure or approximation.

## Related building blocks

- [06_database_internals.md](06_database_internals.md)
- [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md)
- [19_consensus_and_coordination.md](19_consensus_and_coordination.md)
- [20_specialized_data_structures.md](20_specialized_data_structures.md)
