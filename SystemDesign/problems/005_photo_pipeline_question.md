# 005 — Design a Photo Pipeline

Design a service that ingests user photo uploads, processes them into variants, and serves them globally.

## Functional requirements

- A user uploads a photo up to 50 MB, resumable if the connection drops.
- The system scans uploads (e.g., malware/content checks) before publishing.
- The system generates derivative variants (thumbnails, resized versions).
- The user can see processing status (uploading, processing, ready, failed).
- Processed photos are served with low latency worldwide.
- Deleting a photo removes the original and all derivatives, including from caches.

## Constraints to assume

- 50 MB max upload size, resumable uploads for flaky connections.
- Tens of millions of uploads/day at peak.
- Variant generation completes within seconds for most photos p99.
- Global read latency under 200 ms p99.
- Deletion must propagate to all derivatives and edges within an hour.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Upload/resume and async processing pipeline strategy.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
