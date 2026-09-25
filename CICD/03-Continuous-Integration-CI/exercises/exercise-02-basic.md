# Exercise 02: Write Your First CI Pipeline 🟢

## 🎯 Objective
Write a basic GitHub Actions CI pipeline from scratch for a simple Python project.

## 📋 Prerequisites
- GitHub account
- Basic Python knowledge

## 📝 Instructions

### Step 1: Create the Python Project

Create these files in a new repository:

**`app.py`:**
```python
def celsius_to_fahrenheit(celsius):
    return (celsius * 9/5) + 32

def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5/9

def is_freezing(celsius):
    return celsius <= 0

if __name__ == "__main__":
    print(f"0°C = {celsius_to_fahrenheit(0)}°F")
    print(f"100°C = {celsius_to_fahrenheit(100)}°F")
    print(f"32°F = {fahrenheit_to_celsius(32)}°C")
```

**`test_app.py`:**
```python
from app import celsius_to_fahrenheit, fahrenheit_to_celsius, is_freezing

def test_celsius_to_fahrenheit():
    assert celsius_to_fahrenheit(0) == 32
    assert celsius_to_fahrenheit(100) == 212
    assert celsius_to_fahrenheit(-40) == -40

def test_fahrenheit_to_celsius():
    assert fahrenheit_to_celsius(32) == 0
    assert fahrenheit_to_celsius(212) == 100

def test_is_freezing():
    assert is_freezing(0) == True
    assert is_freezing(-5) == True
    assert is_freezing(10) == False
```

**`requirements.txt`:**
```
pytest==8.3.2
```

### Step 2: Write the CI Pipeline

Create `.github/workflows/ci.yml` that does the following:
1. Triggers on push to main and on pull requests
2. Runs on Ubuntu
3. Sets up Python 3.11
4. Installs dependencies from `requirements.txt`
5. Runs pytest

### Step 3: Push and Verify
Push to GitHub and check the Actions tab to see your pipeline run.

## 💡 Hints
- Use `actions/setup-python@v5` to set up Python
- Use `pip install -r requirements.txt` to install dependencies
- Use `pytest` to run tests

## ✅ Expected Output / Solution

```yaml
name: Python CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run tests
        run: pytest -v
```

Your Actions tab should show a green ✅ build.

## 🧠 Key Takeaway
A CI pipeline can be as simple as 20 lines of YAML. The key is starting simple and adding complexity as needed.
