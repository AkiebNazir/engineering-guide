# Exercise 5: Enterprise Multi-target Makefile 🔴

## 🎯 Objective
Create an advanced, enterprise-ready Makefile for a project that contains *both* a Go backend and a Python data-processing worker, simulating a real-world monorepo structure. Ensure artifacts are versioned using SemVer.

## 📋 Prerequisites
- Deep understanding of Go and Python build processes.
- Knowledge of Semantic Versioning.
- Ability to manage complex Makefiles with variables and multiple directories.

## 📝 Instructions

1. Imagine the following directory structure:
   ```
   my-monorepo/
   ├── backend/         # Go API
   │   ├── main.go
   │   └── go.mod
   ├── worker/          # Python Worker
   │   ├── pyproject.toml
   │   └── src/main.py
   └── Makefile
   ```
2. Your root `Makefile` must handle both projects.
3. Define targets: `setup`, `lint`, `test`, `build`, and `package`.
4. The `build` target should:
   - Cross-compile the Go backend for Linux.
   - Inject a SemVer version (e.g., `v1.2.3-<commit-hash>`).
5. The `package` target should:
   - Create a tarball (`.tar.gz`) containing the Go binary and the Python source code, ready for deployment.

## 💡 Hints
- Use Make's `-C` flag to run Make in subdirectories if you want, or just `cd` into them in the command execution (e.g., `cd backend && go build...`).
- A SemVer version can be simulated or read from a file. In this case, construct it using a static prefix and the Git commit.
- To create a tarball: `tar -czvf artifact.tar.gz file1 dir1/`

## ✅ Expected Output / Solution

**Makefile**
```makefile
# Variables
VERSION_PREFIX := v1.2.3
COMMIT := $(shell git rev-parse --short HEAD 2>/dev/null || echo "dev")
SEMVER := $(VERSION_PREFIX)-$(COMMIT)

GO_DIR := backend
PY_DIR := worker
OUTPUT_DIR := dist

GO_LDFLAGS := -ldflags="-X main.Version=$(SEMVER)"
GO_BINARY := api-server-linux-amd64

.PHONY: all setup lint test build package clean

all: setup lint test build package

setup:
	@echo "Setting up Go..."
	cd $(GO_DIR) && go mod tidy
	@echo "Setting up Python Worker..."
	cd $(PY_DIR) && poetry install

lint:
	@echo "Linting Go..."
	cd $(GO_DIR) && golangci-lint run ./...
	@echo "Linting Python..."
	cd $(PY_DIR) && poetry run flake8 src/

test:
	@echo "Testing Go..."
	cd $(GO_DIR) && go test -v ./...
	@echo "Testing Python..."
	cd $(PY_DIR) && poetry run pytest

build:
	@echo "Building Go backend (Version: $(SEMVER))..."
	mkdir -p $(OUTPUT_DIR)
	cd $(GO_DIR) && GOOS=linux GOARCH=amd64 go build $(GO_LDFLAGS) -o ../$(OUTPUT_DIR)/$(GO_BINARY) main.go
	@echo "Python worker does not require compilation. Ready."

package: build
	@echo "Packaging artifacts..."
	cp -r $(PY_DIR)/src $(OUTPUT_DIR)/worker-src
	cp $(PY_DIR)/pyproject.toml $(OUTPUT_DIR)/worker-src/
	cd $(OUTPUT_DIR) && tar -czvf release-$(SEMVER).tar.gz $(GO_BINARY) worker-src/
	@echo "Artifact release-$(SEMVER).tar.gz created successfully."

clean:
	rm -rf $(OUTPUT_DIR)
	cd $(PY_DIR) && find . -type d -name "__pycache__" -exec rm -rf {} +
```

## 🧠 Key Takeaway
Enterprise environments often mix technologies. A master Makefile at the root of a repository acts as the single source of truth for the CI pipeline, orchestrating complex multi-language builds and packaging them into unified, semantically versioned artifacts.
