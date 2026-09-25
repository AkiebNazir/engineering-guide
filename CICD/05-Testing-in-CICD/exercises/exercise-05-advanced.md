# Exercise 05: Code Coverage and CI Pipeline Integration 🔴

## 🎯 Objective
Simulate a CI environment by running tests, generating code coverage reports, and enforcing coverage thresholds for both a Go and a Python project.

## 📋 Prerequisites
- Go installed.
- Python installed.
- `pip install pytest pytest-cov`

## 📝 Instructions

You will create a unified script that acts like a CI pipeline step. If tests fail or coverage drops below 80%, the script should exit with a non-zero status code (causing the CI build to fail).

### Step 1: The Go Project setup
1. Create a directory `mathapp`.
2. Add `math.go`:
```go
package mathapp

func Multiply(a, b int) int {
	return a * b
}

func Subtract(a, b int) int {
	return a - b
}
```
3. Add `math_test.go`:
```go
package mathapp

import "testing"

func TestMultiply(t *testing.T) {
	if Multiply(2, 3) != 6 {
		t.Error("expected 6")
	}
}
// Notice: We intentionally do NOT write a test for Subtract to lower coverage!
```
4. Run `go mod init mathapp`.

### Step 2: The Python Project setup
1. Create a directory `pyapp`.
2. Add `app.py`:
```python
def is_even(n):
    if n % 2 == 0:
        return True
    else:
        return False

def is_odd(n):
    return not is_even(n)
```
3. Add `test_app.py`:
```python
from app import is_even

def test_is_even():
    assert is_even(2) == True
    assert is_even(3) == False
# Notice: We intentionally do NOT write a test for is_odd!
```

### Step 3: Create the CI Script
Create a shell script `ci-test.sh` in the root folder:

```bash
#!/bin/bash
set -e # Exit immediately if a command exits with a non-zero status

echo "🚀 Starting CI Pipeline Tests..."

# --- GO TESTING ---
echo "🐹 Running Go Tests with Coverage..."
cd mathapp

# Run tests and generate coverage profile
go test -coverprofile=coverage.out ./...

# Extract total coverage percentage
GO_COVERAGE=$(go tool cover -func=coverage.out | grep total | awk '{print substr($3, 1, length($3)-1)}')

echo "Go Coverage: $GO_COVERAGE%"

# Bash math to check if coverage is less than 80% (using awk for floating point)
if (( $(echo "$GO_COVERAGE < 80.0" | bc -l) )); then
  echo "❌ Go Code Coverage ($GO_COVERAGE%) is below the 80% threshold!"
  exit 1
else
  echo "✅ Go Coverage is acceptable."
fi

cd ..

# --- PYTHON TESTING ---
echo "🐍 Running Python Tests with Coverage..."
cd pyapp

# Run pytest with pytest-cov, failing if under 80%
# pytest-cov has built-in threshold failure support!
if pytest --cov=app --cov-fail-under=80 test_app.py; then
    echo "✅ Python Coverage is acceptable."
else
    echo "❌ Python Code Coverage failed the threshold check!"
    exit 1
fi

echo "🎉 All tests and coverage checks passed!"
```
*(Note: Ensure you have `bc` installed to run the floating point math in bash, or adjust the script for integer math).*

### Step 4: Run the CI Script
Make the script executable and run it:
```bash
chmod +x ci-test.sh
./ci-test.sh
```

### Step 5: Fix the build
The pipeline will fail because coverage is too low in both projects.
1. Go into `mathapp/math_test.go` and add a test for `Subtract`.
2. Go into `pyapp/test_app.py` and add a test for `is_odd`.
3. Rerun `./ci-test.sh`. It should now pass!

## 🧠 Key Takeaway
In a real CI pipeline (like GitHub Actions or GitLab CI), tools like `go test` and `pytest-cov` are used to automatically block PRs that reduce code quality. Setting a `--cov-fail-under` threshold is a standard enterprise practice to maintain a healthy codebase.
