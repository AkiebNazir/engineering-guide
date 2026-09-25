# 03 Data Vault Hub Link Sat

This project implements a basic Data Vault 2.0 schema in Go using SQLite.
It consists of a Hub (`Hub_Customer`), a Link (`Link_Transaction`), and a Satellite (`Sat_Customer_Demographics`).

## Running the project

1. Initialize a Go module (if not done): `go mod init data-vault`
2. Install SQLite driver: `go get github.com/mattn/go-sqlite3`
3. Run the code: `go run main.go`
