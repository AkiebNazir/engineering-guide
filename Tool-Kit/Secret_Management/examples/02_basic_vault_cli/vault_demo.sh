#!/bin/bash
set -e

echo "Starting Vault in dev mode in the background..."
vault server -dev -dev-root-token-id="root" &
VAULT_PID=$!

# Wait for vault to start
sleep 3
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

echo "Writing a secret to secret/my-app..."
vault kv put secret/my-app api_key="vault_secure_key_456" db_pass="vault_db_password"

echo "Reading the secret back..."
vault kv get secret/my-app

echo "Cleaning up..."
kill $VAULT_PID
