# Ranking, Recommendation, and Experimentation

Two systems decide what a user sees: a ranking pipeline that chooses the items, and an experimentation platform that decides whether a change to that pipeline was an improvement. [23_ml_and_llm_systems.md](23_ml_and_llm_systems.md) covers the generic funnel, feature stores, ANN indexes and model serving. This block covers what Meta, Netflix and Google interviews probe next: where the latency and compute budget goes, what you must log, why offline and online metrics disagree, and how to run an experiment that does not lie.

> 🎯 Say the objective and the log before the model: "We rank by predicted watch time under integrity filters. We log every impression with position, score and model version, because without that log we can neither train without selection bias nor evaluate a new ranker offline. We ship only on a randomized experiment that passed a sample-ratio check."

## Part 1 — Ranking and recommendation as a system

### The cascade and its budget

Scoring every item with the best model costs corpus size × model cost per request, so a cascade spends little on many items and a lot on few. YouTube's paper ("Deep Neural Networks for YouTube Recommendations", Covington, Adams, Sargin, RecSys 2016) uses this shape: candidate generation narrows millions of videos to hundreds, then a richer model ranks those.

```arch
%% caption: Each stage sees fewer items and spends more per item, so total cost is set by how many candidates reach the heavy ranker.
grid 160x105
node corpus "Corpus" at 1.5,0 icon=db sub="10^8 items"
group ret "Candidate retrieval" color=teal icon=search
node R1 "Two-tower ANN" at 0,1 in ret icon=vector
node R2 "Graph 2-hop" at 1,1 in ret icon=graph
node R3 "Co-visitation" at 2,1 in ret icon=link
node R4 "Popular and fresh" at 3,1 in ret icon=news
node M "Merge, dedupe, filter" at 1.5,2 color=slate sub="10^4"
node L "Light ranker" at 1.5,3 color=blue sub="10^4 to 500"
node H "Heavy ranker" at 1.5,4 color=purple sub="500 to 50"
node B "Re-rank and blend" at 1.5,5 color=indigo sub="50 to 20"
node P "Page" at 0.5,6 shape=pill color=green
node LOG "Impression log" at 2.5,6 icon=logs
corpus -> R1
corpus -> R2
corpus -> R3
corpus -> R4
R1 -> M
R2 -> M
R3 -> M
R4 -> M
M -> L -> H -> B
B -> P
B ..> LOG : "shown items, positions, scores, features"
```

Assumptions (ours, not a real system's): 200M DAU × 10 ranked requests/day = 2×10^9/day ÷ 86,400 = 23k/s average, ×3 peak ≈ 70k/s, p99 budget 200 ms.

| Stage | Items in → out | Cost per item (assumed) | Wall clock | CPU per request |
|---|---|---|---|---|
| Retrieval, 4 sources in parallel | 10^8 → 10^4 | index and ANN lookups | 30 ms (slowest source) | 5 ms |
| Feature fetch | 500 items | batched multi-get | 15 ms | in stages |
| Light ranker, sharded 5 ways | 10^4 → 500 | 5 µs (small tree or MLP) | 10 ms + 5 ms overhead | 10^4 × 5 µs = 50 ms |
| Heavy ranker, batched | 500 → 50 | 200 µs (multi-task DNN) | 40 ms | 500 × 200 µs = 100 ms |
| Re-rank and blend | 50 → 20 | rules, diversity | 10 ms | 5 ms |

Wall clock is 30 + 15 + 15 + 40 + 10 = 110 ms of the 200 ms budget; the other 90 ms is network hops, content hydration and tail. CPU is 5 + 50 + 100 + 5 = 160 ms per request, so 70k × 0.16 s = 11,200 busy cores, about 22,000 at 50% utilisation. So: (1) the heavy ranker is 62% of compute and the candidate count entering it is the cost dial — each extra 100 candidates costs 70k × 100 × 200 µs = 1,400 cores, and doubling 500 to 1,000 lifts CPU to 260 ms per request (36,000 cores at 50%); (2) parallelism buys latency, not cost — sharding the light ranker 5 ways cuts its wall time from 50 to 10 ms but leaves its 50 ms of CPU; (3) under overload you shrink N per stage before you fail a request ([28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md)).

**Decision rule:** name each stage's job (retrieval buys recall, rankers buy precision, re-rank enforces policy), its in/out counts and its budget. If a stage has no distinct job, delete it.

### Retrieval sources and merging

| Source | How it works | Strong at | Weak at |
|---|---|---|---|
| Collaborative filtering, co-visitation | Precomputed "engaged with X, also engaged with Y" lists (item-to-item CF, Linden, Smith, York, IEEE Internet Computing 2003) | Cheap lookup, explainable ("because you watched") | New items with no co-engagement; popularity bias |
| Two-tower embeddings + ANN | User tower and item tower emit vectors; top-k by inner product from an ANN index over item vectors (Covington 2016; Yi et al., RecSys 2019, corrects sampling bias in training) | Personalisation over the whole corpus | No user×item cross features; item index must be refreshed for new items |
| Graph, 2-hop | Friends-of-friends, follows-of-follows, random walks (Pixie, Pinterest, WWW 2018) | People and social feeds, high precision | Dense-node explosion; needs a fast graph service ([30_social_graph_and_caching_at_scale.md](30_social_graph_and_caching_at_scale.md)) |
| Popularity and recency | Top items per region or topic in the last hours; a queue of new items | Cold start, fallback | Not personal |
| Subscriptions | Items from accounts the user chose | High intent | Little discovery |

Merge as a union by item id, tagged with source. Retriever scores are not comparable (cosine similarity against a co-visit count), so do not sort the union by them: give each source a quota, apply hard filters once (seen, blocked, ineligible, integrity), and let the rankers decide. Run sources in parallel with a per-source deadline; a source that misses it is dropped from that request and counted, not waited for. Log the source on every candidate and tune quotas by each source's share of the final slate, so you can tell which retriever earns its cost.

### Features and online/offline consistency

| Class | Example | Freshness | Computed by |
|---|---|---|---|
| Static and slow | Item category, user language, embeddings | Day | Batch, materialised to the online store |
| Real-time counters | Item CTR last hour, user clicks last 10 min | Seconds to minutes | Stream job with sliding windows ([21_batch_and_stream_processing.md](21_batch_and_stream_processing.md)) |
| Sequences | Last 50 items watched | Seconds | Event log or state store, read at request time |
| Cross and context | User×creator affinity, time of day, device | Request time | In the ranker; cannot be precomputed (users × items) |

Train and serve diverge through different code paths, different freshness, and leakage (a feature value from after the label event). Two defences. **Log at serve:** record the exact features the ranker saw and train on them (Google's "Rules of Machine Learning", rule 29), which removes skew by construction. It is expensive: 20 shown items × 300 features × 4 B = 24 KB per request × 2×10^9 requests/day = 48 TB/day raw, so log only shown items, sample requests, and quantise. **Point-in-time join:** rebuild each training row from versioned offline tables so a row at time t gets each feature as of t, never later. That stores far less but leaves skew wherever offline and streaming logic differ.

**Decision rule:** log-at-serve for volatile features (counters, sequences), point-in-time joins for slow ones, one feature definition executed by both paths.

### Training data: log what was shown

- **Log the impression, not just the click.** Per impression: request id, user, item, slot and position, model version, source retriever, scores, feature snapshot or its key, and a client-side viewability event. A click-only log has no negatives and no propensities. "Served" is not "seen": an item below the fold that never rendered is not a negative.
- **Delayed labels.** Watch time is known at session end, a purchase days later. Join impressions to outcomes with a waiting window: Facebook's ads paper ("Practical Lessons from Predicting Clicks on Ads at Facebook", He et al., ADKDD 2014) describes an online joiner whose window trades label completeness against freshness; Chapelle (KDD 2014) models the delay explicitly.
- **Negative downsampling needs recalibration.** If you keep a fraction w of negatives, correct predictions with p = p′ / (p′ + (1 − p′)/w) (same paper). A true 2% CTR with w = 0.1 trains to 17%; the correction returns 2.0%. Skip it and an ads auction multiplying bid × pCTR misprices by about 8×.
- **Position bias.** Top slots get clicks regardless of quality, so the model learns "position 1 is good". Feed position in training and fix it at serve time, use a shallow position tower (Zhao et al., RecSys 2019), or weight by inverse propensity (Joachims, Swaminathan, Schnabel, WSDM 2017).
- **Selection bias.** You see outcomes only for what the previous policy showed. Keep 1–2% exploration traffic with logged propensities and train or evaluate on it (Schnabel et al., ICML 2016).
- **Feedback loops.** Show X, X gets clicks, show more X (Sculley et al., NeurIPS 2015 name direct and hidden loops). Counter with exploration, an example-age feature, diversity constraints and long-term holdouts.

### Objectives, blending, and guardrails

CTR alone rewards clickbait; the 2016 YouTube paper trains a weighted logistic regression whose odds approximate expected watch time for that reason. In practice you predict several actions with a multi-task model (click, watch ≥ 30 s, like, share, hide, report; Zhao et al. 2019) and blend: `score = Σ wᵢ · pᵢ`, with negative weights on hide and report. The weights are product policy tuned by experiments along a Pareto frontier, not learned, and a constrained form ("maximise watch time with report rate below a threshold") is easier to defend. Session metrics miss retention, so check long-term effects with holdouts (Part 2) and surrogate metrics validated against them.

Integrity and quality filters are hard filters at merge and re-rank, not features the ranker may trade off: the policy team owns them and can change them without retraining. Diversity is a re-rank constraint (per-author and per-topic caps, maximal marginal relevance, Carbonell and Goldstein 1998); fairness of exposure (Singh and Joachims, KDD 2018) becomes reserved slots for new creators or sellers. Both cost short-term CTR, so justify them with a long-term holdout.

### Exploration, cold start, and freshness

- **ε-greedy** replaces a slot with a random item with probability ε (1–5%): simple, wasteful, and gives clean propensities.
- **Thompson sampling and UCB** sample each item's CTR from its posterior and rank by the sample, so items with little data get shown until the data settles (Chapelle and Li, NeurIPS 2011; LinUCB, Li et al., WWW 2010). Netflix's tech blog "Artwork Personalization at Netflix" (2017) describes contextual bandits choosing artwork per member, with logged exploration data for offline replay.
- **New items:** content embeddings into the same space, a reserved budget (say 5% of slots for items under 24 h old with an impression cap), and an example-age feature so the model does not prefer old items (Covington 2016). **New users:** popularity by locale and device, onboarding choices, then switch to the personalised retriever after a few events.
- **Freshness ladder:** real-time counters (seconds, no retrain) first; then hourly incremental updates of embeddings or top layers (FTRL online learning in McMahan et al., KDD 2013; ByteDance's Monolith paper, 2022, describes real-time parameter sync); then a daily full retrain. He et al. 2014 measured quality decaying as training data ages, so news, ads and short video need hours, movies do not.

### Serving: precompute, cache, fall back

Netflix's 2013 blog "System Architectures for Personalization and Recommendation" (Amatriain, Basilico) splits work into offline (batch), nearline (triggered by events, precomputed before the request) and online (at request time). Use that vocabulary. **Precompute** slates or candidate sets on a schedule when context barely matters (email, push, TV home rows, PYMK): millisecond serving, but stale and wasted on users who never return. **On-demand** ranking is needed when session context matters (feeds). The common hybrid caches *retrieval output* per user for a few minutes and ranks fresh each request; do not cache the final slate across requests, because seen-sets and context change. Batch the heavy ranker (block 23). The fallback ladder, triggered by deadline not just error: full pipeline → skip the heavy ranker (light-ranker order) → last good slate for this user, served stale while refreshing → per-locale popular list. Each rung is tested and has a metric.

### Offline metrics versus online metrics

| Metric | Measures | Blind spot |
|---|---|---|
| AUC | Chance a clicked item outscores an unclicked one, whole list | Ignores calibration and the top of the list; gains in a tail nobody sees still count |
| NDCG@k, recall@k | Top-k quality with position discount (recall@k for retrieval) | Labels exist only for items the old policy showed |
| Log loss, calibration by bucket | Whether scores are probabilities | Matters when scores are combined or priced (eCPM = bid × pCTR, McMahan 2013) |
| Online: CTR, watch time, retention, hides | Real outcomes under the new policy | Slow, noisy, and costs real users |

They disagree because: the new ranker's best picks were mostly never shown, so offline has no labels to reward them; position bias inflates the old order; AUC is not the launch objective; latency, diversity and slot interactions are system effects; stale or leaky features flatter offline numbers; and novelty. Mitigate with counterfactual evaluation over logged propensities (Li et al., WSDM 2011) and with interleaving, which mixes two rankers' results in one list and needs far less traffic than a split test (Chapelle et al., ACM TOIS 2012; Netflix's 2017 blog on interleaving describes using it before full A/B tests).

**Decision rule:** offline metrics gate (reject regressions, check calibration); only a randomized online experiment decides a launch.

### How it shows up in feed, video, ads, and PYMK

| Design | Retrieval | Objective | Serving | Signature trap |
|---|---|---|---|---|
| Feed ([007](../solutions/007_news_feed_solution.md), [032](../solutions/032_ranked_home_feed_solution.md)) | Follow graph, friends' posts, interest ANN | Blend of engagement predictions minus negative feedback, integrity filters | On-demand rank over cached candidates | Viral feedback loop; celebrity posts merged from pull tier |
| Video | Two-tower ANN, co-watch, continue watching | Watch time and retention, not CTR (Netflix's 2015 paper by Gomez-Uribe and Hunt describes a homepage of rows, each from its own algorithm, ordered by a page-generation algorithm) | Nearline rows plus online rank | Clickbait; new-title cold start; artwork choice |
| Ads | Targeting filter + ANN | eCPM = bid × pCTR × pCVR, needs calibrated probabilities | On-demand, strict latency, auction | Miscalibration, delayed conversions, budget pacing |
| PYMK | 2-hop graph, contact import | Probability both sides accept (reciprocal) | Precompute daily, re-rank online | Rich-get-richer degree skew, privacy, blocked users |

## Part 2 — Experimentation platforms

### Unit of randomization and deterministic bucketing

Randomize at the unit where outcomes are independent and treatment must stay consistent. User id is the default; a device or cookie id for logged-out traffic (one person on two devices sees both arms); a session or request only for changes with no memory, analysed with clustered errors; a cluster or geography when users interact. **The analysis unit must equal the randomization unit**, or use the delta method or clustered errors; a per-page t-test on user-randomized data understates variance.

Assign with `bucket = hash(salt ‖ unit_id) mod 10,000`. The experiment owns a range of buckets; ramping only *adds* buckets, so no user flips. Give every layer and experiment its own salt, otherwise the same 5% of users land in every experiment's treatment arm and effects compound. Specify the hash (MurmurHash3, or a SHA-256 prefix): Python's built-in `hash()` is randomised per process. A deterministic function needs no assignment store, gives the same answer on every server, and can be replayed in analysis. The cost is that changing assignment means changing the salt, which is exactly what you do on a re-run, to avoid carryover from the previous run.

### Layers and assignment paths

Tang, Agarwal, O'Brien and Meyer ("Overlapping Experiment Infrastructure: More, Better, Faster Experimentation", Google, KDD 2010) describe how to run many experiments on the same traffic: parameters are grouped into layers, a request falls into at most one experiment per layer, and each layer hashes independently so the layers are orthogonal. Experiments that touch the same parameter share a layer and get disjoint bucket ranges; independent layers average out interactions instead of detecting them, so declare interacting experiments as conflicts.

```arch
%% caption: One unit id is hashed independently per layer, giving each layer an unbiased split, and exposure is logged where the parameter is actually used.
grid 160x105
node U "user_id" at 0.5,0 shape=pill color=slate
group lr "Ranking layer" color=blue icon=layers
node H1 "hash salt_rank + id" at 0,1 in lr color=blue sub="mod 10000"
node L1 "Layer ranking" at 0,2 in lr color=blue sub="exp A 0-499, exp B 500-999, rest control"
group lu "UI layer" color=purple icon=layers
node H2 "hash salt_ui + id" at 1,1 in lu color=purple sub="mod 10000"
node L2 "Layer UI" at 1,2 in lu color=purple sub="exp C 0-1999, rest control"
node P "Resolved parameters" at 0.5,3 color=slate sub="ranker v7, page size 20"
node S "Service applies parameters" at 0.5,4 icon=service
node X "Exposure log" at 0.5,5 icon=logs
node ST "Stream job" at 0,6 icon=stream sub="guardrails, SRM"
node BT "Batch job" at 1,6 icon=cron sub="CUPED, full stats"
U -> H1
U -> H2
H1 -> L1
H2 -> L2
L1 -> P
L2 -> P
P -> S -> X
X -> ST
X -> BT
```

| | Central assignment service | SDK-local evaluation |
|---|---|---|
| Latency | One network hop per decision, plus its tail | In-process, microseconds |
| Consistency | One source of truth, instant config change, can hold state | Bounded staleness, two servers may briefly disagree |
| Failure | Outage blocks decisions unless clients keep defaults | Keeps working from the last snapshot |
| Use for | Mobile and web clients, targeting on server-side attributes: fetch all assignments once per session | Server-side hot paths, ranking |

The flag platform in [019_feature_flags_solution.md](../solutions/019_feature_flags_solution.md) is the same mechanism (local snapshot, deterministic hash, per-flag safe default); the experimentation platform adds exposure logging, layers and analysis ([037_experimentation_platform_solution.md](../solutions/037_experimentation_platform_solution.md)). Assignment is a pure function of (config version, unit id), so skew is bounded and detectable if you log the config version with each exposure. **Decision rule:** prefer stickiness over freshness. Delay a config change before you flip a user mid-experiment.

### Exposure logging and metric pipelines

Log exposure where the user could first be affected (the parameter is read, the UI renders), not at assignment, and log it for control too, so both arms are counted the same way. Fields: unit, experiment, variant, layer, config version, timestamp, event id for dedupe. Analysing only exposed users matters: if 10% of assigned users ever reach the changed page, the diluted effect is 10× smaller and needs 1/0.1² = 100× the sample.

| | Stream (minutes) | Batch (daily) |
|---|---|---|
| Purpose | Safety: error, latency, crash rate, SRM, kill switch, ramp gating | Decision-grade: CUPED, ratio metrics, segments, dedupe |
| Correctness | Approximate; may double count or miss late events | Exact, reproducible, re-runnable with late data |

Compile one metric definition to both paths (the feature-store idea again); see [013_metrics_platform_solution.md](../solutions/013_metrics_platform_solution.md) and [27 ad click aggregation](../solutions/027_ad_click_aggregation_solution.md) for the counting side.

### The statistics you must explain

- **Sample-ratio mismatch (SRM).** Planned 50/50, observed 497,000 vs 503,000 of 1,000,000: χ² = 2 × 3,000²/500,000 = 36, p ≈ 2×10^-9. A 0.6% skew looks trivial and is impossible by chance: something drops users unevenly (a crash, redirect, bot filter, logging bug in one arm). Check it before reading any metric (alarm at p < 0.001); an SRM invalidates the readout (Kohavi, Tang, Xu, *Trustworthy Online Controlled Experiments*, 2020).
- **Power and MDE.** Per arm, n = 2 (z₁₋α/₂ + z₁₋β)² σ² / δ². With α = 0.05 two-sided (1.96) and 80% power (0.84), (1.96 + 0.84)² = 7.85. Baseline conversion 5% gives σ² = 0.05 × 0.95 = 0.0475; a minimum detectable effect of 0.1 pp (2% relative) gives δ = 0.001, so n = 2 × 7.85 × 0.0475 / 0.001² ≈ 746k, about 750k per arm (an exact two-proportion calculation gives 753k). n scales with 1/δ², so a 1% relative MDE needs 3.0M per arm. So a surface with 20M weekly users at 10% per arm (2M each) detects a 2% relative lift in a week but not 1%: add allocation, run longer, or reduce variance. Still run whole weeks, for day-of-week effects.
- **CUPED** (Deng, Xu, Kohavi, Walker, WSDM 2013). Adjust Y′ = Y − θ(X − X̄) with θ = cov(X, Y)/var(X), X the same metric measured before the experiment. Variance shrinks by (1 − ρ²): ρ = 0.5 gives ×0.75, so 746k → 560k per arm at no extra traffic; ρ = 0.8 gives ×0.36. X must come from before exposure.
- **Peeking.** A 5% error rate assumes one look. Simulated (python, stop at first |z| > 1.96): 10 looks give 19% false positives, 14 daily looks 23%. Use a fixed horizon, or a method built for monitoring: group-sequential with alpha spending (Lan and DeMets 1983) or always-valid mSPRT p-values (Johari et al., 2017). The price is somewhat wider intervals.
- **Multiple comparisons.** Twenty metrics at α = 0.05 give 1 − 0.95²⁰ = 64% chance that at least one looks significant under no effect. Fix one primary metric in advance, use Bonferroni (0.05/20 = 0.0025) or Benjamini-Hochberg for the rest, and treat post-hoc segments as hypotheses, not results.
- **Ratio metrics.** CTR with users as the unit needs the delta method (Deng, Knoblich, Lu, KDD 2018) or a user-level bootstrap.
- **Novelty and primacy.** A new UI draws curiosity clicks that decay, or needs time to learn. Plot effect by days since first exposure, run at least 1–2 weeks, and do not ship on a shrinking week-one lift.
- **Interference.** In social products and marketplaces a treated user changes what control users see or compete for, biasing the estimate. Cluster randomization (Ugander et al., KDD 2013) randomizes connected clusters, or geographies and time slices in marketplaces. It costs a design effect 1 + (m − 1)ρ: clusters of m = 50 users with intra-cluster correlation ρ = 0.05 give 3.45×, turning 750k into 2.6M per arm. Pay it when the spillover is the thing you care about (messaging, invites).
- **Holdouts and long-term effects.** Keep 1–5% of users out of a class of launches for months to measure cumulative and learning effects and to catch short-term wins that cost retention. The price is that those users get the older product.
- **Guardrail metrics.** Latency, crash and error rate, hide and report rate, revenue, and long-term proxies, each with a preset threshold. A launch needs the primary win and no guardrail breach.

### Ramp-up and how experiments lie

Ramp: 1% canary for bugs and performance (gate on stream guardrails and SRM, hours) → 5% (a day, verify exposure logging) → 20–50% for the measured run at constant allocation, 1–2 full weeks → 100% with a 1–5% holdout retained. Allocation only grows so no user flips; analyse a constant-allocation window only (pooling ramp stages invites Simpson's paradox); roll back automatically on a guardrail breach.

| Symptom | Cause | Defence |
|---|---|---|
| Metric moves and SRM fails | Users dropped unevenly by one arm | SRM gate before any readout |
| Effect fades after week one | Novelty | Effect by days since first exposure |
| Lift is tiny across all assigned users | Dilution by never-exposed users | Exposure-triggered analysis |
| Confidence intervals too narrow | Analysis unit ≠ randomization unit | Delta method or clustered errors |
| "Significant" on day 3 | Peeking | Fixed horizon or sequential test |
| One of 20 metrics significant | Multiple comparisons | Preregistered primary metric |
| Arms instrumented differently | New UI fires different events | A/A tests, log-parity checks |
| Control improves too | Interference; a shared model trained on both arms' logs | Per-arm training data, cluster randomization |
| Odd results after a re-run | Carryover from the same buckets | New salt per run |

Run A/A tests routinely: about 5% should flag at α = 0.05 and none should fail SRM. Twyman's law applies: an interesting result is usually a bug until proven otherwise.

## Interview angles

- **"Walk me through the ranking pipeline with numbers."** Stage counts and budgets that add up (110 ms wall, 160 ms CPU), the heavy-ranker candidate count as the cost dial, parallel retrievers with deadlines, and a fallback ladder.
- **"Offline AUC is up but the A/B is flat."** Selection and position bias, AUC is not the objective, calibration, system effects; propose counterfactual evaluation and interleaving; the experiment decides.
- **"You log clicks. What is missing?"** Impressions with positions and propensities, viewability, model version, features; without them there are no negatives and no bias correction.
- **"Cold-start item or user?"** Content embeddings, exploration budget with a cap, example age, popularity fallback, switch to personal signals after a few events.
- **"Users are drifting to clickbait."** Objective mismatch: predict watch time or satisfaction, negative weights on hide and report, integrity filters as hard filters, long-term holdout.
- **"Design assignment so a user never changes variant."** Salted hash to buckets, monotonic ramp, SDK-local evaluation, config version in the exposure log.
- **"Day 3 shows +2%, p = 0.03. Ship?"** No: peeking, novelty, SRM, multiple metrics. Fixed horizon or sequential test, whole weeks.
- **"How do you A/B test on a social network?"** Interference; cluster randomization and its design effect, or a geo test; say what you give up.

## Related building blocks

- [23_ml_and_llm_systems.md](23_ml_and_llm_systems.md)
- [20_specialized_data_structures.md](20_specialized_data_structures.md)
- [21_batch_and_stream_processing.md](21_batch_and_stream_processing.md)
- [28_overload_control_and_graceful_degradation.md](28_overload_control_and_graceful_degradation.md)
- [30_social_graph_and_caching_at_scale.md](30_social_graph_and_caching_at_scale.md)
- [07_caching.md](07_caching.md)
- [32_industry_papers_and_case_studies.md](32_industry_papers_and_case_studies.md)
