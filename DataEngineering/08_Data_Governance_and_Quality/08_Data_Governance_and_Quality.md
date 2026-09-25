# Data Governance and Quality

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
