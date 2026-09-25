# 014 — Design a Logging Platform

Design a centralized logging platform that collects and makes searchable the logs emitted by thousands of services.

## Functional requirements

- Services stream structured and unstructured log lines continuously to the platform.
- Users search logs by time range, service, and trace ID, and view them in correlated order.
- Ingestion must survive a slow or unavailable search/storage backend without dropping or blocking callers.
- Retention varies by service or tenant (e.g. 7 days for debug logs, 1 year for audit logs).
- Sensitive fields (PII, secrets) must be detected/redacted before they are durably stored or searchable.
- Operators can tail live logs for a given service.

## Constraints to assume

- 3,000 services emitting 2 million log lines/second at peak.
- Search query p99 under 2 seconds for a 1-hour window across one service.
- Ingest must tolerate a 10-minute backend outage without data loss.
- Retention configurable from 7 days to 1 year per source.
- Redaction must complete before data is queryable.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Buffering/backpressure strategy so ingestion survives backend slowdown without loss or blocking.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
