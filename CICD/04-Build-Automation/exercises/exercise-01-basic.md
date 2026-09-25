# Exercise 1: Basic Go Makefile 🟢

## 🎯 Objective
Create a simple, standardized `Makefile` for a Go project to automate formatting, testing, and building.

## 📋 Prerequisites
- A basic understanding of Go commands (`go run`, `go build`, `go test`).
- Terminal access.

## 📝 Instructions

Imagine you have a simple Go application with a main file and a math package.

1. Create a file named `main.go`:
```go
package main

import "fmt"

func main() {
    fmt.Println("Hello, Build Automation!")
}
```

2. Create a file named `Makefile` in the same directory.
3. Define variables for the binary name.
4. Implement standard targets: `all`, `build`, `test`, `fmt`, and `clean`.
5. Ensure `.PHONY` is used so Make doesn't confuse targets with actual files.

## 💡 Hints
- Go files can be formatted automatically using `go fmt ./...`.
- To clean up, just remove the compiled binary or the output directory.
- `all` is the default target if you just run `make`. It should usually run formatting, tests, and then build.

## ✅ Expected Output / Solution

```makefile
# Makefile

# Variables
APP_NAME := my-basic-app
OUTPUT_DIR := bin

# Declare non-file targets
.PHONY: all fmt test build clean

# Default target
all: fmt test build

fmt:
	@echo "Formatting Go code..."
	go fmt ./...

test:
	@echo "Running tests..."
	go test -v ./...

build:
	@echo "Building binary..."
	mkdir -p $(OUTPUT_DIR)
	go build -o $(OUTPUT_DIR)/$(APP_NAME) main.go

clean:
	@echo "Cleaning up..."
	rm -rf $(OUTPUT_DIR)
```

To run this, you would execute:
```bash
make          # Runs all: fmt, test, build
make build    # Only builds the binary
make clean    # Removes the bin directory
```

## 🧠 Key Takeaway
A Makefile standardizes the developer workflow. Anyone cloning the repository can simply run `make` without needing to remember the exact Go compiler flags or output directories.
