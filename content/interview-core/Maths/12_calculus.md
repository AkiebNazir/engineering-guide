# Calculus — Change, Accumulation and Optimisation

Calculus answers two questions about anything that varies: **how fast is it changing
right now?** (the derivative) and **how much has built up over time?** (the integral).
For engineers it is the maths of rates on dashboards, of training every machine-learning
model (gradient descent and backpropagation are the chain rule, applied millions of
times), of optimisation, and of the numerical methods inside libraries that compute
square roots, sines and logarithms. This chapter builds calculus visually — slopes you
can see, areas you can count — and ends with code that differentiates, integrates,
optimises and approximates.

**Where this fits:** Part 3 · Continuous maths, chapter 12 of 15. **Builds on:** [06 Sequences, sums and recurrences](06_sequences_sums_recurrences.md) (sums and the number e); [09 Linear algebra](09_linear_algebra.md) (vectors and matrices). **Next in order:** [13 Information theory and coding](13_information_theory_and_coding.md).

## Where You Will Use This

| Where | Calculus inside |
|---|---|
| Dashboards | `rate()` of a counter is a derivative; a total from a rate is an integral |
| Machine learning | Gradients, gradient descent, backpropagation (the chain rule) |
| Tuning and trade-offs | Finding a minimum: batch sizes, cache sizes, timeouts |
| Numerical code | Square roots, `exp`, `sin` via Taylor series and Newton's method |
| Smoothing and load averages | Exponential decay (EWMA) |
| Animation and physics | Velocity and acceleration as derivatives of position |

## Foundations — Speedometer and Odometer

A car has two instruments that are calculus made physical:

- The **speedometer** shows how fast distance is changing *right now* — a
  **derivative**.
- The **odometer** shows how much distance has accumulated — an **integral** of speed
  over time.

> **Key idea:** They are inverses. Differentiate the odometer reading and you get the
> speed; accumulate (integrate) the speed and you get the odometer reading. This is the
> **fundamental theorem of calculus**, and your monitoring system uses it constantly: a
> request **counter** is an odometer; `rate(requests_total[5m])` is a speedometer.

The obstacle calculus overcomes is "right now". Speed is distance ÷ time, but at a
single instant no time passes. The fix is a **limit**: measure over shorter and shorter
intervals and see what the ratio approaches.

## 1 · Limits: What a Value Approaches

$\lim_{x \to a} f(x) = L$ means f(x) gets as close to L as you like when x is close
enough to a. You do not need f(a) itself — often it is undefined, like $\frac{\sin x}{x}$
at 0.

```python
import math
print([round(math.sin(x) / x, 8) for x in (0.1, 0.01, 0.001)])   # → [0.99833417, 0.99998333, 0.99999983]
print([round((1 + 1 / n) ** n, 6) for n in (1, 10, 1000, 10**6)])   # → [2.0, 2.593742, 2.716924, 2.71828]
print(round(math.e, 6))                                             # → 2.718282
```

The second line is the most important limit in applied maths: compounding more and more
often, $(1 + 1/n)^n \to e \approx 2.71828$. It defines the number e (§8).

> **Notebook example:** Find $\lim_{x \to 3} \frac{x^2 - 9}{x - 3}$. In words: what number
> does the fraction get close to as x gets close to 3?
>
> **What you need:** a **limit** asks what a function is heading towards, not what it
> equals at that exact point. If plugging in gives $\frac{0}{0}$, that is not an answer:
> it means "simplify first, then try again". One handy pattern is the **difference of
> squares**: $a^2 - b^2 = (a - b)(a + b)$.
>
> **Plan:** try plugging in; when that gives $\frac{0}{0}$, factor the top, cancel the
> part that causes the zero, and plug in again.
>
> 1. **Try plugging in x = 3 on top.** $3^2 - 9 = 9 - 9 = 0$.
> 2. **Try plugging in x = 3 underneath.** $3 - 3 = 0$. So we get $\frac{0}{0}$.
>    *Why:* $\frac{0}{0}$ is not a number; it is a sign that the top and bottom share a
>    factor that we can remove.
> 3. **Factor the top.** $x^2 - 9$ is $x^2 - 3^2$, a difference of squares, so
>    $x^2 - 9 = (x - 3)(x + 3)$.
>    *Why:* multiply it back out to be sure: $x \cdot x + 3x - 3x - 9 = x^2 - 9$.
> 4. **Rewrite the fraction.** $\frac{x^2 - 9}{x - 3} = \frac{(x - 3)(x + 3)}{x - 3}$.
> 5. **Cancel the common factor.** The $(x - 3)$ on top and bottom cancel, leaving
>    $x + 3$.
>    *Why:* a limit only looks at x *near* 3, never at 3 itself, so $x - 3$ is never zero
>    and dividing by it is allowed.
> 6. **Plug in again.** $x + 3$ at $x = 3$ is $3 + 3 = 6$.
>
> **Answer:** the limit is 6. As x gets close to 3, the fraction gets close to 6, even
> though at exactly $x = 3$ the fraction itself is undefined.
>
> **Check:** try numbers near 3 in the original fraction. $x = 2.9$ gives 5.9,
> $x = 2.99$ gives 5.99, and $x = 3.01$ gives 6.01. It closes in on 6 from both sides. ✓
> In Python: `[(x*x - 9) / (x - 3) for x in (2.9, 2.99, 3.01)]`.

> **Your turn:** Find $\lim_{x \to 2} \frac{x^2 - 4}{x - 2}$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Try plugging in x = 2 on top.** $2^2 - 4 = 4 - 4 = 0$.
> 2. **Try plugging in x = 2 underneath.** $2 - 2 = 0$. So $\frac{0}{0}$: simplify first.
> 3. **Factor the top.** $x^2 - 4 = x^2 - 2^2 = (x - 2)(x + 2)$.
> 4. **Cancel the common factor.** $\frac{(x - 2)(x + 2)}{x - 2} = x + 2$.
> 5. **Plug in again.** $2 + 2 = 4$.
>
> **Answer:** the limit is 4. (Check: $x = 1.99$ gives 3.99 and $x = 2.01$ gives 4.01.)
>
> </details>

## 2 · The Derivative: Slope at a Point

The average rate of change of f between x and x + h is the slope of the line through
the two points (the **secant**):

$$
\frac{f(x + h) - f(x)}{h}
$$

Shrink h towards 0 and the secant turns into the **tangent** line, whose slope is the
**derivative**:

$$
f'(x) = \lim_{h \to 0} \frac{f(x + h) - f(x)}{h}
$$

> **Intuition:** Zoom in far enough on any smooth curve and it looks like a straight
> line. The derivative is the slope of that line. That is why "linearise near a point"
> works in engineering: locally, everything smooth is linear.

**Try it: shrink the secant.** Drag h down from 1 towards 0.001 and watch the secant
(accent) swing onto the tangent (green); the chips show its slope approaching f′(x).
Drag the point along the curve: the lower graph traces the slope at every x — the
derivative is itself a function. Then choose |x| and put the point at 0: a corner, where
no single slope exists.

<div class="lab" data-viz="math-derivative"></div>

> **Notebook example:** Use the definition to find the derivative (slope) of $f(x) = x^2$
> at $x = 3$.
>
> **What you need:** the **derivative** $f'(x)$ says **how fast the output changes per
> unit of input**, right at the point x. To find it, take a small step h in the input
> and measure "change in output ÷ change in input":
> $\frac{f(x + h) - f(x)}{h}$ (the **difference quotient**, which is the slope of the line
> through the two points). Then let h shrink towards 0.
>
> **Plan:** write the difference quotient with x = 3, simplify it until h is no longer
> on the bottom, then set h to 0.
>
> 1. **Write the difference quotient for x = 3.** $\frac{f(3 + h) - f(3)}{h} = \frac{(3 + h)^2 - 3^2}{h}$.
> 2. **Work out the easy square.** $3^2 = 9$, so the top is $(3 + h)^2 - 9$.
> 3. **Write the square as a product.** $(3 + h)^2 = (3 + h)(3 + h)$.
> 4. **Multiply every pair.** $3 \cdot 3 = 9$, $3 \cdot h = 3h$, $h \cdot 3 = 3h$ and
>    $h \cdot h = h^2$. So $(3 + h)^2 = 9 + 3h + 3h + h^2$.
>    *Why:* each part of the first bracket multiplies each part of the second.
> 5. **Collect the like terms.** $3h + 3h = 6h$, so $(3 + h)^2 = 9 + 6h + h^2$.
> 6. **Subtract the 9.** The top becomes $9 + 6h + h^2 - 9 = 6h + h^2$.
> 7. **Divide by h.** $\frac{6h + h^2}{h} = \frac{6h}{h} + \frac{h^2}{h} = 6 + h$.
>    *Why:* every term on top contains an h, so each one can be divided by h.
> 8. **Let h shrink to 0.** $6 + h$ becomes $6 + 0 = 6$.
>    *Why:* h is no longer on the bottom, so setting it to 0 is safe.
>
> **Answer:** $f'(3) = 6$. At $x = 3$, the output $x^2$ grows 6 times as fast as the
> input: nudge x from 3 to 3.001 and $x^2$ rises by about 0.006.
>
> **Check:** compute the secant slope for real values of h. $h = 1$ gives
> $\frac{16 - 9}{1} = 7$, $h = 0.1$ gives 6.1 and $h = 0.01$ gives 6.01, exactly
> $6 + h$, closing in on 6. ✓ It also matches the power rule in §3:
> $\frac{d}{dx}x^2 = 2x$, and $2 \cdot 3 = 6$.

> **Your turn:** Use the definition to find the derivative of $f(x) = x^2$ at $x = 2$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the difference quotient for x = 2.** $\frac{(2 + h)^2 - 2^2}{h} = \frac{(2 + h)^2 - 4}{h}$.
> 2. **Multiply every pair.** $(2 + h)(2 + h) = 4 + 2h + 2h + h^2$.
> 3. **Collect the like terms.** $4 + 4h + h^2$.
> 4. **Subtract the 4.** The top is $4 + 4h + h^2 - 4 = 4h + h^2$.
> 5. **Divide by h.** $\frac{4h + h^2}{h} = 4 + h$.
> 6. **Let h shrink to 0.** $4 + 0 = 4$.
>
> **Answer:** $f'(2) = 4$: near $x = 2$, $x^2$ changes 4 times as fast as x (and $2x = 4$ ✓).
>
> </details>

### Numerical derivatives and the h trade-off

In code, you cannot take a limit, so you pick a small h. Too big and the secant is a poor
approximation; too small and floating-point cancellation (chapter 02) destroys the
digits. The **central difference** $\frac{f(x+h) - f(x-h)}{2h}$ is far more accurate for
the same h.

```python
import math
f, x, true = math.sin, 1.0, math.cos(1.0)
errors = {h: (abs((f(x + h) - f(x)) / h - true), abs((f(x + h) - f(x - h)) / (2 * h) - true)) for h in (1e-2, 1e-5, 1e-8, 1e-12)}
print({h: f"{e[0]:.0e} / {e[1]:.0e}" for h, e in errors.items()})   # → {0.01: '4e-03 / 9e-06', 1e-05: '4e-06 / 1e-11', 1e-08: '3e-09 / 3e-09', 1e-12: '4e-05 / 1e-05'}
```

Read the table as forward error / central error. Forward differences are best around
$h \approx 10^{-8}$ (the square root of machine epsilon); at $h = 10^{-12}$ cancellation
makes both worse again. ML frameworks use this **gradient check** to test hand-written
derivatives — and use exact automatic differentiation (§6) for the real thing.

## 3 · Rules for Derivatives

You rarely take limits by hand; a few rules cover almost everything.

| Function | Derivative | Note |
|---|---|---|
| $c$ (constant) | $0$ | constants do not change |
| $x^n$ | $n x^{n-1}$ | power rule: $x^2 \to 2x$, $\sqrt{x} \to \frac{1}{2\sqrt{x}}$ |
| $e^x$ | $e^x$ | its own slope — that is what makes e special |
| $\ln x$ | $1/x$ | |
| $\sin x$, $\cos x$ | $\cos x$, $-\sin x$ | angles in radians |
| $c\,f(x)$, $f + g$ | $c\,f'$, $f' + g'$ | derivatives are linear |
| $f \cdot g$ | $f'g + fg'$ | product rule |
| $f(g(x))$ | $f'(g(x)) \cdot g'(x)$ | **chain rule** |

> **Analogy (chain rule):** Gears. If gear A turns 3 times as fast as gear B, and B
> turns 2 times as fast as C, then A turns 3 × 2 = 6 times as fast as C. Rates of change
> through a chain **multiply**. That single idea is backpropagation.

> **Worked example:** $h(x) = (3x^2 + 1)^5$. Outer $u^5$, inner $u = 3x^2 + 1$:
> $h'(x) = 5u^4 \cdot 6x = 30x(3x^2 + 1)^4$. At x = 1: $30 \cdot 4^4 = 7680$.

```python
h = lambda x: (3 * x**2 + 1) ** 5
central = lambda f, x, e=1e-6: (f(x + e) - f(x - e)) / (2 * e)
print(round(central(h, 1.0)), 30 * 1 * (3 + 1) ** 4)   # → 7680 7680
```

Checking an analytic derivative against a numerical one is a habit worth keeping.

## 4 · Using Derivatives: Maxima, Minima and Trade-offs

Where a smooth function reaches a peak or valley, its tangent is flat: $f'(x) = 0$. The
**second derivative** $f''$ (the rate of change of the slope — curvature, or
acceleration) says which: $f'' > 0$ is a valley (minimum), $f'' < 0$ a peak.

> **Worked example: the best batch size.** Sending a batch costs a fixed overhead
> c = 50 ms plus a waiting cost: items wait on average for half the batch to fill, say
> k = 0.02 ms per item per item in the batch. The cost per item is
> $f(b) = \frac{c}{b} + k\,b$. Setting $f'(b) = -\frac{c}{b^2} + k = 0$ gives
> $b^* = \sqrt{c/k} = 50$.

```python
import math
c, k = 50, 0.02
cost = lambda b: c / b + k * b
best = min(range(1, 500), key=cost)
print(best, math.sqrt(c / k), round(cost(best), 3))   # → 50 50.0 2.0
```

This **square-root law** (fixed cost against a cost that grows with size) appears in
batching, checkpoint intervals, economic order quantities and the $\sqrt{n}$ block size
in sqrt-decomposition. At the optimum the two costs are **equal** — a useful sanity check.

## 5 · Many Variables: Partial Derivatives and the Gradient

A model's loss depends on thousands of parameters at once. A **partial derivative**
$\frac{\partial f}{\partial x}$ is the ordinary derivative with respect to one variable,
holding the others fixed. Collect them all into a vector and you get the **gradient**:

$$
\nabla f = \left(\frac{\partial f}{\partial x_1}, \dots, \frac{\partial f}{\partial x_n}\right)
$$

> **Key idea:** The gradient points in the direction of **steepest ascent**, and its
> length is how steep. So to go **downhill** fastest, step against it. That is
> **gradient descent**: $x \leftarrow x - \eta \nabla f(x)$, where the **learning rate**
> η sets the step size.

> **Analogy:** You are on a foggy mountain and want to reach the valley. You cannot see
> far, but you can feel the slope under your feet. Step downhill, feel again, repeat.
> Too small a step and you take forever; too large and you leap across the valley and
> up the other side.

```python
def gradient_descent(grad, x, lr, steps):
    for _ in range(steps):
        x = [xi - lr * gi for xi, gi in zip(x, grad(x))]
    return x

# f(x, y) = (x - 3)^2 + 10 (y + 1)^2 : a stretched bowl with its minimum at (3, -1)
grad = lambda p: [2 * (p[0] - 3), 20 * (p[1] + 1)]
print([round(v, 4) for v in gradient_descent(grad, [0.0, 0.0], lr=0.05, steps=200)])   # → [3.0, -1.0]
print([round(v, 1) for v in gradient_descent(grad, [0.0, 0.0], lr=0.11, steps=20)])    # → [3.0, 37.3]
```

With learning rate 0.11 the steep direction (the $10(y+1)^2$ term) overshoots more each
step and diverges: the step must be smaller than about $2/\text{curvature}$ in the
steepest direction. Stretched bowls like this are why plain gradient descent zig-zags,
and why optimisers such as momentum and Adam exist.

> **Notebook example:** For $f(x, y) = x^2 + xy + 2y^2$, find the gradient at the point
> (2, 1).
>
> **What you need:** a **partial derivative** $\frac{\partial f}{\partial x}$ is how fast f
> changes when only x moves. Treat every other letter as a fixed number (freeze it) and
> differentiate as usual. Three facts cover this example: $x^2$ becomes $2x$ (power
> rule); a fixed number times x, like $5x$, becomes just the number, 5; and a term with
> no x in it at all is a constant, so it becomes 0. The **gradient** $\nabla f$ is the
> list of all the partial derivatives: $\left(\frac{\partial f}{\partial x}, \frac{\partial f}{\partial y}\right)$.
>
> **Plan:** find each partial derivative as a formula, then put in x = 2 and y = 1.
>
> 1. **Freeze y and differentiate each term in x.** $x^2 \to 2x$. $xy \to y$ (y is just
>    a number here, like $5x \to 5$). $2y^2 \to 0$ (no x in it).
> 2. **Add the pieces.** $\frac{\partial f}{\partial x} = 2x + y + 0 = 2x + y$.
> 3. **Freeze x and differentiate each term in y.** $x^2 \to 0$ (no y in it). $xy \to x$
>    (x is just a number now). $2y^2 \to 2 \cdot 2y = 4y$.
> 4. **Add the pieces.** $\frac{\partial f}{\partial y} = 0 + x + 4y = x + 4y$.
> 5. **Substitute (2, 1) into the x-slope.** $2 \cdot 2 + 1 = 4 + 1 = 5$.
> 6. **Substitute (2, 1) into the y-slope.** $2 + 4 \cdot 1 = 2 + 4 = 6$.
> 7. **Collect them into the gradient.** $\nabla f(2, 1) = (5, 6)$.
>
> **Answer:** $\nabla f(2, 1) = (5, 6)$. Standing at (2, 1), f rises about 5 per unit
> step in x and about 6 per unit step in y; the vector (5, 6) points uphill.
>
> **Check:** nudge x a little. $f(2.001, 1) = 4.004001 + 2.001 + 2 = 8.005001$, and
> $f(2, 1) = 8$, so f rose 0.005001 for a 0.001 step: a slope of about 5. ✓

> **Your turn:** Find the gradient of $f(x, y) = x^2 + 3xy$ at (1, 2).
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Freeze y and differentiate each term in x.** $x^2 \to 2x$, and $3xy \to 3y$.
> 2. **Add the pieces.** $\frac{\partial f}{\partial x} = 2x + 3y$.
> 3. **Freeze x and differentiate each term in y.** $x^2 \to 0$, and $3xy \to 3x$, so
>    $\frac{\partial f}{\partial y} = 3x$.
> 4. **Substitute (1, 2).** $2 \cdot 1 + 3 \cdot 2 = 2 + 6 = 8$, and $3 \cdot 1 = 3$.
>
> **Answer:** $\nabla f(1, 2) = (8, 3)$.
>
> </details>

> **Notebook example:** For the same $f(x, y) = x^2 + xy + 2y^2$, start at (2, 1), where
> the gradient is (5, 6). Take one gradient-descent step with learning rate η = 0.1.
>
> **What you need:** the gradient points uphill, so to go downhill you step the
> **opposite** way. The update rule is new point = old point − η × gradient, done
> separately for each coordinate. η (the Greek letter eta) is the **learning rate**: the
> fraction of the gradient you step by.
>
> **Plan:** scale the gradient by η, then subtract it from each coordinate.
>
> 1. **Write the rule.** $(x, y) \leftarrow (2, 1) - 0.1 \times (5, 6)$.
> 2. **Scale the gradient by η.** $0.1 \times 5 = 0.5$ and $0.1 \times 6 = 0.6$, so the
>    step is (0.5, 0.6).
>    *Why:* a small learning rate keeps the step short, so we do not overshoot the valley.
> 3. **Subtract from x.** $2 - 0.5 = 1.5$.
> 4. **Subtract from y.** $1 - 0.6 = 0.4$.
> 5. **Write the new point.** (1.5, 0.4).
>
> **Answer:** the new point is (1.5, 0.4). One step of gradient descent is exactly the
> line `x = [xi - lr * gi for xi, gi in zip(x, grad(x))]` in the code above.
>
> **Check:** the loss should have gone down. Before: $f(2, 1) = 4 + 2 + 2 = 8$. After:
> $f(1.5, 0.4) = 2.25 + 0.6 + 0.32 = 3.17$. It fell from 8 to 3.17. ✓

> **Your turn:** For $f(x, y) = x^2 + y^2$ at (3, 4) the gradient is (6, 8). Take one
> gradient-descent step with η = 0.25.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the rule.** $(x, y) \leftarrow (3, 4) - 0.25 \times (6, 8)$.
> 2. **Scale the gradient by η.** $0.25 \times 6 = 1.5$ and $0.25 \times 8 = 2$.
> 3. **Subtract from x.** $3 - 1.5 = 1.5$.
> 4. **Subtract from y.** $4 - 2 = 2$.
>
> **Answer:** the new point is (1.5, 2), and the loss fell from $9 + 16 = 25$ to
> $2.25 + 4 = 6.25$.
>
> </details>

**Try it: race the optimisers.** Click a starting point on the loss surface and press
*Play* to watch plain gradient descent, momentum and Adam find the valley — and how the
learning rate changes their paths.

<div class="lab" data-viz="gradient"></div>

## 6 · The Chain Rule at Scale: Backpropagation

A neural network is a long composition of simple functions. To train it you need the
derivative of the loss with respect to every weight. The chain rule says: multiply local
derivatives along the path. **Backpropagation** does this efficiently by working
**backwards** from the loss, reusing each intermediate result — one backward pass costs
about as much as one forward pass, whatever the number of weights.

**Try it: backprop one node at a time.** Run the forward pass, then the backward pass.
Each red number is ∂L/∂(that node), built by multiplying local slopes from right to
left — the chain rule, drawn.

<div class="lab" data-viz="backprop"></div>

> **Notebook example:** (warm-up: the chain rule) Let $L = (2w + 1)^2$. Find
> $\frac{dL}{dw}$ at $w = 1$, that is, how fast L changes per unit change in w there.
>
> **What you need:** the **chain rule**. When L depends on u, and u depends on w, the
> slopes multiply: $\frac{dL}{dw} = \frac{dL}{du} \times \frac{du}{dw}$. It is the gear
> analogy from §3: if L turns 6 times as fast as u, and u turns 2 times as fast as w,
> then L turns $6 \times 2 = 12$ times as fast as w.
>
> **Plan:** name the inside part u, find the outer slope and the inner slope, and
> multiply them.
>
> 1. **Name the inside.** Let $u = 2w + 1$, so $L = u^2$.
> 2. **Find the value of u.** At $w = 1$: $u = 2 \cdot 1 + 1 = 3$.
> 3. **Find the outer slope.** $L = u^2$, so $\frac{dL}{du} = 2u = 2 \cdot 3 = 6$.
>    *Why:* the power rule turns $u^2$ into $2u$.
> 4. **Find the inner slope.** $u = 2w + 1$, so $\frac{du}{dw} = 2$.
>    *Why:* every extra 1 in w adds 2 to u; the "+ 1" never changes, so it adds nothing.
> 5. **Multiply the slopes.** $\frac{dL}{dw} = 6 \times 2 = 12$.
>
> **Answer:** $\frac{dL}{dw} = 12$ at $w = 1$: nudge w up by 0.001 and L rises by about
> 0.012.
>
> **Check:** multiply out first instead. $(2w + 1)^2 = 4w^2 + 4w + 1$, whose derivative
> is $8w + 4$. At $w = 1$ that is $8 + 4 = 12$. ✓

> **Your turn:** Let $L = (3w - 1)^2$. Find $\frac{dL}{dw}$ at $w = 2$ with the chain rule.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Name the inside.** $u = 3w - 1$, so $L = u^2$.
> 2. **Find the value of u.** $u = 3 \cdot 2 - 1 = 6 - 1 = 5$.
> 3. **Find the outer slope.** $\frac{dL}{du} = 2u = 2 \cdot 5 = 10$.
> 4. **Find the inner slope.** $\frac{du}{dw} = 3$.
> 5. **Multiply the slopes.** $10 \times 3 = 30$.
>
> **Answer:** $\frac{dL}{dw} = 30$. (Check: $9w^2 - 6w + 1$ has derivative $18w - 6 = 36 - 6 = 30$.)
>
> </details>

> **Notebook example:** A one-weight model: $L = (w x + b - y)^2$ with $w = 2$, $x = 3$,
> $b = 1$ and $y = 5$. Find $\frac{\partial L}{\partial w}$ and $\frac{\partial L}{\partial b}$
> by backpropagation.
>
> **What you need:** L is the **loss**: how wrong the model is (here, the squared gap
> between the prediction $wx + b$ and the target y). $\frac{\partial L}{\partial w}$ means
> "how much L changes per unit change in w, with everything else held still". To train,
> we need it for every adjustable number (here w and b). **Backpropagation** is the chain
> rule done in an order that reuses work: first a **forward pass** computes and saves
> each intermediate value; then a **backward pass** goes from the loss back towards the
> inputs, and at each node does: gradient here = gradient from the node after it
> (the **upstream gradient**) × this node's own **local slope**.
>
> **Plan:** break L into three small steps ($z$, then $e$, then $L$), compute them
> forwards, then multiply slopes backwards.
>
> 1. **Forward: compute the prediction.** $z = wx + b = 2 \cdot 3 + 1 = 6 + 1 = 7$.
> 2. **Forward: compute the error.** $e = z - y = 7 - 5 = 2$.
> 3. **Forward: compute the loss.** $L = e^2 = 2^2 = 4$.
> 4. **Backward through the square.** $L = e^2$, so the local slope is $2e = 2 \cdot 2 = 4$.
>    So $\frac{\partial L}{\partial e} = 4$.
>    *Why:* this is the first node going backwards, so the upstream gradient is just 1,
>    and $1 \times 4 = 4$.
> 5. **Backward through the subtraction.** $e = z - y$: raising z by 1 raises e by 1, so
>    the local slope is 1. $\frac{\partial L}{\partial z} = 4 \times 1 = 4$.
> 6. **Backward to w.** $z = wx + b$: raising w by 1 raises z by x, which is 3. So the
>    local slope is 3, and $\frac{\partial L}{\partial w} = 4 \times 3 = 12$.
> 7. **Backward to b.** Raising b by 1 raises z by 1, so the local slope is 1, and
>    $\frac{\partial L}{\partial b} = 4 \times 1 = 4$.
>    *Why:* both w and b reuse $\frac{\partial L}{\partial z} = 4$ from step 5. That reuse
>    is what makes backprop cheap.
>
> **Answer:** $\frac{\partial L}{\partial w} = 12$ and $\frac{\partial L}{\partial b} = 4$.
> Every backward step was "upstream gradient × local slope", done in reverse order: the
> same thing the `Value` class below does in `backward()`.
>
> **Check:** nudge w and recompute. With $w = 2.001$: $z = 7.003$, $e = 2.003$ and
> $L = 4.012009$. L rose by 0.012009 for a 0.001 nudge, a slope of
> $\frac{0.012009}{0.001} \approx 12.0$. ✓

> **Your turn:** Same model, $L = (wx + b - y)^2$, now with $w = 1$, $x = 2$, $b = 0$ and
> $y = 1$. Find $\frac{\partial L}{\partial w}$ and $\frac{\partial L}{\partial b}$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Forward: compute z, e and L.** $z = 1 \cdot 2 + 0 = 2$, $e = 2 - 1 = 1$ and
>    $L = 1^2 = 1$.
> 2. **Backward through the square.** $\frac{\partial L}{\partial e} = 2e = 2 \cdot 1 = 2$.
> 3. **Backward through the subtraction.** $\frac{\partial L}{\partial z} = 2 \times 1 = 2$.
> 4. **Backward to w.** The local slope is x = 2, so $\frac{\partial L}{\partial w} = 2 \times 2 = 4$.
> 5. **Backward to b.** The local slope is 1, so $\frac{\partial L}{\partial b} = 2 \times 1 = 2$.
>
> **Answer:** $\frac{\partial L}{\partial w} = 4$ and $\frac{\partial L}{\partial b} = 2$.
>
> </details>

The whole idea fits in a few lines of Python: record each operation and how to pass a
gradient back through it (**reverse-mode automatic differentiation**, the engine inside
PyTorch and JAX):

```python
import math

class Value:
    def __init__(self, data, parents=(), backward=lambda: None):
        self.data, self.grad, self._parents, self._backward = data, 0.0, parents, backward

    def __add__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data + other.data, (self, other))
        def backward():
            self.grad += out.grad                  # d(a+b)/da = 1
            other.grad += out.grad
        out._backward = backward
        return out

    def __mul__(self, other):
        other = other if isinstance(other, Value) else Value(other)
        out = Value(self.data * other.data, (self, other))
        def backward():
            self.grad += other.data * out.grad     # d(ab)/da = b
            other.grad += self.data * out.grad
        out._backward = backward
        return out

    def tanh(self):
        t = math.tanh(self.data)
        out = Value(t, (self,))
        def backward():
            self.grad += (1 - t * t) * out.grad    # d tanh(u)/du = 1 - tanh²
        out._backward = backward
        return out

    def backprop(self):
        order, seen = [], set()
        def visit(v):
            if id(v) not in seen:
                seen.add(id(v))
                for p in v._parents:
                    visit(p)
                order.append(v)
        visit(self)
        self.grad = 1.0
        for v in reversed(order):                  # reverse topological order
            v._backward()

# one neuron: out = tanh(w1*x1 + w2*x2 + b)
x1, x2, w1, w2, b = Value(2.0), Value(0.0), Value(-3.0), Value(1.0), Value(6.8813735870195432)
out = (x1 * w1 + x2 * w2 + b).tanh()
out.backprop()
print(round(out.data, 4), round(w1.grad, 4), round(x1.grad, 4))   # → 0.7071 1.0 -1.5

f = lambda w: math.tanh(2.0 * w + 0.0 * 1.0 + 6.8813735870195432)
print(round((f(-3.0 + 1e-6) - f(-3.0 - 1e-6)) / 2e-6, 4))          # → 1.0
```

The last line checks ∂out/∂w1 numerically: the automatic gradient is right. Notice
`backprop` visits nodes in reverse **topological order** (chapter 08) — every node's
gradient is complete before it is passed further back.

## 7 · Integrals: Accumulation and Area

The integral $\int_a^b f(x)\,dx$ is the total accumulated by a rate f(x) from a to b —
geometrically, the area under the curve. Compute it by slicing into thin strips and
adding them up (a **Riemann sum**); the integral is the limit as the strips get thin.

**Try it: count the strips.** Raise n and watch the rectangles fill the area. With left
or right rectangles the error halves when n doubles (the "÷ 2" chip); midpoint and
trapezoid rules divide it by about 4 — the same work, much better answers.

<div class="lab" data-viz="math-riemann"></div>

> **Key idea (fundamental theorem of calculus):** If $F' = f$, then
> $\int_a^b f(x)\,dx = F(b) - F(a)$. Integration undoes differentiation. The area under
> $x^2$ from 0 to 2 is $\frac{2^3}{3} - 0 = \frac{8}{3}$ because the derivative of
> $\frac{x^3}{3}$ is $x^2$.

```python
def trapezoid(f, a, b, n):
    h = (b - a) / n
    return h * (f(a) / 2 + sum(f(a + i * h) for i in range(1, n)) + f(b) / 2)

print(round(trapezoid(lambda x: x * x, 0, 2, 1000), 6), round(8 / 3, 6))   # → 2.666668 2.666667

# a traffic curve in requests/second over one hour; the total is its integral
import math
rate = lambda t: 200 + 150 * math.sin(math.pi * t / 3600)      # t in seconds
print(round(trapezoid(rate, 0, 3600, 3600)))                   # → 1063775
```

About 1.06 million requests in the hour. Going the other way, `rate()` over a counter
is a derivative computed as a difference quotient over a window — exactly §2's secant.

> **Notebook example:** Estimate $\int_0^2 x^2\,dx$ (the area under $y = x^2$ from 0 to 2)
> using 4 strips and the **left** edge of each strip.
>
> **What you need:** a **Riemann sum** estimates an area by cutting it into n thin
> vertical strips and pretending each strip is a rectangle. Every strip has width
> $\frac{b - a}{n}$, where a and b are the start and end. With the **left rule**, a
> strip's height is the curve's value at the strip's left edge. Rectangle area = width ×
> height; add up all the rectangles.
>
> **Plan:** find the width, list the left edges, find the heights, add them, and multiply
> by the width.
>
> 1. **Find the strip width.** $\frac{2 - 0}{4} = \frac{2}{4} = 0.5$.
> 2. **List the left edges.** Start at 0 and add 0.5 each time: 0, 0.5, 1, 1.5.
>    *Why:* the fourth strip runs from 1.5 to 2, so 2 itself is never a left edge.
> 3. **Find each height.** Square each edge: $0^2 = 0$, $0.5^2 = 0.25$, $1^2 = 1$ and
>    $1.5^2 = 2.25$.
> 4. **Add the heights.** $0 + 0.25 = 0.25$, then $0.25 + 1 = 1.25$, then
>    $1.25 + 2.25 = 3.5$.
> 5. **Multiply by the width.** $3.5 \times 0.5 = 1.75$.
>    *Why:* every rectangle has the same width, so multiplying once does all four
>    "width × height" sums in one go.
>
> **Answer:** about 1.75. It is too low: $x^2$ rises across each strip, so its left edge
> is the lowest point, and every rectangle sits under the curve.
>
> **Check:** in Python, `sum((i * 0.5) ** 2 for i in range(4)) * 0.5` gives 1.75. ✓ It is
> below the exact area, 2.667, found two examples further on.

> **Your turn:** Estimate the same area, $\int_0^2 x^2\,dx$ with 4 strips, using the
> **right** edge of each strip.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the strip width.** $\frac{2 - 0}{4} = 0.5$.
> 2. **List the right edges.** 0.5, 1, 1.5, 2.
> 3. **Find each height.** $0.25$, $1$, $2.25$ and $4$.
> 4. **Add the heights.** $0.25 + 1 + 2.25 + 4 = 7.5$.
> 5. **Multiply by the width.** $7.5 \times 0.5 = 3.75$.
>
> **Answer:** about 3.75. This time it is too high, because each right edge is the
> highest point of its strip.
>
> </details>

> **Notebook example:** Estimate $\int_0^2 x^2\,dx$ with 4 strips using the **midpoint**
> of each strip.
>
> **What you need:** the **midpoint rule** is the same as the left rule, except each
> rectangle's height is the curve's value at the **middle** of its strip. The middle is
> the left edge plus half a width.
>
> **Plan:** find the width, list the midpoints, find the heights, add them, multiply by
> the width.
>
> 1. **Find the strip width.** $\frac{2 - 0}{4} = 0.5$, so half a width is 0.25.
> 2. **List the midpoints.** Add 0.25 to each left edge (0, 0.5, 1, 1.5): that gives
>    0.25, 0.75, 1.25, 1.75.
> 3. **Find each height.** $0.25^2 = 0.0625$, $0.75^2 = 0.5625$, $1.25^2 = 1.5625$ and
>    $1.75^2 = 3.0625$.
> 4. **Add the heights.** $0.0625 + 0.5625 = 0.625$, then $0.625 + 1.5625 = 2.1875$, then
>    $2.1875 + 3.0625 = 5.25$.
> 5. **Multiply by the width.** $5.25 \times 0.5 = 2.625$.
>    *Why:* in each strip the rectangle pokes above the curve on one half and falls short
>    of it on the other half, so the two errors mostly cancel.
>
> **Answer:** about 2.625, much closer to the true area than the left (1.75) or right
> (3.75) sums, for exactly the same amount of work.
>
> **Check:** in Python, `sum(((i + 0.5) * 0.5) ** 2 for i in range(4)) * 0.5` gives
> 2.625. ✓ It also sits between the left and right estimates, as it should.

> **Your turn:** Estimate $\int_0^2 x^2\,dx$ with only **2** strips, using midpoints.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the strip width.** $\frac{2 - 0}{2} = 1$, so half a width is 0.5.
> 2. **List the midpoints.** 0.5 and 1.5.
> 3. **Find each height.** $0.5^2 = 0.25$ and $1.5^2 = 2.25$.
> 4. **Add the heights.** $0.25 + 2.25 = 2.5$.
> 5. **Multiply by the width.** $2.5 \times 1 = 2.5$.
>
> **Answer:** about 2.5. Even two midpoint strips beat four left-edge strips (1.75).
>
> </details>

> **Notebook example:** Find $\int_0^2 x^2\,dx$ exactly, and compare it with the three
> estimates above.
>
> **What you need:** the **fundamental theorem of calculus**: if F is a function whose
> derivative is f (F is called an **antiderivative** of f), then
> $\int_a^b f(x)\,dx = F(b) - F(a)$. In words: the total built up from a to b is
> "odometer at the end minus odometer at the start".
>
> **Plan:** find an antiderivative of $x^2$, evaluate it at 2 and at 0, subtract.
>
> 1. **Find an antiderivative.** $F(x) = \frac{x^3}{3}$.
>    *Why:* by the power rule the derivative of $x^3$ is $3x^2$, and dividing by 3
>    leaves exactly $x^2$.
> 2. **Evaluate at the end.** $F(2) = \frac{2^3}{3} = \frac{8}{3}$.
> 3. **Evaluate at the start.** $F(0) = \frac{0^3}{3} = 0$.
> 4. **Subtract.** $\frac{8}{3} - 0 = \frac{8}{3} \approx 2.667$.
> 5. **Compare with the estimates.** Left: $2.667 - 1.75 \approx 0.92$ too low. Right:
>    $3.75 - 2.667 \approx 1.08$ too high. Midpoint: $2.667 - 2.625 \approx 0.04$ too low.
>
> **Answer:** exactly $\frac{8}{3} \approx 2.667$. The midpoint rule missed by only 0.04,
> while the left and right sums missed by about 0.9 and 1.1: same work, much better
> answer.
>
> **Check:** the trapezoid code above, with 1,000 strips, prints 2.666668. ✓

> **Your turn:** Find $\int_0^3 x^2\,dx$ exactly.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find an antiderivative.** $F(x) = \frac{x^3}{3}$.
> 2. **Evaluate at the end.** $F(3) = \frac{27}{3} = 9$.
> 3. **Evaluate at the start.** $F(0) = 0$.
> 4. **Subtract.** $9 - 0 = 9$.
>
> **Answer:** the area under $x^2$ from 0 to 3 is exactly 9.
>
> </details>

## 8 · The Number e and Exponential Change

e is the base whose exponential is its own derivative: $\frac{d}{dx}e^x = e^x$. So
$e^{kx}$ describes anything that **changes in proportion to its current size**: growth
when k > 0, decay when k < 0.

- Continuous compound growth: $P(t) = P_0 e^{rt}$.
- Decay with a half-life: the amount left after t is $e^{-t \ln 2 / T_{1/2}}$.
- **Exponentially weighted moving averages** (EWMA) — smoothing where each old sample's
  weight decays exponentially. The Unix load average, adaptive timeouts (TCP's RTT
  estimate), anomaly baselines and "peak EWMA" load balancers all use it.

```python
def ewma(samples, alpha):
    avg = samples[0]
    out = []
    for s in samples:
        avg = alpha * s + (1 - alpha) * avg      # new = α·sample + (1−α)·old
        out.append(round(avg, 1))
    return out

latency = [100, 100, 100, 400, 100, 100, 100, 100]
print(ewma(latency, 0.2))   # → [100.0, 100.0, 100.0, 160.0, 148.0, 138.4, 130.7, 124.6]
```

One spike moves the average by α × (spike − average) and then decays by a factor
$(1 - \alpha)$ per sample — memory that fades exponentially.

> **Notebook example:** An EWMA with α = 0.2 has settled at 100 ms. Then one sample of
> 400 ms arrives, followed by more 100s. Track the average for four samples.
>
> **What you need:** an **EWMA** (exponentially weighted moving average) is a running
> average that updates once per sample with
> new = α × sample + (1 − α) × old. Rearranged, that is
> new = old + α × (sample − old): "move a fraction α of the way from the old average
> towards the new sample". α (alpha) is a number between 0 and 1; here 0.2, one fifth.
>
> **Plan:** for each sample, find the gap between it and the average, take α of that
> gap, and move the average by that much.
>
> 1. **Find the gap for the spike.** $400 - 100 = 300$.
> 2. **Take α of the gap.** $0.2 \times 300 = 60$.
> 3. **Move the average.** $100 + 60 = 160$.
>    *Why:* the average only moves one fifth of the way, so one bad sample cannot drag
>    it all the way up to 400.
> 4. **Repeat for the next 100.** Gap: $100 - 160 = -60$. Fifth: $0.2 \times (-60) = -12$.
>    Move: $160 - 12 = 148$.
> 5. **Repeat for the next 100.** Gap: $100 - 148 = -48$. Fifth: $-9.6$. Move:
>    $148 - 9.6 = 138.4$.
> 6. **Repeat for the next 100.** Gap: $100 - 138.4 = -38.4$. Fifth: $-7.68$. Move:
>    $138.4 - 7.68 = 130.72$.
> 7. **Look at the excess over 100.** The averages sit 60, 48, 38.4 and 30.72 above 100.
> 8. **Compare neighbours.** $48 \div 60 = 0.8$, $38.4 \div 48 = 0.8$ and
>    $30.72 \div 38.4 = 0.8$.
>    *Why:* each sample keeps $1 - \alpha = 0.8$ of the old excess, so the excess shrinks
>    by the same factor every time.
>
> **Answer:** 160, 148, 138.4, 130.72. The spike's effect shrinks by a factor
> $(1 - \alpha) = 0.8$ per sample, like $e^{-kt}$: exponential forgetting.
>
> **Check:** the `ewma` code above prints 160.0, 148.0, 138.4, 130.7 for these samples
> (rounded to one decimal place). ✓ And $60 \times 0.8^3 = 60 \times 0.512 = 30.72$. ✓

> **Your turn:** An EWMA with α = 0.5 has settled at 10. One sample of 30 arrives, then
> two samples of 10. Track the average.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the gap for the spike.** $30 - 10 = 20$.
> 2. **Take α of the gap.** $0.5 \times 20 = 10$.
> 3. **Move the average.** $10 + 10 = 20$.
> 4. **Repeat for the next 10.** Gap $10 - 20 = -10$, half is $-5$, so $20 - 5 = 15$.
> 5. **Repeat for the next 10.** Gap $10 - 15 = -5$, half is $-2.5$, so $15 - 2.5 = 12.5$.
>
> **Answer:** 20, 15, 12.5. The excess over 10 goes 10, 5, 2.5: it halves each time,
> because $1 - \alpha = 0.5$.
>
> </details>

## 9 · Taylor Series: Polynomials That Imitate Functions

Near a point, a smooth function can be approximated by a polynomial that matches its
value, slope, curvature and higher derivatives there:

$$
f(x) \approx f(0) + f'(0)\,x + \frac{f''(0)}{2!}x^2 + \frac{f'''(0)}{3!}x^3 + \dots
$$

$$
e^x = 1 + x + \frac{x^2}{2!} + \dots \qquad \sin x = x - \frac{x^3}{3!} + \frac{x^5}{5!} - \dots \qquad \ln(1+x) = x - \frac{x^2}{2} + \frac{x^3}{3} - \dots
$$

**Try it: build sin from polynomials.** Add terms one at a time: each hugs the curve over
a wider range. Then choose ln(1 + x) — past x = 1 the polynomials diverge wildly: every
series has a range where it works.

<div class="lab" data-viz="math-taylor"></div>

The first-order versions are the approximations engineers use constantly, and they
explain results elsewhere in this module:

| Approximation (small x) | Used for |
|---|---|
| $e^x \approx 1 + x$, $1 - x \approx e^{-x}$ | the birthday bound (chapter 10), $(1 - 1/n)^n \approx 1/e$ |
| $\ln(1 + x) \approx x$ | rule of 70 for doubling times (chapter 06) |
| $(1 + x)^n \approx 1 + nx$ | small-percentage compounding, error propagation |
| $\sin x \approx x$ | small angles in graphics and physics |

```python
import math
x = 0.01
print(round(math.exp(x), 6), 1 + x)                           # → 1.01005 1.01
print(round(sum(x**k / math.factorial(k) for k in range(8)), 12) == round(math.exp(x), 12))   # → True
```

> **Notebook example:** Approximate $e^{0.1}$ with the first four Taylor terms.
>
> **What you need:** the Taylor series for $e^x$ is
> $e^x = 1 + x + \frac{x^2}{2!} + \frac{x^3}{3!} + \dots$, where $n!$ ("n factorial")
> means $1 \cdot 2 \cdot \ldots \cdot n$, so $2! = 2$ and $3! = 6$. For small x each term is
> much smaller than the one before, so the first few terms already give a very good
> answer. "Four terms" means $1 + x + \frac{x^2}{2} + \frac{x^3}{6}$.
>
> **Plan:** work out each of the four terms with x = 0.1, then add them up.
>
> 1. **Write the first term.** It is just 1.
> 2. **Write the second term.** It is x, which is 0.1.
> 3. **Work out the third term.** $x^2 = 0.1 \times 0.1 = 0.01$, and
>    $\frac{0.01}{2} = 0.005$.
> 4. **Work out the fourth term.** $x^3 = 0.01 \times 0.1 = 0.001$, and
>    $\frac{0.001}{6} \approx 0.000167$.
>    *Why:* each term is at least 10 times smaller than the one before, so the terms we
>    leave out are tiny.
> 5. **Add the terms.** $1 + 0.1 = 1.1$, then $1.1 + 0.005 = 1.105$, then
>    $1.105 + 0.000167 = 1.105167$.
>
> **Answer:** $e^{0.1} \approx 1.105167$, which is 1.10517 to 5 decimal places, from four
> terms. Even just $1 + x = 1.1$ is within 0.5%; that first-order approximation (also
> written $\ln(1 + x) \approx x$) is the one behind the rule of 70.
>
> **Check:** `math.exp(0.1)` gives 1.105171, so the error is about 0.000004. That is
> roughly the size of the first term we left out, $\frac{x^4}{4!} = \frac{0.0001}{24} \approx 0.000004$. ✓

> **Your turn:** Approximate $e^{0.2}$ with the first four Taylor terms.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the first term.** 1.
> 2. **Write the second term.** 0.2.
> 3. **Work out the third term.** $0.2 \times 0.2 = 0.04$, and $\frac{0.04}{2} = 0.02$.
> 4. **Work out the fourth term.** $0.04 \times 0.2 = 0.008$, and
>    $\frac{0.008}{6} \approx 0.001333$.
> 5. **Add the terms.** $1 + 0.2 + 0.02 + 0.001333 = 1.221333$.
>
> **Answer:** $e^{0.2} \approx 1.22133$. The true value is 1.22140, so the error is about
> 0.00007: bigger than for 0.1, because x is further from 0.
>
> </details>

## 10 · Newton's Method: Solving Equations With Tangents

To solve $f(x) = 0$, start with a guess, follow the tangent line down to where it
crosses zero, and repeat:

$$
x_{k+1} = x_k - \frac{f(x_k)}{f'(x_k)}
$$

Near a root the number of correct digits roughly **doubles** every step (**quadratic
convergence**).

**Try it: ride the tangents.** Starting from the guess 4 for √2, press *Next step*
repeatedly and watch the correct-digits chip: 0, 0, 0 while the guess is still far away,
then 2 → 4 → 9 → 15 once it is close — doubling. Change the first guess; then solve
cos x = x, which has no formula at all.

<div class="lab" data-viz="math-newton"></div>

> **Notebook example:** Find $\sqrt{10}$ with Newton's method, starting from the guess 3.
>
> **What you need:** Newton's method solves an equation $f(x) = 0$ by repeating
> $x_{\text{new}} = x - \frac{f(x)}{f'(x)}$: follow the tangent line from your guess down
> to where it hits zero, and use that as the next guess. $\sqrt{10}$ is the positive
> number whose square is 10, so it solves $x^2 - 10 = 0$.
>
> **Plan:** build the update rule for $f(x) = x^2 - 10$, simplify it, then apply it
> three times starting from 3.
>
> 1. **Choose the equation.** $f(x) = x^2 - 10$. Its zero is $\sqrt{10}$.
> 2. **Find the derivative.** $f'(x) = 2x$ (power rule; the constant −10 has slope 0).
> 3. **Put both into Newton's rule.** $x_{\text{new}} = x - \frac{x^2 - 10}{2x}$.
> 4. **Split the fraction.** $\frac{x^2 - 10}{2x} = \frac{x^2}{2x} - \frac{10}{2x} = \frac{x}{2} - \frac{5}{x}$.
> 5. **Subtract it from x.** $x - \left(\frac{x}{2} - \frac{5}{x}\right) = x - \frac{x}{2} + \frac{5}{x}$.
>    *Why:* taking away a "minus 5/x" is the same as adding 5/x.
> 6. **Tidy up.** $x - \frac{x}{2} = \frac{x}{2}$, so the rule is
>    $x_{\text{new}} = \frac{x}{2} + \frac{5}{x} = \frac12\left(x + \frac{10}{x}\right)$.
>    *Why:* this is "average x and 10/x". If x is too big, 10/x is too small, so their
>    average lands in between, closer to the truth.
> 7. **Divide 10 by the first guess.** $\frac{10}{3} = 3.3333$.
> 8. **Average the two.** $\frac{3 + 3.3333}{2} = \frac{6.3333}{2} = 3.1667$. That is
>    the second guess.
> 9. **Repeat from 3.1667.** Divide: $\frac{10}{3.1667} = 3.1579$. Average:
>    $\frac{3.1667 + 3.1579}{2} = 3.1622807$ (keeping more digits).
> 10. **Repeat from 3.1622807.** Divide: $\frac{10}{3.1622807} = 3.1622746$. Average:
>     $\frac{3.1622807 + 3.1622746}{2} = 3.1622777$.
> 11. **Count the correct digits.** The true value is $3.16227766\ldots$. The guesses
>     match it in 1 digit (3), then 3 (3.16), then 5 (3.1622), then 12.
>     *Why:* near the answer, Newton's error is roughly squared each step, so the number
>     of correct digits roughly doubles.
>
> **Answer:** $\sqrt{10} \approx 3.1622777$ after three steps. The correct digits went
> 1, 3, 5, 12, roughly doubling each time: **quadratic convergence**.
>
> **Check:** square the answer: $3.1622777^2 \approx 10.0000$. ✓ And `math.sqrt(10)`
> prints 3.1622776601683795.

> **Your turn:** Find $\sqrt{5}$ with Newton's method, starting from 2. Do two updates.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Build the update rule.** For $f(x) = x^2 - 5$ the same steps give
>    $x_{\text{new}} = \frac12\left(x + \frac{5}{x}\right)$.
> 2. **First update from 2.** $\frac{5}{2} = 2.5$. Average: $\frac{2 + 2.5}{2} = 2.25$.
> 3. **Second update from 2.25.** $\frac{5}{2.25} = 2.2222$. Average:
>    $\frac{2.25 + 2.2222}{2} = 2.2361$.
> 4. **Compare with the true value.** $\sqrt{5} = 2.236068\ldots$, and
>    $2.236111 - 2.236068 = 0.000043$.
>
> **Answer:** $\sqrt{5} \approx 2.2361$ after just two updates, already within 0.00005.
>
> </details>

For $\sqrt{a}$, $f(x) = x^2 - a$ gives $x \leftarrow \frac{1}{2}\left(x + \frac{a}{x}\right)$ —
the Babylonian method. Python's `math.isqrt` uses the integer version of the same
iteration.

```python
import math

def newton_sqrt(a, x=1.0, steps=6):
    trail = []
    for _ in range(steps):
        x = (x + a / x) / 2
        trail.append(x)
    return trail

print([f"{v:.12f}" for v in newton_sqrt(2)][:5])   # → ['1.500000000000', '1.416666666667', '1.414215686275', '1.414213562375', '1.414213562373']
print(math.isqrt(10**30 + 12345), math.isqrt(10**30 + 12345) ** 2 <= 10**30 + 12345)   # → 1000000000000000 True
```

## Common Mistakes

1. **Using degrees in trig derivatives.** $\frac{d}{dx}\sin x = \cos x$ only in radians.
2. **Forgetting the inner derivative** in the chain rule.
3. **Too small an h** in numerical derivatives (cancellation) or too large (bias).
4. **A learning rate larger than the curvature allows** — gradient descent diverges.
5. **Assuming f′ = 0 means a minimum** — it may be a maximum or a saddle point.
6. **Trusting a Taylor approximation far from its centre.**
7. **Taking `rate()` over a window shorter than the scrape interval** — the difference
   quotient has too few samples to mean anything.

## Check Yourself

**1.** A counter reads 12,000 at 10:00:00 and 15,600 at 10:01:00. What does `rate()`
compute, and what is it the derivative of?

<details>
<summary>Open the answer</summary>

$(15600 - 12000) / 60\,\text{s} = 60$ requests per second: the average slope (a secant)
of the counter over the window, approximating the derivative of "total requests" with
respect to time.

</details>

**2.** Differentiate $f(x) = x^2 e^{3x}$.

<details>
<summary>Open the answer</summary>

Product and chain rules: $f'(x) = 2x e^{3x} + x^2 \cdot 3e^{3x} = e^{3x}(3x^2 + 2x)$.

</details>

**3.** Why does gradient descent zig-zag in a long, narrow valley?

<details>
<summary>Open the answer</summary>

The gradient points across the valley (the steep direction) more than along it. A step
size small enough to be stable in the steep direction is tiny in the shallow one, so the
path bounces between the walls while creeping forward. Momentum averages out the
bouncing; adaptive methods (Adam) rescale each direction.

</details>

**4.** Using $1 - x \approx e^{-x}$, estimate $(1 - 1/1000)^{1000}$.

<details>
<summary>Open the answer</summary>

$(e^{-1/1000})^{1000} = e^{-1} \approx 0.368$. (The exact value is 0.3677.)

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Derivative as slope/rate and integral as area/total; the speedometer–odometer link; basic rules; e as natural growth |
| **Interview-ready** | Chain rule and why backprop is efficient; gradient descent and learning-rate stability; finding optima with f′ = 0 (square-root laws); numerical differentiation and integration with their error behaviour; Newton's method and quadratic convergence |
| **Going deeper** | Automatic differentiation (forward vs reverse mode); convexity and saddle points; Taylor series with remainder bounds; multivariable integrals and probability densities; numerical stability |

## Checklist

- [ ] I can explain a derivative as the limit of secant slopes, and relate `rate()` to it.
- [ ] I can apply the power, product and chain rules, and check a result numerically.
- [ ] I can find the optimum of a simple trade-off and recognise the square-root law.
- [ ] I can run gradient descent and explain what the learning rate does.
- [ ] I can explain backpropagation as the chain rule in reverse topological order.
- [ ] I can estimate an integral with the trapezoid rule and state the fundamental theorem.
- [ ] I know the first-order Taylor approximations and where they come from.
- [ ] I can implement Newton's method for square roots.
