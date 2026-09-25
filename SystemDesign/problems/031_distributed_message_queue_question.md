# 031 — Design a Distributed Message Queue

Design a company-wide messaging service in the style of Kafka, Google Cloud Pub/Sub or SQS: producers publish messages to named topics, and independent consumer groups read them with ordering, replay and retries, on a shared multi-tenant fleet.

## Functional requirements

- Publish single or batched messages with a key; messages with the same key are delivered in publish order.
- Several consumer groups read the same topic independently; within a group each message goes to one member, and groups scale by adding consumers.
- Replay from an offset or timestamp for the retention period.
- At-least-once delivery by default, with an opt-in exactly-once effect for a consumer.
- Retry with backoff, a dead-letter queue, and delayed delivery (seconds up to 7 days).
- Self-service topics with per-tenant quotas.

## Constraints to assume

- About 1,000,000 messages/s aggregate at peak (daily average about 40% of that), 1 KB average, 1 MB maximum.
- About 5,000 topics from 200 tenant teams and about 4,000 consumer groups, so roughly three groups read each message.
- 7-day retention, 3 replicas across 3 zones. An acknowledged message must survive the loss of any one zone, and publishing must stay available through it.
- p99 publish acknowledgement under 20 ms in-region; p99 publish-to-delivery under 100 ms for caught-up consumers.
- Broker hardware for sizing: 24 TB of local SSD, 64 GB of page cache, 10 GbE per broker.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates, including broker and partition counts.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Partitioning and ordering, the replication durability versus latency trade-off, consumer group and offset management, delivery semantics with retry, dead-letter and delay, and how the log model compares with a broker-per-message queue.
6. Cache, scale, abuse, failure, and observability plan, including quotas and the metadata plane.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
