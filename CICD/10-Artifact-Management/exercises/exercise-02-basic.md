# Exercise 2: Python Package Building and Inspection 🟢

## 🎯 Objective
Learn how to define a Python package using modern standards (`pyproject.toml`), build it into a Wheel artifact, and inspect its metadata without relying on external CI servers.

## 📋 Prerequisites
* Python 3.8+ installed
* `pip` installed

## 📝 Instructions

### Step 1: Set up the project directory
Create a directory structure for your Python package.

```bash
mkdir -p my_python_pkg/src/my_pkg
cd my_python_pkg
touch src/my_pkg/__init__.py
```

### Step 2: Write a simple Python module
Create `src/my_pkg/hello.py`:

```python
def say_hello(name="World"):
    return f"Hello, {name}! This is a packaged artifact."
```

### Step 3: Define the Package Metadata
Create a `pyproject.toml` file in the root of `my_python_pkg`. This file replaces the legacy `setup.py` and tells build tools how to create the artifact.

```toml
[build-system]
requires = ["setuptools>=61.0"]
build-backend = "setuptools.build_meta"

[project]
name = "my-test-pkg"
version = "0.1.0"
authors = [
  { name="DevOps Student", email="student@example.com" },
]
description = "A simple package to demonstrate Python artifacts."
readme = "README.md"
requires-python = ">=3.8"
dependencies = []
```

Create a dummy `README.md`:
```markdown
# My Test Pkg
This is a test artifact.
```

### Step 4: Install the build tool
Install the official Python build module.
```bash
python3 -m pip install --upgrade build
```

### Step 5: Build the Artifact
Run the build command from the directory containing `pyproject.toml`.
```bash
python3 -m build
```

### Step 6: Inspect the Artifacts
Check the `dist/` directory. You will see two files:
1. A `.tar.gz` file (Source Distribution / sdist)
2. A `.whl` file (Wheel / Built Distribution)

Let's inspect the Wheel artifact (which is just a fancy ZIP file).
```bash
unzip -l dist/my_test_pkg-0.1.0-py3-none-any.whl
```

## 💡 Hints
* A Wheel (`.whl`) is a pre-built artifact. When someone runs `pip install`, downloading a Wheel is much faster than an `sdist` because it doesn't need to be compiled on the user's machine.
* The `py3-none-any` suffix means: Python 3, no specific ABI, any OS platform.

## ✅ Expected Output
```text
$ ls dist/
my_test_pkg-0.1.0-py3-none-any.whl  my-test-pkg-0.1.0.tar.gz

$ unzip -l dist/my_test_pkg-0.1.0-py3-none-any.whl
Archive:  dist/my_test_pkg-0.1.0-py3-none-any.whl
  Length      Date    Time    Name
---------  ---------- -----   ----
       75  ...        ...     my_pkg/hello.py
... (metadata files like METADATA, WHEEL)
```

## 🧠 Key Takeaway
You defined a software component using standard metadata and built it into an immutable artifact (a Wheel). In a real CI/CD pipeline, this `.whl` file is what gets pushed to PyPI or AWS CodeArtifact for others to use.
