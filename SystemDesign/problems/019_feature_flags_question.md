# 019 — Design a Feature Flag System

Design a feature flag platform that lets services evaluate flags with very low latency, even during a control-plane outage.

## Functional requirements

- An operator creates a flag and targets it at a percentage rollout, specific users, or attribute-based rules.
- Application SDKs evaluate a flag for the current user/request locally, without a network call per evaluation.
- An operator can instantly kill-switch a flag to force it off everywhere.
- SDKs receive flag config updates and keep working with a last-known-good config if the control plane is unreachable.
- Every flag change is audit-logged with who, what, and when.

## Constraints to assume

- 50 billion flag evaluations/day across all services.
- 10,000 flags, 5,000 services consuming them.
- Evaluation latency p99 under 1 ms (local, no network round trip).
- Kill-switch propagation to all SDKs under 10 seconds.
- SDKs must keep serving a stale-but-valid config for at least 1 hour of control-plane outage.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Config-distribution and staleness policy for SDKs during a control-plane outage.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
