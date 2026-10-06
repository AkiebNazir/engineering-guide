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
> mean, median and mode.
>
> **What you need:** the **mean** is the ordinary average: add everything, divide by how
> many there are. The **median** is the middle value once the numbers are sorted; with n
> values (n odd) it sits at position $\frac{n + 1}{2}$. The **mode** is the value that
> appears most often.
>
> **Plan:** sort first (it makes the median and mode easy to see), then find each measure
> in turn.
>
> 1. **Sort the values.** 3, 5, 5, 7, 8, 12, 100.
> 2. **Add them up.** Running total: $3 + 5 = 8$, $+ 5 = 13$, $+ 7 = 20$, $+ 8 = 28$,
>    $+ 12 = 40$, $+ 100 = 140$.
> 3. **Divide by the count.** There are 7 values: $140 / 7 = 20$. The mean is 20 ms.
> 4. **Find the middle position.** $\frac{7 + 1}{2} = 4$, so the median is the 4th value.
> 5. **Read off the median.** Counting along the sorted list, the 4th value is **7** ms.
>    *Why:* three values are below it and three above.
> 6. **Find the mode.** Every value appears once except 5, which appears twice. The mode
>    is **5** ms.
>
> **Answer:** mean 20 ms, median 7 ms, mode 5 ms. Six of the seven requests took 12 ms or
> less, yet the mean is 20: the single 100 ms request dragged it up.
>
> **Check:** `statistics.mean`, `median` and `mode` on the list give 20, 7 and 5. ✓ And
> mean × count should give the total: $20 \times 7 = 140$. ✓

> **Your turn:** Five latencies, in ms: 6, 2, 4, 50, 4. Find the mean, median and mode.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sort the values.** 2, 4, 4, 6, 50.
> 2. **Add them up.** $2 + 4 + 4 + 6 + 50 = 66$.
> 3. **Divide by the count.** $66 / 5 = 13.2$.
> 4. **Find the middle position.** $\frac{5 + 1}{2} = 3$.
> 5. **Read off the median.** The 3rd value is 4.
> 6. **Find the mode.** 4 appears twice, so the mode is 4.
>
> **Answer:** mean 13.2 ms, median 4 ms, mode 4 ms.
>
> </details>

> **Notebook example:** Take the same seven response times and remove the slow one,
> leaving 3, 5, 5, 7, 8, 12. Find the new mean and median, and compare with before
> (mean 20, median 7).
>
> **What you need:** the mean is the sum divided by the count. With an **even** number of
> values there is no single middle one, so the median is the **average of the two middle
> values** (positions $\frac{n}{2}$ and $\frac{n}{2} + 1$).
>
> **Plan:** recompute the mean, find the two middle values, average them, then compare.
>
> 1. **Add them up.** $3 + 5 + 5 + 7 + 8 + 12 = 40$ (the old total 140, minus 100).
> 2. **Divide by the new count.** $40 / 6 \approx 6.7$.
> 3. **Find the two middle positions.** With 6 values: positions 3 and 4.
> 4. **Read them off.** The 3rd value is 5 and the 4th is 7.
> 5. **Average them.** $(5 + 7) / 2 = 12 / 2 = 6$. The median is 6.
> 6. **Compare.** The mean fell from 20 to 6.7 (to a third); the median moved from 7 to 6
>    (by just 1).
>    *Why:* the mean uses the size of every value, so one huge value moves it a lot; the
>    median only cares about the order, so the 100 counted as "one value on the big side",
>    no matter how big.
>
> **Answer:** new mean about 6.7 ms, new median 6 ms. One slow value tripled the mean but
> moved the median by just 1. That is why "typical" means median.
>
> **Check:** `statistics.median([3, 5, 5, 7, 8, 12])` returns 6.0. ✓

> **Your turn:** Remove the 50 from 2, 4, 4, 6, 50. Find the new mean and median.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Add them up.** $2 + 4 + 4 + 6 = 16$.
> 2. **Divide by the new count.** $16 / 4 = 4$.
> 3. **Find the two middle positions.** Positions 2 and 3.
> 4. **Read them off.** Both are 4.
> 5. **Average them.** $(4 + 4) / 2 = 4$.
> 6. **Compare.** The mean fell from 13.2 to 4; the median stayed at 4.
>
> **Answer:** mean 4 ms, median 4 ms.
>
> </details>

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

> **Notebook example:** For the data 2, 4, 4, 4, 5, 5, 7, 9, find the (population)
> variance and standard deviation.
>
> **What you need:** a **deviation** is how far a value is from the mean (value − mean;
> negative means below). The **variance** is the average of the **squared** deviations,
> and the **standard deviation** σ is its square root. Squaring stops the minus signs
> cancelling the plus signs; the square root at the end gets back to the original units.
> "Population" means we divide by n, treating these values as everything there is.
>
> **Plan:** mean, then deviations, then square, add, divide by n, and take the root.
>
> 1. **Find the mean.** $2 + 4 + 4 + 4 + 5 + 5 + 7 + 9 = 40$, and $40 / 8 = 5$.
> 2. **Subtract the mean from each value.** −3, −1, −1, −1, 0, 0, 2, 4.
>    *Why:* these deviations always add to 0 (here $-6 + 6 = 0$), which is why we cannot
>    just average them.
> 3. **Square each deviation.** 9, 1, 1, 1, 0, 0, 4, 16.
> 4. **Add the squares.** $9 + 1 + 1 + 1 + 0 + 0 + 4 + 16 = 32$.
> 5. **Divide by n.** $32 / 8 = 4$. This is the variance.
> 6. **Take the square root.** $\sigma = \sqrt 4 = 2$.
>
> **Answer:** variance 4, standard deviation σ = 2: values typically sit about 2 away
> from the mean of 5.
>
> **Check:** `statistics.pstdev([2, 4, 4, 4, 5, 5, 7, 9])` prints 2.0, as in the code
> above. ✓

> **Your turn:** Find the population variance and standard deviation of 2, 4, 5, 6, 8.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the mean.** $2 + 4 + 5 + 6 + 8 = 25$, and $25 / 5 = 5$.
> 2. **Subtract the mean from each value.** −3, −1, 0, 1, 3.
> 3. **Square each deviation.** 9, 1, 0, 1, 9.
> 4. **Add the squares.** $9 + 1 + 0 + 1 + 9 = 20$.
> 5. **Divide by n.** $20 / 5 = 4$.
> 6. **Take the square root.** $\sqrt 4 = 2$.
>
> **Answer:** variance 4, σ = 2.
>
> </details>

> **Notebook example:** Treat 2, 4, 4, 4, 5, 5, 7, 9 as a **sample** from a bigger
> population. Find the sample variance and standard deviation s. (Its squared deviations
> add up to 32, as in the last example.)
>
> **What you need:** for a sample, divide the sum of squared deviations by $n - 1$
> instead of n (**Bessel's correction**). The mean was worked out from these very
> values, so they sit a little closer to it than to the true population mean; dividing
> by a slightly smaller number makes up for that.
>
> **Plan:** reuse the sum of squares, divide by $n - 1$, take the root.
>
> 1. **Reuse the sum of squared deviations.** 32.
> 2. **Find n − 1.** There are 8 values, so $8 - 1 = 7$.
> 3. **Divide.** $32 / 7 \approx 4.57$. This is the sample variance.
> 4. **Take the square root.** $s = \sqrt{4.57} \approx 2.14$.
>    *Why:* $2.1^2 = 4.41$ and $2.2^2 = 4.84$, so the root is a bit above 2.1.
>
> **Answer:** sample variance about 4.57, s ≈ 2.14, slightly bigger than the population
> σ = 2. The difference matters for small samples and fades as n grows.
>
> **Check:** `statistics.stdev` (the sample version) prints 2.1381 in the code above. ✓

> **Your turn:** Treat 2, 4, 5, 6, 8 as a sample (squared deviations add to 20). Find
> the sample variance and s.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Reuse the sum of squared deviations.** 20.
> 2. **Find n − 1.** $5 - 1 = 4$.
> 3. **Divide.** $20 / 4 = 5$.
> 4. **Take the square root.** $\sqrt 5 \approx 2.24$.
>
> **Answer:** sample variance 5, s ≈ 2.24.
>
> </details>

> **Notebook example:** In the data 2, 4, 4, 4, 5, 5, 7, 9 (mean 5, σ = 2), how unusual
> is the value 9? Find its z-score.
>
> **What you need:** a **z-score** says how many standard deviations a value is from the
> mean: $z = \frac{x - \bar{x}}{\sigma}$, where x is the value, $\bar{x}$ the mean and σ
> the standard deviation. Positive means above the mean, negative below. It puts values
> from different datasets on one common ruler.
>
> **Plan:** find the distance from the mean, then measure it in standard deviations.
>
> 1. **Subtract the mean.** $9 - 5 = 4$.
> 2. **Divide by σ.** $4 / 2 = 2$.
>    *Why:* σ is the "typical distance", so this counts how many typical distances away 9
>    is.
>
> **Answer:** z = 2: the value 9 is two standard deviations above the mean, the most
> extreme value in this small dataset.
>
> **Check:** go the other way: mean + z × σ $= 5 + 2 \times 2 = 9$. ✓ The lowest value,
> 2, has $z = (2 - 5)/2 = -1.5$: below the mean, and less extreme.

> **Your turn:** In 2, 4, 5, 6, 8 (mean 5, σ = 2), find the z-score of 8.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Subtract the mean.** $8 - 5 = 3$.
> 2. **Divide by σ.** $3 / 2 = 1.5$.
>
> **Answer:** z = 1.5, one and a half standard deviations above the mean.
>
> </details>

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
> Find p50 and p90 with the nearest-rank method.
>
> **What you need:** the **p-th percentile** (p90 is the 90th) is the value that p% of
> the data is at or below. The **nearest-rank** method: sort the data, compute
> $\frac{p}{100} \times n$, **round up** to a whole number (that is what the brackets in
> $\lceil \cdot \rceil$ mean), and take the value at that position.
>
> **Plan:** sort, then for each percentile compute the position and read off the value.
>
> 1. **Sort the values.** They are already sorted: 10, 11, 12, 12, 13, 14, 15, 20, 45,
>    300 (n = 10).
> 2. **Find the p50 position.** $0.5 \times 10 = 5$. It is already whole, so position 5.
> 3. **Read off p50.** The 5th value is **13 ms**.
> 4. **Find the p90 position.** $0.9 \times 10 = 9$, so position 9.
> 5. **Read off p90.** The 9th value is **45 ms**.
>    *Why:* 9 of the 10 values (90%) are 45 ms or less.
>
> **Answer:** p50 = 13 ms and p90 = 45 ms. Half the requests take 13 ms or less, but 1 in
> 10 takes 45 ms or more, and the very worst took 300 ms.
>
> **Check:** count by hand: values ≤ 13 are 10, 11, 12, 12, 13, five of ten = 50% ✓;
> values ≤ 45 are all but the 300, nine of ten = 90% ✓.

> **Your turn:** Eight latencies, in ms: 12, 30, 9, 15, 11, 10, 14, 200. Find p50 and p90
> with the nearest-rank method.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sort the values.** 9, 10, 11, 12, 14, 15, 30, 200 (n = 8).
> 2. **Find the p50 position.** $0.5 \times 8 = 4$, so position 4.
> 3. **Read off p50.** The 4th value is 12 ms.
> 4. **Find the p90 position.** $0.9 \times 8 = 7.2$, rounded **up** to 8.
> 5. **Read off p90.** The 8th value is 200 ms.
>
> **Answer:** p50 = 12 ms, p90 = 200 ms.
>
> </details>

> **Notebook example:** A page calls 10 backends in parallel and must wait for all of
> them. Each backend is slower than its own p99 on 1% of calls, independently. What is
> the chance that a page load hits at least one backend's p99 tail?
>
> **What you need:** a backend's p99 is the time that 99% of its calls beat, so one call
> is "fast" (under p99) with probability 0.99. For **independent** calls you multiply
> chances. "At least one slow" is easiest through the **complement**:
> $P(\text{at least one slow}) = 1 - P(\text{all fast})$.
>
> **Plan:** find P(all 10 fast) by multiplying, then subtract from 1.
>
> 1. **Chance one backend is fast.** 0.99.
> 2. **Chance all 10 are fast.** Multiply ten 0.99s: $0.99^{10}$. Step by step:
>    0.99, 0.9801, 0.9703, 0.9606, 0.9510, 0.9415, 0.9321, 0.9227, 0.9135, 0.9044.
>    *Why:* each backend must be fast, and independent chances multiply.
> 3. **Take the complement.** $1 - 0.9044 = 0.0956$, about 9.6%.
>
> **Answer:** about 1 page load in 10 sees a p99-slow backend, even though each backend
> is slow only 1 time in 100. With 100 backends it is $1 - 0.99^{100} \approx 63\%$: the
> tail becomes the norm.
>
> **Check:** a rough shortcut for small chances: 10 backends × 1% ≈ 10%, a slight
> overestimate of 9.6%. ✓ In Python, `1 - 0.99**10` gives 0.0956. ✓

> **Your turn:** A page waits for 5 backends, each slow (past its p99) on 1% of calls,
> independently. What is the chance at least one is slow?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Chance one backend is fast.** 0.99.
> 2. **Chance all 5 are fast.** $0.99^5$: 0.99, 0.9801, 0.9703, 0.9606, 0.9510.
> 3. **Take the complement.** $1 - 0.9510 = 0.049$.
>
> **Answer:** about 4.9%, roughly 1 page in 20.
>
> </details>

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
> σ = 20 s. How often does it finish between 160 s and 240 s?
>
> **What you need:** a **z-score** turns a value into "how many standard deviations from
> the mean": $z = \frac{x - \mu}{\sigma}$, where μ is the mean and σ the standard
> deviation. For a normal (bell-shaped) distribution the table above says how much of the
> data lies within ±1, ±2 and ±3 standard deviations: 68.3%, 95.4%, 99.7%.
>
> **Plan:** turn both ends of the range into z-scores, then look the range up in the
> table.
>
> 1. **Find the z-score of 160.** $160 - 200 = -40$, and $-40 / 20 = -2$.
> 2. **Find the z-score of 240.** $240 - 200 = 40$, and $40 / 20 = 2$.
>    *Why:* the range is "from 2σ below the mean to 2σ above it", which is exactly a row
>    of the table.
> 3. **Look it up.** μ ± 2σ holds **95.4%** of the data.
>
> **Answer:** about 95% of runs finish between 160 s and 240 s, so about 1 run in 20
> falls outside that window. Use this only once the histogram looks like a bell.
>
> **Check:** the code above computes `within(2)` as 95.4. ✓ Sanity: the ±2σ window
> should be wider than the ±1σ window (68.3%) and narrower than ±3σ (99.7%). ✓

> **Your turn:** A request's time is roughly normal with mean 50 ms and σ = 5 ms. How
> often is it between 45 ms and 55 ms?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the z-score of 45.** $(45 - 50) / 5 = -5 / 5 = -1$.
> 2. **Find the z-score of 55.** $(55 - 50) / 5 = 5 / 5 = 1$.
> 3. **Look it up.** μ ± 1σ holds 68.3%.
>
> **Answer:** about 68% of requests.
>
> </details>

> **Notebook example:** The same job (mean 200 s, σ = 20 s, roughly normal). How often
> does it take **more than** 260 s?
>
> **What you need:** the z-score $z = \frac{x - \mu}{\sigma}$ and the table above. The
> table gives the share **inside** a window; the share **outside** is 100% minus that.
> A normal curve is symmetric, so the outside share splits equally between the low tail
> and the high tail.
>
> **Plan:** find z, take the outside share of that window, then halve it to keep only
> the slow tail.
>
> 1. **Find the z-score of 260.** $260 - 200 = 60$, and $60 / 20 = 3$.
> 2. **Find the share inside ±3σ.** The table says 99.7% (more precisely 99.73%).
> 3. **Find the share outside.** $100\% - 99.73\% = 0.27\%$.
> 4. **Keep only the slow side.** $0.27\% / 2 = 0.135\%$.
>    *Why:* half of the outside runs are unusually **fast** (under 140 s); we only want
>    the slow half.
> 5. **Turn it into "1 in N".** $1 / 0.00135 \approx 740$.
>
> **Answer:** about 0.135% of runs, roughly 1 run in 740.
>
> **Check:** in Python, `(1 - math.erf(3 / math.sqrt(2))) / 2` gives 0.00135. ✓

> **Your turn:** The request from before (mean 50 ms, σ = 5 ms). How often does it take
> more than 60 ms?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the z-score of 60.** $(60 - 50) / 5 = 10 / 5 = 2$.
> 2. **Find the share inside ±2σ.** 95.4%.
> 3. **Find the share outside.** $100\% - 95.4\% = 4.6\%$.
> 4. **Keep only the slow side.** $4.6\% / 2 = 2.3\%$.
> 5. **Turn it into "1 in N".** $1 / 0.023 \approx 44$.
>
> **Answer:** about 2.3%, roughly 1 request in 44.
>
> </details>

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
> the spread of the **average** of 16 requests, and where do most such averages fall?
>
> **What you need:** the **standard error** is the standard deviation of an average:
> $\text{SE} = \frac{\sigma}{\sqrt n}$, where σ is the spread of one measurement and n is
> how many you average. The **central limit theorem (CLT)** says that average is roughly
> normal (bell-shaped), so about 95% of averages land within 2 standard errors of the
> true mean.
>
> **Plan:** compute √n, divide σ by it, then go 2 standard errors either side of 100.
>
> 1. **Take the square root of n.** $\sqrt{16} = 4$.
> 2. **Divide σ by it.** $40 / 4 = 10$. The standard error is 10 ms.
>    *Why:* in an average, fast and slow requests partly cancel out, so the average
>    wobbles less than single requests.
> 3. **Double the standard error.** $2 \times 10 = 20$.
> 4. **Go that far either side of the mean.** $100 - 20 = 80$ and $100 + 20 = 120$.
>
> **Answer:** the average of 16 requests has a spread of 10 ms (versus 40 ms for one
> request), and about 95% of such averages fall between 80 and 120 ms.
>
> **Check:** variances of independent values add (chapter 10): 16 requests have total
> variance $16 \times 40^2 = 25{,}600$, so the total has σ = 160; dividing the total by
> 16 to get the average divides σ by 16 too: $160 / 16 = 10$. ✓

> **Your turn:** One measurement has mean 50 and σ = 30. What is the standard error of the
> average of 9 measurements, and where do about 95% of such averages fall?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Take the square root of n.** $\sqrt 9 = 3$.
> 2. **Divide σ by it.** $30 / 3 = 10$.
> 3. **Double the standard error.** $2 \times 10 = 20$.
> 4. **Go that far either side of the mean.** $50 - 20 = 30$ and $50 + 20 = 70$.
>
> **Answer:** standard error 10; about 95% of averages fall between 30 and 70.
>
> </details>

> **Notebook example:** With the same requests (σ = 40 ms), how many must you average to
> get the standard error down to 5 ms?
>
> **What you need:** $\text{SE} = \frac{\sigma}{\sqrt n}$. Here you know SE and σ and
> want n, so solve the equation backwards.
>
> **Plan:** set up $40 / \sqrt n = 5$, solve for √n, then square.
>
> 1. **Write the equation.** $\frac{40}{\sqrt n} = 5$.
> 2. **Solve for √n.** Swap √n and 5: $\sqrt n = \frac{40}{5} = 8$.
>    *Why:* if 40 split into √n parts gives 5, then √n must be 40 split into parts of 5.
> 3. **Square both sides.** $n = 8^2 = 64$.
>
> **Answer:** 64 requests. Going from 16 to 64 requests (4 times the data) only halved the
> error, from 10 ms to 5 ms. Precision is expensive.
>
> **Check:** put it back: $40 / \sqrt{64} = 40 / 8 = 5$. ✓

> **Your turn:** With σ = 30, how many measurements give a standard error of 3?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the equation.** $\frac{30}{\sqrt n} = 3$.
> 2. **Solve for √n.** $\sqrt n = 30 / 3 = 10$.
> 3. **Square both sides.** $n = 10^2 = 100$.
>
> **Answer:** 100 measurements.
>
> </details>

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
> **What you need:** the **null hypothesis** $H_0$ is the boring explanation: "the coin
> is fair". The **p-value** is the chance, **if $H_0$ were true**, of a result at least as
> extreme as the one you saw. **Two-sided** means "lopsided in either direction" counts
> (lots of heads **or** lots of tails), since we had no reason to suspect one side. If
> p is below the threshold α (here 0.05 = 5%), we reject $H_0$. For a fair coin every
> sequence of 10 flips is equally likely, so chances come from **counting sequences**;
> $\binom{n}{k}$ counts the sequences with exactly k heads (chapter 05).
>
> **Plan:** count all possible sequences, count the ones at least as lopsided as 9 heads
> (both ways), divide, and compare with 5%.
>
> 1. **Count all sequences.** Each flip has 2 outcomes, so $2^{10} = 1024$ sequences.
> 2. **Count sequences with exactly 9 heads.** The one tail can be in any of 10 places:
>    $\binom{10}{9} = 10$.
> 3. **Count sequences with 10 heads.** Just 1 (all heads).
>    *Why:* "at least as extreme as 9 heads" includes the even more extreme 10 heads.
> 4. **Add the heads side.** $10 + 1 = 11$ sequences.
> 5. **Add the tails side.** By symmetry, 9 or 10 **tails** is another 11 sequences, so
>    $11 + 11 = 22$.
> 6. **Divide.** $22 / 1024 \approx 0.0215$, about 2.15%. That is the p-value.
> 7. **Compare with α.** $2.15\% < 5\%$, so reject $H_0$.
>
> **Answer:** p ≈ 0.021, so the coin is probably biased. Note what p means: *if* the coin
> were fair, results this lopsided would happen about 2% of the time. It does **not**
> mean a 2% chance that the coin is fair.
>
> **Check:** list the 11 heads-side sequences in Python with
> `sum(1 for s in itertools.product('HT', repeat=10) if s.count('H') >= 9)`: it prints
> 11. ✓ (The one-sided p-value, heads only, is $11 / 1024 \approx 1.07\%$.)

> **Your turn:** A coin lands heads 5 times in 5 flips. Is it fair, at α = 0.05
> (two-sided)?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Count all sequences.** $2^5 = 32$.
> 2. **Count sequences with 5 heads.** Just 1.
> 3. **Add the tails side.** 5 tails is 1 more, so 2 in total.
> 4. **Divide.** $2 / 32 = 0.0625$, that is 6.25%.
> 5. **Compare with α.** $6.25\% > 5\%$, so we **cannot** reject $H_0$.
>
> **Answer:** p ≈ 0.06: five heads in a row is not enough evidence. Not significant here
> means "too little data", not "proved fair".
>
> </details>

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
> difference significant (two-sided, at 5%)?
>
> **What you need:** the **two-proportion z-test** asks "is the gap between the two
> conversion rates bigger than random noise would usually make it?". $\hat p_A$ and
> $\hat p_B$ (read "p-hat") are the rates measured in each group. The **pooled rate**
> $\hat p$ (no letter) is the overall rate with both groups lumped together, our best
> guess if A and B are really the same.
> The **standard error** (SE) is the typical size of the gap from noise alone:
> $\text{SE} = \sqrt{\hat p(1 - \hat p)\left(\frac{1}{n_A} + \frac{1}{n_B}\right)}$. Then
> $z = \frac{\text{gap}}{\text{SE}}$ counts how many "noise sizes" the gap is. If
> $|z| > 1.96$, the gap is significant at 5%.
>
> **Plan:** find both rates and the gap, then the pooled rate, then SE piece by piece,
> then z, then compare with 1.96.
>
> 1. **Find A's rate.** $\hat p_A = 200 / 4000 = 0.05$ (5.0%).
> 2. **Find B's rate.** $\hat p_B = 260 / 4000 = 0.065$ (6.5%).
> 3. **Find the gap.** $0.065 - 0.05 = 0.015$.
> 4. **Find the pooled rate.** All conversions over all users:
>    $\frac{200 + 260}{4000 + 4000} = \frac{460}{8000} = 0.0575$.
>    *Why:* if B changed nothing, the best estimate of the one shared rate uses everyone.
> 5. **Find one minus it.** $1 - 0.0575 = 0.9425$.
> 6. **Multiply them.** $0.0575 \times 0.9425 \approx 0.05419$.
> 7. **Add the group-size parts.** $\frac{1}{4000} + \frac{1}{4000} = \frac{2}{4000} = 0.0005$.
>    *Why:* bigger groups mean less noise, which is why n sits underneath.
> 8. **Multiply.** $0.05419 \times 0.0005 \approx 0.0000271$.
> 9. **Take the square root.** $\text{SE} = \sqrt{0.0000271} \approx 0.00521$.
> 10. **Divide the gap by SE.** $z = 0.015 / 0.00521 \approx 2.88$.
> 11. **Compare with 1.96.** $2.88 > 1.96$, so the gap is significant at 5%.
>
> **Answer:** yes: the gap is about 2.9 times the size noise would usually produce (a
> two-sided p-value of about 0.004). B's lift is very unlikely to be chance, *provided*
> the sample size was fixed before looking and nobody peeked.
>
> **Check:** `two_proportion_test(200, 4000, 260, 4000)` from the code above returns
> `(2.88, 0.004)`. ✓

> **Your turn:** A converts 50 of 1,000 users and B converts 60 of 1,000. Is the
> difference significant at 5%?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the two rates.** $50 / 1000 = 0.05$ and $60 / 1000 = 0.06$.
> 2. **Find the gap.** $0.06 - 0.05 = 0.01$.
> 3. **Find the pooled rate.** $110 / 2000 = 0.055$.
> 4. **Multiply it by one minus it.** $0.055 \times 0.945 \approx 0.0520$.
> 5. **Add the group-size parts.** $\frac{1}{1000} + \frac{1}{1000} = 0.002$.
> 6. **Multiply and take the square root.** $0.0520 \times 0.002 = 0.000104$, and
>    $\sqrt{0.000104} \approx 0.0102$.
> 7. **Divide the gap by SE.** $z = 0.01 / 0.0102 \approx 0.98$.
> 8. **Compare with 1.96.** $0.98 < 1.96$: not significant.
>
> **Answer:** no. A 1-point gap with only 1,000 users each is well within normal noise;
> you would need far more users to tell.
>
> </details>

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

> **Notebook example:** Find the correlation r for the points (1, 2), (2, 4), (3, 5),
> (4, 4), (5, 5).
>
> **What you need:** write dx for each point's distance from the mean of the x's
> ($x - \bar x$) and dy for its distance from the mean of the y's ($y - \bar y$). The
> **correlation** is
> $r = \frac{\sum dx\,dy}{\sqrt{\sum dx^2 \cdot \sum dy^2}}$, where Σ means "add up over
> all the points". The top is positive when points that are right of centre also tend to
> be above centre. The bottom rescales so r always lands between −1 (perfect downhill
> line) and +1 (perfect uphill line); 0 means no straight-line pattern.
>
> **Plan:** find the means, the dx's and dy's, three sums, then divide.
>
> 1. **Find the mean of x.** $1 + 2 + 3 + 4 + 5 = 15$, and $15 / 5 = 3$.
> 2. **Find the mean of y.** $2 + 4 + 5 + 4 + 5 = 20$, and $20 / 5 = 4$.
> 3. **Find each dx.** Subtract 3 from each x: −2, −1, 0, 1, 2.
> 4. **Find each dy.** Subtract 4 from each y: −2, 0, 1, 0, 1.
> 5. **Multiply dx by dy for each point, and add.** $(-2)(-2) = 4$, $(-1)(0) = 0$,
>    $0 \cdot 1 = 0$, $1 \cdot 0 = 0$, $2 \cdot 1 = 2$. Sum: $4 + 0 + 0 + 0 + 2 = 6$.
>    *Why:* a positive product means that point is on the same side of both means, which
>    is what an uphill trend looks like.
> 6. **Square each dx and add.** $4 + 1 + 0 + 1 + 4 = 10$.
> 7. **Square each dy and add.** $4 + 0 + 1 + 0 + 1 = 6$.
> 8. **Build the bottom.** $10 \times 6 = 60$, and $\sqrt{60} \approx 7.746$.
> 9. **Divide.** $r = 6 / 7.746 \approx 0.77$.
>
> **Answer:** $r \approx 0.77$: a strong positive association (bigger x tends to come with
> bigger y), though not a perfect line. It says nothing about whether x **causes** y.
>
> **Check:** `statistics.correlation([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])` gives 0.7746… ✓
> And r is between −1 and 1, as it must be. ✓

> **Your turn:** Find r for the points (1, 1), (2, 3), (3, 2).
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the mean of x.** $6 / 3 = 2$.
> 2. **Find the mean of y.** $6 / 3 = 2$.
> 3. **Find each dx.** −1, 0, 1.
> 4. **Find each dy.** −1, 1, 0.
> 5. **Multiply dx by dy for each point, and add.** $1 + 0 + 0 = 1$.
> 6. **Square each dx and add.** $1 + 0 + 1 = 2$.
> 7. **Square each dy and add.** $1 + 1 + 0 = 2$.
> 8. **Build the bottom.** $\sqrt{2 \times 2} = \sqrt 4 = 2$.
> 9. **Divide.** $r = 1 / 2 = 0.5$.
>
> **Answer:** r = 0.5, a moderate positive association.
>
> </details>

> **Notebook example:** Find the least-squares line $y = mx + c$ through the same points
> (1, 2), (2, 4), (3, 5), (4, 4), (5, 5).
>
> **What you need:** the **least-squares line** is the straight line that makes the sum
> of squared vertical misses as small as possible. Its slope (steepness) is
> $m = \frac{\sum dx\,dy}{\sum dx^2}$, and it always passes through the mean point
> $(\bar x, \bar y)$, which gives the intercept (where it crosses x = 0):
> $c = \bar y - m\,\bar x$. From the last example: $\bar x = 3$, $\bar y = 4$,
> $\sum dx\,dy = 6$, $\sum dx^2 = 10$.
>
> **Plan:** reuse the sums to get the slope, then use the mean point to get the
> intercept.
>
> 1. **Divide for the slope.** $m = 6 / 10 = 0.6$.
>    *Why:* on average, one step right goes 0.6 of a step up.
> 2. **Multiply the slope by the mean x.** $0.6 \times 3 = 1.8$.
> 3. **Subtract from the mean y.** $c = 4 - 1.8 = 2.2$.
>    *Why:* the line must pass through (3, 4), so at x = 3 it must reach 4; starting at
>    2.2 and climbing 1.8 does that.
> 4. **Write the line.** $y = 0.6x + 2.2$.
>
> **Answer:** $y = 0.6x + 2.2$. For example, it predicts $0.6 \times 6 + 2.2 = 5.8$ at
> x = 6.
>
> **Check:** the line passes through the mean point: $0.6 \times 3 + 2.2 = 1.8 + 2.2 = 4$. ✓
> `statistics.linear_regression([1, 2, 3, 4, 5], [2, 4, 5, 4, 5])` gives slope 0.6 and
> intercept 2.2. ✓

> **Your turn:** Find the least-squares line through (1, 1), (2, 3), (3, 2). (From your
> last answer: $\bar x = 2$, $\bar y = 2$, $\sum dx\,dy = 1$, $\sum dx^2 = 2$.)
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Divide for the slope.** $m = 1 / 2 = 0.5$.
> 2. **Multiply the slope by the mean x.** $0.5 \times 2 = 1$.
> 3. **Subtract from the mean y.** $c = 2 - 1 = 1$.
> 4. **Write the line.** $y = 0.5x + 1$.
>
> **Answer:** $y = 0.5x + 1$ (check: at x = 2 it gives 2, the mean y).
>
> </details>

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
> 98. Version B: 97, 96, 99, 95, 98, 160, 97. Find the median and mean of each version.
>
> **What you need:** the **median** is the middle value after sorting (for 7 values, the
> 4th); the **mean** is the sum divided by the count. An **outlier** is a value far from
> all the others (here a run disturbed by something like a GC pause). Outliers drag the
> mean but barely touch the median.
>
> **Plan:** sort each version and read off the median, then compute both means and
> compare.
>
> 1. **Sort A.** 98, 99, 100, 101, 102, 103, 180.
> 2. **Read A's median.** The 4th value: **101** ms.
> 3. **Sort B.** 95, 96, 97, 97, 98, 99, 160.
> 4. **Read B's median.** The 4th value: **97** ms.
> 5. **Find A's mean.** The sum is 783, and $783 / 7 \approx 111.9$.
> 6. **Find B's mean.** The sum is 742, and $742 / 7 = 106.0$.
>    *Why:* both means sit above **every** normal run, because the 180 and 160 outliers
>    pull them up. They describe no actual run.
>
> **Answer:** medians 101 ms (A) and 97 ms (B); means about 111.9 ms and 106.0 ms. Use the
> medians to compare: they ignore the single disturbed run in each version.
>
> **Check:** mean × count = total: $106 \times 7 = 742$. ✓ `statistics.median` on each
> list gives 101 and 97. ✓

> **Your turn:** Five runs each, in ms. A: 52, 50, 51, 90, 49. B: 47, 48, 46, 70, 49.
> Find the median and mean of each.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Sort A.** 49, 50, 51, 52, 90.
> 2. **Read A's median.** The 3rd value: 51 ms.
> 3. **Sort B.** 46, 47, 48, 49, 70.
> 4. **Read B's median.** The 3rd value: 48 ms.
> 5. **Find A's mean.** $292 / 5 = 58.4$.
> 6. **Find B's mean.** $260 / 5 = 52$.
>
> **Answer:** medians 51 and 48 ms; means 58.4 and 52 ms (both pulled up by an outlier).
>
> </details>

> **Notebook example:** Using the same runs, is B (median 97 ms) **really** faster than A
> (median 101 ms), or is the gap just noise?
>
> **What you need:** a gap only means something if it is bigger than the run-to-run
> **noise** (the natural wobble between repeated runs). A simple, honest test for small
> samples: drop the single fastest and slowest run of each version, look at the range
> of the **middle** runs, and see whether the two ranges overlap. Little or no overlap
> means a real shift.
>
> **Plan:** find the middle range of each version, compare them, then express the gap as
> a percentage.
>
> 1. **Find A's middle runs.** Sorted A is 98, 99, 100, 101, 102, 103, 180. Drop 98 and
>    180: the middle runs are 99 to 103.
> 2. **Find B's middle runs.** Sorted B is 95, 96, 97, 97, 98, 99, 160. Drop 95 and 160:
>    the middle runs are 96 to 99.
> 3. **Compare the ranges.** A's middle is 99–103 and B's is 96–99; they touch only at
>    99.
>    *Why:* almost every normal run of B beats almost every normal run of A, so the gap is
>    not one lucky run.
> 4. **Find the gap.** $101 - 97 = 4$ ms.
> 5. **Turn it into a percentage of A.** $4 / 101 \approx 0.04$, about 4%.
>
> **Answer:** yes, B is about 4% faster, and the evidence is the whole distribution
> shifting, not one lucky run. If the ranges overlapped heavily, the honest answer would
> be "no measurable difference".
>
> **Check:** each version's middle runs vary by only about 3–4 ms, while the medians
> differ by 4 ms, so the gap is as big as the whole noise band. ✓

> **Your turn:** For A: 49, 50, 51, 52, 90 (median 51) and B: 46, 47, 48, 49, 70 (median
> 48), is B really faster?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find A's middle runs.** Drop 49 and 90: 50 to 52.
> 2. **Find B's middle runs.** Drop 46 and 70: 47 to 49.
> 3. **Compare the ranges.** 50–52 and 47–49 do not overlap at all.
> 4. **Find the gap.** $51 - 48 = 3$ ms.
> 5. **Turn it into a percentage of A.** $3 / 51 \approx 0.059$, about 6%.
>
> **Answer:** yes, B is about 6% faster, with no overlap between the middle runs.
>
> </details>

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
