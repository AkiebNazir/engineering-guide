# 011 — Design a Web Crawler

Design a crawler that discovers and fetches billions of public URLs while respecting site politeness rules.

## Functional requirements

- The crawler discovers new URLs by following links from fetched pages.
- The crawler respects robots.txt and per-site politeness (rate limits, crawl-delay).
- The same URL is not fetched redundantly in short succession (URL dedup).
- Near-duplicate content across different URLs is detected and deduplicated.
- Pages are prioritized for recrawl based on estimated change frequency and importance.
- Fetched content is handed off for downstream indexing.

## Constraints to assume

- Billions of URLs in the frontier over time.
- Politeness limit of roughly one request per host every few seconds by default.
- Crawl throughput in the thousands of pages/second in aggregate.
- Recrawl priority recalculated at least daily for high-value pages.
- Storage and dedup indexes must scale to tens of billions of entries.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. URL frontier, politeness scheduling, and dedup (URL and content) strategy.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
