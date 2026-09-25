# Chapter 06: Continuous Delivery and Deployment

## 🎯 Learning Objectives

By the end of this chapter, you will be able to:
- Distinguish between Continuous Delivery and Continuous Deployment.
- Design release pipelines that promote code across environments.
- Implement Semantic Versioning (SemVer) and manage release notes.
- Automate configuration and secrets management safely.
- Integrate automated database migrations into your deployment pipeline.
- Apply zero-downtime deployment strategies and rollback mechanisms.
- Configure GitHub Actions environments with approval gates.

## 📖 Introduction

Imagine you run a massive shipping network. Building a package (CI) is useless unless that package reaches the customer's doorstep in perfect condition (CD). **Continuous Delivery** is packing the delivery truck and driving it to the depot, waiting for the final nod to dispatch. **Continuous Deployment** is the automated drone that picks up the package and immediately flies it to the customer without any human intervention.

In this chapter, we bridge the gap between "code works on my machine/CI server" and "code is running safely in production." 

## 🔑 Key Terminology

| Term | Definition |
|------|------------|
| **Continuous Delivery (CD)** | The practice of automatically building, testing, and preparing code for a release to production, requiring a manual trigger for the final deployment. |
| **Continuous Deployment (CD)** | The practice of releasing every good build directly to production automatically, with no manual intervention. |
| **Environment Promotion** | Moving a built artifact sequentially through isolated environments (e.g., Dev -> Staging -> Prod) to validate it. |
| **Approval Gates** | Pauses in a pipeline that require human verification before proceeding. |
| **Zero-Downtime Deployment** | Deploying a new version without interrupting service for existing users. |
| **Database Migration** | A version-controlled script that mutates a database schema safely. |

## 🚀 Continuous Delivery vs Continuous Deployment

### Continuous Delivery Workflow

```arch
node Dev "Developer Commit" at 0,0
node CI "CI Pipeline\n(Build & Test)" at 0,2
node Staging "Deploy to Staging" at 0,4
node Gate "Approval Gate" at 0,6
node Prod "Deploy to Production" at 0,8

Dev -> CI
CI -> Staging
Staging -> Gate
Gate -> Prod : "Manual Approval"
```

### Continuous Deployment Workflow

```arch
node Dev "Developer Commit" at 0,0
node CI "CI Pipeline\n(Build & Test)" at 0,2
node Staging "Deploy to Staging\n& Run E2E" at 0,4
node Prod "Auto-Deploy to\nProduction" at 0,6

Dev -> CI
CI -> Staging
Staging -> Prod
```

## 🏗 Release Pipelines and Environment Promotion

A strong deployment pipeline ensures you build an artifact **once** and deploy that exact same artifact everywhere.

### Environment Promotion Path
- **Development (Dev):** Where developers test merged code.
- **Staging / UAT:** A production-like environment for final automated/manual testing.
- **Production (Prod):** The live system serving real users.

## 🔢 Semantic Versioning (SemVer) & Release Management

Versioning provides a contract for compatibility. SemVer follows the `MAJOR.MINOR.PATCH` format.
- **MAJOR:** Breaking changes (e.g., v2.0.0)
- **MINOR:** New features, backward compatible (e.g., v1.1.0)
- **PATCH:** Bug fixes (e.g., v1.0.1)

### Go Example: Reading Version dynamically during build
```go
package main

import (
	"fmt"
	"net/http"
)

// Injected at build time using -ldflags="-X main.Version=1.0.0"
var Version = "development"

func handler(w http.ResponseWriter, r *http.Request) {
	fmt.Fprintf(w, "Hello from version: %s\n", Version)
}

func main() {
	http.HandleFunc("/", handler)
	fmt.Printf("Starting server v%s on :8080\n", Version)
	http.ListenAndServe(":8080", nil)
}
```

## 🔒 Configuration and Secrets Management

Applications should follow the **Twelve-Factor App** methodology: store configuration in the environment.

### Python Example: Loading Config securely
```python
import os
import sys

def load_config():
    db_host = os.getenv("DB_HOST")
    db_pass = os.getenv("DB_PASSWORD")
    
    if not db_host or not db_pass:
        print("CRITICAL: Missing environment variables.", file=sys.stderr)
        sys.exit(1)
        
    return {
        "host": db_host,
        "password": db_pass
    }

if __name__ == "__main__":
    config = load_config()
    print(f"Connecting to {config['host']} (password length: {len(config['password'])})")
```

## 🗄 Database Migrations in CD

Migrating a database must be automated. Use schema versioning tools (like Alembic in Python or golang-migrate).

```arch
node Pipeline "Pipeline" at 0,0
node AppServer "App Server" at 0,3
node Database "Database" at 0,6

Pipeline -> Database : "1. Run Migration\nScripts (V1 -> V2)"
Pipeline -> AppServer : "2. Deploy New\nCode (V2)"
AppServer -> Database : "3. Queries using\nV2 schema"
```

*Always design database changes to be backward compatible (e.g., add a column, don't drop it yet).*

## 🔄 Deployment Automation & Rollbacks

When deploying, you need an automated shell script to pull code, restart services, and roll back if things fail.

```bash
#!/bin/bash
# deploy.sh
set -e

VERSION=$1
if [ -z "$VERSION" ]; then
    echo "Usage: $0 <version>"
    exit 1
fi

echo "Deploying version $VERSION..."
# Backup current version for rollback
cp -r /app/current /app/backup

if ! ./update_service.sh "$VERSION"; then
    echo "Deployment failed. Rolling back..."
    rm -rf /app/current
    mv /app/backup /app/current
    systemctl restart myapp
    exit 1
fi

echo "Deployment successful."
```

## 🕵️ Smoke Tests

Smoke tests are fast, crucial checks run immediately after deployment to verify the system isn't on fire.

```python
# smoke_test.py
import requests
import sys

def run_smoke_test(url):
    try:
        response = requests.get(f"{url}/health")
        if response.status_code == 200:
            print("Smoke test passed.")
            sys.exit(0)
        else:
            print(f"Smoke test failed. Status: {response.status_code}")
            sys.exit(1)
    except Exception as e:
        print(f"Smoke test exception: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_smoke_test("http://localhost:8080")
```

## 🐙 GitHub Actions: Environments and Approvals

GitHub Actions lets you define environments (like `production`) that require manual approval.

```yaml
name: Release Pipeline
on:
  push:
    tags:
      - 'v*.*.*'

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - run: make build

  deploy_staging:
    needs: build
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - run: ./deploy.sh staging

  deploy_production:
    needs: deploy_staging
    runs-on: ubuntu-latest
    environment: production # Set up Approval Rules in GitHub UI for this env
    steps:
      - run: ./deploy.sh production
```

## 💡 Best Practices

- **Do** build your artifact exactly once in CI and deploy that same binary to Staging and Prod.
- **Do** automate database migrations and make them backward compatible.
- **Don't** use `latest` tags. Always deploy explicit, immutable versions (e.g., git SHA or SemVer).
- **Don't** hardcode configurations in deployment scripts. Use injected environment variables.

## 🔗 How This Connects

This chapter builds entirely on the sturdy foundation of automated testing (Chapter 5). Next, we will learn how to package these applications into immutable, portable units in **Chapter 7: Containerization with Docker**.

## 📝 Chapter Summary

| Concept | Summary |
|---------|---------|
| **CD vs CD** | Delivery requires manual approval; Deployment is fully automatic to Prod. |
| **Artifacts** | Build once, deploy everywhere. |
| **Environments** | Progressively strict stages (Dev -> Staging -> Prod) to catch issues. |
| **Zero-Downtime** | Keep the old version running while routing traffic to the new one. |
| **Smoke Tests** | Instant sanity checks after a deployment completes. |

## ➡️ What's Next
Head over to the `exercises/` folder to start practicing deployment scripts, database migrations, and pipeline environments!
