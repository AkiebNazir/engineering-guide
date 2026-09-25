# Multi-Region and Global Traffic

"Now make it multi-region" is the follow-up that separates a design that survives a zone failure from one that survives a region failure, and it is not one feature. It is four decisions: where each piece of state lives, how users reach a region, how data gets between regions, and what you do when a region is lost. Each has a cost in latency, money or complexity, and the physics of distance sets a floor you cannot engineer away.

> 🎯 Say the topology and its numbers: "Regional ownership: each user has a home region that owns their writes. Data replicates asynchronously with a 1 to 5 s lag, so RPO is seconds. <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> steering with a 60 s TTL moves stateless traffic in about 90 s. A human approves promoting stateful primaries. Three regions at 60% utilisation absorb the loss of one at 90%."

## Why go multi-region, and what it costs

| Driver | What it buys | What it costs | Do you need it? |
|---|---|---|---|
| Latency | Users reach a nearby region. | Data must be near them too, or you trade one cross-region call for another. | Only if the p99 budget cannot absorb 80 to 200 ms (below). |
| Availability | Survive the loss of a whole region. | 1.2x to 3x infrastructure, a data-replication design, drills. | If a region outage exceeds your downtime budget ([18](18_back_of_envelope_estimation.md)). |
| Residency | Personal data stays in a jurisdiction. | Partitioning by user residency, region-local backups and analytics. | If law or contract says so. |
| Blast radius | A regional problem is not a global one. | Only real if config, deploys and control planes are not global (last sections). | Yes, but it is a cells question first. |

Multi-AZ is the default and covers most hardware faults ([15](15_observability_and_reliability.md)). Multi-region is a product decision priced in engineer-years: it does not protect against a bad deploy that ships to every region.

## What distance costs

Light in fibre travels about 200,000 km/s, so one-way delay is about 5 µs per km. Great-circle distances are exact; real cable routes are longer, so we assume 1.5x for planning (assumption, measure yours).

| Pair | Great-circle | Floor RTT (2 x km x 5 µs) | Planning RTT (x1.5) |
|---|---|---|---|
| Same datacenter ([18](18_back_of_envelope_estimation.md)) | n/a | n/a | 0.5 ms |
| Dublin to Frankfurt | 1,090 km | 11 ms | 16 ms |
| Virginia to Oregon | 3,620 km | 36 ms | 54 ms |
| Virginia to Dublin | 5,460 km | 55 ms | 82 ms |
| Virginia to Tokyo | 10,870 km | 109 ms | 163 ms |
| Virginia to Singapore | 15,520 km | 155 ms | 233 ms |

Consequences: (1) a synchronous cross-region write costs at least the round trip to the nearest quorum member, so a majority quorum of Virginia, Dublin and Frankfurt led from Dublin pays about 16 ms, and one of Virginia, Oregon and Dublin led from Virginia pays about 54 ms; (2) a request that chains three cross-region calls at 82 ms spends 246 ms, so allow at most one per request; (3) the best fix for latency is to avoid crossing, not to speed the crossing.

## Topology patterns

The AWS DR whitepaper (2021) names backup and restore, pilot light, warm standby and multi-site active/active; the rest of this table adds the data-ownership patterns that decide correctness.

| Pattern | Who accepts writes | RPO / RTO | Consistency | Relative cost | Choose when |
|---|---|---|---|---|---|
| Single region + DR backup | One region | Hours / hours to days | Strong | 1.1x | Internal tools, low revenue per minute. |
| Active-passive (pilot light, warm standby) | Primary region; standby scales up on failover | Seconds to minutes / minutes | Strong in primary; standby lags | 1.1x to 1.3x | Most B2B and checkout-like systems. |
| Active-active, regional ownership (home region, geo-partitioning) | The record's home region | Async lag / minutes (per partition) | Strong per record | 1.5x | Users mostly touch their own data: chat, mail, profiles. CockroachDB `REGIONAL BY ROW` gives each row a home region. |
| Active-active, multi-writer | Any region | Lag / seconds | Eventual with conflict rule | 1.5x | Shared state that merges (counters, sets, presence). DynamoDB global tables (eventual mode) resolve conflicts by last writer wins. |
| Globally consistent store | Quorum across regions | 0 / seconds | Strict serializable | 1.5x plus latency | Ledgers, inventory. Spanner base multi-region configurations need a write quorum across two regions ([24](24_google_papers.md)). |
| Read-local, write-global | One primary region | Lag / minutes | Stale reads in replicas | 1.3x | Read-heavy. Facebook's 2013 memcache paper: one master region takes writes, others serve reads. |

Regional ownership is the pattern that lets interviewers stop asking: every record has exactly one writer, so no conflicts, and only the ownership map is global. Multi-writer with last-writer-wins silently discards a concurrent write ([10](10_distributed_systems_theory.md)); use it only where losing one is acceptable.

**Decision rule:** pick the weakest pattern that meets the stated RPO and latency, then name the writer of every record.

## Traffic steering

```arch
%% caption: Steering is layered: pick a region by name, address or client logic, then a healthy region-local path, so each layer has its own failover time.
node C "Client" at 1,0 icon=client
node H "Health checks" at 2,0 icon=monitor sub="from outside"
node S "Steering" at 1,1 shape=diamond color=amber
group ra "Region A" color=blue icon=region
node R1 "Region A entry" at 0,2 in ra icon=edge
node L "Regional L7 LB" at 0,3 in ra icon=lb
node CR "Cell router" at 0,4 in ra icon=gateway
node CELL "Cell" at 0,5 in ra icon=server
node R2 "Region B entry" at 1,2 icon=edge
node R3 "Region C entry" at 2,2 icon=edge
C -> S
S:L -> R1:T : "latency DNS, TTL 60 s"
S:B -> R2:T : "anycast IP via BGP"
S:R -> R3:T : "client SDK endpoint list"
R1 -> L -> CR -> CELL
H ..> S
```

| Mechanism | How it works | Failover | Limits |
|---|---|---|---|
| GeoDNS or latency <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> | Resolver gets the address of the closest healthy region (Route 53 latency routing uses measured latency between the user's network and each region). | Detection plus TTL: AWS recommends TTL of 60 s or less and documents a 110 s example (60 s TTL, 10 s checks, threshold 5). | Clients and resolvers may cache beyond TTL, so plan a tail; the resolver's location, not the user's, is what <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> sees. |
| Anycast | Many edge sites announce one <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>; BGP delivers to a nearby site, which forwards to a region. | AWS Global Accelerator redirects new connections when health checks fail, described as tens of seconds. | BGP path is usually, not always, the nearest; existing connections to a dead region still break. |
| Global L7 <abbr title="Load Balancer - A device or software service that distributes network or application traffic across a number of servers to improve capacity and reliability.">LB</abbr> | One anycast VIP terminates connections at the edge and proxies to the closest healthy backend with capacity (Google Cloud's global external Application Load Balancer; Maglev, NSDI 2016, describes the software <abbr title="Load Balancer - A device or software service that distributes network or application traffic across a number of servers to improve capacity and reliability.">LB</abbr> fleet). | Health-check interval and retries. | The <abbr title="Load Balancer - A device or software service that distributes network or application traffic across a number of servers to improve capacity and reliability.">LB</abbr> is a shared dependency; keep it static-stable (last section). |
| Client-side | <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> holds several endpoints and retries the next on failure. | One timeout. | Needs a client rollout to change; hard to control fleet-wide. |

Failover time is `interval x threshold + TTL + client tail`. Use hysteresis (do not flap on one failed probe), probe the real dependency chain from outside the region, and never let automation fail over stateful tiers without a fence.

## Data replication: RPO, RTO, consistency

| Mode | Commit waits for | RPO | Write latency | Documented example |
|---|---|---|---|---|
| Synchronous quorum across regions | Majority of voting replicas | 0 | At least RTT to nearest quorum member | Spanner multi-region; DynamoDB multi-Region strong consistency (synchronous to at least one other region, RPO zero, concurrent conflicting writes fail and retry). |
| Asynchronous, single primary | Local commit only | Replication lag | Local | Aurora Global Database: typical lag under a second, promotion on failover takes minutes. |
| Asynchronous, multi-writer | Local commit only | Lag, and conflicts | Local | DynamoDB global tables (eventual mode): typically about a second, last writer wins. |

RPO is `lag x write rate`: at 5,000 writes/s a 1 s lag puts 5,000 writes at risk, and a 5 s p99 lag puts 25,000. You need a way to find and reconcile them after failover (replay from the source log, or compare against the other system of record), and an alert on lag itself.

## Read-your-writes across regions

- **Sticky home region:** route a user to the region that owns their data by cookie or token claim. Cost: a travelling user pays the distance; on failover their home moves.
- **Read the primary after a write:** Facebook's memcache paper (NSDI 2013) sets a remote marker when a non-master region writes, and reads for that key go to the master region until replication catches up, "explicitly trading additional latency ... for decreased probability of reading stale data".
- **Causal token:** the write returns its commit timestamp, the client sends it with reads, and a replica waits until it has applied that point (Zanzibar's zookies, [24](24_google_papers.md)).

## State that stays global versus regional

| State | Placement | Why |
|---|---|---|
| Token verification | Regional, with replicated signing keys | Must work with the global identity service degraded. |
| Login, revocation | Home region or globally replicated | Revocation must propagate; bound the staleness. |
| Config and flags | Replicated, staged, last-known-good cached | See the control-plane section. |
| IDs | Region bits in the ID, no coordination ([10](10_distributed_systems_theory.md)) | A global counter is a global dependency. |
| Uniqueness (usernames) | One authoritative region or a strongly consistent store | Only place a race can be resolved. |
| Money | Home region or strong store | Never last-writer-wins ([11](11_transactions_and_concurrency.md)). |
| Caches, rate limits | Regional | Approximate, rebuildable. |

## Data residency and GDPR

GDPR Chapter V (Articles 44 to 50) restricts transfers of personal data outside the EEA unless a legal mechanism applies (an adequacy decision or standard contractual clauses); it does not itself require EU-only storage, though some countries' laws do require local storage. Have counsel decide, then engineer for the strictest reading: partition by the user's residency so the home region is the legal region; keep replicas, backups, search indexes, analytics and logs inside it; pair regions inside one jurisdiction (Dublin and Frankfurt are 11 ms apart at the floor); and make erasure reach replicas, backups and mirrored streams ([26](26_distributed_log_internals.md)). CockroachDB and Spanner both document residency-oriented placement.

## Capacity: N+1 regions and evacuation

With `N` regions and one lost, each survivor carries `1/(N-1)` of peak, so total provisioned capacity is `N/(N-1)` of peak. At steady utilisation `u`, survivors run at `u x N/(N-1)`.

| Regions | Total capacity | Survivor load at 60% steady |
|---|---|---|
| 2 | 200% | 120% (overload) |
| 3 | 150% | 90% |
| 4 | 133% | 80% |

**Evacuation runbook:** (1) declare, and freeze deploys; (2) shed non-critical work first ([28](28_overload_control_and_graceful_degradation.md)); (3) shift traffic in steps (10%, 50%, 100%) watching survivor saturation, because moved users arrive with cold caches: at a 95% hit rate misses are 1/(1 - 0.95) = 20x steady state; (4) fence the old primary with a fencing token, promote the replica ([19](19_consensus_and_coordination.md)); (5) verify SLIs; (6) plan failback. Netflix's tech blog documents regular Chaos Kong exercises that evacuate a whole region under live traffic.

## Cells, shuffle sharding, blast radius

A **cell** is a complete, independent copy of the stack serving a subset of customers; a thin, static **cell router** maps customer to cell. The AWS whitepaper "Reducing the Scope of Impact with Cell-Based Architecture" (2023) lists deployment failures, poison pills, misbehaving clients and operator mistakes as what cells contain. With 20 cells a bad deploy reaching one cell hurts 5% of customers; roll out to one cell, then 2, then 4. Slack (2023) made each cell an availability zone and set a design goal of draining an AZ in 5 minutes without depending on resources inside the failing cell.

**Shuffle sharding** (AWS Builders' Library): give each customer a random subset of workers. With 8 workers and 2 per customer there are C(8,2) = 28 combinations, so one bad customer overlaps a given other customer with probability 1/28 instead of 1/4 for plain 4-way sharding. Route 53 assigns each domain 4 of 2,048 virtual name servers, C(2048,4), about 730 billion combinations.

```arch
%% caption: A global config push reaches every cell at once unless it is staged, which is why cells alone do not bound blast radius.
node R "Cell router" at 1,0 icon=gateway
group cells "Cells" color=blue icon=grid
node C1 "Cell 1: 5%" at 0,1 in cells icon=server
node C2 "Cell 2: 5%" at 1,1 in cells icon=server
node CN "Cells 3 to 20" at 2,1 in cells icon=server
node CP "Global control plane" at 1,2 icon=sitemap sub="config, flags, quotas"
R:B -> C1:T
R -> C2
R:B -> CN:T
CP:L ..> C1:B : "staged push, one cell first"
CP ..> C2 : "then"
CP:R ..> CN:B : "then"
```

## Global control planes are hidden single points of failure

- **Global replication of a bad input.** Google's 12 June 2025 incident report: a policy change with blank fields "was replicated globally within seconds", crash-looped Service Control in every region for about 3 hours, and the code "was not feature flag protected". Remediations named: audit consumers of globally replicated data and propagate it incrementally with time to detect issues.
- **A dependency under recovery tooling.** AWS's post-event summary for the 19 to 20 October 2025 us-east-1 DynamoDB <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> failure lists EC2 instance launches and console sign-in among the affected operations. Lesson from AWS's multi-region guidance: initiate failover from the healthy region and rely on data-plane operations, not on making changes in the impaired one (static stability, Builders' Library).

**Rules:** stage every global push with soak time; cache last-known-good config; keep runbooks, dashboards and paging outside the region they diagnose; inventory every global dependency (<abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>, identity, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>, secrets, flags, <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr>).

## Testing: game days and failback

Drill failover at production traffic on a schedule (Google's DiRT, Netflix's Chaos Kong) and record achieved RTO and RPO against targets. **Failback is a separate, risky operation:** the old primary may hold writes that never replicated (the RPO set) that you must review, merge or discard on purpose; caches are cold again; capacity shifts back. Move in small steps (Slack's design lets an operator undrain to as little as 1%).

## Worked example: a failover timeline

Assumptions (ours): 3 regions at 60% steady utilisation; Route 53 fast checks every 10 s with threshold 3; <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> TTL 60 s; async DB replication with 1 s median and 5 s p99 lag; 5,000 writes/s in the failed region; 95% cache hit rate; a human approves database promotion.

| Time | Event | Derived number |
|---|---|---|
| t = 0 | Region A fails | 5,000 writes/s at risk |
| t = 30 s | 3 failed 10 s probes mark A unhealthy | 3 x 10 s = 30 s |
| t = 30 to 90 s | Cached answers expire | 30 s + TTL 60 s = 90 s |
| t = 2 to 5 min | Stragglers that cache beyond TTL (assumed) | The tail sets the "fully drained" time. |
| t = 90 s on | B and C take A's load | 60% x 3/2 = 90%; cold caches send 20x steady misses to the database for moved users |
| t = 5 to 10 min | On-call approves and promotes (assumed 5 min to decide plus promotion) | Writes resume; RPO 5,000 to 25,000 writes |

So stateless reads recover in about 90 s plus a tail, writes recover in minutes because of the human gate, and the RPO is the lag at the moment of failure: hence the lag alert, the cache-warming plan and the reconcile job.

```arch
%% caption: DNS moves reads in about 90 s but writes wait on database promotion, which is gated on a human and a fence.
node cl "Client" at 0,0 icon=client color=slate
node d "DNS" at 1,0 icon=network color=teal
node a "Region A" at 2,0 icon=region color=blue

node op "On-call" at 0,1 icon=user color=orange
node b "Region B" at 1,1 icon=region color=blue
node hc "Health checks" at 2,1 icon=monitor color=pink

node fail "t=0 region fails" at 3,0 shape=card color=red
a -> fail -> a

hc -> a : "probe fails 3x"
hc -> d : "t=30s mark A unhealthy"

cl -> d : "lookup after cache expires"
d -> cl : "address of B"

cl -> b : "reads served from cold cache"

op -> b : "approve promote"
b -> cl : "writes accepted again (5-10 min)"
```

## Cost model

Compute is `peak x N/(N-1)`: 1.5x for three regions, against 1x for one, plus `s` x peak for a warm standby at scale `s`, which is 1.25x at 25%. Storage is one copy per region. Transfer is billed per GB: 50 MB/s of replication is 50 MB x 86,400 = 4.3 TB/day, about $2,600/month at an assumed $0.02/GB (check the provider's price list). So three-region active-active costs roughly 1.5x compute, 3x storage plus transfer, against 1.25x compute and 2x storage for warm standby: buy the extra region only if the downtime it removes is worth it.

## Per-problem cheat sheet

| Problem | Topology | Data | Watch out |
|---|---|---|---|
| Chat ([006](../solutions/006_chat_solution.md)) | Regional ownership: home region per conversation | Sequence authority in the home region, replicated log | Cross-region chats miss a same-region latency budget: state a looser target. |
| Feed ([007](../solutions/007_news_feed_solution.md)) | Read-local, write from the author's home | Posts and graph replicate, feeds stay regional and rebuild | Replication lag adds to the freshness budget. |
| Payments ([017](../solutions/017_payment_ledger_solution.md)) | Single home or strongly consistent store | Synchronous quorum, RPO 0 | Latency of the quorum; idempotency across failover. |
| KV store ([023](../solutions/023_distributed_key_value_store_solution.md)) | Per-key choice: quorum across regions or async | Tunable consistency per table | Conflict rule if multi-writer. |
| Video ([016](../solutions/016_video_on_demand_solution.md)) | Regional origins, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> pull-through | Object storage replicated to two regions | Cold-region origin cost and latency. |

## Interview angles

- **"Make it multi-region."** Strong answer: name the driver, pick a pattern from the table, name each record's writer, give RPO and RTO as numbers.
- **"How fast is failover?"** `interval x threshold + TTL + tail` for reads; a human-gated promotion for writes.
- **"Why not active-active everywhere?"** Cost, conflicts, and a shared control plane that defeats isolation.
- **"What can still take you down?"** Global config or deploy pushes, identity, <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>, the tooling you would use to recover.
- **"How do you fail back?"** Reconcile the un-replicated set, warm caches, shift in steps.

## Related building blocks

- [10_distributed_systems_theory.md](10_distributed_systems_theory.md): consistency models, conflict resolution.
- [15_observability_and_reliability.md](15_observability_and_reliability.md): failure domains, DR patterns.
- [19_consensus_and_coordination.md](19_consensus_and_coordination.md): quorums, fencing.
- [24_google_papers.md](24_google_papers.md): Spanner, Zanzibar zookies.
- [25_partitioning_and_hot_keys.md](25_partitioning_and_hot_keys.md): geo-partitioning by key.
- [26_distributed_log_internals.md](26_distributed_log_internals.md): mirroring streams across regions.
- [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md): shedding during evacuation.
