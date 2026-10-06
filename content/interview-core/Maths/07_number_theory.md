# Number Theory — Primes, GCD and Modular Arithmetic

Number theory is the study of whole numbers: divisibility, primes, remainders. For
centuries it was the "purest", most useless branch of mathematics — until computers
made it the engine of hashing, checksums, random number generators and all of
public-key cryptography. This chapter builds it from remainders on a clock face up to
the pieces every engineer meets: primes and the sieve, Euclid's gcd, modular arithmetic
and why division is special, fast exponentiation, modular inverses, the Chinese
remainder theorem, and a complete worked example of RSA.

**Where this fits:** Part 2 · Discrete maths, chapter 7 of 15. **Builds on:** [02 Number systems and binary](02_number_systems_and_binary.md) (binary and wrap-around). **Used again in:** 13, 15. **Next in order:** [08 Graph theory](08_graph_theory.md).

## Where You Will Use This

| Where | Number theory inside |
|---|---|
| Hash tables | `hash(key) % size`; probe steps coprime to the size |
| "Answer modulo 10⁹ + 7" | Modular arithmetic, inverses via Fermat |
| String matching (Rabin–Karp), deduplication | Polynomial rolling hashes mod a prime |
| HTTPS, SSH, signatures | RSA and Diffie–Hellman: modular exponentiation, inverses, primes |
| Credit cards, ISBNs, IBANs | Check digits (mod 10, mod 11, mod 97) |
| Random numbers, shuffles, sharding | Modular reduction and its bias |
| Array rotation, fractions, aspect ratios, slopes | gcd |

## Foundations — Remainders and Clocks

When you divide 17 by 5 you get 3 with **remainder** 2: $17 = 3 \cdot 5 + 2$. The
**division algorithm** says that for any integer a and positive integer n there is
exactly one way to write

$$
a = q \cdot n + r \qquad \text{with } 0 \le r < n
$$

q is the **quotient** (`a // n`) and r the **remainder** (`a % n`). If r = 0 we say
n **divides** a, written $n \mid a$.

> **Analogy:** A clock face. 15 hours after 10 o'clock is 1 o'clock, because
> $10 + 15 = 25$ and 25 leaves remainder 1 when divided by 12 (on a 12-hour dial,
> 12 plays the role of 0). Arithmetic "mod n" is arithmetic on a clock with n
> positions: numbers wrap around. You already do it for hours, days of the week and
> angles.

## 1 · Primes

A **prime** is an integer greater than 1 whose only positive divisors are 1 and
itself: 2, 3, 5, 7, 11, 13, … Other integers greater than 1 are **composite**.

> **Key idea:** **The fundamental theorem of arithmetic** — every integer greater than
> 1 is a product of primes in exactly one way (up to order). $360 = 2^3 \cdot 3^2 \cdot 5$.
> Primes are the atoms; every number is a molecule with a unique formula. Many
> problems become easy once you think in prime factorisations: gcd, lcm, number of
> divisors, perfect squares.

### Testing for primality: stop at √n

If $n = a \cdot b$ with $a \le b$, then $a \le \sqrt{n}$ (otherwise $a \cdot b > n$).
So if n has any divisor other than 1 and n, it has one no bigger than $\sqrt{n}$. Trial
division therefore only needs to try divisors up to $\sqrt{n}$: $O(\sqrt{n})$ instead
of $O(n)$.

```python
def is_prime(n: int) -> bool:
    if n < 2:
        return False
    d = 2
    while d * d <= n:          # d <= sqrt(n), without floating point
        if n % d == 0:
            return False
        d += 1
    return True

def factorise(n: int) -> dict:
    f, d = {}, 2
    while d * d <= n:
        while n % d == 0:
            f[d] = f.get(d, 0) + 1
            n //= d
        d += 1
    if n > 1:
        f[n] = f.get(n, 0) + 1     # what remains is a prime bigger than sqrt(original)
    return f

print([p for p in range(30) if is_prime(p)])   # → [2, 3, 5, 7, 11, 13, 17, 19, 23, 29]
print(factorise(360))                          # → {2: 3, 3: 2, 5: 1}
print(factorise(2**31 - 1))                    # → {2147483647: 1}
```

$2^{31} - 1$ (the largest signed 32-bit integer) happens to be prime — a **Mersenne
prime**. For numbers with hundreds of digits, trial division is hopeless; real systems
use the probabilistic **Miller–Rabin** test, built on Fermat's little theorem (§6).

> **Notebook example:** Is 221 a prime number?
>
> **What you need:** A **prime** is a whole number above 1 that only 1 and itself divide
> exactly. To test a number n, divide it by small primes d and write each try as
> $n = q \cdot d + r$: q (the **quotient**) is how many whole times d fits, and r (the
> **remainder**) is what is left over. If r = 0, d **divides** n, so n is not prime. Two
> shortcuts: you only need to try **primes** (if 4 divided n, then 2 would too), and you
> can stop once $d \cdot d > n$ (divisors come in pairs $a \cdot b = n$, and the smaller
> one of a pair is never bigger than $\sqrt{n}$).
>
> **Plan:** work out where to stop, then try 2, 3, 5, 7, … in turn until one leaves
> remainder 0 or you run out of primes.
>
> 1. **Find where to stop.** $14 \cdot 14 = 196$, which is not more than 221, and
>    $15 \cdot 15 = 225$, which is. So $\sqrt{221}$ lies between 14 and 15, and the primes
>    to try are 2, 3, 5, 7, 11 and 13.
>    *Why:* if 221 were $a \cdot b$ with both a and b at least 15, the product would be at
>    least 225, which is too big.
> 2. **Try 2.** $221 = 110 \cdot 2 + 1$. Remainder 1, so 2 does not divide 221.
> 3. **Try 3.** $221 = 73 \cdot 3 + 2$. Remainder 2: no.
> 4. **Try 5.** $221 = 44 \cdot 5 + 1$. Remainder 1: no.
> 5. **Try 7.** $221 = 31 \cdot 7 + 4$. Remainder 4: no.
> 6. **Try 11.** $221 = 20 \cdot 11 + 1$. Remainder 1: no.
> 7. **Try 13.** $221 = 17 \cdot 13 + 0$. Remainder **0**: 13 divides 221.
>    *Why:* one divisor (other than 1 and 221) is enough to prove a number is not prime,
>    so you can stop here.
>
> **Answer:** 221 is **not** prime: $221 = 13 \times 17$. It looks prime because it has no
> small factor, which is exactly why trial division must keep going up to $\sqrt{n}$.
>
> **Check:** multiply back: $13 \times 10 = 130$, $13 \times 7 = 91$, and
> $130 + 91 = 221$. In Python, `is_prime(221)` from the code above returns `False`. ✓

> **Your turn:** Is 97 a prime number?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find where to stop.** $9 \cdot 9 = 81$ is not more than 97, but $10 \cdot 10 = 100$
>    is. So try the primes 2, 3, 5 and 7.
> 2. **Try 2.** $97 = 48 \cdot 2 + 1$. Remainder 1: no.
> 3. **Try 3.** $97 = 32 \cdot 3 + 1$. Remainder 1: no.
> 4. **Try 5.** $97 = 19 \cdot 5 + 2$. Remainder 2: no.
> 5. **Try 7.** $97 = 13 \cdot 7 + 6$. Remainder 6: no.
>
> **Answer:** no prime up to $\sqrt{97}$ divides it, so 97 **is** prime.
>
> </details>

> **Notebook example:** Write 360 as a product of primes.
>
> **What you need:** The **fundamental theorem of arithmetic** (the Key idea above): every
> whole number above 1 is a product of primes in exactly one way, ignoring order. To find
> it, divide by the smallest prime for as long as it goes in exactly, then move on to the
> next prime. A small raised number, the **exponent**, counts copies: $2^3$ means
> $2 \cdot 2 \cdot 2$.
>
> **Plan:** peel off 2s until the number is odd, then 3s, and so on, until what is left is
> a prime.
>
> 1. **Divide by 2.** $360 = 2 \times 180$.
> 2. **Divide by 2 again.** $180 = 2 \times 90$.
> 3. **Divide by 2 again.** $90 = 2 \times 45$.
> 4. **Notice that 2 is used up.** $45 = 22 \cdot 2 + 1$ leaves remainder 1, so 45 is odd.
>    So far: three 2s, with 45 left over.
> 5. **Divide by 3.** $45 = 3 \times 15$.
> 6. **Divide by 3 again.** $15 = 3 \times 5$.
> 7. **Stop at a prime.** What is left, 5, is prime, so it is the last factor.
> 8. **Collect the factors.** $360 = 2 \times 2 \times 2 \times 3 \times 3 \times 5$, which
>    is $2^3 \times 3^2 \times 5$.
>    *Why:* grouping the copies of each prime and writing the count as an exponent gives
>    the short form.
>
> **Answer:** $360 = 2^3 \cdot 3^2 \cdot 5$. This is 360's one and only "formula" in
> primes.
>
> **Check:** multiply back: $2^3 = 8$, $3^2 = 9$, $8 \times 9 = 72$ and $72 \times 5 = 360$.
> The code above prints `factorise(360)` as `{2: 3, 3: 2, 5: 1}`: the same exponents. ✓

> **Your turn:** Write 84 as a product of primes.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Divide by 2.** $84 = 2 \times 42$.
> 2. **Divide by 2 again.** $42 = 2 \times 21$.
> 3. **Notice that 2 is used up.** $21 = 10 \cdot 2 + 1$, so 21 is odd.
> 4. **Divide by 3.** $21 = 3 \times 7$.
> 5. **Stop at a prime.** 7 is prime.
> 6. **Collect the factors.** $84 = 2 \times 2 \times 3 \times 7 = 2^2 \times 3 \times 7$.
>
> **Answer:** $84 = 2^2 \cdot 3 \cdot 7$ (check: $4 \times 3 \times 7 = 84$).
>
> </details>

> **Notebook example:** How many whole numbers divide 360 exactly?
>
> **What you need:** From the previous example, $360 = 2^3 \cdot 3^2 \cdot 5^1$. A
> **divisor** of 360 can only be built from the same primes, using each one no more times
> than 360 does. So every divisor looks like $2^a \cdot 3^b \cdot 5^c$ with a from 0 to 3,
> b from 0 to 2 and c from 0 to 1 (an exponent of 0 means "leave that prime out", since
> $2^0 = 1$), and different choices give different divisors. When you make several
> independent choices, the number of combinations is the **product** of the number of
> options for each.
>
> **Plan:** count the options for each exponent, then multiply the counts.
>
> 1. **Write the factorisation.** $360 = 2^3 \cdot 3^2 \cdot 5^1$.
> 2. **Count options for the 2s.** a can be 0, 1, 2 or 3: **4** options.
> 3. **Count options for the 3s.** b can be 0, 1 or 2: **3** options.
> 4. **Count options for the 5.** c can be 0 or 1: **2** options.
> 5. **Multiply the counts.** $4 \times 3 = 12$, and $12 \times 2 = 24$.
>    *Why:* each of the 4 choices for a goes with each of the 3 choices for b (12 pairs),
>    and each pair goes with each of the 2 choices for c.
>
> **Answer:** 360 has **24** divisors. The shortcut to remember: add 1 to each exponent and
> multiply, $(3 + 1)(2 + 1)(1 + 1) = 24$.
>
> **Check:** test one choice, a = 2, b = 1, c = 0: $2^2 \cdot 3^1 \cdot 5^0 = 4 \cdot 3 \cdot 1 = 12$,
> and $360 = 30 \times 12$ exactly. The one-liner
> `sum(1 for d in range(1, 361) if 360 % d == 0)` also gives 24. ✓

> **Your turn:** How many divisors does $72 = 2^3 \cdot 3^2$ have?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the factorisation.** $72 = 2^3 \cdot 3^2$ (since $8 \times 9 = 72$).
> 2. **Count options for the 2s.** 0, 1, 2 or 3: 4 options.
> 3. **Count options for the 3s.** 0, 1 or 2: 3 options.
> 4. **Multiply the counts.** $4 \times 3 = 12$.
>
> **Answer:** 12 divisors: 1, 2, 3, 4, 6, 8, 9, 12, 18, 24, 36 and 72.
>
> </details>

### All primes up to N: the sieve

To find every prime up to N, cross out multiples instead of testing each number.

**Try it: run the sieve.** Press *Play*. Each new prime crosses off its multiples,
starting from its square (smaller multiples were already crossed off by smaller
primes). Notice the crossing stops after 7 for N = 120: since 11² > 120, everything left
is prime. Compare the count of cross-offs with trial division.

<div class="lab" data-viz="math-sieve"></div>

```python
def sieve(n: int) -> list:
    is_p = [True] * (n + 1)
    is_p[0] = is_p[1] = False
    p = 2
    while p * p <= n:
        if is_p[p]:
            for m in range(p * p, n + 1, p):
                is_p[m] = False
        p += 1
    return [i for i, ok in enumerate(is_p) if ok]

import math
primes = sieve(1_000_000)
print(len(primes), round(1_000_000 / math.log(1_000_000)))   # → 78498 72382
```

There are 78,498 primes below a million. The **prime number theorem** says the count
up to N is about $N / \ln N$ (here 72,382, within 8%): primes thin out slowly, so a
random number near N is prime with probability about $1/\ln N$. That is why generating
a random 1024-bit prime is fast: try random odd numbers, and about one in 355 is prime.

## 2 · GCD and LCM

The **greatest common divisor** $\gcd(a, b)$ is the largest integer dividing both. The
**least common multiple** $\text{lcm}(a, b)$ is the smallest positive integer both
divide. They are linked by

$$
\gcd(a, b) \cdot \text{lcm}(a, b) = a \cdot b
$$

### Euclid's algorithm (about 300 BC, still the best)

> **Key idea:** $\gcd(a, b) = \gcd(b, a \bmod b)$. Any number dividing a and b also
> divides $a - q b = a \bmod b$, and vice versa, so the pair (b, a mod b) has exactly
> the same common divisors — but smaller numbers. Repeat until the remainder is 0.

$$
\gcd(1071, 462):\quad 1071 = 2 \cdot 462 + 147,\quad 462 = 3 \cdot 147 + 21,\quad 147 = 7 \cdot 21 + 0 \quad\Rightarrow\quad 21
$$

**Try it: tile the rectangle.** Euclid's algorithm has a picture: cut the largest square
from an a × b rectangle, repeat on what is left. The last square tiles everything, so its
side divides both sides. Press the Fibonacci preset for the worst case, and read the
division table beside it — each row is one `a % b`.

<div class="lab" data-viz="math-euclid"></div>

```python
def gcd(a: int, b: int) -> int:
    while b:
        a, b = b, a % b
    return a

import math
print(gcd(1071, 462), math.gcd(1071, 462))   # → 21 21
print(1920 // gcd(1920, 1080), 1080 // gcd(1920, 1080))   # → 16 9
print(math.lcm(4, 6), 4 * 6 // gcd(4, 6))    # → 12 12
```

Each two steps at least halve the larger number, so Euclid takes $O(\log \min(a, b))$
steps. The worst case is consecutive Fibonacci numbers, where every quotient is 1
(**Lamé's theorem**, 1844 — the first ever complexity analysis of an algorithm).

> **Notebook example:** Find $\gcd(252, 198)$ with Euclid's algorithm.
>
> **What you need:** $\gcd(a, b)$, the **greatest common divisor**, is the largest number
> that divides both a and b exactly. **Euclid's rule:** $\gcd(a, b) = \gcd(b, r)$, where r
> is the remainder when you divide a by b, written $a = q \cdot b + r$ (in Python,
> `r = a % b`). Each step swaps the pair for a smaller pair with the same gcd. When the
> remainder reaches 0, the last **non-zero** remainder is the gcd.
>
> **Plan:** divide; keep the divisor and the remainder as the new pair; repeat until the
> remainder is 0.
>
> 1. **Divide 252 by 198.** 198 fits once: $252 = 1 \cdot 198 + 54$. New pair: (198, 54).
>    *Why:* any number dividing both 252 and 198 also divides $252 - 198 = 54$, so the
>    common divisors do not change.
> 2. **Divide 198 by 54.** $3 \cdot 54 = 162$ and $198 - 162 = 36$, so
>    $198 = 3 \cdot 54 + 36$. New pair: (54, 36).
> 3. **Divide 54 by 36.** $54 = 1 \cdot 36 + 18$. New pair: (36, 18).
> 4. **Divide 36 by 18.** $36 = 2 \cdot 18 + 0$. The remainder is 0, so stop.
> 5. **Read off the gcd.** The last non-zero remainder was **18**.
>    *Why:* 18 divides 36 exactly, so the gcd of the final pair (36, 18) is plainly 18,
>    and every earlier pair had the same gcd.
>
> **Answer:** $\gcd(252, 198) = 18$: 18 is the biggest number that divides both.
>
> **Check:** $252 = 14 \times 18$ and $198 = 11 \times 18$, and 14 and 11 share no factor,
> so nothing bigger works. With prime factors, $252 = 2^2 \cdot 3^2 \cdot 7$ and
> $198 = 2 \cdot 3^2 \cdot 11$; the gcd takes the lower power of each shared prime,
> $2 \cdot 3^2 = 18$. `math.gcd(252, 198)` agrees. ✓

> **Your turn:** Find $\gcd(90, 24)$ with Euclid's algorithm.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Divide 90 by 24.** $3 \cdot 24 = 72$ and $90 - 72 = 18$, so $90 = 3 \cdot 24 + 18$.
>    New pair: (24, 18).
> 2. **Divide 24 by 18.** $24 = 1 \cdot 18 + 6$. New pair: (18, 6).
> 3. **Divide 18 by 6.** $18 = 3 \cdot 6 + 0$. Remainder 0, so stop.
> 4. **Read off the gcd.** The last non-zero remainder was 6.
>
> **Answer:** $\gcd(90, 24) = 6$.
>
> </details>

> **Notebook example:** One job runs every 252 minutes and another every 198 minutes.
> Both ran at midnight. When do they next run at the same time?
>
> **What you need:** The **multiples** of 252 are 252, 504, 756, … The **least common
> multiple** $\text{lcm}(a, b)$ is the smallest number that is a multiple of both a and b.
> It is linked to the gcd by $\gcd(a, b) \cdot \text{lcm}(a, b) = a \cdot b$, so
> $\text{lcm}(a, b) = \dfrac{a \cdot b}{\gcd(a, b)}$. From the previous example,
> $\gcd(252, 198) = 18$.
>
> **Plan:** turn the story into an lcm, then use the formula, dividing before multiplying
> to keep the numbers small.
>
> 1. **Turn the story into maths.** Job 1 runs at 252, 504, 756, … minutes and job 2 at
>    198, 396, 594, … minutes. A time when both run is in both lists, so it is a common
>    multiple. The first such time is $\text{lcm}(252, 198)$.
> 2. **Write the formula.** $\text{lcm}(252, 198) = \dfrac{252 \times 198}{18}$.
> 3. **Divide first.** $252 \div 18 = 14$ (because $18 \times 14 = 252$). So the lcm is
>    $14 \times 198$.
>    *Why:* dividing first avoids the big product $252 \times 198 = 49896$.
> 4. **Multiply.** $14 \times 198 = 14 \times 200 - 14 \times 2 = 2800 - 28 = 2772$.
> 5. **Convert to hours.** $2772 = 46 \cdot 60 + 12$, so 46 hours and 12 minutes.
>
> **Answer:** the jobs next run together **2,772 minutes** after midnight, which is
> 46 h 12 min later.
>
> **Check:** 2772 must be a whole number of runs of each job: $2772 = 11 \times 252$ and
> $2772 = 14 \times 198$. With prime factors, the lcm takes the higher power of each
> prime: $2^2 \cdot 3^2 \cdot 7 \cdot 11 = 4 \cdot 9 \cdot 7 \cdot 11 = 2772$.
> `math.lcm(252, 198)` agrees. ✓

> **Your turn:** Two buses leave the depot together, one every 90 minutes and one every
> 24 minutes. When do they next leave together? (You found $\gcd(90, 24) = 6$ above.)
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Turn the story into maths.** The first common departure is $\text{lcm}(90, 24)$.
> 2. **Write the formula.** $\text{lcm}(90, 24) = \dfrac{90 \times 24}{6}$.
> 3. **Divide first.** $90 \div 6 = 15$, so the lcm is $15 \times 24$.
> 4. **Multiply.** $15 \times 24 = 360$.
> 5. **Convert to hours.** $360 = 6 \cdot 60 + 0$, so exactly 6 hours.
>
> **Answer:** after 360 minutes, which is 6 hours (4 trips of the first bus, 15 of the
> second).
>
> </details>

> **In practice:** gcd appears in "reduce a fraction", "aspect ratio of 1920 × 1080 is
> 16:9", "rotate an array by k in place" (the rotation splits into $\gcd(n, k)$ cycles),
> "lines through points" (store a slope as the reduced pair $(dy/g, dx/g)$ — exact,
> unlike a float), and "when do two periodic jobs coincide?" (their lcm).

## 3 · Modular Arithmetic

We write $a \equiv b \pmod{n}$ ("a is **congruent** to b mod n") when a and b leave the
same remainder mod n — equivalently, $n \mid (a - b)$. The key fact:

> **Key idea:** You can reduce **before** adding, subtracting or multiplying, and the
> remainder of the result does not change:
> $(a + b) \bmod n = ((a \bmod n) + (b \bmod n)) \bmod n$, and the same for $-$ and
> $\times$. That is what lets you compute with huge numbers while only ever storing
> numbers smaller than n.

```python
a, b, n = 123456789, 987654321, 97
print((a * b) % n, ((a % n) * (b % n)) % n)   # → 6 6
print((a + b) % n, ((a % n) + (b % n)) % n)   # → 69 69
```

**Division does not work that way.** $6 \equiv 16 \pmod{10}$, but dividing both by 2
gives 3 and 8, which are not congruent mod 10. Division mod n needs an **inverse**
(§5), and an inverse only exists sometimes.

**Try it: arithmetic on a clock.** In *keep adding a* mode, adding 5 on a 12-hour clock
visits every number before returning to 0 — because gcd(5, 12) = 1. Set a = 4: only 0,
4 and 8 are ever reached. Switch to *multiply by a*: multiplication by a is a
reshuffling of 0…m−1 (and therefore undoable) exactly when gcd(a, m) = 1. Then try
*powers of a* with m = 13.

<div class="lab" data-viz="math-mod"></div>

### Everyday uses

```python
# circular buffer of size 8: the index after 7 is 0
print([(7 + k) % 8 for k in range(4)])          # → [7, 0, 1, 2]
# day of the week, 100 days after a Wednesday (Monday = 0)
days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
print(days[(2 + 100) % 7])                      # → Fri
# casting out nines: a number is congruent to its digit sum mod 9 (because 10 ≡ 1 mod 9)
x = 987654321
print(x % 9, sum(map(int, str(x))) % 9)          # → 0 0
```

> **Notebook example:** Compute $(47 \times 58 + 93) \bmod 7$ without multiplying out
> the big numbers.
>
> **What you need:** $a \bmod n$ is the remainder when a is divided by n (Python's
> `a % n`). $a \equiv b \pmod n$, read "a is **congruent** to b mod n", means a and b leave
> the same remainder. **Reduce-first rule** (the Key idea above): in a sum or a product you
> may replace any number by its remainder mod n before calculating, and the final
> remainder does not change.
>
> **Plan:** shrink 47, 58 and 93 to their remainders mod 7, do the arithmetic with those
> tiny numbers, then take the remainder once more.
>
> 1. **Reduce 47.** $47 = 6 \cdot 7 + 5$, so $47 \equiv 5 \pmod 7$.
> 2. **Reduce 58.** $58 = 8 \cdot 7 + 2$, so $58 \equiv 2$.
> 3. **Reduce 93.** $93 = 13 \cdot 7 + 2$, so $93 \equiv 2$.
> 4. **Swap in the small numbers.** $47 \times 58 + 93 \equiv 5 \times 2 + 2 \pmod 7$.
>    *Why:* the reduce-first rule lets each number be replaced by its remainder.
> 5. **Multiply.** $5 \times 2 = 10$.
> 6. **Add.** $10 + 2 = 12$.
> 7. **Reduce the result.** $12 = 1 \cdot 7 + 5$, so the remainder is 5.
>    *Why:* 12 is not below 7 yet, so one last reduction gives the true remainder.
>
> **Answer:** $(47 \times 58 + 93) \bmod 7 = 5$. This is how code computes "the answer
> modulo $10^9 + 7$" without the numbers ever overflowing.
>
> **Check:** the long way, $47 \times 58 = 2726$, $2726 + 93 = 2819$ and
> $2819 = 402 \cdot 7 + 5$. In Python, `(47 * 58 + 93) % 7` gives 5. ✓

> **Your turn:** Compute $(23 \times 19 + 40) \bmod 6$ the same way.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Reduce 23.** $23 = 3 \cdot 6 + 5$, so $23 \equiv 5$.
> 2. **Reduce 19.** $19 = 3 \cdot 6 + 1$, so $19 \equiv 1$.
> 3. **Reduce 40.** $40 = 6 \cdot 6 + 4$, so $40 \equiv 4$.
> 4. **Swap in the small numbers.** $5 \times 1 + 4$.
> 5. **Multiply, then add.** $5 \times 1 = 5$, and $5 + 4 = 9$.
> 6. **Reduce the result.** $9 = 1 \cdot 6 + 3$, so the remainder is 3.
>
> **Answer:** 3 (the long way: $23 \times 19 + 40 = 477 = 79 \cdot 6 + 3$).
>
> </details>

> **Notebook example:** Today is Wednesday. What day of the week is it 100 days from now?
>
> **What you need:** Weekdays repeat every 7 days, so moving on by a whole number of weeks
> lands on the same weekday. Only the **remainder** of the number of days divided by 7
> matters. The code above numbers the days Monday = 0, Tuesday = 1, Wednesday = 2,
> Thursday = 3, Friday = 4, Saturday = 5, Sunday = 6.
>
> **Plan:** split 100 days into whole weeks plus leftover days, ignore the weeks, and count
> the leftover days on from Wednesday.
>
> 1. **Divide by 7.** $100 = 14 \cdot 7 + 2$: 14 whole weeks and 2 leftover days.
> 2. **Drop the whole weeks.** After 14 weeks (98 days) it is Wednesday again.
>    *Why:* each full week brings you back to the weekday you started on.
> 3. **Count the leftover days.** One day after Wednesday is Thursday; two days after is
>    Friday.
>
> **Answer:** **Friday**. A hundred days on, the weekday has moved just 2 places.
>
> **Check:** with the numbering, Wednesday is 2 and $(2 + 100) \bmod 7 = 102 \bmod 7$;
> $102 = 14 \cdot 7 + 4$, and day 4 is Friday. That is exactly the code line
> `days[(2 + 100) % 7]`. ✓

> **Your turn:** Today is Friday. What day is it 30 days from now?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Divide by 7.** $30 = 4 \cdot 7 + 2$: 4 whole weeks and 2 leftover days.
> 2. **Drop the whole weeks.** After 28 days it is Friday again.
> 3. **Count the leftover days.** Friday → Saturday → Sunday.
>
> **Answer:** Sunday (check: $(4 + 30) \bmod 7 = 34 \bmod 7 = 6$, which is Sunday).
>
> </details>

## 4 · Fast Modular Exponentiation

Cryptography computes things like $a^{65537} \bmod n$ with 2048-bit numbers.
Multiplying a by itself 65,536 times is too slow, and the intermediate $a^{65537}$ would
have millions of digits. **Repeated squaring** fixes both problems: write the exponent
in binary, square repeatedly, and reduce mod n after every step.

$$
a^{13} = a^{8} \cdot a^{4} \cdot a^{1} \quad (13 = 1101_2), \qquad a \to a^2 \to a^4 \to a^8 \text{ by squaring}
$$

```python
def power_mod(a: int, e: int, n: int) -> int:
    result, a = 1, a % n
    while e:
        if e & 1:                 # this bit of the exponent is 1: include the current power
            result = result * a % n
        a = a * a % n             # a, a^2, a^4, a^8, ...
        e >>= 1
    return result

print(power_mod(7, 13, 11), pow(7, 13, 11), 7**13 % 11)   # → 2 2 2
print(power_mod(3, 10**18, 10**9 + 7) == pow(3, 10**18, 10**9 + 7))   # → True
```

That is $O(\log e)$ multiplications: 60 or so for an exponent of $10^{18}$. Python's
built-in three-argument `pow` does exactly this. The same squaring trick powers matrix
exponentiation for linear recurrences (chapter 06).

> **Notebook example:** Compute $3^{13} \bmod 7$ by repeated squaring.
>
> **What you need:** Three facts. (1) Exponents add when you multiply powers of the same
> number: $3^8 \cdot 3^4 \cdot 3^1 = 3^{8+4+1}$. (2) Squaring doubles the exponent:
> $(3^4)^2 = 3^8$. (3) The reduce-first rule from §3: you may replace any number by its
> remainder mod 7 before multiplying. Also, every whole number is a sum of different
> **powers of two** (1, 2, 4, 8, …); that is just its binary form.
>
> **Plan:** write 13 as a sum of powers of two, build $3^1, 3^2, 3^4, 3^8$ by squaring
> (reducing mod 7 each time), then multiply together the ones you need.
>
> 1. **Write 13 in powers of two.** $13 = 8 + 4 + 1$ (in binary, $1101_2$).
> 2. **Split the power.** $3^{13} = 3^8 \cdot 3^4 \cdot 3^1$.
>    *Why:* this is fact (1) read backwards.
> 3. **Start with the first power.** $3^1 = 3$, already below 7.
> 4. **Square to get the 2nd power.** $3 \times 3 = 9$, and $9 = 1 \cdot 7 + 2$, so
>    $3^2 \equiv 2$.
> 5. **Square to get the 4th power.** $2 \times 2 = 4$, already below 7, so $3^4 \equiv 4$.
>    *Why:* $3^4 = (3^2)^2$, and fact (3) lets us square the small 2 instead of 9.
> 6. **Square to get the 8th power.** $4 \times 4 = 16$, and $16 = 2 \cdot 7 + 2$, so
>    $3^8 \equiv 2$.
> 7. **Multiply the 8th power by the 4th.** $2 \times 4 = 8$, and $8 = 1 \cdot 7 + 1$, so
>    the running result is 1.
> 8. **Multiply by the 1st power.** $1 \times 3 = 3$.
>
> **Answer:** $3^{13} \bmod 7 = 3$, from 3 squarings and 2 multiplications instead of 12
> multiplications. For an exponent like $10^{18}$ the same method needs about 60 steps
> instead of a billion billion.
>
> **Check:** the long way, $3^{13} = 1594323 = 227760 \cdot 7 + 3$. Python's
> `pow(3, 13, 7)`, which uses exactly this method, also returns 3. ✓

> **Your turn:** Compute $2^{13} \bmod 11$ by repeated squaring.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write 13 in powers of two.** $13 = 8 + 4 + 1$, so $2^{13} = 2^8 \cdot 2^4 \cdot 2^1$.
> 2. **Square to get the 2nd power.** $2 \times 2 = 4$, so $2^2 \equiv 4$.
> 3. **Square to get the 4th power.** $4 \times 4 = 16 = 1 \cdot 11 + 5$, so $2^4 \equiv 5$.
> 4. **Square to get the 8th power.** $5 \times 5 = 25 = 2 \cdot 11 + 3$, so $2^8 \equiv 3$.
> 5. **Multiply the 8th power by the 4th.** $3 \times 5 = 15 = 1 \cdot 11 + 4$: running
>    result 4.
> 6. **Multiply by the 1st power.** $4 \times 2 = 8$.
>
> **Answer:** $2^{13} \bmod 11 = 8$ (the long way: $8192 = 744 \cdot 11 + 8$).
>
> </details>

## 5 · Modular Inverses: Division, Mod n

The **inverse** of a mod n is the number x with $a x \equiv 1 \pmod{n}$. Dividing by a
then means multiplying by x.

> **Key idea:** a has an inverse mod n **if and only if** $\gcd(a, n) = 1$ (a and n
> are **coprime**). If they share a factor g > 1, then $a x - 1$ would have to be a
> multiple of n, hence of g — but g divides $ax$, so it would divide 1. Impossible.
> When n is **prime**, every a from 1 to n − 1 has an inverse — which is why so many
> problems use a prime modulus like $10^9 + 7$.

Two ways to find it:

1. **Extended Euclid.** Run Euclid backwards to find integers x, y with
   $a x + n y = \gcd(a, n)$ (**Bézout's identity**). If the gcd is 1, then
   $a x \equiv 1 \pmod n$.
2. **Fermat's little theorem** (next section), when n is prime: $a^{-1} \equiv a^{n-2}$.

```python
def extended_gcd(a: int, b: int):
    """Return (g, x, y) with a*x + b*y == g == gcd(a, b)."""
    if b == 0:
        return a, 1, 0
    g, x, y = extended_gcd(b, a % b)
    return g, y, x - (a // b) * y

def inverse(a: int, n: int) -> int:
    g, x, _ = extended_gcd(a, n)
    if g != 1:
        raise ValueError(f"{a} has no inverse mod {n}")
    return x % n

print(extended_gcd(240, 46))                   # → (2, -9, 47)
print(inverse(3, 11), 3 * inverse(3, 11) % 11)  # → 4 1
print(pow(3, -1, 11), pow(3, 11 - 2, 11))      # → 4 4
try:
    inverse(4, 10)
except ValueError as e:
    print(e)                                   # → 4 has no inverse mod 10
```

> **Notebook example:** Find the inverse of 3 mod 11 by trying each candidate (a warm-up
> for the faster method below).
>
> **What you need:** The **inverse** of a mod n is the number x (from 1 to n − 1) with
> $a \cdot x \equiv 1 \pmod n$, meaning $a \cdot x$ leaves remainder 1 when divided by n.
> Multiplying by x undoes multiplying by a, just as multiplying by $\tfrac{1}{3}$ undoes
> multiplying by 3 in ordinary arithmetic. It exists exactly when $\gcd(a, n) = 1$. For a
> small n you can simply test x = 1, 2, 3, … in turn.
>
> **Plan:** check that an inverse exists, then multiply 3 by 1, 2, 3, … and reduce mod 11
> until the remainder is 1.
>
> 1. **Check that an inverse exists.** 11 is prime and does not divide 3, so
>    $\gcd(3, 11) = 1$.
> 2. **Try x = 1.** $3 \cdot 1 = 3$. Remainder 3, not 1.
> 3. **Try x = 2.** $3 \cdot 2 = 6$. Remainder 6.
> 4. **Try x = 3.** $3 \cdot 3 = 9$. Remainder 9.
> 5. **Try x = 4.** $3 \cdot 4 = 12$, and $12 = 1 \cdot 11 + 1$. Remainder **1**: found it.
>
> **Answer:** the inverse of 3 mod 11 is **4**. So "dividing by 3" mod 11 means
> multiplying by 4. For example, "6 divided by 3" becomes $6 \cdot 4 = 24 = 2 \cdot 11 + 2$,
> which is 2, and indeed $3 \cdot 2 = 6$.
>
> **Check:** $3 \times 4 = 12 = 1 \cdot 11 + 1$. The code above prints `inverse(3, 11)` as
> 4, and `pow(3, -1, 11)` agrees. (Trying every x can take n steps, hopeless for huge n;
> the next example takes only about $\log n$ steps.) ✓

> **Your turn:** Find the inverse of 3 mod 7 by trying each candidate.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Check that an inverse exists.** 7 is prime and does not divide 3, so the gcd is 1.
> 2. **Try x = 1 and x = 2.** $3 \cdot 1 = 3$ and $3 \cdot 2 = 6$: remainders 3 and 6.
> 3. **Try x = 3.** $3 \cdot 3 = 9 = 1 \cdot 7 + 2$: remainder 2.
> 4. **Try x = 4.** $3 \cdot 4 = 12 = 1 \cdot 7 + 5$: remainder 5.
> 5. **Try x = 5.** $3 \cdot 5 = 15 = 2 \cdot 7 + 1$: remainder **1**.
>
> **Answer:** the inverse of 3 mod 7 is 5.
>
> </details>

> **Notebook example:** Find the inverse of 7 mod 26 with the extended Euclidean
> algorithm.
>
> **What you need:** The inverse of 7 mod 26 is the x with $7x \equiv 1 \pmod{26}$.
> Euclid's algorithm (§2) finds $\gcd(7, 26)$ as a chain of divisions $a = q \cdot b + r$.
> Run the chain **backwards** and you can write the gcd as $7x + 26y$ for some whole
> numbers x and y (**Bézout's identity**). If the gcd is 1, that says $7x + 26y = 1$.
> Since $26y$ is a multiple of 26, it is $\equiv 0 \pmod{26}$, which leaves
> $7x \equiv 1$: x is the inverse. To **substitute** means to replace a number by an
> expression equal to it.
>
> **Plan:** run Euclid forwards, rearrange each row to "remainder = …", then start from
> the row that ends in 1 and substitute back up the chain until only 7s and 26s remain.
>
> 1. **Run Euclid forwards.** Each row divides the previous divisor by the previous
>    remainder:
>    | Division | Remainder |
>    |---|---|
>    | $26 = 3 \cdot 7 + 5$ | 5 |
>    | $7 = 1 \cdot 5 + 2$ | 2 |
>    | $5 = 2 \cdot 2 + 1$ | 1 |
> 2. **Confirm the inverse exists.** The last non-zero remainder is 1 (the next row would
>    be $2 = 2 \cdot 1 + 0$), so $\gcd(7, 26) = 1$.
> 3. **Rearrange each row to "remainder = …".** Move the $q \cdot b$ part to the other
>    side:
>    - $5 = 26 - 3 \cdot 7$
>    - $2 = 7 - 1 \cdot 5$
>    - $1 = 5 - 2 \cdot 2$
> 4. **Start from the row that gives 1.** $1 = 5 - 2 \cdot 2$.
> 5. **Substitute for 2.** Replace 2 with $(7 - 5)$: $1 = 5 - 2 \cdot (7 - 5)$.
>    *Why:* we want only 7s and 26s in the end, so we replace the smallest number first
>    and climb back up the chain.
> 6. **Expand the brackets.** $1 = 5 - 2 \cdot 7 + 2 \cdot 5$.
> 7. **Collect the 5s.** One 5 plus two 5s is three 5s: $1 = 3 \cdot 5 - 2 \cdot 7$.
> 8. **Substitute for 5.** Replace 5 with $(26 - 3 \cdot 7)$:
>    $1 = 3 \cdot (26 - 3 \cdot 7) - 2 \cdot 7$.
> 9. **Expand the brackets.** $1 = 3 \cdot 26 - 9 \cdot 7 - 2 \cdot 7$.
> 10. **Collect the 7s.** $-9 - 2 = -11$, so $1 = 3 \cdot 26 - 11 \cdot 7$.
>    *Why:* now only 26 and 7 appear, which is the Bézout form we were after.
> 11. **Read it mod 26.** $3 \cdot 26$ is a multiple of 26, so it is $\equiv 0$. That
>    leaves $-11 \cdot 7 \equiv 1 \pmod{26}$, so −11 works as an inverse.
> 12. **Make it positive.** $-11 + 26 = 15$.
>    *Why:* adding 26 does not change a number mod 26, and inverses are usually quoted
>    between 1 and 25.
>
> **Answer:** the inverse of 7 mod 26 is **15**: multiplying by 15 mod 26 undoes
> multiplying by 7.
>
> **Check:** $7 \times 15 = 105 = 4 \cdot 26 + 1$. Step 10 also checks itself:
> $3 \cdot 26 - 11 \cdot 7 = 78 - 77 = 1$. In Python, `pow(7, -1, 26)` returns 15 and
> `extended_gcd(7, 26)` returns `(1, -11, 3)`: the same −11 and 3. ✓

> **Your turn:** Find the inverse of 5 mod 13 with the extended Euclidean algorithm.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Run Euclid forwards.** $13 = 2 \cdot 5 + 3$, then $5 = 1 \cdot 3 + 2$, then
>    $3 = 1 \cdot 2 + 1$. The last non-zero remainder is 1, so the inverse exists.
> 2. **Rearrange each row to "remainder = …".** $3 = 13 - 2 \cdot 5$, $2 = 5 - 3$ and
>    $1 = 3 - 2$.
> 3. **Substitute for 2.** $1 = 3 - (5 - 3) = 2 \cdot 3 - 5$.
> 4. **Substitute for 3.** $1 = 2 \cdot (13 - 2 \cdot 5) - 5 = 2 \cdot 13 - 4 \cdot 5 - 5 = 2 \cdot 13 - 5 \cdot 5$.
> 5. **Read it mod 13.** $2 \cdot 13 \equiv 0$, so $-5 \cdot 5 \equiv 1$: −5 works.
> 6. **Make it positive.** $-5 + 13 = 8$.
>
> **Answer:** the inverse of 5 mod 13 is 8 (check: $5 \cdot 8 = 40 = 3 \cdot 13 + 1$).
>
> </details>

(`pow(a, -1, n)` computes inverses directly in Python 3.8+.)

## 6 · Fermat, Euler and the Chinese Remainder Theorem

> **Definition:** **Fermat's little theorem** — if p is prime and p does not divide a,
> then $a^{p-1} \equiv 1 \pmod p$.

Multiplying $1, 2, \dots, p-1$ by a (mod p) just reshuffles them (the lab's multiply
mode shows this), so their products are equal: $a^{p-1}(p-1)! \equiv (p-1)! \pmod p$,
and the factorial can be cancelled because it is coprime to p.

**Euler's generalisation** works for any modulus n: $a^{\varphi(n)} \equiv 1 \pmod n$
when $\gcd(a, n) = 1$, where **Euler's totient** $\varphi(n)$ counts the numbers from
1 to n coprime to n. For a prime, $\varphi(p) = p - 1$; for a product of two distinct
primes, $\varphi(pq) = (p-1)(q-1)$.

```python
import math
p = 101
print(all(pow(a, p - 1, p) == 1 for a in range(1, p)))                 # → True
phi = lambda n: sum(1 for k in range(1, n + 1) if math.gcd(k, n) == 1)
print(phi(15), (3 - 1) * (5 - 1))                                      # → 8 8
print(pow(561 - 1, 560, 561), all(pow(a, 560, 561) == 1 for a in range(2, 561) if math.gcd(a, 561) == 1))   # → 1 True
```

The last line is a warning: **561 = 3 · 11 · 17 is not prime**, yet it passes the Fermat
test for every base coprime to it. Such numbers are **Carmichael numbers**, which is why
real primality tests use Miller–Rabin, a strengthened version with no such blind spots.

### The Chinese remainder theorem

If you know a number's remainders modulo several **pairwise coprime** moduli, you know
the number modulo their product — uniquely.

> **Worked example:** A number leaves remainder 2 when divided by 3, 3 when divided
> by 5 and 2 when divided by 7. Modulo $3 \cdot 5 \cdot 7 = 105$, it is 23. (This
> puzzle is from Sunzi's *Mathematical Classic*, around the 3rd–5th century.)

```python
def crt(remainders, moduli):
    x, m = 0, 1
    for r, n in zip(remainders, moduli):
        # find t with x + m*t ≡ r (mod n): t ≡ (r - x) * m⁻¹ (mod n)
        t = (r - x) * pow(m, -1, n) % n
        x, m = x + m * t, m * n
    return x % m

print(crt([2, 3, 2], [3, 5, 7]))   # → 23
```

CRT is how RSA implementations speed up decryption about fourfold (work mod p and
mod q separately, then combine), and why a counter split into several small
coprime-period counters can represent a huge range.

## 7 · RSA, Worked End to End

Everything above combines into the public-key cryptosystem published by Rivest, Shamir
and Adleman in 1977. With toy-sized numbers (real keys use primes of ~1024 bits each):

1. Pick two primes: $p = 61$, $q = 53$. Their product $n = 3233$ is public.
2. $\varphi(n) = (p-1)(q-1) = 3120$. Keep it secret.
3. Pick a public exponent e coprime to $\varphi(n)$: $e = 17$.
4. The private exponent is $d = e^{-1} \bmod \varphi(n) = 2753$ (§5).
5. **Encrypt** a message $m < n$: $c = m^e \bmod n$. **Decrypt**: $m = c^d \bmod n$.

```python
p, q = 61, 53
n, phi_n = p * q, (p - 1) * (q - 1)
e = 17
d = pow(e, -1, phi_n)
m = 65
c = pow(m, e, n)
print(n, phi_n, d)              # → 3233 3120 2753
print(c, pow(c, d, n))          # → 2790 65
print(all(pow(pow(x, e, n), d, n) == x for x in range(n)))   # → True
```

> **Notebook example:** Build a textbook RSA key small enough to do by hand, from the
> primes $p = 5$ and $q = 11$ with public exponent $e = 3$: find n, $\varphi(n)$ and the
> private exponent d.
>
> **What you need:** The key recipe above, restated. (1) $n = p \cdot q$; it is public.
> (2) $\varphi(n) = (p - 1)(q - 1)$, read "phi of n", counts the numbers from 1 to n that
> share no factor with n; it stays secret. (3) e must have $\gcd(e, \varphi(n)) = 1$.
> (4) d is the inverse of e mod $\varphi(n)$: the number with $e \cdot d \equiv 1$, which
> means $e \cdot d$ is one more than a multiple of $\varphi(n)$.
>
> **Plan:** follow the four lines of the recipe in order. Find d by checking which of 41,
> 81, 121, … (one more than a multiple of 40) is divisible by 3.
>
> 1. **Multiply the primes.** $n = 5 \times 11 = 55$.
> 2. **Compute phi.** $p - 1 = 4$ and $q - 1 = 10$, so $\varphi(55) = 4 \times 10 = 40$.
> 3. **Check that e is allowed.** Euclid: $40 = 13 \cdot 3 + 1$, then $3 = 3 \cdot 1 + 0$.
>    The last non-zero remainder is 1, so $\gcd(3, 40) = 1$ and e = 3 is fine.
>    *Why:* d is an inverse, and §5 showed an inverse exists only when the gcd is 1.
> 4. **List the candidates for 3d.** $3d$ must be one more than a multiple of 40: 41, 81,
>    121, …
> 5. **Try 41.** $41 = 13 \cdot 3 + 2$: not divisible by 3.
> 6. **Try 81.** $81 = 27 \cdot 3 + 0$: divisible. So $3d = 81$ and $d = 27$.
>
> **Answer:** the public key is $(n, e) = (55, 3)$ and the private exponent is $d = 27$.
> Anyone who could factor 55 into $5 \times 11$ could redo steps 2 to 6 and find d. That
> is the entire security argument, at toy scale.
>
> **Check:** $3 \times 27 = 81 = 2 \cdot 40 + 1$, so $e \cdot d \equiv 1 \pmod{40}$. In
> Python, `pow(3, -1, 40)` returns 27. ✓

> **Your turn:** Build the RSA key for $p = 3$, $q = 11$ and $e = 3$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Multiply the primes.** $n = 3 \times 11 = 33$.
> 2. **Compute phi.** $\varphi(33) = 2 \times 10 = 20$.
> 3. **Check that e is allowed.** $20 = 6 \cdot 3 + 2$, then $3 = 1 \cdot 2 + 1$: the gcd
>    is 1.
> 4. **List the candidates for 3d.** One more than a multiple of 20: 21, 41, 61, …
> 5. **Try 21.** $21 = 7 \cdot 3 + 0$: divisible, so $d = 7$.
>
> **Answer:** public key $(33, 3)$, private exponent $d = 7$ (check:
> $3 \cdot 7 = 21 = 1 \cdot 20 + 1$).
>
> </details>

> **Notebook example:** With the public key $(n, e) = (55, 3)$ from the previous example,
> encrypt the message $m = 9$.
>
> **What you need:** RSA **encryption** turns a message number m (smaller than n) into the
> **ciphertext** $c = m^e \bmod n$. The reduce-first rule (§3) lets you take the remainder
> after every multiplication, so the numbers stay small.
>
> **Plan:** compute $9^3$ as $9 \cdot 9 \cdot 9$, reducing mod 55 after each
> multiplication.
>
> 1. **Write out the power.** $c = 9^3 \bmod 55 = (9 \cdot 9 \cdot 9) \bmod 55$.
> 2. **Do the first multiplication.** $9 \times 9 = 81$.
> 3. **Reduce.** $81 = 1 \cdot 55 + 26$, so keep 26.
> 4. **Do the second multiplication.** $26 \times 9 = 234$.
> 5. **Reduce.** $4 \cdot 55 = 220$ and $234 - 220 = 14$, so $234 = 4 \cdot 55 + 14$:
>    keep 14.
>
> **Answer:** the ciphertext is $c = 14$. Anyone can compute it, because n and e are
> public.
>
> **Check:** the long way, $9^3 = 729$ and $729 = 13 \cdot 55 + 14$. In Python,
> `pow(9, 3, 55)` returns 14. ✓

> **Your turn:** With the public key $(33, 3)$, encrypt $m = 4$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write out the power.** $c = 4^3 \bmod 33$.
> 2. **Do the first multiplication.** $4 \times 4 = 16$, already below 33.
> 3. **Do the second multiplication.** $16 \times 4 = 64$.
> 4. **Reduce.** $64 = 1 \cdot 33 + 31$, so keep 31.
>
> **Answer:** the ciphertext is $c = 31$.
>
> </details>

> **Notebook example:** Decrypt the ciphertext $c = 14$ with the private exponent
> $d = 27$ and $n = 55$.
>
> **What you need:** RSA **decryption** is $m = c^d \bmod n$. For a big exponent, use
> **repeated squaring** (§4): write d as a sum of powers of two, build
> $c^1, c^2, c^4, c^8, \dots$ by squaring and reducing mod n each time, then multiply
> together the ones you need, reducing as you go. Each line below multiplies and then
> writes the result as $q \cdot 55 + r$ to find the remainder r.
>
> **Plan:** split 27 into powers of two, make the squares of 14, then multiply the needed
> ones in one at a time.
>
> 1. **Write 27 in powers of two.** $27 = 16 + 8 + 2 + 1$, so
>    $14^{27} = 14^{16} \cdot 14^{8} \cdot 14^{2} \cdot 14^{1}$.
> 2. **Square to get the 2nd power.** $14 \times 14 = 196 = 3 \cdot 55 + 31$, so
>    $14^2 \equiv 31$.
> 3. **Square to get the 4th power.** $31 \times 31 = 961 = 17 \cdot 55 + 26$, so
>    $14^4 \equiv 26$.
> 4. **Square to get the 8th power.** $26 \times 26 = 676 = 12 \cdot 55 + 16$, so
>    $14^8 \equiv 16$.
> 5. **Square to get the 16th power.** $16 \times 16 = 256 = 4 \cdot 55 + 36$, so
>    $14^{16} \equiv 36$.
> 6. **Multiply the 16th power by the 8th.** $36 \times 16 = 576 = 10 \cdot 55 + 26$:
>    running result 26.
>    *Why:* 27 uses 16, 8, 2 and 1 but not 4, so $14^4$ was only a stepping stone to
>    $14^8$.
> 7. **Multiply by the 2nd power.** $26 \times 31 = 806 = 14 \cdot 55 + 36$: running
>    result 36.
> 8. **Multiply by the 1st power.** $36 \times 14 = 504 = 9 \cdot 55 + 9$: result **9**.
>
> **Answer:** decryption gives back **m = 9**, the original message. Only the holder of d
> can do this, and d came from $\varphi(55) = 40$, which needs the factors 5 and 11.
>
> **Check:** `pow(14, 27, 55)` returns 9, and 9 is the message we encrypted. ✓

> **Your turn:** With $d = 7$ and $n = 33$, decrypt the ciphertext $c = 31$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write 7 in powers of two.** $7 = 4 + 2 + 1$, so $31^7 = 31^4 \cdot 31^2 \cdot 31^1$.
> 2. **Square to get the 2nd power.** $31 \times 31 = 961 = 29 \cdot 33 + 4$, so
>    $31^2 \equiv 4$.
> 3. **Square to get the 4th power.** $4 \times 4 = 16$, so $31^4 \equiv 16$.
> 4. **Multiply the 4th power by the 2nd.** $16 \times 4 = 64 = 1 \cdot 33 + 31$: running
>    result 31.
> 5. **Multiply by the 1st power.** $31 \times 31 = 961 = 29 \cdot 33 + 4$: result 4.
>
> **Answer:** $m = 4$, the message you encrypted in the previous Your turn.
>
> </details>

**Why decryption works:** $e d \equiv 1 \pmod{\varphi(n)}$, so $ed = 1 + k\varphi(n)$ and
$c^d = m^{ed} = m \cdot (m^{\varphi(n)})^k \equiv m \cdot 1^k = m$ by Euler's theorem (the
last line of the code checks every message, including those not coprime to n).

**Why it is secure:** anyone can compute $m^e \bmod n$. Undoing it needs d, which needs
$\varphi(n)$, which needs p and q — the factorisation of n. Multiplying two primes takes
microseconds; factoring a 2048-bit product is beyond every known classical computer.

> **Watch out:** This is textbook RSA, for understanding only. Real RSA adds
> randomised padding (OAEP), because textbook RSA is deterministic (the same message
> always gives the same ciphertext) and malleable. Never implement crypto yourself for
> production; use a vetted library.

## 8 · Hashing, Randomness and Check Digits

### Polynomial rolling hashes

To compare substrings quickly, treat a string as a number in base B, reduced mod a
large prime P:

$$
h(s) = \left(s_0 B^{k-1} + s_1 B^{k-2} + \dots + s_{k-1}\right) \bmod P
$$

Sliding the window one character right is O(1): subtract the leftmost character's
term, multiply by B, add the new character. That is **Rabin–Karp** string search, and
the idea behind rsync, content-defined chunking and plagiarism detectors. Equal hashes
mean "probably equal" — verify, or use two moduli.

```python
def find_all(text, pattern, B=256, P=1_000_000_007):
    k = len(pattern)
    if k > len(text):
        return []
    top = pow(B, k - 1, P)
    hp = hw = 0
    for i in range(k):
        hp = (hp * B + ord(pattern[i])) % P
        hw = (hw * B + ord(text[i])) % P
    hits = []
    for i in range(len(text) - k + 1):
        if hw == hp and text[i:i + k] == pattern:   # verify: equal hashes may still collide
            hits.append(i)
        if i + k < len(text):
            hw = ((hw - ord(text[i]) * top) * B + ord(text[i + k])) % P
    return hits

print(find_all("abracadabra", "abra"))   # → [0, 7]
```

### Modulo bias

`random_value % n` looks like a uniform choice from 0…n−1, but it is **biased** unless
n divides the size of the random range. With random bytes (0–255) reduced mod 10, the
values 0–5 appear 26 times in 256 and 6–9 only 25 times.

```python
counts = [0] * 10
for byte in range(256):
    counts[byte % 10] += 1
print(counts)   # → [26, 26, 26, 26, 26, 26, 25, 25, 25, 25]
```

Negligible for a game, fatal for key generation or a fair lottery. Correct libraries
(`random.randrange`, `secrets.randbelow`) reject the uneven top part of the range and
draw again.

### Check digits

A **check digit** is extra information that makes typos detectable. The **Luhn
algorithm** (credit cards, IMEI numbers) doubles every second digit from the right,
sums the digits, and requires the total to be $\equiv 0 \pmod{10}$. It catches every
single-digit error and most swaps of adjacent digits.

```python
def luhn_valid(number: str) -> bool:
    total = 0
    for i, ch in enumerate(reversed(number)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

print(luhn_valid("79927398713"))   # → True
print(luhn_valid("79927398712"))   # → False
print(luhn_valid("79927389713"))   # → False
```

ISBN-10 uses mod 11 (hence the occasional "X" check digit for 10); IBANs use mod 97.

> **Notebook example:** Is 79927398713 a valid Luhn number?
>
> **What you need:** The **Luhn rule**: number the digits from the **right**, starting at 1
> (the rightmost digit is the check digit). Double every digit in an even position (2nd,
> 4th, 6th, …). If a doubled value is more than 9, subtract 9 from it. Add up all the
> digits, changed and unchanged. The number is valid when the total is a multiple of 10,
> that is, $\text{total} \bmod 10 = 0$.
>
> **Plan:** read the digits right to left, split them into a "double" group and a "keep"
> group, add up each group, then test the total.
>
> 1. **Write the digits right to left.** 3, 1, 7, 8, 9, 3, 7, 2, 9, 9, 7 (positions 1
>    to 11).
> 2. **Pick out the even positions.** Positions 2, 4, 6, 8 and 10 hold 1, 8, 3, 2, 9.
> 3. **Double them.** 2, 16, 6, 4, 18.
> 4. **Fix the ones over 9.** $16 - 9 = 7$ and $18 - 9 = 9$, giving 2, 7, 6, 4, 9.
>    *Why:* subtracting 9 is the same as adding the two digits ($1 + 6 = 7$), so each
>    position still adds just one digit.
> 5. **Add the doubled group.** $2 + 7 + 6 + 4 + 9 = 28$.
> 6. **Add the kept group.** The odd positions 1, 3, 5, 7, 9, 11 hold 3, 7, 9, 7, 9, 7,
>    and $3 + 7 + 9 + 7 + 9 + 7 = 42$.
> 7. **Add the two groups.** $28 + 42 = 70$.
> 8. **Test the total.** $70 = 7 \cdot 10 + 0$: remainder 0.
>
> **Answer:** **valid**. Change any single digit, say the final 3 to a 4, and the total
> becomes 71, which is not a multiple of 10, so the typo is caught.
>
> **Check:** `luhn_valid("79927398713")` in the code above returns `True`, and its loop
> does exactly steps 2 to 8 (`i % 2 == 1` picks our even positions, because Python counts
> from 0). ✓

> **Your turn:** Is 5678 a valid Luhn number?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the digits right to left.** 8, 7, 6, 5.
> 2. **Pick out the even positions.** Positions 2 and 4 hold 7 and 5.
> 3. **Double them.** 14 and 10.
> 4. **Fix the ones over 9.** $14 - 9 = 5$ and $10 - 9 = 1$.
> 5. **Add everything.** Doubled group $5 + 1 = 6$; kept group $8 + 6 = 14$; total
>    $6 + 14 = 20$.
> 6. **Test the total.** $20 = 2 \cdot 10 + 0$: remainder 0.
>
> **Answer:** valid.
>
> </details>

## Common Mistakes

1. **Dividing mod n.** Multiply by an inverse, and check it exists (gcd = 1).
2. **Negative remainders** in C/Java/Go: normalise with `((a % n) + n) % n`.
3. **Overflow before reducing:** in fixed-width languages `a * b % n` can overflow if
   a, b < n but $a b$ exceeds 64 bits — keep n below $2^{31}$ or use 128-bit
   intermediates.
4. **`rand() % n`** where uniformity matters.
5. **Assuming a Fermat-test pass means prime** (Carmichael numbers).
6. **Trial division up to n** instead of $\sqrt{n}$, or with `range(2, int(n**0.5))`,
   which misses $\sqrt{n}$ itself — use `d * d <= n`.

## Check Yourself

**1.** What is $2^{100} \bmod 7$? (No calculator: find the cycle.)

<details>
<summary>Open the answer</summary>

Powers of 2 mod 7 cycle 2, 4, 1, 2, 4, 1, … with period 3. $100 = 3 \cdot 33 + 1$, so
$2^{100} \equiv 2^1 = 2$. `pow(2, 100, 7)` agrees.

</details>

**2.** Why do open-addressing hash tables often use a prime table size, or a probe
step that is odd when the size is a power of two?

<details>
<summary>Open the answer</summary>

Probing slot $h, h + s, h + 2s, \dots \pmod{m}$ visits every slot exactly when
$\gcd(s, m) = 1$ (the lab's add mode). A prime m makes every step 1…m−1 coprime; with
$m = 2^k$ any odd step is coprime.

</details>

**3.** Compute $\binom{n}{k} \bmod 10^9 + 7$ — why can you divide by $k!$ here but not
mod $10^9$?

<details>
<summary>Open the answer</summary>

$10^9 + 7$ is prime, so $k!$ (for $k < 10^9 + 7$) is coprime to it and has an inverse,
$(k!)^{p-2} \bmod p$. $10^9 = 2^9 5^9$ shares factors with most factorials, so the
inverse does not exist.

</details>

**4.** In the RSA example, why must e be coprime to $\varphi(n)$?

<details>
<summary>Open the answer</summary>

d is defined as the inverse of e mod $\varphi(n)$, which exists only when
$\gcd(e, \varphi(n)) = 1$. Without it there is no decryption exponent (and encryption
would not even be a bijection).

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Remainders and `%`; primes and trial division to √n; gcd with Euclid; modular addition and multiplication |
| **Interview-ready** | The sieve; lcm via gcd; fast modular exponentiation; modular inverses (when they exist, Fermat and extended Euclid); nCr mod p; gcd uses (rotation cycles, reduced slopes); rolling hashes; modulo bias |
| **Going deeper** | Fermat and Euler theorems with proofs; CRT; RSA end to end and why padding matters; Miller–Rabin and Carmichael numbers; the prime number theorem |

## Checklist

- [ ] I can test primality in $O(\sqrt{n})$ and sieve all primes up to N.
- [ ] I can run Euclid's algorithm by hand and explain why it is correct and fast.
- [ ] I reduce mod n after every addition and multiplication, and I never divide directly.
- [ ] I can implement fast modular exponentiation and find a modular inverse two ways.
- [ ] I can explain RSA's key generation, encryption, decryption and security in five sentences.
- [ ] I know why `rand() % n` is biased and how to fix it.
