# 034 — Design Maps Routing and ETA

Design the routing and ETA backend of a navigation app in the style of Google Maps: driving directions over a global road graph, live re-checking while the user drives, and traffic learned from other phones. Map tile rendering and place search are covered elsewhere and out of scope.

## Functional requirements

- Compute a route (optional waypoints, avoid tolls or ferries) with up to 3 alternatives, each with distance, ETA, geometry and turn-by-turn maneuvers.
- ETA for "leave now", "leave at 8:00" and "arrive by 9:00".
- During navigation, follow the user, detect a missed turn, re-route, and offer a faster route when traffic changes.
- Live traffic: per-road-segment speeds and incidents inferred from phone location data, used for both display and routing.
- Ingest base-map changes (new roads, one-way flips, turn restrictions, closures) and publish them safely.
- Offline maps: download a region and get directions without connectivity.

## Constraints to assume

- **Graph:** about 10^9 directed edges and 4×10^8 nodes worldwide (turn restrictions, one-ways, speed limits), car profile first. About 1M map edits a day: a closure must affect routing within 30 minutes, a new road within 24 hours.
- **Users and probes:** 1M phones navigating concurrently, each with a GPS fix per second (uploaded in 5 s batches) and ETA and route status re-checked every 5 s. About 10M more opted-in phones report a fix every 10 s while driving (about 10% at any moment).
- **Routing SLO:** 5,000 route requests per second at peak (previews, starts, re-routes), p99 under 300 ms end to end for routes up to 3,000 km, and 99.95% availability.
- **Freshness and quality:** measured speeds reach routing within 3 minutes at p99, a materially better route is offered within 30 seconds of the change, and trip-start ETA is within 10% of actual for 80% of trips.
- **Offline:** a region of up to about 10M edges must fit an offline pack under 400 MB.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Why plain Dijkstra fails at continental scale and the hierarchical or partitioned remedy, live-traffic weights and time-dependent ETA with an <abbr title="Machine Learning">ML</abbr> correction layer, map matching, rerouting triggers and alternative routes, and the map-data update pipeline.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
