# Day 4: Singular Value Decomposition (<abbr title="Singular Value Decomposition">SVD</abbr>) & Matrix Approximation

Welcome to Day 4. Today we reach the absolute pinnacle of linear algebra for Machine Learning: **Singular Value Decomposition (<abbr title="Singular Value Decomposition">SVD</abbr>)**. 

If Eigendecomposition (from Day 3) is a scalpel that only works on perfectly square, symmetric matrices, <abbr title="Singular Value Decomposition">SVD</abbr> is the ultimate Swiss Army knife. <abbr title="Singular Value Decomposition">SVD</abbr> can dismantle **any matrix in the universe**—no matter its shape—into three fundamental components. It powers recommendation engines (like Netflix and Spotify), image compression, and is the mathematical ancestor of modern Word Embeddings (like Word2Vec).

Let's dive in, remembering to break down the tough math and technical terms as we go.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. The Ultimate Factorization: $A = U \Sigma V^T$
In middle school, you learned that any integer can be factored into prime numbers (e.g., $12 = 2 \times 2 \times 3$). <abbr title="Singular Value Decomposition">SVD</abbr> is the exact same concept, but for data matrices. <abbr title="Singular Value Decomposition">SVD</abbr> proves that *any* matrix $A$ can be factored into three simpler matrices multiplied together.

**Algebraic Definition:**
$$ A = U \Sigma V^T $$

Where:
- $U$: The **Left Singular Vectors**. An orthogonal matrix *(a matrix where all columns are perfectly perpendicular to each other, meaning they are completely independent and share no overlapping information)*. 
- $\Sigma$ (Sigma): A **Diagonal Matrix** *(a matrix where all numbers are zero except for a diagonal line of numbers from the top-left to bottom-right)* containing the **Singular Values** sorted from largest to smallest.
- $V^T$ (V-Transpose): The transpose *(flipping the rows into columns)* of the **Right Singular Vectors** matrix. This is also an orthogonal matrix.

> **Mathematical Example (Concrete Numbers):**
> Let's look at a simple $2 \times 2$ matrix $A = \begin{bmatrix} 3 & 0 \\ 0 & -2 \end{bmatrix}$. 
> If we compute its <abbr title="Singular Value Decomposition">SVD</abbr> ($A = U \Sigma V^T$):
> $U = \begin{bmatrix} 1 & 0 \\ 0 & -1 \end{bmatrix}$ (An orthogonal rotation/flip matrix).
> $\Sigma = \begin{bmatrix} 3 & 0 \\ 0 & 2 \end{bmatrix}$ (The diagonal matrix of singular values, sorted largest to smallest: 3, then 2).
> $V^T = \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix}$ (The identity matrix, doing nothing).
> If you multiply them back together: $\begin{bmatrix} 1 & 0 \\ 0 & -1 \end{bmatrix} \begin{bmatrix} 3 & 0 \\ 0 & 2 \end{bmatrix} \begin{bmatrix} 1 & 0 \\ 0 & 1 \end{bmatrix} = \begin{bmatrix} 3 & 0 \\ 0 & -2 \end{bmatrix} = A$.
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Recommendation Systems):** 
> Imagine $A$ is a massive User-Movie rating matrix ($10,000$ users by $5,000$ movies). It is full of missing values. 
> - $U$ becomes a matrix mapping Users to hidden "Concepts" (like Action or Romance).
> - $\Sigma$ represents the "Importance" or weight of each concept across the entire dataset.
> - $V^T$ maps those hidden Concepts back to specific Movies.
> By multiplying these three back together, the math magically predicts the missing ratings!

### 2. The Geometric Meaning (Rotate, Stretch, Rotate)
Because matrices are transformations *(actions that change space)*, <abbr title="Singular Value Decomposition">SVD</abbr> tells us a beautiful truth: **Every complex transformation in the universe can be broken down into exactly three simple steps.**

1. **$V^T$ (Rotate):** First, it rotates your input data to align with a perfect grid.
2. **$\Sigma$ (Stretch):** Next, it stretches or squishes the grid along the axes. The singular values in $\Sigma$ tell you exactly *how much* to stretch.
3. **$U$ (Rotate):** Finally, it rotates the stretched grid into its final position.

> **Analogy:** Imagine trying to stretch a circular pizza dough into a long oval. <abbr title="Singular Value Decomposition">SVD</abbr> says you do this by: (1) Rotating the dough so it aligns perfectly with your hands ($V^T$), (2) Pulling your hands apart to stretch the dough ($\Sigma$), and (3) Rotating the oval pizza back to fit on the serving tray ($U$).

### 3. Truncated <abbr title="Singular Value Decomposition">SVD</abbr> (Low-Rank Approximation)
The real magic of <abbr title="Singular Value Decomposition">SVD</abbr> is in the $\Sigma$ (Sigma) matrix. Because the singular values are sorted from largest to smallest, the math explicitly tells you which dimensions contain the most "information" (variance) and which dimensions contain "noise" (random static).

**Low-Rank Approximation Formula:**
$$ A_k = U_k \Sigma_k V_k^T $$
*(We only keep the top $k$ singular values, and throw away the rest).*

> **Mathematical Example (Concrete Numbers):**
> Let $\Sigma = \begin{bmatrix} 1000 & 0 & 0 \\ 0 & 10 & 0 \\ 0 & 0 & 0.1 \end{bmatrix}$. 
> The first value (1000) is massive. The last value (0.1) is tiny.
> If we want to compress our data, we "truncate" *(cut off)* the matrix by forcing the smallest value to zero: $\Sigma_{k=2} = \begin{bmatrix} 1000 & 0 & 0 \\ 0 & 10 & 0 \\ 0 & 0 & 0 \end{bmatrix}$.
> We just deleted an entire dimension of data, but we only lost $0.1$ units of information!
> 
> **<abbr title="Artificial Intelligence">AI</abbr> Context (Data Compression & Denoising):** 
> If you have a high-resolution 10-megapixel image, it takes up a lot of memory. By computing the <abbr title="Singular Value Decomposition">SVD</abbr> of the image matrix and keeping only the top 50 singular values (throwing away the other 3000), you can reconstruct a slightly blurry version of the image that takes up 98% less memory. Furthermore, because "noise" (like camera static) is mathematically random, it gets trapped in the smallest singular values. Throwing them away actually *cleans* the image!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's prove that <abbr title="Singular Value Decomposition">SVD</abbr> is the ultimate compression algorithm. We will write a script that generates a 2D image (which is just a matrix of pixel intensities), computes its <abbr title="Singular Value Decomposition">SVD</abbr>, and reconstructs it using fewer and fewer singular values.

Create a file named `svd_compression.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from skimage import data # pip install scikit-image
from skimage.color import rgb2gray

def demonstrate_svd_compression():
    """
    Loads a standard test image, computes SVD, and reconstructs it 
    at various levels of compression (Low-Rank Approximation).
    """
    print("--- SVD IMAGE COMPRESSION ---")
    
    # 1. Load an image and convert to grayscale (so it is a 2D matrix)
    # The 'astronaut' image is a classic computer vision test image
    image = rgb2gray(data.astronaut())
    
    # The image is a matrix of floats between 0 (black) and 1 (white)
    print(f"Original Image Shape (Matrix A): {image.shape}")
    
    # 2. Compute the SVD
    # full_matrices=False is a memory optimization (Truncated SVD)
    U, Sigma, Vt = np.linalg.svd(image, full_matrices=False)
    
    print(f"U shape: {U.shape} (Left Singular Vectors)")
    print(f"Sigma shape: {Sigma.shape} (Singular Values array)")
    print(f"Vt shape: {Vt.shape} (Right Singular Vectors)")
    
    # 3. Plotting the results
    plt.figure(figsize=(15, 10))
    
    # Original Image
    plt.subplot(2, 3, 1)
    plt.imshow(image, cmap='gray')
    plt.title(f"Original\n({image.shape[0]}x{image.shape[1]} pixels)")
    plt.axis('off')
    
    # Reconstruct with different numbers of 'k' (singular values to keep)
    k_values = [5, 20, 50, 100]
    
    for i, k in enumerate(k_values):
        # Truncate the matrices (Keep only the first 'k' columns/rows)
        U_k = U[:, :k]
        
        # Sigma is returned as a 1D array by numpy for memory efficiency.
        # We need to make it a diagonal matrix to multiply it.
        Sigma_k = np.diag(Sigma[:k]) 
        
        Vt_k = Vt[:k, :]
        
        # Reconstruct the image: A_k = U_k * Sigma_k * Vt_k
        # We use the @ operator for matrix multiplication
        reconstructed_image = U_k @ Sigma_k @ Vt_k
        
        # Calculate compression ratio
        # Original size = 512 * 512 = 262,144 numbers
        # Compressed size = (512 * k) + k + (k * 512)
        original_size = image.shape[0] * image.shape[1]
        compressed_size = (U_k.shape[0] * k) + k + (k * Vt_k.shape[1])
        compression_ratio = original_size / compressed_size
        
        plt.subplot(2, 3, i + 2)
        plt.imshow(reconstructed_image, cmap='gray')
        plt.title(f"Reconstructed with k={k}\nCompression: {compression_ratio:.1f}x")
        plt.axis('off')
        
    # Plot the Singular Values themselves (Scree Plot)
    plt.subplot(2, 3, 6)
    # Plot only the first 100 values to see the drop-off
    plt.plot(Sigma[:100], 'r-', linewidth=2)
    plt.title("Scree Plot (Magnitude of Singular Values)")
    plt.ylabel("Information / Variance")
    plt.xlabel("Singular Value Index")
    plt.grid(True)
    
    plt.tight_layout()
    filename = "svd_image_compression.png"
    plt.savefig(filename)
    print(f"\nSaved visualization to {filename}. Open it to see the magic of SVD!")

if __name__ == "__main__":
    demonstrate_svd_compression()
```

### Key Takeaways from Code:
1. **The Scree Plot:** Look at the bottom right graph generated by the code. It shows the magnitude of the singular values. Notice how it looks like a cliff? The first 20 values contain almost all the "information", and the remaining 400+ values are basically flat at zero. <abbr title="Singular Value Decomposition">SVD</abbr> mathematically isolated the "signal" from the "noise".
2. **Matrix Memory:** To store the $512 \times 512$ image requires 262,144 floats. Using <abbr title="Singular Value Decomposition">SVD</abbr> with $k=50$, we only store $U$ ($512 \times 50$), $\Sigma$ ($50$), and $V^T$ ($50 \times 512$). This equals 51,250 floats. We achieved a **5x compression** while keeping the image perfectly recognizable!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Netflix Recommendation Engine
**Your Task:** Create a file named `collaborative_filtering.py`.

You are going to build a miniature recommendation system.
1. Create a $5 \times 4$ numpy array representing 5 Users and 4 Movies (Sci-Fi 1, Sci-Fi 2, Romance 1, Romance 2). 
2. Fill the matrix with ratings from 1 to 5. Make sure User 1 and 2 only rate Sci-Fi highly, and User 4 and 5 only rate Romance highly. *Leave two cells as `0` to represent movies a user hasn't watched yet.*
3. Compute the <abbr title="Singular Value Decomposition">SVD</abbr> of this matrix using `np.linalg.svd`.
4. Truncate the matrices to keep only $k=2$ singular values *(because we have 2 hidden genres: Sci-Fi and Romance!)*.
5. Multiply $U_k \Sigma_k V_k^T$ back together to create a "Reconstructed Rating Matrix".
6. Look at the cells that were originally `0`. The math has magically filled them in with predicted ratings! Print out the highest predicted movie for the users who had missing data.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Why is Truncated <abbr title="Singular Value Decomposition">SVD</abbr> mathematically guaranteed to find the best possible low-rank approximation of a matrix? Furthermore, how does this matrix factorization concept relate to how Word2Vec creates word embeddings?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Eckart-Young-Mirsky Theorem:** 
   - State clearly that Truncated <abbr title="Singular Value Decomposition">SVD</abbr> isn't just a "good" heuristic; it is mathematically proven by the **Eckart-Young-Mirsky Theorem** to be the *optimal* approximation. 
   - Explain that if you want to approximate a matrix $A$ with a lower-rank *(fewer dimensions)* matrix $B$, Truncated <abbr title="Singular Value Decomposition">SVD</abbr> minimizes the **Frobenius Norm** *(the sum of the squared differences between the original pixels/numbers and the new pixels/numbers)* of the error matrix $(A - B)$. You cannot physically get a lower error margin than what <abbr title="Singular Value Decomposition">SVD</abbr> provides.
2. **Word2Vec Connection (Implicit Matrix Factorization):**
   - Explain that traditional <abbr title="Natural Language Processing">NLP</abbr> used **Co-occurrence Matrices** *(a massive grid tracking how often word X appears next to word Y)*. Applying <abbr title="Singular Value Decomposition">SVD</abbr> to this massive matrix yields word embeddings (the $U$ matrix becomes the word vectors).
   - Word2Vec (Skip-Gram with Negative Sampling) trains a shallow neural network to predict context words. 
   - **The critical insight:** In 2014, researchers proved mathematically that training a Word2Vec neural network is implicitly performing the exact same matrix factorization (<abbr title="Singular Value Decomposition">SVD</abbr>) on a Pointwise Mutual Information (PMI) matrix! Word embeddings are literally just the singular vectors of language data.

---
**Task for the end of the day:** Commit your code to Git. You have now completed the Linear Algebra gauntlet! By understanding Vectors, Matrices, Eigenvectors, and <abbr title="Singular Value Decomposition">SVD</abbr>, you possess the mathematical intuition required to understand exactly how Attention Mechanisms and LLMs manipulate high-dimensional concepts. 

Tomorrow, we pivot to Phase 2: Calculus, Gradients, and Backpropagation!
