# Secret Management

Committing an API key or a database password to a Git repository is a critical security violation. Even if the repo is private, anyone who clones it (or a compromised CI/CD pipeline) has access to production data.

Secrets must be injected into applications at runtime.

## 1. The Wrong Ways

1. **Hardcoding in source code**: Disastrous.
2. **Hardcoding in Dockerfiles (`ENV DB_PASS=secret`)**: Anyone who pulls the image can run `docker inspect` and see the password.
3. **Committing `.env` files**: Easily leaked.

## 2. The Right Way: Injected Environment Variables

The application code should only know that the password lives in `os.Getenv("DB_PASSWORD")`. It should not know *how* it got there.

### AWS Secrets Manager / Parameter Store
You store the secret securely in AWS. During deployment, the CI/CD pipeline (or a Kubernetes operator like the External Secrets Operator) reads the secret from AWS and injects it into the container as an environment variable or a mounted file.

```arch
%% caption: The application reads standard environment variables, while an infrastructure operator handles fetching them securely from a Vault.
route straight
node sm "AWS Secrets Manager" at 0,0 icon=secrets color=red
group k8s "Kubernetes Cluster" color=slate style=dashed
node op "External Secrets\\nOperator" at 0,1 in k8s icon=worker color=slate
node sec "K8s Secret" at 0,2 in k8s icon=file color=slate
node pod "App Pod" at 0,3 in k8s icon=app color=blue

sm -> op : "Syncs (auth via IAM)"
op -> sec : "Creates"
sec -> pod : "Mounted as ENV"
```

## 3. HashiCorp Vault

Vault is the industry standard for multi-cloud, heavy-duty secret management. It goes far beyond simply storing static passwords.

### Dynamic Secrets
Instead of storing a static MySQL password in Vault, Vault connects to MySQL as an admin. When your app asks Vault for database credentials, Vault dynamically generates a brand new MySQL user/password that expires in 1 hour, and gives it to your app. 
If the app is compromised, the attacker's password expires in an hour anyway.

### Encryption as a Service (Transit Secrets Engine)
If your app needs to encrypt user PII (Personally Identifiable Information) before saving it to the database, the app shouldn't hold the encryption key. 
The app sends the plaintext to Vault via API: `POST /vault/encrypt {"plaintext": "123-45-678"}`. Vault encrypts it and returns the ciphertext. The app saves the ciphertext to the database. The app never sees the actual encryption key.
