# 025 — Design a Web Search Engine

Design the crawl, index, and serve pipeline for a general web search engine: a user types a query and gets the ten most relevant pages from billions of documents in a fraction of a second.

## Functional requirements

- Crawl the public web continuously, respecting robots.txt and site politeness.
- Build and maintain an index that supports keyword queries with relevance ranking.
- Return the top 10 results with title, URL, and snippet for a query.
- New and changed pages appear in results: news within minutes, most pages within days.
- Remove pages that disappear or must be taken down (legal, safety) promptly.

## Constraints to assume

- 50 billion pages indexed; average page 100 KB of HTML, 10 KB of extracted text.
- 100,000 queries per second at peak, globally.
- p99 query latency under 300 ms end to end.
- Crawl capacity of several billion fetches per day.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope estimates: crawl rate, index size, and query fan-out.
3. The main interfaces between crawl, indexing, and serving.
4. Baseline architecture for the three pipelines and how data flows between them.
5. Index sharding, query fan-out and merging, and controlling tail latency.
6. Ranking stages, freshness, duplicate detection, and caching of popular queries.
7. One explicit trade-off you would revisit between index freshness and serving cost.

Do not open the solution until you have made and explained your own design.
