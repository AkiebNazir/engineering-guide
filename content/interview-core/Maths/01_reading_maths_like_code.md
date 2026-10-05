# Reading Maths Like Code — Notation, Functions, Σ and Π

Maths notation is a programming language with very short variable names. Every symbol
is a compressed sentence, and almost every one of them has a direct translation into
code you already write: a function is a `def`, Σ is a `for` loop with an accumulator,
set-builder notation is a list comprehension, ∀ is `all()` and ∃ is `any()`. This
chapter builds that translation table from zero, so every later chapter — and every
algorithm paper, ML formula and complexity proof you meet — reads like code instead
of hieroglyphs.

**Where this fits:** Part 1 · The language of maths, chapter 1 of 15. **Builds on:** nothing beyond school arithmetic and basic Python, so this is a fine first chapter. **Used again in:** 05, 06. **Next in order:** [02 Number systems and binary](02_number_systems_and_binary.md).

## Where You Will Use This

| You meet… | For example | This chapter gives you |
|---|---|---|
| Complexity analysis | $\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$, so a triangle-shaped double loop is O(n²) | Σ as a loop, and how to simplify it |
| Machine learning papers | $\text{softmax}(z)_i = \frac{e^{z_i}}{\sum_j e^{z_j}}$ | Subscripts as array indices, Σ as `sum()` |
| Algorithm docs | $\lfloor \log_2 n \rfloor + 1$ bits | floor, log, and why `//` matters |
| Specifications | $\forall x \in S,\ f(x) \ge 0$ | Quantifiers as `all()` |
| Interviews | "Prove this loop terminates", "what is the sum of this series?" | The vocabulary to answer precisely |

## Foundations — Maths Is a Language

### Why notation exists

Try writing "add up the squares of the whole numbers from one to n" a hundred times.
Mathematicians got tired of it too, and invented $\sum_{i=1}^{n} i^2$. Notation is
compression. The price is that you must know the codebook — and nobody hands it to
you, which is why maths can feel like it is written for insiders. It is not harder
than code; it is *terser* than code.

> **Analogy:** Maths notation is like a regular expression. `^\d{3}-\d{4}$` is
> unreadable until someone tells you what `^`, `\d` and `{3}` mean — then it is a
> very precise, very short sentence. Formulas are the same: learn a few dozen symbols
> and they become the fastest way to say exactly what you mean.

### The translation table

Keep this table open while you read the rest of the module. Every row is expanded
below.

| Maths | Read it as | Python |
|---|---|---|
| $x = 3$ | "x is 3" (a fact, not an assignment) | `x == 3` is true |
| $f(x) = x^2 + 1$ | "f of x" | `def f(x): return x**2 + 1` |
| $f: \mathbb{Z} \to \mathbb{Z}$ | "f maps integers to integers" | `def f(x: int) -> int` |
| $\sum_{i=1}^{n} a_i$ | "sum of a-i for i from 1 to n" | `sum(a[i] for i in range(1, n + 1))` |
| $\prod_{i=1}^{n} a_i$ | "product of a-i …" | `math.prod(a[i] for i in range(1, n + 1))` |
| $a_i$, $a_{i,j}$ | "a sub i" | `a[i]`, `a[i][j]` |
| $\{x^2 \mid x \in S,\ x > 0\}$ | "the set of x² such that x is in S and positive" | `{x**2 for x in S if x > 0}` |
| $\forall x \in S,\ P(x)$ | "for all x in S, P holds" | `all(P(x) for x in S)` |
| $\exists x \in S,\ P(x)$ | "there exists x in S with P" | `any(P(x) for x in S)` |
| $\lfloor x \rfloor$, $\lceil x \rceil$ | "floor", "ceiling" | `math.floor(x)`, `math.ceil(x)` |
| $\lvert x \rvert$ | "absolute value" (or size of a set) | `abs(x)` (or `len(S)`) |
| $a \bmod n$ | "a mod n" | `a % n` |
| $n!$ | "n factorial" | `math.factorial(n)` |
| $\binom{n}{k}$ | "n choose k" | `math.comb(n, k)` |
| $\log_b x$ | "log base b of x" | `math.log(x, b)` |
| $\approx$, $\propto$ | "approximately", "proportional to" | — |

> **Key idea:** One big difference from code: in maths, `=` states that two things
> **are** equal. It is never "store this value". $x = x + 1$ is not an increment; it is
> a false statement (there is no such x). When you see an equation, read it as a
> claim you could test with `==`.

## 1 · Expressions and the Order of Operations

An expression is a recipe for a value. The order of operations is the same one your
compiler uses: brackets, then exponents, then multiplication and division, then
addition and subtraction (often remembered as BODMAS or PEMDAS).

Two conventions trip up programmers:

- **Juxtaposition means multiply.** $2x$ is `2 * x`, and $ab$ is `a * b` — not a
  two-letter variable. Single-letter names are the reason this works.
- **A minus sign binds weaker than an exponent.** $-2^2 = -(2^2) = -4$, not 4.
  Python agrees; Excel famously does not.

```python
print(-2**2)          # → -4
print((-2)**2)        # → 4
print(2 * 3 + 4)      # → 10
print(2 * (3 + 4))    # → 14
print(2 ** 3 ** 2)    # → 512
```

The last one surprises people: exponentiation is **right-associative**, so
$2^{3^2} = 2^9 = 512$, not $(2^3)^2 = 64$. Maths and Python agree here too.

> **Watch out:** Fractions group everything above and below the bar:
> $\frac{a + b}{c + d}$ is `(a + b) / (c + d)`. Writing `a + b / c + d` is the most
> common transcription bug when turning a formula into code.

> **Notebook example:** Evaluate $3 + 2 \cdot 4^2 - (6 - 2) \div 2$ by hand.
>
> 1. **Brackets first:** $6 - 2 = 4$, so the expression is $3 + 2 \cdot 4^2 - 4 \div 2$.
> 2. **Exponents:** $4^2 = 16$, giving $3 + 2 \cdot 16 - 4 \div 2$.
> 3. **Multiply and divide, left to right:** $2 \cdot 16 = 32$ and $4 \div 2 = 2$, giving
>    $3 + 32 - 2$.
> 4. **Add and subtract, left to right:** $3 + 32 = 35$, then $35 - 2 = 33$.
>
> **Answer:** 33. **Check the usual slip:** doing the addition first,
> $(3 + 2) \cdot 16 - 2 = 78$, is a completely different number. Write one line per rule
> and you cannot make that mistake.

## 2 · Functions: `def` With a Contract

### The idea

A function is a rule that takes an input and gives exactly one output. That is all.
$f(x) = x^2 + 1$ is a `def` with a one-line body.

> **Definition:** A **function** $f: A \to B$ assigns to every element of the set $A$
> (the **domain**, the allowed inputs) exactly one element of the set $B$ (the
> **codomain**, where outputs live). The outputs that actually occur form the
> **range** or **image**.

$f: A \to B$ is a type signature. `def f(x: int) -> float` says the same thing. The
important words are **every** (every input must have an output — no crashes) and
**exactly one** (the same input always gives the same output — no randomness, no
hidden state). A Python function that reads a global counter is not a function in
the maths sense; a pure function is.

### Functions you will see constantly

```python
import math

print(abs(-7))            # → 7
print(math.floor(3.7))    # → 3
print(math.ceil(3.2))     # → 4
print(math.floor(-3.7))   # → -4
print(17 % 5)             # → 2
print(math.factorial(5))  # → 120
print(math.comb(5, 2))    # → 10
```

$\lfloor x \rfloor$ ("floor") rounds **down** to the nearest integer and
$\lceil x \rceil$ ("ceiling") rounds **up**. Note that $\lfloor -3.7 \rfloor = -4$:
down means towards minus infinity, not towards zero.

> **In practice:** "How many pages of 10 results do I need for 95 results?" is
> $\lceil 95 / 10 \rceil = 10$. In integer code the ceiling trick is
> `(n + k - 1) // k`, which avoids floating point entirely.

```python
n, k = 95, 10
print((n + k - 1) // k)   # → 10
print(-(-n // k))          # → 10
```

### Integer division and mod: where languages disagree

Maths defines division with remainder so that the remainder is never negative:
$a = q \cdot n + r$ with $0 \le r < n$. Python follows maths. C, C++, Java, Go, Rust
and JavaScript **truncate towards zero** instead, so their `%` can be negative.

```python
print(-7 // 2)   # → -4
print(-7 % 2)    # → 1
print(int(-7 / 2))   # → -3
```

In C or Java, `-7 / 2` is `-3` and `-7 % 2` is `-1`. This matters the moment you
compute a hash bucket or a circular-buffer index from a value that can be negative:
`index = h % size` can go negative in Java and crash with an out-of-range index. The
portable fix is `((h % size) + size) % size`.

> **Interview angle:** "Is `x % 2 == 1` a correct test for odd numbers?" In Python,
> yes. In Java or C, no: `-3 % 2` is `-1`. Use `x % 2 != 0` or `(x & 1) == 1`.

### Composition and inverse

Composing functions is chaining calls: $(f \circ g)(x) = f(g(x))$ — apply g first,
then f. Read ∘ right to left, like nested calls.

An **inverse** $f^{-1}$ undoes f: $f^{-1}(f(x)) = x$. Encoding and decoding,
`json.dumps` and `json.loads`, encrypt and decrypt are inverse pairs. Not every
function has one: `abs` sends both 3 and −3 to 3, so from the output 3 you cannot
tell which input you had. Chapter 04 makes this precise (only **bijections** are
invertible) with a lab.

```python
import json
f = json.dumps
g = json.loads
x = {"a": [1, 2]}
print(g(f(x)) == x)   # → True
```

> **Watch out:** $f^{-1}(x)$ means the inverse function, **not** $\frac{1}{f(x)}$.
> But $\sin^2 x$ means $(\sin x)^2$. Notation is not always consistent; context
> decides.

### Piecewise functions are `if` statements

$$
\lvert x \rvert = \begin{cases} x & \text{if } x \ge 0 \\ -x & \text{if } x < 0 \end{cases}
$$

is exactly

```python
def absolute(x):
    if x >= 0:
        return x
    return -x

print(absolute(-5), absolute(5))   # → 5 5
```

> **Notebook example:** Let $f(x) = x^2 + 1$ and $g(x) = 2x - 3$. Find $(f \circ g)(4)$,
> $(g \circ f)(4)$ and $g^{-1}$, then divide $-7$ by 2 "the maths way".
>
> 1. $(f \circ g)(4)$: apply g **first**. $g(4) = 2 \cdot 4 - 3 = 5$. Then
>    $f(5) = 5^2 + 1 = 26$.
> 2. $(g \circ f)(4)$: apply f first. $f(4) = 16 + 1 = 17$. Then $g(17) = 34 - 3 = 31$.
>    Different from step 1: **the order of composition matters.**
> 3. Inverse of g: write $y = 2x - 3$ and solve for x: $y + 3 = 2x$, so
>    $x = \frac{y + 3}{2}$. So $g^{-1}(y) = \frac{y + 3}{2}$.
> 4. Check the inverse: $g^{-1}(g(4)) = g^{-1}(5) = \frac{5 + 3}{2} = 4$. ✓
> 5. Divide $-7$ by 2 with $-7 = q \cdot 2 + r$ and $0 \le r < 2$:
>    $q = \lfloor -3.5 \rfloor = -4$ (floor goes **down**, towards minus infinity), and
>    $r = -7 - (-4)(2) = -7 + 8 = 1$.
>
> **Answer:** 26, 31, $g^{-1}(y) = (y + 3)/2$, and $-7 = (-4)(2) + 1$. That quotient and
> remainder are exactly Python's `-7 // 2` and `-7 % 2`.

## 3 · Σ and Π Are Loops

This is the single most useful translation in the chapter.

$$
\sum_{i=1}^{n} f(i) = f(1) + f(2) + \dots + f(n)
$$

- The big Σ (capital sigma, "S" for **sum**) means *add up*.
- $i = 1$ underneath is the loop variable and its start.
- $n$ on top is the last value, **inclusive**.
- $f(i)$ to the right is the loop body.

```python
def sigma(f, lo, hi):
    total = 0                       # the empty sum is 0
    for i in range(lo, hi + 1):     # note: hi is INCLUSIVE in maths
        total += f(i)
    return total

print(sigma(lambda i: i, 1, 100))       # → 5050
print(sigma(lambda i: i * i, 1, 10))    # → 385
print(sigma(lambda i: 2 ** i, 0, 10))   # → 2047
```

Π (capital pi, "P" for **product**) is the same loop with `*=` and a start value of 1
(the **empty product** is 1, just as the empty sum is 0).

```python
import math
print(math.prod(range(1, 6)))   # → 120
```

$\prod_{i=1}^{5} i = 5! = 120$.

**Try it: watch Σ run as a loop.** Pick Σ i, press *Run the loop*, and watch the code's
`total` and the bars grow one iteration at a time; the chips compare the loop's
answer with the closed-form formula. Then switch to Σ 2ⁱ (the last bar is bigger than
all the others combined) and Σ 1/2ⁱ (the total creeps towards 1 but never reaches it).

<div class="lab" data-viz="math-sigma"></div>

### Gauss's trick: why $\sum_{i=1}^{n} i = \frac{n(n+1)}{2}$

The story goes that a young Carl Friedrich Gauss was told to add 1 to 100 and
answered in seconds. Write the sum forwards and backwards and add the two rows:

```
   1 +   2 +   3 + … +  99 + 100
 100 +  99 +  98 + … +   2 +   1
 ─────────────────────────────────
 101 + 101 + 101 + … + 101 + 101     ← n columns, each n + 1
```

Two copies of the sum make $n(n+1)$, so one copy is $\frac{n(n+1)}{2}$. For
$n = 100$ that is 5050.

> **In practice:** This is the reason a loop like `for i in range(n): for j in
> range(i):` is O(n²): the inner loop runs 0 + 1 + … + (n − 1) = n(n − 1)/2 times.
> Every "compare each pair once" algorithm has this cost.

### Rules for manipulating sums (they are loop refactorings)

| Rule | Maths | As code |
|---|---|---|
| Constants factor out | $\sum c \cdot a_i = c \sum a_i$ | multiply once after the loop instead of every iteration |
| Sums split | $\sum (a_i + b_i) = \sum a_i + \sum b_i$ | one loop doing two things = two loops |
| Index shift | $\sum_{i=1}^{n} a_i = \sum_{j=0}^{n-1} a_{j+1}$ | switching between 0- and 1-based indexing |
| Counting | $\sum_{i=1}^{n} 1 = n$ | a loop that adds 1 counts its iterations |
| Double sums | $\sum_i \sum_j a_{ij}$ | nested loops |
| Swap order | $\sum_i \sum_j a_{ij} = \sum_j \sum_i a_{ij}$ (finite sums) | swap the loops: same total |

```python
a = [3, 1, 4, 1, 5]
b = [9, 2, 6, 5, 3]
lhs = sum(2 * x + y for x, y in zip(a, b))
rhs = 2 * sum(a) + sum(b)
print(lhs, rhs)   # → 53 53
```

Swapping the order of a double sum is how many clever algorithms are born. "For each
pair, count …" can often be rewritten as "for each element, count how many pairs it
is in", turning O(n²) into O(n).

> **Worked example:** The total of all subarray sums of `[1, 2, 3]`. Brute force
> sums every subarray (O(n³), or O(n²) with prefix sums). Swap the order: element
> `a[i]` appears in `(i + 1) * (n - i)` subarrays (choose a start at or before i and
> an end at or after it), so the answer is $\sum_i a_i (i+1)(n-i)$ — one loop, O(n).

```python
def all_subarray_sums_brute(a):
    n = len(a)
    return sum(sum(a[l:r + 1]) for l in range(n) for r in range(l, n))

def all_subarray_sums_fast(a):
    n = len(a)
    return sum(x * (i + 1) * (n - i) for i, x in enumerate(a))

print(all_subarray_sums_brute([1, 2, 3]), all_subarray_sums_fast([1, 2, 3]))   # → 20 20
import random
xs = [random.randint(-9, 9) for _ in range(50)]
assert all_subarray_sums_brute(xs) == all_subarray_sums_fast(xs)
```

## 4 · Exponents and Logarithms in One Page

Exponents are repeated multiplication: $2^5 = 2 \cdot 2 \cdot 2 \cdot 2 \cdot 2 = 32$.
A **logarithm** asks the reverse question: $\log_2 32 = 5$ means "2 to what power
gives 32?" For computer scientists the most useful reading is:

> **Intuition:** $\log_2 n$ is **the number of times you can halve n before you reach
> 1**. That is why it appears wherever an algorithm throws away half of the problem
> per step (binary search, balanced trees, merge sort's depth). Chapter 06 has a lab.

| Rule | Example | Why you care |
|---|---|---|
| $b^{x} \cdot b^{y} = b^{x+y}$ | $2^{10} \cdot 2^{10} = 2^{20}$ | KB × KB ≈ MB |
| $(b^x)^y = b^{xy}$ | $(2^{10})^3 = 2^{30}$ | 1 GiB = 2³⁰ bytes |
| $b^0 = 1$, $b^{-x} = 1/b^x$ | $2^{-1} = 0.5$ | fractional bits, halving |
| $\log(xy) = \log x + \log y$ | multiplying becomes adding | log-probabilities avoid underflow |
| $\log(x^k) = k \log x$ | $\log_2 (2^{20}) = 20$ | |
| $\log_b x = \frac{\log_c x}{\log_c b}$ | $\log_2 x = \ln x / \ln 2$ | any base is a constant factor away from any other |

The last row is why complexity analysis never writes the base: $\log_2 n$ and
$\log_{10} n$ differ by a constant factor ($\log_2 10 \approx 3.32$), and Big-O drops
constant factors. $\ln$ means log base $e \approx 2.718$ (the "natural" log, see
chapter 12).

```python
import math
print(math.log2(1024))                 # → 10.0
print(round(math.log(1_000_000, 10)))  # → 6
print((1_000_000).bit_length())        # → 20
print(math.ceil(math.log2(1_000_000))) # → 20
```

> **Precision note:** `math.log(x, b)` is computed as `log(x) / log(b)` in floating
> point and can land a hair below an exact integer — `math.log(1000, 10)` is
> `2.9999999999999996` in CPython. Never `int()` a floating-point log; use
> `math.log2`/`math.log10`, integer `bit_length()`, or round deliberately.

```python
import math
print(math.log(1000, 10))        # → 2.9999999999999996
print(int(math.log(1000, 10)))   # → 2
print(math.log10(1000))          # → 3.0
```

> **Notebook example:** Without a calculator, find $\log_2(8 \cdot 32)$, $\log_8 64$ and
> roughly $\log_2 1{,}000{,}000$.
>
> 1. Product rule: $\log_2(8 \cdot 32) = \log_2 8 + \log_2 32 = 3 + 5 = 8$.
>    Check: $8 \cdot 32 = 256 = 2^8$. ✓
> 2. Change of base to 2: $\log_8 64 = \frac{\log_2 64}{\log_2 8} = \frac{6}{3} = 2$.
>    Check: $8^2 = 64$. ✓
> 3. Estimate with $2^{10} \approx 10^3$:
>    $1{,}000{,}000 = (10^3)^2 \approx (2^{10})^2 = 2^{20}$, so
>    $\log_2 1{,}000{,}000 \approx 20$.
>
> **Answer:** 8, 2 and about 20. That means a binary search over a million sorted items
> takes about 20 steps.

## 5 · Sets, Comprehensions and Quantifiers

Set-builder notation is Python's comprehension syntax — Python borrowed it from maths.

$$
\{\, x^2 \mid x \in \{1, \dots, 10\},\ x \text{ odd} \,\}
$$

reads "the set of x² such that x is in 1…10 and x is odd":

```python
print({x**2 for x in range(1, 11) if x % 2 == 1} == {1, 9, 25, 49, 81})   # → True
```

The bar $\mid$ (or a colon) means **such that**. Everything before it is the output
expression; everything after it is the generator and the filter.

**Quantifiers** turn a property of one element into a statement about a whole set:

- $\forall$ ("for all", an upside-down A) is `all(...)`.
- $\exists$ ("there exists", a backwards E) is `any(...)`.

```python
S = [4, 8, 15, 16, 23, 42]
print(all(x > 0 for x in S))        # → True
print(any(x % 5 == 0 for x in S))   # → True
print(all(x % 2 == 0 for x in S))   # → False
print(all(x > 100 for x in []))     # → True
```

The last line is not a bug: "every element of the empty set is greater than 100" is
**vacuously true** — there is no counterexample. It is the same reason the empty sum
is 0 and the empty product is 1: they are the identity values, so that splitting a
loop into pieces always works.

> **Key idea:** To show a "for all" claim is false you need **one counterexample**. To
> show a "there exists" claim is true you need **one example**. To prove a "for all"
> claim true you need an argument (chapter 03) — testing a million cases is evidence,
> not proof.

Negating quantifiers flips them: "not every x is positive" means "some x is not
positive": $\neg \forall x\, P(x) \equiv \exists x\, \neg P(x)$. In code,
`not all(p(x) for x in S) == any(not p(x) for x in S)`.

> **Notebook example:** Let $S = \{\, x^2 \mid x \in \{1, \dots, 6\},\ x \text{ even} \,\}$.
> List S, then decide $\forall x \in S: x > 3$, $\exists x \in S: x > 20$ and
> $\forall x \in S: x < 30$.
>
> 1. **Generator and filter:** the even x in 1…6 are 2, 4 and 6.
> 2. **Output expression:** square each one, giving $S = \{4, 16, 36\}$.
> 3. $\forall x \in S: x > 3$. Check every element: 4 > 3, 16 > 3, 36 > 3. **True.**
> 4. $\exists x \in S: x > 20$. One witness is enough: 36 > 20. **True.**
> 5. $\forall x \in S: x < 30$. Negate it: $\exists x \in S: x \ge 30$. The witness is 36,
>    so the negation is true and the original claim is **false**. One counterexample
>    kills a "for all".

## 6 · The Symbol Cheat Sheet

### Greek letters and what they usually mean

| Letter | Name | Usual meaning |
|---|---|---|
| α, β | alpha, beta | learning rate, significance level; generic parameters |
| γ | gamma | discount factor (reinforcement learning), Euler's constant 0.5772… |
| δ, Δ | delta | a small change; Δx = "change in x" |
| ε | epsilon | a tiny positive number, an error tolerance, the empty string |
| θ | theta | an angle; model parameters |
| λ | lambda | an eigenvalue, a rate (events per second), an anonymous function |
| μ | mu | a mean (average) |
| π | pi | 3.14159…; also a permutation or a policy |
| σ, Σ | sigma | standard deviation; Σ = sum, also an alphabet in automata |
| φ | phi | golden ratio 1.618…, Euler's totient |
| ω, Ω | omega | lower bound in complexity (Ω), sample space |

### Sets of numbers

| Symbol | Name | Contains | Programming analogue |
|---|---|---|---|
| $\mathbb{N}$ | natural numbers | 0, 1, 2, … (some books start at 1) | unsigned integers |
| $\mathbb{Z}$ | integers | …, −2, −1, 0, 1, 2, … | Python `int` |
| $\mathbb{Q}$ | rationals | fractions p/q | `fractions.Fraction` |
| $\mathbb{R}$ | reals | every point on the number line | approximated by `float` |
| $\mathbb{C}$ | complex numbers | a + bi | `complex` |

### Relations and logic

| Symbol | Meaning | Symbol | Meaning |
|---|---|---|---|
| $\in$, $\notin$ | is (not) an element of | $\Rightarrow$ | implies |
| $\subseteq$ | is a subset of | $\Leftrightarrow$, iff | if and only if |
| $\cup$, $\cap$ | union, intersection | $\equiv$ | is equivalent to / congruent to |
| $\emptyset$ | empty set | $\approx$ | approximately equal |
| $\land$, $\lor$, $\neg$ | and, or, not | $\propto$ | proportional to |
| $\infty$ | infinity (a limit, not a number) | $:=$ | "is defined as" |

## 7 · How to Read a Formula You Have Never Seen

A four-step method that works on anything, from a textbook to a research paper:

1. **Type-check every symbol.** Is it a number, a vector, a set, a function? What are
   the loop variables (they appear under Σ, Π, or after ∀)?
2. **Plug in tiny numbers.** n = 1, n = 2, n = 3. Compute by hand.
3. **Write it as code.** Every Σ becomes a loop, every subscript an index.
4. **Sanity-check the result.** Units, signs, edge cases (empty input, zero), and
   what happens as numbers get large.

> **Worked example:** The **softmax** function turns scores into probabilities:
>
> $$\text{softmax}(z)_i = \frac{e^{z_i}}{\sum_{j=1}^{K} e^{z_j}}$$
>
> Step 1: $z$ is a vector of K numbers, $i$ and $j$ are indices, $e^{x}$ is `exp`.
> Step 2: for $z = (0, 0)$ both outputs are $1/2$. Step 3 below. Step 4: outputs are
> positive and add to 1 (they are probabilities); a big $z_i$ gets most of the mass.

```python
import math

def softmax(z):
    m = max(z)                              # subtracting the max changes nothing mathematically…
    exps = [math.exp(x - m) for x in z]     # …but prevents overflow for large scores
    total = sum(exps)
    return [e / total for e in exps]

print(softmax([0, 0]))                             # → [0.5, 0.5]
print([round(p, 3) for p in softmax([1, 2, 3])])   # → [0.09, 0.245, 0.665]
print(round(sum(softmax([1000, 1001, 1002])), 6))  # → 1.0
```

Step 4 found something the formula alone hides: computed naively, `exp(1000)`
overflows a float. The fix — subtract the maximum first — comes straight from the
maths: $\frac{e^{z_i - m}}{\sum_j e^{z_j - m}} = \frac{e^{-m} e^{z_i}}{e^{-m} \sum_j e^{z_j}}$,
the same value.

## Common Mistakes

1. **Off-by-one on Σ bounds.** $\sum_{i=1}^{n}$ has n terms and includes n. Python's
   `range(1, n)` stops at n − 1. Write `range(1, n + 1)`.
2. **Reading = as assignment.** An equation is a claim both sides are equal.
3. **Trusting `%` and `//` with negative numbers across languages.** Python floors,
   C/Java/Go truncate.
4. **`int(math.log(x, b))`** to count digits or bits. Use exact integer methods.
5. **$f^{-1}$ as $1/f$.** It is the inverse function.
6. **Forgetting empty cases.** Σ over nothing is 0, Π over nothing is 1, ∀ over nothing
   is true, ∃ over nothing is false.

## Check Yourself

**1.** Translate $\sum_{i=0}^{n-1} \sum_{j=i+1}^{n-1} 1$ into code. What does it count,
and what is its closed form?

<details>
<summary>Open the answer</summary>

Two nested loops, `for i in range(n): for j in range(i + 1, n): count += 1`. It counts
the pairs (i, j) with i < j — every unordered pair once. The inner loop runs
n − 1, n − 2, …, 0 times, so the total is $\frac{n(n-1)}{2} = \binom{n}{2}$.

</details>

**2.** What is $\lceil \log_2 1000 \rceil$, and what does it mean for binary search?

<details>
<summary>Open the answer</summary>

$2^9 = 512 < 1000 \le 1024 = 2^{10}$, so it is 10. Binary search over 1000 sorted items
needs at most 10 halvings to shrink the range to one item (11 comparisons in the
common implementation that also checks the final element).

</details>

**3.** Is "every element of an empty list is negative" true or false? What do
`all([])` and `any([])` return?

<details>
<summary>Open the answer</summary>

True (vacuously): there is no counterexample. `all([])` is `True`, `any([])` is
`False` — the identities for AND and OR, just as 0 is for + and 1 for ×.

</details>

**4.** A formula says $\bar{x} = \frac{1}{n} \sum_{i=1}^{n} x_i$. Say it in words and in code.

<details>
<summary>Open the answer</summary>

"x-bar is the average of the x's": `sum(xs) / len(xs)`. The bar over a letter usually
means "mean of". Undefined for n = 0 — check the empty case.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Read Σ, Π, subscripts, set-builder notation and ∀/∃ as code; floor and ceiling; the log/exponent rules |
| **Interview-ready** | Derive Gauss's sum; simplify nested sums into closed forms to state complexity; know language differences in `%` and `//`; translate any formula into correct, numerically safe code |
| **Going deeper** | Swap summation order to turn O(n²) counting into O(n); explain numerical stability tricks (log-sum-exp) from the algebra; read a paper's notation section and implement it |

## Checklist

- [ ] I can translate Σ, Π, set-builder, ∀ and ∃ into Python without looking.
- [ ] I can state and prove $\sum_{i=1}^{n} i = n(n+1)/2$.
- [ ] I know why `-7 // 2` is −4 in Python and −3 in C, and how to write a safe modulo.
- [ ] I use `(n + k - 1) // k` for integer ceiling division.
- [ ] I never convert a floating-point log to an int without rounding deliberately.
- [ ] Given an unfamiliar formula, I type-check, plug in small numbers, code it, and sanity-check it.
