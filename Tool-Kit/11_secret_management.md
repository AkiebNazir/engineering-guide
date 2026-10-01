# Secret Management

Committing an API key or a database password to a Git repository is one of the most
common ways real companies get breached. Even in a private repository, everyone who
clones it, every CI system that checks it out, and every backup of it now holds a
production credential, forever, because Git history does not forget. This chapter
explains what counts as a secret and why it is hard to handle, then covers the working
toolkit: how secrets reach an application at runtime, cloud secret managers and the
External Secrets Operator, Kubernetes Secrets and their limits, HashiCorp Vault (dynamic
secrets, leases, encryption as a service), workload identity that removes secrets
altogether, rotation, and leak detection and response.

## Foundations — What is a secret, and why is it hard to keep one?

### What counts as a secret

A **secret** is any value that grants access or proves identity: database passwords,
API keys and tokens, OAuth client secrets, TLS private keys, SSH keys, signing keys,
cloud access keys, webhook signing secrets, encryption keys. Configuration such as a
database *hostname* or a feature flag is not a secret; mixing the two is how passwords
end up in plain config files.

### Why it is hard

An application needs the secret in memory in plain text to use it, so the problem is
not "encrypt it" but **controlling every place it travels**: the developer's laptop,
the repository, the CI system, the container image, the orchestrator, the process
environment, logs, crash dumps and backups. Every copy is a place it can leak from. Good
secret management reduces the number of copies, narrows who and what can read each one,
makes each secret short-lived, and records every access.

### The pieces of a modern setup

| Piece | Job | Examples |
|---|---|---|
| **Secret store** | the single, encrypted source of truth, with access control and audit logs | HashiCorp Vault / OpenBao, AWS Secrets Manager, GCP Secret Manager, Azure Key Vault |
| **Identity** | proves *which workload* is asking, without a password of its own | Kubernetes service account tokens, cloud IAM roles, SPIFFE IDs, OIDC tokens from CI |
| **Delivery** | puts the secret where the app can read it | External Secrets Operator, Vault Agent, CSI Secrets Store driver, SDK calls at startup |
| **Key management (KMS)** | holds the master keys that encrypt everything else, usually in HSMs | AWS KMS, Cloud KMS, Azure Key Vault keys |
| **Detection** | finds secrets that escaped into code, logs or images | GitHub secret scanning and push protection, gitleaks, TruffleHog |

### An everyday analogy

A hotel does not hand every guest a master key. The front desk (the secret store)
checks your identity (workload identity), gives you a key card for one room (least
privilege) that stops working at checkout (a lease or TTL), logs every issue (audit),
and can cancel a card instantly if you lose it (revocation). Secret management
reproduces each of those properties for machines.

## 1. The wrong ways, and why they fail

| Anti-pattern | How it leaks |
|---|---|
| Hardcoded in source code | every clone, fork, code search, CI log and backup; Git history keeps it after you delete the line |
| `ENV DB_PASS=secret` or `ARG` in a Dockerfile | baked into image layers: `docker history` and `docker inspect` show it to anyone who can pull the image |
| Committed `.env` files | the same as source code; `.gitignore` only helps if it existed *before* the first commit |
| Pasted into Slack, tickets, wikis | searchable, retained, shared with third-party integrations |
| One shared "prod" password for everyone and every service | no attribution, no way to revoke one user or service, rotation breaks everything at once |
| Long-lived cloud access keys in CI variables | a compromised pipeline or a malicious dependency exfiltrates keys valid for years |

For build-time secrets (a private package registry token), use BuildKit secret mounts,
which never land in a layer:

```dockerfile
# syntax=docker/dockerfile:1
FROM python:3.13-slim
RUN --mount=type=secret,id=pip_token \
    PIP_INDEX_URL="https://__token__:$(cat /run/secrets/pip_token)@pypi.example.com/simple" \
    pip install --no-cache-dir -r requirements.txt
```

`docker build --secret id=pip_token,env=PIP_TOKEN .` supplies it at build time only.

## 2. Getting secrets into the application at runtime

The application should read a secret from a well-known place (an environment variable
or a file path) and not care how it got there. That keeps code identical across laptops,
CI and production, which is the twelve-factor "config in the environment" idea.

**Environment variables versus mounted files.** Environment variables are simple and
universal, and the owner's original advice ("inject as environment variables") is a
fine starting point. Know their weaknesses: they are inherited by every child process,
readable in `/proc/<pid>/environ` by the same user or root, often printed by debug
endpoints, crash reporters and "dump the config" log lines, and they cannot change
without restarting the process. **Files** (a tmpfs volume with mode 0400) avoid most of
that and can be rotated in place: the app re-reads the file or watches it. Many teams use
env vars for low-risk values and files for keys and certificates.

```python
import os
from pathlib import Path


def read_secret(name: str) -> str:
    """Prefer a mounted file (NAME_FILE=/run/secrets/...), fall back to an env var."""
    path = os.environ.get(f"{name}_FILE")
    if path:
        return Path(path).read_text().strip()
    value = os.environ.get(name)
    if value is None:
        raise RuntimeError(f"missing secret {name}")
    return value
```

The `_FILE` convention is used by many official Docker images (Postgres, MySQL).

On a plain VM, systemd's `LoadCredential=` (see [CLI and Linux System Mastery](07_cli_and_linux_mastery.md)) exposes
a credential file only to that service at `$CREDENTIALS_DIRECTORY`, instead of putting
it in the unit file.

## 3. Cloud secret managers and the External Secrets Operator

**AWS Secrets Manager**, **GCP Secret Manager** and **Azure Key Vault** store secrets
encrypted with KMS keys, control access through IAM, log every read (CloudTrail, Cloud
Audit Logs), version secrets and can rotate some of them automatically (Secrets Manager
runs a rotation Lambda for RDS, for example). AWS **SSM Parameter Store** is a cheaper
option for configuration plus `SecureString` values without built-in rotation.

In Kubernetes, the **External Secrets Operator** (ESO) syncs from any of these (and from
Vault) into native Kubernetes Secrets:

```arch
%% caption: The operator authenticates with workload identity, reads the cloud secret and writes a Kubernetes Secret that the pod consumes as a file or env var. The app never talks to the secret store.
grid 170x105
node sm "AWS Secrets Manager" at 1,1 icon=aws-secrets-manager sub="prod/orders/db"
node iam "IAM role" at 1,2 icon=identity sub="via EKS Pod Identity"
group k8s "Kubernetes cluster" color=slate icon=k8s style=dashed
node op "External Secrets Operator" at 0,1 in k8s icon=worker sub="refreshInterval: 1h"
node sec "Kubernetes Secret" at 0,2 in k8s icon=secrets sub="base64, in etcd"
node pod "App pod" at 0,3 in k8s icon=app sub="volume or env"
iam:T -> sm:B : "grants read"
op -> sm : "GetSecretValue"
op -> sec : "creates / updates"
sec -> pod : "mounted"
```

```yaml
apiVersion: external-secrets.io/v1
kind: ExternalSecret
metadata:
  name: orders-db
  namespace: orders
spec:
  refreshInterval: 1h
  secretStoreRef:
    name: aws-secrets-manager
    kind: ClusterSecretStore
  target:
    name: orders-db          # the Kubernetes Secret to create
  data:
    - secretKey: password
      remoteRef:
        key: prod/orders/db
        property: password
```

(ESO's API reached `v1` in 2025; older manifests use `v1beta1`.) Alternatives: the
**Secrets Store CSI Driver** mounts secrets from the external store directly into the
pod as files without necessarily creating a Kubernetes Secret, and **Vault Secrets
Operator** / **Vault Agent Injector** do the same for Vault.

## 4. Kubernetes Secrets: what they are and are not

A Kubernetes `Secret` is an API object whose values are **base64-encoded, not
encrypted**. Base64 is an encoding for binary safety; anyone who can read the object can
decode it. What protects Secrets:

- **RBAC.** `get`/`list`/`watch` on Secrets in a namespace is effectively access to all
  of them; `list` returns their contents. Grant it sparingly, and remember that anyone
  who can create a Pod in the namespace can mount any Secret in it.
- **Encryption at rest in etcd**, which is *off by default* in self-managed clusters:
  configure an `EncryptionConfiguration`, preferably with the KMS v2 provider so the
  key lives in a cloud KMS. Managed services (EKS, GKE, AKS) encrypt etcd storage and
  offer envelope encryption of Secrets with your own KMS key.
- **Keeping them out of Git.** A Secret manifest in a GitOps repository is a plaintext
  password. Commit an `ExternalSecret` reference instead, or encrypt the manifest with
  **Sealed Secrets** (encrypted with a public key; only the in-cluster controller can
  decrypt) or **SOPS** (encrypts the values in YAML/JSON with KMS, age or PGP keys, and
  Argo CD / Flux can decrypt at deploy time).

## 5. HashiCorp Vault

Vault is the most widely used dedicated secrets platform for multi-cloud and
on-premises environments. Since 2023 it is under the Business Source License, and
**OpenBao** is the open-source (MPL) fork maintained under the Linux Foundation;
concepts and APIs below apply to both.

### Architecture in one paragraph

Clients **authenticate** through an **auth method** (Kubernetes, AWS IAM, GCP, Azure,
JWT/OIDC, AppRole, TLS certificates, LDAP, userpass for humans) and receive a **Vault
token** carrying **policies**. Policies grant capabilities (`read`, `create`, `update`,
`delete`, `list`) on paths. Paths are served by **secrets engines**: KV (static
key/value, versioned in v2), database, AWS/GCP/Azure (dynamic cloud credentials), PKI
(issue certificates), Transit (encryption as a service), SSH, and more. Everything
Vault stores is encrypted by a barrier key; at startup Vault is **sealed** and must be
**unsealed** (by key shares, or automatically through a cloud KMS or HSM, which is what
production uses). Every request can be written to an **audit device**. Production runs
a cluster of 3–5 nodes with **integrated storage** (Raft consensus); one is the active
leader.

```hcl
# Policy: the orders service may read its KV secrets and get DB credentials
path "secret/data/orders/*" {
  capabilities = ["read"]
}
path "database/creds/orders-readwrite" {
  capabilities = ["read"]
}
```

### Solving "secret zero"

If an app needs a password to log in to Vault, where does *that* password live? This
bootstrap problem is called **secret zero**. The answer is **platform identity**: the
app proves who it is using something the platform already gives it and that it did not
have to store.

- In Kubernetes, the pod presents its projected, short-lived service account token (a
  JWT). Vault's Kubernetes auth method validates it with the Kubernetes API
  (`TokenReview`) and maps the service account and namespace to a Vault role.
- On AWS, the app signs a request with its instance or pod IAM role; Vault verifies it
  with AWS STS.
- In CI, the job presents an OIDC token issued by the CI provider.

### Dynamic secrets and leases

Instead of storing one long-lived MySQL or Postgres password, Vault holds an admin
connection to the database. When the app asks for credentials, Vault **creates a brand
new database user** with exactly the grants the role defines, returns the username and
password with a **lease** (for example TTL 1 h, renewable up to a max TTL of 24 h), and
**drops the user when the lease expires or is revoked**.

```bash
vault secrets enable database
vault write database/config/orders-pg \
    plugin_name=postgresql-database-plugin \
    connection_url="postgresql://{{username}}:{{password}}@pg.internal:5432/orders" \
    username="vault_admin" password="$VAULT_PG_ADMIN_PASSWORD" \
    allowed_roles="orders-readwrite"
vault write -force database/rotate-root/orders-pg      # now only Vault knows the admin password

vault write database/roles/orders-readwrite \
    db_name=orders-pg default_ttl=1h max_ttl=24h \
    creation_statements="CREATE ROLE \"{{name}}\" WITH LOGIN PASSWORD '{{password}}' VALID UNTIL '{{expiration}}'; GRANT SELECT, INSERT, UPDATE ON ALL TABLES IN SCHEMA public TO \"{{name}}\";"

vault read database/creds/orders-readwrite              # a fresh user every call
# lease_id  database/creds/orders-readwrite/Ht3... lease_duration 1h  username v-k8s-orders-...
vault lease renew database/creds/orders-readwrite/Ht3...
vault lease revoke -prefix database/creds/orders-readwrite   # kill every credential of this role now
```

Why this is powerful:

- **Every pod gets its own credentials**, so the database's own logs and
  `pg_stat_activity` show which instance did what.
- **Leaked credentials expire on their own**, in an hour rather than never.
- **Revocation is one command**, per lease or per role, during an incident.
- **Nobody knows the admin password** after `rotate-root`.

Costs: Vault is now on the critical path at startup (cache and renew rather than
fetching per request, and run it highly available); every renewal cycle creates and
drops database roles, which some databases handle badly at high churn; and apps must
handle credentials changing (reconnect with the new pair when the lease is replaced,
which connection pools must support). **Vault Agent** or the **Vault Secrets Operator**
usually does the login, renewal and file rendering so the app just reads a file.

The live flow below follows one pod through login, credential creation, renewal and an
incident revocation.

<div class="lab" data-viz="flow-vault-lease"></div>

### Encryption as a service: the Transit engine

If your app must encrypt personal data (national ID numbers, card data) before storing
it, the app should not hold the encryption key. With the **Transit** engine, the app
sends plaintext to Vault and gets ciphertext back; the key never leaves Vault.

```bash
vault secrets enable transit
vault write -f transit/keys/pii
# The API takes base64-encoded plaintext:
vault write transit/encrypt/pii plaintext=$(printf '123-45-6789' | base64)
# ciphertext  vault:v1:8SDd3WHDOjf7mq69CyCqYjBXAiQQAVZRkFM13ok481zoCmHnSeDX9vyf7w==
vault write transit/decrypt/pii ciphertext="vault:v1:8SDd3..."   # returns base64 plaintext
vault write -f transit/keys/pii/rotate                            # new key version v2
vault write transit/rewrap/pii ciphertext="vault:v1:8SDd3..."    # re-encrypt under v2 without exposing plaintext
```

The owner's example (`POST /vault/encrypt {"plaintext": "123-45-678"}`) had the idea
right; the real HTTP API is `POST /v1/transit/encrypt/<key-name>` with a **base64**
`plaintext` field. The `vault:v1:` prefix records the key version, which is what makes
rotation painless: old ciphertexts still decrypt, new ones use the new version, and
`rewrap` upgrades stored data in the background. Cloud KMS services offer the same idea
(and **envelope encryption**: KMS encrypts a small data key, the data key encrypts the
large payload locally).

## 6. Workload identity: the best secret is no secret

Many credentials can be removed entirely by federating identity between platforms,
which leaves nothing long-lived to steal.

| From | To | Mechanism |
|---|---|---|
| Kubernetes pod | AWS | IRSA (IAM roles for service accounts, OIDC) or **EKS Pod Identity** |
| Kubernetes pod | GCP | GKE Workload Identity Federation |
| Kubernetes pod | Azure | Microsoft Entra Workload ID |
| GitHub Actions / GitLab CI | any cloud | OIDC token → `AssumeRoleWithWebIdentity` / workload identity federation |
| Service | service | mTLS certificates from a mesh or SPIFFE/SPIRE ([Service Mesh (Istio / Linkerd)](12_service_mesh.md)) |
| Human | servers, databases | SSO + short-lived certificates (Teleport, Vault SSH/PKI, cloud IAM database auth) |

```mermaid
sequenceDiagram
    participant Job as CI job (acme/api, main)
    participant IdP as CI OIDC issuer
    participant STS as Cloud STS
    participant API as Cloud APIs
    Job->>IdP: request ID token (audience = cloud)
    IdP-->>Job: signed JWT (iss, aud, sub = repo:acme/api:ref:refs/heads/main)
    Job->>STS: AssumeRoleWithWebIdentity(deploy role, JWT)
    STS->>STS: verify signature via issuer keys, check the role's trust policy on sub/aud
    STS-->>Job: temporary credentials (≈15-60 min)
    Job->>API: deploy with temporary credentials
```

OIDC federation from CI: the job gets a signed identity token, the cloud checks it
against the trusted issuer and returns credentials that expire in minutes, so no key is
stored anywhere.

The trust policy should pin the token's `sub` claim to a specific repository and branch
or environment (`repo:acme/api:ref:refs/heads/main`); trusting the whole issuer would let
any repository on the CI platform assume the role.

## 7. Rotation, detection and incident response

**Rotation** limits how long a leaked secret is useful. Automate it; manual rotation
happens once, during an incident, badly. Zero-downtime rotation of a static secret uses
two valid versions at once:

1. Create the new credential while the old one still works (two database users, or an
   API provider that allows two active keys).
2. Update the secret store; consumers pick it up (file reload, restart, or next lease).
3. Verify nothing still uses the old credential (access logs, database `pg_stat_activity`).
4. Revoke the old one.

Dynamic secrets and workload identity make rotation continuous and automatic, which is
the strongest argument for them.

**Detection.** Turn on GitHub secret scanning with **push protection** (blocks a push
containing a recognized credential format), run `gitleaks` or `TruffleHog` as a
pre-commit hook and in CI, scan container images and logs, and alert on use of
credentials from unexpected places (cloud anomaly detection, canary tokens that raise an
alarm when used).

**When a secret leaks**, in order:

1. **Revoke or rotate it immediately.** Deleting the commit is not enough: forks,
   clones, CI caches and scrapers that watch public GitHub pushes (they find new keys
   within minutes) may already have it. Rewriting history comes after, if at all.
2. **Investigate use**: audit logs (CloudTrail, Vault audit log, the provider's
   dashboard) for access with that credential since the leak.
3. **Fix the path** it leaked through (a log statement, a `.env` committed, a
   misconfigured bucket) and add a control that would have caught it.

## Common interview questions

**How should an application get its database password?**
From a secret store at runtime, via workload identity, delivered as a file or env var
by an operator or agent, never from code, images or Git. Better still, short-lived
dynamic credentials or IAM database authentication.

**Are Kubernetes Secrets secure?**
They are base64-encoded, not encrypted. Protect them with tight RBAC, encryption at rest
through KMS, and keep plaintext manifests out of Git (ExternalSecret references, Sealed
Secrets or SOPS).

**What is secret zero, and how do you solve it?**
The credential needed to fetch all other credentials. Solve it with platform identity:
Kubernetes service account tokens, cloud IAM roles or CI OIDC tokens, which the
platform issues and rotates, so the app stores nothing.

**What are Vault dynamic secrets?**
Credentials Vault creates on demand per client with a lease and TTL, and deletes on
expiry or revocation. Each workload has unique, short-lived, auditable credentials, and
revocation is instant.

**Environment variables or files for secrets?**
Env vars are simple but leak through child processes, `/proc`, debug dumps and logs,
and need a restart to change. Files on tmpfs with tight permissions can be rotated in
place. Both beat hardcoding; files are preferable for high-value secrets.

**A developer pushed an AWS key to a public repo. What do you do?**
Deactivate and rotate the key first, then check CloudTrail for its use, then clean up
history and fix the process (push protection, pre-commit scanning, OIDC instead of
static keys).

**How does CI deploy to the cloud without stored keys?**
OIDC federation: the CI provider issues a signed JWT for the job, the cloud trusts that
issuer and exchanges the token for short-lived role credentials, constrained by claims
such as repository and branch.

**What is envelope encryption?**
A KMS master key encrypts a per-object data key; the data key encrypts the data locally.
Only small data keys go to KMS, rotation re-wraps data keys, and the master key never
leaves the HSM.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | — | Never commit secrets; what counts as a secret; use `.gitignore` and environment variables; what to do if you leak one (tell someone, rotate). |
| Junior (L3) | Software Engineer I | L3 | Read secrets from env or files, use the team's secret store, avoid secrets in Dockerfiles and logs, and know that Kubernetes Secrets are only base64. |
| Mid (L4) | Software Engineer II | L4 | Wire up External Secrets or Vault Agent, use BuildKit secret mounts, set up OIDC from CI to the cloud, and run a zero-downtime rotation. |
| Senior (L5) | Senior Software Engineer | L5 | Design secret delivery for a platform: workload identity, dynamic secrets and leases, Transit/envelope encryption, least-privilege policies, audit, secret scanning, and incident response. |
| Staff+ (L6+) | Staff / Principal Engineer | L6+ | Set the organization's strategy: eliminating long-lived credentials, choosing Vault/OpenBao vs cloud-native managers, KMS and HSM key hierarchy, compliance needs, and the availability risk of putting a secret store on every startup path. |

## Interview checklist

- [ ] I can list where secrets leak (Git history, image layers, env dumps, logs, CI) and how to avoid each.
- [ ] I can use BuildKit `--mount=type=secret` for build-time secrets.
- [ ] I can compare env vars and mounted files for delivering secrets.
- [ ] I can explain External Secrets Operator and the CSI Secrets Store driver.
- [ ] I can explain why Kubernetes Secrets are not encrypted by default and how to fix it (RBAC, KMS, Sealed Secrets, SOPS).
- [ ] I can describe Vault auth methods, policies, secrets engines, sealing and HA.
- [ ] I can explain secret zero and solve it with platform identity.
- [ ] I can walk through a Vault dynamic database credential lease: issue, renew, expire, revoke.
- [ ] I can explain Transit encryption, key versioning, rewrap and envelope encryption.
- [ ] I can set up OIDC federation from CI to a cloud with a tightly scoped trust policy.
- [ ] I can run a leaked-secret response in the right order.

Related: [Security](../SystemDesign/building_blocks/14_security.md), [OpenID Connect and Single Sign-On](../API/Fundamentals/05_openid_connect_and_sso.md)
(OIDC tokens and claims), [Infrastructure as Code (IaC)](08_infrastructure_as_code.md) (secrets in Terraform state),
[Service Mesh (Istio / Linkerd)](12_service_mesh.md) (mTLS identities), [Continuous Integration (CI) Fundamentals](../CICD/01_ci_fundamentals.md) (pipeline credentials).
