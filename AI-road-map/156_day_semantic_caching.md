# Day 156: Caching Strategies (Semantic Cache & Cache Invalidation)

Welcome to Day 156.

If you are running a massive production <abbr title="Application Programming Interface">API</abbr>, you will notice a trend: users ask the same questions repeatedly.
If 1,000 users ask "How do I reset my password?", and your <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr> costs $0.01 per query, you just spent $10 generating the exact same text 1,000 times.

Today, we learn how to slash <abbr title="Application Programming Interface">API</abbr> costs by up to 40% and drop latency to 5 milliseconds by implementing a **Semantic Cache**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Exact Match Cache (The Legacy Way)
In traditional software, we use tools like Redis to cache database queries. 
If `query == "SELECT * FROM users"`, Redis returns the cached <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> instantly. 
This is an **Exact Match Cache**. It hashes the exact string. If the user types *"SELECT * from users "* (with a trailing space), the hash changes, it misses the cache, and the database is queried.
**This fails for LLMs.** Users never type the exact same string. "How do I reset my password?" and "I forgot my password, how do I change it?" have completely different string hashes but require the exact same answer.

### 2. The Semantic Cache
*Analogy:* A librarian doesn't organize books by the exact title string; they organize them by the *meaning* (Dewey Decimal System).
A **Semantic Cache** uses vector embeddings.
1. User asks a question.
2. We convert the question into an Embedding Vector (a string of numbers representing its meaning).
3. We search our Cache Database (e.g., Redis Vector Store or Pinecone).
4. If we find a past question with a **Cosine Similarity > 0.95**, we declare a "Semantic Hit!"
5. We instantly return the past answer. The <abbr title="Large Language Model">LLM</abbr> is never called. Latency drops from 3,000ms to 10ms. Cost drops to zero.

### 3. The Multi-Layer Cache Architecture
In production, you don't just use one cache. You use three:
- **Layer 1: Exact Match (Redis).** Instant (1ms). Catches identical copy-pasted prompts.
- **Layer 2: Semantic Cache (Vector DB).** Fast (20ms). Catches paraphrased prompts.
- **Layer 3: Prefix Cache (vLLM).** If L1 and L2 miss, the query goes to the GPU. But the GPU might already have the System Prompt loaded in VRAM (as we learned in Day 152).

### 4. Cache Invalidation
The hardest problem in computer science is naming things and cache invalidation.
If you update your "Password Reset Policy", your Semantic Cache will still confidently serve the *old* policy to users! 
- **Time-To-Live (TTL):** Evict cache entries after 24 hours.
- **Model Versioning:** If you upgrade from `gpt-4` to `gpt-4o`, you must clear the cache, or users will receive old `gpt-4` responses!
- **Prompt Versioning:** The cache key must include a hash of the System Prompt. If you change the prompt, the hash changes, automatically invalidating old cached responses.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a working Semantic Cache using a fast local embedding model and an in-memory dictionary. 
*(In production, this dictionary would be replaced by Redis with the RediSearch module).*

```python
import time
import numpy as np
from sentence_transformers import SentenceTransformer
from langchain_openai import ChatOpenAI

class SemanticCache:
    def __init__(self, similarity_threshold=0.92):
        print("[SYSTEM] Initializing Semantic Cache...")
        # A fast, tiny local embedding model. Runs instantly on CPU.
        self.encoder = SentenceTransformer('all-MiniLM-L6-v2')
        self.threshold = similarity_threshold
        
        # In production, this is Redis or Pinecone
        self.cache_vectors = []
        self.cache_responses = []

    def _cosine_similarity(self, vec_a, vec_b):
        """Math to calculate how similar two vectors are (0.0 to 1.0)"""
        dot_product = np.dot(vec_a, vec_b)
        norm_a = np.linalg.norm(vec_a)
        norm_b = np.linalg.norm(vec_b)
        return dot_product / (norm_a * norm_b)

    def check_cache(self, query: str):
        # 1. Embed the incoming query
        query_vector = self.encoder.encode(query)
        
        # 2. Search for the most similar past query
        best_score = -1
        best_response = None
        
        for i, cached_vector in enumerate(self.cache_vectors):
            score = self._cosine_similarity(query_vector, cached_vector)
            if score > best_score:
                best_score = score
                best_response = self.cache_responses[i]
                
        # 3. Check against the strict threshold
        if best_score >= self.threshold:
            print(f"   [CACHE HIT] Semantic Match! (Score: {best_score:.3f})")
            return best_response
            
        print(f"   [CACHE MISS] Best match was only {best_score:.3f}. Sending to LLM...")
        return None

    def add_to_cache(self, query: str, response: str):
        print("   [CACHE UPDATE] Saving new response to semantic cache.")
        query_vector = self.encoder.encode(query)
        self.cache_vectors.append(query_vector)
        self.cache_responses.append(response)

# --- EXECUTION SIMULATION ---

def run_caching_simulation():
    # We will simulate a slow LLM
    def simulate_llm(query):
        print("   [LLM] Generating response... (Simulating 3s latency)")
        time.sleep(3)
        return f"To reset your password, click 'Forgot Password' on the login screen."
    
    cache = SemanticCache(similarity_threshold=0.90)
    
    # 1. First User asks the question (Cache Miss)
    query_1 = "How do I reset my password?"
    print(f"\nUser 1: '{query_1}'")
    start = time.time()
    
    response = cache.check_cache(query_1)
    if not response:
        response = simulate_llm(query_1)
        cache.add_to_cache(query_1, response)
        
    print(f"Latency: {time.time() - start:.2f}s | Response: {response}")
    
    # 2. Second User asks the exact same question, but worded differently!
    query_2 = "I forgot my password, how can I change it?"
    print(f"\nUser 2: '{query_2}'")
    start = time.time()
    
    response = cache.check_cache(query_2)
    if not response:
        response = simulate_llm(query_2)
        cache.add_to_cache(query_2, response)
        
    # Notice the latency! It drops from 3.00s to 0.05s!
    print(f"Latency: {time.time() - start:.2f}s | Response: {response}")

# To run:
# run_caching_simulation()
```

### 🔍 Understanding the Savings
On Query 1, the <abbr title="Large Language Model">LLM</abbr> was called. It took 3 seconds and cost <abbr title="Application Programming Interface">API</abbr> tokens.
On Query 2, the user typed a completely different string. But the local embedding model recognized the *semantic meaning* was 93% identical. It bypassed the <abbr title="Large Language Model">LLM</abbr> entirely, returning the answer in 0.05 seconds for exactly $0.00.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
The biggest danger of a Semantic Cache is a **False Positive**. 
If User A asks "Write me a Python script to sort an array," and User B asks "Write me a Java script to sort an array," the semantic meaning is very close. If the threshold is too low, the cache will serve Python code to the Java developer!
**Your Task:** Modify the script above to test this exact scenario. Adjust the `similarity_threshold` until it successfully catches paraphrased questions but correctly rejects the Python vs. Java difference. 

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Your <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr> costs $200,000/month. Analysis shows 40% of queries are semantically similar. Design a caching strategy that reduces costs. Discuss cache architecture, invalidation, and quality risks."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **The Architecture:** Redis with the RediSearch module (or a dedicated service like GPTCache). The Gateway hashes incoming prompts for Layer 1 Exact Match. If missed, it embeds the prompt and queries Redis for Layer 2 Semantic Match.
2. **Quality Risks (False Positives):** Acknowledge that a 40% cache hit rate might include 5% False Positives (giving users slightly wrong context). Propose strict similarity thresholds (e.g., `> 0.98`) to mitigate this.
3. **Context Awareness:** Explain that caching multi-turn chat is dangerous. You cannot just cache `query="What is it?"`. The cache key MUST include the conversation history!
4. **Invalidation Strategy:** Set a strict 24-hour TTL on the cache. Automatically flush the entire cache whenever the underlying <abbr title="Retrieval-Augmented Generation">RAG</abbr> documents are updated, ensuring users don't get cached answers based on stale data.

---
**Task for the end of the day:** Look up **GPTCache**, an open-source library specifically designed for semantic caching of <abbr title="Large Language Model">LLM</abbr> APIs.

Tomorrow, in **Day 157**, we will tackle **Traffic Management**. What happens when your traffic spikes from 100 requests to 10,000 requests in a minute? We will learn Kubernetes Auto-Scaling (HPA and KEDA)!
