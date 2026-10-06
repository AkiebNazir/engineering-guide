# Sequences, Sums, Logarithms and Recurrences — The Maths of Complexity

Every complexity bound you will ever state comes from this chapter. A loop's cost is a
**sum**; a recursive function's cost is a **recurrence**; "fast" algorithms are fast
because of **logarithms**; and Big-O is a precise statement about **growth rates**.
Here we build each tool from scratch — arithmetic and geometric series, logarithms as
counting halvings, the formal definitions of O, Ω and Θ, solving recurrences by
unrolling, recursion trees and the master theorem, and the characteristic-equation
method that explains why naive Fibonacci is exponential and how to compute it in
O(log n).

**Where this fits:** Part 2 · Discrete maths, chapter 6 of 15. **Builds on:** [01 Reading maths like code](01_reading_maths_like_code.md) (Σ notation and logarithms). **Used again in:** 12, 15. **Next in order:** [07 Number theory](07_number_theory.md).

## Where You Will Use This

| You need to… | Tool |
|---|---|
| Price a nested loop | Arithmetic series, Σ manipulation (chapter 01) |
| Explain why doubling an array is O(1) amortized | Geometric series |
| Explain why binary search, heaps and balanced trees are fast | Logarithms |
| State a precise bound, or prove one | O, Ω, Θ definitions |
| Price merge sort, quicksort, Karatsuba, a tree recursion | Recurrences, recursion trees, master theorem |
| Know why naive recursive Fibonacci explodes, and fix it | Linear recurrences, memoisation, matrix power |
| Tune retries | Exponential backoff |

## Foundations — Sequences and How They Grow

A **sequence** is a list of numbers indexed by position: $a_0, a_1, a_2, \dots$ It is
just a function from ℕ to numbers, $n \mapsto a_n$. You can define one in two ways:

- **Explicitly:** $a_n = 2n + 1$ — compute any term directly (like an array lookup).
- **Recursively:** $a_0 = 1,\ a_n = a_{n-1} + 2$ — each term from earlier ones (like a
  loop or recursion). This is a **recurrence relation**.

Both define 1, 3, 5, 7, … Much of this chapter is turning recursive definitions (which
is how code is written) into explicit ones (which is how you read off complexity).

> **Intuition:** For complexity we care about the *shape* of growth as n gets large:
> does the sequence grow like n, like n², like $2^n$, like $\log n$? The exact
> constants matter far less than which family it belongs to.

## 1 · Arithmetic and Geometric Series

### Arithmetic: adding a constant step

1, 2, 3, …, n (step 1), or 5, 8, 11, … (step 3). The sum of an arithmetic series is
**the number of terms times the average of the first and last term**:

$$
\sum_{i=1}^{n} i = \frac{n(n+1)}{2} = \Theta(n^2)
$$

(Gauss's pairing trick, chapter 01.) Any loop whose i-th iteration costs about i steps
is quadratic in total.

### Geometric: multiplying by a constant ratio

$1 + r + r^2 + \dots + r^{n}$. The trick to sum it: call it S, multiply by r, subtract —
everything except the ends cancels:

$$
S - rS = 1 - r^{n+1} \quad\Rightarrow\quad S = \frac{1 - r^{n+1}}{1 - r} \quad (r \ne 1)
$$

Three regimes, and each one shows up in algorithms:

| Ratio | Behaviour | The sum is dominated by | Example |
|---|---|---|---|
| $r < 1$ | converges to $\frac{1}{1-r}$ | the **first** term | $n + n/2 + n/4 + \dots < 2n$: halving work (quickselect's expected cost) |
| $r = 1$ | $n + 1$ terms of 1 | every term equally | a loop of equal steps |
| $r > 1$ | grows like $r^n$ | the **last** term | $1 + 2 + 4 + \dots + 2^k = 2^{k+1} - 1$: tree levels, doubling arrays |

```python
def geometric_sum(r, n):
    return sum(r**i for i in range(n + 1))

print(geometric_sum(2, 10), 2**11 - 1)          # → 2047 2047
print(round(geometric_sum(0.5, 60), 12))       # → 2.0
print(geometric_sum(3, 4), (3**5 - 1) // 2)     # → 121 121
```

> **Key idea:** In a geometric series with $r > 1$ the last term is bigger than all the
> previous terms combined (for r = 2) or at least a constant fraction of the total.
> So **a geometric sum costs a constant times its biggest term**. This one fact
> explains amortized array growth, why a heap can be built in O(n), and why the leaves
> of a binary tree are half of its nodes.

**Try it: watch sums settle or explode.** Drag the ratio *r* of the geometric series
from 0.5 up past 1 and on to 2: the running total (line) settles at 1/(1 − r), then
grows linearly at r = 1, then explodes with the last bar dominating. Then compare the
harmonic series, whose terms shrink but whose sum still grows forever.

<div class="lab" data-viz="math-series"></div>

> **Notebook example:** Add up $5 + 8 + 11 + \dots + 50$.
>
> **What you need:** an **arithmetic series** adds numbers that go up by the same
> **step** each time. Its sum is **(number of terms) × (average of the first and last
> term)**. The number of terms is $\frac{\text{last} - \text{first}}{\text{step}} + 1$.
>
> **Plan:** find the step, count the terms, find the average of the ends, multiply.
>
> 1. **Find the step.** $8 - 5 = 3$ (and $11 - 8 = 3$ too).
> 2. **Measure the distance from first to last.** $50 - 5 = 45$.
> 3. **Count the steps.** $45 \div 3 = 15$ steps of 3.
> 4. **Count the terms.** $15 + 1 = 16$ terms.
>    *Why:* like fence posts and gaps, 15 gaps between numbers need 16 numbers. Forgetting
>    the +1 is the classic off-by-one bug.
> 5. **Average the first and last.** $5 + 50 = 55$, and $55 \div 2 = 27.5$.
>    *Why:* the terms are evenly spaced, so their average is exactly halfway between the
>    ends.
> 6. **Multiply.** $16 \times 27.5$: $16 \times 27 = 432$ and $16 \times 0.5 = 8$, so
>    $432 + 8 = 440$.
>
> **Answer:** $5 + 8 + 11 + \dots + 50 = 440$.
>
> **Check:** Gauss's pairing trick. First + last $= 5 + 50 = 55$; second + second-last
> $= 8 + 47 = 55$; every pair makes 55. 16 terms make 8 pairs: $8 \times 55 = 440$. ✓ In
> Python, `sum(range(5, 51, 3))` prints 440.

> **Your turn:** Add up $2 + 5 + 8 + \dots + 20$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the step.** $5 - 2 = 3$.
> 2. **Count the steps.** $(20 - 2) \div 3 = 18 \div 3 = 6$.
> 3. **Count the terms.** $6 + 1 = 7$.
> 4. **Average the first and last.** $(2 + 20) \div 2 = 22 \div 2 = 11$.
> 5. **Multiply.** $7 \times 11 = 77$.
>
> **Answer:** 77.
>
> </details>

> **Notebook example:** Add up $3 + 6 + 12 + \dots + 1536$, where each term is double the
> one before.
>
> **What you need:** a **geometric series** multiplies by the same **ratio** r each
> time. For ratio 2 there is a neat fact: $1 + 2 + 4 + \dots + 2^m = 2^{m+1} - 1$ (one
> less than the next power of two). It comes from the **subtract trick**: call the sum
> S, double it, and subtract; everything cancels except the two ends.
>
> **Plan:** pull out the common factor 3, sum the powers of two, multiply back.
>
> 1. **Find the ratio.** $6 \div 3 = 2$ (and $12 \div 6 = 2$).
> 2. **Pull out the common factor.** Every term is 3 times a power of two:
>    $3(1 + 2 + 4 + \dots + 512)$.
> 3. **Find the last power.** $1536 \div 3 = 512$, and $512 = 2^9$. So the bracket is
>    $1 + 2 + \dots + 2^9$.
> 4. **Set up the subtract trick.** Call the bracket $S'$. Then
>    $2S' = 2 + 4 + \dots + 2^9 + 2^{10}$.
> 5. **Subtract.** In $2S' - S'$ every middle term appears once with $+$ and once with
>    $-$ and cancels. What is left: $2^{10} - 1$. And $2S' - S' = S'$, so
>    $S' = 2^{10} - 1$.
> 6. **Do the arithmetic.** $2^{10} = 1024$, and $1024 - 1 = 1023$.
> 7. **Multiply back the 3.** $3 \times 1023 = 3069$.
>
> **Answer:** $3 + 6 + 12 + \dots + 1536 = 3069$.
>
> **Check:** the last term, 1536, is just over half of 3069. That is the "last term
> dominates" rule for ratio 2: the last term is bigger than all the others put together.
> In Python, `sum(3 * 2**i for i in range(10))` prints 3069. ✓

> **Your turn:** Add up $5 + 10 + 20 + 40 + 80$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the ratio.** $10 \div 5 = 2$.
> 2. **Pull out the common factor.** $5(1 + 2 + 4 + 8 + 16)$.
> 3. **Find the last power.** $16 = 2^4$.
> 4. **Use the powers-of-two fact.** $1 + \dots + 2^4 = 2^5 - 1 = 32 - 1 = 31$.
> 5. **Multiply back the 5.** $5 \times 31 = 155$.
>
> **Answer:** 155.
>
> </details>

> **Notebook example:** Add up $1 + \frac13 + \frac19 + \frac{1}{27} + \dots$ forever.
>
> **What you need:** when the ratio r is between 0 and 1, the terms shrink so fast that
> the never-ending sum settles on a fixed number:
> $1 + r + r^2 + \dots = \frac{1}{1 - r}$. (It is the formula
> $\frac{1 - r^{n+1}}{1 - r}$ from above, with $r^{n+1}$ shrinking to 0.)
>
> **Plan:** find r, make sure it is below 1, put it into $\frac{1}{1 - r}$.
>
> 1. **Find the ratio.** $\frac13 \div 1 = \frac13$, so $r = \frac13$.
> 2. **Check the ratio is below 1.** $\frac13 < 1$, so the formula applies.
>    *Why:* with $r \ge 1$ the terms never shrink and the sum grows forever.
> 3. **Substitute.** $\frac{1}{1 - \frac13}$.
> 4. **Simplify the bottom.** $1 - \frac13 = \frac33 - \frac13 = \frac23$.
> 5. **Divide.** $1 \div \frac23 = \frac32 = 1.5$.
>    *Why:* dividing by a fraction is multiplying by it flipped over.
>
> **Answer:** the sum gets as close to 1.5 as you like, and never goes past it.
>
> **Check:** add the first few terms: 1, then 1.333, 1.444, 1.481, 1.494, 1.498. They
> creep up towards 1.5. ✓

> **Your turn:** Add up $1 + \frac14 + \frac{1}{16} + \dots$ forever.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the ratio.** $r = \frac14$, which is below 1.
> 2. **Substitute.** $\frac{1}{1 - \frac14}$.
> 3. **Simplify the bottom.** $1 - \frac14 = \frac34$.
> 4. **Divide.** $1 \div \frac34 = \frac43$.
>
> **Answer:** $\frac43 \approx 1.333$.
>
> </details>

### The amortized array, priced by a geometric series

A dynamic array doubles its capacity when full, copying every element. Copies happen
at sizes 1, 2, 4, …, up to n: a geometric series with $r = 2$, whose sum is under $2n$.
Add the n writes themselves and n appends cost under $3n$ steps: **O(1) amortized** per
append. Grow by a constant (+4) instead and the copies form an **arithmetic** series,
about $n^2/8$ in total — O(n) per append. The CS Fundamentals lab shows both:

<div class="lab" data-viz="cs-amortized"></div>

### The harmonic series

$$
H_n = 1 + \frac{1}{2} + \frac{1}{3} + \dots + \frac{1}{n} \approx \ln n + 0.5772
$$

It grows without bound, but only logarithmically: a million terms add up to about 14.4.

```python
import math
H = sum(1 / k for k in range(1, 10**6 + 1))
print(round(H, 4), round(math.log(10**6) + 0.5772156649, 4))   # → 14.3927 14.3927
```

It appears whenever the i-th step costs $n/i$: the sieve of Eratosthenes
($\sum_p n/p = O(n \log\log n)$ over primes), the loop
`for i in 1..n: for j in range(i, n, i)` ($O(n \log n)$), and the expected cost of
the coupon-collector problem (chapter 10).

## 2 · Logarithms: the Reason Fast Algorithms Are Fast

$\log_2 n$ answers: **how many times can you halve n before reaching 1?** Equivalently,
how many times do you double 1 to reach n. So it counts:

- the steps of binary search over n items;
- the height of a balanced binary tree with n nodes;
- the levels of merge sort's recursion;
- the number of bits needed to write n;
- the rounds of a tournament with n players.

**Try it: count the halvings.** Press *Play* with a million names and count the steps
(20). Now drag n to a billion: only 30. Switch on the log scale and the plunging curve
becomes a straight line — each halving is one equal step down.

<div class="lab" data-viz="math-log"></div>

> **Notebook example:** In the worst case, how many comparisons does binary search need
> on 5,000 sorted items?
>
> **What you need:** each comparison in binary search throws away half of the items
> still in play. So the number of comparisons is the number of times you can **halve**
> 5000 before 1 item is left, which is what $\log_2 5000$ measures. When the count is
> odd, the halves are uneven; in the worst case you keep the bigger half, so **round up**.
> $\lceil x \rceil$ ("ceiling of x") means x rounded up to a whole number.
>
> **Plan:** halve repeatedly, rounding up, and count the halvings; then confirm with
> powers of two.
>
> 1. **Halve the even part.** 5000 → 2500 → 1250 → 625. That is 3 halvings.
> 2. **Halve an odd number.** Half of 625 is 312.5. Round up: 313. That is 4 halvings.
>    *Why:* the worst case keeps the bigger half.
> 3. **Keep halving, rounding up.** 313 → 157 → 79 → 40 → 20 → 10 → 5 → 3 → 2 → 1.
> 4. **Count the arrows.** 3 in step 1, 1 in step 2, and 9 in step 3: $3 + 1 + 9 = 13$
>    halvings.
>
> **Answer:** at most 13 comparisons to search 5,000 items.
>
> **Check:** powers of two. $2^{12} = 4096$ is smaller than 5000, and $2^{13} = 8192$ is
> at least 5000, so $\log_2 5000$ is between 12 and 13, and rounding up gives
> $\lceil \log_2 5000 \rceil = 13$. ✓ In Python, `math.ceil(math.log2(5000))` prints 13.

> **Your turn:** In the worst case, how many comparisons does binary search need on 100
> sorted items?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Halve the even part.** 100 → 50 → 25.
> 2. **Halve an odd number.** Half of 25 is 12.5; round up to 13.
> 3. **Keep halving, rounding up.** 13 → 7 → 4 → 2 → 1.
> 4. **Count the arrows.** $2 + 1 + 4 = 7$.
>
> **Answer:** 7 comparisons. ($2^6 = 64 < 100 \le 128 = 2^7$.)
>
> </details>

> **Notebook example:** Any sorting algorithm that works by comparing two items at a
> time must, in the worst case, use at least how many comparisons to sort 5 items?
>
> **What you need:** before sorting, the 5 items could be in any of $5!$ orders, and
> the algorithm has to tell all of them apart. Each comparison has 2 possible outcomes
> (yes or no), so c comparisons can lead to at most $2^c$ different results. To tell
> all orders apart you need $2^c \ge$ (number of orders).
>
> **Plan:** count the orders, then find the smallest power of two that covers them.
>
> 1. **Count the possible orders.** $5! = 5 \cdot 4 \cdot 3 \cdot 2 \cdot 1$:
>    $5 \cdot 4 = 20$, $20 \cdot 3 = 60$, $60 \cdot 2 = 120$.
> 2. **Write the condition.** You need $2^c \ge 120$.
>    *Why:* with fewer than 120 possible results, two different input orders would get
>    the same treatment, and one of them would come out unsorted.
> 3. **Try c = 6.** $2^6 = 64$. Too small, since $64 < 120$.
> 4. **Try c = 7.** $2^7 = 128$. Enough, since $128 \ge 120$.
>
> **Answer:** at least 7 comparisons in the worst case. (Seven is actually achievable
> for 5 items.)
>
> **Check:** $\log_2 120 \approx 6.9$, which rounds up to 7. ✓ In Python,
> `math.ceil(math.log2(math.factorial(5)))` prints 7.

> **Your turn:** At least how many comparisons must any comparison sort use, in the
> worst case, for 3 items?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Count the possible orders.** $3! = 3 \cdot 2 \cdot 1 = 6$.
> 2. **Write the condition.** $2^c \ge 6$.
> 3. **Try c = 2.** $2^2 = 4$, too small.
> 4. **Try c = 3.** $2^3 = 8$, enough.
>
> **Answer:** at least 3 comparisons.
>
> </details>

### Logarithm facts you will use

| Fact | Consequence |
|---|---|
| $\log(ab) = \log a + \log b$ | multiplying becomes adding; log-probabilities in ML avoid underflow |
| $\log(a^k) = k \log a$ | $\log(n^2) = 2 \log n = O(\log n)$ |
| $\log_b n = \frac{\log n}{\log b}$ | the base is a constant factor, so O(log n) needs no base |
| $\log_2 (2^{10}) = 10$, $2^{10} \approx 10^3$ | $\log_2$ of a million ≈ 20, of a billion ≈ 30 |
| $\log(n!) = \Theta(n \log n)$ | comparison sorting needs $\Omega(n \log n)$ comparisons |

The last line deserves a closer look. $n! \le n^n$ gives $\log n! \le n \log n$, and
the largest half of the factors are each at least $n/2$, so $n! \ge (n/2)^{n/2}$ and
$\log n! \ge \frac{n}{2}\log\frac{n}{2}$. Both bounds are $\Theta(n \log n)$.
(**Stirling's formula** is the precise version: $\ln n! \approx n \ln n - n$.)

> **Key idea:** A comparison sort must distinguish all $n!$ possible input orders, and
> each comparison has 2 outcomes, so it needs at least $\log_2 n!$ comparisons in the
> worst case — and $\log_2 n! = \Theta(n \log n)$. That is a proof that **no comparison
> sort can beat O(n log n)**, using only counting and logarithms.

```python
import math
n = 1000
print(round(math.log2(math.factorial(n))), round(n * math.log2(n)))   # → 8529 9966
print(round(n * math.log2(n) - n * math.log2(math.e)))              # → 8523
```

$\log_2 1000! \approx 8529$: any comparison sort needs at least that many comparisons
for some input of 1000 items. Merge sort uses at most about $n \log_2 n \approx 9966$.
Stirling's approximation, $n\log_2 n - n\log_2 e \approx 8523$, is within 0.1%.

## 3 · Growth Rates, Precisely: O, Ω and Θ

> **Definition:** $f(n) = O(g(n))$ ("f is big-O of g") if there are constants $c > 0$
> and $n_0$ such that $f(n) \le c \cdot g(n)$ for all $n \ge n_0$. It is an **upper
> bound** on growth, ignoring constant factors and small n.

| Notation | Meaning | Analogy |
|---|---|---|
| $f = O(g)$ | f grows **at most** as fast as g | $\le$ |
| $f = \Omega(g)$ | f grows **at least** as fast as g | $\ge$ |
| $f = \Theta(g)$ | both: same growth rate | $=$ |
| $f = o(g)$ | f grows **strictly slower** ($f/g \to 0$) | $<$ |

> **Worked example:** Show $3n^2 + 10n + 7 = O(n^2)$. For $n \ge 1$: $10n \le 10n^2$
> and $7 \le 7n^2$, so $3n^2 + 10n + 7 \le 20n^2$. Take $c = 20$, $n_0 = 1$. ∎ It is also
> $\Omega(n^2)$ (it is at least $3n^2$), so it is $\Theta(n^2)$.

**The limit test** is usually faster: if $\lim_{n\to\infty} f(n)/g(n)$ is a finite
positive number, $f = \Theta(g)$; if it is 0, $f = o(g)$; if it is ∞, $f = \omega(g)$.

The hierarchy you should know by heart, slowest to fastest:

$$
1 \;<\; \log n \;<\; \sqrt{n} \;<\; n \;<\; n \log n \;<\; n^2 \;<\; n^3 \;<\; 2^n \;<\; n! \;<\; n^n
$$

Any power of $\log n$ is eventually beaten by any power of n ($(\log n)^{100} = o(n^{0.01})$),
and any polynomial by any exponential.

> **Watch out:** "O" is an upper bound, so saying binary search is $O(n)$ is *true* but
> useless. When people say "O" in interviews they almost always mean Θ — a tight bound.
> Say "Θ" or "tight" when precision matters, and state best, average and worst cases
> separately (quicksort is Θ(n log n) on average and Θ(n²) in the worst case).

## 4 · Recurrences: Recursion Written as Maths

A recursive function's running time is naturally a recurrence. The task is to solve it
— find an explicit formula or at least its Θ.

### Unrolling (the iteration method)

Substitute the recurrence into itself until a pattern appears.

> **Worked example: the Tower of Hanoi.** Moving n disks: move $n-1$ disks out of the
> way, move the biggest, move the $n-1$ back on top. $T(n) = 2T(n-1) + 1$, $T(1) = 1$.
> Unroll:
>
> $T(n) = 2T(n-1) + 1 = 4T(n-2) + 2 + 1 = 8T(n-3) + 4 + 2 + 1 = \dots = 2^{n-1}T(1) + (2^{n-2} + \dots + 1)$
>
> $= 2^{n-1} + 2^{n-1} - 1 = 2^n - 1.$ Then **prove it by induction** (chapter 03): it
> holds at n = 1, and $2(2^{k} - 1) + 1 = 2^{k+1} - 1$.

```python
def hanoi(n, src="A", dst="C", via="B", moves=None):
    moves = [] if moves is None else moves
    if n:
        hanoi(n - 1, src, via, dst, moves)
        moves.append((src, dst))
        hanoi(n - 1, via, dst, src, moves)
    return moves

print([len(hanoi(n)) for n in range(1, 11)])   # → [1, 3, 7, 15, 31, 63, 127, 255, 511, 1023]
```

A 64-disk tower at one move per second takes $2^{64} - 1$ seconds — about 585 billion
years.

### Common recurrences to recognise on sight

| Recurrence | Solution | Where |
|---|---|---|
| $T(n) = T(n-1) + O(1)$ | $\Theta(n)$ | linear recursion over a list |
| $T(n) = T(n-1) + O(n)$ | $\Theta(n^2)$ | selection sort; quicksort's worst case |
| $T(n) = T(n/2) + O(1)$ | $\Theta(\log n)$ | binary search |
| $T(n) = T(n/2) + O(n)$ | $\Theta(n)$ | quickselect (expected), a geometric series |
| $T(n) = 2T(n/2) + O(1)$ | $\Theta(n)$ | tree traversal |
| $T(n) = 2T(n/2) + O(n)$ | $\Theta(n \log n)$ | merge sort |
| $T(n) = 2T(n-1) + O(1)$ | $\Theta(2^n)$ | Tower of Hanoi, all subsets |
| $T(n) = T(n-1) + T(n-2) + O(1)$ | $\Theta(\varphi^n) \approx \Theta(1.618^n)$ | naive Fibonacci |

## 5 · Divide and Conquer: Recursion Trees and the Master Theorem

For recurrences of the form

$$
T(n) = a \, T\!\left(\frac{n}{b}\right) + f(n)
$$

(a subproblems, each of size n/b, plus f(n) work to split and combine), draw the
**recursion tree**: level k has $a^k$ nodes, each doing $f(n/b^k)$ work. The total is
a sum over levels — and the answer depends on whether the per-level work shrinks,
stays level, or grows as you go down. That is the geometric-series trichotomy from
§1 again:

| Case | Compare f(n) with $n^{\log_b a}$ | Work per level | Answer |
|---|---|---|---|
| 1 | $f(n) = O(n^{\log_b a - \epsilon})$ — smaller | grows downward; leaves dominate | $\Theta(n^{\log_b a})$ |
| 2 | $f(n) = \Theta(n^{\log_b a})$ — equal | the same on every level | $\Theta(n^{\log_b a} \log n)$ |
| 3 | $f(n) = \Omega(n^{\log_b a + \epsilon})$ — bigger | shrinks downward; root dominates | $\Theta(f(n))$ |

$n^{\log_b a}$ is the number of leaves of the recursion tree. Merge sort ($a = b = 2$,
$f = n$): $n^{\log_2 2} = n$ equals f, case 2, $\Theta(n \log n)$. Binary search
($a = 1, b = 2, f = 1$): $n^0 = 1$, case 2, $\Theta(\log n)$.

**Try it: see the levels.** The CS Fundamentals recursion-tree lab draws the work at
every level for a chosen a, b and f(n), and names the case.

<div class="lab" data-viz="cs-master"></div>

> **Worked example: Karatsuba multiplication.** Multiplying two n-digit numbers the
> school way is $\Theta(n^2)$. Karatsuba splits each number in half and gets away with
> **3** half-size multiplications instead of 4: $T(n) = 3T(n/2) + O(n)$. Leaves:
> $n^{\log_2 3} \approx n^{1.585}$, which beats f(n) = n — case 1:
> $\Theta(n^{1.585})$. Python's own `int` multiplication switches to Karatsuba above
> about 70 machine digits. One fewer subproblem changed the exponent.

## 6 · Linear Recurrences and the Golden Ratio

The Fibonacci numbers: $F_0 = 0$, $F_1 = 1$, $F_n = F_{n-1} + F_{n-2}$.

**Why naive recursion is exponential.** `fib(n)` calls `fib(n-1)` and `fib(n-2)`, which
call… The number of calls satisfies nearly the same recurrence as $F_n$ itself, so it
grows like $F_n$:

```python
calls = 0
def fib(n):
    global calls
    calls += 1
    return n if n < 2 else fib(n - 1) + fib(n - 2)

fib(25)
print(calls)   # → 242785
```

A quarter of a million calls to compute the 25th number — because the same subproblems
are recomputed over and over. Memoisation computes each once: $\Theta(n)$.

**The closed form.** For a **linear recurrence with constant coefficients** such as
$F_n = F_{n-1} + F_{n-2}$, try $F_n = x^n$. Substituting gives the **characteristic
equation** $x^2 = x + 1$, with roots

$$
\varphi = \frac{1 + \sqrt{5}}{2} \approx 1.618, \qquad \psi = \frac{1 - \sqrt{5}}{2} \approx -0.618
$$

Every solution is a combination $A\varphi^n + B\psi^n$; fitting $F_0 = 0, F_1 = 1$ gives
**Binet's formula**:

$$
F_n = \frac{\varphi^n - \psi^n}{\sqrt{5}}
$$

Since $\lvert\psi\rvert < 1$, the $\psi^n$ term vanishes: $F_n$ is the nearest integer to
$\varphi^n / \sqrt{5}$. So Fibonacci — and naive `fib` — grows like $1.618^n$.

```python
import math
phi = (1 + math.sqrt(5)) / 2

def fib_iter(n):
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a

print(round(phi**30 / math.sqrt(5)), fib_iter(30))    # → 832040 832040
first_bad = next(n for n in range(200) if round(phi**n / math.sqrt(5)) != fib_iter(n))
print(first_bad)                                       # → 71
```

> **Precision note:** Binet's formula is exact in real arithmetic but not in floating
> point: with float64 it first gives a wrong answer at n = 71, where $F_{71}$ has 15
> digits and float64's ~16 significant digits are exhausted by the rounding in
> $\varphi^n$. Closed forms are great for analysis; for exact large answers use integer
> methods.

> **Notebook example:** (Warm-up.) Find a formula for $a_n = 3a_{n-1}$ with $a_0 = 2$.
>
> **What you need:** a **recurrence** gives each term from earlier ones; **solving** it
> means finding an explicit formula, so you can jump straight to any $a_n$ without
> computing all the terms before it. The standard first move is to **guess**
> $a_n = x^n$ for some unknown number x, put the guess into the recurrence, and see
> which x makes it work.
>
> **Plan:** list a few terms, guess $x^n$, find x, then scale to fit the starting value.
>
> 1. **List a few terms.** $a_0 = 2$, $a_1 = 3 \cdot 2 = 6$, $a_2 = 3 \cdot 6 = 18$,
>    $a_3 = 3 \cdot 18 = 54$.
> 2. **Substitute the guess.** Put $a_n = x^n$ into $a_n = 3a_{n-1}$: $x^n = 3x^{n-1}$.
> 3. **Divide by $x^{n-1}$.** $x = 3$.
>    *Why:* $x^n \div x^{n-1} = x$, and dividing both sides by the same thing keeps them
>    equal.
> 4. **Allow a constant in front.** $a_n = A \cdot 3^n$ also satisfies the recurrence,
>    for any number A.
>    *Why:* multiplying every term by A does not change the rule "each term is 3 times
>    the last".
> 5. **Fit the start.** At $n = 0$: $A \cdot 3^0 = A \cdot 1 = A$, and this must equal
>    $a_0 = 2$. So $A = 2$.
>
> **Answer:** $a_n = 2 \cdot 3^n$.
>
> **Check:** $n = 3$ gives $2 \cdot 27 = 54$, matching step 1. ✓

> **Your turn:** Find a formula for $a_n = 2a_{n-1}$ with $a_0 = 5$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Substitute the guess.** $x^n = 2x^{n-1}$.
> 2. **Divide by the smaller power.** $x = 2$.
> 3. **Allow a constant in front.** $a_n = A \cdot 2^n$.
> 4. **Fit the start.** $n = 0$: $A = 5$.
>
> **Answer:** $a_n = 5 \cdot 2^n$ (5, 10, 20, 40, …).
>
> </details>

> **Notebook example:** Solve $a_n = 5a_{n-1} - 6a_{n-2}$ with $a_0 = 0$ and $a_1 = 1$.
>
> **What you need:** the same guess, $a_n = x^n$, now gives a quadratic, the
> **characteristic equation**, with two solutions (**roots**) $r_1$ and $r_2$. Any mix
> $a_n = A \cdot r_1^n + B \cdot r_2^n$ obeys the recurrence (the **general solution**).
> Then pick A and B so the first two terms come out right. To **factor**
> $x^2 - 5x + 6$, look for two numbers that multiply to 6 and add to $-5$.
>
> **Plan:** get the characteristic equation, find its two roots, write the general
> solution, then fit A and B to $a_0$ and $a_1$.
>
> 1. **Substitute the guess.** $x^n = 5x^{n-1} - 6x^{n-2}$.
> 2. **Divide by the smallest power, $x^{n-2}$.** $x^2 = 5x - 6$.
>    *Why:* this strips out the n, leaving an ordinary equation in x.
> 3. **Move everything to one side.** $x^2 - 5x + 6 = 0$. This is the characteristic
>    equation.
> 4. **Factor.** $-2$ and $-3$ multiply to $+6$ and add to $-5$, so
>    $(x - 2)(x - 3) = 0$.
> 5. **Read off the roots.** A product is 0 only if one factor is 0: $x = 2$ or $x = 3$.
> 6. **Write the general solution.** $a_n = A \cdot 2^n + B \cdot 3^n$.
> 7. **Fit $a_0 = 0$.** Put $n = 0$: $A \cdot 1 + B \cdot 1 = 0$, so $A + B = 0$, which
>    means $A = -B$.
> 8. **Fit $a_1 = 1$.** Put $n = 1$: $2A + 3B = 1$.
> 9. **Substitute $A = -B$.** $2(-B) + 3B = 1$, so $-2B + 3B = 1$, so $B = 1$.
> 10. **Find A.** $A = -B = -1$.
> 11. **Write the formula.** $a_n = -1 \cdot 2^n + 1 \cdot 3^n = 3^n - 2^n$.
>
> **Answer:** $a_n = 3^n - 2^n$. It grows like $3^n$, the larger root: that is how you
> read off the growth rate of any linear recurrence.
>
> **Check:** run the recurrence. $a_2 = 5 \cdot 1 - 6 \cdot 0 = 5$, and
> $3^2 - 2^2 = 9 - 4 = 5$. ✓ $a_3 = 5 \cdot 5 - 6 \cdot 1 = 25 - 6 = 19$, and
> $3^3 - 2^3 = 27 - 8 = 19$. ✓

> **Your turn:** Solve $a_n = 3a_{n-1} - 2a_{n-2}$ with $a_0 = 0$ and $a_1 = 1$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Substitute the guess and divide.** $x^2 = 3x - 2$.
> 2. **Move everything to one side.** $x^2 - 3x + 2 = 0$.
> 3. **Factor.** $-1$ and $-2$ multiply to 2 and add to $-3$: $(x - 1)(x - 2) = 0$.
> 4. **Write the general solution.** $a_n = A \cdot 1^n + B \cdot 2^n = A + B \cdot 2^n$.
> 5. **Fit the start.** $n = 0$: $A + B = 0$. $n = 1$: $A + 2B = 1$. Subtracting the
>    first from the second: $B = 1$, so $A = -1$.
>
> **Answer:** $a_n = 2^n - 1$: 0, 1, 3, 7, 15, …, the Tower of Hanoi numbers.
>
> </details>

### O(log n) Fibonacci with a matrix power

The recurrence is a linear map on the pair $(F_{n+1}, F_n)$:

$$
\begin{pmatrix} F_{n+1} \\ F_{n} \end{pmatrix} = \begin{pmatrix} 1 & 1 \\ 1 & 0 \end{pmatrix}\begin{pmatrix} F_{n} \\ F_{n-1} \end{pmatrix}
\quad\Rightarrow\quad
\begin{pmatrix} 1 & 1 \\ 1 & 0 \end{pmatrix}^{n} = \begin{pmatrix} F_{n+1} & F_n \\ F_n & F_{n-1} \end{pmatrix}
$$

A matrix power can be computed by **repeated squaring** in $O(\log n)$ multiplications
(the same fast exponentiation as $a^n \bmod m$ in chapter 07). This works for **any**
linear recurrence, which is how problems like "count the ways, n up to $10^{18}$,
modulo $10^9 + 7$" are solved.

```python
def mat_mult(A, B, mod):
    return [[sum(A[i][k] * B[k][j] for k in range(2)) % mod for j in range(2)] for i in range(2)]

def fib_matrix(n, mod=10**9 + 7):
    result, base = [[1, 0], [0, 1]], [[1, 1], [1, 0]]
    while n:
        if n & 1:
            result = mat_mult(result, base, mod)
        base = mat_mult(base, base, mod)
        n >>= 1
    return result[0][1]

print(fib_matrix(90, 10**30), fib_iter(90))   # → 2880067194370816120 2880067194370816120
print(fib_matrix(10**18))                     # → 209783453
```

The last line computes the $10^{18}$-th Fibonacci number modulo $10^9 + 7$ in about 60
squarings.

## 7 · Exponential Growth in Running Systems

**Exponential backoff.** A client retrying a failing call waits 1 s, 2 s, 4 s, 8 s, …
— a geometric sequence. The total wait after k retries is $2^k - 1$ seconds (a
geometric sum), so a handful of retries covers a long outage without hammering the
server. Real systems add a **cap** (never wait more than, say, 30 s) and **jitter**
(randomise each wait) so thousands of clients that failed together do not retry in
lock-step.

```python
import random
def backoff_waits(retries, base=0.1, cap=5.0, seed=1):
    rnd = random.Random(seed)
    return [round(rnd.uniform(0, min(cap, base * 2**k)), 2) for k in range(retries)]   # "full jitter"

print([min(5.0, 0.1 * 2**k) for k in range(8)])   # → [0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 5.0, 5.0]
print(len(backoff_waits(8)))                       # → 8
```

**Doubling time.** Anything growing by p% per period doubles after about $70/p$ periods
(because $\ln 2 \approx 0.693$ and $\ln(1 + p/100) \approx p/100$). Traffic growing 10%
a month doubles in about 7 months — capacity planning in one line.

```python
import math
print(round(math.log(2) / math.log(1.10), 2))   # → 7.27
```

> **Notebook example:** A client retries a failing call with exponential backoff: it
> waits 1 s before the first retry, and doubles the wait each time, but never waits more
> than 30 s (the **cap**). How long has it waited in total after 8 retries?
>
> **What you need:** **exponential backoff** means each wait is double the last: 1, 2,
> 4, 8, … The **cap** replaces any wait above it with the cap itself. The doubling part
> is a geometric series: $1 + 2 + 4 + \dots + 2^{k-1} = 2^k - 1$.
>
> **Plan:** list all 8 waits, applying the cap, then add the doubling part and the capped
> part separately.
>
> 1. **List the doubling waits.** 1, 2, 4, 8, 16. That is 5 waits.
> 2. **Apply the cap.** The next wait would be $16 \times 2 = 32$, which is more than 30,
>    so it becomes 30. Every later wait is capped too.
> 3. **Fill up to 8 waits.** $8 - 5 = 3$ capped waits: 30, 30, 30.
> 4. **Add the doubling part.** $1 + 2 = 3$, $3 + 4 = 7$, $7 + 8 = 15$, $15 + 16 = 31$.
>    *Why it is quick:* this is $2^5 - 1 = 32 - 1 = 31$, the geometric-sum shortcut.
> 5. **Add the capped part.** $3 \times 30 = 90$.
> 6. **Add the two parts.** $31 + 90 = 121$ seconds.
>
> **Answer:** 121 seconds, about 2 minutes, of total waiting after 8 retries.
>
> **Check:** in Python, `sum(min(30, 2**k) for k in range(8))` prints 121. ✓

> **Your turn:** Backoff starts at 1 s, doubles, and is capped at 10 s. What is the total
> wait after 6 retries?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **List the doubling waits.** 1, 2, 4, 8.
> 2. **Apply the cap.** The next would be 16, more than 10, so 10.
> 3. **Fill up to 6 waits.** $6 - 4 = 2$ capped waits: 10, 10.
> 4. **Add the doubling part.** $1 + 2 + 4 + 8 = 15$ ($= 2^4 - 1$).
> 5. **Add the capped part.** $2 \times 10 = 20$.
> 6. **Add the two parts.** $15 + 20 = 35$ seconds.
>
> **Answer:** 35 seconds.
>
> </details>

> **Notebook example:** Your traffic grows 5% every month. How many months until it
> doubles?
>
> **What you need:** growing 5% means multiplying by $1.05$ each month, so after t
> months traffic is $1.05^t$ times bigger. Doubling means $1.05^t = 2$. Quick estimate,
> the **rule of 70**: doubling takes about $70 \div p$ periods at p% growth. Exact answer
> uses the **natural log** ln (the `math.log` button), whose key property is that it
> brings a power down in front: $\ln(a^t) = t \ln a$.
>
> **Plan:** estimate with the rule of 70, then solve $1.05^t = 2$ exactly with logs.
>
> 1. **Write the equation.** $1.05^t = 2$.
> 2. **Estimate with the rule of 70.** $70 \div 5 = 14$ months.
> 3. **Take ln of both sides.** $\ln(1.05^t) = \ln 2$.
>    *Why:* doing the same thing to both sides keeps them equal, and ln can pull the
>    unknown t out of the exponent.
> 4. **Bring the power down.** $t \cdot \ln 1.05 = \ln 2$.
> 5. **Divide to get t alone.** $t = \frac{\ln 2}{\ln 1.05}$.
> 6. **Look up the logs.** $\ln 2 \approx 0.6931$ and $\ln 1.05 \approx 0.0488$.
> 7. **Divide.** $0.6931 \div 0.0488 \approx 14.2$ months.
>
> **Answer:** traffic doubles in about 14.2 months. The rule of 70 said 14, off by only
> 0.2 months.
>
> **Check:** $1.05^{14} \approx 1.98$ (just under double) and $1.05^{15} \approx 2.08$
> (just over), so the answer must be a little above 14. ✓ In Python,
> `math.log(2) / math.log(1.05)` prints about 14.21.

> **Your turn:** Something grows 7% per year. Estimate the doubling time with the rule of
> 70, then find it exactly ($\ln 1.07 \approx 0.0677$).
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the equation.** $1.07^t = 2$.
> 2. **Estimate with the rule of 70.** $70 \div 7 = 10$ years.
> 3. **Take ln and bring the power down.** $t \cdot \ln 1.07 = \ln 2$.
> 4. **Divide to get t alone.** $t = 0.6931 \div 0.0677 \approx 10.2$ years.
>
> **Answer:** about 10.2 years; the rule of 70 gave 10.
>
> </details>

## Common Mistakes

1. **Adding complexities that should multiply** (nested loops multiply; sequential
   loops add).
2. **Assuming a halving recursion is always Θ(log n).** $T(n) = T(n/2) + n$ is Θ(n):
   the first level dominates.
3. **Applying the master theorem outside its form** — e.g. $T(n) = T(n-1) + n$ is not
   $aT(n/b) + f(n)$; unroll it instead.
4. **Writing the base of a logarithm inside O**, or treating $\log(n^2)$ as bigger than
   $O(\log n)$.
5. **Saying O when you mean Θ**, or forgetting to separate best, average and worst
   cases.
6. **Trusting floating-point closed forms for exact integer answers.**

## Check Yourself

**1.** What does `for i in range(n): j = 1; while j < n: j *= 2` cost?

<details>
<summary>Open the answer</summary>

The inner loop doubles j until it reaches n: about $\log_2 n$ iterations. The outer loop
runs n times, so $\Theta(n \log n)$.

</details>

**2.** Solve $T(n) = 4T(n/2) + n$ and $T(n) = 2T(n/2) + n^2$.

<details>
<summary>Open the answer</summary>

First: $n^{\log_2 4} = n^2$ leaves, beating $f(n) = n$ — case 1, $\Theta(n^2)$.
Second: $n^{\log_2 2} = n$ leaves, beaten by $f(n) = n^2$ — case 3 (the regularity
condition holds), $\Theta(n^2)$: the root's work dominates.

</details>

**3.** Is $2^{n+1} = O(2^n)$? Is $2^{2n} = O(2^n)$?

<details>
<summary>Open the answer</summary>

$2^{n+1} = 2 \cdot 2^n$: yes, with c = 2. $2^{2n} = 4^n$, and $4^n / 2^n = 2^n \to \infty$:
no. Constant factors are free, but a constant in the **exponent** changes the growth
rate.

</details>

**4.** Why is building a binary heap from n items O(n), not O(n log n)?

<details>
<summary>Open the answer</summary>

Sift-down costs the height of the node. About n/2 nodes are leaves (height 0), n/4 have
height 1, n/8 height 2, … The total is $\sum_h \frac{n}{2^{h+1}} \cdot h = O(n)$, because
$\sum_h h/2^h$ converges (to 2). Most nodes are near the bottom, where sifting is cheap.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Arithmetic and geometric sums; $\log_2$ as counting halvings; the growth hierarchy; O as "grows at most like" |
| **Interview-ready** | Price any loop nest; the table of common recurrences; the master theorem with recursion-tree intuition; amortized doubling; the $\Omega(n \log n)$ sorting lower bound; memoisation vs naive recursion |
| **Going deeper** | Formal O/Ω/Θ proofs and the limit test; characteristic equations and Binet; matrix exponentiation for linear recurrences; Stirling's formula; Akra–Bazzi for uneven splits |

## Checklist

- [ ] I can sum arithmetic and geometric series and say which term dominates.
- [ ] I can explain log n as "number of halvings" and list five places it appears.
- [ ] I can state the definition of O with c and $n_0$, and prove a simple bound.
- [ ] I can solve recurrences by unrolling and by the master theorem, and I recognise the common ones on sight.
- [ ] I can prove comparison sorting needs $\Omega(n \log n)$.
- [ ] I can compute Fibonacci in O(n) and O(log n), and explain why naive recursion is exponential.
