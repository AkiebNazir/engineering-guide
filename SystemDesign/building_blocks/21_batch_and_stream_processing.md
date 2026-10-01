# Batch and Stream Processing

Serving systems answer one request at a time. Data systems answer questions about *all* the requests: how many clicks per ad per minute, which videos are trending, what should this user see tomorrow. They split into two families — **batch** (bounded data, run later, correct and complete) and **stream** (unbounded data, results as it arrives, fast but must handle disorder). Most real systems use both.

This file starts from first principles (bounded vs unbounded data, and why the raw log is the
source of truth), then measures what the concepts cost: the shuffle and a skewed key, the
watermark's speed-versus-completeness trade, delivery semantics through crashes, and row versus
column storage. It ends with backfills and a worked ad-click pipeline.

> 💡 The interview-grade question is not "Spark or Flink?" It is: how fresh must the answer be, how correct, and what happens to events that arrive late or twice?

## Foundations — Data Systems vs Serving Systems

### Bounded and unbounded data

A **bounded** dataset has an end: yesterday's logs, a table snapshot. You can read all of it, sort
it, and compute an exact answer, and if the job fails you run it again. An **unbounded** dataset
never ends: the click stream, the payments feed. You can never wait for "all of it", so every result
is about a window of it, and has to be produced while more data is still arriving, some of it out of
order.

That single difference explains the two families:

| | Batch | Stream |
|---|---|---|
| Input | Bounded (files, snapshots) | Unbounded (a log such as Kafka or Pub/Sub) |
| Latency | Minutes to hours | Milliseconds to seconds |
| Completeness | Sees everything before answering | Must decide when a window is "done enough" |
| Failure handling | Re-run the task or the job | Restore a checkpoint and replay from an offset |
| State | Recomputed each run | Kept for as long as windows and joins need it |
| Typical outputs | Daily reports, training data, billing, backfills | Dashboards, alerts, fraud checks, feature updates |

### The log is the source of truth; everything else is derived

The durable, replayable log of raw events (or the raw files in object storage) is the one thing you
must never lose. Every table, index, aggregate and model built from it is **derived data**: if the
logic was wrong, fix the code and recompute. This is why pipelines keep raw input for a long time,
make outputs **deterministic** (same input, same output) and **idempotent** (writing twice gives the
same result), and treat a backfill as a normal operation instead of an emergency.

### Vocabulary

| Term | Meaning |
|---|---|
| Partition | A slice of the data processed independently, by one task |
| Shuffle | Moving records between machines so all records with the same key meet |
| Combiner | A pre-aggregation on the map side that shrinks what the shuffle moves |
| Skew | Some keys or partitions having far more data than others |
| Event time / processing time | When it happened / when the pipeline saw it |
| Window | A finite slice of an unbounded stream (by time or by session) |
| Watermark | The pipeline's estimate that no earlier events are still coming |
| Checkpoint | A consistent snapshot of operator state plus input positions |
| Backfill | Re-running a pipeline over historical data |
| Idempotent sink | An output that gives the same result if the same records are written twice |
| Columnar format | Storing each column's values together (Parquet, ORC, BigQuery's Capacitor) |

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
| Spark | Keeps intermediate data in memory (RDDs/DataFrames), optimises whole pipelines, SQL interface. | Iterative jobs, ML feature pipelines, interactive analysis. |
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
- "How do you compute top-K trending?" → sliding windows of count-min sketches plus a heap per window, merged across partitions ([Specialized Data Structures and Indexes](20_specialized_data_structures.md)).
- "What if the pipeline is down for an hour?" → the log retains events; the job resumes from its last checkpoint and catches up; watermarks prevent a flood of false "late" data if sources report progress.
- "Why not just use the batch job?" → freshness requirement; "why not only streaming?" → correctness and reprocessing.

## The shuffle and skew, measured

A MapReduce job's cost is dominated by the shuffle, where every map output record crosses the
network to its reducer. And the job finishes only when its slowest reducer does. Here is the
click-counting job from the diagram above, run on one machine:

```python
"""A MapReduce job counting clicks per ad, run on one machine: 8 mappers,
8 reducers, 2 million clicks. Measures what the shuffle moves, and what one
very popular ad does to the reducers."""
import random
from collections import Counter, defaultdict

MAPPERS, REDUCERS, CLICKS = 8, 8, 2_000_000
rng = random.Random(4)


def clicks(hot_share):
    """Ad ids 0..9,999 with a mildly skewed popularity; ad 7 gets hot_share of all clicks."""
    weights = [1 / (i + 1) ** 0.6 for i in range(10_000)]
    ads = rng.choices(range(10_000), weights, k=CLICKS)
    return [7 if rng.random() < hot_share else a for a in ads]


def run(log, combine=False, salt=1):
    splits = [log[i::MAPPERS] for i in range(MAPPERS)]
    shuffled = [defaultdict(list) for _ in range(REDUCERS)]
    moved = 0
    for split in splits:                                  # map (+ optional combine)
        pairs = [((ad, rng.randrange(salt)), 1) for ad in split]
        if combine:
            pairs = list(Counter(k for k, _ in pairs).items())
        for key, v in pairs:                              # shuffle: hash-partition by key
            shuffled[hash(key) % REDUCERS][key].append(v)
            moved += 1
    work = [sum(len(vs) for vs in part.values()) for part in shuffled]
    partial = Counter()
    for part in shuffled:                                 # reduce
        for (ad, _), vs in part.items():
            partial[ad] += sum(vs)
    return moved, work, partial                           # (salted keys are summed again per ad)


print(f"{CLICKS:,} clicks, {MAPPERS} mappers, {REDUCERS} reducers")
print(f"  {'variant':40} {'records shuffled':>16} {'busiest reducer / mean':>23}")
for name, hot, combine, salt in [("plain", 0.0, False, 1), ("with a combiner", 0.0, True, 1),
                                 ("one ad = 30% of clicks", 0.3, False, 1),
                                 ("30% hot ad, combiner", 0.3, True, 1),
                                 ("30% hot ad, key salted 16 ways", 0.3, False, 16)]:
    log = clicks(hot)
    moved, work, counts = run(log, combine, salt)
    assert counts == Counter(log)                         # every variant gives the same answer
    print(f"  {name:40} {moved:16,} {max(work) / (sum(work) / REDUCERS):22.2f}x")
```

```text
2,000,000 clicks, 8 mappers, 8 reducers
  variant                                  records shuffled  busiest reducer / mean
  plain                                           2,000,000                   1.10x
  with a combiner                                    79,999                   1.01x
  one ad = 30% of clicks                          2,000,000                   3.11x
  30% hot ad, combiner                               79,987                   1.01x
  30% hot ad, key salted 16 ways                  2,000,000                   1.15x
```

- **A combiner shrinks the shuffle about 25×.** Summing inside each mapper first means each mapper
  sends one record per ad it saw instead of one per click. It works because a sum is associative:
  partial sums can be summed again. Counts, sums, min, max and sketches all combine; a median or a
  "list every click" doesn't.
- **One hot key makes one reducer do three times the average work.** Hash partitioning puts every
  record for ad 7 on one reducer, so the whole job waits for it. At real scale this is the classic
  "99% of tasks finished an hour ago" job.
- **Two fixes for skew.** When the operation combines, the combiner removes the skew too (1.01×
  above), because the hot key arrives as 8 partial sums instead of 600,000 records. When it doesn't
  (joins, collecting values), **salt** the key: spread `ad 7` over 16 sub-keys, process them in
  parallel, and merge the 16 partial results in a second step. Skewed joins use the same idea, and
  replicate the small side's matching row to every salt.

Spark and Dataflow do these for you in common cases (map-side combining, adaptive skew-join
handling), but you still need to recognise a skewed stage in a job's metrics: one task much slower
and bigger than the rest.

## Watermarks, measured

The watermark section above describes a trade-off; this simulation puts numbers on it. Clicks are
counted in 1-minute event-time windows. 95% of clicks arrive within seconds, 4% come from phones
that batch uploads for up to 2 minutes, and 1% come from phones that were offline for up to 3 hours:

```python
"""Clicks counted in 1-minute event-time windows. Most clicks reach the pipeline
within seconds, some phones batch uploads for up to 2 minutes, and 1% were
offline for up to 3 hours. The watermark is (latest event time seen - D);
a window fires when the watermark passes its end. What does D trade off?
(5 hours of clicks; statistics are for clicks made in the first 2 hours, so
even the 3-hour stragglers arrive while the stream is still running.)"""
import heapq, random, statistics

rng = random.Random(8)
events = []                                     # (arrival time, event time)
for i in range(5 * 3600 * 20):                  # 20 clicks/s for 5 hours
    t = i / 20
    r = rng.random()
    delay = (rng.lognormvariate(0.7, 0.8) if r < 0.95 else     # normal: ~2 s
             rng.uniform(10, 120) if r < 0.99 else             # batched uploads
             rng.uniform(600, 10_800))                          # offline for a while
    events.append((t + delay, t))
events.sort()
COUNTED = 2 * 3600                              # measure clicks made before this


def run(D, lateness=0.0):
    wm, seen = -1e9, set()                      # seen: windows that have state
    unfired, held, fired = [], [], set()        # heaps of window ids
    n = late = corrections = dropped = most_open = 0
    fire_delay = []
    for arrival, t in events:
        w = int(t // 60)
        measured = t < COUNTED
        n += measured
        if w in fired:
            late += measured
            if (w + 1) * 60 + lateness > wm:
                corrections += measured          # state still kept: emit an updated count
            else:
                dropped += measured
        elif w not in seen:
            seen.add(w)
            heapq.heappush(unfired, w)
        wm = max(wm, t - D)
        while unfired and (unfired[0] + 1) * 60 <= wm:
            ww = heapq.heappop(unfired)
            fired.add(ww)
            heapq.heappush(held, ww)
            if ww * 60 < COUNTED:
                fire_delay.append(arrival - (ww + 1) * 60)
        while held and (held[0] + 1) * 60 + lateness <= wm:
            heapq.heappop(held)                  # grace period over: state discarded
        most_open = max(most_open, len(unfired) + len(held))
    return late / n, statistics.median(fire_delay), corrections, dropped / n, most_open


print(f"  {'D':>6} {'late events':>11} {'result ready after window end':>30}")
for D in (0, 5, 30, 120, 600):
    late, delay, *_ = run(D)
    print(f"  {D:>4} s {late:10.2%} {delay:28.1f} s")

print("\nD = 30 s, keeping each window's state for extra 'allowed lateness'")
print(f"  {'lateness':>9} {'late updates emitted':>21} {'dropped':>8} {'windows kept in state':>22}")
for L in (0, 600, 3600, 3 * 3600):
    _, _, corr, dropped, most_open = run(30, L)
    print(f"  {L // 60:>6} min {corr:21,} {dropped:8.2%} {most_open:22}")
```

```text
       D late events  result ready after window end
     0 s      7.32%                          0.9 s
     5 s      4.60%                          5.8 s
    30 s      3.23%                         30.8 s
   120 s      0.99%                        120.9 s
   600 s      0.99%                        600.9 s

D = 30 s, keeping each window's state for extra 'allowed lateness'
   lateness  late updates emitted  dropped  windows kept in state
       0 min                     0    3.23%                      2
      10 min                 3,234    0.98%                     12
      60 min                 3,646    0.70%                     62
     180 min                 4,649    0.00%                    182
```

- **The watermark delay D is a direct trade between speed and completeness.** Firing as soon as
  possible (D = 0) makes over 7% of clicks late. Waiting 2 minutes catches the batched uploads, and
  every result is 2 minutes later. Waiting 10 minutes gains nothing more: the remaining 1% are the
  offline phones, which no reasonable watermark waits for.
- **Allowed lateness handles the tail without delaying everyone.** Fire on time with D = 30 s, then
  keep each window's state for a while and emit updated counts as stragglers arrive. Keeping state
  for 3 hours drops nothing, but holds 182 windows per key in state instead of 2. With millions of
  keys, that state is the real cost, which is why grace periods are chosen per use case.
- **The right settings come from the use case.** A live dashboard fires fast and ignores the
  stragglers. Budget pacing for ads fires fast and applies late updates. Billing waits for a daily
  batch job over the complete raw log, which catches even the phones that were offline for a day.

Always count late and dropped events as a metric. A sudden rise usually means an upstream problem
(a stuck producer, a client release that batches differently), not a watermark setting.

## Delivery semantics, measured

What "exactly-once" actually requires, shown by counting clicks through crashes. The log has
100,000 events; 2% are clients' retries of the same click (same event ID); the consumer crashes 12
times and restarts from its last saved progress:

```python
"""A consumer counts clicks per ad from a log of 100,000 events. 2% of clicks
were sent twice by the client (a retry after a timeout: same event id). The
consumer crashes 12 times at random points and restarts from its last saved
position. Which strategies end with the true count?"""
import random

rng = random.Random(21)
log, eid = [], 0
while len(log) < 100_000:
    eid += 1
    e = (eid, rng.randrange(50))                 # (event id, ad id)
    log.append(e)
    if rng.random() < 0.02:
        log.append(e)                            # the client's retry
TRUE = len({e for e in log})
crashes = set(rng.sample(range(len(log)), 12))
EVERY = 1_000                                    # save progress every 1,000 events


def consume(strategy):
    sink = {}                                    # the external output: counts per ad
    saved = {"offset": 0, "state": {}, "seen": set()}
    pos, crashed = 0, set()
    state, seen = {}, set()
    while pos < len(log):
        if pos in crashes and pos not in crashed:  # crash: in-memory work is lost
            crashed.add(pos)
            pos = saved["offset"]
            state, seen = dict(saved["state"]), set(saved["seen"])
            continue
        eid, ad = log[pos]
        if strategy == "commit offset first":        # at-most-once
            if pos % EVERY == 0:
                saved["offset"] = pos + EVERY          # claim the batch before doing it
            sink[ad] = sink.get(ad, 0) + 1
        elif strategy == "write, then commit offset":  # at-least-once
            sink[ad] = sink.get(ad, 0) + 1
        else:                                          # checkpoint state + offset together
            if strategy.endswith("dedup by id") and eid in seen:
                pos += 1
                continue
            seen.add(eid)
            state[ad] = state.get(ad, 0) + 1
        pos += 1
        if pos % EVERY == 0 and strategy != "commit offset first":
            saved = {"offset": pos, "state": dict(state), "seen": set(seen)}
            if strategy.startswith("checkpoint"):
                sink = dict(state)                     # output committed with the checkpoint
    if strategy.startswith("checkpoint"):
        sink = dict(state)
    return sum(sink.values())


print(f"{len(log):,} events, {TRUE:,} real clicks, 12 crashes\n")
for s in ("commit offset first", "write, then commit offset",
          "checkpoint state + offset", "checkpoint state + offset, dedup by id"):
    got = consume(s)
    print(f"  {s:40} counted {got:7,}  error {got - TRUE:+6,}")
```

```text
100,000 events, 98,069 real clicks, 12 crashes

  commit offset first                      counted  94,016  error -4,053
  write, then commit offset                counted 106,016  error +7,947
  checkpoint state + offset                counted 100,000  error +1,931
  checkpoint state + offset, dedup by id   counted  98,069  error     +0
```

- **Commit first (at-most-once) loses data.** The consumer claims each batch of 1,000 before
  processing it, so a crash loses the rest of that batch.
- **Write first (at-least-once) double-counts.** The sink was updated for events after the last
  saved offset, and the restarted consumer replays them. That is the default behaviour of most
  consumers, and why sinks must be idempotent.
- **Checkpointing state and offset together gets the pipeline right**, because the replayed events
  update a state that was restored to the same point. But it still counts the client's retries: to
  the pipeline they are different events.
- **Only deduplication by the client's event ID gives the true count.** That is the gap the warning
  above describes: exactly-once processing is a property of the pipeline, and duplicates created
  before the pipeline are your job. In production, the set of seen IDs is kept per key with an
  expiry (a day, say), not forever.

## Row and column storage, measured

Analytical queries read a few columns of very many rows. Row-oriented storage has to read every
column of every row; column-oriented storage reads only the columns the query names, and each
column compresses well because its values are similar:

```python
"""Row vs column layout for analytics: 1,000,000 orders with 8 columns. The
query is SELECT sum(amount) WHERE country = 'DE'. How many bytes must be read?"""
import random, struct, zlib

rng = random.Random(6)
N = 1_000_000
countries = ["US", "DE", "IN", "BR", "JP", "FR", "GB", "NG"]
cols = {
    "order_id":   [struct.pack("<q", i) for i in range(N)],
    "user_id":    [struct.pack("<q", rng.randrange(10**8)) for _ in range(N)],
    "created":    [struct.pack("<q", 1_790_000_000 + i * 3) for i in range(N)],
    "country":    [rng.choice(countries).encode() for _ in range(N)],
    "status":     [rng.choice([b"paid", b"paid", b"paid", b"refunded"]).ljust(8) for _ in range(N)],
    "amount":     [struct.pack("<i", rng.randrange(100, 20_000)) for _ in range(N)],
    "currency":   [b"EUR" for _ in range(N)],
    "sku":        [f"SKU-{rng.randrange(5000):05}".encode() for _ in range(N)],
}
row_bytes = sum(len(v[0]) for v in cols.values())
rows_total = N * row_bytes
rows_z = len(zlib.compress(b"".join(b"".join(c[i] for c in cols.values()) for i in range(0, N, 1)), 6))

print(f"{N:,} rows x {row_bytes} bytes = {rows_total / 1e6:.0f} MB raw\n")
print(f"  {'column':10} {'raw MB':>7} {'compressed MB':>14} {'ratio':>6}")
sizes = {}
for name, vals in cols.items():
    raw = b"".join(vals)
    z = len(zlib.compress(raw, 6))
    sizes[name] = z
    print(f"  {name:10} {len(raw) / 1e6:7.1f} {z / 1e6:14.2f} {len(raw) / z:6.1f}x")

need = sizes["country"] + sizes["amount"]
print(f"\nBytes read for sum(amount) WHERE country = 'DE':")
print(f"  row store, uncompressed      {rows_total / 1e6:7.1f} MB")
print(f"  row store, compressed        {rows_z / 1e6:7.1f} MB")
print(f"  column store, 2 of 8 columns {need / 1e6:7.2f} MB  ({rows_total / need:.0f}x less than raw rows)")

de = sum(struct.unpack("<i", a)[0] for c, a in zip(cols["country"], cols["amount"]) if c == b"DE")
print(f"\n  answer: {de:,} (same whichever layout computed it)")
```

```text
1,000,000 rows x 50 bytes = 50 MB raw

  column      raw MB  compressed MB  ratio
  order_id       8.0           1.51    5.3x
  user_id        8.0           4.28    1.9x
  created        8.0           1.53    5.2x
  country        2.0           0.48    4.2x
  status         8.0           0.22   36.1x
  amount         4.0           2.45    1.6x
  currency       3.0           0.00 1022.5x
  sku            9.0           2.25    4.0x

Bytes read for sum(amount) WHERE country = 'DE':
  row store, uncompressed         50.0 MB
  row store, compressed           16.7 MB
  column store, 2 of 8 columns    2.93 MB  (17x less than raw rows)

  answer: 1,250,158,448 (same whichever layout computed it)
```

- **Reading 2 columns of 8 cut the bytes read 17×** compared with the raw rows, and more than 5×
  compared with compressing whole rows.
- **Compression depends on the column.** A constant column (`currency`) shrinks to almost nothing,
  low-cardinality columns (`status`, `country`) shrink a lot, and random IDs and amounts barely
  shrink. Real columnar formats (Parquet, ORC) do much better than the general-purpose compression
  used here, with dictionary encoding (countries as small integers), run-length encoding (runs of the
  same value) and delta encoding (sequential IDs and timestamps).
- **Columnar engines skip data too.** Files store per-block min and max values, so a filter on
  `created` or a sorted column skips whole blocks without reading them. Partitioning tables by date
  and clustering by common filters are the main levers for query cost.

This is why the OLTP table above (row-oriented, fast point lookups) and the warehouse
(column-oriented, fast scans) are different systems fed by change data capture, not one database
asked to do both.

## Backfills and reprocessing

Every pipeline eventually needs to recompute history: a bug fix, a new metric, a new feature for a
model. Plan for it from the start:

- **Keep raw input** long enough to recompute what matters (object storage is cheap; see
  [Object Storage](08_object_storage.md)).
- **Make outputs partitioned and overwritable** (by date, say), so a backfill replaces
  `date=2026-09-01` atomically instead of appending duplicates.
- **Keep code deterministic**: no "now()" inside the transform, no dependence on processing order;
  use event time and inputs only.
- **Run backfills separately from the live pipeline** (a batch job over files, or a second stream job
  reading from an old offset) with its own resource limits, so recomputing a year doesn't delay
  today's results.
- **Version the outputs** during a migration and switch readers only after validation.

## A worked design: ad-click aggregation

"Count clicks per ad per minute for dashboards and billing; 1 million clicks a second at peak."

| Quantity | Estimate | Consequence |
|---|---|---|
| Ingest | 1M/s × ~200 bytes ≈ 200 MB/s | A partitioned log; ~100 partitions for parallelism and headroom |
| Keys | ~10M active ads × 1-minute windows | State per (ad, minute), kept for the grace period |
| Output | ~10M ads × 1,440 minutes/day at most, far fewer active | An OLAP store for dashboards; daily files for billing |

1. **Ingest.** Click servers validate, assign an event ID, and write to the log partitioned by
   `ad_id`. Raw events also land in object storage, hourly, for batch and backfills.
2. **Stream path.** A stream job deduplicates by event ID (keyed state, 24-hour expiry), aggregates
   in 1-minute event-time windows with a short watermark delay, and applies late updates for an
   hour. It writes to the OLAP store with an idempotent upsert keyed by `(ad_id, minute)`, so
   replays after failures overwrite instead of adding.
3. **Hot ads.** A few ads get a large share of clicks. Pre-aggregate on the click servers for a
   second, or salt the key and merge, so no single partition becomes the bottleneck.
4. **Batch path.** A daily job over the complete raw events, with the same deduplication logic,
   produces the billing numbers. A reconciliation report compares it with the stream totals; a
   difference over a small threshold pages someone.
5. **Fraud and bots.** Filtering rules and models run in the stream for fast budget protection
   and again in batch, with more context, before billing.

## What each level should know

| Topic | L4 · Mid | L5 · Senior | L6+ · Staff |
|---|---|---|---|
| **Batch** | Writes MapReduce/Spark jobs | Explains the shuffle, combiners and skew, and fixes a skewed stage | Designs the data platform: storage formats, partitioning, orchestration, cost |
| **Stream** | Consumes from a log | Designs event-time windows, watermarks, allowed lateness and state size | Chooses stream vs batch vs both for each product need, with correctness guarantees |
| **Correctness** | Knows retries cause duplicates | Explains at-least-once vs checkpointed exactly-once and designs dedup and idempotent sinks | Designs reconciliation between stream and batch; owns data-quality SLOs |
| **Storage** | Knows OLTP vs OLAP | Explains columnar formats, compression and partition pruning | Designs lakehouse and warehouse layouts and the CDC paths feeding them |

## Interview checklist

- [ ] I can explain bounded vs unbounded data and when to use batch, stream, or both.
- [ ] I can explain the shuffle, what a combiner saves, and how to handle a skewed key.
- [ ] I can explain event time vs processing time, windows, and what a watermark trades off.
- [ ] I can design allowed lateness and say what it costs in state.
- [ ] I can explain at-most-once, at-least-once and checkpointed exactly-once, and why dedup by event ID is still needed.
- [ ] I can explain why columnar storage makes analytics cheaper, with numbers.
- [ ] I can plan backfills: raw retention, deterministic code, overwritable partitions.
- [ ] I can design an ad-click aggregation pipeline end to end with a reconciliation path.

## Related building blocks

- [Messaging and Streaming](09_messaging_and_streaming.md)
- [Specialized Data Structures and Indexes](20_specialized_data_structures.md)
- [The Papers Behind Google-Scale Systems](24_google_papers.md)
- [Databases: Source of Truth](05_databases.md)
- [Object Storage](08_object_storage.md)
