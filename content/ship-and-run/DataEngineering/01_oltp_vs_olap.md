# OLTP vs OLAP & Data Warehouses

Backend engineers usually build OLTP systems: the database behind the app, answering
"what is in order 812?" in a millisecond. Data engineers build OLAP systems: the
warehouse or lakehouse that answers "what was revenue per country per week for five
years?" over billions of rows. This chapter explains why those are two different
machines, how columnar warehouses, data lakes and open table formats actually work,
and how data gets from one side to the other (batch extracts, ELT and change data
capture). It is the map for the rest of this module.

## Foundations — Why can't analysts just query the production database?

### Two jobs, one company

Picture a coffee chain with a mobile ordering app. Every tap in the app becomes a
small database operation: insert an order, update a loyalty balance, read one
customer's last five orders. There are thousands of these per second, each touching a
handful of rows, and each must be correct and fast because a customer is waiting.

Now the finance team asks: *"What was average order value by city, by week, for the
last three years, split by new vs. returning customers?"* That question touches every
order ever placed, but only three or four columns of each. It can run for a minute and
nobody minds, but if it runs on the same database the app uses, it reads gigabytes
through the same disks and buffer cache the app depends on, and the app slows down for
every customer while it runs.

These two workloads have names:

- **OLTP (Online Transaction Processing)**: many small, concurrent reads and writes
  by key, each needing to be fast and correct right now. The database of record.
- **OLAP (Online Analytical Processing)**: few, large, read-mostly queries that scan
  and aggregate huge amounts of history. The database of insight.

Data engineering is mostly the work of **copying data from the first kind of system
into the second kind**, reshaping it on the way so it is easy and cheap to ask
questions of, and keeping that copy correct and fresh.

### The pieces of a data platform

| Piece | What it does | Examples (2026) |
|---|---|---|
| **Sources** | Where data is born | Postgres/MySQL app databases, event streams from apps, SaaS APIs (Stripe, Salesforce), files |
| **Ingestion** | Copies data out of sources | Batch extracts, CDC with Debezium, Fivetran/Airbyte connectors, Kafka Connect |
| **Storage** | Holds the analytical copy | Warehouses (Snowflake, BigQuery, Redshift), lakes/lakehouses (S3 + Iceberg/Delta), real-time OLAP (ClickHouse, Druid, Pinot) |
| **Transformation** | Cleans, joins and models raw data into tables people can use | SQL with dbt ([chapter 6](06_data_transformation_dbt.md)), Spark ([chapter 3](03_batch_processing_spark.md)), Flink ([chapter 4](04_stream_processing.md)) |
| **Orchestration** | Runs every step in the right order, retries, alerts | Airflow ([chapter 5](05_orchestration_airflow.md)), Dagster, Prefect |
| **Serving** | Puts the results in front of people and systems | BI dashboards (Looker, Tableau, Power BI), ML feature stores, reverse ETL back into SaaS tools |
| **Governance & quality** | Says what data means, who may see it, and whether it is right | Catalogs (Unity Catalog, Glue, Polaris), data tests, lineage, access policies |

```arch
%% caption: A data platform copies data out of the systems that create it, lands it raw, reshapes it in layers, and serves the result; orchestration and quality checks wrap every step.
grid 170x115
group src "Sources" color=slate icon=app
node app "App database" at 0,0 in src icon=db sub="Postgres, OLTP"
node ev "App events" at 1,0 in src icon=event sub="clicks, logs"
node saas "SaaS APIs" at 2,0 in src icon=api sub="Stripe, CRM"
node ing "Ingestion" at 1,1 icon=workflow shape=card sub="CDC, batch extract, connectors"
group wh "Warehouse or lakehouse (OLAP)" color=blue icon=layers
node raw "Raw / bronze" at 0,2 in wh icon=archive sub="exact copy"
node clean "Clean / silver" at 1,2 in wh icon=filter sub="typed, deduped"
node marts "Marts / gold" at 2,2 in wh icon=table sub="facts + dimensions"
group use "Consumers" color=green icon=users
node bi "Dashboards" at 0,3 in use icon=dashboard
node ml "ML features" at 1,3 in use icon=model
node rev "Reverse ETL" at 2,3 in use icon=sync sub="back into SaaS"
app -> ing
ev -> ing
saas -> ing
ing -> raw
raw -> clean : "transform"
clean -> marts : "model"
marts -> bi
marts -> ml
marts -> rev
```

### An everyday analogy

A restaurant kitchen (OLTP) is organised around serving one table at a time, fast: the
ingredients for each dish are within arm's reach. The accountant (OLAP) wants totals:
how much flour was used this quarter, by dish. You do not let the accountant walk
through the kitchen counting flour bags during dinner service. Instead, every night
someone copies the day's receipts into a ledger organised by ingredient, and the
accountant works from the ledger. The ledger is the warehouse; the nightly copy is the
pipeline; the ledger's layout (by ingredient, not by table) is the modeling.

### Vocabulary you will meet in this module

| Term | One-line meaning |
|---|---|
| OLTP / OLAP | Transactional (small, fast, by key) vs. analytical (big scans and aggregates) workloads |
| Data warehouse | A managed database built for OLAP, usually columnar and massively parallel |
| Data lake | Cheap object storage (S3, GCS, ADLS) holding files, often Parquet |
| Lakehouse | A lake plus an open table format (Iceberg, Delta, Hudi) that adds tables, transactions and time travel |
| ETL / ELT | Extract-Transform-Load vs. Extract-Load-then-Transform inside the warehouse |
| CDC | Change data capture: streaming every insert/update/delete out of a database's log |
| Partition / clustering | Physical organisation that lets a query skip files it does not need |
| Fact / dimension | Tables of events/measurements vs. tables of descriptive attributes ([chapter 2](02_data_modeling.md)) |
| Freshness / latency | How old the newest data in a table is |

## 1. Two workloads, two machines

| | OLTP | OLAP |
|---|---|---|
| Typical question | "Get order 812", "insert this payment" | "Revenue by country by week since 2021" |
| Rows touched per query | 1 to hundreds | Millions to billions |
| Columns touched | Most of the row | A few of many |
| Concurrency | Thousands of small queries per second | Tens to hundreds of large queries |
| Latency target | Milliseconds | Hundreds of milliseconds to minutes |
| Writes | Constant small inserts/updates, ACID per row | Bulk loads and merges, often appended in batches |
| Data shape | Normalised (3NF) to avoid update anomalies | Denormalised (star schema, wide tables) to avoid joins |
| Storage layout | Row-oriented pages (B-tree + heap) | Column-oriented files, compressed |
| History | Current state (old values overwritten) | Full history, often years |
| Examples | Postgres, MySQL, Oracle, SQL Server, DynamoDB, MongoDB, Spanner | Snowflake, BigQuery, Redshift, Databricks SQL, ClickHouse, Druid, Pinot, DuckDB |

The normalised OLTP schema is covered from first principles in
[Normalization and Denormalization](../../data-and-apis/SQL/16_normalization_and_denormalization.md);
the reasons OLTP engines use B-trees and a write-ahead log are in
[Database Internals: How They Actually Work](../../interview-core/SystemDesign/building_blocks/06_database_internals.md).

### Why not one database for both?

1. **Resource contention.** A full-table scan evicts the hot working set from the
   buffer cache and saturates disk bandwidth. The app's p99 latency goes up for as long
   as the report runs.
2. **Locking and MVCC side effects.** A long-running read transaction in Postgres holds
   back `VACUUM`: dead row versions cannot be removed while an old snapshot might still
   need them, so tables and indexes bloat
   ([Transactions and Isolation Levels](../../data-and-apis/SQL/09_transactions_and_isolation_levels.md)).
3. **Wrong physical layout.** Row storage reads every column of every row it scans.
   §2 shows why that costs 10× or more for analytical queries.
4. **Wrong shape.** The OLTP schema has no history (an `UPDATE` overwrites the old city)
   and needs many joins; the analytical copy wants history and few joins.

### The first step people take: a read replica

Pointing BI at a **read replica** fixes contention with the primary, and for a small
company it is often the right answer for a while. Its limits show up as the data grows:
the replica still has row storage, still the OLTP schema, still no history, and a very
long query on a streaming replica either gets cancelled ("canceling statement due to
conflict with recovery") or, with `hot_standby_feedback = on`, bloats the primary
instead ([Replication and High Availability](../../data-and-apis/SQL/17_replication_and_high_availability.md)).

### HTAP: one system, two engines

**HTAP** (hybrid transactional/analytical processing) systems keep a row store for
writes and a columnar copy for analytics, inside one product: TiDB (TiKV + TiFlash),
SingleStore, AlloyDB's columnar engine, Oracle's in-memory column store, SQL Server
columnstore indexes. They remove a pipeline for fresh operational analytics, but they
do not replace a warehouse that joins data from dozens of sources and keeps years of
modeled history.

## 2. Row vs. column storage

This is the single most important physical idea in analytics.

```arch
%% caption: The same three orders stored two ways. A row store keeps each order together; a column store keeps each column together, so a query that needs two columns reads two runs of bytes.
grid 170x95
group rs "Row store" color=amber icon=table
node r1 "812 | ana | DE | 42.00 | paid" at 0,0 in rs shape=box w=250
node r2 "813 | bo | US | 9.50 | paid" at 0,1 in rs shape=box w=250
node r3 "814 | cy | DE | 18.00 | refunded" at 0,2 in rs shape=box w=250
group cs "Column store" color=blue icon=layers
node c1 "id: 812, 813, 814" at 2,0 in cs shape=box w=220
node c2 "country: DE, US, DE" at 2,1 in cs shape=box color=green w=220
node c3 "amount: 42.00, 9.50, 18.00" at 2,2 in cs shape=box color=green w=220
node c4 "status: paid, paid, refunded" at 2,3 in cs shape=box w=220
```

A query like `SELECT country, SUM(amount) FROM orders GROUP BY country` needs two
columns. A row store must read all columns of all rows to find them; a column store
reads only the `country` and `amount` regions (green above).

### Why columns win for analytics

1. **Less I/O.** Read only the columns the query names. Warehouses bill and slow down
   by bytes scanned, so `SELECT *` on a 200-column table is the most expensive habit
   in analytics.
2. **Better compression.** A column holds values of one type with lots of repetition,
   so encodings work well:
   - **Dictionary encoding**: store each distinct string once, then small integer codes.
   - **Run-length encoding (RLE)**: `DE, DE, DE, DE` becomes `(DE, 4)`. Works best on
     sorted or clustered data.
   - **Delta encoding**: store differences between neighbouring values (timestamps,
     ids).
   - **Bit-packing**: a column whose values fit in 5 bits uses 5 bits, not 64.
   Typical warehouse tables compress several times over; the exact ratio depends
   entirely on the data.
3. **Vectorised execution.** Engines process a batch of a few thousand values of one
   column at a time in tight loops that suit CPU caches and SIMD instructions,
   instead of interpreting one row at a time.
4. **Late materialisation.** Filter on the compressed `country` column first, then
   fetch `amount` only for the matching positions.

### Why columns lose for OLTP

Inserting one order means touching every column file; updating one field means
rewriting a compressed block. Columnar engines therefore write in **batches** and
merge in the background (ClickHouse's MergeTree parts, Snowflake's immutable
micro-partitions, Parquet files that are never modified in place). That is fine for
loading a million rows a minute, and terrible for a thousand single-row updates a
second.

### Seeing it on your laptop

This script stores 200,000 synthetic orders both ways and compresses each with zlib.
It runs with only the standard library.

```python
import random, zlib, json

random.seed(7)
N = 200_000
countries = ["US", "DE", "IN", "BR", "JP", "GB", "FR", "CA"]
rows = [
    {
        "order_id": 10_000_000 + i,
        "customer_id": random.randint(1, 50_000),
        "country": random.choice(countries),
        "status": random.choice(["paid", "paid", "paid", "refunded", "cancelled"]),
        "amount_cents": random.randint(100, 50_000),
        "note": "".join(random.choices("abcdefghijklmnopqrstuvwxyz ", k=40)),
    }
    for i in range(N)
]

# Row layout: each record stored contiguously (like a heap page in Postgres).
row_bytes = "\n".join(json.dumps(r, separators=(",", ":")) for r in rows).encode()

# Column layout: each column stored contiguously (like a Parquet column chunk).
cols = {k: [r[k] for r in rows] for k in rows[0]}
col_bytes = {k: "\n".join(map(str, v)).encode() for k, v in cols.items()}

def z(b):
    return len(zlib.compress(b, 6))

print(f"row layout, all columns     : {len(row_bytes)/1e6:6.1f} MB raw, {z(row_bytes)/1e6:5.1f} MB compressed")
total_col = sum(z(b) for b in col_bytes.values())
print(f"column layout, all columns  : {sum(map(len, col_bytes.values()))/1e6:6.1f} MB raw, {total_col/1e6:5.1f} MB compressed")
need = ["country", "amount_cents"]   # SELECT country, SUM(amount_cents) ... GROUP BY country
read = sum(z(col_bytes[k]) for k in need)
print(f"query reads 2 of 6 columns  : {read/1e6:5.2f} MB compressed ({read/z(row_bytes):.0%} of the row-store bytes)")
# Sorting a low-cardinality column makes runs, which compress to almost nothing.
srt = "\n".join(sorted(cols["country"])).encode()
print(f"country column unsorted     : {z(col_bytes['country'])/1e3:6.1f} KB; sorted: {z(srt)/1e3:5.1f} KB")
```

Output on one run:

```text
row layout, all columns     :   29.1 MB raw,   8.6 MB compressed
column layout, all columns  :   14.3 MB raw,   6.9 MB compressed
query reads 2 of 6 columns  :  0.63 MB compressed (7% of the row-store bytes)
country column unsorted     :  118.2 KB; sorted:   0.6 KB
```

The row layout here is inflated by repeated JSON keys, so do not read too much into
the first two lines. The last two are the lesson: a two-column query reads a small
fraction of the bytes, and **sorting a low-cardinality column shrinks it by orders of
magnitude**, which is exactly why warehouses let you choose a sort or clustering key
(§4). A real format such as Parquet does better still, with type-aware encodings in
place of generic zlib.

### Parquet, the file format of the lake

**Apache Parquet** is the default columnar file format for data lakes and the
interchange format between Spark, Trino, DuckDB, Snowflake, BigQuery and pandas.

```arch
%% caption: A Parquet file is split into row groups; each row group holds one column chunk per column, split into pages; the footer stores the schema and min/max statistics used to skip data.
grid 150x100
group f "orders-00017.parquet" color=blue icon=file
node rg1 "Row group 1" at 0.5,0 in f shape=card icon=layers sub="≈128 MB of rows"
node foot "Footer" at 2,0 in f shape=card icon=doc sub="schema + stats"
node cc1 "Chunk: country" at 0,1 in f shape=card icon=table sub="dict + RLE pages"
node cc2 "Chunk: amount" at 1,1 in f shape=card icon=table sub="delta pages"
node st "min/max per chunk" at 2,1 in f shape=card icon=filter sub="lets readers skip"
node rg2 "Row groups 2..N" at 0.5,2 in f shape=card icon=layers sub="same structure"
rg1:B -> cc1:T
rg1:B -> cc2:T
foot:B -> st:T
```

- A file holds **row groups** (commonly ≈128 MB each when written by Spark); each row
  group holds one **column chunk** per column; each chunk is split into **pages**
  (≈1 MB) that carry the actual encoded values.
- The **footer** stores the schema and, per column chunk, min/max values and null
  counts. A reader first reads the footer, then:
  - **projection pushdown**: reads only the column chunks the query needs;
  - **predicate pushdown**: skips a whole row group when, say, `max(order_date)` is
    before the date in the `WHERE` clause.
- Parquet supports nested types (structs, lists, maps).
- **ORC** is a similar columnar format from the Hive world; **Apache Arrow** is the
  matching *in-memory* columnar format that lets engines and languages hand data to
  each other without re-serialising it.

## 3. Inside a cloud data warehouse

Modern warehouses share three design ideas:

1. **Massively parallel processing (MPP).** A query is split into fragments that run
   on many nodes at once; each scans part of the data, and partial results are
   exchanged (shuffled) and merged, much like the Spark stages in
   [chapter 3](03_batch_processing_spark.md).
2. **Separation of storage and compute.** Data lives in cheap, durable object storage;
   compute clusters are started, resized and stopped independently. Two teams can
   query the same tables on two separate clusters without slowing each other down, and
   you pay for compute only while it runs.
3. **Immutable columnar files plus metadata.** Tables are sets of immutable compressed
   files with statistics; the service keeps the list of which files make up the table
   right now, which gives cheap snapshots, time travel and zero-copy clones.

```arch
%% caption: Storage and compute are separate. Several independent compute clusters read the same columnar files in object storage; a shared metadata service knows which files make up each table.
grid 170x110
node users "Analysts and jobs" at 1,0 icon=users
group svc "Cloud services layer" color=purple icon=cloud
node meta "Metadata + optimizer" at 1,1 in svc icon=index sub="file lists, stats, security"
group comp "Independent compute clusters" color=amber icon=cpu
node wh1 "BI cluster" at 0,2 in comp icon=server sub="small, always on"
node wh2 "ETL cluster" at 1,2 in comp icon=server sub="large, scheduled"
node wh3 "Data science" at 2,2 in comp icon=server sub="auto-suspends"
node obj "Object storage" at 1,3 icon=storage sub="columnar files, shared"
users -> meta
meta -> wh1
meta -> wh2
meta -> wh3
wh1 -> obj
wh2 -> obj
wh3 -> obj
```

| | Snowflake | BigQuery | Redshift | Databricks SQL |
|---|---|---|---|---|
| Storage | Proprietary micro-partitions (≈50–500 MB uncompressed each) in object storage; can also read/write Iceberg | Capacitor columnar format on Colossus; BigLake/Iceberg tables | Managed storage on RA3/Serverless; Spectrum reads S3 | Delta Lake (and Iceberg via UniForm) on your object storage |
| Compute | Virtual warehouses (T-shirt sizes), per-second billing with a 60 s minimum | Serverless "slots"; on-demand or capacity (editions) pricing | Provisioned clusters or Serverless (RPUs) | SQL warehouses (serverless or classic) |
| Physical tuning | Clustering keys; automatic clustering service | Partitioning + clustering | Distribution key + sort key | Partitioning, liquid clustering, Z-order |
| Billing gotcha | Warehouse left running; oversized warehouse | On-demand bills bytes scanned (≈$6.25 per TiB list price in US regions) | Idle provisioned clusters | Always-on clusters |

**Precision note:** pricing numbers change; quote the *model* (bytes scanned vs.
compute time) in an interview, not a figure.

### Real-time OLAP engines

For **user-facing analytics** (a dashboard inside your product that thousands of
customers load, needing sub-second answers on data seconds old) teams use **ClickHouse,
Apache Druid, Apache Pinot or StarRocks**. They ingest straight from Kafka, pre-sort
and index aggressively, and trade flexibility (fewer big joins, more denormalised
tables) for predictable low latency at high concurrency. **DuckDB** is the opposite
end: an embedded, in-process columnar engine, excellent for local analysis of Parquet
files and for small pipelines.

## 4. Partitioning, clustering and pruning

The cheapest byte is the one you never read. Warehouses skip data at two levels:

- **Partitioning** splits a table into separately stored pieces by a column, almost
  always a date. A query with `WHERE order_date = '2026-09-27'` opens one partition.
- **Clustering / sort keys** order rows inside partitions, so per-file min/max
  statistics become tight and most files can be skipped for a filter on the cluster
  column.

```sql
-- BigQuery: daily partitions, clustered by the most common filters.
CREATE TABLE shop.fact_orders (
  order_id     STRING,
  customer_id  STRING,
  country      STRING,
  order_ts     TIMESTAMP,
  amount       NUMERIC
)
PARTITION BY DATE(order_ts)
CLUSTER BY country, customer_id
OPTIONS (require_partition_filter = TRUE);  -- refuse queries that would scan every day

-- Snowflake: tables are micro-partitioned automatically; a clustering key keeps
-- large tables well sorted on the columns you filter by.
ALTER TABLE fact_orders CLUSTER BY (order_date, country);

-- Redshift: co-locate join keys on the same node, sort for range filters.
CREATE TABLE fact_orders (
  order_id    BIGINT,
  customer_id BIGINT,
  order_date  DATE,
  amount      DECIMAL(12,2)
)
DISTSTYLE KEY DISTKEY (customer_id)
SORTKEY (order_date);

-- ClickHouse: the ORDER BY key is the sparse primary index.
CREATE TABLE fact_orders (
  order_id    UInt64,
  country     LowCardinality(String),
  order_date  Date,
  amount      Decimal(12, 2)
) ENGINE = MergeTree
PARTITION BY toYYYYMM(order_date)
ORDER BY (country, order_date);
```

Rules of thumb:

- Partition by the column nearly every query filters on (event or order date), at a
  granularity that keeps partitions reasonably large. Thousands of tiny partitions
  cost more metadata than they save.
- Cluster/sort by the next most selective filter columns, low to medium cardinality
  first.
- Wrapping the partition column in a function in the `WHERE` clause can defeat
  pruning in some engines; filter on the column directly.
- **The small-files problem.** A streaming job writing a file per partition per
  minute produces millions of tiny files; every query then spends its time opening
  files and reading footers. Compact them into files of ≈128 MB–1 GB.

## 5. Data lakes and the lakehouse

A **data lake** is just files in object storage (S3, GCS, Azure Data Lake Storage),
usually Parquet, organised in folders like `s3://lake/orders/date=2026-09-27/`. It is
cheap, holds any format (including images and logs), and any engine can read it. The
problems appear once many jobs share it:

- **No transactions.** A reader listing a folder while a job rewrites it sees half the
  new files and half the old ones.
- **No safe updates or deletes.** GDPR "delete user 42" means rewriting every file that
  contains that user, by hand.
- **Schema drift.** One job adds a column; another writes a string where an int was.
- **Slow listing.** Planning a query by listing millions of objects is slow and
  expensive.

**Open table formats** fix this by adding a metadata layer on top of the Parquet files:
**Apache Iceberg**, **Delta Lake** and **Apache Hudi**. The result, a lake that
behaves like warehouse tables, is called a **lakehouse**.

### How Apache Iceberg works

```arch
%% caption: An Iceberg table is a tree of metadata. A commit writes new files and then atomically swaps the catalog pointer to a new metadata file; readers always see one complete snapshot.
grid 190x95
node cat "Catalog" at 1,0 icon=index sub="table -> current metadata"
node md "metadata.json v42" at 1,1 icon=doc sub="schema, partitions, snapshots"
node ml "Manifest list" at 1,2 icon=file sub="one per snapshot"
node m1 "Manifest A" at 0.5,3 icon=file sub="files + column stats"
node m2 "Manifest B" at 2,3 icon=file sub="files + column stats"
node d1 "data-001.parquet" at 0,4 icon=blob
node d2 "data-002.parquet" at 1,4 icon=blob
node d3 "data-003.parquet" at 2,4 icon=blob
cat -> md : "atomic swap"
md -> ml
ml -> m1
ml -> m2
m1 -> d1
m1 -> d2
m2 -> d3
```

1. A writer writes new Parquet data files, then new manifest files listing them (with
   per-file column statistics), then a manifest list and a new `metadata.json`.
2. It **commits** by asking the catalog to swap the table's pointer from `v41` to `v42`
   atomically (compare-and-swap). If another writer committed first, it retries on
   top of the new version (optimistic concurrency).
3. Readers load the current metadata and get a consistent **snapshot**: the exact set
   of files, with stats for pruning, and no directory listing.

What that buys you:

| Feature | How |
|---|---|
| ACID commits | Atomic metadata-pointer swap |
| Time travel | Old snapshots stay until expired: `FOR TIMESTAMP AS OF '2026-09-01 00:00:00'` |
| Schema evolution | Columns tracked by id, so rename and add are metadata-only |
| Hidden partitioning | Partition by `days(order_ts)`; queries filter on `order_ts` and still prune |
| Row-level deletes/updates | Copy-on-write (rewrite files) or merge-on-read (delete files / deletion vectors applied at read) |

```sql
-- Spark SQL with an Iceberg catalog named "lake".
CREATE TABLE lake.sales.orders (
  order_id    BIGINT,
  customer_id BIGINT,
  order_ts    TIMESTAMP,
  amount      DECIMAL(12, 2)
) USING iceberg
PARTITIONED BY (days(order_ts));

SELECT count(*) FROM lake.sales.orders FOR TIMESTAMP AS OF '2026-09-01 00:00:00';

-- Housekeeping every lakehouse needs on a schedule:
CALL lake.system.rewrite_data_files(table => 'sales.orders');           -- compact small files
CALL lake.system.expire_snapshots(table => 'sales.orders',
                                  older_than => TIMESTAMP '2026-09-21 00:00:00');
```

**Copy-on-write vs. merge-on-read.** Copy-on-write rewrites every data file touched
by an update: slow writes, fast reads. Merge-on-read writes small delete files and
merges them at query time: fast writes (good for CDC), slower reads until compaction
runs. Both Iceberg and Delta support both; Hudi was built around the choice.

**Catalogs** matter as much as the format: the Iceberg REST catalog protocol is now
the common interface, implemented by Apache Polaris, Unity Catalog, AWS Glue, Snowflake
and others, and managed offerings such as Amazon S3 Tables keep Iceberg tables
compacted for you. As of 2026 Iceberg is the format most engines agree on; Delta is
native to Databricks and can expose Iceberg metadata through UniForm.

### The medallion layers

Most lakehouses (and warehouses) organise tables in layers. Names vary; the idea is
the same.

| Layer | Also called | Contents | Rule |
|---|---|---|---|
| Bronze | raw, landing | Exact copy of the source, append-only, with load metadata | Never edit; this is what you replay from |
| Silver | staging, clean | Typed, deduplicated, renamed, conformed | One row per real thing; tests live here |
| Gold | marts, presentation | Facts and dimensions, aggregates for a business area | Modeled for readers ([chapter 2](02_data_modeling.md)) |

## 6. ETL vs. ELT

Data is useless while it is trapped in isolated OLTP databases and SaaS tools. The
pipeline that moves it has two historical shapes.

- **ETL (Extract, Transform, Load)**: the older shape. A dedicated server or tool
  (Informatica, SSIS, custom scripts) extracts data from Postgres, transforms it
  (cleans, joins, aggregates) in its own memory, and *then* loads only the finished
  tables into the warehouse. It made sense when warehouse compute was expensive and
  fixed-size. It needs separate transformation servers, and the raw data is not kept.
- **ELT (Extract, Load, Transform)**: the modern default. Extract raw data and load it
  directly into the warehouse or lake, then use the warehouse's own elastic compute to
  transform raw tables into clean ones with SQL (usually managed by dbt,
  [chapter 6](06_data_transformation_dbt.md)).

```arch
%% caption: The modern ELT pipeline extracts raw data, loads it into the warehouse, and then transforms it in place using the warehouse's parallel compute.
grid 170x100
node pg "Postgres" at 0,0 icon=postgresql sub="OLTP"
node kafka "Kafka" at 2,0 icon=kafka-icon sub="events"
group bq "BigQuery (OLAP)" color=slate style=dashed icon=layers
node raw "Raw layer" at 1,1 in bq icon=archive
node clean "Clean layer" at 1,2 in bq icon=filter
node agg "Aggregations" at 1,3 in bq icon=dashboard
pg -> raw : "extract + load"
kafka -> raw : "extract + load"
raw -> clean : "transform"
clean -> agg : "transform"
```

| | ETL | ELT |
|---|---|---|
| Where transforms run | Separate engine before loading | Inside the warehouse/lakehouse after loading |
| Raw data kept? | Usually not | Yes, so you can re-transform when logic changes |
| Who writes transforms | Specialist ETL developers, GUI tools | Analytics engineers in SQL + git (dbt) |
| Good for | Heavy non-SQL processing, PII that must be removed before landing | Most analytics in 2026 |
| Risk | Rigid; a logic bug means re-extracting | Warehouse bill grows; raw layer may hold sensitive data |

Two related shapes you will hear about:

- **Reverse ETL** copies modeled data *back out* of the warehouse into operational
  tools (lead scores into the CRM, audiences into an ad platform). Hightouch and Census
  are the usual tools.
- **Zero-ETL** is a vendor feature that replicates an operational database into the
  warehouse without a pipeline you run (Aurora to Redshift, AlloyDB/Spanner to
  BigQuery). It is CDC operated for you.

**PII note.** ELT lands raw data, including personal data, in the warehouse. Mask or
tokenise sensitive columns at ingestion or in the first transform, restrict the raw
layer, and make deletions reachable (GDPR/CCPA). "We keep raw forever" collides with
"delete user 42 within 30 days".

## 7. Getting data out of OLTP: batch extracts vs. CDC

### Full extract

`SELECT * FROM orders` every night, then replace the warehouse copy. Simple and always
consistent with the source, and fine for small tables. It gets slower and more
expensive every day and puts a big scan on the source.

### Incremental extract with a high-water mark

Remember the largest `updated_at` you copied and next time ask for rows changed after
it. Cheap, and it has two classic bugs, both reproduced here with SQLite:

```python
import sqlite3

src = sqlite3.connect(":memory:")   # the OLTP database
src.execute("CREATE TABLE orders (id INTEGER PRIMARY KEY, status TEXT, updated_at TEXT)")
src.executemany("INSERT INTO orders VALUES (?, ?, ?)", [
    (1, "paid", "2026-09-28 10:00:00"),
    (2, "paid", "2026-09-28 10:00:05"),
    (3, "paid", "2026-09-28 10:00:09"),
])

warehouse = {}                       # id -> row, what the analytics side holds
high_water = "1970-01-01 00:00:00"

def extract():
    """Incremental extract: fetch rows changed since the last high-water mark."""
    global high_water
    rows = src.execute(
        "SELECT id, status, updated_at FROM orders WHERE updated_at > ? ORDER BY updated_at",
        (high_water,)).fetchall()
    for r in rows:
        warehouse[r[0]] = r
    if rows:
        high_water = rows[-1][2]
    return len(rows)

print("run 1 copied", extract(), "rows; high-water mark =", high_water)

# A transaction that STARTED at 10:00:07 stamps updated_at when it runs its UPDATE,
# but only COMMITS after run 1 has finished. Its timestamp is below the mark.
src.execute("UPDATE orders SET status='refunded', updated_at='2026-09-28 10:00:07' WHERE id=1")
# A hard delete leaves nothing behind to select.
src.execute("DELETE FROM orders WHERE id=2")

print("run 2 copied", extract(), "rows")
print("source   :", src.execute("SELECT id, status FROM orders ORDER BY id").fetchall())
print("warehouse:", sorted((k, v[1]) for k, v in warehouse.items()))
```

```text
run 1 copied 3 rows; high-water mark = 2026-09-28 10:00:09
run 2 copied 0 rows
source   : [(1, 'refunded'), (3, 'paid')]
warehouse: [(1, 'paid'), (2, 'paid'), (3, 'paid')]
```

1. **Late commits are missed.** `updated_at` is set when the statement runs, but the
   row becomes visible at commit. A transaction that was in flight during the extract
   commits later with a timestamp *below* the mark, and is never copied. The usual
   patch is to re-read a lookback window (`updated_at > high_water - interval '1 hour'`)
   and make the load an idempotent `MERGE`, which narrows the gap without closing it.
2. **Hard deletes are invisible.** There is no row left to select. You need soft
   deletes (`deleted_at`), a periodic full key comparison, or CDC.

It also depends on every writer remembering to update `updated_at` (a trigger helps)
and on an index on that column.

### Log-based change data capture (CDC)

Every OLTP database already writes an ordered log of every committed change (the
Postgres WAL, the MySQL binlog, the MongoDB oplog) so replicas can follow it. **CDC
reads that log** and turns each committed change into an event, in commit order,
including deletes, without querying the tables.

```arch
%% caption: Log-based CDC. Debezium reads committed changes from the Postgres WAL through a replication slot, publishes one event per row change to Kafka, and sinks apply them to the lakehouse with an idempotent MERGE.
grid 165x110
group oltp "App side" color=blue icon=app
node app "Order service" at 0,0 in oltp icon=service
node pg "Postgres primary" at 0,1 in oltp icon=postgresql sub="wal_level=logical"
node slot "Replication slot" at 0,2 in oltp icon=logs sub="pgoutput, holds WAL"
group pipe "Kafka Connect" color=purple icon=stream
node dbz "Debezium" at 1,2 in pipe icon=worker sub="source connector"
node topic "Kafka topic" at 2,2 in pipe icon=kafka-icon sub="shop.public.orders"
node reg "Schema registry" at 1,3 in pipe icon=doc sub="Avro / Protobuf"
group ana "Analytics" color=green icon=layers
node sink "Sink job" at 3,2 in ana icon=worker sub="Flink / Spark / connector"
node lake "Iceberg table" at 3,1 in ana icon=table sub="MERGE by key + LSN"
app -> pg : "INSERT / UPDATE"
pg -> slot : "WAL"
slot -> dbz : "logical decoding"
dbz -> topic
dbz ..> reg
topic -> sink
sink -> lake
```

How it works with Postgres and Debezium:

```sql
-- On the source database (wal_level needs a restart to take effect).
ALTER SYSTEM SET wal_level = logical;
CREATE PUBLICATION dbz_shop FOR TABLE public.orders, public.customers;
-- Send full old row images for updates/deletes if consumers need them:
ALTER TABLE public.orders REPLICA IDENTITY FULL;

-- The query to alert on: how much WAL is each slot holding back?
SELECT slot_name, active,
       pg_size_pretty(pg_wal_lsn_diff(pg_current_wal_lsn(), confirmed_flush_lsn)) AS retained
FROM pg_replication_slots;
```

```json
{
  "name": "shop-orders-cdc",
  "config": {
    "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
    "database.hostname": "orders-db.internal",
    "database.port": "5432",
    "database.user": "debezium",
    "database.password": "${file:/opt/kafka/secrets/pg.properties:password}",
    "database.dbname": "shop",
    "topic.prefix": "shop",
    "plugin.name": "pgoutput",
    "slot.name": "debezium_shop",
    "publication.name": "dbz_shop",
    "table.include.list": "public.orders,public.customers",
    "snapshot.mode": "initial"
  }
}
```

Each change becomes an event with the row **before** and **after**, the operation
(`c` create, `u` update, `d` delete, `r` snapshot read), and source metadata such as the
log position (LSN) and commit time:

```json
{
  "before": {"id": 812, "status": "paid", "amount": 4200},
  "after":  {"id": 812, "status": "refunded", "amount": 4200},
  "op": "u",
  "ts_ms": 1790589607412,
  "source": {"db": "shop", "table": "orders", "lsn": 2398475520, "txId": 88121}
}
```

The Kafka message key is the row's primary key, so all changes to one row land in one
partition, in order. A delete is followed by a **tombstone** (key with a null value) so
log compaction can eventually drop the key.

**Initial snapshot, then stream.** A new connector first copies existing rows
(`snapshot.mode=initial`), then streams from the log position where the snapshot
started, so nothing is missed in between. Debezium's **incremental snapshots**
(based on Netflix's DBLog watermarking idea) re-snapshot a table in chunks while
streaming continues, which is how you backfill a table added later.

**Applying CDC to the warehouse.** Deduplicate to the latest change per key, then
`MERGE`, guarding with the log position so a replayed old event cannot overwrite a
newer one:

```sql
MERGE INTO analytics.orders AS t
USING (
  SELECT *
  FROM staging.orders_cdc
  QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY source_lsn DESC) = 1
) AS s
ON t.id = s.id
WHEN MATCHED AND s.op = 'd' THEN DELETE
WHEN MATCHED AND s.source_lsn > t.source_lsn THEN
  UPDATE SET status = s.status, amount = s.amount, source_lsn = s.source_lsn
WHEN NOT MATCHED AND s.op <> 'd' THEN
  INSERT (id, status, amount, source_lsn) VALUES (s.id, s.status, s.amount, s.source_lsn);
```

(`QUALIFY` works in Snowflake, BigQuery and Databricks; elsewhere wrap the window
function in a subquery.) Many teams also keep the full change history as an
append-only table, which gives SCD Type 2 history almost for free
([chapter 2](02_data_modeling.md)).

### CDC failure modes you should be able to name

| Symptom | Cause | Fix |
|---|---|---|
| Source disk fills up, primary goes down | A replication slot whose consumer stopped keeps all WAL since its position | Alert on retained WAL per slot; set `max_slot_wal_keep_size` (Postgres 13+) so a dead slot is invalidated instead; drop abandoned slots |
| Updates arrive with missing columns | Postgres TOAST: unchanged large values are not in the log | `REPLICA IDENTITY FULL`, or have the sink keep the old value |
| Pipeline breaks after a deploy | Source schema changed (column dropped or retyped) | Schema registry with compatibility rules, schema-change alerts, data contracts |
| Failover loses the stream position | Logical slots did not exist on the new primary | Postgres 17 failover slots (`failover = true` + slot sync) or a re-snapshot runbook |
| Totals double-count | Sink is at-least-once and appends | Idempotent `MERGE` keyed by primary key + LSN |
| Cross-table order looks wrong | Order is guaranteed per key/partition, not across topics | Use transaction metadata, or model with event time |

When the event is a *business* fact ("order placed") rather than a row change, use the
**transactional outbox** instead: write the event into an `outbox` table in the same
transaction and let CDC publish it. That decouples the published contract from the
table layout ([Messaging and Streaming](../../interview-core/SystemDesign/building_blocks/09_messaging_and_streaming.md)).
Kafka itself (partitions, consumer groups, KRaft) is covered in
[Kafka and Event Streaming](../Tool-Kit/04_kafka_and_event_streaming.md).

<div class="lab" data-viz="flow-cdc-pipeline"></div>

## 8. Choosing where analytical data lives

| Situation | Reasonable choice |
|---|---|
| Startup, one Postgres, a few dashboards | A read replica or a nightly copy into DuckDB/Postgres; a managed warehouse once queries hurt |
| Many sources, SQL-first analysts, little infra appetite | Snowflake or BigQuery with ELT (Fivetran/Airbyte + dbt) |
| Big raw volume, Spark/ML workloads, many engines, avoid lock-in | Lakehouse: object storage + Iceberg/Delta + Spark/Trino, a warehouse reading the same tables |
| Customer-facing dashboards, sub-second, high concurrency | ClickHouse, Pinot, Druid or StarRocks fed from Kafka |
| Fresh operational analytics on one database | HTAP (TiDB, AlloyDB columnar) or CDC into a real-time OLAP store |

The question behind all of them: *how fresh, how big, how many concurrent readers, and
who writes the transforms?*

## Common interview questions

**Why are analytical databases columnar?**
Analytical queries read few columns of many rows. Columnar storage reads only those
columns, compresses them well because each column has one type and lots of repetition,
and lets the engine run vectorised loops over batches of values. The cost is slow
single-row inserts and updates, so columnar stores load in batches.

**ETL or ELT, and why did the industry move?**
ELT: load raw data first, transform inside the warehouse with SQL. Cloud warehouses
made compute elastic and cheap enough, keeping raw data allows re-transformation when
logic changes, and SQL in git (dbt) is easier to staff and review than GUI ETL. ETL
still fits heavy non-SQL processing and data that must be scrubbed before it lands.

**How would you get data from a production Postgres into the warehouse?**
Small tables: nightly full copy. Large tables: log-based CDC (Debezium reading logical
replication through a slot, into Kafka, merged into the warehouse by primary key and
LSN). Mention the initial snapshot, deletes, schema changes, and alerting on the
replication slot's retained WAL.

**What goes wrong with `updated_at > last_run` extraction?**
It misses hard deletes, misses transactions that commit after the extract with a
timestamp below the mark, depends on every writer maintaining the column, and scans
the source. Mitigate with a lookback window and idempotent merge, or switch to CDC.

**What is a lakehouse, and what does Iceberg add over Parquet files?**
Object storage plus a table format. Iceberg keeps a metadata tree (metadata file,
manifest list, manifests with per-file stats) and commits by atomically swapping a
catalog pointer, which gives ACID commits, snapshots and time travel, schema evolution,
hidden partitioning and row-level deletes, without listing directories.

**How do partitioning and clustering reduce cost?**
They let the engine skip data. Partition pruning skips whole partitions from the
`WHERE` clause; clustering keeps rows sorted so per-file min/max stats exclude most
files. On bytes-scanned pricing that is a direct cost cut.

**Why not run analytics on a read replica?**
It works early on. Later: still row storage and OLTP schema, no history, long queries
get cancelled by replication conflicts or bloat the primary through
`hot_standby_feedback`, and it cannot join data from other sources.

**What is the small-files problem?**
Too many small files (often from streaming writes or over-partitioning) make planning
and reading dominated by per-file overhead. Fix with fewer partitions, larger write
batches, and scheduled compaction.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student / Intern | Intern, new learner | — | OLTP vs. OLAP in plain words; why you don't run reports on the app database; what a warehouse is; ETL vs. ELT as terms |
| Junior | Data Engineer I / Junior Analytics Engineer | L3 | Row vs. column storage and why columns win for scans; partition filters in queries; avoiding `SELECT *`; loading a table with an idempotent merge; what Parquet is |
| Mid | Data Engineer II | L4 | Designs partitioning/clustering for a table; builds incremental extracts and knows their delete/late-commit bugs; runs a Debezium CDC pipeline; knows medallion layers and warehouse cost models |
| Senior | Senior Data Engineer | L5 | Explains Parquet internals and pushdown, Iceberg commits and copy-on-write vs. merge-on-read; handles CDC failure modes (slot WAL retention, TOAST, schema change, failover); chooses warehouse vs. lakehouse vs. real-time OLAP with reasons |
| Staff+ | Staff / Principal Data Engineer, Data Architect | L6+ | Sets platform direction (open table formats and catalogs, one copy of data for many engines); owns cost and governance (PII, deletion, access); designs freshness and correctness SLAs across dozens of teams and sources |

## Interview checklist

- [ ] I can contrast OLTP and OLAP on query shape, concurrency, layout, schema and history.
- [ ] I can explain why columnar storage compresses well and reads less, and why it is bad at single-row updates.
- [ ] I can describe a Parquet file (row groups, column chunks, pages, footer stats) and projection/predicate pushdown.
- [ ] I can explain storage/compute separation and name how Snowflake, BigQuery and Redshift bill.
- [ ] I can write partitioned and clustered DDL and explain pruning.
- [ ] I can explain what Iceberg/Delta add to a data lake and how an Iceberg commit works.
- [ ] I can compare ETL, ELT, reverse ETL and zero-ETL.
- [ ] I can name the two bugs of high-water-mark extraction and how CDC avoids them.
- [ ] I can sketch a Debezium CDC pipeline and name its failure modes, especially replication-slot WAL retention.
- [ ] I can write an idempotent `MERGE` that applies CDC events safely.

Related: [Batch and Stream Processing](../../interview-core/SystemDesign/building_blocks/21_batch_and_stream_processing.md),
[Object Storage](../../interview-core/SystemDesign/building_blocks/08_object_storage.md),
[Databases: Source of Truth](../../interview-core/SystemDesign/building_blocks/05_databases.md),
[Replication and High Availability](../../data-and-apis/SQL/17_replication_and_high_availability.md),
[Choosing a Database, and CAP Theorem Applied](../../data-and-apis/NoSQL/concepts/01_choosing_a_database_and_cap_theorem.md).
