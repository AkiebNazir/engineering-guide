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

> **Notebook example:** Find $\lim_{x \to 3} \frac{x^2 - 9}{x - 3}$.
>
> 1. Substituting gives $\frac{0}{0}$, which tells you nothing, so you need another
>    route.
> 2. Factor the top: $x^2 - 9 = (x - 3)(x + 3)$.
> 3. For $x \ne 3$, cancel: $\frac{(x - 3)(x + 3)}{x - 3} = x + 3$.
> 4. As x approaches 3, $x + 3$ approaches **6**.
> 5. **Check** with a table: $x = 2.9$ gives 5.9, $x = 2.99$ gives 5.99, and $x = 3.01$
>    gives 6.01. It closes in on 6 from both sides. ✓
>
> **Answer:** 6, although the function itself is undefined at $x = 3$.

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

> **Notebook example:** Use the definition to find the slope of $f(x) = x^2$ at $x = 3$.
>
> 1. Difference quotient: $\frac{(3 + h)^2 - 3^2}{h}$.
> 2. Expand: $(3 + h)^2 = 9 + 6h + h^2$, so the top is $6h + h^2$.
> 3. Divide by h: $6 + h$.
> 4. Let $h \to 0$: the slope is **6**.
> 5. Watch the secant close in: $h = 1$ gives 7, $h = 0.1$ gives 6.1, and $h = 0.01$
>    gives 6.01.
>
> **Answer:** $f'(3) = 6$. That matches the rule $\frac{d}{dx}x^2 = 2x = 6$.

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

> **Notebook example:** For $f(x, y) = x^2 + xy + 2y^2$, find the gradient at (2, 1) and
> take one gradient-descent step with η = 0.1.
>
> 1. $\frac{\partial f}{\partial x}$, holding y fixed: $2x + y = 2 \cdot 2 + 1 = 5$.
> 2. $\frac{\partial f}{\partial y}$, holding x fixed: $x + 4y = 2 + 4 = 6$.
> 3. $\nabla f(2, 1) = (5, 6)$. That is uphill, so step against it.
> 4. New point: $(2, 1) - 0.1 \times (5, 6) = (1.5, 0.4)$.
> 5. **Check** that it went downhill: $f(2, 1) = 4 + 2 + 2 = 8$, and
>    $f(1.5, 0.4) = 2.25 + 0.6 + 0.32 = 3.17$. ✓
>
> **Answer:** gradient $(5, 6)$, new point $(1.5, 0.4)$, and the loss fell from 8 to 3.17.

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

> **Notebook example:** A one-weight model: $L = (w x + b - y)^2$ with $w = 2$, $x = 3$,
> $b = 1$ and $y = 5$. Find $\frac{\partial L}{\partial w}$ and $\frac{\partial L}{\partial b}$
> by backpropagation.
>
> 1. **Forward**, saving every intermediate: $z = w x + b = 7$, then $e = z - y = 2$, then
>    $L = e^2 = 4$.
> 2. **Backward**, starting from $\frac{\partial L}{\partial L} = 1$:
>    $\frac{\partial L}{\partial e} = 2e = 4$.
> 3. $e = z - y$, so the local slope is 1: $\frac{\partial L}{\partial z} = 4 \times 1 = 4$.
> 4. $z = w x + b$: the local slope for w is x = 3, so
>    $\frac{\partial L}{\partial w} = 4 \times 3 = 12$. The local slope for b is 1, so
>    $\frac{\partial L}{\partial b} = 4$.
> 5. **Check numerically:** with $w = 2.001$, $z = 7.003$, $e = 2.003$ and
>    $L = 4.012009$. The slope is $\frac{0.012009}{0.001} \approx 12.0$. ✓
>
> **Answer:** 12 and 4. Every step is "upstream gradient × local slope", done in reverse
> order.

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

> **Notebook example:** Estimate $\int_0^2 x^2\,dx$ with 4 strips, then find it exactly.
>
> 1. The strip width is $\frac{2 - 0}{4} = 0.5$.
> 2. **Left** edges 0, 0.5, 1 and 1.5 give heights 0, 0.25, 1 and 2.25, which sum to 3.5.
>    Times 0.5, that is **1.75**.
> 3. **Right** edges 0.5, 1, 1.5 and 2 give 0.25, 1, 2.25 and 4, which sum to 7.5. Times
>    0.5, that is **3.75**.
> 4. **Midpoints** 0.25, 0.75, 1.25 and 1.75 give 0.0625, 0.5625, 1.5625 and 3.0625,
>    which sum to 5.25. Times 0.5, that is **2.625**.
> 5. **Exact:** an antiderivative of $x^2$ is $\frac{x^3}{3}$, so
>    $\frac{8}{3} - 0 = 2.667$.
>
> **Answer:** $\frac83 \approx 2.667$. The midpoint rule is off by only 0.04, while the
> left and right sums miss by about 0.9 and 1.1: same work, much better answer.

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
> 1. The rule is new = old + α × (sample − old).
> 2. Spike: $100 + 0.2 \times (400 - 100) = 160$.
> 3. Next, a 100: $160 + 0.2 \times (100 - 160) = 148$.
> 4. Then $148 - 0.2 \times 48 = 138.4$, then $138.4 - 0.2 \times 38.4 = 130.72$.
> 5. Look at the excess over 100: 60, 48, 38.4, 30.72. Each is 0.8 times the one before.
>
> **Answer:** 160, 148, 138.4, 130.72. The spike's effect decays by a factor
> $(1 - \alpha) = 0.8$ per sample, like $e^{-kt}$: exponential forgetting.

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
> 1. $e^x \approx 1 + x + \frac{x^2}{2} + \frac{x^3}{6}$.
> 2. $x = 0.1$: the terms are $1$, $0.1$, $\frac{0.01}{2} = 0.005$ and
>    $\frac{0.001}{6} \approx 0.000167$.
> 3. Their sum is $1.105167$.
> 4. The true value is $e^{0.1} = 1.105171$, so the error is about 0.000004. That is
>    roughly the next term, $\frac{0.0001}{24}$.
>
> **Answer:** 1.10517, correct to 5 decimal places from four terms. Just $1 + x = 1.1$
> is already within 0.5%, and that is the approximation behind the rule of 70.

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

> **Notebook example:** Find $\sqrt{10}$ with Newton's method, starting from 3.
>
> 1. For $f(x) = x^2 - 10$ the update is $x \leftarrow \frac12\left(x + \frac{10}{x}\right)$.
> 2. $x_1 = \frac12(3 + 3.3333) = 3.1667$.
> 3. $x_2 = \frac12(3.1667 + 3.1579) = 3.1622807$.
> 4. $x_3 = \frac12(3.1622807 + 3.1622746) = 3.1622777$.
>
> **Answer:** $\sqrt{10} = 3.16227766\ldots$. Count the correct digits: 1 (3), then 3
> (3.16), then 5 (3.1622), then 12. They roughly double each step, which is quadratic
> convergence.

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
