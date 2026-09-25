# System Design Problem Catalog

Solve questions before opening their solution. Work in numeric order — each later problem assumes the building blocks and vocabulary from earlier ones. Numbering matches `05_architecture_blueprints.md`.

| # | Problem | Primary skills | Files |
|---|---|---|---|
| 001 | URL Shortener | IDs, read-heavy cache, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>, async analytics | [Question](problems/001_url_shortener_question.md) · [Solution](solutions/001_url_shortener_solution.md) |
| 002 | Rate Limiter | Token bucket, atomicity, quotas, failure policy | [Question](problems/002_rate_limiter_question.md) · [Solution](solutions/002_rate_limiter_solution.md) |
| 003 | Pastebin | Public/unlisted/private reads, object storage, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> | [Question](problems/003_pastebin_question.md) · [Solution](solutions/003_pastebin_solution.md) |
| 004 | Notification Platform | Fanout, preferences, provider retries, idempotency | [Question](problems/004_notification_platform_question.md) · [Solution](solutions/004_notification_platform_solution.md) |
| 005 | Photo Pipeline | Object store, direct uploads, async pipeline | [Question](problems/005_photo_pipeline_question.md) · [Solution](solutions/005_photo_pipeline_solution.md) |
| 006 | Chat | WebSockets, ordering, delivery, offline sync | [Question](problems/006_chat_question.md) · [Solution](solutions/006_chat_solution.md) |
| 007 | News Feed | Fanout, materialized views, hot users | [Question](problems/007_news_feed_question.md) · [Solution](solutions/007_news_feed_solution.md) |
| 008 | Checkout | Transactions, inventory, payment saga, audit | [Question](problems/008_checkout_question.md) · [Solution](solutions/008_checkout_solution.md) |
| 009 | Search and Autocomplete | Derived index, relevance, freshness, caching | [Question](problems/009_search_and_autocomplete_question.md) · [Solution](solutions/009_search_and_autocomplete_solution.md) |
| 010 | Seat Reservation | Contention, holds, anti-oversell | [Question](problems/010_seat_reservation_question.md) · [Solution](solutions/010_seat_reservation_solution.md) |
| 011 | Web Crawler | Frontier partitioning, politeness, dedupe | [Question](problems/011_web_crawler_question.md) · [Solution](solutions/011_web_crawler_solution.md) |
| 012 | Workflow Scheduler | Leases, fencing, idempotent activities | [Question](problems/012_workflow_scheduler_question.md) · [Solution](solutions/012_workflow_scheduler_solution.md) |
| 013 | Metrics Platform | Ingestion, cardinality, retention, aggregation | [Question](problems/013_metrics_platform_question.md) · [Solution](solutions/013_metrics_platform_solution.md) |
| 014 | Logging Platform | Ingestion, redaction, tiered retention, bounded search | [Question](problems/014_logging_platform_question.md) · [Solution](solutions/014_logging_platform_solution.md) |
| 015 | Drive | Versioned objects, ACL graph, offline sync/conflict | [Question](problems/015_drive_question.md) · [Solution](solutions/015_drive_solution.md) |
| 016 | Video on Demand | Transcode ladder, manifests, <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr>, entitlement | [Question](problems/016_video_on_demand_question.md) · [Solution](solutions/016_video_on_demand_solution.md) |
| 017 | Payment Ledger | Immutable journal, idempotent transfers, reconciliation | [Question](problems/017_payment_ledger_question.md) · [Solution](solutions/017_payment_ledger_solution.md) |
| 018 | Distributed Cache | Consistent hashing, hot keys, invalidation | [Question](problems/018_distributed_cache_question.md) · [Solution](solutions/018_distributed_cache_solution.md) |
| 019 | Feature Flags | Local evaluation, kill switch, staleness | [Question](problems/019_feature_flags_question.md) · [Solution](solutions/019_feature_flags_solution.md) |
| 020 | Ride Dispatch | Geo indexing, offer leases, exactly-once assignment | [Question](problems/020_ride_dispatch_question.md) · [Solution](solutions/020_ride_dispatch_solution.md) |
| 021 | Multi-Tenant <abbr title="Application Programming Interface">API</abbr> Gateway | Routing, quota isolation, tracing propagation | [Question](problems/021_multi_tenant_api_gateway_question.md) · [Solution](solutions/021_multi_tenant_api_gateway_solution.md) |

### Google L5 set

The problems most often asked in Google design rounds that the first 21 do not cover. Read the [L5 playbook](00_google_l5_playbook.md) first, and do each one against the 45-minute clock.

| # | Problem | Primary skills | Files |
|---|---|---|---|
| 022 | Unique ID Generator | Snowflake bit layout, clock skew, worker-ID leases | [Question](problems/022_unique_id_generator_question.md) · [Solution](solutions/022_unique_id_generator_solution.md) |
| 023 | Distributed Key-Value Store | Consistent hashing, quorums, version vectors, hinted handoff, Merkle repair | [Question](problems/023_distributed_key_value_store_question.md) · [Solution](solutions/023_distributed_key_value_store_solution.md) |
| 024 | Collaborative Document Editor | Session servers, OT vs CRDT, op log + snapshots, offline edits | [Question](problems/024_collaborative_document_editor_question.md) · [Solution](solutions/024_collaborative_document_editor_solution.md) |
| 025 | Web Search Engine | Crawl frontier, inverted index sharding, fan-out and tail latency, ranking stages | [Question](problems/025_web_search_engine_question.md) · [Solution](solutions/025_web_search_engine_solution.md) |
| 026 | Nearby Places | S2/geohash/quadtree, dense areas, area caching, map tiles | [Question](problems/026_nearby_places_question.md) · [Solution](solutions/026_nearby_places_solution.md) |
| 027 | Ad Click Aggregation | Event-time windows, watermarks, exactly-once, batch reconciliation | [Question](problems/027_ad_click_aggregation_question.md) · [Solution](solutions/027_ad_click_aggregation_solution.md) |
| 028 | Top-K Trending | Count-min sketch + heaps, sliding windows, merging across servers | [Question](problems/028_top_k_trending_question.md) · [Solution](solutions/028_top_k_trending_solution.md) |
| 029 | Real-Time Leaderboard | Sorted sets, tie-breaking, sharding, approximate global rank | [Question](problems/029_realtime_leaderboard_question.md) · [Solution](solutions/029_realtime_leaderboard_solution.md) |
| 030 | <abbr title="Large Language Model">LLM</abbr> Assistant Feature | Token streaming, batching and prefix caching, model routing, quotas, prompt injection | [Question](problems/030_llm_assistant_feature_question.md) · [Solution](solutions/030_llm_assistant_feature_solution.md) |

### Breadth set: infrastructure and product systems from Meta, Netflix and Google interviews

The problem families the first 30 do not cover: log/queue infrastructure, ranking, live media, routing, storage, CDNs, experimentation, social graphs, coordination and email. Each is built on the new building blocks `26`–`32`.

| # | Problem | Primary skills | Files |
|---|---|---|---|
| 031 | Distributed Message Queue | Partitioned replicated log, ISR and acks, consumer groups, delivery semantics, quotas | [Question](problems/031_distributed_message_queue_question.md) · [Solution](solutions/031_distributed_message_queue_solution.md) |
| 032 | Ranked Home Feed | Retrieval → ranking cascade, feature serving, session-stable pagination, exploration | [Question](problems/032_ranked_home_feed_question.md) · [Solution](solutions/032_ranked_home_feed_solution.md) |
| 033 | Live Streaming and Comments | Ingest, real-time transcode, low-latency packaging, mega-stream <abbr title="Content Delivery Network - A geographically distributed network of proxy servers and their data centers used to deliver content with low latency.">CDN</abbr> fan-out, comment fan-out | [Question](problems/033_live_streaming_and_comments_question.md) · [Solution](solutions/033_live_streaming_and_comments_solution.md) |
| 034 | Maps Routing and ETA | Contraction hierarchies, graph sharding, live traffic weights, map matching, ETA models | [Question](problems/034_maps_routing_and_eta_question.md) · [Solution](solutions/034_maps_routing_and_eta_solution.md) |
| 036 | Content Delivery Network | Steering, cache hierarchy, hot objects, purge, <abbr title="Transport Layer Security - A cryptographic protocol designed to provide communications security over a computer network.">TLS</abbr> at the edge, ISP-embedded caches | [Question](problems/036_content_delivery_network_question.md) · [Solution](solutions/036_content_delivery_network_solution.md) |
| 037 | Experimentation Platform | Hash bucketing, layers, exposure logging, SRM, power and CUPED, guardrails | [Question](problems/037_experimentation_platform_question.md) · [Solution](solutions/037_experimentation_platform_solution.md) |
| 038 | Video Conferencing | SFU vs MCU, WebRTC signaling, simulcast, congestion control, cascaded SFUs | [Question](problems/038_video_conferencing_question.md) · [Solution](solutions/038_video_conferencing_solution.md) |
| 039 | Social Graph Service | Objects and associations, cache tiers, hot edge lists, 2-hop queries, privacy checks | [Question](problems/039_social_graph_service_question.md) · [Solution](solutions/039_social_graph_service_solution.md) |
| 040 | Distributed Lock Service | Consensus state machine, sessions and leases, fencing, watches, client caching | [Question](problems/040_distributed_lock_service_question.md) · [Solution](solutions/040_distributed_lock_service_solution.md) |

Every full solution now ends with **Follow-ups the interviewer will ask**, **Common mistakes**, and **Going from L5 to L6**. Use them after your timed attempt: answer the follow-ups aloud before you read the model answers.

For every catalog item, solve the question independently before opening the solution. Each solution covers requirements, estimates, APIs, data, flows, architecture, trade-offs, failure modes, observability, security, evolution, and a build exercise.

## Faster review pass

For a condensed pass across all 39 problems in one sitting (prompt, reference answer, one-paragraph blueprint), use:

- [Practice prompts](03_practice_prompts.md): one paragraph per problem, with the constraints that matter.
- [Condensed reference answers](04_practice_answers.md): the design in one paragraph each.
- [Architecture blueprints](05_architecture_blueprints.md): source of truth, contract, flow, hard part, scale trigger, and the one thing never to do, per problem. Good for a pre-mock refresher.

Preparing for a specific company? Start with the [company interview guide](01_company_interview_guide.md), which maps each company's typical questions onto this catalog.
