# 018 — Distributed Cache: Full System Design Solution

## Goal and contract

A distributed cache absorbs read load from an authoritative data source and returns bounded-staleness data fast. The invariant is not "the cache is correct" — it is: the cache is disposable, the external source database remains the only source of truth, and losing every cache node must degrade latency, never correctness or business data.

The question fixes the numbers, and they are the contract for everything below:

- **2M requests/s** at peak across **500 nodes** holding **1 TB** of cache memory in total.
- Get/set **p99 under 5 ms**.
- Replacing a node must not remap more than **~1/N of the keys** (N = 500, so 0.2%).
- Source fallback must stay **at or under 5% of traffic** in steady state (100k requests/s).

This question asks you to design the cache itself, not just how a service uses one. So the hard decisions are three: who maps a key to a node and how that survives node churn; what keeps the hit ratio above 95% when memory, not request rate, is the scarce resource; and how invalidation races are bounded. What is promised: a bounded-stale value or a miss, never a wrong-key value. What is not promised: durability, linearizability, or that any given key is present.

Clients route each key to a node through a fixed table of hash slots, so adding, removing, or replacing a node remaps only the slots that change owner. TTL and a replacement policy bound memory so the cache never grows unbounded. A short client-side timeout plus fallback to source with request coalescing is what prevents a cache outage from becoming a full outage — cache eviction, node restart, or total cache-cluster loss must mean higher latency and more source load, never data loss, because nothing important is allowed to live only in cache.

## Estimates

All scale inputs beyond the question's five constraints are assumptions, labelled as such.

- **Request rate per node.** 2M req/s ÷ 500 nodes = **4,000 req/s per node**. One in-memory cache process serves on the order of 100k ops/s (assumption; benchmark your build), so a node runs at ~4% of its request capacity. So request rate is *not* what sizes this fleet; the 500 comes from memory and blast radius.
- **Memory per node.** 1 TB ÷ 500 = **2 GB of item data per node**. Assume a 1 KB value, a ~50 B key, and ~64 B of header and pointers per item = ~1.1 KB, plus ~10% allocator waste = **~1.2 KB per item**. 1 TB ÷ 1.2 KB ≈ **0.8 billion items**, about 1.6M per node. So capacity in *items* decides the hit ratio, and every byte of overhead is paid 800 million times.
- **Hit-ratio budget.** 5% of 2M = **100k req/s** may reach the source. With ~90% reads (assumption) that is 1.8M gets/s, so misses may not exceed 100k ÷ 1.8M ≈ 5.6%. Round to **hit ratio ≥ 95%** to leave margin.
- **What capacity does to the hit ratio** (illustrative; assumes Zipf popularity with exponent 1 over 2 billion distinct keys, and an ideal frequency-aware policy). Hit ratio for the top C keys ≈ H(C) ÷ H(N) with H(n) ≈ ln n + 0.577:
  - full 0.8B items: **96%**
  - 10% lost to fragmentation or overhead (0.73B): **95.4%**
  - half the capacity, i.e. one full replica of everything (0.4B): **92.8%**

  Each 10% of memory lost costs about 0.5 point, and the whole budget has about 1 point of slack. Real <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> sits a few points below the ideal. So we need: **no blanket replication** (it halves capacity and breaks the 5% budget), tight allocator waste, and an admission policy so scans cannot pollute the cache.
- **Blast radius.** One node is 0.2% of keys, so a node loss adds ~0.2% × 2M = **4k req/s** to the source, 4% of the budget: absorbable. A whole zone (1/3 of the fleet) adds **~670k req/s**, 6.7× the entire steady-state budget: not absorbable. And if you pack 25 of these 2 GB shards onto each of 20 hosts, one host loss removes 5% of the keys, **100k req/s**, the entire budget. So we need cross-zone copies of the hottest keys plus load shedding at the source, and at least ~100 hosts (host loss ≤ 1% of keys) even though 500 nodes is the nominal count.
- **Bandwidth.** 2M × ~1.05 KB ≈ 2.1 GB/s ≈ **17 Gbps** in aggregate, ≈ 34 Mbps per node. So bandwidth is not a constraint; large values and multi-get fan-out hurt the tail long before the NIC.
- **Connections.** Assume 20k client processes: 20k × 500 nodes = **10M connections**, 20k per node. Fine for an epoll server but a reconnect storm after a failover is real. So we pool connections, and offer a proxy tier for thin clients.
- **Latency budget for p99 < 5 ms.** Client encode plus pool checkout ~0.2 ms, in-zone network round trip ~0.3–0.5 ms, server work ~0.1 ms. That leaves ~4 ms of slack for queueing, allocator stalls, and one retransmit. So we set a **3 ms per-attempt deadline**, then count the request as a miss and fall back; we never retry the same node in the hot path.
- **Fleet sizing formula.** nodes = max(⌈data ÷ usable memory per node⌉, ⌈peak QPS ÷ safe QPS per node⌉) + headroom. Here the memory term gives 500 at 2 GB and the QPS term gives 20 at 100k ops/s. QPS binds only at ~25× today's traffic (4k × 25 = 100k). Virtual nodes do not appear in the formula at all: they change *evenness* of load, not capacity.

## API

```text
get(key)                     → {hit, value, flags, version, ttl_left} | {miss}
get_lease(key)               → {hit, value, ...} | {miss, lease_token} | {miss, wait_ms}
mget(keys[])                 → per-key results; the client splits by slot and fans out in parallel
set(key, value, ttl, flags?, lease_token?, if_version_gt?)
                             → stored | rejected(lease_void | version_older) | too_large
add(key, value, ttl)         → stored | exists          # for hold-offs and markers
delete(key, holdoff_ms = 0)  → ok                       # for holdoff_ms, add and set(no token) are refused
touch(key, ttl)              → ok | miss
```

- **Limits.** Key ≤ 250 B and value ≤ 1 MB (the memcached defaults); larger values are rejected with `too_large` so one bad write cannot evict a disproportionate share of the working set.
- **Namespaced keys.** `ns:entity:id:v3`. The namespace gives per-team quotas and pools; the schema version `v3` means a deploy that changes the value format reads different keys instead of choking on old bytes.
- **Idempotency.** `get`, `set`, `delete`, and `touch` are safe to retry. There is deliberately no `incr` or `append`: a retry after a timeout would double-apply, and counters belong in the source.
- **Errors and redirects.** `MOVED slot=1234 node=10.1.2.3:11211 epoch=18` means the client's slot map is stale, so update that slot and retry once. `BUSY` means the node is shedding load, so treat it as a miss. Cap redirects at 3 per request, then re-fetch the whole map.
- **Control plane.** `GET /slotmap?since_epoch=N` returns `{epoch, slots:[[start, end, primary, replicas]], nodes:[...]}`, about 16,384 × 16 B ≈ 260 KB, pushed or polled. `POST /nodes/{id}/drain` and `POST /slots/{s}/assign` are operator and automation calls, and each bumps the epoch.

## Data model

| Entity | Shape | Role | Partition key |
|---|---|---|---|
| `item` (node memory) | `key, value, flags, expire_at, version?, replacement metadata (recency or reference bit or frequency)` | **Derived** copy, never the truth | `slot = crc16(key) mod 16384`, then `slot → node` |
| `slot_map` | `epoch, slot → {primary, replicas, state STABLE / MIGRATING / IMPORTING}` | **Source of truth for routing**, in a small Raft-backed store, cached by every client | Single small document |
| `node` | `id, address, zone, host, memory_budget, state, last_heartbeat` | Membership | By `id` |
| `lease` (node memory) | `key → 64-bit token, issued_at` (expires in ~10 s) | Arbitrates fills and blocks stale sets | With the key's node |
| `hold-off / tombstone` (node memory) | `key → refuse-until or version` | Blocks a late set of an older value after a delete | With the key's node |
| `hot_key_set` | `key → copies, expires_at`, thousands of entries | Derived from sampled counters, pushed to clients | Replicated to all clients |

**Why slots, not raw hashes, as the partition unit.** A key's slot never changes; only the slot's owner does. That makes "how much moves when a node changes" a table edit you can reason about (33 slots), and it lets you migrate, replicate, and account for load per slot.

## Core mechanisms

| Mechanism | Behavior | Choose it when | Main weakness |
|---|---|---|---|
| Fixed hash slots + slot map | `slot = crc16(key) mod 16384`; a table assigns slots to nodes; a node replaced takes exactly its predecessor's slots. | You want exact balance and an exact bound on remap (Redis Cluster uses 16,384 slots). | Needs a control plane and clients that cache and refresh the map. |
| Consistent hashing with virtual nodes | Keys map to ring positions; nodes own ranges; virtual nodes smooth load distribution. | Any multi-node cache that must survive node add/remove without full remap, without a central table. | Without enough virtual nodes per physical node, load skews unevenly (~1/√V relative spread), and memory-bound nodes hit their cap on the heaviest one. |
| TTL + replacement policy (LRU/LFU) | Entries expire by time or get replaced under memory pressure. | Always, to bound memory and cap staleness. | Uniform TTL across many keys causes synchronized expiry ("thundering herd"). |
| TinyLFU admission | A new item enters only if its estimated frequency beats the would-be victim's. | Workloads with scans or one-hit wonders that would flush a Zipf head. | Extra CPU on the miss path and a sketch to maintain. |
| Leases | A miss returns a token that the later `set` must present; a delete voids it. | Concurrent fillers and writers on the same key. | Server-side state per in-flight fill; clients must implement the protocol. |
| Short client deadline + source fallback | Client gives up on a slow/dead cache node quickly and reads source directly. | Always, as the outage circuit breaker. | If not coalesced, a miss storm can multiply source load by concurrent request count. |
| Request coalescing (single-flight) | Concurrent misses for the same key collapse into one source fetch, others wait on it. | Any hot key or expiry-herd scenario. | Adds a small in-process synchronization point per key. |
| Read replicas / near-cache | Extra copies of hot keys near or colocated with callers. | Very hot keys exceeding one node's serving capacity. | Complicates invalidation — every copy must expire or be told to invalidate. |
| Gutter pool | A small spare pool (~1% of nodes) takes a failed node's traffic with short TTLs. | Absorbing a node loss without rehashing onto neighbors. | Serves slightly stale data for its short TTL. |

## Architecture and data flow

```arch
%% caption: Clients route by a cached slot map, the owning node answers hits and issues a lease on a miss, and only the lease holder reads the source.
grid 180x130
node cp "Control plane" at 3,0 icon=scheduler sub="Raft store"
node smap "Slot map" at 0,1 icon=kv sub="epoch N, cached"
node app "App process" at 1,1 icon=app sub="client library"
node n1 "Owning node" at 3,1 icon=cache sub="table + policy + TTL"
node gut "Gutter pool" at 0,3 icon=cache sub="short TTL"
node src "Source of truth" at 2,3 icon=db
app:L -> smap:R : "slot = crc16\nmod 16384"
app:R -> n1:L : "get_lease"
n1:T -> app:T : "hit"
n1:T -> app:T : "miss and token"
app:R -> n1:L : "set with token"
app:B -> src:T : "lease holder only"
cp:L -> smap:T : "new epoch"
n1:R -> cp:R : "heartbeat"
app:B -> gut:T : "node timeout" dashed
gut ..> src
```

**One read, end to end.** The client computes `crc16(key) mod 16384`, looks the slot up in its cached map, and sends `get_lease` to that node with a 3 ms deadline. On a hit it returns the value. On a miss the node returns a lease token (or `wait_ms` if another client already holds one for this key). The lease holder reads the source, then calls `set(key, value, ttl, lease_token)`; the node stores it only if the token is still valid. Waiting clients retry after a few milliseconds and hit. If the node does not answer inside the deadline, the client goes to the gutter pool, and if that also misses, to the source through a per-process single-flight.

**One write, end to end.** The writer commits to the source, then calls `delete(key)` on the owning node (and on any hot-key copies). It never writes the new value into the cache. The delete voids any outstanding lease for that key, so a slower reader's stale fill is rejected. A durable invalidation feed from the source's commit log replays the same deletes idempotently (see the invalidation section), so a lost delete is repaired, not permanent.

The hard decision is what to do when a cache node is unreachable within the client's deadline: block and wait, or fall back to source immediately. Blocking protects source load but risks cascading request queuing across the whole caller fleet when one node is slow; falling back to source immediately protects caller latency but risks a load spike hitting source exactly when cache capacity is degraded. This trades strict "always prefer cache" behavior for a bounded-latency guarantee to the caller — the deadline is set short enough that a fallback burst is survivable by source capacity headroom, which is a capacity-planning decision, not just a code decision. Replication for hot keys is a similar trade: it buys read throughput past a single node's limit at the cost of invalidation now needing to reach multiple copies instead of one, so replication is applied selectively to known-hot keys rather than uniformly.

## Single-node engine: memory, replacement, expiry

**Structure.** A hash table maps key → item; each item carries its value, `expire_at`, and replacement metadata. Exact LRU adds a doubly linked list: every hit splices the item to the head, which costs two 8-byte pointers per item (16 B × 1.6M items ≈ 26 MB per node) and, worse, a *write on every read* under a lock. That write is what stops a multi-threaded server from scaling, so real engines approximate. The hash table must resize incrementally (Redis rehashes a few buckets per operation; the Facebook paper describes automatic hash-table expansion in memcached) because a stop-the-world rehash of 1.6M entries is a p99 spike.

| Policy | Mechanism | Per-item cost | Weakness |
|---|---|---|---|
| Exact LRU | Hash table + doubly linked list | 16 B pointers, list write on hit | Lock contention; a one-time scan flushes the working set |
| Sampled LRU (Redis) | On pressure, sample K random keys (default 5; 10 is close to true LRU per the Redis docs) and drop the oldest | ~3 B timestamp | Approximation noise; still recency-only |
| CLOCK | Ring with a reference bit set on hit; a hand sweeps, clearing bits and dropping unmarked items | 1 bit | No frequency signal, coarse |
| LFU with decay (Redis 4+) | 8-bit logarithmic counter that decays over minutes | 1 B | Slow to admit a newly popular key |
| TinyLFU admission (Einziger, Friedman, Manes, ACM ToS 2017) | Count-Min sketch of small counters, periodically halved; the candidate replaces the victim only if its estimated frequency is higher | ~0.5 B per item (≈0.8 MB per node here) | CPU on each insert; needs a small recency window for bursty new keys (W-TinyLFU, as in Caffeine) |

**Decision: sampled or segmented LRU for ordering, plus TinyLFU admission.** It gives scan resistance and a frequency-aware Zipf head, at the cost of a sketch and one comparison per insert. The cost is acceptable because the 5% budget has only ~1 point of slack (see Estimates) and a scan-polluted cache loses several. Bound the work per `set`: evict inline at most a few items, and keep a free-memory watermark with a background reclaimer, so a large set never stalls behind a long eviction loop.

**Allocation and fragmentation.**

| Allocator | How it works | Waste | Failure mode |
|---|---|---|---|
| Slab classes (memcached) | 1 MB pages are cut into fixed chunks per class; chunk sizes grow by a factor (default 1.25) | 0–20% internal per item, ~10% on average, no external fragmentation | *Slab calcification*: pages stay assigned to a class after the size mix shifts, so you need a rebalancer |
| General allocator, jemalloc-style (Redis default on Linux) | Fine size classes, arenas, per-thread caches | Less internal waste, but external fragmentation grows as items of different ages are freed | The resident-to-used ratio drifts upward; Redis exposes `mem_fragmentation_ratio` and an active-defrag option |
| TTL-grouped segments (research, e.g. Segcache, NSDI 2021) | Items with similar expiry share a segment that is freed whole | Low | New, less proven; more complex |

We plan for **~10% waste** (already in the ×1.2 KB item footprint) and alert when the resident-to-used ratio exceeds ~1.2, because 10% of memory is ~0.5 hit-ratio points.

**TTL expiry.** *Lazy:* on `get`, if `expire_at` has passed, delete the item and return a miss. *Active:* a background loop samples random keys that have a TTL and deletes the expired ones, repeating while a large share of the sample was expired (the Redis documentation describes 20 keys, 10 times a second, repeating above 25%). Lazy alone leaves dead items holding memory until touched; active sampling alone can lag behind bursts. Do both, and track "expired but unreclaimed bytes" because dead items steal capacity from live ones.

## Cluster topology and routing

Three ways to put the routing table somewhere:

| Option | How a request finds its node | Gives | Costs |
|---|---|---|---|
| Client-side consistent hashing (ketama-style ring, or rendezvous / jump hash) | Every client holds the node list and computes the owner | No extra hop, lowest latency, no router fleet | Membership drift makes two clients disagree, so a key can live on two nodes and serve stale copies; every language needs the library; 10M connections |
| Proxy tier (twemproxy, mcrouter, Envoy-style) | Clients talk to a proxy that owns routing, pooling, retries, replication, and warm-up | Thin clients, central policy, pooled connections (Facebook's mcrouter coalesces connections for this reason) | An extra hop (~0.2–0.5 ms in-zone), and a fleet to run: 2M ÷ 100k per proxy = 20, ~40 with 2× headroom |
| Server-side fixed slots with redirects (Redis Cluster) | `crc16(key) mod 16384` → slot → owner from a cached map; a wrong node replies `MOVED` | Exact balance, explicit move unit, self-correcting stale clients | A control plane and a smart client; more slots needed beyond ~1,000 nodes |

**Decision: fixed slots (16,384), a smart client that caches the slot map and follows `MOVED`, and an optional proxy tier for thin clients.** It gives exact balance and an exact remap bound at the cost of running a small control plane. That cost is acceptable because 500 nodes make an unbalanced ring expensive: with V virtual nodes a node's share varies by ~1/√V, so at V=100 the heaviest of 500 nodes sits at about 1 + 2.9 × 0.1 ≈ **1.3× the average**, and since memory is the binding constraint, the heaviest node sets the per-node cap and strands ~23% of your 1 TB (1 − 1/1.3). With slots, 16,384 ÷ 500 = 32.8, so every node owns 32 or 33 slots: **at most 0.7% above average**, by construction.

**Node replacement and scale-out.** The replacement takes over exactly its predecessor's 33 slots: 33 ÷ 16,384 = **0.2% of the keys**, ~2 GB, which meets the ~1/N bound, and no other node's keys move. Adding node 501 takes ~33 slots spread across the others, again ~0.2%. Because the cache is disposable, "moving" a slot means changing its owner and letting the new owner start cold, or optionally copying entries first (see cold start). During a copy-based move the slot is `MIGRATING` on the old owner and `IMPORTING` on the new one; a key the old owner no longer has gets an `ASK` redirect (one-off, do not update the map) while a completed slot gets `MOVED` (permanent, update the map).

## Membership, failure detection, and failover

| Option | Detects failure by | Gives | Costs |
|---|---|---|---|
| Gossip (Redis Cluster bus, SWIM-style) | Peers ping each other, a node is flagged after a timeout, and it is declared failed when a majority of primaries agree | No central component; scales out | Slow, probabilistic convergence; harder to reason about during partitions |
| Central control plane (small Raft group) + heartbeats | Nodes heartbeat every second; the controller confirms with independent observers before acting | One versioned slot map, easy audits and staged changes | A control plane to run; it must not sit on the request path |

**Decision: a Raft-backed control plane owns the epoch-numbered slot map, and the data plane keeps working from the last-known map if the control plane is down.** No new failovers happen during that outage, which is acceptable because cache reads already degrade to the source (see [Consensus and coordination](../building_blocks/19_consensus_and_coordination.md)).

**Detection and failover timeline** (all timings are assumptions to tune):

1. **t = 0–3 s.** A node misses 3 one-second heartbeats, or clients trip a circuit breaker on 5 consecutive timeouts within a second. The controller asks two independent observers before it trusts one client's view.
2. **Immediately.** Clients route that node's slots to the gutter pool (~1% of 500 = **5 nodes, 10 GB**), or straight to the source. Gutter entries use a short TTL so they never need invalidation, as in the Facebook Memcache design (Nishtala et al., NSDI 2013). The paper distinguishes this from rehashing keys onto the survivors, which risks overloading whichever node inherits a very hot key.
3. **After ~30 s of confirmed failure.** The controller assigns the slots to a spare or a promoted replica, bumps the epoch, and clients pick it up via `MOVED` or the map watch. The 30 s hysteresis stops a flapping node from causing constant remapping.
4. **On rejoin.** A node that comes back after its slots were reassigned **must wipe them**: its data predates deletes it never saw, and serving it resurrects stale values. It checks the epoch at startup and starts empty for any slot it no longer owns.

**Replication and what is lost.** Copies are asynchronous primary-to-replica (Redis Cluster's design; its spec states that acknowledged writes can be lost on failover). Synchronous replication across zones would add a ~1 ms round trip to every `set` and consume the 5 ms budget for a cache, so we accept async. What a failover loses is the last few milliseconds of writes. Lost *sets* are harmless (they become misses). A lost *delete* is dangerous: the promoted replica still holds the old value and would serve it until TTL. The fix is to **replay the invalidation feed for the last 60 s after every promotion**; deletes are idempotent, so replay is safe.

**Decision on what to replicate.** Blanket replication halves capacity (hit ratio 96% → 93% in the model above) to protect against a 0.2% event, so the default is **RF = 1**, spread across three zones. Replicate only by heat: under the same Zipf model the top 1% of keys (20M keys, ~25 GB, 2.5% of the 1 TB) carry ~79% of requests. One extra copy of those in a *different zone* costs 2.5% of memory and cuts the zone-loss source spike from ~670k req/s to roughly 21% × 2M ÷ 3 ≈ **140k req/s**, since only tail keys in the lost zone miss. That is the cost/benefit that justifies replicating by heat.

## Capacity and storage

The working set is not the 10 GB a 10M-key story would suggest: the question gives 1 TB, about 0.8 billion items, which is the entire reason to keep the fleet memory-bound and to fight for every byte. Size the fleet with the formula in Estimates: memory sets the node count (500 at 2 GB), QPS does not (20 at 100k ops/s), and virtual nodes only change how evenly keys spread, never how many nodes you need. Size the ring or slot table so the heaviest node's memory share stays under its cap, and account physical RAM at about 1.3× the data budget: 2 GB of items + ~20 MB of hash table + ~1 MB of sketch + ~320 MB of connection buffers (20k connections × ~16 KB, assumption) puts a node near 2.4 GB before the OS.

Do not use a single global TTL for every key — stagger TTLs with jitter so millions of entries don't expire in the same second and stampede the source simultaneously. Concretely: 1M keys written in the same second with a fixed 10-minute TTL all expire in the same second, a 1M req/s spike at the source; with ±10% jitter (a 120 s window) the same cohort expires at ~8k req/s. Set the base TTL from the product's staleness tolerance, not from memory pressure: memory is managed by the replacement policy.

For keys that exceed what one node can serve even with correct routing, see the skew section below. Do not treat a node crash or a full cluster restart as data loss — if it would be, the cache has become a hidden source of truth, which is the core anti-pattern here; verify by asking "if this cache vanished right now, would any business fact disappear" and if the answer is yes, that data belongs in the source store.

## Miss storms and request coalescing

A miss storm is many callers missing on the same key at once: after a TTL expiry, after a delete on a popular key, or after a node goes cold. Defences from cheapest to strongest:

| Defence | What it does | Numbers |
|---|---|---|
| Single-flight per process | Concurrent local misses for a key share one source fetch | 20k client processes each still send one, so 20k source reads at one expiry |
| Lease at the cache node | The node hands one token per key per ~10 s; other clients wait a few ms and retry | 1 source read instead of 20k. The Facebook paper reports that for herd-prone keys the peak database rate fell from 17K/s to 1.3K/s |
| TTL jitter, or probabilistic early refresh (Vattani et al., VLDB 2015) | Spread expiry, or refresh a little before it | Cohort of 1M keys: 1M/s → ~8k/s |
| Stale-while-revalidate | Serve the recently deleted or expired value, marked stale, while one client refreshes it (the paper describes a recently-deleted-items structure for this) | Waiters return in microseconds; stale for the fill time |
| Negative caching | Cache "not found" for 30–60 s | Stops a flood of nonexistent keys from reaching the source |

**Decision: lease + per-process single-flight + jitter, with negative caching for lookups by user-supplied ids.** It bounds source load per key to one read per lease interval, at the cost of a small wait for the losers and a protocol the client library must implement. Source-side, put a concurrency cap on cache-fill queries so even a bug in this layer cannot exceed the 100k req/s budget (see [Overload control](../building_blocks/28_overload_control_and_graceful_degradation.md)).

## Invalidation races, versions, and leases

**The set-after-delete race.** With cache-aside (read → miss → read source → set), a slow reader can undo a writer's invalidation:

```arch
%% caption: The lease token issued at miss time is voided by the writer's delete, so the slow reader's late set is rejected instead of caching a stale value.
node A "Reader A" at 0,0
node N "Cache node" at 1,0
node D "Source DB" at 2,0
node B "Writer B" at 1,1

A -> N : "1. get_lease k\n2. miss, token L1"
A -> D : "3. read k\n4. value v1"
B -> D : "5. write k as v2"
B -> N : "6. delete k (token L1 voided)"
A -> N : "7. set k v1 with L1\n(rejected)"
```

Without the token, A's `set` of v1 lands after B's `delete` and v1 stays until TTL — possibly minutes, and possibly forever if nobody sets a TTL.

| Approach | How it works | Handles the race? | Cost |
|---|---|---|---|
| TTL only | Accept staleness up to the TTL | No, just bounds it | Simple; staleness = TTL |
| Update in place on write (`set` the new value) | Writer overwrites the entry | No: two writers' cache updates can arrive in the opposite order of their DB commits | Stale forever until TTL |
| Delete on write + hold-off | Delete, and refuse `add` for a short window (the paper uses 2 s on cold-cluster deletes) | Mostly; a slow reader beyond the window still wins | A timing assumption |
| Versioned conditional set | Every value carries the source row's monotonic version; `set` applies only if `version > stored`; a delete leaves a tombstone with the deleted version for a few seconds | Yes, if the source provides a monotonic version | Tombstones use memory; needs a version column |
| Leases (Nishtala et al., NSDI 2013) | A miss returns a 64-bit token bound to the key; `set` must present it; a delete voids it, in the manner of load-linked/store-conditional | Yes, for cache-aside fills | Per-key server state; client protocol; a herd control as a bonus |

**Decision: delete-on-write (never overwrite) + leases for fills, and version checks where the source exposes a monotonic version.** It closes the stale-set window at the cost of server-side lease state and a client protocol, acceptable because it also delivers the herd protection above for free.

**Lost invalidations.** A delete can still be dropped on the network or lost in a failover. Two backstops: a **durable invalidation feed** (the source's commit log carries the keys to delete; a daemon tails it and replays idempotently, batching many keys per packet, which the Facebook paper reports as an 18× increase in deletes per packet), and a **TTL cap** on every entry so no bug leaves a value forever. See [Caching](../building_blocks/07_caching.md) for the general patterns.

## Skewed keys and load spikes

**The problem.** Popularity is Zipfian: in the model above the top 2M keys (0.1% of keys) take ~69% of requests. A single viral key can exceed one node's capacity; the Facebook paper notes a single key can account for 20% of a server's requests. Take a key at 300k req/s (assumption): that is 3× a node's safe 100k ops/s and 15% of the whole fleet's traffic, all on one of 500 nodes.

| Mitigation | Effect on the 300k req/s key | Cost |
|---|---|---|
| Near-cache in each client process (TTL 1 s) | ≤ 20k client processes × 1 fetch/s = **≤ 20k req/s** at the node, a 15× cut | Up to 1 s of staleness; memory per client |
| Replicate the key to k nodes (`hot_key_set`, clients pick a copy at random) | k = 4 gives **75k req/s** per node | A delete must reach all k copies; the copy nodes lose that memory |
| Key splitting (`key#0..k-1`, random suffix on read) | Same as replication, but chosen by the application | The application owns the fan-out and invalidation |
| Request coalescing + lease | Removes miss amplification only | Does not reduce hit traffic |
| Load shedding at the node (`BUSY`) | Protects the node's other keys | Hot key sees errors, so needs the copies above |

**Detection.** Each node samples ~1 in 100 requests into a small heavy-hitter sketch (see [Top-K trending](028_top_k_trending_solution.md)) and reports its top keys every ~10 s. A key above ~10% of a node's safe rate joins `hot_key_set`, pushed to clients within seconds; it leaves when the rate has been under a lower threshold for a few minutes (hysteresis).

**Decision: near-cache with a 1 s TTL first, replicated copies for keys that still exceed a node, and no application key-splitting unless the platform cannot do it.** The near-cache is a client-only change that cuts load an order of magnitude at the price of bounded staleness the caller already tolerates. Details of the general hot-key toolbox are in [Partitioning and hot keys](../building_blocks/25_partitioning_and_hot_keys.md).

## Cold start and warm-up

A node that is new or restarted has an empty table. Its 33 slots are 0.2% of keys, ~4k req/s of extra source load, which is fine. A whole cold cluster is the real problem: 2M req/s of misses against a source budgeted for 100k.

**How fast can a cold cache fill?** Under the Zipf model, and if the source can serve the full 100k reads/s budget purely as fills:

| Cached keys | Hit ratio | Time at 100k fills/s |
|---|---|---|
| 20M (top 1%) | ~79% | ~3 min |
| 220M | ~90% | ~37 min |
| 670M | ~95% | ~1.9 h |

The head warms in minutes; the last points of hit ratio take hours. And misses are not just fills: at 79% the cold cluster generates 0.21 × its traffic in source reads, so with a 100k/s budget it can take only 100k ÷ 0.21 ≈ 476k req/s, **about 24% of the traffic**. So **ramp traffic onto a cold cluster in steps sized to keep misses under the source budget**, rather than flipping it all at once.

Two ways to warm faster: (1) **copy from a warm peer** — the Facebook paper's cold-cluster warm-up lets clients in a cold cluster read from a warm cluster and populate their own cache, bringing a cold cluster to full capacity in hours rather than days; deletes to the cold cluster carry a 2 s hold-off so a stale copy from the warm side cannot be re-added; or (2) **replay recent hot keys** from the sampled top-K list. A node-to-node copy of one replacement's 2 GB at a throttled 200 MB/s takes 10 s.

## Multi-region and cross-cluster invalidation

Each region runs its own cache cluster over its own replica of the source. Caches are never replicated across regions: a cross-region round trip (tens of ms) already exceeds the 5 ms budget, and a cache is cheaper to refill than to ship.

```arch
%% caption: Invalidations ride the database's own replication stream so a replica region never invalidates before its database has the new row.
group ra "Home region" color=blue icon=region
node w "Writer" at 0,0 in ra icon=app sub="home region"
node db1 "Primary DB" at 0,1 in ra icon=db
node inv1 "Invalidation daemon" at 0,2 in ra icon=worker
node c1 "Home cache cluster" at 0,3 in ra icon=cache
group rb "Region B" color=blue icon=region
node db2 "Replica DB" at 2,1 in rb icon=replica sub="region B"
node inv2 "Invalidation daemon B" at 2,2 in rb icon=worker
node c2 "Region B cache cluster" at 2,3 in rb icon=cache
w -> db1
db1 -> inv1 : "commit log"
inv1 -> c1
db1 ..> db2 : "replication stream"
db2 -> inv2 : "commit log after apply"
inv2 -> c2
```

**The trap.** If the writer in the home region deletes the key in region B's cache directly, the delete can arrive *before* replication delivers the new row. A region-B reader then misses, reads the old row from the lagging replica, and caches the stale value indefinitely. The Facebook paper avoids this by having a daemon on each database tail its commit log and issue the deletes *after* commit, and in replica regions only after replication applies the change; it also batches deletes and replays them if a router or cluster was down.

**Read-your-writes after a write from a non-home region.** The paper's *remote marker*: the writer sets a marker for the key in its region, writes to the home region, and deletes the local key. A later miss that finds the marker reads from the home region instead of the possibly lagging local replica, trading extra latency on that miss for a lower chance of reading stale data. Markers are state, not cache: evicting one is not safe, so they live in a separate pool.

**Staleness bound.** With this design a cached value is at most (replication lag + invalidation delay) stale if the delete arrives, and TTL-stale if it does not. State both numbers; see [Multi-region and global traffic](../building_blocks/27_multi_region_and_global_traffic.md).

## Failure and abuse behavior

| Case | Correct behavior |
|---|---|
| One cache node dies | Slot map stays fixed. Clients trip a breaker in ~1 s and serve that node's slots from the gutter pool or the source; after ~30 s the controller assigns the slots to a spare. Impact ~0.2% of keys, ~4k req/s of extra source load. |
| Zone loss (1/3 of nodes) | Hot copies in other zones keep serving the head; the source sees roughly 140k req/s of extra tail misses instead of ~670k. Load shedding and per-key leases protect the source; page on source-fallback ratio. |
| Full cache cluster loss | All reads fall back to source; source must have enough headroom (or a load-shedding policy) to survive the temporary full-traffic hit. Ramp traffic back onto the refilled cluster in steps (cold-start section). |
| Control plane down | Data plane runs on the last-known slot map; no new failovers until it returns. Alert, but nothing user-visible. |
| Client with a stale slot map | Gets `MOVED`, updates the slot, retries once; after 3 redirects re-fetches the whole map. The node never serves a slot it does not own. |
| Node returns after being replaced | Checks the epoch and wipes slots it no longer owns before serving; otherwise it would serve values that missed later deletes. |
| Slow node (gray failure) | Per-node latency outlier ejection and a hedged request to the gutter/replica after the p95 time; p99 stays under 5 ms without waiting for a hard failure. |
| Hot key overwhelms one node | Detect via per-key QPS sampling; add a near-cache and replicas, and coalesce concurrent misses. |
| Uniform TTL causes expiry herd | Add jitter to TTLs; stagger writes so expiry is naturally spread. |
| Node rebalance after scale-out | Only the reassigned slots go cold (~0.2% of keys); monitor rebalance-triggered miss rate and warm from the old owner when possible. |
| Stale value served past acceptable staleness | Bound TTL to the product's staleness tolerance; invalidate explicitly on writes where staleness is unacceptable rather than relying on TTL alone; lost deletes are replayed from the invalidation feed. |
| Cache poisoned with a bad/oversized value | Validate value size/shape before caching; cap max entry size at 1 MB so one bad write can't evict a disproportionate share of the working set; schema-versioned keys prevent misreading old formats. |
| Bad deploy of the cache software | Canary on ~1% of slots (5 nodes) and watch hit ratio, p99, and fragmentation; a value-format or key-format change ships as a new key version so old and new coexist. |
| Tenant floods the cache with scans | Per-namespace pools and quotas (the paper's separate pools) plus TinyLFU admission keep one team's scan from evicting another's working set. |
| Source down while cache is up | Serve stale within a bounded age and negative-cache errors briefly, rather than passing every miss through. |

## Observability and interview close

Measure hit ratio and eviction rate per node and per namespace, the *age of the oldest evicted item* (a shrinking value means the working set is outgrowing memory), key-distribution skew across the slot map, node error rate and timeout rate, source-fallback QPS (the leading indicator of cache degradation), rebalance-triggered key movement volume, hot-key concentration (top-N keys by request share), resident-to-used memory ratio, slot-map epoch skew across clients, `MOVED` rate, and client-side get p99 (measured at the caller, not on the server, since queueing lives in between).

**The one paging alert:** source-fallback ratio above **5% of traffic for 10 minutes** (or source-fallback QPS approaching the source's safe capacity). Everything else is a ticket: hit-ratio drift, a node above its memory cap, slow rebalances. Alert on any single node's QPS share exceeding its ceiling as a ticket unless it coincides with the paging condition.

Trade-off to state: "The cache is disposable by design — the source database is truth, and every read path has a short deadline plus coalesced, lease-protected fallback, so losing cache nodes costs latency and source load, never correctness. I chose fixed hash slots over a virtual-node ring to get exact balance and an exact 1/N remap bound, at the price of a small control plane; and I replicate only the hottest ~1% of keys across zones instead of everything, because full replication halves an already memory-bound capacity and would push the hit ratio below the 5% source budget."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Each region has its own cache cluster over its own source replica; caches are never replicated across regions. Invalidations follow the database's commit log and apply in a replica region only after replication lands, with remote markers for read-your-writes after a non-home write. Staleness is bounded by replication lag plus invalidation delay, and by TTL if a delete is lost.
2. **"What changes at 10× and 100× scale?"** At 10× traffic, QPS per node is 40k/s, still under a 100k/s safe rate, so grow memory per node ×10 (20 GB nodes) and keep 500 nodes and the same blast radius. QPS becomes binding near 25× (4k × 25 = 100k), so at 100× you need ~2,000 nodes by QPS alone and 16,384 slots is only ~8 per node: raise the slot count and shard the control plane by keyspace cell.
3. **"What if I need stricter consistency: read-your-writes, or linearizable reads?"** Do not cache those reads, or make them version-checked: the writer keeps the committed version, and a read whose cached version is older than that misses and reloads from the source. True linearizability means the cache is never the arbiter: the source decides, and the cache is an optimization the read may bypass.
4. **"What dominates cost, and what are the knobs?"** RAM. One hit-ratio point equals 1% × 1.8M ≈ **18k req/s** of source reads, and 10% of memory is about 0.5 points (~9k req/s), so you price memory against source capacity. Knobs: value compression, smaller items, TinyLFU admission, TTLs, and dropping the replicated hot tier.
5. **"How do you defend against abuse?"** Namespaced quotas and separate pools so one team's scan cannot evict another's data, a 1 MB value cap, TinyLFU so one-hit wonders are not admitted, negative caching plus a per-client fill limit against enumeration of nonexistent keys, and schema-versioned keys against poisoned or mis-decoded values.
6. **"Why not just replicate every node?"** It halves usable capacity: hit ratio falls from about 96% to 93% in the model, which is 7% × 1.8M = 126k req/s of misses, over the 100k budget, to protect against a 0.2% event. I would concede it if the source has the headroom or memory is cheap relative to the source, but selective replication of the top 1% gets most of the availability benefit for 2.5% of the memory.
7. **"What if I told you to use consistent hashing with virtual nodes instead of slots?"** A ring works, and it needs no central table. I would raise V until the heaviest node is within ~10% of the mean (V of about 1,000) and accept a larger membership state. The reason I prefer slots here is the memory cap: at V=100 the heaviest node is ~1.3× the mean, which strands ~23% of the 1 TB, and slots make the 1/N replacement bound a table edit instead of a statistical property.
8. **"Why not write-behind to make sets fast?"** Because it makes the cache the only holder of an acknowledged write, which is exactly the hidden-source-of-truth anti-pattern: a node loss loses data the caller was told was saved. Write-behind is a different system (a buffered write path with its own durability story), not a cache setting.

## Common mistakes

1. **Sizing the fleet from virtual nodes or per-node QPS.** Virtual nodes change evenness, not capacity, and QPS is 4% of a node here. Size from memory and blast radius, then check evenness.
2. **Replicating everything "for availability".** It halves the items you can hold; with a 1-point hit-ratio margin that breaks the 5% source budget. Replicate by heat.
3. **Rehashing a dead node's keys over the survivors.** A ring or `hash mod N` re-route sends a hot key's load onto one neighbor, and `mod N` remaps nearly every key. Keep the slot table fixed and reassign to a spare or gutter.
4. **Writing the new value into the cache on update.** Two writers' cache updates can arrive in the opposite order of their commits and leave the older value forever. Delete on write, and let the next reader fill under a lease.
5. **One global TTL.** Every entry written together expires together; you get a periodic source spike. Add jitter and set TTL from staleness tolerance.
6. **No value-size cap, namespaces, or quotas.** One oversized or poisoned write, or one team's scan, displaces the shared working set. Cap at 1 MB, pool by namespace, and use an admission filter.
7. **Judging the cache by average hit ratio.** A 96% average can hide a namespace at 60% that is driving the source. Track per-namespace hit ratio, miss cost, and client-side p99.
8. **Letting a returned node serve old slots.** After reassignment its data predates deletes it missed. Epoch-check on rejoin and wipe.

## Going from L5 to L6

- **Migration path.** Start with a managed memcached or Redis Cluster behind a client wrapper that owns the deadline, single-flight, and jitter. Add the proxy tier when you have several languages, dual-read from the new tier in shadow, compare hit ratio and latency, then shift traffic in steps.
- **Cost model.** Price RAM against the source: 1 hit-ratio point ≈ 18k req/s of source capacity. Show the marginal dollar per point for more memory, compression, and admission tuning, and stop where a point costs more than the source capacity it saves.
- **Ownership and blast radius.** Split by namespace into pools with their own quotas and on-call, so a noisy tenant cannot evict others; run independent cells (a full copy of the cache and control plane per cohort) so a bad deploy or a corrupted slot map touches a fraction of traffic.
- **Build versus buy.** A managed Redis/memcached is right until you need behaviour it cannot offer: leases plus versioned deletes, a commit-log invalidation feed, or a 1-point hit-ratio budget. Buy the engine and build the client, the invalidation pipeline, and the control-plane policy.
- **Phased evolution.** Near-cache and single-flight first (client-only, biggest cut in load), then the cluster tier with leases, then the hot-key replicated tier, then regional invalidation.
- **What to measure first.** The item-size distribution and a hit-ratio-versus-memory curve replayed from production traces. Every number in Estimates (Zipf exponent, item size, working set) is an assumption until that curve exists.

## Build exercise

Build a simulation of the routing and invalidation logic with an in-memory map as the "source":

1. Implement a 16,384-slot table over 500 simulated nodes, and a hash-ring with 100 virtual nodes for comparison. Route 1M keys through both.
2. Implement a node with a lease table and delete-voiding, a single-flight wrapper for clients, and jittered TTLs.

Named assertions:

- `test_replace_remaps_at_most_one_over_n`: replace one node and assert at most 0.2% (+ tolerance) of keys change owner, and no key on any other node moves.
- `test_slots_balanced_within_one_percent`: assert the fullest node has at most 1.01× the mean slots, and that the ring's max/mean is measurably worse (around 1.3×).
- `test_lease_rejects_stale_set`: reader A takes a lease, writer B deletes the key, and A's `set` with the old token returns `rejected(lease_void)`.
- `test_single_flight_one_source_call`: 100 concurrent misses on one key produce one source read.
- `test_jitter_spreads_expiry`: expire 1M keys written in one second with ±10% jitter and assert the peak per-second expiry is under 1% of the cohort.
- `test_returned_node_wipes_reassigned_slots`: fail a node, reassign its slots, bring it back with old data, and assert none of that data is served.
- `test_tinylfu_scan_resistance`: run a Zipf workload with an interleaved one-time scan and assert the hit ratio with admission is higher than plain <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr>.
