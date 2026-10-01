# Orchestration with Apache Airflow

A data pipeline is rarely a single script. It is a set of steps with dependencies,
schedules, retries, backfills and alerts, and something has to run them in the right
order every day and tell a human when they break. That something is an
**orchestrator**, and Apache Airflow is the most widely used one. This chapter explains
orchestration from zero, then Airflow's architecture (as of Airflow 3), how the
scheduler turns a schedule into runs with data intervals, operators, sensors and
deferrable tasks, XCom and assets, backfills, the idempotency rules that keep
retries safe, testing, and how Airflow compares with Dagster, Prefect and Temporal.

## Foundations — Why can't we just use cron?

### The problem

A typical daily pipeline:

1. Extract yesterday's orders from Postgres.
2. Extract yesterday's accounts from the Salesforce API.
3. Wait for both to finish.
4. Run a Spark job that joins them.
5. If the Spark job fails, retry it up to 3 times.
6. If it succeeds, load the result into Snowflake.
7. Email a report.

With `cron` you would schedule each step at a guessed time ("Spark at 03:30, it
usually starts after the extracts finish"). Then one night the Salesforce API is slow,
Spark runs on half the data, the report goes out wrong, and nobody knows. Cron has no
idea of dependencies, no retries, no history of what ran, no way to re-run "the 12th
of last month" and everything downstream of it, and no alert when step 4 silently
did not happen.

An orchestrator adds exactly those things:

| Need | What the orchestrator provides |
|---|---|
| Order | A dependency graph: step 4 starts only after 1 and 2 succeed |
| Time | Schedules, and a notion of *which period* each run is for |
| Failure | Retries with backoff, timeouts, failure callbacks and alerts |
| History | A record of every run and task attempt, with logs |
| Re-runs | Clear a task and everything downstream; backfill a date range |
| Resources | Concurrency limits and pools so 200 tasks do not hit one database at once |

**The orchestrator coordinates work; it does not do the heavy work itself.** The
Spark job runs on a Spark cluster, the SQL runs in Snowflake; Airflow starts them,
waits, checks the result and decides what happens next.

### DAGs

Airflow describes a workflow as a **DAG (Directed Acyclic Graph)** written in Python:

- **Directed**: dependencies point one way (A → B means B waits for A).
- **Acyclic**: no loops (A → B → A is forbidden), so there is always a valid order.

```arch
%% caption: The pipeline as a DAG. The Spark join waits for both extracts; if an upstream task fails, the tasks downstream of it are marked upstream_failed and do not run.
grid 160x100
node pg "Extract Postgres" at 0,0 icon=postgresql sub="task 1"
node sf "Extract Salesforce" at 2,0 icon=api sub="task 2"
node spark "Spark join" at 1,1 icon=apache-spark sub="task 3, retries=3"
node snow "Load Snowflake" at 1,2 icon=db sub="task 4, MERGE"
node mail "Email report" at 1,3 icon=email sub="task 5"
pg -> spark
sf -> spark
spark -> snow
snow -> mail
```

### Vocabulary

| Term | Meaning |
|---|---|
| DAG | A workflow definition: tasks plus dependencies plus a schedule |
| Task | One node in the DAG, created from an operator or a `@task` function |
| Operator | A template for a kind of work (`BashOperator`, `SparkSubmitOperator`, `SQLExecuteQueryOperator`) |
| Sensor | A task that waits for a condition (a file landed, another job finished) |
| DAG run | One execution of a DAG, usually for one **data interval** |
| Task instance | One task in one DAG run, with a state and one or more attempts |
| Data interval | The period of data a run is responsible for (e.g. 2026-09-27 00:00 to 2026-09-28 00:00) |
| XCom | Small messages passed between tasks |
| Asset | A named piece of data (a table, a path) that tasks produce and DAGs can be scheduled on (called *Dataset* before Airflow 3) |
| Executor | The mechanism that decides where tasks run (local processes, Celery workers, Kubernetes pods) |

## 1. Airflow's architecture (Airflow 3)

Airflow 3.0 (April 2025) was the first major release since 2020. The architecture
changed in one important way: **task code no longer talks to the metadata database
directly**. Workers talk to the API server through the Task Execution API, using the
Task SDK (`airflow.sdk`). That isolates the database, enables remote workers, and
paves the way for tasks in other languages.

```arch
%% caption: Airflow 3 components. The DAG processor parses DAG files into the metadata database; the scheduler creates runs and queues ready tasks to the executor; workers run tasks and report through the API server; the triggerer handles deferred waits.
grid 165x110
node files "DAG files" at 0,0 icon=folder sub="Python in git"
node proc "DAG processor" at 1,0 icon=process sub="parses, serialises"
node db "Metadata DB" at 2,1 icon=postgresql sub="runs, states, XCom"
node sched "Scheduler" at 1,1 icon=scheduler sub="runs + ready tasks"
node api "API server" at 2,2 icon=api sub="UI, REST, task API"
node exec "Executor" at 0,1 icon=workflow sub="Celery / K8s / Local"
node work "Workers" at 0,2 icon=worker sub="run task code"
node trig "Triggerer" at 1,2 icon=timer sub="async waits"
node user "Engineers" at 2,0 icon=users sub="UI / CLI"
files -> proc
proc -> db
sched <-> db
sched -> exec : "queue"
exec -> work
work -> api : "state, XCom"
trig -> api
api <-> db
user -> api
```

| Component | Job |
|---|---|
| **DAG processor** | Parses DAG files (every `min_file_process_interval`, default 30 s) and stores serialised DAGs. A separate process in Airflow 3 |
| **Scheduler** | Creates DAG runs when their schedule is due, decides which task instances are ready (all dependencies met, within concurrency limits), and sends them to the executor |
| **Executor** | Runs inside the scheduler and hands tasks to workers: `LocalExecutor` (subprocesses on one machine), `CeleryExecutor` (a queue plus a worker fleet), `KubernetesExecutor` (one pod per task), the Edge executor (remote workers), or several at once (multiple executors, since 2.10) |
| **Workers** | Run the task code |
| **Triggerer** | Runs asyncio *triggers* for deferred tasks, so thousands of waits cost no worker slots |
| **API server** | Serves the React UI, the public REST API, and the Task Execution API that workers call (replaces the Airflow 2 "webserver") |
| **Metadata database** | Postgres (or MySQL): DAG runs, task states, XComs, connections, variables |

Managed options: Astronomer (Astro), Google Cloud Composer, Amazon MWAA.

## 2. Writing a DAG (Airflow 3 syntax)

```python
from __future__ import annotations

import pendulum

from airflow.sdk import Asset, dag, get_current_context, task
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor
from airflow.providers.apache.spark.operators.spark_submit import SparkSubmitOperator
from airflow.providers.common.sql.operators.sql import SQLExecuteQueryOperator

orders_daily_asset = Asset("snowflake://analytics/marts/orders_daily")


@dag(
    dag_id="orders_daily",
    schedule="0 3 * * *",                          # 03:00 UTC, for the previous day's interval
    start_date=pendulum.datetime(2026, 1, 1, tz="UTC"),
    catchup=False,                                 # the Airflow 3 default; backfill explicitly instead
    max_active_runs=1,
    default_args={
        "retries": 3,
        "retry_delay": pendulum.duration(minutes=5),
        "retry_exponential_backoff": True,
        "execution_timeout": pendulum.duration(hours=2),
    },
    tags=["orders", "tier-1"],
)
def orders_daily():
    @task
    def extract_postgres() -> str:
        ctx = get_current_context()
        start, end = ctx["data_interval_start"], ctx["data_interval_end"]
        path = f"s3://landing/orders/dt={start:%Y-%m-%d}/"
        # Copy rows with start <= updated_at < end to `path`, overwriting the folder.
        # Deterministic output path + overwrite = safe to retry.
        return path                                 # a small string goes through XCom

    wait_for_salesforce = S3KeySensor(
        task_id="wait_for_salesforce_export",
        bucket_key="s3://landing/salesforce/dt={{ ds }}/_SUCCESS",
        deferrable=True,                            # waits in the triggerer, not in a worker slot
        poke_interval=300,
        timeout=6 * 60 * 60,
    )

    spark_join = SparkSubmitOperator(
        task_id="spark_join",
        conn_id="spark_k8s",
        application="/opt/jobs/join_orders_accounts.py",
        application_args=["--date", "{{ ds }}"],
    )

    load_snowflake = SQLExecuteQueryOperator(
        task_id="load_snowflake",
        conn_id="snowflake",
        sql="sql/merge_orders_daily.sql",           # MERGE keyed on order_id, for dt = '{{ ds }}'
        outlets=[orders_daily_asset],               # marks the asset as updated on success
    )

    @task
    def email_report():
        ...

    orders_path = extract_postgres()
    [orders_path, wait_for_salesforce] >> spark_join >> load_snowflake >> email_report()


orders_daily()
```

What changed from Airflow 2 (a frequent interview and migration topic):

| Airflow 2 | Airflow 3 |
|---|---|
| `from airflow.decorators import dag, task` | `from airflow.sdk import dag, task` |
| `schedule_interval=` | `schedule=` only |
| `execution_date` in templates and context | Removed; use `logical_date`, `data_interval_start`/`end`, `ds` |
| Datasets | **Assets** (`Asset`, `@asset`) |
| SubDAGs | Removed; use TaskGroups |
| SLAs | Removed (Deadline Alerts arrived in 3.1) |
| `catchup=True` by default | `catchup=False` by default |
| Backfill as a CLI loop on your machine | Backfills run by the scheduler, visible in the UI |
| Webserver | API server; new React UI; DAG versioning |
| Core operators in `airflow.operators.*` | In the `apache-airflow-providers-standard` package (`airflow.providers.standard.*`) |

### Rules for DAG files

- **No heavy work at the top level.** The DAG processor imports every DAG file every
  ≈30 seconds. A database query or API call at module level runs on every parse and
  slows or breaks scheduling. Put it inside tasks.
- **Static `start_date`.** Never `datetime.now()`: the schedule moves every parse and
  runs never become due.
- **Tasks should be atomic.** One task, one logical unit that fully succeeds or fully
  fails.
- **Deterministic task ids and DAG structure.** Dynamic DAGs generated from a config
  file are fine; generating them from a live API call at parse time is not.

## 3. Schedules, data intervals and logical dates

This is the concept people most often get wrong.

A scheduled run is **for a data interval**, and it starts **after that interval
ends**. With `schedule="@daily"`, the run covering 2026-09-27 00:00 → 2026-09-28 00:00
starts at 2026-09-28 00:00, because only then is the day's data complete. Its
`logical_date` (and `{{ ds }}`) is `2026-09-27`, the *start* of the interval.

| Template | Value for the run covering 27 Sep |
|---|---|
| `{{ ds }}` | `2026-09-27` |
| `{{ data_interval_start }}` | `2026-09-27T00:00:00+00:00` |
| `{{ data_interval_end }}` | `2026-09-28T00:00:00+00:00` |
| When it actually runs | shortly after 2026-09-28 00:00 |

Write every task to process **exactly its data interval**, never "now minus one day".
Then a retry, a re-run next month, or a backfill of last year produces the same result
as the original run.

Other schedule forms: cron strings, presets (`@hourly`, `@daily`), `timedelta`,
**timetables** for custom calendars (business days, fiscal periods), **asset
schedules** (run when upstream data is updated), and `None` (manual or API-triggered
only). Manually triggered and asset-triggered runs in Airflow 3 may have no logical
date, one more reason to use data intervals deliberately.

**Catchup and backfill.** With `catchup=True`, a DAG whose `start_date` is in the past
creates a run for every missed interval when it is turned on. Airflow 3 defaults to
`False` and makes backfills an explicit, scheduler-managed operation:

```bash
airflow backfill create --dag-id orders_daily \
  --from-date 2026-08-01 --to-date 2026-08-31 \
  --max-active-runs 4 --reprocess-behavior failed
```

## 4. Operators, sensors and deferrable tasks

**Operators** are grouped by provider packages (`apache-airflow-providers-amazon`,
`-google`, `-snowflake`, `-databricks`, `-cncf-kubernetes`, `-dbt-cloud` …). Three
styles cover most needs:

| Style | Example | When |
|---|---|---|
| `@task` (TaskFlow) | Python function; return values go through XCom | Glue logic, small Python work, calling APIs |
| Provider operator | `SparkSubmitOperator`, `SQLExecuteQueryOperator`, `DbtCloudRunJobOperator` | Triggering work in an external system |
| Container per task | `KubernetesPodOperator`, `@task.kubernetes`, `@task.docker` | Isolated dependencies, heavy or non-Python work |

**Sensors** wait for something: a file (`S3KeySensor`), another DAG's task
(`ExternalTaskSensor`), a SQL condition. A sensor in classic `poke` mode occupies a
worker slot the whole time it waits; a hundred sensors waiting for six hours can starve
the whole deployment. Options:

- `mode="reschedule"`: the sensor checks, releases its slot, and is rescheduled later
  (state `up_for_reschedule`).
- **Deferrable** operators and sensors (`deferrable=True`): the task suspends itself
  (state `deferred`) and hands an async trigger to the **triggerer**, which can wait on
  thousands of conditions in one process. When the trigger fires, the task resumes on
  a worker. Prefer this for any long wait.
- Better still, avoid polling: schedule the downstream DAG on the **asset** the
  upstream task produces.

**Dynamic task mapping** creates a variable number of task instances at run time:

```python
@task
def list_partitions() -> list[str]:
    return ["eu", "us", "apac"]          # e.g. discovered from S3 at run time

@task
def process(region: str) -> int:
    ...
    return 0

process.expand(region=list_partitions())  # one mapped task instance per region
```

## 5. Task states, retries and trigger rules

```arch
%% caption: The main task instance states. A task is scheduled when its dependencies are met, queued to the executor, and run; failures retry until attempts run out; tasks downstream of a failure become upstream_failed.
grid 150x100
node none "none" at 0,0 shape=pill color=slate
node sch "scheduled" at 1,0 shape=pill color=blue
node q "queued" at 2,0 shape=pill color=blue
node run "running" at 2,1 shape=pill color=amber
node def "deferred" at 3,1 shape=pill color=purple
node ok "success" at 2,2 shape=pill color=green
node retry "up_for_retry" at 1,1 shape=pill color=orange
node fail "failed" at 3,2 shape=pill color=red
node uf "upstream_failed" at 3,3 shape=pill color=red
none -> sch : "deps met"
sch -> q
q -> run
run <-> def : "trigger"
run -> ok
run -> retry : "error"
retry -> sch : "after delay"
run -> fail : "no retries left"
fail -> uf : "downstream"
```

- `retries`, `retry_delay`, `retry_exponential_backoff` and `max_retry_delay` handle
  transient failures (API timeouts, preempted pods). They are **only safe if the task is
  idempotent** (§7).
- `execution_timeout` kills a hung task; without it a stuck task can hold a slot and
  block the next day's run (with `max_active_runs=1`).
- **Trigger rules** decide when a task runs based on upstream states. Default
  `all_success`. Others: `all_done` (cleanup tasks), `one_failed` (alerting),
  `none_failed` (after a branch skipped something), `all_skipped`, `none_failed_min_one_success`.
- **Precision note:** when a task fails, the tasks downstream of it are marked
  `upstream_failed`, not `skipped`. `skipped` comes from branching
  (`@task.branch`) or short-circuiting (`@task.short_circuit`).
- Callbacks (`on_failure_callback`, `on_success_callback`, `on_retry_callback`) and
  notifiers send alerts to Slack, PagerDuty or email.

**Concurrency controls:** `max_active_runs` (per DAG), `max_active_tasks` (per DAG),
**pools** (a named number of slots shared by tasks across DAGs, e.g. "at most 8 tasks
may query the production replica"), `priority_weight`, and executor/worker capacity.

## 6. XCom and assets: passing information between tasks

Tasks run in different processes, often on different machines, so they cannot share
Python variables. **XCom** ("cross-communication") passes small values: a file path,
a row count, a run id. Returning a value from a `@task` pushes it to XCom; passing it
to another `@task` pulls it.

**Do not pass data through XCom.** By default XComs are stored in the metadata
database; pushing a 500 MB DataFrame there bloats the database and slows everything.
Pass a *reference* (the S3 path) and keep the data in storage. A custom XCom backend
(for example the object-storage backend in the common-io provider) can offload larger
values to S3 transparently, but the principle stays: Airflow moves pointers, storage
moves bytes.

**Assets** declare data dependencies between DAGs. A task lists
`outlets=[Asset(...)]`; a downstream DAG sets `schedule=[that_asset]` and runs whenever
it is updated, without sensors or guessed times:

```python
from airflow.sdk import Asset, dag, task
import pendulum

orders_daily_asset = Asset("snowflake://analytics/marts/orders_daily")

@dag(schedule=[orders_daily_asset], start_date=pendulum.datetime(2026, 1, 1, tz="UTC"))
def revenue_dashboard_refresh():
    @task
    def refresh():
        ...
    refresh()

revenue_dashboard_refresh()
```

Airflow 3 also adds event-driven scheduling (asset watchers that react to messages,
for example on a queue) and the `@asset` decorator for asset-centric pipelines.

## 7. The golden rule: idempotent tasks

**Running a task once or five times for the same data interval must leave the same
final state.** Retries, manual re-runs, backfills and "clear downstream" all depend on
it.

If task 4 runs `INSERT INTO fact_orders SELECT ... FROM staging` and fails halfway,
or succeeds but the worker dies before reporting success, the retry inserts the rows
again. Revenue doubles.

Idempotent patterns:

| Pattern | Example |
|---|---|
| **Delete-then-insert the interval, in one transaction** | `BEGIN; DELETE FROM fact_orders WHERE order_date = '{{ ds }}'; INSERT INTO fact_orders SELECT ... WHERE order_date = '{{ ds }}'; COMMIT;` |
| **MERGE / upsert by key** | `MERGE INTO fact_orders t USING staging s ON t.order_id = s.order_id WHEN MATCHED THEN UPDATE ... WHEN NOT MATCHED THEN INSERT ...` |
| **Overwrite a partition** | Spark dynamic partition overwrite, Iceberg `overwritePartitions()`, BigQuery `WRITE_TRUNCATE` to `table$20260927` |
| **Deterministic output paths** | `s3://landing/orders/dt=2026-09-27/`, overwritten on retry, never `.../run_<uuid>/` appended to |
| **Idempotency keys for side effects** | Sending an email or calling a payment API: record "sent for interval X" and check it first |

Related rules: process **only the data interval** (never `now()`), make reads
reproducible (read from a snapshot or an immutable raw layer), and keep tasks atomic.

## 8. Testing and deploying DAGs

```python
# tests/test_dags.py  (run with pytest in CI)
from airflow.models import DagBag


def test_dags_import_without_errors():
    bag = DagBag(dag_folder="dags/", include_examples=False)
    assert bag.import_errors == {}


def test_orders_daily_structure():
    bag = DagBag(dag_folder="dags/", include_examples=False)
    dag = bag.get_dag("orders_daily")
    assert dag is not None
    assert dag.get_task("spark_join").retries == 3
    assert {t.task_id for t in dag.get_task("load_snowflake").upstream_list} == {"spark_join"}
```

- **Import test** in CI catches syntax errors, missing imports and cycles before they
  reach the scheduler.
- **Unit-test task logic** as plain Python functions, outside Airflow.
- `dag.test()` runs a whole DAG in one process locally for debugging;
  `airflow tasks test <dag> <task> <date>` runs one task without recording state.
- Deploy DAG files from git (CI syncs to the DAG folder or bakes them into the
  image); Airflow 3's DAG versioning keeps the UI showing which code version each run
  used. Pin provider versions with Airflow's constraints files.

## 9. Operating Airflow in production

| Symptom | Likely cause | Fix |
|---|---|---|
| Tasks sit in `scheduled`/`queued` for a long time | No free worker slots, pools exhausted, sensors hogging slots | Deferrable sensors, more workers, check pool sizes and `max_active_tasks` |
| UI and scheduler slow | Heavy top-level DAG code, huge XComs, metadata DB bloat | Move work into tasks, pass references, `airflow db clean` on a schedule |
| Yesterday's data doubled | Non-idempotent task retried | Delete-insert/MERGE/overwrite patterns |
| A run "succeeded" on empty data | Upstream was late; no data check | Sensors or asset scheduling; data quality checks (row counts, freshness) as tasks |
| One stuck run blocks the next day | `max_active_runs=1` and no `execution_timeout` | Timeouts on every task |
| Backfill overloads the warehouse | Too many concurrent runs | `--max-active-runs`, pools |

## 10. Airflow and its alternatives

| Tool | Model | Choose it when |
|---|---|---|
| **Airflow** | Task-centric DAGs in Python, huge provider ecosystem | Scheduling many heterogeneous batch jobs; the industry default; managed everywhere |
| **Dagster** | Asset-centric: you declare the tables/files and how each is computed; strong typing, lineage and local testing | Data platforms that think in assets, want lineage and partitions built in |
| **Prefect** | Python-native flows, dynamic by default | Pythonic workflows with less ceremony |
| **Temporal** | Durable execution for application workflows (code that survives crashes, waits for days) | Business processes and microservice sagas, not scheduled batch analytics |
| **Argo Workflows** | Kubernetes-native DAGs of containers (YAML) | Container-first teams, ML pipelines on Kubernetes |
| **dbt Cloud / warehouse schedulers** | Schedule dbt jobs only | A pure-SQL stack with nothing else to coordinate |

A common 2026 setup: Airflow (or Dagster) orchestrates extraction, dbt builds
([chapter 6](06_data_transformation_dbt.md)), Spark jobs
([chapter 3](03_batch_processing_spark.md)) and data quality checks, while streaming
jobs ([chapter 4](04_stream_processing.md)) run continuously outside the orchestrator.

## Common interview questions

**Why use an orchestrator instead of cron?**
Dependencies between tasks, retries with backoff, timeouts, run history and logs,
re-running a past period and everything downstream, backfills, concurrency limits,
and alerting. Cron only knows the time.

**What is the difference between logical date and when a run executes?**
A run covers a data interval and executes after the interval ends. The logical date
(`ds`) is the interval start, so the run for 27 September executes on 28 September.

**What does idempotent mean for a task, and how do you achieve it?**
Running it multiple times for the same interval gives the same final state. Process
only the data interval and write with delete-insert in a transaction, MERGE by key,
or partition overwrite to deterministic locations.

**Why not pass a DataFrame through XCom?**
XComs live in the metadata database by default and are meant for small metadata.
Large values bloat the database and slow the scheduler; write data to storage and pass
the path.

**Sensors: poke vs. reschedule vs. deferrable?**
Poke holds a worker slot while waiting. Reschedule frees it between checks.
Deferrable hands the wait to the triggerer's async loop, so thousands of waits cost
almost nothing. Asset-based scheduling removes the need to poll at all.

**How would you backfill a year of data safely?**
Idempotent tasks that read only their interval, `airflow backfill create` with a
limited number of active runs and a pool protecting shared systems, and verification
of row counts per partition afterwards.

**What happens to downstream tasks when a task fails?**
After retries are exhausted it is `failed`; downstream tasks with the default
`all_success` trigger rule become `upstream_failed`. Tasks with `all_done` or
`one_failed` still run (cleanup, alerting).

**What changed in Airflow 3?**
Task Execution API and Task SDK (workers no longer touch the DB), separate DAG
processor, API server with a new UI, DAG versioning, assets replacing datasets,
scheduler-managed backfills, removal of SubDAGs, SLAs and `execution_date`, and
`catchup=False` by default.

**Airflow vs. Dagster vs. Temporal?**
Airflow schedules task DAGs with a vast ecosystem; Dagster models data assets with
lineage and partitions; Temporal provides durable execution for long-running
application workflows, not scheduled analytics.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student / Intern | Intern, new learner | — | Why orchestration beats cron; what a DAG, task and operator are; reads a simple DAG file |
| Junior | Data Engineer I | L3 | Writes DAGs with TaskFlow and provider operators; sets retries and timeouts; uses `{{ ds }}`/data intervals correctly; knows XCom is for small values |
| Mid | Data Engineer II | L4 | Designs idempotent tasks; uses deferrable sensors, pools, dynamic mapping and asset schedules; backfills safely; tests DAG imports in CI; debugs stuck and failing runs |
| Senior | Senior Data Engineer | L5 | Explains the scheduler, executors and Airflow 3 architecture; chooses executors; designs cross-DAG dependencies and failure handling; runs Airflow at scale (DB hygiene, parse performance, upgrades from 2 to 3) |
| Staff+ | Staff / Principal Engineer | L6+ | Picks the orchestration platform (Airflow, Dagster, managed vs. self-hosted) for the organisation; sets standards for idempotency, data contracts, SLAs/deadlines and on-call; designs how batch, streaming and dbt fit together |

## Interview checklist

- [ ] I can explain what an orchestrator adds over cron and that it coordinates rather than computes.
- [ ] I can name Airflow 3's components and what the Task Execution API changed.
- [ ] I can write a DAG with TaskFlow, a provider operator, a deferrable sensor and dependencies.
- [ ] I can explain data intervals, logical date and when a run executes.
- [ ] I can explain catchup and run a backfill safely.
- [ ] I can compare poke, reschedule and deferrable sensors.
- [ ] I can list task states and trigger rules, and explain `upstream_failed` vs. `skipped`.
- [ ] I can explain why XCom is for references, not data, and how assets schedule DAGs.
- [ ] I can make a task idempotent in three different ways.
- [ ] I can test DAGs in CI and name common production failure modes.
- [ ] I can compare Airflow with Dagster, Prefect, Temporal and Argo Workflows.

Related: [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md) (testing and shipping DAG code),
[Application Resilience Patterns](../SystemDesign/building_blocks/12_application_resilience_patterns.md) (retries, backoff, idempotency),
[Messaging and Streaming](../SystemDesign/building_blocks/09_messaging_and_streaming.md) (workflow engines vs. queues),
[Transactions and Isolation Levels](../SQL/09_transactions_and_isolation_levels.md) (the transaction behind delete-then-insert).
