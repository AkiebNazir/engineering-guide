# syntax=docker/dockerfile:1
#
# Multi-stage build for the problem 25 capstone service.
#
# Stage 1 (build) uses the full Go toolchain to produce a static binary.
# Stage 2 (final) copies ONLY that binary into a distroless, non-root
# runtime image — no shell, no package manager, no libc even, which
# shrinks both the image size and the attack surface: there is nothing in
# the final image an attacker who gets code execution could use to pull
# further tools, read arbitrary files as root, or persist a shell.
#
# Build (from the GoEngineering/ module root, so the build context has
# go.mod/go.sum and every problem's source):
#
#   docker build -f 25_production_service_capstone/solution/Dockerfile -t capstone-server .
#
# Run:
#
#   docker run --rm -p 8080:8080 capstone-server

### ---- Stage 1: build ----
FROM golang:1.26-alpine AS build

WORKDIR /src

# Copy go.mod/go.sum first and download separately from the rest of the
# source so Docker's layer cache is only invalidated by a dependency
# change, not by every source edit.
COPY go.mod go.sum ./
RUN go mod download

COPY . .

# CGO_ENABLED=0 produces a fully static binary (no libc dependency at
# runtime, required for a scratch/distroless-static final image).
# -trimpath removes local filesystem paths from the binary for
# reproducibility. -ldflags="-s -w" strips debug symbols/DWARF info,
# reducing binary size (trade-off: no symbolized stack traces or delve
# debugging against the shipped binary — acceptable for a production
# artifact when symbols are kept in a separate build/debug pipeline).
RUN CGO_ENABLED=0 GOOS=linux GOARCH=amd64 go build \
    -trimpath -ldflags="-s -w" \
    -o /out/capstone-server \
    ./25_production_service_capstone/solution

### ---- Stage 2: final runtime image ----
# distroless "static-debian12:nonroot": no shell, no package manager, and
# already runs as a non-root "nonroot" user/group by default — the
# explicit USER line below is kept anyway so the intent is visible without
# having to know that fact about the base image.
FROM gcr.io/distroless/static-debian12:nonroot AS final

COPY --from=build /out/capstone-server /capstone-server

USER nonroot:nonroot

EXPOSE 8080

ENTRYPOINT ["/capstone-server"]
