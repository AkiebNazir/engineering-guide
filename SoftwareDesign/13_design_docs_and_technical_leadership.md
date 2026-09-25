# Design Docs and Technical Leadership

> "Weeks of coding can save you hours of planning." — engineering folklore
>
> "If you can't write it down clearly, you don't understand it yet."

At Google and most large engineering organisations, significant work starts with a
**design doc**. For an L5 candidate, design docs matter three ways:

1. **They are how senior engineers actually lead** — so they are the backbone of the best
   behavioural stories.
2. **They are the written form of a system design round** — the same sections, the same
   trade-off reasoning, in the same order.
3. **Writing and reviewing them well is a skill interviewers probe** — "how did you get
   alignment on that approach?", "tell me about a time you disagreed with a design".

`01_philosophy_of_software_design.md` is about making **code** simple. This file is about
making **decisions** clear, shared, and reversible when they turn out to be wrong — and
about the rest of what "technical leadership" means day to day at L5.

**Already covered elsewhere — not repeated here:**

| Topic | Where |
|---|---|
| How Google scores leadership and Googleyness | `GoogleBehavioral/01_how_google_scores_and_googleyness.md` |
| STAR structure, story bank, L5 leadership stories | `GoogleBehavioral/02–04` |
| System design interview structure | `SystemDesign/00_google_l5_playbook.md` |
| Back-of-envelope estimation | `SystemDesign/building_blocks/18_back_of_envelope_estimation.md` |
| Technical debt as a design decision; code review as design review | `05_testability_refactoring_and_legacy_code.md` §9–§10 |
| "Design it twice" | `01_philosophy_of_software_design.md` §15 |
| Threat modeling (STRIDE) for the security section | `12_secure_code_by_design.md` §12 |

---

## Contents

1. [Why design docs exist](#1--why-design-docs-exist)
2. [When to write one — and what to write instead](#2--when-to-write-one--and-what-to-write-instead)
3. [The structure](#3--the-structure)
4. [A complete example design doc](#4--a-complete-example-design-doc)
5. [Writing well: before-and-after rewrites](#5--writing-well-before-and-after-rewrites)
6. [Planning inside the doc: milestones, estimates, risk](#6--planning-inside-the-doc-milestones-estimates-risk)
7. [Architecture Decision Records](#7--architecture-decision-records)
8. [Running the review — and reviewing others' docs](#8--running-the-review--and-reviewing-others-docs)
9. [Disagreement: from opinions to decisions](#9--disagreement-from-opinions-to-decisions)
10. [Reversibility: one-way and two-way doors](#10--reversibility-one-way-and-two-way-doors)
11. [Other written artifacts senior engineers produce](#11--other-written-artifacts-senior-engineers-produce)
12. [Technical leadership beyond the doc](#12--technical-leadership-beyond-the-doc)
13. [Using this in interviews](#13--using-this-in-interviews)
14. [Interview questions and model answers](#14--interview-questions-and-model-answers)
15. [Checklist](#15--checklist)

---

## 1 · Why design docs exist

- **Find problems when they're cheap.** A wrong decision caught in a doc review costs an
  hour; caught in code review, a week; caught in production, a quarter. Writing forces
  vague ideas into specifics, and specifics are where the problems show.
- **Build consensus asynchronously** across teams and time zones, without a meeting for
  every question.
- **Record the why.** Code records *what* the system does. Six months later, only the doc
  explains why it looks this way — including the alternatives that were rejected, which code
  never records. That prevents re-litigating settled questions and repeating failed
  experiments.
- **Scale your influence.** A senior engineer's leverage is in decisions many people
  execute; a doc is how those decisions travel to people who weren't in the room.
- **Make ownership and scope explicit.** Goals, non-goals, and milestones turn "improve
  checkout" into something a team can plan, staff, and finish.

What design docs are **not**: a bureaucratic gate, a specification of every class, or a
document that must stay perfect forever. Google's own engineering culture treats them as
informal, lightweight, and mostly valuable during the design phase.

---

## 2 · When to write one — and what to write instead

Write a doc when the work has any of:

- More than ~2 engineer-weeks of effort, or more than one team involved.
- A change that is **hard to reverse**: data models, public APIs, storage engines,
  security boundaries, vendor commitments (§10).
- A change to an <abbr title="Service Level Objective - A specific target level for the reliability of a service, usually defined by a numerical goal for a metric.">SLO</abbr>, cost profile, or on-call burden.
- Meaningful security, privacy, legal, or compliance implications.
- A decision people will disagree about.

Don't write one when the solution is obvious and cheap to change, or when you'd learn
more from a one-day prototype than a one-week document — build the prototype, then write
the doc with the prototype's results.

| Size of decision | Artifact | Length | Review |
|---|---|---|---|
| A local implementation choice | Code comment, PR description | A paragraph | Code review |
| One significant decision with lasting consequences | **ADR** (§7) | Half a page | Team |
| "Is this problem worth solving?" | **One-pager** | 1–2 pages | Manager, TL, stakeholders |
| A feature or system spanning weeks/teams | **Design doc** (§3–§4) | 3–10 pages | Owners of affected systems, security/privacy, SRE |
| A shared <abbr title="Application Programming Interface">API</abbr> or cross-org contract | **RFC / <abbr title="Application Programming Interface">API</abbr> proposal** | Varies | <abbr title="Application Programming Interface">API</abbr> review board, consumers |
| A multi-quarter program | **Strategy / vision doc** + several design docs | 5–15 pages | Leadership |

A 30-page design doc usually means the scope should be split into several docs.

---

## 3 · The structure

Google-style design docs vary by team, but most contain these sections:

```text
Title · Author(s) · Reviewers · Status (draft / in review / approved / implemented / obsolete) · Last updated

1. Context and scope        What exists today, what's wrong or missing, why now. Brief.
2. Goals and non-goals      Measurable goals. Explicit NON-goals: things a reasonable
                            reader might expect that you're deliberately not doing.
3. Overview                 The proposed design in a paragraph and one diagram.
4. Detailed design          APIs, data model, data flow, key algorithms — the parts that
                            are actually hard or contentious. Not every class.
5. Alternatives considered  Each serious alternative, its trade-offs, and why it lost.
                            Often the most valuable section.
6. Cross-cutting concerns   Security, privacy, reliability/SLOs, observability,
                            scalability, cost, accessibility, compliance.
7. Rollout and migration    Phases, flags, compatibility, data migration, rollback plan,
                            success metrics.
8. Milestones               What ships when; what each milestone proves.
9. Risks and open questions What you don't know yet and how you'll find out.
```

What each section is **for**:

| Section | The reviewer's question it answers |
|---|---|
| Context | "Do I understand the problem well enough to judge the solution?" |
| Goals / non-goals | "How will we know it worked, and what are we deliberately not doing?" |
| Overview | "What's the idea, in 60 seconds?" |
| Detailed design | "Will it actually work? Where are the hard parts?" |
| Alternatives | "Did the author consider the options I would have suggested?" |
| Cross-cutting | "What will hurt us in production, in a security review, or on the bill?" |
| Rollout | "How do we get there safely, and how do we back out?" |
| Milestones | "When do we learn whether this is working?" |
| Risks / open questions | "What could make this plan wrong?" |

---

## 4 · A complete example design doc

### The same structure, at 30 seconds

Before the realistic (and longer) example below, here's the §3 structure filled in for a
decision small enough to read in one breath — the shape doesn't change with size, only
the depth:

```text
Design: Add a GET /healthz endpoint to the checkout service
Status: Approved

CONTEXT    SRE has no way to tell the process is up without sending real traffic.
GOAL       An uptime check can confirm the process is alive in < 50 ms.
OVERVIEW   Add GET /healthz, returning 200 "ok" once startup has finished. No auth,
           no dependency checks — this is liveness, not readiness.
ALTERNATIVE  Also check DB connectivity here — rejected: that's a readiness concern,
             not liveness (`10_designing_observable_code.md` §7), and would fail every
             replica at once during a DB blip.
ROLLOUT    Additive route, no flag needed; ships in the next regular deploy.
```

That's a real, reviewable design doc — it just has a decision small enough that every
section is one line. The next example is the same nine sections at the size and depth a
multi-team, hard-to-reverse decision actually needs.

### The full worked example

A condensed but realistic example. Real docs have more prose; the shape and the
decisions are what matter.

```text
═══════════════════════════════════════════════════════════════════════════════════════
 Design: Safe client retries for the Payments API (idempotency keys)
 Author: <you> · Reviewers: payments-core TL, API platform, SRE (payments), security
 Status: In review · Last updated: 2026-09-17
═══════════════════════════════════════════════════════════════════════════════════════

1. CONTEXT
   POST /v1/charges is not idempotent. Mobile clients retry on timeout (client p99
   network timeout: 10 s). In Q2, 0.04% of charges (~3,100/month) were duplicates,
   each refunded manually by support at ~$9 handling cost plus chargeback risk.
   Server-side dedupe by (customer, amount, 60 s window) was tried in 2024 and removed:
   it blocked legitimate repeat purchases (design doc: go/charges-dedupe-postmortem).

2. GOALS
   G1. Duplicate charges caused by client retries: 0.04% → < 0.001% of charges.
   G2. Added latency on POST /v1/charges: ≤ 5 ms p99.
   G3. Existing clients keep working unchanged (the header is optional in v1).
   G4. Available to all API clients, including third-party integrators, by Q1.

   NON-GOALS
   N1. Idempotency for endpoints other than charge creation (refunds follow in a separate doc).
   N2. Deduplicating charges that clients intentionally submit twice with different keys.
   N3. Exactly-once delivery of webhooks.

3. OVERVIEW
   Clients send an Idempotency-Key header (UUID) with POST /v1/charges. The API stores
   (key, request fingerprint, status, response) in the payments database IN THE SAME
   TRANSACTION as the charge record. A retry with the same key returns the stored
   response; a different request body with the same key returns 422.

      client ──POST + Idempotency-Key──▶ API ──┬─▶ idempotency_keys (claim)  ┐ one DB
                                               └─▶ charges (insert)          ┘ transaction
                                                     │
                                                     └─▶ card processor (processor key = charge id)

4. DETAILED DESIGN
   4.1 API
       Header: Idempotency-Key: <1–64 chars, [A-Za-z0-9-_]>. Keys are scoped per API account.
       Same key + same fingerprint + completed      → original status code and body, plus
                                                      header Idempotent-Replayed: true
       Same key + same fingerprint + in progress    → 409 {"error": "request_in_progress"}
       Same key + different fingerprint             → 422 {"error": "idempotency_key_reused"}
       Keys expire 24 h after first use (documented).

   4.2 Data model
       idempotency_keys(
         account_id, key, PRIMARY KEY (account_id, key),
         fingerprint BYTEA,           -- SHA-256 of method + path + canonical JSON body
         status TEXT,                 -- in_progress | completed
         response_code INT, response_body JSONB,
         charge_id UUID NULL,
         created_at TIMESTAMPTZ, expires_at TIMESTAMPTZ)
       Index on expires_at for the cleanup job.

   4.3 Flow
       1. BEGIN; INSERT key row (status=in_progress) ON CONFLICT DO NOTHING.
       2. If conflict: read the row → replay / 409 / 422 as in 4.1. COMMIT.
       3. Else: INSERT charge (status=pending). COMMIT.
       4. Call processor with processor idempotency key = charge_id (processor dedupes 24 h).
       5. BEGIN; UPDATE charge status; UPDATE key row (completed, response). COMMIT.
       Crash between 3 and 5: the reconciler finds pending charges older than 2 min, queries
       the processor by charge_id, and completes both rows.

   4.4 Capacity
       Peak 1,800 charges/s → 1,800 key inserts/s; 24 h retention ≈ 155M rows × ~600 B
       ≈ 95 GB. Payments DB has 2.1 TB free; expiry job deletes in 10k-row batches.

5. ALTERNATIVES CONSIDERED
   A. Server-side dedupe by (customer, amount, time window) — REJECTED.
      No client changes, but cannot distinguish a retry from a real repeat purchase;
      already failed in 2024 (false positives).
   B. Store keys in Redis with a 24 h TTL — REJECTED.
      Lower latency (~1 ms vs ~3 ms). But the key and the charge would not commit
      atomically: a Redis write followed by a DB failure (or the reverse) reopens
      the duplicate window, and a Redis failover loses keys. Correctness is the goal.
   C. Client-generated charge IDs (PUT /v1/charges/{id}) — DEFERRED to v2.
      Cleanest REST semantics, naturally idempotent. But a breaking API change for
      ~4,000 integrators; revisit with the v2 API.
   D. Do nothing; improve the manual refund tooling — REJECTED.
      Cheaper now, but costs ~$28k/month in support and leaves chargeback exposure.

6. CROSS-CUTTING CONCERNS
   Security:    Keys scoped per account (no cross-account replay). Stored responses
                contain no card data (only charge id, last4, status). Rate limit on
                422/409 responses to stop key probing.
   Privacy:     Stored bodies follow the charges table's 24 h → deletion policy.
   Reliability: No new dependency. If the key insert fails, the request fails (fail
                closed) — never charge without a claimed key when one was supplied.
   Observability: idempotent_replays_total, key_reuse_conflicts_total,
                in_progress_conflicts_total; reconciler lag; trace attribute
                idempotency.replayed.
   Cost:        ~95 GB storage; no new infrastructure.

7. ROLLOUT
   Phase 0: Schema migration (additive table). Reconciler deployed, dry-run mode.
   Phase 1: Header accepted, behind flag, for 2 internal clients; compare duplicates.
   Phase 2: 10% → 50% → 100% of accounts over 2 weeks; SDKs send keys automatically.
   Phase 3: Public docs; announce to integrators.
   Rollback: disable the flag → header ignored, behaviour as today; table retained.
   Success:  G1 measured via the weekly duplicate-charge report; G2 via latency SLO dashboard.

8. MILESTONES
   M1 (wk 2): Internal clients using keys; latency impact measured (validates G2).
   M2 (wk 5): 100% of accounts; SDK releases (validates G1 for SDK users).
   M3 (wk 8): Duplicate rate reported < 0.001% for 2 consecutive weeks.

9. RISKS AND OPEN QUESTIONS
   R1. Fingerprinting on canonical JSON: SDKs that reorder fields or add default
       fields could cause false 422s. → Canonicalise; fingerprint only documented fields;
       test against all 5 official SDKs in M1.
   R2. Hot-row contention if a buggy client reuses one key at high rate.
       → Per-key 409 is cheap; rate limit conflicts.
   Q1. Should keys be required in v2? (Decision owner: API platform; by M2.)
═══════════════════════════════════════════════════════════════════════════════════════
```

What makes this doc effective, section by section:

- **Context quantifies the pain** (0.04%, ~3,100/month, $9 each) and cites the prior failed
  attempt, so no reviewer proposes it again.
- **Goals are numbers with a measurement plan**; G3 and G4 constrain the solution space.
  Non-goals pre-empt the three most likely scope expansions.
- **The overview fits on a screen.** A reader who stops there knows the idea.
- **The detailed design goes deep only on the hard parts**: the atomicity of key + charge,
  the crash window, the error semantics. It doesn't describe handler classes.
- **Alternatives are real**, including "do nothing" and a genuinely better-but-breaking
  option (C) that is deferred rather than dismissed.
- **Cross-cutting concerns** name specific decisions (fail closed, what's stored), not
  "we will consider security".
- **Rollout has a rollback**, and every milestone *proves* something rather than just
  marking progress.

---

## 5 · Writing well: before-and-after rewrites

### Goals

| Weak | Strong |
|---|---|
| "Improve checkout performance." | "Reduce checkout p99 server latency from 1.2 s to < 500 ms at peak load, without increasing fraud losses above 0.1% of GMV." |
| "Make the system more reliable." | "Raise monthly availability of `/search` from 99.5% to 99.9% (≤ 43 min downtime/month) as measured by the external prober." |
| "Support more users." | "Handle 3× current peak (15k QPS) on the same hardware budget ±10%." |

### Non-goals

| Weak | Strong |
|---|---|
| (none written) | "Non-goal: migrating existing reports to the new engine; they keep running on the old one until Q3." |
| "Non-goal: bugs." | "Non-goal: real-time updates. Dashboards may be up to 5 minutes stale." |

A non-goal is only useful if a reasonable reader might otherwise assume it's included.

### Leading with the decision

| Weak (journey first) | Strong (decision first) |
|---|---|
| "We first looked at Redis, then considered DynamoDB, and after some benchmarking we eventually felt Postgres might work best, which we propose below." | "We propose storing idempotency keys in the existing Postgres database, in the same transaction as the charge. Redis and DynamoDB were rejected because keys and charges couldn't commit atomically (§5)." |

### Explicit trade-offs

| Weak (hidden) | Strong (named) |
|---|---|
| "The new design is simpler and faster." | "We accept up to 5 s of staleness in the order list in exchange for removing the synchronous dependency on the inventory service, which caused 3 of last quarter's 5 checkout incidents." |

### Alternatives

| Weak (strawman) | Strong |
|---|---|
| "Alternative: rewrite everything in Rust. Rejected: too much work." | "Alternative: shard the existing Postgres by tenant. Pros: no new technology, keeps joins within a tenant. Cons: cross-tenant reports need a scatter-gather layer; re-sharding is manual. Rejected because 30% of queries are cross-tenant (analysis in appendix A)." |

### Precision

- **Quantify:** QPS, storage, cost, latency budgets — estimates turn opinions into
  arithmetic.
- **Define terms** on first use; avoid team jargon and code names outsiders don't know.
- **Diagrams:** one context diagram and one data-flow diagram for the main path beat ten
  diagrams. Label arrows with what flows and whether it's sync or async.
- **Write for the skeptical reader who wasn't in your meetings.** Link prior docs rather
  than assuming shared memory.
- **Use "we propose", not "we might consider".** Hedged language makes reviewers do the
  deciding.

---

## 6 · Planning inside the doc: milestones, estimates, risk

A design that can't be planned can't be delivered. The doc should make the plan visible.

### Order work by risk, not by layer

```
 LAYER ORDER (risky)                      RISK ORDER (better)
 ───────────────────                      ────────────────────
 1. Database schema                       1. Spike: can Postgres hold key+charge
 2. Repository layer                         atomically within 5 ms p99? (the crux)
 3. Service layer                         2. Walking skeleton: header → table → replay,
 4. API                                      end to end, behind a flag, one client
 5. SDKs                                  3. Crash recovery (reconciler)
 6. Discover the latency goal is             4. Rollout tooling, SDKs, docs
    impossible in week 7                  5. Polish
```

- **Retire the biggest unknowns first** with spikes or prototypes. If the crux assumption
  is wrong, find out in week 1, not week 7.
- **A walking skeleton** — the thinnest end-to-end slice through every component — exposes
  integration problems early and gives something real to measure.
- **Each milestone should prove something** (a goal met, a risk retired) and ideally ship
  value on its own.

### Estimates

- **Estimate in ranges with confidence:** "3–5 weeks, 80% confident; the range is driven
  by SDK release cycles we don't control."
- **Break work down until pieces are ≤ 1 week**; unknown pieces become spikes with a
  timebox instead of estimates.
- **Name dependencies on other teams** explicitly, with owners and dates you've agreed with
  them — not dates you hope for.
- **Add the unglamorous work:** migrations, dashboards, alerts, runbooks, load tests,
  documentation, security review, the rollout itself. It is commonly a third of the total.

### Risk register

| Risk | Likelihood | Impact | Mitigation | Owner | Trigger to act |
|---|---|---|---|---|---|
| Fingerprint false positives from SDK field ordering | Medium | High (legit charges blocked) | Canonical JSON; SDK compatibility tests in M1 | you | Any 422 from official SDKs in canary |
| Payments DB write latency | Low | Medium | Load test at 2× peak before Phase 2 | SRE | p99 insert > 5 ms |
| <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> team capacity | Medium | Medium (delays G1) | Agreed dates; we contribute PRs | <abbr title="Software Development Kit. A collection of software development tools in one installable package.">SDK</abbr> TL | M2 slip > 1 week |

---

## 7 · Architecture Decision Records

A design doc covers a project. An **ADR** records **one decision** — short, immutable, and
stored next to the code (`docs/adr/0007-idempotency-keys-in-postgres.md`) so it's found by
the people who change that code.

### Template (Michael Nygard's format)

```markdown
# ADR-NNNN: <decision as a short noun phrase>

Status: Proposed | Accepted | Superseded by ADR-MMMM | Deprecated
Date: YYYY-MM-DD
Deciders: <names/roles>

## Context
The forces at play: requirements, constraints, facts. Neutral; no solution yet.

## Decision
"We will …" in active voice.

## Consequences
What becomes easier, what becomes harder, what we must now do. Include the negatives.

## Alternatives considered (optional)
One line each, with the reason they lost.
```

### Example

```markdown
# ADR-0007: Store idempotency keys in the payments Postgres database

Status: Accepted · Date: 2026-09-17 · Deciders: payments-core TL, API platform TL

## Context
Charges must not be duplicated when clients retry. A key record and its charge must
commit or fail together; a gap between them re-opens the duplicate window. Peak load is
1,800 charges/s; the latency budget for the check is 5 ms p99. The payments database
already runs at 35% write capacity.

## Decision
We will store idempotency keys in a new `idempotency_keys` table in the payments
Postgres database and write each key in the same transaction as its charge.

## Consequences
+ Atomic key/charge commits; no new infrastructure or failure mode.
+ Keys follow the database's existing backup and retention policies.
− ~95 GB additional storage and ~3 ms added p99 latency.
− Expiry requires a batch deletion job; we own its monitoring.
− Moving charges to another datastore later means moving keys with them.

## Alternatives considered
- Redis with TTL: faster, but not atomic with the charge; failover loses keys.
- Client-generated charge IDs (PUT): cleanest, but a breaking change; revisit for API v2.
```

**Rules:** one decision per ADR; never edit an accepted ADR's decision — supersede it with a
new ADR that links back; write the consequences honestly, including the costs, because those
are what future engineers need.

---

## 8 · Running the review — and reviewing others' docs

### As the author

1. **Socialise early.** Share a one-page sketch with the one or two people most likely to
   object *before* writing ten pages. Surprises in a big review meeting are expensive, and
   people defend positions they've taken publicly.
2. **Pick reviewers deliberately:** owners of systems you depend on or change, security and
   privacy reviewers when relevant, SRE for production changes, a senior engineer who'll
   challenge the core premise, and — for learning — a less experienced engineer.
3. **Tell reviewers what you need:** "Please focus on §4.3's crash recovery and §5's Redis
   rejection. Deadline: Thursday."
4. **Asynchronous comments first**; a meeting only for unresolved disagreements, with an
   agenda listing those threads.
5. **Resolve every comment** — accept, reject with a reason, or record it as an open
   question with an owner. Unresolved threads are where later conflict comes from.
6. **Agree how decisions get made** when reviewers disagree: who decides, and what evidence
   would change the decision (§9).
7. **Mark it approved**, then keep it honest: update it when implementation diverges, or add
   a note at the top saying which sections are obsolete.

### As a reviewer

Good reviewing is one of the most visible forms of senior leadership. The difference is in
the comments.

| Weak comment | Strong comment |
|---|---|
| "Have you considered Kafka?" | "Consider Kafka for the event stream: consumers could replay from an offset after the reconciler crashes, which the current queue can't do. Cost: a new dependency for this team. Worth a line in §5 either way." |
| "This won't scale." | "At 1,800 charges/s with 24 h retention, the key table reaches ~155M rows. Does the expiry job's batch delete keep up during peak? A load-test number in §4.4 would settle it." |
| "I don't like this approach." | "My concern is operational: this adds a third datastore our on-call must understand. Would the doc's goals still be met by the existing Postgres? If not, which goal forces Redis?" |
| "LGTM" on a doc you skimmed | "Reviewed §3–§5 closely; didn't review the rollout — @sre-reviewer is better placed." |
| Twenty nits on wording | Blocking concerns first, clearly labelled; nits batched and marked optional |

A useful labelling convention:

- **[blocking]** — must be resolved before approval, with the reason.
- **[question]** — you want to understand; not necessarily a problem.
- **[suggestion]** — take it or leave it.
- **[nit]** — trivial; author's discretion.

Review the **premise** before the details: is this the right problem, are the goals right,
is there a much simpler option? Detailed comments on a design that shouldn't be built waste
everyone's time.

---

## 9 · Disagreement: from opinions to decisions

Design disagreements are the most common source of L5 behavioural stories (see
`GoogleBehavioral/03_L5_leadership_deep_dive.md`). Techniques that work:

| Technique | How it helps |
|---|---|
| **Agree on criteria first** | "We're optimising for p99 latency and on-call load, not development speed" makes options comparable |
| **Steelman the other option** | Write the other side's proposal as strongly as they would; often reveals a hybrid |
| **Identify the crux** | Most disagreements hinge on one factual question — answer it with a prototype, benchmark, or data |
| **Separate facts, predictions, and preferences** | Facts can be checked; predictions can be tested cheaply; preferences need a decider |
| **Classify reversibility** | Two-way doors decided fast; one-way doors get more rigour (§10) |
| **Timebox and name a decider** | Prevents indefinite debate; everyone knows how it ends |
| **Disagree and commit** | Once decided, everyone executes fully; record dissent and the metric that would trigger revisiting |
| **Escalate as a joint question, not a complaint** | "We need a decision between A and B; here's a one-page comparison we both agree is fair" |

### A worked example

```
 SITUATION   You propose Postgres for idempotency keys. A senior engineer on another team
             strongly prefers Redis: "Postgres will add too much latency."

 1. CRITERIA   Agree in a 15-minute call: correctness (no duplicates) is the top goal;
               latency budget is 5 ms p99; operational load matters.

 2. CRUX       The disagreement is not "Postgres vs. Redis" — it's a factual prediction:
               "a same-transaction key insert adds more than 5 ms p99."

 3. EVIDENCE   Two-day spike: load test at 2× peak on a staging replica.
               Result: +3.1 ms p99. The prediction is testable, and it was wrong.

 4. STEELMAN   The Redis concern is still valid at 10× growth. Record it: "Revisit if
               p99 impact exceeds 4 ms or write load exceeds 60% of capacity."

 5. DECIDE     The payments TL (named decider) approves Postgres; ADR written with the
               revisit trigger; the other engineer reviews the load-test method and signs off.
```

In a behavioural answer, this is the shape interviewers look for: **you made it about data
and shared criteria, you took the other view seriously, you ended with a decision and a
mechanism to revisit, and the relationship survived.**

### Decision frameworks

For cross-team decisions, name the roles explicitly. **DACI** is common:

| Role | Meaning | Count |
|---|---|---|
| **D**river | Runs the process, gathers input, writes the doc | 1 |
| **A**pprover | Makes the decision | Exactly 1 |
| **C**ontributors | Consulted for expertise; their input shapes the decision | Several |
| **I**nformed | Told the outcome | Many |

The failure mode it prevents: five stakeholders who each believe they have a veto, and a
decision that never happens.

---

## 10 · Reversibility: one-way and two-way doors

Jeff Bezos's framing, widely used: **two-way doors** can be walked back through cheaply;
**one-way doors** can't. Spend rigour in proportion.

| Two-way doors — decide fast, learn from production | One-way doors — design docs, prototypes, reviews |
|---|---|
| Internal function and module structure | Public <abbr title="Application Programming Interface">API</abbr> shapes and URLs |
| Choice of library behind an adapter | Data models and storage formats with years of data |
| Feature-flagged behaviour changes | Storage engine / primary database choice |
| Cache TTLs, pool sizes, timeouts | Security and trust boundaries |
| UI copy, experiment variants | Pricing and contractual commitments; deleting data |
| Internal service boundaries within one team | Protocols other organisations integrate against |

Two useful moves:

- **Turn one-way doors into two-way doors.** An adapter around a vendor (`08` §3), a feature
  flag, dual-writing during a migration (`09` §5), or versioned APIs make a hard-to-reverse
  decision reversible for a while.
- **Beware slow one-way doors.** A "temporary" internal <abbr title="Application Programming Interface">API</abbr> that 40 services start calling
  becomes a one-way door by accretion. Notice when a two-way door is closing.

The cost of *not* deciding is real too: a team debating a two-way door for three weeks has
spent more than a wrong choice would have cost.

---

## 11 · Other written artifacts senior engineers produce

| Artifact | Purpose | Size |
|---|---|---|
| **One-pager / proposal** | Agreement that a problem is worth solving before designing | 1–2 pages |
| **RFC / <abbr title="Application Programming Interface">API</abbr> proposal** | Changes to shared APIs or cross-team contracts (Google's public <abbr title="Application Programming Interface">API</abbr> guidance: aip.dev) | Varies |
| **ADR** | One decision, its context, alternatives, consequences (§7) | Half a page |
| **Production readiness review / launch checklist** | Monitoring, alerts, runbooks, capacity, rollback, security review — done before launch | Checklist |
| **Runbook** | What on-call does when an alert fires: diagnosis steps, mitigations, escalation | 1–3 pages per alert family |
| **Postmortem** | Blameless incident analysis with action items | 2–5 pages |
| **Status update** | Progress vs. plan, risks, decisions needed, asks | Weekly, short |

### A one-pager, in full

The one-pager's job is narrower than a design doc's: get agreement that a problem is
worth solving *before* spending a week designing the solution.

```text
One-pager: Should we build in-app receipt scanning?

PROBLEM   23% of expense-report support tickets are "receipt didn't attach" — about
          400 tickets/month at ~12 minutes of support time each.
PROPOSAL  Let users photograph a receipt in the app; OCR fills in amount and vendor.
COST      ~3 engineer-weeks. OCR vendor: ~$0.01/scan, ~$40/month at current volume.
ASK       Approve scoping a full design doc for Q4.
```

Four lines answer one question — is this worth a design doc — and nothing else. A
one-pager that starts describing the OCR pipeline has become a design doc without the
sections that make one reviewable.

### A runbook entry, in full

```text
Alert: idempotent_replay_rate > 5% for 10 minutes (payments)

MEANING    Clients are retrying far more than normal. Usually a client bug or an
           upstream timeout — not necessarily a payments-side problem.
DIAGNOSE   1. Check p99 latency on POST /v1/charges — if elevated, the retries are
              probably caused by us (see the latency runbook).
           2. Check which account IDs dominate replays (dashboard: go/payments-replays).
MITIGATE   Single account driving it: contact them or rate-limit that account.
           Latency-caused: follow the latency runbook.
ESCALATE   Payments on-call if replay rate > 20%, or if any duplicate charge is seen —
           duplicates should be impossible with idempotency keys in place, so one is a
           page, not a ticket.
```

The pattern that makes a runbook usable at 3 a.m.: **diagnose before mitigate**, steps
numbered and checkable half-asleep, and an explicit line for when to stop trying to fix
it yourself and wake someone else.

### Status update that leaders actually read

```text
Idempotency keys — week 4 of 8 · Status: 🟡 AT RISK (was 🟢)

TL;DR: Server side done and at 50% of accounts; duplicates down 91% for those accounts.
       iOS SDK release slipped 2 weeks → M3 at risk by ~1 week.

Progress:  ✅ Phase 2 at 50%; p99 impact +3.1 ms (budget 5 ms)
           ✅ Reconciler live; completed 14 interrupted charges this week
Risks:     iOS SDK release train moved to Oct 12 (owner: SDK TL). Mitigation: server
           accepts keys from the web SDK now; iOS covered in the Oct train.
Decisions needed: Should keys be required in API v2? Need API platform decision by Oct 1.
Asks:      SRE review of the reconciler alert thresholds (30 min).
```

The shape: **status and change first, then evidence, then risks with owners and mitigations,
then explicit decisions and asks.** Never make the reader hunt for bad news.

### Postmortem skeleton

```text
Summary       What happened, impact (users, duration, money, SLO budget), in 3 sentences.
Timeline      UTC timestamps: trigger, detection, escalation, mitigation, resolution.
Root causes   Plural. Contributing factors across code, process, tooling, and detection.
What went well / what went poorly / where we got lucky
Action items  Each: owner, priority, due date, tracking bug. Prefer ones that prevent a
              CLASS of incident (a guardrail) over ones that fix this instance.
```

**Blameless** means analysing the system that let a reasonable person make the mistake —
missing validation, confusing tooling, no canary — not whether the person should have known
better. "Human error" is where the analysis starts, never where it ends.

---

## 12 · Technical leadership beyond the doc

What L5 leadership looks like day to day, independent of title:

| Behaviour | What it looks like concretely |
|---|---|
| **Scoping** | Turning "make checkout faster" into a measurable goal, milestones, and a plan others can pick up without you |
| **Unblocking others** | Reviews within a day; answering design questions; making the call when the team is stuck on a two-way door |
| **Raising the bar** | Code review that teaches; better tests, release practices, and dashboards nobody asked for; fixing the flaky test everyone ignores |
| **Mentoring** | Giving others real ownership of meaningful pieces, with support; letting them present their work |
| **Cross-team alignment** | Knowing owners of the systems you depend on; bringing them in before the doc is written |
| **Saying no, with reasons** | Protecting the team from scope creep and unrealistic dates by making trade-offs visible |
| **Owning outcomes, not tasks** | Measuring whether the launched thing met its goal, and following up when it didn't |
| **Operational ownership** | Improving on-call for the systems you build: alerts that mean something, runbooks, fewer pages |

### Influence without authority

Most of an L5's leadership is over people who don't report to them.

- **Lead with the other team's goals.** "This removes the synchronous call that pages your
  on-call" persuades better than "this helps my project".
- **Do the work to make yes easy:** write the PR against their service, draft the migration,
  offer to handle their review comments.
- **Build credibility before you need it:** review their docs well, help in their incidents,
  deliver what you promised.
- **Use data and prototypes** instead of seniority or volume.
- **Give credit publicly**, especially to the people who changed your mind.

### Mentoring through delegation

```
 Too little support               Right                                Too much
 ──────────────────               ─────                                ────────
 "Here's a vague project,         "You own the reconciler. Here's      "I'll write the design;
  good luck."                      why it matters and what done looks   you implement exactly
                                   like. Draft the design; let's        what I wrote."
                                   review the crash cases together
                                   Thursday. You present it at the
                                   design review."
```

### Pitching technical debt work

Leaders fund outcomes, not refactors. Translate debt into the currency the decision-maker
uses (`05` §9):

| Weak pitch | Strong pitch |
|---|---|
| "The billing module is a mess; we need two sprints to clean it up." | "Every pricing change takes ~9 days, 6 of them in the billing module, and caused 2 of Q2's 4 incidents. A 3-week refactor (plan attached) cuts pricing changes to ~3 days — paying for itself after ~4 pricing launches, and we have 7 planned next half." |

### Saying no

- **Make the trade-off explicit** instead of refusing: "We can add multi-currency to this
  launch if we move the launch 3 weeks, or ship without it and add it in November. Which
  matters more?"
- **Offer an alternative** that meets the underlying need.
- **Put it in writing** — a non-goal in the doc, a line in the status update — so the "no"
  survives the next meeting.

---

## 13 · Using this in interviews

### System design round

Structure the answer like a design doc, out loud:

| Design doc section | Interview step | What to say |
|---|---|---|
| Context, goals, non-goals | Requirements | "Functional requirements are…; I'll treat X as out of scope unless you'd like it." |
| Capacity (§4.4) | Estimation | "At 20k <abbr title="Queries Per Second - A common metric used to measure the rate of traffic passing through a particular server or system.">QPS</abbr> writes and 1 KB per record, that's ~1.7 TB/day…" |
| Detailed design (<abbr title="Application Programming Interface">API</abbr>, data model) | <abbr title="Application Programming Interface">API</abbr> and schema | "The core <abbr title="Application Programming Interface">API</abbr> is… The key access pattern is… so the primary key is…" |
| Overview diagram | High-level design | Draw the main path end to end before any deep dive |
| Hard parts | Deep dives | "The hardest part is the crash window between the charge and the key write…" |
| Alternatives | Trade-offs | "One alternative I considered was Redis for keys; I rejected it because…" |
| Cross-cutting + rollout | Reliability, security, evolution | "Failure modes…, how we'd monitor it…, how we'd roll it out safely…" |

### Behavioural round

- Have **one design-doc story** in your story bank (`GoogleBehavioral/04_story_bank_worksheet.md`,
  story types 1–3): the problem, the doc, the disagreement, the crux you resolved with data,
  the decision, the outcome in numbers, and what you'd do differently.
- **L5 language:** "I wrote", "I proposed", "I ran a benchmark on the crux question", "I
  aligned the storage team by…", "we measured…". Not "we kind of decided".
- Include a **reviewer story** too: a design you improved or stopped by reviewing someone
  else's doc well.

### Project deep dive

"What alternatives did you reject?", "What would you change?", "How did you roll it out?" —
answer straight from the doc's alternatives, risks, and rollout sections. Engineers who wrote
docs have crisp answers; engineers who didn't, reconstruct them live.

### Talk tracks worth having ready

- *On writing docs:* "I write a doc when a decision is hard to reverse or spans teams. I share
  a one-page sketch with likely objectors first, keep goals measurable, include 'do nothing' as
  an alternative, and make sure every milestone proves something."
- *On disagreement:* "I try to find the crux — usually one factual question — and settle it
  with a prototype or data, with a named decider and a trigger to revisit."
- *On reversibility:* "I move fast on two-way doors and slow down on data models and public
  APIs; where I can, I turn a one-way door into a two-way door with a flag or an adapter."

---

## 14 · Interview questions and model answers

**Q: When do you write a design doc?**
When work spans more than a couple of weeks or more than one team, when it's hard to reverse —
data models, public APIs, storage choices — when it changes SLOs, cost, or security posture, or
when people will disagree. For small or easily reversible changes, a PR description or an ADR is
enough, and sometimes a one-day prototype teaches more than a doc.

**Q: What's the most important section of a design doc?**
Goals and non-goals, because they determine whether any design is right; and alternatives
considered, because they show whether the author explored the space and they record why other
options lost. A doc with vague goals invites endless debate; a doc without real alternatives
invites reviewers to propose them all again.

**Q: Tell me about a time you disagreed with a senior engineer on a design.**
(Structure.) Situation and stakes in two sentences. How you aligned on criteria first. The crux
— a factual question — and the prototype or data that answered it. How you represented their
concern fairly and built it into the decision as a revisit trigger. The decision process and who
decided. The outcome in numbers, and what the relationship looked like afterwards.

**Q: How do you get buy-in from a team that doesn't report to you?**
Engage them before the doc exists, frame the proposal in terms of their goals, reduce their cost
of saying yes — contribute the code, draft the migration — use data rather than authority, and
give them real influence over the parts that affect them. Credit them publicly.

**Q: How do you review a design doc?**
Premise first: is it the right problem, are the goals measurable and right, is there a much
simpler option. Then the hard parts: failure modes, data model, reversibility, rollout and
rollback. Comments are specific and actionable, explain the concern, and are labelled blocking,
question, suggestion, or nit — and I say which sections I didn't review.

**Q: How do you decide how much rigour a decision needs?**
By reversibility and blast radius. Two-way doors — internal structure, flagged behaviour, tunable
parameters — get decided quickly and corrected with production data. One-way doors — public APIs,
data formats, storage engines, security boundaries — get a doc, a prototype for the crux, and
broader review. Where possible I make one-way doors reversible with adapters, flags, or
dual-writes.

**Q: A project you lead is going to miss its date. What do you do?**
Say so early, in writing, with the cause, the new estimate with a confidence range, and options:
cut scope (with what each cut costs), add a specific resource, or move the date. Recommend one.
Bad news delivered early with options is leadership; delivered late, it's a surprise.

**Q: What makes a good postmortem?**
Blameless analysis of the system rather than the person, a precise timeline, multiple
contributing causes including detection and response, honest "where we got lucky", and a small
number of owned, dated action items that prevent a class of incident rather than the exact
recurrence.

---

## 15 · Checklist

**Writing**
- [ ] I can list design doc sections and the reviewer question each answers.
- [ ] My goals are measurable; my non-goals pre-empt real scope expansion.
- [ ] My overview states the decision first and fits on one screen.
- [ ] My alternatives include "do nothing" and at least one genuinely different approach.
- [ ] Cross-cutting concerns contain decisions, not placeholders.
- [ ] Rollout includes a rollback; milestones each prove something.

**Planning**
- [ ] Work is ordered by risk; the crux is prototyped first.
- [ ] Estimates are ranges with confidence and named dependencies.
- [ ] Unglamorous work (migrations, dashboards, runbooks, rollout) is in the plan.

**Decisions**
- [ ] I can write an ADR with honest consequences.
- [ ] I can turn a disagreement into criteria, a crux, evidence, a named decider, and a revisit trigger.
- [ ] I classify decisions as one-way or two-way doors and match rigour to reversibility.

**Leadership**
- [ ] My review comments are specific, reasoned, and labelled.
- [ ] I can write a status update that leads with status, risks, and asks.
- [ ] I can pitch technical debt in terms of outcomes and cost.
- [ ] I have behavioural stories for writing a doc, resolving a disagreement, and reviewing someone else's design.
