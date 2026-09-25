# Exercise 3: Container Image Scanning with Trivy 🟡

## 🎯 Objective
Build a Docker image and scan it for OS and language-level vulnerabilities using `trivy`.

## 📋 Prerequisites
- Docker installed
- `trivy` installed (`brew install trivy` or use the Trivy Docker image)

## 📝 Instructions

1. **Create a Go Application with an outdated dependency**
   Create `main.go`:
   ```go
   package main
   
   import "fmt"
   
   func main() {
       fmt.Println("Vulnerable App")
   }
   ```
   
   Initialize the module and add an intentionally old package:
   ```bash
   go mod init vuln-app
   go get golang.org/x/text@v0.3.0
   ```

2. **Create a Dockerfile**
   We will use an outdated base image intentionally.
   Create `Dockerfile`:
   ```dockerfile
   # Intentionally using an old vulnerable base image
   FROM alpine:3.10
   
   WORKDIR /app
   COPY . .
   
   CMD ["sh"]
   ```

3. **Build the Docker Image**
   ```bash
   docker build -t my-vuln-app:1.0 .
   ```

4. **Scan the image with Trivy**
   Run Trivy against the local image:
   ```bash
   trivy image my-vuln-app:1.0
   ```

5. **Fix the Vulnerabilities**
   Update the `Dockerfile` to use a modern, secure base image:
   ```dockerfile
   FROM alpine:3.19
   
   WORKDIR /app
   COPY . .
   
   CMD ["sh"]
   ```
   
   Update the Go dependency:
   ```bash
   go get golang.org/x/text@latest
   ```

6. **Rebuild and Rescan**
   ```bash
   docker build -t my-secure-app:1.0 .
   trivy image my-secure-app:1.0
   ```

## 💡 Hints
- `trivy` scans both OS packages (like `apk` packages in Alpine) and language-specific dependencies (like `go.mod`).
- In CI/CD, you can use `--exit-code 1 --severity CRITICAL,HIGH` to break the build only on major issues.

## ✅ Expected Output
Before fix:
```text
my-vuln-app:1.0 (alpine 3.10.3)
===============================
Total: 30 (UNKNOWN: 0, LOW: 2, MEDIUM: 10, HIGH: 15, CRITICAL: 3)
... (list of CVEs for musl, busybox, etc.)

Node.js / Python / Go / Java dependencies...
... (list of CVEs for golang.org/x/text)
```

After fix:
```text
my-secure-app:1.0 (alpine 3.19.1)
===============================
Total: 0 (UNKNOWN: 0, LOW: 0, MEDIUM: 0, HIGH: 0, CRITICAL: 0)
```

## 🧠 Key Takeaway
Container base images and application dependencies rot over time. Regular scanning during the CI process ensures you don't deploy known vulnerabilities to production.
