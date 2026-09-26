import os
import hvac

def main():
    client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
    
    # Request dynamic credentials for a configured postgres role
    db_creds = client.secrets.database.generate_credentials(name='my-app-role')
    
    username = db_creds['data']['username']
    password = db_creds['data']['password']
    lease_duration = db_creds['lease_duration']

    print(f"Dynamic DB Username: {username}")
    print(f"Dynamic DB Password: {password}")
    print(f"Valid for: {lease_duration} seconds")

if __name__ == '__main__':
    main()
