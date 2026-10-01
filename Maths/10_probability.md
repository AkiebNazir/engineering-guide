# Probability — Reasoning About Uncertainty and Randomness

Software meets chance everywhere: hash collisions, disk failures, network retries,
random pivots, load balancing, cache hits, A/B tests, spam filters, and every machine
learning model. Probability is the maths of reasoning about outcomes you cannot predict
individually but can describe collectively. This chapter starts from counting equally
likely outcomes and builds up to conditional probability and Bayes' rule, random
variables and expectation (with the surprisingly powerful linearity of expectation),
the distributions engineers meet, and the classic results behind hashing, randomized
algorithms and Bloom filters.

**Where this fits:** Part 3 · Continuous maths, chapter 10 of 15. **Builds on:** [05 Counting, permutations and combinations](05_counting_and_combinatorics.md) (counting outcomes). **Used again in:** 11, 13, 15. **Next in order:** [11 Statistics](11_statistics.md).

## Where You Will Use This

| Where | Probability question |
|---|---|
| Hash tables, IDs, sharding | When do collisions become likely? (birthday bound) |
| Replication and availability | If each replica fails with probability p, how often do all fail? |
| Randomized algorithms | Why is random-pivot quicksort O(n log n) on average? |
| Bloom filters, sketches | What is the false-positive rate for m bits and k hashes? |
| Monitoring and security alerts | Given an alert fired, how likely is a real incident? (Bayes) |
| Retries, backoff, polling | How many attempts on average until success? (geometric) |
| Load testing and simulation | Estimating what you cannot compute (Monte Carlo) |

## Foundations — Outcomes, Events, Probabilities

An **experiment** has uncertain outcomes (roll a die, send a packet). The **sample
space** Ω is the set of all possible outcomes. An **event** is a subset of Ω — a set of
outcomes you care about ("the roll is even" = {2, 4, 6}). A **probability** assigns
each event a number from 0 (impossible) to 1 (certain).

> **Key idea:** When all outcomes are **equally likely**,
> $$P(A) = \frac{\text{number of outcomes in } A}{\text{number of outcomes in } \Omega}$$
> — probability is counting (chapter 05) followed by one division.

> **Intuition:** Read "P(A) = 0.3" as "if you repeated the experiment many times, A
> would happen about 30% of the time". This **frequency** reading is what simulations
> measure, and the **law of large numbers** (§9) guarantees the frequency converges to
> the probability.

```python
from itertools import product
from fractions import Fraction

omega = list(product(range(1, 7), repeat=2))          # two dice: 36 equally likely outcomes
sum_is_7 = [o for o in omega if sum(o) == 7]
print(len(omega), len(sum_is_7), Fraction(len(sum_is_7), len(omega)))   # → 36 6 1/6
```

Using `Fraction` keeps answers exact — a good habit when checking probability by
enumeration.

## 1 · The Basic Rules

| Rule | Formula | When |
|---|---|---|
| Complement | $P(\text{not } A) = 1 - P(A)$ | "at least one" is almost always easier as 1 − "none" |
| Addition | $P(A \cup B) = P(A) + P(B) - P(A \cap B)$ | inclusion–exclusion (chapter 04) |
| Multiplication (independent) | $P(A \cap B) = P(A)\,P(B)$ | only when A and B are **independent** |

> **Worked example:** A request is served by 3 replicas; each is down independently
> with probability 1%. P(all three down) = $0.01^3 = 10^{-6}$. P(at least one down) =
> $1 - 0.99^3 \approx 2.97\%$ — the complement rule.

```python
p = 0.01
print(round(p**3, 12), round(1 - (1 - p)**3, 6))   # → 1e-06 0.029701
```

> **Watch out:** The $10^{-6}$ relies on **independence**. Replicas in the same rack,
> on the same software version, or behind the same config push fail **together**; then
> P(all down) can be close to P(one down). Most large outages are correlated failures.
> Independence is an assumption to justify, never a default.

## 2 · Conditional Probability and Independence

"Given that B happened, how likely is A?" Knowing B shrinks the sample space to B:

$$
P(A \mid B) = \frac{P(A \cap B)}{P(B)}
$$

> **Worked example:** Roll two dice. P(sum is 8) = 5/36. But given the first die shows
> 6, only (6, 2) works out of 6 equally likely second rolls: P(sum 8 | first is 6) =
> 1/6. The information changed the probability.

A and B are **independent** when knowing one tells you nothing about the other:
$P(A \mid B) = P(A)$, equivalently $P(A \cap B) = P(A)P(B)$.

```python
from itertools import product
from fractions import Fraction
omega = list(product(range(1, 7), repeat=2))
P = lambda ev: Fraction(sum(1 for o in omega if ev(o)), len(omega))
A = lambda o: o[0] + o[1] == 8
B = lambda o: o[0] == 6
print(P(A), P(lambda o: A(o) and B(o)) / P(B))   # → 5/36 1/6
C = lambda o: o[1] % 2 == 0                     # second die even
print(P(lambda o: B(o) and C(o)) == P(B) * P(C))   # → True
```

> **Watch out:** $P(A \mid B) \ne P(B \mid A)$ in general. P(fever | flu) is high;
> P(flu | fever) is much lower, because many things cause fever. Confusing the two is
> the **prosecutor's fallacy**, and Bayes' rule is the fix.

## 3 · Bayes' Rule: Updating Beliefs With Evidence

$$
P(H \mid E) = \frac{P(E \mid H)\, P(H)}{P(E)}, \qquad P(E) = P(E \mid H)P(H) + P(E \mid \neg H)P(\neg H)
$$

In words: **posterior = likelihood × prior ÷ evidence.** Start with how plausible the
hypothesis was (the **prior**), weigh how well it explains what you saw, and normalise.

> **Worked example (the base-rate trap):** A disease affects 1% of people. A test
> catches 90% of cases and gives a false positive 9% of the time. You test positive.
> How likely are you to be sick? Most people say about 90%. In 1,000 people: 10 are
> sick, 9 of whom test positive; 990 are healthy, about 89 of whom test positive
> anyway. So only 9 of about 98 positives are sick — **about 9%**.

**Try it: see the thousand people.** Each square is a person; solid squares tested
positive. Move the base rate, sensitivity and false-positive rate and count how many
solid squares are really sick. With a rare condition, even a good test produces mostly
false alarms.

<div class="lab" data-viz="bayes"></div>

```python
def posterior(prior, sensitivity, false_pos):
    evidence = sensitivity * prior + false_pos * (1 - prior)
    return sensitivity * prior / evidence

print(round(posterior(0.01, 0.90, 0.09), 3))    # → 0.092
print(round(posterior(0.30, 0.90, 0.09), 3))    # → 0.811
```

> **In practice:** The same arithmetic governs every alerting system. An anomaly
> detector with a 1% false-positive rate, run over thousands of healthy metrics, pages
> someone mostly for nothing when real incidents are rare — "alert fatigue" is Bayes'
> rule. It also powers naive Bayes spam filters: multiply the likelihood of each word
> under "spam" and "not spam", times the prior, and compare.

## 4 · Random Variables and Expectation

A **random variable** X is a number determined by the outcome: the value of a die, the
number of heads in 10 flips, a request's latency. Its **expected value** (mean) is the
probability-weighted average of its values:

$$
E[X] = \sum_{x} x \cdot P(X = x)
$$

A fair die: $E[X] = (1 + 2 + \dots + 6)/6 = 3.5$ — a value the die never shows, but the
long-run average of many rolls.

### Linearity of expectation: the most useful fact in this chapter

> **Key idea:** $E[X + Y] = E[X] + E[Y]$ **always** — even when X and Y are dependent.
> So to find the expected count of something, write it as a sum of **indicator
> variables** (1 if a thing happens, 0 if not) and add their probabilities.

> **Worked example (hat check):** n people throw their hats in a pile and each takes one
> at random. On average, how many get their own hat back? Let $X_i = 1$ if person i
> gets their own hat. $P(X_i = 1) = 1/n$, so $E[X_1 + \dots + X_n] = n \cdot 1/n = 1$.
> The answer is 1 for every n — and the $X_i$ are dependent, which did not matter.

```python
import random
random.seed(7)

def own_hats(n):
    hats = list(range(n))
    random.shuffle(hats)
    return sum(h == i for i, h in enumerate(hats))

trials = 100_000
print(round(sum(own_hats(10) for _ in range(trials)) / trials, 1))   # → 1.0
```

Linearity also gives, in one line each: the expected number of **inversions** in a
random permutation ($\binom{n}{2} \cdot \frac12$), the expected number of empty buckets
when hashing n keys into m buckets ($m(1 - 1/m)^n$), and — in §8 — the expected number
of comparisons in quicksort.

## 5 · Variance: How Spread Out

The expected value says where the centre is; the **variance** says how far values
typically stray from it:

$$
\text{Var}(X) = E\big[(X - E[X])^2\big] = E[X^2] - E[X]^2, \qquad \sigma = \sqrt{\text{Var}(X)}
$$

σ, the **standard deviation**, is in the same units as X. For **independent** variables
variances add: $\text{Var}(X + Y) = \text{Var}(X) + \text{Var}(Y)$. So the sum of n
independent copies has standard deviation $\sigma\sqrt{n}$ — it grows, but much slower
than the sum itself (which grows like n). That $\sqrt{n}$ is why averages of many
measurements are more reliable than one, and it is the heart of chapter 11.

```python
from fractions import Fraction
die = range(1, 7)
E = Fraction(sum(die), 6)
Var = Fraction(sum(x * x for x in die), 6) - E**2
print(E, Var, round(float(Var) ** 0.5, 4))   # → 7/2 35/12 1.7078
```

> **Notebook example:** A game pays 10 points if a die shows 6 and nothing otherwise. Find the
> mean and standard deviation of one play, then of 100 plays.
>
> 1. $E[X] = 10 \cdot \frac16 = \frac53 \approx 1.67$.
> 2. $E[X^2] = 100 \cdot \frac16 = \frac{50}{3}$.
> 3. $\text{Var}(X) = \frac{50}{3} - \left(\frac53\right)^2 = \frac{150}{9} - \frac{25}{9} = \frac{125}{9} \approx 13.9$,
>    so $\sigma \approx 3.73$.
> 4. For 100 independent plays, means and variances add: the mean is
>    $100 \times \frac53 \approx 166.7$, and the variance is $100 \times 13.9$, so the
>    standard deviation is $3.73 \times \sqrt{100} = 37.3$.
>
> **Answer:** one play has mean 1.67 points and σ 3.73. 100 plays have mean 166.7 points and σ 37.3. The
> total grew 100×, but the spread grew only 10×.

## 6 · The Distributions Engineers Meet

| Distribution | Models | P(X = k) or density | Mean | Variance |
|---|---|---|---|---|
| **Bernoulli(p)** | one success/failure | $p$ or $1-p$ | $p$ | $p(1-p)$ |
| **Binomial(n, p)** | successes in n independent trials | $\binom{n}{k}p^k(1-p)^{n-k}$ | $np$ | $np(1-p)$ |
| **Geometric(p)** | trials until the first success | $(1-p)^{k-1}p$ | $1/p$ | $(1-p)/p^2$ |
| **Poisson(λ)** | count of rare, independent events in an interval (arrivals, errors) | $e^{-\lambda}\lambda^k/k!$ | $\lambda$ | $\lambda$ |
| **Uniform(a, b)** | "any value equally likely" | $1/(b-a)$ | $(a+b)/2$ | $(b-a)^2/12$ |
| **Exponential(λ)** | waiting time between Poisson arrivals | $\lambda e^{-\lambda x}$ | $1/\lambda$ | $1/\lambda^2$ |
| **Normal(μ, σ)** | sums/averages of many small effects | $\frac{1}{\sigma\sqrt{2\pi}}e^{-(x-\mu)^2/2\sigma^2}$ | $\mu$ | $\sigma^2$ |

A few you will use constantly:

- **Geometric — retries.** If each attempt succeeds with probability p, you need $1/p$
  attempts on average. A call that fails 20% of the time needs 1.25 tries on average,
  but the chance of 5 failures in a row is still $0.2^5 = 0.032\%$ — per request, which
  at a million requests a day is 320 times a day.
- **Poisson — arrivals.** Requests arriving independently at an average rate λ per
  second. The number in any second is Poisson(λ); the gaps are exponential. This is the
  standard model behind queueing theory and capacity planning.
- **Exponential — memorylessness.** For exponential waiting times, having waited 5
  minutes does not change the expected remaining wait. Good for "random failures", bad
  for components that wear out.

```python
import math
lam = 3                      # 3 requests per second on average
pois = lambda k: math.exp(-lam) * lam**k / math.factorial(k)
print(round(pois(0), 4), round(sum(pois(k) for k in range(7)), 4))   # → 0.0498 0.9665
print(round(0.2**5 * 1_000_000))                                      # → 320
```

With 3 requests per second on average, a second with no requests happens about 5% of
the time, and 6 or fewer covers 96.65% of seconds — so provisioning for "average plus a
bit" still leaves bursts 3% of the time.

> **Notebook example:** A service runs 5 replicas, each down 10% of the time,
> independently. What is the chance that at least 4 are up? And if requests arrive at 3
> per second, what is the chance of a silent second?
>
> 1. The number down is Binomial(5, 0.1). "At least 4 up" means 0 or 1 down.
> 2. $P(0 \text{ down}) = 0.9^5 = 0.59049$.
> 3. $P(1 \text{ down}) = \binom51 (0.1)(0.9)^4 = 5 \times 0.1 \times 0.6561 = 0.32805$.
> 4. Add the disjoint cases: $0.59049 + 0.32805 = 0.91854$.
> 5. Poisson with λ = 3: $P(0) = e^{-3} \frac{3^0}{0!} = e^{-3} \approx 0.0498$.
>
> **Answer:** about 91.9% for at least 4 up, and a silent second about 5% of the time.

**Try it: shapes of distributions.** Pick a distribution, move its parameters, and draw
samples to watch the histogram fill in the curve.

<div class="lab" data-viz="distributions"></div>

## 7 · The Birthday Paradox and Hash Collisions

How many people must be in a room before two probably share a birthday? Not 183 — just
**23**. The chance that n people all have different birthdays (out of N = 365 days) is

$$
P(\text{no collision}) = \frac{N}{N}\cdot\frac{N-1}{N}\cdots\frac{N-n+1}{N} = \prod_{i=0}^{n-1}\left(1 - \frac{i}{N}\right) \approx e^{-n^2/2N}
$$

The approximation uses $1 - x \approx e^{-x}$ for small x (chapter 12). Setting it to ½
gives $n \approx \sqrt{2\ln 2}\,\sqrt{N} \approx 1.18\sqrt{N}$.

> **Key idea:** Collisions depend on the number of **pairs**, $\binom{n}{2} \approx n^2/2$,
> not on n. So collisions appear after about $\sqrt{N}$ items, not N. For hashing into N
> buckets or generating random IDs from N possibilities, plan for $\sqrt{N}$.

> **Notebook example:** What is the exact chance that 5 people share a birthday? And
> about how many random 32-bit IDs give even odds of a collision?
>
> 1. All different: $\frac{365}{365} \cdot \frac{364}{365} \cdot \frac{363}{365} \cdot \frac{362}{365} \cdot \frac{361}{365}$.
> 2. Multiply step by step: 1 → 0.99726 → 0.99180 → 0.98364 → 0.97286.
> 3. So a shared birthday has probability $1 - 0.97286 \approx 2.7\%$.
> 4. **Check** with the approximation: there are $\binom52 = 10$ pairs, and
>    $e^{-10/365} \approx 0.97297$. That is very close.
> 5. 32-bit IDs: $n \approx 1.18\sqrt{N} = 1.18 \times \sqrt{2^{32}} = 1.18 \times 65{,}536 \approx 77{,}000$.
>
> **Answer:** 2.7%, and about 77,000 IDs, out of a space of 4.3 billion.

**Try it: guess, then check.** With 365 days, drag to find where the curve crosses 50%.
Fill rooms at random and simulate a thousand of them to see the frequency match the
curve. Then switch to 2³² buckets: a 32-bit hash gives 50% odds of a collision after
only about 77,000 items.

<div class="lab" data-viz="math-birthday"></div>

```python
import math

def p_collision(n, N):
    p_none = 1.0
    for i in range(n):
        p_none *= 1 - i / N
    return 1 - p_none

print(round(p_collision(23, 365), 4), round(p_collision(70, 365), 4))   # → 0.5073 0.9992
print(round(math.sqrt(2 * math.log(2) * 2**32)))                         # → 77163
print(round(math.sqrt(2 * math.log(2) * 2**122) / 1e18, 2))              # → 2.71
```

A random UUIDv4 has 122 random bits: you would need about $2.7 \times 10^{18}$ of them for
even odds of one collision — that is why systems generate them freely without
coordination.

## 8 · Two Classic Results for Algorithms

### Coupon collector: how long to see everything?

Drawing uniformly from n types with replacement, how many draws until you have seen
every type? When you have seen k types, a new one appears with probability
$(n-k)/n$, so the wait is geometric with mean $n/(n-k)$. Linearity adds these:

$$
E[\text{draws}] = \frac{n}{n} + \frac{n}{n-1} + \dots + \frac{n}{1} = n\,H_n \approx n \ln n
$$

```python
import random, math
random.seed(3)

def draws_until_all(n):
    seen, t = set(), 0
    while len(seen) < n:
        seen.add(random.randrange(n))
        t += 1
    return t

n = 50
avg = sum(draws_until_all(n) for _ in range(2000)) / 2000
exact = n * sum(1 / k for k in range(1, n + 1))
print(round(exact), abs(avg - exact) < 10)   # → 225 True
```

To hit all 50 shards with random requests takes about 225 requests on average, not 50.
The same result says random load balancing across n servers leaves some idle for a long
time, and that "random testing covers every branch" needs about $n\ln n$ tests.

> **Notebook example:** A cereal box holds one of 4 toys, each equally likely. On
> average, how many boxes until you have all 4?
>
> | Toys already seen | Chance the next box is new | Expected boxes to wait |
> |---|---|---|
> | 0 | 4/4 | 1 |
> | 1 | 3/4 | 4/3 ≈ 1.33 |
> | 2 | 2/4 | 2 |
> | 3 | 1/4 | 4 |
>
> **Answer:** add the waits (linearity of expectation):
> $1 + \frac43 + 2 + 4 = \frac{25}{3} \approx 8.33$ boxes. **Check** with the formula:
> $n H_n = 4\left(1 + \frac12 + \frac13 + \frac14\right) = 4 \cdot \frac{25}{12} = \frac{25}{3}$. ✓
> Half of the wait is for the very last toy.

### Randomized quicksort: why the average is O(n log n)

Pick pivots at random. Two elements with ranks i < j are compared **only if** one of them
is the first pivot chosen among the $j - i + 1$ elements between them (inclusive) —
otherwise a pivot in between separates them forever. That happens with probability
$\frac{2}{j-i+1}$. By linearity, the expected number of comparisons is

$$
\sum_{i<j}\frac{2}{j-i+1} \le 2n\,H_n = O(n \log n)
$$

— for **every** input. Randomness moved the worst case from "a bad input" (which an
adversary can choose) to "bad luck" (which no one can choose, and which is
astronomically unlikely).

> **Definition:** A **Las Vegas** algorithm is always correct but its running time is
> random (randomized quicksort). A **Monte Carlo** algorithm has bounded running time
> but may be wrong with small probability (Miller–Rabin, Bloom filters, the π estimate
> below).

## 9 · Monte Carlo and the Law of Large Numbers

When a probability is hard to compute, simulate: run the experiment many times and
count. The **law of large numbers** guarantees the frequency converges to the true
probability; the error shrinks like $1/\sqrt{n}$ (chapter 11 explains why).

**Try it: estimate π by throwing darts.** The fraction of random points in the unit
square that land inside the quarter circle is π/4. Press *Play* and watch the estimate
wander, then settle inside the shrinking band. Notice how slowly: each extra digit of
accuracy costs 100 times more darts.

<div class="lab" data-viz="math-montecarlo"></div>

> **Notebook example:** You throw 20 darts and 16 land inside the quarter circle. What
> is your estimate of π? About how many darts would you need for ±0.01 accuracy?
>
> 1. Estimate: $\pi \approx 4 \times \frac{16}{20} = 3.2$.
> 2. One dart is a coin with $p = \pi/4 \approx 0.785$, so its standard deviation is
>    $\sqrt{p(1 - p)} = \sqrt{0.785 \times 0.215} \approx 0.411$.
> 3. The π estimate multiplies by 4, so its error is about
>    $\frac{4 \times 0.411}{\sqrt n} = \frac{1.64}{\sqrt n}$.
> 4. Set $\frac{1.64}{\sqrt n} = 0.01$: $\sqrt n = 164$, so $n \approx 27{,}000$.
>
> **Answer:** 3.2 from 20 darts, and about 27,000 darts for a typical error of 0.01. Each
> extra digit costs 100 times more darts.

## 10 · Bloom Filters: Probability as a Data Structure

A **Bloom filter** answers "have I seen this key?" in a fixed number of bits m, using k
hash functions: adding a key sets k bits; querying checks whether all k bits are set.
It never says "no" wrongly, but may say "yes" wrongly. After inserting n keys, a given
bit is still 0 with probability $(1 - 1/m)^{kn} \approx e^{-kn/m}$, so a false positive
(all k bits of an absent key happen to be set) has probability about

$$
\left(1 - e^{-kn/m}\right)^k, \qquad \text{minimised at } k = \frac{m}{n}\ln 2
$$

```python
import math

def bloom_fp(m, n, k):
    return (1 - math.exp(-k * n / m)) ** k

m, n = 10 * 1_000_000, 1_000_000        # 10 bits per key
k = round(m / n * math.log(2))
print(k, round(bloom_fp(m, n, k) * 100, 2))   # → 7 0.82
```

Ten bits per key (1.25 MB per million keys) with 7 hashes gives under a 1% false-positive
rate — a tiny memory cost to skip most disk lookups for keys that are not there, which
is exactly how LSM-tree databases such as Cassandra and RocksDB use them.

> **Notebook example:** A Bloom filter has m = 1,000 bits and holds n = 100 keys. What
> is the best number of hashes, and what false-positive rate does it give?
>
> 1. Best k: $\frac{m}{n}\ln 2 = 10 \times 0.693 = 6.93$, so use **7**.
> 2. The chance a given bit is still 0: $e^{-kn/m} = e^{-7 \times 100 / 1000} = e^{-0.7} \approx 0.497$.
> 3. So a bit is 1 with probability $1 - 0.497 = 0.503$.
> 4. A false positive needs all 7 of an absent key's bits to be 1: $0.503^7 \approx 0.0082$.
>
> **Answer:** 7 hashes and about a 0.8% false-positive rate, using 125 bytes for 100
> keys.

## Common Mistakes

1. **Assuming independence** (correlated failures, repeated hash seeds).
2. **Confusing $P(A \mid B)$ with $P(B \mid A)$** and ignoring base rates.
3. **The gambler's fallacy:** after five heads, the next flip is still 50/50 —
   independent trials have no memory.
4. **Multiplying probabilities of overlapping events** or adding probabilities of
   non-exclusive ones.
5. **Expecting collisions only near capacity** — they arrive at about $\sqrt{N}$.
6. **Reporting an average without the spread** (chapter 11).

## Check Yourself

**1.** You roll a die until you get a 6. Expected number of rolls? Probability it takes
more than 10?

<details>
<summary>Open the answer</summary>

Geometric with p = 1/6: expected 6 rolls. More than 10 means the first 10 all fail:
$(5/6)^{10} \approx 16.2\%$.

</details>

**2.** You hash 1,000 keys into 1,000,000 buckets. Probability of at least one collision?

<details>
<summary>Open the answer</summary>

About $1 - e^{-n^2/2N} = 1 - e^{-10^6/(2 \cdot 10^6)} = 1 - e^{-0.5} \approx 39\%$. With a
thousand times more buckets than keys, a collision is still likely. The expected number
of colliding pairs is $\binom{1000}{2}/10^6 \approx 0.5$.

</details>

**3.** An alert has 99% sensitivity and a 1% false-positive rate; real incidents occur in
0.1% of the checked windows. When it fires, how likely is a real incident?

<details>
<summary>Open the answer</summary>

$\frac{0.99 \cdot 0.001}{0.99 \cdot 0.001 + 0.01 \cdot 0.999} \approx 9\%$. Nine in ten
pages are false alarms. Raise the prior (alert only on already-suspicious windows) or
lower the false-positive rate.

</details>

**4.** Throw n balls into n bins at random. Expected number of empty bins?

<details>
<summary>Open the answer</summary>

Indicator per bin: empty with probability $(1 - 1/n)^n \approx 1/e$. By linearity,
about $n/e \approx 0.37n$ bins stay empty — why a hash table at load factor 1 leaves
about 37% of slots unused even though, on average, there is one key per slot.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Sample spaces and events; probability by counting; complement, addition and (independent) multiplication rules; expectation of simple variables |
| **Interview-ready** | Conditional probability and Bayes with base rates; linearity of expectation with indicators; geometric, binomial and Poisson in practice; the birthday bound for hashing and IDs; coupon collector; why randomized quicksort is O(n log n) expected |
| **Going deeper** | Variance of sums and concentration; Markov chains (chapter 09); Bloom filter analysis; tail bounds (Markov, Chebyshev, Chernoff); Las Vegas vs Monte Carlo design |

## Checklist

- [ ] I compute "at least one" probabilities with the complement.
- [ ] I question every independence assumption.
- [ ] I can apply Bayes' rule and explain the base-rate trap with numbers.
- [ ] I use linearity of expectation with indicator variables.
- [ ] I know the expected number of trials until success is 1/p.
- [ ] I can estimate when collisions become likely for N buckets or IDs.
- [ ] I can derive the Bloom filter false-positive rate and the optimal k.
