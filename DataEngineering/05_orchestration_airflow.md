# Orchestration with Apache Airflow

A data pipeline is rarely a single script. 
1. Extract data from Postgres.
2. Extract data from Salesforce API.
3. Wait for both to finish.
4. Run a Spark job to join them.
5. If the Spark job fails, retry 3 times.
6. If it succeeds, load the result into Snowflake.
7. Send an email report.

You cannot manage this with `cron`. You need an orchestrator. Apache Airflow is the industry standard.

## 1. DAGs (Directed Acyclic Graphs)

In Airflow, a workflow is defined as a DAG written in Python.

- **Directed**: Dependencies flow in one direction (A -> B).
- **Acyclic**: No infinite loops (A -> B -> A is forbidden).

```arch
%% caption: Airflow DAGs define the execution order and dependencies of tasks; if an upstream task fails, downstream tasks are skipped.
route straight
node pg "Task 1\nExtract Postgres" at 0,0 icon=db color=blue
node sf "Task 2\nExtract Salesforce" at 2,0 icon=network color=blue
node spark "Task 3\nSpark Join" at 1,1 icon=cpu color=amber
node snow "Task 4\nLoad Snowflake" at 1,2 icon=db color=green
node mail "Task 5\nEmail Report" at 1,3 icon=file color=slate

pg -> spark
sf -> spark
spark -> snow
snow -> mail
```

## 2. Core Concepts

- **Operators**: The actual work to be done. (e.g., `PythonOperator`, `BashOperator`, `SparkSubmitOperator`, `PostgresOperator`).
- **Sensors**: A special type of operator that just waits for something to happen (e.g., `S3KeySensor` waits for a file to appear in S3 before letting the DAG continue).
- **Task**: An instance of an operator in a DAG.
- **XCom (Cross-Communication)**: Tasks in Airflow run on different workers, so they cannot share variables in memory. XCom is a mechanism (backed by Airflow's internal DB) to pass small amounts of metadata between tasks (e.g., Task A returns a file path, Task B reads the path from XCom). Do NOT use XCom to pass gigabytes of actual data.

## 3. The Golden Rule of Airflow

**Tasks must be idempotent.**

If Task 3 (Spark Join) fails halfway through and you click "Retry" in the Airflow UI, it will run again. If your task was `INSERT INTO table`, running it twice will duplicate the data. 

To make it idempotent, the task should be `DELETE WHERE date = 'today' AND THEN INSERT INTO table`, or it should use an `UPSERT` / `MERGE` statement. No matter how many times an idempotent task is retried, the final state of the database is exactly the same.
