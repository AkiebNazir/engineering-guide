# Decision Framework

This is the capstone file for the `building_blocks/` module. Everything else here taught what a component is and when it earns its place; this file is the translation machinery — how to go from an ambiguous prompt to a defensible set of choices, out loud, in an interview. Read it last.

## Start from a requirement, not a tool

Every good design decision traces back to a stated requirement, not to a component you wanted to use. Use this table as the mental move before drawing anything:

| Requirement | Property needed | Typical building block | Cost/trade-off |
|---|---|---|---|
| Users worldwide see images quickly. | Geography-aware cached delivery. | CDN + object storage. | Cache invalidation/access control and egress cost. |
| A user can safely retry "place order." | Duplicate suppression. | Idempotency key + DB uniqueness/record. | Extra state and key-retention policy. |
| Sending email must not delay checkout. | Decoupled background work. | Outbox + queue/stream + worker. | Eventual completion, retry/DLQ/replay design. |
| Product page is read far more than written. | Avoid repeated source reads. | Cache-aside cache. | Staleness and stampedes. |
| One service is slow. Others should still work. | Isolation and fast failure. | Timeouts, bulkheads, circuit breaking, queues. | Fallback behavior and capacity planning. |
| A single DB node cannot hold/write all the data. | Horizontal distribution. | Partition/shard strategy. | Routing, hot keys, rebalancing, cross-shard queries. |
| Need 99.9% user success. | Redundancy, controlled failure, measurement. | Multi-instance service, backups/replication, SLOs. | Cost and more operational complexity. |

## The interview-quality trade-off sentence

Every component you introduce should be justified in this exact shape, said out loud:

> "I use **X** to get **property Y** for **requirement Z**; the cost is **C**, which I accept because **reason**."

If you cannot fill in all five blanks for a component you just drew on the whiteboard, you have not actually justified it — you have decorated the diagram. This sentence is also the fastest way to catch yourself reaching for a tool (Kafka, Kubernetes, a graph database) before naming the requirement it serves.

## Decision worksheet

Fill this before choosing components, on any prompt, real or interview:

```text
User action:
Success condition / invariant:
Peak read QPS / write QPS / payload / retention:
Latency & availability SLO:
Source of truth:
Reads that may be stale (and allowed delay):
Async work:
Idempotency key / duplicate behavior:
Ordering required (global, per-key, none):
Failure/degradation plan:
Security/tenant/privacy constraints:
Signals / alerts / RPO / RTO:
First scale trigger and evolution:
```

Every blank maps to a file in this module: "source of truth" and "idempotency key" pull from `05_databases.md` and `03_api_design_high_level.md`; "ordering required" pulls from `10_distributed_systems_theory.md`; "security/tenant/privacy" pulls from `14_security.md`; "signals/alerts/RPO/RTO" pulls from `15_observability_and_reliability.md`. The worksheet is the whole module compressed into one page you can fill in under interview time pressure.

## Interview decision tree

When given any unfamiliar prompt, walk this tree in order — do not skip to "which database" before the first two questions are answered:

```text
What is the user-visible action and success invariant?
  |
What volume, object size, latency, availability, geography, and privacy matter?
  |
Can one modular service + relational DB meet the launch need?
  +-- yes -> use it; add cache/async processing only for clear, stated pressure.
  +-- no  -> identify the exact limit: read, write, bytes, fanout, latency,
             isolation, or correctness.
                |
             Which component directly solves that limit, and what new
             failure does it introduce?
                |
             What is the source of truth, idempotency story, consistency
             promise, and recovery plan?
                |
             How will users, operators, and future engineers know it
             is working?
```

The tree's whole point is to force you to earn complexity. "One service + relational DB" is the default answer; every deviation from it must be justified by a named limit from the second box, not by familiarity with a fancier tool.

## You're ready to move to problems when you can answer these

Merged from the module's two check-yourself gates — answer all of these without naming a vendor, and in the last five, teach each with a concrete example and a concrete counterexample:

1. Why does an order-creation request need idempotency even with a database transaction?
2. When does a queue help, and what new failures does it introduce?
3. Why can a cache cause an outage instead of preventing one?
4. Why is a read replica not automatically safe for every read?
5. What is the smallest ordering scope needed for chat?
6. What evidence tells you a system is failing users rather than merely using high CPU?
7. CAP vs. PACELC, and a concrete per-operation consistency choice you'd actually make.
8. Transaction vs. saga; optimistic vs. pessimistic concurrency — when each wins.
9. Cache-aside, and how it behaves specifically under outage, stampede, and staleness.
10. Queue vs. stream vs. workflow engine, and what "at-least-once + idempotent consumer" actually guarantees.
11. Partition key, hot partition, replica lag, and a query-derived index — how they interact.
12. Deadline/retry/backpressure/bulkhead, and why an uncoordinated retry policy can cause an outage.
13. SLI/SLO/error budget, RPO/RTO, and what a *tested* recovery flow looks like versus an assumed one.
14. Why "add Kafka/Kubernetes/microservices" is not, by itself, a design answer.

Move to problems only after you can explain these in plain language, out loud, without notes.

## Model answers to the readiness questions

Answer each question out loud first, then compare. These are the length and shape an interviewer can absorb in under a minute: the mechanism, one concrete example, and (where it teaches something) a counterexample that shows the limit of the rule. The block that owns the detail is linked in each answer.

1. **Idempotency on top of a transaction.** A transaction makes *one attempt* atomic; it says nothing about the client sending the request twice. If the response is lost (timeout, dropped connection, app killed), the client cannot know whether the order exists, and the retry runs as a brand-new transaction that inserts a second order (the "timeout means I don't know" row in [10_distributed_systems_theory.md](10_distributed_systems_theory.md)). The fix is a client-supplied idempotency key stored under a unique constraint in the *same* transaction as the order, so a retry with the same key returns the original result ([03_api_design_high_level.md](03_api_design_high_level.md)). Example: `POST /orders` with key `K` times out, the client retries with `K`, and the server returns order 123 instead of creating order 124. Counterexample: `PUT /orders/123` with the full body is naturally idempotent and needs no key, and a *new* key for an identical cart is a genuinely new intent, not a duplicate.

2. **When a queue helps, and what it breaks.** A queue helps when work can finish after the response (email, thumbnail), when it smooths a burst so consumers run at a steady rate, or when a slow or flaky consumer must not slow the producer. It buys time, not capacity: if producers outrun consumers for an hour, the backlog must fit and the drain time must be acceptable. It introduces duplicate delivery (a visibility timeout that expires before the consumer finishes redelivers the message, so consumers must be idempotent), poison messages that need a dead-letter queue with an owner, backlog and lag you must alert on (age of the oldest message), the DB-commit-versus-publish gap (transactional outbox), and ordering only within a partition key ([09_messaging_and_streaming.md](09_messaging_and_streaming.md)). Counterexample: when the user needs the result in this response (a price quote, a password check), a queue only adds latency and a new failure mode.

3. **How a cache causes an outage.** The cache absorbs most reads, so the source is sized for the misses only. At a 95% hit rate the source sees 5% of reads; when the cache dies, restarts cold or expires a hot set all at once, it sees 100%, which is 20 times more, and it falls over. Stampedes on one hot key do the same at a smaller scale, and a cache call with no timeout in the request path turns a slow cache into slow requests. Mitigate with a tight timeout and fail-open to the source, source headroom or load shedding, single-flight coalescing, TTL jitter and stale-while-revalidate ([07_caching.md](07_caching.md)). Counterexample: a cache-aside tier whose source has headroom for full traffic turns a cache outage into a latency blip, not an outage.

4. **Why a replica is not safe for every read.** Replication is asynchronous by default, so a replica can lag the primary by milliseconds to seconds under load. A read that must reflect a write can therefore return old data: "did my edit save" shows the previous profile, and a stock check on a replica that has not yet applied the last sale shows stock that is already gone. Route those reads to the primary (for a short window after the user's own write, or always for that query class), or read the replica only when its lag is under a bound ([05_databases.md](05_databases.md)). Example of a safe replica read: a catalog page or dashboard where a few seconds of staleness changes nothing. Counterexample: the read inside a read-modify-write, which belongs on the primary and should be a single conditional `UPDATE` anyway.

5. **Smallest ordering scope for chat.** Order within one conversation: every participant must see that conversation's messages in the same order, and nothing requires an order *between* two conversations. Make `conversation_id` the partition key and assign a monotonically increasing per-conversation sequence number at the durable write, so clients sort by that sequence and never by client clocks. A global order would force one sequencer or partition for all chat traffic, a bottleneck that buys no user-visible benefit ([09_messaging_and_streaming.md](09_messaging_and_streaming.md), "Ordering scope"). Ask "ordered relative to what, for whom?": if a feature needs order across conversations, such as a per-user unread total, its scope is per user, still not global.

6. **Failing users versus busy CPU.** Look for user-visible evidence: the SLI falling (error rate up, p99 above the target on a critical path, checkouts completed per minute dropping), the SLO burn rate above the sustainable rate, and leading indicators of harm such as queue age growing or a connection pool near saturation. CPU on its own is a diagnostic to read *after* a page, not a page ([15_observability_and_reliability.md](15_observability_and_reliability.md)). Example: CPU is 40% but requests are queuing behind a saturated database pool and p99 has doubled, so users are failing and CPU says nothing ([13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md)). Counterexample: CPU at 85% with every SLI green is a capacity-planning note, not an incident.

7. **CAP, PACELC, and a per-operation choice.** CAP: during a network partition, a replicated system must either refuse or delay some requests (keeping consistency) or answer possibly stale (keeping availability). Partitions are not optional, so it is a choice *per operation, during a partition*, not "pick two". PACELC adds the everyday half: else (no partition) you still trade latency against consistency, because a synchronous cross-region write pays a round trip on every write. Concrete choices: the payment-ledger write is strongly coordinated (accept the latency, reject during a partition), a profile edit is read-your-writes through a sticky session, and search results are eventual with a stated freshness bound and conflict rule ([10_distributed_systems_theory.md](10_distributed_systems_theory.md)). Counterexample: "we are AP because we use a NoSQL store" is not an answer; one product makes different choices for different operations.

8. **Transaction vs saga, optimistic vs pessimistic.** Use a local ACID transaction whenever all the data lives in one database. Use a saga when the business action spans services with no shared transaction: a chain of local, idempotent steps, each with a compensating action (checkout: reserve stock, authorize payment, create shipment; if shipment fails, void the authorization and release the hold). Counterexample: an order row and its line items in one database need a transaction, and a saga there is pure overhead. Optimistic control (version check or compare-and-swap, the loser retries) wins when conflicts are rare because no lock is held while the app computes. Pessimistic control (`SELECT ... FOR UPDATE`, with a fixed lock order to avoid deadlock) wins on a hot row where retries would be wasted, such as flash-sale stock, and where a single conditional `UPDATE` fits, use that instead ([11_transactions_and_concurrency.md](11_transactions_and_concurrency.md)).

9. **Cache-aside under outage, stampede, and staleness.** The app reads the cache, on a miss reads the source and populates the cache, and writes go to the source and then invalidate the entry. Outage: the cache holds no unique data, so fail open to the source under a tight deadline; it becomes a load problem, and only survivable if the source has headroom or sheds load. Stampede: many concurrent misses on one key hit the source together, so coalesce them (single flight), jitter TTLs and serve stale while one request refreshes. Staleness is bounded by the TTL, and a reader that loads the old value just before a writer invalidates can re-cache it until the TTL ends, so choose the TTL from the product's tolerance. Example: a product page with a 60-second TTL on the description. Counterexample: an account balance used to authorize a payment must not come from a cache-aside cache at all ([07_caching.md](07_caching.md)).

10. **Queue vs stream vs workflow engine, and at-least-once plus idempotent consumer.** A work queue hands each job to one consumer group and removes it after the ack (resize an image). A durable stream is a retained, ordered log per partition that independent consumers read at their own offsets and can replay (`OrderPlaced` feeding fulfillment, analytics and search independently). A workflow engine durably runs a multi-step process with state, retries and compensation over minutes or days (payment, then inventory hold, then shipment). "At-least-once plus an idempotent consumer" guarantees every message is processed one or more times and that duplicates are harmless, because the consumer dedups on an event ID or applies a conditional state transition (`UPDATE ... WHERE status = 'PAID'`), so the *effect in the consumer's own state* happens once. Counterexample: a consumer that sends an email and records the event ID afterwards can crash in between and send twice, so it is not end-to-end exactly-once ([09_messaging_and_streaming.md](09_messaging_and_streaming.md)).

11. **Partition key, hot partition, replica lag, and derived indexes together.** The partition key decides which shard owns a row and therefore which queries touch one shard: a good key has high cardinality, even load and matches the dominant query (`conversation_id` for messages). A hot partition is what remains when one key is disproportionately popular, and the fixes (a cache in front, salted keys, buffered counters, replicas) each trade some consistency or read cost. Replicas scale reads but lag, so reads that must see a write still go to the primary. A query on a non-key attribute needs a secondary index: a local index means scatter-gather across every shard, while a global index gives one lookup but is usually updated asynchronously and lags too ([25_partitioning_and_hot_keys.md](25_partitioning_and_hot_keys.md)). Counterexample: partitioning by `created_at` sends every new write to the newest shard, a moving hotspot that no replica or index fixes.

12. **Deadline, retry, backpressure, bulkhead, and retry-induced outages.** Every call gets a deadline smaller than the caller's *remaining* budget, propagated down the chain. Retries apply only to transient, idempotent operations, with exponential backoff, jitter, a cap and a fleet-wide retry budget. Queues are bounded so "full" triggers a reject or shed decision. Bulkheads give each dependency or tenant its own pool so one slow dependency cannot starve the rest ([12_application_resilience_patterns.md](12_application_resilience_patterns.md)). Uncoordinated retries cause outages by multiplying: if three layers each make up to 3 attempts, one failing database call at the bottom is attempted 3 x 3 x 3 = 27 times per user request, and that extra load keeps the dependency down. Counterexample: retrying once with jitter at the edge only, within a 10% retry budget, on an idempotent read is safe, and [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md) covers what to do once overload has started.

13. **SLI/SLO/error budget, RPO/RTO, tested vs assumed recovery.** The SLI is a measured fraction of good events (feed requests that succeed in under 300 ms), the SLO is the target for it (99.9% over a rolling 28 days), and the error budget is the remainder: 0.1% of 28 days, about 40 minutes of full outage-equivalent, which you spend on shipping and stop spending on risky changes when it runs out. RPO is the most data you may lose (it sets replication and backup frequency) and RTO is the longest you may be down (it sets restore automation and drill cadence). A *tested* recovery is a backup restored into an isolated environment on a schedule, verified at the application level, with the restore time compared to the RTO, plus rehearsed failover game days ([15_observability_and_reliability.md](15_observability_and_reliability.md)). Counterexample: "we take nightly backups" with no restore drill is an assumption, and untested backups routinely turn out incomplete or inconsistent, which you then learn during the real incident.

14. **Why "add Kafka/Kubernetes/microservices" is not a design.** A component is the answer to a *named limit* (read volume, write volume, fan-out, isolation, correctness), and each one adds its own failure modes and operating cost: broker lag and durability, cluster operations, network calls and partial failure between services. Without the requirement it serves, it decorates the diagram; the default is one modular service plus a relational database until a stated limit says otherwise, and every addition is justified in the sentence "I use X to get Y for Z; the cost is C, accepted because R". Example where it earns its place: several independent consumers must each replay an ordered `OrderPlaced` history at sustained volume, which a retained log gives you. Counterexample: a welcome email at 50 per second needs a simple work queue or a jobs table, and a four-person team with one deployable gains little except extra network hops and failure modes from splitting into microservices.

## Related building blocks

This file is the synthesis of the whole directory — see [00_overview.md](00_overview.md) for the full reading order if any of the terms above are unfamiliar.
