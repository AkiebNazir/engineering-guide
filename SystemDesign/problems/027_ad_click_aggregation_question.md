# 027 — Design an Ad Click Aggregation System

Design the system that counts ad clicks in real time for advertiser dashboards and budget pacing, and produces accurate counts for billing.

## Functional requirements

- Ingest click events from ad servers and client beacons worldwide.
- Show advertisers clicks per ad per minute, with dashboards updated within about a minute.
- Stop serving an ad within a few seconds of its campaign exhausting its daily budget.
- Produce final, accurate click counts per ad per hour for billing.
- Filter invalid traffic (bots, duplicate clicks, click fraud) before billing.
- Support queries by ad, campaign, advertiser, country, and device over the last 90 days.

## Constraints to assume

- 1 billion clicks per day; 5× peak-to-average ratio.
- 10 million active ads.
- Events can arrive late: mobile clients batch and may be offline for hours.
- Billing counts must not double-count and must be reproducible for audits.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope estimates: event rate, storage, and aggregate cardinality.
3. Event schema and query <abbr title="Application Programming Interface">API</abbr>.
4. Baseline architecture for ingestion, stream aggregation, and storage.
5. Windowing, watermarks, late events, and exactly-once counting.
6. Deduplication, fraud filtering, batch reconciliation for billing, and failure handling.
7. One explicit trade-off you would revisit between dashboard freshness and billing accuracy.

Do not open the solution until you have made and explained your own design.
