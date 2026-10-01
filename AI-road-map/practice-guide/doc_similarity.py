import numpy as np

# We can import the exact math functions we just built!
from vector_math import cosine_similarity

def get_vocabulary(docs: list[str]) -> list[str]:
    """
    Step 1: Compute the vocabulary.
    Given a list of sentences, return a sorted list of all unique words across all sentences.
    """
    unique_words = set()
    for doc in docs:
        words = doc.lower().split()
        for word in words:
            unique_words.add(word)
    return sorted(list(unique_words))

def compute_tf_vector(doc: str, vocab: list[str]) -> np.ndarray:
    """
    Step 2: Create a Term Frequency (TF) vector.
    Given a single sentence and the full vocabulary, return a numpy array vector 
    where each position counts how many times that vocab word appears in the sentence.
    """
    vector = np.zeros(len(vocab))
    words = doc.lower().split()
    
    for word in words:
        if word in vocab:
            index = vocab.index(word)
            vector[index] += 1
            
    return vector

if __name__ == "__main__":
    docs = [
        "The quick brown fox jumps over the lazy dog",
        "A fast brown fox leaps over a sleepy dog",
        "Machine learning models require huge amounts of compute"
    ]
    
    # --- Step 1: Get Vocabulary ---
    vocab = get_vocabulary(docs)
    print(f"Vocabulary Size: {len(vocab)}")
    print(f"Vocabulary: {vocab}\n")
    
    # --- Step 2: Convert Docs to Vectors ---
    vec1 = compute_tf_vector(docs[0], vocab)
    vec2 = compute_tf_vector(docs[1], vocab)
    vec3 = compute_tf_vector(docs[2], vocab)
    
    print(f"Doc 1 Vector: {vec1}")
    
    # --- Step 3: Compute Pairwise Similarities ---
    sim_1_2 = cosine_similarity(vec1, vec2)
    sim_1_3 = cosine_similarity(vec1, vec3)
    sim_2_3 = cosine_similarity(vec2, vec3)
    
    print(f"\n--- Similarity Scores ---")
    print(f"Doc 1 vs Doc 2 (Foxes & Dogs): {sim_1_2:.4f}")
    print(f"Doc 1 vs Doc 3 (Fox vs Machine Learning): {sim_1_3:.4f}")
    print(f"Doc 2 vs Doc 3 (Dog vs Machine Learning): {sim_2_3:.4f}")
