# Statistics — Learning From Data Without Fooling Yourself

Probability goes from a known model to predictions about data; statistics goes the
other way, from data to conclusions about the world. Engineers do statistics every day
without calling it that: reading latency dashboards, deciding whether a change made
things faster, running A/B tests, setting alert thresholds, sizing capacity. This
chapter covers the parts that matter in that work — summarising data honestly (and why
the average latency is nearly useless), the central limit theorem, confidence
intervals, hypothesis tests and p-values, A/B testing done right, correlation versus
causation, and how to benchmark without fooling yourself.

**Where this fits:** Part 3 · Continuous maths, chapter 11 of 15. **Builds on:** [10 Probability](10_probability.md) (distributions). **Next in order:** [12 Calculus](12_calculus.md).

## Where You Will Use This

| Task | Statistics you need |
|---|---|
| Latency SLOs and dashboards | Percentiles, tails, why you cannot average p99s |
| "Did my change make it faster?" | Repeated measurements, spread, confidence intervals |
| A/B tests and feature launches | Hypothesis tests, p-values, power, sample size, peeking |
| Alert thresholds | Distributions, z-scores, base rates (chapter 10) |
| Capacity planning | Means, variance, growth, the CLT |
| ML evaluation | Sampling, confidence, correlation, leakage and confounders |

## Foundations — Samples Stand In for Populations

The **population** is everything you care about (every request your service will ever
serve); a **sample** is the part you measured (last hour's requests). **Descriptive
statistics** summarise the sample. **Inferential statistics** say what the sample
implies about the population, and how sure you can be.

> **Analogy:** Tasting soup. One spoonful (a sample) tells you about the whole pot (the
> population) — **if the pot is stirred** (the sample is random). A spoonful skimmed
> from the top tells you about the top. Most statistical disasters are unstirred pots:
> measuring only fast requests, only happy users, only the servers that responded.

## 1 · The Centre: Mean, Median, Mode

| Measure | Definition | Sensitive to outliers? |
|---|---|---|
| **Mean** $\bar{x} = \frac{1}{n}\sum x_i$ | the balance point | **very** |
| **Median** | the middle value when sorted | no |
| **Mode** | the most common value | no |

```python
import statistics as st

latencies_ms = [12, 13, 13, 14, 15, 15, 15, 16, 18, 2400]   # one request hit a GC pause
print(st.mean(latencies_ms), st.median(latencies_ms), st.mode(latencies_ms))   # → 253.1 15.0 15
```

One slow request makes the mean 253 ms, though 9 of 10 requests took 12–18 ms. The
median (15 ms) describes the typical request; the mean describes nobody. Neither
describes the slow one — for that you need the tail (§3).

> **Key idea:** Use the **median** for "typical", **percentiles** for "how bad does it
> get", and the **mean** when you need totals (mean × count = total work, which is what
> capacity planning cares about).

> **Notebook example:** Seven response times, in ms: 8, 3, 5, 12, 5, 7, 100. Find the
> mean, median and mode, then do it again without the 100.
>
> 1. Sort them: 3, 5, 5, 7, 8, 12, 100.
> 2. **Mean:** the sum is $3 + 5 + 5 + 7 + 8 + 12 + 100 = 140$, and $140 / 7 = 20$.
> 3. **Median:** the 4th of 7 values is **7**.
> 4. **Mode:** 5 appears twice, so the mode is **5**.
> 5. Without the 100: the mean is $40 / 6 \approx 6.7$, and the median is the average of
>    the middle two, $(5 + 7)/2 = 6$.
>
> **Answer:** mean 20, median 7, mode 5. One slow value tripled the mean but moved the
> median by just 1. That is why "typical" means median.

## 2 · The Spread: Variance, Standard Deviation, IQR

- **Variance**: the average squared distance from the mean. **Standard deviation** σ is
  its square root, in the original units.
- **Sample** variance divides by $n - 1$, not n (**Bessel's correction**): the sample
  mean is fitted to the data, so deviations from it are slightly too small, and dividing
  by $n - 1$ compensates.
- **Interquartile range** (IQR): the 75th minus the 25th percentile — the spread of the
  middle half, robust to outliers.
- A **z-score** $z = (x - \bar{x})/\sigma$ says how many standard deviations a value is
  from the mean.

```python
import statistics as st
data = [2, 4, 4, 4, 5, 5, 7, 9]
print(st.pstdev(data), round(st.stdev(data), 4))   # → 2.0 2.1381
q1, q2, q3 = st.quantiles(data, n=4)
print(q1, q3, q3 - q1)                             # → 4.0 6.5 2.5
```

(`pstdev` treats the data as the whole population; `stdev` as a sample.)

> **Notebook example:** For the data 2, 4, 4, 4, 5, 5, 7, 9, find the variance and
> standard deviation (population and sample), and the z-score of 9.
>
> 1. Mean: $40 / 8 = 5$.
> 2. Deviations from 5: −3, −1, −1, −1, 0, 0, 2, 4.
> 3. Squares: 9, 1, 1, 1, 0, 0, 4, 16. They sum to **32**.
> 4. Population variance $= 32 / 8 = 4$, so $\sigma = 2$.
> 5. Sample variance $= 32 / 7 \approx 4.57$, so $s \approx 2.14$.
> 6. z-score of 9: $(9 - 5) / 2 = 2$, which is two standard deviations above the mean.
>
> **Answer:** σ = 2 (or s ≈ 2.14 as a sample), and z = 2.

## 3 · Percentiles and Tail Latency

The **p-th percentile** is the value below which p% of the data falls. p50 is the
median; p99 means "99% of requests were faster than this". Latency distributions have
**long right tails** — queueing, garbage collection, retries, cold caches — so the tail
behaves nothing like the middle.

**Try it: grow the tail.** Drag the share of slow requests from 0% to 5%. The median
barely moves; the mean creeps up; the p99 jumps from the body of the distribution to the
slow cluster. Then raise the fan-out: a page that waits for 100 backends sees at least
one backend's p99 on 63% of loads.

<div class="lab" data-viz="math-percentiles"></div>

```python
print(round(1 - 0.99**100, 3))   # → 0.634
```

> **Notebook example:** Ten latencies, in ms: 10, 11, 12, 12, 13, 14, 15, 20, 45, 300.
> Find p50 and p90 with the nearest-rank method, then the chance that a page calling 10
> backends sees at least one backend's p99.
>
> 1. **Nearest rank** for p%: take the value at position $\lceil \frac{p}{100} \times n \rceil$
>    in sorted order.
> 2. p50: $\lceil 0.5 \times 10 \rceil = 5$, and the 5th value is **13 ms**.
> 3. p90: $\lceil 0.9 \times 10 \rceil = 9$, and the 9th value is **45 ms**.
> 4. A backend is faster than its p99 with probability 0.99. All 10 are fast with
>    probability $0.99^{10} \approx 0.904$.
> 5. So at least one is slow with probability $1 - 0.904 = 9.6\%$.
>
> **Answer:** p50 = 13 ms, p90 = 45 ms, and about 1 page in 10 hits a p99 tail. With 100
> backends it is $1 - 0.99^{100} \approx 63\%$.

> **Key idea:** In a system that fans out, **the tail of one component becomes the
> typical experience of the whole**. That is why large services set SLOs on p99/p99.9,
> use hedged requests (send a duplicate after the p95 delay), and chase GC pauses.

### Two percentile traps

**There are several definitions.** For small samples, "the 90th percentile" depends on
the interpolation method; libraries differ.

```python
import statistics as st
data = list(range(1, 11))                   # 1..10
print(st.quantiles(data, n=10, method="exclusive")[-1], st.quantiles(data, n=10, method="inclusive")[-1])   # → 9.9 9.1
```

**You cannot average percentiles.** The p99 of the whole fleet is not the average of each
server's p99. Percentiles are not additive; combine **histograms** (bucket counts) and
compute the percentile from the merged histogram — which is what Prometheus histograms,
HdrHistogram and t-digest are for.

```python
import random, statistics as st
random.seed(5)
fast = [random.expovariate(1 / 10) for _ in range(9000)]     # server A: busy and fast
slow = [random.expovariate(1 / 100) for _ in range(1000)]    # server B: quiet and slow
p99 = lambda xs: st.quantiles(xs, n=100)[-1]
avg_of_p99s = (p99(fast) + p99(slow)) / 2
true_p99 = p99(fast + slow)
print(round(avg_of_p99s), round(true_p99))   # → 255 233
```

Averaging the two servers' p99s (255 ms) misstates the fleet's real p99 (233 ms), because
it ignores that server A handles nine times the traffic. The error can go either way.

## 4 · The Shape of Data: the Normal Distribution and Its Limits

Many measurements that are **sums of many small independent effects** (heights,
measurement noise, averages of samples) follow the **normal** (Gaussian) bell curve. Its
convenient rule of thumb:

| Within | Fraction of data |
|---|---|
| μ ± 1σ | 68.3% |
| μ ± 2σ | 95.4% |
| μ ± 3σ | 99.7% |

```python
import math
within = lambda k: math.erf(k / math.sqrt(2))
print([round(within(k) * 100, 1) for k in (1, 2, 3)])   # → [68.3, 95.4, 99.7]
```

> **Notebook example:** A batch job's run time is roughly normal, with mean 200 s and
> σ = 20 s. How often does it finish between 160 s and 240 s? How often does it take
> over 260 s?
>
> 1. Convert to z-scores: $160 = 200 - 2 \times 20$ and $240 = 200 + 2 \times 20$, so
>    this is the range ±2σ.
> 2. From the table, ±2σ holds **95.4%** of runs.
> 3. $260 = 200 + 3\sigma$. ±3σ holds 99.7%, which leaves 0.3% outside, split between
>    the two tails.
> 4. The upper tail alone is about $0.3\% / 2 \approx 0.13\%$ (exactly 0.135%).
>
> **Answer:** about 95% of runs, and about 1 run in 740. Use this only once the
> histogram looks like a bell.

> **Watch out:** Latencies, file sizes, incomes and request counts per user are **not**
> normal — they are skewed with heavy tails (often closer to lognormal or power-law).
> "Alert when latency exceeds mean + 3σ" assumes normality and will fire constantly
> (or never). Look at the histogram before choosing a summary.

## 5 · The Central Limit Theorem

> **Key idea:** Take the average of n independent measurements from **any**
> distribution with mean μ and standard deviation σ. As n grows, the distribution of
> that average approaches a normal distribution with mean μ and standard deviation
> $\sigma/\sqrt{n}$ — the **standard error**.

That is why the normal distribution is everywhere even when data is not normal: we
usually care about **averages** (conversion rates, mean times, totals), and averages are
approximately normal. It is also why error bars shrink like $1/\sqrt{n}$ — quadruple the
sample to halve the uncertainty.

**Try it: watch the bell appear.** Choose the skewed exponential source with n = 1: the
histogram is the skewed source itself. Raise n to 2, 5, 30: the averages pile into a
bell around μ, and the measured spread tracks σ/√n. Try the U-shaped source, which looks
nothing like a bell, and watch it happen anyway.

<div class="lab" data-viz="math-clt"></div>

> **Notebook example:** A single request takes 100 ms on average, with σ = 40 ms. What is
> the spread of the **average** of 16 requests? How many requests would give a spread of
> 5 ms?
>
> 1. Standard error $= \sigma / \sqrt{n} = 40 / \sqrt{16} = 40 / 4 = 10$ ms.
> 2. By the CLT the average is roughly normal, so about 95% of 16-request averages fall
>    within $100 \pm 2 \times 10$, that is, 80 to 120 ms.
> 3. For a spread of 5 ms: $40 / \sqrt{n} = 5$, so $\sqrt{n} = 8$ and $n = 64$.
>
> **Answer:** 10 ms, and 64 requests. Halving the error took 4 times the data.

## 6 · Confidence Intervals

A **95% confidence interval** for a mean is roughly

$$
\bar{x} \pm 1.96 \cdot \frac{s}{\sqrt{n}}
$$

where s is the sample standard deviation. The precise meaning: if you repeated the
whole experiment many times, about 95% of the intervals built this way would contain the
true mean. (It is **not** "95% probability the true value is in this particular
interval" — a subtle but real distinction.)

> **Worked example:** Twenty benchmark runs average 118 ms with a standard deviation of
> 9 ms. Standard error $9/\sqrt{20} \approx 2.0$ ms; 95% CI ≈ 118 ± 3.9 ms. If the old
> version's interval is 124 ± 4 ms, the intervals barely overlap — suggestive, not
> conclusive. More runs narrow both.

```python
import math, statistics as st
runs = [118, 109, 131, 115, 122, 104, 127, 119, 113, 125, 117, 121, 108, 130, 116, 120, 112, 124, 114, 125]
m, s, n = st.mean(runs), st.stdev(runs), len(runs)
half = 1.96 * s / math.sqrt(n)
print(m, round(s, 2), f"{m - half:.1f} .. {m + half:.1f}")   # → 118.5 7.33 115.3 .. 121.7
```

(For small n, the t-distribution gives a slightly wider interval than 1.96; with n = 20
the multiplier is 2.09.)

## 7 · Hypothesis Tests and p-Values

The logic of a test is proof by contradiction with a tolerance for bad luck:

1. State a **null hypothesis** $H_0$ — "no effect" (the coin is fair; the new button
   changes nothing).
2. Compute how surprising your data would be **if $H_0$ were true**: the **p-value**
   is the probability of data at least as extreme as yours, under $H_0$.
3. If p is below a threshold α (conventionally 0.05), reject $H_0$.

**Try it: test a coin.** The bars are how often a fair coin gives each head count in n
flips. The pre-loaded result, 58 heads in 100, gives p ≈ 0.13 — not unusual for a fair
coin. Press *Flip* a few times, then *Repeat the experiment 1,000×* with the coin fair:
about 5% of experiments "detect" a bias that is not there. Set the true P(heads) to 0.55
and see how often a test of 100 flips catches it (its power), then raise n.

<div class="lab" data-viz="math-pvalue"></div>

> **Notebook example:** A coin lands heads 9 times in 10 flips. Is it fair, at
> α = 0.05?
>
> 1. $H_0$: the coin is fair, so each of the $2^{10} = 1024$ flip sequences is equally
>    likely.
> 2. Results at least this extreme in the heads direction: 9 heads ($\binom{10}{9} = 10$
>    sequences) or 10 heads (1 sequence), 11 sequences in all.
> 3. One-sided: $11 / 1024 \approx 1.07\%$. Two-sided, counting 9 or more **tails** too:
>    $22 / 1024 \approx 2.15\%$.
> 4. $2.15\% < 5\%$, so reject $H_0$.
>
> **Answer:** p ≈ 0.021, so the coin is probably biased. Note what p means: *if* the coin
> were fair, results this lopsided would happen about 2% of the time. It does **not**
> mean a 2% chance that the coin is fair.

| | $H_0$ true (no effect) | $H_0$ false (real effect) |
|---|---|---|
| **Reject $H_0$** | Type I error — false positive (rate α) | correct detection (rate = **power**) |
| **Keep $H_0$** | correct | Type II error — missed effect |

> **Watch out:** A p-value is **not** the probability that the null hypothesis is true,
> and "not significant" does **not** mean "no effect" — it may mean too little data. And
> "statistically significant" does not mean "important": with enough data, a 0.01%
> improvement is significant and worthless.

## 8 · A/B Testing

Show version A to one random group and B to another; compare a metric such as conversion
rate. For proportions, the **two-proportion z-test** asks whether the difference is
larger than chance explains:

$$
z = \frac{\hat{p}_B - \hat{p}_A}{\sqrt{\hat{p}(1-\hat{p})\left(\frac{1}{n_A} + \frac{1}{n_B}\right)}}, \qquad \hat{p} = \text{pooled rate}
$$

```python
import math

def two_proportion_test(conv_a, n_a, conv_b, n_b):
    pa, pb = conv_a / n_a, conv_b / n_b
    pooled = (conv_a + conv_b) / (n_a + n_b)
    se = math.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = (pb - pa) / se
    p_two_sided = 1 - math.erf(abs(z) / math.sqrt(2))
    return round(z, 2), round(p_two_sided, 4)

print(two_proportion_test(1000, 20000, 1100, 20000))   # → (2.24, 0.025)
print(two_proportion_test(100, 2000, 110, 2000))       # → (0.71, 0.4784)
```

The same 5.0% → 5.5% lift is significant with 20,000 users per arm (p = 0.025) and
invisible with 2,000 (p = 0.48). **Decide the sample size before the test.** A handy rule
(80% power, α = 0.05): about $16\,p(1-p)/\delta^2$ users per arm to detect an absolute
change δ.

```python
p, delta = 0.05, 0.005
print(round(16 * p * (1 - p) / delta**2))   # → 30400
```

> **Notebook example:** A converts 200 of 4,000 users and B converts 260 of 4,000. Is the
> difference significant?
>
> 1. Rates: $\hat p_A = 200/4000 = 5.0\%$ and $\hat p_B = 260/4000 = 6.5\%$. The
>    difference is 0.015.
> 2. Pooled rate: $\hat p = 460 / 8000 = 0.0575$.
> 3. Standard error: $\sqrt{0.0575 \times 0.9425 \times \left(\frac{1}{4000} + \frac{1}{4000}\right)} = \sqrt{0.05419 \times 0.0005} \approx 0.00521$.
> 4. $z = 0.015 / 0.00521 \approx 2.88$.
> 5. $|z| > 1.96$, so it is significant at 5%. The two-sided p-value is about 0.004.
>
> **Answer:** yes, B's lift is very unlikely to be chance, *provided* the sample size was
> fixed before looking and nobody peeked.

### Three ways A/B tests lie

1. **Peeking.** Checking every day and stopping at the first p < 0.05 inflates the
   false-positive rate far above 5% — you get many chances to be lucky. Fix the sample
   size in advance, or use sequential-testing methods designed for peeking.
2. **Multiple comparisons.** Test 20 metrics and one will be "significant" by chance.
   Pick a primary metric in advance; correct for the rest (Bonferroni: use α / number of
   tests).
3. **Broken randomisation.** Unequal split, users seeing both variants, novelty effects,
   or a bug affecting one arm. Always check that the groups' sizes and pre-experiment
   metrics match (a **sample ratio mismatch** check).

## 9 · Correlation, Causation and Simpson's Paradox

The **correlation coefficient** r (from −1 to 1) measures how well a straight line
describes the relationship between two variables. It measures **association**, not
causation: ice-cream sales and drownings are correlated because both rise in summer (a
**confounder**).

**Simpson's paradox** is the dramatic version: a trend in every subgroup can reverse
when the groups are combined. Real data from a 1986 study of kidney-stone treatments:

```python
data = {  # (successes, patients)
    "A": {"small": (81, 87), "large": (192, 263)},
    "B": {"small": (234, 270), "large": (55, 80)},
}
rate = lambda s, n: round(100 * s / n)
def summary(t):
    s = sum(v[0] for v in data[t].values()); n = sum(v[1] for v in data[t].values())
    return rate(*data[t]["small"]), rate(*data[t]["large"]), rate(s, n)

print(summary("A"), summary("B"))   # → (93, 73, 78) (87, 69, 83)
print("A wins both groups:", data["A"]["small"][0] / data["A"]["small"][1] > data["B"]["small"][0] / data["B"]["small"][1])   # → A wins both groups: True
```

Treatment A succeeds more often for small stones (93% vs 87%) **and** for large stones
(73% vs 69%), yet B looks better overall (83% vs 78%). Why? Doctors gave A mostly to the
hard, large-stone cases. Stone size is a confounder. In engineering, the same thing
happens when a new version is rolled out first to low-traffic regions, or a feature is
used mostly by power users: aggregate numbers can point the wrong way.

> **In practice:** Randomised experiments (A/B tests) are how you get causation:
> randomisation spreads every confounder evenly across the groups, known or unknown.
> Observational data ("users who used feature X spent more") cannot, by itself, tell
> you that X caused the spending.

> **Notebook example:** Find the correlation and the least-squares line for the points
> (1, 2), (2, 4), (3, 5), (4, 4), (5, 5).
>
> 1. Means: $\bar x = 15/5 = 3$ and $\bar y = 20/5 = 4$.
> 2. Deviations: dx = −2, −1, 0, 1, 2 and dy = −2, 0, 1, 0, 1.
> 3. $\sum dx\,dy = 4 + 0 + 0 + 0 + 2 = 6$, $\sum dx^2 = 10$ and $\sum dy^2 = 4 + 0 + 1 + 0 + 1 = 6$.
> 4. $r = \frac{6}{\sqrt{10 \times 6}} = \frac{6}{7.746} \approx 0.77$.
> 5. Slope $= \frac{\sum dx\,dy}{\sum dx^2} = 0.6$, and the intercept is
>    $\bar y - 0.6\,\bar x = 4 - 1.8 = 2.2$.
>
> **Answer:** $r \approx 0.77$ (a strong positive association) and the line
> $y = 0.6x + 2.2$. **Check:** the line passes through the mean point:
> $0.6 \times 3 + 2.2 = 4$. ✓

### Fitting a line: least squares

Linear regression chooses the line minimising the sum of **squared** vertical errors.
Its slope is $r \cdot \frac{s_y}{s_x}$ — the correlation, rescaled to the data's units.
Squared errors make the fit sensitive to outliers (one far point pulls hard), which you
can feel in the lab:

<div class="lab" data-viz="regression"></div>

## 10 · Benchmarking Without Fooling Yourself

Timing code is a statistics problem: every measurement is signal plus noise (CPU
frequency changes, other processes, caches, JIT warm-up, garbage collection).

1. **Warm up**, then **repeat** many times.
2. Report the **median** (or minimum, for pure CPU work) **and the spread**, not one
   number.
3. Compare distributions or confidence intervals, not single runs; a "3% faster" inside
   ±5% noise is nothing.
4. Change **one thing at a time**, on the same machine, interleaving A and B runs so
   drift affects both equally.
5. Measure at **realistic sizes**: constant factors and caches dominate small inputs
   (chapter 06, CS Fundamentals chapter 07).

```python
import timeit, statistics as st
times = timeit.repeat("sorted(xs)", setup="import random; xs = [random.random() for _ in range(10_000)]", number=20, repeat=7)
per_call_ms = [t / 20 * 1000 for t in times]
summary = (round(st.median(per_call_ms), 2), round(min(per_call_ms), 2), round(max(per_call_ms), 2))
print(len(summary))   # → 3
```

(The printed claim only checks the shape: real timings depend on the machine — which is
the point of this section.)

> **Notebook example:** Seven runs each, in ms. Version A: 101, 99, 103, 100, 180, 102,
> 98. Version B: 97, 96, 99, 95, 98, 160, 97. Is B faster?
>
> 1. Sort A: 98, 99, 100, **101**, 102, 103, 180. Its median is 101.
> 2. Sort B: 95, 96, 97, **97**, 98, 99, 160. Its median is 97.
> 3. The means are 783/7 ≈ 111.9 and 742/7 = 106.0. The one slow outlier in each run
>    pulls them up, so ignore them.
> 4. Compare the spreads: the middle runs of A lie between 99 and 103, and those of B
>    between 96 and 99. They barely overlap.
> 5. The difference in medians is $4 / 101 \approx 4\%$, larger than the noise in
>    either version.
>
> **Answer:** B is about 4% faster, and the evidence is the whole distribution shifting,
> not one lucky run. If the ranges overlapped heavily, the honest answer would be "no
> measurable difference".

## Common Mistakes

1. **Reporting the mean of a skewed distribution** as "typical".
2. **Averaging percentiles** across servers or time windows.
3. **Treating non-significance as "no effect"** or significance as "important".
4. **Peeking** at A/B tests and stopping early; testing many metrics without correction.
5. **Assuming normality** for latencies and alert thresholds.
6. **Concluding causation from correlation**, and ignoring confounders (Simpson).
7. **Benchmarking once.**

## Check Yourself

**1.** Your p50 is 20 ms and p99 is 900 ms. What might the histogram look like, and what
would you investigate?

<details>
<summary>Open the answer</summary>

A tight body around 20 ms plus a separate slow cluster or a long tail containing at least
1% of requests — often a bimodal shape (cache misses, GC pauses, retries, a slow
dependency, lock contention). Look at the slow requests specifically (traces, whether
they share a host, route, or time pattern), not at averages.

</details>

**2.** A test with 10,000 users per arm shows p = 0.03 for a 0.1% lift in revenue per
user. Should you ship?

<details>
<summary>Open the answer</summary>

"Significant" only says the lift is probably not zero. Ask whether 0.1% is worth the
cost and risk, what the confidence interval is (it may include near-zero lifts), whether
the test was peeked at, and whether revenue was the pre-registered primary metric.

</details>

**3.** To halve the width of a confidence interval, how much more data do you need?

<details>
<summary>Open the answer</summary>

Four times as much: the width is proportional to $1/\sqrt{n}$.

</details>

**4.** Version 2 has a lower error rate than version 1 overall, but it was rolled out
first to your least-loaded region. What should you check?

<details>
<summary>Open the answer</summary>

Compare within regions (or within load levels). Region is a confounder that could create
a Simpson's-paradox reversal: v2 might be worse in every region and still look better
overall. Better still, randomise which hosts get v2.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Mean vs median vs mode; standard deviation; percentiles; histograms before summaries |
| **Interview-ready** | Tail latency and fan-out; why percentiles do not average; standard error and the CLT; confidence intervals; p-values, type I/II errors and power; A/B test sample size and peeking; correlation vs causation |
| **Going deeper** | t-tests and small samples; multiple-comparison corrections; sequential testing; Simpson's paradox and causal inference; regression assumptions; HdrHistogram/t-digest for streaming percentiles |

## Checklist

- [ ] I use the median and percentiles for latency, the mean for totals.
- [ ] I never average p99s; I merge histograms.
- [ ] I can explain the CLT and why error bars shrink like $1/\sqrt{n}$.
- [ ] I can compute and correctly interpret a 95% confidence interval.
- [ ] I can say what a p-value is and is not.
- [ ] I size A/B tests in advance and do not peek.
- [ ] I look for confounders before believing a causal story.
- [ ] I benchmark with warm-up, repetition and spread.
