# Chapter 07: Containerization with Docker

## 🎯 Learning Objectives

By the end of this chapter, you will be able to:
- Understand the fundamental differences between containers and Virtual Machines (VMs).
- Write optimized `Dockerfile`s for Go and Python applications.
- Leverage multi-stage builds to dramatically reduce image sizes and improve security.
- Implement container security best practices, including non-root users and minimal base images.
- Utilize Docker Compose to spin up complex multi-container environments for local development and CI testing.
- Design robust tagging strategies for container images (semantic versioning, Git SHAs).
- Integrate Docker seamlessly into CI/CD pipelines (e.g., GitHub Actions), including layer caching and image pushing.

## 📖 Introduction

Imagine you're trying to move an entire house. Traditionally, you might try to drive the whole house on a giant flatbed truck (a Virtual Machine). It's slow, incredibly heavy, and takes up a massive amount of space on the road. What if, instead, you could instantly pack up exactly the furniture you need, along with the precise dimensions of the rooms, into standard-sized shipping containers? These containers can be easily loaded onto any standard ship, truck, or train anywhere in the world. 

That is **Containerization**. In software development, the "it works on my machine" problem is one of the most persistent headaches. Containerization solves this by packaging an application and all its dependencies—libraries, binaries, configuration files—into a single, standardized unit called a container. Docker is the de facto standard tool for creating and managing these containers.

For CI/CD, containers are revolutionary. They guarantee that the exact same environment used to build and test code in the CI pipeline is the one deployed to production.

## 🔑 Key Terminology

| Term | Definition |
| :--- | :--- |
| **Image** | A read-only template with instructions for creating a Docker container. Think of it as a snapshot or a blueprint. |
| **Container** | A runnable instance of an image. It runs completely isolated from the host environment by default. |
| **Layer** | A modification to an image, represented by an instruction in the Dockerfile. Images are built from a stack of these read-only layers. |
| **Dockerfile** | A text document containing all the commands a user could call on the command line to assemble an image. |
| **Registry** | A stateless, highly scalable server-side application that stores and lets you distribute Docker images (e.g., Docker Hub, GHCR). |
| **Docker Engine** | The core background service (daemon) that builds, runs, and manages Docker containers. |
| **Multi-stage Build** | A method of building an image where you use multiple `FROM` statements in your Dockerfile, allowing you to copy artifacts from one stage to another, discarding unnecessary build tools in the final image. |

## 🏗️ Containers vs. Virtual Machines

Before diving into Docker, it's crucial to understand how containers differ from traditional Virtual Machines.

```arch
node v_host "Host OS (VM)" at 0,0 icon=server color=slate
node v_hyper "Hypervisor" at 0,1 icon=process color=amber
node v1 "VM 1 (Guest OS + App)" at -0.5,2 shape=card color=blue
node v2 "VM 2 (Guest OS + App)" at 0.5,2 shape=card color=blue
v_host -> v_hyper
v_hyper -> v1
v_hyper -> v2
node c_host "Host OS (Container)" at 1.5,0 icon=server color=slate
node c_docker "Docker Engine" at 1.5,1 icon=process color=teal
node c1 "Container 1 (App + Libs)" at 1,2 shape=card color=purple
node c2 "Container 2 (App + Libs)" at 2,2 shape=card color=purple
c_host -> c_docker
c_docker -> c1
c_docker -> c2
```

- **Virtual Machines** include a full "Guest OS" (operating system) along with the application and necessary binaries/libraries. This makes them heavy (Gigabytes in size) and slow to boot.
- **Containers** share the host system's kernel. They only include the application and its dependencies. This makes them lightweight (Megabytes in size), fast to start, and highly portable.

## 🐳 Docker Fundamentals: Images, Containers, Layers, Registries

### The Docker Architecture

Docker uses a client-server architecture. The Docker client talks to the Docker daemon, which does the heavy lifting of building, running, and distributing your Docker containers.

```arch
node u "Docker Client" at 0,0 icon=client color=slate
node d "Docker Daemon" at 1,0 icon=server color=blue
node r "Docker Registry" at 2,0 icon=cloud color=purple
u -> d : "docker build"
node bld "Builds image layers" at 1,1 shape=card color=amber
d -> bld -> d
u -> d : "docker run"
node start "Starts container" at 1,2 shape=card color=green
d -> start -> d
u -> d : "docker push"
d -> r : "Pushes image layers"
```

### Image Layers

Every instruction in a Dockerfile (like `RUN`, `COPY`, `ADD`) creates a new layer. Docker utilizes a union file system to combine these layers into a single image. 

```arch
node l4 "Layer 4: App Code" at 0,0 shape=card color=red
node l3 "Layer 3: Installed Deps" at 0,1 shape=card color=amber
node l2 "Layer 2: Base System Updates" at 0,2 shape=card color=teal
node l1 "Layer 1: Base Image" at 0,3 shape=card color=blue
l4 -> l3 -> l2 -> l1
```

**Crucial CI/CD Concept:** Caching. When Docker builds an image, it checks its cache layer by layer. If a layer hasn't changed (e.g., your dependencies), Docker reuses the cached layer, drastically speeding up the build. This is why we copy `requirements.txt` or `go.mod` *before* the application code.

## 📝 Writing Dockerfiles for Go Applications

Go applications are uniquely suited for containers because Go compiles to a single, statically linked binary. This means the final container doesn't need a Go runtime, package managers, or underlying OS libraries.

### Anti-Pattern: Single-Stage Build

Here is a naive, inefficient way to build a Go app in Docker.

```dockerfile
# DON'T DO THIS FOR PRODUCTION
FROM golang:1.21-alpine

WORKDIR /app
COPY . .
RUN go build -o myapp .

CMD ["./myapp"]
```
*Why is this bad?* The resulting image contains the Go compiler, source code, and alpine OS tools. It's massive and insecure.

### The Standard: Multi-Stage Builds (CRITICAL for Go)

Multi-stage builds allow us to use a heavy image with all the build tools to compile the application, and then copy *only* the compiled binary into a tiny, secure, empty image (`scratch` or `distroless`) for production.

```dockerfile
# -----------------------------------------
# STAGE 1: Build Stage
# -----------------------------------------
FROM golang:1.21-alpine AS builder

# Install CA certificates for HTTPS calls and tzdata for timezones
RUN apk add --no-cache ca-certificates tzdata

# Set working directory
WORKDIR /app

# Copy dependency files first to leverage Docker layer caching
COPY go.mod go.sum ./
RUN go mod download

# Copy the rest of the source code
COPY . .

# Build the application statically
# CGO_ENABLED=0 ensures a static binary with no C dependencies
# GOOS=linux GOARCH=amd64 ensures it runs on Linux containers
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o main .

# -----------------------------------------
# STAGE 2: Final Production Stage
# -----------------------------------------
# Use `scratch` (an explicitly empty image) for the absolute smallest size.
# Alternatively, use `gcr.io/distroless/static` for minimal debugging tools.
FROM scratch

# Copy essential files from the builder stage
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Copy the static binary
COPY --from=builder /app/main /main

# Define a non-root user (scratch doesn't have `useradd`, so we use arbitrary UID)
USER 10001:10001

# Expose port (metadata only)
EXPOSE 8080

# Command to run the application
ENTRYPOINT ["/main"]
```

## 📝 Writing Dockerfiles for Python Applications

Python is an interpreted language, so we need the Python runtime in our final image. Therefore, we can't use `scratch`. Instead, we use `slim` variants of Python official images.

```dockerfile
# Use a slim, specific base image (Debian-based)
FROM python:3.11-slim-bookworm

# Set environment variables for Python behavior
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Create a non-root user to run the app
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Set working directory
WORKDIR /app

# Install system dependencies required for building Python packages (if any)
# Clean up apt cache in the same layer to keep image size small
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy dependency file and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Change ownership of the app directory to the non-root user
RUN chown -R appuser:appgroup /app

# Switch to the non-root user
USER appuser

EXPOSE 8000

# Healthcheck ensures the container is actually serving traffic
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start the application using a production WSGI/ASGI server
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "src.main:app"]
```

## 🧠 Docker Build Best Practices

### 1. Optimize Layer Ordering
Order your Dockerfile instructions from least likely to change to most likely to change.
1. `FROM` base image
2. System packages (e.g., `apt-get install`)
3. Application dependencies (e.g., `go mod download`, `pip install`)
4. Application code (`COPY . .`)

### 2. The `.dockerignore` File
Always include a `.dockerignore` file. This prevents copying large, unnecessary, or sensitive files into your build context, speeding up the build and shrinking the image.

```text
# .dockerignore
.git
.github
__pycache__/
*.pyc
node_modules/
vendor/
.env
Dockerfile
```

### 3. Use Specific Tags
Never use `latest` in production Dockerfiles (`FROM python:latest`). Base images can introduce breaking changes. Always pin versions (e.g., `python:3.11.4-slim-bookworm`).

### 4. Run as Non-Root
By default, Docker containers run as the `root` user. If an attacker breaches the container, they have root access within it. Always create and use a dedicated non-root user.

## 🏗️ Docker Compose for Local Dev and CI Testing

Docker Compose is a tool for defining and running multi-container Docker applications. It uses a YAML file to configure your application's services. It's incredibly valuable for spinning up dependencies like databases or message queues during integration testing in your CI pipeline.

Example `docker-compose.yml` for an app needing PostgreSQL:

```yaml
version: '3.8'

services:
  app:
    build: 
      context: .
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      - DB_HOST=db
      - DB_USER=myuser
      - DB_PASSWORD=mypassword
      - DB_NAME=mydb
    depends_on:
      db:
        condition: service_healthy

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_USER: myuser
      POSTGRES_PASSWORD: mypassword
      POSTGRES_DB: mydb
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U myuser -d mydb"]
      interval: 5s
      timeout: 5s
      retries: 5

volumes:
  postgres_data:
```

## 📦 Container Registries and Tagging Strategies

Once an image is built, it needs a home. Container Registries are repositories for Docker images.
- **Docker Hub:** The default public registry.
- **GitHub Container Registry (GHCR):** Highly integrated with GitHub Actions.
- **AWS ECR / Google GCR / Azure ACR:** Cloud provider specific enterprise registries.

### Tagging Strategies

How should you tag your images during the CI process?
1. **Semantic Versioning (SemVer):** `v1.2.3`. Good for public releases.
2. **Git SHA:** `commit-8a7b6c5`. **CRITICAL FOR CI/CD.** Tagging with the Git commit hash ensures absolute traceability. You know exactly which code built which image.
3. **Environment Tags:** `staging`, `production`. (Anti-pattern: better to deploy specific SHAs to environments).

*Best Practice:* In CI, build your image once, tag it with the Git SHA, push it. If it passes tests, tag *that exact same image* as `latest` or a release version. Do not rebuild.

## 🛡️ Container Security in CI/CD

Security must "shift left" into your CI pipeline.

1. **Scan Base Images:** Use tools like `Trivy` or `Grype` in your CI to scan for CVEs (Common Vulnerabilities and Exposures) in your image layers.
2. **Minimal Base Images:** Use `scratch`, `distroless`, or `alpine/slim` images. The fewer tools in an image, the smaller the attack surface. If there's no shell (`/bin/sh`) in the container (like `scratch`), an attacker can't easily execute malicious scripts even if they find an exploit.
3. **Never Hardcode Secrets:** Never `COPY .env` or `ENV DB_PASS=secret` in a Dockerfile. Inject secrets at runtime via the orchestrator (Kubernetes, ECS).

## 🚀 Building and Pushing in CI (GitHub Actions)

Here is a robust GitHub Actions workflow demonstrating caching, building, tagging, and pushing to GitHub Container Registry (GHCR).

```yaml
name: Build and Push Docker Image

on:
  push:
    branches: [ "main" ]
  pull_request:
    branches: [ "main" ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  build-and-push:
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      # Setup Docker Buildx for advanced features like caching
      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      # Login to GHCR (skip on PRs)
      - name: Log in to the Container registry
        if: github.event_name != 'pull_request'
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      # Extract metadata (tags, labels) for Docker
      - name: Extract metadata (tags, labels) for Docker
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}
          tags: |
            type=sha,format=long
            type=ref,event=branch
            type=raw,value=latest,enable={{is_default_branch}}

      # Build and push Docker image with Buildx (using layer caching)
      - name: Build and push Docker image
        uses: docker/build-push-action@v5
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

## 🔄 Using Docker Services in CI Pipelines

Often, your integration tests require a database. GitHub Actions provides `services` to run containers alongside your job.

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: testdb
          POSTGRES_PASSWORD: password
        ports:
          - 5432:5432
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5

    steps:
      - uses: actions/checkout@v4
      - name: Run Integration Tests
        env:
          DATABASE_URL: postgres://postgres:password@localhost:5432/testdb
        run: make test-integration
```

## 🔗 How This Connects
- **Previous Chapter:** [Continuous Delivery and Deployment](../06-Continuous-Delivery-and-Deployment/README.md) - CD pipelines rely on the standardized, portable container artifacts we learned to build in this chapter.
- **Next Chapter:** [CI/CD Tools Deep Dive](../08-CI-CD-Tools-Deep-Dive/README.md) - We will explore specific platforms that orchestrate the execution of the Docker containers and Compose environments we've defined.

## 📝 Chapter Summary

| Concept | Key Takeaway |
| :--- | :--- |
| **Containers vs VMs** | Containers share the OS kernel, making them incredibly fast and lightweight compared to VMs. |
| **Multi-stage Builds** | Essential for compiled languages (Go). Use a fat builder image, copy binary to a `scratch` image. |
| **Layer Caching** | Copy dependency manifests (`go.mod`, `requirements.txt`) *before* source code to drastically speed up CI builds. |
| **Security** | Always run as a non-root user. Use minimal base images (Distroless/Scratch). Scan for CVEs. |
| **CI Tagging** | Tag images with the exact Git SHA to ensure absolute traceability from code to deployed container. |

## ➡️ What's Next
Proceed to the exercises in the `exercises/` directory to practice writing Dockerfiles, optimizing layers, and building CI pipelines with Docker. Start with `exercise-01-basic.md`.
