# 04 SCD Type 2 Implementer

This project demonstrates Slowly Changing Dimension (SCD) Type 2 tracking in Go using SQLite.
It updates a customer's old record by setting `EndDate` and `IsCurrent = 0`, and inserts a new row.

## Running the project

1. Initialize a Go module (if not done): `go mod init scd-type2`
2. Install SQLite driver: `go get github.com/mattn/go-sqlite3`
3. Run the code: `go run main.go`
