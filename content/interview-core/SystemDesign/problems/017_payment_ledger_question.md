# 017 — Design a Payment Ledger

Design an internal ledger service that moves money between accounts with exact balances and an immutable audit trail.

## Functional requirements

- A client requests a transfer between two internal accounts, which either fully succeeds or fully fails.
- Every balance change is recorded as an immutable, append-only entry that can reconstruct any account's history.
- The same transfer request submitted twice (e.g. due to a client retry) must never be applied twice.
- External settlement events (e.g. a bank correction) can be applied after the fact and reconciled against internal balances.
- Operators can run reconciliation reports comparing ledger totals against external statements.
- Account balances are always queryable with strong consistency.

## Constraints to assume

- 20,000 transfers/second at peak.
- 500 million accounts, balances in fixed-point currency units (no floating point).
- Transfer p99 under 200 ms end-to-end.
- Zero tolerance for double-applied or lost transfers; entries retained indefinitely.
- Reconciliation runs complete within 1 hour of end-of-day close.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Idempotency and double-entry consistency strategy preventing duplicate or partial transfers.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
