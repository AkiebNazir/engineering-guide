# A/B Testing and Experimentation

A new model beats the production model on last month's held-out data. Should it go to
100% of users? Not yet. Offline metrics (AUC, NDCG, F1) predict online outcomes (clicks,
revenue, retention) only loosely, and the only reliable way to learn whether a change
helps users is a randomised controlled experiment. This chapter covers designing an A/B
test for an ML model (metrics, power, sample size), assigning users correctly, analysing
the result without fooling yourself, the classic pitfalls (peeking, sample-ratio
mismatch, novelty, interference), and ML-specific tools: interleaving, off-policy
evaluation and bandits. The Python in this chapter runs with the standard library.

## Foundations — How do you know a new model is actually better?

### Why offline evaluation is not enough

Offline evaluation replays history: "on last month's sessions, would the new ranker have
put the clicked item higher?" It cannot answer:

- **What users do when they see something different.** The logs only show reactions to
  what the *old* model chose. A new model that surfaces different items has no labels for
  them (this is selection bias).
- **Whether the offline metric tracks the business goal.** A ranker can raise click
  probability and lower long-term retention (clickbait).
- **System effects**: latency, a changed mix of content, marketplace responses.

An **A/B test** (online controlled experiment) answers these by randomly splitting users
into groups, giving each group a different version, and comparing outcomes. Because
assignment is random, the only systematic difference between the groups is the version
they got, so a difference in outcomes beyond what chance explains is caused by the change.

### The pieces

| Piece | Meaning | Example |
|---|---|---|
| **Unit of randomisation** | What gets assigned: user, session, device, request, city | `user_id` |
| **Variants** | Control (A, current model) and treatment(s) (B, new model) | ranker v1 vs v2 |
| **Assignment** | A deterministic function from unit to variant | `hash("exp_123:" + user_id) % 100 < 50` |
| **Exposure log** | A record that a unit actually experienced its variant | Logged when the ranked page renders |
| **Primary metric** | The one metric the decision is based on (overall evaluation criterion, OEC) | Purchases per user |
| **Guardrail metrics** | Must not get worse | Latency p99, crash rate, unsubscribes, revenue |
| **Minimum detectable effect (MDE)** | The smallest effect worth detecting, which sets the sample size | +0.2 percentage points of CTR |
| **Significance level α, power** | False-positive rate you accept (0.05), chance of detecting a real MDE (0.8) | Conventions; choose deliberately |

An everyday analogy: a clinical trial. Patients are randomly assigned to drug or placebo,
the outcome and the sample size are fixed before the trial starts, and nobody declares
victory after the first good week.

## 1. Designing the experiment

Write this down *before* launch:

1. **Hypothesis.** "Ranker v2 increases purchases per user by at least 1% without
   increasing p99 latency by more than 10 ms."
2. **Unit.** Usually the user, so that each person has a consistent experience and
   repeated actions by one person are not treated as independent.
3. **Primary metric and guardrails.** One primary metric; a short list of guardrails;
   diagnostic metrics for understanding (CTR, dwell time, coverage).
4. **MDE, α and power**, which give the **sample size**.
5. **Duration.** Long enough to reach the sample size and to cover **whole weekly cycles**
   (at least one, usually two), because behaviour differs by weekday.
6. **Decision rule.** What result ships, what result is rolled back, what is inconclusive.

### Sample size: why small lifts need big experiments

For a conversion-type metric with baseline rate *p* and absolute MDE *δ*, the number of
units per arm for a two-sided test is approximately

n ≈ (z₁₋α/₂ + z₁₋β)² · [p₁(1 − p₁) + p₂(1 − p₂)] / δ²

A typical ranking test (CTR 5.1% → 5.3%, an absolute lift of 0.2 points, about 4% relative)
needs roughly **193,000 users per arm** at α = 0.05 and 80% power (computed below). Halving
the MDE quadruples the sample size, which is why detecting a 0.1-point change takes four
times as long.

### Runnable toolkit

```python
# ab_stats.py  (stdlib only)
import hashlib
import math
import random
from statistics import NormalDist

Z = NormalDist()


def bucket(user_id: str, experiment: str, buckets: int = 100) -> int:
    """Deterministic assignment: same user + experiment -> same bucket, independent across experiments."""
    h = hashlib.sha256(f"{experiment}:{user_id}".encode()).digest()
    return int.from_bytes(h[:8], "big") % buckets


def sample_size_per_arm(p_base: float, mde_abs: float, alpha=0.05, power=0.8) -> int:
    """Users per arm to detect an absolute lift `mde_abs` on a conversion rate (two-sided z-test)."""
    p2 = p_base + mde_abs
    z = Z.inv_cdf(1 - alpha / 2) + Z.inv_cdf(power)
    return math.ceil(z * z * (p_base * (1 - p_base) + p2 * (1 - p2)) / mde_abs ** 2)


def two_proportion_z(conv_a: int, n_a: int, conv_b: int, n_b: int):
    pa, pb = conv_a / n_a, conv_b / n_b
    pooled = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (pb - pa) / se
    se_diff = math.sqrt(pa * (1 - pa) / n_a + pb * (1 - pb) / n_b)
    ci = (pb - pa - 1.96 * se_diff, pb - pa + 1.96 * se_diff)
    return z, 2 * (1 - Z.cdf(abs(z))), ci


def srm_p_value(n_a: int, n_b: int, expected_share_a=0.5) -> float:
    """Sample-ratio mismatch: chi-square test (1 d.o.f.) of the observed split vs the design."""
    total = n_a + n_b
    ea, eb = total * expected_share_a, total * (1 - expected_share_a)
    chi2 = (n_a - ea) ** 2 / ea + (n_b - eb) ** 2 / eb
    return 2 * (1 - Z.cdf(math.sqrt(chi2)))            # chi-square(1) tail = two-sided normal tail


print("bucket of user 42 in exp_123:", bucket("42", "exp_123"))
n = sample_size_per_arm(0.051, 0.002)
print(f"users per arm to detect 5.1% -> 5.3%: {n:,}")

z, p, ci = two_proportion_z(5_100, 100_000, 5_300, 100_000)
print(f"100k per arm, 5.1% vs 5.3%: z={z:.2f} p={p:.3f} 95% CI of lift=({ci[0]:+.4f}, {ci[1]:+.4f})")
print(f"SRM check for 50,000 vs 51,000 users: p={srm_p_value(50_000, 51_000):.4f}")

# Peeking: an A/A test (no real difference) checked every day for 20 days.
random.seed(1)
runs, days, users_per_day, rate = 1000, 20, 2_000, 0.05
false_wins_peek = false_wins_end = 0
for _ in range(runs):
    ca = cb = na = nb = 0
    peeked_significant = False
    for _ in range(days):
        na += users_per_day; nb += users_per_day
        ca += sum(random.random() < rate for _ in range(users_per_day))
        cb += sum(random.random() < rate for _ in range(users_per_day))
        if two_proportion_z(ca, na, cb, nb)[1] < 0.05:
            peeked_significant = True
    false_wins_peek += peeked_significant
    false_wins_end += two_proportion_z(ca, na, cb, nb)[1] < 0.05
print(f"A/A false positive rate: checked once at the end {false_wins_end / runs:.1%}, "
      f"stopped at first daily p<0.05 {false_wins_peek / runs:.1%}")
```

Output (≈ 5 s):

```text
bucket of user 42 in exp_123: 0
users per arm to detect 5.1% -> 5.3%: 193,456
100k per arm, 5.1% vs 5.3%: z=2.01 p=0.044 95% CI of lift=(+0.0001, +0.0039)
SRM check for 50,000 vs 51,000 users: p=0.0017
A/A false positive rate: checked once at the end 4.8%, stopped at first daily p<0.05 24.2%
```

Each line is used in a section below.

## 2. Assignment: randomise correctly

- **Deterministic hashing.** `hash(experiment_salt + ":" + user_id) % buckets` gives
  every user the same variant on every request and every server, with no lookup table.
  A per-experiment salt makes assignments in different experiments independent, so the
  users in treatment for one test are not systematically in treatment for another.
- **Use a good hash.** A cryptographic or well-mixed hash (SHA-256, MurmurHash3,
  xxHash). Language built-ins like Python's `hash()` are randomised per process and
  must not be used.
- **Layers.** Large platforms run hundreds of experiments at once. Experiments that could
  interact (two ranking changes) go in the same *layer* and get disjoint bucket ranges;
  experiments in different layers (ranking vs UI colour) overlap independently.
- **Log exposure, analyse exposed users.** Assign at the point where the variant can
  first make a difference, and include only users who reached that point, in both arms.
  Counting users who never saw the ranked page dilutes the effect.
- **Unit of analysis = unit of randomisation.** If you randomise users but compute CTR
  per page view, page views from one user are correlated; the naive variance is too
  small and p-values are too optimistic. Use the delta method or a bootstrap over users
  for such ratio metrics.

```arch
%% caption: Assignment is a pure function of the user and the experiment salt; exposure is logged where the variant takes effect, and analysis joins exposures to outcomes.
grid 150x110
node user "User request" at 0,0 icon=user sub="user_id"
node assign "Assignment" at 1,0 icon=sigma sub="hash(salt:user) % 100"
node cfg "Experiment config" at 1,1 icon=file sub="layers, ranges, ramp"
node ctrl "Ranker v1" at 2,0 icon=model sub="control, 0-49"
node treat "Ranker v2" at 2,1 icon=model sub="treatment, 50-99"
node expo "Exposure + outcomes" at 3,1 icon=logs sub="variant, clicks, buys"
node stats "Analysis" at 3,2 icon=metrics sub="SRM, lift, CI"
user -> assign
cfg -> assign
assign -> ctrl
assign -> treat
ctrl -> expo
treat -> expo
expo -> stats
```

Assignment, layers, config distribution and exposure pipelines at scale are designed in
[Experimentation Platform](../../interview-core/SystemDesign/solutions/037_experimentation_platform_solution.md).

## 3. Analysing the result

With 100,000 users per arm, control converts at 5.1% and treatment at 5.3%. The test
gives z = 2.01, p = 0.044, and a 95% confidence interval for the lift of +0.01 to +0.39
percentage points.

**Precision note: what a p-value is and is not.** The p-value is the probability of
seeing a difference *at least this large* **if there were truly no difference** (the null
hypothesis). It is **not** the probability that the difference is due to chance, and
p < 0.05 does **not** mean "95% confident that v2 is better". What α = 0.05 guarantees is
that, among experiments where the change truly does nothing, about 5% will still come out
"significant". The honest summary here is: "the data are unlikely under no effect; the
lift is somewhere between about 0 and 0.4 points."

Read the result with the **confidence interval**, not the p-value alone:

- The interval barely excludes zero, and this experiment ran with about half the users
  the design called for (193k per arm). An underpowered experiment that just crosses
  p < 0.05 tends to overstate the true effect (the "winner's curse"). Run to the planned
  size.
- **Statistical vs practical significance.** A lift can be real and too small to matter,
  or too small to pay for the new model's serving cost.
- **Check the guardrails** and the **sample ratio** before believing any of it.

### Variance reduction: CUPED

Much of the noise in a user metric is just that some users buy more than others, before
and during the experiment. **CUPED** (Deng et al., 2013) adjusts each user's metric by
their pre-experiment value of the same metric:
`Y_adj = Y − θ · (X_pre − mean(X_pre))`, with `θ = cov(Y, X_pre) / var(X_pre)`. Because
assignment is random, this does not bias the comparison, and when pre- and in-experiment
behaviour are strongly correlated, it cuts variance substantially, which means smaller
samples or shorter tests for the same power.

## 4. Pitfalls

### Peeking

A product manager checks the dashboard every day and stops the test the first time
p < 0.05. In the simulation above, an **A/A test** (no difference at all) checked daily
for 20 days reached "significance" at some point in **24%** of runs, against the 5%
promised, versus 4.8% when checked once at the end.

Fixes, in order of practicality:
- **Fix the sample size and duration in advance** and decide only at the end; dashboards
  can show data but not "significance" before then.
- **Sequential testing** when you really need to monitor continuously: group-sequential
  designs with alpha spending (O'Brien–Fleming boundaries), or always-valid p-values /
  confidence sequences (mSPRT). Many commercial experimentation platforms offer these.
- Stop early only for **harm** on guardrails, with pre-agreed thresholds.

### Sample-ratio mismatch (SRM)

A 50/50 test that ends with 50,000 users in control and 51,000 in treatment looks
harmless, but the chi-square test gives p = 0.0017: the split is very unlikely to be
chance. Common causes: the new model is slower, so more treatment sessions time out
before being logged (or fewer, and the reverse); a bot filter hits one arm more; a
redirect loses users; exposure is logged in different places in each arm. **An SRM
invalidates the result**: find the cause before reading any metric.

### Novelty and primacy effects

Users click new-looking recommendations because they are new (**novelty**), or resist a
change because they are used to the old layout (**primacy**). Both fade. Plot the
treatment effect by day since first exposure; if it trends, run longer or measure on
new users only, who have no old habit.

### Interference (network effects)

The analysis assumes one user's variant does not affect another's outcome (SUTVA). It
breaks in:

- **Marketplaces.** Give treatment drivers better dispatch and they take rides from
  control drivers; control looks worse *because* treatment exists. Fix: **switchback
  tests** (a whole city alternates between control and treatment in time slices, e.g.
  every hour or day) or **geo experiments** (whole regions assigned).
- **Social networks.** A feature that makes treatment users share more changes what control
  users see. Fix: **cluster randomisation** over graph communities.
- **Shared budgets** in ads: treatment spends the budget that control would have used.
  Fix: budget-split experiments.

Switchbacks and geo tests have far fewer independent units, so they need more time and
analysis that accounts for correlation between adjacent periods or regions.

### Multiple comparisons

Twenty metrics at α = 0.05 will produce about one false "win" even when nothing changed.
Name one primary metric in advance, and treat the rest as guardrails or diagnostics. Use
corrections (Bonferroni, Benjamini–Hochberg) when many hypotheses are tested, and be wary
of post-hoc slicing ("it worked on Android tablets in Brazil").

### Other traps

| Trap | Symptom | Fix |
|---|---|---|
| **Carryover** | Users re-bucketed from a previous test still behave differently | Fresh salts; cool-down periods |
| **Bots and outliers** | One heavy user dominates revenue | Bot filtering; winsorise or cap per-user metrics |
| **Simpson's paradox** | Ramp changes the traffic mix across days | Constant allocation during the analysis period; stratify |
| **Metric definition drift** | Logging change mid-test | Freeze metric definitions; A/A tests after logging changes |

## 5. ML-specific experimentation

### Offline metric vs online metric

Offline metrics are necessary gates, not verdicts. Track, across past launches, how
offline improvements translated online; if NDCG gains stop predicting online gains, the
offline metric or its test set needs changing. The gap has predictable causes: selection
bias in logs, position bias, training–serving skew, and metrics that reward short-term
clicks over long-term value.

### Interleaving (for rankers)

Instead of splitting users, **interleaving** merges the results of rankers A and B into
one list for the same user (team-draft interleaving alternates picks) and credits each
click to the ranker that contributed the item. Because each user compares both rankers
directly, it needs far less traffic than an A/B test to detect *which ranker is
preferred*. It does not measure effects on business metrics like revenue, so a common
flow is: interleave many candidates quickly, then A/B test the winner.

### Off-policy (counterfactual) evaluation

If the production system logs the **probability** with which it chose each action (the
propensity), you can estimate how a different policy would have performed from logs
alone, with **inverse propensity scoring**: reweight each logged reward by
`π_new(action | context) / π_logged(action | context)`. This requires that the logging
policy gave every action the new policy might take a non-zero probability, which is why
systems keep a small amount of randomised exploration. Doubly robust estimators reduce
the variance.

### Bandits

A/B tests spend half the traffic on the loser for the whole test. **Multi-armed bandits**
(epsilon-greedy, Thompson sampling, UCB) shift traffic toward better variants as evidence
arrives. Use them when the goal is to earn reward during the test (headlines, creatives,
cold-start exploration), not when you need a clean, unbiased effect estimate for a launch
decision. **Contextual bandits** pick per user and are common in recommendation
exploration (chapter 06).

### A launch sequence for a new model

```arch
%% caption: Each stage answers a different question with more risk than the last: is it better on history, is it safe on live traffic, is it better for users.
grid 130x100
node off "Offline eval" at 0,0 icon=table sub="vs champion, slices"
node shadow "Shadow" at 1,0 icon=eye sub="latency, output drift"
node canary "Canary 1-5%" at 2,0 icon=flag sub="guardrails"
node ab "A/B test" at 3,0 icon=metrics sub="planned size"
node ramp "Ramp to 100%" at 4,0 icon=rocket sub="holdback 1-5%"
node rb "Roll back" at 2,1 icon=error color=red sub="alias to champion"
off -> shadow -> canary -> ab -> ramp
canary ..> rb : "breach"
ab:B ..> rb:R : "loses"
```

A **long-term holdback** (a small share of users kept on the old model for weeks or
months after launch) measures effects that a two-week test cannot, such as retention,
and checks whether the gains from many launches actually add up.

## Common interview questions

**Your new model has better AUC. Why not ship it?**
AUC is measured on logs produced by the old model, so it has selection bias and may not
track the business metric; it ignores latency and system effects. Gate on offline metrics,
then shadow, canary and A/B test on the primary metric with guardrails.

**How do you pick the sample size?**
From the baseline rate, the minimum detectable effect worth shipping, α and power; for
conversion metrics n per arm ≈ (z_α/2 + z_β)² (p₁q₁ + p₂q₂) / δ². Then round the
duration up to whole weeks.

**What is a p-value?**
The probability of observing a difference at least as extreme as the one seen, assuming
there is no true difference. It is not the probability that the treatment is better.

**What is peeking and how do you avoid it?**
Repeatedly checking significance and stopping at the first p < 0.05 inflates false
positives (≈ 24% in the 20-look simulation above). Fix the horizon in advance, or use
sequential methods (alpha spending, always-valid p-values).

**What is sample-ratio mismatch?**
An observed split that differs significantly from the designed one (chi-square test).
It means assignment or logging is broken in one arm, and it invalidates the results until
explained.

**How do you test a change in a two-sided marketplace?**
User-level randomisation is contaminated by interference. Use switchback tests by time
slice, geo experiments or cluster randomisation, and analyse with the reduced number of
independent units in mind.

**A/B test or interleaving for a new ranker?**
Interleaving for a fast, sensitive preference check among several rankers; an A/B test
for the launch decision on business metrics and guardrails.

**When would you use a bandit instead of an A/B test?**
When earning reward during the test matters more than an unbiased effect estimate: many
variants, short-lived content, exploration for cold start.

## What Each Engineering Level Should Know

| Level | Industry title | Google ladder | What they should know |
|---|---|---|---|
| **Student / Intern** | Intern | Intern (pre-L3) | Explains why randomisation gives causal answers and why a new model needs an online test. Knows what a control group is. |
| **Junior (L3)** | ML Engineer I | L3 | Implements deterministic hash bucketing and exposure logging; reads a results dashboard correctly (CI, not just p); knows peeking is invalid. |
| **Mid (L4)** | ML Engineer II | L4 | Designs a test: primary metric, guardrails, MDE, sample size, duration; checks SRM; handles ratio metrics with the delta method; runs shadow and canary before the A/B test. |
| **Senior (L5)** | Senior ML Engineer, Senior Data Scientist | L5 | Chooses the right method for the situation (A/B, interleaving, switchback, geo, bandit, off-policy evaluation); uses CUPED and sequential testing; diagnoses novelty, interference and offline–online metric gaps; defines launch criteria. |
| **Staff+ (L6+)** | Staff / Principal | L6–L8 | Owns experimentation culture and platform: the OEC for a product, layers and holdbacks, metric governance, and the link between offline metrics and online outcomes across many teams. |

## Interview checklist

- [ ] I can explain why offline metrics are insufficient and list what an A/B test adds.
- [ ] I can define unit of randomisation, exposure, primary metric, guardrails, MDE, α and power.
- [ ] I can compute a sample size for a conversion metric and explain why halving the MDE quadruples it.
- [ ] I can implement deterministic, salted hash assignment and explain layers.
- [ ] I can state the correct definition of a p-value and read a confidence interval.
- [ ] I can explain peeking, SRM, novelty/primacy, interference and multiple comparisons, with a fix for each.
- [ ] I can explain CUPED, sequential testing and the delta method at a high level.
- [ ] I can compare A/B testing, interleaving, off-policy evaluation and bandits for ML models.
- [ ] I can lay out a launch sequence from offline eval to holdback, with rollback points.

Related: [Ranking, Recommendation, and Experimentation](../../interview-core/SystemDesign/building_blocks/31_ranking_recommendation_and_experimentation.md)
(Part 2), [Experimentation Platform](../../interview-core/SystemDesign/solutions/037_experimentation_platform_solution.md),
[Feature Flags and Rollbacks](../../ship-and-run/CICD/05_feature_flags_and_rollbacks.md), [System Design: Recommendation Systems](06_sysdesign_recsys.md).
