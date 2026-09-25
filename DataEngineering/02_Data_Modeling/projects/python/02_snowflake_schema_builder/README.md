# Snowflake Schema Builder

This project extends the Star schema concept by normalizing the dimension tables into a Snowflake schema. Specifically, the location data is split into hierarchical tables: `dim_country`, `dim_state`, and `dim_city`.

## Overview
- **Fact Table:** `fact_sales`
- **Normalized Dimensions:** `dim_store` -> `dim_city` -> `dim_state` -> `dim_country`

## How to Run
```bash
python main.py
```
