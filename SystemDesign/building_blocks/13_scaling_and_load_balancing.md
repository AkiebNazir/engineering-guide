# Scaling and Load Balancing

One server has a ceiling: so many cores, so much memory, so many connections, one power
supply. Scaling is everything you do once demand passes that ceiling or once losing that one
server is no longer acceptable. This file starts from first principles — the three ways to
scale and what a load balancer actually does — then goes as deep as a senior design round:
which balancing algorithm to choose (with a simulation that measures them), why the "smartest"
algorithm can send a quarter of your traffic to a broken server, health checks and draining,
where state goes, autoscaling signals, and a worked capacity plan.

## Foundations — What Scaling Means and What a Load Balancer Does

### The three ways to scale

The "scale cube" names three independent axes. Real systems use all three:

| Axis | What you do | Example | Limit it hits |
|---|---|---|---|
| **X: clone** | Run identical copies behind a load balancer | 40 stateless API servers | Shared state underneath (the database) |
| **Y: split by function** | Different services for different jobs | Search, checkout and feed as separate services | Coordination between services |
| **Z: split by data** | Each copy owns a subset of the data | Users A–M on shard 1, N–Z on shard 2 | Cross-partition queries, hot partitions ([Partitioning, Shard Keys, and Hot Keys](25_partitioning_and_hot_keys.md)) |

**Vertical scaling** (a bigger machine) sits outside the cube: simplest of all, until the
biggest machine isn't big enough or its failure takes everything down (see below).

### What a load balancer is

A **load balancer** (LB) is the component that makes X-axis scaling work: clients talk to one
address, and the LB spreads their requests across a pool of interchangeable **backends**. It
has three jobs, and interview answers usually mention only the first:

1. **Distribute** requests so no backend is overloaded (the algorithms below).
2. **Detect failure** and stop sending traffic to unhealthy backends (health checks and
   outlier ejection).
3. **Change the pool safely** — add, remove and replace backends without dropping requests
   (connection draining).

Load balancing happens at several layers of one request's path, and each layer uses the same
ideas: DNS or anycast picks a region ([Multi-Region and Global Traffic](27_multi_region_and_global_traffic.md)),
an edge or regional LB picks a cluster, an L4 or L7 balancer picks a backend (L4 sees TCP
connections, L7 sees HTTP requests — [Networking & Distributed Communication](../../CSFundamentals/02_networking_deep_dive.md) §4), and
inside the data centre a client library or service-mesh sidecar often picks the backend itself
(**client-side load balancing**, the default for gRPC at Google-like scale, because it removes
a network hop and a central bottleneck).

### Vocabulary

| Term | Meaning |
|---|---|
| Backend, upstream, target | One instance the LB can send a request to |
| Pool, target group | The set of backends for one service |
| Outstanding requests | Requests sent to a backend and not yet answered — the best cheap signal of its load |
| Health check | A periodic probe (TCP connect, HTTP `/healthz`) that marks backends up or down |
| Outlier ejection | Removing a backend because its *real traffic* is failing or slow, not because a probe failed |
| Connection draining | Letting in-flight requests finish before a backend leaves the pool |
| Sticky session / affinity | Sending one client's requests to the same backend |
| Headroom | Spare capacity kept deliberately so spikes and failures don't push the fleet over the queueing cliff |
| N+1, N+2 | Enough capacity to lose one (or two) instances, or zones, and still meet the target |

## Load balancing algorithms

| Algorithm | How it picks a target | Good for | Weakness |
|---|---|---|---|
| Round robin | Cycles through instances in order. | Similar-cost, similar-duration requests on uniform instances. | Ignores actual load — a slow instance keeps getting the same share of new work as a fast one. |
| Least connections/requests | Sends to the instance with the fewest active requests. | Variable request duration (some requests take far longer than others). | Needs accurate, low-latency live connection-count state from every instance — stale state defeats the point. |
| Weighted (round robin or least-connections) | Like the base algorithm, but instances get traffic proportional to a configured weight. | Heterogeneous hardware/capacity in the same pool. | Weights are usually set once and go stale as real capacity or instance health changes. |
| Consistent hash | Routes by a hash of a key (user ID, cache key) onto a ring of nodes. | Session affinity, cache locality — same key keeps hitting the same node so its cache stays warm. | A popular key creates a genuinely hot node — hashing doesn't fix skewed key popularity, only key-to-node mapping. |
| Power of two choices | Sample two random instances, send to whichever reports less load. | Large pools where full least-connections state is too expensive to track globally. | Only as good as the load metric sampled — a cheap-but-misleading metric (e.g. raw CPU) picks the wrong instance. |

Round robin and weighted round robin are stateless and cheap — a reasonable default until you have evidence request costs are uneven enough to justify least-connections' extra bookkeeping. Reach for consistent hashing specifically when locality (cache/session affinity) matters more than perfectly even load; reach for power-of-two-choices when the pool is too large for tracking exact per-instance load cheaply, which is most large fleets.

Everything here balances across instances *inside one region*. Choosing which region serves a user, and shifting traffic between regions when one degrades, is a different problem with different levers (geo-aware DNS, anycast, capacity and failover planning) and is covered in [Multi-Region and Global Traffic](27_multi_region_and_global_traffic.md).

## Horizontal vs. vertical scaling


```arch
%% caption: Vertical scaling hits a hardware ceiling; horizontal scaling requires a load balancer and stateless instances.
grid 160x110
group vert "Vertical Scaling (Scale Up)" color=blue
node v1 "Small Server" at 0,0 in vert icon=server sub="2 cores"
node v2 "Big Server" at 0,2 in vert icon=cpu sub="32 cores"

v1 ==> v2 : "replace with\nbigger box"

group horiz "Horizontal Scaling (Scale Out)" color=green
node lb "Load Balancer" at 1,1 in horiz icon=internet
node h1 "Instance 1" at 2,0 in horiz icon=server
node h2 "Instance 2" at 2,1 in horiz icon=server
node h3 "Instance 3" at 2,2 in horiz icon=server

lb -> h1
lb -> h2
lb -> h3
```
```text
Vertical scaling:              Horizontal scaling:
┌────────────────┐             ┌────┐ ┌────┐ ┌────┐ ┌────┐
│  one bigger box  │             │inst│ │inst│ │inst│ │inst│
│  more CPU/RAM/IO │             │ A  │ │ B  │ │ C  │ │ D  │
└────────────────┘             └────┘ └────┘ └────┘ └────┘
one box dies →                  one box dies →
whole service down               3 of 4 still serving
```

**Vertical scaling** (bigger machine) is simple — no distribution logic — but has a hard ceiling (largest instance type available), a single point of failure, and usually a restart/migration required to resize.

**Horizontal scaling** (more machines) improves fault isolation — losing one instance loses a fraction of capacity, not all of it — and has effectively no ceiling for stateless work. But it is not free of limits of its own:

- **State:** any state that lives only on one instance (in-memory session, local cache) doesn't automatically show up on the instance that gets the next request — externalize state (cache tier, DB, sticky routing with a fallback) before scaling out.
- **Data:** the database backing N stateless app instances is very often the actual bottleneck — adding app instances doesn't help once the DB is saturated (see [Databases: Source of Truth](05_databases.md)/[Database Internals: How They Actually Work](06_database_internals.md) for partitioning).
- **Hot keys:** consistent-hash routing or a natural partition key can concentrate load onto one instance/shard regardless of total fleet size — more instances don't help a single overloaded key.

Default to horizontal scaling for the application tier (it's stateless by construction, per [Application Resilience Patterns](12_application_resilience_patterns.md)'s pool guidance); vertical scaling is usually reserved for stateful single-writer components (a primary database) where horizontal write scaling requires a real partitioning strategy, not just "add a box."

## What to autoscale on

Average CPU alone is a bad autoscaling signal because CPU can look moderate while requests are actually piling up waiting on I/O (a DB call, a downstream dependency) rather than computing — the service can be visibly failing users (growing queues, rising latency) with CPU sitting at 40%. Autoscale on signals that actually correlate with saturation:

- **Queue depth / queue age:** how much work is waiting and how long the oldest item has waited — a direct measurement of "falling behind."
- **Concurrent in-flight requests:** rising concurrency at roughly flat throughput means requests are taking longer to finish, i.e. the system is saturating.
- **Pending work / backlog size:** for worker fleets, the actual count of unclaimed jobs.
- **CPU + latency together**, if CPU is used at all — never CPU in isolation.

## Scale-out lag and headroom

Adding instances is not instant — provisioning, image pull/boot, warm-up (JIT, cache fill, connection pool ramp-up) all take real time, often tens of seconds to minutes. An autoscaler reacting only once a pool is already saturated will always be behind the spike it's reacting to.

```text
demand ──────────────╱‾‾‾‾‾‾‾  ← spike arrives
capacity ──────────╱───────    ← new instances not ready yet
                   ▲
          gap = requests degraded/dropped during scale-out lag
```

Mitigate with **headroom** (run below the point where the queueing-theory cliff hits — see [Application Resilience Patterns](12_application_resilience_patterns.md)'s Little's Law section), predictive/scheduled scaling for known traffic patterns, and a fast-scaling policy that reacts to leading indicators (queue growth rate) rather than lagging ones (CPU already pegged).

## Admission control before collapse

Once a service is already past its sustainable capacity, letting every request in and trying to serve all of them (badly, slowly) is worse than the alternative: **reject some requests fast and cheaply so the ones you do accept can actually be served within budget.** This is the same principle as the seat-reservation waiting room in [Seat Reservation](../solutions/010_seat_reservation_solution.md) — admission control paces load down to what the system can sustain, rather than making a sale/business decision itself. Combine with bounded queues ([Application Resilience Patterns](12_application_resilience_patterns.md)) so "full" is a real, enforced state rather than an unbounded backlog silently growing until the process falls over.

Rejecting is only the first tool. Choosing *which* requests to reject (priority classes, per-tenant fairness, dropping optional work first), limiting concurrency adaptively, and degrading features on purpose are covered in [Overload Control and Graceful Degradation](28_overload_control_and_graceful_degradation.md).

## Queueing theory, briefly

As utilization on any pool (thread pool, connection pool, single-partition write path) approaches 100%, wait time grows nonlinearly, not linearly — a pool at 95% average utilization can already have severe tail latency even though it "looks fine" on an average-utilization dashboard. [Application Resilience Patterns](12_application_resilience_patterns.md) works this through: Little's Law (`L = λW`) is an identity that tells you how many requests are in flight for a given arrival rate and latency, and the *cliff* comes from queueing at high utilization, where waiting time grows like `ρ / (1 − ρ)`. The short version for scaling purposes is: **plan capacity and autoscaling thresholds against headroom below that cliff, not against 100% theoretical throughput.**

## Balancing algorithms, measured

The table at the top of this file says which algorithm fits which situation. A simulation
shows *how much* it matters. Ten single-worker backends, requests arriving at random (Poisson)
at 70% of the fleet's capacity, 10 ms average service time, 100,000 requests per run:

```python
"""Load-balancing algorithms under a discrete-event simulation.

10 servers, each handling one request at a time from its own FIFO queue.
Requests arrive as a Poisson stream at 70% of the fleet's capacity; service
times are exponential with mean 10 ms. The balancer sees each server's number
of outstanding requests (queued + in service) at the moment it routes."""
import heapq, random, statistics

def simulate(policy, servers=10, load=0.7, n=100_000, slow=None, broken=None, eject=False, seed=1):
    rng = random.Random(seed)
    mean = [10.0] * servers                       # ms per request
    if slow is not None:
        mean[slow] = 50.0                         # one degraded server, 5x slower
    rate = load * servers / 10.0                  # arrivals per ms at the nominal capacity
    free_at = [0.0] * servers                     # when each server's queue drains
    done = [[] for _ in range(servers)]           # completion times still in the future
    rr, t, lat, errors, share = 0, 0.0, [], 0, [0] * servers
    consecutive, ejected_until = [0] * servers, [0.0] * servers
    for _ in range(n):
        t += rng.expovariate(rate)
        for s in range(servers):                  # forget requests that finished before t
            while done[s] and done[s][0] <= t:
                heapq.heappop(done[s])
        out = [len(d) if ejected_until[i] <= t else 10**9 for i, d in enumerate(done)]
        if policy == "round robin":
            s, rr = rr, (rr + 1) % servers
        elif policy == "random":
            s = rng.randrange(servers)
        elif policy == "least outstanding":
            low = min(out)
            s = rng.choice([i for i in range(servers) if out[i] == low])
        elif policy == "power of two choices":
            a, b = rng.sample(range(servers), 2)
            s = a if out[a] <= out[b] else b
        share[s] += 1
        if s == broken:                           # fails instantly: a fast error
            errors += 1
            consecutive[s] += 1
            if eject and consecutive[s] >= 5:     # outlier ejection: 5 errors in a row
                ejected_until[s] = t + 30_000     # -> out of the pool for 30 s, then probed again
                consecutive[s] = 0
            continue
        consecutive[s] = 0
        start = max(t, free_at[s])
        free_at[s] = start + rng.expovariate(1 / mean[s])
        heapq.heappush(done[s], free_at[s])
        lat.append(free_at[s] - t)
    q = statistics.quantiles(lat, n=100)
    return q[49], q[98], errors / n, share

scenarios = [("10 identical servers", {}),
             ("one server 5x slower", {"slow": 0}),
             ("one server failing fast", {"broken": 0})]
for title, kw in scenarios:
    print(f"{title}:")
    for policy in ("round robin", "random", "least outstanding", "power of two choices"):
        p50, p99, err, share = simulate(policy, **kw)
        extra = f"  errors {100 * err:4.1f}%  (bad server got {100 * share[0] / sum(share):4.1f}% of traffic)" if kw else ""
        print(f"   {policy:21} p50 {p50:6.1f} ms  p99 {p99:7.1f} ms{extra}")
p50, p99, err, share = simulate("least outstanding", broken=0, eject=True)
print(f"one server failing fast, least outstanding + outlier ejection:\n"
      f"   {'least outstanding':21} p50 {p50:6.1f} ms  p99 {p99:7.1f} ms  errors {100 * err:4.2f}%  "
      f"(bad server got {100 * share[0] / sum(share):4.1f}% of traffic)")
```

```text
10 identical servers:
   round robin           p50   13.9 ms  p99    90.8 ms
   random                p50   22.5 ms  p99   143.9 ms
   least outstanding     p50    8.0 ms  p99    51.9 ms
   power of two choices  p50   12.6 ms  p99    68.7 ms
one server 5x slower:
   round robin           p50   16.3 ms  p99 322324.0 ms  errors  0.0%  (bad server got 10.0% of traffic)
   random                p50   26.4 ms  p99 316726.4 ms  errors  0.0%  (bad server got 10.0% of traffic)
   least outstanding     p50    9.3 ms  p99    85.4 ms  errors  0.0%  (bad server got  2.7% of traffic)
   power of two choices  p50   15.7 ms  p99   175.6 ms  errors  0.0%  (bad server got  2.9% of traffic)
one server failing fast:
   round robin           p50   14.0 ms  p99    94.8 ms  errors 10.0%  (bad server got 10.0% of traffic)
   random                p50   22.9 ms  p99   153.2 ms  errors 10.0%  (bad server got 10.0% of traffic)
   least outstanding     p50    6.9 ms  p99    46.2 ms  errors 26.2%  (bad server got 26.2% of traffic)
   power of two choices  p50   11.4 ms  p99    64.5 ms  errors 16.6%  (bad server got 16.6% of traffic)
one server failing fast, least outstanding + outlier ejection:
   least outstanding     p50    9.5 ms  p99    58.6 ms  errors 0.03%  (bad server got  0.0% of traffic)
```

What each scenario teaches:

- **Identical servers: using load information halves the tail.** Round robin ignores that
  some requests are longer than others, so queues form behind unlucky backends; random is
  worse still. Sending each request to the backend with the fewest outstanding requests cut
  p99 from 91 ms to 52 ms. Power of two choices — look at only two random backends and pick
  the less loaded — got most of that benefit (69 ms) while reading two counters instead of all
  of them, which is why large fleets and client-side balancers use it.
- **One slow server: load-blind algorithms fall off a cliff.** Round robin keeps sending the
  degraded backend 10% of the traffic, but at 5× slower it can only handle 2% — its queue grows
  without bound and p99 reaches minutes. Load-aware algorithms notice its queue and send it
  less than 3% of the traffic. **A gray failure — slow, not dead — is exactly where
  load-blind balancing hurts most**, and health checks that only ask "are you up?" never catch
  it.
- **One server failing fast: the smartest algorithm makes it worse.** A backend that returns an
  error in a millisecond always has zero outstanding requests, so least-outstanding keeps
  choosing it: 26% of all requests failed, versus 10% with round robin. This "black hole"
  effect is a well-known production incident pattern. The fix is **outlier ejection**:
  after five consecutive errors the backend leaves the pool for 30 seconds, then is probed
  again — errors fell to 0.03%, the handful of requests that detected it each time.

In an interview, the answer that scores is: "least-outstanding or power of two choices for
uneven request costs, **combined with** outlier ejection on error rate and latency, because
load-aware balancing rewards whatever answers fastest — including a broken server."

## Health checks, outlier ejection, and connection draining

**Active health checks** probe each backend on a schedule (every 5–10 s is common): a TCP
connect, or an HTTP request to an endpoint such as `/healthz`. A backend is marked down after
a few consecutive failures and up after a few successes — the thresholds stop one lost packet
from flapping it in and out.

What the endpoint checks matters more than how often it runs:

- **Liveness** ("is the process alive and not deadlocked?") should check only the process
  itself. If it fails, restart the process.
- **Readiness** ("should I receive traffic right now?") can check that the process has warmed
  up and that its *own* critical resources work. If it fails, stop routing, don't restart.
- **Never make readiness depend on a shared dependency.** If every backend's readiness check
  calls the same database and the database has a brief hiccup, every backend reports unready at
  once and the LB has nowhere to send traffic — a partial outage becomes a total one. Many LBs
  "fail open" when every backend is unhealthy for exactly this reason.

**Passive checks (outlier ejection)** watch real traffic instead: consecutive 5xx responses,
error rate, or latency far above the pool's median. They catch what probes miss — a backend
that answers `/healthz` fine but fails real requests, or the fast-failing black hole above.
Cap how much of the pool can be ejected at once (Envoy's default is 10%), so a bad deploy or a
shared dependency failure can't eject everyone.

**Connection draining.** Removing a backend (deploys, scale-in, spot reclamation) must not
drop requests in flight: the LB stops sending *new* requests, waits for existing ones up to a
timeout, then closes. The backend's side of the contract is graceful shutdown on `SIGTERM`
([Operating Systems & Hardware Symbiosis](../../CSFundamentals/01_operating_systems_deep_dive.md) §10): stop accepting, finish in-flight work,
exit. In Kubernetes these two sides race — the pod gets `SIGTERM` while load balancers may still
be sending it traffic for a few seconds — which is why services add a short `preStop` sleep
before they stop accepting connections.

**Long-lived connections break naive balancing.** HTTP/2, gRPC and WebSockets keep one
connection open for minutes or hours. An L4 balancer places *connections*, not requests, so a
new backend added during a spike receives nothing until clients reconnect, and old backends
stay hot. Fixes: balance per request at L7 (or client-side), cap connection lifetime so clients
reconnect periodically (`max_connection_age` in gRPC), and for WebSockets rebalance by closing
connections gradually.

## Where state goes when you scale out

X-axis scaling assumes any backend can serve any request. State that lives on one backend
breaks that:

| Option | How it works | Cost |
|---|---|---|
| **Stateless backends + shared store** | Sessions in Redis or a database; each request carries a token | One network hop per request for state; the store becomes the thing to scale |
| **Signed client-side state** | The session is in a signed, possibly encrypted, cookie or JWT | Size limits; revocation is hard ([Security Fundamentals](../../CSFundamentals/11_security_fundamentals_deep_dive.md) §2) |
| **Sticky sessions** | The LB pins a client to one backend by cookie or hashed IP | Uneven load; a backend loss loses its sessions; scale-in has to drain for hours |
| **Consistent hashing on a key** | Route by user or entity ID so its cache stays warm on one node | Hot keys stay hot ([Partitioning, Shard Keys, and Hot Keys](25_partitioning_and_hot_keys.md)) |

The default for web and API tiers is the first: stateless backends. Stickiness is an
optimisation for cache warmth, never a correctness requirement — if losing the sticky node
loses data, the design is wrong.

## Capacity planning, worked

Capacity planning turns a traffic forecast into a number of machines, and interviewers expect
the arithmetic out loud. A worked example for an API tier:

- **Given:** peak 20,000 requests/s; mean latency 50 ms; each instance has 8 worker slots;
  three availability zones; the fleet must survive losing one zone at peak.
- **In flight (Little's law, L = λW):** 20,000 × 0.050 s = **1,000** concurrent requests across
  the fleet.
- **One instance at 100%:** 8 slots ÷ 0.050 s = **160 requests/s**.
- **Target utilisation 60%** (below the queueing cliff, [Application Resilience Patterns](12_application_resilience_patterns.md)):
  96 requests/s per instance, so 20,000 ÷ 96 = 208.3 → **209 instances**.
- **Survive a zone loss:** the two surviving zones must carry the whole peak, so each zone needs
  ⌈209 ÷ 2⌉ = 105 instances: **315 in total**, of which a third is zone-failure headroom.
- **Downstream check:** if each request holds a database connection for 10 ms, the database sees
  20,000 × 0.010 = **200** busy connections on average. But 315 instances with a pool of 10
  connections each would open 3,150 connections, far more than a PostgreSQL primary should
  accept — so either shrink per-instance pools or put a pooler (PgBouncer) in between. Scaling
  one tier moves the bottleneck to the next; always follow it down.
- **Growth:** at 10% growth a month, peak is 1.1¹² ≈ **3.1×** higher in a year. Plan the
  database's path (read replicas, then partitioning) now, not when it saturates.

The numbers matter less than the habit: every figure produces a decision (instance count,
zone headroom, a connection pooler, a partitioning roadmap).

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Scaling axes** | Scales stateless tiers horizontally behind an LB | Names X/Y/Z scaling and which bottleneck each moves | Plans the sequence of scaling steps and their migration costs for years of growth |
| **Algorithms** | Knows round robin and least connections | Chooses least-outstanding or P2C with reasons; explains gray failure and the fast-failure black hole | Designs balancing across tiers (DNS, edge, L7, client-side) and its failure modes |
| **Health and draining** | Adds a health check endpoint | Separates liveness from readiness, adds outlier ejection, drains on deploy | Prevents correlated ejection and fail-open disasters fleet-wide |
| **State** | Keeps sessions in a shared store | Explains stickiness trade-offs and long-lived connection imbalance | Sets platform-wide statelessness and connection-lifetime policy |
| **Capacity** | Estimates instance counts roughly | Plans with Little's law, utilisation targets, N+1 zones and downstream limits | Owns capacity forecasting, cost and headroom policy across services |

## Interview checklist

- [ ] I can explain X, Y and Z scaling and when vertical scaling is still the right call.
- [ ] I can compare round robin, random, least-outstanding and power of two choices, with the measured effect on p99.
- [ ] I can explain why load-blind balancing collapses on a slow server and why least-outstanding feeds a fast-failing one.
- [ ] I can design health checks: liveness vs readiness, thresholds, outlier ejection, and why readiness must not depend on shared dependencies.
- [ ] I can explain connection draining, graceful shutdown, and the imbalance long-lived connections cause.
- [ ] I can say where session state should live when scaling out, and what sticky sessions cost.
- [ ] I can do a capacity plan out loud: Little's law, per-instance throughput, utilisation target, zone headroom, downstream connection limits.

## Related building blocks

- [Application Resilience Patterns](12_application_resilience_patterns.md)
- [Operating Systems for System Design](01_operating_systems.md)
- [Databases: Source of Truth](05_databases.md)
- [Decision Framework](17_decision_framework.md)
- [Multi-Region and Global Traffic](27_multi_region_and_global_traffic.md) — balancing and failing over between regions.
- [Overload Control and Graceful Degradation](28_overload_control_and_graceful_degradation.md) — what to shed, limit or degrade once capacity is exceeded.
