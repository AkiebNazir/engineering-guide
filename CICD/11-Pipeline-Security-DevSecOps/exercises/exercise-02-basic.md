# Exercise 2: Secrets Scanning with Gitleaks 🟢

## 🎯 Objective
Learn how to scan a repository for accidentally committed secrets using `gitleaks`.

## 📋 Prerequisites
- Git installed
- `gitleaks` installed (e.g., `brew install gitleaks` on Mac, or download the binary)

## 📝 Instructions

1. **Create a local git repository**
   ```bash
   mkdir secret-test
   cd secret-test
   git init
   ```

2. **Commit a simulated secret**
   Create a file `config.py`:
   ```python
   # config.py
   AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
   AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
   DB_PASSWORD = "super_secret_password_123"
   ```
   
   Commit it:
   ```bash
   git add config.py
   git commit -m "Add database configuration"
   ```

3. **Run Gitleaks**
   Run gitleaks to detect secrets in the git history:
   ```bash
   gitleaks detect -v
   ```

4. **Analyze the output**
   Gitleaks should find the AWS keys and fail with a non-zero exit code. This is how a CI pipeline knows to block the merge.

5. **Fix the issue**
   Remove the secrets and use environment variables instead:
   ```python
   # config.py
   import os
   
   AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
   AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")
   DB_PASSWORD = os.environ.get("DB_PASSWORD")
   ```
   
   Commit the fix:
   ```bash
   git add config.py
   git commit -m "Remove hardcoded secrets"
   ```

6. **The problem with Git history**
   Run `gitleaks detect -v` again. It will *still* fail! Why? Because the secret is still in the git history.
   
   *Note: In a real scenario, you MUST rotate the exposed AWS keys immediately.*

## 💡 Hints
- Even if you delete a file or remove a string in a new commit, it remains in Git's history forever unless you rewrite the history (e.g., using `git filter-repo` or `BFG Repo-Cleaner`).
- This is why running `gitleaks` as a pre-commit hook is highly recommended.

## ✅ Expected Output
```text
Finding:     AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
Secret:      AKIAIOSFODNN7EXAMPLE
RuleID:      aws-access-token
Entropy:     3.080537
File:        config.py
...
```

## 🧠 Key Takeaway
Never commit secrets. Secrets scanners look at the entire Git history, not just the current state of the files. If a secret is committed, consider it compromised and rotate it immediately.
