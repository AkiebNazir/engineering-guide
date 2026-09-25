# Exercise 05: The Enterprise-Grade Container 🏢🔐

## 🎯 Objective
Combine all concepts to create a production-ready, enterprise-grade Dockerfile for a Go API, including multi-stage builds, non-root users, timezone data, SSL certificates, and Docker Healthchecks.

## 📋 Prerequisites
- All previous exercises in this chapter.

## 📝 Instructions

Enterprise environments demand secure and observable containers. 
Create an advanced `Dockerfile` for a Go API:

1. **Builder Stage:**
   - Base: `golang:1.21-alpine`.
   - Install `ca-certificates` and `tzdata` (timezone data).
   - Create a non-root user and group (e.g., `appuser` with UID/GID 10001) in the builder stage by editing `/etc/passwd` and `/etc/group` (because we'll copy these files later). 
     *(Hint: `RUN echo "appuser:x:10001:10001::/nonexistent:/sbin/nologin" > /etc_passwd_custom`)*
   - Build the Go app statically (`CGO_ENABLED=0`).
2. **Final Stage:**
   - Base: `scratch`.
   - Copy `ca-certificates` and `zoneinfo` from the builder.
   - Copy the custom passwd/group files from the builder to `/etc/passwd` and `/etc/group` in scratch.
   - Copy the compiled Go binary.
   - Switch to the `appuser` using `USER 10001:10001`.
   - Expose port `8080`.
   - Add a `HEALTHCHECK` instruction. Since `scratch` doesn't have `curl`, you must assume the Go binary itself has a built-in health check flag, e.g., `/app/server -health`. Wait, Docker `HEALTHCHECK` requires a shell by default, but you can use an exec form.
   - Entrypoint is the binary.

## 💡 Hints
- You cannot run `useradd` in `scratch`. You must create the user definitions in the builder stage and `COPY` them into `/etc/passwd` in the final stage.
- For `HEALTHCHECK` in scratch, use the array syntax: `HEALTHCHECK --interval=10s CMD ["/server", "-healthcheck"]` (assuming your Go app implements this CLI flag).

## ✅ Expected Output / Solution

```dockerfile
# ==========================================
# STAGE 1: Builder
# ==========================================
FROM golang:1.21-alpine AS builder

# Install SSL root certificates and Timezone data
RUN apk add --no-cache ca-certificates tzdata

# Create a non-root user definition in custom files
RUN echo "appuser:x:10001:10001::/nonexistent:/sbin/nologin" > /custom_passwd
RUN echo "appgroup:x:10001:" > /custom_group

WORKDIR /app

# Cache dependencies
COPY go.mod go.sum ./
RUN go mod download

# Build static binary
COPY . .
RUN CGO_ENABLED=0 GOOS=linux go build -ldflags="-w -s" -o server .

# ==========================================
# STAGE 2: Production Final Image
# ==========================================
FROM scratch

# Import certs and timezone data from builder
COPY --from=builder /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=builder /usr/share/zoneinfo /usr/share/zoneinfo

# Import the user and group files
COPY --from=builder /custom_passwd /etc/passwd
COPY --from=builder /custom_group /etc/group

# Copy the binary
COPY --from=builder /app/server /server

# Switch to the non-root user
USER 10001:10001

EXPOSE 8080

# Healthcheck utilizing a built-in command in the Go binary
# (Requires the Go app to handle the "-healthcheck" flag)
HEALTHCHECK --interval=30s --timeout=3s --retries=3 \
  CMD ["/server", "-healthcheck"]

ENTRYPOINT ["/server"]
```

## 🧠 Key Takeaway
This is the gold standard for Go containers in enterprise environments. It results in a tiny image (only the binary size + certs), prevents root escalation attacks, handles secure outbound HTTPS requests (via `ca-certificates`), handles timezones correctly, and tells the orchestrator (like Kubernetes or Docker Compose) if the application is actually healthy.
