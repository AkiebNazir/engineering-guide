# 21 System Design Architecture Blueprints

Use this alongside the questions and solutions. Each blueprint captures the missing interview detail: source of truth, contract, ordering, failure boundary, and scale trigger.

## 01 URL Shortener
**Truth:** `Link(code, destination, status)` in a durable DB. **Contract:** idempotent create; `GET /{code}` returns mutable `302`. **Flow:** cache-aside redirect; click event is asynchronous. **Hard part:** code uniqueness/custom aliases use a DB unique constraint. **Scale trigger:** redirect DB reads → CDN/cache, then partition by code hash. **Never:** make analytics synchronous or cache mappings forever.

## 02 Rate Limiter
**Truth:** atomic bucket state with refill timestamp. **Contract:** return allow/deny, remaining quota, retry-after. **Flow:** gateway spends token before expensive backend work. **Hard part:** compose global/tenant/route policies without double-counting; failure policy differs by endpoint. **Scale trigger:** shared limiter QPS → shard by actor hash and add local approximate pre-limit. **Never:** let each app instance enforce an independent global quota.

## 03 Pastebin
**Truth:** metadata/ACL/expiry DB record; body object. **Contract:** create is idempotent; read authorizes private resource before body fetch. **Flow:** public body via CDN; private through signed short-lived access. **Hard part:** expiry/abuse state overrides stale cache. **Scale trigger:** public reads → edge caching; body growth → object lifecycle tiers. **Never:** use unlisted URL as authorization.

## 04 Notification Platform
**Truth:** notification intent and delivery-attempt state. **Contract:** product emits intent, not “send exactly once.” **Flow:** preference decision → priority queue → channel worker → provider callback. **Hard part:** idempotent provider outcome and distinct urgent/bulk capacity. **Scale trigger:** campaign fanout → batch/partition recipient expansion. **Never:** let a marketing campaign share a queue/pool with password reset.

## 05 Photo Pipeline
**Truth:** media metadata/state; object store holds bytes. **Contract:** upload session is resumable/idempotent; readiness is explicit state. **Flow:** direct upload → scan → transform event → variants. **Hard part:** delete denies serving first then asynchronously removes every derivative. **Scale trigger:** transform queue backlog → autoscaled workers by format/size class. **Never:** trust filename/MIME or proxy all bytes through API.

## 06 Chat
**Truth:** durably appended per-conversation messages. **Contract:** client message ID is idempotency key; sequence cursor syncs history. **Flow:** gateway authorizes → append → online fanout/notification. **Hard part:** order only per room and make read receipts monotonic. **Scale trigger:** hot group → partition delivery/read fanout, not message truth. **Never:** treat live sockets/presence as durable delivery proof.

## 07 News Feed
**Truth:** posts and follows. **Contract:** feed has bounded freshness; cursor is stable. **Flow:** post outbox → fanout projection; read hydrates references. **Hard part:** hybrid push/pull for celebrity accounts and privacy deletion repair. **Scale trigger:** fanout write amplification → pull celebrity timelines at read. **Never:** duplicate full post data into every feed as permanent truth.

## 08 Checkout
**Truth:** order, inventory reservation, and financial journal. **Contract:** checkout idempotency key yields one order outcome. **Flow:** local transaction creates pending order/hold/outbox → payment saga → guarded state transition. **Hard part:** late/duplicate callback and compensation release. **Scale trigger:** inventory hot SKU → serialized/partition-aware allocation policy. **Never:** hold DB locks while calling payment provider.

## 09 Search and Autocomplete
**Truth:** catalog; index is rebuildable projection. **Contract:** state freshness target and permission filtering. **Flow:** catalog change → idempotent indexer → versioned index; query uses filters/ranking. **Hard part:** deletion/reindex without search leak. **Scale trigger:** autocomplete QPS → prefix cache/debounce. **Never:** declare search immediately consistent without a synchronization design.

## 10 Seat Reservation
**Truth:** seat state in transactional DB. **Contract:** hold token owns a short expiry; confirm only current hold. **Flow:** admission token → conditional seat hold → payment → sold. **Hard part:** race between expiry, payment, and concurrent buyers. **Scale trigger:** hot event → virtual waiting room and partition by venue/section. **Never:** read seat availability from cache then write it later.

## 11 Web Crawler
**Truth:** URL crawl state, content object/hash, robots/politeness state. **Contract:** URL normalization/version and per-host schedule. **Flow:** discovery → dedupe → host frontier → fetch → extract. **Hard part:** host-level rate policy and canonicalization that does not lose pages. **Scale trigger:** URL frontier → host partitions and distributed dedupe. **Never:** use one global FIFO or ignore terms/robots.

## 12 Workflow Scheduler
**Truth:** durable workflow state/task/lease. **Contract:** workflow steps are idempotent; task completion requires valid lease/fencing. **Flow:** timer/schedule generates task → worker activity → guarded next state. **Hard part:** crash after external side effect before acknowledgement. **Scale trigger:** task volume → shard queues by workflow/tenant class. **Never:** claim exactly-once without idempotent activities.

## 13 Metrics Platform
**Truth:** accepted timestamped samples in durable time-series blocks. **Contract:** labels/quotas are validated at ingest; queries have range/cardinality limits. **Flow:** agent → ingest/WAL → compacted store → query/alert. **Hard part:** active-series cardinality protection. **Scale trigger:** ingest → partition by tenant/time/series; downsample old data. **Never:** use metrics as audit-grade billing truth.

## 14 Logging Platform
**Truth:** durable log chunks; index is derived. **Contract:** structured schema and retention/ACL policy. **Flow:** agent buffer → ingest → chunks/index → bounded search. **Hard part:** redaction before broad access and bounded disk backpressure. **Scale trigger:** query/index cost → time/tenant partition plus tiered retention. **Never:** synchronously block user requests on logging.

## 15 Drive
**Truth:** immutable object versions plus metadata/ACL graph. **Contract:** sync cursor and version conflict semantics. **Flow:** direct upload → metadata transaction/outbox → device change feed. **Hard part:** offline concurrent edit conflict and delete/restore lifecycle. **Scale trigger:** metadata listing/sync → indexed per-folder/per-user change log. **Never:** make object key a permission token.

## 16 Video on Demand
**Truth:** source/derivative metadata and objects. **Contract:** playback entitlement authorizes manifest; encode state is explicit. **Flow:** upload → transcode ladder → manifests/segments → CDN/player. **Hard part:** quality adaptation and asynchronous encode failure/retry. **Scale trigger:** global playback → CDN origin shielding and rendition optimization. **Never:** serve original through application servers for each viewer.

## 17 Payment Ledger
**Truth:** immutable balanced journal postings. **Contract:** idempotent transfer/provider reference; corrections are new postings. **Flow:** transaction posts debit/credit → balance projection/outbox → reconciliation. **Hard part:** strong available-funds check and external mismatch. **Scale trigger:** account posting throughput → partition with careful per-account serialization. **Never:** overwrite balance/history as the only financial record.

## 18 Distributed Cache
**Truth:** external source database; cache is disposable. **Contract:** client has short timeout and TTL/stale policy. **Flow:** consistent-hash route → node/replica → coalesced source fallback. **Hard part:** hot key, expiry herd, node-loss miss storm. **Scale trigger:** add virtual nodes/replicas/local cache. **Never:** make eviction/restart mean data loss of business truth.

## 19 Feature Flags
**Truth:** versioned audited flag configuration. **Contract:** SDK evaluates a locally cached snapshot and reports staleness. **Flow:** control-plane change → validated distribution → SDK poll/stream → local evaluation. **Hard part:** safe kill-switch default during stale config/control outage. **Scale trigger:** many SDKs → CDN/stream fanout and segmented snapshots. **Never:** add remote lookup to every request or let flags live forever.

## 20 Ride Dispatch
**Truth:** transactional trip/assignment; location index is ephemeral. **Contract:** offer lease plus conditional first acceptance. **Flow:** driver location stream → geo cells; rider request → candidates → atomic assignment → realtime updates. **Hard part:** late accept/disconnect and dense-cell hotspot. **Scale trigger:** cell subdivision/region dispatch partitions. **Never:** choose a driver from stale location without assignment guard.

## 21 Multi-Tenant API Gateway
**Truth:** identity/policy/config control plane; services remain truth for resource permissions. **Contract:** gateway verifies token, quota, deadline, route/version; backend re-authorizes. **Flow:** edge → policy/cache → gateway → isolated service/data path. **Hard part:** identity/config outage and tenant noisy-neighbor limits. **Scale trigger:** route/tenant traffic → distributed quota and partitioned policy/config distribution. **Never:** centralize all domain logic or trust caller-supplied tenant ID.

## How to use each blueprint

Before reviewing a solution, replace each bold label with your own answer. Then force one changed condition: strict multi-region consistency, 100× traffic, no cache, a dependency outage, or regulated data. If your architecture still has a precise source of truth, idempotent mutations, bounded failure, and evidence, you are learning system design rather than reciting it.
