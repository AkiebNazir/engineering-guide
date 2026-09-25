# Data Transformation with dbt

In the ELT (Extract, Load, Transform) paradigm, raw data is dumped into a Data Warehouse (Snowflake, BigQuery). Now it needs to be transformed into clean Star Schemas.

Historically, this meant writing hundreds of massive stored procedures. **dbt (data build tool)** revolutionized this by bringing software engineering best practices (version control, testing, modularity) to SQL.

## 1. How dbt Works

dbt is a command-line tool. You write `SELECT` statements, and dbt wraps them in `CREATE TABLE` or `CREATE VIEW` statements and executes them against the Data Warehouse.

You don't write DDL (Data Definition Language). You just write the logic.

```sql
-- models/clean_users.sql
WITH raw_users AS (
    SELECT * FROM {{ source('raw_postgres', 'users') }}
)

SELECT
    id AS user_id,
    LOWER(email) AS email,
    created_at
FROM raw_users
WHERE is_deleted = false
```

When you run `dbt run`, dbt connects to Snowflake and executes:
```sql
CREATE OR REPLACE TABLE my_schema.clean_users AS (
    WITH raw_users AS (
        SELECT * FROM raw_postgres.users
    )
    SELECT ...
)
```

## 2. The DAG and `ref()`

dbt automatically builds a DAG based on how models reference each other using the `{{ ref() }}` macro.

If `model_b` has `SELECT * FROM {{ ref('model_a') }}`, dbt knows it must execute `model_a` before `model_b`. This eliminates the need for complex manual scheduling.

## 3. Testing

Data quality is the hardest part of data engineering. dbt allows you to write tests in simple YAML.

```yaml
version: 2
models:
  - name: clean_users
    columns:
      - name: user_id
        tests:
          - unique
          - not_null
      - name: email
        tests:
          - accepted_values:
              values: ['@gmail.com', '@yahoo.com']
```

When you run `dbt test`, dbt automatically generates and executes SQL queries to verify that `user_id` is truly unique and has no nulls. If a test fails, the CI pipeline fails, preventing bad data models from being deployed.

## 4. Materializations

dbt allows you to configure how the SQL is materialized in the database using a simple config block at the top of the file:

- **View**: `{{ config(materialized='view') }}`. Creates a `CREATE VIEW`. Recomputed every time a user queries it. Cheap to build, slow to query.
- **Table**: `{{ config(materialized='table') }}`. Creates a `CREATE TABLE`. Drops and rebuilds the entire table from scratch. Fast to query, expensive to build if the table is 10TB.
- **Incremental**: `{{ config(materialized='incremental') }}`. Only transforms the *new* rows that have arrived since the last time dbt ran, appending them to the existing table. Complex to write, but highly efficient for massive tables.
