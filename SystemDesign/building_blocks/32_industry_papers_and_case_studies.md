# Industry Papers and Case Studies: Meta, Amazon, LinkedIn, Netflix, Uber and Others

Interviews at Meta, Netflix, Amazon and similar companies lean on a shared set of published designs. This block digests the well-documented ones in the shape of [24_google_papers.md](24_google_papers.md): the problem, the decisions that matter, the cost, and how to use it. Every claim comes from the named paper, official documentation or engineering blog; where a source says less than the folklore, this page says less too.

> 💡 Cite the trade-off, not the trademark. "Facebook deleted cached values instead of updating them because deletes are idempotent" is a design argument you can defend. "Facebook uses memcache" is trivia.

## Scaling Memcache at Facebook (NSDI 2013)

*Rajesh Nishtala et al., NSDI 2013.*

**Problem.** A read-heavy site fetches many items per page, so the database cannot take the read rate. The cache in front must absorb it, stay non-authoritative, and survive races, herds and server failures.

**Key decisions.**

- **Delete on write.** The web server writes the database, then *deletes* the key. The paper's reason: deletes are idempotent, so they can be retried and replayed.
- **Leases.** On a miss the cache hands out a 64-bit token bound to the key, and a later set must present it. A delete invalidates outstanding tokens, so a stale set is rejected. Tokens are issued at most once per key per 10 seconds by default, so a herd of missing clients mostly waits.
- **Gutter pool.** About 1% of a cluster's machines stand in for failed cache servers, with quickly expiring entries; the paper reports it reduces client-visible failures by 99%.
- **Replayable invalidation.** A daemon (`mcsqueal`) reads the MySQL commit log and issues the deletes, so lost ones can be replayed. Across regions, a **remote marker** sends reads of a just-written key to the master region until replication catches up.

**Trade-offs.** Stale reads remain possible in the windows these mechanisms cannot close (the marker trades extra miss latency for less staleness), and a cold or failed cache shifts its load to the database.

**Where it shows up in an interview.** Any cache-aside design: "invalidate on write, protect the miss path with a lease, keep a small fallback pool so one dead cache node does not stampede the database." Depth: [30_social_graph_and_caching_at_scale.md](30_social_graph_and_caching_at_scale.md), [07_caching.md](07_caching.md).

## TAO (USENIX ATC 2013)

*Nathan Bronson et al., "TAO: Facebook's Distributed Data Store for the Social Graph", USENIX ATC 2013.*

**Problem.** Look-aside memcache served the graph badly, the paper says: a key-value cache fits edge lists poorly (one changed edge reloads the list), control logic lives in uncoordinated clients, and read-after-write across regions is expensive.

**Key decisions.**

- **A two-type API**: objects `(id) → (otype, data)` and time-ordered associations `(id1, atype, id2) → (time, data)`. "Newest 50 comments" is a range read of one association list.
- **A write-through cache that knows the API.** Followers serve reads; a leader per shard handles writes and misses against sharded MySQL and asynchronously sends invalidations to other followers. The writing follower is updated synchronously, so clients sharing it see their own writes.
- **Shard by source**: an association is stored on the shard of `id1`, so one query touches one server. The paper reports a 96.4% read hit rate.

**Trade-offs.** Eventual consistency, no compare-and-set, no multi-object transactions in this paper, and a bidirectional edge is two associations, so two writes.

**Where it shows up in an interview.** Friends, followers, likes: model objects and typed edges, shard edges by source id, cache at the API level, and name the consistency you give.

## Haystack (OSDI 2010) and f4 (OSDI 2014)

*Doug Beaver et al., "Finding a Needle in Haystack", OSDI 2010. Subramanian Muralidhar et al., "f4: Facebook's Warm BLOB Storage System", OSDI 2014.*

**Problem.** Photos are small, immutable and numerous, and a file per photo on a POSIX filesystem costs extra disk reads for metadata that does not fit in memory. As content ages its request rate drops, so triple replication wastes capacity.

**Key decisions.**

- **Haystack** appends photos into volume files of about 100 GB with an in-memory index of id to offset and size, so a read costs at most one disk operation (the paper reports about 10 bytes of memory per photo). Writes go to every physical volume of a logical volume, and deletes are flags reclaimed by compaction.
- **f4** moves aged BLOBs to a warm store using erasure coding: Reed-Solomon(10,4) in a datacenter (`14/10 = 1.4×`) plus XOR across datacenters. Effective replication falls from Haystack's 3.6 (`3 × 1.2` for RAID-6) to 2.8 (`1.4 × 2`) or 2.1 (`(1.4 × 2 + 1.4) / 2`). The paper cites a three-month threshold for photos.

**Trade-offs.** Index memory bounds a Haystack machine; f4 gives up throughput per byte and pays reconstruction reads, so it fits only immutable, low-request-rate data.

**Where it shows up in an interview.** Photo, video and file storage: metadata separate from data, hot head on a cache or CDN, erasure-code what has gone cold. See [08_object_storage.md](08_object_storage.md).

## Gorilla (VLDB 2015)

*Tuomas Pelkonen et al., "Gorilla: A Fast, Scalable, In-Memory Time Series Database", VLDB 2015.*

**Problem.** In spring 2015 Facebook's monitoring produced over 2 billion series and about 12 million points per second, over 1 trillion a day. At 16 bytes each that is `10^12 × 16 B = 16 TB` of RAM per day. At least 85% of queries were for the last 26 hours.

**Key decisions.**

- Keep the latest **26 hours** in memory as a write-through cache in front of the long-term store.
- **Compress by exploiting regularity**: delta-of-delta timestamps (about 96% compress to one bit) and XOR of consecutive values, averaging 1.37 bytes per point, a 12× cut (`16 / 1.37 ≈ 11.7`).
- Run instances in several regions, stream writes to each without guaranteeing consistency, and read from the closest.

**Trade-offs.** Only the recent window is in RAM. Replicas can differ, which is fine for monitoring and wrong for money.

**Where it shows up in an interview.** Metrics platforms ([013](../solutions/013_metrics_platform_solution.md)): recent data in RAM, compressed, regional replicas, availability over consistency. Compare Google's [Monarch](24_google_papers.md#monarch-2020).

## Amazon Aurora (SIGMOD 2017)

*Alexandre Verbitski et al., "Amazon Aurora: Design Considerations for High Throughput Cloud-Native Relational Databases", SIGMOD 2017.*

**Problem.** In the cloud the bottleneck moves from disk to network: mirrored MySQL on network storage sends log, binlog and pages in synchronous chained steps, so one slow replica stalls commits.

**Key decisions.**

- **The log is the database.** The instance sends only redo records to storage, which builds pages itself in the background. The paper reports an order-of-magnitude cut in network IOPS and faster crash recovery.
- **Six copies over three AZs**, write quorum 4/6, read quorum 3/6 (`3 + 4 > 6`). It survives losing an AZ plus one node for reads, and an AZ for writes.
- **10 GB segments** repair in about 10 seconds on a 10 Gbps link, shrinking the window for a second failure. Normal reads use one up-to-date segment, not a quorum; one writer and up to 15 read replicas share the volume.

**Trade-offs.** One writer per cluster and a purpose-built storage tier.

**Where it shows up in an interview.** "Highly available SQL": separate compute from storage, replicate the log not pages, and derive quorum sizes from failure domains ("survive an AZ plus one node" gives `V=6, Vw=4, Vr=3`). See [26_distributed_log_internals.md](26_distributed_log_internals.md), [06_database_internals.md](06_database_internals.md).

## DynamoDB (USENIX ATC 2022) and S3's documented properties

*Mostafa Elhemali et al., "Amazon DynamoDB: A Scalable, Predictably Performant, and Fully Managed NoSQL Database Service", USENIX ATC 2022.*

**Problem.** The paper says Dynamo ([24](24_google_papers.md#dynamo-amazon-2007)) was single-tenant with each team running its own installation, and that this burden limited adoption. DynamoDB is the multi-tenant managed successor aiming at predictable single-digit-millisecond latency.

**Key decisions.**

- **Leader-based, not leaderless.** A partition's replicas sit in different AZs and use **Multi-Paxos** with a leased leader, which serves writes and strongly consistent reads. Log-only replicas (write-ahead log, no key-value data) add availability and durability.
- **Admission control in the data plane.** Static per-partition throughput broke on skew, so it added bursting, adaptive capacity, then **global admission control**: routers hold local token buckets that a central service replenishes every few seconds.

**Trade-offs.** Per-partition throughput is still a ceiling, and splitting a partition can leave its hot part with less, so key design matters ([25](25_partitioning_and_hot_keys.md)).

**S3, documented properties only.** AWS documents strong read-after-write consistency including listings (December 2020), a 99.999999999% durability design target across at least three AZs, and at least 3,500 write and 5,500 read requests per second per prefix.

**Where it shows up in an interview.** Key-value and object stores: choose leader-per-partition when you need strongly consistent reads, and design throttling in from the start.

## Kafka at LinkedIn (NetDB 2011)

*Jay Kreps, Neha Narkhede, Jun Rao, "Kafka: a Distributed Messaging System for Log Processing", NetDB 2011.*

**Problem.** Move high volumes of activity and operational events to online and offline consumers who read a retained backlog at their own pace.

**Key decisions.**

- A topic is split into **partitions**, each an append-only log of segment files, and a message is addressed by its **logical offset**, with no separate index.
- **Consumers pull and keep their position.** Retention is time-based (typically 7 days), so a consumer can rewind and replay.
- **Lean on the OS**: the page cache serves reads, plus batching and `sendfile`.

**Trade-offs.** Order only within a partition, and at-least-once delivery. The 2011 paper describes no replication: unconsumed data on a failed broker is unavailable, and lost if the disk dies.

**Where it shows up in an interview.** Any queue: the partition is the unit of ordering and parallelism, the offset is consumer state, retention gives replay. See [26_distributed_log_internals.md](26_distributed_log_internals.md), [09_messaging_and_streaming.md](09_messaging_and_streaming.md).

## Netflix: Open Connect, chaos engineering, bulkheads and Eureka

*Sources: Netflix Open Connect documentation; Ali Basiri et al., "Chaos Engineering", IEEE Software, 2016; Netflix's `Hystrix`, `concurrency-limits` and `Eureka` repositories.*

**Problem.** Video is bulk bandwidth a cloud region should not carry, and hundreds of services will fail in unpredicted ways, so failure has to be practised.

**Key decisions.**

- **Open Connect.** Netflix's own CDN: appliances (OCAs) inside ISP networks or at internet exchanges, pre-filled with content and refreshed nightly in off-peak fill windows, with ISPs steering traffic to them over BGP. A control plane in AWS picks the OCAs a client streams from by file availability, health and proximity.
- **Chaos engineering.** Define steady state by a business metric (the paper uses stream starts per second), hypothesise it holds under a real fault, run in production, minimise blast radius. The paper mentions "Chaos Kong" exercises that simulate losing an entire EC2 region.
- **Bulkheads and limits.** Hystrix isolates each dependency call (thread or semaphore) behind a circuit breaker with fallback; it is now in maintenance mode. `concurrency-limits` adapts a cap on in-flight requests using TCP-congestion-control ideas and rejects work above it.
- **Eureka.** Heartbeats every 30 seconds; clients cache the registry and keep working "even when all of the eureka servers go down". One cluster per region. It favours availability.

**Trade-offs.** A private CDN costs hardware and ISP relationships; production chaos needs strong observability; thread isolation spends threads per dependency.

**Where it shows up in an interview.** Video delivery ([29_cdn_and_streaming_media.md](29_cdn_and_streaming_media.md)) and resilience ([12](12_application_resilience_patterns.md), [28](28_overload_control_and_graceful_degradation.md)): pre-position the head of the catalogue, keep the control plane small, rehearse the failures you claim to survive.

## Uber: H3 and Cadence

*Sources: Uber Engineering blog posts on H3 (2018) and Cadence; Temporal's documentation for the durable-execution model.*

**Problem.** Surge pricing and dispatch need moving points bucketed into comparable regions, and long-running processes must survive crashes and deploys without hand-built state machines.

**Key decisions.**

- **H3** is a hexagonal hierarchical index with 16 resolutions, each cell about a seventh of its parent's area. Uber's reason for hexagons: one distance to all neighbours where a square has two, which simplifies smoothing and neighbour queries.
- **Cadence** is, in Uber's words, a multi-tenant orchestration framework for fault-tolerant long-running workflows. In the model Temporal (a descendant) documents, workflow code is deterministic, progress is an event history, and after a crash the code is replayed against it. Side effects run in retried activities, and timers are durable.

**Trade-offs.** H3 cells do not subdivide exactly and include 12 pentagons. Durable workflows demand deterministic code, and retried activities must be idempotent.

**Where it shows up in an interview.** Dispatch and nearby search ([026](../solutions/026_nearby_places_solution.md)): H3, S2 and geohash are interchangeable "cell id becomes bucket key" schemes. Sagas and schedulers ([012](../solutions/012_workflow_scheduler_solution.md)): durable orchestrator plus idempotent steps.

## Snowflake IDs (Twitter, 2010)

*Twitter's `snowflake` repository.*

**Problem.** 64-bit IDs from many machines with no per-ID coordination, roughly time-sorted.

**Key decisions.** 41 bits of milliseconds since a custom epoch (`2^41 ms ≈ 69.7 years`), 10 bits of configured machine id (1,024 machines), a 12-bit sequence (4,096 per millisecond per machine, about 4.1M/s). The README calls IDs "k-sorted", requires NTP, and has the generator refuse to issue IDs if the clock goes backwards.

**Trade-offs.** Needs sane clocks and unique machine ids; order across machines is approximate.

**Where it shows up in an interview.** ID generators ([022](../solutions/022_unique_id_generator_solution.md)) and chat: Discord's post says every ID it used was a Snowflake.

## Stripe idempotency keys (API documentation)

**Problem.** A timeout on "charge this card" leaves the client unsure whether it happened, and a blind retry can charge twice.

**Key decisions.** The client sends an `Idempotency-Key` on POST. Stripe saves the status and body of the first request for the key, **including 500s**, and replays them. Keys are up to 255 characters, may be pruned after at least 24 hours, and a request whose parameters differ from the original errors.

**Trade-offs.** A durable store with atomic claim-then-execute, and a retention window; clients must reuse the key for one operation only.

**Where it shows up in an interview.** Payments ([008](../solutions/008_checkout_solution.md), [017](../solutions/017_payment_ledger_solution.md)): at-least-once delivery plus an idempotent handler is effectively once. See [04_api_design_low_level.md](04_api_design_low_level.md).

## Discord message storage (Discord Engineering blog, 2023)

**Problem.** Trillions of messages, read mostly as recent history of one channel, with wildly skewed channel sizes.

**Key decisions.**

- **Schema**: partition by channel plus a **bucket** (a static time window), ordered by Snowflake id.
- **The move**: Cassandra hit hot partitions, compaction lag and GC pauses (12 nodes in 2017, 177 by early 2022). On ScyllaDB: 72 nodes, p99 reads 40-125 ms down to 15 ms, inserts 5-70 ms down to 5 ms.
- **Rust data service** with **request coalescing** (concurrent requests for a row make one query) and consistent-hash routing by channel id so identical requests meet. A custom migrator ran at about 3.2 million messages per second, finishing in nine days against a three-month Spark estimate.

**Trade-offs.** Buckets bound partitions but make a read span buckets; coalescing needs identical requests routed together.

**Where it shows up in an interview.** Chat ([006](../solutions/006_chat_solution.md)): a time bucket in the partition key, coalescing for hot partitions, and a migration plan.

## Recurring ideas across these papers

| Idea | Where it appears | Where to use it |
|---|---|---|
| Separate metadata from data | GFS ([24](24_google_papers.md)), Haystack index, Aurora compute/storage split | [08_object_storage.md](08_object_storage.md) |
| Invalidate, don't update | Memcache delete-on-write, TAO invalidations | [07_caching.md](07_caching.md), [018](../solutions/018_distributed_cache_solution.md) |
| Log-structured, append-only storage | Haystack, Kafka segments, Aurora redo log, Bigtable | [26_distributed_log_internals.md](26_distributed_log_internals.md) |
| Cells and blast radius | Aurora AZ quorum, Eureka per region, Gorilla regions, chaos limits | [27_multi_region_and_global_traffic.md](27_multi_region_and_global_traffic.md) |
| Make retries safe | Stripe keys, Cadence activities, Kafka at-least-once | [04_api_design_low_level.md](04_api_design_low_level.md), [008](../solutions/008_checkout_solution.md) |
| Protect the backend from misses | Leases and Gutter, Discord coalescing, concurrency limits, [hedging limits](24_google_papers.md#the-tail-at-scale-2013) | [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md) |
| Tier by temperature | Haystack to f4, Gorilla's 26 hours in RAM | [013](../solutions/013_metrics_platform_solution.md) |
| Availability where data is derived | Gorilla, Eureka, Monarch | [10_distributed_systems_theory.md](10_distributed_systems_theory.md) |
| Quorums from failure domains | Aurora 4/6 and 3/6, DynamoDB Multi-Paxos | [19_consensus_and_coordination.md](19_consensus_and_coordination.md) |

## Related building blocks

- [24_google_papers.md](24_google_papers.md)
- [07_caching.md](07_caching.md)
- [08_object_storage.md](08_object_storage.md)
- [26_distributed_log_internals.md](26_distributed_log_internals.md)
- [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md)
- [30_social_graph_and_caching_at_scale.md](30_social_graph_and_caching_at_scale.md)
