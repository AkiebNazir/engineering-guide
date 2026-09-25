# Building Blocks of Any System

This is the first module. Do not rush to microservices, Kafka, Kubernetes, or multi-region design. A system is a set of responsibilities connected by flows. Learn what each responsibility does, when it earns its place, and what it costs — then use the decision framework at the end of this module to go from a requirement to a defensible design, out loud.

## The universal request path

Most internet systems can begin with this picture:

```arch
%% caption: The universal request path: an edge in front, a stateless tier in the middle, stores and async work behind it.
node client "Client" at 0,0 icon=client
node dns "DNS" at 1,0 icon=dns
node edge "Edge" at 2,0 icon=cdn sub="CDN · WAF"
node lb "Load balancer" at 3,0 icon=lb sub="or API gateway"
node app "Stateless application" at 1,1 icon=server
group stores "Data stores" color=green icon=storage
node cache "Cache" at 0,2 in stores icon=cache
node db "Primary data store" at 1,2 in stores icon=db
node obj "Object store" at 2,2 in stores icon=blob
node queue "Broker / queue" at 3,2 icon=queue
node worker "Async workers" at 3,3 icon=worker sub="& integrations"
client -> dns -> edge -> lb
lb -> app
app -> cache:T
app -> db
app -> obj:T
app ..> queue:T : "async"
queue -> worker
```

> 💡 This diagram is a checklist, not a blueprint. It is not an architecture to copy blindly — it is a map for asking questions: which of these does my requirement actually need, and what does adding it cost?

> ⚠️ Every box on this diagram is a thing that can be down, slow, or wrong. Adding one because "that's what real systems use" — without a requirement it satisfies — is the single most common system-design-interview mistake.

| Component | Job | Add it when | Do not use it as |
|---|---|---|---|
| Client | Presents UX, sends requests, stores limited local state. | Always. | A trusted authority for permissions, prices, or data integrity. |
| <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> | Maps a name to a reachable endpoint. | Every public service. | Precise real-time failover/load balancing; resolvers cache it. |
| <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> | Serves cacheable content near the user. | Static assets, media, public/cacheable responses, global latency. | Your authorization or primary database. |
| WAF/DDoS edge | Filters malformed/known abusive traffic before origin. | Public endpoints. | Complete business-abuse prevention. |
| Load balancer | Sends traffic to healthy instances. | More than one serving instance or managed ingress. | A database, queue, or authorization engine. |
| <abbr title="Application Programming Interface">API</abbr> gateway | Routes APIs; centralizes coarse auth, quotas, request policy, telemetry. | Multiple APIs/clients or a need for a consistent edge contract. | A place for all business logic. |
| Application service | Implements domain rules and orchestrates dependencies. | Any nontrivial product action. | The permanent home of user session or unreplicated critical state. |
| Operating system | Schedules processes/threads, manages memory and I/O. | Always — it's the substrate everything else sits on. | Something you can ignore because "the cloud handles it." |
| Database | Durable authoritative facts and constraints. | Any durable business state. | A high-speed cache or free full-text search engine. |
| Cache | Fast derived copy of data/results. | Measured read latency/load justifies it. | The only copy of important data. |
| Object store | Durable blobs: images, video, documents, backups. | Large/unstructured objects. | A transactional relational data store. |
| Broker/queue | Buffers and delivers asynchronous work/events. | Work can happen later, be retried, or fan out. | A replacement for a data model or idempotency. |
| Worker | Consumes background work. | Slow/bursty/failure-prone work. | A reason to ignore progress, retries, and backpressure. |
| Observability | Produces evidence about behavior. | From the first deploy. | An afterthought added after the first outage. |

> 🎯 When an interviewer says "design X," the strongest opening move is naming which rows of this table X actually needs — out loud — before you draw a single box. It signals you're solving *this* requirement, not reciting a template.

<details>
<summary>Why does the diagram put the load balancer before the <abbr title="Application Programming Interface">API</abbr> gateway, not after?</summary>

They can be the same box, or two boxes in either order, depending on the product:

- **<abbr title="Load Balancer - A device or software service that distributes network or application traffic across a number of servers to improve capacity and reliability.">LB</abbr> → gateway** (most common): the load balancer just spreads <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr>/<abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> connections across healthy gateway instances — it doesn't understand your <abbr title="Application Programming Interface">API</abbr>. The gateway then does the <abbr title="Application Programming Interface">API</abbr>-aware work: auth, rate limits, routing by path.
- **Gateway → <abbr title="Load Balancer - A device or software service that distributes network or application traffic across a number of servers to improve capacity and reliability.">LB</abbr>**: rarer, used when the gateway itself is a single managed edge (e.g. a cloud <abbr title="Application Programming Interface">API</abbr> gateway service) that then load-balances to backend pools per route.

The diagram picks the common case. In an interview, say which one you mean and why — "managed <abbr title="Application Programming Interface">API</abbr> gateway that fans out to per-service load balancers" is a complete, defensible sentence; "there's a gateway and a load balancer" is not.

</details>

## Reading order

| File | Covers |
|---|---|
| [01_operating_systems.md](01_operating_systems.md) | Processes/threads, memory, I/O, scheduling — the substrate every other layer sits on. |
| [02_networking.md](02_networking.md) | The request path end to end: <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>, WAF/DDoS, <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr>, <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr>, <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>/1.1 vs. /2 vs. /3, the latency budget, and what a load balancer does. |
| [03_api_design_high_level.md](03_api_design_high_level.md) | <abbr title="Representational State Transfer - An architectural style for distributed hypermedia systems, commonly used for creating interactive web services.">REST</abbr> vs. <abbr title="Remote Procedure Call - A protocol that allows one program to request a service from a program located in another computer on a network.">RPC</abbr> vs. WebSocket vs. webhook vs. queue; resource modeling, pagination, versioning, error contract, idempotency keys, sync vs. async contracts. |
| [04_api_design_low_level.md](04_api_design_low_level.md) | Wire-level mechanics: <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr> method and status semantics, caching headers, serialization formats, connection reuse, token and mTLS auth, token-bucket rate limiting, deadline propagation. |
| [05_databases.md](05_databases.md) | Relational-first modeling, primary keys, indexes, normalization vs. denormalization, read replicas and staleness, conditional updates for check-then-act races. |
| [06_database_internals.md](06_database_internals.md) | B-tree vs. <abbr title="Log-Structured Merge-tree. A data structure with performance characteristics that make it attractive for providing indexed access to files with high insert volume.">LSM</abbr> tree, <abbr title="Write-Ahead Logging. A family of techniques for providing atomicity and durability in database systems by writing modifications to a log before they are applied.">WAL</abbr>, <abbr title="Multi-Version Concurrency Control. A concurrency control method commonly used by database management systems to provide concurrent access without locking.">MVCC</abbr> — why storage engines behave differently under load. |
| [07_caching.md](07_caching.md) | Cache-aside, invalidation, stampedes, staleness. |
| [08_object_storage.md](08_object_storage.md) | Blob storage, signed uploads, lifecycle and derivative handling. |
| [09_messaging_and_streaming.md](09_messaging_and_streaming.md) | Work queues, pub/sub, durable event streams, workflow engines, at-least-once delivery, transactional outbox. |
| [10_distributed_systems_theory.md](10_distributed_systems_theory.md) | Remote-call outcomes, <abbr title="CAP Theorem - A concept stating that a distributed data store can only simultaneously provide two out of three guarantees: Consistency, Availability, and Partition tolerance.">CAP</abbr>/PACELC, the consistency-model partial order, conflict resolution, clocks and unique IDs. |
| [11_transactions_and_concurrency.md](11_transactions_and_concurrency.md) | <abbr title="Atomicity, Consistency, Isolation, Durability - A set of properties of database transactions intended to guarantee data validity despite errors.">ACID</abbr>, isolation anomalies and what each isolation level defends (database-dependent), optimistic vs. pessimistic concurrency, sagas. |
| [12_application_resilience_patterns.md](12_application_resilience_patterns.md) | Pool sizing, timeout budgets, retries, circuit breakers, bulkheads, backpressure, and why latency explodes near saturation (Little's Law vs. queueing). |
| [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md) | Balancing algorithms, autoscaling signals, queueing theory intuition. |
| [14_security.md](14_security.md) | AuthN/AuthZ, secrets, encryption, input validation, threat checklist. |
| [15_observability_and_reliability.md](15_observability_and_reliability.md) | Metrics/logs/traces/profiles, <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>/error budgets, alert design, backups, RPO/RTO, failure domains, safe deployment, capacity planning, tail latency and hedged requests, multi-region DR. |
| [16_platform_and_infra.md](16_platform_and_infra.md) | Containers/Kubernetes, service mesh, eBPF, IaC/GitOps/progressive delivery. |
| [17_decision_framework.md](17_decision_framework.md) | Capstone — requirement-to-component translation, the decision worksheet, the interview decision tree. Read this one last in the core sequence. |

### Google L5 depth

Read these after the core sequence. They cover what the Google design round pushes on that the core files only touch.

| File | Covers |
|---|---|
| [18_back_of_envelope_estimation.md](18_back_of_envelope_estimation.md) | The estimation method, latency numbers, powers of two, availability nines, worked examples. |
| [19_consensus_and_coordination.md](19_consensus_and_coordination.md) | Quorums (R + W > N), Raft, Paxos, leases and fencing tokens, Chubby/ZooKeeper/etcd, gossip, Merkle-tree anti-entropy, clocks and TrueTime. |
| [20_specialized_data_structures.md](20_specialized_data_structures.md) | Bloom filters, HyperLogLog, count-min sketch, geohash/quadtree/S2, inverted indexes and BM25, sorted-set leaderboards, <abbr title="Log-Structured Merge-tree. A data structure with performance characteristics that make it attractive for providing indexed access to files with high insert volume.">LSM</abbr> trees. |
| [21_batch_and_stream_processing.md](21_batch_and_stream_processing.md) | MapReduce, Spark, Dataflow/Flink, event time, windows, watermarks, exactly-once, lambda vs kappa. |
| [22_realtime_and_collaboration.md](22_realtime_and_collaboration.md) | Polling vs <abbr title="Server-Sent Events - A standard describing how servers can initiate data transmission towards clients once an initial connection is established.">SSE</abbr> vs WebSockets, connection gateways, presence, operational transformation vs CRDTs. |
| [23_ml_and_llm_systems.md](23_ml_and_llm_systems.md) | Feature stores, candidate generation → ranking, ANN search (HNSW, ScaNN), model serving, <abbr title="Large Language Model">LLM</abbr> serving and cost. |
| [24_google_papers.md](24_google_papers.md) | GFS, MapReduce, Bigtable, Chubby, Spanner, Dremel, Borg, Zanzibar, Dynamo, and the Dataflow model. |
| [25_partitioning_and_hot_keys.md](25_partitioning_and_hot_keys.md) | Shard-key choice, range vs hash, local vs global secondary indexes, rebalancing, hot-key mitigation. |

### Global-scale and industry depth

Read these after the Google depth files. They cover what Meta, Netflix, Amazon and Google rounds probe once the single-region design is settled: how the log under a stream works, running in many regions, staying up under overload, video and social-graph workloads, ranking and experimentation, and how to cite published systems accurately.

| File | Covers |
|---|---|
| [26_distributed_log_internals.md](26_distributed_log_internals.md) | How a replicated, partitioned, append-only log works inside: replication and the commit point, segments, retention and compaction, producer idempotence, consumer offsets. |
| [27_multi_region_and_global_traffic.md](27_multi_region_and_global_traffic.md) | Running in more than one region: home-region vs. active-active, steering users to a region (<abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>, anycast), cross-region replication and its consistency cost, regional failover. |
| [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md) | Staying useful past capacity: load shedding and admission control, priorities and fairness, adaptive concurrency limits, retry and hedging budgets, deliberate feature degradation. |
| [29_cdn_and_streaming_media.md](29_cdn_and_streaming_media.md) | Delivering large objects and video: <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> cache hierarchy and origin protection, adaptive-bitrate streaming, live vs. on-demand, egress cost. |
| [30_social_graph_and_caching_at_scale.md](30_social_graph_and_caching_at_scale.md) | Storing and serving a social graph, and the multi-tier caching that keeps read-heavy graph workloads alive (fan-out, hot objects, invalidation). |
| [31_ranking_recommendation_and_experimentation.md](31_ranking_recommendation_and_experimentation.md) | Ranking and recommendation as a system (cascade budget, retrieval, features, logging what was shown, offline vs. online metrics) and experimentation platforms (bucketing, layers, exposure logging, statistics, ramp-up). |
| [32_industry_papers_and_case_studies.md](32_industry_papers_and_case_studies.md) | Published industry systems beyond Google's: what each paper or engineering write-up actually says, the design lesson, and how to cite it without overclaiming. |
