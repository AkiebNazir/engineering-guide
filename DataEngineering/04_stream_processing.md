# Stream Processing Fundamentals

Batch processing (a Spark job or dbt run every night) means the numbers are up to a
day old. Fraud detection, surge pricing, live dashboards, alerting and ad budget pacing
cannot wait that long, so data engineers build **stream processing** pipelines that
compute results continuously as events arrive. This chapter explains streams from
zero, then goes deep on the parts interviews actually test: event time vs. processing
time, windows, watermarks and late data, state and checkpoints, exactly-once
semantics, stream joins, backpressure, and choosing between Flink, Spark Structured
Streaming and Kafka Streams.

## Foundations — What does it mean to process data "as it arrives"?

### Bounded vs. unbounded data

A batch job reads a **bounded** dataset: yesterday's files. It knows when the input
ends, so it can sort, count and join everything and then stop.

A stream processor reads an **unbounded** dataset: every click, forever. There is no
"end" to wait for. Instead the job runs permanently, keeps running totals and other
**state**, and emits results continuously. The input is usually a durable, replayable
**log** such as Apache Kafka, Amazon Kinesis or Google Pub/Sub.

Everyday example: a bank watching card payments. Batch: every morning, list yesterday's
suspicious payments. Streaming: as each payment arrives, compare it to the last 10
minutes of that card's activity and block it within 200 ms if it looks like fraud.
Same logic, very different freshness and very different engineering.

### The pieces

| Piece | Role | Examples |
|---|---|---|
| **Producers** | Emit events (apps, services, CDC from databases) | Mobile SDKs, backend services, Debezium ([chapter 1](01_oltp_vs_olap.md)) |
| **Event log / broker** | Durable, ordered, partitioned, replayable storage for events | Kafka, Redpanda, Kinesis, Pub/Sub, Pulsar |
| **Stream processor** | Continuously reads, transforms, aggregates and joins, keeping state | Apache Flink, Spark Structured Streaming, Kafka Streams, Beam on Dataflow |
| **State store** | The processor's memory of the past (counts per window, last value per key) | Flink RocksDB state, Kafka Streams RocksDB + changelog topics |
| **Checkpoint storage** | Durable snapshots of state and input positions, for recovery | S3, GCS, HDFS |
| **Sinks** | Where results go | Kafka topics, databases, Iceberg/Delta tables, real-time OLAP (Pinot, ClickHouse), alerts |

```arch
%% caption: A streaming pipeline. Producers append events to a partitioned log; a stateful processor reads it continuously, keeps keyed state in a local store, snapshots state and offsets to object storage, and writes results to sinks.
grid 160x110
group prod "Producers" color=slate icon=users
node mob "Mobile apps" at 0,0 in prod icon=mobile sub="clicks, events"
node svc "Services" at 0,1 in prod icon=service sub="payments"
node cdc "CDC" at 0,2 in prod icon=sync sub="Debezium"
node kafka "Kafka" at 1,1 icon=kafka-icon sub="partitioned log"
group job "Stream processor (Flink)" color=purple icon=cpu
node op "Operators" at 2,1 in job icon=worker sub="keyBy, window, join"
node st "Keyed state" at 2,2 in job icon=kv sub="RocksDB, local disk"
node ck "Checkpoints" at 3,2 icon=storage sub="S3: state + offsets"
group sinks "Sinks" color=green icon=layers
node olap "Real-time OLAP" at 3,0 in sinks icon=dashboard sub="Pinot / ClickHouse"
node lake "Iceberg table" at 3,1 in sinks icon=table
mob -> kafka
svc -> kafka
cdc -> kafka
kafka -> op
op -> st
st ..> ck : "snapshot"
op -> olap
op -> lake
```

### Vocabulary

| Term | Meaning |
|---|---|
| Event time | When the event actually happened (timestamp set on the device or service) |
| Processing time | When the processor handles it (the server's wall clock) |
| Window | A finite slice of an infinite stream that an aggregate is computed over |
| Watermark | The processor's estimate that "no more events older than *T* will arrive" |
| Late event | An event whose event time is behind the current watermark |
| State | Data the processor remembers between events (counts, sums, last-seen values) |
| Checkpoint | A consistent snapshot of all state plus input offsets, used to recover |
| Backpressure | Slowing upstream when downstream cannot keep up |
| Exactly-once | The *effect* on state and outputs is as if every event were processed once |

## 1. The log underneath: Kafka in five minutes

Almost every streaming pipeline starts from a partitioned log. What you need to know
for stream processing (Kafka itself is covered in depth in
[Kafka and Event Streaming](../Tool-Kit/04_kafka_and_event_streaming.md)
and [Distributed Log Internals](../SystemDesign/building_blocks/26_distributed_log_internals.md)):

- A **topic** is split into **partitions**. Each partition is an append-only, ordered
  sequence of records, each with an **offset**. Order is guaranteed only *within* a
  partition.
- The producer chooses the partition, usually `hash(key) mod partitions`, so all
  events for one key (one user, one card) are in order on one partition.
- A **consumer group** divides partitions among its members; each partition is read by
  exactly one member of the group. The partition count caps a job's parallelism.
- Consumers track their position by **committing offsets**. Because the log is
  retained (days, or forever with tiered storage or compaction), a consumer can
  **replay**: rewind offsets and reprocess. This is what makes streaming results
  recomputable.
- Kafka 4.0 (2025) runs only in **KRaft** mode; ZooKeeper is gone.

## 2. Time: event time vs. processing time

```text
event time       12:00:05   12:00:12   12:00:58   12:00:47   12:01:11
processing time  12:00:06   12:00:13   12:00:59   12:01:02   12:01:12
                                                      ^ arrived 15 s late and out of order
```

Events arrive **late** and **out of order** because of mobile networks, retries,
batching in SDKs, clock skew and phones that are offline for hours (a flight, a
tunnel). If you aggregate by processing time, a phone that reconnects at 09:00 dumps
last night's clicks into the 09:00 bucket: easy, deterministic in real time, and wrong,
and replaying the same data tomorrow gives different answers.

Aggregating by **event time** gives the right answer and the same answer on replay.
The price: you must decide how long to wait for stragglers. That decision is the
watermark (§4).

Also know **ingestion time**: the time the broker received the event. It is a
compromise when device clocks cannot be trusted.

## 3. Windows

You cannot compute an average over an infinite stream, so you chop it into finite
windows.

| Window | Definition | Example |
|---|---|---|
| **Tumbling** | Fixed size, non-overlapping, aligned: `[12:00, 12:01)`, `[12:01, 12:02)` | Clicks per ad per minute for billing |
| **Hopping / sliding** | Fixed size, overlapping, advancing by a slide: size 10 min, every 1 min | "Orders in the last 10 minutes", refreshed each minute. Each event belongs to size/slide windows (10 here) |
| **Session** | Per key, closes after a gap of inactivity | A user's session ends after 30 minutes idle |
| **Global + trigger** | One window per key, emitted on a custom trigger | Running totals emitted every 1,000 events |

Notes that matter in practice:

- Hopping windows multiply state and output by size/slide. A 24-hour window sliding
  every minute puts each event in 1,440 windows; use pre-aggregated panes or a
  different design.
- Session windows **merge**: two sessions for a user become one when an event lands in
  the gap between them. Pair the gap with a maximum session length so a key with a
  steady trickle of events does not keep its window open forever.
- Windows are half-open intervals. An event at exactly 12:01:00.000 belongs to
  `[12:01, 12:02)`.

## 4. Watermarks and late data

A **watermark** with timestamp *T* flowing through the job is an assertion: *"from here
on, I do not expect events with event time ≤ T."* When the watermark passes the end
of a window, the window **fires**: it emits its result.

The most common strategy is **bounded out-of-orderness**:

```text
watermark = (largest event time seen so far) − (max expected delay)
```

With a 20-second bound, once the job has seen an event stamped 12:01:23, the watermark
is 12:01:03, so the `[12:00, 12:01)` window can fire.

**Precision note:** a watermark is measured in **event time**, not wall-clock time. A
common wrong explanation is "a 10-minute watermark waits 10 minutes". It does not wait
at all in wall-clock terms: it advances only as newer events arrive. If traffic stops,
the watermark stops too, and windows do not fire (see *idle sources* below).

### What happens to late events

An event is late if its event time is behind the current watermark. The options:

| Policy | Behaviour | Cost |
|---|---|---|
| **Drop** | Ignore it; count it in a metric | Simple; results are slightly incomplete |
| **Allowed lateness** | Keep the window's state for an extra period after it fires; a late event updates the window and it **fires again** with a corrected result | More state; the sink must accept updates (upsert by window key) |
| **Side output** | Route too-late events to a separate stream (a "late events" topic or table) | Someone must reconcile them, often a batch job |

The trade-off in one sentence: **a tighter bound gives fresher results and more late
events; a looser bound gives more complete results, later, with more state held in
memory.** Pick the bound from the measured delay distribution (for example, the p99 of
`processing_time − event_time`) and monitor the late-event rate.

### Simulating it

This pure-Python simulation implements a 1-minute tumbling window, a 20-second
out-of-orderness bound and 30 seconds of allowed lateness:

```python
from collections import defaultdict

WINDOW = 60            # 1-minute tumbling windows (seconds)
MAX_DELAY = 20         # bounded out-of-orderness: watermark = max event time seen - 20 s
ALLOWED_LATENESS = 30  # keep a fired window's state 30 s more (of event time) for updates

# (arrival order) event time in seconds since 12:00:00, and the user who clicked
events = [(5, "a"), (12, "b"), (58, "c"), (47, "d"), (71, "e"), (83, "f"),
          (55, "g"),   # late but within allowed lateness -> updated result
          (95, "h"), (130, "i"), (145, "k"),
          (40, "j")]   # too late: its window's state is already gone -> side output

counts = defaultdict(int)          # window start -> count (the operator's state)
fired, dropped = set(), []
watermark = float("-inf")

def ts(sec):
    return f"12:{sec // 60:02d}:{sec % 60:02d}"

for event_time, user in events:
    start = event_time - event_time % WINDOW
    end = start + WINDOW
    if end + ALLOWED_LATENESS <= watermark:
        dropped.append((ts(event_time), user))
        print(f"event {ts(event_time)} {user}: window [{ts(start)},{ts(end)}) already purged -> side output")
        continue
    counts[start] += 1
    if start in fired:
        print(f"event {ts(event_time)} {user}: late, window [{ts(start)},{ts(end)}) re-fires count={counts[start]}")
    watermark = max(watermark, event_time - MAX_DELAY)
    for w in sorted(counts):                       # fire every window the watermark has passed
        if w + WINDOW <= watermark and w not in fired:
            fired.add(w)
            print(f"watermark {ts(watermark)}: window [{ts(w)},{ts(w + WINDOW)}) fires count={counts[w]}")
    for w in [w for w in counts if w + WINDOW + ALLOWED_LATENESS <= watermark]:
        del counts[w]                              # state cleanup bounds memory

print("side output (too late):", dropped)
```

```text
watermark 12:01:03: window [12:00:00,12:01:00) fires count=4
event 12:00:55 g: late, window [12:00:00,12:01:00) re-fires count=5
watermark 12:02:05: window [12:01:00,12:02:00) fires count=3
event 12:00:40 j: window [12:00:00,12:01:00) already purged -> side output
side output (too late): [('12:00:40', 'j')]
```

Note the event at 12:00:47 arrived after 12:00:58 but *before* the watermark passed
12:01, so it was simply counted: out-of-order is not the same as late.

### The same thing in real engines

**Flink SQL** (window table-valued functions):

```sql
CREATE TABLE clicks (
  user_id    STRING,
  ad_id      STRING,
  event_time TIMESTAMP(3),
  WATERMARK FOR event_time AS event_time - INTERVAL '20' SECOND
) WITH (
  'connector' = 'kafka',
  'topic' = 'clicks',
  'properties.bootstrap.servers' = 'kafka:9092',
  'properties.group.id' = 'click-agg',
  'scan.startup.mode' = 'earliest-offset',
  'format' = 'json'
);

SELECT window_start, window_end, ad_id, COUNT(*) AS clicks
FROM TABLE(TUMBLE(TABLE clicks, DESCRIPTOR(event_time), INTERVAL '1' MINUTE))
GROUP BY window_start, window_end, ad_id;
```

**Flink DataStream API** (Java, Flink 2.x), with allowed lateness and a side output:

```java
WatermarkStrategy<Click> watermarks = WatermarkStrategy
    .<Click>forBoundedOutOfOrderness(Duration.ofSeconds(20))
    .withTimestampAssigner((click, kafkaTs) -> click.eventTimeMillis())
    .withIdleness(Duration.ofMinutes(1));          // idle partitions don't stall the watermark

OutputTag<Click> tooLate = new OutputTag<Click>("too-late") {};

SingleOutputStreamOperator<AdCount> counts = env
    .fromSource(kafkaSource, watermarks, "clicks")
    .keyBy(Click::adId)
    .window(TumblingEventTimeWindows.of(Duration.ofMinutes(1)))
    .allowedLateness(Duration.ofSeconds(30))
    .sideOutputLateData(tooLate)
    .aggregate(new CountClicks(), new EmitWindowResult());

counts.sinkTo(resultsSink);
counts.getSideOutput(tooLate).sinkTo(lateEventsSink);
```

**Spark Structured Streaming** (PySpark):

```python
from pyspark.sql import functions as F

clicks = (
    spark.readStream.format("kafka")
    .option("kafka.bootstrap.servers", "kafka:9092")
    .option("subscribe", "clicks")
    .load()
    .select(F.from_json(F.col("value").cast("string"),
                        "user_id STRING, ad_id STRING, event_time TIMESTAMP").alias("c"))
    .select("c.*")
)

counts = (
    clicks
    .withWatermark("event_time", "20 seconds")     # also the point where old state is dropped
    .groupBy(F.window("event_time", "1 minute"), "ad_id")
    .count()
)

query = (
    counts.writeStream
    .outputMode("append")                          # emit each window once, after the watermark passes it
    .option("checkpointLocation", "s3://lake/checkpoints/click_counts/")
    .trigger(processingTime="30 seconds")
    .toTable("lake.marts.click_counts")
)
```

In Spark the watermark delay does double duty: it decides when `append` mode emits a
window and when its state is dropped. `update` mode emits changed rows every
micro-batch instead.

### Watermark failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Windows never fire; output stops though the job is "healthy" | An idle source partition: the watermark is the **minimum** across inputs, and one silent partition holds it back | Idleness timeout (`withIdleness`), or fewer partitions than producers |
| Sudden flood of dropped late events | One device with a clock far in the future pushed the max event time (and the watermark) ahead | Reject or clamp timestamps far ahead of processing time |
| State grows without bound | Watermark not advancing, or no watermark on a stream aggregation/join | Always set a watermark; set state TTL |
| Results change after a backfill | Replaying months of data very fast with a tight bound | Sources that emit watermarks per partition (Flink's Kafka source does); bounded replays |

Watch the watermark advance, a late event update a window, and a too-late event go to
the side output:

<div class="lab" data-viz="flow-stream-watermark"></div>

### Triggers

Triggers decide *when* a window emits: an **early** speculative result every few
seconds (for dashboards), the **on-time** result when the watermark passes, and **late**
updates while allowed lateness lasts. Beam/Dataflow makes all three explicit; Flink
has custom triggers; Spark's output modes cover the common cases.

## 5. State and checkpoints

Anything more than a stateless `map`/`filter` keeps **state**: window contents,
running counts, the last event per user, one side of a join. State is **keyed**
(partitioned by the same key as the stream), so each parallel instance holds only its
keys, and rescaling means redistributing key groups.

| Engine | Where state lives | How it survives failure |
|---|---|---|
| Flink | Heap (small state) or **RocksDB** on local disk (large state, TB-scale in total), or disaggregated remote state in Flink 2.x | Periodic asynchronous checkpoints to S3/HDFS |
| Spark Structured Streaming | State store per partition (default HDFS-backed in memory, or RocksDB) | Checkpoint directory with offsets and state versions |
| Kafka Streams | RocksDB per task | Every change also written to a compacted **changelog topic**; a restarted instance restores from it |

### Flink checkpoints: aligned barriers

Flink's checkpointing is an asynchronous barrier snapshot, a variant of the
Chandy–Lamport algorithm:

```arch
%% caption: A Flink checkpoint. The coordinator injects barrier n into every source; each operator snapshots its state when the barrier reaches it and passes the barrier on; when every sink has acknowledged, checkpoint n is complete and recovery can restart from its offsets and state.
grid 150x105
node jm "JobManager" at 1.5,0 icon=scheduler sub="checkpoint coordinator"
node src "Kafka source" at 0,1 icon=kafka-icon sub="offsets 1042, 998"
node agg "Window operator" at 1,1 icon=worker sub="keyed state"
node join "Join operator" at 2,1 icon=worker sub="keyed state"
node sink "Sink" at 3,1 icon=table sub="2-phase commit"
node s3 "Checkpoint storage" at 1.5,2 icon=storage sub="S3: chk-n"
jm -> src : "barrier n"
src -> agg
agg -> join
join -> sink
agg ..> s3
join ..> s3
sink ..> jm : "ack"
```

1. The JobManager injects **barrier n** into each source; the source records its
   offsets.
2. The barrier flows with the data. When an operator has received barrier n on all
   its inputs, it snapshots its state (asynchronously, copying RocksDB files
   incrementally) and forwards the barrier. Records after the barrier belong to the
   next checkpoint. *Unaligned checkpoints* let barriers overtake buffered records
   under backpressure, so checkpoints still complete quickly.
3. When all sinks acknowledge, checkpoint n is complete.
4. On failure, every operator restores its state from checkpoint n and the sources
   rewind to the recorded offsets. Events after the checkpoint are **replayed**.

**Savepoints** are user-triggered, portable checkpoints used for upgrades, rescaling
and code changes: stop with a savepoint, deploy the new version, restore from it.
Give operators stable ids (`.uid("click-window")`) or state cannot be mapped to the new
job graph.

Typical settings: checkpoint every 10 s to a few minutes. Shorter intervals mean less
replay after a crash and lower end-to-end latency for transactional sinks, at the
cost of more overhead.

## 6. Delivery semantics and exactly-once

| Guarantee | Meaning | How you get it |
|---|---|---|
| At-most-once | May lose events, never duplicates | Commit offsets before processing |
| At-least-once | Never loses; may duplicate after a failure | Commit offsets after processing; replay on recovery |
| Exactly-once (effectively-once) | Effect on state and outputs as if each event were processed once | Consistent snapshots of state + offsets, **and** a sink that is transactional or idempotent |

Replays mean every real system *processes* some events more than once. Exactly-once is
about the **effect**, and it has three parts:

1. **Internal state**: snapshot state and input offsets together (Flink checkpoints,
   Spark checkpoint directory). After recovery the counts are as if nothing happened.
2. **Outputs**, one of:
   - a **transactional sink** that commits output together with the checkpoint. Flink's
     `KafkaSink` with `DeliveryGuarantee.EXACTLY_ONCE` uses Kafka transactions in a
     two-phase commit: write inside a transaction during the checkpoint interval,
     commit when the checkpoint completes. Consumers must read with
     `isolation.level=read_committed`, and results become visible only at checkpoint
     boundaries (latency ≈ checkpoint interval). Set the Kafka transaction timeout
     longer than the maximum checkpoint duration plus restart time, or transactions
     abort and data is lost;
   - an **idempotent sink**: upsert by a deterministic key (`window_start, ad_id`), so a
     replayed write overwrites the same row.
3. **Input duplicates**: a client retrying a request produces a genuinely duplicate
   event with a new offset. No engine can know. Deduplicate by a client-generated
   event id, keeping seen ids in keyed state with a TTL.

Kafka Streams gets exactly-once within Kafka by setting
`processing.guarantee=exactly_once_v2`: consumed offsets, state changelog writes and
output records are committed in one Kafka transaction.

## 7. Joins on streams

| Join | Example | How it is bounded |
|---|---|---|
| **Stream–stream, windowed / interval** | Match an ad impression with a click within 30 minutes | Both sides buffered in state for the interval; the watermark expires them |
| **Stream–table (enrichment)** | Add the user's country to each click | The table is a changelog (CDC topic) materialised into state, or a lookup against an external store with a cache |
| **Temporal (versioned) join** | Convert each order with the exchange rate valid *at the order's event time* | The table side keeps versions; the watermark decides when older versions can go |

A stream–stream join without a time bound keeps both sides forever and eventually
runs out of state. An external lookup per event (calling a database for every click)
caps throughput at the database's speed; prefer consuming the table's CDC stream into
local state, or use async I/O with a cache.

## 8. Backpressure, lag and scaling

When a sink or operator is slower than the input, buffers fill and the engine slows
upstream operators, all the way back to the source, which simply reads Kafka more
slowly. Nothing is lost (the log holds the data), but **consumer lag** grows.

What to monitor:

- **Consumer lag** in records and in time (how old is the oldest unprocessed event).
  This is the freshness SLO.
- **Watermark lag**: processing time minus the current watermark.
- **Checkpoint duration and size**; failing or slow checkpoints are the first sign of
  trouble.
- **Busy/backpressured time per operator** (Flink web UI) to find the bottleneck.
- **Late-event rate** and side-output volume.

Scaling: parallelism is capped by Kafka partitions for the source and by key
distribution after `keyBy`. A hot key (one celebrity, one bot) overloads one subtask no
matter how many you add; pre-aggregate locally or split the key, as in batch
([chapter 3](03_batch_processing_spark.md) §8,
[Partitioning, Shard Keys, and Hot Keys](../SystemDesign/building_blocks/25_partitioning_and_hot_keys.md)).
Rescaling a stateful job means taking a savepoint and restarting with new parallelism
(or letting an autoscaler do it).

## 9. Tools of the trade (2026)

| Engine | Model | Strengths | Watch out for |
|---|---|---|---|
| **Apache Flink** (2.x since 2025) | True streaming, event at a time, with DataStream API, Table API and SQL | Large keyed state, precise event-time semantics, low latency, exactly-once, savepoints | Operational depth (state sizing, checkpoints, upgrades); managed options: Confluent Cloud for Flink, Amazon Managed Service for Apache Flink, Ververica |
| **Spark Structured Streaming** | Micro-batches: each trigger processes the new data as a small batch job | Same DataFrame API and team as batch; good for streaming ETL into Delta/Iceberg | Latency is typically sub-second to seconds per batch; windows and state are less flexible than Flink's (Spark 4 adds `transformWithState` for arbitrary state) |
| **Kafka Streams** | A Java library inside your service; no cluster | Simple deployment, exactly-once within Kafka, great for per-service aggregations and joins | Kafka in and out only; scaling tied to partitions; state restore from changelogs can be slow |
| **ksqlDB** | SQL on Kafka Streams | Quick streaming SQL | Narrower feature set; check its status in your vendor's roadmap |
| **Apache Beam / Google Dataflow** | Unified batch + stream model with explicit windows, watermarks and triggers | Fully managed autoscaling on Dataflow; portable pipelines | Beam's abstraction layer; Dataflow is GCP-only |
| **Streaming databases** (RisingWave, Materialize) | Incrementally maintained materialised views in SQL | Streaming as "just SQL", queryable results | Newer; fit depends on workload |

**Precision note:** Spark Structured Streaming does not process "1-second chunks" by
default. With no trigger set, a new micro-batch starts as soon as the previous one
finishes; `trigger(processingTime="30 seconds")` fixes the interval, and
`trigger(availableNow=True)` processes everything available and stops (incremental
batch). Its old experimental "continuous processing" mode is rarely used.

## 10. Lambda vs. Kappa

| | Lambda | Kappa |
|---|---|---|
| Shape | A batch layer (complete, correct, slow) plus a speed layer (fast, approximate), merged at query time | One streaming pipeline over a replayable log; reprocessing means replaying the log through new code |
| Pros | Batch recomputation corrects streaming mistakes | One codebase and one set of semantics |
| Cons | Two implementations of the same logic that drift apart | Needs long retention and a processor that handles event time, state and late data well |
| Typical today | Billing/finance, where a nightly reconciliation is required anyway | Most new pipelines on Kafka + Flink, with results in Iceberg |

The pragmatic 2026 pattern: stream for fresh numbers, land the raw events in the
lakehouse, and let a batch job over the complete data be authoritative where money is
involved, with a reconciliation report
([Ad Click Aggregation](../SystemDesign/solutions/027_ad_click_aggregation_solution.md)).

## Common interview questions

**Event time vs. processing time: which do you aggregate by?**
Event time, for correctness and reproducibility on replay. Processing-time
aggregation is simpler but assigns delayed events to the wrong bucket and gives
different answers on replay.

**What is a watermark?**
A marker in event time saying no events older than T are expected. Windows fire when
the watermark passes their end. Usually computed as max event time seen minus a
bounded delay, taking the minimum across input partitions.

**How do you handle late data?**
Choose a bound from the measured delay distribution; use allowed lateness to update
fired windows with an upserting sink; send events beyond that to a side output for
reconciliation; monitor the late rate.

**Explain exactly-once in Flink end to end.**
Checkpoints snapshot state and source offsets consistently via barriers; on failure
both are restored and input is replayed. Outputs are either committed in a two-phase
commit tied to the checkpoint (Kafka transactions, read with `read_committed`) or
written idempotently by key. Duplicates created by producers still need deduplication
by event id.

**Your streaming job's output stopped but the job is running. What do you check?**
The watermark: an idle partition or a stalled source holds it back so windows never
fire. Then consumer lag, backpressure, and checkpoint failures.

**Why does state keep growing?**
No watermark on an aggregation or join, unbounded stream–stream join, session windows
that never close, or keys that never expire. Add watermarks, time-bounded joins and
state TTL.

**Flink vs. Spark Structured Streaming vs. Kafka Streams?**
Flink for large state, precise event time and low latency; Spark when the team and
code are already Spark and seconds of latency are fine; Kafka Streams for Kafka-to-Kafka
processing embedded in a service without a cluster.

**How do you count unique users per hour on a stream?**
Exact distinct counts need state proportional to the number of users; for large scale
use HyperLogLog sketches per window, mergeable across partitions
([Specialized Data Structures and Indexes](../SystemDesign/building_blocks/20_specialized_data_structures.md)).

**Lambda or Kappa?**
Kappa by default with a replayable log and a capable engine; keep a batch
recomputation path where correctness is contractual (billing).

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student / Intern | Intern, new learner | — | Batch vs. stream; what Kafka topics and partitions are; event time vs. processing time; tumbling windows |
| Junior | Data Engineer I | L3 | Writes a windowed aggregation in Flink SQL or Spark; knows the window types; sets a watermark; knows consumer groups and offsets |
| Mid | Data Engineer II | L4 | Chooses the watermark bound from data; handles late data (allowed lateness, side outputs, upsert sinks); configures checkpoints; monitors lag and backpressure; idempotent sinks |
| Senior | Senior Data Engineer | L5 | Explains barrier checkpoints, two-phase-commit sinks and the limits of exactly-once; designs stateful jobs (state size, TTL, RocksDB, savepoint upgrades, rescaling); debugs stalled watermarks, hot keys and state growth; stream joins |
| Staff+ | Staff / Principal Engineer | L6+ | Decides streaming vs. batch per use case against freshness and correctness SLOs; designs Kappa/Lambda architectures with reconciliation; sets platform standards (schemas, event-time contracts, replay strategy, managed vs. self-run Flink) |

## Interview checklist

- [ ] I can explain bounded vs. unbounded data and why a replayable log underpins streaming.
- [ ] I can explain event time, processing time and ingestion time, and why event time is the default.
- [ ] I can describe tumbling, hopping, session and global windows and their state costs.
- [ ] I can define a watermark precisely (event time, minimum across inputs) and compute one.
- [ ] I can list the late-data policies and their costs, and pick a watermark bound from data.
- [ ] I can explain idle-partition stalls and future-timestamp jumps.
- [ ] I can explain Flink's barrier checkpoints, savepoints and state backends.
- [ ] I can explain exactly-once end to end: state, transactional or idempotent sinks, input dedup.
- [ ] I can compare stream–stream, stream–table and temporal joins.
- [ ] I can compare Flink, Spark Structured Streaming and Kafka Streams, and Lambda vs. Kappa.

Related: [Batch and Stream Processing](../SystemDesign/building_blocks/21_batch_and_stream_processing.md),
[Messaging and Streaming](../SystemDesign/building_blocks/09_messaging_and_streaming.md),
[Streams and Consumer Groups](../NoSQL/redis/12_streams_and_consumer_groups.md) (the same consumer-group ideas in Redis Streams),
[System Design: Fraud Detection](../MLOps/08_sysdesign_fraud.md) (streaming features in a real design).
