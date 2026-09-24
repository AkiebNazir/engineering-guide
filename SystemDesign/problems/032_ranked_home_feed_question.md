# 032 — Design a Ranked Home Feed

Design the ranking and serving pipeline behind the home feed of a large photo-and-video app: choose, order and serve the posts each user sees, mixing accounts they follow with recommendations from accounts they do not. Fanout of posts to followers is problem 007; this problem starts from "we can produce candidates" and asks how to rank and serve them.

## Functional requirements

- A feed request returns a first page of about 10 ranked posts; scrolling returns further pages that never repeat or skip items.
- Mix in-network posts (accounts the user follows) with out-of-network recommendations.
- Integrity and quality filters: policy-violating, borderline, blocked, muted and already-seen posts are excluded.
- New engagement (likes, dwell time, hides) affects ranking within minutes; new posts and new creators get a fair chance.
- Every impression and outcome is logged for model training and experiments.
- The feed still loads when the ranker or a feature store is slow.

## Constraints to assume

- 500 million daily active users, about 10 feed loads per user per day, peak about 2.5× average.
- p99 under 400 ms server-side, end to end, per feed load.
- Thousands of candidate posts per request; about 10^8 new eligible posts per day, with the last three days recommendable.
- The heavy ranker uses about 300 features per candidate; engagement counters must be fresh within two minutes.
- Training data must reflect exactly what was shown, with no leakage from the future.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, candidate counts per stage, compute, feature-fetch bandwidth, and log volume.
3. API contracts and core data model.
4. Baseline architecture and the request flow with its latency budget.
5. The multi-stage cascade with per-stage counts and budget, feature serving and training/serving consistency, precompute versus on-demand with stable pagination, exploration and cold start, logging and feedback loops, and fallbacks when a stage is slow.
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
