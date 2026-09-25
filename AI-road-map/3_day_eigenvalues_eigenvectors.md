# Day 3: Eigenvalues, Eigenvectors & Spectral Decomposition

Welcome to Day 3. Today we tackle one of the most notoriously intimidating, yet beautiful and crucial topics in all of Machine Learning: **Eigendecomposition**. 

If Day 2 taught us that matrices are *transformations* (actions that stretch, rotate, and squish space), today we learn how to find the hidden "bones" or "skeleton" of those transformations. If you want to understand Principal Component Analysis (PCA), how Google Search was invented (PageRank), or how recommendation algorithms compress user data (<abbr title="Singular Value Decomposition">SVD</abbr>), you must master eigenvectors.

Let's break it down using deep intuition and real-world analogies.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. What are Eigenvectors and Eigenvalues?
The word "eigen" is German for *own*, *characteristic*, or *peculiar to*. An eigenvector is a vector that is characteristic of a specific matrix.

**Geometric Intuition:**
Imagine you have a rubber sheet with a grid drawn on it, and you draw a bunch of arrows (vectors) pointing in random directions from the center. Now, grab the edges of the sheet and stretch it horizontally, and maybe shear it a bit.
Most of the arrows you drew will change their **length** AND their **direction**. 
However, there are a few special, magical arrows that *do not change direction at all*. They might get longer, they might get shorter, or they might flip backwards, but they stay on the exact same line they started on.

- **Eigenvector ($\mathbf{v}$):** The special vector that doesn't get knocked off its span during a transformation.
- **Eigenvalue ($\lambda$):** The scalar factor by which the eigenvector is stretched or shrunk. If $\lambda = 2$, the vector doubled in length. If $\lambda = -1$, it flipped backwards but stayed on the same line.

**Algebraic Definition:**
$$ A\mathbf{v} = \lambda\mathbf{v} $$
*Read this carefully:* A matrix $A$ (a complex transformation) acting on a vector $\mathbf{v}$ produces the exact same result as a simple scalar number $\lambda$ multiplying that same vector $\mathbf{v}$. 

> **Mathematical Example (Concrete Numbers):**
> Let's test if a vector is an eigenvector! 
> Let Matrix $A = \begin{bmatrix} 2 & 0 \\ 0 & 3 \end{bmatrix}$. 
> Let's try vector $\mathbf{v} = \begin{bmatrix} 1 \\ 0 \end{bmatrix}$.
> Left side ($A\mathbf{v}$): $\begin{bmatrix} 2 & 0 \\ 0 & 3 \end{bmatrix} \begin{bmatrix} 1 \\ 0 \end{bmatrix} = \begin{bmatrix} (2)(1)+(0)(0) \\ (0)(1)+(3)(0) \end{bmatrix} = \begin{bmatrix} 2 \\ 0 \end{bmatrix}$.
> Right side ($\lambda\mathbf{v}$): Can we write $\begin{bmatrix} 2 \\ 0 \end{bmatrix}$ as a single number times our original vector $\begin{bmatrix} 1 \\ 0 \end{bmatrix}$? Yes! $2 \times \begin{bmatrix} 1 \\ 0 \end{bmatrix}$.
> Therefore, $\mathbf{v} = [1, 0]$ IS an eigenvector, and its eigenvalue is $\lambda = 2$.
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Feature Extraction):** 
> If $A$ is a Covariance Matrix of housing data (Size vs Price), the eigenvector with the largest eigenvalue represents the most dominant pattern in the data (e.g., "Bigger houses cost more"). This is the mathematical core of **Principal Component Analysis (PCA)**, which reduces massive datasets down to their most important features.
> **Analogy:** Imagine a complex corporate hierarchy (Matrix A) trying to process a specific type of task (Vector $\mathbf{v}$). If the task is an "eigen-task", the complex corporate bureaucracy handles it as efficiently as a single person ($\lambda$) just doing the work directly. 

### 2. How to Find Them: The Characteristic Polynomial
How does a computer (or a math student) actually find these special vectors? We use algebra.

1. Start with the definition: $A\mathbf{v} = \lambda\mathbf{v}$
2. Move everything to one side: $A\mathbf{v} - \lambda\mathbf{v} = 0$
3. Factor out $\mathbf{v}$. To do this properly in matrix algebra, we multiply the scalar $\lambda$ by the Identity matrix $I$ (a matrix of 1s on the diagonal, 0s elsewhere):
   $$ (A - \lambda I)\mathbf{v} = 0 $$

Now we have a puzzle. A matrix $(A - \lambda I)$ multiplied by a vector $\mathbf{v}$ equals zero. 
We know $\mathbf{v}$ isn't a zero vector (that would be cheating). The only way a matrix can multiply a non-zero vector and get zero is if that matrix squishes space so much that it loses dimensions. Mathematically, this means its **determinant must be zero**.

$$ \det(A - \lambda I) = 0 $$
This equation is called the **Characteristic Polynomial** *(an algebraic equation used to find the exact values that make the determinant zero)*. Solving it gives you the Eigenvalues ($\lambda$). Once you have the eigenvalues, you plug them back in to find the Eigenvectors ($\mathbf{v}$).

> **Mathematical Example (Concrete Numbers):**
> Let $A = \begin{bmatrix} 2 & 1 \\ 1 & 2 \end{bmatrix}$. Let's find its eigenvalues!
> Step 1: $(A - \lambda I) = \begin{bmatrix} 2-\lambda & 1 \\ 1 & 2-\lambda \end{bmatrix}$.
> Step 2: Set determinant to 0. The formula for a 2x2 determinant is $(ad - bc)$.
> $(2-\lambda)(2-\lambda) - (1)(1) = 0$
> $4 - 4\lambda + \lambda^2 - 1 = 0 \implies \lambda^2 - 4\lambda + 3 = 0$.
> Step 3: Factor the polynomial. $(\lambda - 3)(\lambda - 1) = 0$.
> Result: The eigenvalues are $\lambda = 3$ and $\lambda = 1$.
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Computational Bottleneck):** 
> Finding roots of polynomials for a 2x2 matrix is easy. But in <abbr title="Artificial Intelligence">AI</abbr>, our matrices (like <abbr title="Large Language Model">LLM</abbr> weights) are $10,000 \times 10,000$. Finding the roots of a 10,000-degree polynomial is computationally impossible. This is why in production <abbr title="Artificial Intelligence">AI</abbr>, we NEVER compute determinants. We use iterative approximation algorithms like **Power Iteration** or **Lanczos** to find the largest eigenvalues!

### 3. The Spectral Theorem (The Magic of Symmetric Matrices)
In Machine Learning, we almost always deal with **Symmetric Matrices**. A symmetric matrix is one that equals its transpose ($A = A^T$, *meaning it acts like a perfect mirror across its diagonal*). The most famous example is a **Covariance Matrix**, which measures how different features in your dataset vary together *(e.g., if square footage goes up, does house price go up?)*.

The **Spectral Theorem** states that if a matrix is symmetric:
1. All its eigenvalues are real numbers (no complex/imaginary numbers).
2. **Its eigenvectors are orthogonal (perfectly perpendicular) to each other.**

> **Real-World Application (Principal Component Analysis - PCA):**
> Imagine a massive dataset with 1,000 features (dimensions). You compute its covariance matrix (which is symmetric). When you find the eigenvectors of this covariance matrix, the Spectral Theorem guarantees they form a perfectly perpendicular 3D-style grid (a new coordinate system). 
> The eigenvector with the *largest eigenvalue* points in the direction where your data is most spread out (the most information). This is your "1st Principal Component". By keeping only the top 50 eigenvectors and throwing away the other 950, you compress your data drastically while retaining 99% of the signal.

### 4. Positive Definite Matrices & Optimization
A symmetric matrix is **Positive Definite** *(a property meaning the mathematical space always curves upwards like a bowl)* if all of its eigenvalues are strictly positive ($\lambda > 0$).

> **Enterprise Context (Deep Learning Optimization):**
> In calculus, the second derivative tells you the curvature of a function. In high-dimensional neural networks, the equivalent of the second derivative is a massive matrix called the **Hessian Matrix**. 
> If the Hessian matrix at a certain point is Positive Definite (all positive eigenvalues), it means the loss landscape curves upwards in *every single direction*. Geometrically, you are at the bottom of a perfect bowl. 
> Why does this matter? If your optimizer (like Adam or <abbr title="Stochastic Gradient Descent">SGD</abbr>) reaches a point where the Hessian is positive definite, you have mathematically proven you are at a **local minimum**. If it has negative eigenvalues, you are on a saddle point, and the optimizer needs to keep sliding down!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write code to find eigenvectors. While `numpy.linalg.eig` can do this instantly, production systems dealing with matrices of size 1,000,000 x 1,000,000 cannot use standard linear algebra libraries (it takes too much memory and $O(n^3)$ time). Instead, they use iterative approximations like **Power Iteration**.

Create a file named `eigen_analysis.py`:

```python
import numpy as np
import matplotlib.pyplot as plt

def power_iteration(A: np.ndarray, num_iterations: int = 100) -> tuple[float, np.ndarray]:
    """
    Approximates the dominant eigenvalue and eigenvector of matrix A.
    This is the fundamental algorithm behind Google's original PageRank!
    """
    n, m = A.shape
    if n != m:
        raise ValueError("Matrix must be square")
        
    # 1. Start with a random vector
    v = np.random.rand(n)
    
    for _ in range(num_iterations):
        # 2. Multiply the vector by the matrix (Apply the transformation)
        v = A @ v
        
        # 3. Normalize the vector (Prevent it from blowing up to infinity)
        v = v / np.linalg.norm(v)
        
    # Calculate the Rayleigh quotient to find the eigenvalue
    # lambda = (v^T * A * v) / (v^T * v)
    # Since v is normalized, v^T * v = 1, so lambda = v^T * A * v
    eigenvalue = np.dot(v, A @ v)
    
    return eigenvalue, v

def visualize_covariance_eigenvectors():
    """
    Generates a 2D dataset, computes its covariance matrix, finds the 
    eigenvectors, and visualizes how they point in the direction of maximum variance.
    This is the visual proof of PCA!
    """
    print("\n--- VISUALIZING COVARIANCE EIGENVECTORS (PCA INTUITION) ---")
    
    # 1. Generate synthetic data (a stretched oval of points)
    np.random.seed(42)
    # Start with a circular blob
    data = np.random.randn(2, 500) 
    
    # Apply a transformation matrix to stretch and rotate it
    transformation = np.array([[2, 1], [1, 0.5]])
    data = transformation @ data
    
    # 2. Calculate the Covariance Matrix
    # Center the data first (mean = 0)
    data_centered = data - np.mean(data, axis=1, keepdims=True)
    # Covariance formula: (1/n) * X * X^T
    cov_matrix = (data_centered @ data_centered.T) / (data.shape[1] - 1)
    
    print("Covariance Matrix:")
    print(cov_matrix)
    
    # 3. Find Eigenvectors and Eigenvalues using NumPy
    eigenvalues, eigenvectors = np.linalg.eig(cov_matrix)
    
    print("\nEigenvalues (Variance in each direction):")
    print(eigenvalues)
    print("\nEigenvectors (The directions themselves):")
    print(eigenvectors)
    
    # 4. Visualization
    plt.figure(figsize=(8, 8))
    plt.scatter(data[0, :], data[1, :], alpha=0.2, color='blue')
    
    # Plot the eigenvectors originating from the mean
    mean_x, mean_y = np.mean(data, axis=1)
    
    for i in range(len(eigenvalues)):
        # Scale the eigenvector by the square root of its eigenvalue 
        # (Standard deviation in that direction) for visual clarity
        vector = eigenvectors[:, i] * np.sqrt(eigenvalues[i]) * 2
        
        plt.arrow(mean_x, mean_y, vector[0], vector[1], 
                  head_width=0.2, head_length=0.3, fc='red', ec='red', linewidth=3)
        plt.text(mean_x + vector[0]*1.1, mean_y + vector[1]*1.1, 
                 f"PC {i+1}", color='red', fontsize=12, fontweight='bold')

    plt.axis('equal') # Keep aspect ratio 1:1 so orthogonal lines look orthogonal
    plt.title("Data Distribution and its Principal Components (Eigenvectors)")
    plt.grid(True)
    
    # Save the plot
    filename = "eigenvectors_pca.png"
    plt.savefig(filename)
    print(f"\nSaved visualization to {filename}. Open this image to see the math in action!")

if __name__ == "__main__":
    # Test Power Iteration
    print("--- TESTING POWER ITERATION ---")
    A = np.array([[4, 1], [2, 3]])
    
    # Using our custom iterative algorithm
    custom_val, custom_vec = power_iteration(A)
    print(f"Power Iteration Dominant Eigenvalue: {custom_val:.4f}")
    print(f"Power Iteration Dominant Eigenvector: {custom_vec}")
    
    # Using NumPy's exact algebraic solver
    np_vals, np_vecs = np.linalg.eig(A)
    # Find the index of the largest eigenvalue
    max_idx = np.argmax(np.abs(np_vals))
    print(f"NumPy Dominant Eigenvalue: {np_vals[max_idx]:.4f}")
    print(f"NumPy Dominant Eigenvector: {np_vecs[:, max_idx]}")
    
    visualize_covariance_eigenvectors()
```

### Key Takeaways from Code:
1. **Power Iteration:** Notice how simple the loop is. Just multiply `A @ v` and normalize. Yet, this simple loop naturally converges to the most important vector in the matrix.
2. **Covariance & PCA:** When you run `visualize_covariance_eigenvectors()`, look at the image generated. Notice how the two red arrows (eigenvectors) are perfectly 90 degrees apart (orthogonal). The longest arrow points exactly along the longest stretch of the blue data dots. **You just built the mathematical engine of Principal Component Analysis from scratch.**

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Image Compression via Eigendecomposition
**Your Task:** Create a file named `pca_compression.py`.

You are going to use Eigenvectors to compress data. 
1. Create a synthetic dataset of 1000 samples, where each sample has 10 features (A $10 \times 1000$ matrix). Make the features highly correlated (e.g., feature 2 is just feature 1 multiplied by 2 plus some noise).
2. Compute the $10 \times 10$ Covariance Matrix of this dataset.
3. Use `np.linalg.eig` to find the 10 eigenvalues and 10 eigenvectors.
4. Sort the eigenvectors based on their corresponding eigenvalues in descending order.
5. Take only the top **2** eigenvectors. This is your $10 \times 2$ projection matrix $W$.
6. Project your original $10 \times 1000$ dataset down to $2 \times 1000$ by doing $W^T \times \text{Data}$. 

*Congratulations, you have just compressed a 10-dimensional dataset into 2 dimensions while keeping the maximum possible amount of variance (information)!*

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Explain how Google's original PageRank algorithm fundamentally relies on eigenvector computation. Given that the modern web has billions of pages, standard matrix decomposition is impossible. How would you scale this computation?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Web as a Matrix (Markov Chain):** 
   - Explain that the internet can be modeled as a massive adjacency matrix (or transition matrix). If Page A links to Page B, there is a probability $> 0$ in that cell. 
   - The matrix represents the probability of a "random surfer" clicking a link and landing on a new page. This is a classic **Markov Chain** *(a mathematical system that hops from one state to another, where the next hop depends entirely on where you are right now)*.
2. **PageRank = Dominant Eigenvector:** 
   - A page is important if important pages link to it. This is a recursive definition.
   - Mathematically, finding the steady-state probability of landing on any given page after infinite random clicks is exactly equivalent to finding the **dominant eigenvector** of this transition matrix (where the eigenvalue $\lambda = 1$).
3. **Scaling the Computation:** 
   - A $10 \text{ billion} \times 10 \text{ billion}$ matrix cannot fit in memory, and $O(n^3)$ operations would take centuries. 
   - Therefore, we CANNOT use standard eigendecomposition (like `np.linalg.eig`).
   - Instead, we use the **Power Iteration Method** (which we coded in Hour 2!). We start with a vector of $1/N$, and repeatedly multiply it by the transition matrix: $\mathbf{v}_{t+1} = M \mathbf{v}_t$.
4. **Distributed Systems (MapReduce):** 
   - Furthermore, the matrix is extremely **sparse** *(meaning 99.9% of the entries are just zero, so we use special data structures to only store the non-zero numbers to save memory)*. 
   - The sparse matrix-vector multiplication ($M \mathbf{v}$) can be trivially distributed across thousands of commodity servers. This exact problem is what prompted Google to invent the **MapReduce** framework!

---
**Task for the end of the day:** Commit your code to Git. Review the `eigenvectors_pca.png` image until the connection between data variance and eigenvectors intuitively clicks in your brain. Tomorrow, we finish the linear algebra gauntlet with Singular Value Decomposition (<abbr title="Singular Value Decomposition">SVD</abbr>)!
