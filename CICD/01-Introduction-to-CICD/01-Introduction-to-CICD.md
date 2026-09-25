# 1. Overview & Purpose

## What is it?
Continuous Integration (CI) and Continuous Deployment/Delivery (CD) are practices that automate the building, testing, and deployment of software. CI focuses on automatically integrating code changes from multiple contributors into a single software project. CD focuses on automatically delivering or deploying these changes to different environments like staging or production.

## Why does it exist?
Before CI/CD, engineers manually merged code, built artifacts, tested them, and deployed them. This was error-prone, slow, and led to "integration hell" where features worked locally but failed when merged. CI/CD exists to automate this, ensuring fast, reliable, and consistent software delivery.

## What problem does it solve?
*   **Integration Hell**: Long-lived feature branches are hard to merge.
*   **Manual Errors**: Humans make mistakes when deploying.
*   **Slow Feedback Loop**: Finding out a bug days after writing code is expensive.
*   **Inconsistent Environments**: "It works on my machine" syndrome.

## Where is it used?
It is used in almost all modern software engineering teams, from startups to enterprises. Any project that has multiple developers, requires testing, or is deployed to a server will use CI/CD.

## Where does it fit in backend/software engineering?
It acts as the bridge between writing code (development) and running code (operations). It is the backbone of the DevOps culture.

---

# 2. Prerequisites

*   **Version Control (Git)**: Understanding repositories, commits, branches, and pull requests.
*   **Command Line Basics**: Ability to navigate and run basic commands (e.g., `make`, `go build`, `python test.py`).
*   **Basic Testing**: Knowing what a unit test is.

---

# 3. Complete Theory

## Major Concepts
*   **Continuous Integration (CI)**: The practice of merging all developers' working copies to a shared mainline several times a day. Every push triggers an automated build and test sequence.
*   **Continuous Delivery (CD)**: The practice of keeping the codebase in a state where it can be deployed to production at any time. The deployment itself might require a manual click (approval).
*   **Continuous Deployment (CD)**: The practice where every change that passes the automated tests is automatically deployed to production without human intervention.
*   **Pipeline**: A set of automated steps defined in a sequence. Typically: `Lint -> Build -> Test -> Deploy`.
*   **Runner / Agent**: A worker machine that actually executes the CI/CD pipeline jobs (e.g., GitHub Actions Runner, GitLab Runner).
*   **Artifacts**: The output of a build process (e.g., a compiled binary, a Docker image, a tarball) that can be stored and deployed later.

---

# 4. Theory + Example

**Concept**: CI Pipeline.
A CI pipeline automatically runs tests when you push code.
**Example**:
If you push a Python file with a syntax error, the CI pipeline will run `pytest` (or `flake8`), fail, and block the Pull Request from being merged.

```yaml
# Simple GitHub Actions example
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Run Tests
        run: python -m pytest
```

---

# 5. Visual Explanation

```arch
node a "Dev Pushes Code" at 0,0 icon=user color=slate
node b "CI Server" at 1,0 icon=server color=blue
node c "Linting" at 2,0 shape=card color=amber
node d "Unit Tests" at 3,0 shape=card color=amber
node e "Integration Tests" at 3,1 shape=card color=amber
node f "Build Artifact" at 2,1 icon=doc color=purple
node g "CD Server" at 1,1 icon=server color=blue
node h "Deploy to Staging" at 0,1 icon=gateway color=teal
node i "End-to-End Tests" at 0,2 shape=card color=amber
node j "Deploy / Approval" at 1,2 shape=card color=red
a -> b -> c -> d
d -> e
e -> f -> g -> h
h -> i
i -> j
```

*Explanation*: 
1. The developer pushes code to GitHub/GitLab.
2. The CI server triggers the pipeline. It checks code style (Lint), runs small tests (Unit), and larger tests (Integration).
3. If successful, it builds the application into an Artifact.
4. The CD server takes over, deploying the artifact to a safe Staging environment.
5. After verifying in Staging, it deploys to Production.

---

# 6. How It Works Internally

1.  **Webhooks**: When you push to a Git repository, the Git provider (like GitHub) sends an HTTP POST request (a Webhook) to the CI/CD server (like Jenkins, or GitHub's own Actions backend).
2.  **Job Queuing**: The CI server receives the webhook, looks at the repository's CI configuration file (e.g., `.github/workflows/main.yml`), and creates a Job. This job is placed in a queue.
3.  **Runner Assignment**: A runner (a VM or container) constantly polls the CI server for jobs. It picks up the job.
4.  **Execution**: The runner clones the repository, sets up the environment, and executes the bash commands specified in the configuration file step-by-step.
5.  **Status Reporting**: After each step, the runner reports the success/failure and logs back to the CI server, which updates the UI on the Pull Request.

---

# 7. Real-World Engineering Usage

In real backend systems, CI/CD is used to:
*   Ensure every microservice is tested independently.
*   Build Docker images and push them to a container registry (like ECR, GCR).
*   Run database migration scripts automatically on staging/production.
*   Deploy infrastructure changes using Terraform (Infrastructure as Code) via pipelines.

**Trade-offs**: 
*   Maintaining CI/CD pipelines requires dedicated engineering effort.
*   Slow pipelines can frustrate developers. Balancing exhaustive testing vs. speed is a constant challenge.

---

# 8. Failure & Debugging

**Common Failure Modes**:
*   **Flaky Tests**: Tests that pass sometimes and fail sometimes due to timing issues or shared state.
*   **Environment Mismatch**: The CI runner has a different version of a library than the developer's local machine.
*   **Timeout**: A job takes too long and the CI system kills it.
*   **Secret Issues**: Missing or expired API keys in the CI environment variables.

**Debugging**:
1.  **Read the Logs**: The first step is always to look at the CI output logs to see exactly which command failed.
2.  **Reproduce Locally**: Try to run the exact command that failed locally (e.g., `make test-integration`).
3.  **SSH into Runner**: Some CI systems (like CircleCI, GitHub Actions via tmate) allow you to SSH into the runner container to debug the state.

---

# 9. Production Concerns

*   **Reliability**: Ensure the CI/CD system itself is highly available. A broken CI blocks all deployments.
*   **Security**: Limit who can trigger deployments. Protect secrets (API keys, database passwords) used in pipelines. Avoid running untrusted code on privileged runners.
*   **Performance**: Cache dependencies (like `node_modules` or `go mod`) to speed up builds. Parallize test suites.
*   **Observability**: Track deployment frequency, lead time for changes, and pipeline failure rates (DORA metrics).
*   **Failure Recovery**: Ensure you have a "Rollback" mechanism. If a deployment fails or causes an incident, you should be able to instantly redeploy the previous artifact.

---

# 10. Practical Projects — Exactly 5 in Go

Here are 5 progressively difficult Go projects focusing on CI/CD.

### Go Project 1: Basic Go App with CI (Testing)
**Problem**: Set up automated tests for a simple math function.
**Code**:
```go
// math.go
package main

func Add(a, b int) int {
	return a + b
}

// math_test.go
package main
import "testing"

func TestAdd(t *testing.T) {
	if Add(1, 2) != 3 {
		t.Error("Expected 1 + 2 to equal 3")
	}
}
```
**CI Config (`.github/workflows/go-p1.yml`)**:
```yaml
name: Go P1
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-go@v4
      with:
        go-version: '1.20'
    - run: go test ./...
```

### Go Project 2: Linting and Building
**Problem**: Add linting (`golangci-lint`) and build an artifact for a basic web server.
**Code**: A simple `main.go` starting an HTTP server.
**CI Config**: Runs `golangci-lint run`, then `go build -o server main.go`, and uploads `server` as an artifact.

### Go Project 3: Dockerizing and Pushing
**Problem**: Build a Docker image of the Go API and push to DockerHub.
**CI Config**: Logs into DockerHub using Secrets, builds `Dockerfile`, and pushes `my-go-api:latest`.

### Go Project 4: Multi-Service Testing
**Problem**: An API that talks to a Postgres DB. CI must spin up Postgres to run integration tests.
**CI Config**: Uses GitHub Actions `services` to start a Postgres container, waits for it, runs integration tests connecting to it.

### Go Project 5: Production Deployment via CD
**Problem**: Deploy the Dockerized Go API to a remote server via SSH automatically on merge to `main`.
**CI Config**: After testing and pushing to DockerHub, uses an SSH action to connect to a production VM, pull the new image, and restart the service. Includes rollback instructions if the healthcheck fails.

---

# 11. Practical Projects — Exactly 5 in Python

### Python Project 1: Basic Python App with Pytest
**Problem**: Set up automated tests for a basic string manipulation module.
**Code**:
```python
# utils.py
def reverse_string(s):
    return s[::-1]

# test_utils.py
from utils import reverse_string
def test_reverse():
    assert reverse_string("abc") == "cba"
```
**CI Config (`.github/workflows/py-p1.yml`)**:
```yaml
name: Py P1
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.10'
    - run: pip install pytest
    - run: pytest
```

### Python Project 2: Linting and Code Formatting
**Problem**: Enforce `black` formatting and `flake8` linting for a Flask app.
**CI Config**: Pipeline fails if `black --check .` or `flake8 .` fails, ensuring code quality before tests run.

### Python Project 3: Tox and Multiple Python Versions
**Problem**: Test a Python library against Python 3.8, 3.9, and 3.10.
**CI Config**: Uses a build matrix in GitHub Actions to run jobs in parallel for each Python version.

### Python Project 4: Database Integration Testing
**Problem**: A FastAPI app using SQLAlchemy and Redis.
**CI Config**: Uses Service containers to spin up Redis and Postgres in CI, sets environment variables, and runs pytest integration tests against them.

### Python Project 5: Automated PyPI Publish
**Problem**: A Python package that is automatically published to PyPI on a new GitHub Release.
**CI Config**: Triggers on `release`, builds wheels (`python -m build`), and uses Twine to upload to PyPI using a secret API token.

---

# 12. Project Requirements
*(Applied implicitly to the project descriptions above, providing code, tests, CI setup, and explanations).*

---

# 13. Progressive Difficulty
The path follows: Core Testing Mechanism -> Code Quality/Linting -> Artifact Generation (Docker/Matrix) -> Multi-component Integration (Databases) -> Production Deployment/Publishing.

---

# 14. Interview Preparation

*   **Fundamental Questions**:
    *   What is the difference between Continuous Delivery and Continuous Deployment? *(Delivery means ready to deploy but needs a manual click. Deployment is fully automated into production).*
*   **Practical Questions**:
    *   How do you speed up a slow CI pipeline? *(Caching dependencies, parallelizing test execution, splitting unit and integration tests).*
*   **Debugging Questions**:
    *   A test is flaky in CI but works locally. Why? *(Timing differences, network latency, timezone differences, lack of isolation between tests in CI).*
*   **Design/Trade-off Questions**:
    *   Should you run End-to-End tests on every commit? *(No, they are too slow and brittle. Run them nightly or only on Pull Requests to main).*
*   **System-Design Questions**:
    *   Design a CI/CD system like GitHub Actions. *(Focus on Webhooks -> Queue -> Fleet of Runners -> Status Updates -> Log Storage).*

---

# 15. Final Summary

*   **Key Mental Models**: CI is the safety net catching bugs before merge. CD is the conveyor belt moving code to users.
*   **Important Terminology**: Pipeline, Runner/Agent, Artifact, Webhook, Flaky Test.
*   **Cheat Sheet**:
    *   `Lint`: Is the code pretty?
    *   `Build`: Does the code compile?
    *   `Test`: Does the code work?
    *   `Deploy`: Put the code on the server.
*   **Common Mistakes**: Putting secrets in code instead of CI variables, having no automated tests, ignoring flaky tests.
*   **Production Checklist**:
    *   Is main branch protected?
    *   Are secrets encrypted?
    *   Is there a deployment rollback mechanism?
*   **Interview Checklist**: Understand the full lifecycle from `git push` to user traffic.
