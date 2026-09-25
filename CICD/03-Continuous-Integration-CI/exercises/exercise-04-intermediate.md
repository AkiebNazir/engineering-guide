# Exercise 04: Multi-Stage CI with Parallel Jobs 🟡

## 🎯 Objective
Build a multi-stage CI pipeline with parallel jobs, conditional execution, and proper artifact passing — using a Go project written from scratch.

## 📋 Prerequisites
- Go installed (`go version` to check)
- GitHub account with a repository

## 📝 The Project: A Go REST API Calculator

Create these files locally:

### `main.go`
```go
package main

import (
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"strconv"
)

type Response struct {
	Operation string  `json:"operation"`
	A         float64 `json:"a"`
	B         float64 `json:"b"`
	Result    float64 `json:"result"`
}

type ErrorResponse struct {
	Error string `json:"error"`
}

func parseParams(r *http.Request) (float64, float64, error) {
	a, err := strconv.ParseFloat(r.URL.Query().Get("a"), 64)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid parameter 'a': %v", err)
	}
	b, err := strconv.ParseFloat(r.URL.Query().Get("b"), 64)
	if err != nil {
		return 0, 0, fmt.Errorf("invalid parameter 'b': %v", err)
	}
	return a, b, nil
}

func addHandler(w http.ResponseWriter, r *http.Request) {
	a, b, err := parseParams(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{Error: err.Error()})
		return
	}
	json.NewEncoder(w).Encode(Response{Operation: "add", A: a, B: b, Result: a + b})
}

func subtractHandler(w http.ResponseWriter, r *http.Request) {
	a, b, err := parseParams(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{Error: err.Error()})
		return
	}
	json.NewEncoder(w).Encode(Response{Operation: "subtract", A: a, B: b, Result: a - b})
}

func multiplyHandler(w http.ResponseWriter, r *http.Request) {
	a, b, err := parseParams(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{Error: err.Error()})
		return
	}
	json.NewEncoder(w).Encode(Response{Operation: "multiply", A: a, B: b, Result: a * b})
}

func divideHandler(w http.ResponseWriter, r *http.Request) {
	a, b, err := parseParams(r)
	if err != nil {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{Error: err.Error()})
		return
	}
	if b == 0 {
		w.WriteHeader(http.StatusBadRequest)
		json.NewEncoder(w).Encode(ErrorResponse{Error: "division by zero"})
		return
	}
	json.NewEncoder(w).Encode(Response{Operation: "divide", A: a, B: b, Result: a / b})
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	json.NewEncoder(w).Encode(map[string]string{
		"status":  "healthy",
		"version": "1.0.0",
	})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	http.HandleFunc("/add", addHandler)
	http.HandleFunc("/subtract", subtractHandler)
	http.HandleFunc("/multiply", multiplyHandler)
	http.HandleFunc("/divide", divideHandler)
	http.HandleFunc("/health", healthHandler)

	log.Printf("Server starting on port %s", port)
	log.Fatal(http.ListenAndServe(":"+port, nil))
}
```

### `main_test.go`
```go
package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestAddHandler(t *testing.T) {
	tests := []struct {
		name     string
		query    string
		wantCode int
		wantResult float64
	}{
		{"positive numbers", "?a=2&b=3", 200, 5},
		{"negative numbers", "?a=-1&b=-4", 200, -5},
		{"decimals", "?a=1.5&b=2.5", 200, 4},
	}
	for _, tt := range tests {
		t.Run(tt.name, func(t *testing.T) {
			req := httptest.NewRequest("GET", "/add"+tt.query, nil)
			w := httptest.NewRecorder()
			addHandler(w, req)
			if w.Code != tt.wantCode {
				t.Errorf("got status %d, want %d", w.Code, tt.wantCode)
			}
			var resp Response
			json.NewDecoder(w.Body).Decode(&resp)
			if resp.Result != tt.wantResult {
				t.Errorf("got result %f, want %f", resp.Result, tt.wantResult)
			}
		})
	}
}

func TestDivideByZero(t *testing.T) {
	req := httptest.NewRequest("GET", "/divide?a=10&b=0", nil)
	w := httptest.NewRecorder()
	divideHandler(w, req)
	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestInvalidParams(t *testing.T) {
	req := httptest.NewRequest("GET", "/add?a=abc&b=2", nil)
	w := httptest.NewRecorder()
	addHandler(w, req)
	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestHealthEndpoint(t *testing.T) {
	req := httptest.NewRequest("GET", "/health", nil)
	w := httptest.NewRecorder()
	healthHandler(w, req)
	if w.Code != http.StatusOK {
		t.Errorf("expected 200, got %d", w.Code)
	}
}
```

### Your Task: Write `.github/workflows/ci.yml`

Write a CI pipeline that has these **4 parallel jobs after checkout**:

```
                    ┌── lint (golangci-lint) ──┐
git push ── build ──┤                          ├── report (summary)
                    ├── test (go test -race)   │
                    └── security (govulncheck) ─┘
```

Requirements:
1. **lint** job: Run `golangci-lint` on the code
2. **test** job: Run `go test -race -coverprofile=coverage.out ./...` and upload coverage as artifact
3. **security** job: Run `govulncheck ./...` to check for known vulnerabilities
4. **report** job: Runs ONLY if all 3 above pass, downloads coverage artifact, prints summary

## ✅ Expected Output / Solution

```yaml
name: Go CI Pipeline

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  lint:
    name: 🔍 Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Run golangci-lint
        run: |
          go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
          golangci-lint run ./...

  test:
    name: 🧪 Test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Run tests with race detector
        run: go test -race -coverprofile=coverage.out -v ./...
      - name: Show coverage
        run: go tool cover -func=coverage.out
      - name: Upload coverage
        uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage.out

  security:
    name: 🔒 Security Scan
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Run govulncheck
        run: |
          go install golang.org/x/vuln/cmd/govulncheck@latest
          govulncheck ./...

  report:
    name: 📊 Report
    needs: [lint, test, security]
    runs-on: ubuntu-latest
    steps:
      - name: Download coverage
        uses: actions/download-artifact@v4
        with:
          name: coverage
      - name: Print summary
        run: |
          echo "## CI Summary" >> $GITHUB_STEP_SUMMARY
          echo "✅ Lint: Passed" >> $GITHUB_STEP_SUMMARY
          echo "✅ Tests: Passed" >> $GITHUB_STEP_SUMMARY
          echo "✅ Security: Passed" >> $GITHUB_STEP_SUMMARY
          echo "### Coverage" >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
          cat coverage.out | head -20 >> $GITHUB_STEP_SUMMARY
          echo '```' >> $GITHUB_STEP_SUMMARY
```

## 🧠 Key Takeaway
Parallel jobs dramatically speed up CI. The `needs` keyword creates dependencies so the report job only runs when all checks pass. Artifacts let you pass data between jobs that run on different runners.
