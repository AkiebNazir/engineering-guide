import os

files = {
    "06_Data_Orchestration/06_Data_Orchestration.md": """# Data Orchestration

Data orchestration tools schedule, manage, and monitor the execution of data pipelines.

## 1. Directed Acyclic Graphs (DAGs)
A DAG is a collection of all the tasks you want to run, organized in a way that reflects their relationships and dependencies.
- **Directed**: Tasks have a defined order (A must run before B).
- **Acyclic**: No loops are allowed. A task cannot depend on itself or a downstream task.

## 2. Apache Airflow
The industry standard for data orchestration.
- **Scheduler**: Triggers workflows and submits tasks to the executor.
- **Webserver**: Provides a UI to inspect, trigger, and debug DAGs.
- **Executor / Workers**: Processes the actual tasks.
- **Metadata Database**: Stores state, variables, and connections.

### Core Concepts
- **Operators**: Define a single task (e.g., `PythonOperator`, `BashOperator`).
- **Sensors**: Special operators that wait for a certain condition to be met (e.g., wait for a file to arrive in S3).
- **XCom (Cross-Communication)**: A mechanism to share small amounts of data between tasks.

```mermaid
flowchart LR
    Start([Start]) --> Extract[Extract Data]
    Extract --> Transform[Transform Data]
    Transform --> Load[Load Data]
    Load --> End([End])
```

## 3. Idempotency
A critical concept in data orchestration. A task is idempotent if running it multiple times produces the same result as running it once. This ensures that retrying failed tasks doesn't corrupt data.
""",
    "07_Data_Transformation/07_Data_Transformation.md": """# Data Transformation

Transformation is the process of cleaning, structuring, and enriching raw data into a desired format.

## 1. ETL vs ELT
- **ETL (Extract, Transform, Load)**: Data is transformed before it is loaded into the warehouse. Uses separate processing servers (e.g., Spark, Dataflow).
- **ELT (Extract, Load, Transform)**: Data is loaded raw into the warehouse, and the warehouse's own compute power is used to transform it via SQL.

## 2. dbt (Data Build Tool)
dbt has revolutionized ELT by allowing data analysts and engineers to transform data in their warehouses simply by writing select statements.

### Key Concepts
- **Models**: SQL SELECT statements. dbt wraps them in CREATE TABLE/VIEW automatically.
- **Materializations**: How models are built (table, view, incremental, ephemeral).
- **Macros**: Snippets of SQL combined with Jinja templating to reuse logic.
- **Tests**: Assertions about your data (e.g., `unique`, `not_null`, `accepted_values`).

```mermaid
flowchart TD
    Raw[Raw Data] --> Staging[Staging Models]
    Staging --> Intermediate[Intermediate Models]
    Intermediate --> Fact[Fact/Dimension Models]
    Fact --> Mart[Data Marts / BI]
```

## 3. Jinja Templating
dbt uses Jinja to add control structures (like `if` statements and `for` loops) to SQL.
Example: Using a loop to pivot rows into columns dynamically.
""",
    "08_Data_Governance_and_Quality/08_Data_Governance_and_Quality.md": """# Data Governance and Quality

As data platforms grow, ensuring the data is accurate, secure, and understandable becomes paramount.

## 1. Data Quality
Ensuring data meets business expectations.
- **Great Expectations**: A framework to define, document, and validate data quality.
- **Anomaly Detection**: Using statistical methods or ML to detect spikes or drops in data volumes or values.

## 2. Data Lineage
Understanding the lifecycle of data: where it originated, how it was transformed, and where it is consumed.
- Crucial for debugging ("Why is this dashboard wrong?") and compliance ("Where is PII used?").

## 3. Metadata Management & Data Catalogs
A centralized repository to understand what data exists.
- **Tools**: Amundsen, Datahub, Alation.
- **Purpose**: Allows users to search for tables, see their schemas, owners, and documentation.

## 4. Data Privacy & Security
- **RBAC (Role-Based Access Control)**: Restricting access based on a user's role.
- **Data Masking / Hashing**: Obfuscating PII (Personally Identifiable Information) like emails or SSNs before they reach downstream analysts.

## 5. Data Observability
The ability to fully understand the health of your data systems.
1. **Freshness**: Is the data up to date?
2. **Distribution**: Is the data within expected ranges?
3. **Volume**: Is the data complete?
4. **Schema**: Did the structure change?
5. **Lineage**: What depends on this data?
"""
}

for filepath, content in files.items():
    with open(filepath, 'w') as f:
        f.write(content)

print("Restored theory files.")
