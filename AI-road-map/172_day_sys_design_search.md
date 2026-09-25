# Day 172: System Design: Modern Search Engines (Semantic Search)

Welcome to Day 172.

In Day 171, we learned how to push content to users (Recommendations). Today, we learn how to pull content when a user actively searches for it.
Historically, search engines used **Lexical Search (BM25)**. If you searched for "laptop battery", the system scanned an index for the exact strings "laptop" and "battery". If a document contained the phrase "notebook power cell", it wouldn't match.

Today, we design a **Semantic Search Engine**—a system that understands the *meaning* of the query, retrieves documents using vectors, reranks them using Cross-Encoders, and uses LLMs to generate a direct answer at the top of the page.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Anatomy of Modern Search
A 2026 Search Engine (like Google or Perplexity) follows a 4-step pipeline:
1. **Query Understanding:** The user types "apple stock price." Does "apple" mean the fruit or the company? An intent classification model tags the query.
2. **Hybrid Retrieval (L0):** We use *two* systems to pull 1,000 candidate documents:
   - *BM25 (Exact Match):* Great for finding specific IDs or exact names.
   - *Dense Vector Search:* Great for semantic meaning ("notebook power cell").
3. **Cross-Encoder Reranking (L1):** We take the 1,000 candidates and pass them through a heavy <abbr title="Natural Language Processing">NLP</abbr> model that looks at the query and the document *simultaneously*, scoring their relevance 1-100.
4. **Answer Generation (L2):** We take the top 5 reranked documents and pass them into an <abbr title="Large Language Model">LLM</abbr> to generate the "Quick Answer" box at the top of the Google search results.

### 2. The Bi-Encoder vs Cross-Encoder
*Analogy:* 
- **Bi-Encoder (Fast Retrieval):** You are at a massive speed-dating event. You glance at someone across the room, decide they look interesting (Embedding Similarity), and put them on a list of 1,000 candidates. This takes 1 second.
- **Cross-Encoder (Slow Reranking):** You take those 1,000 candidates, sit down with them one by one, and have a 5-minute deep conversation to find the absolute best match. This is slow, but highly accurate.

In system design, you **must use both**. You cannot run a Cross-Encoder on 10 Million documents; the latency would be 5 hours. You use the Bi-Encoder to retrieve 1,000 documents in 50ms, then the Cross-Encoder to rerank those 1,000 in 100ms.

### 3. The Inverted Index (Elasticsearch)
Even with vectors, you still need an Inverted Index (Elasticsearch).
If a user searches for "Steve Jobs iPhone presentation 2007", you don't want a vector database returning a presentation from 2008 just because the vectors are "close". You use Elasticsearch to explicitly filter the metadata (`year=2007`), and *then* use vectors to find the semantic match.

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a conceptual Python implementation of a Hybrid Search Engine that implements the Retrieval $\rightarrow$ Reranking cascade!

*(Note: In production, `BM25DB` would be Elasticsearch, and `VectorDB` would be Pinecone/Qdrant. The Cross-Encoder would be a HuggingFace model).*

```python
import time
import random

# --- MOCK INFRASTRUCTURE ---

class BM25Database:
    """Keyword / Exact Match Search"""
    def search(self, query: str, k: int = 500):
        print("   [BM25] Running keyword search...")
        time.sleep(0.02)
        # Returns [DocID, KeywordScore]
        return [(i, random.uniform(0, 10)) for i in range(k)]

class VectorDatabase:
    """Semantic / Concept Search"""
    def search(self, query_vector, k: int = 500):
        print("   [VECTOR] Running semantic search (ANN)...")
        time.sleep(0.03)
        # Returns [DocID, VectorScore]
        return [(i + 500, random.uniform(0.7, 1.0)) for i in range(k)]

class CrossEncoderReranker:
    """Heavy Deep Learning Reranking Model"""
    def rerank(self, query: str, candidate_docs: list):
        print(f"   [CROSS-ENCODER] Reranking {len(candidate_docs)} combined candidates...")
        time.sleep(0.1) # Simulating heavy compute
        
        # We assign a highly accurate relevance score (0.0 to 1.0)
        reranked = [(doc_id, random.uniform(0.1, 0.99)) for doc_id, _ in candidate_docs]
        
        # Sort by best score!
        return sorted(reranked, key=lambda x: x[1], reverse=True)

class LLMAnswerGenerator:
    def generate_snippet(self, query: str, top_docs: list):
        print("   [LLM] Generating direct answer from top 3 documents...")
        time.sleep(0.5)
        return "Based on the top results, a laptop battery typically lasts 3-5 years."

# --- THE SEARCH ENGINE PIPELINE ---

def execute_search_query(user_query: str):
    print(f"\n--- SEARCH: '{user_query}' ---")
    start_time = time.time()
    
    bm25_db = BM25Database()
    vector_db = VectorDatabase()
    reranker = CrossEncoderReranker()
    llm = LLMAnswerGenerator()
    
    # 1. Query Understanding (Embed the query)
    mock_query_vector = [0.1, 0.5, 0.9]
    
    # 2. Hybrid Retrieval (Run BM25 and Vector Search in PARALLEL!)
    # We retrieve 500 keyword matches + 500 semantic matches
    bm25_results = bm25_db.search(user_query, k=500)
    vector_results = vector_db.search(mock_query_vector, k=500)
    
    # Combine the 1,000 candidates
    combined_candidates = bm25_results + vector_results
    
    # 3. Reranking
    final_ranked_results = reranker.rerank(user_query, combined_candidates)
    top_10 = final_ranked_results[:10]
    
    # 4. LLM Answer Generation (RAG)
    # We only pass the absolute best 3 documents to the LLM to save money/time
    top_3_docs = top_10[:3]
    quick_answer = llm.generate_snippet(user_query, top_3_docs)
    
    latency = (time.time() - start_time) * 1000
    print(f"\n✅ Quick Answer: {quick_answer}")
    print(f"✅ Top 10 Doc IDs returned in {latency:.0f}ms!")

# To run:
# execute_search_query("How long does a laptop battery last?")
```

### 🔍 Understanding the Enterprise Value
If you only used Vectors, you might miss a document that explicitly contains the exact model number of the laptop. If you only used BM25, you miss documents using synonyms.
By using **Hybrid Retrieval**, combining them, and passing them through a smart Cross-Encoder, you get the absolute best of both worlds within a 150ms latency budget. This is exactly how Bing, Google, and Perplexity work today.

---

## 🕒 HOUR 3: CHALLENGE & INTERVIEW PREP

### 🛠️ The Challenge
When combining BM25 scores (which range from 0 to 100+) and Vector scores (which range from 0 to 1.0), you cannot just add them together! 
Research **Reciprocal Rank Fusion (RRF)**. It is an algorithm that combines search results from different systems purely based on their *rank* position, ignoring the absolute score.

### 🎤 MAANG Technical Interview Prep

**The Question:**
*"Design a Search Engine for a global e-commerce platform (like Amazon). Users search for products. The system must handle spelling mistakes, synonyms, and support real-time inventory filtering."*

#### 📝 Strong Hire Rubric:
A "Strong Hire" candidate must articulate:
1. **Query Understanding:** Draw an <abbr title="Application Programming Interface">API</abbr> gateway that routes the query to an <abbr title="Natural Language Processing">NLP</abbr> service. The service fixes spelling (e.g., `iphne -> iphone`), detects intent (is this a brand search or a category search?), and extracts entities.
2. **Hybrid Indexing:** Draw an Elasticsearch cluster (for BM25 and filtering inventory > 0) side-by-side with a Vector Database (for semantic matching). 
3. **The Indexing Pipeline (Freshness):** How does the database update when a seller changes a price? Explain a Kafka event-streaming architecture. When a price updates, a Kafka event triggers an update in Elasticsearch instantly (preventing the user from seeing stale prices).
4. **Learning to Rank (LTR):** Explain that the Reranker isn't just a generic <abbr title="Natural Language Processing">NLP</abbr> model. It is trained on user click-data. If users search "apple" and click the iPhone 99% of the time, the reranker learns to boost the iPhone over an actual fruit.

---
**Task for the end of the day:** Review **Elasticsearch**. It is the backbone of almost every text search engine on earth.

Tomorrow, in **Day 173**, we design a system where latency is a matter of life and death: **Real-Time Fraud Detection**. How do you use <abbr title="Machine Learning">ML</abbr> to block a stolen credit card in under 50 milliseconds?
