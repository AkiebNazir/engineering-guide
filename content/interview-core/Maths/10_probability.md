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
> mean and standard deviation of one play.
>
> **What you need:** X is the payout of one play. The **mean** (expected value)
> $E[X] = \sum x \cdot P(X = x)$: multiply each possible value by its chance and add. The
> **variance** measures spread: $\text{Var}(X) = E[X^2] - E[X]^2$, "the average of the
> squares minus the square of the average". The **standard deviation** σ is the square
> root of the variance, which puts it back in points.
>
> **Plan:** list the two outcomes, find the average payout, then the average squared
> payout, then combine them into the variance and take the root.
>
> 1. **List the outcomes.** Pay 10 with chance $\frac16$ (a six); pay 0 with chance
>    $\frac56$ (anything else).
> 2. **Find the mean.** $E[X] = 10 \cdot \frac16 + 0 \cdot \frac56 = \frac{10}{6} = \frac53 \approx 1.67$.
>    *Why:* over 6 plays you expect one six, so 10 points shared over 6 plays.
> 3. **Square each payout.** $10^2 = 100$ and $0^2 = 0$.
> 4. **Find the mean of the squares.** $E[X^2] = 100 \cdot \frac16 + 0 \cdot \frac56 = \frac{100}{6} = \frac{50}{3}$.
> 5. **Square the mean.** $E[X]^2 = \left(\frac53\right)^2 = \frac{25}{9}$.
> 6. **Subtract.** Put both over 9 first: $\frac{50}{3} = \frac{150}{9}$. Then
>    $\frac{150}{9} - \frac{25}{9} = \frac{125}{9} \approx 13.9$.
> 7. **Take the square root.** $\sigma = \sqrt{13.9} \approx 3.73$.
>    *Why:* the variance is in "points squared", which means nothing; the root is back
>    in points.
>
> **Answer:** one play has mean about 1.67 points and standard deviation about 3.73
> points. The spread is bigger than the mean: a single play is usually 0, sometimes 10.
>
> **Check:** compute the variance the long way, as the average squared distance from the
> mean. The six is $10 - \frac53 = \frac{25}{3}$ away, squared $\frac{625}{9}$, chance
> $\frac16$; the miss is $\frac53$ away, squared $\frac{25}{9}$, chance $\frac56$. Then
> $\frac{625}{54} + \frac{125}{54} = \frac{750}{54} = \frac{125}{9}$. ✓

> **Your turn:** A coin game pays 4 points on heads and nothing on tails. Find the mean
> and standard deviation of one play.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **List the outcomes.** 4 with chance $\frac12$; 0 with chance $\frac12$.
> 2. **Find the mean.** $4 \cdot \frac12 + 0 = 2$.
> 3. **Square each payout.** $4^2 = 16$ and $0^2 = 0$.
> 4. **Find the mean of the squares.** $16 \cdot \frac12 = 8$.
> 5. **Square the mean.** $2^2 = 4$.
> 6. **Subtract.** $8 - 4 = 4$.
> 7. **Take the square root.** $\sigma = \sqrt 4 = 2$.
>
> **Answer:** mean 2 points, standard deviation 2 points.
>
> </details>

> **Notebook example:** Now play the same die game (mean $\frac53 \approx 1.67$,
> variance $\frac{125}{9} \approx 13.9$, σ ≈ 3.73 per play) 100 times. Find the mean and
> standard deviation of the total.
>
> **What you need:** for a sum of plays, **means always add**. For **independent** plays
> (one roll does not affect the next), **variances add** too. Standard deviations do
> **not** add: you add the variances and then take the square root. So n plays have
> variance $n \cdot \text{Var}(X)$ and standard deviation $\sigma \sqrt{n}$.
>
> **Plan:** multiply the mean by 100, multiply the variance by 100, then take the root.
>
> 1. **Add up the means.** $100 \times \frac53 = \frac{500}{3} \approx 166.7$.
> 2. **Add up the variances.** $100 \times \frac{125}{9} = \frac{12500}{9} \approx 1389$.
>    *Why:* each play brings its own independent wobble, and wobbles add in "squared"
>    units.
> 3. **Take the square root.** $\sqrt{1389} \approx 37.3$.
> 4. **Compare with the shortcut.** $\sigma\sqrt{n} = 3.73 \times \sqrt{100} = 3.73 \times 10 = 37.3$.
>    *Why:* $\sqrt{100 \cdot \text{Var}} = \sqrt{100} \cdot \sqrt{\text{Var}}$, so both
>    routes must agree.
>
> **Answer:** 100 plays total about 166.7 points on average, give or take about 37.3. The
> total grew 100×, but the spread grew only 10×, so totals are far more predictable,
> relative to their size, than single plays.
>
> **Check:** a simulation such as
> `sum(10 * (random.randint(1, 6) == 6) for _ in range(100))`, repeated many times,
> averages near 167 with most totals within about 37 of it. ✓

> **Your turn:** Play the coin game (mean 2, variance 4, σ = 2 per play) 25 times. Find
> the mean and standard deviation of the total.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Add up the means.** $25 \times 2 = 50$.
> 2. **Add up the variances.** $25 \times 4 = 100$.
> 3. **Take the square root.** $\sqrt{100} = 10$.
> 4. **Compare with the shortcut.** $2 \times \sqrt{25} = 2 \times 5 = 10$. ✓
>
> **Answer:** mean 50 points, standard deviation 10 points.
>
> </details>

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
> independently. What is the chance that at least 4 are up?
>
> **What you need:** **independent** means one replica being down tells you nothing about
> the others, so you may **multiply** their chances. Counting how many of n independent
> tries "succeed" (here: how many replicas are down) gives a **binomial** distribution:
> one exact pattern with k downs has chance $p^k (1 - p)^{n-k}$, and there are
> $\binom{n}{k}$ ("n choose k", chapter 05) such patterns. Outcomes that cannot happen
> together (**disjoint**: exactly 0 down, exactly 1 down) have chances you can **add**.
>
> **Plan:** turn "at least 4 up" into "0 down or 1 down", find each chance, then add.
>
> 1. **Translate the question.** With 5 replicas, "at least 4 up" means "0 down or exactly
>    1 down".
> 2. **Find the chance one replica is up.** $1 - 0.1 = 0.9$.
> 3. **Find P(0 down).** All five must be up: $0.9^5$. Step by step: $0.9 \to 0.81 \to 0.729 \to 0.6561 \to 0.59049$.
>    *Why:* independent, so multiply one 0.9 per replica.
> 4. **Find the chance of one exact pattern with 1 down.** Say replica 1 is down and the
>    other four are up: $0.1 \times 0.9^4 = 0.1 \times 0.6561 = 0.06561$.
> 5. **Count the patterns.** The down replica could be any of the 5, so there are
>    $\binom51 = 5$ patterns, each with the same chance.
> 6. **Find P(1 down).** $5 \times 0.06561 = 0.32805$.
> 7. **Add the two disjoint cases.** $0.59049 + 0.32805 = 0.91854$.
>
> **Answer:** about 91.9%. So about 1 time in 12 you are down to 3 or fewer healthy
> replicas, which is worth knowing if you need 4 to carry the load.
>
> **Check:** in Python, `sum(math.comb(5, k) * 0.1**k * 0.9**(5 - k) for k in (0, 1))`
> gives 0.91854. ✓ Out of 100,000 moments, about 59,049 have all up and 32,805 have one
> down, 91,854 in all.

> **Your turn:** 4 replicas are each down 20% of the time, independently. What is the
> chance that at least 3 are up?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Translate the question.** "At least 3 up" means 0 down or exactly 1 down.
> 2. **Find the chance one replica is up.** $1 - 0.2 = 0.8$.
> 3. **Find P(0 down).** $0.8^4$: $0.8 \to 0.64 \to 0.512 \to 0.4096$.
> 4. **Find the chance of one exact pattern with 1 down.** $0.2 \times 0.8^3 = 0.2 \times 0.512 = 0.1024$.
> 5. **Count the patterns.** $\binom41 = 4$.
> 6. **Find P(1 down).** $4 \times 0.1024 = 0.4096$.
> 7. **Add the two disjoint cases.** $0.4096 + 0.4096 = 0.8192$.
>
> **Answer:** about 81.9%.
>
> </details>

> **Notebook example:** Requests arrive independently at an average of 3 per second.
> What is the chance that a given second has no requests at all?
>
> **What you need:** the **Poisson** distribution counts rare, independent events in a
> fixed window. With an average of λ events per window, the chance of exactly k events
> is $P(k) = e^{-\lambda} \frac{\lambda^k}{k!}$. Here e ≈ 2.718 (`math.e`), and $k!$
> ("k factorial") is $1 \cdot 2 \cdots k$, with $0! = 1$ by definition.
>
> **Plan:** put λ = 3 and k = 0 into the formula and simplify.
>
> 1. **Pick λ and k.** λ = 3 (the average per second); k = 0 (a silent second).
> 2. **Substitute.** $P(0) = e^{-3} \cdot \frac{3^0}{0!}$.
> 3. **Simplify the fraction.** $3^0 = 1$ (anything to the power 0 is 1) and $0! = 1$, so
>    the fraction is $\frac11 = 1$.
> 4. **What is left.** $P(0) = e^{-3}$.
> 5. **Rewrite as a division.** $e^{-3} = \frac{1}{e^3}$, and $e^3 \approx 20.09$.
> 6. **Divide.** $1 / 20.09 \approx 0.0498$.
>
> **Answer:** about 5%: roughly one second in twenty gets no requests, even though the
> average is 3.
>
> **Check:** `math.exp(-3)` prints 0.0497… ✓ Out of 1,000 seconds, about 50 would be
> silent; the code above (`pois(0)`) gives the same 0.0498.

> **Your turn:** Errors arrive independently at an average of 2 per hour. What is the
> chance of an hour with no errors?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Pick λ and k.** λ = 2, k = 0.
> 2. **Substitute.** $P(0) = e^{-2} \cdot \frac{2^0}{0!}$.
> 3. **Simplify the fraction.** $2^0 = 1$ and $0! = 1$, so it is 1.
> 4. **Rewrite as a division.** $e^{-2} = 1 / e^2$, and $e^2 \approx 7.39$.
> 5. **Divide.** $1 / 7.39 \approx 0.135$.
>
> **Answer:** about 13.5%, roughly one hour in seven.
>
> </details>

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

> **Notebook example:** In a room of 5 people, what is the exact chance that at least two
> share a birthday? (Ignore leap years; all 365 days equally likely.)
>
> **What you need:** "at least two share" covers many messy cases, so use the
> **complement**: $P(\text{some shared}) = 1 - P(\text{all different})$. Bring people in
> one at a time. Each newcomer must avoid the birthdays already taken; the chance of that
> is (free days) / 365. People's birthdays are independent, so **multiply** these
> chances.
>
> **Plan:** build P(all different) one person at a time, then subtract from 1.
>
> 1. **Person 1.** Any day is fine: $\frac{365}{365} = 1$.
> 2. **Person 2.** Must avoid 1 taken day, so 364 days are free:
>    $1 \times \frac{364}{365} \approx 0.99726$.
> 3. **Person 3.** Must avoid 2 taken days: $0.99726 \times \frac{363}{365} \approx 0.99180$.
> 4. **Person 4.** Must avoid 3 taken days: $0.99180 \times \frac{362}{365} \approx 0.98364$.
> 5. **Person 5.** Must avoid 4 taken days: $0.98364 \times \frac{361}{365} \approx 0.97286$.
>    *Why:* every factor is a little below 1, so the product keeps sliding down as the
>    room fills.
> 6. **Take the complement.** $1 - 0.97286 = 0.02714 \approx 2.7\%$.
>
> **Answer:** about 2.7%. Small for 5 people, but the chance grows quickly: it passes 50%
> at 23 people.
>
> **Check:** the shortcut $e^{-\text{pairs}/N}$. There are $\binom52 = 10$ pairs of
> people, and $e^{-10/365} \approx 0.97297$, very close to 0.97286. ✓
> `p_collision(5, 365)` below gives 0.0271. ✓

> **Your turn:** What is the chance that at least two of 4 people share a birthday?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Person 1.** $\frac{365}{365} = 1$.
> 2. **Person 2.** $1 \times \frac{364}{365} \approx 0.99726$.
> 3. **Person 3.** $0.99726 \times \frac{363}{365} \approx 0.99180$.
> 4. **Person 4.** $0.99180 \times \frac{362}{365} \approx 0.98364$.
> 5. **Take the complement.** $1 - 0.98364 = 0.01636 \approx 1.6\%$.
>
> **Answer:** about 1.6%.
>
> </details>

> **Notebook example:** About how many random 32-bit IDs can you generate before there is
> an even (50%) chance that two are the same?
>
> **What you need:** with N equally likely values, collisions reach even odds after about
> $n \approx 1.18\sqrt{N}$ items (the 1.18 is $\sqrt{2\ln 2}$, from the formula above). A
> 32-bit ID has $N = 2^{32}$ possible values. Square roots of powers of 2 are easy:
> $\sqrt{2^{32}} = 2^{16}$, because $2^{16} \times 2^{16} = 2^{32}$.
>
> **Plan:** find N, take its square root, multiply by 1.18.
>
> 1. **Find N.** $2^{32} = 4{,}294{,}967{,}296$, about 4.3 billion.
> 2. **Take the square root.** Halve the exponent: $\sqrt{2^{32}} = 2^{16} = 65{,}536$.
>    *Why:* collisions are about **pairs**, and the number of pairs grows like $n^2$, so
>    the answer scales with $\sqrt N$, not N.
> 3. **Multiply by 1.18.** $1.18 \times 65{,}536 \approx 77{,}300$, so about 77,000.
>
> **Answer:** about 77,000 IDs, out of a space of 4.3 billion. Random 32-bit IDs are
> **not** safe for a system with millions of records.
>
> **Check:** count the pairs. $77{,}000$ items make about $\frac{77{,}000^2}{2} \approx 2.96$
> billion pairs; each pair matches with chance $\frac{1}{4.29 \text{ billion}}$, so we
> expect about 0.69 matching pairs, and $e^{-0.69} \approx 0.5$. ✓ The code below prints
> 77163.

> **Your turn:** About how many random 16-bit IDs give an even chance of a collision?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find N.** $2^{16} = 65{,}536$.
> 2. **Take the square root.** $\sqrt{2^{16}} = 2^8 = 256$.
> 3. **Multiply by 1.18.** $1.18 \times 256 \approx 302$.
>
> **Answer:** about 300 IDs.
>
> </details>

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
> **What you need:** two facts. (1) **Waiting for a success:** if each try succeeds with
> chance p, you need $1/p$ tries on average (the geometric distribution). A 1-in-4
> chance takes 4 tries on average. (2) **Linearity of expectation:** the average of a
> total is the sum of the averages, so you can split the long wait into stages and add
> their average lengths.
>
> **Plan:** split the hunt into 4 stages (waiting for the 1st new toy, the 2nd, the 3rd,
> the 4th), find each stage's chance of success and average wait, and add.
>
> 1. **Stage 1: no toys yet.** Any toy is new, so the chance is $\frac44 = 1$ and the
>    wait is $1 / 1 = 1$ box.
> 2. **Stage 2: one toy seen.** 3 of the 4 toys are new, so the chance is $\frac34$ and
>    the wait is $1 \div \frac34 = \frac43 \approx 1.33$ boxes.
>    *Why:* dividing by a fraction flips it: $1 \div \frac34 = \frac43$.
> 3. **Stage 3: two toys seen.** The chance is $\frac24 = \frac12$, so the wait is 2 boxes.
> 4. **Stage 4: three toys seen.** Only 1 toy is new: chance $\frac14$, wait 4 boxes.
>    *Why:* the last toy is the hardest, since 3 boxes in 4 are repeats.
> 5. **Add the stages.** $1 + \frac43 + 2 + 4 = 7 + \frac43 = \frac{21}{3} + \frac43 = \frac{25}{3} \approx 8.33$.
>
> **Answer:** about 8.33 boxes on average, more than twice the 4 you might guess. Almost
> half of that (4 boxes) is spent waiting for the very last toy.
>
> **Check:** the formula $n H_n$, where $H_n = 1 + \frac12 + \dots + \frac1n$:
> $1 + \frac12 + \frac13 + \frac14 = \frac{12 + 6 + 4 + 3}{12} = \frac{25}{12}$, and
> $4 \cdot \frac{25}{12} = \frac{25}{3}$. ✓ `draws_until_all(4)` averaged over many runs
> lands near 8.3.

> **Your turn:** A box holds one of 3 equally likely toys. On average, how many boxes
> until you have all 3?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Stage 1: no toys yet.** Chance $\frac33 = 1$, wait 1 box.
> 2. **Stage 2: one toy seen.** Chance $\frac23$, wait $\frac32 = 1.5$ boxes.
> 3. **Stage 3: two toys seen.** Chance $\frac13$, wait 3 boxes.
> 4. **Add the stages.** $1 + 1.5 + 3 = 5.5$.
>
> **Answer:** 5.5 boxes on average (formula: $3 \cdot (1 + \frac12 + \frac13) = 3 \cdot \frac{11}{6} = 5.5$).
>
> </details>

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

> **Notebook example:** You throw 20 darts at random into the unit square and 16 land
> inside the quarter circle. What is your estimate of π?
>
> **What you need:** the quarter circle of radius 1 has area $\frac{\pi}{4}$ and the
> square has area 1. A random dart lands inside with chance equal to that area ratio,
> $\frac{\pi}{4} \approx 0.785$. The **fraction of darts inside** estimates that chance
> (the frequency reading of probability), so 4 × (fraction inside) estimates π.
>
> **Plan:** find the fraction of hits, then multiply by 4.
>
> 1. **Find the fraction inside.** $\frac{16}{20} = 0.8$.
>    *Why:* this is our best guess at the chance a dart lands inside, which is
>    $\frac{\pi}{4}$.
> 2. **Undo the quarter.** $\pi \approx 4 \times 0.8 = 3.2$.
>    *Why:* if $\frac{\pi}{4} \approx 0.8$, multiplying both sides by 4 gives π.
>
> **Answer:** π ≈ 3.2 from 20 darts. That is in the right area but off by about 0.06: 20
> darts is a very small sample.
>
> **Check:** the true value gives $\frac{\pi}{4} \times 20 \approx 0.785 \times 20 = 15.7$
> darts expected inside, and we saw 16, which is close. ✓

> **Your turn:** 100 darts, 78 inside. Estimate π.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the fraction inside.** $\frac{78}{100} = 0.78$.
> 2. **Undo the quarter.** $4 \times 0.78 = 3.12$.
>
> **Answer:** π ≈ 3.12.
>
> </details>

> **Notebook example:** About how many darts would you need for the π estimate to be
> accurate to about ±0.01?
>
> **What you need:** one dart is a yes/no coin that says "inside" with chance
> $p = \frac{\pi}{4} \approx 0.785$. Such a coin has standard deviation (typical
> wobble) $\sqrt{p(1 - p)}$. Averaging n independent darts shrinks the wobble by
> $\sqrt n$ (chapter 11): the typical error of the average is
> $\frac{\text{one dart's wobble}}{\sqrt n}$.
>
> **Plan:** find one dart's wobble, scale it by 4 (because we multiply by 4 to get π),
> then solve "wobble / √n = 0.01" for n.
>
> 1. **Find 1 − p.** $1 - 0.785 = 0.215$.
> 2. **Multiply.** $p(1 - p) = 0.785 \times 0.215 \approx 0.169$.
> 3. **Take the square root.** $\sqrt{0.169} \approx 0.411$. That is one dart's wobble.
> 4. **Scale by 4.** $4 \times 0.411 \approx 1.64$.
>    *Why:* the π estimate is 4 × the fraction, so its wobble is 4 × as big too.
> 5. **Write the error for n darts.** $\frac{1.64}{\sqrt n}$.
> 6. **Set it equal to 0.01 and solve for √n.** $\sqrt n = \frac{1.64}{0.01} = 164$.
> 7. **Square both sides.** $n = 164^2 = 164 \times 164 = 26{,}896$, about 27,000.
>
> **Answer:** about 27,000 darts for a typical error of 0.01. Each extra digit of
> accuracy costs 100 times more darts, because the error only shrinks like $1/\sqrt n$.
>
> **Check:** with the 20 darts of the last example, the typical error is
> $1.64 / \sqrt{20} \approx 1.64 / 4.47 \approx 0.37$, and the 3.2 we got was off by
> only 0.06, comfortably inside that. ✓

> **Your turn:** About how many darts give a typical error of 0.1 instead?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the error for n darts.** $\frac{1.64}{\sqrt n}$ (same wobble as before).
> 2. **Set it equal to 0.1 and solve for √n.** $\sqrt n = \frac{1.64}{0.1} = 16.4$.
> 3. **Square both sides.** $n = 16.4^2 \approx 269$.
>
> **Answer:** about 270 darts, 100 times fewer than for ±0.01.
>
> </details>

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

> **Notebook example:** A Bloom filter has m = 1,000 bits and will hold n = 100 keys. What
> is the best number of hash functions k?
>
> **What you need:** each key sets k bits. Too few hashes and an absent key is easy to
> mistake for a present one (few bits to check); too many and the array fills up with 1s.
> The sweet spot is $k = \frac{m}{n}\ln 2$, where $\frac{m}{n}$ is "bits per key" and
> $\ln 2 \approx 0.693$ (`math.log(2)`). k must be a whole number, so round.
>
> **Plan:** find bits per key, multiply by 0.693, round.
>
> 1. **Find the bits per key.** $\frac{m}{n} = \frac{1000}{100} = 10$.
> 2. **Multiply by ln 2.** $10 \times 0.693 = 6.93$.
> 3. **Round to a whole number.** 6.93 rounds to **7**.
>    *Why:* you cannot run 6.93 hash functions, and the rate changes very little near the
>    best value.
>
> **Answer:** use 7 hash functions. A handy rule: the best k is about 0.7 × bits per
> key.
>
> **Check:** the formula from the next example gives about 0.84% for k = 6, 0.82% for
> k = 7 and 0.85% for k = 8, so 7 is the lowest. ✓ This is the
> `round(m / n * math.log(2))` line in the code above.

> **Your turn:** A Bloom filter has 400 bits for 100 keys. What is the best k?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the bits per key.** $400 / 100 = 4$.
> 2. **Multiply by ln 2.** $4 \times 0.693 \approx 2.77$.
> 3. **Round to a whole number.** 2.77 rounds to 3.
>
> **Answer:** 3 hash functions.
>
> </details>

> **Notebook example:** The same filter (m = 1,000 bits, n = 100 keys) uses k = 7
> hashes. What is its false-positive rate?
>
> **What you need:** a **false positive** is when you ask about a key that was never
> added and all k of its bits happen to be 1 already. After inserting n keys with k
> hashes each, one particular bit is still 0 with chance about $e^{-kn/m}$ (so it is 1
> with chance $1 - e^{-kn/m}$). The k bits of the absent key behave roughly
> independently, so multiply: false-positive rate $\approx \left(1 - e^{-kn/m}\right)^k$.
>
> **Plan:** compute the exponent, the chance a bit is 0, the chance it is 1, then raise to
> the power k.
>
> 1. **Compute the exponent.** $\frac{kn}{m} = \frac{7 \times 100}{1000} = \frac{700}{1000} = 0.7$.
>    *Why:* 700 bit-settings were spread over 1,000 bits, 0.7 per bit on average.
> 2. **Find the chance a bit is still 0.** $e^{-0.7} \approx 0.4966$.
> 3. **Find the chance a bit is 1.** $1 - 0.4966 = 0.5034$. About half the bits are set.
> 4. **Square it.** $0.5034^2 \approx 0.2534$.
> 5. **Square again for the 4th power.** $0.2534^2 \approx 0.0642$.
> 6. **Multiply up to the 7th power.** $0.5034^7 = 0.5034^4 \times 0.5034^2 \times 0.5034$,
>    so $0.0642 \times 0.2534 \approx 0.01627$, then $0.01627 \times 0.5034 \approx 0.0082$.
>    *Why:* all 7 bits must be 1 by bad luck, and each is a roughly 50/50 chance.
>
> **Answer:** about 0.8%: fewer than 1 in 100 lookups for absent keys wrongly says "maybe
> present", using only 1,000 bits = 125 bytes for 100 keys.
>
> **Check:** a quick estimate: 7 coin flips all coming up heads is
> $\left(\tfrac12\right)^7 = \frac{1}{128} \approx 0.78\%$, very close. ✓
> `bloom_fp(1000, 100, 7)` from the code above gives 0.0082. ✓

> **Your turn:** A filter with m = 400 bits and n = 100 keys uses k = 3 hashes. What is
> its false-positive rate?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Compute the exponent.** $\frac{3 \times 100}{400} = 0.75$.
> 2. **Find the chance a bit is still 0.** $e^{-0.75} \approx 0.4724$.
> 3. **Find the chance a bit is 1.** $1 - 0.4724 = 0.5276$.
> 4. **Raise to the power 3.** $0.5276^2 \approx 0.2784$, then $0.2784 \times 0.5276 \approx 0.147$.
>
> **Answer:** about 14.7%. With only 4 bits per key the filter is far leakier than with
> 10.
>
> </details>

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
