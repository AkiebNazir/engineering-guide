# System Design Practice Prompts

One prompt per problem in the [problem catalog](02_problem_catalog.md), 01 to 41, with the constraints that matter. For each prompt, state requirements/non-goals, estimates, API/data, baseline flow, bottleneck, failure plan, SLOs, security, and evolution. Solve before opening [System Design Reference Answers](04_practice_answers.md); the full question and solution for each number are in `problems/` and `solutions/`.

## 01 URL Shortener
Create short links (with optional custom aliases) and redirect visitors: 100M new links/month, 10B redirects/month, redirect p99 under 100 ms, owners can disable links, and click analytics may lag five minutes but must never slow the redirect.

## 02 Rate Limiter
Design API quotas: 100 requests/minute/API key, controlled bursts, millions of keys, route and tenant policies, and a safe degraded mode for checkout.

## 03 Pastebin
Create/read/expire public, unlisted, and private text snippets. Reads are 1,000× writes, snippets reach 10 MB, and reads must be globally fast.

## 04 Notification Platform
Deliver email, push, and SMS with preferences/quiet hours. Handle 20M-recipient campaigns, high-priority password reset, provider outage, and duplicate callbacks.

## 05 Photo Pipeline
Upload resumable 50 MB photos, scan/process variants, show status, deliver globally, and delete originals plus derivatives safely.

## 06 Chat
Build group and direct chat with durable history, per-room ordering, offline sync, live delivery, read status, and 100k-member groups.

## 07 News Feed
Build a home feed with follows, posts, ranking, 30-second freshness, deletions, and celebrity authors with 50M followers.

## 08 Checkout
Build checkout with inventory, payment, order, confirmation, late/duplicate provider callback, reconciliation, and no double charge/oversell.

## 09 Search and Autocomplete
Search a product catalog with filters, typo tolerance, relevance, prefixes, authorization, and five-minute index freshness.

## 10 Seat Reservation
Sell concert seats to 2M users arriving in minutes. Hold seats five minutes, prevent double sell, manage waiting room and payment failure.

## 11 Web Crawler
Crawl billions of public URLs while respecting robots/politeness, deduplicating URL/content, and prioritizing recrawls.

## 12 Workflow Scheduler
Run scheduled and multi-day jobs with retries, human approval, dependent steps, worker crashes, and no concurrent duplicate execution.

## 13 Metrics Platform
Ingest millions of samples/second, query/alert, retain/downsample data, and protect against high-cardinality tenant labels.

## 14 Logging Platform
Collect/search logs from thousands of services by time/service/trace ID, survive backend slowdown, vary retention, and protect sensitive data.

## 15 Drive
Build upload, folders, sharing, version history, deletion/restore, device sync, and conflict behavior for offline edits.

## 16 Video on Demand
Accept creator uploads, transcode adaptive renditions/captions, stream globally with access control, and record playback analytics asynchronously.

## 17 Payment Ledger
Implement internal transfers with exact balances, immutable audit, external settlement correction, reconciliation, and no duplicate transfer.

## 18 Distributed Cache
Design cache client/ring, TTL/eviction, consistent hashing, hot-key protection, node replacement, replication, and source fallback.

## 19 Feature Flags
Create low-latency flag evaluation surviving control-plane outage, targeted rollout, kill switch, SDK updates, audit, and stale-config policy.

## 20 Ride Dispatch
Accept driver location updates, find nearby eligible drivers, assign exactly once, and provide real-time trip state under high city-scale load.

## 21 Multi-Tenant API Gateway
Route/version hundreds of APIs; authenticate, enforce quotas and tenant isolation, propagate tracing, and protect backends during tenant abuse.

## 22 Unique ID Generator
Hand out unique 64-bit, roughly time-sortable IDs to 10,000 application servers in 5 datacenters: 1M IDs/s peak, 10,000/s bursts on one server, under 1 ms p99 added latency, and IDs must keep flowing through a datacenter partition or any single failure.

## 23 Distributed Key-Value Store
Build a Dynamo-style `put/get/delete` store on hundreds of commodity nodes: 10 TB growing to 100 TB, 200k reads/s and 50k writes/s, p99 under 10 ms, per-request consistency, no lost acknowledged write when any two servers die, and writable during a network partition.

## 24 Collaborative Document Editor
Let up to 100 people edit one rich-text document at once with live cursors, sub-200 ms p95 keystroke-to-remote-display, convergence for every user, full revision history, immediate permission revocation, brief offline editing, and no lost acknowledged edit.

## 25 Web Search Engine
Crawl, index and serve 50 billion pages: 100k queries/s, p99 under 300 ms for the top 10 with snippets, news fresh within minutes and most pages within days, polite crawling, and prompt legal/safety takedowns.

## 26 Nearby Places
Answer "coffee within 2 km" for 200M places and 100M DAU: 50k searches/s concentrated in dense cities, p99 under 200 ms, ranking by distance/rating/open-now, map pins at every zoom level, and owner edits visible within minutes.

## 27 Ad Click Aggregation
Count 1 billion clicks/day (5× peaks) for 10M ads: per-minute dashboards within a minute, budget stop within seconds, exact deduplicated hourly billing that is reproducible for audits, fraud filtering, and mobile events arriving hours late.

## 28 Top-K Trending
Serve the top 100 items per country and category over 5-minute, 1-hour and 24-hour windows from 5B events/day over 1B items (300k/s peak), refreshed every minute, 20k reads/s at p99 under 50 ms, with bounded approximation and spam excluded.

## 29 Real-Time Leaderboard
Rank 100M players per season, region and friend group: 5k–20k score updates/s, 50k reads/s at p99 under 100 ms, top 100 plus a player's own rank and neighbours, deterministic tie-break by earliest achiever, and new rank visible within seconds.

## 30 LLM Assistant Feature
Add summarise/draft/ask-my-mailbox to an email product for 50M daily users (6 requests each, 3,000 prompt and 250 output tokens): streaming, first token under 1 s p95, answers grounded only in mail the user may see, plan quotas, admin disable, prompt-injection safety, and a fixed GPU budget.

## 31 Distributed Message Queue
Run a shared Kafka/Pub/Sub-style fleet: 1M messages/s, 5,000 topics, about three consumer groups per message, per-key ordering, 7-day replay, retries/DLQ/delays, tenant quotas, publish p99 under 20 ms, and no acknowledged loss or publish outage when a zone dies.

## 32 Ranked Home Feed
Rank and serve the home feed for 500M DAU (about 10 loads/day each) from thousands of in-network and recommended candidates: p99 under 400 ms, about 300 features per candidate, integrity filters, stable pagination, fresh engagement within minutes, leak-free training logs, and a feed that still loads when the ranker is slow.

## 33 Live Streaming and Comments
Ingest 200k concurrent broadcasts and serve 15M viewers (10M on one event) with standard (under 10 s) and low-latency (under 3 s) tiers, plus live chat peaking at 300k comments/s and 2M reactions/s, synced to the video, with 2-second moderation, DVR and VOD within a minute.

## 34 Maps Routing and ETA
Route over a 10^9-edge global road graph at 5,000 requests/s with p99 under 300 ms for 3,000 km trips, live traffic from millions of phones reaching routing within 3 minutes, re-routing during navigation, closures applied within 30 minutes, accurate ETAs, and offline packs under 400 MB.

## 35 Distributed Object Store
Build an S3/GCS-style blob store: `PUT/GET/DELETE/LIST` on billions of objects in buckets, eleven-nines durability at lower cost than triple replication, background repair when disks and servers fail, garbage collection of deleted data, and `LIST` by prefix that stays fast at scale.

## 36 Content Delivery Network
Build the CDN itself: 500 POPs, 50 Tbps and 12.5M requests/s, 92% request and 90% byte hit ratio, at most 1% of bytes reaching origins, purge p99 under 5 s worldwide, TLS for 5M hostnames, DDoS absorption, and no customer outage when a POP, the control plane or an origin fails.

## 37 Experimentation Platform
Assign 100M daily users to variants of about 1,000 concurrent experiments in under 1 ms with no remote call, stable assignment, 60-second pause propagation, exposure logging, guardrails at most 15 minutes stale, daily decision-grade results with a 5% false-positive rate under daily peeking, and a plan for network effects.

## 38 Video Conferencing
Serve 1M concurrent meetings (mean 6 people, some 500+, webinars to 50,000 viewers) across 20+ regions: 150–250 ms one-way latency, join under 2 s, 720p degrading to audio-only on 1–5% loss, UDP-blocked networks, recording plus transcript within 15 minutes, and media-node failure costing under 10 s.

## 39 Social Graph Service
Store objects and typed edges for 3B users (200 edges each, accounts with 10^8 followers) and serve 10M+ reads/s at p99 under 10 ms from cache across three full-copy regions: newest-N lists, counts, mutual friends, read-your-own-writes, and blocks enforced everywhere within 5 seconds.

## 40 Distributed Lock Service
Build a Chubby/ZooKeeper-style cell of 5 replicas over 3 zones for 30,000 client sessions: locks freed within about 15 s of a holder crash, leader election, a small CAS namespace, watches within 1 s, 100k reads/s but 200 writes/s, no lost write on a zone loss, and protection against a holder that wrongly believes it still has the lock.

## 41 Email Service
Build a Gmail-style service: receive mail over SMTP, filter spam and malware, store mailboxes for hundreds of millions of users, search each user's own mail, sync clients incrementally with cursors, and send outbound mail that keeps good deliverability.
