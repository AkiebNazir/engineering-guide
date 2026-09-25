# Exercise 3: Go Cross-Compilation and ldflags 🟡

## 🎯 Objective
Use a Makefile to compile a Go binary for multiple operating systems and inject a Git commit hash as the version number at build time.

## 📋 Prerequisites
- Completion of Exercise 1.
- Understanding of Go cross-compilation environment variables (`GOOS`, `GOARCH`).

## 📝 Instructions

1. Create a `main.go` that prints out a global variable called `Version`.
2. Write a `Makefile` that grabs the current Git commit hash using `git rev-parse --short HEAD` and stores it in a Make variable.
3. Create targets to build for:
   - Linux (amd64)
   - macOS (arm64)
   - Windows (amd64)
4. Use Go's `-ldflags="-X main.Version=..."` to inject the Git commit into the binary.

## 💡 Hints
- In a Makefile, you evaluate a shell command and assign it to a variable like this: `COMMIT := $(shell git rev-parse --short HEAD)`.
- If you don't have a git repo initialized, run `git init` and commit a file so the shell command doesn't fail.

## ✅ Expected Output / Solution

**main.go**
```go
package main

import "fmt"

// Version will be injected at build time
var Version = "dev"

func main() {
    fmt.Printf("Starting application, Version: %s\n", Version)
}
```

**Makefile**
```makefile
APP_NAME := my-multiarch-app
OUTPUT_DIR := bin

# Get the short git commit hash; fallback to 'dev' if not a git repo
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "dev")
LDFLAGS := -ldflags="-X main.Version=$(COMMIT)"

.PHONY: all clean build-linux build-mac build-windows

all: build-linux build-mac build-windows

build-linux:
	@echo "Building for Linux (amd64)..."
	GOOS=linux GOARCH=amd64 go build $(LDFLAGS) -o $(OUTPUT_DIR)/$(APP_NAME)-linux-amd64 main.go

build-mac:
	@echo "Building for macOS (arm64)..."
	GOOS=darwin GOARCH=arm64 go build $(LDFLAGS) -o $(OUTPUT_DIR)/$(APP_NAME)-darwin-arm64 main.go

build-windows:
	@echo "Building for Windows (amd64)..."
	GOOS=windows GOARCH=amd64 go build $(LDFLAGS) -o $(OUTPUT_DIR)/$(APP_NAME)-windows-amd64.exe main.go

clean:
	rm -rf $(OUTPUT_DIR)
```

## 🧠 Key Takeaway
By combining `Makefile` automation, Go cross-compilation, and `ldflags`, you can produce release-ready binaries for multiple platforms with exact version traceability—all from a single command (`make all`).
