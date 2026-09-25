# Continuous Integration (CI) Fundamentals

Continuous Integration is the practice of merging all developers' working copies to a shared mainline several times a day, backed by automated builds and tests to verify that the code isn't broken.

## 1. The CI Pipeline

When a developer opens a Pull Request (PR) or pushes to `main`, a CI runner intercepts the event and executes a defined pipeline.

```arch
%% caption: A typical CI pipeline fails fast; linting and unit tests run before slow integration tests and container builds.
route straight
node push "Git Push\n(Developer)" at 0,0 icon=client color=blue
node lint "1. Lint & Format" at 2,0 icon=check color=green
node unit "2. Unit Tests" at 0,1 icon=check color=green
node it "3. Integration Tests" at 2,1 icon=check color=amber
node build "4. Build & Push\n(Docker Image)" at 1,2 icon=package color=slate

push -> lint
lint -> unit
unit -> it
it -> build
```

### Fail Fast
Order your pipeline from fastest to slowest.
1. **Linters and Formatting**: Takes seconds. If the code is formatted incorrectly, fail the build immediately.
2. **Unit Tests**: Takes seconds to minutes. Tests individual functions without database dependencies.
3. **Integration / E2E Tests**: Takes minutes to hours. Spins up actual databases (e.g., using Testcontainers) and tests the system end-to-end.
4. **Security Scanning**: SAST (Static Application Security Testing) and dependency vulnerability scans.
5. **Build**: Only if all tests pass, compile the binary or build the Docker image and push it to a container registry.

## 2. GitHub Actions Deep Dive

GitHub Actions is a popular CI/CD tool because it requires no external infrastructure. You define workflows in YAML inside `.github/workflows/`.

```yaml
name: Backend CI

# Triggers
on:
  pull_request:
    branches: [ "main" ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    # Caching dependencies speeds up the pipeline dramatically
    - name: Cache Go modules
      uses: actions/cache@v3
      with:
        path: ~/go/pkg/mod
        key: ${{ runner.os }}-go-${{ hashFiles('**/go.sum') }}
        
    - name: Set up Go
      uses: actions/setup-go@v4
      with:
        go-version: '1.21'
        
    - name: Run Unit Tests
      run: go test -v -short ./...
```

### CI Anti-Patterns
- **Flaky Tests**: Tests that pass 90% of the time and fail 10% of the time due to race conditions or network timeouts. Developers will learn to ignore CI and just "click retry until it passes". Flaky tests must be deleted or fixed immediately.
- **Slow Pipelines**: If CI takes 45 minutes, developers will context-switch. Keep PR pipelines under 10 minutes.
- **"Works on my machine"**: CI must run in the exact same Docker container environment that runs in production.
