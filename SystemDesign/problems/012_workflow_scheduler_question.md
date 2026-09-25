# 012 — Design a Workflow Scheduler

Design a service that runs scheduled and multi-day jobs made of dependent steps, with retries and human approval gates.

## Functional requirements

- A user defines a workflow as an ordered/dependent set of steps, some automated and some requiring human approval.
- Workflows can be scheduled for a future time or run immediately.
- Failed steps retry with backoff up to a configured limit before the workflow is marked failed.
- A worker that crashes mid-step must not cause the step to be lost or run twice.
- Users can inspect the live status and history of any workflow run.
- Long-running workflows may span multiple days waiting on approval or external signals.

## Constraints to assume

- 1 million workflow runs/day, average 8 steps each.
- 5,000 workflows active concurrently at peak.
- Step dispatch latency p99 under 2 seconds from ready to picked-up.
- No concurrent duplicate execution of the same step, ever.
- Workflow state durable for at least 1 year for audit.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Lease/fencing strategy and idempotent-step policy for worker crash recovery.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
