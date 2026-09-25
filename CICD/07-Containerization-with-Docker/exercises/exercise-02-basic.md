# Exercise 02: Multi-Stage Builds for Go 🐹

## 🎯 Objective
Write a multi-stage Dockerfile for a Go application to create the smallest, most secure production image possible using `scratch`.

## 📋 Prerequisites
- Understanding of Go compilation (static binaries).
- Understanding of Docker Multi-stage builds.

## 📝 Instructions

You have a simple Go API:
```text
myapp/
├── main.go
├── go.mod
└── go.sum
```

1. Create a `Dockerfile`.
2. **Stage 1 (Builder):** 
   - Use `golang:1.21-alpine` as `builder`.
   - Set working directory to `/app`.
   - Copy `go.mod` and `go.sum`, then run `go mod download`.
   - Copy the rest of the code.
   - Build a static binary named `server`. Ensure you disable CGO (`CGO_ENABLED=0`) so it works on `scratch`.
3. **Stage 2 (Final):**
   - Start a new stage `FROM scratch`.
   - Copy *only* the compiled `server` binary from the `builder` stage to the root (`/`) of this new stage.
   - Expose port `8080`.
   - Set the `ENTRYPOINT` to execute the binary.

## 💡 Hints
- The `go build` command for a static linux binary looks like this: `CGO_ENABLED=0 GOOS=linux go build -o server .`
- To copy from a previous stage, use `COPY --from=builder /source/path /dest/path`.
- `scratch` is entirely empty. It doesn't even have `/bin/sh`.

## ✅ Expected Output / Solution

```dockerfile
# ==========================================
# STAGE 1: Builder
# ==========================================
FROM golang:1.21-alpine AS builder

WORKDIR /app

# Cache Go modules
COPY go.mod go.sum ./
RUN go mod download

# Copy source and compile static binary
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -o server .

# ==========================================
# STAGE 2: Production Final Image
# ==========================================
# Start from completely empty image
FROM scratch

# Copy only the compiled binary from the builder stage
COPY --from=builder /app/server /server

# Document port
EXPOSE 8080

# Execute the binary directly
ENTRYPOINT ["/server"]
```

## 🧠 Key Takeaway
Multi-stage builds are critical for compiled languages. Our builder stage might be 300MB+ containing the Go compiler and OS tools. Our final `scratch` image will be exactly the size of the compiled binary (e.g., ~15MB) with zero vulnerabilities because there is no OS!
