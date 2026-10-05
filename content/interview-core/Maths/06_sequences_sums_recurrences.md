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

> **Notebook example:** Add $5 + 8 + 11 + \dots + 50$, then $3 + 6 + 12 + \dots + 1536$,
> then $1 + \frac13 + \frac19 + \dots$ forever.
>
> 1. **Arithmetic.** Count the terms: the step is 3, so there are
>    $\frac{50 - 5}{3} + 1 = 16$ terms. The average of the first and last is
>    $\frac{5 + 50}{2} = 27.5$. Sum $= 16 \times 27.5 = 440$.
> 2. **Geometric.** The ratio is 2 and $1536 = 3 \cdot 2^9$, so the sum is
>    $S = 3(1 + 2 + \dots + 2^9)$.
> 3. Use the subtract trick: $2S' - S' = 2^{10} - 1$, so $S' = 1023$ and $S = 3 \times 1023 = 3069$.
> 4. **Infinite, ratio below 1:** $\frac{1}{1 - r} = \frac{1}{1 - \frac13} = \frac{3}{2}$.
>
> **Answer:** 440, 3069 and 1.5. **Check** step 3: the last term, 1536, is just over
> half the total, 3069. That is the "last term dominates" rule for r = 2.

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
> on 5,000 sorted items? And at least how many comparisons must any sort use for 5
> items?
>
> 1. Halve until 1 item is left, rounding up: 5000 → 2500 → 1250 → 625 → 313 → 157 →
>    79 → 40 → 20 → 10 → 5 → 3 → 2 → 1.
> 2. Count the arrows: **13** halvings.
> 3. Check with powers of two: $2^{12} = 4096 < 5000 \le 8192 = 2^{13}$, so
>    $\lceil \log_2 5000 \rceil = 13$. ✓
> 4. Sorting 5 items must tell apart $5! = 120$ orders. Each comparison has 2 outcomes,
>    so you need $2^c \ge 120$. $2^6 = 64$ is too small and $2^7 = 128$ is enough.
>
> **Answer:** 13 comparisons, and at least 7. (Seven is actually achievable for 5 items.)

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

> **Notebook example:** Solve $a_n = 5a_{n-1} - 6a_{n-2}$ with $a_0 = 0$ and $a_1 = 1$.
>
> 1. Try $a_n = x^n$: $x^n = 5x^{n-1} - 6x^{n-2}$. Divide by $x^{n-2}$ to get the
>    characteristic equation $x^2 - 5x + 6 = 0$.
> 2. Factor: $(x - 2)(x - 3) = 0$, so the roots are 2 and 3.
> 3. General solution: $a_n = A \cdot 2^n + B \cdot 3^n$.
> 4. Fit the start: $n = 0$ gives $A + B = 0$. $n = 1$ gives $2A + 3B = 1$. Substitute
>    $A = -B$: $-2B + 3B = 1$, so $B = 1$ and $A = -1$.
> 5. $a_n = 3^n - 2^n$.
>
> **Check** against the recurrence: $a_2 = 5 \cdot 1 - 6 \cdot 0 = 5$, and
> $3^2 - 2^2 = 5$ ✓. $a_3 = 5 \cdot 5 - 6 \cdot 1 = 19$, and $27 - 8 = 19$ ✓. It grows
> like $3^n$, the larger root. That is how you read off the growth rate of any linear
> recurrence.

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

> **Notebook example:** A client retries with backoff starting at 1 s, doubling, capped at
> 30 s. How long has it waited in total after 8 retries? And how long until 5% monthly
> growth doubles your traffic?
>
> 1. The waits double until they hit the cap: 1, 2, 4, 8, 16, then 32 would exceed 30,
>    so 30, 30, 30.
> 2. Total: $1 + 2 + 4 + 8 + 16 = 31$ (that is $2^5 - 1$), plus $3 \times 30 = 90$, so
>    **121 s**.
> 3. Rule of 70: $70 / 5 = 14$ months.
> 4. Exact: solve $1.05^t = 2$, so $t = \frac{\ln 2}{\ln 1.05} = \frac{0.6931}{0.0488} \approx 14.2$
>    months.
>
> **Answer:** 121 s of waiting, and about 14 months to double. The rule of 70 was off by
> only 0.2 months.

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
