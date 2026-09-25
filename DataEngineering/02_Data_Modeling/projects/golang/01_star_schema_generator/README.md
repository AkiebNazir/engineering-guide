# 01 Star Schema Generator

This project demonstrates how to create a simple Star Schema in Go using SQLite. 
It defines a Fact table (`FactSales`) and two Dimension tables (`DimTime`, `DimProduct`).

## Running the project

1. Initialize a Go module (if not done): `go mod init star-schema`
2. Install SQLite driver: `go get github.com/mattn/go-sqlite3`
3. Run the code: `go run main.go`
