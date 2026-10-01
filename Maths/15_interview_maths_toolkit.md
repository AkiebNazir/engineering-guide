# The Interview Maths Toolkit — Geometry, Classic Tricks, Estimation and a Question Bank

This chapter turns the module into interview performance. It covers the computational
geometry that shows up in coding rounds (and is almost always solved with one cross
product), the maths behind the classic "trick" problems — each one a chapter of this
module in disguise — the back-of-the-envelope arithmetic of system design interviews,
and a question bank tagged by level with layered answers. Use it last, as a review, or
first, to find out which chapters you need.

**Where this fits:** Part 4 · Maths behind computing, chapter 15 of 15. **Builds on:** [05 Counting, permutations and combinations](05_counting_and_combinatorics.md) (counting); [06 Sequences, sums and recurrences](06_sequences_sums_recurrences.md) (complexity maths); [07 Number theory](07_number_theory.md) (number theory); [08 Graph theory](08_graph_theory.md) (graphs); [10 Probability](10_probability.md) (probability); [14 Automata, computability and complexity](14_automata_computability_complexity.md) (hardness). **Next in order:** back to the [start page](README.md) to review your weakest chapters.

## Where You Will Use This

| Interview moment | Section |
|---|---|
| "Do these segments intersect?", "area of this polygon", "points on the hull" | §1 Geometry |
| "Find the missing number / the duplicate / the majority element in O(1) space" | §2 Classic tricks |
| "Shuffle fairly", "sample from a stream", "count trailing zeros of n!" | §2 |
| "How many servers / how much storage for this design?" | §3 Estimation |
| "Explain / prove / derive…" follow-ups | §4 Question bank |

## 1 · Computational Geometry With One Tool

### Points are vectors

A point $(x, y)$ is a vector from the origin, so chapter 09 applies: differences of
points are directions, and the dot and cross products answer almost every question.

- **Distance:** $\sqrt{dx^2 + dy^2}$ — but to **compare** distances, compare the squares
  and skip the square root (faster, and exact on integers).
- **Dot product** $a \cdot b = a_x b_x + a_y b_y$: angle information (positive: less
  than 90°).
- **2-D cross product** $a \times b = a_x b_y - a_y b_x$: orientation — the heart of this
  section.

### Orientation: left turn, right turn, straight

> **Key idea:** For points A, B, C, let $\text{cross} = (B - A) \times (C - A)$.
> Positive: A→B→C turns **left** (counter-clockwise). Negative: **right**. Zero:
> **collinear**. Its absolute value is twice the area of triangle ABC. It uses only
> multiplication and subtraction, so on integer coordinates it is **exact**.

This is the 2×2 determinant from chapter 09: the signed area of the parallelogram
spanned by $B - A$ and $C - A$.

**Try it: one test, three problems.** Drag A, B and C and watch the sign of the cross
product flip as C crosses the line AB. Switch to *do two segments cross?* (four
orientation tests) and *polygon area and convexity* (the shoelace formula; a vertex
turning the wrong way is ringed and the polygon is no longer convex).

<div class="lab" data-viz="math-geometry"></div>

```python
def cross(o, a, b):
    return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

print(cross((0, 0), (4, 0), (2, 3)), cross((0, 0), (4, 0), (2, -3)), cross((0, 0), (4, 0), (8, 0)))   # → 12 -12 0
```

> **Notebook example:** For A = (1, 1), B = (4, 2), C = (2, 4), which way does A → B → C
> turn, and what is the triangle's area?
>
> 1. $B - A = (3, 1)$ and $C - A = (1, 3)$.
> 2. Cross product: $3 \times 3 - 1 \times 1 = 9 - 1 = 8$.
> 3. It is positive, so the turn is **left** (counter-clockwise).
> 4. The triangle's area is half the absolute value: $8 / 2 = 4$.
>
> **Answer:** a left turn, with area 4. Only integer multiplications were used, so the
> answer is exact.

### Segment intersection

Segments PQ and RS properly cross exactly when R and S are on opposite sides of line PQ
**and** P and Q are on opposite sides of line RS. The touching and collinear cases
(a zero cross product) need an "is the point within the segment's bounding box" check —
that is where most bugs live.

```python
def on_segment(p, q, r):          # r collinear with pq: is it between them?
    return min(p[0], q[0]) <= r[0] <= max(p[0], q[0]) and min(p[1], q[1]) <= r[1] <= max(p[1], q[1])

def segments_intersect(p, q, r, s):
    d1, d2 = cross(p, q, r), cross(p, q, s)
    d3, d4 = cross(r, s, p), cross(r, s, q)
    if ((d1 > 0) != (d2 > 0)) and d1 and d2 and ((d3 > 0) != (d4 > 0)) and d3 and d4:
        return True
    return any([d1 == 0 and on_segment(p, q, r), d2 == 0 and on_segment(p, q, s),
                d3 == 0 and on_segment(r, s, p), d4 == 0 and on_segment(r, s, q)])

print(segments_intersect((0, 0), (4, 4), (0, 4), (4, 0)))   # → True
print(segments_intersect((0, 0), (2, 2), (3, 3), (5, 5)))   # → False
print(segments_intersect((0, 0), (2, 2), (2, 2), (5, 0)))   # → True
```

### Polygon area: the shoelace formula

$$
\text{Area} = \frac{1}{2}\left\lvert \sum_{i} (x_i\,y_{i+1} - x_{i+1}\,y_i) \right\rvert
$$

Each term is the cross product of consecutive vertices — the signed area of a triangle
with the origin. The parts outside the polygon cancel. The **sign** of the sum tells you
the vertex order (positive: counter-clockwise).

```python
def shoelace(poly):
    s = sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1] for i in range(len(poly)))
    return s / 2

print(shoelace([(0, 0), (4, 0), (4, 3), (0, 3)]), shoelace([(0, 0), (0, 3), (4, 3), (4, 0)]))   # → 12.0 -12.0
```

> **Notebook example:** Find the area of the quadrilateral (1, 1), (5, 2), (4, 5),
> (2, 4) with the shoelace formula.
>
> | Edge | $x_i y_{i+1} - x_{i+1} y_i$ |
> |---|---|
> | (1, 1) → (5, 2) | $1 \cdot 2 - 5 \cdot 1 = -3$ |
> | (5, 2) → (4, 5) | $5 \cdot 5 - 4 \cdot 2 = 17$ |
> | (4, 5) → (2, 4) | $4 \cdot 4 - 2 \cdot 5 = 6$ |
> | (2, 4) → (1, 1) | $2 \cdot 1 - 1 \cdot 4 = -2$ |
>
> **Answer:** the sum is $-3 + 17 + 6 - 2 = 18$, so the area is $18 / 2 = 9$. The sum is
> positive, so the vertices are listed counter-clockwise.

### Convex hull: sort, then keep only left turns

The **monotone chain** algorithm sorts the points, then builds the lower and upper hulls,
popping any point that would make a right turn. $O(n \log n)$, dominated by the sort —
which matches the $\Omega(n \log n)$ lower bound, since sorting reduces to hulls.

```python
def convex_hull(points):
    pts = sorted(set(points))
    if len(pts) <= 2:
        return pts
    def half(seq):
        h = []
        for p in seq:
            while len(h) >= 2 and cross(h[-2], h[-1], p) <= 0:   # not a left turn: drop it
                h.pop()
            h.append(p)
        return h
    lower, upper = half(pts), half(reversed(pts))
    return lower[:-1] + upper[:-1]

pts = [(0, 0), (2, 1), (4, 0), (3, 2), (4, 4), (1, 3), (0, 4), (2, 2)]
print(convex_hull(pts))   # → [(0, 0), (4, 0), (4, 4), (0, 4)]
```

### Point in polygon: ray casting

Shoot a ray to the right from the point and count edge crossings: odd means inside
(each crossing toggles in/out — a parity argument).

```python
def inside(pt, poly):
    x, y = pt
    count = 0
    for i in range(len(poly)):
        (x1, y1), (x2, y2) = poly[i], poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y):                               # edge straddles the ray's height
            x_cross = x1 + (y - y1) * (x2 - x1) / (y2 - y1)
            if x_cross > x:
                count += 1
    return count % 2 == 1

L_shape = [(0, 0), (4, 0), (4, 1), (1, 1), (1, 4), (0, 4)]
print(inside((0.5, 3), L_shape), inside((3, 3), L_shape))   # → True False
```

> **Watch out:** Geometry with floats needs tolerances (`abs(x) < 1e-9` instead of
> `== 0`), and slopes as floats collide or differ by rounding. Prefer integer arithmetic:
> cross products, squared distances, and slopes as gcd-reduced integer pairs (chapter 07).

## 2 · The Maths Behind the Classic Tricks

Most "clever" interview solutions are one idea from this module. Recognising the idea is
the skill.

| Problem | The maths | Chapter |
|---|---|---|
| Missing number in 0…n | Gauss's sum, or XOR cancellation | 01, 02 |
| Single number (others appear twice) | $a \oplus a = 0$ | 02 |
| Duplicate in n + 1 numbers from 1…n, O(1) space | Pigeonhole guarantees it; the array as a function has a cycle (Floyd) | 04 |
| Power of two, count bits | `x & (x - 1)` | 02 |
| Unique paths, climbing stairs, decode ways | Counting by last step = DP; binomials | 05 |
| Generate parentheses / count BST shapes | Catalan numbers | 05 |
| "Answer mod 10⁹ + 7", nCr for big n | Modular arithmetic, Fermat inverses | 05, 07 |
| Pow(x, n), Fibonacci for huge n | Repeated squaring, matrix power | 06, 07 |
| GCD of strings, rotate array, max points on a line | Euclid, gcd cycles, reduced slope keys | 07 |
| Count primes | Sieve of Eratosthenes | 07 |
| Shuffle an array fairly, random pick from a stream | Counting permutations; probability proofs | 05, 10 |
| Trailing zeros of n! | Counting factors of 5 (Legendre) | 07 |
| Excel column title | Bijective base 26 (no zero digit) | 02 |
| Happy number, linked-list cycle | Pigeonhole ⇒ a cycle; Floyd | 04 |
| Course schedule | Partial orders, topological sort | 04, 08 |
| Subarray sum equals k | Prefix sums: $\text{sum}(i..j) = P_j - P_{i-1}$ | 01 |

A few of these deserve their proofs, because interviewers ask "why does that work?".

### Missing number, two ways

```python
from functools import reduce
from operator import xor
nums = [3, 0, 1, 5, 2]                  # 0..5 with one missing
n = len(nums)
print(n * (n + 1) // 2 - sum(nums))                                  # → 4
print(reduce(xor, range(n + 1)) ^ reduce(xor, nums))                 # → 4
```

The XOR version cannot overflow in fixed-width languages; the sum version can.

### Fisher–Yates shuffle: why it is uniform

For i from n − 1 down to 1, swap `a[i]` with `a[j]` for a uniformly random j in 0…i. The
number of possible random choices is $n \cdot (n-1) \cdots 2 = n!$, each distinct choice
sequence gives a distinct permutation, and there are exactly $n!$ permutations — so each
appears exactly once: **uniform**. The tempting "swap each element with a random position
in 0…n−1" has $n^n$ equally likely choice sequences, and since $n!$ does not divide $n^n$
(for n ≥ 3), some permutations must come up more often.

```python
import random
from collections import Counter
random.seed(42)

def fisher_yates(a):
    a = a[:]
    for i in range(len(a) - 1, 0, -1):
        j = random.randint(0, i)
        a[i], a[j] = a[j], a[i]
    return a

def naive(a):
    a = a[:]
    for i in range(len(a)):
        j = random.randint(0, len(a) - 1)
        a[i], a[j] = a[j], a[i]
    return a

N = 60_000
fy = Counter(tuple(fisher_yates([1, 2, 3])) for _ in range(N))
nv = Counter(tuple(naive([1, 2, 3])) for _ in range(N))
spread = lambda c: round((max(c.values()) - min(c.values())) / (N / 6), 2)
print(len(fy), spread(fy) < 0.1, spread(nv) > 0.15)   # → 6 True True

# exact: enumerate all 3^3 = 27 equally likely choice sequences of the naive shuffle
from itertools import product
def naive_with(choices):
    a = [1, 2, 3]
    for i, j in enumerate(choices):
        a[i], a[j] = a[j], a[i]
    return tuple(a)
exact = Counter(naive_with(c) for c in product(range(3), repeat=3))
print(sorted(exact.values()))                          # → [4, 4, 4, 5, 5, 5]
```

With 3 elements the naive shuffle has $3^3 = 27$ equally likely paths onto 6 permutations.
27 is not a multiple of 6, so the frequencies cannot all be equal — and exact enumeration
shows three permutations come up 5 times in 27 and three only 4 times: a 25% bias.

### Reservoir sampling: one uniform item from a stream of unknown length

Keep the first item; when the i-th item arrives (counting from 1), replace the kept item
with probability 1/i. Why uniform: item i is chosen at step i with probability 1/i and
then survives every later step j with probability $1 - 1/j$. The product telescopes:

$$
\frac{1}{i}\cdot\frac{i}{i+1}\cdot\frac{i+1}{i+2}\cdots\frac{n-1}{n} = \frac{1}{n}
$$

```python
import random
from collections import Counter
random.seed(1)

def reservoir(stream):
    kept = None
    for i, x in enumerate(stream, 1):
        if random.randrange(i) == 0:        # probability 1/i
            kept = x
    return kept

counts = Counter(reservoir(range(5)) for _ in range(50_000))
print(sorted(counts), max(counts.values()) - min(counts.values()) < 500)   # → [0, 1, 2, 3, 4] True
```

### Trailing zeros of n!

A trailing zero needs a factor 10 = 2 × 5, and factors of 2 are plentiful, so count the
factors of 5: $\lfloor n/5 \rfloor + \lfloor n/25 \rfloor + \lfloor n/125 \rfloor + \dots$
(numbers like 25 contribute two fives). This is **Legendre's formula**, O(log n).

```python
import math
def trailing_zeros(n):
    z, p = 0, 5
    while p <= n:
        z += n // p
        p *= 5
    return z

s = str(math.factorial(100))
print(trailing_zeros(100), len(s) - len(s.rstrip("0")))   # → 24 24
```

> **Notebook example:** How many trailing zeros does $125!$ have?
>
> 1. Multiples of 5 up to 125: $\lfloor 125/5 \rfloor = 25$.
> 2. Multiples of 25 give a second 5: $\lfloor 125/25 \rfloor = 5$.
> 3. Multiples of 125 give a third 5: $\lfloor 125/125 \rfloor = 1$.
> 4. Total fives: $25 + 5 + 1 = 31$. There are far more factors of 2, so each 5 pairs
>    with a 2 to make a 10.
>
> **Answer:** 31 trailing zeros.

### Excel column titles: bijective base 26

A, B, …, Z, AA, AB, … is base 26 **without a zero digit** (A = 1 … Z = 26). The fix to
ordinary base conversion is to subtract 1 before each division.

```python
def column_title(n):
    out = []
    while n:
        n, r = divmod(n - 1, 26)
        out.append(chr(ord("A") + r))
    return "".join(reversed(out))

print(column_title(1), column_title(26), column_title(27), column_title(702), column_title(703))   # → A Z AA ZZ AAA
```

> **Notebook example:** Which spreadsheet column is number 705?
>
> 1. Subtract 1, then divide by 26: $704 = 27 \times 26 + 2$. The remainder 2 is the
>    letter **C** (0 = A).
> 2. Carry on with 27: $27 - 1 = 26 = 1 \times 26 + 0$. The remainder 0 is **A**.
> 3. Carry on with 1: $1 - 1 = 0 = 0 \times 26 + 0$. The remainder 0 is **A**. The
>    quotient is 0, so stop.
> 4. Read the letters from last to first: **AAC**.
>
> **Answer:** AAC. **Check:** $1 \times 26^2 + 1 \times 26 + 3 = 676 + 26 + 3 = 705$. ✓

## 3 · Back-of-the-Envelope Estimation

System design interviews expect quick, order-of-magnitude arithmetic. The skill is
rounding boldly and keeping track of powers of ten.

**Numbers worth memorising**

| Quantity | Value |
|---|---|
| Seconds per day | 86,400 ≈ $10^5$ |
| Seconds per month / year | ≈ $2.6 \times 10^6$ / ≈ $3.15 \times 10^7$ |
| $2^{10}$, $2^{20}$, $2^{30}$, $2^{40}$ | ≈ thousand, million, billion, trillion (KiB, MiB, GiB, TiB) |
| $2^{31}$, $2^{32}$, $2^{63}$ | ≈ 2.1 × 10⁹, 4.3 × 10⁹, 9.2 × 10¹⁸ |
| log₂ of a million / a billion | ≈ 20 / 30 |
| Characters in a tweet-length text | ~ 300 bytes with metadata |

> **Worked example:** A photo-sharing app with 50 million daily active users; each user
> views 30 photos and uploads 0.2 photos a day; photos average 500 KB. **Reads:**
> 50M × 30 / 86,400 ≈ 17,000 requests/s on average; with a peak factor of 3, ~50,000/s.
> **Writes:** 50M × 0.2 = 10M photos/day ≈ 116/s. **Storage:** 10M × 500 KB = 5 TB/day,
> about 1.8 PB/year before replication — a read-heavy system dominated by blob storage
> and a CDN.

```python
dau, views, uploads, size_kb = 50e6, 30, 0.2, 500
reads_per_s = dau * views / 86_400
writes_per_s = dau * uploads / 86_400
tb_per_day = dau * uploads * size_kb / 1e9
print(round(reads_per_s, -3), round(writes_per_s), tb_per_day, round(tb_per_day * 365 / 1000, 2))   # → 17000.0 116 5.0 1.82
```

State assumptions, round to one significant figure, sanity-check against known systems,
and name which resource dominates. Precision is not the point; the order of magnitude
and the reasoning are.

## 4 · Question Bank

Each question is tagged with the level where it typically appears and the chapter that
teaches it. Answer out loud before opening. Each answer has three layers: **say this
first**, **then explain**, and **the follow-up** you should expect.

### Warm-up (L3–L4)

**Q1 · L3 · ch 02 — Why is `0.1 + 0.2 != 0.3`?**

<details>
<summary>Open the answer</summary>

**Say this first.** 0.1, 0.2 and 0.3 cannot be represented exactly in binary floating
point, so each is rounded, and the rounding errors do not cancel.

**Then explain.** A fraction terminates in base 2 only if its denominator is a power of
two; 1/10 is not, so its binary expansion repeats forever and is cut off at 53 significant
bits. Compare floats with a tolerance (`math.isclose`), and use integer cents or
`Decimal` for money.

**Follow-up.** "Which integers can a double hold exactly?" All up to $2^{53}$.

</details>

**Q2 · L3 · ch 05 — How many subsets does a set of n elements have, and why?**

<details>
<summary>Open the answer</summary>

**Say this first.** $2^n$: each element is independently in or out.

**Then explain.** By the product rule, n binary choices give $2^n$ outcomes; equivalently
each subset is an n-bit mask, so counting from 0 to $2^n - 1$ enumerates them all.

**Follow-up.** "How many of size k?" $\binom{n}{k}$, and summing over k gives $2^n$
(the binomial theorem with a = b = 1).

</details>

**Q3 · L4 · ch 06 — What is the time complexity of `for i in range(n): for j in range(i, n):`?**

<details>
<summary>Open the answer</summary>

**Say this first.** Θ(n²): about n²/2 iterations.

**Then explain.** The inner loop runs n, n − 1, …, 1 times; the arithmetic series sums to
$n(n+1)/2$.

**Follow-up.** "And if the inner loop doubles j instead?" Then each inner loop is
O(log n) and the total is Θ(n log n).

</details>

**Q4 · L4 · ch 07 — How do you compute $a^b \bmod m$ for huge b?**

<details>
<summary>Open the answer</summary>

**Say this first.** Repeated squaring: O(log b) multiplications, reducing mod m after each.

**Then explain.** Write b in binary; square the base once per bit, multiply it into the
result when the bit is 1. Reducing each step keeps numbers below $m^2$.

**Follow-up.** "Division mod m?" Multiply by the modular inverse, which exists iff
gcd(a, m) = 1; for prime m it is $a^{m-2} \bmod m$.

</details>

### Core (L4–L5)

**Q5 · L4 · ch 10 — You hash n keys into m buckets. When do collisions become likely?**

<details>
<summary>Open the answer</summary>

**Say this first.** Around $\sqrt{m}$ keys — the birthday bound — far earlier than m.

**Then explain.** Collisions depend on the number of pairs, about $n^2/2$, each colliding
with probability 1/m; the probability of none is about $e^{-n^2/2m}$, which is 50% at
$n \approx 1.18\sqrt{m}$.

**Follow-up.** "So how long should random IDs be?" Long enough that $\sqrt{N}$ exceeds
the number you will ever generate by a wide margin — e.g. 122 random bits for UUIDv4.

</details>

**Q6 · L5 · ch 10 — Explain why randomized quicksort is O(n log n) expected on every input.**

<details>
<summary>Open the answer</summary>

**Say this first.** Elements of rank i and j are compared only if one of them is the first
pivot chosen among the j − i + 1 elements between them, probability 2/(j − i + 1); summing
over pairs gives O(n log n) by linearity of expectation.

**Then explain.** Randomness makes the analysis independent of the input: no adversarial
input exists, only unlucky pivot sequences, which are exponentially unlikely.

**Follow-up.** "Worst case?" Still Θ(n²), with vanishing probability; introsort switches to
heapsort to cap it.

</details>

**Q7 · L5 · ch 06 — Solve $T(n) = 2T(n/2) + n$ and explain it without the master theorem.**

<details>
<summary>Open the answer</summary>

**Say this first.** Θ(n log n).

**Then explain.** Draw the recursion tree: level k has $2^k$ nodes of size $n/2^k$, so each
level does n work in total, and there are $\log_2 n$ levels.

**Follow-up.** "What if the combine step were O(1)?" Then the leaves dominate: Θ(n).

</details>

**Q8 · L5 · ch 10 — An alert with a 1% false-positive rate fires; incidents happen in 0.1% of windows. How worried should you be?**

<details>
<summary>Open the answer</summary>

**Say this first.** Not very: with ~99% sensitivity only about 9% of such alerts are real.

**Then explain.** Bayes: $\frac{0.99 \times 0.001}{0.99 \times 0.001 + 0.01 \times 0.999} \approx 0.09$.
The base rate dominates.

**Follow-up.** "How do you fix it?" Raise the prior (alert on combined signals), lower the
false-positive rate, or route low-confidence alerts to a ticket instead of a page.

</details>

**Q9 · L5 · ch 11 — Why can't you average p99 latencies across servers?**

<details>
<summary>Open the answer</summary>

**Say this first.** Percentiles are not additive; the fleet p99 depends on the full
combined distribution, including how much traffic each server handles.

**Then explain.** Merge histograms (bucket counts) and compute the percentile from the
merged histogram; tools like HdrHistogram and t-digest exist for exactly this.

**Follow-up.** "Why does p99 matter so much?" Fan-out: a request touching 100 services hits
at least one p99 about 63% of the time.

</details>

**Q10 · L5 · ch 09 — How does PageRank relate to eigenvectors?**

<details>
<summary>Open the answer</summary>

**Say this first.** The PageRank vector is the stationary distribution of a random surfer —
the eigenvector with eigenvalue 1 of the (damped) link matrix.

**Then explain.** Power iteration — repeatedly multiplying a rank vector by the matrix —
converges to that dominant eigenvector; damping guarantees convergence and uniqueness.

**Follow-up.** "Why the damping factor?" It handles dead ends and disconnected parts of the
web and makes the chain ergodic.

</details>

### Senior (L6+)

**Q11 · L6 · ch 14 — A teammate proposes a static checker that proves the absence of all null dereferences. Your response?**

<details>
<summary>Open the answer</summary>

**Say this first.** Exactly that is impossible in general (Rice's theorem), so the tool
must be conservative — sound with false alarms, or precise with misses — and we should
choose which.

**Then explain.** Practical designs restrict the language (non-null types, Optional),
require annotations at boundaries, and accept some warnings, turning an undecidable
question into a decidable type-checking one.

**Follow-up.** "Then why do tools like this work well in practice?" Most real code stays in
decidable fragments; the tool only needs to be right on the code people write.

</details>

**Q12 · L6 · ch 14 — Your scheduling problem is NP-hard. How do you ship something?**

<details>
<summary>Open the answer</summary>

**Say this first.** Look at the real constraints: small n allows exact search, small
numbers allow pseudo-polynomial DP, otherwise use a heuristic or an ILP/SAT solver with a
time limit, and measure the gap against a lower bound.

**Then explain.** NP-hardness is about the worst case over all inputs; your inputs may have
structure. Greedy plus local search often lands within a few percent of optimal; a lower
bound (for example an LP relaxation) tells you how close.

**Follow-up.** "How would you detect regressions?" Keep a benchmark set of instances with
known optima or bounds and track the solution quality and runtime.

</details>

**Q13 · L6 · ch 13 — Design the durability math: three replicas or erasure coding?**

<details>
<summary>Open the answer</summary>

**Say this first.** Three replicas cost 200% overhead and survive two failures; a (10, 4)
Reed–Solomon code costs 40% and survives any four, at the price of more CPU and wider
reads during repair.

**Then explain.** Probability of loss depends on failures within the repair window and on
correlation (racks, zones); place fragments across failure domains. Hot data often stays
replicated for latency; cold data moves to erasure coding.

**Follow-up.** "What dominates real data loss?" Correlated failures and operator error —
which the independence maths does not cover.

</details>

**Q14 · L6 · ch 11 — An A/B test shows +2% conversion, p = 0.04, after the team checked daily and stopped when it crossed significance. Ship it?**

<details>
<summary>Open the answer</summary>

**Say this first.** Not on that evidence: stopping at the first significant peek inflates
the false-positive rate well above 5%.

**Then explain.** Rerun with a pre-registered sample size (or use a sequential test designed
for continuous monitoring), check for sample-ratio mismatch, and look at the confidence
interval and guardrail metrics.

**Follow-up.** "The re-run shows +0.5%, significant — ship?" Decide on practical value and
cost; the first estimate was inflated by the winner's curse.

</details>

**Q15 · L6 · ch 06/07 — Compute the n-th Fibonacci number modulo $10^9 + 7$ for $n = 10^{18}$.**

<details>
<summary>Open the answer</summary>

**Say this first.** Matrix exponentiation: $\begin{pmatrix}1&1\\1&0\end{pmatrix}^n$ by
repeated squaring, mod p — about 60 squarings of a 2×2 matrix.

**Then explain.** Any linear recurrence of order k becomes a k×k matrix power in
$O(k^3 \log n)$; reduce mod p after each multiplication.

**Follow-up.** "Why not Binet's formula?" Floating point loses exactness beyond n ≈ 70 and
cannot work modulo p.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **L3–L4** | Orientation tests and shoelace area; the classic tricks (missing number, XOR, power of two, gcd, sieve, fast power); rough estimation with powers of ten |
| **L5** | Proofs for the tricks (Fisher–Yates, reservoir sampling, Legendre); segment intersection with edge cases; convex hull; birthday-bound and percentile reasoning in designs; Bayes for alerting |
| **L6+** | Choosing approaches for NP-hard problems; undecidability limits on tooling; durability and experiment-design maths; explaining trade-offs quantitatively to non-experts |

## Checklist

- [ ] I can write orientation, segment intersection, shoelace area, point-in-polygon and a convex hull from memory.
- [ ] For each classic trick in the table, I can name the maths and prove why it works.
- [ ] I can prove Fisher–Yates is uniform and why the naive shuffle is not.
- [ ] I can do back-of-envelope QPS, storage and bandwidth estimates in a minute.
- [ ] I have answered every question in §4 out loud, including its follow-up.
