# Chapter 11: Pipeline Security (DevSecOps)

## 🎯 Learning Objectives
By the end of this chapter, you will be able to:
1. Understand the concept of "Shift Left" security and DevSecOps.
2. Implement SAST, DAST, and SCA scanning in CI/CD pipelines.
3. Securely manage secrets and prevent credential leaks.
4. Scan container images for vulnerabilities.
5. Generate and utilize Software Bill of Materials (SBOMs).
6. Apply supply chain security principles and the SLSA framework.
7. Enforce security gates and least privilege for CI/CD runners.

## 📖 Introduction
Imagine you're building a massive bank vault. In traditional software development, security was like hiring a guard to stand at the completed vault door and test the lock. If they found a flaw, you'd have to tear down the vault and start over. 

DevSecOps changes this model entirely. It's like having a security expert inspect the steel before it's poured, check the blueprints as they're drawn, and test the hinges as they're installed. This is known as **"Shift Left" security**—moving security checks as early in the software development lifecycle (SDLC) as possible (to the "left" of the timeline). 

By integrating security into the CI/CD pipeline, vulnerabilities are caught when they are cheapest and easiest to fix: right after the developer writes the code.

## 🔑 Key Terminology

| Term | Definition |
|------|------------|
| **DevSecOps** | Development, Security, and Operations. Integrating security practices within the DevOps process. |
| **Shift Left** | Moving security checks earlier in the development process. |
| **SAST** | Static Application Security Testing. Analyzing source code for vulnerabilities without running it. |
| **DAST** | Dynamic Application Security Testing. Analyzing a running application for vulnerabilities. |
| **SCA** | Software Composition Analysis. Scanning third-party dependencies for known vulnerabilities. |
| **SBOM** | Software Bill of Materials. A comprehensive inventory of all software components and dependencies. |
| **SLSA** | Supply-chain Levels for Software Artifacts. A security framework for preventing tampering. |

## 🛡️ Security in Every Pipeline Stage

A robust DevSecOps pipeline integrates security at every phase:

```arch
node c "1. Code Phase" at 0,0 shape=card color=blue
node b "2. Build Phase" at 1,0 shape=card color=purple
node t "3. Test Phase" at 2,0 shape=card color=teal
node d "4. Deploy Phase" at 3,0 shape=card color=red
c -> b -> t -> d
node sec1 "Secrets Scanning (gitleaks)" at 0,1 shape=text
node sec2 "SAST (gosec, bandit)" at 0,2 shape=text
c -> sec1
c -> sec2
node sec3 "SCA (dependabot)" at 1,1 shape=text
node sec4 "Image Scanning (trivy)" at 1,2 shape=text
b -> sec3
b -> sec4
```

## 🔍 Static Application Security Testing (SAST)

SAST analyzes source code for vulnerabilities (like SQL injection, hardcoded secrets, or buffer overflows) without executing the program. It's a "white-box" testing method.

### SAST Tools:
- **Go**: `gosec`
- **Python**: `bandit`
- **Multi-language**: `semgrep`, `SonarQube`

**Example: Go Code with Vulnerability (main.go)**
```go
package main

import (
	"database/sql"
	"fmt"
	"log"
	"net/http"

	_ "github.com/mattn/go-sqlite3"
)

func handleUser(db *sql.DB) http.HandlerFunc {
	return func(w http.ResponseWriter, r *http.Request) {
		username := r.URL.Query().Get("username")
		// VULNERABILITY: SQL Injection
		query := fmt.Sprintf("SELECT * FROM users WHERE username = '%s'", username)
		rows, err := db.Query(query)
		if err != nil {
			log.Println(err)
		}
		defer rows.Close()
	}
}
```

Running `gosec` on this code:
```bash
gosec ./...
```
*Output will flag the SQL injection vulnerability.*

**Example: Python Code with Vulnerability (app.py)**
```python
import subprocess

def run_command(user_input):
    # VULNERABILITY: Command Injection
    subprocess.call("ping -c 1 " + user_input, shell=True)
```

Running `bandit`:
```bash
bandit -r .
```

## 🏃 Dynamic Application Security Testing (DAST)

DAST involves interacting with a running application to find vulnerabilities (e.g., Cross-Site Scripting, misconfigurations). It's a "black-box" testing method. Examples include OWASP ZAP and Burp Suite. In CI/CD, you typically deploy a temporary testing environment, run DAST tools against it, and then tear it down.

## 📦 Software Composition Analysis (SCA)

SCA focuses on third-party dependencies. Modern applications are often 80% open-source libraries. If a library has a vulnerability (e.g., Log4Shell), your app is vulnerable.

SCA tools analyze `go.mod`, `requirements.txt`, or `package.json` against vulnerability databases (CVEs).

## 🤫 Secrets Management and Scanning

**NEVER COMMIT SECRETS** (API keys, passwords, tokens) to source control. Even if the repository is private, leaked secrets are the number one cause of massive data breaches.

**Secrets Management:**
Use tools like HashiCorp Vault, AWS Secrets Manager, or GitHub Actions Secrets to inject credentials at runtime or build time.

**Secrets Scanning:**
Tools like `gitleaks` and `trufflehog` scan repositories for accidentally committed secrets.

```bash
gitleaks detect -v
```

## 🐳 Container Image Scanning

Containers package the OS along with your app. If the base OS (e.g., Debian, Alpine) has a vulnerability, your container is at risk. Tools like `trivy` and `grype` scan container images for known OS and language-level vulnerabilities.

```bash
trivy image my-app:latest
```

## 📋 Software Bill of Materials (SBOM)

An SBOM is a detailed list of all components, libraries, and modules required to build a software product. It's the "ingredients list" for your software.

Generate an SBOM using `syft`:
```bash
syft my-app:latest -o spdx-json > sbom.json
```

## 🛡️ Supply Chain Security

Supply chain security ensures that the code you wrote is exactly what gets deployed, without tampering.

- **Signed Commits:** Use GPG or SSH to sign commits.
- **Signed Images:** Use tools like `cosign` to sign container images.
- **SLSA (Supply-chain Levels for Software Artifacts):** A framework providing guidelines for securing the software supply chain (e.g., generating provenance).

## 🔒 Dependency Pinning and Lock Files

Always use lock files (`go.sum`, `Pipfile.lock`, `package-lock.json`) to ensure reproducible builds and prevent malicious dependency updates from being automatically pulled in.

## 🕸️ OWASP Top 10 in CI/CD

The OWASP Top 10 outlines the most critical web application security risks. CI/CD pipelines mitigate these by:
- **Injection:** Blocked by SAST (gosec, bandit).
- **Vulnerable and Outdated Components:** Blocked by SCA and container scanning (trivy).
- **Identification and Authentication Failures:** Prevented by secrets scanning (gitleaks).

## 👮 Least Privilege Principle for CI/CD Runners

CI/CD runners have powerful access. Ensure they operate with the **Principle of Least Privilege**:
- Runners should not run as `root`.
- Limit network access for runners (e.g., cannot access internal databases).
- Grant minimum necessary IAM permissions for deployments.

## 🛑 Security Gates in Pipelines

A "Security Gate" is a threshold that, if crossed, blocks the deployment. For example, failing the pipeline if *any* "CRITICAL" vulnerability is found, but allowing "LOW" severity ones with a warning.

## 🛠️ Practical: Complete Security-Focused CI Pipeline

Here is a complete GitHub Actions pipeline for a Python/Docker application.

```yaml
name: DevSecOps Pipeline

on: [push, pull_request]

jobs:
  security-scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Gitleaks (Secrets Scanning)
        uses: gitleaks/gitleaks-action@v2
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.10'
          
      - name: Install Bandit
        run: pip install bandit
        
      - name: SAST with Bandit
        run: bandit -r . -ll -ii # Only report medium/high
        
  build-and-scan:
    needs: security-scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Build Docker image
        run: docker build -t my-app:${{ github.sha }} .
        
      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: 'my-app:${{ github.sha }}'
          format: 'table'
          exit-code: '1' # Fail pipeline if vulnerabilities found
          ignore-unfixed: true
          vuln-type: 'os,library'
          severity: 'CRITICAL,HIGH'
          
      - name: Generate SBOM
        uses: anchore/sbom-action@v0
        with:
          image: my-app:${{ github.sha }}
          format: spdx-json
```

## 💡 Best Practices

- **DO** fail the build on critical vulnerabilities or leaked secrets.
- **DO** generate and archive an SBOM for every release.
- **DO** use ephemeral, least-privilege CI runners.
- **DON'T** commit secrets to version control. Ever.
- **DON'T** ignore security tool alerts. If they are false positives, configure the tool to ignore them explicitly.

## 🔗 How This Connects
- Connects from **Chapter 10 (Artifact Management)**: Secure artifacts are scanned, signed, and accompanied by an SBOM before being stored.
- Connects to **Chapter 12 (Advanced Deployment Strategies)**: Secure artifacts are deployed safely using progressive delivery methods.

## 📝 Chapter Summary

| Concept | Tool Example | Pipeline Stage | Purpose |
|---------|--------------|----------------|---------|
| SAST | gosec, bandit | Code/Linting | Scan code for flaws |
| Secrets Scanning | gitleaks | Pre-commit/Code | Find leaked credentials |
| SCA / Image Scanning | trivy | Build | Find vulnerable dependencies |
| SBOM | syft | Artifacts | Generate ingredient list |

## ➡️ What's Next
Next, in Chapter 12, we will cover Advanced Deployment Strategies like Blue/Green, Canary, and Feature Flags to deploy our secure applications safely.
