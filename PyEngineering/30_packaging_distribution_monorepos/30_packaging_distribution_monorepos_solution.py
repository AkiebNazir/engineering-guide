"""
Topic 30: Packaging, Distribution & Monorepos

================================================================================
SOLUTION & WALKTHROUGH
================================================================================
"""

import sys
if sys.version_info >= (3, 11):
    import tomllib
else:
    # If running on <3.11, requires `pip install tomli`
    try:
        import tomli as tomllib
    except ImportError:
        print("Please install tomli: pip install tomli")
        sys.exit(1)

# ============================================================================
# 1. pyproject.toml configuration
# ============================================================================
# PEP 518 defines [build-system]
# PEP 621 defines [project]
PYPROJECT_TOML_CONTENT = \"\"\"
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "my-awesome-tool"
version = "0.1.0"
description = "A great CLI tool"
authors = [
  { name="Senior Engineer", email="senior@example.com" },
]
dependencies = [
  "requests>=2.30.0",
]

# This creates an executable named `awesome-cli` in the user's PATH
# when they pip install this package.
[project.scripts]
awesome-cli = "my_module:main"
\"\"\"

# ============================================================================
# 2. Parsing and Verification
# ============================================================================
def verify_packaging(toml_string: str) -> bool:
    try:
        # tomllib parses a TOML string into a Python dictionary
        data = tomllib.loads(toml_string)
        
        # Verify Build System
        build_backend = data.get("build-system", {}).get("build-backend")
        if build_backend != "hatchling.build":
            print("❌ Invalid build backend")
            return False
            
        # Verify Project Name
        project_name = data.get("project", {}).get("name")
        if project_name != "my-awesome-tool":
            print(f"❌ Expected project name 'my-awesome-tool', got '{project_name}'")
            return False
            
        # Verify Entry Point
        scripts = data.get("project", {}).get("scripts", {})
        cli_command = scripts.get("awesome-cli")
        if cli_command != "my_module:main":
            print(f"❌ Expected awesome-cli to point to 'my_module:main', got '{cli_command}'")
            return False
            
        print("✅ pyproject.toml is perfectly configured!")
        return True
        
    except tomllib.TOMLDecodeError as e:
        print(f"❌ Failed to parse TOML: {e}")
        return False

if __name__ == "__main__":
    verify_packaging(PYPROJECT_TOML_CONTENT)
