# Observability and Reliability

Observability is the evidence a system produces about its own behavior. Reliability is what you do with that evidence: define an acceptable failure budget, alert on the right thing, and recover within a stated bound when something breaks. Without observability, reliability work is guessing; without a reliability target, observability is just data with no decision attached to it.

## The four signal types

| Signal | What it captures | Primary use |
|---|---|---|
| Metrics | Numerical time series (rate, errors, latency, saturation, queue age, cache hit rate). | Dashboards, alerting, trend detection at low storage cost. |
| Logs | Structured event records with correlation IDs and safe context. | Root-cause detail for one specific event or request; never log secrets/PII by default. |
| Traces | Path and timing of one request across services. | Finding which hop in a distributed call is actually slow. |
| Profiles | <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>/memory/code-path evidence over a window. | Performance regressions and resource-usage root cause within one process. |

Metrics tell you *that* something is wrong and roughly how bad. Traces tell you *where* in the call graph. Logs tell you *why*, for one specific instance. Profiles tell you *what code* is spending the resource. Reach for all four together — a single signal type answers only one of "what/where/why/what specifically."

## Metrics types and the cardinality trap

| Type | Meaning | Example |
|---|---|---|
| Counter | Monotonic total, only increases (until reset). | Requests served, errors. |
| Gauge | Current value, rises and falls. | Queue depth, open connections. |
| Histogram | Distribution buckets/samples. | Request latency; derive p50/p95/p99. |
| Summary | Client-side precomputed quantiles. | Similar to histogram but harder to aggregate correctly across instances. |

**High-cardinality labels are the most common way to turn a metrics platform into an incident.** A label with unbounded distinct values — `user_id`, `request_id`, raw URL, raw error text — multiplies the number of distinct time series the backend has to store and index. A metric with tens of legitimate series can balloon to millions if a single label is user-controlled. Keep unbounded-cardinality detail in logs or traces, where it belongs; keep metric labels to a small, bounded set (status code class, region, tenant tier — not `tenant_id` unless tenant count is small and bounded).

## RED, USE, and four golden signals — prompts, not rules

| Framework | Applies to | Dimensions |
|---|---|---|
| RED | Request-serving services | Rate, Errors, Duration. |
| USE | Resources (<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>, disk, connection pool, queue) | Utilization, Saturation, Errors. |
| Four golden signals | General service health | Latency, traffic, errors, saturation. |

None of these is the "correct" framework to recite. They're starting checklists for "what should I be measuring here" — pick metrics tied to actual user harm, not to whichever framework sounds most credentialed. A service can have RED metrics that look fine while its underlying USE metrics show a connection pool at 98% saturation about to fall over — track both the request-facing view and the resource-facing view.

## <abbr title="Service Level Indicator - A carefully defined quantitative measure of some aspect of the level of service that is provided, such as latency.">SLI</abbr>/<abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>/error budget — worked example

```text
SLI (indicator):  fraction of feed requests that return successfully in < 300ms
SLO (objective):  99.9% of feed requests meet the SLI, measured over a rolling 28 days
Error budget:     0.1% of requests may fail the SLI without violating the SLO
                  = ~40 minutes of full outage-equivalent per 28 days
```

The error budget is a resource you spend deliberately. If the budget is nearly exhausted, that is a reason to freeze risky changes and prioritize reliability work over new features. If the budget is healthy, that is license to ship faster. This turns "is our reliability good enough" from a vague debate into a number both engineering and product can plan against.

## Alert design

Page on customer impact and burn rate, not on a raw resource number. "<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> at 80%" is a diagnostic signal you look at *after* a page fires — it is rarely, by itself, something that should wake someone up. Alert on:

- <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> burn rate (are we consuming error budget faster than sustainable).
- A symptom the user actually experiences (elevated error rate, elevated p99 latency on a critical path).
- A leading indicator close enough to real harm to be actionable (queue depth trending toward the point where requests will start timing out).

Every page needs a named owner, a severity, and a runbook with a concrete first action. An alert with no runbook trains the on-call engineer to ignore pages, which is worse than not alerting at all — alert fatigue is itself a reliability failure.

## Backups and tested restore

"We take backups" is not a recovery plan; a recovery plan is a backup you have actually restored into an isolated environment and verified at the application level, on a schedule, not just once during initial setup. Untested backups routinely turn out to be incomplete, corrupted, or restorable-but-inconsistent with the app's expectations — you find this out during the real incident if you never rehearsed it.

- **RPO (Recovery Point Objective):** maximum acceptable data loss, measured in time (e.g., "at most 5 minutes of writes lost").
- **RTO (Recovery Time Objective):** maximum acceptable time to restore service (e.g., "back online within 1 hour").

RPO drives your replication/backup frequency (continuous replication vs. hourly snapshot). RTO drives your restore automation and drill cadence (a manual, undocumented restore process has a much worse real-world RTO than a tested, scripted one, regardless of what the runbook claims).

## Failure domains

```text
process < node < zone < region < account < provider
```

Each level is a blast radius. A replica in the same failure domain as its primary does not protect against that domain's failure — two nodes in the same zone both go down in a zone-level outage; two zones in the same region both go down in a region-level event (rare, but it happens); a single cloud provider account is a blast radius for account-level compromise or billing/config mistakes; a single provider is a blast radius for a provider-wide outage.

State explicitly which failure domain your redundancy actually covers. "We have three replicas" means nothing for availability until you also say across how many zones/regions, because three replicas in one zone survive a process crash and a node failure but not a zone failure — and "99.99% availability" as a target is not credible if every replica shares one failure domain that itself doesn't hit 99.99%.

## Distributed tracing in practice

- A **trace** is a tree of **spans** (one per operation: <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr>, DB query, queue publish). Each span has a trace ID, span ID, parent span ID, timing, and attributes.
- **Context propagation** carries the trace ID across process boundaries in headers (W3C `traceparent`) and across async hops by putting it in message metadata. A queue consumer that doesn't propagate context breaks the trace.
- **Sampling:** head-based sampling (decide at the start, e.g. 1%) is cheap but misses rare slow requests; tail-based sampling (decide after completion, keep all errors and slow traces) costs buffering but keeps the traces you actually need.
- **Use:** find which hop owns the latency, detect fan-out explosions (one request causing 400 downstream calls), and link from a metric spike to exemplar traces. OpenTelemetry is the standard instrumentation <abbr title="Application Programming Interface">API</abbr>; Google's Dapper paper is the origin of the model.

## Safe deployment: canary, blue-green, feature flags, rollback


```arch
%% caption: Canary limits risk by routing a small percentage of traffic to new code; Blue-Green enables instant rollback via a load balancer flip.
group canary "Canary Deployment (1% Traffic)" color=slate
node clb "Load Balancer" at 0,1 in canary icon=internet
node cv1 "v1 (Baseline)" at 2,0 in canary icon=server color=blue
node cv2 "v2 (Canary)" at 2,2 in canary icon=server color=green

clb -> cv1 : "99%"
clb -> cv2 : "1%"

group bg "Blue-Green Deployment" color=slate
node bglb "Load Balancer" at 4,1 in bg icon=internet
node bgv1 "v1 (Blue)" at 6,0 in bg icon=server color=blue
node bgv2 "v2 (Green)" at 6,2 in bg icon=server color=green

bglb ==> bgv2 : "flipped to v2"
bglb ..> bgv1 : "instant rollback\nif needed"
```
Most outages are caused by changes. Safe delivery limits the blast radius of a bad change and shortens time to detect and revert it.

| Technique | How | Protects against | Cost |
|---|---|---|---|
| **Canary** | Deploy to a small slice (1% of traffic, one zone, or one cluster), compare its SLIs against the baseline, then widen in stages | Bad binaries and config reaching everyone | Needs automated comparison (canary analysis) and enough traffic for signal |
| **Blue-green** | Run the new version (green) alongside the old (blue); switch traffic at the load balancer; switch back to roll back | Slow rollbacks | Double capacity during the switch; database changes still need compatibility |
| **Rolling update** | Replace instances in batches | Downtime | Mixed versions run together; rollback is another rolling update |
| **Feature flags** | Ship code dark; enable per user/tenant/percentage at runtime; kill switch to disable instantly | Coupling deploy with release | Flag debt; flag evaluation must fail safe |
| **Progressive rollout by geography/time** | Region by region with soak time | Region-wide outages | Slower releases |

Rules that make these work:
- **Every change is rollback-safe**: new code reads old data, schema changes are expand-and-contract, config changes go through the same canary as binaries.
- **Automate the decision**: a canary that needs a human to stare at dashboards gets skipped under pressure. Compare error rate, latency, and saturation of canary vs control with statistical tests; auto-rollback on regression.
- **Roll back first, debug second.** Fix-forward only when rollback is impossible (e.g., after a non-reversible migration).
- **Error budgets gate velocity**: when the budget is spent, slow or freeze risky rollouts.

## Capacity planning

1. **Measure demand:** peak <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> per endpoint, growth rate, seasonality (daily, weekly, holidays, launches).
2. **Measure supply:** load-test one instance to find the throughput at which the latency <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> breaks (not the throughput at which it crashes).
3. **Compute:** `instances = peak_QPS / safe_QPS_per_instance`, then add **headroom** for failures: in N+2 planning, the system must meet the <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> with the largest failure domain (a zone) down plus one more instance during a deploy. With 3 zones, each zone must carry 50% of peak, so total provisioned capacity is 150% of peak.
4. **Watch the true bottleneck:** often not <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> — database connections, lock contention, network bandwidth, downstream quotas, or memory.
5. **Plan lead time:** hardware and quota take weeks or months; autoscaling handles minutes-to-hours variation but has warm-up time and needs quota available.
6. **Revisit on every launch** and after any architectural change; model the cost as well as the capacity.

See `18_back_of_envelope_estimation.md` for the arithmetic.

## Tail latency and overload

The latency <abbr title="Service Level Indicator - A carefully defined quantitative measure of some aspect of the level of service that is provided, such as latency.">SLI</abbr> in the worked example above is decided at the tail, not the mean. When one request fans out to many servers and waits for all of them, the slowest server sets the latency: with 100 backends that are each slow 1% of the time, 63% of requests hit at least one slow backend (`1 − 0.99¹⁰⁰`, derived in `18_back_of_envelope_estimation.md`), so per-server p99 is what you measure and alert on. A standard mitigation is the **hedged request**: for an idempotent read, send a second copy to another replica if the first has not answered within about the typical p95, take whichever reply arrives first and cancel the other, which costs a small amount of extra load only on the requests that are already slow. Hedging is a retry, so it needs the same budget discipline as any retry ([12_application_resilience_patterns.md](12_application_resilience_patterns.md)) and must back off under overload, because extra copies add load exactly when there is none to spare. The technique is described in Dean and Barroso, "The Tail at Scale" (Communications of the ACM, 2013); see [24_google_papers.md](24_google_papers.md) for where it sits among the Google papers. When demand exceeds even the planned headroom, the next layer of defence (shedding, prioritization, graceful degradation) is in [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md).

## Multi-region disaster recovery patterns

| Pattern | RPO | RTO | Cost | Notes |
|---|---|---|---|---|
| Backup and restore to another region | Hours (backup interval) | Hours to days | Low | Must be drilled |
| Pilot light (data replicated, minimal compute) | Minutes (async replication lag) | Tens of minutes | Medium | Scale-up automation is the risk |
| Warm standby (reduced full stack) | Seconds to minutes | Minutes | Medium-high | Regular failover tests |
| Active-active (all regions serve) | Near zero for synchronously replicated data | Seconds to minutes | High | Needs conflict handling or globally consistent storage (Spanner-style) |

Failover must be **tested regularly** (game days, Google's DiRT exercises), and failback is a separate, equally risky operation.

## Incident response and postmortems

- **Roles:** incident commander (coordinates, doesn't debug), operations lead, communications lead. Declare early; downgrading is cheap.
- **Mitigate before root-causing:** roll back, drain a region, disable a flag, shed load.
- **Communicate** on a fixed cadence to stakeholders and customers.
- **Blameless postmortem:** timeline, impact, root cause and contributing factors, what went well, where we got lucky, and action items with owners and deadlines. The goal is fixing the system that allowed the human error.

## Related building blocks

- [16_platform_and_infra.md](16_platform_and_infra.md) — IaC/GitOps/progressive delivery reduce operational risk but do not replace a tested restore.
- [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md) — saturation signals here are what autoscaling triggers should be reading.
- [17_decision_framework.md](17_decision_framework.md) — the worksheet's "signals / alerts / RPO / RTO" line is this file, filled in per design.
- [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md) — what to do when saturation signals fire: shed, prioritize, degrade.
- [24_google_papers.md](24_google_papers.md) — the papers behind these practices, including the tail-latency work on hedged requests.
