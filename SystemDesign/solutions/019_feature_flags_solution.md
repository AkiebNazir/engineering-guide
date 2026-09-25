# 019 — Feature Flags: Full System Design Solution

## Goal and contract

A feature flag platform lets engineers control behavior at runtime — percentage rollouts, targeted segments, kill switches — without a deploy. The invariant is not "every request sees the latest flag state instantly" — it is: every request is evaluated against a locally cached, versioned, audited configuration snapshot, evaluation never blocks on a remote call, and staleness is bounded and visible rather than silent.

Every flag has an owner, a documented default (the value used when config can't be resolved), and ideally an expiry so temporary flags don't calcify into permanent untracked branches. Targeting rules evaluate against a validated context (plan tier, region, user id — never arbitrary unvalidated client input treated as trusted). Changing rules or rollout is a control-plane write through RBAC, logged with who/when/what-changed.

The question's numbers are the contract: **50B evaluations/day, 10,000 flags, 5,000 services, eval p99 < 1 ms with no network round trip, kill switch to all SDKs in < 10 s, and SDKs serving stale-but-valid config for ≥ 1 h of control-plane outage.** The hard decision: evaluation is a local function of a versioned snapshot, so all the engineering is in distribution, freshness and safety of that snapshot, not in serving evaluations.

## Estimates

- **Aggregate eval rate**: 50B ÷ 86,400 = **579K evals/s** average, ~1.7M/s at an assumed 3× peak; per service 579K ÷ 5,000 = 116/s average (a hot service may reach 50K/s). At ~1 µs per local evaluation the *entire fleet* burns 0.58 core-seconds per second (2.9 cores at 5 µs). → *Evaluation cost is irrelevant, which is why it is local. A central flag service would need 0.6–1.7M RPS, could not meet 1 ms p99 across a network hop, and its outage would be everyone's outage.*
- **Snapshot size**: 10,000 flags × ~1.5 KB (variations, rules, prerequisites, rollout, salt; assumption) = **15 MB raw, ~3 MB gzip (5:1)** org-wide. Scoped per project/environment (assume 200 projects, ~50 flags): **75 KB raw, ~15 KB gzip**. → *An SDK holds a per-environment snapshot of tens of KB, never the org's; a 1M-key user-list segment (20 MB) would blow that budget and needs a side store.*
- **Fleet size** (assumption): 5,000 services × ~20 instances = **100,000 SDK instances**.
- **Polling cost**: at a 5 s interval, 100K ÷ 5 = **20K req/s**. With `ETag` almost all are ~400 B `304`s: 20K × 400 B = **8 MB/s**; without it, full 15 KB bodies would be 300 MB/s (2.4 Gb/s). At 30 s: 3.3K req/s, but worst-case staleness is 30 s, which breaks the 10 s kill-switch target. → *Poll only as a fallback, served by relays.*
- **Streaming cost**: 100K long-lived connections ÷ 20 regional relays = **5K each**, easy. One flag change is ~1.5 KB per subscriber: worst case (org-wide flag) 100K × 1.5 KB = **150 MB**; scoped by project, the average change reaches ~500 SDKs = 750 KB. At an assumed 1,000 changes/day that is **0.75 GB/day**. Control-plane load is ~0.01 writes/s. → *Distribution is a fan-out problem, not a throughput one; control-plane outage does not touch evaluation.*
- **Kill-switch budget (10 s)**: commit ~50 ms + publish to relays ~250 ms + relay push to SDK ~500 ms + apply ~10 ms ≈ **0.8 s typical**; budget p99 3 s. If a stream is down, a 5 s fallback poll adds ≤ 5 s + fetch = ~6 s. → *10 s is met with margin only for SDKs that are connected or polling; alert on the share of SDKs fresh within 10 s.*
- **Event volume**: logging every evaluation = 579K × 200 B = 116 MB/s = **10 TB/day**, unaffordable. Aggregated summaries: 100K instances × ~2.4 KB per minute = **4 MB/s**. Per-user exposure events only for experiment flags (assume 5% of evals): 29K/s × 150 B = 4.3 MB/s = **375 GB/day**. → *Aggregate everything, log exposures only where analysis needs them.*
- **Bootstrap burst**: every instance restarting fetches ~15 KB gzip → 100K × 15 KB = 1.5 GB, absorbed by relays and a CDN; reconnects use jittered backoff.

## Core mechanisms

| Mechanism | Behavior | Choose it when | Main weakness |
|---|---|---|---|
| Central control plane (typed, versioned, audited) | Stores flag definitions, rules, rollout percentages, owner, expiry; every change versioned and attributed. | Always — the single authored source of truth. | Not in the request hot path; if it were, its outage would take down evaluation everywhere. |
| Push/poll distribution to SDK | Changes propagate by streaming push or periodic poll of a versioned snapshot. | Always, decoupling evaluation from the control plane. | Poll interval or stream reconnect gap defines worst-case staleness. |
| Local SDK evaluation | SDK evaluates rules against context using its last snapshot, in-process. | Always — keeps flag checks off the remote-call path. | SDK must expose snapshot age, or teams debug invisible staleness. |
| Percentage-hash rollout | User key hashed deterministically into a bucket compared to the rollout. | Gradual rollout that must be sticky per user. | Hash and salt must stay stable, or users flip in and out. |
| Kill-switch default policy | Explicit behavior (usually "off"/safe default) when the snapshot is stale beyond a threshold or missing. | Any flag gating risky or expensive behavior. | Needs a per-flag policy: "safe" differs by flag. |

## API

Control plane (REST, authenticated users; every mutation is optimistic-concurrent and audited):

```text
PUT   /v1/projects/{p}/envs/{e}/flags/{key}        If-Match: <version>   { on, variations, offVariation, prerequisites, targets, rules, fallthrough, expiresAt, salt }
      → 200 { version } | 409 version conflict | 422 { errors:[cycle | weights≠100000 | unknown variation] } | 403
PATCH /v1/projects/{p}/envs/{e}/flags/{key}        [{ "op":"turnOff" } | { "op":"setRollout", "percent":20 }]     reason required
POST  /v1/projects/{p}/envs/{e}/flags/{key}:kill   { reason }          # on=false, needs `kill`, no approval, fully audited
GET   /v1/projects/{p}/envs/{e}/flags?limit=100&cursor=…     GET /v1/audit?flag=…&actor=…&from=…
```

SDK and relay (server SDK key in `Authorization`; client-side keys are public IDs and receive only evaluated values):

```text
GET  /sdk/flags                 If-None-Match: "<etag>"   → 200 { version, flags:{…} } + ETag | 304
GET  /sdk/stream                Last-Event-ID: <version>   → SSE: event put {snapshot} | patch {key, version, flag} | delete {key, version}
POST /sdk/events                { summaries:[{flag, variation, version, count}], exposures:[…] }   → 202 (best-effort, batched)
POST /sdk/eval                  { context } → { flags:{key:{value, variation, reason}} }     # client-side and edge evaluation only
```

**Idempotency and ordering**: writes carry `If-Match`; SDKs apply an update only if its `version` exceeds the held one (per environment and per flag), so duplicate or out-of-order stream messages are harmless and a reconnect resumes with `Last-Event-ID`. Event batches carry a batch id and are deduped downstream.

## Data model

| Entity | Shape | Notes |
|---|---|---|
| `flags` | `(project, env, key)` → definition JSON, `version`, owner, type, `expires_at`, salt | Source of truth (Postgres); rows are small and few (10K) |
| `flag_versions` | append-only history of every definition | Rollback and diff; part of the audit trail |
| `segments` | reusable rules or key lists | Large lists (> ~15K keys) live in a side store |
| `audit_events` | `(id, at, actor, env, flag, before, after, reason, request_id)` | Append-only, written in the same transaction as the flag change |
| `snapshots` | per env: compiled blob + `version` + ETag in object storage | **Derived**; rebuilt on every change, then pushed to relays |
| `sdk_keys`, `members/roles` | key hash, env, permissions | Keys stored hashed; rotation supported |

**Partition key**: `(project, env)`. It bounds each snapshot, scopes streams and blast radius, and matches RBAC. One Postgres with replicas holds everything (10K flags); scale problems here are fan-out, never storage.

## Architecture and data flow

```arch
%% caption: Feature flag evaluation happens entirely locally in the SDK, using rules distributed from the Control Plane via Relays.
node eng "Engineer" at 0,0 icon=user color=blue
node cp "Control Plane\n(Validation, RBAC, DB)" at 2,0 icon=server color=slate
node relay "Regional Relays\n(SSE Fan-out / Polling)" at 4,0 icon=internet color=amber
group svc "Application Service" color=green style=dashed
node sdk "Feature Flag SDK\n(Local Rule Cache)" at 4,2 in svc icon=code
node eval "evaluate(context)\n-> decision" at 2,2 in svc icon=function

eng -> cp : "update\nrule"
cp -> relay : "push\nsnapshot"
relay ..> sdk : "stream/poll\nrules"
sdk -> eval : "local\ndecision"
```

```arch
%% caption: A kill switch is one transactional write followed by a fan-out through relays, and every hop is a cache that keeps serving the last good version if the hop before it dies.
node Op "Operator" at 0,0 icon=user
node CP "Control Plane" at 2,0 icon=server
node Rel "Regional Relay" at 2,2 icon=internet
node SDK "SDK in Service" at 0,2 icon=code

Op -> CP : "POST flag:kill\nwith reason"
CP -> CP : "commit flag\n& audit" dir=right
CP -> Op : "200 OK\nversion N+1"
CP -> Rel : "publish\npatch N+1"
Rel -> SDK : "SSE patch\nversion N+1"
SDK -> SDK : "apply if\nN+1 > held" dir=left
SDK -> SDK : "next evaluate()\nreturns off" dir=left
SDK -> Rel : "poll if\nstream broken"
Rel -> SDK : "200 new\nsnapshot"
```

The hard decision is what happens during a control-plane or distribution outage: the SDK keeps serving its last good snapshot rather than failing evaluation, but it must not serve an arbitrarily old snapshot as if current — this trades perfect freshness for availability, made visible by exposing snapshot age. The safe-default behavior must be defined per flag at authoring time, because "fail to off" is right for a risky new code path but "fail to on" is right for a flag whose only job is an emergency kill for something already live — getting this backwards turns a control-plane hiccup into an incident.

**One write, end to end**: validate (schema, prerequisite DAG, weights sum to 100,000) → transaction writes the new `flags` row, `flag_versions` and `audit_events` → builder recompiles the environment snapshot → relays receive a patch (or a full `put`) → SDKs apply. **One read**: `evaluate(key, ctx, default)` looks up the flag in an in-memory map, runs the rule engine, returns `{value, variation, reason}`, and bumps a local counter; nothing leaves the process on that path.

## Deterministic percentage bucketing

`bucket = hash(flagKey + salt + userKey) mod 100,000` (a fixed hash such as SHA-1 or MurmurHash3, first 64 bits), and the user gets the rollout variation when `bucket < percent × 1,000`. Properties:

- **Sticky and monotonic**: the same inputs give the same bucket, so raising 10% → 20% keeps everyone already in and adds only users with buckets in [10,000, 20,000). No re-randomization flip-flop.
- **Independent across flags**: `flagKey` and `salt` are in the hash, so the users at the front of one rollout are not the same users at the front of every other one (else the same customers absorb every new feature's bugs and experiments correlate). Rotating `salt` deliberately re-randomizes, e.g. between experiments.
- **Bucket-by attribute**: hash `orgId` instead of `userId` for B2B (all users of a customer see the same experience); anonymous traffic uses a device id.
- **Resolution**: 100,000 buckets give 0.001% steps; with 1M users at 1% the count is ~10,000 ± 100 (binomial sd ≈ 1% relative), so small canaries are noisy but unbiased.
- **Cross-language conformance**: server (Go, Java) and client (JS) SDKs must agree bit for bit, so publish a shared test-vector suite (`(flagKey, salt, userKey) → bucket`) that every SDK must pass, including integer-width and UTF-8 edge cases.

## Targeting model and precedence

A flag is `{key, on, variations[], offVariation, prerequisites[{flag, variation}], targets[{variation, keys[]}], rules[{clauses[{attribute, op, values, negate}], serve | rollout{bucketBy, weights[]}}], fallthrough, salt, version}`. Evaluation order, first hit wins:

1. `on = false` → `offVariation`. **Kill switch outranks everything**, including individual targets.
2. **Prerequisites**: every prerequisite flag must evaluate to its required variation, else `offVariation`. Cycles are rejected at write time, depth is capped (say 5), so evaluation stays bounded and cheap.
3. **Individual targets** (explicit keys, e.g. QA or a VIP).
4. **Rules** in order, first match serves its variation or rollout.
5. **Fallthrough**: a fixed variation or a percentage rollout.

Every result carries a `reason` (`OFF`, `PREREQ_FAILED`, `TARGET`, `RULE#3`, `FALLTHROUGH`, `ERROR`) so "why did this user get X" is answerable from logs. Evaluation never throws: malformed rules or unknown attributes return the caller's default with reason `ERROR`. Large segments are the one exception to "no network in evaluation": membership lookups go to a side store (as LaunchDarkly's Big Segments do, per its docs) with a local cache, and flags depending on them are marked as such.

## Distribution: snapshot, stream, and the relay tier

| Option | Latency | Load | Failure behavior | Verdict |
|---|---|---|---|---|
| ETag polling (5 s) | ≤ 5 s + RTT | 20K req/s of ~400 B 304s | Trivially resilient, stateless | **Fallback** |
| SSE stream + `Last-Event-ID` | ~1 s | 100K connections | Reconnect storm risk, mitigated by jittered backoff | **Primary** |
| WebSocket / gRPC stream | ~1 s | Same | Same, more ceremony | Only if you need bidirectional |
| Sidecar or xDS-style config push | ~1 s | One agent per host | Extra moving part per host | If a mesh already exists |
| Coordination store watches (etcd, ZooKeeper) from every SDK | ~1 s | 100K watchers | Strongly consistent store as fan-out layer | Reject as the fan-out layer: it couples a quorum store's availability to every service |

**Relay tier**: ~20 regional relays hold the compiled snapshot in memory and on disk, subscribe upstream once per environment, and serve SDK streams and polls. This cuts control-plane connections from 100K to 20, keeps traffic in-region, and lets relays keep serving during a control-plane outage (they are the caches the 1-hour requirement leans on). SDKs list two relays (client-side failover) and fall back to polling. Hierarchy is control plane → relays → SDKs; relays are stateless enough to autoscale, and a relay restart reloads its disk copy before reconnecting upstream. Sign snapshots (HMAC or Ed25519) so a compromised relay or CDN cannot forge config.

## SDK bootstrap and offline behavior

1. **Start**: load the persisted snapshot from local disk (or one baked into the image) and mark `snapshot_age`; try relay with a timeout (block `init` for at most ~2 s, configurable), then proceed with whatever exists. Never block startup on the control plane.
2. **No snapshot at all**: every `variation(key, ctx, default)` returns the **compiled-in default** with reason `DEFAULT`; the code author chose that default at the call site.
3. **Steady state**: apply stream patches by version; on parse or schema failure keep the last good snapshot and emit an error metric.
4. **Outage**: keep serving the held snapshot. The contract is ≥ 1 h; configure `max_stale` (say 24 h, measured on a monotonic clock since receipt, not wall time). Beyond it each flag applies its `stale_policy` (`serve_last` for proven flags, `default` for risky ones) and the SDK reports `stale=true`.
5. **Expose health**: `snapshot_age`, `stream_connected`, `initialized`, so a service can alert on itself.

## Audit, RBAC, environments, and lifecycle

- **Environments** (dev, staging, prod) are separate flag configs with separate SDK keys; promoting a change to prod is a new write, not a copy.
- **RBAC** per project and environment: viewer, writer, approver, admin, plus a narrow `kill` permission. Prod writes need an approval (four-eyes) except `kill`, which is always allowed but requires a reason and pages the owner. Every change, attempted or applied, lands in the append-only audit log (shipped to a SIEM; optionally hash-chained as in [012](012_workflow_scheduler_solution.md)).
- **Guarded change delivery**: flag changes are production changes, so use staged rollout and a **dry-run** ("this rule would affect ~4% of yesterday's traffic"), scheduled changes, and metric-linked automatic rollback.
- **Lifecycle**: every flag has a type (release, ops or kill, experiment, entitlement), an owner and an `expires_at`. Release flags expire ~30 days after reaching 100%; a stale-flag report lists flags unchanged at 100% for 30 days, and a code-reference scan finds dead branches. **Removal order**: delete the code path first (hard-code the winning variation), then archive the flag, so old builds still get a defined default. Uncleaned flags multiply test states (2²⁰ combinations for 20 flags).

## Exposure and evaluation logging

Per-evaluation logging costs 10 TB/day, so SDKs aggregate **summary counters** (per flag, variation, version) and flush every 60 s (4 MB/s across the fleet). **Exposure events** (who saw which variation, needed to analyze an experiment) are emitted only for flags marked `experiment`, deduped per `(flag, user)` per flush window and sampled if needed: ~375 GB/day at 5% of evaluations. Events are batched with retry and a bounded in-memory queue; dropping them under pressure is acceptable, blocking the request path is not. Private attributes are redacted in the <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr>. For assignment, analysis and guardrails see [31 — ranking, recommendation, and experimentation](../building_blocks/31_ranking_recommendation_and_experimentation.md) and [037](037_experimentation_platform_solution.md).

## Capacity and storage

Evaluation is sub-microsecond in-process logic against an in-memory map, which rules out any remote lookup on the hot path; the control plane serves change-rate traffic (~0.01 writes/s) plus snapshot generation and fan-out, sized for writes and distribution, not per-request reads. Snapshots are segmented by project and environment, so an <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> never holds or diffs the whole organization's flag set.

Do not add a remote lookup to every request "just for flags that need very fresh values"; a genuinely live flag is a targeted low-<abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> admin path. Do not let flags live forever.

## Failure and abuse behavior

| Case | Correct behavior |
|---|---|
| Control plane unreachable | SDKs and relays keep serving the last good snapshot; distribution outage does not stop request handling. |
| Relay down or stream drops | <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> reconnects to a second relay with jittered backoff, polls every 5 s meanwhile; kill switch still meets ~6 s. |
| Snapshot older than `max_stale` | Per-flag `stale_policy` applied explicitly; staleness exposed in <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> health metrics. |
| <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> just started, no snapshot | Load disk copy, else compiled-in defaults; never block startup on the control plane. |
| Malformed or invalid flag pushed | Control plane validates on write; <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> validates on receipt and keeps the last good snapshot instead of crashing. |
| Rollout percentage change flip-flops users | Deterministic hash on a stable key keeps users in or out as percentage rises. |
| Unauthorized change attempt | RBAC rejects it; attempts and applied changes are audited. |
| Bad flag change causes an incident (the most common flag failure) | `kill` propagates in seconds; staged rollout, dry-run and metric-linked auto-rollback; the audit log pins the change and author in one query. |
| Zone or region loss | Relays run in every region and SDKs list two; the control plane fails over to a replica region, and the 1-hour stale window covers the failover. |
| Bad <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> release (evaluation bug) | Shared conformance vectors gate releases; <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr>-version telemetry in events lets relays or ops pin a minimum version; <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> errors return defaults, never throw. |
| Reconnect storm after relay restart | Full-jitter backoff (1 s base, 30 s cap); 5K clients × 15 KB = 75 MB, absorbed. |
| Leaked server <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> key | Rotate the key, alert on unexpected source IPs; client-side IDs expose only evaluated values, never rules. |
| Flag never expires, rules pile up | Ownership and expiry metadata feed the stale-flag report and a review process. |

## Observability and interview close

Measure propagation latency from control-plane commit to <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr>-applied (p50/p99, from a version-stamped heartbeat flag), the share of SDKs fresh within 10 s, snapshot-age distribution, `stream_connected` ratio, stale-fallback count, evaluation error rate and latency (near zero), flags past expiry, and event drop rate. **The one paging alert**: kill-switch propagation p99 above 10 s, or fewer than 99% of SDKs within 10 s of the latest version. Fallback-rate and expiry counts are ticket-level.

Interview close: "Flag evaluation has to be local and synchronous with zero network calls, because it sits on every single request — so the real system is the control plane plus distribution pipeline that keeps SDKs' cached snapshots fresh and tells them how stale they are. Kill-switch defaults are defined per flag at authoring time so a control-plane outage degrades to a known-safe behavior instead of an undefined one."

**Trade-off to state:** local evaluation from an eventually consistent snapshot gives sub-millisecond, outage-proof decisions at the cost of a bounded window (about 1–6 s here) in which different <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> instances disagree; I accept it because flags are not transactions, and any flag that must flip atomically is handled by a staged, versioned rollout instead.

## Follow-ups the interviewer will ask

1. **"How do you do multi-region?"** One writable control-plane region with a replica elsewhere, relays in every region, and SDKs bound to the nearest two. Relays fan out from whichever control plane is up, and the ≥ 1 h stale window covers a control-plane failover ([27](../building_blocks/27_multi_region_and_global_traffic.md)). Kill switch latency is one relay hop, in-region.
2. **"What changes at 10× and 100×?"** Evaluations at 500B/day still cost ~6 cores fleet-wide, since evaluation is local. What scales is <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> instances (1M → ~200 relays at 5K streams each, or a relay hierarchy), event volume (sampling and aggregation must tighten, 3.75 TB/day of exposures becomes an experiment-only pipeline) and snapshot size (segment by service, delta-only updates). At 100× (5T/day) evaluation is ~58 cores, still trivial; the event pipeline is what must be redesigned (counters plus sampled exposures).
3. **"Can you make all instances flip at the same instant?"** No; distribution is asynchronous. For consistency-sensitive changes (schema migrations) use a versioned, staged flag (dual-write → dual-read → cut over) and a convergence view ("99.9% of instances at version ≥ N") before advancing. Only if it must be transactional does the decision belong in a central authority in the request path.
4. **"What does it cost and what do you cut first?"** <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> ~0.6 core fleet-wide (negligible); the costs are relays, egress (~0.75 GB/day of config) and events (375 GB/day of exposures, ~11 TB or ~$260/month at 30-day retention and $23/TB-month; processing costs more). Cut exposure sampling first. Build vs buy: LaunchDarkly, Unleash or an OpenFeature-compatible service unless audit or tenancy demands custom.
5. **"How do you defend against abuse?"** RBAC with environment-scoped roles, approvals on prod, rate limits on flag writes, hashed and rotatable keys, no rules shipped to browsers, private-attribute redaction, validation limits (rule count, prerequisite depth, payload size).
6. **"What if the interviewer says just use etcd or Consul watches for flags?"** They are fine as a control-plane store or a small internal deployment, but 100K <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> watchers on a strongly consistent quorum store make its availability the flag system's availability, and consensus buys nothing for a config that tolerates seconds of skew. Keep the store behind the builder and distribute through relays.
7. **"What if a client-side (browser or mobile) <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> needs flags?"** It cannot hold rules (they leak segments and internal logic and would be large), so evaluate at a relay or edge with `POST /sdk/eval`, return only values, cache them per session and refresh by stream. That is the one place a network call is part of evaluation, made once per session, not per check.

## Common mistakes

1. **Making evaluation a remote call.** 579K–1.7M RPS and a 1 ms budget forbid it, and it turns a flag outage into a total outage. Evaluate locally against a snapshot.
2. **Rehashing randomly when the percentage changes.** Users flip in and out. Hash `(flagKey, salt, userKey)` deterministically and compare to a threshold.
3. **Sharing one hash across flags.** The same users are always first, correlating rollouts and experiments; include the flag key and salt.
4. **No stale policy.** "Serve last forever" hides a dead pipeline; "fail everything to default" turns an outage into an incident. Use a per-flag policy and expose snapshot age.
5. **Treating kill switches like ordinary flags.** They need highest precedence, a narrow permission with no approval delay, an <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>, and a tested path.
6. **Ignoring flag debt.** Without owners and expiry, flags become permanent untested branches; remove code before the flag.
7. **Polling without ETag or jitter.** 100K synchronized full-body polls are a self-inflicted DDoS; use conditional requests, jitter and relays.

## Going from L5 to L6

- **Migration and rollout.** Adopt per team: wrap an existing config in the <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> interface first, run the new evaluator in shadow (log disagreements), then flip; dual-run old and new SDKs and compare decisions.
- **Cost model.** Cost scales with <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> instances (relay streams) and exposure events, not with evaluations; report cost per 1,000 instances and per experiment.
- **Ownership and blast radius.** A platform team owns control plane, relays and SDKs; service teams own their flags and expiry. Environment- and project-scoped snapshots, staged flag delivery and the `kill` path limit blast radius; a bad <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> release is the one global risk, so canary SDKs.
- **Build vs buy.** Prefer an established service or an OpenFeature-compatible OSS server; build only for compliance, tenancy or cost, and keep the <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> behind the OpenFeature interface to avoid lock-in.
- **Phased evolution.** Phase 1: control plane, ETag polling, <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> with disk cache. Phase 2: relays and <abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr>. Phase 3: experiments, guarded rollouts and auto-rollback. Phase 4: edge evaluation for client-side SDKs.
- **What I would measure first.** Real flags per service (drives snapshot size), instance counts (relay sizing), change rate and the share of incidents that begin with a flag change, since those set the priority of dry-run and auto-rollback.

## Build exercise

Implement a local flag evaluator that takes a cached snapshot (rules + percentage rollout) and a request context, using a deterministic hash for percentage bucketing; simulate a stale/missing snapshot and assert evaluation falls back to the flag's configured safe default rather than erroring or blocking.

Extend it with named assertions:

- `test_rollout_monotonic`: users in the 10% rollout are a subset of the 20% rollout for the same flag and salt.
- `test_rollout_independent_across_flags`: with two flags at 50%, the overlap of enrolled users is within 2% of 25% over 100K users.
- `test_kill_beats_targets`: a user in an individual target and matching a rule gets `offVariation` once `on=false`.
- `test_prerequisite_cycle_rejected`: a write creating a cycle fails validation and leaves the snapshot unchanged.
- `test_conformance_vectors`: a Go and a Python implementation produce identical buckets for 10,000 `(flagKey, salt, userKey)` vectors.
- `test_out_of_order_patch_ignored`: applying version 7 after 8 leaves the held flag at 8.
- `test_stale_policy`: after `max_stale` a `default`-policy flag returns its default and a `serve_last` flag returns the last value, both reporting `stale=true`, and no call blocks past 1 ms.
