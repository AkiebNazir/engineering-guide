# Data Engineering

**Start here.** This module bridges backend engineering (OLTP: the database behind the
app) and analytics (OLAP: the warehouse or lakehouse behind dashboards, reports and
ML). It teaches how data is moved out of production systems, stored for analysis,
modeled, transformed in batch and in real time, and orchestrated reliably, at the
depth data engineering and backend interviews expect.

## Who it is for

- Backend engineers who own services whose data ends up in a warehouse, and who get
  asked "how would you get this into analytics?" in system design rounds.
- Engineers moving into data engineering or analytics engineering.
- Anyone preparing for data engineering interviews (modeling, Spark, streaming,
  Airflow, dbt).

Each chapter starts with a from-zero **Foundations** section, then numbered deep
sections with runnable or production-shaped code, diagrams, failure modes, common
interview questions with model answers, a per-level expectations table and an
interview checklist.

## Reading order

Read in order; each chapter builds on the previous ones.

1. [OLTP vs OLAP & Data Warehouses](01_oltp_vs_olap.md): why analytics needs its own
   systems; row vs. column storage and Parquet; cloud warehouses; lakehouses and
   Iceberg; ETL vs. ELT; batch extracts vs. CDC with Debezium. Live flow: a CDC
   pipeline.
2. [Data Modeling: Star Schema & SCDs](02_data_modeling.md): facts and dimensions,
   grain, fact and dimension types, slowly changing dimensions with a runnable SCD
   Type 2, surrogate keys, late-arriving data, Data Vault and one big table.
3. [Batch Processing with Apache Spark](03_batch_processing_spark.md): driver and
   executors, lazy evaluation and Catalyst, stages and the shuffle, join strategies,
   AQE, skew, memory and failure recovery, the Spark UI. Live flow: a job's shuffle,
   a skewed key and a lost executor.
4. [Stream Processing Fundamentals](04_stream_processing.md): event time, windows,
   watermarks and late data, state and checkpoints, exactly-once, stream joins,
   Flink vs. Spark Structured Streaming vs. Kafka Streams. Live flow: a watermark,
   a late event and a side output.
5. [Orchestration with Apache Airflow](05_orchestration_airflow.md): Airflow 3
   architecture, DAGs and data intervals, sensors and deferrable tasks, XCom and
   assets, backfills, idempotent tasks, testing, alternatives.
6. [Data Transformation with dbt](06_data_transformation_dbt.md): models, `ref()`
   and the DAG, project layering, materializations and incremental models,
   snapshots, data tests, unit tests and contracts, slim CI.

Short on time? Chapters 1, 2 and 4 cover what most backend system design interviews
touch; add 3, 5 and 6 for data engineering roles.

## Prerequisites

- SQL: joins, aggregation, window functions, CTEs, transactions
  ([SQL/](../../data-and-apis/SQL/README.md), especially chapters 06–09 and 16).
- Basic Python.
- Helpful: how databases store data and replicate
  ([Database Internals: How They Actually Work](../../interview-core/SystemDesign/building_blocks/06_database_internals.md),
  [Replication and High Availability](../../data-and-apis/SQL/17_replication_and_high_availability.md))
  and what Kafka is ([Kafka and Event Streaming](../Tool-Kit/04_kafka_and_event_streaming.md)).

## Related modules

- [SQL/](../../data-and-apis/SQL/README.md) and [NoSQL/](../../data-and-apis/NoSQL/README.md): the operational databases
  that data pipelines read from.
- [Batch and Stream Processing](../../interview-core/SystemDesign/building_blocks/21_batch_and_stream_processing.md),
  [Messaging and Streaming](../../interview-core/SystemDesign/building_blocks/09_messaging_and_streaming.md) and
  [Object Storage](../../interview-core/SystemDesign/building_blocks/08_object_storage.md): the
  system design view of the same ideas.
- [MLOps/](../../ai-engineering/MLOps/README.md): feature stores and training pipelines built on top of
  this module's warehouse, lakehouse and streaming layers.
- [CICD/](../CICD/README.md) and [TestingAndQuality/](../TestingAndQuality/README.md):
  shipping and testing pipeline code (dbt CI, DAG tests, data contracts).
