# 02 Snowflake Schema Builder

This project demonstrates how to build a Snowflake Schema in Go using SQLite.
It includes a normalized dimension (`DimStore` linked to `DimRegion`) and a Fact table (`FactSales`).

## Running the project

1. Initialize a Go module (if not done): `go mod init snowflake-schema`
2. Install SQLite driver: `go get github.com/mattn/go-sqlite3`
3. Run the code: `go run main.go`
