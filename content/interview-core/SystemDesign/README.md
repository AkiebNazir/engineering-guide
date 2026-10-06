# System Design Mastery Curriculum

Learn system design in this order:

0. Read [Google L5 System Design Playbook](00_google_l5_playbook.md) first: how the Google design round is scored, the 45-minute timeline, and the signals that separate L4 from L5 (and L5 from L6). Then read [Company Interview Guide](01_company_interview_guide.md) for how Meta, Netflix and Amazon rounds differ and which parts of this module to lean on for each.
1. Read [Building Blocks of Any System](building_blocks/00_overview.md) and work through the directory in order until you can explain each component in plain language. Files `00`–`17` are the core sequence; `18`–`32` add the depth that senior rounds probe (estimation, consensus, data structures, streaming, real-time, ML, papers, partitioning, log internals, multi-region, overload control, CDN and media, social graph and caching at scale, ranking and experimentation, industry case studies). Then read [`best_practices/`](best_practices/00_overview.md), at least [Design Principles](best_practices/01_design_principles.md) and [Architectural Patterns](best_practices/05_architectural_patterns.md), so you can defend the structure inside a service and not only the boxes between services (see *Where code-level design fits* below).
2. Work a `*_question.md` file without reading its solution. State assumptions, estimate load, draw a baseline, then reason about failure.
3. Read the matching `*_solution.md`. Compare your trade-offs, not just your boxes and arrows.
4. Answer the solution's **Follow-ups the interviewer will ask** out loud before reading the model answers, then check yourself against **Common mistakes** and **Going from L5 to L6**.
5. Rework the problem under one changed constraint: 100× traffic, multi-region, strict correctness, or a new privacy rule.
6. Build a small version when the solution suggests it.
7. Before a mock, use the fast-review files: [System Design Practice Prompts](03_practice_prompts.md), [System Design Reference Answers](04_practice_answers.md), [41 System Design Architecture Blueprints](05_architecture_blueprints.md). Read one of the scripted 45-minute answers in [Spoken Walkthroughs](06_spoken_walkthroughs.md) aloud against a timer to calibrate pacing and wording.
8. Drill the follow-up questions interviewers ask *between* the big prompts with the [interview question bank](07_interview_question_bank.md): 42 questions tagged by level, each with a 30-second answer, the full reasoning and the next follow-up, hidden until you have answered out loud.

**Where code-level design fits.** A design round is scored on the system, but senior interviewers also probe the structure *inside* a service: "how would you keep the ranking logic swappable?", "is this a microservice or a module?", "event sourcing or CRUD for the ledger?". The [`best_practices/`](best_practices/00_overview.md) folder is this module's compact reference for exactly those questions: SOLID and related principles, the GoF patterns (with when each is over-engineering), architectural patterns (layered, hexagonal, clean, monolith versus microservices, event-driven, CQRS, event sourcing, DDD basics), code-quality practice, and anti-patterns. It is kept here, next to the building blocks, because its architectural-patterns and anti-patterns files are the vocabulary for service boundaries in a design answer. Read it after the building blocks, or whenever a solution's trade-off leans on one of those patterns. The full treatment (testability, refactoring, error handling, concurrency in code, and the low-level design interview with its problem sets) lives in the separate Software Design module ([foundations](../SoftwareDesign/00_software_design_foundations.md), [low-level design interview playbook](../SoftwareDesign/14_low_level_design_interview_playbook.md)); use that for LLD and object-oriented design rounds.

## Learning path by level

The same material serves every level; what changes is how deep you go and what you are
expected to volunteer.

| Target | Focus | You should be able to |
|---|---|---|
| **L3/L4 · Junior–Mid** | Building blocks `00`–`13`, problems `001`–`010`, the L4 questions in the [question bank](07_interview_question_bank.md) | Produce a working design with the standard components, use each correctly, and estimate load |
| **L5 · Senior** | All building blocks `00`–`20`, problems `001`–`030` timed at 45 minutes, every live lab, L4–L5 questions | Drive the round: numbers first, two options compared, a decision with its cost, failure modes and monitoring raised unprompted |
| **L6+ · Staff** | Building blocks `21`–`32`, problems `031`–`041`, each solution's “Going from L5 to L6”, the L6 questions and the grading table in the bank | Handle ambiguity and evolution: the requirement that really drives the design, 10× growth, multi-region, migrations, cost and team impact |

If the CS underneath feels shaky — queues, TCP, isolation levels, replication — pause and
read the matching chapter of the CS Fundamentals module; its labs and question bank cover
the foundations these designs rest on.

## Deepened building blocks

Blocks `03` (API design), `05` (databases), `08` (object storage), `09` (messaging), `12`
(resilience), `13` (scaling and load balancing), `16` (platform), `18` (estimation), `20`
(specialized data structures), `21` (batch and stream), `22` (real-time), `23` (ML and LLM systems)
and `25` (partitioning) open with a **Foundations** section for readers new to the topic and close
with a **level table** and an **interview checklist**. In between, each adds runnable simulations
whose real output is in the text: load-balancing algorithms and the fast-failure black hole,
consistent hashing with virtual nodes, hot keys under Zipf traffic, consumer catch-up time, retry
reordering, metastable retry storms, fan-out tail latency and hedging, CPU throttling, canary
detection time, sketch error bounds, OT vs CRDT merges, reconnect storms, offset vs cursor
pagination, N+1 queries, rate-limiter algorithms, erasure-coding durability, multipart uploads,
storage-tier costs, Little's law, percentile arithmetic, shuffle skew, watermarks, delivery
semantics, columnar storage, feature leakage, vector-index recall, LLM memory and continuous
batching. The OS, networking, database-internals, distributed-theory, transactions and consensus
blocks point to the matching CS Fundamentals chapters for the mechanisms underneath.

## Live labs

Most building blocks and every practice problem's reference design carry interactive,
animated labs placed next to the section they explain: request flows through each
reference architecture, and concept labs for the arithmetic of distributed systems —
queueing and the utilization hockey stick, composing availability nines, consistent
hashing, quorums, Raft, Lamport and vector clocks, gossip, replication vs erasure coding,
rate-limiting algorithms, caching and stampedes, LSM trees, B+ trees, isolation
anomalies, TCP windows, and latency numbers. Change the inputs, predict the result, then
press play.

The goal is not to memorize “the architecture” of a famous product. The goal is to reliably answer: **what is true, what is slow, what can fail, what must be consistent, and why this component is justified.**

## Learning modules

| Module | Outcome |
|---|---|
| [Google L5 playbook](00_google_l5_playbook.md) | How the round is scored, the 45-minute timeline, estimation numbers, deep dives by problem family, and red flags. |
| [Company interview guide](01_company_interview_guide.md) | How Google, Meta, Netflix and Amazon rounds differ in format, level expectations and depth areas, with a reading and practice path through this module for each. |
| [Building blocks](building_blocks/00_overview.md) | Select and connect the core components of a production system — OS, networking, APIs, databases, caching, messaging, distributed-systems theory, resilience, scaling, security, observability, and platform/infra, one topic per file. Files 18–32 add senior-level depth: estimation, consensus, specialized data structures, stream processing, real-time collaboration, ML/LLM systems, the Google papers, partitioning, distributed log internals, multi-region and global traffic, overload control, CDN and streaming media, social graph and caching at scale, ranking and experimentation, and industry papers and case studies. |
| [Best practices](best_practices/00_overview.md) | Defend the code and service structure inside a box: SOLID and related principles, creational/structural/behavioral patterns, architectural patterns (hexagonal, clean, microservices, event-driven, CQRS, event sourcing, DDD), code-quality practice, and anti-patterns. Eight files, `00`–`07`. |
| [02 — Problem catalog](02_problem_catalog.md) | Practice the most reusable interview and real-world patterns: 41 problems (`001`–`041`), from URL shortener to email service. |
| [Problems](problems) | Blank prompts to solve independently. |
| [Solutions](solutions) | Full reference designs: estimates, API, data model, deep dives, failure behavior, interviewer follow-ups, common mistakes, and the L5→L6 step. |
| [Fast review](03_practice_prompts.md) | One-paragraph prompts ([03](03_practice_prompts.md)), answers ([04](04_practice_answers.md)) and blueprints ([05](05_architecture_blueprints.md)) for all 41 problems. |
| [Interview question bank](07_interview_question_bank.md) | 42 questions interviewers ask between the big prompts — estimation, caching, sharding, consistency, queues, reliability, measured failure modes, staff-level scenarios — tagged by level with layered answers, plus a table of how the same problem is graded at L4, L5 and L6. |
| [Spoken walkthroughs](06_spoken_walkthroughs.md) | Five full 45-minute answers (URL shortener, news feed, seat reservation, ad clicks, key-value store) scripted in the first person with the clock and interviewer interjections, for pacing and wording. |

## Rules for every problem

- Do not introduce a component without naming the requirement it solves.
- A technology name is not a reason. State its property and its downside.
- Every write needs a source of truth, an idempotency story, and a failure story.
- Every asynchronous path needs ordering scope, retry policy, poison-message handling, and replay plan.
- Every cache needs a source of truth, TTL/invalidation rule, and outage behavior.
- Every system needs user-facing SLOs and a recovery plan.
- Every number gets a consequence: say what decision it forces.
