import numpy as np
import time
from scipy.spatial.distance import cosine

def l2_norm(v: np.ndarray) -> float:
    """Computes the L2 norm (magnitude) of a vector.
    Think of this as calculating how active a user is, or how long a document is."""
    # Production note: np.linalg.norm is heavily optimized in C, 
    # but implementing it from scratch builds intuition.
    return np.sqrt(np.sum(v ** 2))

def dot_product(v1: np.ndarray, v2: np.ndarray) -> float:
    """Computes the dot product of two vectors.
    Think of this as the raw 'matching score' between two profiles."""
    if v1.shape != v2.shape:
        raise ValueError(f"Vector shapes must match. Got {v1.shape} and {v2.shape}")
    return np.sum(v1 * v2)

def cosine_similarity(v1: np.ndarray, v2: np.ndarray) -> float:
    """
    Computes the cosine similarity between two vectors.
    Returns a float between -1.0 and 1.0.
    """
    norm_v1 = l2_norm(v1)
    norm_v2 = l2_norm(v2)
    
    # Handle zero vectors gracefully to prevent NaN (Not a Number) crashes
    # In production, a user who hasn't rated anything will be a zero vector.
    if norm_v1 == 0 or norm_v2 == 0:
        return 0.0 
        
    # We divide the raw match score by their magnitudes to purely compare DIRECTION (taste)
    return dot_product(v1, v2) / (norm_v1 * norm_v2)

def project_vector(b: np.ndarray, a: np.ndarray) -> np.ndarray:
    """Projects vector b onto vector a.
    Think of this as calculating exactly how much of b points in the direction of a."""
    if l2_norm(a) == 0:
        raise ValueError("Cannot project onto a zero vector.")
    
    scalar_projection = dot_product(b, a) / dot_product(a, a)
    return scalar_projection * a

def run_netflix_example():
    """A real-world analogy using our functions."""
    print("--- NETFLIX RECOMMENDATION EXAMPLE ---")
    # Categories: [Action, Sci-Fi, Comedy, Romance]
    
    # Alice likes Action/Sci-Fi a little bit
    alice = np.array([2, 1, 0, 0])
    
    # Bob is a fanatic, watches 10x more, but likes the exact same genres
    bob = np.array([20, 10, 0, 0])
    
    # Charlie only likes Comedy and Romance
    charlie = np.array([0, 0, 5, 4])
    
    print(f"Alice & Bob Cosine Similarity: {cosine_similarity(alice, bob):.4f}") 
    # Output: 1.0 (Identical taste, despite magnitude difference)
    
    print(f"Alice & Charlie Cosine Similarity: {cosine_similarity(alice, charlie):.4f}") 
    # Output: 0.0 (Orthogonal/Perpendicular. They have nothing in common)

def run_benchmarks():
    """Benchmark our custom implementation against scipy."""
    print("\n--- BENCHMARKING HIGH-DIMENSIONAL VECTORS ---")
    # Generate high-dimensional vectors (e.g., standard LLM embedding size like OpenAI's)
    d = 1536 
    v1 = np.random.randn(d)
    v2 = np.random.randn(d)
    print(f"v1: {v1}")
    print(f"v2: {v2}")
    print(f"")
    # Custom Implementation
    start_time = time.perf_counter()
    sim_custom = cosine_similarity(v1, v2)
    custom_time = time.perf_counter() - start_time
    
    # Scipy (Note: Scipy computes cosine distance, which is 1 - cosine similarity)
    start_time = time.perf_counter()
    sim_scipy = 1.0 - cosine(v1, v2)
    scipy_time = time.perf_counter() - start_time
    
    print(f"Custom Output: {sim_custom:.6f} | Time: {custom_time*1e6:.2f} μs")
    print(f"Scipy Output:  {sim_scipy:.6f} | Time: {scipy_time*1e6:.2f} μs")
    print(f"Results Match Exact? {np.isclose(sim_custom, sim_scipy)}")

if __name__ == "__main__":
    run_netflix_example()
    run_benchmarks()
