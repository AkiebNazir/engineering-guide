# Kafka and Event Streaming

Apache Kafka is an event streaming platform: a cluster of servers that stores streams of
records durably in partitioned, replicated, append-only logs, so that many independent
consumers can read the same data at their own pace, replay it, and process it in order
per key. Unlike a traditional message queue, reading a record does not delete it. This
chapter starts with what a log-based stream is and why it exists, then goes through what
you need to run and design with Kafka: partitions and keys, replication and durability
settings, producer batching and idempotence, consumer groups and rebalancing, delivery
semantics and transactions, schemas, Connect and Streams, and an operations playbook.
Everything is current for Kafka 4.x, which runs without ZooKeeper.

## Foundations — What is an event stream, and why a log?

### The problem

An online shop takes an order. The payment service must charge it, the warehouse must
reserve stock, the email service must send a confirmation, the analytics pipeline must
count it, and the search index must update the "bestsellers" list. If the order service
calls all five synchronously, it becomes slow (it waits on each), fragile (any one being
down fails the order) and coupled (adding a sixth consumer means changing the order
service).

The alternative: the order service **publishes one event**, `OrderPlaced{id: 981, …}`, to
a durable stream and returns. Every interested system **subscribes** and reacts in its own
time. A new consumer can be added next month and even **replay** past orders to build its
initial state.

### Why a log

Kafka's core data structure is the **log**: an append-only, ordered sequence of records,
each with a sequential **offset**. Producers only append to the end; consumers read
forward from an offset they choose and remember. Because reads don't remove data, any
number of consumers can read the same log independently, one reading live at the head
while another replays last week. The log is kept for a configured retention (time or
size) regardless of whether anyone has read it.

### The pieces

| Piece | What it is | Everyday analogy |
|---|---|---|
| **Record** (message, event) | Key (optional), value (bytes), headers, timestamp | One line in a ledger |
| **Topic** | A named stream of records, such as `orders` | One ledger book |
| **Partition** | One ordered log; a topic is split into N partitions for parallelism | The book is split into volumes, each written in order |
| **Offset** | A record's position in its partition (0, 1, 2 …) | A line number |
| **Broker** | A Kafka server that stores partitions and serves reads and writes | A librarian with a shelf of volumes |
| **Producer** | A client that appends records | Someone writing entries |
| **Consumer group** | A set of consumers sharing the work of reading a topic; each partition goes to exactly one member | A team of readers who split the volumes between them |
| **Controller** | The brokers (in KRaft mode) that manage cluster metadata: which broker leads which partition | The head librarian's catalogue |

### How they fit

```arch
%% caption: Producers hash each key to a partition; each partition has a leader broker; each partition is read by exactly one consumer per group.
grid 170x105
node prod "Order service" at 1,0 icon=service sub="key → hash(key) % 3"
group cluster "Kafka cluster: topic orders" color=pink icon=kafka-icon
node b1 "Broker 1" at 0,1 in cluster icon=server sub="P0 leader"
node b2 "Broker 2" at 1,1 in cluster icon=server sub="P1 leader"
node b3 "Broker 3" at 2,1 in cluster icon=server sub="P2 leader"
group cga "Group: payments" color=green icon=worker
node c1 "Consumer A1" at 0,2 in cga icon=worker sub="reads P0"
node c2 "Consumer A2" at 1,2 in cga icon=worker sub="reads P1 + P2"
group cgb "Group: analytics" color=blue icon=metrics
node d1 "Consumer B1" at 2.5,2 in cgb icon=worker sub="P0 + P1 + P2"
prod -> b1
prod -> b2
prod -> b3
b1 -> c1
b2 -> c2
b3 -> c2
b3 ..> d1 : "own offsets"
```

Two groups read the same topic independently: payments has two members sharing the three
partitions; analytics has one member reading all three (only one of its edges is drawn). Each group has its own committed
offsets.

### Vocabulary table

| Term | Meaning |
|---|---|
| Leader / follower | Each partition has one leader replica that handles writes (and by default reads) and follower replicas that copy it |
| ISR | In-sync replicas: the replicas caught up with the leader |
| High watermark | The offset up to which records are replicated to all ISR members; consumers only see records below it |
| `acks` | How many replicas must have a record before the producer is told it succeeded |
| Consumer lag | Log end offset minus the group's committed offset, per partition |
| Rebalance | Redistributing partitions among group members when membership or subscriptions change |
| Compaction | A retention mode that keeps only the latest record per key |
| KRaft | Kafka's built-in Raft-based metadata quorum, which replaced ZooKeeper |

## 1. Cluster architecture and KRaft

A Kafka cluster is a set of brokers. Since **Kafka 4.0 (March 2025), ZooKeeper is gone**:
cluster metadata (topics, partitions, leaders, configs, ACLs) lives in an internal
replicated log, `__cluster_metadata`, managed by a **KRaft controller quorum** (usually
3 or 5 controller nodes, separate from brokers in production). One controller is the
active leader; brokers fetch metadata changes from it as a log. Migration from ZooKeeper
must be done on a 3.x release before upgrading to 4.x.

Why it matters: metadata changes are log appends instead of ZooKeeper writes, so failover
of the controller is fast, and clusters can hold far more partitions (the design target
is millions) than the ZooKeeper era's practical limits.

Each partition has a replication factor (typically 3), with replicas on different brokers,
ideally in different racks or availability zones (`broker.rack` makes Kafka spread
replicas across them).

## 2. Storage: segments, the page cache and retention

Each partition is a directory of **segment** files (`00000000000000368201.log` plus
`.index` and `.timeindex`). Only the newest segment is written; older ones are
immutable and deleted or compacted as a whole. Reads find the right segment by offset,
then use the sparse index to seek.

Why Kafka is fast:

- **Sequential I/O.** Appends and forward reads are sequential, which disks and SSDs do
  well.
- **The OS page cache** holds recent segments; consumers at the head read from memory.
  Kafka deliberately does not keep its own large in-heap cache.
- **Zero-copy.** For plaintext connections, the broker sends log bytes to the socket with
  `sendfile()`, never copying them through user space. (TLS prevents this, because the
  bytes must be encrypted in user space.)
- **Batching and compression end to end.** Producers compress batches; brokers store them
  as-is; consumers decompress. One network request carries many records.

### Retention

| Policy | Config | Keeps | Use for |
|---|---|---|---|
| Time | `retention.ms` (default 7 days) | Everything newer than the window | Event streams |
| Size | `retention.bytes` (per partition) | The newest N bytes | Bounding disk |
| **Compaction** | `cleanup.policy=compact` | At least the latest record for each key | Changelogs, "current state" topics (user profiles, CDC tables) |
| Both | `cleanup.policy=compact,delete` | Latest per key, within a time window | State that may expire |

Compaction deletes a key when it sees a **tombstone** (a record with that key and a null
value), after `delete.retention.ms`. Compaction runs on closed segments, so the active
segment can still hold older values for a key.

**Tiered storage** (KIP-405, production-ready since Kafka 3.9) moves closed segments to
object storage such as S3 or GCS while brokers keep only the recent tail on local disk,
which makes long retention cheap and broker replacement fast. Deeper internals are in
[Distributed Log Internals](../../interview-core/SystemDesign/building_blocks/26_distributed_log_internals.md).

## 3. Replication and durability

```arch
%% caption: The producer writes to the leader; followers fetch from it. A record is committed once every in-sync replica has it, and only then can consumers read it.
grid 170x100
node p "Producer" at 1,0 icon=service sub="acks=all"
node f1 "Follower (broker 1)" at 0,1 icon=replica sub="in ISR"
node lead "Leader (broker 2)" at 1,1 icon=server sub="P1 · LEO 1042"
node f3 "Follower (broker 3)" at 2,1 icon=replica sub="in ISR"
node hw "High watermark 1040" at 1,2 shape=pill color=green
node cons "Consumer" at 1,3 icon=worker sub="reads below HW"
p -> lead : "produce"
f1 -> lead : "fetch"
f3 -> lead : "fetch"
lead -> hw
hw -> cons
```

- Followers **pull** from the leader, like consumers. A follower that falls more than
  `replica.lag.time.max.ms` (30 s) behind is dropped from the **ISR**.
- The **high watermark** is the highest offset copied to every ISR member. Consumers see
  only records below it, so a consumer never reads a record that could be lost in a
  leader failover.
- If the leader dies, the controller elects a new leader from the ISR, so no committed
  record is lost.

### The durability settings, and what each protects against

| Setting | Where | Recommended for important data | Meaning |
|---|---|---|---|
| `replication.factor` | Topic | 3 | Copies of each partition |
| `acks` | Producer | `all` (the default since Kafka 3.0) | Success only after all current ISR members have the record |
| `min.insync.replicas` | Topic/broker | 2 | With `acks=all`, reject writes (`NotEnoughReplicas`) if fewer than 2 replicas are in sync |
| `unclean.leader.election.enable` | Topic/broker | `false` (default) | Never elect an out-of-sync replica, which would silently drop committed records |
| `enable.idempotence` | Producer | `true` (default since 3.0) | Retries can't create duplicates or reorder within a partition |

**The classic trap:** `acks=all` with `min.insync.replicas=1` (the default!) means that
when the ISR shrinks to just the leader, "all" is one replica, and a leader disk failure
loses acknowledged data. RF=3 with `min.insync.replicas=2` tolerates one broker down
while still accepting writes, and never acknowledges a write held by only one machine.

Kafka acknowledges after records reach the replicas' **page cache**, not after `fsync`;
durability comes from replication across machines (and racks or zones), not from each
disk flush.

## 4. Producers: keys, partitioning, batching

```python
# pip install confluent-kafka   (needs a running broker)
from confluent_kafka import Producer

p = Producer({
    "bootstrap.servers": "kafka-1:9092,kafka-2:9092",
    "acks": "all",
    "enable.idempotence": True,
    "linger.ms": 10,             # wait up to 10 ms to fill a batch
    "compression.type": "zstd",
})

def on_delivery(err, msg):
    if err:
        print("delivery failed:", err)            # alert, retry or dead-letter
    else:
        print(f"{msg.topic()}[{msg.partition()}] @ {msg.offset()}")

p.produce("orders", key="order-981", value=b'{"total": 42.50}', on_delivery=on_delivery)
p.flush(10)
```

**Partitioning.** With a key, the default partitioner uses `murmur2(key) % partitions`,
so all records for one key land in one partition and **stay in order relative to each
other**. There is no ordering across partitions. Without a key, the producer fills a
batch for one partition before moving on ("sticky" partitioning), which spreads load
while keeping batches large.

**Choosing the key** is a design decision: `order_id` gives per-order ordering;
`customer_id` gives per-customer ordering but lets one huge customer create a **hot
partition**. Partition count is effectively permanent for keyed topics: adding partitions
changes `hash % N`, so keys move and ordering across the change breaks. Size up front
(see §10).

**Batching.** `linger.ms` (default 5 ms since Kafka 4.0, 0 before) and `batch.size`
(16 KB default) trade a few milliseconds of latency for much higher throughput and better
compression. `buffer.memory` bounds unsent data; when it's full, `send` blocks for up to
`max.block.ms`, which is backpressure you must handle.

**Idempotence** gives each producer an ID and a sequence number per partition; the broker
discards duplicates caused by retries and rejects gaps. It makes retries safe *within one
producer session*. It does not stop your application from producing the same business
event twice (for that you need an idempotency key or transactions).

**Timeouts.** `delivery.timeout.ms` (default 2 minutes) bounds the total time for a send
including retries; after that the callback gets an error. Log and alert on these, never
ignore callbacks.

## 5. Consumers, consumer groups and rebalancing

### The poll loop

```python
from confluent_kafka import Consumer

c = Consumer({
    "bootstrap.servers": "kafka-1:9092",
    "group.id": "payments",
    "enable.auto.commit": False,         # commit after processing: at-least-once
    "auto.offset.reset": "earliest",     # where a brand-new group starts
    "group.protocol": "consumer",        # KIP-848 protocol (Kafka 4.0+ brokers and clients)
})
c.subscribe(["orders"])
try:
    while True:
        msg = c.poll(1.0)
        if msg is None:
            continue
        if msg.error():
            print("error:", msg.error())
            continue
        charge(msg.key(), msg.value())   # must be idempotent: it may run twice
        c.commit(message=msg, asynchronous=False)
finally:
    c.close()                            # leave the group cleanly: immediate rebalance, no timeout wait
```

(`charge` stands for your business logic.) Committing per message is simple but slow;
production code commits every N records or every few hundred milliseconds, or
asynchronously with a final synchronous commit on shutdown.

### Offsets

Committed offsets are stored in the internal compacted topic `__consumer_offsets`,
managed by the group's **coordinator** broker. The committed value is the *next* offset
to read. `auto.offset.reset` (`earliest` or `latest`) applies only when the group has no
committed offset for a partition (or it has been deleted by retention).

### Rebalancing

Partitions are assigned to group members; when a member joins, leaves, crashes or stops
polling, the group **rebalances**. A member is considered dead when:

- it stops sending heartbeats for `session.timeout.ms` (default 45 s), or
- it doesn't call `poll()` within `max.poll.interval.ms` (default 5 minutes), which is
  what happens when processing one batch takes too long.

| Protocol / mode | What happens | Cost |
|---|---|---|
| Classic, eager (`RangeAssignor`) | Every member revokes **all** partitions, rejoins, gets a new assignment | Whole group stops processing ("stop the world") for seconds |
| Classic, cooperative (`CooperativeStickyAssignor`) | Only partitions that must move are revoked, over two rounds | Others keep processing; needs care when migrating |
| Static membership (`group.instance.id`) | A restarting member with the same ID gets its partitions back if it returns within the session timeout | Rolling restarts don't rebalance; real failures are detected later |
| **KIP-848 (`group.protocol=consumer`)**, GA in Kafka 4.0 | The broker-side coordinator computes assignments and moves partitions incrementally; no global sync barrier | Needs 4.0-era brokers and clients |

<div class="lab" data-viz="flow-kafka-rebalance"></div>

### Parallelism

Within one group, **at most one consumer per partition**: a topic with 12 partitions
supports up to 12 active consumers; a 13th sits idle. To go faster than one consumer per
partition, either add partitions (with the keyed-ordering caveat) or process records
concurrently *within* a consumer while preserving per-key order (e.g. Confluent's
Parallel Consumer, or your own per-key worker queues). Kafka 4.x also introduces **share
groups** (KIP-932, "queues for Kafka"), where several consumers share a partition with
per-record acknowledgment and redelivery, like a work queue; check its status in your
Kafka version before relying on it.

### Lag

**Consumer lag** is the primary health signal of a consumer: log end offset minus
committed offset, per partition. Alert on lag *growing* for several minutes, and convert
it to time (lag divided by net drain rate); raw lag numbers mean little on their own.
Tools: `kafka-consumer-groups.sh --describe`, Burrow, or the exporter metrics in
Prometheus (chapter 06).

## 6. Delivery semantics

| Semantics | Consumer order of operations | On crash | Use when |
|---|---|---|---|
| **At-most-once** | Commit, then process | Records in flight are **lost** | Losing a metric sample is fine |
| **At-least-once** | Process, then commit | Records since the last commit are **reprocessed** | The default; make processing idempotent |
| **Exactly-once (Kafka to Kafka)** | Consume, produce results and commit offsets in **one transaction** | The transaction aborts and is retried; readers never see partial results | Stream processing pipelines inside Kafka |

**Idempotent processing** is what turns at-least-once into "effectively once" for side
effects outside Kafka: dedupe on an event ID (a unique constraint on
`processed_events(event_id)`), use upserts, or make the operation naturally idempotent
("set status to PAID" rather than "add 10").

**Transactions.** A producer with a `transactional.id` can write to several partitions
and commit consumer offsets atomically (`sendOffsetsToTransaction`). Consumers with
`isolation.level=read_committed` see only committed transactions. Kafka Streams enables
this with `processing.guarantee=exactly_once_v2`. Exactly-once does **not** extend to an
external database or an HTTP call: for those, use idempotency keys, or write to the
database and publish with the **transactional outbox** pattern
([Messaging and Streaming](../../interview-core/SystemDesign/building_blocks/09_messaging_and_streaming.md)).

## 7. Schemas and evolution

Producers and consumers are deployed independently, often by different teams in
different languages. If a producer renames a field, consumers break. A **schema
registry** (Confluent Schema Registry, Apicurio, AWS Glue Schema Registry) stores
versioned Avro, Protobuf or JSON Schema definitions; the serializer registers or looks up
the schema and puts a small schema ID in each record; the deserializer fetches the schema
by ID. The registry enforces a **compatibility mode** on every new version:

| Mode | New schema must be readable by… | Safe changes | Deploy order |
|---|---|---|---|
| `BACKWARD` (default) | New consumers reading old data | Delete fields, add optional fields (with defaults) | Consumers first |
| `FORWARD` | Old consumers reading new data | Add fields, delete optional fields | Producers first |
| `FULL` | Both | Add/remove optional fields with defaults | Any order |
| `*_TRANSITIVE` | …all previous versions, not just the last | Same, checked against the whole history | Needed when consumers replay old data |

Never reuse a Protobuf field number, never change a field's type in place, and give new
Avro fields defaults. See `content/data-and-apis/API/` for Protobuf evolution rules in depth.

## 8. The ecosystem: Connect, Streams, CDC

- **Kafka Connect** runs source and sink **connectors** (JDBC, S3, Elasticsearch,
  BigQuery…) as a scalable, fault-tolerant service configured by JSON, so you don't
  write a consumer for every integration. Single message transforms handle simple
  reshaping; failed records can go to a dead-letter topic.
- **Change data capture (CDC)** with **Debezium** reads a database's replication log
  (Postgres WAL, MySQL binlog) and emits every row change as an event: the cleanest way
  to stream a database into Kafka without dual writes.
- **Kafka Streams** is a Java library for stateful stream processing (joins, windowed
  aggregations) with state stored locally in RocksDB and backed up to compacted
  changelog topics. **Apache Flink** is the heavier, cluster-based alternative with
  richer event-time semantics and SQL. See [Stream Processing Fundamentals](../DataEngineering/04_stream_processing.md).

## 9. Kafka and the alternatives

| | Kafka | RabbitMQ | Pulsar | Redpanda | Kinesis / Pub/Sub / Event Hubs |
|---|---|---|---|---|---|
| Model | Partitioned log | Broker with queues and routing | Log with segment storage in BookKeeper; queues and streams | Kafka-API-compatible log (C++, no JVM) | Managed streams |
| Consumption | Pull, offsets per group | Push, per-message ack, deleted on ack | Both | Same as Kafka | Pull (Kinesis) / push or pull (Pub/Sub) |
| Replay | Yes, within retention | Only with RabbitMQ Streams | Yes | Yes | Yes, within retention |
| Ordering | Per partition | Per queue, single consumer | Per partition/key | Per partition | Per shard / ordering key |
| Routing | Topic + key only | Rich (exchanges, bindings) | Topics, subscriptions | Topic + key | Topic + filters |
| Ops burden | Moderate to high (managed: MSK, Confluent Cloud, Aiven) | Low to moderate | High | Moderate | None |
| Best for | High-throughput event streams, event sourcing, CDC, stream processing | Task queues, complex routing, RPC-style work | Multi-tenant geo-replicated streaming | Kafka workloads wanting lower tail latency | Teams all-in on one cloud |

For queue semantics and RabbitMQ specifically see [RabbitMQ and Message Brokers](05_rabbitmq_and_message_brokers.md).

## 10. Operations playbook

### Sizing partitions

Partitions bound consumer parallelism and per-partition throughput. A rough method:
`partitions ≥ max(target throughput / per-partition producer throughput, target
throughput / per-consumer throughput)`, then add headroom for 1–2 years of growth
because keyed topics can't easily be repartitioned. Per-partition throughput depends on
record size, compression and hardware; measure it with `kafka-producer-perf-test.sh`
rather than trusting a rule of thumb. Too many partitions cost memory, open files,
longer leader elections and more rebalance work. A worked sizing example is in
[Distributed Log Internals](../../interview-core/SystemDesign/building_blocks/26_distributed_log_internals.md).

### Everyday commands

```bash
kafka-topics.sh --bootstrap-server kafka:9092 --create --topic orders \
  --partitions 12 --replication-factor 3 --config min.insync.replicas=2
kafka-topics.sh --bootstrap-server kafka:9092 --describe --topic orders   # leaders, replicas, ISR
kafka-consumer-groups.sh --bootstrap-server kafka:9092 --describe --group payments   # lag per partition
kafka-consumer-groups.sh --bootstrap-server kafka:9092 --group payments --topic orders \
  --reset-offsets --to-datetime 2026-09-01T00:00:00.000 --execute     # replay (group must be stopped)
kafka-console-consumer.sh --bootstrap-server kafka:9092 --topic orders \
  --from-beginning --property print.key=true --max-messages 10
```

### Failure modes

| Symptom | Likely cause | Fix |
|---|---|---|
| Lag grows on all partitions | Consumers too slow or too few | Scale consumers (up to partition count), speed up processing, batch downstream writes |
| Lag grows on one partition | Hot key, or one stuck consumer | Better key, key salting, or split the hot entity; check that consumer |
| Repeated rebalances ("rebalance storm") | Processing exceeds `max.poll.interval.ms`, GC pauses, frequent deploys | Smaller `max.poll.records`, longer interval, static membership, cooperative or KIP-848 protocol |
| Duplicates downstream | At-least-once after a crash or rebalance | Idempotent processing keyed on event ID |
| `NotEnoughReplicas` errors | ISR fell below `min.insync.replicas` | Investigate the slow or down broker; that is the setting doing its job |
| Under-replicated partitions | Broker down, slow disk, network | Alert on `UnderReplicatedPartitions > 0`; replace or rebalance with Cruise Control |
| Poison record blocks a partition | A record the consumer can't handle, retried forever | Catch, send to a dead-letter topic with error context, commit and move on |
| Consumers read nothing after deploy | New `group.id` with `auto.offset.reset=latest` | Decide the reset policy deliberately; reset offsets explicitly |

Security basics: TLS for encryption in transit, SASL (SCRAM or OAUTHBEARER) or mTLS for
authentication, ACLs per topic and group, and quotas so one client can't starve the
cluster.

## Common interview questions

**"How does Kafka guarantee ordering?"**
Only within a partition. Records with the same key go to the same partition (hash of the
key), so per-key order is preserved as long as the partition count doesn't change and the
producer is idempotent (retries can't reorder). There is no global order across
partitions.

**"How do you make sure Kafka doesn't lose data?"**
Replication factor 3, `acks=all`, `min.insync.replicas=2`, unclean leader election
disabled, idempotent producer, replicas spread across zones, and a producer that
handles delivery errors. On the consumer side, commit offsets only after processing.

**"What happens when a consumer in a group dies?"**
Its heartbeats stop; after `session.timeout.ms` the coordinator removes it and
rebalances; its partitions move to other members, which resume from the last committed
offsets, so records processed but not committed are processed again.

**"What is a rebalance storm, and how do you stop one?"**
Members repeatedly leave and rejoin, typically because processing a batch takes longer
than `max.poll.interval.ms` or deploys restart members one at a time. Reduce
`max.poll.records` or speed up processing, raise the interval, use static membership for
rolling restarts, and use cooperative rebalancing or the KIP-848 protocol.

**"Explain at-least-once vs exactly-once in Kafka."**
At-least-once: process then commit, so a crash repeats work; consumers must be idempotent.
Exactly-once: transactions atomically write outputs and commit offsets, with
`read_committed` consumers, which only covers Kafka-to-Kafka pipelines. External side
effects need idempotency keys or the outbox pattern.

**"How many partitions should a topic have?"**
Enough for peak throughput and the consumer parallelism you need, with headroom, because
changing it later reshuffles keys. Measure per-partition throughput; don't create
thousands "just in case" because each partition has a cost.

**"Kafka or RabbitMQ?"**
Kafka for high-throughput streams that several consumers read independently, replay,
ordering per key and stream processing. RabbitMQ for task queues with per-message acks,
flexible routing, priorities and delayed retries.

**"What changed with KRaft?"**
Kafka 4.0 removed ZooKeeper; metadata is a Raft-replicated log managed by controller
nodes. Faster controller failover, more partitions per cluster, one system to operate.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | Explain topic, partition, offset, producer, consumer and consumer group; why reading doesn't delete; produce and consume with the console tools |
| Junior (L3) | Software Engineer I / New grad | L3 | Write a producer with keys and delivery callbacks and a consumer with manual commits; explain per-partition ordering and at-least-once; read lag with `kafka-consumer-groups` |
| Mid (L4) | Software Engineer II | L4 | Choose keys and partition counts; configure `acks`, idempotence, `min.insync.replicas`; handle rebalances, poison records and dead-letter topics; design idempotent consumers; use a schema registry correctly |
| Senior (L5) | Senior Software Engineer | L5 | Explain ISR, high watermark and leader election; diagnose rebalance storms, hot partitions and lag; use transactions and the outbox pattern appropriately; design topic, schema and retention strategy across teams |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7 | Own the streaming platform: multi-cluster and multi-region replication (MirrorMaker 2, Cluster Linking), tiered storage and cost, KRaft migration and upgrades, managed vs self-hosted, governance of schemas and data contracts across the organization |

## Interview checklist

- [ ] I can explain why a log with offsets lets many consumers read independently and replay.
- [ ] I can explain partitions as the unit of ordering and parallelism, and how keys map to partitions.
- [ ] I know ZooKeeper was removed in Kafka 4.0 and what KRaft controllers do.
- [ ] I can explain segments, page cache, zero-copy, retention, compaction and tombstones.
- [ ] I can explain leader, followers, ISR and high watermark.
- [ ] I can state the no-data-loss configuration and the `min.insync.replicas=1` trap.
- [ ] I can explain producer batching, `linger.ms`, compression and idempotence.
- [ ] I can explain consumer groups, the one-consumer-per-partition limit and offset commits.
- [ ] I can compare eager, cooperative, static and KIP-848 rebalancing and fix a rebalance storm.
- [ ] I can compare at-most-once, at-least-once and exactly-once, and where exactly-once stops.
- [ ] I can explain schema registry compatibility modes and safe schema changes.
- [ ] I can use `kafka-topics` and `kafka-consumer-groups` to inspect ISR and lag and reset offsets.
- [ ] I can choose between Kafka, RabbitMQ and a managed cloud stream for a given workload.

Related: [Distributed Log Internals](../../interview-core/SystemDesign/building_blocks/26_distributed_log_internals.md) (log internals and
sizing), [Messaging and Streaming](../../interview-core/SystemDesign/building_blocks/09_messaging_and_streaming.md) (queues vs streams,
outbox, idempotency), [RabbitMQ and Message Brokers](05_rabbitmq_and_message_brokers.md),
[Stream Processing Fundamentals](../DataEngineering/04_stream_processing.md) (Flink and Kafka Streams),
[Observability and Monitoring](06_observability_and_monitoring.md) (monitoring lag).
