# Exercise 2: Basic Python Makefile 🟢

## 🎯 Objective
Create a standard `Makefile` for a Python project to automate environment setup, linting, and testing using `pip`.

## 📋 Prerequisites
- Basic knowledge of Python and `pip`.
- Familiarity with the structure of a `requirements.txt` file.

## 📝 Instructions

1. Imagine a Python project with source code in a `src/` folder and tests in a `tests/` folder.
2. You have a `requirements.txt` containing your dependencies.
3. Create a `Makefile` that sets up a virtual environment, installs dependencies, runs a linter (`flake8`), runs tests (`pytest`), and cleans up temporary files.

## 💡 Hints
- Creating a virtual environment: `python3 -m venv venv`
- Activating the virtual environment in a Makefile command requires running the activation and the command in the same shell execution (e.g., `. venv/bin/activate && pytest`).
- Python leaves behind `__pycache__` directories that should be removed during `clean`.

## ✅ Expected Output / Solution

```makefile
# Makefile

# Variables
VENV := venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: all setup lint test clean

all: lint test

setup:
	@echo "Creating virtual environment..."
	python3 -m venv $(VENV)
	@echo "Installing dependencies..."
	$(PIP) install -r requirements.txt
	$(PIP) install flake8 pytest

lint:
	@echo "Linting Python code..."
	$(VENV)/bin/flake8 src/ tests/

test:
	@echo "Running tests..."
	$(VENV)/bin/pytest tests/

clean:
	@echo "Cleaning up virtual environment and cache..."
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
```

**How it works:**
By referencing `$(VENV)/bin/python` or `$(VENV)/bin/pip` directly, we bypass the need to run `source venv/bin/activate` in the Makefile, which can sometimes cause issues due to Make spawning separate subshells for every line.

## 🧠 Key Takeaway
Even interpreted languages like Python benefit massively from a build automation script. It encapsulates the complexity of virtual environments and cache invalidation away from the developer.
