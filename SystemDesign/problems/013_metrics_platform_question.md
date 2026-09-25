# 013 — Design a Metrics Platform

Design a time-series metrics platform that ingests numeric samples from many services, and supports querying and alerting on them.

## Functional requirements

- Services emit metric samples (name, tags, value, timestamp) continuously.
- Users query metrics over arbitrary time ranges with aggregation (sum, avg, percentile) grouped by tags.
- Users define alert rules that evaluate continuously and fire notifications.
- Old raw data is downsampled and eventually expired per a retention policy.
- The system must protect itself from a tenant emitting unbounded label cardinality.
- Dashboards refresh with near-real-time data.

## Constraints to assume

- 5 million samples/second ingest at peak.
- 10,000 tenants, retention 13 months raw at 1-minute resolution, downsampled after 7 days.
- Query p99 under 500 ms for a 24-hour window.
- Alert evaluation lag under 30 seconds from data arrival.
- A single tenant's label cardinality must not degrade other tenants.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Cardinality-control and downsampling strategy for high-cardinality tenant labels.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
