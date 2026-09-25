# 028 — Top-K Trending: Full System Design Solution

## Goal and contract

Serve an approximate but stable top-K list per (window, region, category), refreshed every minute from a high-volume event stream. Approximation is explicitly allowed; the contract is that an item's position may be off by a small, bounded amount of events, and truly heavy hitters are never missed.

## Estimates

- **Events**: 5B/day ≈ 58K/s average, **300K/s peak**.
- **Distinct items**: up to 1B/day, but with a power law, the top 100 account for a tiny fraction of keys and a large share of events.
- **Exact counting memory**: a hash map entry per item per window (~50 bytes key + counter + overhead) × hundreds of millions of distinct items per day × (windows × countries × categories) → **tens to hundreds of GB per slice** — far too much to keep for every slice, and it must be merged across servers.
- **Count-min sketch memory**: for error `εN` with ε = 0.0001 (1 event in 10,000) and 99.9% confidence: width `e/ε ≈ 27,200`, depth `ln(1/0.001) ≈ 7` → 190K counters × 4 bytes ≈ **760 KB per sketch**, independent of the number of items but not of the number of slices: 6,000 slices × 760 KB ≈ 4.6 GB per minute-bucket, or about 270 GB for a 60-bucket hour if every slice used a full-size sketch (see Slicing). The additive error is 0.01% of the window's events; under an assumed Zipf (s = 1) distribution over 1B items that is about 21% of the rank-100 item's count but only 2% of rank 10's (see the follow-ups).

The numbers make the core decision: **sketches plus small heaps, not exact maps**.

## <abbr title="Application Programming Interface">API</abbr>

```text
GET /v1/trending?window=1h&region=US&category=music&k=50
→ { generated_at, window, items: [{item_id, score, approx_count, rank_change}] }
```

Served from precomputed results, so reads are key-value lookups (and <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>-cacheable for 30–60 seconds).

## Architecture

```arch
%% caption: Events are counted in sketches per partition and minute; a merger combines minutes into windows and publishes top-K lists.
node ev "View / use events" at 0,0 icon=event shape=pill
node log "Event log" at 0,1 icon=stream sub="partitioned by item_id"
node batch "Daily exact batch job" at 1,1 icon=worker
group cnt "Per-partition counting" color=pink icon=counter
node filter "Abuse filter" at 0,2 in cnt icon=filter
node agg1 "Counter workers" at 0,3 in cnt icon=worker sub="per partition"
node store "Minute buckets" at 0,4 in cnt icon=storage sub="sketch + heap per slice"
node merger "Window merger" at 1,4 icon=sigma sub="sum last N buckets"
group read "Read path" color=blue icon=search
node users "Clients" at 2,0 in read icon=users
node api "Trending API + cache" at 2,1 in read icon=api
node topk "Top-K results" at 2,3 in read icon=kv sub="per window, region, category"
ev -> log -> filter -> agg1
agg1 -> store : "every minute"
store -> merger
merger:R -> topk:B
log -> batch
batch:B -> topk:L
topk -> api -> users
```

## Counting with sketches

Each counter worker consumes a subset of partitions and, per slice (region, category) and per one-minute bucket, maintains:

- A **count-min sketch** for frequencies of every item in that slice.
- A **min-heap of candidates** of size ~K × 10: on each event, estimate the item's count from the sketch; if it exceeds the heap's minimum (or the item is already in the heap), update the heap. Keeping more candidates than K absorbs estimation noise near the cut-off.

Why it works: the sketch never undercounts, and heavy hitters are, by definition, far above the collision noise `εN`. Items near the boundary of the top K can swap positions, which is within the contract.

**Merging across workers**: sketches with identical dimensions and hash functions merge by **adding counters cell by cell**. The merger sums the minute buckets from all workers, takes the union of candidate items from all heaps, re-estimates each candidate's count from the merged sketch, and selects the top K. Candidate union is important: an item can be moderately popular on every partition without being top on any single one — partitioning events by `item_id` prevents that split for the same item.

## Sliding windows

- Store one merged sketch + candidate set **per minute** per slice.
- The **last hour** = sum of the latest 60 minute-buckets; every minute, add the newest bucket and subtract the oldest (count-min sketches support subtraction of exactly what was added).
- The **last 24 hours** uses coarser buckets (e.g. 10- or 60-minute buckets built by merging minute buckets) to keep work bounded.
- **Last 5 minutes** is computed directly from the latest buckets for responsiveness.

This is a sliding window with a 1-minute hop, matching the refresh requirement, with bounded state.

## Trend scoring

Raw counts produce "always popular" lists. To surface rising items:

- `score = count_recent_window / max(baseline, floor)` — compare the last hour against the same hour over the previous days (or an exponentially decayed average), with a floor to avoid tiny items with 3 → 30 events dominating.
- Or an exponentially time-decayed count, updated incrementally: `score = score × e^(−λΔt) + 1` per event, which favours recent activity.
- Combine with quality and safety signals and diversity rules (not ten videos from the same channel) at publish time.

## Slicing by dimension

Every (region × category) slice needs its own sketch and heap. With 200 regions × 30 categories = 6,000 slices × 760 KB ≈ 4.5 GB per minute-bucket — too much if kept for 1,440 minutes. Controls:

- Use smaller sketches for small slices (error tolerance relative to their volume).
- Keep minute-level buckets only for recent windows; roll older ones into coarser buckets.
- Only maintain slices that are actually requested; compute rare combinations on demand from the batch store.

## Abuse filtering

Manipulated activity is exactly what top-K lists attract. Before counting: drop events from known bots and invalid clients, cap events per user per item per window (using a keyed dedup set or a Bloom filter per window), and weight events by account trust. After computing: anomaly checks on sudden spikes concentrated in few accounts or IPs, and manual/automated policy review for the published lists.

## Exact batch job

A daily batch job over the raw events computes exact counts for the published top lists and a larger candidate set. It validates the streaming results (alert if the approximate top 100 diverges significantly from the exact top 100) and serves as the source for historical "top of the day" pages.

## Failure behaviour

| Failure | Behaviour |
|---|---|
| Counter worker dies | Partitions reassigned; the worker replays from the log since its last committed bucket. Buckets are idempotent per (partition, minute). |
| Merger lagging | <abbr title="Application Programming Interface">API</abbr> serves the last published lists with `generated_at`; freshness <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr> alert. |
| Hot item floods one partition | The sketch handles volume cheaply; the partition's <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> is the limit — scale consumers, or pre-aggregate at the edge per second. |
| Late events | Counted into the bucket of their event minute if it is still within the window; otherwise dropped from real time and counted by the batch job. |

## Observability and interview close

Measure: ingest lag, events filtered as abuse, sketch saturation (fraction of non-zero counters), streaming vs exact top-K overlap, list churn per refresh (too much churn feels random), publish latency, <abbr title="Application Programming Interface">API</abbr> p99, and cache hit rate.

Trade-off to state: "I use count-min sketches with candidate heaps, so memory stays constant and sketches merge across servers, at the cost of small overcounts near the cut-off. If exact counts were required — say, for creator payouts — I'd keep exact per-item counters for those items in a stream processor with keyed state and an idempotent sink, and pay the memory and state-management cost only where money depends on it."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Events land in the nearest region, and each region builds its own sketches. Sketches merge by cell-wise addition, so a global list is the sum of regional sketches plus the union of their candidate heaps. Shipping every slice would be 4.6 GB per minute (76 MB/s), so ship only the global and continent slices (about 7 slices, 5 MB a minute in total plus 16 KB of candidates each) and keep country slices local. The global list is then a minute or two staler than the local ones, which the contract allows.
2. **"What changes at 10× and 100×?"** At 10× (3M events/s) the <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> is still small: 4 slice updates × 7 counters is 28 increments per event, about 1.7 cores at an assumed 20 ns each. The error `εN` scales with N, so the relative accuracy of the top 100 does not degrade with volume. What grows is log throughput (at an assumed 100 B per event, 300 MB/s at 10× and 3 GB/s at 100×), merge fan-in and slice count. At 100× add an edge combiner that pre-aggregates per item per second, which collapses hot-item traffic before the log, and merge in a tree.
3. **"What if creator payouts need exact counts?"** Keep exact per-item counters only for the monetised set, in keyed stream state with an idempotent sink and event-ID dedup. Even 10M monetised items × ~64 B is 0.64 GB of state, so exactness where money depends on it is cheap, and the sketch path stays for ranking. The daily exact batch job remains the audit source.
4. **"What does it cost?"** Memory is the design: about 270 GB if every slice were full size, but most of the 6,000 slices are small, so size sketches to slice volume (assume 10× smaller, about 27 GB). The log at 30 MB/s is 2.6 TB/day. Reads are 20K rps × ~6 KB ≈ 120 MB/s, served from the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>; with 6,000 slices × 3 windows = 18,000 keys and a 30 s TTL, the origin sees about 600 requests/s per cache tier.
5. **"How do you handle abuse?"** Filter before counting, because a sketch cannot cleanly un-count an event: drop known bots, dedup per user per item per window, cap per <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>, and weight by account trust. After counting, flag spikes concentrated in few accounts (low source entropy), and hold newly spiking items for review before publishing.
6. **"How accurate is your top 100, really?"** Under a Zipf (s = 1) assumption over 1B items, the rank-k item holds 1/(k × 21.3) of events: 0.047% at rank 100 and 0.47% at rank 10. With ε = 0.01% the additive error is about 21% of the rank-100 count and 2% of rank 10's, so the boundary blurs but heavy hitters are safe. For 5% at rank 100, ε = 2.3×10⁻⁵, width about 116K and 3.2 MB per sketch, which is 4.3× the memory.
7. **"Why count-min plus a heap instead of exact counts or Space-Saving?"** Exact maps need about 60 GB per slice-window for 1B items and do not merge cheaply. Space-Saving (Metwally et al., 2005) keeps m counters and guarantees that any item above N/m events is tracked, and it is a good alternative. I chose count-min because minute buckets add and subtract linearly, which gives cheap sliding windows and cross-server merges. If the interviewer prefers Space-Saving, I would merge summaries per partition and accept that errors accumulate.

## Common mistakes

1. **Exact per-item maps for every window and slice.** Tens to hundreds of GB per slice, plus a hard merge. Use sketches with candidate heaps.
2. **A sketch with no candidate set.** A count-min sketch answers "how many?" but cannot list the top items. Track candidates in a heap of about 1,000 entries (K × 10) per slice.
3. **Randomly partitioning events.** An item spread evenly across partitions is top on none of them. Partition by `item_id`, and still take the union of candidates when merging.
4. **Sizing ε for one minute, then reusing it for the window.** The error is relative to total events N, so an hourly or daily sketch needs the accuracy check against the rank you care about, not just the minute.
5. **Recomputing a window by summing all its buckets every minute.** Add the newest bucket and subtract the oldest instead, which is exact for count-min.
6. **Ranking by raw counts.** You get the same popular items forever. Score against a baseline with a floor, and handle cold-start items.
7. **Filtering abuse after counting.** The sketch has already absorbed the bots. Filter before the counter workers.

## Going from L5 to L6

- **Migration and rollout.** Scoring and sketch parameters are product changes: shadow-run the new version and compare its top-100 overlap and churn with the exact batch result, ramp a few regions first, and keep the previous list as an instant fallback.
- **Cost model.** Sketch memory scales with slices, not events, so control slice count and size per slice; log retention is the storage cost, and the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> absorbs read cost. Report cost per million events.
- **Ownership and blast radius.** Counter workers run in regional cells and publish atomically per slice with `generated_at`, so a bad deploy freezes some lists and corrupts none. Abuse filtering belongs to a trust-and-safety owner with its own review path.
- **Build versus buy.** Build the sketch and merge logic (small) on a managed stream processor and key-value store, and buy the <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>. For small slices, an OLAP store's approximate top-N may be enough.
- **Phased evolution and what to measure first.** Start with exact counts in one region plus the daily batch, and add sketches when memory forces it. Measure first: the item-frequency distribution (its Zipf exponent sets ε), events per slice, churn per refresh, and top-100 overlap with the exact result.

## Build exercise

Generate a Zipf-distributed stream of 100 million events over 10 million items across 16 simulated partitions. Implement per-partition count-min sketches with candidate heaps, merge them, and compare the approximate top 100 with an exact count: report overlap, rank displacement, and memory used. Vary width and depth.
