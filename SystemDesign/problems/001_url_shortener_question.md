# 001 — Design a URL Shortener

Design a service that creates short links such as `https://sho.rt/aZ8k2P` and redirects visitors to the original URL.

## Functional requirements

- A signed-in user creates a short link for a long URL.
- Anyone opening a short link is redirected to the destination.
- Optional custom aliases such as `sho.rt/summer-sale` are supported.
- Click analytics are useful but must not delay redirect.
- Link owner can disable a link.

## Constraints to assume

- 100 million new links/month.
- 10 billion redirects/month.
- 100:1 redirect:create ratio.
- Redirect p99 under 100 ms in the primary region.
- Links are durable; analytics may appear within five minutes.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. ID/short-code strategy and collision/custom-alias handling.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
