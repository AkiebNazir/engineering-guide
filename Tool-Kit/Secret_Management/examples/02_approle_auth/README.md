# AppRole Authentication (Python)
AppRole is an authentication mechanism tailored for machines and services. This example shows how to authenticate using a `role_id` and `secret_id` to obtain a client token.

## Prerequisites
- Vault running locally: `vault server -dev -dev-root-token-id="root"`
- Enable AppRole: `vault auth enable approle`
- Create a role: `vault write auth/approle/role/my-role policies="default"`
- Get Role ID: `vault read auth/approle/role/my-role/role-id`
- Get Secret ID: `vault write -f auth/approle/role/my-role/secret-id`

## Running
```bash
export VAULT_ADDR='http://127.0.0.1:8200'
export VAULT_ROLE_ID='<role_id>'
export VAULT_SECRET_ID='<secret_id>'
python main.py
```
