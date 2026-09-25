# 026 — Nearby Places Search: Full System Design Solution

## Goal and contract

A read-dominated service (50K searches/s vs ~12 writes/s) where place data can be a few minutes stale but search must be fast everywhere, including dense city centres. The design therefore precomputes a geospatial index, serves it from memory, caches aggressively by area, and handles writes asynchronously.

## Estimates

- **Place records**: 200M × ~2 KB of core fields (name, lat/lng, categories, rating, hours) ≈ 400 GB; photos and reviews live elsewhere (object storage and a review service).
- **Geo index**: per place, a cell ID (8 bytes) + place ID (8 bytes) + a few ranking fields (~32 bytes) ≈ 50 bytes × 200M ≈ **10 GB** — the whole world's index fits in memory on one server, so sharding is for throughput and locality, not size.
- **Reads**: 50K <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> peak. If one index server handles ~5K <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>, ~10 servers plus replicas per region; regional deployment keeps latency low.
- **Writes**: 1M updates/day ≈ 12/s — trivial; an asynchronous pipeline is fine.

## <abbr title="Application Programming Interface">API</abbr> and data model

```text
GET /v1/places/search?lat=37.78&lng=-122.41&radius_m=2000&category=coffee&open_now=true&page_token=…
→ { results: [{place_id, name, lat, lng, distance_m, rating, open_now}], next_page_token }

GET /v1/places/{place_id}            → full details (served from cache + place store)
POST /v1/places / PATCH /v1/places/{id}   → owner updates (authenticated, moderated)
```

- `Place(place_id, name, lat, lng, s2_cell_l16, categories[], rating, review_count, hours, updated_at)` in a relational or document store, sharded by `place_id` — the source of truth.
- `GeoIndex(cell_id, category) → [place_id, lat, lng, score…]` derived in memory on search servers.

## Geospatial index

| Option | Behaviour | Verdict here |
|---|---|---|
| Lat/lng B-tree + bounding box | Range on latitude, filter longitude — scans a whole latitude strip. | Too slow at this scale. |
| Geohash strings | Prefix = cell; query cell + 8 neighbours at a precision where cells ≈ search radius. | Simple, works in any KV store; fixed-size cells are uneven in dense vs empty areas. |
| Quadtree | Split cells until each holds ≤ K places. | Adapts to density; in-memory tree to rebuild. |
| **S2 cells** | Hilbert-curve cell IDs on the sphere (30 levels); a region is covered by a few cell ID ranges. | **Chosen**: uniform-ish cells without pole distortion, covering algorithms built in, IDs sort locally. |

**Decision:** index each place under its S2 cell at a fine level (e.g. level 16, cells roughly 150 m across), and store sorted `(cell_id, place)` arrays per region in memory. A search:

1. Compute an S2 **covering** of the search circle: a small set of cells (at mixed levels) that together cover the circle.
2. For each covering cell, range-scan the sorted cell IDs (a cell at level *n* corresponds to a contiguous ID range of its level-16 descendants).
3. Filter by exact distance and category, then rank.

This avoids the geohash boundary problem (the covering naturally includes neighbouring cells) and keeps the number of lookups small (typically 4–8 ranges).

**Dense areas**: in Manhattan, a 2 km radius may contain 20,000 places. Keep per-cell candidate lists pre-sorted by a static score (rating × popularity), and scan only the top N per cell before exact ranking; if too many candidates remain, shrink the radius progressively ("expanding ring" search in reverse). In sparse areas, grow the radius until enough results are found.

## Architecture and flows

```arch
%% caption: Writes flow asynchronously into in-memory geo indexes; searches never touch the source-of-truth database.
node user "User" at 1,0 icon=mobile
node owner "Business owner" at 3,0 icon=user
group search "Search path" color=blue icon=search
node edge "Edge / CDN cache" at 1,1 in search icon=cdn sub="rounded area + filters"
node rank "Ranking" at 0,2 in search icon=sort
node gw "Search gateway" at 1,2 in search icon=gateway
node hours "Open-now + personalization" at 0,3 in search icon=time
group det "Place details" color=teal icon=doc
node details "Place details API" at 2,1 in det icon=api
node cache "Detail cache" at 2,2 in det icon=cache
group write "Write path" color=green icon=edit
node api "Places API" at 3,1 in write icon=api
node db "Place store" at 3,2 in write icon=db sub="sharded by place_id"
node indexer "Geo indexer" at 3,3 in write icon=worker
group idx "In-memory S2 index" color=purple icon=map
node idx1 "Search servers" at 2,4 in idx icon=server sub="region A"
node idx2 "Search servers" at 3,4 in idx icon=server sub="region B"
user -> edge -> gw
user:R -> details:T
details -> cache -> db
owner -> api -> db
db ..> indexer : "CDC events"
indexer ..> idx1
indexer ..> idx2
gw -> idx1:L
gw -> rank
gw -> hours
```

- **Write path**: validate and moderate the update, write to the place store, emit a change event; the geo indexer updates the in-memory index on search servers (and a periodic full rebuild corrects drift). Freshness: seconds to minutes.
- **Search path**: the gateway routes to the user's region, which holds the index for that region plus neighbouring regions (so searches near borders still work). The index servers return candidates; ranking combines distance decay, rating, review count, popularity, open-now, and optional personalisation.
- **Place details**: cache-aside with a TTL of minutes, invalidated by change events.

## Sharding by geography

Even though the index fits in memory, serve it **regionally** for latency and to isolate load: a city's evening peak should not affect another continent. Shard by S2 cell prefix (level 4–6 regions), with replicas sized to each region's traffic — dense metros get more replicas. Hot areas (Times Square on New Year's Eve) get extra replicas and more aggressive result caching.

## Caching

Nearby searches are highly repetitive: many people search "coffee" near the same downtown blocks. Cache results keyed by `(level-14 cell of the user, radius bucket, category, filters)` with a TTL of 1–5 minutes. Rounding the location into a cell trades a little precision for a much higher hit rate; the client still sorts by exact distance for display. "Open now" is either part of the key with a short TTL or applied after the cache as a filter.

## Map pins and zoom levels

At low zoom, showing 50,000 pins is useless and slow. Precompute **clusters per tile per zoom level** (count of places per cell, representative top places) in the same pipeline, and serve them as vector tiles through a <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>. The client fetches tiles for the visible viewport and requests detailed search results only at high zoom.

## Failure behaviour

| Failure | Behaviour |
|---|---|
| Search server down | Load balancer removes it; replicas absorb load. |
| Indexer lagging | Searches serve slightly stale data; a new place may take longer to appear. Alert on index age. |
| Place store down | Searches continue from in-memory indexes and caches; owner updates fail with a retryable error. |
| Region outage | Route to the nearest region, which holds neighbouring regions' index data; latency rises, results stay correct. |
| Bad data update (place moved to the ocean) | Validation rules and moderation for large location changes; index rebuild from the source of truth after correction. |

## Observability and interview close

Measure: search p50/p99 per region and city tier, candidates scanned per query (a proxy for dense-area cost), result-cache hit rate, index age, empty-result rate, click-through on results, and write-to-searchable latency.

Trade-off to state: "Because places rarely move, I rebuild and update a read-optimised in-memory index asynchronously. For constantly moving objects like drivers or food trucks with location updates every few seconds, that pipeline would lag badly; I'd switch to a mutable in-memory grid keyed by cell ID where each location update moves one entry, partitioned by city, and accept that results are only as fresh as the last update."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** The whole index is 10 GB, so every serving region can hold a full copy, which is simpler than the regional-plus-neighbours layout above and makes a region outage a pure latency event. Owner writes go to one home region (12 writes/s), and change events replicate asynchronously to every region's indexer, so a new place appears everywhere within seconds to minutes. A partition only delays that propagation; search keeps answering from local memory.
2. **"What changes at 10× and 100×?"** At 10× (2B places, 500K <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>) the index is 100 GB, still one box, and the search tier is about 100 servers, or about 30 with a 70% cache hit rate (assumed). At 100× (20B places, 5M <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>) the index is 1 TB, so I shard by S2 cell prefix with more replicas for dense metros, and the edge cache with location rounding stops being an optimisation and becomes the design. What breaks first is the dense-metro cache-miss storm, not memory.
3. **"What if a closure or takedown must disappear immediately?"** The 1–5 minute cache TTL and the async index are too slow. Push tombstones (place ID, version) to every search server within seconds and filter them at serving time, and purge affected cache entries by surrogate key (place or cell). The owner's own view reads the source-of-truth store, so read-your-writes holds for them without changing the derived index.
4. **"What does it cost?"** The index servers are almost free: 3 servers' worth of traffic at a 70% cache hit rate, or 10 servers before caching, plus replicas across a few regions. Egress dominates: 50K <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> × ~5 KB (assumed) = 250 MB/s = 2 Gbps, about 650 TB a month at a sustained peak, so payload trimming, compression and the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> hit rate matter more than <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>. The place store is 400 GB times its replicas, and photos and reviews are priced separately.
5. **"How do you handle abuse?"** Scrapers sweep a grid of small searches to copy the database, so rate-limit per key and <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>, cap page depth and result count, and detect sweep patterns. Listing spam and fake places go through moderation and large-move validation. Normalise and cap filter values so odd parameters cannot poison the cache or force full scans.
6. **"Why a custom S2 index rather than PostGIS or Elasticsearch?"** A managed geo store is a fine start: with 12 writes/s and 200M places, PostGIS or Elasticsearch geo queries meet the need and ship sooner. I chose an in-memory S2 array because 10 GB fits in <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr> and gives predictable p99 and control of dense-area scan caps. H3 hexagons are a reasonable alternative, with more uniform neighbour distances but only approximately nested cells. I would say which I would pick first: the managed store, then move when the p99 in dense metros forces it.
7. **"How do you keep p99 under 200 ms in Manhattan?"** A 2 km radius holds about 20,000 places, and scanning them at an assumed 50 ns each is 1 ms, so scanning is not the cost. Ranking is: cap candidates per cell by static score, apply a cheap score first, and run the full ranker (open-now, personalisation) only on the top ~200. If the cap truncates, shrink the radius or page by cell.

## Common mistakes

1. **A lat/lng bounding-box query on a relational B-tree.** It scans a whole latitude strip. Use a cell index (S2, geohash, quadtree).
2. **Geohash lookup of only the user's cell.** Places just across a cell edge are missed. Query the covering or the 8 neighbours too.
3. **Searching the source-of-truth database.** Read load and writes then couple. Serve from a derived in-memory index and cache, and let the store handle only writes and details.
4. **Ranking every candidate in a dense area.** 20,000 candidates per query multiplies <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>. Cap per cell by static score and use a two-stage ranker.
5. **Caching on exact coordinates.** The hit rate is near zero. Round the location to a cell and radius bucket, and let the client re-sort by exact distance.
6. **Hashing the search index by `place_id`.** Every query then fans out to all shards. Shard the index geographically and the store by id.
7. **Doing spherical math by hand.** Longitude wrap-around at the antimeridian and pole cases break naive distance filters. Use a library covering algorithm.

## Going from L5 to L6

- **Migration and rollout.** The index is derived, so change it by rebuilding beside the old one: build from the store plus change-event replay, compare counts and sampled query recall against the live index, then shift regions one at a time. Changing the S2 level is a dual-index migration, never an in-place edit.
- **Cost model.** Memory and <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> are small, so egress, the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> and the place store's replicas set the bill; cache hit rate is the main lever. Report cost per 1,000 searches.
- **Ownership and blast radius.** Place data, search serving and ranking are separate owners joined by the change-event contract. A bad index build is confined to the region being rolled, and moderation stays a separate gate on writes.
- **Build versus buy.** Start on a managed geo database or search engine and buy the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> and map tiles; build the in-memory S2 tier only when dense-city p99 or cost forces it.
- **Phased evolution and what to measure first.** Ship radius search on a managed store, then add the cache and the in-memory index, then tiles and clusters. Measure first: candidates scanned per query in the top 20 metros, cache hit rate by cell, and write-to-searchable latency.

## Build exercise

Load 1 million synthetic places clustered around 20 cities. Implement geohash and S2-style (or quadtree) indexes and measure candidates scanned and latency for 2 km searches in dense vs sparse areas, including queries that straddle cell boundaries.
