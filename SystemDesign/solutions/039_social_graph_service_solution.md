# 039 — Social Graph Service: Full System Design Solution

## Goal and contract

Store objects and typed, directed, time-ordered associations, and answer single-list reads at 10M+ per second from cache. The shape follows "TAO: Facebook's Distributed Data Store for the Social Graph" (Bronson et al., USENIX ATC 2013); the mechanics live in [30_social_graph_and_caching_at_scale.md](../building_blocks/30_social_graph_and_caching_at_scale.md), and this page applies them to the question's numbers. Anything marked "ours" is not in the paper.

- **Reads** are eventually consistent for everyone except the actor: others see a write in about a second, in the tail seconds.
- **The actor** sees their own write on the next read, including after a tier failover (a version token, ours).
- **Every edge exists in both directions**, written non-atomically; a transactional outbox (ours) guarantees convergence.
- **Privacy** is evaluated at read time, so blocks and unfriends affect content that is already cached or precomputed.
- **Not promised:** cross-region linearizability, multi-edge transactions, exact counts above 10^4.

The hard decision: the graph cannot be split by geography or community, so every region holds all of it and a two-level cache must absorb about 99% of reads.

## Estimates

Assumptions (ours): 3×10^9 users, 10^9 daily active, 200 average edges, 500 graph reads per active user per day (page renders fan out into privacy checks, counts, lists), peak 2.5× average, 64 B per edge row with its index, 1 KB per object, 3 regions, 50k cached reads/s per follower server and 5k indexed reads/s per MySQL host (both to load-test), 1 TB usable per host.

| Quantity | Arithmetic | Result | So we need |
|---|---|---|---|
| Edge rows | 3×10^9 × 200 | 6×10^11 (3×10^11 friendships, two rows each) | Sharding by `id1` |
| Storage per copy | edges 6×10^11 × 64 B = 38 TB, objects 3 TB, counts 3×10^9 × 6 × 24 B = 0.4 TB | 42 TB, so 42 hosts | 6 copies (3 regions × primary and in-region replica) = 250 TB, 252 hosts. Storage, not <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, sizes the database |
| Shards | 16,384 = 2^14; 42 TB ÷ 16,384 | 2.6 GB each, about 390 per host | Rebalance by moving a shard, never a host |
| Reads | 10^9 × 500 ÷ 86,400 = 5.8M/s, × 2.5 | 14M/s peak, 4.8M/s per region | Meets the 10M+ requirement |
| Writes | 14.5M ÷ 500 = 29k/s, each 2 edge rows + 2 counts + 1 outbox row | 145k row writes/s, 48k/s mastered per region | Easy. The hard part is the two-shard inverse |
| Follower tier | Region loss: 14.5M ÷ 2 = 7.2M/s ÷ 2 tiers = 3.6M/s ÷ (50k × 0.8) | 91 servers per tier, 546 in all, 53% utilised at normal peak | Two independent tiers per region |
| Working set | 10^9 hot users × 3 KB (100-edge prefix × 24 B = 2.4 KB, object 1 KB, counts; half of lists are shorter) | 3 TB per tier; 91 × 64 GB = 5.8 TB installed | <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> sets the fleet, spare <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> buys clones |
| Miss path | 14.5M × 4% follower misses = 580k/s to leaders; × 25% leader misses | 145k/s to MySQL = 1% of reads, 570/s per host over 84 regional hosts | 24 leaders per region (290k/s after a region loss ÷ 14k = 21). The 4% is near the paper's 96.4% overall hit rate |
| Sensitivity | Follower hit 90%: 14.5M × 10% × 25%; cold region: 4.8M/s ÷ (84 × 5k) | 362k/s (2.5×); 11.5× over capacity | Hit ratio is the <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>, and a cold cache is an outage |
| Replicas instead of cache | 14.5M ÷ 5k | 2,900 hosts versus 870 (252 + 546 + 72) | The cache tier is the design |

**Latency.** A follower hit is one round trip (about 0.5 ms) plus lookup and queueing: budget p99 3 ms. A leader hit adds a hop, p99 6 ms; a MySQL read adds an <abbr title="Solid-State Drive - A solid-state storage device that uses integrated circuit assemblies to store data persistently, offering faster access times.">SSD</abbr> read, p99 12 ms. Since 4% of reads miss the follower and 1% reach MySQL, the blended p99 sits at the leader-hit/database boundary: "p99 under 10 ms" is a claim about the leader path, p99.9 under 25 ms about the database path.

**Fan-out tail.** A page issues about 60 parallel reads (assumption); the chance one exceeds its own p99 is 1 − 0.99^60 = 45%, so batch per destination and hedge (*The Tail at Scale*, Dean and Barroso, 2013; [13_scaling_and_load_balancing.md](../building_blocks/13_scaling_and_load_balancing.md)).

## <abbr title="Application Programming Interface">API</abbr>

```text
obj_get(id)                                    → {id, otype, version, fields}
obj_add(otype, fields, home_region, idem_key)  → {id}                     # id embeds its shard
assoc_add(id1, atype, id2, data?, ts?)         → {version, created}       # idempotent upsert
assoc_delete(id1, atype, id2)                  → {version, deleted}
assoc_get(id1, atype, id2set ≤ 500, ts_high?, ts_low?) → [assoc]
assoc_count(id1, atype)                        → {count, approx}
assoc_range(id1, atype, pos, limit ≤ 100)      → [assoc]                  # pos < 100, the cached prefix
assoc_time_range(id1, atype, ts_high, ts_low, limit, cursor?) → {items, next_cursor}   # cursor = (ts, id2)
# every call: viewer, min_version? (token from a write), critical? (read the master region)
```

- **Idempotency.** `(id1, atype, id2)` makes `assoc_add` an upsert; the count increments only if a row was inserted, in the same transaction, so a retry cannot double-count.
- **Pagination.** Positions work on the cached prefix; deeper pages use the `(ts, id2)` cursor because offsets rescan and shift as edges arrive. Limits are capped and enumeration is rate limited.
- **Errors.** `NOT_FOUND` also means "hidden by privacy", so callers cannot probe for blocks. `OVERLOADED` carries retry-after with jitter. An unsatisfiable token is forwarded to the master region internally.

## Data model

```sql
objects(id BIGINT PK, otype, version, fields BLOB)                  -- id = shard(14b) | sequence(50b)
assocs(id1, atype, id2, ts, data, PK(id1, atype, id2), KEY(id1, atype, ts DESC, id2))
assoc_counts(id1, atype, count, PK(id1, atype))
outbox(seq, dest_id1, atype, id2, op, state)                        -- inverse edges, committed with the forward write
```

- **Partition key: the shard in `id1`.** An association lives on its source's shard, so a list query touches one shard. A versioned config service holds the 16,384-entry map `shard → (master region, hosts)`, cached in every server.
- **Placement (ours).** Create a user on a shard mastered in their home region, so their own writes skip the 100+ ms cross-region hop.
- **Source of truth:** the shard's master MySQL primary. Caches and PYMK lists are derived; counts are derived but transactional.

## Architecture

```arch
%% caption: Clients read from the nearest follower tier, misses climb to the region's leader and then MySQL, writes go to the shard's master region, and replication carries invalidations back.
group R2 "Region B: replica" icon=region color=blue
node C "Web tier" at 0.5,0 in R2 icon=app
node FB "Follower tier B" at 0,1 in R2 icon=cache
node FA "Follower tier A" at 1,1 in R2 icon=cache sub="91 servers"
node L2 "Leader tier" at 0.5,2 in R2 icon=cache sub="24 servers"
node RDB "Replica MySQL" at 0.5,3 in R2 icon=mysql-icon
node PY "PYMK batch" at 2,1 icon=worker sub="low priority"
group R1 "Region A: master for shard S" icon=region color=green
node L1 "Leader tier" at 2,2 in R1 icon=cache
node MDB "Primary MySQL" at 2,3 in R1 icon=mysql-icon sub="plus semi-sync replica"
node OB "Outbox worker" at 3,3 in R1 icon=worker
C -> FA
C ..> FB
FA:B -> L2:T : "miss or write"
FB:B -> L2:L : "miss or write"
L2 -> RDB : "read miss"
L1 -> MDB
OB -> MDB
L2:R -> L1:L : "write for shard S"
MDB -> RDB : "replication:\ninvalidate + refill"
PY ..> FA
```

**Write.** A user in region B follows an account: follower → local leader → master-region leader (this hop vanishes for a locally mastered shard). The leader runs one transaction: insert the edge, increment the count if inserted, insert an outbox row for the inverse. It commits, acknowledged by a replica in another zone (semi-sync, ours), and returns a changeset and version; the changeset updates the actor's follower before it answers, and the response carries the version as a token. The outbox worker then applies the inverse through the other shard, idempotently. Replication reaches region B's replica, and only then does the leader send invalidate and refill messages: earlier delivery would let a refill read stale data (the paper's ordering argument).

```arch
%% caption: The actor's follower is updated synchronously from the changeset, while the inverse edge and the other tiers converge asynchronously.
node C "Client" at 0,0 icon=user
node F "Follower A" at 0,1 icon=cache
node SL "Local leader" at 0,2 icon=cache
node ML "Master leader" at 2,2 icon=cache
node DB "Master MySQL" at 4,2 icon=mysql-icon
node OB "Outbox worker" at 4,1 icon=worker
node PL "Leader of shard B" at 2,1 icon=cache

C -> F : "1. assoc_add"
F -> SL : "2. forward write"
SL -> ML : "3. forward"
ML -> DB : "4. insert"
DB -> ML : "5. commit"
ML -> SL : "6. changeset"
SL -> F : "7. apply"
F -> C : "8. ok"
OB -> DB : "9. poll"
OB -> PL : "10. inverse"
DB -> SL : "11. invalidate"
```

**Read.** `assoc_time_range(viewer, friend, limit 50)`: hash `id1` to its shard and ask the follower that owns it. A hit returns from memory; a miss goes to the shard's leader, which answers from cache or issues one database query for that `(id1, atype)` however many followers ask, then fills. A cached count of zero answers a range with no database read.

## Sharding, hot lists and hot objects

The average shard is 2.6 GB, but one account with 10^8 followers is 10^8 × 64 B = 6.4 GB of rows (2.4 GB as cached 24 B entries). Mechanics: [25_partitioning_and_hot_keys.md](../building_blocks/25_partitioning_and_hot_keys.md).

**Follower lists** are never served in full on the hot path. Membership uses the inverse edge on the viewer's shard, `assoc_get(viewer, following, {celeb})`; the count is a cached counter. The feed's fanout scan reads a replica offline: 10^8 rows at an assumed 100k rows/s is 17 minutes ([007](007_news_feed_solution.md)).

**Hot writes.** A viral account gains 5,000 followers/s on one shard.

| Option | Gives | Costs |
|---|---|---|
| Do nothing | Simplest | 5,000 updates/s on one count row, which serialises at about 1,000/s (assumed, one commit each): 5× over |
| Sub-lists and sub-counters, k = 8 | 625 updates/s per counter | Every count read sums 8 rows and every range merges 8 lists, forever |
| Leader micro-batching (ours) | The leader already serialises the shard's writes, so it holds hot-list adds up to 100 ms and commits 500 rows plus one `count = count + 500`: 10 count updates/s | Up to 100 ms extra write latency, on flagged lists only |

Decision: micro-batch, because follows tolerate 100 ms and the cost stays in one leader. Split into buckets only if a shard's inserts exceed about 10k/s after batching (assumption).

**Hot reads.** One celebrity profile at 200k reads/s is 4× a follower server. The paper documents shard cloning and, above an access-rate threshold, a client-side cache with version checks; use both. Cloning across 8 followers gives 25k/s each, at 8 invalidations per write, fine for a rarely written object. A one-second client cache on 2,000 web hosts (assumed) sends at most 2,000 reads/s, a 100× cut, for one second of staleness. Followers run a count-min sketch and flag keys above 5,000 reads/s.

## Cache tiers and invalidation

| Option | Gives | Costs |
|---|---|---|
| Look-aside memcache, logic in clients | Familiar | A change to one edge reloads the whole list, uncoordinated clients stampede, read-after-write is hard (the paper's reasons for replacing it) |
| Cache service that knows the <abbr title="Application Programming Interface">API</abbr> (TAO) | Range, count, membership from cached prefixes; one coordinator per shard | A leader hop on every miss and write; a service to run |
| Replicas only | No invalidation | 2,900 hosts, still lagging |

Decision: the TAO shape. **Follower tiers** serve clients from demand-filled <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> prefixes; **one leader per shard per region** owns fills, invalidations and write order and caps pending queries, so many missing followers cause one query. The extra hop is acceptable at 4% misses.

**Invalidation.** After commit the leader sends followers an invalidate for an object or a refill for an association list (an invalidate would truncate the prefix). Messages carry versions and a follower ignores an older one. Only the issuing follower is updated synchronously.

**Lost messages are the failure that matters.** The paper has leaders queue messages for unreachable followers (verify the wording before quoting). We add two backstops (ours): a 24-hour jittered TTL on every entry, costing 6 tiers × 10^9 entries ÷ 86,400 = 69k refills/s (12% of leader traffic) to bound any missed invalidation; and a prober that writes canary edges per region and reads them from every tier, alerting on time-to-visible. Meta's 2022 engineering blog on cache consistency describes such a monitor (check details before citing).

**Cold caches.** A cold region sends 4.8M/s at a database sized for 420k/s (11.5×). Never rotate in an empty tier: replay a healthy tier's hot keys and ramp traffic over minutes.

## Consistency: read-your-writes, cross-region, the inverse edge

| Reader | Guarantee | Mechanism |
|---|---|---|
| Actor, same tier | Sees own write | Changeset applied synchronously |
| Actor after failover or eviction | Sees own write for 10 s | `min_version` token: a leader whose replica is behind forwards the read to the master region (ours) |
| Other user, master region | Tens of ms | Invalidate or refill after commit |
| Other user, replica region | Eventual; the paper reports lag under 1 s about 85% of the time, 3 s at 99%, 10 s at 99.8% | Messages ride the replication stream |
| Block and unfriend checks | Master truth | `critical = true`, which the paper uses for reads that must be right |

**Token cost.** If each write is followed by 5 reads in 10 s, 29k × 5 = 145k/s (1% of reads) carry tokens; only those that miss and hit a lagging replica cross regions: 1% × 4% × 14.5M = 5.8k/s. The memcache paper's remote marker ([block 30](../building_blocks/30_social_graph_and_caching_at_scale.md)) is per-key state that slows every reader of the key; a token affects only the actor, at the cost of threading it through every <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr>.

**The inverse edge.** Two-phase commit is atomic but a dead participant blocks the write; TAO accepts a "hanging association" and repairs it asynchronously; the outbox commits the inverse row with the forward edge and retries idempotently. Decision: outbox plus a nightly reconcile. Cost: the inverse lags (alert on p99 above 2 s). Reconcile scans a replica at 1 TB per host ÷ 100 MB/s = 2.8 hours.

**Region loss.** Promote the replica region for the affected shards. RPO equals replication lag (about a second, up to 10 s in the tail). Blocks and unfriends alone wait for a cross-region ack, one extra round trip on a rare write, so they survive.

## Counters

`COUNT(*)` over up to 10^8 rows is out. Keep `assoc_counts` in the write transaction, cache it on the same message flow, and micro-batch hot lists. Above 10^4 entries return `approx: true` and let the UI round ("1.2M"). Viral like counters (50,000/s) are stream aggregates (sub-counter arithmetic in block 30). "You liked this" is an edge lookup on the viewer's shard, not the counter. The reconcile corrects drift.

## Privacy at read time and two-hop queries

**Privacy.** Make visibility predicates evaluate on the viewer's shard. For 20 posts by 20 authors, asking each author's shard "did you block this viewer" costs 91 × (1 − (1 − 1/91)^20) ≈ 18 RPCs across a 91-server tier. Instead read the viewer's own `blocked` and `blocked_by` lists (tiny for almost everyone) and one `assoc_get(viewer, friend, author_set)`: all `id1 = viewer`, one <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr>. The price is that `blocked_by` is an inverse edge that lags by the outbox delay plus propagation. So use two layers (ours): the cheap list check when assembling a page, and the authoritative forward edge read critically when the post or profile is opened. A confirmed block is enforced at open time at once and in listings within seconds.

**Mutual friends.** `assoc_get(B, friend, id2set = A's newest 500)` is one 4 KB <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> (500 × 8 B), against two lists of up to 120 KB (5,000 × 24 B); above 500 it is a lower bound ("at least N").

**People You May Know.** Uncapped, two hops is 200 × 200 = 40,000 reads. Cap it (ranking in [31](../building_blocks/31_ranking_recommendation_and_experimentation.md)): top 50 friends by interaction, each one's newest 100 edges (the cached prefix), skipping friends with more than 5,000 edges: 1 + 50 = 51 reads, at most 5,000 candidates. Count mutual occurrences, drop friends and blocked users, keep 500, rank, store the top 200: 10^9 × 200 × 16 B = 3.2 TB. Refresh weekly and on debounced friend-add events: 10^9 × 51 ÷ 7 ÷ 86,400 = 84k reads/s, 1.5% of average load, in a class that [overload control](../building_blocks/28_overload_control_and_graceful_degradation.md) sheds first. Per profile view it would be 11.6k/s × 51 = 590k reads/s, so precompute.

## Failure behaviour

| Failure | Behaviour |
|---|---|
| One follower server (about 180 shards) | Clients use the other tier, already warm; misses climb to leaders; tokens cover cross-tier read-your-writes |
| A whole tier at daily peak | The other runs at 4.8M ÷ (91 × 50k) = 106%: shed PYMK batch and prefetch, disable hedging, fail nothing |
| Leader server | Followers send its shards' misses to the database under a cap; a replacement takes writes, then bulk invalidate (per the paper) |
| MySQL primary | Promote the semi-sync replica (no committed loss); writes to its 390 shards retry for tens of seconds, reads continue from cache |
| Replication lag spike | Tokens and critical reads go to the master region; alert on lag |
| Region loss | Survivors take 1.5×; masters move; RPO equals lag (blocks excepted) |
| Bad deploy | Canary 10 servers in one tier, then the tier, then the region; entries carry a format version; roll back the binary, never flush (a flush is a cold cache) |
| Stuck outbox worker | One-sided edges accumulate; alert on outbox age |

## Observability and interview close

SLIs: follower and leader hit ratio; p50, p99, p999 per path; MySQL reads per host; replication lag per shard; canary time-to-visible; outbox age; count drift.

The one paging alert: **follower hit ratio below 92% for 5 minutes** (baseline 96%). At 92% the database sees 14.5M × 8% × 25% = 290k/s (2× baseline), at 80% 720k/s, so it fires while there is time to react.

Trade-off to state: "I chose an `id1`-sharded MySQL graph behind follower and leader cache tiers, eventually consistent for everyone except the writer, because the graph cannot be partitioned by community and 99.8% of traffic is reads that are cheapest from memory. The cost is that others see writes seconds late, inverse edges lag behind an outbox, and a cold cache is an outage. If the product needed linearizable relationship changes, I would put only the few edge types that need it, such as blocks, on synchronous cross-region writes."

## Follow-ups the interviewer will ask

1. **"How does multi-region work?"** Each region holds a full copy. Each shard has one master region, chosen so users' own shards are mastered at home. Writes go to the master, reads and misses stay local, and messages fire only after the local replica applies the change. Non-master writers pay one round trip (80 to 150 ms, assumed).
2. **"What changes at 10× and 100×?"** At 10× (145M reads/s) the same per-server rate needs 5,460 followers and 350 TB of <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>, so first add a per-request cache in the web tier. At 100× add a mid-tier cache per cluster and route users to a consistent tier so each caches a slice. The database grows with data, not traffic.
3. **"Make friend and block changes linearizable."** One consensus group per shard across regions, reads through the leaseholder. Every write pays a cross-region quorum (100+ ms) and reads lose local latency unless you accept bounded staleness. Use it for blocks and credentials only.
4. **"What dominates cost?"** Followers: 546 of 870 hosts. Each point of follower hit ratio is 14.5M × 1% × 25% = 36k database reads/s; batching and client caching cut follower <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> directly; prefix length trades <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> for hit ratio.
5. **"How do you handle abuse?"** Per-viewer rate limits on enumeration, page caps, `NOT_FOUND` for hidden edges, follow-spam limits per actor, and read-time visibility so mutual-friend counts cannot reveal a hidden list.
6. **"Why not a graph database or Cassandra?"** The query shapes are fixed: a list, a count, a membership, two capped hops. At 6×10^11 edges a graph database shards and every hop is a network call. If pushed, use wide-column rows keyed `(id1, atype)` and keep the cache tier.
7. **"Delete an account with 10^8 followers."** Tombstone the object so privacy hides it at once, then delete in the background at 5,000 rows/s: 5.6 hours, inverse deletes through the outbox.

## Common mistakes

1. **Partitioning the graph by region or community.** It is too interconnected. Say every region holds a full copy.
2. **`COUNT(*)` and offset pagination.** Both scan the list. Keep counts in the write transaction and page by `(ts, id2)`.
3. **Ignoring the inverse edge.** It spans two shards and is not atomic. Name the hanging edge, the outbox, and the reconcile.
4. **Sizing the database from read <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>.** 14.5M ÷ 5k says 2,900 hosts; the cache makes it 1%. Storage sizes the database; the cold cache is the risk.
5. **One hot key, one server.** A 200k/s celebrity object is 4× a server. Clone it, add a client cache, detect with a sketch.
6. **Read-your-writes without a mechanism.** Say changeset, then tokens for failover and lag, and state the cost.
7. **Privacy at fanout or write time.** An unfriend must affect cached content. Check on read, on the viewer's shard.
8. **Uncapped friends-of-friends.** 40,000 candidates per user. Cap each hop, skip hubs, precompute.

## Going from L5 to L6

- **Migration.** From look-aside memcache over MySQL: service in front, shadow reads, dual writes with diffing, cut over per edge type, warm caches first.
- **Cost model.** Price per million reads as hosts, <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> and hit ratio: 870 hosts for 14M/s versus 2,900 for replicas only, and 36k database reads/s per hit-ratio point.
- **Ownership and blast radius.** Two follower tiers per region, deployed one at a time; a per-edge-type registry (inverse type, prefix length, count mode, privacy class) owned by product teams; a low-priority class for PYMK.
- **Build versus buy.** Buy MySQL and a cache primitive, build the association service (TAO is not downloadable); a graph database only for offline analysis.
- **Phasing and first measurements.** One region with a look-aside cache, then leaders, then replica regions with tokens, then the outbox and hot lists. Measure first: degree distribution, the top 1,000 lists' <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, miss rate per edge type, lag percentiles.

## Build exercise

Simulate SQLite shards, a leader per shard, two follower tiers, a lagging replica, an outbox worker, tokens and micro-batching.
Named assertions:

- `test_actor_reads_own_write_on_same_tier`: `assoc_add` then `assoc_range` on the issuing follower returns the edge before any invalidation arrives.
- `test_token_forwards_when_replica_lags`: with the replica behind the token, the read returns the edge; without a token it returns the stale list.
- `test_outbox_applies_inverse_after_crash`: kill the worker after the forward commit, restart, and assert the inverse exists once.
- `test_duplicate_add_does_not_double_count`: two identical adds leave `count = 1`.
- `test_leader_coalesces_concurrent_misses`: 100 concurrent misses on one list issue one database query.
- `test_hot_list_microbatch_updates_count_once`: 500 adds in 100 ms produce one transaction and one count update.
- `test_block_hides_cached_post`: a cached page drops a blocked author's post once the block is written.
- `test_two_hop_is_capped`: for a user with 5,000 friends, candidate generation issues at most 51 reads and returns at most 5,000 rows.
