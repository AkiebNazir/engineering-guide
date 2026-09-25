# <abbr title="Not Only SQL - A broad class of database management systems that differ from the classic relational model, designed for distributed data stores.">NoSQL</abbr> — Document and Key-Value Stores, Hands-On

This module teaches <abbr title="Not Only SQL - A broad class of database management systems that differ from the classic relational model, designed for distributed data stores.">NoSQL</abbr> databases the same way `SQL/` teaches PostgreSQL: hands-on,
against real local databases, with every claim that can be measured (a timing number, a
row count, an actual command's output) measured on this machine and reported honestly —
never asserted from memory. It uses **MongoDB** for the document model and **Redis** for
the key-value/cache model. Every hands-on level's client-code demos are shown in **both
Python and Go**, side by side.

## The <abbr title="Not Only SQL - A broad class of database management systems that differ from the classic relational model, designed for distributed data stores.">NoSQL</abbr> landscape, briefly

"<abbr title="Not Only SQL - A broad class of database management systems that differ from the classic relational model, designed for distributed data stores.">NoSQL</abbr>" isn't one thing — it's everything that isn't the relational model in `SQL/`,
and the four families below solve genuinely different problems. This module goes deep
on the first two, because between them they cover the concepts a working engineer needs
most; the other two are worth being able to recognize and place, even without a
dedicated module here.

| Family | Shape | What it's for | Examples |
|---|---|---|---|
| **Key-value** | An opaque value behind a key, usually in <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> | Sub-millisecond lookups, caching, sessions, counters, queues | **Redis**, Memcached, DynamoDB (as a KV store) |
| **Document** | Schema-flexible, nested <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr>-like documents | Data whose shape varies or nests naturally, fast iteration without a rigid schema | **MongoDB**, Couchbase, Elasticsearch (as a document store) |
| **Wide-column** | Rows with a huge, sparse, per-row-variable set of columns, partitioned for horizontal scale | Massive write-heavy workloads spread across many machines (time series, event logs) | Cassandra, HBase, Bigtable |
| **Graph** | Nodes and edges, queried by traversal | Data that's fundamentally about relationships — social graphs, fraud rings, recommendation paths | Neo4j, Amazon Neptune |

Why Mongo and Redis specifically: a document store and a key-value store are the two
you'll actually reach for or be asked about in most interviews and most real systems —
"we need a flexible schema and rich queries" (document) and "we need something faster
than the database in front of a hot path" (key-value/cache) are two of the most common
system-design pressures that push a team off pure relational. Wide-column and graph
solve narrower, scale- or shape-specific problems; graph is still covered at the
concept level in `SystemDesign/building_blocks/` only, but wide-column (Cassandra/
DynamoDB) gets a real design-level treatment in `concepts/` below, since it comes up
constantly in interviews — as a schema-design exercise rather than a hands-on lab
(no container for it in this repo's lab stack).

## Starting the lab environment

A `docker-compose.databases.yml` at the repo root brings up all three lab databases
(Postgres for `SQL/`, MongoDB, and Redis) on non-default host ports, so none of them
collide with anything you already run natively:

```bash
docker compose -f docker-compose.databases.yml up -d       # start (keeps data across restarts)
docker compose -f docker-compose.databases.yml down        # stop, keep data
docker compose -f docker-compose.databases.yml down -v     # stop, wipe data (fresh start)
```

**MongoDB** — host `localhost`, port **27018** (not Mongo's default 27017), no auth:

```bash
mongosh "mongodb://localhost:27018"
```

```python
from pymongo import MongoClient
client = MongoClient("mongodb://localhost:27018")
```

**Redis** — host `localhost`, port **6390** (not Redis's default 6379), no auth:

```bash
redis-cli -p 6390
# or, if you don't have a local redis-cli binary:
docker exec -it dsa-redis redis-cli
```

```python
import redis
r = redis.Redis(host="localhost", port=6390, decode_responses=True)
```

`NoSQL/requirements.txt` lists the Python packages every level's code needs
(`pymongo`, `redis`). Install them into whatever virtualenv you run the samples from:
`pip install -r NoSQL/requirements.txt`.

**Go.** Every hands-on level also shows Go client code: the official
`go.mongodb.org/mongo-driver/v2/mongo` for MongoDB, `github.com/redis/go-redis/v9` for
Redis. As with the Python side, no `.go` files are committed here — copy a snippet into
your own scratch module and run it:

```bash
mkdir nosql-lab && cd nosql-lab && go mod init nosql-lab
go get go.mongodb.org/mongo-driver/v2/mongo github.com/redis/go-redis/v9
```

(`concepts/00`'s DynamoDB snippet is the one exception — illustrative only, since there's
no DynamoDB container in this lab stack; it isn't meant to be run.)

Every level uses its own key prefix or its own scratch collection/database, and cleans
up its own state at the top of its code — you can run any level's examples
independently, in any order, without cleaning up after another level first.

## Roadmap

Both hands-on ladders are 12 levels (00–11), shaped the same way: start from the
storage engine's core mental model, build up through its native operations, then spend
the back half on the patterns and production concerns (indexing/caching, atomicity,
locking/concurrency, scaling the read path, durability, and a capstone client) that
actually show up in interviews and in real systems. A third, non-hands-on `concepts/`
set closes the module with wide-column/DynamoDB design, the cross-cutting <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>-vs-<abbr title="Not Only SQL - A broad class of database management systems that differ from the classic relational model, designed for distributed data stores.">NoSQL</abbr>
decision framework, and an interview playbook.

### MongoDB — the document model (`mongodb/`)

| # | Level | What you'll be able to do |
|---|---|---|
| 00 | [The Document Model](mongodb/00_the_document_model.md) | Explain documents/collections vs. rows/tables, and where a flexible schema helps or hurts |
| 01 | [Connecting and Your First Query](mongodb/01_connecting_and_first_query.md) | Connect via `mongosh` and Python `pymongo`; run a first query end to end |
| 02 | [CRUD Basics](mongodb/02_crud_basics.md) | Insert, find, update, and delete documents |
| 03 | [Query Operators and Projections](mongodb/03_query_operators_and_projections.md) | Filter with comparison/logical operators; shape results with projections |
| 04 | [Embedding vs. Referencing](mongodb/04_embedding_vs_referencing.md) | Decide when to nest data inside a document vs. link it by reference |
| 05 | [Indexes in MongoDB](mongodb/05_indexes_in_mongodb.md) | Build and measure indexes; read a query plan |
| 06 | [The Aggregation Pipeline](mongodb/06_aggregation_pipeline.md) | Build multi-stage aggregation pipelines for real reporting queries |
| 07–11 | *(the document-model equivalent of levels 00–11 below)* | Transactions and write concerns, schema validation and data modeling patterns at scale, replication and read scaling, durability, and a capstone `pymongo` client — written to the same spec shape as the Redis ladder |

### Redis — the key-value / cache model (`redis/`)

| # | Level | What you'll be able to do |
|---|---|---|
| 00 | [The Key-Value Model](redis/00_the_key_value_model.md) | Explain Redis's in-memory, single-threaded event-loop model and why it's fast |
| 01 | [Connecting and Your First Command](redis/01_connecting_and_first_command.md) | Connect via `redis-cli` and Python `redis-py`; `SET`/`GET`; key expiry basics |
| 02 | [Strings and Atomic Counters](redis/02_strings_and_counters.md) | `INCR`/`DECR`/`INCRBY` as race-free counters; `SETEX`/`GETEX` |
| 03 | [Hashes, Lists, and Sets](redis/03_hashes_lists_sets.md) | Model an object with a hash; a queue and a stack with lists; set algebra |
| 04 | [Sorted Sets and Leaderboards](redis/04_sorted_sets_and_leaderboards.md) | Build a real leaderboard: top-N, a player's rank, live score updates |
| 05 | [Caching Patterns](redis/05_caching_patterns.md) | Cache-aside vs. write-through vs. write-back; eviction policy; fix a cache stampede |
| 06 | [Pub/Sub](redis/06_pubsub.md) | `PUBLISH`/`SUBSCRIBE`'s fire-and-forget nature, and when to reach for Streams instead |
| 07 | [Transactions and Pipelining](redis/07_transactions_and_pipelining.md) | `MULTI`/`EXEC`, `WATCH` for optimistic locking, and a measured pipelining speedup |
| 08 | [Distributed Locking](redis/08_distributed_locking.md) | The `SET NX PX` lock pattern, safe release, and Redlock's real limits |
| 09 | [Rate Limiting With Redis](redis/09_rate_limiting_with_redis.md) | A sliding-window limiter shared across every app-server instance, not just one process |
| 10 | [Persistence: RDB and AOF](redis/10_persistence_rdb_aof.md) | RDB snapshots vs. the append-only file, and the durability/performance tradeoff |
| 11 | [Capstone: Being a Good Redis Client](redis/11_being_a_client_capstone.md) | A connection-pooled, retrying, timeout-aware client combining a session store, cache, and rate limiter |

### Concepts and Interview Prep (`concepts/`)

Design-level, not hands-on (no lab container for these) — schema design, cross-cutting
decision frameworks, and the interview questions this module actually gets asked as.

| # | Level | What you'll be able to do |
|---|---|---|
| 00 | [Wide-Column and DynamoDB-Style Databases](concepts/00_wide_column_and_dynamodb_style_databases.md) | Design a single-table DynamoDB schema; state Cassandra's `R + W > N` consistency formula |
| 01 | [Choosing a Database, and CAP Theorem Applied](concepts/01_choosing_a_database_and_cap_theorem.md) | Pick between <abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>/Mongo/Redis/wide-column by access pattern; name the concrete consistency knob in each real system |
| 02 | [Interview Playbook](concepts/02_interview_playbook.md) | The concrete <abbr title="Not Only SQL - A broad class of database management systems that differ from the classic relational model, designed for distributed data stores.">NoSQL</abbr> data-modeling and conceptual questions this ladder gets asked as, answered precisely |

## How to use this module

1. Pick the ladder that matches what you're prepping for — they don't depend on each
   other, though the closing "capstone" level of each is a good place to stop if you're
   short on time.
2. Run every code block yourself against the live lab containers. This module was
   written that way: every command's output shown in these files is real output from
   this machine, not a guess at what Redis or Mongo "should" print.
3. Where a level shows a measured number (a timing comparison, a real error), treat that
   as the point of the level, not decoration — re-run it and see your own machine's
   numbers.

## Related tracks

| Track | Relationship |
|---|---|
| **<abbr title="Structured Query Language. A standard language for storing, manipulating and retrieving data in databases.">SQL</abbr>** | The relational counterpart — same hands-on approach, PostgreSQL instead of Mongo/Redis |
| **CS Fundamentals** | `03_databases_deep_dive.md` covers the underlying storage-engine theory (B-trees, <abbr title="Log-Structured Merge-tree. A data structure with performance characteristics that make it attractive for providing indexed access to files with high insert volume.">LSM</abbr> trees, replication, consistency models) this module makes concrete |
| **System Design** | `building_blocks/` covers when a system's requirements point toward a given <abbr title="Not Only SQL - A broad class of database management systems that differ from the classic relational model, designed for distributed data stores.">NoSQL</abbr> family, including wide-column and graph stores not covered hands-on here |
| **Software Design** | `09_data_design_and_schema_evolution.md` covers schema evolution patterns that apply directly to MongoDB's flexible-schema documents |
