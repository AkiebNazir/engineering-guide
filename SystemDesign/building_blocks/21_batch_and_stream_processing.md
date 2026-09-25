# Batch and Stream Processing

Serving systems answer one request at a time. Data systems answer questions about *all* the requests: how many clicks per ad per minute, which videos are trending, what should this user see tomorrow. They split into two families — **batch** (bounded data, run later, correct and complete) and **stream** (unbounded data, results as it arrives, fast but must handle disorder). Most real systems use both.

> 💡 The interview-grade question is not "Spark or Flink?" It is: how fresh must the answer be, how correct, and what happens to events that arrive late or twice?

## Batch processing: MapReduce and its successors

**MapReduce** (Google, 2004) made large-scale batch processing boring in the best way: you write a `map` function (record → key/value pairs) and a `reduce` function (key + all its values → output), and the framework handles partitioning, shuffling, sorting, retries, and stragglers across thousands of machines.

```arch
%% caption: Counting clicks per ad. The shuffle moves every value for the same key to the same reducer.
group input "Input splits" color=slate icon=file
node s1 "click log part 1" at 0,0 in input icon=logs
node s2 "click log part 2" at 1,0 in input icon=logs
node s3 "click log part 3" at 2,0 in input icon=logs
node m1 "map" at 0,1 color=orange sub="emit ad_id, 1"
node m2 "map" at 1,1 color=orange sub="emit ad_id, 1"
node m3 "map" at 2,1 color=orange sub="emit ad_id, 1"
node sh "shuffle + sort" at 1,2 color=amber icon=sort shape=card sub="by ad_id"
node r1 "reduce: sum" at 0.5,3 color=purple sub="ads A–M"
node r2 "reduce: sum" at 1.5,3 color=purple sub="ads N–Z"
node out "counts per ad" at 1,4 icon=db
s1 -> m1
s2 -> m2
s3 -> m3
m1:B -> sh:T
m2 -> sh
m3:B -> sh:T
sh:B -> r1:T
sh:B -> r2:T
r1:B -> out:T
r2:B -> out:T
```

Why it works: map tasks are embarrassingly parallel and restartable; outputs are written to a distributed file system so a failed task simply re-runs; and moving computation to where the data lives (data locality) avoids shipping terabytes over the network.

| Engine | What it improved | When to name it |
|---|---|---|
| MapReduce / Hadoop | The original model; disk between every stage. | Historical context, very large simple jobs. |
| Spark | Keeps intermediate data in memory (RDDs/DataFrames), optimises whole pipelines, SQL interface. | Iterative jobs, <abbr title="Machine Learning">ML</abbr> feature pipelines, interactive analysis. |
| Dataflow / Apache Beam | One programming model for batch *and* streaming, with windows and triggers. | "Same logic for backfill and real time." |
| BigQuery / Dremel | Columnar storage plus massively parallel SQL over it; no cluster to manage. | Ad-hoc analytics over petabytes. |

Batch is the **source of correctness**: it reads complete, deduplicated data and can be re-run from raw logs when logic changes.

## Stream processing

A stream processor (Flink, Dataflow, Kafka Streams, Spark Structured Streaming) runs continuously over an unbounded log such as Kafka or Pub/Sub and maintains state — counts, joins, aggregates — updated as each event arrives. The hard parts are all about **time**.

### Event time vs processing time

- **Event time**: when the thing happened (the click on the user's phone).
- **Processing time**: when the pipeline saw it.

They differ by network delays, retries, batching, and offline devices that sync hours later. Aggregating by processing time is easy but wrong: a phone that reconnects after a flight dumps yesterday's clicks into today's counts. Aggregating by event time is right, but then you need to decide *when a window is finished*.

## Windows

| Window | Definition | Example |
|---|---|---|
| Tumbling | Fixed size, non-overlapping: `[0,60)`, `[60,120)`… | Clicks per ad per minute for billing. |
| Sliding (hopping) | Fixed size, overlapping, advancing by a slide: size 10 min every 1 min. | "Trending in the last 10 minutes", updated each minute. |
| Session | Per key, closes after a gap of inactivity. | A user's viewing session ends after 30 minutes idle. |
| Global | One window with custom triggers. | Running totals with periodic emits. |

Tumbling and sliding windows are cut on a fixed clock, so every key shares the same boundaries. **Session windows** do not: each key gets its own window that stays open while events keep arriving and closes after a configured gap of inactivity, so two events 29 minutes apart join one session and the next one, 31 minutes later, starts a new one. That makes them the right shape for "how long was this user active" questions, and the awkward one for state size — a key with a steady trickle of events never closes its window, so production pipelines pair the gap with a maximum session duration.

## Watermarks, triggers and late data

A **watermark** is the pipeline's assertion that "no more events with event time earlier than *T* are expected". When the watermark passes the end of a window, the window **fires** and emits its result. Watermarks are typically computed from the maximum event time seen minus an allowed delay, or from source-provided progress.

The fundamental trade-off:

- A **tight** watermark fires quickly but classifies more stragglers as late.
- A **loose** watermark waits longer, which makes results more complete but slower.

For events that arrive after their window fired, you choose:

1. **Drop** them (and count how many — that metric matters).
2. **Allowed lateness**: keep window state for a grace period and emit an updated result (a *retraction* or *correction*) when a late event arrives.
3. **Side output**: route very late events to a separate path for the batch job to reconcile.

**Triggers** control *when* results are emitted: early speculative results every few seconds, an on-time result at the watermark, and late updates afterwards.

## Exactly-once, precisely

Every distributed pipeline delivers at least once somewhere. "Exactly-once" means the *effect* on state and outputs is as if each event were processed once:

- **Internal state**: stream processors checkpoint operator state and source offsets together (Flink's asynchronous barrier snapshots); on failure they restore both and replay from the checkpointed offset.
- **Outputs**: either a transactional sink (commit the output with the checkpoint), or an **idempotent** sink keyed by a deterministic ID so replays overwrite rather than add.
- **Input duplicates** (the client retried the click): deduplicate by event ID within a bounded window, often with a keyed state store or Bloom filter.

> ⚠️ Exactly-once inside the processor does not stop a client from sending the same click twice. Deduplication by a client-generated event ID is still your job.

## Lambda vs kappa architectures

| | Lambda | Kappa |
|---|---|---|
| Shape | A batch layer (complete, correct, slow) plus a speed layer (fast, approximate), merged at query time. | One streaming pipeline over a replayable log; reprocessing = replay the log with new code. |
| Pros | Batch recomputation fixes streaming mistakes; each layer uses the best tool. | One codebase, one set of semantics. |
| Cons | Two implementations of the same logic that drift apart. | Needs long log retention and a processor that handles windows, late data, and state well. |
| Typical today | Billing and finance, where a nightly reconciliation is required anyway. | Most new analytics pipelines built on Kafka/Pub/Sub + Flink/Dataflow. |

A common pragmatic hybrid for ad-click or metrics systems: stream for real-time dashboards and budget pacing, plus a daily batch job over the raw logs whose output is authoritative for billing, with a reconciliation report of the differences.

## OLTP vs analytics storage

| | OLTP (serving) | OLAP (analytics) |
|---|---|---|
| Queries | Point lookups and small updates by key | Scans and aggregates over billions of rows |
| Layout | Row-oriented | Column-oriented (read only needed columns, compress well) |
| Examples | PostgreSQL, Spanner, Bigtable | BigQuery, Snowflake, ClickHouse, Druid |
| Freshness | Immediate | Seconds (streaming ingest) to hours (batch load) |

Do not run heavy analytics on the serving database. Stream changes out with change data capture (CDC) or the outbox pattern into the warehouse.

## Interview angles

- "How do you count ad clicks per minute accurately?" → event-time tumbling windows, watermark with allowed lateness, dedup by click ID, idempotent sink, batch reconciliation for billing.
- "How do you compute top-K trending?" → sliding windows of count-min sketches plus a heap per window, merged across partitions ([20_specialized_data_structures.md](20_specialized_data_structures.md)).
- "What if the pipeline is down for an hour?" → the log retains events; the job resumes from its last checkpoint and catches up; watermarks prevent a flood of false "late" data if sources report progress.
- "Why not just use the batch job?" → freshness requirement; "why not only streaming?" → correctness and reprocessing.

## Related building blocks

- [09_messaging_and_streaming.md](09_messaging_and_streaming.md)
- [20_specialized_data_structures.md](20_specialized_data_structures.md)
- [24_google_papers.md](24_google_papers.md)
