# Feature Stores and Data Leakage

Most production ML bugs are not in the model. They are in the features: a value computed
one way for training and another way at serving time, or a training row that quietly used
information from the future. This chapter explains what a feature is, why teams build a
**feature store**, how its offline and online halves work, and how **point-in-time
correctness** prevents leakage. It includes a runnable as-of join, a Feast setup, a
streaming-feature design and a live flow that follows one feature through both paths.

## Foundations — What is a feature store, and why would I need one?

### Features, in plain terms

A **feature** is one input to a model, one measurable fact about the thing you are
predicting for. For a model that predicts whether a user will buy something in this
session, features might be:

| Feature | Kind | Where it comes from |
|---|---|---|
| `user_country` | Static attribute | User table |
| `orders_last_90d` | Batch aggregate | Warehouse SQL, recomputed daily |
| `clicks_last_10m` | Streaming aggregate | Click events, updated within seconds |
| `cart_value_now` | Request-time | The request itself |
| `user_embedding` | Learned | A model trained elsewhere, refreshed daily |

An **entity** is the thing a feature describes (a user, an item, a merchant, a
user–item pair), and its **join key** is how you look it up (`user_id`).

### Two consumers, one definition

The same features are needed in two very different places:

1. **Training (offline)** needs *millions of historical rows*, each with the feature values
   *as they were* at that row's moment in the past. Throughput matters; latency does not.
2. **Serving (online)** needs *one row, right now*, for the user who just opened the app,
   in a few milliseconds.

Without shared infrastructure, those two get built separately. A data scientist writes a
SQL query against the warehouse to compute `clicks_last_7d` for training. A backend
engineer writes Java that reads an event stream or Redis to compute `clicks_last_7d` at
request time. If the two disagree even slightly (one counts bot clicks, one excludes
today, one uses UTC and the other local time), the model is fed inputs in production that
differ from what it learned on. That mismatch is **training–serving skew**, and it is the
most common reason a model that looked great offline does nothing online.

### What a feature store is

A **feature store** is a system that lets you define a feature once and then:

- **computes** it (batch, streaming or at request time) from that one definition;
- **stores its history** in an *offline store* (warehouse or lakehouse tables) for training;
- **stores its latest value** in an *online store* (a low-latency key-value store) for serving;
- **joins it correctly in time** when building training sets (point-in-time joins);
- **catalogues it**, with owner, description, freshness and lineage, so other teams reuse it.

An everyday analogy: a bank keeps a full **ledger** of every transaction (the offline
store) and a **current balance** per account that an ATM can read instantly (the online
store). Both are derived from the same transactions, so they agree. If the ATM computed
balances with its own rules, they would drift apart.

```arch
%% caption: One feature definition feeds two stores: the offline store keeps every historical value for training, the online store keeps only the latest value per key for serving.
grid 150x110
node raw "Raw data" at 1,0 icon=db sub="events, tables"
node defn "Feature definitions" at 1,1 icon=code sub="one source of truth"
group off "Offline path" color=slate icon=archive
node batch "Batch job" at 0,2 in off icon=workflow sub="compute + backfill"
node offs "Offline store" at 0,3 in off icon=table sub="full history"
node train "Training" at 0,4 in off icon=cpu sub="point-in-time join"
group on "Online path" color=green icon=speed
node stream "Stream job" at 2,2 in on icon=stream sub="fresh windows"
node ons "Online store" at 2,3 in on icon=kv sub="latest per key"
node serve "Model server" at 2,4 in on icon=model sub="one row, now"
raw -> defn
defn -> batch
defn -> stream
batch -> offs -> train
stream -> ons -> serve
offs ..> ons : "materialize"
```

### Vocabulary

| Term | Meaning |
|---|---|
| **Offline store** | Historical feature values with timestamps, in BigQuery, Snowflake, Redshift, Delta/Iceberg tables or Parquet files |
| **Online store** | Latest value per entity key in Redis, DynamoDB, Bigtable, Cassandra/ScyllaDB or similar |
| **Materialization** | Copying the latest values from the offline store (or a stream) into the online store |
| **Point-in-time (as-of) join** | For each training row at time *t*, take each feature's latest value available *before t* |
| **Entity dataframe** | The list of (entity key, timestamp, label) rows you want features for |
| **TTL** | How old a feature value may be before it counts as missing |
| **Feature view** | A named group of features that share an entity, a source and a schedule |
| **On-demand feature** | Computed at request time from request data, possibly combined with stored features |
| **Freshness** | How far behind real time the served value is |

## 1. Training–serving skew, precisely

Skew is any difference between the feature values a model trained on and the values it
receives in production for the same situation. It comes in three flavours:

| Kind | Example | How it shows up |
|---|---|---|
| **Logic skew** | Training SQL counts clicks including bots; the serving code filters bots | Served values systematically lower; model under-predicts |
| **Data / freshness skew** | Training used values computed after the day was complete; serving reads a stream that lags 20 minutes, or a daily batch that is 30 hours old | Model trained on fresher information than it gets live |
| **Version skew** | Training used vocabulary v12 for a categorical feature; serving still loads v11 | New categories map to "unknown"; slice quality drops |

**Detecting it.** Log the exact feature vector the model received for a sample of
requests (a *feature log*), then recompute the same features offline for the same keys and
timestamps and compare them. Any feature whose values disagree for more than a small
fraction of rows is skewed. Many teams run this comparison daily as a monitor.

**Preventing it.** Use one definition for both paths (the feature store's job), or
**log-and-wait**: build training data from the features actually served (§6), which
removes skew by construction at the cost of waiting for new features to accumulate.

## 2. Offline store vs online store

| | Offline store | Online store |
|---|---|---|
| Holds | Every value over time, with timestamps | Latest value per key (sometimes a few versions) |
| Read pattern | Large scans and joins for millions of rows | Point lookups and small multi-gets |
| Latency target | Minutes are fine | Single-digit ms at p99 (≈) |
| Typical tech | BigQuery, Snowflake, Redshift, Delta/Iceberg on S3/GCS, Parquet | Redis, DynamoDB, Bigtable, Cassandra/ScyllaDB, Aerospike |
| Size | Grows with history (TBs to PBs) | Entities × features (GBs to low TBs) |
| Written by | Batch jobs, stream sinks, backfills | Materialization jobs, stream jobs (push) |
| Main risk | Wrong join (leakage), slow backfills | Staleness, hot keys, missing keys |

**Online store sizing, back of the envelope.** 100M users × 50 numeric features × 8 bytes
≈ 40 GB of raw values. Key overhead, serialisation and replication multiply that by
roughly 2–4× (≈ depends on the store), so plan for about 100–150 GB of memory, which is a
small sharded Redis or a DynamoDB table. The read side matters more: a ranking request
that fetches features for one user and 500 candidate items is 1 + 500 lookups, so item
features are usually cached inside the ranking service ([System Design: Recommendation Systems](06_sysdesign_recsys.md)).

## 3. Point-in-time correctness and data leakage

**Data leakage** is training with information the model will not have when it makes a
real prediction. It produces models that look excellent offline and fail in production,
and it is hard to notice because every metric you compute offline is inflated in the
same way.

### The classic example

You predict whether a user will churn next month. The training query joins a `labels`
table (user, date, churned?) with the `users` table. But `users` stores the *current*
state: a user who cancelled in March 2026 now has `is_unsubscribed = true` and
`support_tickets = 7`. If you join today's `users` row to a label from January 2026, the
model learns that `is_unsubscribed` perfectly predicts churn. Offline AUC is near 1.0. In
production, every user being scored is still subscribed at prediction time, so the
feature is useless and the model collapses.

### The rule

For a training row whose prediction moment is *t*, every feature must use only data that
**was available to the production system before *t***. "Available" includes pipeline lag:
a daily aggregate computed at 02:00 for yesterday is available from 02:00, not from
midnight.

### An as-of join, runnable

```python
# pit_join.py  (needs pandas)
import pandas as pd

# Labels: one row per prediction moment we want to learn from.
labels = pd.DataFrame({
    "user_id": [1, 1, 2],
    "event_timestamp": pd.to_datetime(["2026-03-01 12:00", "2026-04-01 12:00", "2026-03-15 09:00"]),
    "churned_next_30d": [0, 1, 0],
})

# Feature history: every time the daily job recomputed `sessions_7d`, with the time
# the value became available to production.
features = pd.DataFrame({
    "user_id": [1, 1, 1, 2, 2],
    "feature_timestamp": pd.to_datetime(["2026-02-28 02:00", "2026-03-31 02:00",
                                         "2026-04-02 02:00", "2026-03-14 02:00",
                                         "2026-03-16 02:00"]),
    "sessions_7d": [14, 3, 0, 9, 11],
})

# WRONG: join the latest value per user (what "SELECT * FROM features_current" gives you).
latest = features.sort_values("feature_timestamp").groupby("user_id").tail(1)
leaky = labels.merge(latest[["user_id", "sessions_7d"]], on="user_id")

# RIGHT: for each label row, the most recent value available strictly before the label time.
pit = pd.merge_asof(
    labels.sort_values("event_timestamp"),
    features.sort_values("feature_timestamp"),
    left_on="event_timestamp", right_on="feature_timestamp",
    by="user_id", direction="backward", allow_exact_matches=False,
    tolerance=pd.Timedelta(days=2),          # older than this counts as missing (a TTL)
)

print("leaky:\n", leaky[["user_id", "event_timestamp", "sessions_7d", "churned_next_30d"]].to_string(index=False))
print("point-in-time:\n", pit[["user_id", "event_timestamp", "feature_timestamp", "sessions_7d", "churned_next_30d"]].to_string(index=False))
```

Output:

```text
leaky:
  user_id     event_timestamp  sessions_7d  churned_next_30d
       1 2026-03-01 12:00:00            0                 0
       1 2026-04-01 12:00:00            0                 1
       2 2026-03-15 09:00:00           11                 0
point-in-time:
  user_id     event_timestamp   feature_timestamp  sessions_7d  churned_next_30d
       1 2026-03-01 12:00:00 2026-02-28 02:00:00           14                 0
       2 2026-03-15 09:00:00 2026-03-14 02:00:00            9                 0
       1 2026-04-01 12:00:00 2026-03-31 02:00:00            3                 1
```

The leaky join gives user 1 a `sessions_7d` of 0 on *both* rows, a value computed on
2 April after the user had already churned. The model would learn "0 sessions → churn" from
a value it could never have seen in time. The as-of join gives 14 (engaged, did not churn)
and 3 (fading, did churn), which is what production would have seen.

The same join in SQL, for warehouses without a native `ASOF JOIN`:

```sql
SELECT l.user_id, l.event_timestamp, l.churned_next_30d, f.sessions_7d
FROM labels AS l
LEFT JOIN LATERAL (
  SELECT sessions_7d
  FROM feature_history AS f
  WHERE f.user_id = l.user_id
    AND f.feature_timestamp <  l.event_timestamp
    AND f.feature_timestamp >= l.event_timestamp - INTERVAL '2 days'   -- TTL
  ORDER BY f.feature_timestamp DESC
  LIMIT 1
) AS f ON TRUE;
```

That is PostgreSQL syntax. DuckDB, Snowflake and ClickHouse have `ASOF JOIN`; BigQuery and
Spark usually use a window function (`ROW_NUMBER() OVER (PARTITION BY label_id ORDER BY
feature_timestamp DESC)`) after a range join. At scale the join is the expensive part of
building a training set, and feature stores implement it for you.

### Other kinds of leakage

| Kind | Example | Guard |
|---|---|---|
| **Target leakage** | A fraud model uses `chargeback_filed`, which is only set after the fraud is known | Review every feature's availability time; ban post-outcome columns |
| **Temporal split leakage** | Random train/test split on time-series data, so the model trains on next week to predict last week | Split by time: train on the past, validate on a later window |
| **Entity leakage** | The same user's sessions appear in both train and test, so the model memorises users | Group split by entity where generalising to new entities matters |
| **Preprocessing leakage** | Normalisation statistics or target encodings computed on the full dataset, including test | Fit preprocessing on the training fold only |
| **Duplicate leakage** | Near-duplicate items (reposts, retries) straddle the split | Deduplicate before splitting |

A feature with suspiciously high importance, or an offline metric that is too good
(AUC 0.99 on a hard problem), is the usual first clue.

<div class="lab" data-viz="flow-feature-store"></div>

## 4. A feature store in practice: Feast

**Feast** is the most widely used open-source feature store. It is a thin layer: it
keeps a registry of definitions, generates point-in-time joins against your offline store,
and materializes into your online store. It does not run your transformation cluster for
you (batch transformations are your Spark/dbt/SQL jobs; streaming ones push into Feast).

Repository layout:

```text
feature_repo/
  feature_store.yaml
  features.py
```

`feature_store.yaml`, with Redis as the online store and local Parquet as the offline store
(swap `offline_store.type` for `bigquery`, `snowflake.offline`, `redshift` or `spark` in
production):

```yaml
project: shop
registry: data/registry.db
provider: local
offline_store:
  type: file
online_store:
  type: redis
  connection_string: "redis:6379"
entity_key_serialization_version: 3
```

`features.py`:

```python
from datetime import timedelta

from feast import Entity, FeatureView, Field, FileSource, PushSource
from feast.types import Float32, Int64

user = Entity(name="user", join_keys=["user_id"], description="A signed-in shopper")

user_activity_batch = FileSource(
    name="user_activity_batch",
    path="data/user_activity.parquet",
    timestamp_field="event_timestamp",          # when the value became true
    created_timestamp_column="created",         # tie-breaker for late corrections
)

# A stream job can push fresh rows here; Feast writes them to the online store
# (and, if configured, to the offline store so training sees the same values).
user_activity_push = PushSource(name="user_activity_push", batch_source=user_activity_batch)

user_activity = FeatureView(
    name="user_activity",
    entities=[user],
    ttl=timedelta(days=2),                      # older values count as missing
    schema=[
        Field(name="sessions_7d", dtype=Int64),
        Field(name="orders_90d", dtype=Int64),
        Field(name="avg_order_value_90d", dtype=Float32),
    ],
    online=True,
    source=user_activity_push,
    tags={"owner": "growth-ml"},
)
```

The workflow:

```bash
feast apply                                           # register definitions, create online tables
feast materialize-incremental "$(date -u +%Y-%m-%dT%H:%M:%S)"   # copy latest values to Redis
```

Building a training set and reading online features:

```python
from datetime import datetime, timezone

import pandas as pd
from feast import FeatureStore

store = FeatureStore(repo_path="feature_repo")
features = ["user_activity:sessions_7d", "user_activity:orders_90d",
            "user_activity:avg_order_value_90d"]

# Offline: point-in-time join for every (user, timestamp) label row.
entity_df = pd.DataFrame({
    "user_id": [1001, 1002, 1001],
    "event_timestamp": pd.to_datetime(["2026-09-01 10:00", "2026-09-02 18:30",
                                       "2026-09-20 08:15"], utc=True),
    "purchased": [0, 1, 1],
})
training_df = store.get_historical_features(entity_df=entity_df, features=features).to_df()

# Online: latest values for one request, a few ms from Redis.
row = store.get_online_features(features=features, entity_rows=[{"user_id": 1001}]).to_dict()

# From the stream job: push a fresh value.
store.push("user_activity_push", pd.DataFrame({
    "user_id": [1001], "sessions_7d": [5], "orders_90d": [3], "avg_order_value_90d": [42.0],
    "event_timestamp": [datetime.now(timezone.utc)], "created": [datetime.now(timezone.utc)],
}))
```

In a latency-critical service you would usually call the Feast feature server (HTTP or
gRPC) or read the online store directly with the same key format, rather than embedding
the Python SDK in the request path.

## 5. Streaming features and freshness

Some features only matter when they are fresh: `transactions_last_5m` for fraud,
`clicks_this_session` for a feed. Those are computed by a stream processor (Flink, Spark
Structured Streaming, Kafka Streams) over windows of events and pushed to the online
store within seconds. Streaming itself is covered in [Stream Processing Fundamentals](../DataEngineering/04_stream_processing.md)
and [Kafka and Event Streaming](../Tool-Kit/04_kafka_and_event_streaming.md).

The hard part is keeping the offline history consistent with what the stream served:

| Approach | How | Trade-off |
|---|---|---|
| **Stream writes both stores** | The stream job writes each window result to the online store and appends it (with its timestamp) to the offline store | Offline history is exactly what was served; backfilling a new feature means replaying the event log through the stream job |
| **Batch recompute offline, stream online** | A batch job recomputes the same aggregate from the warehouse for training; the stream serves online | Two implementations of one definition, so skew is back unless both are generated from one spec |
| **Log served features** | Record the online value at serving time (§6) | Exactly consistent, but new features need weeks of logs before you can train on them |
| **Unified engine** | Frameworks that compile one definition to both a batch backfill and a streaming job | Less code; you depend on the framework's window semantics |

**Window semantics must match.** "Last 10 minutes" is a sliding window in one system and
a 10-minute tumbling bucket in another; event time vs processing time; how late events are
handled. Write the definition down (event time, window type, allowed lateness) and test
both implementations on the same replayed events.

**Tiling.** Long windows over high-rate streams (e.g. "sum over 30 days, updated every
minute") are usually stored as pre-aggregated tiles (per-minute or per-hour partial sums)
and combined at read time, so each event updates one tile rather than every window it
falls in.

## 6. Feature logging: training on what was served

The alternative to rebuilding features for training is to **log the feature vector the
model actually received** at serving time, keyed by request ID, and later join it with
the label (a click, a purchase, a chargeback).

- **Pro:** no training–serving skew at all, because the training rows are the serving
  rows. No point-in-time join is needed for logged features.
- **Con:** a new feature can only be trained on after it has been logged for long enough
  (weeks), so experimentation slows down. Logging every candidate's features for a
  ranker is expensive; teams sample (see the feature-log sizing in
  [Ranked Home Feed](../SystemDesign/solutions/032_ranked_home_feed_solution.md)).

Large recommendation and ads systems commonly combine both: log served features for the
production model's training data, and use point-in-time backfills from the offline store to
evaluate candidate features before they are logged.

## 7. Online store design details

- **Key design.** `feature_view:entity_key` → a hash or serialized row of all the view's
  features, so one lookup returns a view. Composite entities (user × merchant) become one
  composite key.
- **Multi-get.** Batch every lookup a request needs into one round trip per store
  (`MGET`/pipelines in Redis, `BatchGetItem` in DynamoDB).
- **Defaults for missing values.** A new user has no history. Decide the default per
  feature (0, a global mean, a "missing" indicator) and use *the same* default in training.
  Training rows with nulls filled one way and serving rows filled another is skew.
- **Hot keys.** A viral item's features are read by every ranking request. Cache item
  features in the serving process with a short TTL; see
  [Partitioning, Shard Keys, and Hot Keys](../SystemDesign/building_blocks/25_partitioning_and_hot_keys.md).
- **Staleness monitoring.** Emit "age of the value read" as a metric. A materialization
  job that silently stopped yesterday looks healthy from every other angle.
- **Timeouts and fallbacks.** If the online store is slow, the model server should use
  defaults for missing features and mark the response as degraded rather than failing the
  request ([Serving: Online vs Offline Inference](03_serving_and_inference.md)).

## 8. Build or buy

| Option | Type | Notes |
|---|---|---|
| **Feast** | Open source | Registry, point-in-time joins, materialization, feature server; bring your own compute and stores |
| **Hopsworks** | Open source core + managed | Full platform with its own feature pipelines and online store (RonDB) |
| **Databricks Feature Engineering (Unity Catalog)** | Managed, in Databricks | Feature tables are Delta tables governed by Unity Catalog; online serving built in |
| **Vertex AI Feature Store** | Managed, Google Cloud | Offline data lives in BigQuery; online serving from managed nodes |
| **SageMaker Feature Store** | Managed, AWS | Online and offline (S3 + Glue catalog) feature groups |
| **Tecton** | Managed, commercial | Strong streaming-feature support; one definition compiled to batch and streaming |
| **Home-grown** | Your code | Common at large companies: warehouse tables + a KV store + a join library + logging |

Many teams do not need a feature store on day one. A single model with batch features and
a well-tested SQL job is fine. The need appears with the second and third model sharing
features, with real-time features, or with the first skew incident.

## 9. Failure modes

| Symptom | Cause | Fix |
|---|---|---|
| Offline AUC far above online performance | Leakage or skew | As-of joins; feature logging; skew monitor |
| Model degrades on Monday mornings | Weekend batch job did not run; online values are 3 days old | Freshness metric and alert per feature view |
| New users get strange scores | Null handling differs between training and serving | One default per feature, tested in both paths |
| Offline join takes 12 hours | Range join over unpartitioned history | Partition history by date; pre-aggregate; limit the TTL window |
| Redis latency spikes during materialization | Bulk writes compete with reads | Rate-limit materialization; write to a new key version and switch |
| Two teams' `active_user` features disagree | Duplicate definitions | Registry with owners; reuse over re-implementation |

## Common interview questions

**What is training–serving skew and how do you prevent it?**
A difference between the feature values seen in training and at serving time for the same
situation, from different logic, freshness or versions. Prevent it with one feature
definition used by both paths, or by logging served features and training on them.
Detect it by recomputing logged requests offline and comparing.

**What is point-in-time correctness?**
When building a training row for a prediction at time *t*, each feature takes its latest
value that was available before *t*, including pipeline lag, never a later value. It is an
as-of join, and it prevents leakage from the future.

**Why two stores?**
Training needs the full history with timestamps and large scans; serving needs the latest
value per key in milliseconds. No single store is good at both, so a warehouse or
lakehouse holds history and a key-value store holds the latest values.

**How do you serve a "clicks in the last 5 minutes" feature?**
A stream processor aggregates click events with an event-time sliding window and pushes
the result to the online store within seconds. It also writes the same values with
timestamps to the offline store, or the served values are logged, so training sees what
serving saw.

**Give three kinds of leakage.**
Target leakage (a feature set only after the outcome), temporal leakage (random split on
time-ordered data or future values in an as-of join), and preprocessing leakage
(statistics fitted on the test set). Also entity and duplicate leakage across splits.

**When don't you need a feature store?**
One model with daily batch features and no real-time path. A tested SQL job and a
registry entry are enough. Introduce one when features are shared, real-time, or when skew
has already bitten.

**What does TTL do in a feature view?**
It bounds how old a value may be. In point-in-time joins, values older than the TTL
relative to the row's timestamp come back as missing, so training sees the same "no
recent data" that serving would.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| **Student / Intern** | Intern | Intern (pre-L3) | Knows what a feature and an entity are, and can explain data leakage with an example. Splits time-series data by time, not randomly. |
| **Junior (L3)** | ML Engineer I | L3 | Writes feature code with tests for window boundaries and nulls; uses an existing feature store's APIs for training sets and online reads; knows why offline and online stores differ. |
| **Mid (L4)** | ML Engineer II | L4 | Defines feature views with correct timestamps and TTLs; writes as-of joins by hand; sets up materialization and freshness alerts; detects skew by comparing logged and recomputed features. |
| **Senior (L5)** | Senior ML Engineer | L5 | Designs the feature platform for a product: batch vs streaming vs request-time features, window semantics, online store sizing, hot-key caching, fallbacks, feature logging vs backfill, and leakage reviews for new features. |
| **Staff+ (L6+)** | Staff / Principal ML Engineer | L6–L8 | Decides build vs buy across the organisation, sets feature ownership and governance (PII, retention, lineage), unifies streaming and batch definitions, and makes feature reuse measurable. |

## Interview checklist

- [ ] I can define a feature, an entity, an offline store, an online store and materialization.
- [ ] I can explain training–serving skew with its three kinds (logic, freshness, version) and how to detect it.
- [ ] I can explain point-in-time correctness, write an as-of join (pandas `merge_asof` or SQL), and say why availability lag matters.
- [ ] I can name five kinds of leakage and the guard for each.
- [ ] I can sketch a Feast repo: entity, source, feature view with TTL, `apply`, `materialize`, historical and online retrieval.
- [ ] I can design a streaming feature and say how its offline history stays consistent.
- [ ] I can compare feature logging with point-in-time backfills.
- [ ] I can size an online store and say how to handle hot keys, missing values and staleness.

Related: [The MLOps Lifecycle](01_mlops_lifecycle.md), [Serving: Online vs Offline Inference](03_serving_and_inference.md),
[ML and LLM Systems](../SystemDesign/building_blocks/23_ml_and_llm_systems.md) (feature stores and skew),
[Stream Processing Fundamentals](../DataEngineering/04_stream_processing.md), [Day 166: Feature Stores & Feature Engineering for LLM Apps](../AI-road-map/166_day_feature_stores.md).
