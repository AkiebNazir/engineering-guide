# Twenty System Design Practice Prompts

For each prompt, state requirements/non-goals, estimates, <abbr title="Application Programming Interface">API</abbr>/data, baseline flow, bottleneck, failure plan, SLOs, security, and evolution. Solve before opening `04_twenty_practice_solutions.md`.

## 02 Rate Limiter
Design <abbr title="Application Programming Interface">API</abbr> quotas: 100 requests/minute/<abbr title="Application Programming Interface">API</abbr> key, controlled bursts, millions of keys, route and tenant policies, and a safe degraded mode for checkout.

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
Create low-latency flag evaluation surviving control-plane outage, targeted rollout, kill switch, <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> updates, audit, and stale-config policy.

## 20 Ride Dispatch
Accept driver location updates, find nearby eligible drivers, assign exactly once, and provide real-time trip state under high city-scale load.

## 21 Multi-Tenant <abbr title="Application Programming Interface">API</abbr> Gateway
Route/version hundreds of APIs; authenticate, enforce quotas and tenant isolation, propagate tracing, and protect backends during tenant abuse.

## 22 Unique ID Generator
Design a highly available unique id generator capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 23 Distributed Key-Value Store
Design a highly available distributed key-value store capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 24 Collaborative Document Editor
Design a highly available collaborative document editor capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 25 Web Search Engine
Design a highly available web search engine capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 26 Nearby Places
Design a highly available nearby places capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 27 Ad Click Aggregation
Design a highly available ad click aggregation capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 28 Top-K Trending
Design a highly available top-k trending capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 29 Real-Time Leaderboard
Design a highly available real-time leaderboard capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 30 LLM Assistant Feature
Design a highly available llm assistant feature capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 31 Distributed Message Queue
Design a highly available distributed message queue capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 32 Ranked Home Feed
Design a highly available ranked home feed capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 33 Live Streaming and Comments
Design a highly available live streaming and comments capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 34 Maps Routing and ETA
Design a highly available maps routing and eta capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 36 Content Delivery Network
Design a highly available content delivery network capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 37 Experimentation Platform
Design a highly available experimentation platform capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 38 Video Conferencing
Design a highly available video conferencing capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 39 Social Graph Service
Design a highly available social graph service capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.

## 40 Distributed Lock Service
Design a highly available distributed lock service capable of handling thousands of requests per second with strict constraints on latency and data correctness. Detail the APIs, data model, scaling approach, and how you handle failure states, hot partitions, and network partitions.
