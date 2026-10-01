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

> **Notebook example:** Is 221 prime? Factorise 360 and count its divisors.
>
> 1. $\sqrt{221}$ is a bit under 15 ($15^2 = 225$), so try the primes up to 13.
> 2. 221 is odd, so not 2. Its digit sum is 5, so not 3. It does not end in 0 or 5, so
>    not 5. $221 = 7 \times 31 + 4$, so not 7. $221 = 11 \times 20 + 1$, so not 11.
>    $221 = 13 \times 17$. **Composite.**
> 3. Factor tree for 360: $360 = 2 \times 180 = 2 \times 2 \times 90 = 2 \times 2 \times 2 \times 45 = 2^3 \times 3 \times 15 = 2^3 \times 3^2 \times 5$.
> 4. A divisor picks each prime's exponent independently: 0–3 for 2, 0–2 for 3, 0–1
>    for 5. That is $(3 + 1)(2 + 1)(1 + 1) = 24$ divisors.
>
> **Answer:** $221 = 13 \times 17$, $360 = 2^3 \cdot 3^2 \cdot 5$, with 24 divisors.

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

> **Notebook example:** One job runs every 252 minutes and another every 198 minutes.
> Both ran at midnight. When do they next run together?
>
> 1. Euclid: $252 = 1 \times 198 + 54$.
> 2. $198 = 3 \times 54 + 36$.
> 3. $54 = 1 \times 36 + 18$.
> 4. $36 = 2 \times 18 + 0$. The last non-zero remainder is the gcd: **18**.
> 5. $\text{lcm} = \frac{252 \times 198}{18} = 14 \times 198 = 2772$.
>
> **Answer:** after 2,772 minutes, which is 46 h 12 min. **Check** with the
> factorisations: $252 = 2^2 \cdot 3^2 \cdot 7$ and $198 = 2 \cdot 3^2 \cdot 11$. The gcd
> takes the lower powers, $2 \cdot 3^2 = 18$ ✓. The lcm takes the higher powers,
> $2^2 \cdot 3^2 \cdot 7 \cdot 11 = 2772$ ✓.

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

> **Notebook example:** Compute $(47 \times 58 + 93) \bmod 7$ without big numbers. Then
> find the weekday 100 days after a Wednesday.
>
> 1. Reduce each number first: $47 = 42 + 5 \equiv 5$, $58 = 56 + 2 \equiv 2$ and
>    $93 = 91 + 2 \equiv 2$.
> 2. Compute with the small numbers: $5 \times 2 + 2 = 12 \equiv 12 - 7 = 5$.
> 3. **Check** the long way: $47 \times 58 = 2726$, and $2726 + 93 = 2819 = 7 \times 402 + 5$. ✓
> 4. Weekdays repeat every 7 days, and $100 = 14 \times 7 + 2$, so move 2 days on from
>    Wednesday: **Friday**.
>
> **Answer:** 5, and Friday.

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
> 1. Exponent in binary: $13 = 8 + 4 + 1 = 1101_2$.
> 2. Square repeatedly, reducing each time: $3^1 \equiv 3$, $3^2 = 9 \equiv 2$,
>    $3^4 \equiv 2^2 = 4$, $3^8 \equiv 4^2 = 16 \equiv 2$.
> 3. Multiply the powers whose bit is 1 (8, 4 and 1): $2 \times 4 \times 3 = 24 \equiv 3$.
>
> **Answer:** 3, from 3 squarings and 2 multiplications instead of 12 multiplications.
> **Check** with Fermat: $3^6 \equiv 1 \pmod 7$, so $3^{13} = (3^6)^2 \cdot 3 \equiv 3$. ✓

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

> **Notebook example:** Find the inverse of 7 mod 26 with the extended Euclidean
> algorithm.
>
> 1. Run Euclid forwards: $26 = 3 \times 7 + 5$, then $7 = 1 \times 5 + 2$, then
>    $5 = 2 \times 2 + 1$. The gcd is 1, so an inverse exists.
> 2. Run it backwards, writing 1 in terms of the earlier numbers:
>    $1 = 5 - 2 \times 2$.
> 3. Replace 2 using $2 = 7 - 5$: $1 = 5 - 2(7 - 5) = 3 \times 5 - 2 \times 7$.
> 4. Replace 5 using $5 = 26 - 3 \times 7$: $1 = 3(26 - 3 \times 7) - 2 \times 7 = 3 \times 26 - 11 \times 7$.
> 5. Read it mod 26: $-11 \times 7 \equiv 1$, so the inverse is $-11 \equiv 15$.
>
> **Answer:** 15. **Check:** $7 \times 15 = 105 = 4 \times 26 + 1$. ✓

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

> **Notebook example:** Textbook RSA small enough to do by hand: $p = 5$, $q = 11$,
> $e = 3$. Encrypt $m = 9$, then decrypt.
>
> 1. $n = 5 \times 11 = 55$ and $\varphi(n) = 4 \times 10 = 40$. Since $\gcd(3, 40) = 1$,
>    $e = 3$ is allowed.
> 2. $d = 3^{-1} \bmod 40$: $3 \times 27 = 81 = 2 \times 40 + 1$, so $d = 27$.
> 3. **Encrypt:** $c = 9^3 \bmod 55 = 729 \bmod 55$. $55 \times 13 = 715$, so $c = 14$.
> 4. **Decrypt:** $14^{27} \bmod 55$ by squaring. $14^2 = 196 \equiv 31$,
>    $14^4 \equiv 31^2 = 961 \equiv 26$, $14^8 \equiv 26^2 = 676 \equiv 16$,
>    $14^{16} \equiv 16^2 = 256 \equiv 36$.
> 5. $27 = 16 + 8 + 2 + 1$, so multiply those powers: $36 \times 16 = 576 \equiv 26$,
>    $26 \times 31 = 806 \equiv 36$, $36 \times 14 = 504 \equiv 9$.
>
> **Answer:** $c = 14$, and decryption gives back $m = 9$. ✓ Anyone who could factor 55
> would find d in step 2. That is the entire security argument, at toy scale.

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
> 1. Write the digits from the right: 3, 1, 7, 8, 9, 3, 7, 2, 9, 9, 7.
> 2. Double every second one (2nd, 4th, …): 1 → 2, 8 → 16, 3 → 6, 2 → 4, 9 → 18.
> 3. Wherever a double is over 9, subtract 9 (the same as adding its digits): 16 → 7 and
>    18 → 9. The doubled digits are now 2, 7, 6, 4, 9, which sum to 28.
> 4. The untouched digits 3, 7, 9, 7, 9, 7 sum to 42.
> 5. Total $28 + 42 = 70$, and $70 \bmod 10 = 0$.
>
> **Answer:** valid. Change any single digit (say the last 3 to 4) and the total becomes
> 71, which is not divisible by 10, so the typo is caught.

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
