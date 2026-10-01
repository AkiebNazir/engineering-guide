# Resilience: Chaos Engineering

"What happens if the database goes down?" You can write unit tests that mock database
exceptions, but in a distributed system the interesting failures are partial, slow, and
emergent: one replica returns errors, a dependency answers in 3 seconds instead of 30 ms,
retries from a hundred clients pile onto a struggling service. **Chaos engineering** is the
discipline of experimenting on a system to build confidence that it withstands those
conditions. This chapter covers the principles, how to design and run an experiment safely
(steady state, hypothesis, blast radius, abort conditions), the tools used in 2026 (Chaos
Mesh, LitmusChaos, AWS FIS, Toxiproxy, service-mesh fault injection), game days, and how to
test resilience code in ordinary unit tests.

## Foundations — Why break things on purpose?

### The problem

Every production system depends on things that fail: machines, disks, networks, DNS,
certificates, cloud APIs, other teams' services. Designs include timeouts, retries, circuit
breakers, fallbacks and failover to cope (see
[Application Resilience Patterns](../SystemDesign/building_blocks/12_application_resilience_patterns.md)). But those mechanisms are
code and configuration like any other, and they have bugs. Worse, they run only during failures,
so they are the **least exercised** code in the system. A fallback that has never run is a
hypothesis, not a feature.

Common ways the safety nets turn out to be broken:

- The timeout is configured on one HTTP client and not on the other one that also calls the
  dependency.
- The retry policy retries non-idempotent requests, or retries immediately with no backoff and
  turns a blip into an overload.
- Failover to the replica works, but the replica's connection pool is sized for 10% of the traffic.
- The alert that should fire uses a metric that stops being emitted when the service is down.
- The runbook refers to a dashboard that was deleted last year.

You find these either during a real incident, at 3 a.m., under pressure, or during an experiment
you chose to run, in daylight, with an abort button.

### What chaos engineering is, and isn't

The definition from *Principles of Chaos Engineering* (principlesofchaos.org, written by the
Netflix team): "the discipline of experimenting on a system in order to build confidence in the
system's capability to withstand turbulent conditions in production."

The key word is **experimenting**. It is the scientific method applied to reliability:

1. Measure a **steady state**: a business-level signal and its normal range.
2. State a **hypothesis**: "If X fails, the steady state will not change (much)."
3. **Inject** a realistic fault, on a limited **blast radius**, with automatic **abort conditions**.
4. **Observe**: did the steady state hold?
5. **Learn and fix**: a disproved hypothesis is a found bug. Fix it and rerun the experiment.

It is **not** randomly breaking production to see what happens, it is not load testing (though
the two combine well), and it doesn't replace tests. It finds the weaknesses that only appear when
real components, real configuration, and real traffic meet real faults.

```arch
%% caption: A chaos experiment is a loop: define normal, predict, inject a bounded fault, compare, and turn every surprise into a fix and a rerun.
grid 150x100
node steady "Steady state" at 0,0 shape=card icon=gauge color=green sub="errors, p99 normal"
node hyp "Hypothesis" at 1,0 shape=card icon=idea sub="fallback holds"
node inject "Inject fault" at 2,0 shape=card icon=flag color=amber sub="small blast radius"
node learn "Learn and fix" at 0,1 shape=card icon=edit sub="ticket, rerun"
node observe "Observe" at 2,1 shape=card icon=monitor sub="metrics, alerts"
node widen "Widen scope" at 3,1 shape=card icon=rocket color=green sub="prod, automate"
node abort "Abort" at 2,2 shape=card icon=stop color=red sub="stop condition"
steady -> hyp -> inject -> observe
observe -> learn : "disproved"
observe ..> widen : "held"
observe -> abort : "SLO breach"
abort -> learn
learn -> steady : "rerun"
```

### An everyday example

A product page reads prices from a Redis cache, falling back to the database. Hypothesis: "If
Redis becomes 300 ms slower, requests time out on the cache after 50 ms, read the database, and the
error rate stays below 1%." You inject 300 ms of latency between one of the three API pods and
Redis for ten minutes, with an automatic stop if the error rate exceeds 1% for a minute. Either the
graphs stay flat (confidence gained, based on evidence) or the stop condition trips and you've
found, for example, a second code path with no timeout (§6 animates both outcomes).

## 1. The principles, precisely

The five "advanced principles" from principlesofchaos.org:

| Principle | Meaning | Why it matters |
|---|---|---|
| **Build a hypothesis around steady-state behaviour** | Measure outputs users care about (orders per minute, successful playback starts, p99 latency), not internals like CPU | Internals change under faults by design; what matters is whether users notice |
| **Vary real-world events** | Inject faults that actually happen: instance loss, latency, DNS failure, dependency errors, clock skew, full disks, traffic spikes | Weight experiments by likelihood and impact from your incident history |
| **Run experiments in production** | Only production has the real traffic, data, configuration and scale | Staging never fully matches; start there, but the goal is production |
| **Automate experiments to run continuously** | Run them on a schedule or in the delivery pipeline | Systems drift; a result from last quarter says little about today |
| **Minimize blast radius** | Start with one host, a fraction of traffic, a canary cell; have automatic abort | The experiment must never cause the outage it is looking for |

Production is the end goal, not the starting point. Teams begin in development and staging,
move to production at a small scale with an abort switch, and widen only as confidence grows.

## 2. Where it came from

- **Google DiRT** (Disaster Recovery Testing): annual, company-wide exercises since around 2006
  that deliberately take down real infrastructure, including data centres, to test systems and people.
- **Netflix Chaos Monkey** (built in 2010 during the move to AWS, open-sourced in 2012): randomly
  terminates production instances during **business hours**, when engineers are at their desks,
  so every service must tolerate instance loss. The **Simian Army** followed: Latency Monkey
  (injected delays), Chaos Gorilla (a whole availability zone), Chaos Kong (a whole AWS region).
- **Netflix FIT** (Failure Injection Testing, 2014) moved from killing machines to injecting
  failures into specific requests via request metadata, and **ChAP** (Chaos Automation Platform)
  ran experiments against a small slice of traffic, comparing an experiment group with a control group.
- **The industry**: Gremlin (commercial, 2016), then open-source Kubernetes tools (Chaos Mesh and
  LitmusChaos, both CNCF projects), and cloud-native services (AWS Fault Injection Service, Azure
  Chaos Studio).

## 3. What to inject

| Fault class | Examples | Typical tool | What it often reveals |
|---|---|---|---|
| **Compute loss** | Kill a pod, terminate an instance, drain a node | Chaos Mesh `PodChaos`, Litmus `pod-delete`, FIS, Chaos Monkey | Stateful singletons, slow startup, missing readiness probes |
| **Network latency** | +100–500 ms, jitter | `NetworkChaos` delay, `tc netem`, Toxiproxy, mesh fault injection | Missing or too-long timeouts, thread-pool exhaustion, retry storms |
| **Network loss / partition** | Drop packets, blackhole a dependency, split AZs | `NetworkChaos` loss/partition, FIS network actions | Hanging connections, split brain, failover that never triggers |
| **Dependency errors** | 503s from a downstream, throttling, 5% error rate | Istio/Envoy abort faults, FIS API error injection, stub proxies | Retries without backoff, no fallback, unhandled error types |
| **Resource pressure** | CPU burn, memory hog, disk full, file-descriptor exhaustion | `StressChaos`, `stress-ng`, fill a volume | OOM kills, log disks filling, GC death spirals |
| **Time** | Clock skew, NTP jump | `TimeChaos` | Token/certificate validation, TTL and lease bugs |
| **Zone / region** | Evacuate an AZ or region | Traffic steering, FIS AZ-scoped scenarios | Capacity headroom in the survivors, DNS TTLs, data replication lag |
| **State / data** | Corrupted message, stale cache, poison pill | Custom | Consumers that crash-loop on one bad message |
| **Human / process** | On-call engineer unavailable, dashboard missing | Game days | Runbook and escalation gaps |

Pick experiments from your **incident history** and your architecture's **single points of
failure**, not from a tool's menu.

## 4. Resilience in ordinary tests first

Before injecting faults into a live system, test the resilience **logic** where it is cheap: a
unit test with an injected fault is a tiny, deterministic chaos experiment.

```python
# resilience.py — a product lookup that should survive a slow or dead cache
import random
import time


class CircuitBreaker:
    """Closed: calls go through. After `threshold` consecutive failures it opens for
    `reset_after` seconds and calls are skipped. Then one trial call is allowed (half-open)."""

    def __init__(self, threshold=5, reset_after=30.0, clock=time.monotonic):
        self.threshold, self.reset_after, self.clock = threshold, reset_after, clock
        self.failures, self.opened_at = 0, None

    def allow(self) -> bool:
        if self.opened_at is None:
            return True
        return self.clock() - self.opened_at >= self.reset_after   # half-open trial

    def success(self):
        self.failures, self.opened_at = 0, None

    def failure(self):
        self.failures += 1
        if self.failures >= self.threshold:
            self.opened_at = self.clock()


class ProductService:
    def __init__(self, cache, db, breaker, cache_timeout=0.05):
        self.cache, self.db, self.breaker, self.cache_timeout = cache, db, breaker, cache_timeout

    def get(self, pid):
        if self.breaker.allow():
            try:
                value = self.cache.get(pid, timeout=self.cache_timeout)
                self.breaker.success()
                if value is not None:
                    return value
            except (TimeoutError, ConnectionError):
                self.breaker.failure()
        return self.db[pid]                      # fallback: the source of truth


class FaultyCache:
    """Fault injector wrapped around a cache: adds latency and connection errors.
    Latency is simulated against the caller's timeout, so the test never sleeps."""

    def __init__(self, inner, latency=0.0, error_rate=0.0, seed=0):
        self.inner, self.latency, self.error_rate = inner, latency, error_rate
        self.rng = random.Random(seed)            # seeded: the experiment is reproducible
        self.calls = 0

    def get(self, key, timeout):
        self.calls += 1
        if self.rng.random() < self.error_rate:
            raise ConnectionError("injected: connection refused")
        if self.latency > timeout:
            raise TimeoutError(f"injected: {self.latency * 1000:.0f} ms > {timeout * 1000:.0f} ms timeout")
        return self.inner.get(key)
```

```python
# test_resilience.py — a small chaos experiment as a unit test: inject faults, check the steady state
import pytest

from resilience import CircuitBreaker, FaultyCache, ProductService

DB = {pid: {"id": pid, "price_cents": 100 + pid} for pid in range(100)}


class FakeClock:
    def __init__(self):
        self.now = 0.0

    def __call__(self):
        return self.now


def run_traffic(svc, n=1000):
    """Steady-state metric: fraction of requests answered correctly."""
    ok = sum(svc.get(i % 100) == DB[i % 100] for i in range(n))
    return ok / n


@pytest.mark.parametrize("fault", [
    {"latency": 0.3},                  # cache 300 ms slow
    {"error_rate": 1.0},               # cache down
    {"error_rate": 0.3},               # cache flapping
])
def test_steady_state_holds_under_cache_faults(fault):
    cache = FaultyCache(inner={}, **fault)
    svc = ProductService(cache, DB, CircuitBreaker(clock=FakeClock()))
    assert run_traffic(svc) == 1.0     # hypothesis: every request still succeeds


def test_breaker_stops_hammering_a_dead_cache():
    clock = FakeClock()
    cache = FaultyCache(inner={}, error_rate=1.0)
    svc = ProductService(cache, DB, CircuitBreaker(threshold=5, reset_after=30, clock=clock))
    run_traffic(svc, n=1000)
    assert cache.calls == 5            # after 5 failures the breaker opens; 995 calls skip the cache
    clock.now += 30                    # half-open: exactly one trial call
    run_traffic(svc, n=10)
    assert cache.calls == 6
```

(Run with pytest 9.1: 4 passed in ≈ 0.1 s.) The same structure as a production experiment is all
there: a steady-state metric, a hypothesis, injected faults, and a check. What it can't tell you is
whether the **real** client library honours the timeout, whether the thread pool survives, or
whether the alert fires. That is what the next levels are for:

| Level | Tool | Real parts |
|---|---|---|
| Unit | Fault-injecting double (above) | Your resilience logic |
| Integration | **Toxiproxy** between the service and a real Redis/Postgres in Testcontainers | Real client libraries, sockets, timeouts |
| Staging / pre-prod | Chaos Mesh, Litmus, FIS, mesh fault injection | Real deployment, configuration, autoscaling, alerts |
| Production | The same tools, small blast radius, abort conditions | Real traffic, data and scale |

Toxiproxy (from Shopify) is a TCP proxy controlled over an HTTP API. The test creates a proxy
`localhost:26379 -> redis:6379`, points the service at it, and adds "toxics" on demand: `latency`,
`bandwidth`, `timeout` (hold data, then close), `reset_peer`, `slicer`. Testcontainers has a
Toxiproxy module, so this runs in CI.

## 5. Tools and what they look like

### Chaos Mesh (Kubernetes)

Chaos Mesh (a CNCF project) defines experiments as Kubernetes custom resources. A controller
manager watches them, and a privileged **chaos-daemon** DaemonSet on each node enters the target
pod's network, PID or mount namespace to apply the fault (`tc` rules for network faults, process
signals, stress workers).

```arch
%% caption: Chaos Mesh: an experiment is a custom resource; the controller picks targets by label and the per-node daemon applies the fault inside their namespaces.
grid 165x105
node eng "Engineer or CI" at 0,0 icon=developer sub="kubectl apply"
group k8s "Kubernetes cluster" color=blue icon=k8s
node api "API server" at 1,0 in k8s icon=api sub="NetworkChaos CR"
node ctrl "Controller manager" at 2,0 in k8s shape=card icon=scheduler sub="selects targets"
node daemon "chaos-daemon" at 2,1 in k8s shape=card icon=worker sub="DaemonSet, privileged"
node mon "Prometheus" at 1,2 in k8s icon=prometheus sub="steady state"
node pod "Target pod" at 2,2 in k8s icon=container sub="app=product-api"
node redis "Redis" at 2,3 in k8s icon=redis
eng -> api
api -> ctrl : "watch"
ctrl -> daemon : "inject"
daemon -> pod : "tc netem"
pod -> redis : "+300 ms"
mon ..> pod : "scrape"
```

```yaml
# network-delay.yaml — +300 ms on traffic from ONE product-api pod to Redis, for 10 minutes
apiVersion: chaos-mesh.org/v1alpha1
kind: NetworkChaos
metadata:
  name: product-api-redis-latency
  namespace: shop
spec:
  action: delay
  mode: one                        # blast radius: a single randomly chosen matching pod
  selector:
    namespaces: [shop]
    labelSelectors:
      app: product-api
  direction: to
  target:
    mode: all
    selector:
      namespaces: [shop]
      labelSelectors:
        app: redis
  delay:
    latency: "300ms"
    jitter: "50ms"
    correlation: "25"
  duration: "10m"                  # the fault is removed automatically afterwards
---
# pod-kill.yaml — kill one pod; the Deployment must replace it without user-visible errors
apiVersion: chaos-mesh.org/v1alpha1
kind: PodChaos
metadata:
  name: product-api-pod-kill
  namespace: shop
spec:
  action: pod-kill
  mode: one
  selector:
    namespaces: [shop]
    labelSelectors:
      app: product-api
```

A `Schedule` resource runs an experiment on a cron, and a `Workflow` chains experiments with
status checks between them. Chaos Mesh itself does not know your SLOs; pair it with alerts or a
workflow status check that stops the run.

### The wider toolbox

| Tool | Scope | Notes |
|---|---|---|
| **Chaos Mesh** | Kubernetes | CRDs for pod, network, IO, stress, time, kernel, HTTP faults; dashboard; CNCF |
| **LitmusChaos** | Kubernetes (+ some cloud) | ChaosHub of reusable experiments, "probes" that check steady state during the run; CNCF |
| **AWS Fault Injection Service (FIS)** | AWS | Experiment templates with actions (stop EC2 instances, stop ECS tasks, EKS pod faults, network disruption, API error injection) and **stop conditions** tied to CloudWatch alarms |
| **Azure Chaos Studio** | Azure | Service-direct and agent-based faults, experiments as ARM resources |
| **Gremlin, Steadybit** | Multi-platform, commercial | Safety controls, scheduling, reliability scoring |
| **Istio / Envoy fault injection** | Service mesh | Delay or abort a percentage of HTTP/gRPC requests at the sidecar, no app changes |
| **Toxiproxy** | Tests, CI | TCP-level latency, resets, timeouts between app and dependency |
| **`tc netem`, `stress-ng`, `iptables`** | Any Linux host | The primitives many tools use underneath |

Service-mesh fault injection, which affects only requests matching a route, is often the smallest
possible blast radius:

```yaml
# Istio: delay 5% of calls to the ratings service by 300 ms and fail 1% with 503
apiVersion: networking.istio.io/v1
kind: VirtualService
metadata:
  name: ratings
spec:
  hosts: [ratings]
  http:
  - fault:
      delay:
        percentage: { value: 5 }
        fixedDelay: 300ms
      abort:
        percentage: { value: 1 }
        httpStatus: 503
    route:
    - destination:
        host: ratings
```

On a plain Linux host the primitive is one command, and removing it is another:

```bash
sudo tc qdisc add dev eth0 root netem delay 300ms 50ms   # +300 ms ± 50 ms on everything leaving eth0
sudo tc qdisc del dev eth0 root netem                    # remove it
```

## 6. Running an experiment safely in production

The difference between chaos engineering and an outage is control. Before any production
experiment, write down:

| Item | Example |
|---|---|
| **Steady-state metric** | Successful product-page loads per minute; p99 latency; error rate from the load balancer |
| **Hypothesis** | "With +300 ms to Redis on one pod, error rate < 1% and p99 < 400 ms" |
| **Blast radius** | One pod of three; or 1% of traffic via the mesh; one cell or one AZ in one region |
| **Abort (stop) conditions** | Error rate > 1% for 1 minute; any page from the owning service; manual abort button |
| **Duration** | 10 minutes, fault removed automatically |
| **Timing and people** | Business hours, owning team present, incident channel open, no concurrent deploys or other experiments |
| **Rollback** | How the fault is removed if the tool itself fails (e.g. delete the CR, flush the `tc` rule) |
| **Expected observations** | Which dashboards and alerts should move, and which should not |

Abort conditions must be **automatic** and decided beforehand, like AWS FIS stop conditions wired
to CloudWatch alarms. A person staring at a graph under pressure decides slowly and badly. The
Kubernetes tools can be wired the same way through their workflow and probe features, or an external
controller that deletes the experiment.

A typical progression: unit and integration tests with injected faults → staging experiments →
production with the smallest blast radius during business hours → wider blast radius → scheduled,
automated experiments (for example, pod-kill on every service weekly, a latency experiment in the
deployment pipeline) → regular zone-evacuation drills.

Watch one experiment hold, and another trip its abort condition and pay off:

<div class="lab" data-viz="flow-chaos"></div>

## 7. Game days

You don't run Chaos Monkey in production on day one. You start with **game days**: scheduled,
facilitated exercises where a team injects a failure together and watches what happens to the
system **and to the people**.

1. **Plan**: pick a scenario (primary database fails over, a dependency returns 50% errors, an AZ is
   lost), write the hypothesis and abort conditions, choose the environment, and tell adjacent teams
   and on-call.
2. **Roles**: a facilitator who runs the script, the team responding as if on call (without knowing
   exactly what will break, if you want to test detection), an observer taking notes, and someone who
   owns the abort.
3. **Run**: inject the fault. Did the alerts fire, and on the right signal? Did the on-call find the
   right runbook and dashboard? How long until detection, diagnosis and mitigation?
4. **Debrief** in blameless-postmortem style: what surprised us, what broke, which action items, and
   which experiment should now be automated.

Game days test what automated experiments can't: alert quality, runbooks, access permissions,
escalation paths, and whether anyone besides one senior engineer knows how to fail over the database.
Google's DiRT exercises test exactly that at company scale. A cheap variant is the **"wheel of
misfortune"**: role-playing a past incident on paper with a new on-call engineer.

## 8. What good looks like, and the ultimate goal

A popular way to state the goal: "When a real AWS zone goes down at 3 a.m. on a Sunday, your pager
should not ring." That's the right direction, stated slightly too strongly. The realistic goal
is:

- **Users don't notice**, or notice only degraded (not broken) behaviour, because failover and
  fallbacks have been exercised recently and actually work.
- **The page that does fire is informative**: it says what failed and that automation is handling it,
  and the runbook is current, because the team practised with it.
- **Recovery is routine**: zone evacuation is something the system has done many times on purpose, so
  doing it by accident is uneventful.

Signals that a chaos practice is working: experiments regularly disprove hypotheses early on and then
stop doing so; incident retrospectives increasingly say "we had tested this"; the list of untested
failure modes for critical services shrinks; experiments run automatically, not only when a
motivated engineer remembers.

Signals that it isn't: experiments only in staging; no written hypothesis ("let's see what happens");
no abort conditions; findings without tickets; or chaos run by a central team *on* service teams
rather than *with* them.

## Common interview questions

**What is chaos engineering?**
Controlled experiments that inject realistic faults to test a hypothesis about a system's
steady-state behaviour, building evidence-based confidence in its resilience. It is the scientific
method (steady state, hypothesis, experiment, observation), not random breakage.

**Walk me through designing a chaos experiment.**
Pick a failure from incident history or architecture review. Define the steady-state metric and its
normal range. Write the hypothesis. Choose the smallest meaningful blast radius, the duration, and
automatic abort conditions. Tell stakeholders, run during business hours, observe, remove the fault,
then file fixes and rerun or widen.

**Why run experiments in production? Isn't that dangerous?**
Only production has the real traffic, configuration, data volume and dependencies, so staging results
don't transfer fully. It is made safe by blast-radius limits, automatic stop conditions, business-hours
timing and a progression from test environments. The alternative is learning the same lesson during an
unplanned incident.

**What is blast radius and how do you limit it?**
The scope of users or systems an experiment can affect. Limit it by targeting one pod, host, cell or AZ;
a percentage of requests through the mesh; internal or test users first; a short duration; and automatic
abort.

**Chaos engineering vs load testing vs fault-injection unit tests?**
Load testing checks behaviour under traffic volume; chaos checks behaviour under component failure (and
combines well with load). Unit tests with injected faults check resilience logic deterministically;
chaos experiments check that the deployed system with real configuration and dependencies behaves as the
logic intended.

**What's a game day?**
A scheduled team exercise that injects a failure and observes both the system and the humans: alert
quality, runbooks, access, escalation, time to detect and mitigate. It ends with a blameless debrief and
action items.

**What would you inject first for a typical microservice?**
Pod or instance termination (does it restart cleanly and drain properly?), latency to its most important
dependency (are timeouts set and sane?), and error responses from that dependency (fallback, retry with
backoff, circuit breaker). These three find the most common gaps.

**What tools exist?**
Chaos Mesh and LitmusChaos for Kubernetes, AWS Fault Injection Service and Azure Chaos Studio for cloud
resources, Gremlin and Steadybit commercially, Istio/Envoy fault injection at the mesh, Toxiproxy in tests,
and `tc netem`/`stress-ng` as primitives.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — (intern) | Knows why distributed systems fail partially, and that timeouts, retries and fallbacks exist and need testing |
| Junior (L3) | Software Engineer I | L3 | Writes unit tests with injected faults (timeouts, errors) for resilience code; takes part in game days |
| Mid (L4) | Software Engineer II | L4 | Uses Toxiproxy / Testcontainers to test real client timeouts; designs a simple experiment with steady state, hypothesis and abort conditions in staging |
| Senior (L5) | Senior Software Engineer | L5 | Runs production experiments for their service with limited blast radius and automated stop conditions; facilitates game days; turns findings into fixes and automated experiments |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Builds the org's resilience programme: which failure modes are tested and how often, AZ/region evacuation drills, DiRT-style exercises, platform tooling and safety policy |

## Interview checklist

- [ ] I can define chaos engineering and list its five principles.
- [ ] I can design an experiment: steady state, hypothesis, fault, blast radius, duration, abort conditions.
- [ ] I can list fault classes (compute, latency, loss, errors, resources, time, zone) and what each tends to reveal.
- [ ] I can test resilience logic in a unit test with a fault-injecting double and a fake clock.
- [ ] I can explain how Toxiproxy fits into integration tests.
- [ ] I can write a Chaos Mesh `NetworkChaos` or `PodChaos` resource and explain how it is applied.
- [ ] I can explain AWS FIS stop conditions and mesh-level fault injection.
- [ ] I can explain how to run and debrief a game day.
- [ ] I can explain why production experiments are worth it and how they are kept safe.

Related: [Application Resilience Patterns](../SystemDesign/building_blocks/12_application_resilience_patterns.md) (timeouts, retries,
circuit breakers), [Observability and Reliability](../SystemDesign/building_blocks/15_observability_and_reliability.md) (SLOs, alerting),
[Overload Control and Graceful Degradation](../SystemDesign/building_blocks/28_overload_control_and_graceful_degradation.md),
[Multi-Region and Global Traffic](../SystemDesign/building_blocks/27_multi_region_and_global_traffic.md), [Integration and End-to-End (E2E) Testing](03_integration_and_e2e.md) §4,
[Deployment Strategies](../CICD/03_deployment_strategies.md).
