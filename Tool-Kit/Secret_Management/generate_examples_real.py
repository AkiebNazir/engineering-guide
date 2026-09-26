import os

base = "/Users/njasm/Njasm/AI/engineering-guide/Tool-Kit/Secret_Management"
files = {}

# --- PYTHON ---
files["examples/01_kv_read_write/README.md"] = """# KV V2 Secret Read/Write (Python)
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
"""
files["examples/01_kv_read_write/main.py"] = """import os
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
"""

files["examples/02_approle_auth/README.md"] = """# AppRole Authentication (Python)
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
"""
files["examples/02_approle_auth/main.py"] = """import os
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
"""

files["examples/03_dynamic_db_secrets/README.md"] = """# Dynamic Database Secrets (Python)
Vault can generate dynamic credentials for databases that expire after a set lease time. This example requests ephemeral PostgreSQL credentials.
"""
files["examples/03_dynamic_db_secrets/main.py"] = """import os
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
"""

files["examples/04_transit_encryption/README.md"] = """# Transit Encryption as a Service (Python)
The Transit secret engine provides "encryption as a service". It encrypts/decrypts data without storing it in Vault.
"""
files["examples/04_transit_encryption/main.py"] = """import os
import hvac
import base64

def main():
    client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
    
    plaintext = "Confidential User Data".encode('utf-8')
    encoded_plaintext = base64.b64encode(plaintext).decode('utf-8')
    
    encrypt_res = client.secrets.transit.encrypt_data(
        name='my-app-key',
        plaintext=encoded_plaintext
    )
    ciphertext = encrypt_res['data']['ciphertext']
    print(f"Ciphertext: {ciphertext}")

    decrypt_res = client.secrets.transit.decrypt_data(
        name='my-app-key',
        ciphertext=ciphertext
    )
    decoded_plaintext = base64.b64decode(decrypt_res['data']['plaintext']).decode('utf-8')
    print(f"Decrypted Data: {decoded_plaintext}")

if __name__ == '__main__':
    main()
"""

files["examples/05_aws_dynamic_secrets/README.md"] = """# AWS Dynamic Secrets (Python)
Vault can dynamically generate IAM users/STS tokens for AWS based on policy.
"""
files["examples/05_aws_dynamic_secrets/main.py"] = """import os
import hvac

def main():
    client = hvac.Client(url=os.getenv('VAULT_ADDR'), token=os.getenv('VAULT_TOKEN'))
    aws_creds = client.secrets.aws.generate_credentials(name='my-s3-role')
    print("Generated AWS Credentials:")
    print(f"Access Key: {aws_creds['data']['access_key']}")
    print(f"Secret Key: {aws_creds['data']['secret_key']}")

if __name__ == '__main__':
    main()
"""

# --- GOLANG ---
files["examples_go/01_kv_read_write/README.md"] = """# KV V2 Secret Read/Write (Golang)
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
"""
files["examples_go/01_kv_read_write/main.go"] = """package main

import (
	"context"
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)

func main() {
	config := api.DefaultConfig()
	client, err := api.NewClient(config)
	if err != nil {
		log.Fatalf("Unable to initialize Vault client: %v", err)
	}

	client.SetToken(os.Getenv("VAULT_TOKEN"))
	ctx := context.Background()
	secretData := map[string]interface{}{"api_key": "go-secret-123", "db_pass": "go-pass-456"}

	_, err = client.KVv2("secret").Put(ctx, "myapp/config", secretData)
	if err != nil {
		log.Fatalf("Unable to write secret: %v", err)
	}
	fmt.Println("Secret successfully written.")

	secret, err := client.KVv2("secret").Get(ctx, "myapp/config")
	if err != nil {
		log.Fatalf("Unable to read secret: %v", err)
	}
	fmt.Printf("Retrieved Secret: %v\\n", secret.Data)
}
"""

files["examples_go/02_approle_auth/README.md"] = """# AppRole Authentication (Golang)
Authenticates a machine identity against Vault using an AppRole RoleID and SecretID to dynamically acquire a token.
"""
files["examples_go/02_approle_auth/main.go"] = """package main
import (
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)
func main() {
	config := api.DefaultConfig()
	client, err := api.NewClient(config)
	if err != nil { log.Fatalf("Unable to initialize client: %v", err) }

	data := map[string]interface{}{
		"role_id":   os.Getenv("VAULT_ROLE_ID"),
		"secret_id": os.Getenv("VAULT_SECRET_ID"),
	}

	resp, err := client.Logical().Write("auth/approle/login", data)
	if err != nil { log.Fatalf("AppRole login failed: %v", err) }

	client.SetToken(resp.Auth.ClientToken)
	fmt.Println("Successfully authenticated via AppRole!")
}
"""

files["examples_go/03_dynamic_db_secrets/README.md"] = """# Dynamic Database Secrets (Golang)"""
files["examples_go/03_dynamic_db_secrets/main.go"] = """package main
import (
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)
func main() {
	client, _ := api.NewClient(api.DefaultConfig())
	client.SetToken(os.Getenv("VAULT_TOKEN"))

	secret, err := client.Logical().Read("database/creds/my-app-role")
	if err != nil || secret == nil { log.Fatalf("Unable to read dynamic DB credentials: %v", err) }

	fmt.Printf("Dynamic DB Username: %s\\n", secret.Data["username"])
	fmt.Printf("Dynamic DB Password: %s\\n", secret.Data["password"])
}
"""

files["examples_go/04_transit_encryption/README.md"] = """# Transit Encryption as a Service (Golang)"""
files["examples_go/04_transit_encryption/main.go"] = """package main
import (
	"encoding/base64"
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)
func main() {
	client, _ := api.NewClient(api.DefaultConfig())
	client.SetToken(os.Getenv("VAULT_TOKEN"))

	plaintext := []byte("Confidential Go Data")
	encodedPlaintext := base64.StdEncoding.EncodeToString(plaintext)

	encData := map[string]interface{}{"plaintext": encodedPlaintext}
	encResp, err := client.Logical().Write("transit/encrypt/my-app-key", encData)
	if err != nil { log.Fatalf("Encryption failed: %v", err) }
	
	ciphertext := encResp.Data["ciphertext"].(string)
	fmt.Printf("Ciphertext: %s\\n", ciphertext)

	decData := map[string]interface{}{"ciphertext": ciphertext}
	decResp, err := client.Logical().Write("transit/decrypt/my-app-key", decData)
	
	decodedRaw, _ := base64.StdEncoding.DecodeString(decResp.Data["plaintext"].(string))
	fmt.Printf("Decrypted Data: %s\\n", string(decodedRaw))
}
"""

files["examples_go/05_aws_dynamic_secrets/README.md"] = """# AWS Dynamic Secrets (Golang)"""
files["examples_go/05_aws_dynamic_secrets/main.go"] = """package main
import (
	"fmt"
	"log"
	"os"
	"github.com/hashicorp/vault/api"
)
func main() {
	client, _ := api.NewClient(api.DefaultConfig())
	client.SetToken(os.Getenv("VAULT_TOKEN"))

	secret, err := client.Logical().Read("aws/creds/my-s3-role")
	if err != nil || secret == nil { log.Fatalf("Unable to read AWS credentials: %v", err) }

	fmt.Println("Generated AWS Credentials:")
	fmt.Printf("Access Key: %s\\n", secret.Data["access_key"])
	fmt.Printf("Secret Key: %s\\n", secret.Data["secret_key"])
}
"""

for filepath, content in files.items():
    full_path = os.path.join(base, filepath)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w") as f:
        f.write(content.strip() + "\n")
