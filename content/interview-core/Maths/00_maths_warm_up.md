# Maths Warm-Up — The School Maths Everything Else Uses

If you have not done this since school, or maths always felt like a test you were about
to fail, this chapter is for you. Most people who get stuck on "CS maths" are not stuck
on the computer science at all. They are stuck one layer down: a minus sign in the wrong
place, a fraction that will not add up, a power they half remember, or an equation they
are not sure how to rearrange. This chapter rebuilds exactly that layer, slowly, with
tiny numbers and one move at a time. It takes 30–60 minutes. Each section opens with a
one-line test; if you can already do it, skip the section with a clear conscience.

**Where this fits:** Part 0 · Warm-up, an optional chapter before chapter 1. **Builds on:** nothing but counting and basic Python. **Used again in:** every chapter, especially 01, 05, 06, 09, 10 and 12. **Next in order:** [01 Reading maths like code](01_reading_maths_like_code.md).

## Where You Will Use This

| You meet… | For example | This chapter gives you |
|---|---|---|
| Error rates and SLAs | "99.9% uptime" allows about 43 minutes of downtime in a 30-day month | Percentages, and how to take a percentage of something |
| Probabilities | Rolling a 6 has probability $\frac{1}{6}$; two independent events multiply | Fractions: what they mean and how to add and multiply them |
| Complexity and memory | $2^n$ subsets, $2^{10} = 1024$ bytes in a KB, $2^{20}$ in a MB | Powers, powers of 2, and scientific notation |
| Capacity estimates | "Each server handles 300 requests per second; we need 1,200. How many servers?" | Rearranging a formula to solve for the letter you want |
| Performance graphs | "Latency grows 2 ms per 100 users" | Slope, straight lines and $y = mx + b$ |
| Back-of-the-envelope maths | "Is 1,900 requests per second a million or a billion a day?" | Rounding, estimating and sanity checks |

## Foundations — You Already Know More Than You Think

Everything in this chapter is built from four things you already do every day: count,
share, scale up and balance. Negative numbers are counting below zero. Fractions are
sharing. Powers are scaling up again and again. Equations are balancing. The symbols are
only a short way of writing those everyday actions down.

> **Analogy:** School maths is like the standard library of a programming language. Nobody
> admires `len()` or `sorted()`, but every interesting program leans on them, and a bug in
> how you *use* them breaks everything above. This chapter is a quick tour of that standard
> library, so the clever parts of later chapters have something solid to stand on.

### The symbols in this chapter

| Symbol | Read it as | Python |
|---|---|---|
| $3 \times 4$, $3 \cdot 4$, $3(4)$ | "3 times 4" (all three mean the same) | `3 * 4` |
| $2x$ | "2 times x" (a number stuck to a letter means multiply) | `2 * x` |
| $12 \div 3$, $\frac{12}{3}$, $12/3$ | "12 divided by 3" | `12 / 3` |
| $2^3$ | "2 to the power 3", that is $2 \times 2 \times 2$ | `2 ** 3` |
| $\sqrt{9}$ | "the square root of 9", the number that squares to 9 | `math.sqrt(9)` |
| $\approx$ | "is roughly equal to" | — |
| $-5$ | "minus 5" or "negative 5" | `-5` |

> **Key idea:** Brackets are done first, then powers, then × and ÷ (left to right), then
> + and − (left to right). Python follows the same order, so when in doubt you can always
> type the expression into Python and compare.

## 1 · Negative Numbers

**Skip this if you can already** work out $-4 + 7 - (-2)$ and $(-3) \times (-4)$ without
hesitating (answers: 5 and 12).

### The number line

Picture a ruler that carries on past zero to the left. Numbers to the right of zero are
positive; numbers to the left are negative. A thermometer below freezing, a bank balance
in the red, or a list index counted from the end (`xs[-1]`) all live on the left side.

```
  -5  -4  -3  -2  -1   0   1   2   3   4   5
 --+---+---+---+---+---+---+---+---+---+---+-->
   ← smaller                         bigger →
```

- **Adding** a positive number moves you **right**.
- **Subtracting** a positive number moves you **left**.
- **Subtracting a negative** is the same as **adding** the positive: $5 - (-2) = 5 + 2$.
  Taking away a debt of 2 leaves you 2 better off.
- **Adding a negative** is the same as **subtracting**: $5 + (-2) = 5 - 2$.

> **Notebook example:** Work out $-4 + 7 - (-2)$.
>
> **What you need:** On the number line, adding a positive number moves you right and
> subtracting moves you left. Two minus signs side by side, as in $-(-2)$, become a plus:
> taking away a negative is the same as adding.
>
> **Plan:** start at −4 and do one move at a time, left to right.
>
> 1. **Start at the first number.** Put your finger on −4 on the number line.
> 2. **Add 7.** Move 7 steps right: −3, −2, −1, 0, 1, 2, 3. You land on 3.
>    *Why:* adding a positive number always moves right.
> 3. **Turn the double minus into a plus.** $-(-2)$ becomes $+2$, so we now have $3 + 2$.
>    *Why:* removing a debt of 2 is the same as gaining 2.
> 4. **Add 2.** Move 2 steps right from 3: $3 + 2 = 5$.
>
> **Answer:** $-4 + 7 - (-2) = 5$.
>
> **Check:** typing `-4 + 7 - (-2)` into Python prints 5. ✓

> **Your turn:** Work out $-6 + 2 - (-5)$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Start at the first number.** −6.
> 2. **Add 2.** Move 2 steps right: −5, −4. You land on −4.
> 3. **Turn the double minus into a plus.** $-(-5)$ becomes $+5$, so we have $-4 + 5$.
> 4. **Add 5.** Move 5 steps right from −4: −3, −2, −1, 0, 1. You land on 1.
>
> **Answer:** $-6 + 2 - (-5) = 1$.
>
> </details>

### Multiplying and dividing: the sign rules

Work with the sizes as if there were no signs, then decide the sign separately:

| Signs | Result | Example |
|---|---|---|
| plus × plus | plus | $3 \times 4 = 12$ |
| plus × minus | minus | $3 \times (-4) = -12$ |
| minus × plus | minus | $(-3) \times 4 = -12$ |
| minus × minus | plus | $(-3) \times (-4) = 12$ |

Division follows exactly the same rules: $(-12) \div 3 = -4$ and $(-12) \div (-3) = 4$.
A quick way to remember it for a longer chain: **count the minus signs. An even number of
them gives a plus; an odd number gives a minus.**

**Why minus times minus is plus.** It is not an arbitrary rule; it is the only answer that
keeps a pattern going. Watch what happens as we multiply by −3 and the other number goes
down by 1 each time:

| Multiply | Result | Compared with the line above |
|---|---|---|
| $2 \times (-3)$ | $= -6$ | (start) |
| $1 \times (-3)$ | $= -3$ | up by 3 |
| $0 \times (-3)$ | $= 0$ | up by 3 |
| $(-1) \times (-3)$ | $= 3$ | up by 3 — the pattern must carry on |
| $(-2) \times (-3)$ | $= 6$ | up by 3 |

Each step down on the left adds 3 on the right. For the pattern not to break at zero,
$(-1) \times (-3)$ has to be $+3$.

> **Notebook example:** Work out $(-3) \times (-4) \div (-6)$.
>
> **What you need:** For × and ÷, ignore the signs and work with the sizes, then count the
> minus signs: an even count gives a positive answer, an odd count gives a negative one.
>
> **Plan:** do the sizes first, then decide the sign at the end.
>
> 1. **Count the minus signs.** There are three: in −3, in −4 and in −6.
> 2. **Decide the sign.** Three is odd, so the answer will be negative.
>    *Why:* each pair of minus signs cancels to a plus, and one minus is left over.
> 3. **Multiply the sizes.** $3 \times 4 = 12$.
> 4. **Divide the sizes.** $12 \div 6 = 2$.
> 5. **Attach the sign.** The size is 2 and the sign is negative, so the answer is −2.
>
> **Answer:** $(-3) \times (-4) \div (-6) = -2$.
>
> **Check:** step by step with signs: $(-3) \times (-4) = 12$, then $12 \div (-6) = -2$. ✓
> Python's `(-3) * (-4) / (-6)` prints `-2.0`.

> **Your turn:** Work out $(-2) \times 6 \div (-3)$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Count the minus signs.** Two: in −2 and in −3.
> 2. **Decide the sign.** Two is even, so the answer is positive.
> 3. **Multiply the sizes.** $2 \times 6 = 12$.
> 4. **Divide the sizes.** $12 \div 3 = 4$.
> 5. **Attach the sign.** Positive, so 4.
>
> **Answer:** $(-2) \times 6 \div (-3) = 4$.
>
> </details>

```python
print(-3 + 5)             # → 2
print(2 - 7)              # → -5
print(5 - (-2))           # → 7
print(-4 + 7 - (-2))      # → 5
print((-3) * 4)           # → -12
print((-3) * (-4))        # → 12
print((-12) / (-3))       # → 4.0
print(abs(-7))            # → 7
```

`abs()` gives the **size** of a number without its sign (its distance from zero), which
is exactly the "work with the sizes" step above.

> **Watch out:** $-3^2$ means $-(3^2) = -9$, because the power is done before the minus.
> If you mean "negative three, squared", write the brackets: $(-3)^2 = 9$. Python agrees:
> `-3**2` is `-9`.

## 2 · Fractions, Decimals and Percentages

**Skip this if you can already** work out $\frac{1}{4} + \frac{2}{3}$, $\frac{3}{4} \div \frac{1}{2}$
and "200 went up to 250: what is the percentage change?" (answers: $\frac{11}{12}$,
$\frac{3}{2}$ and 25%).

### What a fraction means

$\frac{3}{4}$ means "cut something into 4 equal pieces and take 3 of them". The bottom
number (the **denominator**) says how many equal pieces the whole is cut into; the top
number (the **numerator**) says how many pieces you have. A fraction is also just a
division: $\frac{3}{4} = 3 \div 4 = 0.75$.

**Simplifying.** Dividing the top and the bottom by the same number does not change the
amount, only the size of the pieces: $\frac{6}{8} = \frac{3}{4}$ (divide both by 2).
Four quarters of a pizza and eight eighths are the same pizza.

### The four operations

| Operation | Rule in words | Example |
|---|---|---|
| Add or subtract | Make the bottoms the same first, then add or subtract the tops | $\frac{1}{4} + \frac{2}{4} = \frac{3}{4}$ |
| Multiply | Top times top, bottom times bottom | $\frac{2}{3} \times \frac{3}{5} = \frac{6}{15} = \frac{2}{5}$ |
| Divide | Flip the second fraction, then multiply | $\frac{3}{4} \div \frac{1}{2} = \frac{3}{4} \times \frac{2}{1}$ |
| "Of" | "Of" means multiply | $\frac{1}{2}$ of 10 is $\frac{1}{2} \times 10 = 5$ |

Why do the bottoms have to match before adding? Because you can only add pieces of the
same size. One quarter plus two thirds is like adding 1 apple to 2 oranges: first turn
them both into the same kind of thing (twelfths, here).

> **Notebook example:** Work out $\frac{1}{4} + \frac{2}{3}$.
>
> **What you need:** You can only add fractions whose bottom numbers (denominators) match.
> To change a fraction's bottom, multiply its top **and** bottom by the same number; that
> keeps its value the same. Once the bottoms match, add the tops and keep the bottom.
>
> **Plan:** turn both fractions into twelfths, then add the tops.
>
> 1. **Pick a common bottom.** $4 \times 3 = 12$, and both 4 and 3 go into 12.
>    *Why:* multiplying the two bottoms always gives a number both of them divide into.
> 2. **Rewrite the first fraction.** To turn 4 into 12, multiply by 3. Do it to the top
>    too: $\frac{1 \times 3}{4 \times 3} = \frac{3}{12}$.
> 3. **Rewrite the second fraction.** To turn 3 into 12, multiply by 4. Do it to the top
>    too: $\frac{2 \times 4}{3 \times 4} = \frac{8}{12}$.
> 4. **Add the tops.** $3 + 8 = 11$, so the sum is $\frac{11}{12}$.
>    *Why:* 3 twelfths plus 8 twelfths is 11 twelfths, just as 3 apples plus 8 apples is 11 apples.
> 5. **Try to simplify.** No number bigger than 1 divides both 11 and 12, so it stays.
>
> **Answer:** $\frac{1}{4} + \frac{2}{3} = \frac{11}{12}$, a little less than one whole.
>
> **Check:** in decimals, $0.25 + 0.667 \approx 0.917$, and $11 \div 12 \approx 0.917$. ✓
> Python's `Fraction(1, 4) + Fraction(2, 3)` prints `11/12`.

> **Your turn:** Work out $\frac{1}{2} + \frac{1}{3}$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Pick a common bottom.** $2 \times 3 = 6$.
> 2. **Rewrite the first fraction.** $\frac{1 \times 3}{2 \times 3} = \frac{3}{6}$.
> 3. **Rewrite the second fraction.** $\frac{1 \times 2}{3 \times 2} = \frac{2}{6}$.
> 4. **Add the tops.** $3 + 2 = 5$, so $\frac{5}{6}$.
> 5. **Try to simplify.** Nothing divides both 5 and 6, so it stays.
>
> **Answer:** $\frac{1}{2} + \frac{1}{3} = \frac{5}{6}$.
>
> </details>

Dividing by a fraction asks "how many of these fit into that?" $\frac{3}{4} \div \frac{1}{2}$
asks "how many halves fit into three quarters?" Flipping and multiplying is the shortcut
that answers it.

> **Notebook example:** Work out $\frac{3}{4} \div \frac{1}{2}$.
>
> **What you need:** To divide by a fraction, flip the second fraction upside down (its
> top and bottom swap places) and multiply instead. To multiply fractions, multiply the
> tops together and the bottoms together.
>
> **Plan:** flip, multiply, then simplify.
>
> 1. **Flip the second fraction.** $\frac{1}{2}$ becomes $\frac{2}{1}$.
>    *Why:* dividing by a half is the same as doubling, and $\frac{2}{1}$ is 2.
> 2. **Change ÷ to ×.** The problem is now $\frac{3}{4} \times \frac{2}{1}$.
> 3. **Multiply the tops.** $3 \times 2 = 6$.
> 4. **Multiply the bottoms.** $4 \times 1 = 4$. So we have $\frac{6}{4}$.
> 5. **Simplify.** Divide top and bottom by 2: $\frac{6}{4} = \frac{3}{2}$.
> 6. **Turn it into a decimal.** $3 \div 2 = 1.5$.
>
> **Answer:** $\frac{3}{4} \div \frac{1}{2} = \frac{3}{2} = 1.5$: one and a half halves fit
> into three quarters.
>
> **Check:** multiply back: $1.5 \times \frac{1}{2} = 0.75 = \frac{3}{4}$. ✓

> **Your turn:** Work out $\frac{2}{3} \div \frac{1}{6}$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Flip the second fraction.** $\frac{1}{6}$ becomes $\frac{6}{1}$.
> 2. **Change ÷ to ×.** $\frac{2}{3} \times \frac{6}{1}$.
> 3. **Multiply the tops.** $2 \times 6 = 12$.
> 4. **Multiply the bottoms.** $3 \times 1 = 3$, giving $\frac{12}{3}$.
> 5. **Simplify.** $12 \div 3 = 4$.
>
> **Answer:** $\frac{2}{3} \div \frac{1}{6} = 4$: four sixths fit into two thirds.
>
> </details>

### Fractions, decimals and percentages are the same number

**Percent** means "out of 100". So 75% is $\frac{75}{100}$, which is 0.75, which is
$\frac{3}{4}$. They are three spellings of one amount.

| Fraction | Decimal | Percentage | How to convert |
|---|---|---|---|
| $\frac{1}{2}$ | 0.5 | 50% | fraction → decimal: divide top by bottom |
| $\frac{3}{4}$ | 0.75 | 75% | decimal → percentage: multiply by 100 |
| $\frac{1}{5}$ | 0.2 | 20% | percentage → decimal: divide by 100 |
| $\frac{1}{3}$ | 0.333… | about 33.3% | some fractions never stop as decimals |
| $\frac{1}{1000}$ | 0.001 | 0.1% | the downtime allowed by "99.9% uptime" |

**"Percent of"** means multiply: 15% of 40 is $0.15 \times 40 = 6$. And 0.1% of a 30-day
month (43,200 minutes) is $43{,}200 \div 1000 = 43.2$ minutes, which is why "three nines"
of uptime means about 43 minutes of downtime a month.

**Percentage change** compares the change with where you **started**:

$$
\text{percentage change} = \frac{\text{new} - \text{old}}{\text{old}} \times 100
$$

> **Notebook example:** A service handled 200 requests per second last month and handles
> 250 now. What is the percentage change?
>
> **What you need:** Percentage change is the change divided by the **old** (starting)
> value, then multiplied by 100: $\frac{\text{new} - \text{old}}{\text{old}} \times 100$.
> A positive answer is an increase; a negative answer is a decrease.
>
> **Plan:** find the change, divide by the old value, turn it into a percentage.
>
> 1. **Find the change.** $250 - 200 = 50$ requests per second.
> 2. **Divide by the old value.** $50 \div 200 = 0.25$.
>    *Why:* we want the change as a share of where we started, not of where we ended.
> 3. **Turn it into a percentage.** $0.25 \times 100 = 25$.
>
> **Answer:** a 25% increase in traffic.
>
> **Check:** 25% of 200 is $0.25 \times 200 = 50$, and $200 + 50 = 250$. ✓

> **Your turn:** A page's response time drops from 80 ms to 60 ms. What is the percentage change?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the change.** $60 - 80 = -20$ ms (negative, so it went down).
> 2. **Divide by the old value.** $-20 \div 80 = -0.25$.
> 3. **Turn it into a percentage.** $-0.25 \times 100 = -25$.
>
> **Answer:** −25%, that is, a 25% decrease.
>
> </details>

```python
from fractions import Fraction

print(Fraction(6, 8))                       # → 3/4
print(Fraction(1, 4) + Fraction(2, 3))      # → 11/12
print(Fraction(2, 3) * Fraction(3, 5))      # → 2/5
print(Fraction(3, 4) / Fraction(1, 2))      # → 3/2
print(3 / 4)                                # → 0.75
print(0.75 * 100)                           # → 75.0
print(15 / 100 * 40)                        # → 6.0
print((250 - 200) / 200 * 100)              # → 25.0
print(0.1 + 0.2)                            # → 0.30000000000000004
print(Fraction(1, 10) + Fraction(2, 10))    # → 3/10
```

`Fraction` keeps exact tops and bottoms, so it never rounds. Ordinary decimals (floats)
are stored in binary and can be off by a hair, as `0.1 + 0.2` shows; chapter 02 explains why.

> **Watch out:** You cannot add fractions by adding tops and bottoms:
> $\frac{1}{2} + \frac{1}{2}$ is 1, not $\frac{2}{4}$. And a percentage change always
> divides by the **old** value: going from 80 to 60 is a 25% drop, but going back from 60
> to 80 is a 33% rise.

## 3 · Powers and Roots

**Skip this if you can already** say what $2^{10}$, $5^0$ and $2^{-3}$ are, and write
4,500,000 in scientific notation (answers: 1024, 1, $\frac{1}{8}$ and $4.5 \times 10^6$).

### Powers are repeated multiplication

$2^5$ means "multiply 2 by itself, 5 times": $2 \times 2 \times 2 \times 2 \times 2 = 32$.
The big number at the bottom is the **base**; the small raised number is the
**exponent** (or **power**). $x^2$ is read "x squared" and $x^3$ "x cubed".

Powers of 2 are the most important numbers in computing, because every extra bit doubles
the number of values you can store:

| $n$ | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 |
|---|---|---|---|---|---|---|---|---|---|---|---|
| $2^n$ | 1 | 2 | 4 | 8 | 16 | 32 | 64 | 128 | 256 | 512 | 1024 |

- 8 bits make a byte, and a byte has $2^8 = 256$ possible values (0 to 255).
- $2^{10} = 1024$ is close to 1000, which is why 1024 bytes are called a kilobyte (KB,
  strictly a KiB).
- $2^{20} = 1024 \times 1024 = 1{,}048{,}576$, about a million: a megabyte (MB).
- An algorithm that tries every subset of $n$ items does $2^n$ things: 30 items is
  already about a billion.

Two rules save a lot of work: **multiplying powers of the same base adds the exponents**
($2^3 \times 2^4 = 2^7$, since that is 3 twos then 4 more twos), and **a power of a power
multiplies them** ($(2^{10})^2 = 2^{20}$).

### Power zero and negative powers

Walk **down** the table: each step down in the exponent **divides by the base**. Keep
walking past 1 and the pattern tells you what the strange cases must be.

| $2^3$ | $2^2$ | $2^1$ | $2^0$ | $2^{-1}$ | $2^{-2}$ | $2^{-3}$ |
|---|---|---|---|---|---|---|
| 8 | 4 | 2 | 1 | $\frac{1}{2}$ | $\frac{1}{4}$ | $\frac{1}{8}$ |

So **anything to the power 0 is 1** (it is what you get just before the fractions
start), and a **negative power means "one over"**: $2^{-3} = \frac{1}{2^3} = \frac{1}{8}$.
A negative exponent never makes the answer negative; it makes it small.

> **Notebook example:** Work out $2^{-3}$, as a fraction and as a decimal.
>
> **What you need:** Each time the exponent goes down by 1, you divide by the base (here
> 2). Following that pattern below 0 gives the rule $2^{-n} = \frac{1}{2^n}$: a negative
> exponent means "one over the positive power".
>
> **Plan:** start from a power you know and walk down one step at a time.
>
> 1. **Start from a power you know.** $2^0 = 1$.
> 2. **Step down to −1.** Divide by 2: $1 \div 2 = \frac{1}{2}$. So $2^{-1} = \frac{1}{2}$.
>    *Why:* every step down the table divides by the base.
> 3. **Step down to −2.** Divide by 2 again: $\frac{1}{2} \div 2 = \frac{1}{4}$.
> 4. **Step down to −3.** Divide by 2 again: $\frac{1}{4} \div 2 = \frac{1}{8}$.
> 5. **Turn it into a decimal.** $1 \div 8 = 0.125$.
>
> **Answer:** $2^{-3} = \frac{1}{8} = 0.125$: one eighth.
>
> **Check:** with the rule directly, $2^3 = 8$, so $2^{-3} = \frac{1}{8}$. ✓ Also
> $8 \times 0.125 = 1$, and Python's `2 ** -3` prints `0.125`.

> **Your turn:** Work out $10^{-2}$, as a fraction and as a decimal.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Start from a power you know.** $10^0 = 1$.
> 2. **Step down to −1.** $1 \div 10 = \frac{1}{10}$.
> 3. **Step down to −2.** $\frac{1}{10} \div 10 = \frac{1}{100}$.
> 4. **Turn it into a decimal.** $1 \div 100 = 0.01$.
>
> **Answer:** $10^{-2} = \frac{1}{100} = 0.01$.
>
> </details>

### Square roots undo squaring

$\sqrt{49}$ asks "which number, multiplied by itself, gives 49?" The answer is 7, because
$7 \times 7 = 49$. Roots are to powers what subtraction is to addition: the undo button.
Most roots are not whole numbers: $\sqrt{50} \approx 7.07$, a little more than 7 because 50
is a little more than 49. In this module, $\sqrt{x}$ always means the positive root, and
there is no ordinary (real) square root of a negative number.

### Powers of 10 and scientific notation

$10^3 = 1000$ (a 1 followed by 3 zeros) and $10^6 = 1{,}000{,}000$. **Scientific
notation** writes a big or small number as "a number between 1 and 10, times a power of
10". The power counts how many places the decimal point moved.

| Ordinary | Scientific | Spoken |
|---|---|---|
| 1,000 | $1 \times 10^3$ | a thousand |
| 4,500,000 | $4.5 \times 10^6$ | four and a half million |
| 0.003 | $3 \times 10^{-3}$ | three thousandths (3 ms is $3 \times 10^{-3}$ s) |

> **Notebook example:** Write 4,500,000 in scientific notation.
>
> **What you need:** Scientific notation is (a number from 1 up to, but not including,
> 10) × (a power of 10). The power of 10 is how many places you move the decimal point.
> Moving it left for a big number gives a positive power.
>
> **Plan:** move the decimal point until one digit is in front of it, and count the moves.
>
> 1. **Find the decimal point.** 4,500,000 is 4500000.0; the point is at the very end.
> 2. **Move it to just after the first digit.** That gives 4.500000, which is 4.5.
>    *Why:* scientific notation wants exactly one non-zero digit before the point.
> 3. **Count the moves.** Past 0, 0, 0, 0, 0 and 5: that is 6 places to the left.
> 4. **Write the power.** 6 moves gives $10^6$, so the number is $4.5 \times 10^6$.
>
> **Answer:** $4{,}500{,}000 = 4.5 \times 10^6$, four and a half million.
>
> **Check:** $10^6 = 1{,}000{,}000$, and $4.5 \times 1{,}000{,}000 = 4{,}500{,}000$. ✓
> Python writes the same number as `4.5e6`.

> **Your turn:** Write 72,000 in scientific notation.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the decimal point.** 72000.0; the point is at the end.
> 2. **Move it to just after the first digit.** 7.2000, which is 7.2.
> 3. **Count the moves.** Past 0, 0, 0 and 2: 4 places.
> 4. **Write the power.** $7.2 \times 10^4$.
>
> **Answer:** $72{,}000 = 7.2 \times 10^4$.
>
> </details>

```python
import math

print(2 ** 10)                  # → 1024
print(2 ** 3 * 2 ** 4 == 2 ** 7)  # → True
print(1024 * 1024)              # → 1048576
print(5 ** 0)                   # → 1
print(2 ** -3)                  # → 0.125
print(math.sqrt(49))            # → 7.0
print(math.isqrt(50))           # → 7
print(4.5e6 == 4_500_000)       # → True
print(f"{72000:.1e}")           # → 7.2e+04
```

The `e` in `4.5e6` is Python's way of typing "× 10 to the power", and `math.isqrt` gives
the whole-number part of a square root.

> **Watch out:** $2^3$ is $2 \times 2 \times 2 = 8$, not $2 \times 3 = 6$. And in many
> languages `^` is **not** a power: in Python, C and Java `2 ^ 3` is a bitwise XOR and
> gives 1. Use `**` in Python (or `pow`).

## 4 · Letters Stand for Numbers

**Skip this if you can already** work out $2a^2 - 3b$ when $a = 3$ and $b = -2$, and
expand $(x + 3)(x + 2)$ (answers: 24 and $x^2 + 5x + 6$).

### A letter is a variable

A letter in maths is a variable, just as in code: a name for a number. $3x + 1$ is a
recipe, "take x, multiply by 3, add 1", exactly like `3 * x + 1`. **Substitution** means
replacing the letter with a number and doing the arithmetic. Put brackets round a
negative number when you substitute it, so you do not lose its sign.

> **Notebook example:** If $a = 3$ and $b = -2$, work out $2a^2 - 3b$.
>
> **What you need:** Substitution: replace every letter with its number, in brackets.
> $2a^2$ means $2 \times a^2$ (square first, then double), and $3b$ means $3 \times b$.
> Minus times minus is plus.
>
> **Plan:** work out each part separately, then combine them.
>
> 1. **Square a.** $a^2 = 3^2 = 3 \times 3 = 9$.
>    *Why:* powers come before multiplication, so square before you double.
> 2. **Double it.** $2a^2 = 2 \times 9 = 18$.
> 3. **Work out 3b.** $3b = 3 \times (-2) = -6$.
> 4. **Put the parts back together.** $2a^2 - 3b = 18 - (-6)$.
> 5. **Turn the double minus into a plus.** $18 - (-6) = 18 + 6 = 24$.
>
> **Answer:** $2a^2 - 3b = 24$ when $a = 3$ and $b = -2$.
>
> **Check:** in Python, `a, b = 3, -2` then `2 * a**2 - 3 * b` prints 24. ✓

> **Your turn:** If $a = 2$ and $b = -1$, work out $3a^2 - 2b$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Square a.** $a^2 = 2 \times 2 = 4$.
> 2. **Triple it.** $3a^2 = 3 \times 4 = 12$.
> 3. **Work out 2b.** $2b = 2 \times (-1) = -2$.
> 4. **Put the parts back together.** $12 - (-2)$.
> 5. **Turn the double minus into a plus.** $12 + 2 = 14$.
>
> **Answer:** $3a^2 - 2b = 14$.
>
> </details>

### Tidying up: like terms, brackets and factoring

| Move | What it means | Example |
|---|---|---|
| Collect like terms | Add things of the same kind, like counting apples with apples | $3x + 2x = 5x$, but $3x + 2y$ stays as it is |
| Expand a bracket | Multiply the outside by **everything** inside | $3(x + 4) = 3x + 12$ |
| Factor out | The reverse: pull out something every term shares | $6x + 9 = 3(2x + 3)$ |

Factoring is the same idea as pulling a repeated line out of both branches of an `if`.
Expanding is the same as inlining it back.

### The box picture for two brackets

To multiply $(a + b)(c + d)$, draw a rectangle whose sides are split into $a + b$ and
$c + d$. Its area is the product, and it is made of four small boxes:

```
            c        d
        +--------+--------+
    a   |   ac   |   ad   |
        +--------+--------+
    b   |   bc   |   bd   |
        +--------+--------+
```

So $(a + b)(c + d) = ac + ad + bc + bd$: **every part of the first bracket multiplies
every part of the second.** Four boxes, four terms.

> **Notebook example:** Expand $(x + 3)(x + 2)$.
>
> **What you need:** To multiply two brackets, every part of the first multiplies every
> part of the second. Picture a rectangle with sides $x + 3$ and $x + 2$ split into four
> boxes; the answer is the sum of the four box areas. **Like terms** (terms with the same
> letter part, such as $2x$ and $3x$) can then be added.
>
> **Plan:** fill in the four boxes, add them up, then collect like terms.
>
> 1. **Top-left box.** $x \times x = x^2$.
> 2. **Top-right box.** $x \times 2 = 2x$.
> 3. **Bottom-left box.** $3 \times x = 3x$.
> 4. **Bottom-right box.** $3 \times 2 = 6$.
> 5. **Add the four boxes.** $x^2 + 2x + 3x + 6$.
> 6. **Collect like terms.** $2x + 3x = 5x$, so we get $x^2 + 5x + 6$.
>    *Why:* 2 lots of x plus 3 lots of x is 5 lots of x.
>
> **Answer:** $(x + 3)(x + 2) = x^2 + 5x + 6$.
>
> **Check:** try $x = 1$. Left side: $(1 + 3)(1 + 2) = 4 \times 3 = 12$. Right side:
> $1 + 5 + 6 = 12$. ✓ Try $x = 10$: $13 \times 12 = 156$ and $100 + 50 + 6 = 156$. ✓

> **Your turn:** Expand $(x + 1)(x + 4)$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Top-left box.** $x \times x = x^2$.
> 2. **Top-right box.** $x \times 4 = 4x$.
> 3. **Bottom-left box.** $1 \times x = x$.
> 4. **Bottom-right box.** $1 \times 4 = 4$.
> 5. **Collect like terms.** $4x + x = 5x$, giving $x^2 + 5x + 4$.
>
> **Answer:** $(x + 1)(x + 4) = x^2 + 5x + 4$. Check with $x = 1$: $2 \times 5 = 10$ and
> $1 + 5 + 4 = 10$.
>
> </details>

```python
a, b = 3, -2
print(2 * a**2 - 3 * b)     # → 24

x = 7
print(3 * (x + 4) == 3 * x + 12)   # → True
print(6 * x + 9 == 3 * (2 * x + 3))   # → True
print(all((x + 3) * (x + 2) == x**2 + 5 * x + 6 for x in range(-10, 11)))   # → True
```

Testing an identity on many values is not a proof, but it is an excellent way to catch a
slip in your algebra.

> **Watch out:** A bracket multiplies **everything** inside: $3(x + 4)$ is $3x + 12$, not
> $3x + 4$. And $(x + 3)^2$ is **not** $x^2 + 9$; draw the boxes and you get
> $x^2 + 6x + 9$.

## 5 · Solving and Rearranging Equations

**Skip this if you can already** solve $3x + 5 = 20$ and turn $t = \frac{w}{r}$ into a
formula for $r$ (answers: $x = 5$ and $r = \frac{w}{t}$).

### Keep the scales balanced

> **Analogy:** An equation is a balance scale with equal weights on both pans. You may do
> anything you like to it, **as long as you do the same thing to both sides**: take 5 off
> both pans, or halve both pans, and it still balances.

**Solving** means getting the letter alone on one side. Undo what was done to it, in
reverse order, using the opposite operation each time:

| To undo… | Do this to both sides |
|---|---|
| $+ 5$ | $- 5$ |
| $- 7$ | $+ 7$ |
| $\times 3$ | $\div 3$ |
| $\div 4$ | $\times 4$ |

A one-step equation needs one undo: $x + 5 = 12$ gives $x = 12 - 5 = 7$. A two-step
equation needs two, and you undo the + or − **before** the × or ÷, like taking off your
shoes before your socks.

> **Notebook example:** Solve $3x + 5 = 20$.
>
> **What you need:** You may do anything to an equation as long as you do the same to both
> sides. Undo each operation on x with its opposite (+ is undone by −, × by ÷), starting
> with the one done **last**.
>
> **Plan:** first remove the + 5, then remove the × 3.
>
> 1. **Subtract 5 from both sides.** Left: $3x + 5 - 5 = 3x$. Right: $20 - 5 = 15$.
>    Now $3x = 15$.
>    *Why:* the + 5 was the last thing done to x, so it is the first thing to undo.
> 2. **Divide both sides by 3.** Left: $3x \div 3 = x$. Right: $15 \div 3 = 5$.
> 3. **Write the result.** $x = 5$.
>
> **Answer:** $x = 5$.
>
> **Check:** substitute back: $3 \times 5 = 15$, and $15 + 5 = 20$, which matches the
> right side. ✓

> **Your turn:** Solve $2x - 7 = 9$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Add 7 to both sides.** $2x = 9 + 7 = 16$.
> 2. **Divide both sides by 2.** $x = 16 \div 2 = 8$.
> 3. **Check by substituting.** $2 \times 8 = 16$, and $16 - 7 = 9$. ✓
>
> **Answer:** $x = 8$.
>
> </details>

**x on both sides.** First gather the x terms on one side by subtracting the smaller one
from both sides, then carry on as before. For $5x - 4 = 2x + 8$:

| Move | Equation |
|---|---|
| Start | $5x - 4 = 2x + 8$ |
| Subtract $2x$ from both sides | $3x - 4 = 8$ |
| Add 4 to both sides | $3x = 12$ |
| Divide both sides by 3 | $x = 4$ |
| Check: substitute $x = 4$ | $5 \times 4 - 4 = 16$ and $2 \times 4 + 8 = 16$ ✓ |

### Rearranging a formula

Engineering formulas often come the "wrong way round" for the question you have. The
balance-scale moves work just as well with letters as with numbers. That is how you
"solve for n" in a capacity estimate.

> **Notebook example:** A batch job processes $w$ records at a rate of $r$ records per
> second, so it takes $t = \frac{w}{r}$ seconds. Rearrange the formula to give $r$, then
> find the rate needed to process 600 records in 12 seconds.
>
> **What you need:** Rearranging is solving with letters: do the same thing to both sides
> until the letter you want is alone. $\frac{w}{r}$ means $w \div r$, and the opposite of
> dividing by $r$ is multiplying by $r$. Here $t$ is time, $w$ is work (records) and $r$
> is rate (records per second).
>
> **Plan:** get $r$ out of the bottom of the fraction, then get it alone.
>
> 1. **Multiply both sides by r.** Left: $t \times r$. Right: $\frac{w}{r} \times r = w$.
>    Now $t r = w$.
>    *Why:* r was dividing, so multiplying by r undoes it and lifts it out of the bottom.
> 2. **Divide both sides by t.** Left: $\frac{t r}{t} = r$. Right: $\frac{w}{t}$.
> 3. **Write the new formula.** $r = \frac{w}{t}$: rate is work divided by time.
> 4. **Substitute the numbers.** $r = \frac{600}{12}$.
> 5. **Do the division.** $600 \div 12 = 50$.
>
> **Answer:** $r = \frac{w}{t}$, so the job needs a rate of 50 records per second.
>
> **Check:** put it back into the original formula: $t = \frac{600}{50} = 12$ seconds,
> exactly the time we wanted. ✓

> **Your turn:** The total capacity of a cluster is $T = s \times p$, where $s$ is the
> number of servers and $p$ is the requests per second one server handles. Rearrange for
> $s$, then find how many servers give 1,200 requests per second if each handles 300.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Divide both sides by p.** Left: $\frac{T}{p}$. Right: $\frac{s \times p}{p} = s$.
> 2. **Write the new formula.** $s = \frac{T}{p}$.
> 3. **Substitute the numbers.** $s = \frac{1200}{300}$.
> 4. **Do the division.** $1200 \div 300 = 4$.
> 5. **Check by substituting.** $4 \times 300 = 1200$. ✓
>
> **Answer:** $s = \frac{T}{p}$, so 4 servers.
>
> </details>

```python
x = (20 - 5) / 3
print(x)                    # → 5.0
print(3 * x + 5 == 20)      # → True

def rate_needed(work, time):
    return work / time      # r = w / t, the rearranged formula

r = rate_needed(600, 12)
print(r)                    # → 50.0
print(600 / r)              # → 12.0
```

> **Watch out:** Doing something to only **one** side breaks the balance. And do it to the
> **whole** side: dividing both sides of $3x + 6 = 12$ by 3 gives $x + 2 = 4$, not
> $x + 6 = 4$. Always finish by substituting your answer back in; it takes ten seconds and
> catches almost every slip.

## 6 · Graphs, Slope and Straight Lines

**Skip this if you can already** find the slope of the line through $(2, 7)$ and
$(5, 13)$, and say what the 10 means in $y = 2x + 10$ (answers: 2, and the value of y when
x is 0).

### Coordinates and plotting

A point is written $(x, y)$: go $x$ steps across (right), then $y$ steps up. It is a pair
of numbers, like a `(column, row)` tuple. To draw a graph of a rule such as $y = 2x + 1$,
make a table, work out each y, and plot the pairs:

| x | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| $y = 2x + 1$ | 1 | 3 | 5 | 7 |

```
  y
  7 |                 •
  5 |           •
  3 |     •
  1 •
    +-----+-----+-----+--- x
    0     1     2     3
```

The points sit on a straight line, and every step of 1 to the right goes up by exactly 2.

### Slope: how much y changes when x goes up by 1

The **slope** (or **gradient**) of a line says how steep it is: **how much y changes when
x goes up by 1.** From any two points:

$$
\text{slope} = \frac{\text{rise}}{\text{run}} = \frac{\text{change in } y}{\text{change in } x} = \frac{y_2 - y_1}{x_2 - x_1}
$$

The small numbers in $y_1$ and $x_1$ are labels ("first point"), not powers. A positive
slope goes up to the right, a negative one goes down, and zero is flat.

> **Notebook example:** A test suite with 2 tests takes 7 seconds; with 5 tests it takes 13
> seconds. Treat these as the points $(2, 7)$ and $(5, 13)$ and find the slope.
>
> **What you need:** Slope = rise ÷ run, where the **rise** is how much y changes between
> the two points and the **run** is how much x changes. It tells you how much y goes up
> for each 1 that x goes up. Here x is the number of tests and y is seconds.
>
> **Plan:** find the rise, find the run, divide.
>
> 1. **Find the rise.** $13 - 7 = 6$ seconds.
> 2. **Find the run.** $5 - 2 = 3$ tests.
>    *Why:* subtract in the same order as the rise (second point minus first point).
> 3. **Divide rise by run.** $6 \div 3 = 2$.
>
> **Answer:** the slope is 2: each extra test adds 2 seconds.
>
> **Check:** walk it: 2 tests take 7 s, 3 take 9 s, 4 take 11 s, 5 take 13 s. ✓ Walking
> back to 0 tests gives $7 - 2 - 2 = 3$ seconds of start-up time.

> **Your turn:** Find the slope of the line through $(1, 3)$ and $(3, 4)$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the rise.** $4 - 3 = 1$.
> 2. **Find the run.** $3 - 1 = 2$.
> 3. **Divide rise by run.** $1 \div 2 = \frac{1}{2} = 0.5$.
>
> **Answer:** the slope is $\frac{1}{2}$: y goes up half a step for every step in x.
>
> </details>

### The equation of a straight line: $y = mx + b$

Every straight line can be written $y = mx + b$:

- $m$ is the **slope**: how much y goes up each time x goes up by 1.
- $b$ is the **intercept**: the value of y when x is 0, where the line crosses the
  y axis. In engineering it is usually the fixed cost, the start-up time or the base
  latency.

For the test suite above, $y = 2x + 3$: 3 seconds to start, plus 2 seconds per test.

> **Notebook example:** A service's latency is 10 ms with no users and grows by 2 ms for
> every 100 users. Write the line $y = mx + b$, then predict the latency at 500 users.
>
> **What you need:** In $y = mx + b$, $m$ is the slope (change in y for each 1 that x goes
> up) and $b$ is the intercept (y when x is 0). Here x is users and y is latency in ms.
>
> **Plan:** turn the words into m and b, write the line, then substitute x = 500.
>
> 1. **Read off the intercept.** With no users (x = 0) latency is 10 ms, so $b = 10$.
> 2. **Find the slope per single user.** 2 ms per 100 users is $2 \div 100 = 0.02$ ms per user, so $m = 0.02$.
>    *Why:* slope is always "per 1", so divide the change by the 100 users it was spread over.
> 3. **Write the line.** $y = 0.02x + 10$.
> 4. **Substitute x = 500.** $y = 0.02 \times 500 + 10$.
> 5. **Multiply.** $0.02 \times 500 = 10$.
> 6. **Add.** $10 + 10 = 20$.
>
> **Answer:** $y = 0.02x + 10$, and at 500 users the latency is about 20 ms.
>
> **Check:** count up in hundreds: 0 users 10 ms, 100 users 12, 200 users 14, 300 users
> 16, 400 users 18, 500 users 20. ✓

> **Your turn:** A monthly cloud bill is 20 dollars fixed plus 3 dollars per million
> requests. Write it as $y = mx + b$ (x in millions of requests) and find the bill for 4
> million requests.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Read off the intercept.** The fixed part is 20, so $b = 20$.
> 2. **Read off the slope.** 3 dollars per million, so $m = 3$.
> 3. **Write the line.** $y = 3x + 20$.
> 4. **Multiply.** $3 \times 4 = 12$.
> 5. **Add.** $12 + 20 = 32$.
>
> **Answer:** $y = 3x + 20$, so 32 dollars for 4 million requests.
>
> </details>

```python
def slope(p, q):
    (x1, y1), (x2, y2) = p, q
    return (y2 - y1) / (x2 - x1)

print(slope((2, 7), (5, 13)))     # → 2.0
print(slope((1, 3), (3, 4)))      # → 0.5

def latency_ms(users):
    return 0.02 * users + 10      # y = mx + b

print(latency_ms(0))              # → 10.0
print(latency_ms(500))            # → 20.0
print([2 * x + 1 for x in range(4)])   # → [1, 3, 5, 7]
```

> **Watch out:** Subtract in the **same order** on top and bottom. $\frac{13 - 7}{2 - 5}$
> mixes the orders and gives −2, the wrong sign. And real systems are only roughly
> straight lines: latency often bends sharply upwards near full capacity (chapter 11
> looks at why), so a straight-line prediction is a first guess, not a promise.

## 7 · Rounding, Estimating and Sanity Checks

**Skip this if you can already** round 3.14159 to two decimal places, and estimate
1,900 × 86,400 in your head to the nearest power of 10 (answers: 3.14 and about
$2 \times 10^8$).

### Rounding

To round, look at the **first digit you are dropping**: 5 or more rounds up, 4 or less
rounds down.

| Number | Round to | Look at | Result |
|---|---|---|---|
| 3.14159 | 2 decimal places | the 1 after 3.14 | 3.14 |
| 2.678 | 1 decimal place | the 7 after 2.6 | 2.7 |
| 2,749 | the nearest hundred | the 4 after 27 | 2,700 |
| 86,400 | 1 significant figure | the 6 after 8 | 90,000 |
| 0.004567 | 2 significant figures | the 6 after 45 | 0.0046 |

**Significant figures** count digits from the first non-zero one, so leading zeros do not
count. "Two significant figures" means "keep the two digits that matter most", which is
usually all an estimate needs.

### Estimating with round numbers

To estimate, round every number to one or two significant figures, then calculate. For
multiplying powers of 10, **multiply the front digits and add up the zeros**:
$2{,}000 \times 100{,}000$ is $2 \times 1$ with $3 + 5 = 8$ zeros, which is $200{,}000{,}000$.

The **order of magnitude** of a number is its nearest power of 10: roughly how many digits
it has. Estimates only need to get the order of magnitude right: 160 million and 200
million are "the same answer" for deciding whether one machine is enough; 2 million or 2
billion would not be.

> **Notebook example:** A service receives about 1,900 requests per second, all day. Roughly
> how many requests is that per day?
>
> **What you need:** To estimate, round each number to one significant figure (keep only
> its first digit and fill the rest with zeros), then multiply. To multiply round numbers,
> multiply the front digits and add up the zeros.
>
> **Plan:** count the seconds in a day, round both numbers, multiply the round numbers.
>
> 1. **Seconds in an hour.** $60 \times 60 = 3{,}600$.
> 2. **Seconds in a day.** $3{,}600 \times 24 = 86{,}400$.
> 3. **Round the request rate.** 1,900 is about 2,000.
> 4. **Round the seconds.** 86,400 is about 100,000.
>    *Why:* rounding to a 1 followed by zeros makes the multiplication trivial.
> 5. **Multiply the front digits.** $2 \times 1 = 2$.
> 6. **Add up the zeros.** 2,000 has 3 zeros and 100,000 has 5, so $3 + 5 = 8$ zeros.
> 7. **Write the estimate.** 2 followed by 8 zeros: $200{,}000{,}000 = 2 \times 10^8$.
>
> **Answer:** about 200 million requests per day (a few hundred million).
>
> **Check:** the exact value is $1{,}900 \times 86{,}400 = 164{,}160{,}000$, about
> $1.6 \times 10^8$. Same order of magnitude, and we rounded both numbers up, so the
> estimate should be a bit high. ✓

> **Your turn:** 3,100 users each store 48 MB of photos. Roughly how much storage is that in
> total, in MB and in GB (use 1 GB ≈ 1,000 MB)?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Round the users.** 3,100 is about 3,000.
> 2. **Round the size.** 48 MB is about 50 MB.
> 3. **Multiply the front digits.** $3 \times 5 = 15$.
> 4. **Add up the zeros.** 3,000 has 3 zeros and 50 has 1, so 4 zeros: 150,000 MB.
> 5. **Convert to GB.** $150{,}000 \div 1{,}000 = 150$ GB.
>
> **Answer:** about 150 GB. (Exactly, $3{,}100 \times 48 = 148{,}800$ MB.)
>
> </details>

### Does the answer make sense?

Before you trust any answer, run through this checklist. It takes seconds and catches most
mistakes, on paper and in production dashboards alike.

1. **Sign.** Should it be positive or negative? A negative number of servers is a bug.
2. **Size.** Is the order of magnitude plausible? A web page that loads in 4,000 seconds,
   or a probability of 1.3, means a slip somewhere.
3. **Units.** ms or s? MB or GB? Per second or per day? Many "wrong" answers are right
   numbers in the wrong unit.
4. **A tiny case.** Plug in 0, 1 or 2 and check by hand.
5. **Substitute back.** If you solved an equation, put the answer back in.
6. **Estimate first.** A quick round-number guess tells you roughly what the exact answer
   should be.

```python
print(round(3.14159, 2))          # → 3.14
print(round(2.678, 1))            # → 2.7
print(round(2749, -2))            # → 2700
print(round(2.5), round(3.5))     # → 2 4
print(60 * 60 * 24)               # → 86400
print(1900 * 86400)               # → 164160000
print(f"{1900 * 86400:.1e}")      # → 1.6e+08
print(len(str(1900 * 86400)))     # → 9
```

The last line counts digits: a 9-digit number is in the hundreds of millions, $10^8$.

> **Watch out:** Python's `round` breaks ties towards the **even** neighbour ("banker's
> rounding"), so `round(2.5)` is 2, not the school answer 3. That avoids a slight upward
> bias when you round lots of numbers. If you need school rounding, say so explicitly
> (for example with the `decimal` module).

## Common Mistakes

1. **Losing a minus sign when substituting.** Put negative numbers in brackets:
   $3 \times (-2)$, not $3 \times -2$ written loosely and then forgotten.
2. **Reading $-3^2$ as 9.** The power comes first, so it is −9. Write $(-3)^2$ if you mean 9.
3. **Adding fractions top-and-bottom.** $\frac{1}{2} + \frac{1}{3}$ is $\frac{5}{6}$, not
   $\frac{2}{5}$. Match the bottoms first.
4. **Dividing a percentage change by the new value.** Always divide by where you started.
5. **Thinking a negative exponent makes a negative number.** $2^{-3} = \frac{1}{8}$, a
   small positive number.
6. **Using `^` for powers in code.** In Python, C and Java it is XOR. Use `**` or `pow`.
7. **Expanding only part of a bracket.** $3(x + 4) = 3x + 12$; $(x + 3)^2$ has four boxes.
8. **Doing something to only one side of an equation**, or to only part of a side.
9. **Mixing the order of subtraction in a slope.** Second minus first, top and bottom.
10. **Not checking.** Substitute back, try a tiny case, estimate first.

## Check Yourself

**1.** Work out $7 - (-3) \times 2$.

<details>
<summary>Open the answer</summary>

Multiplication comes before subtraction, so do $(-3) \times 2 = -6$ first. Then
$7 - (-6) = 7 + 6 = 13$. (Doing it left to right, $(7 + 3) \times 2 = 20$, is the classic
slip.)

</details>

**2.** An error rate goes from 2 errors in 1,000 requests to 3 errors in 1,000 requests.
What are the two error rates as percentages, and what is the percentage change?

<details>
<summary>Open the answer</summary>

$\frac{2}{1000} = 0.002 = 0.2\%$ and $\frac{3}{1000} = 0.003 = 0.3\%$. The change is
$0.3 - 0.2 = 0.1$ percentage points, and as a percentage change it is
$\frac{0.1}{0.2} \times 100 = 50\%$: the error rate rose by half. Saying "it went up 0.1%"
and "it went up 50%" describe the same event, which is why dashboards should say which
they mean.

</details>

**3.** A disk holds $2^{30}$ bytes. How many 1 KB ($2^{10}$-byte) blocks is that?

<details>
<summary>Open the answer</summary>

Dividing powers of the same base subtracts the exponents: $2^{30} \div 2^{10} = 2^{20}$,
which is $1{,}048{,}576$, about a million blocks. (Check: $2^{10} \times 2^{20} = 2^{30}$,
because multiplying adds the exponents.)

</details>

**4.** Solve $4x + 1 = x + 10$, then check your answer.

<details>
<summary>Open the answer</summary>

Subtract $x$ from both sides: $3x + 1 = 10$. Subtract 1: $3x = 9$. Divide by 3: $x = 3$.
Check: left $4 \times 3 + 1 = 13$, right $3 + 10 = 13$. ✓

</details>

**5.** Each server handles 250 requests per second and you expect 2,000 requests per second
at peak. Write a formula for the number of servers $n$, and find it.

<details>
<summary>Open the answer</summary>

Total capacity is $n \times 250$, and it must equal 2,000: $250n = 2000$. Divide both
sides by 250: $n = \frac{2000}{250} = 8$ servers. In practice you would add headroom
(for example 10 servers), but the maths gives the floor.

</details>

**6.** A queue's wait time is $y = 5x + 40$ milliseconds, where x is the number of jobs
already waiting. What do the 5 and the 40 mean, and what is the wait with 12 jobs queued?

<details>
<summary>Open the answer</summary>

The slope 5 means each extra waiting job adds 5 ms; the intercept 40 is the wait (in ms)
with an empty queue. With 12 jobs: $5 \times 12 = 60$, and $60 + 40 = 100$ ms.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Add, subtract, multiply and divide negative numbers and fractions; convert between fractions, decimals and percentages; know the powers of 2 up to $2^{10}$; substitute numbers into a formula |
| **Interview-ready** | Solve and rearrange equations to answer "how many servers / how long / what rate"; read slope and intercept from a description; estimate to the right order of magnitude in your head and sanity-check the result |
| **Going deeper** | Move fluently between scientific notation and powers of 2; spot percentage-point versus percentage-change confusion in metrics; know when a straight-line model stops being trustworthy |

## Checklist

- [ ] I can add, subtract, multiply and divide with negative numbers, and explain why minus times minus is plus.
- [ ] I can add, multiply and divide fractions, and convert between fractions, decimals and percentages.
- [ ] I can work out a percentage of a number and a percentage change.
- [ ] I know the powers of 2 up to $2^{10}$, and what $x^0$ and negative powers mean.
- [ ] I can write a large or small number in scientific notation.
- [ ] I can substitute numbers into a formula, collect like terms and expand two brackets.
- [ ] I can solve a two-step equation and rearrange a formula for a different letter.
- [ ] I can find a slope from two points and read $y = mx + b$ in words.
- [ ] I round, estimate and sanity-check before I trust an answer.
