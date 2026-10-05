# Day 5: Norms, Distances & Metric Spaces

Welcome to Day 5. After conquering vectors, matrices, eigenvectors, and SVD, you might think you know everything about how data is mapped. But there is a massive difference between *plotting* a point in space and *measuring the distance* between two points.

Today, we cover **Norms and Distances**. In Machine Learning, everything is an optimization problem: we define an "Error" or "Loss", and we try to minimize it. The mathematical tool we use to measure that error is a Norm. If you choose the wrong norm, your AI will learn the wrong thing. 

Let's understand how an AI physically measures space.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. What is a Norm?
A **Norm** *(a mathematical function that assigns a strictly positive length or size to a vector)* is simply how we measure length in linear algebra. 

For a function to officially be called a "norm", it must obey the axioms of a **Metric Space** *(a mathematical set where the concept of distance between any two elements is strictly defined)*:
1. **Non-negativity:** Length cannot be negative ($\|\mathbf{x}\| \ge 0$).
2. **Identity:** If the length is 0, the vector must be the zero vector ($\|\mathbf{x}\| = 0 \iff \mathbf{x} = \mathbf{0}$).
3. **Triangle Inequality:** The shortest path between two points is a straight line ($\|\mathbf{x} + \mathbf{y}\| \le \|\mathbf{x}\| + \|\mathbf{y}\|$).

### 2. The $L_1$ Norm (Manhattan Distance)
The $L_1$ norm calculates distance by only allowing you to move along the grid lines (like a taxi driving through the grid-like streets of Manhattan).

**Algebraic Definition:**
$$ \|\mathbf{x}\|_1 = \sum_{i=1}^{n} |x_i| $$

> **Mathematical Example (Concrete Numbers):**
> Let vector $\mathbf{x} = [3, -4, 2]$. 
> Step 1: Take the absolute value *(removing the negative sign)* of each element: $|3|, |-4|, |2| \rightarrow 3, 4, 2$.
> Step 2: Sum them up: $3 + 4 + 2 = 9$.
> Result: The $L_1$ norm is 9.
> 
> **AI Context (Sparsity & Lasso Regression):** 
> If you use the $L_1$ norm to penalize your model's weights during training (called $L_1$ Regularization or Lasso), the math naturally forces many of the weights to become *exactly zero*. This creates a **Sparse** *(mostly zeros)* model. This is incredibly useful for Feature Selection—the AI automatically deletes useless features by setting their weight to 0!

### 3. The $L_2$ Norm (Euclidean Distance)
This is the standard "straight-line" distance you learned in high school geometry (the Pythagorean theorem generalized to $n$-dimensions).

**Algebraic Definition:**
$$ \|\mathbf{x}\|_2 = \sqrt{\sum_{i=1}^{n} x_i^2} $$

> **Mathematical Example (Concrete Numbers):**
> Let vector $\mathbf{x} = [3, -4]$. 
> Step 1: Square each element: $3^2 = 9$, $(-4)^2 = 16$.
> Step 2: Sum them up: $9 + 16 = 25$.
> Step 3: Take the square root: $\sqrt{25} = 5$.
> Result: The $L_2$ norm is 5. *(Notice how this is smaller than the $L_1$ norm of 7 for the same 2D vector, because a straight line is shorter than driving along the grid!)*
> 
> **AI Context (Ridge Regression & Weight Decay):** 
> If you use the $L_2$ norm to penalize your weights (called $L_2$ Regularization or Ridge Regression), the math punishes *large* weights very heavily (because $10^2$ is much worse than $1^2$). However, it rarely pushes weights to exactly zero. It just forces them to all be very small and smoothly distributed, which prevents the AI from over-relying on a single dominant feature.

### 4. The Generalized $L_p$ Norm
Both $L_1$ and $L_2$ are just specific versions of the overarching $L_p$ norm formula.

**Algebraic Definition:**
$$ \|\mathbf{x}\|_p = \left( \sum_{i=1}^{n} |x_i|^p \right)^{1/p} $$

> **Mathematical Example (Concrete Numbers):**
> Let's look at the $L_\infty$ (L-Infinity) norm, also called the **Chebyshev distance**. As $p \rightarrow \infty$, the math dictates that the single largest element in the vector completely dominates the sum.
> If $\mathbf{x} = [3, -8, 2]$, the $L_\infty$ norm is simply the maximum absolute value: $8$. 
> 
> **AI Context (Adversarial Robustness):** 
> When researchers test if a neural network can be hacked by adding invisible "noise" to an image (Adversarial Attacks), they often use the $L_\infty$ norm to restrict the attack. Constraining the $L_\infty$ norm to $0.01$ means the hacker cannot alter *any single pixel* by more than 1%, ensuring the hack remains completely invisible to the human eye.

### 5. Mahalanobis Distance (Accounting for Covariance)
Euclidean ($L_2$) distance assumes space is perfectly spherical. But what if your data is shaped like a stretched oval? 

> **Mathematical Example (Conceptual):**
> Imagine plotting human Height vs. Weight. The data forms an upward-sloping oval (taller people weigh more). If you have an outlier point that is [Short, Heavy], it might be the same *Euclidean* distance from the center as a [Tall, Heavy] point. But [Tall, Heavy] is completely normal, while [Short, Heavy] is highly unusual!
> The **Mahalanobis Distance** divides the distance by the **Covariance Matrix** *(a matrix tracking how features stretch together)*. 
> 
> **AI Context (Anomaly Detection):** 
> In production cybersecurity systems, when detecting credit card fraud, you *must* use Mahalanobis distance. It stretches the ruler based on the shape of the data, allowing the system to realize that a \$500 purchase at a grocery store is an anomaly, even if a \$500 purchase at an electronics store is considered a normal distance from the mean.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's write a script that visually proves how different norms "view" space differently by plotting their **Unit Balls** *(all the points in space where the distance to the origin is exactly 1)*.

Create a file named `norms_and_metrics.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from scipy.spatial.distance import mahalanobis

def plot_unit_balls():
    """
    Plots the geometric shape of the "Unit Ball" for L1, L2, and L-Infinity norms.
    This shows how different AI algorithms 'see' a distance of 1.
    """
    print("--- VISUALIZING METRIC SPACES ---")
    
    # Generate points in a 2D grid
    x = np.linspace(-1.5, 1.5, 500)
    y = np.linspace(-1.5, 1.5, 500)
    X, Y = np.meshgrid(x, y)
    
    # Calculate distances from the origin (0,0) for every point in the grid
    # 1. L1 Norm (Manhattan)
    Z_L1 = np.abs(X) + np.abs(Y)
    
    # 2. L2 Norm (Euclidean)
    Z_L2 = np.sqrt(X**2 + Y**2)
    
    # 3. L-Infinity Norm (Chebyshev)
    Z_Linf = np.maximum(np.abs(X), np.abs(Y))
    
    # Plotting
    fig, axes = plt.subplots(1, 3, figsize=(15, 5))
    
    # We use contour plots to draw a line exactly where the distance equals 1
    axes[0].contour(X, Y, Z_L1, levels=[1], colors='r', linewidths=3)
    axes[0].set_title('L1 Norm (Diamond)')
    
    axes[1].contour(X, Y, Z_L2, levels=[1], colors='b', linewidths=3)
    axes[1].set_title('L2 Norm (Circle)')
    
    axes[2].contour(X, Y, Z_Linf, levels=[1], colors='g', linewidths=3)
    axes[2].set_title('L-Infinity Norm (Square)')
    
    for ax in axes:
        ax.axhline(0, color='black', linewidth=1)
        ax.axvline(0, color='black', linewidth=1)
        ax.set_aspect('equal')
        ax.grid(True, linestyle='--', alpha=0.6)
        
    plt.tight_layout()
    filename = "norm_unit_balls.png"
    plt.savefig(filename)
    print(f"Saved visualization to {filename}. Notice how L1 favors the axes (sparsity)!")

def test_mahalanobis():
    """
    Demonstrates why Mahalanobis distance is better for anomaly detection.
    """
    print("\n--- MAHALANOBIS VS EUCLIDEAN ---")
    
    # Imagine a dataset of [Height (cm), Weight (kg)]
    # Taller people weigh more (positive covariance)
    mean_vector = np.array([170, 70])
    
    # Covariance Matrix: High variance in height, high variance in weight, strong positive correlation
    covariance_matrix = np.array([[100, 80], 
                                  [80, 100]])
    
    # Inverse covariance is required for Mahalanobis
    inv_cov = np.linalg.inv(covariance_matrix)
    
    # Point A: [190cm, 90kg] - A very tall, heavy person (Normal pattern)
    # Point B: [170cm, 90kg] - An average height, very heavy person (Anomalous pattern)
    point_A = np.array([190, 90])
    point_B = np.array([170, 90])
    
    # Euclidean Distances
    dist_A_euclidean = np.linalg.norm(point_A - mean_vector)
    dist_B_euclidean = np.linalg.norm(point_B - mean_vector)
    
    # Mahalanobis Distances
    dist_A_mahalanobis = mahalanobis(point_A, mean_vector, inv_cov)
    dist_B_mahalanobis = mahalanobis(point_B, mean_vector, inv_cov)
    
    print(f"Point A (Normal Pattern) - Euclidean: {dist_A_euclidean:.2f} | Mahalanobis: {dist_A_mahalanobis:.2f}")
    print(f"Point B (Anomaly)        - Euclidean: {dist_B_euclidean:.2f} | Mahalanobis: {dist_B_mahalanobis:.2f}")
    print("Conclusion: Euclidean thinks both are equally 'far' from the mean. Mahalanobis realizes Point B breaks the correlation pattern and flags it as a massive anomaly!")

if __name__ == "__main__":
    plot_unit_balls()
    test_mahalanobis()
```

### Key Takeaways from Code:
1. **The Shape of L1:** Look at the `norm_unit_balls.png` image. The $L_1$ unit ball is a diamond. The corners of the diamond lie exactly on the X and Y axes. When an optimization algorithm tries to find the shortest distance touching this shape, it almost always hits a corner. Hitting a corner means one of the features is exactly $0$. **This is the geometric proof of why $L_1$ regularization forces neural networks to delete features!**
2. **Mahalanobis Logic:** Run the script and look at the terminal output. Point A and Point B are both exactly 28 Euclidean units away from the center. But the Mahalanobis distance reveals that Point B is actually *3 times further away* in terms of probability distribution. 

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Configurable K-Nearest Neighbors (KNN)
**Your Task:** Create a file named `knn_classifier.py`.

You will build a classification algorithm from scratch.
1. Create a synthetic dataset of 100 points in 2D space, divided into 2 classes (e.g., Class 0 in the bottom left, Class 1 in the top right).
2. Write a function `calculate_distance(point1, point2, metric="l2")` that accepts a string argument to switch between $L_1$ and $L_2$ math.
3. Write the `predict(new_point, k=3, metric="l2")` function. It should compute the distance from `new_point` to all 100 data points, find the `k` closest points, and return the majority vote of their classes.
4. Test it! Feed it a new point and see if changing the metric from `l1` to `l2` ever changes the predicted class.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"In a production anomaly detection system at Google, why might you choose Mahalanobis distance over standard Euclidean distance to flag fraudulent transactions? What are the computational trade-offs at massive scale?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Flaw of Euclidean:** Euclidean distance treats all features as perfectly independent and equally scaled. If Feature X represents "Account Age in Days" (0 to 5000) and Feature Y represents "Failed Logins" (0 to 5), Euclidean math will completely ignore the Failed Logins because the sheer size of the Age numbers dominates the math.
2. **The Mahalanobis Solution:** Mahalanobis divides the distance by the **Covariance Matrix** *(a grid showing how features stretch and relate to each other)*. It mathematically normalizes the scale of all features and factors in correlations. It understands that 4 failed logins on a 10-day-old account is highly anomalous, even if the absolute Euclidean distance seems small.
3. **The Computational Trade-off ($O(n^3)$ problem):** To compute Mahalanobis distance, you must invert the Covariance Matrix. Matrix inversion is an $O(n^3)$ operation. If the system tracks 10,000 features for a transaction, inverting a $10,000 \times 10,000$ matrix in real-time for every single transaction will crush the latency budget. 
4. **The Engineering Fix:** In production, the covariance matrix and its inverse are computed *offline* asynchronously in a batch job (e.g., once an hour). The real-time inference engine just caches the pre-inverted matrix and performs a fast $O(n^2)$ matrix-vector multiplication when a transaction arrives.

---
**Task for the end of the day:** Commit your code to Git. Look at the unit ball image until it burns into your memory. Tomorrow, we dive into the engine of modern AI: **Matrix Calculus and Backpropagation!**
