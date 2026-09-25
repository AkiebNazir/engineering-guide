# Exercise 4: Python Dependency Management with Poetry 🟡

## 🎯 Objective
Migrate a standard Python setup to **Poetry** for reproducible builds and write a Makefile to interface with Poetry's commands.

## 📋 Prerequisites
- Completion of Exercise 2.
- Understanding the difference between `requirements.txt` and lock files.

## 📝 Instructions

1. Define a `pyproject.toml` file (Poetry's configuration) for a basic Python project. Include FastAPI as a dependency and `pytest` as a development dependency.
2. Write a `Makefile` that uses `poetry` commands instead of `pip`.
3. The Makefile should have targets to:
   - Install dependencies.
   - Run a development server (mocked).
   - Export the locked dependencies to a `requirements.txt` (useful for older CI systems or Dockerfiles).

## 💡 Hints
- Poetry manages its own virtual environments automatically. You run commands inside it using `poetry run <command>`.
- To export requirements: `poetry export -f requirements.txt --output requirements.txt`.

## ✅ Expected Output / Solution

**pyproject.toml**
```toml
[tool.poetry]
name = "api-service"
version = "0.1.0"
description = "A fast API service"
authors = ["Engineer <engineer@example.com>"]

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.103.0"
uvicorn = "^0.23.0"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.0"
```

**Makefile**
```makefile
.PHONY: setup update test run export clean

setup:
	@echo "Installing dependencies from lockfile..."
	poetry install

update:
	@echo "Updating dependencies and rewriting lockfile..."
	poetry update

test:
	@echo "Running tests via poetry..."
	poetry run pytest

run:
	@echo "Starting development server..."
	poetry run uvicorn src.main:app --reload

export:
	@echo "Exporting poetry.lock to requirements.txt for backward compatibility..."
	poetry export -f requirements.txt --output requirements.txt --without-hashes

clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .pytest_cache
```

## 🧠 Key Takeaway
Using `Poetry` and `pyproject.toml` gives Python developers the same robust dependency locking that Go and Node.js developers enjoy. Wrapping these tools in a `Makefile` keeps the CI/CD pipeline simple, as the CI runner just calls `make setup` and `make test`.
