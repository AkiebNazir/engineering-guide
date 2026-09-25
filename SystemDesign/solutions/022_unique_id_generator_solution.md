# 022 — Unique ID Generator: Full System Design Solution

## Goal and contract

The contract is: **unique, 64-bit, k-sortable** (ordered by time to within a few milliseconds, not strictly monotonic across machines), available during partitions, and cheap enough to call on every write. Strict global ordering is explicitly *not* promised — it would require a single sequencer or consensus on every ID, which contradicts availability during a datacenter partition.

Why the 64-bit and sortable requirements matter: database primary keys that increase with time keep B-tree inserts at the right-hand edge of the index (few page splits, good cache locality), and time-ordered IDs make "newest first" pagination a simple range scan.

## Options compared

| Approach | Unique? | 64-bit? | Time-sortable? | Coordination per ID | Main weakness |
|---|---|---|---|---|---|
| UUIDv4 (random) | Practically | No (128 bits) | No | None | Random keys scatter B-tree inserts; too wide for the requirement. |
| UUIDv7 (time-ordered) | Practically | No (128 bits) | Yes | None | Still 128 bits. Excellent default when 64 bits is not required. |
| Database auto-increment | Yes | Yes | Yes | Every ID hits the database | Single point of failure and throughput bottleneck; leaks volume. |
| Multi-master auto-increment (step = N, offset = k) | Yes | Yes | Roughly | Every ID hits a database | Adding a master changes the step; ordering across masters is poor. |
| Ticket server / range allocation (e.g. hand out blocks of 10,000) | Yes | Yes | Roughly | Once per block | Block allocator must be highly available; IDs from different blocks interleave out of time order. |
| **Snowflake-style time + worker + sequence** | Yes | Yes | Yes (k-sorted) | None per ID; worker ID assigned once | Depends on clocks; worker IDs must be unique. |

**Decision:** Snowflake-style IDs generated **in-process** by a library in each application server, with worker IDs leased from a coordination service. This removes the network hop from the hot path (well under 1 µs per ID) and keeps working during partitions, at the cost of relying on reasonably synchronised clocks and a correct worker-ID assignment.

## Snowflake bit layout

Twitter's original 2010 Snowflake announcement used 41 bits of timestamp, 10 bits of machine identity and 12 bits of sequence. That split gives only 1,024 generators, and the question gives us 10,000 application servers. If every server embeds the library and holds its own worker ID, 10,000 servers need ceil(log2 10,000) = 14 bits of identity, so the classic split does not fit and we re-split the 22 low bits:

```text
 0 | 41 bits timestamp (ms since custom epoch) | 3 bits DC | 12 bits worker | 7 bits sequence
 ^ sign bit kept 0 so the ID is a positive signed 64-bit integer
```

Bit-budget arithmetic (checked with python):

- **41 bits of milliseconds** = 2⁴¹ ms ≈ 69.7 years from the custom epoch (choose an epoch near launch, e.g. 2020-01-01, not 1970). So we need no more timestamp bits until about 2089.
- **3 bits of datacenter** = 8 datacenters; we have 5, so there is room for 3 more regions without a re-split.
- **12 bits of worker** = 4,096 workers per datacenter. We need 10,000 / 5 = 2,000 servers per datacenter, so this is 2.0× headroom for autoscaling and lease churn (a recycled worker ID sits idle for one lease TTL).
- **7 bits of sequence** = 128 IDs per worker per millisecond = 128,000 per second per worker. Average demand is 1 M/s ÷ 10,000 servers = 100 IDs/s per server, and the stated burst of 10,000/s is 10 IDs/ms, so the sequence has 12.8× headroom over the worst burst. So 7 bits is enough, and every bit not spent on sequence goes to worker identity.
- System capacity: 8 × 4,096 = 32,768 generators × 128,000/s ≈ 4.2 billion IDs/s, about 4,200× the 1 M/s peak. It equals the classic layout's capacity because both spend 22 bits on machine plus sequence.

The alternative that keeps the classic 10/12 layout is the **ID service** below: a pool of about 100 generator processes (5 DCs × 20) serves all 10,000 servers, because one generator can issue 4 M/s and 1 M/s is the whole system's peak. Batches of 1,000 IDs mean about 1,000 RPCs/s system-wide. The trade is one extra network hop (amortised across a batch) and a service to operate, versus a library with no hop but a worker-ID lease per process.

Generation algorithm (per generator, single-threaded or with a lock/atomic CAS):

```text
now = currentMillis() - EPOCH
if now < lastTs:                 # clock went backwards
    wait until now >= lastTs     # or fail fast if the gap is large (see below)
if now == lastTs:
    seq = (seq + 1) & 127
    if seq == 0:                 # 128 IDs used in this ms
        now = waitForNextMillis(lastTs)
else:
    seq = 0
lastTs = now
return (now << 22) | (dc << 19) | (worker << 7) | seq
```

To avoid leaking volume (sequence numbers resetting to 0 every millisecond reveal activity), start `seq` at a random value each millisecond, or expose IDs externally only through an obfuscation (e.g. a keyed permutation or base62 of an encrypted form).

## Clock skew and worker IDs

**Clocks moving backwards.** NTP can step a clock backwards, and a VM can resume with a stale clock. If the generator issued IDs for millisecond *T* and the clock now reads *T − 5*, generating more IDs could duplicate earlier ones (same timestamp, same worker, sequence restarting).

- Small regressions (a few ms): block until the clock passes `lastTs`.
- Large regressions (e.g. > 1 s): refuse to generate, raise an alert, and mark the instance unhealthy so the load balancer drains it.
- Persist `lastTs` periodically so a restart after a large clock rollback does not reuse old timestamps.
- Configure NTP to **slew** (gradually adjust) rather than step, and monitor offset.

**Clock drift between machines** only affects sortability, not uniqueness: IDs from two machines whose clocks differ by 20 ms may be out of order by up to 20 ms. That is the "k-sortable" contract.

**Worker-ID assignment.** Two generators with the same (DC, worker) bits and overlapping timestamps will produce duplicates, so assignment must be correct:

- On startup, the process acquires a **lease** on a free worker ID from a coordination service (etcd/ZooKeeper/Chubby), with a TTL of e.g. 30 s renewed every 10 s.
- If the lease cannot be renewed (partition from the coordinator), the process **stops generating** before the TTL expires, so a new owner can never overlap with it.
- On restart, wait at least the lease TTL (or until the clock passes the previous owner's last possible timestamp) before using a recycled worker ID.
- For stable fleets (Kubernetes StatefulSets), the ordinal index can serve as the worker ID, but the lease is still the safer choice.

The coordination service is on the startup path only, never on the per-ID path — so its latency and brief outages do not affect ID generation.

## Architecture

```arch
%% caption: Coordination happens once per process (worker-ID lease); every ID is generated locally with no network hop.
group dc1 "Datacenter 1" icon=region color=blue
node coord1 "etcd / ZooKeeper" at 0.5,0 in dc1 icon=etcd
node app1 "App server" at 0,1 in dc1 icon=server sub="+ ID library"
node app2 "App server" at 1,1 in dc1 icon=server sub="+ ID library"
group dc2 "Datacenter 2" icon=region color=blue
node coord2 "etcd / ZooKeeper" at 2.5,0 in dc2 icon=etcd
node app3 "App server" at 2.5,1 in dc2 icon=server sub="+ ID library"
node db "Databases" at 1.75,2 icon=db sub="BIGINT primary keys"
app1:T -> coord1:L : "lease worker 17"
app2:T -> coord1:R : "lease worker 18"
app3 -> coord2 : "lease worker 3"
app1 -> db
app3 -> db
```

**Library vs service.** An embedded library gives the lowest latency and no new failure point, but every language needs an implementation and every process needs a worker ID. A small **ID service** (a pool of generators behind gRPC, clients fetching batches of, say, 1,000 IDs at a time) centralises correctness and worker management; batching keeps the network cost per ID tiny. Large companies use both: a library in core services, a service for everything else.

## Failure modes

| Failure | Behaviour |
|---|---|
| Coordination service down | Running processes keep their leases until TTL; they keep generating if they can renew, otherwise stop cleanly. New processes cannot start generating — alert, but existing capacity continues. |
| Datacenter partition | Each DC keeps generating independently; uniqueness is guaranteed by DC bits; ordering across DCs is only as good as clock sync. |
| Clock rollback | Bounded wait or refusal plus alert, as above. No duplicates. |
| Sequence exhaustion in a millisecond | Generator waits ≤ 1 ms; a worker needs more than 128 IDs in one millisecond (128,000/s sustained), which is 12.8× the stated 10,000/s burst, so it is rare. |
| Duplicate worker ID (misconfiguration) | Prevented by leases; detected by a background job sampling recent IDs for collisions, and by unique constraints in the database as a last line of defence. |

## Observability and interview close

Metrics: IDs generated per second per worker, clock offset from NTP per host, clock-regression events, sequence-exhaustion waits, worker-ID lease renewals and failures, and unique-constraint violations in consumers (should be zero).

Trade-off to state: "I give up strict global monotonicity to avoid coordination on every ID. If the product truly required a single total order — say an audit log where ID order must equal commit order globally — I would move to a consensus-backed sequencer (or Spanner-style commit timestamps) and accept both the latency and the loss of availability during partitions."

At 100× traffic (100 M IDs/s) the layout still has about 42× aggregate headroom; the first limit to hit is the 12-bit worker space if the fleet grows beyond about 4,000 servers per datacenter, and after that the epoch's remaining lifetime.

## Follow-ups the interviewer will ask

1. **"How does this work across regions, and what happens in a partition?"** The datacenter bits make cross-region uniqueness a static property: each DC leases worker IDs from its own coordination cluster, so a partition between DCs stops nothing. What degrades is ordering: IDs from two DCs are ordered only to within their clock offset, so I would assume a 50 ms bound (an assumption to measure), alert when any host exceeds it, and tell consumers not to infer causality from ID order across DCs.
2. **"What changes at 10× and 100×?"** At 10× or 100× IDs per second nothing changes: the layout has about 420× and 42× aggregate headroom. The limit that binds first is fleet size. At 100,000 servers (20,000 per DC) I would need 15 worker bits, and 1 + 41 + 3 + 15 + 4 = 64 leaves 4 sequence bits, or 16 IDs/ms per worker, only 1.6× over the 10 IDs/ms burst. At that point I would stop embedding and move to the ID service pool, which decouples worker count from fleet size.
3. **"Your clock goes backwards during a leap-second event. What happens?"** A step correction can rewind the clock by up to 1 s, so the rollback guard fires. Blocking that long breaks the 1 ms p99, so for regressions up to about 1 s I keep issuing from `lastTs` and let sequence overflow advance it one millisecond per 128 IDs (borrowing from the future). The wall clock catches up because even a 10,000/s burst advances logical time only 78 ms per second. Past a borrow cap, refuse and drain the host. Better still, prevent it: use a smeared time source (a 24-hour smear is about 11.6 ppm) and never let NTP step production hosts.
4. **"How do you migrate from 32-bit IDs?"** Use expand and contract: add a `BIGINT` column, dual-write, backfill in batches, switch reads, then drop the old column. Old rows keep their small IDs (below 2³¹, about 2.1 billion) and new Snowflake IDs are far above that, so the two ranges cannot collide. The dangerous part is every client, log parser and cache key that stores IDs as an `int32` or a JavaScript number (safe only to 2⁵³). Inventory those first and ship IDs as strings in JSON.
5. **"What if IDs must be strictly increasing across the whole system?"** That needs every ID to pass through a single serialisation point, meaning a consensus-replicated sequencer (or Spanner-style commit timestamps with commit-wait, as in the 2012 Spanner paper). At 1 M/s you would need group commit, and every caller pays a cross-datacenter round trip, breaking the 1 ms p99 and the partition-availability requirement. If the real need is "order per entity" (a conversation, an account), use a per-key version or a hybrid logical clock and keep the global IDs k-sortable.
6. **"What does it cost?"** Generation is nearly free: assuming about 50 ns per ID, 1 M/s is 0.05 of one core system-wide. Leases are 10,000 servers ÷ 10 s = 1,000 renewals/s, or 200/s per datacenter, trivial for a 3- or 5-node etcd cluster. The real costs are on-call for clocks and leases, and storage: a 128-bit key adds 8 bytes per row per index, about 690 GB/day at 1 M inserts/s (assuming every ID becomes a row).
7. **"How do you handle abuse and enumeration?"** Time-ordered IDs are guessable, so authorisation must never depend on an ID being secret; check ownership on every read. To hide volume, randomise the starting sequence per millisecond, or expose only a keyed 64-bit permutation of the ID at the edge (which gives up public sortability). On the ID-service path, apply per-client quotas.
8. **"Why not UUIDv7, or a database sequence?"** If 64 bits is not a hard requirement, UUIDv7 (RFC 9562, 2024) is the better answer: no worker leases, no bit-budget review, nothing to operate. I keep Snowflake here because the question demands `BIGINT` keys, and the 8 extra bytes per key per index add up at this write volume. If the interviewer prefers database sequences, I would cite the per-shard approach in Instagram's 2012 sharding write-up (timestamp, logical shard ID, per-shard sequence): the shard ID plays the worker ID's role, so no lease service is needed, but ID generation now lives in the database tier and scales with it.

## Common mistakes

1. **Sizing worker bits from the classic 10-bit diagram.** 1,024 identities cannot cover 10,000 embedded servers. Count the fleet first (10,000 needs 14 bits), then either re-split the bits or move to a pooled ID service.
2. **Sending 64-bit IDs as JSON numbers.** A 2026 ID with a 2020 epoch is about 8.9 × 10¹⁷, roughly 99× larger than 2⁵³, so JavaScript clients silently round it and two different IDs compare equal. Serialise as strings in every external <abbr title="Application Programming Interface">API</abbr>.
3. **Trusting the wall clock without a monotonic guard.** An NTP step or VM resume reuses (timestamp, worker, sequence) triples and creates duplicates, which show up weeks later as primary-key violations or, worse, silent overwrites. Track `lastTs`, and decide up front between wait, borrow and refuse.
4. **Assigning worker IDs from hostnames or config files.** Cloned images and autoscaling produce two live processes with the same ID. Use a lease from a coordination service, and check the lease's remaining validity against a monotonic clock before every batch, because a garbage-collection pause longer than the TTL lets a stale process keep generating after the ID has been re-leased.
5. **Choosing a 1970 epoch.** 41 bits from 1970 run out in about 2039; from 2020 they last to about 2089. The epoch is a one-way door, so pick it at launch and write it down.
6. **Resetting the sequence to 0 every millisecond, then sharding on `id % N`.** A lightly loaded generator issues mostly `seq = 0`, so the low bits are nearly constant and one shard gets the traffic. Randomise the sequence start, or shard on a hash of the ID.
7. **Promising "strictly increasing".** The contract is k-sortable; downstream code that orders events or resolves conflicts by ID across machines will silently lose updates whenever clocks disagree. Use per-entity versions for correctness and IDs only for coarse ordering.
8. **Putting the coordination service on the per-ID path.** It turns a sub-microsecond local operation into a network call with the coordinator's availability. Coordinate once per process, generate locally.

## Going from L5 to L6

- **Migration and rollout.** The bit layout is a one-way door because IDs are permanent, so validate it with a shadow generator (compute IDs, use none, check uniqueness and ordering) before the first production ID. Roll out one DC at a time, and reserve one of the three unused DC codes as an escape hatch so a future layout can be told apart from this one without touching existing rows.
- **Cost model.** Per-ID compute is negligible; the numbers that matter are 8 bytes per key per index against a 128-bit alternative (about 690 GB/day per index at 1 M rows/s) and the operational cost of clock discipline. Say that Snowflake's win over UUIDv7 is storage, not speed.
- **Ownership and blast radius.** An embedded library ships a bug to all 10,000 servers at once, so it needs staged rollout and version-skew tolerance; a pooled service is a tier-0 dependency whose outage stops every write path. Keep the coordinator on the startup path only, and give each DC its own coordination cluster so a bad deploy or outage stays inside one DC.
- **Build versus buy.** The generator is about 50 lines: build it or take a maintained library. Buy the coordination service (managed etcd or ZooKeeper) and never write consensus yourself. If 64 bits is negotiable, buy UUIDv7 and delete the whole problem.
- **Phased evolution and what to measure first.** Start with per-shard database sequences or UUIDv7, and move to Snowflake only when key size or a sharding requirement forces it. Measure the p99 clock offset per DC first, since it sets the "k" in k-sortable, and then peak IDs per second per host to validate the 7-bit sequence.

## Build exercise

Implement the generator in your language with a lock-free CAS loop. Test: 8 threads × 1 million IDs with zero duplicates; simulated clock rollback of 5 ms (waits) and 5 s (refuses); two generators accidentally given the same worker ID (show the collision, then prevent it with a lease).

Named assertions:

- `test_no_duplicates_under_contention`: 8 threads × 1 M IDs, `len(set(ids)) == 8_000_000`.
- `test_layout_roundtrip`: `decode(encode(ts, dc, worker, seq))` returns the same four fields, and every ID at the field maxima is positive as a signed 64-bit integer.
- `test_clock_rollback_5ms_waits`: inject a clock that steps back 5 ms; assert no duplicate and that the call returns within the guard bound.
- `test_clock_rollback_5s_refuses`: assert the generator raises and the health check flips to unhealthy.
- `test_duplicate_worker_id_blocked_by_lease`: start two generators requesting the same worker ID; assert the second is refused or waits out the TTL.
- `test_json_ids_are_strings`: assert the <abbr title="Application Programming Interface">API</abbr> serialises an ID above 2⁵³ as a string and that a round trip through a float-based parser is never used.
