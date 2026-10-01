# Continuous Integration (CI) Fundamentals

Continuous Integration is the practice of merging every developer's work into one shared
mainline many times a day, with an automated build and test run proving each merge did
not break anything. This chapter starts from what problem CI solves and what the moving
parts are, then goes as deep as a senior interview goes: how a pipeline should be
ordered, how GitHub Actions actually executes a workflow, how merge queues keep `main`
green, how to make a slow pipeline fast, why flaky tests are an organisational problem and
not just a technical one, and how CI became one of the most attacked parts of the
software supply chain. Every later chapter in this module (delivery, deployment
strategies, GitOps, feature flags) assumes the output of this one: a tested, immutable
artifact built from a known commit.

## Foundations — What problem does CI solve, and what are its pieces?

### Integration hell

Picture five engineers each working on their own branch for three weeks. Every branch
compiles and passes its own tests. On merge day, they discover that Alice renamed a
function Bob now calls in twelve places, Carol changed a database column Dave's new query
reads, and the combined code fails in ways none of the branches did alone. The longer
branches live apart, the more they diverge, and the cost of merging grows faster than
the time spent apart: two changes that each touch a file can conflict, and the number of
pairs grows with the square of the number of changes. Teams in the 1990s scheduled whole
"integration phases" that took weeks. That is **integration hell**.

CI's answer is almost embarrassingly simple: **integrate so often that each integration is
small.** If everyone merges to `main` at least daily, the diff between your branch and
`main` is a few hours of work, conflicts are tiny, and when something breaks, the culprit
is one of a handful of recent commits. The practice was named in Extreme Programming in
the late 1990s and popularised by Martin Fowler's 2000 article *Continuous Integration*.

Merging often only helps if you find out quickly that a merge broke something. Nobody can
run the full test suite by hand thirty times a day, so the second half of CI is
automation: **every push triggers a machine that builds the code and runs the tests, and
reports the result back on the change before it merges.**

### The pieces and how they fit

| Piece | What it is | Example |
|---|---|---|
| Version control | The shared history everyone integrates into | Git, hosted on GitHub / GitLab / Bitbucket |
| Mainline / trunk | The one branch that is always meant to work | `main` |
| Change | A proposed set of commits, reviewed before merging | A pull request (PR) / merge request (MR) |
| Trigger | The event that starts CI | `push`, `pull_request`, `merge_group`, a schedule |
| CI system | The orchestrator that reads the pipeline definition and schedules work | GitHub Actions, GitLab CI, Jenkins, Buildkite, CircleCI |
| Pipeline / workflow | The declared graph of work, usually YAML in the repo | `.github/workflows/ci.yml` |
| Job / stage | A unit of work that runs on one machine | `lint`, `unit-test`, `build-image` |
| Step | One command or reusable action inside a job | `go test ./...` |
| Runner / agent | The (usually ephemeral) machine or container that executes a job | GitHub-hosted `ubuntu-latest`, a self-hosted Kubernetes pod |
| Cache | Saved dependencies or build outputs reused across runs | Go module cache, Docker layer cache |
| Artifact | The output worth keeping: a binary, a container image, a test report | `ghcr.io/acme/api@sha256:…` |
| Status check | The pass/fail result reported back onto the PR | "CI / unit-test — passed" |
| Branch protection / ruleset | The rule that says a PR can only merge if named checks passed | "Require `unit-test` and 1 approval" |

```arch
%% caption: A push triggers the CI system, which runs the workflow's jobs on runners and reports a status check back to the pull request.
grid 170x110
node dev "Developer" at 0,0 icon=developer sub="git push"
node host "Git host" at 1,0 icon=git sub="PR + branch rules"
node ci "CI orchestrator" at 2,0 icon=workflow sub="reads workflow YAML"
group run "Ephemeral runners" color=orange icon=container
node r1 "Lint job" at 1,1 in run icon=check
node r2 "Test job" at 2,1 in run icon=check
node r3 "Build job" at 3,1 in run icon=package
node cache "Cache" at 1,2 icon=cache sub="deps, layers"
node reg "Registry" at 3,2 icon=storage sub="image by digest"
dev -> host : "push"
host -> ci : "webhook event"
ci -> r1
ci -> r2
ci -> r3
r1 .. cache
r3 -> reg : "push image"
ci ..> host : "status checks"
```

### An everyday example

You fix a typo-level bug in a checkout service and open a PR. Within a few seconds a
webhook tells the CI system; within a minute a fresh virtual machine has cloned your
commit, restored the dependency cache and run the linter. Two minutes later the unit
tests pass; a parallel job spins up a throwaway Postgres container and runs integration
tests. The PR page shows green ticks, a reviewer approves, and the merge button unlocks.
Nobody ran anything by hand, and nobody merged code that had not been built and tested
exactly as it will be merged.

### CI, CD and CD: the vocabulary this module uses

- **Continuous Integration**: every change is merged to mainline frequently and verified
  by an automated build and test run. This chapter.
- **Continuous Delivery**: every change that passes CI produces an artifact that *could*
  be released to production at the push of a button. [Continuous Deployment (CD) and Delivery](02_cd_and_delivery.md).
- **Continuous Deployment**: every change that passes the pipeline *is* released to
  production automatically, with no human gate. Also [Continuous Deployment (CD) and Delivery](02_cd_and_delivery.md).

**Precision note:** running a CI server does not mean you practise CI. A team with
Jenkins that merges long-lived feature branches once a month is doing automated builds,
not continuous integration. The "continuous" part is the merge frequency.

## 1. The CI pipeline and why order matters

A pipeline is a directed graph of jobs. The design goal is **fast, trustworthy feedback**:
tell the author as early as possible that the change is broken, and never say "green"
when it is not.

```arch
%% caption: Cheap checks fan out in parallel first; slower integration tests and the image build only run once they pass, and the build publishes one immutable artifact.
grid 160x110
node push "Push / PR" at 1.5,0 shape=pill color=slate
node lint "Lint + format" at 0,1 icon=check sub="seconds"
node unit "Unit tests" at 1,1 icon=check sub="< 2 min"
node sast "SAST + deps scan" at 2,1 icon=shield sub="1-3 min"
node types "Typecheck / vet" at 3,1 icon=code sub="seconds"
node it "Integration tests" at 1,2 icon=db sub="real Postgres, 3-8 min"
node build "Build image" at 2,2 icon=package sub="tag = commit SHA"
node pub "Publish + attest" at 1.5,3 icon=storage sub="registry, SBOM"
push -> lint
push -> unit
push -> sast
push -> types
unit -> it
sast -> build
it -> pub
build -> pub
```

### Fail fast, but in parallel

Order work from cheapest-and-most-likely-to-fail to most expensive:

| Stage | Typical duration (≈) | Catches | Notes |
|---|---|---|---|
| Format + lint | 5–60 s | Style, unused imports, obvious bugs | `gofmt`, `ruff`, `eslint`, `golangci-lint` |
| Type check / compile | 10 s–2 min | Type errors, broken builds | `tsc --noEmit`, `mypy`, `go vet` |
| Unit tests | 30 s–5 min | Logic errors in isolated code | No network, no real DB, run in parallel |
| Static security (SAST) + dependency scan | 1–5 min | Known-vulnerable libraries, injection patterns, leaked secrets | CodeQL, Semgrep, `govulncheck`, `osv-scanner`, gitleaks |
| Integration tests | 2–15 min | Wrong SQL, broken serialisation, config mistakes | Real dependencies in containers (Testcontainers, service containers) |
| Build + push artifact | 1–10 min | Dockerfile errors, missing files | Tag by commit SHA, push once |
| End-to-end / smoke | 5–30 min | Whole-system regressions | Often after deploy to a test environment, see chapter 02 |

"Fail fast" does not mean "run strictly one after another". A pure sequence makes the
total time the *sum* of all stages. Independent checks (lint, unit tests, scanning) should
run as **parallel jobs**, and only genuinely dependent work (the build needs the code to
compile; publishing needs tests to have passed) should wait with `needs:`. The critical
path, the longest chain of dependent jobs, sets your feedback time.

**Precision note:** the owner's original outline ordered security scanning after
integration tests. In practice SAST and dependency scans do not depend on tests at all and
belong in the first parallel wave; the only thing that must wait for them is *publishing*.

### Two pipelines, not one

Most mature teams run two variants of the same workflow:

- **Pre-merge (PR) pipeline**: optimised for speed. Lint, unit tests, affected
  integration tests, a build that proves the image builds. Target: under ≈10 minutes,
  because a developer is waiting on it.
- **Post-merge (mainline) pipeline**: optimised for completeness and for producing the
  artifact. Full test suite, image build and push, SBOM and provenance, then hand-off to
  delivery. Slower suites (long E2E, fuzzing, performance tests) run here or nightly.

The DORA research programme (the *Accelerate* book and the yearly *State of DevOps*
reports) repeatedly finds that high-performing teams keep this feedback loop short;
Fowler's rule of thumb is the "ten-minute build".

## 2. GitHub Actions in depth

GitHub Actions is the most common CI system for projects hosted on GitHub. It is a good
one to learn in detail because its concepts (events, jobs, steps, runners, reusable
units) map onto every other CI system.

### The execution model

1. An **event** happens on the repository: `push`, `pull_request`, `merge_group`,
   `workflow_dispatch` (manual button), `schedule` (cron), `release`, and many more.
2. GitHub finds every file under `.github/workflows/*.yml` whose `on:` matches the
   event, filtered by branch and path.
3. Each matching **workflow** becomes a **workflow run**. Its **jobs** form a DAG through
   `needs:`; jobs without dependencies start in parallel.
4. Each job is queued for a **runner** matching `runs-on:`. A GitHub-hosted runner is a
   fresh VM per job, thrown away afterwards; self-hosted runners are your own machines
   (increasingly ephemeral pods via Actions Runner Controller on Kubernetes).
5. On the runner, the **steps** run in order in one workspace. A step is either a shell
   command (`run:`) or a reusable **action** (`uses: owner/repo@ref`), which is a
   JavaScript, Docker or composite unit someone published.
6. Each job reports a **check run** back to the commit; branch protection rules decide
   which checks must be green to merge.

Jobs do not share a filesystem. To pass files between jobs, upload them as artifacts
(`actions/upload-artifact`) or rebuild them; to pass small values, use job `outputs`.

### A realistic workflow

The owner's original snippet used `actions/checkout@v3`, `actions/cache@v3` and
`actions/setup-go@v4` with Go 1.21. Those major versions are deprecated (the v3 cache and
artifact actions stopped working against GitHub's new cache and artifact backends in
early 2025), and `setup-go` has cached the module and build caches on its own since v4,
so the separate cache step was redundant. Here is a current version that also shows the
things a real pipeline needs: least-privilege permissions, cancellation of superseded
runs, a merge-queue trigger, a service container for integration tests, and an image
tagged with the commit SHA.

```yaml
name: ci

on:
  pull_request:
    branches: [main]
  merge_group:            # required if main uses a merge queue (see section 3)
  push:
    branches: [main]

# Default the GITHUB_TOKEN to read-only; jobs ask for more only when they need it.
permissions:
  contents: read

# A new push to the same PR cancels the run for the old commit.
concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: ${{ github.event_name == 'pull_request' }}

jobs:
  lint:
    runs-on: ubuntu-latest
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod      # one source of truth for the Go version
      - name: gofmt
        run: test -z "$(gofmt -l .)" || (gofmt -l . && exit 1)
      - name: go vet
        run: go vet ./...

  unit-test:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-go@v5      # caches ~/go/pkg/mod and the build cache by go.sum
        with:
          go-version-file: go.mod
      - run: go test -race -short -count=1 ./...

  integration-test:
    needs: unit-test
    runs-on: ubuntu-latest
    timeout-minutes: 20
    services:
      postgres:
        image: postgres:17
        env:
          POSTGRES_PASSWORD: test
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U postgres"
          --health-interval 5s --health-timeout 5s --health-retries 10
    env:
      DATABASE_URL: postgres://postgres:test@localhost:5432/postgres?sslmode=disable
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-go@v5
        with:
          go-version-file: go.mod
      - run: go test -count=1 -run Integration ./...

  build-image:
    needs: [lint, integration-test]
    runs-on: ubuntu-latest
    timeout-minutes: 20
    permissions:
      contents: read
      packages: write                  # push to ghcr.io with GITHUB_TOKEN
    steps:
      - uses: actions/checkout@v5
      - uses: docker/setup-buildx-action@v3
      - uses: docker/login-action@v3
        if: github.event_name != 'pull_request'
        with:
          registry: ghcr.io
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}
      - uses: docker/build-push-action@v6
        with:
          context: .
          push: ${{ github.event_name != 'pull_request' }}   # PRs only prove it builds
          tags: ghcr.io/acme/checkout-api:${{ github.sha }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
```

Things worth being able to explain line by line in an interview:

- **`permissions: contents: read`** at the top: the automatically issued `GITHUB_TOKEN`
  otherwise may have write access to the repository. A compromised step can only do what
  the token allows.
- **`concurrency`**: without it, five quick pushes to a PR queue five full runs; with it,
  only the newest commit's run survives. It is not cancelled on `main`, where every
  commit should produce a result.
- **`timeout-minutes`**: the default job timeout is 6 hours. A hung test would otherwise
  burn a runner for that long.
- **Service containers**: `services:` starts Postgres next to the job, and the health
  options make the job wait until it accepts connections.
- **`needs:`** builds the DAG. `lint` and `unit-test` start together; the image build
  waits for both lint and integration tests.
- **Tag with `github.sha`**, never with `latest`: the tag names exactly which commit is
  inside the image. Chapter 02 goes further and deploys by image digest.
- **`cache-from/cache-to: type=gha`** stores BuildKit's layer cache in the Actions cache,
  so unchanged layers (base image, dependency download) are not rebuilt.
- **Version pins**: `@v5` is a moving tag the action's owner can repoint. Security-critical
  repositories pin third-party actions to a full commit SHA; see section 7.

### Matrix builds and reusable workflows

A **matrix** fans one job out over combinations, for example three OSes times two
language versions:

```yaml
jobs:
  test:
    strategy:
      fail-fast: false           # let every combination finish so you see all failures
      matrix:
        os: [ubuntu-latest, macos-latest, windows-latest]
        python: ["3.12", "3.13"]
    runs-on: ${{ matrix.os }}
    steps:
      - uses: actions/checkout@v5
      - uses: actions/setup-python@v5
        with:
          python-version: ${{ matrix.python }}
          cache: pip
      - run: pip install -r requirements.txt && pytest -q
```

A **reusable workflow** (`on: workflow_call`) lets a platform team publish one vetted
pipeline that dozens of repositories call with `uses: acme/ci-templates/.github/workflows/go.yml@v3`.
A **composite action** packages a sequence of steps. Both are how organisations stop
every team from copy-pasting a slightly different, slightly insecure pipeline.

### How other CI systems compare

| System | Where pipelines live | Execution | Typical fit |
|---|---|---|---|
| GitHub Actions | `.github/workflows/*.yml` | Hosted VMs or self-hosted runners | Repos on GitHub; large marketplace of actions |
| GitLab CI | `.gitlab-ci.yml` | Shared or self-managed GitLab Runners | GitLab users; strong built-in environments and registry |
| Jenkins | `Jenkinsfile` (Groovy) or UI jobs | Controller plus agents you operate | Legacy estates and highly custom on-prem needs; you own upgrades and plugins |
| Buildkite | `pipeline.yml`, can be generated dynamically | Hosted control plane, your agents | Large monorepos wanting their own compute |
| CircleCI | `.circleci/config.yml` | Hosted or self-hosted | Teams wanting managed CI independent of the Git host |
| Bazel / Buck2 + remote execution | `BUILD` files | Distributed build farm with a shared cache | Very large monorepos (Google's internal TAP/Blaze lineage) |

## 3. Trunk-based development, branch protection and merge queues

### Branching strategy decides whether you are doing CI at all

| Strategy | Branch lifetime | Integration frequency | When it fits |
|---|---|---|---|
| Trunk-based development | Hours to a day or two; small PRs into `main` | Many times per day | Most product teams practising CI/CD; incomplete work hidden behind flags (chapter 05) |
| GitHub flow | Short feature branch, PR, merge, deploy | Daily-ish | Similar to trunk-based, with a PR for every change |
| GitFlow | `develop`, `release/*`, `hotfix/*`, long feature branches | Weekly or per release | Versioned, shipped software with parallel supported releases; poor fit for continuous delivery |
| Release branches off trunk | Trunk-based plus a cut branch per release that only receives cherry-picked fixes | Trunk daily; release branch rarely | Mobile apps, on-prem products, anything with a release train |

The DORA research associates trunk-based development (few active branches, branches
living less than a day, no code freezes) with higher delivery performance. The enabling
trick is decoupling *merging* code from *releasing* it: unfinished features merge behind
a feature flag that is off. That is the subject of [Feature Flags and Rollbacks](05_feature_flags_and_rollbacks.md).

### Branch protection and required checks

Protecting `main` (GitHub branch protection rules or the newer **rulesets**) typically
requires: a PR for every change, N approving reviews, specific **required status checks**
to pass, the branch to be up to date with `main` (or a merge queue instead), signed
commits, and no force-pushes. Required checks are the enforcement point: CI results are
advisory until a rule makes them mandatory.

### The "green PR, red main" problem

Two PRs can each pass CI against the `main` they branched from, yet break when combined:
PR A renames a function, PR B adds a new call to the old name. Each PR is green; after
both merge, `main` does not compile. "Require branch to be up to date" fixes this by
forcing a rebase and re-run before every merge, but on a busy repository that becomes a
race where everyone rebases, re-runs, and loses to whoever merged first.

A **merge queue** (GitHub merge queue, GitLab merge trains, Bors, Mergify, Aviator; Google
and other large companies built their own) fixes it properly:

```arch
%% caption: A merge queue tests each PR on top of main plus every PR ahead of it, and only fast-forwards main to combinations that passed.
grid 170x110
node pa "PR A approved" at 0,0 icon=git
node pb "PR B approved" at 1,0 icon=git
node pc "PR C approved" at 2,0 icon=git
node q "Merge queue" at 1,1 icon=queue sub="ordered A, B, C"
node ta "main + A" at 0,2 icon=check sub="CI run 1"
node tb "main + A + B" at 1,2 icon=check sub="CI run 2"
node tc "main + A + B + C" at 2,2 icon=error color=red sub="CI run 3 fails"
node main "main" at 1,3 shape=pill color=green sub="advances to A + B"
pa -> q
pb -> q
pc -> q
q -> ta
q -> tb
q -> tc
ta -> main
tb -> main
tc ..> q : "C ejected"
```

The queue builds temporary branches (`main + A`, `main + A + B`, …), runs CI on each **in
parallel**, and fast-forwards `main` only to states that passed. If C's combination fails,
C is removed from the queue and the author is notified, while A and B still merge. In
GitHub Actions the workflow must listen for the **`merge_group`** event, otherwise the
queue waits forever for a check that never starts; that is the most common setup bug.

### Monorepos: build only what changed

In a monorepo, running every test for every change does not scale. Options, in increasing
order of precision:

1. **Path filters** (`on: pull_request: paths: ['services/billing/**']`): cheap, but a
   change in a shared library must also trigger its dependants, and path filters do not
   know the dependency graph.
2. **Affected-target tools** that read the dependency graph: Nx, Turborepo, Pants,
   `bazel query 'rdeps(//..., set(changed files))'`.
3. **Hermetic builds with content-addressed caching** (Bazel, Buck2, Pants): every action
   is keyed by the hash of its inputs, so an unchanged target is never rebuilt or retested
   anywhere in the organisation. Google's internal presubmit system works on this model.

## 4. Making CI fast

Slow CI is expensive in a way that is easy to miss: the cost is not runner minutes, it is
engineers context-switching while they wait, batching changes into bigger PRs to "save"
CI runs, and ignoring results. Treat pipeline time as a product metric with a p50 and p90.

| Technique | What it saves | How | Pitfall |
|---|---|---|---|
| Dependency cache | Re-downloading packages | `setup-*` action caching, `actions/cache` keyed on the lockfile hash | Key on the lockfile, not a date; a stale key restores the wrong deps |
| Build cache | Recompiling unchanged code | Go build cache, Gradle build cache, `ccache`, Bazel remote cache | Non-hermetic builds make cache hits wrong, not just slow |
| Docker layer cache | Rebuilding unchanged image layers | Order Dockerfile from least to most frequently changed; BuildKit `cache-from/to` (gha, registry) | `COPY . .` before installing deps invalidates everything on every commit |
| Parallel jobs | Wall-clock time | Split independent stages into jobs | Each job pays VM start and checkout, ≈20–60 s |
| Test sharding | Wall-clock time of one big suite | `pytest-xdist`, `jest --shard`, `go test` per package, split by recorded timings | Uneven shards: the slowest shard sets the time |
| Test impact analysis | Running unaffected tests | Dependency graph or coverage mapping picks tests touched by the diff | Must fall back to the full suite post-merge |
| Bigger or warm runners | CPU-bound compile | Larger hosted runners, self-hosted pools with warm caches | Cost; self-hosted security (section 7) |
| Skip work on superseded commits | Wasted runs | `concurrency: cancel-in-progress` | Do not cancel runs on `main` |

A Dockerfile ordered for caching, for a Go service:

```dockerfile
# syntax=docker/dockerfile:1
FROM golang:1.25 AS build
WORKDIR /src
# 1. Dependencies change rarely: copy only the module files and download first.
COPY go.mod go.sum ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
# 2. Source changes on every commit: this layer and below rebuild each time.
COPY . .
RUN --mount=type=cache,target=/go/pkg/mod \
    --mount=type=cache,target=/root/.cache/go-build \
    CGO_ENABLED=0 go build -trimpath -ldflags="-s -w" -o /out/api ./cmd/api

# 3. Minimal runtime image: no compiler, no shell, runs as non-root.
FROM gcr.io/distroless/static-debian12:nonroot
COPY --from=build /out/api /api
USER nonroot:nonroot
ENTRYPOINT ["/api"]
```

A multi-stage build keeps the toolchain out of the shipped image (smaller, fewer CVEs to
scan), and the `--mount=type=cache` lines keep Go's caches between builds on the same
builder. The Docker details are in [Docker and Containerization](../Tool-Kit/01_docker_and_containers.md).

## 5. Flaky tests

A **flaky test** passes and fails on the same code. It is the single biggest destroyer
of trust in CI. Google published that about 1.5% of all its test runs reported a flaky
result and almost 16% of its tests showed some flakiness (John Micco, *Flaky Tests at
Google and How We Mitigate Them*, 2016). At that scale a large change touching many tests
almost always sees at least one spurious failure.

### Why flakiness is worse than it looks

If a PR runs 200 tests and each has an independent 0.5% flake rate, the chance that the
run is green is 0.995^200 ≈ 37%. Developers learn that red usually means "retry", start
clicking retry without reading the failure, and eventually merge a real regression
because "it's probably flaky". The signal is gone.

### Common causes

| Cause | Example | Fix |
|---|---|---|
| Timing assumptions | `sleep(1)` then assert the async job finished | Wait on a condition with a timeout, inject a fake clock |
| Shared state between tests | Test B relies on a row test A inserted; order changes under parallelism | Each test creates and cleans its own data; randomise order to expose it (`pytest -p random_order`, `go test -shuffle=on`) |
| Real network / third parties | Calls a sandbox API that rate-limits | Fake or contract-test the dependency ([Microservices: Contract Testing](../TestingAndQuality/05_contract_testing.md)) |
| Concurrency bugs | A genuine data race that shows up 1 run in 50 | Run with `-race`, ThreadSanitizer; this "flake" is a real bug |
| Resource limits | Port collisions, full `/tmp`, OOM on a small runner | Random ports, per-test temp dirs, right-size runners |
| Time and locale | Test fails around midnight UTC or on the 29th of February | Pin time zone and clock in tests |
| Unordered collections | Asserting on map iteration order | Sort before comparing |

### A flake policy that works

1. **Detect**: record every test result with the commit. A test that both passed and
   failed on the same commit is flaky by definition. Many CI systems and test-analytics
   tools (BuildPulse, Trunk, Datadog CI Visibility, Buildkite Test Engine) do this.
2. **Quarantine**: move a known-flaky test out of the blocking set automatically, file a
   ticket to its owning team, and keep running it non-blocking so you know when it is fixed.
3. **Fix or delete** within a deadline. A test nobody fixes is not protecting anything.
4. **Retry sparingly**: an automatic single retry of *only the failed tests* hides flakes
   from developers but must still be reported, or flakiness grows unseen.

## 6. Hermetic, reproducible builds: the real fix for "works on my machine"

The owner's outline said CI must run "in the exact same Docker container that runs in
production". The goal is right but the phrasing is slightly off: production runs a
minimal runtime image with no compiler or test tools. What you actually want:

- **A pinned build environment**: the same toolchain version everywhere (the
  `go-version-file` trick, `.tool-versions` for asdf/mise, a pinned builder image, a
  Nix flake or a devcontainer), so the laptop and the runner compile identically.
- **Locked dependencies**: `go.sum`, `package-lock.json`, `uv.lock`, `poetry.lock`,
  `Cargo.lock`. Floating version ranges mean two builds of one commit can differ.
- **Hermeticity**: the build reads only declared inputs (source, locked deps, pinned
  toolchain), not the network or whatever is installed on the machine.
- **Build once, test the artifact you ship**: integration and E2E tests should run
  against the image the pipeline built, not a separately compiled binary. Chapter 02
  turns this into "build once, deploy many".
- **Reproducibility** (bonus level): building the same commit twice gives bit-identical
  output (`-trimpath`, fixed timestamps via `SOURCE_DATE_EPOCH`). It lets a third party
  verify that a binary really came from the claimed source.

## 7. CI is part of your attack surface

A CI system holds the keys to everything: it can read all source, it holds registry and
cloud credentials, and whatever it builds is trusted by production. Real incidents show
it: the 2020 SolarWinds compromise injected malware during the build, the 2021 Codecov
incident modified a CI upload script to exfiltrate environment variables, and in March
2025 the widely used `tj-actions/changed-files` GitHub Action was compromised and its
version tags repointed to code that printed runners' secrets into build logs
(CVE-2025-30066), affecting every repository that referenced it by tag.

| Risk | Mitigation |
|---|---|
| Over-privileged `GITHUB_TOKEN` | `permissions: contents: read` by default; grant `packages: write`, `id-token: write` per job only where needed |
| A third-party action's tag is repointed to malicious code | Pin actions to a full 40-character commit SHA (with the version in a comment); let Dependabot/Renovate update pins; allow-list actions at org level |
| Long-lived cloud keys stored as CI secrets | **OIDC federation**: the job requests a short-lived token (`id-token: write`) that the cloud provider (AWS, GCP, Azure) exchanges for temporary credentials scoped to that repo and branch. No static key exists to steal |
| Untrusted fork PRs running with secrets | `pull_request` from forks gets no secrets and a read-only token. Never check out and run fork code under `pull_request_target`, which runs with the base repo's secrets |
| Persistent self-hosted runners | Ephemeral, single-use runners (Actions Runner Controller pods, `--ephemeral`); never attach self-hosted runners to public repos |
| Secrets leaking into logs | Masking plus secret scanning; do not `echo` secrets or pass them on command lines |
| Tampered artifacts between CI and deploy | Sign images (Sigstore cosign, keyless via OIDC), publish SLSA build provenance and an SBOM, verify at deploy time; see [Continuous Deployment (CD) and Delivery](02_cd_and_delivery.md) |

The OIDC pattern is worth knowing concretely:

```yaml
jobs:
  deploy-infra:
    runs-on: ubuntu-latest
    permissions:
      id-token: write     # allow this job to request an OIDC token
      contents: read
    steps:
      - uses: aws-actions/configure-aws-credentials@v4
        with:
          role-to-assume: arn:aws:iam::123456789012:role/gha-deploy-prod
          aws-region: eu-west-1
      - run: aws sts get-caller-identity   # temporary credentials, valid about an hour
```

On the AWS side, the role's trust policy only accepts tokens whose `sub` claim is, for
example, `repo:acme/checkout-api:ref:refs/heads/main`, so a fork or another branch
cannot assume it. Secret handling in general is covered in
[Secret Management](../Tool-Kit/11_secret_management.md).

## 8. Measuring CI health and common anti-patterns

What to put on a CI dashboard:

| Metric | Why it matters | Healthy direction |
|---|---|---|
| PR pipeline duration p50 / p90 | The wait a developer feels | p90 under ≈10–15 min |
| Queue time (waiting for a runner) | Capacity problems hide here, not in job time | Near zero |
| Main branch "red" time | How long the trunk is broken per week | Minutes, not hours |
| Flake rate (failures that pass on retry) | Trust in the signal | Falling; every flake has an owner |
| Change failure rate after merge | Whether CI catches what matters | Falling |
| Cost per pipeline run | Runner minutes, cache storage | Tracked, not ignored |

Anti-patterns interviewers like to hear you name:

- **Flaky tests tolerated** and "just retry" culture (section 5).
- **Slow pipelines**: 45 minutes of PR CI pushes people to batch changes and stop
  waiting for results, which defeats integration.
- **Long-lived branches** with a CI server attached, which is automated building, not
  continuous integration.
- **Red main left red**: the team rule should be "fix or revert within minutes"; a broken
  trunk blocks everyone and hides new breakages behind the old one.
- **Building different artifacts per environment**, or rebuilding for production
  (chapter 02).
- **Pipeline logic only in the CI UI**, not versioned in the repo, so nobody can review or
  reproduce it.
- **Secrets and admin credentials everywhere** (section 7).
- **Tests that need a shared staging database**, so two pipelines running at once fight
  over the same rows.

## Common interview questions

**1. What is the difference between continuous integration, continuous delivery and continuous deployment?**
CI: everyone merges small changes to mainline frequently and each merge is verified by an
automated build and tests. Continuous delivery: every change that passes produces a
releasable artifact, and releasing is a business decision behind a button. Continuous
deployment: every passing change goes to production automatically, with no human gate.

**2. How would you order and structure a CI pipeline?**
Cheap, likely-to-fail checks first and in parallel (format, lint, typecheck, unit tests,
static scans), then expensive checks that depend on them (integration tests with real
dependencies), then build the artifact once and tag it with the commit SHA. Keep the
critical path short with `needs:` only where there is a real dependency, and split
pre-merge (fast) from post-merge (complete) pipelines.

**3. Two PRs are both green but `main` breaks after both merge. Why, and how do you prevent it?**
Each PR was tested against an older `main` that did not contain the other. "Require up to
date" forces serial rebases, which does not scale; a merge queue tests each PR on top of
`main` plus the PRs ahead of it, in parallel, and only advances `main` to combinations
that passed.

**4. Your PR pipeline takes 40 minutes. How do you get it to 10?**
Measure first: find the critical path and the queue time. Then cache dependencies and
build outputs keyed on lockfiles, order the Dockerfile for layer caching, split
independent work into parallel jobs, shard the largest test suite by recorded timings,
run only affected tests pre-merge (full suite post-merge), cancel superseded runs, and
move slow E2E suites out of the blocking path.

**5. How do you deal with flaky tests?**
Detect them automatically (pass and fail on the same commit), quarantine them out of the
blocking set with an owner and a deadline, fix the root cause (timing, shared state,
network, real races), and report retries rather than silently retrying. Explain the
compounding maths: many slightly flaky tests make most runs red.

**6. Why tag images with the commit SHA instead of `latest`?**
`latest` is mutable and says nothing about what is inside. A SHA tag (and, better, the
content digest) ties the artifact to exactly one commit, makes deploys reproducible and
rollbacks precise, and lets you promote the same bytes through every environment.

**7. How do you give a CI job access to AWS without storing access keys?**
OIDC federation: grant the job `id-token: write`, have it request a signed token from the
CI provider, and configure an IAM role whose trust policy accepts that token only for the
specific repository and branch. The job gets temporary credentials, and there is no
long-lived key to leak.

**8. What is the risk of `uses: some/action@v2`?**
The tag is mutable; if the action's repository is compromised, the tag can be repointed
to malicious code that runs with your job's token and secrets, as happened with
`tj-actions/changed-files` in 2025. Pin third-party actions to a full commit SHA and keep
the job's permissions minimal.

**9. What does trunk-based development need to work?**
Small changes merged at least daily, a fast and trustworthy CI, a merge queue or
equivalent to keep `main` green, feature flags so incomplete work can merge dark, and a
culture of fixing or reverting a broken trunk immediately.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | Intern | What CI is and why teams merge often; how to read a failing check on their PR, reproduce it locally and fix it; the basic workflow file layout |
| Junior (L3) | Software Engineer / New Grad | L3 | Writes and edits workflow jobs; uses caching and service containers; keeps tests deterministic; knows why `latest` tags and long-lived branches are bad; never commits secrets |
| Mid (L4) | Software Engineer II | L4 | Designs a pipeline with a short critical path and pre/post-merge split; diagnoses and quarantines flaky tests; optimises Dockerfiles and build caches; understands branch protection, required checks and merge queues |
| Senior (L5) | Senior Software Engineer | L5 | Owns CI for a service or team end to end: speed targets, flake policy, least-privilege tokens, OIDC to cloud, SHA-pinned actions, artifact provenance; can explain "green PR, red main" and choose trunk-based vs release-branch models for a product |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7+ | Sets organisation-wide CI strategy: reusable pipeline templates, monorepo build systems with remote caching and test impact analysis, runner fleet security and cost, supply-chain standards (SLSA level targets), and the metrics that tie CI health to delivery performance |

## Interview checklist

- [ ] I can explain integration hell and why frequent small merges fix it.
- [ ] I can define CI, continuous delivery and continuous deployment precisely.
- [ ] I can sketch a pipeline with parallel cheap checks, dependent expensive checks and a single artifact build.
- [ ] I can read a GitHub Actions workflow and explain events, jobs, steps, runners, `needs`, `concurrency`, `permissions` and service containers.
- [ ] I can explain the "green PR, red main" problem and how a merge queue solves it (including the `merge_group` trigger).
- [ ] I can list at least five ways to speed up a slow pipeline and their pitfalls.
- [ ] I can explain why flaky tests destroy CI's value, their common causes and a detect/quarantine/fix policy.
- [ ] I can explain hermetic and reproducible builds and "build once, test what you ship".
- [ ] I can name the main CI supply-chain risks (token scope, mutable action tags, fork PRs, long-lived keys) and their mitigations, including OIDC.
- [ ] I can compare trunk-based development, GitHub flow and GitFlow and say when each fits.

Related: [Continuous Deployment (CD) and Delivery](02_cd_and_delivery.md) (what happens to the artifact next),
[Git and GitHub Workflows](../Tool-Kit/03_git_and_github_workflows.md) (Git and PR mechanics),
[Docker and Containerization](../Tool-Kit/01_docker_and_containers.md) (image builds),
[The Testing Pyramid and Unit Tests](../TestingAndQuality/01_testing_pyramid.md) and [Integration and End-to-End (E2E) Testing](../TestingAndQuality/03_integration_and_e2e.md)
(what the test stages contain), [Secret Management](../Tool-Kit/11_secret_management.md).
