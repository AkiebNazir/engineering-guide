# 003 — Design a Pastebin

Design a service that lets users create and read text snippets, with optional expiry and visibility controls.

## Functional requirements

- A user creates a snippet and receives a shareable link.
- Snippets can be public, unlisted, or private to the owner.
- Snippets can be given an expiration time after which they are no longer readable.
- Anyone with the link can read a public or unlisted snippet; private ones require auth.
- Reads must stay fast globally, including for large snippets.
- Owner can delete a snippet before its expiry.

## Constraints to assume

- Reads outnumber writes 1,000:1.
- Snippets range up to 10 MB.
- Read p99 under 150 ms from any region.
- Expired snippets become unreadable within a few minutes of expiry.
- Snippet content is durable until deleted or expired.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Storage and CDN/edge strategy for large snippets and global fast reads.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
