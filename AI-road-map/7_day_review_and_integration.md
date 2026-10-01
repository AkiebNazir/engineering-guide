# Day 7: Review & Integration Lab (Week 1 Finale)

Welcome to Day 7. You have survived the first week of the 180-day curriculum. 

The goal of a Principal AI Engineer is not to memorize disconnected formulas. The goal is to see the **Matrix** *(the interconnected system of mathematical rules that govern how data behaves)*. Today, there are no new abstract concepts. We are going to wire all 6 previous days together into a single, cohesive mental model, and then we are going to build a production-grade Python package.

Let's synthesize the bedrock.

---

## 🕒 HOUR 1: DEEP THEORY & THE DEPENDENCY GRAPH

### 1. The Grand AI Workflow
Every machine learning algorithm, from a simple Linear Regression to a trillion-parameter GPT, follows this exact sequence of linear algebra and calculus:

1. **The Representation (Day 1):** We take real-world concepts (words, images, user behaviors) and turn them into **Vectors** $\mathbf{x}$. 
2. **The Transformation (Day 2):** We pass the data through a model. The model is just a series of **Matrices** $W$. We multiply them together: $y = W\mathbf{x}$.
3. **The Measurement (Day 5):** We check how wrong the model was using a **Loss Function**. We measure the distance between the prediction and the truth using a **Norm** $\| \hat{y} - y \|$.
4. **The Correction (Day 6):** We use **Matrix Calculus** to compute the **Gradient** $\nabla L$. We use the **Matrix Chain Rule** *(Backpropagation)* to pass that error backward through the **Jacobian matrices** of the network, adjusting the weights.
5. **The Optimization (Days 3 & 4):** To make this process efficient, we use **Eigendecomposition** and **SVD** to compress the data, remove noise, and ensure our optimization algorithms don't get stuck on saddle points *(flat areas in the math landscape where the gradient is zero but it's not the actual bottom)*.

### 2. Synthesizing the Math

Let's look at a single, unified mathematical operation: **Ridge Regression (L2 Regularized Linear Regression)**.
The formula to find the perfect weights mathematically in one shot is:
$$ \mathbf{w} = (X^T X + \lambda I)^{-1} X^T \mathbf{y} $$

Let's break down exactly what Week 1 taught us about this formula:

- $X$: This is our data **Matrix** (Day 2).
- $X^T X$: This creates a symmetric **Covariance Matrix** (Day 3). It measures how all our features interact with each other.
- $\lambda I$: This adds a small scalar $\lambda$ to the diagonal. Why? Because sometimes $\det(X^T X) = 0$ *(the determinant is zero, meaning space was squished and information lost)*, making it impossible to invert. Adding $\lambda I$ guarantees the matrix is **Positive Definite** *(it curves perfectly like a bowl)* (Day 3).
- $+ \lambda I$: This addition mathematically mirrors penalizing the weights using the **$L_2$ Norm** *(Euclidean distance)* (Day 5), preventing any single weight from getting too large!
- $(\dots)^{-1}$: We take the **Inverse** (Day 0) to solve the system. If the matrix is too massive to invert $O(n^3)$ (Day 2), we use Gradient Descent (Day 6) instead.

> **Mathematical Example (Concrete Numbers):**
> Let's do a tiny 1D regression. $X = \begin{bmatrix} 2 \\ 3 \end{bmatrix}$ (two data points). $y = \begin{bmatrix} 4 \\ 6 \end{bmatrix}$ (the target answers). Let $\lambda = 1$.
> Step 1: $X^T X = [2, 3] \begin{bmatrix} 2 \\ 3 \end{bmatrix} = (2\times2) + (3\times3) = 13$.
> Step 2: Add $\lambda I$: $13 + 1 = 14$.
> Step 3: Invert it: $(14)^{-1} = \frac{1}{14}$.
> Step 4: $X^T \mathbf{y} = [2, 3] \begin{bmatrix} 4 \\ 6 \end{bmatrix} = 8 + 18 = 26$.
> Final Math: $\mathbf{w} = \frac{1}{14} \times 26 \approx 1.85$.
> 
> **AI Context (The Perfect Fit):** 
> Without $\lambda$, the answer would be $\frac{26}{13} = 2.0$. The math perfectly deduced that $y$ is exactly $2$ times $x$. But because we added $\lambda=1$ (L2 Regularization), the math "shrank" the weight slightly to $1.85$ to prevent the model from being too overconfident!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

As a Principal Engineer, you don't just write scripts; you write **Software**. Today, we are going to compile our Week 1 functions into a structured Python package. 

Create a folder named `ml_math_toolkit`. Inside it, create two files: `__init__.py` and `core.py`. Also create a file outside the folder called `test_toolkit.py`.

**File 1: `ml_math_toolkit/__init__.py`**
```python
# This empty file tells Python that this directory is a module/package.
# We can expose specific functions here to make importing cleaner.
from .core import dot_product, matrix_multiply, svd_compress, numerical_gradient
```

**File 2: `ml_math_toolkit/core.py`**
```python
import numpy as np

def dot_product(v1: np.ndarray, v2: np.ndarray) -> float:
    """Computes geometric overlap of two vectors."""
    return np.sum(v1 * v2)

def matrix_multiply(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    """Composes two linear transformations using NumPy broadcasting."""
    return A @ B

def svd_compress(matrix: np.ndarray, k: int) -> np.ndarray:
    """
    Performs optimal low-rank approximation.
    Throws away all but the top 'k' dimensions of information.
    """
    U, Sigma, Vt = np.linalg.svd(matrix, full_matrices=False)
    return U[:, :k] @ np.diag(Sigma[:k]) @ Vt[:k, :]

def l2_norm(v: np.ndarray) -> float:
    """Computes standard Euclidean distance."""
    return np.sqrt(np.sum(v ** 2))

def numerical_gradient(func, x: np.ndarray, h: float = 1e-5) -> np.ndarray:
    """Approximates the gradient vector using finite differences."""
    grad = np.zeros_like(x)
    for i in range(len(x)):
        x_plus = np.copy(x)
        x_plus[i] += h
        x_minus = np.copy(x)
        x_minus[i] -= h
        grad[i] = (func(x_plus) - func(x_minus)) / (2 * h)
    return grad
```

**File 3: `test_toolkit.py`**
```python
import numpy as np
from ml_math_toolkit import dot_product, matrix_multiply, svd_compress

def test_dot_product():
    a = np.array([1, 0])
    b = np.array([0, 1])
    assert dot_product(a, b) == 0.0, "Orthogonal vectors must have 0 dot product"
    print("✅ Dot product passed")

def test_matrix_multiply():
    A = np.array([[1, 2], [3, 4]])
    I = np.eye(2) # Identity matrix
    result = matrix_multiply(A, I)
    assert np.allclose(result, A), "Multiplying by Identity must return original matrix"
    print("✅ Matrix multiplication passed")

def test_svd_compression():
    # Create a simple rank-1 matrix
    A = np.array([[2, 4], [3, 6]])
    # Compress keeping only k=1 singular value
    A_compressed = svd_compress(A, k=1)
    assert np.allclose(A, A_compressed), "Rank-1 matrix should compress perfectly at k=1"
    print("✅ SVD compression passed")

if __name__ == "__main__":
    print("--- RUNNING TOOLKIT UNIT TESTS ---")
    test_dot_product()
    test_matrix_multiply()
    test_svd_compression()
    print("All tests passed! Toolkit is production-ready.")
```

### Key Takeaways from Code:
1. **Modularity:** Real ML systems (like PyTorch or Scikit-Learn) are built exactly like this. Core math routines are isolated into modules, and unit tests guarantee that a change in `svd_compress` doesn't silently break downstream recommendation systems.
2. **`assert` Statements:** Using assertions is how you write Unit Tests. If the math fails, the script forcefully crashes before bad data can corrupt your training loop.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Complete PCA Pipeline
**Your Task:** Create a new file `run_pca.py`. 

You are going to build Principal Component Analysis (PCA) from scratch using **only** your `ml_math_toolkit` and basic NumPy operations (no `sklearn`).
1. Import your toolkit.
2. Generate a random dataset of 100 samples with 5 features ($100 \times 5$ matrix).
3. **Step 1:** Mean-center the data (subtract the mean of each column from the data).
4. **Step 2:** Compute the Covariance Matrix using your `matrix_multiply` function: $Cov = \frac{1}{N-1} X^T X$.
5. **Step 3:** Perform Eigendecomposition on the Covariance matrix. (You can use `np.linalg.eig` for this specific step).
6. **Step 4:** Sort the eigenvectors by their eigenvalues. Take the top 2 eigenvectors.
7. **Step 5:** Project the original $100 \times 5$ data down to $100 \times 2$ by multiplying the data matrix by the top 2 eigenvectors. 

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a Linear Algebra computation service for an internal AI team. It needs to handle 10,000 concurrent requests for matrix operations on massive matrices (up to $10,000 \times 10,000$). Discuss the memory, compute, and latency trade-offs."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Memory Bottlenecks (The $O(n^2)$ problem):** 
   - A single $10,000 \times 10,000$ matrix of 32-bit floats (FP32) takes exactly $400$ Megabytes of RAM. 
   - If 10,000 users request an operation at the exact same time, you need $4$ Terabytes of RAM just to hold the matrices in memory. You cannot run this on a single machine.
2. **Compute Bottlenecks (The $O(n^3)$ problem):** 
   - Multiplying two $10,000 \times 10,000$ matrices requires 1 Trillion operations (FLOPs). CPUs will be too slow. You must route these requests to GPU instances running highly optimized cuBLAS kernels.
3. **The Trade-offs & Solutions:** 
   - **Latency vs. Throughput:** Do you process requests instantly (low latency), or do you queue them up to batch them together for the GPU (high throughput)? A strong engineer explicitly states they would implement a queueing system (like Kafka or RabbitMQ) and use **Dynamic Batching** to group smaller matrix multiplications together before sending them to the GPU.
   - **Precision vs. Speed:** Suggest offering an API flag for quantization. If the user accepts `FP16` or `INT8` precision, memory requirements drop by 50% to 75%, and Tensor Cores on the GPU will calculate the result infinitely faster.

---
**Task for the end of the day:** Commit your toolkit to Git. You have mastered Phase 1. 

Get ready. In Phase 2 (Starting on Day 8), we move out of pure math and enter the realm of **Probability, Statistics & Information Theory**. We are going to build the mathematical foundation of how an AI models uncertainty and "thinks" about the world!
