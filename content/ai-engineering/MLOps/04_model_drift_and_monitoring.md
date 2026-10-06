# Monitoring and Model Drift

You deploy a model with excellent offline metrics. Six months later revenue is down 20%,
and the cause turns out to be the model: it has been making worse and worse predictions
the whole time, while every service dashboard stayed green. This chapter explains why
models degrade (the kinds of **drift**, and the more common pipeline breakages that look
like drift), what to monitor at each layer, which statistical tests to use and where they
mislead, how to monitor when labels arrive weeks late, and what to do when an alert fires.

## Foundations — Why does a model that worked stop working?

### A model is a snapshot of the past

A trained model encodes the patterns in its training data: which inputs usually went with
which outcomes. It keeps applying those patterns forever. When the world it is applied to
stops looking like that training data, its predictions get worse, but it still returns
well-formed answers with `200 OK`. Nothing crashes. That is why ordinary monitoring (CPU,
memory, error rate, latency) is necessary but not sufficient for ML systems.

An everyday example: a food-delivery app predicts delivery times from distance, time of
day and restaurant load. It was trained on a year of data. Then:

- the app launches in a new city with longer distances (the **inputs** changed);
- a rainy week makes every delivery slower for the same distance (the **relationship**
  between inputs and outcome changed);
- the restaurant team renames `load` values from `LOW/MED/HIGH` to `1/2/3` (the
  **pipeline** changed, and nothing about the world did).

All three show up as "the ETA model got worse", and each needs a different fix.

### What there is to watch

The table runs from the fastest, least conclusive signal (top) to the slowest, most meaningful one (bottom).

| Layer | Question | Available | Example signal |
|---|---|---|---|
| **Service health** | Is it up and fast? | Immediately | p99 latency, error rate, GPU utilisation |
| **Data quality** | Are inputs well-formed? | Immediately | Null rate of `distance_km` jumped from 0.1% to 30% |
| **Input drift** | Do inputs look like training data? | Minutes to hours | PSI of `distance_km` = 0.4 |
| **Prediction drift** | Do outputs look like before? | Minutes to hours | Mean predicted ETA up 25% |
| **Model quality** | Are predictions right? | When labels arrive (minutes to months) | MAE of ETA vs actual delivery time |
| **Business KPIs** | Is the product better? | Days | Late-delivery complaints, refunds |

The lower layers are fast but only suggest trouble; the upper layers are the truth but
arrive late. Good monitoring uses both.

### Vocabulary

| Term | Meaning |
|---|---|
| **Reference window** | The data you compare against: the training set, or a recent healthy production period |
| **Current window** | The live data being checked: the last hour, day or week |
| **Covariate (data) drift** | The input distribution P(X) changed |
| **Label (prior) shift** | The outcome distribution P(Y) changed |
| **Concept drift** | The relationship P(Y given X) changed: same inputs, different right answer |
| **Ground truth / labels** | The actual outcome, often known only later |
| **Label delay (maturity)** | How long until the label is final: seconds for a click, months for a chargeback |

## 1. Kinds of drift, and the things that only look like drift

| Kind | What changed | Example | Does retraining fix it? |
|---|---|---|---|
| **Covariate (data) drift** | P(X): who or what the model sees | Marketing targets users aged 50–65; the model was trained mostly on 18–35-year-olds | Often, once enough labelled data from the new population exists |
| **Label (prior) shift** | P(Y): how common each outcome is | Fraud rate rises from 0.1% to 0.4% during an attack | Recalibrate thresholds; retrain |
| **Concept drift** | P(Y given X): what inputs mean | In March 2020, grocery demand models saw normal prices and seasons but panic buying, so the same inputs meant much higher demand for toilet paper | Only with data from the new regime; may need new features |
| **Upstream data change** | Nothing in the world; the pipeline changed | `status` values change from `Active` to `ACTIVE`; a one-hot encoder with `handle_unknown="ignore"` maps the new value to all zeros, silently | No. Fix the pipeline; retraining would learn the bug |
| **Training–serving skew** | Features computed differently online | Serving counts clicks in local time, training in UTC | No. Fix the feature definition (chapter 02) |
| **Feedback loop** | The model's own decisions change its future data | A recommender only gets labels for items it showed | Needs exploration traffic, not just retraining (chapter 06) |

Concept drift can be **sudden** (a policy change, a pandemic), **gradual** (tastes shift
over months), **incremental**, or **recurring** (holidays, weekends, seasons). Recurring
patterns are not drift at all if the training data covered them: compare against the same
period last year, or include seasonal features.

**Precision note.** In practice, most "drift" alerts in production turn out to be
**pipeline breakages**, not the world changing: a column renamed, a unit changed from
seconds to milliseconds, a join that started producing nulls, a logging bug. Always rule
those out before retraining, because retraining on broken data makes it worse.

## 2. The monitoring pipeline

The model server logs every prediction (or a sample) with the request ID, model version,
feature values and output. A monitoring job aggregates those logs per window, compares
them with a reference, and later joins labels to compute real quality metrics.

```arch
%% caption: Predictions are logged with their features; drift checks run on the log right away, quality checks run again once labels arrive and are joined by request ID.
grid 150x110
node serve "Model server" at 0,0 icon=model sub="logs predictions"
node plog "Prediction log" at 1,0 icon=logs sub="id, version, features"
node ref "Reference stats" at 0,1 icon=archive sub="training window"
node drift "Drift job" at 1,1 icon=sigma sub="hourly: PSI, nulls"
node join "Label join" at 2,1 icon=link sub="by request id"
node labels "Label source" at 3,1 icon=check sub="clicks, chargebacks"
node dash "Dashboards + alerts" at 1,2 icon=alert sub="Grafana, pager"
node retrain "Retrain pipeline" at 2,2 icon=workflow sub="after triage"
serve -> plog
plog -> drift
ref -> drift
plog -> join
labels -> join
drift -> dash
join -> dash : "quality"
dash ..> retrain
```

What to log per prediction: request ID, timestamp, model name and version, the feature
vector (or a sampled subset for large rankers), the output (score, class, ranking),
whether any fallback or default was used, and experiment assignment. Without the request
ID you cannot join labels; without the model version you cannot tell a regression from a
rollout.

## 3. Statistical tests for drift

Pick the test by feature type, and alert on the **size** of the change, not only on its
statistical significance.

| Measure | For | Reads as | Notes |
|---|---|---|---|
| **PSI** (Population Stability Index) | Numeric (binned) or categorical | ≈ < 0.1 stable, 0.1–0.25 moderate, > 0.25 significant (industry rules of thumb from credit scoring) | Simple, symmetric-ish, sensitive to binning; quantile bins from the reference work well |
| **Kolmogorov–Smirnov (KS)** | Numeric | D = largest gap between the two CDFs, 0 to 1 | p-value becomes tiny for trivial shifts at large n |
| **Chi-square test** | Categorical | Compares category counts | Same large-n problem; merge rare categories |
| **Jensen–Shannon distance** | Numeric (binned) or categorical | 0 (identical) to 1 (disjoint), with log base 2 | Bounded and symmetric; good for dashboards |
| **Wasserstein (earth mover's) distance** | Numeric | In the feature's own units ("moved by 2.3 years") | Easy to explain; scale-dependent |
| **Share of unknown / null / out-of-range** | Any | A plain rate | Catches pipeline bugs faster than any distribution test |
| **Multivariate / model-based** | All features together | A classifier that tries to tell reference from current; AUC ≈ 0.5 means no drift | Catches changes in correlations; costlier |

Here is PSI and the KS statistic on three situations, with 50,000 rows per window:

```python
# drift_checks.py  (needs numpy)
import numpy as np

rng = np.random.default_rng(42)


def psi(reference: np.ndarray, current: np.ndarray, bins: int = 10) -> float:
    """Population Stability Index with bins cut at the reference distribution's quantiles."""
    edges = np.quantile(reference, np.linspace(0, 1, bins + 1))
    edges[0], edges[-1] = -np.inf, np.inf
    ref = np.histogram(reference, edges)[0] / len(reference)
    cur = np.histogram(current, edges)[0] / len(current)
    ref, cur = np.clip(ref, 1e-6, None), np.clip(cur, 1e-6, None)   # avoid log(0)
    return float(np.sum((cur - ref) * np.log(cur / ref)))


def ks_statistic(a: np.ndarray, b: np.ndarray) -> float:
    """Two-sample Kolmogorov-Smirnov D: the largest gap between the two empirical CDFs."""
    grid = np.sort(np.concatenate([a, b]))
    cdf_a = np.searchsorted(np.sort(a), grid, side="right") / len(a)
    cdf_b = np.searchsorted(np.sort(b), grid, side="right") / len(b)
    return float(np.max(np.abs(cdf_a - cdf_b)))


reference = rng.normal(loc=35, scale=8, size=50_000)          # user_age at training time
scenarios = {
    "same distribution": rng.normal(35, 8, 50_000),
    "tiny shift (+0.5 yr)": rng.normal(35.5, 8, 50_000),
    "campaign for 50-65s": np.concatenate([rng.normal(35, 8, 35_000), rng.uniform(50, 65, 15_000)]),
}
for name, current in scenarios.items():
    d = ks_statistic(reference, current)
    n = m = 50_000
    # asymptotic KS p-value approximation (Smirnov): p ≈ 2·exp(-2·D²·n·m/(n+m))
    p = min(1.0, 2 * np.exp(-2 * d * d * n * m / (n + m)))
    print(f"{name:22s} PSI={psi(reference, current):.3f}  KS D={d:.3f}  p≈{p:.1e}")
```

Output:

```text
same distribution      PSI=0.000  KS D=0.004  p≈8.6e-01
tiny shift (+0.5 yr)   PSI=0.004  KS D=0.027  p≈8.6e-16
campaign for 50-65s    PSI=0.451  KS D=0.290  p≈0.0e+00
```

**Precision note.** The half-year shift in average age is irrelevant to almost any model,
yet its KS p-value is 10⁻¹⁵: "statistically significant". With tens of thousands of rows,
every tiny change is significant, so an alert on "p < 0.05" fires constantly and gets
muted. Alert on an effect size (PSI, KS D, Jensen–Shannon distance) with thresholds you
tuned on past incidents, and weight features by their importance to the model: a big
shift in a feature the model barely uses matters less than a small shift in its top
feature. (In production code use `scipy.stats.ks_2samp` or a monitoring library; the
hand-written version above just shows what D is.)

**Practical defaults.** Compare the last day (or hour, for high-traffic models) against
the training window and against the same weekday last week. Monitor the top 10–20
features by importance plus the output. Track null, unknown-category and out-of-range
rates for every feature. Tune thresholds from history so the alert would have fired on
real past incidents and stayed quiet otherwise.

## 4. Monitoring predictions when labels are late

Many labels arrive late or never:

| Use case | Label | Delay (≈) |
|---|---|---|
| Ad click prediction | Click within an attribution window | Minutes to a day |
| Feed ranking | Engagement, dwell time | Minutes to hours |
| Delivery ETA | Actual delivery time | Under an hour |
| Churn | Did the user leave within 30 days? | 30+ days |
| Card fraud | Chargeback or confirmed fraud | Weeks to months; card-network dispute windows commonly allow up to ≈120 days |
| Credit default | Missed payments | Months to years |

While waiting, use:

- **Prediction drift.** If a fraud model historically flags 2% of transactions and
  suddenly flags 15%, either the model or its inputs broke, or a large attack is
  under way. Both need a human now.
- **Proxy labels.** Early signals correlated with the real label: a customer disputing a
  charge within 24 hours, a user who did not return for 7 days.
- **Performance estimation.** If the model is well calibrated, its own confidence
  estimates its accuracy on unlabelled data (NannyML's confidence-based performance
  estimation). It works under covariate drift, not under concept drift.
- **Label maturity.** When labels do arrive, compute quality only on cohorts whose labels
  are mature (for fraud, transactions older than the dispute window), or you will
  mistake "not yet reported" for "not fraud".

When labels arrive, join them to the prediction log by request ID and compute the same
metrics as offline evaluation (AUC, precision/recall at the operating threshold, MAE,
calibration), **per slice** (country, device, new vs returning users, model version).

## 5. Data quality checks at serving time

Most incidents are caught here, cheaply. Checks run on every batch of logged requests
(or inline for critical inputs):

- schema: expected columns present with expected types;
- null rate per feature within its normal band;
- categorical values in the known vocabulary (alert on the *rate* of unknowns);
- numeric values in plausible ranges (`age` between 0 and 120, `amount` ≥ 0);
- freshness: the age of features read from the online store;
- volume: request count by source, so a client that stopped sending one field is visible.

Data contracts with upstream teams (who promises which schema and semantics) prevent many
of these breakages in the first place; [Data Modeling: Star Schema & SCDs](../../ship-and-run/DataEngineering/02_data_modeling.md) and
[Microservices: Contract Testing](../../ship-and-run/TestingAndQuality/05_contract_testing.md) cover the ideas.

## 6. Instrumenting and alerting

Expose ML metrics from the model server in the same system as service metrics, so one
dashboard shows latency and prediction behaviour side by side
([Observability and Monitoring](../../ship-and-run/Tool-Kit/06_observability_and_monitoring.md)):

```python
# inside the model server (prometheus_client)
from prometheus_client import Counter, Histogram

SCORES = Histogram("model_score", "Predicted fraud probability",
                   ["model", "version"], buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 0.8, 0.95])
DECISIONS = Counter("model_decisions_total", "Decisions by outcome",
                    ["model", "version", "decision"])
DEFAULTED = Counter("model_feature_defaulted_total", "Features filled with a default",
                    ["model", "feature"])


def record(score: float, decision: str, defaulted: list[str], version: str) -> None:
    SCORES.labels("fraud", version).observe(score)
    DECISIONS.labels("fraud", version, decision).inc()
    for f in defaulted:
        DEFAULTED.labels("fraud", f).inc()
```

A Prometheus alerting rule on the decline rate:

```yaml
groups:
  - name: fraud-model
    rules:
      - alert: FraudDeclineRateHigh
        expr: |
          sum(rate(model_decisions_total{model="fraud", decision="decline"}[15m]))
            / sum(rate(model_decisions_total{model="fraud"}[15m])) > 0.05
        for: 15m
        labels:
          severity: page
        annotations:
          summary: "Fraud model declining {{ $value | humanizePercentage }} of transactions"
          runbook_url: "https://runbooks.internal/ml/fraud-decline-rate"
```

Feature distribution checks (PSI and friends) usually run as a batch job over the
prediction log every hour or day, writing results to a table that dashboards and alerts
read, because they need whole windows of data rather than counters.

Rules for alerts that people keep listening to:

- **Page only on what needs a human now:** outputs far out of band, a data-quality break
  on a top feature, a quality drop on mature labels. Everything else goes to a daily
  report.
- **Every alert links a runbook** with the triage steps below.
- **Compare with seasonality:** same hour last week, not only the training set.
- **Slice.** An average can hide one country or one app version going wrong.

<div class="lab" data-viz="flow-drift-retrain"></div>

## 7. When an alert fires: triage and response

1. **Is it the pipeline?** Check data-quality metrics, recent upstream deploys, schema
   changes, feature freshness, and whether one client or region accounts for the change.
   If yes: fix or roll back upstream; consider serving with defaults or the fallback.
2. **Is it our own rollout?** Group by model version. If the new version is the outlier,
   roll back by moving the registry alias (chapter 01).
3. **Is it real drift?** The input change is broad, persistent and explained by something
   in the world (a campaign, a new market, a season, an attack).
4. **Does it hurt quality?** Check mature-label metrics and proxies per slice. Not every
   drift hurts; a model can be robust to a shift.
5. **Respond:** retrain on recent data (possibly weighting recent rows higher, or with a
   shorter window), recalibrate the threshold, add features that capture the new regime,
   or fall back to rules while a new model is built.
6. **Ship the fix like any model:** gates, shadow, canary (chapters 01 and 03).

### Retraining strategies

| Strategy | How | Good for | Risk |
|---|---|---|---|
| **Scheduled** | Retrain nightly or weekly on a sliding window | Most models; predictable | Wasted compute when nothing changed; slow on sudden shifts |
| **Triggered** | Retrain when drift or quality alerts fire | Irregular change | Retrains on broken data if pipeline bugs are not ruled out first |
| **Online / incremental** | Update weights continuously from the stream | Very fast-moving domains (ads, feeds) | Hard to validate; can learn an attack or a bug in minutes |
| **Manual** | A data scientist investigates, re-curates data, maybe changes features | Concept drift that needs new features | Slow |

Whatever the trigger, the new model must pass the same validation gates before it
replaces the champion. Triggered retraining without gates is how a logging bug becomes a
production model.

## 8. Tools

| Tool | Type | What it gives you |
|---|---|---|
| **Evidently** | Open source (Python) | Drift and data-quality reports and test suites; monitoring UI |
| **NannyML** | Open source (Python) | Drift detection and performance estimation without labels |
| **Arize, Fiddler** | Commercial | Hosted ML observability: drift, slices, embeddings, LLM tracing |
| **SageMaker Model Monitor, Vertex AI Model Monitoring** | Managed cloud | Scheduled drift and quality checks on endpoint traffic |
| **Prometheus + Grafana** | Open source | Online counters and histograms, alerting |
| **Great Expectations, pandera, Soda** | Data quality | Expectation suites on pipelines and logged inputs |

## Common interview questions

**What is the difference between data drift and concept drift?**
Data (covariate) drift is a change in the input distribution P(X): different users,
different values. Concept drift is a change in P(Y given X): the same inputs now lead to a
different outcome. Data drift can be seen without labels; concept drift usually needs labels.

**How do you monitor a model whose labels arrive after 60 days?**
Data-quality checks, input drift weighted by feature importance, prediction drift and
decision rates immediately; proxy labels and calibrated performance estimation in the
meantime; real quality metrics on mature cohorts once labels arrive, per slice.

**Why not alert on KS test p-values?**
With large samples every negligible shift is significant, so the alert is always firing.
Use effect sizes (PSI, KS D, JS distance) with thresholds tuned on past incidents, and
weight by feature importance.

**Your drift alert fired. What do you do first?**
Rule out the pipeline: data-quality metrics, upstream changes, freshness, one source
dominating. Then check whether a model rollout caused it. Only then treat it as real
drift, check quality impact per slice, and retrain or recalibrate.

**What is PSI and what are its thresholds?**
Population Stability Index: bin the reference, compare the share of data in each bin,
sum (current − reference) × ln(current / reference). Rules of thumb: below 0.1 stable,
0.1–0.25 moderate, above 0.25 significant. They are conventions, not laws.

**Scheduled or triggered retraining?**
Scheduled as a baseline because it is simple and predictable; add triggers for fast
changes. Both go through validation gates. Online learning only where the domain moves in
minutes and there are strong safeguards.

**What should a prediction log contain?**
Request ID, timestamp, model name and version, features (or a sample), output, fallback
or default flags, experiment assignment. It feeds drift checks, label joins, debugging
and the next training set.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| **Student / Intern** | Intern | Intern (pre-L3) | Knows models degrade over time and can define data drift vs concept drift with an example. |
| **Junior (L3)** | ML Engineer I | L3 | Logs predictions with request ID and model version; adds data-quality checks and a PSI dashboard for top features; follows a runbook. |
| **Mid (L4)** | ML Engineer II | L4 | Builds the monitoring pipeline: drift jobs, label joins with maturity, per-slice quality, alert rules with tuned thresholds; triages alerts, separating pipeline breakage from drift. |
| **Senior (L5)** | Senior ML Engineer | L5 | Designs monitoring and retraining for a product with long label delays: proxies, performance estimation, seasonality-aware baselines, feedback-loop controls, retraining policy and its gates, on-call runbooks. |
| **Staff+ (L6+)** | Staff / Principal ML Engineer | L6–L8 | Sets organisation-wide standards for ML observability and model SLOs, data contracts with upstream teams, and incident review practice; decides platform vs vendor tooling. |

## Interview checklist

- [ ] I can list the six monitoring layers from service health to business KPIs and when each signal is available.
- [ ] I can distinguish covariate drift, label shift and concept drift, and tell drift apart from pipeline breakage and skew.
- [ ] I can compute PSI and explain KS D, and why p-values mislead at large sample sizes.
- [ ] I can monitor with delayed labels: prediction drift, proxies, performance estimation, label maturity.
- [ ] I can say what a prediction log must contain and why.
- [ ] I can write a Prometheus metric and alert for prediction behaviour, with a runbook.
- [ ] I can walk the triage steps when a drift alert fires.
- [ ] I can compare scheduled, triggered, online and manual retraining.

Related: [The MLOps Lifecycle](01_mlops_lifecycle.md), [Feature Stores and Data Leakage](02_feature_stores.md),
[ML and LLM Systems](../../interview-core/SystemDesign/building_blocks/23_ml_and_llm_systems.md) (monitoring ML systems),
[Observability and Reliability](../../interview-core/SystemDesign/building_blocks/15_observability_and_reliability.md),
[Day 168: Data Drift & Concept Drift (The Silent Killers)](../AI-road-map/168_day_drift_detection.md).
