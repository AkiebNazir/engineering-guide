# Exercise 3: Matrix Builds in GitHub Actions 🟡

## 🎯 Objective
Use a Matrix Strategy in GitHub Actions to test a Python application across multiple Operating Systems and Python versions concurrently.

## 📋 Prerequisites
- Completed Exercise 1.
- Understanding of JSON/YAML arrays.

## 📝 Instructions

1. **The Scenario**
   You are building an open-source Python library that does path manipulation. Because Windows, Mac, and Linux handle file paths differently, you *must* test your code on all three OSes, and you want to ensure it works on Python 3.10, 3.11, and 3.12.

2. **Create the Python Code**
   Create a file called `path_tool.py`:
   ```python
   # path_tool.py
   import os

   def get_current_path_length():
       return len(os.getcwd())
   ```

   Create `test_path_tool.py`:
   ```python
   # test_path_tool.py
   from path_tool import get_current_path_length

   def test_length():
       assert get_current_path_length() > 0
   ```

3. **Define the Matrix Workflow**
   Create `.github/workflows/matrix-test.yml`:

   ```yaml
   name: Cross-Platform Matrix Test
   
   on:
     push:
       branches: [ "main" ]

   jobs:
     test:
       name: Test on ${{ matrix.os }} with Python ${{ matrix.python-version }}
       
       # 1. Use the matrix os variable for the runner
       runs-on: ${{ matrix.os }}
       
       # 2. Define the strategy matrix
       strategy:
         # fail-fast: false ensures that if Windows fails, Ubuntu and Mac still finish running
         fail-fast: false
         matrix:
           os: [ubuntu-latest, windows-latest, macos-latest]
           python-version: ["3.10", "3.11", "3.12"]

       steps:
         - uses: actions/checkout@v4

         # 3. Use the matrix python-version variable
         - name: Set up Python ${{ matrix.python-version }}
           uses: actions/setup-python@v5
           with:
             python-version: ${{ matrix.python-version }}

         - name: Install dependencies
           run: |
             python -m pip install --upgrade pip
             pip install pytest

         - name: Run Tests
           run: pytest test_path_tool.py
   ```

## 💡 Hints
- The `strategy.matrix` block acts as a Cartesian product. `3 OSes * 3 Python versions = 9 jobs` running in parallel!
- You can access matrix variables dynamically using `${{ matrix.YOUR_VARIABLE }}`.
- Setting `fail-fast: false` is crucial for open-source libraries. If you leave it out (default is `true`), GitHub will cancel all other running matrix jobs the moment one of them fails.

## ✅ Expected Output / Solution
When you commit this to GitHub, the Actions UI will instantly spin up 9 separate jobs under the `test` umbrella:
- `Test on ubuntu-latest with Python 3.10`
- `Test on ubuntu-latest with Python 3.11`
- ...
- `Test on windows-latest with Python 3.12`

All 9 environments will checkout the code, install `pytest`, and assert that the path length logic works on their respective filesystem.

## 🧠 Key Takeaway
Matrix strategies save you from writing hundreds of lines of repetitive YAML. With just a few lines in the `strategy` block, you can validate your application across a massive combination of hardware and software configurations.
