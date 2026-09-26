# KV V2 Secret Read/Write (Python)
Demonstrates how to read and write static secrets to HashiCorp Vault's KV Version 2 secret engine using the `hvac` library.
KV V2 supports versioning, allowing you to keep a history of your secrets.

## Prerequisites
- Vault running locally: `vault server -dev -dev-root-token-id="root"`
- Python dependencies: `pip install hvac`

## Running
```bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'
python main.py
```
