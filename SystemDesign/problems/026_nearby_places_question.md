# 026 — Design Nearby Places Search (Google Maps / Yelp)

Design a service that answers "show me coffee shops within 2 km of me", with business pages, ratings, and a map, for users anywhere in the world.

## Functional requirements

- Search for places near a location, filtered by category or keyword, within a radius or the visible map area.
- Results ranked by a mix of distance, rating, popularity, and open-now status.
- View a place page: details, photos, reviews, opening hours.
- Business owners add and update places; updates appear within minutes.
- Show results as pins on the map at different zoom levels.

## Constraints to assume

- 200 million places worldwide; 100 million daily active users.
- 50,000 nearby-search queries per second at peak, heavily concentrated in dense cities.
- Search p99 under 200 ms.
- Place writes are rare: about 1 million updates per day.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope estimates: index size, read QPS per region, and write rate.
3. API contract for search and place details.
4. Baseline architecture and read/write flows.
5. Geospatial indexing: geohash vs quadtree vs S2 cells, boundaries, and dense-area handling.
6. Ranking, caching, sharding by geography, and map tile/pin serving.
7. One explicit trade-off you would revisit if places moved constantly (e.g. food trucks or drivers).

Do not open the solution until you have made and explained your own design.
