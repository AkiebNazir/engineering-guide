# 023 — Distributed Key-Value Store: Full System Design Solution

## Goal and contract

A leaderless, Dynamo-style store that prioritises **availability and partition tolerance**, with **tunable consistency** per request. The contract:

- `put(key, value, context)` returns success once `W` replicas have durably stored the write.
- `get(key)` returns the value(s) seen by `R` replicas; if concurrent conflicting versions exist, it returns all of them plus a **context** (version vector) that the client passes back on the next put to resolve them.
- With `R + W > N`, a successful read sees the latest successful write (barring concurrent writes and sloppy-quorum edge cases). With smaller `R`/`W`, the store is faster and more available but eventually consistent.

Why leaderless rather than leader-per-partition: the requirement to stay **writable during partitions** and survive arbitrary two-node failures without an election window. A Raft-per-partition design (like CockroachDB/TiKV) would give linearizability instead; that is the trade-off revisited at the end.

## Capacity

- Data: 100 TB × replication factor 3 = 300 TB raw. At ~2 TB of usable data per node (leaving room for compaction and growth), about **150 nodes** at the end state. At 10 TB the same arithmetic gives 30 TB ÷ 2 = 15 nodes, but the peak QPS applies from day one, so throughput sizes the early fleet (next bullet).
- Load: 250K ops/s peak ÷ 150 nodes ≈ 1,700 ops/s per node, and each op touches `N = 3` replicas, so ~750K replica operations/s cluster-wide and ~5,000 per node. Assuming a node sustains about 10,000 replica ops/s of 10 KB values at p99 < 10 ms (an assumption to load-test), throughput needs 750K ÷ 10K = 75 nodes, so we **start at ~75 nodes, not 20**, and capacity takes over as data grows toward 100 TB.
- Bandwidth: clients read 200K × 10 KB = 2 GB/s and writes replicate 50K × 10 KB × 3 = 1.5 GB/s, about 23 MB/s per node at 150 nodes (47 MB/s at 75), well within 10 GbE. Peak ingest of 500 MB/s would be 43 TB/day if sustained, versus the ~250 GB/day needed to grow by 90 TB in a year, so peak writes are mostly overwrites and compaction is the real disk cost: at an assumed 10× write amplification, 1.5 GB/s × 10 ÷ 150 = 100 MB/s of disk writes per node.
- Latency: an in-region round trip is ~0.5 ms; waiting for the 2nd-fastest of 3 replicas keeps p99 well under 10 ms if nodes are not overloaded.

## API

```text
put(key, value, context?, consistency = {W})      → ok | error
get(key, consistency = {R})                        → [(value, context)]   # >1 item means concurrent versions
delete(key, context?)                              → ok                    # writes a tombstone
```

`context` is an opaque version vector. Clients that ignore it get last-writer-wins behaviour; clients that merge (like a shopping cart that unions items) get no lost updates.

## Partitioning with consistent hashing

```arch
%% caption: Any node coordinates a request and fans it out to the key's N = 3 preference-list replicas in different zones; a stand-in holds hinted writes for a replica that is down.
node client "Clients" at 1,0 icon=users sub="partition-aware library"
node lb "Load balancer" at 2,1 icon=lb sub="to any node"
group ring "Consistent-hash ring: 128 vnodes per node, gossip membership" color=blue icon=network
node coord "Coordinator" at 1,2 in ring icon=server sub="any node"
node r1 "Replica 1" at 0,3 in ring icon=db sub="zone A, LSM tree"
node r2 "Replica 2" at 1,3 in ring icon=db sub="zone B, LSM tree"
node r3 "Replica 3" at 2,3 in ring icon=db sub="zone C, LSM tree"
node hint "Stand-in node" at 3,3 in ring icon=server sub="hints for replica 3"
client -> coord : "one fewer hop"
client:R -> lb:T
lb:B -> coord:R
coord -> r1
coord -> r2 : "W acks / R replies"
coord -> r3
coord ..> hint : "sloppy quorum"
hint ..> r3 : "handoff"
r1 <..> r2 : "Merkle repair"
```

Keys are hashed (e.g. MurmurHash3 128-bit) onto a ring. Each physical node owns many **virtual nodes** (tokens) — say 128 — spread around the ring. A key is stored on the first `N` *distinct physical* nodes found walking clockwise from its hash (its **preference list**), skipping virtual nodes of nodes already chosen and, ideally, choosing replicas in different racks/zones.

- **Adding a node** takes over the arcs adjacent to its new virtual nodes — about `1/N_nodes` of the data, pulled evenly from existing nodes, streamed in the background while the old owners keep serving.
- **Heterogeneous hardware** gets more virtual nodes on bigger machines.
- Many virtual nodes also smooth out load; with only one token per node, arc sizes vary by several times.

Any node can act as the **coordinator** for a request: clients either use a partition-aware client library (one fewer hop) or go through a load balancer to any node, which forwards to the preference list.

## Replication and quorums

With `N = 3`:

| Profile | W | R | Behaviour |
|---|---|---|---|
| Default | 2 | 2 | Survives one replica down for reads and writes; `R + W > N`. |
| Write-heavy logging | 1 | 1 | Fastest, most available; reads can be stale until repair. |
| Read-your-writes critical | 3 | 1 | Writes need all replicas (less available); reads are cheap and fresh. |

The coordinator sends the write to all `N` replicas in parallel and returns when `W` acknowledge; it sends reads to all `N` (or `R` plus a speculative extra) and returns when `R` respond, then resolves versions.

**Durability arithmetic.** The question requires no acknowledged write to be lost when any two servers fail. An ack from `W = 2` means only two durable copies, so if exactly those two die before the third replica applies the write, it is gone. Writes under that contract therefore need three durable copies at ack time: `N = 3, W = 3` with sloppy-quorum stand-ins counting as copies (so a write stays available with one replica down), or `N = 5, W = 3, R = 3`. The second costs 100 TB × 5 = 500 TB raw = 250 nodes instead of 150, so I would use it only for keys that need it. For everything else `W = 2` loses a write only if both acking nodes die within the milliseconds before the third copy lands; alert on replica-lag to bound that window.

**Sloppy quorum and hinted handoff.** If a preference-list node is unreachable, the coordinator writes to the next healthy node on the ring with a **hint** ("this belongs to node C"). The stand-in forwards the data when C recovers. This keeps writes available during failures and partitions, but it weakens the `R + W > N` guarantee: the `W` nodes that acknowledged may not overlap the `R` nodes a later read contacts. Say this explicitly.

## Conflict resolution

Concurrent writes to the same key through different coordinators (or during a partition) produce divergent versions.

- Each version carries a **version vector**: a map `{coordinator_node: counter}`. Version A **descends** from B if every counter in A ≥ B's. If neither descends from the other, they are **concurrent** — a real conflict.
- On read, the coordinator discards versions that are ancestors of others and returns the remaining siblings.
- Resolution strategies:
  - **Last-writer-wins** by timestamp: simple, but silently loses one write under clock skew. Acceptable for caches and idempotent overwrites.
  - **Application merge**: the client merges siblings (union for carts, max for counters) and writes back with the merged context.
  - **CRDT values** (counters, sets, maps) that merge automatically — see [22_realtime_and_collaboration.md](../building_blocks/22_realtime_and_collaboration.md).
- Version vectors are pruned (oldest entries dropped past a size cap) to stop them growing forever, at a small risk of false conflicts.

## Membership and repair

**Membership and failure detection.** Nodes gossip membership and token ownership every second to a few random peers, so the ring state converges in `O(log n)` rounds. Each node runs a phi-accrual failure detector for peers it talks to. Crucially, a node being *suspected* only changes routing (use hinted handoff); **permanently** removing a node and rebalancing its data is an explicit operator or automation decision, so a flapping node does not trigger huge data movement.

**Anti-entropy.** Three mechanisms keep replicas converged:

1. **Read repair** — when a read sees stale replicas, write the newest version back to them (synchronously for the `R` set, asynchronously for the rest).
2. **Hinted handoff** — replay hints when the target node returns.
3. **Merkle-tree repair** — each node maintains a Merkle tree per token range; replicas periodically compare trees and stream only the differing ranges. This catches writes that were never read and hints that were lost.

**Deletes** write a **tombstone** (a version marked deleted) that is kept longer than the maximum repair interval (e.g. 10 days); otherwise a replica that missed the delete could resurrect the value during repair.

## Storage engine

Each node stores data in an **LSM tree**: commit log for durability, in-memory memtable, flushed to immutable SSTables with Bloom filters, background compaction (size-tiered for write-heavy, leveled for read-heavy workloads). Writes are sequential appends, which fits the write rate and the "last write/tombstone wins within a node" model. See [20_specialized_data_structures.md](../building_blocks/20_specialized_data_structures.md).

## Failure behaviour

| Failure | Behaviour |
|---|---|
| One node down | Quorums of 2 of 3 still succeed; hinted handoff covers writes; reads may trigger repair. |
| Two replicas of a key down | `W = 2`/`R = 2` operations fail for those keys unless sloppy quorum stand-ins are used; data remains durable on the third replica and on hints. |
| Network partition | Both sides accept writes (with sloppy quorums); conflicts are detected by version vectors after healing and resolved on read. |
| Disk corruption | Checksums per SSTable block detect it; the node rebuilds the affected ranges from replicas via Merkle repair. |
| Hot key | One preference list overloaded; mitigate with client-side caching, request coalescing, or application-level key splitting ([25_partitioning_and_hot_keys.md](../building_blocks/25_partitioning_and_hot_keys.md)). |

## Observability and interview close

Measure per node: p50/p99 latency by operation and consistency level, quorum failures, hint queue size, read-repair rate, Merkle repair bytes streamed, pending compactions and SSTables per read, tombstones scanned per read, disk usage, and gossip convergence time.

Trade-off to state: "I chose leaderless replication with sloppy quorums so the store stays writable during partitions, which means clients must handle concurrent versions. If the product needed linearizable operations — for example conditional writes for inventory — I would switch to one Raft group per partition, accept that a minority partition cannot write, and get compare-and-set semantics in return."

## Follow-ups the interviewer will ask

1. **"How do you do multi-region?"** One ring per region with a local quorum (`W`/`R` counted only among in-region replicas) and asynchronous cross-region replication, because a quorum spanning regions would add a 60 to 100 ms round trip to every write and break the 10 ms p99. Cross-region concurrent writes surface as siblings (or LWW, if the data allows). The cost is an RPO equal to replication lag, so alert on it and state the number.
2. **"What changes at 10× and 100×?"** At 10× traffic the throughput-bound fleet is 7.5 M replica ops/s ÷ 10 K = 750 nodes; gossip and the routing map still work at that size. At 100× data (10 PB, 30 PB raw) the storage-bound fleet is about 15,000 nodes, so I stop growing one ring: split into cells of a few hundred nodes behind a routing layer, and move cold data to erasure coding (about 1.4× overhead for a 10+4 code instead of 3×).
3. **"How do you do a linearizable compare-and-set on top of this?"** You cannot get it from `R + W > N` alone: sloppy quorums and read-repair races let two clients observe different orders. Run a consensus round per key for the subset of operations that need it, the way Cassandra's lightweight transactions run Paxos per partition (roughly four round trips, about 2 ms in-region at 0.5 ms each, and far worse cross-region), and keep plain quorum for the rest. Contended keys will retry, so rate-limit them.
4. **"What does a rolling upgrade look like?"** Replicas are placed in different zones, so I upgrade one zone at a time in small batches (drain, stop, upgrade, rejoin, replay hints) and gate each batch on hint-queue size and p99 before the next; at most one replica of any key is down, so `W = 2` never blocks. Gossip advertises a protocol version and the cluster speaks the lowest one until every node is upgraded; on-disk format changes go in a separate later step so a rollback stays possible. Assuming 3 zones of 50 nodes, batches of 10 and 15 minutes each, that is 15 waves, about 4 hours.
5. **"What dominates cost, and what are the levers?"** Raw SSD capacity: 300 TB at 3× replication is 150 nodes, and moving durable keys to `N = 5` adds 100. Levers are erasure-coding or tiering cold data, the `W = 1` profile for logs, and TTLs. Compaction I/O is the hidden cost, so pick size-tiered for write-heavy tables and leveled for read-heavy ones.
6. **"How do you handle abuse and noisy neighbours?"** Per-tenant quotas on ops and bytes enforced at the coordinator, a hard 1 MB value cap, and hot-key detection with request coalescing. Watch for tombstone bombs: a client deleting millions of keys makes later reads scan the tombstones, so alert on tombstones per read and rate-limit range deletes.
7. **"A node is slow but not dead. What happens?"** Heartbeat-based failure detectors do not flag it, so requests routed to it inflate p99. The coordinator sends a speculative read to the next replica after a p95-based delay and takes the first response (hedged requests, as in *The Tail at Scale*, 2013), and a latency-aware replica choice deprioritises it. Alert on per-node p99 rather than on liveness.
8. **"Why not a Raft-per-partition store? Clients would not need to handle siblings."** For most workloads I would agree, and Spanner-style stores are simpler for clients. Leaderless wins here only because the question requires writes to keep succeeding in a minority partition and with two servers down; a Raft group cannot do that. If the interviewer says in-region partitions are rare enough to give that up, I switch and get compare-and-set and no version vectors.

## Common mistakes

1. **Claiming `R + W > N` means linearizable.** It does not survive sloppy quorums, concurrent writers or read-repair races. Say "read-your-writes in the common case" and name what you would use for linearizable operations.
2. **Meeting "survive any two failures" with `W = 2`.** An ack then means two copies. Do the copy-count arithmetic (three durable copies at ack) and price it.
3. **Last-writer-wins on wall clocks for everything.** A writer whose clock runs 5 s ahead silently overrides later writes. Use version vectors or app merges where updates must not be lost, and LWW only for idempotent overwrites.
4. **One token per node.** Arc sizes vary several-fold and a joining node takes half of one neighbour's data. Use many virtual nodes (about 128).
5. **Removing a node from the ring on suspicion.** A flapping or briefly partitioned node then triggers terabytes of rebalancing. Suspicion changes routing (hints); removal is an explicit decision.
6. **Garbage-collecting tombstones before repair has run.** A replica that missed the delete resurrects the value. Keep tombstones longer than the maximum repair interval (10 days, as in Cassandra's default `gc_grace_seconds`).
7. **Sizing the fleet from storage alone.** 15 nodes at 10 TB cannot serve 750K replica ops/s. Take the maximum of the capacity-bound and throughput-bound counts.
8. **Ignoring sibling growth.** A client that reads, does not pass the context back, and writes again multiplies siblings and version-vector entries. Cap both, alert on them, and make the SDK pass the context automatically.

## Going from L5 to L6

- **Migration and rollout.** Onboard a tenant with dual writes and shadow reads against the old store, compare, then cut reads over per keyspace. Because of consistent hashing, capacity can grow node by node, and every protocol and format change is a two-step rolling upgrade.
- **Cost model.** Cost per million operations and per TB-month, with the three levers priced: replication factor (3 versus 5 for the durable subset), tiering, and write amplification. Show that `N = 5` for everything is 100 extra nodes, and that measured per-node throughput, not the 10,000 ops/s assumption, sets the fleet.
- **Ownership and blast radius.** Run separate cells with a routing layer so a bad deploy or one runaway tenant stays inside one cell; keep the membership control plane separate from the data path; place replicas across zones so a zone loss removes at most one copy of any key.
- **Build versus buy.** Buy (a managed store or Cassandra or ScyllaDB) unless a requirement forces otherwise. Note that today's DynamoDB is not the leaderless design of the 2007 Dynamo paper: its 2022 USENIX ATC paper describes leader-based Multi-Paxos replication per partition, which shows the industry moved toward stronger consistency where it could.
- **Phased evolution and what to measure first.** Start with one region, `N = 3, W = 2, R = 2`; add consensus-backed CAS for the few keys that need it; add regions last. Measure first: key-size and access skew (hot keys), tombstone ratio, hint-queue depth, and whether a full repair finishes inside the tombstone window.

## Build exercise

Build a 3-node in-process simulation: consistent hashing with virtual nodes, `N/R/W` quorums, version vectors, and hinted handoff. Inject a partition, write to both sides, heal, and show the siblings returned on read and resolved by a merge function. Then add a node and measure the fraction of keys that move.

Named assertions:

- `test_quorum_read_sees_latest_write`: with `R + W > N` and no failures, every read returns the latest acked write.
- `test_partition_yields_siblings_then_merge`: write to both sides of a partition, heal, and assert `get` returns two siblings that a union merge resolves into one.
- `test_hinted_handoff_delivers_after_recovery`: kill a replica, write, restart it, and assert it holds the value after hints replay.
- `test_no_resurrection_after_delete`: delete a key while a replica is down, run repair, and assert the key stays deleted.
- `test_node_join_moves_about_one_over_n`: adding the 4th node moves about 25% of keys, within a tolerance you name.
- `test_two_failures_lose_no_acked_w3_write`: with `W = 3`, kill any two nodes right after an ack and assert the value survives.
