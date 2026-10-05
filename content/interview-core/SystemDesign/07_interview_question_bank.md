# System Design Interview Question Bank — Every Level

Design rounds are rarely one monologue. Between the big prompt ("design a news
feed") come dozens of smaller questions: *why that database, what happens when
this node dies, how would you invalidate that cache, what changes at 10×?* This
bank collects those questions, grouped by building block and tagged by the level
they usually appear at. Every answer is hidden until you have tried it out loud.

## How to Use This Bank

Answer each question aloud — about 30 seconds for the short version and two minutes
for the full one — before opening it. Compare the *decisions and trade-offs*, not the
wording. Retest misses after 1, 3 and 10 days.

Each answer has four layers:

| Layer | What it gives you |
|---|---|
| **Say this first** | The 30-second answer: the decision and the reason |
| **Then explain** | The mechanism, the numbers, and the failure modes |
| **Next follow-up** | What a strong interviewer asks next, and how to answer it |
| **Go deeper** | The building block, problem or live lab that covers it |

**What each level must show in a design round.**

| Tag | A passing answer shows |
|---|---|
| **L3/L4 · Junior–Mid** | A working design with the standard components, correct use of each, and sensible defaults |
| **L5 · Senior** | You drive: requirements and numbers first, two or more options compared, an explicit decision, failure modes raised unprompted, and what you would monitor |
| **L6+ · Staff** | You handle ambiguity and evolution: which requirement really drives the design, what changes at 10× or across regions, migration paths, cost, and team and operational consequences |

The most reliable seniority signal in every answer: **a decision followed by its cost.**
"I'll use X; we give up A, which is acceptable because B."

## 1. Framework and Estimation

### Q1.1 · L4 — How do you open a system design interview?

<details>
<summary>Open the answer</summary>

**Say this first.** Clarify before drawing: the core features and what is out of scope,
who the users are and how many, read and write volumes, latency and consistency needs,
and any hard constraints. Then estimate, sketch the API and data model, draw a simple
design that works, and deepen the hardest parts.

**Then explain.**
- Propose requirements and ask the interviewer to confirm them — don't wait to be told.
- A 45-minute shape: requirements (5 min), estimates and API (5), data model (5),
  high-level design (10), deep dives (13), failures and evolution (7).
- Walk a real write and a real read through the diagram; that finds the gaps.
- Every component must be justified by a requirement or a number.

**Next follow-up: "You have 45 minutes and I've said nothing about scale. What do you
assume?"** State an assumption with its consequence: "I'll assume 100 million daily users
and a 100:1 read-to-write ratio, which makes this read-heavy, so caching and read
replicas will matter more than write throughput. Tell me if that's off."

**Go deeper.** [Google L5 playbook](00_google_l5_playbook.md) and the 45-minute coach on
every practice problem.

</details>

### Q1.2 · L4 — Estimate the load for a Twitter-like home timeline.

<details>
<summary>Open the answer</summary>

**Say this first.** Start from users and actions, convert to per-second rates, apply a
peak factor, then estimate storage and bandwidth — rounding aggressively and saying what
each number implies.

**Then explain.**
- 200 M daily users, each loading the timeline 10 times a day = 2 × 10⁹ reads/day ≈
  23,000/s average; with a 3× peak, about 70,000 reads/s.
- 20% of users post once a day = 4 × 10⁷ posts/day ≈ 460/s, peaking near 1,500/s.
- A post of about 1 KB with metadata: 40 GB/day ≈ 15 TB/year before replication and
  media.
- Useful constants: a day is about 10⁵ seconds; one million requests a day is about 12
  per second.
- Conclusion to say aloud: "Reads outnumber writes 50 to 1, so precomputing timelines or
  caching them is worth a lot of write-side work."

**Next follow-up: "What if a user has 50 million followers?"** Fan-out on write explodes:
one post means 50 million timeline inserts. Use a hybrid — push posts from ordinary users
into followers' timelines, but pull celebrities' posts at read time and merge them.

**Go deeper.** [Back-of-envelope estimation](building_blocks/18_back_of_envelope_estimation.md)
and [news feed](problems/007_news_feed_question.md).

</details>

### Q1.3 · L5 — Which number in your estimate actually changes the design?

<details>
<summary>Open the answer</summary>

**Say this first.** Say the threshold each number crosses: peak writes versus what one
primary can take, working-set size versus RAM, fan-out per write, payload size versus
network, and the latency budget versus the number of sequential hops.

**Then explain.**
- A single well-tuned relational primary handles on the order of 10⁴ simple writes per
  second; above that, you partition.
- If the hot working set fits in RAM (hundreds of GB across a cache cluster), a cache
  absorbs most reads.
- A 200 ms p99 budget allows only a few sequential cross-service calls, and no
  cross-ocean round trips.
- Large objects (images, video) go to object storage and a CDN, never through the
  application servers.

**Next follow-up: "Your peak is 5,000 writes/s. Do you shard?"** Not yet: one primary with
batching and good indexes can take it, with read replicas for reads. Plan a shard key and
a migration path now, and shard when growth makes the ceiling real.

**Go deeper.** [Decision framework](building_blocks/17_decision_framework.md) and the
latency-numbers lab in [estimation](building_blocks/18_back_of_envelope_estimation.md).

</details>

## 2. Scaling Reads: Caching and CDNs

### Q2.1 · L4 — Cache-aside, write-through, or write-back?

<details>
<summary>Open the answer</summary>

**Say this first.** Cache-aside (the application reads the cache, and on a miss loads from
the database and fills the cache) is the default: simple, and the cache can fail without
losing data. Write-through updates the cache on every write, for fresher reads. Write-back
acknowledges writes from the cache and persists later — fastest, but it can lose data.

**Then explain.**
- Cache-aside: on a write, update the database, then **delete** the cache entry (don't
  set it), so a stale value can't be written back by a racing reader.
- Write-through keeps the cache warm but writes data that may never be read.
- Write-back suits counters and metrics where losing a few seconds is acceptable.
- Every cache needs a source of truth, a TTL or invalidation rule, and a plan for when
  the cache is down.

**Next follow-up: "Why delete instead of update on write?"** Two concurrent writers can
update the cache in the opposite order to the database, leaving the older value cached
indefinitely. Deleting makes the next read reload the truth; a short TTL bounds any
remaining race.

**Go deeper.** [Caching](building_blocks/07_caching.md) and its cache-aside flow.

</details>

### Q2.2 · L5 — How do you keep a cache consistent with the database, and what goes wrong?

<details>
<summary>Open the answer</summary>

**Say this first.** Decide how stale is acceptable per data type, then combine TTLs with
explicit invalidation — ideally driven from the database's change stream rather than from
every code path that writes.

**Then explain.**
- Races: a reader loads a value, a writer updates and invalidates, then the reader writes
  its stale value into the cache. Fixes: versioned values (only replace older with
  newer), short TTLs, or leases (Facebook's memcache paper).
- Change data capture (tailing the database log) invalidates reliably even when a code
  path forgets.
- Stampedes: a hot key expires and thousands of requests hit the database at once. Use
  request coalescing, early probabilistic refresh, or serve-stale-while-revalidate.
- Negative caching (remembering "not found") stops repeated misses for keys that don't
  exist.

**Next follow-up: "A hot key expires and the database falls over. Fix it."** Coalesce
misses so one request per key refreshes it; refresh before expiry with jittered TTLs;
serve the stale value while one worker reloads it.

**Go deeper.** [Caching](building_blocks/07_caching.md) and its stampede lab.

</details>

### Q2.3 · L5 — A celebrity's post puts one cache node at 100% CPU. What do you do?

<details>
<summary>Open the answer</summary>

**Say this first.** It's a hot key: consistent hashing sends every request for it to one
node. Spread the key — replicate it to several nodes under suffixed keys and read a random
copy — and cache it in-process on the application servers for a second or two.

**Then explain.**
- Detect hot keys by sampling request logs or with a count-min sketch on the proxy.
- Key splitting: `post:123#0` … `post:123#7`, written to all and read from one at random.
- A tiny local cache in each app server absorbs most of the load with little staleness.
- The same pattern applies to write hot spots (counters): shard the counter and sum on
  read.

**Next follow-up: "How do you update a value that's replicated eight ways?"** Write or
invalidate all copies (or let them expire on a short TTL); the brief inconsistency is
usually acceptable for this kind of data.

**Go deeper.** [Partitioning and hot keys](building_blocks/25_partitioning_and_hot_keys.md)
and [social graph and caching at scale](building_blocks/30_social_graph_and_caching_at_scale.md).

</details>

### Q2.4 · L4 — What can a CDN cache, and what can't it?

<details>
<summary>Open the answer</summary>

**Say this first.** Anything identical for many users: static assets, images and video
segments, and public API responses with short TTLs. Not responses that differ per user or
must be fresh — unless you split them into a shared, cacheable part and a small private
part.

**Then explain.**
- Cache keys and `Vary` headers decide what counts as "the same" response.
- Version static files with content hashes in the URL, so they can be cached for a year
  and never need purging.
- Purge or use short TTLs for content that changes; stale-while-revalidate keeps latency
  low during refresh.
- Even uncacheable requests benefit: the edge terminates TCP and TLS near the user and
  keeps warm connections to the origin.

**Next follow-up: "How do you stop a cache miss storm on the origin after a purge?"**
Request collapsing at the edge, an origin shield (a mid-tier cache in front of the
origin), and staggered purges.

**Go deeper.** [CDN and streaming media](building_blocks/29_cdn_and_streaming_media.md) and
[CDN design](problems/036_content_delivery_network_question.md).

</details>

## 3. Scaling Writes and Choosing Storage

### Q3.1 · L4 — SQL or NoSQL for this service?

<details>
<summary>Open the answer</summary>

**Say this first.** Choose from the access patterns and the correctness needs, not from
habit. A relational database for transactions, constraints, joins and flexible queries at
moderate scale; a key-value or wide-column store for simple key lookups at very high write
volume; a document store when data is naturally a self-contained aggregate.

**Then explain.**
- Name the top three queries first, then pick the store that serves them cheaply.
- Relational databases scale further than people assume (replicas, partitioning,
  distributed SQL such as Spanner or CockroachDB).
- NoSQL systems usually give up joins and multi-row transactions — make sure you don't
  need them.
- Many systems use both: a relational source of truth plus derived stores (search index,
  cache, analytics).

**Next follow-up: "Name what you gave up."** For example: "With Cassandra I give up joins
and cross-partition transactions, and I have to model tables per query; that's fine
because every access here is by user ID."

**Go deeper.** [Databases](building_blocks/05_databases.md) and
[database internals](building_blocks/06_database_internals.md).

</details>

### Q3.2 · L4 — Why does consistent hashing use virtual nodes?

<details>
<summary>Open the answer</summary>

**Say this first.** Consistent hashing places nodes and keys on a ring so that adding or
removing a node moves only about 1/N of the keys. Virtual nodes (each server owning many
small points on the ring) even out the load and spread a failed node's keys across all
the others instead of dumping them on one neighbour.

**Then explain.**
- With `hash(key) mod N`, changing N remaps almost every key — a cache wipe or a massive
  data migration.
- With a few points per server, arcs have very uneven sizes; a hundred or so points each
  smooths that out.
- Virtual nodes also let a larger machine take more points, and more load.
- Alternatives: rendezvous (highest-random-weight) hashing, and jump consistent hashing
  when nodes are numbered and only added at the end.

**Next follow-up: "Where do replicas go on the ring?"** On the next N−1 *distinct physical*
nodes clockwise — skipping other virtual nodes of the same server, and ideally in
different racks or zones.

**Go deeper.** [Scaling and load balancing](building_blocks/13_scaling_and_load_balancing.md)
and its consistent-hashing lab.

</details>

### Q3.3 · L5 — How do you choose a shard key, and how do you reshard without downtime?

<details>
<summary>Open the answer</summary>

**Say this first.** Pick the key most queries filter by, that keeps a transaction on one
shard, and that spreads load evenly — usually a tenant or user ID, hashed. Reshard by
splitting into many more logical partitions than machines, then moving whole partitions
while dual-reading or copying and cutting over.

**Then explain.**
- Avoid monotonic keys (timestamps, auto-increment IDs): every write lands on the newest
  shard.
- Queries that don't include the shard key become scatter-gather; add a secondary index
  table or a search index for them.
- Plan for giant tenants: split them further or give them dedicated shards.
- Online move: bulk-copy the partition, stream subsequent changes (CDC), verify, briefly
  pause writes for that partition or use a routing-table switch, then drop the old copy.

**Next follow-up: "A cross-shard transaction is now required. What are your options?"**
Redesign so the data lives together (co-locate by the same key); use a saga with
compensations; or use a database with distributed transactions (Spanner-style) and accept
the latency.

**Go deeper.** [Partitioning and hot keys](building_blocks/25_partitioning_and_hot_keys.md).

</details>

### Q3.4 · L4 — Generate unique IDs across many servers.

<details>
<summary>Open the answer</summary>

**Say this first.** Snowflake-style IDs: a timestamp, a machine ID and a per-machine
sequence packed into 64 bits — unique without coordination and roughly sortable by time.
Or UUIDv7 if 128 bits is fine.

**Then explain.**
- Typical layout: 41 bits of milliseconds (about 69 years), 10 bits of machine ID, 12
  bits of sequence (4,096 IDs per millisecond per machine).
- Machine IDs must be unique: assign them from ZooKeeper or etcd, or derive them from
  the deployment.
- Clock going backwards breaks uniqueness: refuse to issue IDs, or wait, until time
  catches up.
- Random UUIDv4 IDs hurt B-tree index locality; time-ordered IDs don't.

**Next follow-up: "Can users guess other IDs? Does it matter?"** Snowflake IDs are
predictable. That only matters if authorization is missing — never rely on unguessable
IDs as a security control.

**Go deeper.** [Unique ID generator](problems/022_unique_id_generator_question.md).

</details>

## 4. Consistency and Correctness

### Q4.1 · L5 — Strong or eventual consistency — how do you decide, feature by feature?

<details>
<summary>Open the answer</summary>

**Say this first.** Ask what goes wrong if a user sees stale or conflicting data. Money,
inventory, permissions and uniqueness need strong consistency on the write path. Counts,
feeds, recommendations and profiles can be eventually consistent, often with
read-your-writes for the user who made the change.

**Then explain.**
- Mix models inside one product: the like count can lag, the payment cannot.
- Useful middle grounds: read-your-writes, monotonic reads, causal consistency, bounded
  staleness.
- Strong consistency across regions costs a cross-region round trip per write.
- Say it as a trade-off: "Eventual here; the cost is a few seconds of stale counts,
  which users won't notice."

**Next follow-up: "A user changes their password on one device; another region still
accepts the old one for a few seconds. Acceptable?"** No — security state must be
strongly consistent, or at least revoked synchronously everywhere (for example by
invalidating sessions through a strongly consistent store) before the change is
confirmed.

**Go deeper.** [Distributed systems theory](building_blocks/10_distributed_systems_theory.md).

</details>

### Q4.2 · L5 — How do you get "exactly-once" processing?

<details>
<summary>Open the answer</summary>

**Say this first.** You can't get exactly-once *delivery* over a network. You get
exactly-once *effects*: at-least-once delivery plus idempotent processing, or a
transaction that commits the result and the consumer's position together.

**Then explain.**
- Idempotency: deduplicate on a message ID in a processed-IDs table, inside the same
  transaction as the effect; or make the write naturally idempotent (upsert, set).
- Transactional offsets: store the Kafka offset in the same database transaction as the
  output, or use Kafka transactions for read-process-write within Kafka.
- External side effects (sending an email, charging a card) need their own idempotency
  keys at the provider.

**Next follow-up: "Your consumer crashed after writing to the database but before
committing its offset. What happens?"** The message is redelivered; the processed-IDs
check (or the idempotent write) makes the second attempt a no-op.

**Go deeper.** [Messaging and streaming](building_blocks/09_messaging_and_streaming.md) and
[ad click aggregation](problems/027_ad_click_aggregation_question.md).

</details>

### Q4.3 · L5 — Prevent two people from booking the same seat.

<details>
<summary>Open the answer</summary>

**Say this first.** Make the database enforce it: a conditional update
(`UPDATE seats SET holder = ?, hold_until = ? WHERE id = ? AND (holder IS NULL OR
hold_until < now())`) or a unique constraint, so exactly one writer wins. Hold the seat
briefly during checkout, then confirm or release it.

**Then explain.**
- Check-then-write in application code races; the atomic conditional write doesn't.
- Temporary holds with expiry prevent abandoned checkouts from locking seats forever.
- For extremely hot events, put a queue or virtual waiting room in front, and shard
  inventory by section.
- Idempotency keys on "confirm" make payment retries safe.

**Next follow-up: "Why not a distributed lock?"** A lock service adds a dependency, and a
paused lock holder can still write after its lease expires unless storage checks a
fencing token. The database's own atomic write is simpler and correct.

**Go deeper.** [Seat reservation](problems/010_seat_reservation_question.md) and
[transactions and concurrency](building_blocks/11_transactions_and_concurrency.md) with its
isolation lab.

</details>

### Q4.4 · L5 — Explain quorums: why does R + W > N give consistency?

<details>
<summary>Open the answer</summary>

**Say this first.** With N replicas, a write goes to W of them and a read asks R. If
R + W > N, every read set overlaps every write set in at least one replica, so the read
sees the latest acknowledged write (using version numbers to pick it).

**Then explain.**
- Typical choice: N = 3, W = 2, R = 2. W = 1 favours write latency; R = 1 favours reads.
- It isn't full linearizability: sloppy quorums, hinted handoff, concurrent writes and
  clock-based conflict resolution can still produce stale or lost updates.
- Read repair and anti-entropy (Merkle trees) bring lagging replicas up to date.

**Next follow-up: "Two clients write the same key concurrently. Which wins?"** With
last-writer-wins, whichever has the later timestamp — silently dropping the other. To
keep both, use version vectors and return siblings for the application to merge, or use
CRDTs.

**Go deeper.** [Consensus and coordination](building_blocks/19_consensus_and_coordination.md)
and the quorum and logical-clock labs.

</details>

## 5. Asynchronous Work: Queues and Streams

### Q5.1 · L4 — A message queue or a log (RabbitMQ or Kafka)?

<details>
<summary>Open the answer</summary>

**Say this first.** A queue hands each message to one consumer and deletes it once
acknowledged: good for task distribution with per-message retries. A log keeps an ordered,
replayable record; consumers track their own offsets, so many independent consumers can
read the same stream and replay history.

**Then explain.**
- Log strengths: ordering per partition, replay, very high throughput, event sourcing and
  CDC.
- Queue strengths: per-message acknowledgement, routing, delays and priorities, simple
  work distribution.
- In a log, a single slow or poison message blocks its partition unless you move it
  aside.

**Next follow-up: "You need to reprocess the last week's events with a bug fix. Which one
helps?"** The log: reset the consumer group's offsets (or start a new group) and replay,
provided retention covers a week.

**Go deeper.** [Messaging and streaming](building_blocks/09_messaging_and_streaming.md) and
[distributed log internals](building_blocks/26_distributed_log_internals.md).

</details>

### Q5.2 · L5 — What ordering can you guarantee, and at what cost?

<details>
<summary>Open the answer</summary>

**Say this first.** Per key, not globally. Partition by the entity ID so all of an
entity's events go to one partition, where order holds. Global order means one
partition — one consumer — which caps throughput.

**Then explain.**
- Order also requires one producer path per key, no reordering on retry (Kafka's
  idempotent producer), and in-order processing on the consumer side.
- Adding partitions changes which partition a key maps to; in-flight order can break
  during the change.
- Consumers should tolerate out-of-order and duplicate delivery anyway, using versions or
  sequence numbers.

**Next follow-up: "One user generates 30% of events. What now?"** That partition becomes a
hot spot. Split the user's events by a sub-key where order across them doesn't matter,
or give the partition's consumer more capacity; accept that true per-key order limits
that key's throughput.

**Go deeper.** [Distributed log internals](building_blocks/26_distributed_log_internals.md)
and its partitions lab.

</details>

### Q5.3 · L4 — How do you handle a message that always fails?

<details>
<summary>Open the answer</summary>

**Say this first.** Retry a limited number of times with backoff, then move it to a
dead-letter queue with its error, alert on the DLQ, and keep processing the rest. Fix the
cause and replay from the DLQ.

**Then explain.**
- Separate transient failures (timeouts) from permanent ones (bad data): don't retry
  permanent failures.
- In ordered logs, a poison message blocks its whole partition — that's why moving it
  aside matters.
- Make the replay path idempotent.

**Next follow-up: "What do you alert on?"** DLQ growth, consumer lag (and its rate of
change), and processing error rate — not individual failures.

**Go deeper.** [Notification platform](problems/004_notification_platform_question.md) and
the Kafka lab in [messaging](building_blocks/09_messaging_and_streaming.md).

</details>

### Q5.4 · L5 — News feed: fan-out on write or fan-out on read?

<details>
<summary>Open the answer</summary>

**Say this first.** Fan-out on write (push each post into every follower's precomputed
timeline) makes reads cheap and suits the read-heavy common case. Fan-out on read (merge
followees' posts at request time) avoids huge write amplification for accounts with
millions of followers. Real systems do both: push for most users, pull for celebrities.

**Then explain.**
- Push cost = posts × average followers; it explodes for celebrities and wastes work on
  inactive followers.
- Pull cost = timeline reads × followees; it's expensive at read time and hard to rank.
- Hybrid: store timelines in a cache as ID lists, push for normal accounts, merge in
  celebrity posts at read time, skip inactive users.
- Ranking usually happens at read time over a candidate set.

**Next follow-up: "How big are the timeline caches?"** For example 300 million active
users × 800 post IDs × 8 bytes ≈ 2 TB — spread across a cache cluster, with only IDs
stored and posts hydrated from a separate cache.

**Go deeper.** [News feed](problems/007_news_feed_question.md) and
[ranked home feed](problems/032_ranked_home_feed_question.md).

</details>

## 6. Reliability and Operations

### Q6.1 · L5 — How would you design for 99.99% availability?

<details>
<summary>Open the answer</summary>

**Say this first.** 99.99% is about 52 minutes of downtime a year, so no single human
response or single-zone failure can fit in the budget. Remove single points of failure
across zones, make failover automatic and tested, turn non-critical dependencies into
soft ones, and deploy progressively with automatic rollback.

**Then explain.**
- Availability multiplies along hard dependencies in series: five components at 99.9%
  give about 99.5%.
- Redundancy helps only when copies fail independently (different zones, not the same
  rack) and failover is automatic.
- Most outages come from changes: canaries, feature flags, fast rollback.
- Shorten detection and recovery: good alerts, runbooks, and automated remediation.

**Next follow-up: "The database is a single primary. Can you still reach four nines?"**
Only with automatic failover to a synchronous standby in another zone, fast detection,
and clients that reconnect quickly; otherwise every primary failure costs minutes you
don't have.

**Go deeper.** [Observability and reliability](building_blocks/15_observability_and_reliability.md)
with its availability lab.

</details>

### Q6.2 · L6+ — Active-active or active-passive across regions?

<details>
<summary>Open the answer</summary>

**Say this first.** Active-passive is simpler: one region takes writes, the other stands
by, and you accept some data loss and minutes of failover. Active-active serves users
from both regions for lower latency and near-instant failover, but you must handle
conflicting writes or route each user's writes to a home region.

**Then explain.**
- Decide from RPO and RTO targets, write latency requirements, and data sovereignty.
- Active-active options: home-region per user (writes go to one region, reads anywhere);
  conflict-free data types; or a globally consistent database (Spanner-style) paying a
  cross-region round trip per write.
- Failover must be rehearsed; capacity in each region must absorb the other's traffic.
- Watch out for hidden single-region dependencies (auth, config, DNS control plane).

**Next follow-up: "Your 'standby' region hasn't taken traffic in a year. Will failover
work?"** Probably not cleanly: stale configs, missing capacity and untested runbooks. Run
regular failover drills, or keep it taking a slice of real traffic.

**Go deeper.** [Multi-region and global traffic](building_blocks/27_multi_region_and_global_traffic.md).

</details>

### Q6.3 · L5 — Traffic doubles in five minutes. How does your system avoid collapsing?

<details>
<summary>Open the answer</summary>

**Say this first.** Latency rises steeply as utilisation nears 100%, and queues plus
client retries can turn an overload into a collapse. Shed or throttle excess load early,
bound every queue, limit retries, degrade non-critical features, and let autoscaling
catch up.

**Then explain.**
- Admission control at the edge: rate limits and priority-based shedding (drop
  best-effort traffic first).
- Adaptive concurrency limits keep each service near its best throughput.
- Deadlines: drop work whose caller has already given up.
- Retry budgets and circuit breakers stop retry storms.
- Graceful degradation: serve cached or simplified responses, hide optional widgets.
- Autoscaling lags by minutes; keep headroom (scale out around 60–70% utilisation).

**Next follow-up: "Why scale at 60–70% and not 90%?"** With random arrivals, waiting time
grows roughly with 1/(1 − utilisation): at 90% a single server's responses take about 10×
the service time, at 70% about 3×. Headroom also covers the minutes autoscaling needs.

**Go deeper.** [Overload control](building_blocks/28_overload_control_and_graceful_degradation.md)
and the queueing lab there.

</details>

### Q6.4 · L4 — What do you monitor, and what pages someone at 3 a.m.?

<details>
<summary>Open the answer</summary>

**Say this first.** Monitor the four golden signals — latency, traffic, errors,
saturation — for every service, and page only on symptoms users feel: SLO burn rate on
success rate and latency. Everything else is a dashboard or a ticket.

**Then explain.**
- Latency as percentiles (p50, p99), never averages.
- Saturation: queue depths, pool usage, consumer lag, disk and memory headroom.
- Alerts must be actionable, with a runbook link.
- Traces show which hop is slow; logs explain why.

**Next follow-up: "Your p99 doubled but p50 didn't move. What does that tell you?"**
Something affects a minority of requests: a slow dependency on some paths, one bad
host, GC pauses, cache misses for some keys, or contention. Break the p99 down by host,
endpoint and dependency.

**Go deeper.** [Observability and reliability](building_blocks/15_observability_and_reliability.md).

</details>

## 7. Real-Time, Rate Limits and Specialised Structures

### Q7.1 · L4 — WebSockets, server-sent events, or long polling?

<details>
<summary>Open the answer</summary>

**Say this first.** WebSockets for two-way, low-latency traffic (chat, collaboration,
games); server-sent events for one-way server-to-client streams over plain HTTP (live
scores, notifications); long polling as a fallback where nothing else works.

**Then explain.**
- Persistent connections are stateful: you need to know which server holds which user
  (a presence or connection registry) and to route messages there (pub/sub).
- Load balancers must support long-lived connections; deploys must drain them gently.
- Clients reconnect with backoff and resume from a sequence number so nothing is lost.

**Next follow-up: "A gateway server holding 500,000 connections restarts. What
happens?"** Half a million clients reconnect at once — a thundering herd. Add jittered
reconnect backoff, drain servers gradually before a deploy, and size the connection
registry and authentication path for reconnect storms.

**Go deeper.** [Real-time and collaboration](building_blocks/22_realtime_and_collaboration.md)
and [chat](problems/006_chat_question.md).

</details>

### Q7.2 · L4 — Design a rate limiter. Which algorithm, and where does it run?

<details>
<summary>Open the answer</summary>

**Say this first.** A token bucket per client (it allows short bursts and enforces the
average rate), checked at the gateway, with counters in a fast shared store such as Redis
and the check-and-decrement done atomically in one script.

**Then explain.**
- Fixed windows allow double bursts at the window edge; sliding-window counters fix that
  cheaply; sliding logs are exact but memory-hungry.
- Distributed counting: a central store adds a network hop; local limits plus periodic
  synchronisation are cheaper but approximate.
- Decide what happens when the limiter's store is down (fail open for most traffic, fail
  closed for abuse-sensitive endpoints).
- Return 429 with `Retry-After`.

**Next follow-up: "Enforce a global limit across five regions."** Exact global limits need
cross-region coordination per request — too slow. Split the quota across regions and
rebalance periodically, accepting slight overshoot.

**Go deeper.** [Rate limiter](problems/002_rate_limiter_question.md) and the algorithms lab
in [low-level API design](building_blocks/04_api_design_low_level.md).

</details>

### Q7.3 · L5 — Find the restaurants within 2 km of a user, fast.

<details>
<summary>Open the answer</summary>

**Say this first.** Index locations with a spatial scheme — geohash, S2 or H3 cells, or a
quadtree — look up the user's cell and its neighbours, then filter the candidates by exact
distance and rank them.

**Then explain.**
- Cell sizes are chosen so a query touches a few cells; always include neighbours, because
  a nearby point can sit just across a cell boundary.
- Static data (restaurants) goes in a read-optimised index, replicated widely; moving data
  (drivers) goes in an in-memory index updated every few seconds.
- Dense cities need smaller cells or adaptive structures (quadtrees split crowded cells).

**Next follow-up: "Drivers update their location every four seconds. What changes?"**
Writes dominate: keep locations in memory, sharded by cell, with a short TTL; don't
persist every update synchronously.

**Go deeper.** [Nearby places](problems/026_nearby_places_question.md),
[ride dispatch](problems/020_ride_dispatch_question.md), and the geospatial lab in
[specialized data structures](building_blocks/20_specialized_data_structures.md).

</details>

## 8. Staff-Level Scenarios

### Q8.1 · L6+ — Move a live service to a new datastore with zero downtime.

<details>
<summary>Open the answer</summary>

**Say this first.** Migrate in reversible steps: dual-write (or stream changes) to the new
store, backfill history, verify with shadow reads and comparisons, shift reads gradually,
then make the new store the source of truth, and keep the old one as a fallback until
you're sure.

**Then explain.**
1. Put an abstraction around data access so the switch is one place.
2. Stream changes with CDC (safer than application dual-writes, which can diverge).
3. Backfill existing data idempotently, then catch up from the change stream.
4. Shadow-read: serve from the old store, read the new one too, and log mismatches.
5. Ramp reads by percentage; flip writes; reverse the change stream so the old store stays
   current for rollback.
6. Decommission only after a quiet period.
- Each step has a metric that decides whether to proceed and a documented rollback.

**Next follow-up: "What's the riskiest step?"** Flipping the source of truth for writes —
the point after which rolling back needs the reverse sync to be correct. Rehearse it on a
small slice of traffic first.

**Go deeper.** [Platform and infra](building_blocks/16_platform_and_infra.md) and
[decision framework](building_blocks/17_decision_framework.md).

</details>

### Q8.2 · L6+ — Traffic will grow 10× in six months. How do you plan?

<details>
<summary>Open the answer</summary>

**Say this first.** Find what breaks first. Load-test to find each component's ceiling,
rank the bottlenecks by how soon growth hits them, fix the nearest ones, and design the
changes that need long lead times (sharding, multi-region, vendor contracts) now.

**Then explain.**
- Model growth per component: request rates, storage, fan-out, connection counts — they
  don't all grow at the same rate.
- Stateless tiers usually scale out easily; the database, hot keys, queues and third-party
  quotas are typical ceilings.
- Improve efficiency before adding hardware where it is cheap (caching, batching, better
  queries).
- Budget capacity and cost, and set milestones with a test that proves each one.

**Next follow-up: "What would you not change?"** Anything that isn't a bottleneck at 10×
— premature rewrites add risk without benefit. Say what you are deliberately leaving
alone.

**Go deeper.** [Scaling and load balancing](building_blocks/13_scaling_and_load_balancing.md)
and [back-of-envelope estimation](building_blocks/18_back_of_envelope_estimation.md).

</details>

### Q8.3 · L6+ — Build it or buy it?

<details>
<summary>Open the answer</summary>

**Say this first.** Buy (or use managed services) for anything that isn't a
differentiator and has a mature market; build when the capability is core to the product,
when requirements are unusual, or when scale makes vendor cost or limits unacceptable.

**Then explain.**
- Count total cost: engineering time to build *and* to operate for years, on-call, and
  opportunity cost — against licence or usage fees.
- Check lock-in and exit paths, data residency, and the vendor's reliability record.
- Revisit as scale changes: many companies start managed and bring components in-house
  later, or the reverse.

**Next follow-up: "Your team wants to build its own queue. Convince me."** Only with a
requirement no existing system meets (measured, not assumed) and a team that can run it
around the clock; otherwise use Kafka, a managed queue, or the cloud's pub/sub.

**Go deeper.** [Decision framework](building_blocks/17_decision_framework.md).

</details>

## 9. How the Same Problem Is Graded at Each Level

The prompt doesn't change with the level; the expected answer does. Use this table to
check which rows your answer covers.

| Problem | L4 · Mid covers | L5 · Senior adds | L6+ · Staff adds |
|---|---|---|---|
| **URL shortener** | API, key generation, a table, a cache, redirects | Collision-free ID strategy compared, cache hit-rate numbers, hot links, abuse and expiry | Multi-region reads, analytics pipeline separation, custom domains, cost per billion redirects |
| **Rate limiter** | Token bucket, Redis counter, 429 | Algorithm comparison, atomic script, limiter outage policy, per-tenant rules | Global quotas across regions, fairness between tenants, the limiter as a shared critical dependency |
| **News feed** | Posts table, follow graph, timeline cache | Push vs pull with numbers, celebrity hybrid, ranking stage, pagination | Ranking and experimentation platform, cost of fan-out, privacy and deletion propagation |
| **Chat** | WebSockets, message store, delivery | Connection registry, ordering per conversation, offline delivery, receipts | Multi-device sync, end-to-end encryption, regional data residency, reconnect storms |
| **Payments / checkout** | Order and payment tables, provider call | Idempotency keys, state machine, saga with compensations, reconciliation | Ledger correctness guarantees, audit, multi-provider routing, regulatory constraints |
| **Distributed cache** | Consistent hashing, eviction | Replication, hot keys, stampedes, failure of a node | Multi-tenant isolation, cross-region consistency, capacity planning and cost |

## 10. Rapid Fire

| Question | One-sentence answer |
|---|---|
| What is a load balancer's job? | Spread requests across healthy servers and stop sending traffic to unhealthy ones. |
| Vertical vs horizontal scaling? | Bigger machines vs more machines; horizontal scales further but needs stateless design or partitioning. |
| What is a read replica for? | Offloading reads from the primary, at the cost of replication lag. |
| What is a CDN? | A network of edge caches close to users that serves content without a trip to the origin. |
| What is sharding? | Splitting data across machines by a key so each holds and serves a subset. |
| What is a hot key? | One key receiving so much traffic that its single owner becomes the bottleneck. |
| What is a message queue for? | Decoupling producers from consumers and absorbing bursts of work. |
| What is idempotency for? | Making retries safe by ensuring a repeated request has no extra effect. |
| What is a circuit breaker? | A switch that fails calls fast to a dependency that is failing, then probes for recovery. |
| What is backpressure? | Slowing producers when consumers can't keep up instead of queueing without limit. |
| What is an SLO? | A target for a user-facing reliability measure, such as 99.9% of requests succeeding. |
| What is an error budget? | The amount of unreliability the SLO allows, spent on risk such as releases. |
| What is a Bloom filter used for in storage? | Skipping reads of files that definitely don't contain a key. |
| What is consistent hashing? | A key-to-node mapping where adding a node moves only about 1/N of the keys. |
| What is a quorum? | The minimum number of replicas that must acknowledge an operation for it to count. |
| What is a leader lease? | A time-limited right to act as leader, so a new one can be chosen safely if it goes silent. |
| What is a fencing token? | An increasing number attached to a lock grant so storage can reject stale holders. |
| What is CDC? | Change data capture: streaming a database's committed changes out of its log. |
| What is the outbox pattern? | Writing an event in the same transaction as the data, then publishing it asynchronously. |
| What is tail latency? | The slowest requests (p99 and above), which dominate when a request fans out to many servers. |

## 11. Failure Modes, Measured

Each question here comes with a simulation in the building block it links to, so the numbers in
the answers are ones you can reproduce.

### Q11.1 · L5 — You switched the load balancer to least-connections and a quarter of requests started failing. How?

<details>
<summary>Open the answer</summary>

**Say this first.** One backend is failing *fast*. A backend that returns an error in a
millisecond always has the fewest outstanding requests, so a load-aware balancer keeps choosing
it — the "black hole" effect. Round robin would have sent it only its 1/N share.

**Then explain.**
- In the simulation, one fast-failing backend of ten received 26% of traffic under
  least-outstanding and 17% under power-of-two-choices, versus 10% with round robin.
- The fix is outlier ejection on real traffic: after N consecutive errors (or an error-rate
  threshold), remove the backend for a while and probe it again. Errors fell to 0.03%.
- Cap the fraction of the pool that can be ejected, so a shared-dependency failure can't eject
  everyone.

**Next follow-up: "Then why not just use round robin?"** Because with uneven request costs or a
*slow* backend, round robin is far worse: it keeps a 5× slower backend at 10% of traffic, its queue
grows without bound, and p99 goes to minutes. Load-aware balancing plus ejection handles both.

**Go deeper.** [Scaling and load balancing](building_blocks/13_scaling_and_load_balancing.md), *Balancing algorithms, measured*.

</details>

### Q11.2 · L5 — A 20-second traffic spike took the service down, and it stayed down after traffic returned to normal. Why?

<details>
<summary>Open the answer</summary>

**Say this first.** A metastable failure sustained by retries. During the spike, requests time out;
clients retry them; the retries keep offered load above capacity after the spike ends, and the
server spends all its capacity on requests whose clients have already given up — so goodput stays at
zero.

**Then explain.**
- Simulated: capacity 1,000/s, normal load 800/s, three retries per timed-out request. After the
  spike the offered load was 1,730/s and goodput 0 for over two minutes.
- Exponential backoff with jitter did **not** help: it spreads retries in time but doesn't reduce
  their number.
- What worked: a retry budget (retries ≤ 10% of new requests) recovered; servers dropping requests
  whose deadline had passed never degraded at all.

**Next follow-up: "What else would you add?"** Load shedding at the edge before queues grow, circuit
breakers, deadline propagation on every hop, and retries at one layer only — three layers retrying
three times each is 64 attempts per failure.

**Go deeper.** [Application resilience](building_blocks/12_application_resilience_patterns.md), *Retry storms, measured*.

</details>

### Q11.3 · L5 — A consumer group was down for 10 minutes on a 1,000 msg/s stream. How long until it catches up?

<details>
<summary>Open the answer</summary>

**Say this first.** Backlog ÷ headroom, not backlog ÷ capacity. The backlog is 600,000 messages; if
consumers can do 1,250/s, only 250/s goes to the backlog, so catching up takes 40 minutes. With 10%
headroom it takes 100 minutes.

**Then explain.**
- While draining, consumers must also keep up with new messages.
- The oldest message is 10 minutes old at restart and stays old for most of the drain, so alert on
  lag in seconds, not only on message counts.
- Parallelism is capped by the partition count; adding consumers beyond it does nothing.
- Retention must exceed the worst detection-plus-recovery time, or messages are deleted unread.

**Next follow-up: "How would you speed up recovery right now?"** Scale consumers up to the partition
count, defer low-priority processing, batch more aggressively, and only if necessary skip to recent
offsets for data that has lost its value — recording what was skipped.

**Go deeper.** [Messaging and streaming](building_blocks/09_messaging_and_streaming.md), *Lag, backlog, and catch-up time*.

</details>

### Q11.4 · L5 — Keys are hash-partitioned evenly across 16 shards, yet one shard runs at more than twice the average load. Why?

<details>
<summary>Open the answer</summary>

**Say this first.** Hashing spreads *keys* evenly, not *load*. With skewed (Zipf-like) popularity, one
key can carry more traffic than a whole shard's fair share — here the hottest key alone was 8.3% of
requests against a fair share of 6.25%.

**Then explain.**
- Detect hot keys with a count-min sketch or top-K per shard.
- Hot reads: replicate the key across cache nodes, cache in-process for a second.
- Hot writes: split the key into sub-keys (`key#0..key#7`) and merge on read. Splitting only the top
  10 keys took the busiest shard from 2.3× to 1.3× the mean.
- Reads of split keys fan out, so split only detected hot keys.

**Next follow-up: "Would more shards fix it?"** No: the hot key still lives on one shard. More shards
lower the average, which makes the hot shard's *relative* imbalance worse.

**Go deeper.** [Partitioning and hot keys](building_blocks/25_partitioning_and_hot_keys.md), *Skewed load, measured*.

</details>

### Q11.5 · L5 — A page fans out to 100 backends in parallel. Each backend is fast except for 1% of calls. What latency do users see, and how do you fix it?

<details>
<summary>Open the answer</summary>

**Say this first.** The page waits for the slowest call, and 1 − 0.99¹⁰⁰ = 63% of pages hit at least
one slow call — so the *median* page is as slow as the backends' tail. Fix it with hedged requests:
after a call exceeds about its p95, send a second copy to another replica and take the first answer.

**Then explain.**
- Simulated with 10 ms calls and a 1% ~150 ms tail: 100-way fan-out had a 138 ms median.
- Hedging after 15 ms brought p99 from 179 ms to 31 ms for about 1.6% extra backend calls.
- Hedges must be idempotent reads, and capped so they can't become a retry storm under overload.

**Next follow-up: "What else reduces fan-out tail?"** Fewer, larger shards; answering with partial
results after a deadline (search often does); and fixing the backend tail itself (GC, cold caches).

**Go deeper.** [Application resilience](building_blocks/12_application_resilience_patterns.md), *Tail latency at scale*.

</details>

### Q11.6 · L5 — A service in Kubernetes averages 0.2 cores with a 0.25-core limit, yet its p99 is ten times its median. Why?

<details>
<summary>Open the answer</summary>

**Say this first.** CPU limits are enforced per 100 ms period. A request that needs 40 ms of CPU
across four threads burns the container's 25 ms quota in a few milliseconds, then every thread is
frozen until the next period: 10 ms becomes about 104 ms, at low *average* CPU.

**Then explain.**
- The metric that shows it is CPU throttling (`container_cpu_cfs_throttled_periods_total`), not usage.
- Set CPU requests accurately; be cautious with CPU limits on latency-sensitive services; always set
  memory limits.
- Match the runtime to the limit (`GOMAXPROCS`, JVM processor count), or it starts one thread per host
  core and burns the quota in parallel.

**Next follow-up: "And a memory limit?"** It can't throttle: exceeding it gets the container killed
(exit code 137).

**Go deeper.** [Platform and infrastructure](building_blocks/16_platform_and_infra.md), *CPU limits and throttling, worked*.

</details>

### Q11.7 · L6+ — A 0.1% canary ran for 10 minutes with no alarms. Ship to everyone?

<details>
<summary>Open the answer</summary>

**Say this first.** Not on that evidence. At 0.1% of 2,000 requests/s the canary saw about 1,200
requests; a doubled error rate (0.5% → 1.0%) took a median of 16.5 minutes to detect in simulation,
so silence at 10 minutes means little.

**Then explain.**
- Step the traffic (1% → 5% → 25% → 50%) with a bake time sized to the traffic at each step.
- Compare against a baseline cohort of the old version running at the same time.
- Watch several signals — errors, latency percentiles, saturation, business metrics.
- Use tests designed for continuous monitoring: checking a naive z-test every 10 seconds for hours
  produces false alarms (3 in 40 runs at 0.1%).

**Next follow-up: "What can a canary never catch?"** Problems that only appear at full load, data
changes that aren't backward compatible across versions, and slow-burn issues (leaks) — which is
why rollback plans and schema compatibility are separate requirements.

**Go deeper.** [Platform and infrastructure](building_blocks/16_platform_and_infra.md), *Rollouts, and how long a canary must run*.

</details>

### Q11.8 · L5 — A gateway holding 200,000 WebSocket connections restarts. What happens next?

<details>
<summary>Open the answer</summary>

**Say this first.** All 200,000 clients reconnect at once. If they retry on a fixed short timer, the
wave can exceed the fleet's handshake capacity every second and never recover, because refused TLS
handshakes still burn CPU.

**Then explain.**
- Modelled with a fleet completing 20,000 handshakes/s: synchronised retries never recovered;
  jittered backoff recovered in 21 s; server-paced reconnects in 15 s with nothing refused.
- Drain gateways one at a time, send clients a randomised reconnect delay, cap backoff, keep TLS
  session resumption on.
- Clients catch up from the durable log using their last acknowledged sequence number.

**Next follow-up: "How do you deploy a fleet of connection gateways safely?"** One gateway at a time,
draining slowly (clients reconnect elsewhere at a controlled rate), with capacity headroom for the
largest gateway's connections.

**Go deeper.** [Real-time and collaboration](building_blocks/22_realtime_and_collaboration.md), *Reconnect storms, modelled*.

</details>

### Q11.9 · L5 — Users report that an export of their orders is missing some rows, though every page request succeeded. What happened?

<details>
<summary>Open the answer</summary>

**Say this first.** Offset pagination over data that changed during the export. When rows before
the current offset are deleted, every later row shifts up, and the next page starts past rows the
client never saw. Inserts do the opposite and repeat rows.

**Then explain.**
- Measured on a million rows: 7 deletions between each of 5 page requests silently skipped 28 rows;
  7 inserts produced 28 duplicates. A keyset cursor had neither problem.
- Offset is also slow deep in a list: page 19,999 took hundreds of times longer than page 1,
  because the database walks past every skipped row.
- Fix: an opaque cursor encoding the last `(sort key, id)`, with `id` as a tiebreaker because
  sort keys have ties.

**Next follow-up: "The product needs 'jump to page 40'."** Offer filters and date ranges instead,
or accept offset only for shallow pages and cap the depth. Exports should use cursors or a
snapshot (an export job writing a file from one consistent read).

**Go deeper.** [API design, high level](building_blocks/03_api_design_high_level.md), *Pagination, measured*.

</details>

### Q11.10 · L5 — How can three-way replication be less durable than a scheme that stores only 1.4× the data?

<details>
<summary>Open the answer</summary>

**Say this first.** Erasure coding. RS(10,4) splits an object into 10 data pieces plus 4 parity
pieces, any 10 of which rebuild it. It survives any 4 simultaneous losses at 1.4× storage, while 3
replicas survive only 2 at 3×.

**Then explain.**
- In a model with 2% annual disk failures and 24-hour repair, 3 replicas lose about 2 × 10⁻¹⁰ of
  objects a year; RS(10,4) about 2 × 10⁻¹⁵.
- Repair time matters as much as the scheme: stretching repair from a day to a week made 3 replicas
  about 50× more likely to lose data.
- Placement across failure domains is what makes the independence assumption true: RS(10,4) with
  5 pieces per rack becomes unreadable when one rack goes down.
- The costs: reads touch 10 nodes, and repair reads 10 pieces to rebuild one.

**Next follow-up: "So is the data safe?"** Not from correlated events: bugs, bad deploys, deleted
buckets. Versioning, delete protection and a copy in another account or region cover those.

**Go deeper.** [Object storage](building_blocks/08_object_storage.md), *Durability: replication vs erasure coding, modelled*.

</details>

### Q11.11 · L5 — A streaming job counts clicks per minute, and billing says the counts are 2% too high. Where do the extra clicks come from?

<details>
<summary>Open the answer</summary>

**Say this first.** Duplicates the pipeline can't see as duplicates. Checkpointing state and
offsets together gives exactly-once *processing*, but a client that retried a click after a
timeout sent two different events for one click. Only deduplication by a client-generated event
ID removes those.

**Then explain.**
- Simulated with 12 crashes and 2% client retries: at-least-once overcounted by 8%; checkpointed
  exactly-once by exactly the 2% of retries; checkpointing plus dedup by event ID was exact.
- Dedup state is kept per key with an expiry (a day, say), not forever.
- The sink must be idempotent too (upsert by `(ad, minute)`), or replays after a failure add again.

**Next follow-up: "And late clicks?"** A watermark decides when a minute is reported; allowed
lateness emits corrections; the daily batch job over raw logs is authoritative for billing, with a
reconciliation report against the stream.

**Go deeper.** [Batch and stream processing](building_blocks/21_batch_and_stream_processing.md), *Delivery semantics, measured* and *Watermarks, measured*.

</details>

### Q11.12 · L5 — A model scored 0.92 AUC offline and does much worse in production. Nothing errored. What do you check?

<details>
<summary>Open the answer</summary>

**Say this first.** Leakage and training-serving skew. Leakage: training features were joined as
of today rather than as of the prediction time, so they contain the answer. Skew: production
computes the features differently, so the model sees different values than it was trained on.

**Then explain.**
- Simulated: a leaky "purchases in the last 4 weeks" join showed AUC 0.92 offline; the honest,
  point-in-time value was 0.69, and that is the best production can achieve.
- A real-time counter that missed late-recorded purchases then cut recall from 33% to 21%, with
  identical code and model.
- Fixes: point-in-time joins, one feature definition for both stores, log served features and train
  on them, and monitor served feature distributions against training.

**Next follow-up: "How would you have caught it before launch?"** Compare served feature
distributions in shadow traffic with the training data, and be suspicious of any offline gain that
looks too good. The A/B test is the final check.

**Go deeper.** [ML and LLM systems](building_blocks/23_ml_and_llm_systems.md), *Leakage and training-serving skew, measured*.

</details>

### Q11.13 · L5 — An LLM endpoint's GPUs are fully loaded, yet users wait many seconds for the first token. What would you change first?

<details>
<summary>Open the answer</summary>

**Say this first.** Check the batching. With static batching, a batch runs until its longest
generation finishes, so finished sequences hold their slots and new requests wait for the whole
batch. Continuous batching admits new requests at every decode step.

**Then explain.**
- Simulated with outputs of 20–1,000 tokens: at the same load, static batching's median time to
  first token was 7–15 s and its throughput capped near 560 tokens/s; continuous batching served
  2.5× more tokens with first tokens in tens of milliseconds.
- Then check memory: the KV cache (128 KB per token for an 8B model) limits how many sequences can
  run at once; PagedAttention and prefix caching raise that limit.
- Chunk or separate long prefills so one long prompt doesn't stall everyone's decoding.

**Next follow-up: "And to cut cost?"** Prefix-cache the shared system prompt, route easy requests
to a smaller model, cap output tokens, and trim retrieved context.

**Go deeper.** [ML and LLM systems](building_blocks/23_ml_and_llm_systems.md), *Static vs continuous batching, measured* and *LLM serving arithmetic*.

</details>

## Keep Going

- Missed a question? Follow its **Go deeper** link, then retest it cold tomorrow.
- Practise the full 45-minute format on the [practice problems](02_problem_catalog.md);
  each has a timed coach.
- For the CS foundations these answers rest on — operating systems, networking,
  databases, concurrency — use the CS Fundamentals question bank
  ([Interview Question Bank — Every Topic, Every Level](../CSFundamentals/12_interview_question_bank_deep_dive.md)).
