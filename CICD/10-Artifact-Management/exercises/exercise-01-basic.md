# Exercise 1: Docker Image Tagging and Pushing 🟢

## 🎯 Objective
Learn how to build a Docker image from a Go application, tag it with a Git SHA, and push it to a local Docker registry to simulate artifact management.

## 📋 Prerequisites
* Docker installed and running
* Go 1.21+ installed
* A basic understanding of Dockerfiles

## 📝 Instructions

### Step 1: Create a Simple Go Web Server
First, create a simple Go application that we will package.
Create a file named `main.go`:

```go
package main

import (
	"fmt"
	"net/http"
	"os"
)

func main() {
	http.HandleFunc("/", func(w http.ResponseWriter, r *http.Request) {
		version := os.Getenv("APP_VERSION")
		if version == "" {
			version = "unknown"
		}
		fmt.Fprintf(w, "Hello, CI/CD! Running version: %s\n", version)
	})

	fmt.Println("Server starting on port 8080...")
	http.ListenAndServe(":8080", nil)
}
```

### Step 2: Create the Dockerfile
Create a `Dockerfile` that uses multi-stage builds to keep the artifact small.

```dockerfile
# Build Stage
FROM golang:1.21-alpine AS builder
WORKDIR /app
COPY main.go .
RUN go build -o myapp main.go

# Final Stage (The Artifact)
FROM alpine:latest
WORKDIR /app
COPY --from=builder /app/myapp .
EXPOSE 8080
CMD ["./myapp"]
```

### Step 3: Run a Local Docker Registry
We need a place to store our artifact. Let's spin up a local Docker registry.
```bash
docker run -d -p 5000:5000 --name local-registry registry:2
```

### Step 4: Build and Tag the Image
Instead of using `latest`, we will tag the image with a fake Git SHA (e.g., `a1b2c3d`).

```bash
docker build -t localhost:5000/myapp:a1b2c3d .
```

### Step 5: Push the Artifact to the Registry
Push the tagged image to your local registry.
```bash
docker push localhost:5000/myapp:a1b2c3d
```

### Step 6: Verify the Artifact
Pull the image back down to prove it's stored in the registry, then run it.

```bash
docker pull localhost:5000/myapp:a1b2c3d
docker run -d -p 8080:8080 -e APP_VERSION=a1b2c3d localhost:5000/myapp:a1b2c3d
curl http://localhost:8080
```

## 💡 Hints
* `localhost:5000` tells Docker to push to your local registry container instead of Docker Hub.
* Multi-stage builds are crucial for compiled languages like Go so you don't ship the compiler in your final artifact.

## ✅ Expected Output
```text
$ curl http://localhost:8080
Hello, CI/CD! Running version: a1b2c3d
```

## 🧠 Key Takeaway
You built a compiled binary, wrapped it in a minimal Docker image, tagged it with an immutable identifier (a SHA instead of `:latest`), and pushed it to an artifact repository. This is the foundation of modern artifact management!
