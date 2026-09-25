# Day 90: Phase 3 Capstone (Production RAG)

Welcome to Day 90. This is the culmination of everything we have learned since Day 67.
We have learned Transformers, Flash Attention, Vector Databases, Hybrid Search, and Prompt Engineering. 

Today, we assemble all these pieces into a single, massive **Enterprise <abbr title="Retrieval-Augmented Generation">RAG</abbr> System**. This is the exact architecture deployed by Fortune 500 companies to interact with their private knowledge bases.

---

## 🕒 HOUR 1: DEEP THEORY & ANALOGIES

### 1. The Architecture Review
Let's trace the lifecycle of a single query through the system:
1. **The Data Pipeline:** A 1,000-page PDF is loaded. It is mathematically chunked into overlapping paragraphs to preserve semantic meaning without losing the context boundary.
2. **The Vector Database:** The chunks are passed through a Bi-Encoder (`sentence-transformers`) and stored in a Qdrant/Pinecone Vector Database alongside their exact string metadata.
3. **The User Query:** The user asks: *"What is the warranty for part AX-990?"*
4. **Hybrid Search:** The DB runs a Dense Semantic Search (for "warranty") AND a Sparse BM25 Search (for "AX-990").
5. **RRF Merge:** The two lists are mathematically merged using Reciprocal Rank Fusion to extract the Top 50 documents.
6. **Cross-Encoder Reranker:** A massive BERT model reads the query and the Top 50 documents simultaneously using full Self-Attention. It precisely extracts the Top 3 absolute best chunks.
7. **<abbr title="Large Language Model">LLM</abbr> Generation:** The Top 3 chunks are pasted into a strict System Prompt. The <abbr title="Large Language Model">LLM</abbr> acts purely as a reading comprehension engine and outputs the final answer.

### 2. Evaluating <abbr title="Retrieval-Augmented Generation">RAG</abbr> (The RAGAS Framework)
If you update your embedding model, how do you know if your <abbr title="Retrieval-Augmented Generation">RAG</abbr> system got better or worse? You cannot use unit tests. You must use **<abbr title="Large Language Model">LLM</abbr>-as-a-Judge**.
The industry standard framework is **RAGAS** (<abbr title="Retrieval-Augmented Generation">RAG</abbr> Assessment). It evaluates three things:
- **Context Precision:** Look at the Top 3 retrieved chunks. Did the Vector DB actually find the correct information? If the chunks contain garbage, the DB failed.
- **Faithfulness (Grounding):** Look at the final <abbr title="Large Language Model">LLM</abbr> answer. Are the facts in the answer *actually* supported by the retrieved chunks? Or did the <abbr title="Large Language Model">LLM</abbr> hallucinate based on its pre-trained weights?
- **Answer Relevance:** Did the <abbr title="Large Language Model">LLM</abbr> actually answer the user's specific question, or did it just ramble about the topic?

---

## 🕒 HOUR 2: GUIDED CODE-ALONG (THE APPLIED WAY)

Let's build the `EnterpriseRAG` class. We will mock the heavy network calls to keep it runnable, but the architectural logic is 100% production-ready.

Create a file named `rag_capstone.py`:

```python
import numpy as np

class EnterpriseRAG:
    """
    The Phase 3 Capstone Architecture.
    Combines Chunking, Hybrid Search, Reranking, and Generation.
    """
    def __init__(self):
        print("Initializing Enterprise RAG Pipeline...")
        # In production: Connect to Qdrant, load Sentence-Transformers, load Cross-Encoder, initialize OpenAI client
        self.mock_db = [
            "Part AX-990 has a 2-year warranty.",
            "The AX-990 is our flagship part.",
            "All parts have a baseline 1-year warranty unless specified.",
            "The company was founded in 1992."
        ]
        
    def hybrid_search(self, query):
        """Simulates BM25 + Dense Search + RRF Merge"""
        print(f"1. Running Hybrid Search for: '{query}'")
        # In production: Call Qdrant's hybrid search API
        # Mocking the Top 3 results after RRF
        return [
            self.mock_db[2], # "All parts have a baseline 1-year warranty..."
            self.mock_db[0], # "Part AX-990 has a 2-year warranty."
            self.mock_db[1]  # "The AX-990 is our flagship part."
        ]
        
    def rerank_documents(self, query, documents):
        """Simulates passing Query + Docs into a Cross-Encoder BERT model"""
        print("2. Reranking Top Documents with Cross-Encoder...")
        # In production: Use cross-encoder/ms-marco-MiniLM-L-6-v2
        
        # The Cross-Encoder realizes that Doc #1 (mock_db[0]) is the exact answer!
        # It bumps it from Rank #2 to Rank #1.
        reranked = [
            documents[1], # Now Rank 1
            documents[0], # Now Rank 2
            documents[2]  # Now Rank 3
        ]
        return reranked[:2] # Keep only Top 2 for the LLM
        
    def generate_answer(self, query, context_docs):
        """Simulates the final LLM Generation"""
        print("3. Generating Final Answer via LLM...\n")
        
        # Format the context
        context_string = "\n".join([f"- {doc}" for doc in context_docs])
        
        system_prompt = f"""
        Answer the user's question based strictly on the context. 
        Cite your sources.
        
        CONTEXT:
        {context_string}
        
        QUESTION: {query}
        """
        
        # In production: Call OpenAI / LLaMA API
        return "Based on the context, Part AX-990 has a 2-year warranty."

    def evaluate_faithfulness(self, query, context_docs, generated_answer):
        """
        LLM-AS-A-JUDGE (RAGAS Methodology)
        Checks if the generated answer is grounded in the retrieved context.
        """
        print("\n--- RUNNING EVALUATION ---")
        print("Evaluating Faithfulness (Grounding)...")
        
        # We ask a secondary LLM to act as a strict Judge.
        judge_prompt = f"""
        Given the Context and the Answer, does the Answer contain any facts 
        that are NOT explicitly stated in the Context?
        
        Context: {context_docs}
        Answer: {generated_answer}
        
        Output 'PASS' or 'FAIL'.
        """
        
        # In production: Call LLM API with Temperature=0.0
        # In this case, the answer matches the context perfectly.
        return "PASS"

def run_capstone():
    print("========== PHASE 3 CAPSTONE: ENTERPRISE RAG ==========\n")
    
    rag_system = EnterpriseRAG()
    user_query = "What is the warranty for part AX-990?"
    
    # 1. Retrieve (Hybrid Search)
    initial_docs = rag_system.hybrid_search(user_query)
    
    # 2. Rerank (Cross-Encoder)
    top_docs = rag_system.rerank_documents(user_query, initial_docs)
    
    # 3. Generate (LLM)
    final_answer = rag_system.generate_answer(user_query, top_docs)
    
    print("--- FINAL OUTPUT TO USER ---")
    print(final_answer)
    
    # 4. Evaluate (RAGAS)
    eval_result = rag_system.evaluate_faithfulness(user_query, top_docs, final_answer)
    print(f"Grounding Check: {eval_result}")

if __name__ == "__main__":
    run_capstone()
```

### Key Takeaways from Code:
1. **The Modularity:** Notice how completely separate the DB Retrieval, Reranking, and Generation steps are. In a production codebase, these are isolated microservices. If OpenAI goes down, your Hybrid Search <abbr title="Application Programming Interface">API</abbr> still works perfectly.
2. **The <abbr title="Large Language Model">LLM</abbr> Judge:** We didn't ask the user if the answer was good. We built an automated pipeline that can grade 10,000 <abbr title="Retrieval-Augmented Generation">RAG</abbr> queries overnight and output a dashboard showing that $98\%$ of answers passed the Faithfulness check!

---

## 🕒 HOUR 3: SOLO BUILD CHALLENGE & MAANG INTERVIEW

### 🛠️ The Challenge: Fast <abbr title="Application Programming Interface">API</abbr> Deployment
Your Python script works. Now make it an Enterprise <abbr title="Application Programming Interface">API</abbr>.
**Your Task:**
1. Install `fastapi` and `uvicorn`.
2. Wrap your `EnterpriseRAG` class inside a FastAPI app.
3. Create an endpoint: `@app.post("/ask")`.
4. Use a Pydantic schema to define the Request: `{"query": "string"}`.
5. Return the final answer and the retrieved context in a <abbr title="JavaScript Object Notation - A lightweight data-interchange format that is easy for humans to read/write and machines to parse/generate.">JSON</abbr> response. 
6. Start the server and test it using `curl` or Postman!

### 🎤 MAANG Technical Interview Prep

Spend 15 minutes drafting a verbal answer to this question.

**The Question:**
*"Design a <abbr title="Retrieval-Augmented Generation">RAG</abbr>-powered Enterprise Knowledge Base for a company with 500,000 internal documents. Cover Document Processing, Access Control, Hybrid Retrieval, Real-time Updates, and Evaluation."*

#### 📝 Strong Hire Rubric (Evaluate your answer against this):
A "Strong Hire" candidate must articulate the following points clearly:

1. **Document Processing & Real-time Updates:** 
   - State that processing 500k PDFs requires an asynchronous message queue (like Kafka or Celery). 
   - When a document is updated by HR, an event is fired. The worker node deletes the old vectors from the DB based on the `document_id` metadata, re-embeds the new text, and upserts it.
2. **Access Control (Pre-filtering):**
   - Explain that the Vector DB (e.g., Qdrant) must use strict Pre-Filtering. A user's <abbr title="JSON Web Token - A compact, URL-safe means of representing claims to be transferred between two parties, often used for authentication.">JWT</abbr> token is parsed to find their `department_id`. The vector search mathematically restricts the search space to only chunks containing that `department_id` in their metadata.
3. **Retrieval & Evaluation:**
   - Define the Hybrid (Dense + Sparse) -> RRF -> Cross-Encoder pipeline to maximize context precision.
   - Explain that you will build a <abbr title="Continuous Integration and Continuous Deployment">CI/CD</abbr> pipeline running the RAGAS framework. Every time the Embedding model or <abbr title="Large Language Model">LLM</abbr> is updated, you run 500 historical queries and measure Faithfulness and Answer Relevance before deploying to production.

---

### 🎉 CONGRATULATIONS!
You have completed **Phase 3** of the Master Plan. 

You have learned how to use LLMs to build production applications. But we have treated the <abbr title="Large Language Model">LLM</abbr> as a "Black Box" <abbr title="Application Programming Interface">API</abbr>. 

**Tomorrow, we cross the threshold.** 
In **Phase 4 (Days 91-120)**, we pry open the Black Box. We will learn how to build, train, fine-tune, and align massive Language Models across clusters of GPUs! We begin tomorrow with Day 91: The Architecture of LLaMA, Mistral, and Gemma.
