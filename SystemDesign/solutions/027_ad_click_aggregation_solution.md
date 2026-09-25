# 027 — Ad Click Aggregation: Full System Design Solution

## Goal and contract

Two outputs with different contracts from the same events:

| Output | Freshness | Accuracy | Consumer |
|---|---|---|---|
| Real-time aggregates | ~1 minute (budget pacing: seconds) | Approximately right; corrected later | Dashboards, pacing |
| Billing aggregates | Hours | Exact, deduplicated, auditable, reproducible | Invoices, finance |

Designing them as one pipeline with one accuracy target would either make dashboards slow or bills wrong. The design uses a streaming path for freshness and a batch path over the immutable raw log as the source of truth for money.

## Estimates

- **Event rate**: 1B/day ≈ 12K/s average, **~60K/s peak**.
- **Raw events**: ~1 KB each (IDs, timestamps, user agent, <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>, geo, placement) → 1 TB/day; 90 days hot ≈ 90 TB, older data in cold storage for audits.
- **Ingest and dedup state**: 60K/s × 1 KB = 60 MB/s at peak (0.5 Gbps), 180 MB/s across the log with 3× replication; at an assumed 10K/s per click server, 6 servers, **12 with 2× headroom**. A 1-hour dedup window at peak holds 60K × 3,600 = 216M `click_id`s × ~16 B ≈ **3.5 GB** of keyed state, spread across partitions.
- **Aggregates**: at most 10M ads × 1,440 minutes = 14.4B rows/day, but only non-zero `(ad, minute)` rows are stored, and 1B clicks cap that at 1B. Assume ~5 clicks per non-zero row: 200M rows/day (2.3K upserts/s) × ~50 B = 10 GB/day, 0.9 TB for 90 days. So the OLAP store sees thousands of upserts a second, not 60K events a second. Hourly rollups by `(ad, country, device)` are smaller still.
- **Budget pacing**: needs per-campaign spend within seconds, a much smaller keyspace. A campaign holding 5% of peak traffic receives 3,000 clicks/s, so a 5-second pacing interval can overshoot by 15,000 clicks (about $7.5K at an assumed $0.50 per click): that bound is why the interval is a business decision.

## Event schema and <abbr title="Application Programming Interface">API</abbr>

```text
ClickEvent {
  click_id: UUID        # generated at the ad server when the ad was rendered + click nonce; the dedup key
  ad_id, campaign_id, advertiser_id
  event_time            # when the click happened (client or ad server timestamp)
  ingest_time           # when our edge received it
  user/device fingerprint, ip, country, placement, signature   # signed by the ad server to prevent forgery
}

GET /v1/stats?advertiser_id=…&group_by=ad,hour&from=…&to=…&filters=country:US
```

Clicks are redirected through our click server (`/click?ad=…&sig=…`) which logs the event and 302-redirects the user to the advertiser — so the log write must be fast and must not block the redirect (async append to a local buffer and log).

## Architecture

```arch
%% caption: One immutable log feeds a fast streaming path for dashboards and pacing and a batch path that is authoritative for billing.
grid 140x120
node click "User click" at 1.5,0 icon=user shape=pill
node cs "Click servers" at 1.5,1 icon=server sub="log + redirect"
node log "Durable event log" at 1.5,2 icon=stream sub="Kafka / Pub/Sub, by ad_id"
group sp "Streaming path: minutes" color=pink icon=speed
node stream "Stream aggregator" at 1,3 in sp icon=apache-flink-icon sub="Flink / Dataflow"
node pace "Budget pacing" at 0,4 in sp icon=counter sub="spend counters"
node olap "Real-time OLAP" at 1,4 in sp icon=db sub="per ad per minute"
node adserve "Ad servers" at 0,5 in sp icon=server sub="stop exhausted campaigns"
group bp "Batch path: billing truth" color=green icon=archive
node raw "Raw event archive" at 2,3 in bp icon=blob sub="object storage, immutable"
node batch "Batch job" at 2,4 in bp icon=worker sub="dedup + fraud + aggregate"
node recon "Reconciliation" at 3,4 in bp icon=doc sub="report"
node billing "Billing aggregates" at 2,5 in bp icon=sql
node dash "Dashboards API" at 1.5,6 icon=dashboard
click -> cs -> log
log -> stream
log -> raw
stream -> olap
stream -> pace
pace -> adserve
raw -> batch
batch -> billing
batch -> recon
olap -> dash
billing -> dash
```

## Stream processing and windows

- The stream job keys events by `ad_id` and aggregates in **one-minute tumbling windows on event time** (not processing time — a phone syncing hours later must count in the minute the click happened).
- **Watermark**: max observed event time minus a bounded delay (e.g. 1 minute), so windows finalise about a minute after they close. A click can therefore wait up to ~2 minutes (60 s window plus 60 s delay) for its final number, so also emit **early firings** every ~10 s as upserts of the partial count: the dashboard shows a provisional value within ~15 s and the finalised one at the watermark, which meets the "about a minute" target.
- **Late events**: allowed lateness of e.g. 1 hour; a late click updates the already-emitted minute (an upsert into the OLAP store). Events later than that go to a side output that only the batch path counts.
- Aggregates are also rolled up into hourly/daily windows for cheap dashboard queries.
- Budget pacing uses the same keyed stream but emits per-campaign spend deltas every few seconds (early triggers), accepting approximate values; overspend is bounded by the pacing interval times the click rate and is refunded by billing reconciliation.

## Exactly-once and deduplication

"Exactly once" is achieved in layers:

1. **Duplicate clicks from clients** (double taps, retries): deduplicate by `click_id` within a time window using keyed state (e.g. a 1-hour TTL set per `ad_id` partition, or a Bloom filter for memory efficiency with exact checks on hits).
2. **Pipeline replays after failures**: the stream processor checkpoints operator state together with log offsets; on restart it restores both and replays, so internal counts are not doubled.
3. **Sink writes**: each window result is written as an **idempotent upsert** keyed by `(ad_id, window_start)` with the full count (not an increment), so re-emitting the same window overwrites rather than adds.
4. **Billing**: the batch job recomputes from the immutable raw archive with global deduplication by `click_id` — replaying it produces identical results, which is what auditors need.

> ⚠️ Writing `count += n` to the sink is the classic double-counting bug: any replay adds again. Write absolute values for a window, keyed by the window.

## Fraud and invalid traffic

- **Synchronous, cheap rules** at the click server: signature validation, known bot user agents, <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> blocklists, rate limits per <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>/device per ad.
- **Streaming detection**: sliding-window counters per <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>/device/publisher (count-min sketches for heavy hitters) flag abnormal click rates, click-to-impression ratios, and click bursts.
- **Batch models** (hours later) use richer features and can invalidate clicks retroactively; invalidated clicks are excluded from billing and advertisers see adjusted numbers.

## Batch reconciliation for billing

- Hourly batch jobs over the raw archive: deduplicate, apply fraud decisions, aggregate by billing dimensions, write billing tables.
- Compare with the streaming aggregates; differences beyond a threshold (e.g. > 0.5%) raise an alert — a sign of pipeline bugs, not just late data.
- Billing is finalised after a close period (e.g. 48 hours) to include late events; dashboards label numbers as "preliminary" until then.

## Storage

- **Raw archive**: columnar files (Parquet) in object storage, partitioned by `event_date/hour`, retained per legal requirements.
- **Real-time OLAP store** (Druid, Pinot, ClickHouse, or BigQuery with streaming ingest): time-partitioned, pre-aggregated by minute, supports group-by on dimensions with sub-second queries.
- **Billing tables**: in a transactional warehouse, versioned per run for auditability.

## Failure behaviour

| Failure | Behaviour |
|---|---|
| Click server can't reach the log | Buffer events on local disk (bounded) and keep redirecting users; alert if buffers fill. Never block the redirect. |
| Stream job crashes | Restart from the last checkpoint; replay from log offsets; idempotent sinks prevent double counts. Dashboards lag briefly. |
| Log partition hot (viral ad) | Partition by `ad_id` with salting for known hot ads; aggregate sub-keys and sum. |
| OLAP store down | Dashboards show last known values; stream output queues in the log (retention covers the outage). |
| Bug in aggregation logic | Fix code, then recompute affected hours from the raw archive (kappa-style replay for real time, batch for billing). |

## Observability and interview close

Measure: end-to-end event lag (event time → dashboard), watermark delay, late-event and dropped-event rates, dedup hit rate, stream vs batch discrepancy percentage, pacing overspend, fraud invalidation rate, log consumer lag, and sink write errors.

Trade-off to state: "Dashboards and pacing read from a streaming path that is fast but approximate, and billing reads from a batch recomputation over the raw log that is slow but exact and reproducible. If advertisers demanded real-time numbers that exactly match invoices, I'd need end-to-end exactly-once with transactional sinks and a long allowed lateness — much more complex and expensive — so I'd push back and instead label real-time numbers as preliminary."

## Follow-ups the interviewer will ask

1. **"How does this work across regions?"** Click servers write to a regional log, mirrored to a central region for global aggregation and billing. Absolute-value upserts need a single writer per key, so regional aggregators write `(ad_id, window, region)` rows that are summed at query time; otherwise one region overwrites another. Streaming dedup is per region, so a click reported to two regions is double-counted in preliminary numbers until the batch's global dedup, which is why billing never reads the stream. Give each region a slice of a campaign's budget and rebalance it every few seconds, the lease idea from [the rate limiter](002_rate_limiter_solution.md).
2. **"What changes at 10× and 100×?"** At 10× there are 600K events/s at peak (600 MB/s), 10 TB/day of raw events (900 TB for 90 days, so tier to cold storage after about a week), 35 GB of dedup state and about 2B OLAP rows/day. What breaks first is hot keys (a viral ad on one partition, so salt it) and OLAP ingest and compaction. At 100× run regional pipelines and use approximate sketches (HyperLogLog for uniques) for dashboards, while billing stays exact and batch.
3. **"What if dashboards must exactly match invoices in real time?"** That needs end-to-end exactly-once: a transactional sink committed with each checkpoint (two-phase commit, as Flink's transactional sinks do), no late data past the watermark, and deterministic processing. The price is latency of at least a checkpoint interval (about 10 s) plus commit, a failed commit stalling the job, and a much harder recovery story. I would push back and keep "preliminary" labels, but this is how to do it if the business insists.
4. **"What does it cost?"** Storage is cheap: 90 TB raw at an assumed $0.023 per GB-month is about $2K a month, and Parquet at 5–8× compression brings it to a few hundred dollars. Compute is the OLAP cluster and batch: keep a `click_id` index (16 GB/day, 32 GB for a 48-hour window) instead of rescanning 48 TB of raw events each hour. I would track cost per billion events.
5. **"How do you handle abuse?"** Click fraud is the core threat. Sign click URLs, make `click_id` a single-use nonce, bound timestamps, and reject impossible rates per <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>, device and publisher in the stream. Richer batch models invalidate clicks retroactively, and every invalidation records the rule or model version so decisions are reproducible for audits and advertiser disputes.
6. **"Why not increment a counter per ad per minute in a database?"** A viral ad puts 5K increments/s on one row, and retries double-count without a dedup key. The stream aggregates first, turning 60K events/s into a few thousand idempotent upserts. If the interviewer prefers streaming-only (Kappa), I accept it provided the raw log is retained (tiered storage), billing can be replayed deterministically, and the close period stays.
7. **"A phone comes online after 6 hours. What happens?"** It is past the 1-hour allowed lateness, so the stream sends it to a side output and dashboards do not change. The hourly batch counts it in the event-time hour it belongs to, and billing includes it if it arrives within the 48-hour close period. After the close it goes to the next invoice as an adjustment.

## Common mistakes

1. **Windowing on processing time.** A phone that syncs hours later counts in the wrong minute. Use event time with a watermark.
2. **Writing `count += n` to the sink.** Any replay adds again. Write the absolute count keyed by `(ad_id, window_start)`.
3. **One accuracy target for both dashboards and billing.** Dashboards get slow or bills get wrong. Keep the streaming path approximate and the batch path exact.
4. **Deduplicating only in the stream.** State expires after the window, so old duplicates leak into bills. Billing dedups globally on the raw archive.
5. **Blocking the redirect on the log write.** A slow log then hurts users or drops clicks. Append to a local buffer and log asynchronously, and alert when the buffer fills.
6. **Trusting client timestamps in the watermark.** One device with a clock a day ahead moves the watermark and makes real events look late. Clamp `event_time` to `ingest_time` plus a small skew, and track watermarks per partition.
7. **Keying by `ad_id` without salting hot ads.** A viral ad saturates one partition. Salt known hot ads and sum the sub-keys.

## Going from L5 to L6

- **Migration and rollout.** Run new aggregation or fraud logic in shadow beside production and diff it against the batch results for at least one close period before cutting over; backfill by replaying the raw archive; version the event schema in a registry so old and new producers coexist.
- **Cost model.** Storage is small next to the OLAP cluster and recompute. Control dimension cardinality in the OLAP store (rollups, not raw group-bys), tier raw data by age, and report cost per billion events.
- **Ownership and blast radius.** Billing runs on its own infrastructure and on-call with a finance-owned reconciliation, so a real-time bug can never corrupt an invoice. Regional pipelines contain outages, and the raw log is the shared contract.
- **Build versus buy.** Buy managed Kafka or Pub/Sub, a stream engine and an OLAP store; build the dedup and fraud rules and the reconciliation, which are the business logic and the audit surface.
- **Phased evolution and what to measure first.** Start with batch billing plus a minute-level dashboard, then add pacing, then streaming fraud. Measure first: the lateness distribution (what share arrives after 1 hour and after 48 hours, which sets the allowed lateness and close period), the duplicate rate, and the share of clicks from the top 100 ads.

## Build exercise

Generate a synthetic click stream with duplicates, out-of-order events, and a few hours-late events. Implement one-minute event-time windows with a watermark and allowed lateness, idempotent sink upserts, and a batch recomputation. Kill the streaming job mid-run, restart from a checkpoint, and show the counts still match the batch totals.
