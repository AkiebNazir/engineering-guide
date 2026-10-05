# 006 — Design a Chat System

Design a messaging service that supports both direct messages and large group chats.

## Functional requirements

- Two users can exchange direct messages with durable history.
- Users can create groups with up to 100k members.
- Messages within a room are delivered and displayed in a consistent order.
- An offline user's client syncs missed messages when it reconnects.
- Online users receive new messages with low latency.
- Read receipts or read status are tracked per message/user.

## Constraints to assume

- 100k members in the largest groups.
- Message send-to-delivery latency under 200 ms p99 for online recipients.
- Offline sync must catch a client up within a few seconds of reconnect.
- Message history durable and retrievable indefinitely.
- Millions of concurrent connected clients.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Fan-out and ordering strategy for large groups vs direct messages.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
