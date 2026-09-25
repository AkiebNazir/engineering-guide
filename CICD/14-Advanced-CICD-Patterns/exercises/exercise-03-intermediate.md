# Chapter 14: Advanced CI/CD Patterns

<Exercise 3: Monorepo Path Triggering 🟡>
## 🎯 Objective
Write a Python script that simulates analyzing a Git commit to determine which microservices in a monorepo need to be rebuilt.

## 📋 Prerequisites
- Python 3.x

## 📝 Instructions
1. Imagine we have a list of changed files from a commit.
2. Determine which service directories were affected.
3. Output the list of services to rebuild.

## 💡 Hints
- Path manipulation using `os.path` or simple string splitting.

## ✅ Expected Output / Solution
```python
import sys

def get_affected_services(changed_files):
    affected = set()
    for file in changed_files:
        parts = file.split('/')
        if len(parts) > 1 and parts[0] == 'services':
            affected.add(parts[1])
        elif parts[0] == 'shared':
            # If shared library changes, rebuild everything (mocking this behavior)
            print("Shared library changed! Rebuilding all services.")
            return ["auth", "payments", "inventory"] 
    return list(affected)

if __name__ == '__main__':
    # Simulated input from git diff
    mock_changed_files = [
        "services/auth/main.go",
        "docs/readme.md",
        "services/payments/tests/test_api.py"
    ]
    
    services_to_build = get_affected_services(mock_changed_files)
    print(f"Services to trigger CI for: {services_to_build}")
```

## 🧠 Key Takeaway
Intelligent path analysis saves massive amounts of CI compute time in monorepos by only testing what actually changed.
</Exercise 3: Monorepo Path Triggering 🟡>
