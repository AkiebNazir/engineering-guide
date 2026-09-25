# Batch Processing with Apache Spark

While ELT (using BigQuery/Snowflake) is great for SQL transformations, sometimes you need imperative programming (Python/Scala) to process massive datasets. Perhaps you are parsing 50TB of raw unstructured JSON logs, running machine learning models, or crunching complex graph algorithms.

This is where Apache Spark shines.

## 1. What is Spark?

Spark is a distributed compute engine. It does not *store* data (unlike a database). It reads data from distributed storage (like AWS S3 or HDFS), processes it in memory across a cluster of machines, and writes the results back.

## 2. The Architecture

```arch
%% caption: The Spark Driver translates code into a DAG of tasks, which the Cluster Manager schedules across Executor nodes for parallel execution.
route straight
node user "User Code\\n(PySpark)" at 0,1 icon=code color=blue
node driver "Driver Node\\n(Creates DAG)" at 2,1 icon=cpu color=amber
group cluster "Worker Nodes (Executors)" color=slate style=dashed
node w1 "Executor 1\\n(Tasks)" at 4,0 in cluster icon=worker color=green
node w2 "Executor 2\\n(Tasks)" at 4,2 in cluster icon=worker color=green

user -> driver : "submits job"
driver -> w1 : "sends code"
driver -> w2 : "sends code"
```

## 3. RDDs and DataFrames

- **RDD (Resilient Distributed Dataset)**: The core abstraction. An immutable collection of objects partitioned across the cluster. (Low-level, rarely used directly today).
- **DataFrame**: A dataset organized into named columns (like a Pandas DataFrame or SQL table). Spark optimizes DataFrame queries using its Catalyst Optimizer, making Python code run exactly as fast as Scala code.

## 4. Transformations vs Actions

Spark evaluates lazily.

**Transformations** (e.g., `filter()`, `map()`, `groupBy()`) do not execute immediately. They just build a DAG (Directed Acyclic Graph) of operations.
**Actions** (e.g., `count()`, `show()`, `write()`) trigger the actual execution.

```python
# 1. Read 100GB of JSON from S3 (Transformation - lazy)
df = spark.read.json("s3://bucket/logs/")

# 2. Filter for errors (Transformation - lazy)
errors = df.filter(df.level == "ERROR")

# 3. Write to Parquet (Action - execution begins!)
errors.write.parquet("s3://bucket/clean-logs/")
```

## 5. The Shuffle Problem

Some operations (like a simple `filter` or `map`) can be executed completely independently on each Worker node. This is called a **Narrow Dependency**.

Other operations (like `groupBy`, `join`, or `orderBy`) require data with the same key to be physically moved to the same Worker node. This is a **Wide Dependency**, and it triggers a **Shuffle**.

Shuffles write intermediate data to disk and send it over the network. They are the single biggest bottleneck in Spark.
*Optimization rule:* Always `filter` before you `join` or `groupBy` to minimize the amount of data shuffled.
