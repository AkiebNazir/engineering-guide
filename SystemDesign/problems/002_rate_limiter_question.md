# 002 — Design a Rate Limiter

Design <abbr title="Application Programming Interface">API</abbr> quotas that cap requests per <abbr title="Application Programming Interface">API</abbr> key, absorb controlled bursts, and protect checkout traffic under load.

## Functional requirements

- Each <abbr title="Application Programming Interface">API</abbr> key is limited to 100 requests/minute.
- Short bursts above the steady rate are allowed within a bounded window.
- Different routes and tenants can have different policies.
- Callers receive a clear signal (status code and retry hint) when throttled.
- Checkout must keep working in a safe degraded mode even if the limiter is impaired.
- Limits apply consistently across many stateless <abbr title="Application Programming Interface">API</abbr> servers.

## Constraints to assume

- Millions of distinct <abbr title="Application Programming Interface">API</abbr> keys.
- Tens of thousands of requests/second at peak across the fleet.
- Limiter decision added latency under 5 ms p99.
- Limiter state check must not become a single point of failure.
- Policy changes should roll out within one minute.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Algorithm choice (token bucket vs sliding window) and failure-mode policy per route.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
