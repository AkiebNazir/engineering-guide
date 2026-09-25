# Docker and Containerization

Containers are the unit of deployment for modern backend applications. They package your code, runtime, system tools, and libraries into a standardized executable unit. This guide covers how to write production-grade `Dockerfile`s, manage data, and debug running containers.

## 1. The Mental Model

A container is not a Virtual Machine. A VM virtualizes the hardware (using a Hypervisor) so it can run an entire guest Operating System. A container virtualizes the OS (using Linux Namespaces and Cgroups) so it can run isolated processes that share the host's OS kernel.

```arch
%% caption: VMs run a full guest OS on virtual hardware; Containers share the host kernel and isolate processes.
group host1 "Virtual Machine" color=slate style=dashed
node hyp "Hypervisor" at 1,3 in host1 icon=server color=slate
node os1 "Guest OS (App A)" at 0,2 in host1 icon=server color=blue
node os2 "Guest OS (App B)" at 2,2 in host1 icon=server color=blue
os1 -> hyp
os2 -> hyp

group host2 "Container" color=slate style=dashed
node kern "Host Kernel" at 1,7 in host2 icon=cpu color=blue
node eng "Docker Engine" at 1,6 in host2 icon=docker-icon color=amber
node app3 "App A" at 0,5 in host2 icon=app color=green
node app4 "App B" at 2,5 in host2 icon=app color=green
app3 -> eng
app4 -> eng
eng -> kern
```

## 2. Dockerfile Best Practices

Writing a `Dockerfile` that builds quickly, produces a small image, and is secure requires understanding Docker's layer cache.

### The Golden Rules
1. **Order by frequency of change**: Put things that change rarely (installing OS packages) at the top. Put things that change constantly (copying your source code) at the very bottom.
2. **Multi-stage builds**: Use one stage with all the compilers and tools to build the binary, and a second tiny stage (like `alpine` or `distroless`) to actually run it.
3. **Don't run as root**: Always create a non-root user and `USER` directive.
4. **Clean up in the same layer**: If you `apt-get install`, run `rm -rf /var/lib/apt/lists/*` in the exact same `RUN` command to prevent the downloaded archives from being permanently baked into the image layer.

### Example: A Production Go Dockerfile

```dockerfile
# Stage 1: Build
FROM golang:1.21-alpine AS builder

# Install git and ca-certificates (needed for fetching deps and making HTTPS calls)
RUN apk update && apk add --no-cache git ca-certificates tzdata && update-ca-certificates

# Create a non-root user
ENV USER=appuser
ENV UID=10001
RUN adduser --disabled-password --gecos "" --home "/nonexistent" \
    --shell "/sbin/nologin" --no-create-home --uid "${UID}" "${USER}"

WORKDIR /app
COPY go.mod go.sum ./
# Download dependencies first. This layer is cached unless go.mod changes.
RUN go mod download

# Copy the actual code
COPY . .
# Build the binary statically
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build -ldflags="-w -s" -o /go/bin/server .

# Stage 2: Run
FROM scratch
# Import the user and certificates from the builder
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /etc/passwd /etc/passwd
COPY --from=builder /etc/group /etc/group

# Copy the binary
COPY --from=builder /go/bin/server /go/bin/server

# Use the unprivileged user
USER appuser:appuser
EXPOSE 8080
ENTRYPOINT ["/go/bin/server"]
```

## 3. Data Volumes and Persistence

Containers are ephemeral. If a container dies, anything written to its filesystem is destroyed. To persist data, you must mount a volume.

- **Named Volumes**: Managed by Docker (`docker volume create db_data`). Best for databases and persistent app data.
- **Bind Mounts**: Mounts a specific path on your host machine (e.g., `/Users/me/code:/app`). Used exclusively for local development so your code changes instantly reflect inside the container.

```bash
# Run Postgres with a named volume so data survives restarts
docker run -d --name my-db -v pgdata:/var/lib/postgresql/data -e POSTGRES_PASSWORD=secret postgres:15
```

## 4. Networking

By default, containers can't talk to each other using hostnames unless they are on a custom bridge network.

```bash
# 1. Create a network
docker network create my-app-net

# 2. Run DB on the network
docker run -d --name db --network my-app-net postgres:15

# 3. Run Web server on the network, exposing port 8080 to the host
# The web server can connect to the DB using the hostname "db"
docker run -d --name web -p 8080:80 --network my-app-net my-web-image
```

## 5. Docker Compose

`docker-compose.yml` is infrastructure-as-code for local development. It replaces having to memorize 5 long `docker run` commands.

```yaml
version: '3.8'
services:
  api:
    build: .
    ports:
      - "8080:8080"
    environment:
      - DB_URL=postgres://user:pass@db:5432/mydb
    depends_on:
      - db
  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_USER=user
      - POSTGRES_PASSWORD=pass
      - POSTGRES_DB=mydb

volumes:
  pgdata:
```

## 6. Debugging a Running Container

When things go wrong, these are the tools to reach for:

```bash
# See the logs (stdout/stderr) of a container
docker logs -f <container_id>

# Run an interactive shell inside a running container
docker exec -it <container_id> /bin/sh

# See resource usage (CPU/RAM)
docker stats

# Inspect the environment variables and network config
docker inspect <container_id>
```

If the container crashes immediately and `docker exec` isn't possible because the container isn't running, override the entrypoint to keep it alive:

```bash
docker run -it --entrypoint /bin/sh my-failing-image
```

## 7. Common Interview/Troubleshooting Questions

**"My build takes 10 minutes every time I change one line of code."**
You are `COPY . .` before installing dependencies (e.g., `npm install` or `go mod download`). Docker invalidates the cache for the `RUN npm install` layer because the source files changed. Move the dependency installation *above* the source code copy.

**"My image is 1.5GB but my app is only 20MB."**
You are using a full OS base image (like `ubuntu` or `node:18`) instead of an `alpine` or `slim` variant, and you aren't using Multi-stage builds to discard the build tools (compilers, headers) in the final image.

## What's Next
Docker runs containers on one machine. To run containers across 100 machines, handle failover, zero-downtime deployments, and load balancing, you need **Kubernetes**.
