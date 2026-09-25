# 009 — Design Search and Autocomplete

Design search and autocomplete over a product catalog, supporting filters, typo tolerance, and relevance ranking.

## Functional requirements

- A user searches by free-text query and gets relevance-ranked results.
- Results can be filtered by structured attributes (e.g., category, price range).
- The system tolerates minor typos and returns useful results anyway.
- An autocomplete/prefix endpoint suggests queries as the user types.
- Results respect per-user authorization (e.g., hidden or region-restricted products).
- Newly added or updated products become searchable within a few minutes.

## Constraints to assume

- Tens of millions of catalog items.
- Search query latency under 150 ms p99; autocomplete under 50 ms p99.
- Index freshness within five minutes of a catalog update.
- Peak query volume in the tens of thousands of QPS.
- Typo tolerance for at least one-character edits on common queries.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Indexing strategy (inverted index, prefix structure) and freshness/update pipeline.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
