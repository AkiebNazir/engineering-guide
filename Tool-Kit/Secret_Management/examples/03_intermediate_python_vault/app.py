import os
import hvac

# Ensure VAULT_ADDR and VAULT_TOKEN are set in the environment
vault_url = os.getenv('VAULT_ADDR', 'http://127.0.0.1:8200')
vault_token = os.getenv('VAULT_TOKEN', 'root')

client = hvac.Client(url=vault_url, token=vault_token)

if client.is_authenticated():
    print("Successfully authenticated to Vault!")
    
    try:
        # Read from KV v2 engine (default in dev mode for 'secret/')
        read_response = client.secrets.kv.v2.read_secret_version(path='my-app')
        secret_data = read_response['data']['data']
        print(f"Retrieved keys: {list(secret_data.keys())}")
    except Exception as e:
        print(f"Error reading secret: {e}")
else:
    print("Failed to authenticate to Vault.")
