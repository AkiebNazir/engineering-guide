# Batch Processing with Apache Spark

SQL in a warehouse (ELT with dbt) covers most transformations. Some jobs need more:
parsing 50 TB of raw JSON logs, building ML features in Python, joining data that
lives in a lake rather than a warehouse, or anything too big or too custom for one
SQL statement. That is Apache Spark's territory. This chapter builds Spark up from
the problem it solves to the internals interviewers probe: how a job becomes stages
and tasks, what a shuffle physically does, how joins are chosen, how Adaptive Query
Execution and skew handling work, memory and failure behaviour, and how to read the
Spark UI when a job is slow.

## Foundations — How do you process data that does not fit on one machine?

### The problem

Say you have 10 TB of click logs and want clicks per country per day. One laptop
reading at ≈500 MB/s from SSD needs about 6 hours just to read the data once, and it
cannot hold the intermediate results in memory. The answer is to split the work:

1. **Split the data** into many pieces (**partitions**), say 80,000 pieces of
   128 MB each.
2. **Send the code to the data**: run the same function on many machines at once,
   each processing some partitions. With 1,000 CPU cores that is 80 rounds of
   128 MB, a few minutes.
3. **Bring related results together**: every partial count for "DE on 2026-09-27"
   must end up on the same machine to be added up. Moving data between machines by
   key is called a **shuffle**.
4. **Survive failures**: with a thousand machines, one will fail during a long job.
   The system must redo only the lost piece.

Google's **MapReduce** (2004) packaged this as *map, shuffle, reduce* with every step
written to disk. **Apache Spark** (2009 at UC Berkeley, 1.0 in 2014) generalised it:
any graph of operations, intermediate data kept in memory where possible, a SQL
optimizer, and one engine for batch, SQL, streaming and ML. Spark 4.0 shipped in
2025 and is the current major line in 2026.

Spark does **not store** data. It reads from storage (S3, GCS, ADLS, HDFS, Iceberg or
Delta tables, JDBC databases, Kafka), computes across a cluster, and writes results
back.

### The pieces

| Piece | What it is |
|---|---|
| **Driver** | The process running your `main` program. It builds the plan, splits it into stages and tasks, schedules tasks and tracks their results. One per application. |
| **Executors** | JVM processes on worker machines that run tasks and hold cached data and shuffle files. Each has some cores (task slots) and memory. |
| **Cluster manager** | Allocates machines/containers for the driver and executors: Kubernetes, YARN, or Spark's standalone manager. Managed services (Databricks, EMR, Dataproc, Glue) run this for you. |
| **Partition** | A chunk of the data. One task processes one partition. |
| **Task** | One unit of work: one stage's code applied to one partition, on one core. |
| **Stage** | A group of tasks that can run without moving data between machines. Stages are separated by shuffles. |
| **Job** | All the stages triggered by one action (`count()`, `write`). |

```arch
%% caption: The driver turns your code into a plan of stages and tasks; the cluster manager provides executors; executors run tasks on partitions read from storage and exchange shuffle data with each other.
grid 170x110
node user "Your code" at 0,0 icon=python sub="PySpark / SQL / Scala"
node driver "Driver" at 1,0 icon=cpu sub="plan, stages, tasks"
node cm "Cluster manager" at 2,0 icon=k8s sub="Kubernetes / YARN"
group cluster "Executors on worker nodes" color=slate style=dashed icon=server
node w1 "Executor 1" at 0,1 in cluster icon=worker sub="4 cores, cache, shuffle"
node w2 "Executor 2" at 1,1 in cluster icon=worker sub="4 cores, cache, shuffle"
node w3 "Executor 3" at 2,1 in cluster icon=worker sub="4 cores, cache, shuffle"
node store "Object storage" at 1,2 icon=storage sub="S3 / GCS / Iceberg"
user -> driver : "submit"
driver -> cm : "request executors"
driver -> w1 : "tasks"
driver -> w2
driver -> w3
w1 -> store
w2 -> store
w3 -> store
```

### A first job

```python
from pyspark.sql import SparkSession, functions as F

spark = SparkSession.builder.appName("clicks-per-country").getOrCreate()

clicks = spark.read.parquet("s3://lake/raw/clicks/")             # lazy: nothing read yet
daily = (
    clicks
    .filter(F.col("event_date") == "2026-09-27")                  # lazy
    .groupBy("country")                                            # lazy
    .agg(F.count("*").alias("clicks"))                             # lazy
)
daily.write.mode("overwrite").parquet("s3://lake/marts/clicks_by_country/dt=2026-09-27/")
# ^ the action: Spark now plans, reads only the needed columns and files, and runs
```

## 1. Deployment: where the driver and executors run

| Cluster manager | Notes (2026) |
|---|---|
| **Kubernetes** | Driver and executors are pods; the common choice for new self-managed platforms. Spark Operator (Kubeflow) manages `SparkApplication` resources. |
| **YARN** | The Hadoop resource manager; still common on long-lived Hadoop/EMR clusters. |
| **Standalone** | Spark's built-in manager; simple, fine for small dedicated clusters. |
| Mesos | Deprecated in Spark 3.2 and removed in Spark 4.0. |

**Deploy mode.** In *client* mode the driver runs where you launched it (your laptop,
a notebook, an Airflow worker), so if that machine dies the job dies. In *cluster* mode
the driver runs inside the cluster; use it for production jobs.

**Spark Connect** (since 3.4, much more complete in 4.0) separates a thin client from
the driver over gRPC. Notebooks and applications talk to a remote Spark server without
running a JVM driver locally, which isolates client crashes and version upgrades.

```bash
spark-submit \
  --master k8s://https://k8s-api.internal:6443 \
  --deploy-mode cluster \
  --name clicks-daily \
  --conf spark.kubernetes.container.image=registry.internal/spark-jobs:4.0.1 \
  --conf spark.executor.instances=20 \
  --conf spark.executor.cores=4 \
  --conf spark.executor.memory=12g \
  --conf spark.sql.adaptive.enabled=true \
  local:///opt/jobs/clicks_daily.py --date 2026-09-27
```

## 2. APIs: RDDs, DataFrames and Spark SQL

- **RDD (Resilient Distributed Dataset)**: the original abstraction, an immutable,
  partitioned collection of arbitrary objects with a lineage of the functions that
  produced it. Spark cannot see inside your lambdas, so it cannot optimise them. Rarely
  written directly today; still what everything compiles down to.
- **DataFrame**: a distributed table with named, typed columns. Operations are
  declarative (`filter`, `groupBy`, `join`), so the **Catalyst optimizer** can reorder
  and prune them. Python, Scala, Java, R and SQL all build the same plan, which is why
  PySpark DataFrame code runs at about the speed of Scala DataFrame code.
- **Dataset** (Scala/Java only): a typed DataFrame (`Dataset[Click]`).
- **Spark SQL**: `spark.sql("SELECT ...")` produces the same plans as DataFrames.

**Precision note on Python speed.** The "Python is as fast as Scala" claim holds only
while you stay in built-in functions. A plain Python UDF ships every row from the JVM
to a Python worker process and back, which can be many times slower. Prefer built-in
functions in `pyspark.sql.functions`; if you need Python, use **pandas UDFs**
(vectorised, exchanging Arrow batches) or the Arrow-optimised Python UDFs available in
recent versions.

```python
import pandas as pd
from pyspark.sql import functions as F
from pyspark.sql.functions import pandas_udf

@pandas_udf("double")
def usd(amount: pd.Series, rate: pd.Series) -> pd.Series:   # runs on Arrow batches
    return amount * rate

orders = orders.withColumn("amount_usd", usd(F.col("amount"), F.col("fx_rate")))
# Better still when possible: F.col("amount") * F.col("fx_rate") stays in the JVM.
```

## 3. Lazy evaluation and the optimizer

**Transformations** (`select`, `filter`, `withColumn`, `join`, `groupBy`) return a new
DataFrame and only extend a logical plan. **Actions** (`count`, `collect`, `show`,
`write`, `foreach`) force execution, and each action starts one or more **jobs**.

Laziness lets Spark see the whole pipeline before running it:

1. **Analysis**: resolve column names and types against the catalog.
2. **Logical optimisation (Catalyst)**: rule-based rewrites such as **predicate
   pushdown** (filter as early as possible, even into the Parquet reader), **column
   pruning** (read only used columns), constant folding, and join reordering with
   statistics (cost-based optimisation).
3. **Physical planning**: choose join strategies and where exchanges (shuffles) go.
4. **Code generation (Tungsten)**: whole-stage code generation fuses a chain of
   operators into one tight function over binary rows kept off the Java heap.

```python
daily.explain(mode="formatted")
```

An abridged plan for the job above (exact text varies by version):

```text
== Physical Plan ==
AdaptiveSparkPlan (isFinalPlan=false)
+- HashAggregate (keys=[country], functions=[count(1)])          <- final count, stage 2
   +- Exchange hashpartitioning(country, 200)                     <- the shuffle
      +- HashAggregate (keys=[country], functions=[partial_count(1)])   <- map-side combine
         +- Project [country]
            +- FileScan parquet [country, event_date]
                 PartitionFilters: [isnotnull(event_date), (event_date = 2026-09-27)]
                 ReadSchema: struct<country:string>
```

Read plans bottom-up. `FileScan` shows pruning worked (only two columns, only one
partition directory). Every `Exchange` is a shuffle and therefore a stage boundary.
`partial_count` before the exchange means each map task pre-aggregates, so only one
row per country per task crosses the network.

**Common laziness surprises.** Calling two actions on the same DataFrame recomputes
it twice from the source (cache it if it is reused and expensive). A `print` inside a
UDF runs on executors, not the driver. `df.count()` "just to check" launches a full
job.

## 4. Jobs, stages, tasks and the two kinds of dependency

- **Narrow dependency**: each output partition depends on one input partition
  (`filter`, `select`, `withColumn`, `map`, union). Spark **pipelines** consecutive
  narrow operations inside one task: read a row, filter it, project it, pass it on,
  with no intermediate materialisation.
- **Wide dependency**: an output partition needs data from many input partitions
  (`groupBy`, `join` without broadcast, `distinct`, `orderBy`, `repartition`, window
  functions with `partitionBy`). This requires a **shuffle**, and the shuffle is where
  Spark cuts the job into **stages**.

```arch
%% caption: One job, two stages. Stage 1 reads, filters and pre-aggregates each input partition in parallel and writes shuffle files; stage 2 starts only when every map task has finished, fetches its key range from every map output, and finishes the aggregation.
grid 150x100
group s1 "Stage 1: narrow ops, pipelined" color=blue icon=layers
node p1 "Partition 1" at 0,0 in s1 icon=file sub="read + filter"
node p2 "Partition 2" at 1,0 in s1 icon=file sub="read + filter"
node p3 "Partition 3" at 2,0 in s1 icon=file sub="read + filter"
node x "Shuffle (Exchange)" at 1,1 shape=card icon=sort color=amber sub="hash(country) mod N, via local disk"
group s2 "Stage 2: after the shuffle" color=green icon=layers
node r1 "Reduce task 1" at 0.5,2 in s2 icon=sigma sub="countries A-M"
node r2 "Reduce task 2" at 1.5,2 in s2 icon=sigma sub="countries N-Z"
p1 -> x
p2 -> x
p3 -> x
x -> r1
x -> r2
```

Numbers to know:

- **Tasks per stage = partitions of that stage.** Input partitions come from file
  splits (`spark.sql.files.maxPartitionBytes`, default 128 MB). After a shuffle the
  count is `spark.sql.shuffle.partitions` (default **200**), which Adaptive Query
  Execution then coalesces (§7).
- **Parallelism = executors × cores per executor.** 20 executors × 4 cores run 80
  tasks at once. A stage with 80,000 tasks runs in ≈1,000 waves; a stage with 20 tasks
  leaves 60 cores idle.
- Aim for tasks that take from a few seconds to a few minutes and handle ≈100–200 MB
  of data each. Millions of tiny tasks drown in scheduling overhead; a few huge ones
  spill and straggle.

## 5. The shuffle, physically

A shuffle is the most expensive thing Spark does, because it touches every layer:
CPU (serialise, sort, compress), local disk (write, then read), and network (every
reducer fetches from every mapper).

1. **Map side.** Each task of the upstream stage computes, for every output row, the
   target reduce partition (`hash(key) mod N` for a hash partitioner). With the
   default **sort-based shuffle** it buffers records in memory sorted by partition id,
   spills sorted runs to disk when the buffer fills, and finally merges them into **one
   data file plus one index file** per map task. If the operation allows it
   (`groupBy().agg(sum)`, `reduceByKey`), a **map-side combine** pre-aggregates first,
   which can shrink the shuffle enormously.
2. **Registration.** When a map task finishes, the driver's `MapOutputTracker` records
   where its output lives and how big each partition's block is.
3. **Barrier.** The downstream stage starts only after **all** map tasks of the
   upstream stage finish, because any of them may hold data for any key. One slow map
   task delays the whole next stage.
4. **Reduce side.** Each reduce task fetches its block from every map output over the
   network (M × N blocks in total), merges them, and runs the aggregation or join.

Consequences worth saying in an interview:

- **Shuffle files live on executors' local disks.** If an executor dies, its map
  outputs are lost and reducers get a `FetchFailedException`; Spark re-runs the lost
  map tasks (§10). An **external shuffle service** (YARN) or shuffle tracking and
  graceful decommissioning (Kubernetes) keep shuffle data available when executors are
  removed by dynamic allocation.
- **`groupByKey` vs. `reduceByKey`** (RDD API): `groupByKey` ships every value across
  the network; `reduceByKey` combines on the map side first. The DataFrame
  `groupBy().agg()` already does the combine for algebraic aggregates such as `sum`
  and `count`; `collect_list` cannot combine much.
- **Shrink before you shuffle.** Filter rows and drop columns before the wide
  operation. Spark pushes many filters down automatically, but not past UDFs or
  across every join.

Watch one job's stages, a skewed key and a lost executor below.

<div class="lab" data-viz="flow-spark-shuffle"></div>

## 6. Join strategies

| Strategy | How it works | When Spark picks it | Cost |
|---|---|---|---|
| **Broadcast hash join** | Collect the small side to the driver, send a copy to every executor, hash it, stream the big side through it | Small side below `spark.sql.autoBroadcastJoinThreshold` (default 10 MB, by estimated size) or a `broadcast()` hint | No shuffle of the big side. Risk: a "small" table that is really 5 GB causes driver or executor OOM |
| **Sort-merge join** | Shuffle both sides by join key, sort each partition, merge | Default for two large tables with equi-join keys | Two shuffles + sorts; robust, spills gracefully |
| **Shuffle hash join** | Shuffle both sides, build a hash table from the smaller side per partition | When one side is much smaller per partition, or when preferred by AQE | Avoids the sort; needs each build partition to fit in memory |
| **Broadcast nested loop / cartesian** | Compare every pair | Non-equi joins (`a.ts BETWEEN b.start AND b.end`) with no equality key | Can be catastrophically slow; add an equality key (e.g. a bucketed date) if you can |
| **Storage-partitioned join** | Both tables are already bucketed/partitioned the same way (Hive bucketing, Iceberg/Delta partitioning) | Matching layouts and settings | No shuffle at all |

```python
from pyspark.sql import functions as F

orders = spark.read.table("lake.sales.orders")          # billions of rows
countries = spark.read.table("lake.ref.countries")      # 250 rows

enriched = orders.join(F.broadcast(countries), "country_code", "left")
```

## 7. Adaptive Query Execution (AQE)

Static plans are built on estimates that are often wrong (after a filter, after a
UDF). **AQE**, on by default since Spark 3.2 (`spark.sql.adaptive.enabled=true`),
re-optimises at every shuffle boundary using the *actual* sizes of the map outputs:

1. **Coalesce shuffle partitions.** 200 post-shuffle partitions holding 2 GB in total
   become ≈30 partitions of ≈64 MB (the advisory size,
   `spark.sql.adaptive.advisoryPartitionSizeInBytes`), so you rarely need to tune
   `spark.sql.shuffle.partitions` by hand. Set it high enough for your biggest shuffle
   and let AQE shrink it.
2. **Switch join strategy.** If one side turns out to be small after filtering, a
   planned sort-merge join becomes a broadcast join.
3. **Split skewed partitions** (§8).

## 8. Data skew

Skew means some keys have far more rows than others: one mega-customer, `NULL`
country codes, a bot user id, the default value `"unknown"`. The partition that
holds the hot key takes hours while the others finish in minutes.

**How it shows up.** In the Spark UI stage page, the task-duration summary shows a
max far above the 75th percentile (for example median 40 s, max 45 min), one task with
huge "Shuffle Read Size" and "Spill (Disk)", and a job stuck at "199/200 tasks".
Executors may die with out-of-memory on that one task.

**Fixes, in the order to try them:**

1. **Check the key.** Very often the hot key is `NULL` or a placeholder that should be
   filtered out or handled separately.
2. **Broadcast** the other side if it is small enough, so the skewed side is never
   shuffled.
3. **Let AQE split it.** With `spark.sql.adaptive.skewJoin.enabled=true` (default) a
   partition larger than `skewedPartitionFactor` (default 5) × the median *and* larger
   than `skewedPartitionThresholdInBytes` (default 256 MB) is split into several
   tasks, and the matching partition of the other side is duplicated for each.
   This handles sort-merge joins; it does not fix skewed aggregations.
4. **Salt the key** by hand, for aggregations or when AQE is not enough:

```python
from pyspark.sql import functions as F

SALT = 16
events = spark.read.table("lake.raw.events")

# Stage 1: aggregate by (key, random salt) so one hot key is spread over 16 tasks.
partial = (
    events
    .withColumn("salt", (F.rand(seed=7) * SALT).cast("int"))
    .groupBy("customer_id", "salt")
    .agg(F.count("*").alias("n"), F.sum("amount").alias("amount"))
)
# Stage 2: combine the 16 partial results per key. This shuffle is small.
totals = partial.groupBy("customer_id").agg(F.sum("n").alias("n"), F.sum("amount").alias("amount"))
```

For a skewed *join*, salt the big side with a random salt in `[0, SALT)` and
**explode** the small side into `SALT` copies (one per salt value), then join on
`(key, salt)`.

## 9. Partitions, files and writing output

| Operation | What it does | Use when |
|---|---|---|
| `repartition(n)` / `repartition("col")` | Full shuffle into `n` partitions (by hash of `col` if given) | Increase parallelism, or co-locate by key before writing |
| `coalesce(n)` | Merges existing partitions without a shuffle | Reduce the number of output files cheaply. Beware: it also reduces the parallelism of the *upstream* work in the same stage |
| `write.partitionBy("dt")` | Creates a directory per value (`dt=2026-09-27/`) | Date-partitioned lake tables; never on high-cardinality columns |
| `write.bucketBy(n, "col")` | Hash-buckets files within a table | Repeated joins on the same key (Hive-style tables) |

**The small-files problem, from Spark's side.** `df.write.partitionBy("dt", "country")`
from 2,000 tasks can write up to 2,000 files *per directory*. Repartition by the
partition columns first (`df.repartition("dt", "country")`), or rely on the table
format's optimised writes and compaction.

**Idempotent writes.** A retried Airflow task must not duplicate data
([chapter 5](05_orchestration_airflow.md)). Options:

```python
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")

(daily_df
 .write
 .mode("overwrite")                 # with dynamic mode: replaces only the dt partitions present in daily_df
 .partitionBy("dt")
 .parquet("s3://lake/marts/clicks_by_country/"))

# With Iceberg or Delta, prefer the table APIs, which commit atomically:
daily_df.writeTo("lake.marts.clicks_by_country").overwritePartitions()
```

Without `dynamic`, `mode("overwrite")` on a partitioned path deletes **every**
partition, a classic production incident. Writing plain files to S3 also needs a safe
output committer (the S3A "magic" committer, or EMR's optimised committer); table
formats avoid the problem by committing through metadata.

## 10. Memory, caching and failure

### Executor memory

| Region | Setting (defaults) | Holds |
|---|---|---|
| JVM heap | `spark.executor.memory` | Everything below |
| Unified memory | `spark.memory.fraction` = 0.6 of (heap − 300 MB) | Execution (shuffle buffers, joins, sorts, aggregations) and storage (cached blocks, broadcasts), borrowing from each other |
| Protected storage | `spark.memory.storageFraction` = 0.5 of unified | Cached data that execution cannot evict |
| User memory | the remaining ≈40% | Your data structures, UDF objects |
| Overhead (off heap) | `spark.executor.memoryOverhead` = max(384 MB, 10% of executor memory) | JVM internals, Python workers, network buffers. Too small → the container is killed by YARN or Kubernetes (exit code 137) |

Common out-of-memory causes and fixes:

| Symptom | Likely cause | Fix |
|---|---|---|
| Driver OOM | `collect()` or `toPandas()` on a big DataFrame; a broadcast that is too large | Write results out instead; lower or disable the broadcast threshold |
| One executor OOM, others fine | Skew | §8 |
| Container killed, exit 137 | Off-heap usage (PySpark workers, Arrow) above overhead | Raise `memoryOverhead`; fewer cores per executor |
| Heavy "Spill (Disk)" | Partitions too large for execution memory | More shuffle partitions / smaller advisory size; more memory per core |
| Long GC times | Huge heaps, many objects (UDFs, RDDs of objects) | DataFrames over RDDs, moderate executor sizes (≈4–5 cores each) |

### Caching

`df.cache()` (or `persist(StorageLevel.MEMORY_AND_DISK)`) keeps a DataFrame's
partitions after the first action computes them. Cache only what is reused several
times and expensive to recompute; unpersist when done. Caching a DataFrame used once
just wastes memory, and caching before a filter caches the unfiltered data.

### Fault tolerance

- **Lineage.** Every partition knows how it was computed, so a lost partition is
  recomputed from its parents, not restored from a replica.
- **Task retries.** A failed task is retried on another executor, up to
  `spark.task.maxFailures` (default 4) times.
- **Stage retries.** A `FetchFailedException` (lost shuffle output) makes Spark re-run
  only the upstream map tasks whose output was lost, then retry the reducers.
- **Speculation** (`spark.speculation=true`) launches duplicate copies of unusually
  slow tasks; the first to finish wins. Helps with bad machines, not with skew, and
  requires side-effect-free tasks.
- **Checkpointing** (`df.checkpoint()`) writes data to reliable storage and truncates
  a very long lineage (iterative algorithms).
- **Driver failure** kills the application. Batch jobs are made safe by being
  idempotent and re-runnable from the orchestrator.

## 11. Debugging a slow job with the Spark UI

1. **Jobs tab**: which job and stage takes the time.
2. **Stages tab → the slow stage**: compare the task duration percentiles (skew?),
   shuffle read/write sizes (is the shuffle huge?), spill, GC time, and input size per
   task.
3. **SQL / DataFrame tab**: the physical plan with actual row counts per operator. Look
   for a join that exploded row counts (a many-to-many join on a non-unique key), a
   scan reading far more than expected (missing partition filter), and which join
   strategy was used.
4. **Executors tab**: failed tasks, lost executors, memory use.
5. After the application ends, the **Spark History Server** shows the same UI from
   event logs.

A tuning checklist in priority order: read less (partition filters, column
pruning, Parquet/Iceberg stats) → shuffle less (filter early, broadcast small sides,
pre-aggregate) → fix skew → right-size partitions (let AQE coalesce) → fix Python UDFs
→ only then tune memory and executor sizes.

## 12. Spark vs. the alternatives

| Tool | Choose it when |
|---|---|
| Warehouse SQL (Snowflake, BigQuery) + dbt | The logic is SQL and the data is in the warehouse. Least operational burden |
| Spark (Databricks, EMR, Dataproc, self-managed) | Lake-resident data, complex Python/Scala logic, ML feature pipelines, very large joins, one engine for batch and streaming |
| Trino / Presto | Interactive SQL across many sources in a lake without moving data |
| DuckDB / Polars | Data fits on one big machine (tens to hundreds of GB). Far simpler and often faster than a cluster |
| Flink | Stream processing first, batch second ([chapter 4](04_stream_processing.md)) |
| Ray | Python-native distributed compute, especially ML training and inference |
| Apache Beam / Dataflow | One portable pipeline definition for batch and stream on Google Cloud |

Do not reach for a cluster when a single machine will do: a modern server with 64
cores and hundreds of GB of RAM running DuckDB or Polars handles datasets that
needed a Hadoop cluster ten years ago.

## Common interview questions

**What is the difference between a transformation and an action?**
Transformations are lazy and only build a logical plan; actions trigger a job. Laziness
lets Catalyst optimise the whole pipeline (push filters down, prune columns) before
anything runs.

**What is a shuffle, and why is it expensive?**
Redistributing rows across executors so rows with the same key end up in the same
partition. Map tasks serialise, sort and write partitioned files to local disk;
reduce tasks fetch blocks from every map output over the network. It costs CPU,
disk and network, and it is a barrier between stages.

**Narrow vs. wide dependencies?**
Narrow: each output partition depends on one input partition, so operations are
pipelined in one task. Wide: an output partition needs many input partitions, which
requires a shuffle and a new stage.

**How does Spark choose a join strategy?**
Broadcast hash join if one side is estimated under the broadcast threshold or hinted;
otherwise sort-merge join for equi-joins; shuffle hash join in some cases; nested loop
for non-equi joins. AQE can switch to broadcast at runtime once real sizes are known.

**A job is stuck at 199/200 tasks. What do you do?**
Almost certainly skew. Confirm in the stage's task metrics (max vs. median duration,
shuffle read). Check for `NULL`/default keys, broadcast the other side if possible,
rely on AQE skew-join splitting, or salt the key.

**`repartition` vs. `coalesce`?**
`repartition` does a full shuffle and can increase or decrease partitions and
co-locate by key; `coalesce` merges partitions without a shuffle, only decreases,
and can reduce the upstream parallelism of the same stage.

**How does Spark recover from an executor failure?**
Tasks on it are retried elsewhere; lost cached partitions are recomputed from lineage;
lost shuffle outputs cause a fetch failure, and Spark re-runs only the missing map
tasks before retrying the reducers.

**Why is my PySpark UDF slow?**
Rows are serialised from the JVM to a Python worker and back. Use built-in functions,
or pandas/Arrow UDFs that move columnar batches.

**What does AQE do?**
Re-plans at each shuffle using actual statistics: coalesces small post-shuffle
partitions, converts joins to broadcast when a side turns out small, and splits
skewed join partitions.

**How do you make a Spark write idempotent?**
Write a whole partition at a time with dynamic partition overwrite, or use a table
format's atomic `overwritePartitions` / `MERGE`. Never plain append in a job that can
be retried.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student / Intern | Intern, new learner | — | Why distributed processing exists; driver vs. executors; lazy transformations vs. actions; writes a simple PySpark DataFrame job |
| Junior | Data Engineer I | L3 | Narrow vs. wide operations; what a shuffle is; filter early and avoid `collect()`; broadcast joins; reads the Spark UI's jobs and stages |
| Mid | Data Engineer II | L4 | Reads physical plans (`Exchange`, join types, pushed filters); sizes partitions and executors; diagnoses and fixes skew; idempotent partitioned writes; pandas UDFs vs. Python UDFs |
| Senior | Senior Data Engineer | L5 | Explains shuffle internals, AQE, join selection and memory regions; debugs OOM, spill, fetch failures and stragglers from metrics; designs table layouts (partitioning, bucketing, Iceberg) that remove shuffles; knows when not to use Spark |
| Staff+ | Staff / Principal Data Engineer | L6+ | Sets platform choices (Spark vs. warehouse vs. single-node engines vs. Flink), cost and capacity models for the cluster fleet, upgrade strategy (Spark 4, Spark Connect), and standards that make hundreds of jobs reliable and cheap |

## Interview checklist

- [ ] I can explain driver, executors, cluster manager, job, stage, task and partition.
- [ ] I can explain lazy evaluation and what Catalyst does with it (pushdown, pruning, codegen).
- [ ] I can say where stage boundaries are and why, and read an `Exchange` in a plan.
- [ ] I can walk through a sort-based shuffle: map-side sort and spill, index file, fetch, barrier.
- [ ] I can compare broadcast, sort-merge and shuffle hash joins and name the broadcast threshold.
- [ ] I can list the three things AQE does.
- [ ] I can diagnose skew from the Spark UI and fix it (null keys, broadcast, AQE, salting).
- [ ] I can compare `repartition` and `coalesce` and explain the small-files problem.
- [ ] I can make a Spark write idempotent (dynamic partition overwrite, table formats).
- [ ] I can explain executor memory regions and the common OOM causes.
- [ ] I can explain how Spark recovers from task, executor and shuffle-data loss.

Related: [Batch and Stream Processing](../SystemDesign/building_blocks/21_batch_and_stream_processing.md),
[The Papers Behind Google-Scale Systems](../SystemDesign/building_blocks/24_google_papers.md) (MapReduce),
[Partitioning, Shard Keys, and Hot Keys](../SystemDesign/building_blocks/25_partitioning_and_hot_keys.md) (skew is the batch form of a hot key),
[Bonus: How Postgres Executes a Query](../SQL/15_bonus_how_postgres_executes_a_query.md) (the single-node version of plans and joins).
