# Exercise 03: Build Matrix and Caching 🟡

## 🎯 Objective
Extend a CI pipeline with a build matrix (multiple Python versions) and dependency caching to see the speed improvement.

## 📋 Prerequisites
- Completed Exercise 02 (Python CI pipeline)

## 📝 Instructions

### Task 1: Add a Build Matrix

Modify your CI pipeline to test across Python 3.10, 3.11, and 3.12. All three versions must pass for the build to be green.

### Task 2: Add Dependency Caching

Add pip caching so that dependencies are not re-downloaded on every run. Use the `actions/setup-python` built-in cache or `actions/cache`.

### Task 3: Add a Linting Stage

Add a separate job that runs BEFORE tests:
1. Install `flake8` 
2. Run `flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics`
3. The test job should only run if linting passes

### Task 4: Add Timing

Add a step that prints the total time taken for the install step. Compare times with and without cache.

### Task 5: Measure the Impact

Run the pipeline twice and note:
1. First run time (no cache)
2. Second run time (with cache)
3. Time saved

## ✅ Expected Output / Solution

```yaml
name: Python CI with Matrix & Caching

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
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - run: pip install flake8
      - name: Run flake8
        run: |
          flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
          flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

  test:
    name: 🧪 Test (Python ${{ matrix.python-version }})
    needs: lint
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ['3.10', '3.11', '3.12']
      fail-fast: false
    
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python ${{ matrix.python-version }}
        uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'pip'    # Built-in pip caching!

      - name: Install dependencies (timed)
        run: |
          START=$(date +%s)
          pip install -r requirements.txt
          END=$(date +%s)
          echo "⏱️ Install took $((END - START)) seconds"

      - name: Run tests
        run: pytest -v --tb=short
```

## 🧠 Key Takeaway
Build matrices catch version-specific bugs before your users do. Caching can cut build times in half. Both are essential for a production-quality CI pipeline.
