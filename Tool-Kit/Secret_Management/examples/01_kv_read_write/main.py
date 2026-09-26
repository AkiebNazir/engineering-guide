import os
import hvac

def main():
    client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
    if not client.is_authenticated():
        raise Exception("Vault authentication failed.")

    # Write a secret
    secret_path = 'myapp/config'
    secret_data = {'api_key': 'super-secret-key-123', 'db_pass': 'db-pass-456'}
    client.secrets.kv.v2.create_or_update_secret(path=secret_path, secret=secret_data)
    print(f"Secret written to {secret_path}")

    # Read the secret
    read_response = client.secrets.kv.v2.read_secret_version(path=secret_path)
    retrieved_data = read_response['data']['data']
    print(f"Retrieved Secret: {retrieved_data}")

if __name__ == '__main__':
    main()
