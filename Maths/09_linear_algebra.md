# Linear Algebra — Vectors, Matrices and the Transformations They Encode

Linear algebra is the maths of arrays of numbers that behave like arrows. It runs
graphics (every rotation and projection on screen), machine learning (every neural
network layer is a matrix multiplication; every embedding is a vector), search and
recommendations (similarity is a dot product), PageRank (an eigenvector), compression
(the SVD) and scientific computing (solving systems of equations). This chapter builds
intuition first — a vector is an arrow, a matrix is a way of moving space — and then
the computations: dot products, matrix multiplication, determinants, solving systems,
eigenvectors, and the SVD.

**Where this fits:** Part 3 · Continuous maths, chapter 9 of 15. **Builds on:** [08 Graph theory](08_graph_theory.md) (graphs as matrices). **Used again in:** 12. **Next in order:** [10 Probability](10_probability.md).

## Where You Will Use This

| Where | Linear algebra inside |
|---|---|
| Semantic search, recommendations, RAG | Embeddings are vectors; relevance is cosine similarity |
| Neural networks | A layer computes $W x + b$; training is calculus on matrices |
| Graphics, games, robotics | Rotations, scaling, projection: 2×2, 3×3, 4×4 matrices |
| PageRank, Markov chains | The dominant eigenvector of a link matrix |
| Compression, denoising, recommendation | SVD / PCA: keep the most important directions |
| Simulation, curve fitting, least squares | Solving $A x = b$ |

## Foundations — Two Ways to See a Vector

A **vector** is, at the same time:

- **an arrow** — a length and a direction, like "3 steps east and 1 step north";
- **a list of numbers** — `[3, 1]`, its coordinates.

The arrow view gives intuition; the list view gives computation. Linear algebra is the
dictionary between them.

> **Analogy:** A smoothie recipe is a vector: (bananas, strawberries, yoghurt) =
> (2, 5, 1). Doubling the recipe is **scaling** the vector; combining two recipes is
> **adding** them. A shopping list for several smoothies is a **linear combination** —
> which is all a matrix–vector product is.

Vectors can have any number of components. A 2-D vector is an arrow in the plane; a
768-dimensional sentence embedding is an arrow in a space you cannot picture, but every
rule in this chapter still applies to it.

## 1 · Vector Operations

| Operation | Definition | Picture |
|---|---|---|
| Addition | $(a_1 + b_1, a_2 + b_2)$ | put b's tail on a's tip |
| Scaling | $c\,a = (c\,a_1, c\,a_2)$ | stretch (or flip if c < 0) |
| Linear combination | $c_1 v_1 + c_2 v_2 + \dots$ | any mix of scaled arrows |
| Length (L2 norm) | $\lVert a \rVert = \sqrt{a_1^2 + a_2^2 + \dots}$ | Pythagoras |
| Unit vector | $a / \lVert a \rVert$ | same direction, length 1 |

```python
import math

def add(a, b): return [x + y for x, y in zip(a, b)]
def scale(c, a): return [c * x for x in a]
def norm(a): return math.sqrt(sum(x * x for x in a))

a, b = [3, 1], [1, 2]
print(add(a, b), scale(2, a), norm([3, 4]))   # → [4, 3] [6, 2] 5.0
```

> **Notebook example:** Let $a = (3, 4)$ and $b = (1, -2)$. Find $a + b$, $2a - b$,
> $\lVert a \rVert$, the unit vector of a, and the distance from a to b.
>
> 1. $a + b = (3 + 1,\ 4 - 2) = (4, 2)$.
> 2. $2a - b = (6 - 1,\ 8 + 2) = (5, 10)$.
> 3. $\lVert a \rVert = \sqrt{3^2 + 4^2} = \sqrt{25} = 5$.
> 4. Unit vector: $a / 5 = (0.6, 0.8)$. Check its length:
>    $\sqrt{0.36 + 0.64} = 1$ ✓.
> 5. Distance: $a - b = (2, 6)$, so $\sqrt{4 + 36} = \sqrt{40} \approx 6.32$.
>
> **Answer:** $(4, 2)$, $(5, 10)$, 5, $(0.6, 0.8)$ and about 6.32. For comparison, the
> L1 (taxicab) length of a is $3 + 4 = 7$ and its L∞ length is 4.

"Length" is not the only distance. The **L1 norm** $\sum \lvert a_i \rvert$ is the
taxicab distance (walking a street grid); **L∞** is the largest single coordinate. ML
uses L2 for most distances and L1 when it wants sparsity (lasso regularisation).

<div class="lab" data-viz="norms"></div>

## 2 · The Dot Product: How Much Two Vectors Agree

$$
a \cdot b = a_1 b_1 + a_2 b_2 + \dots + a_n b_n = \lVert a \rVert \, \lVert b \rVert \cos\theta
$$

The first formula computes it; the second explains it. θ is the angle between the
arrows, so the dot product measures **alignment**:

- positive: pointing roughly the same way;
- zero: perpendicular (**orthogonal**) — nothing in common;
- negative: pointing apart.

Divide by both lengths and you get **cosine similarity**, $\cos\theta$, between −1 and 1
— the standard measure of "how similar are these two embeddings", independent of their
lengths.

> **Worked example:** Two users rate (action, comedy, drama): Ana (5, 1, 0), Bo
> (4, 0, 1), Cy (0, 5, 4). Ana and Bo point the same way (both love action); Cy points
> elsewhere. Cosine similarity says so in one number each.

```python
import math

def dot(a, b): return sum(x * y for x, y in zip(a, b))
def cosine(a, b): return dot(a, b) / (math.sqrt(dot(a, a)) * math.sqrt(dot(b, b)))

ana, bo, cy = [5, 1, 0], [4, 0, 1], [0, 5, 4]
print(round(cosine(ana, bo), 3), round(cosine(ana, cy), 3))   # → 0.951 0.153
print(dot([1, 0], [0, 1]))                                     # → 0
```

**Projection.** The **shadow** of b on a has length $\frac{a \cdot b}{\lVert a \rVert}$:
how far b goes in a's direction. Projections decompose a vector into "the part along a
direction" plus "the rest" — the basis of least squares and PCA.

**Try it: feel the angle.** Drag the tips of a and b. The band on a is b's shadow; watch
the dot product and cosine change as the angle opens, cross zero at 90°, and turn
negative. The presets show that scaling a vector (a more "active" user) changes the dot
product but not the cosine.

<div class="lab" data-viz="vectors"></div>

## 3 · A Matrix Is a Transformation

A matrix is a grid of numbers. The most useful way to read it:

> **Key idea:** **The columns of a matrix are where the basis arrows land.** In 2-D,
> $\hat{\imath} = (1, 0)$ and $\hat{\jmath} = (0, 1)$. The matrix
> $\begin{pmatrix} a & b \\ c & d \end{pmatrix}$ sends $\hat{\imath}$ to $(a, c)$ and
> $\hat{\jmath}$ to $(b, d)$. Every other vector goes along for the ride, because
> $(x, y) = x\hat{\imath} + y\hat{\jmath}$ lands on $x \cdot (a, c) + y \cdot (b, d)$.

That is the whole definition of matrix–vector multiplication: **a linear combination of
the columns**, weighted by the vector's entries.

$$
\begin{pmatrix} a & b \\ c & d \end{pmatrix}\begin{pmatrix} x \\ y \end{pmatrix} = x\begin{pmatrix} a \\ c \end{pmatrix} + y\begin{pmatrix} b \\ d \end{pmatrix} = \begin{pmatrix} ax + by \\ cx + dy \end{pmatrix}
$$

**Try it: move space with your hands.** Drag the tips of î and ĵ and watch the whole
grid, the unit square and the letter F follow. Then try the presets: *rotate 45°*,
*shear*, *reflect* (the F is mirrored — the determinant turns negative), and
*squash (det 0)*, which flattens the plane onto a line.

<div class="lab" data-viz="math-transform"></div>

"Linear" means the transformation keeps grid lines straight, parallel and evenly spaced,
and keeps the origin fixed. Rotations, scalings, shears, reflections and projections are
all linear; translations (sliding everything over) are not — which is why graphics uses
4×4 matrices with an extra coordinate to fold translation in ("homogeneous coordinates").

```python
import math

def mat_vec(M, v):
    return [sum(M[i][j] * v[j] for j in range(len(v))) for i in range(len(M))]

t = math.radians(90)
rot90 = [[math.cos(t), -math.sin(t)], [math.sin(t), math.cos(t)]]
print([round(x, 10) for x in mat_vec(rot90, [1, 0])])   # → [0.0, 1.0]
shear = [[1, 1], [0, 1]]
print(mat_vec(shear, [0, 1]), mat_vec(shear, [2, 3]))    # → [1, 1] [5, 3]
```

> **Notebook example:** Where does $M = \begin{pmatrix} 2 & 1 \\ 0 & 1 \end{pmatrix}$
> send $v = (3, 2)$? Do it the column way, then check it the row way.
>
> 1. Read the columns: î lands on $(2, 0)$ and ĵ lands on $(1, 1)$.
> 2. $v = 3\hat{\imath} + 2\hat{\jmath}$, so it lands on
>    $3(2, 0) + 2(1, 1) = (6, 0) + (2, 2) = (8, 2)$.
> 3. **Check** the row way: top row $2 \cdot 3 + 1 \cdot 2 = 8$ and bottom row
>    $0 \cdot 3 + 1 \cdot 2 = 2$. ✓
>
> **Answer:** $(8, 2)$. The column view says *what the matrix does* (here, a shear that
> also stretches x). The row view is just the fastest way to compute it.

## 4 · Matrix Multiplication Is Composition

Doing transformation B and then A is itself a linear transformation, and its matrix is
the product $AB$ (read right to left, like function composition $A(B(x))$). The rule
"row of A times column of B" is just computing where AB sends each basis vector.

$$
(AB)_{ij} = \sum_{k} A_{ik} B_{kj}
$$

Two consequences that surprise people:

- **Order matters:** $AB \ne BA$ in general. Rotating then shearing is not shearing then
  rotating.
- **Cost:** multiplying two $n \times n$ matrices by the definition takes $n^3$
  multiplications. (Strassen-style algorithms beat the exponent 3 in theory; GPUs
  exist largely to do the $n^3$ version very fast.)

```python
def mat_mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(len(B))) for j in range(len(B[0]))] for i in range(len(A))]

R = [[0, -1], [1, 0]]          # rotate 90°
S = [[1, 1], [0, 1]]           # shear
print(mat_mul(R, S), mat_mul(S, R))   # → [[0, -1], [1, 1]] [[1, -1], [1, 0]]
```

Multiplication *is* associative — $(AB)C = A(BC)$ — but the cost is not the same both
ways. For shapes (10×1000)(1000×1000)(1000×1), multiplying the right pair first costs
about $10^6 + 10^4$ operations; the left pair first, $10^7 + 10^4$. Choosing the order is
a classic DP problem (matrix-chain multiplication), and ML frameworks do it for you.

> **Notebook example:** Multiply $R = \begin{pmatrix} 0 & -1 \\ 1 & 0 \end{pmatrix}$
> (rotate 90°) and $S = \begin{pmatrix} 1 & 1 \\ 0 & 1 \end{pmatrix}$ (shear) in both
> orders.
>
> 1. $RS$: each entry is a row of R times a column of S. Row 1: $(0 \cdot 1 + (-1) \cdot 0,\ 0 \cdot 1 + (-1) \cdot 1) = (0, -1)$.
>    Row 2: $(1 \cdot 1 + 0 \cdot 0,\ 1 \cdot 1 + 0 \cdot 1) = (1, 1)$.
> 2. $RS = \begin{pmatrix} 0 & -1 \\ 1 & 1 \end{pmatrix}$, which means shear first,
>    then rotate.
> 3. $SR$: row 1 $(1 \cdot 0 + 1 \cdot 1,\ 1 \cdot (-1) + 1 \cdot 0) = (1, -1)$ and
>    row 2 $(0 + 1,\ 0 + 0) = (1, 0)$.
> 4. $SR = \begin{pmatrix} 1 & -1 \\ 1 & 0 \end{pmatrix}$, which means rotate first,
>    then shear.
>
> **Answer:** $RS \ne SR$. **Check** with one vector: $RS$ sends î to $(0, 1)$, the
> first column. Shearing î leaves it at $(1, 0)$, and rotating that gives $(0, 1)$. ✓

## 5 · The Determinant: How Much Area Is Scaled

> **Definition:** The **determinant** of a square matrix is the factor by which it
> scales areas (in 3-D, volumes). Its sign says whether orientation is kept (+) or
> flipped (−).
> $$\det\begin{pmatrix} a & b \\ c & d \end{pmatrix} = ad - bc$$

In the lab, the shaded parallelogram (the image of the unit square) has area $\lvert ad - bc \rvert$.

- $\det = 2$: every shape doubles in area.
- $\det < 0$: the plane is flipped (a mirror image — watch the F).
- $\det = 0$: the plane is squashed onto a line or a point. Information is destroyed —
  many inputs land on the same output — so the transformation **cannot be undone**.

That last bullet connects to chapter 04: a transformation is invertible exactly when it
is a bijection, and for square matrices that is exactly when $\det \ne 0$. The same
$ad - bc$ reappears in chapter 15 as the 2-D cross product, a 2×2 determinant in disguise.

> **Notebook example:** Find the determinants of $\begin{pmatrix} 3 & 1 \\ 2 & 4 \end{pmatrix}$
> and $\begin{pmatrix} 2 & 4 \\ 1 & 2 \end{pmatrix}$, and say what each one does to
> area.
>
> 1. $ad - bc = 3 \cdot 4 - 1 \cdot 2 = 12 - 2 = 10$. The unit square becomes a
>    parallelogram of area 10, and the orientation is kept (positive).
> 2. $2 \cdot 2 - 4 \cdot 1 = 0$. The columns $(2, 1)$ and $(4, 2)$ point the same way
>    (the second is twice the first), so the whole plane is squashed onto one line.
> 3. So the first matrix can be undone and the second cannot: many points land on the
>    same place, like $(2, 0)$ and $(0, 1)$, which both go to $(4, 2)$.
>
> **Answer:** 10 (area × 10, invertible) and 0 (flattened, not invertible).

## 6 · Solving Systems of Equations

Three equations in three unknowns is one matrix equation $A x = b$:

$$
\begin{aligned} 2x + y - z &= 8 \\ -3x - y + 2z &= -11 \\ -2x + y + 2z &= -3 \end{aligned}
\qquad\Longleftrightarrow\qquad
\begin{pmatrix} 2 & 1 & -1 \\ -3 & -1 & 2 \\ -2 & 1 & 2 \end{pmatrix}\begin{pmatrix} x \\ y \\ z \end{pmatrix} = \begin{pmatrix} 8 \\ -11 \\ -3 \end{pmatrix}
$$

Read it with the column picture: *which combination of the three columns of A produces
b?* **Gaussian elimination** answers by subtracting multiples of rows to create zeros
below the diagonal, then solving from the bottom up.

**Try it: eliminate step by step.** Step through the three systems. The first ends with
a unique solution (x, y, z) = (2, 3, −1). In the second a row becomes 0 = 1:
contradictory equations, no solution. In the third a row becomes 0 = 0: one equation
was redundant, leaving a free variable and infinitely many solutions.

<div class="lab" data-viz="math-gauss"></div>

```python
from fractions import Fraction

def solve(A, b):
    n = len(A)
    M = [[Fraction(x) for x in row] + [Fraction(bi)] for row, bi in zip(A, b)]
    for col in range(n):
        piv = next(r for r in range(col, n) if M[r][col] != 0)   # assumes a unique solution
        M[col], M[piv] = M[piv], M[col]
        for r in range(col + 1, n):
            f = M[r][col] / M[col][col]
            M[r] = [x - f * y for x, y in zip(M[r], M[col])]
    x = [Fraction(0)] * n
    for r in range(n - 1, -1, -1):
        x[r] = (M[r][n] - sum(M[r][k] * x[k] for k in range(r + 1, n))) / M[r][r]
    return x

print([str(v) for v in solve([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]], [8, -11, -3])])   # → ['2', '3', '-1']
```

> **Notebook example:** Solve the system above by hand with elimination.
>
> 1. Rows as $[\,x\ y\ z \mid \text{rhs}\,]$: $R_1 = [2,\ 1,\ -1 \mid 8]$,
>    $R_2 = [-3,\ -1,\ 2 \mid -11]$, $R_3 = [-2,\ 1,\ 2 \mid -3]$.
> 2. Clear x below the first pivot: $R_2 \leftarrow R_2 + \tfrac32 R_1 = [0,\ \tfrac12,\ \tfrac12 \mid 1]$
>    and $R_3 \leftarrow R_3 + R_1 = [0,\ 2,\ 1 \mid 5]$.
> 3. Clear y below the second pivot: $R_3 \leftarrow R_3 - 4R_2 = [0,\ 0,\ -1 \mid 1]$.
> 4. Solve from the bottom up: $-z = 1$, so $z = -1$.
> 5. $R_2$: $\tfrac12 y + \tfrac12(-1) = 1$, so $y = 3$.
> 6. $R_1$: $2x + 3 - (-1) = 8$, so $x = 2$.
>
> **Answer:** $(x, y, z) = (2, 3, -1)$. **Check** in equation 3:
> $-2(2) + 3 + 2(-1) = -3$. ✓

> **In practice:** Libraries never compute $A^{-1}$ to solve $Ax = b$; they factor A
> (LU, QR, Cholesky) and solve directly, which is faster and more accurate. Elimination
> costs about $n^3/3$ operations. Sparse systems (most real ones: circuits, finite
> elements, graphs) use iterative methods that exploit the zeros.

The three outcomes — one, none, infinitely many — are governed by the **rank**: the
number of independent rows (pivots). Full rank ($\det \ne 0$ for square A): exactly one
solution.

## 7 · Independence, Span, Basis and Rank

- Vectors are **linearly independent** if none is a combination of the others. In the
  lab, î and ĵ are independent unless one lies along the other (det 0).
- The **span** of some vectors is everything you can build from them by linear
  combinations. Two independent vectors in 2-D span the whole plane.
- A **basis** is an independent set that spans the space. Its size is the space's
  **dimension**.
- The **rank** of a matrix is the dimension of the space its columns span — how many
  genuinely different directions its output has.

> **Intuition:** Rank is "how much information survives". A 1000 × 1000 matrix of
> user–movie ratings might have rank close to 20 in practice: most taste is explained by
> a handful of hidden factors (genre, era, mood). That low rank is exactly what
> recommender systems exploit (§9).

> **Notebook example:** Are $u = (1, 2, 3)$, $v = (2, 0, 1)$ and $w = (4, 4, 7)$
> independent? What is the rank of the matrix with these columns?
>
> 1. Try to build w from u and v: $w = a\,u + b\,v$.
> 2. Second coordinate: $2a + 0b = 4$, so $a = 2$.
> 3. First coordinate: $a + 2b = 4$, so $2 + 2b = 4$ and $b = 1$.
> 4. Third coordinate as a check: $3a + b = 6 + 1 = 7$. ✓ It matches.
> 5. So $w = 2u + v$: w adds no new direction.
>
> **Answer:** dependent. u and v are independent (neither is a multiple of the other),
> so the rank is 2. The three vectors span only a plane in 3-D, and the determinant of
> the 3×3 matrix is 0.

## 8 · Eigenvectors and Eigenvalues

Most vectors get knocked off their direction by a transformation. A few do not.

> **Definition:** A non-zero vector v is an **eigenvector** of A with **eigenvalue** λ
> if $A v = \lambda v$: A only stretches v by the factor λ, without turning it.

In the transformation lab, the dashed green lines are the eigenvector directions, labelled
with their λ. For $\begin{pmatrix} 2 & 1 \\ 1 & 2 \end{pmatrix}$ (*stretch*), the direction
(1, 1) is stretched by 3 and (1, −1) by 1. A rotation has **no** real eigenvectors: every
direction turns.

For a 2×2 matrix the eigenvalues solve the **characteristic equation**
$\det(A - \lambda I) = 0$, i.e. $\lambda^2 - (a + d)\lambda + (ad - bc) = 0$: the sum of
the eigenvalues is the **trace** $a + d$ and their product is the **determinant**.

### Power iteration: finding the biggest eigenvector by repetition

Multiply any starting vector by A again and again (normalising as you go). The
component along the eigenvector with the largest $\lvert\lambda\rvert$ grows fastest and
takes over. This is how PageRank is computed:

> **Worked example: PageRank.** Model the web as a random surfer who follows a random
> link from each page (and occasionally jumps anywhere). The long-run fraction of time
> spent on each page is its rank. Those fractions are the vector r with $r = M r$ — an
> eigenvector with eigenvalue 1 of the link matrix — found by power iteration.

**Try it: rank five pages two ways.** Press *One iteration* a few times, then *Play*:
the ranks settle as the vector converges. Then switch on the *random surfer* and let it
wander: its visit counts (outlined bars) converge to the same values. Lower the damping
d and the ranks even out, because random jumps matter more than links.

<div class="lab" data-viz="math-pagerank"></div>

```python
def power_iteration(M, steps=100):
    n = len(M)
    v = [1.0] * n
    for _ in range(steps):
        w = [sum(M[i][j] * v[j] for j in range(n)) for i in range(n)]
        s = max(abs(x) for x in w)
        v = [x / s for x in w]
    lam = sum(M[0][j] * v[j] for j in range(n)) / v[0]
    return lam, v

lam, v = power_iteration([[2, 1], [1, 2]])
print(round(lam, 6), [round(x, 6) for x in v])   # → 3.0 [1.0, 1.0]
```

Eigenvectors also give the long-run behaviour of any **Markov chain** (a system hopping
between states with fixed probabilities — weather models, queueing, page navigation):
the stationary distribution is the eigenvector with eigenvalue 1.

## 9 · SVD and PCA: the Most Important Directions

The **singular value decomposition** says that *every* matrix — any shape, any rank —
is a rotation, then a stretch along the axes, then another rotation:

$$
A = U \Sigma V^{\top}
$$

The stretch factors on the diagonal of Σ are the **singular values**, sorted from
largest to smallest. Keeping only the top k of them gives the **best possible rank-k
approximation** of A (the Eckart–Young theorem). That single fact powers:

- **Compression:** an image stored as its top 20 singular triples instead of every
  pixel.
- **Recommendations:** approximate the huge, mostly-empty ratings matrix by a low-rank
  one; the missing entries it fills in are predictions (the Netflix-prize family of
  methods).
- **Latent semantic analysis, denoising, and PCA.**

**Try it: rebuild an image from its top k layers.** Slide k up from 1: a handful of
singular values already carries the recognisable picture; the rest is detail and noise.

<div class="lab" data-viz="svd"></div>

**PCA** (principal component analysis) applies this to a data table: centre the data,
and the top singular vectors are the directions of greatest variance. Projecting onto
the first few reduces 100 features to the few that matter.

<div class="lab" data-viz="pca"></div>

> **Notebook example:** Run PCA by hand on four centred points: $(3, 3)$, $(-3, -3)$,
> $(1, -1)$, $(-1, 1)$.
>
> 1. **Variances** (dividing by n = 4): $\text{var}(x) = \frac{9 + 9 + 1 + 1}{4} = 5$,
>    and likewise $\text{var}(y) = 5$.
> 2. **Covariance:** $\frac{3 \cdot 3 + (-3)(-3) + 1 \cdot (-1) + (-1) \cdot 1}{4} = \frac{16}{4} = 4$.
> 3. Covariance matrix $C = \begin{pmatrix} 5 & 4 \\ 4 & 5 \end{pmatrix}$.
> 4. Guess eigenvectors from the symmetry: $C(1, 1) = (9, 9) = 9 \cdot (1, 1)$ and
>    $C(1, -1) = (1, -1) = 1 \cdot (1, -1)$.
> 5. The first component is the direction $(1, 1)/\sqrt2$, with variance 9. The second
>    is $(1, -1)/\sqrt2$, with variance 1.
>
> **Answer:** the diagonal carries $\frac{9}{9 + 1} = 90\%$ of the variance, so keeping
> 1 of 2 dimensions loses only 10%. The point $(3, 3)$ becomes the single number
> $\frac{3 + 3}{\sqrt 2} \approx 4.24$.

## 10 · Doing It for Real: NumPy

The pure-Python functions in this chapter exist to show the arithmetic. In practice,
use NumPy, which runs these loops in optimised C and BLAS libraries — typically tens to
hundreds of times faster than Python loops.

```python
# no-run — NumPy equivalents (install numpy to try)
import numpy as np
a, b = np.array([5, 1, 0]), np.array([4, 0, 1])
a @ b                                   # dot product
np.linalg.norm(a)                       # length
A = np.array([[2, 1, -1], [-3, -1, 2], [-2, 1, 2]])
np.linalg.solve(A, [8, -11, -3])        # array([ 2.,  3., -1.])
np.linalg.det(A)                        # determinant
np.linalg.eig(np.array([[2, 1], [1, 2]]))   # eigenvalues and eigenvectors
U, S, Vt = np.linalg.svd(A)             # singular value decomposition
```

## Common Mistakes

1. **Assuming $AB = BA$.** Order of transformations matters.
2. **Shape mismatches:** an $m \times n$ matrix times an $n \times p$ matrix gives
   $m \times p$; the inner dimensions must agree.
3. **Computing an inverse to solve a system.** Solve directly.
4. **Comparing embeddings by raw dot product** when their lengths differ for irrelevant
   reasons — normalise, or use cosine similarity.
5. **Expecting real eigenvectors from every matrix** (rotations have none).
6. **Floating-point singularity:** a determinant of `1e-17` is "zero" for practical
   purposes; ill-conditioned systems amplify tiny errors.

## Check Yourself

**1.** What does $\begin{pmatrix} 0 & 1 \\ 1 & 0 \end{pmatrix}$ do to the plane? Its
determinant? Its eigenvectors?

<details>
<summary>Open the answer</summary>

It swaps x and y: a reflection across the line y = x. Determinant $0 - 1 = -1$ (area
kept, orientation flipped). Eigenvectors: (1, 1) with λ = 1 (on the mirror, unchanged)
and (1, −1) with λ = −1 (flipped).

</details>

**2.** Two unit-length embeddings have dot product 0.92. What is their cosine
similarity, and their Euclidean distance?

<details>
<summary>Open the answer</summary>

For unit vectors the cosine is the dot product: 0.92. Distance:
$\lVert a - b \rVert^2 = \lVert a \rVert^2 + \lVert b \rVert^2 - 2\,a\cdot b = 2 - 1.84 = 0.16$,
so the distance is 0.4. On normalised vectors, ranking by cosine and by distance give the
same order — why vector databases can use either.

</details>

**3.** Why does a 3×3 matrix with two equal rows have no inverse?

<details>
<summary>Open the answer</summary>

Its rows are dependent, so its rank is at most 2 and its determinant is 0: it squashes
3-D space onto a plane (or less), so different inputs collide and cannot be recovered.

</details>

**4.** Why does power iteration converge to the eigenvector with the largest
$\lvert\lambda\rvert$?

<details>
<summary>Open the answer</summary>

Write the start vector as a combination of eigenvectors $\sum c_i v_i$. After k
multiplications it is $\sum c_i \lambda_i^k v_i$. The term with the largest
$\lvert\lambda_i\rvert$ grows fastest and dominates after normalising (as long as its
$c_i \ne 0$). The speed depends on the ratio of the top two eigenvalues.

</details>

## What Each Level Should Know

| Level | Expected |
|---|---|
| **Getting started** | Vectors as arrows and lists; addition, scaling, length; dot product and cosine similarity; matrix × vector as a combination of columns |
| **Interview-ready** | Matrices as transformations; multiplication as composition and why it is not commutative; determinant as area scale and invertibility; solving $Ax = b$ and its three outcomes; eigenvectors and power iteration (PageRank); cost of matrix operations |
| **Going deeper** | Rank, basis and change of basis; SVD and low-rank approximation; PCA; conditioning and numerical stability; homogeneous coordinates |

## Checklist

- [ ] I can compute and interpret a dot product and cosine similarity.
- [ ] I can read a 2×2 matrix as "where î and ĵ go" and sketch what it does.
- [ ] I know matrix multiplication is composition, costs $O(n^3)$, and is not commutative.
- [ ] I can explain the determinant geometrically, including sign and zero.
- [ ] I can solve a small system by elimination and recognise no/unique/infinite solutions.
- [ ] I can explain eigenvectors, power iteration and PageRank in plain words.
- [ ] I can explain what the SVD gives you and why low rank is useful.
