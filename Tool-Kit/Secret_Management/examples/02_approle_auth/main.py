import os
import hvac

def main():
    client = hvac.Client(url=os.getenv('VAULT_ADDR'))
    role_id = os.getenv('VAULT_ROLE_ID')
    secret_id = os.getenv('VAULT_SECRET_ID')

    # Login using AppRole
    response = client.auth.approle.login(role_id=role_id, secret_id=secret_id)
    client.token = response['auth']['client_token']

    if client.is_authenticated():
        print("Successfully authenticated using AppRole!")
    else:
        print("AppRole authentication failed.")

if __name__ == '__main__':
    main()
