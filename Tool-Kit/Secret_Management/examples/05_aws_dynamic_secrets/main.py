import os
import hvac

def main():
    client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
    aws_creds = client.secrets.aws.generate_credentials(name='my-s3-role')
    print("Generated AWS Credentials:")
    print(f"Access Key: {aws_creds['data']['access_key']}")
    print(f"Secret Key: {aws_creds['data']['secret_key']}")

if __name__ == '__main__':
    main()
