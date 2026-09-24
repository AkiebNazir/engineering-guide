# 028 — Design Top-K Trending (YouTube Trending / Twitter Trends)

Design a service that shows the top 100 trending items — videos, hashtags, or search queries — globally and per country, over the last hour and the last day.

## Functional requirements

- Return the top K (K ≤ 100) items by event count for a time window: last 5 minutes, last hour, last 24 hours.
- Support slicing by country and by category.
- Update results at least every minute.
- "Trending" should favour items whose activity is rising, not only items that are always popular (nice to have).
- Exclude spam and manipulated activity.

## Constraints to assume

- 5 billion view/use events per day across 1 billion distinct items; heavy power-law distribution.
- Peak ingest 300,000 events per second.
- Top-K reads: 20,000 requests per second, p99 under 50 ms.
- An approximate ranking is acceptable if the error is small and bounded.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope estimates: event rate, distinct keys per window, memory for exact vs approximate counting.
3. API contract for reading top-K results.
4. Baseline architecture: ingestion, counting, windowing, serving.
5. Counting at scale: exact vs count-min sketch + heap, merging across servers.
6. Sliding windows, trend scoring, slicing by dimension, and abuse filtering.
7. One explicit trade-off you would revisit if exact counts were required.

Do not open the solution until you have made and explained your own design.
