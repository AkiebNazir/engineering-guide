# Day 2: Matrix Operations & Transformations

Welcome to Day 2. Yesterday we covered vectors (points/arrows in space). Today, we level up to **Matrices**. 

If vectors are the *nouns* of machine learning (data, features, embeddings), matrices are the **verbs**. A matrix is fundamentally an action—it transforms space. Every single layer of a deep neural network is just a series of matrix transformations applied to your input data. 

Let's master the mechanics of moving and morphing data.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. What is a Matrix? (Beyond a Grid of Numbers)
**Algebraic View:** A rectangular array of numbers arranged in rows and columns. An $m \times n$ matrix has $m$ rows and $n$ columns.
**Geometric View:** A matrix is a **Linear Transformation** *(a mathematical rule that moves points in space while guaranteeing that all grid lines remain perfectly straight and evenly spaced)*. It takes a vector in one space, squishes, stretches, or rotates it, and spits it out in a new space.

> **Analogy (Video Games & 3D Rendering):** 
> When you play a 3D game and your character turns around, the computer isn't calculating the physics of light hitting a camera. It is multiplying the 3D coordinates of your character (a vector) by a **Rotation Matrix**. The matrix is the *action* of turning.

### 2. Matrix-Vector Multiplication: Applying the Action
When you multiply a matrix $A$ by a vector $\mathbf{x}$, you are applying the transformation $A$ to the point $\mathbf{x}$.
$$ \mathbf{y} = A\mathbf{x} $$
Here, $A$ grabs the vector $\mathbf{x}$ and moves it to a new location $\mathbf{y}$.

> **Mathematical Example (Concrete Numbers):**
> Let's stretch the X-axis by 2, and leave the Y-axis alone. 
> Matrix $A = \begin{bmatrix} 2 & 0 \\ 0 & 1 \end{bmatrix}$. 
> Let our input vector be $\mathbf{x} = \begin{bmatrix} 3 \\ 4 \end{bmatrix}$.
> Multiplication:
> Row 1 dot $\mathbf{x}$: $(2 \times 3) + (0 \times 4) = 6$
> Row 2 dot $\mathbf{x}$: $(0 \times 3) + (1 \times 4) = 4$
> Result $\mathbf{y} = \begin{bmatrix} 6 \\ 4 \end{bmatrix}$.
> We successfully stretched the point from $X=3$ to $X=6$.
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Forward Pass):** 
> In a neural network layer, $\mathbf{x}$ is the input data (e.g., an image embedding of size 512), $A$ is the weight matrix (size $1024 \times 512$), and $\mathbf{y}$ is the output vector (size 1024). The network "learns" by adjusting the values in the matrix $A$ until it finds the perfect transformation that maps inputs to the correct output shapes.

### 3. Matrix Multiplication: Composition of Actions
What happens if you want to rotate a vector, and *then* scale it up by 2? You could apply two separate matrices: $B$ (scale) and $A$ (rotate).
$$ \mathbf{y} = A(B\mathbf{x}) $$
But matrix multiplication allows us to combine these actions into a *single* new matrix $C = AB$.
$$ \mathbf{y} = C\mathbf{x} $$

> **Mathematical Example (Concrete Numbers):**
> Let $B = \begin{bmatrix} 2 & 0 \\ 0 & 2 \end{bmatrix}$ (scale by 2).
> Let $A = \begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix}$ (rotate 90 degrees).
> To combine them, we multiply $A \times B$:
> $C = \begin{bmatrix} 0 & -1 \\ 1 & 0 \end{bmatrix} \begin{bmatrix} 2 & 0 \\ 0 & 2 \end{bmatrix} = \begin{bmatrix} (0)(2)+(-1)(0) & (0)(0)+(-1)(2) \\ (1)(2)+(0)(0) & (1)(0)+(0)(2) \end{bmatrix} = \begin{bmatrix} 0 & -2 \\ 2 & 0 \end{bmatrix}$.
> Now, instead of doing 2 operations to every data point, we just apply $C$ once!
> 
> **Crucial Intuition:** Matrix multiplication is simply the **composition of transformations**. In deep learning, if you have two linear layers without a non-linear activation (like ReLU) between them, you can mathematically collapse them into a single layer by multiplying their weight matrices together. This saves massive amounts of compute time during inference! 
*Warning:* Order matters! Putting your shoes on and then your socks ($AB$) is very different from putting your socks on and then your shoes ($BA$). Matrix multiplication is **not commutative** *(meaning $AB \neq BA$, so swapping the order of multiplication drastically changes the outcome)*.

**Computational Complexity:**
Standard matrix multiplication for two $n \times n$ matrices requires 3 nested loops, making its time complexity $O(n^3)$. 
> **Enterprise Context:** When training a Large Language Model like GPT-4, 99% of the computational time is spent doing $O(n^3)$ matrix multiplications. This is why GPUs are required—they have thousands of cores that can do these calculations in parallel. Researchers invented algorithms like Strassen's algorithm which drops the complexity to $O(n^{2.807})$, but on modern hardware, highly optimized tiled algorithms (like cuBLAS) running standard $O(n^3)$ on GPUs are usually faster due to hardware architecture.

### 4. Core Matrix Properties
To understand linear algebra in <abbr title="Artificial Intelligence">AI</abbr>, you need to know these descriptors of a matrix:

- **Transpose ($A^T$):** Flipping a matrix over its diagonal *(turning all its rows into columns and columns into rows)*. Essential for making matrix shapes align during backpropagation.
- **Trace ($\text{tr}(A)$):** The sum of the elements on the main diagonal *(from top-left to bottom-right)*. In <abbr title="Artificial Intelligence">AI</abbr>, the trace of a covariance matrix tells you the total variance (total "information") in your dataset.
- **Determinant ($\det(A)$):** A single number representing the factor by which the matrix expands or shrinks the overall volume of space. 
  - If $\det(A) = 0$, the matrix squishes the entire space into a lower dimension (e.g., squishing a 3D cube flat onto a 2D piece of paper). This means information is permanently lost.
- **Rank:** The number of dimensions in the output space after the transformation. If a $3 \times 3$ matrix squishes space into a flat 2D plane, its rank is 2. 
  - **Rank-Nullity Theorem:** Input Dimensions = Rank (Dimensions kept) + Nullity *(the number of dimensions that get completely flattened or erased to zero)*.
  - *Application:* "Low-Rank Adaptation" (<abbr title="Low-Rank Adaptation">LoRA</abbr>), the most popular way to fine-tune LLMs, relies on the assumption that even though a neural network's weight matrix is massive (e.g., $4096 \times 4096$), the *actual* useful transformation it performs has a very low rank (it can be represented by a much smaller matrix without losing information).

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write code that proves matrices are just transformations. We will implement matrix multiplication from scratch to understand the $O(n^3)$ cost, and then visualize transformations using `matplotlib`.

Create `matrix_transforms.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
import time

def slow_matrix_multiply(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """
    Computes A * B using standard O(n^3) triple nested loops.
    This illustrates WHY deep learning needs GPUs.
    """
    # A is (m x n), B is (n x p) -> Result is (m x p)
    m, n = A.shape
    n_b, p = B.shape
    
    if n != n_b:
        raise ValueError("Inner dimensions must match!")
        
    result = np.zeros((m, p))
    
    for i in range(m):
        for j in range(p):
            for k in range(n):
                result[i, j] += A[i, k] * B[k, j]
                
    return result

def visualize_transformation(matrix: np.ndarray, title: str):
    """
    Visualizes how a matrix transforms a grid of points (space).
    """
    # 1. Create a grid of points (a square from 0 to 1)
    grid_points = []
    for x in np.linspace(0, 1, 10):
        for y in np.linspace(0, 1, 10):
            grid_points.append([x, y])
    
    points_matrix = np.array(grid_points).T # Shape: (2, 100)
    
    # 2. Apply the matrix transformation
    # We are applying the matrix (action) to all 100 points at once!
    transformed_points = matrix @ points_matrix
    
    # 3. Plotting
    plt.figure(figsize=(10, 4))
    
    # Original space
    plt.subplot(1, 2, 1)
    plt.scatter(points_matrix[0, :], points_matrix[1, :], c='blue', s=10)
    plt.title("Original Space")
    plt.xlim(-2, 2); plt.ylim(-2, 2)
    plt.grid(True)
    
    # Transformed space
    plt.subplot(1, 2, 2)
    plt.scatter(transformed_points[0, :], transformed_points[1, :], c='red', s=10)
    plt.title(title)
    plt.xlim(-2, 2); plt.ylim(-2, 2)
    plt.grid(True)
    
    # Save the plot as an artifact instead of trying to open a window
    filename = title.replace(' ', '_').lower() + ".png"
    plt.savefig(filename)
    print(f"Saved visualization to {filename}")

def run_benchmarks():
    print("\n--- BENCHMARKING MATMUL ---")
    size = 200
    A = np.random.randn(size, size)
    B = np.random.randn(size, size)
    
    # Slow Custom implementation
    start = time.perf_counter()
    res_slow = slow_matrix_multiply(A, B)
    slow_time = time.perf_counter() - start
    
    # Fast NumPy implementation (Calls highly optimized C/Fortran BLAS libraries)
    start = time.perf_counter()
    res_fast = A @ B 
    fast_time = time.perf_counter() - start
    
    print(f"Triple Loop Time: {slow_time:.4f} seconds")
    print(f"NumPy (@) Time:   {fast_time:.4f} seconds")
    print(f"NumPy is {slow_time/fast_time:.0f}x faster!")

if __name__ == "__main__":
    # Define transformations
    
    # 1. Scale matrix: Multiplies X by 1.5, Multiplies Y by 0.5 (Squishes horizontally)
    scale_matrix = np.array([
        [1.5, 0],
        [0, 0.5]
    ])
    visualize_transformation(scale_matrix, "Scaling Matrix")
    
    # 2. Rotation matrix: Rotates space by 45 degrees
    theta = np.radians(45)
    rotation_matrix = np.array([
        [np.cos(theta), -np.sin(theta)],
        [np.sin(theta),  np.cos(theta)]
    ])
    visualize_transformation(rotation_matrix, "Rotation Matrix")
    
    # 3. Shearing matrix: Pushes the top to the right
    shear_matrix = np.array([
        [1, 1],
        [0, 1]
    ])
    visualize_transformation(shear_matrix, "Shear Matrix")
    
    # 4. Composition: Rotate AND THEN Scale
    # Remember: Order matters! B @ A means apply A first, then B.
    composition_matrix = scale_matrix @ rotation_matrix
    visualize_transformation(composition_matrix, "Composition (Rotate then Scale)")
    
    run_benchmarks()
```

### Key Takeaways from Code:
1. **The `@` Operator:** In modern Python/NumPy, use `@` for matrix multiplication instead of `np.dot()`. It handles multi-dimensional broadcasting much better.
2. **Batch Processing:** Notice how `matrix @ points_matrix` transforms 100 points simultaneously. This is exactly how deep learning batches work. You don't process one image at a time; you put 128 images into a matrix and multiply them all by the weights at once.
3. **The Power of BLAS:** Your pure Python triple loop is incredibly slow. NumPy delegates to BLAS (Basic Linear Algebra Subprograms) written in C/Fortran which uses <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr> vectorization (SIMD) to do operations in parallel.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The 2D Graphics Engine
**Your Task:** Create a new file `graphics_engine.py`.

Imagine you are building a simple 2D game engine. Your player is represented by a triangle with three coordinates:
`A = (0, 0)`, `B = (1, 0)`, `C = (0.5, 1)`.

**Requirements:**
1. Represent the player as a single matrix.
2. Write a function `translate(matrix, dx, dy)` that moves the player. *(Hint: Standard $2 \times 2$ matrices cannot do translation because translation is not a linear transformation. You must use "Homogeneous Coordinates" by adding a 1 to the bottom of your vectors, making them 3D. Look up 2D homogeneous translation matrices!)*
3. Write a function `rotate_and_scale(matrix, degrees, scale_factor)` that composes a rotation and scaling matrix, and applies it to the player.
4. Apply these transformations to the triangle and print the new coordinates. 

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question. Write your answer down or speak it out loud.

**The Question:**
*"You're designing a feature store that needs to perform millions of matrix-vector multiplications per second (e.g., retrieving user embeddings and multiplying them by a real-time weight vector for ad ranking). Walk me through the hardware and software optimization stack."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly across the stack:

1. **Algorithmic / Software Optimization:**
   - Mention replacing sequential processing with **Batched Matrix-Matrix Multiplication (GEMM)**. Instead of doing $1$ million Matrix-Vector multiplications, group the 1 million vectors into a large matrix, and do one massive Matrix-Matrix multiplication.
   - Mention using highly optimized libraries like Intel MKL, OpenBLAS (for <abbr title="Central Processing Unit - The primary component of a computer that acts as its 'brain', executing instructions of a computer program.">CPU</abbr>) or cuBLAS (for GPU).
2. **Data Representation (Sparsity & Precision):**
   - If the matrices are mostly zeros (e.g., user-item interaction matrices), use **Sparse Matrix formats** (CSR/CSC) to skip multiplying zeros entirely.
   - Suggest **Quantization** *(the process of rounding highly precise 32-bit decimals into smaller, rougher 8-bit integers)*. Converting floats (FP32) to (INT8) doubles or quadruples memory bandwidth and computation speed with minimal accuracy loss.
3. **Hardware Selection:**
   - Acknowledge that matrix multiplication is inherently parallelizable. While CPUs have SIMD instructions (AVX-512), **GPUs** (with thousands of cores and specialized Tensor Cores) are vastly superior for dense matrix multiplication. 
   - Mention memory bandwidth bottlenecks: HBM (High Bandwidth Memory) on modern GPUs is critical because fetching the weights from memory often takes longer than the multiplication itself (the system becomes memory-bound, not compute-bound).

---
**Task for the end of the day:** Commit your code to Git. Understanding matrix composition is the exact mechanism that allows Neural Networks to learn complex mappings. Tomorrow, we dissect the matrix with Eigenvectors and <abbr title="Singular Value Decomposition">SVD</abbr>!
