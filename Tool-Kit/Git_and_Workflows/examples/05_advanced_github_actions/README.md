# Advanced: GitHub Actions CI/CD Pipeline
**Goal:** Understand how a production-grade CI/CD pipeline operates to automate testing and prevent broken code from being merged.
**Key Concepts:** [GitHub Actions (CI/CD)](../../Git_and_Workflows.md#8-github-actions-cicd)
**Prerequisites:** Basic understanding of GitHub Actions
**Step-by-Step Execution:**
1. Review the CI/CD workflow defined in `.github/workflows/ci.yml`.
2. Observe the steps: cloning the code, setting up the Node.js environment, installing dependencies, linting, testing, and conditionally building a Docker image.
   - *Expected behavior:* When a PR is opened against `main`, this workflow runs automatically on GitHub's servers to ensure all checks pass before merging.
**Try it yourself:** Fork this repository on GitHub and open a Pull Request modifying a file to trigger this Actions workflow on your own account.
**Teardown:** No cleanup required.
