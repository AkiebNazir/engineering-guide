# The Papers Behind Google-Scale Systems

You do not need to recite these papers in an interview. You do need the design *reasoning* in them: why GFS has a single master, why Bigtable is built on an LSM tree, why Spanner needs atomic clocks. Each summary below is the part worth carrying into a design discussion — the problem, the key decisions, the trade-offs, and where the idea shows up in today's systems.

> 💡 Read for the "why". When an interviewer asks you to justify a design choice, "this is the same trade-off GFS made: a single metadata master is simpler and fast enough because data never flows through it" is a strong answer.

## GFS — the Google File System (2003)

**Problem.** Store enormous files (multi-GB crawl data, logs) on thousands of cheap machines that fail constantly, for workloads that mostly append and read sequentially.

**Key decisions.**

- Files are split into large **64 MB chunks**, each replicated (3× by default) on chunkservers.
- A **single master** holds all metadata (namespace, file → chunk mapping, chunk locations) in memory. Clients ask the master where chunks are, then talk to chunkservers directly, so data never flows through the master.
- The master grants a **lease** to one replica (the primary) per chunk to order mutations; data is pushed along a chain of replicas to use network topology efficiently.
- Relaxed consistency: **atomic record append** with at-least-once semantics — applications tolerate duplicates and padding and use checksums and record IDs.
- Operation log plus checkpoints for master recovery; shadow masters for read-only availability.

```arch
%% caption: The GFS Master holds metadata and directs clients, but actual file chunks flow directly between clients and Chunkservers.
node c "Client" at 0,0 icon=client color=blue
node m "Master" at 2,0 icon=cpu color=amber sub="metadata in RAM"
group cs "Chunkservers (Replicas)" color=slate style=dashed
node r1 "Primary Chunkserver" at 1,1 in cs icon=server color=green sub="holds the lease"
node r2 "Secondary Chunkserver" at 0,2 in cs icon=server color=green
node r3 "Secondary Chunkserver" at 2,2 in cs icon=server color=green

c -> m : "1. Where is file/chunk?"
m ..> c : "2. Primary is R1"
c ==> r1 : "3. Push data to Primary"
r1 ==> r2 : "4. Chain replicate"
r1 ==> r3 : "4. Chain replicate"
```

**Trade-offs.** One master is simple and makes globally good placement decisions, but it limits the number of files (metadata must fit in RAM) and is a failover bottleneck. Its successor, Colossus, distributes the metadata into Bigtable. (Google Cloud's 2021 blog post "A peek behind Colossus" describes a metadata service made of many horizontally scalable curators that keep file metadata in Bigtable, with clients reading and writing data directly to the network-attached "D" disk servers and background custodians doing repair and rebalancing; it reports the Bigtable-backed metadata scaling over 100× beyond the largest GFS clusters.)

**Today.** HDFS copied the design; object stores and Colossus evolved it.

## MapReduce (2004)

**Problem.** Let ordinary engineers run computations over terabytes on thousands of machines without writing distributed systems code.

**Key decisions.** A `map` and `reduce` programming model; the framework handles partitioning, shuffling, sorting, retries; re-executes failed tasks (workers are stateless, outputs go to GFS); schedules tasks near the data; launches **backup tasks** for stragglers, because the slowest few percent of tasks dominate job time.

```arch
%% caption: The master schedules map tasks next to their GFS input, the shuffle groups map output by key for the reducers, and a backup copy of a straggler races the original.
grid 160x150
node in "Input in GFS" at 0,0 icon=storage sub="large splits, read locally"
grid 160x150
node mst "Master" at 2,0 icon=scheduler color=amber sub="assigns, re-executes"
group mp "Map phase (stateless workers)" color=orange
grid 160x150
node m1 "Map task" at 0,1 in mp icon=worker
grid 160x150
node m2 "Map task" at 1,1 in mp icon=worker
grid 160x150
node bk "Backup task" at 2,1 in mp icon=worker sub="copy of a straggler"
grid 160x150
node sh "Shuffle + sort by key" at 1,2 shape=pill color=purple
group rp "Reduce phase" color=blue
grid 160x150
node r1 "Reduce task" at 0,3 in rp icon=worker
grid 160x150
node r2 "Reduce task" at 2,3 in rp icon=worker
grid 160x150
node out "Output in GFS" at 1,4 icon=storage

in -> m1
in -> m2
mst ..> bk : "launch backup"
m1 -> sh
m2 -> sh
bk -> sh : "first to finish wins"
sh -> r1
sh -> r2
r1 -> out
r2 -> out
```

**Trade-offs.** Simple and robust, but disk-heavy between stages and awkward for iterative or interactive work — which is what Spark and Dataflow addressed. See [Batch and Stream Processing](21_batch_and_stream_processing.md).

## Bigtable (2006)

**Problem.** Store petabytes of structured data (web index, Maps, Analytics) with low-latency random reads/writes and efficient scans.

**Key decisions.**

- Data model: a sparse, sorted, multi-dimensional map `(row key, column family:qualifier, timestamp) → value`.
- Rows are sorted lexicographically and split into **tablets** (row ranges), the unit of distribution and load balancing. Row-key design therefore controls locality (e.g. reversed domain names keep a site's pages together).
- Storage is an **LSM tree**: a commit log, an in-memory memtable, immutable SSTables in GFS, with minor and major compactions and per-SSTable **Bloom filters**.
- **Chubby** holds the master lock and bootstrap location; tablet servers can die and their tablets are reassigned.
- Transactions only within a single row.

```arch
%% caption: A tablet server logs each write to GFS, applies it to the memtable, and flushes the memtable to immutable SSTables; Chubby holds the master lock and the bootstrap location.
grid 160x150
node cl "Client" at 0,0 icon=client
grid 160x150
node ch "Chubby" at 2,0 icon=lock sub="master lock, root location"
grid 160x150
node ts "Tablet server" at 0,1 icon=server sub="serves tablets (row ranges)"
grid 160x150
node mst "Master" at 2,1 icon=scheduler color=amber sub="assigns tablets"
grid 160x150
node mt "Memtable" at 1,2 icon=memory sub="sorted, in RAM"
group gfs "GFS" color=green icon=storage
grid 160x150
node log "Commit log" at 0,3 in gfs icon=logs
grid 160x150
node sst "SSTables" at 1,3 in gfs icon=layers sub="immutable, Bloom filter each"

cl ..> ch : "find root tablet"
cl -> ts : "read / write a row"
mst -> ch : "hold lock"
mst ..> ts : "assign"
ts -> log : "1. append"
ts -> mt : "2. insert"
mt -> sst : "flush (minor compaction)"
```

**Trade-offs.** Very high write throughput and scalable scans, at the cost of no cross-row transactions and careful row-key design to avoid hotspots (sequential keys write to one tablet). Cloud Bigtable, HBase, and Cassandra's storage engine follow this model. See [Specialized Data Structures and Indexes](20_specialized_data_structures.md) and [Partitioning, Shard Keys, and Hot Keys](25_partitioning_and_hot_keys.md).

## Chubby (2006)

**Problem.** Give many systems (GFS, Bigtable) a reliable way to elect a leader and store small bits of configuration.

**Key decisions.** A lock service rather than a consensus library, because a service is easier for teams to adopt correctly; a small Paxos-replicated cell of five replicas; **coarse-grained** locks held for hours; files and directories for small data; client sessions with **KeepAlive** and **lease** timeouts; **sequencers** (fencing tokens) so servers can reject stale lock holders; aggressive client-side caching with invalidations.

```arch
%% caption: A Chubby cell is five Paxos replicas with one elected master; clients hold sessions with KeepAlives and cached data, and pass a sequencer to the servers they call.
grid 160x130
node app "Client app" at 1,0 icon=service sub="KeepAlives, cache invalidations"
node srv "Protected server" at 2.5,0 icon=server sub="checks the sequencer"
group cell "Chubby cell (5 replicas)" color=blue style=dashed
node mst "Master" at 1,1 in cell icon=server color=amber sub="elected by Paxos"
node r1 "Replica" at 0,1 in cell icon=replica
node r2 "Replica" at 2,1 in cell icon=replica
node r3 "Replica" at 0,2 in cell icon=replica
node r4 "Replica" at 2,2 in cell icon=replica

app <-> mst
app -> srv : "request + sequencer"
mst <..> r1 : "Paxos"
mst <..> r2
mst <..> r3
mst <..> r4
```

**Trade-offs.** Not built for high throughput or fine-grained locks; outages of a cell affect everything that depends on it, so clients must handle "jeopardy" (lost session) gracefully. ZooKeeper and etcd fill the same role outside Google. See [Consensus and Coordination](19_consensus_and_coordination.md).

## Spanner (2012)

**Problem.** A globally distributed database with SQL, strong consistency, and cross-region transactions — for applications (like Ads) that cannot tolerate eventual consistency.

**Key decisions.**

- Data is sharded into **splits**, each replicated across zones/regions by a **Paxos group** with a leader.
- Cross-shard transactions use **two-phase commit** where every participant is a Paxos group, so participants are themselves fault tolerant.
- **TrueTime**: an API returning an uncertainty interval `[earliest, latest]` backed by GPS and atomic clocks (typically a few milliseconds wide). A read-write transaction picks a commit timestamp and **waits out the uncertainty** before acknowledging, which guarantees that timestamp order equals real-time commit order — **external consistency**.
- Consequently, **lock-free snapshot reads** at any timestamp, from any sufficiently up-to-date replica.

```arch
%% caption: Each split is a Paxos group; a cross-split transaction runs two-phase commit between group leaders, and the coordinator waits out TrueTime's uncertainty before it acknowledges.
grid 160x150
node tt "TrueTime" at 0,0 icon=time color=amber sub="commit waits out [earliest, latest]"
grid 160x150
node cl "Client" at 1,0 icon=client sub="read-write txn"
group ga "Split A: Paxos group" color=blue
grid 160x150
node la "Leader A" at 1,1 in ga icon=db sub="2PC coordinator"
grid 160x150
node a1 "Replica" at 0,2 in ga icon=replica sub="zone 2"
grid 160x150
node a2 "Replica" at 1,2 in ga icon=replica sub="zone 3"
group gb "Split B: Paxos group" color=purple
grid 160x150
node lb "Leader B" at 2,1 in gb icon=db sub="2PC participant"
grid 160x150
node b1 "Replica" at 2,2 in gb icon=replica sub="zone 2"
grid 160x150
node b2 "Replica" at 3,2 in gb icon=replica sub="zone 3"

cl -> la
tt:B -- la:L
la <-> lb : "2PC"
la ..> a1 : "Paxos"
la ..> a2
lb ..> b1 : "Paxos"
lb ..> b2
```

**Trade-offs.** Write latency includes the commit wait and cross-region Paxos round trips; the approach needs specialised time infrastructure (CockroachDB approximates it with hybrid logical clocks and a max-offset assumption). Cloud Spanner productised it.

## Dremel (2010)

**Problem.** Interactive SQL over trillions of rows of nested data in seconds.

**Key decisions.** **Columnar storage for nested records** (repetition and definition levels encode structure per column), so a query reads only the columns it touches and compresses them well; a **multi-level serving tree** that fans a query out to thousands of leaf servers and aggregates partial results upward; tolerating a small fraction of slow leaves by returning results once most data is scanned.

```arch
%% caption: The root fans a query out through intermediate servers to thousands of leaves, each scanning only the columns it needs; partial aggregates merge on the way back up, and a slow leaf can be skipped once most data is in.
grid 150x110
node cl "Client (SQL)" at 1.5,0 icon=client
grid 150x110
node root "Root server" at 1.5,1 icon=server color=amber
grid 150x110
node i1 "Intermediate" at 0.5,2 icon=server
grid 150x110
node i2 "Intermediate" at 2.5,2 icon=server
grid 150x110
node l1 "Leaf" at 0,3 icon=worker
grid 150x110
node l2 "Leaf" at 1,3 icon=worker
grid 150x110
node l3 "Leaf" at 2,3 icon=worker
grid 150x110
node l4 "Slow leaf" at 3,3 icon=worker color=red
group st "Columnar storage (rep/def levels)" color=green
grid 150x110
node c1 "Stripe" at 0,4 in st icon=layers
grid 150x110
node c2 "Stripe" at 1,4 in st icon=layers
grid 150x110
node c3 "Stripe" at 2,4 in st icon=layers
grid 150x110
node c4 "Stripe" at 3,4 in st icon=layers

cl -> root : "query"
root -> i1 : "fan out"
root -> i2
i1 -> l1
i1 -> l2
i2 -> l3
i2 ..> l4
l1 -> c1
l2 -> c2
l3 -> c3
l4 ..> c4
```

**Trade-offs.** Excellent for scans and aggregates, unsuited to point updates. It is the engine behind **BigQuery**; Parquet adopted its column encoding.

## Borg (2015)

**Problem.** Run hundreds of thousands of jobs — long-running services and batch — across many clusters with high utilisation and reliability.

**Key decisions.** A declarative job spec; a Paxos-replicated **Borgmaster** and a scheduler that scores machines for feasibility and packing; mixing high-priority production and low-priority batch work on the same machines with **preemption**; resource reclamation (give batch the unused part of services' reservations); per-task isolation with containers; naming and health integrated with service discovery.

```arch
%% caption: A declarative job goes to the Paxos-replicated Borgmaster; the scheduler scores machines, and Borglets run production and batch tasks side by side, preempting batch when production needs the room.
grid 160x150
node job "Job spec" at 0,0 icon=file sub="declarative config, submitted"
group bm "Borgmaster (Paxos-replicated)" color=blue
grid 160x150
node bmr "Borgmaster" at 0,1 in bm icon=server
grid 160x150
node sch "Scheduler" at 2,1 in bm icon=scheduler sub="feasibility + scoring"
group mc "One machine" color=orange
grid 160x150
node bl "Borglet" at 1,2 in mc icon=server sub="machine agent"
grid 160x150
node prod "Prod service" at 0,3 in mc icon=container color=green sub="high priority"
grid 160x150
node bat "Batch task" at 2,3 in mc icon=container sub="uses reclaimed resources"

job -> bmr
bmr -> sch : "pending tasks"
bmr -> bl : "start / stop tasks"
bl:L -> prod:T
bl:R -> bat:T
prod:R ..> bat:L : "preempts" color=red
```

**Trade-offs.** High utilisation (big cost savings) at the price of complex scheduling and noisy-neighbour management. **Kubernetes** is its open-source descendant (pods ≈ alloc, labels, controllers). See [Platform and Infrastructure](16_platform_and_infra.md).

## Zanzibar (2019)

**Problem.** One authorization system for Drive, YouTube, Photos, Calendar and more: "can user U do action A on object O?" answered in milliseconds, consistently, for trillions of permissions.

**Key decisions.**

- Permissions stored as **relation tuples**: `document:readme#viewer@user:alice`, including indirection (`group:eng#member`), so sharing with a group or folder is one tuple.
- **Namespace configs** define how relations compose (editors are also viewers, a folder's viewers can view its files).
- **Zookies**: consistency tokens tied to Spanner timestamps. A content change records a zookie; later permission checks are evaluated at least as fresh as that snapshot, which avoids the "new enemy" problem (removing someone's access and then adding sensitive content they can still see).
- Heavy caching and a **Leopard** index to flatten deeply nested group memberships.

**Today.** Open-source systems (SpiceDB, OpenFGA) implement the model. See [Security](14_security.md).

## Dynamo (Amazon, 2007)

**Problem.** A shopping-cart store that must *always* accept writes, even during failures and partitions.

**Key decisions.** **Consistent hashing** with virtual nodes for partitioning; replication to the next `N` nodes on the ring; tunable **quorums** (`R`, `W`, `N`) with **sloppy quorums** and **hinted handoff** during failures; **vector clocks** to detect conflicting versions, with application-level reconciliation (merge the carts); **Merkle trees** for anti-entropy; **gossip** for membership.

```arch
%% caption: A key hashes onto the ring; its coordinator writes to the next N=3 nodes, and when one is down a sloppy quorum hands the write to the next healthy node with a hint.
route straight
grid 130x110
node cl "Client" at 3,0 icon=client
node a "A" at 1,0 shape=circle color=blue
node b "B" at 2,1 shape=circle color=green
node c "C" at 2,2 shape=circle color=green
node d "D" at 1,3 shape=circle color=red
node e "E" at 0,2 shape=circle color=amber
node f "F" at 0,1 shape=circle color=blue
node note "vector clocks per version; Merkle trees + gossip in the background" at 3,2.5 shape=text

a -- b
b -- c
c -- d
d -- e
e -- f
f -- a
cl -> b : "put(K)"
b -> c : "replica 2"
b -> d : "replica 3 (down)" color=red
b ..> e : "hinted handoff"
e ..> d : "hand back"
```

**Trade-offs.** Availability first; clients must handle conflicts and eventually consistent reads. Cassandra, Riak and DynamoDB's heritage. See [Consensus and Coordination](19_consensus_and_coordination.md).

## The Dataflow model (2015)

**Problem.** Unify batch and streaming, and give precise control over correctness, latency, and cost for unbounded, out-of-order data.

**Key ideas.** Separate four questions: **what** is computed (transforms), **where** in event time (windows: fixed, sliding, sessions), **when** in processing time results are emitted (watermarks and triggers), and **how** refinements relate (discarding, accumulating, or accumulating with retractions). Batch is simply streaming over bounded data.

**Today.** Google Cloud Dataflow and **Apache Beam**; the concepts are standard in Flink. See [Batch and Stream Processing](21_batch_and_stream_processing.md).

## The Tail at Scale (2013)

*Jeffrey Dean and Luiz André Barroso, Communications of the ACM, 2013.*

**Problem.** When one user request fans out to many servers and must wait for all of them, a rare slow response from any one server becomes a common slow response for the user. The paper's own example: if each server's 99th-percentile latency is one second and a request needs 100 of them in parallel, the chance that at least one is slow is `1 − 0.99^100 ≈ 63%`, so about 63% of user requests take over a second. Even at one slow response in 10,000 per server (`p = 0.0001`), a request that touches 2,000 servers is slow with probability `1 − 0.9999^2000 ≈ 18%`. The general form is `P(slow) = 1 − (1 − p)^N`: the tail of the *fan-out* is far worse than the tail of any one server.

**Key decisions.** The authors argue you cannot remove all sources of variability (shared resources, background daemons, queueing, garbage collection, maintenance work), so you build **tail-tolerant** systems from unpredictable parts, the way you build fault-tolerant systems from unreliable ones. Their techniques:

- **Hedged requests.** Send the request to one replica; if it has not answered within a short delay (the paper suggests about the 95th-percentile latency of that request class), send the same request to a second replica, use whichever answer arrives first, and cancel the other. In the paper's Bigtable benchmark (reading 1,000 keys spread over 100 servers), hedging after a 10 ms delay cut the 99.9th-percentile latency of the whole read from 1,800 ms to 74 ms while sending only about 2% more requests.
- **Tied requests.** Enqueue the request on two servers at once, each told about the other; when one starts executing it tells the other to cancel. This removes the waiting period that plain hedging needs, at the cost of a cancellation message that can cross in flight so both occasionally run.
- **Micro-partitions.** Create many more partitions than machines so load moves in small pieces and a failed machine's partitions are recovered by many machines in parallel. With 20 partitions per machine, for example, the balancer can shift load in steps of `1/20 = 5%` of a machine.
- **Selective replication.** Add extra replicas of items that are, or are predicted to become, hot, and spread their load across the replicas.
- **Latency-induced probation.** Temporarily take a machine that has become slow out of the serving set, keep sending it shadow requests, and return it when it recovers. Removing a slow machine can lower overall latency even though it reduces capacity.
- Smaller supporting techniques: **canary requests** (send a fan-out to one or two leaves first so a query that crashes servers does not take down thousands), **good-enough results** (return once most shards have answered), prioritising interactive traffic over batch, splitting long requests into short ones to avoid head-of-line blocking, and throttling background work.

```arch
%% caption: A request that waits on every server is as slow as the slowest one; hedging sends a second copy to a replica after the p95 delay and takes whichever answers first.
node cl "User request" at 1.5,0 icon=user
node root "Fan-out root" at 1.5,1 icon=server color=amber sub="waits for all N"
node s1 "Server 1" at 0,2 icon=server
node s2 "Server 2" at 1,2 icon=server
node s3 "Server 3" at 2,2 icon=server color=red sub="slow: p99 tail"
node s3r "Replica of 3" at 3,2 icon=replica color=green sub="first answer wins"

cl -> root
root -> s1
root -> s2
root -> s3
root ..> s3r : "hedge after p95"
```

**Trade-offs.** Hedging spends extra capacity to buy latency: if you hedge at the p95, roughly 5% of requests get a second copy, which is cheap only while the system is not overloaded. If slowness is caused by overload rather than by one bad machine, a hedge adds load to the thing that is already struggling, so hedges need a budget and must be paired with the limits in [Overload Control and Graceful Degradation](28_overload_control_and_graceful_degradation.md) and [Application Resilience Patterns](12_application_resilience_patterns.md). Hedging is safe by default for reads; for writes it needs idempotency keys.

**Today.** The techniques are standard options: gRPC's retry design includes a hedging policy, Envoy supports hedging on per-try timeouts, and Cassandra exposes a `speculative_retry` table setting.

**Use it in an interview.** Whenever a design fans a query out to `N` shards, compute `1 − (1 − p)^N` before claiming a p99 target, then say what you will do about it: fewer shards per query, hedged reads after the p95, and micro-partitions so hot shards can be split. See also [Partitioning, Shard Keys, and Hot Keys](25_partitioning_and_hot_keys.md).

## Maglev (2016)

*Daniel E. Eisenbud et al., "Maglev: A Fast and Reliable Software Network Load Balancer", NSDI 2016.*

**Problem.** Google's front-end traffic needed a network load balancer whose capacity grows by adding commodity servers, in which every machine carries traffic (no idle standby), and whose software can be changed quickly, instead of a pair of hardware appliances.

**Key decisions.**

- Each virtual IP (VIP) is announced by all Maglev machines, and the upstream router spreads packets across them with **ECMP** (equal-cost multi-path). The load-balancing tier therefore scales out with no central coordinator.
- Each Maglev machine keeps a **connection-tracking table** keyed by the connection's five-tuple, so established connections stay on their backend. For a new connection it picks the backend from a **consistent-hashing lookup table**.
- **Maglev hashing.** The lookup table has `M` entries, where `M` is a prime much larger than the number of backends `N`. Each backend has its own pseudo-random preference order over the table's slots, and backends take turns claiming their next unclaimed slot until every slot is filled. Lookup is then `table[hash(five-tuple) mod M]`, O(1). The paper's point is that this gives a near-equal share to every backend and limited disruption when the backend set changes.
- Packets reach the backend encapsulated (GRE) and the backend replies directly to the client, so the response traffic does not pass through Maglev (**direct server return**).
- Packet processing runs in user space, bypassing the kernel network stack, to reach high packet rates on ordinary hardware.

```arch
%% caption: The router spreads a VIP's packets over every Maglev with ECMP; each Maglev picks the same backend from its consistent-hash table, and the backend replies straight to the client.
node cl "Client" at 0,0 icon=users
node rt "Router" at 2,0 icon=network sub="ECMP over one VIP"
group mg "Maglev machines (all active)" color=purple
node m1 "Maglev" at 1,1 in mg icon=lb sub="table[hash mod M]"
node m2 "Maglev" at 2,1 in mg icon=lb
node m3 "Maglev" at 3,1 in mg icon=lb
group be "Backends" color=orange
node b1 "Backend" at 0,2 in be icon=server
node b2 "Backend" at 1,2 in be icon=server
node b3 "Backend" at 2,2 in be icon=server

cl -> rt : "packet to VIP"
rt -> m1
rt -> m2
rt -> m3
m1 ==> b1 : "GRE"
b1 ..> cl : "direct server return"
```

**Trade-offs.** The lookup table exists because ECMP is not sticky: when the set of Maglev machines changes, the router may send later packets of a connection to a different machine that has no tracking entry, and hashing the same five-tuple into the same table usually lands on the same backend. "Usually" is the cost: tables can briefly disagree, and changes to the backend set can remap some flows, so a few connections may break. Compared with ring-based consistent hashing (see [Partitioning, Shard Keys, and Hot Keys](25_partitioning_and_hot_keys.md)), Maglev hashing favours even balance over minimal disruption. It is a layer-4 balancer: it sees connections, not requests, so request-level routing happens in a layer-7 tier behind it.

**Today.** The paper says Maglev has served Google's traffic since 2008 and also provides network load balancing for Google Cloud Platform. Envoy ships a `MAGLEV` load-balancing policy that uses this table construction. For the whole path from DNS to backend see [Scaling and Load Balancing](13_scaling_and_load_balancing.md) and [Networking](02_networking.md).

**Use it in an interview.** When asked "how does the load balancer itself scale and stay up?", answer with ECMP across active balancers plus a consistent-hash table so any balancer picks the same backend for a flow, and say what breaks (a few flows) during changes.

## Dapper (2010)

*Benjamin H. Sigelman et al., "Dapper, a Large-Scale Distributed Systems Tracing Infrastructure", Google Technical Report, 2010.*

**Problem.** A single user request crosses dozens of services, so no per-machine log shows where the time or the error came from. The tracing system had to be on for all services all the time, add negligible overhead, and need almost no work from application developers, or it would not be adopted.

**Key decisions.**

- A **trace** is a tree of **spans**. Each span carries a trace id, its own span id, its parent's id, a name and timestamps; RPC client and server sides each record their part of a span. **Annotations** (timestamped text or key-value pairs) let developers attach their own context to a span.
- **Transparency through shared libraries.** Dapper instruments the common threading, control-flow and RPC libraries, so the trace context (trace id and span id) follows a request without application changes.
- **Sampling** keeps overhead low. The first production version sampled uniformly, averaging one trace in 1,024, which the paper found effective for high-throughput services because notable patterns recur often. Low-traffic services need higher rates, which led to **adaptive sampling** by a target number of sampled traces per unit time. A second sampling stage at collection hashes the trace id, so whole traces are kept or dropped, never single spans.
- **Out-of-band collection.** Spans are written to local log files, pulled off the machines by daemons and collectors, and stored in Bigtable with one row per trace, so collection is never on the request path.

```arch
%% caption: Spans form a tree under one trace id carried by the RPC libraries; each machine logs its spans locally and daemons collect them out of band into Bigtable.
node fe "Frontend" at 1,0 icon=service sub="root span, sampling decision"
node sb "Service B" at 0,1 icon=service sub="span, parent = root"
node sc "Service C" at 2,1 icon=service sub="span, parent = root"
node sd "Service D" at 2,2 icon=service sub="span, parent = C"
group oob "Out-of-band collection" color=pink style=dashed
node lf "Local log files" at 0,3 in oob icon=logs
node dm "Daemons + collectors" at 1,3 in oob icon=worker
node bt "Bigtable" at 2,3 in oob icon=table sub="one row per trace"

fe -> sb : "RPC + trace id"
fe -> sc
sc -> sd
sb ..> lf : "write spans"
lf -> dm
dm -> bt
```

**Trade-offs.** Sampling before the outcome is known means a rare slow or failing request is usually *not* in the sample, which is why later tracing systems (the OpenTelemetry Collector, for example) offer tail-based sampling that decides after seeing the whole trace, at the cost of buffering spans. Traces break wherever context is not propagated: queues, thread pools and hand-written async code need explicit instrumentation. Annotations can leak sensitive data if not controlled.

**Today.** Zipkin and Jaeger follow the Dapper span model, and OpenTelemetry with the W3C Trace Context header is the standard way to propagate it. See [Observability and Reliability](15_observability_and_reliability.md).

**Use it in an interview.** In the observability section say "propagate a trace id through every hop, sample at the edge so overhead is bounded, and keep the trace id in logs so I can jump from a slow trace to the exact log lines."

## Monarch (2020)

*Colin Adams et al., "Monarch: Google's Planet-Scale In-Memory Time Series Database", VLDB 2020.*

**Problem.** Monitoring at Google's scale needs dashboards and alerting over a very large number of time series from every service and region, with queries that can span the globe, and it must keep working when the systems it monitors are failing. The paper presents Monarch as the replacement for Borgmon-style deployments that were operated as many separate instances.

**Key decisions.**

- **Regional zones.** Data is stored in memory, in the zone where it was collected, on leaf servers, with recovery logs written to durable storage. Ingestion never crosses a zone boundary, and a zone failure affects only that zone's data.
- **Global query layer.** A query enters a global root component, which fans out to per-zone components and then to leaves; an index of which zones and leaves can contain matching series lets the root skip zones that hold nothing relevant. Results are merged on the way back up, the same fan-out tree shape as Dremel.
- **Compute where the data is.** Monitoring inside a zone works independently of components outside it. Evaluators periodically run standing queries (alerts, pre-aggregation) and write the results back to the leaves as new time series, and operations that combine series from one zone are pushed down and finished in that zone.
- **A typed data model** with schemas for the entity being monitored and for the metric, including histogram ("distribution") values rather than only numbers.
- **Availability over consistency.** The paper says Monarch readily trades consistency for availability and partition tolerance: a blocking, strongly consistent store would delay alerts. It drops delayed writes and returns partial data for queries if necessary, with mechanisms to indicate that data may be incomplete or inconsistent.

```arch
%% caption: Metrics are ingested and held in memory in the zone that produced them; evaluators run alerts there, and a global root fans queries out only to zones that can match.
node dash "Dashboard / query" at 1.5,0 icon=dashboard
node root "Global root" at 1.5,1 icon=search color=amber sub="index skips zones"
group za "Zone A" color=blue
node qa "Zone mixer" at 0.5,2 in za icon=server
node la "Leaves" at 0,3 in za icon=memory sub="series in RAM"
node ea "Evaluator" at 1,3 in za icon=alert sub="alerts, pre-aggregation"
node src "Services" at 0,4 in za icon=service
group zb "Zone B" color=purple
node qb "Zone mixer" at 2.5,2 in zb icon=server
node lb "Leaves" at 2.5,3 in zb icon=memory sub="series in RAM"

dash -> root
root -> qa
root -> qb
qa -> la
qb -> lb
src -> la : "ingest (zone-local)"
ea -> la : "write results"
```

**Trade-offs.** The paper keeps data in memory to isolate itself from failures of the persistent storage layer and to keep the alerting path low-dependency, despite the higher cost per byte; older data goes to a long-term repository. Zone-local storage keeps writes cheap and failures contained, but a global query has to touch every relevant zone and may return incomplete answers. A dashboard that is slightly wrong during a failure is acceptable for monitoring and unacceptable for a ledger.

**Today.** Google documents Cloud Monitoring and its managed Prometheus service as running on Monarch. The same shape shows up outside Google as a per-region Prometheus plus a global query layer (Thanos, for example). See [Observability and Reliability](15_observability_and_reliability.md).

**Use it in an interview.** For a metrics or logging system: store data in the region that produced it, evaluate alerts there, and add a thin global query tier that tolerates partial results.

## Quick reference

| Paper | One-line lesson |
|---|---|
| GFS | Separate metadata from data; design for constant failure; relax consistency where apps can cope. |
| MapReduce | Restartable tasks and data locality make huge jobs routine; stragglers matter. |
| Bigtable | LSM tree + sorted row ranges; row-key design is performance design. |
| Chubby | A lock service with leases and sequencers; coarse-grained coordination only. |
| Spanner | Paxos per shard + 2PC + TrueTime = global external consistency, paid for in commit latency. |
| Dremel | Columnar + fan-out tree = interactive analytics at trillions of rows. |
| Borg | Mixed workloads and preemption buy utilisation; Kubernetes' ancestor. |
| Zanzibar | Relation tuples + consistency tokens = correct authorization at global scale. |
| Dynamo | Always writable via consistent hashing, sloppy quorums, vector clocks, anti-entropy. |
| Dataflow | What / where / when / how — the vocabulary of stream processing. |
| The Tail at Scale | Fan-out to `N` servers turns a 1-in-100 slow response into `1 − 0.99^N` slow requests; hedge, tie, micro-partition. |
| Maglev | Software L4 load balancers scaled with ECMP; a consistent-hash lookup table keeps a flow on one backend. |
| Dapper | Trace id through every hop, sample at the root, collect out of band. |
| Monarch | Store metrics in the zone that produced them, evaluate alerts there, query globally with partial results. |

## Related building blocks

- [Consensus and Coordination](19_consensus_and_coordination.md)
- [Specialized Data Structures and Indexes](20_specialized_data_structures.md)
- [Batch and Stream Processing](21_batch_and_stream_processing.md)
- [Google L5 System Design Playbook](../00_google_l5_playbook.md)
