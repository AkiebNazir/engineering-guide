"""
Topic 30: Packaging, Distribution & Monorepos

================================================================================
EXPLANATION
================================================================================

A senior Python engineer doesn't just write code; they distribute it safely.
Modern Python packaging revolves around `pyproject.toml` (PEP 518/PEP 621),
replacing `setup.py`.

In modern environments, we use tools like `Poetry`, `uv`, or `Hatch` to manage
dependencies and build distribution archives (Wheels and Source Distributions).

---
DIAGRAM: The Python Build Process
---
```mermaid
graph TD
    A[Source Code + pyproject.toml] -->|Build Backend e.g. setuptools, poetry-core| B{Build Type}
    B -->|sdist| C(Source Distribution .tar.gz)
    B -->|bdist_wheel| D(Wheel .whl)
    
    C -.-> E[pip install builds locally]
    D -.-> F[pip install extracts directly]
```

================================================================================
YOUR TASK
================================================================================
Since packaging isn't purely code, this exercise is slightly different.
1. Write a minimal `pyproject.toml` string that defines a package named
   `my-awesome-tool`, using `hatchling` as the build backend, and defines a
   console script (entry point) that points to `my_module:main`.
2. Write a function that parses this TOML string using the built-in `tomllib`
   (Python 3.11+) and verifies that the entry point is configured correctly.
"""

import sys
# Python 3.11+ includes tomllib
if sys.version_info >= (3, 11):
    import tomllib
else:
    import tomli as tomllib # Fallback for older versions

# ============================================================================
# 1. pyproject.toml configuration
# ============================================================================
# TODO: Write a valid pyproject.toml configuration.
# Requirements:
# - [build-system] requires = ["hatchling"] and build-backend = "hatchling.build"
# - [project] name = "my-awesome-tool", version = "0.1.0"
# - [project.scripts] awesome-cli = "my_module:main"
PYPROJECT_TOML_CONTENT = \"\"\"
# Your TOML here
\"\"\"

# ============================================================================
# 2. Parsing and Verification
# ============================================================================
def verify_packaging(toml_string: str) -> bool:
    """
    TODO: Parse the TOML string using tomllib.loads().
    Check if the project name is "my-awesome-tool" and the entry point
    "awesome-cli" exists and points to "my_module:main".
    Return True if valid, False otherwise.
    """
    pass

if __name__ == "__main__":
    print("Run the solution file to see the working implementation!")
