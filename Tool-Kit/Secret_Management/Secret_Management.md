# Secret Management

## The Problem
In modern software development, applications require credentials (API keys, passwords, certificates) to communicate with databases and third-party services. Historically, these secrets were often hardcoded in source code or stored in plaintext configuration files. This led to "secret sprawl" where sensitive data was scattered across repositories, build logs, and developer workstations, greatly increasing the risk of exposure.

> [!TIP] See [01 Basic Env Vars](examples/01_basic_env_vars) for the traditional (and risky) way of managing basic environment variables.

## The Solution
Centralized Secret Management systems like HashiCorp Vault, AWS Secrets Manager, and Google Cloud Secret Manager provide a secure enclave for storing, managing, and auditing access to secrets. They offer encryption at rest and in transit, dynamic secret generation, and granular access controls.

## Interactive Examples
We provide several hands-on examples in the `examples/` directory to help you master secret management:
- [01 Basic Env Vars](examples/01_basic_env_vars)
- [02 Basic Vault CLI](examples/02_basic_vault_cli)
- [03 Intermediate Python Vault](examples/03_intermediate_python_vault)
- [04 Advanced AppRole Auth](examples/04_advanced_approle_auth)
- [05 Advanced Dynamic Secrets](examples/05_advanced_dynamic_secrets)

## Deep Dive: HashiCorp Vault

HashiCorp Vault is a ubiquitous tool for secrets management. It operates on a client-server architecture where the client authenticates to Vault to receive a token, which is then used to access secrets based on policies.

### Authentication Methods
Vault supports various authentication methods depending on the environment:
- **AppRole**: Primarily for machines and automated workflows. It requires a `RoleID` and `SecretID` to authenticate.
> [!TIP] Try the hands-on [04 Advanced AppRole Auth](examples/04_advanced_approle_auth) example to see this in action.
- **Kubernetes**: Allows pods to authenticate using their Kubernetes Service Account tokens. Vault validates the token with the Kubernetes API server.

### Secret Engines
Vault's secret engines are components that store, generate, or encrypt data:
- **KV (Key-Value)**: Stores arbitrary secrets in a key-value format. Version 2 supports secret versioning.
> [!TIP] Learn the basics of the KV engine in [02 Basic Vault CLI](examples/02_basic_vault_cli).
- **Dynamic Secrets**: Vault dynamically generates credentials on demand (e.g., database users with temporary passwords). These credentials have leases and are automatically revoked when the lease expires.
> [!TIP] Check out the [05 Advanced Dynamic Secrets](examples/05_advanced_dynamic_secrets) example for generating temporary PostgreSQL credentials.
- **Transit (Encryption as a Service)**: Vault handles encryption and decryption of data in transit and at rest without storing the data itself.

### Leasing and Revocation
All secrets in Vault have a lease associated with them. When a lease expires, Vault automatically revokes the secret. Clients can renew leases to extend access or Vault can instantly revoke secrets in case of a breach.

## Architecture Diagram

```arch
node app "App" at 0,1 icon=app
node vault "Vault" at 1,0 icon=vault-icon
node db "Database" at 1,2 icon=db
app -> vault : "1. Authenticate (AppRole)"
vault -> app : "2. Return Token"
app -> vault : "3. Request DB Secret"
vault -> app : "4. Return DB Credentials"
app -> db : "5. Connect using Credentials"
```

## Production-Grade Code Examples

### Python Example
Using the official `hvac` client library to authenticate via AppRole and read a KV secret.

> [!TIP] See the complete code and try it yourself in [03 Intermediate Python Vault](examples/03_intermediate_python_vault).

```python
import os
import hvac

def get_vault_secret(role_id, secret_id, secret_path):
    # Initialize the client
    client = hvac.Client(url=os.environ.get('VAULT_ADDR', 'http://127.0.0.1:8200'))
    
    # Authenticate via AppRole
    client.auth.approle.login(
        role_id=role_id,
        secret_id=secret_id,
    )
    
    if client.is_authenticated():
        # Read a KV v2 secret
        read_response = client.secrets.kv.v2.read_secret_version(path=secret_path)
        return read_response['data']['data']
    else:
        raise Exception("Vault authentication failed")

# Usage
# secrets = get_vault_secret('my-role-id', 'my-secret-id', 'my-app/db-credentials')
```

### Golang Example
Using the official `vault/api` library to read a secret.

```go
package main

import (
	"context"
	"fmt"
	"log"
	"os"

	vault "github.com/hashicorp/vault/api"
)

func main() {
	config := vault.DefaultConfig()
	config.Address = os.Getenv("VAULT_ADDR")

	client, err := vault.NewClient(config)
	if err != nil {
		log.Fatalf("Unable to initialize Vault client: %v", err)
	}

	// Read token from environment variable or authenticate
	client.SetToken(os.Getenv("VAULT_TOKEN"))

	// Read a KV v2 secret
	secret, err := client.KVv2("secret").Get(context.Background(), "my-app/db-credentials")
	if err != nil {
		log.Fatalf("Unable to read secret: %v", err)
	}

	fmt.Printf("Secret Data: %v\n", secret.Data)
}
```

## MAANG-Level Interview Questions

1. **What is the difference between static and dynamic secrets in HashiCorp Vault?**
   *Answer*: Static secrets (KV) are stored manually and persist until updated or deleted. Dynamic secrets are generated on-the-fly (e.g., creating a short-lived database user) and are automatically revoked when their lease expires, minimizing the risk of credential leakage.

2. **How does Transit secret engine differ from Key-Value storage?**
   *Answer*: The Key-Value engine stores data securely within Vault. The Transit engine does not store the data; it acts as "Encryption as a Service," receiving plaintext, encrypting it, and returning the ciphertext to the application to store externally.

3. **Explain the concept of 'Secret Zero' and how AppRole attempts to solve it.**
   *Answer*: 'Secret Zero' is the initial credential required to authenticate to the secret manager (a chicken-and-egg problem). AppRole splits this into `RoleID` and `SecretID`, which can be delivered via separate trusted channels (e.g., CM tool injects RoleID, pipeline injects SecretID), reducing the risk of a single point of compromise.

4. **How would you architect a highly available Vault cluster?**
   *Answer*: Use a storage backend that supports High Availability (HA) like Consul or Integrated Storage (Raft). Deploy multiple Vault nodes; one becomes the active node handling requests, and others are standby. Put a load balancer in front that routes to the active node.

5. **Describe the sealing/unsealing process in Vault.**
   *Answer*: Vault starts in a sealed state where it knows where the data is and how to access the storage backend, but it cannot decrypt the data because it lacks the master key. Unsealing requires combining Shamir's Secret Shares (or using Auto-unseal via cloud KMS) to reconstruct the master key in memory to decrypt the encryption key.

6. **How do you handle secret rotation for a high-throughput application without downtime?**
   *Answer*: Implement dynamic secrets or overlapping leases. The application should catch authentication failures and dynamically re-authenticate or re-fetch credentials from Vault, using connection pooling that seamlessly replaces old connections with new ones using updated credentials.

7. **What is Kubernetes Service Account authentication in Vault?**
   *Answer*: Vault authenticates pods by having the pod send its projected Service Account Token to Vault. Vault then queries the Kubernetes TokenReview API to verify the token's identity and issues a Vault token mapped to a specific policy.

8. **How does Vault prevent split-brain scenarios in its HA mode?**
   *Answer*: The underlying HA backend (e.g., Consul or Raft) uses consensus algorithms (like Raft) to elect a leader and require a quorum to commit changes, preventing multiple nodes from acting as the active node simultaneously.

9. **What are Vault Agent and Vault Agent Injector?**
   *Answer*: Vault Agent is a client daemon that handles authentication, token lifecycle management, and templating secrets to files. In Kubernetes, the Vault Agent Injector uses a Mutating Admission Webhook to automatically inject the Vault Agent into pods to fetch and manage secrets transparently.

10. **Explain how you would monitor Vault in a production environment.**
    *Answer*: Monitor telemetry metrics (Prometheus/Grafana) for active node status, memory/CPU usage, token creation rates, lease expiration rates, and storage backend latency. Additionally, ingest Vault audit logs into a SIEM (like Splunk or ELK) to track unauthorized access attempts and access patterns.
