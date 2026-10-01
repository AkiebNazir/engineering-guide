# 021 — Design a Multi-Tenant API Gateway

Design an API gateway that routes and versions hundreds of internal APIs for many tenants while protecting backends from abuse.

## Functional requirements

- The gateway routes incoming requests to the correct backend service and API version based on path/host/header.
- Each request is authenticated and authorized before reaching a backend.
- Each tenant has an enforced quota/rate limit, isolated from other tenants' usage.
- A tracing/correlation ID is propagated end-to-end for every request.
- A single abusive or misbehaving tenant must not degrade latency or availability for other tenants.
- Operators can roll out a new API version or route change without downtime.

## Constraints to assume

- 500,000 requests/second across all tenants at peak.
- 800 tenants, 300 distinct backend APIs, 3 concurrent versions each on average.
- Added gateway latency p99 under 10 ms.
- Per-tenant quota enforcement accurate within a 1-second window.
- Zero-downtime route/version changes.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Rate-limiting and tenant-isolation strategy that contains a single abusive tenant.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
