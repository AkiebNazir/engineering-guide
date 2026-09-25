# Platform and Infrastructure

This file covers the userspace-visible packaging and orchestration layer: containers, Kubernetes, service mesh, eBPF, and delivery tooling. It sits directly on top of the <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>-level primitives (processes, cgroups, namespaces) covered in `01_operating_systems.md` — read that first if the process/kernel mechanics underneath containers are unclear; this file does not repeat that detail.

## Containers vs VMs

| | <abbr title="Virtual Machine. The virtualization/emulation of a computer system.">VM</abbr> | Container |
|---|---|---|
| Isolation unit | Full guest <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr> + kernel per <abbr title="Virtual Machine. The virtualization/emulation of a computer system.">VM</abbr>. | Process(es) sharing the host kernel, isolated via namespaces/cgroups. |
| Startup time | Seconds to minutes (boots a kernel). | Milliseconds to seconds (starts a process). |
| Density | Fewer per host (each carries a full <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>). | Many per host (shared kernel overhead only). |
| Isolation strength | Stronger — separate kernel. | Weaker by default — shared kernel is a shared attack surface. |
| What it packages | An entire machine. | A process and its dependencies (the exact bytes it needs to run, not a whole <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>). |

A container is not a <abbr title="Virtual Machine. The virtualization/emulation of a computer system.">VM</abbr> and not a security boundary by itself — it is dependency packaging plus <abbr title="Operating System. System software that manages computer hardware, software resources, and provides common services for computer programs.">OS</abbr>-level isolation primitives. Do not treat "it's containerized" as equivalent to "it's sandboxed against a hostile workload"; that guarantee needs additional controls (gVisor/Kata-style stronger isolation, seccomp profiles, non-root users, read-only filesystems) on top of the base container.

## Kubernetes core concepts

| Concept | Problem it solves |
|---|---|
| Pod | Smallest deployable unit — one or more tightly-coupled containers that must be scheduled, scaled, and networked together. |
| Deployment | Declarative rollout and self-healing for stateless replicas — desired replica count is continuously reconciled. |
| StatefulSet | Stable network identity and stable storage per replica, for workloads that aren't interchangeable (a DB node, not a stateless web server). |
| Service | A stable virtual <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>/<abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> name that load-balances across a changing set of pod IPs — pods come and go, the Service address doesn't. |
| Ingress / Gateway | External <abbr title="Hypertext Transfer Protocol - The foundation of data communication for the World Wide Web, operating on a client-server model.">HTTP</abbr>(S) routing into the cluster, with host/path rules, without a load balancer per service. |
| ConfigMap / Secret | Externalizes configuration from the container image so the same image runs in every environment; Secret still needs real access control — it is not encryption by default. |
| Namespace | Logical partition of a cluster for multi-team/multi-env isolation of names and RBAC scope. |
| Requests/limits | Tells the scheduler how much <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>/memory a pod needs (request) and caps what it can consume (limit) — prevents one workload from starving others on a shared node. |
| HPA (Horizontal Pod Autoscaler) | Adjusts replica count from a metric (<abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>, custom queue-depth metric) instead of a human watching a dashboard. |
| Liveness/readiness/startup probes | Distinguishes "restart this container" (liveness) from "stop sending it traffic but don't restart it" (readiness) from "still starting, don't do either yet" (startup) — conflating these causes either premature traffic or unnecessary restarts. |

## When Kubernetes is actually justified

Kubernetes is a good answer when an organization already has multiple teams, multiple services, and enough operational complexity (varied scaling needs, multi-environment consistency, a platform team to own it) that the orchestration primitives pay for themselves. For a small team shipping one or a handful of services, a managed application/container platform (a managed container-as-a-service offering, a PaaS) is usually the better first operational choice — it gets the same "don't hand-manage servers" benefit without the cluster's own operational surface (upgrades, RBAC, networking CNI choices, etcd health) becoming a second product to run. Reaching for Kubernetes because it's the default system-design-interview answer, without the team/scale to justify it, is a tell, not a strength.

## Service mesh

A service mesh adds a uniform layer of service-to-service traffic policy, mutual <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr>, retries/timeouts at the network layer, and telemetry — implemented via sidecar proxies (or increasingly, node-level/eBPF-based dataplanes) rather than per-service library code.

```text
service A ── proxy ⇄ proxy ── service B
             (mTLS, retry/timeout
              policy, telemetry)
```

What it buys: consistent security and traffic controls applied at the infra layer instead of reimplemented in every service's application code, across languages.

What it costs: added latency per hop (proxy in the path), a new debugging surface (is the failure in my code or in the mesh's policy), and real operational complexity to run correctly. Critically, a service mesh does not replace application-level timeouts and idempotency — mesh-level retries on a non-idempotent operation cause the exact same duplicate-side-effect bug that application-level retries would, just relocated to infrastructure you don't control as directly.

## eBPF

eBPF runs small, verified programs inside the Linux kernel at defined hook points, without writing a kernel module. It is increasingly used for low-overhead networking (mesh dataplanes that skip a userspace proxy hop), observability (capturing syscalls/network events with far less overhead than traditional agents), and security enforcement. Know what it is and why it's attractive (near-zero overhead compared to userspace instrumentation), but it is not something to reach for as a default interview answer — it is a specialized platform capability that shows up when you already have a large fleet and a dedicated platform team optimizing tail overhead, not a starting design choice.

## IaC, GitOps, and progressive delivery

| Practice | What it buys | What it does not replace |
|---|---|---|
| Infrastructure as Code (IaC) | Provisioned resources defined in reviewable, versioned files instead of manual console clicks — repeatable, diffable, auditable changes. | A tested backup/restore plan — IaC recreates infrastructure shape, not lost data. |
| GitOps | Desired state lives in Git; a controller continuously reconciles the live system to match it, giving a clear audit trail and rollback-by-revert. | Correct application-level rollback semantics (schema/data migrations don't revert just because config does). |
| Progressive delivery | Releases to a small cohort first, watches guardrail metrics, then expands — bounds the blast radius of a bad deploy. | A rollback plan for the cohort that already got the bad version, or for state changes that already happened. |

Each of these reduces operational risk and human error. None of them substitutes for the two things that actually save you during a real incident: a backup you have restored and verified, and a rollback path you have actually exercised before you need it under pressure.

## Related building blocks

- [01_operating_systems.md](01_operating_systems.md) — the cgroups/namespaces primitives containers are built from.
- [13_scaling_and_load_balancing.md](13_scaling_and_load_balancing.md) — HPA and autoscaling triggers tie directly into this file's Kubernetes section.
- [15_observability_and_reliability.md](15_observability_and_reliability.md) — service mesh telemetry and eBPF observability feed the signals covered there.
