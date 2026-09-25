# 02_parquet_vs_csv_benchmarker

This script compares the file size and write times between CSV and Parquet.

## How to Run

1. Initialize Go module:
   ```bash
   go mod init benchmarker
   ```
2. Install dependencies:
   ```bash
   go get github.com/xitongsys/parquet-go-source/local
   go get github.com/xitongsys/parquet-go/parquet
   go get github.com/xitongsys/parquet-go/writer
   ```
3. Run the script:
   ```bash
   go run main.go
   ```
