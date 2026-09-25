# Exercise 1: Pipeline Templates (Python) 🟢

## 🎯 Objective
Create a reusable pipeline template for Python applications to enforce a "Golden Path" across multiple repositories.

## 📋 Prerequisites
- Basic understanding of CI/CD configuration files (YAML).
- Python 3.10+ installed.

## 📝 Instructions

1. Create a directory structure simulating a central `.github` repository:
   ```bash
   mkdir -p central-repo/.github/workflows
   ```

2. Create the reusable template file `central-repo/.github/workflows/python-golden-path.yml`:
   ```yaml
   name: Python Golden Path
   
   on:
     workflow_call:
       inputs:
         python-version:
           required: true
           type: string
           default: "3.10"
         run-security-scan:
           required: false
           type: boolean
           default: true
   
   jobs:
     build-test-scan:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
         
         - name: Setup Python
           uses: actions/setup-python@v5
           with:
             python-version: ${{ inputs.python-version }}
             cache: 'pip'
             
         - name: Install Dependencies
           run: |
             python -m pip install --upgrade pip
             pip install -r requirements.txt
             
         - name: Run Tests
           run: pytest
           
         - name: Security Scan (Bandit)
           if: ${{ inputs.run-security-scan == true }}
           run: |
             pip install bandit
             bandit -r .
   ```

3. Create a simulated consumer service workflow `consumer-service/.github/workflows/ci.yml`:
   ```yaml
   name: CI
   
   on:
     push:
       branches: [ main ]
   
   jobs:
     call-golden-path:
       uses: central-repo/.github/workflows/python-golden-path.yml@main
       with:
         python-version: "3.11"
         run-security-scan: true
   ```

## 💡 Hints
- `workflow_call` is the trigger that allows a GitHub Actions workflow to be called by another workflow.
- Inputs allow you to parameterize the reusable workflow.

## ✅ Expected Output / Solution
The consumer service now inherits the entire build, test, and scan process from the centralized template. If the platform team updates the template (e.g., to upgrade the caching mechanism), all consumer services get the update automatically.

## 🧠 Key Takeaway
Pipeline templates are the foundation of Platform Engineering. They reduce duplication, enforce security policies, and improve the developer experience by abstracting CI/CD complexity.
