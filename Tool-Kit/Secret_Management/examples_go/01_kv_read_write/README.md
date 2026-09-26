# KV V2 Secret Read/Write (Golang)
Demonstrates reading and writing to the KV V2 secret engine using the official Vault Go API client.

## Prerequisites
- Vault running locally: `vault server -dev -dev-root-token-id="root"`
- Go init: `go mod init kv && go get github.com/hashicorp/vault/api`

## Running
```bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'
go run main.go
```
