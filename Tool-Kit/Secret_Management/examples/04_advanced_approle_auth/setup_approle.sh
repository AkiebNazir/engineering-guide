#!/bin/bash
set -e

export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_TOKEN='root'

echo "Enabling AppRole auth method..."
vault auth enable approle || echo "AppRole already enabled"

echo "Creating a policy for our app..."
vault policy write my-app-policy - <<EOF
path "secret/data/my-app" {
  capabilities = ["read"]
}
EOF

echo "Creating the AppRole..."
vault write auth/approle/role/my-app-role \
    token_policies="my-app-policy" \
    token_ttl=1h \
    token_max_ttl=4h

echo "Fetching RoleID..."
ROLE_ID=$(vault read -field=role_id auth/approle/role/my-app-role/role-id)
echo "RoleID: $ROLE_ID"

echo "Generating SecretID..."
SECRET_ID=$(vault write -f -field=secret_id auth/approle/role/my-app-role/secret-id)
echo "SecretID: $SECRET_ID"

echo "Logging in with AppRole..."
vault write auth/approle/login role_id="$ROLE_ID" secret_id="$SECRET_ID"
