# Back-of-the-Envelope Estimation

An estimate in a design interview has one job: to force a decision. "12,000 writes per second at peak" is only useful if the next sentence is "…which is more than one relational primary comfortably takes, so we partition the write path." This file gives you the method, the numbers to carry in your head, and worked examples you can reproduce in under four minutes.

> 💡 Precision is not the goal. Being within a factor of 2–3 is plenty, because design decisions change at factors of 10: one machine vs a cluster, a database vs object storage, a single region vs a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>.

## Why estimate at all

| Question the numbers answer | Decision it drives |
|---|---|
| Does the write rate fit on one primary? | Single database vs sharding / write-optimised store. |
| Is the read:write ratio skewed? | Caching and read replicas vs a balanced design. |
| Does the dataset fit in memory? | Cache the whole hot set vs cache selectively. |
| How big does storage get over the retention period? | Database vs object storage; tiering; erasure coding. |
| How much bandwidth leaves the origin? | Whether a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> is required rather than nice to have. |
| How many servers at peak, with a zone down? | Capacity plan and cost ballpark. |

## The method

1. **State the assumptions** out loud: daily active users, actions per user, object size, retention, replication. Round them.
2. **Convert per day to per second**: divide by 86,400 ≈ 10⁵. One million events a day is about 12 per second.
3. **Apply a peak factor**: 2–3× for most consumer products, 5–10× for event-driven spikes (ticket sales, sports, launches).
4. **Multiply out storage and bandwidth**, including replication and retention.
5. **Say the consequence** of each number, then move on. The whole thing should take 3–4 minutes.

Use the estimator to practise: set a preset, estimate in your head first, then check.

```arch
%% caption: The estimation workflow moves from business assumptions to system constraints, culminating in an architectural decision.
route straight
node assum "1. Assumptions\n(DAU, Actions)" at 0,0 icon=user color=blue
node req "2. Per-second rate\n(RPS / QPS)" at 2,0 icon=metrics color=amber
node peak "3. Peak factor\n(x2 or x3 multiplier)" at 4,0 icon=timer color=red
node store "4. Storage & IO\n(Size x Time)" at 6,0 icon=db color=slate
node dec "5. Arch Decision\n(Implications)" at 8,0 icon=app color=green

assum -> req
req -> peak
peak -> store
store -> dec
```

## Latency numbers and tail latency

Memorise the orders of magnitude, not the digits. The ratios are what matter: memory is roughly 1,000× faster than an <abbr title="Solid-State Drive - A solid-state storage device that uses integrated circuit assemblies to store data persistently, offering faster access times.">SSD</abbr> random read, a datacenter round trip is 300× faster than crossing an ocean.

| Operation | Approximate time |
|---|---|
| L1 cache reference | 0.5 ns |
| Branch mispredict | 5 ns |
| Mutex lock/unlock | 25 ns |
| Main memory reference | 100 ns |
| Transmit 1 KB on a 10 Gbps link (serialization time only) | ~0.8 µs (~8 µs at 1 Gbps) |
| Compress 1 KB with a fast codec | 2–10 µs |
| Read 4 KB randomly from an <abbr title="Solid-State Drive - A solid-state storage device that uses integrated circuit assemblies to store data persistently, offering faster access times.">SSD</abbr> | 20–150 µs |
| Read 1 MB sequentially from memory | 250 µs |
| Round trip within one datacenter | 500 µs |
| Read 1 MB sequentially from an <abbr title="Solid-State Drive - A solid-state storage device that uses integrated circuit assemblies to store data persistently, offering faster access times.">SSD</abbr> | ~1 ms |
| <abbr title="Hard Disk Drive - An electro-mechanical data storage device that stores and retrieves digital data using magnetic storage.">HDD</abbr> seek | 10 ms |
| Read 1 MB sequentially from an <abbr title="Hard Disk Drive - An electro-mechanical data storage device that stores and retrieves digital data using magnetic storage.">HDD</abbr> | 20 ms |
| Round trip across a continent | 50–80 ms |
| Round trip California ↔ Europe | 150 ms |

The wire row is pure transmission time: `1 KB × 8 bits ÷ 10 Gbps ≈ 0.8 µs`. A real small send also pays for the kernel network stack, the NIC, switch hops and any queueing, which is why the round trip *within* one datacenter is closer to 500 µs than to 1 µs. Confusing wire time with a completed request under-estimates network cost by two to three orders of magnitude.

Averages hide the tail. When one user request fans out to many servers and waits for all of them, the slowest server decides the latency. If each server has a 1% chance of being slow, a request touching 100 servers hits at least one slow server 63% of the time: `1 − 0.99¹⁰⁰ ≈ 0.63`. That is why search and feed backends care about per-server p99, and use hedged requests and partial results.

## Powers of two and data sizes

| Power | Value | Rule of thumb |
|---|---|---|
| 2¹⁰ | ~1 thousand | KB |
| 2²⁰ | ~1 million | MB |
| 2³⁰ | ~1 billion | GB |
| 2⁴⁰ | ~1 trillion | TB |
| 2⁵⁰ | ~1 quadrillion | PB |

| Thing | Typical size |
|---|---|
| A <abbr title="Universally Unique Identifier - A 128-bit label used for information in computer systems to ensure uniqueness across distributed systems.">UUID</abbr> / 128-bit ID | 16 bytes (36 as text) |
| A 64-bit integer or timestamp | 8 bytes |
| A tweet-sized text post with metadata | 0.5–2 KB |
| A row in a typical OLTP table | 0.2–1 KB |
| A compressed phone photo | 1–3 MB |
| One minute of 1080p video (streaming bitrate, ~5–8 Mbps) | ~40–60 MB |
| An embedding vector (768 float32) | ~3 KB |

## Availability and the nines

| Target | Downtime per year | Per 30 days | What it usually implies |
|---|---|---|---|
| 99% | 3.65 days | 7.2 h | One region, manual recovery is tolerable. |
| 99.9% | 8.8 h | 43 min | Redundant instances, automated failover within a region. |
| 99.99% | 53 min | 4.3 min | Multi-zone everything, no single-writer bottleneck without fast failover, careful deploys. |
| 99.999% | 5.3 min | 26 s | Multi-region active-active, extensive automation — very expensive. |

Components in series multiply availability; components in parallel (with independent failures) combine as `1 − (1 − a)ⁿ`. Two independent replicas at 99% give 99.99% — but only if they don't share a failure domain.

## Worked example: a photo-sharing app

Assumptions: 500M DAU, each uploads 0.2 photos and views 30 photos a day, 2 MB per photo, keep forever (plan 10 years), 3 copies.

| Quantity | Arithmetic | Result | So… |
|---|---|---|---|
| Upload <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> | 500M × 0.2 ÷ 10⁵ | ~1,000/s, peak ~3,000/s | Uploads go directly to object storage with presigned URLs; the <abbr title="Application Programming Interface">API</abbr> only writes metadata. |
| View <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> | 500M × 30 ÷ 10⁵ | ~150,000/s, peak ~450,000/s | Read-heavy at 150:1 — a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> serves image bytes; the metadata path needs caching. |
| New storage/day | 100M photos × 2 MB | 200 TB/day | Object storage with lifecycle tiers; not a database. |
| 10-year storage | 200 TB × 3,650 × 3 | ~2 EB | At this size, erasure coding instead of 3× replication saves roughly half. |
| Egress | 150,000/s × 2 MB × 8 bits | ~2.4 Tbps average, ~7 Tbps at the 3× peak | <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> is mandatory; origin serves only cache misses. |
| Metadata store | 100M rows/day × 1 KB × 3,650 | ~365 TB before replication | Sharded metadata store, partitioned by photo ID or owner. |

## Worked example: a chat service

Assumptions: 1B DAU, 40 messages sent per user per day, 1 KB per message with metadata, 3-year retention, 3 copies.

| Quantity | Arithmetic | Result | So… |
|---|---|---|---|
| Message <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> | 1B × 40 ÷ 10⁵ | ~400,000/s, peak ~1.2M/s at 3× | Partition by conversation; single ordered log per conversation, not a global order. |
| Storage | 40B msgs/day × 1 KB = 40 TB/day; × 365 = 14.6 PB/yr raw; × 3 years × 3 copies | ~15 PB/yr raw, ~44 PB raw over retention, ~130 PB replicated | Ingest is modest (40 TB/day ÷ 86,400 ≈ 0.5 GB/s), but the retained volume is not: shard a wide-column or log-structured store by conversation ID, tier old messages to cold storage, and use erasure coding (~1.5× instead of 3×, so ~66 PB) for the cold tier. Also question whether every user needs 3 years online. |
| Concurrent connections | say 30% of DAU online: 1B × 0.3 | ~300M WebSockets | Assuming ~100K connections per gateway host: 300M ÷ 100K = ~3,000 gateway servers, plus headroom. |

## Capacity: servers, cache, and headroom

- **Servers** = peak <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> ÷ per-server <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>. Measure or assume: a stateless <abbr title="Application Programming Interface">API</abbr> server doing a few database calls handles hundreds to low thousands of requests per second; a cache node handles 100K+ simple gets per second.
- **Headroom**: with three zones, losing one leaves two carrying the load, so utilisation `u` becomes `u × 3/2` on the survivors. At 60% that is 90%, at 70% it is 105% (overload), so plan for roughly 50–60% average utilisation before you also allow for a deploy in flight.
- **Cache size**: if 20% of items receive 80% of reads, caching the daily read set's hot 20% (item size × count) captures most of the benefit. If that is more memory than is sensible, cache small things (IDs, metadata, rendered fragments) instead of whole objects.
- **Queues**: a queue does not create capacity, it only buys time. If producers run faster than consumers for an hour, the backlog must fit, and the drain time must be acceptable.

## Common estimation mistakes

1. Forgetting the peak factor, then sizing for the average.
2. Forgetting replication (×3) and retention (×years) in storage.
3. Mixing bits and bytes in bandwidth (×8).
4. Computing numbers and never saying what they imply.
5. Estimating everything. Pick the 3–4 numbers that drive decisions for *this* problem.
6. False precision: "11,574 requests per second" — say "about 12K".

## Related building blocks

- [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md)
- [15_observability_and_reliability.md](15_observability_and_reliability.md)
- [17_decision_framework.md](17_decision_framework.md)
- [../00_google_l5_playbook.md](../00_google_l5_playbook.md)
