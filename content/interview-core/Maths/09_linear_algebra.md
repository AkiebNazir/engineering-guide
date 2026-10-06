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

> **Notebook example:** Let $a = (3, 4)$ and $b = (1, -2)$. Find $a + b$ and $2a - b$.
>
> **What you need:** a 2-D vector is a pair of numbers (first coordinate, second
> coordinate). Vectors are added **coordinate by coordinate**: first with first, second
> with second. Scaling by a number c (written $c\,a$) multiplies **each** coordinate by c.
> Subtracting works like adding, coordinate by coordinate. It is the list comprehension
> `[x + y for x, y in zip(a, b)]`.
>
> **Plan:** handle the first coordinates and the second coordinates separately, one small
> sum at a time.
>
> 1. **Add the first coordinates.** $3 + 1 = 4$.
> 2. **Add the second coordinates.** $4 + (-2) = 4 - 2 = 2$. So $a + b = (4, 2)$.
>    *Why:* each coordinate only ever meets the matching coordinate of the other vector.
> 3. **Scale a by 2.** $2 \cdot 3 = 6$ and $2 \cdot 4 = 8$, so $2a = (6, 8)$.
>    *Why:* $2a$ is the same arrow made twice as long.
> 4. **Subtract the first coordinates.** $6 - 1 = 5$.
> 5. **Subtract the second coordinates.** $8 - (-2) = 8 + 2 = 10$. So $2a - b = (5, 10)$.
>    *Why:* taking away a negative number is the same as adding it.
>
> **Answer:** $a + b = (4, 2)$ and $2a - b = (5, 10)$. In arrow terms: walk along a, then
> along b, and you end up 4 right and 2 up.
>
> **Check:** `add([3, 4], [1, -2])` from the code above prints `[4, 2]`. ✓ And
> $(5, 10) + b = (5 + 1, 10 - 2) = (6, 8) = 2a$, so adding b back undoes the subtraction. ✓

> **Your turn:** Let $c = (1, 2)$ and $d = (3, -1)$. Find $c + d$ and $3c - d$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Add the first coordinates.** $1 + 3 = 4$.
> 2. **Add the second coordinates.** $2 + (-1) = 1$. So $c + d = (4, 1)$.
> 3. **Scale c by 3.** $3 \cdot 1 = 3$ and $3 \cdot 2 = 6$, so $3c = (3, 6)$.
> 4. **Subtract the first coordinates.** $3 - 3 = 0$.
> 5. **Subtract the second coordinates.** $6 - (-1) = 6 + 1 = 7$. So $3c - d = (0, 7)$.
>
> **Answer:** $c + d = (4, 1)$ and $3c - d = (0, 7)$.
>
> </details>

> **Notebook example:** Let $a = (3, 4)$. Find its length $\lVert a \rVert$ and its unit
> vector.
>
> **What you need:** the **length** (or L2 norm) of $(a_1, a_2)$ is
> $\lVert a \rVert = \sqrt{a_1^2 + a_2^2}$. It is Pythagoras: the arrow is the long side
> of a right-angled triangle whose other sides are $a_1$ and $a_2$. A **unit vector** is
> an arrow of length exactly 1 pointing the same way; you get it by dividing every
> coordinate by the length.
>
> **Plan:** square the coordinates, add, take the square root; then divide a by that
> length.
>
> 1. **Square each coordinate.** $3^2 = 9$ and $4^2 = 16$.
> 2. **Add the squares.** $9 + 16 = 25$.
> 3. **Take the square root.** $\sqrt{25} = 5$. So $\lVert a \rVert = 5$.
>    *Why:* the triangle has sides 3 and 4, so its long side is 5 (the classic 3-4-5
>    triangle).
> 4. **Divide each coordinate by the length.** $3 / 5 = 0.6$ and $4 / 5 = 0.8$, so the
>    unit vector is $(0.6, 0.8)$.
>    *Why:* shrinking both coordinates by the same factor keeps the direction and makes
>    the length $5 / 5 = 1$.
>
> **Answer:** $\lVert a \rVert = 5$ and the unit vector is $(0.6, 0.8)$: same direction
> as a, length 1. Other ways to measure size: the L1 (taxicab) length is
> $3 + 4 = 7$ and the L∞ length (biggest coordinate) is 4.
>
> **Check:** the unit vector should have length 1: $0.6^2 = 0.36$, $0.8^2 = 0.64$,
> $0.36 + 0.64 = 1$, and $\sqrt{1} = 1$. ✓ `norm([3, 4])` above prints 5.0. ✓

> **Your turn:** Find the length and the unit vector of $(8, 6)$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Square each coordinate.** $8^2 = 64$ and $6^2 = 36$.
> 2. **Add the squares.** $64 + 36 = 100$.
> 3. **Take the square root.** $\sqrt{100} = 10$.
> 4. **Divide each coordinate by the length.** $8 / 10 = 0.8$ and $6 / 10 = 0.6$.
>
> **Answer:** length 10, unit vector $(0.8, 0.6)$.
>
> </details>

> **Notebook example:** Let $a = (3, 4)$ and $b = (1, -2)$. How far is the tip of a from
> the tip of b?
>
> **What you need:** the **distance** between two points is the length of the arrow that
> joins them, $\lVert a - b \rVert$. So: subtract coordinate by coordinate, then use the
> length rule $\sqrt{x^2 + y^2}$.
>
> **Plan:** build the joining arrow $a - b$, then measure its length.
>
> 1. **Subtract the first coordinates.** $3 - 1 = 2$.
> 2. **Subtract the second coordinates.** $4 - (-2) = 4 + 2 = 6$. So $a - b = (2, 6)$.
>    *Why:* $a - b$ is the arrow you walk to get from b's tip to a's tip.
> 3. **Square each coordinate.** $2^2 = 4$ and $6^2 = 36$.
> 4. **Add the squares.** $4 + 36 = 40$.
> 5. **Take the square root.** $\sqrt{40} \approx 6.32$.
>    *Why:* 40 is between $6^2 = 36$ and $7^2 = 49$, a bit nearer 36, so the answer is a
>    bit over 6.
>
> **Answer:** about 6.32. This "straight-line" distance is what a nearest-neighbour search
> over embeddings computes.
>
> **Check:** measuring the other way round gives the same distance: $b - a = (-2, -6)$,
> and $(-2)^2 + (-6)^2 = 4 + 36 = 40$ again. ✓ In Python, `norm([2, 6])` prints 6.324… ✓

> **Your turn:** How far is the point $(4, 5)$ from the point $(1, 1)$?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Subtract the first coordinates.** $4 - 1 = 3$.
> 2. **Subtract the second coordinates.** $5 - 1 = 4$. The joining arrow is $(3, 4)$.
> 3. **Square each coordinate.** $3^2 = 9$ and $4^2 = 16$.
> 4. **Add the squares.** $9 + 16 = 25$.
> 5. **Take the square root.** $\sqrt{25} = 5$.
>
> **Answer:** the distance is exactly 5.
>
> </details>

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
> **What you need:** î is the arrow $(1, 0)$ ("one step right") and ĵ is $(0, 1)$ ("one
> step up"). A 2×2 matrix's **first column is where î lands** and its **second column
> is where ĵ lands**. Any vector $(x, y)$ means "x lots of î plus y lots of ĵ", so it
> lands on "x lots of column 1 plus y lots of column 2".
>
> **Plan:** read off the two columns, scale each by the matching entry of v, and add.
>
> 1. **Read column 1.** It is $(2, 0)$, so î lands on $(2, 0)$.
> 2. **Read column 2.** It is $(1, 1)$, so ĵ lands on $(1, 1)$.
> 3. **Split v into basis arrows.** $v = (3, 2) = 3\hat{\imath} + 2\hat{\jmath}$: three
>    steps right and two steps up.
> 4. **Scale column 1 by 3.** $3 \cdot (2, 0) = (6, 0)$.
>    *Why:* three lots of î must land on three lots of where î lands.
> 5. **Scale column 2 by 2.** $2 \cdot (1, 1) = (2, 2)$.
> 6. **Add the two results.** $(6 + 2,\ 0 + 2) = (8, 2)$.
>    *Why:* the matrix keeps sums as sums, so "3 î plus 2 ĵ" lands on "where 3 î lands
>    plus where 2 ĵ lands".
>
> **Answer:** $Mv = (8, 2)$. The column view says *what the matrix does* (here, a shear
> that also stretches x). The row view below is just the fastest way to compute it.
>
> **Check:** the row way multiplies each row of M by v and adds. Top row:
> $2 \cdot 3 + 1 \cdot 2 = 6 + 2 = 8$. Bottom row: $0 \cdot 3 + 1 \cdot 2 = 0 + 2 = 2$.
> Same $(8, 2)$. ✓ This row way is exactly the `mat_vec` loop above.

> **Your turn:** Where does $\begin{pmatrix} 1 & 0 \\ 2 & 1 \end{pmatrix}$ send
> $(2, 3)$? Use the column way.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Read column 1.** î lands on $(1, 2)$.
> 2. **Read column 2.** ĵ lands on $(0, 1)$.
> 3. **Split the vector into basis arrows.** $(2, 3) = 2\hat{\imath} + 3\hat{\jmath}$.
> 4. **Scale column 1 by 2.** $2 \cdot (1, 2) = (2, 4)$.
> 5. **Scale column 2 by 3.** $3 \cdot (0, 1) = (0, 3)$.
> 6. **Add the two results.** $(2 + 0,\ 4 + 3) = (2, 7)$.
>
> **Answer:** $(2, 7)$. Row check: $1 \cdot 2 + 0 \cdot 3 = 2$ and $2 \cdot 2 + 1 \cdot 3 = 7$.
>
> </details>

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
> (rotate 90°) by $S = \begin{pmatrix} 1 & 1 \\ 0 & 1 \end{pmatrix}$ (shear): find
> $RS$.
>
> **What you need:** the entry of $RS$ in row i, column j is **row i of R "times"
> column j of S**: multiply the two first numbers, multiply the two second numbers, and
> add. (That is a dot product, §2.) A 2×2 answer has four entries, so this is four small
> sums. $RS$ means "do S first, then R", like the nested call `R(S(x))`.
>
> **Plan:** write out the rows of R and the columns of S, then fill in the answer one
> entry at a time.
>
> 1. **List the rows of R.** Row 1 is $(0, -1)$; row 2 is $(1, 0)$.
> 2. **List the columns of S.** Column 1 is $(1, 0)$; column 2 is $(1, 1)$.
> 3. **Entry row 1, column 1.** Row 1 of R with column 1 of S:
>    $0 \cdot 1 + (-1) \cdot 0 = 0 + 0 = 0$.
> 4. **Entry row 1, column 2.** Row 1 of R with column 2 of S:
>    $0 \cdot 1 + (-1) \cdot 1 = 0 - 1 = -1$.
> 5. **Entry row 2, column 1.** Row 2 of R with column 1 of S:
>    $1 \cdot 1 + 0 \cdot 0 = 1 + 0 = 1$.
> 6. **Entry row 2, column 2.** Row 2 of R with column 2 of S:
>    $1 \cdot 1 + 0 \cdot 1 = 1 + 0 = 1$.
> 7. **Put the four entries in their places.**
>    $RS = \begin{pmatrix} 0 & -1 \\ 1 & 1 \end{pmatrix}$.
>
> **Answer:** $RS = \begin{pmatrix} 0 & -1 \\ 1 & 1 \end{pmatrix}$: the single matrix
> that shears and then rotates.
>
> **Check:** follow î through the two moves. S sends î to its first column, $(1, 0)$, so
> the shear leaves î alone. R then sends $(1, 0)$ to its first column, $(0, 1)$. The first
> column of $RS$ is also $(0, 1)$. ✓ `mat_mul(R, S)` above prints the same matrix. ✓

> **Your turn:** Find $AB$ for $A = \begin{pmatrix} 1 & 2 \\ 0 & 1 \end{pmatrix}$ and
> $B = \begin{pmatrix} 1 & 0 \\ 3 & 1 \end{pmatrix}$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **List the rows of A.** Row 1 is $(1, 2)$; row 2 is $(0, 1)$.
> 2. **List the columns of B.** Column 1 is $(1, 3)$; column 2 is $(0, 1)$.
> 3. **Entry row 1, column 1.** $1 \cdot 1 + 2 \cdot 3 = 1 + 6 = 7$.
> 4. **Entry row 1, column 2.** $1 \cdot 0 + 2 \cdot 1 = 0 + 2 = 2$.
> 5. **Entry row 2, column 1.** $0 \cdot 1 + 1 \cdot 3 = 0 + 3 = 3$.
> 6. **Entry row 2, column 2.** $0 \cdot 0 + 1 \cdot 1 = 0 + 1 = 1$.
>
> **Answer:** $AB = \begin{pmatrix} 7 & 2 \\ 3 & 1 \end{pmatrix}$.
>
> </details>

> **Notebook example:** Now multiply the same two matrices the other way round: find
> $SR$, and compare it with $RS = \begin{pmatrix} 0 & -1 \\ 1 & 1 \end{pmatrix}$.
>
> **What you need:** the same rule: entry (row i, column j) of $SR$ is row i of S times
> column j of R. $SR$ means "do R first, then S" (`S(R(x))`), so it is a different
> sequence of moves and may give a different matrix. Two matrices are equal only if
> **every** entry matches.
>
> **Plan:** list the rows of S and columns of R, fill in four entries, then compare entry
> by entry.
>
> 1. **List the rows of S.** Row 1 is $(1, 1)$; row 2 is $(0, 1)$.
> 2. **List the columns of R.** Column 1 is $(0, 1)$; column 2 is $(-1, 0)$.
> 3. **Entry row 1, column 1.** $1 \cdot 0 + 1 \cdot 1 = 0 + 1 = 1$.
> 4. **Entry row 1, column 2.** $1 \cdot (-1) + 1 \cdot 0 = -1 + 0 = -1$.
> 5. **Entry row 2, column 1.** $0 \cdot 0 + 1 \cdot 1 = 0 + 1 = 1$.
> 6. **Entry row 2, column 2.** $0 \cdot (-1) + 1 \cdot 0 = 0 + 0 = 0$.
> 7. **Put the four entries in their places.**
>    $SR = \begin{pmatrix} 1 & -1 \\ 1 & 0 \end{pmatrix}$.
> 8. **Compare with RS.** The top-left entries already differ: 1 in $SR$, 0 in $RS$.
>    *Why:* one mismatched entry is enough to show the matrices are different.
>
> **Answer:** $SR = \begin{pmatrix} 1 & -1 \\ 1 & 0 \end{pmatrix} \ne RS$. Rotating then
> shearing is not shearing then rotating: **order matters**.
>
> **Check:** follow î. R sends î to its first column, $(0, 1)$. S then sends $(0, 1)$
> (which is ĵ) to its second column, $(1, 1)$. The first column of $SR$ is $(1, 1)$. ✓
> `mat_mul(S, R)` above prints `[[1, -1], [1, 0]]`. ✓

> **Your turn:** With $A = \begin{pmatrix} 1 & 2 \\ 0 & 1 \end{pmatrix}$ and
> $B = \begin{pmatrix} 1 & 0 \\ 3 & 1 \end{pmatrix}$, find $BA$ and compare it with
> $AB = \begin{pmatrix} 7 & 2 \\ 3 & 1 \end{pmatrix}$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **List the rows of B.** Row 1 is $(1, 0)$; row 2 is $(3, 1)$.
> 2. **List the columns of A.** Column 1 is $(1, 0)$; column 2 is $(2, 1)$.
> 3. **Entry row 1, column 1.** $1 \cdot 1 + 0 \cdot 0 = 1$.
> 4. **Entry row 1, column 2.** $1 \cdot 2 + 0 \cdot 1 = 2$.
> 5. **Entry row 2, column 1.** $3 \cdot 1 + 1 \cdot 0 = 3$.
> 6. **Entry row 2, column 2.** $3 \cdot 2 + 1 \cdot 1 = 6 + 1 = 7$.
> 7. **Compare with AB.** Top-left is 1 here but 7 in $AB$.
>
> **Answer:** $BA = \begin{pmatrix} 1 & 2 \\ 3 & 7 \end{pmatrix} \ne AB$.
>
> </details>

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

> **Notebook example:** Find the determinant of
> $\begin{pmatrix} 3 & 1 \\ 2 & 4 \end{pmatrix}$ and say what the matrix does to area.
>
> **What you need:** for $\begin{pmatrix} a & b \\ c & d \end{pmatrix}$ the determinant
> is $ad - bc$: "top-left times bottom-right, minus top-right times bottom-left". Its
> size is the factor that areas get multiplied by; a **positive** sign means shapes keep
> their orientation, a **negative** sign means they come out mirrored. A non-zero
> determinant means the move can be undone (the matrix is **invertible**).
>
> **Plan:** label a, b, c, d, do the two products, subtract, then read off the meaning.
>
> 1. **Label the entries.** $a = 3$, $b = 1$ (top row); $c = 2$, $d = 4$ (bottom row).
> 2. **Multiply down the main diagonal.** $a \cdot d = 3 \cdot 4 = 12$.
> 3. **Multiply the other diagonal.** $b \cdot c = 1 \cdot 2 = 2$.
> 4. **Subtract.** $12 - 2 = 10$.
> 5. **Read the size.** 10 means every area is multiplied by 10: the unit square (area 1)
>    becomes a parallelogram of area 10.
> 6. **Read the sign.** 10 is positive, so the orientation is kept (no mirror image).
>    *Why:* only a negative determinant flips the picture over.
>
> **Answer:** $\det = 10$: areas grow 10×, nothing is flipped, and since 10 ≠ 0 the
> transformation can be undone.
>
> **Check:** the unit square lands on the parallelogram with sides along the columns
> $(3, 2)$ and $(1, 4)$. Put it in a 4-by-6 box (area 24) and cut off the two
> 3-by-2 triangles (area 3 each), the two 1-by-4 triangles (area 2 each) and the two
> 1-by-2 corner rectangles (area 2 each): $24 - 6 - 4 - 4 = 10$. ✓

> **Your turn:** Find the determinant of $\begin{pmatrix} 1 & 2 \\ 3 & 4 \end{pmatrix}$
> and say what it does to area.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Label the entries.** $a = 1$, $b = 2$, $c = 3$, $d = 4$.
> 2. **Multiply down the main diagonal.** $1 \cdot 4 = 4$.
> 3. **Multiply the other diagonal.** $2 \cdot 3 = 6$.
> 4. **Subtract.** $4 - 6 = -2$.
> 5. **Read the size and sign.** Areas double; the minus sign means the plane is flipped
>    into its mirror image.
>
> **Answer:** $\det = -2$: area × 2, mirrored, still invertible.
>
> </details>

> **Notebook example:** Find the determinant of
> $\begin{pmatrix} 2 & 4 \\ 1 & 2 \end{pmatrix}$, and show that this matrix cannot be
> undone.
>
> **What you need:** the same rule, $\det = ad - bc$. A determinant of **0** means every
> area becomes 0: the whole plane is squashed flat onto a line (or a point). Once two
> different inputs land on the same output, there is no way to tell which one you started
> from, so the move **cannot be undone** (the matrix is not invertible).
>
> **Plan:** compute $ad - bc$; then explain the 0 by looking at the columns, and find two
> inputs that collide.
>
> 1. **Multiply down the main diagonal.** $a \cdot d = 2 \cdot 2 = 4$.
> 2. **Multiply the other diagonal.** $b \cdot c = 4 \cdot 1 = 4$.
> 3. **Subtract.** $4 - 4 = 0$.
> 4. **Compare the columns.** Column 1 is $(2, 1)$ and column 2 is $(4, 2)$, which is
>    exactly $2 \cdot (2, 1)$.
>    *Why:* î and ĵ both land on the same line through $(2, 1)$, so everything built from
>    them lands on that line too. That is the "squashed flat" picture.
> 5. **Send $(2, 0)$ through.** It is 2 lots of î, so it lands on $2 \cdot (2, 1) = (4, 2)$.
> 6. **Send $(0, 1)$ through.** It is ĵ, so it lands on column 2, $(4, 2)$.
>
> **Answer:** $\det = 0$. Two different points, $(2, 0)$ and $(0, 1)$, both land on
> $(4, 2)$, so from the output alone you cannot recover the input: no inverse.
>
> **Check:** the row way for $(2, 0)$: $2 \cdot 2 + 4 \cdot 0 = 4$ and
> $1 \cdot 2 + 2 \cdot 0 = 2$, giving $(4, 2)$. For $(0, 1)$: $2 \cdot 0 + 4 \cdot 1 = 4$
> and $1 \cdot 0 + 2 \cdot 1 = 2$, giving $(4, 2)$. ✓

> **Your turn:** Find the determinant of $\begin{pmatrix} 3 & 6 \\ 1 & 2 \end{pmatrix}$
> and find two different points it sends to the same place.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Multiply down the main diagonal.** $3 \cdot 2 = 6$.
> 2. **Multiply the other diagonal.** $6 \cdot 1 = 6$.
> 3. **Subtract.** $6 - 6 = 0$.
> 4. **Compare the columns.** $(6, 2) = 2 \cdot (3, 1)$, so both columns lie on one line.
> 5. **Send $(2, 0)$ through.** $2 \cdot (3, 1) = (6, 2)$.
> 6. **Send $(0, 1)$ through.** It lands on column 2, $(6, 2)$.
>
> **Answer:** $\det = 0$; $(2, 0)$ and $(0, 1)$ both land on $(6, 2)$, so it cannot be
> undone.
>
> </details>

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

> **Notebook example:** Warm-up: solve $x + y = 5$ and $2x + 3y = 13$ by elimination.
>
> **What you need:** you may replace an equation by "itself minus a multiple of another
> equation" without changing the answer, because you are subtracting equal amounts from
> both sides. **Elimination** uses this to make a variable disappear (its number, the
> **coefficient**, becomes 0). Then the last equation has one unknown, and you solve
> upwards, putting each value you find into the equation above (**back substitution**).
>
> **Plan:** use equation 1 to remove x from equation 2, solve for y, then put y back into
> equation 1.
>
> 1. **Write the two rows.** $R_1$: $x + y = 5$. $R_2$: $2x + 3y = 13$.
> 2. **Choose the multiplier.** $R_2$ has $2x$ and $R_1$ has $1x$, so subtract
>    $2 \times R_1$.
>    *Why:* $2x - 2 \cdot x = 0$, which is exactly what makes x vanish.
> 3. **Double $R_1$.** $2 \times (x + y = 5)$ is $2x + 2y = 10$.
> 4. **Subtract it from $R_2$.** $(2x - 2x) + (3y - 2y) = 13 - 10$, which is $y = 3$.
> 5. **Put $y = 3$ into $R_1$.** $x + 3 = 5$.
> 6. **Solve for x.** $x = 5 - 3 = 2$.
>
> **Answer:** $x = 2$, $y = 3$: the one point where both lines cross.
>
> **Check:** equation 2 with these values: $2 \cdot 2 + 3 \cdot 3 = 4 + 9 = 13$. ✓

> **Your turn:** Solve $x + y = 4$ and $3x + y = 10$ by elimination.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the two rows.** $R_1$: $x + y = 4$. $R_2$: $3x + y = 10$.
> 2. **Choose the multiplier.** $R_2$ has $3x$, so subtract $3 \times R_1$.
> 3. **Triple $R_1$.** $3x + 3y = 12$.
> 4. **Subtract it from $R_2$.** $(3x - 3x) + (y - 3y) = 10 - 12$, which is $-2y = -2$, so
>    $y = 1$.
> 5. **Put $y = 1$ into $R_1$.** $x + 1 = 4$, so $x = 3$.
>
> **Answer:** $x = 3$, $y = 1$ (check: $3 \cdot 3 + 1 = 10$).
>
> </details>

> **Notebook example:** Solve the 3×3 system above by hand with elimination.
>
> **What you need:** write each equation as a row of its coefficients and right-hand side
> (rhs), $[\,x\ y\ z \mid \text{rhs}\,]$. The only move is **"replace a row by itself plus
> a multiple of another row"**; it never changes the solution. A **pivot** is the
> number you use to clear the entries below it: first the x-number in $R_1$, then the
> y-number in $R_2$. Goal: zeros below the pivots (a staircase shape), then back
> substitution from the bottom row up.
>
> **Plan:** clear x from rows 2 and 3, then clear y from row 3, then solve z, y, x in
> that order.
>
> 1. **Write the rows.** $R_1 = [2,\ 1,\ -1 \mid 8]$, $R_2 = [-3,\ -1,\ 2 \mid -11]$,
>    $R_3 = [-2,\ 1,\ 2 \mid -3]$.
> 2. **Choose the multiplier for $R_2$.** The pivot is 2 and $R_2$ starts with $-3$. We
>    need $-3 + 2m = 0$, so $m = \tfrac32$: add $\tfrac32 R_1$ to $R_2$.
> 3. **Scale $R_1$ by $\tfrac32$.** $\tfrac32 \cdot [2,\ 1,\ -1 \mid 8] = [3,\ \tfrac32,\ -\tfrac32 \mid 12]$.
> 4. **Add it to $R_2$.** $[-3 + 3,\ -1 + \tfrac32,\ 2 - \tfrac32 \mid -11 + 12] = [0,\ \tfrac12,\ \tfrac12 \mid 1]$.
>    This is the new $R_2$.
> 5. **Add $R_1$ to $R_3$.** $R_3$ starts with $-2$ and the pivot is 2, so the multiplier
>    is just 1: $[-2 + 2,\ 1 + 1,\ 2 - 1 \mid -3 + 8] = [0,\ 2,\ 1 \mid 5]$.
>    *Why:* x is now gone from both lower rows; only $R_1$ still mentions x.
> 6. **Choose the multiplier for the new $R_3$.** The new pivot is the $\tfrac12$ in $R_2$,
>    and $R_3$ has 2 in that column. $2 - 4 \cdot \tfrac12 = 0$, so subtract $4R_2$.
> 7. **Scale $R_2$ by 4.** $4 \cdot [0,\ \tfrac12,\ \tfrac12 \mid 1] = [0,\ 2,\ 2 \mid 4]$.
> 8. **Subtract it from $R_3$.** $[0 - 0,\ 2 - 2,\ 1 - 2 \mid 5 - 4] = [0,\ 0,\ -1 \mid 1]$.
>    *Why:* the bottom row now has only z left in it.
> 9. **Solve the bottom row for z.** It says $-z = 1$, so $z = -1$.
> 10. **Put z into $R_2$.** $\tfrac12 y + \tfrac12 \cdot (-1) = 1$, which is
>     $\tfrac12 y - \tfrac12 = 1$.
> 11. **Solve for y.** Add $\tfrac12$: $\tfrac12 y = \tfrac32$. Double: $y = 3$.
> 12. **Put y and z into $R_1$.** $2x + 3 - (-1) = 8$, which is $2x + 4 = 8$.
> 13. **Solve for x.** $2x = 8 - 4 = 4$, so $x = 2$.
>
> **Answer:** $(x, y, z) = (2, 3, -1)$: the only combination of A's columns that makes b.
>
> **Check:** put all three values into the original equation 3:
> $-2 \cdot 2 + 3 + 2 \cdot (-1) = -4 + 3 - 2 = -3$. ✓ The `solve` function above prints
> `['2', '3', '-1']`. ✓

> **Your turn:** Solve $x + y + z = 6$, $2x + 3y + z = 11$, $x + 2y + 3z = 14$ by
> elimination.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the rows.** $R_1 = [1,\ 1,\ 1 \mid 6]$, $R_2 = [2,\ 3,\ 1 \mid 11]$,
>    $R_3 = [1,\ 2,\ 3 \mid 14]$.
> 2. **Subtract $2R_1$ from $R_2$.** $2R_1 = [2,\ 2,\ 2 \mid 12]$, so the new
>    $R_2 = [0,\ 1,\ -1 \mid -1]$.
> 3. **Subtract $R_1$ from $R_3$.** New $R_3 = [0,\ 1,\ 2 \mid 8]$.
> 4. **Subtract $R_2$ from $R_3$.** New $R_3 = [0,\ 0,\ 3 \mid 9]$.
> 5. **Solve the bottom row for z.** $3z = 9$, so $z = 3$.
> 6. **Put z into $R_2$.** $y - 3 = -1$, so $y = 2$.
> 7. **Put y and z into $R_1$.** $x + 2 + 3 = 6$, so $x = 1$.
>
> **Answer:** $(x, y, z) = (1, 2, 3)$.
>
> </details>

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
> **What you need:** a **linear combination** of u and v is $a\,u + b\,v$ for some
> numbers a and b ("a lots of u plus b lots of v"). Vectors are **dependent** if one of
> them is a linear combination of the others (it adds no new direction), and
> **independent** if none is. The **rank** is the number of genuinely different
> directions: the size of the largest independent group.
>
> **Plan:** try to find numbers a and b with $w = a\,u + b\,v$, one coordinate at a time.
> If they exist, w is redundant.
>
> 1. **Write the goal coordinate by coordinate.** $a(1, 2, 3) + b(2, 0, 1) = (4, 4, 7)$
>    gives three equations: first $a + 2b = 4$, second $2a + 0b = 4$, third $3a + b = 7$.
> 2. **Use the easiest equation first.** The second has no b in it: $2a = 4$, so $a = 2$.
>    *Why:* the 0 in v's second coordinate means b cannot affect it.
> 3. **Put $a = 2$ into the first equation.** $2 + 2b = 4$.
> 4. **Solve for b.** $2b = 4 - 2 = 2$, so $b = 1$.
> 5. **Test the third equation.** $3a + b = 3 \cdot 2 + 1 = 6 + 1 = 7$. ✓ It matches.
>    *Why:* a and b were chosen to fit two equations; the third is the real test. If it
>    had failed, no combination would work and w would be independent.
> 6. **Conclude.** $w = 2u + v$, so w adds no new direction: the three are dependent.
> 7. **Check u and v on their own.** v is not a multiple of u: to turn u's first
>    coordinate 1 into 2 you would multiply by 2, but that turns u's second coordinate 2
>    into 4, not 0.
> 8. **Count the directions.** u and v give two independent directions; w adds none. So
>    the rank is 2.
>
> **Answer:** dependent, since $w = 2u + v$, and the rank is 2. The three vectors span
> only a flat plane inside 3-D space, so the 3×3 matrix with these columns has
> determinant 0.
>
> **Check:** build $2u + v$ directly: $2u = (2, 4, 6)$, and
> $(2 + 2,\ 4 + 0,\ 6 + 1) = (4, 4, 7) = w$. ✓

> **Your turn:** Are $u = (1, 0, 1)$, $v = (0, 1, 1)$ and $w = (2, 3, 5)$ independent?
> What is the rank?
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Write the goal coordinate by coordinate.** First $a = 2$, second $b = 3$, third
>    $a + b = 5$.
> 2. **Use the easiest equations first.** The first two give $a = 2$ and $b = 3$ straight
>    away.
> 3. **Test the third equation.** $2 + 3 = 5$. ✓
> 4. **Conclude.** $w = 2u + 3v$, so the three are dependent.
> 5. **Count the directions.** u and v are not multiples of each other (u has a 0 where v
>    has a 1), so the rank is 2.
>
> **Answer:** dependent ($w = 2u + 3v$); rank 2.
>
> </details>

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

PCA by hand takes three small jobs: measure the spread (the covariance matrix), find the
directions of greatest spread (its eigenvectors), and squash each point onto the best
direction (a projection). The next three examples do one job each on the same four
points.

> **Notebook example:** Four data points are $(3, 3)$, $(-3, -3)$, $(1, -1)$ and
> $(-1, 1)$. Find their covariance matrix.
>
> **What you need:** the points are **centred**: their average is $(0, 0)$ (the x's add
> to 0 and so do the y's). **Variance** measures spread: the average of the squared
> distances from the centre. With the centre at 0 it is just the average of $x^2$ (for
> x) or $y^2$ (for y). **Covariance** measures whether x and y move together: the average
> of $x \cdot y$. Positive means "when x is big, y tends to be big too"; negative means
> the opposite; 0 means no straight-line link. The **covariance matrix** collects them:
> $C = \begin{pmatrix} \text{var}(x) & \text{cov}(x, y) \\ \text{cov}(x, y) & \text{var}(y) \end{pmatrix}$.
> Here we divide by n = 4.
>
> **Plan:** compute three averages (of $x^2$, of $y^2$, of $x \cdot y$) and put them in
> the matrix.
>
> 1. **Square each x.** The x's are 3, −3, 1, −1, so the squares are 9, 9, 1, 1.
> 2. **Average them.** $9 + 9 + 1 + 1 = 20$, and $20 / 4 = 5$. So $\text{var}(x) = 5$.
> 3. **Square each y.** The y's are 3, −3, −1, 1, so the squares are 9, 9, 1, 1.
> 4. **Average them.** $20 / 4 = 5$. So $\text{var}(y) = 5$.
> 5. **Multiply x by y for each point.** $3 \cdot 3 = 9$, $(-3)(-3) = 9$,
>    $1 \cdot (-1) = -1$, $(-1) \cdot 1 = -1$.
> 6. **Average the products.** $9 + 9 - 1 - 1 = 16$, and $16 / 4 = 4$. So
>    $\text{cov}(x, y) = 4$.
>    *Why:* the two big points agree in sign (big products, +9 each) and the two small
>    points disagree (−1 each); the big ones win, so x and y mostly rise together.
> 7. **Fill in the matrix.** Variances on the diagonal, covariance in both other spots:
>    $C = \begin{pmatrix} 5 & 4 \\ 4 & 5 \end{pmatrix}$.
>
> **Answer:** $C = \begin{pmatrix} 5 & 4 \\ 4 & 5 \end{pmatrix}$: each coordinate has
> spread 5, and the positive 4 says the cloud leans along the up-right diagonal.
>
> **Check:** plot the points: $(3, 3)$ and $(-3, -3)$ lie far out on the line y = x,
> while $(1, -1)$ and $(-1, 1)$ sit close in on the other diagonal. A cloud stretched
> along y = x should have a large positive covariance. ✓

> **Your turn:** Find the covariance matrix of the centred points $(3, 1)$, $(-3, -1)$,
> $(1, 3)$, $(-1, -3)$ (divide by 4).
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Square each x.** 9, 9, 1, 1.
> 2. **Average them.** $20 / 4 = 5$, so $\text{var}(x) = 5$.
> 3. **Square each y.** 1, 1, 9, 9, which also average to $20 / 4 = 5$.
> 4. **Multiply x by y for each point.** $3$, $3$, $3$, $3$.
> 5. **Average the products.** $12 / 4 = 3$, so $\text{cov}(x, y) = 3$.
> 6. **Fill in the matrix.** $\begin{pmatrix} 5 & 3 \\ 3 & 5 \end{pmatrix}$.
>
> **Answer:** $C = \begin{pmatrix} 5 & 3 \\ 3 & 5 \end{pmatrix}$.
>
> </details>

> **Notebook example:** Find the principal components of
> $C = \begin{pmatrix} 5 & 4 \\ 4 & 5 \end{pmatrix}$ (the covariance matrix just found),
> and how much of the spread the first one carries.
>
> **What you need:** an **eigenvector** of C is a direction that C only stretches,
> without turning: $C v = \lambda v$, where the number λ (the **eigenvalue**) is the
> stretch factor. To test a guess v, multiply $C v$ and see whether the answer is a
> multiple of v. For a covariance matrix the eigenvectors are the **principal
> components** (the directions the data spreads along), and each eigenvalue is the
> variance (spread) of the data in that direction. Two useful facts: the eigenvalues add
> up to the diagonal sum (the **trace**), and multiply to the determinant.
>
> **Plan:** make a sensible guess for the two directions, test each by multiplying, then
> compare the eigenvalues.
>
> 1. **Make a guess.** C does not change if you swap x and y (both variances are 5), so
>    the picture is mirror-symmetric about the line y = x. The special directions should
>    be along that mirror, $(1, 1)$, and straight across it, $(1, -1)$.
>    *Why:* a mirror-symmetric stretch cannot prefer one side of the mirror, so it
>    stretches along the mirror line and across it.
> 2. **Multiply C by $(1, 1)$.** Top row: $5 \cdot 1 + 4 \cdot 1 = 9$. Bottom row:
>    $4 \cdot 1 + 5 \cdot 1 = 9$. Result $(9, 9)$.
> 3. **Compare with $(1, 1)$.** $(9, 9) = 9 \cdot (1, 1)$: same direction, stretched 9
>    times. So $(1, 1)$ is an eigenvector with $\lambda = 9$.
> 4. **Multiply C by $(1, -1)$.** Top row: $5 \cdot 1 + 4 \cdot (-1) = 5 - 4 = 1$. Bottom
>    row: $4 \cdot 1 + 5 \cdot (-1) = 4 - 5 = -1$. Result $(1, -1)$.
> 5. **Compare with $(1, -1)$.** $(1, -1) = 1 \cdot (1, -1)$: an eigenvector with
>    $\lambda = 1$.
> 6. **Find the total spread.** $9 + 1 = 10$.
> 7. **Find the first component's share.** $9 / 10 = 90\%$.
>    *Why:* the eigenvalue is the spread in that direction, so this is the fraction of all
>    the spread that lies along $(1, 1)$.
>
> **Answer:** the first principal component is the diagonal direction $(1, 1)$, carrying
> variance 9, which is 90% of the total; the second, $(1, -1)$, carries only 1. Keeping
> one dimension out of two loses just 10% of the spread.
>
> **Check:** the eigenvalues should add up to the trace, $5 + 5 = 10$: $9 + 1 = 10$. ✓
> They should multiply to the determinant, $5 \cdot 5 - 4 \cdot 4 = 25 - 16 = 9$:
> $9 \cdot 1 = 9$. ✓ `power_iteration([[5, 4], [4, 5]])` would settle on 9 and (1, 1).

> **Your turn:** Find the principal components of
> $\begin{pmatrix} 5 & 3 \\ 3 & 5 \end{pmatrix}$ and the first one's share of the spread.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Make a guess.** The matrix is unchanged by swapping x and y, so try $(1, 1)$ and
>    $(1, -1)$.
> 2. **Multiply by $(1, 1)$.** $5 + 3 = 8$ and $3 + 5 = 8$: $(8, 8) = 8 \cdot (1, 1)$, so
>    $\lambda = 8$.
> 3. **Multiply by $(1, -1)$.** $5 - 3 = 2$ and $3 - 5 = -2$: $(2, -2) = 2 \cdot (1, -1)$,
>    so $\lambda = 2$.
> 4. **Find the total spread.** $8 + 2 = 10$ (the trace, $5 + 5$).
> 5. **Find the first component's share.** $8 / 10 = 80\%$.
>
> **Answer:** $(1, 1)$ with variance 8 (80%) and $(1, -1)$ with variance 2.
>
> </details>

> **Notebook example:** Squash the point $(3, 3)$ onto the first principal component
> $(1, 1)$ to describe it with a single number.
>
> **What you need:** to describe a point by one number along a direction, take its
> **projection** (its "shadow" on that line, §2): the dot product of the point with the
> **unit vector** of the direction. The unit vector of $(1, 1)$ is
> $\left(\frac{1}{\sqrt 2}, \frac{1}{\sqrt 2}\right)$, because $(1, 1)$ has length
> $\sqrt{1^2 + 1^2} = \sqrt 2$.
>
> **Plan:** make the direction length 1, then take the dot product with the point.
>
> 1. **Find the length of $(1, 1)$.** $\sqrt{1 + 1} = \sqrt 2 \approx 1.414$.
> 2. **Make it a unit vector.** Divide both coordinates by $\sqrt 2$:
>    $\left(\frac{1}{\sqrt 2}, \frac{1}{\sqrt 2}\right)$.
>    *Why:* with a length-1 direction, the dot product measures distance along the line
>    in the data's own units.
> 3. **Multiply matching coordinates.** $3 \cdot \frac{1}{\sqrt 2}$ and
>    $3 \cdot \frac{1}{\sqrt 2}$.
> 4. **Add them.** $\frac{3 + 3}{\sqrt 2} = \frac{6}{\sqrt 2}$.
> 5. **Divide.** $6 / 1.414 \approx 4.24$.
>
> **Answer:** the 2-D point $(3, 3)$ becomes the single number about 4.24, its position
> along the diagonal. Doing this to every point turns a 2-column table into a 1-column
> table: that is dimensionality reduction.
>
> **Check:** $(3, 3)$ already lies on the line y = x, so its shadow should be the whole
> arrow, whose length is $\sqrt{3^2 + 3^2} = \sqrt{18} \approx 4.24$. ✓

> **Your turn:** Squash the point $(3, 1)$ onto the direction $(1, 1)$.
>
> <details>
> <summary>Show the worked answer</summary>
>
> 1. **Find the length of $(1, 1)$.** $\sqrt 2 \approx 1.414$.
> 2. **Make it a unit vector.** $\left(\frac{1}{\sqrt 2}, \frac{1}{\sqrt 2}\right)$.
> 3. **Multiply matching coordinates and add.** $\frac{3 + 1}{\sqrt 2} = \frac{4}{\sqrt 2}$.
> 4. **Divide.** $4 / 1.414 \approx 2.83$.
>
> **Answer:** about 2.83.
>
> </details>

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
