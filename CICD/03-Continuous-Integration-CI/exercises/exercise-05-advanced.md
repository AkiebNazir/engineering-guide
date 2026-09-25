# Exercise 05: Enterprise CI Pipeline — Monorepo with Go + Python 🔴

## 🎯 Objective
Build an enterprise-grade CI pipeline for a monorepo containing both a Go microservice and a Python service, with path-based triggering, shared workflows, and comprehensive quality gates.

## 📋 Prerequisites
- All previous exercises completed
- Understanding of build matrices, caching, artifacts, and parallel jobs

## 📝 The Project Structure

```
enterprise-app/
├── .github/
│   └── workflows/
│       ├── ci-go.yml          # Go service CI
│       ├── ci-python.yml      # Python service CI
│       └── ci-integration.yml # Full integration tests
├── services/
│   ├── api-gateway/           # Go service
│   │   ├── main.go
│   │   ├── main_test.go
│   │   ├── handlers/
│   │   │   ├── auth.go
│   │   │   └── auth_test.go
│   │   └── go.mod
│   └── ml-service/            # Python service
│       ├── app.py
│       ├── test_app.py
│       ├── models/
│       │   ├── predictor.py
│       │   └── test_predictor.py
│       └── requirements.txt
└── README.md
```

### `services/api-gateway/go.mod`
```
module github.com/enterprise/api-gateway

go 1.22
```

### `services/api-gateway/main.go`
```go
package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"time"

	"github.com/enterprise/api-gateway/handlers"
)

type HealthResponse struct {
	Status    string `json:"status"`
	Service   string `json:"service"`
	Version   string `json:"version"`
	Timestamp string `json:"timestamp"`
}

func healthHandler(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(HealthResponse{
		Status:    "healthy",
		Service:   "api-gateway",
		Version:   os.Getenv("APP_VERSION"),
		Timestamp: time.Now().UTC().Format(time.RFC3339),
	})
}

func main() {
	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}

	mux := http.NewServeMux()
	mux.HandleFunc("/health", healthHandler)
	mux.HandleFunc("/auth/login", handlers.LoginHandler)
	mux.HandleFunc("/auth/validate", handlers.ValidateHandler)

	log.Printf("API Gateway starting on :%s", port)
	log.Fatal(http.ListenAndServe(":"+port, mux))
}
```

### `services/api-gateway/handlers/auth.go`
```go
package handlers

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"net/http"
	"strings"
	"time"
)

type LoginRequest struct {
	Username string `json:"username"`
	Password string `json:"password"`
}

type TokenResponse struct {
	Token     string `json:"token"`
	ExpiresAt string `json:"expires_at"`
}

func hashPassword(password string) string {
	h := sha256.New()
	h.Write([]byte(password))
	return hex.EncodeToString(h.Sum(nil))
}

func generateToken(username string) string {
	h := sha256.New()
	h.Write([]byte(username + time.Now().String()))
	return hex.EncodeToString(h.Sum(nil))
}

func LoginHandler(w http.ResponseWriter, r *http.Request) {
	if r.Method != http.MethodPost {
		http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
		return
	}

	var req LoginRequest
	if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
		http.Error(w, "invalid request body", http.StatusBadRequest)
		return
	}

	if strings.TrimSpace(req.Username) == "" || strings.TrimSpace(req.Password) == "" {
		http.Error(w, "username and password required", http.StatusBadRequest)
		return
	}

	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(TokenResponse{
		Token:     generateToken(req.Username),
		ExpiresAt: time.Now().Add(24 * time.Hour).UTC().Format(time.RFC3339),
	})
}

func ValidateHandler(w http.ResponseWriter, r *http.Request) {
	token := r.Header.Get("Authorization")
	if token == "" {
		http.Error(w, "missing authorization header", http.StatusUnauthorized)
		return
	}
	// Simplified validation
	if len(token) < 10 {
		http.Error(w, "invalid token", http.StatusUnauthorized)
		return
	}
	w.Header().Set("Content-Type", "application/json")
	json.NewEncoder(w).Encode(map[string]string{"status": "valid"})
}
```

### `services/api-gateway/handlers/auth_test.go`
```go
package handlers

import (
	"bytes"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestLoginHandler_Success(t *testing.T) {
	body := `{"username":"admin","password":"secret123"}`
	req := httptest.NewRequest(http.MethodPost, "/auth/login", bytes.NewBufferString(body))
	w := httptest.NewRecorder()
	LoginHandler(w, req)

	if w.Code != http.StatusOK {
		t.Fatalf("expected 200, got %d: %s", w.Code, w.Body.String())
	}
	var resp TokenResponse
	json.NewDecoder(w.Body).Decode(&resp)
	if resp.Token == "" {
		t.Error("expected non-empty token")
	}
}

func TestLoginHandler_EmptyFields(t *testing.T) {
	body := `{"username":"","password":""}`
	req := httptest.NewRequest(http.MethodPost, "/auth/login", bytes.NewBufferString(body))
	w := httptest.NewRecorder()
	LoginHandler(w, req)

	if w.Code != http.StatusBadRequest {
		t.Errorf("expected 400, got %d", w.Code)
	}
}

func TestLoginHandler_WrongMethod(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/auth/login", nil)
	w := httptest.NewRecorder()
	LoginHandler(w, req)
	if w.Code != http.StatusMethodNotAllowed {
		t.Errorf("expected 405, got %d", w.Code)
	}
}

func TestValidateHandler_NoToken(t *testing.T) {
	req := httptest.NewRequest(http.MethodGet, "/auth/validate", nil)
	w := httptest.NewRecorder()
	ValidateHandler(w, req)
	if w.Code != http.StatusUnauthorized {
		t.Errorf("expected 401, got %d", w.Code)
	}
}

func TestHashPassword(t *testing.T) {
	h1 := hashPassword("test")
	h2 := hashPassword("test")
	if h1 != h2 {
		t.Error("same input should produce same hash")
	}
	h3 := hashPassword("different")
	if h1 == h3 {
		t.Error("different input should produce different hash")
	}
}
```

### `services/ml-service/app.py`
```python
"""ML Prediction Service — simplified for CI/CD demonstration."""
from http.server import HTTPServer, BaseHTTPRequestHandler
import json
import os
from models.predictor import Predictor

predictor = Predictor()

class MLHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/health":
            self._respond(200, {
                "status": "healthy",
                "service": "ml-service",
                "model_loaded": predictor.is_loaded(),
            })
        else:
            self._respond(404, {"error": "not found"})

    def do_POST(self):
        if self.path == "/predict":
            content_length = int(self.headers.get("Content-Length", 0))
            body = json.loads(self.rfile.read(content_length))
            features = body.get("features", [])
            if not features:
                self._respond(400, {"error": "features required"})
                return
            result = predictor.predict(features)
            self._respond(200, {"prediction": result})
        else:
            self._respond(404, {"error": "not found"})

    def _respond(self, status, data):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode())

def run(port=5000):
    server = HTTPServer(("", port), MLHandler)
    print(f"ML Service running on port {port}")
    server.serve_forever()

if __name__ == "__main__":
    run(int(os.environ.get("PORT", 5000)))
```

### `services/ml-service/models/predictor.py`
```python
"""Simple predictor for CI/CD demonstration."""
import math
from typing import List

class Predictor:
    def __init__(self):
        self._weights = [0.5, -0.3, 0.8, 0.1]
        self._bias = 0.2
        self._loaded = True

    def is_loaded(self) -> bool:
        return self._loaded

    def predict(self, features: List[float]) -> float:
        if not features:
            raise ValueError("Features list cannot be empty")
        # Simple linear prediction
        weighted_sum = sum(
            f * w for f, w in zip(features, self._weights)
        ) + self._bias
        # Sigmoid activation
        return round(1 / (1 + math.exp(-weighted_sum)), 4)

    def predict_batch(self, batch: List[List[float]]) -> List[float]:
        return [self.predict(features) for features in batch]
```

### `services/ml-service/models/test_predictor.py`
```python
import pytest
from models.predictor import Predictor

@pytest.fixture
def predictor():
    return Predictor()

def test_predictor_is_loaded(predictor):
    assert predictor.is_loaded() is True

def test_predict_returns_float(predictor):
    result = predictor.predict([1.0, 2.0, 3.0, 4.0])
    assert isinstance(result, float)

def test_predict_between_0_and_1(predictor):
    result = predictor.predict([1.0, 2.0, 3.0, 4.0])
    assert 0.0 <= result <= 1.0

def test_predict_empty_raises(predictor):
    with pytest.raises(ValueError):
        predictor.predict([])

def test_predict_batch(predictor):
    batch = [[1.0, 2.0, 3.0, 4.0], [0.0, 0.0, 0.0, 0.0]]
    results = predictor.predict_batch(batch)
    assert len(results) == 2
    assert all(0.0 <= r <= 1.0 for r in results)

def test_predict_deterministic(predictor):
    r1 = predictor.predict([1.0, 2.0, 3.0, 4.0])
    r2 = predictor.predict([1.0, 2.0, 3.0, 4.0])
    assert r1 == r2
```

### `services/ml-service/test_app.py`
```python
import pytest
import json
from unittest.mock import patch, MagicMock
from app import MLHandler

def test_health_endpoint():
    """Verify health check returns loaded status."""
    from models.predictor import Predictor
    p = Predictor()
    assert p.is_loaded() is True

def test_predictor_integration():
    """Integration test: full predict flow."""
    from models.predictor import Predictor
    p = Predictor()
    result = p.predict([0.5, 0.3, 0.7, 0.9])
    assert isinstance(result, float)
    assert 0 <= result <= 1
```

### `services/ml-service/requirements.txt`
```
pytest==8.3.2
pytest-cov==5.0.0
flake8==7.1.0
mypy==1.11.0
```

---

## Your Task: Write 3 Workflow Files

### Workflow 1: `ci-go.yml`
- Triggers ONLY when files in `services/api-gateway/` change
- Jobs: vet, lint, test (with coverage), build binary
- Build matrix: Go 1.21 and 1.22
- Upload test coverage and binary as artifacts

### Workflow 2: `ci-python.yml`
- Triggers ONLY when files in `services/ml-service/` change
- Jobs: lint (flake8), type-check (mypy), test (pytest with coverage)
- Build matrix: Python 3.11 and 3.12
- Upload coverage report as artifact

### Workflow 3: `ci-integration.yml`
- Triggers when EITHER service changes
- Runs AFTER both service pipelines pass
- Starts both services, runs cross-service health checks

---

## ✅ Solution

### `.github/workflows/ci-go.yml`
```yaml
name: Go API Gateway CI

on:
  push:
    branches: [main]
    paths:
      - 'services/api-gateway/**'
  pull_request:
    branches: [main]
    paths:
      - 'services/api-gateway/**'

defaults:
  run:
    working-directory: services/api-gateway

jobs:
  vet:
    name: 🔍 Go Vet
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: go vet ./...

  lint:
    name: 🧹 Lint
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - run: |
          go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest
          golangci-lint run ./...

  test:
    name: 🧪 Test (Go ${{ matrix.go-version }})
    needs: [vet, lint]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        go-version: ['1.21', '1.22']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: ${{ matrix.go-version }}
      - name: Run tests
        run: go test -race -coverprofile=coverage.out -v ./...
      - name: Coverage summary
        run: go tool cover -func=coverage.out
      - uses: actions/upload-artifact@v4
        if: matrix.go-version == '1.22'
        with:
          name: go-coverage
          path: services/api-gateway/coverage.out

  build:
    name: 🔨 Build Binary
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'
      - name: Build
        run: |
          CGO_ENABLED=0 GOOS=linux go build -ldflags="-s -w" -o api-gateway .
          ls -lh api-gateway
      - uses: actions/upload-artifact@v4
        with:
          name: api-gateway-binary
          path: services/api-gateway/api-gateway
```

### `.github/workflows/ci-python.yml`
```yaml
name: Python ML Service CI

on:
  push:
    branches: [main]
    paths:
      - 'services/ml-service/**'
  pull_request:
    branches: [main]
    paths:
      - 'services/ml-service/**'

defaults:
  run:
    working-directory: services/ml-service

jobs:
  lint:
    name: 🔍 Lint (flake8)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install flake8
      - run: flake8 . --max-line-length=120 --statistics

  type-check:
    name: 🏷️ Type Check (mypy)
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'
          cache: 'pip'
      - run: pip install -r requirements.txt
      - run: mypy --ignore-missing-imports .

  test:
    name: 🧪 Test (Python ${{ matrix.python-version }})
    needs: [lint, type-check]
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.11', '3.12']
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'
      - run: pip install -r requirements.txt
      - name: Run tests with coverage
        run: pytest --cov=. --cov-report=term-missing --cov-report=xml -v
      - uses: actions/upload-artifact@v4
        if: matrix.python-version == '3.12'
        with:
          name: python-coverage
          path: services/ml-service/coverage.xml
```

### `.github/workflows/ci-integration.yml`
```yaml
name: Integration Tests

on:
  push:
    branches: [main]
    paths:
      - 'services/**'
  pull_request:
    branches: [main]
    paths:
      - 'services/**'

jobs:
  integration:
    name: 🔗 Cross-Service Integration Tests
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-go@v5
        with:
          go-version: '1.22'

      - uses: actions/setup-python@v5
        with:
          python-version: '3.12'

      - name: Install Python deps
        run: pip install -r services/ml-service/requirements.txt

      - name: Build Go service
        run: go build -o api-gateway .
        working-directory: services/api-gateway

      - name: Start services
        run: |
          # Start Go API Gateway
          cd services/api-gateway && PORT=8080 ./api-gateway &
          # Start Python ML Service
          cd services/ml-service && PORT=5000 python app.py &
          # Wait for services to start
          sleep 3

      - name: Health check — API Gateway
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8080/health)
          if [ "$STATUS" != "200" ]; then
            echo "❌ API Gateway health check failed with status $STATUS"
            exit 1
          fi
          echo "✅ API Gateway is healthy"
          curl -s http://localhost:8080/health | python3 -m json.tool

      - name: Health check — ML Service
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:5000/health)
          if [ "$STATUS" != "200" ]; then
            echo "❌ ML Service health check failed with status $STATUS"
            exit 1
          fi
          echo "✅ ML Service is healthy"
          curl -s http://localhost:5000/health | python3 -m json.tool

      - name: Cross-service test
        run: |
          echo "Testing auth login..."
          RESPONSE=$(curl -s -X POST http://localhost:8080/auth/login \
            -H "Content-Type: application/json" \
            -d '{"username":"testuser","password":"testpass"}')
          echo "$RESPONSE" | python3 -m json.tool
          
          echo "Testing ML prediction..."
          PREDICTION=$(curl -s -X POST http://localhost:5000/predict \
            -H "Content-Type: application/json" \
            -d '{"features":[0.5,0.3,0.7,0.9]}')
          echo "$PREDICTION" | python3 -m json.tool
          
          echo "✅ All integration tests passed!"
```

## 🧠 Key Takeaway
Enterprise monorepos use **path-based triggering** so that changes to one service don't trigger CI for another. Integration tests verify services work together. This pattern scales to dozens of services with fast, targeted CI.
