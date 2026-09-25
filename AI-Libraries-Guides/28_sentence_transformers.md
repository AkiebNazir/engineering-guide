# 28. Embeddings & Sentence-Transformers

Welcome to Embeddings. You cannot build a RAG (Retrieval-Augmented Generation) system, a Semantic Search engine, or a Recommendation System without embeddings.

While massive LLMs (like GPT-4) generate text, smaller models (like Sentence-Transformers) do something equally important: they compress sentences into lists of numbers (vectors) that capture mathematical *meaning*.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. What is an Embedding?
If I ask a computer if "Dog" and "Puppy" are similar, a standard string comparison (`"Dog" == "Puppy"`) returns `False`.
An embedding model converts "Dog" into a 768-dimensional coordinate in space: `[0.12, -0.45, 0.89...]`. It converts "Puppy" into `[0.15, -0.42, 0.81...]`. 
Because the coordinates are extremely close to each other in mathematical space, the computer now knows the words are semantically related!

### 2. Sentence-Transformers (The Library)
While OpenAI provides an Embedding API, you often want to run embeddings locally to save money and ensure privacy. 
**Sentence-Transformers** (built by HuggingFace) is the industry standard Python library for local embeddings. It wraps PyTorch and provides access to thousands of open-source embedding models (like `all-MiniLM-L6-v2` or `BGE-m3`).

### 3. Cosine Similarity
How do you measure the distance between two 768-dimensional vectors? 
You use **Cosine Similarity**. It measures the angle between the two vectors. 
- A score of `1.0` means the sentences have the exact same meaning.
- A score of `0.0` means they are orthogonal (unrelated).
- A score of `-1.0` means they mean the exact opposite.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a mini Semantic Search engine in 30 lines of code.

Create a file named `semantic_search.py`:

```python
# pip install sentence-transformers
from sentence_transformers import SentenceTransformer, util

def run_semantic_search():
    print("--- STARTING SEMANTIC SEARCH ---")
    
    # 1. Load the Embedding Model
    # all-MiniLM-L6-v2 is a tiny, blazing fast model perfect for basic tasks.
    print("Loading model into memory...")
    model = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 2. Our Database of Documents
    corpus = [
        "A man is eating food.",
        "A man is eating a piece of bread.",
        "The girl is carrying a baby.",
        "A man is riding a horse.",
        "A woman is playing violin.",
        "Two men pushed carts through the woods.",
        "A man is riding a white horse on an enclosed ground.",
        "A monkey is playing drums."
    ]
    
    # 3. Embed the Database
    # We compress the English sentences into mathematical vectors.
    print(f"Embedding {len(corpus)} documents...")
    corpus_embeddings = model.encode(corpus, convert_to_tensor=True)
    
    # 4. The User's Search Query
    # Notice this query does not share any exact keywords with the target document!
    query = "Someone in a forest"
    print(f"\nUser Query: '{query}'")
    
    # Embed the query
    query_embedding = model.encode(query, convert_to_tensor=True)
    
    # 5. Calculate Cosine Similarity
    # We compare the query vector against every vector in the database.
    cos_scores = util.cos_sim(query_embedding, corpus_embeddings)[0]
    
    # 6. Get Top Results
    top_results = torch.topk(cos_scores, k=3)
    
    print("\nTop 3 Matches:")
    for score, idx in zip(top_results[0], top_results[1]):
        print(f"Score: {score:.4f} | Document: '{corpus[idx]}'")

if __name__ == "__main__":
    import torch # Required for topk
    run_semantic_search()
```

### Key Takeaways from Code:
1. **Keyword Independence:** If you search "Someone in a forest", traditional keyword search (Elasticsearch BM25) fails completely because the words "Someone" and "Forest" don't exist in the corpus. But Semantic Search finds *"Two men pushed carts through the woods"* because "woods" and "forest" occupy the same mathematical space!
2. **The Vector DB Connection:** In this script, we kept the vectors in RAM. In production with millions of documents, you store `corpus_embeddings` in a Vector Database like Pinecone, Milvus, or pgvector.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Cross-Encoders vs Bi-Encoders
The code above used a **Bi-Encoder**. It embedded the query and the document separately and compared their angles.
**Your Task:**
1. Research **Cross-Encoders**.
2. Why are Cross-Encoders much more accurate than Bi-Encoders?
3. Why are Cross-Encoders way too slow to use across a database of 1 million documents? 
4. How do you combine them in a "Two-Stage Retrieval" (Retrieve & Re-Rank) pipeline?

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"You are building a RAG system for a legal firm. The lawyers complain that when they search for 'Breach of Contract 2021', the semantic search returns documents about 'Breach of Contract 2019' just because the concepts are mathematically similar. How do you fix this?"*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:
1. **The Flaw of Pure Semantic Search:** Semantic embeddings capture concepts, but they are notoriously bad at exact keyword matching (like names, IDs, or years). "2019" and "2021" are very close in vector space.
2. **Hybrid Search:** Propose implementing Hybrid Search. Combine a sparse keyword index (BM25) with the dense semantic index (Embeddings). 
3. **Reciprocal Rank Fusion (RRF):** Explain how you will merge the results. The BM25 engine guarantees the exact year '2021' is matched, while the Vector engine guarantees the conceptual context is matched, creating perfect retrieval.
