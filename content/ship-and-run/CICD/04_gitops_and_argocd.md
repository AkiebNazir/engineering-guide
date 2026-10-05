# GitOps and Argo CD

Traditional pipelines deploy by *pushing*: a CI job holding cluster credentials runs
`kubectl apply` or `helm upgrade`. GitOps flips that to a *pull* model: Git holds the
desired state of every environment, and an agent running next to the workload keeps
comparing reality with Git and correcting the difference. This chapter explains the idea
from zero, then goes deep on Argo CD, the most widely used GitOps controller for
Kubernetes: its architecture, how a reconcile loop actually runs, sync and health
semantics, hooks and waves, repository layouts, ApplicationSets for many clusters,
secrets, how it compares with Flux, and the failure modes that show up in production.

## Foundations — What is GitOps, and why pull instead of push?

### The problem it solves

Imagine a team with three Kubernetes clusters that deploys by running commands: a CI job
runs `helm upgrade`, an engineer applies a hotfix with `kubectl edit` at 2 a.m., someone
else scales a Deployment by hand during a traffic spike. Six months later, nobody can
answer simple questions: *what exactly is running in production? Who changed it, and
when? Is staging the same as production? If this cluster died, could we rebuild it?*
The cluster itself has become the only record of its own configuration, and it keeps no
history.

GitOps answers all of those with one rule: **the desired state of every environment is
declared in Git, and software, not people, makes the running system match it.**

### The thermostat analogy

A thermostat does not execute "heat for 20 minutes". You declare a *desired state*
(21 °C). It continuously measures the *actual state*, and whenever the two differ it acts
to close the gap. If someone opens a window, it notices and compensates without being
told. Kubernetes controllers already work this way inside a cluster (a Deployment
controller keeps the number of pods equal to `replicas`). GitOps extends the same loop one
level up: Git is the thermostat setting, and a GitOps controller keeps the cluster's
objects equal to what Git says.

### The four principles

The CNCF OpenGitOps project wrote the principles down in 2021:

1. **Declarative**: the system's desired state is expressed declaratively (manifests,
   Helm charts, Kustomize overlays), not as a sequence of commands.
2. **Versioned and immutable**: desired state is stored in a way that keeps full history
   and cannot be silently altered. In practice, Git.
3. **Pulled automatically**: software agents pull the desired state from the source
   themselves.
4. **Continuously reconciled**: agents keep observing the actual state and act to match
   the desired state, not only when a pipeline runs.

### Vocabulary

| Term | Meaning |
|---|---|
| Desired state | What Git declares: manifests rendered at a specific commit |
| Live state | What the Kubernetes API server currently holds |
| Drift | Any difference between desired and live state |
| Reconcile | Compare desired with live and act on the difference |
| Sync | Argo CD's action of applying desired state to the cluster |
| Sync status | `Synced` or `OutOfSync`: does live match Git? |
| Health status | `Healthy`, `Progressing`, `Degraded`, `Suspended`, `Missing`, `Unknown`: is it working? |
| Application | Argo CD's custom resource linking a Git source to a cluster destination |
| Prune | Delete live objects that no longer exist in Git |
| Self-heal | Automatically revert live changes that were not made through Git |

## 1. Push vs pull, precisely

```arch
%% caption: Push: the pipeline holds cluster credentials and applies changes. Pull: the pipeline only writes to Git, and an in-cluster agent pulls and reconciles.
grid 170x110
group push "Push model" color=amber icon=rocket
node ci1 "CI pipeline" at 0,0 in push icon=workflow sub="holds cluster admin"
node k1 "Cluster" at 0,1 in push icon=k8s sub="no drift detection"
group pull "Pull model (GitOps)" color=green icon=sync
node ci2 "CI pipeline" at 1,0 in pull icon=workflow sub="writes to Git only"
node git "Config repo" at 2,0 in pull icon=git sub="desired state"
node argo "GitOps agent" at 2,1 in pull icon=sync sub="inside the cluster"
node k2 "Cluster" at 1,1 in pull icon=k8s sub="continuously reconciled"
ci1 -> k1 : "kubectl apply"
ci2 -> git : "commit digest"
argo -> git : "pull"
argo -> k2 : "reconcile"
```

The owner's outline listed three advantages of pull. They hold, with precision:

- **Security.** With push, the CI system holds credentials that can change production;
  compromise CI and you own the cluster. With pull, CI needs only write access to a Git
  repository, and the agent's cluster credentials never leave the cluster.
  **Precision note:** this moves the crown jewels rather than removing them. Anyone who
  can merge to the config repo can now change production, so the repository needs branch
  protection, required reviews, signed commits and tight write access. And an Argo CD
  instance that manages *other* clusters stores their credentials, so a central Argo CD
  is itself a high-value target.
- **Drift detection and correction.** The agent continuously compares live state with
  Git. **Precision note:** the owner wrote that Argo CD "will immediately detect ... and
  will aggressively overwrite the manual change". Detection is continuous, but correction
  only happens if **automated sync with `selfHeal: true`** is enabled on that Application.
  By default Argo CD just marks the app `OutOfSync` and waits for someone to sync.
- **Disaster recovery.** Point a fresh Argo CD at the same repository and it recreates
  every declared object. **Precision note:** "go get coffee and it recreates the entire
  infrastructure perfectly" overstates it. Git holds *object definitions*, not *data*:
  persistent volumes, databases and object storage need their own backups. Secrets are
  usually not in Git in plain form, so the secret store or its keys must be restored
  first. Cloud resources outside Kubernetes (load balancers, DNS, IAM) need IaC too. And
  CRDs must exist before the custom resources that use them, which is an ordering problem
  (section 4). GitOps makes DR far more repeatable; it does not make it automatic.

Two more benefits the outline did not list: **auditability** (every production change is a
reviewed commit with an author and a timestamp) and **rollback by revert** (section 8).

## 2. Argo CD architecture and the reconcile loop

Argo CD (two words; a CNCF graduated project since December 2022, with 3.x the current
major line since 2025) runs as a set of components in a namespace, usually `argocd`:

```arch
%% caption: The repo server renders manifests from Git; the application controller diffs them against the live cluster, syncs and assesses health; the API server serves the UI, CLI and webhooks.
grid 170x110
node git "Git repos" at 0,0 icon=git sub="Helm, Kustomize, YAML"
node user "UI / CLI / webhook" at 2,0 icon=users
group argo "Argo CD (argocd namespace)" color=blue icon=sync
node repo "repo-server" at 0,1 in argo icon=layers sub="clones + renders"
node api "argocd-server" at 2,1 in argo icon=api sub="API, UI, RBAC, SSO"
node ctrl "application-controller" at 1,2 in argo icon=k8s sub="diff, sync, health"
node redis "Redis" at 0,2 in argo icon=redis sub="manifest cache"
node appset "ApplicationSet ctrl" at 2,2 in argo icon=workflow sub="generates Applications"
node k8s "Kubernetes API" at 1,3 icon=k8s sub="live state (watch)"
git -> repo : "fetch"
user -> api
api ..> ctrl : "refresh / sync"
ctrl -> repo : "render @ commit"
repo .. redis
ctrl <-> k8s : "watch + apply"
appset ..> ctrl : "Application CRs"
```

| Component | Job |
|---|---|
| `argocd-repo-server` | Clones repositories and renders manifests for a given commit: plain YAML, Kustomize, Helm (`helm template`), Jsonnet, or a Config Management Plugin. Stateless, horizontally scalable; results cached by commit |
| `argocd-application-controller` | The reconciler. Keeps a watch-based cache of live cluster objects, diffs them against rendered manifests, runs syncs (apply, prune, hooks, waves) and computes health. Runs as a StatefulSet and can be sharded across clusters |
| `argocd-server` | API and web UI, used by the CLI; enforces RBAC; receives Git webhooks |
| `argocd-applicationset-controller` | Generates many Applications from one template (section 6) |
| Redis | Cache for rendered manifests and cluster state; not a source of truth |
| Dex (optional) | SSO bridge to OIDC, SAML, GitHub, LDAP |
| `argocd-notifications-controller` | Sends Slack, email and webhook notifications on sync and health events |

Argo CD itself is configured declaratively: Applications and AppProjects are Kubernetes
custom resources, and settings live in ConfigMaps (`argocd-cm`, `argocd-rbac-cm`), so
Argo CD can manage its own configuration from Git.

### One reconcile, step by step

1. **Detect.** The controller refreshes each Application on a timer (about every 3
   minutes by default, set by `timeout.reconciliation` in `argocd-cm`) or immediately
   when a Git webhook reaches `argocd-server`. Configure webhooks: without them, "I
   merged, why hasn't it deployed?" means waiting for the next poll. It also reacts to
   *live* changes at once, because it watches the cluster.
2. **Render.** For the Application's `targetRevision` (a branch, tag or commit), the
   repo-server resolves the commit SHA and renders manifests, reusing the cache if that
   commit was already rendered.
3. **Diff.** The controller compares each rendered object with its live counterpart,
   after normalising fields the cluster adds (defaults, status, managed fields) and any
   configured `ignoreDifferences`. Any remaining difference makes the app `OutOfSync`.
4. **Sync** (automatically or on request). Objects are applied in phases and waves
   (section 4): `PreSync` hooks, then the resources ordered by wave and kind (namespaces
   and CRDs first), then `PostSync` hooks. Objects in the cluster that Argo CD tracks but
   Git no longer contains are deleted only if pruning is enabled. The controller applies
   with `kubectl apply` semantics by default (client-side), or Server-Side Apply when the
   `ServerSideApply=true` sync option is set.
5. **Assess health.** Built-in rules know what "healthy" means for common kinds: a
   Deployment is `Progressing` until its rollout completes and `Degraded` if it exceeds
   its progress deadline; a PVC is healthy when bound; an Ingress when it has an address.
   Custom resources get health from Lua scripts (many ship built in, including Argo
   Rollouts). The Application's health is the worst of its resources'.
6. **Report and notify**: status, history (which commit was synced when), events and
   notifications.

**Sync status and health are independent.** `Synced` + `Degraded` means "the cluster
matches Git, and what Git describes is broken" (fix Git). `OutOfSync` + `Healthy` means
"something changed or is pending, but it works" (sync or investigate the drift).

**How Argo CD knows what it owns:** each managed object carries a tracking marker. Argo
CD 3.0 changed the default from the `app.kubernetes.io/instance` label to an annotation
(`argocd.argoproj.io/tracking-id`), which avoids clashes with Helm charts that set that
label themselves.

<div class="lab" data-viz="flow-gitops-reconcile"></div>

## 3. The Application resource

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: checkout-api-prod
  namespace: argocd
  finalizers:
    - resources-finalizer.argocd.argoproj.io   # deleting the app deletes its resources
spec:
  project: payments                            # AppProject: allowed repos, clusters, kinds
  source:
    repoURL: https://github.com/acme/deploy-config.git
    targetRevision: main
    path: apps/checkout-api/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: checkout
  syncPolicy:
    automated:
      prune: true          # delete objects removed from Git
      selfHeal: true       # revert changes made outside Git
    syncOptions:
      - CreateNamespace=true
      - ServerSideApply=true
      - PruneLast=true     # prune only after everything else is healthy
    retry:
      limit: 5
      backoff: { duration: 10s, factor: 2, maxDuration: 3m }
  ignoreDifferences:
    - group: apps
      kind: Deployment
      jsonPointers:
        - /spec/replicas   # the HPA owns replicas; do not fight it
```

Points interviewers probe:

- **`automated` is opt-in**, and `prune` and `selfHeal` are separate opt-ins inside it.
  Many teams enable automated sync with pruning off at first, because a mistaken
  deletion in Git then deletes production objects.
- **`ignoreDifferences`** stops fights with other controllers. If an HPA scales the
  Deployment to 14 and Git says `replicas: 6`, self-heal would reset it to 6 every few
  seconds. Either remove `replicas` from the manifest or ignore that field.
- **AppProjects** are the multi-tenancy boundary: which repositories a team's apps may
  pull from, which clusters and namespaces they may deploy to, and which resource kinds
  they may create (for example, no `ClusterRole`).
- **`targetRevision: main`** tracks a branch; pinning to a tag or commit per environment
  is a common promotion technique (section 5).

## 4. Ordering: sync phases, waves and hooks

Some resources must exist before others: a namespace before its objects, CRDs before
custom resources, a schema migration before the new app version starts. Argo CD orders a
sync with:

- **Phases**: `PreSync` → `Sync` → `PostSync` (plus `SyncFail` if something fails).
  A hook is any resource (usually a Job) annotated `argocd.argoproj.io/hook: PreSync`
  etc.
- **Waves** within a phase: the annotation `argocd.argoproj.io/sync-wave: "-1"` puts a
  resource in an earlier wave (default 0). Argo CD applies one wave, waits for its
  resources to become healthy, then moves on.

```yaml
apiVersion: batch/v1
kind: Job
metadata:
  name: checkout-db-migrate
  annotations:
    argocd.argoproj.io/hook: PreSync
    argocd.argoproj.io/hook-delete-policy: BeforeHookCreation
spec:
  backoffLimit: 0                 # a failed migration fails the sync, no blind retries
  template:
    spec:
      restartPolicy: Never
      containers:
        - name: migrate
          # same image digest as the app it prepares for
          image: ghcr.io/acme/checkout-api@sha256:9f2c4e6d0b1a7c3e5f8d2b4a6c8e0f1d3b5a7c9e1f3d5b7a9c1e3f5d7b9a1c3e
          command: ["/api", "migrate", "up"]
```

If the PreSync Job fails, the sync stops before the new Deployment is applied, which is
exactly what you want. The migration must still be backward compatible with the
currently running version (expand/contract, chapter 05), because a sync can fail *after*
it and leave the old version running against the new schema.

## 5. Repository layout and promotion

### Separate the app repo from the config repo

The common pattern is two repositories (or two top-level folders in a monorepo with
separate permissions):

- **Application repo**: source code, Dockerfile, CI workflow. Merges here produce images.
- **Config (environment) repo**: Kubernetes manifests per app and per environment. Merges
  here change what runs.

Keeping them separate means a code change and a deploy are two auditable events, CI's
commits to the config repo do not re-trigger CI on the app repo, and config repo write
access can be tighter than code access.

```text
deploy-config/
├── apps/
│   └── checkout-api/
│       ├── base/                    # Deployment, Service, HPA, PDB
│       └── overlays/
│           ├── staging/             # kustomization.yaml: image digest, replicas, config
│           └── production/
├── clusters/                        # one folder per cluster: which apps it runs
│   ├── prod-eu-1/
│   └── prod-us-1/
└── platform/                        # ingress controller, cert-manager, monitoring, Argo CD itself
```

**Precision note:** avoid one Git *branch* per environment (`staging` branch,
`production` branch) for configuration. Branches drift apart, merges between them carry
unrelated changes, and differences are hidden in history rather than visible as files.
Folders or overlays per environment on a single branch make differences explicit and
reviewable.

### How a new image version gets into Git

```arch
%% caption: CI builds the image and opens a pull request that bumps the digest in the config repo; merging it is the deploy, and Argo CD does the rest.
grid 170x110
node app "App repo" at 0,0 icon=git sub="code merged"
node ci "CI" at 1,0 icon=workflow sub="build, sign, push"
node reg "Registry" at 2,0 icon=storage sub="image@sha256"
node pr "Config repo PR" at 1,1 icon=git sub="bump staging digest"
node cfg "Config repo" at 2,1 icon=file sub="main branch"
node argo "Argo CD" at 2,2 icon=sync sub="per cluster app"
node prom "Promote PR" at 3,2 icon=check sub="staging to prod"
app -> ci
ci -> reg
ci -> pr : "open PR"
pr -> cfg : "merge"
cfg -> argo : "sync"
argo ..> prom : "staging healthy"
prom:T ..> cfg:R : "merge"
```

| Approach | How | Trade-off |
|---|---|---|
| CI commits or opens a PR | The last CI step runs `kustomize edit set image …@sha256:…` in the config repo | Simple and explicit; CI needs write access to the config repo (a scoped token or GitHub App) |
| Argo CD Image Updater | Watches the registry and writes new tags or digests back to Git (or to the Application) | Hands-off; less explicit, and a moving tag pattern must be chosen carefully |
| Flux image automation | `ImageRepository` + `ImagePolicy` + `ImageUpdateAutomation` commit updates to Git | The Flux equivalent, built in |
| Kargo | Models stages (dev, staging, prod) and promotes "freight" (image + config versions) with verification between stages | Purpose-built promotion on top of Argo CD |

Promotion between environments is then a Git change too: copy the digest from the
staging overlay to the production overlay in a PR, gated by staging health.

## 6. Many apps, many clusters

### App of apps

One parent Application points at a folder full of Application manifests. Syncing the
parent creates every child. It is how a cluster is bootstrapped from one `kubectl apply`.

### ApplicationSets

An ApplicationSet generates Applications from a template and a **generator**: a list,
every cluster registered in Argo CD with certain labels, every folder in a repo
(`git` directories), every open pull request (preview environments), or a matrix of two
generators.

```yaml
apiVersion: argoproj.io/v1alpha1
kind: ApplicationSet
metadata:
  name: checkout-api
  namespace: argocd
spec:
  goTemplate: true
  goTemplateOptions: ["missingkey=error"]
  generators:
    - clusters:
        selector:
          matchLabels:
            env: production        # every prod cluster, including ones added later
  template:
    metadata:
      name: 'checkout-api-{{.name}}'
    spec:
      project: payments
      source:
        repoURL: https://github.com/acme/deploy-config.git
        targetRevision: main
        path: 'apps/checkout-api/overlays/{{index .metadata.labels "region"}}'
      destination:
        server: '{{.server}}'
        namespace: checkout
      syncPolicy:
        automated: { prune: true, selfHeal: true }
```

The ApplicationSet controller also supports a **progressive sync** strategy
(`RollingSync`) that updates generated Applications step by step, for example staging
clusters before production ones.

### Topologies

| Topology | How | Pros | Cons |
|---|---|---|---|
| Hub and spoke | One central Argo CD manages many clusters with stored credentials | One UI, one place for policy | Central blast radius and credential store; controller must be sharded at scale; network reach into every cluster |
| Instance per cluster | Each cluster runs its own Argo CD pulling from Git | Pure pull, no remote credentials, isolated failure | Many instances to upgrade and observe |
| Hybrid / agent-based | Central control plane with a lightweight agent in each cluster (for example Akuity's agent, the argocd-agent project) | Central view with pull-based agents | Newer, more moving parts |

## 7. Secrets in a GitOps world

Plain Kubernetes Secrets must not be committed (base64 is not encryption). Options:

| Approach | What is in Git | How it works |
|---|---|---|
| Sealed Secrets (Bitnami) | A `SealedSecret` encrypted with the cluster controller's public key | Only the in-cluster controller can decrypt it into a Secret; back up the controller's key or DR fails |
| SOPS (with age, PGP or a cloud KMS) | Encrypted YAML values | Decrypted at render time by a plugin (KSOPS, or Flux's native SOPS support) |
| External Secrets Operator | An `ExternalSecret` that *references* a path in Vault, AWS/GCP/Azure secret managers | The operator fetches and refreshes the value; nothing secret is in Git |
| Secrets Store CSI driver | A `SecretProviderClass` reference | Secrets mounted as files directly from the store |

External Secrets Operator is the common default: Git holds only references, rotation
happens in the secret manager, and DR depends on the secret manager, not on a key hidden
in one cluster. See [Secret Management](../Tool-Kit/11_secret_management.md).

## 8. Rollback, drift and other production realities

### Rolling back the GitOps way

- **`git revert` the bad commit** and let the controller sync it. The history now shows
  the bad change and its reversal, and every cluster converges.
- `argocd app rollback` (redeploy a previous synced revision) exists, but Argo CD refuses
  it while automated sync is on, because the next reconcile would re-apply Git anyway.
  The same trap catches people using `kubectl rollout undo`: self-heal promptly puts the
  new version back. In a GitOps system, **Git is the only lever that sticks.**
- For progressive rollouts managed by Argo Rollouts, an automatic abort shifts traffic
  back to stable in seconds, then the Git fix follows (chapter 03).

### Common production problems

| Symptom | Cause | Fix |
|---|---|---|
| App flaps between `Synced` and `OutOfSync` | Another controller or a mutating webhook changes a field Git also sets (HPA replicas, injected sidecars, defaulted fields) | `ignoreDifferences`, remove the field from Git, Server-Side Apply field ownership |
| Deleted a file, production object vanished | Automated prune | Review deletes carefully; `Prune=false` annotation on critical objects; `PruneLast` |
| Merged, nothing happens for minutes | No webhook, waiting for the poll | Configure Git webhooks to `argocd-server` |
| Sync stuck at a wave | A resource in that wave never becomes healthy (a hook Job hanging, missing health check for a CRD) | Timeouts on hooks, custom health checks |
| Huge manifests, slow UI, controller OOM | Thousands of apps on one controller | Shard the application controller, scale repo-servers, split instances |
| Argo CD is down | Controller or API outage | Running workloads are unaffected (it is not in the request path); only deploys and drift correction stop |

### Hardening

- Protect the config repo: required reviews, CODEOWNERS per environment, signed commits
  (Argo CD can require GPG-signed commits per AppProject).
- Least privilege: AppProjects restrict repos, destinations and kinds; SSO with RBAC;
  disable or tightly scope the built-in `admin` account.
- Treat Argo CD's own configuration as GitOps-managed, with its own review path.

## 9. Argo CD vs Flux

Both are CNCF graduated (Flux in November 2022, Argo CD in December 2022) and implement
the same principles.

| | Argo CD | Flux (v2) |
|---|---|---|
| Shape | One application with a UI, API and CLI | A set of composable controllers (source, kustomize, helm, notification, image automation), the "GitOps Toolkit" |
| UI | Rich built-in web UI | None built in; third-party UIs and CLIs |
| Core resource | `Application`, `ApplicationSet`, `AppProject` | `GitRepository`/`OCIRepository`, `Kustomization`, `HelmRelease` |
| Multi-tenancy | AppProjects, SSO and RBAC in Argo CD | Kubernetes RBAC and service account impersonation per Kustomization |
| Helm | Renders with `helm template` and applies as manifests (Helm hooks mapped to Argo hooks) | Runs real Helm releases (history, `helm ls` works) |
| Image automation | Separate Image Updater project | Built-in controllers |
| Progressive delivery companion | Argo Rollouts | Flagger |
| Typical fit | Teams wanting a central UI and app-centric view | Platform teams wanting Kubernetes-native building blocks |

## Common interview questions

**1. What is GitOps, and how is it different from a CI pipeline that runs `kubectl apply`?**
Desired state lives in Git and an agent pulls and continuously reconciles the cluster to
it. A push pipeline applies once, needs cluster credentials in CI and never notices
drift afterwards.

**2. Someone runs `kubectl scale --replicas=10` on a GitOps-managed Deployment. What happens?**
Argo CD sees the live object differ from Git and marks the app `OutOfSync`. With
`selfHeal: true` it re-applies Git and the replicas go back; without it, the change stays
until the next sync. If an HPA owns replicas, the field should be ignored or removed from
Git to avoid a fight.

**3. How do you roll back a bad deploy in a GitOps setup?**
Revert the commit in Git and let it sync (or let a progressive delivery controller abort
first). Imperative rollbacks are undone by self-heal, and Argo CD blocks its own rollback
command while auto-sync is on.

**4. Is GitOps more secure than push?**
It removes cluster credentials from CI and gives a full audit trail, but it makes the
config repository the control point: whoever can merge there can change production, so
it needs branch protection, reviews and signed commits. A central Argo CD that holds other
clusters' credentials is also sensitive.

**5. How do you run a database migration before the new version starts?**
A `PreSync` hook Job (or an earlier sync wave) using the same image digest; if it fails,
the sync stops. The migration must be backward compatible with the running version.

**6. How do you manage one app across 30 clusters?**
An ApplicationSet with a cluster generator selecting by labels, a per-region overlay
path, automated sync, and a progressive strategy so production clusters update after
staging ones.

**7. How do secrets work with GitOps?**
Never commit plain Secrets. Commit encrypted forms (Sealed Secrets, SOPS) or references
(External Secrets Operator pulling from Vault or a cloud secret manager).

**8. Argo CD vs Flux?**
Same principles; Argo CD is a single product with a strong UI and app-centric model plus
Argo Rollouts; Flux is a toolkit of controllers with native Helm releases, built-in image
automation and Flagger.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| Student/Intern | Intern | Intern | Desired vs actual state; that GitOps means "deploy by merging to Git" and an agent keeps the cluster matching it |
| Junior (L3) | Software Engineer / New Grad | L3 | Reads the Argo CD UI (sync vs health status); ships a change by PR to the config repo; knows not to `kubectl edit` production and why a manual change gets reverted |
| Mid (L4) | Software Engineer II | L4 | Writes Applications and Kustomize overlays; configures automated sync, prune, self-heal and `ignoreDifferences`; uses hooks and waves for migrations; rolls back by revert |
| Senior (L5) | Senior Software Engineer | L5 | Designs repo layout and promotion flow; chooses image-update automation; handles secrets with ESO or SOPS; explains the security model precisely (config repo as control point); debugs sync loops and stuck waves |
| Staff+ (L6+) | Staff / Principal Engineer | L6–L7+ | Chooses topology (hub-and-spoke vs per-cluster) and tooling (Argo CD vs Flux) for a fleet; sets AppProject tenancy, sharding and DR strategy (including what Git cannot restore); integrates GitOps with progressive delivery and policy enforcement across the organisation |

## Interview checklist

- [ ] I can state the four OpenGitOps principles and the thermostat-style reconcile loop.
- [ ] I can compare push and pull deployment, including where the credentials and the risk move.
- [ ] I can name Argo CD's components and what each does.
- [ ] I can walk through one reconcile: detect (poll or webhook), render, diff, sync, health.
- [ ] I can explain sync status vs health status, with an example of `Synced` + `Degraded`.
- [ ] I can explain automated sync, prune and self-heal, and that self-heal is opt-in.
- [ ] I can use `ignoreDifferences` to stop fights with an HPA or mutating webhook.
- [ ] I can order resources with sync waves and run a migration as a `PreSync` hook.
- [ ] I can design a config repo layout and an image promotion flow, and explain why not branch-per-environment.
- [ ] I can manage many clusters with ApplicationSets and compare hub-and-spoke with per-cluster instances.
- [ ] I can handle secrets with Sealed Secrets, SOPS or External Secrets Operator.
- [ ] I can explain why rollback in GitOps is `git revert`, and what GitOps cannot restore in DR.

Related: [Continuous Deployment (CD) and Delivery](02_cd_and_delivery.md) (push vs pull in context), [Deployment Strategies](03_deployment_strategies.md)
(Argo Rollouts), [Kubernetes and Orchestration](../Tool-Kit/02_kubernetes_and_helm.md), [Infrastructure as Code (IaC)](../Tool-Kit/08_infrastructure_as_code.md),
[Secret Management](../Tool-Kit/11_secret_management.md), [Platform and Infrastructure](../../interview-core/SystemDesign/building_blocks/16_platform_and_infra.md).
