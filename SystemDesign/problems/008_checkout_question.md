# 008 — Design a Checkout System

Design a checkout flow that reserves inventory, charges payment, and creates a confirmed order without double-charging or overselling.

## Functional requirements

- A user checks out a cart, reserving inventory for the items.
- Payment is charged through a third-party provider.
- A confirmed order is created only after successful payment and inventory reservation.
- The user sees an order confirmation with consistent state.
- Late or duplicate payment-provider callbacks must not cause a double charge or duplicate order.
- Inventory and payment state are reconciled if either step fails partway.

## Constraints to assume

- Tens of thousands of checkouts/minute at peak (e.g., flash sale).
- Payment provider callback latency ranges from milliseconds to tens of seconds, occasionally duplicated.
- Checkout end-to-end latency under 3 seconds p99 for the happy path.
- Zero tolerance for double charges; near-zero tolerance for oversell.
- Reconciliation of stuck/partial orders completes within minutes.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Idempotency and distributed-transaction strategy across inventory, payment, and order.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
