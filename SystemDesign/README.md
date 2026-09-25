# System Design Mastery Curriculum

Learn system design in this order:

0. Read [`00_google_l5_playbook.md`](00_google_l5_playbook.md) first: how the Google design round is scored, the 45-minute timeline, and the signals that separate L4 from L5 (and L5 from L6). Then read [`01_company_interview_guide.md`](01_company_interview_guide.md) for how Meta, Netflix and Amazon rounds differ and which parts of this module to lean on for each.
1. Read `building_blocks/00_overview.md` and work through the directory in order until you can explain each component in plain language. Files `00`–`17` are the core sequence; `18`–`32` add the depth that senior rounds probe (estimation, consensus, data structures, streaming, real-time, <abbr title="Machine Learning">ML</abbr>, papers, partitioning, log internals, multi-region, overload control, CDN and media, social graph and caching at scale, ranking and experimentation, industry case studies).
2. Work a `*_question.md` file without reading its solution. State assumptions, estimate load, draw a baseline, then reason about failure.
3. Read the matching `*_solution.md`. Compare your trade-offs, not just your boxes and arrows.
4. Answer the solution's **Follow-ups the interviewer will ask** out loud before reading the model answers, then check yourself against **Common mistakes** and **Going from L5 to L6**.
5. Rework the problem under one changed constraint: 100× traffic, multi-region, strict correctness, or a new privacy rule.
6. Build a small version when the solution suggests it.
7. Before a mock, use the fast-review files: [`03_practice_prompts.md`](03_practice_prompts.md), [`04_practice_answers.md`](04_practice_answers.md), [`05_architecture_blueprints.md`](05_architecture_blueprints.md). Listen for pacing and wording in [`06_spoken_walkthroughs.md`](06_spoken_walkthroughs.md).

Code-level design (SOLID, patterns, testability, refactoring, low-level design interviews) lives in the separate Software Design module (its 14 chapters and the LLD problem sets), not here.

The goal is not to memorize “the architecture” of a famous product. The goal is to reliably answer: **what is true, what is slow, what can fail, what must be consistent, and why this component is justified.**

## Learning modules

| Module | Outcome |
|---|---|
| [Google L5 playbook](00_google_l5_playbook.md) | How the round is scored, the 45-minute timeline, estimation numbers, deep dives by problem family, and red flags. |
| [Company interview guide](01_company_interview_guide.md) | How Google, Meta, Netflix and Amazon rounds differ in format, level expectations and depth areas, with a reading and practice path through this module for each. |
| [Building blocks](building_blocks/00_overview.md) | Select and connect the core components of a production system — OS, networking, APIs, databases, caching, messaging, distributed-systems theory, resilience, scaling, security, observability, and platform/infra, one topic per file. Files 18–32 add senior-level depth: estimation, consensus, specialized data structures, stream processing, real-time collaboration, <abbr title="Machine Learning">ML</abbr>/<abbr title="Large Language Model">LLM</abbr> systems, the Google papers, partitioning, distributed log internals, multi-region and global traffic, overload control, CDN and streaming media, social graph and caching at scale, ranking and experimentation, and industry papers and case studies. |
| [02 — Problem catalog](02_problem_catalog.md) | Practice the most reusable interview and real-world patterns: 41 problems from URL shortener to lock service. |
| [Problems](problems) | Blank prompts to solve independently. |
| [Solutions](solutions) | Full reference designs: estimates, <abbr title="Application Programming Interface">API</abbr>, data model, deep dives, failure behavior, interviewer follow-ups, common mistakes, and the L5→L6 step. |
| [Fast review](03_practice_prompts.md) | One-paragraph prompts, answers and blueprints for all 41 problems, plus full spoken walkthroughs for pacing. |

## Rules for every problem

- Do not introduce a component without naming the requirement it solves.
- A technology name is not a reason. State its property and its downside.
- Every write needs a source of truth, an idempotency story, and a failure story.
- Every asynchronous path needs ordering scope, retry policy, poison-message handling, and replay plan.
- Every cache needs a source of truth, TTL/invalidation rule, and outage behavior.
- Every system needs user-facing SLOs and a recovery plan.
- Every number gets a consequence: say what decision it forces.
