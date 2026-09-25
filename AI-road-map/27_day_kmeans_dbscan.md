# Day 27: Unsupervised Learning, K-Means & DBSCAN

Welcome to Day 27. Every single algorithm we have learned so far has been **Supervised**. We always gave the <abbr title="Artificial Intelligence">AI</abbr> a dataset that contained the "Answers" (e.g., this picture is a Cat, this house costs $500k). 

Today, we enter **Unsupervised Learning**. 
Imagine you are a Data Scientist at Netflix. You have a massive database of 10 million users and their watch histories. There are no "Labels". No one has labeled the users as "Horror Fans" or "Comedy Fans." 
Your job is to ask the <abbr title="Artificial Intelligence">AI</abbr> to mathematically discover hidden groupings (Clusters) inside the raw data, entirely on its own.

---

## 🕒 HOUR 1: DEEP THEORY & MATHEMATICS

### 1. K-Means Clustering & The EM Algorithm
The most famous clustering algorithm is **K-Means**. It relies on an incredibly elegant, 2-step mathematical loop called **Expectation-Maximization (EM)**.

Let's say we want to group our Netflix users into $K=3$ distinct clusters.
1. **Initialization:** The <abbr title="Artificial Intelligence">AI</abbr> randomly drops $3$ points (called **Centroids**) anywhere on the graph.
2. **Step 1 (Expectation):** The <abbr title="Artificial Intelligence">AI</abbr> calculates the Euclidean Distance between every single user and the 3 Centroids. It assigns each user to whichever Centroid is closest. (We now have 3 rough groups).
3. **Step 2 (Maximization):** The <abbr title="Artificial Intelligence">AI</abbr> calculates the exact mathematical average (mean) of all the users in Group 1. It physically picks up Centroid 1 and moves it to that exact coordinate. It does the same for Centroids 2 and 3.
4. **Repeat:** Because the Centroids moved, the <abbr title="Artificial Intelligence">AI</abbr> repeats Step 1 (some users might now be closer to a different Centroid). This loop repeats until the Centroids literally stop moving. The clusters are locked in!

### 2. How to choose K? (The Elbow Method)
How do you know if you should group your customers into 3 clusters or 10 clusters?
We calculate the **WCSS (Within-Cluster Sum of Squares)**. This is a metric that measures how "tight" or compact the clusters are. 
You run K-Means with $K=1$, then $K=2$, then $K=3$, and plot the WCSS on a graph. The WCSS will drop dramatically at first, and then suddenly plateau. The point on the graph where the line bends (looking exactly like a human arm's "Elbow") is the mathematically perfect number of clusters!

### 3. The Flaw of K-Means (Spheres Only)
K-Means calculates distances from a center point. Because of this, K-Means mathematically *assumes* that all clusters are perfectly spherical. 
If your data naturally forms a long, squiggly line, or two concentric circles, K-Means will completely fail and just chop the data in half with a straight line.

### 4. DBSCAN (Density-Based Spatial Clustering)
**DBSCAN** fixes the spherical flaw. It completely abandons Centroids. Instead, it groups data based on **Density**.
It works like a virus spreading:
1. It picks a random dot.
2. It draws a small circle (radius = `Epsilon`) around the dot. 
3. If there are at least `min_samples` dots inside that circle, it declares the dot a **Core Point** and forms a cluster.
4. It then jumps to the neighboring dots and repeats the process, chaining them together.
Because it just follows the density, DBSCAN can successfully cluster wavy lines, spirals, and circles! Even better, if a dot is stranded in the middle of nowhere, DBSCAN automatically flags it as **Noise** (an Outlier) and refuses to put it in a cluster.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG

Let's prove the Expectation-Maximization math by writing K-Means from scratch. Then, we will use `scikit-learn` to prove exactly how K-Means fails on non-spherical data, and how DBSCAN saves the day!

Create a file named `clustering_algorithms.py`:

```python
import numpy as np
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans, DBSCAN
from sklearn.datasets import make_moons

# --- 1. K-MEANS EM MATH FROM SCRATCH ---

def calculate_distance(point, centroid):
    """Calculates standard Euclidean distance."""
    return np.sqrt(np.sum((point - centroid)**2))

def kmeans_from_scratch(X, k=2, epochs=10):
    print("--- RUNNING K-MEANS FROM SCRATCH ---")
    # 1. Randomly drop Centroids
    random_indices = np.random.choice(len(X), size=k, replace=False)
    centroids = X[random_indices]
    
    for epoch in range(epochs):
        # Step 1: EXPECTATION (Assign points to closest centroid)
        clusters = [[] for _ in range(k)]
        for point in X:
            distances = [calculate_distance(point, c) for c in centroids]
            closest_centroid_idx = np.argmin(distances)
            clusters[closest_centroid_idx].append(point)
            
        # Step 2: MAXIMIZATION (Move the centroid to the mathematical average)
        new_centroids = []
        for cluster in clusters:
            # np.mean finds the exact center of the group
            new_centroids.append(np.mean(cluster, axis=0))
            
        centroids = np.array(new_centroids)
        print(f"Epoch {epoch+1} Complete. Centroids updated.")
    
    print("Final Centroid Coordinates:")
    print(centroids, "\n")
    return centroids

# --- 2. K-MEANS VS DBSCAN (THE FATAL FLAW) ---

def demonstrate_dbscan():
    print("--- K-MEANS vs DBSCAN ---")
    # 1. Create the "Moons" dataset (Two interlocking crescent moons)
    # This dataset is NOT spherical.
    X, _ = make_moons(n_samples=400, noise=0.05, random_state=42)
    
    # 2. Run K-Means (It will fail)
    kmeans = KMeans(n_clusters=2, random_state=42, n_init=10)
    kmeans_labels = kmeans.fit_predict(X)
    
    # 3. Run DBSCAN (It will succeed)
    # eps=0.2 means "look for dots within 0.2 distance of each other"
    dbscan = DBSCAN(eps=0.2, min_samples=5)
    dbscan_labels = dbscan.fit_predict(X)
    
    # --- PLOTTING ---
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.scatter(X[:, 0], X[:, 1], c=kmeans_labels, cmap='viridis')
    plt.title("K-Means (Failed: Sliced in half)")
    
    plt.subplot(1, 2, 2)
    plt.scatter(X[:, 0], X[:, 1], c=dbscan_labels, cmap='viridis')
    plt.title("DBSCAN (Success: Traced the density!)")
    
    filename = "clustering_comparison.png"
    plt.savefig(filename)
    print(f"Saved visualization to {filename}. Open it to see the proof!")

if __name__ == "__main__":
    # Generate some simple blobs for the scratch algorithm
    from sklearn.datasets import make_blobs
    X_simple, _ = make_blobs(n_samples=100, centers=2, random_state=42)
    
    kmeans_from_scratch(X_simple, k=2)
    demonstrate_dbscan()
```

### Key Takeaways from Code:
1. **The EM Loop:** The scratch implementation proves how simple K-Means is. It's just a `for` loop that calculates distances (Expectation) and then calculates averages (Maximization). 
2. **The DBSCAN Proof:** When you open the generated image, you will see that K-Means literally drew a straight line through the two crescent moons, mixing them together. Because K-Means relies on "Centers", it thinks the tips of the moons belong to different clusters. DBSCAN, however, just followed the dense path of the dots, perfectly identifying the two distinct moons!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The Elbow Method
**Your Task:**
1. Generate a complex dataset using `make_blobs(n_samples=500, centers=5)`. Do NOT tell the algorithm that `centers=5`.
2. Write a `for` loop that runs `KMeans` for `k=1` through `k=10`.
3. For every run, pull the `kmeans.inertia_` value (this is `scikit-learn`'s term for WCSS).
4. Append these values to a list and plot them on a line graph using `plt.plot()`.
5. Look at the graph. You should see a distinct "Elbow" bending exactly at $X = 5$, proving that the math successfully reverse-engineered the hidden structure of the data!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You deploy a K-Means clustering algorithm to segment our users into 4 marketing tiers. However, the marketing team reports that every time they run the script, the 4 tiers are completely different. The results are wildly unstable. Diagnose the exact mathematical cause of this instability, and propose the standard algorithmic fix."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **The Diagnosis (Random Initialization Trap):** 
   - Explain that standard K-Means starts by randomly dropping $K$ centroids onto the graph.
   - If, by pure bad luck, the algorithm drops two centroids right next to each other in the exact same cluster, the EM algorithm will get permanently stuck in a "Local Optimum." It will artificially slice a single, continuous cluster in half, completely ruining the final segmentation. This is why the results change on every run.
2. **The Fix (K-Means++):**
   - State that the industry standard fix is to use the **K-Means++** initialization algorithm.
   - Explain the math: K-Means++ drops the 1st centroid randomly. But for the 2nd centroid, it mathematically calculates the distances of all points and intentionally drops the 2nd centroid **as far away from the 1st centroid as physically possible**. 
   - By mathematically forcing the starting centroids to be maximally distant from each other, it completely eliminates the Random Initialization Trap and guarantees stable, reproducible clusters every time.

---
**Task for the end of the day:** Commit your code to Git. You have successfully conquered Unsupervised Learning!

Tomorrow, in **Day 28**, we tackle the curse of High-Dimensional Data. How do you visualize data that has 10,000 columns? Enter **Principal Component Analysis (PCA) & t-SNE!**
