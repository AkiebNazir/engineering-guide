# Social Graph and Caching at Scale

A social graph is a read-dominated, densely connected dataset that you cannot partition by geography or by community, and every page render asks it hundreds of small questions: who are your friends, how many, may this viewer see that post. Two Facebook papers describe how one company answered: "TAO: Facebook's Distributed Data Store for the Social Graph" (Bronson et al., USENIX ATC 2013) and "Scaling Memcache at Facebook" (Nishtala et al., NSDI 2013). This block first frames the graph as a data problem, then walks through TAO and the memcache tier under it, stating only what those papers document.

> 🎯 Say the shape before the product: "The graph is objects plus typed, directed, time-ordered associations, stored as adjacency lists sharded by source id. 99.8% of requests are reads, so a two-level cache in front of a sharded database serves them, with one coordinator per shard per region to serialize writes and stop thundering herds. Consistency is eventual for everyone except the writer, and privacy is checked at read time."

## Part 1 — The social graph as a data problem

### Objects, associations, and the query mix

The model in the TAO paper is deliberately small. **Objects** are typed nodes with an id and key-value fields (a user, a post, a photo, a place). **Associations** are typed, directed edges `(id1, atype, id2)` with a timestamp and optional data. An association list is `(id1, atype)` and is ordered by time, newest first. Undirected relations such as friendship are stored as two directed edges, and TAO can be configured with an inverse type that keeps the pair in step.

| Query | Shape | Served by |
|---|---|---|
| Newest 50 friends | Range on `(id1, atype)` by time | One adjacency-list prefix, one shard |
| How many friends | Count of `(id1, atype)` | Separately stored counter, never `COUNT(*)` |
| Is A friends with B | Point read of `(A, friend, B)` | Batched membership check on A's shard |
| Mutual friends of A and B | Intersect two adjacency lists | Two range reads plus a merge in the caller |
| Friends of friends | Two-hop expansion | 1 read plus one read per friend, fan-out cost |

The mix is overwhelmingly reads of single lists and counts. The TAO paper reports that 99.8% of its requests are reads and that its overall read hit rate was 96.4%, which is what keeps the database tier small. Design the graph for the single-shard list read first and treat multi-hop as a separately budgeted feature.

### Storing adjacency: three options

| Option | Layout | Wins when | Loses when |
|---|---|---|---|
| Relational adjacency table | `edges(id1, atype, id2, ts, data)`, primary key on the triple, secondary index `(id1, atype, ts desc)` | You already operate MySQL or Postgres, need a transaction over the pair, and each shard fits a few TB. TAO persists its graph in MySQL | Celebrity lists dominate one shard, and counts and inverse edges need extra tables you maintain |
| KV or wide-column | Row key `(id1, atype)`, columns sorted by `ts` or `id2` | "Newest N" is one sequential read, writes scale linearly, and you want no join engine in the path | One row grows without bound for celebrities, there are no cross-row transactions, and the inverse direction is a second table you write yourself |
| Dedicated graph database | Native adjacency, a traversal language | Deep or pattern-shaped queries (fraud rings, exploration) on a graph that fits one machine or a small cluster | Sharding a huge graph turns every hop into a network call, so it rarely sits on the 10^6 <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> OLTP path |

**Decision rule:** for one-to-two-hop reads at very high <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, use sharded adjacency lists plus a cache. Send deep traversals to an offline graph job or a graph database over a slice of the data. The trade-off is that you give up ad-hoc traversal queries on the hot path, and it is acceptable because the product only ever asks a handful of fixed question shapes.

### Sharding a graph

Shard **by source id**. TAO stores an association on the shard of its `id1`, so any list query is served by one server, and an object id embeds its shard id and never moves. The number of logical shards far exceeds the number of servers, so you rebalance by remapping shards.

Three problems follow:

- **The inverse edge.** A→B lives on `shard(A)` and B→A on `shard(B)`. With 1,024 shards a friendship spans two shards with probability 1 − 1/1024 ≈ 99.9%. TAO does not make the two writes atomic. If a failure leaves a forward edge without its inverse, the paper calls it a hanging association and schedules an asynchronous repair job. Your options are two-phase commit (atomic, slow, blocks on a dead participant), an outbox that applies the second write idempotently (what you should propose), or accept-and-repair as TAO does.
- **Hot and celebrity nodes.** An account with 10^8 followers has a 10^8 × 24 B = 2.4 GB list on one shard. TAO caches only a contiguous prefix of a list, notes that many objects have over 6,000 same-type associations so whole lists are not cached, and uses `assoc_count` to pick the cheaper direction for a membership check, since the inverse edge answers the same question. Add pagination by `(ts, id2)` cursor rather than offset, and cap page size. For write hot spots such as follows landing on one list at thousands per second, split the list into sub-lists `(id1, atype, bucket)`. That split is our suggestion, not something TAO documents.
- **Not partitionable by community.** The TAO paper says the graph is so interconnected that you cannot group users to make cross-partition requests rare, so every region needs a full copy and every cache tier sees the whole graph.

### Counters, consistency, privacy

**Counters.** Store the count beside the edge write, on the source shard, and cache it separately. TAO does this because `SELECT COUNT` is expensive, and it packs `(id1, atype)` counts into 14 bytes in the cache. For a viral counter, split into `k` sub-counters: 50,000 likes/s ÷ 16 = 3,125 writes/s per sub-counter (assuming one key sustains about 5,000 writes/s), and readers sum the 16 and cache the total for a second. Displayed counts may be approximate ("1.2M"). The actor's own "you liked this" state comes from an edge lookup, not the counter.

**Consistency.** The actor needs read-your-writes and everyone else can be eventually consistent. TAO documents that replication lag is usually under a second (in its measurements, under 1 s about 85% of the time, under 3 s 99% and under 10 s 99.8%), and that it gives read-after-write consistency within one tier because the write's response carries a changeset applied to the follower that issued it. Reads that must be right, such as credentials or blocks, are marked critical and go to the master region.

**Privacy at read time.** Check visibility when you read, not when you fan out: an unfriend or block must take effect on posts already sitting in a precomputed feed. The check costs one batched membership read per page (20 authors, one multi-get per shard), which is far cheaper than rewriting materialized feeds. Cache the verdict for seconds, or invalidate it from the same edge write.

### Friends of friends and People You May Know

Two-hop expansion explodes: 200 friends × 200 friends = 40,000 candidates. Cap it, then rank ([31_ranking_recommendation_and_experimentation.md](31_ranking_recommendation_and_experimentation.md)).

```arch
%% caption: Two-hop expansion is capped at each hop so candidate generation costs about 51 reads and 5,000 candidates, and ranking receives only the top few hundred.
grid 160x92
node U "User" at 0,0 shape=pill color=slate
node F1 "Read own friends" at 0,1 shape=card icon=users sub="take 50 by interaction" w=300
node F2 "Read each friend's newest 100" at 0,2 shape=card icon=graph sub="50 reads, skip nodes over 5,000" w=300
node AGG "Count occurrences per candidate" at 0,3 shape=card icon=counter sub="= mutual friends, 5,000 rows" w=300
node FLT "Drop existing friends" at 0,4 shape=card icon=filter sub="blocked, ineligible" w=300
node TOP "Keep top 500" at 0,5 shape=card icon=sort sub="by mutual count" w=300
node RK "Ranker adds signals" at 0,6 shape=card icon=model sub="contacts, workplace, recency" w=300
node OUT "Suggestions, cached 24 h" at 0,7 shape=pill color=green
U -> F1 -> F2 -> AGG -> FLT -> TOP -> RK -> OUT
```

Skipping high-degree friends loses little, because being friends with an account that has a million followers is weak evidence of a real-world tie. **Decision rule:** precompute per user in a batch and refresh on a friend-add event, do not compute per page view (numbers below).

### Worked example: sizing a graph service

Assumptions (ours): 10^9 users, 5×10^8 daily active, mean 200 friends, 400 graph reads per active user per day once page-render fan-out is counted, 0.2% writes, peak = 3× average, 64 B per edge row including its index, 1 KB per user object.

| Quantity | Arithmetic | Result | Decision |
|---|---|---|---|
| Directed edges | 10^9 × 200 | 2×10^11 | Cannot fit one node, shard by `id1` |
| Edge storage | 2×10^11 × 64 B, ×3 for replicas | 12.8 TB, 38 TB | About 13 primaries plus 26 replicas at 1 TB per host, sized by capacity |
| Object storage | 10^9 × 1 KB | 1 TB | Small next to edges |
| Graph reads | 5×10^8 × 400 = 2×10^11/day ÷ 86,400, ×3 | 2.3M/s avg, 6.9M/s peak | No database serves this, so a cache tier must absorb about 99% |
| Writes | 6.9M × 0.2% | 14k/s peak | Throughput is easy, the hard part is the two-shard inverse write |
| Reaching MySQL | 6.9M × 4% follower misses × 25% leader misses (assumed) | 69k/s = 1% of reads | About 1.8k/s per host over 39 hosts |
| Sensitivity | Follower hit 90%: 6.9M × 10% × 25% | 174k/s, 2.5× more | The follower hit ratio is the <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> to alert on |
| Cache <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> | 5×10^8 hot users × 3 KB (50-edge prefix at 24 B = 1.2 KB, object 1 KB, counts and slack) | 1.5 TB per tier | Each region needs this, the graph does not partition |
| Follower servers | 6.9M ÷ 3 regions = 2.3M/s ÷ 50k/s per server | 46 servers × 64 GB = 2.9 TB | <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> sets the fleet, so spare <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> buys longer prefixes |
| PYMK reads | 1 + 50 reads per user | 51 reads | Batch: 5×10^8 × 51 = 2.6×10^10/day = 295k/s, 13% of average graph load, run off-peak |
| PYMK online | 10^9 views/day ÷ 86,400 = 11.6k/s × 51 | 590k/s, 26% of average | Too expensive per view, precompute and refresh on friend-add |

So we need a cache-fronted, `id1`-sharded store where MySQL sees only 1% of reads, and PYMK runs as an off-peak batch.

## Part 2 — TAO

Before TAO, Facebook's web tier used memcache look-aside for the graph. The paper lists the reasons it stopped: a key-value cache fits edge lists badly (a change to one edge reloads the whole list), control logic ran on clients that never talk to each other (more failure modes, harder to avoid thundering herds), and read-after-write consistency was expensive on top of asynchronous MySQL replication. TAO is a service that implements the objects-and-associations <abbr title="Application Programming Interface">API</abbr> directly.

**<abbr title="Application Programming Interface">API</abbr>.** Objects: `obj_add`, `obj_get`, `obj_update`, `obj_delete`. Associations: `assoc_add`, `assoc_delete`, `assoc_get(id1, atype, id2set, high, low)`, `assoc_count(id1, atype)`, `assoc_range(id1, atype, pos, limit)`, `assoc_time_range(id1, atype, high, low, limit)`. Cache servers know the semantics, so a cached count of zero answers a range query without touching the database.

```arch
%% caption: Clients read from a nearby follower tier, followers forward misses and writes to the region's leader, and slave regions send writes to the master region while reading their local replica.
group SR "Slave region" color=blue icon=region
node C "Web client" at 0.5,0 in SR icon=browser
node FA "Follower tier A" at 0,1 in SR icon=cache
node FB "Follower tier B" at 1,1 in SR icon=cache sub="backup"
node SL "Leader tier" at 0.5,2 in SR icon=cache
node RDB "Replica MySQL" at 0.5,3 in SR icon=mysql-icon
group MR "Master region" color=purple icon=region
node ML "Leader tier" at 2.5,2 in MR icon=cache
node MDB "Master MySQL" at 2.5,3 in MR icon=mysql-icon
C -> FA
C ..> FB
FA -> SL : "miss, write"
FB -> SL : "miss, write"
SL -> RDB : "read miss"
ML -> MDB : "read miss, write"
SL -> ML : "forward write"
MDB -> RDB : "replication stream with embedded invalidate and refill"
```

**Tiers.** Clients talk to the closest follower tier and never to leaders. A follower serves hits and forwards misses and writes to the leader for the shard. Each shard has one leader per region, and all writes to it pass through that leader, so writes to a shard serialize naturally. Because one coordinator sees every request for an `id1`, it avoids concurrent overlapping database queries and caps the pending queries per shard, which protects MySQL from herds. Caches are demand-filled with <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> eviction. Followers hold only contiguous prefixes of association lists.

**How a write flows.** The leader writes MySQL synchronously, then sends cache-maintenance messages to followers asynchronously: an **invalidate** for objects, and a **refill** for associations (invalidating would truncate a list, so followers that cached the list re-query the leader). The follower that issued the write is updated synchronously from the response, and a version number in each message lets a late one be ignored.

```arch
%% caption: The writer sees its own change through the synchronous changeset while other follower tiers converge later through asynchronous refills.
node c "Client" at 0,0 icon=client color=slate
node f1 "Follower A" at 1,0 icon=server color=blue
node sl "Slave Leader" at 2,0 icon=server color=blue
node ml "Master Leader" at 3,0 icon=server color=purple
node db "Master MySQL" at 4,0 icon=db color=purple
node f2 "Follower B" at 2,1 icon=server color=blue

c -> f1 : "assoc_add id1 friend id2"
f1 -> sl : "forward write"
sl -> ml : "forward to master region"
ml -> db : "write edge & inverse"
db -> ml : "committed, new version"
ml -> sl : "changeset"
sl -> f1 : "changeset applied to cache"
f1 -> c : "ok"

node rep "replication stream reaches replica, then invalidate and refill" at 3,1 shape=card color=amber
db ..> rep ..> sl

sl ..> f2 : "refill, version checked"
```

**Cross-region.** One region holds the master database for each shard, chosen per shard and switched automatically on database failure. Writes go slave leader → master leader; reads and misses always use the local region's database, so read latency is independent of inter-region latency. The paper gives the reason: follower read misses were 25 times as frequent as writes, so it pays to send only the writes across. Consistency messages ride the replication stream and are delivered only after the change has reached the local replica. Sending them earlier would let a refill read stale data.

**Stated trade-offs.** TAO is eventually consistent by design, favouring availability and read latency over freshness. A client that keeps using one follower tier usually sees a consistent view, but failing over between tiers can break read-after-write. There are no multi-shard transactions, so hanging associations are repaired asynchronously. In a slave region, a value can briefly go back in time when a cache entry is evicted and reloaded from a replica that has not caught up, and the paper calls that rare. Hot objects are handled by shard cloning (several followers serve one shard) and, above an access-rate threshold, a client-side cache with version checks. When a leader dies, followers reroute misses to the database, a replacement leader takes writes, and the shard is bulk-invalidated once the box is replaced.

**Decision rule:** put one coordinator in front of each database shard and let it own fills, invalidations and write serialization. The cost is a leader hop on every miss and write, which is acceptable because misses and writes are the minority.

## Part 3 — Caching at very large scale: Scaling Memcache at Facebook

The 2013 paper describes memcache as a demand-filled look-aside cache: on a miss the web server reads the database and sets the key. On a write it updates the database and **deletes** the key rather than setting it, since deletes are idempotent. Its stated stance is that the probability of reading stale data is a parameter to tune, and it accepts slightly stale data in exchange for insulating the backend from load.

```arch
%% caption: A lease token is voided by a delete, so the slow reader's stale set is rejected and the next reader refills from the new value.
node a "Web Server A" at 0,0 icon=server color=blue
node m "Memcached" at 1,0 icon=cache color=teal
node db "Database" at 2,0 icon=db color=purple
node b "Web Server B" at 3,0 icon=server color=slate

a -> m : "get k"
m -> a : "miss + lease token"
a -> db : "read k (old value)"

b -> db : "update k"
b -> m : "delete k"

node inv "delete invalidates token" at 1,1 shape=card color=amber
m -> inv -> m

a -> m : "set k (old value) + token"
m -> a : "rejected"

a -> m : "get k"
m -> a : "miss + new token"
```

| Problem | Mechanism in the paper | What it costs |
|---|---|---|
| Stale set (race in the diagram) | Lease: a 64-bit token bound to the key, checked on set, voided by a delete | An extra round trip on misses, and a token to carry |
| Thundering herd | The server hands out one token per key per 10 seconds by default. Other requests get a "wait briefly" answer. On a set of keys prone to herds the peak database rate fell from 17K/s to 1.3K/s | Some requests wait or retry. A stale-value option lets tolerant callers use a recently deleted item |
| A few memcached servers fail | Gutter: about 1% of a cluster's servers. On no reply a client asks Gutter, on a miss fills it with a short TTL, so no invalidation is needed. It cut client-visible failures by 99% and converted 10–25% of failures into hits | Gutter data may be slightly stale |
| Mixed workloads evict each other | Separate pools: a default pool plus pools for cheap-miss or expensive-miss keys | Manual heuristics for pool assignment |
| Large, rarely read items waste <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> in every cluster | Regional pool shared by several frontend clusters | Cross-cluster latency and bandwidth, so only for low-rate items |
| Invalidations for many clusters | `mcsqueal` tails the database commit log, extracts deletes and broadcasts them | Delay of a commit-to-invalidate hop |
| Many-to-many connections | `mcrouter` proxy: connection coalescing, routing. Gets go over <abbr title="User Datagram Protocol - A simple, connectionless communication protocol that allows for sending messages with minimal overhead but no delivery guarantees.">UDP</abbr>, sets and deletes over <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> through mcrouter | Dropped <abbr title="User Datagram Protocol - A simple, connectionless communication protocol that allows for sending messages with minimal overhead but no delivery guarantees.">UDP</abbr> gets are treated as misses, with no recovery attempt |
| New or emptied cluster | Cold cluster warm-up: read from a warm cluster instead of the database | Race window, handled by a 2-second delete hold-off |

**Invalidation from the commit log.** Web servers could broadcast deletes, but the paper says that batches poorly and gives little recourse after a misrouted delete, whereas deletes embedded in committed <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr> sit in reliable logs, so `mcsqueal` can replay lost or misrouted ones. It batches deletes into fewer packets for mcrouter tiers, an 18× improvement in median deletes per packet, and the paper notes only 4% of deletes hit cached data. A web server also deletes in its own cluster to give the writer read-your-writes.

```arch
%% caption: Deletes flow from the durable commit log through a batching daemon and mcrouter tiers to every frontend cluster, so a lost delete can be replayed.
node W "Web server" at 0,0 icon=server
node DB "MySQL storage server" at 1.5,0 icon=mysql-icon
node LOG "Commit log" at 2.5,0 icon=logs
node SQ "mcsqueal daemon" at 2.5,1 icon=worker
group c1 "Cluster 1" color=blue icon=group
node R1 "mcrouter, cluster 1" at 1.5,2 in c1 icon=proxy
node M1 "memcached servers" at 1.5,3 in c1 icon=memcached
group c2 "Cluster 2" color=blue icon=group
node R2 "mcrouter, cluster 2" at 3.5,2 in c2 icon=proxy
node M2 "memcached servers" at 3.5,3 in c2 icon=memcached
W -> DB : "UPDATE with keys to invalidate"
DB -> LOG -> SQ
SQ -> R1 : "batched deletes"
SQ -> R2 : "batched deletes"
R1 -> M1
R2 -> M2
W:B ..> M1:L : "delete in own cluster"
```

**Cold cluster warm-up.** An empty cluster has a near-zero hit rate and would expose the databases. Clients in the cold cluster fetch from a warm cluster instead. Deletes in the cold cluster carry a two-second hold-off during which `add` is rejected, so a value fetched from a warm cluster before it saw an invalidation cannot be inserted. The paper says a theoretical gap remains if deletes are delayed more than two seconds, and that it turns the mechanism off once hit rates stabilise; it brought a cold cluster to full capacity in hours instead of days.

**Across regions.** One region holds master databases and the rest read replicas. Having a web server invalidate a replica region directly risks the invalidation arriving before replication, so the commit-log daemon handles it. For a write from a non-master region, the server sets a **remote marker** for the key in the region, writes to the master, and deletes the key locally. A miss that finds the marker is redirected to the master region. This trades latency on a miss for a lower chance of reading stale data.

**Decision rule:** name the herd protection (lease or single coordinator), the failure protection (gutter or bulk invalidation and fail-open), and the invalidation transport (commit log, not application dual-writes). Also say what you give up: bounded staleness, not linearizability.

## Interview angles

- **"Design a friends service."** Objects and typed edges, `id1` sharding, list-prefix cache with counts, both directions written via an outbox, numbers as in the sizing table.
- **"How do you store a celebrity's followers?"** Paginated cursor reads, prefix caching only, sub-lists for write heat, counter separate, no full-list fetch, no full-list fan-out.
- **"Mutual friends or People You May Know at scale?"** Capped two-hop with per-node limits, count occurrences, filter, rank. Precompute offline and refresh on events. State the read cost in reads per user.
- **"You unfriended someone and they still see your post."** Privacy is checked at read time on the current edge state, with short-TTL or invalidated verdicts, and critical reads hit the master.
- **"Why didn't Facebook keep look-aside memcache for the graph?"** The three problems from the TAO paper: edge lists, distributed control logic, read-after-write over async replication. TAO fixes them with semantic caches and one coordinator per shard.
- **"What is a lease?"** Token issued on a miss, voided by a delete, checked on set, rate-limited per key to stop herds. Show the diagram.
- **"A cache server dies. What protects the database?"** Fail open with a deadline, and a gutter tier with short TTLs instead of rehashing keys onto the survivors, which the paper says risks cascading overload when one key can be 20% of a server's requests. Alert on hit ratio.
- **"How do you add a new cache cluster?"** Warm from a peer with a hold-off on deletes, ramp traffic as hit ratio climbs ([07_caching.md](07_caching.md) covers the ramp arithmetic).

## Related building blocks

- [07_caching.md](07_caching.md)
- [25_partitioning_and_hot_keys.md](25_partitioning_and_hot_keys.md)
- [05_databases.md](05_databases.md)
- [10_distributed_systems_theory.md](10_distributed_systems_theory.md)
- [27_multi_region_and_global_traffic.md](27_multi_region_and_global_traffic.md)
- [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md)
- [31_ranking_recommendation_and_experimentation.md](31_ranking_recommendation_and_experimentation.md)
- [32_industry_papers_and_case_studies.md](32_industry_papers_and_case_studies.md)
- [../solutions/007_news_feed_solution.md](../solutions/007_news_feed_solution.md)
- [../solutions/018_distributed_cache_solution.md](../solutions/018_distributed_cache_solution.md)
- [../solutions/039_social_graph_service_solution.md](../solutions/039_social_graph_service_solution.md)
