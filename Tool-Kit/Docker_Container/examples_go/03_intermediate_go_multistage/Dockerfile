# Stage 1: Build
FROM golang:1.21 AS builder
WORKDIR /app
COPY main.go .
# Disable CGO for static compilation
RUN CGO_ENABLED=0 GOOS=linux go build -o api main.go

# Stage 2: Minimal Runtime
FROM scratch
WORKDIR /
COPY --from=builder /app/api /api
EXPOSE 8080
CMD ["/api"]
