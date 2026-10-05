# 004 — Design a Notification Platform

Design a service that delivers email, push, and SMS notifications to users based on their preferences and quiet hours.

## Functional requirements

- Services trigger notifications for events (e.g., password reset, marketing campaign).
- Users configure channel preferences and quiet hours per notification type.
- High-priority notifications (e.g., password reset) bypass batching delays.
- Large campaigns can target tens of millions of recipients without overwhelming providers.
- Delivery callbacks (success/failure) from providers update notification status.
- Duplicate sends are avoided even when callbacks arrive late or twice.

## Constraints to assume

- 20 million recipients in a single campaign.
- Password-reset notification delivered within 10 seconds p99.
- Third-party provider outages are common and must not block other channels.
- At-least-once delivery with dedupe; no user should get 100 copies of one message.
- Campaign sends may take up to an hour to fully drain.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Fan-out, prioritization, and provider-outage/duplicate-callback handling strategy.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
