# Day 85: Advanced RAG Patterns (HyDE, RAPTOR, GraphRAG)

Welcome to Day 85. In Day 84, we built Hybrid Search. It is perfect for exact keyword matches and clear semantic queries. 

But what if a user asks a complex, multi-hop question? What if they ask a "Global" question that requires summarizing 50 different documents at once? A standard Vector Database will fail completely.

Today, we explore the cutting-edge of <abbr title="Retrieval-Augmented Generation">RAG</abbr> architectures: **HyDE, RAPTOR, Query Decomposition, and GraphRAG**.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. HyDE (Hypothetical Document Embeddings)
- **The Flaw:** If a user asks a 5-word question (*"What is the PTO policy?"*), the 5-word embedding vector is very small and lacks semantic depth. It might fail to match the 500-word HR document in the database.
- **The HyDE Hack:** Before searching the database, we ask an <abbr title="Large Language Model">LLM</abbr> to generate a *fake, hallucinated answer* to the question. 
- **The Magic:** We embed the fake answer! The fake answer contains words like *"vacation, days, human resources, sick leave"*. This hallucinated vector is mathematically **much closer** to the real HR document in the vector space than the 5-word question was!

### 2. Query Decomposition (Multi-Hop Reasoning)
- **The Flaw:** *"Who won the Super Bowl the year the iPhone was released?"* A Vector DB cannot answer this because there is no single document that contains both facts together.
- **The Fix:** We ask an <abbr title="Large Language Model">LLM</abbr> to decompose the prompt into sub-queries.
  - Sub-Query 1: *"What year was the first iPhone released?"* $\rightarrow$ <abbr title="Retrieval-Augmented Generation">RAG</abbr> searches and returns **2007**.
  - Sub-Query 2: *"Who won the Super Bowl in 2007?"* $\rightarrow$ <abbr title="Retrieval-Augmented Generation">RAG</abbr> searches and returns **The Colts**.
  - Final Generation: The <abbr title="Large Language Model">LLM</abbr> combines the sub-answers!

### 3. RAPTOR (Tree-Organized Retrieval)
- **The Flaw:** Standard chunking shatters a 500-page book into 2,000 tiny paragraphs. If a user asks *"What is the main theme of this book?"*, the <abbr title="Retrieval-Augmented Generation">RAG</abbr> system retrieves 3 random paragraphs and completely fails. It lost the Global Context.
- **RAPTOR:** We cluster the 2,000 chunks mathematically. We ask an <abbr title="Large Language Model">LLM</abbr> to summarize each cluster. Then we cluster the summaries, and summarize *those* clusters! We build a Tree. 
- When the user asks a specific question, <abbr title="Retrieval-Augmented Generation">RAG</abbr> retrieves the "Leaves" (paragraphs). When the user asks a global question, <abbr title="Retrieval-Augmented Generation">RAG</abbr> retrieves the "Root" (the high-level summaries)!

### 4. GraphRAG (Knowledge Graphs)
Microsoft's GraphRAG takes RAPTOR a step further. It uses an <abbr title="Large Language Model">LLM</abbr> to read the raw text and extract **Entities** (Person: John, Company: Apple) and **Relationships** (John -> works at -> Apple). 
It builds a massive mathematical NetworkX Graph. It uses Community Detection algorithms to find connected nodes. It allows <abbr title="Retrieval-Augmented Generation">RAG</abbr> to trace complex, hidden relationships across thousands of completely separate documents!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's implement the HyDE (Hypothetical Document Embeddings) algorithm. We will simulate asking an <abbr title="Large Language Model">LLM</abbr> for a hallucination, embedding it, and running the retrieval!

Create a file named `advanced_rag.py`:

```python
import numpy as np
from sentence_transformers import SentenceTransformer

def mock_llm_generate(prompt):
    """
    Simulates an LLM generating text. 
    In production, this is an API call to GPT-4 or LLaMA 3.
    """
    if "PTO policy" in prompt:
        # The LLM hallucinates what a standard PTO policy looks like!
        return "Employees generally receive 15 to 20 days of Paid Time Off (PTO) per year for vacation, sick leave, and personal days, managed through the HR portal."
    return "I don't know."

def test_hyde():
    print("--- RUNNING HyDE (Hypothetical Document Embeddings) ---")
    
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 1. Our Database Document
    real_doc = "HR Directive 402: All full-time staff accrue 1.66 days of Paid Time Off monthly, totaling 20 days annually. Use Workday to request leave."
    doc_emb = embedder.encode([real_doc])[0]
    
    # 2. The Short User Query
    user_query = "What is the PTO policy?"
    query_emb = embedder.encode([user_query])[0]
    
    # Standard Dense Retrieval Score
    standard_score = np.dot(query_emb, doc_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(doc_emb))
    print(f"Standard Query Similarity to Real Doc:  {standard_score:.4f}")
    
    # 3. The HyDE Magic!
    hyde_prompt = f"Please write a hypothetical paragraph that answers this question: '{user_query}'"
    hypothetical_doc = mock_llm_generate(hyde_prompt)
    
    print(f"\nLLM Hallucinated Document:\n-> '{hypothetical_doc}'")
    
    # Embed the HALLUCINATION
    hyde_emb = embedder.encode([hypothetical_doc])[0]
    
    # HyDE Retrieval Score
    hyde_score = np.dot(hyde_emb, doc_emb) / (np.linalg.norm(hyde_emb) * np.linalg.norm(doc_emb))
    print(f"\nHyDE Document Similarity to Real Doc:   {hyde_score:.4f}")
    
    print("\nNotice the massive jump in similarity! Because the hallucinated document")
    print("contained semantically rich words like 'vacation' and 'HR', it matched")
    print("the real document much better than the 5-word user query did!")

def test_query_decomposition():
    print("\n--- RUNNING QUERY DECOMPOSITION (Multi-Hop) ---")
    
    complex_query = "Was the CEO of Apple born before the iPhone was released?"
    print(f"Original Complex Query: '{complex_query}'")
    
    # Simulate LLM Decomposition
    print("\nLLM Decomposes into Sub-Queries:")
    sub_q1 = "Who is the CEO of Apple?"
    sub_q2 = "What year was Tim Cook born?"
    sub_q3 = "What year was the first iPhone released?"
    
    print(f"1. {sub_q1}")
    print(f"2. {sub_q2}")
    print(f"3. {sub_q3}")
    
    print("\nThe RAG system will now run 3 SEPARATE searches in parallel,")
    print("gather the 3 specific facts, and feed them all to the final generator!")

if __name__ == "__main__":
    test_hyde()
    test_query_decomposition()
```

### Key Takeaways from Code:
1. **HyDE Trade-offs:** HyDE dramatically increases retrieval accuracy for vague questions. However, it requires a full <abbr title="Large Language Model">LLM</abbr> generation step *before* the search even begins. This doubles the latency of your <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline. It is not suitable for ultra-fast, real-time chatbots.
2. **Multi-Hop Reasoning:** Query decomposition is mandatory for analytical <abbr title="Retrieval-Augmented Generation">RAG</abbr> systems. A single vector simply cannot capture the intersecting logic of three different historical facts.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: The RAPTOR Cluster
**Your Task:**
1. Conceptually design the RAPTOR tree-building algorithm.
2. You have 1,000 text chunks. Embed them all.
3. Use a clustering algorithm like `GaussianMixture` or `KMeans` to group them into 50 clusters.
4. Loop through the 50 clusters. For each cluster, paste all its chunks into an <abbr title="Large Language Model">LLM</abbr> and prompt: *"Summarize the overarching theme of these texts."*
5. You now have 50 Summaries. Treat these summaries as NEW chunks! Embed them, cluster them into 5 groups, and summarize again! You have built a semantic tree.

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Compare naive <abbr title="Retrieval-Augmented Generation">RAG</abbr>, HyDE, RAPTOR, and GraphRAG for a B2B customer support use case with 50,000 FAQ articles and product manuals. Discuss retrieval quality, latency, cost, and maintenance burden."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Naive <abbr title="Retrieval-Augmented Generation">RAG</abbr> (The Baseline):** 
   - Low cost, extremely low latency (50ms). Perfect for explicit queries ("How do I reset my password?"). Terrible for vague or highly technical multi-step troubleshooting.
2. **HyDE (The Vague Query Fix):**
   - High retrieval quality for poorly phrased user questions. High latency (adds 1-2 seconds of <abbr title="Large Language Model">LLM</abbr> generation time before search). Moderate cost increase.
3. **RAPTOR / GraphRAG (The Global Context):**
   - Essential if users ask global questions ("What are all the security protocols across your 5 software products?"). 
   - **The Maintenance Burden:** Massive! Every time an FAQ article is updated, Naive <abbr title="Retrieval-Augmented Generation">RAG</abbr> just updates one vector. GraphRAG and RAPTOR require you to re-compute community summaries and re-build the graph edges, which can cost thousands of dollars in <abbr title="Large Language Model">LLM</abbr> <abbr title="Application Programming Interface">API</abbr> calls for a large dataset!

---
**Task for the end of the day:** Commit your code to Git. 

You have mastered the architecture of <abbr title="Retrieval-Augmented Generation">RAG</abbr>. But everything relies on one fundamental assumption: that your Embedding Model works.
What if it doesn't? Tomorrow, in **Day 86**, we learn how to train our own mathematical Embedding Models from scratch!
