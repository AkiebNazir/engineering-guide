# Company Interview Guide: Google, Meta, Netflix, Amazon

Every top-company design round tests the same skills: scope a problem, size it, choose and defend trade-offs, go deep where it is hard, and show that you know how it fails. What changes is the **format**, **who steers**, **what flavor of problem you get**, and **which depth areas get probed**. This guide maps those differences onto this module.

> ⚠️ Everything here about a company's process is *commonly reported* — from candidate write-ups, public interview guides, and the companies' own published engineering material. It is not an internal rubric, formats change by team, level and year, and nobody outside a hiring committee sees its scoring. **Confirm with your recruiter:** the round length, whether design is combined with anything else, the level you are being evaluated at, and the drawing tool. Then lean on the principles below, which hold in any format.

## Principles that hold in every format

1. Say your plan in the first 30 seconds, sized to the time you actually have.
2. Ask only the requirement questions that change the design; write the scope down and confirm it.
3. Compute only the numbers that force a decision, and say the decision.
4. Commit, in the four-part sentence: *choice → what it gives → what it costs → why the cost is acceptable here.*
5. Pick the one or two genuinely hard problems and go deep on them unprompted.
6. Say how each box fails before you are asked.
7. Treat an interviewer's hint as a new constraint to explore, never as an attack.

The base method is in the [L5 playbook](00_google_l5_playbook.md); everything below is a lens on it.

---

## At a glance

| | Google | Meta | Netflix | Amazon |
|---|---|---|---|---|
| Commonly reported round | ~45 min, one interviewer, open-ended prompt | ~45 min; product-flavored and/or infrastructure-flavored | Longer, conversational, team-specific; often probes systems you built | ~60 min, with leadership-principle questions taking part of the time |
| Effective design window | ~40 min | ~35 min | 45–60 min, fluid | ~35–40 min |
| Who drives | You; the interviewer injects constraints | You, at a brisk pace; interviewer steers toward depth | Shared, like a peer design review | You, with behavioral probes woven in |
| Commonly reported rewards | Quantified reasoning, depth on scale, tail latency, consistency | Product sense, pragmatism, feed/graph/messaging fluency, ranking | Operating at scale, resilience, judgment, ownership | Customer-first scoping, operational excellence, cost, stories |

### Adapting the timeline (minutes per phase)

Start from the [45-minute timeline](00_google_l5_playbook.md) and compress. These are planning assumptions, not company rules.

| Phase | Google (45) | Meta (35) | Netflix (50, fluid) | Amazon (37) |
|---|---|---|---|---|
| Requirements and scope | 5 | 4 | 4 | 5, customer first |
| Estimates + <abbr title="Application Programming Interface">API</abbr> | 5 | 4 | 3 | 4 |
| Data model | 5 | 4 | 3 | 4 |
| Baseline, one write, one read | 10 | 6 | 8 | 7 |
| Deep dives (two) | 13 | 13 | 20 | 12 |
| Failure, operations, evolution | 7 | 4 | 12 | 5 |

Give extra time to deep dives and operations, not to more boxes. If time is short, keep only the two numbers that decide something and say so aloud.

---

## The level ladder: what changes per level

| Company | Level | What the design round is commonly looking for |
|---|---|---|
| Google | L4 | A sound component when the problem is scoped for you. Some loops give L4 a lighter design round. |
| | L5 | Owns the system end to end and drives; two unprompted deep dives; failure raised early. |
| | L6 | Reframes the problem, phases the design (launch, 10×, multi-region), quantifies cost. See [Going from L5 to L6](00_google_l5_playbook.md). |
| Meta | E4 | Solid design with some guidance. Some E4 loops are coding-heavy with a lighter design round. |
| | E5 | Independent end to end: product judgment, scale, caching, ranking, a clean <abbr title="Application Programming Interface">API</abbr>. |
| | E6 | Cross-team scope, ambiguity handled, org-level trade-offs. |
| Netflix | Senior | Independent judgment, real operating experience, resilience by default. |
| | Staff | Sets direction across teams, argues what *not* to build. |
| Amazon | SDE II | A well-built service; some loops add object-oriented design; operational hygiene. |
| | Senior | Designs across services, owns operational outcomes, drives scope. |
| | Principal | Multi-team influence, long-horizon direction, cost and mechanisms. |

Confirm the level first: a design that is excellent for L4 or SDE II is too narrow for L6 or Principal.

---

## Google

**Commonly reported.** A 45-minute open-ended round whose notes a committee reads later, so *saying* your reasoning matters. The interviewer mostly reacts; you propose.

**Problem families → this module.** Storage and lookup: 001, 003, 023, 018, 022. Search and text: 009, 025. Collaboration and storage products: 015, 024, 035. Video and maps: 016, 026, 034. Counting and streams: 027, 028, 029, 031. Coordination: 040.

**Depth areas commonly probed.**
- **Scale arithmetic** that turns into decisions ([18](building_blocks/18_back_of_envelope_estimation.md)).
- **Tail latency**: fan-out, hedged requests, deadlines. Read Dean and Barroso, "The Tail at Scale" (CACM, 2013), summarized in [24](building_blocks/24_google_papers.md) and [28](building_blocks/28_overload_control_and_graceful_degradation.md).
- **Consistency**: which flows need transactions, which tolerate staleness ([10](building_blocks/10_distributed_systems_theory.md), [19](building_blocks/19_consensus_and_coordination.md)).
- **The papers**: Bigtable, Spanner, Chubby, GFS, MapReduce. Name the *property*, not the product.

**Red flags.** No numbers. A "database" with no consistency story. The interviewer steering every step. Multi-region as decoration rather than as a stated RPO.

## Meta

**Commonly reported.** Loops often distinguish a *product-flavored* design ("design a news feed", "design Messenger") from an *infrastructure-flavored* one. The window is short and the pace brisk, so an early, crisp <abbr title="Application Programming Interface">API</abbr> and data model help.

**Problem families → this module.** Feed and graph: 007, 032, 039. Messaging and media: 006, 005, 033, 004. Discovery: 009, 026, 028. Caching and experimentation: 018, 037. Ads counting: 027.

**Depth areas commonly probed.**
- **Read-heavy scale**: cache tiers, invalidation, hot keys. Sources: "Scaling Memcache at Facebook" (NSDI 2013) and "TAO" (USENIX ATC 2013), both in [30](building_blocks/30_social_graph_and_caching_at_scale.md) and [32](building_blocks/32_industry_papers_and_case_studies.md).
- **Ranking**: candidate retrieval, a cascade of rankers, exploration ([31](building_blocks/31_ranking_recommendation_and_experimentation.md)).
- **Product judgment and pragmatism**: what the user sees, the simplest thing that ships, how you would iterate and measure.

**Red flags.** Ten minutes of requirements. Fan-out with no celebrity story. A feed with no ranking or privacy check. Technologies named without the access pattern that justifies them.

## Netflix

**Commonly reported.** Senior-weighted hiring, team-specific loops, and conversations that read like a design review. Expect questions about systems *you* ran: what broke, what you changed. Netflix's public culture document stresses independent judgment and ownership ("context, not control").

**Problem families → this module.** Streaming and delivery: 016, 036, 033. Personalization and experiments: 032, 037. Platform and operations: 019, 012, 013, 021. Data and events: 031, 027. Caching: 018.

**Depth areas commonly probed.**
- **Operating at scale**: overload, degradation, deploy safety ([28](building_blocks/28_overload_control_and_graceful_degradation.md), [12](building_blocks/12_application_resilience_patterns.md)).
- **Resilience and chaos**: designs that assume dependencies fail; Netflix has published on failure injection (Chaos Monkey, the Simian Army) since about 2011.
- **Streaming and CDN**: adaptive bitrate, manifests, Open Connect appliances placed inside ISP networks ([29](building_blocks/29_cdn_and_streaming_media.md)).
- **Data pipelines and experimentation**: [21](building_blocks/21_batch_and_stream_processing.md), [31](building_blocks/31_ranking_recommendation_and_experimentation.md).
- **Judgment**: the cost of complexity; what you would not build.

**Red flags.** Assuming healthy dependencies. "Someone else operates it." Microservices as a reflex. No opinion on what to cut.

## Amazon

**Commonly reported.** Loops of several roughly hour-long interviews, each mixing behavioral questions tied to Amazon's published Leadership Principles with technical content; one interviewer is commonly described as a "Bar Raiser". Design depth grows with level.

**Problem families → this module.** Commerce and money: 008, 010, 017. Messaging and workflow: 004, 012, 031, 041. Platform: 002, 021. Storage and data: 023, 035, 018.

**Depth areas commonly probed.**
- **Operational excellence**: alarms, dashboards, runbooks, deployment safety, on-call ([15](building_blocks/15_observability_and_reliability.md)).
- **Cost**: cost per request, per GB, per customer; where you would spend less.
- **Failure isolation**: retries with backoff and jitter, load shedding, cell-style blast-radius limits, availability zones. The public Amazon Builders' Library covers these ([28](building_blocks/28_overload_control_and_graceful_degradation.md), [32](building_blocks/32_industry_papers_and_case_studies.md)).
- **Working backwards**: start from the customer's promise, then requirements.
- **Stories woven into design**: when a decision matches something you really did, give two sentences (situation, action, result) and return to the board. Keep 6–8 real stories, each mapped to two or three principles. Never invent one.

**Red flags.** No operations or cost story. Stories with no "I". A design that starts from technology, not the customer. Ignoring the behavioral half of the loop.

---

## Ordered paths and hour budgets

Planning assumption: one problem is a 45-minute timed attempt plus about 30 minutes comparing decisions, so 1.25 h each; "mocks and redo" is three timed mocks plus three constraint-change redos, about 8 h. Totals are arithmetic on those assumptions, not measurements. Read the blocks ("B") first, then attempt problems in the order shown; the [catalog](02_problem_catalog.md) links every question.

| Company | Blocks (~h) | Problems in order (count × 1.25 h) | Mocks and redo | Total |
|---|---|---|---|---|
| Google | [playbook](00_google_l5_playbook.md), B10, 18, 19, 24, 25, 27, 28 (~12) | 007, 018, 023, 009, 025, 026, 028, 027, 024, 015, 016, 035, 034, 040 (14 × 1.25 = 17.5) | 8 | about 38 h |
| Meta | B07, 09, 22, 25, 29, 30, 31 (~11) | 007, 039, 032, 006, 005, 033, 004, 009, 026, 028, 018, 037, 027 (13 × 1.25 = 16.25) | 8 | about 35 h |
| Netflix | B12, 15, 21, 27, 28, 29, 31, 32 (~12) | 016, 036, 033, 032, 037, 019, 031, 013, 021, 012, 018, 027 (12 × 1.25 = 15) | 8 | about 35 h; also prep two stories of systems you ran, one a failure |
| Amazon | B11, 12, 15, 27, 28, 32 (~10) | 008, 010, 017, 004, 002, 021, 012, 023, 035, 031, 041, 018 (12 × 1.25 = 15) | 8 + 4 for the story bank | about 37 h |

> 💡 The four lists overlap heavily. Their union is 32 distinct problems, so preparing for all four is not four times the work. Do the shared core first (007, 018, 023, 028, 031), then your target company's remainder. For faster passes use [practice prompts](03_practice_prompts.md), [blueprints](05_architecture_blueprints.md) and [spoken walkthroughs](06_spoken_walkthroughs.md).

---

## Universal signals

| Signal | Google | Meta | Netflix | Amazon |
|---|---|---|---|---|
| Scoping | You propose scope and confirm it | You tie scope to user behavior fast | You ask what the real constraint is | You start from the customer's promise |
| Numbers | Few, decisive, rounded | Enough to size caches and fan-out | Enough to reason about cost and headroom | Cost per request as well as QPS |
| Trade-offs | Committed, four-part | Committed, pragmatic, shippable first | Committed, with the operating cost named | Committed, with cost and blast radius |
| Depth | Scale, tail, consistency | Ranking, caches, graph | Failure, streaming, experiments | Operations, isolation, idempotency |
| Failure | Raised unprompted, with an RPO | Degrade the product, not the page | Assumed, injected, tested | Alarms, rollback, runbook |
| Communication | Drive; check in at transitions | Move quickly, stay concrete | Converse; disagree with reasons | Own it with "I"; tie to a principle |


---

## One design, four lenses: the news feed

Shared core, from [007](solutions/007_news_feed_solution.md): a per-user precomputed feed store, hybrid fan-out (push for typical authors, pull for very high-follower authors), cursor pagination. Assumption for this exercise: 300M daily users open the feed 10 times a day, so 300M × 10 ÷ 86,400 ≈ 35K reads per second on average and about 100K at a 3× peak. **So the read path must be precomputed and cached.** Which problem you then go deep on is the lens.

**Google lens: scale, tail, consistency.**
- Deep dive 1, tail latency: a read merges the precomputed list with pulled celebrity posts across shards, so p99 is set by the slowest shard. Use per-shard deadlines and a hedged request after roughly the p95 latency, and merge whatever arrived (Dean and Barroso, 2013).
- Deep dive 2, consistency: read-your-writes for the author by merging their own outbox, eventual elsewhere, asynchronous cross-region replication with an RPO of seconds.
- Say: "I'll fan out asynchronously. Writes stay fast, and followers see a post within seconds instead of instantly, which is fine for a feed and would not be for a ledger."

**Meta lens: product, graph, ranking.**
- Open with the product: what the feed optimizes and what a bad feed looks like. Use session-stable cursors so the list does not reshuffle mid-scroll.
- The graph is the source of truth (objects and associations, as in the TAO paper) behind cache tiers; privacy is checked at read time. Deep dive: retrieval of a few thousand candidates, a light ranker, a heavy ranker, then diversity and integrity re-ranking ([032](solutions/032_ranked_home_feed_solution.md), [039](solutions/039_social_graph_service_solution.md)).
- Say: "I'd ship reverse-chronological with a light ranker first, then measure and iterate. We give up ranking quality on day one and gain a system we can reason about and A/B against, which is the right trade for a first launch."

**Netflix lens: operate, degrade, experiment.**
- Reframe the feed as personalized rows: expensive ranking that will sometimes be slow or down. Three tiers: precomputed results, online re-rank, and a static popular fallback ([28](building_blocks/28_overload_control_and_graceful_degradation.md)). Netflix's 2012 "Beyond the 5 stars" posts describe offline, nearline and online computation.
- Prove the fallback by failing the ranker on purpose. Ranking changes ship behind A/B tests with guardrail metrics ([037](solutions/037_experimentation_platform_solution.md)).
- Say: "When ranking is slow I serve the last good page. We give up freshness and keep latency constant, which is right because a slightly stale row is invisible and a blank page is not."

**Amazon lens: customer, cost, operations.**
- Work backwards: the customer's promise is a feed that loads fast and is never empty. Alarms on p99 and on feed age, deployment one cell at a time with automatic rollback, and a runbook for a stuck fan-out queue.
- Cost: fan-out cost per post is followers × write cost, so skip fan-out for users inactive for many days. If it is true for you, add a two-sentence story of a cost cut or an outage you fixed.
- Say: "I'll skip fan-out for inactive users. We avoid write work nobody will read and pay a slower first load on return, which is acceptable because returns are rare."

> 🎯 Same core, four emphases. Do not give all four talks at once: pick the lens the interviewer signals and give the others one sentence each.
