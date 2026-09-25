# System Design: From First Principles to Interview-Ready Designs

System design is the practice of turning a product goal into a system that is correct, safe, operable, and affordable at a stated scale. It is not memorizing a diagram. A strong designer makes explicit trade-offs: which failure is acceptable, which data must be correct now, which work can happen later, and what will be measured in production.

This guide is self-contained. Work through it in order once, then use the interview playbook and question bank repeatedly. The technology examples reflect widely used tools as of September 2026; tool choice must always follow the workload, team skills, and operating constraints.

## 1. The mental model

Every design has five layers. Start at the top and do not choose infrastructure before you understand the first two.

| Layer | Question | Example answer for a photo-sharing app |
|---|---|---|
| Product | What must a user be able to do? | Upload a photo; follow people; see a feed. |
| Contract | What are the APIs and guarantees? | `POST /photos` is idempotent; a published photo is eventually visible in followers' feeds. |
| Data | What facts exist and which must be correct? | Photo metadata, ownership, follow graph, feed entries. |
| Flow | What happens on a read, write, retry, or failure? | Upload directly to object storage; publish an event; fan out asynchronously. |
| Operations | How do we deploy, observe, protect, and recover it? | SLOs, dashboards, alerts, backups, replay plan, access controls. |

The basic loop is:

```text
Clarify → quantify → define contracts → draw the smallest viable design
→ find bottlenecks/failures → evolve it → state trade-offs and observability.
```

### The central trade-off

Distributed systems trade simple local reasoning for scale, availability, and independent deployment. Network calls fail, responses arrive late or twice, clocks disagree, and replicas lag. Design as if all of those will happen, because they will.

Two rules carry a surprising amount of weight:

1. Keep a small, authoritative source of truth for each fact.
2. Treat every remote operation as fallible and every client request as retryable.

## 2. The vocabulary you must own

| Term | Plain meaning | Why it matters |
|---|---|---|
| Availability | Fraction of eligible requests that succeed. | An <abbr title="Application Programming Interface">API</abbr> can be “up” while users get errors; measure at the request boundary. |
| Latency | Time for one operation. Report percentiles, especially p95/p99, not only an average. | Long-tail pauses are what users notice and what exhaust connection pools. |
| Throughput | Work completed per unit time: requests/s, messages/s, bytes/s. | Drives capacity and partition count. |
| Durability | Probability acknowledged data survives over time. | A cache may be highly available but not durable. |
| Consistency | What reads are allowed to see after writes. | “Consistent” must be qualified: read-your-writes, linearizable, eventual, etc. |
| Scalability | Ability to handle more load by adding resources or changing design. | A service can be fast today yet have a fixed hard limit. |
| Elasticity | Ability to add/remove capacity as load changes. | Avoid paying peak cost all day. |
| Backpressure | Signal that a downstream system cannot safely accept more work. | Prevents queues, memory, and retry storms from turning slowdowns into outages. |
| Idempotency | Repeating an operation has the same intended effect as doing it once. | Makes retries safe for payment, creation, and event consumers. |
| Partition | A split of data/work across nodes. | It is the primary route to horizontal scale, and a source of skew. |
| Replication | Keeping copies of data in multiple places. | Improves resilience/read scale but introduces replication lag and conflict choices. |
| Shard key | The field used to select a partition. | A poor key creates hot shards and makes growth painful. |
| Control plane | The system that configures/manages a service. | Can be slower or unavailable during incidents; data paths should not depend on it per request. |
| Data plane | The path that serves real traffic. | Must keep serving safely when management systems are impaired. |
| RPO | Recovery Point Objective: maximum acceptable data loss measured in time. | “RPO 5 min” requires backups/replication that lose at most five minutes. |
| RTO | Recovery Time Objective: maximum acceptable time to restore service. | Drives hot standby vs restore-from-backup investment. |

### Availability math

An <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> is a target such as “99.9% of successful `GET /feed` requests finish within 300 ms over 28 days.” Its error budget is `1 − SLO`: 0.1% in this case. A 99.9% monthly availability target permits about 43.2 minutes of failed time, but request-success SLIs are usually more meaningful than a wall-clock uptime calculation. Google’s SRE guidance explicitly recommends user-relevant SLIs and acknowledges that 100% targets are neither realistic nor usually desirable.[^sre-slo]

### Little’s Law: the one formula to remember

`L = λW`

- `L`: average number of in-flight items
- `λ`: arrival rate (items/second)
- `W`: average time an item spends in the system (seconds)

At 2,000 requests/s and 0.15 s average latency, expect roughly 300 concurrent requests. If latency jumps to 3 s while traffic stays constant, in-flight work becomes 6,000. This is why slow dependencies turn into connection, thread, and queue exhaustion.

## 3. A repeatable interview playbook

Use this sequence aloud. It gives the interviewer a way to correct your assumptions early and shows disciplined thinking.

### Minute 0–5: scope the problem

Ask only questions that change the design.

- Who are the users and most important actions?
- Which actions are reads vs writes? What is the critical path?
- Expected active users, peak QPS, object sizes, and growth horizon?
- Which facts require strong correctness? Which can be eventually consistent?
- SLO, regions, privacy/compliance, budget, and whether this is greenfield or an evolution?
- What is explicitly out of scope?

Then state assumptions. Example: “I will optimize a single-region launch for 100k daily active users and 2k read QPS peak. Booking must never double-charge; search results may lag by a minute.”

### Minute 5–10: estimate, do not guess

Write quick, rounded calculations. Correct order of magnitude is more valuable than false precision.

```text
10M daily active users × 20 feed loads/day = 200M reads/day
200M / 86,400 ≈ 2.3k average read QPS
Peak at 5× average ≈ 12k read QPS

1M uploads/day × 2 MB original = 2 TB/day raw object storage
2 TB/day × 365 ≈ 730 TB/year before replicas/derivatives
```

Also estimate bandwidth: `QPS × average payload bytes`. A 100 KB response at 12k QPS is about 1.2 GB/s before overhead: CDN and pagination are suddenly first-class design decisions.

### Minute 10–20: define API and data

APIs are agreements, not implementation details.

```http
POST /v1/orders
Idempotency-Key: 3ca7...

{ "items": [{"sku":"A12", "quantity":2}], "payment_method":"pm_7" }

201 Created
{ "order_id":"ord_123", "status":"PENDING_PAYMENT" }
```

For each entity, state owner, primary key, important indexes, and consistency rule.

```text
Order(order_id PK, user_id, status, total, created_at)
OrderItem(order_id, sku, quantity, price_snapshot)
IdempotencyKey(key PK, request_hash, response, expires_at)
```

The price snapshot is deliberate: an order must retain the price paid even if the catalog price changes.

### Minute 20–35: draw the baseline

Start boring and correct.

```text
client → CDN/WAF → load balancer/API gateway → stateless application
                                            ├─ cache
                                            ├─ primary database
                                            └─ object store / message broker
```

Describe one read and one write end-to-end. Then name the first bottleneck and evolve only the affected part.

### Final minutes: close like an owner

- Revisit the hardest trade-off.
- Explain failure handling: timeouts, bounded retries, idempotency, dead-letter/replay, degradation.
- Name SLI/SLO, dashboards, alerts, capacity signal, backup and restore test.
- Give a phased plan: launch architecture → scale trigger → next evolution.

## 4. Building blocks and when to choose them

### Edge: DNS, CDN, WAF, load balancer, API gateway

**DNS** translates a name to an address and can route broadly by geography, but it is cached and not a precise real-time traffic switch.

**CDN** caches static and cacheable dynamic responses close to users. Put immutable media behind versioned URLs and set cache headers deliberately. CDN is not a substitute for authorization: use signed URLs/cookies or an origin authorization check where needed.

**WAF** filters known malicious patterns and enforces coarse policies. **Rate limiting** controls allowed work per actor; use both.

**Load balancer** distributes traffic among healthy instances. L4 balances connections; L7 understands HTTP methods/paths/headers and can route accordingly. Health checks must be cheap, meaningful, and separate from a dependency-heavy “everything is healthy” endpoint.

**API gateway** centralizes routing, auth verification, quotas, request shaping, and observability. Keep core business policy in the owning service; a gateway should not become a monolith.

### Stateless services and compute

Keep request-serving processes stateless: session state and durable state live elsewhere. That permits replacement and horizontal scaling. A container packages an app and runtime dependencies; Kubernetes is a portable platform for managing containerized workloads declaratively and automatically, not a requirement for every service.[^k8s]

Choose the simplest operational model that meets needs:

| Option | Use it when | Watch for |
|---|---|---|
| Managed/serverless container or function | Spiky traffic, small platform team, standard HTTP/event workload. | Startup latency, execution limits, vendor coupling, connection behavior. |
| Managed container service | Long-running services with simple deployment/scaling. | Fewer advanced scheduling controls. |
| Kubernetes | Many workloads, custom scheduling/networking, established platform capability. | Significant operational/security complexity; do not adopt for résumé aesthetics. |
| VM/bare metal | Special networking, hardware, predictable high utilization, legacy constraints. | You own patching, placement, autoscaling, and failure recovery. |

### A professional toolchain (choose capabilities, not brands)

There is no mandatory “modern stack.” This is a current, representative map of capabilities worth recognizing in architecture discussions. Managed equivalents are often the professional choice for a small team.

| Capability | Representative tools | Use it for | Do not confuse it with |
|---|---|---|---|
| Containers | Docker, containerd | Reproducible application packaging. | An orchestrator or security boundary by itself. |
| Orchestration | Kubernetes; managed container platforms | Declarative deployment, placement, autoscaling, service lifecycle. | A reason to split every service. |
| Infrastructure as code | Terraform/OpenTofu, Pulumi, CloudFormation | Reviewed, repeatable cloud resources and policy. | Application deployment or a secret store. |
| Delivery / GitOps | GitHub Actions/GitLab CI, Argo CD, Flux | Build/test artifacts; reconcile declared deployment state from Git. | A substitute for progressive rollout and monitoring. |
| Packaging | Helm, Kustomize | Compose Kubernetes manifests for environments. | A general programming language. |
| Service connectivity | Cloud load balancers, Envoy, service mesh | TLS, traffic policy, service discovery, retries where appropriate. | A free reliability upgrade; mesh adds operational cost. |
| Telemetry | OpenTelemetry, Prometheus, Grafana, Loki/Tempo | Instrumentation, metrics, dashboards, logs/traces. | A billing-grade event ledger. |
| Workflow / durable execution | Temporal, cloud workflow services | Long-running, retrying, compensating business processes. | A simple fire-and-forget queue. |
| Data movement | Kafka, managed queues, CDC connectors | Durable asynchronous integration and replay. | A transactional database. |
| Policy / secrets | Cloud IAM, Vault/secret managers, OPA-style policy engines | Least privilege, secret lifecycle, admission/policy checks. | Putting credentials in environment files committed to Git. |

Prometheus stores numeric monitoring data as labeled time series and uses a pull model over HTTP for most targets; it is excellent for operational metrics but is not designed as an exact per-request billing system.[^prometheus] Argo CD is a common GitOps choice for Kubernetes, while its production guidance recommends pinning a version rather than following an unpinned stable branch.[^argocd] For durable multi-step processes, Temporal is a current example of a workflow platform that persists workflow state and resumes after failures; evaluate it when handwritten retry/state-machine code is becoming the product’s hidden complexity.[^temporal]

### Data stores

Start from access pattern, not a fashionable database.

| Need | Usually start with | Why / design note |
|---|---|---|
| Transactions, joins, constraints | Relational DB: PostgreSQL/MySQL | Excellent default for orders, users, money, metadata. Model indexes from query paths. |
| Key lookup at huge scale, flexible schema | Distributed key-value/wide-column DB | Design around partition key; accept query/model constraints. |
| Documents with nested evolving fields | Document DB | Useful when documents are the retrieval unit; define indexes and transaction boundaries. |
| Full-text, relevance, filters | Search engine | It is a derived index, not your source of truth; rebuild from events/data. |
| Blob/video/image | Object storage | Cheap/durable; store object key and metadata in the database. |
| Relationships / multi-hop traversal | Graph database or precomputed adjacency | First prove relational adjacency tables cannot meet the access pattern. |
| Analytics/OLAP | Columnar warehouse/lakehouse | Keep analytical scans away from transactional primaries. |

Relational databases are the default for correctness-heavy workflows. Use transactions to group related changes; choose isolation based on anomalies you must prevent. PostgreSQL documents `READ COMMITTED` as its default and `SERIALIZABLE` as an option that can abort conflicting transactions, so callers must be able to retry a serialization failure.[^postgres]

### Cache

A cache is a performance optimization with a correctness cost. Every cache needs an ownership, TTL/eviction, invalidation, and outage policy.

**Cache-aside**: application reads cache; on miss reads database and populates cache. Easy and common; tolerate stale data and thundering herds with request coalescing/locking.

**Write-through**: write cache and database synchronously. Better read freshness, higher write latency.

**Write-behind**: acknowledge to cache then persist later. Higher write throughput but harder durability/failure semantics; avoid for money without a durable log.

Redis is often used for cache, rate limits, sessions, queues, and ephemeral coordination because it provides native data structures. Redis notes that caching works best for data read frequently and updated infrequently, and invalidation remains a required design concern.[^redis]

Never make cache the only copy of critical data. Plan cache stampede behavior: stale-while-revalidate, TTL jitter, bounded fallbacks, and per-key request coalescing.

### Messaging and streams

Use asynchronous messaging when the caller does not need the result now, work is bursty, or multiple consumers need the same durable event.

| Pattern | Meaning | Example |
|---|---|---|
| Queue | One work item is handled by one worker group. | Resize uploaded image. |
| Pub/sub | Fan out a transient message to current subscribers. | Live presence notification. |
| Durable event stream | Ordered, retained events consumed independently. | `OrderPlaced` powers fulfillment, email, analytics. |
| Workflow/orchestrator | Coordinates durable multistep business work. | Payment → reserve inventory → create shipment, with compensations. |

Kafka is an event-streaming platform: producers append records to topics, partitions establish order within a partition, and consumer groups divide partitions among consumers. It supports durable streams and independent consumers, but it does not remove the need for idempotency, schemas, retention, and replay controls.[^kafka]

**Exactly once** is usually not an end-to-end property. Prefer *at-least-once delivery + idempotent consumer*: record a stable event ID in the same transaction as the business effect, or use a unique constraint/conditional write. For database-to-broker publishing, use the **transactional outbox**: commit business data and an outbox row together; a relay publishes the outbox reliably; consumers deduplicate.

### Identity, secrets, and encryption

- Authenticate: establish who is calling (OIDC/OAuth, session, mTLS for services).
- Authorize: decide whether that identity may perform this action on this resource (RBAC, ABAC, relationship checks).
- Encrypt in transit with TLS; encrypt storage with managed keys where required.
- Keep secrets in a secret manager; never in source, images, chat logs, or client code.
- Validate input, use parameterized queries, scope service identities narrowly, audit privileged actions, and define data retention/deletion.

## 5. Reliability patterns you should explain naturally

### Timeouts, retries, and circuit breakers

Every network call needs a deadline. Budget it across the call chain: an upstream request with 500 ms left must not begin a 2-second downstream call.

Retry only transient failures, only idempotent operations (or those protected by an idempotency key), with exponential backoff and jitter, a cap, and a retry budget. Retries multiply load during an incident; three layers each retrying three times can create 27 downstream attempts.

A **circuit breaker** temporarily stops calls to a failing dependency after a threshold and returns a fallback/failure quickly. A **bulkhead** isolates pools/queues so one dependency or tenant cannot consume all capacity. AWS recommends bounded queues, client timeouts, throttling, loosely coupled dependencies, and idempotent mutations as reliability practices.[^aws-reliability]

### Graceful degradation

Decide what can be reduced without breaking the core transaction.

```text
Search down → serve recently cached results or a browse-only experience.
Recommendation down → show chronological feed.
Email provider slow → accept order, enqueue notification, expose order status.
Payment provider unavailable → do not claim payment success; retain safe pending state.
```

### Replication and consistency

Replication solves availability and read scale, not every correctness need.

- **Leader/follower**: writes go to a leader; replicas serve reads. Reads from a replica can be stale.
- **Quorum**: require enough replica responses for a chosen consistency/durability target. Higher latency and availability trade-offs.
- **Read-your-writes**: after a user changes a profile, route that user’s reads to a sufficiently fresh source for a bounded time.
- **Eventual consistency**: replicas converge later. State the user-visible rule and conflict resolution, not just the phrase.

Do not casually invoke CAP. Under a network partition, a distributed replicated system must choose whether a request may wait/fail or return a response that might not reflect the latest acknowledged write. Most real systems make this choice per operation.

### Multi-region and disaster recovery

Start single-region unless latency, regulation, or availability target justifies more. Then choose deliberately:

| Strategy | RTO / RPO tendency | Cost/complexity |
|---|---|---|
| Backup + restore | High RTO, non-zero RPO | Lowest |
| Pilot light | Moderate | Moderate |
| Warm standby | Lower | Higher |
| Active/active | Lowest target latency/RTO | Highest; conflicts and global data rules are hard |

Document the failure domains: process, node, availability zone, region, cloud account, and vendor. Test restores and failovers; a backup not restored is an assumption, not a recovery strategy.

## 6. Observability and operations

Observability answers “why is the system behaving this way?” using evidence.

| Signal | Best at answering | Example |
|---|---|---|
| Metrics | How much/how often? | `http_requests_total`, p99 latency, queue depth, cache hit rate. |
| Logs | What happened in this event? | Structured JSON with request ID, event ID, tenant, error code. |
| Traces | Where did this request spend time? | One trace across gateway → order → payment → DB. |
| Profiles | Which code paths consume CPU/memory? | CPU flame graph during p99 regression. |

OpenTelemetry is a vendor-neutral framework for collecting and exporting traces, metrics, logs, and related context; instrument services at request boundaries and propagate trace context across async messages.[^otel]

For every service define:

1. **SLIs**: request success rate, p95/p99 latency, freshness lag, queue age, durability/restore result.
2. **SLOs**: targets and window, with exclusions defined sparingly.
3. **Alerts**: actionable, user-impacting, with severity and a runbook link.
4. **Dashboards**: RED for request services (Rate, Errors, Duration); USE for resources (Utilization, Saturation, Errors).
5. **Runbooks**: symptom, impact, safe mitigation, rollback, escalation, and verification.

Alert on symptoms first (SLO burn rate, failed payments), then causes (database connections, pod restarts). Test load, failure, and recovery before production. This is what separates a diagram from an operated system.

## 7. Worked design: a URL shortener

### Requirements and assumptions

- Create a short URL for a long URL; redirect a short URL quickly.
- 100M new URLs/month; 10B redirects/month; 100:1 read/write ratio.
- Redirect p99 < 100 ms within one region; links should be durable.
- Custom aliases optional; analytics can be delayed; abuse prevention is required.

### API and data

```http
POST /v1/links
{ "url":"https://example.com/a/very/long/path", "custom_alias":"launch" }

201 { "code":"aZ8k2P", "short_url":"https://sho.rt/aZ8k2P" }

GET /{code} → 302 Location: original_url
```

```text
Link(code PK, long_url, owner_id, created_at, expires_at, status)
```

Use an opaque, random base62 code rather than a predictable sequential ID when enumeration is a concern. At 62^7, seven characters provide roughly 3.5 trillion possible codes; allocate randomly and retry on rare collision, or encode a unique distributed ID.

### Baseline architecture

```text
browser → CDN/edge redirect cache → redirect service → Redis → Link DB
                                           └──────────────→ event stream → analytics warehouse

creator → API service → Link DB + transactional outbox → event stream
```

**Redirect path:** validate code → cache lookup → database fallback → return 302/301. Cache positive mappings with TTL and negative results briefly to protect the database from repeated invalid codes. A redirect event is asynchronous: failure to record analytics must not block the redirect.

**Create path:** validate URL and permissions → generate code → insert with unique constraint → commit outbox row → respond. For a custom alias, unique constraint on `code` is the concurrency guard; return a conflict if already taken.

### Failure and evolution

- Redis unavailable: database fallback with rate limiting; do not make links disappear.
- Hot celebrity link: CDN absorbs traffic; cache keys are by code.
- Malicious destination: abuse scanning/allow/block rules and a kill switch on `status`.
- Database read pressure: add read replicas only if redirecting to a replica still meets freshness needs; a new link may require sticky reads to primary until replica catch-up.
- Multi-region: replicate mappings; choose a home region for creates or accept carefully defined conflict resolution for aliases.

The key trade-off: strong global uniqueness for a small code versus local availability. At modest scale a database unique index is enough; do not introduce a distributed ID service merely to make the drawing more complex.

## 8. Worked design: a news feed

### Requirements

Users follow authors and browse a reverse-chronological home feed. Posting must be durable; a new post should reach most followers in seconds. Some eventual consistency is acceptable. A user with 20M followers is possible.

### Data and flow

```text
Post(post_id PK, author_id, body, media_keys, created_at, visibility)
Follow(follower_id, followee_id, created_at)       -- index both directions
FeedItem(user_id, sort_key, post_id, author_id)    -- materialized inbox, if used
```

```text
post API → Post DB + outbox → PostCreated stream
                                 ├→ fanout workers → FeedItem store
                                 ├→ search indexer
                                 └→ notification worker

feed API → FeedItem store → hydrate posts from cache/Post DB → paginate
```

### Fanout choices

- **Fanout on write (push):** on post, write feed references to each follower’s inbox. Reads are fast; writes are expensive for popular authors.
- **Fanout on read (pull):** at read time query recent posts from followed authors and merge/rank. Writes are cheap; reads are costly.
- **Hybrid:** push for ordinary authors, pull/merge for high-fanout authors. This is common because the follower distribution is skewed.

Use cursor pagination, not offsets: `GET /feed?cursor=<created_at, post_id>`. An offset moves under concurrent inserts, producing duplicates/gaps. Feed items are references; hydrate current post state so deletion/privacy changes take effect.

### Correctness discussion

Post persistence is the source of truth. The feed is a derived, rebuildable projection. “A post may take up to 30 seconds to appear in the home feed” is a useful explicit freshness SLO. Make consumers idempotent by keying `FeedItem` on `(user_id, post_id)`; replaying an event then does not duplicate the item.

## 9. Worked design: rate limiting

Rate limiting protects fairness and survival. A policy might be “60 API requests/minute per user and 10/minute per IP for anonymous traffic.”

| Algorithm | Behavior | Best use |
|---|---|---|
| Fixed window | Simple counter resets on boundary; permits boundary burst. | Coarse internal controls. |
| Sliding log | Exact recent-request history; memory-heavy. | Low-volume strict policies. |
| Sliding window counter | Approximate smooth limit from adjacent windows. | General purpose. |
| Token bucket | Tokens refill steadily; permits controlled burst. | APIs where burst is acceptable. |
| Leaky bucket | Smooths output rate. | Downstream protection/queuing. |

Typical distributed implementation: gateway/service executes an atomic token-bucket operation in Redis keyed by `limit:{policy}:{actor}`; returns remaining quota and reset/retry metadata. Replicate/partition the limiter for scale, choose behavior on limiter failure (fail-open for low-risk browse endpoint, fail-closed for expensive abuse-sensitive action), and never rely solely on client identifiers users can forge.

## 10. Common system-design traps

- Starting with microservices, Kafka, Kubernetes, or multi-region before a baseline need exists.
- Saying “use a cache” without defining source of truth, invalidation, TTL, miss stampede, and failure behavior.
- Saying “use a queue” without consumer concurrency, ordering key, retry policy, poison message handling, and replay plan.
- Treating a replica as a free scalable primary; ignoring lag and write bottlenecks.
- Promising “exactly once” without an idempotency/deduplication mechanism.
- Using averages instead of p95/p99 and missing saturation.
- Omitting authorization and tenant isolation from the diagram.
- Optimizing a component in isolation rather than the end-to-end request path.
- Designing for an imagined billion users while failing to meet the stated launch needs.
- Naming products in place of explaining properties and trade-offs.

## 11. Deep mechanics: APIs, storage, partitioning, and coordination

### API design is a reliability decision

Use nouns/resources for the stable business model and actions where an action has real domain meaning. A request should carry a versioned, validated contract; the server should return machine-readable error codes and a correlation ID. Add fields compatibly, do not silently change a field’s meaning, and deprecate only after measuring actual client use.

For a write, distinguish these outcomes:

| Result | Meaning | Caller action |
|---|---|---|
| `201 Created` / `200 OK` | The business effect is known to have committed. | Use returned resource/state. |
| `202 Accepted` | Work was accepted for asynchronous processing, not completed. | Poll/status callback/event; do not imply success too early. |
| `409 Conflict` | Request violates current state or unique constraint. | Resolve/reload; do not blind-retry. |
| `429 Too Many Requests` | Admission control rejected work. | Retry only after server guidance/backoff. |
| Timeout / broken connection | Outcome may be unknown. | Repeat only with the same idempotency key. |

An **idempotency key** maps a caller’s logical operation to a stored result. The server stores key, authenticated principal, request fingerprint, status, and response for a retention window. A replay with the same key and same body returns the original response; same key with a different body is rejected. This turns ambiguous network failure into a safe retry without pretending the network is reliable.

### Indexes and query-driven modeling

An index is an auxiliary structure that makes a query faster at the cost of write amplification, storage, and maintenance. A B-tree is the common default for equality/range/order queries. A composite index follows a leftmost-prefix rule in many relational engines: an index on `(tenant_id, created_at)` can efficiently serve `WHERE tenant_id = ? ORDER BY created_at`, but often not an unbounded lookup by `created_at` alone.

Design each index from a specific query:

```text
Query: latest visible orders for one user
WHERE user_id = ? AND status IN (...) ORDER BY created_at DESC LIMIT 50

Candidate index: (user_id, created_at DESC)
```

Then inspect the execution plan with realistic cardinality. Avoid `SELECT *` on hot paths, unbounded pagination, N+1 fanout from an application loop, and adding indexes “just in case.” A full-text/search engine is often a projection optimized for retrieval; update it asynchronously from the authoritative write database and make its freshness contract visible.

### Storage trade-offs in one view

| Design | Strength | Cost / failure mode |
|---|---|---|
| Normalize relational data | Constraints, transaction boundaries, single truth. | Read joins and cross-domain schemas can become heavy. |
| Denormalize a read model | Fast predictable reads. | Duplicate data, asynchronous repair/rebuild needs. |
| Append-only event log | Audit, replay, derived views. | Schema evolution, retention, consumer correctness. |
| Immutable object + metadata row | Cheap durable media storage. | Lifecycle, access, and orphan cleanup must be designed. |
| Materialized view | Fast common query at scale. | Freshness lag and rebuild cost. |

Choose a source of truth, then derive caches/search/feed/analytics from it. This means an outage in the derived system reduces capability but does not erase truth.

### Partitioning without hand-waving

Partition when one machine/store reaches a proven limit in storage, write throughput, or working set. Your partition key decides four things: which node receives a write, which data is co-located, which query is cheap, and how a hot customer can hurt everyone else.

- **Hash partitioning** distributes keys evenly: good for key lookup; poor for range scans.
- **Range partitioning** keeps adjacent keys together: good for time/range scans; vulnerable to a hot current range.
- **Directory/lookup partitioning** maps tenant/key to location: flexible moves; adds a routing dependency.
- **Consistent hashing** minimizes keys moved when nodes change: useful for distributed caches; virtual nodes smooth imbalance.

Start with tenant/user ID when most traffic is tenant-scoped. For an exceptionally hot tenant, introduce a second dimension such as `(tenant_id, bucket)` only after proving it is needed, and preserve a way to enumerate every bucket. Track per-partition QPS, bytes, latency, and queue age; averages hide hot partitions.

### Ordering, clocks, and coordination

Global order is expensive and usually unnecessary. Define the smallest order your product needs: per chat conversation, per account ledger, per device, or none. Put that key in the stream partition key or serialization boundary. A broker partition can preserve append order, but duplicate delivery and retries still require idempotent application behavior.

Wall clocks can jump and distributed clocks are not perfectly synchronized. Never use “last writer wins by client timestamp” for important conflicts unless clock skew is acceptable. Prefer server-assigned sequence/version, compare-and-swap, database constraints, or a domain-specific conflict rule.

For a scarce resource (one seat, one coupon, one inventory unit), use the source of truth to arbitrate:

```sql
UPDATE inventory
SET available = available - :quantity
WHERE sku = :sku AND available >= :quantity;
```

Check affected rows in the same transaction. A “check then update” pattern races. For a temporary hold, create a hold record with expiry and make reservation/release operations idempotent; a background cleanup is a safety net, not the sole correctness mechanism.

### Consensus: what it is and what it is not

Consensus systems allow a set of replicas to agree on a sequence of decisions despite some failures. You use them indirectly in managed databases, Kubernetes control planes, or coordination stores. They are appropriate for small, high-value control state: leader election, configuration, membership, lease ownership. They are not a general database scaling trick and should not sit in the hot request path for every user action.

A **lease** grants temporary ownership and must be renewed. Design for lease expiry and fencing: a stale holder can wake up after a pause, so downstream writes should reject older fencing tokens. “We elected a leader” is insufficient without handling the old leader’s late work.

### 11a. Consistent hashing — the math, not just the name

The one-line version above (§ Partitioning) says virtual nodes smooth imbalance. Here is why, with numbers.

**The ring.** Hash both nodes and keys into the same space, typically `[0, 2^32)` or `[0, 2^64)` via a well-distributed hash (murmur3, xxhash — never a cryptographic hash, it's needlessly slow for this). Sort node hash-positions; a key belongs to the first node whose position is ≥ the key's hash, walking clockwise, wrapping at the max value back to 0.

```text
ring positions (mod 2^32), 3 nodes, 1 virtual node each:
  A: 1_500_000_000      B: 2_800_000_000      C: 4_000_000_000
key hash 1_900_000_000 → first node ≥ it walking clockwise → B
key hash 4_100_000_000 → wraps past C, past the max, back to A
```

**Why it minimizes movement.** With plain modulo hashing (`node = hash(key) % N`), changing `N` by one remaps nearly every key — `% N` and `% (N+1)` agree on almost nothing. With ring hashing, removing node `B` only reassigns the keys that were owned by `B`; they move to `B`'s clockwise successor. Every other key's owner is unchanged. Expected fraction of keys moved when going from `N` to `N+1` nodes is `1/(N+1)` — provably optimal for any scheme that must redistribute *some* keys, since a new node has to acquire its fair share from somewhere.

**Why you need virtual nodes.** With one ring-position per physical node, the *gaps* between consecutive nodes are arbitrary — for `N` uniformly random points on a circle, the largest gap is `Θ(log N / N)` of the ring, not `1/N`. A node that happens to own a big arc gets a disproportionate share of keys, and losing/gaining one physical node causes a lumpy, unpredictable load shift. Giving each physical node `v` virtual points (`v` independent hashes, e.g. `hash(nodeID + ":0")`, `hash(nodeID + ":1")`, …) means each physical node's total ownership is the *sum* of `v` samples from the gap distribution — by the law of large numbers, the coefficient of variation of a physical node's load shrinks as `1/√v`. Practical systems (Cassandra, DynamoDB-style rings) use `v` in the 100–256 range specifically to drive load imbalance under ~5–10%.

| `v` (virtual nodes/physical node) | typical load stdev/mean | rebalance granularity |
|---|---|---|
| 1 | 40–90% (highly skewed) | one huge chunk moves per node change |
| 32 | ~15–20% | still lumpy |
| 256 | ~5–7% | smooth, near-uniform |

**Cost of a topology change**, precisely: adding one node to an `N`-node ring with `v` virtual points each moves `≈ K/(N+1)` keys (`K` = total keys), spread across up to `v` distinct donor nodes rather than one — which is *also* why virtual nodes help operationally: the rebalance I/O is spread across the whole cluster instead of hammering one neighbor.

### 11b. Raft vs. Paxos — what leader election actually does

Both solve the same problem (agree on a totally ordered log of commands across replicas that can crash/restart/partition), but Raft was explicitly designed to be *understandable* by decomposing it into three sub-problems: leader election, log replication, and safety. Paxos (classic "single-decree" Paxos, and its log-replicated cousin Multi-Paxos) proves the same safety properties but leaves the *engineering* of leader election and log management as an exercise, which is why real systems built on Paxos (Chubby, Spanner) layer significant undocumented machinery on top.

**Raft leader election, mechanically:**

1. Every replica starts as a **follower** with a randomized election timeout (e.g. 150–300 ms, randomized specifically so followers don't all time out simultaneously and split votes forever).
2. If a follower hears no heartbeat from a leader before its timeout fires, it becomes a **candidate**, increments its **term** (a monotonic logical clock — the core trick that makes staleness detectable), votes for itself, and sends `RequestVote(term, lastLogIndex, lastLogTerm)` to every peer.
3. A peer grants its vote for a given term **at most once**, and only if the candidate's log is at least as up-to-date as its own (comparing `lastLogTerm` then `lastLogIndex` — this is what prevents a replica with a stale/short log from becoming leader and silently discarding committed entries).
4. A candidate that receives votes from a **majority** (`⌊N/2⌋ + 1`) becomes leader for that term and starts sending periodic heartbeats (`AppendEntries` with no entries) to suppress other elections.
5. An entry is **committed** once the leader has replicated it to a majority — at that point it is durable even if the leader immediately crashes, because any future leader must have that entry in its log to win an election (step 3's log-comparison rule guarantees this: the "Leader Completeness" property).

**Why terms prevent split-brain, not just detect it.** Every RPC carries the sender's term. A node that sees a higher term than its own immediately steps down to follower and adopts that term — this is the entire split-brain defense. An old leader that was network-partitioned and comes back believing it still leads gets a heartbeat rejection or a higher-term RPC from a client contacting the new leader, sees the higher term, and demotes itself. It cannot commit new entries in the meantime because it cannot reach a majority (the majority is on the other side of the partition, participating in the new leader's term) — this is the quorum intersection argument: any two majorities of `N` nodes share at least one node, so a stale leader's majority and a new leader's majority cannot both exist simultaneously without overlapping in a node that has already voted for the new term.

**Paxos, for contrast — same safety, two-phase instead of leader-first:**

- **Phase 1 (Prepare/Promise):** a proposer picks a proposal number `n` (must be higher than any it has used), asks a majority "promise not to accept anything numbered `< n`." Acceptors reply with the highest-numbered proposal they've already accepted, if any.
- **Phase 2 (Accept/Accepted):** if a majority promises, the proposer sends `Accept(n, v)` — where `v` is *forced* to be the value from the highest-numbered proposal any acceptor already reported (this is the crux of Paxos's safety proof: it never lets a new proposal override an already-possibly-chosen value). Only if no acceptor reported a prior value is the proposer free to pick its own `v`.
- A value is **chosen** once a majority accepts it in some round.

Multi-Paxos optimizes the common case by electing a stable leader (skipping Phase 1 per-entry once one proposer is recognized as distinguished) — at which point it converges operationally to something Raft-shaped, which is precisely Raft's insight: formalize the "stable leader" case from day one instead of deriving it as an optimization.

| | Raft | (Multi-)Paxos |
|---|---|---|
| Roles | Leader / follower / candidate, explicit | Proposer / acceptor / learner, symmetric |
| Leader | Always required before any write commits | Optional per-round; classic Paxos has none |
| Log gaps | Disallowed — log is a strict prefix-replicated sequence | Classic Paxos allows out-of-order slot decisions |
| Understandability | Designed for it; single coherent algorithm | Notoriously requires care to implement correctly (see Chubby/Zab/Raft papers' own commentary) |
| Real systems | etcd, Consul, CockroachDB (per-range), TiKV | Chubby, Google Spanner (uses Paxos per-shard), ZooKeeper (Zab, a Paxos-family protocol) |

**Split-brain, restated generally:** it is prevented by requiring every write-granting decision to cross a **majority quorum**, and by making staleness self-evident via a monotonic term/ballot number that every message carries and every node obeys ("if you see higher, you are stale, stop acting"). Fencing tokens (§11, Consensus) are the same idea applied one layer up, for clients talking to a lock/lease service rather than replicas talking to each other.

### 11c. Vector clocks — ordering without a shared clock

A vector clock lets a replica detect *causality* between two events without synchronized wall clocks. Each of `N` replicas keeps a vector `V = [v_1, ..., v_N]`, one counter per replica.

- On a local event, replica `i` increments its own component: `V[i] += 1`.
- On sending a message, attach the current vector.
- On receiving a message with vector `V_msg`, replica `i` sets `V[j] = max(V[j], V_msg[j])` for every `j`, then increments its own component.

**Comparing two vectors `A` and `B` tells you the causal relationship:**

- `A ≤ B` component-wise (and `A ≠ B`) → `A` happened-before `B` (A causally precedes B; B's writer had already observed A).
- `B ≤ A` component-wise → `B` happened-before `A`.
- Neither dominates (`A` has a larger component somewhere and `B` has a larger component somewhere else) → **concurrent**, i.e. a genuine conflict that must be resolved (last-writer-wins by wall clock, application-level merge — e.g. a CRDT — or surfaced to the user, as Dynamo's original design does with sibling values).

```text
Replica X writes:            V = [1,0,0]
Replica Y reads X's write, then writes:  V = [1,1,0]   ([1,0,0] ≤ [1,1,0] → causal)
Replica Z, unaware of either, writes:    V = [0,0,1]   (incomparable with both → concurrent)
```

This is exactly the mechanism Amazon Dynamo used to detect when two replicas' versions of a value must be reconciled by the application rather than silently overwritten by whichever write happened to arrive later on a given node — the thing §"Ordering, clocks, and coordination" above warns you not to solve with client wall-clock LWW.

**Practical cost, and why most systems avoid raw vector clocks:** the vector grows with the number of writers that have ever touched a key (not just current replicas — client-side or per-session vector clocks can grow unboundedly), so production systems prune (drop old/quiescent components with a bounded size and accept rare false conflicts) or replace vector clocks with **version vectors** (bounded to physical replica count only) or dotted version vectors (Riak) which track per-write provenance more precisely at similar cost. Where you don't need full causal history — only "is my write based on the current value" — a single monotonic version/CAS counter (as recommended in §"Ordering, clocks, and coordination") is far cheaper and usually sufficient.

### 11d. B+ trees vs. LSM trees — the actual storage-engine trade-off

Both answer "how do I keep a sorted, indexable structure on disk that supports point lookups, range scans, and durability." They make opposite bets about where to pay the cost.

**B+ tree (used by: PostgreSQL, MySQL/InnoDB, most relational engines' default index).**

- A balanced tree where every leaf is at the same depth. Internal nodes hold only routing keys; **all** values live in leaf nodes, and leaves are linked in a doubly-linked list for fast range scans without re-walking the tree.
- Node size is chosen to match the storage page size (commonly 4 KB or 8 KB) so **one node = one disk page = one I/O**. Fanout `f` (children per node) is therefore `≈ page_size / (key_size + pointer_size)` — for 8-byte keys and 8-byte pointers on a 4 KB page, `f ≈ 4096/16 = 256`.
- Tree height for `n` keys is `⌈log_f(n)⌉`. With `f = 256` and `n = 10^9` rows: `log_256(10^9) ≈ 3.7` → **4 levels**, i.e. a point lookup costs ~4 random I/Os (fewer in practice since the top 1–2 levels are almost always cache-resident in the buffer pool).
- **Writes are in-place.** Updating a key means locating its leaf and mutating it — no rewrite of unrelated data — but that mutation is a **random** disk write, and if it overflows the page, the tree must **split** the node and propagate a new routing key upward (occasionally cascading to the root). Random writes are the B+ tree's weak point on spinning disks and, to a lesser degree, on SSDs, where they still cause write amplification inside the FTL and fragment free-space maps.

**LSM tree (used by: RocksDB, Cassandra, LevelDB, HBase, and most modern write-optimized stores).**

- Writes go to an in-memory sorted structure, the **MemTable** (typically a skip list or balanced tree), after first being appended to a **write-ahead log** on disk for durability (see §11e) — so a write is one sequential log append plus an in-memory insert: no random disk I/O at all.
- When the MemTable reaches a size threshold, it is flushed to disk as an immutable, sorted **SSTable** (Sorted String Table): a sequence of sorted key-value blocks plus a sparse index and, critically, a **Bloom filter** over the keys it contains.
- Reads must check the MemTable, then potentially **every** SSTable, newest-first (a key may have been overwritten/deleted in a newer table) — this is the LSM tree's weak point: read amplification. The Bloom filter on each SSTable lets a read skip tables that provably do not contain the key (a Bloom filter never false-negatives; it can false-positive at a tunable rate, commonly tuned to ~1%, trading `~10 bits/key` of memory for that rate via `m/n ≈ -1.44 log_2(p)`), so in practice most SSTables are skipped in O(1) per table instead of a real disk seek.
- **Compaction** merges SSTables to bound the number a read must check and to physically remove tombstoned/overwritten data:
  - **Size-tiered compaction** (Cassandra default): merge SSTables of similar size into a bigger one when enough accumulate. Good write throughput, worse read amplification and space amplification (deleted data can survive until a large compaction happens).
  - **Leveled compaction** (LevelDB/RocksDB default): SSTables are organized into levels `L0, L1, L2, ...` where each level is ~10× the size of the one above, and within a level (`L1+`) key ranges are non-overlapping. A compaction merges one SSTable from `L_i` with the overlapping SSTables in `L_{i+1}`. This bounds read amplification much better (a key exists in at most one table per level, past L0) at the cost of more total write I/O — this **write amplification** (each byte written by the app gets rewritten ~10× more across levels, for a 10× level ratio) is the leveled strategy's core trade against size-tiered's.

| | B+ tree | LSM tree |
|---|---|---|
| Write path | In-place random write | Sequential log append + in-memory insert |
| Write amplification | Low–moderate (page splits) | Higher (repeated compaction rewrites) |
| Read path | O(log_f n) disk seeks, single structure | Memtable + Bloom-filter-pruned SSTable scan, more moving parts |
| Read amplification | Low (one structure, always current) | Higher (multiple SSTables, mitigated by Bloom filters + leveling) |
| Space amplification | Low | Higher until compaction runs (old versions linger) |
| Best for | Read-heavy / balanced OLTP with in-place updates | Write-heavy ingestion, time-series, log-structured workloads |

### 11e. Write-ahead logging and MVCC — how "durable" and "consistent read without blocking" actually work

**Write-ahead logging (WAL).** The rule: **never mutate the actual data structure (B+ tree page, in-memory table) until the change has been durably appended to an append-only log on disk.** The log record contains enough information to redo (and, for undo-style logging, undo) the change. Because appending to the end of a file is a sequential write, this converts what would otherwise be a random-I/O-bound commit into a cheap sequential write followed by an `fsync`. On crash, recovery replays the log from the last checkpoint forward, reapplying any committed-but-not-yet-flushed-to-the-data-file changes (**redo**) and rolling back any in-flight, uncommitted changes recorded before the crash (**undo**) — this is the ARIES-style recovery algorithm relational databases use, and it is the same durability primitive an LSM tree's WAL provides for its MemTable (§11d).

**MVCC (Multi-Version Concurrency Control).** Instead of a writer blocking readers (or vice versa) with locks, every row/value carries version metadata — commonly a creation transaction ID (`xmin`) and a deletion/expiration transaction ID (`xmax`), as in PostgreSQL, or an explicit timestamp, as in Spanner/CockroachDB. A transaction reading under **snapshot isolation** takes a **snapshot** — conceptually, a cutoff of "which transaction IDs were already committed when I started" — and only sees row versions whose `xmin` is in that committed set and whose `xmax` is not (i.e., not yet deleted as of the snapshot). A concurrent writer creates a **new version** of the row rather than mutating the old one in place, so it never blocks the reader, and the reader never blocks the writer.

- This is *why* "readers don't block writers and writers don't block readers" under MVCC, at the cost of needing **garbage collection of old versions** (PostgreSQL's `VACUUM`; RocksDB-backed stores rely on compaction) once no active snapshot can still see them.
- MVCC does **not**, by itself, prevent write-write conflicts. Two transactions concurrently writing the same row under snapshot isolation is handled either by first-committer-wins (the second writer's commit fails validation because the row it read has since been superseded — this is how CockroachDB/Postgres serializable-snapshot-isolation detect the conflict) or by locking at write time even though reads stay lock-free.
- **Snapshot isolation is not full serializability** — it admits the classic *write skew* anomaly (two transactions each read a shared invariant, each independently make a change that's individually valid against what they read, but the combination violates the invariant, e.g. two doctors each independently going off-call because they each see one other doctor still on-call). Reaching for `SERIALIZABLE` isolation (or an explicit `SELECT ... FOR UPDATE`) is the fix when a design genuinely needs it — most designs don't, which is why Postgres/MySQL default to a weaker level.

### 11f. Cache stampede prevention, the actual algorithm

§"Cache" above names the symptom (stampede) and the mitigations by label (jitter, coalescing, stale-while-revalidate). Here is the mechanism behind the most cited one, **probabilistic early expiration** (the XFetch algorithm):

Instead of a hard TTL where every requester past the deadline triggers a synchronous recompute — causing every concurrent request in that instant to miss simultaneously and hammer the origin — each read probabilistically decides to recompute *before* expiry, with a probability that ramps up as expiry approaches:

```text
recompute early if:  now - (delta * beta * ln(random()))  >=  expiry_time

where:
  delta  = measured/estimated time the last recompute took to produce this value
  beta   = tuning constant (β=1 is the standard XFetch default; >1 recomputes earlier/more)
  random() ∈ (0, 1)
```

Because `-ln(random())` is exponentially distributed, the probability of any single request choosing to trigger recompute rises smoothly as `now` approaches `expiry_time`, and — crucially — is **independent per requester**, so only a small number of the many concurrent requests near expiry actually recompute; the rest keep serving the (still technically valid, or "soft-expired") cached value. `delta` (how expensive the recompute is) naturally widens the early window for expensive keys and narrows it for cheap ones, which a flat "expire 10% early" rule cannot do.

This is complementary to, not a replacement for, **request coalescing** (a.k.a. single-flight): when a real cache miss does occur, only the first concurrent requester for that key actually calls the origin; every other concurrent requester for the same key blocks on / subscribes to that one in-flight call's result instead of independently re-triggering it. Combined, the two mechanisms mean a hot key essentially never causes more than one origin call at a time, whether the miss is a true expiry or an early-refresh.

## 12. Rules of thumb, with the reason behind each one

Rules of thumb accelerate early design; they are not laws. Say the rule and the condition under which you would break it.

| Rule of thumb | Why it works | Break it when |
|---|---|---|
| Start with a modular monolith and a relational database. | Lowest operational complexity; transactions and constraints preserve correctness. | A demonstrated workload/domain requires independent scaling, isolation, or a specialized store. |
| Put durable truth in one place; derive everything else. | Caches, indexes, feeds, and analytics can be rebuilt. | You intentionally use a multi-writer replicated database and define its conflict rule. |
| Keep request handlers stateless. | Horizontal scaling and replacement become routine. | A stateful protocol/server has a proven latency or coordination need; externalize/recover state anyway. |
| Make writes idempotent before adding retries. | Networks produce ambiguous outcomes. | Never for a public mutation; idempotency is required or retries must be avoided. |
| Time out every remote call and bound every queue. | Prevents resource exhaustion and retry cascades. | Do not omit it; tune deadlines per operation instead. |
| Prefer async work off the user path. | Smooths bursts and reduces user-perceived latency. | The user requires an immediate, authoritative result. |
| Preserve order only within the smallest required key. | Global ordering destroys parallelism. | The domain truly requires a global sequence, such as a narrow ledger journal. |
| Use cache-aside first and design invalidation explicitly. | It is understandable, observable, and easy to remove. | Write-through or read-through is justified by specific freshness/latency needs. |
| Paginate with a stable cursor, not an offset. | New writes do not shift a cursor result set. | Small immutable admin result sets where offsets are harmless. |
| Partition after measurement, not imagination. | Shards add routing, migrations, hotspots, and debugging burden. | Storage/write limits are known before launch or a managed service handles it transparently. |
| Prefer a managed primitive over self-hosting undifferentiated infrastructure. | The team can spend time on product and reliability controls. | Regulation, cost at scale, performance, or required control makes it unsuitable. |
| Make operations observable before scale demands it. | Missing telemetry during first failure is expensive. | Never omit basic logs, metrics, traces, and restore tests. |
| Encrypt and authorize at the boundary, then enforce again at data access. | Defense in depth limits blast radius. | Never relax it solely because traffic is “internal.” |
| Progressive delivery beats big-bang deployment. | Small cohorts and fast rollback reduce impact. | Emergency security remediation may require an immediate wider rollout. |

### Capacity and cost heuristics

- Size on **peak** and tail behavior, not daily averages. A 5× peak multiplier is a starting assumption, not a fact.
- Reserve a safety margin; autoscaling reacts after demand changes and dependencies also have limits.
- The most expensive resource might be database I/O, cross-zone/region egress, high-cardinality telemetry, or cache memory—not CPU.
- Store a pointer/reference rather than repeatedly moving a large object. Upload media directly to object storage using short-lived signed URLs when authorization allows it.
- Measure the cardinality of metric labels. A label like `user_id` can create millions of time series and cripple a metrics backend.
- Do not use a log/metric pipeline for financial billing or an analytics estimate for entitlement. Keep an auditable, exact source for money and rights.

## 13. Terminology reference

This is a compact working glossary. When you meet a new term, classify it: **traffic/compute, data, distributed behavior, security, or operations**. That immediately tells you which questions to ask.

### Traffic, network, and compute

| Term | Meaning |
|---|---|
| Anycast | One IP announced from multiple locations; routing tends to reach a nearby/healthy location. |
| Connection pool | Reusable database/HTTP connections; protects setup cost but must be bounded to avoid overwhelming a dependency. |
| Connection draining | Stop assigning new work to an instance while existing work finishes before termination. |
| CORS | Browser policy controlling cross-origin requests; not an authorization system. |
| DDoS | Attempt to exhaust network, protocol, or application resources; mitigate at edge plus application admission controls. |
| Egress | Data leaving a network/provider; often a latency and cost consideration. |
| gRPC | RPC framework/protocol commonly using HTTP/2 and typed schemas; useful for internal service contracts, not automatically public-browser friendly. |
| Head-of-line blocking | One slow request/packet delays later work sharing a constrained queue/connection. |
| HTTP keep-alive | Reuse a TCP connection for multiple HTTP requests; reduces handshake cost. |
| HTTP/2 and HTTP/3 | Multiplexed HTTP versions; HTTP/3 uses QUIC over UDP and reduces some transport-level head-of-line effects. |
| Ingress | Incoming traffic; in Kubernetes also a resource/API for external HTTP routing. |
| Load shedding | Deliberately reject/degrade low-priority work to protect the core service. |
| Long polling | Client holds a request open until data/timeout; a simpler near-real-time fallback. |
| NAT | Network address translation; can make many clients share an address and exhaust ports under high outbound connection volume. |
| Reverse proxy | Server in front of application servers that routes/terminates TLS/caches/enforces policy. |
| Service discovery | Locate a healthy service instance by logical name rather than a hard-coded address. |
| Sticky session | Route a client repeatedly to one instance; avoid unless required because it harms balancing/failover. |
| WebSocket | Long-lived bidirectional connection; design connection ownership, fanout, reconnection, and offline delivery. |

### Data and storage

| Term | Meaning |
|---|---|
| ACID | Atomicity, Consistency, Isolation, Durability: properties of a database transaction. “Consistency” here means constraints preserved, not replica freshness. |
| Base table | Authoritative stored table; compare with derived index/view/cache. |
| CDC | Change Data Capture: publish database changes to another system, often from transaction logs. |
| Compaction | Reclaim/merge stale records in log-structured stores; can create temporary I/O pressure. |
| Covering index | An index containing all fields needed by a query, avoiding a table lookup in favorable cases. |
| Data lake | Low-cost storage for raw/semi-structured analytical data; governance and table format matter. |
| Data warehouse | Curated analytical system optimized for SQL scans/aggregation, not OLTP writes. |
| Dead-letter queue (DLQ) | Separate holding place for messages that exceed retry policy; requires triage, correction, and replay workflow. |
| Foreign key | Database constraint that references another table; protects referential integrity. |
| Hot key | A key receiving disproportionate traffic; cache/partition it deliberately. |
| LSM tree | Write-optimized storage structure that buffers then sorts/merges files; common in many distributed stores. |
| MVCC | Multi-Version Concurrency Control; readers see a consistent version without necessarily blocking writers. |
| OLTP | Online transaction processing: short, correctness-sensitive operational reads/writes. |
| OLAP | Online analytical processing: large scans/aggregations over historical data. |
| Retention | How long data/events/logs are kept; a product, legal, cost, and recovery decision. |
| Schema migration | Deliberate compatible evolution of stored data; use expand → migrate/backfill → contract for zero-downtime changes. |
| Secondary index | Lookup structure on non-primary fields; accelerates reads while adding write/storage cost. |
| TTL | Time to live; expiry duration for cache/session/message/object data. |
| Write amplification | More physical writes than logical writes due to indexes, replication, compaction, and logs. |

### Distributed systems and messaging

| Term | Meaning |
|---|---|
| At-most-once | A message may be lost but will not be intentionally redelivered. |
| At-least-once | A message is retried until acknowledged; duplicates are possible. |
| Causal consistency | Effects can be observed after their causes; concurrent independent writes need not have one global order. |
| Consumer group | Consumers jointly share a topic’s partitions so one partition is processed by one group member at a time. |
| Event sourcing | Store domain events as primary history and derive current state; powerful audit/replay model with schema/replay complexity. |
| Fanout | Deliver one logical event to many users/consumers. |
| Fencing token | Monotonic token that lets a resource reject actions from stale leaders/lease holders. |
| Linearizability | Each operation appears to occur atomically between invocation and response; strong but may cost latency/availability. |
| Materialized view | Stored result/projection of data optimized for a query, refreshed synchronously or asynchronously. |
| Outbox pattern | Write domain change and publish-intent row atomically; relay emits event after commit. |
| Poison message | Event that repeatedly fails; quarantine with context and correct/replay it. |
| Read repair | Fix stale replica data while servicing reads. |
| Saga | Distributed business transaction expressed as local steps with compensating actions, not a global lock/rollback. |
| Split brain | Two nodes believe they lead/own the same responsibility; use quorum/leases/fencing to prevent damage. |
| Thundering herd | Many clients/workers simultaneously retry or refresh same work after expiry/failure. |
| Watermark | Stream-processing progress marker indicating event-time completeness up to a point, with late-event rules. |

### Security, privacy, and delivery

| Term | Meaning |
|---|---|
| ABAC | Attribute-Based Access Control: policy depends on attributes such as tenant, role, region, resource classification. |
| Audit log | Tamper-resistant record of security/business actions; define retention, access, and event completeness. |
| CSRF | Cross-Site Request Forgery: a browser is tricked into sending authenticated state-changing request; mitigate with same-site cookies/tokens/origin checks. |
| Data classification | Label data by sensitivity (public, internal, confidential, regulated) to drive controls. |
| Defense in depth | Multiple independent layers of control so one failure is not a breach. |
| IAM | Identity and Access Management: identities, authentication, roles/policies, permissions. |
| Key rotation | Replace cryptographic keys/credentials without outage; design versioning and overlap. |
| Least privilege | Give only permissions necessary for the task and duration. |
| mTLS | Mutual TLS: both client and server authenticate with certificates. |
| PII | Personally Identifiable Information; minimize collection and control access/retention. |
| RBAC | Role-Based Access Control: permissions grouped into roles. |
| SBOM | Software Bill of Materials: inventory of dependencies/artifacts for supply-chain response. |
| SAST/DAST | Static/Dynamic Application Security Testing. Both are inputs, not proof of security. |
| Supply-chain security | Protect build dependencies, artifacts, CI credentials, provenance, and deployment path. |

### Operations and delivery

| Term | Meaning |
|---|---|
| Blue/green deployment | Maintain old/new environments; switch traffic after verification, with fast rollback. |
| Canary deployment | Release to a small cohort, observe, then widen. |
| Error budget burn rate | Speed at which failures consume allowed SLO budget; alerts can combine short/long windows. |
| Feature flag | Runtime-controlled behavior gate; use for gradual release/kill switch, then remove stale flags. |
| Game day | Planned exercise of a failure/operational scenario to validate people, tooling, and runbooks. |
| GitOps | Desired deployment state is versioned in Git and reconciled to actual state by an agent. |
| IaC | Infrastructure as Code: version-controlled, repeatable infrastructure definitions. |
| Incident commander | Person coordinating response and communication, freeing responders to investigate. |
| MTTR | Mean Time To Restore/Recover; a useful outcome metric, not the only one. |
| Runbook | Concrete, safe operational procedure with verification and escalation. |
| Toil | Manual, repetitive, automatable operational work with no enduring engineering value. |

## 14. Current trends worth understanding—not blindly adopting

| Trend | What changed | Good fit | Caution |
|---|---|---|---|
| Platform engineering | Internal platforms provide reusable secure paths for delivery, data, and observability. | Many teams sharing infrastructure and standards. | Do not build a platform before repeatable user pain exists. |
| Durable execution | Workflow runtimes persist progress/retries for long-running business processes. | Orders, onboarding, human approval, agent pipelines, compensations. | Learn determinism, workflow versioning, activity idempotency, and vendor/runtime boundaries. |
| OpenTelemetry-first observability | Common instrumentation reduces vendor lock-in across traces/metrics/logs. | Any distributed service estate. | Semantic conventions and cardinality discipline still matter. |
| eBPF-based visibility/networking | Verified programs can observe/enforce at Linux kernel hooks with low overhead. | Deep network/security profiling in Linux/cloud-native fleets. | Kernel expertise, privileges, portability, and operational maturity are real requirements. eBPF is powerful but complex.[^ebpf] |
| GitOps and progressive delivery | Desired state is versioned/reconciled; rollouts are measured and gradual. | Kubernetes or declarative infrastructure environments. | Git commits alone do not prove a safe rollout; use health and SLO evidence. |
| Feature-flag standards | Vendor-neutral interfaces can decouple application code from flag providers. | Teams with multiple services/languages or changing providers. | Flags need lifecycle/ownership; they are not permanent configuration. OpenFeature is an example open vendor-neutral API.[^openfeature] |
| Serverless + managed data | More teams buy operational primitives rather than operate them. | Variable workloads, small teams, common patterns. | Model limits, egress, startup/connection behavior, and exit plan. |
| AI/agent workloads | New systems combine model calls, retrieval, tools, approvals, and long-running orchestration. | Bounded workflows with audit, evaluation, and human override. | Treat models as probabilistic dependencies: validate outputs, cap cost/time, protect tool permissions, and retain traces. |
| FinOps | Architecture decisions are evaluated on unit economics and cost allocation. | Any material cloud bill. | Cost optimization must not silently violate latency, resilience, or security needs. |

## 15. Security and privacy by design

Security is a system property. Put it in requirements, data model, threat model, deployment, and operations—not a lock icon next to the final diagram.

### A usable threat-model method

For each asset and flow, name: **asset**, **actor**, **entry point**, **trust boundary**, **abuse case**, **control**, **detection**, and **response**.

```text
Asset: private document
Actor: authenticated tenant user; malicious external user; compromised service
Entry point: GET /documents/{id}, signed object URL
Trust boundaries: browser → edge → API → object store
Abuse: ID guessing, confused-deputy download, replayed signed URL, insider bulk export
Controls: resource-level authorization; opaque IDs; short-lived scoped URL; tenant-aware IAM
Detection: denied-access and high-volume-export alerts; audit event
Response: revoke session/key, disable sharing, investigate audit trail
```

Use STRIDE as a prompt when useful: **S**poofing identity, **T**ampering data, **R**epudiation (lack of accountable audit), **I**nformation disclosure, **D**enial of service, **E**levation of privilege. It is a way to find questions, not a checklist that makes a system safe.

### Authentication, authorization, and session choices

Authentication proves a principal; authorization evaluates whether that principal may do a specific thing to a specific resource in its current context. Always authorize on the server close to the data/action. A UI hiding a button is only usability.

| Mechanism | Best for | Key risk to design |
|---|---|---|
| Server session + secure cookie | Browser applications needing easy revocation. | Cookie flags, CSRF, shared session-store availability. |
| Short-lived access token + refresh flow | Mobile/API clients and delegated access. | Token theft, refresh rotation, revocation delay, audience/issuer validation. |
| OAuth/OIDC | Delegated identity and federated login. | Validate redirect URI, state/PKCE, token claims; do not implement protocol from memory. |
| mTLS/workload identity | Service-to-service trust. | Certificate lifecycle, authorization policy after authentication. |
| RBAC | Stable job-role permissions. | Role explosion and resource-level exceptions. |
| ABAC/relationship access | Multi-tenant/product permissions such as “viewer of this project.” | Policy evaluation performance, explainability, change audit. |

**Zero trust** means each access is authenticated, authorized, and observed based on current context; it does not mean trusting no employee or using one particular product.

### Sensitive data lifecycle

1. Minimize: collect only what is necessary.
2. Classify: public, internal, confidential, restricted/regulated.
3. Isolate: tenant ID is part of every data key, query, authorization decision, and event.
4. Protect: TLS in transit; encryption at rest; keys controlled and rotated through a key-management system.
5. Limit: least-privilege identities, just-in-time admin access, separate production access.
6. Retain/delete: define legal/product retention, deletion propagation to replicas/indexes/backups, and evidence.
7. Audit: immutable-enough records of access and high-risk changes, with protected access to logs.

**Tokenization** replaces a sensitive value with a surrogate whose mapping is kept in a protected vault. **Hashing** is one-way and suitable only for verification/lookups designed for it; do not “hash” data that must later be recovered. **Redaction** removes or masks sensitive fields in logs/UI. These are different controls.

### Abuse and application protection

- Rate limit by the right identity (account, API key, tenant, device signal), not only IP.
- Make expensive actions require stronger quotas/verification; apply quotas before expensive fanout or database scans.
- Validate content type, size, structure, and ownership. Store uploads out of web roots; scan as required.
- Use parameterized queries; do not construct SQL, shell, or template expressions from untrusted input.
- Apply output encoding/context-aware escaping to prevent injection into HTML, JavaScript, URLs, and headers.
- Protect SSRF paths: restrict outbound destinations, resolve/check IPs, block metadata/private networks, and use egress policy.
- Treat webhooks as untrusted: verify signature, timestamp/replay window, idempotency, and payload limits.

## 16. Real-time, media, search, and analytics patterns

### Real-time systems: chat, collaboration, location, and presence

Separate the **connection plane** from the **durable message plane**. A WebSocket gateway owns live connections and receives client events; a durable service/log persists authorized messages; a fanout service delivers to online recipients; offline clients sync from durable history.

```text
client ⇄ websocket gateway ⇄ message service → durable message store/event stream
                                     ├→ online fanout gateways
                                     ├→ push notification worker
                                     └→ search/index projection
```

For chat, define order per conversation, not globally. Assign a server sequence number after durable acceptance. Client message IDs provide idempotency; recipients acknowledge up to a sequence/cursor. Presence (“online now”) is ephemeral and approximate; it should not be your source of truth for delivery.

For collaborative editing, understand the difference:

- **Operational Transformation (OT):** transform concurrent edit operations against each other, usually with a central ordered server.
- **CRDT:** conflict-free replicated data type; replicas merge deterministically without a central coordination step for supported operations.

Both require product decisions about cursor/selection, permissions, history, compaction, snapshots, and malicious/oversized operations. Use a mature library/service unless collaboration is the product differentiator.

### Media pipeline

Media is object data plus asynchronous derivatives:

```text
client → authorization API → short-lived upload URL → object store
object-created event → validator/scanner → transcoder/resizer → derivatives + metadata
viewer → CDN → authorized manifest/object variant
```

Originals and derivatives need immutable object keys, content hash/checksum, lifecycle rules, ownership, visibility, and deletion fanout. For video, produce multiple bitrate/resolution renditions and a manifest so the player can adapt to bandwidth. Separate upload completion from processing completion; expose a state machine (`UPLOADING`, `PROCESSING`, `READY`, `FAILED`) rather than making users guess.

### Search

Search is a query-optimized projection. The pipeline is normally source-of-truth change → indexer → search index. Define:

- document schema and analyzer/tokenizer per language;
- filters/authorization strategy (never leak a result through a search index);
- relevance signals and evaluation set;
- freshness target and reindex procedure;
- synonym/spell/correction behavior and explainability;
- index version and blue/green rebuild strategy.

Autocomplete often needs prefix-friendly structures such as a search index completion feature, edge n-grams, or a trie-like in-memory index. Cache popular prefixes, cap result count, debounce clients, and protect against high-cardinality query logging.

### Analytics and stream processing

Operational events are not automatically analytical truth. Make event contracts explicit: event ID, producer, schema version, occurred-at time, received-at time, tenant, privacy classification, and correlation ID.

**Event time** is when something happened; **processing time** is when your system saw it. They differ due to delay/retry. A stream processor uses windows (tumbling, sliding, session) and watermarks/late-event policy to make that explicit. For revenue or compliance, retain an immutable reconciliable record and understand correction/backfill flow; do not assume a dashboard counter is exact.

## 17. Testing, release engineering, and incident practice

### Test the properties, not only functions

| Test | Question it answers | Example |
|---|---|---|
| Unit | Does isolated logic meet its contract? | Token-bucket refill math. |
| Integration | Does it work with real dependency behavior? | Transaction rollback and unique constraint. |
| Contract | Do producer/consumer API/schema assumptions remain compatible? | Event schema field addition. |
| End-to-end | Does a core user journey work? | Checkout through payment sandbox. |
| Load | What happens at expected and peak volume? | 12k feed reads/s with realistic payload/cache state. |
| Soak | What leaks/degrades over time? | Connection pool/memory after 24 hours. |
| Chaos/resilience | Does system fail and recover as designed? | Kill one worker/zone; delay a dependency. |
| Restore/DR | Can we recover within RPO/RTO? | Restore a clean database into isolated environment and verify. |
| Security | Can known abuse/injection/authz bypasses succeed? | Cross-tenant access test suite. |

Use production-like data shape without copying sensitive production data into lower environments. Test migrations both forward and rollback/compatibility paths. A release is not complete until its behavior is observable.

### Progressive delivery

Deploy artifact once, promote it through environments/cohorts, and observe an explicit comparison against baseline: error rate, p99 latency, saturation, and business guardrails. A feature flag can decouple code deployment from exposure, but it needs owner, expected expiry, targeting policy, audit trail, and cleanup date. OpenFeature describes flags as runtime-controlled behavior and supports use cases such as canaries, experiments, and safe degradation.[^openfeature]

### Incident response mechanics

1. Detect and declare: state customer impact, time, scope, and incident commander.
2. Stabilize: stop the bleeding with rollback, load shed, feature disable, capacity, or dependency isolation.
3. Investigate: follow evidence—recent changes, SLO signals, traces, logs, resource saturation—not intuition.
4. Communicate: regular concise updates with known impact, mitigation, and next checkpoint.
5. Recover and verify: validate end-to-end user SLI, catch-up queues, data reconciliation, and residual risk.
6. Learn: blameless review focused on system conditions, detection gaps, safeguards, and tracked actions.

## 18. Build laboratory: turn understanding into capability

Reading creates vocabulary; building creates intuition. Build these in order, write an ADR and runbook for each, then intentionally break it.

| Lab | Build | Required learning outcomes |
|---|---|---|
| 1. API + DB | Multi-tenant notes API with PostgreSQL. | Migrations, constraints, indexes, authorization, cursor pagination, idempotent create. |
| 2. Cache + limiter | Cache-aside reads and Redis token bucket. | TTL jitter, stampede control, atomic script/operation, fail-open vs fail-closed. |
| 3. Async pipeline | Upload → event → thumbnail worker → state endpoint. | Object store, outbox, retries, DLQ, idempotent consumer, observability. |
| 4. Notification service | Email/push preferences and delivery workers. | Fanout, provider webhooks, quotas, template/version audit, retry policy. |
| 5. Real-time chat | WebSocket chat with offline sync. | Per-room ordering, reconnect cursor, presence, durable history, backpressure. |
| 6. Checkout | Order/inventory/payment sandbox flow. | Transaction boundary, hold expiry, saga/compensation, reconciliation, audit. |
| 7. Search | Index your notes/products asynchronously. | Projection, schema/index version, authorization, freshness, reindex. |
| 8. Operate it | Deploy one lab with CI, IaC, dashboards, SLO, and restore test. | Delivery, secrets, tracing, alerting, rollback, cost/capacity review. |

For every lab answer: What is authoritative? What happens if the response is lost? What happens if the worker retries? What happens if this dependency is slow? How is it measured? How is it restored? Those six questions are the core of professional system design.

## 19. Interview question bank with heuristic likelihood

These are **practice-priority estimates**, not universal hiring statistics. They reflect how commonly a problem family appears in general backend/platform interviews and how many concepts it tests. Company, level, and job type change the distribution. Prepare the high-priority rows first; then learn the patterns rather than memorizing one “answer.”

| Priority / estimated likelihood | Question family | Core patterns to demonstrate |
|---|---|---|
| Very high · 70–90% | URL shortener | IDs, cache-aside, read-heavy scale, analytics async. |
| Very high · 70–90% | Rate limiter | Token bucket, atomicity, distributed state, abuse/failure policy. |
| Very high · 65–85% | News/social feed | Fanout, materialized views, cursors, hot users. |
| Very high · 65–85% | Chat/messaging | WebSockets, ordering scope, presence, durable delivery, offline sync. |
| Very high · 60–80% | File/photo/video upload and sharing | Object storage, direct uploads, async processing, CDN, access control. |
| High · 55–75% | Notification service | Preferences, fanout, provider retries, idempotency, channels. |
| High · 55–75% | E-commerce checkout/order | Transactions, inventory/payment saga, idempotency, audit trail. |
| High · 50–70% | Search/autocomplete | Indexing pipeline, relevance, cache, prefix search, freshness. |
| High · 50–70% | Web crawler | Frontier queue, politeness, dedupe, storage, distributed workers. |
| High · 45–65% | Metrics/logging platform | Ingestion, partitioning, retention, aggregation, cardinality. |
| Medium · 35–55% | Ride dispatch/delivery tracking | Geospatial index, matching, real-time location, consistency. |
| Medium · 35–55% | Ticketing/seat reservation | Contention, holds/expiry, anti-oversell, payment. |
| Medium · 30–50% | Distributed cache | Eviction, invalidation, replication, consistent hashing, hot keys. |
| Medium · 30–50% | Feature flag/config service | Low-latency reads, propagation, audit, safe rollout. |
| Medium · 25–45% | API gateway | Routing, auth, quotas, service discovery, observability. |
| Medium · 25–45% | Pastebin/document collaboration | Storage, sharing, versions; for collaboration: operations/CRDTs. |
| Targeted · 20–45% | Payment ledger | Double-entry accounting, immutable events, reconciliation, compliance. |
| Targeted · 20–45% | Ad/campaign counter | High-write aggregation, dedupe, windows, late events. |
| Targeted · 20–40% | Video streaming | Transcoding ladder, manifests, CDN, DRM, QoE metrics. |
| Targeted · 15–35% | Job scheduler/workflow engine | Leases, retries, clocks, durable execution, compensations. |

### How to practice each question

1. Spend five minutes writing requirements and estimates only.
2. Spend ten minutes on API/data and one baseline flow.
3. Add one scale problem, one correctness problem, and one failure problem.
4. Explain your design aloud in 35–45 minutes and record it.
5. Review against the checklist below, then redesign under a changed constraint: multi-region, 100× writes, strict ordering, or a new privacy rule.

## 20. The design review checklist

Before calling any design complete, answer these questions.

### Product and contract

- What is the user-visible success/failure state?
- What is synchronous versus asynchronous?
- Which operations are idempotent and how are duplicate requests recognized?
- How does pagination, versioning, and backward compatibility work?

### Data

- What is the source of truth for every critical fact?
- What is the primary key, partition key, and required index for each access pattern?
- What data is a projection that can be rebuilt?
- Which reads may be stale, for how long, and for whom?
- How are deletion, retention, encryption, and audit handled?

### Scale and failure

- What happens at 10× traffic? Which resource saturates first?
- What happens when the cache, one partition, one zone, or one dependency is slow/down?
- Are timeouts, retries, load shedding, and backpressure bounded?
- Are events ordered only where necessary? What happens to a poison message?
- What is the RPO/RTO and when was restore last tested?

### Operations and security

- What SLI/SLO tells you users are harmed?
- How do you trace one request/event across services?
- Who can access which data? How are secrets and keys rotated?
- How are deployments rolled out and rolled back safely?
- How do you estimate and cap cost per request, tenant, or GB?

## 21. A 12-week mastery plan

| Weeks | Focus | Deliverable |
|---|---|---|
| 1–2 | Estimation, APIs, relational modeling, indexing, transactions | Design URL shortener and checkout; write calculations and schemas. |
| 3–4 | Caching, load balancing, rate limiting, CDNs | Implement a token-bucket limiter and explain cache failure modes. |
| 5–6 | Queues, streams, outbox, idempotency, workflows | Design notifications and an order pipeline; include replay and DLQ plan. |
| 7–8 | Partitioning, replication, consistency, multi-region | Design chat/feed; state ordering and freshness contracts. |
| 9–10 | Reliability, SLOs, observability, incident response | Add SLOs/dashboards/runbooks to three prior designs; run a failure review. |
| 11–12 | Timed interviews and specialization | Complete six 45-minute mocks: one each product, data, platform, real-time, and security-sensitive system. |

For each design, maintain a one-page architecture decision record (ADR): context, constraints, decision, alternatives rejected, consequences, and future trigger for revision. Professionals do not seek a permanent “best architecture”; they make a reversible decision with evidence and a plan to revisit it.

## 22. How to learn this book: an active course

Do not try to memorize every tool. Your target is to build a reflex: **requirements → load → data → flow → failure → evidence → trade-off**. Follow this weekly loop for the 12-week plan.

| Day | 60–90 minute session | Output |
|---|---|---|
| 1 | Read one focused chapter; make a one-page concept map in your own words. | Definitions + one trade-off per concept. |
| 2 | Do a five-minute estimate and API/data model for a new prompt. | Assumption sheet. |
| 3 | Draw the baseline architecture and narrate read/write paths aloud. | One diagram + a 5-minute recording. |
| 4 | Add failures: timeout, duplicate request, slow dependency, stale replica, bad deploy. | Failure table and mitigations. |
| 5 | Build or extend one lab component. | Working code + README/ADR. |
| 6 | Run a timed 45-minute mock; ask “why not the simpler design?” for each added component. | Mock answer and self-review. |
| 7 | Review flashcards, simplify the diagram, and plan the next week. | One-page revised design. |

### The four levels of mastery

1. **Name it** — define a term correctly: “a cache is a derived performance layer, not the source of truth.”
2. **Use it** — select it for a stated access pattern: “cache-aside protects the DB on read-heavy product pages.”
3. **Defend it** — explain its downside: “stale data and invalidation/stampede behavior.”
4. **Operate it** — state metrics, alerts, failure behavior, and recovery plan.

You are interview-ready when you can consistently reach level 3 in a 45-minute design and level 4 for the critical path of a system you have built.

### Lesson 1: design a reliable create operation

**Prompt:** Design `POST /orders` for a storefront. A client may retry after a network timeout. Inventory must not become negative. Payment and email are external dependencies.

First, identify the non-negotiable facts: an order must be created at most once per client intent; inventory allocation cannot oversell; payment outcome must be reconciled; email failure must not erase the order.

```text
Client ── POST /orders (Idempotency-Key) ──> Order API
                                               │ transaction
                                               ├─ Order row
                                               ├─ conditional inventory update
                                               └─ Outbox row: OrderCreated
                                                       │
                                              outbox relay → durable event stream
                                                       ├─ payment workflow
                                                       └─ email worker
```

**Data and invariants**

```text
orders(order_id PK, customer_id, status, total, idempotency_key UNIQUE, ...)
inventory(sku PK, available, ...)
outbox(event_id PK, type, payload, created_at, published_at NULL)

Invariant: inventory.available never falls below zero.
Invariant: one idempotency key maps to one request fingerprint and one order result.
```

Perform the allocation with one conditional statement/transaction, not a read followed by an update:

```sql
UPDATE inventory
SET available = available - :quantity
WHERE sku = :sku AND available >= :quantity;
```

If zero rows change, return a business-level out-of-stock result. If the client loses the response after commit, its retry uses the same idempotency key and receives the original order outcome. The outbox means an order committed to the database eventually creates a durable event even if the process crashes before publishing.

**Questions you must now answer aloud**

1. Why should payment not happen inside the inventory database transaction?
2. Which status does an order have while payment is pending?
3. What happens when payment confirms but the callback/event is delivered twice?
4. What do you measure to discover a stuck outbox relay or payment backlog?
5. If payment permanently fails, how is inventory released exactly once?

**Model answer:** payment is an unreliable remote action and holding a database transaction across it is slow and fragile. Create a durable pending order, run payment as an idempotent workflow/activity, and transition state with guarded updates. Duplicate callbacks deduplicate by provider event/payment reference. Alert on outbox age, workflow age, payment error rate, and inventory hold expiry. Compensation/release is itself an idempotent state transition.

### Mock-interview self-scorecard

After each design, score 0–2 in each row. A score of 14+ means a strong baseline; under 10 tells you what to practice next.

| Skill | 0 | 1 | 2 |
|---|---|---|---|
| Scope | Starts building immediately. | Names some requirements. | States relevant functional, non-functional, and out-of-scope assumptions. |
| Estimation | No numbers. | Gives numbers without derivation. | Derives QPS, storage, bandwidth, and peak assumptions. |
| Data | Names a database. | Has entities. | Names ownership, keys/indexes, invariants, and freshness. |
| Flow | Component diagram only. | Explains happy path. | Explains read/write path, async boundaries, retries, and state transitions. |
| Scale | Adds popular tools. | Identifies one bottleneck. | Evolves only proven bottlenecks and explains partition/cache choices. |
| Reliability | Says “replicas/retries.” | Mentions failures. | Uses deadlines, idempotency, bounded retries/queues, degradation, and recovery. |
| Operations | Mentions logs. | Mentions monitoring. | Defines SLI/SLO, traces, alerts, deploy/rollback, capacity and DR. |
| Trade-offs | Claims one best design. | Names a drawback. | Compares alternatives and identifies a future trigger to change. |

### Your first four weeks, exactly

| Week | Read | Design drills | Build |
|---|---|---|---|
| 1 | Sections 1–3, 11–12 | URL shortener; paginated notes API. | Notes API with PostgreSQL, migrations, tenant auth. |
| 2 | Sections 4 (edge/data/cache), 13 | Product catalog; rate limiter. | Redis cache-aside plus token bucket. |
| 3 | Sections 5, 11, 17 | Notification service; image processing. | Outbox + worker + DLQ/replay procedure. |
| 4 | Sections 6, 15, 20 | Checkout; seat reservation. | Trace the flow, add SLO dashboard and a restore test. |

At the end of week four, record a 45-minute checkout design. Do not compare it to an ideal online answer; compare it to the scorecard, identify the two lowest rows, and use those to choose week five’s work.

## 23. A compact answer template

Use this when an interviewer gives you a new prompt:

```text
1. Goal and non-goals
2. Assumptions: users, peak QPS, payload, SLO, correctness
3. API + core entities
4. Baseline: edge → stateless service → source-of-truth store
5. Read/write flow
6. Scaling: cache, partition, async work, replicas where justified
7. Correctness: transactions, idempotency, ordering, consistency promise
8. Reliability: timeout/retry/backpressure/degradation/DR
9. Security and operations: auth, observability, SLO, rollout
10. Trade-offs, phased evolution, and open questions
```

If you can explain every line of that template for a new product, you can design unfamiliar systems. The nouns will change; the reasoning does not.

## References

[^sre-slo]: Google SRE, [Service Level Objectives](https://sre.google/sre-book/service-level-objectives/), accessed September 2026.
[^aws-reliability]: AWS, [Reliability Pillar](https://docs.aws.amazon.com/wellarchitected/latest/reliability-pillar/welcome.html), revised November 2024.
[^k8s]: Kubernetes, [Concepts Overview](https://kubernetes.io/docs/concepts/index.html), accessed September 2026.
[^postgres]: PostgreSQL Global Development Group, [SET TRANSACTION](https://www.postgresql.org/docs/current/sql-set-transaction.html), PostgreSQL 18 documentation, accessed September 2026.
[^redis]: Redis, [Client-side Caching Introduction](https://redis.io/docs/latest/develop/clients/client-side-caching/), accessed September 2026.
[^kafka]: Apache Kafka, [Introduction](https://kafka.apache.org/documentation/), accessed September 2026.
[^otel]: OpenTelemetry, [Signals](https://opentelemetry.io/docs/concepts/signals/), accessed September 2026.
[^prometheus]: Prometheus, [Overview](https://prometheus.io/docs/introduction/overview/), accessed September 2026.
[^argocd]: Argo CD, [Getting Started](https://argo-cd.readthedocs.io/en/latest/getting_started/), accessed September 2026.
[^temporal]: Temporal, [Temporal Platform Documentation](https://docs.temporal.io/), accessed September 2026.
[^ebpf]: eBPF.io, [What is eBPF?](https://ebpf.io/what-is-ebpf/), accessed September 2026.
[^openfeature]: OpenFeature, [Introduction](https://openfeature.dev/docs/reference/intro/), accessed September 2026.
