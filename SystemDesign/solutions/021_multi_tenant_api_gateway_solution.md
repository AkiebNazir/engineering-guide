# 021 — Multi-Tenant API Gateway: Full System Design Solution

## Goal and contract

An <abbr title="Application Programming Interface">API</abbr> gateway is the single edge every external and internal-tenant request passes through before reaching backend services. The invariant is not "the gateway secures everything" — it is: the gateway verifies identity, enforces route/version policy, quota, and deadlines, and propagates trustworthy tenant/tracing context, while backend services remain the source of truth for fine-grained resource authorization and never trust a caller-supplied tenant identifier as-is.

The question's numbers are the contract: **500k requests/s** at peak, **800 tenants**, **300 APIs × about 3 live versions** (900 pairs), **added gateway latency p99 under 10 ms** (upstream time excluded), **per-tenant quota accurate within a 1-second window**, **zero-downtime route and version changes**.

Promised: authenticated, entitled, quota-counted requests (within 5%, derived below), forwarded with a verified tenant identity, trace ID and deadline; no tenant consumes another's capacity. Not promised: resource-level authorization (backends own it, because only they have the domain model), exact cross-region counts, instant config convergence (about 5 s). The hard decision: keep every shared service off the request path. Route, entitlement, token check, quota and concurrency are answered from node memory (a pushed immutable config snapshot, cached keys, local token buckets refilled by short leases), so the 10 ms budget and availability never depend on a network call to a shared store.

## Estimates

Everything beyond the question's constraints is a labelled assumption.

- **Skew.** 500k ÷ 800 = 625 rps average, but assume the top 20 tenants carry 60%: 300k ÷ 20 = **15k rps each**; the other 780 average 200k ÷ 780 = **256 rps**. So quotas must work at both scales.
- **Fleet.** Assume 20k rps per 8-vCPU node with <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr>, <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> and mTLS (load-test it first). 500k ÷ 60 ÷ 20k = 42% <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>, and **62.5%** after losing a zone (500k ÷ 40 ÷ 20k). So headroom, not throughput (25 nodes would be 100% busy), sizes it: **60 nodes, 20 per zone**. At an assumed 1 KB in and 4 KB out per request, a node moves about 0.67 Gbps, so NICs do not bind.
- **Route table.** 900 pairs × an assumed 30 operations = 27,000 routes × 1 KB = 27 MB; entitlements 800 × 300 × 100 B = 24 MB; about 50 MB. So config sits in every node's memory (twice during a swap) and lookup is a hash plus radix walk (~1 µs). A full push is 50 MB × 60 = 3 GB but one <abbr title="Application Programming Interface">API</abbr> version's delta is 30 KB × 60 = 1.8 MB, so push deltas.
- **Auth <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>.** At an assumed 100 µs per ES256 verify, even uncached 8.3k rps × 100 µs = 0.83 core of 8, so verification is not the bottleneck; an invalid-token flood is the risk.
- **Quota state.** 800 buckets × 32 B = 26 KB, yet a central check per request is 500k ops/s plus a round trip. With 25 ms leases each active (tenant, node) pair renews at most 40 times/s: about 3 nodes per tenant gives 2,400 pairs × 40 = **96k ops/s** (2,400 batched RPCs/s). So the shared service is tiny; the issue is latency and availability coupling.

## <abbr title="Application Programming Interface">API</abbr>

```text
ANY  https://{tenant}.api.example.com/{api}/v{n}/...    Authorization: Bearer <JWT>
     optional: X-Api-Version (else tenant pin, else API default), traceparent, Idempotency-Key (passed through)
     → backend response + X-Request-Id | 401 INVALID_TOKEN | 403 NOT_ENTITLED, MISSING_SCOPE | 404 NO_ROUTE
       | 410 VERSION_SUNSET | 413 | 429 TENANT_QUOTA, CONCURRENCY + Retry-After | 502/503 | 504 DEADLINE
To backend (mTLS): x-gw-tenant, x-gw-principal, x-gw-scopes, x-gw-api-version, x-gw-deadline-ms, traceparent
POST /v1/snapshots {base, changes[]}  Idempotency-Key → 201 {snapshot_id, VALIDATING} | 409 STALE_BASE    # control plane
POST /v1/snapshots/{id}/rollout {stages: [node, zone, fleet], bake_s} → 202    # and /rollback
PUT  /v1/tenants/{t}/policy {quota_rps, burst_ms, concurrency_share};  PUT .../entitlements/{api} {allowed_versions, pinned}
GET  /v1/fleet/status?cursor → [{node, snapshot_id, staleness_s}]
```

Every mutation creates a snapshot; `base` gives optimistic concurrency. The gateway passes `Idempotency-Key` through and retries only routes flagged `retryable`. `429 CONCURRENCY` differs from `TENANT_QUOTA` because the fix differs; an unknown tenant and a bad token get the same 401, so tenants cannot be enumerated.

## Data model

| Entity | Fields | Role |
|---|---|---|
| `api_version`, `route`, `upstream_cluster` | `(api_id, version)`, `state` DRAFT→CANARY→ACTIVE→DEPRECATED→SUNSET; route `match{host, path_prefix, methods}`, `required_scopes`, `timeout_ms`, `retryable`; cluster `max_in_flight`, identity | **Truth** (config DB) |
| `tenant`, `tenant_policy`, `entitlement` | issuers `[{iss, jwks_uri, aud}]`, `quota_rps`, `burst_ms`, `concurrency_share`; `(tenant, api)` → `allowed_versions`, `pinned` | **Truth** |
| `snapshot`; node tables; lease bucket | id, `parent_id`, `content_hash`; radix tree, entitlement map; `tenant → {tokens, last_refill}` | Audit truth; **derived**; **soft state**, rebuilt empty |

**Partition key.** None for config: 50 MB and 200 changes/day fit one relational database plus a synchronous replica, so the problem is fan-out. The lease service partitions by `hash(tenant_id)` into 8 partitions (about 100 tenants each) to bound a loss ([partitioning](../building_blocks/25_partitioning_and_hot_keys.md)).

## Core mechanisms

| Mechanism | Behavior | Choose it when | Main weakness |
|---|---|---|---|
| Gateway-terminated auth (token validation) | Validates an auth token's signature/expiry and extracts a verified principal/tenant claim. | Always, at the edge. | If it also decides fine-grained resource access, it drifts from service-owned logic. |
| Distributed per-tenant quota | Token bucket per tenant: local buckets per node, refilled by short leases from a small shared service. | Always, for noisy-neighbor protection. | A per-request central counter adds a hop and shared fate; a static split is inaccurate under skew. |
| Route/version policy table | Config maps path/version to the correct upstream service and contract version. | Always, for hundreds of evolving APIs. | Stale policy can route to a wrong backend if distribution lags. |
| Deadline propagation | Gateway sets and forwards a request deadline; backend honors and propagates it. | Always, to bound tail latency. | Every hop must respect it, or one slow hop blows the budget. |
| Backend re-authorization | Service re-checks that the verified principal may act on the specific resource. | Always, for mutating or sensitive reads. | Duplicated per service, but the only place the domain check can be correct. |

## Architecture and data flow

```arch
%% caption: Every request is answered from node memory (config snapshot, cached keys, leased quota tokens); the control plane and lease service stay off the request path.
node client "Tenant clients" at 2,0 icon=users sub="Bearer JWT, TLS"
node ddos "DDoS filter" at 2,1 icon=shield sub="per-IP limits"
node lb "L4 balancer" at 2,2 icon=lb
group dp "Gateway fleet: 60 nodes, 3 zones" color=purple icon=region
node snap "Config snapshot" at 1,3 in dp icon=layers sub="routes, entitlements, keys"
node gw "Gateway node" at 2,3 in dp icon=gateway sub="JWT, route, deadline"
node bkt "Quota buckets" at 3,3 in dp icon=counter sub="local tokens, conc. caps"
node be "Backend services" at 2,4 icon=service sub="re-authorize, tenant-scoped"
node lease "Lease service" at 3,4 icon=kv sub="8 partitions by tenant"
group cp "Control plane" color=slate icon=scheduler
node jwks "Issuer JWKS" at 0,2 in cp icon=key sub="800 issuers, 60 s poll"
node ctl "Snapshot compiler" at 0,3 in cp icon=workflow sub="validate, canary, rollback"
node cfg "Config DB" at 0,4 in cp icon=sql sub="+ sync replica"
client -> ddos -> lb -> gw
gw -> be : "mTLS + verified claim"
snap -- gw
gw -- bkt
bkt <..> lease : "25 ms leases"
jwks ..> ctl : "key changes"
cfg -> ctl
ctl ..> snap : "xDS deltas, ACK/NACK"
```

```arch
%% caption: The gateway forwards the verified claim extracted from the token — never a raw header the caller could set themselves.
node client "Client" at 0,1
node gw "Edge / gateway\nvalidate auth token\nset deadline" at 1,1
node policy "Route policy\n(cached)\nresolve route + version" at 2,0
node quota "Quota buckets\ncheck safety buckets" at 2,2
node backend "Upstream backend service\nre-authorize\ntenant-scoped data access" at 3,1

client -> gw
gw -> policy
gw -> quota
gw -> backend
backend -> gw
gw -> client
```

**One request.** Strip inbound `x-gw-*`, verify the <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr>, resolve route and version, check entitlement and scopes, take a local quota token and a concurrency slot, set the deadline, forward on a pooled mTLS connection, all from node memory. **One config change.** The control plane validates and compiles snapshot 813 and canaries it on one node, a zone, then the fleet; each node swaps one pointer, so in-flight requests finish on 812 and new ones see 813.

The hard decision is what identity the backend trusts: the *verified* claim from the validated token, never a raw header the caller could set, with every backend query scoped by it rather than a `tenant_id` in the body. That costs a little duplicated plumbing and closes the commonest multi-tenant hole, cross-tenant access via a spoofed identifier. The second is splitting policy (route, quota tier) from domain authorization: merged, the gateway must know every service's data model and goes wrong when their rules change.

## Capacity and storage

Three zones × 20 nodes behind an L4 balancer. Per node: two snapshots (100 MB), a token cache (assume 50k × 500 B = 25 MB) and 14,400 upstream connections (900 clusters × 8 endpoints × 2, about 0.6 GB at 40 KB each) in 16 GB. At an assumed 200 changes/day, full snapshots are 73,000/yr × 50 MB = 3.7 TB but 30 KB deltas are 2.2 GB. Logs at 500k/s × 300 B = 150 MB/s = **13 TB/day** are unaffordable, so keep every non-2xx, 429 and slow request plus 1% of successes (about 2%, 0.26 TB/day), with metrics and 0.1% sampled traces for the rest.

## Control plane and config distribution

The data plane must converge on the same routes and policies within seconds, atomically, with the control plane never on the request path.

| Approach | Convergence | If the control plane dies | Cost |
|---|---|---|---|
| Look up config per request | Immediate | Every request fails | 500k lookups/s plus a hop |
| Nodes poll object storage for the whole file | Up to one poll interval | Keep the last file | 3 GB per version; no NACK |
| Push versioned deltas over streams with ACK/NACK (xDS-style) | About 1–5 s (assumed) | Keep the last snapshot | 60 streams, 1.8 MB per change |

Push wins: fast, observable convergence plus a stop signal, at the cost of a streaming server off the request path. Envoy's xDS protocol is the documented reference: versioned resources, ACK or NACK, make-before-break ordering (clusters before the routes that reference them).

1. **Validate.** Schema; every route's cluster exists and has a healthy endpoint; no shadowed routes; nothing the parent's routes still reference may disappear.
2. **Apply.** Build tables off the request thread, swap one pointer, ACK. In-flight requests keep the old tables. Any NACK halts the rollout.
3. **Canary.** One node for 5 minutes, a zone, then the fleet, comparing 5xx and latency with un-updated nodes and auto-rolling back. Nodes keep five snapshots, so rollback is fast.
4. **Restart.** Nodes persist the last good snapshot and boot from disk. Alarm at 60 s of staleness.

Nodes hold N and N+1 for seconds, so changes must be safe beside the parent: expand, shift traffic, contract.

## Authentication and identity propagation

Checks run cheapest first, so floods die early:

1. **Shape and key.** Header at most 8 KB; `alg` from the issuer's allow-list (ES256 or RS256), never `none`; `kid` found in cached JWKS (RFC 7517). Per RFC 8725 (<abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> best practices, 2020), the token does not choose how it is verified.
2. **Signature.** Verify (about 100 µs, assumed) or hit a cache keyed by SHA-256 of the token for min(`exp`, 60 s).
3. **Claims.** `iss` maps to a tenant, `aud` is this gateway, `exp` and `nbf` with 30 s leeway, and the `tenant_id` claim equals the tenant owning `iss`, so one tenant's identity provider cannot mint tokens for another.
4. **Policy.** Required scopes are a subset of the token's; `(tenant, api, version)` is entitled. Coarse authorization only.
5. **Headers.** Strip every inbound `x-gw-*`, then set them from verified claims.

**Keys.** The control plane polls the 800 JWKS endpoints every 60 s (13 fetches/s) and ships changes in the snapshot stream, so nodes make no outbound calls and an unknown `kid` cannot force a fetch. Issuers publish a key 5 minutes before signing with it and retire the old one after the longest token lifetime (15 minutes, assumed); failed fetches keep the last good keys (24 hours, assumed).

**Revocation.** A <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> cannot be revoked before `exp`, so use 5–15 minute lifetimes plus a snapshot deny-list. Opaque tokens with introspection (RFC 7662) revoke instantly but need a call per request; at 500k rps and 10 ms we choose JWTs.

**Toward backends.** mTLS with short-lived workload certificates (SPIFFE-style identities); each backend checks it is talking to the gateway before trusting `x-gw-*`. For multi-hop calls the gateway can mint a signed 60 s internal token per target service so each hop verifies instead of trusts: at an assumed 40 µs per signature, 500k × 40 µs = 20 cores fleet-wide.

## Per-tenant allowances: leased token buckets

A tenant with quota L must be admitted at most about L per second across all 60 nodes, with no network call per request.

| Approach | Accuracy over 1 s | Hot-path cost | If the shared part fails |
|---|---|---|---|
| Central counter per request (Redis `INCR`) | Exact | Round trip (assume 1–3 ms p99), 500k ops/s | Fail open (abuse) or closed (outage) |
| Static split, L ÷ nodes | Only if traffic is even | None | Skew is common: long-lived <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/2 connections pin clients to few nodes |
| **Local buckets, leased allowances** | ±5% by construction | One atomic decrement | Falls back to a static share |

Leases give near-exact counts with no hot-path hop, at the cost of a bounded error and a small stateful service, acceptable because its failure costs accuracy, not availability. (A fixed one-second window would admit up to 2L across a window edge.) Google's open-source Doorman (from YouTube) uses time-limited capacity leases the same way.

**Protocol.** The lease service keeps a bucket per tenant: refill L per second, capacity C = L × `burst_ms` (default 25 ms). Before local tokens fall under half the last grant, a node asks for `EWMA_rate × τ` tokens (τ = 25 ms), returning unspent ones; the service grants what is available (proportionally if asks exceed it) and grants expire after τ. On an empty bucket a request waits up to 2 ms for a renewal, then gets `429 TENANT_QUOTA`.

**Error bound.** A token lives from grant to τ later, so anything admitted in [t, t+W] was granted in [t−τ, t+W]: at most L × (W + τ) + C. Over-admission is at most (τ + burst_ms) ÷ 1 s = 25 + 25 ms of allowance = **5%** in the worst window (750 requests for a 15k rps tenant). Under-admission comes only from tokens stranded on a node that lost its traffic, at most L × τ = 2.5%. The floor is the lease round trip: at a 3 ms p99, τ under about 12 ms waits on renewals, so about ±2.5% is the best this design does; tighter needs the central counter.

**Small tenants.** If L × 25 ms is under one token (L below 40 rps) leases cannot amortise, so those tenants use the exact per-request path (at most 40 ops/s each). **Degraded mode.** With the lease service unreachable, each node uses static share L ÷ k over the tenant's live nodes. If traffic splits 50/30/20 over three nodes, the busy node admits 1/3 L of its 0.5 L, so a tenant sending exactly L gets 0.33 + 0.30 + 0.20 = 0.83 L: a 17% shortfall, never over-admission. Reject excess rather than queue it.

## Latency budget for the 10 ms p99

Assumes 99% of requests use warm connections and a native (no GC) proxy. Values are p99 contributions in ms; p99s do not add, so the sum is conservative.

| Stage | ms | Notes |
|---|---|---|
| Accept, TLS records, HTTP parse | 0.5 | Symmetric crypto only; handshakes amortise |
| JWT cache hit, route, entitlement, quota, concurrency | 0.2 | Hash lookups, atomic decrements |
| CPU queueing | 1.0 | Erlang C, below |
| Trace, deadline, headers, response path | 0.4 | |
| Extra network hop, same zone | 0.5 | Cross-zone costs 1–2 ms: prefer same-zone |
| Upstream write, jitter reserve | 1.2 | |
| **Typical p99** | **≈ 3.8** | |
| Cold paths, if hit | up to about 3 | New upstream mTLS handshake (2–3 ms), or a 2 ms lease wait |

**Queueing is the term that blows up.** Service time is 8 cores ÷ 20k rps = 0.4 ms per core, and the M/M/8 (Erlang C) p99 wait is 0.07 ms at 42% utilisation, 0.38 ms at 62.5%, 1.35 ms at 85% and 4.4 ms at 95%. Real service times have heavy tails, so reserve 1 ms and cap utilisation near 60% even after a zone loss; see [overload control](../building_blocks/28_overload_control_and_graceful_degradation.md).

## Noisy-neighbor isolation

A quota stops a tenant sending too much, not one that stays within quota but is slow: in-flight work is rate × latency (Little's law), so 5,000 rps × 0.1 s = 500 in flight but 5,000 × 5 s = **25,000** when a backend slows to 5 s. Four layers, each covering a gap in the last:

| Layer | Stops | Numbers |
|---|---|---|
| Per-tenant quota | Sustained excess | ±5% |
| Concurrency cap per (tenant, upstream cluster) | Slow calls filling shared pools | 2 × 500 = 1,000 fleet-wide, about 333 per node; borrow idle capacity until the cluster is 70% busy |
| Weighted fair queue under <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> saturation | One tenant crowding the worker queue | Per-tenant queues, deficit round-robin, drop expired deadlines |
| Shuffle sharding onto node subsets | Poison or flood traffic reaching every node | Below |

**Shuffle sharding** (the Amazon Builders' Library technique for workload isolation): each tenant gets its own hostname resolving to a rendezvous-hashed subset of k = max(3, ⌈peak rps ÷ 5,000⌉) nodes across zones. With 3 nodes, one per zone, there are 20³ = 8,000 subsets: another tenant has the identical one with probability 1/8,000, and 1 − (19/20)³ = 14% of tenants (about 114) share one node and lose one of three, which retries absorb. An abusive tenant hurts at most 3 of 60 nodes. It needs per-tenant hostnames or SNI routing; without them, rely on the other layers.

**Limits.** Unauthenticated floods cannot be attributed to a tenant, so per-<abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> limits and DDoS filtering sit in front. Rejection after <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr>, parse and verify costs about half a served request (assumed): a 100× spike from a 5k rps tenant is 500k rps of rejects, about 250k request-equivalents, 21% of the 1.2M rps fleet if spread everywhere but 417% of the tenant's 3-node subset (250k ÷ 60k), which saturates only that subset. Retries use a budget of about 10% ([resilience patterns](../building_blocks/12_application_resilience_patterns.md)).

## Zero-downtime version and route changes

1. **Add.** Ship the cluster and a disabled route, verify a healthy endpoint, enable it for explicit `X-Api-Version` (testers), then shift the default by weight (1% → 10% → 50% → 100%) or tenant cohort.
2. **Change.** A route edit is a new snapshot; connections are not dropped.
3. **Remove.** Mark DEPRECATED with `Deprecation` and `Sunset` headers (the latter is RFC 8594), track requests per tenant and version, return `410 VERSION_SUNSET` for a grace week, then delete the route, and the backend after 14 quiet days.
4. **Roll back.** Re-point to the parent snapshot (about 5 s).

## Failure and abuse behavior

| Case | Correct behavior |
|---|---|
| Identity/auth control plane unreachable | Serve from last cached valid signing keys/policy within a bounded staleness window; never accept unverifiable tokens. |
| Config distribution lags, or the control plane is down | Route on the previous known-good snapshot, never a partial one; nodes restart from disk. |
| One tenant spikes traffic 100x | Its quota bucket throttles that tenant; global safety and per-route buckets protect shared backends; concurrency caps and the 3-node subset contain the rest. |
| Caller sends a forged `X-Tenant-Id` header | Ignored; tenant scope comes only from the verified token's claim. |
| Backend service is slow/degraded | Deadline bounds the wait with a clean error; concurrency caps stop one tenant filling the pool; outlier ejection avoids bad endpoints. |
| Sensitive route (admin/export) hit at high volume, or a backend skips its authorization check | Stricter per-route quota; gateway checks are necessary but not sufficient, so backend re-authorization is mandatory. |
| Lease service partition lost | Its tenants (about 100) use static share L ÷ k: at worst the 17% shortfall, never over-admission. A replica takes over in seconds with an empty bucket. |
| Bad snapshot (schema-valid but wrong) or bad gateway binary | Validation and NACK catch structural errors; the canary catches semantic ones (5xx, latency, route-hit mix) and rolls back in one propagation time; a poison request crashes at most its tenant's 3 nodes. |
| Zone loss | 20 of 60 nodes gone, the other 40 at 62.5% <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>, each tenant loses one of three nodes, leases resize within 25 ms. |
| Region loss | <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> moves traffic to another region's fleet, with its own lease service and a config replica. |

## Observability and interview close

Measure auth failures, quota rejects by tenant, upstream p99 and errors, config staleness per node, and deadline-exceeded rate. Add **gateway-added latency** (total minus upstream time, per route), a **quota-accuracy audit** (admitted per tenant per second across nodes against L; flag above 110%), lease grant latency and fallbacks, and each tenant's spread across its nodes.

**The one paging alert:** gateway-added p99 above 10 ms for 5 minutes, the promise made to every tenant. Quota audit, staleness and lease fallback are tickets; a snapshot NACK halts its own rollout.

Interview close: "The gateway owns everything that's identical across every <abbr title="Application Programming Interface">API</abbr> — auth, quota, routing, deadlines, tracing — and stops exactly at business authorization, because only the owning service can correctly answer 'can this principal touch this resource.' Tenant identity always comes from the verified token claim, never from anything the caller can set directly, because that's the one shortcut that turns a convenience header into a cross-tenant data leak."

Trade-off to state: "I keep every shared service off the request path: pushed immutable config snapshots and local quota buckets with 25 ms leases. That meets 10 ms and survives the control plane dying, and costs a bounded 5% quota error and seconds of config staleness, which the requirements tolerate."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Each region runs its own fleet, lease service and config replica behind GeoDNS. A tenant's quota L splits into regional allocations L_r = L × w_r, rebalanced every 1–5 s by a global allocator (leases one level up); a partitioned region keeps its last allocation, safe because allocations sum to at most L. A synchronous cross-region counter costs 50–100 ms and breaks the budget. See [multi-region traffic](../building_blocks/27_multi_region_and_global_traffic.md).
2. **"What changes at 10× and 100×?"** At 5M rps I need about 600 nodes and lease load stays near 100–120k ops/s, since it scales with (tenant, node) pairs. Fan-out and blast radius break first: add a relay tier between control plane and nodes. At 50M rps, split into cells of about 100 nodes, each with its own lease service and tenants.
3. **"What if quota must be exact, for example billing hard caps?"** Rate limits stay leased. A monthly cap uses local counters flushed about once a second, which can overshoot by roughly 60 nodes × 1 s of demand, so within the last 0.1% of the cap that tenant switches to a synchronous conditional decrement in a strongly consistent store: 2–5 ms (assumed), affordable for one tenant.
4. **"What does this cost?"** 480 vCPU (60 × 8) at an assumed $0.04 per vCPU-hour is about $14k a month. A per-request managed gateway at list prices on the order of $1–3.5 per million (verify current pricing) would be $0.5M–$1.8M a month at an assumed 200k rps average (5.3 × 10¹¹ requests a month). The real self-run cost is the platform team.
5. **"How do you handle abuse?"** Invalid-token floods die at the shape check, a token-hash negative cache and per-<abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> limits before any signature is verified; slow clients hit header, body and idle timeouts; authenticated abuse hits quota and concurrency caps. Volumetric attacks belong to the L3/L4 provider in front.
6. **"Why not Redis `INCR` per request? It is much simpler."** At 500k rps that is 500k ops/s (about 5 shards), a 1–3 ms p99 hop eating up to 30% of the budget, and shared fate for every tenant on a shard. If the interviewer insists, I accept it for tenants needing exact counts and keep leases for the rest; `Allow(tenant, n)` is the same interface, so the choice is reversible.

## Common mistakes

1. **A shared counter call on every request.** It puts a hop and a shared failure domain inside a 10 ms budget. Use local buckets with short leases and state the error bound.
2. **Splitting the limit as L ÷ nodes and calling it accurate.** Long-lived <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/2 connections concentrate a client on few nodes, so a tenant under its limit gets rejected. Use demand-sized leases; keep static shares for degraded mode.
3. **Rate limits with no concurrency caps.** Within its rate a tenant can still fill every backend connection when latency rises (500 in flight becomes 25,000). Cap concurrency per tenant per cluster, and size the fleet for zone-loss headroom (42% becomes 62.5%), not average <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>.
4. **Trusting `X-Tenant-Id` or forwarding inbound `x-gw-*` headers.** A caller sets them and reads another tenant's data. Strip them, derive tenant from the verified claim, and have backends check the gateway's mTLS identity.
5. **Fetching signing keys on the request path.** A slow issuer becomes a gateway outage, and an unknown `kid` forces fetches. Ship keys with the config and keep last-good keys.
6. **Mutating live route tables or pushing independent updates.** Requests see half a change, such as a route to a cluster that does not exist yet. Push immutable snapshots in make-before-break order and swap one pointer.

## Going from L5 to L6

- **Migration and rollout.** Run quotas in shadow mode (count and log, do not reject) for two weeks to calibrate limits from real traffic, then enforce tenant by tenant, with a tester route on the new gateway before any hostname moves. Every step rolls back by snapshot.
- **Cost model.** Compute is the small number (about $14k a month, against a managed $0.5M or more; both from assumed inputs); the platform team, on-call and the log pipeline are the real cost, and 2% log sampling cuts 13 TB/day to 0.26.
- **Ownership and blast radius.** The platform team owns the data plane and validators; <abbr title="Application Programming Interface">API</abbr> teams own routes through self-service changes that pass the same validation. Subsets, cells and zone-by-zone rollout confine failures to a slice of tenants.
- **Build versus buy.** Buy the proxy (an Envoy-class data plane with xDS); build validation, rollout and the lease service, since the isolation policy lives there. For one hostname and coarse limits, buy a managed gateway.
- **Phased evolution and what to measure first.** Start with an off-the-shelf gateway and a central limiter, adding leases once its hop and shared fate hurt. Measure first: per-node cost and queueing under load (validates 20k rps), each tenant's spread across nodes, config propagation time.

## Build exercise

Implement a route-level token bucket keyed by tenant id plus route, verify it rejects a spiking tenant while leaving other tenants' buckets unaffected, and propagate a trace/deadline context through a simulated gateway-to-backend call, asserting the backend receives and can check the remaining deadline.

Then extend it to the leased design: three gateway nodes, a lease service and an atomic-swap config store. Named assertions:

- `test_forged_tenant_header_ignored`: send `X-Tenant-Id: other` and `x-gw-tenant: other` with a valid `acme` token; the backend sees `acme` only.
- `test_spiking_tenant_isolated`: tenant A offers 100× its quota; tenant B at 50% has zero rejections.
- `test_lease_error_bound`: unbalanced traffic on three nodes, quota 10,000 rps, τ = 25 ms; over 100 one-second windows admitted stays within [0.95, 1.05] × 10,000 at 1.2× demand.
- `test_lease_service_down_static_share`: kill the lease service; total admitted never exceeds L, and a 50/30/20 split admits about 0.83 L.
- `test_snapshot_swap_is_atomic`: 8 threads route while 812 swaps to 813 (which needs a new cluster); no request sees a route without its cluster, and an unappliable snapshot produces a NACK.
- `test_deadline_and_concurrency`: `x-gw-deadline-ms` shrinks across hops and an expired request gets 504 before the backend; with one backend at 5 s, that tenant hits its cap while others succeed.
