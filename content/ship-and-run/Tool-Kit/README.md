# Backend Tool-Kit

This module is a hands-on guide to the backend and infrastructure tools you use every day
in production: containers, Kubernetes, Git and CI, event streaming and message brokers,
observability, Linux, infrastructure as code, proxies, load testing, secrets and service
meshes. The `SystemDesign` module covers *why* systems use these building blocks; this
module covers *how* they work inside and how to operate, configure and debug them. Each
chapter starts from zero in a Foundations section and goes to the depth a Senior (L5)
interview or an on-call shift expects.

## Who it is for

- **Students and new grads** who have used none of these tools: read each chapter's
  Foundations section first, and run the commands.
- **Working engineers** preparing for interviews: go straight to the numbered sections,
  the "Common interview questions" and the interview checklist at the end of each
  chapter.
- **Senior engineers** filling gaps: each chapter's "What Each Engineering Level Should
  Know" table shows what separates L4, L5 and Staff+ answers.

## Prerequisites

Comfort with a terminal and one backend language (Python or Go examples appear
throughout), and basic networking and OS vocabulary. If "process", "namespace" or "TCP
connection" are fuzzy, read [Operating Systems & Hardware Symbiosis](../../interview-core/CSFundamentals/01_operating_systems_deep_dive.md) and
[Networking & Distributed Communication](../../interview-core/CSFundamentals/02_networking_deep_dive.md) first.

## Reading order

The chapters are ordered so each builds on the ones before it. Chapters 01–02 (containers,
then orchestration) and 04–05 (streams, then brokers) are pairs; read each pair in order.

| # | Chapter | What you will be able to do |
|---|---|---|
| 01 | [Docker and Containerization](01_docker_and_containers.md) | Explain containers as namespaces + cgroups + layered images; write fast, small, secure multi-stage Dockerfiles; debug exit codes, networking and storage |
| 02 | [Kubernetes and Orchestration (with Helm)](02_kubernetes_and_helm.md) | Narrate `kubectl apply` through the control plane; set requests, probes and rollouts for zero-downtime deploys; debug every common Pod status; package with Helm (includes a live rolling-update flow) |
| 03 | [Git and GitHub Workflows](03_git_and_github_workflows.md) | Use Git's object model to merge, rebase and recover confidently; choose branching strategies; protect `main`; write and secure GitHub Actions |
| 04 | [Kafka and Event Streaming](04_kafka_and_event_streaming.md) | Design topics, keys and partitions; configure for no data loss; run consumer groups and handle rebalances; reason about delivery semantics (includes a live consumer-group rebalance flow) |
| 05 | [RabbitMQ and Message Brokers](05_rabbitmq_and_message_brokers.md) | Route with exchanges; build reliable task queues with confirms, acks, prefetch, quorum queues, DLQs and delayed retries; choose between brokers |
| 06 | [Observability: Prometheus, Grafana, OpenTelemetry](06_observability_and_monitoring.md) | Instrument services with metrics, logs and traces; write PromQL; define SLOs and burn-rate alerts; debug from alert to trace to log |
| 07 | [CLI and Linux System Mastery](07_cli_and_linux_mastery.md) | Work fluently in the shell and diagnose a Linux host |
| 08 | [Infrastructure as Code (Terraform & Ansible)](08_infrastructure_as_code.md) | Provision and configure infrastructure declaratively and safely |
| 09 | [Web Servers & Proxies (Nginx & Envoy)](09_web_servers_and_proxies.md) | Configure reverse proxies, TLS termination and load balancing |
| 10 | [Performance and Load Testing](10_performance_and_load_testing.md) | Plan and run load tests and read the results correctly |
| 11 | [Secret Management](11_secret_management.md) | Keep credentials out of code, images and Git, and rotate them |
| 12 | [Service Mesh](12_service_mesh.md) | Explain what a mesh adds (mTLS, traffic policy, telemetry) and when it is worth it |

## Related modules

- `content/interview-core/SystemDesign/building_blocks/` — the design-level view of the same tools, especially
  [Messaging and Streaming](../../interview-core/SystemDesign/building_blocks/09_messaging_and_streaming.md), [Observability and Reliability](../../interview-core/SystemDesign/building_blocks/15_observability_and_reliability.md),
  [Platform and Infrastructure](../../interview-core/SystemDesign/building_blocks/16_platform_and_infra.md) and [Distributed Log Internals](../../interview-core/SystemDesign/building_blocks/26_distributed_log_internals.md).
- `content/ship-and-run/CICD/` — pipelines, deployment strategies, GitOps with Argo CD, feature flags.
- `content/ship-and-run/TestingAndQuality/` — testing pyramid, integration tests with containers, chaos
  engineering.
- `content/ship-and-run/DataEngineering/` — stream processing on top of Kafka, orchestration.
- `content/interview-core/CSFundamentals/` — the OS and networking foundations these tools are built on.
