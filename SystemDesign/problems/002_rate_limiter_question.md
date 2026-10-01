# 002 — Design a Rate Limiter

Design API quotas that cap requests per API key, absorb controlled bursts, and protect checkout traffic under load.

## Functional requirements

- Each API key is limited to 100 requests/minute.
- Short bursts above the steady rate are allowed within a bounded window.
- Different routes and tenants can have different policies.
- Callers receive a clear signal (status code and retry hint) when throttled.
- Checkout must keep working in a safe degraded mode even if the limiter is impaired.
- Limits apply consistently across many stateless API servers.

## Constraints to assume

- Millions of distinct API keys.
- Tens of thousands of requests/second at peak across the fleet.
- Limiter decision added latency under 5 ms p99.
- Limiter state check must not become a single point of failure.
- Policy changes should roll out within one minute.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Algorithm choice (token bucket vs sliding window) and failure-mode policy per route.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
