# Twenty System Design Reference Solutions

Use the same lens for every design: authoritative data, access patterns, idempotency, ordering scope, bounded failure behavior, observability, security, and an explicit scale trigger.

## 02 Rate Limiter
Use an atomic token bucket keyed by policy and actor in a shared in-memory store: `tenant:user:route`. Capacity permits burst; steady refill sets average rate. Layer global safety, tenant-plan, and expensive-route quotas. Fixed windows are simpler but burst at boundaries; sliding logs are exact but costly. Fail closed for payments/abuse-sensitive work and use bounded local/fail-open policy only for low-risk browsing. Measure rejection rate, limiter p99/error, hot keys, and protected-backend saturation. Build it with atomic refill/spend and simulate concurrent requests/outage.

## 03 Pastebin
Keep metadata/ACL/expiry in relational storage and body in object storage for large snippets; CDN/cache public immutable reads. Opaque IDs help unlisted links but private data still needs resource authorization. Expiry status is enforced on read before asynchronous cleanup. Cache public content with TTL/purge rules; cache outage falls back to source. Avoid database BLOBs by default for large bodies, but small snippets may fit. Measure read p99, hit ratio, expiry denial, storage growth, abuse reports. Build create/read/expiry with signed private access.

## 04 Notification Platform
Persist notification intent then route through preference/quiet-hour decision into separate priority/channel queues. Channel workers call providers; verified provider webhooks update idempotent delivery state. Key intent by event/user/template/channel to deduplicate retries. Separate password-reset from marketing so bulk work cannot starve critical work. Do not send inline from product APIs: provider latency/outage becomes product outage. Measure intent-to-delivery latency, provider error/bounce, queue age, DLQ, opt-out compliance. Build one channel plus preference and retry policy.

## 05 Photo Pipeline
Authorize resumable direct multipart upload to object storage; metadata DB tracks `UPLOADING → PROCESSING → READY/FAILED/DELETED`; workers scan and create idempotent derivative versions. Keep original checksum/owner/visibility/object keys in metadata. Do not proxy 50 MB through app servers or process synchronously. Deletion first denies metadata/access and invalidates CDN, then deletes all variants asynchronously. Measure upload success, processing lag, failure, orphan objects, CDN hit. Build signed upload plus one thumbnail worker.

## 06 Chat
WebSocket gateways provide live transport; durable message store/log provides truth and offline replay. Assign a server sequence per conversation after append; client message ID makes send idempotent. Recipient cursor supports delivered/read/offline sync. Presence is TTL-based approximate state, never delivery truth. Global ordering is unnecessary; 100k-member groups persist once and fan out only to active clients/notification policy. Measure durable append/fanout lag, reconnect sync, hot-room partitions. Build one room, reconnect cursor, duplicate send test.

## 07 News Feed
Posts are truth and feeds are derived projections. Push fanout for normal accounts gives fast reads; pull/merge celebrity timelines to avoid 50M writes; hybrid selects by follower threshold. Store feed references, hydrate current post/visibility, and cursor paginate. Search/cache cannot be source because deletes/privacy must propagate. State 30-second freshness rather than false strict consistency. Measure post-to-feed lag, fanout backlog, feed p99, delete propagation, hot author impact. Build chronological feed before ranking.

## 08 Checkout
One transaction creates idempotent order, conditional inventory hold, and outbox event. A workflow performs payment/fulfillment with guarded state transitions; provider event ID deduplicates callbacks. Reconciliation compares external settlement to internal immutable records. Do not call payment inside inventory transaction; locks and remote failure create outage. Do not decrement inventory after payment without reservation. Measure hold expiry, duplicate checkout, payment lag/error, mismatch, oversell invariant. Build an order state machine and simulated provider retries.

## 09 Search and Autocomplete
Catalog DB/outbox drives a versioned derived search index; query applies tenant/visibility filters and ranking. Autocomplete is a separate bounded prefix path with debounce/cache. Reindex into a new index then atomically swap alias. Search is not authoritative: index lag and deletion repair exist; publish a five-minute freshness target. Avoid relational wildcard scans at scale. Measure index lag, query p99, zero-result/relevance quality, authorization leak tests. Build an indexer and blue/green reindex simulation.

## 10 Seat Reservation
Authoritative seat row atomically transitions `AVAILABLE → HELD(hold, expiry) → SOLD`; only current unexpired hold can confirm. Waiting room issues signed admission tokens and limits safe arrival rate. Payment is a saga; expiry/release is idempotent. Never check then update availability, and never use cache as sale arbiter. Measure hold conflicts, lock waits, expiry, payment-before-expiry, double-sell invariant. Build conditional SQL hold and concurrent race test.

## 11 Web Crawler
Normalize URLs then deduplicate URL hash; host-partitioned frontier applies robots and per-host token bucket; fetchers store content hash and extract links. Schedule recrawls by change/importance/error backoff. One global queue violates politeness and lets a host dominate. URL and content dedupe solve different problems. Measure frontier age, host error, politeness violation, dedupe ratio, bytes. Build a local host-aware frontier first.

## 12 Workflow Scheduler
Persist workflow/job state, retry policy, timer, and lease/fencing token. Workers claim ready work under a lease; only current lease can complete; expiry enables recovery. Durable timers replace sleeping threads; human approval is a persisted wait. Exactly-once execution is impossible around uncertain side effects, so activities need idempotency. Measure schedule lateness, task age, retry/DLQ, lease reclaim, workflow age. Build a two-step workflow with worker crash simulation.

## 13 Metrics Platform
Ingest validates tenant/schema/quota, appends to WAL/stream and write-optimized time-series blocks partitioned by tenant/time/series. Retain high-resolution recent data, compact/downsample older data, and evaluate alert rules. Cap active series; labels like user/request ID create a cardinality incident. Metrics are not exact billing records. Measure accepted/rejected samples, active series, compaction lag, query p99, alert delay. Build a counter/histogram ingest and tenant cardinality guard.

## 14 Logging Platform
Agents batch/spool structured logs to durable ingest; index common fields/time partitions and retrieve chunks for bounded query. Redact sensitive fields before/at ingest; enforce tenant query ACL/audit and retention lifecycle. Logging must not synchronously block product requests. Bounded local disk buffer sheds under backend outage. Do not index every arbitrary field forever. Measure loss/buffer fullness, index lag, query cost, redaction failures. Build structured logs correlated with trace ID.

## 15 Drive
Object storage holds immutable file versions; relational metadata represents current version, folders, ACL, trash, and change cursor. Direct resumable upload reduces API bandwidth; outbox powers sync/index/scanning. Offline clients sync from cursor and create conflict copy/domain merge rather than silent overwrite. Object key is not permission. Measure sync success, conflict rate, orphan objects, ACL denial, delete propagation. Build versioned metadata and two-client conflict test.

## 16 Video on Demand
Source object triggers asynchronous validation/transcoding into bitrate/resolution segments and manifest; CDN serves signed/authorized manifest and immutable segments. Player adapts bitrate to bandwidth/buffer. Playback analytics is asynchronous. One source file through app servers cannot provide global adaptive delivery. Measure start time, rebuffer ratio, encoding lag/failure, CDN hit, origin egress, entitlement denial. Build one source-to-HLS-like derivative flow conceptually.

## 17 Payment Ledger
Post immutable balanced double-entry journal lines in one transaction; balance is derived/materialized and checked. Idempotency/provider reference prevents duplicate postings; corrections are reversing entries, not edits. Spend authorization uses strong transactional available-balance check; reconciliation imports external settlement as evidence/correction. A mutable balance field alone loses audit and recovery. Measure balance invariant, duplicate rejection, reconciliation mismatch, posting p99. Build journal plus replayed transfer test.

## 18 Distributed Cache
Client routes keys through consistent-hash ring with virtual nodes; TTL/eviction bound memory; short client deadline and coalesced source fallback prevent outage cascade. Replication can improve reads but complicates invalidation. Hot keys need near-cache/replicas/prewarm/coalescing; uniform TTL causes expiry herd. Cache is never truth. Measure hit/eviction/memory, skew, node error, source fallback, rebalance movement. Build a simple ring and node-loss simulation.

## 19 Feature Flags
Audited control plane stores typed/versioned rules; distribution pushes/polls snapshots to SDK local cache; request evaluation is local and has visible staleness. Flags require owner/default/expiry and kill-switch policy. Central request-time evaluation makes every request depend on control plane. Targeting uses validated context and RBAC-protected change audit. Measure propagation/staleness, evaluation errors/latency, stale flags. Build local evaluator with percentage hash and snapshot fallback.

## 20 Ride Dispatch
Location stream updates an ephemeral geo-cell index; trip DB holds durable request/assignment/payment state. Dispatch queries adjacent cells, ranks candidates, offers a short lease, and conditionally assigns first accept. Location is approximate and TTL’d; assignment is strongly guarded. Raw full-table geo scans do not scale; location store should not arbitrate trip state. Measure location freshness, candidate p99, offer races, assignment time, hot cells. Build cell-neighbor lookup and assignment race test.

## 21 Multi-Tenant API Gateway
Gateway handles TLS, authentication validation, route/version policy, quota/body/deadline limits, tracing, and upstream routing; services re-authorize business/resource access and enforce tenant-scoped queries. Cache keys/config safely and define identity-control-plane outage behavior. Do not put all business logic in gateway or trust a caller-provided tenant header. Measure auth/quotas, upstream p99/error, tenant saturation, config staleness. Build route-level token bucket and trace propagation.
