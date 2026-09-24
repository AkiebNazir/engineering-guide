# 010 — Design a Seat Reservation System

Design a system that sells concert seats to a huge simultaneous audience without double-selling any seat.

## Functional requirements

- A user selects a seat and it is held exclusively for a few minutes while they pay.
- If payment isn't completed in time, the hold expires and the seat becomes available again.
- No two users can ever be confirmed for the same seat.
- Users arriving faster than the system can serve are placed in a waiting room/queue.
- A failed payment releases the hold immediately for others to claim.
- A user can see real-time seat map availability.

## Constraints to assume

- 2 million users arriving within a few minutes of on-sale.
- Seat hold duration of 5 minutes.
- Seat-selection response under 300 ms p99 for users past the waiting room.
- Zero tolerance for double-selling a seat.
- Waiting room admits users at a rate the backend can sustain without overload.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. API contracts and core data model.
4. Baseline architecture and read/write flows.
5. Seat-locking and waiting-room admission strategy to guarantee no double-sell.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
