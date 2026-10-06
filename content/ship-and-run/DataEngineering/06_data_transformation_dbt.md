# Data Transformation with dbt

In the ELT pattern ([chapter 1](01_oltp_vs_olap.md)) raw data is loaded into the
warehouse first, and then it has to be transformed into clean, tested, modeled tables
([chapter 2](02_data_modeling.md)). Historically that meant hundreds of hand-run
scripts and stored procedures nobody dared to change. **dbt (data build tool)** brought
software engineering practice to SQL transformations: version control, modularity,
dependency graphs, tests, documentation and CI. This chapter covers dbt from zero to
production: how it compiles and runs models, `ref` and the DAG, project layering,
materializations and incremental models, snapshots for SCD Type 2, the testing
toolbox (data tests, unit tests, contracts), CI with state selection, and the failure
modes you meet at scale.

## Foundations — What problem does dbt solve?

### Before dbt

A team has raw tables loaded by Fivetran or a CDC pipeline: `raw.shop.orders`,
`raw.shop.customers`, `raw.stripe.charges`. Analysts need `fct_orders` and
`dim_customers`. So someone writes a folder of SQL scripts:

```text
01_create_clean_customers.sql
02_create_clean_orders.sql
03_create_orders_with_payments.sql   -- must run after 01 and 02
04_create_fct_orders.sql             -- must run after 03
```

The order lives in file names and people's heads. Every script repeats
`CREATE OR REPLACE TABLE ... AS`. Nothing checks that `order_id` is unique. Nobody
knows which dashboard breaks if a column is renamed. A change goes straight to
production because there is no development copy.

### What dbt does

dbt is a **compiler and runner for SQL `SELECT` statements**. You write each model as
one `SELECT` in its own file; dbt:

1. **Builds the dependency graph** from `{{ ref('other_model') }}` calls, so the run
   order is derived, never hand-maintained.
2. **Generates the DDL/DML** (`CREATE TABLE AS`, `CREATE VIEW`, `MERGE`) from a
   `materialized` setting.
3. **Runs it in your warehouse.** dbt moves no data; all compute happens in Snowflake,
   BigQuery, Databricks, Redshift, Postgres, DuckDB and others, through an
   **adapter**.
4. **Tests** assumptions about the data (unique, not null, relationships, custom SQL)
   and, since dbt 1.8, unit-tests model logic on fixed inputs.
5. **Documents** every model and column and draws the lineage graph.
6. **Separates environments**: each developer builds into their own schema
   (`dbt_ana`), CI into a temporary schema, production into `analytics`.

Everyday analogy: dbt is to SQL tables what `make` plus a unit-test framework is to
source files. You declare how each output is built from its inputs; the tool works out
the order, rebuilds what is needed, and checks the results.

**dbt Core** is the open-source CLI (Apache 2.0). **dbt Cloud** (the dbt platform) is
dbt Labs' hosted service with an IDE, scheduler, CI, the Semantic Layer and more. In
2025 dbt Labs also released **dbt Fusion**, a new Rust-based engine that parses and
compiles projects much faster and understands SQL (so it can flag errors before
running them); the concepts in this chapter apply to both engines.

### Vocabulary

| Term | Meaning |
|---|---|
| Model | One `.sql` (or Python) file containing one `SELECT`; becomes a table or view |
| Source | A raw table dbt did not build, declared in YAML and read with `{{ source() }}` |
| `ref()` | Reference to another model; builds the DAG and resolves the right schema per environment |
| Materialization | How a model is persisted: view, table, incremental, ephemeral, materialized view |
| Data test | A query that returns failing rows; zero rows means pass |
| Unit test | Fixed input rows + expected output rows for one model |
| Snapshot | A dbt-managed SCD Type 2 history table of a mutable source |
| Seed | A small CSV in the repo loaded as a table (country codes, mappings) |
| Macro | A reusable Jinja function that generates SQL |
| Manifest | `target/manifest.json`: the compiled project graph, used for state comparison and docs |

## 1. How dbt works: from Jinja-SQL to warehouse objects

```sql
-- models/staging/shop/stg_shop__users.sql
with source as (
    select * from {{ source('shop', 'users') }}
),

renamed as (
    select
        id                  as user_id,
        lower(email)        as email,
        created_at::timestamp as created_at,
        is_deleted
    from source
)

select * from renamed
where not is_deleted
```

`dbt run --select stg_shop__users` does three things:

1. **Parse** every file, resolve `source()`/`ref()` and configs, build the graph.
2. **Compile** Jinja to plain SQL for the target warehouse. `{{ source('shop', 'users') }}`
   becomes `raw.shop.users` (from the YAML declaration); in a developer's environment
   `ref()`s resolve to `analytics_dev.dbt_ana.<model>`.
3. **Execute** the materialization, wrapping the compiled `SELECT`. On Snowflake,
   with `materialized='view'` (the default), roughly:

```sql
create or replace view analytics.staging.stg_shop__users as (
    with source as (
        select * from raw.shop.users
    ),
    renamed as ( ... )
    select * from renamed
    where not is_deleted
);
```

**Precision note:** with `materialized='table'` on Snowflake, dbt-snowflake creates a
`transient` table by default (`create or replace transient table ... as (...)`), which
skips Fail-safe storage costs. Set `transient: false` for tables that need Fail-safe.
You can always inspect the exact SQL in `target/compiled/` and `target/run/`.

```arch
%% caption: dbt compiles Jinja-templated SELECTs into warehouse SQL using the project graph and profile, then runs it in the warehouse; all data stays in the warehouse.
grid 165x105
node repo "dbt project" at 0,0 icon=git sub="models, tests, YAML"
node prof "profiles.yml" at 0,1 icon=key sub="target: dev / prod"
node parse "Parse + graph" at 1,0 icon=sitemap sub="ref(), source()"
node comp "Compile" at 2,0 icon=code sub="Jinja -> SQL"
node run "Run in DAG order" at 2,1 icon=workflow sub="threads in parallel"
node wh "Warehouse" at 2,2 icon=db sub="Snowflake / BigQuery / ..."
node art "Artifacts" at 1,2 icon=file sub="manifest, run_results"
repo -> parse
parse -> comp
prof -> run
comp -> run
run -> wh : "DDL / DML"
run -> art
```

### Connecting: `profiles.yml`

```yaml
# ~/.dbt/profiles.yml (keep secrets in env vars, never in git)
shop_analytics:
  target: dev
  outputs:
    dev:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      authenticator: externalbrowser
      role: TRANSFORMER
      warehouse: TRANSFORMING
      database: ANALYTICS_DEV
      schema: dbt_ana            # every developer gets their own schema
      threads: 8
    prod:
      type: snowflake
      account: "{{ env_var('SNOWFLAKE_ACCOUNT') }}"
      user: "{{ env_var('SNOWFLAKE_USER') }}"
      private_key_path: "{{ env_var('SNOWFLAKE_PRIVATE_KEY_PATH') }}"
      role: TRANSFORMER
      warehouse: TRANSFORMING
      database: ANALYTICS
      schema: analytics
      threads: 16
```

## 2. `ref()`, `source()` and the DAG

If `fct_orders` contains `select * from {{ ref('int_orders_with_payments') }}`, dbt
knows `int_orders_with_payments` must be built first. The whole run order comes from
these references, and `threads` controls how many independent models build in
parallel.

```yaml
# models/staging/shop/_shop__sources.yml
sources:
  - name: shop
    database: raw
    schema: shop
    loaded_at_field: _loaded_at             # set by the loader
    freshness:
      warn_after: {count: 6, period: hour}
      error_after: {count: 24, period: hour}
    tables:
      - name: users
      - name: orders
      - name: order_items
```

`dbt source freshness` fails the pipeline when raw data stopped arriving, so a
stale dashboard is caught before a human notices.

Node selection is the everyday power tool:

| Command | Builds |
|---|---|
| `dbt build --select fct_orders` | Just that model (and its tests) |
| `dbt build --select +fct_orders` | It and everything upstream |
| `dbt build --select fct_orders+` | It and everything downstream |
| `dbt build --select tag:finance` | Models tagged `finance` |
| `dbt build --select state:modified+ --defer --state prod-artifacts/` | Only changed models and their children, reading unchanged parents from production (slim CI, §7) |
| `dbt build --exclude tag:hourly` | Everything except hourly models |

`dbt build` runs seeds, models, snapshots and tests together in DAG order, and a
failing test **skips the models downstream of it**, so bad data does not propagate.
Prefer it over `dbt run` followed by `dbt test`.

## 3. Project structure: staging, intermediate, marts

The layering dbt Labs recommends maps directly onto the medallion layers:

```arch
%% caption: A dbt project in layers. Sources are declared, staging models clean one source table each, intermediate models join and reshape, marts expose facts and dimensions; the lineage comes from ref().
grid 160x100
group src "Sources (raw)" color=slate icon=archive
node s1 "shop.orders" at 0,0 in src icon=table
node s2 "shop.customers" at 2,0 in src icon=table
node s3 "stripe.charges" at 1,0 in src icon=table
group stg "Staging: 1:1 with sources, views" color=blue icon=filter
node t1 "stg_shop__orders" at 0,1 in stg icon=filter
node t2 "stg_shop__customers" at 2,1 in stg icon=filter
node t3 "stg_stripe__charges" at 1,1 in stg icon=filter
node i1 "int_orders_paid" at 0.5,2 icon=layers sub="intermediate"
group mart "Marts: tables for people" color=green icon=table
node f1 "fct_orders" at 0.5,3 in mart icon=table sub="incremental"
node d1 "dim_customers" at 2,3 in mart icon=user sub="table"
s1 -> t1
s2 -> t2
s3 -> t3
t1 -> i1
t3 -> i1
i1 -> f1
t2 -> d1
```

```text
models/
  staging/
    shop/
      _shop__sources.yml
      _shop__models.yml
      stg_shop__orders.sql
      stg_shop__customers.sql
    stripe/
      stg_stripe__charges.sql
  intermediate/
    int_orders_paid.sql
  marts/
    finance/
      fct_orders.sql
      _finance__models.yml
    marketing/
      dim_customers.sql
snapshots/
seeds/
macros/
tests/            # singular data tests
dbt_project.yml
```

| Layer | Rules |
|---|---|
| **Staging** | One model per source table; rename, cast, light cleaning, no joins; the only place `source()` is used. Usually views |
| **Intermediate** | Joins, pivots, deduplication, business logic shared by several marts. Not exposed to BI |
| **Marts** | Facts and dimensions ([chapter 2](02_data_modeling.md)) or wide tables for one business area. Tables or incremental |

Directory-level config in `dbt_project.yml` sets sensible defaults:

```yaml
name: shop_analytics
version: "1.0.0"
profile: shop_analytics

models:
  shop_analytics:
    staging:
      +materialized: view
    intermediate:
      +materialized: ephemeral
    marts:
      +materialized: table
      finance:
        +tags: ["finance", "tier-1"]
```

## 4. Materializations

| Materialization | Creates | Build cost | Query cost | Use for |
|---|---|---|---|---|
| `view` | `CREATE VIEW` | Almost nothing | Recomputed on every query | Staging, light logic |
| `table` | `CREATE TABLE AS` (full rebuild each run) | Full recompute | Fast | Most marts up to a size where full rebuilds get slow or expensive |
| `incremental` | Table built once, then only new/changed rows processed each run | Small per run | Fast | Large, append-mostly facts (events, orders) |
| `ephemeral` | Nothing; inlined as a CTE into models that ref it | None | Part of the parent | Small reusable logic |
| `materialized_view` | A warehouse materialized view / dynamic table | Warehouse-managed refresh | Fast | Where the warehouse can maintain freshness for you |

### Incremental models

```sql
-- models/marts/finance/fct_orders.sql  (Snowflake SQL)
{{
    config(
        materialized='incremental',
        unique_key='order_id',
        incremental_strategy='merge',
        on_schema_change='append_new_columns',
        cluster_by=['order_date']
    )
}}

select
    o.order_id,
    o.customer_id,
    o.order_date,
    o.status,
    p.amount_paid,
    o.updated_at
from {{ ref('stg_shop__orders') }} as o
left join {{ ref('int_orders_paid') }} as p using (order_id)

{% if is_incremental() %}
  -- Only rows changed since the last run, with a 3-day lookback for late updates.
  where o.updated_at > (
      select dateadd(day, -3, max(updated_at)) from {{ this }}
  )
{% endif %}
```

- On the **first run** (or with `--full-refresh`) `is_incremental()` is false and dbt
  builds the whole table.
- On later runs dbt selects only new rows into a temporary relation and applies them
  with the chosen **strategy**.
- `{{ this }}` is the model's own existing table.
- The **lookback window** catches rows that were updated late (the same late-commit
  problem as incremental extraction in [chapter 1](01_oltp_vs_olap.md) §7); `unique_key`
  plus `merge` makes reprocessing those rows idempotent.

| Strategy | What it does | Watch out for |
|---|---|---|
| `append` | Inserts new rows only | Duplicates if rows are reprocessed |
| `merge` | `MERGE` on `unique_key`: update matches, insert new | Must scan the target to match; add a predicate (`incremental_predicates`) for very large tables |
| `delete+insert` | Deletes target rows with matching keys, then inserts | Two statements; fine where `MERGE` is slow |
| `insert_overwrite` | Replaces whole partitions (BigQuery, Spark/Databricks) | Rows in a replaced partition that are absent from the new batch disappear, by design |
| `microbatch` (dbt 1.9+) | Splits processing into time batches by `event_time` (e.g. one day each), each run and retried independently; `dbt run --event-time-start ... --event-time-end ...` backfills | Upstream models need `event_time` configured to filter efficiently |

`on_schema_change` controls what happens when the model's columns change: `ignore`
(default), `fail`, `append_new_columns`, or `sync_all_columns`. A **full refresh**
rebuilds from scratch; schedule one periodically for models whose logic can drift, and
plan for its cost on huge tables.

## 5. Snapshots: SCD Type 2 without writing the MERGE

Snapshots record how a mutable source row changes over time, producing the Type 2
history described in [chapter 2](02_data_modeling.md) §5. Since dbt 1.9 they are
configured in YAML:

```yaml
# snapshots/customers_snapshot.yml
snapshots:
  - name: customers_snapshot
    relation: source('shop', 'customers')
    config:
      schema: snapshots
      unique_key: id
      strategy: timestamp          # or: check, with check_cols: [city, segment]
      updated_at: updated_at
      hard_deletes: invalidate     # close the current row when the source row is deleted
```

Each `dbt snapshot` (or `dbt build`) run compares the source with the current snapshot
rows and adds `dbt_scd_id`, `dbt_valid_from`, `dbt_valid_to` (NULL for the current
version, unless `dbt_valid_to_current` sets a sentinel date) and `dbt_updated_at`.

- The **timestamp** strategy trusts `updated_at`; the **check** strategy compares
  column values and works without a reliable timestamp, at more cost.
- A snapshot only sees the states that exist *when it runs*: if a row changes twice
  between daily runs, the middle state is lost. For complete history, build Type 2 from
  a CDC change log instead.
- Snapshots are **not reproducible from sources**: if you drop the table, history is
  gone. Treat snapshot tables as precious, back them up, and never `--full-refresh`
  them.

## 6. Testing

Data quality is the hardest part of data engineering, and dbt gives several layers of
defence.

### Data tests (formerly "schema tests")

A data test is a query that returns the rows violating an assumption. Generic tests
are declared in YAML (`data_tests:` since dbt 1.8; the older `tests:` key still works):

```yaml
# models/staging/shop/_shop__models.yml
models:
  - name: stg_shop__users
    columns:
      - name: user_id
        data_tests:
          - unique
          - not_null
      - name: email
        data_tests:
          - not_null
          - dbt_utils.expression_is_true:           # from the dbt_utils package
              expression: "like '%_@_%._%'"
      - name: email_domain
        data_tests:
          - accepted_values:
              values: ['gmail.com', 'yahoo.com', 'outlook.com', 'other']
              config:
                severity: warn

  - name: fct_orders
    data_tests:
      - dbt_utils.recency:
          datepart: hour
          field: updated_at
          interval: 6
    columns:
      - name: order_id
        data_tests: [unique, not_null]
      - name: customer_id
        data_tests:
          - relationships:
              to: ref('dim_customers')
              field: customer_id
```

**Precision note on the original example:** `accepted_values` checks that each value is
*exactly* one of the listed strings. Applied to a full email address with values like
`'@gmail.com'`, every row fails. Test the pattern with an expression or regex, or
derive an `email_domain` column and test that.

The four built-in generic tests are `unique`, `not_null`, `accepted_values` and
`relationships`. Packages add many more: `dbt_utils` (`expression_is_true`, `recency`,
`unique_combination_of_columns`, `equal_rowcount`) and `dbt_expectations`
(Great-Expectations-style tests). **Singular tests** are one-off SQL files in `tests/`:

```sql
-- tests/assert_no_negative_order_totals.sql
select order_id, amount_paid
from {{ ref('fct_orders') }}
where amount_paid < 0
```

Configure `severity: warn` for soft checks, `error_if`/`warn_if` thresholds
(`">100"`), and `store_failures: true` to keep failing rows in a table for debugging.

### Unit tests (dbt 1.8+)

Data tests check the data you have; **unit tests check the logic** on inputs you
choose, including edge cases that are not in production yet. They run before the model
is built:

```yaml
# models/staging/shop/_shop__unit_tests.yml
unit_tests:
  - name: stg_users_lowercases_email_and_drops_deleted
    model: stg_shop__users
    given:
      - input: source('shop', 'users')
        rows:
          - {id: 1, email: "Ana@Example.COM", created_at: "2026-01-01 10:00:00", is_deleted: false}
          - {id: 2, email: "bo@example.com", created_at: "2026-01-02 10:00:00", is_deleted: true}
    expect:
      rows:
        - {user_id: 1, email: "ana@example.com"}
```

Run unit tests in development and CI (`dbt test --select test_type:unit`), not in
production builds, since their inputs are fixtures.

### Model contracts and versions

A **contract** (dbt 1.5+) makes a model's columns and types an enforced interface:
the build fails if the SQL's output does not match, and constraints like `not_null` or
`primary_key` are applied where the warehouse supports them.

```yaml
models:
  - name: dim_customers
    config:
      contract:
        enforced: true
    access: public              # other projects/teams may ref it
    columns:
      - name: customer_id
        data_type: varchar
        constraints:
          - type: not_null
      - name: city
        data_type: varchar
```

Combine contracts with **model versions** (`fct_orders_v2` alongside `v1`, with a
deprecation date) for breaking changes on widely used models, and **groups/access**
to keep private models private. This is the "data contract" idea applied inside the
warehouse; dbt Mesh uses it for cross-project references.

## 7. CI/CD for dbt

```arch
%% caption: Slim CI. A pull request builds only modified models and their children into a throwaway schema, deferring unchanged parents to production; merging runs the production job.
grid 150x100
node pr "Pull request" at 0,0 icon=git sub="changes 2 models"
node ci "CI runner" at 1,0 icon=workflow sub="dbt build state:modified+"
node art "Prod manifest" at 1,1 icon=file sub="from last prod run"
node ciwh "CI schema" at 2,0 icon=db sub="pr_1234, dropped after"
node prod "Prod schema" at 2,1 icon=db sub="unchanged parents"
node merge "Merge + deploy" at 0,1 icon=rocket sub="prod job runs"
pr -> ci
art -> ci : "--state"
ci -> ciwh : "build + test"
ciwh ..> prod : "--defer reads"
pr -> merge : "tests pass"
```

```yaml
# .github/workflows/dbt-ci.yml
name: dbt CI
on:
  pull_request:
    paths: ["models/**", "snapshots/**", "macros/**", "seeds/**", "dbt_project.yml"]

jobs:
  slim-ci:
    runs-on: ubuntu-latest
    env:
      SNOWFLAKE_ACCOUNT: ${{ secrets.SNOWFLAKE_ACCOUNT }}
      SNOWFLAKE_USER: ${{ secrets.SNOWFLAKE_CI_USER }}
      SNOWFLAKE_PRIVATE_KEY_PATH: /tmp/sf_key.p8
      DBT_CI_SCHEMA: pr_${{ github.event.number }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install dbt-snowflake==1.10.*
      - run: echo "${{ secrets.SNOWFLAKE_CI_KEY }}" > /tmp/sf_key.p8
      - run: dbt deps
      - name: Download production manifest
        run: aws s3 cp s3://dbt-artifacts/prod/manifest.json prod-artifacts/manifest.json
      - name: Build and test only what changed
        run: dbt build --target ci --select state:modified+ --defer --state prod-artifacts/
```

(The `ci` target in `profiles.yml` would set `schema: "{{ env_var('DBT_CI_SCHEMA') }}"`;
AWS credentials for the artifact download are omitted.)

- `state:modified+` compares the PR's manifest with production's and selects changed
  models plus their descendants.
- `--defer` makes `ref()`s to unchanged, unbuilt parents resolve to production
  objects, so CI does not rebuild the whole project.
- Add SQL linting (SQLFluff) and a check that every model has a description and
  primary-key tests. On merge, the production job (Airflow, dbt Cloud, or a CI deploy
  workflow) runs `dbt build` and uploads the new `manifest.json`.

General CI/CD practice lives in [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md);
test strategy in [The Testing Pyramid and Unit Tests](../TestingAndQuality/01_testing_pyramid.md).

## 8. Jinja, macros and packages

Jinja makes SQL programmable. Use it for genuinely repeated logic, not to hide simple
SQL.

```sql
-- macros/cents_to_dollars.sql
{% macro cents_to_dollars(column_name, scale=2) %}
    round({{ column_name }} / 100.0, {{ scale }})
{% endmacro %}
```

```sql
-- in a model
select
    order_id,
    {{ cents_to_dollars('amount_cents') }} as amount
from {{ ref('stg_shop__orders') }}
```

```sql
-- Generate one column per payment method (Jinja loop)
{% set methods = ['card', 'bank_transfer', 'gift_card'] %}
select
    order_id,
    {% for m in methods %}
    sum(case when payment_method = '{{ m }}' then amount else 0 end) as {{ m }}_amount
    {%- if not loop.last %},{% endif %}
    {% endfor %}
from {{ ref('stg_stripe__charges') }}
group by 1
```

Packages go in `packages.yml` and install with `dbt deps` (`dbt-labs/dbt_utils` for
`generate_surrogate_key`, `date_spine`, `pivot`, tests). Hooks
(`pre-hook`/`post-hook`, `on-run-end`) run grants or housekeeping SQL. dbt also
supports **Python models** (`def model(dbt, session)`) on Snowflake (Snowpark),
Databricks and BigQuery (Dataproc) for logic that is awkward in SQL.

## 9. Documentation, lineage and the semantic layer

- Descriptions in YAML plus `dbt docs generate` produce a browsable site with the
  lineage graph and column docs; the same metadata feeds catalogs (DataHub, Atlan,
  Unity Catalog, OpenMetadata).
- **Exposures** declare downstream dashboards and ML jobs in YAML, so lineage shows
  which dashboard breaks when a model changes.
- The **dbt Semantic Layer** (powered by MetricFlow) defines metrics (`revenue`,
  `active_customers`) once, with their measures, dimensions and join paths; BI tools
  then query metrics instead of re-implementing them. This addresses "every dashboard
  computes revenue differently".

## 10. dbt in production: failure modes and fixes

| Symptom | Cause | Fix |
|---|---|---|
| Nightly build takes hours | Everything is `table`; large models fully rebuilt every run | Incremental models for large facts; `microbatch` for event data; right-size warehouse; parallel threads |
| Incremental table drifted from truth | Late-arriving updates outside the filter; logic changed without full refresh | Lookback window + `unique_key`; periodic full refresh; compare with a full rebuild in a test environment |
| Duplicate keys in a fact | `append` strategy with reprocessed rows; upstream duplicates | `merge` with `unique_key`; dedupe in staging; `unique` test |
| Dashboard broken after a "harmless" rename | No contracts or exposures | Contracts on public models, exposures, `state:modified+` CI, model versions |
| Tests pass but numbers are wrong | Only generic tests; no logic tests | Unit tests, reconciliation tests against source totals, anomaly monitoring |
| Hundreds of tests fail after a source outage | Stale sources not caught upstream | `dbt source freshness` as the first step; `dbt build` skips downstream on failure |
| Project too big to understand | One monolithic project for all teams | Layering conventions, groups and access, dbt Mesh (multi-project with cross-project `ref`) |

**Alternatives and neighbours.** SQLMesh (virtual environments, column-level lineage,
semantic understanding of SQL), Google Dataform (BigQuery-native), Coalesce, and plain
warehouse features (Snowflake dynamic tables, BigQuery scheduled queries) for small
needs. dbt does not replace an orchestrator for non-SQL steps
([chapter 5](05_orchestration_airflow.md)): Airflow or Dagster typically runs
ingestion, then `dbt build`, then downstream jobs.

## Common interview questions

**What does dbt actually do?**
It compiles Jinja-templated `SELECT` statements into warehouse SQL, orders them by the
`ref()` graph, wraps them in the DDL/DML for their materialization, and runs them in
the warehouse. It also runs tests, snapshots and docs. It moves no data itself.

**Why `ref()` instead of hard-coding table names?**
It builds the dependency graph (run order, selection, lineage) and resolves to the
right database and schema per environment, so dev, CI and prod use the same code.

**View, table, incremental, ephemeral: how do you choose?**
Views for light staging logic; tables for marts that rebuild cheaply; incremental for
large, append-mostly facts where full rebuilds are too slow or expensive; ephemeral for
small reusable CTEs.

**How does an incremental model work, and what can go wrong?**
First run builds everything; later runs filter to new rows inside `is_incremental()`
and merge/append them by strategy. Risks: late updates missed by the filter (use a
lookback plus `unique_key`), duplicates with `append`, schema changes
(`on_schema_change`), and drift that needs periodic full refreshes.

**How do you implement SCD Type 2 in dbt?**
Snapshots with the timestamp or check strategy, which maintain `dbt_valid_from` and
`dbt_valid_to`. They only capture states present at each run; use CDC for complete
history. Never full-refresh a snapshot.

**Data tests vs. unit tests vs. contracts?**
Data tests query real data for violations (unique, not null, relationships). Unit
tests run model logic on fixed inputs to check transformations. Contracts enforce the
output schema (columns, types, constraints) as an interface for consumers.

**How do you keep CI fast on a 1,000-model project?**
Slim CI: `dbt build --select state:modified+ --defer --state <prod manifest>` into a
per-PR schema, so only changed models and their children are built and unchanged
parents are read from production.

**`dbt run` vs. `dbt build`?**
`run` only builds models. `build` runs seeds, models, snapshots and tests in DAG order
and skips children of failed tests, preventing bad data from propagating.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student / Intern | Intern, new learner | — | What ELT and dbt are; writes a model with `ref()` and `source()`; runs `dbt build` |
| Junior | Analytics Engineer / Data Engineer I | L3 | Staging/intermediate/marts layering; materializations; generic data tests; reads compiled SQL; source freshness |
| Mid | Analytics Engineer II / Data Engineer II | L4 | Writes correct incremental models (strategies, lookback, `unique_key`); snapshots; unit tests; macros and packages; selection syntax; slim CI |
| Senior | Senior Analytics / Data Engineer | L5 | Designs project structure and conventions; contracts, versions and access; performance and cost tuning (incremental, microbatch, clustering); debugging drift and duplicates; integrates dbt with orchestration and CDC |
| Staff+ | Staff Analytics Engineer / Data Architect | L6+ | Multi-project architecture (dbt Mesh) and ownership boundaries; data contracts with producing teams; semantic layer and metric governance; tooling choices (dbt Core vs. Cloud vs. Fusion vs. SQLMesh) |

## Interview checklist

- [ ] I can explain parse → compile → run and what SQL dbt generates for a view and a table.
- [ ] I can explain why `ref()` and `source()` matter and use graph selectors (`+model+`, `tag:`, `state:modified+`).
- [ ] I can lay out staging, intermediate and marts layers and their rules.
- [ ] I can choose between view, table, incremental, ephemeral and materialized view.
- [ ] I can write an incremental model with a lookback window, `unique_key` and a suitable strategy.
- [ ] I can configure a snapshot and explain its limits.
- [ ] I can use generic, package and singular data tests, and explain why `accepted_values` needs exact values.
- [ ] I can write a dbt unit test and explain contracts and model versions.
- [ ] I can set up slim CI with `--defer` and `--state`.
- [ ] I can diagnose incremental drift, duplicate keys and slow builds.

Related: [Subqueries and CTEs](../../data-and-apis/SQL/08_subqueries_and_ctes.md) (the CTE style every dbt model uses),
[Schema Migrations](../../data-and-apis/SQL/12_schema_migrations.md) (schema change discipline),
[Microservices: Contract Testing](../TestingAndQuality/05_contract_testing.md) (contracts between services, the same idea as model contracts),
[Batch and Stream Processing](../../interview-core/SystemDesign/building_blocks/21_batch_and_stream_processing.md).
