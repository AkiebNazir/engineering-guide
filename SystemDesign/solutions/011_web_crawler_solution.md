# 011 — Web Crawler: Full System Design Solution

## Goal and contract

A web crawler discovers and fetches billions of public URLs while respecting each site's stated crawl rules and not hammering any single host. The source of truth is per-URL crawl state (queued/fetched/error/next-recrawl-time), the stored content object plus its hash, and each host's robots/politeness state. A page's freshness is bounded and re-evaluated on a schedule, not guaranteed real-time.

Assume: billions of URLs arrive via links, sitemaps and seed lists; per-host `robots.txt` defines disallowed paths and (optionally) a crawl-delay; the same content is reachable via many URLs, and the same URL is discovered many times.

The contract: no host is crawled faster than its politeness budget, every URL is normalized to a canonical form before any dedupe decision, and URL-level dedupe (don't refetch an address needlessly) stays strictly separate from content-level dedupe (don't store or index identical content found at different addresses) — conflating them either wastes storage on near-duplicates or drops distinct pages that share content momentarily.

The question's numbers are the contract: **billions of URLs in the frontier, ~1 request per host every few seconds, thousands of pages/s aggregate, daily recrawl priority for high-value pages, dedup indexes at tens of billions of entries.** Assumed concrete values: **5,000 pages/s, 30B known URLs, 3 s per-host delay.** The hard decision: throughput is easy and *politeness is the binding constraint*, so the design is organised around per-host scheduling, and freshness is a budget-allocation problem.

## Estimates

- **Throughput**: 5,000/s × 86,400 = **432M pages/day**. A pass over 30B URLs takes 30B ÷ 432M = **69 days**. Recrawling 100M high-value URLs daily = 1,157/s = **23%** of capacity, leaving ~330M/day, so the long tail cycles every ~90 days. → *Freshness is decided by which 432M URLs we pick each day, not by raw speed.*
- **Politeness**: a 3 s delay caps a host at 0.33 pages/s, so 5,000/s needs **≥ 15,000 hosts ready at once**, and one host yields at most 86,400 ÷ 3 = **28,800 pages/day**. A 10M-page site would take 347 days. → *Big sites cap coverage, so recrawl priority must choose their best 28.8K pages; the same ceiling bounds a spider trap to 28.8K ÷ 432M = 0.007% of daily work.*
- **Bandwidth**: assume 100 KB average HTML, ~4:1 gzip → 25 KB on the wire: 5,000 × 25 KB = **125 MB/s ≈ 1 Gb/s** (500 MB/s decompressed). → *NICs are not the constraint.*
- **Concurrency and nodes**: Little's law with ~1 s per fetch (<abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> + <abbr title="Transmission Control Protocol - A core protocol of the Internet Protocol Suite that provides reliable, ordered, and error-checked delivery of a stream of bytes.">TCP</abbr> + <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> + body; assumption) = 5,000 open connections, which ~5 async nodes could hold; parsing at ~5 ms/page = 25 core-seconds/s. State decides the node count (next bullet).
- **Frontier size and nodes**: 30B × ~120 B (80 B URL + 40 B state) = **3.6 TB**; with ~0.5 TB of URL store, ~4.1 TB ÷ ~100 GB of NVMe state per node = **~40 nodes**. Memory holds only queue heads.
- **Link volume**: 50 outlinks/page (assumption) × 5,000 = **250K candidate URLs/s** = 25 MB/s. A small <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> absorbs most: Broder et al. (WWW 2003) report ~80% hits from a ~50K-entry cache, leaving **~50K/s** for the owners' URL tests (~1.3K/s per node).
- **URL-test memory**: exact 64-bit fingerprints: 30B × 8 B = **240 GB** (480 GB with an 8 B value); with n = 3×10¹⁰ the expected false collisions are n²/2⁶⁵ ≈ **24 URLs**, negligible. Bloom filter: bits per key m/n = −ln p ÷ (ln 2)², k = (m/n) ln 2. p = 1% → 9.6 bits, k = 7, **36 GB** total (0.9 GB/node); p = 0.1% → 14.4 bits, k = 10, **54 GB**. Overfilled 2× at fixed size (k = 7): p = (1 − e^(−kn/m))^k ≈ **16%**. → *Size for 2× growth or use scalable filters (Almeida et al., 2007). A Bloom-only design at p = 1% with 2% of the 250K links/s new (5K/s) silently loses ~50 new URLs/s ≈ **4.3M/day**, so keep an exact store behind it.*
- **Content indexes**: 128-bit exact hash: 30B × 16 B = 480 GB; 64-bit SimHash: **240 GB per table copy**; MinHash with 128 × 8 B signatures = 1 KB/page = **30 TB**. → *SimHash for near-duplicates.*
- **<abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>**: one lookup per fetch would be **5,000 <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>**. Host-pinned nodes with a caching resolver need only first-touch lookups (assume 20M new hosts/day ÷ 86,400 = 230/s) plus refreshes (15K–45K active hosts ÷ 300 s TTL floor = 50–150/s): **~300–400 <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr>** upstream.
- **Storage**: 30B × 25 KB = **750 TB per full crawl**; ~25% exact duplicates (assumed) → ~560 TB; daily ingest 10.8 TB. At $23/TB-month (S3 list) that is ~$13–17K/month. → *Object storage in large compressed segments, never a row store.*

## Mechanisms compared

| Mechanism | Behavior | Choose it when | Main weakness |
|---|---|---|---|
| Single global <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> queue | One queue, workers pull next URL regardless of host. | Never at scale. | One popular host dominates and gets hammered; no fairness across hosts. |
| Host-partitioned frontier | Each host has its own sub-queue and politeness state. | Standard for respecting per-host delay/robots. | Needs routing by host and rebalancing as hosts grow. |
| URL-hash dedupe | Normalize, hash, check membership before enqueueing. | Stops the same address being queued repeatedly. | Nothing for different URLs serving identical content. |
| Content-hash dedupe | Hash fetched content; compare to known hashes. | Avoids storing or indexing the same content from different URLs. | Needs the fetch first (cost already spent) unless paired with canonical-tag heuristics. |
| Fixed recrawl interval | Every page every N days. | Small, low-churn corpora. | Wastes budget on static pages, under-serves high-churn ones. |
| Adaptive recrawl (change rate + importance + error backoff) | Next crawl from observed change frequency, importance and recent errors. | Large mixed-churn corpora — the realistic case. | More per-URL state; needs decay and backoff logic. |

## <abbr title="Application Programming Interface">API</abbr>

Internal system; discovery is a pipeline, not a request/response service.

```text
POST /v1/urls:submit   { urls:[…≤1000], source:"seed|sitemap|user", priority? }
     → 202 { accepted, already_known, rejected:[{url, reason:"robots|too_long|bad_scheme|private_ip"}] }
POST /v1/recrawl       { url | {host, pattern}, reason, priority }      → 202   (still bounded by the host budget)
PUT  /v1/hosts/{host}/policy   { crawl_delay_s?, daily_budget?, blocked?, reason }   → 200   # opt-outs, complaints
GET  /v1/urls/{url_fp}  |  /v1/hosts/{host}      → state, next_fetch, last_status, robots status

topic crawl.results (key = url_fp, at-least-once):
  { url, final_url, status, fetched_at, etag, last_modified, content_hash, simhash64, body_ref, outlinks_n, dup_of? }
```

**Idempotency**: submit is a no-op for a known URL fingerprint; result consumers dedupe on `(url_fp, fetched_at)`; a refetch after a crash is harmless. **Errors**: `429` on submit rate; rejected URLs are reported, never silently dropped.

## Data model

```text
url_state    PK url_fp (64-bit of normalized URL); shard = hash(host)
  url, host_id, state NEW|QUEUED|FETCHED|ERROR|DEAD, priority 0-7, importance, first_seen, last_fetch, next_fetch,
  interval_s, lambda_est, fail_count, etag, last_modified, content_hash, simhash64, canonical_fp
host_state   PK host: ip, robots{body, fetched_at, status}, crawl_delay_s, next_allowed_at, backoff_until,
             err_ewma, budget_left_today, quality, url_count
content_index   content_hash → canonical_fp        simhash tables: sorted, permuted copies
segments        object store  {date}/{shard}/{seg}.warc.zst   body_ref = (segment, offset, len)
topics          links.discovered (key = host hash)    crawl.results (key = url_fp)
```

- **Source of truth**: `url_state` and `host_state` (local NVMe, checkpointed), plus stored segments; the frontier queues and heap are rebuildable from `url_state`.
- **Partition key**: `hash(registrable domain)` for both URL state and host state, so a host's URLs, robots cache, delay and back queue live on one node and politeness never needs cross-node coordination (see [25](../building_blocks/25_partitioning_and_hot_keys.md)). Skew: a huge site is still capped by its per-host rate, so it cannot overload its node.

## Architecture and flow

```arch
%% caption: Every URL is normalized and dedup-checked before it ever reaches a per-host frontier, so politeness budgets are a local, not global, coordination problem.
grid 3x2
node Disc "Discovery" at 0,0
node Norm "Normalizer" at 1,0
node Dedup "URL-hash dedupe" at 2,0
node Frontier "Host-partitioned frontier" at 2,1
node Fetcher "Fetcher" at 1,1
node Store "Content store" at 0,1

Disc -> Norm : "seeds, links\nsitemaps"
Norm -> Dedup : "normalized\nURL"
Dedup -> Norm : "drop if\nseen"
Dedup -> Frontier : "route by\nhost (new)"
Frontier:R -> Frontier:B : "apply robots\ntoken bucket"
Frontier -> Fetcher : "next allowed\nURL"
Fetcher -> Store : "store content\n+ hash"
Store:B -> Store:L : "compare hash\nschedule recrawl"
Store -> Disc : "extract links"
```

Routing every discovered URL to the node that owns its host converts "don't overload any one host" from global coordination into an independent local scheduling problem, so the system scales by adding nodes. This trades some cross-host load balance (a node with many small hosts may idle while another serves one huge site) for the correctness property that no host can be crawled faster than its budget however many workers exist.

Walk-through: a fetcher on node 17 extracts links and posts them to `links.discovered` keyed by host hash; each owner drains its partition, runs normalization → <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> → Bloom → exact store, and enqueues survivors into its front queues. Its fetcher slots pop the earliest-ready host from the back-queue heap, check the cached robots rules, fetch (conditional GET if it has an `etag`), write the body to a segment, compute hashes, and emit `crawl.results`; content-duplicate verdicts and the next `next_fetch` update `url_state`. The read side is the indexer consuming `crawl.results` (see [025](025_web_search_engine_solution.md)).

## Crawl queues: priority in front, politeness behind

The Mercator design (Heydon and Najork, 1999; also Manning et al., *Introduction to Information Retrieval*, ch. 20) splits the two concerns, and the split is the answer.

```arch
%% caption: Front queues encode priority and back queues encode politeness, so one min-heap of next-allowed times is the only structure that decides which host to fetch next.
grid 170x125
node N "New normalized URL" at 1,0 shape=pill
node P "Priority assigner" at 1,1 icon=sort
group fq "Front queues (priority)" color=blue icon=queue
node F1 "Front queue 1" at 0,2 in fq icon=queue sub="high"
node F2 "Front queue 2" at 1,2 in fq icon=queue
node F3 "Front queue F" at 2,2 in fq icon=queue sub="low"
node S "Biased selector" at 1,3 icon=filter
node R "Router" at 1,4 icon=sitemap sub="host to back queue"
group bq "Back queues (politeness)" color=green icon=queue
node B1 "Back queue: host A" at 0,5 in bq icon=queue
node B2 "Back queue: host B" at 1,5 in bq icon=queue
node B3 "Back queue: host C" at 2,5 in bq icon=queue
node H "Min-heap" at 1,6 icon=tree sub="by next_allowed_at"
node T "Fetcher slot" at 2,7 icon=worker sub="pop root, wait, fetch"
N -> P
P -> F1
P -> F2
P -> F3
F1 -> S
F2 -> S
F3 -> S
S -> R
R -> B1
R -> B2
R -> B3
B1:B -> H:T
B2 -> H
B3:B -> H:T
H:B -> T:L
T:T -> H:R : "next_allowed_at =\nnow + delay"
```

- **Front queues** (say 8) hold URLs by priority from importance and freshness need. A *biased* selector prefers high queues by weight rather than strict priority, so the low tail is not starved.
- **Back queues** each hold URLs of exactly one host; a `host → queue` table routes. A fetcher slot pops the heap root, sleeps until `next_allowed_at`, fetches one URL, then sets `next_allowed_at = now + max(crawl_delay, floor, multiple of the last fetch time)` (Mercator scaled the wait with the previous download's duration). When a back queue empties, refill it from the front queues, giving the slot to the first URL whose host has no back queue.
- **Sizing** (my numbers): ≥ 15,000 active back queues to hit 5,000/s, and ~3× that (45K) so hosts in backoff never idle a slot. Only each queue's head page stays in memory: 45K × 4 KB ≈ 180 MB; the rest is append-only segments on disk.
- **Rejected**: one priority queue keyed by `(priority, time)` (violates politeness), plain per-host token buckets (no priority), and SQS/Kafka delay queues (no per-host ordering or budget).

## Robots.txt, crawl-delay, and partitioning crawler nodes

- **Fetch and cache** `/robots.txt` on first contact with a host and refresh at most every 24 h (RFC 9309, 2022, says not to use a cache older than that unless the file is unreachable). Parse at least 500 KiB, follow a few redirects. **Status rules (RFC 9309)**: 2xx parse; 4xx = no robots, allowed; 5xx or timeout = *unreachable*, treat as fully disallowed and retry with backoff (after 30 days unreachable it may be treated as 4xx). Robots-disallowed URLs are dropped at enqueue and re-checked at fetch, since cached rules can be stale.
- **Crawl-delay** is not in RFC 9309 and Google's crawlers ignore it, while some others honor it. State a policy: honor it up to a cap (say 30 s) and derive the host budget as 86,400 ÷ delay, so a delay of 3,600 s means 24 pages/day and hosts asking more are deprioritized, not overridden.
- **Partitioning**: consistent hashing of `hash(registrable domain)` over ~40 nodes with virtual nodes; a node loss moves ~1/40 of hosts. Politeness is *per host and per <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr>*; different domains on one shared-hosting <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> can land on different nodes, so give each <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> a low per-node share (cap ÷ nodes) or re-route by <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> after first resolution. After reassignment two nodes can briefly both own a host, so the host→node map carries an **epoch** (fencing token, as in [012](012_workflow_scheduler_solution.md)) and a new owner cold-starts every host at `now + delay`.
- **Courtesy**: descriptive `User-Agent` plus contact URL, verifiable by reverse <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>; back off on 429/503 and honor `Retry-After`; prefer sitemaps and conditional requests so an unchanged page costs a 304.

## Normalizing and filtering repeat URLs

**Normalize first**, versioned: RFC 3986 §6 syntactic rules (lowercase scheme and host, IDNA to punycode, drop default ports, resolve dot-segments, normalize percent-encoding, strip fragments), then crawler rules (drop known session and tracking parameters like `jsessionid`, `utm_*`, `gclid`; sort parameters only where a host is proven order-insensitive; cap length at ~2,000 chars). `rel=canonical` is a hint, not a rule. A rule change is replayed on a sample and must not lower content-hash equivalence.

**The repeat-URL test** at the owner node, in order: (1) <abbr title="Least Recently Used - A cache replacement policy that discards the least recently used items first when the cache reaches its capacity.">LRU</abbr> of ~1M recent fingerprints (~8 MB) drops popular nav links; (2) in-memory Bloom filter (~0.9 GB/node at p = 1%): "no" means definitely new, so insert and enqueue without touching disk; (3) "maybe" goes to the exact fingerprint store (<abbr title="Log-Structured Merge-tree. A data structure with performance characteristics that make it attractive for providing indexed access to files with high insert volume.">LSM</abbr> on NVMe, ~12 GB/node) for the true answer. A Bloom false positive therefore costs one lookup and never drops a URL. At this size the exact store alone would work; the Bloom filter earns its keep as a cheap negative filter over the <abbr title="Log-Structured Merge-tree. A data structure with performance characteristics that make it attractive for providing indexed access to files with high insert volume.">LSM</abbr> (RocksDB uses per-file Bloom filters for the same reason) and becomes essential at 10–100× when the store no longer fits in <abbr title="Random Access Memory - A form of computer memory that can be read and changed in any order, typically used to store working data.">RAM</abbr>.

## Duplicate content: exact hashes, SimHash, and shingling

Exact duplicates (mirrors, `http`/`https`, `www`): a 128-bit hash of the decompressed body catches identical bytes. **Near duplicates** (same article, different ads or timestamps): **SimHash** (Charikar, 2002), a 64-bit fingerprint over weighted word features where similar documents differ in few bits; Manku, Jain and Das Sarma (WWW 2007) found Hamming distance ≤ 3 works at 8B pages, searching several permuted sorted tables (memory scales with table count, hence 240 GB per copy above). **Shingling/MinHash** (Broder, 1997) estimates resemblance more accurately but costs ~1 KB per page (30 TB), so use it only to verify candidate clusters. Hash *extracted main content*, not the template, or every page of a site looks alike, and require a minimum length (say 50 tokens) before near-duplicate matching. A hit records `dup_of` and skips indexing but leaves the URL's state alone, so a transiently identical page mid-deploy is not lost. Hosts that are mostly duplicates lose crawl budget.

## Recrawl scheduling from estimated change rate

Model page changes as a Poisson process with rate λ. With `n` regular visits and `X` detected changes over interval `I`, the bias-reduced estimator from Cho and Garcia-Molina (2003) is λ̂ = −ln((n − X + 0.5)/(n + 0.5)) / I: 10 visits with 3 changes gives ≈ 0.34 changes per interval. **Adaptive rule**: `interval ×= 1.5` (cap 30 d) when unchanged, `×= 0.5` (floor 24 h for high-value pages, 1 h for news) when changed, blended with λ̂; then `priority = importance × (1 − e^(−λ̂·age))` is the expected value of fetching now. The daily job re-scores importance and pushes priorities to owners, and picks the top ~432M by priority per day within per-host budgets. Their analysis also warns that, for freshness, over-visiting the fastest-changing pages wastes budget, so cap `interval` from below. **Conditional GET** (`If-None-Match`, `If-Modified-Since`) turns an unchanged page into a ~1 KB 304: if 70% of recrawls are unchanged, recrawl bandwidth drops from 29 MB/s to ~9.5 MB/s. Trust sitemap `lastmod` only for hosts where it has proven accurate.

## Fetch failures, backoff, and JavaScript rendering

| Failure | Behavior |
|---|---|
| NXDOMAIN | Retry at 24 h up to 3 times, then `DEAD` (tombstone 30 d) |
| SERVFAIL, connect timeout, reset | Per-URL backoff 1 h, 6 h, 24 h, 3 d with jitter, then `DEAD` |
| 429/503 | Honor `Retry-After` (cap 24 h); raise that host's delay |
| Host error EWMA > 30% over 50 requests | Host-level exponential backoff 1 min up to 24 h; other hosts unaffected |
| 404 / 410 | 410: `DEAD` at once; 404: retry once at the next interval |
| 301/308 | Update canonical, drop the old URL; cap redirect chains at 5 |

**JavaScript rendering** is a follow-up tier, not the default path. Rendering costs roughly 1–3 <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>-seconds and hundreds of MB per page against ~5 ms to parse static HTML. If 5% of pages need it (empty body, framework markers, high script-to-text ratio), that is 250 renders/s × 2 s ≈ **500 cores** at 5,000 fetches/s (assumption). Run it as a separate asynchronous queue, sandboxed with no internal-network access, with a hard timeout; sub-resource fetches also spend the host's politeness budget; the render result re-enters the pipeline as a new content version.

## Checkpointing and recovery

Node state is local NVMe: frontier segments (append-only), the URL store (<abbr title="Log-Structured Merge-tree. A data structure with performance characteristics that make it attractive for providing indexed access to files with high insert volume.">LSM</abbr>) and host state. Every ~5 minutes the node uploads incremental segments plus the `links.discovered` offset to object storage. **Recovery**: a replacement node restores the last checkpoint and replays `links.discovered` from the stored offset; inserts are idempotent on `url_fp`, so replay is safe. Fetches completed after the checkpoint are simply refetched: 125 pages/s per node × 300 s ≈ **37K refetches** per node loss, acceptable for a crawler. The new owner then ramps politeness from cold rather than trusting old `next_allowed_at`.

## Capacity and storage

At tens of billions of URLs the URL-state and dedupe indexes reach the terabyte range, so they are partitioned across nodes (host hash) and never held in one in-memory set. Partition the frontier by host; shard within a host only for the few enormous sites. Store content by content hash so identical content is stored once and referenced many times, keeping storage proportional to unique content.

Do not run one global <abbr title="First-In, First-Out. A method for processing data where the first items entered are the first to be removed, characteristic of queue data structures.">FIFO</abbr> queue across all hosts — the classic crawler mistake: it starves the long tail and, whenever workers pull from one host back to back, violates politeness. Do not filter robots-disallowed paths after fetch; exclude them before queueing. Do not conflate URL dedupe with content dedupe: treating "different URL, same content" as "don't crawl" loses distinct pages that render the same content transiently.

## Failure and abuse behavior

| Case | Correct behavior |
|---|---|
| Host returns elevated error rate | Exponential backoff on that host's queue only; no tight retries. |
| robots.txt unreachable or slow | Unreachable (5xx/timeout) means treat as disallowed and retry, never assume permissive; 4xx means no restrictions. |
| Normalization collapses two distinct pages | Rules are conservative and versioned; a bad change shows as a spike in "new content under old URL" mismatches and is rolled back. |
| One host floods the frontier with millions of links | Per-host budget caps sustained fetches whatever the depth; that host's queue ages, others are unaffected. |
| Mirrors serve duplicate content | Stored once, canonical referenced; crawl budget is still spent per URL to discover this. |
| Recrawl scheduling drifts (stale index) | Adaptive scheduling corrects over time; alert on the frontier-age distribution. |
| Crawler node or zone lost | Partitions reassigned by consistent hashing; restore checkpoint, replay, cold-start politeness; a few minutes of refetches. |
| Bad deploy (robots parser or normalizer bug) | A parser bug that reads `Disallow: /` as empty is a politeness incident: canary on a small host sample, run the new parser against a corpus of real robots files before rollout, and keep a global fetch-rate kill switch. |
| Fetching internal addresses (SSRF via crafted links, <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> rebinding) | Resolve once, block private, loopback and metadata ranges, connect to the resolved <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> only. |
| Cloaking (different content for crawler UA) | Sample-compare crawler and browser fetches; penalize hosts that differ. |

## Crawler traps, <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr>, and adversarial content

A crawler that follows every link eventually enters a region that generates infinite URLs. Budget and detect rather than trust links:

| Trap | Example | Defense |
|---|---|---|
| Infinite calendars, pagination | `/calendar?month=2031-07`, `?page=99999` | Per-host and per-pattern URL budgets; stop when new pages stop yielding new content hashes |
| Session IDs, tracking params | `;jsessionid=…`, `?utm_source=…` | Strip known volatile params; learn per-host relevance by checking whether removing a param changes the content hash |
| Relative-link loops | `/a/b/../a/b/../a/b/…` | Canonicalize paths; cap URL length and depth |
| Soft 404s | Missing pages return 200 "not found" | Probe a random nonexistent URL per host, fingerprint it, treat matches as 404 |
| Link farms, generated spam | Millions of pages linking each other | Host quality scores gate budget; low-score hosts get tiny budgets |
| Near-duplicate content | Same article, different ads | SimHash with a Hamming threshold |
| Huge or slow responses | Multi-GB files, trickle bodies | Max body size, content-type allowlist, total timeout |
| Redirect chains and loops | A → B → A | Cap at 5 redirects, record the final URL |

**<abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> is a hidden bottleneck** (numbers above): run a crawler-local caching resolver, honor TTLs with a floor, resolve asynchronously, and group by resolved <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> as well as hostname.

## Observability and interview close

Measure frontier age (time since last successful fetch) per host and overall, per-host error rate and backoff state, politeness-violation count (zero by construction, so any nonzero value is a token-bucket bug), URL-to-content duplicate ratio, Bloom filter fill (false-positive rate rising as it fills), exact-store hit rate, <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> cache hit rate, and bytes fetched/stored per day. **The one paging alert**: any politeness violation (per-host request gap below its delay) or high-importance frontier age p99 above target. Elevated host errors and <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> latency are ticket-level signals.

Interview close: "I partition the frontier by host so politeness is a local, per-host scheduling problem instead of a global coordination problem, I keep URL-level dedupe and content-level dedupe as separate concerns because they solve different problems, and I schedule recrawls adaptively by observed change rate and importance rather than a uniform interval that wastes budget on static pages."

**Trade-off to state:** an exact fingerprint store behind a Bloom filter costs about 12 GB per node more than Bloom-only, and I accept that because a Bloom false positive on *new* URLs silently loses coverage (~4M URLs/day at 1%), whereas a false positive in front of an exact store costs one lookup.

## Follow-ups the interviewer will ask

1. **"How do you do multi-region?"** Run fetch fleets in a few regions with a stable host-to-region assignment so politeness stays local and latency to targets is low, and replicate results (not frontier state) to a central store. Hosts moved between regions carry the epoch and cold-start; <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> answers can differ by region, so resolve in the fetching region ([27](../building_blocks/27_multi_region_and_global_traffic.md)).
2. **"What changes at 10× and 100×?"** At 50K pages/s: 4,300M pages/day, ~400 nodes, a 10× larger frontier (36 TB), Bloom filters of 360 GB at 1% for 300B URLs, and 150K hosts ready at once. The limit becomes distinct hosts and egress <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> reputation; use an <abbr title="Internet Protocol. The principal communications protocol in the Internet protocol suite for relaying datagrams across network boundaries.">IP</abbr> pool and shard the URL test by fingerprint range. At 100× (~100 Gb/s wire) the fleet spans regions by necessity.
3. **"Can you guarantee no host is ever fetched too fast, even during failover?"** Only with fencing: the host→node epoch, a cold-start ramp, and leases on ownership, because two briefly-overlapping owners can each be individually polite yet jointly aggressive. It costs a few minutes of reduced throughput per node loss.
4. **"What does it cost, what do you cut first?"** Storage (~$13–17K/month for a full crawl), ~40 nodes plus a 500-core render tier if JS is on. Cut rendering scope and tail recrawl frequency first, then store diffs or skip re-storing unchanged pages (304).
5. **"How do you defend against abuse?"** Both directions: we must not abuse sites (robots, budgets, opt-out, verifiable UA), and sites abuse us (traps, cloaking, SSRF links, decompression bombs). Budgets, private-range blocking, size and time limits, and host quality scoring.
6. **"What if the interviewer says just use a Bloom filter for the URL test?"** Concede the memory win (36 GB for 30B URLs) and the simplicity, then show the cost: at 1% it drops ~4.3M new URLs/day, cannot delete, and degrades to 16% if it grows 2× past its size. Offer the compromise already in the design: Bloom as a negative filter in front of an exact store, or an accepted-loss Bloom only for the low-priority tail.

## Common mistakes

1. **Sizing on bandwidth.** 1 Gb/s looks easy and hides that politeness (15,000 ready hosts, 28.8K pages/host/day) is the binding constraint.
2. **One global queue with a rate limiter.** It cannot express per-host delay and lets a hot host consume workers; use back queues plus a next-allowed heap.
3. **Bloom-only URL dedupe.** False positives silently drop new URLs and grow unbounded as the filter fills; keep an exact store or size for 2× growth.
4. **Conflating URL and content dedupe.** Different URLs with the same content are still separate URLs to schedule; decide at content time, not by dropping the URL.
5. **Trusting robots and <abbr title="Domain Name System - A hierarchical and decentralized naming system for computers, services, or other resources connected to the Internet.">DNS</abbr> defaults.** Treat 5xx robots as disallow, cache with TTL floors, and resolve once to avoid rebinding.
6. **A uniform recrawl interval.** It spends the budget on static pages; use change-rate estimates, conditional GET and per-host budgets.
7. **No plan for node loss.** Say what is checkpointed, what is replayed, and how politeness restarts.

## Going from L5 to L6

- **Migration and rollout.** Shadow-crawl a host sample with a new parser, normalizer or scheduler and compare content hashes and coverage before switching; ramp politeness budgets slowly and publish a contact and opt-out path.
- **Cost model.** Storage is ~$0.6 per million pages per month (25 KB × $23/TB-month); rendering is the multiplier; let product value set each host's budget.
- **Ownership and blast radius.** Frontier/scheduler, fetch fleet, and content pipeline are separate teams; per-host budgets, a global rate kill switch and node-level partitions bound blast radius; abuse complaints route to an owned opt-out process.
- **Build vs buy.** Consider buying crawled data (Common Crawl-style corpora) when you do not need freshness; build only when freshness or coverage is the product.
- **What I would measure first.** Real page-size and outlink distributions, the share of hosts that publish crawl-delay, the fraction of new links per fetch, and the duplicate rate: my 25 KB, 50 links and 25% are assumptions.

## Build exercise

Build a local host-aware frontier: implement per-host token buckets and a robots.txt check gating a small in-memory queue, seed it with URLs from a handful of fake hosts including one that returns many links quickly, and assert no host is fetched faster than its configured rate even as the others queue independently.

Extend it with named assertions:

- `test_min_heap_politeness`: with two hosts at 3 s and 10 s delays, the fetch log never shows two requests to one host closer than its delay, while the other host proceeds.
- `test_bloom_fp_and_exact_backstop`: a Bloom sized for 10K keys at p = 1% and loaded with 20K shows a measured <abbr title="Functional Programming. A programming paradigm where programs are constructed by applying and composing functions.">FP</abbr> rate near 16%, yet the Bloom-then-exact pipeline drops zero new URLs.
- `test_robots_status_rules`: 404 allows, 503 blocks and retries, 200 with `Disallow: /private` blocks only that prefix.
- `test_trap_budget`: an infinite `?page=N` host stops after its budget while other hosts keep progressing.
- `test_recovery_replay`: kill the node mid-run, restore from checkpoint and replay; no URL is lost and no host is fetched before its cold-start delay.
