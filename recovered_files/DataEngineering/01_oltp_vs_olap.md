# OLTP vs OLAP & Data Warehouses

Backend engineers usually work with OLTP systems. Data engineers work with OLAP systems.

## 1. OLTP (Online Transaction Processing)
- **Goal**: Fast, reliable transactions for the user application (e.g., placing an order).
- **Databases**: Postgres, MySQL, MongoDB, DynamoDB.
- **Data Shape**: Highly normalized (3NF) to prevent anomalies during updates. Row-oriented storage.
- **Queries**: Milliseconds. "Get the current balance for user 42." "Insert a new order."

## 2. OLAP (Online Analytical Processing)
- **Goal**: Complex queries over massive datasets for business intelligence.
- **Databases**: Snowflake, BigQuery, Redshift (Data Warehouses).
- **Data Shape**: Denormalized (Star Schema) to make querying easier. Column-oriented storage.
- **Queries**: Seconds to minutes. "What was the average revenue per user by country over the last 5 years?"

## 3. The ETL/ELT Pipeline

Data is useless if it's trapped in isolated OLTP databases. Data Engineers build pipelines to move it into the Data Warehouse.

```arch
%% caption: The modern ELT pipeline extracts raw data, loads it into the warehouse, and then transforms it in-place using massive parallel compute.
route straight
node pg "Postgres\n(OLTP)" at 0,0 icon=db color=blue
node kafka "Kafka\n(Events)" at 2,0 icon=network color=amber

group bq "BigQuery (OLAP)" color=slate style=dashed
node raw "Raw Layer" at 1,1 in bq icon=file color=slate
node clean "Clean Layer" at 1,2 in bq icon=doc color=blue
node agg "Aggregations" at 1,3 in bq icon=dashboard color=green

pg -> raw : "Extract/Load"
kafka -> raw : "Extract/Load"
raw -> clean : "Transform"
clean -> agg : "Transform"
```

### ETL vs ELT
- **ETL (Extract, Transform, Load)**: The old way. A dedicated server extracts data from Postgres, transforms it (cleans it, joins it) in memory, and *then* loads it into the Warehouse. This requires huge, expensive transformation servers.
- **ELT (Extract, Load, Transform)**: The modern way. Extract raw data and dump it directly into the Warehouse. Use the massive compute power of the Warehouse itself (using tools like `dbt`) to write SQL queries that transform the raw tables into clean tables.
