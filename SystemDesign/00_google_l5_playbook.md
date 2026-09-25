# Google L5 System Design Playbook

The system design round is the one that most often decides between an L4 and an L5 offer. Coding rounds show that you can build a component; this round shows that you can own a system — scope it, size it, make the hard trade-offs, and anticipate how it fails — while leading the conversation.

This page is the operating manual. Every practice problem in this module has a 45-minute coach on it that follows exactly this structure.

> 🎯 At L5 the interviewer should mostly be *reacting* to you. If they are steering every step — "what about caching?", "how would you store this?" — the same design reads as L4.

---

## Preparing for a specific company

This page is the base method, and its examples lean toward Google's 45-minute round. Meta, Netflix and Amazon test the same skills with a different format, a different steering style, and different depth areas. Read this page first, then the [company interview guide](01_company_interview_guide.md). For each company it gives:

- the commonly reported round format, and how to compress or stretch the timeline below;
- who drives the conversation, and what tends to be rewarded or penalized;
- a level ladder (Google L4–L6, Meta E4–E6, Netflix senior and staff, Amazon SDE II to Principal);
- an ordered path through this module with an hour budget, and the news feed argued four ways.

> ⚠️ Interview formats are *commonly reported*, not official. They change by team, level and year, so confirm the round length, level and tooling with your recruiter. The method on this page holds either way.

---

## What the round actually measures

A Google design interview is 45 minutes with one interviewer and an open-ended prompt ("design YouTube view counting", "design a service like Google Docs"). There is no single right architecture. The interviewer writes notes against a handful of signals, and a hiring committee that never met you reads those notes. That is why *saying* your reasoning out loud matters as much as having it.

| Signal | L4 answer | L5 answer | L6 answer |
|---|---|---|---|
| Problem exploration | Accepts the prompt, starts drawing. | Proposes requirements and scale, confirms them, names what is out of scope. | Reframes the problem around what the business actually needs; spots the requirement nobody said out loud. |
| Estimation | Computes numbers when asked. | Computes the few numbers that matter and turns each into a decision. | Knows which numbers are irrelevant and skips them. |
| Design quality | A reasonable box diagram with standard components. | Every component is justified by a requirement; the data model follows access patterns. | Evolves the design across phases (launch, 10×, multi-region) with migration paths. |
| Trade-offs | Lists pros and cons. | Compares alternatives, **commits**, and says what is given up and why that is acceptable. | Quantifies the trade-off and ties it to cost, team, and operational burden. |
| Depth | Goes deep only when pushed. | Picks the two hardest problems unprompted and goes deep on them. | Goes deep anywhere, and knows when depth is not worth the time. |
| Operations & failure | Mentions "add monitoring" and "replicas". | Raises failure modes before being asked; names SLIs, alerts, degradation behaviour. | Designs for failure domains, deploys, and incident response from the start. |
| Communication | Answers questions. | Drives: announces the plan, checks in at transitions, manages time. | Makes the interviewer's job easy; the conversation feels like a design review with a peer. |

### Going from L5 to L6

L6 is not "L5 with more boxes". The diagram can be identical. What changes is what you treat as the problem, and how far your reasoning reaches beyond the diagram.

| Dimension | L5 does | L6 adds |
|---|---|---|
| Scoping | Proposes requirements and scale, names what is out of scope. | Asks what decision the system serves and for whom, spots the requirement nobody said (a migration, a compliance rule, a second team's consumer), and proposes a phase-one scope that ships. |
| Estimation | Computes the few numbers that decide something. | Finds the number that dominates cost or risk (often write amplification or storage, not read <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>), skips the rest, and says what would make the estimate wrong. |
| Depth | Two hard problems, unprompted. | Depth wherever the risk is, including the unglamorous parts (backfill, deletion, schema evolution), and a sense of when to stop. |
| Trade-offs | Compares, commits, names the cost. | Quantifies the cost in money, latency and on-call burden, and says what evidence would reverse the decision. |
| Operations | Failure modes, SLIs, one paging alert. | Rollout path (canary, cell by cell, rollback triggers), blast-radius boundaries, the migration from the old system, and how you would know it works before scaling it. |
| Communication | Drives and checks in at transitions. | Runs it as a design review with a peer: states assumptions as decisions to confirm, names the risks you are *not* solving, invites the strongest objection. |

Three moments, as an L5 sentence and an L6 sentence. The numbers are illustrative assumptions for a news feed, not measurements.

**Scoping**
- L5: "I'll assume 300M daily users, read-heavy, with ranking and ads out of scope. Is that the right scope?"
- L6: "Before sizing anything: what is the feed for? If the goal is retention, a blank page hurts more than a slightly stale one, so I'll optimize for never being empty. I'd ship phase one as reverse-chronological with hybrid fan-out and add ranking behind the same <abbr title="Application Programming Interface">API</abbr> in phase two. Does that ordering match the goal?"

**Estimation**
- L5: "300M users × 10 opens a day ÷ 86,400 is about 35K reads per second, about 100K at a 3× peak, so one database cannot serve this and we need a cache."
- L6: "Reads are the easy part: a cache that absorbs 95% leaves 5K reads per second for the store. What sizes the system is fan-out writes: 100M posts a day × 200 followers ÷ 86,400 is about 230K feed inserts per second, roughly 700K at peak. So I'll cap push fan-out by author size and skip inactive users, and I'd measure the real follower distribution before trusting any of it."

**Trade-off**
- L5: "Async replication to the follower region: low write latency, and we accept losing a few seconds of likes on failover, which is fine because likes are not money."
- L6: "Async replication, with the loss window as a number we own: replication-lag p99 is our RPO and we alert at half of the agreed budget. If the business later wants zero loss for likes, it costs a cross-region round trip, about 150 ms, on every like. I'd ship async, keep the synchronous path behind a flag, and revisit once we know how much loss users notice."

> 💡 The L6 version is longer by a clause, not by a minute. Add the cost, the evidence that would change your mind, or the rollout path — one clause each — instead of talking more.

---

## The 45-minute timeline

| Minutes | Phase | What you produce | The trap |
|---|---|---|---|
| 0–5 | Requirements | Core features, out-of-scope list, scale, latency, availability vs consistency. | Spending 12 minutes here, or skipping non-functional requirements entirely. |
| 5–10 | Estimates & <abbr title="Application Programming Interface">API</abbr> | Peak <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, bandwidth; main endpoints. | Numbers with no consequence ("so 12K <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>… anyway"). |
| 10–15 | Data model | Entities, access patterns, database choice with the rejected alternative, first shard key. | Picking a database by brand name. |
| 15–25 | High-level design | Baseline diagram; one write and one read walked end to end. | Drawing 15 boxes before any of them are justified. |
| 25–38 | Deep dives | Two hard problems, alternatives compared, decisions made. | Going wide instead of deep; waiting for the interviewer to pick. |
| 38–45 | Failure & evolution | What breaks, how you notice, what changes at 10×. | Running out of time before ever mentioning failure. |

> 💡 Say the plan out loud in the first 30 seconds: *"I'll spend a few minutes on requirements and scale, sketch the <abbr title="Application Programming Interface">API</abbr> and data model, draw a baseline, then go deep on the two hardest parts and finish with failure modes."* It signals that you drive the round, and it gives the interviewer a map to interrupt against.

---

## Requirements: the questions worth asking

Ask questions that change the design. "Should it be scalable?" changes nothing. These do:

| Ask about | Why it changes the design |
|---|---|
| Read:write ratio | Read-heavy → caches, replicas, precomputation. Write-heavy → log-structured storage, partitioning, async pipelines. |
| Consistency per flow | "Can a like count be a few seconds stale?" (yes → eventual) vs "can two people book the same seat?" (no → transactions or conditional writes). |
| Latency target and where | p99 for the hot read path decides caching and fan-out limits. |
| Data size and retention | Decides object storage vs database, tiering, and deletion obligations. |
| Global or regional | Multi-region replication, data residency, conflict handling. |
| Freshness | "Within 30 seconds" permits async fan-out; "immediately visible to the author" needs read-your-writes. |
| Abuse and trust | Anything user-generated needs rate limits, validation, and moderation hooks. |

Then **write down** 3–5 functional requirements and 3–5 non-functional requirements and ask: *"Is this the right scope?"*

---

## Estimation in under four minutes

You are estimating to make decisions, not to be precise. Round everything to one significant figure, and after each number say what it implies.

The core formulas:

- **<abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>** = daily active users × actions per user ÷ 86,400. Peak ≈ 2–3× average (more for spiky products).
- **Storage** = records per day × size × 365 × years × replication factor.
- **Bandwidth** = <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> × payload size × 8 bits.
- **Cache** = roughly 20% of the daily read set if access is skewed (80/20).
- **Servers** = peak <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> ÷ what one server handles, plus headroom for a zone failure.

The estimator below lets you check your mental arithmetic against presets for common problems.

### Numbers worth memorizing

| Operation | Time | Scale in human terms |
|---|---|---|
| L1 cache reference | 0.5 ns | |
| Main memory reference | 100 ns | |
| Compress 1 KB (fast codec) | 2–10 µs | |
| Read 4 KB randomly from <abbr title="Solid-State Drive - A solid-state storage device that uses integrated circuit assemblies to store data persistently, offering faster access times.">SSD</abbr> | ~100 µs | |
| Round trip within a datacenter | ~500 µs | |
| Read 1 MB sequentially from <abbr title="Solid-State Drive - A solid-state storage device that uses integrated circuit assemblies to store data persistently, offering faster access times.">SSD</abbr> | ~1 ms | |
| Disk seek (<abbr title="Hard Disk Drive - An electro-mechanical data storage device that stores and retrieves digital data using magnetic storage.">HDD</abbr>) | ~10 ms | 20× slower than a datacenter round trip |
| Round trip California ↔ Netherlands | ~150 ms | Why CDNs and regional replicas exist |

| Power of two | Exact | Approx. | Name |
|---|---|---|---|
| 2¹⁰ | 1,024 | 1 thousand | 1 KB |
| 2²⁰ | 1,048,576 | 1 million | 1 MB |
| 2³⁰ | ~1.07 × 10⁹ | 1 billion | 1 GB |
| 2⁴⁰ | ~1.1 × 10¹² | 1 trillion | 1 TB |
| 2⁵⁰ | ~1.13 × 10¹⁵ | 1 quadrillion | 1 PB |

| Availability | Downtime per year | Downtime per month |
|---|---|---|
| 99% | 3.65 days | 7.3 hours |
| 99.9% | 8.8 hours | 44 minutes |
| 99.99% | 53 minutes | 4.4 minutes |
| 99.999% | 5.3 minutes | 26 seconds |

> ⚠️ Serial dependencies multiply: three services at 99.9% in a chain give about 99.7%. Parallel redundancy is what raises availability — and only if the replicas fail independently.

The full treatment, with worked examples, is in [building_blocks/18_back_of_envelope_estimation.md](building_blocks/18_back_of_envelope_estimation.md).

---

## Deep dives interviewers push on, by problem family

When you reach the deep-dive phase, pick the parts where the problem is actually hard. For most prompts, they are predictable:

| Problem family | The hard parts to volunteer | Building block |
|---|---|---|
| URL shortener, pastebin | ID generation and collisions; read-heavy caching; redirects and analytics without slowing the hot path. | [10](building_blocks/10_distributed_systems_theory.md), [07](building_blocks/07_caching.md) |
| Rate limiter, <abbr title="Application Programming Interface">API</abbr> gateway | Algorithm choice; atomic counters in a shared store; multi-region limits; fail-open vs fail-closed. | [04](building_blocks/04_api_design_low_level.md) |
| Key-value store, distributed cache | Partitioning with consistent hashing; quorum replication; conflict resolution; hot keys; rebalancing. | [19](building_blocks/19_consensus_and_coordination.md), [25](building_blocks/25_partitioning_and_hot_keys.md) |
| News feed, notifications | Fan-out on write vs read; celebrity accounts; ranking; delivery guarantees and deduplication. | [09](building_blocks/09_messaging_and_streaming.md) |
| Chat, Google Docs | Connection servers and presence; per-conversation ordering; offline sync; OT vs CRDT. | [22](building_blocks/22_realtime_and_collaboration.md) |
| Drive, YouTube, photo pipeline | Chunked resumable uploads; dedup; transcoding <abbr title="Directed Acyclic Graph. A directed graph with no directed cycles, consisting of vertices and edges where each edge is directed from one vertex to another.">DAG</abbr>; <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>; view counting at scale. | [08](building_blocks/08_object_storage.md) |
| Web search, autocomplete | Crawl → index → serve; sharding the inverted index; fan-out and tail latency; top-K per prefix. | [20](building_blocks/20_specialized_data_structures.md) |
| Maps, nearby, ride sharing | Geospatial indexing (geohash, quadtree, S2); location update volume; matching without double assignment. | [20](building_blocks/20_specialized_data_structures.md) |
| Ad clicks, metrics, top-K | Windowed stream aggregation; late data and watermarks; exactly-once counting; batch reconciliation. | [21](building_blocks/21_batch_and_stream_processing.md) |
| Payments, booking | Idempotency; double-entry ledger; sagas and reconciliation; holds with expiry; contention. | [11](building_blocks/11_transactions_and_concurrency.md) |
| <abbr title="Large Language Model">LLM</abbr> or <abbr title="Machine Learning">ML</abbr> feature | Serving cost and batching; token streaming; caching; quotas; evaluation and safety. | [23](building_blocks/23_ml_and_llm_systems.md) |
| Message queue, distributed log | Partitioned replicated log; acks and in-sync replicas versus latency; consumer groups and rebalancing; delivery semantics; retention and compaction. | [26](building_blocks/26_distributed_log_internals.md) · [031](problems/031_distributed_message_queue_question.md) |
| Ranked feed, recommendations | Retrieval, then a ranking cascade under a per-stage latency budget; feature serving; session-stable pagination; exploration; fallback when the ranker is down. | [31](building_blocks/31_ranking_recommendation_and_experimentation.md), [23](building_blocks/23_ml_and_llm_systems.md) · [032](problems/032_ranked_home_feed_question.md) |
| Live streaming and comments | Ingest, real-time transcode, low-latency packaging; fan-out of one mega-stream through the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>; comment fan-out and sampling; the glass-to-glass latency budget. | [29](building_blocks/29_cdn_and_streaming_media.md), [22](building_blocks/22_realtime_and_collaboration.md) · [033](problems/033_live_streaming_and_comments_question.md) |
| Routing, maps, ETA | Preprocessing the road graph (contraction hierarchies), sharding it, live traffic weights, map matching, and how an ETA model is fed. | [20](building_blocks/20_specialized_data_structures.md), [25](building_blocks/25_partitioning_and_hot_keys.md) · [034](problems/034_maps_routing_and_eta_question.md) |
| Object store | Erasure coding versus replication (durability arithmetic); metadata index separate from data placement; repair bandwidth; garbage collection; LIST at scale. | [08](building_blocks/08_object_storage.md), [25](building_blocks/25_partitioning_and_hot_keys.md) |
| <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> | Request steering; cache hierarchy; hot objects and request coalescing; purge; <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> at the edge; caches embedded in ISP networks. | [29](building_blocks/29_cdn_and_streaming_media.md), [27](building_blocks/27_multi_region_and_global_traffic.md) · [036](problems/036_content_delivery_network_question.md) |
| Experimentation platform | Hash bucketing and layers; exposure logging; sample-ratio mismatch; power and variance reduction; guardrail metrics. | [31](building_blocks/31_ranking_recommendation_and_experimentation.md), [21](building_blocks/21_batch_and_stream_processing.md) · [037](problems/037_experimentation_platform_question.md) |
| Video conferencing | SFU versus MCU; signaling; simulcast and congestion control; cascaded SFUs across regions. | [22](building_blocks/22_realtime_and_collaboration.md), [02](building_blocks/02_networking.md) · [038](problems/038_video_conferencing_question.md) |
| Social graph | Objects and associations; cache tiers; hot edge lists; two-hop queries; privacy checks on every read. | [30](building_blocks/30_social_graph_and_caching_at_scale.md), [25](building_blocks/25_partitioning_and_hot_keys.md) · [039](problems/039_social_graph_service_question.md) |
| Lock service, coordination | Consensus-backed state machine; sessions and leases; fencing tokens; watches; client-side caching. | [19](building_blocks/19_consensus_and_coordination.md) · [040](problems/040_distributed_lock_service_question.md) |
| Email | SMTP ingest and the spam pipeline; mailbox storage; per-user search; sync cursors; deliverability. | [08](building_blocks/08_object_storage.md), [09](building_blocks/09_messaging_and_streaming.md) |
| Any global service | Traffic steering, data replication modes, RPO and RTO, failback. | [27](building_blocks/27_multi_region_and_global_traffic.md) |
| Any service under load spikes | Load shedding, retry budgets, priorities, graceful degradation. | [28](building_blocks/28_overload_control_and_graceful_degradation.md) |

The problem number after the · is the practice problem to attempt against the clock; the [catalog](02_problem_catalog.md) lists all 39. Company-specific emphasis is in the [company interview guide](01_company_interview_guide.md).

---

## The trade-off sentence

Every decision you make in the deep dives should come out as one sentence with four parts: **choice, what it gives, what it costs, why the cost is acceptable here.**

> ✅ "I'll use asynchronous replication to the follower region. We get low write latency, and we accept that a regional failover can lose a few seconds of likes, which is fine because likes are not money. For the payment ledger I'd make the opposite choice."

Compare with the L4 version: "We could use sync or async replication; sync is consistent but slow, async is fast but can lose data." Both are true. Only one makes a decision.

---

## Failure and operations: what to say before you are asked

Walk the diagram box by box and say what happens when each one fails:

| Component fails | Say this |
|---|---|
| Cache cluster | Requests fall through to the database; protect it with request coalescing, a circuit breaker, and serving stale values. Warm the cache before shifting traffic back. |
| One database shard | Reads fail over to a replica; writes to that key range pause for the election window. Other shards are unaffected — that is the point of partitioning. |
| Message queue backs up | Consumers scale out to the partition count; producers apply backpressure; lower-priority work is shed first. |
| A whole region | <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>/anycast shifts traffic; the surviving region needs spare capacity (plan N+1 regions); state replication lag defines RPO. Steering, replication modes and failback are in [27](building_blocks/27_multi_region_and_global_traffic.md). |
| A bad deploy | Canary, automated rollback on <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> burn, feature flags to turn off new paths. |
| A dependency is slow, not down | A request that fans out to many servers is as slow as the slowest reply. Set deadlines, hedge a request after roughly the p95 latency, and return a partial result when a shard is late. These are the techniques in Dean and Barroso, "The Tail at Scale" (CACM, 2013), summarized in [24](building_blocks/24_google_papers.md). |
| A traffic spike or retry storm | Shed low-priority requests early, cap retries with a budget, and degrade the product before the page. See [28](building_blocks/28_overload_control_and_graceful_degradation.md). |

Two calculations make the last rows concrete:

- **Tail.** If each of 100 servers is slow on 1% of requests, a request that waits for all 100 is slow with probability 1 − 0.99¹⁰⁰ ≈ 63%. So at high fan-out the tail *is* the typical case, and you design for it with deadlines and hedging, not by hoping for faster servers.
- **Retries.** If each of three layers makes up to three attempts per call, one client request can become 3 × 3 × 3 = 27 calls to the bottom layer, at the moment it is already struggling. So retry at one layer, budget the retries, and shed load rather than queue it. When a region fails, the survivors also absorb the shifted traffic on top of their own, which is why the failover plan in [27](building_blocks/27_multi_region_and_global_traffic.md) and the shedding rules in [28](building_blocks/28_overload_control_and_graceful_degradation.md) belong in the same answer.

Then name 3–4 SLIs (e.g. p99 read latency, write success rate, fan-out lag, queue age) and the one alert that should page someone.

---

## Red flags that cap the level

> ⚠️ Each of these is survivable on its own. Two or three together usually produce an L4 or no-hire recommendation.

1. Drawing a diagram before stating requirements or scale.
2. Choosing technologies by name ("Kafka, Cassandra, Redis") without the property that justifies each.
3. Over-engineering from minute one — microservices, multi-region, and a service mesh for a problem that fits on three servers.
4. Never making a decision: listing options and waiting for the interviewer to choose.
5. Hand-waving the hard part ("the ranking service handles that").
6. No mention of failure, monitoring, or data loss until the interviewer asks.
7. Ignoring the interviewer's hints, or arguing with them instead of exploring the constraint they introduced.
8. Running out of time with no deep dive at all.

---

## Naming Google infrastructure

You are not expected to design with Google-internal products, and naming them is not a shortcut. Name the **property**, and optionally the system as an example:

- "A globally consistent relational store with external consistency — the Spanner model" — only when you truly need cross-region transactions.
- "A wide-column store optimised for high write throughput and range scans — like Bigtable" — for time-series or large sparse tables.
- "A lock service with leases for leader election — the Chubby model."

Summaries of the papers behind these systems are in [building_blocks/24_google_papers.md](building_blocks/24_google_papers.md).

---

## A one-page answer template

```text
1. Requirements    functional (3–5), out of scope, non-functional: scale, latency, consistency, durability
2. Estimates       peak read/write QPS, storage/year, bandwidth → "so we need …"
3. API             3–5 endpoints: method, path, request, response, idempotency
4. Data model      entities + keys, access patterns, store choice (and the rejected one), shard key
5. Baseline        client → edge/LB → services → cache/DB/queue/object store; walk 1 write + 1 read
6. Deep dive #1    problem, 2 alternatives, decision + trade-off sentence, numbers
7. Deep dive #2    same
8. Failure         each box fails → behaviour; SLIs + paging alert
9. Evolution       10× traffic, multi-region, what you would revisit
```

---

## How to practise with this module

1. Read the building blocks in order, then [18](building_blocks/18_back_of_envelope_estimation.md) through [25](building_blocks/25_partitioning_and_hot_keys.md) for the Google-specific depth.
2. Open a practice problem, start the coach's 45-minute clock, and talk out loud — record yourself if you can.
3. Only when the clock ends, reveal the reference design and compare **decisions**, not boxes.
4. Redo the problem a week later under one changed constraint: 10× traffic, strict consistency, or a region failure.
5. Aim for at least 15 of the problems done cold, each with two real deep dives — that is the bar in the prep plan.

## Related building blocks

- [01_company_interview_guide.md](01_company_interview_guide.md)
- [building_blocks/27_multi_region_and_global_traffic.md](building_blocks/27_multi_region_and_global_traffic.md)
- [building_blocks/28_overload_control_and_graceful_degradation.md](building_blocks/28_overload_control_and_graceful_degradation.md)
- [building_blocks/17_decision_framework.md](building_blocks/17_decision_framework.md)
- [building_blocks/18_back_of_envelope_estimation.md](building_blocks/18_back_of_envelope_estimation.md)
- [02_problem_catalog.md](02_problem_catalog.md)
