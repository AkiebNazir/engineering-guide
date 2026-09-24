# 020 — Design a Ride Dispatch System

Design a ride-hailing dispatch system that matches riders to nearby drivers and tracks trips in real time.

## Functional requirements

- Drivers continuously stream their GPS location while online.
- A rider requests a ride and the system finds nearby eligible drivers to offer it to.
- A ride is assigned to exactly one driver, even if multiple drivers respond near-simultaneously.
- Riders and drivers see live trip state (requested, matched, en route, in progress, completed).
- The system degrades gracefully in dense cities during demand spikes (e.g. surge events).

## Constraints to assume

- 5 million concurrent online drivers at peak, location updates every 4 seconds.
- 200,000 ride requests/minute in the busiest city at peak.
- Match latency p99 under 3 seconds from request to driver offer.
- Exactly-once assignment even under concurrent driver responses.
- Trip state updates delivered to both parties within 2 seconds.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Geo-indexing and exactly-once assignment strategy under concurrent driver responses.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
