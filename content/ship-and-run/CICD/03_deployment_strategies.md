# Deployment Strategies

"Deploying" by stopping the server, copying the new binary and starting it again gives
users an outage every time you ship. This chapter covers the strategies that replace
that with zero-downtime, low-risk rollouts: rolling updates, blue/green, canary releases
with automated analysis, and shadow traffic. For each one it explains the mechanics
down to the Kubernetes and load-balancer level, what it costs, how it fails, and when to
choose it. The recurring theme is that every strategy except "recreate" runs two
versions at the same time, so compatibility between versions is the real prerequisite.

## Foundations — Why is replacing running software risky, and what are the options?

### The problem

A running service holds promises: open connections, requests half-processed, users mid
checkout. Replacing it means three things must go right at once:

1. **Capacity**: while old instances stop and new ones start, enough instances must be
   up to serve the traffic.
2. **Correctness**: the new version must actually work, under real traffic, with real
   data, which no test environment perfectly reproduces.
3. **Reversibility**: if it does not work, you need a fast way back that does not itself
   cause an outage.

Each strategy is a different trade between **speed**, **cost** (how much extra capacity
you run during the deploy) and **blast radius** (how many users a bad version can hurt
before you notice and undo it).

### An everyday analogy

A restaurant changing its menu can close for a day and reopen (recreate); swap tables to
the new menu a few at a time (rolling); set up a second identical dining room with the
new menu and move everyone at once (blue/green); give the new menu to one table in
twenty, watch their faces, then expand (canary); or have the kitchen secretly cook every
order twice, serving only the old dish, to see whether the new recipe holds up at dinner
rush (shadow).

### The strategies at a glance

| Strategy | Two versions live at once? | Extra capacity | Blast radius of a bad version | Rollback speed | Needs |
|---|---|---|---|---|---|
| Recreate | No | None | Everyone, plus downtime | Slow (another recreate) | Nothing |
| Rolling update | Yes, during the roll | Small (`maxSurge`) | Grows with the roll, up to everyone | Minutes (roll back the same way) | Health checks, compatible versions |
| Blue/green | Briefly | 2× during the switch | Everyone, but only after pre-switch tests | Seconds (switch back) | A switchable router, 2× capacity |
| Canary | Yes | Small | A chosen slice (1–5%) | Seconds (shift weight back) | Traffic splitting, good metrics, analysis |
| Shadow | Yes, new version gets copies | Up to 2× | None for users (responses discarded) | Not applicable | Mirroring, side-effect isolation |

### Vocabulary

| Term | Meaning |
|---|---|
| Readiness | "This instance can take traffic now"; the load balancer only routes to ready instances |
| Draining | Letting in-flight requests finish before an instance stops |
| Stable / baseline / canary | The current version; a fresh copy of it used for comparison; the new version under test |
| Traffic weight | The share of requests a version receives |
| Bake time | A deliberate wait at a stage so slow-burning problems can appear |
| Blast radius | How many users or requests a failure can affect |
| Progressive delivery | The umbrella term for canary-style rollouts driven by metrics |

## 1. Recreate

Stop all old instances, then start new ones (Kubernetes `strategy: type: Recreate`).
There is downtime between the two. It is still the right choice when two versions
**must not** run at once: a singleton job that would double-process, a database schema
change the old version cannot survive, or a dev environment where nobody cares. It is
also what happens by accident when a service has one replica and no surge room.

## 2. Rolling update (the Kubernetes default)

Replace instances in batches: start some new ones, wait until they are ready, stop some
old ones, repeat. A Kubernetes Deployment does this by managing two ReplicaSets, scaling
the new one up and the old one down in steps.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout-api
spec:
  replicas: 10
  revisionHistoryLimit: 10        # old ReplicaSets kept for `rollout undo` (default 10)
  progressDeadlineSeconds: 600    # mark the rollout failed if it stalls (default)
  minReadySeconds: 10             # a new pod must stay ready this long to count
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxSurge: 25%               # default: up to 13 pods may exist (10 + ceil(2.5))
      maxUnavailable: 0           # default is 25%; 0 keeps full capacity throughout
  selector:
    matchLabels: { app: checkout-api }
  template:
    metadata:
      labels: { app: checkout-api }
    spec:
      terminationGracePeriodSeconds: 30
      containers:
        - name: api
          image: ghcr.io/acme/checkout-api:3f9a1c2
          readinessProbe:
            httpGet: { path: /readyz, port: 8080 }
            periodSeconds: 5
            failureThreshold: 3
          lifecycle:
            preStop:
              exec:
                command: ["sleep", "5"]   # let load balancers stop routing first
```

### The arithmetic

`maxSurge` is how many pods *above* `replicas` may exist; `maxUnavailable` is how many
*below* `replicas` may be unready. Percentages round **up** for surge and **down** for
unavailable. With the defaults (25% / 25%) and 10 replicas: at most 13 pods, at least 8
available. With `maxSurge: 25%, maxUnavailable: 0` you never drop below 10 ready pods,
at the cost of up to 3 extra pods during the roll.

**Precision note:** the owner's outline said a rolling update "only requires +1 instance
capacity". That is only true with `maxSurge: 1`. The default surge is 25% of replicas,
and you can also roll with *zero* extra capacity by allowing `maxUnavailable > 0`, which
temporarily reduces serving capacity instead. Pick based on whether you have headroom in
the cluster or in the service.

### Where rolling updates fail in production

- **No or wrong readiness probe**: pods are marked ready before they can serve (caches
  cold, DB pool not connected), so traffic hits them and errors spike during every
  deploy. A readiness probe that checks downstream dependencies can have the opposite
  problem: one slow dependency marks every pod unready at once.
- **Dropped connections at shutdown**: when a pod is deleted, Kubernetes sends it
  `SIGTERM` *at the same time* as it removes it from the Service's endpoints. Load
  balancers and kube-proxy on other nodes take a moment to notice, so for a few seconds
  requests still arrive at a pod that is shutting down. The fix is a short `preStop`
  sleep (as above; newer Kubernetes versions also offer a built-in `sleep` preStop
  action that needs no `sleep` binary in the image), then a graceful shutdown that stops
  accepting new connections and finishes in-flight requests within
  `terminationGracePeriodSeconds`.
- **Mixed versions**: halfway through the roll, a user's first request hits v2 and their
  next hits v1. If v2 wrote data or returned a response v1 cannot handle, you get errors
  that disappear when the roll finishes, which makes them hard to reproduce (section 7).
- **The bad version still reaches everyone**: the rollout only checks readiness, not
  business correctness. A version that returns `200 OK` with wrong prices rolls out to
  100% without complaint. That is the gap canary analysis closes.
- **Stalled rollouts**: a crash-looping new pod stops the roll, and after
  `progressDeadlineSeconds` the Deployment reports `ProgressDeadlineExceeded`. Kubernetes
  does *not* roll back on its own; a pipeline or controller must.

```bash
kubectl -n checkout rollout status deployment/checkout-api     # waits; non-zero exit on failure
kubectl -n checkout rollout history deployment/checkout-api
kubectl -n checkout rollout undo deployment/checkout-api        # back to the previous ReplicaSet
kubectl -n checkout rollout pause deployment/checkout-api       # freeze mid-roll to investigate
```

**Precision note:** the owner's outline said rolling-update rollbacks are slow because
"you have to roll backward one by one". `rollout undo` is simply another rolling update
toward the previous ReplicaSet, so it takes about as long as the forward roll (minutes
for a large service). That is slow compared with blue/green or canary, where rollback is
a traffic switch, and it is why those strategies exist.

## 3. Blue/green deployment

Run two complete environments. **Blue** serves all production traffic on the current
version. Deploy the new version to **green**, test green directly (smoke tests, internal
users, synthetic traffic) while it serves no customers, then switch the router so green
takes 100% of traffic. Blue stays running, untouched, as an instant way back.

```arch
%% caption: Blue/green: the new version is deployed and tested in an idle environment, then one router change moves all traffic; switching back is equally instant.
grid 170x110
node users "Users" at 1,0 icon=users
node lb "Router / LB" at 1,1 icon=lb sub="one switch"
group blue "Blue: v1 (previous)" color=blue icon=server style=dashed
node b1 "App v1" at 0,2 in blue icon=app sub="idle, kept warm"
group green "Green: v2 (live)" color=green icon=server style=dashed
node g1 "App v2" at 2,2 in green icon=app sub="100% traffic"
node db "Shared database" at 1,3 icon=db sub="schema works for both"
node qa "Smoke tests" at 3,2 icon=check sub="hit green first"
users -> lb
lb:L ..> b1:T : "0% (rollback)"
lb:R ==> g1:T : "100%"
b1:B -- db:L
g1:B -- db:R
qa:L -> g1:R
```

### How the switch is implemented

| Switch point | How | Switch time | Watch out for |
|---|---|---|---|
| Kubernetes Service selector | Two Deployments labelled `version: blue` / `green`; patch the Service selector | Seconds (endpoint propagation) | Long-lived connections stay on the old pods until they close |
| Load balancer target groups | Swap which target group the listener forwards to (AWS ALB, GCP backend services) | Seconds | Connection draining settings on the old group |
| Ingress / gateway route | Change the backend in an Ingress or Gateway API `HTTPRoute` | Seconds | Controller reconcile delay |
| DNS | Point the name at the green load balancer | Minutes to hours | Clients and resolvers cache beyond the TTL; the slowest and least predictable switch |
| Argo Rollouts `blueGreen` | Controller manages `activeService` and `previewService` and switches for you | Seconds | Set `autoPromotionEnabled: false` to require a test gate |

```yaml
# Argo Rollouts: blue/green with a pre-promotion analysis gate
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: checkout-api
spec:
  replicas: 10
  selector:
    matchLabels: { app: checkout-api }
  template:
    metadata:
      labels: { app: checkout-api }
    spec:
      containers:
        - name: api
          image: ghcr.io/acme/checkout-api:3f9a1c2
  strategy:
    blueGreen:
      activeService: checkout-api          # what users hit
      previewService: checkout-api-preview # what smoke tests hit
      autoPromotionEnabled: false          # wait for analysis or a human
      prePromotionAnalysis:
        templates:
          - templateName: smoke-tests
      scaleDownDelaySeconds: 600           # keep blue up 10 min after the switch
```

### Trade-offs

- **Pros**: the new version is tested *in production infrastructure* before any user sees
  it; switch and rollback are both near-instant and atomic from the router's point of
  view; there is never a mixed-version fleet serving users.
- **Cons**: roughly 2× capacity during the deploy (cheap in the cloud if green is torn
  down after, expensive on fixed hardware); **every user moves at once**, so a bug that
  only real traffic reveals hits 100% immediately; shared state is still shared.
- **The database is the catch.** Blue and green almost always share the database (two
  copies of production data do not stay in sync). So the schema must work for both
  versions, and data written by green must be readable by blue if you ever switch back.
  Blue/green makes *code* rollback instant; it does nothing for *data* rollback (chapter
  05).
- **Warm-up**: green starts with cold caches, JIT not warmed and connection pools empty.
  Switching 100% of peak traffic onto it can cause a latency spike or a thundering herd
  on the database. Warm it with synthetic load, or switch in steps, which is a canary.

## 4. Canary releases and automated analysis

Send a small share of real production traffic to the new version, compare its health with
the old version, and increase the share in steps only while it stays healthy. The name
comes from the canaries miners carried: a small, early victim that warns everyone else.

```arch
%% caption: A progressive delivery controller shifts traffic weights step by step, while an analysis job compares the canary's metrics with the baseline and aborts on regression.
grid 170x110
node users "Users" at 0,1 icon=users
node router "Traffic router" at 1,1 icon=mesh sub="mesh or ingress"
node stable "Stable v1" at 2,0 icon=app sub="95%"
node canary "Canary v2" at 2,2 icon=app color=amber sub="5%"
node prom "Metrics" at 3,1 icon=prometheus sub="errors, latency"
node ana "Analysis" at 3,3 icon=gauge sub="vs thresholds"
node ctrl "Rollout controller" at 1,3 icon=k8s sub="Argo Rollouts, Flagger"
users -> router
router:T -> stable:L : "95%"
router:B -> canary:L : "5%"
stable:R ..> prom:T
canary:R ..> prom:B
prom -> ana
ana -> ctrl : "pass / fail"
ctrl -> router : "set weight"
```

### Three ways to split traffic

| Method | How | Granularity | Limits |
|---|---|---|---|
| Replica ratio | 1 canary pod next to 19 stable pods behind the same Service | Only as fine as replica counts (1/20 = 5%) | Cannot send 1% without 100 pods; weight follows pod count |
| Weighted routing | A mesh or ingress routes by weight: Istio `VirtualService`, Linkerd/SMI `TrafficSplit`, NGINX canary annotations, AWS ALB weighted target groups, Gateway API `HTTPRoute` `backendRefs[].weight` | Percentages independent of pod count | Needs that routing layer |
| Header or cohort routing | Route by header, cookie or user attribute (employees, a beta cohort, one country) | Deterministic cohorts | Cohort is not representative of everyone |

**Precision note:** the owner's outline said canaries "require advanced load balancers
(like Envoy/Istio)". Weighted routing makes canaries precise, but the simplest canary
needs nothing beyond a Kubernetes Service: run a second, small Deployment with the same
labels and the Service spreads traffic by pod count. What canaries really require is
**good metrics and a way to judge them automatically**.

### A canary with Argo Rollouts

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
metadata:
  name: checkout-api
spec:
  replicas: 10
  selector:
    matchLabels: { app: checkout-api }
  template:
    metadata:
      labels: { app: checkout-api }
    spec:
      containers:
        - name: api
          image: ghcr.io/acme/checkout-api:3f9a1c2
  strategy:
    canary:
      canaryService: checkout-api-canary
      stableService: checkout-api-stable
      trafficRouting:
        istio:
          virtualService:
            name: checkout-api
            routes: [primary]
      analysis:                       # background analysis for the whole rollout
        startingStep: 1
        templates:
          - templateName: success-rate
        args:
          - name: service
            value: checkout-api-canary
      steps:
        - setWeight: 5
        - pause: { duration: 10m }
        - setWeight: 25
        - pause: { duration: 10m }
        - setWeight: 50
        - pause: { duration: 10m }
        # after the last step the canary becomes the new stable (100%)
---
apiVersion: argoproj.io/v1alpha1
kind: AnalysisTemplate
metadata:
  name: success-rate
spec:
  args:
    - name: service
  metrics:
    - name: success-rate
      interval: 1m
      failureLimit: 2                 # a third failed measurement aborts the rollout
      successCondition: len(result) > 0 && result[0] >= 0.99
      failureCondition: len(result) > 0 && result[0] < 0.97
      # between 0.97 and 0.99 the measurement is Inconclusive -> the rollout pauses
      provider:
        prometheus:
          address: http://prometheus.monitoring.svc:9090
          query: |
            sum(rate(istio_requests_total{destination_service_name="{{args.service}}",response_code!~"5.."}[2m]))
            /
            sum(rate(istio_requests_total{destination_service_name="{{args.service}}"}[2m]))
```

When an AnalysisRun fails, the controller **aborts**: it sets the canary weight back to
0, scales the canary down and marks the Rollout `Degraded`. The Git state still says v2,
so the fix is a new commit (a revert or a fix), not a manual poke. Flagger (from the Flux
project) implements the same loop with a `Canary` resource; Spinnaker uses Kayenta.

### What to measure, and against what

- **Signals**: request success rate, latency percentiles (p50, p99), saturation (CPU,
  memory, queue depth), plus business signals where you can (checkouts per minute,
  payment authorisation rate). Golden signals and SLOs are covered in
  [Observability and Reliability](../../interview-core/SystemDesign/building_blocks/15_observability_and_reliability.md).
- **Compare canary with a baseline, not with stable.** Long-running stable pods have warm
  caches and have survived for days; brand-new canary pods have neither, so they look
  slightly worse even when the code is identical. Netflix's and Google's canary practice
  (Kayenta in Spinnaker) deploys a fresh **baseline** of the old version, the same size
  as the canary, at the same time, and compares canary against baseline.
- **Use statistics, not eyeballs.** Kayenta compares each metric's distributions with a
  Mann-Whitney U test and turns the per-metric verdicts into an overall score. A simpler
  threshold check (success rate ≥ 99%) works for most services.
- **Enough traffic to decide.** At 5% of a service handling 20 requests per second, the
  canary sees 1 request per second. A 1% error rate is then about one error every 100
  seconds, so ten minutes of data cannot distinguish 0.5% from 1.5% with any confidence.
  Low-traffic services need longer steps, a larger initial weight or synthetic traffic.
  This is also why "no data" must count as inconclusive or failed, never as success.

<div class="lab" data-viz="flow-canary-analysis"></div>

## 5. Shadow traffic (dark launching, traffic mirroring)

The router sends each request to the current version, which answers the user, and a
**copy** to the new version, whose response is thrown away (or compared, then thrown
away). You test v2 under real production load and real request shapes with zero user
impact.

```arch
%% caption: Shadowing: the live version answers users while a mirrored copy of each request exercises the new version, whose responses are only compared.
grid 170x110
node users "Users" at 0,0 icon=users
node proxy "Proxy / mesh" at 1,0 icon=proxy sub="request mirroring"
node v1 "Live v1" at 2,0 icon=app sub="answers users"
node v2 "Shadow v2" at 1,1 icon=app color=amber sub="responses dropped"
node diff "Response diff" at 2,1 icon=search sub="compare v1 vs v2"
node fake "Stubbed side effects" at 1,2 icon=warn color=red sub="no real charges"
users -> proxy
proxy ==> v1
proxy ..> v2 : "copy"
v1 ..> diff
v2 ..> diff
v2 -> fake
```

Implementations: Istio `VirtualService` `mirror` and `mirrorPercentage`, Envoy
`request_mirror_policies`, NGINX `mirror` directive, or replaying captured traffic
(GoReplay). Twitter's open-source Diffy popularised comparing live and candidate
responses automatically, using two copies of the old version to learn which fields are
naturally noisy (timestamps, random IDs).

Trade-offs:

- **Side effects are the whole problem.** If v2 handles `POST /purchase` for real, it
  charges the card a second time; if it sends email, users get two. Shadowing is
  straightforward for reads and idempotent operations. For writes, point the shadow at
  stubbed or sandboxed dependencies, a separate database copy, or a dry-run mode.
- **Capacity**: mirroring 100% doubles the load on everything the shadow calls unless
  those calls are stubbed. Start with a small `mirrorPercentage`.
- **It proves "does not crash and responds similarly", not "is correct"**, and it says
  nothing about how users react. It is a good step *before* a canary for risky rewrites
  (a new storage engine, a language migration), not a replacement for one.

## 6. Progressive delivery at scale

Large platforms chain these ideas into a rollout policy:

- **Rings or waves**: internal users ("dogfood"), then a small percentage of one region,
  then the rest of that region, then other regions a few at a time. Microsoft's ring
  model and Azure's safe deployment practices, and Google's staged rollouts across
  clusters and regions, are public descriptions of the same idea.
- **Cells**: the fleet is split into independent cells, each serving a subset of
  customers. A rollout goes cell by cell, so a bad version can never affect more than one
  cell's customers at a time.
- **Bake time between waves**, longer as waves get larger, so problems that take an hour
  to appear (leaks, daily jobs, cache expiry) show up while the blast radius is small.
- **Automatic halt** across the whole rollout on SLO burn anywhere, not just in the wave
  being deployed.
- **Canary for health, experiments for product.** A canary asks "is v2 *safe*?" using
  system metrics over minutes. An A/B test asks "is v2 *better*?" using user behaviour
  over days, with per-user randomisation and statistical power. They use similar
  plumbing but answer different questions; see
  [Experimentation Platform](../../interview-core/SystemDesign/solutions/037_experimentation_platform_solution.md) and
  [A/B Testing and Experimentation](../../ai-engineering/MLOps/05_ab_testing.md).
- **Feature flags on top**: deploy the code everywhere with the feature off, then do the
  percentage rollout on the flag (chapter 05). Canary deploys still matter, because a
  flag cannot protect against a crash at startup or a broken dependency upgrade.

## 7. Two versions at once: the compatibility contract

Rolling, canary, blue/green (briefly) and shadow all run v1 and v2 simultaneously, and
any strategy's *rollback* runs v1 again after v2 has been live. So every change must be
compatible in both directions for the duration:

| Surface | What breaks | Rule |
|---|---|---|
| Database schema | v2 drops or renames a column v1 still reads | Expand/contract: add first, migrate, remove only after no running version needs it (chapter 05, [Schema Migrations](../../data-and-apis/SQL/12_schema_migrations.md)) |
| API between services | v2 of a caller sends a field v1 of the callee rejects, or vice versa | Additive changes only; tolerant readers; version breaking changes |
| Messages and events | v2 producer writes a format v1 consumers cannot parse; after rollback, v1 consumers meet v2 messages still in the queue | Schema registry with backward and forward compatibility checks |
| Caches | v2 writes a new serialised shape under the same key; v1 reads it and crashes | Version the cache key or the payload |
| Client sessions | Sticky session state or cookies written by v2 | Keep session format compatible or version it |
| Frontend assets | New HTML references JS bundles only on v2 servers | Content-hashed asset names served from a CDN, keep old assets available |

## 8. Choosing a strategy

| Situation | Reasonable choice | Why |
|---|---|---|
| Stateless web service, moderate traffic, good metrics | Canary with automated analysis | Smallest blast radius for real-traffic bugs |
| Same, but no mesh or ingress weights available | Rolling update with conservative `maxUnavailable`, plus a small canary Deployment | Works with plain Kubernetes |
| Strict "all users on one version" requirement, or large coordinated change | Blue/green | Atomic switch, instant rollback, tested in place |
| Risky rewrite of a read-heavy component | Shadow first, then canary | Real load with zero user impact, then real users |
| Singleton worker or incompatible schema change | Recreate (in a maintenance window) or redesign for compatibility | Two versions must not run |
| Very low traffic service | Blue/green or rolling with good smoke tests | A canary would not collect enough data to judge |
| Mobile client | Staged store rollout plus server-side flags | Cannot roll back a binary on a phone |

## Common interview questions

**1. Compare rolling, blue/green and canary deployments.**
Rolling replaces instances in batches with little extra capacity; rollback is another
roll and a bad version eventually reaches everyone. Blue/green deploys to an idle copy,
tests it, then switches all traffic at once; rollback is instant but costs 2× capacity and
exposes everyone together. Canary exposes a small slice first and expands only while
metrics stay healthy; smallest blast radius, but needs traffic splitting and automated
analysis.

**2. What do `maxSurge` and `maxUnavailable` do?**
They bound a rolling update: how many pods may exist above the desired count, and how
many may be unavailable below it. Defaults are 25% each (surge rounds up, unavailable
rounds down). `maxUnavailable: 0` keeps full capacity at the cost of surge pods.

**3. Users see errors during every deploy even though the rollout succeeds. Why?**
Usually shutdown and startup races: pods get traffic before they are truly ready (weak
readiness probe, cold caches) or keep receiving traffic after `SIGTERM` because endpoint
removal propagates asynchronously. Fix with an honest readiness probe, a `preStop`
delay, graceful shutdown that drains in-flight requests, and `minReadySeconds`.

**4. How does automated canary analysis decide pass or fail?**
It queries metrics for the canary (ideally against a same-sized fresh baseline of the old
version) over the step's window, compares them against thresholds or with a statistical
test, and fails after a set number of bad measurements. Failure triggers an abort that
returns traffic to stable. Missing data must be inconclusive or a failure, never a pass.

**5. What is the hardest part of blue/green?**
The shared database: the schema must work for both versions and data written by green
must be usable by blue after a switch back. Also cold caches on the new environment and
2× capacity.

**6. When can you not use shadow traffic?**
When requests have side effects you cannot isolate (payments, emails, writes to shared
systems) unless the shadow's dependencies are stubbed or sandboxed. And it does not tell
you whether users like the change.

**7. Your service gets 5 requests per second. Would you canary it?**
A 5% canary would see one request every four seconds, far too little to judge error-rate
differences in minutes. Use a larger initial weight, longer steps, synthetic traffic, or
prefer blue/green with strong smoke tests and fast rollback.

**8. What has to be true for any zero-downtime strategy to work?**
The old and new versions must be compatible with each other and with shared state (DB
schema, APIs, message formats, caches), because both run at the same time and a rollback
runs the old one against data the new one wrote.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | Intern | Why "stop, copy, start" causes downtime; the idea of rolling, blue/green and canary in one sentence each |
| Junior (L3) | Software Engineer / New Grad | L3 | Writes correct readiness probes and graceful shutdown; understands `maxSurge`/`maxUnavailable`; can pause, check and undo a rollout |
| Mid (L4) | Software Engineer II | L4 | Chooses a strategy per service; sets up blue/green or canary with Argo Rollouts or Flagger; writes analysis queries; keeps changes backward compatible across versions |
| Senior (L5) | Senior Software Engineer | L5 | Designs canary analysis that is statistically meaningful (baseline, sample size, inconclusive handling); diagnoses deploy-time error spikes from connection draining; plans compatibility for schema, API, events and caches across a rollout and a rollback |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7+ | Defines the organisation's rollout policy: rings, cells, bake times, automated global halts tied to SLOs, and when shadowing or experimentation is required for high-risk changes |

## Interview checklist

- [ ] I can compare recreate, rolling, blue/green, canary and shadow on capacity, blast radius and rollback speed.
- [ ] I can compute pod counts during a rolling update from `replicas`, `maxSurge` and `maxUnavailable`.
- [ ] I can explain why pods receive traffic after `SIGTERM` and how `preStop` plus graceful shutdown fix it.
- [ ] I can explain that Kubernetes marks a stalled rollout failed but does not roll back by itself.
- [ ] I can describe three ways to split canary traffic and their granularity limits.
- [ ] I can explain automated canary analysis, baseline vs stable, and why low traffic makes it unreliable.
- [ ] I can explain what an Argo Rollouts abort does and why the fix is still a Git change.
- [ ] I can explain blue/green's database problem and cold-start risk.
- [ ] I can explain shadow traffic and its side-effect problem.
- [ ] I can list the compatibility surfaces (schema, API, events, caches, sessions, assets) two live versions share.

Related: [Continuous Deployment (CD) and Delivery](02_cd_and_delivery.md), [GitOps and Argo CD](04_gitops_and_argocd.md),
[Feature Flags and Rollbacks](05_feature_flags_and_rollbacks.md), [Kubernetes and Orchestration](../Tool-Kit/02_kubernetes_and_helm.md),
[Service Mesh (Istio / Linkerd)](../Tool-Kit/12_service_mesh.md), [Scaling and Load Balancing](../../interview-core/SystemDesign/building_blocks/13_scaling_and_load_balancing.md),
[Observability and Reliability](../../interview-core/SystemDesign/building_blocks/15_observability_and_reliability.md).
