# Day 83: Retrieval-Augmented Generation (<abbr title="Retrieval-Augmented Generation">RAG</abbr>) v1

Welcome to Day 83. We begin the **<abbr title="Retrieval-Augmented Generation">RAG</abbr> Masterclass**.
If you ask ChatGPT about a private document on your laptop, it will either say *"I don't know"* or it will hallucinate a lie. 

LLMs only know what they were trained on (**Parametric Knowledge**). If you want an <abbr title="Large Language Model">LLM</abbr> to answer questions about your company's private wiki, you must connect the <abbr title="Large Language Model">LLM</abbr> to a database (**Non-Parametric Knowledge**). This is Retrieval-Augmented Generation (<abbr title="Retrieval-Augmented Generation">RAG</abbr>).

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The <abbr title="Retrieval-Augmented Generation">RAG</abbr> Pipeline
<abbr title="Retrieval-Augmented Generation">RAG</abbr> is fundamentally a search engine duct-taped to an <abbr title="Large Language Model">LLM</abbr>. It has three steps:
1. **Index:** Read 1,000 PDFs. Break them into small paragraphs (Chunks). Convert each chunk into a mathematical vector using an Embedding Model. Save them in a Vector Database (like FAISS).
2. **Retrieve:** The user asks a question. Convert the question into a vector. Calculate the Cosine Similarity between the Question vector and the Database vectors. Extract the Top 5 most similar paragraphs.
3. **Generate:** Take the 5 paragraphs, format them as text, and paste them into the <abbr title="Large Language Model">LLM</abbr> prompt. Tell the <abbr title="Large Language Model">LLM</abbr>: *"Read these 5 paragraphs, and answer the user's question."*

### 2. Dense Retrieval (The Bi-Encoder)
How do we turn paragraphs into vectors? We use a **Bi-Encoder** (like `Sentence-BERT` or `OpenAI text-embedding-3`).
It is called a Bi-Encoder because the Query and the Document are embedded independently. The model has no idea what the question is when it is embedding the document. 
This makes the database highly efficient to pre-compute!

### 3. FAISS & Vector Databases
If you have 100 Million documents, calculating Cosine Similarity (Dot Product) against the query takes too long ($O(N)$).
Facebook released **FAISS** (Facebook <abbr title="Artificial Intelligence">AI</abbr> Similarity Search). It uses Approximate Nearest Neighbor (ANN) algorithms.
Instead of scanning every document, it clusters documents into mathematical "neighborhoods" (like cities on a map). If your query is about "Taxes", FAISS instantly teleports to the "Finance City" cluster and only searches the documents in that neighborhood, reducing search time to $O(\log N)$!

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build a pure <abbr title="Retrieval-Augmented Generation">RAG</abbr> pipeline from scratch. We will embed 3 documents, load them into FAISS, query the database, and print the exact prompt we would send to the <abbr title="Large Language Model">LLM</abbr>.

*(Mentally run `pip install sentence-transformers faiss-cpu`)*

Create a file named `rag_foundations.py`:

```python
import numpy as np
import faiss
from sentence_transformers import SentenceTransformer

def build_rag_system():
    print("--- RUNNING RAG v1: DENSE RETRIEVAL ---")
    
    # 1. Load a lightweight, open-source Embedding Model (Bi-Encoder)
    # This model outputs 384-dimensional vectors
    print("Loading Embedding Model...")
    embedder = SentenceTransformer('all-MiniLM-L6-v2')
    
    # 2. Our "Private Company Database"
    documents = [
        "Company Policy: Employees are allowed 20 days of Paid Time Off (PTO) per year.",
        "Engineering standards require all Python code to be formatted using the 'Black' formatter.",
        "The WiFi password for the guest network is 'Welcome123!'.",
        "The CEO's dog is named Barnaby and he is a Golden Retriever."
    ]
    
    # 3. INDEXING: Convert documents to Vectors
    print("Embedding Documents...")
    doc_embeddings = embedder.encode(documents)
    
    # Ensure vectors are normalized for Cosine Similarity (Dot Product)
    faiss.normalize_L2(doc_embeddings)
    
    # 4. Create the FAISS Vector Database
    dimension = doc_embeddings.shape[1] # 384
    # IndexFlatIP means "Exact Inner Product" (Cosine Similarity since we normalized)
    index = faiss.IndexFlatIP(dimension)
    
    # Insert the vectors into the DB
    index.add(doc_embeddings)
    print(f"Successfully added {index.ntotal} documents to the Vector DB!\n")
    
    # 5. RETRIEVAL: The User Query
    user_query = "What formatting tool should I use for my code?"
    print(f"User Query: '{user_query}'")
    
    query_embedding = embedder.encode([user_query])
    faiss.normalize_L2(query_embedding)
    
    # Search FAISS for the Top K=1 most similar documents
    TOP_K = 1
    scores, indices = index.search(query_embedding, TOP_K)
    
    retrieved_doc = documents[indices[0][0]]
    print(f"\nRetrieved Document (Similarity Score: {scores[0][0]:.4f}):")
    print(f"-> {retrieved_doc}")
    
    # 6. GENERATION: The final LLM Prompt
    final_prompt = f"""
    You are a helpful company assistant. Answer the user's question based ONLY on the provided context.
    If the answer is not in the context, say "I don't know".
    
    CONTEXT:
    {retrieved_doc}
    
    USER QUESTION: {user_query}
    
    ASSISTANT ANSWER:
    """
    
    print("\n--- FINAL PROMPT SENT TO LLM ---")
    print(final_prompt)

if __name__ == "__main__":
    build_rag_system()
```

### Key Takeaways from Code:
1. **`faiss.normalize_L2`:** By mathematically forcing the length of every vector to equal $1.0$, the Dot Product (`IndexFlatIP`) becomes exactly equivalent to Cosine Similarity. This is the fastest way to calculate similarity on a CPU!
2. **The Prompt Restriction:** The most critical part of <abbr title="Retrieval-Augmented Generation">RAG</abbr> is the system prompt: *"Answer based ONLY on the provided context"*. This instruction is what forces the <abbr title="Large Language Model">LLM</abbr> to stop hallucinating and act strictly as a reading comprehension engine.

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Semantic Chunking
If you feed FAISS a massive 1,000-page PDF, you must "chunk" it. If you chunk purely by character count (e.g., every 500 characters), you might slice a sentence perfectly in half, destroying its mathematical meaning!
**Your Task:**
1. Conceptually design a **Recursive Text Splitter**.
2. First, try to split the document by Double Newlines `\n\n` (Paragraphs).
3. If a paragraph is still too large (>500 tokens), split it by Single Newlines `\n`.
4. If still too large, split by Periods `. ` (Sentences).
5. Always implement an **Overlap** of 50 tokens. The last sentence of Chunk 1 should also be the first sentence of Chunk 2, preserving the context boundary!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Your <abbr title="Retrieval-Augmented Generation">RAG</abbr> system retrieves the perfectly correct documents, but the <abbr title="Large Language Model">LLM</abbr> still generates answers that contradict the context. Diagnose the issue and discuss how you would programmatically evaluate 'Grounding' in production."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Diagnosing the Contradiction:** 
   - State that the <abbr title="Large Language Model">LLM</abbr> is suffering from **Prior Knowledge Override**. If the context says *"The sky is green"*, but the <abbr title="Large Language Model">LLM</abbr> was pre-trained to know the sky is blue, the massive pre-trained weights will overpower the context prompt. 
   - Fix: Use a strictly Instruction-Tuned model (like LLaMA-3-Instruct), set Temperature to $0.0$, and aggressively engineer the prompt to penalize outside knowledge.
2. **Evaluating Grounding (RAGAS framework):**
   - Propose using the **<abbr title="Large Language Model">LLM</abbr>-as-a-Judge** pattern (e.g., RAGAS).
   - *Faithfulness Metric:* Pass the retrieved context and the generated answer to GPT-4. Ask GPT-4 to extract every single factual claim from the answer, and verify if each claim is explicitly stated in the context.
   - *Answer Relevance Metric:* Measure the cosine similarity between the generated answer and the original user query to ensure the <abbr title="Large Language Model">LLM</abbr> actually answered the question instead of just summarizing the context.

---
**Task for the end of the day:** Commit your code to Git. 

You have built <abbr title="Retrieval-Augmented Generation">RAG</abbr> v1. But Dense Retrieval has a fatal flaw: it is terrible at exact keyword searches (like searching for a specific serial number).
Tomorrow, in **Day 84**, we build production-grade <abbr title="Retrieval-Augmented Generation">RAG</abbr>: **Hybrid Search with Cross-Encoder Reranking**!
