# Exercise 5: Complete DevSecOps Pipeline 🔴

## 🎯 Objective
Create a complete GitHub Actions pipeline that builds a Go application, runs SAST, scans for secrets, builds a Docker image, scans the image, and generates an SBOM.

## 📋 Prerequisites
- A GitHub account.
- Basic knowledge of GitHub Actions.

## 📝 Instructions

1. **Set up the Repository**
   Create a new GitHub repository and clone it locally.
   
2. **Create the Go Application**
   ```go
   // main.go
   package main
   import "fmt"
   func main() {
       fmt.Println("Secure Enterprise App")
   }
   ```
   ```bash
   go mod init enterprise-app
   ```

3. **Create the Dockerfile**
   ```dockerfile
   FROM golang:1.22-alpine AS builder
   WORKDIR /app
   COPY . .
   RUN go build -o main .
   
   FROM alpine:3.19
   WORKDIR /app
   COPY --from=builder /app/main .
   CMD ["./main"]
   ```

4. **Create the CI/CD Pipeline Workflow**
   Create `.github/workflows/devsecops.yml`:

   ```yaml
   name: Enterprise DevSecOps Pipeline
   
   on:
     push:
       branches: [ "main" ]
     pull_request:
       branches: [ "main" ]
   
   jobs:
     security-checks:
       name: Code Security (SAST & Secrets)
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
             
         - name: Run Gitleaks
           uses: gitleaks/gitleaks-action@v2
           env:
             GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
             
         - name: Run Gosec Security Scanner
           uses: securego/gosec@master
           with:
             args: ./...
             
     build-and-image-security:
       name: Build, Image Scan, & SBOM
       needs: security-checks
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Build Docker Image
           run: docker build -t my-app:${{ github.sha }} .
           
         - name: Run Trivy vulnerability scanner
           uses: aquasecurity/trivy-action@master
           with:
             image-ref: 'my-app:${{ github.sha }}'
             format: 'table'
             exit-code: '1'
             ignore-unfixed: true
             vuln-type: 'os,library'
             severity: 'CRITICAL,HIGH'
             
         - name: Generate SBOM
           uses: anchore/sbom-action@v0
           with:
             image: my-app:${{ github.sha }}
             format: spdx-json
             artifact-name: sbom.spdx.json
   ```

5. **Push and Observe**
   Commit these files and push them to your GitHub repository.
   Navigate to the "Actions" tab in your repository and watch the pipeline execute.

6. **Test the Security Gates**
   Create a new branch. Add a hardcoded password to `main.go`. Commit and push. Open a Pull Request.
   Observe how Gitleaks and Gosec *fail the pipeline*, acting as a security gate and preventing the merge.

## 💡 Hints
- The pipeline uses `needs: security-checks` to ensure we don't bother building the Docker image if the source code contains critical flaws or leaked secrets.
- `artifact-name` in the SBOM step automatically uploads the generated SBOM as a downloadable GitHub Action Artifact.

## ✅ Expected Output
A fully green GitHub Actions workflow where:
1. Gitleaks verifies no secrets are checked in.
2. Gosec verifies the Go code has no vulnerabilities.
3. Trivy verifies the Alpine base image has no CRITICAL or HIGH vulnerabilities.
4. An `sbom.spdx.json` artifact is available for download at the end of the run.

## 🧠 Key Takeaway
A complete DevSecOps pipeline automates security from code commit through to the built artifact, providing continuous assurance without slowing down developer velocity.
