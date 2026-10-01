# CI/CD & Deployment Strategies

This module covers the automation that moves code from a developer's laptop to
production safely, quickly and repeatably: continuous integration, continuous delivery
and deployment, zero-downtime rollout strategies, GitOps with Argo CD, and the feature
flags and rollback discipline that make failures cheap.

## Who it is for

- **You are new to CI/CD**: every chapter opens with a plain-language **Foundations**
  section that explains the problem, the pieces and an everyday example before any YAML.
- **You are preparing for a mid-level to Staff interview**: the numbered sections go into
  mechanics (merge queues, `maxSurge` arithmetic, canary analysis, the Argo CD reconcile
  loop, expand/contract migrations), with current tooling, real config, failure modes and
  **Precision notes** where a common simplification is wrong. Each chapter ends with model
  answers to common interview questions, a "What Each Engineering Level Should Know" table
  and an interview checklist.

## Read in this order

1. [Continuous Integration (CI) Fundamentals](01_ci_fundamentals.md): why teams merge
   often, pipeline design and ordering, GitHub Actions in depth, merge queues, fast
   pipelines, flaky tests, hermetic builds and CI supply-chain security.
2. [Continuous Deployment (CD) and Delivery](02_cd_and_delivery.md): delivery vs
   deployment, environment promotion, build once / deploy by digest, config and secrets
   injection, signing and provenance, deploy-time safety checks, DORA metrics.
3. [Deployment Strategies](03_deployment_strategies.md): recreate, rolling updates,
   blue/green, canary with automated analysis (Argo Rollouts), shadow traffic, and the
   compatibility rules for running two versions at once. Includes the live flow
   *canary promoted, aborted, or paused by analysis*.
4. [GitOps and Argo CD](04_gitops_and_argocd.md): push vs pull, Argo CD architecture
   and the reconcile loop, sync and health, hooks and waves, repo layout and promotion,
   ApplicationSets, secrets, rollback by revert, Argo CD vs Flux. Includes the live flow
   *the GitOps reconcile loop*.
5. [Feature Flags and Rollbacks](05_feature_flags_and_rollbacks.md): deploy vs release,
   kinds of flags, deterministic percentage rollouts (runnable Python), flag debt,
   rollback vs roll forward, what `rollout undo` really reverts, and expand/contract for
   database changes.

Chapters 01 → 02 → 03 build on each other; 04 and 05 can be read in either order after 03.

## Prerequisites

- Basic Git (commits, branches, pull requests): [Git and GitHub Workflows](../Tool-Kit/03_git_and_github_workflows.md).
- What a container image is: [Docker and Containerization](../Tool-Kit/01_docker_and_containers.md).
- Kubernetes basics (Pod, Deployment, Service): [Kubernetes and Orchestration](../Tool-Kit/02_kubernetes_and_helm.md).

## Related modules

- `TestingAndQuality/`: what goes into the test stages of a pipeline.
- [Infrastructure as Code (IaC)](../Tool-Kit/08_infrastructure_as_code.md), [Secret Management](../Tool-Kit/11_secret_management.md),
  [Service Mesh (Istio / Linkerd)](../Tool-Kit/12_service_mesh.md): the infrastructure the pipeline deploys onto.
- [Platform and Infrastructure](../SystemDesign/building_blocks/16_platform_and_infra.md) and
  [Observability and Reliability](../SystemDesign/building_blocks/15_observability_and_reliability.md): platform and SLO
  context.
- [Feature Flags](../SystemDesign/solutions/019_feature_flags_solution.md): designing a feature flag
  platform at scale.
- [Schema Migrations](../SQL/12_schema_migrations.md): zero-downtime schema changes in Postgres.
