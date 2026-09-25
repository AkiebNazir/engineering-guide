# 04_data_warehouse_schema_builder

This script builds a local data warehouse Star Schema using SQLite.

## How to Run

1. Initialize Go module:
   ```bash
   go mod init dwbuilder
   ```
2. Install SQLite driver:
   ```bash
   go get github.com/mattn/go-sqlite3
   ```
3. Run the script:
   ```bash
   go run main.go
   ```
   *This will create a `warehouse.db` file containing `dim_users`, `dim_products`, and `fact_sales` tables.*
