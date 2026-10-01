# Continuous Deployment (CD) and Delivery

If CI is about proving a change works, CD is about getting that proven change in front of
users safely, repeatably and often. This chapter explains what "delivery" means in
practice: the difference between continuous delivery and continuous deployment, how one
immutable artifact is promoted through environments, how configuration and secrets are
injected so the same bytes run everywhere, how the software supply chain is signed and
verified, which gates and safety checks belong in a pipeline, and how teams measure
whether any of it is working. Deployment *strategies* (rolling, blue/green, canary) have
their own chapter, [Deployment Strategies](03_deployment_strategies.md); the pull-based GitOps model has
[GitOps and Argo CD](04_gitops_and_argocd.md).

## Foundations — What happens to code after CI says it is green?

### From "it works" to "users have it"

A green CI run gives you an artifact, usually a container image, that passed its tests.
Nobody has used it yet. Between that moment and a user benefiting from the change, a
team has to answer several questions:

- **Where does it go first?** Usually a test or staging environment that looks like
  production, where broader tests run against the deployed system.
- **Who or what decides it is ready for production?** A person pressing a button, an
  automated check, or both.
- **How does it get there without downtime?** A deployment strategy.
- **How do we know it is healthy once it is there, and how do we undo it if not?**
  Monitoring, automated analysis and rollback.

**Continuous delivery** is the discipline of making that whole path automated,
repeatable and boring, so that releasing is a low-risk decision you could make at any
moment. Jez Humble and David Farley's book *Continuous Delivery* (2010) gave it the name
and its core idea: the **deployment pipeline**, one automated path every change takes
from commit to production.

### The pieces

| Piece | What it is | Example |
|---|---|---|
| Artifact | The immutable, versioned output of CI | `ghcr.io/acme/checkout-api@sha256:9f2c…` |
| Artifact registry | Where artifacts are stored and pulled from | GHCR, ECR, Artifact Registry, Harbor, Artifactory |
| Environment | A running copy of the system with its own config and data | `dev`, `staging`, `prod-eu`, `prod-us` |
| Promotion | Moving the *same* artifact to the next environment | staging digest → prod |
| Gate | A condition that must hold before promotion | Tests passed, approval given, error budget left |
| Deployment | Installing a new version into an environment | New pods running image X |
| Release | Exposing new behaviour to users | Feature flag turned on, traffic shifted |
| Rollback / roll-forward | Getting back to a good state | Redeploy the previous digest, or ship a fix |
| CD tool | The orchestrator that performs deploys | Argo CD, Flux, Spinnaker, GitHub Actions environments, GitLab, Harness, Octopus |

### An everyday example

A food-delivery company merges a change to its pricing service at 10:02. CI builds image
`pricing@sha256:ab12…` and pushes it. The CD system deploys that digest to staging, runs
a ten-minute suite of API tests against it and checks staging's error rate. At 10:20 the
same digest is deployed to 5% of production pods in one region; automated analysis
compares their error rate and latency with the other 95% for fifteen minutes; then it
rolls through the rest of that region, then the other regions one at a time. By noon the
change is everywhere, and at no point did anyone rebuild the image, copy a file by hand
or SSH into a server. If the canary had looked worse, the pipeline would have shifted
traffic back and paged nobody but the author.

### Deploy is not release

A **deployment** puts new code on servers. A **release** exposes new behaviour to users.
Separating them is the most useful idea in modern delivery: you can deploy code that is
switched off behind a flag (chapter 05), deploy to a canary that sees 1% of traffic
(chapter 03), or deploy to a region with no users yet. Most of the risk management in
this module is about making the gap between the two controllable.

## 1. Continuous delivery vs. continuous deployment

- **Continuous delivery**: every change that passes the pipeline is *releasable*. The
  artifact is built, tested and ready; promoting it to production is a decision, often a
  human pressing a button or approving a deployment. The key property is that the button
  is always safe to press.
- **Continuous deployment**: every change that passes the pipeline *is* deployed to
  production automatically, with no human in the path. Humans still decide what merges;
  the pipeline decides what ships.

| | Continuous delivery | Continuous deployment |
|---|---|---|
| Production trigger | Human approval or schedule | Passing pipeline |
| Typical deploy frequency | Daily to weekly | Many times per day |
| Requires | Reliable pipeline, releasable trunk | All of that, plus strong automated tests, automated canary analysis and rollback, feature flags |
| Fits | Regulated environments needing a sign-off, release trains, apps where a release is costly (mobile, on-prem) | Web services and APIs with good observability |
| Risk per deploy | Larger batches | Tiny batches, easy to bisect |

**Precision note:** the owner's outline said continuous deployment "requires immense trust
in your automated test suite". That is true but incomplete. Tests catch only what someone
thought to test; what makes continuous deployment safe in practice is the combination of
**small batches** (each deploy contains one or two changes, so a regression points at its
cause), **progressive exposure** (canary or percentage rollout) and **automated
detection and rollback** based on production signals. Teams that practise it well rely at
least as much on those as on pre-production tests.

### Gates that are worth having

| Gate | What it checks | Automated? |
|---|---|---|
| Tests on the deployed system | Smoke, API, E2E tests against staging | Yes |
| Canary / progressive analysis | Error rate, latency and saturation of the new version vs the old | Yes (chapter 03) |
| Error budget policy | The service has SLO budget left this window; if not, only fixes ship | Yes, from SLO tooling |
| Change freeze / deploy window | No deploys during peak events or holidays | Yes (calendar) |
| Manual approval | A named person accepts the risk | No, and it should be rare and meaningful |
| Policy checks | Signed image, no critical CVEs, required labels, resource limits set | Yes (admission control, policy engines) |

Manual approvals feel safe but often are not: an approver clicking through twenty
deploys a day is not reviewing anything. The DORA research found that heavyweight
external change approval (a change advisory board) was associated with *lower*
delivery performance and no improvement in stability, while lightweight peer review plus
automation was not. Keep human gates for decisions that are genuinely human (a legal
launch date, a risky data migration).

## 2. The deployment pipeline and environment promotion

```arch
%% caption: CI publishes one image digest; CD promotes that exact digest through staging and progressive production waves, gated by tests and health analysis at each step.
grid 170x110
node ci "CI" at 0,0 icon=workflow sub="build + test once"
node reg "Registry" at 1,0 icon=storage sub="image@sha256:ab12"
node cd "CD orchestrator" at 2,0 icon=rocket sub="promotes by digest"
node stg "Staging" at 0,1 icon=cloud sub="E2E + smoke tests"
node gate "Gates pass?" at 1,1 shape=diamond color=amber
node can "Prod canary" at 2,1 icon=cloud sub="5% in one region"
node w1 "Prod wave 1" at 1,2 icon=region sub="rest of region A"
node w2 "Prod wave 2" at 2,2 icon=region sub="other regions"
ci -> reg : "push once"
reg -> cd : "new digest"
cd -> stg : "deploy"
stg -> gate
gate -> can : "yes"
can -> w1 : "analysis ok"
w1 -> w2 : "bake time"
```

A good pipeline has these properties:

- **One path to production.** Every change, including hotfixes, goes through the same
  pipeline, perhaps with some stages sped up. Out-of-band "just this once" deploys are
  where outages come from.
- **Same artifact everywhere** (section 3).
- **Environments differ only in configuration and scale**, not in how they are built or
  deployed (section 4).
- **Progressive production exposure**: canary, then waves by cell or region with **bake
  time** between them, so a problem that only shows under real load or after an hour
  (a memory leak, a daily batch job) hits a small slice first. Large providers publish
  this practice: Google's SRE book and Azure's "safe deployment practices" both describe
  staged rollouts across increasingly large groups of servers and regions.
- **Automatic rollback on failure signals**, not only on a human noticing.
- **Everything recorded**: which digest, which commit, who approved, when, where. This is
  also what auditors ask for.

### Push-based vs pull-based deployment

| | Push (pipeline deploys) | Pull (GitOps agent reconciles) |
|---|---|---|
| Who talks to the cluster | The CI/CD runner, with cluster credentials | An agent inside the cluster (Argo CD, Flux) |
| How a deploy happens | `kubectl apply`, `helm upgrade`, a cloud API call from the pipeline | CI commits the new digest to a config repo; the agent notices and syncs |
| Drift detection | None unless you build it | Continuous; the agent compares live state with Git |
| Credentials | Cluster admin credentials stored in CI | Stay in the cluster; CI only writes to Git |
| Good for | Simple setups, non-Kubernetes targets (serverless, VMs, mobile stores) | Kubernetes fleets, many clusters, audit-heavy environments |

Both are legitimate. Chapter 04 goes deep on the pull model.

### A push-based deploy job with an environment gate

GitHub Actions **environments** give a job a protection rule (required reviewers, a wait
timer, allowed branches) and environment-scoped secrets:

```yaml
name: deploy
on:
  workflow_run:
    workflows: [ci]
    types: [completed]
    branches: [main]

permissions:
  contents: read
  id-token: write          # OIDC to the cloud, no stored keys

jobs:
  staging:
    if: github.event.workflow_run.conclusion == 'success'
    runs-on: ubuntu-latest
    environment: staging
    steps:
      - uses: actions/checkout@v5
        with:
          ref: ${{ github.event.workflow_run.head_sha }}
      - run: ./deploy.sh staging "${{ github.event.workflow_run.head_sha }}"
      - run: ./smoke-test.sh https://staging.acme.internal

  production:
    needs: staging
    runs-on: ubuntu-latest
    environment:
      name: production     # protection rule: 1 required reviewer, main branch only
      url: https://acme.com
    steps:
      - uses: actions/checkout@v5
        with:
          ref: ${{ github.event.workflow_run.head_sha }}
      - run: ./deploy.sh production "${{ github.event.workflow_run.head_sha }}"
```

The job pauses at `environment: production` until an allowed reviewer approves; that is
continuous delivery. Removing the reviewer rule makes it continuous deployment.

### Tools you will hear about

| Tool | Model | Notes |
|---|---|---|
| Argo CD | Pull, Kubernetes | CNCF graduated; UI, multi-cluster, ApplicationSets (chapter 04) |
| Flux | Pull, Kubernetes | CNCF graduated; set of controllers, image automation |
| Argo Rollouts / Flagger | Progressive delivery controllers | Canary and blue/green with metric analysis (chapter 03) |
| Kargo | Promotion orchestration on top of Argo CD | Models stages and "freight" moving between them |
| Spinnaker | Push, multi-cloud | Created at Netflix; pipelines, Kayenta automated canary analysis |
| GitHub Actions / GitLab CI environments | Push, from the CI system | Simple and common; approval rules and scoped secrets |
| Harness, Octopus Deploy, AWS CodeDeploy, Google Cloud Deploy | Managed or commercial CD | Built-in strategies, approvals, verification |
| Tekton | Kubernetes-native pipeline building blocks | Often underneath other products |

## 3. Build once, deploy many: immutable artifacts

The rule: **the artifact that reaches production is byte-for-byte the one that was
tested.** Never rebuild for a later environment.

Why rebuilding is dangerous (the owner's example, kept because it is the classic one):

1. Push to `main`.
2. CI builds an image and deploys it to staging, where tests pass.
3. For production, CI checks out the code again and builds again.
4. Between 2 and 3 a floating dependency released a new version, a base image tag moved,
   or the build machine changed. Production now runs bytes that were never tested.

The correct flow:

1. CI builds once, tags the image with the commit SHA (`checkout-api:3f9a1c2`) and
   records its **digest**.
2. CD deploys that digest to staging; tests pass.
3. CD deploys the *same digest* to production.

### Tags vs digests

A **tag** (`:v1.4.2`, `:3f9a1c2`, `:latest`) is a mutable pointer; anyone with push
access can move it. A **digest** (`@sha256:9f2c…`) is the hash of the image manifest, so
it names exactly one set of bytes and cannot be changed. Deploy by digest:

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: checkout-api
spec:
  replicas: 6
  selector:
    matchLabels: { app: checkout-api }
  template:
    metadata:
      labels: { app: checkout-api }
    spec:
      containers:
        - name: api
          # the tag is informative; the digest is what the kubelet pulls
          image: ghcr.io/acme/checkout-api:3f9a1c2@sha256:9f2c4e6d0b1a7c3e5f8d2b4a6c8e0f1d3b5a7c9e1f3d5b7a9c1e3f5d7b9a1c3e
          ports: [{ containerPort: 8080 }]
```

Get a digest from a registry with `docker buildx imagetools inspect ghcr.io/acme/checkout-api:3f9a1c2`
or `crane digest ghcr.io/acme/checkout-api:3f9a1c2`. `docker/build-push-action` also
exposes it as the `digest` output.

**Precision note:** `:latest` is not special to the registry; it is just the tag Docker
uses when you give none. It does not mean "newest", and Kubernetes defaults
`imagePullPolicy` to `Always` for `:latest` (and for images with no tag), which is one
more reason never to deploy it.

### Versioning what is not a container

The same rule applies to other artifacts: a JAR in Maven, a wheel in a private PyPI, a
Lambda zip in S3, a Helm chart in an OCI registry, a mobile binary. Give each a unique,
immutable version (semantic version plus build metadata, or the commit SHA), store it
once, and promote the reference.

## 4. Configuration and secrets injection

Because staging and production run the same image, **the image must not contain
environment-specific configuration** such as hostnames, feature defaults or credentials.
This is factor III of the Twelve-Factor App: "store config in the environment".

```arch
%% caption: One image, many environments: each environment supplies its own configuration and secrets at deploy or start time.
grid 170x110
group stg "Staging" color=blue icon=cloud
node cs "Staging config" at 0,0 in stg icon=file sub="DB_HOST=stg-db"
node ps "Staging pods" at 0,1 in stg icon=container
node img "checkout-api image" at 1,1 icon=package sub="sha256:9f2c, no config"
group prod "Production" color=green icon=cloud
node cp "Prod config" at 2,0 in prod icon=file sub="DB_HOST=prod-db"
node pp "Prod pods" at 2,1 in prod icon=container
node vault "Secret store" at 1,2 icon=secrets sub="Vault, cloud SM"
img -> ps : "same digest"
img -> pp : "same digest"
cs -> ps
cp -> pp
vault ..> ps : "creds"
vault ..> pp : "creds"
```

### Mechanisms

| Mechanism | How it reaches the app | Changes need | Notes |
|---|---|---|---|
| Environment variables | Set on the container from a ConfigMap/Secret or the platform | Pod restart | Simple; visible in process listings and crash dumps, so prefer files for secrets |
| Mounted files | ConfigMap/Secret volume, read at start or watched | Kubelet refreshes mounted files after a delay (≈ a minute, not for `subPath` mounts); app must re-read | Good for secrets and larger config |
| Kustomize overlays / Helm values | Rendered into manifests per environment | A new commit and sync | The GitOps-friendly way to express differences |
| External secret operators | Sync from Vault, AWS Secrets Manager, GCP Secret Manager into Kubernetes Secrets | Operator refresh interval | External Secrets Operator, Vault Agent, CSI Secrets Store driver |
| Remote config / flags service | App fetches at runtime | No deploy | Chapter 05; for behaviour, not for credentials |

A Kustomize layout that keeps environment differences small and reviewable:

```yaml
# overlays/production/kustomization.yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
resources:
  - ../../base
images:
  - name: ghcr.io/acme/checkout-api
    digest: sha256:9f2c4e6d0b1a7c3e5f8d2b4a6c8e0f1d3b5a7c9e1f3d5b7a9c1e3f5d7b9a1c3e
replicas:
  - name: checkout-api
    count: 12
configMapGenerator:
  - name: checkout-config
    literals:
      - DB_HOST=prod-db.internal
      - LOG_LEVEL=info
```

`configMapGenerator` appends a hash of the contents to the ConfigMap name, so changing a
value changes the name, which changes the pod template and triggers a normal rolling
update. That fixes a classic surprise: editing a ConfigMap in place does **not** restart
pods that read it through environment variables.

**Precision note:** a Kubernetes Secret is base64-encoded, not encrypted. Protect it with
RBAC, enable encryption at rest for etcd (ideally through a KMS provider), and do not
commit plain Secret manifests to Git. For GitOps, commit an *encrypted* or *referenced*
form instead: Sealed Secrets, SOPS-encrypted files, or an `ExternalSecret` that points at
the real store. See [Secret Management](../Tool-Kit/11_secret_management.md).

### Config changes are deploys

A configuration change can take production down as easily as a code change. Several of
the largest public cloud outages were configuration pushes, not binaries. Treat config
with the same pipeline: versioned, reviewed, validated (schema checks, `kubectl apply
--dry-run=server`), rolled out progressively, and easy to revert.

## 5. The software supply chain: sign, attest, verify

Once artifacts move between systems, you need to answer: *is this the image our CI built
from reviewed source, and has nobody tampered with it since?* The industry answer has
settled on three pieces:

| Piece | What it proves | Common tools and formats |
|---|---|---|
| Signature | This digest was signed by an identity you trust | Sigstore **cosign** (keyless: a short-lived certificate from Fulcio tied to the CI's OIDC identity, recorded in the Rekor transparency log), Notation / Notary v2 |
| Provenance attestation | Which source commit, which workflow and which builder produced it | **SLSA** provenance (in-toto format), GitHub artifact attestations |
| SBOM | Which packages and versions are inside | SPDX, CycloneDX; generated by Syft, Trivy, BuildKit |

```arch
%% caption: CI signs the image and attaches provenance and an SBOM; the cluster's admission policy refuses anything whose signature or provenance does not verify.
grid 170x110
node ci "CI job" at 0,0 icon=workflow sub="OIDC identity"
node sign "Sign + attest" at 1,0 icon=key sub="cosign, SLSA, SBOM"
node reg "Registry" at 2,0 icon=storage sub="image + attestations"
node log "Transparency log" at 1,1 icon=logs sub="Rekor"
node adm "Admission policy" at 2,1 icon=shield sub="Kyverno / policy-controller"
node pods "Pods run" at 2,2 icon=container color=green
node deny "Rejected" at 1,2 icon=error color=red sub="unsigned or wrong identity"
ci -> sign
sign -> reg
sign ..> log : "record"
reg -> adm : "deploy request"
adm -> pods : "verified"
adm -> deny : "fails"
```

Keyless signing and verification with cosign, in a CI job with `id-token: write`:

```bash
# In CI, after pushing: sign the digest (never a tag) with the job's OIDC identity.
cosign sign --yes ghcr.io/acme/checkout-api@sha256:9f2c4e...

# Anywhere later: verify it was signed by *this* repository's workflow on main.
cosign verify \
  --certificate-identity-regexp '^https://github.com/acme/checkout-api/\.github/workflows/.+@refs/heads/main$' \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  ghcr.io/acme/checkout-api@sha256:9f2c4e...

# GitHub-native alternative: provenance from actions/attest-build-provenance, then
gh attestation verify oci://ghcr.io/acme/checkout-api@sha256:9f2c4e... --owner acme
```

**SLSA** (Supply-chain Levels for Software Artifacts) grades how trustworthy a build's
provenance is. Its v1.0 Build track: L1 means provenance exists; L2 means it is generated
and signed by a hosted build platform; L3 means the build platform is hardened so that
even the build's own steps cannot forge the provenance. Many organisations target L2 or
L3 for production artifacts and enforce it at admission time.

## 6. Safety mechanisms inside a deploy

The deploy itself should fail loudly and early rather than leave a half-broken service:

- **Readiness probes** gate traffic: a pod receives requests only when its readiness
  endpoint passes, so a version that cannot reach its database never gets traffic.
- **`minReadySeconds`** makes Kubernetes wait until a new pod has been ready for that
  long before counting it available, which catches crash-after-start bugs.
- **`progressDeadlineSeconds`** (default 600 s) marks a Deployment as failed
  (`ProgressDeadlineExceeded`) if the rollout stops making progress, so the pipeline can
  react. Kubernetes itself does **not** roll back automatically; your pipeline or a
  progressive delivery controller must.
- **Post-deploy verification**: smoke tests, synthetic checks and an automated
  comparison of error rate and latency against the previous version (chapter 03).
- **Bake time**: wait a fixed period in each wave before the next, long enough for
  slow-burning problems to show.
- **Deploy markers**: annotate dashboards with each deploy, so "what changed?" takes
  seconds to answer during an incident.

```bash
# In a push-based pipeline: block until the rollout finishes or fails, and undo on failure.
kubectl -n checkout set image deployment/checkout-api \
  api=ghcr.io/acme/checkout-api@sha256:9f2c4e...
if ! kubectl -n checkout rollout status deployment/checkout-api --timeout=10m; then
  kubectl -n checkout rollout undo deployment/checkout-api
  exit 1
fi
```

### Database migrations belong in the pipeline, carefully

Schema changes are the part of a deploy that cannot be undone by redeploying an old
image. Run them as a separate, explicit pipeline step (a Kubernetes Job, an Argo CD
`PreSync` hook, a Flyway/Liquibase/Atlas/Alembic step), make every migration backward
compatible with the version currently running, and follow expand/contract. Chapter 05
and [Schema Migrations](../SQL/12_schema_migrations.md) cover the pattern in detail.

## 7. Measuring delivery: the DORA metrics

The DORA research programme (DevOps Research and Assessment, now part of Google Cloud)
defines the most widely used delivery metrics. The original four, from *Accelerate*
(Forsgren, Humble, Kim, 2018):

| Metric | Measures | Type |
|---|---|---|
| Deployment frequency | How often you deploy to production | Throughput |
| Lead time for changes | Commit to running in production | Throughput |
| Change failure rate | Share of deployments that cause a failure needing remediation | Stability |
| Failed deployment recovery time | How long to recover from a failed deployment (renamed from "time to restore service"/MTTR in 2023) | Stability |

The 2024 report added a fifth stability metric, **rework rate**: the share of deployments
that were unplanned fixes for a problem in production.

The research's key finding is that throughput and stability are **not** a trade-off:
teams that deploy more often also tend to have lower failure rates and faster recovery,
because small, frequent changes are easier to test, review, roll out and debug. The
top-performing clusters in the reports typically deploy on demand (several times a day)
with lead times under a day and recovery under an hour.

Use them for a team to improve against itself, not to rank teams: a metric that becomes
a target gets gamed (splitting deploys to raise frequency, reclassifying incidents to
lower failure rate).

## 8. When the target is not a server

| Target | What changes |
|---|---|
| Mobile apps | Store review adds hours to days; you cannot roll back a binary on users' phones. Use staged rollouts (Google Play percentage rollout, App Store phased release over 7 days), server-driven config and feature flags, and keep old app versions working against the API for a long time |
| Libraries and SDKs | "Deploy" means publishing a version; consumers upgrade on their own schedule. Semantic versioning, changelogs, deprecation periods, and never re-publishing an existing version number |
| Serverless functions | Versions and aliases with weighted traffic (AWS Lambda aliases, Cloud Run revisions) give canary behaviour without managing servers |
| Infrastructure (Terraform, Pulumi) | `plan` in the PR, `apply` after merge, state locking, drift detection; destructive changes need extra review ([Infrastructure as Code (IaC)](../Tool-Kit/08_infrastructure_as_code.md)) |
| Databases and data pipelines | Migrations and backfills are one-way doors; version data contracts and run them as explicit steps |
| On-prem / customer-hosted | Release trains, long-term support branches, upgrade paths across several versions |

## Common interview questions

**1. What is the difference between continuous delivery and continuous deployment?**
Continuous delivery keeps every passing change releasable; a human or a schedule decides
when to promote to production. Continuous deployment promotes every passing change
automatically. Deployment requires, beyond tests, small batches, progressive exposure,
automated health analysis and automated rollback.

**2. Why build once and promote, rather than build per environment?**
So production runs exactly the bytes that were tested. Rebuilding can pick up different
dependency versions, base images or toolchains, which means shipping untested code. Tag
by commit and deploy by digest so the reference is immutable.

**3. If the same image runs in staging and production, where does the configuration come from?**
From the environment at deploy or start time: ConfigMaps and Secrets (or overlays that
render them), mounted files, environment variables, and a secret manager for
credentials. The image contains no environment-specific values.

**4. Why is `:latest` a bad deployment reference?**
It is a mutable tag, not "the newest"; it hides which code is running, breaks
reproducibility and rollback, and makes Kubernetes pull on every start. Use SHA tags for
humans and digests for machines.

**5. How would you design a production rollout for a service in five regions?**
Deploy to staging and run automated tests; canary in one region with automated metric
comparison; roll the rest of that region; then proceed region by region (or cell by
cell) with bake time between waves; halt and roll back automatically on SLO-based
signals; avoid starting new waves near peak traffic or during a freeze.

**6. How do you know a container image in production came from your CI?**
Sign images in CI (cosign keyless with the workflow's OIDC identity), produce SLSA
provenance and an SBOM, and enforce verification at admission (Kyverno, Sigstore
policy-controller) so unsigned or wrongly signed images are refused.

**7. What are the DORA metrics and why do they matter?**
Deployment frequency, lead time for changes, change failure rate and failed deployment
recovery time, plus rework rate since 2024. They measure delivery throughput and
stability together, and the research shows high performers are better at both.

**8. A config change caused an outage. What should change in the process?**
Treat config as code: version it, review it, validate it against a schema, roll it out
progressively with health checks and bake time, and make rollback one step, exactly as
for binaries.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | Intern | The difference between CI, continuous delivery and continuous deployment; that staging and production are separate environments; that deploys should be automated |
| Junior (L3) | Software Engineer / New Grad | L3 | Uses the team's pipeline; knows why images are tagged by SHA and never rebuilt per environment; keeps config and secrets out of images; can read a rollout status and trigger a rollback |
| Mid (L4) | Software Engineer II | L4 | Builds a deploy pipeline with staging, gates and environment protection; deploys by digest; uses Kustomize/Helm overlays and a secret manager; wires readiness probes, progress deadlines and post-deploy smoke tests |
| Senior (L5) | Senior Software Engineer | L5 | Designs progressive multi-region rollouts with bake times and automated rollback; chooses push vs pull deployment; sets up signing, provenance and admission verification; plans migrations as pipeline steps; reads DORA metrics for their team |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7+ | Sets the delivery platform and policy for many teams: one path to production, supply-chain level targets, change-management that satisfies auditors without a slow approval board, and a metrics programme that improves throughput and stability together |

## Interview checklist

- [ ] I can explain continuous delivery vs continuous deployment and what each requires.
- [ ] I can explain deploy vs release and why separating them reduces risk.
- [ ] I can draw a deployment pipeline with staging, gates, a canary and production waves.
- [ ] I can explain "build once, deploy many", tags vs digests, and why `:latest` is harmful.
- [ ] I can describe how configuration and secrets reach the same image in different environments, and why a Kubernetes Secret is not encryption.
- [ ] I can explain why editing a ConfigMap does not restart pods and how hashed ConfigMap names fix it.
- [ ] I can explain image signing, SLSA provenance, SBOMs and admission-time verification.
- [ ] I can list deploy-time safety mechanisms (readiness, `minReadySeconds`, progress deadline, bake time) and note that Kubernetes does not auto-rollback.
- [ ] I can compare push-based and pull-based deployment.
- [ ] I can name the DORA metrics and explain why throughput and stability move together.

Related: [Continuous Integration (CI) Fundamentals](01_ci_fundamentals.md) (where the artifact comes from),
[Deployment Strategies](03_deployment_strategies.md), [GitOps and Argo CD](04_gitops_and_argocd.md),
[Feature Flags and Rollbacks](05_feature_flags_and_rollbacks.md), [Platform and Infrastructure](../SystemDesign/building_blocks/16_platform_and_infra.md),
[Multi-Region and Global Traffic](../SystemDesign/building_blocks/27_multi_region_and_global_traffic.md),
[Kubernetes and Orchestration](../Tool-Kit/02_kubernetes_and_helm.md), [Secret Management](../Tool-Kit/11_secret_management.md).
