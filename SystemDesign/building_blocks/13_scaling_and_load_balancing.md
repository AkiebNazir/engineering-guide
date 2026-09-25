# Scaling and Load Balancing

## Load balancing algorithms

| Algorithm | How it picks a target | Good for | Weakness |
|---|---|---|---|
| Round robin | Cycles through instances in order. | Similar-cost, similar-duration requests on uniform instances. | Ignores actual load — a slow instance keeps getting the same share of new work as a fast one. |
| Least connections/requests | Sends to the instance with the fewest active requests. | Variable request duration (some requests take far longer than others). | Needs accurate, low-latency live connection-count state from every instance — stale state defeats the point. |
| Weighted (round robin or least-connections) | Like the base algorithm, but instances get traffic proportional to a configured weight. | Heterogeneous hardware/capacity in the same pool. | Weights are usually set once and go stale as real capacity or instance health changes. |
| Consistent hash | Routes by a hash of a key (user ID, cache key) onto a ring of nodes. | Session affinity, cache locality — same key keeps hitting the same node so its cache stays warm. | A popular key creates a genuinely hot node — hashing doesn't fix skewed key popularity, only key-to-node mapping. |
| Power of two choices | Sample two random instances, send to whichever reports less load. | Large pools where full least-connections state is too expensive to track globally. | Only as good as the load metric sampled — a cheap-but-misleading metric (e.g. raw <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>) picks the wrong instance. |

Round robin and weighted round robin are stateless and cheap — a reasonable default until you have evidence request costs are uneven enough to justify least-connections' extra bookkeeping. Reach for consistent hashing specifically when locality (cache/session affinity) matters more than perfectly even load; reach for power-of-two-choices when the pool is too large for tracking exact per-instance load cheaply, which is most large fleets.

Everything here balances across instances *inside one region*. Choosing which region serves a user, and shifting traffic between regions when one degrades, is a different problem with different levers (geo-aware <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>, anycast, capacity and failover planning) and is covered in [27_multi_region_and_global_traffic.md](27_multi_region_and_global_traffic.md).

## Horizontal vs. vertical scaling


```arch
%% caption: Vertical scaling hits a hardware ceiling; horizontal scaling requires a load balancer and stateless instances.
group vert "Vertical Scaling (Scale Up)" color=blue
node v1 "Small Server\n(2 Cores)" at 0,0 in vert icon=server
node v2 "Big Server\n(32 Cores)" at 0,2 in vert icon=cpu

v1 ==> v2 : "replace with\nbigger box"

group horiz "Horizontal Scaling (Scale Out)" color=green
node lb "Load Balancer" at 3,1 in horiz icon=globe
node h1 "Instance 1" at 5,0 in horiz icon=server
node h2 "Instance 2" at 5,1 in horiz icon=server
node h3 "Instance 3" at 5,2 in horiz icon=server

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
- **Data:** the database backing N stateless app instances is very often the actual bottleneck — adding app instances doesn't help once the DB is saturated (see `05_databases.md`/`06_database_internals.md` for partitioning).
- **Hot keys:** consistent-hash routing or a natural partition key can concentrate load onto one instance/shard regardless of total fleet size — more instances don't help a single overloaded key.

Default to horizontal scaling for the application tier (it's stateless by construction, per `12_application_resilience_patterns.md`'s pool guidance); vertical scaling is usually reserved for stateful single-writer components (a primary database) where horizontal write scaling requires a real partitioning strategy, not just "add a box."

## What to autoscale on

Average <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> alone is a bad autoscaling signal because <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> can look moderate while requests are actually piling up waiting on I/O (a DB call, a downstream dependency) rather than computing — the service can be visibly failing users (growing queues, rising latency) with <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> sitting at 40%. Autoscale on signals that actually correlate with saturation:

- **Queue depth / queue age:** how much work is waiting and how long the oldest item has waited — a direct measurement of "falling behind."
- **Concurrent in-flight requests:** rising concurrency at roughly flat throughput means requests are taking longer to finish, i.e. the system is saturating.
- **Pending work / backlog size:** for worker fleets, the actual count of unclaimed jobs.
- **<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> + latency together**, if <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> is used at all — never <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> in isolation.

## Scale-out lag and headroom

Adding instances is not instant — provisioning, image pull/boot, warm-up (JIT, cache fill, connection pool ramp-up) all take real time, often tens of seconds to minutes. An autoscaler reacting only once a pool is already saturated will always be behind the spike it's reacting to.

```text
demand ──────────────╱‾‾‾‾‾‾‾  ← spike arrives
capacity ──────────╱───────    ← new instances not ready yet
                   ▲
          gap = requests degraded/dropped during scale-out lag
```

Mitigate with **headroom** (run below the point where the queueing-theory cliff hits — see `12_application_resilience_patterns.md`'s Little's Law section), predictive/scheduled scaling for known traffic patterns, and a fast-scaling policy that reacts to leading indicators (queue growth rate) rather than lagging ones (<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> already pegged).

## Admission control before collapse

Once a service is already past its sustainable capacity, letting every request in and trying to serve all of them (badly, slowly) is worse than the alternative: **reject some requests fast and cheaply so the ones you do accept can actually be served within budget.** This is the same principle as the seat-reservation waiting room in `solutions/010_seat_reservation_solution.md` — admission control paces load down to what the system can sustain, rather than making a sale/business decision itself. Combine with bounded queues (`12_application_resilience_patterns.md`) so "full" is a real, enforced state rather than an unbounded backlog silently growing until the process falls over.

Rejecting is only the first tool. Choosing *which* requests to reject (priority classes, per-tenant fairness, dropping optional work first), limiting concurrency adaptively, and degrading features on purpose are covered in [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md).

## Queueing theory, briefly

As utilization on any pool (thread pool, connection pool, single-partition write path) approaches 100%, wait time grows nonlinearly, not linearly — a pool at 95% average utilization can already have severe tail latency even though it "looks fine" on an average-utilization dashboard. `12_application_resilience_patterns.md` works this through: Little's Law (`L = λW`) is an identity that tells you how many requests are in flight for a given arrival rate and latency, and the *cliff* comes from queueing at high utilization, where waiting time grows like `ρ / (1 − ρ)`. The short version for scaling purposes is: **plan capacity and autoscaling thresholds against headroom below that cliff, not against 100% theoretical throughput.**

## Related building blocks

- [12_application_resilience_patterns.md](12_application_resilience_patterns.md)
- [01_operating_systems.md](01_operating_systems.md)
- [05_databases.md](05_databases.md)
- [17_decision_framework.md](17_decision_framework.md)
- [27_multi_region_and_global_traffic.md](27_multi_region_and_global_traffic.md) — balancing and failing over between regions.
- [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md) — what to shed, limit or degrade once capacity is exceeded.
