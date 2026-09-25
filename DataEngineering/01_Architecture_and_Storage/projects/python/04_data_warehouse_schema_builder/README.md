# Data Warehouse Schema Builder

This project demonstrates how to build a basic Star Schema (Fact and Dimension tables) using an in-memory SQLite database.

## Usage

Run the script:

```bash
python main.py
```

This will define the DDL for `dim_date`, `dim_product`, and `fact_sales`, insert some mock data, and run a join query representing typical analytical workloads.
