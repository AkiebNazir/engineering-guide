# 037 — Design an Experimentation (A/B Testing) Platform

Design the platform a large consumer product uses to run controlled experiments on ranking, UI and backend changes: it assigns users to variants, measures the effect, and helps teams roll a change out or stop it. A wrong readout is worse than a late one, because teams ship on it.

## Functional requirements

- Define an experiment: variants with parameter values, eligibility rules, allocation, owner, primary and guardrail metrics.
- Assign each user (or device, or user cluster) to one variant, consistently across web, mobile and backend, with mutual exclusion between experiments on the same feature.
- Record exposures and compute per-variant metric results with confidence intervals, and flag invalid experiments.
- Ramp an experiment up in stages, and pause or roll it back automatically when a guardrail metric breaks.
- Keep holdouts, an audit trail and a history of every change; let non-statisticians read a result safely.
- Handle products where users influence each other (feeds, messaging) and per-user randomization is biased.

## Constraints to assume

- 200 M monthly and 100 M daily active users; about 10 B server requests per day read experiment parameters, from roughly 30,000 service instances.
- About 1,000 experiments run concurrently over about 50 independent parameter surfaces, and about 70 start each day. A typical one must detect a 1–2% relative lift on a 5% conversion metric within two weeks.
- The assignment decision inside a request must take under 1 ms at p99 with no remote call, must not change for a user during an experiment, and a config change or pause must reach all servers within 60 seconds.
- About 5 B raw exposure events per day, on top of about 10 B product metric events per day, some arriving a day or more late from mobile clients.
- Guardrail metrics (errors, latency, crashes) are at most 15 minutes stale; decision-grade results for every experiment are ready within 6 hours of each UTC day ending; a false-positive rate of 5% must hold even if people look at results daily.

## Your task

Spend 45 minutes and produce:

1. Clarifying questions and assumptions.
2. Back-of-envelope QPS, storage, and bandwidth estimates.
3. <abbr title="Application Programming Interface">API</abbr> contracts and core data model.
4. Baseline architecture and read/write flows.
5. Deterministic assignment and layers, config distribution, exposure logging and the sample-ratio-mismatch trap, the metrics pipeline (stream, batch, late data), and the statistics engine (power, peeking, multiple comparisons, interference).
6. Cache, scale, abuse, failure, and observability plan.
7. One explicit trade-off you would revisit at 100× traffic or multi-region.

Do not open the solution until you have made and explained your own design.
