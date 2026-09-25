# Exercise 1: Basic GitHub Actions Workflow 🟢

## 🎯 Objective
Create a simple GitHub Actions workflow that automatically lints and tests a Python script whenever code is pushed to the repository.

## 📋 Prerequisites
- Basic understanding of YAML syntax.
- Understanding of GitHub repository structure (`.github/workflows/`).

## 📝 Instructions

1. **Create the Project Files**
   Imagine you have a simple Python script. Create a scratch file called `calculator.py`.

   ```python
   # calculator.py
   def add(a, b):
       return a + b

   def subtract(a, b):
       return a - b
   ```

2. **Create the Test File**
   Create a test file `test_calculator.py`.

   ```python
   # test_calculator.py
   import unittest
   from calculator import add, subtract

   class TestCalculator(unittest.TestCase):
       def test_add(self):
           self.assertEqual(add(2, 3), 5)

       def test_subtract(self):
           self.assertEqual(subtract(5, 3), 2)

   if __name__ == '__main__':
       unittest.main()
   ```

3. **Define the GitHub Actions Workflow**
   Create a directory `.github/workflows` and inside it, create a file named `python-ci.yml`.

   Write the following workflow configuration from scratch:

   ```yaml
   # .github/workflows/python-ci.yml
   name: Python CI

   # 1. Define the events that trigger the workflow
   on:
     push:
       branches: [ "main" ]
     pull_request:
       branches: [ "main" ]

   # 2. Define the jobs
   jobs:
     build-and-test:
       # 3. Specify the runner environment
       runs-on: ubuntu-latest

       # 4. Define the sequential steps
       steps:
         # Step A: Check out the repository code
         - name: Checkout Code
           uses: actions/checkout@v4

         # Step B: Set up the Python environment
         - name: Set up Python 3.11
           uses: actions/setup-python@v5
           with:
             python-version: "3.11"
             cache: 'pip'

         # Step C: Install dependencies (flake8 for linting)
         - name: Install Dependencies
           run: |
             python -m pip install --upgrade pip
             pip install flake8

         # Step D: Lint the code
         - name: Lint with flake8
           run: |
             # stop the build if there are Python syntax errors or undefined names
             flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
             # exit-zero treats all errors as warnings
             flake8 . --count --exit-zero --max-complexity=10 --max-line-length=127 --statistics

         # Step E: Run the unit tests
         - name: Run Tests
           run: |
             python -m unittest test_calculator.py
   ```

## 💡 Hints
- The `on:` block determines *when* the pipeline runs. We restrict it to the `main` branch to save resources.
- `uses: actions/checkout@v4` is crucial; without it, the runner has an empty directory!
- The pipe `|` character in YAML allows you to write multi-line shell scripts.

## ✅ Expected Output / Solution
If you were to push this to GitHub, the Actions tab would show a successful run labeled "Python CI". The console output would look like this:

```text
Run actions/checkout@v4
Run actions/setup-python@v5
Run python -m pip install --upgrade pip
Run flake8 . --count ...
Run python -m unittest test_calculator.py
..
----------------------------------------------------------------------
Ran 2 tests in 0.001s
OK
```

## 🧠 Key Takeaway
GitHub Actions workflows are straightforward sequence of steps. By leveraging pre-built marketplace actions (`checkout` and `setup-python`), you avoid writing boilerplate code to configure the environment, allowing you to focus purely on your build and test commands.
