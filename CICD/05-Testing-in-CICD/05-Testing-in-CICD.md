# Chapter 05: Testing in CI/CD

## 🎯 Learning Objectives
By the end of this chapter, you will be able to:
1. Understand the Testing Pyramid and how it maps to CI/CD pipelines.
2. Write idiomatic unit tests in Go and Python (including table-driven tests and fixtures).
3. Test HTTP handlers, APIs, and use mocking frameworks effectively.
4. Integrate code coverage analysis into your pipelines.
5. Manage test parallelism, flaky tests, and test result reporting (e.g., JUnit XML).
6. Understand advanced concepts like contract testing, load testing, and mutation testing.

## 📖 Introduction
Imagine trying to launch a rocket without testing any of its parts individually, testing its engines on the launchpad, or running a simulation. The chances of a spectacular explosion are basically 100%. Software delivery is similar. Testing in CI/CD acts as a series of automated checkpoints, from checking individual "nuts and bolts" (unit tests) to simulating the full "rocket launch" (End-to-End tests).

A robust CI/CD pipeline ensures that every commit is automatically verified against a suite of automated tests, providing rapid feedback to developers and ensuring that bugs don't reach production.

## 🔑 Key Terminology

| Term | Definition |
|------|------------|
| **Unit Test** | Testing an individual, isolated component (like a function or class) in code. |
| **Integration Test** | Testing how multiple components work together, often involving external dependencies like databases. |
| **End-to-End (E2E) Test** | Testing the entire application flow from the user's perspective. |
| **Mock/Stub** | A fake implementation of a dependency used to isolate the system under test. |
| **Code Coverage** | A metric measuring the percentage of source code executed by the test suite. |
| **Test Fixture** | Fixed state or data used as a baseline for running tests. |
| **Flaky Test** | A test that sometimes passes and sometimes fails without code changes. |
| **TDD** | Test-Driven Development; writing tests before writing the actual code. |

## 📐 The Testing Pyramid

The Testing Pyramid is a framework that guides how many tests of each type you should write.

```arch
node e "E2E Tests (UI)" at 1,0 shape=card color=red sub="Slow, Expensive"
node i "Integration / API Tests" at 1,1 shape=card color=amber sub="Medium Speed"
node u "Unit Tests" at 1,2 shape=card color=green sub="Fast, Cheap, Isolated"
e -> i
i -> u
```

* **Unit Tests**: Form the base. They are fast, reliable, and cheap to write and run. You should have thousands of these.
* **Integration Tests**: Form the middle. They check component interactions. They are slower and require more setup.
* **E2E Tests**: Form the peak. They test the whole system. They are slow, prone to flakiness, and hard to maintain. Keep these to critical user journeys.

## 🐹 Unit Testing in Go

Go has a built-in testing framework via the `testing` package. The idiomatic way to write tests in Go is using **Table-Driven Tests**.

### Go Table-Driven Tests Example
Table-driven tests use a slice of anonymous structs to define inputs and expected outputs, iterating over them to run subtests (`t.Run`).

```go
// math_test.go
package math

import "testing"

func Add(a, b int) int {
	return a + b
}

func TestAdd(t *testing.Test) {
	// Define the test table
	tests := []struct {
		name     string
		a        int
		b        int
		expected int
	}{
		{"positive numbers", 2, 3, 5},
		{"negative numbers", -1, -2, -3},
		{"mixed numbers", -1, 5, 4},
		{"zeroes", 0, 0, 0},
	}

	for _, tt := range tests {
		// Run subtests
		t.Run(tt.name, func(t *testing.T) {
			result := Add(tt.a, tt.b)
			if result != tt.expected {
				t.Errorf("Add(%d, %d) = %d; expected %d", tt.a, tt.b, result, tt.expected)
			}
		})
	}
}
```

Run tests with: `go test ./... -v`

## 🐍 Unit Testing in Python

In Python, `pytest` is the industry standard. It's powerful, extensible, and requires less boilerplate than the built-in `unittest` module.

### Pytest Fixtures and Parametrize Example
Pytest uses `fixtures` for setup/teardown and `@pytest.mark.parametrize` for table-driven testing.

```python
# test_math.py
import pytest

def divide(a, b):
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b

# A simple fixture
@pytest.fixture
def sample_numbers():
    return {"a": 10, "b": 2}

def test_divide_fixture(sample_numbers):
    assert divide(sample_numbers["a"], sample_numbers["b"]) == 5.0

# Table-driven testing using parametrize
@pytest.mark.parametrize("a, b, expected", [
    (10, 2, 5.0),
    (-10, 2, -5.0),
    (0, 5, 0.0),
])
def test_divide_parametrize(a, b, expected):
    assert divide(a, b) == expected

def test_divide_by_zero():
    with pytest.raises(ValueError, match="Cannot divide by zero"):
        divide(10, 0)
```

Run tests with: `pytest -v`

## 🌐 Testing HTTP Handlers

Testing endpoints is critical for web services. Both Go and Python provide tools to test HTTP handlers without starting a real web server.

### Go HTTP Handler Testing (`httptest`)

```go
package api

import (
	"fmt"
	"net/http"
	"net/http/httptest"
	"testing"
)

func HealthCheckHandler(w http.ResponseWriter, r *http.Request) {
	w.WriteHeader(http.StatusOK)
	fmt.Fprint(w, "OK")
}

func TestHealthCheckHandler(t *testing.T) {
	req, err := http.NewRequest("GET", "/health", nil)
	if err != nil {
		t.Fatal(err)
	}

	// Create a ResponseRecorder (which satisfies http.ResponseWriter) to record the response.
	rr := httptest.NewRecorder()
	handler := http.HandlerFunc(HealthCheckHandler)

	// Our handlers satisfy http.Handler, so we can call their ServeHTTP method 
	// directly and pass in our Request and ResponseRecorder.
	handler.ServeHTTP(rr, req)

	if status := rr.Code; status != http.StatusOK {
		t.Errorf("handler returned wrong status code: got %v want %v", status, http.StatusOK)
	}

	expected := `OK`
	if rr.Body.String() != expected {
		t.Errorf("handler returned unexpected body: got %v want %v", rr.Body.String(), expected)
	}
}
```

### Python HTTP Handler Testing (FastAPI/Flask)
Using `TestClient` in FastAPI:

```python
from fastapi import FastAPI
from fastapi.testclient import TestClient

app = FastAPI()

@app.get("/health")
def read_health():
    return {"status": "OK"}

client = TestClient(app)

def test_read_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "OK"}
```

## 🎭 Mocking and Stubbing

When testing a component that relies on external services (like a database or an external API), we use mocks to isolate the unit.

### Python Mocking with `unittest.mock`

```python
import requests
from unittest.mock import patch

def get_user_name(user_id):
    response = requests.get(f"https://api.example.com/users/{user_id}")
    return response.json().get("name")

@patch('requests.get')
def test_get_user_name(mock_get):
    # Setup mock behavior
    mock_get.return_value.json.return_value = {"name": "Alice"}
    
    name = get_user_name(1)
    
    assert name == "Alice"
    mock_get.assert_called_once_with("https://api.example.com/users/1")
```

### Go Mocking with Interfaces
In Go, mocking is naturally achieved using interfaces.

```go
package service

import "testing"

// 1. Define an interface for the dependency
type UserRepository interface {
	GetUser(id string) string
}

// 2. The service depends on the interface
type UserService struct {
	Repo UserRepository
}

func (s *UserService) GetUserName(id string) string {
	return s.Repo.GetUser(id)
}

// 3. Create a mock implementation for tests
type MockUserRepository struct {
	MockGetUser func(id string) string
}

func (m *MockUserRepository) GetUser(id string) string {
	return m.MockGetUser(id)
}

// 4. Use the mock in tests
func TestGetUserName(t *testing.T) {
	mockRepo := &MockUserRepository{
		MockGetUser: func(id string) string {
			return "Alice"
		},
	}
	
	service := UserService{Repo: mockRepo}
	name := service.GetUserName("123")
	
	if name != "Alice" {
		t.Errorf("Expected Alice, got %s", name)
	}
}
```

## 📊 Code Coverage in CI/CD

Code coverage measures how much of your code is executed by tests. While 100% coverage is rarely practical, enforcing a threshold (e.g., 80%) in CI prevents PRs from dropping coverage.

**In Go:**
```bash
go test -coverprofile=coverage.out ./...
go tool cover -html=coverage.out # View in browser
go tool cover -func=coverage.out # View in terminal
```

**In Python (using pytest-cov):**
```bash
pip install pytest-cov
pytest --cov=my_app --cov-report=xml --cov-report=term
```

**CI Integration (GitHub Actions example):**
```yaml
      - name: Run Python Tests and Coverage
        run: |
          pytest --junitxml=junit.xml --cov=src --cov-fail-under=80
```
*Note: We generate `junit.xml` to integrate test results directly into CI UI interfaces.*

## ⚡ Test Parallelism

As your test suite grows, it slows down. CI pipelines should run tests in parallel.

- **Go**: Use `t.Parallel()` inside your tests.
- **Python**: Use `pytest-xdist`: `pytest -n auto` (uses all available CPU cores).
- **CI Level**: Split tests into different jobs (e.g., Run Unit tests and Integration tests simultaneously).

## 🛡️ Flaky Tests

Flaky tests pass sometimes and fail sometimes. They destroy developer trust in CI.
**Causes:** Race conditions, time/timezone dependencies, reliance on shared state (DBs), or network calls.
**Solution:**
1. **Quarantine:** Immediately skip flaky tests (e.g., `@pytest.mark.skip` or `t.Skip()`) and open a ticket to fix them.
2. **Fix the Root Cause:** Use mocks for network calls, isolate DB state, or use Go's race detector `go test -race`.
3. **Retries:** As a last resort, retry failing tests automatically (e.g., `pytest-rerunfailures`).

## 📈 Advanced Testing Strategies

* **Integration Testing**: Use tools like `Testcontainers` (available in both Go and Python) to spin up real Docker containers (like PostgreSQL) during tests instead of mocking.
* **Contract Testing**: Ensures that two separate microservices agree on what API requests/responses look like. (e.g., using Pact).
* **Performance/Load Testing**: Running tools like `k6` or `Locust` in the CI pipeline to ensure a PR doesn't degrade system performance.
* **Mutation Testing**: A tool modifies (mutates) your code (e.g., changes `+` to `-`). If your tests still pass, your tests are weak. It tests the quality of your tests.

## 💡 Best Practices (Do/Don't)
- **DO** write fast, isolated unit tests.
- **DON'T** rely on external network calls in unit tests; use mocks.
- **DO** fail the CI pipeline if code coverage drops below a threshold.
- **DON'T** ignore flaky tests. Fix them or remove them.
- **DO** output test results in standard formats (JUnit XML) for CI tools to parse.

## 🔗 How This Connects
- **Previous**: [04-Build-Automation](../04-Build-Automation/README.md) – Once your code builds successfully, it must be tested before being packaged.
- **Next**: [06-Continuous-Delivery-and-Deployment](../06-Continuous-Delivery-and-Deployment/README.md) – Only code that passes all automated tests is eligible for automatic deployment.

## 📝 Chapter Summary

| Concept | Go Tooling | Python Tooling | CI/CD Goal |
|---------|------------|----------------|------------|
| Unit Testing | `testing` package | `pytest` | Fast feedback on logic. |
| Coverage | `go test -cover` | `pytest-cov` | Enforce test quality thresholds. |
| Parallelism | `t.Parallel()` | `pytest-xdist` | Reduce CI run time. |
| Mocks | Interfaces | `unittest.mock` | Isolate external dependencies. |
| E2E/Integration | `Testcontainers`, `k6` | `Testcontainers`, `Selenium` | Ensure components work together. |

## ➡️ What's Next
Proceed to the exercises to get hands-on experience writing Go and Python tests and integrating them with coverage reports.
