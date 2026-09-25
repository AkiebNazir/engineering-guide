# 02 Beginner HTTP API Client

This project makes a GET request to a public REST API (JSONPlaceholder), unmarshals the JSON response into Go structs, and inserts the data into a local SQLite database.

## Usage
Since this depends on `go-sqlite3`, you will need to initialize a Go module and install dependencies:
```bash
go mod init http_client
go get github.com/mattn/go-sqlite3
go run main.go
```
